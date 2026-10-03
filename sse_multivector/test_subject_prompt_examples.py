"""Offline checks for the SP examples' declared hierarchy relationships."""

import json
import re
import unittest
from unittest.mock import patch
from collections import Counter
from pathlib import Path

from sse_multivector import experiment_inputs


PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.53/ASv6.53.md"
)
FOCUSED_PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.58/ASv6.58.md"
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



# R IDs refer to the rule-to-case map in subject-prompt-goal-v1/asv6.50/README.md.
# Subjects and relationships are reviewed expectations, not model-generated truth.
FOCUSED_CASES = (
    {
        "id": "C1",
        "purpose": "Reference resolution and heading-established repair purpose, with general and qualified items and cutting retained.",
        "post": "Boiler repair:\nOne tube.\nCutting it.",
        "subjects": {
            "tubes": "Tubes",
            "one_tube": "One tube",
            "repair_tube": "One tube for boiler repair",
            "tube_cutting": "Cutting one tube",
            "repair_tube_cutting": "Cutting one tube for boiler repair",
            "boilers": "Boilers",
            "repair": "Repair",
            "boiler_repair": "Boiler repair",
            "cutting": "Cutting",
            "boiler_repair_cutting": "Cutting for boiler repair",
        },
        "relationships": (
            ("one_tube", "tubes"),
            ("repair_tube", "one_tube"),
            ("repair_tube", "boiler_repair"),
            ("tube_cutting", "one_tube"),
            ("tube_cutting", "cutting"),
            ("repair_tube_cutting", "repair_tube"),
            ("repair_tube_cutting", "tube_cutting"),
            ("repair_tube_cutting", "boiler_repair_cutting"),
            ("boiler_repair", "repair"),
            ("boiler_repair", "boilers"),
            ("boiler_repair_cutting", "cutting"),
            ("boiler_repair_cutting", "boiler_repair"),
        ),
        "primary_rules": (
            "R01", "R02", "R04", "R16", "R20", "R21", "R22", "R23",
            "R25", "R26", "R27", "R28", "R29", "R30", "R31", "R34",
        ),
        "secondary_rules": (
            ("R18", "One tube remains alongside its repair-qualified and cutting subjects."),
            ("R24", "Nonempty output contrasts with C3's empty array."),
        ),
        "invalid": (
            ("cutting", "boiler_repair"),
            ("boiler_repair", "cutting"),
            ("boilers", "boiler_repair"),
            ("tubes", "boiler_repair"),
            ("one_tube", "boiler_repair"),
            ("tube_cutting", "boiler_repair"),
            ("one_tube", "repair_tube"),
            ("tube_cutting", "repair_tube"),
            ("repair_tube", "cutting"),
            ("boiler_repair", "tubes"),
            ("boiler_repair_cutting", "tubes"),
        ),
    },
    {
        "id": "C2",
        "purpose": "Names, hashtags, figurative labels, rhetorical meaning and an unresolved name.",
        "post": "The app #RavenWorks is a lifesaver, figuratively speaking—how could I not appreciate it? Also: AmberLoop.",
        "subjects": {
            "apps": "Apps",
            "ravenworks": "RavenWorks app",
            "help": "Help",
            "app_help": "Help from apps",
            "ravenworks_help": "Help from the RavenWorks app",
            "appreciation": "Appreciation",
            "app_appreciation": "Appreciation for apps",
            "ravenworks_appreciation": "Appreciation for the RavenWorks app",
            "amberloop": "AmberLoop",
        },
        "relationships": (
            ("ravenworks", "apps"),
            ("app_help", "apps"),
            ("app_help", "help"),
            ("ravenworks_help", "app_help"),
            ("ravenworks_help", "ravenworks"),
            ("app_appreciation", "apps"),
            ("app_appreciation", "appreciation"),
            ("ravenworks_appreciation", "app_appreciation"),
            ("ravenworks_appreciation", "ravenworks"),
        ),
        "primary_rules": (
            "R03", "R05", "R06", "R17",
        ),
        "secondary_rules": (
            ("R02", "Named referent: 'it' retains RavenWorks's stated app type and hashtag-established name."),
            ("R12", "Unresolved name retained without commentary about its unknown type."),
        ),
        "invalid": (
            ("amberloop", "apps"),
            ("amberloop", "help"),
            ("amberloop", "appreciation"),
        ),
    },
    {
        "id": "C3",
        "purpose": "URL and opaque identifier bodies without surrounding subject evidence.",
        "post": "https://birds.example/repair?count=12\n8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f",
        "subjects": {
        },
        "relationships": (
        ),
        "primary_rules": (
            "R07", "R24",
        ),
        "invalid": (
        ),
    },
    {
        "id": "C4",
        "purpose": "URL and identifier subjects established by prose, without a cross-link.",
        "post": "Profile URL: https://birds.example/repair?count=12\nEvent ID: 8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f",
        "subjects": {
            "urls": "URLs",
            "profile_urls": "Profile URLs",
            "profiles": "Profiles",
            "identifiers": "Identifiers",
            "event_identifiers": "Event identifiers",
            "events": "Events",
        },
        "relationships": (
            ("profile_urls", "urls"),
            ("profile_urls", "profiles"),
            ("event_identifiers", "identifiers"),
            ("event_identifiers", "events"),
        ),
        "primary_rules": (
            "R08",
        ),
        "secondary_rules": (
            ("R07", "Relevant prose establishes topics while URL bodies still contribute no birds, repair or count."),
        ),
        "invalid": (
            ("profile_urls", "event_identifiers"),
            ("event_identifiers", "profile_urls"),
        ),
    },
    {
        "id": "C5",
        "purpose": "Two direct ambiguity interpretations, independent co-mention and statement order.",
        "post": "I saw her duck. I bought a notebook.",
        "subjects": {
            "ducks": "Ducks",
            "owned_duck": "A person's duck",
            "duck_observation": "Observation of a person's duck",
            "ducking": "Ducking",
            "person_ducking": "A person ducking",
            "ducking_observation": "Observation of a person ducking",
            "people": "People",
            "observation": "Observation",
            "notebooks": "Notebooks",
            "purchases": "Purchases",
            "notebook_purchase": "Purchase of a notebook",
        },
        "relationships": (
            ("owned_duck", "ducks"),
            ("owned_duck", "people"),
            ("duck_observation", "owned_duck"),
            ("duck_observation", "observation"),
            ("person_ducking", "ducking"),
            ("person_ducking", "people"),
            ("ducking_observation", "person_ducking"),
            ("ducking_observation", "observation"),
            ("notebook_purchase", "notebooks"),
            ("notebook_purchase", "purchases"),
        ),
        "primary_rules": (
            "R09", "R10", "R11", "R12", "R19",
        ),
        "invalid": (
            ("notebook_purchase", "observation"),
            ("duck_observation", "ducking_observation"),
            ("ducking_observation", "duck_observation"),
            ("notebooks", "ducks"),
            ("notebooks", "people"),
        ),
    },
    {
        "id": "C6",
        "purpose": "Count versus length, preserved negation, both comparison sides and no unstated arithmetic.",
        "post": "2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.",
        "subjects": {
            "cables": "Cables",
            "lengths": "Cable lengths",
            "two_m": "2 m cables",
            "three_m": "3 m cables",
            "a": "2 m cable A",
            "b": "3 m cable B",
            "pairs": "Pairs of cables",
            "pair": "Pair consisting of 2 m cable A and 3 m cable B",
            "comparisons": "Cable length comparisons",
            "not_longer": "2 m cable A not longer than 3 m cable B",
        },
        "relationships": (
            ("lengths", "cables"),
            ("two_m", "lengths"),
            ("three_m", "lengths"),
            ("a", "two_m"),
            ("b", "three_m"),
            ("pairs", "cables"),
            ("pair", "pairs"),
            ("pair", "a"),
            ("pair", "b"),
            ("comparisons", "lengths"),
            ("not_longer", "comparisons"),
            ("not_longer", "pair"),
        ),
        "primary_rules": (
            "R13", "R14", "R18", "R32", "R33",
        ),
        "secondary_rules": (
            ("R15", "No unstated 1 m difference or 5 m total."),
            ("R17", "The pair combines the count, both named cables and their stated lengths."),
            ("R20", "The pair fits both cable headings; either cable can be mentioned without the other."),
        ),
        "invalid": (
            ("pairs", "lengths"),
            ("a", "b"),
            ("b", "a"),
            ("a", "pair"),
            ("b", "pair"),
        ),
    },
    {
        "id": "C7",
        "purpose": "Explicit arithmetic result with separately retained addends and result.",
        "post": "2 + 3 = 5.",
        "subjects": {
            "arithmetic": "Arithmetic",
            "addition": "Addition",
            "addends": "Addends",
            "two": "2 as an addend",
            "three": "3 as an addend",
            "results": "Addition results",
            "five": "5 as an addition result",
            "sum": "Addition of 2 and 3 yielding 5",
        },
        "relationships": (
            ("addition", "arithmetic"),
            ("addends", "addition"),
            ("two", "addends"),
            ("three", "addends"),
            ("results", "addition"),
            ("five", "results"),
            ("sum", "two"),
            ("sum", "three"),
            ("sum", "five"),
        ),
        "primary_rules": (
            "R15",
        ),
        "secondary_rules": (
            ("R13", "Arithmetic roles distinguish addends 2 and 3 from result 5."),
        ),
        "invalid": (
        ),
    },
)


