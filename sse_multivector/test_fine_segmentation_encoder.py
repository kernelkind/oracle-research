import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sse_multivector.fine_segmentation_encoder import (
    run_frozen_encoder,
    verify_frozen_encoder_run,
)
import sse_multivector.fine_segmentation_encoder as encoder_runner
from sse_multivector.fine_segmentation_suite import prepare_suite
from sse_multivector.worker import canonical_tree_sha256


REPO_ROOT = Path(__file__).resolve().parents[1]
BLINDING_NAMESPACES = (
    "01-repeated-subject-recovery",
    "02-nearby-subject-resolution",
    "03-lexical-coincidence",
    "04-unmasked-context",
    "06-irrelevant-change-stability",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class FrozenEncoderExecutionTests(unittest.TestCase):
    def test_runs_the_frozen_worker_once_in_the_hardened_profile_and_replays(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            prepared = root / "prepared"
            prepare_suite(
                REPO_ROOT,
                prepared,
                namespace_seeds={
                    name: bytes([ordinal]) * 32
                    for ordinal, name in enumerate(BLINDING_NAMESPACES, start=1)
                },
                review_seed=bytes([9]) * 32,
            )

            checkpoint = root / "checkpoint.ckpt"
            checkpoint.write_bytes(b"frozen checkpoint")
            worker = root / "worker.py"
            worker.write_text("# frozen worker\n", encoding="utf-8")
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n", encoding="utf-8")
            image_id = "sha256:" + "d" * 64
            image_reference = image_id
            prepared_manifest = json.loads(
                (prepared / "manifest.json").read_text(encoding="utf-8")
            )
            freeze = root / "technical-freeze.json"
            _write_json(
                freeze,
                {
                    "schema_version": 1,
                    "suite_id": "fine-segmentation-controlled-suite-v1",
                    "prepared_manifest_sha256": _sha256(prepared / "manifest.json"),
                    "protocol_sha256": prepared_manifest["protocol_sha256"],
                    "worker_request_sha256": _sha256(prepared / "worker-request.json"),
                    "encoding_count": 207,
                    "encoder": {
                        "request_sha256": _sha256(prepared / "worker-request.json"),
                        "checkpoint_path": str(checkpoint),
                        "checkpoint_sha256": _sha256(checkpoint),
                        "worker_path": str(worker),
                        "worker_sha256": _sha256(worker),
                        "base_model_artifact_path": str(model),
                        "base_model_artifact_tree_sha256": canonical_tree_sha256(model),
                        "container_image": image_reference,
                        "note_batch_size": 8,
                        "model": {
                            "base_model": "sentence-transformers/sentence-t5-base",
                            "dimensions": 768,
                            "maximum_tokens": 512,
                            "pooling": (
                                "selected-contextual-token-mean-linear-relu-linear-v1"
                            ),
                        },
                        "dimensions": 768,
                        "vector_format": "row-major-f32le-v1",
                    },
                },
            )

            docker_log = root / "docker-log.jsonl"
            fake_docker = root / "docker"
            fake_docker.write_text(
                r"""#!/usr/bin/env python3
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

with open(os.environ["FAKE_DOCKER_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")

if sys.argv[1:3] == ["image", "inspect"]:
    print(sys.argv[3])
    raise SystemExit(0)

args = sys.argv[1:]
if not args or args[0] != "run":
    raise SystemExit(91)

mounts = {}
for index, argument in enumerate(args):
    if argument != "--mount":
        continue
    fields = dict(field.split("=", 1) for field in args[index + 1].split(",") if "=" in field)
    mounts[fields["dst"]] = Path(fields["src"])

config = json.loads(mounts["/input/worker-config.json"].read_text(encoding="utf-8"))
request = json.loads(mounts["/input/worker-request.json"].read_text(encoding="utf-8"))
output = mounts["/output"] / Path(config["output_path"]).name
output.mkdir()

raw = bytearray()
rows = []
ordinal = 0
for note in request["notes"]:
    for subject in note["subjects"]:
        vector = [0.0] * config["model"]["dimensions"]
        vector[ordinal % len(vector)] = 2.0
        raw.extend(struct.pack("<768f", *vector))
        rows.append({
            "ordinal": ordinal,
            "note_id": note["note_id"],
            "subject_id": subject["subject_id"],
            "selected_token_indices": [0],
            "selected_token_ids": [101],
            "token_count": 1,
        })
        ordinal += 1

(output / "raw-vectors.f32le").write_bytes(raw)
receipt = {
    "schema_version": 1,
    "proposal_sha256": request["proposal_sha256"],
    "request_sha256": config["request_sha256"],
    "checkpoint_sha256": config["checkpoint_sha256"],
    "base_model_artifact_tree_sha256": config["base_model_artifact_tree_sha256"],
    "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
    "model": config["model"],
    "runtime": {"worker_sha256": hashlib.sha256(mounts["/workspace/worker.py"].read_bytes()).hexdigest()},
    "device": config["device"],
    "container_image": config["container_image"],
    "note_batch_size": config["note_batch_size"],
    "vector_format": "row-major-f32le-v1",
    "dimensions": config["model"]["dimensions"],
    "row_count": len(rows),
    "rows": rows,
    "files": {
        "raw-vectors.f32le": {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    },
}
(output / "worker-receipt.json").write_text(
    json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
    encoding="utf-8",
)
print(json.dumps({"dimensions": 768, "row_count": len(rows)}))
""",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)

            protected_before = {
                "prepared": canonical_tree_sha256(prepared),
                "checkpoint": _sha256(checkpoint),
                "worker": _sha256(worker),
                "model": canonical_tree_sha256(model),
            }
            output = root / "encoder-run"
            with patch.dict(os.environ, {"FAKE_DOCKER_LOG": str(docker_log)}):
                report = run_frozen_encoder(
                    REPO_ROOT,
                    prepared,
                    freeze,
                    output,
                    docker_executable=fake_docker,
                )

            self.assertEqual(207, report["vector_count"])
            self.assertEqual(635_904, report["raw_vector_bytes"])
            self.assertEqual(
                report,
                verify_frozen_encoder_run(REPO_ROOT, prepared, freeze, output),
            )
            self.assertEqual(
                protected_before,
                {
                    "prepared": canonical_tree_sha256(prepared),
                    "checkpoint": _sha256(checkpoint),
                    "worker": _sha256(worker),
                    "model": canonical_tree_sha256(model),
                },
            )

            invocations = [
                json.loads(line) for line in docker_log.read_text().splitlines()
            ]
            self.assertEqual(2, len(invocations))
            self.assertEqual(["image", "inspect", image_id], invocations[0][:3])
            command = invocations[1]
            self.assertEqual("run", command[0])
            self.assertIn("--network", command)
            self.assertEqual("none", command[command.index("--network") + 1])
            self.assertIn("--read-only", command)
            self.assertIn("no-new-privileges", command)
            self.assertIn("ALL", command)
            self.assertIn(image_id, command)
            mounts = [
                command[index + 1]
                for index, argument in enumerate(command)
                if argument == "--mount"
            ]
            for destination in (
                "/input/worker-request.json",
                "/input/worker-config.json",
                "/checkpoint/subencoder_st5_base.ckpt",
                "/model",
                "/workspace/worker.py",
            ):
                mount = next(value for value in mounts if f"dst={destination}" in value)
                self.assertIn("readonly", mount)
            self.assertNotIn(
                "readonly", next(value for value in mounts if "dst=/output" in value)
            )

            execution = json.loads((output / "execution.json").read_text())
            self.assertEqual(
                _sha256(Path(encoder_runner.__file__)),
                execution["encoder_runner"]["sha256"],
            )
            self.assertEqual(command, execution["worker"]["argv"][1:])
            self.assertEqual(0, execution["worker"]["return_code"])
            self.assertTrue((output / "image-inspect.stdout").is_file())
            self.assertTrue((output / "worker.stdout").is_file())
            self.assertTrue((output / "worker.stderr").is_file())
            with self.assertRaisesRegex(ValueError, "already exists"):
                run_frozen_encoder(
                    REPO_ROOT,
                    prepared,
                    freeze,
                    output,
                    docker_executable=fake_docker,
                )


if __name__ == "__main__":
    unittest.main()
