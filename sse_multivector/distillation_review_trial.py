"""Freeze complete validation answers for a bounded offline review trial.

Sampling uses saved answer structure and source identities, never reviewer
outputs. The existing preview verifier keeps reserved test content sealed.
"""
from collections import Counter, defaultdict
from pathlib import Path
import random
import re

from . import distillation_review_preview as preview
from . import distillation_run as run


SETTINGS = dict(provider="openai-codex", model="gpt-6.1-sol",
    reasoning_effort="xhigh", transport="sse", concurrency=8,
    prompts=dict(matching="DSMv3", support="DSSv2", relationship="DSLv2"))
_PRIOR_SOURCES = ("matching-actual-v2-source.json", "actual-three-check-matching-source.json",
                  "actual-three-check-support-source.json", "actual-three-check-relationship-source.json")
_PATTERNS = ("teacher_catalog_size", "nonexact_composite_subjects",
             "student_max_depth", "candidate_variants")
_COMPOSITE = re.compile(r"\b(?:and|or|but)\b|[,;]", re.IGNORECASE)


def _prior_notes(sources):
    notes = set()
    directory = Path(__file__).parent / "distillation-review-v1"
    for filename in _PRIOR_SOURCES:
        value = preview._decode(preview._read(directory / filename, sources))
        for case in value["cases"]:
            notes.add(case["generation"]["note_id"])
    return notes


def _population(manifest_path, outputs):
    verified = preview.preview(manifest_path, outputs)
    sources = dict(verified["sources"])
    manifest, evaluation, teachers = preview._validation(manifest_path, sources)
    # Identity headers and the complete ledger hash have already been checked.
    # Decode only the same validation slice as the production preview verifier.
    raw = preview._read(manifest_path.parent / "references.jsonl", sources,
                        manifest["outputs"]["references.jsonl"])
    start = len(manifest["train_note_ids"])
    references = [preview._decode(line) for line in raw.splitlines()[start:start + len(evaluation)]]
    prior = _prior_notes(sources)
    candidates, versions = [], []
    for model_index, model in enumerate(verified["models"], 1):
        output = Path(model["output"])
        for version in model["versions"]:
            name = version["version"]
            key = f"M{model_index:02}-{name}"
            versions.append(key)
            stage = output / ("baseline" if name == "baseline" else "evaluations/" + name)
            seal = preview._decode(preview._read(stage / "complete.json", sources,
                                                sources[str(stage / "complete.json")]))
            rows = preview._decode(preview._read(stage / "results.json", sources, seal["results.json"]))
            for index, (row, teacher, reference) in enumerate(zip(rows, teachers, references)):
                wording = [s["subject"] for s in row["subjects"]]
                nonexact = [s for s in wording if s not in teacher[0].by_subject]
                candidates.append(dict(id=f"{key}-N{index:04}", note_id=row["note_id"],
                    model=model["model"], revision=model["revision"], model_output=str(output),
                    version=name, version_key=key, stage=str(stage), index=index, row=row,
                    teacher_index=teacher, teacher=[{key: s[key] for key in ("number", "context", "subject")}
                                                   for s in reference["subjects"]],
                    previously_used_note=row["note_id"] in prior,
                    complexity=dict(teacher_catalog_size=len(teacher[0].catalog),
                        teacher_occurrences=len(reference["subjects"]),
                        nonexact_subjects=len(nonexact),
                        nonexact_composite_subjects=sum(bool(_COMPOSITE.search(s)) for s in nonexact),
                        student_max_depth=max((s["number"].count(".") + 1 for s in row["subjects"]), default=0)),
                    generation=dict(path=str(stage / f"note-{index:04}" / "subjects.json"),
                        sha256=seal[f"note-{index:04}/subjects.json"], index=index, note_id=row["note_id"])))
    variants = defaultdict(set)
    for candidate in candidates:
        row = candidate["row"]
        variants[candidate["note_id"]].add(preview._digest(dict(subjects=[
            [s["number"], s["subject"]] for s in row["subjects"]], errors=row["errors"])))
    for candidate in candidates:
        candidate["complexity"]["candidate_variants"] = len(variants[candidate["note_id"]])
    return verified, sources, candidates, versions


