import copy
import unittest

from group_description_relations import prepare_pairs


class GroupDescriptionRelationsTests(unittest.TestCase):
    def setUp(self):
        self.groups = [
            dict(id='a', seeds=[dict(source=dict(fragments=['GM']))], evidence=[dict(row=1)]),
            dict(id='b', seeds=[dict(source=dict(fragments=['good morning']))], evidence=[dict(row=2)]),
        ]
        self.fixture = dict(template='This text is about {}.', groups=[
            dict(id='a', description='greeting people'),
            dict(id='b', description='wishing people a good morning')],
            expected_implications=[['a', 'b'], ['b', 'a']])

    def test_all_directions_and_context_conditions(self):
        pairs = prepare_pairs(self.groups, self.fixture)
        self.assertEqual(len(pairs), 8)
        both = next(p for p in pairs if p['condition'] == 'both_context'
                    and p['child'] == 'a')
        self.assertEqual(both['premise'], 'This text is about greeting people.')
        self.assertEqual(both['hypothesis'], 'This text is about wishing people a good morning.')
        parent = next(p for p in pairs if p['condition'] == 'parent_context'
                      and p['child'] == 'a')
        self.assertEqual(parent['premise'], 'This text is about GM.')
        self.assertEqual(parent['hypothesis'], both['hypothesis'])
        self.assertTrue(all(p['child'] != p['parent'] for p in pairs))

    def test_original_data_and_source_order_are_preserved(self):
        self.groups[0]['seeds'][0]['source']['fragments'] = ['a word', 'in source order']
        before = copy.deepcopy(self.groups)
        pairs = prepare_pairs(self.groups, self.fixture)
        self.assertEqual(self.groups, before)
        self.assertEqual(pairs[0]['premise'], 'This text is about a word in source order.')
        self.assertNotIn('evidence', pairs[0])

    def test_rejects_unknown_duplicate_or_empty_groups(self):
        for replacement in [[], [dict(id='missing', description='x')],
                            [self.fixture['groups'][0]] * 2]:
            fixture = dict(self.fixture, groups=replacement)
            with self.assertRaises(ValueError):
                prepare_pairs(self.groups, fixture)

    def test_seed_meaning_must_not_be_silently_chosen(self):
        self.groups[0]['seeds'].append(dict(source=dict(fragments=['different seed'])))
        with self.assertRaises(ValueError):
            prepare_pairs(self.groups, self.fixture)


if __name__ == '__main__':
    unittest.main()
