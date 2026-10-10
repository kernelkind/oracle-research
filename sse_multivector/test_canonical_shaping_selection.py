"""Local nominations for overcrowded groups; relationships stay with traversal."""
import unittest

from sse_multivector.canonical_shaping_selection import rank_candidates, rank_subgroups


class ShapingSelectionTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
