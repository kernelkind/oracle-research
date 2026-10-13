"""Source-bound, pre-call agent assessments for complete validation answers.

Teacher contexts are recorded separately from candidate judgments. Neither is
a reviewer output or independently adjudicated gold. Frozen files cannot change.
"""
from pathlib import Path

from . import distillation_review as review
from . import distillation_review_preview as preview
from . import distillation_review_trial as trial
from . import distillation_run as run


def answers(bundle):
    return [(f"{prefix}{index:02}", row) for cohort, prefix in (("random", "R"), ("challenge", "C"))
            for index, row in enumerate(bundle[cohort]["answers"], 1)]


def _answer(bundle, identifier):
    found = [row for alias, row in answers(bundle) if identifier in (alias, row["id"])]
    if len(found) != 1:
        raise ValueError("unknown or ambiguous trial answer")
    return found[0]


def _context_key(row):
    return preview._digest({key: row[key] for key in ("note_id", "post", "teacher", "task_prompt")})


def inspect(selection_path, answer_id=None, *, teacher_only=False):
    bundle = trial.load_trial(selection_path)
    if answer_id is None:
        return dict(inference_calls=0, answers=[dict(id=alias, cohort=row["cohort"],
            teacher_entries=len(row["teacher"]), student_entries=len(row["student"]),
            invalid=bool(row["errors"])) for alias, row in answers(bundle)])
    row = _answer(bundle, answer_id)
    result = dict(inference_calls=0, answer_id=answer_id, note_id=row["note_id"],
                  post=row["post"], teacher=row["teacher"], task_prompt=row["task_prompt"])
    if not teacher_only:
        result.update(student=row["student"], errors=row["errors"],
                      exact_matches=review.exact_matches(row["teacher"], row["student"]))
    return result


def _validate_expectations(row, context, value, *, allow_ancestor_paths=True):
    review._fields(value, {"matching", "support", "relationships", "compatibility"}, "trial expectations")
    known = {s["number"]: s["subject"] for s in row["student"]} if not row["errors"] else {}
    index = review._TeacherIndex(row["teacher"])
    for field in ("matching", "support", "relationships", "compatibility"):
        if not isinstance(value[field], list):
            raise ValueError("trial expectation rows must be arrays")
    for field in ("matching", "support"):
        seen = set()
        for entry in value[field]:
            fields = {"student_number", "reason", "teacher_number" if field == "matching" else "valid"}
            if field == "matching" and "unresolved" in entry:
                fields.add("unresolved")
            review._fields(entry, fields, "expected " + field)
            number = entry.get("student_number")
            if number not in known or number in seen:
                raise ValueError("unknown or duplicate expected student number")
            seen.add(number)
            if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
                raise ValueError("expected judgment requires a reason")
            if field == "matching":
                expected = entry.get("teacher_number")
                if expected is not None and expected not in index.by_number:
                    raise ValueError("unknown expected teacher number")
                mechanical = index.matching(known[number])
                if mechanical is not None:
                    actual = preview._decode(mechanical["output"])["teacher_id"]
                    expected_id = index.by_number[expected] if expected is not None else None
                    if expected_id != actual or entry.get("unresolved", False):
                        raise ValueError("expectation contradicts exact trusted teacher wording")
                if type(entry.get("unresolved", False)) is not bool or (entry.get("unresolved") and expected is not None):
                    raise ValueError("unresolved matching must have a null teacher number")
            else:
                if entry.get("valid") is not None and type(entry["valid"]) is not bool:
                    raise ValueError("support expectation must be Boolean or unresolved")
                if index.support(known[number]) is not None and entry.get("valid") is False:
                    raise ValueError("expectation contradicts exact trusted teacher support")
        if seen != set(known):
            raise ValueError("omitted expected student judgment")
    expected_children = {n for n in known if "." in n}
    children = set()
    for entry in value["relationships"]:
        review._fields(entry, {"child", "valid", "reason"}, "expected relationship")
        child = entry.get("child")
        if child not in expected_children or child in children:
            raise ValueError("unknown or duplicate expected relationship")
        children.add(child)
        if entry.get("valid") is not None and type(entry["valid"]) is not bool:
            raise ValueError("relationship expectation must be Boolean or unresolved")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError("expected relationship requires a reason")
        if (index.relationship(known[child.rpartition(".")[0]], known[child],
                               allow_ancestor_paths=allow_ancestor_paths) is not None
                and entry.get("valid") is False):
            raise ValueError("expectation contradicts a trusted relationship")
    if children != expected_children:
        raise ValueError("omitted expected immediate relationship")
    groups = {frozenset(g["teacher_numbers"]) for g in context if g["required"]}
    seen = set()
    for entry in value["compatibility"]:
        review._fields(entry, {"teacher_numbers", "compatible_heading_numbers", "reason"}, "expected compatibility")
        review._numbers(entry["teacher_numbers"], index.by_number, "expected teacher numbers", nonempty=True)
        group = frozenset(entry.get("teacher_numbers", []))
        if group not in groups or group in seen:
            raise ValueError("unknown or duplicate expected compatibility group")
        seen.add(group)
        headings = entry.get("compatible_heading_numbers")
        if headings is not None:
            review._numbers(headings, known, "expected compatible headings")
            representative = next(g["teacher_numbers"][0] for g in context
                                  if frozenset(g["teacher_numbers"]) == group)
            subject = next(s["subject"] for s in row["teacher"] if s["number"] == representative)
            if any(index.relationship(text, subject, allow_ancestor_paths=allow_ancestor_paths) is not None
                   and number not in headings
                   for number, text in known.items()):
                raise ValueError("expectation contradicts trusted compatibility")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError("expected compatibility requires a reason")
    if seen != groups and not row["errors"]:
        raise ValueError("omitted expected required compatibility group")


