"""The viewer packet must preserve the completed TRUE04 experiment exactly."""
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'navigation-research-v1' / 'TRUE04'


class TRUE04ReviewPacketTests(unittest.TestCase):
    def test_packet_contains_every_incorrect_or_ambiguous_pair_and_its_raw_directions(self):
        packet = json.loads((RUN / 'review-pairs.json').read_text())
        judgments = json.loads((RUN / 'title-pair-judgments.json').read_text())['pairs']
        scores = [json.loads(line) for line in (RUN / 'scores.jsonl').read_text().splitlines()]
        expected = {(j['a'], j['b']): j for j in judgments if j['judgment'] != 'valid'}
        self.assertEqual(packet['schema_version'], 1)
        self.assertEqual(packet['experiment'], 'TRUE04')
        self.assertEqual(packet['threshold'], 0.142)
        self.assertEqual(len(packet['items']), 11)
        self.assertEqual(len(expected), 11)
        self.assertEqual([(i['item_id'], i['assessment']) for i in packet['items']],
                         [(f'I{i:02}', 'Incorrect') for i in range(1, 7)] +
                         [(f'A{i:02}', 'Ambiguous') for i in range(1, 6)])
        self.assertEqual({(i['a'], i['b']) for i in packet['items']}, set(expected))
        original_ids = []
        for item in packet['items']:
            key = item['a'], item['b']
            judgment = expected[key]
            self.assertEqual(item['reason'], judgment['rationale'])
            self.assertEqual(item['assessment'], {'invalid': 'Incorrect', 'ambiguous': 'Ambiguous'}[judgment['judgment']])
            original = [s for s in scores if (s['a'], s['b']) == key and s['threshold_predicted']]
            projected = [dict(id=s['id'], a_id=s['a_id'], b_id=s['b_id'],
                              native=s['predicted'], score=s['entailment_score'],
                              cutoff=s['threshold_predicted'], model_input=s['model_input']) for s in original]
            self.assertEqual(item['decisions'], projected)
            original_ids.extend(d['id'] for d in item['decisions'])
        self.assertEqual(len(original_ids), 15)
        self.assertEqual(len(set(original_ids)), 15)
        nostr_food = next(i for i in packet['items'] if (i['a'], i['b']) == ('Nostr', 'Food'))
        self.assertEqual(len({d['score'] for d in nostr_food['decisions']}), 2)

    def test_launcher_is_self_locating_and_does_not_run_inference(self):
        launcher = ROOT / 'run-true04-review.sh'
        text = launcher.read_text()
        checked = subprocess.run(['bash', '-n', str(launcher)], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn('BASH_SOURCE[0]', text)
        self.assertIn('target/release/true-review', text)
        self.assertIn('navigation-research-v1/TRUE04/review-pairs.json', text)
        self.assertIn('"$@"', text)
        self.assertNotIn('true_all_titles_probe', text)


if __name__ == '__main__':
    unittest.main()
