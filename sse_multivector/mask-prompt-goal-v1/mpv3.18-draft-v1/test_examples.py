"""Validate the prompt's examples using the existing word-position decoder."""
import hashlib
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))
from selection import decode, index_post


class ContrastiveExampleTests(unittest.TestCase):
    def test_actual_examples_decode_to_approved_masks(self):
        prompt = (HERE / 'mask-prompt.md').read_text()
        source = re.search(r'<example_post>\n(.*?)\n</example_post>', prompt, re.S).group(1)
        indexed = re.search(r'<example_indexed_post>\n(.*?)\n</example_indexed_post>', prompt, re.S).group(1)
        self.assertEqual(source, 'My train arrived twenty minutes late.')
        self.assertEqual(indexed, index_post(source))
        expected = {
            'Trains': ['train'],
            "The author's train arriving twenty minutes late": ['My train arrived twenty minutes late'],
        }
        examples = re.findall(r'<example>\n<subject>(.*?)</subject>\n<response>(.*?)</response>\n</example>', prompt, re.S)
        self.assertEqual([subject for subject, _ in examples], list(expected))
        for subject, raw in examples:
            with self.subTest(subject=subject):
                spans = decode(raw, source)
                self.assertEqual([source[s['start']:s['end']] for s in spans], expected[subject])

    def test_only_examples_added_to_mpv316(self):
        baseline = (HERE.parent / 'mpv3.16-draft-v1/mask-prompt.md').read_bytes()
        self.assertEqual(hashlib.sha256(baseline).hexdigest(), '9b07da9be7fd9e2f3aa5b5543d97d3e03019046acded28374791cf1c30cf8348')
        revised = (HERE / 'mask-prompt.md').read_text()
        restored = re.sub(r'<examples>.*?</examples>\n\n', '', revised, count=1, flags=re.S)
        self.assertEqual(restored.encode(), baseline)


if __name__ == '__main__':
    unittest.main()
