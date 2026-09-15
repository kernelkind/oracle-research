#!/usr/bin/env python3
"""Prepare one shared set of exact masks for title generation and title review."""

import argparse
import hashlib
import json
from pathlib import Path


def prepare(source, template, selected_groups):
    if template.count("{NUMBERED_INSTANCES}") != 1:
        raise ValueError("prompt must contain NUMBERED_INSTANCES exactly once")
    packets = source["packets"]
    ids = [packet["packet"] for packet in packets]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate group IDs")
    if set(selected_groups) - set(ids):
        raise ValueError("unknown group requested")
    texts, groups = {}, []
    for packet in packets:
        if selected_groups and packet["packet"] not in selected_groups:
            continue
        instances, sources, seen_ids, masks = [], [], set(), {}
        for item in packet["instances"]:
            name, note_id, text = item["instance"], item["note_id"], item["text"]
            if name in seen_ids:
                raise ValueError("duplicate instance ID")
            seen_ids.add(name)
            if note_id in texts and texts[note_id] != text:
                raise ValueError(f"conflicting text for note {note_id}")
            texts[note_id] = text
            spans, fragments = item["byte_spans"], item["fragments"]
            if not spans or len(spans) != len(fragments):
                raise ValueError("mask needs matching nonempty spans and fragments")
            raw, previous_end = text.encode("utf-8"), 0
            for span, fragment in zip(spans, fragments):
                if (len(span) != 2 or any(type(x) is not int for x in span)
                        or not previous_end <= span[0] < span[1] <= len(raw)):
                    raise ValueError("invalid mask byte spans")
                if raw[span[0]:span[1]] != fragment.encode("utf-8"):
                    raise ValueError("fragment does not match source byte span")
                previous_end = span[1]
            key = (note_id, tuple(tuple(span) for span in spans))
            if key in masks:
                masks[key]["source_instances"].append(name)
                masks[key]["source_vector_ids"].append(item["vector_id"])
                continue
            instances.append({"instance": name, "fragments": fragments})
            sources.append({
                "instance": name, "note_id": note_id, "byte_spans": spans,
                "source_instances": [name],
                "source_vector_ids": [item["vector_id"]],
            })
            masks[key] = sources[-1]
        if not instances:
            raise ValueError("empty category")
        numbered = "\n".join(
            f"{index}. " + "; ".join(f"“{part}”" for part in item["fragments"])
            for index, item in enumerate(instances, 1)
        )
        groups.append({
            "group": packet["packet"], "instances": instances, "sources": sources,
            "duplicates_removed": len(packet["instances"]) - len(instances),
            "prompt": template.replace("{NUMBERED_INSTANCES}", numbered),
        })
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_packets", type=Path)
    parser.add_argument("prompt", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--group", action="append", default=[])
    args = parser.parse_args()
    try:
        source_bytes, prompt_bytes = args.source_packets.read_bytes(), args.prompt.read_bytes()
        groups = prepare(json.loads(source_bytes), prompt_bytes.decode(), args.group)
        result = {
            "schema_version": 1,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
            "groups": groups,
        }
        with args.output.open("x") as destination:
            json.dump(result, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
