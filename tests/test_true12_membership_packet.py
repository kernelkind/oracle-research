"""The six TRUE12 Coffee additions reach review without altering frozen evidence."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "sse_multivector/navigation-research-v1/TRUE12"
PACKET = RUN / "membership-review.json"
LAUNCHER = Path("sse_multivector/run-true12-review.sh")


class TRUE12MembershipPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        diagnostic = json.loads((RUN / "cutoff-diagnostic.json").read_text())
        coffee = next(row for row in diagnostic["categories"] if row["title"] == "Coffee")
        rule = coffee["rules"]["historical_cutoff"]
        cls.note_ids = set(rule["new_negative_notes"] + rule["new_uncertain_notes"])
        cls.accepted_masks = {note_id: [] for note_id in cls.note_ids}
        for line in (RUN / "scores.jsonl").read_text().splitlines():
            score = json.loads(line)
            if score["category_id"] != coffee["group"] or score["entailment_score"] <= 0.142:
                continue
            for mask in score["masks"]:
                if mask["note_short_id"] in cls.note_ids:
                    cls.accepted_masks[mask["note_short_id"]].append(mask)
        source = json.loads((RUN / "data/reviewed-input.json").read_text())
        cls.notes = {note["note_id"]: note["text"] for note in source["notes"]}

    def packet(self):
        self.assertTrue(PACKET.is_file(), "the TRUE12 membership review packet is missing")
        return json.loads(PACKET.read_text())

    def test_exactly_six_notes_have_separate_assessments_and_no_user_decisions(self):
        packet = self.packet()
        self.assertEqual(set(packet), {"schema_version", "batch_id", "items"})
        self.assertEqual(packet["schema_version"], 1)
        self.assertTrue(packet["batch_id"].strip())
        self.assertEqual(len(self.note_ids), 6)
        self.assertEqual(len(packet["items"]), 6)
        self.assertEqual({item["item_id"] for item in packet["items"]}, self.note_ids)
        for item in packet["items"]:
            with self.subTest(note=item["item_id"]):
                self.assertEqual(set(item), {
                    "item_id", "note_id", "subject", "note", "fragments", "assessment", "details",
                })
                self.assertEqual(item["subject"], "Coffee")
                self.assertIsInstance(item["assessment"], str)
                self.assertTrue(item["assessment"].strip())
                self.assertIsInstance(item["details"], str)
                self.assertTrue(item["details"].strip())
                source_ids = {mask["note_id"] for mask in self.accepted_masks[item["item_id"]]}
                self.assertEqual(source_ids, {item["note_id"]})
                self.assertEqual(item["note"], self.notes[item["note_id"]])

    def test_inline_fragments_cover_exact_union_of_all_fourteen_accepted_masks(self):
        packet = self.packet()
        accepted_count = sum(len(masks) for masks in self.accepted_masks.values())
        self.assertEqual(accepted_count, 14)
        accounted = set()
        for item in packet["items"]:
            with self.subTest(note=item["item_id"]):
                masks = self.accepted_masks[item["item_id"]]
                expected = {
                    offset
                    for mask in masks
                    for start, end in mask["byte_spans"]
                    for offset in range(start, end)
                }
                content = item["note"].encode("utf-8")
                self.assertTrue(item["fragments"])
                actual = set()
                previous_end = 0
                for fragment in item["fragments"]:
                    self.assertEqual(set(fragment), {"text", "occurrence"})
                    self.assertTrue(fragment["text"].strip())
                    self.assertIs(type(fragment["occurrence"]), int)
                    self.assertGreater(fragment["occurrence"], 0)
                    text = fragment["text"].encode("utf-8")
                    # re.finditer, like Rust str::match_indices, finds nonoverlapping occurrences.
                    occurrences = list(re.finditer(re.escape(text), content))
                    self.assertLessEqual(fragment["occurrence"], len(occurrences))
                    match = occurrences[fragment["occurrence"] - 1]
                    start, end = match.span()
                    self.assertGreaterEqual(start, previous_end, "union fragments must not overlap")
                    content[:start].decode("utf-8")
                    content[:end].decode("utf-8")
                    actual.update(range(start, end))
                    previous_end = end
                self.assertEqual(actual, expected, "all accepted masks must be overlaid together")
                detail_ids = set(re.findall(r"\bV\d{3}\b", item["details"]))
                mask_ids = {mask["short_id"] for mask in masks}
                self.assertTrue(mask_ids <= detail_ids, f"missing mask IDs: {mask_ids - detail_ids}")
                accounted.update(mask_ids)
        self.assertEqual(len(accounted), 14)

    def test_frozen_experiment_inputs_and_results_are_unchanged(self):
        expected = {
            "config.json": "98dd5e45730c3d8b6b1aef6ba88e996944b3ac292f1bd6ff911472d17d57e25e",
            "baseline.json": "0c93bd773edcb2118815e953c26dba5f5999b896aa037bd386bf9caf7f8c7589",
            "memberships.json": "5dccf19eb63722a8ae61e9a24d51a35626485b9ccf4e6bf67f62649d5e0611ed",
            "scores.jsonl": "9c088ed13a292c3e43b50bba44e28b6ffede10484fd4393712d024330a174fa7",
            "semantic-review-before-inference.json": "a75b1f7d8ee0adb4f061634c659bd255066797e96dfe8cf080bf8bf0a2caed49",
            "cutoff-diagnostic.json": "4ee20d1b7f9bb2979664152e86b95f2e64eef190b7f1c7bd756357173f2631be",
            "data/reviewed-input.json": "9de47b1a66867e612aaf706da5002d4b04b4e9d8192e3782330a693dd1dea019",
            "inputs.json": "c8d42232f6f65827f263266f73c5ecf13a0a28d9ce29c267e5941a93049aed6c",
            "comparison-details.json": "e115a89e124bab08e0300680ff92ec43706793a3e8415f5d2c9a9665ecad8368",
        }
        for relative, digest in expected.items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((RUN / relative).read_bytes()).hexdigest(), digest)


class TRUE12MembershipLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / LAUNCHER).is_file(), "the TRUE12 review launcher is missing")
        temporary = tempfile.TemporaryDirectory(prefix="true12 review ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.script = self.root / LAUNCHER
        self.script.parent.mkdir(parents=True)
        shutil.copy2(ROOT / LAUNCHER, self.script)
        self.binary = self.root / "target/release/sse-mask-review"
        self.binary.parent.mkdir(parents=True)
        tools = self.root / "tools"
        tools.mkdir()
        for name in ("cargo", "nix"):
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

    def test_launches_saved_packet_and_forwards_options_from_arbitrary_cwd(self):
        self.binary.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\nexit 23\n')
        self.binary.chmod(0o755)
        result = self.run_launcher("--start-at", "N065")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.splitlines(), [
            "review-membership",
            str(self.root / "sse_multivector/navigation-research-v1/TRUE12/membership-review.json"),
            str(self.root / "target/true12-membership-review-session.json"),
            "--start-at",
            "N065",
        ])
        self.assertFalse((self.root / "target/true12-membership-review-session.json").exists())

    def test_missing_binary_reports_how_to_build_without_building(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("cargo build", result.stderr)
        self.assertIn("--bin sse-mask-review", result.stderr)
        self.assertNotIn("unexpected build invocation", result.stderr)
        self.assertFalse(self.binary.exists())


if __name__ == "__main__":
    unittest.main()
