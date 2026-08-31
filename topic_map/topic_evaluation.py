#!/usr/bin/env python3
"""Verify CREC-113 artifacts and publish one tiny discarded procedure pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import re
import shutil
import struct
import tempfile
import unicodedata
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SAMPLE_RULE = (
    "semantic-order-prefix-author-hash-text-copy-disjoint-learning-first-v2"
)
EMBEDDING_FORMAT = "learning-first-note-embedding-matrix-v1"
RELATION_FORMAT = "canonical-sparse-note-topic-relation-v1"
PILOT_RULE = (
    "sha256-domain-separated-structurally-complete-blinded-cases-v4"
)
NOTE_ONLY_PILOT_RULE = (
    "sha256-domain-separated-structurally-complete-note-only-cases-v1"
)
PILOT_RANK_DOMAIN = b"oracle-mvp/crec-113/discarded-preview/v2\0"
SCALE_PREFLIGHT_NOTES = 5_120
TOPIC_CASES = 3
NOTE_CASES = 2
TOPIC_PROBE_STRATA = ("high", "middle", "low")
TOPIC_EXEMPLARS = 3
TOPIC_PROBES = 4
NOTE_TOPIC_CARDS = 3
CARD_EXEMPLARS = 3
RELATION_FILES = (
    "note-offsets.u64le",
    "topic-ids.u32le",
    "weights.f32le",
    "topic-offsets.u64le",
    "topic-edge-order.u64le",
    "source-topic-ids.u32le",
    "note-ids.bin",
)
REFERENCE_TOKEN = re.compile(
    r"(?iu)(?:"
    r"\b[a-z][a-z0-9+.-]{1,31}://\S+"
    r"|\bwww\.\S+"
    r"|\bnostr:\S+"
    r"|\b(?:npub|nprofile|note|nevent|naddr|nrelay|nsec)1"
    r"[02-9ac-hj-np-z]+"
    r")"
)
LONG_OPAQUE_TOKEN = re.compile(r"\S{64,}")
VISIBLE_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _integer(value: object, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"`{name}` must be an integer >= {minimum}")
    return value


def _digest(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"`{name}` must be a lowercase SHA-256 digest")
    return value


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"`{name}` must be an object")
    return value


def _manifest(path: Path, name: str) -> tuple[dict[str, Any], str]:
    contents = path.read_bytes()
    try:
        value = _object(json.loads(contents), name)
    except json.JSONDecodeError as error:
        raise ValueError(f"`{name}` is invalid JSON") from error
    return value, hashlib.sha256(contents).hexdigest()


def _spec(
    files: dict[str, Any], name: str, expected_size: int | None = None
) -> tuple[int, str]:
    value = _object(files.get(name), f"files.{name}")
    size = _integer(value.get("bytes"), f"files.{name}.bytes")
    digest = _digest(value.get("sha256"), f"files.{name}.sha256")
    if expected_size is not None and size != expected_size:
        raise ValueError(f"`{name}` has the wrong declared length")
    return size, digest


@dataclass(frozen=True)
class PilotConfig:
    sample_manifest_path: Path
    embedding_manifest_path: Path
    relation_manifest_path: Path
    scale_preflight_note_ids_path: Path
    scale_preflight_note_ids_sha256: str
    output_path: Path
    seed_hex: str


@dataclass(frozen=True)
class _Bound:
    sample_path: Path
    sample_sha: str
    sample_manifest_sha: str
    embedding_manifest_sha: str
    relation_manifest_sha: str
    excluded_sha: str
    excluded: frozenset[bytes]
    embedding_ids_spec: tuple[int, str]
    relation_specs: tuple[tuple[str, int, str], ...]
    learning: int
    notes: int
    topics: int
    entries: int


def _validated_seed(config: PilotConfig) -> bytes:
    return bytes.fromhex(_digest(config.seed_hex, "seed_hex"))


def _bind(config: PilotConfig) -> _Bound:
    sample, sample_manifest_sha = _manifest(
        config.sample_manifest_path, "sample manifest"
    )
    if sample.get("schema_version") != 3 or sample.get("selection_rule") != SAMPLE_RULE:
        raise ValueError("unsupported sample artifact")
    learning = _integer(sample.get("learning_rows"), "learning_rows", 1)
    evaluation = _integer(sample.get("evaluation_rows"), "evaluation_rows", 1)
    notes = learning + evaluation
    sample_file = _object(sample.get("sample"), "sample")
    if (
        sample_file.get("file") != "sample.jsonl"
        or sample_file.get("records") != notes
    ):
        raise ValueError("sample file does not match its split quotas")
    sample_path = config.sample_manifest_path.parent / "sample.jsonl"
    sample_size = _integer(sample_file.get("bytes"), "sample.bytes")
    sample_sha = _digest(sample_file.get("sha256"), "sample.sha256")
    if sample_path.stat().st_size != sample_size:
        raise ValueError("sample length differs from its manifest")

    embedding, embedding_manifest_sha = _manifest(
        config.embedding_manifest_path, "embedding manifest"
    )
    if (
        embedding.get("schema_version") != 1
        or embedding.get("embedding_format") != EMBEDDING_FORMAT
        or embedding.get("sample_manifest_sha256") != sample_manifest_sha
        or embedding.get("sample_sha256") != sample_sha
        or embedding.get("sample_selection_rule") != SAMPLE_RULE
        or embedding.get("learning_rows") != learning
        or embedding.get("evaluation_rows") != evaluation
        or embedding.get("total_rows") != notes
    ):
        raise ValueError("embedding does not bind the exact sample")
    encoder = _object(embedding.get("encoder"), "embedding.encoder")
    dimensions = _integer(encoder.get("dimensions"), "dimensions", 1)
    if encoder.get("numeric_type") != "float32":
        raise ValueError("unsupported embedding numeric type")
    embedding_files = _object(embedding.get("files"), "embedding.files")
    vector_size, vector_sha = _spec(
        embedding_files, "vectors.f32le", notes * dimensions * 4
    )
    # The relation binds this encoder-produced digest. Pilot generation never
    # reads the full matrix because it needs only the sparse relation.
    if (
        config.embedding_manifest_path.parent / "vectors.f32le"
    ).stat().st_size != vector_size:
        raise ValueError("embedding matrix length differs from its manifest")
    embedding_ids_spec = _spec(
        embedding_files, "note-ids.bin", notes * 32
    )
    embedding_ids_sha = embedding_ids_spec[1]

    relation, relation_manifest_sha = _manifest(
        config.relation_manifest_path, "relation manifest"
    )
    topics = _integer(relation.get("topic_count"), "topic_count", 1)
    entries = _integer(relation.get("entry_count"), "entry_count", 1)
    metadata = _object(relation.get("metadata"), "relation.metadata")
    if (
        relation.get("schema_version") != 1
        or relation.get("relation_format") != RELATION_FORMAT
        or relation.get("note_count") != notes
        or relation.get("weight_semantics")
        != "positive activation normalized within each note"
        or metadata.get("start_row") != 0
        or metadata.get("learning_rows") != learning
        or metadata.get("evaluation_rows") != evaluation
        or metadata.get("matrix_range_sha256") != vector_sha
        or metadata.get("note_ids_range_sha256") != embedding_ids_sha
        or metadata.get("embedding_manifest_sha256")
        != embedding_manifest_sha
    ):
        raise ValueError("relation does not bind the exact embedding")
    relation_files = _object(relation.get("files"), "relation.files")
    sizes = (
        (notes + 1) * 8,
        entries * 4,
        entries * 4,
        (topics + 1) * 8,
        entries * 8,
        topics * 4,
        notes * 32,
    )
    relation_specs = tuple(
        (name, *_spec(relation_files, name, size))
        for name, size in zip(RELATION_FILES, sizes, strict=True)
    )
    if _spec(relation_files, "note-ids.bin")[1] != embedding_ids_sha:
        raise ValueError(
            "relation NoteId order differs from the sample/embedding chain"
        )

    excluded_bytes = config.scale_preflight_note_ids_path.read_bytes()
    excluded_size = len(excluded_bytes)
    excluded_sha = hashlib.sha256(excluded_bytes).hexdigest()
    expected_excluded_sha = _digest(
        config.scale_preflight_note_ids_sha256,
        "scale_preflight_note_ids_sha256",
    )
    if excluded_sha != expected_excluded_sha:
        raise ValueError("scale-preflight exclusion hash differs from config")
    if excluded_size != SCALE_PREFLIGHT_NOTES * 32:
        raise ValueError("scale-preflight exclusion must contain 5,120 NoteIds")
    excluded = frozenset(
        excluded_bytes[offset : offset + 32]
        for offset in range(0, excluded_size, 32)
    )
    if len(excluded) != SCALE_PREFLIGHT_NOTES:
        raise ValueError("scale-preflight exclusion NoteIds are not unique")
    return _Bound(
        sample_path,
        sample_sha,
        sample_manifest_sha,
        embedding_manifest_sha,
        relation_manifest_sha,
        excluded_sha,
        excluded,
        embedding_ids_spec,
        relation_specs,
        learning,
        notes,
        topics,
        entries,
    )


def _mapped_verified(
    stack: ExitStack, path: Path, expected: tuple[int, str]
) -> mmap.mmap:
    source = stack.enter_context(path.open("rb"))
    digest = hashlib.sha256()
    size = 0
    while chunk := source.read(1024 * 1024):
        size += len(chunk)
        digest.update(chunk)
    if (size, digest.hexdigest()) != expected:
        raise ValueError(f"`{path.name}` differs from its manifest")
    return stack.enter_context(mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ))


def _at(mapped: mmap.mmap, code: str, index: int) -> int | float:
    return struct.unpack_from("<" + code, mapped, index * struct.calcsize(code))[0]


def _rank(seed: bytes, domain: bytes, identity: bytes) -> bytes:
    digest = hashlib.sha256(PILOT_RANK_DOMAIN)
    for part in (domain, seed, identity):
        digest.update(len(part).to_bytes(4, "big"))
        digest.update(part)
    return digest.digest()


def _choose(
    values: Iterable[int], count: int, seed: bytes, domain: bytes, identity
) -> list[int]:
    ordered = sorted(
        values, key=lambda value: (_rank(seed, domain, identity(value)), value)
    )
    if len(ordered) < count:
        raise ValueError(f"only {len(ordered)} eligible cases for {count} requested")
    return ordered[:count]


def _note_for_edge(offsets: mmap.mmap, edge: int, notes: int) -> int:
    low, high = 0, notes
    while low < high:
        middle = (low + high) // 2
        if int(_at(offsets, "Q", middle + 1)) <= edge:
            low = middle + 1
        else:
            high = middle
    if low == notes:
        raise ValueError("relation edge does not belong to a note")
    return low


def _topic_members(
    bound: _Bound,
    maps: dict[str, mmap.mmap],
    note_ids: mmap.mmap,
    topic: int,
    start_row: int,
    end_row: int,
    maximum: int | None = None,
) -> list[tuple[int, float]]:
    start = int(_at(maps["topic-offsets.u64le"], "Q", topic))
    end = int(_at(maps["topic-offsets.u64le"], "Q", topic + 1))
    selected: list[tuple[int, float]] = []
    for position in range(start, end):
        edge = int(_at(maps["topic-edge-order.u64le"], "Q", position))
        if edge >= bound.entries or int(
            _at(maps["topic-ids.u32le"], "I", edge)
        ) != topic:
            raise ValueError("relation topic edge order is invalid")
        row = _note_for_edge(maps["note-offsets.u64le"], edge, bound.notes)
        note_id = note_ids[row * 32 : (row + 1) * 32]
        if row < start_row or row >= end_row or note_id in bound.excluded:
            continue
        weight = float(_at(maps["weights.f32le"], "f", edge))
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("relation contains an invalid weight")
        selected.append((row, weight))
        if maximum is not None and len(selected) == maximum:
            break
    return sorted(selected, key=lambda item: (-item[1], item[0]))


def _note_topics(
    bound: _Bound, maps: dict[str, mmap.mmap], row: int
) -> list[tuple[int, float]]:
    start = int(_at(maps["note-offsets.u64le"], "Q", row))
    end = int(_at(maps["note-offsets.u64le"], "Q", row + 1))
    topics = []
    for edge in range(start, end):
        topic = int(_at(maps["topic-ids.u32le"], "I", edge))
        weight = float(_at(maps["weights.f32le"], "f", edge))
        if (
            topic >= bound.topics
            or not math.isfinite(weight)
            or weight <= 0
        ):
            raise ValueError("relation contains an invalid edge")
        topics.append((topic, weight))
    return sorted(topics, key=lambda item: (-item[1], item[0]))


def _select(
    bound: _Bound,
    seed: bytes,
    maps: dict[str, mmap.mmap],
    note_ids: mmap.mmap,
    visible_note_case_rows: frozenset[int],
    topic_case_count: int = TOPIC_CASES,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[int]]:
    eligible_evaluation_rows = [
        row
        for row in range(bound.learning, bound.notes)
        if note_ids[row * 32 : (row + 1) * 32] not in bound.excluded
    ]

    learning_exemplars: dict[int, list[tuple[int, float]]] = {}
    eligible_topics = []
    for topic in range(bound.topics):
        exemplars = _topic_members(
            bound,
            maps,
            note_ids,
            topic,
            0,
            bound.learning,
            TOPIC_EXEMPLARS,
        )
        learning_exemplars[topic] = exemplars
        if len(exemplars) != TOPIC_EXEMPLARS:
            continue
        held_out = _topic_members(
            bound,
            maps,
            note_ids,
            topic,
            bound.learning,
            bound.notes,
        )
        if len(held_out) < len(TOPIC_PROBE_STRATA):
            continue
        if len({row for row, _ in held_out}) >= len(
            eligible_evaluation_rows
        ):
            continue
        eligible_topics.append(topic)

    topics = _choose(
        eligible_topics,
        topic_case_count,
        seed,
        b"topic-cases",
        lambda value: value.to_bytes(8, "big"),
    )
    content_rows: set[int] = set()
    topic_cases: list[dict[str, Any]] = []
    for topic in topics:
        members = _topic_members(
            bound,
            maps,
            note_ids,
            topic,
            bound.learning,
            bound.notes,
        )
        probes: list[dict[str, Any]] = []
        for index, stratum in enumerate(TOPIC_PROBE_STRATA):
            start = index * len(members) // len(TOPIC_PROBE_STRATA)
            end = (index + 1) * len(members) // len(TOPIC_PROBE_STRATA)
            band = members[start:end]
            row = _choose(
                (candidate for candidate, _ in band),
                1,
                seed,
                b"topic-probe/" + stratum.encode(),
                lambda candidate: (
                    topic.to_bytes(8, "big")
                    + note_ids[candidate * 32 : (candidate + 1) * 32]
                ),
            )[0]
            weight = next(
                weight for candidate, weight in band if candidate == row
            )
            probes.append({"row": row, "weight": weight, "stratum": stratum})

        positive_rows = {row for row, _ in members}
        control = _choose(
            (
                row
                for row in eligible_evaluation_rows
                if row not in positive_rows
            ),
            1,
            seed,
            b"topic-probe/absent-control",
            lambda row: (
                topic.to_bytes(8, "big")
                + note_ids[row * 32 : (row + 1) * 32]
            ),
        )[0]
        probes.append(
            {"row": control, "weight": 0.0, "stratum": "absent_control"}
        )
        probes.sort(
            key=lambda probe: (
                _rank(
                    seed,
                    b"topic-probe/presentation-order",
                    topic.to_bytes(8, "big")
                    + note_ids[
                        probe["row"] * 32 : (probe["row"] + 1) * 32
                    ],
                ),
                probe["row"],
            )
        )
        for presentation_order, probe in enumerate(probes, 1):
            probe["presentation_order"] = presentation_order
        exemplars = learning_exemplars[topic]
        content_rows.update(row for row, _ in exemplars)
        content_rows.update(probe["row"] for probe in probes)
        topic_cases.append(
            {
                "topic_id": topic,
                "learning_exemplars": exemplars,
                "probes": probes,
            }
        )

    eligible_note_cases: dict[int, list[dict[str, Any]]] = {}
    topic_probe_rows = {
        probe["row"] for case in topic_cases for probe in case["probes"]
    }
    for row in eligible_evaluation_rows:
        if row in topic_probe_rows or row not in visible_note_case_rows:
            continue
        top_topics = _note_topics(bound, maps, row)[:NOTE_TOPIC_CARDS]
        if len(top_topics) != NOTE_TOPIC_CARDS:
            continue
        if any(
            len(learning_exemplars.get(topic, [])) != CARD_EXEMPLARS
            for topic, _ in top_topics
        ):
            continue
        cards = [
            {
                "topic_id": topic,
                "weight": weight,
                "learning_exemplars": learning_exemplars[topic],
            }
            for topic, weight in top_topics
        ]
        cards.sort(
            key=lambda card: (
                _rank(
                    seed,
                    b"note-topic-card/presentation-order",
                    note_ids[row * 32 : (row + 1) * 32]
                    + card["topic_id"].to_bytes(8, "big"),
                ),
                card["topic_id"],
            )
        )
        for presentation_order, card in enumerate(cards, 1):
            card["presentation_order"] = presentation_order
        eligible_note_cases[row] = cards
    if len(eligible_note_cases) < NOTE_CASES:
        raise ValueError(
            f"only {len(eligible_note_cases)} structurally eligible note cases "
            f"with usable visible text for {NOTE_CASES} requested"
        )
    notes = _choose(
        eligible_note_cases,
        NOTE_CASES,
        seed,
        b"note-cases",
        lambda row: note_ids[row * 32 : (row + 1) * 32],
    )
    note_cases = []
    for row in notes:
        cards = eligible_note_cases[row]
        content_rows.add(row)
        for card in cards:
            content_rows.update(
                exemplar for exemplar, _ in card["learning_exemplars"]
            )
        note_cases.append({"row": row, "topic_cards": cards})
    return topic_cases, note_cases, content_rows


def _records(
    bound: _Bound,
    wanted: set[int] | None,
    embedding_ids: mmap.mmap,
    relation_ids: mmap.mmap,
) -> dict[int, dict[str, str]]:
    selected = {}
    seen = set()
    digest = hashlib.sha256()
    size = 0
    with bound.sample_path.open("rb") as source:
        for row, line in enumerate(source):
            size += len(line)
            digest.update(line)
            if row >= bound.notes:
                raise ValueError("sample contains extra rows")
            try:
                record = _object(json.loads(line), f"sample row {row}")
                note_id = bytes.fromhex(record["note_id"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"sample row {row} is invalid") from error
            split = "learning" if row < bound.learning else "evaluation"
            content = record.get("content")
            if (
                len(note_id) != 32
                or note_id in seen
                or record.get("split") != split
                or not isinstance(content, str)
            ):
                raise ValueError(f"sample row {row} violates its manifest")
            seen.add(note_id)
            position = slice(row * 32, (row + 1) * 32)
            if embedding_ids[position] != note_id:
                raise ValueError("embedding NoteId order differs from the sample")
            if relation_ids[position] != note_id:
                raise ValueError("relation NoteId order differs from the sample")
            if wanted is None or row in wanted:
                selected[row] = {
                    "note_id": note_id.hex(),
                    "split": split,
                    "content": content,
                }
    if (
        len(seen) != bound.notes
        or size != bound.sample_path.stat().st_size
        or digest.hexdigest() != bound.sample_sha
        or set(selected)
        != (set(range(bound.notes)) if wanted is None else wanted)
    ):
        raise ValueError("sample contents differ from the bound artifact")
    return selected


def _has_usable_visible_subject_text(content: str) -> bool:
    residual = REFERENCE_TOKEN.sub(" ", content)
    residual = LONG_OPAQUE_TOKEN.sub(" ", residual)
    words = [
        word
        for word in VISIBLE_WORD.findall(residual)
        if len(word) >= 2
    ]
    return len(words) >= 4 and sum(map(len, words)) >= 20


def _materialize(
    topic_cases: list[dict[str, Any]],
    note_cases: list[dict[str, Any]],
    records: dict[int, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    topics = [
        {
            "topic_id": case["topic_id"],
            "learning_exemplars": [
                {**records[row], "weight": weight}
                for row, weight in case["learning_exemplars"]
            ],
            "probes": [
                {
                    **records[probe["row"]],
                    "weight": probe["weight"],
                    "stratum": probe["stratum"],
                    "presentation_order": probe["presentation_order"],
                }
                for probe in case["probes"]
            ],
        }
        for case in topic_cases
    ]
    notes = [
        {
            "note": records[case["row"]],
            "topic_cards": [
                {
                    "topic_id": card["topic_id"],
                    "weight": card["weight"],
                    "presentation_order": card["presentation_order"],
                    "learning_exemplars": [
                        {**records[exemplar], "weight": exemplar_weight}
                        for exemplar, exemplar_weight in card[
                            "learning_exemplars"
                        ]
                    ],
                }
                for card in case["topic_cards"]
            ],
        }
        for case in note_cases
    ]
    return topics, notes


def _note_text(content: str) -> str:
    normalized = (
        content.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u2028", "\n")
        .replace("\u2029", "\n")
    )
    visible = "".join(
        (
            character
            if character == "\n"
            or not unicodedata.category(character).startswith("C")
            else f"\\u{ord(character):04x}"
        )
        for character in normalized
    )
    return "    " + visible.replace("\n", "\n    ")


def _strength_scale() -> list[str]:
    return [
        "[ ] 1 — Not at all",
        "[ ] 2 — Probably not",
        "[ ] 3 — Partly/unclear",
        "[ ] 4 — Clearly",
        "[ ] 5 — Clearly and centrally",
    ]


VISIBLE_TEXT_RULE = (
    "Judge only the visible note text; do not open links or decode payloads."
)


def _topic_stage1_markdown(pilot: dict[str, Any]) -> bytes:
    lines = [
        "# Discarded CREC-113 topic procedure preview — stage 1",
        "",
        "Open this only after every note stage 1 subject list is frozen. "
        "Complete and freeze every coherence answer and phrase without opening "
        "the topic stage 2 preview. Do not treat any response as formal evidence.",
        "",
        VISIBLE_TEXT_RULE,
    ]
    for number, case in enumerate(pilot["topic_cases"], 1):
        lines += [
            "",
            f"## Topic case {number}",
            "",
            "### Learning exemplars",
            "",
        ]
        for exemplar_number, note in enumerate(
            case["learning_exemplars"], 1
        ):
            lines += [
                f"#### Exemplar {exemplar_number}",
                "",
                _note_text(note["content"]),
                "",
            ]
        lines += [
            "### Coherence judgment",
            "",
            "Do these notes express one substantive semantic subject—not merely "
            "the same author, language, style, format, or boilerplate?",
            "",
            "`Yes` means every exemplar shares at least one such subject. "
            "Additional unrelated subjects do not by themselves make the "
            "answer `No`.",
            "",
            "[ ] Yes  [ ] No  [ ] Unclear",
            "",
            "If Yes: Describe it in one short phrase.",
            "",
            "Phrase: ______________________________",
            "",
            "Freeze this answer and phrase before continuing. If No or Unclear, "
            "leave the corresponding stage 2 case blank.",
            "",
        ]
    return ("\n".join(lines) + "\n").encode()


def _topic_stage2_markdown(pilot: dict[str, Any]) -> bytes:
    lines = [
        "# Discarded CREC-113 topic procedure preview — stage 2",
        "",
        "Open this only after every stage 1 answer and phrase is frozen. Do not "
        "revise stage 1 after seeing these probes.",
        "",
        VISIBLE_TEXT_RULE,
    ]
    for number, case in enumerate(pilot["topic_cases"], 1):
        lines += [
            "",
            f"## Topic case {number}",
            "",
            "If your frozen stage 1 answer was No or Unclear, leave this "
            "case blank.",
            "",
        ]
        for probe_number, note in enumerate(case["probes"], 1):
            lines += [
                f"### Probe {probe_number}",
                "",
                _note_text(note["content"]),
                "",
                "How strongly does this note express [your phrase]?",
                "",
                *_strength_scale(),
                "",
            ]
    return ("\n".join(lines) + "\n").encode()


def _note_stage1_markdown(pilot: dict[str, Any]) -> bytes:
    lines = [
        "# Discarded CREC-113 note procedure preview — stage 1",
        "",
        "Open this file first, before any topic or stage 2 preview. Complete "
        "every subject list without opening another preview. "
        "Freeze your list before opening `note-stage2-preview.md`.",
        "",
        VISIBLE_TEXT_RULE,
        "Enter `Unclear/unobservable` if the visible text does not expose a "
        "subject.",
    ]
    for number, case in enumerate(pilot["note_cases"], 1):
        lines += [
            "",
            f"## Held-out note {number}",
            "",
            _note_text(case["note"]["content"]),
            "",
            "List its distinct substantive subjects that would matter for "
            "discovery, one short phrase each; enter none if there are none.",
            "",
            "Subjects:",
            "",
            "1. ______________________________",
            "2. ______________________________",
            "3. ______________________________",
            "(continue as needed)",
            "",
        ]
    return ("\n".join(lines) + "\n").encode()


def _note_stage2_markdown(pilot: dict[str, Any]) -> bytes:
    lines = [
        "# Discarded CREC-113 note procedure preview — stage 2",
        "",
        "Open this only after every note stage 1 subject list and every topic "
        "stage 1 answer and phrase are frozen. Use only the corresponding "
        "frozen subject list.",
        "",
        VISIBLE_TEXT_RULE,
    ]
    for number, case in enumerate(pilot["note_cases"], 1):
        lines += [
            "",
            f"## Held-out note {number}",
            "",
            _note_text(case["note"]["content"]),
            "",
        ]
        for card_number, card in enumerate(case["topic_cards"], 1):
            lines += [f"### Topic card {card_number}", ""]
            for exemplar_number, note in enumerate(
                card["learning_exemplars"], 1
            ):
                lines += [
                    f"#### Exemplar {exemplar_number}",
                    "",
                    _note_text(note["content"]),
                    "",
                ]
            lines += [
                "Which subject from your list does this topic represent?",
                "",
                "[ ] Subject: ______  [ ] None  [ ] Unclear",
                "",
                "If you selected None or Unclear, skip the strength scale.",
                "",
                "How strongly does the held-out note express "
                "[your selected subject]?",
                "",
                *_strength_scale(),
                "",
            ]
    return ("\n".join(lines) + "\n").encode()


def _note_only_markdown(pilot: dict[str, Any]) -> bytes:
    lines = [
        "# Discarded CREC-113 note-to-subject procedure preview",
        "",
        "This is a procedure test only. Do not treat any response as formal "
        "evidence.",
        "",
        VISIBLE_TEXT_RULE,
        "",
        "Judge every subject card independently. More than one card may be "
        "valid for the same held-out note.",
    ]
    for number, case in enumerate(pilot["note_cases"], 1):
        lines += [
            "",
            f"## Held-out note {number}",
            "",
            _note_text(case["note"]["content"]),
            "",
        ]
        for card_number, card in enumerate(case["topic_cards"], 1):
            lines += [f"### Subject card {card_number}", ""]
            for exemplar_number, note in enumerate(
                card["learning_exemplars"], 1
            ):
                lines += [
                    f"#### Exemplar {exemplar_number}",
                    "",
                    _note_text(note["content"]),
                    "",
                ]
            lines += [
                "Do these exemplars express one coherent substantive semantic "
                "subject?",
                "",
                "[ ] Yes  [ ] No  [ ] Unclear",
                "",
                "If No or Unclear, skip the next question.",
                "",
                "How strongly is that subject expressed in the held-out note?",
                "",
                "[ ] Absent  [ ] Incidental  [ ] Substantive  [ ] Central  "
                "[ ] Unclear",
                "",
            ]
    return ("\n".join(lines) + "\n").encode()


def _json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode()


def _publish(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"output path already exists: {path}")
    staging = Path(tempfile.mkdtemp(prefix=f".{path.name}.", dir=path.parent))
    try:
        for name, contents in files.items():
            with (staging / name).open("xb") as output:
                output.write(contents)
                output.flush()
                os.fsync(output.fileno())
        if path.exists():
            raise FileExistsError(f"output path already exists: {path}")
        os.rename(staging, path)
        staging = None
    finally:
        if staging is not None:
            shutil.rmtree(staging)


def generate_discarded_pilot(config: PilotConfig) -> dict[str, Any]:
    generator_path = Path(__file__).resolve()
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    seed = _validated_seed(config)
    if config.output_path.exists():
        raise FileExistsError(f"output path already exists: {config.output_path}")
    bound = _bind(config)
    root = config.relation_manifest_path.parent
    with ExitStack() as stack:
        relation_specs = {
            name: (size, digest)
            for name, size, digest in bound.relation_specs
        }
        maps = {
            name: _mapped_verified(
                stack, root / name, relation_specs[name]
            )
            for name in RELATION_FILES[:-1]
        }
        relation_ids = _mapped_verified(
            stack,
            root / "note-ids.bin",
            relation_specs["note-ids.bin"],
        )
        embedding_ids = _mapped_verified(
            stack,
            config.embedding_manifest_path.parent / "note-ids.bin",
            bound.embedding_ids_spec,
        )
        records = _records(bound, None, embedding_ids, relation_ids)
        visible_note_case_rows = frozenset(
            row
            for row in range(bound.learning, bound.notes)
            if _has_usable_visible_subject_text(records[row]["content"])
        )
        topic_cases, note_cases, _ = _select(
            bound,
            seed,
            maps,
            relation_ids,
            visible_note_case_rows,
        )
    topic_cases, note_cases = _materialize(topic_cases, note_cases, records)
    pilot = {
        "schema_version": 2,
        "discarded": True,
        "purpose": "procedure preview only; no quality conclusion",
        "selection_rule": PILOT_RULE,
        "case_structure": {
            "topic_cases": TOPIC_CASES,
            "note_cases": NOTE_CASES,
            "rank_domain": PILOT_RANK_DOMAIN.rstrip(b"\0").decode(),
            "topic_learning_exemplars": TOPIC_EXEMPLARS,
            "topic_probes": TOPIC_PROBES,
            "positive_probe_strata": list(TOPIC_PROBE_STRATA),
            "positive_probe_strata_rule": (
                "rank eligible positive-weight evaluation members by "
                "descending weight, divide the complete order into equal-count "
                "thirds, and select one deterministically from each third"
            ),
            "control_rule": (
                "select one structurally eligible evaluation note with no "
                "edge for the topic"
            ),
            "note_case_visible_text_rule": (
                "remove URI, Nostr-reference, and 64+-character opaque tokens; "
                "require at least four residual words of at least two letters "
                "and at least 20 residual letters in total; applies only to "
                "discarded-pilot note targets"
            ),
            "note_topic_cards": NOTE_TOPIC_CARDS,
            "topic_card_learning_exemplars": CARD_EXEMPLARS,
        },
        "topic_cases": topic_cases,
        "note_cases": note_cases,
    }
    pilot_bytes = _json(pilot)
    topic_stage1_markdown = _topic_stage1_markdown(pilot)
    topic_stage2_markdown = _topic_stage2_markdown(pilot)
    note_stage1_markdown = _note_stage1_markdown(pilot)
    note_stage2_markdown = _note_stage2_markdown(pilot)
    visible_notes = sorted(
        {
            note["note_id"]
            for case in topic_cases
            for note in case["learning_exemplars"] + case["probes"]
        }
        | {case["note"]["note_id"] for case in note_cases}
        | {
            note["note_id"]
            for case in note_cases
            for card in case["topic_cards"]
            for note in card["learning_exemplars"]
        }
    )
    visible_topics = sorted(
        {case["topic_id"] for case in topic_cases}
        | {
            card["topic_id"]
            for case in note_cases
            for card in case["topic_cards"]
        }
    )
    configuration = asdict(config)
    for key in tuple(configuration):
        if key.endswith("_path"):
            del configuration[key]
    manifest = {
        "schema_version": 1,
        "artifact_type": "discarded-topic-relation-procedure-preview-v5",
        "discarded": True,
        "selection_rule": PILOT_RULE,
        "runtime": {
            "generator_sha256": generator_sha256,
            "verification": "verified-before-and-after-generation-v1",
        },
        "configuration": configuration,
        "inputs": {
            "sample_manifest_sha256": bound.sample_manifest_sha,
            "sample_sha256": bound.sample_sha,
            "embedding_manifest_sha256": bound.embedding_manifest_sha,
            "relation_manifest_sha256": bound.relation_manifest_sha,
            "scale_preflight_note_ids_sha256": bound.excluded_sha,
            "excluded_scale_preflight_note_count": SCALE_PREFLIGHT_NOTES,
        },
        "future_formal_exclusions": {
            "note_ids": visible_notes,
            "topic_ids": visible_topics,
        },
        "files": {
            "pilot.json": {
                "bytes": len(pilot_bytes),
                "sha256": hashlib.sha256(pilot_bytes).hexdigest(),
            },
            "topic-stage1-preview.md": {
                "bytes": len(topic_stage1_markdown),
                "sha256": hashlib.sha256(
                    topic_stage1_markdown
                ).hexdigest(),
            },
            "topic-stage2-preview.md": {
                "bytes": len(topic_stage2_markdown),
                "sha256": hashlib.sha256(
                    topic_stage2_markdown
                ).hexdigest(),
            },
            "note-stage1-preview.md": {
                "bytes": len(note_stage1_markdown),
                "sha256": hashlib.sha256(
                    note_stage1_markdown
                ).hexdigest(),
            },
            "note-stage2-preview.md": {
                "bytes": len(note_stage2_markdown),
                "sha256": hashlib.sha256(
                    note_stage2_markdown
                ).hexdigest(),
            },
        },
    }
    if hashlib.sha256(generator_path.read_bytes()).hexdigest() != generator_sha256:
        raise ValueError("preview generator changed during generation")
    _publish(
        config.output_path,
        {
            "pilot.json": pilot_bytes,
            "topic-stage1-preview.md": topic_stage1_markdown,
            "topic-stage2-preview.md": topic_stage2_markdown,
            "note-stage1-preview.md": note_stage1_markdown,
            "note-stage2-preview.md": note_stage2_markdown,
            "manifest.json": _json(manifest),
        },
    )
    return manifest


def generate_note_only_pilot(config: PilotConfig) -> dict[str, Any]:
    generator_path = Path(__file__).resolve()
    generator_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    seed = _validated_seed(config)
    if config.output_path.exists():
        raise FileExistsError(f"output path already exists: {config.output_path}")
    bound = _bind(config)
    root = config.relation_manifest_path.parent
    with ExitStack() as stack:
        relation_specs = {
            name: (size, digest)
            for name, size, digest in bound.relation_specs
        }
        maps = {
            name: _mapped_verified(
                stack, root / name, relation_specs[name]
            )
            for name in RELATION_FILES[:-1]
        }
        relation_ids = _mapped_verified(
            stack,
            root / "note-ids.bin",
            relation_specs["note-ids.bin"],
        )
        embedding_ids = _mapped_verified(
            stack,
            config.embedding_manifest_path.parent / "note-ids.bin",
            bound.embedding_ids_spec,
        )
        records = _records(bound, None, embedding_ids, relation_ids)
        visible_note_case_rows = frozenset(
            row
            for row in range(bound.learning, bound.notes)
            if _has_usable_visible_subject_text(records[row]["content"])
        )
        topic_cases, note_cases, _ = _select(
            bound,
            seed,
            maps,
            relation_ids,
            visible_note_case_rows,
            topic_case_count=0,
        )
    if topic_cases:
        raise ValueError("note-only selection unexpectedly produced topic cases")
    _, note_cases = _materialize(topic_cases, note_cases, records)
    pilot = {
        "schema_version": 3,
        "discarded": True,
        "purpose": "note-to-subject procedure preview only; no quality conclusion",
        "selection_rule": NOTE_ONLY_PILOT_RULE,
        "case_structure": {
            "note_cases": NOTE_CASES,
            "rank_domain": PILOT_RANK_DOMAIN.rstrip(b"\0").decode(),
            "note_case_visible_text_rule": (
                "remove URI, Nostr-reference, and 64+-character opaque tokens; "
                "require at least four residual words of at least two letters "
                "and at least 20 residual letters in total; applies only to "
                "discarded-pilot note targets"
            ),
            "note_topic_cards": NOTE_TOPIC_CARDS,
            "topic_card_learning_exemplars": CARD_EXEMPLARS,
            "card_judgment": {
                "coherence": ["yes", "no", "unclear"],
                "membership_strength": [
                    "absent",
                    "incidental",
                    "substantive",
                    "central",
                    "unclear",
                ],
                "multiple_cards_may_be_valid": True,
            },
        },
        "note_cases": note_cases,
    }
    pilot_bytes = _json(pilot)
    note_markdown = _note_only_markdown(pilot)
    visible_notes = sorted(
        {case["note"]["note_id"] for case in note_cases}
        | {
            note["note_id"]
            for case in note_cases
            for card in case["topic_cards"]
            for note in card["learning_exemplars"]
        }
    )
    visible_topics = sorted(
        {
            card["topic_id"]
            for case in note_cases
            for card in case["topic_cards"]
        }
    )
    configuration = asdict(config)
    for key in tuple(configuration):
        if key.endswith("_path"):
            del configuration[key]
    manifest = {
        "schema_version": 1,
        "artifact_type": "discarded-note-topic-procedure-preview-v1",
        "discarded": True,
        "selection_rule": NOTE_ONLY_PILOT_RULE,
        "runtime": {
            "generator_sha256": generator_sha256,
            "verification": "verified-before-and-after-generation-v1",
        },
        "configuration": configuration,
        "inputs": {
            "sample_manifest_sha256": bound.sample_manifest_sha,
            "sample_sha256": bound.sample_sha,
            "embedding_manifest_sha256": bound.embedding_manifest_sha,
            "relation_manifest_sha256": bound.relation_manifest_sha,
            "scale_preflight_note_ids_sha256": bound.excluded_sha,
            "excluded_scale_preflight_note_count": SCALE_PREFLIGHT_NOTES,
        },
        "future_formal_exclusions": {
            "note_ids": visible_notes,
            "topic_ids": visible_topics,
        },
        "files": {
            "pilot.json": {
                "bytes": len(pilot_bytes),
                "sha256": hashlib.sha256(pilot_bytes).hexdigest(),
            },
            "note-preview.md": {
                "bytes": len(note_markdown),
                "sha256": hashlib.sha256(note_markdown).hexdigest(),
            },
        },
    }
    if hashlib.sha256(generator_path.read_bytes()).hexdigest() != generator_sha256:
        raise ValueError("preview generator changed during generation")
    _publish(
        config.output_path,
        {
            "pilot.json": pilot_bytes,
            "note-preview.md": note_markdown,
            "manifest.json": _json(manifest),
        },
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    for option in (
        "sample_manifest",
        "embedding_manifest",
        "relation_manifest",
        "scale_preflight_note_ids",
        "output",
    ):
        parser.add_argument("--" + option.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--seed-hex", required=True)
    parser.add_argument("--scale-preflight-note-ids-sha256", required=True)
    arguments = parser.parse_args()
    print(
        json.dumps(
            generate_note_only_pilot(
                PilotConfig(
                    sample_manifest_path=arguments.sample_manifest,
                    embedding_manifest_path=arguments.embedding_manifest,
                    relation_manifest_path=arguments.relation_manifest,
                    scale_preflight_note_ids_path=arguments.scale_preflight_note_ids,
                    scale_preflight_note_ids_sha256=(
                        arguments.scale_preflight_note_ids_sha256
                    ),
                    output_path=arguments.output,
                    seed_hex=arguments.seed_hex,
                )
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
