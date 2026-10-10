"""Lossless offline collection of source-bound SP/MP inputs for SSE."""
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

try:
    from . import extraction_pipeline as engine
    from . import corpus_inputs
except ImportError:
    import extraction_pipeline as engine
    import corpus_inputs


def validate_collection(directory, *, load_plan=None, load_report=None, active=(), cache=None):
    """Rebuild a native SP/MP collection from its complete validated receipts.

    Return ``(files, protected_sha256, reference)``. ``files`` contains only the
    canonical collection documents, not worker runtime settings. ``reference``
    names the native provenance.json and its byte hash. Callbacks read a frozen
    plan dict and a native report respectively; defaults use experiment.load /
    report. This read-only path does not replay any later hierarchy placements.
    MP sources must be direct documents; indirect corpus references fail closed.
    """
    if load_plan is None or load_report is None:
        try:
            from . import experiment
        except ImportError:
            import experiment
        load_plan = load_plan or (lambda path: experiment.load(path)[0])
        load_report = load_report or experiment.report
    directory = Path(directory).resolve()
    if directory in active:
        raise ValueError("native collection reference cycle")
    cache = {} if cache is None else cache
    key = "native_collection", directory
    canonical_names = {"subjects.json", "masked-posts.json", "vector-map.json", "worker-request.json"}
    if key in cache:
        files, protected, reference = cache[key]
        if {name for name in canonical_names if (directory / name).exists()} != set(files):
            raise ValueError("canonical collection files differ")
        for path, expected in protected.items():
            if engine._sha256_file(Path(path)) != expected:
                raise ValueError(f"protected collection source changed: {path}")
        return deepcopy(files), dict(protected), dict(reference)
    protected = {}

    def protect(path, expected=None):
        path = Path(path).resolve()
        if str(path) in protected:
            if expected is not None and protected[str(path)] != expected:
                raise ValueError(f"protected collection source changed: {path}")
            return protected[str(path)]
        measured = engine._sha256_file(path)
        if expected is not None and measured != expected:
            raise ValueError(f"protected collection source changed: {path}")
        protected[str(path)] = measured
        return measured

    provenance_path = directory / "provenance.json"
    reference = dict(path=str(provenance_path), sha256=protect(provenance_path))
    provenance = engine._load_json(provenance_path, "native collection provenance")
    if (type(provenance.get("schema_version")) is not int or provenance["schema_version"] != 1
            or not isinstance(provenance.get("sources"), dict)
            or not isinstance(provenance.get("experiments"), list)
            or not provenance["experiments"] or type(provenance.get("inference_calls")) is not int
            or provenance["inference_calls"] != 0
            or any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
                   for value in provenance["sources"].values())):
        raise ValueError("expected native collection provenance schema_version 1")
    for path, expected in provenance["sources"].items():
        protect(path, expected)
    bundles, adapters, seen = [], set(), set()
    receipt_files = engine.ReceiptFiles()
    for recorded in provenance["experiments"]:
        experiment_dir = Path(recorded["experiment"]).resolve()
        if experiment_dir in seen:
            raise ValueError("duplicate native collection experiment")
        seen.add(experiment_dir)
        protect(experiment_dir / "experiment.json")
        plan = load_plan(experiment_dir)
        adapter = plan["dataset"]["adapter"]
        if adapter not in {"subjects", "masks", "grouped_masks"} or "path" not in plan["dataset"]:
            raise ValueError("native collection requires source-bound SP/MP experiments")
        for path, expected in plan["sources"].items():
            protect(path, expected)
        for name, expected in plan["files"].items():
            protect(experiment_dir / name, expected)
        run_directory = Path(plan["run_directory"]).resolve()
        protect(run_directory / "manifest.json")
        for path in (run_directory / "runner-upgrades.jsonl", experiment_dir / "code-upgrades.jsonl",
                     experiment_dir / "execution-settings.jsonl"):
            if path.exists():
                protect(path)
        if adapter in {"masks", "grouped_masks"}:
            source = Path(plan["dataset"]["path"]).resolve()
            source_value = engine._load_json(source, "mask subjects source")
            if "sources" in source_value:
                raise ValueError("native MP corpus-reference sources are unsupported")
            native_origins = any(note.get("origin", {}).get("receipt")
                                 for note in source_value.get("notes", []))
            if native_origins and source.name != "subjects.json":
                raise ValueError("receipt-bearing SP source requires native subjects.json collection")
            if source.name == "subjects.json":
                if (source.parent / "provenance.json").exists() or native_origins:
                    upstream, upstream_protected, _ = validate_collection(source.parent,
                        load_plan=load_plan, load_report=load_report,
                        active=(*active, directory), cache=cache)
                    if set(upstream) != {"subjects.json"}:
                        raise ValueError("mask source must be a native subjects collection")
                    for path, expected in upstream_protected.items():
                        protect(path, expected)
        result = load_report(experiment_dir)
        if (result.get("experiment") != str(experiment_dir) or result.get("adapter") != adapter
                or result.get("prompt_id") != plan["prompt"]["id"]
                or any(result.get("settings", {}).get(k) != v for k, v in plan["runner"].items())):
            raise ValueError("native collection report identity differs")
        cases = result["cases"]
        if ([case["id"] for case in cases] != [case["id"] for case in plan["cases"]]
                or any(case["status"] not in {"valid", "empty"} or not case.get("receipt")
                       for case in cases)):
            raise ValueError("native collection requires complete valid receipt-bearing cases")
        for frozen, case in zip(plan["cases"], cases, strict=True):
            if any(case.get(k) != frozen.get(k) for k in ("inputs", "evidence")):
                raise ValueError("native collection case differs from frozen source")
            receipt = case["receipt"]
            ledger = Path(receipt["results_path"]).resolve()
            protect(ledger)
            # Native report validates each selected record. Pin its reuse source
            # too, so replay cannot later read changed original native receipts.
            records_key = "collection_receipts", ledger
            if records_key not in cache:
                cache[records_key] = {engine._sha256_bytes(engine._canonical_json_bytes(record)): record.get("reused_from")
                    for record in (json.loads(line) for line in receipt_files.lines(ledger))}
            if receipt["record_sha256"] not in cache[records_key]:
                raise ValueError("native collection receipt record is missing")
            reuse = cache[records_key][receipt["record_sha256"]]
            if reuse is not None:
                original = Path(reuse["results_path"]).resolve()
                protect(original)
                protect(original.parent / "manifest.json")
                original_manifest = receipt_files.json(original.parent / "manifest.json")
                config_path = Path(original_manifest["config_path"])
                if config_path.exists():
                    protect(config_path)
                execution_path = config_path.parent / "execution-settings.jsonl"
                if execution_path.exists():
                    protect(execution_path)
                upgrade_path = original.parent / "runner-upgrades.jsonl"
                if upgrade_path.exists():
                    protect(upgrade_path)
        measured = dict(experiment=str(experiment_dir), prompt_id=plan["prompt"]["id"],
            settings=result["settings"], sources=plan["sources"], cases=[dict(id=case["id"],
            receipt=case["receipt"], reused=case.get("reused", False)) for case in cases])
        if measured != recorded:
            raise ValueError("native collection provenance differs from saved receipts")
        bundles.append(({**plan, "experiment": str(experiment_dir)}, result))
        adapters.add(adapter)
    if adapters == {"subjects"}:
        files = collect_subjects(bundles)
    elif adapters <= {"masks", "grouped_masks"}:
        files = collect_masks(bundles)
        if "worker-request.json" in files:
            files["worker-request.json"]["proposal_sha256"] = engine._sha256_file(directory / "masked-posts.json")
    else:
        raise ValueError("native collection cannot mix SP and MP experiments")
    if {name for name in canonical_names if (directory / name).exists()} != set(files):
        raise ValueError("canonical collection files differ")
    for name, expected in files.items():
        path = directory / name
        protect(path)
        if engine._load_json(path, "canonical collection file") != expected:
            raise ValueError(f"canonical collection file differs from native receipts: {name}")
    for path, expected in protected.items():
        if engine._sha256_file(Path(path)) != expected:
            raise ValueError(f"protected collection source changed: {path}")
    cache[key] = deepcopy(files), dict(protected), dict(reference)
    return files, protected, reference


