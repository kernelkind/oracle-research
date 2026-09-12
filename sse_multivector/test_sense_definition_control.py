import unittest

from sense_definition_control import prepare_control


class SenseDefinitionControlTests(unittest.TestCase):
    def test_preserves_all_pairs_and_their_original_readings(self):
        source = [dict(condition='manual', child_group='a', parent_group='b',
                       first='A', second='B', scores={'hyponym': .7}, prediction='hyponym'),
                  dict(condition='manual', child_group='b', parent_group='a',
                       first='B', second='A', scores={'hypernym': .8}, prediction='hypernym')]
        definitions = dict(groups=[dict(id='a', description='Meaning A'),
                                   dict(id='b', description='Meaning B')])
        pairs = prepare_control(source, definitions)
        self.assertEqual(len(pairs), 2)
        self.assertEqual([p['first'] for p in pairs], ['Meaning A', 'Meaning B'])
        self.assertEqual([p['baseline']['first'] for p in pairs], ['A', 'B'])
        self.assertEqual(pairs[0]['baseline']['scores'], {'hyponym': .7})
        self.assertEqual(source[0]['first'], 'A')
        with self.assertRaises(ValueError): prepare_control(source[:1], definitions)
        definitions['groups'].append(dict(id='a', description='Duplicate'))
        with self.assertRaises(ValueError): prepare_control(source, definitions)


if __name__ == '__main__':
    unittest.main()
