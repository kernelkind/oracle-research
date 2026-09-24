import copy
import math
import unittest

from sse_multivector import experiment_inputs


class ProminenceRankingTests(unittest.TestCase):
    def fixture(self):
        cases = []
        rows = []
        for cid, node, prominence, cosine in [
            ("a", "Coffee", 100, .04), ("b", "Coffee", 60, 1),
            ("c", "Coffee", None, None), ("d", "Tea", 90, -.1),
        ]:
            evidence = dict(node_id=node, node_title=node, note_id="N1",
                            mask_ids=[cid], text="tea", byte_spans=[[0, 3]])
            cases.append(dict(id=cid, evidence=evidence,
                              status="valid" if prominence is not None else "unrun",
                              parsed={"prominence": prominence}, reviews=[], prompt="PPv10",
                              inputs={"INPUT_JSON": '{"marked_post":"⟦tea⟧"}'}))
            if prominence is not None:
                rows.append(dict(id=cid, node_id=node, title=node, note_id="N1",
                                 mask_ids=[cid], fragments=["tea"], prominence=prominence,
                                 cosine=cosine))
        report = {"cases": cases}
        batch = experiment_inputs.prominence_review_batch({"prompt": {"id": "PPv10"}}, report)
        return batch, report, {"groups": {"Coffee": rows[:2], "Tea": rows[2:]}}

    def test_orders_preserve_all_cases_groups_and_original_outputs(self):
        from sse_multivector.prominence_ranking import add_rankings
        batch, report, scores = self.fixture()
        before = copy.deepcopy((batch, report, scores))
        result = add_rankings(batch, report, scores)
        self.assertEqual((batch, report, scores), before)
        self.assertEqual([o["note_ids"] for o in result["orderings"]],
                         [["a", "b", "c", "d"], ["b", "a", "c", "d"]])
        self.assertEqual([n["text"] for n in result["notes"]], ["⟦tea⟧"] * 4)
        self.assertIn("Linear cosine: 52.00", result["notes"][0]["results"][0]["output"])
        self.assertIn("Linear cosine: 40.50", result["notes"][3]["results"][0]["output"])
        self.assertIn("unranked", result["notes"][2]["title"])
        self.assertNotIn("score 100", result["notes"][0]["title"])
        self.assertIn("tied", result["notes"][0]["results"][0]["comment"])

    def test_linear_normalization_uses_native_bounds_and_preserves_ties(self):
        from sse_multivector.prominence_ranking import add_rankings
        for cosine, expected in [(-1, 0), (0, 50), (1, 100),
                                 (-1.0000001, 0), (1.0000001, 100)]:
            batch, report, scores = self.fixture()
            scores["groups"]["Coffee"][0]["cosine"] = cosine
            result = add_rankings(batch, report, scores)
            self.assertIn(f"Linear cosine: {expected:.2f}",
                          result["notes"][0]["results"][0]["output"])
        batch, report, scores = self.fixture()
        scores["groups"]["Coffee"][0]["cosine"] = .2
        result = add_rankings(batch, report, scores)
        for card in result["notes"][:2]:
            self.assertIn("Linear cosine: 60.00 · rank 1/2", card["results"][0]["output"])

    def test_stale_missing_duplicate_and_invalid_cosines_are_refused(self):
        from sse_multivector.prominence_ranking import add_rankings
        for field, value in [("prominence", 99), ("title", "Other"),
                             ("mask_ids", ["other"]), ("fragments", ["coffee"]),
                             ("cosine", math.nan), ("cosine", 1.5), ("cosine", True)]:
            batch, report, scores = self.fixture()
            scores["groups"]["Coffee"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                add_rankings(batch, report, scores)
        for duplicate in [False, True]:
            batch, report, scores = self.fixture()
            if duplicate:
                scores["groups"]["Coffee"].append(scores["groups"]["Coffee"][0])
            else:
                scores["groups"]["Coffee"].pop(0)
            with self.assertRaises(ValueError):
                add_rankings(batch, report, scores)


if __name__ == "__main__":
    unittest.main()
