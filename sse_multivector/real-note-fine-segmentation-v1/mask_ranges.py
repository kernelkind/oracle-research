#!/usr/bin/env python3
"""Prepare exact mask placements and apply explicit review decisions without judging."""

import argparse
import copy
import json
from pathlib import Path

from generation import new_directory, read, sha, write
from sse_multivector.worker import _byte_span_to_character_span


def enumerate_placements(text, fragments, *, limit=256):
    if (
        not isinstance(fragments, list)
        or not fragments
        or any(not isinstance(fragment, str) or not fragment for fragment in fragments)
    ):
        raise ValueError("mask must contain nonempty string fragments")
    if type(limit) is not int or limit < 1:
        raise ValueError("placement limit must be a positive integer")
    raw, occurrences = text.encode("utf-8"), []
    for fragment in fragments:
        needle, start, found = fragment.encode("utf-8"), 0, []
        while (start := raw.find(needle, start)) != -1:
            found.append([start, start + len(needle)])
            start += 1
        occurrences.append(found)
    # The latest feasible suffix position prunes prefixes that cannot finish.
    latest, bound = [], len(raw)
    for choices in reversed(occurrences):
        valid = [span for span in choices if span[1] <= bound]
        if not valid:
            return {
                "fragment_occurrences": occurrences,
                "placements": [],
                "alternatives_complete": True,
                "placement_status": "no_valid_placement",
            }
        bound = valid[-1][0]
        latest.append(bound)
    latest.reverse()
    placements = []

    def visit(index, end, spans):
        if index == len(occurrences):
            placements.append(spans)
            return len(placements) > limit
        for span in occurrences[index]:
            if end <= span[0] <= latest[index] and visit(
                index + 1, span[1], spans + [span]
            ):
                return True
        return False

    overflow = visit(0, 0, [])
    return {
        "fragment_occurrences": occurrences,
        "placements": placements[:limit],
        "alternatives_complete": not overflow,
        "placement_status": "overflow"
        if overflow
        else "unique"
        if len(placements) == 1
        else "ambiguous",
    }


def highlighted(text, spans):
    raw, parts, end = text.encode("utf-8"), [], 0
    for left, right in spans:
        parts.extend(
            [raw[end:left].decode("utf-8"), "⟦", raw[left:right].decode("utf-8"), "⟧"]
        )
        end = right
    return "".join(parts) + raw[end:].decode("utf-8")


def prepare(review_path, output_path):
    source, output = Path(review_path).resolve(), Path(output_path)
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    review, calls, seen = read(source), [], set()
    if review.get("schema_version") != 1 or review.get("stage") != "masks":
        raise ValueError("input must be a collected masks review")
    lines = ["Mechanical positions only; no semantic acceptance is implied.", ""]
    for note_index, note in enumerate(review["notes"]):
        for result in note["outputs"]:
            call_id = result["call_id"]
            if call_id in seen:
                raise ValueError("duplicate mask call ID")
            seen.add(call_id)
            subject_index = result["subject_index"]
            subject = note["subjects"][subject_index]
            call = {
                "call_id": call_id,
                "note_index": note_index,
                "subject_index": subject_index,
                "note_id": note["note_id"],
                "subject_id": subject["id"],
                "subject": subject["subject"],
                "raw_mask": result.get("raw_response"),
            }
            try:
                if result["status"] != "succeeded":
                    raise ValueError("mask generation did not succeed")
                call["fragments"] = json.loads(call["raw_mask"])
                call.update(enumerate_placements(note["text"], call["fragments"]))
            except (ValueError, TypeError) as error:
                call.update(
                    placement_status="invalid_output",
                    placements=[],
                    alternatives_complete=True,
                    mechanical_error=str(error),
                )
            calls.append(call)
            lines.extend(
                [
                    call_id,
                    "Subject: " + call["subject"],
                    "Placement: " + call["placement_status"],
                    "Raw mask: " + str(call["raw_mask"]),
                ]
            )
            spans = (
                call["placements"][0] if call["placement_status"] == "unique" else []
            )
            lines.extend(
                [
                    highlighted(note["text"], spans),
                    "Alternatives (UTF-8 bytes): " + json.dumps(call["placements"]),
                    "",
                ]
            )
    prepared = {
        "schema_version": 1,
        "source_path": str(source),
        "source_sha256": sha(source),
        "placement_limit": 256,
        "calls": calls,
    }
    new_directory(output)
    with (output / "source-review.json").open("xb") as destination:
        destination.write(source.read_bytes())
    write(output / "placements.json", prepared)
    with (output / "review.txt").open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines) + "\n")
    return prepared


