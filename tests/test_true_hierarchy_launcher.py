"""The TRUE11 launcher opens the frozen category graph without inference or rebuilding."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TrueHierarchyLauncherTest(unittest.TestCase):
    def test_launcher_preserves_paths_and_does_not_enable_simplification(self):
        with tempfile.TemporaryDirectory(prefix='TRUE viewer ') as temporary:
            root = Path(temporary)
            script = root/'sse_multivector/run-true-hierarchy.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1]/script.relative_to(root), script)
            binary = root/'target/infomap-review-build/debug/sse-subject-navigation'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            for options in ([], ['--check']):
                result = subprocess.run(['bash', str(script), *options], cwd='/',
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    '--categories',
                    str(root/'sse_multivector/navigation-research-v1/TRUE11/categories.json'),
                    str(root/'sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json'),
                    *options])
            for options in (['--check', '--check'], ['--absorb-single-children'], ['--unknown']):
                result = subprocess.run(['bash', str(script), *options],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('Usage:', result.stderr)
            binary.unlink()
            result = subprocess.run(['bash', str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Build first:', result.stderr)


if __name__ == '__main__':
    unittest.main()