def validate_subjects(value):
    """Validate SP numbering and fields without judging or repairing meanings."""
    if not isinstance(value, dict) or set(value) != {"subjects"}:
        raise ValueError("expected a subjects array")
    entries = value["subjects"]
    if not isinstance(entries, list):
        raise ValueError("expected a subjects array")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"number", "context", "subject"}:
            raise ValueError("subject entries require number, context and subject")
        number = entry["number"]
        if (not isinstance(number, str) or re.fullmatch(r"[1-9][0-9]*(\.[1-9][0-9]*)*", number) is None
                or number in seen
                or ("." in number and number.rsplit(".", 1)[0] not in seen)):
            raise ValueError("invalid subject numbering: duplicate or missing preceding parent")
        if any(not isinstance(entry[k], str) or not entry[k].strip() for k in ("context", "subject")):
            raise ValueError("subject and context must be nonempty strings")
        seen.add(number)
    return entries


def origin(plan, case):
    return dict(experiment=plan["experiment"], case_id=case["id"],
                prompt_id=case["id"], prompt_version=plan["prompt"]["id"], settings=plan["runner"],
                receipt=case["receipt"], reused=case.get("reused", False))


def source_posts(plan, cache):
    path = Path(plan["dataset"]["path"])
    key = ("posts", path)
    if key in cache:
        protected, notes = cache[key]
        for source_path, measured in protected.items():
            if measured != plan["sources"].get(str(source_path)):
                raise ValueError(f"protected source changed: {source_path}")
        return notes
    protected = {}

    def read_bytes(source_path):
        raw = source_path.read_bytes()
        measured = hashlib.sha256(raw).hexdigest()
        if measured != plan["sources"].get(str(source_path)):
            raise ValueError(f"protected source changed: {source_path}")
        protected[source_path] = measured
        return raw

    def read(source_path):
        json_key = "post_source_json", source_path
        if json_key not in cache:
            value = json.loads(read_bytes(source_path))
            cache[json_key] = protected[source_path], value
        measured, value = cache[json_key]
        if measured != plan["sources"].get(str(source_path)):
            raise ValueError(f"protected source changed: {source_path}")
        protected[source_path] = measured
        return value

    source = corpus_inputs.load(read(path), path.parent, read, read_bytes=read_bytes)
    notes = {n["note_id"]: n for n in source["notes"]}
    cache[key] = protected, notes
    return notes


