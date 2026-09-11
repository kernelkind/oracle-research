"""Exercise frozen-input range extension through the real experiment launcher."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class ExtensionLauncherTests(unittest.TestCase):
    def test_runner_passes_source_and_endpoint_without_changing_other_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-hidef-experiment.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            nix = root / 'bin/nix'
            nix.parent.mkdir()
            nix.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            nix.chmod(0o755)
            env = {**os.environ, 'PATH': str(nix.parent) + os.pathsep + os.environ['PATH']}
            source = root / 'old run'
            source.mkdir()
            result = subprocess.run([str(script), '124', str(root / 'new run'),
                '--extend-from', str(source), '--maxres', '190', '--plan'],
                env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            args = result.stdout.splitlines()
            self.assertEqual(args[args.index('--extend-from') + 1], str(source))
            self.assertEqual(args[args.index('--maxres') + 1], '190')
            self.assertEqual(args[args.index('--run-id') + 1], 'HDFv3-seed124')
            for key, value in [('--minres', '.001'), ('--density', '.1'), ('--neighbors', '10'),
                               ('--persistence', '5'), ('--consensus-percent', '75')]:
                self.assertEqual(args[args.index(key) + 1], value)
            self.assertEqual(args[-1], '--plan')
            for extra in [['--extend-from'], ['--maxres', '190'],
                          ['--extend-from', str(source)],
                          ['--extend-from', str(source), '--maxres', '190', '--maxres', '200'],
                          ['--extend-from', str(source), '--maxres', '190', '--graph-policy', 'mutual_best_per_note']]:
                result = subprocess.run([str(script), '123', str(root / 'invalid'), *extra],
                    env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stderr)

if __name__ == '__main__':
    unittest.main()
