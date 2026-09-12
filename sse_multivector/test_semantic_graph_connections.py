import copy
import json
from pathlib import Path
import unittest

from semantic_graph_patterns import construct


def fixture():
    # Synthetic labels exercise the supplied order, not linguistic judgments.
    lexicon = {
        'alpha': {'ancestors': ['alpha', 'material', 'thing']},
        'beta': {'ancestors': ['beta', 'material', 'thing']},
        'material': {'ancestors': ['material', 'thing']},
        'thing': {'ancestors': ['thing']},
        'event': {'ancestors': ['event', 'activity']},
        'activity': {'ancestors': ['activity']},
    }
    records = [{'row': 1, 'note': 'N1'}, {'row': 2, 'note': 'N2'},
               {'row': 3, 'note': 'N1'}]
    graphs = []
    for row, sense, edge in [
            (1, 'alpha', {'source': 10, 'role': 'Theme', 'target': 20}),
            (2, 'beta', {'source': 20, 'role': 'MadeOf', 'target': 10}),
            (3, 'alpha', {'source': 10, 'role': 'Patient', 'target': 20})]:
        graphs.append({'row': row, 'nodes': [
            {'id': 10, 'sense': 'event', 'context': 0},
            {'id': 20, 'sense': sense, 'context': 1},
            {'id': 30, 'sense': 'unconnected', 'context': 2},
        ], 'edges': [edge]})
    return records, graphs, lexicon


def condition(result, name):
    return next(item for item in result['conditions'] if item['id'] == name)


def patterns(result, name):
    return {(item['kind'], *item['key']): item
            for item in condition(result, name)['patterns']}


