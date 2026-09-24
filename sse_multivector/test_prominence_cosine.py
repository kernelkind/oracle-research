import unittest

from sse_multivector.prominence_cosine import cosine, rank_rows


class ProminenceCosineTests(unittest.TestCase):
    def test_cosine_is_normalized_and_product_is_unclipped(self):
        self.assertAlmostEqual(cosine([3, 4], [6, 8]), 1)
        self.assertAlmostEqual(cosine([1, 0], [0, 3]), 0)
        self.assertAlmostEqual(cosine([1, 0], [-1, 0]), -1)
        with self.assertRaises(ValueError):
            cosine([0, 0], [1, 0])
        with self.assertRaises(ValueError):
            cosine([1], [1, 2])

    def test_three_rankings_preserve_cases_and_distinguish_the_product(self):
        rows = [dict(id="a", prominence=100, cosine=.2),
                dict(id="b", prominence=60, cosine=.8),
                dict(id="c", prominence=0, cosine=1),
                dict(id="d", prominence=90, cosine=-.1)]
        result = rank_rows(rows)
        self.assertEqual(result["prominence"], ["a", "d", "b", "c"])
        self.assertEqual(result["cosine"], ["c", "b", "a", "d"])
        self.assertEqual(result["product"], ["b", "a", "c", "d"])
        self.assertEqual(rows[-1]["product"], -9)


if __name__ == "__main__":
    unittest.main()