def record(selection_path, answer_id, directory, *, teacher_meanings=None, expectations=None, reason):
    """Record one independently assessed context or answer before freezing."""
    selection_path = Path(selection_path).expanduser().resolve()
    bundle = trial.load_trial(selection_path)
    row = _answer(bundle, answer_id)
    directory = Path(directory).expanduser().resolve()
    if any((directory / filename).exists() for filename in
           ("assessment.complete.json", "inventory.complete.json")):
        raise ValueError("trial assessments are frozen")
    if (teacher_meanings is None) == (expectations is None) or not isinstance(reason, str) or not reason.strip():
        raise ValueError("supply one teacher context or expectations and an assessment reason")
    bound = dict(path=str(selection_path), sha256=run.sha256(selection_path))
    context_path = directory / ("teacher-" + _context_key(row) + ".json")
    if teacher_meanings is not None:
        if not isinstance(teacher_meanings, list):
            raise ValueError("teacher meanings must be an array")
        for group in teacher_meanings:
            review._fields(group, {"teacher_numbers", "required"}, "assessed teacher meaning")
        review._groups(teacher_meanings, row["teacher"])
        path = context_path
        data = dict(schema_version=1, origin="agent_assessed", selection=bound,
                    context_key=_context_key(row), teacher_meanings=teacher_meanings, reason=reason)
    else:
        if not context_path.is_file():
            raise ValueError("record the candidate-independent teacher context first")
        context = run.read_json(context_path)["teacher_meanings"]
        _validate_expectations(row, context, expectations)
        path = directory / ("answer-" + preview._digest(row["id"]) + ".json")
        data = dict(schema_version=2, origin="agent_assessed", selection=bound,
            answer_id=row["id"], teacher_context_sha256=run.sha256(context_path),
            expectations=expectations, reason=reason)
    if path.exists():
        raise ValueError("assessment already exists and cannot overwrite frozen judgments")
    run.write_json(path, data)
    return dict(inference_calls=0, path=str(path), sha256=run.sha256(path), origin="agent_assessed")


