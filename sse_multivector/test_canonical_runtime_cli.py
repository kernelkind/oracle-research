"""The shared launcher exposes the integrated canonical construction workflow."""
from pathlib import Path
import subprocess
import sys
import unittest


class CanonicalRuntimeCliTests(unittest.TestCase):
    def test_saved_data_audit_retains_its_standalone_import(self):
        project = Path(__file__).resolve().parents[1]
        result = subprocess.run([
            sys.executable, '-c',
            'import sys; sys.path.insert(0, sys.argv[1]); import canonical_hierarchy_audit; '
            'assert callable(canonical_hierarchy_audit.audit_trial)',
            str(project/'sse_multivector')], cwd=project, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shared_launcher_exposes_selection_and_finished_menu_commands(self):
        project = Path(__file__).resolve().parents[1]
        launcher = project.parent / 'experiment-runner/bin/experiment-runner'
        for command in ('prepare-hierarchy', 'advance-hierarchy',
                        'run-hierarchy', 'audit-canonical-trial',
                        'shape-canonical-trial', 'export-canonical-viewer',
                        'evaluate-canonical-policy-trial'):
            with self.subTest(command=command):
                result = subprocess.run(
                    [str(launcher), '--project-root', str(project), command, '--help'],
                    capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(command, result.stdout)


if __name__ == '__main__':
    unittest.main()
