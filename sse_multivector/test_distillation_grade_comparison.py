"""Compare already collected native grades without another collection or call."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_coverage_search as coverage
from sse_multivector import distillation_grade_comparison as comparison
from sse_multivector import test_distillation_coverage_search as fixtures


class CollectedGradeComparisonTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = fixtures.DistillationCoverageSearchTests()
        self.fixture.root = self.root

    def prepared(self):
        fixture, _, directory, native, row = self.fixture.collection_fixture(
            "collected-comparison", policy="grading", audit_prerequisites=False)
        reference = self.root / "reference.json"
        coverage.collect(directory, reference)
        automated = self.root / "automated.json"
        coverage.collect(directory, automated, automated_analysis=True)
        return fixture, directory, reference, automated, native

    def test_saved_native_report_is_compared_without_recollection_or_inference(self):
        _, directory, reference, automated, _ = self.prepared()
        calls = (self.root / "calls.json").read_bytes()
        frozen = automated.read_bytes()
        with patch.object(coverage, "collect", side_effect=AssertionError("must reuse collected grades")):
            result = comparison.compare(directory, reference, self.root / "comparison",
                automated_report=automated)
        self.assertEqual(result["automated"], str(automated))
        self.assertEqual(result["random"]["complete_pairs"], 1)
        self.assertEqual(result["inference_calls"], 0)
        self.assertEqual(automated.read_bytes(), frozen)
        self.assertEqual((self.root / "calls.json").read_bytes(), calls)

    def test_saved_native_report_rechecks_its_frozen_source_hashes(self):
        _, directory, reference, automated, native = self.prepared()
        ledger = native / "run/results.jsonl"
        ledger.write_text(ledger.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "source changed"):
            comparison.compare(directory, reference, self.root / "comparison-changed",
                automated_report=automated)


if __name__ == "__main__":
    unittest.main()