def record_exact_groups(selection_path, answer_id, directory, required_numbers, optional_numbers, *, reason):
    """Expand explicit classifications using only identical trusted wording."""
    row = _answer(trial.load_trial(selection_path), answer_id)
    index = review._TeacherIndex(row["teacher"])
    classified = {}
    for numbers, required in ((required_numbers, True), (optional_numbers, False)):
        review._numbers(numbers, index.by_number, "assessed teacher numbers")
        for number in numbers:
            identifier = index.by_number[number]
            if identifier in classified:
                raise ValueError("duplicate classified teacher meaning")
            classified[identifier] = required
    if set(classified) != set(index.numbers):
        raise ValueError("classify every distinct trusted teacher meaning explicitly")
    return record(selection_path, answer_id, directory, teacher_meanings=[
        dict(teacher_numbers=numbers, required=classified[identifier])
        for identifier, numbers in index.numbers.items()], reason=reason)


def record_wording_expectations(selection_path, answer_id, directory, value, *, reason):
    """Expand explicitly judged identical inputs to all numbered occurrences."""
    row = _answer(trial.load_trial(selection_path), answer_id)
    review._fields(value, {"matching", "support", "relationships", "compatibility"}, "wording expectations")
    students = {s["number"]: s["subject"] for s in row["student"]}
    def key(number, edge=False):
        if number not in students:
            raise ValueError("unknown assessed student number")
        if edge:
            parent = number.rpartition(".")[0]
            if parent not in students:
                raise ValueError("expected an immediate child number")
            return students[parent], students[number]
        return students[number]
    expanded = {}
    for field in ("matching", "support", "relationships"):
        name = "child" if field == "relationships" else "student_number"
        labels = {}
        for entry in value[field]:
            meaning = key(entry[name], field == "relationships")
            if meaning in labels:
                raise ValueError("duplicate assessed wording input")
            labels[meaning] = entry
        expanded[field] = []
        for number in students:
            if field == "relationships" and "." not in number:
                continue
            meaning = key(number, field == "relationships")
            if meaning not in labels:
                raise ValueError("omitted distinct assessed wording input")
            expanded[field].append(dict(labels[meaning], **{name: number}))
    expanded["compatibility"] = []
    for entry in value["compatibility"]:
        headings = entry["compatible_heading_numbers"]
        words = None if headings is None else {key(number) for number in headings}
        expanded["compatibility"].append(dict(entry, compatible_heading_numbers=None if words is None else
            [number for number, subject in students.items() if subject in words]))
    return record(selection_path, answer_id, directory, expectations=expanded, reason=reason)


def _inventory_rows(bundle):
    result = {}
    for _, row in answers(bundle):
        result.setdefault(_context_key(row), []).append(row)
    return result


def _inventory_teacher(path, selected, checked_selections, sources):
    """Verify an original teacher-only record against its sealed source selection."""
    data = run.read_json(path)
    if (type(data["schema_version"]) is not int or data["schema_version"] not in (1, 2)
            or data["origin"] != "agent_assessed" or data["context_key"] != _context_key(selected)):
        raise ValueError("teacher inventory source differs")
    review._fields(data["selection"], {"path", "sha256"}, "teacher inventory selection")
    selection = Path(data["selection"]["path"]).expanduser().resolve()
    binding = (str(selection), data["selection"]["sha256"])
    if binding not in checked_selections:
        if run.sha256(selection) != binding[1]:
            raise ValueError("teacher inventory original selection hash differs")
        bundle = trial.load_trial(selection)
        checked_selections[binding] = (_inventory_rows(bundle), bundle["sources"])
    original_rows, original_sources = checked_selections[binding]
    sources.update(original_sources)
    sources[str(selection)] = binding[1]
    seal = selection.parent / "selection.complete.json"
    sources[str(seal)] = run.sha256(seal)
    originals = original_rows.get(data["context_key"], [])
    if not originals or any(original[key] != selected[key] for key in
            ("note_id", "post", "teacher", "task_prompt") for original in originals):
        raise ValueError("teacher inventory context differs from its original selection")
    for group in data["teacher_meanings"]:
        review._fields(group, {"teacher_numbers", "required"}, "inventoried teacher meaning")
    review._groups(data["teacher_meanings"], selected["teacher"])
    checksum = run.sha256(path)
    assessment_seal = path.parent / "assessment.complete.json"
    if assessment_seal.is_file():
        if run.read_json(assessment_seal).get(str(path)) != checksum:
            raise ValueError("frozen teacher inventory source hash differs")
        sources[str(assessment_seal)] = run.sha256(assessment_seal)
    sources[str(path)] = checksum
    return data["teacher_meanings"]


