"""Native checks for complete source-bound saved subject answers.

Numbered occurrences remain separate cases. The shared runner reuses identical
requests and owns model execution, warmups, receipt validation and usage.
"""
import hashlib
import json
from pathlib import Path

from . import distillation_matching as matching
from . import distillation_review as review
from . import distillation_review_preview as preview
from . import distillation_verdict as verdict
from . import extraction_pipeline as engine


_DEFINITIONS = dict(
    matching=("DSMv3", "matching-prompt-v3.md", "matching-response-schema.json", "MATCH_INPUT", "student_subject"),
    support=("DSSv2", "support-prompt-v2.md", "boolean-response-schema.json", "SUPPORT_INPUT", "student_subject"),
    relationship=("DSLv2", "relationship-prompt-v2.md", "boolean-response-schema.json", "RELATIONSHIP_INPUT", "child_subject"))


def review_prefix(template, variables, payload, field, render):
    """Share relationship instructions and post across different parent wordings."""
    if field == "child_subject" and "{POST}" in template:
        boundary = "{TEACHER_CONTEXTS}" if "{TEACHER_CONTEXTS}" in template else "{" + payload + "}"
        head = template[:template.index(boundary)]
        fixed = {key: value for key, value in variables.items() if "{" + key + "}" in head}
        return render(head, fixed)
    return preview._natural_prefix(template, variables, payload, field, render)


def _selection(reference, base):
    from .distillation_review_trial import load_trial
    review._fields(reference, {"path", "sha256"}, "review evaluation selection")
    path = engine._resolve_path(reference["path"], "review evaluation selection", Path(base))
    if engine._sha256_file(path) != reference["sha256"]:
        raise ValueError("review evaluation selection hash differs")
    bundle = load_trial(path)
    return bundle, {**bundle["sources"], str(path): reference["sha256"]}


def _assessments(directory, bundle):
    if directory is None:
        return dict(contexts={}, expectations={}, sources={})
    from .distillation_review_assessment import load_assessments
    return load_assessments(directory, bundle)


def compatibility_case(answer, group, ordinal, number, assessments=None, *, include_post=False,
                       include_teacher_contexts=False, teacher=None, students=None):
    """Construct one reached teacher/student comparison using the native contract."""
    teacher = review._TeacherIndex(answer["teacher"]) if teacher is None else teacher
    students = {row["number"]: row["subject"] for row in answer["student"]} if students is None else students
    representative = group["teacher_numbers"][0]
    child, heading = teacher.subjects[representative], students[number]
    expected = {} if assessments is None else assessments["expectations"].get(answer["id"], {})
    label = next((row for row in expected.get("compatibility", [])
                  if frozenset(row["teacher_numbers"]) == frozenset(group["teacher_numbers"])), None)
    headings = None if label is None else label["compatible_heading_numbers"]
    expected_valid = None if headings is None else number in headings
    evidence = dict(check="relationship", role="compatibility", answer_id=answer["id"], cohort=answer["cohort"],
        note_id=answer["note_id"], generation=answer["generation"], heading_number=number,
        teacher_numbers=group["teacher_numbers"], teacher_representative_number=representative,
        expectation_status="unresolved" if expected_valid is None else "agent_assessed",
        expected_valid=expected_valid, expected_reason="Not independently assessed." if label is None else label["reason"])
    contexts = (teacher.interpretation_entries(heading, child, child_number=representative)
                if include_teacher_contexts else None)
    if contexts is not None:
        evidence["teacher_context_numbers"] = [row["number"] for row in contexts]
    case = dict(id=answer["id"] + f":compatibility:{ordinal:03}:" + number,
        inputs=verdict._relationship_inputs(answer["task_prompt"], heading, child,
            post=answer["post"] if include_post else None, teacher_contexts=contexts), evidence=evidence)
    mechanical = teacher.relationship(heading, child)
    if mechanical is not None:
        case["mechanical"] = mechanical
    return case


def _cases(bundle, check, assessments, *, include_post=False, include_teacher_contexts=False,
           actual_edges_only=False, selected=None):
    cases = []
    wanted = None if selected is None else set(selected)
    wanted_answers = None if wanted is None else {identifier.split(":", 1)[0] for identifier in wanted}
    for answer in bundle["random"]["answers"] + bundle["challenge"]["answers"]:
        if answer["errors"] or (wanted_answers is not None and answer["id"] not in wanted_answers):
            continue
        teacher = review._TeacherIndex(answer["teacher"])
        students = {row["number"]: row["subject"] for row in answer["student"]}
        expected = assessments["expectations"].get(answer["id"], {})
        field = "relationships" if check == "relationship" else check
        labels = {row["child" if check == "relationship" else "student_number"]: row
                  for row in expected.get(field, [])}
        for number, subject in students.items():
            if check == "relationship" and not number.rpartition(".")[0]:
                continue
            identifier = answer["id"] + ":" + number
            if wanted is not None and identifier not in wanted:
                continue
            evidence = dict(check=check, answer_id=answer["id"], cohort=answer["cohort"],
                note_id=answer["note_id"], generation=answer["generation"], student_number=number,
                student_entries=len(students), expectation_status="unresolved",
                selection="Complete frozen selected answer.", expected_reason="Not independently assessed.")
            definition = dict(id=identifier, student_number=number, expected_teacher_number=None,
                expected_reason=evidence["expected_reason"])
            label = labels.get(number)
            if label is not None:
                evidence["expected_reason"] = definition["expected_reason"] = label["reason"]
                resolved = not label.get("unresolved", False) if check == "matching" else label["valid"] is not None
                evidence["expectation_status"] = "agent_assessed" if resolved else "unresolved"
            if check == "matching":
                if label is not None:
                    definition["expected_teacher_number"] = label["teacher_number"]
                case = matching._matching_case(definition, teacher, subject, evidence, post=answer["post"])
            else:
                evidence["role"] = "support" if check == "support" else "actual_relationship"
                case = verdict._verdict_case(check, definition, answer["post"], students,
                    answer["task_prompt"], evidence, None if label is None else label["valid"], teacher,
                    include_post=include_post, include_teacher_contexts=include_teacher_contexts)
            cases.append(case)
        if check == "relationship" and not actual_edges_only:
            for ordinal, group in enumerate(assessments["contexts"].get(answer["id"], []), 1):
                if not group["required"]:
                    continue
                for number in students:
                    if wanted is not None and answer["id"] + f":compatibility:{ordinal:03}:" + number not in wanted:
                        continue
                    cases.append(compatibility_case(answer, group, ordinal, number, assessments,
                        include_post=include_post, include_teacher_contexts=include_teacher_contexts,
                        teacher=teacher, students=students))
    return cases