def _random_sample(candidates, versions, count, rng):
    order = list(versions)
    rng.shuffle(order)
    pools = {version: [] for version in order}
    for candidate in candidates:
        pools[candidate["version_key"]].append(candidate)
    for pool in pools.values():
        rng.shuffle(pool)
    quotient, remainder = divmod(count, len(order))
    quotas = {version: quotient + int(i < remainder) for i, version in enumerate(order)}
    if any(quotas[version] > len(pool) for version, pool in pools.items()):
        raise ValueError("not enough complete validation answers for balanced random sampling")
    selected, used_notes = [], set()
    for round_index in range(quotient + bool(remainder)):
        for version in order:
            if round_index >= quotas[version]:
                continue
            pool = pools[version]
            candidate = min(pool, key=lambda c: (c["note_id"] in used_notes, c["previously_used_note"]))
            pool.remove(candidate)
            selected.append(candidate)
            used_notes.add(candidate["note_id"])
    return selected, quotas


def _challenge_sample(candidates, random_answers, count, rng):
    selected_ids = {a["id"] for a in random_answers}
    remaining = [c for c in candidates if c["id"] not in selected_ids]
    rng.shuffle(remaining)
    selected, selected_notes = [], set()
    for index in range(count):
        pattern = _PATTERNS[index % len(_PATTERNS)]
        candidate = max(remaining, key=lambda c: (c["note_id"] not in selected_notes, c["complexity"][pattern],
            tuple(c["complexity"][p] for p in _PATTERNS)))
        remaining.remove(candidate)
        selected.append((candidate, pattern))
        selected_notes.add(candidate["note_id"])
    return selected


def _answer(candidate, cohort, sources, *, pattern=None):
    generation = candidate["generation"]
    saved = preview._decode(preview._read(Path(generation["path"]), sources, generation["sha256"]))
    row = candidate["row"]
    parsed = run.subject_result(candidate["note_id"], saved["answer"])
    teacher = candidate["teacher_index"]
    if (saved["note_id"] != candidate["note_id"] or parsed != {key: row[key] for key in parsed}
            or saved["messages"] != [dict(role="user", content=teacher[4] + "\n\n<post>\n" + teacher[3] + "\n</post>")]):
        raise ValueError("selected validation answer differs from verified source")
    result = {key: candidate[key] for key in ("id", "note_id", "model", "revision", "model_output",
        "version", "version_key", "stage", "generation", "previously_used_note", "complexity", "teacher")}
    result.update(cohort=cohort, post=teacher[3], task_prompt=teacher[4],
                  student=row["subjects"], errors=row["errors"], raw_answer=saved["answer"])
    if pattern is not None:
        result["selection_pattern"] = pattern
    return result


def _cohort(selected, candidates):
    by_id = {c["id"]: c for c in candidates}
    work = preview._Workload()
    for answer in selected:
        candidate = by_id[answer["id"]]
        work.include(preview._note_workload(candidate["row"], candidate["teacher_index"]))
    counts = Counter(answer["version_key"] for answer in selected)
    work.counts["versions"] = len(counts)
    return dict(answers=selected, totals=work.summary(), versions=dict(sorted(counts.items())),
        distinct_notes=len({a["note_id"] for a in selected}),
        previously_used_note_answers=sum(a["previously_used_note"] for a in selected))


