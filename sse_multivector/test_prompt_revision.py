import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).with_name("extraction_pipeline.py")


class PromptRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / "base.md"
        self.destination = self.root / "v2" / "prompt.md"
        self.receipt = self.destination.with_name("prompt.md.revision.json")
        self.original = (
            "Read the complete post.\r\n\r\nOld instruction.\r\n\r\n"
            "Preserve these lines.\r\nOne.\r\nTwo.\r\nThree.\r\n"
            "UNCHANGED EXAMPLE: café ⟦art⟧\r\nNo final newline"
        ).encode("utf-8")
        self.base.write_bytes(self.original)

    def request(self, edits=None):
        return {
            "base_sha256": hashlib.sha256(self.original).hexdigest(),
            "edits": edits if edits is not None else [
                {"old": "Old instruction.", "new": "New instruction."}
            ],
        }

    def run_revision(self, request, *, from_file=False, destination=None):
        text = json.dumps(request, ensure_ascii=False)
        edits_path = "-"
        if from_file:
            path = self.root / "edits.json"
            path.write_text(text, encoding="utf-8")
            edits_path = str(path)
        return subprocess.run(
            [sys.executable, str(CLI), "revise-prompt", str(self.base),
             str(destination or self.destination), "--edits", edits_path],
            input=None if from_file else text,
            text=True, capture_output=True, cwd=self.root,
            env={"PATH": os.defpath, "HOME": str(self.root)},
            timeout=10, check=False,
        )

    def test_creates_exact_revision_and_receipt_without_echoing_examples(self):
        request = self.request()
        result = self.run_revision(request)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = self.original.replace(b"Old instruction.", b"New instruction.")
        self.assertEqual(self.base.read_bytes(), self.original)
        self.assertEqual(self.destination.read_bytes(), expected)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["base_path"], str(self.base))
        self.assertEqual(receipt["base_sha256"], request["base_sha256"])
        self.assertEqual(receipt["prompt_sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(receipt["edits"], request["edits"])
        self.assertIn("-Old instruction.", result.stdout)
        self.assertIn("+New instruction.", result.stdout)
        self.assertNotIn("UNCHANGED EXAMPLE", result.stdout)
        self.assertIn("Created", result.stderr)

    def test_edits_match_original_not_text_inserted_by_another_edit(self):
        result = self.run_revision(self.request([
            {"old": "Old instruction.", "new": "Preserve these lines."},
            {"old": "Preserve these lines.", "new": ""},
        ]), from_file=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = self.original.replace(b"Preserve these lines.", b"").replace(
            b"Old instruction.", b"Preserve these lines."
        )
        self.assertEqual(self.destination.read_bytes(), expected)

    def test_refuses_wrong_baseline_missing_ambiguous_overlapping_and_noop_edits(self):
        cases = [
            ({**self.request(), "base_sha256": "0" * 64}, "baseline SHA-256"),
            (self.request([{"old": "Missing", "new": "New"}]), "exactly once"),
            (self.request([{"old": "\r\n", "new": "\n"}]), "exactly once"),
            (self.request([
                {"old": "Old instruction.", "new": "New"},
                {"old": "instruction.", "new": "Other"},
            ]), "overlap"),
            (self.request([{"old": "Old", "new": "Old"}]), "unchanged"),
            (self.request([]), "nonempty"),
            (self.request([{"old": "", "new": "New"}]), "nonempty"),
            (self.request([{"old": "Old", "new": 3}]), "string"),
            (self.request([{"old": "Old", "new": "New", "extra": True}]), "not supported"),
        ]
        for request, message in cases:
            with self.subTest(message=message, request=request):
                result = self.run_revision(request)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(message, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse(self.destination.exists())
                self.assertFalse(self.receipt.exists())
                self.assertEqual(self.base.read_bytes(), self.original)

    def test_refuses_existing_destination_or_receipt_and_leaves_them_untouched(self):
        self.destination.parent.mkdir()
        for existing in (self.destination, self.receipt):
            with self.subTest(existing=existing):
                existing.write_bytes(b"DO NOT OVERWRITE")
                result = self.run_revision(self.request())
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("already exists", result.stderr)
                self.assertEqual(existing.read_bytes(), b"DO NOT OVERWRITE")
                other = self.receipt if existing == self.destination else self.destination
                self.assertFalse(other.exists())
                existing.unlink()
        result = self.run_revision(self.request(), destination=self.base)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.base.read_bytes(), self.original)

    def test_refuses_dangling_destination_symlink(self):
        self.destination.parent.mkdir()
        target = self.root / "missing.md"
        self.destination.symlink_to(target)
        result = self.run_revision(self.request())
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("already exists", result.stderr)
        self.assertTrue(self.destination.is_symlink())
        self.assertFalse(target.exists())
        self.assertFalse(self.receipt.exists())

    def test_diff_marks_a_changed_final_line_without_adding_a_newline(self):
        result = self.run_revision(self.request([
            {"old": "No final newline", "new": "Changed final line"}
        ]))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.destination.read_bytes().endswith(b"Changed final line"))
        self.assertEqual(result.stdout.count("\\ No newline at end of file"), 2)

    def test_invalid_utf8_and_invalid_json_do_not_create_a_revision(self):
        self.original = b"bad UTF-8: \xff"
        self.base.write_bytes(self.original)
        result = self.run_revision(self.request())
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("could not read baseline", result.stderr)
        self.assertFalse(self.destination.exists())
        result = subprocess.run(
            [sys.executable, str(CLI), "revise-prompt", str(self.base),
             str(self.destination), "--edits", "-"],
            input="not json", text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("could not read edits JSON", result.stderr)
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.receipt.exists())

    def test_concurrent_revisions_publish_only_one_matching_prompt_and_receipt(self):
        processes = []
        for replacement in ("First revision.", "Second revision."):
            process = subprocess.Popen(
                [sys.executable, str(CLI), "revise-prompt", str(self.base),
                 str(self.destination), "--edits", "-"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True,
            )
            self.addCleanup(lambda p=process: p.kill() if p.poll() is None else None)
            processes.append(process)
            process.stdin.write(json.dumps(self.request([
                {"old": "Old instruction.", "new": replacement}
            ])))
            process.stdin.close()
            process.stdin = None
        results = [process.communicate(timeout=10) for process in processes]
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1], results)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        expected = self.original.replace(
            b"Old instruction.", receipt["edits"][0]["new"].encode("utf-8")
        )
        self.assertEqual(self.destination.read_bytes(), expected)
        self.assertEqual(receipt["prompt_sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(self.base.read_bytes(), self.original)
        self.assertEqual(set(self.destination.parent.iterdir()), {self.destination, self.receipt})

    def test_help_explains_input_and_offline_behavior(self):
        result = subprocess.run(
            [sys.executable, str(CLI), "revise-prompt", "--help"],
            text=True, capture_output=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for word in ("base_sha256", '"old"', '"new"', "stdin", "original", "model"):
            self.assertIn(word, result.stdout)


if __name__ == "__main__":
    unittest.main()
