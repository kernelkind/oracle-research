"""Exercise the real read-only launcher in a temporary checkout."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest


class InfomapLauncherTest(unittest.TestCase):
    def test_each_saved_configuration_uses_native_view_and_forwards_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            script = root / 'sse_multivector/run-infomap-hierarchy.sh'
            script.parent.mkdir()
            shutil.copy2(pathlib.Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/hdbscan-hierarchy'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$0" "$@"\n')
            binary.chmod(0o755)
            for run in ['I01', 'I02', 'I03', 'I04']:
                path = root / f'sse_multivector/infomap-experiment-v1/{run}/hierarchy.json'
                path.parent.mkdir(parents=True)
                path.write_text('{}')
                output = subprocess.run([str(script), run, '--start-at', '917', '--check'],
                                        capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr)
                args = output.stdout.splitlines()
                self.assertEqual(args[0], str(binary))
                self.assertEqual(args[1], str(path))
                self.assertEqual(args[-4:], ['--infomap', '--start-at', '917', '--check'])
            invalid = subprocess.run([str(script), 'M07'], capture_output=True, text=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertIn('I01', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
