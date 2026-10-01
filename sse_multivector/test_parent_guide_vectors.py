"""Saved parent-guide names become source-bound SSE requests, not inference."""

import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from sse_multivector import worker
from sse_multivector import test_parent_guide_workflow as guide_fixtures
from sse_multivector import test_subject_matching_probe as vector_fixtures


class ParentGuideVectorTests(unittest.TestCase):
    def setUp(self):
        fixture = guide_fixtures.ParentGuideWorkflowTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        self.report = fixture.guide_report({"S0000": ["Bread", "Dairy products", "植物性脂肪"],
                                            "S0005": ["植物性脂肪", "Communities"]})
        _, self.probe = vector_fixtures.SavedMatchingTests().fixture(self.root)
        checkpoint = self.root / "checkpoint.ckpt"
        checkpoint.write_bytes(b"Pinned test checkpoint")
        model = self.root / "model"
        model.mkdir()
        (model / "config.json").write_text("{}")
        self.worker_source = Path(worker.__file__).resolve()
        identity = dict(checkpoint_sha256=worker._sha256_file(checkpoint),
            base_model_artifact_tree_sha256=worker.canonical_tree_sha256(model),
            model=dict(base_model="sentence-transformers/sentence-t5-base", dimensions=2,
                       maximum_tokens=512, pooling=worker.POOLING_RULE),
            device="cpu", note_batch_size=8, container_image="sha256:" + "a" * 64,
            runtime=dict(worker_sha256=worker._sha256_file(self.worker_source)))
        receipt_path = self.probe / "worker-result" / "worker-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt.update(identity)
        receipt_path.write_text(json.dumps(receipt))
        self.config_path = self.root / "worker-config.json"
        config = {key: value for key, value in identity.items() if key != "runtime"}
        config.update(schema_version=1, request_path=str(self.probe / "unused-request.json"),
            request_sha256="b" * 64, checkpoint_path=str(checkpoint), base_model_artifact_path=str(model),
            output_path=str(self.probe / "worker-result"))
        self.config_path.write_text(json.dumps(config))
        self.source = dict(fixture.refs, discoveries=[self.report["experiment"]],
            subject_probe=str(self.probe), worker_config=str(self.config_path), worker_source=str(self.worker_source))
        self.source_path = self.root / "vector-source.json"
        self.source_path.write_text(json.dumps(self.source))

    def prepare(self, name="new-vectors"):
        from sse_multivector.parent_guide_vectors import prepare_vectors
        return prepare_vectors(self.source_path, self.root / name, lambda path: self.report)

    def test_preparation_deduplicates_reuses_and_selects_only_exact_absent_names(self):
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        summary = self.prepare()
        output = self.root / "new-vectors"
        self.assertEqual((summary["unique_names"], summary["reused_encodings"], summary["new_encodings"]), (3, 1, 2))
        inputs = json.loads((output / "inputs.json").read_text())
        self.assertEqual(inputs["names"], ["Bread", "植物性脂肪", "Communities"])
        self.assertEqual(inputs["reused_probes"], [str(self.probe)])
        request = json.loads((output / "worker-request.json").read_text())
        self.assertEqual([note["text"] for note in request["notes"]], ["植物性脂肪", "Communities"])
        for note in request["notes"]:
            raw = note["text"].encode()
            identity = hashlib.sha256(raw).hexdigest()
            self.assertEqual(note["note_id"], identity)
            self.assertEqual(note["subjects"], [dict(subject_id=identity[:16], byte_spans=[[0, len(raw)]])])
        worker._load_request(output / "worker-request.json")
        config = worker.WorkerConfig.load(output / "worker-config.json")
        self.assertEqual(config.device, "cpu")
        self.assertEqual(config.note_batch_size, 8)
        self.assertEqual(config.request_sha256, worker._sha256_file(output / "worker-request.json"))
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((output / "worker-result").exists())
        self.assertEqual((output / ".gitignore").read_text(), "*\n")

    def test_completed_probe_loads_with_original_full_receipt_identity(self):
        from sse_multivector.subject_matching_probe import load_subject_vectors
        self.prepare()
        output = self.root / "new-vectors"
        request = json.loads((output / "worker-request.json").read_text())
        folder = output / "worker-result"
        folder.mkdir()
        raw = struct.pack("<ffff", 1, 0, 0, 1)
        (folder / "raw-vectors.f32le").write_bytes(raw)
        receipt = json.loads((self.probe / "worker-result" / "worker-receipt.json").read_text())
        receipt.update(row_count=2, rows=[dict(note_id=note["note_id"], subject_id=note["subjects"][0]["subject_id"])
            for note in request["notes"]], proposal_sha256=worker._sha256_file(output / "inputs.json"),
            request_sha256=worker._sha256_file(output / "worker-request.json"),
            files={"raw-vectors.f32le": dict(sha256=hashlib.sha256(raw).hexdigest())})
        (folder / "worker-receipt.json").write_text(json.dumps(receipt))
        vectors, original_receipt, protected = load_subject_vectors(output)
        self.assertEqual(len(vectors), 4)
        self.assertEqual(original_receipt["runtime"], receipt["runtime"])
        self.assertIn(str(folder / "raw-vectors.f32le"), protected)
        receipt["runtime"] = dict(worker_sha256="wrong")
        (folder / "worker-receipt.json").write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "runtime"):
            load_subject_vectors(output)

    def test_fully_cached_preparation_writes_no_worker_request_or_config(self):
        from sse_multivector.subject_matching_probe import load_subject_vectors
        for case in self.report["cases"]:
            qid = case["evidence"]["queries"][0]
            case["parsed"] = dict(queries=[dict(id=qid, parents=["Bread", "Empty"] if qid == "S0000" else ["Bread"])])
        summary = self.prepare()
        output = self.root / "new-vectors"
        self.assertEqual((summary["unique_names"], summary["reused_encodings"], summary["new_encodings"]), (2, 2, 0))
        self.assertIsNone(summary["worker_config"])
        self.assertFalse((output / "worker-request.json").exists())
        self.assertFalse((output / "worker-config.json").exists())
        self.assertEqual(load_subject_vectors(output)[0], load_subject_vectors(self.probe)[0])

    def test_mismatched_worker_source_and_config_are_refused_without_output(self):
        original = self.config_path.read_bytes()
        for field, value in [("checkpoint_sha256", "c" * 64), ("note_batch_size", 1),
                             ("device", "cuda"), ("container_image", "sha256:" + "c" * 64)]:
            config = json.loads(original)
            config[field] = value
            self.config_path.write_text(json.dumps(config))
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse((self.root / "new-vectors").exists())
        self.config_path.write_bytes(original)
        different = self.root / "different-worker.py"
        different.write_text("Different worker")
        self.source["worker_source"] = str(different)
        self.source_path.write_text(json.dumps(self.source))
        with self.assertRaisesRegex(ValueError, "frozen worker source"):
            self.prepare()
        self.assertFalse((self.root / "new-vectors").exists())
        self.source["worker_source"] = dict(path=str(self.worker_source), sha256="wrong")
        self.source_path.write_text(json.dumps(self.source))
        with self.assertRaisesRegex(ValueError, "protected source changed"):
            self.prepare()
        self.assertFalse((self.root / "new-vectors").exists())

    def test_protected_nomination_files_and_invalid_reports_fail_before_vector_loading(self):
        from sse_multivector import parent_guide_vectors as preparation
        directory = Path(self.report["experiment"])
        path = directory / "prompt.txt"
        path.write_text("Original")
        (directory / "experiment.json").write_text(json.dumps(dict(plan=dict(files={
            "prompt.txt": worker._sha256_file(path)}, sources={}))))
        path.write_text("Changed")
        with patch.object(preparation, "load_subject_vectors", side_effect=AssertionError("vectors reached")) as vectors:
            with self.assertRaisesRegex(ValueError, "protected parent-guide source changed"):
                self.prepare()
            vectors.assert_not_called()
        self.assertFalse((self.root / "new-vectors").exists())
        path.write_text("Original")
        self.report["cases"][0].update(status="failed", receipt=None)
        with self.assertRaisesRegex(ValueError, "complete valid"):
            self.prepare()
        self.assertFalse((self.root / "new-vectors").exists())

    def test_strict_source_shape_and_existing_destination_are_refused(self):
        for source in (None, {**self.source, "schema_version": 2}, {**self.source, "foreign": True}):
            self.source_path.write_text(json.dumps(source))
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.prepare()
            self.assertFalse((self.root / "new-vectors").exists())
        self.source_path.write_text(json.dumps(self.source))
        self.prepare()
        before = {path: path.read_bytes() for path in (self.root / "new-vectors").iterdir() if path.is_file()}
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual({path: path.read_bytes() for path in before}, before)


if __name__ == "__main__":
    unittest.main()
