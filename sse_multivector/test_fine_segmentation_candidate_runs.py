import hashlib
import json
import platform
import resource
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from sse_multivector.fine_segmentation_candidate_runs import (
    run_candidate_suite,
    verify_candidate_suite_runs,
)


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cpu_model() -> str:
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def _cpu_features() -> list[str]:
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() in {"flags", "features"}:
            return sorted(value.split())
    return []


def _resource_limits() -> dict[str, list[int]]:
    return {
        name: list(resource.getrlimit(limit))
        for name, limit in {
            "address_space_bytes": resource.RLIMIT_AS,
            "cpu_seconds": resource.RLIMIT_CPU,
            "file_size_bytes": resource.RLIMIT_FSIZE,
            "open_files": resource.RLIMIT_NOFILE,
            "processes": resource.RLIMIT_NPROC,
            "stack_bytes": resource.RLIMIT_STACK,
        }.items()
    }


class CandidateSuiteRunTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        prepared = root / "prepared"
        prepared.mkdir()
        protocol = {
            "schema_version": 1,
            "suite_id": "test-suite",
            "encodings": [
                {"encoding_id": "e1"},
                {"encoding_id": "e2"},
            ],
            "inputs": [
                {
                    "input_id": "input/a",
                    "experiment": "experiment-a",
                    "encoding_ids": ["e1", "e2"],
                    "opaque_ids": ["1" * 64, "2" * 64],
                },
                {
                    "input_id": "input/b",
                    "experiment": "experiment-b",
                    "encoding_ids": ["e2"],
                    "opaque_ids": ["3" * 64],
                },
            ],
        }
        (prepared / "protocol.json").write_bytes(_canonical(protocol))
        prepared_manifest = {
            "schema_version": 1,
            "suite_id": "test-suite",
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "logical_input_count": 2,
            "fresh_invocations_per_candidate": 4,
        }
        (prepared / "manifest.json").write_bytes(_canonical(prepared_manifest))
        (prepared / "blinding-private.json").write_bytes(
            _canonical({"seed_hex": bytes(range(32)).hex()})
        )

        executable = root / "fake-candidate.py"
        executable.write_text(
            "#!"
            + sys.executable
            + "\n"
            + """
import hashlib, json, struct, sys
from pathlib import Path

request = json.loads(Path(sys.argv[1]).read_text())
invocation_log = Path(__file__).with_name("invocations.log")
diagnostic_nonce = len(invocation_log.read_text().splitlines()) if invocation_log.exists() else 0
with invocation_log.open("a") as log:
    log.write("1\\n")
candidate = request["candidate"]
failure_marker = Path(__file__).with_name("fail-once")
if failure_marker.exists() and candidate == "hdbscan" and len(request["inputs"]) == 2:
    failure_marker.unlink()
    print("deliberate candidate failure", file=sys.stderr)
    raise SystemExit(9)
ids = sorted(item["opaque_id"] for item in request["inputs"])
canonical = sorted(request["inputs"], key=lambda item: item["opaque_id"])
raw = bytearray(b"fine-region-candidate-input-v1\\0")
for item in canonical:
    raw.extend(item["opaque_id"].encode())
    raw.extend(len(item["normalized_vector"]).to_bytes(8, "big"))
    for value in item["normalized_vector"]:
        raw.extend(struct.pack(">d", value))
fine = (
    {"segments": [ids, [ids[0]]], "unassigned": []}
    if len(ids) > 1
    else {"segments": [], "unassigned": ids}
)
result = {"diagnostic_nonce": diagnostic_nonce, "fine_output": fine}
compact_result = json.dumps(result, separators=(",", ":"))
compact_fine = json.dumps(fine, separators=(",", ":"))
config = {"snn":"{\\\"test\\\":\\\"snn\\\"}","hdbscan":"{\\\"test\\\":\\\"hdbscan\\\"}"}[candidate]
identity = {"snn":"snn-test-v1","hdbscan":"hdbscan-test-v1"}[candidate]
algorithm = {"snn":"snn-algorithm-test-v1","hdbscan":"hdbscan-algorithm-test-v1"}[candidate]
selector = {"snn":"snn-output-test-v1","hdbscan":"hdbscan-output-test-v1"}[candidate]
manifest = {
    "schema_version": 4,
    "algorithm_version": algorithm,
    "input_contract_version": "opaque-id-order-bitwise-vector-alias-v1",
    "fine_output_selector_version": selector,
    "adapter_implementation_source_sha256": "a" * 64,
    "algorithm_implementation_source_sha256": "b" * 64,
    "preprocessing_implementation_source_sha256": "c" * 64,
    "source_vector_manifest_sha256": request["source_vector_manifest_sha256"],
    "normalized_vector_sha256": request["normalized_vector_sha256"],
    "canonical_input_sha256": hashlib.sha256(raw).hexdigest(),
    "vector_count": len(request["inputs"]),
    "unique_vector_count": len(request["inputs"]),
    "parameters": {"test": candidate},
    "configuration_sha256": hashlib.sha256(config.encode()).hexdigest(),
    "tie_rule_version": "test-tie-v1",
    "result_sha256": hashlib.sha256(compact_result.encode()).hexdigest(),
    "fine_output_sha256": hashlib.sha256(compact_fine.encode()).hexdigest(),
}
response = {
    "schema_version": 1,
    "candidate_identity": identity,
    "artifact": {
        "manifest": manifest,
        "canonical_input_ids": ids,
        "canonical_configuration_json": config,
        "canonical_fine_output_json": compact_fine,
        "result": result,
    },
}
print(json.dumps(response, separators=(",", ":")))
"""
        )
        executable.chmod(0o755)

        freeze = root / "technical-freeze.json"
        candidate_contracts = {}
        for candidate in ("snn", "hdbscan"):
            candidate_contracts[candidate] = {
                "candidate_identity": f"{candidate}-test-v1",
                "artifact_contract": {
                    "schema_version": 4,
                    "algorithm_version": f"{candidate}-algorithm-test-v1",
                    "input_contract_version": "opaque-id-order-bitwise-vector-alias-v1",
                    "fine_output_selector_version": f"{candidate}-output-test-v1",
                    "adapter_implementation_source_sha256": "a" * 64,
                    "algorithm_implementation_source_sha256": "b" * 64,
                    "preprocessing_implementation_source_sha256": "c" * 64,
                    "configuration_sha256": hashlib.sha256(
                        f'{{"test":"{candidate}"}}'.encode()
                    ).hexdigest(),
                    "tie_rule_version": "test-tie-v1",
                },
                "canonical_configuration_json": f'{{"test":"{candidate}"}}',
            }
        uname = platform.uname()
        freeze_value = {
            "schema_version": 1,
            "suite_id": "test-suite",
            "prepared_manifest_sha256": _sha(prepared / "manifest.json"),
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "worker_request_sha256": "d" * 64,
            "encoding_count": 2,
            "logical_input_count": 2,
            "invocations_per_candidate": 4,
            "candidate_execution": {
                "executable_path": str(executable.resolve()),
                "executable_sha256": _sha(executable),
                "working_directory": str(root.resolve()),
                "argv_template": ["{executable}", "{request_path}"],
                "environment": {},
                "fresh_process_per_invocation": True,
                "repetitions_per_input": 2,
                "random_seed": None,
                "numeric_type": "f64",
                "normalized_vector_contract": "row-major-f64le-v1",
                "launcher": "direct-executable-v1",
                "device": "cpu",
                "accelerator": None,
                "numerical_backend": "rust-standard-library-f64-v1",
                "determinism": "no-randomness-canonical-input-and-ties-v1",
                "thread_count": 1,
                "process_count": 1,
                "isolation": "fresh-process-empty-environment-no-shared-mutable-state-v1",
                "resource_limits": _resource_limits(),
                "host": {
                    "system": uname.system,
                    "release": uname.release,
                    "machine": uname.machine,
                    "cpu_model": _cpu_model(),
                    "cpu_features": _cpu_features(),
                },
            },
            "candidates": candidate_contracts,
            "candidate_build_inputs": {
                "files": {},
                "aggregate_sha256": "e" * 64,
            },
            "encoder": {"dimensions": 2},
        }
        freeze.write_bytes(_canonical(freeze_value))

        vectors = root / "vectors"
        vectors.mkdir()
        normalized = struct.pack("<4d", 1.0, 0.0, 0.0, 1.0)
        (vectors / "normalized-vectors.f64le").write_bytes(normalized)
        vector_map = {
            "schema_version": 1,
            "suite_id": "test-suite",
            "vector_count": 2,
            "dimensions": 2,
            "vectors": [
                {"ordinal": 0, "encoding_id": "e1"},
                {"ordinal": 1, "encoding_id": "e2"},
            ],
        }
        (vectors / "vector-map.json").write_bytes(_canonical(vector_map))
        vector_manifest = {
            "schema_version": 1,
            "suite_id": "test-suite",
            "vector_count": 2,
            "dimensions": 2,
            "sources": {
                "prepared_manifest_sha256": _sha(prepared / "manifest.json"),
                "technical_freeze_sha256": _sha(freeze),
            },
            "files": {
                "normalized-vectors.f64le": {
                    "bytes": len(normalized),
                    "sha256": hashlib.sha256(normalized).hexdigest(),
                },
                "vector-map.json": {
                    "bytes": (vectors / "vector-map.json").stat().st_size,
                    "sha256": _sha(vectors / "vector-map.json"),
                },
            },
        }
        (vectors / "manifest.json").write_bytes(_canonical(vector_manifest))
        return prepared, vectors, freeze, executable, root / "runs"

    def test_runs_every_frozen_input_twice_in_fresh_candidate_processes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            prepared, vectors, freeze, executable, output = self._fixture(root)

            report = run_candidate_suite(prepared, vectors, freeze, output)

            self.assertEqual(8, report["completed_invocation_count"])
            self.assertEqual({"hdbscan": 4, "snn": 4}, report["candidate_counts"])
            self.assertEqual(
                {"different": 0, "identical": 4, "unavailable": 0},
                report["repeatability_counts"],
            )
            self.assertTrue(report["complete"])
            self.assertEqual(
                8, len((root / "invocations.log").read_text().splitlines())
            )
            run_manifest = json.loads((output / "manifest.json").read_text())
            self.assertRegex(run_manifest["runner_source_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(
                run_manifest["candidate_execution_profile_sha256"],
                r"^[0-9a-f]{64}$",
            )
            self.assertEqual(
                report, verify_candidate_suite_runs(prepared, vectors, freeze, output)
            )

            # A completed run is replay-verified rather than executed again.
            self.assertEqual(
                report, run_candidate_suite(prepared, vectors, freeze, output)
            )
            self.assertEqual(
                8, len((root / "invocations.log").read_text().splitlines())
            )

            completion = output / "completion.json"
            completion_bytes = completion.read_bytes()
            completion.unlink()
            with self.assertRaisesRegex(ValueError, "completion"):
                verify_candidate_suite_runs(prepared, vectors, freeze, output)
            self.assertFalse(completion.exists())
            completion.write_bytes(completion_bytes)

            run_directories = sorted((output / "runs").iterdir())
            self.assertEqual(8, len(run_directories))
            request = json.loads((run_directories[0] / "request.json").read_text())
            self.assertEqual(
                {
                    "candidate",
                    "inputs",
                    "normalized_vector_sha256",
                    "schema_version",
                    "source_vector_manifest_sha256",
                },
                set(request),
            )
            self.assertTrue(
                all(
                    set(item) == {"opaque_id", "normalized_vector"}
                    for item in request["inputs"]
                )
            )
            self.assertNotIn(
                b"experiment-", (run_directories[0] / "request.json").read_bytes()
            )
            frozen_execution = json.loads(freeze.read_text())["candidate_execution"]
            for directory in run_directories:
                record = json.loads((directory / "record.json").read_text())
                self.assertEqual(frozen_execution, record["execution_profile"])
                self.assertEqual(
                    run_manifest["candidate_execution_profile_sha256"],
                    record["execution_profile_sha256"],
                )

            # Replay verification detects corruption of retained raw process output.
            (run_directories[0] / "stdout.bin").write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "stdout"):
                verify_candidate_suite_runs(prepared, vectors, freeze, output)

    def test_retains_one_failed_invocation_and_continues_the_complete_schedule(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            prepared, vectors, freeze, executable, output = self._fixture(root)
            executable.with_name("fail-once").write_text(
                "fail one matching invocation\n"
            )

            report = run_candidate_suite(prepared, vectors, freeze, output)

            self.assertTrue(report["complete"])
            self.assertEqual(8, report["completed_invocation_count"])
            self.assertEqual(1, report["integrity_failure_count"])
            self.assertEqual(
                {"different": 0, "identical": 3, "unavailable": 1},
                report["repeatability_counts"],
            )
            failed = [
                json.loads((item / "record.json").read_text())
                for item in (output / "runs").iterdir()
                if json.loads((item / "record.json").read_text())["status"]
                == "integrity-failure"
            ]
            self.assertEqual(1, len(failed))
            self.assertEqual(9, failed[0]["return_code"])
            self.assertIn(
                "candidate exited with status 9", failed[0]["integrity_error"]
            )
            self.assertEqual(
                report, verify_candidate_suite_runs(prepared, vectors, freeze, output)
            )


if __name__ == "__main__":
    unittest.main()
