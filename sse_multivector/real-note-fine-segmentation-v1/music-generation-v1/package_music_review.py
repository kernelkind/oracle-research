#!/usr/bin/env python3
"""Copy complete saved segments into non-repeating, initially unanswered reviews."""

import copy
import hashlib
import json
import sys
from pathlib import Path

M = Path(__file__).resolve().parent
E = M.parent
sys.path.insert(0, str(E))
from generation import write


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(packet):
    return frozenset(row["vector_id"] for row in packet["instances"])


def evidence(packet):
    return {
        row["vector_id"]: {key: row[key] for key in ("note_id", "text", "byte_spans")}
        for row in packet["instances"]
    }


def main():
    destination = M / "review-handoff"
    if destination.exists():
        raise ValueError("handoff already exists; preserve user reviews")
    prior = {}
    sources = {}
    for folder in (E / "cross-note-density-v1", E / "review-handoff/baseline"):
        review_path, response_path = folder / "review.json", folder / "user-response.json"
        review, response = read(review_path), read(response_path)
        if response["review_set"] != review["review_set"]:
            raise ValueError("prior response does not match its review")
        packets = {p["packet"]: p for p in review["packets"]}
        sources[str(review_path)] = sha(review_path)
        sources[str(response_path)] = sha(response_path)
        for decision in response["judgments"]:
            packet = packets[decision["packet"]]
            prior[members(packet)] = {
                "kind": "prior_user_response",
                "packet": packet["packet"],
                "review": str(review_path),
                "response": str(response_path),
                "evidence": evidence(packet),
            }
    # The user approved the displayed baseline in chat, including its few
    # unconfirmed clicks. Preserve that distinction instead of asking again.
    baseline_path = E / "review-handoff/baseline/review.json"
    chat_record = E / "results.md"
    quote = "done. these all look like valid groupings to me"
    if quote not in chat_record.read_text():
        raise ValueError("baseline-wide chat assessment is not recorded")
    sources[str(chat_record)] = sha(chat_record)
    for packet in read(baseline_path)["packets"]:
        if len({row["note_id"] for row in packet["instances"]}) >= 2:
            prior.setdefault(members(packet), {
                "kind": "prior_baseline_chat_assessment",
                "packet": packet["packet"], "review": str(baseline_path),
                "chat_record": str(chat_record), "quote": quote,
                "evidence": evidence(packet),
            })
    music_pending = {}
    manifest = {
        "schema_version": 1,
        "purpose": "Review packaging only; not a new partition or copied verdicts.",
        "user_decisions": "Initially absent. Partial review and resume are supported.",
        "reuse_policy": "Skip only identical complete vector sets with matching mask evidence. A prior response is not reinterpreted; any later chat retraction remains authoritative. Music duplicates remain pending in the music review.",
        "sources": sources,
        "sets": {},
    }
    outputs = {}
    for name, run in (("music", "HDBv2-music100"), ("combined", "HDBv2-combined200")):
        source_path = M / run / "review/review.json"
        source = read(source_path)
        proof_path = M / run / "replay-proof.json"
        if not read(proof_path)["full_parsed_response_equal"]:
            raise ValueError("candidate replay is not verified")
        manifest["sources"][str(source_path)] = sha(source_path)
        manifest["sources"][str(proof_path)] = sha(proof_path)
        kept, skipped = [], []
        for packet in source["packets"]:
            if len({row["note_id"] for row in packet["instances"]}) < 2:
                skipped.append({"packet": packet["packet"], "kind": "one_source_note"})
                continue
            key = members(packet)
            previous = music_pending.get(key) or prior.get(key)
            if previous is not None:
                if evidence(packet) != previous["evidence"]:
                    raise ValueError("same vector set has different mask evidence")
                skipped.append({"packet": packet["packet"], "vector_ids": sorted(key),
                                **{k: v for k, v in previous.items() if k != "evidence"}})
            else:
                kept.append(packet)
                if name == "music":
                    music_pending[key] = {
                        "kind": "pending_in_music_review", "packet": packet["packet"],
                        "review": str(destination / "music/review.json"),
                        "evidence": evidence(packet),
                    }
        output = copy.deepcopy(source)
        output["packets"] = kept
        identity = "RN" + hashlib.sha256(json.dumps(
            [sha(source_path), [p["packet"] for p in kept]]
        ).encode()).hexdigest()[:12]
        output["review_set"] = identity
        output["response_contract"]["review_set"] = identity
        outputs[name] = output
        manifest["sets"][name] = {
            "review": str(destination / name / "review.json"),
            "source_review": str(source_path),
            "included_segments": [p["packet"] for p in kept], "skipped": skipped,
        }
    for path, digest in manifest["sources"].items():
        if sha(Path(path)) != digest:
            raise ValueError("source changed while packaging")
    for name, output in outputs.items():
        folder = destination / name
        folder.mkdir(parents=True, exist_ok=False)
        write(folder / "review.json", output)
        manifest["sets"][name]["sha256"] = sha(folder / "review.json")
    write(destination / "manifest.json", manifest)
    print(json.dumps({name: len(output["packets"]) for name, output in outputs.items()}))


if __name__ == "__main__":
    main()
