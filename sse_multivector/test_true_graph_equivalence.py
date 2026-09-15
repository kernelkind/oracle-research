"""Reviewed-equivalence tests use production scoring, graph, and note paths."""
from copy import deepcopy
import unittest

from true_category_graph import build_graph, prepare_inputs
from true_graph_equivalence import consolidate_verified_equivalents
from true_graph_notes import derive_note_memberships


def source_instance(instance, note_id, text, fragment):
    start = text.encode('utf-8').index(fragment.encode('utf-8'))
    return dict(instance=instance, note_id=note_id, text=text,
                vector_id='vector-' + instance, fragments=[fragment],
                byte_spans=[[start, start + len(fragment.encode('utf-8'))]],
                extra={'evidence': [instance]})


def fixture():
    a = source_instance('Va', 'n1', 'café and milk', 'café')
    b = source_instance('Vb', 'n1', 'café and milk', 'milk')
    c = source_instance('Vc', 'n2', 'coffee', 'coffee')
    d = source_instance('Vd', 'n3', 'beans', 'beans')
    e = source_instance('Ve', 'n4', 'other', 'other')
    instances = [[a], [b, a, c], [d], [e]]
    titles = dict(source='frozen titles', groups=[
        dict(group=key, title='Coffee' if key in 'AB' else key,
             original={'metadata': [key]},
             instances=[dict(instance=row['instance'], fragments=row['fragments'])
                        for row in rows])
        for key, rows in zip('ABCD', instances)])
    packets = dict(source='frozen packets', packets=[
        dict(packet=key, original={'metadata': [key]}, instances=deepcopy(rows))
        for key, rows in zip('ABCD', instances)])
    packets['packets'][1]['instances'].append(
        source_instance('V-old', 'old-note', 'obsolete', 'obsolete'))
    accepted = {('A', 'B'), ('B', 'A'), ('A', 'C'), ('B', 'C'),
                ('C', 'D'), ('D', 'C')}
    scores = prepare_inputs(titles)
    for row in scores:
        score = 0.9 if (row['a_id'], row['b_id']) in accepted else 0.1
        row.update(entailment_score=score, threshold_predicted=score > 0.142,
                   predicted=False, generated_text='0', generated_token_ids=[0, 632, 1],
                   eos_terminated=True, original={'pair': [row['id']]})
    approvals = [dict(canonical='A', members=['A', 'B'], title='Coffee',
                      reason='Reviewed masks describe the same category.')]
    return titles, scores, packets, approvals


def pair(rows, a, b):
    return next(row for row in rows if row['a_id'] == a and row['b_id'] == b)