def apply_decisions(prepared_path, decisions_path, output_path):
    prepared, decisions_path, output = (
        Path(prepared_path).resolve(),
        Path(decisions_path).resolve(),
        Path(output_path),
    )
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    placements = read(prepared / "placements.json")
    if sha(prepared / "source-review.json") != placements["source_sha256"]:
        raise ValueError("saved source review hash changed")
    source, decisions = read(prepared / "source-review.json"), read(decisions_path)
    if (
        decisions.get("schema_version") != 1
        or not isinstance(decisions.get("reviewer"), str)
        or not decisions["reviewer"].strip()
        or not isinstance(decisions.get("decisions"), dict)
    ):
        raise ValueError(
            "decisions require schema_version 1, reviewer, and decisions keyed by call ID"
        )
    supplied = decisions["decisions"]
    calls = {
        (call["note_index"], call["subject_index"]): call
        for call in placements["calls"]
    }
    if len(calls) != len(placements["calls"]) or set(supplied) - {
        call["call_id"] for call in calls.values()
    }:
        raise ValueError("duplicate subject call or unknown decision call ID")
    notes, lines = (
        [],
        [
            "Explicit mask-review decisions; complete originals and chosen UTF-8 ranges.",
            "",
        ],
    )
    accounting = {"accepted": 0, "rejected": 0, "unresolved": 0}
    for note_index, source_note in enumerate(source["notes"]):
        note = {
            key: copy.deepcopy(value)
            for key, value in source_note.items()
            if key not in ("subjects", "outputs")
        }
        note["subjects"] = []
        for subject_index, original in enumerate(source_note["subjects"]):
            subject = copy.deepcopy(original)
            subject.pop("byte_spans", None)
            call = calls.get((note_index, subject_index))
            if call is None:
                subject["judgment"] = (
                    original["judgment"]
                    if original["judgment"] in ("rejected", "unresolved")
                    else "unresolved"
                )
                subject.setdefault("provenance", {})["mask_review"] = {
                    "status": "no_saved_mask_call"
                }
            else:
                decision = supplied.get(call["call_id"])
                if decision is not None and (
                    not isinstance(decision, dict)
                    or decision.get("judgment") not in accounting
                ):
                    raise ValueError(
                        "every explicit decision requires an accepted/rejected/unresolved judgment"
                    )
                subject["judgment"] = (
                    decision["judgment"] if decision is not None else "unresolved"
                )
                fragments = (
                    decision.get("fragments", call.get("fragments"))
                    if decision
                    else call.get("fragments")
                )
                subject["fragments"] = copy.deepcopy(fragments)
                try:
                    alternatives = enumerate_placements(note["text"], fragments)
                except ValueError:
                    if subject["judgment"] == "accepted":
                        raise
                    alternatives = {
                        "placements": [],
                        "alternatives_complete": True,
                        "placement_status": "invalid_output",
                    }
                provenance = {
                    "call_id": call["call_id"],
                    "reviewer": decisions["reviewer"],
                    "decision": copy.deepcopy(decision),
                    "raw_mask": call["raw_mask"],
                    "raw_fragments": call.get("fragments"),
                    "raw_placements": call["placements"],
                    "raw_alternatives_complete": call["alternatives_complete"],
                    "reviewed_placements": alternatives["placements"],
                    "reviewed_alternatives_complete": alternatives[
                        "alternatives_complete"
                    ],
                    "source_review_sha256": placements["source_sha256"],
                    "source_review_path": str(prepared / "source-review.json"),
                    "decisions_sha256": sha(decisions_path),
                }
                subject.setdefault("provenance", {})["mask_review"] = provenance
                if subject["judgment"] == "accepted":
                    spans = decision.get("byte_spans")
                    if spans is None:
                        if alternatives["placement_status"] != "unique":
                            raise ValueError(
                                f"accepted mask {call['call_id']} requires explicit byte_spans"
                            )
                        spans = alternatives["placements"][0]
                        provenance["placement_resolution"] = "uniquely_determined"
                    else:
                        provenance["placement_resolution"] = "explicit_byte_spans"
                    if not isinstance(spans, list) or len(spans) != len(fragments):
                        raise ValueError(
                            "explicit byte_spans must match the fragment count"
                        )
                    end = 0
                    for fragment, span in zip(fragments, spans, strict=True):
                        if (
                            not isinstance(span, list)
                            or len(span) != 2
                            or any(type(value) is not int for value in span)
                        ):
                            raise ValueError(
                                "explicit byte_spans require integer [start, end] pairs"
                            )
                        left, right = span
                        _byte_span_to_character_span(note["text"], (left, right))
                        if left < end:
                            raise ValueError(
                                "explicit mask spans overlap or are out of source order"
                            )
                        if note["text"].encode("utf-8")[left:right] != fragment.encode(
                            "utf-8"
                        ):
                            raise ValueError(
                                "explicit mask spans do not select exact fragments"
                            )
                        end = right
                    subject["byte_spans"] = copy.deepcopy(spans)
            note["subjects"].append(subject)
            accounting[subject["judgment"]] += 1
            lines.extend(
                [
                    subject["id"] + " — " + subject["judgment"],
                    "Subject: " + subject["subject"],
                    highlighted(note["text"], subject.get("byte_spans", [])),
                    "",
                ]
            )
        notes.append(note)
    result = {
        "schema_version": 1,
        "accounting": accounting,
        "provenance": {
            "placements_path": str(prepared / "placements.json"),
            "placements_sha256": sha(prepared / "placements.json"),
            "decisions_path": str(decisions_path),
            "decisions_sha256": sha(decisions_path),
            "reviewer": decisions["reviewer"],
        },
        "notes": notes,
    }
    new_directory(output)
    write(output / "reviewed-input.json", result)
    with (output / "review.txt").open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    command = commands.add_parser("prepare")
    command.add_argument("input", type=Path)
    command.add_argument("output", type=Path)
    command = commands.add_parser("apply")
    command.add_argument("prepared", type=Path)
    command.add_argument("decisions", type=Path)
    command.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.operation == "apply":
        print(
            json.dumps(
                apply_decisions(args.prepared, args.decisions, args.output)[
                    "accounting"
                ],
                sort_keys=True,
            )
        )
        return
    result = prepare(args.input, args.output)
    counts = {}
    for call in result["calls"]:
        key = call["placement_status"]
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
