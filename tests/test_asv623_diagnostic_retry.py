"""Retry only missing GLM outputs, preserving the initial diagnostic."""

import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "sse_multivector/frontier-model-comparison-v1"
ORIGINAL = BASE / "asv6.23-diagnostic-v2"
RETRY = BASE / "asv6.23-diagnostic-retry-v1"


class DiagnosticRetryTests(unittest.TestCase):
    def test_only_two_failed_glm_outputs_are_replaced_in_the_viewer(self):
        old = json.loads((ORIGINAL / "review.json").read_text())
        new = json.loads((RETRY / "review.json").read_text())
        records = [json.loads(line) for line in (RETRY / "glm/results.jsonl").read_text().splitlines()]
        self.assertEqual({r["note_id"] for r in records}, {"H06", "H21"})
        latest = {r["note_id"]: r for r in records}
        self.assertEqual(len(old["notes"]), len(new["notes"]))
        for before, after in zip(old["notes"], new["notes"]):
            self.assertEqual({k: v for k, v in before.items() if k != "results"},
                             {k: v for k, v in after.items() if k != "results"})
            self.assertEqual(len(before["results"]), len(after["results"]))
            for original, updated in zip(before["results"], after["results"]):
                if before["id"] not in latest or original["model"] != "GLM":
                    self.assertEqual(updated, original)
                    continue
                row = latest[before["id"]]
                self.assertEqual(row["status"], "succeeded")
                subjects = json.loads(row["final_output_raw"])["subjects"]
                self.assertEqual(updated["output"], "\n\n".join(
                    f"{i}. {s['subject']}" for i, s in enumerate(subjects, 1)))
                self.assertTrue(updated["comment"].strip())
                self.assertEqual(updated["model"], original["model"])
                self.assertIn("No output", original["output"])

    def test_retries_preserve_exact_inputs_and_original_failed_receipts(self):
        selection = json.loads((ORIGINAL / "selection.json").read_text())
        notes = {n["id"]: n for n in selection["notes"]}
        for name, path in [("H06", ORIGINAL / "glm/results.jsonl"),
                           ("H21", ORIGINAL / "glm-remaining/H21/results.jsonl")]:
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "failed")
            self.assertIn("429", rows[0]["model_result"]["error"])
        for line in (RETRY / "glm/results.jsonl").read_text().splitlines():
            row = json.loads(line)
            self.assertEqual(row["model"], "z-ai/glm-5.3-flash")
            body = row["model_result"]["request"]["body"]
            self.assertEqual(body["messages"], [{"role": "user", "content": notes[row["note_id"]]["prompt"]}])
            self.assertEqual(body["response_format"]["json_schema"]["schema"], notes[row["note_id"]]["schema"])
            self.assertEqual(body["reasoning"]["effort"], "low")

    def test_existing_launcher_opens_the_completed_results(self):
        result = subprocess.run(["bash", str(ORIGINAL / "run-review.sh"), "--check"],
                                cwd="/tmp", capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GLM retries", result.stdout)
        self.assertIn("12 notes, 4 models", result.stdout)


if __name__ == "__main__":
    unittest.main()
