import copy
import hashlib
import json
import unittest

from sse_multivector import test_real_note_segmentation as fixtures
from sse_multivector.real_note_segmentation import package_review


class CrossNoteReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ReviewedInputTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.vectors = self.fixture.packaging_vectors()
        self.candidate, self.response, _ = self.fixture.candidate_response(self.vectors)
        mapping = json.loads((self.vectors / "vector-map.json").read_text())
        source_notes = {row["vector_id"]: row["note_id"] for row in mapping["vectors"]}
        self.cross_note = {
            "core_distance_rule_version": "nearest-different-source-note-angular-v1",
            "source_note_ids_sha256": hashlib.sha256(
                json.dumps(source_notes, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }

    def cross_note_response(self):
        response = copy.deepcopy(self.response)
        response["candidate_identity"] = "hdbscan-cross-note-controlled-suite-config-v1"
        manifest = response["artifact"]["manifest"]
        manifest["algorithm_version"] = "hdbscan-star-cross-note-exact-angular-v1"
        manifest["cross_note"] = copy.deepcopy(self.cross_note)
        return response

    def package(self, response, name="review"):
        fixtures._write(self.candidate, response)
        return package_review(self.vectors, self.candidate, self.root / name)

    def test_cross_note_review_exposes_verified_rule_and_source_note_map_hash(self):
        metadata = self.package(self.cross_note_response())
        self.assertEqual(self.cross_note, metadata["cross_note"])
        saved = json.loads((self.root / "review/metadata.json").read_text())
        self.assertEqual(self.cross_note, saved["cross_note"])
        self.assertEqual(1, metadata["segment_count"])
        self.assertEqual(1, metadata["unassigned_count"])

    def test_cross_note_review_rejects_missing_changed_or_extra_note_metadata(self):
        invalid = [
            None,
            {},
            {**self.cross_note, "source_note_ids_sha256": "f" * 64},
            {**self.cross_note, "core_distance_rule_version": "different-rule"},
            {**self.cross_note, "unexpected": True},
        ]
        for index, value in enumerate(invalid):
            with self.subTest(value=value):
                response = self.cross_note_response()
                if value is None:
                    del response["artifact"]["manifest"]["cross_note"]
                else:
                    response["artifact"]["manifest"]["cross_note"] = value
                with self.assertRaisesRegex(ValueError, "cross.note"):
                    self.package(response, f"invalid-{index}")
                self.assertFalse((self.root / f"invalid-{index}").exists())

    def test_cross_note_metadata_must_match_the_algorithm_and_identity(self):
        responses = []
        response = self.cross_note_response()
        response["candidate_identity"] = self.response["candidate_identity"]
        responses.append(response)
        response = copy.deepcopy(self.response)
        response["artifact"]["manifest"]["cross_note"] = self.cross_note
        responses.append(response)
        response = copy.deepcopy(self.response)
        response["candidate_identity"] = "hdbscan-cross-note-controlled-suite-config-v1"
        responses.append(response)
        for index, response in enumerate(responses):
            with self.subTest(index=index):
                with self.assertRaisesRegex(ValueError, "cross.note"):
                    self.package(response, f"mismatched-{index}")

    def test_cross_note_review_retains_frozen_evidence_and_source_hash_checks(self):
        response = self.cross_note_response()
        response["artifact"]["manifest"]["canonical_input_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "source hash"):
            self.package(response, "changed-input")
        mapping = self.vectors / "vector-map.json"
        mapping.write_bytes(mapping.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "vector-map.json"):
            self.package(self.cross_note_response(), "changed-map")

    def test_standard_review_stays_without_cross_note_metadata_and_same_packets(self):
        standard = self.package(self.response, "standard")
        self.assertNotIn("cross_note", standard)
        self.package(self.cross_note_response(), "cross-note")
        self.assertEqual(
            (self.root / "standard/review.json").read_bytes(),
            (self.root / "cross-note/review.json").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
