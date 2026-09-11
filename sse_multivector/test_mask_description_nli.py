import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mask_description_nli import prepare_pairs, independent_scores


class MaskDescriptionNLITests(unittest.TestCase):
    def test_only_exact_fragments_and_fixed_description_enter_model_input(self):
        ev = [dict(row=0, aliases=[dict(short_id='V1', note_short_id='N1',
               fragments=['hot', 'coffee'], text='hot coffee and unrelated bread',
               subject='Do not use this generated subject')])]
        fixture = dict(vectors=['V1'], descriptions=['coffee', 'bread'],
                       template='This text is about {}')
        pairs = prepare_pairs(ev, fixture)
        self.assertEqual([(p['premise'], p['hypothesis']) for p in pairs],
                         [('hot coffee', 'This text is about coffee'),
                          ('hot coffee', 'This text is about bread')])
        self.assertEqual(pairs[0]['source'], ev[0]['aliases'][0])

    def test_duplicate_or_unknown_vector_is_rejected(self):
        fixture = dict(vectors=['V1'], descriptions=['coffee'], template='{}')
        with self.assertRaisesRegex(ValueError, 'unknown vector'):
            prepare_pairs([], fixture)
        fixture['vectors'] = ['V1', 'V1']
        with self.assertRaisesRegex(ValueError, 'duplicate requested vector'):
            prepare_pairs([], fixture)

    def test_scores_are_independent_of_other_descriptions(self):
        result = independent_scores([[4.0, 0.0], [4.0, 0.0]], 0)
        self.assertEqual(result[0], result[1])
        self.assertGreater(result[0], .98)
        self.assertEqual(independent_scores([[4.0, 0.0]], 0)[0], result[0])
        self.assertAlmostEqual(independent_scores([[1004.0, 1000.0]], 0)[0], result[0])

    def test_nonfinite_or_wrong_binary_logits_rejected(self):
        for logits in [[[math.nan, 0]], [[0, 1, 2]]]:
            with self.assertRaises(ValueError):
                independent_scores(logits, 0)

    def test_cli_refuses_existing_output_before_loading_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(__file__).with_name('mask_description_nli.py')
            run = subprocess.run([sys.executable, str(script), '--output', temporary,
                                  '--fixture', '/missing', '--evidence', '/missing',
                                  '--cache', '/missing'], text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('preserve earlier experiments', run.stderr)
            self.assertEqual(list(Path(temporary).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
