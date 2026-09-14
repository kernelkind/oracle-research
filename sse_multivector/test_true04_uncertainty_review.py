"""Every saved uncertain title relationship must reach the human review unchanged."""

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "navigation-research-v1" / "TRUE04"
REVIEW = RUN / "collection-review"


class TRUE04UncertaintyReviewTests(unittest.TestCase):
    def test_all_uncertainties_include_both_accepted_and_rejected_predictions(self):
        packet = json.loads((REVIEW / "uncertainty-review.json").read_text())
        comparison = json.loads((REVIEW / "comparison.json").read_text())
        expected = sorted(comparison["uncertain"],
                          key=lambda row: (row["set_aside"], row["a_index"], row["b_index"]))
        self.assertEqual(packet["schema_version"], 1)
        self.assertEqual(packet["experiment"], "TRUE04")
        self.assertEqual(packet["threshold"], 0.142)
        self.assertEqual(len(expected), 65)
        self.assertEqual(len(packet["items"]), len(expected))
        self.assertEqual([item["item_id"] for item in packet["items"]],
                         [f"U{i:03}" for i in range(1, 66)])
        self.assertEqual([(item["a"], item["b"]) for item in packet["items"]],
                         [(row["a"], row["b"]) for row in expected])
        self.assertFalse(any(row["set_aside"] for row in expected[:63]))
        self.assertTrue(all(row["set_aside"] for row in expected[63:]))
        originals = [json.loads(line) for line in (RUN / "scores.jsonl").read_text().splitlines()]
        source_ids = []
        for item, row in zip(packet["items"], expected):
            self.assertEqual(item["assessment"], "Ambiguous")
            self.assertGreater(len(item["reason"].strip()), 40)
            self.assertNotIn("outcome", item)
            source = [record for record in originals if (record["a"], record["b"]) == (item["a"], item["b"])]
            self.assertEqual(item["decisions"], [dict(
                id=r["id"], a_id=r["a_id"], b_id=r["b_id"], native=r["predicted"],
                score=r["entailment_score"], cutoff=r["threshold_predicted"], model_input=r["model_input"]
            ) for r in source])
            self.assertEqual([r["id"] for r in item["decisions"]], row["original_direction_ids"])
            source_ids.extend(r["id"] for r in item["decisions"])
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertEqual({r["cutoff"] for item in packet["items"] for r in item["decisions"]}, {False, True})
        self.assertEqual({r["native"] for item in packet["items"] for r in item["decisions"]}, {False, True})

    def test_launcher_uses_saved_review_mode_and_separate_session(self):
        path = ROOT / "run-true04-uncertainties.sh"
        contents = path.read_text()
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BASH_SOURCE[0]", contents)
        self.assertIn("target/release/true-review", contents)
        self.assertIn("collection-review/uncertainty-review.json", contents)
        self.assertIn("--session", contents)
        self.assertIn("target/true04-uncertainty-review/decisions.json", contents)
        self.assertIn('"$@"', contents)
        self.assertNotIn("true_all_titles_probe", contents)
        self.assertNotIn("rm ", contents)


if __name__ == "__main__":
    unittest.main()
