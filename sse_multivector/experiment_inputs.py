"""Input preparation and mechanical validation for the shared experiment workflow.

Adapters return explicit template variables separately from review-only evidence.
Execution, history, baselines and human judgments do not belong here.
"""

import hashlib
import json
import re

try:
    from . import extraction_pipeline as engine
    from .prepare_category_title_inputs import prepare as prepare_titles
except ImportError:
    import extraction_pipeline as engine
    from prepare_category_title_inputs import prepare as prepare_titles


def digest(value):
    return hashlib.sha256(engine._canonical_json_bytes(value)).hexdigest()


def render(template, inputs):
    if not isinstance(inputs, dict) or not inputs:
        raise ValueError("case inputs must be a nonempty object of template variables")
    for key, value in inputs.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not isinstance(value, str):
            raise ValueError(
                "template variables must be UPPER_CASE names with string values"
            )
        if "{" + key + "}" not in template:
            raise ValueError(f"unused input variable: {key}")

    # Only named placeholders are interpreted; literal JSON braces remain intact.
    def substitute(match):
        key = match[1]
        if key not in inputs:
            raise ValueError(f"missing template variable: {key}")
        return inputs[key]

    return re.sub(r"\{([A-Z][A-Z0-9_]*)\}", substitute, template)


def prepare_prominence(source, selected=None):
    """Render one exact saved mask per case, retaining node metadata only for review."""
    if 'memberships' in source:
        nodes = source['memberships']['nodes']
        available = {node['group']: node for node in nodes}
        if len(available) != len(nodes):
            raise ValueError('duplicate hierarchy node identity')
        if selected is not None and set(selected) - available.keys():
            raise ValueError('unknown hierarchy node requested')
        members = []
        for nid, node in available.items():
            if selected is not None and nid not in selected:
                continue
            for mask in node['matched_instances']:
                aliases = []
                for origin in mask.get('origins', []):
                    original = origin['source_instance']
                    if any(original[key] != mask[key] for key in ('note_id', 'byte_spans')):
                        raise ValueError('hierarchy mask origin differs from direct member')
                    aliases.append(original['instance'])
                aliases = list(dict.fromkeys(aliases or [mask['instance']]))
                raw = mask['text'].encode()
                if [raw[a:b].decode() for a, b in mask['byte_spans']] != mask['fragments']:
                    raise ValueError('hierarchy mask fragments differ from source spans')
                members.append(dict(id=f'{nid}-{aliases[0]}', node_id=nid,
                                    node_title=node['title'], note_id=mask['note_id'],
                                    text=mask['text'], mask_ids=aliases, byte_spans=mask['byte_spans']))
        source, selected = {'cases': members}, None
    if source.get("adapter") == "titles":
        available = {c["id"]: c for c in source["cases"]}
        if len(available) != len(source["cases"]):
            raise ValueError("duplicate title case identity")
        if selected is not None and set(selected) - available.keys():
            raise ValueError("unknown title group requested")
        members = []
        for cid, case in available.items():
            if selected is not None and cid not in selected:
                continue
            if case["status"] != "valid":
                raise ValueError(f"title is not valid: {cid}")
            packet = case["evidence"]["packet"]
            if packet["packet"] != cid:
                raise ValueError("title packet identity mismatch")
            # Reuse the title adapter's exact-span validation and same-post deduplication.
            group = prepare_titles({"packets": [packet]}, "{NUMBERED_INSTANCES}", [cid])[0]
            posts = {i["note_id"]: i["text"] for i in packet["instances"]}
            for mask in group["sources"]:
                members.append(dict(id=f"{cid}-{mask['instance']}", node_id=cid,
                                    node_title=case["parsed"]["title"], note_id=mask["note_id"],
                                    text=posts[mask["note_id"]], mask_ids=mask["source_instances"],
                                    byte_spans=mask["byte_spans"]))
        source, selected = {"cases": members}, None
    cases, nodes, posts, ids = [], {}, {}, set()
    for item in source["cases"]:
        engine._expect_fields(
            item,
            "prominence case",
            {
                "id",
                "node_id",
                "node_title",
                "note_id",
                "text",
                "mask_ids",
                "byte_spans",
            },
        )
        for field in ("id", "node_id", "node_title", "note_id", "text"):
            engine._expect_string(item[field], field)
        if item["id"] in ids:
            raise ValueError("duplicate case identity")
        ids.add(item["id"])
        mask_ids = engine._validate_string_array(
            item["mask_ids"], "mask_ids", allow_empty=False
        )
        if len(set(mask_ids)) != len(mask_ids):
            raise ValueError("duplicate mask IDs")
        for lookup, key, value in (
            (nodes, item["node_id"], item["node_title"]),
            (posts, item["note_id"], item["text"]),
        ):
            if key in lookup and lookup[key] != value:
                raise ValueError("conflicting node title or source post")
            lookup[key] = value
        raw, cursor, marked, fragments = item["text"].encode("utf-8"), 0, [], []
        spans = item["byte_spans"]
        if not isinstance(spans, list) or not spans:
            raise ValueError("prominence requires a nonempty saved mask")
        for span in spans:
            if (
                not isinstance(span, list)
                or len(span) != 2
                or any(type(x) is not int for x in span)
                or not cursor <= span[0] < span[1] <= len(raw)
            ):
                raise ValueError("invalid prominence mask byte spans")
            start, end = span
            fragment = raw[start:end].decode("utf-8")
            marked.extend((raw[cursor:start].decode("utf-8"), "⟦", fragment, "⟧"))
            fragments.append(fragment)
            cursor = end
        marked.append(raw[cursor:].decode("utf-8"))
        payload = {"mask": fragments, "marked_post": "".join(marked)}
        cases.append(
            {
                "id": item["id"],
                "evidence": item,
                "inputs": {"INPUT_JSON": json.dumps(payload, ensure_ascii=False)},
            }
        )
    if selected is not None:
        if set(selected) - ids:
            raise ValueError("unknown case requested")
        cases = [c for c in cases if c["id"] in selected]
    return cases


