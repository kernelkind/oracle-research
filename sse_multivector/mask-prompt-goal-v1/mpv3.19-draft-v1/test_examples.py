"""Validate example masks with the same decoder used in the model probes."""
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'position-selection-v4'))
from selection import decode, index_post


class ExampleTests(unittest.TestCase):
    def test_examples(self):
        prompt = (HERE / 'mask-prompt.md').read_text()
        source = re.search(r'<example_post>\n(.*?)\n</example_post>', prompt, re.S).group(1)
        indexed = re.search(r'<example_indexed_post>\n(.*?)\n</example_indexed_post>', prompt, re.S).group(1)
        self.assertEqual(indexed, index_post(source))
        expected = {
            'Bicycle repair': ['bicycle', 'repaired', 'fixed', 'bikes'],
            "The author repairing their daughter's bicycle on Saturday using secondhand parts": ["My daughter's bicycle", 'On Saturday I repaired', 'using secondhand parts'],
        }
        examples = re.findall(r'<example>\n<subject>(.*?)</subject>\n<response>(.*?)</response>\n</example>', prompt, re.S)
        self.assertEqual([subject for subject, _ in examples], list(expected))
        for subject, raw in examples:
            with self.subTest(subject=subject):
                spans = decode(raw, source)
                self.assertEqual([source[s['start']:s['end']] for s in spans], expected[subject])

    def test_only_example_block_changed(self):
        before = (HERE.parent / 'mpv3.18-draft-v1/mask-prompt.md').read_text()
        after = (HERE / 'mask-prompt.md').read_text()
        strip = lambda text: re.sub(r'<examples>.*?</examples>\n\n', '', text, count=1, flags=re.S)
        self.assertEqual(strip(before), strip(after))
        self.assertEqual(strip(after), (HERE.parent / 'mpv3.16-draft-v1/mask-prompt.md').read_text())


if __name__ == '__main__':
    unittest.main()