class TrueGraphEquivalenceTests(unittest.TestCase):
    def test_duplicate_titles_and_mutual_acceptance_do_not_approve_equivalence(self):
        titles, scores, packets, _ = fixture()
        result = consolidate_verified_equivalents(titles, scores, packets, [])
        self.assertEqual(result, dict(titles=titles, scores=scores,
                                      source_packets=packets, consolidations=[]))
        self.assertIn(['A', 'B'], build_graph(result['titles'], result['scores'])
                      ['cycle_components'])

    def test_explicit_class_unions_masks_and_notes_without_changing_other_rows(self):
        titles, scores, packets, approvals = fixture()
        before = deepcopy((titles, scores, packets, approvals))
        result = consolidate_verified_equivalents(titles, list(reversed(scores)),
                                                   packets, approvals)
        self.assertEqual((titles, scores, packets, approvals), before)
        self.assertEqual([node['group'] for node in result['titles']['groups']], list('ACD'))
        node = result['titles']['groups'][0]
        self.assertEqual(node['group'], 'A')
        self.assertEqual(node['title'], 'Coffee')
        self.assertEqual(node['original'], titles['groups'][0]['original'])
        self.assertEqual([row['instance'] for row in node['instances']], ['Va', 'Vb', 'Vc'])
        self.assertEqual(node['source_group_ids'], ['A', 'B'])
        self.assertEqual(node['instance_contributors'],
                         {'Va': ['A', 'B'], 'Vb': ['B'], 'Vc': ['B']})
        self.assertEqual(result['titles']['groups'][1:], titles['groups'][2:])
        expected_scores = [row for row in scores if 'B' not in (row['a_id'], row['b_id'])]
        self.assertEqual(result['scores'], expected_scores)
        self.assertEqual(result['source_packets']['packets'][1:], packets['packets'][2:])
        self.assertEqual(result['titles']['source'], titles['source'])
        self.assertEqual(result['source_packets']['source'], packets['source'])

        graph = build_graph(result['titles'], result['scores'])
        notes = derive_note_memberships(graph, result['source_packets'])
        a = notes['nodes'][0]
        self.assertEqual(a['own_note_ids'], ['n1', 'n2'])
        self.assertEqual(a['own_note_count'], 2)
        self.assertEqual(a['recursive_note_ids'], ['n1', 'n2', 'n3', 'n4'])
        self.assertEqual([row['instance'] for row in a['matched_instances']],
                         ['Va', 'Vb', 'Vc'])
        self.assertEqual(a['matched_instances'][1], packets['packets'][1]['instances'][0])
        self.assertNotIn('old-note', a['recursive_note_ids'])

        consolidation, = result['consolidations']
        self.assertEqual(consolidation['approval'], approvals[0])
        self.assertEqual(consolidation['source_groups'], titles['groups'][:2])
        self.assertEqual(consolidation['source_packets'], packets['packets'][:2])
        self.assertEqual(consolidation['source_group_ids'], ['A', 'B'])
        self.assertEqual(consolidation['instance_contributors'], node['instance_contributors'])
        self.assertEqual(consolidation['removed_score_ids'],
                         [row['id'] for row in scores if 'B' in (row['a_id'], row['b_id'])])

    def test_other_cycles_remain_and_no_edge_is_added_or_repaired(self):
        titles, scores, packets, approvals = fixture()
        result = consolidate_verified_equivalents(titles, scores, packets, approvals)
        graph = build_graph(result['titles'], result['scores'])
        self.assertEqual(graph['cycle_components'], [['C', 'D']])
        self.assertEqual(graph['transitive_reduction_status'], 'blocked_by_cycles')
        self.assertIsNone(graph['transitive_reduced_edges'])
        self.assertEqual({(row['a_id'], row['b_id']) for row in graph['raw_edges']},
                         {('A', 'C'), ('C', 'D'), ('D', 'C')})
        self.assertEqual(graph['reachable_rejected_pairs'], [pair(scores, 'A', 'D')])

    def test_canonical_position_and_instances_are_preserved_despite_approval_order(self):
        titles, _, packets, approvals = fixture()
        titles['groups'] = [titles['groups'][0], titles['groups'][2],
                            titles['groups'][1], titles['groups'][3]]
        # Reuse original scores: graph validation orders them by current groups.
        _, scores, _, _ = fixture()
        approvals[0].update(canonical='B', members=['B', 'A'])
        result = consolidate_verified_equivalents(titles, scores, packets, approvals)
        self.assertEqual([node['group'] for node in result['titles']['groups']], list('CBD'))
        canonical = result['titles']['groups'][1]
        self.assertEqual(canonical['original'], {'metadata': ['B']})
        self.assertEqual(canonical['instances'], titles['groups'][2]['instances'])

    def test_approval_requires_explicit_disjoint_known_same_title_class_and_reason(self):
        mutations = [
            lambda approvals: approvals.append(deepcopy(approvals[0])),
            lambda approvals: approvals[0].update(members=['A']),
            lambda approvals: approvals[0].update(members=['A', 'A']),
            lambda approvals: approvals[0].update(members=['A', 'unknown']),
            lambda approvals: approvals[0].update(members=['A', []]),
            lambda approvals: approvals[0].update(members='AB'),
            lambda approvals: approvals[0].update(canonical='C'),
            lambda approvals: approvals[0].update(canonical=[]),
            lambda approvals: approvals[0].update(reason='  '),
            lambda approvals: approvals[0].pop('reason'),
            lambda approvals: approvals[0].update(title='Different title'),
            lambda approvals: approvals[0].update(members=['A', 'C']),
            lambda approvals: approvals.__setitem__(0, None),
        ]
        for index, mutate in enumerate(mutations):
            titles, scores, packets, approvals = fixture()
            mutate(approvals)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                consolidate_verified_equivalents(titles, scores, packets, approvals)
        for approvals in (None, {}, 'approved'):
            titles, scores, packets, _ = fixture()
            with self.subTest(approvals=approvals), self.assertRaises(ValueError):
                consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_every_distinct_pair_inside_a_class_must_be_accepted(self):
        for a, b in [('A', 'B'), ('B', 'A')]:
            titles, scores, packets, approvals = fixture()
            pair(scores, a, b).update(entailment_score=0.142, threshold_predicted=False)
            with self.subTest(pair=(a, b)), self.assertRaisesRegex(ValueError, 'accepted'):
                consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_complete_raw_scores_are_required_even_for_removed_rows(self):
        for a, b in [('A', 'B'), ('B', 'C'), ('C', 'D')]:
            titles, scores, packets, approvals = fixture()
            scores.remove(pair(scores, a, b))
            with self.subTest(pair=(a, b)), self.assertRaisesRegex(ValueError, 'missing'):
                consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_external_scores_and_native_provenance_must_agree_exactly_both_ways(self):
        changes = [dict(entailment_score=0.8),
                   dict(entailment_score=0.1, threshold_predicted=False),
                   dict(predicted=True, generated_text='1', generated_token_ids=[0, 209, 1]),
                   dict(generated_token_ids=[0, 3, 632, 1])]
        for a, b in [('B', 'C'), ('C', 'B')]:
            for change in changes:
                titles, scores, packets, approvals = fixture()
                row = pair(scores, a, b)
                row.update(change)
                row['threshold_predicted'] = row['entailment_score'] > 0.142
                # Do not accidentally test an unchanged rejected input.
                if row['entailment_score'] == pair(scores, a.replace('B', 'A'),
                                                  b.replace('B', 'A'))['entailment_score']:
                    if set(change) == {'entailment_score', 'threshold_predicted'}:
                        row.update(entailment_score=0.9, threshold_predicted=True)
                with self.subTest(pair=(a, b), change=change), \
                        self.assertRaisesRegex(ValueError, 'external'):
                    consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_identical_instance_ids_require_identical_full_payloads(self):
        for source in ('titles', 'packets'):
            titles, scores, packets, approvals = fixture()
            if source == 'titles':
                titles['groups'][1]['instances'][1]['extra'] = 'conflict'
            else:
                packets['packets'][1]['instances'][1]['extra']['evidence'].append('conflict')
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'instance'):
                consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_two_classes_check_all_cross_class_rows_and_record_contributors(self):
        titles, scores, packets, approvals = fixture()
        for node in titles['groups'][2:]:
            node['title'] = 'Beans'
        approvals.append(dict(canonical='C', members=['C', 'D'], title='Beans',
                              reason='Explicit second reviewed class.'))
        for row, frozen in zip(scores, prepare_inputs(titles)):
            row.update(frozen)
            if row['a_id'] in 'AB' and row['b_id'] in 'CD':
                row.update(entailment_score=0.9, threshold_predicted=True)
            if row['a_id'] in 'CD' and row['b_id'] in 'AB':
                row.update(entailment_score=0.1, threshold_predicted=False)
        result = consolidate_verified_equivalents(titles, scores, packets, approvals)
        self.assertEqual([node['group'] for node in result['titles']['groups']], ['A', 'C'])
        self.assertEqual(result['scores'], [pair(scores, 'A', 'C'), pair(scores, 'C', 'A')])
        self.assertEqual(result['consolidations'][0]['score_contributors']['A-contains-C'],
                         ['A-contains-C', 'A-contains-D', 'B-contains-C', 'B-contains-D'])
        pair(scores, 'B', 'D').update(entailment_score=0.8)
        with self.assertRaisesRegex(ValueError, 'external'):
            consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_three_member_class_requires_alias_to_alias_acceptance_too(self):
        titles, scores, packets, approvals = fixture()
        titles['groups'][2]['title'] = 'Coffee'
        approvals[0]['members'].append('C')
        for row, frozen in zip(scores, prepare_inputs(titles)):
            row.update(frozen)
            score = 0.9 if row['a_id'] in 'ABC' and row['b_id'] in 'ABC' else 0.1
            row.update(entailment_score=score, threshold_predicted=score > 0.142)
        result = consolidate_verified_equivalents(titles, scores, packets, approvals)
        self.assertEqual([node['group'] for node in result['titles']['groups']], ['A', 'D'])
        pair(scores, 'B', 'C').update(entailment_score=0.1, threshold_predicted=False)
        with self.assertRaisesRegex(ValueError, 'accepted'):
            consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_canonical_masks_require_matching_complete_source_evidence(self):
        mutations = [
            lambda packets: packets['packets'].pop(1),
            lambda packets: packets['packets'][1]['instances'].pop(0),
            lambda packets: packets['packets'][1]['instances'][0].update(fragments=['wrong']),
            lambda packets: packets['packets'][1]['instances'][0].pop('byte_spans'),
        ]
        for index, mutate in enumerate(mutations):
            titles, scores, packets, approvals = fixture()
            mutate(packets)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                consolidate_verified_equivalents(titles, scores, packets, approvals)

    def test_outputs_do_not_share_mutable_input_payloads(self):
        titles, scores, packets, approvals = fixture()
        before = deepcopy((titles, scores, packets, approvals))
        result = consolidate_verified_equivalents(titles, scores, packets, approvals)
        result['titles']['groups'][0]['instances'][0]['fragments'].append('changed')
        result['scores'][0]['generated_token_ids'].append(999)
        result['source_packets']['packets'][0]['instances'][0]['extra']['evidence'].append('changed')
        result['consolidations'][0]['source_groups'][0]['original']['metadata'].append('changed')
        result['consolidations'][0]['approval']['members'].append('changed')
        self.assertEqual((titles, scores, packets, approvals), before)


if __name__ == '__main__':
    unittest.main()