def _source_state(path):
    try:
        stamp = Path(path).stat()
    except FileNotFoundError:
        return None
    return stamp.st_dev, stamp.st_ino, stamp.st_size, stamp.st_mtime_ns, stamp.st_ctime_ns


def prepare_source(source, base, selected=None, *, include_post=False, include_teacher_contexts=False,
                   preparation_context=None):
    """Turn a verified trial selection into existing matching/verdict cases."""
    review._fields(source, {"schema_version", "selection", "check", "assessment_directory"}
                   | ({"actual_edges_only"} & source.keys()),
                   "review evaluation source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected review evaluation source schema_version 1")
    check = source["check"]
    if check not in _DEFINITIONS:
        raise ValueError("unknown review evaluation check")
    actual_edges_only = source.get("actual_edges_only", False)
    if type(actual_edges_only) is not bool:
        raise ValueError("actual_edges_only must be a Boolean")
    if selected is not None:
        engine._validate_string_array(selected, "review evaluation case selection", allow_empty=False)
        if len(selected) != len(set(selected)):
            raise ValueError("unknown or duplicate review evaluation case selection")
    directory = source["assessment_directory"]
    if directory is not None:
        directory = engine._resolve_path(directory, "review assessment directory", Path(base))
    selection_path = engine._resolve_path(source["selection"]["path"], "review evaluation selection", Path(base))
    key = (str(selection_path), source["selection"]["sha256"], str(directory))
    cache = {} if preparation_context is None else preparation_context.setdefault("review_evaluation_sources", {})
    cached = cache.get(key)
    if cached is None:
        bundle, sources = _selection(source["selection"], base)
        assessments = _assessments(directory, bundle)
        sources.update(assessments["sources"])
        state = {path: _source_state(path) for path in sources}
        if directory is not None:
            state[str(directory)] = _source_state(directory)
        cache[key] = bundle, assessments, sources, state
    else:
        bundle, assessments, sources, state = cached
        for path, stamp in state.items():
            if _source_state(path) != stamp:
                raise ValueError("review evaluation source changed: " + path)
    cases = _cases(bundle, check, assessments, include_post=include_post,
                   include_teacher_contexts=include_teacher_contexts, actual_edges_only=actual_edges_only,
                   selected=selected)
    identifiers = [case["id"] for case in cases]
    if selected is not None:
        if set(selected) - set(identifiers):
            raise ValueError("unknown or duplicate review evaluation case selection")
    return cases, sources, dict(check=check, qualification_case_ids=[case["id"] for case in cases])


def validate(case, raw):
    """Keep the established typed response and label-comparison contracts."""
    return (matching.validate(case, raw) if case["evidence"]["check"] == "matching"
            else verdict.validate(case, raw))


def _answer_subset(bundle, answer_ids):
    if answer_ids is None:
        return bundle
    if (not isinstance(answer_ids, list) or not answer_ids
            or any(not isinstance(identifier, str) or not identifier.strip() for identifier in answer_ids)):
        raise ValueError("answer_ids must be a nonempty array of nonempty strings")
    known = {answer["id"] for cohort in ("random", "challenge") for answer in bundle[cohort]["answers"]}
    if len(answer_ids) != len(set(answer_ids)) or set(answer_ids) - known:
        raise ValueError("unknown or duplicate answer_ids")
    wanted = set(answer_ids)
    return dict(bundle, **{cohort: dict(bundle[cohort], answers=[
        answer for answer in bundle[cohort]["answers"] if answer["id"] in wanted])
        for cohort in ("random", "challenge")})


