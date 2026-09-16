"""Package exact mask differences, not note differences, through the real browser."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / 'sse_multivector'
RUN = CODE / 'navigation-research-v1/TRUE13'
COFFEE = 'S9c440e7f47'
sys.path.insert(0, str(CODE))
from true_unmatched_masks import build_view


def read(path):
    return json.loads(path.read_text())


def identity(mask):
    return mask['note_id'], tuple(map(tuple, mask['byte_spans']))


class UnmatchedMasksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name) / 'view'
        cls.inputs = [RUN / 'categories.json', RUN / 'native-notes.json',
                      CODE / 'navigation-research-v1/TRUE12/scores.jsonl',
                      CODE / 'real-note-fine-segmentation-v1/reviewed-input.json']
        cls.hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in cls.inputs}
        result = subprocess.run([sys.executable, str(CODE / 'true_unmatched_masks.py'),
                                 '--output', str(cls.output)], cwd='/',
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.view = read(cls.output / 'categories.json')
        cls.masks = read(cls.output / 'masks.json')

    def test_exact_masks_excluded_recursively_not_entire_notes(self):
        nodes = {n['node_id']: n for n in read(RUN / 'categories.json')['nodes']}
        descendants, pending = set(), list(nodes[COFFEE]['children'])
        while pending:
            key = pending.pop()
            if key not in descendants:
                descendants.add(key)
                pending.extend(nodes[key]['children'])
        native = {n['group']: n['matched_instances'] for n in read(RUN / 'native-notes.json')['nodes']}
        parent = list(native[COFFEE])
        for line in self.inputs[2].read_text().splitlines():
            row = json.loads(line)
            if row['category_id'] == COFFEE and row['entailment_score'] > 0.142:
                parent.extend(row['masks'])
        excluded = {identity(m) for child in descendants for m in native[child]}
        expected = {identity(m) for m in parent} - excluded
        self.assertEqual({identity(m) for m in self.masks}, expected)
        self.assertEqual(len(self.masks), 52)
        self.assertEqual(len(self.view['notes']), 17)
        self.assertTrue({'N071', 'N086', 'N094', 'N095'} <= set(self.view['nodes'][0]['note_ids']))

    def test_inline_ranges_are_only_the_union_of_remaining_masks(self):
        expected = {}
        source = {n['note_id']: n['text'] for n in read(self.inputs[3])['notes']}
        for mask in self.masks:
            expected.setdefault(mask['note_short_id'], set()).update(map(tuple, mask['byte_spans']))
            encoded = source[mask['note_id']].encode('utf-8')
            self.assertEqual([encoded[a:b].decode('utf-8') for a, b in mask['byte_spans']], mask['fragments'])
        self.assertEqual(self.view['note_masks'][COFFEE],
                         {n: [list(s) for s in sorted(spans)] for n, spans in expected.items()})
        self.assertEqual(self.view['nodes'][0]['children'], [])
        self.assertEqual(set(self.view['nodes'][0]['note_ids']), set(expected))

    def test_production_browser_accepts_saved_full_notes_and_masks(self):
        result = subprocess.run([str(ROOT / 'target/infomap-review-build/debug/sse-subject-navigation'),
            '--categories', str(self.output / 'categories.json'), str(self.inputs[3]), '--check'],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('17 notes', result.stdout)

    def test_inputs_are_preserved_and_output_is_not_overwritten(self):
        self.assertEqual(self.hashes, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.inputs})
        before = (self.output / 'categories.json').read_bytes()
        result = subprocess.run([sys.executable, str(CODE / 'true_unmatched_masks.py'),
                                 '--output', str(self.output)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.output / 'categories.json').read_bytes(), before)

    def test_grandchild_match_does_not_remove_overlaps_other_occurrences_or_other_notes(self):
        texts = {'one': 'coffee beans coffee', 'two': 'coffee'}
        source = json.dumps({'notes': [{'note_id': n, 'text': t} for n, t in texts.items()]}).encode()

        def mask(key, note, start, end):
            return dict(instance=key, note_id=note, byte_spans=[[start, end]],
                        fragments=[texts[note][start:end]])

        a = mask('A', 'one', 0, 6)
        parents = [a, mask('B', 'one', 0, 12), mask('C', 'one', 13, 19),
                   mask('D', 'two', 0, 6), mask('E', 'one', 13, 19)]
        spec = {'source_sha256': hashlib.sha256(source).hexdigest(),
                'nodes': [{'node_id': COFFEE, 'label': 'Coffee', 'children': ['child']},
                          {'node_id': 'child', 'label': 'Child', 'children': ['grandchild']},
                          {'node_id': 'grandchild', 'label': 'Grandchild', 'children': []}],
                'notes': [{'note_id': 'one', 'note_short_id': 'N1'},
                          {'note_id': 'two', 'note_short_id': 'N2'}]}
        native = {'nodes': [{'group': COFFEE, 'matched_instances': parents},
                            {'group': 'child', 'matched_instances': []},
                            {'group': 'grandchild', 'matched_instances': [a]}]}
        view, remaining = build_view(spec, native, [], source)
        self.assertEqual([m['ids'] for m in remaining], [['B'], ['C', 'E'], ['D']])
        self.assertEqual(view['note_masks'][COFFEE], {'N1': [[0, 12], [13, 19]], 'N2': [[0, 6]]})


if __name__ == '__main__':
    unittest.main()
