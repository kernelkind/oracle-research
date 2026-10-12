"""Source-bound focused coverage searches; saved premise checks remain separate.

This experimental adapter changes the question shape, not coverage criteria.
It does not score an unverified DCS-returned witness as a missing placement.
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
    receipt_hashes = {}
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
                    if item not in receipt_hashes:
                        receipt_hashes[item] = engine._sha256_file(item)
                    protected[str(item)] = receipt_hashes[item]
    frozen = experiment.read(path)
    bundle, _ = evaluation._selection(frozen["selection"], path.parent)
    assessments = evaluation._assessments(frozen["assessment_directory"], bundle)
    return report, assessments, protected


def _premise_audits(references, base, protected):
    """Bind existing complete-output assessments, never invent an acceptance."""
    audits = {}
    if not isinstance(references, list):
        raise ValueError("coverage premise audits must be an array")
    for reference in references:
        review._fields(reference, {"path", "sha256"}, "coverage premise audit reference")
        path = engine._resolve_path(reference["path"], "coverage premise audit", Path(base))
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise ValueError("coverage premise audit hash differs")
        protected[str(path)] = reference["sha256"]
        for line_number, line in enumerate(raw.splitlines(), 1):
            row = json.loads(line, object_pairs_hook=engine._position_decoder().unique_object)
            if isinstance(row, dict) and row.get("record_type") == "skip" and "verdict" not in row:
                continue
            if (not isinstance(row, dict) or row.get("check") not in {"matching", "support", "relationship", "coverage_search"}
                    or row.get("verdict") not in {"accept", "reject", "uncertain"}
                    or not isinstance(row.get("reason"), str) or not row["reason"].strip()):
                raise ValueError("coverage premise audit requires a complete-output assessment")
            for field in ("input_sha256", "output_sha256"):
                checksum = row.get(field)
                if (not isinstance(checksum, str) or len(checksum) != 64
                        or any(char not in "0123456789abcdef" for char in checksum)):
                    raise ValueError("coverage premise audit requires exact input/output hashes")
            verdict = row["verdict"]
            if row.get("decision_error") or row.get("explanation_error"):
                verdict = "reject"
            key = row["check"], row["input_sha256"], row["output_sha256"]
            audits.setdefault(key, []).append(dict(path=str(path), sha256=reference["sha256"],
                line=line_number, verdict=verdict, reason=row["reason"]))
    return audits


def _bound_premise_audits(row, audits):
    """Return external assessments bound to this exact input and output."""
    output_hash = hashlib.sha256(row["output"].encode()).hexdigest()
    bound = audits.get((row["evidence"]["check"], row["input_sha256"], output_hash), [])
    return output_hash, bound


def _accepted_premise(row, audits):
    if row["status"] != "valid":
        return None
    output_hash, bound = _bound_premise_audits(row, audits)
    reviews = [item for item in row.get("reviews", []) if item.get("current") is True]
    if any(item.get("verdict") in {"reject", "uncertain"} for item in reviews + bound):
        return None
    if row.get("origin") != "mechanical" and not any(item.get("verdict") == "accept" for item in reviews + bound):
        return None
    premise = dict(case_id=row["id"], input_sha256=row["input_sha256"], output_sha256=output_hash,
        origin=row.get("origin"), receipt=row.get("receipt"), reviews=reviews, audits=bound)
    if row.get("origin") == "mechanical":
        premise.update(mechanical_evidence=row["mechanical_evidence"], mechanical_sha256=row["mechanical_sha256"])
    return premise


def _accepted_matching(teacher, matching, relationships, audits):
    """Index accepted matches and their available self guards once per answer."""
    by_number = {row["evidence"]["student_number"]: row for row in matching}
    guards, identifiers = {}, {}
    for row in relationships:
        if row["evidence"]["role"] != "compatibility":
            continue
        number = row["evidence"]["heading_number"]
        group = tuple(row["evidence"]["teacher_numbers"])
        if group not in identifiers:
            identifiers[group] = {teacher.by_number[item] for item in group}
        if by_number[number]["parsed"]["teacher_id"] in identifiers[group]:
            guards.setdefault(number, []).append(row)
    accepted = {}
    for number, row in by_number.items():
        identifier = row["parsed"]["teacher_id"]
        if identifier is None:
            continue
        premise = _accepted_premise(row, audits)
        own_guards = guards.get(number, [])
        guard_premises = [_accepted_premise(guard, audits) for guard in own_guards]
        if (premise is not None
                and all(guard["status"] == "valid" and guard["parsed"]["valid"] is True for guard in own_guards)
                and all(guard is not None for guard in guard_premises)):
            accepted[number] = dict(teacher_id=identifier, premise=premise, self_guards=guard_premises)
    return accepted


def _matching_path_settlement(identity, teacher, group, matching, accepted, uncovered, guards, audits):
    """Substitute an accepted equivalent parent into an actual trusted path."""
    target_guards = [_accepted_premise(row, audits) for row in guards]
    if any(row["status"] != "valid" or row["parsed"]["valid"] is not True for row in guards) \
            or any(premise is None for premise in target_guards):
        return None
    candidates = {}
    order = {number: index for index, number in enumerate(uncovered)}
    for number in uncovered:
        if number in accepted:
            candidates.setdefault(accepted[number]["teacher_id"], number)
    witness = None
    for child_number in group["teacher_numbers"]:
        path = [child_number]
        ancestor = child_number.rpartition(".")[0]
        while ancestor:
            path.append(ancestor)
            number = candidates.get(teacher.by_number[ancestor])
            if number is not None and (witness is None or order[number] < order[witness[0]]):
                witness = number, list(reversed(path))
            ancestor = ancestor.rpartition(".")[0]
    if witness is None:
        return None
    number, path = witness
    premise = accepted[number]
    return dict(identity, rule="accepted_matching_trusted_teacher_path", covered=False,
        witness_student_number=number, matching_premise=premise["premise"],
        matched_teacher_id=premise["teacher_id"], matching_case_ids=[row["id"] for row in matching],
        matching_self_guard_premises=target_guards + premise["self_guards"],
        teacher_path=[dict(number=item, subject=teacher.subjects[item], context=teacher.contexts[item]) for item in path],
        semantic_status="Conditional on the accepted ancestor match, saved coverage matches and fixed interpretations of the trusted teacher path; separate matching uncertainties remain unresolved.")


def _cases(report, assessments, audits=None):
    audits = {} if audits is None else audits
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
            disputed_actual = {number for number, row in actual.items()
                if row["status"] == "valid" and row["parsed"]["valid"] is True
                and any(item.get("verdict") in {"reject", "uncertain"}
                    for item in row.get("reviews", []) + _bound_premise_audits(row, audits)[1])}
            accepted_matching = _accepted_matching(teacher, matching, answer["checks"]["relationship"], audits)
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
                accepted_pair = next((row for row in answer["checks"]["relationship"]
                    if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]
                    and row["evidence"]["heading_number"] in uncovered
                    and row["status"] == "valid" and row["parsed"]["valid"] is True
                    and _accepted_premise(row, audits) is not None), None)
                if accepted_pair is not None:
                    settlements.append(dict(identity, rule="accepted_uncovered_compatible_heading", covered=False,
                        witness_student_number=accepted_pair["evidence"]["heading_number"],
                        compatibility_premise=_accepted_premise(accepted_pair, audits)))
                    continue
                derived = _matching_path_settlement(identity, teacher, group, matching,
                    accepted_matching, uncovered, guard_rows, audits)
                if derived is not None:
                    settlements.append(derived)
                    continue
                roots, omitted = [], []
                for number in uncovered:
                    parent = number.rpartition(".")[0]
                    edge = actual.get(number)
                    if (parent in uncovered and edge is not None and edge["status"] == "valid"
                            and edge["parsed"]["valid"] is True
                            and number not in disputed_actual):
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
    fields = {"schema_version", "evaluation", "answer_ids"}
    review._fields(source, fields | ({"premise_audits"} if "premise_audits" in source else set()), "coverage search source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("coverage search source schema_version must be 1")
    report, assessments, protected = _snapshot(source["evaluation"], base)
    report = evaluation._answer_subset(report, source["answer_ids"])
    audits = _premise_audits(source.get("premise_audits", []), base, protected)
    cases, settlements, guards = _cases(report, assessments, audits)
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


def prepare(evaluation_path, output, *, answer_ids=None, runner_binary=None, history_root=None, premise_audits=None,
            reasoning_effort="xhigh"):
    """Prepare native search experiments; never performs inference."""
    from experiment_runner import experiment, inputs, project, prompt_cache
    project.configure(Path(__file__).resolve().parents[1])
    if reasoning_effort not in ("xhigh", "high", "medium", "low"):
        raise ValueError("reasoning_effort must be xhigh, high, medium or low")
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
    if premise_audits is not None:
        source["premise_audits"] = [dict(path=str(Path(audit).expanduser().resolve()),
            sha256=engine._sha256_file(Path(audit).expanduser().resolve())) for audit in premise_audits]
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
        runner = dict(provider="openai-codex", auth_file=None, model="gpt-6.1-sol", reasoning_effort=reasoning_effort,
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
        premise_audits=source.get("premise_audits", []),
        experiments=experiments, inference_calls=0, preparation=preparation,
        semantic_status="Experimental. DCS-returned positive witnesses require separate unchanged DSL verification; conditional teacher-path settlements retain their accepted premises.")
    experiment.write(output / "coverage-search.json", frozen)
    experiment.write(output / "coverage-search.complete.json", {
        "coverage-search.json": engine._sha256_file(output / "coverage-search.json")})
    return dict(frozen, output=str(output), search_cases=len(cases))


def collect(coverage_directory, output, *, verification_experiments=None, premise_audits=None):
    """Score accepted native checks and searches without running the old matrix."""
    from experiment_runner import experiment, project
    project.configure(Path(__file__).resolve().parents[1])
    directory = Path(coverage_directory).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("coverage collection output already exists")
    frozen_path = directory / "coverage-search.json"
    if experiment.read(directory / "coverage-search.complete.json") != {
            "coverage-search.json": engine._sha256_file(frozen_path)}:
        raise ValueError("coverage search preparation changed")
    frozen = experiment.read(frozen_path)
    protected = dict(frozen["sources"])
    for path, checksum in protected.items():
        if engine._sha256_file(Path(path)) != checksum:
            raise ValueError("coverage collection source changed: " + path)

    def protect(sources):
        for path, checksum in sources.items():
            if path in protected and protected[path] != checksum:
                raise ValueError("coverage collection source changed: " + path)
            protected[path] = checksum

    protected[str(frozen_path)] = engine._sha256_file(frozen_path)
    baseline, assessments, snapshot_sources = _snapshot(frozen["evaluation"], directory)
    protect(snapshot_sources)
    baseline = evaluation._answer_subset(baseline, frozen["answer_ids"])
    audit_references = [dict(path=str(Path(path).expanduser().resolve()),
        sha256=engine._sha256_file(Path(path).expanduser().resolve())) for path in premise_audits or []]
    # Preparation audits remain part of the immutable native source definition.
    preparation_references = list(frozen.get("premise_audits", []))
    searches, verifiers = {}, {}

    def native(path):
        path = Path(path).expanduser().resolve()
        plan, _, _ = experiment.load(path)
        protect(plan["sources"])
        protected[str(path / "experiment.json")] = engine._sha256_file(path / "experiment.json")
        result = experiment.report(path, include_request_preview=False)
        for name in ("reviews.jsonl", "run/results.jsonl", "run/manifest.json"):
            source = path / name
            if source.exists():
                protected[str(source)] = engine._sha256_file(source)
        return plan, result

    for entry in frozen["experiments"]:
        path = Path(entry["path"])
        if engine._sha256_file(path / "experiment.json") != entry["sha256"]:
            raise ValueError("coverage native preparation changed")
        plan, result = native(path)
        definition = experiment.read(Path(plan["dataset"]["path"]))
        preparation_references.extend(definition.get("premise_audits", []))
        for row in result["cases"]:
            key = row["evidence"]["answer_id"], tuple(row["evidence"]["teacher_numbers"])
            if key in searches:
                raise ValueError("duplicate coverage search teacher group")
            searches[key] = row
    audits = _premise_audits(preparation_references + audit_references, directory, protected)
    for path in verification_experiments or []:
        _, result = native(path)
        for row in result["cases"]:
            if row["evidence"].get("check") != "relationship":
                raise ValueError("coverage verification requires native relationship checks")
            verifiers.setdefault((row["input_sha256"], row["prompt"]), []).append(row)
    settlements = {(row["answer_id"], tuple(row["teacher_numbers"])): row
        for row in frozen["preparation"]["settlements"] if "teacher_numbers" in row}
    cohorts = {}
    for cohort in ("random", "challenge"):
        answers = []
        for answer in baseline[cohort]["answers"]:
            if answer["errors"]:
                answers.append(dict(id=answer["id"], note_id=answer["note_id"],
                    scoring=dict(status="valid", scores=answer["scores"]), dependencies=[]))
                continue
            checks = answer["checks"]
            dependencies, premises = [], []
            source_rows = {(row["id"], row["input_sha256"], hashlib.sha256(row["output"].encode()).hexdigest()): row
                for rows in checks.values() for row in rows if row["status"] == "valid"}

            def settlement_accepted(settlement):
                stored = [settlement[field] for field in ("matching_premise", "compatibility_premise")
                          if field in settlement]
                stored.extend(settlement.get("matching_self_guard_premises", []))
                for premise in stored:
                    key = premise["case_id"], premise["input_sha256"], premise["output_sha256"]
                    row = source_rows.get(key)
                    if row is None or _accepted_premise(row, audits) is None:
                        dependencies.append(dict(check="relationship", case_id=premise["case_id"],
                            reason="Previously accepted settlement premise is now absent or disputed."))
                        return False
                return True

            def accepted(row):
                premise = _accepted_premise(row, audits)
                if premise is not None:
                    premises.append(premise)
                    return True
                dependencies.append(dict(check=row["evidence"]["check"], case_id=row["id"],
                    status=row["status"], reason="No accepted complete input/output-bound assessment.",
                    reviews=row.get("reviews", [])))
                return False

            subjects = {row["evidence"]["student_number"]: row["parsed"]["valid"]
                for row in checks["support"] if row["status"] == "valid" and accepted(row)}
            actual = {row["evidence"]["student_number"]: row for row in checks["relationship"]
                if row["evidence"]["role"] == "actual_relationship"}
            relationships = {number: row["parsed"]["valid"] if row["status"] == "valid" and accepted(row)
                else None for number, row in actual.items()}
            matching_pending = [row["id"] for row in checks["matching"] if not accepted(row)]
            teacher = review._TeacherIndex(answer["teacher"])
            matching = {row["evidence"]["student_number"]: row["parsed"]["teacher_id"]
                for row in checks["matching"] if row["status"] == "valid"}
            coverage = []
            for group in assessments["contexts"][answer["id"]]:
                key = answer["id"], tuple(group["teacher_numbers"])
                identifiers = {teacher.by_number[number] for number in group["teacher_numbers"]}
                matches = [number for number, identifier in matching.items() if identifier in identifiers]
                known = {}
                pairs = [row for row in checks["relationship"] if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]]
                if group["required"]:
                    for pair in pairs:
                        number = pair["evidence"]["heading_number"]
                        candidates = verifiers.get((pair["input_sha256"], pair["prompt"]), [])
                        if number in matches:
                            candidates = [pair] + candidates
                        accepted_pairs = [row for row in candidates if _accepted_premise(row, audits) is not None]
                        verdicts = {row["parsed"]["valid"] for row in accepted_pairs}
                        if len(verdicts) == 1:
                            known[number] = verdicts.pop()
                            premises.extend(_accepted_premise(row, audits) for row in accepted_pairs)
                        elif candidates:
                            dependencies.append(dict(check="relationship", case_id=pair["id"],
                                reason="Exact verification is disputed, unaudited or contradictory."))
                    settlement = settlements.get(key)
                    if (settlement is not None and settlement.get("covered") is False
                            and settlement.get("witness_student_number") and settlement_accepted(settlement)):
                        known[settlement["witness_student_number"]] = True
                    search = searches.get(key)
                    if search is not None and accepted(search):
                        witness = search["parsed"]["witness_student_number"]
                        if witness is None:
                            for number in search["evidence"]["candidate_student_numbers"]:
                                known[number] = False
                            for alias in search["evidence"]["candidate_aliases"]:
                                known.update({number: False for number in alias["student_numbers"]})
                            for omitted in search["evidence"]["omitted_descendants"]:
                                number, parent = omitted["student_number"], omitted["parent_number"]
                                if known.get(parent) is False and relationships.get(number) is True:
                                    known[number] = False
                        elif known.get(witness) is not True:
                            dependencies.append(dict(check="coverage_search", case_id=search["id"],
                                reason="Positive search lacks an accepted exact positive DSL witness."))
                coverage.append(dict(teacher_numbers=group["teacher_numbers"], required=group["required"],
                    student_numbers=matches, compatibility=known))
            scored = review.score_partial(dict(post=answer["post"], teacher=answer["teacher"],
                student=answer["student"], exact_matches=review.exact_matches(answer["teacher"], answer["student"]),
                teacher_meanings=assessments["contexts"][answer["id"]]), subjects=subjects,
                relationships=relationships, coverage=coverage)
            if matching_pending:
                scored["status"] = "pending"
                scored.get("scores", {}).pop("coverage", None)
                scored.setdefault("pending", {})["matching"] = matching_pending
                for finding in scored.get("findings", {}).get("coverage", []):
                    finding["covered"] = None
            answers.append(dict(id=answer["id"], note_id=answer["note_id"], scoring=scored,
                dependencies=dependencies, premises=premises))
        cohorts[cohort] = dict(answers=answers)
    for path, checksum in protected.items():
        if engine._sha256_file(Path(path)) != checksum:
            raise ValueError("coverage collection source changed: " + path)
    result = dict(schema_version=1, coverage=str(directory), output=str(output), sources=protected,
        inference_calls=0, **cohorts)
    output.parent.mkdir(parents=True, exist_ok=True)
    experiment.write(output, result)
    return result
