#!/usr/bin/env python3
"""Reproduce frozen input selection. No model calls, network, or file writes."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
RELATIVE = HERE.relative_to(HERE.parents[2]).as_posix()
SOURCE_HASH = "61dd56ba952ce4f323ceef81f24c10fc56570c6107c55f652ab53992111d94de"
SEED = "frontier-english-input-selection-v1/2026-09-16/"
TARGET = 60
CHALLENGES = {
    "B": "Short or sparse text (at most 10 words after URLs and encoded Nostr IDs)",
    "M": "Multiple statements, comparisons, or list items",
    "C": "References, ellipsis, or missing thread/attachment context",
    "S": "Opinions, emotion, rhetoric, or figurative language",
    "A": "Headlines, quotations, or attributed statements",
    "Q": "Questions, requests, advice, or instructions",
    "N": "Numbers, dates, measurements, or codes in the text",
    "P": "URLs, hashtags, handles, contact addresses, or Nostr identifiers",
}
POINTER = re.compile(r"https?://\S+|(?:nostr:)?(?:npub|nprofile|note|nevent|naddr|nsec)1[a-zA-Z0-9]+")
HAS_POINTER = re.compile(r"https?://|#[\w]+|@[a-zA-Z]|\bnostr:|\b(?:npub|nprofile|nevent|naddr|note)1|\S+@\S+\.\S+")


def read(name):
    return json.loads((HERE / name).read_text())


def rank(channel, note_id):
    return sha256((SEED + channel + "/" + note_id).encode()).hexdigest()


def template(text):
    """Group only full texts equal after pointer/number/whitespace normalization."""
    value = POINTER.sub("_", text).casefold()
    value = re.sub(r"\d+", "_", value)
    return re.sub(r"\s+", " ", value).strip()


def artifacts():
    source_bytes = (HERE / "source-notes.json").read_bytes()
    if sha256(source_bytes).hexdigest() != SOURCE_HASH:
        raise ValueError("Source snapshot hash changed")
    source = json.loads(source_bytes)["notes"]
    manual = read("manual-audit.json")["rows"]
    prior = set(read("prior-prompt-note-ids.json")["note_ids"])
    if set(manual) != {str(i + 501) for i in range(len(source))}:
        raise ValueError("Manual audit must cover every source row exactly once")
    rows = []
    families = defaultdict(list)
    for index, note in enumerate(source, 1):
        codes = manual[str(index + 500)]
        clean = POINTER.sub("", note["text"])
        words = len(clean.split())
        challenges = {c for c in codes if c in CHALLENGES}
        if words <= 10:
            challenges.add("B")
        if re.search(r"\d", clean):
            challenges.add("N")
        if HAS_POINTER.search(note["text"]):
            challenges.add("P")
        excluded = []
        if note["note_id"] in prior:
            excluded.append("known_prompt_development_note")
        if "L" in codes:
            excluded.append("non_english_or_mixed_prose")
        if "Z" in codes:
            excluded.append("not_readable_english_text")
        row = {
            "id": f"E{index + 500:04d}", "source_index": index,
            "frozen_sample_row": index + 500, "note_id": note["note_id"],
            "manual_codes": codes, "words_after_pointer_removal": words,
            "challenges": sorted(challenges), "exclude_reasons": excluded,
        }
        rows.append(row)
        if not excluded:
            families[template(note["text"])].append(row)
    duplicate_groups = []
    for family in families.values():
        family.sort(key=lambda r: rank("template-representative", r["note_id"]))
        representative = family[0]
        for row in family:
            row["template_representative"] = representative["id"]
            row["template_notes"] = len(family)
        for row in family[1:]:
            row["exclude_reasons"].append("repeated_template")
        if len(family) > 1:
            duplicate_groups.append([row["id"] for row in family])
    eligible = [r for r in rows if not r["exclude_reasons"]]
    draws = {}
    pools = {"general": eligible}
    pools.update({c: [r for r in eligible if c in r["challenges"]] for c in CHALLENGES})
    for channel, pool in pools.items():
        if len(pool) < TARGET:
            raise ValueError(f"{channel}: only {len(pool)} eligible notes; need {TARGET}")
        draws[channel] = {
            r["note_id"] for r in sorted(pool, key=lambda r: rank(channel, r["note_id"]))[:TARGET]
        }
    selected_ids = set().union(*draws.values())
    notes = []
    for row in rows:
        row["selected_by"] = [c for c, ids in draws.items() if row["note_id"] in ids]
        row["selected"] = row["note_id"] in selected_ids
        if row["exclude_reasons"]:
            continue
        # Probability over the separately salted draws, conditional on the deduplicated frame.
        miss_probability = 1.0
        for channel in ["general", *row["challenges"]]:
            miss_probability *= 1.0 - TARGET / len(pools[channel])
        row["inclusion_probability"] = 1.0 - miss_probability
        if not row["selected"]:
            continue
        original = source[row["source_index"] - 1]
        reasons = "; ".join(CHALLENGES[c] for c in row["challenges"])
        notes.append({
            "id": row["id"], "title": "Original English post",
            "note_id": original["note_id"], "text": original["text"],
            "why": reasons or "Ordinary English post from the general random draw.",
            "source": {"path": RELATIVE + "/source-notes.json", "index": row["source_index"]},
        })
    purpose = (
        "Input review only. Original posts are unchanged. No subjects, masks, or model answers "
        "have been generated. Coverage labels are reviewer notes, not instructions sent to a model."
    )
    selection = {"schema_version": 1, "title": "English model-comparison inputs", "purpose": purpose, "notes": notes}
    viewer_plan = read("sampler-plan.json")
    by_label = {n["id"]: n for n in notes}
    sample = []
    for item in viewer_plan["notes"]:
        note = by_label[item["id"]]
        note["title"] = item["title"]
        note["why"] = item["why"]
        sample.append(note)
    sampler = {"schema_version": 1, "title": f"English input sample — {len(sample)} notes", "purpose": purpose, "notes": sample}
    report = {
        "schema_version": 1, "model_calls_made": False,
        "source_notes": len(source), "eligible_notes_before_template_deduplication": sum(map(len, families.values())),
        "eligible_distinct_templates": len(eligible), "selected_notes": len(notes), "viewer_notes": len(sample),
        "exclusions": dict(Counter(reason for r in rows for reason in r["exclude_reasons"])),
        "challenges": [{"id": c, "description": title, "target_notes": TARGET,
                        "eligible_notes": len(pools[c]),
                        "selected_notes": sum(c in r["challenges"] and r["selected"] for r in rows)}
                       for c, title in CHALLENGES.items()],
        "selected_length_bands": dict(Counter(
            "0–10" if r["words_after_pointer_removal"] <= 10 else
            "11–30" if r["words_after_pointer_removal"] <= 30 else
            "31–100" if r["words_after_pointer_removal"] <= 100 else ">100"
            for r in rows if r["selected"])),
        "selection": {
            "seed": SEED, "notes_per_draw": TARGET,
            "method": "Separate hash-random draws of 60 from the whole eligible frame and each of eight overlapping challenges; retain their union.",
            "template_rule": "One hash-random representative of full texts equal after replacing URLs, encoded Nostr identifiers, digits and whitespace. Different headlines with the same publisher footer are not collapsed.",
            "template_groups": duplicate_groups,
            "weighting": "The oversampled union is not a simple random sample. For each challenge, use its original 60-note random draw (selected_by in audit.json), or weight the pooled results by inverse inclusion probability. A whole-frame mean can use the Horvitz–Thompson sum divided by eligible frame size. These estimate the deduplicated English frame, not raw production traffic.",
        },
        "provenance": {
            "source_sha256": SOURCE_HASH,
            "original_frozen_rows": [501, 1000],
            "frozen_ordered_ids_sha256": "8b0ce45049ed10cfebccab6db15c665f3e2598f5efbb5ef0fc5813dba899bfd5",
            "source_db_sha256_verified_by_export": "3b19f650035fbb71c09bc51e06957f64ca421df948bac3b4751fa4809ffe73e4",
            "known_prompt_note_ids_checked": len(prior),
            "manual_audit": "The main agent read every source post before model outputs; the coding is a fallible input audit, not a model-generated annotation or answer key.",
        },
        "limits": [
            "Challenge counts overlap and must not be added together. They do not imply 60 examples of every subtype or combination.",
            "A includes simple headlines as well as complex attribution. S includes literal opinions as well as fiction and metaphor. Q includes promotional instructions as well as genuine help requests.",
            "The 60-note target gives 1 - 0.95^60 = 95.39% chance to observe at least one 5%-frequency failure only under an independent, representative Bernoulli model within that challenge. It is not a precision guarantee or proof of equivalence.",
            "Template filtering removes obvious repeated forms but cannot establish statistical independence between authors or sources.",
            "This comparison requires readable English text. The manual audit excludes untranslated non-English prose, emoji-only posts and opaque payloads. Readable English reports remain eligible even when machine-generated. Translated titles, proper names and borrowed expressions can occur inside English posts.",
            "Known prompt-note exclusion does not prove absence from all earlier experiments or model pretraining.",
            "The 12-note viewer is curated for easy inspection after selection, not a representative accuracy sample.",
            "No model prompts were changed; subject and mask comparison remain separate, with identical fixed subjects required for the later mask comparison.",
        ],
    }
    return {"audit.json": {"schema_version": 1, "notes": rows}, "selection.json": selection,
            "sampler.json": sampler, "coverage.json": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--artifact", choices=["audit.json", "selection.json", "sampler.json", "coverage.json"])
    args = parser.parse_args()
    generated = artifacts()
    if args.check:
        for name, value in generated.items():
            if read(name) != value:
                raise SystemExit(f"Saved artifact differs: {name}")
        print(f"Verified {generated['coverage.json']['selected_notes']} selected notes and {generated['coverage.json']['viewer_notes']} viewer notes; no model calls.")
    else:
        print(json.dumps(generated[args.artifact] if args.artifact else generated, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
