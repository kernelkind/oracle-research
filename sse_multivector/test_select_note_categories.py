"""Navigation selection must preserve every retained destination's evidence."""
from copy import deepcopy
import unittest

from select_note_categories import select_categories, memberships


class CategorySelectionTests(unittest.TestCase):
    def fixture(self):
        return dict(root_node_id='r', hierarchy_id='test', nodes=[
            dict(node_id='r', children=['big', 'side'], note_ids=['z'], label='Root'),
            dict(node_id='big', children=['a', 'b'], note_ids=['residual'], label='Intermediate'),
            dict(node_id='a', children=[], note_ids=list('abcdef'), label='A'),
            dict(node_id='b', children=[], note_ids=['g', 'h'], label='B'),
            dict(node_id='side', children=[], note_ids=['i'], label='Side'),
        ], note_masks={
            'r': {n: [[0, 1]] for n in [*'abcdefghi', 'residual', 'z']},
            'big': {n: [[0, 1]] for n in [*'abcdefgh', 'residual']},
            'a': {n: [[0, 1]] for n in 'abcdef'},
            'b': {n: [[0, 1]] for n in 'gh'}, 'side': {'i': [[0, 1]]}})

    def test_promotes_multichild_branch_preserving_side_leaf_residual_and_masks(self):
        original = self.fixture()
        before = deepcopy(original)
        result, trace = select_categories(original, max_choices=3)
        nodes = {n['node_id']: n for n in result['nodes']}
        self.assertEqual(nodes['r']['children'], ['a', 'b', 'side'])
        self.assertEqual(nodes['r']['note_ids'], ['residual', 'z'])
        self.assertEqual(set(nodes), {'r', 'a', 'b', 'side'})
        full = memberships(original)
        self.assertEqual(memberships(result), {i: full[i] for i in nodes})
        self.assertEqual(result['note_masks'], {i: original['note_masks'][i] for i in nodes})
        self.assertEqual(original, before)
        self.assertEqual(trace[0]['removed'], 'big')

    def test_bound_prevents_large_menus_and_operation_is_deterministic(self):
        original = self.fixture()
        result, trace = select_categories(original, max_choices=2)
        self.assertEqual(result['nodes'], original['nodes'])
        self.assertEqual(trace, [])
        self.assertEqual(select_categories(original, max_choices=3),
                         select_categories(original, max_choices=3))

    def test_same_note_sets_in_separate_branches_are_not_deduplicated(self):
        original = self.fixture()
        original['nodes'][3]['note_ids'] = list('abcdef')
        result, _ = select_categories(original, max_choices=3)
        self.assertTrue({'a', 'b'} <= {n['node_id'] for n in result['nodes']})

    def test_cycles_or_shared_children_are_rejected(self):
        original = self.fixture()
        original['nodes'][1]['children'].append('side')
        with self.assertRaises(ValueError):
            select_categories(original, max_choices=3)


if __name__ == '__main__':
    unittest.main()
