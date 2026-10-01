"""The shared workflow must use the bounded adapters, not generic JSON checks."""

import json
import unittest

from sse_multivector import experiment, experiment_inputs
from sse_multivector.test_bounded_hierarchy_workflow import discovery_case


class BoundedHierarchyIntegrationTests(unittest.TestCase):
    def test_shared_discovery_validation_rejects_excluded_nomination(self):
        raw = json.dumps({"queries": [{"id": "S0000", "candidates": [
            {"id": "S0002", "reason": "Related wording."}]}]})
        with self.assertRaisesRegex(ValueError, "excluded"):
            experiment_inputs.validate({"adapter": "bounded_discovery"},
                                       discovery_case(), raw, None)

    def test_shared_discovery_validation_preserves_parsed_empty_nominations(self):
        value = {"queries": [{"id": "S0000", "candidates": []}]}
        result = experiment_inputs.validate({"adapter": "bounded_discovery"},
                                           discovery_case(), json.dumps(value), None)
        self.assertEqual(result["parsed"], value)

    def test_shared_comparison_validation_rejects_missing_pair(self):
        case = {"inputs": {"INPUT_JSON": json.dumps({"nodes": [], "pairs": [
            {"id": "S0000-S0001", "A": "S0000", "B": "S0001"}]})}}
        with self.assertRaisesRegex(ValueError, "every supplied pair"):
            experiment_inputs.validate({"adapter": "bounded_comparisons"}, case,
                                       '{"comparisons":[]}', None)

    def test_build_preparation_is_an_offline_shared_command(self):
        args = experiment.parser().parse_args([
            "prepare-bounded-hierarchy", "target/build", "--spec", "spec.json"])
        self.assertEqual(args.destination.name, "build")
        self.assertEqual(args.spec.name, "spec.json")


if __name__ == "__main__":
    unittest.main()
