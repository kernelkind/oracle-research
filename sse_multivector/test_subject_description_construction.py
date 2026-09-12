import copy
import json
from pathlib import Path
import unittest

from subject_description_construction import compare_representations


def record(row, note, fragments, subjects):
    return dict(row=row, aliases=[dict(note_short_id=note, short_id=f'V{row}-{i}',
                                     fragments=fragments, subject=subject,
                                     text=' '.join(fragments))
                                  for i, subject in enumerate(subjects)])


class SubjectDescriptionConstructionTests(unittest.TestCase):
    def test_alias_descriptions_remain_separate_and_source_unchanged(self):
        evidence = [record(0, 'a', ['GM'], ['A morning greeting.', 'Wishing a good morning.']),
                    record(1, 'b', ['Good morning'], ['A morning greeting.']),
                    record(2, 'c', ['Morning coffee'], ['Coffee in the morning.'])]
        before = copy.deepcopy(evidence)
        result = compare_representations(evidence)
        self.assertEqual(evidence, before)
        self.assertEqual(len(result['inputs']), 4)
        self.assertEqual([r['canonical_row'] for r in result['inputs']], [0, 0, 1, 2])
        by_features = {tuple(d['features']): d for d in result['subjects']['descriptions']}
        self.assertEqual(by_features[('a', 'greeting', 'morning')]['notes'], ['a', 'b'])
        self.assertNotIn(('a', 'good', 'greeting', 'morning', 'wishing'), by_features)
        self.assertTrue(result['control_reproduced'])

    def test_alternatives_from_one_note_cannot_create_recurrence(self):
        evidence = [record(0, 'a', ['GM'], ['Morning greeting.', 'A morning greeting.'])]
        result = compare_representations(evidence)
        self.assertEqual(result['subjects']['descriptions'], [])

    def test_saved_cap02_memberships_reproduce(self):
        root = Path(__file__).resolve().parent
        evidence = json.loads((root / 'geometric-hierarchy-v1/GDC09/evidence.json').read_bytes())
        frozen = json.loads((root / 'navigation-research-v1/CAP02-result.json').read_bytes())
        result = compare_representations(evidence)
        self.assertTrue(result['control_reproduced'])
        self.assertEqual(result['control_canonical_descriptions'], frozen['descriptions'])
        self.assertEqual(result['mask']['relations'], frozen['relations'])


if __name__ == '__main__':
    unittest.main()
