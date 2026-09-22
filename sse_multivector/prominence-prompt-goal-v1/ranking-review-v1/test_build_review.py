"""Tests for the read-only PPv10 ranking review builder; no model execution."""
import unittest
from pathlib import Path

import build_review as br

HAVE_DATA = all(
    (br.GOAL / name / file).exists()
    for name in ("ppv10-ranking-v1", "ppv10-mixed-notes-v1")
    for file in ("plan.json", "inputs.json", "results.json")
)


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


class MarkedHtmlTests(unittest.TestCase):
    def test_highlights_marks_and_escapes_text(self):
        self.assertEqual(
            "x&lt;y <mark>coffee</mark> ☕",
            br.marked_html("x<y ⟦coffee⟧ ☕"))

    def test_repeated_selections_each_get_a_highlight(self):
        self.assertEqual(
            "<mark>baby</mark> #<mark>baby</mark>",
            br.marked_html("⟦baby⟧ #⟦baby⟧"))

    def test_rejects_unbalanced_or_missing_markers(self):
        for marked in ("plain", "⟦a", "a⟧", ""):
            with self.subTest(marked=marked), self.assertRaises(ValueError):
                br.marked_html(marked)


class CoverageTests(unittest.TestCase):
    def test_every_case_appears_exactly_once(self):
        groups = [{"id": "G1", "cases": ["R01", "R02"]}, {"id": "G2", "cases": ["R03"]}]
        br.check_coverage(groups, ["R01", "R02", "R03"])
        with self.assertRaises(ValueError):
            br.check_coverage(groups, ["R01", "R02", "R03", "R04"])
        with self.assertRaises(ValueError):
            br.check_coverage([{"id": "G1", "cases": ["R01", "R01"]}], ["R01"])

    def test_comparison_cases_must_share_a_group(self):
        groups = [{"id": "G1", "cases": ["R01", "R02"]}, {"id": "G2", "cases": ["R03"]}]
        br.check_comparisons([{"higher": "R01", "lower": "R02", "kind": "clear"}], groups)
        with self.assertRaises(ValueError):
            br.check_comparisons([{"higher": "R01", "lower": "R03", "kind": "clear"}], groups)


@unittest.skipUnless(HAVE_DATA, "saved study artifacts are local-only")
class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = br.build_context()

    def test_cases_carry_saved_scores_and_inputs(self):
        cases = self.context["cases"]
        self.assertEqual(19, len(cases))
        self.assertEqual(95, cases["R01"]["score"])
        self.assertEqual(["coffee"], cases["R01"]["mask"])
        self.assertEqual(58, cases["M03"]["score"])
        self.assertEqual("central", br.band(cases["M09"]["score"]))

    def test_predeclared_comparisons_get_mechanical_verdicts(self):
        comparisons = [c for g in self.context["groups"] for c in g["comparisons"]]
        self.assertEqual(10, len(comparisons))
        by_pair = {(c["higher"], c["lower"]): c for c in comparisons}
        self.assertEqual("ordered", by_pair[("R01", "R04")]["result"])
        self.assertEqual(93, by_pair[("R01", "R04")]["gap"])
        self.assertEqual("ordered", by_pair[("R05", "R06")]["result"])
        self.assertEqual(1, by_pair[("R05", "R06")]["gap"])
        self.assertEqual("ordered", by_pair[("M11", "M10")]["result"])

    def test_clear_counts_are_mechanical_not_an_accuracy_rate(self):
        self.assertEqual({"ordered": 7, "tie": 0, "reversed": 0},
                         self.context["clear_counts"])

    def test_cross_note_groups_precede_within_note_groups(self):
        kinds = [g["kind"] for g in self.context["groups"]]
        self.assertEqual(sorted(kinds), kinds)
        self.assertIn("cross_note", kinds)
        self.assertIn("within_note", kinds)

    def test_html_escapes_posts_highlights_masks_and_keeps_caveats(self):
        html_text = br.render_html(self.context)
        self.assertIn("PPv10", html_text)
        self.assertIn("user-approved, tested experimentally, not production-frozen", html_text)
        self.assertIn("not an accuracy", html_text)
        self.assertIn("<mark>coffee</mark>", html_text)
        self.assertNotIn("⟦", html_text)
        self.assertNotIn("<script>alert", html_text)

    def test_separate_muse_probe_is_still_available(self):
        if not (br.GOAL / "ppv10-mpv3.43-muse13high-v1" / "results.json").exists():
            self.skipTest("muse probe artifacts are local-only")
        html_text = br.render_html(self.context)
        self.assertIn("Rise and grind", html_text)
        self.assertIn("muse-spark-1.3-contributor", html_text)


if __name__ == '__main__':
    unittest.main()
