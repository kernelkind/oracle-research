"""Authored prompt checks; clause meaning still requires semantic review."""

import re
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
        template = ROOT / "experiment_specs" / f"{self.path.parent.name}-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        # This counts existing assignments, not rewritten instruction meanings.
        self.assertEqual(
            Counter(rule for case in example_checks.FOCUSED_CASES for rule in case["primary_rules"]),
            Counter({f"R{i:02d}": 1 for i in range(1, 35)}),
        )
