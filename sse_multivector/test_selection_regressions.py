"""Selection tests measure reachable relationships, not every direct edge."""
from argparse import Namespace
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from sse_multivector import selection_regressions as regression


class SelectionRegressions(unittest.TestCase):
    def test_graph_method_is_exposed_by_the_production_cli(self):
        result = subprocess.run([sys.executable, regression.__file__, 'evaluate', '--help'],
                                capture_output=True, text=True, check=True)
        self.assertIn('graph-search', result.stdout)

    def test_graph_selection_reuses_only_answers_it_reaches(self):
        frame = dict(rows=[dict(id='Parent', parents=[]), dict(id='Child', parents=['Parent'])],
            eligible=['Parent', 'Child'], step={},
            known={'Parent': dict(parsed=dict(relation='local_contains_canonical')),
                   'Child': dict(parsed=dict(relation='uncertain'))})
        result = regression.graph_selection(frame)
        self.assertTrue(result['complete'])
        self.assertEqual(result['queried'], ['Parent'])
        self.assertEqual(result['inferred'], {'Child': 'local_contains_canonical'})

    def test_graph_selection_records_missing_roots_as_pending(self):
        frame = dict(rows=[dict(id='Food', parents=[]), dict(id='Mental states', parents=[])],
            eligible=['Food', 'Mental states'], step={},
            known={'Food': dict(parsed=dict(relation='neither'))})
        result = regression.graph_selection(frame)
        self.assertFalse(result['complete'])
        self.assertEqual(result['queried'], ['Food'])
        self.assertEqual(result['pending'], ['Mental states'])

    def test_pending_graph_comparison_cannot_be_applied_or_priced_as_complete(self):
        from sse_multivector import candidate_ranking_study as study
        frame = dict(rows=[dict(id='Food', parents=[]), dict(id='Mental states', parents=[])],
            eligible=['Food', 'Mental states'], ids=['Food', 'Mental states'],
            local_subject='Hope that breakfast will energize the author',
            step=dict(index=108, local=dict(note_id='note', number='6.1'),
                      selected_meaning='Hope of feeling energized.', status='held'),
            known={'Food': dict(parsed=dict(relation='neither'))})
        row = regression.evaluate_case(frame, ['Food'], study, (None, None, None),
                                       pending=['Mental states'])
        self.assertEqual(row['outcome'], 'unresolved')
        self.assertEqual(row['local_subject'], frame['local_subject'])
        self.assertEqual(row['unresolved'], ['Mental states'])
        self.assertFalse(row['same_graph'])
        self.assertEqual(row['observed_relationships'], {})

    def test_meals_preserves_food_without_a_direct_food_comparison(self):
        original = [dict(id='Food', parents=[]), dict(id='Meals', parents=['Food']),
                    dict(id='Breakfast', parents=['Food', 'Meals'])]
        reduced = [dict(id='Food', parents=[]), dict(id='Meals', parents=['Food']),
                   dict(id='Breakfast', parents=['Meals'])]
        expected = dict(status='added', relationships=regression.relationships(
            original, 'Breakfast', ['Food', 'Meals']))
        observed = regression.relationships(reduced, 'Breakfast', ['Food', 'Meals'])
        self.assertEqual(regression.assess(expected, None, [], observed)['outcome'], 'matched')

    def test_chicken_processing_as_a_root_misses_food(self):
        expected = dict(status='added', relationships={'Food': 'canonical_contains_local'})
        result = regression.assess(expected, None, [], {})
        self.assertEqual(result['outcome'], 'missed_relationship')
        self.assertEqual(result['missing'], {'Food': 'canonical_contains_local'})

    def test_preserves_new_parent_relationships_and_equivalence(self):
        nodes = [dict(id='Food', parents=[]), dict(id='Meals', parents=['Food']),
                 dict(id='Dinner', parents=['Meals'])]
        self.assertEqual(regression.relationships(nodes, 'Meals', ['Food', 'Meals', 'Dinner']),
            {'Food': 'canonical_contains_local', 'Meals': 'equivalent',
             'Dinner': 'local_contains_canonical'})

    def test_historical_contradiction_cannot_silently_be_admitted(self):
        expected = dict(status='held', relationships={})
        self.assertEqual(regression.assess(expected, None, [], {})['outcome'], 'missed_hold')
        self.assertEqual(regression.assess(expected, 'contradiction', [], {})['outcome'], 'matched')

    def test_holding_everything_cannot_pass(self):
        expected = dict(status='added', relationships={'Food': 'canonical_contains_local'})
        self.assertEqual(regression.assess(expected, 'uncertain', [], {})['outcome'], 'unexpected_hold')

    def test_unknown_comparison_remains_unresolved(self):
        expected = dict(status='held', relationships={})
        self.assertEqual(regression.assess(expected, None, ['unknown'], {})['outcome'], 'unresolved')

    def test_different_direct_edges_are_not_a_failure(self):
        expected = dict(status='added', relationships={'Food': 'canonical_contains_local'})
        observed = {'Food': 'canonical_contains_local', 'Meals': 'canonical_contains_local'}
        self.assertEqual(regression.assess(expected, None, [], observed)['outcome'], 'matched')

    def test_cycles_and_missing_parents_are_rejected(self):
        with self.assertRaises(ValueError):
            regression.relationships([dict(id='a', parents=['b']), dict(id='b', parents=['a'])], 'a', ['a'])
        with self.assertRaises(ValueError):
            regression.relationships([dict(id='a', parents=['missing'])], 'a', ['a'])

    def test_changed_sources_refuse_evaluation_before_reading_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, suite = root / 'state.json', root / 'suite.json'
            source.write_text('{}')
            suite.write_text(json.dumps(dict(schema_version=1,
                protected_sha256={str(source): regression.digest(source)})))
            source.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                regression.evaluate(Namespace(suite=suite))

    def test_missing_cases_or_different_graph_cannot_be_scored_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'selection.json'
            path.write_text(json.dumps(dict(state_sha256='same', steps=[dict(index=1, queried=['Food'])])))
            self.assertEqual(regression.selections_from_report(path, None, 'same', [1]), {1: ['Food']})
            with self.assertRaisesRegex(ValueError, 'every frozen case'):
                regression.selections_from_report(path, None, 'same', [1, 2])
            with self.assertRaisesRegex(ValueError, 'different frozen hierarchy'):
                regression.selections_from_report(path, None, 'changed', [1])

    def test_existing_saved_screen_is_accepted_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'screen.json'
            path.write_text(json.dumps(dict(provenance=dict(state_sha256='same'),
                profiles={'meaning-12': dict(steps=[dict(index=1, queried=['Meals'])])})))
            original = path.read_bytes()
            self.assertEqual(regression.selections_from_report(path, 'meaning-12', 'same', [1]), {1: ['Meals']})
            self.assertEqual(path.read_bytes(), original)

    def test_frozen_datasets_and_reports_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'suite.json'
            regression.write_once(path, {'saved': True})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                regression.write_once(path, {'saved': False})
            self.assertEqual(path.read_bytes(), original)

    def test_ineligible_and_duplicate_selections_are_rejected(self):
        frame = dict(eligible=['Food'], step={})
        for selected in (['Food', 'Food'], ['unknown']):
            with self.assertRaisesRegex(ValueError, 'unique eligible'):
                regression.checked_selection(frame, selected, None)

    def test_empty_selection_cannot_drop_a_required_mapped_parent(self):
        frame = dict(eligible=['Food'], step=dict(mapped_parent='Food'))
        with self.assertRaisesRegex(ValueError, 'mapped parent'):
            regression.checked_selection(frame, [], None)

    def test_native_usage_reference_keeps_archived_work_and_unknown_failures(self):
        audit = dict(summary_version='experiment-usage-summary-v2', generation_usage=dict(
            known_catalog_cost_estimate_usd=7.3, attempts_without_usage=14))
        result = regression.cost_reference(audit, 'state', dict(known_catalog_cost_estimate_usd=4.0))
        self.assertAlmostEqual(result['overhead_usd'], 3.3)
        self.assertEqual(result['attempts_without_usage'], 14)

    def test_original_cost_reference_remains_supported(self):
        audit = dict(state_sha256='state', cost_by_kind=dict(
            comparison=dict(known_catalog_cost_estimate_usd=4.0, attempts_without_usage=3),
            verification=dict(known_catalog_cost_estimate_usd=.5, attempts_without_usage=0),
            meaning=dict(known_catalog_cost_estimate_usd=1.0, attempts_without_usage=4)))
        result = regression.cost_reference(audit, 'state', dict(known_catalog_cost_estimate_usd=4.5))
        self.assertEqual(result['overhead_usd'], 1.0)
        self.assertEqual(result['attempts_without_usage'], 7)

    def test_review_hold_requires_its_original_comparison_evidence(self):
        row = dict(reason=None, unresolved=['Stockpots'], queried=['Food', 'Coffee'],
                   verification={'Stockpots': 'local_contains_canonical'}, same_graph=False)
        review = dict(reason='Incompatible food/drink interpretations', comparison_ids=['Food', 'Coffee'])
        regression.apply_review_hold(row, review)
        self.assertTrue(row['same_graph'])
        self.assertTrue(row['source_review_hold'])
        self.assertEqual(row['unresolved'], [])
        self.assertEqual(row['verification'], {})
        self.assertEqual(row['retained_cases'], 2)
        row = dict(reason=None, unresolved=[], queried=['Food'], verification={}, same_graph=False)
        regression.apply_review_hold(row, review)
        self.assertEqual(row['unresolved'], ['Coffee'])
        self.assertFalse(row['same_graph'])


if __name__ == '__main__':
    unittest.main()
