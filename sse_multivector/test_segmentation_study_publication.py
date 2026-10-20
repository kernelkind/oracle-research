"""Final segmentation evidence uses the production historical publisher."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .real_note_segmentation import _compile_inputs


class SegmentationStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'source'
        self.output = self.root/'publication'

    def write(self, name, value):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True)+'\n').encode()
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def fixture(self, version='ASv6.23'):
        reviewed = {'schema_version': 1, 'accounting': {'accepted': 2, 'unresolved': 1},
            'provenance': {'encoding_exception': {'semantic_rejection': False,
                'user_response': 'sure', 'unencoded_subject': 'S2'}},
            'notes': [{'note_id': 'a'*64, 'text': 'Tea and coffee.', 'subjects': [
                {'id': 'S1', 'subject': 'Tea', 'context': 'Tea is named.',
                 'judgment': 'accepted', 'fragments': ['Tea'], 'byte_spans': [[0, 3]]},
                {'id': 'S2', 'subject': 'Coffee', 'context': 'Coffee is named.',
                 'judgment': 'unresolved', 'fragments': [], 'byte_spans': []}]},
                {'note_id': 'b'*64, 'text': 'Coffee.', 'subjects': [
                {'id': 'S1', 'subject': 'Coffee', 'context': 'A drink.',
                 'judgment': 'accepted', 'fragments': ['Coffee'], 'byte_spans': [[0, 6]]}]}]}
        inputs = self.write('vectors/reviewed-input.json', reviewed)
        _, mapping = _compile_inputs(reviewed, inputs['sha256'])
        mapping['dimensions'] = 3
        mapped = self.write('vectors/vector-map.json', mapping)
        package = self.write('vectors/subject-package.json', {'version': version, 'model': 'saved/extractor',
            'reasoning_effort': 'low', 'generation': {'model_tools': False}})
        subject_origin = self.write('subject/frozen.json', json.loads((self.source/package['path']).read_text()))
        mask_package = self.write('vectors/mask-package.json', {'version': 'MPv3.5',
            'model': 'saved/mask', 'reasoning_effort': 'low'})
        encoder = self.write('vectors/encoder.json', {'schema_version': 1,
            'checkpoint_path': '/private/checkpoint', 'checkpoint_sha256': '1'*64,
            'worker_path': '/private/worker', 'worker_sha256': '2'*64,
            'base_model_artifact_path': '/private/model', 'base_model_artifact_tree_sha256': '3'*64,
            'container_image': 'sha256:'+'4'*64, 'note_batch_size': 8,
            'model': {'base_model': 'saved/model', 'dimensions': 3,
                      'maximum_tokens': 512, 'pooling': 'selected-contextual-token-mean-linear-relu-linear-v1'}})
        vector_manifest = self.write('vectors/manifest.json', {'schema_version': 1,
            'vector_count': 2, 'dimensions': 3,
            'minimum_normalized_norm': 0.9999999999999998, 'maximum_normalized_norm': 1.0,
            'raw_decode_and_normalization_contract': 'row-major-f32le-to-exact-f64-l2-normalized-f64le-v1',
            'files': {Path(binding['path']).name: {'sha256': binding['sha256'],
                'bytes': (self.source/binding['path']).stat().st_size}
                for binding in (inputs, mapped, package, mask_package, encoder)}})
        ids = [row['vector_id'] for row in mapping['vectors']]
        fine = {'segments': [[ids[0]]], 'unassigned': [ids[1]]}
        manifest = {'schema_version': 4, 'algorithm_version': 'saved-hdbscan',
            'parameters': {'min_samples': 2}, 'vector_count': 2, 'unique_vector_count': 2,
            'source_vector_manifest_sha256': vector_manifest['sha256'],
            'fine_output_sha256': hashlib.sha256(json.dumps(fine, separators=(',', ':')).encode()).hexdigest()}
        response = self.write('baseline/response.json', {'artifact': {'manifest': manifest,
            'result': {'fine_output': fine, 'algorithm_result': {
                'mutual_reachability_distances': ['UNPUBLISHED-WORKING-DATA'],
                'condensed_tree': [{'parent': 2, 'child': 0}],
                'single_linkage_tree': [{'id': 2, 'left': 0, 'right': 1}]},
                'alias_groups': [[0], [1]], 'canonical_unique_ids': ids}}})
        packet = {'packet': 'P1', 'instances': [{'instance': 'V001', 'vector_id': ids[0],
            'note_id': 'a'*64, 'text': 'Tea and coffee.', 'byte_spans': [[0, 3]]}]}
        packets = self.write('baseline/review.json', {'schema_version': 1,
            'review_set': 'review-one', 'packets': [packet]})
        user = self.write('baseline/user.json', {'schema_version': 1,
            'review_set': 'review-one', 'judgments': [{'packet': 'P1', 'verdict': 'uncertain',
                                                    'comment': 'Needs further review.'}]})
        context = self.write('README.md', {'later_user_correction': 'Separate authored record.'})
        return {'authored_context': [context], 'profile': 'segmentation-study', 'datasets': [{'id': 'base',
            'reviewed_input': inputs, 'vector_map': mapped, 'manifest': vector_manifest,
            'encoder': encoder, 'subject_package': package, 'mask_package': mask_package, 'subject_package_origin': subject_origin}], 'runs': [{'id': 'baseline',
            'dataset': 'base', 'response': response, 'full_hierarchy': False,
            'review': packets}], 'records': [], 'user_reviews': [{'source': user,
            'review': packets, 'dataset': 'base', 'run': 'baseline'}]}

    def export(self, selection):
        from .historical_study_publication import export_results
        spec = self.root/'selection.json'
        spec.write_text(json.dumps({'schema_version': 1, 'studies': {'segmentation': selection}}))
        return export_results(self.source, spec, 'segmentation', self.output)

    def rows(self, name):
        return [json.loads(line) for line in (self.output/name).read_text().splitlines()]

    def test_final_memberships_curated_inputs_and_user_review_without_working_arrays(self):
        self.export(self.fixture())
        results = self.rows('results.jsonl')
        run = next(row for row in results if row.get('type') == 'segmentation')
        self.assertEqual(run['run_id'], 'baseline')
        self.assertEqual(len(run['fine_output']['unassigned']), 1)
        self.assertNotIn('hierarchy', run)
        self.assertEqual(self.rows('answers.jsonl'), [])
        vector = next(row for row in self.rows('inputs.jsonl') if row['type'] == 'vector_mapping')
        self.assertNotIn('fragments', vector['data'])
        self.assertNotIn('byte_spans', vector['data'])
        self.assertNotIn('subject', vector['data'])
        self.assertEqual(vector['data']['reviewed_subject_index'], 0)
        packet_set = next(row for row in self.rows('inputs.jsonl') if row['type'] == 'review_set')
        instance = packet_set['data']['packets'][0]['instances'][0]
        self.assertEqual(set(instance), {'instance', 'vector_id'})
        text = '\n'.join(path.read_text() for path in self.output.iterdir())
        self.assertNotIn('UNPUBLISHED-WORKING-DATA', text)
        self.assertNotIn('/private/', text)
        self.assertIn('"semantic_rejection":false', text)
        self.assertIn('"judgment":"unresolved"', text)
        user = next(row for row in self.rows('judgments.jsonl') if row.get('actor') == 'user')
        self.assertEqual(user['verdict'], 'uncertain')
        self.assertEqual(user['comment'], 'Needs further review.')
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['authored_context']['sources'][0]['path'], 'README.md')
        self.assertIn('original saved states', metadata['authored_context']['status'])
        self.assertEqual(metadata['subject_provenance']['versions'], ['ASv6.23'])
        self.assertTrue(metadata['subject_provenance']['generated_subjects_deprecated'])
        dataset = next(row for row in self.rows('inputs.jsonl') if row['type'] == 'input_dataset')
        self.assertEqual(dataset['mask_prompt_version'], 'MPv3.5')
        self.assertEqual(dataset['upstream_package_origins']['subject']['path'], 'subject/frozen.json')
        self.assertEqual(dataset['subject_package']['model'], 'saved/extractor')
        self.assertFalse(dataset['subject_package']['generation']['model_tools'])
        self.assertEqual(dataset['mask_package']['reasoning_effort'], 'low')
        self.assertEqual(dataset['vector_manifest']['minimum_normalized_norm'], 0.9999999999999998)

    def test_any_old_subject_source_marks_mixed_selection_deprecated(self):
        selection = self.fixture(version='ASv6.100')
        first = selection['datasets'][0]
        second = {**first, 'id': 'other'}
        package = self.write('other/subject-package.json', {'version': 'ASv6.23'})
        manifest = json.loads((self.source/first['manifest']['path']).read_text())
        manifest['files']['subject-package.json'] = {'sha256': package['sha256'],
            'bytes': (self.source/package['path']).stat().st_size}
        second.update(subject_package=package, subject_package_origin=package,
                      manifest=self.write('other/manifest.json', manifest))
        selection['datasets'].append(second)
        self.export(selection)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertTrue(metadata['subject_provenance']['generated_subjects_deprecated'])
        self.assertEqual(len([r for r in self.rows('inputs.jsonl') if r['type'] == 'reviewed_note']), 2)

    def test_unproven_subject_lineage_remains_unknown(self):
        self.export(self.fixture(version='unknown'))
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertIsNone(metadata['subject_provenance']['generated_subjects_deprecated'])

    def test_saved_assessment_binds_its_exact_original_review_packet(self):
        selection = self.fixture()
        review = selection['runs'][0]['review']
        wrong = self.write('assistant.json', {'review_set': 'review-one',
            'source_review_sha256': '0'*64, 'assessments': [
                {'packet': 'P1', 'verdict': 'valid', 'reason': 'Same subject.'}]})
        selection['records'] = [{**wrong, 'role': 'assistant_review',
            'review': review, 'dataset': 'base', 'run': 'baseline'}]
        with self.assertRaisesRegex(ValueError, 'assessment review-source hash differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())
        value = json.loads((self.source/wrong['path']).read_text())
        value['source_review_sha256'] = review['sha256']
        value['assessments'][0]['packet'] = 'UNKNOWN'
        wrong = self.write('assistant.json', value)
        selection['records'][0].update(wrong)
        with self.assertRaisesRegex(ValueError, 'unknown review packet'):
            self.export(selection)
        self.assertFalse(self.output.exists())
        value['assessments'][0]['packet'] = 'P1'
        selection['records'][0].update(self.write('assistant.json', value))
        self.export(selection)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['counts']['reviewed_notes'], 2)

    def test_explicit_final_hierarchy_and_review_source_checks(self):
        selection = self.fixture()
        selection['runs'][0]['full_hierarchy'] = True
        self.export(selection)
        run = next(row for row in self.rows('results.jsonl') if row.get('type') == 'segmentation')
        self.assertEqual(run['hierarchy']['single_linkage_tree'], [{'id': 2, 'left': 0, 'right': 1}])
        self.output = self.root/'bad-review'
        review = json.loads((self.source/'baseline/review.json').read_text())
        review['packets'][0]['instances'][0]['text'] = 'Different source text.'
        changed = self.write('baseline/review.json', review)
        selection['runs'][0]['review'] = changed
        selection['user_reviews'][0]['review'] = changed
        with self.assertRaisesRegex(ValueError, 'source text/identity differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
