"""Audit selected TRAIN/validation inputs and SP training answers.

This inventories possible SHR inputs; it does not infer SHR relation labels.
Run with --registry inputs.json --prepared prepared/ --output target/.../audit.json.
The selected registry's adjacent manifest binds its bytes. Mixed source files,
final-test content and validation references are never followed or opened.
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


def audit(registry, prepared):
    registry, prepared = Path(registry).resolve(), Path(prepared).resolve()
    manifest_path = prepared / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest["schema_version"] != 2 or set(manifest["tasks"]) != {"subjects"}:
        raise ValueError("expected prepared subject-only schema 2")
    registry_manifest_path = registry.parent / "manifest.json"
    registry_manifest = read_json(registry_manifest_path)
    hashes = {str(registry): sha256(registry), str(manifest_path): sha256(manifest_path),
              str(registry_manifest_path): sha256(registry_manifest_path)}
    if (registry_manifest["schema_version"] != 1
            or registry_manifest["files"].get(registry.name) != hashes[str(registry)]):
        raise ValueError("selected registry hash mismatch")
    saved_registry = read_json(registry)
    if saved_registry["schema_version"] != 1 or not isinstance(saved_registry.get("posts"), list):
        raise ValueError("expected selected post registry schema 1")
    posts = {n["note_id"]: n for n in saved_registry["posts"]}
    split_ids = {name: manifest[key] for name, key in (
        ("train", "train_note_ids"), ("validation", "evaluation_note_ids"), ("test", "test_note_ids"))}
    order = [nid for ids in split_ids.values() for nid in ids]
    if (any(not ids for ids in split_ids.values()) or len(set(order)) != len(order)
            or len(posts) != len(saved_registry["posts"])
            or set(split_ids["train"] + split_ids["validation"]) != set(posts)):
        raise ValueError("frozen splits overlap, are empty or differ from the selected registry")
    assignments = {nid: name for name, ids in split_ids.items() for nid in ids}
    if any(n["split"] != assignments[nid] for nid, n in posts.items()):
        raise ValueError("registry split differs from frozen membership")

    rows, notes = {}, {}
    for split, filename in (("train", "train.jsonl"), ("validation", "evaluation.jsonl")):
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
            delimiter, ending = "\n\n<post>\n", "\n</post>"
            if not isinstance(content, str) or not content.endswith(ending):
                raise ValueError("saved prompt differs from full instruction and source note")
            boundary = next((m.start() for m in re.finditer(re.escape(delimiter), content)
                             if hashlib.sha256(content[:m.start()].encode()).hexdigest()
                             == manifest["subject_instruction_sha256"]), None)
            if boundary is None:
                raise ValueError("saved prompt differs from full instruction and source note")
            text = content[boundary + len(delimiter):-len(ending)]
            post = posts[row["note_id"]]
            if hashlib.sha256(text.encode()).hexdigest() != post["text_sha256"]:
                raise ValueError("saved prompt differs from full instruction and source note")
            notes[row["note_id"]] = {"note_id": row["note_id"], "text": text, "pubkey": post["pubkey"]}

    prepare_posts({"schema_version": 1, "notes": list(notes.values())})
    authors, copies = defaultdict(set), defaultdict(list)
    for nid, note in notes.items():
        author = note.get("pubkey")
        if not isinstance(author, str) or not author:
            raise ValueError("every selected note requires an author")
        authors[author].add(assignments[nid])
        copies[" ".join(note["text"].split())].append(nid)
    if any(len(splits) != 1 for splits in authors.values()):
        raise ValueError("author crosses frozen splits")
    if any(len({assignments[nid] for nid in ids}) != 1 for ids in copies.values()):
        raise ValueError("identical content crosses frozen splits")

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
    split_stats = {name: {"notes": len(ids), "content_opened": True,
                          "authors": len({notes[i]["pubkey"] for i in ids}),
                          "post_characters": distribution([len(notes[i]["text"]) for i in ids])}
                   for name, ids in split_ids.items() if name != "test"}
    split_stats["test"] = {"notes": len(split_ids["test"]), "content_opened": False}
    return {"schema_version": 2, "hashes": hashes, "tasks": manifest["tasks"],
            "reserved_final_test_content_opened": False, "reserved_final_test_answers_opened": False,
            "validation_references_opened": False, "shr_relation_labels": 0,
            "registry_contains_validation_sp_entries": any(
                e["split"] == "validation" for e in saved_registry.get("subjects", [])),
            "comparison_splits": ["train", "validation"],
            "splits": split_stats,
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
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_json(args.output, audit(args.registry, args.prepared))


if __name__ == "__main__":
    main()
