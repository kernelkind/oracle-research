"""Source-bound focused coverage searches; saved premise checks remain separate.

This experimental adapter changes the question shape, not coverage criteria.
It does not score an unverified positive witness as a missing placement.
"""
import hashlib
import json
from pathlib import Path

from . import distillation_review as review
from . import distillation_review_evaluation as evaluation
from . import extraction_pipeline as engine


def _snapshot(reference, base):
    """Load only an independently verified frozen native evaluation."""
    from experiment_runner import experiment
    review._fields(reference, {"path", "sha256"}, "coverage evaluation reference")
    path = engine._resolve_path(reference["path"], "coverage evaluation reference", Path(base))
    if path.name != "evaluation.json" or engine._sha256_file(path) != reference["sha256"]:
        raise ValueError("coverage evaluation hash differs")
    report = evaluation.report(path.parent)
    protected = dict(report["sources"])
    for item in (path, path.parent / "evaluation.complete.json"):
        protected[str(item)] = engine._sha256_file(item)
    for native in report["experiments"]:
        directory = Path(native["experiment"])
        plan, _, _ = experiment.load(directory)
        protected.update(plan["sources"])
        for filename, checksum in plan["files"].items():
            protected[str(directory / filename)] = checksum
        protected[str(directory / "experiment.json")] = engine._sha256_file(directory / "experiment.json")
        ledger = directory / "reviews.jsonl"
        if ledger.exists():
            protected[str(ledger)] = engine._sha256_file(ledger)
        for row in native["cases"]:
            receipt = row.get("receipt")
            if receipt:
                results = Path(receipt["results_path"])
                for item in (results, results.parent / "manifest.json"):
                    protected[str(item)] = engine._sha256_file(item)
    frozen = experiment.read(path)
    bundle, _ = evaluation._selection(frozen["selection"], path.parent)
    assessments = evaluation._assessments(frozen["assessment_directory"], bundle)
    return report, assessments, protected


