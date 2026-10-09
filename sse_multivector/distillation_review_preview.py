"""Count mechanically resolved and remaining validation checks without inference.

Only evaluation content is decoded. The mixed reference ledger is hash checked
as opaque bytes, then identity headers establish which rows may be decoded.
Distinct semantic inputs describe theoretical request grouping under one fixed
prompt and settings per check; this command prepares no reviewer requests.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

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


def _validation(manifest_path, sources):
    manifest = _decode(_read(manifest_path, sources))
    if manifest["schema_version"] != 2 or manifest["tasks"] != {"subjects": "ASv6.100"}:
        raise ValueError("review preview requires an ASv6.100 subjects-only dataset")
    splits = [manifest[name + "_note_ids"] for name in ("train", "evaluation", "test")]
    if any(not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids)
           for ids in splits):
        raise ValueError("invalid frozen validation splits")
    identities = [i for ids in splits for i in ids]
    if not splits[0] or not splits[1] or len(set(identities)) != len(identities):
        raise ValueError("invalid or overlapping frozen validation splits")
    directory = manifest_path.parent
    raw = _read(directory / "references.jsonl", sources, manifest["outputs"]["references.jsonl"])
    lines = raw.splitlines()
    if len(lines) != len(identities):
        raise ValueError("reference identity count differs from frozen splits")
    # The frozen writer emits note_id first. Reject unsupported order before
    # decoding any row content, including accidentally reordered reserved rows.
    header = re.compile(rb'^\s*\{\s*"note_id"\s*:\s*("(?:[^"\\]|\\.)*")\s*[,}]')
    for line, identifier in zip(lines, identities):
        match = header.match(line)
        if match is None or _decode(match[1]) != identifier:
            raise ValueError("reference identity header order differs from frozen splits")
    start = len(splits[0])
    references = [_decode(line) for line in lines[start:start + len(splits[1])]]
    raw = _read(directory / "evaluation.jsonl", sources, manifest["outputs"]["evaluation.jsonl"])
    evaluation = [_decode(line) for line in raw.splitlines()]
    if [r["note_id"] for r in evaluation] != splits[1]:
        raise ValueError("evaluation identities differ from frozen splits")
    teachers = []
    for reference, row in zip(references, evaluation):
        suffix = "\n\n<post>\n" + reference["text"] + "\n</post>"
        messages = row["messages"]
        if (reference["note_id"] != row["note_id"] or reference["split"] != "evaluation"
                or len(messages) != 1 or messages[0]["role"] != "user"
                or not messages[0]["content"].endswith(suffix)
                or hashlib.sha256(messages[0]["content"][:-len(suffix)].encode()).hexdigest()
                   != manifest["subject_instruction_sha256"]):
            raise ValueError("validation post or instruction differs from frozen reference")
        subjects = run.parse_subjects(json.dumps(dict(subjects=[
            {key: s[key] for key in ("number", "context", "subject")}
            for s in reference["subjects"]]), ensure_ascii=False))
        index = review._TeacherIndex(subjects)
        teachers.append((index, _digest(index.catalog), _digest(reference["text"])))
    return manifest, evaluation, teachers


class _Workload:
    def __init__(self):
        self.counts = Counter({name: 0 for name in (
            "versions", "outputs", "valid_outputs", "invalid_outputs", "empty_outputs",
            "subject_occurrences", "relationship_occurrences")})
        self.checks = {name: Counter(occurrences=0, mechanical=0, semantic=0)
                       for name in ("matching", "support", "relationship")}
        self.rules = {name: Counter() for name in self.checks}
        self.semantic = {name: set() for name in self.checks}

    def check(self, name, mechanical, key):
        counts = self.checks[name]
        counts["occurrences"] += 1
        if mechanical is not None:
            counts["mechanical"] += 1
            self.rules[name][mechanical["evidence"]["rule"]] += 1
        else:
            counts["semantic"] += 1
            self.semantic[name].add(key)

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


def _note_workload(row, teacher):
    index, catalog_key, post_key = teacher
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
            work.check("relationship", index.relationship(parent, subject), (parent, subject))
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


def preview(manifest_path, model_outputs):
    """Verify complete saved validation stages and count all three review checks."""
    manifest_path = Path(manifest_path).expanduser().resolve()
    outputs = [Path(p).expanduser().resolve() for p in model_outputs]
    if not outputs or len(outputs) != len(set(outputs)):
        raise ValueError("expected nonempty distinct model output directories")
    if "test" in manifest_path.parts or any("test" in p.parts for p in outputs):
        raise ValueError("reserved test paths cannot be previewed")
    sources = {}
    manifest, evaluation, teachers = _validation(manifest_path, sources)
    total, models = _Workload(), []
    for output in outputs:
        config, plan = _model_plan(output, manifest, sources)
        model_work, versions, baseline_plan = _Workload(), [], None
        stages = [("baseline", output / "baseline", None)] + [
            (f"checkpoint-{m}", output / "evaluations" / f"checkpoint-{m}", m)
            for m in plan["milestones"]]
        for version, directory, cursor in stages:
            if cursor is not None:
                _checkpoint(output, cursor, plan, sources)
            stage_summary = run.subject_stage_summary(directory, {"evaluation": evaluation})
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
            if (stage_work.counts["outputs"] != stage_summary["notes"]
                    or stage_work.counts["invalid_outputs"] != stage_summary["subject_failures"]
                    or stage_work.counts["subject_occurrences"] != stage_summary["returned_subjects"]):
                raise ValueError("review preview accounting differs from saved validation stage")
            versions.append(dict(version=version, totals=stage_work.summary(), notes=notes))
            model_work.include(stage_work)
        models.append(dict(output=str(output), model=config["model"], revision=config["revision"],
                           totals=model_work.summary(), versions=versions))
        total.include(model_work)
    for module in (Path(__file__), Path(review.__file__), Path(run.__file__)):
        _read(module.resolve(), sources)
    return dict(schema_version=1, inference_calls=0, dataset=dict(path=str(manifest_path),
        sha256=sources[str(manifest_path)]), sources=sources, totals=total.summary(), models=models,
        distinct_input_basis="Identical remaining input payloads under one fixed prompt/settings per check; "
                             "unprepared, before saved-answer reuse, warmups or retries.",
        checkpoint_verification="Sealed metadata and identity only; weight files are not opened.")
