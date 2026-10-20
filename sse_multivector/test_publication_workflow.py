"""Oracle review commands keep compact public results in sync."""
import json
import unittest

from sse_multivector import test_experiment as fixtures


class PublicationReviewTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    calls = fixtures.ExperimentTests.calls

    def results(self, name):
        return [json.loads(line) for line in
                (self.root/name/'publication/results.jsonl').read_text().splitlines()]

    def test_manual_reviews_refresh_compact_answers_with_distinct_roles(self):
        self.prepare()
        self.cli('run', 'E1')
        original = self.results('E1')[0]['output']
        calls = self.calls()
        self.cli('review', 'E1', '--case', 'one', '--role', 'agent',
                 '--verdict', 'reject', '--comment', 'Agent finding')
        self.cli('review', 'E1', '--case', 'one', '--role', 'user',
                 '--verdict', 'accept', '--comment', 'User decision')
        first = self.results('E1')[0]
        self.assertEqual(first['output'], original)
        self.assertEqual([(r['role'], r['verdict']) for r in first['reviews']],
                         [('agent', 'reject'), ('user', 'accept')])
        self.assertTrue(all(r['current'] for r in first['reviews']))
        self.assertEqual(self.calls(), calls)

    def test_imported_reviews_refresh_compact_results_without_original_paths(self):
        self.prepare()
        self.cli('run', 'E1')
        self.cli('review', 'E1', '--case', 'one', '--role', 'agent',
                 '--verdict', 'reject', '--comment', 'Saved finding')
        self.cli('prepare', 'E2', '--from', 'E1')
        self.cli('run', 'E2')
        calls = self.calls()
        self.cli('review', 'E2', '--from-experiment', 'E1')
        first = self.results('E2')[0]
        self.assertEqual(first['reviews'][0]['comment'], 'Saved finding')
        self.assertEqual(first['reviews'][0]['role'], 'agent')
        exported = b''.join(path.read_bytes() for path in
                            (self.root/'E2/publication').iterdir())
        self.assertNotIn(str(self.root).encode(), exported)
        self.assertNotIn(b'REVIEW ONLY', exported)
        self.assertEqual(self.calls(), calls)


class PublicationExportCliTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli

    def test_partial_validation_stage_exports_saved_answers_without_results_file(self):
        stage = self.root/'run/baseline'
        (stage/'note-0000').mkdir(parents=True)
        (stage/'note-0000/subjects.json').write_text(json.dumps(dict(
            note_id='post-one', answer=dict(raw='{"subjects":[]}', tokens=5, truncated=False))))
        self.cli('export-evaluation-results', stage, '--kind', 'validation')
        output = self.root/'run/publication/evaluations/baseline'
        rows = [json.loads(line) for line in (output/'results.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['note_id'], 'post-one')
        self.assertEqual(rows[0]['answer']['raw'], '{"subjects":[]}')

    def test_numerical_cli_exports_final_merge_tree_without_distances(self):
        source = self.write('merge.json', dict(schema_version='merge-rule-experiment-v1',
            canonical_unique_ids=['a', 'b'], alias_groups=[['a'], ['b']],
            merges=[dict(id=2, left=0, right=1, size=2, merge_score=.7)],
            distances=[[1234.5]], summary={'notes': 2}))
        self.cli('export-numerical-results', source, '--family', 'merge-rule')
        output = self.root/'publication/merge'
        rows = [json.loads(line) for line in (output/'results.jsonl').read_text().splitlines()]
        self.assertIn(dict(type='merge', id=2, left=0, right=1, size=2, merge_score=.7), rows)
        self.assertNotIn('1234.5', (output/'results.jsonl').read_text())


if __name__ == '__main__':
    unittest.main()
