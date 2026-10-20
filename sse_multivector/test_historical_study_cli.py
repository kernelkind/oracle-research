"""Historical selections use the supported offline publication command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class HistoricalStudyCliTests(unittest.TestCase):
    def test_unselected_study_is_rejected_without_creating_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root/'selection.json'
            spec.write_text(json.dumps(dict(schema_version=1, studies={})))
            output = root/'publication'
            result = subprocess.run([sys.executable,
                str(Path(__file__).with_name('experiment.py')),
                'export-evaluation-results', str(root), '--kind', 'prompt-study',
                '--spec', str(spec), '--study', 'missing', '--output', str(output)],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('study is not explicitly selected: missing', result.stderr)
            self.assertFalse(output.exists())

    def test_study_argument_requires_a_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable,
                str(Path(__file__).with_name('experiment.py')),
                'export-evaluation-results', temporary, '--kind', 'prompt-study',
                '--study', 'missing'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--study requires --spec', result.stderr)


if __name__ == '__main__':
    unittest.main()
