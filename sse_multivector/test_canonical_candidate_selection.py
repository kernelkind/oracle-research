"""Replay protects directional inference and reports hidden contradictory answers."""
import unittest

from sse_multivector.canonical_candidate_selection import evaluate_snapshots


class CanonicalCandidateSelectionTests(unittest.TestCase):
    def snapshot(self, relations, *, mapped='C002', held=False):
        nodes = [dict(id='C001', subject='Food', meaning='Food for eating.', parents=[], entries=[]),
                 dict(id='C002', subject='Vegetables', meaning='Vegetables for eating.',
                      parents=['C001'], entries=[]),
                 dict(id='C003', subject='Carrots', meaning='Carrots for eating.',
                      parents=['C002'], entries=[])]
        local = dict(note_id='new-note', number='1')
        meaning = 'Vegetables for eating.'
        answers = [dict(id=identifier, status='valid',
                        output=dict(meaning=meaning, relation=relation, reason='Saved conclusion.'),
                        receipt=dict(record_sha256='verified-by-loader'))
                   for identifier, relation in relations.items()]
        return dict(index=3, adapter='hierarchy_node_pairs', local=local,
                    local_input=dict(entry=dict(subject='Vegetables'), meaning=meaning),
                    selected_meaning=meaning, mapped_parent=mapped, answers=answers,
                    prompt_bytes={identifier: 200 for identifier in relations},
                    before=nodes, after=nodes,
                    status='held' if held else 'equivalent',
                    canonical_id=None if held else 'C002',
                    reason='contradiction at C001' if held else None)

    def profile(self, step, limit=1, closure=True):
        result = evaluate_snapshots([step], [limit])
        name = f'text-{limit}' + ('-closure' if closure else '')
        return next(p for p in result['profiles'] if p['id'] == name)

    def test_equivalence_supplies_strict_ancestor_and_descendant_relationships(self):
        step = self.snapshot(dict(C001='canonical_contains_local', C002='equivalent',
                                  C003='local_contains_canonical'))
        profile = self.profile(step)
        self.assertEqual(profile['totals']['asked'], 1)
        self.assertEqual(profile['totals']['inferred'], 2)
        self.assertEqual(profile['positive_recall'], 1)
        self.assertEqual(profile['steps'][0]['inferred']['C001']['relation'], 'canonical_contains_local')
        self.assertEqual(profile['steps'][0]['inferred']['C003']['relation'], 'local_contains_canonical')

    def test_neither_excludes_only_one_direction_for_descendants(self):
        step = self.snapshot(dict(C001='neither', C002='neither', C003='local_contains_canonical'),
                             mapped='C001')
        profile = self.profile(step)
        self.assertEqual(profile['steps'][0]['asked'], ['C001'])
        self.assertEqual(profile['steps'][0]['inferred'], {})
        self.assertIn('C003', profile['steps'][0]['missed_positive'])

    def test_uncertain_does_not_supply_transitive_exclusions(self):
        step = self.snapshot(dict(C001='neither', C002='uncertain', C003='neither'))
        profile = self.profile(step)
        self.assertEqual(profile['steps'][0]['inferred'], {})
        self.assertEqual(profile['steps'][0]['frozen_proposal_guard'], 'unresolved_selected_answer')

    def test_positive_recall_does_not_hide_a_withheld_ancestor_disagreement(self):
        step = self.snapshot(dict(C001='neither', C002='canonical_contains_local', C003='neither'), held=True)
        profile = self.profile(step)
        self.assertEqual(profile['positive_recall'], 1)
        self.assertEqual(profile['totals']['inferred_disagreements'], 1)
        self.assertEqual(profile['totals']['held_pair_steps_without_guard'], 1)
        disagreement = profile['steps'][0]['inferred_disagreements'][0]
        self.assertEqual((disagreement['id'], disagreement['observed']), ('C001', 'neither'))
        self.assertEqual(disagreement['inferred'], 'canonical_contains_local')


if __name__ == '__main__':
    unittest.main()