def prepare(selection_path, output, *, runner_binary=None, history_root=None, assessment_directory=None,
            reasoning_effort=None, matching_reasoning_effort=None, support_reasoning_effort=None,
            relationship_prompt=None, relationship_prompt_id=None,
            relationship_runner_binary=None, answer_ids=None, relationship_history_root=None,
            actual_edges_only=False):
    """Freeze native check groups; preparation never performs inference."""
    from experiment_runner import experiment, inputs, project, prompt_cache
    project.configure(Path(__file__).resolve().parents[1])
    if type(actual_edges_only) is not bool:
        raise ValueError("actual_edges_only must be a Boolean")
    if reasoning_effort is not None and reasoning_effort not in ("xhigh", "high", "medium", "low"):
        raise ValueError("reasoning_effort must be xhigh, high, medium or low")
    if matching_reasoning_effort is not None and matching_reasoning_effort not in ("xhigh", "high", "medium", "low"):
        raise ValueError("matching_reasoning_effort must be xhigh, high, medium or low")
    if support_reasoning_effort is not None and support_reasoning_effort not in ("xhigh", "high", "medium", "low"):
        raise ValueError("support_reasoning_effort must be xhigh, high, medium or low")
    if (relationship_prompt is None) != (relationship_prompt_id is None):
        raise ValueError("--relationship-prompt and --relationship-prompt-id must be supplied together")
    definitions = dict(_DEFINITIONS)
    if relationship_prompt is not None:
        identifier = engine._expect_identifier(relationship_prompt_id, "relationship prompt ID")
        path = Path(relationship_prompt).expanduser().resolve()
        definitions["relationship"] = (identifier, str(path), *_DEFINITIONS["relationship"][2:])
    selection_path = Path(selection_path).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("review evaluation output already exists")
    reference = dict(path=str(selection_path), sha256=engine._sha256_file(selection_path))
    bundle, _ = _selection(reference, selection_path.parent)
    scoped = _answer_subset(bundle, answer_ids)
    if assessment_directory is not None:
        assessment_directory = str(Path(assessment_directory).expanduser().resolve())
    assessments = _assessments(assessment_directory, bundle)
    directory = Path(__file__).parent / "distillation-review-v1"
    groups = []
    for check, (identifier, filename, schema, payload, field) in definitions.items():
        template = (directory / filename).read_text()
        ordinary, prefixes = [], {}
        for case in _cases(scoped, check, assessments, include_post='{POST}' in template,
                           include_teacher_contexts='{TEACHER_CONTEXTS}' in template,
                           actual_edges_only=actual_edges_only):
            if "mechanical" in case:
                ordinary.append(case["id"])
                continue
            text = inputs.render(template, case["inputs"])
            prefix = review_prefix(template, case["inputs"], payload, field, inputs.render)
            if not text.startswith(prefix):
                raise ValueError("review evaluation natural prefix differs from rendered prompt")
            group = prefixes.setdefault(prefix, dict(cases=[], inputs=set()))
            group["cases"].append(case["id"])
            group["inputs"].add(inputs.digest(case["inputs"]))
        for prefix, group in prefixes.items():
            if len(group["inputs"]) > 1 and prompt_cache.prefix_policy(prefix)["eligible"]:
                groups.append(dict(check=check, name=check + "-prefix-" + hashlib.sha256(prefix.encode()).hexdigest()[:12],
                    cases=group["cases"], prefix=prefix, distinct_inputs=len(group["inputs"])))
            else:
                ordinary.extend(group["cases"])
        if ordinary:
            groups.append(dict(check=check, name=check + "-ordinary", cases=ordinary, prefix=None))
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    experiments = []
    preparation_context = {}
    configurations = {}
    for check in definitions:
        identifier, filename, schema = definitions[check][:3]
        runner = {key: bundle["settings"][key] for key in (
            "provider", "model", "reasoning_effort", "transport")}
        if reasoning_effort is not None:
            runner["reasoning_effort"] = reasoning_effort
        if check == "matching" and matching_reasoning_effort is not None:
            runner["reasoning_effort"] = matching_reasoning_effort
        if check == "support" and support_reasoning_effort is not None:
            runner["reasoning_effort"] = support_reasoning_effort
        runner["auth_file"] = None
        runner["timeout_seconds"] = 3600
        runner["output_schema_path"] = str(directory / schema)
        binary = runner_binary
        if check == "relationship" and relationship_runner_binary is not None:
            binary = relationship_runner_binary
        if binary is not None:
            runner["runner_binary"] = str(Path(binary).expanduser().resolve())
        configurations[check] = dict(prompt=dict(id=identifier, path=str(directory / filename),
            sha256=engine._sha256_file(directory / filename)), runner=runner)
    for group in groups:
        check = group["check"]
        source = output / "sources" / (group["name"] + ".json")
        experiment.write(source, dict(schema_version=1, selection=reference, check=check,
                                      assessment_directory=assessment_directory,
                                      **({"actual_edges_only": True} if actual_edges_only else {})))
        configuration = configurations[check]
        spec = output / "specs" / (group["name"] + ".json")
        experiment.write(spec, dict(schema_version=1, prompt={key: configuration["prompt"][key] for key in ("id", "path")},
            dataset=dict(adapter="distillation_review_evaluation", path=str(source), select=group["cases"]),
            runner=configuration["runner"]))
        destination = output / "experiments" / group["name"]
        history = history_root
        if check == "relationship" and relationship_history_root is not None:
            history = relationship_history_root
        arguments = ["prepare", str(destination), "--spec", str(spec), "--history-root",
                     str(Path(history).resolve() if history is not None else output),
                     "--publication-role", "internal"]
        if group["prefix"] is not None:
            prefix_path = output / "prefixes" / (group["name"] + ".txt")
            prefix_path.parent.mkdir(exist_ok=True)
            prefix_path.write_text(group["prefix"])
            arguments.extend(["--prompt-cache-prefix", str(prefix_path)])
        experiment.prepare(experiment.parser().parse_args(arguments), include_request_preview=False,
                           preparation_context=preparation_context)
        experiments.append(dict(check=check, path=str(destination),
            sha256=engine._sha256_file(destination / "experiment.json"), occurrences=len(group["cases"]),
            prefix_cached=group["prefix"] is not None))
    if _assessments(assessment_directory, bundle)["sources"] != assessments["sources"]:
        raise ValueError("review assessments changed while preparing")
    frozen = dict(schema_version=3 if actual_edges_only else 2, selection=reference, assessment_directory=assessment_directory,
                  assessment_sources=assessments["sources"],
                  experiments=experiments, inference_calls=0)
    if actual_edges_only:
        configured = configurations["relationship"]
        paths = [configured["prompt"]["path"], configured["runner"]["output_schema_path"]]
        if configured["runner"].get("runner_binary"):
            paths.append(configured["runner"]["runner_binary"])
        frozen.update(relationship_configuration=configured,
            configuration_sources={path: engine._sha256_file(Path(path)) for path in paths})
    if answer_ids is not None:
        frozen["answer_ids"] = answer_ids
    experiment.write(output / "evaluation.json", frozen)
    experiment.write(output / "evaluation.complete.json", {"evaluation.json": engine._sha256_file(output / "evaluation.json")})
    return dict(frozen, output=str(output), summary=report(output)["summary"])


