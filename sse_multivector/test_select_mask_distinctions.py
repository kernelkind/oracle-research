"""Frozen masks, not generated names, supply this experimental selector's evidence."""
from copy import deepcopy
import unittest

from select_mask_distinctions import mask_words, describe_categories, select_distinctions
from select_note_categories import memberships


class MaskDistinctionTests(unittest.TestCase):
    def fixture(self):
        fragments = [['coffee'], ['Coffee'], ['iced coffee'], ['had coffee'], ['just had', 'coffee']]
        evidence = [dict(row=i, aliases=[dict(fragments=f)]) for i, f in enumerate(fragments)]
        hierarchy = dict(nodes=[
            dict(id=1, members=list(range(5))), dict(id=2, members=[0, 1]),
            dict(id=3, members=[3, 4]), dict(id=4, members=[2]),
        ])
        categories = dict(root_node_id='1', hierarchy_id='test', nodes=[
            dict(node_id='1', label='Untrusted title', children=['2', '3', '4'], note_ids=[]),
            dict(node_id='2', label='Different title', children=[], note_ids=['a', 'b']),
            dict(node_id='3', label='Untrusted title', children=[], note_ids=['d', 'e']),
            dict(node_id='4', label='Untrusted title', children=[], note_ids=['c']),
        ], note_masks={'1': {n: [[0, 1]] for n in 'abcde'},
                       '2': {n: [[0, 1]] for n in 'ab'},
                       '3': {n: [[0, 1]] for n in 'de'}, '4': {'c': [[0, 1]]}})
        return categories, hierarchy, evidence

    def test_all_words_retained_without_joining_fragments_into_phrases(self):
        self.assertEqual(mask_words(['You’ve had coffee.', '#coffee']), {'you', 've', 'had', 'coffee'})
        self.assertEqual(mask_words(['not', 'coffee']), {'not', 'coffee'})

    def test_only_shared_words_are_not_sufficient_to_remove_a_child(self):
        categories, hierarchy, evidence = self.fixture()
        description = describe_categories(categories, hierarchy, evidence)
        self.assertEqual(description['1']['common_words'], ['coffee'])
        self.assertEqual(description['3']['common_words'], ['coffee', 'had'])
        selected, trace = select_distinctions(categories, description)
        self.assertEqual([t['removed'] for t in trace], ['2'])
        self.assertEqual(selected['nodes'][0]['children'], ['3', '4'])
        self.assertEqual(selected['nodes'][0]['note_ids'], ['a', 'b'])

    def test_same_common_word_with_extra_child_evidence_is_preserved(self):
        categories, hierarchy, evidence = self.fixture()
        evidence[3]['aliases'][0]['fragments'] = ['wine', 'food']
        evidence[4]['aliases'][0]['fragments'] = ['dry white wine']
        for e in evidence[:3]:
            e['aliases'][0]['fragments'] = ['wine']
        description = describe_categories(categories, hierarchy, evidence)
        self.assertEqual(description['1']['common_words'], ['wine'])
        self.assertEqual(description['3']['common_words'], ['wine'])
        selected, trace = select_distinctions(categories, description)
        self.assertIn('3', {n['node_id'] for n in selected['nodes']})
        self.assertNotIn('3', {t['removed'] for t in trace})

    def test_retained_memberships_masks_titles_and_input_are_unchanged(self):
        categories, hierarchy, evidence = self.fixture()
        original = deepcopy(categories)
        description = describe_categories(categories, hierarchy, evidence)
        selected, _ = select_distinctions(categories, description)
        full = memberships(original)
        self.assertEqual(categories, original)
        self.assertEqual(memberships(selected), {n['node_id']: full[n['node_id']] for n in selected['nodes']})
        for n in selected['nodes']:
            i = n['node_id']
            self.assertEqual(selected['note_masks'][i], original['note_masks'][i])
            self.assertEqual(n['label'], next(x['label'] for x in original['nodes'] if x['node_id'] == i))

    def test_empty_common_words_abstain(self):
        categories, hierarchy, evidence = self.fixture()
        evidence[2]['aliases'][0]['fragments'] = ['tea']
        description = describe_categories(categories, hierarchy, evidence)
        self.assertEqual(description['1']['common_words'], [])
        selected, trace = select_distinctions(categories, description)
        self.assertEqual(trace, [])
        self.assertEqual(selected, categories)

    def test_removing_intermediate_promotes_children_without_losing_notes(self):
        categories, hierarchy, evidence = self.fixture()
        categories['nodes'][1]['children'] = ['5']
        categories['nodes'][1]['note_ids'] = ['a']
        categories['nodes'].append(dict(node_id='5', label='Leaf', children=[], note_ids=['b']))
        categories['note_masks']['5'] = {'b': [[0, 1]]}
        hierarchy['nodes'].append(dict(id=5, members=[1]))
        description = describe_categories(categories, hierarchy, evidence)
        selected, trace = select_distinctions(categories, description)
        self.assertEqual([t['removed'] for t in trace], ['2', '5'])
        self.assertEqual(selected['nodes'][0]['note_ids'], ['a', 'b'])
        self.assertEqual(memberships(selected)['1'], set('abcde'))

    def test_malformed_sources_are_rejected(self):
        categories, hierarchy, evidence = self.fixture()
        hierarchy['nodes'][1]['members'] = [999]
        with self.assertRaises(ValueError):
            describe_categories(categories, hierarchy, evidence)

    def test_missing_profile_is_not_treated_as_empty_evidence(self):
        categories, hierarchy, evidence = self.fixture()
        description = describe_categories(categories, hierarchy, evidence)
        del description['2']
        with self.assertRaises(ValueError):
            select_distinctions(categories, description)


if __name__ == '__main__':
    unittest.main()
