"""Production CLI checks for witnessed shaping of saved canonical graphs."""
import json
import unittest

from sse_multivector import test_experiment as fixtures
from sse_multivector import test_canonical_trial as roots_fixtures
from sse_multivector import test_canonical_hierarchy_audit as audit_fixtures


class CanonicalHierarchyShapeTests(unittest.TestCase):
    setUp = fixtures.ExperimentTests.setUp
    write = fixtures.ExperimentTests.write
    cli = fixtures.ExperimentTests.cli
    setup_trial = roots_fixtures.CanonicalTrialTests.setup_trial
    completed_trial = audit_fixtures.CanonicalHierarchyAuditTests.completed_trial

    def shape_source(self):
        self.completed_trial()
        return self.write('shape.json', {'schema_version': 1, 'trial': 'trial',
            'roots': ['C001', 'C002'], 'children': {'C001': ['C003'], 'C002': ['C003']}})

    def test_shape_preserves_fixed_nodes_and_records_transitive_witnesses(self):
        self.shape_source()
        original_path = self.root / 'trial/state.json'
        original_bytes = original_path.read_bytes()
        original = json.loads(original_bytes)
        summary = json.loads(self.cli('shape-canonical-trial', '--source', 'shape.json',
                                     '--output', 'candidate').stdout)
        shaped = json.loads((self.root / 'candidate/state.json').read_text())
        self.assertEqual(original_path.read_bytes(), original_bytes)
        self.assertEqual(shaped['roots'], original['roots'])
        before = {node['id']: node for node in original['nodes']}
        after = {node['id']: node for node in shaped['nodes']}
        for identifier in before:
            for field in ('subject', 'meaning', 'entries'):
                self.assertEqual(after[identifier][field], before[identifier][field])
        self.assertEqual(after['C003']['parents'], ['C001', 'C002'])
        self.assertEqual(shaped['status'], 'shaped_candidate')
        witnesses = shaped['shape']['edges']
        shortcut = next(edge for edge in witnesses if edge['parent'] == 'C001')
        self.assertEqual(shortcut['original_path'], ['C001', 'C002', 'C003'])
        self.assertEqual(shaped['shape']['omitted_edges'], [{'parent': 'C001', 'child': 'C002'}])
        self.assertFalse(summary['done'])
        audit = json.loads((self.root / 'candidate/audit.json').read_text())
        self.assertEqual(audit['note_coverage']['missing'], [])
        self.assertEqual(audit['metrics']['roots'], 2)
        self.assertEqual(len(fixtures.ExperimentTests.calls(self)), 4)


    def test_shape_rejects_dropped_notes_and_unknown_relationships_before_publication(self):
        self.shape_source()
        source = json.loads((self.root / 'shape.json').read_text())
        cases = [
            {'roots': ['C001'], 'children': {'C001': ['C003']}},
            {'roots': ['C001'], 'children': {'C001': ['C002'], 'C003': ['C002']}}]
        for i, fields in enumerate(cases):
            self.write('shape.json', {**source, **fields})
            result = self.cli('shape-canonical-trial', '--source', 'shape.json',
                              '--output', f'rejected-{i}', ok=False)
            expected = 'drops selected notes' if i == 0 else 'parentless nodes'
            self.assertIn(expected, result.stderr)
            self.assertFalse((self.root / f'rejected-{i}').exists())
        self.write('shape.json', {**source, 'roots': ['C001', 'C003'],
                                 'children': {'C003': ['C002']}})
        result = self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'reverse', ok=False)
        self.assertIn('not an original transitive containment', result.stderr)
        self.assertFalse((self.root / 'reverse').exists())

    def test_shape_rejects_duplicate_unknown_self_and_cyclic_selections(self):
        self.shape_source()
        source = json.loads((self.root / 'shape.json').read_text())
        cases = [
            {'roots': ['C001', 'C001'], 'children': {}},
            {'roots': ['C001'], 'children': {'C001': ['C002', 'C002', 'C003']}},
            {'roots': ['unknown'], 'children': {}},
            {'roots': ['C001'], 'children': {'C001': ['C001']}},
            {'roots': ['C001'], 'children': {'C001': ['C002'], 'C002': ['C001']}}]
        for i, fields in enumerate(cases):
            self.write('shape.json', {**source, **fields})
            self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', f'bad-{i}', ok=False)
            self.assertFalse((self.root / f'bad-{i}').exists())

    def test_shape_refuses_budget_overflow_source_changes_and_existing_output(self):
        self.shape_source()
        original = (self.root / 'trial/state.json').read_bytes()
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'small',
                 '--work-budget', '1', ok=False)
        self.assertFalse((self.root / 'small').exists())
        existing = self.root / 'existing'
        existing.mkdir()
        marker = existing / 'preserve.txt'
        marker.write_text('Keep existing output')
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', existing, ok=False)
        self.assertEqual(marker.read_text(), 'Keep existing output')
        path = self.root / 'notes.json'
        path.write_bytes(path.read_bytes() + b'\n')
        result = self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'changed', ok=False)
        self.assertIn('trial source changed', result.stderr)
        self.assertFalse((self.root / 'changed').exists())
        self.assertEqual((self.root / 'trial/state.json').read_bytes(), original)

    def test_audit_budget_failure_removes_unpublished_candidate(self):
        self.shape_source()
        summary = json.loads(self.cli('shape-canonical-trial', '--source', 'shape.json',
                                     '--output', 'reference').stdout)
        limit = summary['shape_work_used'] + 1
        result = self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'limited',
                          '--work-budget', str(limit), ok=False)
        self.assertIn('work budget exceeded', result.stderr)
        self.assertFalse((self.root / 'limited').exists())
        self.assertTrue((self.root / 'reference/audit.json').exists())

    def test_shaped_state_source_hashes_and_actual_state_path_reference(self):
        import hashlib
        self.shape_source()
        source = json.loads((self.root / 'shape.json').read_text())
        source['trial'] = 'trial/state.json'
        self.write('shape.json', source)
        self.cli('shape-canonical-trial', '--source', 'shape.json', '--output', 'candidate')
        shaped = json.loads((self.root / 'candidate/state.json').read_text())
        for name in ('shape.json', 'trial/state.json'):
            path = self.root / name
            self.assertEqual(shaped['sources'][str(path)], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertFalse(shaped['shape']['semantic_certified'])
        self.assertEqual(shaped['shape']['group_task_coverage'], 'unknown')
        self.cli('prepare-canonical-child-trial', 'not-construction', '--base-trial', 'candidate', ok=False)
        self.assertFalse((self.root / 'not-construction').exists())


if __name__ == '__main__':
    unittest.main()
