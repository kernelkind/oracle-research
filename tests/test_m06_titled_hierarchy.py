"""Exercise the production launcher without rebuilding or opening a terminal."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class M06TitledHierarchyLauncherTest(unittest.TestCase):
    def test_paths_options_and_missing_binary(self):
        with tempfile.TemporaryDirectory(prefix="m06 titled ") as directory:
            root = Path(directory)
            script = root / "sse_multivector/run-m06-titled-hierarchy.sh"
            script.parent.mkdir()
            shutil.copy2(ROOT / script.relative_to(root), script)
            binary = root / "target/merge-rule-review-build/debug/sse-subject-navigation"
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            result = subprocess.run([str(script), "--start-at", "1605", "--check"], cwd="/tmp", capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [
                "--merge-notes",
                str(root / "sse_multivector/merge-rule-exploration-v1/M06.json"),
                str(root / "sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json"),
                str(root / "sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json"),
                str(root / "sse_multivector/merge-rule-exploration-v1/M06-titles.json"),
                "--start-at", "1605", "--check",
            ])
            binary.unlink()
            result = subprocess.run([str(script)], cwd="/tmp", capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nix develop", result.stderr)


if __name__ == "__main__":
    unittest.main()
