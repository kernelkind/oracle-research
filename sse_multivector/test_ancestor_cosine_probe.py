import unittest

from sse_multivector.ancestor_cosine_probe import ancestor_path, score_path, marked_post


class AncestorCosineTests(unittest.TestCase):
    def test_uses_exact_saved_path_including_root_and_endpoint(self):
        subjects = [dict(note_short_id="N1", number=n, subject=n) for n in
                    ("1.10", "1.1.1", "1", "1.1", "2")]
        subjects.append(dict(note_short_id="N2", number="1", subject="other post"))
        self.assertEqual([s["number"] for s in ancestor_path(subjects, "N1", "1.1.1")],
                         ["1", "1.1", "1.1.1"])
        with self.assertRaises(ValueError):
            ancestor_path(subjects, "N1", "1.1.2")
        with self.assertRaises(ValueError):
            ancestor_path(subjects[1:], "N1", "1.10")

    def test_missing_intermediate_ancestor_is_an_error(self):
        subjects = [dict(note_short_id="N1", number=n) for n in ("1", "1.1.1")]
        with self.assertRaises(ValueError):
            ancestor_path(subjects, "N1", "1.1.1")

    def test_scores_instance_against_each_subject_and_keeps_tied_peaks(self):
        path = [dict(subject="Food"), dict(subject="Bread"), dict(subject="Sourdough bread")]
        points, peaks = score_path([2., 0.], path, [[0., 3.], [4., 0.], [1., 0.]])
        self.assertEqual([p["depth"] for p in points], [0, 1, 2])
        self.assertEqual([p["cosine"] for p in points], [0., 1., 1.])
        self.assertEqual(peaks, [1, 2])
        with self.assertRaises(ValueError):
            score_path([0., 0.], path, [[0., 3.], [4., 0.], [1., 0.]])
        with self.assertRaises(ValueError):
            score_path([float("nan"), 0.], path, [[0., 3.], [4., 0.], [1., 0.]])

    def test_post_marks_exact_utf8_spans_and_escapes_html(self):
        self.assertEqual(marked_post("☕ <bread>", [[5, 10]]), "☕ &lt;<mark>bread</mark>&gt;")


if __name__ == "__main__":
    unittest.main()