def prepare(dataset, source, template):
    adapter = dataset["adapter"]
    if "select" in dataset:
        selected = engine._validate_string_array(
            dataset["select"], "dataset.select", allow_empty=False
        )
        if len(set(selected)) != len(selected):
            raise ValueError("duplicate selection IDs")
    if adapter != "masks" and "mask_format" in dataset:
        raise ValueError("mask_format is only supported by the masks adapter")
    if adapter == "generic":
        cases = source["cases"]
        for case in cases:
            engine._expect_fields(
                case, "case", {"id", "inputs"} | ({"evidence"} & case.keys())
            )
        if len({c["id"] for c in cases}) != len(cases):
            raise ValueError("duplicate case identity")
        if "select" in dataset:
            if set(dataset["select"]) - {c["id"] for c in cases}:
                raise ValueError("unknown case requested")
            cases = [c for c in cases if c["id"] in dataset["select"]]
    elif adapter == "prominence":
        cases = prepare_prominence(source, dataset.get("select"))
    elif adapter == "titles":
        groups = prepare_titles(
            source, "{NUMBERED_INSTANCES}", dataset.get("select", [])
        )
        packets = {p["packet"]: p for p in source["packets"]}
        cases = [
            {
                "id": g["group"],
                "inputs": {"NUMBERED_INSTANCES": g["prompt"]},
                "evidence": {**g, "packet": packets[g["group"]]},
            }
            for g in groups
        ]
    elif adapter == "masks":
        format_ = dataset.get("mask_format", "word_positions")
        items, _ = engine.prepare_mask_inputs(
            source, template, format_, dataset.get("select")
        )
        cases = []
        for item in items:
            inputs = {"POST": item["note"], "SUBJECT": item["subject"]}
            if format_ == "word_positions":
                inputs["INDEXED_POST"] = engine._position_decoder().index_post(
                    item["note"]
                )
            # Independent of batch order, while changed text still fails input pairing.
            identifier = "M" + digest([item["note_id"], item["subject"]])[:24]
            cases.append({"id": identifier, "inputs": inputs, "evidence": item})
    else:
        raise ValueError(f"unknown dataset adapter: {adapter}")
    if not cases:
        raise ValueError("dataset contains no cases")
    ids = set()
    for case in cases:
        identifier = engine._expect_identifier(case["id"], "case.id")
        if identifier in ids:
            raise ValueError(f"duplicate case identity: {identifier}")
        ids.add(identifier)
        case["prompt"] = render(template, case["inputs"])
        case["input_sha256"] = digest(case["inputs"])
    return cases


