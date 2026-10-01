"""Offline sizing of one draft parent-guide pass; no inference or new vectors."""

from collections import defaultdict
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import resource
import sys
import time

try:
    from .bounded_hierarchy_build import _load, _budget
    from .bounded_hierarchy_candidates import _validate_graph, compact_entries
    from .bounded_hierarchy_sizing import comparison_capacity_bound
    from .bounded_hierarchy_workflow import MAX_INPUT_TOKENS
    from .experiment_inputs import digest, render
    from . import experiment as workflow
except ImportError:
    from bounded_hierarchy_build import _load, _budget
    from bounded_hierarchy_candidates import _validate_graph, compact_entries
    from bounded_hierarchy_sizing import comparison_capacity_bound
    from bounded_hierarchy_workflow import MAX_INPUT_TOKENS
    from experiment_inputs import digest, render
    import experiment as workflow


PARENT_GUIDE_SCHEMA = dict(type="object", additionalProperties=False, required=["queries"],
    properties=dict(queries=dict(type="array", minItems=1, maxItems=16, items=dict(
        type="object", additionalProperties=False, required=["id", "parents"], properties=dict(
            id=dict(type="string", pattern=r"^S[0-9]{4}$"),
            parents=dict(type="array", maxItems=3, uniqueItems=True,
                         items=dict(type="string", minLength=1, maxLength=160)))))))


