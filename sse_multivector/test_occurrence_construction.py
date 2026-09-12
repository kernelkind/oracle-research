import unittest

from occurrence_construction import source_graphs
from semantic_graph_patterns import construct


class OccurrenceConstructionTests(unittest.TestCase):
    def example(self):
        inputs = [dict(row=1, note='N01', subject='apple cooking'),
                  dict(row=2, note='N01', subject='bread'),
                  dict(row=3, note='N02', subject='pear cooking')]
        scores = []
        for record, senses in zip(inputs, [['apple', 'cook'], ['bread'], ['pear', 'cook']]):
            for i, (word, sense) in enumerate(zip(record['subject'].split(), senses)):
                start = record['subject'].index(word)
                scores.append(dict(**record, word_index=i,
                                   word=dict(text=word, start_char=start, end_char=start+len(word)),
                                   matches=[dict(synset=sense)]))
        return inputs, scores

    def test_pairs_are_distinct_occurrences_within_one_description(self):
        inputs, scores = self.example()
        graphs = source_graphs(inputs, scores, pairs=True)
        self.assertEqual([len(g['edges']) for g in graphs], [1, 0, 1])
        self.assertTrue(all(e['role'] == 'same_description' for g in graphs for e in g['edges']))
        baseline = source_graphs(inputs, scores, pairs=False)
        self.assertTrue(all(not g['edges'] for g in baseline))
        scores[1]['matches'] = []
        self.assertEqual(len(source_graphs(inputs, scores, pairs=True)[0]['nodes']), 1)
        self.assertFalse(source_graphs(inputs, scores, pairs=True)[0]['edges'])

    def test_production_construction_preserves_singletons_and_witnessed_narrowing(self):
        inputs, scores = self.example()
        lexicon = {s:dict(ancestors=a) for s,a in {
            'apple':['apple','fruit'], 'pear':['pear','fruit'],
            'fruit':['fruit'], 'cook':['cook'], 'bread':['bread']}.items()}
        baseline = construct(inputs, source_graphs(inputs,scores,pairs=False), lexicon, 'connection')
        paired = construct(inputs, source_graphs(inputs,scores,pairs=True), lexicon, 'connection')
        old = baseline['conditions'][1]['patterns']
        new = paired['conditions'][1]['patterns']
        self.assertEqual(old, [p for p in new if p['kind']=='singleton'])
        group = next(p for p in new if p['key']==['cook','fruit'])
        self.assertEqual(group['notes'], ['N01','N02'])
        self.assertEqual(group['rows'], [1,3])
        self.assertEqual([w['node_ids'] for w in group['witnesses']], [[0,1],[0,1]])
        self.assertFalse(any(p['key']==['bread','cook'] for p in new))

    def test_source_drift_duplicate_words_and_duplicate_senses(self):
        inputs, scores = self.example()
        scores[1]['matches'] = scores[0]['matches']
        self.assertFalse(source_graphs(inputs,scores,pairs=True)[0]['edges'])
        with self.assertRaises(ValueError):
            source_graphs(inputs, scores+[scores[0]], pairs=False)
        scores[0]['note'] = 'N99'
        with self.assertRaises(ValueError):
            source_graphs(inputs, scores, pairs=False)


if __name__ == '__main__':
    unittest.main()
