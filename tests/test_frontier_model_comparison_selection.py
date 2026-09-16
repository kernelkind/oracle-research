"""The model-comparison viewer must preserve its inputs and launch without a build."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("sse_multivector/frontier-model-comparison-v1")


class ModelComparisonSelectionTest(unittest.TestCase):
    def test_all_26_notes_are_unchanged_and_have_reasons(self):
        selection = json.loads((ROOT / DIRECTORY / "selection.json").read_text())
        notes = selection["notes"]
        self.assertEqual(len(notes), 26)
        self.assertEqual(len({note["note_id"] for note in notes}), 26)
        self.assertEqual(len({note["text"] for note in notes}), 26)
        expected = {
            "H23", "H06", "H21", "D11", "H19", "D06", "H11", "H49", "H51",
            "H17", "H15", "H18", "H31", "H27", "H13", "D21", "H05", "H50",
            "H55", "D16", "H54", "H04", "D12", "H12", "D14", "H57",
        }
        self.assertEqual({note["id"] for note in notes}, expected)
        sources = {}
        for note in notes:
            source = note["source"]
            path = ROOT / source["path"]
            if path not in sources:
                sources[path] = json.loads(path.read_text())["notes"]
            original = sources[path][source["index"] - 1]
            self.assertEqual(note["note_id"], original["note_id"], note["id"])
            self.assertEqual(note["text"], original["text"], note["id"])
            self.assertEqual(int(note["id"][1:]), source["index"])
            self.assertTrue(note["title"].strip())
            self.assertTrue(note["why"].strip())
        self.assertIn("not a representative", selection["purpose"])

    def test_launcher_uses_saved_selection_without_building(self):
        with tempfile.TemporaryDirectory(prefix="note sample ") as temporary:
            root = Path(temporary)
            script = root / DIRECTORY / "run-review.sh"
            script.parent.mkdir(parents=True)
            shutil.copy2(ROOT / DIRECTORY / "run-review.sh", script)
            binary = root / "target/release/note-sample-review"
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\nexit 23\n')
            binary.chmod(0o755)
            result = subprocess.run(
                ["bash", str(script), "--start-at", "H57"], cwd="/",
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 23, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                str(script.parent / "selection.json"), "--start-at", "H57",
            ])
            binary.unlink()
            tools = root / "tools"
            tools.mkdir()
            for name in ("cargo", "nix"):
                stub = tools / name
                stub.write_text('#!/usr/bin/env bash\necho unexpected-build >&2\nexit 97\n')
                stub.chmod(0o755)
            result = subprocess.run(
                ["bash", str(script)], cwd="/", capture_output=True, text=True, timeout=5,
                env={**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"]},
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Build first:", result.stderr)
            self.assertNotIn("unexpected-build", result.stderr)


if __name__ == "__main__":
    unittest.main()