def pack_parent_guide_requests(inputs, hierarchy, template, *, max_queries=16,
                               max_input_tokens=MAX_INPUT_TOKENS):
    """Create source-bound generic cases containing only compact query evidence."""
    import tiktoken

    if len(inputs["subjects"]) > 5000:
        raise ValueError("parent-guide measurement is limited to 5000 SP entries")
    if type(max_queries) is not int or not 1 <= max_queries <= 16:
        raise ValueError("parent-guide query limit must be one through 16")
    if type(max_input_tokens) is not int or not 1 <= max_input_tokens <= MAX_INPUT_TOKENS:
        raise ValueError("parent-guide input-token limit must be one through 4000")
    if not isinstance(template, str) or template.count("{INPUT_JSON}") != 1:
        raise ValueError("parent-guide prompt requires exactly one INPUT_JSON placeholder")
    _, groups, _, _ = _validate_graph(inputs, hierarchy)
    references = {q: compact_entries(inputs, g) for q, g in groups.items()}
    by_post = defaultdict(list)
    for q in sorted(groups):
        by_post[inputs["subjects"][groups[q][0]]["note_short_id"]].append(q)
    source = dict(inputs_sha256=digest(inputs), hierarchy_sha256=digest(hierarchy))
    encoding = tiktoken.get_encoding("o200k_base")

    def prepare(post, queries, page):
        payload = dict(queries=[dict(id=q, entries=references[q]) for q in queries])
        variables = dict(INPUT_JSON=json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        tokens = len(encoding.encode(render(template, variables)))
        return dict(id=f"PCPv3-{post}-{page:03d}", inputs=variables, evidence=dict(
            source_post=post, queries=list(queries), query_entries={q: references[q] for q in queries},
            original_members={q: groups[q] for q in queries}, source=source, input_tokens=tokens))

    cases = []
    for post, queries in sorted(by_post.items()):
        page, pending = 1, []
        for query in queries:
            trial = prepare(post, pending + [query], page)
            if pending and (len(pending) == max_queries or
                            trial["evidence"]["input_tokens"] > max_input_tokens):
                cases.append(prepare(post, pending, page))
                page += 1
                pending = []
                trial = prepare(post, [query], page)
            if trial["evidence"]["input_tokens"] > max_input_tokens:
                raise ValueError(f"query {query} exceeds {max_input_tokens} rendered input tokens")
            pending.append(query)
        if pending:
            cases.append(prepare(post, pending, page))
    return cases


def _distribution(values):
    values = sorted(values)
    if not values:
        return dict(total=0, min=0, max=0, mean=0, p95=0)
    return dict(total=sum(values), min=values[0], max=values[-1], mean=sum(values) / len(values),
                p95=values[math.ceil(.95 * len(values)) - 1])


def measure_build(build, destination, *, prompt, prompt_id="PCPv3"):
    """Size a separate prospective pass from frozen sources, without preparing jobs."""
    started = time.perf_counter()
    build, destination, prompt = Path(build).resolve(), Path(destination).resolve(), Path(prompt).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    if not isinstance(prompt_id, str) or not prompt_id.strip():
        raise ValueError("versioned parent-guide prompt ID required")
    manifest_path = build / "bounded-build.json"
    protected = {str(manifest_path): hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    _, plan = _load(build)
    budget_path = build / "budget.json"
    protected[str(budget_path)] = hashlib.sha256(budget_path.read_bytes()).hexdigest()
    budget = _budget(build, plan)
    if not isinstance(plan.get("export"), str):
        raise ValueError("saved build has no hierarchy export")
    snapshot = Path(plan["export"])
    export_manifest = snapshot / "manifest.json"
    protected[str(export_manifest)] = hashlib.sha256(export_manifest.read_bytes()).hexdigest()
    manifest = workflow.read(export_manifest)
    if manifest.get("schema_version") != 1 or set(manifest.get("files", {})) != {
            "results.json", "categories.json", "provenance.json", "summary.json"}:
        raise ValueError("saved hierarchy export is incomplete")
    for name, expected in manifest["files"].items():
        path = snapshot / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"saved hierarchy export changed: {name}")
        protected[str(path)] = expected
    input_path = Path(plan["spec"]["inputs"])
    measured = hashlib.sha256(input_path.read_bytes()).hexdigest()
    if measured != plan["protected_sha256"][str(input_path)]:
        raise ValueError("saved original SP inputs changed")
    protected[str(input_path)] = measured
    inputs = workflow.read(input_path)
    if len(inputs["subjects"]) > 5000:
        raise ValueError("parent-guide measurement is limited to 5000 SP entries")
    hierarchy = workflow.read(snapshot / "results.json")
    comparison_prompt = Path(plan["spec"]["prompts"]["comparison"]["path"])
    measured = hashlib.sha256(comparison_prompt.read_bytes()).hexdigest()
    if measured != plan["protected_sha256"][str(comparison_prompt)]:
        raise ValueError("saved comparison prompt changed")
    protected[str(comparison_prompt)] = measured
    protected[str(prompt)] = hashlib.sha256(prompt.read_bytes()).hexdigest()
    code_sha256 = {}
    for name in ("parent_guide_measurement.py", "bounded_hierarchy_candidates.py",
                 "bounded_hierarchy_sizing.py", "bounded_hierarchy_workflow.py", "experiment.py",
                 "bounded_hierarchy_build.py", "experiment_inputs.py", "extraction_pipeline.py"):
        path = Path(__file__).with_name(name).resolve()
        code_sha256[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    protected.update(code_sha256)
    requirements = Path(__file__).with_name("bounded-hierarchy-v1") / "requirements.txt"
    protected[str(requirements.resolve())] = hashlib.sha256(requirements.read_bytes()).hexdigest()
    cases = pack_parent_guide_requests(inputs, hierarchy, prompt.read_text())
    nodes = {f"S{min(g):04d}": compact_entries(inputs, g) for g in hierarchy["groups"]}
    capacity = comparison_capacity_bound(nodes, comparison_prompt.read_text(), None)
    if capacity["guaranteed_pairs_per_request"] < 1:
        raise ValueError("cannot certify verification requests within the token limit")
    count = len(nodes)
    pair_bound = min(3 * count, count * (count - 1) // 2)
    verification = math.ceil(pair_bound / capacity["guaranteed_pairs_per_request"])
    first_attempts = len(cases) + verification
    discovery_tokens = sum(c["evidence"]["input_tokens"] for c in cases)
    input_ceiling = discovery_tokens + verification * MAX_INPUT_TOKENS
    remaining = budget["limit"] - budget["used"]
    if sys.platform.startswith("linux"):
        peak_rss = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                            if line.startswith("VmHWM:")))
        rss_source = "/proc/self/status VmHWM"
    else:
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (
            1024 if sys.platform == "darwin" else 1)
        rss_source = "getrusage RUSAGE_SELF"
    result = dict(schema_version=1, measurement_id="PGMv1", status="draft_offline_measurement",
        inference_attempts=0, new_vectors=0, supplementary_passes=1,
        source_build=str(build), source_snapshot=str(snapshot), source_build_plan_sha256=digest(plan),
        protected_sha256=protected, code_sha256=code_sha256, prompt_id=prompt_id,
        guide_prompt_sha256=protected[str(prompt)], response_schema=PARENT_GUIDE_SCHEMA,
        comparison_prompt_id=plan["spec"]["prompts"]["comparison"]["id"],
        source_runner=plan["spec"]["runner"], node_count=count, sp_entry_count=len(inputs["subjects"]),
        maximum_sp_entries=5000, small_corpus_measurement_only=True,
        archive_loading_note="Saved build plan, export and SP inputs are loaded in memory; no all-pairs enumeration.",
        process_peak_rss_kib=peak_rss, process_peak_rss_source=rss_source,
        total_seconds=time.perf_counter() - started,
        discovery_requests=len(cases), rendered_input_tokens=_distribution(
            [c["evidence"]["input_tokens"] for c in cases]),
        queries_per_request=_distribution([len(c["evidence"]["queries"]) for c in cases]),
        maximum_parent_guides=3 * count, maximum_name_unicode_characters=160,
        maximum_resolved_candidates_per_query=3, maximum_unique_resolved_pairs=pair_bound,
        prospective_sse_encodings_upper=3 * count, actual_resolution_and_sse_work_unknown=True,
        creates_no_nodes=True, extra_pcpv2_requests=0, comparison_capacity=capacity,
        exact_verification_requests_unknown=True, maximum_verification_requests=verification,
        maximum_first_attempt_requests=first_attempts,
        maximum_attempts_with_one_retry=2 * first_attempts,
        maximum_rendered_input_tokens_first_attempt=input_ceiling,
        maximum_rendered_input_tokens_with_one_retry=2 * input_ceiling,
        tokenizer="o200k_base", tokenizer_library_version=version("tiktoken"),
        token_counts_are_rendered_proxy_not_provider_billing=True,
        output_and_reasoning_token_ceiling=None,
        output_ceiling_reason="Guide strings are length-bounded; saved settings impose no total output/reasoning-token cap.",
        existing_budget=budget, remaining_attempts=remaining,
        within_remaining_first_attempt_budget=first_attempts <= remaining,
        within_remaining_budget_with_one_retry_each=2 * first_attempts <= remaining,
        existing_quota_unchanged=True, source_build_finished=plan["status"] == "finished",
        queries_at_existing_nomination_limit=sum(plan["quota"].get(q, 0) >=
            plan["spec"]["max_nominations_per_reference"] for q in nodes),
        requires_new_versioned_pass_authorization=True)
    for path, expected in protected.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("source changed during parent-guide measurement")
    destination.mkdir(parents=True)
    (destination / ".gitignore").write_text("*\n")
    workflow.write(destination / "report.json", result)
    return result