def collect_subjects(bundles):
    notes, seen, cache = [], set(), {}
    for plan, report in bundles:
        originals = source_posts(plan, cache)
        for case in report["cases"]:
            nid, text = case["evidence"]["note_id"], case["inputs"]["POST"]
            if nid in seen:
                raise ValueError(f"duplicate collected post: {nid}")
            seen.add(nid)
            if originals[nid]["text"] != text:
                raise ValueError("subject post differs from saved source")
            entries = validate_subjects(case["parsed"])
            note = {**originals[nid], "subjects": entries, "origin": origin(plan, case)}
            if originals[nid].get("origin"):
                note["origin"]["source_origin"] = originals[nid]["origin"]
            notes.append(note)
    return {"subjects.json": dict(schema_version=1, notes=notes)}


def collect_masks(bundles):
    """Keep every selected SP entry, including valid empty MP answers."""
    notes, answers, cache, selected_sources = {}, {}, {}, set()
    for plan, report in bundles:
        selected = plan["dataset"].get("select")
        originals = source_posts(plan, cache)
        selection = plan["dataset"]["path"], None if selected is None else frozenset(selected)
        if selection not in selected_sources:
            selected_sources.add(selection)
            selected_ids = None if selected is None else set(selected)
            for nid, post in originals.items():
                if selected_ids is not None and nid not in selected_ids:
                    continue
                if nid in notes and notes[nid] != post:
                    raise ValueError(f"conflicting collected post: {nid}")
                notes[nid] = post
        for case in report["cases"]:
            nid = case["evidence"]["note_id"]
            if nid not in notes or case["inputs"]["POST"] != notes[nid]["text"]:
                raise ValueError("mask post differs from saved subject source")
            if plan["dataset"]["adapter"] == "grouped_masks":
                rows = [(i, row) for i, row in enumerate(case["mask_results"])]
            else:
                if plan["dataset"].get("mask_format", "word_positions") != "word_positions":
                    raise ValueError("mask collection requires unambiguous word_positions")
                rows = [(case["evidence"]["subject_index"], case)]
            for index, row in rows:
                key = nid, index
                if key in answers:
                    raise ValueError("duplicate collected subject mask")
                entry = notes[nid]["subjects"][index]
                subject = entry.get("subject", entry.get("text")) if isinstance(entry, dict) else entry
                supplied = row["subject"] if plan["dataset"]["adapter"] == "grouped_masks" else case["inputs"]["SUBJECT"]
                if supplied != subject:
                    raise ValueError("mask subject differs from saved source")
                answers[key] = dict(status="valid", ranges=row["ranges"],
                                    diagnostics=row["diagnostics"], origin=origin(plan, case))
    source, checks = dict(notes=[]), []
    for nid, post in notes.items():
        entries = []
        for index, entry in enumerate(post["subjects"]):
            if (nid, index) not in answers:
                raise ValueError(f"missing subject mask: {nid}/{index}")
            entry = dict(entry) if isinstance(entry, dict) else dict(subject=entry)
            if "subject" not in entry:
                entry["subject"] = entry.pop("text")
            entries.append(entry)
            checks.append(dict(answers[nid, index], item_id=f"M{len(checks) + 1:03}"))
        if any("number" in e for e in entries):
            validate_subjects(dict(subjects=[{k: e.get(k) for k in ("number", "context", "subject")}
                                            for e in entries]))
        source["notes"].append({**post, "subjects": entries})
    request, mapping, preserved = encode_inputs(source, checks)
    for original, post in zip(source["notes"], preserved["notes"], strict=True):
        post.update({k: v for k, v in original.items() if k != "subjects"})
    files = {"masked-posts.json": preserved, "vector-map.json": mapping}
    if request:
        files["worker-request.json"] = dict(schema_version=1, notes=request)
    return files


