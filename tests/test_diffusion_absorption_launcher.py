from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class AbsorptionLauncherTest(unittest.TestCase):
    def test_absorption_switch_is_forwarded_once_in_either_option_order(self):
        with tempfile.TemporaryDirectory(prefix='category absorption ') as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-diffusion-categories.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/sse-subject-navigation'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            flag = '--absorb-single-children'
            for options in [[flag], [flag, '--check'], ['--check', flag]]:
                result = subprocess.run(['bash', str(script), *options], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    '--categories',
                    str(root / 'sse_multivector/geometric-hierarchy-v1/GDC09/categories.json'),
                    str(root / 'sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json'),
                    *options,
                ])
            for options in [[flag, flag], ['--check', flag, '--check'], [flag, '--unknown']]:
                result = subprocess.run(['bash', str(script), *options], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('Usage:', result.stderr)


if __name__ == '__main__':
    unittest.main()
