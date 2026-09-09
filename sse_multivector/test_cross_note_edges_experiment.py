import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sse_multivector/run_cross_note_edges_experiment.py"
BINARY = Path(os.environ.get(
    "HDBV3_CANDIDATE_BINARY",
    ROOT / "target/hdbv3-build/debug/fine-segmentation-candidate",
))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value))


class CrossNoteEdgesExperimentTests(unittest.TestCase):
    def invoke(self, baseline, mapping, notes, output, pin=None):
        return subprocess.run([
            sys.executable, str(SCRIPT), str(baseline), str(mapping), str(notes),
            str(BINARY), pin or digest(BINARY), str(output),
        ], capture_output=True, text=True, timeout=60)

    def fixture(self, root):
        baseline = root / "baseline"
        baseline.mkdir()
        angles = [0.0, 0.4, 0.6, 1.0, 2.0, 2.02]
        note_ids = [f"{n:064x}" for n in [10, 11, 11, 12, 13, 14]]
        inputs = [{"opaque_id": f"{i + 1:064x}",
                   "normalized_vector": [math.cos(a), math.sin(a)]}
                  for i, a in enumerate(angles)]
        request = {
            "schema_version": 1, "candidate": "hdbscan_cross_note",
            "source_vector_manifest_sha256": "a" * 64,
            "normalized_vector_sha256": "b" * 64, "inputs": inputs,
            "source_note_ids": {v["opaque_id"]: n for v, n in zip(inputs, note_ids)},
        }
        save(baseline / "request.json", request)
        result = subprocess.run([str(BINARY), str(baseline / "request.json")],
                                capture_output=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        (baseline / "response.json").write_bytes(result.stdout)
        mapping, notes = root / "vectors.json", root / "notes.json"
        save(mapping, {"vectors": [
            {"vector_id": v["opaque_id"], "short_id": f"V{i + 1:03}",
             "note_id": n, "note_short_id": f"N{int(n, 16):03}",
             "fragments": [f"example {i}"]}
            for i, (v, n) in enumerate(zip(inputs, note_ids))]})
        save(notes, {"notes": [{"note_id": n, "text": "synthetic test"}
                               for n in sorted(set(note_ids))]})
        return baseline, mapping, notes

    def test_existing_results_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.invoke(root, root, root, root, pin="0" * 64)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("output already exists", result.stderr)
            self.assertEqual([], list(root.iterdir()))

    def test_full_run_replays_baseline_and_variant_and_preserves_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline, mapping, notes = self.fixture(root)
            originals = {p: digest(p) for p in [baseline / "request.json",
                         baseline / "response.json", mapping, notes]}
            result = self.invoke(baseline, mapping, notes, root / "run")
            self.assertEqual(0, result.returncode, result.stderr)
            proof = json.loads((root / "run/proof.json").read_bytes())
            self.assertTrue(proof["baseline_result_identical"])
            self.assertTrue(proof["fresh_replay_identical"])
            self.assertTrue(proof["frozen_numeric_inputs_identical"])
            self.assertEqual(3, len(proof["invocations"]))
            self.assertEqual(originals, {p: digest(p) for p in originals})
            changed = json.loads((root / "run/request.json").read_bytes())
            changed["candidate"] = "hdbscan_cross_note"
            self.assertEqual(json.loads((baseline / "request.json").read_bytes()), changed)
            comparison = json.loads((root / "run/comparison.json").read_bytes())
            self.assertEqual(0, comparison["HDBv3"]["same_note_mst_edges"])
            self.assertGreater(comparison["HDBv2"]["same_note_mst_edges"], 0)
            self.assertEqual(5, comparison["HDBv3"]["mst_edges"])
            for path, sha in proof["files"].items():
                self.assertEqual(sha, digest(root / "run" / path))

    def test_changed_baseline_is_rejected_before_variant_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline, mapping, notes = self.fixture(root)
            response = json.loads((baseline / "response.json").read_bytes())
            response["artifact"]["result"]["algorithm_result"]["core_distances"][0] = 9.0
            save(baseline / "response.json", response)
            result = self.invoke(baseline, mapping, notes, root / "run")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("baseline result differs", result.stderr)
            self.assertFalse((root / "run/response.json").exists())
            self.assertTrue((root / "run/failure.json").exists())


if __name__ == "__main__":
    unittest.main()
