import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mask_description_relevance import prepare_queries, relevance_scores


class MaskDescriptionRelevanceTests(unittest.TestCase):
    def test_query_is_description_and_passage_is_exact_mask(self):
        source = dict(fragments=['hot', 'coffee'], text='hot coffee and unrelated bread',
                      subject='This generated subject must not become input')
        saved = [dict(vector='V1', description='coffee', premise='hot coffee',
                      hypothesis='This text is about coffee', source=source,
                      logits=[100, -100], score=1)]
        rows = prepare_queries(saved)
        self.assertEqual(rows, [dict(vector='V1', description='coffee',
                                   query='coffee', passage='hot coffee', source=source)])
        self.assertNotIn('score', rows[0])
        self.assertNotIn('hypothesis', rows[0])

    def test_source_mismatch_and_duplicate_pair_are_rejected(self):
        row = dict(vector='V1', description='coffee', premise='coffee',
                   source=dict(fragments=['bread']))
        with self.assertRaisesRegex(ValueError, 'source fragments'):
            prepare_queries([row])
        row['source']['fragments'] = ['coffee']
        with self.assertRaisesRegex(ValueError, 'duplicate pair'):
            prepare_queries([row, row])

    def test_scores_do_not_compete_across_descriptions(self):
        self.assertEqual(relevance_scores([[0], [0]]), [0.5, 0.5])
        self.assertEqual(relevance_scores([[1000], [-1000]]), [1, 0])
        for rows in [[[0, 1]], [[math.nan]], [[math.inf]]]:
            with self.assertRaises(ValueError):
                relevance_scores(rows)

    def test_cli_refuses_overwriting_before_model_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run([sys.executable, str(Path(__file__).with_name(
                'mask_description_relevance.py')), '--output', directory,
                '--input', '/missing', '--fixture', '/missing', '--cache', '/missing'],
                text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('preserve earlier experiments', run.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
