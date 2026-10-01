"""Source-bound bounded hierarchy discovery and batched pair comparisons.

Preparation never performs inference or changes the saved SP hierarchy. Discovery
nominations are not judgments; only complete, separately verified pair answers
can be extracted for the hierarchy workflow.
"""

import hashlib
import json
from pathlib import Path

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


RELATIONS = (
    "equivalent", "a_parent_of_b", "b_parent_of_a", "neither", "uncertain",
)
MAX_NOMINATIONS = 3
MAX_PAIRS = 16
MAX_INPUT_TOKENS = 4000
REFERENCE_POLICY = "earliest SP entry; earliest different wording, otherwise different context"


def _response_object(properties):
    return dict(type="object", additionalProperties=False,
                required=list(properties), properties=properties)


DISCOVERY_SCHEMA = _response_object({"queries": dict(type="array", maxItems=16,
    items=_response_object({"id": dict(type="string"), "candidates": dict(type="array",
        maxItems=MAX_NOMINATIONS, items=_response_object({"id": dict(type="string"),
            "reason": dict(type="string")}))}))})
COMPARISON_SCHEMA = _response_object({"comparisons": dict(type="array", maxItems=MAX_PAIRS,
    items=_response_object({"id": dict(type="string"),
        "relation": dict(type="string", enum=list(RELATIONS)),
        "reason": dict(type="string")}))})


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _fields(value, expected, description):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"expected {description} fields: {', '.join(sorted(expected))}")


def _parse(raw):
    return json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)


