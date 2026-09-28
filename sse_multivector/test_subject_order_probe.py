"""Tests for the subject-vector/order diagnostic, including real OPHAC calls."""

import unittest

import numpy as np

from sse_multivector.subject_order_probe import build_inputs, cosine_distances, merge_sequence


class SubjectOrderTests(unittest.TestCase):
    def sample(self):
        subjects = [
            dict(number="1", subject="Food", id="M1", byte_spans=[], fragments=[]),
            dict(number="1.1", subject="Bread", id="M2", byte_spans=[[0, 5]], fragments=["bread"]),
            dict(number="2", subject="Bread", id="M3", byte_spans=[[0, 5]], fragments=["bread"]),
        ]
        posts = {"notes": [dict(note_id="a" * 64, text="bread", subjects=subjects)]}
        vectors = {"vectors": [dict(note_id="a" * 64, note_short_id="N001", vector_id="v1",
                                    short_id="V0001", byte_spans=[[0, 5]])]}
        return posts, vectors

    def test_preserves_occurrences_empty_masks_and_original_edges(self):
        inputs, request = build_inputs(*self.sample(), ["N001"])
        self.assertEqual(len(inputs["subjects"]), 3)
        self.assertEqual(len(request["notes"]), 2)  # Cache encoding, not graph entries.
        self.assertEqual(inputs["edges"], [[0, 1]])
        self.assertEqual(inputs["subjects"][0]["mask_vector_ids"], [])
        self.assertEqual(inputs["subjects"][1]["mask_vector_ids"], ["v1"])
        self.assertEqual(inputs["subjects"][2]["mask_vector_ids"], ["v1"])
        self.assertEqual(inputs["subjects"][1]["encoding_id"], inputs["subjects"][2]["encoding_id"])

    def test_rejects_missing_post_or_parent_instead_of_silently_dropping(self):
        posts, vectors = self.sample()
        with self.assertRaises(ValueError):
            build_inputs(posts, vectors, ["N002"])
        posts["notes"][0]["subjects"][1]["number"] = "3.1"
        with self.assertRaises(ValueError):
            build_inputs(posts, vectors, ["N001"])

    def test_cosine_distances_are_symmetric_zero_diagonal_and_scale_invariant(self):
        d = cosine_distances(np.array([[1., 0.], [2., 0.], [0., 1.]]))
        np.testing.assert_allclose(d, [[0, 0, 1], [0, 0, 1], [1, 1, 0]])
        for v in ([[0., 0.], [1., 1.]], [[float("nan"), 0.], [1., 1.]]):
            with self.assertRaises(ValueError):
                cosine_distances(np.array(v))

    def test_real_ophac_preserves_two_parents_and_is_deterministic(self):
        # Two separate parents whose equivalent children can merge.
        d = np.array([[0, .9, .9, .9], [.9, 0, .9, 0], [.9, .9, 0, .9], [.9, 0, .9, 0]])
        edges = [[0, 1], [2, 3]]
        result = merge_sequence(d, edges, constrained=True)
        self.assertEqual(result, merge_sequence(d, edges, constrained=True))
        first = result["steps"][0]
        self.assertEqual(first["merged"], [1, 3])
        self.assertEqual(first["edges"], [[0, 1], [2, 1]])
        self.assertEqual(first["parent_collapses"], 0)
        self.assertEqual(first["new_reachable_pairs"], [[0, 3], [2, 1]])
        self.assertTrue(all(s["acyclic"] for s in result["steps"]))

    def test_strict_ancestry_blocks_identical_vectors_but_control_does_not(self):
        d = np.zeros((3, 3))
        edges = [[0, 1], [1, 2]]
        constrained = merge_sequence(d, edges, constrained=True)
        control = merge_sequence(d, edges, constrained=False)
        self.assertEqual(constrained["steps"], [])
        self.assertEqual(len(control["steps"]), 2)
        self.assertEqual(control["steps"][-1]["parent_collapses"], 3)

    def test_rechecks_reachability_after_each_merge(self):
        # Initially 1 and 2 are unrelated; merging 0 and 3 creates 2 -> (0,3) -> 1.
        # The newly created path must then prohibit merging 1 and 2.
        d = np.array([[0, .9, .9, .01], [.9, 0, .02, .9],
                      [.9, .02, 0, .9], [.01, .9, .9, 0]])
        result = merge_sequence(d, [[0, 1], [2, 3]], constrained=True)
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["merged"], [0, 3])
        self.assertEqual(result["steps"][0]["edges"], [[0, 1], [2, 0]])

    def test_rejects_cycles_and_invalid_distances(self):
        with self.assertRaises(ValueError):
            merge_sequence(np.zeros((2, 2)), [[0, 1], [1, 0]], constrained=True)
        with self.assertRaises(ValueError):
            merge_sequence(np.array([[0, 1], [2, 0]]), [], constrained=True)


if __name__ == "__main__":
    unittest.main()
