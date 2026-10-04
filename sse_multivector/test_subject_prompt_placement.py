"""Offline ASv6.101 revision preservation and production validation checks."""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sse_multivector import experiment_inputs


ROOT = Path(__file__).resolve().parent
VERSION = ROOT / "subject-prompt-goal-v1/asv6.101"
OLD = (
    "Determine valid relationships before numbering, combine shared headings, and give "
    "every heading and subheading its own entry. For each complete source subject, "
    "compare its own wording with every returned heading using the parent check. "
    "An equal-meaning heading's own entry already represents the source subject; "
    "include it among the descendants of every more-general compatible heading, "
    "independently at every numbered occurrence even when surrounding branches "
    "differ. Placement elsewhere cannot repair a missing branch."
)
NEW = (
    "Determine valid relationships before numbering, combine shared headings, and give "
    "every heading and subheading its own entry. For each returned heading, compare "
    "every complete source subject's own wording with it using the parent check. "
    "The heading's own entry already represents an equal-meaning source subject; "
    "include every more-specific compatible source subject among its descendants, "
    "independently at every numbered occurrence even when surrounding branches "
    "differ. Placement elsewhere cannot repair a missing branch."
)


class SubjectPlacementRevisionTests(unittest.TestCase):
    def test_native_revision_changes_only_placement_and_preserves_valid_examples(self):
        candidate = (VERSION / "ASv6.101.md").read_bytes()
        paths = (
            (ROOT / "subject-prompt-goal-v1/asv6.99/ASv6.99.md",
             VERSION / "ASv6.101.md", VERSION / "prompt-edits.json"),
            (ROOT / "experiment_specs/asv6.99-hr01-post-template.txt",
             ROOT / "experiment_specs/asv6.101-hr01-post-template.txt",
             VERSION / "edits.json"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for base, destination, edits_path in paths:
                with self.subTest(destination=destination.name):
                    original = base.read_bytes()
                    self.assertEqual(original.count(OLD.encode()), 1)
                    expected = original.replace(OLD.encode(), NEW.encode())
                    request = json.loads(edits_path.read_text())
                    self.assertEqual(request, {
                        "base_sha256": hashlib.sha256(original).hexdigest(),
                        "edits": [{"old": OLD, "new": NEW}],
                    })
                    replay = Path(temporary) / destination.name
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "experiment.py"), "revise",
                         str(base), str(replay), "--edits", str(edits_path)],
                        text=True, capture_output=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(replay.read_bytes(), expected)
                    self.assertEqual(destination.read_bytes(), expected)
                    replay_receipt = json.loads(
                        replay.with_name(replay.name + ".revision.json").read_text()
                    )
                    self.assertEqual(replay_receipt["base_path"], str(base))
                    self.assertEqual(replay_receipt["base_sha256"], request["base_sha256"])
                    self.assertEqual(replay_receipt["prompt_sha256"],
                                     hashlib.sha256(expected).hexdigest())
                    self.assertEqual(replay_receipt["edits"], request["edits"])
                    recorded_receipt = json.loads(destination.with_name(
                        destination.name + ".revision.json").read_text())
                    self.assertEqual(
                        {key: value for key, value in recorded_receipt.items()
                         if key != "base_path"},
                        {key: value for key, value in replay_receipt.items()
                         if key != "base_path"},
                    )
        self.assertEqual(paths[1][1].read_bytes(), candidate + b"\n<post>\n{POST}\n</post>")
        outputs = re.findall(r"<output>\n(.*?)\n</output>", candidate.decode(), re.S)
        self.assertEqual(len(outputs), 8)
        for output in outputs:
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)


if __name__ == "__main__":
    unittest.main()
