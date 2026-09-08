import importlib.util
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "cross_note_comparison", Path(__file__).with_name("compare_cross_note.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def packet(name, *members):
    return {
        "packet": name,
        "instances": [
            {
                "vector_id": vector,
                "instance": vector,
                "note_id": note,
                "text": vector,
                "byte_spans": [[0, len(vector)]],
            }
            for vector, note in members
        ],
    }


class CrossNoteComparisonTests(unittest.TestCase):
    def test_partition_changes_and_no_decision_inheritance(self):
        old = [
            packet("kept", ("a", "1"), ("b", "2")),
            packet("lost", ("c", "1"), ("d", "2")),
            packet("same-note", ("e", "3"), ("f", "3")),
        ]
        new = [
            old[0],
            packet("new", ("c", "1"), ("e", "3")),
            packet("single-note", ("f", "3"), ("g", "3")),
        ]
        result, review = MODULE.compare(old, ["g"], new, ["d"])
        self.assertEqual(["kept"], result["exactly_unchanged_segments"])
        self.assertEqual(["lost"], result["baseline_multi_note_segments_changed"])
        self.assertEqual(["new"], [p["packet"] for p in review])
        self.assertNotIn("judgments", result)
        self.assertEqual(["d"], result["newly_unassigned_vectors"])
        self.assertEqual(["g"], result["newly_assigned_vectors"])
        self.assertEqual(2, result["baseline"]["multi_note_segments"])
        self.assertEqual(2, result["trial"]["multi_note_segments"])
        self.assertEqual(
            ["new"],
            result["baseline_segment_destinations"]["same-note"]["multi_note_segments"],
        )

    def test_refuses_evidence_changes_and_different_vector_universe(self):
        old = [packet("kept", ("a", "1"), ("b", "2"))]
        changed = [packet("kept", ("a", "1"), ("b", "3"))]
        with self.assertRaisesRegex(ValueError, "evidence"):
            MODULE.compare(old, [], changed, [])
        with self.assertRaisesRegex(ValueError, "vector universe"):
            MODULE.compare(old, [], old, ["extra"])

    def test_preservation_check_detects_changes_and_removal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "previous.json"
            MODULE.write_json(source, {"verdict": "valid"})
            snapshot = MODULE.snapshot(root, [source])
            MODULE.verify_snapshot(root, snapshot)
            MODULE.write_json(root / "unrelated.json", {})
            MODULE.verify_snapshot(root, snapshot)
            source.unlink()
            with self.assertRaisesRegex(ValueError, "preserved"):
                MODULE.verify_snapshot(root, snapshot)
            MODULE.write_json(source, {"verdict": "invalid"})
            with self.assertRaisesRegex(ValueError, "preserved"):
                MODULE.verify_snapshot(root, snapshot)

    def test_artifact_writes_never_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "review.json"
            MODULE.write_json(path, {"first": True})
            with self.assertRaises(FileExistsError):
                MODULE.write_json(path, {"first": False})

    def test_packaged_memberships_must_equal_the_replayed_result(self):
        original = [
            packet("ab", ("a", "1"), ("b", "2")),
            packet("cd", ("c", "3"), ("d", "4")),
        ]
        fine_output = {"segments": [["a", "b"], ["c", "d"]], "unassigned": []}
        MODULE.verify_partition(original, [], fine_output)
        changed = [
            packet("ac", ("a", "1"), ("c", "3")),
            packet("bd", ("b", "2"), ("d", "4")),
        ]
        with self.assertRaisesRegex(ValueError, "replayed"):
            MODULE.verify_partition(changed, [], fine_output)


if __name__ == "__main__":
    unittest.main()
