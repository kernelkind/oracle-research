import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from omission_report import build_report
from sse_multivector.real_note_segmentation import (
    REVIEW_INSTRUCTIONS, REVIEW_QUESTION, REVIEW_VERDICTS, _canonical,
)


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical(value))


def identity(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def fixture(root):
    audit = root / "audit"
    packets, selected, excluded, noise = [], [], [], []
    for k in range(128):
        left = {"instance": f"V{2*k+1:03d}", "vector_id": f"{2*k+1:064x}",
                "note_id": f"{1 if k < 3 else k+1:064x}",
                "text": "☕ coffee / coffee\nhttps://example.test/full  ",
                "byte_spans": [[0, 3], [4, 10] if k == 2 else [13, 19]]}
        right = {"instance": f"V{2*k+2:03d}", "vector_id": f"{2*k+2:064x}",
                 "note_id": f"{k+500:064x}", "text": "tea", "byte_spans": [[0, 3]]}
        sid = "S" + hashlib.sha256(_canonical(sorted([left["vector_id"], right["vector_id"]]))).hexdigest()[:10]
        packets.append({"packet": sid, "instances": [left, right], "question": REVIEW_QUESTION, "verdicts": REVIEW_VERDICTS})
        selected.append({"pair_id": sid, "pair": [left["instance"], right["instance"]],
                         "stratum": "proposed" if k % 2 == 0 else "nonproposed"})
        excluded.append(left["instance"])
        if k == 0:
            noise.append(left)
    review = {"schema_version": 3, "review_set": "RNfixture", "instructions": REVIEW_INSTRUCTIONS,
              "packets": packets, "response_contract": {"schema_version": 3, "review_set": "RNfixture",
              "judgments": "zero or one judgment for every packet", "judgment_fields": ["packet", "verdict", "comment"],
              "allowed_verdicts": REVIEW_VERDICTS}}
    write(audit / "sample/review.json", review)
    write(audit / "inventory/excluded-ids.json", excluded)
    noise_path = root / "hdbscan-baseline/review/unassigned.json"
    write(noise_path, {"schema_version": 1, "kind": "unassigned", "instances": noise})
    write(audit / "inventory/manifest.json", {"schema_version": 1,
          "files": {"excluded-ids.json": identity(audit / "inventory/excluded-ids.json")},
          "sources": {"hdbscan-baseline/review/unassigned.json": identity(noise_path)}})
    write(audit / "sample/sampling-manifest.json", {"schema_version": 1, "review_set": "RNfixture",
          "audit_manifest": identity(audit / "inventory/manifest.json"),
          "files": {"review.json": identity(audit / "sample/review.json")}, "selected": selected})
    review_sha = identity(audit / "sample/review.json")["sha256"]
    rounds = []
    for name in ("A", "B"):
        rows = []
        for k, p in enumerate(packets):
            verdict = "valid" if k < 2 or k == 2 and name == "A" else "invalid"
            rows.append({"packet": p["packet"], "verdict": verdict, "comment": f"{name} saved comment {k}"})
        rounds.append({"round": name, "judgments": rows})
    write(audit / "judgments.json", {"schema_version": 1, "source_review_sha256": review_sha,
          "prepared_manifest_sha256": "a" * 64, "calls": [], "rounds": rounds})
    write(audit / "primary-review.json", {"schema_version": 1, "source_review_sha256": review_sha,
          "assessor": "primary assistant", "scope": "Read all 128 pairs.",
          "recording": "Every other packet in the bound review was explicitly judged Invalid.",
          "valid": [p["packet"] for p in packets[:2]], "uncertain": [packets[2]["packet"]],
          "judgment_notes": "Saved primary notes."})
    return audit, review


class OmissionReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.audit, self.review = fixture(self.root)
        self.output = self.audit / "report"

    def test_counts_aliases_strata_and_all_exact_review_instances(self):
        result = build_report(self.audit, self.output)
        self.assertEqual(128, result["counts"]["reviewed"])
        self.assertEqual(2, result["counts"]["all_three_valid"])
        self.assertEqual(1, result["counts"]["any_valid_not_all_valid"])
        self.assertEqual(125, result["counts"]["no_valid"])
        self.assertEqual({"valid": 2, "invalid": 125, "uncertain": 1}, result["counts"]["verdicts"]["primary"])
        self.assertEqual(64, result["by_stratum"]["proposed"]["counts"]["reviewed"])
        self.assertEqual(1, result["by_stratum"]["proposed"]["counts"]["all_three_valid"])
        group = result["groups"]["agreements"]
        self.assertEqual(["V001", "V003"], group["excluded_vector_ids"])
        self.assertEqual(1, group["distinct_source_mask_count"])
        self.assertEqual(1, group["excluded_note_count"])
        self.assertEqual(["V001"], group["baseline_noise_ids"])
        self.assertEqual(["V003"], group["baseline_one_note_ids"])
        self.assertEqual(2, result["groups"]["any_valid"]["distinct_source_mask_count"])
        self.assertEqual([p["packet"] for p in self.review["packets"]], [p["packet"] for p in result["assessments"]])
        for name, indices in (("agreements", [0, 1]), ("disagreements", [2])):
            subset = read(self.output / name / "review.json")
            self.assertEqual([self.review["packets"][k] for k in indices], subset["packets"])
            self.assertEqual(subset["review_set"], subset["response_contract"]["review_set"])
            self.assertNotEqual(self.review["review_set"], subset["review_set"])
            self.assertNotIn("judgments", subset)
        markdown = (self.output / "assessments.md").read_text()
        self.assertEqual(128, markdown.count("\n## S"))
        self.assertIn("⟦☕⟧ ⟦coffee⟧", markdown)
        self.assertIn("A saved comment 0", markdown)
        self.assertIn("B saved comment 0", markdown)
        self.assertEqual({"summary.json", "assessments.md", "agreements/review.json", "disagreements/review.json"},
                         {str(p.relative_to(self.output)) for p in self.output.rglob("*") if p.is_file()})

    def test_hash_failures_refuse_output(self):
        for relative in ("sample/review.json", "inventory/manifest.json", "inventory/excluded-ids.json",
                         "../hdbscan-baseline/review/unassigned.json"):
            path = self.audit / relative
            original = path.read_bytes()
            try:
                path.write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "hash"):
                    build_report(self.audit, self.output)
                self.assertFalse(self.output.exists())
            finally:
                path.write_bytes(original)
        for relative in ("judgments.json", "primary-review.json"):
            path = self.audit / relative
            original = path.read_bytes()
            try:
                document = json.loads(original)
                document["source_review_sha256"] = "0" * 64
                write(path, document)
                with self.assertRaisesRegex(ValueError, "hash"):
                    build_report(self.audit, self.output)
            finally:
                path.write_bytes(original)

    def test_missing_judgment_and_incomplete_primary_recording_are_rejected(self):
        path = self.audit / "judgments.json"
        original = path.read_bytes()
        document = json.loads(original)
        document["rounds"][0]["judgments"].pop()
        write(path, document)
        with self.assertRaisesRegex(ValueError, "coverage"):
            build_report(self.audit, self.output)
        path.write_bytes(original)
        primary = read(self.audit / "primary-review.json")
        del primary["recording"]
        write(self.audit / "primary-review.json", primary)
        with self.assertRaisesRegex(ValueError, "recording"):
            build_report(self.audit, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_overwrite_refusal_and_deterministic_evidence(self):
        command = [sys.executable, str(Path(__file__).with_name("omission_report.py")),
                   "--audit", str(self.audit), "--output", str(self.output)]
        subprocess.run(command, check=True, capture_output=True)
        original = {str(p.relative_to(self.output)): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(ValueError, "exists"):
            build_report(self.audit, self.output)
        other = self.audit / "other-report"
        build_report(self.audit, other)
        self.assertEqual(original["agreements/review.json"], (other / "agreements/review.json").read_bytes())
        self.assertEqual(original["disagreements/review.json"], (other / "disagreements/review.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
