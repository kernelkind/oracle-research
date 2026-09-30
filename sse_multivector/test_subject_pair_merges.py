"""Saved comparison-driven preparation through the real experiment CLI."""

import hashlib
import json
import unittest

from sse_multivector import test_experiment as fixtures


class SubjectPairMergeTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def saved_comparisons(self, edges=None, duplicate_meaning=False, empty_mask=False, duplicate_title=False):
        self.prompt.write_text('GENERIC PROMPT\n{INPUT_JSON}')
        names = ['Food', 'Foods', 'Foodstuffs', 'Meals', 'Dining', 'Tea', 'Bread']
        if duplicate_title:
            names[5] = 'Bread'
        subjects = [dict(index=i, subject=name, context=f'Source meaning: {name}.',
                         note_id=f'N{i}', note_short_id=f'N{i}', number='1',
                         fragments=[name], byte_spans=[[0, len(name)]],
                         mask_vector_ids=[f'V{i}']) for i, name in enumerate(names)]
        if duplicate_meaning:
            subjects[1].update(subject=subjects[0]['subject'], context=subjects[0]['context'])
        if empty_mask:
            subjects[5].update(fragments=[], byte_spans=[], mask_vector_ids=[])
        edges = edges if edges is not None else [[0, 6], [2, 6]]
        self.write('subjects.json', dict(subjects=subjects, edges=edges,
            posts=[dict(note_id=f'N{i}', note_short_id=f'N{i}', text=name + '.')
                   for i, name in enumerate(names)]))
        self.write('hierarchy.json', dict(groups=[[i] for i in range(len(names))],
            member_to_group=list(range(len(names))), edges=edges))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='pairs.json')
        spec['runner']['output_schema'] = {
            'type': 'object', 'additionalProperties': False,
            'required': ['relation', 'reason'],
            'properties': {'relation': {'type': 'string', 'enum': [
                'equivalent', 'a_parent_of_b', 'b_parent_of_a', 'neither', 'uncertain']},
                'reason': {'type': 'string'}}}
        self.write('spec.json', spec)
        batches = [
            ('merges', 'equivalent', [('m01', 0, 1), ('m12', 1, 2)]),
            ('parents', 'a_parent_of_b', [('p03', 0, 3), ('p13', 1, 3), ('p24', 2, 4)]),
            ('separate', 'neither', [('keep54', 5, 4)]),
        ]
        for name, relation, pairs in batches:
            self.write('pairs.json', dict(schema_version=1, inputs='subjects.json',
                hierarchy='hierarchy.json', pairs=[dict(id=cid, A=f'S{a:04d}', B=f'S{b:04d}')
                                                  for cid, a, b in pairs]))
            self.prepare(name)
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                dict(relation=relation, reason='Saved fixture judgment.'))})
        self.write('combined.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='hierarchy.json', comparisons=[name for name, _, _ in batches]))
        spec['dataset']['path'] = 'combined.json'
        self.write('spec.json', spec)

    def test_combines_chained_equivalences_recompares_changed_pairs_and_reuses_unchanged(self):
        self.saved_comparisons()
        source_bytes = {name: (self.root / name).read_bytes()
                        for name in ['subjects.json', 'hierarchy.json']}
        self.assertEqual(len(self.calls()), 6)
        self.prepare('combined')
        report = self.show('combined')
        self.assertEqual(report['requests']['new'], 2)
        self.assertEqual(report['requests']['reusable'], 0)
        self.assertEqual(len(self.calls()), 6)
        changed = report['cases']
        self.assertEqual(len(changed), 2)
        case = next(c for c in changed if c['evidence']['B']['node_id'] == 'S0003')
        self.assertEqual([s['index'] for s in case['evidence']['A']['subject_entries']], [0, 1, 2])
        self.assertEqual([s['mask_vector_ids'] for s in case['evidence']['A']['subject_entries']],
                         [['V0'], ['V1'], ['V2']])
        self.assertEqual([e['subject'] for e in json.loads(case['inputs']['INPUT_JSON'])['A']],
                         ['Food', 'Foods', 'Foodstuffs'])
        self.assertNotIn('Saved fixture judgment', case['prompt'])
        self.assertNotIn('V0', case['prompt'])
        self.assertEqual(len(case['evidence']['previous_comparisons']), 2)
        plan = json.loads((self.root / 'combined/experiment.json').read_text())['plan']
        combined = plan['preparation']
        unchanged = combined['unchanged_comparisons'][0]
        self.assertEqual(unchanged['source']['inputs'], self.show('separate')['cases'][0]['inputs'])
        self.assertEqual(unchanged['source']['answer']['relation'], 'neither')
        self.assertEqual((unchanged['A'], unchanged['B']), ('S0005', 'S0004'))
        self.assertEqual(combined['summary'], dict(original_nodes=7, combined_nodes=5,
            equivalent_answers=2, internal_comparisons=2, original_comparisons=6,
            current_pairs=3, changed_pairs=2, unchanged_pairs=1))
        self.assertEqual(combined['hierarchy']['groups'], [[0, 1, 2], [3], [4], [5], [6]])
        self.assertEqual(combined['hierarchy']['edges'], [[0, 4]])
        self.assertEqual(combined['original_node_to_combined']['S0002'], 'S0000')
        for name in ['combined.json', 'merges/experiment.json', 'parents/run/results.jsonl']:
            path = self.root / name
            self.assertEqual(plan['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.cli('run', 'combined', '--max-new-attempts', 2,
                 env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"relation":"neither","reason":"New judgment."}'})
        result = self.show('combined')
        self.assertEqual(result['summary']['reused'], 0)
        self.assertEqual(result['summary']['attempts'], 2)
        self.assertEqual(result['summary']['valid'], 2)
        self.assertEqual(len(self.calls()), 8)
        for name, raw in source_bytes.items():
            self.assertEqual((self.root / name).read_bytes(), raw)

    def test_deduplicates_only_exact_model_entries_not_original_subjects(self):
        self.saved_comparisons(duplicate_meaning=True)
        self.prepare('combined')
        case = next(c for c in self.show('combined')['cases']
                    if c['evidence']['A']['node_id'] == 'S0000')
        self.assertEqual([e['subject'] for e in json.loads(case['inputs']['INPUT_JSON'])['A']],
                         ['Food', 'Foodstuffs'])
        self.assertEqual([e['index'] for e in case['evidence']['A']['subject_entries']], [0, 1, 2])

    def test_rejects_changed_source_hash_without_new_calls_or_artifacts(self):
        self.saved_comparisons()
        source = json.loads((self.root / 'subjects.json').read_text())
        source['subjects'][0]['context'] = 'Different meaning.'
        self.write('subjects.json', source)
        result = self.cli('prepare', 'combined', '--spec', self.spec, ok=False)
        self.assertIn('source hash differs', result.stderr)
        self.assertFalse((self.root / 'combined').exists())
        self.assertEqual(len(self.calls()), 6)

    def test_rejects_corrupt_saved_receipt_without_reprompting(self):
        self.saved_comparisons()
        path = self.root / 'merges/run/results.jsonl'
        records = [json.loads(line) for line in path.read_text().splitlines()]
        records[0]['final_output_raw'] = '{"relation":"neither","reason":"Tampered."}'
        path.write_text(''.join(json.dumps(record) + '\n' for record in records))
        result = self.cli('prepare', 'combined', '--spec', self.spec, ok=False)
        self.assertIn('comparison is not valid', result.stderr)
        self.assertFalse((self.root / 'combined').exists())
        self.assertEqual(len(self.calls()), 6)

    def test_stops_on_sp_cycle_without_choosing_a_merge_winner(self):
        self.saved_comparisons(edges=[[0, 3], [3, 1]])
        original = (self.root / 'hierarchy.json').read_bytes()
        result = self.cli('prepare', 'combined', '--spec', self.spec, ok=False)
        self.assertIn('creates an SP cycle', result.stderr)
        self.assertFalse((self.root / 'combined').exists())
        self.assertEqual((self.root / 'hierarchy.json').read_bytes(), original)
        self.assertEqual(len(self.calls()), 6)

    def prepare_export(self, relation='a_parent_of_b', run=True, **kwargs):
        self.saved_comparisons(**kwargs)
        self.prepare('combined')
        if run:
            self.cli('run', 'combined', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                dict(relation=relation, reason='Current saved answer.'))})
        subjects = json.loads((self.root / 'subjects.json').read_text())
        source = self.root / 'masks'
        source.mkdir()
        (source / 'masked-posts.json').write_text(json.dumps({'notes': subjects['posts']}))
        (source / 'vector-map.json').write_text(json.dumps({'vectors': [dict(
            vector_id=s['mask_vector_ids'][0], short_id=s['mask_vector_ids'][0],
            note_id=s['note_id'], note_short_id=s['note_short_id'],
            byte_spans=s['byte_spans'], fragments=s['fragments'])
            for s in subjects['subjects'] if s['mask_vector_ids']]}))
        return source, subjects

    def test_exports_saved_ancestors_and_reduces_only_browsing_links(self):
        source, subjects = self.prepare_export(edges=[[0, 6], [2, 6], [3, 6], [5, 6]])
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['ancestor_answers'], 2)
        self.assertEqual(summary['browsing_links_omitted'], 1)
        self.assertEqual(summary['inference_calls'], 0)
        graph = json.loads((self.root / 'view/results.json').read_text())
        self.assertIn([0, 4], graph['edges'])  # Food -> Bread remains underlying evidence.
        self.assertNotIn([0, 4], graph['browsing_edges'])
        view = json.loads((self.root / 'view/categories.json').read_text())
        nodes = {n['node_id']: n for n in view['nodes']}
        self.assertEqual(set(nodes), {'root', 'S0000', 'S0003', 'S0004', 'S0005', 'S0006'})
        self.assertEqual(set(nodes['S0000']['children']), {'S0003', 'S0004'})
        self.assertEqual(nodes['S0003']['children'], ['S0006'])
        self.assertEqual(nodes['S0005']['children'], ['S0006'])  # Second parent retained.
        self.assertEqual(nodes['S0006']['note_ids'], ['N6'])  # No direct membership expansion.
        self.assertEqual(view['mask_instances']['S0000']['N6'][0]['ids'], ['V6'])
        self.assertNotIn('original SP links only', nodes['S0000']['analysis'])
        provenance = json.loads((self.root / 'view/provenance.json').read_text())
        self.assertEqual(provenance['subjects'], subjects['subjects'])
        self.assertEqual(len(provenance['comparisons']), 3)
        self.assertTrue(all(c['receipt'] for c in provenance['comparisons']))
        self.assertEqual(len(self.calls()), calls)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        snapshot = {p: p.read_bytes() for p in (self.root / 'view').iterdir()}
        failed = self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view', ok=False)
        self.assertIn('exists', failed.stderr)
        self.assertEqual(snapshot, {p: p.read_bytes() for p in snapshot})

    def test_export_stops_on_conflicts_and_pending_equivalences_without_repair(self):
        for kwargs, message in [
            (dict(edges=[[3, 0]]), 'create a cycle'),
            (dict(edges=[[5, 4]]), 'neither answer conflicts'),
            (dict(relation='equivalent'), 'separate HG6 decision'),
            (dict(run=False), 'comparison is not valid'),
        ]:
            with self.subTest(kwargs=kwargs):
                self.setUp()
                source, _ = self.prepare_export(**kwargs)
                before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                calls = len(self.calls())
                failed = self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view', ok=False)
                self.assertIn(message, failed.stderr)
                self.assertFalse((self.root / 'view').exists())
                self.assertEqual(before, {p: p.read_bytes() for p in before})
                self.assertEqual(len(self.calls()), calls)

    def prepare_additional_export(self, relation='a_parent_of_b', run=True, pairs=None, **kwargs):
        source, _ = self.prepare_export(**kwargs)
        self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view')
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='additional.json')
        self.write('additional-spec.json', spec)
        self.write('additional.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='view/results.json', pairs=pairs or [dict(id='food-tea', A='S0000', B='S0005')]))
        self.cli('prepare', 'additional', '--spec', self.root / 'additional-spec.json')
        if run:
            self.cli('run', 'additional', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(
                dict(relation=relation, reason='Saved additional answer.'))})
        return source

    def test_extends_saved_export_with_completed_comparisons_without_calls_or_source_changes(self):
        source = self.prepare_additional_export(edges=[[0, 6], [2, 6], [3, 6], [5, 6]])
        base = json.loads((self.root / 'view/results.json').read_text())
        previous = json.loads((self.root / 'view/provenance.json').read_text())
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        calls = len(self.calls())
        exported = self.cli('export-hierarchy', 'additional', '--base', 'view',
            '--source', source, '--output', 'extended')
        summary = json.loads(exported.stdout)
        self.assertEqual(summary['inference_calls'], 0)
        self.assertEqual(summary['new_ancestor_links'], 1)
        self.assertEqual(summary['comparisons'], 4)
        graph = json.loads((self.root / 'extended/results.json').read_text())
        self.assertEqual(graph['groups'], base['groups'])
        self.assertEqual(graph['member_to_group'], base['member_to_group'])
        self.assertEqual(graph['sp_edges'], base['sp_edges'])
        self.assertEqual(set(map(tuple, graph['edges'])), set(map(tuple, base['edges'])) | {(0, 3)})
        view = json.loads((self.root / 'extended/categories.json').read_text())
        old_view = json.loads((self.root / 'view/categories.json').read_text())
        self.assertEqual({n['node_id']: n['note_ids'] for n in view['nodes']},
                         {n['node_id']: n['note_ids'] for n in old_view['nodes']})
        self.assertEqual(view['mask_instances']['S0005'], old_view['mask_instances']['S0005'])
        provenance = json.loads((self.root / 'extended/provenance.json').read_text())
        self.assertEqual(provenance['comparisons'][:-1], previous['comparisons'])
        self.assertEqual(provenance['comparisons'][-1]['id'], 'food-tea')
        self.assertEqual(provenance['masks'], previous['masks'])
        self.assertEqual(provenance['subjects'], previous['subjects'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(len(self.calls()), calls)

    def test_merge_only_export_rejects_other_answers_and_missing_base(self):
        source = self.prepare_additional_export(relation='uncertain')
        calls = len(self.calls())
        for base, message in [(['--base', 'view'], 'requires only equivalent'),
                              ([], 'requires --base')]:
            with self.subTest(base=base):
                failed = self.cli('export-hierarchy', 'additional', *base,
                    '--source', source, '--output', 'merged-view', '--combine-equivalent', ok=False)
                self.assertIn(message, failed.stderr)
                self.assertFalse((self.root / 'merged-view').exists())
        self.assertEqual(len(self.calls()), calls)

    def test_inherits_consistent_judgments_through_saved_equivalence_merges(self):
        source = self.prepare_additional_export(relation='equivalent',
            pairs=[dict(id='merge-meals', A='S0003', B='S0004')])
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'additional', '--base', 'view',
            '--source', source, '--output', 'inherited-view', '--combine-equivalent',
            '--inherit-equivalent-judgments')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['inherited_comparisons'], 2)
        self.assertEqual(summary['pending_comparisons'], 0)
        self.assertEqual(summary['inference_calls'], 0)
        provenance = json.loads((self.root / 'inherited-view/provenance.json').read_text())
        self.assertEqual(len(provenance['comparisons']), 2)
        for c in provenance['comparisons']:
            self.assertEqual(c['stage'], 'HG7-inherited')
            self.assertIsNone(c['receipt'])  # No model receipt for these new inputs.
            self.assertTrue(c['inheritance']['previous_comparisons'])
            self.assertTrue(c['inheritance']['equivalence_case_ids'])
            self.assertTrue(all(p['receipt'] for p in c['inheritance']['previous_comparisons']))
        food = next(c for c in provenance['comparisons'] if c['A'] == 'S0000')
        self.assertEqual(food['answer']['relation'], 'a_parent_of_b')
        self.assertEqual(len(food['inheritance']['previous_comparisons']), 2)
        self.assertEqual(len(json.loads(food['inputs']['INPUT_JSON'])['B']), 2)
        self.assertNotEqual(food['inputs'], food['inheritance']['previous_comparisons'][0]['inputs'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(len(self.calls()), calls)

        self.write('inherited-followup.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='inherited-view/results.json',
            pairs=[dict(id='food-tea', A='S0000', B='S0005')]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='inherited-followup.json')
        self.write('inherited-followup-spec.json', spec)
        self.cli('prepare', 'inherited-followup', '--spec', self.root / 'inherited-followup-spec.json')
        self.cli('run', 'inherited-followup', env={'FAKE_RUNNER_PROMPT_RESPONSE':
            '{"relation":"uncertain","reason":"Unrelated fixture."}'})
        calls = len(self.calls())
        replay = self.cli('export-hierarchy', 'inherited-followup', '--base', 'inherited-view',
                         '--source', source, '--output', 'inherited-replay')
        self.assertEqual(json.loads(replay.stdout)['inherited_comparisons'], 2)
        self.assertEqual(json.loads(replay.stdout)['pending_comparisons'], 0)
        self.assertEqual(len(self.calls()), calls)

    def prepare_merge_after_additional(self, relation, a, b):
        source = self.prepare_additional_export(relation=relation,
            pairs=[dict(id='prior', A=a, B=b)])
        self.cli('export-hierarchy', 'additional', '--base', 'view',
                 '--source', source, '--output', 'before-merge')
        self.write('new-merge.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='before-merge/results.json',
            pairs=[dict(id='merge-meals', A='S0003', B='S0004')]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='new-merge.json')
        self.write('new-merge-spec.json', spec)
        self.cli('prepare', 'new-merge', '--spec', self.root / 'new-merge-spec.json')
        self.cli('run', 'new-merge', env={'FAKE_RUNNER_PROMPT_RESPONSE':
            '{"relation":"equivalent","reason":"Fixture equivalence."}'})
        return source

    def test_equivalence_inheritance_normalizes_reversed_ancestor_answers(self):
        source = self.prepare_merge_after_additional('a_parent_of_b', 'S0006', 'S0003')
        calls = len(self.calls())
        self.cli('export-hierarchy', 'new-merge', '--base', 'before-merge',
                 '--source', source, '--output', 'inherited-view', '--combine-equivalent',
                 '--inherit-equivalent-judgments')
        p = json.loads((self.root / 'inherited-view/provenance.json').read_text())
        c = next(c for c in p['comparisons'] if (c['A'], c['B']) == ('S0003', 'S0006'))
        self.assertEqual(c['answer']['relation'], 'b_parent_of_a')
        self.assertEqual(c['inheritance']['previous_comparisons'][0]['answer']['relation'], 'a_parent_of_b')
        self.assertEqual(len(self.calls()), calls)

    def test_equivalence_inheritance_keeps_disagreements_pending_without_choosing(self):
        source = self.prepare_merge_after_additional('a_parent_of_b', 'S0005', 'S0003')
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'new-merge', '--base', 'before-merge',
                 '--source', source, '--output', 'inherited-view', '--combine-equivalent',
                 '--inherit-equivalent-judgments')
        self.assertEqual(json.loads(result.stdout)['pending_comparisons'], 1)
        p = json.loads((self.root / 'inherited-view/provenance.json').read_text())
        pending = p['preparation']['pending_comparisons'][0]
        self.assertEqual(len(pending['previous_comparisons']), 2)
        self.assertIn('disagree', pending['pending_reason'])
        self.assertFalse(any({c['A'], c['B']} == {'S0003', 'S0005'} for c in p['comparisons']))
        self.assertEqual(len(self.calls()), calls)

    def test_merge_export_rebuilds_automatic_sibling_nomination_evidence(self):
        source, _ = self.prepare_export(duplicate_title=True,
            edges=[[0, 5], [0, 6], [2, 6]])
        self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view')
        self.write('siblings.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='view/results.json', selection='same_worded_siblings'))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='siblings.json')
        self.write('siblings-spec.json', spec)
        self.cli('prepare', 'siblings', '--spec', self.root / 'siblings-spec.json')
        self.cli('run', 'siblings', env={'FAKE_RUNNER_PROMPT_RESPONSE':
            '{"relation":"equivalent","reason":"The same broad subject."}'})
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'siblings', '--base', 'view',
            '--source', source, '--output', 'merged-view', '--combine-equivalent')
        self.assertEqual(json.loads(result.stdout)['nodes_combined'], 1)
        self.assertEqual(len(self.calls()), calls)

    def test_additional_export_replays_first_generation_provenance(self):
        source = self.prepare_additional_export()
        path = self.root / 'view/provenance.json'
        old = json.loads(path.read_text())
        del old['export']
        path.write_text(json.dumps(old))
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'additional', '--base', 'view',
            '--source', source, '--output', 'extended')
        self.assertEqual(json.loads(result.stdout)['new_ancestor_links'], 1)
        self.assertEqual(len(self.calls()), calls)

    def test_exports_equivalence_only_merges_without_inference_or_stale_answers(self):
        source = self.prepare_additional_export(relation='equivalent',
            pairs=[dict(id='merge-meals', A='S0003', B='S0004')])
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'additional', '--base', 'view',
            '--source', source, '--output', 'merged-view', '--combine-equivalent')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['nodes'], 4)
        self.assertEqual(summary['nodes_combined'], 1)
        self.assertEqual(summary['pending_comparisons'], 2)
        self.assertEqual(summary['inference_calls'], 0)
        graph = json.loads((self.root / 'merged-view/results.json').read_text())
        self.assertEqual(graph['groups'], [[0, 1, 2], [3, 4], [5], [6]])
        self.assertIn([0, 1], graph['edges'])  # Existing Food ancestry survives.
        provenance = json.loads((self.root / 'merged-view/provenance.json').read_text())
        original = json.loads((self.root / 'view/provenance.json').read_text())
        self.assertEqual(provenance['subjects'], original['subjects'])
        self.assertEqual(provenance['masks'], original['masks'])
        self.assertEqual(provenance['comparisons'], [])  # Old inputs are not current judgments.
        prep = provenance['preparation']
        self.assertEqual(len(prep['equivalent_answers']), 1)
        self.assertEqual(len(prep['pending_comparisons']), 2)
        self.assertEqual(len(prep['previous_comparisons']), 4)
        view = json.loads((self.root / 'merged-view/categories.json').read_text())
        nodes = {n['node_id']: n for n in view['nodes']}
        self.assertEqual(nodes['S0003']['note_ids'], ['N3', 'N4'])
        self.assertIn('HG7', nodes['S0003']['analysis'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual(len(self.calls()), calls)

        # Continuation reconstructs the merge from bound source answers, not
        # a trusted copy of its groups. Unrelated answers leave HG7 pending.
        self.write('followup.json', dict(schema_version=1, inputs='subjects.json',
            hierarchy='merged-view/results.json',
            pairs=[dict(id='food-tea', A='S0000', B='S0005')]))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='subject_pairs', path='followup.json')
        self.write('followup-spec.json', spec)
        self.cli('prepare', 'followup', '--spec', self.root / 'followup-spec.json')
        self.cli('run', 'followup', env={'FAKE_RUNNER_PROMPT_RESPONSE':
            '{"relation":"uncertain","reason":"Unrelated fixture."}'})
        calls = len(self.calls())
        result = self.cli('export-hierarchy', 'followup', '--base', 'merged-view',
                         '--source', source, '--output', 'replayed-view')
        self.assertEqual(json.loads(result.stdout)['pending_comparisons'], 2)
        self.assertEqual(len(self.calls()), calls)
        altered = json.loads((self.root / 'merged-view/provenance.json').read_text())
        altered['preparation']['pending_comparisons'].clear()
        self.write('merged-view/provenance.json', altered)
        failed = self.cli('export-hierarchy', 'followup', '--base', 'merged-view',
                         '--source', source, '--output', 'tampered-view', ok=False)
        self.assertIn('provenance preparation differs', failed.stderr)
        self.assertFalse((self.root / 'tampered-view').exists())

    def test_additional_export_rejects_conflicts_equivalence_duplicates_and_unrun_answers(self):
        for kwargs, message in [
            (dict(pairs=[dict(id='cycle', A='S0006', B='S0000')]), 'create a cycle'),
            (dict(relation='b_parent_of_a'), 'neither answer conflicts'),
            (dict(relation='equivalent'), 'separate HG6 decision'),
            (dict(run=False), 'comparison is not valid'),
            (dict(pairs=[dict(id='repeat', A='S0000', B='S0003')]), 'duplicate saved comparison'),
        ]:
            with self.subTest(kwargs=kwargs):
                self.setUp()
                source = self.prepare_additional_export(**kwargs)
                before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                calls = len(self.calls())
                failed = self.cli('export-hierarchy', 'additional', '--base', 'view',
                    '--source', source, '--output', 'extended', ok=False)
                self.assertIn(message, failed.stderr)
                self.assertFalse((self.root / 'extended').exists())
                self.assertEqual(before, {p: p.read_bytes() for p in before})
                self.assertEqual(len(self.calls()), calls)

    def test_additional_export_rejects_tampered_base_receipts_and_source_hashes(self):
        for name, message in [
            ('view/categories.json', 'base export categories differs'),
            ('view/provenance.json', 'base export provenance comparisons differs'),
            ('additional/run/results.jsonl', 'comparison is not valid'),
            ('subjects.json', 'protected source changed'),
        ]:
            with self.subTest(name=name):
                self.setUp()
                source = self.prepare_additional_export()
                path = self.root / name
                if path.suffix == '.jsonl':
                    records = [json.loads(line) for line in path.read_text().splitlines()]
                    records[0]['final_output_raw'] = '{"relation":"neither","reason":"Tampered."}'
                    path.write_text(''.join(json.dumps(r) + '\n' for r in records))
                else:
                    value = json.loads(path.read_text())
                    if name.endswith('categories.json'):
                        value['nodes'][1]['label'] = 'Tampered.'
                    elif name.endswith('provenance.json'):
                        value['comparisons'][0]['answer']['reason'] = 'Tampered.'
                    else:
                        value['subjects'][0]['context'] = 'Tampered.'
                    path.write_text(json.dumps(value))
                calls = len(self.calls())
                failed = self.cli('export-hierarchy', 'additional', '--base', 'view',
                    '--source', source, '--output', 'extended', ok=False)
                self.assertIn(message, failed.stderr)
                self.assertFalse((self.root / 'extended').exists())
                self.assertEqual(len(self.calls()), calls)

    def test_additional_export_keeps_empty_masks_and_uncertain_answers(self):
        source = self.prepare_additional_export(relation='uncertain', empty_mask=True)
        result = self.cli('export-hierarchy', 'additional', '--base', 'view',
            '--source', source, '--output', 'extended')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['uncertain_answers'], 1)
        self.assertEqual(summary['new_ancestor_links'], 0)
        base = json.loads((self.root / 'view/categories.json').read_text())
        view = json.loads((self.root / 'extended/categories.json').read_text())
        self.assertEqual(view['mask_instances'], base['mask_instances'])
        self.assertEqual(view['mask_instances']['S0005'], {'N5': []})

    def test_additional_export_requires_exact_base_and_separate_output(self):
        source = self.prepare_additional_export()
        self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'other')
        for base, output, message in [('other', 'extended', 'does not match --base'),
                                     ('view', 'view/nested', 'separate from saved source')]:
            failed = self.cli('export-hierarchy', 'additional', '--base', base,
                '--source', source, '--output', output, ok=False)
            self.assertIn(message, failed.stderr)
            self.assertFalse((self.root / output).exists())

    def test_export_preserves_empty_masks_and_distinct_nodes_with_identical_titles(self):
        source, _ = self.prepare_export(empty_mask=True, duplicate_title=True)
        self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view')
        view = json.loads((self.root / 'view/categories.json').read_text())
        nodes = {n['node_id']: n for n in view['nodes']}
        self.assertEqual(nodes['S0005']['label'], nodes['S0006']['label'])
        self.assertEqual(view['mask_instances']['S0005'], {'N5': []})
        self.assertEqual(view['note_masks']['S0005'], {'N5': []})

    def test_export_keeps_uncertain_answers_without_inventing_links(self):
        source, _ = self.prepare_export(relation='uncertain')
        result = self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view')
        summary = json.loads(result.stdout)
        self.assertEqual(summary['ancestor_answers'], 0)
        self.assertEqual(summary['uncertain_answers'], 2)
        self.assertEqual(summary['comparisons'], 3)

    def test_export_rejects_changed_source_or_receipts_and_bad_mask_provenance(self):
        for name, expected in [
            ('subjects.json', 'protected source changed'),
            ('separate/run/results.jsonl', 'protected source changed'),
            ('combined/run/results.jsonl', 'comparison is not valid'),
            ('masks/vector-map.json', 'mask provenance mismatch'),
        ]:
            with self.subTest(name=name):
                self.setUp()
                source, _ = self.prepare_export()
                path = self.root / name
                if path.suffix == '.jsonl':
                    records = [json.loads(line) for line in path.read_text().splitlines()]
                    records[0]['final_output_raw'] = '{"relation":"neither","reason":"Tampered."}'
                    path.write_text(''.join(json.dumps(r) + '\n' for r in records))
                else:
                    data = json.loads(path.read_text())
                    if name == 'subjects.json':
                        data['subjects'][0]['context'] = 'Tampered.'
                    else:
                        data['vectors'][0]['fragments'] = ['Wrong']
                    path.write_text(json.dumps(data))
                calls = len(self.calls())
                failed = self.cli('export-hierarchy', 'combined', '--source', source, '--output', 'view', ok=False)
                self.assertIn(expected, failed.stderr)
                self.assertFalse((self.root / 'view').exists())
                self.assertEqual(len(self.calls()), calls)


if __name__ == '__main__':
    unittest.main()
