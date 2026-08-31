import hashlib
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import torch

from topic_map.worker import (
    BatchTopKSae,
    ExperimentConfig,
    IoBudget,
    IoPlan,
    SparseRelation,
    _measure_training_state,
    calibrate_inference_threshold,
    run_experiment,
)


class BatchTopKTests(unittest.TestCase):
    def test_measurement_masks_features_seen_only_on_evaluation_notes(self) -> None:
        model = BatchTopKSae(input_dimensions=2, dictionary_size=2, average_k=1)
        with torch.no_grad():
            model.encoder.weight.copy_(torch.eye(2))
            model.encoder.bias.zero_()
            model.decoder.weight.copy_(torch.eye(2))
            model.decoder_bias.zero_()
        learning = torch.tensor([[2.0, 0.0], [1.0, 0.0]])
        evaluation = torch.tensor([[0.0, 2.0]])

        measurement = _measure_training_state(
            model,
            learning=learning,
            evaluation=evaluation,
            average_k=1,
            batch_size=2,
            step=1,
            last_batch_loss=0.0,
            last_batch_reconstruction_loss=0.0,
            last_batch_auxiliary_loss=0.0,
        )

        self.assertEqual(0, measurement["evaluation"]["active_topic_count"])
        self.assertEqual(0, measurement["evaluation"]["relation_entry_count"])
        self.assertEqual(1, measurement["evaluation"]["unassigned_note_count"])

    def test_training_selection_is_batch_global_and_variable_per_note(self) -> None:
        activations = torch.tensor(
            [
                [9.0, 8.0, 7.0, 0.0],
                [6.0, 0.5, 0.4, 0.3],
            ]
        )

        selected = BatchTopKSae.select_batch_topk(activations, average_k=2)

        self.assertEqual(4, int(torch.count_nonzero(selected)))
        self.assertEqual([3, 1], torch.count_nonzero(selected, dim=1).tolist())

    def test_inference_is_independent_of_batch_composition_and_order(self) -> None:
        model = BatchTopKSae(input_dimensions=3, dictionary_size=5, average_k=2)
        with torch.no_grad():
            model.encoder.weight.copy_(
                torch.tensor(
                    [
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                        [0.0, 0.0, 1.0],
                        [0.5, 0.5, 0.0],
                        [0.0, 0.5, 0.5],
                    ]
                )
            )
            model.decoder_bias.zero_()

        corpus = torch.tensor(
            [
                [3.0, 2.0, 0.0],
                [0.0, 4.0, 1.0],
                [1.0, 0.0, 5.0],
            ]
        )
        threshold = calibrate_inference_threshold(model, corpus, average_k=2)
        alone = model.encode_inference(corpus[0:1], threshold)
        reordered = model.encode_inference(corpus[[2, 0, 1]], threshold)[1:2]

        torch.testing.assert_close(alone, reordered)

    def test_inference_threshold_averages_training_batch_boundaries(self) -> None:
        model = BatchTopKSae(input_dimensions=2, dictionary_size=2, average_k=1)
        with torch.no_grad():
            model.encoder.weight.copy_(torch.eye(2))
            model.decoder_bias.zero_()
        corpus = torch.tensor(
            [[4.0, 0.0], [3.0, 0.0], [2.0, 0.0], [1.0, 0.0]]
        )

        threshold = calibrate_inference_threshold(
            model, corpus, average_k=1, batch_size=2
        )

        self.assertEqual(2.0, threshold)

    def test_encoder_bias_is_part_of_the_learned_feature_boundary(self) -> None:
        model = BatchTopKSae(input_dimensions=2, dictionary_size=2, average_k=1)
        with torch.no_grad():
            model.encoder.weight.copy_(torch.eye(2))
            model.encoder.bias.copy_(torch.tensor([-2.0, 1.0]))
            model.decoder_bias.zero_()

        activations = model.dense_activations(torch.tensor([[1.0, 0.0]]))

        torch.testing.assert_close(activations, torch.tensor([[0.0, 1.0]]))