def prepare_trial(manifest_path, model_outputs, output, *, random_count=50, hard_count=10,
                  seed="DS-final-20261009"):
    """Verify and freeze disjoint complete-answer samples without inference."""
    if (type(random_count) is not int or random_count < 0 or type(hard_count) is not int or hard_count < 0
            or not random_count + hard_count or not isinstance(seed, str) or not seed):
        raise ValueError("expected nonnegative trial counts and a nonempty seed")
    manifest_path = Path(manifest_path).expanduser().resolve()
    outputs = [Path(p).expanduser().resolve() for p in model_outputs]
    directory = Path(output).expanduser().resolve()
    if directory.exists():
        raise ValueError("trial output already exists; frozen selection cannot be overwritten")
    verified, sources, candidates, versions = _population(manifest_path, outputs)
    if random_count + hard_count > len(candidates):
        raise ValueError("not enough complete validation answers for the requested trial")
    rng = random.Random(seed)
    random_answers, quotas = _random_sample(candidates, versions, random_count, rng)
    challenge_answers = _challenge_sample(candidates, random_answers, hard_count, rng)
    random_rows = [_answer(c, "random", sources) for c in random_answers]
    challenge_rows = [_answer(c, "challenge", sources, pattern=p) for c, p in challenge_answers]
    preview._read(Path(__file__).resolve(), sources)
    report = dict(schema_version=1, inference_calls=0, dataset=verified["dataset"],
        model_outputs=[dict(output=m["output"], model=m["model"], revision=m["revision"])
                       for m in verified["models"]], sources=sources, settings=SETTINGS,
        population=verified["totals"], selection_policy=dict(seed=seed, random_count=random_count,
            hard_count=hard_count, version_quotas=quotas,
            random="Seeded shuffled version quotas differ by at most one; choose unseen notes first, "
                   "preferring notes absent from earlier actual sources. Invalid and empty answers remain eligible.",
            challenge="Disjoint answer IDs from the entire remaining population, cycling descending teacher "
                "catalog size, literal nonexact composite markers, student depth and same-note candidate variants; "
                "prefer distinct challenge notes, then other complexity values and seeded order break ties. "
                "Notes may overlap random or prior trials and are marked.",
            composite_markers="Whole words and/or/but or comma/semicolon; an observable heuristic, not a correctness label.",
            previous_note_sources=list(_PRIOR_SOURCES)),
        random=_cohort(random_rows, candidates), challenge=_cohort(challenge_rows, candidates),
        checkpoint_verification=verified["checkpoint_verification"])
    path = directory / "selection.json"
    run.write_json(path, report)
    run.write_json(directory / "selection.complete.json", {"selection.json": run.sha256(path)})
    return dict(report, selection_path=str(path))