def prepare_inventory(selection_path, output, source_directories=()):
    """Freeze reusable teacher contexts only; missing policies stay explicit."""
    selection_path = Path(selection_path).expanduser().resolve()
    bundle = trial.load_trial(selection_path)
    directory = Path(output).expanduser().resolve()
    if directory.exists():
        raise ValueError("teacher inventory output already exists and cannot overwrite frozen contexts")
    wanted = _inventory_rows(bundle)
    sources = {str(selection_path): run.sha256(selection_path),
        str(selection_path.parent / "selection.complete.json"):
            run.sha256(selection_path.parent / "selection.complete.json")}
    imported, checked = {}, {}
    for source in source_directories:
        source = Path(source).expanduser().resolve()
        if not source.is_dir():
            raise ValueError("teacher inventory assessment directory is missing")
        for key, rows in wanted.items():
            path = source / ("teacher-" + key + ".json")
            if not path.is_file():
                continue
            candidate_sources = {}
            groups = _inventory_teacher(path, rows[0], checked, candidate_sources)
            if key in imported and imported[key]["teacher_meanings"] != groups:
                raise ValueError("conflicting teacher inventory policies for the same source context")
            if key not in imported:
                sources.update(candidate_sources)
                imported[key] = dict(context_key=key, teacher_meanings=groups,
                    source=dict(path=str(path), sha256=run.sha256(path)))
    missing = [dict(context_key=key, note_id=rows[0]["note_id"],
        answer_ids=[row["id"] for row in rows]) for key, rows in wanted.items() if key not in imported]
    value = dict(schema_version=1, origin="teacher_inventory", inference_calls=0,
        selection=dict(path=str(selection_path), sha256=run.sha256(selection_path)),
        contexts=list(imported.values()), missing_contexts=missing, sources=sources)
    path = directory / "inventory.json"
    run.write_json(path, value)
    run.write_json(directory / "inventory.complete.json", {path.name: run.sha256(path)})
    return dict(inference_calls=0, inventory_path=str(path), sha256=run.sha256(path),
        context_count=len(imported), total_contexts=len(wanted),
        answer_count=sum(len(rows) for rows in wanted.values()), missing_contexts=missing)


def _load_inventory(directory, selection_bundle):
    path = directory / "inventory.json"
    seal = directory / "inventory.complete.json"
    if run.read_json(seal) != {path.name: run.sha256(path)}:
        raise ValueError("teacher inventory hash differs")
    data = run.read_json(path)
    review._fields(data, {"schema_version", "origin", "inference_calls", "selection",
                         "contexts", "missing_contexts", "sources"}, "teacher inventory")
    if (type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["origin"] != "teacher_inventory" or data["inference_calls"] != 0):
        raise ValueError("teacher inventory schema differs")
    review._fields(data["selection"], {"path", "sha256"}, "teacher inventory selection")
    selection = Path(data["selection"]["path"])
    if (run.sha256(selection) != data["selection"]["sha256"]
            or run.read_json(selection) != selection_bundle):
        raise ValueError("teacher inventory selection differs")
    for filename, checksum in data["sources"].items():
        if run.sha256(filename) != checksum:
            raise ValueError("teacher inventory source hash differs: " + filename)
    wanted = _inventory_rows(selection_bundle)
    contexts, checked = {}, {}
    sources = {str(selection): data["selection"]["sha256"],
        str(selection.parent / "selection.complete.json"):
            run.sha256(selection.parent / "selection.complete.json")}
    for item in data["contexts"]:
        review._fields(item, {"context_key", "teacher_meanings", "source"}, "teacher inventory context")
        review._fields(item["source"], {"path", "sha256"}, "teacher inventory context source")
        key = item["context_key"]
        if key not in wanted or key in contexts:
            raise ValueError("unknown or duplicate teacher inventory context")
        source = Path(item["source"]["path"])
        if run.sha256(source) != item["source"]["sha256"]:
            raise ValueError("teacher inventory context source hash differs")
        groups = _inventory_teacher(source, wanted[key][0], checked, sources)
        if groups != item["teacher_meanings"]:
            raise ValueError("teacher inventory policy differs from original source")
        contexts[key] = groups
    missing = [dict(context_key=key, note_id=rows[0]["note_id"],
        answer_ids=[row["id"] for row in rows]) for key, rows in wanted.items() if key not in contexts]
    if missing != data["missing_contexts"] or sources != data["sources"]:
        raise ValueError("teacher inventory source or missing-context inventory differs")
    sources.update({str(path): run.sha256(path), str(seal): run.sha256(seal)})
    return dict(contexts={row["id"]: contexts[key] for key, rows in wanted.items()
                         if key in contexts for row in rows}, expectations={}, sources=sources)


