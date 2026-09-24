import unittest

from sse_multivector.prominence_centroid import centroid
from sse_multivector.prominence_cosine import cosine


class CentroidTests(unittest.TestCase):
    def test_each_mask_has_equal_weight_regardless_of_vector_magnitude(self):
        mean = centroid([[3, 0], [0, 10]])
        self.assertEqual(mean, [.5, .5])
        self.assertAlmostEqual(cosine(mean, [1, 1]), 1)

    def test_rejects_empty_zero_or_inconsistent_vectors(self):
        for rows in ([], [[0, 0]], [[1, 0], [1]], [[1, 0], [-1, 0]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                centroid(rows)


if __name__ == "__main__":
    unittest.main()
