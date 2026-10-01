"""Publish a source-bound supplementary hierarchy without changing its build.

Only the shared runner's complete, receipt-validated BCPv5 experiments supply
additional judgments. Historical comparisons, including negative answers,
remain intact; graph deferrals are recorded rather than repaired.
"""

from copy import deepcopy
from pathlib import Path

try:
    from . import bounded_hierarchy_build as build_workflow
    from . import bounded_hierarchy_workflow as bounded
    from . import experiment as workflow
    from . import experiment_inputs as adapters
    from . import extraction_pipeline as engine
    from .bounded_hierarchy_graph import apply_relations, export_hierarchy
    from .parent_guide_workflow import _protect_report
except ImportError:
    import bounded_hierarchy_build as build_workflow
    import bounded_hierarchy_workflow as bounded
    import experiment as workflow
    import experiment_inputs as adapters
    import extraction_pipeline as engine
    from bounded_hierarchy_graph import apply_relations, export_hierarchy
    from parent_guide_workflow import _protect_report


EXPORT_FILES = {"results.json", "categories.json", "provenance.json", "summary.json"}


def _protect(protected, path, expected=None):
    path = Path(path).resolve()
    actual = engine._sha256_file(path)
    previous = protected.get(str(path))
    if ((expected is not None and actual != expected)
            or (previous is not None and previous != actual)):
        raise ValueError(f"protected source changed: {path}")
    protected[str(path)] = actual
    return actual


def _verify(protected):
    for name, expected in protected.items():
        if engine._sha256_file(Path(name)) != expected:
            raise ValueError(f"protected source changed: {name}")


def _baseline(build, protected):
    build = Path(build).resolve()
    _protect(protected, build / build_workflow.MANIFEST)
    _, plan = build_workflow._load(build)
    if plan.get("schema_version") != 1 or plan.get("status") != "finished" or not plan.get("export"):
        raise ValueError("a finished bounded build with a saved export is required")
    snapshot = Path(plan["export"]).resolve()
    hierarchy_path = snapshot / "results.json"
    if Path(plan["current_hierarchy"]).resolve() != hierarchy_path:
        raise ValueError("bounded build current hierarchy differs from its final export")
    for name, expected in plan["protected_sha256"].items():
        _protect(protected, name, expected)
    spec = plan["spec"]
    required = [Path(spec["inputs"]).resolve(), Path(spec["hierarchy"]).resolve(), hierarchy_path,
                Path(spec["source"]).resolve() / "masked-posts.json",
                Path(spec["source"]).resolve() / "vector-map.json"]
    if any(str(path) not in plan["protected_sha256"] for path in required):
        raise ValueError("bounded build source is not protected")
    _protect(protected, build / "budget.json")
    budget = build_workflow._budget(build, plan)
    _protect(protected, snapshot / "manifest.json")
    manifest = workflow.read(snapshot / "manifest.json")
    if manifest.get("schema_version") != 1 or set(manifest.get("files", {})) != EXPORT_FILES:
        raise ValueError("saved hierarchy export is incomplete")
    for name, expected in manifest["files"].items():
        if plan["protected_sha256"].get(str(snapshot / name)) != expected:
            raise ValueError("saved hierarchy export differs from protected build hashes")
        _protect(protected, snapshot / name, expected)
    evidence = workflow.read(snapshot / "provenance.json")
    archived = evidence.get("baseline")
    if (not isinstance(archived, dict) or archived.get("build_id") != plan["id"]
            or archived.get("spec") != spec or archived.get("comparisons") != plan["comparisons"]
            or archived.get("status") != plan["status"]
            or archived.get("stop_reason") != plan["stop_reason"]):
        raise ValueError("saved hierarchy export does not bind the original build")
    binding = adapters.digest(dict(application=plan["application"], provenance=archived))
    if manifest.get("snapshot_binding") != binding:
        raise ValueError("saved hierarchy export snapshot binding differs")
    inputs = workflow.read(required[0])
    hierarchy = workflow.read(hierarchy_path)
    if ({k: v for k, v in hierarchy.items() if k != "browsing_edges"}
            != plan["application"]["results"]):
        raise ValueError("saved hierarchy export results differ from the bounded build")
    if any(evidence.get(key) != inputs[source] for key, source in (
            ("posts", "posts"), ("subjects", "subjects"), ("original_edges", "edges"))):
        raise ValueError("saved hierarchy export original SP evidence differs")
    references = dict(inputs=dict(path=str(required[0]), sha256=protected[str(required[0])]),
                      hierarchy=dict(path=str(hierarchy_path), sha256=protected[str(hierarchy_path)]))
    # Historical implementation hashes describe the archived build. They are
    # not an assertion that all current helper files still have those bytes.
    return plan, inputs, hierarchy, references, budget, manifest