def report(output, *, include_request_summary=True):
    """Join native outcomes to every selected answer and numbered occurrence."""
    from experiment_runner import experiment, project
    project.configure(Path(__file__).resolve().parents[1])
    output = Path(output).expanduser().resolve()
    frozen = experiment.read(output / "evaluation.json")
    if type(frozen["schema_version"]) is not int or frozen["schema_version"] not in {1, 2, 3}:
        raise ValueError("unknown review evaluation schema_version")
    if experiment.read(output / "evaluation.complete.json") != {
            "evaluation.json": engine._sha256_file(output / "evaluation.json")}:
        raise ValueError("review evaluation preparation changed")
    bundle, sources = _selection(frozen["selection"], output)
    assessments = _assessments(frozen["assessment_directory"], bundle)
    if assessments["sources"] != frozen["assessment_sources"]:
        raise ValueError("review assessment snapshot changed")
    sources.update(assessments["sources"])
    if frozen["schema_version"] >= 3:
        for path, checksum in frozen["configuration_sources"].items():
            if engine._sha256_file(Path(path)) != checksum:
                raise ValueError("review evaluation relationship configuration changed: " + path)
            sources[path] = checksum
    bundle = _answer_subset(bundle, frozen.get("answer_ids"))
    cases, experiments, by_answer = {}, [], {}
    for entry in frozen["experiments"]:
        path = Path(entry["path"])
        if engine._sha256_file(path / "experiment.json") != entry["sha256"]:
            raise ValueError("review evaluation native preparation changed")
        native = experiment.report(path, generation_costs=True, include_request_preview=False)
        experiments.append(native)
        for case in native["cases"]:
            key = (entry["check"], case["id"])
            if key in cases:
                raise ValueError("duplicate review evaluation occurrence")
            cases[key] = case
            by_answer.setdefault(case["evidence"]["answer_id"], {}).setdefault(entry["check"], []).append(case)
    expected = {(check, case["id"]) for check in _DEFINITIONS for case in _cases(bundle, check, assessments,
                actual_edges_only=frozen["schema_version"] >= 3)}
    if set(cases) != expected:
        raise ValueError("review evaluation omitted or added numbered occurrences")
    cohorts = {}
    for cohort in ("random", "challenge"):
        answers = []
        for answer in bundle[cohort]["answers"]:
            answer_cases = by_answer.get(answer["id"], {})
            checks = {check: answer_cases.get(check, []) for check in _DEFINITIONS}
            context = assessments["contexts"].get(answer["id"])
            if frozen["schema_version"] >= 2:
                _apply_stopping(answer, checks, context)
            all_cases = [case for rows in checks.values() for case in rows]
            complete = all(case["status"] in {"valid", "skipped"} for case in all_cases)
            failed = any(case["status"] not in {"valid", "skipped", "unrun"} for case in all_cases)
            findings = dict(
                incorrect_subjects=[case["evidence"]["student_number"] for case in checks["support"]
                                    if case["status"] == "valid" and not case["parsed"]["valid"]],
                invalid_relationships=[dict(parent=case["evidence"]["parent_number"], child=case["evidence"]["student_number"])
                    for case in checks["relationship"] if case["evidence"]["role"] == "actual_relationship"
                    and case["status"] == "valid" and not case["parsed"]["valid"]],
                unmatched_subjects=[case["evidence"]["student_number"] for case in checks["matching"]
                                    if case["status"] == "valid" and case["parsed"]["teacher_id"] is None])
            result = dict(answer, status="invalid_output" if answer["errors"] else "complete" if complete else "failed" if failed else "pending",
                checks=checks, findings=findings, coverage=dict(status="pending",
                    reason="Independent teacher meaning groups, required flags and compatible-heading checks are needed."))
            if answer["errors"]:
                failure = review.score_saved_output({}, answer["raw_answer"]["raw"],
                    truncated=answer["raw_answer"]["truncated"])
                result.update(scores=failure["scores"], expected_scores=failure["scores"],
                    expected_score_basis="The existing saved-output failure rule, independent of semantic judgments.",
                    coverage=dict(status="output_failure", reason=failure["error"]))
            elif complete and context is not None:
                try:
                    scored = _score(answer, checks, context, partial=frozen["schema_version"] >= 2)
                except ValueError as error:
                    result["coverage"] = dict(status="pending", reason=str(error))
                    result["status"] = "inconsistent_verdicts"
                else:
                    if scored["status"] != "valid":
                        result["status"] = scored["status"]
                        result["coverage"] = dict(status="pending",
                            reason=scored.get("error", scored.get("reason", "Undetermined score.")))
                        result["score_evidence"] = scored
                        scored = None
                    if scored is not None:
                        result.update(scores=scored["scores"],
                            scoring_basis="Assembled from the separate verified native checks; no additional model call or receipt.",
                            coverage=dict(status="complete", findings=scored["findings"]["coverage"]))
                        if "parsed" in scored:
                            result["assembled_review"] = scored["parsed"]
                        else:
                            result["score_evidence"] = scored
            if not answer["errors"] and context is not None:
                gold = _expected_checks(checks)
                if gold is not None:
                    try:
                        expected = _score(answer, gold, context)
                    except ValueError as error:
                        result["expected_score_error"] = str(error)
                    else:
                        result.update(expected_scores=expected["scores"],
                            expected_score_basis="Pre-call agent-assessed expectations and independent frozen teacher context; not reviewer output.")
            result["qualification"] = _qualification(result, all_cases)
            answers.append(result)
        cohorts[cohort] = dict(answers=answers)
    usage, generation_usage = _usage(experiments, sources)
    summary = {cohort: dict(answers=len(value["answers"]),
        statuses={status: sum(row["status"] == status for row in value["answers"])
                  for status in sorted({row["status"] for row in value["answers"]})},
        score_comparisons=sum("scores" in row and "expected_scores" in row for row in value["answers"]),
        score_mismatches=sum(bool(row["qualification"]["score_differences"]) for row in value["answers"]),
        checks={check: _check_summary([case for row in value["answers"] for case in row["checks"][check]])
                for check in _DEFINITIONS}) for cohort, value in cohorts.items()}
    if include_request_summary:
        skipped = {(check, case["id"]) for value in cohorts.values() for answer in value["answers"]
                   for check, rows in answer["checks"].items() for case in rows if case["status"] == "skipped"}
        summary["requests"] = _request_summary(experiments, skipped)
    return dict(schema_version=1, output=str(output), selection=frozen["selection"], sources=sources,
                experiments=experiments, usage=usage, generation_usage=generation_usage, summary=summary, **cohorts,
                **({"actual_edges_only": True, "relationship_configuration": frozen["relationship_configuration"]}
                   if frozen["schema_version"] >= 3 else {}))


