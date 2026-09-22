"""Tests for the node-note walk batch builder; no model execution."""
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
                          "comment": "fine."}]},
            {"id": "N2", "title": "Second", "text": "other note",
             "results": [{"model": "PPv10", "output": "{\"prominence\":2}",
                          "comment": "fine."}]},
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


class MaskLineTests(unittest.TestCase):
    def test_verified_fragment_display_with_scores(self):
        self.assertEqual(
            "V244  ⟦coffee⟧ — score 88\n"
            "V277  ⟦More⟧ ⟦coffee⟧ — score unscored",
            br._mask_lines([("V244", ["coffee"], 88),
                            ("V277", ["More", "coffee"], None)]))


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

    def test_the_walk_is_node_order_then_gap_sections(self):
        ids = [note["id"] for note in self.review["notes"]]
        self.assertEqual(19, len(ids))
        self.assertEqual(["S9c440e7f47-N029", "S9c440e7f47-N048",
                          "Sbb8511308a-N035", "Sbb8511308a-N036", "Sbb8511308a-N079",
                          "S68ce4fd21f-N092"], ids[:6])
        self.assertIn("unassigned-N100", ids)
        self.assertIn("outside-corpus-R07+R08", ids)

    def test_each_card_is_one_complete_note_verbatim(self):
        cases = self.context["cases"]
        self.assertEqual(cases["R03"]["text"], self.cards["S9c440e7f47-N029"]["text"])
        self.assertEqual(cases["M03"]["text"], self.cards["unassigned-N100"]["text"])
        for card in self.review["notes"]:
            with self.subTest(card=card["id"]):
                self.assertNotIn("⟦", card["text"])

    def test_title_states_node_title_position_note_and_score(self):
        self.assertEqual('S9c440e7f47 "Coffee" · position 1 of 2 · N029 · score 88',
                         self.cards["S9c440e7f47-N029"]["title"])
        self.assertEqual('Sbb8511308a "Coffee" · position 1 of 3 · N035 · score 95',
                         self.cards["Sbb8511308a-N035"]["title"])
        self.assertIn("(no saved title)", self.cards["S68ce4fd21f-N092"]["title"])

    def test_comment_is_short_and_carries_only_the_essentials(self):
        comment = self.cards["S9c440e7f47-N029"]["results"][0]["comment"]
        self.assertLess(len(comment), 700)
        self.assertIn("V244  ⟦coffee⟧ — score 88", comment)
        self.assertIn("predeclared R03 over R04: holds (88 vs 2)", comment)
        for crammed in ("LIMITS", "EXPECTATIONS", "PREDECLARED CHECKS", "PROVENANCE"):
            self.assertNotIn(crammed, comment)

    def test_multi_mask_and_unscored_flags(self):
        multi = self.cards["Sbb8511308a-N035"]["results"][0]["comment"]
        self.assertIn("2 masks in this node; how they combine is undecided", multi)
        unscored = self.cards["Sbb8511308a-N079"]["results"][0]["comment"]
        self.assertIn("position unknown", unscored)
        self.assertIn("score unscored", unscored)

    def test_gap_cards_state_that_there_is_nothing_to_order(self):
        unassigned = self.cards["unassigned-N100"]["results"][0]["comment"]
        self.assertIn("task 24", unassigned)
        self.assertIn("PRESERVED DISAGREEMENT (M03)", unassigned)
        baby = self.cards["outside-corpus-R07+R08"]
        self.assertIn("score 94, 3", baby["title"])
        self.assertIn("R07  ⟦baby⟧ ⟦baby⟧ — score 94", baby["results"][0]["comment"])

    def test_outputs_are_the_saved_verbatim_responses(self):
        cases = self.context["cases"]
        self.assertEqual(f"R03: {cases['R03']['raw']}",
                         self.cards["S9c440e7f47-N029"]["results"][0]["output"])
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
        self.assertIn("19 notes", run.stdout)


if __name__ == '__main__':
    unittest.main()
