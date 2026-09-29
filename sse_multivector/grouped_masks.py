"""Prepare one post's fixed subjects and validate independently decoded masks."""
import json

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


def saved_mask(subject, text):
    """Validate optional saved byte spans before using them as a comparison."""
    if not isinstance(subject, dict) or "byte_spans" not in subject:
        return None
    spans = subject["byte_spans"]
    if not isinstance(spans, list):
        raise ValueError("saved mask byte_spans must be an array")
    raw, fragments, previous = text.encode("utf-8"), [], 0
    for span in spans:
        if (not isinstance(span, list) or len(span) != 2
                or any(type(p) is not int for p in span)
                or not previous <= span[0] < span[1] <= len(raw)):
            raise ValueError("invalid saved mask byte spans")
        # Decode both the prefix and selection to verify UTF-8 boundaries.
        raw[:span[0]].decode("utf-8")
        fragments.append(raw[span[0]:span[1]].decode("utf-8"))
        previous = span[1]
    if "fragments" in subject and subject["fragments"] != fragments:
        raise ValueError("saved mask fragments differ from byte spans")
    return {"byte_spans": spans, "fragments": fragments,
            "diagnostics": subject.get("diagnostics")}


def prepare(source, selected=None):
    """Use the masks source schema; never send context or saved selections."""
    notes = source.get("notes")
    if (type(source.get("schema_version")) is not int or source["schema_version"] != 1
            or not isinstance(notes, list) or not notes):
        raise ValueError("input must contain schema_version 1 and nonempty notes")
    cases, seen = [], set()
    for note in notes:
        engine._expect_object(note, "note")
        nid = engine._expect_string(note.get("note_id"), "note_id")
        if nid in seen:
            raise ValueError("duplicate note_id")
        seen.add(nid)
        if selected is not None and nid not in selected:
            continue
        text = engine._expect_string(note.get("text"), "note text")
        subjects = note.get("subjects")
        if not isinstance(subjects, list) or not subjects:
            raise ValueError("each selected note must have nonempty subjects")
        entries, evidence = [], []
        for i, subject in enumerate(subjects, 1):
            name = subject
            if isinstance(subject, dict):
                if "subject" in subject and "text" in subject:
                    raise ValueError("subject entry must use subject or text, not both")
                name = subject.get("subject", subject.get("text"))
            engine._expect_string(name, "subject")
            if not name.strip():
                raise ValueError("subject must not be blank")
            entry = {"id": f"S{i}", "subject": name}
            entries.append(entry)
            evidence.append({**entry, "source": subject, "baseline": saved_mask(subject, text)})
        cases.append({"id": nid, "inputs": {
            "POST": text, "INDEXED_POST": engine._position_decoder().index_post(text),
            "SUBJECTS": json.dumps(entries, ensure_ascii=False, separators=(",", ":")),
        }, "evidence": {"note_id": nid, "text": text, "subjects": evidence}})
    if selected is not None and set(selected) - seen:
        raise ValueError("unknown note requested")
    return cases


def validate(case, raw):
    """Require complete ordered IDs; overlaps across subjects remain legitimate."""
    decoder = engine._position_decoder()
    value = json.loads(raw, object_pairs_hook=decoder.unique_object)
    if not isinstance(value, dict) or set(value) != {"results"}:
        raise ValueError("expected a results array")
    results = value["results"]
    subjects = case["evidence"]["subjects"]
    if not isinstance(results, list) or len(results) != len(subjects):
        raise ValueError("expected exactly one result per supplied subject")
    text, masks = case["inputs"]["POST"], []
    for result, subject in zip(results, subjects):
        if not isinstance(result, dict) or result.get("id") != subject["id"]:
            raise ValueError("result IDs must match supplied IDs in input order")
        response = {k: v for k, v in result.items() if k != "id"}
        encoded = json.dumps(response, ensure_ascii=False)
        diagnostics, ranges = decoder.decode(encoded, text)
        fragments, _, _ = engine._map_mask_fragments(encoded, text, "word_positions")
        spans = [[len(text[:r["start"]].encode("utf-8")),
                  len(text[:r["end"]].encode("utf-8"))] for r in ranges]
        baseline = subject["baseline"]
        masks.append({"id": subject["id"], "subject": subject["subject"],
            "status": "valid" if fragments else "empty", "fragments": fragments,
            "byte_spans": spans, "ranges": ranges,
            "diagnostics": {k: v for k, v in diagnostics.items() if k != "mask"},
            "baseline": baseline,
            "matches_baseline": None if baseline is None else spans == baseline["byte_spans"]})
    return {"parsed": value, "mask_results": masks}