class FocusedSubjectPromptExampleTests(unittest.TestCase):
    def examples(self):
        examples = {}
        for block in re.findall(
            r"<example>\n(.*?)\n</example>",
            FOCUSED_PROMPT_PATH.read_text(),
            re.S,
        ):
            post = re.search(r"<post>\n(.*?)\n</post>", block, re.S)
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S)
            self.assertIsNotNone(post)
            self.assertIsNotNone(output)
            self.assertNotIn(post.group(1), examples)
            examples[post.group(1)] = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output.group(1), None
            )["parsed"]["subjects"]
        return examples

    def test_consolidated_examples_omit_overlapping_lunar_and_advice_cases(self):
        posts = set(self.examples())
        for post in (
            "I watched a lunar eclipse through binoculars. Tried sketching the Moon, but clouds kept hiding it.",
            "Advice: book ahead and stay on marked routes.",
        ):
            with self.subTest(post=post):
                self.assertNotIn(post, posts)

    def test_remaining_ambiguity_has_two_direct_interpretations(self):
        examples = self.examples()
        post = "I saw her duck. I bought a notebook."
        self.assertIn(post, set(examples), "missing remaining-ambiguity example")
        subjects = {entry["subject"] for entry in examples[post]}
        self.assertIn("Observation of a person's duck", subjects)
        self.assertIn("Observation of a person ducking", subjects)

    def test_list_heading_establishes_the_tube_and_cutting_repair_purpose(self):
        examples = self.examples()
        post = next(iter(examples))
        lines = post.splitlines()
        self.assertEqual(lines[0], "Boiler repair:", "missing purpose heading")
        self.assertEqual(lines[1:], ["One tube.", "Cutting it."])
        for entry in examples[post]:
            with self.subTest(number=entry["number"]):
                self.assertNotIn("that repair", entry["context"])
                if "for boiler repair" in entry["subject"]:
                    self.assertIn("heading", entry["context"])

    def test_cutting_for_boiler_repair_retains_general_and_qualified_subjects(self):
        entries = self.examples()[FOCUSED_CASES[0]["post"]]
        subjects = {entry["subject"] for entry in entries}
        self.assertIn("Cutting", subjects)
        self.assertIn("Boiler repair", subjects)
        self.assertIn("Cutting for boiler repair", subjects)
        for parent in entries:
            if parent["subject"] not in {"Cutting", "Boiler repair"}:
                continue
            descendants = {
                entry["subject"] for entry in entries
                if entry["number"].startswith(parent["number"] + ".")
            }
            with self.subTest(parent=parent["number"]):
                self.assertIn("Cutting for boiler repair", descendants)
                if parent["subject"] == "Boiler repair":
                    self.assertNotIn("Cutting", descendants)

    def test_quantified_tube_keeps_its_repair_purpose_in_every_valid_branch(self):
        entries = self.examples()[FOCUSED_CASES[0]["post"]]
        subjects = {entry["subject"] for entry in entries}
        self.assertIn("One tube", subjects)
        self.assertIn("One tube for boiler repair", subjects)
        self.assertIn("Cutting one tube", subjects)
        self.assertIn("Cutting one tube for boiler repair", subjects)
        for parent in entries:
            descendants = {
                entry["subject"] for entry in entries
                if entry["number"].startswith(parent["number"] + ".")
            }
            with self.subTest(parent=parent["number"]):
                if parent["subject"] in {"One tube", "Boiler repair"}:
                    self.assertIn("One tube for boiler repair", descendants)
                if parent["subject"] in {
                    "One tube for boiler repair", "Cutting one tube",
                    "Cutting for boiler repair",
                }:
                    self.assertIn("Cutting one tube for boiler repair", descendants)
                if parent["subject"] == "Boiler repair":
                    self.assertNotIn("One tube", descendants)
                    self.assertNotIn("Cutting one tube", descendants)

    def test_each_instruction_is_traced_to_a_present_case(self):
        self.assertEqual(set(self.examples()), {c["post"] for c in FOCUSED_CASES})
        primary_rules = Counter(
            rule for case in FOCUSED_CASES for rule in case["primary_rules"]
        )
        self.assertEqual(
            primary_rules,
            Counter({f"R{i:02d}": 1 for i in range(1, 35)}),
            "each instruction must have exactly one primary example",
        )
        self.assertEqual(len({c["id"] for c in FOCUSED_CASES}), len(FOCUSED_CASES))
        for case in FOCUSED_CASES:
            self.assertTrue(case["purpose"])
            secondary_rules = case.get("secondary_rules", ())
            self.assertEqual(
                len(secondary_rules), len({rule for rule, _ in secondary_rules})
            )
            for rule, aspect in secondary_rules:
                self.assertIn(rule, primary_rules)
                self.assertNotIn(rule, case["primary_rules"])
                self.assertTrue(aspect.strip())

    def test_all_expected_subjects_and_output_fields_are_retained(self):
        examples = self.examples()
        for case in FOCUSED_CASES:
            with self.subTest(case=case["id"]):
                entries = examples[case["post"]]
                self.assertEqual(
                    {e["subject"] for e in entries},
                    set(case["subjects"].values()),
                )
                for entry in entries:
                    self.assertEqual(list(entry), ["number", "context", "subject"])

    def test_each_reviewed_relationship_holds_beneath_every_parent_copy(self):
        examples = self.examples()
        for case in FOCUSED_CASES:
            entries = examples[case["post"]]
            for child, parent in case["relationships"]:
                child_subject = case["subjects"][child]
                parent_subject = case["subjects"][parent]
                parents = [e for e in entries if e["subject"] == parent_subject]
                self.assertTrue(parents, parent_subject)
                for parent_entry in parents:
                    with self.subTest(case=case["id"], parent=parent_entry["number"], child=child):
                        self.assertTrue(any(
                            e["subject"] == child_subject
                            and e["number"].startswith(parent_entry["number"] + ".")
                            for e in entries
                        ))

    def test_all_displayed_relationships_have_a_reviewed_basis(self):
        examples = self.examples()
        for case in FOCUSED_CASES:
            ancestors = {node: set() for node in case["subjects"]}
            for child, parent in case["relationships"]:
                ancestors[child].add(parent)
            while True:
                expanded = {
                    child: parents.union(*(ancestors[parent] for parent in parents))
                    for child, parents in ancestors.items()
                }
                if expanded == ancestors:
                    break
                ancestors = expanded
            ids = {subject: node for node, subject in case["subjects"].items()}
            entries = examples[case["post"]]
            by_number = {e["number"]: e for e in entries}
            for entry in entries:
                if "." in entry["number"]:
                    parent = by_number[entry["number"].rsplit(".", 1)[0]]
                    with self.subTest(case=case["id"], number=entry["number"]):
                        self.assertIn(ids[parent["subject"]], ancestors[ids[entry["subject"]]])

    def test_general_subjects_and_independent_mentions_keep_valid_parents(self):
        examples = self.examples()
        for case in FOCUSED_CASES:
            entries = examples[case["post"]]
            for child, parent in case["invalid"]:
                child_subject = case["subjects"][child]
                parent_subject = case["subjects"][parent]
                parents = [e for e in entries if e["subject"] == parent_subject]
                self.assertTrue(parents, parent_subject)
                self.assertTrue(any(e["subject"] == child_subject for e in entries))
                for parent_entry in parents:
                    with self.subTest(case=case["id"], child=child, parent=parent):
                        self.assertFalse(any(
                            e["subject"] == child_subject
                            and e["number"].startswith(parent_entry["number"] + ".")
                            for e in entries
                        ))

    def test_identical_opaque_bodies_require_surrounding_subject_prose(self):
        cases = {case["id"]: case for case in FOCUSED_CASES}
        bare = cases["C3"]["post"].splitlines()
        labelled = cases["C4"]["post"].splitlines()
        self.assertEqual(labelled, ["Profile URL: " + bare[0], "Event ID: " + bare[1]])
        examples = self.examples()
        self.assertEqual(examples[cases["C3"]["post"]], [])
        self.assertEqual(
            {e["subject"] for e in examples[cases["C4"]["post"]]},
            {"URLs", "Profile URLs", "Profiles", "Identifiers", "Event identifiers", "Events"},
        )

    def test_instructions_and_retained_focused_cases_are_preserved(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        approved = (directory / "asv6.51/ASv6.51.md").read_text()
        expanded = (directory / "asv6.54/ASv6.54.md").read_text()
        previous = (directory / "asv6.55/ASv6.55.md").read_text()
        last_approved = (directory / "asv6.57/ASv6.57.md").read_text()
        focused = FOCUSED_PROMPT_PATH.read_text()
        self.assertEqual(
            focused.split("<example>", 1)[0], approved.split("<example>", 1)[0]
        )
        self.assertEqual(
            re.findall(r"<example>\n.*?\n</example>", previous, re.S),
            [
                block for index, block in enumerate(
                    re.findall(r"<example>\n.*?\n</example>", expanded, re.S)
                ) if index not in (0, 2)
            ],
        )
        current_blocks = re.findall(r"<example>\n.*?\n</example>", focused, re.S)
        approved_blocks = re.findall(r"<example>\n.*?\n</example>", last_approved, re.S)
        self.assertEqual(len(current_blocks), 7)
        self.assertEqual(current_blocks[1:], approved_blocks[1:])
        headings = []
        for block in (current_blocks[0], approved_blocks[0]):
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S)
            entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output.group(1), None
            )["parsed"]["subjects"]
            headings.append([(entry["number"], entry["subject"]) for entry in entries])
        self.assertEqual(headings[0], headings[1])
        self.assertEqual(
            focused.split("<example>", 1)[0], last_approved.split("<example>", 1)[0]
        )
        self.assertNotEqual(current_blocks[0], approved_blocks[0])


