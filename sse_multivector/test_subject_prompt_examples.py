"""Offline checks for the SP examples' declared hierarchy relationships."""

import re
import unittest
from pathlib import Path

from sse_multivector import experiment_inputs


PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.53/ASv6.53.md"
)


# These IDs identify subjects in ASv6.52, rather than fixing the numbering of
# their occurrences in the corrected examples.
LUNAR_SUBJECTS = {
    "1": "Astronomical observation",
    "2": "The Moon",
    "3": "Binoculars",
    "4": "Sketching",
    "5": "Clouds",
    "1.1": "Lunar eclipse observation",
    "1.1.1": "Lunar eclipse observation through binoculars",
    "2.1": "Lunar eclipses",
    "4.1": "Sketching the Moon",
    "4.1.1": "Cloud cover hindering attempts to sketch the Moon",
    "5.1": "Clouds repeatedly obscuring the Moon",
}

RAILWAY_SUBJECTS = {
    "1": "Museums",
    "2": "Locomotives",
    "3": "Restoration",
    "4": "Volunteering",
    "5": "Volunteers",
    "6": "Boilers",
    "7": "Photography",
    "8": "Exhibitions",
    "9": "Guided tours",
    "10": "Replacement parts",
    "11": "Advice",
    "12": "Advance booking",
    "13": "Marked routes",
    "14": "Staying on marked routes",
    "15": "Visitors",
    "1.1": "Railway museum",
    "1.1.1": "Railway museum's steam locomotive Bracken",
    "2.1": "Steam locomotives",
    "2.1.1": "Bracken the steam locomotive",
    "2.1.1.1": "Restoration of Bracken the steam locomotive",
    "2.1.1.2": "Bracken the steam locomotive's need for a replacement boiler",
    "3.1": "Steam locomotive restoration",
    "3.1.1": "Volunteer participation in steam locomotive restoration",
    "3.1.1.1": "Mira's volunteer work restoring the railway museum's steam locomotive Bracken",
    "4.1": "Volunteering in railway museum locomotive restoration",
    "5.1": "Mira, the railway locomotive restoration volunteer",
    "6.1": "Steam locomotive boilers",
    "6.1.1": "Replacement boiler for Bracken the steam locomotive",
    "6.2": "Boiler replacement",
    "6.2.1": "Steam locomotive boiler replacement",
    "7.1": "Restoration photography",
    "7.1.1": "Photography of Bracken the steam locomotive's restoration",
    "7.1.1.1": "Photography of Bracken the steam locomotive's restoration for an exhibition",
    "7.2": "Photography for an exhibition",
    "8.1": "Exhibition of photographs of Bracken the steam locomotive's restoration",
    "9.1": "Railway museum's guided tours",
    "9.1.1": "Railway museum's guided tours continuing during restoration of Bracken the steam locomotive",
    "10.1": "Replacement boilers",
    "11.1": "Advice for railway museum visitors",
    "11.1.1": "Advice for railway museum visitors to book their railway museum visits in advance",
    "11.1.1.1": "Advice for railway museum visitors to book their railway museum visits in advance and stay on the museum's marked visitor route",
    "11.1.2": "Advice for railway museum visitors to stay on the museum's marked visitor route",
    "12.1": "Advance booking for railway museum visits",
    "13.1": "Railway museum's marked visitor route",
    "14.1": "Staying on a railway museum's marked visitor route",
    "15.1": "Railway museum visitors",
}

LUNAR_RELATIONSHIPS = (
    ("1.1", "1"),
    ("1.1", "2.1"),
    ("1.1.1", "1.1"),
    ("1.1.1", "3"),
    ("2.1", "2"),
    ("4.1", "4"),
    ("4.1", "2"),
    ("4.1.1", "4.1"),
    ("4.1.1", "5"),
    ("5.1", "5"),
    ("5.1", "2"),
)

