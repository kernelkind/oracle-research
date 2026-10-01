"""Publish a source-bound supplementary hierarchy without changing its build.

Only the shared runner's complete, receipt-validated BCPv5 experiments supply
additional judgments. Historical comparisons, including negative answers,
remain intact; graph deferrals are recorded rather than repaired.
"""

from copy import deepcopy
from collections import Counter, defaultdict, deque
from pathlib import Path

try:
    from . import bounded_hierarchy_build as build_workflow
    from . import bounded_hierarchy_workflow as bounded
    from . import experiment as workflow
    from . import experiment_inputs as adapters
    from . import extraction_pipeline as engine
    from .bounded_hierarchy_graph import apply_relations, audit_neither, export_hierarchy
    from .parent_guide_workflow import _protect_report
except ImportError:
    import bounded_hierarchy_build as build_workflow
    import bounded_hierarchy_workflow as bounded
    import experiment as workflow
    import experiment_inputs as adapters
    import extraction_pipeline as engine
    from bounded_hierarchy_graph import apply_relations, audit_neither, export_hierarchy
    from parent_guide_workflow import _protect_report


EXPORT_FILES = {"results.json", "categories.json", "provenance.json", "summary.json"}
EXPORT_SUMMARY_FIELDS = {"masks", "comparisons", "underlying_links", "browsing_links",
                         "browsing_links_omitted", "browsing_ancestry_preserved"}


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


def _navigation(categories):
    nodes = {node["node_id"]: node for node in categories["nodes"]}
    parents = defaultdict(set)
    remaining = {identifier: len(set(node["children"])) for identifier, node in nodes.items()}
    memberships = {identifier: set(node["note_ids"]) for identifier, node in nodes.items()}
    for identifier, node in nodes.items():
        for child in node["children"]:
            parents[child].add(identifier)
    pending = deque(sorted(identifier for identifier, count in remaining.items() if not count))
    completed = 0
    while pending:
        child = pending.popleft()
        completed += 1
        for parent in sorted(parents[child]):
            memberships[parent].update(memberships[child])
            remaining[parent] -= 1
            if not remaining[parent]:
                pending.append(parent)
    if completed != len(nodes):
        raise ValueError("browsing graph has a cycle or missing child")
    memberships = {identifier: frozenset(posts) for identifier, posts in memberships.items()}
    posts = memberships.__getitem__
    root = nodes[categories["root_node_id"]]
    return nodes, posts, dict(roots=len(root["children"]),
        displayed_roots_min_notes_2=sum(len(posts(child)) >= 2 for child in root["children"]))


def _route_changes(before, after):
    before_nodes, before_posts, _ = _navigation(before)
    after_nodes, after_posts, _ = _navigation(after)
    changed = []
    for identifier in sorted(before_nodes.keys() - {before["root_node_id"]}):
        added = sorted(after_posts(identifier) - before_posts(identifier))
        removed = sorted(before_posts(identifier) - after_posts(identifier))
        if added or removed:
            changed.append(dict(node=identifier, label=after_nodes[identifier]["label"],
                before_posts=len(before_posts(identifier)), after_posts=len(after_posts(identifier)),
                added_posts=added, removed_posts=removed))
    def edges(nodes):
        return {(identifier, child) for identifier, node in nodes.items()
                if identifier != before["root_node_id"] for child in node["children"]}
    old_edges, new_edges = edges(before_nodes), edges(after_nodes)
    return dict(changed_reachability=changed, added_browsing_links=sorted(new_edges - old_edges),
                removed_browsing_links=sorted(old_edges - new_edges))