def _expected_checks(checks):
    gold = {}
    for check, rows in checks.items():
        gold[check] = []
        for row in rows:
            evidence = row["evidence"]
            if evidence["expectation_status"] == "unresolved":
                return None
            parsed = dict(reason=evidence["expected_reason"])
            parsed["teacher_id" if check == "matching" else "valid"] = evidence[
                "expected_teacher_id" if check == "matching" else "expected_valid"]
            gold[check].append(dict(row, status="valid", parsed=parsed))
    return gold


def _qualification(answer, rows):
    incorrect = [row["id"] for row in rows if row.get("qualification", {}).get("passed") is False]
    unresolved = [row["id"] for row in rows if row["evidence"]["expectation_status"] == "unresolved"]
    skipped = [row["id"] for row in rows if row["status"] == "skipped"]
    differences = {}
    if "scores" in answer and "expected_scores" in answer:
        differences = {metric: dict(actual=value["value"], expected=answer["expected_scores"][metric]["value"])
            for metric, value in answer["scores"].items() if value["value"] != answer["expected_scores"][metric]["value"]}
    return dict(basis="agent_assessed" if not answer["errors"] else "saved_output_failure",
        status="failed" if incorrect or differences or answer["status"] in {"failed", "inconsistent_verdicts"}
               else "pending" if unresolved or skipped or "scores" not in answer or "expected_scores" not in answer else "passed",
        checked=sum(type(row.get("qualification", {}).get("passed")) is bool for row in rows),
        incorrect_cases=incorrect, unresolved=unresolved, skipped_cases=skipped, score_differences=differences)


def _check_summary(rows):
    result = dict(occurrences=len(rows), mechanical=sum(row.get("origin") == "mechanical" for row in rows),
        semantic=sum(row.get("origin") != "mechanical" for row in rows),
        distinct_semantic_inputs=len({row["input_sha256"] for row in rows if row.get("origin") != "mechanical"}),
        reused=sum(row.get("reused", False) for row in rows),
        checked=sum(type(row.get("qualification", {}).get("passed")) is bool for row in rows),
        incorrect_cases=[row["id"] for row in rows if row.get("qualification", {}).get("passed") is False],
        unresolved=sum(row["evidence"]["expectation_status"] == "unresolved" for row in rows),
        pending=sum(row["status"] == "unrun" for row in rows),
        skipped=sum(row["status"] == "skipped" for row in rows))
    roles = sorted({row["evidence"].get("role", row["evidence"]["check"]) for row in rows})
    result["roles"] = {role: dict(occurrences=len(selected), mechanical=sum(row.get("origin") == "mechanical" for row in selected),
        semantic=sum(row.get("origin") != "mechanical" for row in selected),
        checked=sum(type(row.get("qualification", {}).get("passed")) is bool for row in selected),
        incorrect_cases=[row["id"] for row in selected if row.get("qualification", {}).get("passed") is False],
        unresolved=sum(row["evidence"]["expectation_status"] == "unresolved" for row in selected))
        for role in roles for selected in [[row for row in rows if row["evidence"].get("role", row["evidence"]["check"]) == role]]}
    return result


