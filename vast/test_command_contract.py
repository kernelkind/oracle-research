"""The deployment CLI accepts current command workloads, never retired builds."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CommandContractTest(unittest.TestCase):
    def test_retired_build_is_rejected_before_operation_state_is_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "operation.json"
            config.write_text(json.dumps({
                "schema_version": 1,
                "artifact_kind": "gte-vast-full-build-operation",
            }))
            root = directory / "operation"
            result = subprocess.run([
                sys.executable, "-B", str(Path(__file__).with_name("runner.py")),
                "--root", str(root), "--config", str(config), "prepare",
            ], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only vast-command-operation is supported", result.stderr)
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