class AutonomousSubjectPromptCandidateTests(unittest.TestCase):
    def test_asv659_preserves_the_reviewed_rule_examples(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        baseline = FOCUSED_PROMPT_PATH.read_text()
        candidate = (directory / "asv6.59/ASv6.59.md").read_text()
        blocks = re.findall(r"<example>\n.*?\n</example>", candidate, re.S)
        self.assertEqual(
            blocks, re.findall(r"<example>\n.*?\n</example>", baseline, re.S)
        )
        self.assertEqual(len(blocks), len(FOCUSED_CASES))
        for block in blocks:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S)
            experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output.group(1), None
            )

    def test_autonomous_templates_contain_exact_candidate_and_post_variable(self):
        root = Path(__file__).parent
        for version in range(59, 88):
            with self.subTest(version=version):
                candidate = (
                    root / f"subject-prompt-goal-v1/asv6.{version}/ASv6.{version}.md"
                ).read_text()
                template = (
                    root / f"experiment_specs/asv6.{version}-hr01-post-template.txt"
                ).read_text()
                self.assertEqual(template, candidate + "\n<post>\n{POST}\n</post>")

    def test_asv660_explanation_preserves_reviewed_posts_outputs_and_rules(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        baseline = (directory / "asv6.59/ASv6.59.md").read_text()
        candidate = (directory / "asv6.60/ASv6.60.md").read_text()
        without_explanation = re.sub(
            r"<explanation>\n.*?\n</explanation>\n\n", "", candidate, flags=re.S
        )
        self.assertNotEqual(candidate, without_explanation)
        self.assertEqual(without_explanation, baseline)

    def test_asv661_only_revises_the_named_app_example(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        baseline = (directory / "asv6.60/ASv6.60.md").read_text()
        candidate = (directory / "asv6.61/ASv6.61.md").read_text()
        self.assertEqual(
            baseline.split("<example>", 1)[0], candidate.split("<example>", 1)[0]
        )
        before = re.findall(r"<example>\n.*?\n</example>", baseline, re.S)
        after = re.findall(r"<example>\n.*?\n</example>", candidate, re.S)
        self.assertEqual(len(after), 7)
        self.assertEqual(before[:1] + before[2:], after[:1] + after[2:])
        self.assertNotEqual(before[1], after[1])

    def test_asv661_retains_rule_coverage_and_valid_example_relationships(self):
        app_case = {
            **FOCUSED_CASES[1],
            "purpose": "Named new app, first-use help and appreciation, rhetoric and unresolved independent name.",
            "post": "On my first use, the new app #RavenWorks was a lifesaver, figuratively speaking—how could I not appreciate it on that first use? Also: AmberLoop.",
            "subjects": {
                "apps": "Apps",
                "named": "RavenWorks app",
                "new": "New RavenWorks app",
                "first": "First use of the new RavenWorks app",
                "help": "Help",
                "named_help": "Help from the new RavenWorks app",
                "first_help": "Help from the new RavenWorks app on first use",
                "appreciation": "Appreciation",
                "named_appreciation": "Appreciation for the new RavenWorks app",
                "first_appreciation": "Appreciation for the new RavenWorks app on first use",
                "first_use": "First use",
                "unknown": "AmberLoop",
            },
            "relationships": (
                ("named", "apps"), ("new", "named"),
                ("first", "new"), ("first", "first_use"),
                ("named_help", "new"), ("named_help", "help"),
                ("first_help", "first"), ("first_help", "named_help"),
                ("named_appreciation", "new"),
                ("named_appreciation", "appreciation"),
                ("first_appreciation", "first"),
                ("first_appreciation", "named_appreciation"),
            ),
            "secondary_rules": FOCUSED_CASES[1]["secondary_rules"] + (
                ("R20", "Newness and first use remain in children under qualified parents."),
                ("R22", "First-use help and appreciation occur beneath every applicable parent copy."),
            ),
            "invalid": (
                ("named", "new"), ("named_help", "first"),
                ("named_appreciation", "first"), ("first", "named_help"),
                ("first_help", "named_appreciation"),
                ("first_appreciation", "named_help"),
                ("unknown", "apps"), ("unknown", "help"),
                ("unknown", "appreciation"), ("unknown", "first_use"),
            ),
        }
        for version in range(61, 74):
            repair_case = FOCUSED_CASES[0]
            if version >= 62:
                repair_case = {
                    **repair_case,
                    "post": repair_case["post"] + "\nSeparately, olive oil for cooking.",
                    "subjects": {**repair_case["subjects"],
                        "oils": "Oils", "olive": "Olive oil",
                        "cooking_oils": "Oils for cooking",
                        "cooking_olive": "Olive oil for cooking",
                        "cooking": "Cooking",
                    },
                    "relationships": repair_case["relationships"] + (
                        ("olive", "oils"), ("cooking_oils", "oils"),
                        ("cooking_oils", "cooking"),
                        ("cooking_olive", "olive"),
                        ("cooking_olive", "cooking_oils"),
                    ),
                    "invalid": repair_case["invalid"] + (
                        ("olive", "cooking_oils"), ("olive", "cooking"),
                        ("oils", "cooking_oils"), ("oils", "cooking"),
                        ("cooking_olive", "boiler_repair"),
                    ),
                }
            if version >= 68:
                repair_case = {
                    **FOCUSED_CASES[0],
                    "purpose": "Count/reference/purpose plus explicit edible/inedible qualities and a retained oil-use combination.",
                    "post": "Repair:\nOne tube.\nCutting it.\nSeparately, edible olive oil for cooking and inedible olive oil for a lamp.",
                    "subjects": {
                        "tubes": "Tubes", "one": "One tube",
                        "repair_tube": "One tube for repair",
                        "cut_tube": "Cutting one tube",
                        "repair_cut_tube": "Cutting one tube for repair",
                        "repair": "Repair", "cutting": "Cutting",
                        "repair_cutting": "Cutting for repair",
                        "oils": "Oils", "olive": "Olive oil",
                        "edible": "Edible oils", "inedible": "Inedible oils",
                        "edible_olive": "Edible olive oil",
                        "inedible_olive": "Inedible olive oil",
                        "cooking_olive": "Edible olive oil for cooking",
                        "lamp_olive": "Inedible olive oil for a lamp",
                        "cooking": "Cooking", "lamps": "Lamps",
                        "oil_combination": "Edible olive oil for cooking and inedible olive oil for a lamp",
                    },
                    "relationships": (
                        ("one", "tubes"), ("repair_tube", "one"),
                        ("repair_tube", "repair"), ("cut_tube", "one"),
                        ("cut_tube", "cutting"),
                        ("repair_cut_tube", "repair_tube"),
                        ("repair_cut_tube", "cut_tube"),
                        ("repair_cut_tube", "repair_cutting"),
                        ("repair_cutting", "repair"),
                        ("repair_cutting", "cutting"),
                        ("olive", "oils"), ("edible", "oils"),
                        ("inedible", "oils"),
                        ("edible_olive", "olive"), ("edible_olive", "edible"),
                        ("inedible_olive", "olive"), ("inedible_olive", "inedible"),
                        ("cooking_olive", "edible_olive"),
                        ("cooking_olive", "cooking"),
                        ("lamp_olive", "inedible_olive"), ("lamp_olive", "lamps"),
                        ("oil_combination", "cooking_olive"),
                        ("oil_combination", "lamp_olive"),
                    ),
                    "invalid": (
                        ("tubes", "repair"), ("one", "repair"),
                        ("cut_tube", "repair"), ("cutting", "repair"),
                        ("repair", "cutting"), ("one", "repair_tube"),
                        ("cut_tube", "repair_tube"), ("repair_tube", "cutting"),
                        ("olive", "edible"), ("olive", "inedible"),
                        ("olive", "cooking"), ("olive", "lamps"),
                        ("edible_olive", "inedible"),
                        ("inedible_olive", "edible"),
                        ("edible_olive", "cooking"), ("inedible_olive", "lamps"),
                        ("cooking_olive", "lamps"), ("lamp_olive", "cooking"),
                        ("oil_combination", "repair"),
                        ("cooking_olive", "oil_combination"),
                        ("lamp_olive", "oil_combination"),
                    ),
                    "secondary_rules": (
                        ("R18", "Counted tube and qualified cutting remain; the stated oil-use combination retains both constituents."),
                        ("R24", "Nonempty output contrasts with C3's empty array."),
                    ),
                }
            if version >= 72:
                repair_case = {
                    **FOCUSED_CASES[0],
                    "purpose": "Resolved counted-water reference, soup-preparation purpose and every valid parent copy.",
                    "post": "Soup preparation:\nOne cup of water.\nHeating it.",
                    "subjects": {
                        "water": "Water", "one": "One cup of water",
                        "qualified_water": "One cup of water for soup preparation",
                        "heating_one": "Heating one cup of water",
                        "full": "Heating one cup of water for soup preparation",
                        "soup": "Soup preparation", "heating": "Heating",
                        "qualified_heating": "Heating for soup preparation",
                    },
                    "relationships": (
                        ("one", "water"), ("qualified_water", "one"),
                        ("qualified_water", "soup"), ("heating_one", "one"),
                        ("heating_one", "heating"),
                        ("qualified_heating", "soup"),
                        ("qualified_heating", "heating"),
                        ("full", "qualified_water"),
                        ("full", "heating_one"),
                        ("full", "qualified_heating"),
                    ),
                    "invalid": (
                        ("water", "soup"), ("one", "soup"),
                        ("heating", "soup"), ("heating_one", "soup"),
                        ("one", "qualified_water"),
                        ("heating_one", "qualified_water"),
                        ("qualified_water", "heating"),
                        ("soup", "heating"),
                    ),
                    "secondary_rules": (
                        ("R18", "Counted water and qualified heating remain separate subjects."),
                        ("R24", "Nonempty output contrasts with C3's empty array."),
                    ),
                }
            current_app = app_case
            if version >= 73:
                current_app = {
                    **app_case,
                    "purpose": "Named new app, figurative first-use help, blocking exception, rhetoric and unresolved blocker type.",
                    "post": "On my first use, the new app #RavenWorks was a lifesaver, figuratively speaking, unless AmberLoop blocked it—how could I not appreciate the app on that first use?",
                    "subjects": {
                        **app_case["subjects"],
                        "blocking": "Blocking",
                        "blocker_app": "AmberLoop blocking the new RavenWorks app",
                        "conditional_help": "Help from the new RavenWorks app on first use unless AmberLoop blocks the app",
                    },
                    "relationships": app_case["relationships"] + (
                        ("blocker_app", "blocking"),
                        ("blocker_app", "unknown"), ("blocker_app", "new"),
                        ("conditional_help", "first_help"),
                        ("conditional_help", "blocker_app"),
                    ),
                    "invalid": app_case["invalid"] + (
                        ("unknown", "blocking"),
                        ("blocker_app", "first_help"),
                        ("first_help", "blocker_app"),
                        ("blocker_app", "named_appreciation"),
                    ),
                    "secondary_rules": app_case["secondary_rules"] + (
                        ("R04", "The blocking pronoun refers to the named new app."),
                        ("R32", "The unless relationship remains in the complete help subject."),
                    ),
                }
            cases = (repair_case, current_app) + FOCUSED_CASES[2:]
            path = FOCUSED_PROMPT_PATH.parent.parent / f"asv6.{version}/ASv6.{version}.md"
            # Reuse semantic fixtures through production validation, patching
            # only test inputs, never a production API or path.
            with self.subTest(version=version), patch(
                __name__ + ".FOCUSED_PROMPT_PATH", path
            ), patch(__name__ + ".FOCUSED_CASES", cases):
                checks = FocusedSubjectPromptExampleTests()
                checks.test_each_instruction_is_traced_to_a_present_case()
                checks.test_all_expected_subjects_and_output_fields_are_retained()
                checks.test_each_reviewed_relationship_holds_beneath_every_parent_copy()
                checks.test_all_displayed_relationships_have_a_reviewed_basis()
                checks.test_general_subjects_and_independent_mentions_keep_valid_parents()

    def test_asv662_preserves_other_cases_and_the_reviewed_repair_entries(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        before = (directory / "asv6.61/ASv6.61.md").read_text()
        after = (directory / "asv6.62/ASv6.62.md").read_text()
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in (before, after)]
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        outputs = []
        for b in blocks:
            raw = re.search(r"<output>\n(.*?)\n</output>", b[0], re.S).group(1)
            outputs.append(experiment_inputs.validate(
                {"adapter": "subjects"}, {}, raw, None
            )["parsed"]["subjects"])
        self.assertEqual(outputs[0], outputs[1][:len(outputs[0])])

    def test_asv663_preserves_every_reviewed_example(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        before = (directory / "asv6.62/ASv6.62.md").read_text()
        after = (directory / "asv6.63/ASv6.63.md").read_text()
        self.assertEqual(
            re.findall(r"<example>\n.*?\n</example>", before, re.S),
            re.findall(r"<example>\n.*?\n</example>", after, re.S),
        )

    def test_asv664_only_compacts_json_layout(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent

        def normalized(version):
            source = (directory / f"asv6.{version}/ASv6.{version}.md").read_text()

            def output(match):
                parsed = experiment_inputs.validate(
                    {"adapter": "subjects"}, {}, match.group(1), None
                )["parsed"]
                return json.dumps(parsed, ensure_ascii=False)

            return re.sub(r"<output>\n(.*?)\n</output>", output, source, flags=re.S)

        self.assertEqual(normalized(63), normalized(64))

    def test_asv665_only_moves_existing_hierarchy_instructions(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        before = (directory / "asv6.64/ASv6.64.md").read_text()
        after = (directory / "asv6.65/ASv6.65.md").read_text()
        start = before.index("For each enumerated subject, derive broader headings")
        end = before.index("\n\nReturn only one JSON object", start)
        rules = before[start:end]
        expected = before.replace(rules + "\n\n", "", 1)
        last = expected.rindex("</example>") + len("</example>")
        expected = expected[:last] + "\n\n" + rules + expected[last:]
        self.assertEqual(expected, after)

    def test_domain_and_copy_clarifications_preserve_reviewed_examples(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        baseline = (directory / "asv6.65/ASv6.65.md").read_text()
        blocks = re.findall(r"<example>\n.*?\n</example>", baseline, re.S)
        for version in (66, 67):
            with self.subTest(version=version):
                source = (directory / f"asv6.{version}/ASv6.{version}.md").read_text()
                self.assertEqual(blocks, re.findall(r"<example>\n.*?\n</example>", source, re.S))

    def test_asv668_only_revises_the_restriction_example(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        before = (directory / "asv6.67/ASv6.67.md").read_text()
        after = (directory / "asv6.68/ASv6.68.md").read_text()
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertNotEqual(blocks[0][0], blocks[1][0])
        for tag in ("<example>", "</example>"):
            if tag.startswith("</"):
                self.assertEqual(before.rsplit(tag, 1)[1], after.rsplit(tag, 1)[1])
            else:
                self.assertEqual(before.split(tag, 1)[0], after.split(tag, 1)[0])

    def test_asv669_preserves_every_reviewed_example(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        before = (directory / "asv6.68/ASv6.68.md").read_text()
        after = (directory / "asv6.69/ASv6.69.md").read_text()
        self.assertEqual(
            re.findall(r"<example>\n.*?\n</example>", before, re.S),
            re.findall(r"<example>\n.*?\n</example>", after, re.S),
        )

    def test_asv670_only_shortens_example_contexts(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent

        def without_contexts(version):
            source = (directory / f"asv6.{version}/ASv6.{version}.md").read_text()

            def output(match):
                parsed = experiment_inputs.validate(
                    {"adapter": "subjects"}, {}, match.group(1), None
                )["parsed"]
                for row in parsed["subjects"]:
                    del row["context"]
                return json.dumps(parsed, ensure_ascii=False)

            return re.sub(r"<output>\n(.*?)\n</output>", output, source, flags=re.S)

        self.assertEqual(without_contexts(68), without_contexts(70))


MATERIAL_PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.74/ASv6.74.md"
)

# Agent-reviewed source meanings and entailments; these are not an independent
# semantic oracle. The adapter and every numbered occurrence are checked below.
MATERIAL_SUBJECTS = {
    "plates": "Steel plates",
    "plate": "One steel plate",
    "repair_plate": "One steel plate for chair repair",
    "bolts": "Steel bolts",
    "two_bolts": "Two steel bolts",
    "repair_bolts": "Two steel bolts for chair repair",
    "group": "One steel plate and two steel bolts for chair repair",
    "attachment": "Attaching one steel plate to a chair with two steel bolts for chair repair",
    "chairs": "Chairs",
    "repair": "Repair",
    "chair_repair": "Chair repair",
    "attaching": "Attaching",
    "counted_attachment": "Attaching one steel plate to a chair with two steel bolts",
    "repair_attaching": "Attaching for chair repair",
}
MATERIAL_RELATIONSHIPS = (
    ("plate", "plates"),
    ("repair_plate", "plate"),
    ("repair_plate", "chair_repair"),
    ("two_bolts", "bolts"),
    ("repair_bolts", "two_bolts"),
    ("repair_bolts", "chair_repair"),
    ("chair_repair", "chairs"),
    ("chair_repair", "repair"),
    ("group", "repair_plate"),
    ("group", "repair_bolts"),
    ("attachment", "group"),
    ("attachment", "counted_attachment"),
    ("attachment", "repair_attaching"),
    ("counted_attachment", "attaching"),
    ("counted_attachment", "chairs"),
    ("repair_attaching", "attaching"),
    ("repair_attaching", "chair_repair"),
)


class MaterialSubjectPromptExampleTests(unittest.TestCase):
    def material_example(self, path=None):
        source = (path or MATERIAL_PROMPT_PATH).read_text()
        block = re.findall(r"<example>\n(.*?)\n</example>", source, re.S)[0]
        post = re.search(r"<post>\n(.*?)\n</post>", block, re.S).group(1)
        output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
        entries = experiment_inputs.validate(
            {"adapter": "subjects"}, {}, output, None
        )["parsed"]["subjects"]
        return post, entries

    def assert_participants_retained(self, path=None):
        post, entries = self.material_example(path)
        # These are source-participant judgments, separate from the action.
        participants = {
            "Soup preparation:": ("Water", "Soup"),
            "Chair repair:": ("Steel plates", "Steel bolts", "Chairs"),
        }[post.splitlines()[0]]
        subjects = {e["subject"] for e in entries}
        for participant in participants:
            self.assertIn(participant, subjects, "event replaced its participant")

    def test_c1_keeps_individual_participants(self):
        self.assert_participants_retained()

    def test_saved_c1_still_demonstrates_the_participant_omission(self):
        before = MATERIAL_PROMPT_PATH.parent.parent / "asv6.73/ASv6.73.md"
        with self.assertRaisesRegex(AssertionError, "'Soup' not found"):
            self.assert_participants_retained(before)

    def ancestors(self):
        ancestors = {node: set() for node in MATERIAL_SUBJECTS}
        for child, parent in MATERIAL_RELATIONSHIPS:
            ancestors[child].add(parent)
        while True:
            expanded = {
                child: parents.union(*(ancestors[parent] for parent in parents))
                for child, parents in ancestors.items()
            }
            if expanded == ancestors:
                return ancestors
            ancestors = expanded

    def test_source_groups_and_actions_fill_every_compatible_parent_copy(self):
        _, entries = self.material_example()
        ancestors = self.ancestors()
        for child in ("repair_plate", "repair_bolts", "group", "attachment"):
            for parent in ancestors[child]:
                parents = [e for e in entries if e["subject"] == MATERIAL_SUBJECTS[parent]]
                self.assertTrue(parents, parent)
                for occurrence in parents:
                    with self.subTest(child=child, parent=occurrence["number"]):
                        self.assertTrue(any(
                            e["subject"] == MATERIAL_SUBJECTS[child]
                            and e["number"].startswith(occurrence["number"] + ".")
                            for e in entries
                        ))

    def test_every_displayed_edge_has_a_reviewed_heading_only_basis(self):
        _, entries = self.material_example()
        ids = {subject: node for node, subject in MATERIAL_SUBJECTS.items()}
        self.assertEqual({e["subject"] for e in entries}, set(ids))
        ancestors = self.ancestors()
        by_number = {e["number"]: e for e in entries}
        for entry in entries:
            if "." in entry["number"]:
                parent = by_number[entry["number"].rsplit(".", 1)[0]]
                with self.subTest(number=entry["number"]):
                    self.assertIn(ids[parent["subject"]], ancestors[ids[entry["subject"]]])

    def test_generic_materials_and_attachment_do_not_inherit_repair_purpose(self):
        _, entries = self.material_example()
        for parent in entries:
            descendants = {
                e["subject"] for e in entries
                if e["number"].startswith(parent["number"] + ".")
            }
            if parent["subject"] == "Chair repair":
                for node in ("plates", "plate", "bolts", "two_bolts", "counted_attachment"):
                    with self.subTest(parent=parent["number"], child=node):
                        self.assertNotIn(MATERIAL_SUBJECTS[node], descendants)
            if parent["subject"] == MATERIAL_SUBJECTS["group"]:
                for node in ("repair_plate", "repair_bolts", "repair_attaching"):
                    self.assertNotIn(MATERIAL_SUBJECTS[node], descendants)

    def test_revision_preserves_instructions_six_other_examples_and_schema(self):
        before = (MATERIAL_PROMPT_PATH.parent.parent / "asv6.73/ASv6.73.md").read_text()
        after = MATERIAL_PROMPT_PATH.read_text()
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        self.assertEqual(before.rsplit("</example>", 1)[1], after.rsplit("</example>", 1)[1])
        for block in blocks[1]:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output, None
            )["parsed"]["subjects"]
            for entry in entries:
                self.assertEqual(list(entry), ["number", "context", "subject"])


FOOD_PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.75/ASv6.75.md"
)

# Reviewed heading meanings, not a semantic oracle. Ingredient role is explicit
# in the source; the separate dog-recipient clause does not establish that role.
FOOD_SUBJECTS = {
    "salt": "Salt",
    "food_salt": "Salt for food seasoning",
    "tissue": "Connective tissue",
    "dog_tissue": "Connective tissue for the dog",
    "food_tissue": "One piece of connective tissue as a food ingredient for the dog",
    "meat": "Meat scraps",
    "food_meat": "Two meat scraps as food ingredients for the dog",
    "group": "One piece of connective tissue and two meat scraps as food ingredients for the dog",
    "dogs": "Dogs",
    "dog_food": "Dog food",
    "ingredients": "Dog-food ingredients",
    "food": "Food",
    "seasoning": "Food seasoning",
    "mixing": "Mixing",
    "food_mixing": "Mixing food ingredients for the dog",
    "complete_mixing": "Mixing food ingredients for the dog: one piece of connective tissue and two meat scraps",
}
FOOD_RELATIONSHIPS = (
    ("food_salt", "salt"),
    ("food_salt", "seasoning"),
    ("seasoning", "food"),
    ("dog_tissue", "tissue"),
    ("dog_tissue", "dogs"),
    ("food_tissue", "dog_tissue"),
    ("food_tissue", "ingredients"),
    ("food_meat", "meat"),
    ("food_meat", "ingredients"),
    ("dog_food", "dogs"),
    ("dog_food", "food"),
    ("ingredients", "dog_food"),
    ("group", "food_tissue"),
    ("group", "food_meat"),
    ("food_mixing", "mixing"),
    ("food_mixing", "ingredients"),
    ("complete_mixing", "group"),
    ("complete_mixing", "food_mixing"),
)


class FoodSubjectPromptExampleTests(unittest.TestCase):
    def food_example(self, path=FOOD_PROMPT_PATH):
        source = path.read_text()
        block = re.findall(r"<example>\n(.*?)\n</example>", source, re.S)[0]
        output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
        return experiment_inputs.validate(
            {"adapter": "subjects"}, {}, output, None
        )["parsed"]["subjects"]

    def assert_food_parents(self, path=FOOD_PROMPT_PATH):
        entries = self.food_example(path)
        subjects = {e["subject"] for e in entries}
        self.assertIn("Food", subjects, "C1 does not demonstrate the reproduced food parent")
        self.assertGreaterEqual(sum(e["subject"] == "Dog food" for e in entries), 2)

    def test_c1_exposes_food_and_dog_food_parent_copies(self):
        self.assert_food_parents()

    def test_saved_repair_example_does_not_expose_food_parents(self):
        with self.assertRaisesRegex(AssertionError, "C1 does not demonstrate"):
            self.assert_food_parents(MATERIAL_PROMPT_PATH)

    def ancestors(self):
        ancestors = {node: set() for node in FOOD_SUBJECTS}
        for child, parent in FOOD_RELATIONSHIPS:
            ancestors[child].add(parent)
        while True:
            expanded = {
                child: parents.union(*(ancestors[parent] for parent in parents))
                for child, parents in ancestors.items()
            }
            if expanded == ancestors:
                return ancestors
            ancestors = expanded

    def test_source_subjects_fill_every_compatible_numbered_parent(self):
        entries = self.food_example()
        ancestors = self.ancestors()
        for child in (
            "food_salt", "dog_tissue", "food_tissue", "food_meat",
            "group", "complete_mixing", "seasoning", "ingredients",
        ):
            for parent in ancestors[child]:
                parents = [e for e in entries if e["subject"] == FOOD_SUBJECTS[parent]]
                self.assertTrue(parents, parent)
                for occurrence in parents:
                    with self.subTest(child=child, parent=occurrence["number"]):
                        self.assertTrue(any(
                            e["subject"] == FOOD_SUBJECTS[child]
                            and e["number"].startswith(occurrence["number"] + ".")
                            for e in entries
                        ), "source subject missing from this parent occurrence")

    def test_every_edge_has_a_reviewed_heading_only_basis(self):
        entries = self.food_example()
        ids = {subject: node for node, subject in FOOD_SUBJECTS.items()}
        self.assertEqual({e["subject"] for e in entries}, set(ids))
        ancestors = self.ancestors()
        by_number = {e["number"]: e for e in entries}
        for entry in entries:
            if "." in entry["number"]:
                parent = by_number[entry["number"].rsplit(".", 1)[0]]
                with self.subTest(number=entry["number"]):
                    self.assertIn(ids[parent["subject"]], ancestors[ids[entry["subject"]]])

    def test_generic_materials_and_recipient_only_tissue_stay_outside_food(self):
        entries = self.food_example()
        for parent in entries:
            descendants = {
                e["subject"] for e in entries
                if e["number"].startswith(parent["number"] + ".")
            }
            if parent["subject"] in ("Food", "Dog food", "Dog-food ingredients", "Food seasoning"):
                for node in ("salt", "tissue", "dog_tissue", "meat", "mixing"):
                    with self.subTest(parent=parent["number"], child=node):
                        self.assertNotIn(FOOD_SUBJECTS[node], descendants)
            if parent["subject"] == FOOD_SUBJECTS["group"]:
                for node in ("food_tissue", "food_meat", "food_mixing"):
                    self.assertNotIn(FOOD_SUBJECTS[node], descendants)

    def test_individual_materials_and_dogs_remain_alongside_the_action(self):
        subjects = {e["subject"] for e in self.food_example()}
        for node in ("salt", "tissue", "meat", "dogs"):
            self.assertIn(FOOD_SUBJECTS[node], subjects, "event replaced its participant")

    def test_revision_preserves_instructions_other_examples_and_post_template(self):
        before = MATERIAL_PROMPT_PATH.read_text()
        after = FOOD_PROMPT_PATH.read_text()
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        self.assertEqual(before.rsplit("</example>", 1)[1], after.rsplit("</example>", 1)[1])
        template = Path(__file__).parent / "experiment_specs/asv6.75-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        for block in blocks[1]:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output, None
            )["parsed"]["subjects"]
            for entry in entries:
                self.assertEqual(list(entry), ["number", "context", "subject"])


SHARED_ACTION_PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.78/ASv6.78.md"
)
SHARED_ACTION_SUBJECTS = {
    **{node: subject for node, subject in FOOD_SUBJECTS.items()
       if node not in ("mixing", "food_mixing", "complete_mixing")},
    "cutting": "Cutting",
    "tissue_cutting": "Cutting one piece of connective tissue as a food ingredient for the dog",
    "meat_cutting": "Cutting two meat scraps as food ingredients for the dog",
    "complete_cutting": "Cutting one piece of connective tissue and two meat scraps as food ingredients for the dog",
}
# Independently reviewed heading meanings; the source output is authored as
# explicit numbered rows, not rendered from this relationship graph.
SHARED_ACTION_RELATIONSHIPS = tuple(
    (child, parent) for child, parent in FOOD_RELATIONSHIPS
    if "mixing" not in child and "mixing" not in parent
) + (
    ("tissue_cutting", "food_tissue"),
    ("tissue_cutting", "cutting"),
    ("meat_cutting", "food_meat"),
    ("meat_cutting", "cutting"),
    ("complete_cutting", "group"),
    ("complete_cutting", "tissue_cutting"),
    ("complete_cutting", "meat_cutting"),
)


class SharedActionSubjectPromptExampleTests(unittest.TestCase):
    subjects = SHARED_ACTION_SUBJECTS
    relationships = SHARED_ACTION_RELATIONSHIPS

    def entries(self, path=SHARED_ACTION_PROMPT_PATH):
        block = re.findall(r"<example>\n(.*?)\n</example>", path.read_text(), re.S)[0]
        output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
        return experiment_inputs.validate(
            {"adapter": "subjects"}, {}, output, None
        )["parsed"]["subjects"]

    def ancestors(self):
        ancestors = {node: set() for node in self.subjects}
        for child, parent in self.relationships:
            ancestors[child].add(parent)
        while True:
            expanded = {
                child: parents.union(*(ancestors[parent] for parent in parents))
                for child, parents in ancestors.items()
            }
            if expanded == ancestors:
                return ancestors
            ancestors = expanded

    def test_partial_actions_and_complete_shared_action_are_demonstrated(self):
        subjects = {e["subject"] for e in self.entries()}
        for node in ("tissue_cutting", "meat_cutting", "complete_cutting"):
            self.assertIn(self.subjects[node], subjects,
                          "C1 does not demonstrate partial and complete shared actions")
        self.assertEqual(subjects, set(self.subjects.values()))

    def test_each_source_subject_fills_every_compatible_parent_copy(self):
        entries = self.entries()
        ancestors = self.ancestors()
        for child in (
            "food_salt", "dog_tissue", "food_tissue", "food_meat", "group",
            "tissue_cutting", "meat_cutting", "complete_cutting",
            "seasoning", "ingredients", "dog_food",
        ):
            for parent in ancestors[child]:
                copies = [e for e in entries if e["subject"] == self.subjects[parent]]
                self.assertTrue(copies, parent)
                for copy in copies:
                    with self.subTest(child=child, parent=copy["number"]):
                        self.assertTrue(any(
                            e["subject"] == self.subjects[child]
                            and e["number"].startswith(copy["number"] + ".")
                            for e in entries
                        ), "source subject missing from this compatible parent occurrence")

    def test_every_rendered_edge_preserves_the_parent_heading_meaning(self):
        entries = self.entries()
        ids = {subject: node for node, subject in self.subjects.items()}
        ancestors = self.ancestors()
        by_number = {e["number"]: e for e in entries}
        for entry in entries:
            self.assertEqual(list(entry), ["number", "context", "subject"])
            if "." in entry["number"]:
                parent = by_number[entry["number"].rsplit(".", 1)[0]]
                with self.subTest(number=entry["number"]):
                    self.assertIn(ids[parent["subject"]], ancestors[ids[entry["subject"]]])

    def test_food_role_and_combination_restrictions_are_not_borrowed(self):
        entries = self.entries()
        invalid = {
            "food": ("salt", "tissue", "dog_tissue", "meat", "cutting"),
            "dog_food": ("tissue", "dog_tissue", "meat", "cutting"),
            "group": ("food_tissue", "food_meat", "tissue_cutting", "meat_cutting"),
            "complete_cutting": ("group", "tissue_cutting", "meat_cutting"),
            "tissue_cutting": ("group", "meat_cutting"),
            "meat_cutting": ("group", "tissue_cutting"),
        }
        for parent in entries:
            descendants = {
                e["subject"] for e in entries
                if e["number"].startswith(parent["number"] + ".")
            }
            for node, children in invalid.items():
                if parent["subject"] == self.subjects[node]:
                    for child in children:
                        with self.subTest(parent=parent["number"], child=child):
                            self.assertNotIn(self.subjects[child], descendants)

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = FOOD_PROMPT_PATH.parent.parent / "asv6.76/ASv6.76.md"
        sources = (before.read_text(), SHARED_ACTION_PROMPT_PATH.read_text())
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in sources]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(sources[0].split("<example>", 1)[0], sources[1].split("<example>", 1)[0])
        self.assertEqual(sources[0].rsplit("</example>", 1)[1], sources[1].rsplit("</example>", 1)[1])
        template = Path(__file__).parent / "experiment_specs/asv6.78-hr01-post-template.txt"
        self.assertEqual(template.read_text(), sources[1] + "\n<post>\n{POST}\n</post>")
        # The shared-predicate example supplements R17's rhetoric case; all
        # established primary assignments stay exactly once.
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class LaterReferentSubjectPromptExampleTests(unittest.TestCase):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.85/ASv6.85.md"

    def test_comparison_uses_qualifications_established_later_in_the_post(self):
        blocks = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)
        post = re.search(r"<post>\n(.*?)\n</post>", blocks[5], re.S).group(1)
        self.assertLess(post.index("not longer"), post.index("2 m long"),
                        "C6 does not demonstrate later-established referent qualifications")
        output = re.search(r"<output>\n(.*?)\n</output>", blocks[5], re.S).group(1)
        entries = experiment_inputs.validate(
            {"adapter": "subjects"}, {}, output, None
        )["parsed"]["subjects"]
        comparisons = [e for e in entries if "not longer" in e["subject"]]
        self.assertTrue(comparisons)
        for entry in comparisons:
            self.assertEqual(entry["subject"], "2 m cable A not longer than 3 m cable B")

    def test_only_the_source_order_changes_and_reviewed_output_is_preserved(self):
        before = (self.path.parent.parent / "asv6.81/ASv6.81.md").read_text()
        self.assertEqual(self.path.read_text(), before.replace(
            "2 cables: cable A is 2 m long and cable B is 3 m long. A is not longer than B.",
            "2 cables: cable A is not longer than cable B. Cable A is 2 m long and cable B is 3 m long.",
        ))


class CompleteSharedActionSubjectPromptExampleTests(SharedActionSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.86/ASv6.86.md"

    def entries(self, path=None):
        return super().entries(path or self.path)

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = FOOD_PROMPT_PATH.parent.parent / "asv6.81/ASv6.81.md"
        sources = (before.read_text(), self.path.read_text())
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S) for s in sources]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(sources[0].split("<example>", 1)[0], sources[1].split("<example>", 1)[0])
        self.assertEqual(sources[0].rsplit("</example>", 1)[1], sources[1].rsplit("</example>", 1)[1])
        audited = re.findall(r"<example>\n.*?\n</example>", SHARED_ACTION_PROMPT_PATH.read_text(), re.S)
        self.assertEqual(blocks[1][0], audited[0])
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class SpecificSourceEnumerationExampleTests(FoodSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.87/ASv6.87.md"

    def food_example(self, path=None):
        return super().food_example(path or self.path)

    def assert_food_parents(self, path=None):
        return super().assert_food_parents(path or self.path)

    def test_complete_source_subjects_are_demonstrated_before_generalization(self):
        block = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)[0]
        explanation = re.search(r"<explanation>\n(.*?)\n</explanation>", block, re.S).group(1)
        for node in ("food_salt", "dog_tissue", "food_tissue", "food_meat", "group", "complete_mixing"):
            with self.subTest(subject=node):
                self.assertIn(FOOD_SUBJECTS[node], explanation,
                              "C1 does not explicitly demonstrate the complete source enumeration")
                self.assertLess(explanation.index(FOOD_SUBJECTS[node]),
                                explanation.index("Then derive"))

    def test_revision_preserves_instructions_other_examples_and_post_template(self):
        before = (self.path.parent.parent / "asv6.81/ASv6.81.md").read_text()
        after = self.path.read_text()
        omit_first_explanation = lambda s: re.sub(
            r"<explanation>\n.*?\n</explanation>", "<explanation/>", s, count=1, flags=re.S
        )
        self.assertEqual(omit_first_explanation(before), omit_first_explanation(after))
        blocks = re.findall(r"<example>\n(.*?)\n</example>", after, re.S)
        self.assertEqual(len(blocks), 7)
        for block in blocks:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


ORIGIN_SUBJECTS = {
    **{node: subject.replace(" as ", " from specimen A as ", 1)
       if node in ("food_tissue", "food_meat", "group", "tissue_cutting",
                   "meat_cutting", "complete_cutting") else subject
       for node, subject in SHARED_ACTION_SUBJECTS.items()},
    "specimens": "Specimens", "specimen_a": "Specimen A",
}
ORIGIN_RELATIONSHIPS = SHARED_ACTION_RELATIONSHIPS + (
    ("specimen_a", "specimens"),
    ("food_tissue", "specimen_a"), ("food_meat", "specimen_a"),
)


class OriginQualifiedSubjectPromptExampleTests(SharedActionSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.88/ASv6.88.md"
    subjects = ORIGIN_SUBJECTS
    relationships = ORIGIN_RELATIONSHIPS

    def entries(self, path=None):
        return super().entries(path or self.path)

    def test_complete_ingredients_and_actions_retain_named_physical_source(self):
        subjects = {entry["subject"] for entry in self.entries()}
        for node in ("food_tissue", "food_meat", "group", "tissue_cutting",
                     "meat_cutting", "complete_cutting"):
            with self.subTest(subject=node):
                self.assertIn(ORIGIN_SUBJECTS[node], subjects,
                              "C1 does not demonstrate enclosing physical origin with local food role")
        for parent in self.entries():
            if parent["subject"] == "Specimen A":
                for node in ("food_tissue", "food_meat", "group", "tissue_cutting",
                             "meat_cutting", "complete_cutting"):
                    self.assertTrue(any(
                        e["subject"] == ORIGIN_SUBJECTS[node]
                        and e["number"].startswith(parent["number"] + ".")
                        for e in self.entries()
                    ))

    def test_recipient_only_tissue_does_not_gain_food_or_source_role(self):
        entries = self.entries()
        for parent in entries:
            if parent["subject"] in ("Food", "Dog food", "Specimens", "Specimen A"):
                self.assertFalse(any(
                    e["subject"] == ORIGIN_SUBJECTS["dog_tissue"]
                    and e["number"].startswith(parent["number"] + ".")
                    for e in entries
                ))

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = (self.path.parent.parent / "asv6.86/ASv6.86.md").read_text()
        after = self.path.read_text()
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S)
                  for s in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        self.assertEqual(before.rsplit("</example>", 1)[1], after.rsplit("</example>", 1)[1])
        template = Path(__file__).parent / "experiment_specs/asv6.88-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class CompleteSourceCollectionExampleTests(SpecificSourceEnumerationExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.89/ASv6.89.md"

    def test_explanation_demonstrates_one_complete_source_collection(self):
        entries = self.food_example()
        block = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)[0]
        explanation = re.search(r"<explanation>\n(.*?)\n</explanation>", block, re.S).group(1)
        rows = [tuple(cell.strip() for cell in line.strip("|").split("|"))
                for line in explanation.splitlines() if line.startswith("|")]
        group_rows = [row for row in rows if row[0] == FOOD_SUBJECTS["group"]]
        self.assertEqual(len(group_rows), 1,
                         "C1 does not explicitly demonstrate the complete group collection")
        source_nodes = ("food_salt", "dog_tissue", "food_tissue", "food_meat",
                        "group", "complete_mixing")
        ancestors = self.ancestors()
        expected = {FOOD_SUBJECTS[node] for node in source_nodes
                    if "group" in ancestors[node]}
        self.assertEqual(set(group_rows[0][1:]), expected)
        groups = [entry for entry in entries if entry["subject"] == FOOD_SUBJECTS["group"]]
        self.assertTrue(groups)
        for parent in groups:
            descendants = {entry["subject"] for entry in entries
                           if entry["number"].startswith(parent["number"] + ".")}
            self.assertEqual(descendants, expected)

    def test_previous_explanation_lacks_complete_collection_demonstration(self):
        before = self.path.parent.parent / "asv6.87/ASv6.87.md"
        with patch.object(self, "path", before):
            with self.assertRaisesRegex(AssertionError, "complete group collection"):
                self.test_explanation_demonstrates_one_complete_source_collection()

    def test_revision_preserves_instructions_other_examples_and_post_template(self):
        super().test_revision_preserves_instructions_other_examples_and_post_template()
        before = (self.path.parent.parent / "asv6.87/ASv6.87.md").read_text()
        after = self.path.read_text()
        omit_first_explanation = lambda s: re.sub(
            r"<explanation>\n.*?\n</explanation>", "<explanation/>", s, count=1, flags=re.S
        )
        self.assertEqual(omit_first_explanation(before), omit_first_explanation(after))
        template = Path(__file__).parent / "experiment_specs/asv6.89-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")


