"""Source-bound parent-name nominations and bounded diagnostic lookup.

Preparation never performs inference, creates nodes or changes a hierarchy.
Exact-only lookup remains the default; vector lookup selects comparisons only.
"""

from collections import defaultdict
import hashlib
from pathlib import Path
import re

try:
    from . import bounded_hierarchy_workflow as bounded
    from .bounded_hierarchy_candidates import _ancestor, _validate_graph
    from .bounded_hierarchy_build import _unchanged_judgments
    from .experiment_inputs import digest
    from .parent_guide_measurement import PARENT_GUIDE_SCHEMA, pack_parent_guide_requests
except ImportError:
    import bounded_hierarchy_workflow as bounded
    from bounded_hierarchy_candidates import _ancestor, _validate_graph
    from bounded_hierarchy_build import _unchanged_judgments
    from experiment_inputs import digest
    from parent_guide_measurement import PARENT_GUIDE_SCHEMA, pack_parent_guide_requests


def validate_guides(case, raw):
    """Require every supplied query in order, with at most three distinct names."""
    payload = bounded._parse(case["inputs"]["INPUT_JSON"])
    expected = [q["id"] for q in payload["queries"]]
    value = bounded._parse(raw)
    bounded._fields(value, {"queries"}, "parent-guide response")
    if not isinstance(value["queries"], list):
        raise ValueError("queries must be an array")
    for query in value["queries"]:
        bounded._fields(query, {"id", "parents"}, "parent guide")
        names = query["parents"]
        if (not isinstance(names, list) or len(names) > 3
                or any(not isinstance(name, str) or not name.strip() or len(name) > 160 for name in names)
                or len(set(names)) != len(names)):
            raise ValueError("each query permits at most three distinct nonblank parent names of 160 characters")
    if [q["id"] for q in value["queries"]] != expected:
        raise ValueError("parent guides must return every supplied query exactly once in order")
    return value


def create_guide_source(source_refs, template, *, base=None, selected=None):
    """Prepare compact query-only requests from protected saved SP references."""
    if not isinstance(source_refs, dict) or set(source_refs) - {
            "schema_version", "inputs", "hierarchy", "query_nodes"}:
        raise ValueError("invalid parent-guide source references")
    loaded, references, protected = bounded._read_sources(source_refs, base)
    cases = pack_parent_guide_requests(loaded["inputs"], loaded["hierarchy"], template,
                                      query_nodes=source_refs.get("query_nodes"))
    for case in cases:
        case["evidence"]["source"] = references
        case["evidence"]["reference_policy"] = bounded.REFERENCE_POLICY
    if selected is not None:
        if set(selected) - {case["id"] for case in cases}:
            raise ValueError("unknown parent-guide case requested")
        cases = [case for case in cases if case["id"] in selected]
    preparation = dict(phase="parent_guides", source=references,
        reference_policy=bounded.REFERENCE_POLICY,
        query_nodes=[q for case in cases for q in case["evidence"]["queries"]],
        max_queries=16, max_input_tokens=bounded.MAX_INPUT_TOKENS, tokenizer="o200k_base")
    return cases, protected, preparation


def _judged_pairs(history, inputs, hierarchy, references, owner):
    if history is None:
        return set()
    if "plan" in history:
        plan = history["plan"]
        if digest(plan) != history.get("sha256"):
            raise ValueError("saved judgment build digest differs")
        path = plan.get("spec", {}).get("inputs")
        if not isinstance(path, str) or plan.get("protected_sha256", {}).get(path) != references["inputs"]["sha256"]:
            raise ValueError("saved judgment build SP inputs differ")
        judgments = plan.get("comparisons")
    else:
        if history.get("subjects") != inputs["subjects"]:
            raise ValueError("saved judgment subjects differ from source SP entries")
        judgments = history.get("comparisons")
    if not isinstance(judgments, list):
        raise ValueError("saved judgments require comparisons")
    for judgment in judgments:
        if not isinstance(judgment, dict) or any(
                not isinstance(judgment.get(side), str)
                or not re.fullmatch(r"S[0-9]+", judgment[side])
                or int(judgment[side][1:]) not in owner for side in ("A", "B")):
            raise ValueError("judged node reference is outside original SP inputs")
    unchanged = _unchanged_judgments(inputs, hierarchy, judgments)
    return {frozenset(owner[int(judgment[side][1:])] for side in ("A", "B"))
            for judgment in unchanged}


