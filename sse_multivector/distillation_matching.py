"""Source-bound matching controls and saved validation-wording previews.

Gold judgments describe controlled edits, never another reviewer response.
The catalog groups identical wording; required flags are outside this task.
"""
import hashlib
import json
from pathlib import Path

try:
    from . import distillation_review as review
    from . import extraction_pipeline as engine
except ImportError:
    import distillation_review as review
    import extraction_pipeline as engine


def prepare_source(source, base, selected=None, *, include_post=False):
    if isinstance(source, dict) and type(source.get("schema_version")) is int and source["schema_version"] == 2:
        return _prepare_generations(source, base, selected, include_post=include_post)
    review._fields(source, {"schema_version", "review_source", "cases"}, "matching source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected matching source schema_version 1")
    reference = source["review_source"]
    review._fields(reference, {"path", "sha256"}, "matching review reference")
    path = engine._resolve_path(reference["path"], "matching review source", Path(base))
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum != reference["sha256"]:
        raise ValueError(f"matching review source hash differs: {path}")
    original = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    if not isinstance(source["cases"], list) or not source["cases"]:
        raise ValueError("matching controls require nonempty cases")
    originals = {case["id"]: case for case in original["cases"]}
    identifiers, partitions = [], {}
    for definition in source["cases"]:
        review._fields(definition, {"id", "case", "student_number", "replacements",
            "expected_teacher_number", "expected_reason", "partition"}, "matching control")
        identifier = engine._expect_identifier(definition["id"], "matching case id")
        if identifier in identifiers:
            raise ValueError("duplicate matching case identity")
        identifiers.append(identifier)
        if definition["case"] not in originals:
            raise ValueError("unknown original review case")
        partition = definition["partition"]
        if partition not in {"development", "confirmation"}:
            raise ValueError("unknown matching control partition")
        original_reference = originals[definition["case"]]["reference"]
        note = original["references"][original_reference]
        note_key = ("training", note["note_id"]) if note["format"] == "training_jsonl" else ("example", note["index"])
        if partitions.setdefault(note_key, partition) != partition:
            raise ValueError("reference note crosses matching control partitions")
        if not isinstance(definition["expected_reason"], str) or not definition["expected_reason"].strip():
            raise ValueError("matching control needs an expected reason")
    if selected is not None and (len(selected) != len(set(selected)) or set(selected) - set(identifiers)):
        raise ValueError("unknown or duplicate matching case selection")
    definitions = [d for d in source["cases"] if selected is None or d["id"] in selected]
    original_ids = list(dict.fromkeys(d["case"] for d in definitions))
    saved, protected, _ = review.prepare_source(original, path.parent, original_ids,
                                               include_teacher_meanings=False)
    protected[str(path)] = checksum
    saved = {case["id"]: case for case in saved}
    cases = []
    for definition in definitions:
        original_case = saved[definition["case"]]
        payload = json.loads(original_case["inputs"]["REVIEW_INPUT"])
        students = {entry["number"]: entry["subject"] for entry in payload["student"]}
        if definition["student_number"] not in students:
            raise ValueError("unknown matching student number")
        subject = students[definition["student_number"]]
        if not isinstance(definition["replacements"], list):
            raise ValueError("matching replacements must be an array")
        for replacement in definition["replacements"]:
            review._fields(replacement, {"old", "new"}, "matching replacement")
            old, new = replacement["old"], replacement["new"]
            if (not isinstance(old, str) or not old or not isinstance(new, str)
                    or old not in subject or old == new):
                raise ValueError("matching replacement does not change the selected wording")
            subject = subject.replace(old, new)
        cases.append(_matching_case(definition, payload["teacher"], subject,
            dict(note_id=original_case["evidence"]["note_id"],
                 reference=original_case["evidence"]["reference"], partition=definition["partition"]),
            post=payload["post"] if include_post else None))
    return cases, protected, dict(qualification_case_ids=[d["id"] for d in definitions])


def _matching_case(definition, teacher, subject, evidence, *, post=None):
    catalog, by_subject, by_number, numbers = [], {}, {}, {}
    for entry in teacher:
        wording = entry["subject"]
        if wording not in by_subject:
            identifier = f"T{len(catalog) + 1:02d}"
            by_subject[wording] = identifier
            catalog.append(dict(id=identifier, subject=wording))
            numbers[identifier] = []
        identifier = by_subject[wording]
        by_number[entry["number"]] = identifier
        numbers[identifier].append(entry["number"])
    if not subject.strip():
        raise ValueError("matching subject must be nonempty")
    if subject in by_subject:
        raise ValueError("exact match belongs to mechanical preselection, not a model control")
    expected_number = definition["expected_teacher_number"]
    if expected_number is not None and (not isinstance(expected_number, str) or expected_number not in by_number):
        raise ValueError("unknown expected teacher number")
    match_input = dict(teacher_subjects=catalog, student_subject=subject)
    variables = dict(MATCH_INPUT=json.dumps(match_input, ensure_ascii=False))
    if post is not None:
        variables["POST"] = json.dumps(post, ensure_ascii=False)
    return dict(id=definition["id"],
        inputs=variables,
        evidence=dict(evidence, definition=definition,
            expected_teacher_id=None if expected_number is None else by_number[expected_number],
            expected_reason=definition["expected_reason"], teacher_numbers=numbers,
            teacher_entries=len(teacher), distinct_teacher_subjects=len(catalog)))


