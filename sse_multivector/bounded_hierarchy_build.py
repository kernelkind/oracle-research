"""Finite, resumable bounded hierarchy builds through the shared experiment runner.

Prepare is offline. Run invokes only frozen child experiments, sharing one
persistent launch budget. Source snapshots, partial answers, and failed or
unrun cases remain visible; no failed answer is guessed or retried here.
"""

from copy import deepcopy
from pathlib import Path

try:
    from . import experiment as workflow
    from . import experiment_inputs as adapters
    from . import extraction_pipeline as engine
    from .bounded_hierarchy_candidates import compact_entries
    from .bounded_hierarchy_graph import apply_relations, export_hierarchy
    from .bounded_hierarchy_workflow import extract_comparisons, DISCOVERY_SCHEMA, COMPARISON_SCHEMA
except ImportError:
    import experiment as workflow
    import experiment_inputs as adapters
    import extraction_pipeline as engine
    from bounded_hierarchy_candidates import compact_entries
    from bounded_hierarchy_graph import apply_relations, export_hierarchy
    from bounded_hierarchy_workflow import extract_comparisons, DISCOVERY_SCHEMA, COMPARISON_SCHEMA


MANIFEST = "bounded-build.json"
POLICY_VERSION = "bounded-hierarchy-v1"


def _is_attempt_allowance_error(message):
    """Recognize only the runner's exact aggregate attempt-limit diagnostic."""
    diagnostic = message.split("; partial results:", 1)[0]
    prefix = "unresolved prompt cases: "
    return (diagnostic.startswith(prefix)
            and all(part == "new-attempt allowance exhausted"
                    for part in diagnostic[len(prefix):].split(", ")))


def _is_case_failure_error(message, report):
    """Accept only exact runner diagnostics for receipt-backed case failures.

    Match complete error strings: a case's own error can contain commas.
    Unknown causes are not retried; they need not prevent independent queries.
    Fatal provider and preflight errors remain build-wide stops.
    """
    if any(case['status'] not in ('valid', 'failed') for case in report['cases']):
        return False
    failed = [case for case in report['cases'] if case['status'] == 'failed']
    if not failed or any(not case.get('receipt') or case.get('failure_kind') == 'provider_fatal'
                         or not isinstance(case.get('error'), str) for case in failed):
        return False
    expected = {case.get('job_id', case['id']): case['error'] for case in failed}
    if len(expected) != len(failed):
        return False
    suffix = f"; partial results: {Path(report['experiment']) / 'report.json'}"
    diagnostic = message.removesuffix(suffix)
    prefix = 'unresolved prompt cases: '
    if not diagnostic.startswith(prefix):
        return False
    offset = len(prefix)
    while offset < len(diagnostic):
        end = diagnostic.find(': ', offset)
        identifier = diagnostic[offset:end] if end >= 0 else ''
        error = expected.pop(identifier, None)
        if error is None:
            return False
        part = f'{identifier}: {error}'
        if not diagnostic.startswith(part, offset):
            return False
        offset += len(part)
        if offset != len(diagnostic):
            if not diagnostic.startswith(', ', offset):
                return False
            offset += 2
            if offset == len(diagnostic):
                return False
    return not expected


def _atomic(path, value):
    engine._atomic_write(Path(path), engine._canonical_json_bytes(value))


def _save(directory, plan):
    _atomic(directory / MANIFEST, dict(sha256=adapters.digest(plan), plan=plan))


def _load(directory):
    directory = Path(directory).resolve()
    envelope = workflow.read(directory / MANIFEST)
    plan = envelope["plan"]
    if envelope["sha256"] != adapters.digest(plan):
        raise ValueError("bounded build manifest hash differs")
    return directory, plan


def _verify(plan):
    for path, expected in plan["protected_sha256"].items():
        if engine._sha256_file(Path(path)) != expected:
            raise ValueError(f"bounded build source changed: {path}")
    for path, expected in plan["code_sha256"].items():
        if engine._sha256_file(Path(path)) != expected:
            raise ValueError(f"bounded build implementation changed: {path}")


def _budget(directory, plan):
    budget = workflow.read(directory / "budget.json")
    if (budget.get("schema_version") != 1 or budget.get("limit") != plan["spec"]["max_model_calls"]
            or type(budget.get("used")) is not int or not 0 <= budget["used"] <= budget["limit"]):
        raise ValueError("bounded build launch budget differs from frozen policy")
    return budget


