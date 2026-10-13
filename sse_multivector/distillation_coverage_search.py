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


def _snapshot(reference, base, *, observed_paths=None):
    """Load only an independently verified frozen native evaluation."""
    from experiment_runner import experiment
    review._fields(reference, {"path", "sha256"}, "coverage evaluation reference")
    path = engine._resolve_path(reference["path"], "coverage evaluation reference", Path(base))
    if path.name != "evaluation.json" or engine._sha256_file(path) != reference["sha256"]:
        raise ValueError("coverage evaluation hash differs")
    frozen = experiment.read(path)
    plans, initial_paths = {}, {path, path.parent / "evaluation.complete.json"}
    for entry in frozen["experiments"]:
        directory = Path(entry["path"])
        plan, _, _ = experiment.load(directory)
        plans[directory] = plan
        initial_paths.update(map(Path, plan["sources"]))
        initial_paths.update(directory / filename for filename in plan["files"])
        initial_paths.update((directory / "experiment.json", directory / "reviews.jsonl",
                             Path(plan["run_directory"]) / "results.jsonl",
                             Path(plan["run_directory"]) / "manifest.json"))
    state = {str(item): _file_state(item) for item in initial_paths}
    report = evaluation.report(path.parent, include_request_summary=False)
    _check_preparation_state(state)
    protected = dict(report["sources"])
    receipt_hashes = {}
    for item in (path, path.parent / "evaluation.complete.json"):
        protected[str(item)] = engine._sha256_file(item)
    for native in report["experiments"]:
        directory = Path(native["experiment"])
        plan = plans[directory]
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
    bundle, _ = evaluation._selection(frozen["selection"], path.parent)
    assessments = evaluation._assessments(frozen["assessment_directory"], bundle)
    _check_preparation_state(state)
    if observed_paths is not None:
        observed_paths.update(state)
    return report, assessments, protected


def _source_key(source, base):
    resolved = dict(source, evaluation=dict(source["evaluation"], path=str(engine._resolve_path(
        source["evaluation"]["path"], "coverage evaluation reference", Path(base)))))
    if "premise_audits" in source:
        resolved["premise_audits"] = [dict(row, path=str(engine._resolve_path(
            row["path"], "coverage premise audit", Path(base)))) for row in source["premise_audits"]]
    if "correction_experiments" in source:
        resolved["correction_experiments"] = [dict(row, path=str(engine._resolve_path(
            row["path"], "coverage correction experiment", Path(base)))) for row in source["correction_experiments"]]
    return json.dumps(resolved, sort_keys=True)


def _file_state(path):
    try:
        value = Path(path).stat()
    except FileNotFoundError:
        return None
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _check_preparation_state(state):
    for filename, expected in state.items():
        if _file_state(filename) != expected:
            raise ValueError("coverage premise changed while preparing: " + filename)


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
    bound = [item for item in audits.get((row["evidence"]["check"], row["input_sha256"], output_hash), [])
             if "prompt" not in item or item["prompt"] == row["prompt"]]
    return output_hash, bound


def _policy(value):
    if value not in {"audited", "grading"}:
        raise ValueError("coverage policy must be audited or grading")
    return value


def _accepted_premise(row, audits, policy="audited"):
    if row["status"] != "valid" or row.get("decision_conflicts"):
        return None
    output_hash, bound = _bound_premise_audits(row, audits)
    reviews = [item for item in row.get("reviews", []) if item.get("current") is True]
    assessments = reviews
    if policy == "grading":
        latest = {}
        for item in reviews:
            if item.get("verdict") in {"accept", "reject", "uncertain"}:
                latest[item.get("role")] = item
        assessments = list(latest.values())
    if row.get("origin") == "adjudicated":
        if policy != "grading" or row.get("adjudication", {}).get("actor") != "agent":
            return None
        assessments, bound = [], []
    if any(item.get("verdict") in ({"reject", "uncertain"} if policy == "audited" else {"reject"})
           for item in assessments + bound):
        return None
    if policy == "audited" and row.get("origin") != "mechanical" and not any(
            item.get("verdict") == "accept" for item in reviews + bound):
        return None
    premise = dict(case_id=row["id"], input_sha256=row["input_sha256"], output_sha256=output_hash,
        origin=row.get("origin"), receipt=row.get("receipt"), reviews=reviews, audits=bound)
    if row.get("origin") == "mechanical":
        premise.update(mechanical_evidence=row["mechanical_evidence"], mechanical_sha256=row["mechanical_sha256"])
    if row.get("correction"):
        premise["correction"] = row["correction"]
    if row.get("coverage_subset"):
        premise["coverage_subset"] = row["coverage_subset"]
    if row.get("adjudication"):
        premise["adjudication"] = row["adjudication"]
    if row.get("automatic_decision"):
        premise["automatic_decision"] = row["automatic_decision"]
    if row.get("automatic_equivalence_premise"):
        premise["automatic_equivalence_premise"] = row["automatic_equivalence_premise"]
    return premise


def _correction_references(paths, case_ids=None):
    if case_ids is not None:
        engine._validate_string_array(case_ids, "coverage correction selection", allow_empty=False)
        if not paths:
            raise ValueError("coverage correction selection requires correction experiments")
    return [dict(path=str(Path(path).expanduser().resolve()),
        sha256=engine._sha256_file(Path(path).expanduser().resolve() / "experiment.json"),
        **({"case_ids": list(case_ids)} if case_ids is not None else {})) for path in paths]