class CombinedReferenceAndSharedActionPromptTests(SharedActionSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.92/ASv6.92.md"

    def entries(self, path=None):
        return super().entries(path or self.path)

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = (self.path.parent.parent / "asv6.90/ASv6.90.md").read_text()
        shared = (self.path.parent.parent / "asv6.86/ASv6.86.md").read_text()
        first = lambda s: re.findall(r"<example>\n.*?\n</example>", s, re.S)[0]
        self.assertEqual(self.path.read_text(), before.replace(first(before), first(shared), 1))
        template = Path(__file__).parent / "experiment_specs/asv6.92-hr01-post-template.txt"
        self.assertEqual(template.read_text(), self.path.read_text() + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class BroadAndExactSourceCollectionExampleTests(SharedActionSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.91/ASv6.91.md"

    def entries(self, path=None):
        return super().entries(path or self.path)

    def test_complete_broad_and_exact_descendant_collections_are_demonstrated(self):
        entries = self.entries()
        block = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)[0]
        explanation = re.search(r"<explanation>\n(.*?)\n</explanation>", block, re.S).group(1)
        rows = [tuple(cell.strip() for cell in line.strip("|").split("|"))
                for line in explanation.splitlines() if line.startswith("|")]
        source_nodes = ("food_tissue", "food_meat", "group", "tissue_cutting",
                        "meat_cutting", "complete_cutting")
        source_subjects = {self.subjects[node] for node in source_nodes}
        ancestors = self.ancestors()
        for parent_node in ("ingredients", "group"):
            matching = [row for row in rows if row[0] == self.subjects[parent_node]]
            self.assertEqual(len(matching), 1,
                             "C1 lacks a complete broad/exact collection demonstration")
            self.assertEqual(len(matching[0]), 2)
            expected = {self.subjects[node] for node in source_nodes
                        if parent_node in ancestors[node]}
            self.assertEqual(set(matching[0][1].split("; ")), expected)
            for parent in entries:
                if parent["subject"] != self.subjects[parent_node]:
                    continue
                descendants = {entry["subject"] for entry in entries
                               if entry["number"].startswith(parent["number"] + ".")}
                self.assertEqual(descendants & source_subjects, expected)

    def test_previous_example_lacks_the_broad_collection_demonstration(self):
        before = self.path.parent.parent / "asv6.86/ASv6.86.md"
        with patch.object(self, "path", before):
            with self.assertRaisesRegex(AssertionError, "broad/exact collection"):
                self.test_complete_broad_and_exact_descendant_collections_are_demonstrated()

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = (self.path.parent.parent / "asv6.90/ASv6.90.md").read_text()
        shared = (self.path.parent.parent / "asv6.86/ASv6.86.md").read_text()
        after = self.path.read_text()
        blocks = [re.findall(r"<example>\n.*?\n</example>", s, re.S)
                  for s in (before, shared, after)]
        self.assertEqual(len(blocks[2]), 7)
        self.assertEqual(blocks[0][1:], blocks[2][1:])
        omit_explanation = lambda s: re.sub(
            r"<explanation>\n.*?\n</explanation>", "<explanation/>", s,
            count=1, flags=re.S,
        )
        self.assertEqual(omit_explanation(blocks[1][0]), omit_explanation(blocks[2][0]))
        self.assertEqual(before.split("<example>", 1)[0], after.split("<example>", 1)[0])
        self.assertEqual(before.rsplit("</example>", 1)[1], after.rsplit("</example>", 1)[1])
        for block in blocks[2]:
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        template = Path(__file__).parent / "experiment_specs/asv6.91-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class CompleteReferentResolutionPromptTests(unittest.TestCase):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.90/ASv6.90.md"

    def test_source_resolution_precedes_complete_subject_construction(self):
        source = self.path.read_text()
        for block in re.findall(r"<example>\n(.*?)\n</example>", source, re.S):
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        self.assertIn(
            "Build complete specific subjects and expressed combinations from those resolved referents",
            source, "Source resolution is not demonstrated as an input to subject construction",
        )
        self.assertIn("of its referent for that occurrence", source)
        self.assertIn("Derive less specific descriptions only as broader headings.", source)

    def test_only_source_resolution_operation_changes(self):
        before = (self.path.parent.parent / "asv6.81/ASv6.81.md").read_text()
        old = (
            "Use the complete post to resolve each reference and local description to its most specific "
            "supported referent, including meaning established by a title, enclosing heading, list or "
            "shared predicate. A local role or purpose does not replace a supported enclosing "
            "relationship: retain both in the complete specific subject and expressed combination."
        )
        new = (
            "Resolve each reference or local description to the complete supported description of its "
            "referent for that occurrence, using the whole post, including titles, enclosing headings, "
            "lists and shared predicates. Build complete specific subjects and expressed combinations "
            "from those resolved referents, retaining both enclosing relationships and local roles or "
            "purposes. Derive less specific descriptions only as broader headings."
        )
        self.assertEqual(self.path.read_text(), before.replace(old, new))
        template = Path(__file__).parent / "experiment_specs/asv6.90-hr01-post-template.txt"
        self.assertEqual(template.read_text(), self.path.read_text() + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))


class FiniteSourceCollectionPromptTests(SharedActionSubjectPromptExampleTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.93/ASv6.93.md"

    def entries(self, path=None):
        return super().entries(path or self.path)

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = (self.path.parent.parent / "asv6.92/ASv6.92.md").read_text()
        after = self.path.read_text()
        blocks = [re.findall(r"<example>\n(.*?)\n</example>", s, re.S)
                  for s in (before, after)]
        self.assertEqual(len(blocks[1]), 7)
        self.assertEqual(blocks[0][1:], blocks[1][1:])
        for previous, current in zip(*blocks):
            for tag in ("post", "output"):
                pattern = rf"<{tag}>\n(.*?)\n</{tag}>"
                self.assertEqual(re.search(pattern, previous, re.S).group(1),
                                 re.search(pattern, current, re.S).group(1))
            output = re.search(r"<output>\n(.*?)\n</output>", current, re.S).group(1)
            experiment_inputs.validate({"adapter": "subjects"}, {}, output, None)
        template = (Path(__file__).parent / "experiment_specs" /
                    f"{self.path.parent.name}-hr01-post-template.txt")
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))

    def assert_distinct_descendants(self, entries):
        for entry in entries:
            self.assertFalse(any(
                child["subject"] == entry["subject"]
                and child["number"].startswith(entry["number"] + ".")
                for child in entries
            ), f"same source subject repeated beneath its own heading {entry['number']}")

    def test_a_source_subject_is_represented_at_its_own_entry(self):
        self.assert_distinct_descendants(self.entries())

    def test_identical_self_descendant_is_rejected(self):
        subject = self.subjects["complete_cutting"]
        parsed = experiment_inputs.validate({"adapter": "subjects"}, {}, json.dumps({
            "subjects": [
                {"number": "1", "context": "Cutting both counted ingredients.", "subject": subject},
                {"number": "1.1", "context": "Cutting both counted ingredients.", "subject": subject},
            ]
        }), None)["parsed"]["subjects"]
        with self.assertRaisesRegex(AssertionError, "same source subject"):
            self.assert_distinct_descendants(parsed)


