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
EXPERIMENT = ROOT / "sse_multivector/real-note-fine-segmentation-v1"
FROZEN = EXPERIMENT / "vectors"
COMPOSE = EXPERIMENT / "coverage-expansion-v1/coverage_artifacts.py"


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
            FROZEN / "encoder.json",
            FROZEN / "subject-package.json",
            FROZEN / "mask-package.json",
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

    def test_compose_cli_keeps_all_frozen_rows_and_new_subject_associations(self):
        frozen_before = {path.name: identity(path) for path in FROZEN.iterdir()}
        prepared, _ = self.prepare(self.document, "deduplicated")
        added = self.finalize(prepared, "added")
        selection = self.root / "selection.json"
        write(
            selection,
            {"schema_version": 1, "note_ids": [note["note_id"] for note in self.document["notes"]]},
        )
        combined = self.root / "combined"
        self.cli(COMPOSE, "compose", FROZEN, added, selection, combined)
        old_map = read(FROZEN / "vector-map.json")
        added_map = read(added / "vector-map.json")
        combined_map = read(combined / "vector-map.json")
        old_count = old_map["vector_count"]
        self.assertEqual(945, old_count)
        self.assertEqual(953, combined_map["vector_count"])
        self.assertEqual(old_map["vectors"], combined_map["vectors"][:old_count])
        for filename in ("raw-vectors.f32le", "normalized-vectors.f64le"):
            self.assertEqual(
                (FROZEN / filename).read_bytes() + (added / filename).read_bytes(),
                (combined / filename).read_bytes(),
            )
        self.assertEqual(
            read(FROZEN / "reviewed-input.json")["notes"] + self.document["notes"],
            read(combined / "reviewed-input.json")["notes"],
        )
        old_note_count = len(old_map["notes"])
        for original, composed in zip(
            added_map["vectors"], combined_map["vectors"][old_count:], strict=True
        ):
            self.assertEqual(original["vector_id"], composed["vector_id"])
            self.assertEqual(original["worker_subject_id"], composed["worker_subject_id"])
            original_sources = original.get("reviewed_subjects", [])
            composed_sources = composed.get("reviewed_subjects", [])
            self.assertEqual(len(original_sources), len(composed_sources))
            for source, copied in zip(original_sources, composed_sources, strict=True):
                expected = dict(source)
                expected["reviewed_note_index"] += old_note_count
                expected["note_short_id"] = f"N{expected['reviewed_note_index'] + 1:03d}"
                self.assertEqual(expected, copied)
        self.assertEqual(
            frozen_before, {path.name: identity(path) for path in FROZEN.iterdir()}
        )

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