def _correction_rows(references, base, protected):
    """Read native fallback decisions, retaining their exact source and receipt bindings."""
    from experiment_runner import experiment
    if not isinstance(references, list):
        raise ValueError("coverage correction experiments must be an array")
    rows, seen, requested, known = [], set(), set(), set()
    for reference in references:
        review._fields(reference, {"path", "sha256"} | ({"case_ids"} & reference.keys()), "coverage correction experiment")
        selection = reference.get("case_ids")
        if selection is not None:
            engine._validate_string_array(selection, "coverage correction selection", allow_empty=False)
            requested.update(selection)
        path = engine._resolve_path(reference["path"], "coverage correction experiment", Path(base))
        identity = str(path), None if selection is None else tuple(selection)
        if identity in seen:
            continue
        seen.add(identity)
        manifest = path / "experiment.json"
        if engine._sha256_file(manifest) != reference["sha256"]:
            raise ValueError("coverage correction preparation changed")
        plan, _, _ = experiment.load(path)
        sources = dict(plan["sources"], **{str(manifest): reference["sha256"]})
        for name, checksum in plan["files"].items():
            sources[str(path / name)] = checksum
        ledger = path / "reviews.jsonl"
        if ledger.exists():
            sources[str(ledger)] = engine._sha256_file(ledger)
        for filename in ("results.jsonl", "manifest.json"):
            source = Path(plan["run_directory"]) / filename
            if source.exists():
                sources[str(source)] = engine._sha256_file(source)
        result = experiment.report(path, include_request_preview=False)
        for row in result["cases"]:
            known.add(row["id"])
            if selection is not None and row["id"] not in selection:
                continue
            if row["evidence"].get("check") not in {"matching", "support", "relationship", "coverage_search"}:
                raise ValueError("coverage correction requires native distillation review checks")
            receipt = row.get("receipt")
            if receipt:
                results = Path(receipt["results_path"])
                for source in (results, results.parent / "manifest.json"):
                    if str(source) not in sources:
                        sources[str(source)] = engine._sha256_file(source)
            rows.append(dict(row, correction_experiment=str(path)))
        for filename, checksum in sources.items():
            if filename in protected and protected[filename] != checksum:
                raise ValueError("coverage correction source changed: " + filename)
            protected[filename] = checksum
    if requested - known:
        raise ValueError("unknown coverage correction selection")
    return rows


def _correction_index(rows):
    index = {}
    for row in rows:
        index.setdefault((row["evidence"]["check"], row["input_sha256"], row["prompt"]), []).append(row)
    return index


def _native_correction_audits(audits, rows, protected, policy):
    """Propagate exact native rejections without changing historical review ledgers."""
    result = {key: list(value) for key, value in audits.items()}
    for row in rows:
        if row["status"] != "valid":
            continue
        reviews = [item for item in row.get("reviews", []) if item.get("current") is True]
        if policy == "grading":
            latest = {}
            for item in reviews:
                if item.get("verdict") in {"accept", "reject", "uncertain"}:
                    latest[item.get("role")] = item
            reviews = list(latest.values())
        key = (row["evidence"]["check"], row["input_sha256"], hashlib.sha256(row["output"].encode()).hexdigest())
        ledger = str(Path(row["correction_experiment"]) / "reviews.jsonl")
        for item in reviews:
            if item.get("verdict") == "reject":
                result.setdefault(key, []).append(dict(verdict="reject", reason=item["comment"],
                    path=ledger, sha256=protected[ledger], prompt=row["prompt"],
                    native_experiment=row["correction_experiment"], native_review=item,
                    receipt=row.get("receipt")))
    return result


def _corrected_row(row, index, audits, policy):
    # A fallback repairs a missing or rejected decision; it never replaces a usable
    # decision merely because another model draw has different wording or a verdict.
    if _accepted_premise(row, audits, policy) is not None:
        return row
    candidates = index.get((row["evidence"]["check"], row["input_sha256"], row["prompt"]), [])
    usable = [item for item in candidates if _accepted_premise(item, audits, policy) is not None]
    field = {"matching": "teacher_id", "coverage_search": "witness_student_number"}.get(
        row["evidence"]["check"], "valid")
    verdicts = {item["parsed"][field] is not None if field == "witness_student_number"
                else item["parsed"][field] for item in usable}
    if len(verdicts) > 1:
        return dict(row, decision_conflicts=[dict(experiment=item["correction_experiment"],
            case_id=item["id"], verdict=item["parsed"][field], receipt=item.get("receipt")) for item in usable])
    if not usable:
        return row
    chosen = usable[0]
    return dict(chosen, id=row["id"], evidence=row["evidence"], correction=dict(
        experiment=chosen["correction_experiment"], case_id=chosen["id"],
        original_case_id=row["id"], original_status=row["status"],
        original_output_sha256=(hashlib.sha256(row["output"].encode()).hexdigest()
                                if row.get("output") is not None else None),
        original_receipt=row.get("receipt"), original_reviews=row.get("reviews", [])))


def _corrected_report(report, corrections, audits, policy):
    if not corrections:
        return report
    index = _correction_index(corrections)
    result = dict(report)
    for cohort in ("random", "challenge"):
        result[cohort] = dict(report[cohort], answers=[dict(answer, checks={
            check: [_corrected_row(row, index, audits, policy) for row in rows]
            for check, rows in answer["checks"].items()}) for answer in report[cohort]["answers"]])
    return result


def _negative_subset(case, candidates, audits, template):
    """Derive a narrower negative question without rewriting its provider receipt."""
    from experiment_runner import inputs
    current = json.loads(case["inputs"]["COVERAGE_INPUT"])
    for row in candidates:
        if (_accepted_premise(row, audits, "grading") is None
                or row["parsed"]["witness_student_number"] is not None
                or row["inputs"].get("POST") != case["inputs"]["POST"]
                or inputs.render(template, row["inputs"]) != row["prompt"]):
            continue
        previous = json.loads(row["inputs"]["COVERAGE_INPUT"])
        if (previous["teacher_subject"] != current["teacher_subject"]
                or len(current["candidates"]) >= len(previous["candidates"])
                or any(candidate not in previous["candidates"] for candidate in current["candidates"])):
            continue
        retained = [candidate["student_number"] for candidate in current["candidates"]]
        return dict(row, id=case["id"], evidence=case["evidence"], coverage_subset=dict(
            rule="negative_search_candidate_subset", source_case_id=row["id"],
            current_inputs=case["inputs"], current_input_sha256=inputs.digest(case["inputs"]),
            current_prompt_sha256=hashlib.sha256(inputs.render(template, case["inputs"]).encode()).hexdigest(),
            retained_student_numbers=retained, removed_student_numbers=[candidate["student_number"]
                for candidate in previous["candidates"] if candidate["student_number"] not in retained]))
    return None


