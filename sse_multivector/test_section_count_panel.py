"""Production CLI checks for frozen multi-section count comparisons."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from sse_multivector.section_count_panel import prepare, run


class SectionCountPanelTests(unittest.TestCase):
    def test_cli_nested_selector_uses_the_frozen_producer_original_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            angles = np.array([3, 0, 3.01, .05, 3.02, 2])
            np.savez(source['input'], vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array(['a' + str(i) for i in range(6)]))
            entries = json.loads(Path(source['entries']).read_text())
            for i, entry in enumerate(entries):
                entry['source_group'] = 'chosen' if i in [1, 3, 5] else None
            Path(source['entries']).write_text(json.dumps(entries))
            for path in [source['input'], source['entries']]:
                source['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            spec['cases'][0]['selector'] = dict(kind='source_group', value='chosen')
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'parent')
            run(root / 'parent', 'D01')
            producer_plan = root / 'parent/plan.json'
            producer_result = root / 'parent/D01/count-2.json'
            parent = json.loads(producer_result.read_text())
            labels = parent['panel']['best']['labels']
            selected = next(label for label in set(labels) if labels.count(label) == 2)
            expected = [i for i, label in zip([1, 3, 5], labels) if label == selected]
            source['labels']['parent'] = str(producer_result)
            for path in [producer_result, producer_plan]:
                source['files'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            spec['cases'][0]['selector'] = dict(kind='labels', mode='parent', value=selected,
                                               plan=str(producer_plan))
            child_spec = root / 'child.json'
            child_spec.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prepared = subprocess.run(cli + ['prepare', str(child_spec), str(root / 'child')],
                                      capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            plan = json.loads((root / 'child/plan.json').read_text())
            self.assertEqual(plan['cases'][0]['indices'], expected)
            self.assertEqual(plan['cases'][0]['entry_ids'], [str(i) for i in expected])
            self.assertEqual(plan['cases'][0]['note_ids'], ['a' + str(i) for i in expected])
            subprocess.run(cli + ['run', str(root / 'child'), 'D01'],
                           check=True, capture_output=True, text=True)
            child = json.loads((root / 'child/D01/count-2.json').read_text())['panel']['best']
            self.assertEqual(sorted(child['section_notes']), [1, 1])
            original_result = producer_result.read_bytes()
            parent['binding']['case_id'] = 'different'
            producer_result.write_text(json.dumps(parent))
            source['files'][str(producer_result)] = hashlib.sha256(producer_result.read_bytes()).hexdigest()
            child_spec.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'disagree with the frozen producer plan'):
                prepare(child_spec, root / 'wrong-binding')
            producer_result.write_bytes(original_result)
            source['files'][str(producer_result)] = hashlib.sha256(original_result).hexdigest()
            source['files'].pop(str(producer_plan))
            child_spec.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'frozen.*plan'):
                prepare(child_spec, root / 'unbound')
            producer_plan.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'child', 'D01')

    def test_child_selector_reads_the_completed_parent_panel_and_preserves_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            angles = np.array([0, .01, .02, 2, 2.01, 2.02])
            np.savez(source['input'], vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array(['a' + str(i) for i in range(6)]))
            source['files'][source['input']] = hashlib.sha256(Path(source['input']).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'parent')
            run(root / 'parent', 'D01')
            parent_path = root / 'parent/D01/count-2.json'
            parent = json.loads(parent_path.read_text())
            label = parent['panel']['best']['labels'][0]
            source['labels']['parent'] = str(parent_path)
            source['files'][str(parent_path)] = hashlib.sha256(parent_path.read_bytes()).hexdigest()
            spec['cases'][0]['selector'] = dict(kind='labels', mode='parent', value=label)
            child_spec = root / 'child.json'
            child_spec.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            result = subprocess.run(cli + ['prepare', str(child_spec), str(root / 'child')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads((root / 'child/plan.json').read_text())
            self.assertEqual(plan['cases'][0]['indices'], [0, 1, 2])
            self.assertEqual(plan['cases'][0]['entry_ids'], ['0', '1', '2'])
            self.assertEqual(plan['cases'][0]['notes'], 3)
            subprocess.run(cli + ['run', str(root / 'child'), 'D01'],
                           check=True, capture_output=True, text=True)
            child = json.loads((root / 'child/D01/count-2.json').read_text())['panel']['best']
            self.assertEqual(sum(child['section_notes']), 3)
            self.assertTrue(all(0 < n < 3 for n in child['section_notes']))
            parent_path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'child', 'D01')

    def test_cli_unmatched_entries_attach_to_frozen_reciprocal_groups_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            angles = np.array([0, .05, .14, .35, 2, 2.05])
            np.savez(source['input'], vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array(['a' + str(i) for i in range(6)]))
            entries = json.loads(Path(source['entries']).read_text())
            for entry in entries:
                entry['source_group'] = None
            Path(source['entries']).write_text(json.dumps(entries))
            for path in [source['input'], source['entries']]:
                source['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            spec['cases'][0].update(preserve_groups=True, reciprocal_nearest=True, attach_nearest=True)
            spec['cases'].append(dict(spec['cases'][0], id='reciprocal', attach_nearest=False))
            manifest.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prep = subprocess.run(cli + ['prepare', str(manifest), str(root / 'out')],
                                  capture_output=True, text=True)
            self.assertEqual(prep.returncode, 0, prep.stderr)
            plan = json.loads((root / 'out/plan.json').read_text())
            case = plan['cases'][0]
            self.assertEqual(case['groups'], [0, 0, 0, 1, 2, 2])
            self.assertEqual(case['reciprocal_pairs'], [[0, 1], [4, 5]])
            self.assertEqual(case['nearest_attachments'], [[2, 1]])
            self.assertEqual(plan['cases'][2]['groups'], [0, 0, 1, 2, 3, 3])
            subprocess.run(cli + ['run', str(root / 'out'), 'D01'],
                           check=True, capture_output=True, text=True)
            path = root / 'out/D01/count-2.json'
            before = path.read_bytes()
            for trial in json.loads(before)['panel']['trials']:
                self.assertEqual(len(set(trial['labels'][:3])), 1)
                self.assertEqual(trial['labels'][4], trial['labels'][5])
            run(root / 'out', 'D01')
            self.assertEqual(before, path.read_bytes())
            entries[2]['source_group'] = entries[3]['source_group'] = 'existing'
            Path(source['entries']).write_text(json.dumps(entries))
            source['files'][source['entries']] = hashlib.sha256(Path(source['entries']).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(spec))
            grouped = prepare(manifest, root / 'grouped')
            self.assertEqual(grouped['cases'][0]['groups'], [0, 0, 0, 0, 1, 1])
            self.assertEqual(grouped['cases'][0]['nearest_attachments'], [[2, 1]])
            run(root / 'grouped', 'D01')

    def test_attachment_flags_and_singleton_use_frozen_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            case = spec['cases'][0]
            case.update(preserve_groups=True, reciprocal_nearest=True, attach_nearest=True,
                        selector=dict(kind='source_group', value='G2'))
            manifest.write_text(json.dumps(spec))
            plan = prepare(manifest, root / 'singleton')
            self.assertEqual(plan['cases'][0]['groups'], [0])
            self.assertEqual(plan['cases'][0]['nearest_attachments'], [])
            for flag, reciprocal in [('yes', True), (True, False)]:
                case.update(attach_nearest=flag, reciprocal_nearest=reciprocal)
                manifest.write_text(json.dumps(spec))
                with self.assertRaisesRegex(ValueError, 'attach_nearest'):
                    prepare(manifest, root / 'invalid')

    def test_cli_same_title_filter_keeps_original_nearest_and_reciprocal_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            angles = np.array([0, .05, .14, .35, 2, 2.05, 2.14, 2.35])
            np.savez(source['input'], vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array([f'a{i}' for i in range(8)]))
            entries = [dict(id=str(i), note_id=f'a{i}', meaning='fixed meaning',
                            title='CoreB' if i in [4, 5] else 'CoreA', source_group=None)
                       for i in range(8)]
            Path(source['entries']).write_text(json.dumps(entries))
            for path in [source['input'], source['entries']]:
                source['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            case = spec['cases'][0]
            case.update(preserve_groups=True, reciprocal_nearest=True, attach_nearest=True)
            spec['cases'] = [dict(case, id='filtered', attachment_same_title=True),
                             dict(case, id='unchanged')]
            manifest.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prepared = subprocess.run(cli + ['prepare', str(manifest), str(root / 'out')],
                                      capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            filtered, original = json.loads((root / 'out/plan.json').read_text())['cases']
            self.assertEqual(filtered['reciprocal_pairs'], original['reciprocal_pairs'])
            self.assertEqual(filtered['reciprocal_pairs'], [[0, 1], [4, 5]])
            self.assertEqual(original['nearest_attachments'], [[2, 1], [6, 5]])
            self.assertEqual(filtered['nearest_attachments'], [[2, 1]])
            self.assertEqual(filtered['groups'], [0, 0, 0, 1, 2, 2, 3, 4])
            # Row 6's nearest entry has a different title. Do not search for
            # the more distant same-title matched core at rows 0/1.
            completed = subprocess.run(cli + ['run', str(root / 'out'), 'filtered'],
                                       capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            saved = root / 'out/filtered/count-2.json'
            before = saved.read_bytes()
            run(root / 'out', 'filtered')
            self.assertEqual(before, saved.read_bytes())
            entries[2]['title'] = 'corea'
            Path(source['entries']).write_text(json.dumps(entries))
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'out', 'filtered')
            source['files'][source['entries']] = hashlib.sha256(Path(source['entries']).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(spec))
            changed = prepare(manifest, root / 'case-sensitive')
            self.assertEqual(changed['cases'][0]['nearest_attachments'], [])

    def test_same_title_attachment_setting_requires_enabled_one_way_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            cfg = spec['cases'][0]
            cfg.update(preserve_groups=True, reciprocal_nearest=True)
            for same_title, attach in [('yes', True), (True, False)]:
                cfg.update(attachment_same_title=same_title, attach_nearest=attach)
                manifest.write_text(json.dumps(spec))
                with self.assertRaisesRegex(ValueError, 'attachment_same_title'):
                    prepare(manifest, root / 'invalid')

    def test_cli_reciprocal_neighbors_join_whole_existing_groups_before_scoring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            angles = np.array([0, .01, 2, 2.01, 4, 4.01])
            np.savez(source['input'], vectors=np.c_[np.cos(angles), np.sin(angles)],
                     notes=np.array(['a' + str(i) for i in range(6)]))
            entries = json.loads(Path(source['entries']).read_text())
            for i, entry in enumerate(entries):
                entry['source_group'] = 'G1' if i in [0, 2] else None
            Path(source['entries']).write_text(json.dumps(entries))
            for path in [source['input'], source['entries']]:
                source['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            spec['cases'][0].update(preserve_groups=True, reciprocal_nearest=True)
            manifest.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prep = subprocess.run(cli + ['prepare', str(manifest), str(root / 'out')],
                                  capture_output=True, text=True)
            self.assertEqual(prep.returncode, 0, prep.stderr)
            plan = json.loads((root / 'out/plan.json').read_text())
            case = plan['cases'][0]
            self.assertEqual(case['groups'], [0, 0, 0, 0, 1, 1])
            self.assertEqual(case['reciprocal_pairs'], [[0, 1], [2, 3], [4, 5]])
            subprocess.run(cli + ['run', str(root / 'out'), 'D01'],
                           check=True, capture_output=True, text=True)
            path = root / 'out/D01/count-2.json'
            before = path.read_bytes()
            for trial in json.loads(before)['panel']['trials']:
                self.assertEqual(len(set(trial['labels'][:4])), 1)
                self.assertEqual(trial['labels'][4], trial['labels'][5])
            run(root / 'out', 'D01')
            self.assertEqual(before, path.read_bytes())

    def test_reciprocal_ties_singleton_and_invalid_settings_use_preparation_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            np.savez(source['input'], vectors=np.tile([1., 0.], (6, 1)),
                     notes=np.array(['a' + str(i) for i in range(6)]))
            entries = json.loads(Path(source['entries']).read_text())
            for i, entry in enumerate(entries):
                entry['source_group'] = 'only' if i == 0 else None
            Path(source['entries']).write_text(json.dumps(entries))
            for path in [source['input'], source['entries']]:
                source['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            spec['cases'][0].update(preserve_groups=True, reciprocal_nearest=True)
            spec['cases'].append(dict(spec['cases'][0], id='singleton',
                selector=dict(kind='source_group', value='only')))
            manifest.write_text(json.dumps(spec))
            plan = prepare(manifest, root / 'out')
            self.assertEqual(plan['cases'][0]['reciprocal_pairs'], [[0, 1]])
            self.assertEqual(plan['cases'][0]['groups'], [0, 0, 1, 2, 3, 4])
            self.assertEqual(plan['cases'][2]['reciprocal_pairs'], [])
            self.assertEqual(plan['cases'][2]['groups'], [0])
            for flag, preserve in [('yes', True), (True, False)]:
                spec['cases'][0].update(reciprocal_nearest=flag, preserve_groups=preserve)
                manifest.write_text(json.dumps(spec))
                with self.assertRaisesRegex(ValueError, 'reciprocal_nearest'):
                    prepare(manifest, root / 'invalid')

    def test_cli_paired_vectors_freeze_view_and_use_equal_title_meaning_cosine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            source = spec['sources']['examined']
            title = np.repeat(np.eye(2), 3, axis=0)
            meaning = np.tile(np.eye(2), (3, 1))
            notes = np.array(['a' + str(i) for i in range(6)])
            np.savez(source['input'], title=title, meaning=meaning, notes=notes)
            source['files'][source['input']] = hashlib.sha256(Path(source['input']).read_bytes()).hexdigest()
            source['vector_view'] = 'combined'
            manifest.write_text(json.dumps(spec))
            cli = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            result = subprocess.run(cli + ['prepare', str(manifest), str(root / 'out')],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run(cli + ['run', str(root / 'out'), 'D01'],
                           check=True, capture_output=True, text=True)
            saved = json.loads((root / 'out/D01/count-2.json').read_text())
            x = np.concatenate((title, meaning), axis=1) / np.sqrt(2)
            np.testing.assert_allclose(x @ x.T, (title @ title.T + meaning @ meaning.T) / 2)
            for trial in saved['panel']['trials']:
                labels, centers = np.array(trial['labels']), np.array(trial['centers'])
                self.assertEqual(centers.shape, (2, 4))
                self.assertAlmostEqual(trial['objective'],
                    np.clip(1 - np.einsum('ij,ij->i', x, centers[labels]), 0, 2).sum())
            source['vector_view'] = 'unknown'
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'vector view'):
                prepare(manifest, root / 'invalid')
            source['vector_view'] = 'combined'
            title[0] *= 2
            np.savez(source['input'], title=title, meaning=meaning, notes=notes)
            source['files'][source['input']] = hashlib.sha256(Path(source['input']).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'normalized'):
                prepare(manifest, root / 'nonunit')

    def test_native_grouped_case_preserves_original_members_and_ungrouped_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            src = spec['sources']['examined']
            np.savez(src['input'], vectors=np.eye(2)[[0, 1, 0, 1, 1, 1]],
                     notes=np.array(['a' + str(i) for i in range(6)]))
            entries = json.loads(Path(src['entries']).read_text())
            entries[3]['source_group'] = entries[4]['source_group'] = None
            Path(src['entries']).write_text(json.dumps(entries))
            for path in [src['input'], src['entries']]:
                src['files'][path] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            spec['cases'][0]['preserve_groups'] = True
            spec['cases'].append(dict(spec['cases'][0], id='D02', preserve_groups=False))
            manifest.write_text(json.dumps(spec))
            output = root / 'out'
            plan = prepare(manifest, output)
            self.assertEqual(plan['cases'][0]['groups'], [0, 0, 0, 1, 2, 3])
            grouped = run(output, 'D01')
            baseline = run(output, 'D02')
            self.assertGreater(grouped['counts'][1]['objective'], baseline['counts'][1]['objective'])
            path = output / 'D01/count-2.json'
            before = path.read_bytes()
            run(output, 'D01')
            self.assertEqual(path.read_bytes(), before)
            bad = json.loads(before)
            bad['panel'] = json.loads((output / 'D02/count-2.json').read_text())['panel']
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'split an original group'):
                run(output, 'D01')
            spec['counts'] = [1, 2, 3, 4, 5, 6]
            manifest.write_text(json.dumps(spec))
            bounded = prepare(manifest, root / 'bounded')
            self.assertEqual(bounded['cases'][0]['counts'], [1, 2, 3, 4])
            spec['cases'][0]['minimum_notes'] = 1
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'zero note minimum'):
                prepare(manifest, root / 'unsupported')

    def _fixture(self, root):
        sources = {}
        for name, prefix in [('examined', 'a'), ('reserved', 'b')]:
            base = root / name
            base.mkdir()
            np.savez(base / 'input.npz', vectors=np.repeat(np.eye(2), 3, axis=0),
                     notes=np.array([prefix + str(i) for i in range(6)]))
            entries = [dict(id=str(i), note_id=prefix + str(i), title='topic',
                            meaning='fixed meaning', source_group=['G1', 'G1', 'G1', 'G2', 'G3', 'G3'][i])
                       for i in range(6)]
            (base / 'entries.json').write_text(json.dumps(entries))
            (base / 'labels.json').write_text(json.dumps({'best': {'labels': [0, 0, 0, 1, 1, 1]}}))
            sources[name] = {
                'input': str(base / 'input.npz'), 'entries': str(base / 'entries.json'),
                'labels': {'saved': str(base / 'labels.json')},
                'files': {str(base / file): hashlib.sha256((base / file).read_bytes()).hexdigest()
                          for file in ['input.npz', 'entries.json', 'labels.json']}}
        spec = dict(sources=sources, counts=[1, 2], seeds=[10, 11],
                    max_iterations=50, time_limit=30, cases=[
                        dict(id='D01', role='development', source='examined',
                             selector={'kind': 'all'}, minimum_notes=0),
                        dict(id='V01', role='reserved', source='reserved',
                             selector={'kind': 'all'}, minimum_notes=0)])
        manifest = root / 'spec.json'
        manifest.write_text(json.dumps(spec))
        return manifest, spec

    def test_no_split_and_two_children_use_same_inputs_without_running_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            output = root / 'output'
            command = [sys.executable, '-m', 'sse_multivector.section_count_panel']
            prepared = subprocess.run(command + ['prepare', str(manifest), str(output)],
                                      capture_output=True, text=True)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            subprocess.run(command + ['run', str(output), 'D01'], check=True,
                           capture_output=True, text=True)
            summary = json.loads((output / 'D01/summary.json').read_text())
            self.assertEqual(summary['counts'][0]['count'], 1)
            self.assertTrue(summary['counts'][0]['no_split'])
            self.assertIsNone(summary['counts'][0]['valid_refinement'])
            self.assertEqual(summary['counts'][1]['notes_per_child'], [3, 3])
            self.assertTrue(summary['counts'][1]['valid_refinement'])
            self.assertAlmostEqual(summary['counts'][1]['objective'], 0)
            self.assertFalse((output / 'V01').exists())
            before = (output / 'D01/count-2.json').read_bytes()
            subprocess.run(command + ['run', str(output), 'D01'], check=True,
                           capture_output=True, text=True)
            self.assertEqual((output / 'D01/count-2.json').read_bytes(), before)

    def test_saved_label_and_group_selectors_preserve_rows_and_singleton_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            spec['cases'][0]['selector'] = {'kind': 'labels', 'mode': 'saved', 'value': 0}
            spec['cases'].append(dict(id='D02', role='development', source='examined',
                                     selector={'kind': 'source_group', 'value': 'G2'}, minimum_notes=0))
            manifest.write_text(json.dumps(spec))
            plan = prepare(manifest, root / 'out')
            self.assertEqual(plan['cases'][0]['indices'], [0, 1, 2])
            self.assertEqual(plan['cases'][2]['entry_ids'], ['3'])
            self.assertEqual(plan['cases'][2]['counts'], [1])
            result = run(root / 'out', 'D01')
            self.assertEqual(result['counts'][1]['nonempty_children'], 1)
            self.assertFalse(result['counts'][1]['valid_refinement'])
            singleton = run(root / 'out', 'D02')
            self.assertTrue(singleton['counts'][0]['no_split'])

    def test_cross_role_note_overlap_is_rejected_before_preparing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            spec['cases'][1]['source'] = 'examined'
            manifest.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'share original notes'):
                prepare(manifest, root / 'out')
            self.assertFalse((root / 'out').exists())

    def test_changed_source_is_rejected_before_case_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            prepare(manifest, root / 'out')
            Path(spec['sources']['examined']['input']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                run(root / 'out', 'D01')
            self.assertFalse((root / 'out/D01').exists())

    def test_native_exact_reuse_requires_settings_and_original_note_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, spec = self._fixture(root)
            native = root / 'native'
            subprocess.run([sys.executable, '-m', 'sse_multivector.direct_section_partition',
                            spec['sources']['examined']['input'], str(native), '--sections', '2',
                            '--minimum-notes', '0', '--minimum-total-notes', '6',
                            '--starts', '2', '--seed', '10'], check=True,
                           capture_output=True, text=True)
            spec['cases'][0]['reuse'] = {'2': {
                'plan': str(native / 'plan.json'), 'result': str(native / 'unconstrained.json'),
                'mode': 'unconstrained',
                'files': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [native / 'plan.json', native / 'unconstrained.json']}}}
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'out')
            result = run(root / 'out', 'D01')
            self.assertTrue(result['counts'][1]['reused_producer'])
            saved = json.loads((root / 'out/D01/count-2.json').read_text())
            self.assertEqual(saved['panel']['best'],
                             json.loads((native / 'unconstrained.json').read_text())['best'])
            spec['cases'][0]['source'] = 'reserved'
            spec['cases'][1]['source'] = 'examined'
            manifest.write_text(json.dumps(spec))
            prepare(manifest, root / 'wrong')
            with self.assertRaisesRegex(ValueError, 'different original input rows'):
                run(root / 'wrong', 'D01')
            self.assertFalse((root / 'wrong/D01/count-2.json').exists())


if __name__ == '__main__':
    unittest.main()
