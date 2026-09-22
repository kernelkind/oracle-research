"""Tests for the node-note order review batch builder; no model execution."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import build_review as br

HAVE_DATA = all(
    (br.GOAL / name / file).exists()
    for name in ("ppv10-ranking-v1", "ppv10-mixed-notes-v1")
    for file in ("plan.json", "inputs.json", "results.json")
) and (br.CORPUS / "vectors" / "vector-map.json").exists() \
    and (br.CORPUS / "hdbscan-cross-note" / "review" / "review.json").exists()
REVIEW_BINARY = br.ROOT.parents[2] / "target" / "release" / "model-output-review"


def minimal_review():
    return {
        "schema_version": 1,
        "title": "Example review",
        "notes": [
            {"id": "N1", "title": "First", "text": "complete note",
             "model_input": '{"mask": ["note"]}',
             "results": [{"model": "PPv10", "output": "{\"prominence\":1}",
                          "comment": "My assessment: fine."}]},
            {"id": "N2", "title": "Second", "text": "other note",
             "results": [{"model": "PPv10", "output": "{\"prominence\":2}",
                          "comment": "My assessment: fine."}]},
        ],
    }


class BandTests(unittest.TestCase):
    def test_ppv10_anchor_bands(self):
        for score, expected in ((100, "central"), (90, "central"), (89, "major"),
                                (70, "major"), (69, "secondary"), (40, "secondary"),
                                (39, "incidental"), (10, "incidental"), (9, "absent"),
                                (0, "absent")):
            with self.subTest(score=score):
                self.assertEqual(expected, br.band(score))

    def test_out_of_range_scores_are_rejected(self):
        for score in (-1, 101, 2.5):
            with self.subTest(score=score), self.assertRaises(ValueError):
                br.band(score)


class VerdictTests(unittest.TestCase):
    def test_mechanical_order_tie_and_reversal(self):
        self.assertEqual(("ordered", 93), br.verdict(95, 2))
        self.assertEqual(("tie", 0), br.verdict(85, 85))
        self.assertEqual(("reversed", -20), br.verdict(58, 78))


class MarkSpansTests(unittest.TestCase):
    def test_marks_selections_and_merges_overlaps(self):
        self.assertEqual("More ⟦coffee⟧ in cool places",
                         br.mark_spans("More coffee in cool places", [[5, 11]]))
        self.assertEqual("⟦More coffee⟧ in cool places",
                         br.mark_spans("More coffee in cool places", [[0, 11], [5, 11]]))

    def test_byte_spans_are_utf8_offsets(self):
        text = "☕ coffee"
        self.assertEqual("☕ ⟦coffee⟧", br.mark_spans(text, [[4, 10]]))
        with self.assertRaises(ValueError):
            br.mark_spans(text, [[1, 3]])

    def test_rejects_empty_or_out_of_range(self):
        for spans in ([], [[0, 100]], [[3, 3]]):
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                br.mark_spans("coffee", spans)

    def test_mask_lines_follow_the_verified_fragment_display(self):
        self.assertEqual("V244  ⟦coffee⟧\n\nV277  ⟦More⟧ ⟦coffee⟧",
                         br._mask_lines([("V244", ["coffee"]),
                                         ("V277", ["More", "coffee"])]))


class CoverageTests(unittest.TestCase):
    def test_every_case_appears_in_exactly_one_placement(self):
        placements = {"S1": ["R01", "R02"], "unassigned": ["R03"]}
        br.check_coverage(placements, ["R01", "R02", "R03"])
        with self.assertRaises(ValueError):
            br.check_coverage({"S1": ["R01", "R02"]}, ["R01", "R02", "R03"])
        with self.assertRaises(ValueError):
            br.check_coverage({"S1": ["R01"], "u": ["R01"]}, ["R01"])


class SchemaCheckTests(unittest.TestCase):
    def test_accepts_a_valid_review(self):
        br.check_review(minimal_review())

    def test_rejects_broken_reviews(self):
        breakers = [
            lambda r: r.update(schema_version=2),
            lambda r: r.update(title="  "),
            lambda r: r.update(notes=[]),
            lambda r: r["notes"][1].update(id="N1"),
            lambda r: r["notes"][0].update(text=""),
            lambda r: r["notes"][0].update(model_input=""),
            lambda r: r["notes"][0]["results"][0].update(comment=" "),
            lambda r: r["notes"][1]["results"][0].update(model="Other"),
            lambda r: r["notes"][1].update(results=[]),
        ]
        for index, break_it in enumerate(breakers):
            review = minimal_review()
            break_it(review)
            with self.subTest(index=index), self.assertRaises(ValueError):
                br.check_review(review)


@unittest.skipUnless(HAVE_DATA, "saved study and hierarchy artifacts are local-only")
class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = br.build_context()
        cls.review = br.render_review(cls.context)
        cls.cards = {note["id"]: note for note in cls.review["notes"]}

    def test_scored_masks_map_to_real_hierarchy_nodes(self):
        placements = self.context["placement_of"]
        self.assertEqual("S9c440e7f47", placements["R03"])
        self.assertEqual("S9c440e7f47", placements["R04"])
        self.assertEqual("Sbb8511308a", placements["R01"])
        self.assertEqual("Sbb8511308a", placements["R02"])
        self.assertEqual("S68ce4fd21f", placements["M06"])
        self.assertEqual("unassigned", placements["M03"])
        self.assertEqual("outside-corpus", placements["R08"])

    def test_every_case_appears_in_exactly_one_placement(self):
        br.check_coverage(self.context["placements"], list(self.context["cases"]))
        placed = [case for cases in self.context["placements"].values() for case in cases]
        self.assertEqual(sorted(placed), sorted(self.context["cases"]))

    def test_cards_are_nodes_then_gap_sections(self):
        self.assertEqual(
            ["S9c440e7f47", "Sbb8511308a", "S68ce4fd21f", "unassigned", "outside-corpus"],
            [note["id"] for note in self.review["notes"]])
        self.assertIn("complete", self.cards["S9c440e7f47"]["title"])
        self.assertIn("partial", self.cards["Sbb8511308a"]["title"])
        self.assertIn("unscored", self.cards["S68ce4fd21f"]["title"])

    def test_node_card_shows_marked_masks_and_the_produced_order(self):
        card = self.cards["S9c440e7f47"]
        cases = self.context["cases"]
        self.assertIn("V244  ⟦coffee⟧", card["text"])
        self.assertIn("V381  ⟦Coffee⟧", card["text"])
        self.assertIn("1 · N029", card["text"])
        self.assertIn(cases["R03"]["text"], card["text"])
        self.assertIn(cases["R04"]["text"], card["text"])
        comment = card["results"][0]["comment"]
        self.assertIn("node-note order", comment.lower())
        self.assertIn("as expected: R03 over R04 (88 vs 2, gap 86)", comment)

    def test_outputs_are_the_saved_verbatim_responses(self):
        card = self.cards["S9c440e7f47"]
        output = card["results"][0]["output"]
        self.assertIn('{"prominence":88}', output)
        self.assertIn('{"prominence":2}', output)
        cases = self.context["cases"]
        self.assertEqual(cases["R03"]["raw"], '{"prominence":88}')

    def test_multiple_masks_per_note_are_flagged_as_undecided(self):
        comment = self.cards["Sbb8511308a"]["results"][0]["comment"]
        self.assertIn("V277", comment)
        self.assertIn("undecided", comment)
        self.assertIn("task 27", comment)
        sparse = self.cards["S68ce4fd21f"]["results"][0]["comment"]
        self.assertIn("position unknown", sparse)

    def test_gap_sections_carry_the_unplaced_cases(self):
        unassigned = self.cards["unassigned"]["results"][0]["comment"]
        self.assertIn("task 24", unassigned)
        self.assertIn("PRESERVED DISAGREEMENT", unassigned)
        self.assertIn("S68ce4fd21f", unassigned)  # cross-placement pair note
        self.assertIn(self.context["cases"]["M03"]["text"],
                      self.cards["unassigned"]["text"])  # complete note, verbatim
        outside = self.cards["outside-corpus"]["results"][0]["comment"]
        self.assertIn("not in the hierarchy corpus", outside)

    def test_review_labels_the_prompt_version_and_status(self):
        self.assertIn("PPv10", self.review["title"])
        self.assertIn("user-approved, tested experimentally, not production-frozen",
                      self.review["title"])
        br.check_review(self.review)

    @unittest.skipUnless(HAVE_DATA and REVIEW_BINARY.exists(),
                         "release model-output-review binary is not built")
    def test_production_review_tool_accepts_the_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            path.write_text(json.dumps(self.review, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
            run = subprocess.run([str(REVIEW_BINARY), str(path), "--check"],
                                 capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("5 notes", run.stdout)


if __name__ == '__main__':
    unittest.main()
