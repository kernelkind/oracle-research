"""Exercise the real launcher without a terminal or a build."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class DiffusionLauncherTest(unittest.TestCase):
    def test_frozen_run_and_group_selection_are_forwarded(self):
        with tempfile.TemporaryDirectory(prefix='diffusion viewer ') as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-diffusion-hierarchy.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/hdbscan-hierarchy'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            for options, group in [([], '1487'), (['1671'], '1671'), (['1753', '--check'], '1753'), (['--check'], '1487')]:
                output = subprocess.run(['bash', str(script), *options], cwd='/', capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr)
                args = output.stdout.splitlines()
                self.assertEqual(args[0], str(root / 'sse_multivector/geometric-hierarchy-v1/GDC09/viewer.json'))
                self.assertEqual(args[1:3], [str(root / 'sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json'), str(root / 'sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json')])
                self.assertEqual(args[3:6], ['--containment', '--start-at', group])
                self.assertEqual(args[6:], ['--check'] if '--check' in options else [])
            for options in [['bad'], ['-1'], ['1487', '1671'], ['--selection'], ['--check', '--check']]:
                output = subprocess.run(['bash', str(script), *options], capture_output=True, text=True)
                self.assertEqual(output.returncode, 2, output.stderr)
                self.assertIn('Usage:', output.stderr)


if __name__ == '__main__':
    unittest.main()
