import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class GuardedEncoderLauncherTests(unittest.TestCase):
    def test_rejects_output_parent_that_contains_encoder_inputs(self) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-encoder-alias.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary)
            sample = root / "sample"
            sample.mkdir()
            (sample / "manifest.json").write_text("{}")
            (sample / "sample.jsonl").write_text("{}\n")
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}")
            (model / "model.safetensors").write_bytes(b"model")
            dependencies = root / "dependencies"
            dependencies.mkdir()
            (dependencies / "transformers").mkdir()
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "purpose": "guard-alias-rejection-test",
                        "sample_manifest_path": str(sample / "manifest.json"),
                        "model_path": str(model),
                        "dependencies_path": str(dependencies),
                        "encoder": {
                            "model_id": "example/encoder",
                            "model_revision": "abc",
                            "dimensions": 3,
                            "pooling": "cls-token-no-normalization-v1",
                            "maximum_tokens": 64,
                            "numeric_type": "float32",
                        },
                        "runtime": {
                            "canonical_tree_hash_rule": (
                                "sorted-relative-path-type-size-content-sha256-v1"
                            ),
                            "model_tree_sha256": "11" * 32,
                            "dependencies_tree_sha256": "22" * 32,
                            "encoder_implementation_sha256": "33" * 32,
                            "container_image": (
                                "pytorch/pytorch@sha256:"
                                "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26"
                                "bc469de4c8a28b427"
                            ),
                        },
                        "batch_size": 2,
                        "io_budget": {
                            "maximum_sample_artifact_bytes": 4096,
                            "maximum_output_bytes": 4096,
                        },
                        "output_path": str(root / "embeddings"),
                    }
                )
            )
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            fake_docker = fake_bin / "docker"
            fake_docker.write_text("#!/bin/sh\nexit 97\n")
            fake_docker.chmod(0o755)

            completed = subprocess.run(
                [
                    str(
                        Path(__file__).resolve().with_name(
                            "run_guarded_encoder.sh"
                        )
                    ),
                    str(config),
                    str(dependencies),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                },
                timeout=30,
            )

            self.assertNotEqual(0, completed.returncode)
            self.assertIn(
                "output parent must not contain or alias an encoder input",
                completed.stderr,
            )

    def test_mounts_all_experiment_inputs_read_only_and_output_on_tmpfs(
        self,
    ) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-encoder-launcher.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary)
            sample = root / "sample"
            sample.mkdir()
            (sample / "manifest.json").write_text("{}")
            (sample / "sample.jsonl").write_text("{}\n")
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}")
            (model / "model.safetensors").write_bytes(b"model")
            dependencies = root / "dependencies"
            dependencies.mkdir()
            (dependencies / "transformers").mkdir()
            output_parent = root / "output"
            output_parent.mkdir()
            output = output_parent / "embeddings"
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "purpose": "guard-integration-test",
                        "sample_manifest_path": str(sample / "manifest.json"),
                        "model_path": str(model),
                        "dependencies_path": str(dependencies),
                        "encoder": {
                            "model_id": "example/encoder",
                            "model_revision": "abc",
                            "dimensions": 3,
                            "pooling": "cls-token-no-normalization-v1",
                            "maximum_tokens": 64,
                            "numeric_type": "float32",
                        },
                        "runtime": {
                            "canonical_tree_hash_rule": (
                                "sorted-relative-path-type-size-content-sha256-v1"
                            ),
                            "model_tree_sha256": "11" * 32,
                            "dependencies_tree_sha256": "22" * 32,
                            "encoder_implementation_sha256": "33" * 32,
                            "container_image": (
                                "pytorch/pytorch@sha256:"
                                "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26"
                                "bc469de4c8a28b427"
                            ),
                        },
                        "batch_size": 2,
                        "io_budget": {
                            "maximum_sample_artifact_bytes": 4096,
                            "maximum_output_bytes": 4096,
                        },
                        "output_path": str(output),
                    }
                )
            )

            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            docker_log = root / "docker.log"
            timeout_log = root / "timeout.log"
            captured_config = root / "container-config.json"
            fake_docker = fake_bin / "docker"
            fake_docker.write_text(
                """#!/bin/sh
set -eu
printf '%s\\n' "$*" >> "$DOCKER_LOG"
case "$1" in
  create)
    for argument in "$@"; do
      case "$argument" in
        type=bind,src=*,dst=/output)
          output_mount=${argument#type=bind,src=}
          output_mount=${output_mount%,dst=/output}
          cp "$output_mount/.encoder-config.json" "$CAPTURED_CONFIG"
          ;;
      esac
    done
    printf '%s\\n' fake-container
    ;;
  start)
    printf '%s\\n' '{"total_rows":3}'
    ;;
  rm)
    ;;
  *)
    exit 97
    ;;
esac
"""
            )
            fake_docker.chmod(0o755)
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
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "DOCKER_LOG": str(docker_log),
                    "TIMEOUT_LOG": str(timeout_log),
                    "CAPTURED_CONFIG": str(captured_config),
                }
            )

            completed = subprocess.run(
                [
                    str(
                        Path(__file__).resolve().with_name(
                            "run_guarded_encoder.sh"
                        )
                    ),
                    str(config),
                    str(dependencies),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
                timeout=30,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            invocation = docker_log.read_text()
            self.assertIn("--read-only", invocation)
            self.assertIn("--network none", invocation)
            self.assertIn("--log-driver none", invocation)
            self.assertIn(f"src={sample},dst=/sample,readonly", invocation)
            self.assertIn(f"src={model},dst=/model,readonly", invocation)
            self.assertIn(
                f"src={dependencies},dst=/dependencies,readonly", invocation
            )
            self.assertIn(f"src={output_parent},dst=/output", invocation)
            self.assertIn("TRANSFORMERS_OFFLINE=1", invocation)
            self.assertEqual(
                "--signal=TERM --kill-after=30s 10800 "
                "docker start -a fake-container",
                timeout_log.read_text().strip(),
            )

            rewritten = json.loads(captured_config.read_text())
            self.assertEqual(
                "/sample/manifest.json", rewritten["sample_manifest_path"]
            )
            self.assertEqual("/model", rewritten["model_path"])
            self.assertEqual(
                "/dependencies", rewritten["dependencies_path"]
            )
            self.assertEqual("/output/embeddings", rewritten["output_path"])
            self.assertEqual(
                "pytorch/pytorch@sha256:"
                "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26"
                "bc469de4c8a28b427",
                rewritten["runtime"]["container_image"],
            )
            self.assertFalse((output_parent / ".encoder-config.json").exists())


if __name__ == "__main__":
    unittest.main()