def _cases(report, assessments):
    cases, settlements, guards = [], [], []
    for cohort in ("random", "challenge"):
        for answer in report[cohort]["answers"]:
            if answer["errors"]:
                settlements.append(dict(answer_id=answer["id"], rule="invalid_output"))
                continue
            groups = assessments["contexts"].get(answer["id"])
            if groups is None:
                raise ValueError("coverage search requires frozen teacher meanings")
            matching = answer["checks"]["matching"]
            if any(row["status"] != "valid" for row in matching):
                raise ValueError("coverage search requires complete matching checks")
            teacher = review._TeacherIndex(answer["teacher"])
            students = {row["number"]: row["subject"] for row in answer["student"]}
            actual = {row["evidence"]["student_number"]: row
                for row in answer["checks"]["relationship"]
                if row["evidence"]["role"] == "actual_relationship"}
            for ordinal, group in enumerate(groups, 1):
                if not group["required"]:
                    continue
                identity = dict(answer_id=answer["id"], teacher_numbers=group["teacher_numbers"])
                teacher_ids = {teacher.by_number[number] for number in group["teacher_numbers"]}
                matches = [row["evidence"]["student_number"] for row in matching
                           if row["parsed"]["teacher_id"] in teacher_ids]
                guard_rows = [row for row in answer["checks"]["relationship"]
                    if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]
                    and row["evidence"]["heading_number"] in matches]
                if {row["evidence"]["heading_number"] for row in guard_rows} != set(matches):
                    raise ValueError("coverage search omitted matching self guards")
                guards.extend(dict(identity, student_number=row["evidence"]["heading_number"],
                    case_id=row["id"], status=row["status"],
                    valid=row["parsed"]["valid"] if row["status"] == "valid" else None)
                    for row in guard_rows)
                if any(row["status"] == "valid" and row["parsed"]["valid"] is False for row in guard_rows):
                    settlements.append(dict(identity, rule="inconsistent_matching_self_guard", covered=None))
                    continue
                if not matches:
                    settlements.append(dict(identity, rule="no_full_match", covered=False))
                    continue
                covered = review._matched_headings(matches)
                uncovered = [number for number in students if number not in covered]
                representative = group["teacher_numbers"][0]
                child = teacher.subjects[representative]
                mechanical = None
                for number in uncovered:
                    proof = teacher.relationship(students[number], child)
                    if proof is not None:
                        mechanical = number, proof
                        break
                if mechanical is not None:
                    number, proof = mechanical
                    settlements.append(dict(identity, rule="trusted_uncovered_compatible_heading", covered=False,
                        witness_student_number=number, mechanical_evidence=proof["evidence"]))
                    continue
                roots, omitted = [], []
                for number in uncovered:
                    parent = number.rpartition(".")[0]
                    edge = actual.get(number)
                    if (parent in uncovered and edge is not None and edge["status"] == "valid"
                            and edge["parsed"]["valid"] is True
                            and not any(row.get("verdict") in {"reject", "uncertain"} for row in edge.get("reviews", []))):
                        omitted.append(dict(student_number=number, parent_number=parent, edge_case_id=edge["id"],
                            rule="valid_actual_edge_retains_ancestor_candidate",
                            semantic_status="Conditional on the accepted actual-edge verdict and fixed interpretations."))
                    else:
                        roots.append(number)
                if not roots:
                    settlements.append(dict(identity, rule="no_uncovered_heading", covered=True))
                    continue
                candidates = [dict(student_number=number, student_subject=students[number],
                    teacher_contexts=[{key: row[key] for key in ("subject", "context")}
                        for row in teacher.interpretation_entries(students[number], child,
                                                                child_number=representative)])
                    for number in roots]
                distinct, aliases = {}, {}
                for candidate in candidates:
                    key = json.dumps({field: candidate[field] for field in ("student_subject", "teacher_contexts")},
                                     ensure_ascii=False, sort_keys=True)
                    representative_candidate = distinct.setdefault(key, candidate)
                    aliases.setdefault(representative_candidate["student_number"], []).append(candidate["student_number"])
                candidates = list(distinct.values())
                baseline_pairs = {row["evidence"]["heading_number"]: row
                    for row in answer["checks"]["relationship"]
                    if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]}
                evidence = dict(identity, check="coverage_search", cohort=cohort, note_id=answer["note_id"],
                    generation=answer["generation"], teacher_representative_number=representative,
                    matched_student_numbers=matches, covered_heading_numbers=sorted(covered),
                    original_uncovered_heading_numbers=uncovered,
                    candidate_student_numbers=[row["student_number"] for row in candidates], omitted_descendants=omitted,
                    candidate_aliases=[dict(representative_student_number=number, student_numbers=numbers)
                        for number, numbers in aliases.items() if len(numbers) > 1],
                    matching_case_ids=[row["id"] for row in matching],
                    self_guard_case_ids=[row["id"] for row in guard_rows],
                    baseline_compatibility=[dict(student_number=number, status=baseline_pairs[number]["status"],
                        valid=baseline_pairs[number]["parsed"]["valid"] if baseline_pairs[number]["status"] == "valid" else None)
                        for number in uncovered],
                    expectation_status="unresolved")
                cases.append(dict(id=answer["id"] + f":coverage-search:{ordinal:03}",
                    inputs=dict(POST=answer["post"], COVERAGE_INPUT=json.dumps(
                        dict(teacher_subject=child, candidates=candidates), ensure_ascii=False)), evidence=evidence))
    return cases, settlements, guards


