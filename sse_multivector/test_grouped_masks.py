"""Grouped masks through the real experiment CLI and production decoder."""
import json
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector import experiment_inputs as inputs


class GroupedMaskTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    prepare = fixtures.ExperimentTests.prepare
    show = fixtures.ExperimentTests.show
    calls = fixtures.ExperimentTests.calls

    def grouped_spec(self):
        self.prompt.write_text("GENERIC PROMPT\n{POST}\n{INDEXED_POST}\n{SUBJECTS}")
        self.cases.write_text(json.dumps({"schema_version": 1, "notes": [{
            "note_id": "N1", "text": "Thé helps. Thé helps.", "subjects": [
                {"subject": "Tea", "context": "REVIEW ONLY",
                 "byte_spans": [[0, 4], [12, 16]], "fragments": ["Thé", "Thé"]},
                {"subject": "Tea drinking", "byte_spans": [], "fragments": []},
            ]}]}))
        spec = json.loads(self.spec.read_text())
        spec["dataset"]["adapter"] = "grouped_masks"
        self.spec.write_text(json.dumps(spec))

    def response(self):
        return {"results": [
            {"id": "S1", "meaning": "Tea", "expressible": True,
             "evidence": "Both tea words", "mask": [[1, 1], [3, 3]]},
            {"id": "S2", "meaning": "Tea drinking", "expressible": False,
             "evidence": "No drinking", "mask": []},
        ]}

    def test_one_call_all_subjects_decode_and_compare_saved_masks(self):
        self.grouped_spec()
        self.prepare()
        report = self.show()
        self.assertEqual(len(report["cases"]), 1)
        case = report["cases"][0]
        self.assertNotIn("REVIEW ONLY", case["prompt"])
        self.assertEqual(json.loads(case["inputs"]["SUBJECTS"]), [
            {"id": "S1", "subject": "Tea"}, {"id": "S2", "subject": "Tea drinking"}])
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(self.response())})
        self.assertEqual(len(self.calls()), 1)
        masks = self.show()["cases"][0]["mask_results"]
        self.assertEqual([m["status"] for m in masks], ["valid", "empty"])
        self.assertEqual(masks[0]["fragments"], ["Thé", "Thé"])
        self.assertEqual(masks[0]["byte_spans"], [[0, 4], [12, 16]])
        self.assertTrue(all(m["matches_baseline"] for m in masks))

    def test_overlap_across_subjects_and_changed_baseline_are_valid(self):
        self.grouped_spec()
        response = self.response()
        response["results"][1].update(expressible=True, mask=[[1, 1]], evidence="Tea")
        self.prepare()
        self.cli("run", "E1", env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(response)})
        masks = self.show()["cases"][0]["mask_results"]
        self.assertEqual(masks[1]["fragments"], ["Thé"])
        self.assertFalse(masks[1]["matches_baseline"])

    def test_missing_duplicate_foreign_reordered_and_invalid_masks_fail_without_retry(self):
        self.grouped_spec()
        responses = []
        for kind in ("missing", "duplicate", "foreign", "reordered", "position", "overlap", "verdict"):
            response = self.response()
            if kind == "missing":
                response["results"].pop()
            elif kind == "duplicate":
                response["results"][1]["id"] = "S1"
            elif kind == "foreign":
                response["results"][1]["id"] = "S3"
            elif kind == "reordered":
                response["results"].reverse()
            elif kind == "position":
                response["results"][0]["mask"] = [[99, 99]]
            elif kind == "overlap":
                response["results"][0]["mask"] = [[1, 1], [1, 1]]
            else:
                response["results"][0]["expressible"] = False
            responses.append((kind, response))
        for kind, response in responses:
            with self.subTest(kind=kind):
                self.prepare(kind, "--repeat")
                self.cli("run", kind, ok=False,
                         env={"FAKE_RUNNER_PROMPT_RESPONSE": json.dumps(response)})
                self.assertEqual(self.show(kind)["cases"][0]["status"], "malformed")
        self.assertEqual(len(self.calls()), len(responses))

    def test_source_selection_validation_and_duplicate_subjects(self):
        self.grouped_spec()
        source = json.loads(self.cases.read_text())
        template = self.prompt.read_text()
        dataset = {"adapter": "grouped_masks", "select": ["N1"]}
        source["notes"].append({"note_id": "N2", "text": "Coffee", "subjects": ["Coffee"]})
        self.assertEqual(len(inputs.prepare(dataset, source, template)), 1)
        self.assertEqual(len(inputs.prepare({"adapter": "grouped_masks"}, source, template)), 2)
        source["notes"][0]["subjects"].append("Tea")
        case = inputs.prepare(dataset, source, template)[0]
        self.assertEqual(json.loads(case["inputs"]["SUBJECTS"])[2], {"id": "S3", "subject": "Tea"})
        with self.assertRaisesRegex(ValueError, "unknown note"):
            inputs.prepare({"adapter": "grouped_masks", "select": ["absent"]}, source, template)
        source["notes"].append(source["notes"][0])
        with self.assertRaisesRegex(ValueError, "duplicate note_id"):
            inputs.prepare(dataset, source, template)

    def test_bad_baseline_bytes_and_fragments_are_rejected(self):
        self.grouped_spec()
        for spans, fragments in (([[0, 3]], ["Th"]), ([[0, 4]], ["wrong"]),
                                 ([[12, 16], [0, 4]], ["Thé", "Thé"])):
            source = json.loads(self.cases.read_text())
            source["notes"][0]["subjects"][0].update(byte_spans=spans, fragments=fragments)
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                inputs.prepare({"adapter": "grouped_masks"}, source, self.prompt.read_text())

    def test_duplicate_json_keys_and_prohibited_identifiers_are_rejected(self):
        self.grouped_spec()
        source = json.loads(self.cases.read_text())
        source["notes"][0].update(text="https://example.com", subjects=["Example"])
        dataset = {"adapter": "grouped_masks"}
        case = inputs.prepare(dataset, source, self.prompt.read_text())[0]
        response = {"results": [self.response()["results"][0]]}
        response["results"][0]["mask"] = [[1, 1]]
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            inputs.validate(dataset, case, '{"results":[],"results":[]}', None)
        with self.assertRaisesRegex(Exception, "prohibited URL"):
            inputs.validate(dataset, case, json.dumps(response), None)


if __name__ == "__main__":
    unittest.main()