class SemanticGraphConnectionsTests(unittest.TestCase):
    def test_connection_identity_forgets_role_and_direction_only(self):
        result = construct(*fixture(), relation_policy='connection')
        literal = patterns(result, 'literal')
        self.assertEqual(set(literal), {
            ('singleton', sense)
            for sense in ['alpha', 'beta', 'event', 'unconnected']
        } | {('connection', 'alpha', 'event'), ('connection', 'beta', 'event')})
        pair = literal['connection', 'alpha', 'event']
        self.assertEqual(pair['rows'], [1, 3])
        self.assertEqual(pair['notes'], ['N1'])
        self.assertEqual([w['edge']['role'] for w in pair['witnesses']],
                         ['Theme', 'Patient'])
        generalized = patterns(result, 'generalized')
        shared = generalized['connection', 'event', 'material']
        self.assertEqual(shared['rows'], [1, 2, 3])
        self.assertEqual(shared['notes'], ['N1', 'N2'])
        self.assertEqual(shared['witnesses'][1], {
            'row': 2, 'note': 'N2', 'node_ids': [20, 10],
            'contexts': [1, 0], 'source_senses': ['beta', 'event'],
            'edge': {'source': 20, 'role': 'MadeOf', 'target': 10}})

    def test_duplicate_pairs_keep_each_distinct_native_edge_once(self):
        records = [{'row': 4, 'note': 'N4'}]
        graphs = [{'row': 4, 'nodes': [
            {'id': 1, 'sense': 'alpha', 'context': 0},
            {'id': 2, 'sense': 'beta', 'context': 1},
        ], 'edges': [
            {'source': 1, 'role': 'R', 'target': 2},
            {'source': 1, 'role': 'R', 'target': 2},
            {'source': 2, 'role': 'R', 'target': 1},
            {'source': 1, 'role': 'S', 'target': 2},
        ]}]
        result = construct(records, graphs, fixture()[2], relation_policy='connection')
        expected = [(1, 'R', 2), (1, 'S', 2), (2, 'R', 1)]
        for name, key in [('literal', ('alpha', 'beta')),
                          ('generalized', ('material', 'thing'))]:
            with self.subTest(name=name):
                pair = patterns(result, name)['connection', *key]
                self.assertEqual([(w['edge']['source'], w['edge']['role'], w['edge']['target'])
                                  for w in pair['witnesses']], expected)
                self.assertEqual(pair['rows'], [4])
                self.assertEqual(pair['notes'], ['N4'])
        # Two ancestor assignment routes produce material--thing; neither is a
        # new occurrence. Equal endpoint senses still occupy two key positions.
        broad = patterns(result, 'generalized')['connection', 'thing', 'thing']
        self.assertEqual(len(broad['witnesses']), 3)

    def test_repeated_sense_nodes_and_native_self_edge_retain_identity(self):
        records = [{'row': 4, 'note': 'N4'}]
        graphs = [{'row': 4, 'nodes': [
            {'id': 1, 'sense': 'unknown', 'context': 0},
            {'id': 2, 'sense': 'unknown', 'context': 1},
            {'id': 3, 'sense': 'unknown', 'context': 2},
        ], 'edges': [{'source': 1, 'role': 'R', 'target': 2},
                     {'source': 3, 'role': 'R', 'target': 3}]}]
        result = construct(records, graphs, {}, relation_policy='connection')
        for name in ['literal', 'generalized']:
            items = patterns(result, name)
            self.assertEqual(set(items), {('singleton', 'unknown'),
                                          ('connection', 'unknown', 'unknown')})
            self.assertEqual([w['node_ids'] for w in
                              items['connection', 'unknown', 'unknown']['witnesses']],
                             [[1, 2], [3, 3]])
            self.assertEqual(len(condition(result, name)['edges']), 1)
            self.assertEqual(condition(result, name)['edges'][0]['operations'],
                             ['drop_endpoint'])

    def test_no_cooccurrence_transitive_or_cross_row_pair_is_invented(self):
        records = [{'row': 1, 'note': 'N1'}, {'row': 2, 'note': 'N1'}]
        graphs = [{'row': 1, 'nodes': [
            {'id': index, 'sense': sense, 'context': index}
            for index, sense in enumerate(['a', 'b', 'c', 'd'])
        ], 'edges': [{'source': 0, 'role': 'R', 'target': 1},
                     {'source': 1, 'role': 'R', 'target': 2}]},
                  {'row': 2, 'nodes': [
                      {'id': 0, 'sense': 'e', 'context': 0},
                      {'id': 1, 'sense': 'f', 'context': 0}], 'edges': []}]
        result = construct(records, graphs, {}, relation_policy='connection')
        for name in ['literal', 'generalized']:
            self.assertEqual({key for key in patterns(result, name)
                              if key[0] == 'connection'},
                             {('connection', 'a', 'b'), ('connection', 'b', 'c')})

    def test_complete_links_use_only_immediate_coordinate_broadening_and_deletion(self):
        records, graphs, lexicon = fixture()
        result = construct(records[:1], graphs[:1], lexicon,
                           relation_policy='connection')
        generalized = patterns(result, 'generalized')
        by_id = {p['id']: key for key, p in generalized.items()}
        actual = {(by_id[e['parent']], by_id[e['child']], tuple(e['operations']))
                  for e in condition(result, 'generalized')['edges']}
        expected = {
            (('singleton', 'activity'), ('singleton', 'event'), ('broaden_singleton',)),
            (('singleton', 'material'), ('singleton', 'alpha'), ('broaden_singleton',)),
            (('singleton', 'thing'), ('singleton', 'material'), ('broaden_singleton',)),
        }
        for activity in ['activity', 'event']:
            for material in ['alpha', 'material', 'thing']:
                key = ('connection', *sorted([activity, material]))
                for endpoint in [activity, material]:
                    expected.add((('singleton', endpoint), key, ('drop_endpoint',)))
                if activity == 'event':
                    expected.add((('connection', *sorted(['activity', material])),
                                  key, ('broaden_endpoint',)))
                if material != 'thing':
                    broader = {'alpha': 'material', 'material': 'thing'}[material]
                    expected.add((('connection', *sorted([activity, broader])),
                                  key, ('broaden_endpoint',)))
        self.assertEqual(actual, expected)
        self.assertEqual(len(generalized), 12)  # Six singletons and six pairs.

    def test_support_containment_acyclicity_and_recurring_groups_keep_aliases(self):
        result = construct(*fixture(), relation_policy='connection')
        for current in result['conditions']:
            by_id = {p['id']: p for p in current['patterns']}
            children = {identifier: set() for identifier in by_id}
            indegrees = dict.fromkeys(by_id, 0)
            for edge in current['edges']:
                parent, child = edge['parent'], edge['child']
                self.assertNotEqual(parent, child)
                self.assertLessEqual(set(by_id[child]['rows']), set(by_id[parent]['rows']))
                self.assertLessEqual(set(by_id[child]['notes']), set(by_id[parent]['notes']))
                children[parent].add(child)
                indegrees[child] += 1
            ready = [identifier for identifier, degree in indegrees.items() if degree == 0]
            visited = 0
            while ready:
                visited += 1
                for child in children[ready.pop()]:
                    indegrees[child] -= 1
                    if indegrees[child] == 0:
                        ready.append(child)
            self.assertEqual(visited, len(by_id))
            grouped = {tuple(g['notes']): g for g in current['recurring_groups']}
            expected = {}
            for pattern in by_id.values():
                if len(pattern['notes']) >= 2:
                    expected.setdefault(tuple(pattern['notes']), set()).add(pattern['id'])
            self.assertEqual(set(grouped), set(expected))
            for notes, identifiers in expected.items():
                self.assertEqual(set(grouped[notes]['pattern_ids']), identifiers)
                broader = {e['parent'] for e in current['edges']
                           if e['parent'] in identifiers and e['child'] in identifiers}
                self.assertEqual(set(grouped[notes]['most_specific_pattern_ids']),
                                 identifiers - broader)

    def test_singletons_are_unchanged_and_native_witnesses_are_traceable(self):
        args = fixture()
        exact = construct(*args)
        connected = construct(*args, relation_policy='connection')
        graphs = {g['row']: g for g in args[1]}
        for name in ['literal', 'generalized']:
            self.assertEqual([p for p in condition(exact, name)['patterns']
                              if p['kind'] == 'singleton'],
                             [p for p in condition(connected, name)['patterns']
                              if p['kind'] == 'singleton'])
            for pair in condition(connected, name)['patterns']:
                if pair['kind'] != 'connection':
                    continue
                self.assertEqual(pair['key'], sorted(pair['key']))
                for witness in pair['witnesses']:
                    graph = graphs[witness['row']]
                    self.assertIn(witness['edge'], graph['edges'])
                    nodes = {n['id']: n for n in graph['nodes']}
                    self.assertEqual(witness['node_ids'],
                                     [witness['edge']['source'], witness['edge']['target']])
                    self.assertEqual(witness['contexts'],
                                     [nodes[i]['context'] for i in witness['node_ids']])
                    self.assertEqual(witness['source_senses'],
                                     [nodes[i]['sense'] for i in witness['node_ids']])

    def test_canonical_order_flip_keeps_both_generalization_routes(self):
        records = [{'row': row, 'note': f'N{row}'} for row in [1, 2]]
        graphs = [{'row': row, 'nodes': [
            {'id': 0, 'sense': 'a', 'context': 0},
            {'id': 1, 'sense': 'm', 'context': 0}],
            'edges': [{'source': 0, 'role': 'R', 'target': 1}]} for row in [1, 2]]
        lexicon = {sense: {'ancestors': [sense, 'z']} for sense in ['a', 'm']}
        lexicon['z'] = {'ancestors': ['z']}
        result = construct(records, graphs, lexicon, relation_policy='connection')
        items = patterns(result, 'generalized')
        by_id = {p['id']: key for key, p in items.items()}
        pair_links = {(by_id[e['parent']][1:], by_id[e['child']][1:])
                      for e in condition(result, 'generalized')['edges']
                      if by_id[e['parent']][0] == 'connection'}
        self.assertEqual(pair_links, {
            (('a', 'z'), ('a', 'm')), (('m', 'z'), ('a', 'm')),
            (('z', 'z'), ('a', 'z')), (('z', 'z'), ('m', 'z')),
        })
        self.assertEqual({key[1:] for key in items if key[0] == 'connection'},
                         {('a', 'm'), ('a', 'z'), ('m', 'z'), ('z', 'z')})
        groups = condition(result, 'generalized')['recurring_groups']
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['most_specific_pattern_ids'],
                         [items['connection', 'a', 'm']['id']])
        self.assertTrue(all(p['notes'] == ['N1', 'N2'] for p in items.values()))

    def test_deterministic_without_input_mutation_and_ids_survive_generalization(self):
        args = fixture()
        original = copy.deepcopy(args)
        result = construct(*args, relation_policy='connection')
        self.assertEqual(args, original)
        records, graphs, lexicon = copy.deepcopy(args)
        records.reverse()
        graphs.reverse()
        for graph in graphs:
            graph['nodes'].reverse()
            graph['edges'].reverse()
        for entry in lexicon.values():
            entry['ancestors'].reverse()
        self.assertEqual(json.dumps(result), json.dumps(construct(
            records, graphs, lexicon, relation_policy='connection')))
        generalized = patterns(result, 'generalized')
        for key, pattern in patterns(result, 'literal').items():
            self.assertEqual(pattern['id'], generalized[key]['id'])

    def test_empty_graph_has_no_connection_and_invalid_policy_is_rejected(self):
        records = [{'row': 0, 'note': 'N0'}]
        graphs = [{'row': 0, 'nodes': [], 'edges': []}]
        result = construct(records, graphs, {}, relation_policy='connection')
        for current in result['conditions']:
            self.assertEqual(current['patterns'], [])
            self.assertEqual(current['edges'], [])
            self.assertEqual(current['recurring_groups'], [])
        for policy in [None, '', 'roles', 'Connection', True, [], {}]:
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(ValueError, 'relation_policy'):
                    construct(records, graphs, {}, relation_policy=policy)

    def test_exact_default_and_explicit_exact_replay_saved_sgc01_bytes(self):
        saved = Path(__file__).parent / 'navigation-research-v1' / 'SGC01' / 'construction'
        graphs = json.loads((saved / 'graphs.json').read_bytes())
        rows = {g['row'] for g in graphs}
        records = [r for r in json.loads((saved / 'inputs.json').read_bytes()) if r['row'] in rows]
        lexicon = json.loads((saved / 'lexicon.json').read_bytes())['senses']
        saved_bytes = (saved / 'result.json').read_bytes()
        saved_result = json.loads(saved_bytes)
        for options in [{}, {'relation_policy': 'exact'}]:
            with self.subTest(options=options):
                result = construct(records, graphs, lexicon, **options)
                result['run_id'] = saved_result['run_id']
                result['excluded_rows'] = saved_result['excluded_rows']
                replay = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
                          + '\n').encode('utf-8')
                self.assertEqual(replay, saved_bytes)


if __name__ == '__main__':
    unittest.main()
