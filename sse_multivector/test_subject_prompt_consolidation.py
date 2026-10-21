"""Authored prompt checks; clause meaning still requires semantic review."""

import json
import re
import unittest
from collections import Counter
from pathlib import Path

from sse_multivector import experiment_inputs
from sse_multivector import test_subject_prompt_examples as example_checks


ROOT = Path(__file__).parent
BASELINE_PATH = ROOT / "subject-prompt-goal-v1/asv6.95/ASv6.95.md"
CANDIDATE_PATH = ROOT / "subject-prompt-goal-v1/asv6.96/ASv6.96.md"


class ConsolidatedSubjectPromptTests(example_checks.FiniteSourceCollectionPromptTests):
    path = CANDIDATE_PATH

    def validated_blocks(self, source):
        blocks = re.findall(r"<example>\n(.*?)\n</example>", source, re.S)
        self.assertEqual(len(blocks), 7)
        for block in blocks:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S)
            self.assertIsNotNone(output)
            experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output.group(1), None
            )
        return blocks

    def test_all_instructions_precede_examples(self):
        source = self.path.read_text()
        self.validated_blocks(source)
        after_instructions = source[source.index("<example>"):]
        self.assertEqual(
            re.sub(r"<example>\n.*?\n</example>", "", after_instructions, flags=re.S).strip(),
            "",
            "instructions remain after the worked examples begin",
        )

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = BASELINE_PATH.read_text()
        after = self.path.read_text()
        self.assertEqual(self.validated_blocks(before), self.validated_blocks(after))
        # This counts existing assignments, not rewritten instruction meanings.
        self.assertEqual(
            Counter(rule for case in example_checks.FOCUSED_CASES for rule in case["primary_rules"]),
            Counter({f"R{i:02d}": 1 for i in range(1, 35)}),
        )


class FoodClassificationSubjectPromptTests(example_checks.GroupedSourceCopiesPromptTests):
    path = ROOT / "subject-prompt-goal-v1/asv6.97/ASv6.97.md"
    subjects = {
        **example_checks.SHARED_ACTION_SUBJECTS,
        "salt": "Sea salt",
        "food_salt": "Sea salt for food seasoning",
    }
    # The user accepts Food -> Sea salt. Other C1 meanings retain their
    # existing reviewed basis; this graph is not a general semantic oracle.
    relationships = example_checks.SHARED_ACTION_RELATIONSHIPS + (("salt", "food"),)

    def test_food_membership_and_complete_seasoning_subject_coexist(self):
        entries = self.entries()
        by_number = {entry["number"]: entry for entry in entries}
        self.assertTrue(any(
            entry["subject"] == "Sea salt"
            and "." in entry["number"]
            and by_number[entry["number"].rsplit(".", 1)[0]]["subject"] == "Food"
            for entry in entries
        ), "C1 lacks the accepted Food -> Sea salt example")
        for parent in entries:
            if parent["subject"] in ("Sea salt", "Food seasoning"):
                with self.subTest(parent=parent["number"]):
                    self.assertTrue(any(
                        child["subject"] == "Sea salt for food seasoning"
                        and child["number"].startswith(parent["number"] + ".")
                        for child in entries
                    ), "complete source purpose is missing from a compatible copy")

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = CANDIDATE_PATH.read_text()
        after = self.path.read_text()
        blocks = [re.findall(r"<example>\n(.*?)\n</example>", source, re.S)
                  for source in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        self.assertEqual(before.rsplit("</example>", 1)[1], after.rsplit("</example>", 1)[1])
        for block in blocks[1]:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        self.assertEqual(
            Counter(rule for case in example_checks.FOCUSED_CASES for rule in case["primary_rules"]),
            Counter({f"R{i:02d}": 1 for i in range(1, 35)}),
        )


class TitledRecipeSubjectPromptTests(unittest.TestCase):
    path = ROOT / "subject-prompt-goal-v1/asv6.98/ASv6.98.md"

    def test_titled_recipe_retains_complete_source_relationship(self):
        blocks = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)
        self.assertEqual(len(blocks), 8, "missing the titled-recipe example")
        output = re.search(r"<output>\n(.*?)\n</output>", blocks[-1], re.S).group(1)
        experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        entries = json.loads(output)["subjects"]
        by_number = {entry["number"]: entry for entry in entries}
        recipe = "Author's reliable lentil soup recipe serving four people"
        seasoning = "Cumin to taste for seasoning food in the author's reliable lentil soup recipe serving four people"
        self.assertEqual([entry["number"] for entry in entries if entry["subject"] == recipe],
                         ["1.1", "2.1"])
        self.assertEqual([entry["number"] for entry in entries if entry["subject"] == seasoning],
                         ["1.1.1", "2.1.1", "3.1", "4.1"])
        for entry in entries:
            if "." not in entry["number"]:
                continue
            parent = by_number[entry["number"].rsplit(".", 1)[0]]["subject"]
            self.assertIn((parent, entry["subject"]), {
                ("Recipes", recipe), ("Lentil soup", recipe),
                (recipe, seasoning), ("Cumin", seasoning), ("Food seasoning", seasoning),
            })

    def test_existing_instructions_examples_and_wrapper_are_preserved(self):
        before = FoodClassificationSubjectPromptTests.path.read_text()
        after = self.path.read_text()
        self.assertTrue(after.startswith(before + "\n<example>\n"))
        blocks = re.findall(r"<example>\n(.*?)\n</example>", after, re.S)
        self.assertEqual(len(blocks), 8)
        for block in blocks:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)


