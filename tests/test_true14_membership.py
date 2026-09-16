import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'sse_multivector'
sys.path.insert(0, str(CODE))
SCRIPT = CODE / 'true_branch_membership.py'


class True14PreparationTests(unittest.TestCase):
    def test_prepare_covers_all_six_categories_and_runs_only_four_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'TRUE14'
            process = subprocess.run([sys.executable, str(SCRIPT), 'prepare', '--output', str(output)],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            all_inputs = json.loads((output / 'inputs.json').read_text())
            new_inputs = json.loads((output / 'new-inputs.json').read_text())
            self.assertEqual(len(all_inputs), 5388)
            self.assertEqual(len(new_inputs), 3592)
            grouped = {}
            for row in all_inputs:
                grouped.setdefault(row['category_title'], []).extend(m['short_id'] for m in row['masks'])
                self.assertEqual(row['id'], 'M' + hashlib.sha256(row['model_input'].encode()).hexdigest())
                self.assertEqual(row['model_input'], f'premise: {row["premise"]} hypothesis: This text is about {row["category_title"]}.')
            self.assertEqual(len(grouped), 6)
            for aliases in grouped.values():
                self.assertEqual(len(aliases), 945)
                self.assertEqual(set(aliases), {f'V{i:03d}' for i in range(1, 946)})
            self.assertEqual({r['category_title'] for r in new_inputs}, {
                'Coffee Bean Preparation', 'Having drunk coffee',
                'Appreciating Coffee for Its Flavour', '#coffeechain'})
            from true_branch_membership import verify
            verify(output)
            # Existing runs cannot be replaced, and stale frozen inputs are rejected.
            process = subprocess.run([sys.executable, str(SCRIPT), 'prepare', '--output', str(output)],
                                     capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            with (output / 'new-inputs.json').open('a') as stream:
                stream.write(' ')
            with self.assertRaises(ValueError):
                verify(output)

    def test_changed_or_missing_cached_scores_are_not_silently_reused(self):
        from true_branch_membership import plan_inputs, read
        research = CODE / 'navigation-research-v1'
        view = read(research / 'TRUE13/categories-with-mask-ids.json')
        inputs = read(research / 'TRUE12/inputs.json')
        scores = [json.loads(line) for line in (research / 'TRUE12/scores.jsonl').read_text().splitlines()]
        for case in ('missing', 'changed_text', 'changed_mask', 'duplicate', 'nonfinite'):
            changed = copy.deepcopy(scores)
            if case == 'missing': changed.pop()
            if case == 'changed_text': changed[0]['model_input'] += ' '
            if case == 'changed_mask': changed[0]['masks'][0]['fragments'] = ['changed']
            if case == 'duplicate': changed.append(changed[0])
            if case == 'nonfinite': changed[0]['entailment_score'] = float('nan')
            with self.subTest(case=case), self.assertRaises(ValueError):
                plan_inputs(view, inputs, changed)


if __name__ == '__main__':
    unittest.main()
