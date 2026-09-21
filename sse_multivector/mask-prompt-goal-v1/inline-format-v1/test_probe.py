import unittest

from probe import parse_inline


class InlineMaskTests(unittest.TestCase):
    def test_repeated_text_uses_marker_position(self):
        self.assertEqual(
            parse_inline("train train", "train ⟦train⟧"),
            [{"start": 6, "end": 11, "byte_start": 6, "byte_end": 11, "text": "train"}],
        )

    def test_unicode_discontinuous_ranges_and_exact_whitespace(self):
        source = "🙂  café\r\n\ttrain train  "
        parsed = parse_inline(source, "🙂  ⟦café⟧\r\n\ttrain ⟦train⟧  ")
        self.assertEqual([item["text"] for item in parsed], ["café", "train"])
        for item in parsed:
            self.assertEqual(source[item["start"]:item["end"]], item["text"])
            self.assertEqual(
                source.encode()[item["byte_start"]:item["byte_end"]].decode(),
                item["text"],
            )

    def test_no_silent_copy_repairs(self):
        for response in ["⟦train⟧", "⟦Train⟧  ", "⟦train⟧ \n", "```\n⟦train⟧  \n```"]:
            with self.subTest(response=response), self.assertRaises(ValueError):
                parse_inline("train  ", response)

    def test_malformed_markings_are_rejected(self):
        for response in ["⟦train", "train⟧", "⟦⟦train⟧⟧", "⟦⟧train"]:
            with self.subTest(response=response), self.assertRaises(ValueError):
                parse_inline("train", response)

    def test_unmarked_text_can_be_preserved_without_proving_coverage(self):
        self.assertEqual(parse_inline("train", "train"), [])

    def test_source_marker_collision_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_inline("literal ⟦ marker", "literal ⟦ marker")


if __name__ == "__main__":
    unittest.main()
