import json
import unittest

import study


class InputRenderingTests(unittest.TestCase):
    def test_preserves_selected_occurrences_repetitions_and_json_characters(self):
        text = '“baby”\n#baby #nostrbaby'
        spans = [(8, 12), (19, 23)]
        data = study.render_input(text, spans)
        self.assertEqual(["baby", "baby"], data["mask"])
        self.assertEqual('“baby”\n#⟦baby⟧ #nostr⟦baby⟧', data["marked_post"])
        self.assertEqual(data, json.loads(json.dumps(data, ensure_ascii=False)))

    def test_utf8_byte_offsets_are_not_character_offsets(self):
        self.assertEqual([(2, 8)], study.character_spans('☕ coffee', [[4, 10]]))
        with self.assertRaises(UnicodeDecodeError):
            study.character_spans('☕ coffee', [[1, 3]])

    def test_rejects_empty_overlapping_or_out_of_bounds_masks(self):
        for spans in ([], [(1, 1)], [(0, 4), (2, 5)], [(0, 100)], [(-1, 2)]):
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                study.render_input('coffee', spans)

    def test_score_contract(self):
        self.assertEqual(85, study.decode_score('{"prominence":85}'))
        for raw in ('{"prominence":true}', '{"prominence":101}', '{"prominence":1.5}',
                    '{"prominence":5,"reason":"extra"}', '{"prominence":1,"prominence":2}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                study.decode_score(raw)


if __name__ == '__main__':
    unittest.main()
