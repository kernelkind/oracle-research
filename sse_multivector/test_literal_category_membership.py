from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from literal_category_membership import literal_memberships


class LiteralMembershipTests(unittest.TestCase):
    def fixture(self):
        phrases = [('a', ['coffee']), ('b', ['Coffee']),
                   ('c', ['coffee', 'with milk']), ('d', ['coffeehouse']),
                   ('a', ['tea']), ('e', ['wine with food']), ('f', ['dry white wine'])]
        evidence = [dict(row=i, aliases=[dict(note_short_id=n, fragments=f)])
                    for i, (n, f) in enumerate(phrases)]
        hierarchy = dict(nodes=[dict(id=1, members=list(range(7))),
                                dict(id=2, members=[0, 1]), dict(id=3, members=[5, 6])])
        categories = dict(root_node_id='1', nodes=[
            dict(node_id='1', children=['2', '3'], note_ids=['c', 'd']),
            dict(node_id='2', children=[], note_ids=['a', 'b']),
            dict(node_id='3', children=[], note_ids=['e', 'f']),
        ])
        return categories, hierarchy, evidence

    def test_complete_word_match_adds_context_but_not_prefix_or_other_mask(self):
        data = self.fixture()
        before = deepcopy(data)
        families = literal_memberships(*data)
        self.assertEqual(len(families), 1)
        f = families[0]
        self.assertEqual(f['words'], ['coffee'])
        self.assertEqual(f['seed_rows'], [0, 1])
        self.assertEqual(f['matched_rows'], [0, 1, 2])
        self.assertEqual(f['added_rows'], [2])
        self.assertEqual(f['added_notes'], ['c'])
        self.assertEqual(data, before)

    def test_intersection_does_not_silently_broaden_qualified_subject(self):
        families = literal_memberships(*self.fixture())
        self.assertFalse(any(f['words'] == ['wine'] for f in families))

    def test_two_vectors_from_one_note_do_not_establish_recurrence(self):
        categories, hierarchy, evidence = self.fixture()
        evidence[1]['aliases'][0]['note_short_id'] = 'a'
        categories['nodes'][1]['note_ids'] = ['a']
        self.assertEqual(literal_memberships(categories, hierarchy, evidence), [])

    def test_inconsistent_native_note_membership_is_rejected(self):
        categories, hierarchy, evidence = self.fixture()
        categories['nodes'][1]['note_ids'] = ['wrong']
        with self.assertRaises(ValueError):
            literal_memberships(categories, hierarchy, evidence)

    def test_same_words_across_disjoint_seed_groups_form_one_family(self):
        categories, hierarchy, evidence = self.fixture()
        categories['nodes'][0]['children'].append('4')
        categories['nodes'][0]['note_ids'] = ['c']
        categories['nodes'].append(dict(node_id='4', children=[], note_ids=['d', 'g']))
        evidence[3]['aliases'][0]['fragments'] = ['coffee']
        evidence.append(dict(row=7, aliases=[dict(note_short_id='g', fragments=['#coffee'])]))
        hierarchy['nodes'][0]['members'].append(7)
        hierarchy['nodes'].append(dict(id=4, members=[3, 7]))
        families = literal_memberships(categories, hierarchy, evidence)
        self.assertEqual(len(families), 1)
        self.assertEqual(families[0]['seed_categories'], ['2', '4'])
        self.assertEqual(families[0]['seed_notes'], ['a', 'b', 'd', 'g'])
        self.assertEqual(families[0]['matched_notes'], ['a', 'b', 'c', 'd', 'g'])

    def test_every_word_required_even_across_multiple_fragments(self):
        categories, hierarchy, evidence = self.fixture()
        evidence[0]['aliases'][0]['fragments'] = ['iced coffee']
        evidence[1]['aliases'][0]['fragments'] = ['ICED', 'coffee']
        evidence[2]['aliases'][0]['fragments'] = ['iced coffee', 'with milk']
        evidence[3]['aliases'][0]['fragments'] = ['coffee']
        f = literal_memberships(categories, hierarchy, evidence)[0]
        self.assertEqual(f['words'], ['coffee', 'iced'])
        self.assertEqual(f['matched_rows'], [0, 1, 2])

    def test_aliases_cannot_mix_notes(self):
        categories, hierarchy, evidence = self.fixture()
        evidence[0]['aliases'].append(dict(note_short_id='other', fragments=['coffee']))
        with self.assertRaises(ValueError):
            literal_memberships(categories, hierarchy, evidence)

    def test_real_cli_preserves_inputs_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, value in zip(('categories', 'hierarchy', 'evidence'), self.fixture()):
                paths[name] = root / (name + '.json')
                paths[name].write_text(json.dumps(value))
            before = {k: p.read_bytes() for k, p in paths.items()}
            output = root / 'result'
            command = [sys.executable, str(Path(__file__).with_name('literal_category_membership.py')),
                       str(paths['categories']), '--hierarchy', str(paths['hierarchy']),
                       '--evidence', str(paths['evidence']), '--output', str(output),
                       '--run-id', 'test']
            subprocess.run(command, check=True, capture_output=True, text=True)
            expected = literal_memberships(*self.fixture())
            self.assertEqual(json.loads((output / 'results.json').read_text()), expected)
            self.assertEqual({k: p.read_bytes() for k, p in paths.items()}, before)
            saved = {p.relative_to(output): p.read_bytes() for p in output.rglob('*') if p.is_file()}
            rerun = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertIn('output exists', rerun.stderr)
            self.assertEqual({p.relative_to(output): p.read_bytes()
                              for p in output.rglob('*') if p.is_file()}, saved)


if __name__ == '__main__':
    unittest.main()