def _accepted_matching(teacher, matching, relationships, audits, policy="audited"):
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
        premise = _accepted_premise(row, audits, policy)
        own_guards = guards.get(number, [])
        guard_premises = [_accepted_premise(guard, audits, policy) for guard in own_guards]
        if (premise is not None
                and all(guard["status"] == "valid" and guard["parsed"]["valid"] is True for guard in own_guards)
                and all(guard is not None for guard in guard_premises)):
            accepted[number] = dict(teacher_id=identifier, premise=premise, self_guards=guard_premises)
    return accepted


def _matching_path_settlement(identity, teacher, group, matching, accepted, uncovered, guards, audits, policy="audited"):
    """Substitute an accepted equivalent parent into an actual trusted path."""
    target_guards = [_accepted_premise(row, audits, policy) for row in guards]
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


def _cases(report, assessments, audits=None, policy="audited", *, final_groups=None):
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
                and (any(item.get("verdict") in {"reject", "uncertain"}
                    for item in row.get("reviews", []) + _bound_premise_audits(row, audits)[1])
                    if policy == "audited" else _accepted_premise(row, audits, policy) is None)}
            accepted_matching = _accepted_matching(teacher, matching, answer["checks"]["relationship"], audits, policy)
            for ordinal, group in enumerate(groups, 1):
                if not group["required"]:
                    continue
                identity = dict(answer_id=answer["id"], teacher_numbers=group["teacher_numbers"])
                final_search = (answer["id"], tuple(group["teacher_numbers"])) in (final_groups or set())
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
                if any(row["status"] == "valid" and row["parsed"]["valid"] is False
                       and (policy == "audited" or _accepted_premise(row, audits, policy) is not None)
                       for row in guard_rows):
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
                    and _accepted_premise(row, audits, policy) is not None), None)
                if accepted_pair is not None and not final_search:
                    settlements.append(dict(identity, rule="accepted_uncovered_compatible_heading", covered=False,
                        witness_student_number=accepted_pair["evidence"]["heading_number"],
                        compatibility_premise=_accepted_premise(accepted_pair, audits, policy)))
                    continue
                derived = _matching_path_settlement(identity, teacher, group, matching,
                    accepted_matching, uncovered, guard_rows, audits, policy)
                if derived is not None and not final_search:
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
                baseline_pairs = {row["evidence"]["heading_number"]: row
                    for row in answer["checks"]["relationship"]
                    if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]}
                excluded = []
                for number in roots:
                    pair = baseline_pairs[number]
                    if not final_search and pair["status"] == "valid" and pair["parsed"]["valid"] is False:
                        premise = _accepted_premise(pair, audits, policy)
                        if premise is not None:
                            excluded.append(dict(student_number=number, compatibility_premise=premise))
                excluded_numbers = {row["student_number"] for row in excluded}
                roots = [number for number in roots if number not in excluded_numbers]
                if not roots:
                    if excluded:
                        settlements.append(dict(identity, rule="accepted_uncovered_incompatible_headings", covered=None,
                            excluded_incompatible_candidates=excluded, omitted_descendants=omitted,
                            semantic_status="Accepted negative roots; collection separately requires accepted descendant edges."))
                    else:
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
                evidence = dict(identity, check="coverage_search", cohort=cohort, note_id=answer["note_id"],
                    generation=answer["generation"], teacher_representative_number=representative,
                    matched_student_numbers=matches, covered_heading_numbers=sorted(covered),
                    original_uncovered_heading_numbers=uncovered,
                    candidate_student_numbers=[row["student_number"] for row in candidates], omitted_descendants=omitted,
                    excluded_incompatible_candidates=excluded,
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


def prepare_source(source, base, selected=None, *, preparation_context=None):
    fields = {"schema_version", "evaluation", "answer_ids"}
    review._fields(source, fields | ({"premise_audits", "policy", "correction_experiments"} & source.keys()), "coverage search source")
    policy = _policy(source.get("policy", "audited"))
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("coverage search source schema_version must be 1")
    key = _source_key(source, base)
    prepared = None if preparation_context is None else preparation_context.get("coverage_source", {}).get(key)
    if prepared is not None:
        _check_preparation_state(prepared["state"])
        cases, protected, preparation = prepared["cases"], prepared["protected"], prepared["preparation"]
    else:
        observed = {}
        snapshot = None if preparation_context is None else preparation_context.get("coverage_snapshot", {}).get(key)
        if snapshot is None:
            report, assessments, protected = _snapshot(source["evaluation"], base, observed_paths=observed)
            state = {**{str(path): _file_state(path) for path in protected}, **observed}
        else:
            report, assessments, protected, observed, state = snapshot
            _check_preparation_state(state)
        report = evaluation._answer_subset(report, source["answer_ids"])
        audits = _premise_audits(source.get("premise_audits", []), base, protected)
        state = {**state, **{path: _file_state(path) for path in protected if path not in state}}
        corrections = _correction_rows(source.get("correction_experiments", []), base, protected)
        state = {**state, **{path: _file_state(path) for path in protected if path not in state}}
        audits = _native_correction_audits(audits, corrections, protected, policy)
        report = _corrected_report(report, corrections, audits, policy)
        cases, settlements, guards = _cases(report, assessments, audits, policy)
        _check_preparation_state(state)
        preparation = dict(settlements=settlements, matching_self_guards=guards,
            semantic_status="Experimental, unqualified searches.")
        if preparation_context is not None:
            preparation_context.setdefault("coverage_source", {})[key] = dict(
                cases=cases, protected=protected, preparation=preparation, state=state)
    if selected is not None:
        engine._validate_string_array(selected, "coverage search selection", allow_empty=False)
        known = {row["id"] for row in cases}
        if len(selected) != len(set(selected)) or set(selected) - known:
            raise ValueError("unknown or duplicate coverage search selection")
        cases = [row for row in cases if row["id"] in selected]
    return cases, protected, dict(preparation, qualification_case_ids=[row["id"] for row in cases])


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
            reasoning_effort="xhigh", policy="audited", correction_experiments=None, correction_case_ids=None):
    """Prepare native search experiments; never performs inference."""
    from experiment_runner import experiment, inputs, project, prompt_cache
    project.configure(Path(__file__).resolve().parents[1])
    policy = _policy(policy)
    if reasoning_effort not in ("xhigh", "high", "medium", "low"):
        raise ValueError("reasoning_effort must be xhigh, high, medium or low")
    path = Path(evaluation_path).expanduser().resolve()
    path = path / "evaluation.json" if path.is_dir() else path
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("coverage search output already exists")
    reference = dict(path=str(path), sha256=engine._sha256_file(path))
    observed = {}
    snapshot = _snapshot(reference, path.parent, observed_paths=observed)
    if answer_ids is None:
        baseline = snapshot[0]
        answer_ids = [answer["id"] for cohort in ("random", "challenge") for answer in baseline[cohort]["answers"]]
    source = dict(schema_version=1, evaluation=reference, answer_ids=answer_ids, policy=policy)
    correction_references = _correction_references(correction_experiments or [], correction_case_ids)
    if correction_references:
        source["correction_experiments"] = correction_references
    if premise_audits is not None:
        source["premise_audits"] = [dict(path=str(Path(audit).expanduser().resolve()),
            sha256=engine._sha256_file(Path(audit).expanduser().resolve())) for audit in premise_audits]
    state = {**{str(item): _file_state(item) for item in snapshot[2]}, **observed}
    context = dict(coverage_snapshot={_source_key(source, path.parent): (*snapshot, observed, state)})
    cases, protected, preparation = prepare_source(source, path.parent, preparation_context=context)
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
        experiment.prepare(experiment.parser().parse_args(arguments), include_request_preview=False,
                           preparation_context=context)
        experiments.append(dict(path=str(destination), sha256=engine._sha256_file(destination / "experiment.json"),
                                occurrences=len(rows), prefix_cached=cached))
    _check_preparation_state(context["coverage_source"][_source_key(source, path.parent)]["state"])
    for filename, checksum in protected.items():
        if engine._sha256_file(Path(filename)) != checksum:
            raise ValueError("coverage premise changed while preparing: " + filename)
    frozen = dict(schema_version=1, evaluation=reference, answer_ids=answer_ids, sources=protected,
        policy=policy, correction_experiments=source.get("correction_experiments", []),
        premise_audits=source.get("premise_audits", []),
        experiments=experiments, inference_calls=0, preparation=preparation,
        semantic_status="Experimental. DCS-returned positive witnesses require separate unchanged DSL verification; conditional teacher-path settlements retain their accepted premises.")
    experiment.write(output / "coverage-search.json", frozen)
    experiment.write(output / "coverage-search.complete.json", {
        "coverage-search.json": engine._sha256_file(output / "coverage-search.json")})
    return dict(frozen, output=str(output), search_cases=len(cases))