def _resolve_spec(path):
    path = Path(path).resolve()
    spec = workflow.read(path)
    required = {"schema_version", "id", "inputs", "hierarchy", "subject_probe", "source",
                "prompts", "runner", "max_model_calls", "max_passes",
                "max_nominations_per_reference", "work_budget"}
    if set(spec) != required or spec["schema_version"] != 1:
        raise ValueError("invalid bounded hierarchy build spec")
    for key, maximum in (("max_model_calls", 2000), ("max_passes", 3),
                         ("max_nominations_per_reference", 9)):
        if type(spec[key]) is not int or not 1 <= spec[key] <= maximum:
            raise ValueError(f"{key} must be one through {maximum}")
    if type(spec["work_budget"]) is not int or spec["work_budget"] < 0:
        raise ValueError("nonnegative graph work budget required")
    runner = spec["runner"]
    if runner.get("provider") != "openai-codex" or runner.get("model") != "gpt-6.1-sol":
        raise ValueError("bounded build requires gpt-6.1-sol subscription without fallback")
    spec = deepcopy(spec)
    for key in ("inputs", "hierarchy", "subject_probe", "source"):
        spec[key] = str(workflow.resolve(spec[key], path.parent))
    if set(spec["prompts"]) != {"discovery", "comparison"}:
        raise ValueError("discovery and comparison prompts required")
    for phase, identifier in (("discovery", "PCPv2"), ("comparison", "BCPv5")):
        prompt = spec["prompts"][phase]
        if set(prompt) != {"id", "path"} or prompt["id"] != identifier:
            raise ValueError(f"{phase} requires {identifier}")
        prompt["path"] = str(workflow.resolve(prompt["path"], path.parent))
    for key in ("runner_binary", "auth_file"):
        if runner.get(key):
            spec["runner"][key] = str(workflow.resolve(runner[key], path.parent))
    return path, spec


def _entries(inputs, hierarchy):
    return {f"S{group[0]:04d}": compact_entries(inputs, group) for group in hierarchy["groups"]}


def _unchanged_judgments(inputs, hierarchy, judgments):
    """Skip pairs only while their compact reference inputs are unchanged."""
    entries = _entries(inputs, hierarchy)
    owners = hierarchy["member_to_group"]
    ids = [f"S{group[0]:04d}" for group in hierarchy["groups"]]
    result = []
    for judgment in judgments:
        reference = judgment.get("reference_entries", {})
        current = {side: entries[ids[owners[int(judgment[side][1:])]]]
                   for side in ("A", "B")}
        if all(reference.get(side) == current[side] for side in ("A", "B")):
            result.append(judgment)
    return result


def _query_nodes(plan, hierarchy, number):
    ids = [f"S{group[0]:04d}" for group in hierarchy["groups"]]
    if number == 1:
        proposed = set(ids)
    else:
        nonroots = {b for _, b in hierarchy["edges"]}
        proposed = {identifier for i, identifier in enumerate(ids) if i not in nonroots}
        if number == 2:
            proposed.update(plan["passes"][-1].get("changed_nodes", []))
    quota = plan["quota"]
    maximum = plan["spec"]["max_nominations_per_reference"]
    return sorted(identifier for identifier in proposed if identifier in ids
                  and quota.get(identifier, 0) + 3 <= maximum)


def _prepare_child(directory, plan, phase, kind):
    child = directory / "passes" / f"{phase['number']:02d}" / kind
    if (child / "experiment.json").exists():
        return child
    refs = dict(schema_version=1, inputs=plan["spec"]["inputs"],
                hierarchy=phase["hierarchy_input"])
    if kind == "discovery":
        refs.update(subject_probe=plan["spec"]["subject_probe"],
                    query_nodes=phase["queries"], judgments=phase["judgments_input"])
    else:
        refs.update(discoveries=[phase["discovery"]], allow_incomplete=True)
    parent = child.parent
    parent.mkdir(parents=True, exist_ok=True)
    references = parent / f"{kind}-source.json"
    specification = parent / f"{kind}-spec.json"
    _atomic(references, refs)
    runner = dict(plan["spec"]["runner"], output_schema=DISCOVERY_SCHEMA
                  if kind == "discovery" else COMPARISON_SCHEMA)
    _atomic(specification, dict(schema_version=1, prompt=plan["spec"]["prompts"][kind],
        dataset=dict(adapter="bounded_discovery" if kind == "discovery" else "bounded_comparisons",
                     path=str(references)), runner=runner))
    args = workflow.parser().parse_args(["prepare", str(child), "--spec", str(specification),
                                        "--history-root", str(directory / "passes")])
    args.publication_role = 'internal'
    workflow.prepare(args)
    return child