def resolve_exact_guides(inputs, hierarchy, reports, references, *, history=None):
    """Resolve verbatim saved wordings, with 32 alias inspections and three nodes/query."""
    if len(inputs["subjects"]) > 5000:
        raise ValueError("parent-guide diagnostic is limited to 5000 SP entries")
    owner, groups, parents, _ = _validate_graph(inputs, hierarchy)
    nodes = bounded._node_entries(inputs, hierarchy)
    judged = _judged_pairs(history, inputs, hierarchy, references, owner)
    aliases = defaultdict(set)
    for index, entry in enumerate(inputs["subjects"]):
        aliases[entry["subject"]].add(owner[index])
    aliases = {name: sorted(ids) for name, ids in aliases.items()}
    pairs, records = {}, []
    inspections, chosen, proposed = defaultdict(int), defaultdict(set), defaultdict(set)
    for report in reports:
        if report.get("adapter") != "bounded_parent_guides" or report.get("prompt_id") != "PCPv3":
            raise ValueError("comparison preparation requires validated PCPv3 parent-guide reports")
        for case in report["cases"]:
            source = case["evidence"].get("source", {})
            if any(source.get(key) != references[key] for key in ("inputs", "hierarchy")):
                raise ValueError("parent-guide source differs from current hierarchy inputs")
            payload = bounded._parse(case["inputs"]["INPUT_JSON"])
            bounded._fields(payload, {"queries"}, "parent-guide input")
            for query in payload["queries"]:
                bounded._fields(query, {"id", "entries"}, "parent-guide query")
                qid = query["id"]
                if (not isinstance(qid, str) or qid not in nodes or query["entries"] != nodes[qid]
                        or case["evidence"].get("original_members", {}).get(qid) != groups[qid]):
                    raise ValueError("parent-guide query differs from original SP references")
            if case.get("status") != "valid" or not case.get("receipt"):
                raise ValueError("parent guides require complete valid saved answers")
            parsed = validate_guides(case, bounded.compact(case["parsed"]))
            for query in parsed["queries"]:
                qid = query["id"]
                proposed[qid].update(query["parents"])
                if len(proposed[qid]) > 3:
                    raise ValueError("query has more than three distinct parent names across reports")
                for name in query["parents"]:
                    record = dict(query=qid, name=name, experiment=report["experiment"],
                                  case_id=case["id"], selected=[], skipped_nodes=[], alias_inspections=0)
                    records.append(record)
                    if inspections[qid] >= 32 or len(chosen[qid]) >= 3:
                        record.update(status="skipped", reason=("alias_limit" if inspections[qid] >= 32
                                                               else "candidate_limit"))
                        continue
                    matches = aliases.get(name, [])
                    if not matches:
                        record.update(status="unresolved", reason="exact_name_absent")
                        continue
                    for cid in matches:
                        if inspections[qid] >= 32 or len(chosen[qid]) >= 3:
                            break
                        inspections[qid] += 1
                        record["alias_inspections"] += 1
                        reason = None
                        if cid == qid:
                            reason = "self"
                        elif cid in chosen[qid]:
                            reason = "duplicate_candidate"
                        elif frozenset((qid, cid)) in judged:
                            reason = "unchanged_judgment"
                        else:
                            forward = _ancestor(qid, cid, parents, max_operations=2048)
                            reverse = _ancestor(cid, qid, parents, max_operations=2048)
                            if forward is None or reverse is None:
                                reason = "ancestry_work_limit"
                            elif forward or reverse:
                                reason = "existing_ancestry"
                        if reason:
                            record["skipped_nodes"].append(dict(id=cid, reason=reason))
                            continue
                        chosen[qid].add(cid)
                        record["selected"].append(cid)
                        a, b = sorted((qid, cid))
                        pair = pairs.setdefault((a, b), dict(id=a + "-" + b, A=a, B=b,
                            reference_entries=dict(A=nodes[a], B=nodes[b]), parent_candidates=[]))
                        pair["parent_candidates"].append(dict(experiment=report["experiment"],
                            case_id=case["id"], prompt_id=report["prompt_id"], settings=report["settings"],
                            query=qid, candidate=dict(id=cid, name=name), resolution="exact_saved_wording",
                            receipt=case["receipt"]))
                    record["search_complete"] = record["alias_inspections"] == len(matches)
                    record["status"] = "resolved" if record["selected"] else "unresolved"
                    if not record["search_complete"]:
                        record["reason"] = "alias_limit" if inspections[qid] >= 32 else "candidate_limit"
                    elif not record["selected"]:
                        record["reason"] = "no_eligible_exact_match"
    return [pairs[key] for key in sorted(pairs)], nodes, dict(
        guides=records, alias_inspections_by_query=dict(inspections),
        candidates_by_query={qid: sorted(ids) for qid, ids in chosen.items()},
        unresolved_guides=[record for record in records if record["status"] == "unresolved"],
        skipped_guides=[record for record in records if record["status"] == "skipped"])


