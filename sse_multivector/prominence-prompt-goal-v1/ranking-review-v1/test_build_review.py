"""Tests for the model-output-review batch builder; no model execution."""
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
)
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


@unittest.skipUnless(HAVE_DATA, "saved study artifacts are local-only")
class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = br.build_context()
        cls.review = br.render_review(cls.context)

    def test_cases_carry_saved_scores_and_inputs(self):
        cases = self.context["cases"]
        self.assertEqual(19, len(cases))
        self.assertEqual(95, cases["R01"]["score"])
        self.assertEqual(["coffee"], cases["R01"]["mask"])
        self.assertEqual(58, cases["M03"]["score"])

    def test_predeclared_comparisons_get_mechanical_verdicts(self):
        comparisons = [c for g in self.context["groups"] for c in g["comparisons"]]
        self.assertEqual(10, len(comparisons))
        by_pair = {(c["higher"], c["lower"]): c for c in comparisons}
        self.assertEqual(("ordered", 93),
                         (by_pair[("R01", "R04")]["result"], by_pair[("R01", "R04")]["gap"]))
        self.assertEqual(1, by_pair[("R05", "R06")]["gap"])
        self.assertTrue(by_pair[("M08", "M07")]["informational"])

    def test_clear_counts_are_mechanical_not_an_accuracy_rate(self):
        self.assertEqual({"ordered": 7, "tie": 0, "reversed": 0},
                         self.context["clear_counts"])

    def test_review_is_score_sorted_within_groups(self):
        ids = [note["id"] for note in self.review["notes"]]
        self.assertEqual(
            ["R01", "R02", "R03", "R04", "R05", "R06", "M08", "M07", "R07", "R08",
             "M01", "M02", "M03", "M04", "M05", "M06", "M11", "M10", "M09"], ids)
        self.assertIn("rank 1/4", self.review["notes"][0]["title"])
        self.assertIn("score 95", self.review["notes"][0]["title"])
        self.assertIn("central 90–100", self.review["notes"][0]["title"])
        self.assertIn("Coffee: more coffee in cool places", self.review["notes"][0]["title"])

    def test_review_preserves_saved_outputs_and_exact_inputs(self):
        cases = self.context["cases"]
        for note in self.review["notes"]:
            case = cases[note["id"]]
            with self.subTest(case=case["id"]):
                self.assertEqual(case["raw"], note["results"][0]["output"])
                self.assertEqual(
                    json.dumps(case["input"], ensure_ascii=False, indent=2),
                    note["model_input"])
                self.assertEqual(case["text"], note["text"])

    def test_comments_separate_assessment_expectation_and_limits(self):
        comment = self.review["notes"][0]["results"][0]["comment"]
        self.assertIn("My assessment:", comment)
        self.assertIn("Predeclared expectation", comment)
        self.assertIn("not an accuracy rate", comment)
        self.assertIn("clear_cross_note: ordered, gap 93", comment)
        vacuum = next(n for n in self.review["notes"] if n["id"] == "M03")
        self.assertIn("Preserved disagreement:", vacuum["results"][0]["comment"])

    def test_each_card_identifies_its_own_selection(self):
        r08 = next(n for n in self.review["notes"] if n["id"] == "R08")
        self.assertIn("Baby update: nostr selections inside two hashtags", r08["title"])
        self.assertTrue(r08["results"][0]["comment"]
                        .startswith("Selection on this card: “nostr”, “nostr”. "
                                    "Case R08 — Baby update: nostr selections"))

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
        self.assertIn("19 notes", run.stdout)


if __name__ == '__main__':
    unittest.main()