def _start_pass(directory, plan):
    number = len(plan["passes"]) + 1
    hierarchy = workflow.read(plan["current_hierarchy"])
    inputs = workflow.read(plan["spec"]["inputs"])
    queries = _query_nodes(plan, hierarchy, number)
    if not queries:
        return None
    parent = directory / "passes" / f"{number:02d}"
    parent.mkdir(parents=True, exist_ok=True)
    judgments = parent / "prior-judgments.json"
    _atomic(judgments, dict(subjects=inputs["subjects"],
                           comparisons=_unchanged_judgments(inputs, hierarchy, plan["comparisons"])))
    phase = dict(number=number, status="discovery", queries=queries,
                 hierarchy_input=plan["current_hierarchy"], judgments_input=str(judgments),
                 discovery=str(parent / "discovery"), comparison=None, errors=[],
                 unresolved=[], collected=[])
    plan["passes"].append(phase)
    for query in queries:
        plan["quota"][query] = plan["quota"].get(query, 0) + 3
    _save(directory, plan)
    _prepare_child(directory, plan, phase, "discovery")
    return phase


def prepare_build(specpath, destination):
    """Freeze one build and prepare its first ordinary experiment offline."""
    path, spec = _resolve_spec(specpath)
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("bounded build destination already exists")
    inputs, hierarchy = workflow.read(Path(spec["inputs"])), workflow.read(Path(spec["hierarchy"]))
    initial = apply_relations(inputs, hierarchy, [], work_budget=spec["work_budget"])
    protected_paths = [path, Path(spec["inputs"]), Path(spec["hierarchy"]),
                       *(Path(p["path"]) for p in spec["prompts"].values()),
                       Path(spec["source"]) / "masked-posts.json",
                       Path(spec["source"]) / "vector-map.json"]
    protected = {str(p): engine._sha256_file(p) for p in protected_paths}
    code = [Path(__file__), Path(__file__).with_name("bounded_hierarchy_graph.py"),
            Path(__file__).with_name("bounded_hierarchy_candidates.py"),
            Path(__file__).with_name("bounded_hierarchy_workflow.py")]
    destination.mkdir(parents=True)
    (destination / ".gitignore").write_text("*\n")
    initial_path = destination / "initial" / "results.json"
    initial_path.parent.mkdir()
    _atomic(initial_path, initial["results"])
    _atomic(destination / "budget.json", dict(schema_version=1, limit=spec["max_model_calls"], used=0))
    plan = dict(schema_version=1, id=spec["id"], policy_version=POLICY_VERSION, spec=spec,
                protected_sha256=protected, code_sha256={str(p.resolve()): engine._sha256_file(p) for p in code},
                status="prepared", stop_reason=None, passes=[], quota={}, comparisons=[],
                current_hierarchy=str(initial_path), application=initial, exports=[], export=None)
    _save(destination, plan)
    phase = _start_pass(destination, plan)
    if phase:
        child, _, _ = workflow.load(Path(phase["discovery"]))
        plan["protected_sha256"].update(child["sources"])
        _save(destination, plan)
    return report_build(destination)


def _unresolved(report, kind):
    return [dict(phase=kind, id=case["id"], status=case["status"])
            for case in report["cases"] if case["status"] != "valid"]


def _changed(before, after):
    """Changed current nodes include merged membership or changed adjacency."""
    before_ids = [f"S{group[0]:04d}" for group in before["groups"]]
    after_ids = [f"S{group[0]:04d}" for group in after["groups"]]
    old_groups = {identifier: group for identifier, group in zip(before_ids, before["groups"])}
    changed = {identifier for identifier, group in zip(after_ids, after["groups"])
               if old_groups.get(identifier) != group}
    old_edges = {(before_ids[a], before_ids[b]) for a, b in before["edges"]}
    new_edges = {(after_ids[a], after_ids[b]) for a, b in after["edges"]}
    changed.update(node for edge in old_edges ^ new_edges for node in edge if node in after_ids)
    return sorted(changed)


