"""Offline checks for the SP examples' declared hierarchy relationships."""

import re
import unittest
from pathlib import Path

from sse_multivector import experiment_inputs


PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.53/ASv6.53.md"
)
FOCUSED_PROMPT_PATH = (
    Path(__file__).parent / "subject-prompt-goal-v1/asv6.54/ASv6.54.md"
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



# R/I IDs refer to the rule-to-case map in subject-prompt-goal-v1/asv6.50/README.md.
# Subjects and relationships are reviewed expectations, not model-generated truth.
FOCUSED_CASES = (
    {
        "id": "C1",
        "purpose": "Whole-post references, implied subjects and repeated hierarchy branches.",
        "post": "I watched a lunar eclipse through binoculars. Tried sketching the Moon, but clouds kept hiding it.",
        "subjects": LUNAR_SUBJECTS,
        "relationships": LUNAR_RELATIONSHIPS,
        "rules": (
            "R01", "R02", "R03", "R04", "R16", "R17", "R18",
            "R19", "R20", "R21", "R22", "R23", "R24", "R25",
            "R26", "R27", "R28", "R29", "R30", "R31", "R32",
            "R34", "I04",
        ),
        "invalid": (
            ("3", "1"),
            ("2.1", "1.1"),
            ("5", "4.1"),
        ),
    },
    {
        "id": "C2",
        "purpose": "Named referent resolution, replacement-part roles and retained locomotive type.",
        "post": "Replacement boiler for Bracken. Bracken is a steam locomotive.",
        "subjects": {
            "boilers": "Boilers",
            "steam_boilers": "Steam locomotive boilers",
            "replacement_boilers": "Replacement boilers",
            "bracken_boiler": "Replacement boiler for Bracken the steam locomotive",
            "locomotives": "Locomotives",
            "steam_locomotives": "Steam locomotives",
            "bracken": "Bracken the steam locomotive",
            "replacement_parts": "Replacement parts",
        },
        "relationships": (
            ("steam_boilers", "boilers"),
            ("steam_boilers", "steam_locomotives"),
            ("replacement_boilers", "boilers"),
            ("replacement_boilers", "replacement_parts"),
            ("bracken_boiler", "steam_boilers"),
            ("bracken_boiler", "replacement_boilers"),
            ("bracken_boiler", "bracken"),
            ("steam_locomotives", "locomotives"),
            ("bracken", "steam_locomotives"),
        ),
        "rules": (
            "R02", "R03", "R04", "R05", "R16", "R18", "R19",
            "R20", "R21", "R22", "R27", "R28", "R29", "R30",
            "R31", "R32", "R34", "I01", "I02", "I05",
        ),
        "invalid": (
            ("boilers", "replacement_parts"),
            ("replacement_boilers", "steam_boilers"),
            ("bracken", "replacement_parts"),
        ),
    },
    {
        "id": "C3",
        "purpose": "Individual advice instructions and their stated combination.",
        "post": "Advice: book ahead and stay on marked routes.",
        "subjects": {
            "advice": "Advice",
            "booking": "Advance booking",
            "routes": "Marked routes",
            "staying": "Staying on marked routes",
            "booking_advice": "Advice to book in advance",
            "route_advice": "Advice to stay on marked routes",
            "combined_advice": "Advice to book in advance and stay on marked routes",
        },
        "relationships": (
            ("staying", "routes"),
            ("booking_advice", "advice"),
            ("booking_advice", "booking"),
            ("route_advice", "advice"),
            ("route_advice", "staying"),
            ("combined_advice", "booking_advice"),
            ("combined_advice", "route_advice"),
        ),
        "rules": (
            "R04", "R16", "R17", "R18", "R19", "R20", "R21",
            "R22", "R27", "R28", "R29", "R30", "R31", "R32",
            "R34", "I03",
        ),
        "invalid": (
            ("booking", "advice"),
            ("routes", "advice"),
            ("booking_advice", "combined_advice"),
            ("route_advice", "combined_advice"),
        ),
    },
    {
        "id": "C4",
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
        "rules": (
            "R01", "R02", "R03", "R04", "R05", "R06", "R10",
            "R12", "R16", "R17", "R18", "R19", "R20", "R21",
            "R22", "R27", "R28", "R29", "R30", "R31", "R32",
            "R34",
        ),
        "invalid": (
            ("amberloop", "apps"),
            ("amberloop", "help"),
            ("amberloop", "appreciation"),
        ),
    },
    {
        "id": "C5",
        "purpose": "URL and opaque identifier bodies without surrounding subject evidence.",
        "post": "https://birds.example/repair?count=12\n8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f8ca25e7f",
        "subjects": {
        },
        "relationships": (
        ),
        "rules": (
            "R07", "R12", "R24",
        ),
        "invalid": (
        ),
    },
    {
        "id": "C6",
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
        "rules": (
            "R04", "R07", "R08", "R10", "R11", "R12", "R16",
            "R18", "R20", "R21", "R22", "R27", "R28", "R29",
            "R30", "R31", "R34",
        ),
        "invalid": (
            ("profile_urls", "event_identifiers"),
            ("event_identifiers", "profile_urls"),
        ),
    },
    {
        "id": "C7",
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
        "rules": (
            "R01", "R03", "R04", "R09", "R10", "R11", "R12",
            "R16", "R18", "R19", "R20", "R21", "R22", "R27",
            "R28", "R29", "R30", "R31", "R32", "R34",
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
        "id": "C8",
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
        "rules": (
            "R01", "R02", "R04", "R05", "R13", "R14", "R15",
            "R16", "R17", "R18", "R19", "R20", "R21", "R22",
            "R27", "R28", "R29", "R30", "R31", "R32", "R33",
            "R34",
        ),
        "invalid": (
            ("pairs", "lengths"),
            ("a", "b"),
            ("b", "a"),
        ),
    },
    {
        "id": "C9",
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
        "rules": (
            "R03", "R04", "R13", "R14", "R15", "R16", "R17",
            "R18", "R19", "R20", "R21", "R22", "R27", "R28",
            "R29", "R30", "R31", "R32", "R34",
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

    def test_remaining_ambiguity_has_two_direct_interpretations(self):
        examples = self.examples()
        post = "I saw her duck. I bought a notebook."
        self.assertIn(post, set(examples), "missing remaining-ambiguity example")
        subjects = {entry["subject"] for entry in examples[post]}
        self.assertIn("Observation of a person's duck", subjects)
        self.assertIn("Observation of a person ducking", subjects)

    def test_each_instruction_is_traced_to_a_present_case(self):
        self.assertEqual(set(self.examples()), {c["post"] for c in FOCUSED_CASES})
        self.assertEqual(
            {rule for c in FOCUSED_CASES for rule in c["rules"]},
            {f"R{i:02d}" for i in range(1, 35)}
            | {f"I{i:02d}" for i in range(1, 6)},
        )
        self.assertEqual(len({c["id"] for c in FOCUSED_CASES}), len(FOCUSED_CASES))
        for case in FOCUSED_CASES:
            self.assertTrue(case["purpose"])

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
        bare = cases["C5"]["post"].splitlines()
        labelled = cases["C6"]["post"].splitlines()
        self.assertEqual(labelled, ["Profile URL: " + bare[0], "Event ID: " + bare[1]])
        examples = self.examples()
        self.assertEqual(examples[cases["C5"]["post"]], [])
        self.assertEqual(
            {e["subject"] for e in examples[cases["C6"]["post"]]},
            {"URLs", "Profile URLs", "Profiles", "Identifiers", "Event identifiers", "Events"},
        )

    def test_instructions_and_corrected_lunar_case_are_preserved(self):
        directory = FOCUSED_PROMPT_PATH.parent.parent
        approved = (directory / "asv6.51/ASv6.51.md").read_text()
        corrected = PROMPT_PATH.read_text()
        focused = FOCUSED_PROMPT_PATH.read_text()
        self.assertEqual(
            focused.split("<example>", 1)[0], approved.split("<example>", 1)[0]
        )
        self.assertEqual(
            re.findall(r"<example>\n.*?\n</example>", focused, re.S)[0],
            re.findall(r"<example>\n.*?\n</example>", corrected, re.S)[0],
        )


if __name__ == "__main__":
    unittest.main()
