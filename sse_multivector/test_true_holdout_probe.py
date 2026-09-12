"""TRUE02 production-path tests; no model loading or inference."""
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import true_category_probe
import true_holdout_probe as probe


def fixture():
    domains = []
    for prefix, domain in zip('FSERP', ('food', 'software', 'energy', 'research', 'photography')):
        domains.append(dict(id=domain,
            categories={f'{prefix}{i}': f'{domain} category {i}' for i in range(1, 7)},
            contains=[[prefix+'1', prefix+'2'], [prefix+'2', prefix+'1'],
                      [prefix+'1', prefix+'3'], [prefix+'2', prefix+'3']],
            rationale='The first two are equivalent and contain the third; all others are separate.'))
    return dict(experiment='TRUE02', threshold=0.142, domains=domains)


class TRUEHoldoutProbeTests(unittest.TestCase):
    def test_all_ordered_pairs_exact_strings_and_input_direction(self):
        data = fixture()
        data['domains'][0]['categories']['F1'] = '  Exact | category\nname  '
        before = copy.deepcopy(data)
        rows = probe.prepare_inputs(data)
        self.assertEqual(data, before)
        self.assertEqual(len(rows), 150)
        self.assertEqual(len({row['id'] for row in rows}), 150)
        self.assertTrue(all(sum(row['domain'] == domain['id'] for row in rows) == 30
                            for domain in data['domains']))
        row = next(row for row in rows if row['id'] == 'F1-contains-F3')
        self.assertEqual(row['a'], '  Exact | category\nname  ')
        self.assertEqual(row['b'], 'food category 3')
        self.assertEqual(row['a_id'], 'F1')
        self.assertEqual(row['b_id'], 'F3')
        self.assertEqual(row['format'], 'topic')
        self.assertEqual(row['model_input'], true_category_probe.model_input(row, 'topic'))
        self.assertTrue(row['expected'])

    def test_kinds_follow_both_frozen_directions(self):
        rows = {row['id']: row for row in probe.prepare_inputs(fixture())}
        for key, kind, expected in (
                ('F1-contains-F2', 'equivalent', True),
                ('F2-contains-F1', 'equivalent', True),
                ('F1-contains-F3', 'strict-containment', True),
                ('F3-contains-F1', 'reversed-containment', False),
                ('F3-contains-F4', 'noncontaining', False)):
            self.assertEqual(rows[key]['kind'], kind)
            self.assertIs(rows[key]['expected'], expected)

    def test_fixed_experiment_dimensions_and_cutoff_required(self):
        for field, value in (('experiment', 'TRUE01'), ('threshold', 0.14),
                             ('domains', fixture()['domains'][:4])):
            changed = fixture()
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                probe.prepare_inputs(changed)
        changed = fixture()
        del changed['domains'][0]['categories']['F6']
        with self.assertRaises(ValueError):
            probe.prepare_inputs(changed)

    def test_duplicate_ids_and_empty_titles_rejected(self):
        mutations = [
            lambda d: d['domains'][1].update(id='food'),
            lambda d: d['domains'][1]['categories'].update(F1=d['domains'][1]['categories'].pop('S1')),
            lambda d: d['domains'][0]['categories'].update(F1=' \n '),
            lambda d: d['domains'][0].update(rationale=''),
        ]
        for mutate in mutations:
            changed = fixture()
            mutate(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                probe.prepare_inputs(changed)

    def test_invalid_positive_pairs_rejected(self):
        for pair in (['F1', 'F1'], ['F1', 'S1'], ['F1', 'unknown'],
                     ['F1', 'F2'], ['F1'], 'F1-F2', [[], 'F2']):
            changed = fixture()
            changed['domains'][0]['contains'].append(pair)
            with self.subTest(pair=pair), self.assertRaises(ValueError):
                probe.prepare_inputs(changed)

    def test_missing_transitive_and_equivalent_closure_rejected_not_added(self):
        changed = fixture()
        changed['domains'][0]['contains'].remove(['F2', 'F3'])
        before = copy.deepcopy(changed)
        with self.assertRaisesRegex(ValueError, 'closure'):
            probe.prepare_inputs(changed)
        self.assertEqual(changed, before)
        changed = fixture()
        changed['domains'][0]['contains'].append(['F3', 'F4'])
        with self.assertRaisesRegex(ValueError, 'closure'):
            probe.prepare_inputs(changed)

    def test_frozen_bytes_and_source_provenance_saved_before_any_model_loading(self):
        raw = ('  ' + json.dumps(fixture(), ensure_ascii=False) + '\n').encode()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source, output = root / 'fixture.json', root / 'run'
            source.write_bytes(raw)
            inputs = probe.freeze_inputs(source, digest, output)
            self.assertEqual((output / 'fixture.json').read_bytes(), raw)
            self.assertEqual(json.loads((output / 'inputs.json').read_text()), inputs)
            self.assertEqual((output / 'true_holdout_probe.py').read_bytes(),
                             Path(probe.__file__).read_bytes())
            self.assertEqual((output / 'true_category_probe.py').read_bytes(),
                             Path(true_category_probe.__file__).read_bytes())
            started = json.loads((output / 'started.json').read_text())
            self.assertEqual(started['fixture_sha256'], digest)
            self.assertEqual(started['threshold'], 0.142)
            self.assertEqual(started['scorer_sha256'], probe.sha256(Path(true_category_probe.__file__)))
            with self.assertRaises(FileExistsError):
                probe.freeze_inputs(source, digest, output)

    def test_bad_freeze_hash_and_duplicate_json_keys_never_create_output(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source, output = root / 'fixture.json', root / 'run'
            source.write_text(json.dumps(fixture()))
            with self.assertRaisesRegex(ValueError, 'fixture'):
                probe.freeze_inputs(source, '0' * 64, output)
            self.assertFalse(output.exists())
            source.write_text('{"experiment":"TRUE02","experiment":"TRUE02"}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                probe.freeze_inputs(source, probe.sha256(source), output)
            self.assertFalse(output.exists())

    def test_frozen_cutoff_is_strict_and_native_scorer_is_unchanged(self):
        self.assertFalse(probe.threshold_decision(0.142))
        self.assertTrue(probe.threshold_decision(math.nextafter(0.142, 1.0)))
        self.assertFalse(probe.threshold_decision(math.nextafter(0.142, 0.0)))
        self.assertIs(probe.score_generation, true_category_probe.score_generation)
        self.assertIs(probe.model_input, true_category_probe.model_input)
        for value in (math.nan, math.inf, -0.1, 1.1):
            with self.assertRaises(ValueError):
                probe.threshold_decision(value)

    def scored_rows(self):
        rows = []
        for a, b, expected, native, score in (
                ('F1', 'F2', True, True, 0.8), ('F2', 'F1', False, False, 0.9),
                ('F3', 'F4', True, None, 0.142), ('F4', 'F3', False, False, 0.1)):
            rows.append(dict(id=f'{a}-contains-{b}', a_id=a, b_id=b, a=a, b=b,
                domain='food', kind='strict-containment' if expected else 'reversed-containment',
                expected=expected, predicted=native, entailment_score=score,
                threshold_predicted=probe.threshold_decision(score), format='topic'))
        return rows

    def test_summary_separates_native_cutoff_and_whole_unordered_pairs(self):
        result = probe.summarize(self.scored_rows())
        native, cutoff = result['overall']['native'], result['overall']['cutoff']
        self.assertEqual(native['correct'], 3)
        self.assertEqual(native['unresolved'], 1)
        self.assertEqual(native['true_positive'], 1)
        self.assertEqual(native['true_negative'], 2)
        self.assertEqual(native['false_negative'], 0)
        self.assertEqual(cutoff['correct'], 2)
        self.assertEqual(cutoff['false_positive'], 1)
        self.assertEqual(cutoff['false_negative'], 1)
        self.assertEqual(result['unordered_pairs']['overall']['total'], 2)
        self.assertEqual(result['unordered_pairs']['overall']['native_correct'], 1)
        self.assertEqual(result['unordered_pairs']['overall']['cutoff_correct'], 0)
        self.assertEqual(result['domain']['food'], result['overall'])
        self.assertEqual(result['kind']['strict-containment']['native']['unresolved'], 1)

    def test_score_inversions_extrema_and_separation_without_fitting(self):
        result = probe.summarize(self.scored_rows())['score_ordering']
        overall = result['overall']
        self.assertEqual(overall['comparisons'], 4)
        self.assertEqual(overall['inversions'], 2)
        self.assertEqual(overall['ties'], 0)
        self.assertEqual(overall['minimum_positive']['score'], 0.142)
        self.assertEqual(overall['maximum_negative']['score'], 0.9)
        self.assertEqual(overall['minimum_positive']['ids'], ['F3-contains-F4'])
        self.assertAlmostEqual(overall['separation_gap'], 0.142 - 0.9)
        self.assertFalse(overall['strictly_separated'])
        self.assertEqual(result['domain']['food'], overall)

    def test_report_contains_every_verdict_and_lists_both_error_types(self):
        rows = self.scored_rows()
        rows[0]['a'] = 'Category | with\na newline'
        report = probe.render_decisions(rows)
        self.assertIn('A contains B', report)
        self.assertIn('Category \\| with a newline', report)
        self.assertIn('0.142000', report)
        self.assertIn('Unresolved', report)
        self.assertIn('Native errors', report)
        self.assertIn('Cutoff errors', report)
        self.assertIn('> 0.142', report)
        for row in rows:
            self.assertIn(row['id'], report)


if __name__ == '__main__':
    unittest.main()