class SparseRelationTests(unittest.TestCase):
    def test_both_lookup_directions_share_one_canonical_relation(self) -> None:
        activations = torch.tensor(
            [
                [0.0, 0.8, 0.2],
                [0.7, 0.0, 0.0],
                [0.1, 0.0, 0.9],
            ],
            dtype=torch.float32,
        )

        relation = SparseRelation.from_activations(activations)

        note_topics = relation.topics_for_note(0)
        self.assertEqual([1, 2], [topic for topic, _ in note_topics])
        self.assertAlmostEqual(0.8, note_topics[0][1])
        self.assertAlmostEqual(0.2, note_topics[1][1])
        topic_notes = relation.notes_for_topic(0)
        self.assertEqual([1, 2], [note for note, _ in topic_notes])
        self.assertAlmostEqual(1.0, topic_notes[0][1])
        self.assertAlmostEqual(0.1, topic_notes[1][1])
        relation.validate()

    def test_activation_batches_build_the_same_relation_without_dense_join(self) -> None:
        activations = torch.tensor(
            [
                [0.0, 0.8, 0.2],
                [0.7, 0.0, 0.0],
                [0.1, 0.0, 0.9],
            ],
            dtype=torch.float32,
        )

        together = SparseRelation.from_activations(activations)
        streamed = SparseRelation.from_activation_batches(
            [activations[:2], activations[2:]], topic_count=3, maximum_entries=5
        )

        self.assertTrue(torch.equal(together.note_offsets, streamed.note_offsets))
        self.assertTrue(torch.equal(together.topic_ids, streamed.topic_ids))
        torch.testing.assert_close(together.weights, streamed.weights)
        self.assertTrue(
            torch.equal(together.topic_edge_order, streamed.topic_edge_order)
        )
        self.assertTrue(torch.equal(together.topic_offsets, streamed.topic_offsets))

    def test_only_features_active_on_learning_notes_become_topics(self) -> None:
        activations = torch.tensor(
            [[0.9, 0.0, 0.0], [0.8, 0.0, 0.0], [0.0, 0.7, 0.0]]
        )

        relation = SparseRelation.from_activation_batches(
            [activations],
            topic_count=3,
            maximum_entries=3,
            learning_note_count=2,
        )

        self.assertEqual(1, relation.topic_count)
        self.assertEqual([0], relation.source_topic_ids.tolist())
        self.assertEqual([], relation.topics_for_note(2))


class IoAdmissionTests(unittest.TestCase):
    def test_frozen_worker_identity_is_verified_before_input_open(self) -> None:
        config = ExperimentConfig.from_dict(
            {
                "schema_version": 1,
                "purpose": "test-worker-identity",
                "runtime": {
                    "worker_sha256": "0" * 64,
                    "container_image": "example.invalid/pinned@sha256:abc",
                },
                "input": {
                    "matrix_path": "/definitely/missing/vectors.f32le",
                    "note_ids_path": "/definitely/missing/note-ids.bin",
                    "dimensions": 2,
                    "start_row": 0,
                    "learning_rows": 1,
                    "evaluation_rows": 1,
                },
                "model": {
                    "dictionary_size": 2,
                    "average_k": 1,
                    "batch_size": 1,
                    "steps": 1,
                    "learning_rate": 0.001,
                    "seed": 1,
                },
                "io_budget": {
                    "max_source_read_bytes": 80,
                    "max_durable_write_bytes": 1048576,
                },
                "output_path": "/tmp/must-not-exist",
            }
        )

        with self.assertRaisesRegex(ValueError, "worker implementation"):
            run_experiment(config)

    def test_measurement_steps_must_be_strictly_increasing_and_bounded(self) -> None:
        raw = {
            "schema_version": 1,
            "purpose": "test-measurement-step-validation",
            "input": {
                "matrix_path": "/definitely/missing/vectors.f32le",
                "note_ids_path": "/definitely/missing/note-ids.bin",
                "dimensions": 2,
                "start_row": 0,
                "learning_rows": 2,
                "evaluation_rows": 1,
            },
            "model": {
                "dictionary_size": 2,
                "average_k": 1,
                "batch_size": 1,
                "steps": 4,
                "measurement_steps": [1, 3, 3],
                "learning_rate": 0.001,
                "seed": 1,
            },
            "io_budget": {
                "max_source_read_bytes": 108,
                "max_durable_write_bytes": 1048576,
            },
            "output_path": "/tmp/must-not-exist",
        }

        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            ExperimentConfig.from_dict(raw)
        raw["model"]["measurement_steps"] = [1, 5]
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            ExperimentConfig.from_dict(raw)

    def test_plan_is_rejected_before_input_open_when_read_budget_is_exceeded(self) -> None:
        budget = IoBudget(max_source_read_bytes=64, max_durable_write_bytes=64)
        plan = IoPlan(source_read_bytes=65, durable_write_bytes=0)

        with self.assertRaisesRegex(ValueError, "source-read budget"):
            plan.require_admitted(budget)

    def test_plan_is_rejected_before_input_open_when_write_budget_is_exceeded(self) -> None:
        budget = IoBudget(max_source_read_bytes=64, max_durable_write_bytes=64)
        plan = IoPlan(source_read_bytes=64, durable_write_bytes=65)

        with self.assertRaisesRegex(ValueError, "durable-write budget"):
            plan.require_admitted(budget)

    def test_experiment_rejects_budget_before_opening_missing_inputs(self) -> None:
        config = ExperimentConfig.from_dict(
            {
                "schema_version": 1,
                "purpose": "test-pre-open-admission",
                "input": {
                    "matrix_path": "/definitely/missing/vectors.f32le",
                    "note_ids_path": "/definitely/missing/note-ids.bin",
                    "dimensions": 2,
                    "start_row": 0,
                    "learning_rows": 1,
                    "evaluation_rows": 1,
                },
                "model": {
                    "dictionary_size": 2,
                    "average_k": 1,
                    "batch_size": 1,
                    "steps": 1,
                    "learning_rate": 0.001,
                    "seed": 1,
                },
                "io_budget": {
                    "max_source_read_bytes": 79,
                    "max_durable_write_bytes": 1048576,
                },
                "output_path": "/tmp/must-not-exist",
            }
        )

        with self.assertRaisesRegex(ValueError, "source-read budget"):
            run_experiment(config)


