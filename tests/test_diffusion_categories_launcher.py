"""The category launcher opens frozen data without rebuilding or reclustering."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CategoryLauncherTest(unittest.TestCase):
    def test_launcher_opens_categories_and_forwards_check_only(self):
        with tempfile.TemporaryDirectory(prefix='category viewer ') as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-diffusion-categories.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/sse-subject-navigation'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            for options in [[], ['--check']]:
                output = subprocess.run(['bash', str(script), *options], cwd='/', capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr)
                self.assertEqual(output.stdout.splitlines(), [
                    '--categories',
                    str(root / 'sse_multivector/geometric-hierarchy-v1/GDC09/categories.json'),
                    str(root / 'sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json'),
                    *options,
                ])
            for options in [['--check', '--check'], ['1487'], ['--unknown']]:
                output = subprocess.run(['bash', str(script), *options], capture_output=True, text=True)
                self.assertEqual(output.returncode, 2)
                self.assertIn('Usage:', output.stderr)
            binary.unlink()
            output = subprocess.run(['bash', str(script)], capture_output=True, text=True)
            self.assertEqual(output.returncode, 1)
            self.assertIn('Build first:', output.stderr)


if __name__ == '__main__':
    unittest.main()
