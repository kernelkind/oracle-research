"""Source-bound DSR review preparation, mechanical validation and scoring.

Semantic verdicts come from a supplied reviewer report. This module performs no
inference and does not repair answers or infer missing report judgments.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re

try:
    from . import extraction_pipeline as engine
    from .distillation_run import parse_subjects
except ImportError:
    import extraction_pipeline as engine
    from distillation_run import parse_subjects


def _fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"expected exact {label} fields: {', '.join(sorted(fields))}")


def load_saved_generations(dataset_manifest, definitions, base):
    """Bind selected validation answers to the frozen post, teacher and task.

    Matching, support and relationship preparation share these checks. Reserved
    test generation paths are rejected before opening them; answers are parsed
    through the production subject-result contract without rewriting wording.
    """
    try:
        from .distillation_run import subject_result
    except ImportError:
        from distillation_run import subject_result
    protected = {}

    def read_bound(reference):
        _fields(reference, {"path", "sha256"}, "saved validation reference")
        path = engine._resolve_path(reference["path"], "saved validation source", Path(base))
        raw = path.read_bytes()
        checksum = hashlib.sha256(raw).hexdigest()
        if checksum != reference["sha256"]:
            raise ValueError(f"saved validation source hash differs: {path}")
        protected[str(path)] = checksum
        return path, raw

    def decode(raw):
        return json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)

    manifest_path, raw = read_bound(dataset_manifest)
    manifest = decode(raw)
    if manifest["schema_version"] != 2 or manifest["tasks"] != {"subjects": "ASv6.100"}:
        raise ValueError("saved validation requires an ASv6.100 subjects-only dataset")
    splits = [manifest[name + "_note_ids"] for name in ("train", "evaluation", "test")]
    all_ids = [identifier for split in splits for identifier in split]
    if not splits[1] or len(set(all_ids)) != len(all_ids):
        raise ValueError("invalid or overlapping saved validation splits")
    rows = {}
    for name in ("evaluation", "references"):
        _, raw = read_bound(dict(path=str(manifest_path.parent / (name + ".jsonl")),
                                sha256=manifest["outputs"][name + ".jsonl"]))
        rows[name] = [decode(line) for line in raw.splitlines()]
    if [row["note_id"] for row in rows["evaluation"]] != splits[1]:
        raise ValueError("saved validation evaluation identities differ")
    references = {row["note_id"]: row for row in rows["references"]}
    if len(references) != len(rows["references"]):
        raise ValueError("duplicate saved validation reference identity")
    loaded = []
    for definition in definitions:
        generation = definition["generation"]
        _fields(generation, {"path", "sha256", "index", "note_id"}, "validation generation")
        path = engine._resolve_path(generation["path"], "validation generation", Path(base))
        index = generation["index"]
        if (type(index) is not int or not 0 <= index < len(rows["evaluation"])
                or generation["note_id"] != splits[1][index] or "test" in path.parts
                or path.name != "subjects.json" or path.parent.name != f"note-{index:04}"):
            raise ValueError("expected a saved validation generation")
        _, raw = read_bound({key: generation[key] for key in ("path", "sha256")})
        saved = decode(raw)
        if saved["note_id"] != generation["note_id"]:
            raise ValueError("saved validation identity differs")
        if saved["messages"] != rows["evaluation"][index]["messages"]:
            raise ValueError("saved validation input differs")
        reference = references[generation["note_id"]]
        messages = saved["messages"]
        suffix = "\n\n<post>\n" + reference["text"] + "\n</post>"
        if (reference["split"] != "evaluation" or len(messages) != 1 or messages[0]["role"] != "user"
                or not messages[0]["content"].endswith(suffix)
                or hashlib.sha256(messages[0]["content"][:-len(suffix)].encode()).hexdigest()
                   != manifest["subject_instruction_sha256"]):
            raise ValueError("saved validation prompt differs from instruction or note")
        teacher = parse_subjects(json.dumps(dict(subjects=[
            {key: row[key] for key in ("number", "context", "subject")} for row in reference["subjects"]])))
        parsed = subject_result(saved["note_id"], saved["answer"])
        if parsed["errors"]:
            raise ValueError(parsed["errors"][0]["error"])
        loaded.append(dict(definition=definition, post=reference["text"], teacher=teacher,
            student=parsed["subjects"], note_id=saved["note_id"],
            task_prompt=messages[0]["content"][:-len(suffix)]))
    return loaded, protected


def _numbers(value, known, label, *, nonempty=False):
    if (not isinstance(value, list) or (nonempty and not value)
            or any(not isinstance(number, str) or number not in known for number in value)
            or len(value) != len(set(value))):
        raise ValueError(f"invalid, duplicate or unknown {label}")
    return set(value)


def _reason(row):
    if not isinstance(row["reason"], str) or not row["reason"].strip():
        raise ValueError("review reasons must be nonblank strings")


def exact_matches(teacher, student):
    by_subject = {}
    for entry in student:
        by_subject.setdefault(entry["subject"], []).append(entry["number"])
    return [dict(teacher_number=entry["number"], student_number=number)
            for entry in teacher for number in by_subject.get(entry["subject"], [])]


def rank_generations(manifest_path, top=5):
    """Size all frozen pilot labels and select training extremes without inference.

    Answer bytes measure canonical saved subject JSON, not transport formatting
    or model tokens. Held-out notes contribute aggregate sizes only.
    """
    if type(top) is not int or top < 1:
        raise ValueError("top must be a positive integer")
    manifest_path = Path(manifest_path).resolve()
    protected = {}
    def read_bound(path, checksum=None):
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if checksum is not None and actual != checksum:
            raise ValueError(f"generation source hash differs: {path}")
        protected[str(path)] = actual
        return raw
    def decode(raw):
        return json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    manifest = decode(read_bound(manifest_path))
    if manifest["schema_version"] != 2 or set(manifest["tasks"]) != {"subjects"}:
        raise ValueError("generation ranking requires a subjects-only pilot manifest")
    splits = {name: manifest[key] for name, key in (
        ("train", "train_note_ids"), ("evaluation", "evaluation_note_ids"), ("test", "test_note_ids"))}
    if any(not isinstance(ids, list) or any(not isinstance(i, str) or not i for i in ids)
           for ids in splits.values()):
        raise ValueError("invalid frozen splits")
    identifiers = [identifier for ids in splits.values() for identifier in ids]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("invalid or overlapping frozen splits")
    assignments = {identifier: split for split, ids in splits.items() for identifier in ids}
    references_path = manifest_path.parent / "references.jsonl"
    training_path = manifest_path.parent / "train.jsonl"
    references = [decode(line) for line in read_bound(references_path,
        manifest["outputs"]["references.jsonl"]).splitlines()]
    if (len(references) != len(assignments)
            or {row["note_id"] for row in references} != set(assignments)):
        raise ValueError("reference identities differ from frozen splits")
    sizes, training_subjects = [], {}
    for row in references:
        identifier, split = row["note_id"], row["split"]
        if assignments[identifier] != split:
            raise ValueError("reference split differs from frozen split")
        raw = json.dumps(dict(subjects=row["subjects"]), ensure_ascii=False)
        subjects = parse_subjects(raw)
        sizes.append(dict(note_id=identifier, split=split, entries=len(subjects),
            edges=sum("." in entry["number"] for entry in subjects),
            distinct_subjects=len({entry["subject"] for entry in subjects}),
            answer_bytes=len(raw.encode("utf-8"))))
        if split == "train":
            training_subjects[identifier] = subjects
    lines = {}
    training_raw = read_bound(training_path, manifest["outputs"]["train.jsonl"])
    for line, raw in enumerate(training_raw.splitlines(), 1):
        row = decode(raw)
        identifier = row["note_id"]
        if identifier not in training_subjects or identifier in lines or row["task"] != "subjects":
            raise ValueError("training identities differ from frozen split")
        completion = row["completion"]
        if (len(completion) != 1 or completion[0]["role"] != "assistant"
                or parse_subjects(completion[0]["content"]) != training_subjects[identifier]):
            raise ValueError("saved training teacher answer differs from frozen reference")
        lines[identifier] = line
    if set(lines) != set(training_subjects):
        raise ValueError("training identities differ from frozen split")
    eligible = [row for row in sizes if row["split"] == "train"]
    rankings = {metric: sorted(eligible, key=lambda row: (-row[metric], row["note_id"]))[:top]
                for metric in ("entries", "answer_bytes")}
    selected = {}
    for ranked in rankings.values():
        for row in ranked:
            identifier = row["note_id"]
            selected.setdefault(identifier, dict(row, reference=dict(format="training_jsonl",
                path=str(training_path), sha256=protected[str(training_path)],
                line=lines[identifier], note_id=identifier)))
    return dict(schema_version=1, inference_calls=0, sources=protected,
        prompt_id=manifest["tasks"]["subjects"], eligible_split="train", top_per_metric=top,
        answer_size="canonical_subject_json_utf8_bytes",
        split_counts={name: len(ids) for name, ids in splits.items()},
        maxima_all_notes={metric: max((row[metric] for row in sizes), default=0)
                          for metric in ("entries", "edges", "distinct_subjects", "answer_bytes")},
        rankings=rankings, selected=list(selected.values()))


def _payload(case):
    value = json.loads(case["inputs"]["REVIEW_INPUT"],
                       object_pairs_hook=engine._position_decoder().unique_object)
    _fields(value, {"post", "teacher", "student", "exact_matches", "teacher_meanings"}, "review input")
    if not isinstance(value["post"], str):
        raise ValueError("post must be a string")
    for field in ("teacher", "student"):
        parse_subjects(json.dumps(dict(subjects=value[field])))
    if value["exact_matches"] != exact_matches(value["teacher"], value["student"]):
        raise ValueError("mechanical exact matches differ from the supplied answers")
    return value


def _groups(rows, teacher):
    known = {entry["number"] for entry in teacher}
    groups, seen = {}, set()
    for row in rows:
        numbers = _numbers(row["teacher_numbers"], known, "teacher numbers", nonempty=True)
        if seen & numbers:
            raise ValueError("overlapping teacher meaning groups")
        if type(row["required"]) is not bool:
            raise ValueError("required must be a Boolean")
        groups[frozenset(numbers)] = row["required"]
        seen.update(numbers)
    if seen != known:
        raise ValueError("omitted teacher numbers")
    by_subject = {}
    for entry in teacher:
        group = next(group for group in groups if entry["number"] in group)
        prior = by_subject.setdefault(entry["subject"], group)
        if prior != group:
            raise ValueError("exact duplicate teacher subjects must share a meaning group")
    return groups


def _ratio(numerator, denominator, empty):
    return dict(numerator=numerator, denominator=denominator,
                value=numerator / denominator if denominator else float(empty))


def validate(case, raw):
    """Validate a complete report and calculate fractions from its verdicts."""
    payload = _payload(case)
    report = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    _fields(report, {"schema_version", "prompt_id", "subjects", "relationships", "coverage"}, "review report")
    if type(report["schema_version"]) is not int or report["schema_version"] != 1:
        raise ValueError("expected review schema_version 1")
    version = re.match(r"(DSRv[1-9][0-9]*(?:\.[0-9]+)?)\b", case.get("prompt", ""))
    prompt_id = version[1] if version else "DSRv1"
    if report["prompt_id"] != prompt_id:
        raise ValueError(f"expected review prompt_id {prompt_id}")
    if any(not isinstance(report[key], list) for key in ("subjects", "relationships", "coverage")):
        raise ValueError("review verdicts and coverage must be arrays")
    student = {entry["number"]: entry for entry in payload["student"]}
    actual_edges = {(number.rpartition(".")[0], number) for number in student if "." in number}
    subjects, edges = {}, {}
    for row in report["subjects"]:
        _fields(row, {"number", "valid", "reason"}, "subject verdict")
        _reason(row)
        if (not isinstance(row["number"], str) or row["number"] not in student
                or row["number"] in subjects or type(row["valid"]) is not bool):
            raise ValueError("invalid, duplicate or unknown subject verdict")
        subjects[row["number"]] = row["valid"]
    if set(subjects) != set(student):
        raise ValueError("omitted subject verdict")
    for row in report["relationships"]:
        _fields(row, {"parent", "child", "valid", "reason"}, "relationship verdict")
        _reason(row)
        if not isinstance(row["parent"], str) or not isinstance(row["child"], str):
            raise ValueError("relationship numbers must be strings")
        edge = row["parent"], row["child"]
        if edge not in actual_edges or edge in edges or type(row["valid"]) is not bool:
            raise ValueError("invalid, duplicate or invented relationship verdict")
        edges[edge] = row["valid"]
    if set(edges) != actual_edges:
        raise ValueError("omitted immediate relationship verdict")
    for row in report["coverage"]:
        _fields(row, {"teacher_numbers", "required", "student_numbers",
                      "compatible_heading_numbers", "reason"}, "coverage row")
        _reason(row)
        matches = _numbers(row["student_numbers"], student, "student match numbers")
        headings = _numbers(row["compatible_heading_numbers"], student, "compatible heading numbers")
        if row["required"] is False and headings:
            raise ValueError("optional meanings must have empty compatibility lists")
        if row["required"] is True and not matches <= headings:
            raise ValueError("full matches of required meanings must also be compatible headings")
    groups = _groups(report["coverage"], payload["teacher"])
    frozen = payload["teacher_meanings"]
    if frozen is not None:
        if not isinstance(frozen, list):
            raise ValueError("teacher_meanings must be null or an array")
        for row in frozen:
            _fields(row, {"teacher_numbers", "required"}, "frozen teacher meaning")
        if _groups(frozen, payload["teacher"]) != groups:
            raise ValueError("teacher meaning groups or required flags differ from the fixed reference")
    row_for_number = {number: row for row in report["coverage"] for number in row["teacher_numbers"]}
    for match in payload["exact_matches"]:
        if match["student_number"] not in row_for_number[match["teacher_number"]]["student_numbers"]:
            raise ValueError("omitted mechanical exact match")
    # One candidate entry cannot represent two distinct complete teacher meanings.
    matched = set()
    for row in report["coverage"]:
        numbers = set(row["student_numbers"])
        if matched & numbers:
            raise ValueError("student entry matched to different teacher meanings")
        matched.update(numbers)
    coverage = []
    for row in report["coverage"]:
        if not row["required"]:
            continue
        matches = row["student_numbers"]
        missing = [heading for heading in row["compatible_heading_numbers"]
                   if not any(number == heading or number.startswith(heading + ".") for number in matches)]
        coverage.append(dict(teacher_numbers=row["teacher_numbers"], covered=bool(matches) and not missing,
                             matched_student_numbers=matches, missing_heading_numbers=missing))
    correct = sum(valid and ("." not in number or edges[number.rpartition(".")[0], number])
                  for number, valid in subjects.items())
    required = len(coverage)
    scores = dict(correctness=_ratio(correct, len(student), not required),
                  coverage=_ratio(sum(row["covered"] for row in coverage), required, True))
    findings = dict(incorrect_subjects=[number for number, valid in subjects.items() if not valid],
                    invalid_relationships=[dict(parent=parent, child=child)
                                           for (parent, child), valid in edges.items() if not valid],
                    coverage=coverage)
    result = dict(status="valid", output=raw, parsed=report, scores=scores, findings=findings,
                  teacher_meanings=[dict(teacher_numbers=row["teacher_numbers"], required=row["required"])
                                    for row in report["coverage"]])
    if "expected" in case.get("evidence", {}):
        result["qualification"] = check_expected(case["evidence"]["expected"], result)
        known = case["evidence"].get("known_teacher_meanings")
        if known is not None and _groups(known, payload["teacher"]) != groups:
            result["qualification"]["differences"].append(
                "teacher meaning groups or required flags differ from the known control")
            result["qualification"]["passed"] = False
    return result


def check_expected(expected, result):
    """Compare known controls without treating unknown judgments as gold."""
    differences = []
    report = result["parsed"]
    for metric, fraction in expected.get("scores", {}).items():
        numerator, denominator = fraction
        actual = result["scores"][metric]
        if actual["value"] != numerator / denominator:
            differences.append(f"{metric}: expected {numerator}/{denominator}, got {actual['value']}")
    for field, actual in (
        ("incorrect_subjects", result["findings"]["incorrect_subjects"]),
        ("invalid_relationship_children", [row["child"] for row in result["findings"]["invalid_relationships"]]),
    ):
        if field in expected and set(actual) != set(expected[field]):
            differences.append(f"{field}: expected {expected[field]}, got {actual}")
    for number in expected.get("valid_subjects", []):
        if not next(row["valid"] for row in report["subjects"] if row["number"] == number):
            differences.append(f"subject {number}: expected valid")
    for number in expected.get("valid_relationship_children", []):
        if not next(row["valid"] for row in report["relationships"] if row["child"] == number):
            differences.append(f"incoming relationship {number}: expected valid")
    for control in expected.get("meanings", []):
        row = next(row for row in report["coverage"] if control["teacher_number"] in row["teacher_numbers"])
        if "required" in control and row["required"] != control["required"]:
            differences.append(f"meaning {control['teacher_number']}: required flag differs")
        if "student_numbers" in control and set(row["student_numbers"]) != set(control["student_numbers"]):
            differences.append(f"meaning {control['teacher_number']}: full matches differ")
        if "missing_heading_numbers" in control:
            finding = next((finding for finding in result["findings"]["coverage"]
                            if control["teacher_number"] in finding["teacher_numbers"]), None)
            missing = set(finding["missing_heading_numbers"]) if finding else set()
            if not set(control["missing_heading_numbers"]) <= missing:
                differences.append(f"meaning {control['teacher_number']}: known missing placements absent")
    return dict(passed=not differences, differences=differences)


def score_saved_output(case, student_raw, reviewer_raw=None, *, truncated=False):
    """Apply saved-output failure rules before requiring any reviewer judgments."""
    if student_raw is None:
        raise ValueError("saved student output is missing; evaluation is blocked")
    try:
        if truncated:
            raise ValueError("saved student output is truncated")
        # The production parser already rejects duplicate keys and accepts a
        # complete JSON fence. Preserve that saved-output contract.
        student = parse_subjects(student_raw)
    except (ValueError, engine.RunnerError) as error:
        return dict(status="output_failure", error=str(error),
                    scores={name: _ratio(0, 0, False) for name in ("correctness", "coverage")})
    if student != _payload(case)["student"]:
        raise ValueError("saved student output differs from the frozen review input")
    if reviewer_raw is None:
        raise ValueError("reviewer report is missing; output remains ungraded")
    return validate(case, reviewer_raw)


def _signature(report, removed=()):
    removed = set(removed)
    return dict(
        subjects={row["number"]: row["valid"] for row in report["subjects"] if row["number"] not in removed},
        relationships={(row["parent"], row["child"]): row["valid"] for row in report["relationships"]
                       if row["parent"] not in removed and row["child"] not in removed},
        coverage={frozenset(row["teacher_numbers"]): (
            row["required"], frozenset(row["student_numbers"]) - removed,
            frozenset(row["compatible_heading_numbers"]) - removed) for row in report["coverage"]})


def qualification(cases, all_case_ids):
    """Gate complete saved qualification results, including large-case controls."""
    by_id = {case["id"]: case for case in cases}
    valid = {identifier: case for identifier, case in by_id.items() if case["status"] == "valid"}
    pending = [identifier for identifier in all_case_ids
               if identifier not in by_id or by_id[identifier]["status"] == "unrun"]
    differences, frozen = [], {}
    for identifier, case in by_id.items():
        if case["status"] not in {"valid", "unrun"}:
            differences.append(f"{identifier}: reviewer result is {case['status']}")
    for identifier, case in valid.items():
        differences.extend(f"{identifier}: {message}" for message in case["qualification"]["differences"])
        payload = _payload(case)
        key = payload["post"], json.dumps(payload["teacher"], sort_keys=True)
        groups = _groups(case["parsed"]["coverage"], payload["teacher"])
        if frozen.setdefault(key, groups) != groups:
            differences.append(f"{identifier}: teacher groups or required flags differ across versions")
        baseline_id = case["evidence"]["expected"].get("relative_to")
        if not baseline_id:
            continue
        if baseline_id not in valid:
            if baseline_id not in pending:
                pending.append(baseline_id)
            continue
        removed = [number for change in case["evidence"]["definition"]["changes"]
                   if change["op"] == "remove" for number in change["numbers"]]
        if _signature(case["parsed"]) != _signature(valid[baseline_id]["parsed"], removed):
            differences.append(f"{identifier}: judgments differ from {baseline_id} beyond the specified candidate change")
    return dict(status="failed" if differences else "pending" if pending else "passed",
                checked=len(valid), total=len(all_case_ids), pending=pending, differences=differences)


def _changes(teacher, changes):
    student = copy.deepcopy(teacher)
    for change in changes:
        op = change["op"]
        if op in {"remove", "replace"}:
            fields = {"op", "numbers"} | ({"old", "new"} if op == "replace" else set())
            _fields(change, fields, "candidate change")
            numbers = _numbers(change["numbers"], {entry["number"] for entry in student}, "change numbers", nonempty=True)
            if op == "remove":
                student = [entry for entry in student if entry["number"] not in numbers]
            else:
                if not isinstance(change["old"], str) or not change["old"] or not isinstance(change["new"], str):
                    raise ValueError("replacement requires nonempty old wording and string new wording")
                for entry in student:
                    if entry["number"] in numbers:
                        if change["old"] not in entry["subject"]:
                            raise ValueError("replacement wording is absent from the selected subject")
                        entry["subject"] = entry["subject"].replace(change["old"], change["new"])
        elif op == "renumber":
            _fields(change, {"op", "from", "to"}, "renumber change")
            if change["from"] not in {entry["number"] for entry in student}:
                raise ValueError("renumber prefix is absent")
            for entry in student:
                number = entry["number"]
                if number == change["from"] or number.startswith(change["from"] + "."):
                    entry["number"] = change["to"] + number[len(change["from"]):]
        elif op == "append":
            _fields(change, {"op", "entries"}, "append change")
            for entry in change["entries"]:
                if "copy" in entry:
                    _fields(entry, {"copy", "number"}, "copied entry")
                    source = next((item for item in teacher if item["number"] == entry["copy"]), None)
                    if source is None:
                        raise ValueError("copied teacher entry is absent")
                    student.append(dict(source, number=entry["number"]))
                else:
                    student.append(dict(entry))
        elif op == "empty":
            _fields(change, {"op"}, "empty change")
            student = []
        else:
            raise ValueError(f"unknown candidate change: {op}")
    # Reordering preserves entries and guarantees parents precede children after moves.
    if any(change["op"] == "renumber" for change in changes):
        student.sort(key=lambda entry: tuple(int(part) for part in entry["number"].split(".")))
    return parse_subjects(json.dumps(dict(subjects=student)))


def prepare_source(source, base, selected=None, load_report=None, *, include_teacher_meanings=True):
    """Read frozen worked examples or saved training controls into review cases."""
    _fields(source, {"schema_version", "task_prompt", "references", "cases"}, "review source")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected review source schema_version 1")
    protected, cache, reports = {}, {}, {}
    def read(path):
        if path not in cache:
            cache[path] = path.read_bytes()
            protected[str(path)] = hashlib.sha256(cache[path]).hexdigest()
        return cache[path]
    def bound(reference):
        path = engine._resolve_path(reference["path"], "review source", Path(base))
        raw = read(path)
        checksum = protected[str(path)]
        if checksum != reference["sha256"]:
            raise ValueError(f"review source hash differs: {path}")
        return raw
    _fields(source["task_prompt"], {"path", "sha256"}, "task prompt reference")
    task_prompt = bound(source["task_prompt"]).decode()
    examples = re.findall(r"<example>(.*?)</example>", task_prompt, re.S)
    identifiers = [definition["id"] for definition in source["cases"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate review case identity")
    if selected is not None and (len(selected) != len(set(selected)) or set(selected) - set(identifiers)):
        raise ValueError("unknown or duplicate review case selection")
    references, cases = {}, []
    for definition in source["cases"]:
        _fields(definition, {"id", "reference", "changes", "expected"}
                | ({"teacher_meanings"} & definition.keys()), "review case definition")
        identifier = engine._expect_identifier(definition["id"], "review case id")
        if selected is not None and identifier not in selected:
            continue
        key = definition["reference"]
        if key not in references:
            reference = source["references"][key]
            if reference["format"] == "as_example":
                _fields(reference, {"format", "index"}
                        | ({"required_meanings", "teacher_meanings_from"} & reference.keys()), "worked example reference")
                index = reference["index"]
                if type(index) is not int or not 1 <= index <= len(examples):
                    raise ValueError("unknown worked example")
                block = examples[index - 1]
                post = re.search(r"<post>\s*(.*?)\s*</post>", block, re.S)[1]
                teacher = parse_subjects(re.search(r"<output>\s*(.*?)\s*</output>", block, re.S)[1])
                note_id = f"ASv6.100-example-{index}"
            elif reference["format"] == "training_jsonl":
                _fields(reference, {"format", "path", "sha256", "line", "note_id"}
                        | ({"teacher_meanings_from"} & reference.keys()), "training control reference")
                if Path(reference["path"]).name != "train.jsonl":
                    raise ValueError("full-size qualification requires the training split")
                raw = bound(reference)
                index = reference["line"]
                lines = raw.splitlines()
                if type(index) is not int or not 1 <= index <= len(lines):
                    raise ValueError("unknown training source line")
                row = json.loads(lines[index - 1], object_pairs_hook=engine._position_decoder().unique_object)
                if row["note_id"] != reference["note_id"] or row["task"] != "subjects":
                    raise ValueError("training control identity or task differs")
                if len(row["prompt"]) != 1 or row["prompt"][0]["role"] != "user":
                    raise ValueError("expected complete original training prompt")
                prompt = row["prompt"][0]["content"]
                if not prompt.startswith(task_prompt):
                    raise ValueError("training control task prompt differs")
                match = re.fullmatch(r"\s*<post>\n(.*?)\n</post>\s*", prompt[len(task_prompt):], re.S)
                if match is None:
                    raise ValueError("training control full post binding differs")
                post = match[1]
                if len(row["completion"]) != 1 or row["completion"][0]["role"] != "assistant":
                    raise ValueError("expected one saved teacher completion")
                teacher = parse_subjects(row["completion"][0]["content"])
                note_id = row["note_id"]
            else:
                raise ValueError("unknown review reference format")
            frozen = None
            if include_teacher_meanings and "required_meanings" in reference:
                by_subject = {}
                for entry in teacher:
                    by_subject.setdefault(entry["subject"], []).append(entry["number"])
                required = {frozenset(numbers) for numbers in reference["required_meanings"]}
                if not required <= {frozenset(numbers) for numbers in by_subject.values()}:
                    raise ValueError("known required groups differ from worked example")
                frozen = [dict(teacher_numbers=numbers, required=frozenset(numbers) in required)
                          for numbers in by_subject.values()]
            known, frozen_source = frozen, None
            if include_teacher_meanings and "teacher_meanings_from" in reference:
                if known is not None:
                    raise ValueError("saved teacher meanings cannot override known worked-example groups")
                if load_report is None:
                    raise ValueError("teacher meaning reuse requires validated experiment reports")
                previous = reference["teacher_meanings_from"]
                _fields(previous, {"experiment", "case_id", "record_sha256"}, "teacher meaning reference")
                directory = engine._resolve_path(previous["experiment"], "teacher meaning experiment", Path(base))
                if directory not in reports:
                    report = load_report(directory)
                    if report["adapter"] != "distillation_review":
                        raise ValueError("teacher meanings require a distillation review experiment")
                    reports[directory] = {case["id"]: case for case in report["cases"]}
                    envelope = json.loads(read(directory / "experiment.json"))
                    read(Path(envelope["plan"]["run_directory"]) / "manifest.json")
                    for name in envelope["plan"]["files"]:
                        read(directory / name)
                saved = reports[directory].get(previous["case_id"])
                if saved is None or saved["status"] != "valid":
                    raise ValueError("teacher meanings require a valid reviewer case")
                if saved["receipt"]["record_sha256"] != previous["record_sha256"]:
                    raise ValueError("teacher meaning receipt differs from the frozen reference")
                saved_input = _payload(saved)
                if (saved["inputs"]["TASK_PROMPT"] != task_prompt
                        or saved_input["post"] != post or saved_input["teacher"] != teacher):
                    raise ValueError("saved teacher meaning task, post or teacher differs")
                frozen = validate(saved, saved["output"])["teacher_meanings"]
                read(Path(saved["receipt"]["results_path"]))
                frozen_source = {**previous, "experiment": str(directory)}
            references[key] = post, teacher, note_id, frozen, known, frozen_source
        post, teacher, note_id, frozen, known, frozen_source = references[key]
        if frozen_source is not None and "teacher_meanings" in definition:
            raise ValueError("candidate cannot override shared saved teacher meanings")
        student = _changes(teacher, definition["changes"])
        payload = dict(post=post, teacher=teacher, student=student,
                       exact_matches=exact_matches(teacher, student),
                       teacher_meanings=definition.get("teacher_meanings", frozen)
                           if include_teacher_meanings else None)
        cases.append(dict(id=identifier, inputs=dict(TASK_PROMPT=task_prompt,
            REVIEW_INPUT=json.dumps(payload, ensure_ascii=False)), evidence=dict(note_id=note_id,
            reference=key, definition=definition, expected=definition["expected"],
            known_teacher_meanings=known,
            **({"teacher_meanings_from": frozen_source} if frozen_source is not None else {}),
            teacher_entries=len(teacher), student_entries=len(student),
            student_edges=sum("." in entry["number"] for entry in student),
            student_output_raw=json.dumps(dict(subjects=student), ensure_ascii=False))))
    return cases, protected, dict(qualification_case_ids=identifiers)