def compare_parent_policies(snapshot, output):
    """Offline fixed-membership comparison; never alter a source or call a model.

    This small-snapshot diagnostic reconstructs SP-only starting links rather
    than privileging teacher edges accumulated in earlier build passes.
    """
    snapshot, output = Path(snapshot).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("comparison output already exists")
    if snapshot in output.parents:
        raise ValueError("comparison output must be outside the source export")
    protected = {}
    _protect(protected, snapshot / "manifest.json")
    manifest = workflow.read(snapshot / "manifest.json")
    if manifest.get("schema_version") != 1 or set(manifest.get("files", {})) != EXPORT_FILES:
        raise ValueError("a complete source hierarchy export is required")
    for name, expected in manifest["files"].items():
        _protect(protected, snapshot / name, expected)
    evidence = workflow.read(snapshot / "provenance.json")
    baseline = evidence["baseline"]
    published = workflow.read(snapshot / "results.json")
    source_summary = workflow.read(snapshot / "summary.json")
    # The exporter adds browsing edges and six summary fields to its original
    # application. Remove those additions to verify the original binding.
    source_application = dict(results={key: value for key, value in published.items()
                                      if key != "browsing_edges"},
        mapping=evidence["mapping"], applied=evidence["applied"], deferred=evidence["deferred"],
        stats={key: value for key, value in source_summary.items() if key not in EXPORT_SUMMARY_FIELDS})
    if manifest.get("snapshot_binding") != adapters.digest(dict(application=source_application,
                                                                 provenance=baseline)):
        raise ValueError("source snapshot binding differs")
    input_path = Path(baseline["spec"]["inputs"]).resolve()
    source = Path(baseline["spec"]["source"]).resolve()
    if source in output.parents:
        raise ValueError("comparison output must be outside the source corpus")
    pinned = baseline["protected_sha256"]
    if str(input_path) not in pinned:
        raise ValueError("original SP input is not protected")
    _protect(protected, input_path, pinned[str(input_path)])
    inputs = workflow.read(input_path)
    if len(inputs["subjects"]) > 5000:
        raise ValueError("offline parent-policy comparison is limited to 5000 SP entries")
    if any(evidence[key] != inputs[original] for key, original in (
            ("subjects", "subjects"), ("posts", "posts"), ("original_edges", "edges"))):
        raise ValueError("source export differs from original SP evidence")
    for name in ("masked-posts.json", "vector-map.json"):
        path = source / name
        expected = evidence["protected_sha256"].get(str(path))
        if not expected:
            raise ValueError("source corpus is not protected")
        _protect(protected, path, expected)
    groups, owners = published["groups"], published["member_to_group"]
    sp_edges = sorted({(owners[a], owners[b]) for a, b in inputs["edges"] if owners[a] != owners[b]})
    seed = dict(experiment_id="fixed-membership-parent-replay-v1", groups=deepcopy(groups),
                member_to_group=list(owners), edges=[list(edge) for edge in sp_edges])
    originals = baseline["comparisons"]
    # Keep full historical inputs/receipts in the hash-bound original export,
    # rather than copying rendered batches into every new snapshot again.
    judgments = []
    for index, judgment in enumerate(originals):
        if not judgment.get("receipt"):
            raise ValueError("saved judgment has no receipt")
        judgments.append(dict(id=judgment["id"], A=judgment["A"], B=judgment["B"],
            answer=deepcopy(judgment["answer"]), receipt=deepcopy(judgment["receipt"]),
            source_index=index, source_provenance=str(snapshot / "provenance.json")))
    work_budget = baseline["spec"]["work_budget"]
    descriptor = dict(schema_version=1, workflow="fixed-membership-parent-policy-v1",
        source_snapshot=str(snapshot), source_input=str(input_path), source=str(source),
        protected_sha256=protected, comparisons=judgments,
        fixed_membership_sha256=adapters.digest(dict(groups=groups, member_to_group=owners)),
        seed="mapped original SP links only", work_budget=work_budget,
        inference_calls=0, implementation_sha256={str(Path(__file__).resolve()):
                                                engine._sha256_file(Path(__file__))})
    _verify(protected)
    bundles, applications, audits = {}, {}, {}
    for policy in ("binding", "diagnostic"):
        application = apply_relations(inputs, seed, judgments, work_budget=work_budget,
            freeze_membership=True, cross_pair_neither=policy)
        if (application["results"]["groups"] != groups
                or application["results"]["member_to_group"] != owners):
            raise ValueError("parent replay changed fixed memberships")
        audits[policy] = audit_neither(application, judgments, work_budget=work_budget)
        applications[policy] = application
        _verify(protected)
        bundles[policy] = export_hierarchy(output / policy, inputs, application, source=source,
            provenance=dict(descriptor, policy=policy))
    # Attach original SP and accepted teacher contributors to every witness hop.
    for policy, audit in audits.items():
        contributors = defaultdict(list)
        for a, b in inputs["edges"]:
            if owners[a] != owners[b]:
                contributors[owners[a], owners[b]].append(dict(original_sp_entries=[a, b]))
        for row in applications[policy]["applied"]:
            judgment = row["judgment"]
            relation = judgment["answer"]["relation"]
            if relation not in {"a_parent_of_b", "b_parent_of_a"}:
                continue
            a, b = owners[int(judgment["A"][1:])], owners[int(judgment["B"][1:])]
            if relation == "b_parent_of_a":
                a, b = b, a
            contributors[a, b].append(dict(judgment_index=judgment["source_index"]))
        indices = {f"S{group[0]:04d}": index for index, group in enumerate(groups)}
        for row in audit["contradictions"]:
            row["edge_sources"] = [dict(parent=a, child=b,
                contributors=contributors[indices[a], indices[b]])
                for a, b in zip(row["path"], row["path"][1:])]
    published_categories = workflow.read(snapshot / "categories.json")
    comparison = dict(descriptor,
        published_navigation=_navigation(published_categories)[2],
        binding_navigation=_navigation(bundles["binding"]["categories"])[2],
        diagnostic_navigation=_navigation(bundles["diagnostic"]["categories"])[2],
        published_vs_binding=_route_changes(published_categories, bundles["binding"]["categories"]),
        binding_vs_diagnostic=_route_changes(bundles["binding"]["categories"],
                                             bundles["diagnostic"]["categories"]),
        binding_neither=audits["binding"], diagnostic_neither=audits["diagnostic"],
        deferrals={policy: dict(Counter(row["reason"] for row in application["deferred"]))
                   for policy, application in applications.items()})
    _verify(protected)
    workflow.write(output / "comparison.json", comparison)
    workflow.write(output / "manifest.json", dict(schema_version=1,
        protected_sha256=protected, files={name: engine._sha256_file(output / name)
            for name in ("comparison.json", "binding/manifest.json", "diagnostic/manifest.json")}))
    return dict(output=str(output), inference_calls=0, membership_fixed=True,
        comparisons=len(judgments), binding=comparison["binding_navigation"],
        diagnostic=comparison["diagnostic_navigation"],
        binding_contradictions=len(audits["binding"]["contradictions"]),
        diagnostic_contradictions=len(audits["diagnostic"]["contradictions"]),
        changed_nodes=len(comparison["binding_vs_diagnostic"]["changed_reachability"]))
