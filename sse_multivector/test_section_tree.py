"""Production CLI checks for the experimental fixed-group construction."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector import section_count_panel as panel


class SectionTreeTests(unittest.TestCase):
    def _fixture(self, root, *, one_note=False, attach_nearest=True, outsider=False):
        angles = np.repeat(np.r_[np.arange(12) * .001, np.arange(1, 6)], 2)
        if outsider:
            angles = np.r_[angles, .0031]
        notes = np.array(['only' if one_note else f'n{i}' for i in range(len(angles))])
        np.savez(root / 'input.npz', vectors=np.c_[np.cos(angles), np.sin(angles)], notes=notes)
        entries = [dict(id=f'e{i}', title=f'Topic {i // 2}', meaning=f'Definition {i // 2}',
                        note_id=str(notes[i]), source_group=f'g{i // 2}')
                   for i in range(len(angles))]
        (root / 'entries.json').write_text(json.dumps(entries))
        source = dict(input=str(root / 'input.npz'), entries=str(root / 'entries.json'),
                      files={str(root / name): hashlib.sha256((root / name).read_bytes()).hexdigest()
                             for name in ['input.npz', 'entries.json']})
        spec = dict(sources=dict(test=source), counts=[1, 6], seeds=[10, 11],
                    max_iterations=50, time_limit=30, cases=[dict(id='Roots', role='development',
                    source='test', selector=dict(kind='all'), minimum_notes=0, preserve_groups=True,
                    reciprocal_nearest=True, attach_nearest=attach_nearest)])
        (root / 'spec.json').write_text(json.dumps(spec))
        panel.prepare(root / 'spec.json', root / 'panel')
        panel.run(root / 'panel', 'Roots')
        return entries

    def _cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'sse_multivector.section_tree', *map(str, args)],
                              capture_output=True, text=True)

    def _build(self, root, *, one_note=False):
        entries = self._fixture(root, one_note=one_note)
        prepared = self._cli('prepare', root / 'panel', 'Roots', root / 'tree',
                             '--corpus-notes', 1 if one_note else len(entries),
                             '--minimum-root-notes', 1)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        result = self._cli('run', root / 'tree')
        self.assertEqual(result.returncode, 0, result.stderr)
        return entries, json.loads((root / 'tree/tree.json').read_text())

    def test_cli_complete_tree_preserves_groups_stops_before_matching_and_resumes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries, tree = self._build(root)
            nodes = {node['id']: node for node in tree['nodes']}
            self.assertEqual(tree['roots'], ['1', '2', '3', '4', '5', '6'])
            self.assertEqual(tree['summary']['covered_notes'], len(entries))
            self.assertEqual(tree['summary']['max_children'], 6)
            self.assertGreaterEqual(tree['summary']['max_leaf_depth'], 3)
            self.assertFalse(tree['summary']['non_narrowing_edges'])
            self.assertFalse(tree['summary']['unresolved_nodes'])
            leaves = [n for n in nodes.values() if not n['children']]
            rows = [i for n in leaves for i in n['indices']]
            self.assertEqual(sorted(rows), list(range(len(entries))))
            for i in range(0, len(entries), 2):
                self.assertTrue(any(i in n['indices'] and i + 1 in n['indices'] for n in leaves))
            for node in nodes.values():
                if node['mode'] == 'direct_groups':
                    self.assertLessEqual(node['inherited_group_count'], 6)
                    self.assertFalse(node['matching_applied'])
                    self.assertEqual(len(node['children']), node['inherited_group_count'])
                if len(node['indices']) == 2:
                    self.assertFalse(node['children'])
                    self.assertEqual(node['mode'], 'leaf')
            before = {p: p.read_bytes() for p in (root / 'tree').rglob('*.json')}
            resumed = self._cli('run', root / 'tree')
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            (root / 'entries.json').write_text('[]')
            changed = self._cli('run', root / 'tree')
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn('Frozen source changed', changed.stderr)

    def test_one_note_does_not_replace_the_group_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            entries, tree = self._build(Path(directory), one_note=True)
            self.assertGreaterEqual(tree['summary']['max_leaf_depth'], 3)
            self.assertEqual(tree['summary']['covered_notes'], 1)
            self.assertTrue(tree['summary']['non_narrowing_edges'])
            self.assertFalse(tree['summary']['quality_requirements_pass'])
            self.assertEqual(sum(len(n['indices']) for n in tree['nodes'] if not n['children']),
                             len(entries))

    def test_completed_partition_and_root_result_cannot_change_silently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._build(root)
            path = next((root / 'tree/fits').glob('*.json'))
            saved = json.loads(path.read_text())
            saved['binding']['node'] = 'different'
            path.write_text(json.dumps(saved))
            resumed = self._cli('run', root / 'tree')
            self.assertNotEqual(resumed.returncode, 0)
            self.assertIn('frozen bindings', resumed.stderr)
            path = root / 'panel/Roots/count-6.json'
            path.write_text('{}')
            changed = self._cli('run', root / 'tree')
            self.assertNotEqual(changed.returncode, 0)
            self.assertIn('Frozen source changed', changed.stderr)

    def test_cli_freezes_root_attachment_setting_and_uses_it_at_every_depth(self):
        with tempfile.TemporaryDirectory() as directory:
            for enabled in [True, False]:
                root = Path(directory) / str(enabled)
                root.mkdir()
                self._fixture(root, attach_nearest=enabled, outsider=True)
                producer = json.loads((root / 'panel/plan.json').read_text())['cases'][0]
                self.assertEqual(bool(producer.get('nearest_attachments', [])), enabled)
                prepared = self._cli('prepare', root / 'panel', 'Roots', root / 'tree',
                                     '--corpus-notes', 35, '--minimum-root-notes', 1)
                self.assertEqual(prepared.returncode, 0, prepared.stderr)
                plan = json.loads((root / 'tree/plan.json').read_text())
                self.assertEqual(plan['attach_nearest'], enabled)
                self.assertEqual(plan['child_attach_nearest'], enabled)
                completed = self._cli('run', root / 'tree')
                self.assertEqual(completed.returncode, 0, completed.stderr)
                tree = json.loads((root / 'tree/tree.json').read_text())
                leaves = [n for n in tree['nodes'] if not n['children']]
                outsider = next(n for n in leaves if 34 in n['indices'])
                self.assertEqual(len(outsider['indices']) > 1, enabled)
                if not enabled:
                    self.assertTrue(any(n['matching_applied'] for n in tree['nodes']))
                    self.assertTrue(all(not n['nearest_attachments'] for n in tree['nodes']))
                plan['attach_nearest'] = not enabled
                (root / 'tree/plan.json').write_text(json.dumps(plan))
                changed = self._cli('run', root / 'tree')
                self.assertNotEqual(changed.returncode, 0)
                self.assertIn('Tree settings disagree', changed.stderr)

    def test_cli_can_separate_initial_from_child_attachments(self):
        with tempfile.TemporaryDirectory() as directory:
            for initial in [True, False]:
                root = Path(directory) / str(initial)
                root.mkdir()
                self._fixture(root, attach_nearest=initial, outsider=True)
                prepared = self._cli('prepare', root / 'panel', 'Roots', root / 'tree',
                    '--corpus-notes', 35, '--minimum-root-notes', 1,
                    '--child-attachments', 'off' if initial else 'on')
                self.assertEqual(prepared.returncode, 0, prepared.stderr)
                plan = json.loads((root / 'tree/plan.json').read_text())
                self.assertEqual(plan['attach_nearest'], initial)
                self.assertEqual(plan['child_attach_nearest'], not initial)
                producer = json.loads((root / 'panel/plan.json').read_text())['cases'][0]
                self.assertEqual(bool(producer.get('nearest_attachments', [])), initial)
                completed = self._cli('run', root / 'tree')
                self.assertEqual(completed.returncode, 0, completed.stderr)
                tree = json.loads((root / 'tree/tree.json').read_text())
                self.assertEqual(any(n['nearest_attachments'] for n in tree['nodes']), not initial)
                outsider = next(n for n in tree['nodes'] if not n['children'] and 34 in n['indices'])
                self.assertGreater(len(outsider['indices']), 1)
                before = {p: p.read_bytes() for p in (root / 'tree').rglob('*.json')}
                resumed = self._cli('run', root / 'tree')
                self.assertEqual(resumed.returncode, 0, resumed.stderr)
                self.assertEqual(before, {p: p.read_bytes() for p in before})
                plan['child_attach_nearest'] = 'on'
                (root / 'tree/plan.json').write_text(json.dumps(plan))
                invalid = self._cli('run', root / 'tree')
                self.assertNotEqual(invalid.returncode, 0)
                self.assertIn('Tree settings disagree', invalid.stderr)

    def test_initial_title_filter_does_not_filter_the_deeper_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, outsider=True)
            manifest = root / 'spec.json'
            spec = json.loads(manifest.read_text())
            spec['cases'][0]['attachment_same_title'] = True
            manifest.write_text(json.dumps(spec))
            producer = panel.prepare(manifest, root / 'filtered-panel')
            self.assertFalse(producer['cases'][0]['nearest_attachments'])
            panel.run(root / 'filtered-panel', 'Roots')
            prepared = self._cli('prepare', root / 'filtered-panel', 'Roots', root / 'tree',
                '--corpus-notes', 35, '--minimum-root-notes', 1, '--child-attachments', 'on')
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            completed = self._cli('run', root / 'tree')
            self.assertEqual(completed.returncode, 0, completed.stderr)
            tree = json.loads((root / 'tree/tree.json').read_text())
            self.assertTrue(any(n['nearest_attachments'] for n in tree['nodes']))
            outsider = next(n for n in tree['nodes'] if not n['children'] and 34 in n['indices'])
            self.assertGreater(len(outsider['indices']), 1)


if __name__ == '__main__':
    unittest.main()
