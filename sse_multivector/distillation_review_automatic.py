"""Finish native distillation grades with bounded automatic final decisions.

The Oracle adapter owns dependencies and collection. The shared runner owns
request admission, execution, retries, cache warming and immutable receipts.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

from . import distillation_coverage_search as coverage
from . import extraction_pipeline as engine


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / "experiment-runner/bin/experiment-runner"
ROLES = {"required", "final_matching", "final_coverage"}


def prepare_source(source, base, *, preparation_context=None):
    """Project compact native requests while independently binding their sources."""
    engine._expect_fields(source, "automatic grading source", {"automatic_requests", "sources", "role"})
    if source["role"] not in ROLES or not isinstance(source["automatic_requests"], list):
        raise ValueError("invalid automatic grading requests")
    protected = source["sources"]
    if not isinstance(protected, dict):
        raise ValueError("automatic grading sources must be a hash mapping")
    cache = {} if preparation_context is None else preparation_context.setdefault("automatic_sources", {})
    for filename, expected in protected.items():
        path = engine._resolve_path(filename, "automatic grading source", Path(base))
        stamp = coverage._file_state(path)
        if cache.get(str(path)) != (expected, stamp):
            if engine._sha256_file(path) != expected:
                raise ValueError("automatic grading source changed: " + str(path))
            cache[str(path)] = (expected, stamp)
    cases = []
    for case in source["automatic_requests"]:
        if case.get("origin") == "mechanical" or "mechanical" in case:
            raise ValueError("automatic calls cannot replace trusted mechanical results")
        cases.append({key: case[key] for key in ("id", "inputs", "evidence")})
    return cases, protected, dict(automatic_role=source["role"], application_allowed=False)


def _configuration(request, runner_binary):
    from experiment_runner import experiment
    source = request.get("source_experiment")
    if source:
        plan, _, _ = experiment.load(Path(source))
        template = plan["prompt"]
        runner = dict(plan["runner"])
        adapter = plan["dataset"]["adapter"]
    else:
        directory = PROJECT / "sse_multivector/distillation-review-v1"
        identifier = request["prompt_id"]
        files = {"DSMv3": ("matching-prompt-v3.md", "matching-response-schema.json"),
            "DSSv2": ("support-prompt-v2.md", "boolean-response-schema.json"),
            "DSLv2": ("relationship-prompt-v2.md", "boolean-response-schema.json"),
            "DSLv4": ("relationship-prompt-v4.md", "boolean-response-schema.json"),
            "DCSv1": ("coverage-search-prompt-v1.md", "coverage-search-response-schema.json")}
        filename, schema = files[identifier]
        template = dict(id=identifier, source_path=str(directory / filename),
            text=(directory / filename).read_text())
        runner = {key: value for key, value in request.get("configuration", {}).items()
            if key in {"provider", "model", "reasoning_effort", "transport", "timeout_seconds",
                "max_output_tokens", "auth_file", "runner_binary"}}
        runner["output_schema_path"] = str(directory / schema)
        adapter = request["adapter"]
    for key in ("prompt_cache_key", "prompt_cache_prefix", "prompt_cache"):
        runner.pop(key, None)
    runner.setdefault("provider", "openai-codex")
    runner.setdefault("model", "gpt-6.1-sol")
    runner.setdefault("transport", "sse")
    runner.setdefault("reasoning_effort", "xhigh")
    runner.setdefault("timeout_seconds", 3600)
    runner.setdefault("auth_file", None)
    if request["role"] != "required":
        runner.update(provider="openai-codex", model="gpt-6.1-sol", reasoning_effort="xhigh", transport="sse")
    if runner_binary:
        runner["runner_binary"] = str(Path(runner_binary).resolve())
    return template, runner, adapter


def _request_key(request):
    case = request["case"]
    return (request["role"], request["prompt_id"], case["input_sha256"])


def _prepare_groups(requests, directory, state, report, context):
    from experiment_runner import experiment, inputs, prompt_cache
    groups = {}
    already = {tuple(key) for group in state["experiments"] for key in group["request_keys"]}
    for request in requests:
        if _request_key(request) in already:
            continue
        template, runner, adapter = _configuration(request, state.get("runner_binary"))
        # Preserve the original exact question; no prompt-development overrides.
        rendered = inputs.render(experiment.without_cache_marker(template["text"]), request["case"]["inputs"])
        if rendered != request["case"]["prompt"]:
            raise ValueError("automatic grading prompt differs from its native question")
        prefix, _ = inputs.template_prefix(template["text"], request["case"]["inputs"])
        cacheable = prompt_cache.prefix_policy(prefix)["eligible"]
        key = json.dumps([request["role"], template["id"], adapter, runner,
            prefix if cacheable else None], sort_keys=True)
        group = groups.setdefault(key, dict(template=template, runner=runner, adapter=adapter,
            role=request["role"], prefix=prefix if cacheable else None, requests=[]))
        group["requests"].append(request)
    prepared = []
    for group in groups.values():
        requests = group["requests"]
        name = f"batch-{len(state['experiments']) + 1:04}-{group['role']}"
        source_path = directory / "sources" / (name + ".json")
        experiment.write(source_path, dict(automatic_requests=[r["case"] for r in requests],
            sources=report["sources"], role=group["role"]))
        prompt_path = directory / "prompts" / (name + ".md")
        prompt_path.parent.mkdir(exist_ok=True)
        prompt_path.write_text(group["template"]["text"])
        spec = directory / "specs" / (name + ".json")
        experiment.write(spec, dict(schema_version=1,
            prompt=dict(id=group["template"]["id"], path=str(prompt_path)),
            dataset=dict(adapter=group["adapter"], path=str(source_path)), runner=group["runner"]))
        destination = directory / "experiments" / name
        arguments = ["prepare", str(destination), "--spec", str(spec), "--history-root",
            state.get("history_root") or str(directory)]
        # A final decision must be fresh; ordinary missing checks may reuse exact receipts.
        if group["role"] != "required":
            arguments.append("--repeat")
        cached = group["prefix"] is not None and len({r["case"]["input_sha256"] for r in requests}) > 1
        if cached:
            arguments.append("--prompt-cache")
        experiment.prepare(experiment.parser().parse_args(arguments),
            include_request_preview=False, preparation_context=context)
        entry = dict(path=str(destination), role=group["role"], prefix_cached=cached,
            request_keys=[list(_request_key(r)) for r in requests], status="prepared")
        state["experiments"].append(entry)
        prepared.append(entry)
    return prepared


def _collect(directory, state, context):
    from experiment_runner import experiment
    completed = [entry for entry in state["experiments"] if entry["status"] == "complete"]
    output = directory / "collections" / f"collection-{state['collections'] + 1:04}.json"
    result = coverage.collect(Path(state["coverage"]), output, automatic=True,
        verification_experiments=state["verification_experiments"],
        required_experiments=state["required_experiments"] +
            [entry["path"] for entry in completed if entry["role"] == "required"],
        final_experiments=state["final_experiments"] +
            [entry["path"] for entry in completed if entry["role"] != "required"],
        collection_context=context, answer_ids=state.get("answer_ids"))
    state.update(collections=state["collections"] + 1, report=str(output),
        report_sha256=engine._sha256_file(output))
    return result


def prepare(coverage_directory, output, *, verification_experiments=None, required_experiments=None,
            final_experiments=None, answer_ids=None, runner_binary=None, history_root=None):
    """Freeze ready native batches without inference or changing historical groups."""
    from experiment_runner import experiment, project
    project.configure(PROJECT)
    directory = Path(output).expanduser().resolve()
    if directory.exists():
        raise ValueError("automatic grading output already exists")
    coverage_directory = Path(coverage_directory).expanduser().resolve()
    frozen_path = coverage_directory / "coverage-search.json"
    reference = dict(path=str(frozen_path), sha256=engine._sha256_file(frozen_path))
    if answer_ids:
        engine._validate_string_array(answer_ids, "automatic answer selection", allow_empty=False)
    directory.mkdir(parents=True)
    (directory / ".gitignore").write_text("*\n")
    state = dict(schema_version=1, coverage=str(coverage_directory), coverage_reference=reference,
        project_root=str(PROJECT), launcher=str(LAUNCHER), answer_ids=answer_ids,
        verification_experiments=[str(Path(p).resolve()) for p in verification_experiments or []],
        required_experiments=[str(Path(p).resolve()) for p in required_experiments or []],
        final_experiments=[str(Path(p).resolve()) for p in final_experiments or []],
        runner_binary=str(Path(runner_binary).resolve()) if runner_binary else None,
        history_root=str(Path(history_root).resolve()) if history_root else None,
        experiments=[], collections=0, status="prepared")
    context = {}
    result = _collect(directory, state, context)
    _prepare_groups(result["automatic_requests"], directory, state, result, context)
    state["initial_report"] = dict(path=state["report"], sha256=state["report_sha256"])
    experiment.write(directory / "automatic.json", state)
    experiment.write(directory / "automatic.complete.json", {
        "automatic.json": engine._sha256_file(directory / "automatic.json")})
    experiment.write(directory / "state.json", state)
    return dict(output=str(directory), status="prepared", inference_calls=0,
        experiments=state["experiments"], report=state["report"])


def run(directory):
    """Submit all ready batches, advance dependencies, and require final grades."""
    from experiment_runner import experiment, project
    project.configure(PROJECT)
    directory = Path(directory).expanduser().resolve()
    with experiment.locked(directory):
        frozen_path = directory / "automatic.json"
        if experiment.read(directory / "automatic.complete.json") != {
                "automatic.json": engine._sha256_file(frozen_path)}:
            raise ValueError("automatic grading preparation changed")
        frozen = experiment.read(frozen_path)
        state = experiment.read(directory / "state.json")
        for key in ("coverage", "coverage_reference", "project_root", "launcher", "answer_ids",
                "verification_experiments", "required_experiments", "final_experiments",
                "runner_binary", "history_root"):
            if state[key] != frozen[key]:
                raise ValueError("automatic grading execution binding changed: " + key)
        if state["project_root"] != str(PROJECT) or state["launcher"] != str(LAUNCHER):
            raise ValueError("automatic grading is bound to a different task checkout")
        if engine._sha256_file(Path(state["coverage_reference"]["path"])) != state["coverage_reference"]["sha256"]:
            raise ValueError("automatic grading coverage preparation changed")
        if state["status"] in {"complete", "failed"}:
            return dict(status=state["status"], report=state["report"], experiments=state["experiments"],
                **({"error": state["error"]} if state.get("error") else {}))
        if not frozen.get("initial_report") or state.get("initial_report") != frozen["initial_report"]:
            raise ValueError("automatic grading initial collection binding changed")
        report_path = Path(state["report"])
        expected = state.get("report_sha256")
        if str(report_path) == frozen["initial_report"]["path"]:
            expected = frozen["initial_report"]["sha256"]
        if not expected or engine._sha256_file(report_path) != expected:
            raise ValueError("automatic grading collection changed")
        active, context = {}, {}
        # Prepared dependencies are already validated and native run rechecks
        # their bindings. Dispatch them before recomputing the whole collection.
        result = experiment.read(report_path)
        collected = False
        try:
            while True:
                if result["automatic_status"] == "failed":
                    raise ValueError("automatic grading contains exhausted technical failures")
                # No outer concurrency limit: every independent ready group reaches
                # the shared runner immediately, before waiting for any completion.
                submitted = False
                for entry in state["experiments"]:
                    if entry["status"] in {"prepared", "running"} and entry["path"] not in active:
                        logfile = directory / "logs" / (Path(entry["path"]).name + ".log")
                        logfile.parent.mkdir(exist_ok=True)
                        with logfile.open("a") as log:
                            process = subprocess.Popen([sys.executable, str(LAUNCHER),
                                "--project-root", str(PROJECT), "run", entry["path"]],
                                cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT)
                        entry.update(status="running", pid=process.pid, log=str(logfile))
                        active[entry["path"]] = process
                        submitted = True
                if submitted:
                    experiment.write(directory / "state.json", state)
                if not active:
                    if result["automatic_status"] == "complete":
                        if not collected:
                            for path, checksum in result["sources"].items():
                                if engine._sha256_file(Path(path)) != checksum:
                                    raise ValueError("automatic grading collection source changed: " + path)
                        state["status"] = "complete"
                        experiment.write(directory / "grades.json", result)
                        state["report"] = str(directory / "grades.json")
                        state["report_sha256"] = engine._sha256_file(directory / "grades.json")
                        break
                    raise ValueError("automatic grading cannot finish every selected answer")
                finished = [path for path, process in active.items() if process.poll() is not None]
                if not finished:
                    time.sleep(0.1)
                    continue
                for path in finished:
                    process = active.pop(path)
                    entry = next(row for row in state["experiments"] if row["path"] == path)
                    if process.returncode:
                        entry.update(status="failed", returncode=process.returncode)
                        raise ValueError("native grading batch failed; see " + entry["log"])
                    native = experiment.report(Path(path), include_request_preview=False)
                    if any(row["status"] not in {"valid", "empty"} for row in native["cases"]):
                        entry["status"] = "failed"
                        raise ValueError("native grading batch lacks valid judgments: " + path)
                    entry["status"] = "complete"
                result = _collect(directory, state, context)
                collected = True
                _prepare_groups(result["automatic_requests"], directory, state, result, context)
                experiment.write(directory / "state.json", state)
        except Exception as error:
            # Already submitted independent groups keep their bounded native runs;
            # no new semantic draws are dispatched to disguise a technical failure.
            for path, process in active.items():
                process.wait()
                entry = next(row for row in state["experiments"] if row["path"] == path)
                entry.update(status="complete" if process.returncode == 0 else "failed",
                    returncode=process.returncode)
            state.update(status="failed", error=str(error))
        experiment.write(directory / "state.json", state)
        return dict(status=state["status"], report=state["report"], experiments=state["experiments"],
            **({"error": state["error"]} if state.get("error") else {}))
