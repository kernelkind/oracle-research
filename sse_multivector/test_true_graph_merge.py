"""Exercise reversible merging through its production entry points."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from true_category_graph import prepare_inputs
from true_graph_merge import merge_graph
from prepare_category_title_inputs import prepare
from test_true_graph_equivalence import fixture, source_instance


def inputs(edges):
    titles, scores, packets, _ = fixture()
    for row in scores:
        yes = (row['a_id'], row['b_id']) in edges
        row.update(predicted=yes, generated_text='1' if yes else '0',
                   generated_token_ids=[0, 209 if yes else 632, 1],
                   entailment_score=.9 if yes else .1, threshold_predicted=yes)
    return titles, scores, packets


class MergeTests(unittest.TestCase):
    def test_long_cycle_preserves_conflicting_answers_and_paths(self):
        args = inputs({('A', 'B'), ('B', 'C'), ('C', 'A'), ('C', 'D')})
        before = deepcopy(args)
        result = merge_graph(*args)
        self.assertEqual(args, before)
        merged = result['member_to_group']['A']
        self.assertEqual(result['member_to_group'], dict(A=merged, B=merged, C=merged, D='D'))
        self.assertEqual(result['graph']['reachability'], {merged: ['D'], 'D': []})
        edge, = result['graph']['raw_edges']
        self.assertEqual(edge['source_score_ids'], ['C-contains-D'])
        self.assertEqual(edge['a_id'], merged)
        self.assertEqual(edge['b_id'], 'D')
        self.assertNotIn('predicted', edge)  # No fabricated judgment of a new title.
        conflicts = {r['id'] for r in result['raw_graph']['reachable_rejected_pairs']}
        self.assertIn('A-contains-D', conflicts)
        self.assertIn('A-contains-C', conflicts)
        self.assertEqual(result['source'], dict(titles=args[0], scores=args[1], source_packets=args[2]))
        self.assertEqual(result, merge_graph(**result['source']))
        result['source']['titles']['groups'][0]['title'] = 'changed copy'
        self.assertEqual(args, before)

    def test_mask_union_deduplicates_exact_spans_not_posts_or_words(self):
        titles, scores, packets = inputs({('A', 'B'), ('B', 'A')})
        alias = deepcopy(packets['packets'][0]['instances'][0])
        alias.update(instance='alias', vector_id='alias-vector')
        # Same instance ID is legitimate across different packets, too.
        other = source_instance('Va', 'n5', 'café café', 'café')
        repeated = deepcopy(other)
        repeated.update(instance='repeat', byte_spans=[[6, 11]])
        for row in (alias, other, repeated):
            titles['groups'][1]['instances'].append(dict(instance=row['instance'], fragments=row['fragments']))
            packets['packets'][1]['instances'].append(row)
        # Remove the original Va in B to avoid an ambiguous within-packet ID.
        titles['groups'][1]['instances'].pop(1)
        packets['packets'][1]['instances'].pop(1)
        result = merge_graph(titles, scores, packets)
        node = next(n for n in result['graph']['nodes'] if len(n['source_group_ids']) > 1)
        self.assertIsNone(node['title'])
        self.assertEqual(node['title_status'], 'pending')
        self.assertEqual(len(node['instances']), 5)
        packet, = result['naming_source_packets']['packets']
        self.assertEqual(len(packet['instances']), 5)
        origins = [o for i in packet['instances'] for o in i['origins']]
        self.assertEqual(len(origins), 6)
        self.assertNotIn('V-old', [o['source_instance']['instance'] for o in origins])
        prepared, = prepare(result['naming_source_packets'], '{NUMBERED_INSTANCES}', [])
        self.assertEqual(prepared['duplicates_removed'], 0)
        self.assertEqual(len(prepared['instances']), 5)
        self.assertEqual(result['memberships']['stats']['unique_note_count'], 5)

    def test_id_independent_of_order_and_titles(self):
        titles, scores, packets = inputs({('A', 'B'), ('B', 'A')})
        original = merge_graph(titles, scores, packets)
        titles['groups'].reverse()
        for node in titles['groups']:
            node['title'] += ' changed'
        new_inputs = {r['id']: r for r in prepare_inputs(titles)}
        for row in scores:
            row.update(new_inputs[row['id']])
        packets['packets'].reverse()
        result = merge_graph(titles, list(reversed(scores)), packets)
        self.assertEqual(result['member_to_group'], original['member_to_group'])

    def test_shared_child_disconnected_node_and_transitive_reduction(self):
        args = inputs({('A', 'C'), ('B', 'C')})
        result = merge_graph(*args)
        self.assertEqual(result['member_to_group'], {x: x for x in 'ABCD'})
        self.assertEqual(result['graph']['roots'], ['A', 'B', 'D'])
        self.assertEqual(len(result['graph']['transitive_reduced_edges']), 2)
        self.assertEqual(result['naming_source_packets'], {'packets': []})
        args = inputs({('A', 'B'), ('B', 'A'), ('B', 'C'), ('C', 'D'), ('A', 'D')})
        result = merge_graph(*args)
        self.assertEqual(len(result['graph']['raw_edges']), 3)
        self.assertEqual(len(result['graph']['transitive_reduced_edges']), 2)

    def test_external_contributors_are_all_preserved(self):
        result = merge_graph(*inputs({('A', 'B'), ('B', 'A'), ('A', 'C'), ('B', 'C')}))
        self.assertEqual(result['graph']['raw_edges'][0]['source_score_ids'],
                         ['A-contains-C', 'B-contains-C'])

    def test_title_dedup_does_not_discard_source_mask_aliases(self):
        titles, scores, packets = inputs(set())
        alias = deepcopy(packets['packets'][0]['instances'][0])
        alias.update(instance='duplicate-mask', vector_id='duplicate-vector')
        packets['packets'][0]['instances'].append(alias)
        result = merge_graph(titles, scores, packets)
        mask = result['source_packets']['packets'][0]['instances'][0]
        self.assertEqual([o['source_instance']['instance'] for o in mask['origins']],
                         ['Va', 'duplicate-mask'])

    def test_native_no_above_cutoff_does_not_form_a_cycle(self):
        titles, scores, packets = inputs({('A', 'B')})
        reverse = next(r for r in scores if r['id'] == 'B-contains-A')
        reverse.update(entailment_score=.23, threshold_predicted=True)
        result = merge_graph(titles, scores, packets)
        self.assertEqual(result['graph']['stats']['merged_components'], 0)
        self.assertEqual(result['graph']['raw_edges'][0]['source_score_ids'], ['A-contains-B'])

    def test_all_three_node_directed_graphs_preserve_paths_after_reduction(self):
        pairs = [(a, b) for a in 'ABC' for b in 'ABC' if a != b]
        for bits in range(1 << len(pairs)):
            with self.subTest(bits=bits):
                chosen = {pair for i, pair in enumerate(pairs) if bits & (1 << i)}
                result = merge_graph(*inputs(chosen))
                graph = result['graph']
                mapping = result['member_to_group']
                for source in 'ABCD':
                    expected, pending = set(), [source]
                    while pending:
                        current = pending.pop()
                        for a, b in chosen:
                            if a == current and b not in expected:
                                expected.add(b)
                                pending.append(b)
                    actual, pending = set(), [mapping[source]]
                    while pending:
                        current = pending.pop()
                        for edge in graph['transitive_reduced_edges']:
                            if edge['a_id'] == current and edge['b_id'] not in actual:
                                actual.add(edge['b_id'])
                                pending.append(edge['b_id'])
                    self.assertEqual(actual, {mapping[n] for n in expected} - {mapping[source]})
                accepted = set(result['internal_accepted_score_ids'])
                for edge in graph['raw_edges']:
                    accepted.update(edge['source_score_ids'])
                self.assertEqual(accepted, {f'{a}-contains-{b}' for a, b in chosen})

    def test_incomplete_or_unresolved_evidence_cannot_publish_a_merge(self):
        titles, scores, packets = inputs(set())
        with self.assertRaisesRegex(ValueError, 'missing'):
            merge_graph(titles, scores[:-1], packets)
        scores[0].update(predicted=None, generated_text='?', generated_token_ids=[0, 99, 1])
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            merge_graph(titles, scores, packets)

    def test_conflicting_source_text_is_rejected(self):
        titles, scores, packets = inputs(set())
        packets['packets'][1]['instances'][0]['text'] += '!'
        with self.assertRaisesRegex(ValueError, 'conflicting text'):
            merge_graph(titles, scores, packets)

    def test_cli_creates_artifact_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in zip(('titles', 'scores', 'packets'), inputs({('A', 'B'), ('B', 'A')})):
                (root / f'{name}.json').write_text(json.dumps(value))
            command = [sys.executable, str(Path(__file__).with_name('true_graph_merge.py')),
                       str(root / 'titles.json'), str(root / 'scores.json'),
                       str(root / 'packets.json'), str(root / 'merged.json')]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            saved = json.loads((root / 'merged.json').read_text())
            self.assertEqual(saved['graph']['stats']['nodes'], 3)
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(json.loads((root / 'merged.json').read_text()), saved)


if __name__ == '__main__':
    unittest.main()
