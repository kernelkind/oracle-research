"""The saved selection must implement the approved overlapping coverage draws."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'sse_multivector/frontier-model-comparison-v1/english-selection-v2'


class EnglishCoverageV2Test(unittest.TestCase):
    def generated(self):
        result = subprocess.run(['python3', str(HERE / 'select.py')], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_sixty_per_form_without_general_quota(self):
        result = self.generated()
        report = result['coverage.json']
        rows = result['audit.json']['notes']
        self.assertEqual(len(report['categories']), 16)
        self.assertNotIn('general', report['draws'])
        selected = {r['note_id'] for r in rows if r['selected']}
        union = set()
        for category in report['categories']:
            code = category['id']
            draw = report['draws'][code]
            self.assertEqual(len(draw), 60, code)
            self.assertEqual(len(set(draw)), 60, code)
            union.update(draw)
            actual = [r for r in rows if r['selected'] and code in r['forms']]
            self.assertEqual(category['selected_notes'], len(actual))
            self.assertGreaterEqual(len(actual), 60)
        self.assertEqual(selected, union)
        self.assertFalse(report['model_calls_made'])

    def test_sources_review_decisions_and_known_exclusions(self):
        result = self.generated()
        source = json.loads((HERE / 'reviewed-pool.json').read_text())['notes']
        prior = set(json.loads((HERE.parent / 'english-selection-v1/prior-prompt-note-ids.json').read_text())['note_ids'])
        selected = result['selection.json']['notes']
        self.assertEqual(len(selected), len({n['note_id'] for n in selected}))
        for note in selected:
            original = source[note['source']['index'] - 1]
            self.assertEqual((note['note_id'], note['text']), (original['note_id'], original['text']))
            self.assertTrue(original['include_in_pool'])
            self.assertNotIn(note['note_id'], prior)
        audit = result['audit.json']['notes']
        self.assertEqual(len({r['template_key'] for r in audit if r['selected']}), len(selected))

    def test_small_sampler_is_only_selected_originals(self):
        result = self.generated()
        selected = {n['id']: n for n in result['selection.json']['notes']}
        sample = result['sampler.json']['notes']
        self.assertGreaterEqual(len(sample), 6)
        self.assertLessEqual(len(sample), 12)
        for note in sample:
            self.assertEqual(note, selected[note['id']])

    def test_saved_artifacts_replay_exactly(self):
        result = subprocess.run(['python3', str(HERE / 'select.py'), '--check'], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
