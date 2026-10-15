"""V5 cuts and construction through the production hierarchy workflow."""

import unittest

from sse_multivector import hierarchy_hdbscan as hdbscan
from sse_multivector.test_hierarchy_hdbscan import fixture


class V5CutTests(unittest.TestCase):
    def tree(self, groups, distances=None):
        return hdbscan.project(*fixture(groups, distances))

    def test_middle_eighty_percent_bend_can_keep_more_than_six_sections(self):
        tree = self.tree(14, [100, 99, 98, 97, 96, 95, 94, 93, 92, 80, 60, 30, 1])
        result = hdbscan.select_sections(tree)
        self.assertEqual(result['rule'], 'trimmed-bend-10-percent-v1')
        self.assertEqual(result['omitted_levels_per_end'], 2)
        self.assertEqual(result['epsilon'], 86)
        self.assertEqual(len(result['sections']), 10)
        self.assertEqual(sorted(g for s in result['sections'] for g in s['groups']),
                         list(range(1, 15)))

    def test_short_curve_uses_previous_six_section_cut(self):
        result = hdbscan.select_sections(self.tree(8))
        self.assertEqual(result['rule'], 'six-section-v4')
        self.assertEqual(len(result['sections']), 6)
        self.assertEqual(result['epsilon'], 2.5)

    def test_no_positive_bend_uses_previous_cut(self):
        result = hdbscan.select_sections(self.tree(8, [128, 64, 32, 16, 8, 4, 2]))
        self.assertEqual(result['rule'], 'six-section-v4')
        self.assertIn('positive bend', result['reason'])

    def test_impossible_tied_cut_returns_groups_for_largest_note_selection(self):
        result = hdbscan.select_sections(self.tree(8, [1]*7))
        self.assertEqual(result['rule'], 'largest-groups-v5')
        self.assertIsNone(result['epsilon'])
        self.assertEqual(len(result['sections']), 8)
        self.assertTrue(all(len(s['groups']) == 1 for s in result['sections']))

    def test_six_or_fewer_groups_are_direct_leaves(self):
        for count in (1, 4, 6):
            with self.subTest(count=count):
                result = hdbscan.select_sections(self.tree(count))
                self.assertEqual(result['rule'], 'group-leaves-v5')
                self.assertEqual(len(result['sections']), count)
                self.assertTrue(all(not s['children'] for s in result['sections']))


if __name__ == '__main__':
    unittest.main()