def validate(dataset, case, raw, schema):
    """Check output mechanics, never semantic correctness."""
    adapter = dataset["adapter"]
    result = {"status": "valid", "output": raw}
    if adapter == "prominence":
        value = json.loads(
            raw, object_pairs_hook=engine._position_decoder().unique_object
        )
        if (
            not isinstance(value, dict)
            or (schema is None and set(value) != {"prominence"})
            or type(value.get("prominence")) is not int
            or not 0 <= value["prominence"] <= 100
        ):
            raise ValueError("expected one integer prominence score from 0 through 100")
        result["parsed"] = value
    if schema is not None or adapter == "titles":
        result["parsed"] = json.loads(raw)
    if adapter == "titles":
        value = result["parsed"]
        if (
            not isinstance(value, dict)
            or set(value) != {"title"}
            or not isinstance(value["title"], str)
            or not value["title"].strip()
        ):
            raise ValueError("expected a nonempty JSON title string")
    if adapter == "masks":
        format_ = dataset.get("mask_format", "word_positions")
        fragments, mapped, ambiguous = engine._map_mask_fragments(
            raw, case["inputs"]["POST"], format_
        )
        result.update(
            status="valid" if fragments else "empty",
            fragments=mapped,
            ambiguous_occurrences=ambiguous,
        )
        if format_ == "word_positions":
            diagnostics, ranges = engine._position_decoder().decode(
                raw, case["inputs"]["POST"]
            )
            result.update(
                ranges=ranges,
                diagnostics={k: v for k, v in diagnostics.items() if k != "mask"},
            )
    return result


def is_flagged(case):
    """Current user decisions take precedence; an empty mask alone is not a failure."""
    reviews = [r for r in case["reviews"] if r["current"]]
    users = [r for r in reviews if r["role"] == "user" and r["verdict"] != "comment"]
    if users:
        return users[-1]["verdict"] in {"reject", "uncertain"}
    agents = [r for r in reviews if r["role"] == "agent"]
    return case["status"] not in {"valid", "empty"} or bool(
        agents and agents[-1]["verdict"] in {"reject", "uncertain"}
    )


def review_batch(plan, report, view=None):
    """Translate compatible cases to the existing UI; list all unsupported cases."""
    adapter = plan["dataset"]["adapter"]
    if view == "prominence":
        if adapter not in {"generic", "prominence"}:
            raise ValueError("prominence view requires generic or prominence inputs")
        fields = ("id", "node_id", "node_title", "note_id", "text", "mask_ids", "byte_spans")
        for case in report["cases"]:
            evidence = case.get("evidence", {})
            if any(key not in evidence for key in fields):
                raise ValueError(f"missing prominence evidence: {case['id']}")
            expected = prepare_prominence({"cases": [{key: evidence[key] for key in fields}]})[0]
            if (case["id"] != evidence["id"] or set(case["inputs"]) != {"INPUT_JSON"}
                    or json.loads(case["inputs"]["INPUT_JSON"]) !=
                    json.loads(expected["inputs"]["INPUT_JSON"])):
                raise ValueError(f"model input differs from prominence evidence: {case['id']}")
            if case["status"] == "valid":
                parsed = case.get("parsed")
                score = parsed.get("prominence") if isinstance(parsed, dict) else None
                if type(score) is not int or not 0 <= score <= 100:
                    raise ValueError(f"invalid prominence score: {case['id']}")
        return prominence_review_batch(plan, report), []
    if adapter == "prominence":
        return prominence_review_batch(plan, report), []
    if adapter not in {"titles", "masks"}:
        raise ValueError(
            "generic experiments use review --case, not a task-specific UI"
        )
    items, excluded = [], []
    for case in report["cases"]:
        if adapter == "titles" and case["status"] != "valid":
            excluded.append({"id": case["id"], "reason": case["status"]})
            continue
        if adapter == "titles":
            baseline = case["baseline"]
            items.append(
                {
                    "item_id": case["id"],
                    "candidate_title": case["parsed"]["title"],
                    "baseline_title": (
                        baseline.get("parsed", {}).get("title") if baseline else None
                    )
                    or "(no valid baseline)",
                    "instances": case["evidence"]["instances"],
                }
            )
        else:
            items.append(
                {
                    "item_id": case["id"],
                    "note_id": case["evidence"]["note_id"],
                    "subject": case["inputs"]["SUBJECT"],
                    "note": case["inputs"]["POST"],
                    "fragments": case["fragments"] if case["status"] == "valid" else [],
                }
            )
        assessments = [
            r for r in case["reviews"] if r["role"] == "agent" and r["current"]
        ]
        if assessments:
            latest = assessments[-1]
            items[-1]["assessment"] = f"Agent: {latest['verdict']}. {latest['comment']}"
        if adapter == "masks":
            items[-1]["details"] = "Generated mask; not semantically approved."
            if case["status"] != "valid":
                items[-1]["details"] = "\n\n".join(
                    str(value) for value in (
                        f"Result status: {case['status']}", case.get("error"),
                        case.get("output"),
                    ) if value
                )
                items[-1]["result_status"] = case["status"]
    batch = {
        "schema_version": 1,
        "batch_id": "experiment-" + digest(items)[:16],
    }
    if adapter == "titles":
        batch.update(
            candidate_version=plan["prompt"]["id"],
            baseline_version=plan.get("baseline_prompt_id") or "none",
        )
    # Keep Rust struct field order for review_state::value_sha256 compatibility.
    batch["items"] = items
    return batch, excluded


