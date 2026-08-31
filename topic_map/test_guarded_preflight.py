import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


class GuardedPreflightTests(unittest.TestCase):
    def test_rejects_output_parent_that_contains_guarded_inputs(self) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-guard-alias.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary)
            matrix_path = root / "vectors.f32le"
            note_ids_path = root / "note-ids.bin"
            matrix_path.write_bytes(
                struct.pack("<8f", 1.0, 0.0, 0.9, 0.1, 0.0, 1.0, 0.1, 0.9)
            )
            note_ids_path.write_bytes(
                b"".join(bytes([index]) * 32 for index in range(4))
            )
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "purpose": "guard-alias-rejection-test",
                        "input": {
                            "matrix_path": str(matrix_path),
                            "note_ids_path": str(note_ids_path),
                            "dimensions": 2,
                            "start_row": 0,
                            "learning_rows": 3,
                            "evaluation_rows": 1,
                        },
                        "model": {
                            "dictionary_size": 4,
                            "average_k": 1,
                            "batch_size": 1,
                            "steps": 1,
                            "learning_rate": 0.001,
                            "seed": 7,
                        },
                        "io_budget": {
                            "max_source_read_bytes": 160,
                            "max_durable_write_bytes": 1048576,
                        },
                        "output_path": str(root / "result"),
                    }
                )
            )

            completed = subprocess.run(
                [
                    str(
                        Path(__file__).resolve().with_name(
                            "run_guarded_preflight.sh"
                        )
                    ),
                    str(config_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn(
                "output parent must not contain or alias a guarded input",
                completed.stderr,
            )

    def test_tiny_preflight_runs_only_through_verified_guard(self) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-guard-test.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary)
            matrix_path = root / "vectors.f32le"
            note_ids_path = root / "note-ids.bin"
            output_directory = root / "output"
            output_directory.mkdir()
            output_path = output_directory / "result"
            config_path = root / "config.json"
            worker_path = Path(__file__).resolve().with_name("worker.py")
            worker_sha256 = hashlib.sha256(worker_path.read_bytes()).hexdigest()
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            timeout_log = root / "timeout.log"
            real_timeout = shutil.which("timeout")
            self.assertIsNotNone(real_timeout)
            fake_timeout = fake_bin / "timeout"
            fake_timeout.write_text(
                f"""#!/bin/sh
set -eu
printf '%s\\n' "$*" > "$TIMEOUT_LOG"
exec {real_timeout} "$@"
"""
            )
            fake_timeout.chmod(0o755)
            vectors = [
                [1.0, 0.0, 0.0, 0.0],
                [0.9, 0.1, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.9, 0.1, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.9, 0.1],
                [0.0, 0.0, 0.0, 1.0],
                [0.1, 0.0, 0.0, 0.9],
            ]
            matrix_path.write_bytes(
                b"".join(struct.pack("<4f", *vector) for vector in vectors)
            )
            note_ids_path.write_bytes(
                b"".join(bytes([index]) * 32 for index in range(len(vectors)))
            )
            embedding_manifest_path = root / "embedding-manifest.json"
            embedding_manifest_bytes = (
                json.dumps(
                    {
                        "schema_version": 1,
                        "embedding_format": (
                            "learning-first-note-embedding-matrix-v1"
                        ),
                        "learning_rows": 6,
                        "evaluation_rows": 2,
                        "total_rows": 8,
                        "encoder": {"dimensions": 4},
                        "files": {
                            "vectors.f32le": {
                                "bytes": matrix_path.stat().st_size,
                                "sha256": hashlib.sha256(
                                    matrix_path.read_bytes()
                                ).hexdigest(),
                            },
                            "note-ids.bin": {
                                "bytes": note_ids_path.stat().st_size,
                                "sha256": hashlib.sha256(
                                    note_ids_path.read_bytes()
                                ).hexdigest(),
                            },
                        },
                    },
                    sort_keys=True,
                )
                + "\n"
            ).encode()
            embedding_manifest_path.write_bytes(embedding_manifest_bytes)
            embedding_manifest_sha256 = hashlib.sha256(
                embedding_manifest_bytes
            ).hexdigest()
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "purpose": "guard-integration-test",
                        "runtime": {
                            "worker_sha256": worker_sha256,
                            "container_image": (
                                "pytorch/pytorch@sha256:"
                                "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee"
                                "08dd26bc469de4c8a28b427"
                            ),
                        },
                        "input": {
                            "matrix_path": str(matrix_path),
                            "note_ids_path": str(note_ids_path),
                            "embedding_manifest": {
                                "path": str(embedding_manifest_path),
                                "bytes": len(embedding_manifest_bytes),
                                "sha256": embedding_manifest_sha256,
                            },
                            "dimensions": 4,
                            "start_row": 0,
                            "learning_rows": 6,
                            "evaluation_rows": 2,
                        },
                        "model": {
                            "dictionary_size": 8,
                            "average_k": 2,
                            "batch_size": 2,
                            "steps": 2,
                            "learning_rate": 0.001,
                            "seed": 7,
                        },
                        "io_budget": {
                            "max_source_read_bytes": (
                                384 + len(embedding_manifest_bytes)
                            ),
                            "max_durable_write_bytes": 1048576,
                        },
                        "output_path": str(output_path),
                    }
                )
            )

            completed = subprocess.run(
                [
                    str(
                        Path(__file__).resolve().with_name(
                            "run_guarded_preflight.sh"
                        )
                    ),
                    str(config_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
                env={
                    **os.environ,
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    "TIMEOUT_LOG": str(timeout_log),
                },
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((output_path / "manifest.json").is_file())
            relation_manifest = json.loads(
                (output_path / "manifest.json").read_text()
            )
            self.assertEqual(
                4,
                relation_manifest["metadata"]["torch_num_threads"],
            )
            self.assertEqual(
                worker_sha256,
                relation_manifest["metadata"]["worker_sha256"],
            )
            self.assertEqual(
                (
                    "pytorch/pytorch@sha256:"
                    "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee"
                    "08dd26bc469de4c8a28b427"
                ),
                relation_manifest["metadata"]["container_image"],
            )
            self.assertEqual(
                embedding_manifest_sha256,
                relation_manifest["metadata"]["embedding_manifest_sha256"],
            )
            report = json.loads(
                (output_directory / "guard-report.json").read_text()
            )
            self.assertEqual(
                384 + len(embedding_manifest_bytes),
                report["source_bytes_read"],
            )
            self.assertEqual(
                [
                    "--signal=TERM",
                    "--kill-after=15s",
                    "1800",
                    "docker",
                    "exec",
                ],
                timeout_log.read_text().split()[:5],
            )


if __name__ == "__main__":
    unittest.main()
