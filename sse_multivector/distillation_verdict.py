"""Source-bound, single-subject support and immediate parent-child controls.

Expectations come from the selected authored review cases, outside model input.
This prepares development controls; it does not grade the pilot or qualify a
reviewer for production use.
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


def prepare_source(source, base, selected=None):
    review._fields(source, {"schema_version", "check", "review_source", "cases"}, "verdict source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected verdict source schema_version 1")
    check = source["check"]
    if check not in {"support", "relationship"}:
        raise ValueError("verdict check must be support or relationship")
    reference = source["review_source"]
    review._fields(reference, {"path", "sha256"}, "verdict review reference")
    path = engine._resolve_path(reference["path"], "verdict review source", Path(base))
    raw = path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if checksum != reference["sha256"]:
        raise ValueError(f"verdict review source hash differs: {path}")
    original = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    if not isinstance(source["cases"], list) or not source["cases"]:
        raise ValueError("verdict controls require nonempty cases")
    identifiers = []
    original_ids = {case["id"] for case in original["cases"]}
    for definition in source["cases"]:
        review._fields(definition, {"id", "case", "student_number", "expected_reason"}, "verdict control")
        identifier = engine._expect_identifier(definition["id"], "verdict case id")
        if identifier in identifiers:
            raise ValueError("duplicate verdict case identity")
        identifiers.append(identifier)
        if definition["case"] not in original_ids:
            raise ValueError("unknown original review case")
        if not isinstance(definition["expected_reason"], str) or not definition["expected_reason"].strip():
            raise ValueError("verdict control needs an expected reason")
        if not isinstance(definition["student_number"], str):
            raise ValueError("verdict student number must be a string")
    if selected is not None:
        engine._validate_string_array(selected, "verdict case selection", allow_empty=False)
        if len(selected) != len(set(selected)) or set(selected) - set(identifiers):
            raise ValueError("unknown or duplicate verdict case selection")
    definitions = [d for d in source["cases"] if selected is None or d["id"] in selected]
    saved, protected, _ = review.prepare_source(original, path.parent,
        list(dict.fromkeys(d["case"] for d in definitions)), include_teacher_meanings=False)
    protected[str(path)] = checksum
    saved = {case["id"]: case for case in saved}
    cases = []
    for definition in definitions:
        original_case = saved[definition["case"]]
        payload = json.loads(original_case["inputs"]["REVIEW_INPUT"])
        students = {entry["number"]: entry["subject"] for entry in payload["student"]}
        number = definition["student_number"]
        if number not in students:
            raise ValueError("unknown verdict student number")
        task = original_case["inputs"]["TASK_PROMPT"]
        evidence = dict(check=check, source_case=definition["case"], student_number=number,
            note_id=original_case["evidence"]["note_id"], reference=original_case["evidence"]["reference"],
            expected_reason=definition["expected_reason"])
        if check == "support":
            end = "Derive broader headings by generalizing source meanings without adding restrictions."
            if task.count(end) != 1:
                raise ValueError("ASv6.100 support rule boundary differs")
            variables = dict(ASV6_100_SUPPORT_RULES=task[:task.index(end) + len(end)],
                SUPPORT_INPUT=json.dumps(dict(post=payload["post"], student_subject=students[number]),
                                         ensure_ascii=False))
            invalid = original_case["evidence"]["expected"]["incorrect_subjects"]
        else:
            parent_number = number.rpartition(".")[0]
            if parent_number not in students:
                raise ValueError("relationship control needs an actual immediate parent")
            evidence["parent_number"] = parent_number
            start = "Judge each parent-child pair using only its `subject` strings across possible posts in any domain."
            end = "The post's domain, `context` and other entries cannot supply a missing heading restriction."
            if task.count(start) != 1 or task.count(end) != 1 or task.index(start) > task.index(end):
                raise ValueError("ASv6.100 parent-child rule boundaries differ")
            variables = dict(ASV6_100_PARENT_CHILD_RULES=task[task.index(start):task.index(end) + len(end)],
                RELATIONSHIP_INPUT=json.dumps(dict(parent_subject=students[parent_number],
                    child_subject=students[number]), ensure_ascii=False))
            invalid = original_case["evidence"]["expected"]["invalid_relationship_children"]
        engine._validate_string_array(invalid, "expected invalid subjects", allow_empty=True)
        if set(invalid) - set(students):
            raise ValueError("expected invalid subject is absent from the source case")
        evidence["expected_valid"] = number not in invalid
        cases.append(dict(id=definition["id"], inputs=variables, evidence=evidence))
    return cases, protected, dict(check=check, qualification_case_ids=[d["id"] for d in definitions])


def validate(case, raw):
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    review._fields(value, {"valid", "reason"}, "support/relationship verdict")
    if type(value["valid"]) is not bool:
        raise ValueError("verdict valid must be a JSON Boolean")
    if not isinstance(value["reason"], str) or not value["reason"].strip():
        raise ValueError("verdict needs a nonempty reason")
    expected = case["evidence"]["expected_valid"]
    return dict(status="valid", output=raw, parsed=value,
        qualification=dict(passed=value["valid"] == expected,
                           expected_valid=expected, actual_valid=value["valid"]))


def qualification(cases, all_case_ids):
    by_id = {case["id"]: case for case in cases}
    pending = [identifier for identifier in all_case_ids
               if identifier not in by_id or by_id[identifier]["status"] == "unrun"]
    completed = [by_id[identifier] for identifier in all_case_ids
                 if identifier in by_id and by_id[identifier]["status"] == "valid"]
    failures = [identifier for identifier in all_case_ids if identifier in by_id
                and by_id[identifier]["status"] not in {"valid", "unrun"}]
    incorrect = [case["id"] for case in completed if not case["qualification"]["passed"]]
    return dict(status="failed" if failures or incorrect else "pending" if pending else "passed",
                checked=len(completed), total=len(all_case_ids), pending=pending,
                mechanical_failures=failures, incorrect_verdicts=incorrect)
