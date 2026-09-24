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


def review_batch(plan, report):
    """Translate compatible cases to the existing UI; list all unsupported cases."""
    adapter = plan["dataset"]["adapter"]
    if adapter not in {"titles", "masks"}:
        raise ValueError(
            "generic experiments use review --case, not a task-specific UI"
        )
    items, excluded = [], []
    for case in report["cases"]:
        if case["status"] != "valid":
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
                    "fragments": case["fragments"],
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
