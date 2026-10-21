import copy
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def identity(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


class ExactMaskDeduplicationCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        text = "☕ Rust / Rust"
        masks = [
            (["☕", "Rust"], [[0, 3], [11, 15]]),
            (["☕", "Rust"], [[0, 3], [11, 15]]),
            (["Rust"], [[4, 8]]),
            (["Rust"], [[11, 15]]),
            (["☕ Rust"], [[0, 8]]),
            (["☕", " Rust"], [[0, 3], [3, 8]]),
        ]
        subjects = [
            {
                "id": f"S{index + 1}",
                "subject": f"Original subject {index + 1}.",
                "judgment": "accepted",
                "fragments": fragments,
                "byte_spans": spans,
                "raw_mask": json.dumps(fragments, ensure_ascii=False),
            }
            for index, (fragments, spans) in enumerate(masks)
        ]
        self.document = {
            "schema_version": 1,
            "notes": [
                {
                    "note_id": "f1" * 32,
                    "text": text,
                    "deduplicate_identical_masks": True,
                    "subjects": subjects,
                },
                {
                    "note_id": "f2" * 32,
                    "text": text,
                    "deduplicate_identical_masks": True,
                    "subjects": copy.deepcopy(subjects[:1]),
                },
                {
                    "note_id": "f3" * 32,
                    "text": text,
                    "subjects": copy.deepcopy(subjects[:2]),
                },
            ],
        }
        self.document["notes"][0]["subjects"].extend(
            [
                {"id": "S7", "subject": "Rejected.", "judgment": "rejected"},
                {"id": "S8", "subject": "Unresolved.", "judgment": "unresolved"},
            ]
        )
        self.encoder = self.root / "encoder.json"
        self.subject_package = self.root / "subject-package.json"
        self.mask_package = self.root / "mask-package.json"
        write(self.encoder, {
            "schema_version": 1,
            "checkpoint_path": "unused/checkpoint", "checkpoint_sha256": "a" * 64,
            "base_model_artifact_path": "unused/model",
            "base_model_artifact_tree_sha256": "b" * 64,
            "worker_path": "sse_multivector/worker.py", "worker_sha256": "c" * 64,
            "container_image": "sha256:" + "d" * 64, "note_batch_size": 8,
            "model": {"base_model": "sentence-transformers/sentence-t5-base",
                      "dimensions": 2, "maximum_tokens": 512,
                      "pooling": "selected-contextual-token-mean-linear-relu-linear-v1"},
        })
        write(self.subject_package, {"status": "frozen", "version": "ASv6.23"})
        write(self.mask_package, {"status": "frozen", "version": "MPv3.5"})

    def cli(self, *arguments, success=True):
        result = subprocess.run(
            [sys.executable, *map(str, arguments)],
            cwd=ROOT,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if success:
            self.assertEqual(0, result.returncode, result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, result.stdout)
        return result

    def prepare(self, document, name, *, success=True):
        reviewed = self.root / f"{name}.json"
        write(reviewed, document)
        prepared = self.root / name
        result = self.cli(
            "-m",
            "sse_multivector.real_note_segmentation",
            "prepare",
            reviewed,
            self.encoder,
            self.subject_package,
            self.mask_package,
            prepared,
            success=success,
        )
        return prepared, result

    def finalize(self, prepared, name):
        worker = self.root / f"{name}-worker"
        worker.mkdir()
        request = read(prepared / "worker-request.json")
        encoder = read(prepared / "encoder.json")
        dimensions = encoder["model"]["dimensions"]
        rows, raw = [], bytearray()
        for note in request["notes"]:
            for subject in note["subjects"]:
                ordinal = len(rows)
                coordinates = [0.0] * dimensions
                coordinates[ordinal % dimensions] = 1.0
                raw.extend(struct.pack(f"<{dimensions}f", *coordinates))
                rows.append(
                    {
                        "ordinal": ordinal,
                        "note_id": note["note_id"],
                        "subject_id": subject["subject_id"],
                        "selected_token_indices": [1],
                        "selected_token_ids": [101],
                        "token_count": 8,
                    }
                )
        (worker / "raw-vectors.f32le").write_bytes(raw)
        receipt = {
            "schema_version": 1,
            "proposal_sha256": request["proposal_sha256"],
            "request_sha256": identity(prepared / "worker-request.json")["sha256"],
            "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
            "device": "cpu",
            "vector_format": "row-major-f32le-v1",
            "dimensions": dimensions,
            "row_count": len(rows),
            "runtime": {"worker_sha256": encoder["worker_sha256"]},
            "rows": rows,
            "files": {"raw-vectors.f32le": identity(worker / "raw-vectors.f32le")},
        }
        for field in (
            "checkpoint_sha256",
            "base_model_artifact_tree_sha256",
            "container_image",
            "model",
            "note_batch_size",
        ):
            receipt[field] = encoder[field]
        write(worker / "worker-receipt.json", receipt)
        vectors = self.root / name
        self.cli(
            "-m",
            "sse_multivector.real_note_segmentation",
            "finalize",
            prepared,
            worker,
            vectors,
        )
        return vectors

    def test_prepare_finalizes_only_exact_within_note_duplicates_and_keeps_subjects(self):
        prepared, _ = self.prepare(self.document, "deduplicated")
        mapping = read(prepared / "vector-map.json")
        self.assertEqual(8, mapping["vector_count"])
        request = read(prepared / "worker-request.json")
        self.assertEqual([5, 1, 2], [len(note["subjects"]) for note in request["notes"]])
        self.assertEqual(2, len(mapping["excluded"]))
        self.assertEqual(self.document, read(prepared / "reviewed-input.json"))

        legacy = copy.deepcopy(self.document)
        for note in legacy["notes"]:
            note.pop("deduplicate_identical_masks", None)
        legacy_prepared, _ = self.prepare(legacy, "legacy")
        legacy_map = read(legacy_prepared / "vector-map.json")
        self.assertEqual(9, legacy_map["vector_count"])
        original_subjects = {
            (row["note_id"], row["reviewed_subject_id"]): row
            for row in legacy_map["vectors"]
        }
        representatives = [0, 2, 3, 4, 5, 6, 7, 8]
        for row, original_index in zip(mapping["vectors"], representatives, strict=True):
            original = legacy_map["vectors"][original_index]
            self.assertEqual(original["vector_id"], row["vector_id"])
            self.assertEqual(original["worker_subject_id"], row["worker_subject_id"])
            if row["note_id"] == "f3" * 32:
                self.assertNotIn("reviewed_subjects", row)
                continue
            sources = row["reviewed_subjects"]
            self.assertEqual(2 if row["ordinal"] == 0 else 1, len(sources))
            for source in sources:
                original_source = original_subjects[
                    (source["note_id"], source["reviewed_subject_id"])
                ]
                for field in (
                    "note_id",
                    "note_short_id",
                    "reviewed_note_index",
                    "reviewed_subject_index",
                    "reviewed_subject_id",
                    "subject",
                    "judgment",
                    "reviewed_subject",
                    "worker_subject_id",
                    "vector_id",
                ):
                    self.assertEqual(original_source[field], source[field])
        self.assertEqual(
            ["S1", "S2"],
            [source["reviewed_subject_id"] for source in mapping["vectors"][0]["reviewed_subjects"]],
        )
        vectors = self.finalize(prepared, "vectors")
        finalized_map = read(vectors / "vector-map.json")
        self.assertEqual(8, finalized_map["vector_count"])
        for before, after in zip(mapping["vectors"], finalized_map["vectors"], strict=True):
            self.assertEqual(before, {key: after[key] for key in before})
        self.assertEqual(8, len(read(vectors / "candidate-request.json")["inputs"]))


    def test_invalid_opt_in_or_invalid_duplicate_mask_is_not_silently_accepted(self):
        for index, value in enumerate((None, 0, 1, "true", [])):
            with self.subTest(value=value):
                document = copy.deepcopy(self.document)
                document["notes"][0]["deduplicate_identical_masks"] = value
                prepared, result = self.prepare(document, f"bad-flag-{index}", success=False)
                self.assertIn("deduplicate_identical_masks must be a boolean", result.stderr)
                self.assertFalse(prepared.exists())
        document = copy.deepcopy(self.document)
        document["notes"][0]["subjects"][1]["fragments"][1] = "rust"
        prepared, result = self.prepare(document, "bad-duplicate", success=False)
        self.assertIn("mask fragment is not exact text", result.stderr)
        self.assertFalse(prepared.exists())


if __name__ == "__main__":
    unittest.main()
