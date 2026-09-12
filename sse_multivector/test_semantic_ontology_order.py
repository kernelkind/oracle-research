import copy
import unittest

from semantic_graph_patterns import construct
from semantic_ontology_order import augment, parse_mappings, parse_ontology


def mapping_line(offset, pos, tail):
    return f'{offset:08d} 00 {pos} 01 synthetic 0 000 | synthetic gloss {tail}'


def fixture():
    lexicon = {
        'alpha.n.01': {'ancestors': ['alpha.n.01', 'root.n.01'],
                       'hypernyms': ['root.n.01'], 'known': True,
                       'paths': {'alpha.n.01': ['alpha.n.01'],
                                 'root.n.01': ['alpha.n.01', 'root.n.01']}},
        'root.n.01': {'ancestors': ['root.n.01'], 'hypernyms': [], 'known': True},
        'beta.v.01': {'ancestors': ['beta.v.01'], 'hypernyms': [], 'known': True},
        'unknown.n.01': {'ancestors': ['unknown.n.01'], 'known': False},
    }
    ontology = parse_ontology({'sample.kif': '''(subclass Object Entity)
(subclass Work Entity)
(instance relation BinaryRelation)
(subclass BinaryRelation Relation)
(instance AttributeValue Attribute)
(documentation Object EnglishLanguage "Synthetic object.")
'''})
    nouns = parse_mappings(mapping_line(1, 'n', '&%Object='), 'n', 'noun.txt')
    verbs = parse_mappings(mapping_line(2, 'v', '&%Work+'), 'v', 'verb.txt')
    return lexicon, {'root.n.01': nouns['n:00000001'],
                     'beta.v.01': verbs['v:00000002']}, ontology


class OntologyParsingTests(unittest.TestCase):
    def test_only_ground_class_roles_and_provenanced_definitions(self):
        ontology = parse_ontology({'a.kif': '''; (subclass Comment Entity)
(subclass Alpha Entity)
(instance Beta Class)
(subclass Meta Class)
(instance Gamma Meta)
(instance SomeThing Alpha)
(instance relation Relation)
(=> (instance ?X Alpha) (subclass Conditional Entity))
(subclass ?X Entity)
(documentation Alpha EnglishLanguage "Text; (subclass Quoted Entity) \\"quoted\\".")
(quote (subclass QuotedForm Entity))
'''})
        self.assertEqual(ontology['classes'],
                         ['Alpha', 'Beta', 'Class', 'Entity', 'Gamma', 'Meta', 'Relation'])
        self.assertEqual(ontology['parents']['Alpha'], ['Entity'])
        self.assertNotIn('SomeThing', ontology['parents'])
        fact = next(f for f in ontology['facts'] if f['predicate'] == 'subclass')
        self.assertEqual((fact['subject'], fact['object'], fact['file'], fact['line']),
                         ('Alpha', 'Entity', 'a.kif', 2))
        self.assertEqual(fact['raw'], '(subclass Alpha Entity)')
        self.assertEqual(len([f for f in ontology['facts'] if f['predicate'] == 'instance']), 4)
        definition = ontology['definitions']['Alpha'][0]
        self.assertEqual(definition['line'], 10)
        self.assertIn('(subclass Quoted Entity)', definition['text'])

    def test_duplicate_ground_facts_keep_all_source_locations(self):
        ontology = parse_ontology({'b.kif': '(subclass Alpha Entity)',
                                   'a.kif': '(subclass Alpha Entity)'})
        self.assertEqual(ontology['parents']['Alpha'], ['Entity'])
        self.assertEqual([f['file'] for f in ontology['facts']], ['a.kif', 'b.kif'])

    def test_unmatched_syntax_reports_file_and_position(self):
        for value in ['\n(subclass Alpha Entity', '\n)', '\n(documentation Alpha Lang "bad)']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, r'bad.kif:2:\d+'):
                parse_ontology({'bad.kif': value})


