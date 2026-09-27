import copy
import json
import math
import unittest

from sse_multivector import experiment_inputs


class ProminenceRankingTests(unittest.TestCase):
    def test_hierarchy_prominence_uses_only_direct_members_and_original_ids(self):
        mask = dict(instance='merged-mask', note_id='N', text='Tea, then tea.',
                    byte_spans=[[0, 3]], fragments=['Tea'], origins=[
                        dict(source_instance=dict(instance=identifier, note_id='N', byte_spans=[[0, 3]]))
                        for identifier in ['V1', 'V2']])
        source = {'memberships': {'nodes': [
            dict(group='G', title='Tea', matched_instances=[mask], recursive_note_ids=['N', 'child']),
            dict(group='child', title='Child', matched_instances=[])]}}
        cases = experiment_inputs.prepare({'adapter': 'prominence', 'select': ['G']},
                                          source, '{INPUT_JSON}')
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]['id'], 'G-V1')
        self.assertEqual(cases[0]['evidence']['mask_ids'], ['V1', 'V2'])
        self.assertEqual(json.loads(cases[0]['inputs']['INPUT_JSON']),
                         dict(mask=['Tea'], marked_post='⟦Tea⟧, then tea.'))
        with self.assertRaisesRegex(ValueError, 'unknown'):
            experiment_inputs.prepare_prominence(source, ['missing'])
        mask['origins'][0]['source_instance']['byte_spans'] = [[10, 13]]
        with self.assertRaisesRegex(ValueError, 'origin'):
            experiment_inputs.prepare_prominence(source, ['G'])

    def test_prominence_prepares_original_members_from_selected_title_report(self):
        packet = {"packet": "G", "instances": [
            dict(instance="V1", vector_id="v1", note_id="N", text="Tea tea",
                 byte_spans=[[0, 3]], fragments=["Tea"]),
            dict(instance="V2", vector_id="v2", note_id="N", text="Tea tea",
                 byte_spans=[[0, 3]], fragments=["Tea"]),
        ]}
        source = {"adapter": "titles", "cases": [
            dict(id="G", status="valid", parsed={"title": "Tea"}, evidence={"packet": packet}),
            dict(id="unselected", status="failed", evidence={}),
        ]}
        cases = experiment_inputs.prepare(
            {"adapter": "prominence", "select": ["G"]}, source, "{INPUT_JSON}")
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["evidence"]["mask_ids"], ["V1", "V2"])
        self.assertEqual(cases[0]["evidence"]["node_title"], "Tea")
        self.assertNotIn("node_title", cases[0]["inputs"]["INPUT_JSON"])
        for selection in [["missing"], ["unselected"]]:
            with self.assertRaises(ValueError):
                experiment_inputs.prepare({"adapter": "prominence", "select": selection},
                                          source, "{INPUT_JSON}")

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
                              output=json.dumps({"prominence": prominence}) if prominence is not None else None,
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

    def test_inverse_comparison_adds_orderings_without_changing_masks(self):
        from sse_multivector.prominence_ranking import add_rankings
        batch, report, scores = self.fixture()
        for rows in scores['groups'].values():
            for row in rows:
                row.update(inverse_cosine=.8, full_post_cosine=.9)
        result = add_rankings(batch, report, scores)
        self.assertEqual([o['name'] for o in result['orderings']],
                         ['Prominence', 'Linear cosine', 'Inverse combined', 'Full-post cosine'])
        self.assertEqual([n['text'] for n in result['notes']], [n['text'] for n in batch['notes']])
        self.assertIn('Inverse combined: 96.00', result['notes'][1]['results'][0]['output'])
        self.assertIn('Full-post cosine: 95.00', result['notes'][1]['results'][0]['output'])
        self.assertIn('Inverse cosine: 0.8000', result['notes'][1]['results'][0]['output'])
        del scores['groups']['Coffee'][0]['inverse_cosine']
        with self.assertRaisesRegex(ValueError, 'inverse'):
            add_rankings(batch, report, scores)


if __name__ == "__main__":
    unittest.main()
