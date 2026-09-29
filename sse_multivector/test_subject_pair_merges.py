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
