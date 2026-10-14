"""Checks for the offline full-tree review, without changing construction."""
import unittest
import xml.etree.ElementTree as ET

from sse_multivector import hdbscan_epsilon_review as review
from sse_multivector.test_hierarchy_hdbscan import fixture


class EpsilonReviewTests(unittest.TestCase):
    def test_reviewed_hr21_curve_selects_full_partition_interval(self):
        # The frozen HR21 split distances, including its very tight final pair.
        distances = [1.151103443881878, 1.0998875157610728,
                     1.0783019706888133, 1.0776613900489258,
                     1.0616310216378926, 1.0587271258280344,
                     1.0568904793717049, 1.0471421451927838,
                     1.0210481276903318, 1.0005248238827136,
                     .982620694045027, .9691654684396345,
                     .9677034753479824, .9650745219746838,
                     .9161756052325961, .8817786641492207,
                     .8464473692866891, .7910826408499776,
                     .7228193745003901, .6982921965099583,
                     .6663547730967898, .6533296106811058,
                     .6498710523663698, .30204337792740876]
        response, request, mapping = fixture(25, distances)
        tree = review.project(response, request, mapping)
        selection = review.select_epsilon(tree)
        self.assertAlmostEqual(selection['epsilon'], .94062506360364)
        sections = review.partition(tree, selection['epsilon'])
        self.assertEqual(len(sections), 15)
        self.assertEqual(sorted(g for s in sections for g in s['groups']),
                         list(range(1, 26)))

    def test_tied_splits_are_counted_together_and_groups_stay_atomic(self):
        response, request, mapping = fixture(7, [3, 2, 2, 2, 1, 1])
        tree = review.project(response, request, mapping)
        self.assertEqual([p['section_count'] for p in review.curve(tree)], [2, 5, 7])
        self.assertEqual(len(review.partition(tree, 1.5)), 5)
        with self.assertRaisesRegex(ValueError, 'retained distance levels'):
            review.select_epsilon(tree)

    def test_svg_colors_every_group_and_keeps_cutoff_outside_tree(self):
        response, request, mapping = fixture(7)
        tree = review.project(response, request, mapping)
        sections = review.partition(tree, 3.5)
        groups = [dict(id=i, titles=[f'Topic {i}'], entries=2, notes=2)
                  for i in range(1, 8)]
        svg = review.render_svg(tree, sections, groups, 3.5, title='Review',
                                provenance={})
        root = ET.fromstring(svg)
        labels = [e for e in root.iter() if e.get('data-group')]
        self.assertEqual(len(labels), 7)
        self.assertTrue(all(e.get('fill') not in ('#a8adb4', None) for e in labels))
        self.assertIn('cutoff-arrow-top', svg)
        self.assertIn('cutoff-arrow-bottom', svg)
        self.assertNotIn('stroke-dasharray', svg)


if __name__ == '__main__':
    unittest.main()
