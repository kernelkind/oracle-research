import copy
import unittest

from semantic_conjunction import conjoin, quotient
from semantic_graph_patterns import construct


class SemanticConjunctionTests(unittest.TestCase):
    def example(self):
        rows = [(1, 'N1', ['heat', 'stir', 'meat']),
                (2, 'N2', ['heat', 'meat']), (3, 'N3', ['heat']),
                (4, 'N3', ['meat'])]
        records = [dict(row=r, note=n) for r,n,_ in rows]
        graphs = []
        for row,note,senses in rows:
            nodes = [dict(id=i,context=0,sense=s) for i,s in enumerate(senses)]
            edges = [dict(source=a,target=b,role='same_description')
                     for a in range(len(nodes)) for b in range(a+1,len(nodes))]
            graphs.append(dict(row=row,note=note,nodes=nodes,edges=edges))
        lexicon = {s:dict(ancestors=a) for s,a in {
            'heat':['heat','act'], 'stir':['stir','act'], 'act':['act'],
            'meat':['meat','food'], 'food':['food']}.items()}
        return construct(records, graphs, lexicon, 'connection'), lexicon

    def test_shared_occurrence_preserves_keys_witnesses_and_description_scope(self):
        result, lexicon = self.example()
        original = result['conditions'][1]
        unchanged = copy.deepcopy(original)
        new = conjoin(original)
        self.assertEqual(original, unchanged)
        self.assertEqual([p['id'] for p in original['patterns']],
                         [p['id'] for p in new['patterns']])
        old_pair = next(p for p in original['patterns'] if p['key']==['act','heat'])
        pair = next(p for p in new['patterns'] if p['key']==['act','heat'])
        self.assertEqual(old_pair['rows'], [1])
        self.assertEqual(pair['rows'], [1,2,3])
        self.assertEqual(pair['notes'], ['N1','N2','N3'])
        self.assertEqual(pair['witnesses'][:len(old_pair['witnesses'])], old_pair['witnesses'])
        extra = pair['witnesses'][len(old_pair['witnesses']):]
        self.assertTrue(all(w['node_ids']==[0,0] and w['edge'] is None for w in extra))
        meat = next(p for p in new['patterns'] if p['key']==['heat','meat'])
        self.assertEqual(meat['notes'], ['N1','N2'])
        self.assertEqual(result['conditions'][0], conjoin(result['conditions'][0]))

    def test_quotient_uses_lexical_entailment_not_observed_equal_sets(self):
        result, lexicon = self.example()
        new = conjoin(result['conditions'][1])
        q = quotient(new, lexicon)
        ids = {tuple(p['key']):p['id'] for p in new['patterns']}
        self.assertEqual(q['equivalence'][ids['act','heat']], ids['heat',])
        self.assertEqual(q['equivalence'][ids['heat','meat']], ids['heat','meat'])
        self.assertTrue(all(e['parent'] != e['child'] for e in q['condition']['edges']))
        for p in q['condition']['patterns']:
            original = next(x for x in new['patterns'] if x['id']==p['id'])
            self.assertEqual((p['rows'],p['notes']), (original['rows'],original['notes']))
        literal = quotient(result['conditions'][0], lexicon)
        self.assertEqual(literal['condition'], result['conditions'][0])
        self.assertTrue(all(k==v for k,v in literal['equivalence'].items()))

    def test_refuses_missing_singletons_and_non_occurrence_relations(self):
        result, _ = self.example()
        original = result['conditions'][1]
        original['patterns'] = [p for p in original['patterns'] if p['key']!=['act']]
        with self.assertRaises(ValueError):
            conjoin(original)
        result, _ = self.example()
        next(p for p in result['conditions'][1]['patterns'] if p['kind']=='connection')['kind']='role'
        with self.assertRaises(ValueError):
            conjoin(result['conditions'][1])


if __name__ == '__main__':
    unittest.main()