def _protect_report(report, protected):
    directory = Path(report["experiment"]).resolve()
    path = directory / "experiment.json"
    protected[str(path)] = bounded.engine._sha256_file(path)
    envelope = bounded.engine._load_json(path, str(path))
    paths = {**{str(directory / name): expected for name, expected in envelope["plan"]["files"].items()},
             **envelope["plan"].get("sources", {})}
    for name, expected in paths.items():
        path = Path(name).resolve()
        actual = bounded.engine._sha256_file(path)
        if actual != expected:
            raise ValueError(f"protected parent-guide source changed: {path}")
        protected[str(path)] = actual
    for case in report["cases"]:
        path = Path(case["receipt"]["results_path"]).resolve()
        protected[str(path)] = bounded.engine._sha256_file(path)


def resolve_vector_guides(inputs, hierarchy, reports, references, subject_vectors, *,
                          history=None, prior_reports=()):
    """Test one nearest eligible node per unmatched name; never repeat exact pairs."""
    try:
        from .bounded_hierarchy_candidates import HNSWSubjectNeighbors
    except ImportError:
        from bounded_hierarchy_candidates import HNSWSubjectNeighbors
    exact_pairs, nodes, resolution = resolve_exact_guides(
        inputs, hierarchy, reports, references, history=history)
    exact_selected = {frozenset((pair["A"], pair["B"])) for pair in exact_pairs}
    owner, _, parents, _ = _validate_graph(inputs, hierarchy)
    judged = _judged_pairs(history, inputs, hierarchy, references, owner)
    for report in prior_reports:
        if (report.get("adapter") not in {"bounded_comparisons", "bounded_parent_comparisons"}
                or report.get("prompt_id") != "BCPv5"):
            raise ValueError("prior comparisons require validated BCPv5 reports")
        previous = []
        for case in report["cases"]:
            if (case.get("status") != "valid" or not case.get("receipt")
                    or case["evidence"].get("source", {}).get("inputs") != references["inputs"]):
                raise ValueError("prior comparisons require valid source-bound saved answers")
            previous.extend(bounded.extract_comparisons(case, case["parsed"]))
        judged.update(_judged_pairs(dict(subjects=inputs["subjects"], comparisons=previous),
                                    inputs, hierarchy, references, owner))
    aliases = defaultdict(set)
    for index, entry in enumerate(inputs["subjects"]):
        aliases[entry["subject"]].add(owner[index])
    aliases = {name: sorted(ids) for name, ids in aliases.items()}
    provider = HNSWSubjectNeighbors(inputs, hierarchy, subject_vectors)
    inspections = defaultdict(int, resolution["alias_inspections_by_query"])
    chosen = {qid: set(ids) for qid, ids in resolution["candidates_by_query"].items()}
    saved_cases = {(report["experiment"], case["id"]): (report, case)
                   for report in reports for case in report["cases"]}
    pairs, shortlist_cache = {}, {}
    for record in resolution["guides"]:
        if record.get("reason") != "exact_name_absent":
            continue
        qid, name = record["query"], record["name"]
        if inspections[qid] >= 32 or len(chosen.get(qid, set())) >= 3:
            record.update(status="skipped", reason=("alias_limit" if inspections[qid] >= 32
                                                   else "candidate_limit"))
            continue
        encoding = hashlib.sha256(name.encode()).hexdigest()
        try:
            vector = subject_vectors[encoding, encoding[:16]]
        except KeyError as error:
            raise ValueError(f"missing standalone guide vector: {name}") from error
        if name not in shortlist_cache:
            shortlist_cache[name] = provider.wording_neighbors(vector)
        shortlist = shortlist_cache[name]
        record.update(resolution="subject_vector_fallback", query_encoding_id=encoding,
                      wording_inspections=len(shortlist), search_complete=False)
        found = None
        for word, score in shortlist:
            for cid in aliases[word]:
                if inspections[qid] >= 32:
                    break
                inspections[qid] += 1
                record["alias_inspections"] += 1
                reason = None
                if cid == qid:
                    reason = "self"
                elif cid in chosen.get(qid, set()):
                    reason = "duplicate_candidate"
                elif frozenset((qid, cid)) in exact_selected:
                    reason = "exact_pair_already_selected"
                elif frozenset((qid, cid)) in judged:
                    reason = "unchanged_judgment"
                else:
                    forward = _ancestor(qid, cid, parents, max_operations=2048)
                    reverse = _ancestor(cid, qid, parents, max_operations=2048)
                    if forward is None or reverse is None:
                        reason = "ancestry_work_limit"
                    elif forward or reverse:
                        reason = "existing_ancestry"
                if reason:
                    record["skipped_nodes"].append(dict(id=cid, reason=reason))
                else:
                    found = cid, word, score
                    break
            if found is not None or inspections[qid] >= 32:
                break
        if found is None:
            record.update(status="unresolved", reason=("alias_limit" if inspections[qid] >= 32
                                                       else "no_eligible_shortlist_match"))
            continue
        cid, word, score = found
        chosen.setdefault(qid, set()).add(cid)
        record.update(status="resolved", selected=[cid], matched_wording=word, cosine=score)
        record.pop("reason", None)
        a, b = sorted((qid, cid))
        pair = pairs.setdefault((a, b), dict(id=a + "-" + b, A=a, B=b,
            reference_entries=dict(A=nodes[a], B=nodes[b]), parent_candidates=[]))
        report, case = saved_cases[record["experiment"], record["case_id"]]
        pair["parent_candidates"].append(dict(experiment=report["experiment"],
            case_id=case["id"], prompt_id=report["prompt_id"], settings=report["settings"],
            query=qid, candidate=dict(id=cid, name=name, matched_wording=word, cosine=score),
            resolution="subject_vector_fallback", query_encoding_id=encoding,
            lookup=provider.metadata, receipt=case["receipt"]))
    resolution.update(alias_inspections_by_query=dict(inspections),
        candidates_by_query={qid: sorted(ids) for qid, ids in chosen.items()},
        unresolved_guides=[r for r in resolution["guides"] if r["status"] == "unresolved"],
        skipped_guides=[r for r in resolution["guides"] if r["status"] == "skipped"],
        nearest_neighbors=provider.metadata,
        exact_pairs_excluded_from_trial=[p["id"] for p in exact_pairs])
    return [pairs[key] for key in sorted(pairs)], nodes, resolution


