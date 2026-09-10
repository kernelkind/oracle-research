"""The manual launcher accepts any working directory and never selects an algorithm run."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest


class ManualCoffeeLauncherTest(unittest.TestCase):
    def test_absolute_inputs_and_check_forwarding(self):
        with tempfile.TemporaryDirectory(prefix="manual coffee ") as directory:
            root = pathlib.Path(directory)
            script = root / "sse_multivector/run-manual-coffee-hierarchy.sh"
            script.parent.mkdir()
            original = pathlib.Path(__file__).resolve().parents[1] / script.relative_to(root)
            shutil.copy2(original, script)
            binary = root / "target/merge-rule-review-build/debug/sse-subject-navigation"
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            result = subprocess.run([str(script), "--check"], cwd="/tmp", capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                "--notes",
                str(root / "sse_multivector/manual-coffee-hierarchy-v1/hierarchy.json"),
                str(root / "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json"),
                "--check",
            ])
            binary.unlink()
            result = subprocess.run([str(script)], cwd="/tmp", capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nix develop", result.stderr)


if __name__ == "__main__":
    unittest.main()