def _prepare_generations(source, base, selected, *, include_post):
    """Load validation outputs without opening reserved test generations.

    Actual-wording expectations are agent assessments, not independently
    adjudicated gold. Agreement with them cannot qualify the reviewer.
    """
    review._fields(source, {"schema_version", "dataset_manifest", "cases"}, "saved matching source")
    definitions = source["cases"]
    if not isinstance(definitions, list) or not definitions:
        raise ValueError("saved matching requires nonempty cases")
    identifiers = []
    for definition in definitions:
        review._fields(definition, {"id", "generation", "student_number", "expected_teacher_number",
            "expected_reason", "expectation_status", "selection"}, "saved matching case")
        identifier = engine._expect_identifier(definition["id"], "matching case id")
        if identifier in identifiers:
            raise ValueError("duplicate matching case identity")
        identifiers.append(identifier)
        if (definition["expectation_status"] not in {"agent_assessed", "unresolved"}
                or any(not isinstance(definition[field], str) or not definition[field].strip()
                       for field in ("expected_reason", "selection"))):
            raise ValueError("saved matching needs explicit expectation status and selection")
        if definition["expectation_status"] == "unresolved" and definition["expected_teacher_number"] is not None:
            raise ValueError("unresolved matching expectation cannot name a teacher")
    if selected is not None and (len(selected) != len(set(selected)) or set(selected) - set(identifiers)):
        raise ValueError("unknown or duplicate matching case selection")
    definitions = [d for d in definitions if selected is None or d["id"] in selected]
    loaded, protected = review.load_saved_generations(source["dataset_manifest"], definitions, base)
    cases = []
    for saved in loaded:
        definition = saved["definition"]
        students = {row["number"]: row["subject"] for row in saved["student"]}
        if definition["student_number"] not in students:
            raise ValueError("unknown matching student number")
        cases.append(_matching_case(definition, saved["teacher"], students[definition["student_number"]],
            dict(note_id=saved["note_id"], reference=source["dataset_manifest"],
                 generation=definition["generation"], expectation_status=definition["expectation_status"],
                 student_entries=len(saved["student"])),
            post=saved["post"] if include_post else None))
    return cases, protected, dict(qualification_case_ids=[d["id"] for d in definitions])


def validate(case, raw):
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    review._fields(value, {"teacher_id", "reason"}, "matching verdict")
    if not isinstance(value["reason"], str) or not value["reason"].strip():
        raise ValueError("matching verdict needs a nonempty reason")
    identifier = value["teacher_id"]
    catalog = json.loads(case["inputs"]["MATCH_INPUT"])["teacher_subjects"]
    if identifier is not None and (not isinstance(identifier, str) or identifier not in {row["id"] for row in catalog}):
        raise ValueError("invalid or unknown matching teacher id")
    expected = case["evidence"]["expected_teacher_id"]
    if case["evidence"].get("expectation_status") == "unresolved":
        return dict(status="valid", output=raw, parsed=value,
                    qualification=dict(passed=None, error=None,
                                       expected_teacher_id=None, actual_teacher_id=identifier))
    error = (None if identifier == expected else "false_match" if expected is None
             else "missed_match" if identifier is None else "wrong_match")
    return dict(status="valid", output=raw, parsed=value,
                qualification=dict(passed=error is None, error=error,
                                   expected_teacher_id=expected, actual_teacher_id=identifier))


def qualification(cases, all_case_ids):
    by_id = {case["id"]: case for case in cases}
    pending = [identifier for identifier in all_case_ids
               if identifier not in by_id or by_id[identifier]["status"] == "unrun"]
    completed = [case for case in cases if case["status"] == "valid"
                 and case["qualification"]["passed"] is not None]
    failures = [case["id"] for case in cases if case["status"] not in {"valid", "unrun"}]
    errors = {name: [case["id"] for case in completed if case["qualification"]["error"] == name]
              for name in ("false_match", "missed_match", "wrong_match")}
    failed = bool(failures or any(errors.values()))
    unverified = [case["id"] for case in cases if case["evidence"].get("expectation_status")
                  in {"agent_assessed", "unresolved"}]
    result = dict(status="failed" if failures else "pending" if unverified
                  else "failed" if failed else "pending" if pending else "passed",
                checked=len(completed), total=len(all_case_ids), pending=pending,
                mechanical_failures=failures, errors=errors)
    if unverified:
        result["unverified_expectations"] = unverified
        result["unresolved_expectations"] = [case["id"] for case in cases
                                              if case["evidence"].get("expectation_status") == "unresolved"]
    return result
