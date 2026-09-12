import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from structural_phrase_generalization import PhraseMatcher, run


def phrase(root, *words):
    return [root, [list(word) for word in words]]


def lexicon():
    # Synthetic dictionary relationships test the matching contract, not meanings.
    parents = {
        'broad.n.01': [],
        'middle.n.01': ['broad.n.01'],
        'narrow.n.01': ['middle.n.01'],
        'other.n.01': ['broad.n.01'],
        'peer.n.01': ['broad.n.01'],
    }
    return {
        'queries': {word: [word + '.n.01']
                    for word in ('broad', 'narrow', 'other', 'peer')},
        'senses': {name: dict(definition=name, lemmas=[name.split('.')[0]],
                              examples=[], pos='n', hypernyms=ancestors)
                   for name, ancestors in parents.items()},
        'source': {},
    }


def node(identifier, key, rows):
    return dict(id=identifier, key=key, label=' '.join(w[0] for w in key[1]),
                rows=rows, notes=sorted({'N' + str(row) for row in rows}))


def source_fixture():
    return dict(nodes=[
        node('P', phrase(0, ('broad', 'NOUN', -1, 'root')), [0, 2]),
        node('C', phrase(0, ('narrow', 'NOUN', -1, 'root')), [1]),
        node('X', phrase(0, ('activity', 'NOUN', -1, 'root')), [2]),
        node('M', phrase(1, ('broad', 'NOUN', 1, 'compound'),
                         ('activity', 'NOUN', -1, 'root')), [2]),
        node('U', phrase(0, ('unknown', 'NOUN', -1, 'root')), [3]),
    ], edges=[dict(parent='X', child='M', witnesses=[dict(
        row=2, note='N2', sentence=0, head=2, parent_word_ids=[2], child_word_ids=[1, 2])])])