def prepare_source(source, base, selected=None):
    review._fields(source, {"schema_version", "evaluation", "answer_ids"}, "coverage search source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("coverage search source schema_version must be 1")
    report, assessments, protected = _snapshot(source["evaluation"], base)
    report = evaluation._answer_subset(report, source["answer_ids"])
    cases, settlements, guards = _cases(report, assessments)
    if selected is not None:
        engine._validate_string_array(selected, "coverage search selection", allow_empty=False)
        known = {row["id"] for row in cases}
        if len(selected) != len(set(selected)) or set(selected) - known:
            raise ValueError("unknown or duplicate coverage search selection")
        cases = [row for row in cases if row["id"] in selected]
    return cases, protected, dict(settlements=settlements, matching_self_guards=guards,
        qualification_case_ids=[row["id"] for row in cases], semantic_status="Experimental, unqualified searches.")


def validate(case, raw):
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    review._fields(value, {"evidence", "witness_student_number"}, "coverage search verdict")
    candidates = json.loads(case["inputs"]["COVERAGE_INPUT"])["candidates"]
    numbers = {row["student_number"] for row in candidates}
    witness = value["witness_student_number"]
    if witness is not None and (not isinstance(witness, str) or witness not in numbers):
        raise ValueError("coverage witness must identify a supplied candidate")
    if not isinstance(value["evidence"], list):
        raise ValueError("coverage evidence must be an array")
    seen = []
    for row in value["evidence"]:
        review._fields(row, {"student_number", "reason"}, "coverage evidence row")
        if not isinstance(row["student_number"], str) or row["student_number"] not in numbers:
            raise ValueError("coverage evidence must identify a supplied candidate")
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            raise ValueError("coverage evidence requires a nonempty reason")
        seen.append(row["student_number"])
    if witness is None:
        if len(seen) != len(numbers) or set(seen) != numbers:
            raise ValueError("null coverage verdict must address every candidate exactly once")
    elif seen != [witness]:
        raise ValueError("positive coverage evidence must contain only its witness")
    baseline = {row["student_number"]: row["valid"]
                for row in case["evidence"].get("baseline_compatibility", [])}
    candidate_agreement = (baseline.get(witness) if witness is not None
        else False if any(baseline.get(number) is True for number in numbers)
        else True if all(baseline.get(number) is False for number in numbers) else None)
    original = case["evidence"].get("original_uncovered_heading_numbers", list(numbers))
    baseline_missing = (True if any(baseline.get(number) is True for number in original)
        else False if all(baseline.get(number) is False for number in original) else None)
    coverage_agreement = None if baseline_missing is None else (witness is not None) == baseline_missing
    return dict(status="valid", output=raw, parsed=value,
        qualification=dict(passed=None, candidate_baseline_agreement=candidate_agreement,
            coverage_baseline_agreement=coverage_agreement,
            semantic_status="Unqualified; baseline agreement is diagnostic, not correctness.",
            witness_requires_verification=witness is not None))


def prepare(evaluation_path, output, *, answer_ids=None, runner_binary=None, history_root=None):
    """Prepare native xhigh search experiments; never performs inference."""
    from experiment_runner import experiment, inputs, project, prompt_cache
    project.configure(Path(__file__).resolve().parents[1])
    path = Path(evaluation_path).expanduser().resolve()
    path = path / "evaluation.json" if path.is_dir() else path
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("coverage search output already exists")
    reference = dict(path=str(path), sha256=engine._sha256_file(path))
    if answer_ids is None:
        baseline = evaluation.report(path.parent)
        answer_ids = [answer["id"] for cohort in ("random", "challenge") for answer in baseline[cohort]["answers"]]
    source = dict(schema_version=1, evaluation=reference, answer_ids=answer_ids)
    cases, protected, preparation = prepare_source(source, path.parent)
    directory = Path(__file__).parent / "distillation-review-v1"
    template = (directory / "coverage-search-prompt-v1.md").read_text()
    by_prefix = {}
    for case in cases:
        prefix, _ = inputs.template_prefix(template, case["inputs"])
        by_prefix.setdefault(prefix, []).append(case)
    groups, ordinary = [], []
    for prefix, rows in by_prefix.items():
        if len({inputs.digest(row["inputs"]) for row in rows}) > 1 and prompt_cache.prefix_policy(prefix)["eligible"]:
            groups.append(("coverage-prefix-" + hashlib.sha256(prefix.encode()).hexdigest()[:12], rows, True))
        else:
            ordinary.extend(rows)
    if ordinary:
        groups.append(("coverage-ordinary", ordinary, False))
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    experiments = []
    for name, rows, cached in groups:
        source_path = output / "sources" / (name + ".json")
        experiment.write(source_path, source)
        runner = dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol", reasoning_effort="xhigh",
            transport="sse", timeout_seconds=3600,
            output_schema_path=str(directory / "coverage-search-response-schema.json"))
        if runner_binary is not None:
            runner["runner_binary"] = str(Path(runner_binary).expanduser().resolve())
        spec = output / "specs" / (name + ".json")
        experiment.write(spec, dict(schema_version=1,
            prompt=dict(id="DCSv1", path=str(directory / "coverage-search-prompt-v1.md")),
            dataset=dict(adapter="distillation_coverage_search", path=str(source_path), select=[row["id"] for row in rows]),
            runner=runner))
        destination = output / "experiments" / name
        arguments = ["prepare", str(destination), "--spec", str(spec), "--history-root",
            str(Path(history_root).resolve() if history_root is not None else output)]
        if cached:
            arguments.append("--prompt-cache")
        experiment.prepare(experiment.parser().parse_args(arguments), include_request_preview=False)
        experiments.append(dict(path=str(destination), sha256=engine._sha256_file(destination / "experiment.json"),
                                occurrences=len(rows), prefix_cached=cached))
    for filename, checksum in protected.items():
        if engine._sha256_file(Path(filename)) != checksum:
            raise ValueError("coverage premise changed while preparing: " + filename)
    frozen = dict(schema_version=1, evaluation=reference, answer_ids=answer_ids, sources=protected,
        experiments=experiments, inference_calls=0, preparation=preparation,
        semantic_status="Experimental. Positive witnesses require separate unchanged DSL verification.")
    experiment.write(output / "coverage-search.json", frozen)
    experiment.write(output / "coverage-search.complete.json", {
        "coverage-search.json": engine._sha256_file(output / "coverage-search.json")})
    return dict(frozen, output=str(output), search_cases=len(cases))
