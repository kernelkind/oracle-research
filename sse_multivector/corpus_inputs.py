"""Load ordered saved post corpora without changing source fields or identities."""
import json

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


def load(source, base, read, *, read_bytes=None):
    """Gather references through protected readers, preserving original posts.

    A string reference names a complete notes document. An object reference
    supplies path, format (posts or jsonl), and an optional case-ID selection.
    Nested reference lists are deliberately unsupported. The byte reader is
    required for JSONL so callers can protect its exact source bytes too.
    """
    if "sources" not in source:
        return source
    engine._expect_fields(source, "post sources", {"schema_version", "sources"})
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("expected post sources schema_version 1")
    if not isinstance(source["sources"], list) or not source["sources"]:
        raise ValueError("post sources require a nonempty sources array")
    notes, paths, note_ids, identifiers = [], set(), set(), set()
    for reference in source["sources"]:
        if isinstance(reference, str):
            reference = dict(path=reference, format="posts")
        if not isinstance(reference, dict):
            raise ValueError("post source must be a path string or an object")
        engine._expect_fields(reference, "post source", {"path", "format"}
                              | ({"select"} & reference.keys()))
        path = engine._resolve_path(reference["path"], "post source", base)
        if path in paths:
            raise ValueError("duplicate post source path")
        paths.add(path)
        selected = reference.get("select")
        if selected is not None:
            engine._validate_string_array(selected, "post source selection", allow_empty=False)
            if len(set(selected)) != len(selected):
                raise ValueError("duplicate post source selection")
        if reference["format"] == "posts":
            corpus = read(path)
        elif reference["format"] == "jsonl":
            if read_bytes is None:
                raise ValueError("JSONL post sources require a protected byte reader")
            corpus = dict(schema_version=1, notes=[])
            for row_number, line in enumerate(read_bytes(path).splitlines(), 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("post JSONL row must be an object")
                origin = dict(source_path=str(path), source_row=row_number,
                              **{k: row[k] for k in ("pubkey", "split") if k in row})
                if "origin" in row:
                    origin["source_origin"] = row["origin"]
                corpus["notes"].append({
                    **{k: value for k, value in row.items() if k not in {"content", "origin"}},
                    "note_id": row["note_id"], "text": row["content"],
                    "origin": origin})
        else:
            raise ValueError("post source format must be posts or jsonl")
        if (type(corpus.get("schema_version")) is not int or corpus["schema_version"] != 1
                or not isinstance(corpus.get("notes"), list) or "sources" in corpus):
            raise ValueError("corpus source requires schema_version 1 and a notes array")
        gathered, source_ids, source_identifiers = [], set(), set()
        for note in corpus["notes"]:
            note_id = engine._expect_string(note["note_id"], "note_id")
            engine._expect_string(note["text"], "post text")
            origin = note.get("origin", {})
            if not isinstance(origin, dict):
                raise ValueError("post origin must be an object")
            identifier = engine._expect_identifier(origin.get("prompt_id", note_id), "post identity")
            if note_id in source_ids or identifier in source_identifiers:
                raise ValueError("duplicate post identity")
            source_ids.add(note_id)
            source_identifiers.add(identifier)
            if selected is None or identifier in selected:
                gathered.append((note_id, identifier, note))
        if selected is not None and set(selected) - source_identifiers:
            raise ValueError("unknown post requested")
        for note_id, identifier, note in gathered:
            if note_id in note_ids or identifier in identifiers:
                raise ValueError("duplicate post identity")
            note_ids.add(note_id)
            identifiers.add(identifier)
            notes.append(note)
    return dict(schema_version=1, notes=notes)