def _reason(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("reason must be a nonempty string")


def validate_discovery(case, raw):
    """Require every query once, with zero through three eligible nominations."""
    payload = _parse(case["inputs"]["INPUT_JSON"])
    query_ids = {q["id"] for q in payload["queries"]}
    candidate_ids = {c["id"] for c in payload["candidates"]}
    excluded = payload["excluded_candidates"]
    value = _parse(raw)
    _fields(value, {"queries"}, "discovery response")
    if not isinstance(value["queries"], list):
        raise ValueError("queries must be an array")
    seen = set()
    for query in value["queries"]:
        _fields(query, {"id", "candidates"}, "query nomination")
        qid = query["id"]
        if not isinstance(qid, str) or qid not in query_ids or qid in seen:
            raise ValueError("unknown or duplicate query ID")
        seen.add(qid)
        candidates = query["candidates"]
        if not isinstance(candidates, list) or len(candidates) > MAX_NOMINATIONS:
            raise ValueError("each query permits at most three nominations")
        nominated = set()
        for candidate in candidates:
            _fields(candidate, {"id", "reason"}, "candidate nomination")
            cid = candidate["id"]
            if not isinstance(cid, str) or cid not in candidate_ids or cid in nominated:
                raise ValueError("unknown or duplicate candidate ID")
            if cid == qid or cid in excluded.get(qid, []):
                raise ValueError("excluded candidate cannot be nominated")
            nominated.add(cid)
            _reason(candidate["reason"])
    if seen != query_ids:
        raise ValueError("discovery must return every supplied query exactly once")
    return value


def validate_comparisons(case, raw):
    """Require exactly one of BCPv4's five judgments for every supplied pair."""
    payload = _parse(case["inputs"]["INPUT_JSON"])
    pair_ids = {p["id"] for p in payload["pairs"]}
    value = _parse(raw)
    _fields(value, {"comparisons"}, "comparison response")
    if not isinstance(value["comparisons"], list):
        raise ValueError("comparisons must be an array")
    seen = set()
    for comparison in value["comparisons"]:
        _fields(comparison, {"id", "relation", "reason"}, "pair comparison")
        cid = comparison["id"]
        if not isinstance(cid, str) or cid not in pair_ids or cid in seen:
            raise ValueError("unknown or duplicate comparison ID")
        if comparison["relation"] not in RELATIONS:
            raise ValueError("invalid comparison relation")
        _reason(comparison["reason"])
        seen.add(cid)
    if seen != pair_ids:
        raise ValueError("comparison must return every supplied pair exactly once")
    return value


def _read_reference(ref, base):
    expected = None
    if isinstance(ref, dict):
        _fields(ref, {"path", "sha256"}, "source reference")
        expected, ref = ref["sha256"], ref["path"]
    if not isinstance(ref, str) or not ref:
        raise ValueError("source reference path must be a nonempty string")
    path = (base / ref).resolve()
    raw = path.read_bytes()
    measured = hashlib.sha256(raw).hexdigest()
    if expected is not None and expected != measured:
        raise ValueError(f"protected source changed: {path}")
    return _parse(raw), dict(path=str(path), sha256=measured)


def _read_sources(refs, base=None):
    base = Path(base or ".").resolve()
    if not isinstance(refs, dict) or not {"inputs", "hierarchy"} <= set(refs):
        raise ValueError("bounded hierarchy source requires inputs and hierarchy references")
    allowed = {"schema_version", "inputs", "hierarchy", "subject_probe", "judgments",
               "query_nodes", "discoveries", "allow_incomplete", "retrieval_backend"}
    version = refs.get("schema_version", 1)
    if set(refs) - allowed or type(version) is not int or version != 1:
        raise ValueError("invalid bounded hierarchy source references")
    loaded, references, protected = {}, {}, {}
    for key in ("inputs", "hierarchy", "judgments"):
        if key not in refs:
            continue
        loaded[key], references[key] = _read_reference(refs[key], base)
        protected[references[key]["path"]] = references[key]["sha256"]
    try:
        from .experiment_inputs import prepare_subject_pairs
    except ImportError:
        from experiment_inputs import prepare_subject_pairs
    prepare_subject_pairs(dict(inputs=loaded["inputs"], hierarchy=loaded["hierarchy"],
                               pairs=[], source=references))
    return loaded, references, protected


def create_discovery_source(source_refs, template, *, base=None, selected=None):
    """Prepare bounded discovery directly from saved source and vector references."""
    try:
        from .bounded_hierarchy_candidates import build_discovery, HNSWSubjectNeighbors, ExactSubjectNeighbors
        from .subject_matching_probe import load_subject_vectors
    except ImportError:
        from bounded_hierarchy_candidates import build_discovery, HNSWSubjectNeighbors, ExactSubjectNeighbors
        from subject_matching_probe import load_subject_vectors

    loaded, references, protected = _read_sources(source_refs, base)
    backend = source_refs.get("retrieval_backend", "hnsw")
    if backend not in ("hnsw", "exact"):
        raise ValueError("retrieval_backend must be hnsw or exact")
    probe = source_refs.get("subject_probe")
    if not isinstance(probe, str) or not probe:
        raise ValueError("discovery requires a saved subject_probe reference")
    probe = (Path(base or ".") / probe).resolve()
    vectors, receipt, vector_sources = load_subject_vectors(probe)
    protected.update(vector_sources)
    references["subject_probe"] = dict(path=str(probe), receipt=receipt)
    judged = []
    if "judgments" in loaded:
        history = loaded["judgments"]
        if history.get("subjects") != loaded["inputs"]["subjects"]:
            raise ValueError("saved judgment subjects differ from source SP entries")
        judged = [(c["A"], c["B"]) for c in history["comparisons"]]
    provider = (HNSWSubjectNeighbors if backend == "hnsw" else ExactSubjectNeighbors)(
        loaded["inputs"], loaded["hierarchy"], vectors)
    result = build_discovery(loaded["inputs"], loaded["hierarchy"], vectors, template,
        judged_pairs=judged, query_nodes=source_refs.get("query_nodes"), nearest_neighbors=provider)
    cases = result["cases"]
    for case in cases:
        case["evidence"]["source"] = references
        case["evidence"]["reference_policy"] = REFERENCE_POLICY
    if selected is not None:
        if set(selected) - {c["id"] for c in cases}:
            raise ValueError("unknown discovery case requested")
        cases = [c for c in cases if c["id"] in selected]
    preparation = dict(workflow="HG100-SOL01", phase="discovery", source=references,
                       reference_policy=REFERENCE_POLICY, provenance=result["provenance"],
                       stats=result["stats"])
    return cases, protected, preparation


def _node_entries(inputs, hierarchy):
    try:
        from .bounded_hierarchy_candidates import compact_entries
    except ImportError:
        from bounded_hierarchy_candidates import compact_entries
    return {f"S{members[0]:04d}": compact_entries(inputs, members)
            for members in hierarchy["groups"]}


def _discovery_pairs(inputs, hierarchy, reports, references, *, allow_incomplete=False):
    """Retain all proofs while deduplicating unordered nominated node pairs."""
    nodes = _node_entries(inputs, hierarchy)
    groups = {f"S{members[0]:04d}": members for members in hierarchy["groups"]}
    pairs, query_nominations, unresolved = {}, {}, []
    for report in reports:
        if report.get("prompt_id") != "PCPv2":
            raise ValueError("comparison preparation requires PCPv2 discovery reports")
        for case in report["cases"]:
            evidence = case["evidence"]
            source = evidence.get("source", {})
            if any(source.get(k) != references[k] for k in ("inputs", "hierarchy")):
                raise ValueError("discovery source differs from current hierarchy inputs")
            payload = _parse(case["inputs"]["INPUT_JSON"])
            for query in payload["queries"]:
                if query["id"] not in nodes or query["entries"] != nodes[query["id"]]:
                    raise ValueError("discovery query entries differ from original SP references")
            for candidate in payload["candidates"]:
                cid = candidate["id"]
                if cid not in groups:
                    raise ValueError("discovery candidate is not in the saved hierarchy")
                expected = list(dict.fromkeys(inputs["subjects"][i]["subject"]
                                              for i in sorted(groups[cid])))[:2]
                if candidate["subjects"] != expected:
                    raise ValueError("discovery candidate wordings differ from original SP entries")
            failure = None
            if case.get("status") != "valid" or not case.get("receipt"):
                failure = (case.get("status", "unrun") if case.get("status") != "valid"
                           else "invalid_receipt")
            else:
                try:
                    parsed = validate_discovery(case, compact(case["parsed"]))
                except (ValueError, KeyError):
                    if not allow_incomplete:
                        raise
                    failure = "malformed"
            if failure is not None:
                if not allow_incomplete:
                    raise ValueError("discovery requires complete valid saved answers")
                unresolved.append(dict(experiment=report["experiment"], case_id=case["id"],
                                       status=failure, queries=[q["id"] for q in payload["queries"]]))
                continue
            for query in parsed["queries"]:
                qid = query["id"]
                accumulated = query_nominations.setdefault(qid, set())
                accumulated.update(c["id"] for c in query["candidates"])
                if len(accumulated) > MAX_NOMINATIONS:
                    raise ValueError("query has more than three distinct nominations across discovery pages")
                for candidate in query["candidates"]:
                    a, b = sorted((qid, candidate["id"]))
                    pair = pairs.setdefault((a, b), dict(id=a + "-" + b, A=a, B=b,
                        reference_entries=dict(A=nodes[a], B=nodes[b]), parent_candidates=[]))
                    pair["parent_candidates"].append(dict(
                        experiment=report["experiment"], case_id=case["id"],
                        prompt_id=report["prompt_id"], settings=report["settings"],
                        query=qid, candidate=candidate, receipt=case["receipt"]))
    return [pairs[p] for p in sorted(pairs)], nodes, unresolved


def _pack_comparisons(pairs, nodes, template, references, *, max_pairs=MAX_PAIRS,
                      max_input_tokens=MAX_INPUT_TOKENS):
    try:
        from .experiment_inputs import render
    except ImportError:
        from experiment_inputs import render
    import tiktoken

    if type(max_pairs) is not int or not 1 <= max_pairs <= MAX_PAIRS:
        raise ValueError("comparison batches permit one through sixteen pairs")
    if type(max_input_tokens) is not int or not 1 <= max_input_tokens <= MAX_INPUT_TOKENS:
        raise ValueError("comparison input-token budget must be one through 4000")
    encoding = tiktoken.get_encoding("o200k_base")
    cases, pending = [], []

    def prepare(batch):
        ids = sorted({p[k] for p in batch for k in ("A", "B")})
        payload = dict(nodes=[dict(id=nid, entries=nodes[nid]) for nid in ids],
                       pairs=[{k: p[k] for k in ("id", "A", "B")} for p in batch])
        model_inputs = dict(INPUT_JSON=compact(payload))
        prompt = render(template, model_inputs)
        return model_inputs, prompt, len(encoding.encode(prompt))

    def publish(batch):
        model_inputs, _, count = prepare(batch)
        cases.append(dict(id=f"BCPv5-{len(cases) + 1:04d}", inputs=model_inputs,
                          evidence=dict(pairs=batch, source=references,
                          reference_policy=REFERENCE_POLICY, input_tokens=count,
                          tokenizer="o200k_base")))

    for pair in pairs:
        trial = [*pending, pair]
        if len(trial) > max_pairs or prepare(trial)[2] > max_input_tokens:
            if pending:
                publish(pending)
                pending = []
            if prepare([pair])[2] > max_input_tokens:
                raise ValueError(f"single comparison exceeds input-token budget: {pair['id']}")
        pending.append(pair)
    if pending:
        publish(pending)
    return cases


def _original_sp_source(inputs):
    """Validate saved original entry identities and local edges, not meanings."""
    try:
        from .experiment_inputs import prepare_subject_pairs
    except ImportError:
        from experiment_inputs import prepare_subject_pairs
    if (not isinstance(inputs, dict)
            or not all(isinstance(inputs.get(k), list) for k in ("posts", "subjects", "edges"))
            or not inputs["posts"] or not inputs["subjects"]):
        raise ValueError("original SP inputs require posts, subjects and edges")
    posts, short_ids = {}, set()
    for post in inputs["posts"]:
        if (not isinstance(post, dict)
                or any(not isinstance(post.get(k), str) or not post[k].strip()
                       for k in ("note_id", "note_short_id"))
                or not isinstance(post.get("text"), str)
                or post["note_id"] in posts or post["note_short_id"] in short_ids):
            raise ValueError("unique original source-post identities and text required")
        posts[post["note_id"]] = post
        short_ids.add(post["note_short_id"])
    subjects = inputs["subjects"]
    for subject in subjects:
        if (not isinstance(subject, dict)
                or not {"index", "subject", "context", "note_id", "note_short_id"} <= subject.keys()
                or not isinstance(subject["note_id"], str) or subject["note_id"] not in posts
                or subject["note_short_id"] != posts[subject["note_id"]]["note_short_id"]):
            raise ValueError("original SP entries must identify their saved source post")
    # Reuse the normal source/entry/edge checks without a saved global hierarchy.
    # This partition is only an identity view of the original SP entries.
    singleton = dict(groups=[[i] for i in range(len(subjects))],
                     member_to_group=list(range(len(subjects))), edges=inputs["edges"])
    prepare_subject_pairs(dict(inputs=inputs, hierarchy=singleton, pairs=[], source={}))
    edges = set()
    for edge in inputs["edges"]:
        if (edge[0] == edge[1] or tuple(edge) in edges
                or subjects[edge[0]]["note_id"] != subjects[edge[1]]["note_id"]):
            raise ValueError("distinct original SP edges within a source post required")
        edges.add(tuple(edge))
    return posts, edges


def build_sp_link_comparison_source(source_refs, template, *, base=None, selected=None,
                                    max_pairs=MAX_PAIRS, max_input_tokens=MAX_INPUT_TOKENS):
    """Check selected original local SP edges without global-node remapping."""
    _fields(source_refs, {"schema_version", "inputs", "original_sp_edges"},
            "original SP comparison source")
    if type(source_refs["schema_version"]) is not int or source_refs["schema_version"] != 1:
        raise ValueError("expected original SP comparison schema_version 1")
    source_ref = source_refs["inputs"]
    if isinstance(source_ref, dict):
        expected = source_ref.get("sha256")
        if (not isinstance(expected, str) or len(expected) != 64
                or any(character not in "0123456789abcdef" for character in expected)):
            raise ValueError("original SP hashed source requires a SHA256 digest")
    inputs, reference = _read_reference(source_refs["inputs"], Path(base or ".").resolve())
    posts, available = _original_sp_source(inputs)
    requested = source_refs["original_sp_edges"]
    if requested == "all":
        requested = [list(edge) for edge in sorted(available)]
    if not isinstance(requested, list) or not requested:
        raise ValueError("original_sp_edges must select source edges or 'all'")
    chosen = set()
    for edge in requested:
        if (not isinstance(edge, list) or len(edge) != 2
                or any(type(i) is not int for i in edge)
                or tuple(edge) not in available or tuple(edge) in chosen):
            raise ValueError("distinct directed original SP source edges required")
        chosen.add(tuple(edge))
    try:
        from .bounded_hierarchy_candidates import compact_entries
    except ImportError:
        from bounded_hierarchy_candidates import compact_entries
    nodes = {f"S{i:04d}": compact_entries(inputs, [i])
             for i in sorted({i for edge in chosen for i in edge})}
    pairs = []
    for a, b in sorted(chosen):
        A, B = f"S{a:04d}", f"S{b:04d}"
        pairs.append(dict(id=A + "-" + B, A=A, B=B,
            reference_entries=dict(A=nodes[A], B=nodes[B]), parent_candidates=[],
            original_sp_edge=[a, b]))
    references = dict(inputs=reference)
    cases = _pack_comparisons(pairs, nodes, template, references,
        max_pairs=max_pairs, max_input_tokens=max_input_tokens)
    for case in cases:
        indices = sorted({i for pair in case["evidence"]["pairs"]
                          for i in pair["original_sp_edge"]})
        post_ids = sorted({inputs["subjects"][i]["note_id"] for i in indices})
        case["evidence"].update(
            reference_policy="exact original SP entry; no global-node remapping",
            original_sp_edges=[p["original_sp_edge"] for p in case["evidence"]["pairs"]],
            subject_entries=[inputs["subjects"][i] for i in indices],
            source_posts=[posts[p] for p in post_ids])
    if selected is not None:
        if set(selected) - {case["id"] for case in cases}:
            raise ValueError("unknown comparison case requested")
        cases = [case for case in cases if case["id"] in selected]
    protected = {reference["path"]: reference["sha256"]}
    preparation = dict(phase="comparison", source_mode="original_sp_edges", source=references,
        reference_policy="exact original SP entry; no global-node remapping",
        original_sp_edges=[list(edge) for edge in sorted(chosen)], pairs=pairs,
        max_pairs=max_pairs, max_input_tokens=max_input_tokens, tokenizer="o200k_base")
    return cases, protected, preparation


def build_comparison_source(source_refs, discovery_reports, template, *, base=None,
                            selected=None, max_pairs=MAX_PAIRS,
                            max_input_tokens=MAX_INPUT_TOKENS, allow_incomplete=None):
    """Prepare actual nominated pairs from receipt-validated discovery reports."""
    loaded, references, protected = _read_sources(source_refs, base)
    if allow_incomplete is None:
        allow_incomplete = source_refs.get("allow_incomplete", False)
    if type(allow_incomplete) is not bool:
        raise ValueError("allow_incomplete must be a boolean")
    pairs, nodes, unresolved = _discovery_pairs(loaded["inputs"], loaded["hierarchy"],
        discovery_reports, references, allow_incomplete=allow_incomplete)
    for report in discovery_reports:
        directory = Path(report["experiment"]).resolve()
        path = directory / "experiment.json"
        protected[str(path)] = engine._sha256_file(path)
        envelope = engine._load_json(path, str(path))
        for name, expected in envelope["plan"].get("sources", {}).items():
            path = Path(name).resolve()
            actual = protected.get(str(path))
            if actual is None:
                actual = engine._sha256_file(path)
            if actual != expected:
                raise ValueError(f"protected discovery source changed: {path}")
            protected[str(path)] = actual
        for name, expected in envelope["plan"]["files"].items():
            path = directory / name
            actual = engine._sha256_file(path)
            if actual != expected:
                raise ValueError(f"protected discovery file changed: {path}")
            protected[str(path)] = actual
        for case in report["cases"]:
            if case.get("receipt"):
                path = Path(case["receipt"]["results_path"]).resolve()
                protected[str(path)] = engine._sha256_file(path)
    cases = _pack_comparisons(pairs, nodes, template, references,
                              max_pairs=max_pairs, max_input_tokens=max_input_tokens)
    if selected is not None:
        if set(selected) - {c["id"] for c in cases}:
            raise ValueError("unknown comparison case requested")
        cases = [c for c in cases if c["id"] in selected]
    preparation = dict(workflow="HG100-SOL01", phase="comparison", source=references,
                       reference_policy=REFERENCE_POLICY, pairs=pairs,
                       max_pairs=max_pairs, max_input_tokens=max_input_tokens,
                       tokenizer="o200k_base", allow_incomplete=allow_incomplete,
                       unresolved_discovery=unresolved)
    return cases, protected, preparation


def extract_comparisons(case, parsed):
    """Flatten verified batch answers without changing their evidence or meaning."""
    value = validate_comparisons(case, compact(parsed))
    answers = {p["id"]: p for p in value["comparisons"]}
    result = []
    for pair in case["evidence"]["pairs"]:
        answer = answers[pair["id"]]
        entries = pair["reference_entries"]
        model_inputs = {side: [{k: e[k] for k in ("subject", "context")}
                              for e in entries[side]] for side in ("A", "B")}
        result.append(dict(id=pair["id"], A=pair["A"], B=pair["B"],
            inputs=dict(INPUT_JSON=compact(model_inputs)),
            answer={k: answer[k] for k in ("relation", "reason")},
            reference_entries=entries, reference_policy=REFERENCE_POLICY,
            parent_candidates=pair["parent_candidates"], batch_case_id=case["id"],
            batch_inputs=case["inputs"]))
    return result
