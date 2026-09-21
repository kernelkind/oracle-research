"""Check the actual example responses with the decoder used in model probes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))
from selection import decode, index_post


class ContrastiveExampleTests(unittest.TestCase):
    def test_actual_prompt_examples_decode_to_intended_masks(self):
        prompt = (HERE / 'mask-prompt.md').read_text()
        source = re.search(r'<example_post>\n(.*?)\n</example_post>', prompt, re.S).group(1)
        indexed = re.search(r'<example_indexed_post>\n(.*?)\n</example_indexed_post>', prompt, re.S).group(1)
        self.assertEqual(indexed, index_post(source))
        expected = {
            'Trains': ['train', 'train'],
            'Transport': ['train', 'train'],
            'Train delays': ['train', 'behind schedule', 'train', 'late'],
            "The author's train arriving twenty minutes late": ['My train arrived twenty minutes behind schedule'],
        }
        examples = re.findall(r'<example>\n<subject>(.*?)</subject>\n<response>(.*?)</response>\n</example>', prompt, re.S)
        self.assertEqual([subject for subject, _ in examples], list(expected))
        for subject, raw in examples:
            with self.subTest(subject=subject):
                spans = decode(raw, source)
                self.assertEqual([source[s['start']:s['end']] for s in spans], expected[subject])
                if subject in ('Trains', 'Transport'):
                    self.assertEqual([s['start'] for s in spans], [source.index('train'), source.rindex('train')])

    def test_examples_are_the_only_change_from_mpv313(self):
        baseline = (HERE.parent / 'mpv3.13-draft-v1/mask-prompt.md').read_bytes()
        self.assertEqual(hashlib.sha256(baseline).hexdigest(), '0b39911a34d8f4aadc6241b0715821e3bfbda69d3eb0beeb7fac0243da26ea6a')
        revised = (HERE / 'mask-prompt.md').read_text()
        restored = re.sub(r'<examples>.*?</examples>\n\n', '', revised, count=1, flags=re.S)
        self.assertEqual(restored.encode(), baseline)


if __name__ == '__main__':
    unittest.main()
