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

from coverage_artifacts import _source, compare, compose
from sse_multivector.real_note_segmentation import (
    finalize_vectors,
    package_review,
    prepare_reviewed_inputs,
)


EXPERIMENT = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENT.parents[1]
PIN = "d2c0cf7266ad46a09882c395c20e393c08eff1ab27780538219184d96df4a7d9"
BINARY = ROOT / "target/frozen-binaries" / PIN / "fine-segmentation-candidate"


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n")


def identity(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def source(root, name, entries):
    directory = root / name
    directory.mkdir()
    notes = []
    for number, _ in entries:
        text = f"Original note {number}: coffee ☕"
        notes.append(
            {
                "note_id": f"{number:064x}",
                "text": text,
                "subjects": [
                    {
                        "id": "S1",
                        "subject": "Coffee.",
                        "judgment": "accepted",
                        "fragments": ["coffee ☕"],
                        "byte_spans": [[len(text.encode()) - 10, len(text.encode())]],
                    }
                ],
            }
        )
    encoder = {
        "schema_version": 1,
        "checkpoint_path": "fixture/checkpoint",
        "checkpoint_sha256": "a" * 64,
        "base_model_artifact_path": "fixture/model",
        "base_model_artifact_tree_sha256": "b" * 64,
        "worker_path": "sse_multivector/worker.py",
        "worker_sha256": "c" * 64,
        "container_image": "sha256:" + "d" * 64,
        "note_batch_size": 8,
        "model": {
            "base_model": "sentence-transformers/sentence-t5-base",
            "dimensions": 2,
            "maximum_tokens": 512,
            "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
        },
    }
    for filename, value in (
        ("reviewed.json", {"schema_version": 1, "notes": notes}),
        ("encoder.json", encoder),
        ("subject.json", {"status": "frozen", "version": "ASv6.23"}),
        ("mask.json", {"status": "frozen", "version": "MPv3.5"}),
    ):
        write(directory / filename, value)
    prepared = directory / "prepared"
    prepare_reviewed_inputs(
        directory / "reviewed.json",
        directory / "encoder.json",
        directory / "subject.json",
        directory / "mask.json",
        prepared,
    )
    worker = directory / "worker"
    worker.mkdir()
    raw = struct.pack(f"<{2 * len(entries)}f", *(x for _, row in entries for x in row))
    (worker / "raw-vectors.f32le").write_bytes(raw)
    request = read(prepared / "worker-request.json")
    receipt = {
        "schema_version": 1,
        "proposal_sha256": request["proposal_sha256"],
        "request_sha256": identity(prepared / "worker-request.json")["sha256"],
        "checkpoint_sha256": encoder["checkpoint_sha256"],
        "base_model_artifact_tree_sha256": encoder["base_model_artifact_tree_sha256"],
        "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
        "model": encoder["model"],
        "container_image": encoder["container_image"],
        "device": "cpu",
        "note_batch_size": 8,
        "vector_format": "row-major-f32le-v1",
        "dimensions": 2,
        "row_count": len(entries),
        "runtime": {"worker_sha256": encoder["worker_sha256"]},
        "rows": [
            {
                "ordinal": index,
                "note_id": note["note_id"],
                "subject_id": note["subjects"][0]["subject_id"],
                "selected_token_indices": [1],
                "selected_token_ids": [101],
                "token_count": 3,
            }
            for index, note in enumerate(request["notes"])
        ],
        "files": {"raw-vectors.f32le": identity(worker / "raw-vectors.f32le")},
    }
    write(worker / "worker-receipt.json", receipt)
    vectors = directory / "vectors"
    finalize_vectors(prepared, worker, vectors)
    return vectors


class CoverageArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.old = source(
            self.root, "old", [(1, (1, 0)), (2, (1, 0.01)), (3, (0, 1)), (4, (0.01, 1))]
        )
        self.new = source(
            self.root, "new", [(5, (1, 0.02)), (6, (0.02, 1)), (7, (-1, 0))]
        )

    def compose(self, name="combined", notes=(5,)):
        output = self.root / name
        compose(self.old, self.new, [f"{number:064x}" for number in notes], output)
        return output

    def run_candidate(self, vectors, name):
        self.assertTrue(
            BINARY.is_file(), "the frozen integration-test binary is required"
        )
        output = self.root / name
        result = subprocess.run(
            [
                sys.executable,
                str(EXPERIMENT / "run_candidate.py"),
                str(vectors),
                str(BINARY),
                PIN,
                str(output),
                "--cross-note-density",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return output

    def test_composition_preserves_old_rows_and_ids_and_isolates_each_arm(self):
        before = {
            str(p): identity(p) for root in (self.old, self.new) for p in root.iterdir()
        }
        a, b = self.compose("a", (5,)), self.compose("b", (6,))
        old_map = read(self.old / "vector-map.json")
        for output, note_number in ((a, 5), (b, 6)):
            mapping = read(output / "vector-map.json")
            self.assertEqual(old_map["vectors"], mapping["vectors"][:4])
            self.assertEqual(f"{note_number:064x}", mapping["vectors"][4]["note_id"])
            self.assertEqual("V005", mapping["vectors"][4]["short_id"])
            source_row = read(self.new / "vector-map.json")["vectors"][note_number - 5]
            self.assertEqual(
                source_row["vector_id"], mapping["vectors"][4]["vector_id"]
            )
            for filename, stride in (
                ("normalized-vectors.f64le", 16),
                ("raw-vectors.f32le", 8),
            ):
                expected = (self.old / filename).read_bytes()
                new_raw = (self.new / filename).read_bytes()
                start = (note_number - 5) * stride
                self.assertEqual(
                    expected + new_raw[start : start + stride],
                    (output / filename).read_bytes(),
                )
            manifest = read(output / "manifest.json")
            self.assertEqual(5, manifest["vector_count"])
            self.assertNotIn("worker-receipt.json", manifest["files"])
            self.assertEqual(
                (self.old / "worker-receipt.json").read_bytes(),
                (output / "source-old-worker-receipt.json").read_bytes(),
            )
            self.assertEqual(
                [f"{note_number:064x}"],
                read(output / "composition.json")["selected_note_ids"],
            )
        self.assertEqual(
            before,
            {
                str(p): identity(p)
                for root in (self.old, self.new)
                for p in root.iterdir()
            },
        )

    def test_selection_rejects_unknown_duplicate_and_old_notes_without_output(self):
        for index, notes in enumerate(((99,), (5, 5), (1,), ())):
            with self.subTest(notes=notes), self.assertRaises(ValueError):
                self.compose(f"bad-{index}", notes)
            self.assertFalse((self.root / f"bad-{index}").exists())
        overlap = source(self.root, "overlap", [(1, (1, 0)), (8, (0, 1))])
        with self.assertRaisesRegex(ValueError, "overlap|duplicate"):
            compose(self.old, overlap, [f"{8:064x}"], self.root / "overlap-output")

    def test_overwrite_and_dangling_symlink_are_refused(self):
        output = self.compose()
        before = {p.name: identity(p) for p in output.iterdir()}
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.compose()
        self.assertEqual(before, {p.name: identity(p) for p in output.iterdir()})
        link = self.root / "link"
        link.symlink_to(self.root / "missing")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.compose("link")
        self.assertFalse((self.root / "missing").exists())

    def test_source_tampering_and_rehashed_wrong_normalization_are_rejected(self):
        raw_path = self.new / "raw-vectors.f32le"
        original = raw_path.read_bytes()
        raw_path.write_bytes(original[:-1])
        with self.assertRaisesRegex(ValueError, "hash|byte|shape"):
            self.compose("tampered")
        raw_path.write_bytes(original)
        normalized_path = self.new / "normalized-vectors.f64le"
        raw = normalized_path.read_bytes()
        normalized_path.write_bytes(raw[16:32] + raw[:16] + raw[32:])
        manifest = read(self.new / "manifest.json")
        manifest["files"][normalized_path.name] = identity(normalized_path)
        write(self.new / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "replay|normaliz|source|differs"):
            self.compose("rehashed")
        self.assertFalse((self.root / "rehashed").exists())

    def test_fresh_candidate_replay_and_comparison_report_added_rows_and_changed_packets(
        self,
    ):
        combined = self.compose()
        old_run = self.run_candidate(self.old, "old-run")
        new_run = self.run_candidate(combined, "new-run")
        output = self.root / "comparison"
        report = compare(self.old, old_run, combined, new_run, output)
        old_packets = read(old_run / "review/review.json")["packets"]
        new_packets = read(new_run / "review/review.json")["packets"]
        old_keys = {p["packet"] for p in old_packets}
        expected = [p for p in new_packets if p["packet"] not in old_keys]
        self.assertTrue(
            expected, "the added fixture vector must change a selected segment"
        )
        self.assertEqual(expected, read(output / "review.json")["packets"])
        self.assertEqual(4, len(report["old_vector_transitions"]))
        self.assertEqual(1, report["additions"]["vector_count"])
        added = read(combined / "vector-map.json")["vectors"][4]["vector_id"]
        self.assertEqual(
            [added], [row["vector_id"] for row in report["additions"]["memberships"]]
        )
        destinations = report["baseline_segment_destinations"]
        self.assertEqual(old_keys, set(destinations))
        self.assertTrue(
            any(
                not row["exactly_unchanged"] and row["all_members_together"]
                for row in destinations.values()
            )
        )
        for packet in read(output / "review.json")["packets"]:
            self.assertNotIn("title", packet)
            self.assertNotIn("judgment", packet)
        with self.assertRaisesRegex(ValueError, "already exists"):
            compare(self.old, old_run, combined, new_run, output)

    def test_comparison_rejects_rehashed_changed_review_membership(self):
        combined = self.compose()
        old_run = self.run_candidate(self.old, "old-run")
        new_run = self.run_candidate(combined, "new-run")
        path = new_run / "review/review.json"
        review = read(path)
        self.assertTrue(review["packets"])
        review["packets"][0]["instances"].pop()
        write(path, review)
        manifest_path = new_run / "review/manifest.json"
        manifest = read(manifest_path)
        manifest["files"]["review.json"] = identity(path)
        write(manifest_path, manifest)
        with self.assertRaisesRegex(ValueError, "review|partition|membership"):
            compare(self.old, old_run, combined, new_run, self.root / "bad-review")
        self.assertFalse((self.root / "bad-review").exists())

    def test_comparison_rejects_a_forged_replay_proof(self):
        combined = self.compose()
        old_run = self.run_candidate(self.old, "old-run")
        new_run = self.run_candidate(combined, "new-run")
        proof_path = new_run / "replay-proof.json"
        proof = copy.deepcopy(read(proof_path))
        proof["invocations"][1]["binary_sha256_after"] = "0" * 64
        write(proof_path, proof)
        with self.assertRaisesRegex(ValueError, "replay|binary|invocation"):
            compare(self.old, old_run, combined, new_run, self.root / "bad-proof")

    def test_saved_smoke_artifact_replays_without_changing_its_files(self):
        saved = EXPERIMENT / "smoke-test/vectors"
        before = {p.name: identity(p) for p in saved.iterdir()}
        verified = _source(saved)
        self.assertEqual(10, verified["manifest"]["vector_count"])
        self.assertEqual(before, {p.name: identity(p) for p in saved.iterdir()})

    def test_rehashed_response_and_review_cannot_change_the_frozen_parameters(self):
        combined = self.compose()
        old_run = self.run_candidate(self.old, "old-run")
        new_run = self.run_candidate(combined, "new-run")
        response = read(new_run / "response.json")
        parameters = dict(
            response["artifact"]["manifest"]["parameters"], min_cluster_size=3
        )
        configuration = json.dumps(parameters, separators=(",", ":"))
        response["artifact"]["canonical_configuration_json"] = configuration
        response["artifact"]["manifest"]["parameters"] = parameters
        response["artifact"]["manifest"]["configuration_sha256"] = hashlib.sha256(
            configuration.encode()
        ).hexdigest()
        for name in ("response.json", "replay.json"):
            write(new_run / name, response)
        altered = self.root / "altered-review"
        package_review(combined, new_run / "response.json", altered)
        for path in altered.iterdir():
            (new_run / "review" / path.name).write_bytes(path.read_bytes())
        proof = read(new_run / "replay-proof.json")
        for name in ("response.json", "replay.json"):
            proof["files"][name] = identity(new_run / name)["sha256"]
        write(new_run / "replay-proof.json", proof)
        with self.assertRaisesRegex(ValueError, "parameters|configuration"):
            compare(self.old, old_run, combined, new_run, self.root / "bad-parameters")
        self.assertFalse((self.root / "bad-parameters").exists())


if __name__ == "__main__":
    unittest.main()