class FailureSafetyTests(unittest.TestCase):
    def test_wrong_embedding_manifest_hash_fails_before_matrix_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "embedding-manifest.json"
            manifest_path.write_text("{}\n")
            output_path = root / "result"
            config = ExperimentConfig.from_dict(
                {
                    "schema_version": 1,
                    "purpose": "test-manifest-hash-rejection",
                    "input": {
                        "matrix_path": str(root / "missing-vectors.f32le"),
                        "note_ids_path": str(root / "missing-note-ids.bin"),
                        "embedding_manifest": {
                            "path": str(manifest_path),
                            "bytes": manifest_path.stat().st_size,
                            "sha256": "0" * 64,
                        },
                        "dimensions": 2,
                        "start_row": 0,
                        "learning_rows": 1,
                        "evaluation_rows": 1,
                    },
                    "model": {
                        "dictionary_size": 2,
                        "average_k": 1,
                        "batch_size": 1,
                        "steps": 1,
                        "learning_rate": 0.001,
                        "seed": 1,
                    },
                    "io_budget": {
                        "max_source_read_bytes": (
                            80 + manifest_path.stat().st_size
                        ),
                        "max_durable_write_bytes": 1048576,
                    },
                    "output_path": str(output_path),
                }
            )

            with self.assertRaisesRegex(ValueError, "manifest hash"):
                run_experiment(config)
            self.assertFalse(output_path.exists())

    def test_nonfinite_input_is_rejected_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matrix_path = root / "vectors.f32le"
            note_ids_path = root / "note-ids.bin"
            output_path = root / "result"
            matrix_path.write_bytes(struct.pack("<4f", 1.0, 0.0, float("nan"), 1.0))
            note_ids_path.write_bytes(bytes(64))
            config = ExperimentConfig.from_dict(
                {
                    "schema_version": 1,
                    "purpose": "test-nonfinite-rejection",
                    "input": {
                        "matrix_path": str(matrix_path),
                        "note_ids_path": str(note_ids_path),
                        "dimensions": 2,
                        "start_row": 0,
                        "learning_rows": 1,
                        "evaluation_rows": 1,
                    },
                    "model": {
                        "dictionary_size": 2,
                        "average_k": 1,
                        "batch_size": 1,
                        "steps": 1,
                        "learning_rate": 0.001,
                        "seed": 1,
                    },
                    "io_budget": {
                        "max_source_read_bytes": 80,
                        "max_durable_write_bytes": 1048576,
                    },
                    "output_path": str(output_path),
                }
            )

            with self.assertRaisesRegex(ValueError, "non-finite"):
                run_experiment(config)

            self.assertFalse(output_path.exists())

    def test_duplicate_note_ids_are_rejected(self) -> None:
        activations = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
        duplicate_ids = torch.zeros((2, 32), dtype=torch.uint8)

        with self.assertRaisesRegex(ValueError, "not unique"):
            SparseRelation.from_activation_batches(
                [activations],
                topic_count=2,
                maximum_entries=2,
                note_ids=duplicate_ids,
            )


