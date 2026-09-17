"""The diagnostic viewer must preserve the saved notes and generated subjects."""

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC = ROOT / "sse_multivector/frontier-model-comparison-v1/asv6.23-diagnostic-v2"


class DiagnosticReviewTests(unittest.TestCase):
    def test_all_notes_and_model_outputs_are_preserved(self):
        selection = json.loads((DIAGNOSTIC / "selection.json").read_text())
        packet = json.loads((DIAGNOSTIC / "review.json").read_text())
        self.assertEqual(len(packet["notes"]), 12)
        self.assertEqual([n["id"] for n in packet["notes"]],
                         [n["id"] for n in selection["notes"]])
        records = {}
        for path in DIAGNOSTIC.rglob("results.jsonl"):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                records[(row["model"], row["note_id"])] = row
        models = [
            ("Astra (saved)", None),
            ("Muse", "meta/muse-spark-1.3-contributor"),
            ("DeepSeek", "deepseek/deepseek-v4.1-flash"),
            ("GLM", "z-ai/glm-5.3-flash"),
        ]
        for note, saved in zip(packet["notes"], selection["notes"]):
            self.assertEqual(note["text"], saved["text"])
            self.assertEqual(note.get("model_input", note["text"]), saved["input_text"])
            self.assertEqual([r["model"] for r in note["results"]],
                             [m[0] for m in models])
            for result, (_, model) in zip(note["results"], models):
                self.assertTrue(result["comment"].strip())
                if model is None:
                    output = saved["astra"]["output"]
                else:
                    row = records[(model, note["id"])]
                    if row["status"] != "succeeded":
                        self.assertIn("No output", result["output"])
                        self.assertIn("429", result["output"])
                        continue
                    output = json.loads(row["final_output_raw"])
                expected = "\n\n".join(
                    f"{i}. {subject['subject']}"
                    for i, subject in enumerate(output["subjects"], 1)
                )
                self.assertEqual(result["output"], expected)

    def test_launcher_checks_packet_from_another_directory_without_writing(self):
        paths = list(DIAGNOSTIC.rglob("*"))
        before = {p.relative_to(DIAGNOSTIC): p.read_bytes() for p in paths if p.is_file()}
        result = subprocess.run(
            ["bash", str(DIAGNOSTIC / "run-review.sh"), "--check"],
            cwd="/tmp", capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("12", result.stdout)
        after = {p.relative_to(DIAGNOSTIC): p.read_bytes()
                 for p in DIAGNOSTIC.rglob("*") if p.is_file()}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