class SharedToolSubjectPromptTests(FoodClassificationSubjectPromptTests):
    path = ROOT / "subject-prompt-goal-v1/asv6.99/ASv6.99.md"
    baseline_path = TitledRecipeSubjectPromptTests.path
    subjects = {
        **FoodClassificationSubjectPromptTests.subjects,
        **{node: subject + " with a knife"
           for node, subject in example_checks.SHARED_ACTION_SUBJECTS.items()
           if node in ("tissue_cutting", "meat_cutting", "complete_cutting")},
        "knife": "Knife",
    }
    relationships = FoodClassificationSubjectPromptTests.relationships + (
        ("tissue_cutting", "knife"), ("meat_cutting", "knife"),
    )

    def test_shared_tool_retains_individual_and_combined_actions(self):
        entries = self.entries()
        knives = [entry for entry in entries if entry["subject"] == "Knife"]
        self.assertTrue(knives, "C1 lacks the shared-tool copy example")
        expected = {self.subjects[node] for node in
                    ("tissue_cutting", "meat_cutting", "complete_cutting")}
        for knife in knives:
            descendants = {entry["subject"] for entry in entries
                           if entry["number"].startswith(knife["number"] + ".")}
            self.assertEqual(descendants, expected)

    def test_all_copies_of_a_subject_are_emitted_together(self):
        # Only C1 changes. C8 keeps its reviewed branch ordering verbatim.
        closed = set()
        previous = None
        for entry in self.entries():
            subject = entry["subject"]
            if subject != previous:
                self.assertNotIn(subject, closed)
                if previous is not None:
                    closed.add(previous)
                previous = subject

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = self.baseline_path.read_text()
        after = self.path.read_text()
        blocks = [re.findall(r"<example>\n(.*?)\n</example>", source, re.S)
                  for source in (before, after)]
        self.assertEqual(len(blocks[1]), 8)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        for block in blocks[1]:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        self.assertEqual(
            Counter(rule for case in example_checks.FOCUSED_CASES for rule in case["primary_rules"]),
            Counter({f"R{i:02d}": 1 for i in range(1, 35)}),
        )


class ConditionalParticipantSubjectPromptTests(SharedToolSubjectPromptTests):
    path = ROOT / "subject-prompt-goal-v1/asv6.100/ASv6.100.md"
    baseline_path = SharedToolSubjectPromptTests.path
    subjects = {
        **SharedToolSubjectPromptTests.subjects,
        **{node: SharedToolSubjectPromptTests.subjects[node] + " when a bowl is empty"
           for node in ("tissue_cutting", "meat_cutting", "complete_cutting")},
        "bowl_condition": "A bowl being empty",
    }
    relationships = SharedToolSubjectPromptTests.relationships + (
        ("tissue_cutting", "bowl_condition"), ("meat_cutting", "bowl_condition"),
    )

    def test_condition_retains_individual_and_combined_action_copies(self):
        entries = self.entries()
        conditions = [entry for entry in entries
                      if entry["subject"] == self.subjects["bowl_condition"]]
        self.assertTrue(conditions, "C1 lacks the separate condition-participant copies")
        expected = {self.subjects[node] for node in
                    ("tissue_cutting", "meat_cutting", "complete_cutting")}
        for condition in conditions:
            descendants = {entry["subject"] for entry in entries
                           if entry["number"].startswith(condition["number"] + ".")}
            self.assertEqual(descendants, expected)