def encode_inputs(source, checks):
    """Preserve every heading; only exact nonempty masks enter the encoder."""
    checks = {c["item_id"]: c for c in checks}
    request, vectors, notes, preserved = [], [], [], []
    counter = 0
    for index, post in enumerate(source["notes"], 1):
        short = f"N{index:03}"
        notes.append({"note_id": post["note_id"], "short_id": short})
        distinct, entries = {}, []
        for entry in post["subjects"]:
            counter += 1
            check = checks[f"M{counter:03}"]
            if check["status"] != "valid":
                raise ValueError(f"invalid mask M{counter:03}; never repair or silently omit")
            ranges = check["ranges"]
            text = post["text"]
            spans = [[len(text[:r["start"]].encode()), len(text[:r["end"]].encode())] for r in ranges]
            fragments = [text[r["start"]:r["end"]] for r in ranges]
            record = {**entry, "id": f"M{counter:03}", "byte_spans": spans, "fragments": fragments,
                      "semantic_status": "generated, not independently approved", "diagnostics": check.get("diagnostics")}
            if "origin" in check:
                record["origin"] = check["origin"]
            entries.append(record)
            if not spans:
                continue
            key = tuple(map(tuple, spans))
            if key not in distinct:
                identifier = hashlib.sha256(json.dumps([post["note_id"], text, spans], ensure_ascii=False).encode()).hexdigest()
                row = {"vector_id": identifier, "worker_subject_id": identifier[:16],
                       "note_id": post["note_id"], "note_short_id": short, "byte_spans": spans,
                       "fragments": fragments, "subject_entries": [], "short_id": f"V{len(vectors)+1:04}"}
                distinct[key] = row
                vectors.append(row)
            distinct[key]["subject_entries"].append(record)
        preserved.append({"note_id": post["note_id"], "text": post["text"], "subjects": entries})
        if distinct:
            request.append({"note_id": post["note_id"], "text": post["text"], "subjects": [
                {"subject_id": row["worker_subject_id"], "byte_spans": row["byte_spans"]} for row in distinct.values()]})
    if counter != len(checks):
        raise ValueError("mask count does not match subject entries")
    return request, {"schema_version": 1, "notes": notes, "vectors": vectors, "vector_count": len(vectors)}, {"schema_version": 1, "notes": preserved}
