"""Lossless offline collection of source-bound SP/MP inputs for SSE."""
import hashlib
import json
import re
from pathlib import Path

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


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
    expected = plan["sources"].get(str(path))
    if path not in cache:
        raw = path.read_bytes()
        cache[path] = hashlib.sha256(raw).hexdigest(), {
            n["note_id"]: n for n in json.loads(raw)["notes"]}
    measured, notes = cache[path]
    if measured != expected:
        raise ValueError(f"protected source changed: {path}")
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
