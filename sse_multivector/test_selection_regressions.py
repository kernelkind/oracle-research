"""Selection tests measure reachable relationships, not every direct edge."""
from argparse import Namespace
import json
from pathlib import Path
import tempfile
import unittest

from sse_multivector import selection_regressions as regression


class SelectionRegressions(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