def collect(coverage_directory, output, *, verification_experiments=None, premise_audits=None, correction_experiments=None,
            correction_case_ids=None, adjudications=None, automated_analysis=False, automatic=False,
            final_experiments=None, required_experiments=None, collection_context=None, answer_ids=None):
    """Score accepted native checks and searches without running the old matrix."""
    from experiment_runner import experiment, inputs, project
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
    if automatic:
        automated_analysis = True
    elif final_experiments or required_experiments:
        raise ValueError("automatic decision experiments require automatic collection")
    policy = _policy(frozen.get("policy", "audited"))
    if automated_analysis:
        if premise_audits or correction_experiments or correction_case_ids or adjudications:
            raise ValueError("automated analysis excludes agent audits, corrections and adjudications")
        policy = "grading"
    if adjudications and policy != "grading":
        raise ValueError("adjudications require grading policy")
    protected = dict(frozen["sources"])

    def verify_sources(sources):
        verified = {} if collection_context is None else collection_context.setdefault("verified_sources", {})
        for path, checksum in sources.items():
            stamp = _file_state(path)
            if verified.get(path) != (checksum, stamp):
                if engine._sha256_file(Path(path)) != checksum:
                    raise ValueError("coverage collection source changed: " + path)
                verified[path] = checksum, stamp

    verify_sources(protected)

    def protect(sources):
        for path, checksum in sources.items():
            if path in protected and protected[path] != checksum:
                raise ValueError("coverage collection source changed: " + path)
            protected[path] = checksum

    protected[str(frozen_path)] = engine._sha256_file(frozen_path)
    snapshot_key = json.dumps(frozen["evaluation"], sort_keys=True)
    cached = (collection_context or {}).get("snapshots", {}).get(snapshot_key)
    if cached is None:
        observed = {}
        baseline, assessments, snapshot_sources = _snapshot(frozen["evaluation"], directory, observed_paths=observed)
        if collection_context is not None:
            collection_context.setdefault("snapshots", {})[snapshot_key] = (
                baseline, assessments, snapshot_sources,
                {**{name: _file_state(name) for name in snapshot_sources}, **observed})
    else:
        baseline, assessments, snapshot_sources, snapshot_state = cached
        _check_preparation_state(snapshot_state)
    protect(snapshot_sources)
    baseline = evaluation._answer_subset(baseline, frozen["answer_ids"])
    if answer_ids is not None:
        if not automatic:
            raise ValueError("answer selection requires automatic collection")
        baseline = evaluation._answer_subset(baseline, answer_ids)
    audit_references = [dict(path=str(Path(path).expanduser().resolve()),
        sha256=engine._sha256_file(Path(path).expanduser().resolve())) for path in premise_audits or []]
    # Preparation audits remain part of the immutable native source definition.
    preparation_references = list(frozen.get("premise_audits", []))
    searches, verifiers = {}, {}
    audit_diagnostics = []
    automatic_requests, automatic_failures = [], []
    request_keys = set()
    configurations = {}
    final_matching_keys, final_coverage_keys = set(), set()

    def request(row, role="required"):
        if not automatic:
            return
        if row["status"] in {"failed", "malformed", "invalid_receipt"}:
            automatic_failures.append(dict(case_id=row["id"], check=row["evidence"]["check"],
                status=row["status"], receipt=row.get("receipt"), error=row.get("error")))
            return
        key = role, row["evidence"]["check"], row["input_sha256"], row["prompt"]
        if key in request_keys:
            return
        request_keys.add(key)
        identity = row["evidence"]["check"], row["input_sha256"], row["prompt"]
        configuration = configurations.get(identity, {})
        automatic_requests.append(dict(role=role, case={name: row[name] for name in
            ("id", "inputs", "evidence", "prompt", "input_sha256", "mechanical") if name in row},
            prompt_id=row["prompt"].split(None, 1)[0],
            adapter="distillation_coverage_search" if row["evidence"]["check"] == "coverage_search"
                else "distillation_review_evaluation", configuration=configuration.get("settings", {}),
            source_experiment=configuration.get("experiment")))

    def original(row):
        if not automated_analysis:
            return row
        diagnostics = [item for item in row.get("reviews", []) if item.get("current") is True]
        diagnostics += _bound_premise_audits(row, audits)[1] if row.get("output") is not None else []
        audit_diagnostics.extend(dict(item, check=row["evidence"]["check"], case_id=row["id"],
            answer_id=row["evidence"].get("answer_id"), input_sha256=row["input_sha256"],
            output_sha256=hashlib.sha256(row["output"].encode()).hexdigest() if row.get("output") else None)
            for item in diagnostics)
        return dict(row, reviews=[])

    def native(path):
        path = Path(path).expanduser().resolve()
        cache = None if collection_context is None else collection_context.setdefault("native", {}).get(str(path))
        state = {str(path / name): _file_state(path / name) for name in
            ("experiment.json", "reviews.jsonl", "run/results.jsonl", "run/manifest.json")}
        if cache is not None and cache[0] == state:
            _, plan, result = cache
        else:
            plan, _, _ = experiment.load(path)
            result = experiment.report(path, include_request_preview=False)
            if collection_context is not None:
                collection_context.setdefault("native", {})[str(path)] = (state, plan, result)
        protect(plan["sources"])
        protected[str(path / "experiment.json")] = engine._sha256_file(path / "experiment.json")
        for name in ("reviews.jsonl", "run/results.jsonl", "run/manifest.json"):
            source = path / name
            if source.exists():
                protected[str(source)] = engine._sha256_file(source)
        return plan, result

    for native_report in baseline["experiments"]:
        for row in native_report["cases"]:
            configurations[(row["evidence"]["check"], row["input_sha256"], row["prompt"])] = dict(
                experiment=native_report["experiment"], settings=native_report["settings"])

    for entry in frozen["experiments"]:
        path = Path(entry["path"])
        if engine._sha256_file(path / "experiment.json") != entry["sha256"]:
            raise ValueError("coverage native preparation changed")
        plan, result = native(path)
        definition = experiment.read(Path(plan["dataset"]["path"]))
        preparation_references.extend(definition.get("premise_audits", []))
        for row in result["cases"]:
            configurations[(row["evidence"]["check"], row["input_sha256"], row["prompt"])] = dict(
                experiment=str(path), settings=result["settings"])
            key = row["evidence"]["answer_id"], tuple(row["evidence"]["teacher_numbers"])
            if key in searches:
                raise ValueError("duplicate coverage search teacher group")
            searches[key] = row
    audits = _premise_audits(preparation_references + audit_references, directory, protected)
    if automated_analysis:
        baseline = dict(baseline, **{cohort: dict(baseline[cohort], answers=[dict(answer,
            checks={check: [original(row) for row in rows] for check, rows in answer["checks"].items()})
            for answer in baseline[cohort]["answers"]]) for cohort in ("random", "challenge")})
        searches = {key: original(row) for key, row in searches.items()}
        audits = {}
    corrections = _correction_rows(([] if automated_analysis else list(frozen.get("correction_experiments", []))) +
        _correction_references(correction_experiments or [], correction_case_ids), directory, protected)
    audits = _native_correction_audits(audits, corrections, protected, policy)
    correction_index = _correction_index(corrections)
    baseline = _corrected_report(baseline, corrections, audits, policy)
    from . import distillation_review_adjudication as adjudication
    adjudication_records = adjudication.load(adjudications or [], protected)
    adjudicated = adjudication.index(adjudication_records)
    adjudicated_occurrences = {(row["evidence"]["check"], row["id"]) for cohort in ("random", "challenge")
        for answer in baseline[cohort]["answers"] for rows in answer["checks"].values() for row in rows
        if (row["evidence"]["check"], row["input_sha256"], row["prompt"]) in adjudicated}
    adjudicated_answers = {answer["id"] for cohort in ("random", "challenge") for answer in baseline[cohort]["answers"]
        if any((row["evidence"]["check"], row["id"]) in adjudicated_occurrences
               for rows in answer["checks"].values() for row in rows)}
    if adjudicated:
        baseline = dict(baseline, **{cohort: dict(baseline[cohort], answers=[dict(answer,
            checks={check: [adjudication.apply(row, adjudicated) for row in rows]
                for check, rows in answer["checks"].items()}) for answer in baseline[cohort]["answers"]])
            for cohort in ("random", "challenge")})
    searches = {key: _corrected_row(row, correction_index, audits, policy) for key, row in searches.items()}
    for path in verification_experiments or []:
        _, result = native(path)
        for row in result["cases"]:
            if row["evidence"].get("check") != "relationship":
                raise ValueError("coverage verification requires native relationship checks")
            verifiers.setdefault((row["input_sha256"], row["prompt"]), []).append(original(row))
            configurations[("relationship", row["input_sha256"], row["prompt"])] = dict(
                experiment=str(Path(path).resolve()), settings=result["settings"])
    required_index, final_index = {}, {}
    if automatic:
        for role, paths, index in (("required", required_experiments or [], required_index),
                                   ("final", final_experiments or [], final_index)):
            for path in paths:
                _, result = native(path)
                if role == "final" and (result["settings"]["model"] != "gpt-6.1-sol"
                        or result["settings"]["reasoning_effort"] != "xhigh"):
                    raise ValueError("automatic final decisions require gpt-6.1-sol/xhigh")
                for saved in result["cases"]:
                    row = original(saved)
                    check = row["evidence"].get("check")
                    if check not in {"matching", "support", "relationship", "coverage_search"}:
                        raise ValueError("automatic decisions require native distillation checks")
                    if role == "final" and check not in {"matching", "coverage_search"}:
                        raise ValueError("automatic final decisions require matching or coverage search")
                    identity = check, row["input_sha256"], row["prompt"]
                    if identity in index and index[identity].get("receipt") != row.get("receipt"):
                        raise ValueError("automatic decision has more than one final native response")
                    index[identity] = dict(row, automatic_decision=dict(role=role,
                        experiment=str(Path(path).resolve()), case_id=row["id"]))
                    configurations[identity] = dict(experiment=str(Path(path).resolve()), settings=result["settings"])
                    if role == "required" and check == "relationship":
                        verifiers.setdefault((row["input_sha256"], row["prompt"]), []).append(row)

        def automatic_row(row):
            identity = row["evidence"]["check"], row["input_sha256"], row["prompt"]
            # A trusted teacher proof cannot be replaced by a model response.
            if row.get("origin") == "mechanical":
                return row
            chosen = final_index.get(identity)
            if chosen is None and _accepted_premise(row, {}, "grading") is None:
                chosen = required_index.get(identity)
            if chosen is None:
                return row
            if chosen["status"] != "valid":
                request(chosen)
            if identity in final_index and row["evidence"]["check"] == "matching":
                final_matching_keys.add(identity)
            return dict(chosen, id=row["id"], evidence=row["evidence"])

        baseline = dict(baseline, **{cohort: dict(baseline[cohort], answers=[dict(answer,
            checks={check: [automatic_row(row) for row in rows] for check, rows in answer["checks"].items()})
            for answer in baseline[cohort]["answers"]]) for cohort in ("random", "challenge")})
        # A final complete equivalence decision entails its own compatibility.
        # Keep the final DSM receipt as the premise instead of inventing a DSL receipt.
        for cohort in ("random", "challenge"):
            for answer in baseline[cohort]["answers"]:
                teacher = review._TeacherIndex(answer["teacher"])
                matching_by_number = {row["evidence"]["student_number"]: row for row in answer["checks"]["matching"]}
                relationships = []
                for row in answer["checks"]["relationship"]:
                    if row["evidence"]["role"] == "compatibility" and row.get("origin") != "mechanical":
                        match = matching_by_number[row["evidence"]["heading_number"]]
                        if (match.get("automatic_decision", {}).get("role") == "final"
                                and match["status"] == "valid" and match["parsed"]["teacher_id"] in
                                {teacher.by_number[number] for number in row["evidence"]["teacher_numbers"]}):
                            parsed = dict(valid=True, reason="The final complete-equivalence verdict entails compatibility with the same teacher meaning.")
                            row = dict(row, status="valid", parsed=parsed, output=json.dumps(parsed), reviews=[],
                                origin="derived", receipt=None, automatic_equivalence_premise=_accepted_premise(match, {}, "grading"))
                    relationships.append(row)
                answer["checks"]["relationship"] = relationships
    final_groups, matching_conflict_answers = set(), set()
    if automatic:
        # Retain every exact completed question. A narrower negative question
        # does not resolve a disputed positive witness from an earlier search.
        search_history = {}
        for row in list(searches.values()) + list(required_index.values()):
            if row["evidence"]["check"] == "coverage_search":
                identity = row["evidence"]["answer_id"], tuple(row["evidence"]["teacher_numbers"])
                search_history.setdefault(identity, []).append(row)
        # Detect disagreements before candidate exclusions remove a disputed witness.
        for cohort in ("random", "challenge"):
            for answer in baseline[cohort]["answers"]:
                teacher = review._TeacherIndex(answer["teacher"])
                matches_by_number = {row["evidence"]["student_number"]: row
                    for row in answer["checks"]["matching"] if row["status"] == "valid"}
                students = {row["number"]: row["subject"] for row in answer["student"]}
                group_matches = {}
                for pair in answer["checks"]["relationship"]:
                    if pair["evidence"]["role"] != "compatibility":
                        continue
                    key = answer["id"], tuple(pair["evidence"]["teacher_numbers"])
                    if key not in group_matches:
                        identifiers = {teacher.by_number[number] for number in key[1]}
                        matched = [number for number, row in matches_by_number.items()
                            if row["parsed"]["teacher_id"] in identifiers]
                        group_matches[key] = matched, review._matched_headings(matched)
                    matched, covered = group_matches[key]
                    compatible_rows = ([pair] if pair.get("origin") == "mechanical"
                        or pair.get("automatic_equivalence_premise") else
                        [pair] + verifiers.get((pair["input_sha256"], pair["prompt"]), []))
                    values = {row["parsed"]["valid"] for row in compatible_rows
                        if _accepted_premise(row, {}, "grading") is not None}
                    match = matches_by_number.get(pair["evidence"]["heading_number"])
                    if (match is not None and match["parsed"]["teacher_id"] in
                            {teacher.by_number[number] for number in pair["evidence"]["teacher_numbers"]}
                            and pair.get("origin") != "mechanical"
                            and not pair.get("automatic_equivalence_premise") and False in values):
                        matching_conflict_answers.add(answer["id"])
                        request(match, "final_matching")
                    witness = pair["evidence"]["heading_number"]
                    disputed_search = False
                    witness_searches = [search for search in search_history.get(key, [])
                        if search["status"] == "valid" and search["parsed"]["witness_student_number"] == witness
                        and search["inputs"].get("POST") == answer["post"]]
                    if matched and witness not in covered and False in values and witness_searches:
                        child_number = pair["evidence"]["teacher_representative_number"]
                        child = teacher.subjects[child_number]
                        contexts = [{name: row[name] for name in ("subject", "context")}
                            for row in teacher.interpretation_entries(students[witness], child,
                                                                     child_number=child_number)]
                        candidate = dict(student_number=witness, student_subject=students[witness],
                                         teacher_contexts=contexts)
                        for search in witness_searches:
                            question = json.loads(search["inputs"]["COVERAGE_INPUT"])
                            if question["teacher_subject"] == child and candidate in question["candidates"]:
                                disputed_search = True
                                break
                    if len(values) > 1 or disputed_search:
                        final_groups.add(key)
        for row in final_index.values():
            if row["evidence"]["check"] == "coverage_search":
                final_groups.add((row["evidence"]["answer_id"], tuple(row["evidence"]["teacher_numbers"])))
    current_settlements = frozen["preparation"]["settlements"]
    if policy == "grading":
        # Core corrections can change which headings still need a search. Saved
        # decisions remain usable only for the newly derived complete question.
        question_baseline = baseline
        if automated_analysis:
            question_baseline = dict(baseline, **{cohort: dict(baseline[cohort], answers=[answer
                for answer in baseline[cohort]["answers"] if answer["errors"] or
                    (answer["id"] not in matching_conflict_answers and all(
                        row["status"] == "valid" for row in answer["checks"]["matching"]))])
                for cohort in ("random", "challenge")})
        current_cases, current_settlements, _ = _cases(question_baseline, assessments, audits, policy,
                                                       final_groups=final_groups)
        template = (Path(__file__).parent / "distillation-review-v1/coverage-search-prompt-v1.md").read_text()
        negative_sources = list(searches.values()) + [row for row in corrections
            if row["evidence"]["check"] == "coverage_search"]
        if automatic:
            negative_sources.extend(row for row in required_index.values()
                if row["evidence"]["check"] == "coverage_search")
        current_searches = {}
        for case in current_cases:
            key = case["evidence"]["answer_id"], tuple(case["evidence"]["teacher_numbers"])
            checksum, prompt = inputs.digest(case["inputs"]), inputs.render(template, case["inputs"])
            saved = searches.get(key)
            if saved is None or saved["input_sha256"] != checksum or saved["prompt"] != prompt:
                saved = dict(case, input_sha256=checksum, prompt=prompt, status="unrun", output=None,
                    parsed=None, origin=None, receipt=None, reviews=[])
            else:
                saved = dict(saved, id=case["id"], inputs=case["inputs"], evidence=case["evidence"])
            saved = _corrected_row(saved, correction_index, audits, policy)
            if automatic:
                saved = automatic_row(saved)
                if saved.get("automatic_decision", {}).get("role") == "final":
                    final_coverage_keys.add(("coverage_search", checksum, prompt))
            if _accepted_premise(saved, audits, policy) is None and key not in final_groups:
                saved = _negative_subset(case, negative_sources, audits, template) or saved
            current_searches[key] = saved
        searches = current_searches
    for row in corrections:
        if row["evidence"]["check"] == "relationship":
            verifiers.setdefault((row["input_sha256"], row["prompt"]), []).append(row)
    if adjudicated:
        verifiers = {key: [adjudication.apply(row, adjudicated) for row in rows]
            for key, rows in verifiers.items()}
    settlements = {(row["answer_id"], tuple(row["teacher_numbers"])): row
        for row in current_settlements if "teacher_numbers" in row}
    cohorts = {}
    for cohort in ("random", "challenge"):
        answers = []
        for answer in baseline[cohort]["answers"]:
            if answer["errors"]:
                answers.append(dict(id=answer["id"], note_id=answer["note_id"],
                    scoring=dict(status="valid", scores=answer["scores"]), dependencies=[]))
                continue
            checks = answer["checks"]
            dependencies, premises, inconsistencies = [], [], []
            source_rows = {(row["id"], row["input_sha256"], hashlib.sha256(row["output"].encode()).hexdigest()): row
                for rows in checks.values() for row in rows if row["status"] == "valid"}

            def settlement_accepted(settlement):
                stored = [settlement[field] for field in ("matching_premise", "compatibility_premise")
                          if field in settlement]
                stored.extend(settlement.get("matching_self_guard_premises", []))
                for premise in stored:
                    key = premise["case_id"], premise["input_sha256"], premise["output_sha256"]
                    row = source_rows.get(key)
                    if row is None or _accepted_premise(row, audits, policy) is None:
                        dependencies.append(dict(check="relationship", case_id=premise["case_id"],
                            reason="Previously accepted settlement premise is now absent or disputed."))
                        return False
                return True

            def accepted(row, request_role="required"):
                premise = _accepted_premise(row, audits, policy)
                if premise is not None:
                    premises.append(premise)
                    return True
                dependencies.append(dict(check=row["evidence"]["check"], case_id=row["id"],
                    status=row["status"], reason="No accepted complete input/output-bound assessment.",
                    reviews=row.get("reviews", []), decision_conflicts=row.get("decision_conflicts", [])))
                request(row, request_role)
                return False

            subjects = {row["evidence"]["student_number"]: row["parsed"]["valid"]
                for row in checks["support"] if row["status"] == "valid" and accepted(row)}
            if automatic:
                for row in checks["support"]:
                    if row["status"] != "valid":
                        request(row)
            actual = {row["evidence"]["student_number"]: row for row in checks["relationship"]
                if row["evidence"]["role"] == "actual_relationship"}
            relationships = {number: row["parsed"]["valid"] if row["status"] == "valid" and accepted(row)
                else None for number, row in actual.items()}
            if automatic:
                for number, row in actual.items():
                    if subjects.get(number) is not False and row["status"] != "valid":
                        request(row)
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

                def assign(number, value, source):
                    if number in known and known[number] is not value:
                        inconsistencies.append(dict(teacher_numbers=group["teacher_numbers"], student_number=number,
                            existing_valid=known[number], conflicting_valid=value, source=source))
                        dependencies.append(dict(check="coverage_search", teacher_numbers=group["teacher_numbers"],
                            reason="Accepted exact compatibility evidence is contradictory."))
                    else:
                        known[number] = value

                pairs = [row for row in checks["relationship"] if row["evidence"]["role"] == "compatibility"
                    and row["evidence"]["teacher_numbers"] == group["teacher_numbers"]]
                search = searches.get(key)
                final_search = (automatic and search is not None
                    and search.get("automatic_decision", {}).get("role") == "final")
                if group["required"]:
                    for pair in pairs:
                        number = pair["evidence"]["heading_number"]
                        candidates = verifiers.get((pair["input_sha256"], pair["prompt"]), [])
                        if number in matches:
                            candidates = [pair] + candidates
                        accepted_pairs = [row for row in candidates if _accepted_premise(row, audits, policy) is not None]
                        if automatic and pair.get("origin") == "mechanical":
                            accepted_pairs = [pair]
                        elif automatic and pair.get("automatic_equivalence_premise"):
                            accepted_pairs = [pair]
                        elif final_search and number not in matches:
                            accepted_pairs = []
                        verdicts = {row["parsed"]["valid"] for row in accepted_pairs}
                        premises.extend(_accepted_premise(row, audits, policy) for row in accepted_pairs)
                        if len(verdicts) == 1:
                            assign(number, verdicts.pop(), pair["id"])
                        elif len(verdicts) > 1:
                            inconsistencies.append(dict(teacher_numbers=group["teacher_numbers"], student_number=number,
                                source=pair["id"], reason="Accepted exact DSL comparisons disagree."))
                        elif candidates:
                            dependencies.append(dict(check="relationship", case_id=pair["id"],
                                reason="Exact verification is disputed, unaudited or contradictory."))
                        if automatic and number in matches and not final_search:
                            if any(row["parsed"]["valid"] is False for row in accepted_pairs):
                                match = next(row for row in checks["matching"]
                                    if row["evidence"]["student_number"] == number)
                                if match.get("automatic_decision", {}).get("role") != "final":
                                    request(match, "final_matching")
                            elif not accepted_pairs:
                                request(pair)
                    settlement = settlements.get(key)
                    if (settlement is not None and settlement.get("covered") is False
                            and settlement.get("witness_student_number") and settlement_accepted(settlement)):
                        assign(settlement["witness_student_number"], True, settlement["rule"])
                    exclusions = []
                    omitted = []
                    for evidence in (settlement, search["evidence"] if search is not None else None):
                        if evidence is not None:
                            exclusions.extend(evidence.get("excluded_incompatible_candidates", []))
                            omitted.extend(evidence.get("omitted_descendants", []))
                    for excluded in exclusions:
                        proof = dict(compatibility_premise=excluded["compatibility_premise"])
                        if settlement_accepted(proof):
                            assign(excluded["student_number"], False, excluded["compatibility_premise"]["case_id"])
                            premises.append(excluded["compatibility_premise"])
                    if search is not None and accepted(search,
                            "final_coverage" if automatic and key in final_groups else "required"):
                        witness = search["parsed"]["witness_student_number"]
                        if witness is None:
                            for number in search["evidence"]["candidate_student_numbers"]:
                                assign(number, False, search["id"])
                            for alias in search["evidence"]["candidate_aliases"]:
                                for number in alias["student_numbers"]:
                                    assign(number, False, search["id"])
                        elif final_search:
                            assign(witness, True, search["id"])
                            for alias in search["evidence"]["candidate_aliases"]:
                                if alias["representative_student_number"] == witness:
                                    for number in alias["student_numbers"]:
                                        assign(number, True, search["id"])
                        elif known.get(witness) is not True:
                            dependencies.append(dict(check="coverage_search", case_id=search["id"],
                                reason="Positive search lacks an accepted exact positive DSL witness."))
                            if automatic:
                                if key in final_groups:
                                    request(search, "final_coverage")
                                else:
                                    pair = next(row for row in pairs if row["evidence"]["heading_number"] == witness)
                                    request(pair)
                        if automatic and key in final_groups and not final_search:
                            request(search, "final_coverage")
                    changed = True
                    while changed:
                        changed = False
                        for edge in omitted:
                            number, parent = edge["student_number"], edge["parent_number"]
                            if (known.get(parent) is False and relationships.get(number) is True
                                    and known.get(number) is not False):
                                new_fact = number not in known
                                assign(number, False, edge["edge_case_id"])
                                changed |= new_fact
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
            if inconsistencies:
                scored["status"] = "pending"
                scored.get("scores", {}).pop("coverage", None)
                scored.setdefault("pending", {})["coverage_inconsistencies"] = inconsistencies
                disputed = {tuple(row["teacher_numbers"]) for row in inconsistencies}
                for finding in scored.get("findings", {}).get("coverage", []):
                    if tuple(finding["teacher_numbers"]) in disputed:
                        finding["covered"] = None
            answers.append(dict(id=answer["id"], note_id=answer["note_id"], scoring=scored,
                dependencies=dependencies, premises=premises, coverage_inconsistencies=inconsistencies))
        cohorts[cohort] = dict(answers=answers)
    verify_sources(protected)
    result = dict(schema_version=1, coverage=str(directory), output=str(output), sources=protected,
        policy=policy, inference_calls=0, **cohorts)
    if automated_analysis:
        result.update(analysis_only=True, semantic_audits_applied=False, corrections_applied=False,
            saved_response_selection="Native per-plan saved response and receipt; no fallback experiment selection.",
            audit_diagnostics=list({json.dumps(row, sort_keys=True): row for row in audit_diagnostics}.values()))
    if automatic:
        complete = all(answer["scoring"]["status"] == "valid"
            and set(answer["scoring"].get("scores", {})) == {"correctness", "coverage"}
            for cohort in ("random", "challenge") for answer in result[cohort]["answers"])
        result.update(analysis_only=False, automatic_status="failed" if automatic_failures else
            "complete" if complete and not automatic_requests else "pending",
            automatic_requests=automatic_requests, automatic_failures=automatic_failures,
            automatic_summary=dict(final_matching_questions=len(final_matching_keys),
                final_coverage_questions=len(final_coverage_keys), manual_reviews=0))
    if adjudication_records:
        classifications = {(record["check"], record["original"]["input_sha256"], record["original_prompt_sha256"], record["original_output_sha256"],
            record["original_decision_classification"]) for record in adjudication_records}
        unresolved = sum(any(record["decision"] is None for record in records)
            or len({json.dumps(record["decision"], sort_keys=True) for record in records}) != 1
            for records in adjudicated.values())
        result["adjudication_summary"] = dict(actor="agent", records=len(adjudication_records),
            distinct_questions=len(adjudicated), resolved_questions=len(adjudicated) - unresolved,
            unresolved_questions=unresolved, affected_occurrences=len(adjudicated_occurrences),
            affected_answers=len(adjudicated_answers), original_decision_classifications={label:
                sum(row[-1] == label for row in classifications) for label in ("correct", "incorrect", "uncertain")})
    output.parent.mkdir(parents=True, exist_ok=True)
    experiment.write(output, result)
    return result
