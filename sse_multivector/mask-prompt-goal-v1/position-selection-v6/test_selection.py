import importlib.util
import json
from pathlib import Path
import re
import unittest

from selection import decode, index_post


class MaskSelectionTests(unittest.TestCase):
    def test_whole_words_and_partial_word(self):
        source = 'using secondhand parts.'
        self.assertEqual(
            decode('{"mask":[[1,2],{"word":3,"text":"parts"}]}', source),
            [{'start': 0, 'end': 16}, {'start': 17, 'end': 22}],
        )

    def test_repeated_words_are_selected_by_position(self):
        source = 'I train dogs. The train arrived.'
        self.assertEqual(index_post(source), '[1]I [2]train [3]dogs. [4]The [5]train [6]arrived.')
        self.assertEqual(decode('{"mask":[[5,5]]}', source), [{'start': 18, 'end': 23}])

    def test_unicode_and_original_whitespace(self):
        source = 'é🍅\r\n\tred  tomatoes!'
        self.assertEqual(index_post(source), '[1]é🍅\r\n\t[2]red  [3]tomatoes!')
        self.assertEqual(decode('{"mask":[[1,3]]}', source), [{'start': 0, 'end': len(source)}])
        self.assertEqual(decode('{"mask":[{"word":1,"text":"🍅"}]}', source), [{'start': 1, 'end': 2}])

    def test_repeated_hashtag_parts_in_different_words(self):
        source = '#baby #nostrbaby'
        self.assertEqual(
            decode('{"mask":[{"word":1,"text":"baby"},{"word":2,"text":"baby"}]}', source),
            [{'start': 1, 'end': 5}, {'start': 12, 'end': 16}],
        )

    def test_distinct_parts_of_same_word(self):
        self.assertEqual(
            decode('{"mask":[{"word":1,"text":"art"},{"word":1,"text":"blog"}]}', '#artblog'),
            [{'start': 1, 'end': 4}, {'start': 4, 'end': 8}],
        )

    def test_empty_mask(self):
        for source in ['', '   ', 'a real post']:
            with self.subTest(source=source):
                self.assertEqual(decode('{"mask":[]}', source), [])

    def test_rejects_ambiguous_including_overlapping_matches(self):
        for source, part in [('#artart', 'art'), ('banana', 'ana'), ('aaa', 'aa')]:
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'ambiguous'):
                decode(json.dumps({'mask': [{'word': 1, 'text': part}]}), source)

    def test_no_search_in_another_word_or_text_normalization(self):
        for source, part in [('coffee tea', 'tea'), ('Coffee', 'coffee'), ('café', 'cafe\u0301')]:
            with self.subTest(source=source), self.assertRaises(ValueError):
                decode(json.dumps({'mask': [{'word': 1, 'text': part}]}), source)

    def test_rejects_bad_shape_bounds_order_overlap_and_empty_text(self):
        invalid = [
            '[]', '{}', 'null', '{"mask":null}', '{"mask":[],"extra":1}',
            '{"mask":[],"mask":[]}', '{"mask":[[1,1]]',
            '{"mask":[1]}', '{"mask":[[]]}', '{"mask":[[1]]}', '{"mask":[[1,1,1]]}',
            '{"mask":[[true,1]]}', '{"mask":[[1.0,1]]}', '{"mask":[[0,1]]}',
            '{"mask":[[-1,1]]}', '{"mask":[[1,4]]}', '{"mask":[[2,1]]}',
            '{"mask":[[2,2],[1,1]]}', '{"mask":[[1,2],[2,2]]}',
            '{"mask":[[1,1],{"word":1,"text":"one"}]}',
            '{"mask":[{"word":1,"text":"o"},[1,1]]}',
            '{"mask":[{"word":1,"text":"on"},{"word":1,"text":"ne"}]}',
            '{"mask":[{"word":1,"text":"ne"},{"word":1,"text":"o"}]}',
            '{"mask":[{"word":1,"text":""}]}', '{"mask":[{"word":1,"text":" "}]}',
            '{"mask":[{"word":1,"text":null}]}', '{"mask":[{"word":1,"text":2}]}',
            '{"mask":[{"word":true,"text":"one"}]}', '{"mask":[{"word":1.0,"text":"one"}]}',
            '{"mask":[{"word":0,"text":"one"}]}', '{"mask":[{"word":4,"text":"one"}]}',
            '{"mask":[{"word":1}]}', '{"mask":[{"text":"one"}]}',
            '{"mask":[{"word":1,"text":"one","extra":0}]}',
            '{"mask":[{"word":1,"word":2,"text":"one"}]}',
            '{"mask":[{"word":1,"text":"one","text":"two"}]}',
            '{"mask":[{"word":1,"text":"one two"}]}',
            '{"mask":[{"word":1,"text":"⟦one⟧"}]}',
            '{"mask":[{"start":1,"end":1}]}',
            '```json\n{"mask":[]}\n```',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw, 'one two three')

    def test_invalid_never_becomes_empty_mask(self):
        with self.assertRaises(ValueError):
            decode('{"mask":[[1,1]]}', '')
        with self.assertRaises(ValueError):
            decode('{"mask":[{"word":1,"text":"missing"}]}', 'present')

    def test_all_approved_examples_preserve_selected_characters(self):
        root = Path(__file__).resolve().parent.parent
        spec = importlib.util.spec_from_file_location('old_selection', root / 'position-selection-v4/selection.py')
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)

        def selections(version, decoder):
            prompt = (root / f'{version}-draft-v1/mask-prompt.md').read_text()
            result = []
            for match in re.finditer(r'<(example_post|response)>\s*(.*?)\s*</\1>', prompt, re.S):
                if match[1] == 'example_post':
                    source = match[2]
                else:
                    spans = decoder(match[2], source)
                    result.append((source, [i for s in spans for i in range(s['start'], s['end']) if not source[i].isspace()]))
            return result

        previous = selections('mpv3.27', old.decode)
        self.assertEqual(len(previous), 6)
        self.assertEqual(selections('mpv3.28', decode), previous)


if __name__ == '__main__':
    unittest.main()