RAILWAY_RELATIONSHIPS = (
    ("1.1", "1"),
    ("2.1", "2"),
    ("2.1.1", "2.1"),
    ("1.1.1", "1.1"),
    ("1.1.1", "2.1.1"),
    ("3.1", "3"),
    ("3.1", "2.1"),
    ("2.1.1.1", "3.1"),
    ("2.1.1.1", "2.1.1"),
    ("3.1.1", "3.1"),
    ("3.1.1", "4"),
    ("4.1", "4"),
    ("4.1", "3"),
    ("4.1", "1.1"),
    ("4.1", "2"),
    ("5.1", "5"),
    ("3.1.1.1", "3.1.1"),
    ("3.1.1.1", "4.1"),
    ("3.1.1.1", "2.1.1.1"),
    ("3.1.1.1", "5.1"),
    ("3.1.1.1", "1.1.1"),
    ("6.1", "6"),
    ("6.1", "2.1"),
    ("10.1", "10"),
    ("10.1", "6"),
    ("6.1.1", "6.1"),
    ("6.1.1", "10.1"),
    ("6.1.1", "2.1.1"),
    ("2.1.1.2", "2.1.1"),
    ("2.1.1.2", "6.1.1"),
    ("6.2", "6"),
    ("6.2.1", "6.2"),
    ("6.2.1", "6.1"),
    ("7.1", "7"),
    ("7.1", "3"),
    ("7.1.1", "7.1"),
    ("7.1.1", "2.1.1.1"),
    ("7.2", "7"),
    ("7.2", "8"),
    ("7.1.1.1", "7.1.1"),
    ("7.1.1.1", "7.2"),
    ("8.1", "8"),
    ("8.1", "7.1.1"),
    ("9.1", "9"),
    ("9.1", "1.1"),
    ("9.1.1", "9.1"),
    ("9.1.1", "2.1.1.1"),
    ("15.1", "15"),
    ("15.1", "1.1"),
    ("11.1", "11"),
    ("11.1", "15.1"),
    ("12.1", "12"),
    ("12.1", "1.1"),
    ("13.1", "13"),
    ("13.1", "1.1"),
    ("14.1", "14"),
    ("14.1", "13.1"),
    ("14", "13"),
    ("11.1.1", "11.1"),
    ("11.1.1", "12.1"),
    ("11.1.2", "11.1"),
    ("11.1.2", "14.1"),
    ("11.1.1.1", "11.1.1"),
    ("11.1.1.1", "11.1.2"),
    ("3.1.1", "5"),
)

# Counterexamples: a general entity can lack a role; one instruction can lack
# the other; replacing a working boiler need not be restoration.
INVALID_RELATIONSHIPS = (
    (0, "3", "1"),
    (0, "2.1", "1.1"),
    (0, "5", "4.1"),
    (1, "6", "10"),
    (1, "10.1", "6.1"),
    (1, "2.1.1", "1.1"),
    (1, "12", "11"),
    (1, "13", "11"),
    (1, "15.1", "11"),
    (1, "11.1.1", "11.1.1.1"),
    (1, "11.1.2", "11.1.1.1"),
    (1, "6.2", "3"),
    (1, "6.2.1", "3.1"),
    (1, "8.1", "7.2"),
)


