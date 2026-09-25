"""Prepare one fine-tuning dataset containing subject and mask tasks.

No inference, label repair, or semantic approval happens here. Generated files
belong under target/; keep the original subject annotations for diagnosis.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from sse_multivector.extraction_pipeline import prepare_mask_inputs
from sse_multivector.mask_positions import decode


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selections(text, spans, fragments):
    """Express saved UTF-8 spans in the existing word-position mask format."""
    if len(spans) != len(fragments):
        raise ValueError("span/fragment count differs")
    encoded = text.encode("utf-8")
    words = list(re.finditer(r"\S+", text))
    result, previous = [], 0
    expected = []
    for span, fragment in zip(spans, fragments):
        if (not isinstance(span, list) or len(span) != 2
                or any(type(x) is not int for x in span)):
            raise ValueError("invalid byte span")
        start, end = span
        if not previous <= start < end <= len(encoded):
            raise ValueError("unordered, overlapping or out-of-bounds span")
        if encoded[start:end].decode("utf-8") != fragment:
            raise ValueError("fragment differs from source")
        a = len(encoded[:start].decode("utf-8"))
        b = len(encoded[:end].decode("utf-8"))
        expected.extend(i for i in range(a, b) if not text[i].isspace())
        for position, word in enumerate(words, 1):
            lo, hi = max(a, word.start()), min(b, word.end())
            if lo >= hi:
                continue
            if lo == word.start() and hi == word.end():
                if result and isinstance(result[-1], list) and result[-1][1] == position - 1:
                    result[-1][1] = position
                else:
                    result.append([position, position])
            else:
                result.append({"word": position, "text": text[lo:hi]})
        previous = end
    # Use the production decoder, including partial-word ambiguity checks.
    _, decoded = decode(json.dumps({"meaning": "saved reference", "evidence": "saved spans",
                                   "expressible": bool(spans), "mask": result}), text)
    actual = [i for r in decoded for i in range(r["start"], r["end"])
              if not text[i].isspace()]
    if actual != expected:
        raise ValueError("word-position conversion changed the selected source text")
    return result


def prepare(source_path, annotations_path, subject_prompt_path, mask_prompt_path,
            subject_prompt_id, mask_prompt_id, evaluation_notes, seed, output):
    if output.exists():
        raise FileExistsError(output)
    source = json.loads(source_path.read_text())["notes"]
    annotations = json.loads(annotations_path.read_text())["notes"]
    def by_id(notes):
        result = {n["note_id"]: n for n in notes}
        if len(result) != len(notes):
            raise ValueError("duplicate note IDs")
        return result
    originals, labels = by_id(source), by_id(annotations)
    if originals.keys() != labels.keys():
        raise ValueError("source and annotation note sets differ")
    if not 0 < evaluation_notes < len(source):
        raise ValueError("evaluation count must leave both training and evaluation notes")
    subject_instruction = subject_prompt_path.read_text().rstrip()
    mask_instruction = mask_prompt_path.read_text()
    if not subject_instruction or not subject_prompt_id.strip() or not mask_prompt_id.strip():
        raise ValueError("instructions and prompt IDs must be nonempty")
    items, prompts = prepare_mask_inputs({"schema_version": 1, "notes": annotations}, mask_instruction)
    mask_prompts = {note_id: [] for note_id in originals}
    for item, prompt in zip(items, prompts):
        mask_prompts[item["note_id"]].append(prompt.text)

    # Connected groups keep same-author and identical-content notes together,
    # including copies of the same post by different authors.
    groups, author_groups, text_groups = {}, {}, {}
    for note in source:
        author = note.get("pubkey")
        if not isinstance(author, str) or not author:
            raise ValueError("every note requires an author for splitting")
        content = " ".join(note["text"].split())
        matches = {g for g in [author_groups.get(author), text_groups.get(content)] if g is not None}
        group = min(matches) if matches else note["note_id"]
        groups.setdefault(group, set()).add(note["note_id"])
        for other in matches - {group}:
            groups[group].update(groups.pop(other))
            for mapping in (author_groups, text_groups):
                for key in mapping:
                    if mapping[key] == other:
                        mapping[key] = group
        author_groups[author] = text_groups[content] = group
    ordered = sorted(groups.values(), key=lambda ids: hashlib.sha256(
        (seed + "\n" + "\n".join(sorted(ids))).encode()).hexdigest())
    # Find an exact-size whole-group split without dropping any notes.
    choices = {0: set()}
    for group in ordered:
        for count, ids in list(choices.items()):
            new_count = count + len(group)
            if new_count <= evaluation_notes and new_count not in choices:
                choices[new_count] = ids | group
    if evaluation_notes not in choices:
        raise ValueError("requested evaluation size would split an author/content group")
    held_out = choices[evaluation_notes]
    train, evaluation, references = [], [], []
    empty_count = subject_count = 0
    for note_id in sorted(originals):
        original, note = originals[note_id], labels[note_id]
        if original["text"] != note["text"]:
            raise ValueError("annotation source text differs")
        subject_target = {"subjects": [
            {key: entry[key] for key in ("number", "context", "subject")}
            for entry in note["subjects"]]}
        messages = [{"role": "user", "content": subject_instruction
                     + "\n\n<post>\n" + note["text"] + "\n</post>"}]
        examples = [{"note_id": note_id, "task": "subjects", "prompt": messages,
                     "completion": [{"role": "assistant", "content": json.dumps(subject_target, ensure_ascii=False)}]}]
        for subject, content in zip(note["subjects"], mask_prompts[note_id]):
            subject_count += 1
            mask = selections(note["text"], subject["byte_spans"], subject["fragments"])
            if not mask:
                empty_count += 1
            # Keep the existing response contract, including empty verdicts.
            # Only the representation of equivalent source selections is canonicalized.
            target = json.dumps({**{key: subject["diagnostics"][key]
                                    for key in ("meaning", "expressible", "evidence")},
                                 "mask": mask}, ensure_ascii=False)
            decode(target, note["text"])
            examples.append({"note_id": note_id, "task": "mask", "subject_id": subject["id"],
                             "prompt": [{"role": "user", "content": content}],
                             "completion": [{"role": "assistant", "content": target}]})
        if note_id in held_out:
            # End-to-end evaluation begins with subjects. Its mask inputs must
            # be constructed from the candidate's answers, not teacher subjects.
            evaluation.append({"note_id": note_id, "messages": messages})
        else:
            train.extend(examples)
        references.append({**note, "split": "evaluation" if note_id in held_out else "train"})
    manifest = {
        "schema_version": 2, "seed": seed,
        "tasks": {"subjects": subject_prompt_id, "mask": mask_prompt_id},
        "inputs": {str(p.resolve()): digest(p) for p in
                   [source_path, annotations_path, subject_prompt_path, mask_prompt_path]},
        "train_note_ids": sorted(originals.keys() - held_out),
        "evaluation_note_ids": [n["note_id"] for n in evaluation],
        "subject_entries": subject_count, "empty_subject_masks": empty_count,
        "training_examples": {task: sum(r["task"] == task for r in train) for task in ["subjects", "mask"]},
        "semantic_status": "Saved teacher outputs; no new semantic review or approval.",
    }
    output.mkdir(parents=True)
    for name, rows in [("train", train), ("evaluation", evaluation), ("references", references)]:
        (output / (name + ".jsonl")).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    manifest["outputs"] = {name: digest(output / name) for name in ["train.jsonl", "evaluation.jsonl", "references.jsonl"]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["source", "annotations", "subject-prompt", "mask-prompt", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--subject-prompt-id", required=True)
    parser.add_argument("--mask-prompt-id", required=True)
    parser.add_argument("--evaluation-notes", type=int, required=True)
    parser.add_argument("--seed", required=True)
    args = parser.parse_args()
    manifest = prepare(args.source, args.annotations, args.subject_prompt, args.mask_prompt,
                       args.subject_prompt_id, args.mask_prompt_id,
                       args.evaluation_notes, args.seed, args.output)
    print(json.dumps({"train_notes": len(manifest["train_note_ids"]),
                      "evaluation_notes": len(manifest["evaluation_note_ids"]),
                      "training_examples": manifest["training_examples"]}))


if __name__ == "__main__":
    main()
