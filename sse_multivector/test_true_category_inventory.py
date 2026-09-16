"""A rejected title must not silently remove an HDBSCAN group."""
import unittest

from true_category_graph import prepare_inputs


class InventoryTests(unittest.TestCase):
    def test_missing_source_group_is_an_error(self):
        titles = {'groups': [{'group': 'a', 'title': 'Coffee'}]}
        with self.assertRaisesRegex(ValueError, 'missing.*b'):
            prepare_inputs(titles, source_group_ids=['a', 'b'])

    def test_title_review_status_does_not_filter_groups(self):
        titles = {'groups': [
            {'group': 'a', 'title': 'Coffee'},
            {'group': 'b', 'title': '#coffeechain', 'assistant_judgment': 'rejected'},
        ]}
        rows = prepare_inputs(titles, source_group_ids=['a', 'b'])
        self.assertEqual({(r['a_id'], r['b_id']) for r in rows}, {('a', 'b'), ('b', 'a')})

    def test_explicit_consolidations_account_for_original_groups(self):
        titles = {'groups': [{'group': 'a', 'title': 'Coffee'},
                             {'group': 'c', 'title': 'Tea'}]}
        rows = prepare_inputs(titles, source_group_ids=['a', 'b', 'c'],
                              consolidations=[{'canonical': 'a', 'source_group_ids': ['a', 'b']}])
        self.assertEqual(len(rows), 2)

    def test_consolidation_cannot_hide_a_missing_canonical_group(self):
        titles = {'groups': [{'group': 'c', 'title': 'Tea'}]}
        with self.assertRaisesRegex(ValueError, 'missing.*a'):
            prepare_inputs(titles, source_group_ids=['a', 'b', 'c'],
                           consolidations=[{'canonical': 'a', 'source_group_ids': ['a', 'b']}])

    def test_invented_group_is_an_error(self):
        with self.assertRaisesRegex(ValueError, 'unexpected.*b'):
            prepare_inputs({'groups': [{'group': 'a', 'title': 'Coffee'},
                                       {'group': 'b', 'title': 'Tea'}]}, source_group_ids=['a'])

    def test_overlapping_consolidations_cannot_hide_groups(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            prepare_inputs({'groups': [{'group': 'a', 'title': 'Coffee'}]},
                source_group_ids=['a', 'b', 'c'], consolidations=[
                    {'canonical': 'a', 'source_group_ids': ['a', 'b']},
                    {'canonical': 'a', 'source_group_ids': ['a', 'c']}])

    def test_duplicate_source_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique source'):
            prepare_inputs({'groups': [{'group': 'a', 'title': 'Coffee'}]},
                           source_group_ids=['a', 'a'])

    def test_missing_title_is_an_error_not_a_filtered_group(self):
        with self.assertRaisesRegex(ValueError, 'nonempty exact generated titles'):
            prepare_inputs({'groups': [{'group': 'a', 'title': 'Coffee'},
                                       {'group': 'b', 'title': ''}]},
                           source_group_ids=['a', 'b'])


if __name__ == '__main__':
    unittest.main()