class MappingParsingTests(unittest.TestCase):
    def test_exact_offsets_multiple_annotations_and_unmapped_rows(self):
        text = '\n'.join(['; header', mapping_line(1, 'n', '&%Alpha= &%Beta+ &%Alpha='),
                          mapping_line(2, 'n', ''),
                          mapping_line(3, 'n', 'mentions &%Ignored= inside this gloss')])
        rows = parse_mappings(text, 'n', 'noun.txt')
        self.assertEqual(set(rows), {'n:00000001', 'n:00000002', 'n:00000003'})
        self.assertEqual(rows['n:00000001']['mappings'],
                         [{'term': 'Alpha', 'relation': '='}, {'term': 'Beta', 'relation': '+'},
                          {'term': 'Alpha', 'relation': '='}])
        self.assertEqual(rows['n:00000001']['line'], 2)
        self.assertEqual(rows['n:00000001']['offset'], '00000001')
        self.assertEqual(rows['n:00000002']['mappings'], [])
        self.assertEqual(rows['n:00000003']['mappings'], [])

    def test_types_and_outer_whitespace_do_not_change_syntax(self):
        row = parse_mappings('  ' + mapping_line(1, 'v',
                             '&%A= &%B+ &%C@ &%D: &%E[ &%F]') + ' \t', 'v', 'v.txt')
        self.assertEqual([m['relation'] for m in row['v:00000001']['mappings']],
                         ['=', '+', '@', ':', '[', ']'])

    def test_malformed_annotation_tail_is_not_repaired_or_partially_admitted(self):
        for tail in ['&%Alpha', '&%Alpha +', '&% Alpha+', '&%Alpha+ &%Beta',
                     '&%Alpha+ &% Beta=', '&%Alpha++']:
            with self.subTest(tail=tail):
                raw = mapping_line(1, 'n', tail)
                row = parse_mappings(raw, 'n', 'noun.txt')['n:00000001']
                self.assertEqual(row['mappings'], [])
                self.assertEqual(row['error'], 'invalid_terminal_annotations')
                self.assertEqual(row['raw'], raw)

    def test_pos_is_validated_from_wordnet_prefix(self):
        with self.assertRaisesRegex(ValueError, 'noun.txt:1.*POS'):
            parse_mappings(mapping_line(1, 'v', '&%Alpha+'), 'n', 'noun.txt')

    def test_split_prefix_and_suffix_invalidates_the_complete_annotation_list(self):
        for tail in ['&% Alpha =', '&% Alpha = &%Beta+']:
            with self.subTest(tail=tail):
                row = parse_mappings(mapping_line(1, 'n', tail), 'n', 'noun.txt')['n:00000001']
                self.assertEqual(row['mappings'], [])
                self.assertEqual(row['error'], 'invalid_terminal_annotations')

    def test_duplicate_offsets_are_never_given_invented_keys(self):
        raw = mapping_line(1, 'n', '&%Alpha+')
        rows = parse_mappings(raw + '\n' + raw, 'n', 'noun.txt')
        self.assertEqual(list(rows), ['n:00000001'])
        self.assertEqual(rows['n:00000001']['duplicates'][0]['line'], 2)
        conflict = parse_mappings(raw + '\n' + mapping_line(1, 'n', '&%Beta+'),
                                  'n', 'noun.txt')['n:00000001']
        self.assertEqual(conflict['mappings'], [])
        self.assertEqual(conflict['error'], 'conflicting_duplicate_offset')


