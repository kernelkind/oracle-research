"""Immutable agent decisions bound to preserved native reviewer evidence."""
import hashlib
import json
from pathlib import Path

from . import distillation_matching as matching
from . import distillation_verdict as verdict
from . import extraction_pipeline as engine


def _native(reference, protected):
    from . import distillation_coverage_search as coverage
    rows = coverage._correction_rows([dict(path=reference["experiment"],
        sha256=reference["experiment_sha256"], case_ids=[reference["case_id"]])], Path.cwd(), protected)
    if len(rows) != 1 or rows[0]["status"] != "valid":
        raise ValueError("adjudication requires one valid saved native reviewer output")
    return rows[0]


def _original(row):
    return {key: row.get(key) for key in ("id", "inputs", "input_sha256", "prompt", "output", "parsed",
        "receipt", "origin", "evidence", "reviews")}


def _validate(row, decision, classification, rule, reason):
    check = row["evidence"]["check"]
    if check not in {"matching", "support", "relationship"}:
        raise ValueError("adjudication requires matching, support or relationship evidence")
    field = "teacher_id" if check == "matching" else "valid"
    if classification not in {"correct", "incorrect", "uncertain"}:
        raise ValueError("unknown original decision classification")
    if not isinstance(rule, str) or not rule.strip() or rule not in row["prompt"]:
        raise ValueError("adjudication rule must quote the exact saved prompt")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("adjudication requires an explicit source reason")
    if decision is None:
        if classification != "uncertain":
            raise ValueError("an unresolved adjudication must classify the original decision as uncertain")
        return None
    if set(decision) != {field}:
        raise ValueError("adjudication verdict type does not match " + check)
    raw = json.dumps(dict(decision, reason=reason), ensure_ascii=False)
    result = (matching.validate(row, raw) if check == "matching" else verdict.validate(row, raw))
    if classification == "correct" and decision[field] != row["parsed"][field]:
        raise ValueError("a correct original decision must retain its verdict")
    if row.get("origin") == "mechanical" and decision[field] != row["parsed"][field]:
        raise ValueError("adjudication cannot contradict a trusted mechanical verdict")
    return result


def record(experiment_path, case_id, output, *, decision, classification, rule, reason):
    """Record an agent adjudication; never send requests or change source journals."""
    from experiment_runner import experiment, project
    project.configure(Path(__file__).resolve().parents[1])
    output = Path(output).expanduser().resolve()
    seal = output.with_name(output.name + ".complete.json")
    if output.exists() or seal.exists():
        raise ValueError("adjudication output already exists")
    source = Path(experiment_path).expanduser().resolve()
    reference = dict(experiment=str(source), experiment_sha256=engine._sha256_file(source / "experiment.json"),
        case_id=case_id)
    protected = {}
    row = _native(reference, protected)
    _validate(row, decision, classification, rule, reason)
    result = dict(schema_version=1, actor="agent", check=row["evidence"]["check"], source=reference,
        original=_original(row), original_output_sha256=hashlib.sha256(row["output"].encode()).hexdigest(),
        original_prompt_sha256=hashlib.sha256(row["prompt"].encode()).hexdigest(), decision=decision,
        original_decision_classification=classification, rule=rule, reason=reason, sources=protected,
        inference_calls=0, semantic_status="Explicit agent source adjudication; not a provider response or user gold.")
    for filename, checksum in protected.items():
        if engine._sha256_file(Path(filename)) != checksum:
            raise ValueError("adjudication source changed: " + filename)
    output.parent.mkdir(parents=True, exist_ok=True)
    experiment.write(output, result)
    experiment.write(seal, {output.name: engine._sha256_file(output)})
    return result


def load(paths, protected):
    """Verify immutable records and every original source before using a decision."""
    from experiment_runner import experiment
    records, seen = [], set()
    for filename in paths:
        path = Path(filename).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        seal = path.with_name(path.name + ".complete.json")
        checksum = engine._sha256_file(path)
        if experiment.read(seal) != {path.name: checksum}:
            raise ValueError("adjudication record changed")
        data = experiment.read(path)
        if data.get("schema_version") != 1 or data.get("actor") != "agent":
            raise ValueError("adjudication must be an attributed agent record")
        for source, expected in data["sources"].items():
            if engine._sha256_file(Path(source)) != expected or source in protected and protected[source] != expected:
                raise ValueError("adjudication source changed: " + source)
            protected[source] = expected
        row = _native(data["source"], protected)
        if _original(row) != data["original"] or data["check"] != row["evidence"]["check"]:
            raise ValueError("adjudication original evidence changed")
        if (data["original_output_sha256"] != hashlib.sha256(row["output"].encode()).hexdigest()
                or data["original_prompt_sha256"] != hashlib.sha256(row["prompt"].encode()).hexdigest()):
            raise ValueError("adjudication original digest differs")
        parsed = _validate(row, data["decision"], data["original_decision_classification"], data["rule"], data["reason"])
        protected[str(path)] = checksum
        protected[str(seal)] = engine._sha256_file(seal)
        records.append(dict(data, path=str(path), sha256=checksum, verdict=parsed))
    return records


def index(records):
    result = {}
    for record in records:
        original = record["original"]
        result.setdefault((record["check"], original["input_sha256"], original["prompt"]), []).append(record)
    return result


def apply(row, records):
    candidates = records.get((row["evidence"]["check"], row["input_sha256"], row["prompt"]), [])
    if not candidates:
        return row
    decisions = {json.dumps(item["decision"], sort_keys=True) for item in candidates}
    if len(decisions) != 1 or any(item["decision"] is None for item in candidates):
        return dict(row, origin="adjudication_unresolved", decision_conflicts=[dict(adjudication=item["path"],
            sha256=item["sha256"], actor="agent", decision=item["decision"], reason=item["reason"])
            for item in candidates])
    chosen = candidates[0]
    return dict(row, **chosen["verdict"], origin="adjudicated", receipt=None, reviews=[], decision_conflicts=[],
        adjudication=dict(actor="agent", path=chosen["path"], sha256=chosen["sha256"],
            original=chosen["original"], original_decision_classification=chosen["original_decision_classification"],
            rule=chosen["rule"], reason=chosen["reason"], replaced_output=row.get("output"),
            replaced_receipt=row.get("receipt"), replaced_decision_conflicts=row.get("decision_conflicts", [])))
