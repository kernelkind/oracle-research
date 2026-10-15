"""Checks for the offline full-tree review, without changing construction."""
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

from sse_multivector import hdbscan_epsilon_review as review
from sse_multivector.test_hierarchy_hdbscan import fixture
from sse_multivector import test_hierarchy_generation_v3 as native_fixtures


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


class SavedSourceSelectionTests(unittest.TestCase):
    def source(self, prefix, complete=True):
        native = native_fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.configure_v32(count=3)
        corpus = json.loads((native.root/'notes.json').read_text())
        for note in corpus['notes']:
            note['note_id'] = prefix + note['note_id']
        native.write('notes.json', corpus)
        definition = json.loads(spec.read_text())
        definition['note_ids'] = [n['note_id'] for n in corpus['notes']]
        native.write('hierarchy.json', definition)
        native.cli('prepare-hierarchy', 'trial', '--spec', spec)
        if not complete:
            return native.state()
        native.collect_title_bootstrap()
        native.encode_pending()
        native.cli('advance-hierarchy', 'trial', '--comment', 'Collect original vectors')
        return native.state()

    def test_combination_selects_notes_not_entries_and_reuses_exact_vectors(self):
        sources = [self.source('food-'), self.source('music-')]
        combined, vectors, selections = review.combine_sources(sources, 2)
        self.assertEqual(combined['note_ids'], ['food-n0', 'food-n1', 'music-n0', 'music-n1'])
        self.assertEqual(len(combined['originals']), 4)
        self.assertEqual(len(vectors), 4)
        self.assertEqual(len(set(combined['items'])), 4)
        self.assertEqual([s['note_ids'] for s in selections],
                         [['food-n0', 'food-n1'], ['music-n0', 'music-n1']])
        self.assertEqual(vectors, review._vectors(sources[0], ['L00001', 'L00002']) +
                         review._vectors(sources[1], ['L00001', 'L00002']))
        request, mapping = review.hdbscan.request_for(combined, list(combined['items']), vectors)
        self.assertEqual(len(request['inputs']), 4)
        self.assertEqual(len(mapping), 4)
        with self.assertRaisesRegex(ValueError, 'overlapping note'):
            review.combine_sources([sources[0], sources[0]], 2)
        with self.assertRaisesRegex(ValueError, 'not enough notes'):
            review.combine_sources(sources, 4)

    def test_unfinished_bootstrap_is_not_treated_as_null_meanings(self):
        with self.assertRaisesRegex(ValueError, 'Bootstrap is incomplete'):
            review.combine_sources([self.source('pending-', complete=False)], 2)


class SectionSourceSelectionTests(unittest.TestCase):
    def test_native_cli_selects_one_original_section_plus_noise_without_synthetic_nodes(self):
        native = native_fixtures.HierarchyGenerationV3Tests('runTest')
        native.setUp()
        self.addCleanup(native.doCleanups)
        spec = native.prepare_v41()
        binary = native.root/'hdbscan-fixture'
        binary.write_text(binary.read_text().replace(
            '1/((k-i-1)/10)', '1/(((k-i-1)/10)**0.3)'))
        native.cli('prepare-hierarchy', 'v41', '--spec', spec)
        native.cli('run-hierarchy', 'v41')
        state_path = native.root/'v41/state.json'
        state = json.loads(state_path.read_text())
        baseline = review.saved_review(state_path)
        section = next(s for s in baseline['sections'] if len(s['groups']) >= 2)
        label = f"S{baseline['sections'].index(section)+1:02d}"
        output = native.root/'inside'
        completed = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_epsilon_review',
            str(state_path), '--section', label, '--include-unassigned', '--output', str(output),
            '--name', 'inside-section'], cwd=native_fixtures.PROJECT,
            text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
        result = json.loads((output/'analysis.json').read_text())
        assigned = {i for g in baseline['groups'] for i in g['original_ids']}
        original = state['families'][0]['rounds'][0]['current']
        section_ids = {i for g in baseline['groups'] if g['id'] in section['groups']
                       for i in g['original_ids']}
        noise = set(original)-assigned
        self.assertTrue(noise)
        wanted = [i for i in original if i in section_ids or i in noise]
        selection = result['provenance']['sources'][0]['selection']
        self.assertEqual(selection['source_ids'], wanted)
        self.assertEqual(selection['section_entry_count'], len(section_ids))
        self.assertEqual(selection['unassigned_entry_count'], len(noise))
        self.assertFalse((assigned-section_ids) & set(selection['source_ids']))
        self.assertTrue(all(i.startswith('L') for i in selection['source_ids']))
        expected, _ = review.hdbscan.request_for(state, wanted, review._vectors(state, wanted))
        self.assertEqual(json.loads((output/'request.json').read_text()), expected)
        self.assertEqual(result['encoded_entries'], len(wanted))
        self.assertEqual(result['provenance']['new_model_calls'], 0)
        self.assertEqual(result['provenance']['new_encodings'], 0)
        self.assertTrue((output/'inside-section.svg').exists())
        self.assertEqual(json.loads(state_path.read_text()), state)
        # The existing whole-source mode continues through the same numerical path.
        full_output = native.root/'whole-source'
        whole = subprocess.run([sys.executable, '-m', 'sse_multivector.hdbscan_epsilon_review',
            str(state_path), '--notes-per-source', '43', '--output', str(full_output)],
            cwd=native_fixtures.PROJECT, text=True, capture_output=True)
        self.assertEqual(whole.returncode, 0, whole.stdout+whole.stderr)
        full = json.loads((full_output/'analysis.json').read_text())
        self.assertEqual(full['encoded_entries'], 43)
        self.assertEqual(full['provenance']['sources'][0]['selection']['source_ids'], original)
        self.assertTrue((full_output/'groups.svg').exists())


if __name__ == '__main__':
    unittest.main()
