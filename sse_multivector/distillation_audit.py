"""Audit frozen SP inputs and training answers without opening held-out answers.

This inventories possible SHR inputs; it does not infer SHR relation labels.
Run with --source notes.json --prepared prepared/ --output target/.../audit.json.
"""
import argparse
import hashlib
import itertools
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from sse_multivector.distillation_run import parse_subjects, read_json, sha256, write_json
from sse_multivector.experiment_inputs import prepare_posts


def distribution(values):
    values = sorted(values)
    if not values:
        return {"count": 0}
    return {"count": len(values), "min": values[0], "median": values[len(values) // 2],
            "p95": values[math.ceil(len(values) * .95) - 1], "max": values[-1]}


def near_copies(notes, assignments):
    """Nominate with rare word shingles; never enumerate every corpus pair."""
    index, shingles = defaultdict(list), {}
    for nid, note in notes.items():
        words = re.findall(r"\w+", note["text"].casefold())
        shingles[nid] = {tuple(words[i:i + 5]) for i in range(len(words) - 4)}
        for shingle in shingles[nid]:
            index[shingle].append(nid)
    candidates = set()
    skipped = 0
    for ids in index.values():
        if len(ids) > 50:
            skipped += 1
            continue
        candidates.update(itertools.combinations(sorted(ids), 2))
    matches = []
    for a, b in sorted(candidates):
        union = shingles[a] | shingles[b]
        similarity = len(shingles[a] & shingles[b]) / len(union)
        if similarity >= .8:
            matches.append({"note_ids": [a, b], "splits": [assignments[a], assignments[b]],
                            "jaccard": similarity})
    return {"method": "casefolded word 5-shingles, Jaccard >= 0.8, posting cap 50",
            "candidate_pairs": len(candidates), "skipped_common_shingles": skipped,
            "matches": matches, "exhaustive": False}


def audit(source, prepared):
    source, prepared = Path(source).resolve(), Path(prepared).resolve()
    manifest_path = prepared / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest["schema_version"] != 2 or set(manifest["tasks"]) != {"subjects"}:
        raise ValueError("expected prepared subject-only schema 2")
    hashes = {str(source): sha256(source), str(manifest_path): sha256(manifest_path)}
    if manifest["inputs"].get(str(source)) != hashes[str(source)]:
        raise ValueError("source hash mismatch or source path differs")
    saved_source = read_json(source)
    prepare_posts(saved_source)  # Shared production post validation.
    notes = {n["note_id"]: n for n in saved_source["notes"]}
    split_ids = {name: manifest[key] for name, key in (
        ("train", "train_note_ids"), ("validation", "evaluation_note_ids"), ("test", "test_note_ids"))}
    order = [nid for ids in split_ids.values() for nid in ids]
    if (any(not ids for ids in split_ids.values()) or len(set(order)) != len(order)
            or set(order) != set(notes)):
        raise ValueError("frozen splits overlap, are empty or differ from the source")
    assignments = {nid: name for name, ids in split_ids.items() for nid in ids}
    authors, copies = defaultdict(set), defaultdict(list)
    for nid, note in notes.items():
        author = note.get("pubkey")
        if not isinstance(author, str) or not author:
            raise ValueError("every source note requires an author")
        authors[author].add(assignments[nid])
        copies[" ".join(note["text"].split())].append(nid)
    if any(len(splits) != 1 for splits in authors.values()):
        raise ValueError("author crosses frozen splits")
    if any(len({assignments[nid] for nid in ids}) != 1 for ids in copies.values()):
        raise ValueError("identical content crosses frozen splits")

    rows = {}
    for split, filename in (("train", "train.jsonl"), ("validation", "evaluation.jsonl"), ("test", "test.jsonl")):
        path = prepared / filename
        digest = sha256(path)
        if manifest["outputs"][filename] != digest:
            raise ValueError(f"hash mismatch: {filename}")
        hashes[str(path)] = digest
        rows[split] = [json.loads(line) for line in path.read_text().splitlines()]
        if [row["note_id"] for row in rows[split]] != split_ids[split]:
            raise ValueError(f"{split} row order differs from frozen membership")
        for row in rows[split]:
            if split != "train" and set(row) != {"note_id", "messages"}:
                raise ValueError("held-out data must be input-only")
            messages = row["prompt"] if split == "train" else row["messages"]
            if (not isinstance(messages, list) or len(messages) != 1
                    or set(messages[0]) != {"role", "content"} or messages[0]["role"] != "user"):
                raise ValueError("expected one complete user prompt")
            content = messages[0]["content"]
            suffix = "\n\n<post>\n" + notes[row["note_id"]]["text"] + "\n</post>"
            if not content.endswith(suffix) or hashlib.sha256(content[:-len(suffix)].encode()).hexdigest() != manifest["subject_instruction_sha256"]:
                raise ValueError("saved prompt differs from full instruction and source note")

    entries, per_note, subject_groups, exact_groups = [], [], defaultdict(set), defaultdict(set)
    parent_candidates = 0
    for row in rows["train"]:
        if row["task"] != "subjects" or len(row["completion"]) != 1 or row["completion"][0]["role"] != "assistant":
            raise ValueError("expected one complete subject training answer")
        subjects = parse_subjects(row["completion"][0]["content"])
        per_note.append(len(subjects))
        for subject in subjects:
            entries.append(subject)
            parent_candidates += "." in subject["number"]
            subject_groups[subject["subject"].casefold()].add(row["note_id"])
            exact_groups[(subject["subject"], subject["context"])].add(row["note_id"])
    return {"schema_version": 1, "hashes": hashes, "tasks": manifest["tasks"],
            "held_out_answers_opened": False, "shr_relation_labels": 0,
            "splits": {name: {"notes": len(ids), "authors": len({notes[i]["pubkey"] for i in ids}),
                                "post_characters": distribution([len(notes[i]["text"]) for i in ids])}
                       for name, ids in split_ids.items()},
            "author_overlap": 0, "exact_content_duplicate_groups": [ids for ids in copies.values() if len(ids) > 1],
            "near_copies": near_copies(notes, assignments),
            "training_subjects": {"entries": len(entries), "per_note": distribution(per_note),
                "subject_characters": distribution([len(e["subject"]) for e in entries]),
                "context_characters": distribution([len(e["context"]) for e in entries]),
                "entry_json_characters": distribution([len(json.dumps({k: e[k] for k in ("subject", "context")}, ensure_ascii=False)) for e in entries]),
                "parent_child_candidates": parent_candidates,
                "same_subject_cross_note_groups": sum(len(ids) > 1 for ids in subject_groups.values()),
                "identical_subject_context_cross_note_groups": sum(len(ids) > 1 for ids in exact_groups.values())},
            "semantic_status": "SP training answers only; candidate counts are not SHR gold labels."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_json(args.output, audit(args.source, args.prepared))


if __name__ == "__main__":
    main()
