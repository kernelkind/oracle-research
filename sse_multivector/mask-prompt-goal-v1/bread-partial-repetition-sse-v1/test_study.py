"""Input/collection checks for the BPRv1 experiment, without neural inference."""

import json
from pathlib import Path
import tempfile
import unittest

import study
from sse_multivector.worker import _load_request


class StudyTests(unittest.TestCase):
    def test_prepared_masks_preserve_saved_baseline_and_only_add_declared_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            study.prepare(output)
            _, notes = _load_request(output / "worker-request.json")
            manifest = json.loads((output / "inputs.json").read_text())
            focal = next(note for note in notes if note.note_id == manifest["note_id"])
            self.assertEqual(len(focal.subjects), 5)
            base = set(focal.subjects[0].byte_spans)
            self.assertEqual(len(base), 2)
            self.assertEqual(manifest["variants"]["base"]["fragments"], [
                "An Irish soda bread recipe I tried out recently,",
                "I was very pleased to see this recipe turned out great!",
            ])
            for subject in focal.subjects[1:]:
                self.assertTrue(base < set(subject.byte_spans))
            self.assertEqual(manifest["variants"]["tags"]["added_fragments"], ["bread", "sodabread"])
            self.assertEqual(manifest["variants"]["generic"]["added_fragments"], ["Soda bread"])
            self.assertEqual(manifest["variants"]["all_bread"]["added_fragments"], [
                "soda bread", "Soda bread", "bread", "sodabread",
            ])
            self.assertEqual(len(manifest["anchors"]), 12)
            self.assertEqual(sum(len(note.subjects) for note in notes), 24)
            self.assertEqual(manifest["source_sha256"], study.sha(study.CASES))
            with self.assertRaises(FileExistsError):
                study.prepare(output)

    def test_cosine_rejects_zero_vectors(self):
        self.assertAlmostEqual(study.cosine([1, 0], [1, 1]), 2 ** -0.5)
        with self.assertRaises(ValueError):
            study.cosine([0, 0], [1, 0])


if __name__ == "__main__":
    unittest.main()
