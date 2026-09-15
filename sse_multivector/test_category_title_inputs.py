"""Exercise the actual title-input preparation CLI; no model calls required."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sse_multivector/prepare_category_title_inputs.py"


class CategoryTitleInputsTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "source.json"
        self.prompt = self.directory / "prompt.txt"
        self.output = self.directory / "prepared.json"
        self.template = "Name the category.\n\nInstances:\n\n{NUMBERED_INSTANCES}\n"
        self.prompt.write_text(self.template)

    def instance(self, name, note="N1", spans=None, text="tea tea coffee"):
        spans = spans or [[0, 3]]
        return {
            "instance": name, "note_id": note, "vector_id": "vector-" + name,
            "text": text, "byte_spans": spans,
            "fragments": [text.encode()[a:b].decode() for a, b in spans],
        }

    def prepare(self, instances, *arguments):
        source = {"packets": [{"packet": "S1", "instances": instances}]}
        self.source.write_text(json.dumps(source))
        before = self.source.read_bytes()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.source), str(self.prompt),
             str(self.output), *arguments], capture_output=True, text=True,
        )
        self.assertEqual(self.source.read_bytes(), before)
        return result

    def test_same_note_same_mask_occurs_once_in_prompt_and_review_inputs(self):
        instances = [self.instance("V1"), self.instance("V2"),
                     self.instance("V3", "N2")]
        result = self.prepare(instances)
        self.assertEqual(result.returncode, 0, result.stderr)
        group = json.loads(self.output.read_text())["groups"][0]
        self.assertEqual(group["instances"], [
            {"instance": "V1", "fragments": ["tea"]},
            {"instance": "V3", "fragments": ["tea"]},
        ])
        self.assertEqual(group["prompt"],
                         self.template.replace("{NUMBERED_INSTANCES}",
                                               "1. “tea”\n2. “tea”"))
        self.assertEqual(group["sources"][0]["source_instances"], ["V1", "V2"])
        self.assertEqual(group["sources"][0]["source_vector_ids"],
                         ["vector-V1", "vector-V2"])
        self.assertEqual(group["duplicates_removed"], 1)

    def test_different_notes_positions_and_overlapping_masks_are_preserved(self):
        instances = [self.instance("V1"), self.instance("V2", "N2"),
                     self.instance("V3", spans=[[4, 7]]),
                     self.instance("V4", spans=[[0, 7]])]
        result = self.prepare(instances)
        self.assertEqual(result.returncode, 0, result.stderr)
        group = json.loads(self.output.read_text())["groups"][0]
        self.assertEqual([x["instance"] for x in group["instances"]],
                         ["V1", "V2", "V3", "V4"])
        self.assertEqual(group["duplicates_removed"], 0)

    def test_multiple_fragments_stay_together_and_unicode_uses_byte_offsets(self):
        instance = self.instance("V1", text="☕ tea coffee", spans=[[0, 3], [8, 14]])
        duplicate = copy.deepcopy(instance)
        duplicate.update(instance="V2", vector_id="vector-V2")
        result = self.prepare([instance, duplicate])
        self.assertEqual(result.returncode, 0, result.stderr)
        group = json.loads(self.output.read_text())["groups"][0]
        self.assertEqual(group["prompt"], self.template.replace(
            "{NUMBERED_INSTANCES}", "1. “☕”; “coffee”"))

    def test_mismatched_source_fragments_fail_without_output(self):
        instance = self.instance("V1")
        instance["fragments"] = ["coffee"]
        result = self.prepare([instance])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match", result.stderr)
        self.assertFalse(self.output.exists())

    def test_conflicting_text_for_same_note_fails_without_output(self):
        result = self.prepare([self.instance("V1"),
                               self.instance("V2", text="tea with milk")])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicting text", result.stderr)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_not_overwritten(self):
        self.output.write_text("preserve me")
        result = self.prepare([self.instance("V1")])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(), "preserve me")

    def test_unknown_group_is_not_silently_dropped(self):
        result = self.prepare([self.instance("V1")], "--group", "missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown group", result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