def _request_summary(experiments, skipped=frozenset()):
    """Count the runner's exact identities, including its verified reuse lookup."""
    from experiment_runner import experiment
    states = {check: dict(distinct=set(), remaining=set(), reusable=0, new=0, warmups_remaining=0)
              for check in _DEFINITIONS}
    for native in experiments:
        plan, _, manifest = experiment.load(Path(native["experiment"]))
        representatives = {}
        for row in native["cases"]:
            if row.get("origin") == "mechanical":
                continue
            check = row["evidence"]["check"]
            key = engine._prompt_request_key(manifest, row["prompt"])
            states[check]["distinct"].add(key)
            if (check, row["id"]) in skipped:
                continue
            if row["status"] == "unrun" and key not in states[check]["remaining"]:
                representatives.setdefault(key, row)
        for key, row in representatives.items():
            check = row["evidence"]["check"]
            states[check]["remaining"].add(key)
        check = native["cases"][0]["evidence"]["check"]
        pending = experiment.request_preview(plan, manifest, list(representatives.values()))
        for field in ("reusable", "new"):
            states[check][field] += pending[field]
        if pending["new"] and plan.get("cache_warmup", {}).get("eligible"):
            states[check]["warmups_remaining"] += 1
    return dict(checks={check: {key: len(value) if isinstance(value, set) else value
                               for key, value in state.items()} for check, state in states.items()},
        totals={**{field: len(set().union(*(state[field] for state in states.values())))
                   for field in ("distinct", "remaining")},
                **{field: sum(state[field] for state in states.values())
                   for field in ("reusable", "new", "warmups_remaining")}},
        basis="Distinct counts retain frozen semantic inputs; remaining counts exclude explicitly skipped occurrences. "
              "Native request identity and verified saved-answer lookup at inspection time; excludes retries. "
              "One warmup per eligible group with new work on the next run, when its allowance permits.")


def _skip_case(case, rule, depends_on):
    # Keep already paid-for decisions and their qualification evidence visible.
    if case["status"] != "unrun":
        return
    case.update(status="skipped", skip_evidence=dict(rule=rule, depends_on=depends_on),
                qualification=dict(passed=None, reason="No semantic verdict: the score is already determined."))


def _apply_stopping(answer, checks, context):
    """Omit score-irrelevant questions without inventing semantic verdicts."""
    support = {row["evidence"]["student_number"]: row for row in checks["support"]}
    for row in checks["relationship"]:
        if row["evidence"]["role"] != "actual_relationship":
            continue
        child = support[row["evidence"]["student_number"]]
        if child["status"] == "valid" and not child["parsed"]["valid"]:
            _skip_case(row, "unsupported_child", [child["id"]])
    if context is None or any(row["status"] != "valid" for row in checks["matching"]):
        return
    teacher = review._TeacherIndex(answer["teacher"])
    matching_rows = {row["evidence"]["student_number"]: row for row in checks["matching"]}
    by_group = {}
    for row in checks["relationship"]:
        if row["evidence"]["role"] == "compatibility":
            by_group.setdefault(tuple(row["evidence"]["teacher_numbers"]), []).append(row)
    for group in context:
        if not group["required"]:
            continue
        identifiers = {teacher.by_number[number] for number in group["teacher_numbers"]}
        matches = {number for number, row in matching_rows.items() if row["parsed"]["teacher_id"] in identifiers}
        rows = by_group.get(tuple(group["teacher_numbers"]), [])
        covered = review._matched_headings(matches)
        witness = next((row for row in rows if row["status"] == "valid" and row["parsed"]["valid"]
                        and row["evidence"]["heading_number"] not in covered), None)
        for row in rows:
            heading = row["evidence"]["heading_number"]
            # A positive DSM match must also receive a positive DSL self check.
            if heading in matches:
                continue
            if not matches:
                _skip_case(row, "no_full_match", [dict(check="matching", answer_id=answer["id"])])
            elif heading in covered:
                _skip_case(row, "match_beneath_heading", [dict(check="matching", answer_id=answer["id"])])
            elif witness is not None:
                _skip_case(row, "uncovered_compatible_heading", [witness["id"],
                    dict(check="matching", answer_id=answer["id"])])


