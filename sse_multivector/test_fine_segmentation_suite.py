import tempfile
import unittest
import json
import struct
import hashlib
import hmac
from pathlib import Path

from sse_multivector.fine_segmentation_suite import (
    compile_approved_protocol,
    finalize_vector_artifact,
    freeze_suite,
    prepare_suite,
    verify_technical_freeze,
    verify_prepared_suite,
)
from sse_multivector.worker import canonical_tree_sha256


REPO_ROOT = Path(__file__).resolve().parents[1]
BLINDING_NAMESPACES = (
    "01-repeated-subject-recovery",
    "02-nearby-subject-resolution",
    "03-lexical-coincidence",
    "04-unmasked-context",
    "06-irrelevant-change-stability",
)


def test_namespace_seeds() -> dict[str, bytes]:
    return {
        namespace: bytes([ordinal]) * 32
        for ordinal, namespace in enumerate(BLINDING_NAMESPACES, start=1)
    }


class ApprovedProtocolTests(unittest.TestCase):
    def test_compiles_the_approved_fixture_and_complete_input_schedule(self) -> None:
        protocol = compile_approved_protocol(REPO_ROOT)

        self.assertEqual(207, len(protocol["encodings"]))
        self.assertEqual(
            {
                "candidate-conformance": 1,
                "experiment-01": 1,
                "experiment-02": 512,
                "experiment-03": 10,
                "experiment-04": 10,
                "experiment-06": 4,
            },
            protocol["logical_input_counts"],
        )
        self.assertEqual(538, len(protocol["inputs"]))
        self.assertEqual(
            {
                "experiment-01": 36,
                "experiment-02": 96,
                "experiment-03": 48,
                "experiment-04": 27,
            },
            protocol["encoding_counts"],
        )
        self.assertEqual(
            64,
            min(protocol["experiment_02_vector_appearance_counts"].values()),
        )
        self.assertEqual(
            64,
            max(protocol["experiment_02_vector_appearance_counts"].values()),
        )

    def test_prepared_suite_is_replay_verified_and_immutable(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            output = Path(directory) / "prepared"
            namespace_seeds = test_namespace_seeds()
            report = prepare_suite(
                REPO_ROOT,
                output,
                namespace_seeds=namespace_seeds,
                review_seed=bytes([9]) * 32,
            )

            self.assertEqual(207, report["encoding_count"])
            self.assertEqual(538, report["logical_input_count"])
            self.assertRegex(
                report["experiment_02_review_commitment"], r"^[0-9a-f]{64}$"
            )
            private = json.loads((output / "blinding-private.json").read_text())
            expected_origami_id = hmac.new(
                namespace_seeds["01-repeated-subject-recovery"],
                b"fine-segmentation-id-v1\0" b"01-repeated-subject-recovery\0ORIGAMI-1",
                hashlib.sha256,
            ).hexdigest()
            self.assertEqual(
                expected_origami_id,
                private["opaque_mapping"]["experiment-01"]["ORIGAMI-1"],
            )
            self.assertEqual(
                set(BLINDING_NAMESPACES), set(private["namespace_commitments"])
            )
            self.assertEqual(
                report["experiment_02_review_commitment"],
                private["experiment_02_review"]["commitment"],
            )
            self.assertEqual(report, verify_prepared_suite(REPO_ROOT, output))
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare_suite(
                    REPO_ROOT,
                    output,
                    namespace_seeds=namespace_seeds,
                    review_seed=bytes([9]) * 32,
                )

    def test_finalizes_and_replay_verifies_the_shared_worker_vectors(self) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            prepared = root / "prepared"
            prepare_suite(
                REPO_ROOT,
                prepared,
                namespace_seeds=test_namespace_seeds(),
                review_seed=bytes([9]) * 32,
            )
            request_sha = hashlib.sha256(
                (prepared / "worker-request.json").read_bytes()
            ).hexdigest()
            request = json.loads((prepared / "worker-request.json").read_text())

            worker = root / "worker"
            worker.mkdir()
            raw = bytearray()
            rows = []
            for ordinal, note in enumerate(request["notes"]):
                vector = [0.0] * 768
                vector[ordinal % 768] = 2.0
                raw.extend(struct.pack("<768f", *vector))
                rows.append(
                    {
                        "ordinal": ordinal,
                        "note_id": note["note_id"],
                        "subject_id": note["subjects"][0]["subject_id"],
                        "selected_token_indices": [1],
                        "selected_token_ids": [101],
                        "token_count": 3,
                    }
                )
            (worker / "raw-vectors.f32le").write_bytes(raw)
            receipt = {
                "schema_version": 1,
                "proposal_sha256": request["proposal_sha256"],
                "request_sha256": request_sha,
                "checkpoint_sha256": "a" * 64,
                "base_model_artifact_tree_sha256": "b" * 64,
                "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
                "model": {
                    "base_model": "sentence-transformers/sentence-t5-base",
                    "dimensions": 768,
                    "maximum_tokens": 512,
                    "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
                },
                "runtime": {"worker_sha256": "c" * 64},
                "device": "cpu",
                "container_image": "local/oracle-mvp-sse@sha256:" + "d" * 64,
                "note_batch_size": 8,
                "vector_format": "row-major-f32le-v1",
                "dimensions": 768,
                "row_count": 207,
                "rows": rows,
                "files": {
                    "raw-vectors.f32le": {
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                },
            }
            (worker / "worker-receipt.json").write_text(
                json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
            )
            freeze = root / "technical-freeze.json"
            freeze.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "suite_id": "fine-segmentation-controlled-suite-v1",
                        "encoder": {
                            "request_sha256": request_sha,
                            "checkpoint_sha256": "a" * 64,
                            "base_model_artifact_tree_sha256": "b" * 64,
                            "worker_sha256": "c" * 64,
                            "container_image": "local/oracle-mvp-sse@sha256:"
                            + "d" * 64,
                            "dimensions": 768,
                            "vector_format": "row-major-f32le-v1",
                        },
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

            report = finalize_vector_artifact(
                prepared, freeze, worker, root / "vectors"
            )
            self.assertEqual(207, report["vector_count"])
            self.assertEqual(635_904, report["raw_vector_bytes"])
            self.assertEqual(1.0, report["minimum_normalized_norm"])
            self.assertEqual(1.0, report["maximum_normalized_norm"])
            vector_map = json.loads((root / "vectors" / "vector-map.json").read_text())
            self.assertEqual([101], vector_map["vectors"][0]["selected_token_ids"])

            receipt["rows"][0].pop("selected_token_ids")
            (worker / "worker-receipt.json").write_text(
                json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
            )
            with self.assertRaisesRegex(ValueError, "invalid selected-token evidence"):
                finalize_vector_artifact(
                    prepared, freeze, worker, root / "vectors-missing-token-ids"
                )

    def test_freezes_encoder_candidate_and_protocol_identities_before_encoding(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            root = Path(directory)
            prepared = root / "prepared"
            prepare_suite(
                REPO_ROOT,
                prepared,
                namespace_seeds=test_namespace_seeds(),
                review_seed=bytes([9]) * 32,
            )

            checkpoint = root / "checkpoint.bin"
            checkpoint.write_bytes(b"checkpoint")
            worker = root / "worker.py"
            worker.write_text("# worker\n")
            model = root / "model"
            model.mkdir()
            (model / "tokenizer.json").write_text("{}\n")
            image = "local/test@sha256:" + "d" * 64
            encoder_config = root / "encoder.json"
            encoder_config.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "checkpoint_path": str(checkpoint),
                        "checkpoint_sha256": hashlib.sha256(
                            checkpoint.read_bytes()
                        ).hexdigest(),
                        "worker_path": str(worker),
                        "worker_sha256": hashlib.sha256(
                            worker.read_bytes()
                        ).hexdigest(),
                        "base_model_artifact_path": str(model),
                        "base_model_artifact_tree_sha256": canonical_tree_sha256(model),
                        "container_image": image,
                        "note_batch_size": 8,
                        "model": {
                            "base_model": "sentence-transformers/sentence-t5-base",
                            "dimensions": 768,
                            "maximum_tokens": 512,
                            "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
                        },
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )

            candidate = root / "candidate.py"
            candidate.write_text(
                """#!/usr/bin/env python3
import hashlib, json, sys
request = json.load(open(sys.argv[1]))
candidate = request["candidate"]
identity = {"snn":"snn-controlled-suite-config-v1","hdbscan":"hdbscan-controlled-suite-config-v1"}[candidate]
algorithm = {"snn":"snn-sdm-2003-exact-angular-v1","hdbscan":"hdbscan-star-exact-angular-v1"}[candidate]
selector = {"snn":"snn-segments-members-v1","hdbscan":"hdbscan-clusters-members-v1"}[candidate]
config = {"snn":"{\\\"neighbor_count\\\":5,\\\"minimum_shared_neighbor_count\\\":2,\\\"minimum_core_neighbor_count\\\":3}","hdbscan":"{\\\"min_samples\\\":2,\\\"min_cluster_size\\\":2,\\\"selection_method\\\":\\\"excess_of_mass\\\"}"}[candidate]
print(json.dumps({"schema_version":1,"candidate_identity":identity,"artifact":{"manifest":{"algorithm_version":algorithm,"input_contract_version":"opaque-id-order-bitwise-vector-alias-v1","fine_output_selector_version":selector,"adapter_implementation_source_sha256":"1"*64,"algorithm_implementation_source_sha256":"2"*64,"preprocessing_implementation_source_sha256":"3"*64,"configuration_sha256":hashlib.sha256(config.encode()).hexdigest(),"tie_rule_version":"test-tie-v1"},"canonical_configuration_json":config}}))
"""
            )
            candidate.chmod(0o755)

            output = root / "technical-freeze.json"
            report = freeze_suite(
                REPO_ROOT, prepared, encoder_config, candidate, output
            )
            self.assertEqual(207, report["encoding_count"])
            self.assertEqual(2, report["candidate_count"])
            frozen = json.loads(output.read_text())
            self.assertEqual(
                frozen["encoder"]["byte_span_rule"],
                "complete-token-contained-in-utf8-byte-span-union-v2",
            )
            prepared_private = json.loads(
                (prepared / "blinding-private.json").read_text()
            )
            self.assertEqual(
                prepared_private["experiment_02_review"]["commitment"],
                frozen["experiment_02_review_commitment"],
            )
            self.assertIn(
                "sse_multivector/fine_segmentation_suite.py",
                frozen["suite_implementation"]["files"],
            )
            self.assertIn(
                "sse_multivector/fine_segmentation_candidate_runs.py",
                frozen["suite_implementation"]["files"],
            )
            self.assertIn(
                "sse_multivector/fine_segmentation_encoder.py",
                frozen["suite_implementation"]["files"],
            )
            self.assertEqual(
                report, verify_technical_freeze(REPO_ROOT, prepared, output)
            )


if __name__ == "__main__":
    unittest.main()
