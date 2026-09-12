import copy
import unittest

from sense_relation_probe import prepare_pairs, annotate_scores, select_native


class SenseRelationProbeTests(unittest.TestCase):
    def setUp(self):
        self.source = [dict(measurement='relation', kind='subject', child_group='g1',
                            parent_group='g2', premise='This text is about Bread..',
                            hypothesis='This text is about Food..', score=.9)]
        self.manual = dict(groups=[dict(id='g1', description='bread as food'),
                                  dict(id='g2', description='food')])
        self.native = [dict(id='n1',definition1='small',definition2='large',label='antonym')]

    def test_all_source_text_is_preserved_without_wrappers(self):
        before = copy.deepcopy((self.source,self.manual,self.native))
        pairs = prepare_pairs(self.source,self.manual,self.native)
        self.assertEqual((self.source,self.manual,self.native),before)
        self.assertEqual(len(pairs),4)
        self.assertEqual(pairs[0]['first'],'Bread.')
        self.assertEqual(pairs[0]['second'],'Food.')
        self.assertEqual(pairs[1]['first'],'bread as food')
        self.assertEqual(pairs[2]['first'],'food')
        self.assertEqual(pairs[3]['expected_label'],'antonym')

    def test_multiclass_scores_preserve_label_direction(self):
        pairs = [dict(),dict()]
        labels = {0:'homonym',1:'hyponym',2:'hypernym',3:'co-hyponym',4:'antonym'}
        annotate_scores(pairs,[[0,1000,0,0,0],[0,0,1000,0,0]],labels)
        self.assertEqual([p['prediction'] for p in pairs],['hyponym','hypernym'])
        self.assertTrue(all(abs(sum(p['scores'].values())-1)<1e-10 for p in pairs))

    def test_bad_inputs_or_logits_fail(self):
        self.source[0]['premise']='changed wrapper'
        with self.assertRaises(ValueError):prepare_pairs(self.source,self.manual,self.native)
        with self.assertRaises(ValueError):annotate_scores([{}],[[float('nan')]],{0:'homonym'})
        with self.assertRaises(ValueError):annotate_scores([{}],[],{0:'homonym'})

    def test_native_selection_ignores_classes_absent_from_checkpoint(self):
        rows = [dict(id='extra', label='metaphor')]
        labels = ['negative', 'hyponym', 'hypernym', 'co-hyponym', 'antonym']
        for index in range(3):
            rows.extend(dict(id=f'{label}-{index}', label=label) for label in labels)
        selected = select_native(rows)
        self.assertEqual(selected, rows[1:11])
        with self.assertRaises(ValueError): select_native(rows[:5])


if __name__=='__main__':
    unittest.main()
