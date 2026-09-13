"""The current title review launcher opens saved data without running a build."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TitleReviewLauncherTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="title review ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        relative = Path("sse_multivector/hdbv2-node-description-probe-v11/run-review.sh")
        self.script = self.root / relative
        self.script.parent.mkdir(parents=True)
        shutil.copy2(Path(__file__).resolve().parents[1] / relative, self.script)
        self.binary = self.root / "target/release/sse-mask-review"
        self.binary.parent.mkdir(parents=True)
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("nix", "cargo"):
            stub = tools / name
            stub.write_text('#!/usr/bin/env bash\necho "unexpected build invocation" >&2\nexit 97\n')
            stub.chmod(0o755)
        self.environment = {**os.environ, "PATH": str(tools) + os.pathsep + os.environ["PATH"]}

    def run_launcher(self, *arguments):
        return subprocess.run(
            ["bash", str(self.script), *arguments],
            cwd="/",
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_launches_existing_binary_with_unchanged_inputs_and_options(self):
        self.binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\nexit 23\n')
        self.binary.chmod(0o755)
        result = self.run_launcher("--start-at", "Sfd8645f195")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.splitlines(), [
            "review-titles",
            str(self.script.parent / "review-uncertain.json"),
            str(self.root / "target/hdbv2-node-description-v11-review-session.json"),
            "--comments",
            str(self.script.parent / "review-comments.json"),
            "--start-at",
            "Sfd8645f195",
        ])

    def test_missing_binary_prints_build_command_without_building(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Build first:", result.stderr)
        self.assertIn("nix develop -c cargo build --release --jobs 2 --bin sse-mask-review", result.stderr)
        self.assertNotIn("unexpected build invocation", result.stderr)
        self.assertFalse(self.binary.exists())

    def test_nonexecutable_binary_is_reported_without_building(self):
        self.binary.write_text("not executable\n")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Build first:", result.stderr)
        self.assertNotIn("unexpected build invocation", result.stderr)


if __name__ == "__main__":
    unittest.main()
