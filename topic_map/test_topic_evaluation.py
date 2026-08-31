#!/usr/bin/env python3
"""Production-path tests for the discarded CREC-113 procedure preview."""

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import topic_map.topic_evaluation as topic_evaluation
from topic_map.topic_evaluation import PilotConfig, generate_discarded_pilot


def _json_bytes(value: object) -> bytes:
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


def _sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _write(path: Path, contents: bytes) -> dict[str, int | str]:
    path.write_bytes(contents)
    return {"bytes": len(contents), "sha256": _sha256(contents)}


def _note_id(number: int) -> bytes:
    return number.to_bytes(32, "big")


def _build_artifacts(root: Path) -> tuple[Path, Path, Path, Path]:
    sample = root / "sample"
    embeddings = root / "embeddings"
    relation = root / "relation"
    sample.mkdir()
    embeddings.mkdir()
    relation.mkdir()

    records = [
        {
            "split": "learning",
            "note_id": _note_id(index).hex(),
            "pubkey": _note_id(100 + index).hex(),
            "content": f"learning note {index}",
        }
        for index in range(1, 13)
    ] + [
        {
            "split": "evaluation",
            "note_id": _note_id(index).hex(),
            "pubkey": _note_id(100 + index).hex(),
            "content": (
                f"### forged heading {index}\n"
                "<script>not markup</script>\n"
                "\x1b[31mred"
                if index >= 23
                else f"evaluation note {index}"
            ),
        }
        for index in range(13, 37)
    ]
    sample_bytes = b"".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True).encode() + b"\n"
        for record in records
    )
    sample_spec = _write(sample / "sample.jsonl", sample_bytes)
    sample_manifest = {
        "schema_version": 3,
        "selection_rule": (
            "semantic-order-prefix-author-hash-text-copy-disjoint-"
            "learning-first-v2"
        ),
        "learning_rows": 12,
        "evaluation_rows": 24,
        "sample": {
            "file": "sample.jsonl",
            "records": 36,
            **sample_spec,
        },
    }
    sample_manifest_bytes = _json_bytes(sample_manifest)
    (sample / "manifest.json").write_bytes(sample_manifest_bytes)

    note_ids = b"".join(_note_id(index) for index in range(1, 37))
    note_ids_spec = _write(embeddings / "note-ids.bin", note_ids)
    # The binder does not read the vector matrix. The relation binds its
    # encoder-produced digest, while NoteId order is checked directly.
    vectors = b"x" * (36 * 4)
    (embeddings / "vectors.f32le").write_bytes(vectors)
    declared_vector_sha256 = "a" * 64
    embedding_manifest = {
        "schema_version": 1,
        "embedding_format": "learning-first-note-embedding-matrix-v1",
        "sample_manifest_sha256": _sha256(sample_manifest_bytes),
        "sample_sha256": sample_spec["sha256"],
        "sample_selection_rule": sample_manifest["selection_rule"],
        "learning_rows": 12,
        "evaluation_rows": 24,
        "total_rows": 36,
        "encoder": {"dimensions": 1, "numeric_type": "float32"},
        "files": {
            "vectors.f32le": {
                "bytes": len(vectors),
                "sha256": declared_vector_sha256,
            },
            "note-ids.bin": note_ids_spec,
        },
    }
    embedding_manifest_bytes = _json_bytes(embedding_manifest)
    (embeddings / "manifest.json").write_bytes(embedding_manifest_bytes)

    # One canonical note-major sparse relation. Evaluation notes 23 onward
    # deliberately have three topics and are structurally complete note cases.
    by_note: list[list[tuple[int, float]]] = [
        [(0, 0.9), (1, 0.1)],
        [(0, 0.8)],
        [(0, 0.7), (2, 0.3)],
        [(1, 0.9), (0, 0.1)],
        [(1, 0.8)],
        [(1, 0.7), (2, 0.3)],
        [(2, 0.9)],
        [(2, 0.8)],
        [(2, 0.7), (0, 0.3)],
        [(3, 1.0)],
        [(3, 1.0)],
        [(3, 1.0)],
        [(0, 0.95), (1, 0.05)],
        [(0, 0.9), (1, 0.1)],
        [(0, 0.6), (2, 0.4)],
        [(3, 0.8), (0, 0.2)],
        [(1, 0.9), (2, 0.1)],
        [(1, 0.6), (3, 0.4)],
        [(2, 0.8), (1, 0.2)],
        [(2, 0.9), (0, 0.1)],
        [(2, 0.6), (1, 0.4)],
        [(3, 0.8), (2, 0.2)],
        [(0, 0.4), (1, 0.35), (2, 0.25)],
        [(2, 0.5), (1, 0.3), (0, 0.2)],
    ]
    by_note.extend(
        [
            [
                (rotation % 3, 0.5),
                ((rotation + 1) % 3, 0.3),
                ((rotation + 2) % 3, 0.2),
            ]
            for rotation in range(12)
        ]
    )
    note_offsets = [0]
    topic_ids: list[int] = []
    weights: list[float] = []
    edge_rows: list[int] = []
    for row, edges in enumerate(by_note):
        for topic, weight in edges:
            topic_ids.append(topic)
            weights.append(weight)
            edge_rows.append(row)
        note_offsets.append(len(topic_ids))
    topic_edge_order = sorted(
        range(len(topic_ids)),
        key=lambda edge: (-weights[edge], edge_rows[edge], edge),
    )
    topic_edge_order = sorted(
        topic_edge_order, key=lambda edge: topic_ids[edge]
    )
    topic_offsets = [0]
    for topic in range(4):
        topic_offsets.append(
            topic_offsets[-1]
            + sum(topic_ids[edge] == topic for edge in topic_edge_order)
        )
    relation_files: dict[str, bytes] = {
        "note-offsets.u64le": struct.pack(
            f"<{len(note_offsets)}Q", *note_offsets
        ),
        "topic-ids.u32le": struct.pack(
            f"<{len(topic_ids)}I", *topic_ids
        ),
        "weights.f32le": struct.pack(f"<{len(weights)}f", *weights),
        "topic-offsets.u64le": struct.pack(
            f"<{len(topic_offsets)}Q", *topic_offsets
        ),
        "topic-edge-order.u64le": struct.pack(
            f"<{len(topic_edge_order)}Q", *topic_edge_order
        ),
        "source-topic-ids.u32le": struct.pack("<4I", 10, 20, 30, 40),
        "note-ids.bin": note_ids,
    }
    relation_specs = {
        name: _write(relation / name, contents)
        for name, contents in relation_files.items()
    }
    relation_manifest = {
        "schema_version": 1,
        "relation_format": "canonical-sparse-note-topic-relation-v1",
        "note_count": 36,
        "topic_count": 4,
        "entry_count": len(topic_ids),
        "weight_semantics": "positive activation normalized within each note",
        "topic_semantics": (
            "compact IDs for features active on at least one learning note"
        ),
        "metadata": {
            "learning_rows": 12,
            "evaluation_rows": 24,
            "start_row": 0,
            "matrix_range_sha256": declared_vector_sha256,
            "note_ids_range_sha256": note_ids_spec["sha256"],
            "embedding_manifest_sha256": _sha256(
                embedding_manifest_bytes
            ),
        },
        "files": relation_specs,
    }
    (relation / "manifest.json").write_bytes(_json_bytes(relation_manifest))

    excluded = root / "scale-preflight-note-ids.bin"
    excluded_ids = [_note_id(2), _note_id(13)] + [
        _note_id(10_000 + index) for index in range(5_118)
    ]
    excluded.write_bytes(b"".join(excluded_ids))
    return (
        sample / "manifest.json",
        embeddings / "manifest.json",
        relation / "manifest.json",
        excluded,
    )