class AugmentationTests(unittest.TestCase):
    def test_inherited_mapping_keeps_namespaces_and_originals_with_full_path(self):
        lexicon, mappings, ontology = fixture()
        before = copy.deepcopy((lexicon, mappings, ontology))
        result = augment(lexicon, mappings, ontology, ['n', 'v'])
        self.assertEqual((lexicon, mappings, ontology), before)
        sense = result['senses']['alpha.n.01']
        self.assertEqual(sense['ancestors'], ['alpha.n.01', 'root.n.01', 'SUMO:Entity', 'SUMO:Object'])
        self.assertEqual(sense['paths'], lexicon['alpha.n.01']['paths'])
        path = sense['ontology_paths']['SUMO:Entity']
        self.assertEqual([edge['type'] for edge in path],
                         ['wordnet_hypernym', 'mapping', 'subclass'])
        self.assertEqual([(edge['source'], edge['target']) for edge in path],
                         [('alpha.n.01', 'root.n.01'), ('root.n.01', 'SUMO:Object'),
                          ('SUMO:Object', 'SUMO:Entity')])
        self.assertEqual((path[1]['relation'], path[1]['file'], path[1]['line']), ('=', 'noun.txt', 1))
        self.assertEqual((path[2]['file'], path[2]['line']), ('sample.kif', 1))
        self.assertNotIn('root.n.01', result['senses']['SUMO:Object']['ancestors'])
        self.assertEqual(result['senses']['unknown.n.01'], lexicon['unknown.n.01'])

    def test_typed_admission_class_roles_and_pos_conditions(self):
        lexicon, mappings, ontology = fixture()
        row = parse_mappings(mapping_line(1, 'n', '&%Object= &%Work+ &%Object@ '
                             '&%Object: &%Object[ &%Object] &%relation= '
                             '&%AttributeValue+ &%Absent='), 'n', 'noun.txt')['n:00000001']
        mappings['root.n.01'] = row
        nouns = augment(lexicon, mappings, ontology, ['n'])
        self.assertEqual({item['term'] for item in nouns['admitted']}, {'Object', 'Work'})
        self.assertNotIn('SUMO:Work', nouns['senses']['beta.v.01']['ancestors'])
        self.assertEqual(len(nouns['excluded']), 8)
        both = augment(lexicon, mappings, ontology, ['n', 'v'])
        self.assertIn('SUMO:Work', both['senses']['beta.v.01']['ancestors'])

    def test_reachable_cycle_reports_exact_path_but_unreachable_cycle_is_irrelevant(self):
        lexicon, mappings, ontology = fixture()
        extra = {'cycle.kif': '(subclass Other More)\n(subclass More Other)'}
        unrelated = parse_ontology({'sample.kif': '(subclass Object Entity)\n(subclass Work Entity)', **extra})
        augment(lexicon, mappings, unrelated, ['n'])
        cyclic = parse_ontology({'cycle.kif': '(subclass Object Entity)\n(subclass Entity Object)'})
        with self.assertRaisesRegex(ValueError, r'SUMO:Object -> SUMO:Entity -> SUMO:Object'):
            augment(lexicon, mappings, cyclic, ['n'])

    def test_deterministic_output_and_no_reverse_collapse(self):
        lexicon, mappings, ontology = fixture()
        first = augment(lexicon, mappings, ontology, ['n', 'v'])
        second = augment(dict(reversed(list(lexicon.items()))),
                         dict(reversed(list(mappings.items()))), ontology, ['v', 'n'])
        self.assertEqual(first, second)
        self.assertNotIn('beta.v.01', first['senses']['root.n.01']['ancestors'])
        self.assertNotIn('root.n.01', first['senses']['beta.v.01']['ancestors'])

    def test_construct_keeps_original_patterns_memberships_and_native_witnesses(self):
        lexicon, mappings, ontology = fixture()
        records = [{'row': row, 'note': f'N{row}'} for row in [1, 2]]
        graphs = [{'row': row, 'nodes': [{'id': 1, 'sense': noun, 'context': 0},
                                       {'id': 2, 'sense': 'beta.v.01', 'context': 1}],
                   'edges': [{'source': 1, 'target': 2, 'role': 'synthetic'}]}
                  for row, noun in [(1, 'alpha.n.01'), (2, 'root.n.01')]]
        original = construct(records, graphs, lexicon, relation_policy='connection')
        augmented = construct(records, graphs, augment(lexicon, mappings, ontology, ['n', 'v'])['senses'],
                              relation_policy='connection')
        self.assertEqual(original['conditions'][0], augmented['conditions'][0])
        old_patterns = {p['id']: p for p in original['conditions'][1]['patterns']}
        new_patterns = {p['id']: p for p in augmented['conditions'][1]['patterns']}
        self.assertEqual(old_patterns, {key: new_patterns[key] for key in old_patterns})
        for pattern in new_patterns.values():
            for witness in pattern['witnesses']:
                self.assertTrue(all(not sense.startswith('SUMO:') for sense in witness['source_senses']))


if __name__ == '__main__':
    unittest.main()
