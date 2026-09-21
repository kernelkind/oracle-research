import unittest

from check import decode, highlight


class RangeChecks(unittest.TestCase):
    def test_partial_word(self):
        spans = decode('[{"start":1,"end":4}]', '#artblog')
        self.assertEqual(highlight('#artblog', spans), '#⟦art⟧blog')

    def test_unicode_whitespace_and_repeated_word(self):
        source = '🙂\r\ntrain\ttrain  '
        spans = decode('[{"start":9,"end":14}]', source)
        self.assertEqual(highlight(source, spans), '🙂\r\ntrain\t⟦train⟧  ')

    def test_invalid_ranges_are_rejected_without_repair(self):
        for raw in (
            '[[0,1]]', '{"start":0,"end":1}',
            '[{"start":true,"end":1}]', '[{"start":-1,"end":1}]',
            '[{"start":1,"end":1}]', '[{"start":0,"end":4}]',
            '[{"start":0,"end":2},{"start":1,"end":3}]',
            '[{"start":0,"start":1,"end":2}]',
            '[{"start":0,"end":1,"text":"a"}]',
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw, 'abc')

    def test_separate_fragments_and_empty_mask(self):
        self.assertEqual(highlight('abcd', decode('[{"start":0,"end":1},{"start":3,"end":4}]', 'abcd')), '⟦a⟧bc⟦d⟧')
        self.assertEqual(decode('[]', 'abc'), [])


if __name__ == '__main__':
    unittest.main()