def _extract(report, references, nodes):
    if report.get("adapter") != "bounded_parent_comparisons" or report.get("prompt_id") != "BCPv5":
        raise ValueError("supplementary export requires BCPv5 bounded_parent_comparisons experiments")
    if not report["cases"] or any(case["status"] != "valid" or not case.get("receipt")
                                  for case in report["cases"]):
        raise ValueError("supplementary export requires complete valid receipted comparisons")
    judgments = []
    for case in report["cases"]:
        evidence = case["evidence"]
        source = evidence.get("source", {})
        if any(source.get(key) != references[key] for key in ("inputs", "hierarchy")):
            raise ValueError("comparison source differs from the frozen bounded build")
        if evidence.get("reference_policy") != bounded.REFERENCE_POLICY:
            raise ValueError("comparison reference policy differs from the bounded build")
        payload = bounded._parse(case["inputs"]["INPUT_JSON"])
        bounded._fields(payload, {"nodes", "pairs"}, "comparison input")
        supplied = {}
        for node in payload["nodes"]:
            bounded._fields(node, {"id", "entries"}, "comparison node")
            identifier = node["id"]
            if identifier not in nodes or identifier in supplied or node["entries"] != nodes[identifier]:
                raise ValueError("comparison compact references differ from current original SP entries")
            supplied[identifier] = node["entries"]
        pairs = evidence["pairs"]
        inventory = [{key: pair[key] for key in ("id", "A", "B")} for pair in pairs]
        if (inventory != payload["pairs"] or not 1 <= len(pairs) <= bounded.MAX_PAIRS
                or len({pair["id"] for pair in pairs}) != len(pairs)
                or set(supplied) != {pair[side] for pair in pairs for side in ("A", "B")}):
            raise ValueError("comparison evidence differs from its supplied pair inventory")
        for pair in pairs:
            if (pair["A"] == pair["B"] or any(pair["reference_entries"].get(side)
                    != nodes[pair[side]] for side in ("A", "B"))):
                raise ValueError("comparison compact references differ from current original SP entries")
        for judgment in bounded.extract_comparisons(case, case["parsed"]):
            judgment.update(receipt=deepcopy(case["receipt"]), experiment=report["experiment"],
                            settings=deepcopy(report["settings"]), prompt_id=report["prompt_id"])
            judgments.append(judgment)
    return judgments


def _identity(judgment):
    a, b = judgment["A"], judgment["B"]
    references = judgment["reference_entries"]
    answer = deepcopy(judgment["answer"])
    if a > b:
        a, b = b, a
        references = dict(A=references["B"], B=references["A"])
        answer["relation"] = {"a_parent_of_b": "b_parent_of_a",
                              "b_parent_of_a": "a_parent_of_b"}.get(answer["relation"], answer["relation"])
    return (a, b, adapters.digest(references)), answer


def _combine(original, additional):
    # Preserve every historical row verbatim, even if the archived graph
    # deferred it. Only exact repeated additional answers are deduplicated.
    combined = deepcopy(original)
    meanings, exact = {}, {}
    for index, judgment in enumerate(combined):
        key, answer = _identity(judgment)
        meanings.setdefault(key, set()).add(answer["relation"])
        exact.setdefault((key, adapters.digest(answer)), index)
    duplicates = []
    for judgment in additional:
        key, answer = _identity(judgment)
        if key in meanings and meanings[key] != {answer["relation"]}:
            raise ValueError(f"conflicting duplicate comparison receipts: {key[0]}-{key[1]}")
        answer_key = key, adapters.digest(answer)
        if answer_key in exact:
            duplicates.append(dict(comparison_index=exact[answer_key], judgment=deepcopy(judgment)))
            continue
        exact[answer_key] = len(combined)
        meanings.setdefault(key, set()).add(answer["relation"])
        combined.append(deepcopy(judgment))
    return combined, duplicates


def export_parent_guides(build, directories, output):
    """Validate saved comparisons and publish a fresh lossless aggregate export.

    The original build, final hierarchy and launch budget are never rewritten.
    Incomplete reports cannot be presented as a final supplementary export.
    """
    build, output = Path(build).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("export output already exists")
    directories = [Path(directory).resolve() for directory in directories]
    if not directories or len(set(directories)) != len(directories):
        raise ValueError("distinct comparison experiment directories are required")
    protected = {}
    plan, inputs, hierarchy, references, budget, manifest = _baseline(build, protected)
    nodes = bounded._node_entries(inputs, hierarchy)
    additional, experiments = [], []
    for directory in directories:
        report = workflow.report(directory)
        additional.extend(_extract(report, references, nodes))
        report_protected = {}
        _protect_report(report, report_protected)
        for name, expected in report_protected.items():
            if name in protected and protected[name] != expected:
                raise ValueError(f"protected source changed: {name}")
            protected[name] = expected
        experiments.append(dict(experiment=report["experiment"], prompt_id=report["prompt_id"],
            adapter=report["adapter"], settings=deepcopy(report["settings"]),
            summary=deepcopy(report["summary"]),
            receipts=[dict(case_id=case["id"], receipt=deepcopy(case["receipt"]))
                      for case in report["cases"]]))
    comparisons, duplicates = _combine(plan["comparisons"], additional)
    _verify(protected)
    application = apply_relations(inputs, hierarchy, comparisons, work_budget=plan["spec"]["work_budget"])
    provenance = dict(schema_version=1, build_id=plan["id"], workflow="parent-guide-export-v1",
        status="finished", source_build=str(build), base_export=plan["export"],
        base_export_manifest=manifest, spec=deepcopy(plan["spec"]),
        historical_code_sha256=deepcopy(plan["code_sha256"]), budget=budget,
        original_comparisons=len(plan["comparisons"]), additional_comparisons=len(comparisons) - len(plan["comparisons"]),
        comparisons=comparisons, duplicate_comparisons=duplicates, experiments=experiments,
        protected_sha256=protected, implementation_sha256={
            str(Path(__file__).resolve()): engine._sha256_file(Path(__file__))})
    _verify(protected)
    bundle = export_hierarchy(output, inputs, application, source=plan["spec"]["source"], provenance=provenance)
    return dict(bundle["summary"], output=str(output), source_build=str(build),
        original_comparisons=provenance["original_comparisons"],
        additional_comparisons=provenance["additional_comparisons"], duplicate_comparisons=len(duplicates))
