"""Held-out reference access uses the frozen split identities."""
import json
import unittest

from sse_multivector.distillation_review import _evaluation_reference_lines


class ReferenceSplitTests(unittest.TestCase):
    def test_explicit_test_split_exposes_only_test_content(self):
        raw = (b'{"note_id":"train", "poison": INVALID}\n'
               b'{"note_id":"validation", "poison": INVALID}\n'
               b'{"note_id":"sealed", "split":"test", "text":"Test post"}\n')
        lines = _evaluation_reference_lines(raw, [["train"], ["validation"], ["sealed"]], split="test")
        self.assertEqual([json.loads(line)["note_id"] for line in lines], ["sealed"])

    def test_explicit_test_access_still_checks_other_split_identity_headers(self):
        raw = b'{"note_id":"wrong"}\n{"note_id":"validation"}\n{"note_id":"sealed"}\n'
        with self.assertRaisesRegex(ValueError, "identity header"):
            _evaluation_reference_lines(raw, [["train"], ["validation"], ["sealed"]], split="test")

    def test_default_remains_validation_and_training_is_rejected(self):
        raw = b'{"note_id":"train"}\n{"note_id":"validation"}\n{"note_id":"sealed"}\n'
        splits = [["train"], ["validation"], ["sealed"]]
        self.assertEqual(_evaluation_reference_lines(raw, splits), [b'{"note_id":"validation"}'])
        with self.assertRaisesRegex(ValueError, "evaluation or test"):
            _evaluation_reference_lines(raw, splits, split="train")