class PhraseMatcherTests(unittest.TestCase):
    def test_literal_identity_matches_without_dictionary_entries(self):
        matcher = PhraseMatcher({'queries': {}, 'senses': {}, 'source': {}})
        key = phrase(0, ('unknown', 'NOUN', -1, 'root'))
        result = matcher.match(key, key, structure=True, lexical=False)
        self.assertIsNotNone(result)
        self.assertEqual(result['mapping'], [[0, 0]])

    def test_noun_hypernyms_are_directed_and_optional(self):
        matcher = PhraseMatcher(lexicon())
        broad = phrase(0, ('broad', 'NOUN', -1, 'root'))
        narrow = phrase(0, ('narrow', 'NOUN', -1, 'root'))
        peer = phrase(0, ('peer', 'NOUN', -1, 'root'))
        for structure in (False, True):
            with self.subTest(structure=structure):
                result = matcher.match(broad, narrow, structure=structure, lexical=True)
                self.assertEqual(result['mapping'], [[0, 0]])
                self.assertIsNone(matcher.match(broad, narrow, structure=structure, lexical=False))
                self.assertIsNone(matcher.match(narrow, broad, structure=structure, lexical=True))
                self.assertIsNone(matcher.match(narrow, peer, structure=structure, lexical=True))

    def test_same_head_allows_generalized_modifiers_and_extra_child_words(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(1, ('broad', 'NOUN', 1, 'compound'),
                        ('activity', 'NOUN', -1, 'root'))
        child = phrase(2, ('narrow', 'NOUN', 2, 'compound'),
                       ('extra', 'ADJ', 2, 'amod'), ('activity', 'NOUN', -1, 'root'))
        self.assertIsNone(matcher.match(parent, child, structure=True, lexical=False))
        self.assertEqual(matcher.match(parent, child)['mapping'], [[0, 0], [1, 2]])

    def test_only_word_matching_can_map_the_parent_head_to_a_modifier(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(0, ('modifier', 'NOUN', -1, 'root'))
        child = phrase(1, ('modifier', 'NOUN', 1, 'compound'),
                       ('head', 'NOUN', -1, 'root'))
        self.assertEqual(matcher.match(parent, child, structure=False)['mapping'], [[0, 0]])
        self.assertIsNone(matcher.match(parent, child, structure=True))

    def test_structure_requires_exact_labels_and_direct_mapped_heads(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(1, ('modifier', 'NOUN', 1, 'nmod'),
                        ('head', 'NOUN', -1, 'root'))
        children = [
            phrase(1, ('modifier', 'NOUN', 1, 'compound'), ('head', 'NOUN', -1, 'root')),
            phrase(1, ('modifier', 'NOUN', 1, 'nmod:poss'), ('head', 'NOUN', -1, 'root')),
            phrase(2, ('modifier', 'NOUN', 1, 'nmod'), ('bridge', 'NOUN', 2, 'nmod'),
                   ('head', 'NOUN', -1, 'root')),
        ]
        for child in children:
            with self.subTest(child=child):
                self.assertIsNotNone(matcher.match(parent, child, structure=False, lexical=False))
                self.assertIsNone(matcher.match(parent, child, structure=True, lexical=False))

    def test_structure_preserves_connections_not_surface_order(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(1, ('modifier', 'NOUN', 1, 'compound'),
                        ('head', 'NOUN', -1, 'root'))
        child = phrase(0, ('head', 'NOUN', -1, 'root'),
                       ('modifier', 'NOUN', 0, 'compound'))
        for structure in (False, True):
            self.assertEqual(matcher.match(parent, child, structure=structure,
                                           lexical=False)['mapping'], [[0, 1], [1, 0]])

    def test_both_modes_require_injective_word_mappings(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(2, ('repeat', 'NOUN', 2, 'compound'),
                        ('repeat', 'NOUN', 2, 'compound'), ('head', 'NOUN', -1, 'root'))
        child = phrase(2, ('repeat', 'NOUN', 2, 'compound'),
                       ('different', 'NOUN', 2, 'compound'), ('head', 'NOUN', -1, 'root'))
        for structure in (False, True):
            for lexical in (False, True):
                with self.subTest(structure=structure, lexical=lexical):
                    self.assertIsNone(matcher.match(parent, child, structure=structure,
                                                    lexical=lexical))
                    self.assertEqual(matcher.match(parent, parent, structure=structure,
                                                   lexical=lexical)['mapping'],
                                     [[0, 0], [1, 1], [2, 2]])

    def test_mapping_search_backtracks_after_an_injective_dead_end(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(2, ('broad', 'NOUN', 2, 'compound'),
                        ('narrow', 'NOUN', 2, 'compound'), ('head', 'NOUN', -1, 'root'))
        child = phrase(2, ('narrow', 'NOUN', 2, 'compound'),
                       ('other', 'NOUN', 2, 'compound'), ('head', 'NOUN', -1, 'root'))
        # broad can use either child modifier; narrow can only use index zero.
        for structure in (False, True):
            self.assertEqual(matcher.match(parent, child, structure=structure)['mapping'],
                             [[0, 1], [1, 0], [2, 2]])

    def test_unknown_words_require_identical_lemmas_even_with_lexical_matching(self):
        matcher = PhraseMatcher(lexicon())
        first = phrase(0, ('unknown', 'NOUN', -1, 'root'))
        second = phrase(0, ('different_unknown', 'NOUN', -1, 'root'))
        for structure in (False, True):
            self.assertIsNotNone(matcher.match(first, first, structure=structure))
            self.assertIsNone(matcher.match(first, second, structure=structure))

    def test_pos_is_exact_and_non_nouns_cannot_broaden_lexically(self):
        matcher = PhraseMatcher(lexicon())
        for structure in (False, True):
            for pos in ('ADJ', 'VERB', 'ADP', 'DET'):
                with self.subTest(structure=structure, pos=pos):
                    parent = phrase(0, ('broad', pos, -1, 'root'))
                    child = phrase(0, ('narrow', pos, -1, 'root'))
                    self.assertIsNone(matcher.match(parent, child, structure=structure))
                    self.assertIsNotNone(matcher.match(parent, parent, structure=structure))
                    noun = phrase(0, ('broad', 'NOUN', -1, 'root'))
                    self.assertIsNone(matcher.match(noun, parent, structure=structure))

    def test_all_compatible_noun_senses_and_dictionary_paths_are_retained(self):
        data = lexicon()
        for name, parents in [('broad.n.02', []), ('narrow.n.02', ['broad.n.02']),
                              ('shared.n.01', [])]:
            data['senses'][name] = dict(definition=name, lemmas=[], examples=[],
                                       pos='n', hypernyms=parents)
        data['queries']['broad'] = ['shared.n.01', 'broad.n.02', 'broad.n.01']
        data['queries']['narrow'] = ['narrow.n.02', 'narrow.n.01', 'shared.n.01']
        matcher = PhraseMatcher(data)
        parent = phrase(0, ('broad', 'NOUN', -1, 'root'))
        child = phrase(0, ('narrow', 'NOUN', -1, 'root'))
        result = matcher.match(parent, child)
        self.assertEqual(result['mapping'], [[0, 0]])
        self.assertEqual(len(result['lexical_witnesses']), 1)
        witness = result['lexical_witnesses'][0]
        self.assertEqual((witness['parent_index'], witness['child_index']), (0, 0))
        self.assertEqual(len(witness['relations']), 3)
        self.assertEqual({(r['parent_sense'], r['child_sense'], tuple(r['path']))
                          for r in witness['relations']}, {
            ('broad.n.01', 'narrow.n.01', ('narrow.n.01', 'middle.n.01', 'broad.n.01')),
            ('broad.n.02', 'narrow.n.02', ('narrow.n.02', 'broad.n.02')),
            ('shared.n.01', 'shared.n.01', ('shared.n.01',)),
        })
        for relation in witness['relations']:
            self.assertIsInstance(relation['kind'], str)
            self.assertTrue(relation['kind'])

    def test_first_complete_mapping_is_lexicographically_deterministic(self):
        parent = phrase(1, ('broad', 'NOUN', 1, 'compound'),
                        ('head', 'NOUN', -1, 'root'))
        child = phrase(2, ('other', 'NOUN', 2, 'compound'),
                       ('narrow', 'NOUN', 2, 'compound'), ('head', 'NOUN', -1, 'root'))
        data = lexicon()
        reversed_data = copy.deepcopy(data)
        reversed_data['queries'] = dict(reversed(list(data['queries'].items())))
        reversed_data['senses'] = dict(reversed(list(data['senses'].items())))
        for structure in (False, True):
            matcher = PhraseMatcher(data)
            expected = matcher.match(parent, child, structure=structure)
            self.assertEqual(expected['mapping'], [[0, 0], [1, 2]])
            self.assertEqual(matcher.match(parent, child, structure=structure), expected)
            self.assertEqual(PhraseMatcher(reversed_data).match(parent, child,
                                                               structure=structure), expected)

    def test_matching_does_not_modify_the_lexicon_or_phrase_keys(self):
        data = lexicon()
        parent = phrase(1, ('broad', 'NOUN', 1, 'compound'),
                        ('head', 'NOUN', -1, 'root'))
        child = phrase(1, ('narrow', 'NOUN', 1, 'compound'),
                       ('head', 'NOUN', -1, 'root'))
        before = copy.deepcopy((data, parent, child))
        matcher = PhraseMatcher(data)
        for structure in (False, True):
            for lexical in (False, True):
                matcher.match(parent, child, structure=structure, lexical=lexical)
                matcher.match(child, parent, structure=structure, lexical=lexical)
        self.assertEqual((data, parent, child), before)

    def test_structural_mapping_uses_parent_index_order_not_tree_traversal_order(self):
        matcher = PhraseMatcher(lexicon())
        parent = phrase(3, ('leaf', 'NOUN', 2, 'compound'),
                        ('sibling', 'NOUN', 3, 'compound'),
                        ('branch', 'NOUN', 3, 'compound'), ('head', 'NOUN', -1, 'root'))
        child = phrase(5, ('leaf', 'NOUN', 3, 'compound'),
                       ('leaf', 'NOUN', 2, 'compound'),
                       ('branch', 'NOUN', 5, 'compound'),
                       ('branch', 'NOUN', 5, 'compound'),
                       ('sibling', 'NOUN', 5, 'compound'), ('head', 'NOUN', -1, 'root'))
        # Both branch mappings work; parent index zero decides which is first.
        self.assertEqual(matcher.match(parent, child, structure=True, lexical=False)['mapping'],
                         [[0, 0], [1, 4], [2, 3], [3, 5]])


class PhraseGeneralizationIntegrationTests(unittest.TestCase):
    def test_reciprocal_pairs_are_sorted_and_identical_across_hash_seeds(self):
        nodes = [node(identifier, phrase(0, (identifier, 'NOUN', -1, 'root')), [row])
                 for row, identifier in enumerate(('A', 'B', 'C'))]
        edges = [dict(parent=parent, child=child) for parent in ('A', 'B', 'C')
                 for child in ('A', 'B', 'C') if parent != child]
        program = (
            'import json, sys\n'
            'from structural_phrase_generalization import membership_summary\n'
            'source = json.load(sys.stdin)\n'
            'print(json.dumps(membership_summary(source["nodes"], source["edges"])))\n'
        )
        serialized = []
        for seed in ('0', '1'):
            completed = subprocess.run(
                [sys.executable, '-c', program], cwd=Path(__file__).parent,
                env={**os.environ, 'PYTHONHASHSEED': seed, 'PYTHONDONTWRITEBYTECODE': '1'},
                input=json.dumps(dict(nodes=nodes, edges=edges)),
                capture_output=True, text=True, check=True)
            serialized.append(completed.stdout)
            summary = json.loads(completed.stdout)
            with self.subTest(hash_seed=seed):
                self.assertEqual(summary['reciprocal_pairs'], [['A', 'B'], ['A', 'C'], ['B', 'C']])
                self.assertEqual(summary['cyclic_components'], [['A', 'B', 'C']])
        self.assertEqual(serialized[0], serialized[1])

    def test_run_compares_all_four_conditions_and_preserves_source_nodes(self):
        source, data = source_fixture(), lexicon()
        before = copy.deepcopy((source, data))
        result = run(source, data)
        self.assertEqual((source, data), before)
        self.assertEqual(result['source_nodes'], before[0]['nodes'])
        self.assertEqual(result['source_edges'], before[0]['edges'])
        conditions = {condition['id']: condition for condition in result['conditions']}
        expected = {
            'words_literal': {('P', 'M'), ('X', 'M')},
            'structure_literal': {('X', 'M')},
            'words_lexical': {('P', 'C'), ('P', 'M'), ('X', 'M')},
            'structure_lexical': {('P', 'C'), ('X', 'M')},
        }
        self.assertEqual(set(conditions), set(expected))
        for name, edges in expected.items():
            with self.subTest(condition=name):
                condition = conditions[name]
                self.assertEqual({(e['parent'], e['child']) for e in condition['edges']}, edges)
                self.assertTrue(all(e['parent'] != e['child'] for e in condition['edges']))
                self.assertTrue(all('mapping' in e and 'lexical_witnesses' in e
                                    for e in condition['edges']))
                summaries = {n['id']: n for n in condition['memberships']['nodes']}
                self.assertEqual(set(summaries), {'P', 'C', 'X', 'M', 'U'})
                self.assertEqual(summaries['U']['direct_children'], [])
                self.assertEqual(summaries['U']['reachable'], [])
                self.assertEqual(summaries['U']['direct_rows'], [3])
                self.assertEqual(summaries['U']['reachable_notes'], ['N3'])
        summaries = {n['id']: n for n in conditions['words_literal']['memberships']['nodes']}
        self.assertEqual(summaries['P']['direct_rows'], [0, 2])
        self.assertEqual(summaries['P']['direct_notes'], ['N0', 'N2'])

    def test_run_retains_cycles_and_separates_graph_only_memberships(self):
        data = dict(queries={'alpha': ['left.n.01'], 'bridge': ['left.n.01', 'right.n.01'],
                             'omega': ['right.n.01']},
                    senses={name: dict(definition=name, lemmas=[], examples=[], pos='n',
                                       hypernyms=[]) for name in ('left.n.01', 'right.n.01')},
                    source={})
        source = dict(nodes=[node(identifier, phrase(0, (word, 'NOUN', -1, 'root')), [row])
                             for identifier, word, row in
                             [('A', 'alpha', 0), ('B', 'bridge', 1), ('C', 'omega', 2)]],
                      edges=[])
        result = run(source, data)
        for condition in result['conditions']:
            with self.subTest(condition=condition['id']):
                summary = condition['memberships']
                if condition['id'].endswith('_literal'):
                    self.assertEqual(condition['edges'], [])
                    self.assertEqual(summary['cyclic_components'], [])
                    continue
                self.assertEqual({(e['parent'], e['child']) for e in condition['edges']},
                                 {('A', 'B'), ('B', 'A'), ('B', 'C'), ('C', 'B')})
                self.assertEqual(summary['reciprocal_pairs'], [['A', 'B'], ['B', 'C']])
                self.assertEqual(summary['cyclic_components'], [['A', 'B', 'C']])
                a = next(n for n in summary['nodes'] if n['id'] == 'A')
                self.assertEqual(a['direct_children'], ['B'])
                self.assertEqual(a['reachable'], ['B', 'C'])
                self.assertEqual(a['direct_rows'], [0, 1])
                self.assertEqual(a['direct_notes'], ['N0', 'N1'])
                self.assertEqual(a['graph_only_rows'], [2])
                self.assertEqual(a['graph_only_notes'], ['N2'])
                self.assertEqual(a['reachable_notes'], ['N0', 'N1', 'N2'])

    def test_cli_replays_exact_artifacts_and_refuses_to_overwrite(self):
        script = Path(__file__).with_name('structural_phrase_generalization.py')
        source, data = source_fixture(), lexicon()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path, lexicon_path = root / 'input.json', root / 'lexicon.json'
            input_path.write_text(json.dumps(source))
            lexicon_path.write_text(json.dumps(data))
            command = [sys.executable, str(script), '--input', str(input_path),
                       '--lexicon', str(lexicon_path), '--output']
            outputs = [root / 'first', root / 'replay']
            for output in outputs:
                subprocess.run(command + [str(output)], check=True, capture_output=True, text=True)
            self.assertEqual(json.loads((outputs[0] / 'result.json').read_text()), run(source, data))
            self.assertEqual(json.loads((outputs[0] / 'lexicon.json').read_text()), data)
            for name in ('result.json', 'lexicon.json', script.name):
                self.assertEqual((outputs[0] / name).read_bytes(), (outputs[1] / name).read_bytes())
            self.assertEqual((outputs[0] / script.name).read_bytes(), script.read_bytes())
            configs = [json.loads((output / 'config.json').read_text()) for output in outputs]
            for config in configs:
                self.assertEqual(config['input_sha256'], hashlib.sha256(input_path.read_bytes()).hexdigest())
                self.assertEqual(config['code_sha256'], hashlib.sha256(script.read_bytes()).hexdigest())
                dependency = script.with_name('mask_group_lexical_relations.py')
                self.assertEqual(config['lexical_code_sha256'],
                                 hashlib.sha256(dependency.read_bytes()).hexdigest())
                # Recorded runtime measurements are not deterministic replay artifacts.
                config.pop('elapsed_seconds')
                config.pop('peak_rss_kib')
            self.assertEqual(configs[0], configs[1])
            before = {p.name: p.read_bytes() for p in outputs[0].iterdir()}
            repeated = subprocess.run(command + [str(outputs[0])], capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn('output exists', repeated.stderr)
            self.assertEqual({p.name: p.read_bytes() for p in outputs[0].iterdir()}, before)
            self.assertEqual(json.loads(input_path.read_text()), source)
            self.assertEqual(json.loads(lexicon_path.read_text()), data)


if __name__ == '__main__':
    unittest.main()
