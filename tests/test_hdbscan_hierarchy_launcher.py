"""Exercise the production launcher with recording binaries in a temporary checkout."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest


class HierarchyLauncherTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = pathlib.Path(self.directory.name)
        self.script = self.root / "sse_multivector/run-hdbscan-hierarchy.sh"
        self.script.parent.mkdir()
        source = pathlib.Path(__file__).resolve().parents[1] / self.script.relative_to(self.root)
        shutil.copy2(source, self.script)
        for target in ["target/debug", "target/hierarchy-note-view-build/debug"]:
            binary = self.root / target / "hdbscan-hierarchy"
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$0" "$@"\n')
            binary.chmod(0o755)

    def arguments(self, *args):
        result = subprocess.run([str(self.script), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()

    def test_new_view_uses_separate_binary_and_hdbv3(self):
        args = self.arguments("--note-navigation")
        self.assertEqual(args[0], str(self.root / "target/hierarchy-note-view-build/debug/hdbscan-hierarchy"))
        self.assertTrue(args[1].endswith("hdbv3-cross-note-edges-v1/response.json"))
        self.assertEqual(args[-3:], ["--note-navigation", "--start-at", "1254"])
        self.assertEqual(self.arguments("--note-navigation", "1204")[-1], "1204")

    def test_existing_views_keep_their_binary_data_and_defaults(self):
        args = self.arguments()
        self.assertEqual(args[0], str(self.root / "target/debug/hdbscan-hierarchy"))
        self.assertTrue(args[1].endswith("hdbscan-cross-note/response.json"))
        self.assertEqual(args[-2:], ["--start-at", "1043"])
        selection = self.arguments("--selection")
        self.assertEqual(selection[:4], args[:4])
        self.assertEqual(selection[-4], "--selection")
        self.assertTrue(selection[-3].endswith("hierarchy-selection-v1.json"))
        self.assertEqual(selection[-2:], ["--start-at", "916"])
        self.assertEqual(self.arguments("1045")[-1], "1045")


if __name__ == "__main__":
    unittest.main()
