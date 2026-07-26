import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class GuardedSampleLauncherTests(unittest.TestCase):
    def test_mounts_source_read_only_and_keeps_all_mutable_state_on_tmpfs(
        self,
    ) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-sample-launcher.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary)
            source = root / "source.ndb"
            source.mkdir()
            (source / "data.mdb").write_bytes(b"fixture")
            ordered = root / "ordered-event-ids.bin"
            ordered.write_bytes(b"\x00" * 32)
            semantic_manifest = root / "semantic-manifest.json"
            semantic_manifest.write_text("{}")
            output_parent = root / "output"
            output_parent.mkdir()
            output = output_parent / "sample"
            binary = root / "topic-map-sample"
            binary.write_text("#!/bin/sh\nexit 99\n")
            binary.chmod(0o755)
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "source_corpus_path": str(source),
                        "ordered_event_ids_path": str(ordered),
                        "semantic_manifest_path": str(semantic_manifest),
                        "output_path": str(output),
                        "learning_rows": 1,
                        "evaluation_rows": 1,
                        "max_examined_rows": 2,
                        "max_sample_bytes": 4096,
                        "author_split_seed_hex": "11" * 32,
                    }
                )
            )

            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            docker_log = root / "docker.log"
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
          cp "$output_mount/.topic-sample-config.json" "$CAPTURED_CONFIG"
          ;;
      esac
    done
    printf '%s\\n' fake-container
    ;;
  start)
    printf '%s\\n' '{"schema_version":1}'
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
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "DOCKER_LOG": str(docker_log),
                    "CAPTURED_CONFIG": str(captured_config),
                    "ORACLE_MVP_TOPIC_SAMPLE_BINARY": str(binary),
                }
            )

            completed = subprocess.run(
                [
                    str(
                        Path(__file__).resolve().with_name(
                            "run_guarded_sample.sh"
                        )
                    ),
                    str(config),
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
            self.assertIn("--cgroupns private", invocation)
            self.assertIn("--log-driver none", invocation)
            self.assertIn(f"src={source},dst=/input/corpus,readonly", invocation)
            self.assertIn(
                f"src={ordered},dst=/input/ordered-event-ids.bin,readonly",
                invocation,
            )
            self.assertIn(
                f"src={semantic_manifest},dst=/input/semantic-manifest.json,readonly",
                invocation,
            )
            self.assertIn("src=/nix/store,dst=/nix/store,readonly", invocation)
            self.assertIn(f"src={output_parent},dst=/output", invocation)
            self.assertNotIn("--device-read-bps", invocation)
            self.assertNotIn("--device-read-iops", invocation)

            rewritten = json.loads(captured_config.read_text())
            self.assertEqual("/input/corpus", rewritten["source_corpus_path"])
            self.assertEqual(
                "/input/ordered-event-ids.bin",
                rewritten["ordered_event_ids_path"],
            )
            self.assertEqual(
                "/input/semantic-manifest.json",
                rewritten["semantic_manifest_path"],
            )
            self.assertEqual("/output/sample", rewritten["output_path"])
            self.assertFalse((output_parent / ".topic-sample-config.json").exists())


if __name__ == "__main__":
    unittest.main()
