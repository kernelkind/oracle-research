import copy
import hashlib
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

from sse_multivector.real_note_segmentation import (
    finalize_vectors,
    package_review,
    prepare_reviewed_inputs,
)
from sse_multivector.worker import _load_request


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewedInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.reviewed = self.root / "reviewed.json"
        self.encoder = self.root / "encoder.json"
        self.subject_package = self.root / "as.json"
        self.mask_package = self.root / "mp.json"
        self.document = {
            "schema_version": 1,
            "provenance": {"review": "saved/review.json"},
            "notes": [
                {
                    "note_id": "1" * 64,
                    "text": "☕ Rust / Rust",
                    "provenance": {"source": "saved/input.json"},
                    "subjects": [
                        {
                            "id": "S1",
                            "subject": "Coffee and Rust.",
                            "fragments": ["☕", "Rust"],
                            "byte_spans": [[0, 3], [11, 15]],
                            "judgment": "accepted",
                            "raw_mask": '["☕", "Rust"]',
                            "provenance": {"reviewer": "saved primary agent"},
                        },
                        {"id": "S2", "subject": "Unsupported.", "judgment": "rejected"},
                        {"id": "S3", "subject": "Unclear.", "judgment": "unresolved"},
                    ],
                },
                {
                    "note_id": "2" * 64,
                    "text": "Rust",
                    "subjects": [
                        {
                            "id": "S1",
                            "subject": "Rust.",
                            "fragments": ["Rust"],
                            "byte_spans": [[0, 4]],
                            "judgment": "accepted",
                        }
                    ],
                },
            ],
        }
        self.descriptor = {
            "schema_version": 1,
            "checkpoint_path": "unused/checkpoint",
            "checkpoint_sha256": "a" * 64,
            "base_model_artifact_path": "unused/model",
            "base_model_artifact_tree_sha256": "b" * 64,
            "worker_path": "sse_multivector/worker.py",
            "worker_sha256": "c" * 64,
            "container_image": "sha256:" + "d" * 64,
            "note_batch_size": 8,
            "model": {
                "base_model": "sentence-transformers/sentence-t5-base",
                "dimensions": 2,
                "maximum_tokens": 512,
                "pooling": "selected-contextual-token-mean-linear-relu-linear-v1",
            },
        }
        _write(self.reviewed, self.document)
        _write(self.encoder, self.descriptor)
        _write(self.subject_package, {"status": "frozen", "version": "ASv6.23"})
        _write(self.mask_package, {"status": "frozen", "version": "MPv3.5"})

    def prepare(self, name="prepared"):
        output = self.root / name
        prepare_reviewed_inputs(
            self.reviewed, self.encoder, self.subject_package, self.mask_package, output
        )
        return output

    def worker_output(self, prepared, values=(3.0, 4.0, 5.0, 12.0)):
        output = self.root / "worker"
        output.mkdir()
        raw = struct.pack(f"<{len(values)}f", *values)
        (output / "raw-vectors.f32le").write_bytes(raw)
        request_path = prepared / "worker-request.json"
        request = json.loads(request_path.read_text())
        rows = [
            {
                "ordinal": ordinal,
                "note_id": note["note_id"],
                "subject_id": subject["subject_id"],
                "selected_token_indices": [1],
                "selected_token_ids": [101],
                "token_count": 3,
            }
            for ordinal, (note, subject) in enumerate(
                (note, subject)
                for note in request["notes"]
                for subject in note["subjects"]
            )
        ]
        receipt = {
            "schema_version": 1,
            "proposal_sha256": request["proposal_sha256"],
            "request_sha256": _sha(request_path),
            "checkpoint_sha256": self.descriptor["checkpoint_sha256"],
            "base_model_artifact_tree_sha256": self.descriptor[
                "base_model_artifact_tree_sha256"
            ],
            "tree_hash_rule": "sorted-relative-path-type-size-content-sha256-v1",
            "model": self.descriptor["model"],
            "runtime": {"worker_sha256": self.descriptor["worker_sha256"]},
            "container_image": self.descriptor["container_image"],
            "device": "cpu",
            "note_batch_size": 8,
            "vector_format": "row-major-f32le-v1",
            "dimensions": 2,
            "row_count": len(rows),
            "rows": rows,
            "files": {
                "raw-vectors.f32le": {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            },
        }
        _write(output / "worker-receipt.json", receipt)
        return output, receipt

    def test_prepares_exact_explicit_utf8_masks_and_preserves_review_provenance(self):
        prepared = self.prepare()
        _, notes = _load_request(prepared / "worker-request.json")
        self.assertEqual("☕ Rust / Rust", notes[0].text)
        self.assertEqual(((0, 3), (11, 15)), notes[0].subjects[0].byte_spans)
        self.assertEqual(2, sum(len(note.subjects) for note in notes))
        self.assertNotEqual(
            notes[0].subjects[0].subject_id, notes[1].subjects[0].subject_id
        )
        self.assertEqual(
            self.reviewed.read_bytes(), (prepared / "reviewed-input.json").read_bytes()
        )
        mapping = json.loads((prepared / "vector-map.json").read_text())
        self.assertEqual(
            ["V001", "V002"], [row["short_id"] for row in mapping["vectors"]]
        )
        self.assertEqual(
            ["N001", "N002"], [row["note_short_id"] for row in mapping["vectors"]]
        )
        self.assertEqual(
            ["rejected", "unresolved"], [row["judgment"] for row in mapping["excluded"]]
        )
        for row in mapping["vectors"]:
            self.assertRegex(row["vector_id"], "^[0-9a-f]{64}$")
            self.assertRegex(row["worker_subject_id"], "^[0-9a-f]{16}$")
        second = self.prepare("prepared-again")
        self.assertEqual(
            (prepared / "vector-map.json").read_bytes(),
            (second / "vector-map.json").read_bytes(),
        )
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()

    def test_rejects_missing_or_inexact_overlapping_and_unordered_spans(self):
        invalid = [
            (None, ["Rust"], "byte_spans"),
            ([[0, 1]], ["☕"], "UTF-8"),
            ([[4, 8]], ["rust"], "exact"),
            ([[4, 8], [6, 8]], ["Rust", "st"], "overlap"),
            ([[11, 15], [4, 8]], ["Rust", "Rust"], "order"),
            ([[True, 3]], ["☕"], "integer"),
            ([[0, 3]], [], "fragments"),
        ]
        for index, (spans, fragments, error) in enumerate(invalid):
            with self.subTest(index=index):
                document = copy.deepcopy(self.document)
                subject = document["notes"][0]["subjects"][0]
                subject["fragments"] = fragments
                if spans is None:
                    del subject["byte_spans"]
                else:
                    subject["byte_spans"] = spans
                _write(self.reviewed, document)
                with self.assertRaisesRegex(ValueError, error):
                    self.prepare(f"invalid-{index}")
                self.assertFalse((self.root / f"invalid-{index}").exists())

    def test_rejects_duplicate_notes_unknown_judgments_and_unfrozen_packages(self):
        document = copy.deepcopy(self.document)
        document["notes"][1]["note_id"] = document["notes"][0]["note_id"]
        _write(self.reviewed, document)
        with self.assertRaisesRegex(ValueError, "duplicate note"):
            self.prepare()
        document = copy.deepcopy(self.document)
        document["notes"][0]["subjects"][0]["judgment"] = "probably accepted"
        _write(self.reviewed, document)
        with self.assertRaisesRegex(ValueError, "judgment"):
            self.prepare()
        _write(self.reviewed, self.document)
        _write(self.mask_package, {"status": "draft", "version": "MPv3.5"})
        with self.assertRaisesRegex(ValueError, "frozen"):
            self.prepare()

    def test_finalizes_exact_f64_vectors_and_bound_candidate_request(self):
        prepared = self.prepare()
        worker, _ = self.worker_output(prepared)
        output = self.root / "vectors"
        report = finalize_vectors(prepared, worker, output)
        self.assertEqual(2, report["vector_count"])
        normalized = (output / "normalized-vectors.f64le").read_bytes()
        self.assertEqual((0.6, 0.8, 5 / 13, 12 / 13), struct.unpack("<4d", normalized))
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(
            "row-major-f32le-to-exact-f64-l2-normalized-f64le-v1",
            manifest["raw_decode_and_normalization_contract"],
        )
        request = json.loads((output / "candidate-request.json").read_text())
        self.assertEqual("hdbscan", request["candidate"])
        self.assertEqual(
            _sha(output / "manifest.json"), request["source_vector_manifest_sha256"]
        )
        self.assertEqual(
            _sha(output / "normalized-vectors.f64le"),
            request["normalized_vector_sha256"],
        )
        self.assertEqual([0.6, 0.8], request["inputs"][0]["normalized_vector"])
        self.assertEqual(
            (worker / "raw-vectors.f32le").read_bytes(),
            (output / "raw-vectors.f32le").read_bytes(),
        )
        with self.assertRaisesRegex(ValueError, "already exists"):
            finalize_vectors(prepared, worker, output)

    def test_rejects_changed_source_and_wrong_row_or_token_evidence(self):
        prepared = self.prepare()
        worker, receipt = self.worker_output(prepared)
        self.reviewed.write_bytes(self.reviewed.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "source.*hash"):
            finalize_vectors(prepared, worker, self.root / "bad-source")
        _write(self.reviewed, self.document)
        for field, value, error in [
            ("ordinal", 1, "row order"),
            ("subject_id", "f" * 16, "row order"),
            ("selected_token_ids", [], "selected-token"),
        ]:
            with self.subTest(field=field):
                changed = copy.deepcopy(receipt)
                changed["rows"][0][field] = value
                _write(worker / "worker-receipt.json", changed)
                with self.assertRaisesRegex(ValueError, error):
                    finalize_vectors(prepared, worker, self.root / f"bad-{field}")

    def test_rejects_nonfinite_zero_truncated_and_hash_mismatched_raw_vectors(self):
        prepared = self.prepare()
        worker, receipt = self.worker_output(prepared)
        for index, values in enumerate(
            [(math.nan, 1, 5, 12), (math.inf, 1, 5, 12), (0, 0, 5, 12), (3, 4)]
        ):
            with self.subTest(values=values):
                raw = struct.pack(f"<{len(values)}f", *values)
                (worker / "raw-vectors.f32le").write_bytes(raw)
                changed = copy.deepcopy(receipt)
                changed["files"]["raw-vectors.f32le"] = {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
                _write(worker / "worker-receipt.json", changed)
                with self.assertRaisesRegex(ValueError, "finite|norm|byte count"):
                    finalize_vectors(
                        prepared, worker, self.root / f"bad-vector-{index}"
                    )
        _write(worker / "worker-receipt.json", receipt)
        (worker / "raw-vectors.f32le").write_bytes(struct.pack("<4f", 3, 4, 5, 11))
        with self.assertRaisesRegex(ValueError, "raw vector.*hash"):
            finalize_vectors(prepared, worker, self.root / "bad-hash")

    def packaging_vectors(self):
        self.document["notes"][0]["subjects"].append(
            {
                "id": "S4",
                "subject": "Coffee.",
                "fragments": ["☕"],
                "byte_spans": [[0, 3]],
                "judgment": "accepted",
            }
        )
        _write(self.reviewed, self.document)
        prepared = self.prepare()
        worker, _ = self.worker_output(prepared, (3, 4, 5, 12, 8, 15))
        vectors = self.root / "vectors"
        finalize_vectors(prepared, worker, vectors)
        return vectors

    def candidate_response(self, vectors, segments=None, unassigned=None):
        request = json.loads((vectors / "candidate-request.json").read_text())
        ids = [item["opaque_id"] for item in request["inputs"]]
        fine = {
            "segments": [ids[:2]] if segments is None else segments,
            "unassigned": ids[2:] if unassigned is None else unassigned,
        }
        parameters = {
            "min_samples": 2,
            "min_cluster_size": 2,
            "selection_method": "excess_of_mass",
        }
        configuration = json.dumps(parameters, separators=(",", ":"))
        fine_json = json.dumps(fine, separators=(",", ":"))
        canonical_input = bytearray(b"fine-region-candidate-input-v1\0")
        for item in sorted(request["inputs"], key=lambda item: item["opaque_id"]):
            canonical_input.extend(item["opaque_id"].encode("ascii"))
            canonical_input.extend(len(item["normalized_vector"]).to_bytes(8, "big"))
            for value in item["normalized_vector"]:
                canonical_input.extend(struct.pack(">d", value))
        response = {
            "schema_version": 1,
            "candidate_identity": "hdbscan-controlled-suite-config-v1",
            "artifact": {
                "manifest": {
                    "schema_version": 4,
                    "algorithm_version": "hdbscan-star-exact-angular-v1",
                    "fine_output_selector_version": "hdbscan-clusters-members-v1",
                    "source_vector_manifest_sha256": _sha(vectors / "manifest.json"),
                    "normalized_vector_sha256": _sha(
                        vectors / "normalized-vectors.f64le"
                    ),
                    "canonical_input_sha256": hashlib.sha256(
                        canonical_input
                    ).hexdigest(),
                    "configuration_sha256": hashlib.sha256(
                        configuration.encode()
                    ).hexdigest(),
                    "parameters": parameters,
                    "vector_count": len(ids),
                    "unique_vector_count": len(ids),
                    "fine_output_sha256": hashlib.sha256(
                        fine_json.encode()
                    ).hexdigest(),
                },
                "canonical_input_ids": sorted(ids),
                "canonical_configuration_json": configuration,
                "canonical_fine_output_json": fine_json,
                "result": {"fine_output": fine},
            },
        }
        path = self.root / "candidate.json"
        _write(path, response)
        return path, response, ids

    def test_packages_all_masks_in_same_note_segment_and_separate_noise_without_labels(
        self,
    ):
        vectors = self.packaging_vectors()
        candidate, _, ids = self.candidate_response(vectors)
        output = self.root / "review"
        package_review(vectors, candidate, output)
        review = json.loads((output / "review.json").read_text())
        self.assertEqual(3, review["schema_version"])
        self.assertEqual(
            ["packet", "verdict", "comment"],
            review["response_contract"]["judgment_fields"],
        )
        self.assertEqual(
            "zero or one judgment for every packet",
            review["response_contract"]["judgments"],
        )
        self.assertEqual(1, len(review["packets"]))
        packet = review["packets"][0]
        self.assertRegex(packet["packet"], r"^S[0-9a-f]{10}$")
        self.assertEqual(
            set(ids[:2]), {item["vector_id"] for item in packet["instances"]}
        )
        self.assertEqual({"1" * 64}, {item["note_id"] for item in packet["instances"]})
        for item in packet["instances"]:
            self.assertEqual(
                {"instance", "note_id", "vector_id", "text", "byte_spans"}, set(item)
            )
            self.assertEqual("☕ Rust / Rust", item["text"])
        first = next(item for item in packet["instances"] if item["instance"] == "V001")
        self.assertEqual([[0, 3], [11, 15]], first["byte_spans"])
        self.assertNotIn("Coffee", (output / "review.json").read_text())
        noise = json.loads((output / "unassigned.json").read_text())
        self.assertEqual([ids[2]], [item["vector_id"] for item in noise["instances"]])
        self.assertEqual("Rust", noise["instances"][0]["text"])
        self.assertIn("not segments", (output / "unassigned.txt").read_text())
        self.assertIn("⟦Rust⟧", (output / "unassigned.txt").read_text())
        metadata = json.loads((output / "metadata.json").read_text())
        self.assertEqual(1, metadata["segment_count"])
        self.assertEqual(1, metadata["unassigned_count"])
        self.assertEqual(1, metadata["segments"][0]["distinct_note_count"])
        self.assertRegex(metadata["segments"][0]["membership_sha256"], "^[0-9a-f]{64}$")
        self.assertFalse((output / "response.json").exists())
        with self.assertRaisesRegex(ValueError, "already exists"):
            package_review(vectors, candidate, output)

    def test_package_keeps_packet_evidence_stable_across_config_and_member_order(self):
        vectors = self.packaging_vectors()
        candidate, response, ids = self.candidate_response(vectors)
        package_review(vectors, candidate, self.root / "review-a")
        candidate, response, _ = self.candidate_response(
            vectors, [list(reversed(ids[:2]))]
        )
        response["candidate_identity"] = "hdbscan-explicit-config-v1"
        parameters = response["artifact"]["manifest"]["parameters"]
        parameters["min_samples"] = 3
        configuration = json.dumps(parameters, separators=(",", ":"))
        response["artifact"]["canonical_configuration_json"] = configuration
        response["artifact"]["manifest"]["configuration_sha256"] = hashlib.sha256(
            configuration.encode()
        ).hexdigest()
        _write(candidate, response)
        package_review(vectors, candidate, self.root / "review-b")
        self.assertEqual(
            (self.root / "review-a/review.json").read_bytes(),
            (self.root / "review-b/review.json").read_bytes(),
        )

    def test_package_all_noise_is_an_empty_review_not_a_successful_segment(self):
        vectors = self.packaging_vectors()
        _, _, ids = self.candidate_response(vectors)
        candidate, _, _ = self.candidate_response(vectors, [], ids)
        package_review(vectors, candidate, self.root / "review")
        review = json.loads((self.root / "review/review.json").read_text())
        noise = json.loads((self.root / "review/unassigned.json").read_text())
        self.assertEqual([], review["packets"])
        self.assertEqual(3, len(noise["instances"]))

    def test_package_rejects_unknown_duplicate_and_missing_partition_members(self):
        vectors = self.packaging_vectors()
        _, _, ids = self.candidate_response(vectors)
        invalid = [
            ([[ids[0], "f" * 64]], ids[1:]),
            ([[ids[0], ids[0]]], ids[1:]),
            ([[ids[0]], ids[:2]], ids[2:]),
            ([ids[:2]], ids[1:]),
            ([ids[:2]], []),
        ]
        for index, (segments, noise) in enumerate(invalid):
            with self.subTest(index=index):
                candidate, _, _ = self.candidate_response(vectors, segments, noise)
                with self.assertRaisesRegex(ValueError, "partition|member"):
                    package_review(vectors, candidate, self.root / f"bad-{index}")

    def test_package_rejects_changed_source_vector_and_candidate_hashes(self):
        vectors = self.packaging_vectors()
        candidate, response, _ = self.candidate_response(vectors)
        for field in (
            "source_vector_manifest_sha256",
            "normalized_vector_sha256",
            "canonical_input_sha256",
            "configuration_sha256",
            "fine_output_sha256",
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(response)
                changed["artifact"]["manifest"][field] = "f" * 64
                _write(candidate, changed)
                with self.assertRaisesRegex(ValueError, "hash|source|bound"):
                    package_review(vectors, candidate, self.root / field)
        _write(candidate, response)
        mapping = vectors / "vector-map.json"
        mapping.write_bytes(mapping.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "hash"):
            package_review(vectors, candidate, self.root / "bad-map")

    def test_package_rejects_a_missing_declared_worker_receipt(self):
        vectors = self.packaging_vectors()
        candidate, _, _ = self.candidate_response(vectors)
        (vectors / "worker-receipt.json").unlink()
        output = self.root / "review-with-missing-receipt"
        with self.assertRaisesRegex(ValueError, "worker-receipt.json"):
            package_review(vectors, candidate, output)
        self.assertFalse(output.exists())

    def test_package_rejects_a_changed_declared_encoder_descriptor(self):
        vectors = self.packaging_vectors()
        candidate, _, _ = self.candidate_response(vectors)
        descriptor = vectors / "encoder.json"
        descriptor.write_bytes(descriptor.read_bytes() + b" ")
        output = self.root / "review-with-changed-encoder"
        with self.assertRaisesRegex(ValueError, "encoder.json"):
            package_review(vectors, candidate, output)
        self.assertFalse(output.exists())

    def test_package_reports_the_full_candidate_result_replay_requirement(self):
        vectors = self.packaging_vectors()
        candidate, _, _ = self.candidate_response(vectors)
        metadata = package_review(vectors, candidate, self.root / "review")
        verification = metadata.get("candidate_result_verification", {})
        self.assertIs(verification.get("result_sha256_checked"), False)
        self.assertIn("pinned", verification.get("required_external_check", ""))
        self.assertIn("full parsed response", verification["required_external_check"])


if __name__ == "__main__":
    unittest.main()
