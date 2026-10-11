"""Native report enrichment and producer-bound fixed-meaning consistency."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

from sse_multivector import test_experiment as fixtures


PROJECT = Path(__file__).resolve().parents[1]
LAUNCHER = PROJECT.parent / 'experiment-runner/bin/experiment-runner'
REVERSED = {'equivalent': 'equivalent', 'neither': 'neither',
            'uncertain': 'uncertain',
            'local_contains_canonical': 'canonical_contains_local',
            'canonical_contains_local': 'local_contains_canonical'}


class HierarchyNodePairNativeConsistencyTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    calls = fixtures.ExperimentTests.calls

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run([str(LAUNCHER), '--project-root', str(PROJECT),
                                 *map(str, args)], cwd=self.root, text=True,
            capture_output=True, timeout=30,
            env={**os.environ, 'FAKE_RUNNER_LOG': str(self.log), **(env or {})})
        self.assertEqual(result.returncode == 0, ok, result.stderr + result.stdout)
        return result

    def prepare_original(self):
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}\n')
        self.write('notes.json', {'schema_version': 1, 'notes': [
            {'note_id': name, 'text': 'Post ' + name, 'subjects': [
                {'number': '1', 'subject': name, 'context': 'Original ' + name}]}
            for name in ('Alpha', 'Beta')]})
        self.write('original-source.json', {'schema_version': 2,
            'corpus': 'notes.json', 'canonical_states': {'isolated': [{
                'id': 'C1', 'subject': 'Beta', 'meaning': 'Fixed Beta',
                'entries': [{'note_id': 'Beta', 'number': '1'}], 'parents': []}]},
            'pairs': [{'id': 'pair-forward', 'local': {'note_id': 'Alpha', 'number': '1'},
                'local_meaning': 'Fixed Alpha',
                'canonical': {'state': 'isolated', 'id': 'C1'},
                'review': {'reversal_pair': 'pair', 'comparison_role': 'isolated-forward'}}]})
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = {'adapter': 'hierarchy_node_pairs', 'path': 'original-source.json'}
        self.write('original-spec.json', spec)
        self.cli('prepare', 'original', '--spec', 'original-spec.json')
        return json.loads(self.cli('show', 'original', '--json').stdout)

    def test_shared_show_exposes_consistency_and_missing_producers_honestly(self):
        report = self.prepare_original()
        self.assertIn('node_pair_consistency', report)
        summary = report['node_pair_consistency']
        self.assertFalse(summary['complete'])
        self.assertEqual(summary['eligible_cases'], 0)
        self.assertEqual(summary['skipped_cases'], [{
            'case_id': 'pair-forward', 'reason': 'missing_fixed_meaning_producer_receipt'}])
        self.assertEqual(self.calls(), [])

    def test_native_fixed_meaning_projection_keeps_source_evidence_outside_input(self):
        original = self.prepare_original()
        envelope = self.root / 'original/experiment.json'
        self.write('projected-source.json', {'prepared_experiment': {
            'path': 'original', 'sha256': hashlib.sha256(envelope.read_bytes()).hexdigest()},
            'input_view': 'fixed_meanings'})
        spec = json.loads((self.root / 'original-spec.json').read_text())
        spec['dataset']['path'] = 'projected-source.json'
        self.write('projected-spec.json', spec)
        self.cli('prepare', 'projected', '--spec', 'projected-spec.json')
        report = json.loads(self.cli('show', 'projected', '--json').stdout)
        case = report['cases'][0]
        self.assertEqual(json.loads(case['inputs']['INPUT_JSON']), {
            'local': {'subject': 'Alpha', 'meaning': 'Fixed Alpha'},
            'canonical': {'id': 'C1', 'subject': 'Beta', 'meaning': 'Fixed Beta',
                          'parents': [], 'ancestors': [], 'descendants': []}})
        self.assertEqual(case['evidence']['unprojected_input'],
                         json.loads(original['cases'][0]['inputs']['INPUT_JSON']))
        self.assertNotIn('Original Alpha', case['prompt'])
        self.assertNotIn('Post Alpha', case['prompt'])
        self.assertEqual(report['node_pair_consistency']['eligible_cases'], 0)
        self.assertEqual(report['node_pair_consistency']['skipped_cases'][0]['reason'],
                         'missing_fixed_meaning_producer_receipt')
        self.assertEqual(self.calls(), [])

    def test_native_symmetric_show_keeps_pair_inputs_without_branch_guards(self):
        self.prepare_original()
        envelope = self.root / 'original/experiment.json'
        self.write('symmetric-source.json', {'prepared_experiment': {
            'path': 'original', 'sha256': hashlib.sha256(envelope.read_bytes()).hexdigest()},
            'input_view': 'symmetric_fixed_meanings'})
        spec = json.loads((self.root / 'original-spec.json').read_text())
        spec['dataset']['path'] = 'symmetric-source.json'
        self.write('symmetric-spec.json', spec)
        self.cli('prepare', 'symmetric', '--spec', 'symmetric-spec.json')
        report = json.loads(self.cli('show', 'symmetric', '--json').stdout)
        self.assertEqual(json.loads(report['cases'][0]['inputs']['INPUT_JSON']), {
            'A': {'subject': 'Alpha', 'meaning': 'Fixed Alpha'},
            'B': {'subject': 'Beta', 'meaning': 'Fixed Beta'}})
        self.assertEqual(report['node_pair_consistency']['skipped_cases'], [{
            'case_id': 'pair-forward', 'reason': 'missing_fixed_meaning_producer_receipt'}])
        symmetric_envelope = self.root / 'symmetric/experiment.json'
        self.write('ordered-source.json', {'prepared_experiment': {
            'path': 'symmetric',
            'sha256': hashlib.sha256(symmetric_envelope.read_bytes()).hexdigest()},
            'input_view': 'symmetric_fixed_meanings', 'input_order': ['B', 'A']})
        spec['dataset']['path'] = 'ordered-source.json'
        self.write('ordered-spec.json', spec)
        self.cli('prepare', 'ordered', '--spec', 'ordered-spec.json')
        ordered = json.loads(self.cli('show', 'ordered', '--json').stdout)
        payload = json.loads(ordered['cases'][0]['inputs']['INPUT_JSON'])
        self.assertEqual(list(payload), ['B', 'A'])
        self.assertEqual(payload, json.loads(report['cases'][0]['inputs']['INPUT_JSON']))
        self.assertNotEqual(ordered['cases'][0]['input_sha256'],
                            report['cases'][0]['input_sha256'])
        self.assertEqual(ordered['cases'][0]['evidence']['source_input'],
                         report['cases'][0]['evidence']['source_input'])
        self.assertEqual(ordered['node_pair_consistency'], report['node_pair_consistency'])
        self.assertEqual(self.calls(), [])


class HierarchyNodePairConsistencyTests(unittest.TestCase):
    """Upstream-validated report fixtures exercise the real production scorer."""

    def cases(self, pairs, *, same_input=False):
        rows = []
        producers = {}

        def producer(name):
            if name not in producers:
                producers[name] = {'experiment': '/fixture/producer', 'case': name,
                    'receipt': {'results_path': '/fixture/producer/run/results.jsonl',
                                'record_sha256': hashlib.sha256(name.encode()).hexdigest()}}
            return producers[name]

        for pair_id, left, right, relation, *other in pairs:
            reverse = other[0] if other else REVERSED.get(relation, relation)
            for direction, local, canonical, label in (
                    ('forward', left, right, relation),
                    ('reverse', right, left, reverse)):
                local_text = 'Same' if same_input else local
                other_text = 'Same' if same_input else canonical
                payload = {'local': {'subject': local_text, 'meaning': 'Fixed ' + local_text},
                    'canonical': {'id': 'C1', 'subject': other_text,
                        'meaning': 'Fixed ' + other_text, 'parents': [],
                        'ancestors': [], 'descendants': []}}
                original = json.loads(json.dumps(payload))
                original['local']['entry'] = {'subject': local_text, 'context': 'Original context'}
                original['local']['post'] = 'Original post'
                original['canonical']['entries'] = [{'subject': other_text, 'context': 'Original'}]
                inputs = {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)}
                identifier = pair_id + '-' + direction
                status = label if label in ('unrun', 'failed') else 'valid'
                rows.append({'id': identifier, 'inputs': inputs,
                    'input_sha256': hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest(),
                    'status': status,
                    'receipt': None if status == 'unrun' else {
                        'results_path': '/fixture/comparisons/run/results.jsonl',
                        'record_sha256': hashlib.sha256(identifier.encode()).hexdigest()},
                    'parsed': {'meaning': payload['local']['meaning'], 'relation': label,
                               'reason': 'Fixture relation'} if status == 'valid' else None,
                    'evidence': {'input_view': 'fixed_meanings', 'unprojected_input': original,
                        'local_meaning_from': producer(local),
                        'canonical_meaning_from': {'C1': producer(canonical)},
                        'review': {'reversal_pair': pair_id,
                                   'comparison_role': 'isolated-' + direction}}})
        return rows

    def summarize(self, rows):
        from sse_multivector.hierarchy_node_pair_consistency import summarize
        return summarize(rows)

    def test_projected_reversal_and_transitivity_use_actual_meanings_and_receipts(self):
        rows = self.cases([('ab', 'A', 'B', 'local_contains_canonical'),
            ('bc', 'B', 'C', 'local_contains_canonical'), ('ac', 'A', 'C', 'neither')])
        result = self.summarize(rows)
        self.assertEqual(result['eligible_cases'], 6)
        self.assertEqual(result['reversals']['complete_pairs'], 3)
        self.assertEqual(result['reversals']['conflicts'], [])
        for direction in ('forward', 'reverse'):
            conflict = result['directions'][direction]['conflicts'][0]
            self.assertEqual(conflict['kind'], 'transitivity_conflict')
            self.assertEqual({r['case_id'] for r in conflict['witness']},
                             {p + '-' + direction for p in ('ab', 'bc', 'ac')})
            self.assertTrue(all(r['receipt']['record_sha256'] for r in conflict['witness']))

    def test_reversal_conflict_keeps_both_receipts(self):
        result = self.summarize(self.cases([
            ('ab', 'A', 'B', 'local_contains_canonical', 'neither')]))
        conflict = result['reversals']['conflicts'][0]
        self.assertEqual(conflict['pair_id'], 'ab')
        for direction in ('forward', 'reverse'):
            self.assertEqual(conflict[direction]['case_id'], 'ab-' + direction)
            self.assertTrue(conflict[direction]['receipt']['record_sha256'])

    def test_missing_direct_comparison_does_not_create_a_negative(self):
        result = self.summarize(self.cases([
            ('ab', 'A', 'B', 'local_contains_canonical'),
            ('bc', 'B', 'C', 'local_contains_canonical')]))
        for direction in ('forward', 'reverse'):
            self.assertEqual(result['directions'][direction]['conflicts'], [])
            self.assertEqual(result['directions'][direction]['settled_cases'], 2)

    def test_equivalence_substitution_cycle_and_strict_path_have_witnesses(self):
        result = self.summarize(self.cases([
            ('ab', 'A', 'B', 'equivalent'), ('bc', 'B', 'C', 'local_contains_canonical'),
            ('ac', 'A', 'C', 'neither'), ('cd', 'C', 'D', 'local_contains_canonical'),
            ('db', 'D', 'B', 'local_contains_canonical')]))
        kinds = {r['kind'] for r in result['directions']['forward']['conflicts']}
        self.assertIn('equivalence_substitution_conflict', kinds)
        self.assertIn('cycle_conflict', kinds)
        strict = self.summarize(self.cases([
            ('ab', 'A', 'B', 'local_contains_canonical'),
            ('bc', 'B', 'C', 'local_contains_canonical'), ('ac', 'A', 'C', 'equivalent')]))
        self.assertIn('equivalence_conflict',
                      {r['kind'] for r in strict['directions']['forward']['conflicts']})

    def test_duplicate_inputs_preserve_distinct_producers_and_overlapping_witnesses(self):
        rows = self.cases([('ab', 'A', 'B', 'neither'), ('cd', 'C', 'D', 'neither')],
                          same_input=True)
        result = self.summarize(rows)
        self.assertEqual(result['endpoints'], 4)
        self.assertEqual(result['reversals']['complete_pairs'], 2)
        self.assertEqual(len({row['input_sha256'] for row in rows}), 1)
        self.assertEqual(result['reversals']['unique_complete_request_pairs'], 1)
        self.assertEqual(result['reversals']['duplicate_request_pair_witnesses'][0]['pair_ids'],
                         ['ab', 'cd'])

    def test_failures_uncertainty_rewritten_meanings_and_missing_directions_remain_unresolved(self):
        rows = self.cases([('ab', 'A', 'B', 'local_contains_canonical'),
            ('ac', 'A', 'C', 'uncertain'), ('ad', 'A', 'D', 'unrun', 'failed')])
        rows[0]['parsed']['meaning'] += ' rewritten'
        result = self.summarize(rows)
        self.assertFalse(result['complete'])
        self.assertEqual(result['reversals']['complete_pairs'], 0)
        self.assertEqual(result['directions']['forward']['unresolved_cases'][0]['unresolved_reason'],
                         'returned_local_meaning_differs')
        subset = self.summarize(self.cases([('ab', 'A', 'B', 'neither')])[:1])
        self.assertEqual(subset['reversals']['unresolved_pairs'][0]['missing_directions'], ['reverse'])

    def test_branches_missing_producers_and_unsupported_projection_are_excluded(self):
        rows = self.cases([('ab', 'A', 'B', 'neither'), ('cd', 'C', 'D', 'neither')])
        payload = json.loads(rows[0]['inputs']['INPUT_JSON'])
        payload['canonical']['descendants'] = [{
            'id': 'C2', 'subject': 'Child', 'meaning': 'Fixed child', 'parents': ['C1']}]
        rows[0]['inputs']['INPUT_JSON'] = json.dumps(payload)
        del rows[1]['evidence']['canonical_meaning_from']
        rows[2]['evidence']['input_view'] = 'meanings'
        rows[3]['evidence']['unprojected_input']['canonical']['entries'].append({'subject': 'More'})
        result = self.summarize(rows)
        self.assertEqual(result['eligible_cases'], 0)
        self.assertEqual({r['reason'] for r in result['skipped_cases']}, {
            'canonical_branch_snapshot', 'missing_fixed_meaning_producer_receipt',
            'meaning_only_projection'})

    def test_same_producer_identity_requires_equivalence(self):
        result = self.summarize(self.cases([('same', 'A', 'A', 'neither')]))
        for direction in ('forward', 'reverse'):
            self.assertEqual(result['directions'][direction]['conflicts'][0]['kind'],
                             'identity_conflict')

    def test_reversal_requires_identical_producer_endpoints(self):
        rows = self.cases([('ab', 'A', 'B', 'neither')])
        producers = rows[1]['evidence']['canonical_meaning_from']
        producers['C1'] = {**producers['C1'], 'case': 'Different producer'}
        with self.assertRaisesRegex(ValueError, 'endpoint identities differ'):
            self.summarize(rows)

    def test_symmetric_reversals_and_transitivity_ignore_removed_graph_evidence(self):
        from sse_multivector.hierarchy_node_pairs import project_symmetric_fixed_meanings
        rows = self.cases([('ab', 'A', 'B', 'local_contains_canonical'),
            ('bc', 'B', 'C', 'local_contains_canonical'), ('ac', 'A', 'C', 'neither')])
        symmetric = []
        for row in rows:
            row['evidence']['unprojected_input']['canonical']['parents'] = ['OldParent']
            projected = project_symmetric_fixed_meanings(row)
            del projected['parsed']['meaning']
            projected['parsed']['relation'] = {
                'local_contains_canonical': 'A_contains_B',
                'canonical_contains_local': 'B_contains_A'}.get(
                    row['parsed']['relation'], row['parsed']['relation'])
            symmetric.append(projected)
        result = self.summarize(symmetric)
        self.assertEqual(result['eligible_cases'], 6)
        self.assertEqual(result['reversals']['complete_pairs'], 3)
        self.assertEqual(result['reversals']['conflicts'], [])
        for direction in ('forward', 'reverse'):
            self.assertEqual(result['directions'][direction]['conflicts'][0]['kind'],
                             'transitivity_conflict')
        symmetric[1]['parsed']['relation'] = 'neither'
        conflict = self.summarize(symmetric)['reversals']['conflicts'][0]
        self.assertEqual(conflict['forward']['relation'], 'A_contains_B')
        self.assertEqual(conflict['reverse']['relation'], 'neither')

    def test_symmetric_uncertainty_failures_and_missing_receipts_stay_unresolved(self):
        from sse_multivector.hierarchy_node_pairs import project_symmetric_fixed_meanings
        rows = self.cases([('ab', 'A', 'B', 'uncertain'),
                           ('ac', 'A', 'C', 'unrun', 'failed'),
                           ('ad', 'A', 'D', 'neither')])
        symmetric = [project_symmetric_fixed_meanings(row) for row in rows]
        for row in symmetric:
            if row.get('parsed'):
                del row['parsed']['meaning']
        symmetric[-1]['receipt'] = None
        result = self.summarize(symmetric)
        self.assertFalse(result['complete'])
        self.assertEqual(result['reversals']['complete_pairs'], 0)
        self.assertEqual(len(result['reversals']['unresolved_pairs']), 3)
        self.assertEqual({case['unresolved_reason'] for direction in result['directions'].values()
                          for case in direction['unresolved_cases']},
                         {'uncertain', 'unrun', 'failed', 'missing_compare_receipt'})

    def test_symmetric_input_order_preserves_producer_bound_consistency(self):
        from sse_multivector.hierarchy_node_pairs import project_symmetric_fixed_meanings
        rows = self.cases([('ab', 'A', 'B', 'local_contains_canonical'),
                           ('bc', 'B', 'C', 'local_contains_canonical'),
                           ('ac', 'A', 'C', 'neither')])
        symmetric = [project_symmetric_fixed_meanings(row) for row in rows]
        for row in symmetric:
            del row['parsed']['meaning']
            row['parsed']['relation'] = {
                'local_contains_canonical': 'A_contains_B',
                'canonical_contains_local': 'B_contains_A'}.get(
                    row['parsed']['relation'], row['parsed']['relation'])
        ordered = [project_symmetric_fixed_meanings(row, input_order=['B', 'A'])
                   for row in symmetric]
        for before, after in zip(symmetric, ordered):
            self.assertEqual(json.loads(after['inputs']['INPUT_JSON']),
                             json.loads(before['inputs']['INPUT_JSON']))
            self.assertEqual(list(json.loads(after['inputs']['INPUT_JSON'])), ['B', 'A'])
            for field in ('local_meaning_from', 'canonical_meaning_from', 'source_input'):
                self.assertEqual(after['evidence'][field], before['evidence'][field])
        self.assertEqual(self.summarize(ordered), self.summarize(symmetric))


if __name__ == '__main__':
    unittest.main()
