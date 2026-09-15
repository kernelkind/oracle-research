"""Note aggregation tests use production graph construction and source matching."""
from copy import deepcopy
import unittest

from true_category_graph import build_graph, prepare_inputs
from true_graph_notes import derive_note_memberships


def source_instance(instance, note_id, text, fragments):
    encoded = text.encode('utf-8')
    return dict(instance=instance, note_id=note_id, text=text,
                vector_id='vector-' + instance, fragments=fragments,
                byte_spans=[[encoded.index(fragment.encode('utf-8')),
                             encoded.index(fragment.encode('utf-8'))
                             + len(fragment.encode('utf-8'))]
                            for fragment in fragments])


def fixture(accepted=()):
    instances = [
        source_instance('V1', 'n1', 'café and tea', ['café', 'tea']),
        source_instance('V2', 'n2', '🍵 black tea', ['black tea']),
        source_instance('V3', 'n2', '🍵 black tea', ['tea']),
        source_instance('V4', 'n3', 'coffee', ['coffee']),
    ]
    groups = [dict(group=key, title='Same title' if key in 'AB' else key,
                   instances=[dict(instance=row['instance'], fragments=row['fragments'])])
              for key, row in zip('ABCD', instances)]
    packets = dict(packets=[dict(packet=key, instances=[deepcopy(row)])
                            for key, row in zip('ABCD', instances)])
    # A historical instance must not add a note absent from the canonical node.
    packets['packets'][0]['instances'].append(
        source_instance('V-old', 'old-note', 'obsolete', ['obsolete']))
    titles = dict(groups=groups)
    scores = prepare_inputs(titles)
    for row in scores:
        score = 0.9 if (row['a_id'], row['b_id']) in accepted else 0.1
        row.update(entailment_score=score, threshold_predicted=score > 0.142,
                   predicted=False, generated_text='0', generated_token_ids=[0, 632, 1],
                   eos_terminated=True)
    return build_graph(titles, scores), packets


class TrueGraphNotesTests(unittest.TestCase):
    def test_exact_canonical_instances_keep_full_source_and_deduplicate_notes(self):
        graph, packets = fixture({('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D')})
        # Two canonical masks of one note remain two pieces of evidence.
        second = source_instance('V5', 'n1', 'café and tea', ['and'])
        graph['nodes'][0]['instances'].append(
            dict(instance=second['instance'], fragments=second['fragments']))
        packets['packets'][0]['instances'].append(second)
        second['source_extra'] = {'retained': ['unchanged']}
        before = deepcopy((graph, packets))

        result = derive_note_memberships(graph, packets)
        a = result['nodes'][0]
        self.assertEqual([node['group'] for node in result['nodes']], list('ABCD'))
        self.assertEqual(a['title'], 'Same title')
        self.assertEqual(a['own_note_ids'], ['n1'])
        self.assertEqual(a['recursive_note_ids'], ['n1', 'n2', 'n3'])
        self.assertEqual((a['own_note_count'], a['recursive_note_count']), (1, 3))
        self.assertEqual(a['matched_instances'],
                         [packets['packets'][0]['instances'][0], second])
        self.assertEqual(result['stats'], dict(nodes=4, matched_instances=5,
                                               unique_note_count=3))
        self.assertEqual((graph, packets), before)
        a['matched_instances'][0]['byte_spans'][0][0] = 999
        a['matched_instances'][1]['source_extra']['retained'].append('changed')
        self.assertEqual((graph, packets), before)

    def test_cycles_and_identical_titles_preserve_categories_without_recounting(self):
        graph, packets = fixture({('A', 'B'), ('B', 'A'), ('B', 'C')})
        result = derive_note_memberships(graph, packets)
        a, b, c, d = result['nodes']
        self.assertEqual(graph['reachability']['A'], ['A', 'B', 'C'])
        self.assertEqual(a['recursive_note_ids'], ['n1', 'n2'])
        self.assertEqual(b['recursive_note_ids'], ['n2', 'n1'])
        self.assertEqual(a['recursive_note_count'], 2)
        self.assertEqual(b['recursive_note_count'], 2)
        self.assertEqual(c['recursive_note_ids'], ['n2'])
        self.assertEqual(d['recursive_note_ids'], ['n3'])
        self.assertEqual(len(result['nodes']), 4)
        self.assertNotEqual(a['own_note_ids'], b['own_note_ids'])

    def test_missing_category_path_can_still_have_all_its_notes(self):
        graph, packets = fixture({('A', 'C')})
        a, b, _, _ = derive_note_memberships(graph, packets)['nodes']
        self.assertNotIn('B', graph['reachability']['A'])
        self.assertTrue(set(b['recursive_note_ids']) <= set(a['recursive_note_ids']))
        self.assertEqual(b['own_note_ids'], ['n2'])
        self.assertEqual(a['recursive_note_ids'], ['n1', 'n2'])

    def test_source_must_match_instance_within_its_group_and_exact_fragments(self):
        mutations = [
            lambda graph, packets: packets['packets'][0].update(packet='unknown'),
            lambda graph, packets: packets['packets'][0]['instances'].pop(0),
            lambda graph, packets: packets['packets'][0]['instances'].append(
                deepcopy(packets['packets'][0]['instances'][0])),
            lambda graph, packets: packets['packets'].append(
                deepcopy(packets['packets'][0])),
            lambda graph, packets: graph['nodes'][0]['instances'][0].update(
                fragments=['cafe', 'tea']),
            lambda graph, packets: graph['nodes'][0]['instances'][0].update(
                fragments=['tea', 'café']),
            lambda graph, packets: graph['nodes'][0]['instances'].append(
                deepcopy(graph['nodes'][0]['instances'][0])),
        ]
        for index, mutate in enumerate(mutations):
            graph, packets = fixture()
            mutate(graph, packets)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                derive_note_memberships(graph, packets)

    def test_utf8_ranges_must_decode_to_each_exact_fragment(self):
        mutations = [
            lambda row: row.update(byte_spans=[[0, 4], [10, 13]]),
            lambda row: row.update(byte_spans=[[0, 5]]),
            lambda row: row.update(byte_spans=[[-1, 5], [10, 13]]),
            lambda row: row.update(byte_spans=[[0, 5], [10, 999]]),
            lambda row: row.update(byte_spans=[[False, 5], [10, 13]]),
            lambda row: row.update(byte_spans=[[0, 5], [10, 10]]),
            lambda row: row.update(text='changed café and tea'),
            lambda row: row.pop('note_id'),
            lambda row: row.update(note_id=[]),
            lambda row: row.pop('vector_id'),
        ]
        for index, mutate in enumerate(mutations):
            graph, packets = fixture()
            mutate(packets['packets'][0]['instances'][0])
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                derive_note_memberships(graph, packets)

    def test_reachability_requires_known_groups_and_does_not_infer_edges(self):
        graph, packets = fixture({('A', 'B'), ('B', 'C')})
        graph['reachability']['A'] = ['B']
        # B and C share a note: give C another note to expose any recomputation.
        packets['packets'][2]['instances'][0]['note_id'] = 'n-other'
        self.assertEqual(derive_note_memberships(graph, packets)['nodes'][0]
                         ['recursive_note_ids'], ['n1', 'n2'])
        graph['reachability']['A'] = ['unknown']
        with self.assertRaisesRegex(ValueError, 'reachability'):
            derive_note_memberships(graph, packets)
        graph['reachability'].pop('A')
        with self.assertRaisesRegex(ValueError, 'reachability'):
            derive_note_memberships(graph, packets)


if __name__ == '__main__':
    unittest.main()