class SourceFirstCollectionPromptTests(FiniteSourceCollectionPromptTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.94/ASv6.94.md"


class GroupedSourceCopiesPromptTests(FiniteSourceCollectionPromptTests):
    path = Path(__file__).parent / "subject-prompt-goal-v1/asv6.95/ASv6.95.md"

    def test_instruction_coverage_other_examples_and_template_are_preserved(self):
        before = (self.path.parent.parent / "asv6.94/ASv6.94.md").read_text()
        after = self.path.read_text()
        output_pattern = r"<output>\n(.*?)\n</output>"
        self.assertEqual(re.sub(output_pattern, "<output></output>", before, flags=re.S),
                         re.sub(output_pattern, "<output></output>", after, flags=re.S))
        previous = re.findall(output_pattern, before, re.S)
        current = re.findall(output_pattern, after, re.S)
        self.assertEqual(len(current), 7)
        for old, new in zip(previous, current):
            old_entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, old, None
            )["parsed"]["subjects"]
            new_entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, new, None
            )["parsed"]["subjects"]
            self.assertEqual(Counter(tuple(entry.items()) for entry in old_entries),
                             Counter(tuple(entry.items()) for entry in new_entries))
        template = Path(__file__).parent / "experiment_specs/asv6.95-hr01-post-template.txt"
        self.assertEqual(template.read_text(), after + "\n<post>\n{POST}\n</post>")
        self.assertEqual(Counter(rule for case in FOCUSED_CASES for rule in case["primary_rules"]),
                         Counter({f"R{i:02d}": 1 for i in range(1, 35)}))

    def test_all_copies_of_a_subject_are_emitted_together(self):
        blocks = re.findall(r"<example>\n(.*?)\n</example>", self.path.read_text(), re.S)
        for case, block in enumerate(blocks, 1):
            output = re.search(r"<output>\n(.*?)\n</output>", block, re.S).group(1)
            entries = experiment_inputs.validate(
                {"adapter": "subjects"}, {}, output, None
            )["parsed"]["subjects"]
            closed = set()
            previous = None
            for entry in entries:
                subject = entry["subject"]
                if subject != previous:
                    self.assertNotIn(subject, closed,
                                     f"C{case} separates copies of {subject!r}")
                    if previous is not None:
                        closed.add(previous)
                    previous = subject


if __name__ == "__main__":
    unittest.main()
