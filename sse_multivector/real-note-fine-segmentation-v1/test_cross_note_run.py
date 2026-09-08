import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
ROOT = EXPERIMENT.parents[1]
SCRIPT = EXPERIMENT / "run_candidate.py"
VECTORS = EXPERIMENT / "smoke-test/vectors"
BASELINE_BINARY = ROOT / "target/debug/fine-segmentation-candidate"


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CrossNoteRunTests(unittest.TestCase):
    def run_cli(self, vectors, output, *, binary=BASELINE_BINARY, config=None):
        command = [
            sys.executable,
            str(SCRIPT),
            str(vectors),
            str(binary),
            sha(binary),
            str(output),
            "--cross-note-density",
        ]
        if config is not None:
            command.extend(["--hdbscan-configuration", str(config)])
        return subprocess.run(command, capture_output=True, text=True, timeout=60)

    def cross_note_binary(self):
        supplied = os.environ.get("CROSS_NOTE_CANDIDATE_BINARY")
        if supplied is None:
            self.skipTest("CROSS_NOTE_CANDIDATE_BINARY is not supplied")
        binary = Path(supplied).resolve()
        self.assertTrue(
            binary.is_file(), f"cross-note candidate binary is missing: {binary}"
        )
        return binary

    def test_saved_smoke_changes_only_candidate_and_verified_note_map_and_replays(self):
        binary = self.cross_note_binary()
        before = {path.name: sha(path) for path in VECTORS.iterdir() if path.is_file()}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = self.run_cli(VECTORS, output, binary=binary)
            self.assertEqual(0, result.returncode, result.stderr)
            request = read(output / "request.json")
            self.assertEqual("hdbscan_cross_note", request.pop("candidate"))
            source_notes = request.pop("source_note_ids")
            self.assertEqual(
                {
                    row["vector_id"]: row["note_id"]
                    for row in read(VECTORS / "vector-map.json")["vectors"]
                },
                source_notes,
            )
            request["candidate"] = "hdbscan"
            self.assertEqual(read(VECTORS / "candidate-request.json"), request)
            response = read(output / "response.json")
            self.assertEqual(response, read(output / "replay.json"))
            identity = "hdbscan-cross-note-controlled-suite-config-v1"
            self.assertEqual(identity, response["candidate_identity"])
            manifest = response["artifact"]["manifest"]
            self.assertEqual(
                "hdbscan-star-cross-note-exact-angular-v1",
                manifest["algorithm_version"],
            )
            expected_cross_note = {
                "core_distance_rule_version": "nearest-different-source-note-angular-v1",
                "source_note_ids_sha256": hashlib.sha256(
                    json.dumps(
                        source_notes, sort_keys=True, separators=(",", ":")
                    ).encode()
                ).hexdigest(),
            }
            self.assertEqual(expected_cross_note, manifest["cross_note"])
            self.assertEqual(
                expected_cross_note, read(output / "review/metadata.json")["cross_note"]
            )
            proof = read(output / "replay-proof.json")
            self.assertEqual(identity, proof["candidate_identity"])
            self.assertTrue(proof["full_parsed_response_equal"])
            self.assertEqual(sha(binary), proof["candidate_binary_sha256"])
            self.assertEqual(sha(SCRIPT), proof["runner_sha256"])
            self.assertEqual(
                sha(VECTORS / "candidate-request.json"), proof["source_request_sha256"]
            )
            self.assertEqual(2, len(proof["invocations"]))
            for invocation in proof["invocations"]:
                self.assertEqual(0, invocation["return_code"])
                self.assertEqual(
                    [str(binary), str(output / "request.json")], invocation["argv"]
                )
                self.assertEqual(sha(binary), invocation["binary_sha256_before"])
                self.assertEqual(sha(binary), invocation["binary_sha256_after"])
            for name, digest in proof["files"].items():
                self.assertEqual(sha(output / name), digest)
            saved = {
                path.name: sha(path) for path in output.iterdir() if path.is_file()
            }
            repeated = self.run_cli(VECTORS, output, binary=binary)
            self.assertNotEqual(0, repeated.returncode)
            self.assertIn("already exists", repeated.stderr)
            self.assertEqual(
                saved,
                {path.name: sha(path) for path in output.iterdir() if path.is_file()},
            )
        self.assertEqual(
            before,
            {path.name: sha(path) for path in VECTORS.iterdir() if path.is_file()},
        )

    def test_explicit_cross_note_configuration_preserves_other_source_request_fields(
        self,
    ):
        binary = self.cross_note_binary()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "configuration.json"
            parameters = {
                "min_samples": 2,
                "min_cluster_size": 3,
                "selection_method": "leaf",
            }
            config.write_text(json.dumps(parameters))
            output = root / "run"
            result = self.run_cli(VECTORS, output, binary=binary, config=config)
            self.assertEqual(0, result.returncode, result.stderr)
            request = read(output / "request.json")
            self.assertEqual(parameters, request.pop("hdbscan_configuration"))
            self.assertEqual("hdbscan_cross_note", request.pop("candidate"))
            request.pop("source_note_ids")
            request["candidate"] = "hdbscan"
            self.assertEqual(read(VECTORS / "candidate-request.json"), request)
            self.assertEqual(
                "hdbscan-cross-note-explicit-config-v1",
                read(output / "response.json")["candidate_identity"],
            )
            self.assertEqual(
                parameters, read(output / "review/metadata.json")["parameters"]
            )

    def test_cross_note_min_samples_three_is_rejected_without_admitting_review(self):
        binary = self.cross_note_binary()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "configuration.json"
            config.write_text(
                json.dumps(
                    {
                        "min_samples": 3,
                        "min_cluster_size": 3,
                        "selection_method": "leaf",
                    }
                )
            )
            output = root / "run"
            result = self.run_cli(VECTORS, output, binary=binary, config=config)
            self.assertNotEqual(0, result.returncode)
            failure = read(output / "failure.json")
            self.assertEqual(1, len(failure["invocations"]))
            self.assertNotEqual(0, failure["invocations"][0]["return_code"])
            self.assertIn("min_samples=2", (output / "response.stderr").read_text())
            self.assertFalse(failure["review_admitted"])
            self.assertFalse((output / "replay-proof.json").exists())
            self.assertFalse((output / "review").exists())

    def test_changed_frozen_note_evidence_is_rejected_before_candidate_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vectors = root / "vectors"
            shutil.copytree(VECTORS, vectors)
            mapping = vectors / "vector-map.json"
            changed = read(mapping)
            changed["vectors"][0]["note_id"] = "f" * 64
            mapping.write_text(json.dumps(changed))
            output = root / "run"
            result = self.run_cli(vectors, output)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("vector-map.json", result.stderr)
            self.assertEqual([], read(output / "failure.json")["invocations"])
            self.assertFalse((output / "request.json").exists())
            self.assertFalse((output / "review").exists())

    def test_changed_source_request_is_rejected_before_candidate_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vectors = root / "vectors"
            shutil.copytree(VECTORS, vectors)
            source = vectors / "candidate-request.json"
            changed = read(source)
            changed["inputs"][0]["normalized_vector"][0] += 0.5
            source.write_text(json.dumps(changed))
            output = root / "run"
            result = self.run_cli(vectors, output)
            self.assertNotEqual(0, result.returncode)
            self.assertIn(
                "request differs from verified vector evidence", result.stderr
            )
            self.assertEqual([], read(output / "failure.json")["invocations"])
            self.assertFalse((output / "request.json").exists())
            self.assertFalse((output / "review").exists())


if __name__ == "__main__":
    unittest.main()
