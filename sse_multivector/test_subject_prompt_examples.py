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
        for version in range(59, 70):
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
        for version in range(61, 70):
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
            cases = (repair_case, app_case) + FOCUSED_CASES[2:]
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


if __name__ == "__main__":
    unittest.main()
