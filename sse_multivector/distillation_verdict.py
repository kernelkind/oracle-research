"""Source-bound, single-subject support and immediate parent-child controls.

Expectations come from authored controls or explicitly assessed saved validation
outputs, outside model input. Agent assessments remain unverified; preparing
these inputs does not qualify a reviewer or adopt pilot scoring.
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


def prepare_source(source, base, selected=None, *, include_post=False, include_teacher_contexts=False):
    if isinstance(source, dict) and type(source.get("schema_version")) is int and source["schema_version"] == 2:
        return _prepare_generations(source, base, selected, include_post=include_post,
                                    include_teacher_contexts=include_teacher_contexts)
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
    cases, indexes = [], {}
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
        invalid = original_case["evidence"]["expected"][
            "incorrect_subjects" if check == "support" else "invalid_relationship_children"]
        engine._validate_string_array(invalid, "expected invalid subjects", allow_empty=True)
        if set(invalid) - set(students):
            raise ValueError("expected invalid subject is absent from the source case")
        reference_key = original_case["evidence"]["reference"]
        if reference_key not in indexes:
            indexes[reference_key] = review._TeacherIndex(payload["teacher"])
        cases.append(_verdict_case(check, definition, payload["post"], students, task,
                                   evidence, number not in invalid, indexes[reference_key],
                                   include_post=include_post, include_teacher_contexts=include_teacher_contexts))
    return cases, protected, dict(check=check, qualification_case_ids=[d["id"] for d in definitions])


def _support_inputs(task, post, subject):
    end = "Derive broader headings by generalizing source meanings without adding restrictions."
    if task.count(end) != 1:
        raise ValueError("ASv6.100 support rule boundary differs")
    return dict(ASV6_100_SUPPORT_RULES=task[:task.index(end) + len(end)],
                SUPPORT_INPUT=json.dumps(dict(post=post, student_subject=subject), ensure_ascii=False))


def _relationship_inputs(task, parent, child, *, post=None, teacher_contexts=None):
    start = "Judge each parent-child pair using only its `subject` strings across possible posts in any domain."
    end = "The post's domain, `context` and other entries cannot supply a missing heading restriction."
    if task.count(start) != 1 or task.count(end) != 1 or task.index(start) > task.index(end):
        raise ValueError("ASv6.100 parent-child rule boundaries differ")
    variables = dict(ASV6_100_PARENT_CHILD_RULES=task[task.index(start):task.index(end) + len(end)],
                     RELATIONSHIP_INPUT=json.dumps(dict(parent_subject=parent, child_subject=child), ensure_ascii=False))
    if post is not None:
        variables["POST"] = post
    if teacher_contexts is not None:
        paragraphs = [paragraph for paragraph in task.split("\n\n")
                      if paragraph.startswith("Make each `subject` concise,")]
        if len(paragraphs) != 1:
            raise ValueError("ASv6.100 subject-wording guidance boundary differs")
        variables["ASV6_100_PARENT_CHILD_RULES"] = (
            paragraphs[0] + "\n\n" + variables["ASV6_100_PARENT_CHILD_RULES"])
        rows = [dict(subject=row["subject"], context=row["context"]) for row in teacher_contexts]
        rows = list({(row["subject"], row["context"]): row for row in rows}.values())
        variables["TEACHER_CONTEXTS"] = json.dumps(rows, ensure_ascii=False)
    return variables


def _verdict_case(check, definition, post, students, task, evidence, expected_valid, teacher,
                  *, include_post=False, include_teacher_contexts=False):
    number = definition["student_number"]
    if check == "support":
        subject = definition.get("student_subject", students[number])
        variables = _support_inputs(task, post, subject)
        mechanical = teacher.support(subject)
    else:
        parent_number = number.rpartition(".")[0]
        if parent_number not in students:
            raise ValueError("relationship control needs an actual immediate parent")
        evidence["parent_number"] = parent_number
        contexts = (teacher.interpretation_entries(students[parent_number], students[number])
                    if include_teacher_contexts else None)
        if contexts is not None:
            evidence["teacher_context_numbers"] = [row["number"] for row in contexts]
        variables = _relationship_inputs(task, students[parent_number], students[number],
                                         post=post if include_post else None, teacher_contexts=contexts)
        mechanical = teacher.relationship(students[parent_number], students[number])
    evidence["expected_valid"] = expected_valid
    case = dict(id=definition["id"], inputs=variables, evidence=evidence)
    if mechanical is not None:
        case["mechanical"] = mechanical
    return case


def _prepare_generations(source, base, selected, *, include_post, include_teacher_contexts):
    review._fields(source, {"schema_version", "check", "dataset_manifest", "cases"}, "saved verdict source")
    check = source["check"]
    if check not in {"support", "relationship"}:
        raise ValueError("verdict check must be support or relationship")
    definitions = source["cases"]
    if not isinstance(definitions, list) or not definitions:
        raise ValueError("saved verdicts require nonempty cases")
    identifiers = []
    for definition in definitions:
        fields = {"id", "generation", "student_number", "expected_valid",
                  "expected_reason", "expectation_status", "selection"}
        if check == "support" and isinstance(definition, dict) and "student_subject" in definition:
            fields.add("student_subject")
        review._fields(definition, fields, "saved verdict case")
        if "student_subject" in definition and (not isinstance(definition["student_subject"], str)
                                               or not definition["student_subject"].strip()):
            raise ValueError("saved support student subject must be a nonblank string")
        identifier = engine._expect_identifier(definition["id"], "verdict case id")
        if identifier in identifiers:
            raise ValueError("duplicate verdict case identity")
        identifiers.append(identifier)
        if (definition["expectation_status"] not in {"agent_assessed", "unresolved"}
                or any(not isinstance(definition[field], str) or not definition[field].strip()
                       for field in ("expected_reason", "selection", "student_number"))):
            raise ValueError("saved verdict needs explicit expectation status and selection")
        if definition["expectation_status"] == "unresolved":
            if definition["expected_valid"] is not None:
                raise ValueError("unresolved verdict expectation cannot have a Boolean label")
        elif type(definition["expected_valid"]) is not bool:
            raise ValueError("assessed verdict expectation must be a Boolean")
    if selected is not None:
        engine._validate_string_array(selected, "verdict case selection", allow_empty=False)
        if len(selected) != len(set(selected)) or set(selected) - set(identifiers):
            raise ValueError("unknown or duplicate verdict case selection")
    definitions = [d for d in definitions if selected is None or d["id"] in selected]
    loaded, protected = review.load_saved_generations(source["dataset_manifest"], definitions, base)
    cases, indexes = [], {}
    for saved in loaded:
        definition = saved["definition"]
        students = {row["number"]: row["subject"] for row in saved["student"]}
        if definition["student_number"] not in students:
            raise ValueError("unknown verdict student number")
        evidence = dict(check=check, note_id=saved["note_id"], reference=source["dataset_manifest"],
            generation=definition["generation"], student_number=definition["student_number"],
            student_entries=len(saved["student"]), expectation_status=definition["expectation_status"],
            selection=definition["selection"], expected_reason=definition["expected_reason"])
        if "student_subject" in definition:
            evidence.update(original_student_subject=students[definition["student_number"]],
                            student_subject=definition["student_subject"])
        if saved["note_id"] not in indexes:
            indexes[saved["note_id"]] = review._TeacherIndex(saved["teacher"])
        cases.append(_verdict_case(check, definition, saved["post"], students,
            saved["task_prompt"], evidence, definition["expected_valid"], indexes[saved["note_id"]],
            include_post=include_post, include_teacher_contexts=include_teacher_contexts))
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
        qualification=dict(passed=None if expected is None else value["valid"] == expected,
                           expected_valid=expected, actual_valid=value["valid"]))


def qualification(cases, all_case_ids):
    by_id = {case["id"]: case for case in cases}
    pending = [identifier for identifier in all_case_ids
               if identifier not in by_id or by_id[identifier]["status"] == "unrun"]
    completed = [by_id[identifier] for identifier in all_case_ids
                 if identifier in by_id and by_id[identifier]["status"] == "valid"
                 and by_id[identifier]["qualification"]["passed"] is not None]
    failures = [identifier for identifier in all_case_ids if identifier in by_id
                and by_id[identifier]["status"] not in {"valid", "unrun"}]
    incorrect = [case["id"] for case in completed if not case["qualification"]["passed"]]
    unverified = [case["id"] for case in cases if case["evidence"].get("expectation_status")
                  in {"agent_assessed", "unresolved"}]
    result = dict(status="failed" if failures else "pending" if unverified
                  else "failed" if incorrect else "pending" if pending else "passed",
                checked=len(completed), total=len(all_case_ids), pending=pending,
                mechanical_failures=failures, incorrect_verdicts=incorrect)
    mechanical = [case["id"] for case in cases if case.get("origin") == "mechanical"]
    if mechanical:
        result.update(mechanical_cases=mechanical,
                      model_checked=sum(case.get("origin") != "mechanical" for case in completed))
    if unverified:
        result["unverified_expectations"] = unverified
        result["unresolved_expectations"] = [case["id"] for case in cases
                                              if case["evidence"].get("expectation_status") == "unresolved"]
    return result
