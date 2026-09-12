import copy
import json
import unittest

from semantic_graph_patterns import construct


def fixture():
    # Synthetic sense names test the supplied-order contract, not WordNet facts.
    parents = {
        'thing.n.01': [],
        'material.n.01': ['thing.n.01'],
        'alpha.n.01': ['material.n.01', 'thing.n.01'],
        'beta.n.01': ['material.n.01', 'thing.n.01'],
        'activity.v.01': [],
        'specific.v.01': ['activity.v.01'],
    }
    lexicon = {sense: {'ancestors': [sense, *ancestors], 'definition': sense}
               for sense, ancestors in parents.items()}
    records = [{'row': 1, 'note': 'N1', 'subject': 'First source.'},
               {'row': 2, 'note': 'N2', 'subject': 'Second source.'},
               {'row': 3, 'note': 'N1', 'subject': 'Alias of first source.'}]
    graphs = []
    for row, target in [(1, 'alpha.n.01'), (2, 'beta.n.01'), (3, 'alpha.n.01')]:
        graphs.append({'row': row, 'nodes': [
            {'id': 10, 'sense': 'specific.v.01', 'context': 0},
            {'id': 20, 'sense': target, 'context': 1},
            {'id': 30, 'sense': 'disconnected.n.01', 'context': 0},
        ], 'edges': [{'source': 10, 'role': 'Theme', 'target': 20}]})
    return records, graphs, lexicon


def condition(result, name):
    return next(item for item in result['conditions'] if item['id'] == name)


def patterns(result, name):
    return {tuple(item['key']): item for item in condition(result, name)['patterns']}


