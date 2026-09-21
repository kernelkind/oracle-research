import json
import unittest

from selection import decode, index_post


class WordSelectionTests(unittest.TestCase):
    def test_ids_select_occurrence_without_searching(self):
        source = 'I train dogs. The train arrived.'
        self.assertEqual(index_post(source), '[1]I [2]train [3]dogs. [4]The [5]train [6]arrived.')
        self.assertEqual(decode('[{"start":5,"end":5}]', source), [{'start': 18, 'end': 23}])

    def test_range_preserves_original_unicode_and_whitespace(self):
        source = 'é🍅\r\n\tred  tomatoes!'
        self.assertEqual(index_post(source), '[1]é🍅\r\n\t[2]red  [3]tomatoes!')
        self.assertEqual(decode('[{"start":1,"end":3}]', source), [{'start': 0, 'end': len(source)}])

    def test_partial_word_and_repeated_substrings_are_unambiguous(self):
        source = '#artart'
        raw = json.dumps([
            {'start': 1, 'end': 1, 'start_marked': '#⟦art⟧art'},
            {'start': 1, 'end': 1, 'start_marked': '#art⟦art⟧'},
        ])
        self.assertEqual(decode(raw, source), [{'start': 1, 'end': 4}, {'start': 4, 'end': 7}])

    def test_partial_endpoints_of_range(self):
        source = '(red tea).'
        raw = '[{"start":1,"end":2,"start_marked":"(⟦red⟧","end_marked":"⟦tea⟧)."}]'
        self.assertEqual(decode(raw, source), [{'start': 1, 'end': 8}])

    def test_rejects_malformed_ranges_and_guesses(self):
        invalid = [
            '{}', '[1]', '[{"start":true,"end":1}]', '[{"start":0,"end":1}]',
            '[{"start":1,"end":4}]', '[{"start":2,"end":1}]',
            '[{"start":1,"start":2,"end":2}]', '[{"start":1,"end":1,"extra":1}]',
            '[{"start":1,"end":1,"start_marked":"⟦different⟧"}]',
            '[{"start":1,"end":1,"start_marked":"⟦⟧one"}]',
            '[{"start":1,"end":1,"start_marked":"⟦o⟧⟦ne⟧"}]',
            '[{"start":1,"end":1,"start_marked":null}]',
            '[{"start":1,"end":1,"end_marked":"⟦one⟧"}]',
            '[{"start":1,"end":2,"start_marked":"⟦on⟧e"}]',
            '[{"start":1,"end":2,"end_marked":"t⟦wo⟧"}]',
            '[{"start":2,"end":2},{"start":1,"end":1}]',
            '[{"start":1,"end":2},{"start":2,"end":2}]',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw, 'one two three')

    def test_marker_collision_fails_before_inference(self):
        with self.assertRaises(ValueError):
            index_post('already ⟦marked⟧')

    def test_empty_selection(self):
        self.assertEqual(decode('[]', ''), [])


if __name__ == '__main__':
    unittest.main()