def prominence_comment_key(case):
    return digest({"id": case["id"], "prompt": case["prompt"], "output": case["output"]})


def prominence_comments(envelope):
    session = envelope["session"]
    checksum = hashlib.sha256(engine._ordered_json_bytes(session)[:-1]).hexdigest()
    if envelope.get("schema_version") != 1 or envelope.get("state_sha256") != checksum:
        raise ValueError("review comments failed their state hash")
    return session["comments"]


def prominence_review_batch(plan, report):
    """Full-post, single-mask cards; scores order masks, never aggregated posts."""
    groups = {}
    for case in report["cases"]:
        groups.setdefault(case["evidence"]["node_id"], []).append(case)
    notes = []
    for cases in groups.values():
        cases = sorted(
            cases,
            key=lambda c: (
                c["status"] != "valid",
                -c["parsed"]["prominence"] if c["status"] == "valid" else 0,
                c["id"],
            ),
        )
        scored = sum(c["status"] == "valid" for c in cases)
        for position, case in enumerate(cases, 1):
            evidence = case["evidence"]
            valid = case["status"] == "valid"
            score = case["parsed"]["prominence"] if valid else None
            place = (
                f"{position}/{scored} · score {score}"
                if valid
                else f"unranked · {case['status']}"
            )
            comments = [
                "One mask per entry; repeated posts are intentional. Equal scores are tied."
            ]
            if case.get("error"):
                comments.append(str(case["error"]))
            for review in case["reviews"]:
                if review["current"] and review["verdict"] != "comment":
                    comments.append(
                        f"{review['role']}: {review['verdict']}. {review['comment']}"
                    )
            baseline = case.get("baseline")
            if (
                baseline
                and baseline.get("status") == "valid"
                and isinstance(baseline.get("parsed"), dict)
                and type(baseline["parsed"].get("prominence")) is int
            ):
                comments.append(
                    f"Baseline prominence: {baseline['parsed']['prominence']}"
                )
            notes.append(
                {
                    "id": case["id"],
                    "title": (
                        f"{evidence['node_title']} [{evidence['node_id']}] · {place} · "
                        f"{evidence['note_id']} · {', '.join(evidence['mask_ids'])}"
                    ),
                    "text": json.loads(case["inputs"]["INPUT_JSON"])["marked_post"],
                    "model_input": case["prompt"],
                    "results": [
                        {
                            "model": plan["prompt"]["id"],
                            "comment_key": prominence_comment_key(case),
                            "output": (
                                f"Prominence: {score} / 100"
                                if valid
                                else case.get("output") or f"No output: {case['status']}"
                            ),
                            "comment": "\n".join(comments),
                        }
                    ],
                }
            )
    return {
        "schema_version": 1,
        "title": f"{plan['prompt']['id']} · prominence prompt evaluation · one mask per post entry",
        "notes": notes,
    }


def ui_reviews(binding, batch, envelope):
    """Read the existing UI's hashed session, never synthesize human decisions."""

    def ui_hash(value):
        # serde_json::to_vec preserves struct/BTreeMap order and emits no newline.
        return hashlib.sha256(engine._ordered_json_bytes(value)[:-1]).hexdigest()

    session = envelope["session"]
    if (
        envelope.get("schema_version") != 1
        or envelope.get("state_sha256") != ui_hash(session)
        or session.get("batch_sha256") != ui_hash(batch)
        or digest(batch) != binding["batch_sha256"]
    ):
        raise ValueError("review UI session or batch hash differs")
    result = []
    for identifier, decision in session["decisions"].items():
        if decision["outcome"] is None:
            continue
        result.append(
            {
                "case_id": identifier,
                "role": "user",
                "source": binding["session_path"],
                "verdict": {
                    "approved": "accept",
                    "rejected": "reject",
                    "skipped": "uncertain",
                }[decision["outcome"]],
                "comment": decision["comment"],
                **binding["cases"][identifier],
            }
        )
    return result
