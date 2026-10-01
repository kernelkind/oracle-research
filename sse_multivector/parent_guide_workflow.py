"""Source-bound parent-name nominations and exact-only diagnostic lookup.

Preparation never performs inference, creates nodes or changes a hierarchy.
Unmatched names remain unresolved rather than receiving a semantic substitute.
"""

from collections import defaultdict
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


def build_comparison_source(source_refs, reports, template, *, base=None, selected=None):
    """Pack only resolved real-node pairs for ordinary five-way BCP verification."""
    if not isinstance(source_refs, dict) or set(source_refs) - {
            "schema_version", "inputs", "hierarchy", "judgments", "discoveries"}:
        raise ValueError("invalid parent-comparison source references")
    loaded, references, protected = bounded._read_sources(source_refs, base)
    pairs, nodes, resolution = resolve_exact_guides(loaded["inputs"], loaded["hierarchy"],
        reports, references, history=loaded.get("judgments"))
    for report in reports:
        _protect_report(report, protected)
    cases = bounded._pack_comparisons(pairs, nodes, template, references)
    if selected is not None:
        if set(selected) - {case["id"] for case in cases}:
            raise ValueError("unknown parent-comparison case requested")
        cases = [case for case in cases if case["id"] in selected]
    preparation = dict(phase="parent_comparisons", source=references, pairs=pairs,
        reference_policy=bounded.REFERENCE_POLICY, resolution="exact_saved_wording_only",
        max_candidates_per_query=3, max_alias_inspections_per_query=32,
        ancestry_max_operations=2048, max_pairs=bounded.MAX_PAIRS,
        max_input_tokens=bounded.MAX_INPUT_TOKENS, tokenizer="o200k_base", **resolution)
    return cases, protected, preparation
