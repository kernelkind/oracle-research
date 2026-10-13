"""Offline paired comparison of saved automated and agent-audited grades."""
import json
from collections import Counter
from pathlib import Path

from . import distillation_coverage_search as coverage
from . import extraction_pipeline as engine


def _uncertainty(answer):
    rows = []
    for premise in answer.get("premises", []):
        if premise.get("origin") == "adjudicated":
            continue
        current = {}
        for item in premise.get("reviews", []):
            if item.get("current") is True and item.get("verdict") in {"accept", "reject", "uncertain"}:
                current[item.get("role")] = item
        for item in list(current.values()) + premise.get("audits", []):
            if item.get("verdict") == "uncertain":
                rows.append(dict(case_id=premise["case_id"], input_sha256=premise["input_sha256"],
                    output_sha256=premise["output_sha256"], assessment=item))
        record = premise.get("adjudication", {})
        if record.get("original_decision_classification") == "uncertain":
            rows.append(dict(case_id=premise["case_id"], adjudication=record))
    for dependency in answer.get("dependencies", []):
        for conflict in dependency.get("decision_conflicts", []):
            if conflict.get("actor") == "agent" and conflict.get("decision") is None:
                rows.append(dict(case_id=dependency["case_id"], check=dependency["check"],
                    adjudication=conflict))
    return list({json.dumps(row, sort_keys=True): row for row in rows}.values())


def _metrics(answers, *, exclude_uncertain=False):
    result = {}
    for metric in ("correctness", "coverage"):
        selected = [row for row in answers if metric in row["score_differences"]
            and (not exclude_uncertain or not row["reference_uncertainty"])]
        changes = [row["score_differences"][metric]["automated_minus_reference"] for row in selected]
        result[metric] = dict(paired_answers=len(selected), total_answers=len(answers),
            missing_automated=sum(metric not in row["automated_scores"] for row in answers),
            missing_reference=sum(metric not in row["reference_scores"] for row in answers),
            uncertain_reference_answers=sum(bool(row["reference_uncertainty"]) for row in answers),
            excluded_uncertain_pairs=sum(metric in row["score_differences"] and bool(row["reference_uncertainty"])
                for row in answers) if exclude_uncertain else 0,
            changed_answers=sum(abs(change) > 1e-12 for change in changes),
            mean_signed_change_percentage_points=100 * sum(changes) / len(changes) if changes else None,
            mean_absolute_change_percentage_points=100 * sum(map(abs, changes)) / len(changes) if changes else None,
            maximum_absolute_change_percentage_points=100 * max(map(abs, changes)) if changes else None)
    return result


def _summary(answers):
    return dict(answers=len(answers), statuses={side: dict(Counter(row[side + "_status"] for row in answers))
        for side in ("automated", "reference")},
        complete_pairs=sum(row["automated_status"] == row["reference_status"] == "valid" for row in answers),
        reference_uncertain_answers=sum(bool(row["reference_uncertainty"]) for row in answers),
        metrics=_metrics(answers), metrics_without_uncertain_references=_metrics(answers, exclude_uncertain=True))


def compare(coverage_directory, reference_path, output, *, verification_experiments=None, automated_report=None):
    """Use the production collector without agent interventions, then compare paired answers."""
    from experiment_runner import experiment
    reference_path = Path(reference_path).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("grade comparison output already exists")
    reference = experiment.read(reference_path)
    if reference.get("analysis_only") or reference.get("policy") != "grading":
        raise ValueError("grade comparison requires an agent-audited grading reference")
    if Path(reference["coverage"]).resolve() != Path(coverage_directory).expanduser().resolve():
        raise ValueError("grade comparison requires the same frozen coverage preparation")
    protected = dict(reference["sources"])
    protected[str(reference_path)] = engine._sha256_file(reference_path)
    for path, checksum in protected.items():
        if engine._sha256_file(Path(path)) != checksum:
            raise ValueError("grade comparison reference source changed: " + path)
    if automated_report is None:
        automated_path = output / "automated.json"
        automated = coverage.collect(coverage_directory, automated_path,
            verification_experiments=verification_experiments, automated_analysis=True)
    else:
        if verification_experiments:
            raise ValueError("collected grade comparison cannot add verification experiments")
        automated_path = Path(automated_report).expanduser().resolve()
        automated = experiment.read(automated_path)
        if (automated.get("policy") != "grading"
                or not (automated.get("analysis_only") or automated.get("automatic_status") == "complete")
                or automated.get("semantic_audits_applied") is not False
                or automated.get("corrections_applied") is not False
                or automated.get("adjudication_summary")):
            raise ValueError("collected grade comparison requires original or complete automatic grades without agent corrections")
        if Path(automated["coverage"]).resolve() != Path(coverage_directory).expanduser().resolve():
            raise ValueError("collected grade comparison requires the same frozen coverage preparation")
    cohorts, summaries = {}, {}
    for cohort in ("random", "challenge"):
        expected = {answer["id"]: answer for answer in reference[cohort]["answers"]}
        actual = {answer["id"]: answer for answer in automated[cohort]["answers"]}
        if set(expected) != set(actual):
            raise ValueError("grade comparison requires exactly the same frozen answers")
        answers = []
        for identifier, original in actual.items():
            audited = expected[identifier]
            if original["note_id"] != audited["note_id"]:
                raise ValueError("grade comparison note differs")
            original_scores, reference_scores = original["scoring"].get("scores", {}), audited["scoring"].get("scores", {})
            uncertainty = _uncertainty(audited)
            differences = {metric: dict(automated=original_scores[metric], reference=reference_scores[metric],
                automated_minus_reference=original_scores[metric]["value"] - reference_scores[metric]["value"])
                for metric in ("correctness", "coverage") if metric in original_scores and metric in reference_scores}
            answers.append(dict(id=identifier, note_id=original["note_id"], version=identifier.rsplit("-N", 1)[0],
                automated_status=original["scoring"]["status"], reference_status=audited["scoring"]["status"],
                automated_scores=original_scores, reference_scores=reference_scores, score_differences=differences,
                reference_uncertainty=uncertainty, reference_uncertain=bool(uncertainty),
                automated_pending=original["scoring"].get("pending", {}),
                reference_pending=audited["scoring"].get("pending", {}),
                automated_dependencies=original.get("dependencies", []),
                reference_dependencies=audited.get("dependencies", [])))
        cohorts[cohort] = answers
        summaries[cohort] = dict(_summary(answers), versions={version: _summary([row for row in answers
            if row["version"] == version]) for version in sorted({row["version"] for row in answers})})
    for path, checksum in automated["sources"].items():
        if path in protected and protected[path] != checksum:
            raise ValueError("grade comparison shared source changed: " + path)
        protected[path] = checksum
    protected[str(automated_path)] = engine._sha256_file(automated_path)
    for path, checksum in protected.items():
        if engine._sha256_file(Path(path)) != checksum:
            raise ValueError("grade comparison source changed: " + path)
    result = dict(schema_version=1, analysis_only=True, inference_calls=0, reference=str(reference_path),
        reference_basis="Agent-audited development grades; not human-certified ground truth.",
        automated=str(automated_path), sources=protected,
        qualification="Known correction impact on paired available scores, not absolute grading error against gold. "
            "Missing grades are not zero. Random and challenge cohorts stay separate. "
            "Version cells contain different notes and few answers; these summaries do not establish model rankings.",
        score_units="Values are fractions; aggregate changes are percentage points.",
        audit_diagnostics=automated.get("audit_diagnostics", []), **summaries, paired_answers=cohorts)
    experiment.write(output / "comparison.json", result)
    return result