def _export(directory, plan, label):
    output = directory / "exports" / label
    inputs = workflow.read(Path(plan["spec"]["inputs"]))
    provenance = dict(build_id=plan["id"], policy_version=POLICY_VERSION,
                      spec=plan["spec"], protected_sha256=plan["protected_sha256"],
                      passes=plan["passes"], comparisons=plan["comparisons"],
                      original_hierarchy=plan["spec"]["hierarchy"],
                      budget=_budget(directory, plan), status=plan["status"], stop_reason=plan["stop_reason"])
    if output.exists():
        # Export may have completed immediately before a manifest write was
        # interrupted. Reuse only the exact complete, hash-bound snapshot.
        snapshot = workflow.read(output / "manifest.json")
        binding = adapters.digest(dict(application=plan["application"], provenance=provenance))
        if snapshot.get("schema_version") != 1 or snapshot.get("snapshot_binding") != binding:
            raise ValueError("existing export differs from resumable build snapshot")
        if set(snapshot.get("files", {})) != {"results.json", "categories.json", "provenance.json", "summary.json"}:
            raise ValueError("existing export is incomplete")
        for name, expected in snapshot["files"].items():
            if engine._sha256_file(output / name) != expected:
                raise ValueError(f"existing export changed: {output / name}")
    else:
        export_hierarchy(output, inputs, plan["application"],
                         source=plan["spec"]["source"], provenance=provenance)
    plan["exports"].append(str(output))
    plan["export"] = str(output)
    plan["export_status"] = dict(status=plan["status"], stop_reason=plan["stop_reason"])
    plan["protected_sha256"].update({str(output / name): expected
                                     for name, expected in workflow.read(output / "manifest.json")["files"].items()})
    plan["current_hierarchy"] = str(output / "results.json")


