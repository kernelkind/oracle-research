"""Post-run TRUE12 analysis tests; no model or real experiment analysis."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_true_mask_membership import fixture
import true_mask_membership as runner
import true_mask_membership_analysis as analysis


def cases():
    original, reviewed, graph, old = fixture()
    for index, fragments, spans in ((0, ['Coffee'], [[0, 6]]),
                                    (1, ['Coffee'], [[0, 6]]),
                                    (3, ['tea'], [[11, 14]]),
                                    (4, ['Coffee and'], [[0, 10]])):
        original['vectors'][index].update(fragments=fragments, byte_spans=spans)
    inputs, baseline = runner.prepare_inputs(original, reviewed, graph, old)
    scores = copy.deepcopy(inputs)
    for row in scores:
        native = (row['premise'] in ('tea', 'Coffee and', 'Unrelated food')
                  if row['category_id'] == 'coffee' else
                  True if row['premise'] == 'Unrelated food' else None)
        row.update(predicted=native, entailment_score=0.01 if native is True else 0.9,
            generated_text='1' if native is True else '0' if native is False else 'unknown',
            generated_token_ids=[0, 209, 1] if native is True else [0, 3, 632, 1],
            eos_terminated=True)
    review = dict(experiment='TRUE12', phase='before TRUE12 inference',
        categories=[dict(title='Coffee', positive_ids=['V001', 'V005'],
            uncertain=[dict(ids=['V008'], reason='Reserved boundary')]),
            dict(title='Tea as a beverage', positive_ids=['V007'],
            uncertain=[dict(ids=['V003'], reason='Reserved ingredient boundary')])])
    return original, reviewed, graph, old, inputs, baseline, scores, review


class TRUEMaskMembershipAnalysisTests(unittest.TestCase):
    def test_review_complement_and_native_masks_are_complete_with_uncertain_separate(self):
        original, reviewed, _, _, inputs, baseline, scores, review = cases()
        before = copy.deepcopy((inputs, baseline, scores, review))
        summary, memberships, details = analysis.compare(inputs, scores, baseline, review, reviewed)
        self.assertEqual((inputs, baseline, scores, review), before)
        self.assertEqual(len(details['masks']), 1890)
        coffee = summary['categories'][0]
        self.assertEqual(coffee['mask_counts']['positive'], dict(yes=1, no=1, unresolved=0, total=2))
        self.assertEqual(coffee['mask_counts']['uncertain']['total'], 1)
        self.assertEqual(coffee['mask_counts']['negative']['total'], 942)
        self.assertEqual(coffee['clear_positive_masks_missed'], ['V001'])
        self.assertIn('V004', coffee['clear_negative_masks_accepted'])
        self.assertEqual(coffee['uncertain_mask_ids'], ['V008'])
        uncertain = next(row for row in details['masks']
                         if row['category_id'] == 'tea' and row['mask_id'] == 'V003')
        self.assertEqual(uncertain['expected'], 'uncertain')
        self.assertEqual(uncertain['review_reason'], 'Reserved ingredient boundary')
        self.assertEqual(uncertain['note_text'], 'Unrelated food.')
        self.assertEqual(uncertain['fragments'], ['Unrelated food'])
        self.assertIs(uncertain['predicted'], True)
        self.assertLess(uncertain['entailment_score'], 0.142)

    def test_note_or_distinguishes_good_from_only_incorrect_evidence_and_false_additions(self):
        _, reviewed, _, _, inputs, baseline, scores, review = cases()
        summary, memberships, _ = analysis.compare(inputs, scores, baseline, review, reviewed)
        coffee = summary['categories'][0]
        self.assertEqual(coffee['baseline_recursive_note_count'], 1)
        self.assertEqual(coffee['accepted_note_count'], 3)
        self.assertEqual(coffee['expected_addition_note_ids'], ['note-b'])
        self.assertEqual(coffee['expected_additions_recovered'], ['note-b'])
        self.assertEqual(coffee['clear_negative_note_additions'], ['note-c'])
        note_a, note_b, note_c = memberships['nodes'][0]['notes']
        self.assertEqual(note_a['expected'], 'positive')
        self.assertEqual(note_a['accepted_positive_mask_ids'], [])
        self.assertEqual(note_a['accepted_negative_mask_ids'], ['V004'])
        self.assertEqual(note_a['evidence'], 'only-negative')
        self.assertEqual(note_b['accepted_positive_mask_ids'], ['V005'])
        self.assertEqual(note_b['evidence'], 'positive')
        self.assertEqual(note_c['expected'], 'negative')
        tea = summary['categories'][1]
        self.assertIn('note-a', tea['clear_positive_notes_missed'])
        self.assertIn('note-a', tea['unresolved_note_ids'])
        self.assertEqual(tea['uncertain_note_ids'], ['note-c'])
        self.assertEqual(tea['uncertain_note_additions'], ['note-c'])

    def test_missing_duplicate_or_changed_inputs_aliases_and_native_verdicts_fail(self):
        mutations = [lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows[0]['masks'].pop(),
            lambda rows: rows[0].update(model_input='changed'),
            lambda rows: rows[0]['masks'][0].update(fragments=['changed']),
            lambda rows: rows[0].update(predicted=1),
            lambda rows: rows[0].update(entailment_score=float('nan')),
            lambda rows: rows[0].update(predicted=True, generated_text='0'),
            lambda rows: rows[0].update(threshold_predicted=False)]
        for mutate in mutations:
            _, reviewed, _, _, inputs, baseline, scores, review = cases()
            mutate(scores)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                analysis.compare(inputs, scores, baseline, review, reviewed)

    def test_review_unknown_overlapping_duplicate_ids_and_changed_titles_fail(self):
        mutations = [lambda r: r['categories'][0]['positive_ids'].append('V999'),
            lambda r: r['categories'][0]['positive_ids'].append('V001'),
            lambda r: r['categories'][0]['uncertain'][0]['ids'].append('V001'),
            lambda r: r['categories'][0].update(title='Coffee '),
            lambda r: r['categories'][0]['uncertain'][0].update(reason='')]
        for mutate in mutations:
            _, reviewed, _, _, inputs, baseline, scores, review = cases()
            mutate(review)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                analysis.compare(inputs, scores, baseline, review, reviewed)

    def make_run(self, root):
        original, reviewed, graph, old, inputs, baseline, scores, review = cases()
        paths = {}
        for name, data in zip(runner.DATA_PATHS, (original, reviewed, graph, old)):
            paths[name] = root / name
            paths[name].write_text(json.dumps(data))
        output = root / 'TRUE12'
        runner.freeze_inputs(paths, output)
        review['source_vector_map_sha256'] = runner.sha256(output / 'data/vector-map.json')
        (output / 'semantic-review-before-inference.json').write_text(json.dumps(review))
        (output / 'scores.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in scores))
        (output / 'first-token-logits.npy').write_bytes(b'opaque saved logits; analysis hashes only')
        config = dict(experiment='TRUE12', model_id=runner.MODEL_ID, revision=runner.REVISION,
                      dtype='float32', device='cpu', threads=4, batch_size=4,
                      max_input_tokens=512, truncation=False)
        (output / 'config.json').write_text(json.dumps(config))
        (output / 'model-files.json').write_text('{}')
        (output / 'completion.json').write_text(json.dumps(dict(pairs=len(scores),
            scores_sha256=runner.sha256(output / 'scores.jsonl'),
            logits_sha256=runner.sha256(output / 'first-token-logits.npy'))))
        return output, runner.sha256(output / 'semantic-review-before-inference.json')

    def test_files_require_complete_unchanged_run_and_explicit_frozen_review_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            output, review_hash = self.make_run(Path(temp))
            for name in ('inputs.json', 'baseline.json', 'data/vector-map.json',
                         'source/true_mask_inference.py', 'scores.jsonl',
                         'first-token-logits.npy', 'semantic-review-before-inference.json'):
                path = output / name
                saved = path.read_bytes()
                path.write_bytes(saved + b' ')
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'changed'):
                    analysis.analyze_run(output, review_hash)
                self.assertFalse((output / 'analysis.json').exists())
                path.write_bytes(saved)
            with self.assertRaisesRegex(ValueError, 'review.*changed'):
                analysis.analyze_run(output, '0' * 64)
            (output / 'completion.json').unlink()
            with self.assertRaises(FileNotFoundError):
                analysis.analyze_run(output, review_hash)

    def test_output_is_exclusive_complete_and_records_review_and_artifact_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            output, review_hash = self.make_run(Path(temp))
            analysis.analyze_run(output, review_hash)
            manifest = json.loads((output / 'analysis-manifest.json').read_text())
            self.assertEqual(manifest['semantic_review_sha256'], review_hash)
            for name in ('analysis.json', 'memberships.json', 'comparison-details.json'):
                self.assertEqual(manifest['output_sha256'][name], runner.sha256(output / name))
            self.assertIn('scores.jsonl', manifest['input_sha256'])
            self.assertIn('true_mask_membership_analysis.py', manifest['analysis_source_sha256'])
            details = json.loads((output / 'comparison-details.json').read_text())
            self.assertEqual(len(details['masks']), 1890)
            with self.assertRaises(FileExistsError):
                analysis.analyze_run(output, review_hash)


if __name__ == '__main__':
    unittest.main()
