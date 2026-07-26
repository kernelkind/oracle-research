import json
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


class GuardedPreflightTests(unittest.TestCase):
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
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "purpose": "guard-integration-test",
                        "input": {
                            "matrix_path": str(matrix_path),
                            "note_ids_path": str(note_ids_path),
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
                            "max_source_read_bytes": 384,
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
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue((output_path / "manifest.json").is_file())
            report = json.loads(
                (output_directory / "guard-report.json").read_text()
            )
            self.assertEqual(384, report["source_bytes_read"])


if __name__ == "__main__":
    unittest.main()