def build_comparison_source(source_refs, reports, template, *, base=None, selected=None,
                            prior_reports=()):
    """Pack only resolved real-node pairs for ordinary five-way BCP verification."""
    if not isinstance(source_refs, dict) or set(source_refs) - {
            "schema_version", "inputs", "hierarchy", "judgments", "discoveries",
            "resolution", "subject_probe", "guide_probe", "prior_comparisons"}:
        raise ValueError("invalid parent-comparison source references")
    mode = source_refs.get("resolution", "exact_saved_wording_only")
    if mode not in {"exact_saved_wording_only", "subject_vector_fallback_only"}:
        raise ValueError("invalid parent-comparison resolution mode")
    if mode == "exact_saved_wording_only" and any(
            key in source_refs for key in ("subject_probe", "guide_probe", "prior_comparisons")):
        raise ValueError("vector references require subject-vector fallback mode")
    loaded, references, protected = bounded._read_sources({key: value for key, value in source_refs.items()
        if key in {"schema_version", "inputs", "hierarchy", "judgments", "discoveries"}}, base)
    if mode == "subject_vector_fallback_only":
        try:
            from .subject_matching_probe import load_subject_vectors
        except ImportError:
            from subject_matching_probe import load_subject_vectors
        batches = {}
        for key in ("subject_probe", "guide_probe"):
            if not isinstance(source_refs.get(key), str) or not source_refs[key]:
                raise ValueError("vector fallback requires subject_probe and guide_probe")
            path = (Path(base or ".") / source_refs[key]).resolve()
            vectors, receipt, hashes = load_subject_vectors(path)
            protected.update(hashes)
            references[key] = dict(path=str(path), protected_sha256=hashes)
            batches[key] = vectors, receipt
        candidate_vectors, candidate_receipt = batches["subject_probe"]
        guide_vectors, guide_receipt = batches["guide_probe"]
        for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model",
                    "runtime", "dimensions", "device", "note_batch_size"):
            if candidate_receipt.get(key) != guide_receipt.get(key):
                raise ValueError(f"SSE identity mismatch between guide and saved subject vectors: {key}")
        for key, vector in candidate_vectors.items():
            if key in guide_vectors and guide_vectors[key] != vector:
                raise ValueError("conflicting saved vectors for the same subject")
        pairs, nodes, resolution = resolve_vector_guides(loaded["inputs"], loaded["hierarchy"],
            reports, references, {**candidate_vectors, **guide_vectors},
            history=loaded.get("judgments"), prior_reports=prior_reports)
    else:
        pairs, nodes, resolution = resolve_exact_guides(loaded["inputs"], loaded["hierarchy"],
            reports, references, history=loaded.get("judgments"))
    for report in [*reports, *prior_reports]:
        _protect_report(report, protected)
    cases = bounded._pack_comparisons(pairs, nodes, template, references)
    if selected is not None:
        if set(selected) - {case["id"] for case in cases}:
            raise ValueError("unknown parent-comparison case requested")
        cases = [case for case in cases if case["id"] in selected]
    preparation = dict(phase="parent_comparisons", source=references, pairs=pairs,
        reference_policy=bounded.REFERENCE_POLICY, resolution=mode,
        max_candidates_per_query=3, max_alias_inspections_per_query=32,
        ancestry_max_operations=2048, max_pairs=bounded.MAX_PAIRS,
        max_input_tokens=bounded.MAX_INPUT_TOKENS, tokenizer="o200k_base", **resolution)
    return cases, protected, preparation
