"""Before/after review is derived from the same saved graph used by the browser."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from hierarchy_build import package_merge
from hierarchy_merge_review import build_review, export_review
from test_hierarchy_build import report_for
from test_true_graph_categories import fixture
from true_graph_merge import merge_graph


class MergeReviewTests(unittest.TestCase):
    def package(self, root, accepted, alias=False):
        values = fixture()
        canonical = values['canonical']
        if alias:
            packet = canonical['source_packets']['packets'][0]
            duplicate = deepcopy(packet['instances'][0])
            duplicate['instance'] = 'VA-alias'
            packet['instances'].append(duplicate)
            canonical['titles']['groups'][0]['instances'].append(
                dict(instance='VA-alias', fragments=duplicate['fragments']))
        for row in canonical['scores']:
            yes = (row['a_id'], row['b_id']) in accepted
            row.update(predicted=yes, generated_text='1' if yes else '0',
                       generated_token_ids=[0, 209 if yes else 632, 1])
        merged = merge_graph(**canonical)
        report = report_for(merged['naming_source_packets']) if merged['naming_source_packets']['packets'] else None
        for field in ('source', 'mapping'):
            (root / f'{field}.json').write_text(json.dumps(values[field]))
        package_merge(merged, report, root/'source.json', root/'mapping.json', root/'browser')
        return root/'browser'

    def test_review_keeps_groups_masks_answers_and_links_separate_without_mutating(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A', 'B'), ('B', 'A'), ('B', 'C')})
            before = {p.name: p.read_bytes() for p in package.iterdir()}
            review = build_review(package)
            self.assertEqual(review['labels']['item'], 'Merge')
            self.assertEqual(len(review['notes']), 1)
            item = review['notes'][0]
            self.assertEqual(item['id'], 'M01')
            self.assertIn('Group 1', item['text'])
            self.assertIn('Group 2', item['text'])
            self.assertIn('VA', item['text'])
            self.assertIn('VB', item['text'])
            self.assertNotIn('VC:', item['text'])  # child masks are not original member masks
            result = item['results'][0]
            self.assertIn('Group 1 contains Group 2: Yes', result['comment'])
            self.assertIn('Group 2 contains Group 1: Yes', result['comment'])
            self.assertIn('Children', result['output'])
            self.assertIn('  C', result['output'])
            self.assertIn('No', result['output'])  # conflicting direct rejection survives
            self.assertIn('premise:', result['comment'])
            self.assertIn('⟦', item['model_input'])
            self.assertIn('café ⟦coffee⟧ milk tea', item['model_input'])
            self.assertEqual({p.name: p.read_bytes() for p in package.iterdir()}, before)
            export_review(package, Path(directory)/'review.json')
            with self.assertRaises(FileExistsError):
                export_review(package, Path(directory)/'review.json')

    def test_long_cycle_shows_direct_no_without_claiming_pairwise_equivalence(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A','B'), ('B','C'), ('C','A')})
            item = build_review(package)['notes'][0]
            self.assertIn('Group 1 contains Group 3: No', item['results'][0]['comment'])
            answers = [line for line in item['results'][0]['comment'].splitlines()
                       if line.endswith((': Yes', ': No'))]
            self.assertEqual(len(answers), 6)

    def test_identical_masks_in_a_group_keep_aliases_without_repeating_text(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A','B'), ('B','A')}, alias=True)
            before = build_review(package)['notes'][0]['text']
            self.assertIn('VA, VA-alias: ⟦coffee⟧', before)
            self.assertEqual(before.count('⟦coffee⟧'), 1)

    def test_no_cycle_is_not_presented_as_a_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A','B')})
            with self.assertRaisesRegex(ValueError, 'no cycle merges'):
                build_review(package)

    def test_summary_and_known_decision_are_separate_from_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A','B'), ('B','A')})
            decisions = {'decisions': [{'members': ['B', 'A'], 'decision': 'keep_separate',
                                        'source': 'User explicitly rejected this merge.'}]}
            item = build_review(package, decisions)['notes'][0]
            self.assertIn('Should they stay separate?', item['summary'])
            self.assertIn('Known decision: Keep separate.', item['summary'])
            for absent in ('VA', 'premise:', 'Parents', 'posts'):
                self.assertNotIn(absent, item['summary'])
            self.assertIn('User explicitly rejected', item['results'][0]['comment'])
            undecided = build_review(package)['notes'][0]['summary']
            self.assertIn('Not yet decided.', undecided)
            for bad in ({'members': ['A','C'], 'decision': 'keep_separate', 'source': 'User'},
                        {'members': ['A','B'], 'decision': 'unknown', 'source': 'User'},
                        {'members': ['A','B'], 'decision': 'keep_separate', 'source': ''}):
                with self.assertRaises(ValueError):
                    build_review(package, {'decisions': [bad]})

    def test_tampered_named_graph_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.package(Path(directory), {('A','B'), ('B','A'), ('B','C')})
            path = package/'named-graph.json'
            data = json.loads(path.read_text())
            data['graph']['transitive_reduced_edges'] = []
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                build_review(package)


if __name__ == '__main__':
    unittest.main()
