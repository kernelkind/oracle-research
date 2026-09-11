"""Exercise optional policy selection without changing the HDFv1 defaults."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class GraphPolicyLauncherTests(unittest.TestCase):
    def test_viewer_routes_each_policy_and_preserves_navigation_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-hidef-hierarchy.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'target/infomap-review-build/debug/hdbscan-hierarchy'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            for policy in ('original', 'mutual_best_per_note', 'strongest_edges_matched'):
                result = subprocess.run([str(script), '124', '--graph-policy', policy,
                    '--start-at', '917', '--check'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                args = result.stdout.splitlines()
                self.assertEqual(args[0], str(root / f'sse_multivector/hidef-experiment-v1/HDFv2/{policy}/seed124/hierarchy.json'))
                self.assertEqual(args[-4:], ['--containment', '--start-at', '917', '--check'])
            for extra in (['--graph-policy'], ['--graph-policy', 'typo'],
                          ['--graph-policy', 'original', '--graph-policy', 'original']):
                invalid = subprocess.run([str(script), *extra], capture_output=True, text=True)
                self.assertEqual(invalid.returncode, 2)

    def test_runner_routes_each_policy_with_unchanged_frozen_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'sse_multivector/run-hidef-experiment.sh'
            script.parent.mkdir()
            shutil.copy2(Path(__file__).resolve().parents[1] / script.relative_to(root), script)
            binary = root / 'bin/nix'
            binary.parent.mkdir()
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o755)
            env = {**os.environ, 'PATH': str(binary.parent) + os.pathsep + os.environ['PATH']}
            for policy in ('original', 'mutual_best_per_note', 'strongest_edges_matched'):
                command = [str(script), '125', str(root / policy), '--graph-policy', policy, '--plan']
                result = subprocess.run(command, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                args = result.stdout.splitlines()
                self.assertIn('HDFv2-' + policy + '-seed125', args)
                self.assertEqual(args[args.index('--graph-policy') + 1], policy)
                self.assertEqual(args[args.index('--minres'):args.index('--consensus-percent') + 2],
                                 ['--minres', '.001', '--maxres', '25', '--density', '.1',
                                  '--neighbors', '10', '--persistence', '5', '--consensus-percent', '75'])
                self.assertEqual(args[-1], '--plan')
            for extra in (['--graph-policy'], ['--graph-policy', 'typo'], ['--plan', '--plan']):
                invalid = subprocess.run([str(script), '123', str(root / 'invalid'), *extra],
                                         env=env, capture_output=True, text=True)
                self.assertEqual(invalid.returncode, 2)


if __name__ == '__main__':
    unittest.main()
