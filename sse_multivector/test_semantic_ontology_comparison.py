import copy
import unittest

from semantic_graph_patterns import construct
from semantic_ontology_comparison import compare_condition, resource_names


class SemanticOntologyComparisonTests(unittest.TestCase):
    def test_uses_the_declared_resource_list_not_files_from_other_kbs(self):
        xml = '<configuration><kb name="SUMO"><constituent filename="B.kif"/>' \
              '<constituent filename="A.kif"/></kb><kb name="other">' \
              '<constituent filename="Other.kif"/></kb></configuration>'
        self.assertEqual(resource_names(xml), ['A.kif', 'B.kif'])

    def test_refuses_unsafe_ambiguous_or_empty_resource_lists(self):
        for xml in [
            '<configuration/>',
            '<configuration><kb name="SUMO"/></configuration>',
            '<configuration><kb name="SUMO"><constituent filename="../A.kif"/></kb></configuration>',
            '<configuration><kb name="SUMO"><constituent filename="A.kif"/>'
            '<constituent filename="A.kif"/></kb></configuration>',
        ]:
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                resource_names(xml)

    def fixture(self):
        records = [{'row': i, 'note': f'N{i}'} for i in [1, 2, 3]]
        graphs = [{'row': i, 'nodes': [
            {'id': 0, 'sense': 'event.v.01', 'context': 0},
            {'id': 1, 'sense': 'object.n.01', 'context': 0}],
            'edges': [{'source': 0, 'role': 'R', 'target': 1}] if i != 3 else []}
            for i in [1, 2, 3]]
        lexicon = {
            'event.v.01': {'ancestors': ['event.v.01', 'SUMO:Process']},
            'object.n.01': {'ancestors': ['object.n.01', 'SUMO:Object']},
            'SUMO:Process': {'ancestors': ['SUMO:Process']},
            'SUMO:Object': {'ancestors': ['SUMO:Object']},
        }
        before = construct(records, graphs, {}, relation_policy='connection')['conditions'][1]
        after = construct(records, graphs, lexicon, relation_policy='connection')['conditions'][1]
        return before, after

    def test_preserves_existing_keys_and_audits_new_meanings_with_old_support(self):
        before, after = self.fixture()
        result = compare_condition(before, after)
        pairs = result['new_recurring_patterns']
        target = next(p for p in pairs if p['key'] == ['SUMO:Object', 'SUMO:Process'])
        self.assertEqual(target['notes'], ['N1', 'N2'])
        self.assertTrue(target['same_note_set_in_baseline'])
        self.assertEqual(target['singleton_row_intersection'], [1, 2, 3])
        self.assertEqual(target['connection_excluded_rows'], [3])
        self.assertEqual(target['rows'], [1, 2])
        self.assertTrue(result['baseline_patterns_unchanged'])

    def test_rejects_changed_or_missing_old_pattern_evidence(self):
        before, after = self.fixture()
        for change in ['notes', 'delete']:
            broken = copy.deepcopy(after)
            old = next(p for p in broken['patterns'] if p['id'] == before['patterns'][0]['id'])
            if change == 'notes':
                old['notes'].append('N99')
            else:
                broken['patterns'].remove(old)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'baseline'):
                compare_condition(before, broken)

    def intervention_fixture(self):
        records = [{'row': row, 'note': f'N{row}'} for row in [1, 2, 3, 4]]
        graphs = []
        for row in [1, 2, 3, 4]:
            nodes = [{'id': 2, 'sense': 'object.n.01', 'context': 0}]
            if row in [1, 2]:
                nodes.append({'id': 0, 'sense': 'activity.n.01', 'context': 0})
            if row in [1, 3]:
                nodes.append({'id': 1, 'sense': 'event.v.01', 'context': 0})
            graphs.append({'row': row, 'nodes': nodes,
                           'edges': [{'source': node['id'], 'role': 'R', 'target': 2}
                                     for node in nodes if node['id'] != 2]})
        nouns = {
            'activity.n.01': {'ancestors': ['activity.n.01', 'SUMO:Process']},
            'object.n.01': {'ancestors': ['object.n.01', 'SUMO:Entity']},
            'event.v.01': {'ancestors': ['event.v.01']},
            'SUMO:Process': {'ancestors': ['SUMO:Process']},
            'SUMO:Entity': {'ancestors': ['SUMO:Entity']},
        }
        both = copy.deepcopy(nouns)
        both['event.v.01']['ancestors'] += ['SUMO:Process', 'SUMO:Entity']
        return tuple(construct(records, graphs, lexicon, relation_policy='connection')['conditions'][1]
                     for lexicon in [nouns, both])

    def test_reports_existing_sumo_expansion_only_when_explicitly_allowed(self):
        before, after = self.intervention_fixture()
        with self.assertRaisesRegex(ValueError, 'baseline'):
            compare_condition(before, after)
        result = compare_condition(before, after, allow_sumo_support_changes=True)
        self.assertFalse(result['baseline_patterns_unchanged'])
        self.assertTrue(result['wordnet_patterns_unchanged'])
        changed = result['changed_recurring_patterns']
        process = next(p for p in changed if p['after']['key'] == ['SUMO:Process'])
        self.assertEqual(process['before']['notes'], ['N1', 'N2'])
        self.assertEqual(process['after']['notes'], ['N1', 'N2', 'N3'])
        self.assertEqual(process['added_rows'], [3])
        self.assertEqual(process['added_notes'], ['N3'])
        self.assertEqual(process['removed_rows'], [])
        self.assertEqual(process['removed_notes'], [])
        old = next(p for p in before['patterns'] if p['id'] == process['before']['id'])
        new = next(p for p in after['patterns'] if p['id'] == process['after']['id'])
        self.assertEqual(process['before'], old)
        self.assertEqual(process['after']['witnesses'], new['witnesses'])
        self.assertIn(['N1', 'N2', 'N3'], result['new_recurring_note_sets'])
        self.assertEqual(result['removed_recurring_note_sets'], [])

    def test_reports_new_witnesses_with_unchanged_sumo_support(self):
        before, after = self.intervention_fixture()
        result = compare_condition(before, after, allow_sumo_support_changes=True)
        entity = next(p for p in result['changed_recurring_patterns']
                      if p['after']['key'] == ['SUMO:Entity'])
        self.assertEqual(entity['before']['rows'], entity['after']['rows'])
        self.assertEqual(entity['added_rows'], [])
        self.assertEqual(entity['added_notes'], [])
        self.assertGreater(len(entity['after']['witnesses']), len(entity['before']['witnesses']))

    def test_permissive_comparison_keeps_wordnet_evidence_and_sumo_identity_exact(self):
        before, after = self.intervention_fixture()
        for change in ['wordnet_witness', 'sumo_id', 'sumo_kind', 'sumo_key', 'delete_sumo']:
            broken = copy.deepcopy(after)
            if change == 'wordnet_witness':
                pattern = next(p for p in broken['patterns'] if p['key'] == ['event.v.01'])
                pattern['witnesses'][0]['contexts'][0] = 99
            else:
                pattern = next(p for p in broken['patterns'] if p['key'] == ['SUMO:Process'])
                if change == 'delete_sumo':
                    broken['patterns'].remove(pattern)
                else:
                    field = change.removeprefix('sumo_')
                    pattern[field] = ['SUMO:Other'] if field == 'key' else 'changed'
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'baseline'):
                compare_condition(before, broken, allow_sumo_support_changes=True)

    def test_reports_disappearing_note_sets_and_evidence_losses(self):
        records = [{'row': row, 'note': f'N{row}'} for row in [1, 2, 3, 4]]
        graphs = [{'row': row, 'nodes': [
            {'id': index, 'sense': sense, 'context': 0}
            for index, (sense, rows) in enumerate([
                ('activity.n.01', [1, 2]), ('event.v.01', [1, 3]), ('other.v.01', [4])])
            if row in rows], 'edges': []} for row in [1, 2, 3, 4]]
        lexicon = {
            'activity.n.01': {'ancestors': ['activity.n.01', 'SUMO:Process']},
            'event.v.01': {'ancestors': ['event.v.01', 'SUMO:Process']},
            'other.v.01': {'ancestors': ['other.v.01']},
            'SUMO:Process': {'ancestors': ['SUMO:Process']},
        }
        before = construct(records, graphs, lexicon, relation_policy='connection')['conditions'][1]
        lexicon['other.v.01']['ancestors'].append('SUMO:Process')
        after = construct(records, graphs, lexicon, relation_policy='connection')['conditions'][1]
        forward = compare_condition(before, after, allow_sumo_support_changes=True)
        self.assertEqual(forward['new_recurring_patterns'], [])
        self.assertEqual(forward['removed_recurring_note_sets'], [['N1', 'N2', 'N3']])
        self.assertEqual(forward['new_recurring_note_sets'], [['N1', 'N2', 'N3', 'N4']])
        reverse = compare_condition(after, before, allow_sumo_support_changes=True)
        change, = reverse['changed_recurring_patterns']
        self.assertEqual(change['removed_rows'], [4])
        self.assertEqual(change['removed_notes'], ['N4'])
        self.assertEqual(change['added_rows'], [])


if __name__ == '__main__':
    unittest.main()