def load_trial(path):
    """Load a sealed selection and verify all source hashes and selected evidence."""
    path = Path(path).expanduser().resolve()
    seal = run.read_json(path.parent / "selection.complete.json")
    if seal != {path.name: run.sha256(path)}:
        raise ValueError("trial selection hash differs")
    report = run.read_json(path)
    if report["schema_version"] != 1 or report["inference_calls"] != 0 or report["settings"] != SETTINGS:
        raise ValueError("trial selection schema or reviewer settings differ")
    if "test" in Path(report["dataset"]["path"]).parts:
        raise ValueError("reserved test paths cannot be loaded as a trial")
    for filename, checksum in report["sources"].items():
        if run.sha256(filename) != checksum:
            raise ValueError(f"trial source hash differs: {filename}")
    manifest_path = Path(report["dataset"]["path"])
    sources = dict(report["sources"])
    if sources.get(str(manifest_path)) != report["dataset"]["sha256"]:
        raise ValueError("trial dataset binding differs")
    manifest, evaluation, teachers = preview._validation(manifest_path, sources)
    raw = preview._read(manifest_path.parent / "references.jsonl", sources,
                        manifest["outputs"]["references.jsonl"])
    start = len(manifest["train_note_ids"])
    references = [preview._decode(line) for line in raw.splitlines()[start:start + len(evaluation)]]
    prior = _prior_notes(sources)
    models = {}
    for model_index, model in enumerate(report["model_outputs"], 1):
        output = Path(model["output"])
        if "test" in output.parts or str(output) in models:
            raise ValueError("invalid trial model source")
        config, plan = preview._model_plan(output, manifest, sources)
        if (model["model"], model["revision"]) != (config["model"], config["revision"]):
            raise ValueError("trial model identity differs")
        models[str(output)] = model_index, config, plan
    stages, candidates, seen = {}, [], set()
    for cohort in ("random", "challenge"):
        rows = report[cohort]["answers"]
        requested = report["selection_policy"]["random_count" if cohort == "random" else "hard_count"]
        if len(rows) != requested:
            raise ValueError("trial selected answer count differs")
        for row in rows:
            generation = row["generation"]
            index = generation["index"]
            if (row["id"] in seen or row["model_output"] not in models or type(index) is not int
                    or not 0 <= index < len(evaluation) or generation["note_id"] != evaluation[index]["note_id"]):
                raise ValueError("trial answer IDs or generation identities differ")
            seen.add(row["id"])
            model_index, config, plan = models[row["model_output"]]
            output = Path(row["model_output"])
            version = row["version"]
            versions = {"baseline"} | {f"checkpoint-{m}" for m in plan["milestones"]}
            key = f"M{model_index:02}-{version}"
            stage = output / ("baseline" if version == "baseline" else "evaluations/" + version)
            if (version not in versions or row["id"] != f"{key}-N{index:04}" or row["version_key"] != key
                    or row["stage"] != str(stage) or "test" in stage.parts):
                raise ValueError("trial version or stage identity differs")
            if str(stage) not in stages:
                if version != "baseline":
                    preview._checkpoint(output, int(version.removeprefix("checkpoint-")), plan, sources)
                stage_seal = preview._decode(preview._read(stage / "complete.json", sources,
                    report["sources"][str(stage / "complete.json")]))
                batch_plan = preview._decode(preview._read(stage / "subject-batches.json", sources,
                                                          stage_seal["subject-batches.json"]))
                stages[str(stage)] = stage_seal, batch_plan, {}
            stage_seal, batch_plan, receipts = stages[str(stage)]
            generation_path = stage / f"note-{index:04}" / "subjects.json"
            bound = dict(path=str(generation_path), sha256=stage_seal[f"note-{index:04}/subjects.json"],
                         index=index, note_id=evaluation[index]["note_id"])
            if generation != bound:
                raise ValueError("trial generation binding differs")
            saved = preview._decode(preview._read(generation_path, sources, bound["sha256"]))
            batch = saved["batch"]
            batches = {f"subjects-{i:04}.json": b for i, b in enumerate(batch_plan["batches"])}
            if batch["file"] not in batches:
                raise ValueError("trial owning batch differs")
            if batch["file"] not in receipts:
                receipts[batch["file"]] = preview._decode(preview._read(stage / batch["file"], sources,
                                                                       stage_seal[batch["file"]]))
            receipt = receipts[batch["file"]]
            offset = batch["offset"]
            if (type(offset) is not int or not 0 <= offset < len(receipt["answers"])
                    or receipt["batch"] != batches[batch["file"]]
                    or receipt["batch"]["indices"][offset] != index
                    or receipt["note_ids"][offset] != bound["note_id"]
                    or receipt["messages"][offset] != evaluation[index]["messages"]
                    or receipt["input_tokens"][offset] != batch_plan["inputs"][index]["tokens"]
                    or receipt["answers"][offset] != saved["answer"]):
                raise ValueError("trial selected answer differs from owning batch receipt")
            parsed = run.subject_result(bound["note_id"], saved["answer"])
            teacher = teachers[index]
            if row["previously_used_note"] != (bound["note_id"] in prior):
                raise ValueError("trial previous-note accounting differs")
            candidate = dict(row=parsed, teacher_index=teacher,
                **{k: row[k] for k in ("id", "note_id", "model_output", "version", "version_key", "stage",
                                      "previously_used_note", "complexity")},
                model=config["model"], revision=config["revision"], generation=bound,
                teacher=[{k: s[k] for k in ("number", "context", "subject")} for s in references[index]["subjects"]])
            candidates.append(candidate)
            expected = _answer(candidate, cohort, sources, pattern=row.get("selection_pattern"))
            if row != expected:
                raise ValueError("trial selected evidence differs from source")
        if report[cohort] != _cohort(rows, candidates):
            raise ValueError("trial cohort accounting differs")
    quotas = report["selection_policy"]["version_quotas"]
    if any(report["random"]["versions"].get(version, 0) != count for version, count in quotas.items()):
        raise ValueError("trial random version quotas differ")
    return report
