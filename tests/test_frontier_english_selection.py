"""Integrity of the English comparison inputs and the small read-only sampler."""

import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "sse_multivector/frontier-model-comparison-v1/english-selection-v1"


class FrontierEnglishSelectionTest(unittest.TestCase):
    def read(self, name):
        return json.loads((DIRECTORY / name).read_text())

    def test_selection_preserves_sources_and_excludes_ineligible_notes(self):
        source = self.read("source-notes.json")["notes"]
        audit = self.read("audit.json")
        by_id = {row["note_id"]: row for row in audit["notes"]}
        selected = self.read("selection.json")["notes"]
        self.assertEqual(len(by_id), len(source))
        self.assertEqual(len({n["note_id"] for n in selected}), len(selected))
        for note in selected:
            original = source[note["source"]["index"] - 1]
            self.assertEqual(note["note_id"], original["note_id"])
            self.assertEqual(note["text"], original["text"])
            self.assertFalse(by_id[note["note_id"]]["exclude_reasons"])
            self.assertTrue(note["why"].strip())
            self.assertTrue(note["title"].strip())

    def test_report_counts_actual_selected_notes_without_double_counting(self):
        audit = self.read("audit.json")
        report = self.read("coverage.json")
        selected = {n["note_id"] for n in self.read("selection.json")["notes"]}
        self.assertEqual(report["selected_notes"], len(selected))
        for kind in report["challenges"]:
            actual = [row["note_id"] for row in audit["notes"]
                      if row["note_id"] in selected and kind["id"] in row["challenges"]]
            self.assertEqual(kind["selected_notes"], len(actual), kind["id"])
            self.assertGreaterEqual(len(actual), kind["target_notes"], kind["id"])
            self.assertEqual(kind["target_notes"], 60)
        self.assertFalse(report["model_calls_made"])

    def test_viewer_contains_only_a_small_subset(self):
        complete = {n["note_id"]: n for n in self.read("selection.json")["notes"]}
        sampler = self.read("sampler.json")
        self.assertGreaterEqual(len(sampler["notes"]), 6)
        self.assertLessEqual(len(sampler["notes"]), 12)
        self.assertEqual(len({n["note_id"] for n in sampler["notes"]}), len(sampler["notes"]))
        for note in sampler["notes"]:
            self.assertEqual(note, complete[note["note_id"]])
        self.assertIn("sample", sampler["title"].lower())

    def test_saved_selection_is_reproducible(self):
        result = subprocess.run(
            ["python3", str(DIRECTORY / "select.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_readable_posts_are_excluded_by_confirmed_policy(self):
        result = subprocess.run(
            ["python3", str(DIRECTORY / "select.py"), "--artifact", "audit.json"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)["notes"]
        non_readable = [row for row in rows if "Z" in row["manual_codes"]]
        self.assertTrue(non_readable)
        for row in non_readable:
            self.assertFalse(row["selected"])
            self.assertIn("not_readable_english_text", row["exclude_reasons"])


if __name__ == "__main__":
    unittest.main()
