"""Input preparation and mechanical validation for the shared experiment workflow.

Adapters return explicit template variables separately from review-only evidence.
Execution, history, baselines and human judgments do not belong here.
"""

import hashlib
import json
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
import re

try:
    from . import extraction_pipeline as engine
    from . import grouped_masks
    from .prepare_category_title_inputs import prepare as prepare_titles
except ImportError:
    import extraction_pipeline as engine
    import grouped_masks
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


def prepare_file(dataset, path, template, load_report=None):
    """Load dataset references and hash the exact bytes used for preparation."""
    path = Path(path).resolve()
    sources = {}

    def read(source_path):
        raw = source_path.read_bytes()
        sources[str(source_path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    source = read(path)
    preparation = None
    if dataset['adapter'] == 'subject_pairs':
        comparison_mode = 'comparisons' in source
        engine._expect_fields(source, 'subject pairs',
            {'schema_version', 'inputs', 'hierarchy',
             'comparisons' if comparison_mode else 'pairs'})
        if type(source['schema_version']) is not int or source['schema_version'] != 1:
            raise ValueError('expected subject pairs schema_version 1')
        loaded, references = {}, {}
        for key in ('inputs', 'hierarchy'):
            source_path = engine._resolve_path(source[key], key, path.parent)
            loaded[key] = read(source_path)
            references[key] = dict(path=str(source_path), sha256=sources[str(source_path)])
        if comparison_mode:
            paths = engine._validate_string_array(source['comparisons'], 'comparisons', allow_empty=False)
            paths = [engine._resolve_path(p, 'comparison experiment', path.parent) for p in paths]
            if len(paths) != len(set(paths)):
                raise ValueError('duplicate comparison experiment')
            if load_report is None:
                raise ValueError('comparison preparation requires validated experiment reports')
            reports = []
            for directory in paths:
                envelope = read(directory / 'experiment.json')
                result = load_report(directory)
                # The shared report loader validates frozen plans and actual receipts.
                for name in envelope['plan']['files']:
                    file = directory / name
                    sources[str(file)] = engine._sha256_file(file)
                for case in result['cases']:
                    if case.get('receipt'):
                        file = Path(case['receipt']['results_path'])
                        sources[str(file)] = engine._sha256_file(file)
                reports.append(result)
            source, preparation = combine_subject_pairs(
                dict(**loaded, pairs=[], source=references), reports, template)
        else:
            source = dict(**loaded, pairs=source['pairs'], source=references)
    effective = {**dataset, 'adapter': 'generic'} if preparation is not None else dataset
    return prepare(effective, source, template), sources, preparation


def combine_subject_pairs(source, reports, template):
    """Combine saved equivalent nodes and remap only previously compared pairs.

    Reports must come from the shared receipt-validating loader. No new pair
    selection, ancestor application, retitling or semantic judgment happens here.
    """
    prepare_subject_pairs(source)  # Validate the complete original partition/edges.
    subjects, original = source['inputs']['subjects'], source['hierarchy']
    groups = original['groups']
    by_id = {f'S{members[0]:04d}': g for g, members in enumerate(groups)}
    parent = list(range(len(groups)))

    def find(g):
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    comparisons, equivalences = [], []
    for report in reports:
        for case in report['cases']:
            if case['status'] != 'valid' or not case.get('receipt'):
                raise ValueError(f"comparison is not valid: {case['id']}")
            evidence = case['evidence']
            saved_sources = evidence['source']
            for key, reference in source['source'].items():
                saved = saved_sources.get(key, saved_sources.get('results') if key == 'hierarchy' else None)
                if not saved or saved['sha256'] != reference['sha256']:
                    raise ValueError('comparison source hash differs from saved hierarchy inputs')
            pair = dict(id=case['id'], A=evidence['A']['node_id'], B=evidence['B']['node_id'])
            expected = prepare_subject_pairs({**source, 'pairs': [pair]})[0]
            if (case['inputs'] != expected['inputs']
                    or case['prompt'] != render(template, expected['inputs'])
                    or any(evidence[k]['subject_entries'] != expected['evidence'][k]['subject_entries']
                           for k in ('A', 'B'))):
                raise ValueError('comparison inputs differ from original nodes or prompt')
            answer = case['parsed']
            if (set(answer) != {'relation', 'reason'} or not isinstance(answer['reason'], str)
                    or answer['relation'] not in {'equivalent', 'a_parent_of_b', 'b_parent_of_a',
                                                  'neither', 'uncertain'}):
                raise ValueError('unsupported subject comparison answer')
            prior = dict(experiment=report['experiment'], case_id=case['id'],
                         A=pair['A'], B=pair['B'], inputs=case['inputs'],
                         answer=answer, receipt=case['receipt'],
                         prompt_id=report['prompt_id'], settings=report['settings'],
                         reviews=case.get('reviews', []),
                         shared_children=evidence.get('shared_children', []))
            comparisons.append(prior)
            if answer['relation'] == 'equivalent':
                a, b = find(by_id[pair['A']]), find(by_id[pair['B']])
                parent[b] = a
                equivalences.append(prior)

    components = {}
    for g, members in enumerate(groups):
        components.setdefault(find(g), []).extend(members)
    merged = sorted((sorted(m) for m in components.values()), key=lambda m: m[0])
    owners = {i: g for g, members in enumerate(merged) for i in members}
    remap = {g: owners[members[0]] for g, members in enumerate(groups)}
    edges = sorted({(remap[a], remap[b]) for a, b in original['edges'] if remap[a] != remap[b]})
    outgoing = {g: set() for g in range(len(merged))}
    incoming = {g: set() for g in range(len(merged))}
    for a, b in edges:
        outgoing[a].add(b)
        incoming[b].add(a)
    try:
        list(TopologicalSorter(incoming).static_order())
    except CycleError as error:
        raise ValueError('equivalent-node combination creates an SP cycle; no repair applied') from error
    descendants = {}
    for a, b in source['inputs']['edges']:
        a, b = owners[a], owners[b]
        if a == b:
            continue
        if a not in descendants:
            pending, visited = list(outgoing[a]), set()
            while pending:
                child = pending.pop()
                if child not in visited:
                    visited.add(child)
                    pending.extend(outgoing[child] - visited)
            descendants[a] = visited
        if b not in descendants[a]:
            raise ValueError('equivalent-node combination loses SP ancestry')

    hierarchy = dict(groups=merged, member_to_group=[owners[i] for i in range(len(subjects))],
                     edges=[list(e) for e in edges])
    mapping = {nid: f'S{merged[remap[g]][0]:04d}' for nid, g in by_id.items()}
    pairs, internal = {}, []
    for prior in comparisons:
        a, b = mapping[prior['A']], mapping[prior['B']]
        if a == b:
            internal.append(prior)
        else:
            key = tuple(sorted((remap[by_id[prior['A']]], remap[by_id[prior['B']]])))
            pairs.setdefault(key, []).append(prior)

    combined_source = {**source, 'hierarchy': hierarchy}
    cases, unchanged = [], []
    for (ga, gb), previous in sorted(pairs.items()):
        a, b = f'S{merged[ga][0]:04d}', f'S{merged[gb][0]:04d}'
        pair = dict(id=a + '-' + b, A=a, B=b)
        # Keep unchanged judgments as source-bound evidence, not new model jobs.
        # This does not weaken the executor's exact transport/request cache rules.
        saved = None
        for prior in previous:
            trial = dict(id=prior['case_id'], A=mapping[prior['A']], B=mapping[prior['B']])
            candidate = prepare_subject_pairs({**combined_source, 'pairs': [trial]})[0]
            if candidate['inputs'] == prior['inputs']:
                pair = trial
                saved = prior
                break
        if saved is not None:
            unchanged.append(dict(id=pair['id'], A=pair['A'], B=pair['B'],
                                  source=saved, previous_comparisons=previous))
            continue
        case = prepare_subject_pairs({**combined_source, 'pairs': [pair]})[0]
        case['evidence']['previous_comparisons'] = previous
        for key in ('A', 'B'):
            nid = case['evidence'][key]['node_id']
            case['evidence'][key]['original_nodes'] = [old for old, new in mapping.items() if new == nid]
        cases.append(case)
    preparation = dict(
        hierarchy=hierarchy, original_node_to_combined=mapping,
        equivalent_answers=equivalences, internal_comparisons=internal,
        unchanged_comparisons=unchanged,
        summary=dict(original_nodes=len(groups), combined_nodes=len(merged),
            equivalent_answers=len(equivalences), internal_comparisons=len(internal),
            original_comparisons=len(comparisons), current_pairs=len(pairs),
            changed_pairs=len(cases), unchanged_pairs=len(unchanged)))
    # Already prepared evidence is preserved through the ordinary rendering path.
    return dict(cases=cases), preparation


def prepare_subject_pairs(source, selected=None):
    """Compare explicitly selected saved SP hierarchy nodes, not their source posts."""
    inputs, hierarchy = source['inputs'], source['hierarchy']
    subjects, groups = inputs['subjects'], hierarchy['groups']
    posts = {p['note_id']: p for p in inputs['posts']}
    if len(posts) != len(inputs['posts']):
        raise ValueError('duplicate source post identity')
    for i, subject in enumerate(subjects):
        if type(subject['index']) is not int or subject['index'] != i:
            raise ValueError('subject index does not match saved position')
        engine._expect_string(subject['subject'], 'subject')
        if not isinstance(subject['context'], str):
            raise ValueError('subject context must be a string')
        if subject['note_id'] not in posts:
            raise ValueError('subject refers to an unknown source post')

    owners, nodes = {}, {}
    for g, members in enumerate(groups):
        if not isinstance(members, list) or not members:
            raise ValueError('hierarchy group must be nonempty')
        for i in members:
            if type(i) is not int or not 0 <= i < len(subjects) or i in owners:
                raise ValueError('invalid or repeated hierarchy subject member')
            owners[i] = g
        # Same identity as subject_matching_probe.browser_spec; not the group index.
        nodes[f'S{members[0]:04d}'] = g
    if set(owners) != set(range(len(subjects))):
        raise ValueError('hierarchy groups do not cover the saved subjects')
    if hierarchy['member_to_group'] != [owners[i] for i in range(len(subjects))]:
        raise ValueError('hierarchy member mapping differs from groups')

    def edges(value, size):
        for edge in value:
            if (not isinstance(edge, list) or len(edge) != 2
                    or any(type(i) is not int or not 0 <= i < size for i in edge)):
                raise ValueError('invalid hierarchy or SP edge')
            yield edge

    children = {g: set() for g in range(len(groups))}
    for a, b in edges(hierarchy['edges'], len(groups)):
        children[a].add(b)
    witnesses = {}
    for a, b in edges(inputs['edges'], len(subjects)):
        witnesses.setdefault((owners[a], owners[b]), set()).add(subjects[a]['note_short_id'])

    def node(nid):
        g = nodes[nid]
        entries, seen = [], set()
        for i in groups[g]:
            subject = subjects[i]
            pair = subject['subject'], subject['context']
            if pair not in seen:
                seen.add(pair)
                entries.append(dict(subject=pair[0], context=pair[1]))
        return entries, dict(node_id=nid, group_index=g,
                             subject_entries=[subjects[i] for i in groups[g]])

    cases, ids = [], set()
    for pair in source['pairs']:
        engine._expect_fields(pair, 'subject pair', {'id', 'A', 'B'})
        cid = engine._expect_identifier(pair['id'], 'case.id')
        if cid in ids:
            raise ValueError('duplicate case identity')
        ids.add(cid)
        for key in ('A', 'B'):
            nid = engine._expect_string(pair[key], f'pair.{key}')
            if nid not in nodes:
                raise ValueError(f'unknown hierarchy node: {nid}')
        if pair['A'] == pair['B']:
            raise ValueError('subject pair must name distinct hierarchy nodes')
        if selected is not None and cid not in selected:
            continue
        ea, a = node(pair['A'])
        eb, b = node(pair['B'])
        ga, gb = a['group_index'], b['group_index']
        shared = [dict(id=f'S{groups[g][0]:04d}',
                       names=list(dict.fromkeys(subjects[i]['subject'] for i in groups[g])),
                       a_posts=sorted(witnesses.get((ga, g), [])),
                       b_posts=sorted(witnesses.get((gb, g), [])))
                  for g in sorted(children[ga] & children[gb])]
        post_ids = sorted({s['note_id'] for n in (a, b) for s in n['subject_entries']})
        cases.append(dict(id=cid,
            inputs={'INPUT_JSON': json.dumps({'A': ea, 'B': eb}, ensure_ascii=False, indent=2)},
            evidence=dict(A=a, B=b, source=source['source'], shared_children=shared,
                          source_posts=[posts[p] for p in post_ids])))
    if selected is not None and set(selected) - ids:
        raise ValueError('unknown case requested')
    return cases


def union_spans(spans):
    """Union validated byte spans, preserving every gap in the source text."""
    result = []
    for start, end in sorted(spans):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def prepare_prominence(source, selected=None, combine_masks=False):
    """Render saved masks, optionally unioned per node/post; metadata stays review-only."""
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
    if combine_masks:
        posts = {}
        for case in cases:
            e = case['evidence']
            key = e['node_id'], e['note_id']
            combined = posts.setdefault(key, dict(e, id='P' + digest(key)[:24],
                                                   mask_ids=[], byte_spans=[]))
            combined['mask_ids'].extend(e['mask_ids'])
            combined['byte_spans'].extend(e['byte_spans'])
        for combined in posts.values():
            combined['mask_ids'] = list(dict.fromkeys(combined['mask_ids']))
            combined['byte_spans'] = union_spans(combined['byte_spans'])
        return prepare_prominence({'cases': list(posts.values())})
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
    if 'combine_masks' in dataset:
        if adapter != 'prominence' or type(dataset['combine_masks']) is not bool:
            raise ValueError('combine_masks requires the prominence adapter and a boolean')
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
        cases = prepare_prominence(source, dataset.get("select"), dataset.get('combine_masks', False))
    elif adapter == "subject_pairs":
        cases = prepare_subject_pairs(source, dataset.get("select"))
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
    elif adapter == "grouped_masks":
        cases = grouped_masks.prepare(source, dataset.get("select"))
    elif adapter == "masks":
        format_ = dataset.get("mask_format", "word_positions")
        items, _ = engine.prepare_mask_inputs(
            source, template, format_, dataset.get("select")
        )
        cases = []
        occurrences = {}
        for item in items:
            inputs = {"POST": item["note"], "SUBJECT": item["subject"]}
            if format_ == "word_positions":
                inputs["INDEXED_POST"] = engine._position_decoder().index_post(
                    item["note"]
                )
            # Independent of batch order, while changed text still fails input pairing.
            identifier = "M" + digest([item["note_id"], item["subject"]])[:24]
            occurrences[identifier] = occurrences.get(identifier, 0) + 1
            if occurrences[identifier] > 1:
                identifier += "-" + str(occurrences[identifier])
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
    if adapter == "grouped_masks":
        result.update(grouped_masks.validate(case, raw))
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
