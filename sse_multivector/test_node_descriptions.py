"""Offline tests through the source-bound experiment input preparation paths."""
import json
from pathlib import Path
import tempfile
import unittest

from sse_multivector import experiment_inputs as inputs


class NodeDescriptionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.items = [dict(instance=f'V{i}', vector_id=f'vector{i}', note_id=f'N{i:02}',
                           text='Tea ' + ('x' * (13000 if i == 0 else 100)),
                           byte_spans=[[0, 3]], fragments=['Tea']) for i in range(11)]
        self.write('packets.json', {'packets': [dict(packet='G', instances=self.items)]})
        self.write('hierarchy.json', {'graph': {'nodes': [dict(group='G', title='Tea',
            source_group_ids=['G'])]}})
        self.write('selection.json', dict(schema_version=1, source_packets='packets.json',
                                         hierarchy='hierarchy.json', nodes=['G']))

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def prepare(self):
        return inputs.prepare_file({'adapter': 'node_descriptions'},
                                   self.root / 'selection.json', '{INPUT_JSON}')

    def test_bounded_complete_posts_are_selected_and_source_bound(self):
        cases, sources, _ = self.prepare()
        self.assertEqual(len(cases), 1)
        case = cases[0]
        payload = case['inputs']['INPUT_JSON']
        value = json.loads(payload)
        self.assertLessEqual(len(payload), 12000)
        self.assertEqual((value['node_id'], value['node_title']), ('G', 'Tea'))
        self.assertEqual([p['note_id'] for p in value['instances']],
                         [f'N{i:02}' for i in range(1, 9)])
        for post in value['instances']:
            self.assertEqual(post['post'], self.items[int(post['note_id'][1:])]['text'])
            self.assertEqual(post['masks'], [['Tea']])
        self.assertEqual(case['evidence']['selected_note_ids'], [f'N{i:02}' for i in range(1, 9)])
        self.assertEqual(case['evidence']['skipped_note_ids'], ['N00', 'N09', 'N10'])
        self.assertEqual(set(sources), {str(self.root / p) for p in
                         ('selection.json', 'packets.json', 'hierarchy.json')})

    def test_output_preserves_identity_title_and_bounded_description(self):
        cases, _, _ = self.prepare()
        valid = dict(node_id='G', node_title='Tea', description='Drinking and preparing tea.')
        result = inputs.validate({'adapter': 'node_descriptions'}, cases[0], json.dumps(valid), None)
        self.assertEqual(result['parsed'], valid)
        for update in (dict(node_id='H'), dict(node_title='Coffee'), dict(description=' '),
                       dict(description='x' * 1201), dict(extra='field')):
            with self.subTest(update=update), self.assertRaises(ValueError):
                inputs.validate({'adapter': 'node_descriptions'}, cases[0],
                                json.dumps({**valid, **update}), None)

    def test_packet_masks_remain_validated_and_unknown_node_rejected(self):
        self.items[1]['fragments'] = ['Coffee']
        self.write('packets.json', {'packets': [dict(packet='G', instances=self.items)]})
        with self.assertRaisesRegex(ValueError, 'fragment'):
            self.prepare()
        self.items[1]['fragments'] = ['Tea']
        self.write('packets.json', {'packets': [dict(packet='G', instances=self.items)]})
        self.write('selection.json', dict(schema_version=1, source_packets='packets.json',
                                         hierarchy='hierarchy.json', nodes=['missing']))
        with self.assertRaisesRegex(ValueError, 'unknown'):
            self.prepare()

    def test_merged_sources_deduplicate_posts_and_keep_complete_masks(self):
        self.write('packets.json', {'packets': [dict(packet='G', instances=[self.items[1]]),
            dict(packet='H', instances=[{**self.items[1], 'instance': 'V12', 'vector_id': 'v12'},
                                       self.items[2]])]})
        self.write('hierarchy.json', {'graph': {'nodes': [dict(group='merged', title='Tea',
            source_group_ids=['G', 'H'], sources=[dict(note_id=item['note_id'],
            byte_spans=item['byte_spans']) for item in self.items[1:3]])]}})
        self.write('selection.json', dict(schema_version=1, source_packets='packets.json',
                                         hierarchy='hierarchy.json', nodes=['merged']))
        cases, _, _ = self.prepare()
        instances = json.loads(cases[0]['inputs']['INPUT_JSON'])['instances']
        self.assertEqual([p['note_id'] for p in instances], ['N01', 'N02'])
        self.assertEqual(instances[0]['masks'], [['Tea']])

    def test_no_complete_post_fits_is_rejected_instead_of_truncated(self):
        self.write('packets.json', {'packets': [dict(packet='G', instances=[self.items[0]])]})
        with self.assertRaisesRegex(ValueError, 'no complete posts fit'):
            self.prepare()

    def test_existing_graph_membership_must_match_original_packet_masks(self):
        sources = [dict(note_id=item['note_id'], byte_spans=item['byte_spans']) for item in self.items]
        sources[0]['byte_spans'] = [[0, 2]]
        self.write('hierarchy.json', {'graph': {'nodes': [dict(group='G', title='Tea',
            source_group_ids=['G'], sources=sources)]}})
        with self.assertRaisesRegex(ValueError, 'source masks differ'):
            self.prepare()
        self.write('hierarchy.json', {'graph': {'nodes': [dict(group='G', title='Tea',
            source_group_ids=['G'], sources=[dict(note_id=item['note_id'],
            byte_spans=item['byte_spans']) for item in self.items])]}})
        cases, _, _ = self.prepare()
        self.assertEqual(cases[0]['evidence']['selected_note_ids'], [f'N{i:02}' for i in range(1, 9)])

    def context_source(self, descriptions=None):
        self.write('subjects.json', {'notes': [dict(note_id='N1', text='Tea warms me.',
            subjects=[dict(number='1', subject='Tea', context='Tea warms the writer.',
                           byte_spans=[[0, 3]], fragments=['Tea'])])]})
        self.write('context-hierarchy.json', {'memberships': {'nodes': [dict(group='G', title='Tea',
            matched_instances=[dict(instance='V1', note_id='N1', text='Tea warms me.',
                                    byte_spans=[[0, 3]], fragments=['Tea'])])]}})
        source = dict(schema_version=1, subjects='subjects.json',
                      hierarchy='context-hierarchy.json', nodes=['G'])
        if descriptions is not None:
            self.write('descriptions.json', dict(schema_version=1, nodes=descriptions))
            source['descriptions'] = 'descriptions.json'
        self.write('contexts.json', source)
        return inputs.prepare_file(dict(adapter='subject_contexts', prominence_basis='node_title'),
                                   self.root / 'contexts.json', '{INPUT_JSON}')

    def test_collected_description_is_opt_in_and_provenance_bound(self):
        defaults, _, _ = self.context_source()
        self.assertEqual(json.loads(defaults[0]['inputs']['INPUT_JSON']),
                         dict(node_title='Tea', post='Tea warms me.'))
        description = dict(node_id='G', node_title='Tea', description='Drinking tea.')
        cases, sources, _ = self.context_source([description])
        self.assertEqual(json.loads(cases[0]['inputs']['INPUT_JSON']),
                         dict(node_title='Tea', post='Tea warms me.', node_description='Drinking tea.'))
        self.assertIn(str(self.root / 'descriptions.json'), sources)
        self.assertEqual(cases[0]['evidence']['node_description'], description['description'])
        for records in ([description, description], [], [{**description, 'node_title': 'Coffee'}]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                self.context_source(records)


if __name__ == '__main__':
    unittest.main()
