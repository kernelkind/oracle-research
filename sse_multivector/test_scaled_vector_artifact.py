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


def generation_stages() -> dict[str, object]:
    return {
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


def write_vector_config(
    root: Path,
    notes: Path,
    run: Path,
    *,
    name: str = "fixture",
) -> Path:
    checkpoint = root / f"{name}-checkpoint.ckpt"
    checkpoint.write_bytes(b"checkpoint")
    worker = root / f"{name}-worker.py"
    worker.write_text("# pinned worker\n", encoding="utf-8")
    model = root / f"{name}-model"
    model.mkdir()
    (model / "config.json").write_text("{}\n", encoding="utf-8")
    config = root / f"{name}-config.json"
    write_json(
        config,
        {
            "schema_version": 1,
            "artifact_id": f"{name}-v1",
            "note_count": 1,
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
            "note_batch_size": 1,
            "prepared_path": str(root / f"{name}-prepared"),
            "worker_output_path": str(root / f"{name}-worker-output"),
            "vector_output_path": str(root / f"{name}-vectors"),
        },
    )
    return config


def generation_records(
    manifest_sha256: str,
    note_id: str,
    takeaway: str,
    prominence: int,
    fragments: list[str],
    *,
    wrapper_sha256: str = "a" * 64,
) -> list[dict[str, object]]:
    records = [
        {
            "manifest_sha256": manifest_sha256,
            "wrapper_sha256": wrapper_sha256,
            "job_key": f"takeaway:{note_id}",
            "stage": "takeaway",
            "note_id": note_id,
            "takeaway_index": None,
            "attempt": 1,
            "status": "succeeded",
            "response": [takeaway],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
        {
            "manifest_sha256": manifest_sha256,
            "wrapper_sha256": wrapper_sha256,
            "job_key": f"prominence:{note_id}:0",
            "stage": "prominence",
            "note_id": note_id,
            "takeaway_index": 0,
            "attempt": 1,
            "status": "succeeded",
            "response": prominence,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
        {
            "manifest_sha256": manifest_sha256,
            "wrapper_sha256": wrapper_sha256,
            "job_key": f"mask:{note_id}:0",
            "stage": "mask",
            "note_id": note_id,
            "takeaway_index": 0,
            "attempt": 1,
            "status": "succeeded",
            "response": fragments,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    ]
    for record in records:
        stage = str(record["stage"])
        record["model"] = "gpt-5.6-sol"
        record["reasoning_effort"] = "max"
        record["prompt_sha256"] = hashlib.sha256(
            f"{stage}:{note_id}:{record['takeaway_index']}".encode("utf-8")
        ).hexdigest()
        record["response_schema_sha256"] = hashlib.sha256(
            stage.encode("utf-8")
        ).hexdigest()
    return records


def write_results(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"".join(
            json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
            + b"\n"
            for record in records
        )
    )


def build_reuse_fixture(
    root: Path,
    *,
    text: str = "Rust is useful.",
    takeaway: str = "Rust is useful.",
    prominence: int = 90,
    fragments: list[str] | None = None,
) -> tuple[Path, Path, list[dict[str, object]], list[dict[str, object]]]:
    fragments = fragments or ["Rust is useful"]
    note_id = "1" * 64
    notes = root / "notes.json"
    note_value = {"schema_version": 1, "notes": [{"note_id": note_id, "text": text}]}
    write_json(notes, note_value)

    source_input = root / "source-input.json"
    write_json(source_input, note_value)
    source_run = root / "source-generation"
    source_manifest = {
        "schema_version": 2,
        "wrapper_sha256": "b" * 64,
        "input_sha256": sha256(source_input),
        **generation_stages(),
    }
    write_json(source_run / "manifest.json", source_manifest)
    source_manifest_sha256 = sha256(source_run / "manifest.json")
    source_records = generation_records(
        source_manifest_sha256,
        note_id,
        takeaway,
        prominence,
        fragments,
        wrapper_sha256="b" * 64,
    )
    write_results(source_run / "results.jsonl", source_records)
    write_json(
        source_run / "output.json",
        {
            "schema_version": 2,
            "manifest_sha256": source_manifest_sha256,
            "notes": [
                {
                    "note_id": note_id,
                    "takeaways": [
                        {
                            "text": takeaway,
                            "prominence": prominence,
                            "fragments": fragments,
                        }
                    ],
                }
            ],
        },
    )
    source_lines = (source_run / "results.jsonl").read_bytes().splitlines(keepends=True)
    source_refs = {
        record["job_key"]: {
            "input_sha256": sha256(source_input),
            "manifest_sha256": source_manifest_sha256,
            "results_sha256": sha256(source_run / "results.jsonl"),
            "output_sha256": sha256(source_run / "output.json"),
            "result_line": index,
            "result_sha256": hashlib.sha256(source_lines[index - 1]).hexdigest(),
            "result_attempt": record["attempt"],
        }
        for index, record in enumerate(source_records, 1)
    }

    run = root / "generation"
    reuse_source = {
        "input_path": str(source_input),
        "input_sha256": sha256(source_input),
        "run_directory": str(source_run),
        "manifest_sha256": source_manifest_sha256,
        "results_sha256": sha256(source_run / "results.jsonl"),
        "runner_upgrades_sha256": None,
        "output_sha256": sha256(source_run / "output.json"),
    }
    manifest = {
        "schema_version": 3,
        "wrapper_sha256": "a" * 64,
        "input_sha256": sha256(notes),
        "reuse_source": reuse_source,
        **generation_stages(),
    }
    write_json(run / "manifest.json", manifest)
    manifest_sha256 = sha256(run / "manifest.json")
    write_json(
        run / "output.json",
        {
            "schema_version": 3,
            "manifest_sha256": manifest_sha256,
            "notes": [
                {
                    "note_id": note_id,
                    "takeaways": [
                        {
                            "text": takeaway,
                            "prominence": prominence,
                            "fragments": fragments,
                        }
                    ],
                }
            ],
        },
    )
    current_records = generation_records(
        manifest_sha256, note_id, takeaway, prominence, fragments
    )
    for record in current_records:
        record["execution"] = "reused"
        record["reused_from"] = source_refs[record["job_key"]]
        record["usage"] = {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        }
    write_results(run / "results.jsonl", current_records)
    return write_vector_config(root, notes, run), run, current_records, source_records


class ScaledVectorArtifactTests(unittest.TestCase):
    def test_schema_3_rejects_nonexistent_pinned_reuse_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            note_id = "1" * 64
            notes = root / "notes.json"
            write_json(
                notes,
                {
                    "schema_version": 1,
                    "notes": [{"note_id": note_id, "text": "Rust is useful."}],
                },
            )
            run = root / "generation"
            manifest = {
                "schema_version": 3,
                "wrapper_sha256": "a" * 64,
                "input_sha256": sha256(notes),
                "reuse_source": {
                    "input_path": "/archived/input.json",
                    "input_sha256": "b" * 64,
                    "run_directory": "/archived/generation",
                    "manifest_sha256": "c" * 64,
                    "results_sha256": "d" * 64,
                    "runner_upgrades_sha256": None,
                    "output_sha256": "e" * 64,
                },
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
            write_json(run / "manifest.json", manifest)
            manifest_sha256 = sha256(run / "manifest.json")
            write_json(
                run / "output.json",
                {
                    "schema_version": 3,
                    "manifest_sha256": manifest_sha256,
                    "notes": [
                        {
                            "note_id": note_id,
                            "takeaways": [
                                {
                                    "text": "Rust is useful.",
                                    "prominence": 90,
                                    "fragments": ["Rust is useful"],
                                }
                            ],
                        }
                    ],
                },
            )
            records = [
                {
                    "manifest_sha256": manifest_sha256,
                    "wrapper_sha256": "a" * 64,
                    "job_key": f"takeaway:{note_id}",
                    "stage": "takeaway",
                    "note_id": note_id,
                    "takeaway_index": None,
                    "attempt": 1,
                    "status": "succeeded",
                    "response": ["Rust is useful."],
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "reused_from": {
                        "results_sha256": "d" * 64,
                        "result_line": 1,
                    },
                },
                {
                    "manifest_sha256": manifest_sha256,
                    "wrapper_sha256": "a" * 64,
                    "job_key": f"prominence:{note_id}:0",
                    "stage": "prominence",
                    "note_id": note_id,
                    "takeaway_index": 0,
                    "attempt": 1,
                    "status": "succeeded",
                    "response": 90,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "reused_from": {
                        "results_sha256": "d" * 64,
                        "result_line": 2,
                    },
                },
                {
                    "manifest_sha256": manifest_sha256,
                    "wrapper_sha256": "a" * 64,
                    "job_key": f"mask:{note_id}:0",
                    "stage": "mask",
                    "note_id": note_id,
                    "takeaway_index": 0,
                    "attempt": 1,
                    "status": "succeeded",
                    "response": ["Rust is useful"],
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "reused_from": {
                        "results_sha256": "d" * 64,
                        "result_line": 3,
                    },
                },
            ]
            (run / "results.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            checkpoint = root / "checkpoint.ckpt"
            checkpoint.write_bytes(b"checkpoint")
            worker = root / "worker.py"
            worker.write_text("# pinned worker\n", encoding="utf-8")
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n", encoding="utf-8")
            config = root / "config.json"
            write_json(
                config,
                {
                    "schema_version": 1,
                    "artifact_id": "reuse-fixture-v1",
                    "note_count": 1,
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
                    "note_batch_size": 1,
                    "prepared_path": str(root / "prepared"),
                    "worker_output_path": str(root / "worker-output"),
                    "vector_output_path": str(root / "vectors"),
                },
            )

            with self.assertRaisesRegex(ValueError, "reuse source"):
                prepare_vector_artifact(config)

    def test_schema_3_validates_every_reused_source_ledger_reference(self) -> None:
        mutations = (
            (0, "result_line", 99),
            (1, "result_sha256", "f" * 64),
            (2, "result_attempt", 2),
        )
        for record_index, field, invalid_value in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config, run, records, _ = build_reuse_fixture(root)
                records[record_index]["reused_from"][field] = invalid_value
                write_results(run / "results.jsonl", records)

                with self.assertRaisesRegex(ValueError, "reuse source"):
                    prepare_vector_artifact(config)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            records[0]["response"] = ["A response absent from the source ledger."]
            write_results(run / "results.jsonl", records)

            with self.assertRaisesRegex(ValueError, "reuse source"):
                prepare_vector_artifact(config)

    def test_schema_3_rejects_intact_marker_current_contract_tampering(self) -> None:
        mutations = {
            "model": "different-model",
            "reasoning_effort": "low",
            "prompt_sha256": "f" * 64,
            "response_schema_sha256": "e" * 64,
        }
        for field, invalid_value in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                config, run, records, _ = build_reuse_fixture(root)
                records[0][field] = invalid_value
                write_results(run / "results.jsonl", records)

                with self.assertRaisesRegex(ValueError, "reuse source result line"):
                    prepare_vector_artifact(config)

    def test_schema_3_validates_a_reused_record_superseded_by_a_fresh_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            records[0]["reused_from"]["result_sha256"] = "f" * 64
            retry = dict(records[0])
            retry["attempt"] = 2
            retry.pop("execution")
            retry.pop("reused_from")
            retry["usage"] = {"input_tokens": 1, "output_tokens": 1}
            records.append(retry)
            write_results(run / "results.jsonl", records)

            with self.assertRaisesRegex(ValueError, "reuse source"):
                prepare_vector_artifact(config)

    def test_schema_3_rejects_removed_reuse_markers_from_eligible_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            for record in records:
                record.pop("execution")
                record.pop("reused_from")
                record["usage"] = {"input_tokens": 1, "output_tokens": 1}
            write_results(run / "results.jsonl", records)

            with self.assertRaisesRegex(ValueError, "reuse source provenance"):
                prepare_vector_artifact(config)

    def test_schema_3_rejects_response_and_prompt_tampering_with_removed_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            records[0].pop("execution")
            records[0].pop("reused_from")
            records[0]["usage"] = {"input_tokens": 1, "output_tokens": 1}
            records[0]["response"] = ["A fabricated takeaway."]
            records[0]["prompt_sha256"] = "f" * 64
            write_results(run / "results.jsonl", records)

            with self.assertRaisesRegex(ValueError, "reuse source provenance"):
                prepare_vector_artifact(config)

    def test_schema_3_rejects_a_fresh_attempt_two_without_attempt_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            records[0]["attempt"] = 2
            records[0].pop("execution")
            records[0].pop("reused_from")
            records[0]["usage"] = {"input_tokens": 1, "output_tokens": 1}
            write_results(run / "results.jsonl", records)

            with self.assertRaisesRegex(ValueError, "attempt 1"):
                prepare_vector_artifact(config)

    def test_schema_3_permits_a_fresh_retry_after_a_provenanced_reuse_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, records, _ = build_reuse_fixture(root)
            retry = dict(records[0])
            retry["attempt"] = 2
            retry.pop("execution")
            retry.pop("reused_from")
            retry["usage"] = {"input_tokens": 1, "output_tokens": 1}
            records.append(retry)
            write_results(run / "results.jsonl", records)

            report = prepare_vector_artifact(config)

            self.assertEqual(1, report.vector_count)

    def test_verify_reopens_the_pinned_schema_3_reuse_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, run, _, _ = build_reuse_fixture(root)
            prepare_vector_artifact(config)
            manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
            source_output = Path(manifest["reuse_source"]["run_directory"]) / "output.json"
            source_output.unlink()

            with self.assertRaisesRegex(ValueError, "reuse source output"):
                verify_vector_artifact(config)

    def test_schema_3_prepares_when_every_reused_source_reference_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _, _, _ = build_reuse_fixture(root)

            report = prepare_vector_artifact(config)

            self.assertEqual(1, report.note_count)
            self.assertEqual(1, report.vector_count)

    def test_schema_2_allows_url_fragments_through_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            note_id = "1" * 64
            text = "See https://example.com for the record."
            notes = root / "notes.json"
            write_json(
                notes,
                {"schema_version": 1, "notes": [{"note_id": note_id, "text": text}]},
            )
            run = root / "generation"
            manifest = {
                "schema_version": 2,
                "wrapper_sha256": "a" * 64,
                "input_sha256": sha256(notes),
                **generation_stages(),
            }
            write_json(run / "manifest.json", manifest)
            manifest_sha256 = sha256(run / "manifest.json")
            fragments = ["https://example.com"]
            write_json(
                run / "output.json",
                {
                    "schema_version": 2,
                    "manifest_sha256": manifest_sha256,
                    "notes": [
                        {
                            "note_id": note_id,
                            "takeaways": [
                                {
                                    "text": "The post contains a record link.",
                                    "prominence": 20,
                                    "fragments": fragments,
                                }
                            ],
                        }
                    ],
                },
            )
            write_results(
                run / "results.jsonl",
                generation_records(
                    manifest_sha256,
                    note_id,
                    "The post contains a record link.",
                    20,
                    fragments,
                ),
            )
            config = write_vector_config(root, notes, run)

            report = prepare_vector_artifact(config)
            self.assertEqual(1, report.vector_count)
            config_value = json.loads(config.read_text(encoding="utf-8"))
            prepared = Path(config_value["prepared_path"])
            worker_output = Path(config_value["worker_output_path"])
            worker_output.mkdir()
            request = json.loads(
                (prepared / "worker-input.json").read_text(encoding="utf-8")
            )
            mapping = json.loads(
                (prepared / "vector-map.json").read_text(encoding="utf-8")
            )
            raw_path = worker_output / "raw-vectors.f32le"
            raw_path.write_bytes(struct.pack("<2f", 3.0, 4.0))
            write_json(
                worker_output / "worker-receipt.json",
                {
                    "schema_version": 1,
                    "proposal_sha256": request["proposal_sha256"],
                    "request_sha256": sha256(prepared / "worker-input.json"),
                    "checkpoint_sha256": config_value["checkpoint_sha256"],
                    "base_model_artifact_tree_sha256": config_value[
                        "base_model_artifact_tree_sha256"
                    ],
                    "runtime": {"worker_sha256": config_value["worker_sha256"]},
                    "model": config_value["model"],
                    "dimensions": 2,
                    "row_count": 1,
                    "rows": [
                        {
                            "ordinal": mapping["vectors"][0]["ordinal"],
                            "note_id": mapping["vectors"][0]["note_id"],
                            "subject_id": mapping["vectors"][0]["subject_id"],
                        }
                    ],
                    "files": {
                        "raw-vectors.f32le": {
                            "bytes": raw_path.stat().st_size,
                            "sha256": sha256(raw_path),
                        }
                    },
                },
            )

            finalized = finalize_vector_artifact(config)

            self.assertEqual(1, finalized.vector_count)
            self.assertEqual(finalized, verify_vector_artifact(config))

    def test_schema_3_rejects_url_fragments_through_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, _, _, _ = build_reuse_fixture(
                root,
                text="See https://example.com for the record.",
                takeaway="The post contains a record link.",
                prominence=20,
                fragments=["https://example.com"],
            )

            with self.assertRaisesRegex(ValueError, "must not contain a URL"):
                prepare_vector_artifact(config)

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