def _relationship_wave(current, answer_ids=None):
    """Check independent edges and self guards, plus one witness per meaning."""
    wanted, pending = set(), []
    for cohort in ("random", "challenge"):
        for answer in current[cohort]["answers"]:
            if answer_ids is not None and answer["id"] not in answer_ids:
                continue
            groups = {}
            matching_rows = answer["checks"]["matching"]
            matching_by_number = {row["evidence"]["student_number"]: row for row in matching_rows}
            teacher = review._TeacherIndex(answer["teacher"])
            group_identifiers = {}
            for row in answer["checks"]["relationship"]:
                if row["status"] == "valid":
                    continue
                pending.append(row)
                if row["status"] == "skipped":
                    continue
                if row["evidence"]["role"] == "actual_relationship":
                    wanted.add(row["input_sha256"])
                    continue
                group = tuple(row["evidence"]["teacher_numbers"])
                if group not in group_identifiers:
                    group_identifiers[group] = {teacher.by_number[number] for number in group}
                identifiers = group_identifiers[group]
                heading = row["evidence"]["heading_number"]
                own_match = matching_by_number[heading]
                if own_match["status"] == "valid" and own_match["parsed"]["teacher_id"] in identifiers:
                    wanted.add(row["input_sha256"])
                else:
                    groups.setdefault(group, row)
            wanted.update(row["input_sha256"] for row in groups.values())
    # Dispatch all needed numbered aliases together; native reuse owns receipts.
    return {row["id"] for row in pending if row["input_sha256"] in wanted}


def _usage(experiments, sources):
    """Use the native receipt accounting once per original file/line."""
    from experiment_runner import experiment
    files = engine.ReceiptFiles()
    originals, reconciled = {}, {}
    local_roots = [Path(native["experiment"]) for native in experiments]
    for native in experiments:
        for source in native["generation_usage"]["sources"]:
            key = source["results_path"], source["result_line"]
            if key in originals:
                if originals[key][0]["result_sha256"] != source["result_sha256"]:
                    raise ValueError("review evaluation generation source changed")
                continue
            path = Path(key[0])
            raw = files.line(path, key[1])
            if hashlib.sha256(raw).hexdigest() != source["result_sha256"]:
                raise ValueError("review evaluation receipt changed while reporting")
            record = preview._decode(raw)
            if path.parent not in reconciled:
                records = [preview._decode(line) for line in files.lines(path)]
                reconciled[path.parent] = engine.load_reconciled_costs(path.parent, records)
                sources[str(path)] = engine._sha256_file(path)
            warmup = files.json(path.parent / "manifest.json").get("cache_warmup", False)
            originals[key] = source, record, engine.provider_cost(record, reconciled[path.parent]), warmup
    calls, warmups, local_calls, local_warmups = [], [], [], []
    for (filename, _), (_, record, charge, warmup) in originals.items():
        call = record, charge
        (warmups if warmup else calls).append(call)
        if any(Path(filename).is_relative_to(root) for root in local_roots):
            (local_warmups if warmup else local_calls).append(call)
    generation = dict(experiment.usage_summary(calls, warmup_calls=warmups),
        original_calls=len(originals), sources=[source for source, *_ in originals.values()],
        source_calls_added=sum(source.get("added_from_reuse", False) for source, *_ in originals.values()),
        failed_calls=sum(record["status"] == "failed" for _, record, _, _ in originals.values()))
    return experiment.usage_summary(local_calls, warmup_calls=local_warmups), generation


def _score(answer, checks, context, *, partial=False):
    teacher = review._TeacherIndex(answer["teacher"])
    matches = {row["evidence"]["student_number"]: row["parsed"]["teacher_id"] for row in checks["matching"]}
    compatibility = {}
    for row in checks["relationship"]:
        if row["evidence"]["role"] == "compatibility":
            compatibility.setdefault(tuple(row["evidence"]["teacher_numbers"]), {})[
                row["evidence"]["heading_number"]] = row["parsed"]["valid"] if row["status"] == "valid" else None
    coverage = []
    for group in context:
        teacher_ids = {teacher.by_number[number] for number in group["teacher_numbers"]}
        headings = [number for number, valid in compatibility.get(tuple(group["teacher_numbers"]), {}).items() if valid is True]
        coverage.append(dict(group, student_numbers=[number for number, identifier in matches.items() if identifier in teacher_ids],
            compatible_heading_numbers=headings, reason="Complete DSM matches and unchanged DSL compatibility judgments."))
    if partial:
        return review.score_partial(dict(post=answer["post"], teacher=answer["teacher"], student=answer["student"],
            exact_matches=review.exact_matches(answer["teacher"], answer["student"]), teacher_meanings=context),
            subjects={row["evidence"]["student_number"]: row["parsed"]["valid"]
                      for row in checks["support"] if row["status"] == "valid"},
            relationships={row["evidence"]["student_number"]: row["parsed"]["valid"] if row["status"] == "valid" else None
                for row in checks["relationship"] if row["evidence"]["role"] == "actual_relationship"},
            coverage=[dict(teacher_numbers=group["teacher_numbers"], required=group["required"],
                student_numbers=group["student_numbers"],
                compatibility=compatibility.get(tuple(group["teacher_numbers"]), {})) for group in coverage])
    assembled = dict(schema_version=1, prompt_id="DSRv2",
        subjects=[dict(number=row["evidence"]["student_number"], **row["parsed"]) for row in checks["support"]],
        relationships=[dict(parent=row["evidence"]["parent_number"], child=row["evidence"]["student_number"], **row["parsed"])
            for row in checks["relationship"] if row["evidence"]["role"] == "actual_relationship"], coverage=coverage)
    payload = dict(post=answer["post"], teacher=answer["teacher"], student=answer["student"],
        exact_matches=review.exact_matches(answer["teacher"], answer["student"]), teacher_meanings=context)
    case = dict(prompt="DSRv2", inputs=dict(REVIEW_INPUT=json.dumps(payload, ensure_ascii=False)))
    return review.validate(case, json.dumps(assembled, ensure_ascii=False))