def load_assessments(directory, selection_bundle):
    directory = Path(directory).expanduser().resolve()
    if (directory / "inventory.json").is_file():
        return _load_inventory(directory, selection_bundle)
    contexts, expectations, sources = {}, {}, {}
    checked_selections = set()
    def check_selection(bound):
        path = Path(bound["path"])
        key = (str(path), bound["sha256"])
        if key not in checked_selections:
            if run.sha256(path) != bound["sha256"] or run.read_json(path) != selection_bundle:
                raise ValueError("assessment selection differs")
            checked_selections.add(key)
    for _, row in answers(selection_bundle):
        context_path = directory / ("teacher-" + _context_key(row) + ".json")
        if context_path.is_file():
            data = run.read_json(context_path)
            if (type(data["schema_version"]) is not int or data["schema_version"] not in (1, 2)
                    or data["context_key"] != _context_key(row) or data["origin"] != "agent_assessed"):
                raise ValueError("teacher assessment source differs")
            check_selection(data["selection"])
            review._groups(data["teacher_meanings"], row["teacher"])
            contexts[row["id"]] = data["teacher_meanings"]
            sources[str(context_path)] = run.sha256(context_path)
        answer_path = directory / ("answer-" + preview._digest(row["id"]) + ".json")
        if answer_path.is_file():
            data = run.read_json(answer_path)
            if (type(data["schema_version"]) is not int or data["schema_version"] not in (1, 2)
                    or data["answer_id"] != row["id"] or data["origin"] != "agent_assessed"
                    or data["teacher_context_sha256"] != sources.get(str(context_path))):
                raise ValueError("answer assessment reference differs")
            check_selection(data["selection"])
            # v1 judgments were recorded before ancestor-path proofs existed.
            # Validate their original contract without rewriting frozen labels.
            _validate_expectations(row, contexts[row["id"]], data["expectations"],
                                   allow_ancestor_paths=data["schema_version"] >= 2)
            expectations[row["id"]] = data["expectations"]
            sources[str(answer_path)] = run.sha256(answer_path)
    seal_path = directory / "assessment.complete.json"
    if seal_path.is_file():
        if run.read_json(seal_path) != sources:
            raise ValueError("frozen assessment hashes differ")
        sources[str(seal_path)] = run.sha256(seal_path)
    return dict(contexts=contexts, expectations=expectations, sources=sources)


def freeze(selection_path, directory):
    bundle = trial.load_trial(selection_path)
    result = load_assessments(directory, bundle)
    wanted = {row["id"] for _, row in answers(bundle)}
    if set(result["contexts"]) != wanted or set(result["expectations"]) != wanted:
        raise ValueError("incomplete pre-call trial assessments")
    path = Path(directory).expanduser().resolve() / "assessment.complete.json"
    if path.exists():
        raise ValueError("trial assessments already frozen")
    run.write_json(path, result["sources"])
    return dict(inference_calls=0, answers=len(wanted), path=str(path), sha256=run.sha256(path))
