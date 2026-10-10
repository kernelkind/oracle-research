"""Local nominations for overcrowded groups; relationships stay with traversal."""
import unittest
import hashlib
import json
from pathlib import Path
import struct
import tempfile

from sse_multivector import ancestor_cosine_probe
from sse_multivector.canonical_shaping_selection import (
    load_sibling_meanings, rank_candidates, rank_subgroups)


class ShapingSelectionTests(unittest.TestCase):
    def test_complete_link_considers_all_members_instead_of_seed_neighbors(self):
        import math
        siblings = [dict(id=f'C{i}', subject=f'S{i}') for i in range(4)]
        # S1 and S2 each resemble S0, but lie on opposite sides of it.
        vectors = {f'S{i}': [math.cos(math.radians(angle)), math.sin(math.radians(angle))]
                   for i, angle in enumerate((0, 20, -30, -65))}
        vectors['Candidate'] = [1, 0]
        rows = [dict(note_id='a', number='1', subject='Candidate')]
        nearest = rank_subgroups(rows, siblings, vectors)
        complete = rank_subgroups(rows, siblings, vectors, clustering='complete')
        self.assertIn(['C0', 'C1', 'C2'], [g['members'] for g in nearest])
        self.assertEqual([g['members'] for g in complete], [['C0', 'C1'], ['C2', 'C3']])

    def test_complete_link_is_nested_deterministic_and_respects_proper_group_limits(self):
        import math
        siblings = [dict(id=f'C{i}', subject=f'S{i}') for i in range(8)]
        vectors = {f'S{i}': [math.cos(i / 10), math.sin(i / 10)] for i in range(8)}
        vectors['Candidate'] = [1, 0]
        rows = [dict(note_id='a', number='1', subject='Candidate')]
        groups = rank_subgroups(rows, siblings, vectors, clustering='complete')
        self.assertTrue(groups)
        self.assertLessEqual(len(groups), len(siblings) - 2)
        self.assertTrue(all(2 <= len(g['members']) <= 6 for g in groups))
        sets = [set(g['members']) for g in groups]
        self.assertTrue(all(not a & b or a <= b or b <= a
                            for i, a in enumerate(sets) for b in sets[i + 1:]))
        self.assertEqual(groups, rank_subgroups(rows[::-1], siblings[::-1], vectors,
                                              clustering='complete'))
        self.assertEqual(groups, rank_subgroups(rows, siblings, vectors,
            clustering='complete', sibling_vectors={s['id']: vectors[s['subject']] for s in siblings}))

    def test_unknown_clustering_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'clustering'):
            rank_subgroups([], [], {}, clustering='unknown')

    def test_sibling_meanings_change_groups_and_candidates_without_changing_locals(self):
        siblings = [dict(id='C1', subject='A'), dict(id='C2', subject='B'),
                    dict(id='C3', subject='C')]
        rows = [dict(note_id='a', number='1', subject='AB'),
                dict(note_id='b', number='1', subject='AC')]
        vectors = {'A': [1, 0, 0], 'B': [1, .1, 0], 'C': [0, 1, 0],
                   'AB': [1, 0, 0], 'AC': [0, 0, 1]}
        baseline = rank_subgroups(rows, siblings, vectors)
        changed = rank_subgroups(rows, siblings, vectors, sibling_vectors={
            'C1': [0, 0, 1], 'C2': [1, 0, 0], 'C3': [0, .1, 1]})
        self.assertEqual(baseline[0]['members'], ['C1', 'C2'])
        self.assertEqual(changed[0]['members'], ['C1', 'C3'])
        self.assertEqual(changed[0]['ranked'][0]['subject'], 'AC')
        self.assertEqual(rank_subgroups(rows, siblings, vectors), baseline)

    def test_sibling_vectors_distinguish_same_heading_with_different_meanings(self):
        siblings = [dict(id='C1', subject='Meals'), dict(id='C2', subject='Meals'),
                    dict(id='C3', subject='Other')]
        rows = [dict(note_id='a', number='1', subject='Candidate')]
        groups = rank_subgroups(rows, siblings, {'Candidate': [1, 0]},
                               sibling_vectors={'C1': [1, 0], 'C2': [0, 1], 'C3': [1, .1]})
        self.assertEqual(groups[0]['members'], ['C1', 'C3'])

    def test_sibling_vectors_must_cover_exact_nodes_and_share_valid_dimensions(self):
        siblings = [dict(id='C1', subject='A'), dict(id='C2', subject='B'),
                    dict(id='C3', subject='C')]
        rows = [dict(note_id='a', number='1', subject='Candidate')]
        good = {'C1': [1, 0], 'C2': [0, 1], 'C3': [1, 1]}
        invalid = [{k: v for k, v in good.items() if k != 'C1'},
                   dict(good, C4=[1, 0]), dict(good, C1=[0, 0]),
                   dict(good, C1=[float('nan'), 0]), dict(good, C1=[1])]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                rank_subgroups(rows, siblings, {'Candidate': [1, 0]}, sibling_vectors=values)

    def test_empty_candidates_or_siblings_keep_the_original_empty_result(self):
        row = dict(note_id='a', number='1', subject='Food')
        self.assertEqual(rank_candidates([row], [], {}), [])
        self.assertEqual(rank_candidates([], [dict(id='C1', subject='Food')], {}), [])
        self.assertEqual(rank_subgroups([], [], {}), [])

    def test_subgroup_ranking_prefers_a_selective_match_over_a_broad_match(self):
        siblings = [dict(id='C1', subject='Cookware'), dict(id='C2', subject='Appliances'),
                    *[dict(id=f'C{i}', subject=f'Other {i}') for i in range(3, 8)]]
        rows = [dict(note_id='a', number='1', subject='Equipment'),
                dict(note_id='b', number='1', subject='Everything')]
        vectors = {'Cookware': [1, 0, 0], 'Appliances': [1, .1, 0],
                   'Equipment': [1, 0, 0], 'Everything': [1, 0, 1],
                   **{f'Other {i}': [0, 0, 1] for i in range(3, 8)}}
        groups = rank_subgroups(rows, siblings, vectors)
        group = next(g for g in groups if g['members'] == ['C1', 'C2'])
        self.assertEqual([r['subject'] for r in group['ranked']], ['Equipment', 'Everything'])
        self.assertEqual(group['remaining_choices_if_grouped'], 6)
        self.assertTrue(group['within_choice_limit_if_grouped'])
        self.assertNotIn('relation', group['ranked'][0])
        self.assertNotIn('placement', group)

    def test_subgroups_are_proper_and_do_not_force_a_partition(self):
        siblings = [dict(id=f'C{i}', subject=f'S{i}') for i in range(7)]
        rows = [dict(note_id='a', number='1', subject='Candidate')]
        vectors = {f'S{i}': [1, i / 10] for i in range(7)}
        vectors['Candidate'] = [1, .2]
        groups = rank_subgroups(rows, siblings, vectors)
        self.assertTrue(all(2 <= len(g['members']) <= 6 for g in groups))
        self.assertEqual(len({tuple(g['members']) for g in groups}), len(groups))
        pairs = [set(g['members']) for g in groups if len(g['members']) == 2]
        self.assertTrue(any(a & b for i, a in enumerate(pairs) for b in pairs[i + 1:]))
        self.assertEqual(groups, rank_subgroups(rows[::-1], siblings[::-1], vectors))

    def test_subgroup_members_must_all_be_eligible_but_other_siblings_still_count(self):
        siblings = [dict(id='C1', subject='A'), dict(id='C2', subject='B'),
                    dict(id='C3', subject='Outside')]
        rows = [dict(note_id='a', number='1', subject='Candidate'),
                dict(note_id='b', number='1', subject='Candidate')]
        vectors = {'A': [1, 0], 'B': [1, .1], 'Outside': [1, 0],
                   'Candidate': [1, 0]}
        groups = rank_subgroups(rows, siblings, vectors, eligible={
            ('a', '1'): ['C1', 'C2'], ('b', '1'): ['C1']})
        group = next(g for g in groups if g['members'] == ['C1', 'C2'])
        self.assertEqual(len(group['ranked']), 1)
        self.assertEqual(group['ranked'][0]['local']['note_id'], 'a')
        self.assertEqual(group['ranked'][0]['strongest_outside_match']['canonical_id'], 'C3')
        self.assertLess(group['ranked'][0]['score'], 0)

    def test_subgroup_ranking_requires_matching_every_member(self):
        siblings = [dict(id='C1', subject='A'), dict(id='C2', subject='B'),
                    dict(id='C3', subject='Outside')]
        rows = [dict(note_id='a', number='1', subject='Only A'),
                dict(note_id='b', number='1', subject='Both')]
        vectors = {'A': [1, 0, 0], 'B': [.5, .5, 0], 'Outside': [0, 0, 1],
                   'Only A': [1, -.5, 0], 'Both': [1, .5, 0]}
        group = next(g for g in rank_subgroups(rows, siblings, vectors)
                     if g['members'] == ['C1', 'C2'])
        self.assertEqual(group['ranked'][0]['subject'], 'Both')

    def test_a_candidate_matching_two_siblings_beats_one_exact_match(self):
        siblings = [dict(id='C1', subject='Cookware'),
                    dict(id='C2', subject='Grilling')]
        locals = [dict(note_id='a', number='1', subject='Frying pan'),
                  dict(note_id='b', number='1', subject='Cooking')]
        vectors = {'Cookware': [1, 0], 'Grilling': [0, 1],
                   'Frying pan': [1, 0], 'Cooking': [1, 1]}
        ranked = rank_candidates(locals, siblings, vectors)
        self.assertEqual([row['local']['note_id'] for row in ranked], ['b', 'a'])
        self.assertEqual(ranked[0]['matches'][0]['canonical_id'], 'C1')
        self.assertEqual(ranked[0]['matches'][1]['canonical_id'], 'C2')
        self.assertNotIn('relation', ranked[0])

    def test_native_eligibility_changes_each_entry_even_for_identical_headings(self):
        siblings = [dict(id='C1', subject='Cookware'),
                    dict(id='C2', subject='Grilling'),
                    dict(id='C3', subject='Bread preparation')]
        locals = [dict(note_id='a', number='1', subject='Cooking'),
                  dict(note_id='b', number='1', subject='Cooking')]
        vectors = {'Cookware': [1, 0], 'Grilling': [1, 0],
                   'Bread preparation': [0, 1], 'Cooking': [1, 0]}
        ranked = rank_candidates(locals, siblings, vectors, eligible={
            ('a', '1'): ['C1', 'C3'], ('b', '1'): ['C1', 'C2']})
        self.assertEqual([row['local']['note_id'] for row in ranked], ['b', 'a'])
        self.assertEqual([row['score'] for row in ranked], [1, 0])

    def test_one_eligible_sibling_does_not_claim_a_grouping_score(self):
        siblings = [dict(id='C1', subject='Food')]
        locals = [dict(note_id='a', number='1', subject='Food')]
        ranked = rank_candidates(locals, siblings, {'Food': [1, 0]})
        self.assertIsNone(ranked[0]['score'])
        self.assertEqual(ranked[0]['eligible_siblings'], 1)

    def test_duplicate_canonical_headings_still_describe_distinct_nodes(self):
        siblings = [dict(id='C1', subject='Dinner'), dict(id='C2', subject='Dinner')]
        locals = [dict(note_id='a', number='1', subject='Meals')]
        ranked = rank_candidates(locals, siblings, {'Dinner': [1, 0], 'Meals': [1, 1]})
        self.assertEqual([match['canonical_id'] for match in ranked[0]['matches']], ['C1', 'C2'])

    def test_ties_use_source_identity_independently_of_input_order(self):
        siblings = [dict(id='C1', subject='Meals'), dict(id='C2', subject='Meals')]
        locals = [dict(note_id='b', number='1', subject='Meals'),
                  dict(note_id='a', number='1', subject='Meals')]
        first = rank_candidates(locals, siblings, {'Meals': [1, 0]})
        self.assertEqual(first, rank_candidates(locals[::-1], siblings[::-1], {'Meals': [1, 0]}))

    def test_unknown_eligibility_and_missing_or_invalid_vectors_are_rejected(self):
        siblings = [dict(id='C1', subject='Meals'), dict(id='C2', subject='Food')]
        locals = [dict(note_id='a', number='1', subject='Meals')]
        with self.assertRaisesRegex(ValueError, 'unknown sibling'):
            rank_candidates(locals, siblings, {'Meals': [1, 0], 'Food': [0, 1]},
                            eligible={('a', '1'): ['C9']})
        for vectors in ({'Meals': [1, 0]}, {'Meals': [1, 0], 'Food': [0, 0]},
                        {'Meals': [float('nan'), 0], 'Food': [0, 1]},
                        {'Meals': [1, 0], 'Food': [1]}):
            with self.assertRaises(ValueError):
                rank_candidates(locals, siblings, vectors)

    def test_input_state_and_vectors_are_not_modified(self):
        import copy
        siblings = [dict(id='C1', subject='Food'), dict(id='C2', subject='Meals')]
        locals = [dict(note_id='a', number='1', subject='Meals')]
        vectors = {'Food': [0, 2], 'Meals': [2, 0]}
        original = copy.deepcopy((locals, siblings, vectors))
        rank_candidates(locals, siblings, vectors)
        self.assertEqual((locals, siblings, vectors), original)


class SiblingMeaningLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state.json'
        self.state.write_text('original state')
        self.siblings = [dict(id='C1', subject='Meals', meaning='Occasions of eating food.'),
                         dict(id='C2', subject='Meals', meaning='Food eaten together.')]
        pairs, notes, rows = [], [], []
        for node in self.siblings:
            text = node['meaning']
            digest = hashlib.sha256(text.encode()).hexdigest()
            sid = hashlib.sha256((digest + f':0:{len(text.encode())}').encode()).hexdigest()[:16]
            pair_id = hashlib.sha256((node['subject'] + '\0' + text).encode()).hexdigest()
            pairs.append(dict(id=pair_id, subject=node['subject'], meaning=text,
                              representations=dict(meaning=[digest, sid])))
            notes.append(dict(note_id=digest, text=text, subjects=[
                dict(subject_id=sid, byte_spans=[[0, len(text.encode())]])]))
            rows.append(dict(note_id=digest, subject_id=sid))
        self.plan = dict(state=str(self.state), pairs=pairs,
            references={'node:' + n['id']: p['id'] for n, p in zip(self.siblings, pairs)},
            protected_sha256={str(self.state): hashlib.sha256(self.state.read_bytes()).hexdigest()})
        self.identity = dict(checkpoint_sha256='checkpoint', base_model_artifact_tree_sha256='model',
                             model='same SSE model', dimensions=2)
        (self.root / 'worker-result').mkdir()
        self.save('inputs.json', self.plan)
        self.save('worker-request.json', dict(schema_version=1, notes=notes,
            proposal_sha256=hashlib.sha256((self.root / 'inputs.json').read_bytes()).hexdigest()))
        raw = self.root / 'worker-result/raw-vectors.f32le'
        raw.write_bytes(struct.pack('<ffff', 1, 0, 0, 1))
        self.receipt = dict(self.identity, rows=rows, row_count=2,
            proposal_sha256=hashlib.sha256((self.root / 'inputs.json').read_bytes()).hexdigest(),
            request_sha256=hashlib.sha256((self.root / 'worker-request.json').read_bytes()).hexdigest(),
            files={raw.name: dict(sha256=hashlib.sha256(raw.read_bytes()).hexdigest())})
        self.save('worker-result/worker-receipt.json', self.receipt)

    def save(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def load(self, siblings=None, identity=None):
        return load_sibling_meanings(self.root, self.state,
            self.siblings if siblings is None else siblings,
            self.identity if identity is None else identity, ancestor_cosine_probe)

    def test_real_receipt_reader_binds_distinct_meanings_and_preserves_sources(self):
        vectors, protected = self.load()
        self.assertEqual(list(vectors['C1']), [1, 0])
        self.assertEqual(list(vectors['C2']), [0, 1])
        self.assertEqual(len(protected), 5)
        self.assertFalse(vectors['C1'].flags.writeable)

    def test_changed_state_meaning_checkpoint_or_binding_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'meaning differs'):
            self.load([dict(self.siblings[0], meaning='Changed.'), self.siblings[1]])
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            self.load(identity=dict(self.identity, checkpoint_sha256='different'))
        self.save('inputs.json', dict(self.plan, changed=True))
        with self.assertRaisesRegex(ValueError, 'saved plan or request'):
            self.load()

    def test_changed_protected_source_is_rejected(self):
        self.state.write_text('changed state')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.load()


if __name__ == '__main__':
    unittest.main()
