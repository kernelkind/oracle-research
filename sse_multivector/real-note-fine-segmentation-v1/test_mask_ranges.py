import tempfile
import unittest
from pathlib import Path

from generation import read, write
from mask_ranges import apply_decisions, enumerate_placements, prepare
from sse_multivector.real_note_segmentation import prepare_reviewed_inputs


class MaskRangeTests(unittest.TestCase):
    def test_enumerates_utf8_overlapping_occurrences_but_disjoint_ordered_masks(self):
        result = enumerate_placements("☕ Rust / Rust", ["☕", "Rust"])
        self.assertEqual([[[0, 3], [4, 8]], [[0, 3], [11, 15]]], result["placements"])
        self.assertTrue(result["alternatives_complete"])
        self.assertEqual(
            [[[0, 2], [2, 4]]], enumerate_placements("aaaa", ["aa", "aa"])["placements"]
        )
        self.assertEqual(
            [], enumerate_placements("Rust ☕", ["☕", "Rust"])["placements"]
        )
        with self.assertRaisesRegex(ValueError, "nonempty"):
            enumerate_placements("abc", [""])

    def test_reports_combinatorial_overflow_without_claiming_unique_placement(self):
        result = enumerate_placements("a " * 30, ["a"] * 10, limit=5)
        self.assertFalse(result["alternatives_complete"])
        self.assertEqual("overflow", result["placement_status"])
        self.assertEqual(5, len(result["placements"]))

    def source(self, root):
        source = root / "review.json"
        write(
            source,
            {
                "schema_version": 1,
                "stage": "masks",
                "notes": [
                    {
                        "note_id": "a" * 64,
                        "text": "☕ Rust / Rust",
                        "subjects": [
                            {
                                "id": "S1",
                                "subject": "Coffee and Rust.",
                                "judgment": "accepted",
                                "provenance": {"subject_review": "saved"},
                            },
                            {"id": "S2", "subject": "Coffee.", "judgment": "accepted"},
                        ],
                        "outputs": [
                            {
                                "call_id": "N001-S001-MP",
                                "subject_index": 0,
                                "status": "succeeded",
                                "raw_response": '["☕", "Rust"]',
                                "parsed_response": ["☕", "Rust"],
                            },
                            {
                                "call_id": "N001-S002-MP",
                                "subject_index": 1,
                                "status": "succeeded",
                                "raw_response": '["☕"]',
                                "parsed_response": ["☕"],
                            },
                        ],
                    }
                ],
            },
        )
        return source

    def test_preparation_keeps_unique_positions_separate_from_semantic_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.source(root)
            prepare(source, root / "prepared")
            result = read(root / "prepared/placements.json")
            self.assertEqual(
                ["ambiguous", "unique"],
                [call["placement_status"] for call in result["calls"]],
            )
            self.assertTrue(all("judgment" not in call for call in result["calls"]))
            self.assertEqual(
                source.read_bytes(), (root / "prepared/source-review.json").read_bytes()
            )
            rendered = (root / "prepared/review.txt").read_text()
            self.assertIn("⟦☕⟧ Rust / Rust", rendered)
            self.assertIn("☕ Rust / Rust", rendered)
            self.assertNotIn("⟦☕⟧ ⟦Rust⟧ / Rust", rendered)
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare(source, root / "prepared")

    def test_applies_only_explicit_decisions_and_preserves_raw_masks_and_alternatives(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(self.source(root), root / "prepared")
            decisions = root / "decisions.json"
            write(
                decisions,
                {
                    "schema_version": 1,
                    "reviewer": "primary assistant",
                    "decisions": {
                        "N001-S001-MP": {
                            "judgment": "accepted",
                            "reason": "Explicit review.",
                            "byte_spans": [[0, 3], [11, 15]],
                        },
                    },
                },
            )
            apply_decisions(root / "prepared", decisions, root / "applied")
            result = read(root / "applied/reviewed-input.json")
            accepted, pending = result["notes"][0]["subjects"]
            self.assertEqual("accepted", accepted["judgment"])
            self.assertEqual([[0, 3], [11, 15]], accepted["byte_spans"])
            self.assertEqual(
                '["☕", "Rust"]', accepted["provenance"]["mask_review"]["raw_mask"]
            )
            self.assertEqual(
                2, len(accepted["provenance"]["mask_review"]["raw_placements"])
            )
            self.assertEqual("saved", accepted["provenance"]["subject_review"])
            self.assertEqual("unresolved", pending["judgment"])
            self.assertNotIn("byte_spans", pending)
            self.assertIn(
                "⟦☕⟧ Rust / ⟦Rust⟧", (root / "applied/review.txt").read_text()
            )
            self.assertEqual(
                {"accepted": 1, "rejected": 0, "unresolved": 1}, result["accounting"]
            )
            repo = Path(__file__).resolve().parents[2]
            prepare_reviewed_inputs(
                root / "applied/reviewed-input.json",
                repo / "sse_multivector/fine-segmentation-suite-encoder-v1.json",
                repo / "sse_multivector/subject-prompt-goal-v1/asv6.23/frozen.json",
                repo / "sse_multivector/mask-prompt-goal-v1/frozen.json",
                root / "sse-prepared",
            )
            self.assertEqual(
                1, read(root / "sse-prepared/manifest.json")["vector_count"]
            )

    def test_accepted_ambiguous_mask_requires_explicit_ranges_and_rejects_bad_boundaries(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(self.source(root), root / "prepared")
            for index, spans in enumerate(
                (None, [[0, 1], [11, 15]], [[11, 15], [0, 3]], [[0, 3], [5, 9]])
            ):
                decision = {"judgment": "accepted", "reason": "Explicit review."}
                if spans is not None:
                    decision["byte_spans"] = spans
                path = root / f"decisions-{index}.json"
                write(
                    path,
                    {
                        "schema_version": 1,
                        "reviewer": "primary assistant",
                        "decisions": {"N001-S001-MP": decision},
                    },
                )
                with self.assertRaisesRegex(ValueError, "explicit|UTF-8|order|exact"):
                    apply_decisions(root / "prepared", path, root / f"bad-{index}")
                self.assertFalse((root / f"bad-{index}").exists())

    def test_explicit_correction_is_recorded_without_changing_raw_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(self.source(root), root / "prepared")
            decisions = root / "decisions.json"
            write(
                decisions,
                {
                    "schema_version": 1,
                    "reviewer": "primary assistant",
                    "decisions": {
                        "N001-S001-MP": {
                            "judgment": "rejected",
                            "reason": "Explicit rejection.",
                        },
                        "N001-S002-MP": {
                            "judgment": "accepted",
                            "fragments": ["☕ "],
                            "reason": "Explicit mask correction.",
                        },
                    },
                },
            )
            apply_decisions(root / "prepared", decisions, root / "applied")
            result = read(root / "applied/reviewed-input.json")
            rejected, corrected = result["notes"][0]["subjects"]
            self.assertEqual("rejected", rejected["judgment"])
            self.assertNotIn("byte_spans", rejected)
            self.assertEqual(["☕ "], corrected["fragments"])
            self.assertEqual([[0, 4]], corrected["byte_spans"])
            self.assertEqual(
                '["☕"]', corrected["provenance"]["mask_review"]["raw_mask"]
            )
            self.assertEqual(
                [[[0, 3]]], corrected["provenance"]["mask_review"]["raw_placements"]
            )
            with self.assertRaisesRegex(ValueError, "already exists"):
                apply_decisions(root / "prepared", decisions, root / "applied")


if __name__ == "__main__":
    unittest.main()