def run(output, max_new_attempts=None, *, attempt_budget_path=None, runner_upgrade_reason=None,
        answer_ids=None):
    """Execute and publish the final/partial native assembly without a full copy."""
    result, failure = None, None
    try:
        result = _run(output, max_new_attempts, attempt_budget_path=attempt_budget_path,
            runner_upgrade_reason=runner_upgrade_reason, answer_ids=answer_ids)
        return result
    except BaseException as error:
        failure = error
        raise
    finally:
        try:
            from .evaluation_publication import export_review_evaluation
            if result is None:
                result = report(output)
            export_review_evaluation(Path(output).resolve() / 'evaluation.json',
                Path(output).resolve() / 'publication', result=result,
                execution_status='complete' if failure is None else
                    'stopped' if isinstance(failure, (KeyboardInterrupt, SystemExit)) else 'failed')
        except Exception:
            if failure is None:
                raise


def _run(output, max_new_attempts=None, *, attempt_budget_path=None, runner_upgrade_reason=None,
         answer_ids=None):
    """Execute selected answers under one allowance; retain the full report."""
    from experiment_runner import experiment
    if max_new_attempts is not None and (type(max_new_attempts) is not int or max_new_attempts < 0):
        raise ValueError("max_new_attempts must be nonnegative")
    initial = report(output)
    if answer_ids is not None:
        if not isinstance(answer_ids, list) or any(not isinstance(identifier, str) or not identifier.strip()
                                                  for identifier in answer_ids):
            raise ValueError("answer_ids must be an array of nonempty strings")
        known = {answer["id"] for cohort in ("random", "challenge") for answer in initial[cohort]["answers"]}
        if len(answer_ids) != len(set(answer_ids)) or set(answer_ids) - known:
            raise ValueError("unknown or duplicate answer_ids")
        answer_ids = set(answer_ids)
        if not answer_ids:
            return initial
    frozen = experiment.read(Path(output).resolve() / "evaluation.json")
    remaining = max_new_attempts
    def dispatch(entry, *, only=None, warm_cache=True, allowance=None):
        nonlocal remaining
        directory = Path(entry["experiment"])
        before = entry["summary"]["attempts"]
        selection = ({} if frozen["schema_version"] == 1 and answer_ids is None
                     else dict(only=only, warm_cache=warm_cache))
        try:
            after = experiment.run(directory, remaining if allowance is None else allowance, runner_upgrade_reason,
                attempt_budget_path=Path(attempt_budget_path) if attempt_budget_path is not None else None,
                include_request_preview=False, **selection)
        except engine.RunnerError as error:
            message = str(error.__cause__ or error)
            prefix = "unresolved prompt cases: "
            if not message.startswith(prefix) or set(message[len(prefix):].split(", ")) != {"new-attempt allowance exhausted"}:
                raise
            after = experiment.report(directory, include_request_preview=False)
        if remaining is not None:
            remaining -= after["summary"]["attempts"] - before
        return after
    for entry in initial["experiments"]:
        if frozen["schema_version"] == 1 or entry["cases"][0]["evidence"]["check"] != "relationship":
            only = None if answer_ids is None else [row["id"] for row in entry["cases"]
                if row["evidence"]["answer_id"] in answer_ids]
            if only is None or only:
                dispatch(entry, only=only)
    current = report(output)
    if frozen["schema_version"] == 1:
        return current
    if any(row["status"] != "valid" for cohort in ("random", "challenge")
           for answer in current[cohort]["answers"] if answer_ids is None or answer["id"] in answer_ids
           for check in ("matching", "support")
           for row in answer["checks"][check]):
        return current
    # A cached positive witness may occur after a fresh question in case order.
    # Join only verified saved inputs first; zero allowance cannot hide later
    # cached answers behind a new-request scheduling stop.
    joined = False
    for entry in current["experiments"]:
        if entry["cases"][0]["evidence"]["check"] != "relationship":
            continue
        plan, _, manifest = experiment.load(Path(entry["experiment"]))
        candidates = [row for row in entry["cases"]
                      if answer_ids is None or row["evidence"]["answer_id"] in answer_ids]
        reusable = experiment.request_preview(plan, manifest, candidates,
            include_reusable_case_ids=True)["reusable_case_ids"]
        if reusable:
            dispatch(entry, only=reusable, warm_cache=False, allowance=0)
            joined = True
    if joined:
        current = report(output)
    if max_new_attempts == 0:
        return current
    warmed = set()
    while True:
        selected = _relationship_wave(current, answer_ids)
        if not selected:
            return current
        before = {(row["id"], row["status"], row.get("attempts", 0))
            for cohort in ("random", "challenge") for answer in current[cohort]["answers"]
            for row in answer["checks"]["relationship"]}
        for entry in current["experiments"]:
            if entry["cases"][0]["evidence"]["check"] != "relationship":
                continue
            only = [row["id"] for row in entry["cases"] if row["id"] in selected]
            if only:
                dispatch(entry, only=only, warm_cache=entry["experiment"] not in warmed)
                warmed.add(entry["experiment"])
        current = report(output)
        after = {(row["id"], row["status"], row.get("attempts", 0))
            for cohort in ("random", "challenge") for answer in current[cohort]["answers"]
            for row in answer["checks"]["relationship"]}
        if before == after:
            return current
