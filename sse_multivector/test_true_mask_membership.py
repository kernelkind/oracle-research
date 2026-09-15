"""TRUE12 production-path tests, without loading the checkpoint."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import true_category_probe
import true_mask_inference
import true_mask_membership as probe


def fixture():
    texts = {'note-a': 'Coffee and tea.', 'note-b': 'Coffee and tea.',
             'note-c': 'Unrelated food.'}
    reviewed = {'notes': [dict(note_id=key, text=value) for key, value in texts.items()]}
    vectors = []
    for index in range(945):
        note = ('note-a', 'note-b', 'note-c')[index % 3]
        fragments = ['Coffee', 'tea'] if note != 'note-c' else ['Unrelated food']
        spans = [[0, 6], [11, 14]] if note != 'note-c' else [[0, 14]]
        vectors.append(dict(short_id=f'V{index+1:03d}', vector_id=f'vector-{index}',
            note_id=note, note_short_id=note, fragments=fragments, byte_spans=spans,
            judgment='accepted', reviewed_subject={'provenance': {'source_sha256': 'abc'}}))
    original = dict(vector_count=945, vectors=vectors, notes=[
        dict(note_id=key, text_sha256=hashlib.sha256(value.encode()).hexdigest())
        for key, value in texts.items()])
    graph = {'nodes': [dict(group='coffee', title='Coffee'),
                       dict(group='tea', title='Tea as a beverage')]}
    baseline = {'nodes': [dict(**node, own_note_ids=['note-a'],
        recursive_note_ids=['note-a']) for node in graph['nodes']]}
    return original, reviewed, graph, baseline


class TRUEMaskMembershipTests(unittest.TestCase):
    def test_exact_plain_source_fragments_deduplicated_with_all_mask_provenance(self):
        data = fixture()
        before = copy.deepcopy(data)
        rows, baseline = probe.prepare_inputs(*data)
        self.assertEqual(data, before)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(len(row['masks']) for row in rows), 1890)
        for group, title in (('coffee', 'Coffee'), ('tea', 'Tea as a beverage')):
            selected = [row for row in rows if row['category_id'] == group]
            self.assertEqual({mask['short_id'] for row in selected for mask in row['masks']},
                             {f'V{i:03d}' for i in range(1, 946)})
            row = next(row for row in selected if row['premise'] == 'Coffee tea')
            self.assertEqual(row['model_input'],
                f'premise: Coffee tea hypothesis: This text is about {title}.')
            self.assertEqual(len(row['masks']), 630)
            self.assertEqual(row['masks'][0]['reviewed_subject'],
                             data[0]['vectors'][0]['reviewed_subject'])
            self.assertNotIn('text', row['masks'][0])
            self.assertNotIn('threshold', row)
        self.assertEqual(baseline['nodes'][0]['recursive_note_ids'], ['note-a'])

    def test_source_byte_mismatch_order_missing_mask_and_changed_title_rejected(self):
        mutations = [
            lambda d: d[0]['vectors'][0].update(fragments=['Coffee', 'bad']),
            lambda d: d[0]['vectors'][0].update(byte_spans=[[11, 14], [0, 6]],
                                               fragments=['tea', 'Coffee']),
            lambda d: d[0]['vectors'].pop(),
            lambda d: d[0]['vectors'][1].update(short_id='V001'),
            lambda d: d[2]['nodes'][0].update(title='Coffee '),
            lambda d: d[3]['nodes'][0].update(title='Coffee drinks'),
            lambda d: d[1]['notes'][0].update(text='Edited source note'),
        ]
        for mutate in mutations:
            data = fixture()
            mutate(data)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                probe.prepare_inputs(*data)

    def test_one_added_space_does_not_strip_or_rewrite_source_whitespace(self):
        data = fixture()
        data[0]['vectors'][0].update(fragments=['Coffee ', 'tea.'], byte_spans=[[0, 7], [11, 15]])
        rows, _ = probe.prepare_inputs(*data)
        self.assertEqual(rows[0]['model_input'],
            'premise: Coffee  tea. hypothesis: This text is about Coffee.')

    def test_freeze_copies_source_bytes_baseline_and_executable_sources_exclusively(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = {}
            for name, data in zip(('vector-map.json', 'reviewed-input.json',
                                   'native-graph.json', 'native-notes.json'), fixture()):
                path = root / name
                path.write_text(json.dumps(data))
                paths[name] = path
            output = root / 'TRUE12'
            probe.freeze_inputs(paths, output)
            frozen = probe.load_frozen_inputs(output)
            self.assertEqual(len(frozen), 4)
            manifest = json.loads((output / 'started.json').read_text())
            self.assertEqual(manifest['mask_category_pairs'], 1890)
            self.assertEqual(manifest['unique_inputs'], 4)
            self.assertNotIn('threshold', manifest)
            for name, path in paths.items():
                self.assertEqual((output / 'data' / name).read_bytes(), path.read_bytes())
                self.assertEqual(manifest['data_sha256'][name], probe.sha256(path))
            self.assertEqual((output / 'source' / 'true_mask_membership.py').read_bytes(),
                             Path(probe.__file__).read_bytes())
            self.assertIn('hierarcaps_category_probe.py', manifest['source_sha256'])
            with self.assertRaises(FileExistsError):
                probe.freeze_inputs(paths, output)
            (output / 'inputs.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, 'changed'):
                probe.load_frozen_inputs(output)

    def test_memberships_or_all_masks_keep_alias_notes_and_label_only_additions(self):
        rows, baseline = probe.prepare_inputs(*fixture())
        for row in rows:
            row.update(predicted=(row['category_id'] == 'coffee'), entailment_score=0.01)
        # A No mask cannot cancel a Yes mask from the same note.
        extra = copy.deepcopy(rows[0])
        extra.update(id='extra', predicted=False)
        extra['masks'] = [dict(extra['masks'][0], short_id='extra-mask')]
        result = probe.derive_note_memberships(rows + [extra], baseline)
        coffee = next(node for node in result['nodes'] if node['group'] == 'coffee')
        tea = next(node for node in result['nodes'] if node['group'] == 'tea')
        self.assertEqual(coffee['accepted_note_ids'], ['note-a', 'note-b', 'note-c'])
        self.assertEqual(coffee['added_note_ids'], ['note-b', 'note-c'])
        self.assertEqual(tea['accepted_note_ids'], [])
        self.assertEqual(tea['missing_baseline_note_ids'], ['note-a'])
        self.assertNotIn('false_positive', result)
        note_b = next(note for note in coffee['notes'] if note['note_id'] == 'note-b')
        self.assertEqual(len(note_b['accepted_mask_ids']), 315)
        self.assertIs(note_b['predicted'], True)

    def test_unresolved_is_not_no_and_threshold_is_only_explicit_and_strict(self):
        rows, baseline = probe.prepare_inputs(*fixture())
        for row in rows:
            row.update(predicted=None, entailment_score=0.142)
        native = probe.derive_note_memberships(rows, baseline)
        self.assertTrue(all(note['predicted'] is None
            for node in native['nodes'] for note in node['notes']))
        cutoff = probe.derive_note_memberships(rows, baseline, threshold=0.142)
        self.assertTrue(all(note['predicted'] is False
            for node in cutoff['nodes'] for note in node['notes']))
        for threshold in (float('nan'), -1, 2):
            with self.assertRaises(ValueError):
                probe.derive_note_memberships(rows, baseline, threshold=threshold)

    def test_scores_only_reporting_never_applies_containment_cutoff_or_writes_report(self):
        self.assertIs(true_mask_inference.score_generation, true_category_probe.score_generation)
        logits = [0.0] * 300
        logits[209] = 0.01
        row = true_mask_inference.score_generation(
            logits, '1', [0, 209, 1], {'0': [3, 632], '1': [209]})
        self.assertIs(row['predicted'], True)
        self.assertLess(row['entailment_score'], 0.142)
        self.assertNotIn('threshold_predicted', row)
        module = ast.parse(Path(true_mask_inference.__file__).read_text())
        constants = [node.value for node in ast.walk(module) if isinstance(node, ast.Constant)]
        names = {node.id for node in ast.walk(module) if isinstance(node, ast.Name)}
        self.assertNotIn(0.142, constants)
        self.assertNotIn('threshold_predicted', constants)
        self.assertNotIn('DECISIONS.md', constants)
        self.assertNotIn('analysis.json', constants)
        self.assertTrue({'summarize', 'render_decisions', 'threshold_decision'}.isdisjoint(names))

    def test_infer_uses_isolated_native_engine_and_batch_four(self):
        with patch.object(probe, 'load_frozen_inputs', return_value=[{'id': 'row'}]), \
                patch.object(probe, 'validate_snapshot', return_value=Path('/model')), \
                patch.object(true_mask_inference, 'run_inference') as infer:
            probe.infer(Path('/output'), Path('/snapshot'))
        args, kwargs = infer.call_args
        self.assertEqual(args[:4], (Path('/model'), [{'id': 'row'}], Path('/output'), 4))
        self.assertEqual(kwargs, {})


if __name__ == '__main__':
    unittest.main()