def run_build(directory, max_new_attempts=None, runner_upgrade_reason=None):
    """Advance frozen finite passes; all child launches share budget.json."""
    directory = Path(directory).resolve()
    with workflow.locked(directory):
        directory, plan = _load(directory)
        _verify(plan)
        if (plan["status"] == "finished"
                or (plan["status"] == "unfinished" and plan["stop_reason"] == "partial_failure")):
            # Non-provider failures need an explicit repair/re-preparation,
            # not a fresh pass that conceals an unresolved earlier answer.
            return report_build(directory)
        if max_new_attempts is not None and (type(max_new_attempts) is not int or max_new_attempts < 0):
            raise ValueError("max_new_attempts must be nonnegative")
        used_at_start = _budget(directory, plan)["used"]

        def remaining():
            budget = _budget(directory, plan)
            global_remaining = budget["limit"] - budget["used"]
            if max_new_attempts is None:
                return global_remaining
            return min(global_remaining, max_new_attempts - (budget["used"] - used_at_start))

        def execute(child, phase, kind):
            result = workflow.report(child)
            if any(case["status"] == "unrun" for case in result["cases"]) and remaining() > 0:
                try:
                    workflow.run(child, max_new_attempts=remaining(),
                        runner_upgrade_reason=runner_upgrade_reason,
                        attempt_budget_path=directory / "budget.json")
                except engine.RunnerError as error:
                    phase["errors"].append(dict(phase=kind, message=str(error)))
                result = workflow.report(child)
            return result

        plan["status"] = "running"
        plan["stop_reason"] = None
        while True:
            phase = plan["passes"][-1] if plan["passes"] else None
            if phase is None or phase["status"] == "done":
                if len(plan["passes"]) >= plan["spec"]["max_passes"]:
                    plan.update(status="finished", stop_reason="pass_limit")
                    break
                phase = _start_pass(directory, plan)
                if phase is None:
                    plan.update(status="finished", stop_reason="query_quota")
                    break
            if phase["status"] == "discovery":
                discovery = _prepare_child(directory, plan, phase, "discovery")
                report = execute(discovery, phase, "discovery")
                phase["unresolved"] = _unresolved(report, "discovery")
                pending = any(case["status"] == "unrun" for case in report["cases"])
                if pending and not phase["errors"]:
                    plan.update(status="unfinished", stop_reason="model_call_budget"
                                if _budget(directory, plan)["used"] >= _budget(directory, plan)["limit"]
                                else "invocation_limit")
                    break
                nominated = any(q["candidates"] for case in report["cases"] if case["status"] == "valid"
                                for q in case["parsed"]["queries"])
                phase["status"] = "comparison" if nominated else "apply"
                if nominated:
                    phase["comparison"] = str(_prepare_child(directory, plan, phase, "comparison"))
                _save(directory, plan)
            if phase["status"] == "comparison":
                child = Path(phase["comparison"])
                report = execute(child, phase, "comparison")
                phase["unresolved"] = [r for r in phase["unresolved"] if r["phase"] != "comparison"]
                phase["unresolved"].extend(_unresolved(report, "comparison"))
                for case in report["cases"]:
                    if case["status"] != "valid" or not case.get("receipt"):
                        continue
                    key = case["id"] + ":" + case["receipt"]["record_sha256"]
                    if key in phase["collected"]:
                        continue
                    for comparison in extract_comparisons(case, case["parsed"]):
                        comparison.update(receipt=case["receipt"], experiment=report["experiment"],
                                          settings=report["settings"], prompt_id=report["prompt_id"])
                        plan["comparisons"].append(comparison)
                    phase["collected"].append(key)
                phase["comparison_pending"] = any(c["status"] == "unrun" for c in report["cases"])
                phase["status"] = "apply"
                _save(directory, plan)
            if phase["status"] == "apply":
                inputs = workflow.read(Path(plan["spec"]["inputs"]))
                before = workflow.read(Path(plan["current_hierarchy"]))
                application = apply_relations(inputs, before, plan["comparisons"],
                                              work_budget=plan["spec"]["work_budget"])
                phase["changed_nodes"] = sorted(set(phase.get("changed_nodes", []))
                                                | set(_changed(before, application["results"])))
                plan["application"] = application
                phase["status"] = "comparison" if phase.get("comparison_pending") else "done"
                if phase.get("comparison_pending") and not phase["errors"]:
                    plan.update(status="unfinished", stop_reason="model_call_budget"
                                if _budget(directory, plan)["used"] >= _budget(directory, plan)["limit"]
                                else "invocation_limit")
                elif phase["errors"] or phase["unresolved"]:
                    plan.update(status="unfinished", stop_reason="partial_failure")
                elif not phase["changed_nodes"]:
                    plan.update(status="finished", stop_reason="no_graph_change")
                label = f"pass-{phase['number']:02d}-{len(plan['exports']) + 1:03d}"
                _export(directory, plan, label)
                _save(directory, plan)
                if plan["status"] != "running":
                    break
        if (plan["export"] is None or plan.get("export_status") !=
                dict(status=plan["status"], stop_reason=plan["stop_reason"])):
            _export(directory, plan, f"final-{len(plan['exports']) + 1:03d}")
        _save(directory, plan)
        return report_build(directory)


def report_build(directory):
    """Return build status without model requests or changing its artifacts."""
    directory, plan = _load(directory)
    _verify(plan)
    budget = _budget(directory, plan)
    unresolved = []
    for phase in plan["passes"]:
        if phase["status"] == "discovery":
            child = Path(phase["discovery"])
            if (child / "experiment.json").exists():
                unresolved.extend(_unresolved(workflow.report(child), "discovery"))
        else:
            unresolved.extend(phase["unresolved"])
    return dict(id=plan["id"], status=plan["status"], stop_reason=plan["stop_reason"],
                model_calls=budget["used"], max_model_calls=budget["limit"],
                passes=len(plan["passes"]), max_passes=plan["spec"]["max_passes"],
                subjects=plan["application"]["stats"]["subjects"],
                nodes=plan["application"]["stats"]["nodes"],
                roots=plan["application"]["stats"]["roots"],
                comparisons=len(plan["comparisons"]),
                deferred=len(plan["application"]["deferred"]),
                unresolved_cases=len(unresolved), unresolved=unresolved,
                errors=[error for phase in plan["passes"] for error in phase["errors"]],
                export=plan["export"])
