import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
ROOT = EXPERIMENT.parents[1]
SCRIPT = EXPERIMENT / "run_candidate.py"
VECTORS = EXPERIMENT / "smoke-test/vectors"
BINARY = ROOT / "target/debug/fine-segmentation-candidate"
PINNED_BINARY_SHA256 = "1d9a45211d8af49c1357509c748331b393bba4280db3cb2391d9e1a75f733a6d"


def read(path):
    return json.loads(path.read_text())


class SavedCandidateRunTests(unittest.TestCase):
    def run_cli(self, output, *, binary_sha=PINNED_BINARY_SHA256, config=None):
        command = [
            sys.executable,
            str(SCRIPT),
            str(VECTORS),
            str(BINARY),
            binary_sha,
            str(output),
        ]
        if config is not None:
            command.extend(["--hdbscan-configuration", str(config)])
        return subprocess.run(command, capture_output=True, text=True, timeout=60)

    def test_saved_smoke_baseline_is_replayed_before_review_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = self.run_cli(output)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                (VECTORS / "candidate-request.json").read_bytes(),
                (output / "request.json").read_bytes(),
            )
            proof = read(output / "replay-proof.json")
            self.assertTrue(proof["full_parsed_response_equal"])
            self.assertEqual(PINNED_BINARY_SHA256, proof["candidate_binary_sha256"])
            self.assertEqual(2, len(proof["invocations"]))
            for invocation in proof["invocations"]:
                self.assertEqual(0, invocation["return_code"])
                self.assertEqual(
                    [str(BINARY), str(output / "request.json")], invocation["argv"]
                )
            for name, digest in proof["files"].items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
            self.assertEqual(read(output / "response.json"), read(output / "replay.json"))
            self.assertEqual(
                "hdbscan-controlled-suite-config-v1",
                read(output / "response.json")["candidate_identity"],
            )
            self.assertTrue((output / "review/review.json").is_file())
            self.assertFalse((output / "failure.json").exists())
            self.assertNotIn('"algorithm_result"', result.stdout)

    def test_wrong_binary_pin_refuses_before_any_candidate_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = self.run_cli(output, binary_sha="0" * 64)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("binary SHA-256 differs", result.stderr)
            failure = read(output / "failure.json")
            self.assertEqual([], failure["invocations"])
            self.assertFalse((output / "response.json").exists())
            self.assertFalse((output / "review").exists())

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            marker = output / "saved.txt"
            marker.write_text("keep existing evidence")
            result = self.run_cli(output)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("already exists", result.stderr)
            self.assertEqual([marker], list(output.iterdir()))
            self.assertEqual("keep existing evidence", marker.read_text())

    def test_existing_dangling_output_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "saved-output"
            target = root / "absent-target"
            output.symlink_to(target, target_is_directory=True)
            result = self.run_cli(output)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("already exists", result.stderr)
            self.assertTrue(output.is_symlink())
            self.assertFalse(target.exists())

    def test_explicit_configuration_changes_only_the_request_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "configuration.json"
            chosen = {"min_samples": 3, "min_cluster_size": 3, "selection_method": "leaf"}
            config.write_text(json.dumps(chosen))
            output = root / "run"
            result = self.run_cli(output, config=config)
            self.assertEqual(0, result.returncode, result.stderr)
            request = read(output / "request.json")
            self.assertEqual(chosen, request.pop("hdbscan_configuration"))
            self.assertEqual(read(VECTORS / "candidate-request.json"), request)
            response = read(output / "response.json")
            self.assertEqual("hdbscan-explicit-config-v1", response["candidate_identity"])
            self.assertEqual(chosen, response["artifact"]["manifest"]["parameters"])
            self.assertEqual(chosen, read(output / "replay-proof.json")["hdbscan_configuration"])

    def test_candidate_failure_keeps_diagnostics_without_admitting_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "configuration.json"
            config.write_text(json.dumps({"min_samples": 0, "min_cluster_size": 2, "selection_method": "leaf"}))
            output = root / "run"
            result = self.run_cli(output, config=config)
            self.assertNotEqual(0, result.returncode)
            failure = read(output / "failure.json")
            self.assertEqual(1, len(failure["invocations"]))
            self.assertNotEqual(0, failure["invocations"][0]["return_code"])
            self.assertTrue((output / "response.stderr").read_bytes())
            self.assertTrue((output / "request.json").is_file())
            self.assertFalse((output / "replay-proof.json").exists())
            self.assertFalse((output / "review").exists())


if __name__ == "__main__":
    unittest.main()
