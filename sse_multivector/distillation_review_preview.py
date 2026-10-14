"""Count mechanically resolved and remaining saved-answer checks without inference.

Only the selected split is decoded; evaluation remains the default. The mixed
reference ledger is hash checked as opaque bytes, then identity headers establish
which rows may be decoded. Explicit test previews use baseline and final only.
Distinct semantic inputs describe theoretical request grouping under one fixed
prompt and settings per check; this command prepares no reviewer requests.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

from . import distillation_review as review
from . import distillation_run as run


def _decode(raw):
    return json.loads(raw, object_pairs_hook=run.unique_object)


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _read(path, sources, expected=None):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected is not None and actual != expected:
        raise ValueError(f"review preview source hash differs: {path}")
    sources[str(path)] = actual
    return raw


def _validation(manifest_path, sources, *, split="evaluation"):
    if split not in ("evaluation", "test"):
        raise ValueError("expected evaluation or test split")
    manifest = _decode(_read(manifest_path, sources))
    if manifest["schema_version"] != 2 or manifest["tasks"] != {"subjects": "ASv6.100"}:
        raise ValueError("review preview requires an ASv6.100 subjects-only dataset")
    splits = [manifest[name + "_note_ids"] for name in ("train", "evaluation", "test")]
    if any(not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids)
           for ids in splits):
        raise ValueError("invalid frozen validation splits")
    identities = [i for ids in splits for i in ids]
    selected_ids = manifest[split + "_note_ids"]
    if not splits[0] or not splits[1] or not selected_ids or len(set(identities)) != len(identities):
        raise ValueError("invalid or overlapping frozen validation splits")
    directory = manifest_path.parent
    raw = _read(directory / "references.jsonl", sources, manifest["outputs"]["references.jsonl"])
    references = [_decode(line) for line in review._evaluation_reference_lines(raw, splits, split=split)]
    raw = _read(directory / f"{split}.jsonl", sources, manifest["outputs"][f"{split}.jsonl"])
    evaluation = [_decode(line) for line in raw.splitlines()]
    if [r["note_id"] for r in evaluation] != selected_ids:
        raise ValueError("evaluation identities differ from frozen splits")
    teachers = []
    for reference, row in zip(references, evaluation):
        suffix = "\n\n<post>\n" + reference["text"] + "\n</post>"
        messages = row["messages"]
        if (reference["note_id"] != row["note_id"] or reference["split"] != split
                or len(messages) != 1 or messages[0]["role"] != "user"
                or not messages[0]["content"].endswith(suffix)
                or hashlib.sha256(messages[0]["content"][:-len(suffix)].encode()).hexdigest()
                   != manifest["subject_instruction_sha256"]):
            raise ValueError("validation post or instruction differs from frozen reference")
        subjects = run.parse_subjects(json.dumps(dict(subjects=[
            {key: s[key] for key in ("number", "context", "subject")}
            for s in reference["subjects"]]), ensure_ascii=False))
        index = review._TeacherIndex(subjects)
        teachers.append((index, _digest(index.catalog), _digest(reference["text"]),
                         reference["text"], messages[0]["content"][:-len(suffix)]))
    return manifest, evaluation, teachers


def _stage(output, version, *, split="evaluation"):
    if split == "test":
        return output / "test" / version
    return output / ("baseline" if version == "baseline" else "evaluations/" + version)


class _Workload:
    def __init__(self):
        self.counts = Counter({name: 0 for name in (
            "versions", "outputs", "valid_outputs", "invalid_outputs", "empty_outputs",
            "subject_occurrences", "relationship_occurrences")})
        self.checks = {name: Counter(occurrences=0, mechanical=0, semantic=0)
                       for name in ("matching", "support", "relationship")}
        self.rules = {name: Counter() for name in self.checks}
        self.semantic = {name: Counter() for name in self.checks}

    def check(self, name, mechanical, key):
        counts = self.checks[name]
        counts["occurrences"] += 1
        if mechanical is not None:
            counts["mechanical"] += 1
            self.rules[name][mechanical["evidence"]["rule"]] += 1
        else:
            counts["semantic"] += 1
            self.semantic[name][key] += 1

    def include(self, other):
        self.counts.update(other.counts)
        for name in self.checks:
            self.checks[name].update(other.checks[name])
            self.rules[name].update(other.rules[name])
            self.semantic[name].update(other.semantic[name])

    def summary(self):
        return dict(self.counts, checks={name: dict(counts,
            distinct_semantic_inputs=len(self.semantic[name]),
            mechanical_rules=dict(sorted(self.rules[name].items())))
            for name, counts in self.checks.items()})


def _note_workload(row, teacher, *, allow_ancestor_paths=True):
    index, catalog_key, post_key = teacher[:3]
    work = _Workload()
    work.counts["outputs"] = 1
    if row["errors"]:
        work.counts["invalid_outputs"] = 1
        return work
    work.counts["valid_outputs"] = 1
    students = {s["number"]: s["subject"] for s in row["subjects"]}
    work.counts["empty_outputs"] = int(not students)
    work.counts["subject_occurrences"] = len(students)
    for number, subject in students.items():
        work.check("matching", index.matching(subject), (post_key, catalog_key, subject))
        work.check("support", index.support(subject), (post_key, subject))
        parent_number = number.rpartition(".")[0]
        if parent_number:
            parent = students[parent_number]
            work.counts["relationship_occurrences"] += 1
            work.check("relationship", index.relationship(parent, subject,
                       allow_ancestor_paths=allow_ancestor_paths), (parent, subject))
    return work


def _model_plan(output, manifest, sources):
    saved = _decode(_read(output / "manifest.json", sources))
    plan = _decode(_read(output / "training-plan.json", sources))
    seal = _decode(_read(output / "provenance.complete.json", sources))
    if seal != {name: sources[str(output / name)] for name in ("manifest.json", "training-plan.json")}:
        raise ValueError("model provenance seal differs")
    if saved["dataset"] != manifest:
        raise ValueError("model dataset differs from frozen validation manifest")
    config = saved["config"]
    milestones = config["training_milestones"]
    if (not isinstance(milestones, list) or not milestones
            or any(type(m) is not int or m < 1 for m in milestones)
            or milestones != sorted(set(milestones))
            or milestones[-1] != len(manifest["train_note_ids"])
            or plan["milestones"] != milestones
            or len(plan["note_ids"]) != len(manifest["train_note_ids"])
            or set(plan["note_ids"]) != set(manifest["train_note_ids"])
            or type(plan["examples_per_update"]) is not int or plan["examples_per_update"] < 1):
        raise ValueError("model training plan differs from frozen training identities")
    if (not isinstance(config["model"], str) or not config["model"]
            or not isinstance(config["revision"], str) or not config["revision"]):
        raise ValueError("model identity is missing")
    return config, plan


def _checkpoint(output, cursor, plan, sources):
    directory = output / "checkpoints" / f"checkpoint-{cursor}"
    seal = _decode(_read(directory / "complete.json", sources))
    metadata = _decode(_read(directory / "training.json", sources, seal["training.json"]))
    updates, start = 0, 0
    for stop in plan["milestones"]:
        updates += math.ceil((stop - start) / plan["examples_per_update"])
        start = stop
        if stop == cursor:
            break
    if (type(metadata["cursor"]) is not int or metadata["cursor"] != cursor
            or type(metadata["updates"]) is not int or metadata["updates"] != updates
            or metadata["consumed_note_ids"] != plan["note_ids"][:cursor]
            or metadata["manifest_sha256"] != sources[str(output / "manifest.json")]
            or metadata["plan_sha256"] != sources[str(output / "training-plan.json")]):
        raise ValueError("checkpoint identity or training counters differ")


def _natural_prefix(template, variables, payload_name, field, render):
    payload = variables[payload_name]
    suffix = json.dumps(_decode(payload)[field], ensure_ascii=False) + "}"
    marker = "{" + payload_name + "}"
    if template.count(marker) != 1 or not payload.endswith(suffix):
        raise ValueError("review payload prefix boundary differs")
    head = template[:template.index(marker)]
    fixed = {key: value for key, value in variables.items() if key != payload_name}
    return render(head, fixed) + payload[:-len(suffix)]


def _estimates(work, teachers, sources, timing_experiments):
    import importlib.metadata
    try:
        import tiktoken
    except ImportError as error:
        raise ValueError("--estimate requires tiktoken in the command's Python runtime") from error
    from experiment_runner import inputs, prompt_cache
    from . import distillation_matching as matching
    from . import distillation_verdict as verdict

    encoding = tiktoken.get_encoding("o200k_base")
    directory = Path(__file__).parent / "distillation-review-v1"
    definitions = dict(matching=("DSMv3", "matching-prompt-v3.md", "MATCH_INPUT", "student_subject"),
                       support=("DSSv2", "support-prompt-v2.md", "SUPPORT_INPUT", "student_subject"),
                       relationship=("DSLv2", "relationship-prompt-v2.md", "RELATIONSHIP_INPUT", "child_subject"))
    posts = {t[2]: (t[3], t[4]) for t in teachers}
    catalogs = {t[1]: t[0] for t in teachers}
    task = teachers[0][4]
    checks, templates = {}, {}
    for name, (identifier, filename, payload_name, field) in definitions.items():
        path = directory / filename
        template = _read(path, sources).decode()
        templates[name] = template
        prefix, boundary = inputs.template_prefix(template)
        groups, counts = {}, []
        occurrence_tokens = 0
        for key, occurrences in work.semantic[name].items():
            if name == "matching":
                post_key, catalog_key, subject = key
                variables = matching._matching_inputs(catalogs[catalog_key], subject, post=posts[post_key][0])
            elif name == "support":
                post_key, subject = key
                post, note_task = posts[post_key]
                variables = verdict._support_inputs(note_task, post, subject)
            else:
                variables = verdict._relationship_inputs(task, *key)
            prompt = inputs.render(template, variables)
            count = len(encoding.encode(prompt, disallowed_special=()))
            counts.append(count)
            occurrence_tokens += occurrences * count
            natural = _natural_prefix(template, variables, payload_name, field, inputs.render)
            if not prompt.startswith(natural):
                raise ValueError("natural prefix differs from rendered review prompt")
            digest = hashlib.sha256(natural.encode()).hexdigest()
            if digest not in groups:
                policy = prompt_cache.prefix_policy(natural)
                groups[digest] = dict(tokens=policy["estimated_prefix_tokens"], eligible=policy["eligible"], uses=0)
            groups[digest]["uses"] += 1
        eligible = [g for g in groups.values() if g["uses"] > 1 and g["eligible"]]
        natural_summary = dict(groups=len(groups), repeated_groups=sum(g["uses"] > 1 for g in groups.values()),
            eligible_groups=len(eligible), warmup_calls=len(eligible),
            warmup_input_tokens=sum(g["tokens"] for g in eligible),
            potential_cached_input_tokens=sum(g["tokens"] * g["uses"] for g in eligible),
            cold_first_potential_cached_input_tokens=sum(g["tokens"] * (g["uses"] - 1) for g in eligible))
        checks[name] = dict(prompt=dict(id=identifier, path=str(path), sha256=sources[str(path)]),
            distinct_inputs=len(counts), rendered_input_tokens=sum(counts),
            occurrence_rendered_input_tokens=occurrence_tokens,
            min_rendered_input_tokens=min(counts, default=0), max_rendered_input_tokens=max(counts, default=0),
            automatic_prefix=dict(prompt_cache.prefix_policy(prefix), boundary=boundary), natural_prefix=natural_summary)
    totals = {key: sum(check[key] for check in checks.values()) for key in
              ("distinct_inputs", "rendered_input_tokens", "occurrence_rendered_input_tokens")}
    totals.update({key: sum(check["natural_prefix"][key] for check in checks.values()) for key in
                   ("warmup_calls", "warmup_input_tokens", "potential_cached_input_tokens",
                    "cold_first_potential_cached_input_tokens")})
    result = dict(tokenizer="o200k_base", tokenizer_version=importlib.metadata.version("tiktoken"),
        input_token_basis="Rendered prompt text only; excludes provider instructions, message framing and output-schema overhead.",
        settings=dict(model="gpt-6.1-sol", reasoning="xhigh", concurrency=8), checks=checks, totals=totals,
        cache_basis="Natural-prefix opportunities only; not selected by automatic template caching and no hits guaranteed. "
                    "Warmup input is prefix text only; output and request overhead are additional.")
    if timing_experiments:
        result["timing"] = _timing(timing_experiments, checks, templates, sources)
    for module in (matching, verdict, inputs, prompt_cache):
        _read(Path(module.__file__).resolve(), sources)
    return result


def _statistics(values):
    return dict(mean=statistics.mean(values), median=statistics.median(values),
                p90=statistics.quantiles(values, n=10, method="inclusive")[8] if len(values) > 1 else values[0],
                min=min(values), max=max(values))


def _timing(directories, checks, templates, sources):
    from experiment_runner import experiment, extraction_pipeline as engine
    paths = [Path(p).expanduser().resolve() for p in directories]
    if len(paths) != len(set(paths)) or any("test" in p.parts for p in paths):
        raise ValueError("expected distinct non-test timing experiments")
    observed = {name: [] for name in checks}
    seen = set()
    strata = []
    files = engine.ReceiptFiles()
    for directory in paths:
        plan, config, manifest = experiment.load(directory)
        names = [name for name in checks if plan["prompt"]["id"] == checks[name]["prompt"]["id"]
                 and plan["prompt"]["text"] == templates[name]]
        if (len(names) != 1 or config.provider != "openai-codex" or config.model != "gpt-6.1-sol"
                or config.reasoning_effort != "xhigh" or config.transport != "sse" or config.concurrency != 8
                or manifest.get("cache_warmup")):
            raise ValueError("timing experiment prompt or reviewer settings differ")
        name = names[0]
        schema_name = "matching-response-schema.json" if name == "matching" else "boolean-response-schema.json"
        schema_path = Path(__file__).parent / "distillation-review-v1" / schema_name
        if config.output_schema != _decode(_read(schema_path, sources)):
            raise ValueError("timing experiment output schema differs")
        report = experiment.report(directory, generation_costs=True, include_request_preview=False)
        cases = report["cases"]
        if not cases or any(c["status"] != "valid" or c.get("reused") or c.get("origin") == "mechanical" for c in cases):
            raise ValueError("timing samples require complete fresh valid native calls")
        warmups = {(s["results_path"], s["result_line"]) for s in report.get("cache_warmup", {}).get("sources", [])}
        selected = [s for s in report["generation_usage"]["sources"]
                    if (s["results_path"], s["result_line"]) not in warmups]
        jobs = {"prompt:" + c.get("job_id", c["id"]) for c in cases}
        if len(selected) != len(jobs) or {s["job_key"] for s in selected} != jobs:
            raise ValueError("timing samples require exactly one original attempt per comparison")
        samples = []
        for source in selected:
            key = source["results_path"], source["result_line"]
            if key in seen or source.get("added_from_reuse"):
                raise ValueError("timing sample source is duplicated or reused")
            seen.add(key)
            raw = files.line(Path(key[0]), key[1])
            if hashlib.sha256(raw).hexdigest() != source["result_sha256"]:
                raise ValueError("timing receipt changed while estimating")
            record = _decode(raw)
            usage = experiment.usage_summary([(record, None)])
            seconds = record.get("elapsed_seconds")
            if (record["status"] != "succeeded" or record.get("attempt") != 1 or record.get("retry_reason")
                    or type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0
                    or usage["attempts_without_usage"]):
                raise ValueError("timing receipt lacks fresh complete usage or elapsed time")
            samples.append(dict(elapsed_seconds=seconds, output_tokens=usage["output_tokens"],
                reasoning_tokens=usage["reasoning_tokens"], cached_input_tokens=usage["cached_input_tokens"]))
            path = Path(key[0])
            if str(path) not in sources:
                _read(path, sources)
        observed[name].extend(samples)
        _read(directory / "experiment.json", sources)
        _read(directory / "runner-config.json", sources)
        _read(config.run_directory / "manifest.json", sources)
        strata.append(dict(experiment=str(directory), check=name, samples=len(samples),
            prefix_role_format=bool(config.prompt_cache_prefix),
            cache_hit_calls=sum(s["cached_input_tokens"] > 0 for s in samples),
            excluded_warmup_calls=len(warmups)))
    summaries = {}
    for name, samples in observed.items():
        if not samples:
            continue
        summaries[name] = dict(samples=len(samples),
            elapsed_seconds=_statistics([s["elapsed_seconds"] for s in samples]),
            output_tokens=_statistics([s["output_tokens"] for s in samples]),
            reasoning_tokens=_statistics([s["reasoning_tokens"] for s in samples]))
    complete = set(summaries) == set(checks)
    projections = {}
    for metric in ("mean", "median", "p90"):
        projections[metric] = dict(service_hours_at_concurrency_8=(sum(checks[name]["distinct_inputs"] *
            summary["elapsed_seconds"][metric] for name, summary in summaries.items()) / (8 * 3600) if complete else None),
            output_tokens=(sum(checks[name]["distinct_inputs"] * summary["output_tokens"][metric]
                              for name, summary in summaries.items()) if complete else None))
    _read(Path(experiment.__file__).resolve(), sources)
    return dict(checks=summaries, strata=strata, complete=complete, projections=projections,
        basis="Small selected actual-answer samples, including disputed verdicts. Output includes reasoning once. "
              "Serial service work divided by eight continuously occupied slots; not measured batch wall time. "
              "No additional cache speedup applied; samples retain their observed cache mix. "
              "Saved-answer reuse, warmups, retries, throttling and review work excluded; "
              "median/p90 scenarios are not confidence bounds.")


def preview(manifest_path, model_outputs, *, estimate=False, timing_experiments=(), split="evaluation"):
    """Verify the selected saved stages and count all three review checks."""
    if split not in ("evaluation", "test"):
        raise ValueError("expected evaluation or test split")
    if timing_experiments and not estimate:
        raise ValueError("--timing-experiment requires --estimate")
    manifest_path = Path(manifest_path).expanduser().resolve()
    outputs = [Path(p).expanduser().resolve() for p in model_outputs]
    if not outputs or len(outputs) != len(set(outputs)):
        raise ValueError("expected nonempty distinct model output directories")
    if split == "evaluation" and ("test" in manifest_path.parts or any("test" in p.parts for p in outputs)):
        raise ValueError("reserved test paths cannot be previewed")
    sources = {}
    manifest, evaluation, teachers = _validation(manifest_path, sources, split=split)
    total, models = _Workload(), []
    for output in outputs:
        config, plan = _model_plan(output, manifest, sources)
        model_work, versions, baseline_plan = _Workload(), [], None
        milestones = plan["milestones"] if split == "evaluation" else plan["milestones"][-1:]
        stages = [("baseline", None)] + [(f"checkpoint-{m}", m) for m in milestones]
        for version, cursor in stages:
            directory = _stage(output, version, split=split)
            if cursor is not None:
                _checkpoint(output, cursor, plan, sources)
            if split == "test":
                checkpoint = None if cursor is None else output / "checkpoints" / version
                stage_summary = run.subject_test_summary(output, {split: evaluation}, config, checkpoint)
                _read(directory / "test-collection.json", sources)
            else:
                stage_summary = run.subject_stage_summary(directory, {split: evaluation})
            _read(directory / "complete.json", sources)
            batch_plan = run.read_json(directory / "subject-batches.json")
            if baseline_plan is None:
                baseline_plan = batch_plan
            elif batch_plan != baseline_plan:
                raise ValueError("validation batch plan differs across model versions")
            rows = run.read_json(directory / "results.json")
            stage_work, notes = _Workload(), []
            stage_work.counts["versions"] = 1
            for row, teacher in zip(rows, teachers):
                note_work = _note_workload(row, teacher)
                notes.append(dict(note_id=row["note_id"], totals=note_work.summary()))
                stage_work.include(note_work)
            if (stage_work.counts["outputs"] != stage_summary["notes"] or split == "evaluation" and (
                    stage_work.counts["invalid_outputs"] != stage_summary["subject_failures"]
                    or stage_work.counts["subject_occurrences"] != stage_summary["returned_subjects"])):
                raise ValueError("review preview accounting differs from saved validation stage")
            versions.append(dict(version=version, totals=stage_work.summary(), notes=notes))
            model_work.include(stage_work)
        models.append(dict(output=str(output), model=config["model"], revision=config["revision"],
                           totals=model_work.summary(), versions=versions))
        total.include(model_work)
    estimates = (_estimates(total, teachers, sources, timing_experiments) if estimate else None)
    for module in (Path(__file__), Path(review.__file__), Path(run.__file__)):
        _read(module.resolve(), sources)
    result = dict(schema_version=1, inference_calls=0, dataset=dict(path=str(manifest_path),
        sha256=sources[str(manifest_path)]), sources=sources, totals=total.summary(), models=models,
        distinct_input_basis="Identical remaining input payloads under one fixed prompt/settings per check; "
                             "unprepared, before saved-answer reuse, warmups or retries.",
        checkpoint_verification="Sealed metadata and identity only; weight files are not opened.")
    if estimates is not None:
        result["estimates"] = estimates
    if split == "test":
        result["dataset"]["split"] = split
    return result
