"""Graph traversal through native preparation, receipts and placement."""
import json
import os
from pathlib import Path
import subprocess
import unittest

from sse_multivector import test_canonical_continuation as fixtures


class CanonicalGraphConstructionTests(unittest.TestCase):
    setUp = fixtures.CanonicalContinuationTests.setUp
    write = fixtures.CanonicalContinuationTests.write
    calls = fixtures.CanonicalContinuationTests.calls
    dynamic_runner = fixtures.CanonicalContinuationTests.dynamic_runner
    shared = fixtures.CanonicalContinuationTests.shared
    continue_trial = fixtures.CanonicalContinuationTests.continue_trial

    def cli(self, *args, ok=True, env=None):
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent / 'experiment-runner/bin/experiment-runner'
        result = subprocess.run([str(launcher), '--project-root', str(project), *map(str, args)],
            cwd=self.root, env={**os.environ, 'FAKE_RUNNER_LOG': str(self.log), **(env or {})},
            text=True, capture_output=True, timeout=60)
        self.assertEqual(result.returncode == 0, ok, result.stderr + result.stdout)
        return result

    def setup_graph(self, *, with_child=False):
        self.dynamic_runner()
        self.prompt.write_text('GENERIC PROMPT {INPUT_JSON}')
        names = ['Food', 'Vegetables', 'Gardening', 'New topic']
        notes = [dict(
            note_id=f'n{i}', text=name, subjects=[dict(number='1', subject=name, context=name)])
            for i, name in enumerate(names, 1)]
        if with_child:
            notes[1]['subjects'].append(dict(number='1.1', subject='New topic', context='Selected child'))
        self.write('notes.json', dict(schema_version=1, notes=notes))
        base = json.loads(self.spec.read_text())
        schemas = Path(__file__).with_name('shr_single_pair')
        for name, schema in [('bootstrap', 'Hierarchy-bootstrap-v1.output.schema.json'),
                             ('comparison', 'Hierarchy-compare-v4.output.schema.json')]:
            self.write(name + '.json', {**base, 'runner': {**base['runner'],
                'output_schema': json.loads((schemas / schema).read_text())}})
        self.write('trial.json', dict(schema_version=2, corpus='notes.json',
            note_ids=['n1', 'n2', 'n3'] if with_child else ['n1', 'n2', 'n3', 'n4'], bootstrap_spec='bootstrap.json',
            comparison_spec='comparison.json', independent_meanings=True))
        self.cli('prepare-canonical-trial', 'trial', '--spec', 'trial.json')
        self.shared()
        self.continue_trial(nodes=3, attempts=10, env={'FIXTURE_RELATIONS': json.dumps({
            'Vegetables': {'C001': 'canonical_contains_local'}})})
        self.before = self.state('trial')['nodes']
        self.assertEqual(self.before[1]['parents'], ['C001'])

    def state(self, directory):
        return json.loads((self.root / directory / 'state.json').read_text())

    def fork_graph(self, *extra):
        self.cli('fork-canonical-trial', 'trial', '--output', 'search', '--graph-search', *extra)

    def finish(self, relations, *, attempts=8, ok=True):
        return self.continue_trial(nodes=1, attempts=attempts, directory='search', ok=ok,
            env={'FIXTURE_RELATIONS': json.dumps({'New topic': relations})})

    def queries(self, start):
        payloads = [json.loads(c['prompt'].removeprefix('GENERIC PROMPT '))
                    for c in self.calls()[start:]]
        return [p for p in payloads if 'canonical' in p]

    def test_local_contains_root_skips_descendant_without_inventing_receipts(self):
        self.setup_graph()
        start = len(self.calls())
        self.fork_graph()
        self.finish({'C001': 'local_contains_canonical', 'C003': 'neither'})
        state = self.state('search')
        self.assertEqual(state['status'], 'complete')
        step = state['steps'][-1]
        self.assertEqual(step['status'], 'added')
        self.assertCountEqual([p['canonical']['id'] for p in self.queries(start)], ['C001', 'C003'])
        self.assertEqual([a['id'] for a in step['answers']], ['C001', 'C003'])
        self.assertEqual(step['graph_search']['inferred'], {'C002': 'local_contains_canonical'})
        self.assertEqual(state['nodes'][0]['parents'], ['C004'])
        self.assertEqual(state['nodes'][1]['parents'], ['C001'])

    def test_neither_keeps_child_searchable_and_resumes_with_fixed_inputs(self):
        self.setup_graph()
        self.fork_graph()
        first = self.finish({'C001': 'neither', 'C003': 'neither'},
                            attempts=3, ok=False)
        self.assertIn('attempt_limit', first.stdout)
        pending = self.state('search')
        self.assertEqual(pending['nodes'], self.before)
        self.assertEqual(pending['index'], 3)
        self.assertEqual(pending['phase'], 'comparison')
        # Same persistent bound: use one native run for the remaining frontier.
        self.cli('run', pending['experiment'], '--max-new-attempts', '1', env={
            'FIXTURE_RELATIONS': json.dumps({'New topic': {'C002': 'canonical_contains_local'}})})
        self.cli('advance-canonical-trial', 'search', '--meaning-case', 'C002',
                 '--comment', 'Apply saved graph traversal.')
        state = self.state('search')
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertIn('contradiction', state['steps'][-1]['reason'])
        self.assertEqual(state['nodes'], self.before)
        phases = state['steps'][-1]['comparison_experiments']
        self.assertEqual(len(phases), 2)
        sources = [json.loads((Path(p).parent / 'source.json').read_text()) for p in phases]
        self.assertEqual(sources[0]['canonical_states'], sources[1]['canonical_states'])
        self.assertEqual(sources[0]['pairs'][0]['local_meaning_from'],
                         sources[1]['pairs'][0]['local_meaning_from'])

    def test_snapshot_reuses_exact_answers_and_preserves_source_trial(self):
        self.setup_graph()
        self.continue_trial(nodes=3, attempts=10)
        original = (self.root / 'trial/state.json').read_bytes()
        start = len(self.calls())
        self.fork_graph('--at-step', '2')
        self.continue_trial(nodes=1, attempts=8, directory='search')
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), original)
        self.assertEqual(len(self.calls()), start)
        step = self.state('search')['steps'][-1]
        self.assertEqual(step['index'], 2)
        self.assertTrue(all(a['reused'] for a in step['answers']))
        self.assertEqual(step['after'], self.state('trial')['steps'][2]['after'])

    def test_changed_phase_source_cannot_advance_or_change_graph(self):
        self.setup_graph()
        self.fork_graph()
        self.finish({'C001': 'neither', 'C003': 'neither'}, attempts=3, ok=False)
        state = self.state('search')
        source = Path(state['experiment']).parent / 'source.json'
        data = json.loads(source.read_text())
        data['canonical_states']['current'][0]['meaning'] = 'Changed fixed meaning'
        source.write_text(json.dumps(data))
        before = (self.root / 'search/state.json').read_bytes()
        start = len(self.calls())
        result = self.cli('advance-canonical-trial', 'search', '--meaning-case', 'C002',
                         '--comment', 'Reject changed phase.', ok=False)
        self.assertIn('source', result.stderr)
        self.assertEqual((self.root / 'search/state.json').read_bytes(), before)
        self.assertEqual(len(self.calls()), start)

    def test_required_mapped_parent_is_compared_even_when_inferred(self):
        self.setup_graph(with_child=True)
        start = len(self.calls())
        self.cli('prepare-canonical-child-trial', 'search', '--base-trial', 'trial',
                 '--note-id', 'n2', '--graph-search')
        self.finish({'C001': 'local_contains_canonical', 'C003': 'neither',
                     'C002': 'local_contains_canonical'})
        state = self.state('search')
        queried = [p['canonical']['id'] for p in self.queries(start)]
        self.assertCountEqual(queried[:-1], ['C001', 'C003'])
        self.assertEqual(queried[-1], 'C002')
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertIn('mapped canonical parent', state['steps'][-1]['reason'])
        self.assertEqual(state['nodes'], self.before)

    def test_uncertain_root_holds_child_before_unvisited_mapped_parent(self):
        self.setup_graph(with_child=True)
        start = len(self.calls())
        self.cli('prepare-canonical-child-trial', 'search', '--base-trial', 'trial',
                 '--note-id', 'n2', '--graph-search')
        self.finish({'C001': 'uncertain', 'C003': 'neither'})
        state = self.state('search')
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['steps'][-1]['status'], 'held')
        self.assertEqual(state['steps'][-1]['reason'], 'uncertain meaning or relationship')
        self.assertEqual(state['nodes'], self.before)
        self.assertCountEqual([p['canonical']['id'] for p in self.queries(start)], ['C001', 'C003'])
        self.assertFalse(state['steps'][-1]['graph_search']['complete'])


if __name__ == '__main__':
    unittest.main()
