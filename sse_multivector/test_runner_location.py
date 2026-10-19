"""The real compatibility launchers select the intended source checkout."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class RunnerLocationTests(unittest.TestCase):
    def test_launchers_support_nested_sibling_and_explicit_checkouts(self):
        source = Path(__file__).parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'oracle'
            scripts = project / 'sse_multivector'
            scripts.mkdir(parents=True)
            for name in ('_runner_bootstrap.py', 'run-model.sh'):
                shutil.copy2(source / name, scripts / name)
            env = {k: v for k, v in os.environ.items()
                   if k not in ('EXPERIMENT_RUNNER_ROOT', 'PYTHONPATH')}

            def runner(path):
                package = path / 'experiment_runner'
                package.mkdir(parents=True)
                (package / '__init__.py').write_text('')
                (package / 'project.py').write_text('def configure(root): pass\n')
                (package / 'experiment.py').write_text('')
                launcher = package / 'run-model.sh'
                launcher.write_text('#!/usr/bin/env bash\npwd\n')
                launcher.chmod(0o755)

            sibling, nested, explicit = root / 'experiment-runner', project / 'experiment-runner', root / 'custom'
            for expected in (sibling, nested, explicit):
                runner(expected)
                if expected == explicit:
                    env['EXPERIMENT_RUNNER_ROOT'] = str(explicit)
                loaded = subprocess.run([sys.executable, '-I', '-B', '-c',
                    'import sys; sys.path.insert(0, sys.argv[1]); '
                    'import _runner_bootstrap; print(_runner_bootstrap.shared("experiment").__file__)',
                    str(scripts)], env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(loaded.returncode, 0, loaded.stderr)
                self.assertEqual(Path(loaded.stdout.strip()), expected / 'experiment_runner/experiment.py')
                # A distinct exit status proves which real shell launcher was selected.
                for path, code in ((sibling, 11), (nested, 12), (explicit, 13)):
                    if path.exists():
                        (path / 'experiment_runner/run-model.sh').write_text(f'#!/usr/bin/env bash\nexit {code}\n')
                launched = subprocess.run(['bash', str(scripts / 'run-model.sh'), '--identity'],
                    env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(launched.returncode, {sibling: 11, nested: 12, explicit: 13}[expected], launched.stderr)


if __name__ == '__main__':
    unittest.main()
