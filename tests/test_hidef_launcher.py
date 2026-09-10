"""Exercise the real read-only HiDeF launcher in a temporary checkout."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest


class HidefLauncherTest(unittest.TestCase):
    def test_default_and_explicit_seeds_preserve_identity_and_forward_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            script = root / 'sse_multivector/run-hidef-hierarchy.sh'
            script.parent.mkdir()
            shutil.copy2(pathlib.Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/hdbscan-hierarchy'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$0" "$@"\n')
            binary.chmod(0o755)
            for prefix, seed in [([], 123), (['123'], 123), (['124'], 124), (['125'], 125)]:
                output = subprocess.run([str(script), *prefix, '--start-at', '917', '--check'], capture_output=True, text=True)
                self.assertEqual(output.returncode, 0, output.stderr)
                args = output.stdout.splitlines()
                self.assertEqual(args[0], str(binary))
                self.assertEqual(args[1], str(root / f'sse_multivector/hidef-experiment-v1/HDFv1/seed{seed}/hierarchy.json'))
                self.assertEqual(args[2:4], [str(root / 'sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json'), str(root / 'sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json')])
                self.assertEqual(args[-4:], ['--containment', '--start-at', '917', '--check'])
            for invalid in ['126', 'I03']:
                output = subprocess.run([str(script), invalid], capture_output=True, text=True)
                self.assertEqual(output.returncode, 2)
                self.assertIn('123|124|125', output.stderr)
            binary.unlink()
            missing = subprocess.run([str(script)], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1)
            self.assertIn('Build first:', missing.stderr)


if __name__ == '__main__':
    unittest.main()
