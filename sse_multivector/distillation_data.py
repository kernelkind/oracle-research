"""Prepare subject-hierarchy training data, optionally including mask tasks.

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
            subject_prompt_id, mask_prompt_id, evaluation_notes, seed, output,
            tasks=("subjects", "mask"), splits_path=None):
    tasks = tuple(tasks)
    if tasks not in (("subjects",), ("subjects", "mask")):
        raise ValueError("expected subjects or subjects and masks")
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
    if (not subject_instruction or not subject_prompt_id.strip()
            or "mask" in tasks and (mask_prompt_path is None or not (mask_prompt_id or "").strip())):
        raise ValueError("instructions and prompt IDs must be nonempty")
    items, prompts = [], []
    if "mask" in tasks:
        items, prompts = prepare_mask_inputs({"schema_version": 1, "notes": annotations}, mask_prompt_path.read_text())
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
    if splits_path is not None:
        split_files = ([splits_path / (name + ".json") for name in ("train", "validation", "test")]
                       if splits_path.is_dir() else [splits_path])
        if splits_path.is_dir():
            splits = {}
            for name, path in zip(("train", "validation", "test"), split_files):
                definition = json.loads(path.read_text())
                sources = definition["sources"]
                if (definition["schema_version"] != 1 or len(sources) != 1
                        or sources[0]["format"] != "posts"
                        or Path(sources[0]["path"]).resolve() != source_path.resolve()):
                    raise ValueError("frozen split does not select the supplied source")
                splits[name] = sources[0]["select"]
        else:
            splits = json.loads(splits_path.read_text())
        if (not isinstance(splits, dict) or set(splits) != {"train", "validation", "test"}
                or any(not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids)
                       for ids in splits.values())):
            raise ValueError("expected nonempty train/validation/test note ID lists")
        order = [i for ids in splits.values() for i in ids]
        if len(order) != len(set(order)) or set(order) != originals.keys() or len(splits["validation"]) != evaluation_notes:
            raise ValueError("frozen splits differ from source note set or evaluation count")
        assignments = {i: name for name, ids in splits.items() for i in ids}
        if any(len({assignments[i] for i in group}) != 1 for group in groups.values()):
            raise ValueError("frozen split crosses an author/content group")
        held_out, reserved = set(splits["validation"]), set(splits["test"])
    else:
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
        held_out, reserved, order = choices[evaluation_notes], set(), sorted(originals)
    train, evaluation, test, references = [], [], [], []
    empty_count = subject_count = 0
    for note_id in order:
        original, note = originals[note_id], labels[note_id]
        if original["text"] != note["text"]:
            raise ValueError("annotation source text differs")
        subject_target = {"subjects": [
            {key: entry[key] for key in ("number", "context", "subject")}
            for entry in note["subjects"]]}
        subject_count += len(note["subjects"])
        if "mask" not in tasks:
            from sse_multivector.distillation_run import parse_subjects
            parse_subjects(json.dumps(subject_target, ensure_ascii=False))
        messages = [{"role": "user", "content": subject_instruction
                     + "\n\n<post>\n" + note["text"] + "\n</post>"}]
        examples = [{"note_id": note_id, "task": "subjects", "prompt": messages,
                     "completion": [{"role": "assistant", "content": json.dumps(subject_target, ensure_ascii=False)}]}]
        for subject, content in zip(note["subjects"], mask_prompts[note_id]):
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
        if note_id in held_out or note_id in reserved:
            # End-to-end evaluation begins with subjects. Its mask inputs must
            # be constructed from the candidate's answers, not teacher subjects.
            (test if note_id in reserved else evaluation).append({"note_id": note_id, "messages": messages})
        else:
            train.extend(examples)
        references.append({**note, "pubkey": original["pubkey"],
                           "split": "test" if note_id in reserved else "evaluation" if note_id in held_out else "train"})
    manifest = {
        "schema_version": 2, "seed": seed,
        "tasks": {"subjects": subject_prompt_id, **({"mask": mask_prompt_id} if "mask" in tasks else {})},
        "inputs": {str(p.resolve()): digest(p) for p in
                   [source_path, annotations_path, subject_prompt_path] + ([mask_prompt_path] if "mask" in tasks else [])
                   + (split_files if splits_path is not None else [])},
        "subject_instruction_sha256": hashlib.sha256(subject_instruction.encode()).hexdigest(),
        "train_note_ids": [i for i in order if i not in held_out | reserved],
        "evaluation_note_ids": [n["note_id"] for n in evaluation],
        "subject_entries": subject_count, "empty_subject_masks": empty_count,
        "training_examples": {task: sum(r["task"] == task for r in train) for task in tasks},
        "semantic_status": "Saved teacher outputs; no new semantic review or approval.",
    }
    output.mkdir(parents=True)
    if splits_path is not None:
        manifest["test_note_ids"] = [n["note_id"] for n in test]
    outputs = [("train", train), ("evaluation", evaluation), ("references", references)]
    if splits_path is not None:
        outputs.append(("test", test))
    for name, rows in outputs:
        (output / (name + ".jsonl")).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    manifest["outputs"] = {name + ".jsonl": digest(output / (name + ".jsonl")) for name, _ in outputs}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["source", "annotations", "subject-prompt", "output"]:
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--mask-prompt", type=Path)
    parser.add_argument("--subject-prompt-id", required=True)
    parser.add_argument("--mask-prompt-id")
    parser.add_argument("--tasks", nargs="+", choices=("subjects", "mask"), default=("subjects", "mask"))
    parser.add_argument("--evaluation-notes", type=int, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--splits", type=Path, help="frozen ID lists or directory of train/validation/test source selections")
    args = parser.parse_args()
    manifest = prepare(args.source, args.annotations, args.subject_prompt, args.mask_prompt,
                       args.subject_prompt_id, args.mask_prompt_id,
                       args.evaluation_notes, args.seed, args.output, tasks=args.tasks, splits_path=args.splits)
    print(json.dumps({"train_notes": len(manifest["train_note_ids"]),
                      "evaluation_notes": len(manifest["evaluation_note_ids"]),
                      "training_examples": manifest["training_examples"]}))


if __name__ == "__main__":
    main()
