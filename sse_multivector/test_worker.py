import hashlib
import json
import math
import struct
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from sse_multivector.worker import (
    EncodedSubject,
    canonical_tree_sha256,
    select_token_indices,
    run_worker,
    validate_token_lengths,
)


class DeterministicEncoder:
    def __init__(self) -> None:
        self.calls = []

    def encode(self, notes):
        self.calls.append(notes)
        rows = []
        for note in notes:
            for subject in note.subjects:
                rows.append(
                    EncodedSubject(
                        note_id=note.note_id,
                        subject_id=subject.subject_id,
                        vector=(
                            float(len(note.text)),
                            float(len(subject.byte_spans)),
                            float(int(subject.subject_id[-1], 16) + 1),
                        ),
                        selected_token_indices=tuple(
                            range(1, len(subject.byte_spans) + 1)
                        ),
                        selected_token_ids=tuple(
                            range(101, 101 + len(subject.byte_spans))
                        ),
                        token_count=max(2, len(note.text)),
                    )
                )
        return rows


class WorkerTests(unittest.TestCase):
    def test_rejects_overlong_notes_instead_of_truncating_them(self):
        validate_token_lengths((("11" * 32, 512),), maximum_tokens=512)
        with self.assertRaisesRegex(
            ValueError, "tokenizes to 513 tokens.*truncation is forbidden"
        ):
            validate_token_lengths((("22" * 32, 513),), maximum_tokens=512)

    def test_maps_utf8_byte_spans_to_wholly_contained_non_special_tokens(self):
        text = "☕ Rust + Rust!"
        encoded = text.encode("utf-8")
        second_rust_start = encoded.rindex(b"Rust")
        second_rust_end = second_rust_start + len(b"Rust")
        offsets = [
            (0, 0),
            (0, 1),
            (2, 6),
            (7, 8),
            (9, 13),
            (13, 14),
            (0, 0),
        ]

        selected = select_token_indices(
            text,
            ((second_rust_start, second_rust_end),),
            offsets,
        )

        self.assertEqual((4,), selected)

    def test_unions_discontinuous_spans_but_rejects_empty_token_masks(self):
        text = "Rust while drinking tea"
        offsets = [(0, 4), (5, 10), (11, 19), (20, 23), (0, 0)]
        encoded = text.encode("utf-8")
        rust = (encoded.index(b"Rust"), encoded.index(b"Rust") + len(b"Rust"))
        tea = (encoded.index(b"tea"), encoded.index(b"tea") + len(b"tea"))

        self.assertEqual(
            (0, 3),
            select_token_indices(text, (rust, tea), offsets),
        )
        with self.assertRaisesRegex(ValueError, "selects no complete tokenizer token"):
            select_token_indices(text, ((1, 3),), offsets)

    def test_runs_one_grouped_request_and_publishes_bound_raw_vectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = {
                "schema_version": 1,
                "proposal_sha256": "ab" * 32,
                "notes": [
                    {
                        "note_id": "11" * 32,
                        "text": "Rust while drinking tea",
                        "subjects": [
                            {
                                "subject_id": "0000000000000001",
                                "byte_spans": [[0, 4]],
                            },
                            {
                                "subject_id": "0000000000000002",
                                "byte_spans": [[20, 23]],
                            },
                        ],
                    },
                    {
                        "note_id": "22" * 32,
                        "text": "Growing tomatoes!",
                        "subjects": [
                            {
                                "subject_id": "0000000000000003",
                                "byte_spans": [[0, 17]],
                            }
                        ],
                    },
                ],
            }
            request_path = root / "worker-input.json"
            request_bytes = (
                json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n"
            ).encode()
            request_path.write_bytes(request_bytes)
            checkpoint_path = root / "checkpoint.ckpt"
            checkpoint_path.write_bytes(b"official checkpoint fixture")
            tokenizer = root / "tokenizer"
            tokenizer.mkdir()
            (tokenizer / "tokenizer.json").write_text("{}\n")
            output = root / "worker-output"
            encoder = DeterministicEncoder()
            config = {
                "schema_version": 1,
                "request_path": str(request_path),
                "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                "checkpoint_path": str(checkpoint_path),
                "checkpoint_sha256": hashlib.sha256(
                    checkpoint_path.read_bytes()
                ).hexdigest(),
                "base_model_artifact_path": str(tokenizer),
                "base_model_artifact_tree_sha256": canonical_tree_sha256(tokenizer),
                "model": {
                    "base_model": "fixture/sentence-encoder",
                    "dimensions": 3,
                    "maximum_tokens": 512,
                    "pooling": ("selected-contextual-token-mean-linear-relu-linear-v1"),
                },
                "device": "cpu",
                "container_image": "sha256:" + ("ef" * 32),
                "note_batch_size": 2,
                "output_path": str(output),
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config, sort_keys=True) + "\n")

            with patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=encoder,
            ):
                report = run_worker(config_path)

            self.assertEqual(1, len(encoder.calls))
            self.assertEqual(2, len(encoder.calls[0]))
            self.assertEqual(3, report.row_count)
            self.assertEqual(3, report.dimensions)
            values = struct.unpack("<9f", (output / "raw-vectors.f32le").read_bytes())
            self.assertTrue(all(math.isfinite(value) for value in values))
            self.assertEqual(
                (
                    23.0,
                    1.0,
                    2.0,
                    23.0,
                    1.0,
                    3.0,
                    17.0,
                    1.0,
                    4.0,
                ),
                values,
            )
            receipt = json.loads((output / "worker-receipt.json").read_text())
            self.assertEqual(
                ["0000000000000001", "0000000000000002", "0000000000000003"],
                [row["subject_id"] for row in receipt["rows"]],
            )
            self.assertEqual(
                [23, 23, 17], [row["token_count"] for row in receipt["rows"]]
            )
            self.assertEqual(
                [[101], [101], [101]],
                [row["selected_token_ids"] for row in receipt["rows"]],
            )
            self.assertEqual(
                hashlib.sha256((output / "raw-vectors.f32le").read_bytes()).hexdigest(),
                receipt["files"]["raw-vectors.f32le"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256(request_bytes).hexdigest(),
                receipt["request_sha256"],
            )
            self.assertEqual(
                "sha256:" + ("ef" * 32),
                receipt["container_image"],
            )

    def test_rejects_labels_in_the_encoder_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = {
                "schema_version": 1,
                "proposal_sha256": "ab" * 32,
                "notes": [
                    {
                        "note_id": "11" * 32,
                        "text": "Rust",
                        "subjects": [
                            {
                                "subject_id": "0000000000000001",
                                "label": "Rust programming",
                                "byte_spans": [[0, 4]],
                            }
                        ],
                    }
                ],
            }
            request_path = root / "request.json"
            request_bytes = (
                json.dumps(request, ensure_ascii=False, sort_keys=True) + "\n"
            ).encode()
            request_path.write_bytes(request_bytes)
            checkpoint = root / "checkpoint.ckpt"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer = root / "tokenizer"
            tokenizer.mkdir()
            (tokenizer / "tokenizer.json").write_text("{}")
            config = {
                "schema_version": 1,
                "request_path": str(request_path),
                "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
                "checkpoint_path": str(checkpoint),
                "checkpoint_sha256": hashlib.sha256(
                    checkpoint.read_bytes()
                ).hexdigest(),
                "base_model_artifact_path": str(tokenizer),
                "base_model_artifact_tree_sha256": canonical_tree_sha256(tokenizer),
                "model": {
                    "base_model": "fixture/sentence-encoder",
                    "dimensions": 3,
                    "maximum_tokens": 512,
                    "pooling": ("selected-contextual-token-mean-linear-relu-linear-v1"),
                },
                "device": "cpu",
                "container_image": "fixture/sse@sha256:" + ("ef" * 32),
                "note_batch_size": 1,
                "output_path": str(root / "output"),
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config, sort_keys=True) + "\n")

            with patch(
                "sse_multivector.worker.OfficialSseEncoder",
                return_value=DeterministicEncoder(),
            ):
                with self.assertRaisesRegex(ValueError, "unexpected field.*label"):
                    run_worker(config_path)


if __name__ == "__main__":
    unittest.main()
