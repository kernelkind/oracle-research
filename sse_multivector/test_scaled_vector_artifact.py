import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from sse_multivector.scaled_vector_artifact import (
    finalize_vector_artifact,
    prepare_vector_artifact,
    verify_vector_artifact,
)
from sse_multivector.worker import canonical_tree_sha256


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ScaledVectorArtifactTests(unittest.TestCase):
    def test_prepares_and_finalizes_generation_through_the_worker_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            notes = root / "notes.json"
            source_notes = [
                {
                    "note_id": "1" * 64,
                    "text": "Rust is useful. Rust is enjoyable.",
                },
                {"note_id": "2" * 64, "text": "Tea is calming."},
            ]
            write_json(notes, {"schema_version": 1, "notes": source_notes})

            run = root / "generation"
            generation_manifest = {
                "schema_version": 2,
                "wrapper_sha256": "a" * 64,
                "input_sha256": sha256(notes),
                "takeaway": {
                    "prompt_version": "TPv3.82",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "max",
                },
                "prominence": {
                    "prompt_version": "PPv2",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "max",
                },
                "mask": {
                    "prompt_version": "MPv3.4",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "max",
                },
            }
            write_json(run / "manifest.json", generation_manifest)
            manifest_sha256 = sha256(run / "manifest.json")
            generated = {
                "schema_version": 2,
                "manifest_sha256": manifest_sha256,
                "notes": [
                    {
                        "note_id": "1" * 64,
                        "takeaways": [
                            {
                                "text": "Rust is useful.",
                                "prominence": 80,
                                "fragments": ["Rust is useful"],
                            },
                            {
                                "text": "Rust is enjoyable.",
                                "prominence": 65,
                                "fragments": ["Rust is enjoyable"],
                            },
                        ],
                    },
                    {
                        "note_id": "2" * 64,
                        "takeaways": [
                            {
                                "text": "Tea is calming.",
                                "prominence": 90,
                                "fragments": ["Tea is calming"],
                            }
                        ],
                    },
                ],
            }
            write_json(run / "output.json", generated)
            records = []

            revised_note = generated["notes"][0]
            records.append(
                {
                    "manifest_sha256": manifest_sha256,
                    "job_key": f"takeaway:{revised_note['note_id']}",
                    "stage": "takeaway",
                    "note_id": revised_note["note_id"],
                    "takeaway_index": None,
                    "attempt": 1,
                    "status": "succeeded",
                    "response": [
                        item["text"] for item in revised_note["takeaways"]
                    ]
                    + ["A superseded takeaway."],
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                }
            )
            for index, takeaway in enumerate(
                revised_note["takeaways"]
                + [
                    {
                        "text": "A superseded takeaway.",
                        "prominence": 10,
                        "fragments": ["Rust is useful"],
                    }
                ]
            ):
                for stage, response in (
                    ("prominence", takeaway["prominence"]),
                    ("mask", takeaway["fragments"]),
                ):
                    records.append(
                        {
                            "manifest_sha256": manifest_sha256,
                            "job_key": f"{stage}:{revised_note['note_id']}:{index}",
                            "stage": stage,
                            "note_id": revised_note["note_id"],
                            "takeaway_index": index,
                            "attempt": 1,
                            "status": "succeeded",
                            "response": response,
                            "usage": {"input_tokens": 10, "output_tokens": 2},
                        }
                    )
            records.append(
                {
                    "manifest_sha256": manifest_sha256,
                    "job_key": f"takeaway:{revised_note['note_id']}",
                    "stage": "takeaway",
                    "note_id": revised_note["note_id"],
                    "takeaway_index": None,
                    "attempt": 2,
                    "status": "succeeded",
                    "response": [item["text"] for item in revised_note["takeaways"]],
                    "retry_reason": "removed unsupported meaning",
                    "usage": {"input_tokens": 10, "output_tokens": 2},
                }
            )
            for index, takeaway in enumerate(revised_note["takeaways"]):
                for stage, response in (
                    ("prominence", takeaway["prominence"]),
                    ("mask", takeaway["fragments"]),
                ):
                    records.append(
                        {
                            "manifest_sha256": manifest_sha256,
                            "job_key": f"{stage}:{revised_note['note_id']}:{index}",
                            "stage": stage,
                            "note_id": revised_note["note_id"],
                            "takeaway_index": index,
                            "attempt": 2,
                            "status": "succeeded",
                            "response": response,
                            "retry_reason": "upstream rendered prompt changed",
                            "usage": {"input_tokens": 10, "output_tokens": 2},
                        }
                    )

            for note in generated["notes"][1:]:
                records.append(
                    {
                        "manifest_sha256": manifest_sha256,
                        "job_key": f"takeaway:{note['note_id']}",
                        "stage": "takeaway",
                        "note_id": note["note_id"],
                        "takeaway_index": None,
                        "attempt": 1,
                        "status": "succeeded",
                        "response": [item["text"] for item in note["takeaways"]],
                        "usage": {"input_tokens": 10, "output_tokens": 2},
                    }
                )
                for index, takeaway in enumerate(note["takeaways"]):
                    for stage, response in (
                        ("prominence", takeaway["prominence"]),
                        ("mask", takeaway["fragments"]),
                    ):
                        records.append(
                            {
                                "manifest_sha256": manifest_sha256,
                                "job_key": f"{stage}:{note['note_id']}:{index}",
                                "stage": stage,
                                "note_id": note["note_id"],
                                "takeaway_index": index,
                                "attempt": 1,
                                "status": "succeeded",
                                "response": response,
                                "usage": {"input_tokens": 10, "output_tokens": 2},
                            }
                        )
            for record in records[7:]:
                record["wrapper_sha256"] = "b" * 64
            result_payload = "".join(
                json.dumps(record) + "\n" for record in records
            )
            prefix_payload = "".join(
                json.dumps(record) + "\n" for record in records[:7]
            ).encode("utf-8")
            (run / "results.jsonl").write_text(result_payload, encoding="utf-8")
            (run / "runner-upgrades.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "manifest_sha256": manifest_sha256,
                        "from_wrapper_sha256": "a" * 64,
                        "to_wrapper_sha256": "b" * 64,
                        "first_result_line": 8,
                        "results_prefix_bytes": len(prefix_payload),
                        "results_prefix_sha256": hashlib.sha256(
                            prefix_payload
                        ).hexdigest(),
                        "reason": "add audited semantic retries",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            checkpoint = root / "checkpoint.ckpt"
            checkpoint.write_bytes(b"checkpoint")
            worker = root / "worker.py"
            worker.write_text("# pinned worker\n", encoding="utf-8")
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n", encoding="utf-8")
            prepared = root / "prepared"
            worker_output = root / "sse-worker-output"
            vector_output = root / "vectors"
            config = root / "config.json"
            write_json(
                config,
                {
                    "schema_version": 1,
                    "artifact_id": "fixture-v1",
                    "note_count": 2,
                    "input_path": str(notes),
                    "generation_run_directory": str(run),
                    "checkpoint_path": str(checkpoint),
                    "checkpoint_sha256": sha256(checkpoint),
                    "worker_path": str(worker),
                    "worker_sha256": sha256(worker),
                    "base_model_artifact_path": str(model),
                    "base_model_artifact_tree_sha256": canonical_tree_sha256(model),
                    "model": {
                        "base_model": "fixture",
                        "dimensions": 2,
                        "maximum_tokens": 512,
                        "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
                    },
                    "container_image": "fixture@sha256:" + "a" * 64,
                    "note_batch_size": 2,
                    "prepared_path": str(prepared),
                    "worker_output_path": str(worker_output),
                    "vector_output_path": str(vector_output),
                },
            )

            tampered_records = list(records)
            tampered_records[7] = dict(tampered_records[7])
            tampered_records[7]["wrapper_sha256"] = "c" * 64
            (run / "results.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in tampered_records),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "wrapper provenance"):
                prepare_vector_artifact(config)
            (run / "results.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            prepared_report = prepare_vector_artifact(config)
            self.assertEqual(2, prepared_report.note_count)
            self.assertEqual(3, prepared_report.vector_count)
            prepared_manifest = json.loads(
                (prepared / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                sha256(run / "runner-upgrades.jsonl"),
                prepared_manifest["generation_runner_upgrades_sha256"],
            )
            request = json.loads(
                (prepared / "worker-input.json").read_text(encoding="utf-8")
            )
            worker_config = json.loads(
                (prepared / "worker-config.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                "/output/sse-worker-output", worker_config["output_path"]
            )
            self.assertEqual(3, sum(len(note["subjects"]) for note in request["notes"]))
            self.assertEqual([[0, 14]], request["notes"][0]["subjects"][0]["byte_spans"])

            worker.write_text("# changed worker\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SSE worker hash differs"):
                prepare_vector_artifact(config)
            worker.write_text("# pinned worker\n", encoding="utf-8")

            raw = struct.pack("<6f", 3.0, 4.0, 0.0, 2.0, -2.0, 0.0)
            worker_output.mkdir()
            (worker_output / "raw-vectors.f32le").write_bytes(raw)
            mapping = json.loads(
                (prepared / "vector-map.json").read_text(encoding="utf-8")
            )
            write_json(
                worker_output / "worker-receipt.json",
                {
                    "schema_version": 1,
                    "proposal_sha256": request["proposal_sha256"],
                    "request_sha256": sha256(prepared / "worker-input.json"),
                    "checkpoint_sha256": sha256(checkpoint),
                    "base_model_artifact_tree_sha256": canonical_tree_sha256(model),
                    "runtime": {"worker_sha256": sha256(worker)},
                    "model": json.loads(config.read_text())["model"],
                    "dimensions": 2,
                    "row_count": 3,
                    "rows": [
                        {
                            "ordinal": row["ordinal"],
                            "note_id": row["note_id"],
                            "subject_id": row["subject_id"],
                        }
                        for row in mapping["vectors"]
                    ],
                    "files": {
                        "raw-vectors.f32le": {
                            "bytes": len(raw),
                            "sha256": sha256(worker_output / "raw-vectors.f32le"),
                        }
                    },
                },
            )

            report = finalize_vector_artifact(config)
            self.assertEqual(3, report.vector_count)
            self.assertEqual(report, verify_vector_artifact(config))
            normalized = struct.unpack(
                "<6f", (vector_output / "normalized-vectors.f32le").read_bytes()
            )
            self.assertAlmostEqual(0.6, normalized[0], places=6)
            self.assertAlmostEqual(0.8, normalized[1], places=6)
            self.assertAlmostEqual(1.0, normalized[3], places=6)


if __name__ == "__main__":
    unittest.main()