class ProductionPathTests(unittest.TestCase):
    def test_tiny_experiment_publishes_a_reopenable_weighted_relation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matrix_path = root / "vectors.f32le"
            note_ids_path = root / "note-ids.bin"
            output_path = root / "result"
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
            note_ids = [bytes([index]) * 32 for index in range(len(vectors))]
            note_ids_path.write_bytes(b"".join(note_ids))
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
            raw_config = {
                "schema_version": 1,
                "purpose": "test-production-path",
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
                    "steps": 8,
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
            config = ExperimentConfig.from_dict(raw_config)

            report = run_experiment(config)

            self.assertEqual(8, report.total_rows)
            self.assertEqual(8, report.dictionary_size)
            self.assertEqual([], report.training_trace)
            self.assertTrue((output_path / "manifest.json").is_file())
            manifest = json.loads((output_path / "manifest.json").read_text())
            self.assertEqual("canonical-sparse-note-topic-relation-v1", manifest["relation_format"])
            self.assertEqual(
                embedding_manifest_sha256,
                manifest["metadata"]["embedding_manifest_sha256"],
            )
            relation = SparseRelation.open(output_path)
            relation.validate()
            self.assertEqual(8, relation.note_count)
            self.assertEqual(note_ids[0], relation.note_id(0))
            self.assertEqual(
                relation.topics_for_note(0),
                relation.topics_for_note_id(note_ids[0]),
            )

            second_output = root / "second-result"
            second_config = ExperimentConfig.from_dict(
                {**raw_config, "output_path": str(second_output)}
            )
            run_experiment(second_config)
            first_files = sorted(path.name for path in output_path.iterdir())
            self.assertEqual(
                first_files, sorted(path.name for path in second_output.iterdir())
            )
            for name in first_files:
                self.assertEqual(
                    (output_path / name).read_bytes(),
                    (second_output / name).read_bytes(),
                    name,
                )

            measured_output = root / "measured-result"
            measured_raw_config = json.loads(json.dumps(raw_config))
            measured_raw_config["model"]["measurement_steps"] = [2, 8]
            measured_raw_config["output_path"] = str(measured_output)
            measured_report = run_experiment(
                ExperimentConfig.from_dict(measured_raw_config)
            )
            self.assertEqual([2, 8], [
                point["step"] for point in measured_report.training_trace
            ])
            self.assertEqual([4, 16], [
                point["learning_rows_processed"]
                for point in measured_report.training_trace
            ])
            for point in measured_report.training_trace:
                self.assertTrue(math.isfinite(point["inference_threshold"]))
                for split in ("learning", "evaluation"):
                    metrics = point[split]
                    self.assertTrue(
                        math.isfinite(metrics["reconstruction_r2"])
                    )
                    self.assertTrue(
                        math.isfinite(
                            metrics["normalized_reconstruction_error"]
                        )
                    )
                    self.assertGreaterEqual(metrics["relation_entry_count"], 0)
                    self.assertGreaterEqual(metrics["unassigned_note_count"], 0)
            measured_manifest = json.loads(
                (measured_output / "manifest.json").read_text()
            )
            self.assertEqual(
                measured_report.training_trace,
                measured_manifest["metadata"]["training_trace"],
            )
            self.assertEqual(
                report.inference_threshold,
                measured_report.inference_threshold,
            )
            for name in first_files:
                if name == "manifest.json":
                    continue
                self.assertEqual(
                    (output_path / name).read_bytes(),
                    (measured_output / name).read_bytes(),
                    name,
                )

            original_matrix = matrix_path.read_bytes()
            matrix_path.write_bytes(
                bytes([original_matrix[0] ^ 0x01]) + original_matrix[1:]
            )
            mutated_output = root / "mutated-input-result"
            with self.assertRaisesRegex(ValueError, "matrix hash"):
                run_experiment(
                    ExperimentConfig.from_dict(
                        {**raw_config, "output_path": str(mutated_output)}
                    )
                )
            self.assertFalse(mutated_output.exists())

            with (output_path / "weights.f32le").open("r+b") as weights:
                first = weights.read(1)
                weights.seek(0)
                weights.write(bytes([first[0] ^ 0xFF]))
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                SparseRelation.open(output_path)


if __name__ == "__main__":
    unittest.main()
