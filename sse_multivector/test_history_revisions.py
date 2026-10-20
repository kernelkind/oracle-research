"""Historical source reads use the bundled map without local replacement refs."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import generation_history as history


class HistoryRevisionTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")
        environment.start()
        self.addCleanup(environment.stop)

    def repository(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        (root / "source.txt").write_bytes(b"Original source.\n")
        message = root / "message.txt"
        message.write_text("Source fixture\n")
        subprocess.run(["git", "add", "source.txt"], cwd=root, check=True)
        subprocess.run([
            "git", "-c", "user.name=History fixture", "-c",
            "user.email=fixture@example.invalid", "-c", "commit.gpgSign=false",
            "commit", "--quiet", "-F", str(message),
        ], cwd=root, check=True)
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True,
        ).strip()
        return root, revision

    def write_map(self, root, rows):
        path = root / "docs/experiments/commit-map.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old new\n" + "".join(f"{old} {new}\n" for old, new in rows))

    def test_pinned_runner_source_without_replacement_refs(self):
        result = subprocess.run([
            sys.executable, "-c",
            "import hashlib; from sse_multivector import generation_history as h; "
            "print(hashlib.sha256(h.source_bytes(h.REPOSITORY_ROOT / "
            "'sse_multivector/codex_exec.py')).hexdigest())",
        ], cwd=history.REPOSITORY_ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), history.LEGACY_WRAPPER_SHA256)

    def test_full_and_abbreviated_original_revision_read_identical_source(self):
        path = history.REPOSITORY_ROOT / "sse_multivector/distillation_review_automatic.py"
        for revision in ("808f8bfc121c5d0e76b820e23abc1f54aaa1c660", "808f8bfc"):
            with self.subTest(revision=revision):
                source = history.source_at_revision(path, revision)
                self.assertEqual(hashlib.sha256(source).hexdigest(),
                    "ecd7b45392b515631dab3934eaa8feab7715bf47ad1f4ba9a6defd85cece2c15")

    def test_current_named_revision_still_works(self):
        path = history.REPOSITORY_ROOT / ".dockerignore"
        self.assertEqual(history.source_at_revision(path, "HEAD"), path.read_bytes())

    def test_original_repository_uses_original_commit_when_mapping_target_is_absent(self):
        root, revision = self.repository()
        self.write_map(root, [(revision, "f" * 40)])
        with patch.object(history, "REPOSITORY_ROOT", root):
            self.assertEqual(history.source_at_revision(root / "source.txt", revision),
                b"Original source.\n")

    def test_ambiguous_original_prefix_is_rejected(self):
        root, revision = self.repository()
        self.write_map(root, [("1234567a" + "0" * 32, revision),
                              ("1234567b" + "0" * 32, revision)])
        with patch.object(history, "REPOSITORY_ROOT", root):
            with self.assertRaisesRegex(history.RunnerError, "[Aa]mbiguous"):
                history.source_at_revision(root / "source.txt", "1234567")

    def test_removed_file_does_not_fall_back_to_unverified_local_bytes(self):
        root, revision = self.repository()
        self.write_map(root, [("e" * 40, revision)])
        path = root / "removed.json"
        path.write_bytes(b'{"local_only":true}\n')
        with patch.object(history, "REPOSITORY_ROOT", root):
            with self.assertRaises(subprocess.CalledProcessError):
                history.source_at_revision(path, "e" * 40)


if __name__ == "__main__":
    unittest.main()