class SubjectPromptExampleTests(unittest.TestCase):
    def examples(self):
        blocks = re.findall(
            r"<example>\n(.*?)\n</example>", PROMPT_PATH.read_text(), re.S
        )
        self.assertEqual(len(blocks), 2)
        examples = []
        for block in blocks:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S)
            self.assertIsNotNone(output)
            examples.append(
                experiment_inputs.validate(
                    {"adapter": "subjects"}, {}, output.group(1), None
                )["parsed"]["subjects"]
            )
        return examples

    def assert_in_every_branch(self, entries, child_subject, parent_subject):
        parents = [e for e in entries if e["subject"] == parent_subject]
        self.assertTrue(parents, parent_subject)
        for parent in parents:
            with self.subTest(parent=parent["number"], subject=child_subject):
                self.assertTrue(
                    any(
                        e["subject"] == child_subject
                        and e["number"].startswith(parent["number"] + ".")
                        for e in entries
                    ),
                    f"{child_subject!r} missing beneath {parent_subject!r}",
                )

    def test_binocular_observation_appears_in_every_binoculars_branch(self):
        self.assert_in_every_branch(
            self.examples()[0],
            "Lunar eclipse observation through binoculars",
            "Binoculars",
        )

    def test_reviewed_relationships_hold_in_every_copy_of_each_parent(self):
        examples = self.examples()
        for example, subjects, relationships in (
            (0, LUNAR_SUBJECTS, LUNAR_RELATIONSHIPS),
            (1, RAILWAY_SUBJECTS, RAILWAY_RELATIONSHIPS),
        ):
            for child, parent in relationships:
                with self.subTest(example=example, child=child, parent=parent):
                    self.assert_in_every_branch(
                        examples[example], subjects[child], subjects[parent]
                    )

    def test_general_subjects_and_individual_instructions_keep_valid_parents(self):
        examples = self.examples()
        headings = (LUNAR_SUBJECTS, RAILWAY_SUBJECTS)
        for example, child, parent in INVALID_RELATIONSHIPS:
            entries = examples[example]
            child_subject = headings[example][child]
            parent_subject = headings[example][parent]
            with self.subTest(child=child_subject, parent=parent_subject):
                parents = [e for e in entries if e["subject"] == parent_subject]
                self.assertTrue(parents, parent_subject)
                self.assertTrue(any(e["subject"] == child_subject for e in entries))
                for entry in parents:
                    self.assertFalse(
                        any(
                            e["subject"] == child_subject
                            and e["number"].startswith(entry["number"] + ".")
                            for e in entries
                        )
                    )

    def test_subject_coverage_and_output_field_order(self):
        for entries, subjects in zip(
            self.examples(), (LUNAR_SUBJECTS, RAILWAY_SUBJECTS)
        ):
            self.assertEqual({e["subject"] for e in entries}, set(subjects.values()))
            for entry in entries:
                self.assertEqual(list(entry), ["number", "context", "subject"])

    def test_every_rendered_relationship_has_a_reviewed_basis(self):
        for entries, subjects, relationships in zip(
            self.examples(),
            (LUNAR_SUBJECTS, RAILWAY_SUBJECTS),
            (LUNAR_RELATIONSHIPS, RAILWAY_RELATIONSHIPS),
        ):
            ancestors = {node: set() for node in subjects}
            for child, parent in relationships:
                ancestors[child].add(parent)
            while True:
                expanded = {
                    child: parents.union(
                        *(ancestors[parent] for parent in parents)
                    )
                    for child, parents in ancestors.items()
                }
                if expanded == ancestors:
                    break
                ancestors = expanded
            by_number = {e["number"]: e for e in entries}
            ids = {subject: node for node, subject in subjects.items()}
            for entry in entries:
                if "." not in entry["number"]:
                    continue
                parent = by_number[entry["number"].rsplit(".", 1)[0]]
                self.assertIn(
                    ids[parent["subject"]], ancestors[ids[entry["subject"]]]
                )

    def test_instructions_and_example_posts_are_preserved(self):
        directory = PROMPT_PATH.parent.parent
        approved = (directory / "asv6.51/ASv6.51.md").read_text()
        draft = (directory / "asv6.52/ASv6.52.md").read_text()
        fixed = PROMPT_PATH.read_text()
        self.assertEqual(
            fixed.split("<example>", 1)[0], approved.split("<example>", 1)[0]
        )
        self.assertEqual(
            re.findall(r"<post>\n(.*?)\n</post>", fixed, re.S),
            re.findall(r"<post>\n(.*?)\n</post>", draft, re.S),
        )


if __name__ == "__main__":
    unittest.main()