def _config(
    sample: Path,
    embeddings: Path,
    relation: Path,
    excluded: Path,
    output: Path,
) -> PilotConfig:
    return PilotConfig(
        sample_manifest_path=sample,
        embedding_manifest_path=embeddings,
        relation_manifest_path=relation,
        scale_preflight_note_ids_path=excluded,
        scale_preflight_note_ids_sha256=_sha256(excluded.read_bytes()),
        output_path=output,
        seed_hex="12" * 32,
    )


class TopicEvaluationTest(unittest.TestCase):
    def test_generates_bounded_note_only_discarded_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            first_output = root / "note-only-a"
            first = topic_evaluation.generate_note_only_pilot(
                _config(
                    sample, embeddings, relation, excluded, first_output
                )
            )
            second_output = root / "note-only-b"
            second = topic_evaluation.generate_note_only_pilot(
                _config(
                    sample, embeddings, relation, excluded, second_output
                )
            )

            self.assertEqual(first, second)
            self.assertEqual(
                {"pilot.json", "note-preview.md", "manifest.json"},
                {path.name for path in first_output.iterdir()},
            )
            for filename in ("pilot.json", "note-preview.md", "manifest.json"):
                self.assertEqual(
                    (first_output / filename).read_bytes(),
                    (second_output / filename).read_bytes(),
                )

            pilot = json.loads((first_output / "pilot.json").read_text())
            self.assertTrue(pilot["discarded"])
            self.assertNotIn("topic_cases", pilot)
            self.assertEqual(2, len(pilot["note_cases"]))
            for case in pilot["note_cases"]:
                self.assertEqual(3, len(case["topic_cards"]))
                self.assertEqual(
                    [1, 2, 3],
                    [
                        card["presentation_order"]
                        for card in case["topic_cards"]
                    ],
                )

            preview = (first_output / "note-preview.md").read_text()
            self.assertIn(
                "Judge only the visible note text; do not open links or "
                "decode payloads.",
                preview,
            )
            self.assertIn(
                "Do these exemplars express one coherent substantive "
                "semantic subject?",
                preview,
            )
            self.assertIn("[ ] Yes  [ ] No  [ ] Unclear", preview)
            self.assertIn(
                "How strongly is that subject expressed in the held-out note?",
                preview,
            )
            self.assertIn(
                "[ ] Absent  [ ] Incidental  [ ] Substantive  [ ] Central  "
                "[ ] Unclear",
                preview,
            )
            self.assertNotIn("List its distinct substantive subjects", preview)
            self.assertNotIn("Subjects:", preview)
            self.assertNotIn("stage 2", preview.lower())
            self.assertNotIn("TopicId", preview)
            self.assertNotIn("NoteId", preview)
            self.assertNotIn("weight", preview.lower())

            visible_note_ids = {
                case["note"]["note_id"] for case in pilot["note_cases"]
            } | {
                note["note_id"]
                for case in pilot["note_cases"]
                for card in case["topic_cards"]
                for note in card["learning_exemplars"]
            }
            visible_topic_ids = {
                card["topic_id"]
                for case in pilot["note_cases"]
                for card in case["topic_cards"]
            }
            manifest = json.loads(
                (first_output / "manifest.json").read_text()
            )
            self.assertEqual(
                "discarded-note-topic-procedure-preview-v1",
                manifest["artifact_type"],
            )
            self.assertEqual(
                visible_note_ids,
                set(manifest["future_formal_exclusions"]["note_ids"]),
            )
            self.assertEqual(
                visible_topic_ids,
                set(manifest["future_formal_exclusions"]["topic_ids"]),
            )

    def test_generates_blinded_deterministic_discarded_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            first_output = root / "pilot-a"
            first = generate_discarded_pilot(
                _config(
                    sample, embeddings, relation, excluded, first_output
                )
            )
            second_output = root / "pilot-b"
            second = generate_discarded_pilot(
                _config(
                    sample, embeddings, relation, excluded, second_output
                )
            )

            self.assertEqual(first, second)
            filenames = {
                "pilot.json",
                "topic-stage1-preview.md",
                "topic-stage2-preview.md",
                "note-stage1-preview.md",
                "note-stage2-preview.md",
                "manifest.json",
            }
            self.assertEqual(
                filenames, {path.name for path in first_output.iterdir()}
            )
            for filename in filenames:
                self.assertEqual(
                    (first_output / filename).read_bytes(),
                    (second_output / filename).read_bytes(),
                )

            pilot = json.loads((first_output / "pilot.json").read_text())
            self.assertTrue(pilot["discarded"])
            self.assertEqual(len(pilot["topic_cases"]), 3)
            self.assertEqual(len(pilot["note_cases"]), 2)
            for case in pilot["topic_cases"]:
                self.assertEqual(len(case["learning_exemplars"]), 3)
                self.assertEqual(len(case["probes"]), 4)
                self.assertEqual(
                    {probe["stratum"] for probe in case["probes"]},
                    {"high", "middle", "low", "absent_control"},
                )
                self.assertEqual(
                    [probe["presentation_order"] for probe in case["probes"]],
                    [1, 2, 3, 4],
                )
                by_stratum = {
                    probe["stratum"]: probe for probe in case["probes"]
                }
                self.assertGreaterEqual(
                    by_stratum["high"]["weight"],
                    by_stratum["middle"]["weight"],
                )
                self.assertGreaterEqual(
                    by_stratum["middle"]["weight"],
                    by_stratum["low"]["weight"],
                )
                self.assertGreater(by_stratum["low"]["weight"], 0)
                self.assertEqual(
                    by_stratum["absent_control"]["weight"], 0
                )
                self.assertEqual(
                    len({probe["note_id"] for probe in case["probes"]}), 4
                )
                for probe in case["probes"]:
                    self.assertIn("weight", probe)
            for case in pilot["note_cases"]:
                self.assertEqual(len(case["topic_cards"]), 3)
                self.assertEqual(
                    [card["presentation_order"] for card in case["topic_cards"]],
                    [1, 2, 3],
                )
                for card in case["topic_cards"]:
                    self.assertIn("topic_id", card)
                    self.assertIn("weight", card)
                    self.assertEqual(len(card["learning_exemplars"]), 3)
            topic_probe_ids = {
                probe["note_id"]
                for case in pilot["topic_cases"]
                for probe in case["probes"]
            }
            note_target_ids = {
                case["note"]["note_id"] for case in pilot["note_cases"]
            }
            self.assertTrue(topic_probe_ids.isdisjoint(note_target_ids))

            topic_stage1 = (
                first_output / "topic-stage1-preview.md"
            ).read_text()
            topic_stage2 = (
                first_output / "topic-stage2-preview.md"
            ).read_text()
            self.assertIn(
                "Do these notes express one substantive semantic subject—not "
                "merely the same author, language, style, format, or boilerplate?",
                topic_stage1,
            )
            self.assertIn("[ ] Yes  [ ] No  [ ] Unclear", topic_stage1)
            self.assertNotIn("Probe 1", topic_stage1)
            self.assertNotIn("How strongly", topic_stage1)
            self.assertIn(
                "How strongly does this note express [your phrase]?",
                topic_stage2,
            )
            self.assertIn(
                "If your frozen stage 1 answer was No or Unclear, leave this "
                "case blank.",
                topic_stage2,
            )
            self.assertNotIn("learning note", topic_stage2)
            self.assertIn("1 — Not at all", topic_stage2)
            self.assertIn("5 — Clearly and centrally", topic_stage2)

            stage1 = (
                first_output / "note-stage1-preview.md"
            ).read_text()
            self.assertIn(
                "List its distinct substantive subjects that would matter for "
                "discovery, one short phrase each; enter none if there are none.",
                stage1,
            )
            self.assertIn(
                "Open this file first, before any topic or stage 2 preview.",
                stage1,
            )
            self.assertIn(
                "Freeze your list before opening `note-stage2-preview.md`.",
                stage1,
            )
            self.assertNotIn("Topic card", stage1)
            self.assertIn(
                "Open this only after every note stage 1 subject list is frozen.",
                topic_stage1,
            )

            stage2 = (
                first_output / "note-stage2-preview.md"
            ).read_text()
            self.assertIn(
                "Open this only after every note stage 1 subject list and every "
                "topic stage 1 answer and phrase are frozen.",
                stage2,
            )
            self.assertIn(
                "Which subject from your list does this topic represent?",
                stage2,
            )
            self.assertIn("[ ] Subject: ______  [ ] None  [ ] Unclear", stage2)
            self.assertIn(
                "If you selected None or Unclear, skip the strength scale.",
                stage2,
            )
            self.assertIn("    ### forged heading", stage2)
            self.assertIn(
                "How strongly does the held-out note express "
                "[your selected subject]?",
                stage2,
            )
            visible_text_rule = (
                "Judge only the visible note text; do not open links or "
                "decode payloads."
            )
            for preview in (topic_stage1, topic_stage2, stage1, stage2):
                self.assertIn(visible_text_rule, preview)

            # Identifiers, hidden strata, and weights remain machine-readable
            # but cannot prime the evaluator through any preview document.
            all_markdown = topic_stage1 + topic_stage2 + stage1 + stage2
            self.assertNotIn("TopicId", all_markdown)
            self.assertNotIn("NoteId", all_markdown)
            self.assertNotIn("absent_control", all_markdown)
            self.assertNotIn("stratum", all_markdown.lower())
            self.assertNotIn("weight", all_markdown.lower())
            self.assertNotIn("\x1b", all_markdown)

            selected_note = pilot["note_cases"][0]["note"]
            selected_number = int(selected_note["note_id"], 16)
            self.assertEqual(
                selected_note["content"],
                f"### forged heading {selected_number}\n"
                "<script>not markup</script>\n\x1b[31mred",
            )
            self.assertNotIn(
                f"\n### forged heading {selected_number}\n", stage1
            )
            self.assertNotIn("\x1b", stage1)
            self.assertIn(
                f"    ### forged heading {selected_number}", stage1
            )
            self.assertIn(r"\u001b[31mred", stage1)

            visible_note_ids = {
                note["note_id"]
                for case in pilot["topic_cases"]
                for note in case["learning_exemplars"] + case["probes"]
            } | {
                case["note"]["note_id"] for case in pilot["note_cases"]
            } | {
                note["note_id"]
                for case in pilot["note_cases"]
                for card in case["topic_cards"]
                for note in card["learning_exemplars"]
            }
            self.assertNotIn(_note_id(2).hex(), visible_note_ids)
            self.assertNotIn(_note_id(13).hex(), visible_note_ids)
            manifest = json.loads(
                (first_output / "manifest.json").read_text()
            )
            self.assertEqual(
                "discarded-topic-relation-procedure-preview-v5",
                manifest["artifact_type"],
            )
            self.assertEqual(
                set(manifest["future_formal_exclusions"]["note_ids"]),
                visible_note_ids,
            )
            visible_topic_ids = {
                case["topic_id"] for case in pilot["topic_cases"]
            } | {
                card["topic_id"]
                for case in pilot["note_cases"]
                for card in case["topic_cards"]
            }
            self.assertEqual(
                set(manifest["future_formal_exclusions"]["topic_ids"]),
                visible_topic_ids,
            )

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                generate_discarded_pilot(
                    _config(
                        sample,
                        embeddings,
                        relation,
                        excluded,
                        first_output,
                    )
                )

    def test_filters_incomplete_cases_but_fails_if_quota_cannot_fill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            excluded_ids = [
                excluded.read_bytes()[offset : offset + 32]
                for offset in range(0, excluded.stat().st_size, 32)
            ]
            excluded_ids[-13:] = [
                _note_id(index) for index in range(23, 36)
            ]
            excluded.write_bytes(b"".join(excluded_ids))
            with self.assertRaisesRegex(
                ValueError, "only 0 structurally eligible note cases"
            ):
                generate_discarded_pilot(
                    _config(
                        sample,
                        embeddings,
                        relation,
                        excluded,
                        root / "pilot",
                    )
                )

    def test_note_cases_skip_opaque_payloads_but_topic_cases_may_retain_them(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            sample_path = sample.parent / "sample.jsonl"
            records = [
                json.loads(line)
                for line in sample_path.read_text().splitlines()
            ]
            for record in records:
                number = int(record["note_id"], 16)
                if number == 24:
                    record["content"] = (
                        "Rust compiler diagnostics can teach clearer error "
                        "handling."
                    )
                elif number == 25:
                    record["content"] = (
                        "Local food cooperatives make neighborhood supply "
                        "chains more resilient."
                    )
                elif number >= 13:
                    record["content"] = (
                        f"https://example.com/opaque-only/{number}"
                    )
            sample_bytes = b"".join(
                json.dumps(
                    record, ensure_ascii=False, sort_keys=True
                ).encode()
                + b"\n"
                for record in records
            )
            sample_path.write_bytes(sample_bytes)
            sample_manifest = json.loads(sample.read_text())
            sample_manifest["sample"].update(
                {
                    "bytes": len(sample_bytes),
                    "sha256": _sha256(sample_bytes),
                }
            )
            sample_bytes_manifest = _json_bytes(sample_manifest)
            sample.write_bytes(sample_bytes_manifest)

            embedding_manifest = json.loads(embeddings.read_text())
            embedding_manifest.update(
                {
                    "sample_manifest_sha256": _sha256(
                        sample_bytes_manifest
                    ),
                    "sample_sha256": _sha256(sample_bytes),
                }
            )
            embedding_bytes = _json_bytes(embedding_manifest)
            embeddings.write_bytes(embedding_bytes)
            relation_manifest = json.loads(relation.read_text())
            relation_manifest["metadata"]["embedding_manifest_sha256"] = (
                _sha256(embedding_bytes)
            )
            relation.write_bytes(_json_bytes(relation_manifest))

            output = root / "pilot"
            generate_discarded_pilot(
                _config(sample, embeddings, relation, excluded, output)
            )
            pilot = json.loads((output / "pilot.json").read_text())

            note_case_ids = {
                int(case["note"]["note_id"], 16)
                for case in pilot["note_cases"]
            }
            self.assertEqual({24, 25}, note_case_ids)
            self.assertTrue(
                any(
                    probe["content"].startswith("https://")
                    for case in pilot["topic_cases"]
                    for probe in case["probes"]
                )
            )

    def test_note_stage_one_limits_judgment_to_visible_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            output = root / "pilot"
            generate_discarded_pilot(
                _config(sample, embeddings, relation, excluded, output)
            )

            stage_one = (output / "note-stage1-preview.md").read_text()
            self.assertIn(
                "Judge only the visible note text; do not open links or "
                "decode payloads.",
                stage_one,
            )
            self.assertIn(
                "Enter `Unclear/unobservable` if the visible text does not "
                "expose a subject.",
                stage_one,
            )

    def test_topic_coherence_allows_unrelated_additional_subjects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            output = root / "pilot"
            generate_discarded_pilot(
                _config(sample, embeddings, relation, excluded, output)
            )

            stage_one = (output / "topic-stage1-preview.md").read_text()
            self.assertIn(
                "`Yes` means every exemplar shares at least one such subject. "
                "Additional unrelated subjects do not by themselves make the "
                "answer `No`.",
                stage_one,
            )

    def test_manifest_binds_the_exact_preview_generator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            output = root / "pilot"
            generate_discarded_pilot(
                _config(sample, embeddings, relation, excluded, output)
            )

            manifest = json.loads((output / "manifest.json").read_text())
            expected = _sha256(Path(topic_evaluation.__file__).read_bytes())
            self.assertEqual(
                expected, manifest["runtime"]["generator_sha256"]
            )

    def test_rejects_well_formed_but_wrong_preflight_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            expected_exclusion_sha256 = _sha256(excluded.read_bytes())
            excluded.write_bytes(
                b"".join(_note_id(20_000 + index) for index in range(5_120))
            )
            config = _config(
                sample, embeddings, relation, excluded, root / "pilot"
            )
            config = PilotConfig(
                **{
                    **config.__dict__,
                    "scale_preflight_note_ids_sha256": (
                        expected_exclusion_sha256
                    ),
                }
            )
            with self.assertRaisesRegex(ValueError, "exclusion hash"):
                generate_discarded_pilot(config)

    def test_rejects_relation_bound_to_another_embedding_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            relation_manifest = json.loads(relation.read_text())
            relation_manifest["metadata"]["embedding_manifest_sha256"] = "0" * 64
            relation.write_bytes(_json_bytes(relation_manifest))
            with self.assertRaisesRegex(ValueError, "exact embedding"):
                generate_discarded_pilot(
                    _config(
                        sample,
                        embeddings,
                        relation,
                        excluded,
                        root / "pilot",
                    )
                )

    def test_rejects_relation_note_order_that_differs_from_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            relation_root = relation.parent
            malformed = _note_id(2) + _note_id(1) + b"".join(
                _note_id(index) for index in range(3, 37)
            )
            (relation_root / "note-ids.bin").write_bytes(malformed)
            relation_manifest = json.loads(relation.read_text())
            relation_manifest["files"]["note-ids.bin"] = {
                "bytes": len(malformed),
                "sha256": _sha256(malformed),
            }
            relation.write_bytes(_json_bytes(relation_manifest))
            with self.assertRaisesRegex(
                ValueError, "relation NoteId order differs from the sample"
            ):
                generate_discarded_pilot(
                    _config(
                        sample,
                        embeddings,
                        relation,
                        excluded,
                        root / "pilot",
                    )
                )

    def test_relation_bytes_used_for_selection_are_exactly_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sample, embeddings, relation, excluded = _build_artifacts(root)
            original_bind = topic_evaluation._bind

            def replace_after_bind(config: PilotConfig):
                bound = original_bind(config)
                weights_path = relation.parent / "weights.f32le"
                contents = bytearray(weights_path.read_bytes())
                contents[:4] = struct.pack("<f", 0.85)
                weights_path.write_bytes(contents)
                return bound

            with mock.patch.object(
                topic_evaluation, "_bind", side_effect=replace_after_bind
            ):
                with self.assertRaisesRegex(
                    ValueError, "weights.f32le.*manifest"
                ):
                    generate_discarded_pilot(
                        _config(
                            sample,
                            embeddings,
                            relation,
                            excluded,
                            root / "pilot",
                        )
                    )


if __name__ == "__main__":
    unittest.main()