class SemanticGraphPatternsTests(unittest.TestCase):
    def test_literal_patterns_keep_actual_edge_witnesses_and_distinct_notes(self):
        records, graphs, lexicon = fixture()
        result = construct(records, graphs, lexicon)
        literal = patterns(result, 'literal')
        edge = literal['specific.v.01', 'Theme', 'alpha.n.01']
        self.assertEqual(edge['kind'], 'role')
        self.assertEqual(edge['rows'], [1, 3])
        self.assertEqual(edge['notes'], ['N1'])
        self.assertEqual(edge['witnesses'], [
            {'row': row, 'note': 'N1', 'node_ids': [10, 20], 'contexts': [0, 1],
             'source_senses': ['specific.v.01', 'alpha.n.01'],
             'edge': {'source': 10, 'role': 'Theme', 'target': 20}}
            for row in [1, 3]
        ])
        singleton = literal['alpha.n.01',]
        self.assertEqual(singleton['witnesses'][0], {
            'row': 1, 'note': 'N1', 'node_ids': [20], 'contexts': [1],
            'source_senses': ['alpha.n.01'], 'edge': None})
        self.assertNotIn(('material.n.01',), literal)

    def test_generalization_preserves_both_participants_and_exact_role(self):
        records, graphs, lexicon = fixture()
        result = construct(records, graphs, lexicon)
        generalized = patterns(result, 'generalized')
        edge = generalized['specific.v.01', 'Theme', 'material.n.01']
        self.assertEqual(edge['notes'], ['N1', 'N2'])
        self.assertEqual(edge['rows'], [1, 2, 3])
        self.assertEqual(edge['witnesses'][1]['source_senses'],
                         ['specific.v.01', 'beta.n.01'])
        self.assertEqual(generalized['activity.v.01', 'Theme', 'thing.n.01']['notes'],
                         ['N1', 'N2'])
        self.assertNotIn(('specific.v.01', 'Theme', 'disconnected.n.01'), generalized)
        self.assertNotIn(('material.n.01', 'Theme', 'specific.v.01'), generalized)
        self.assertNotIn(('specific.v.01', 'Patient', 'material.n.01'), generalized)

    def test_sparse_links_preserve_intermediate_ancestors_and_endpoint_deletion(self):
        result = construct(*fixture())
        generalized = patterns(result, 'generalized')
        links = {(edge['parent'], edge['child']): edge['operations']
                 for edge in condition(result, 'generalized')['edges']}
        key = ('specific.v.01', 'Theme', 'alpha.n.01')
        child = generalized[key]['id']
        parent = generalized['specific.v.01', 'Theme', 'material.n.01']['id']
        self.assertEqual(links[parent, child], ['broaden_target'])
        self.assertNotIn((generalized['specific.v.01', 'Theme', 'thing.n.01']['id'], child),
                         links)
        self.assertEqual(links[generalized['specific.v.01',]['id'], child], ['drop_target'])
        self.assertEqual(links[generalized['alpha.n.01',]['id'], child], ['drop_source'])
        self.assertIn((generalized['material.n.01',]['id'], generalized['alpha.n.01',]['id']),
                      links)
        self.assertNotIn((generalized['thing.n.01',]['id'], generalized['alpha.n.01',]['id']),
                         links)
        literal = condition(result, 'literal')
        self.assertTrue(all(set(edge['operations']) <= {'drop_source', 'drop_target'}
                            for edge in literal['edges']))

    def test_equal_note_sets_do_not_merge_distinct_roles_or_count_aliases_twice(self):
        records, graphs, lexicon = fixture()
        for graph in graphs:
            graph['edges'].append({'source': 10, 'role': 'Material', 'target': 20})
        result = construct(records, graphs, lexicon)
        generalized = patterns(result, 'generalized')
        groups = condition(result, 'generalized')['recurring_groups']
        group = next(group for group in groups if group['notes'] == ['N1', 'N2'])
        for role in ['Theme', 'Material']:
            identifier = generalized['specific.v.01', role, 'material.n.01']['id']
            self.assertIn(identifier, group['pattern_ids'])
            self.assertIn(identifier, group['most_specific_pattern_ids'])
        broad = generalized['activity.v.01', 'Theme', 'thing.n.01']['id']
        self.assertIn(broad, group['pattern_ids'])
        self.assertNotIn(broad, group['most_specific_pattern_ids'])
        self.assertNotIn(generalized['alpha.n.01',]['id'],
                         [identifier for group in groups for identifier in group['pattern_ids']])

    def test_repeated_senses_keep_separate_nodes_and_only_observed_edges(self):
        records = [{'row': 7, 'note': 'N7'}]
        graphs = [{'row': 7, 'nodes': [
            {'id': 1, 'sense': 'unknown', 'context': 0},
            {'id': 2, 'sense': 'unknown', 'context': 1},
            {'id': 3, 'sense': 'unknown', 'context': 2}],
            'edges': [{'source': 1, 'role': 'R', 'target': 2},
                      {'source': 1, 'role': 'R', 'target': 2},
                      {'source': 3, 'role': 'R', 'target': 3}]}]
        result = construct(records, graphs, {})
        for name in ['literal', 'generalized']:
            items = patterns(result, name)
            self.assertEqual(len(items['unknown',]['witnesses']), 3)
            self.assertEqual([w['node_ids'] for w in items['unknown', 'R', 'unknown']['witnesses']],
                             [[1, 2], [3, 3]])
            link = condition(result, name)['edges'][0]
            self.assertEqual(link['operations'], ['drop_source', 'drop_target'])

    def test_determinism_cross_condition_ids_and_no_input_mutation(self):
        args = fixture()
        original = copy.deepcopy(args)
        result = construct(*args)
        self.assertEqual(args, original)
        records, graphs, lexicon = copy.deepcopy(args)
        records.reverse()
        graphs.reverse()
        for graph in graphs:
            graph['nodes'].reverse()
            graph['edges'].reverse()
        for entry in lexicon.values():
            entry['ancestors'].reverse()
        self.assertEqual(json.dumps(result), json.dumps(construct(records, graphs, lexicon)))
        literal = patterns(result, 'literal')
        generalized = patterns(result, 'generalized')
        for key, pattern in literal.items():
            self.assertEqual(pattern['id'], generalized[key]['id'])

    def test_row_and_endpoint_validation(self):
        mutations = [
            lambda r, g, l: g.pop(),
            lambda r, g, l: g.append(copy.deepcopy(g[0])),
            lambda r, g, l: r.append(copy.deepcopy(r[0])),
            lambda r, g, l: g[0].update(row=999),
            lambda r, g, l: g[0]['nodes'].append(copy.deepcopy(g[0]['nodes'][0])),
            lambda r, g, l: g[0]['edges'][0].update(target=999),
            lambda r, g, l: g[0]['edges'][0].update(role=''),
            lambda r, g, l: g[0]['nodes'][0].update(sense=''),
            lambda r, g, l: g[0]['nodes'][0].update(context=True),
            lambda r, g, l: g[0]['nodes'][0].update(id=True),
            lambda r, g, l: r[0].update(note=''),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                args = fixture()
                mutation(*args)
                with self.assertRaises(ValueError):
                    construct(*args)

    def test_invalid_ancestor_orders_are_rejected(self):
        for ancestors in [[], ['activity.v.01'], ['specific.v.01', 42]]:
            with self.subTest(ancestors=ancestors):
                records, graphs, lexicon = fixture()
                lexicon['specific.v.01']['ancestors'] = ancestors
                with self.assertRaises(ValueError):
                    construct(records, graphs, lexicon)
        records, graphs, lexicon = fixture()
        lexicon['activity.v.01']['ancestors'].append('specific.v.01')
        with self.assertRaises(ValueError):
            construct(records, graphs, lexicon)

    def test_empty_valid_graph_is_not_given_invented_patterns(self):
        result = construct([{'row': 0, 'note': 'N0'}],
                           [{'row': 0, 'nodes': [], 'edges': []}], {})
        for name in ['literal', 'generalized']:
            self.assertEqual(condition(result, name)['patterns'], [])
            self.assertEqual(condition(result, name)['edges'], [])
            self.assertEqual(condition(result, name)['recurring_groups'], [])

    def test_explicit_null_lexicon_entry_is_rejected(self):
        records = [{'row': 0, 'note': 'N0'}]
        graphs = [{'row': 0, 'nodes': [
            {'id': 0, 'sense': 'unknown', 'context': 0}], 'edges': []}]
        with self.assertRaisesRegex(ValueError, 'lexicon unknown requires an ancestors list'):
            construct(records, graphs, {'unknown': None})


if __name__ == '__main__':
    unittest.main()
