"""Final saved runtime and classifier measurements use the common publisher."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest


class PerformanceStudyPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root/'source'
        self.output = self.root/'publication'

    def write(self, name, value):
        path = self.source/name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(value, ensure_ascii=False)+'\n').encode()
        path.write_bytes(raw)
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def export(self, selection):
        from .historical_study_publication import export_results
        specification = self.root/'selection.json'
        specification.write_text(json.dumps({'schema_version': 1, 'studies': {'performance': selection}}))
        return export_results(self.source, specification, 'performance', self.output)

    def rows(self, name):
        return [json.loads(line) for line in (self.output/name).read_text().splitlines()]

    def runtime_fixture(self):
        source = self.write('equivalence.json', {
            'rows': [{'threads': 2, 'binary_wall_seconds': 1.5, 'allowed_cpus': [0, 1],
                'observed_busy_numerical_threads': 2,
                'thread_cpu_ticks': {'12345': 11, '12346': 9}, 'actual_provider_attempts': 0}],
            'one_vs_24_output_byte_identical': True, 'same_output_as_v1': True,
            'wall_reduction_percent': 50., 'timing_qualification': 'Descriptive timing only.'})
        return {'profile': 'performance-study', 'kind': 'numerical-runtime-equivalence',
            'reports': [{'id': 'replay', **source}],
            'limitations': ['Exact request/executable bindings are not present in the tiny report.']}

    def learning_fixture(self):
        reports = []
        for condition in ['sequential', 'concurrent']:
            source = self.write(condition+'/report.json', {'schema_version': 1,
                'binding': {'config_sha256': '1'*64, 'data_sha256': '2'*64,
                            'manifest_sha256': '3'*64, 'code_sha256': '4'*64},
                'config': {'model': 'saved/model', 'epochs': [1], 'batch_size': 1},
                'data': {'code_sha256': {'/home/private/runtime/fitter.py': '4'*64},
                         'application_allowed': False, 'excluded': 4,
                         'semantic_status': 'Provisional targets, not semantic gold.'},
                'training_pid': 12345, 'verification_pid': 12346, 'complete': True,
                'training_finished': True, 'updates': 1, 'training_examples_seen': 1,
                'supervised_class_decisions': 1, 'zero_loss_updates': 0,
                'architecture': 'encoder', 'method': 'full', 'input_format': 'input_json',
                'workload': 'Relation-only development learning.',
                'baseline': {'cases': 1, 'teacher_agreement': 0.,
                    'per_label': {'uncertain': {'support': 0, 'precision': None}},
                    'decisions': [{'case_id': 'C1', 'relation': 'neither',
                                   'target': 'equivalent', 'identity_control': True}]},
                'checkpoints': [{'epoch': 1, 'path': '/private/checkpoint',
                    'hashes': {'weights.safetensors': '5'*64}, 'mean_epoch_loss': .25,
                    'elapsed_training_seconds': 2.5, 'peak_cuda_allocated_bytes': 1024,
                    'reload_matches': True, 'evaluation': {'cases': 1,
                        'decisions': [{'case_id': 'C1', 'relation': 'equivalent',
                                      'target': 'equivalent', 'identity_control': True}]}}]})
            reports.append({'id': condition, **source})
        summary = self.write('summary.json', {'schema_version': 1,
            'sequential_pair_seconds': 3., 'concurrent_pair_seconds': 2.,
            'saved_seconds': 1., 'saved_percent': 100/3,
            'runs': {row['id']: {'report_sha256': row['sha256'], 'training_pid': 12345}
                     for row in reports}, 'limits': ['One uncontrolled pair only.']})
        return {'profile': 'performance-study', 'kind': 'learning-concurrency',
            'reports': reports, 'summary': summary,
            'reused_inputs': [{'role': 'evaluation', 'publication': 'prompts/previous',
                              'records': 1, 'input_status': 'Already selected teacher population.'}],
            'limitations': ['Exact admitted TRAIN subset and frozen fitter location remain unresolved.']}

    def test_saved_equivalence_and_thread_work_keep_measurements_without_process_ids(self):
        self.export(self.runtime_fixture())
        row = self.rows('results.jsonl')[0]
        self.assertEqual(row['data']['rows'][0]['thread_cpu_ticks'], [11, 9])
        self.assertEqual(row['data']['rows'][0]['actual_provider_attempts'], 0)
        self.assertTrue(row['data']['one_vs_24_output_byte_identical'])
        self.assertEqual(self.rows('answers.jsonl'), [])
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertIn('Exact request', metadata['limitations'][0])

    def test_final_classifier_predictions_methods_and_comparison_are_preserved(self):
        self.export(self.learning_fixture())
        rows = self.rows('results.jsonl')
        self.assertEqual(len(rows), 3)
        result = rows[0]['data']
        self.assertEqual(result['data']['code_sha256'], {'fitter.py': '4'*64})
        self.assertEqual(result['baseline']['per_label']['uncertain']['support'], 0)
        self.assertFalse(result['data']['application_allowed'])
        self.assertEqual(result['checkpoints'][0]['evaluation']['decisions'][0]['target'], 'equivalent')
        self.assertTrue(result['checkpoints'][0]['reload_matches'])
        self.assertEqual(self.rows('inputs.jsonl')[0]['publication'], 'prompts/previous')
        self.assertEqual(self.rows('answers.jsonl'), [])
        published = ''.join(path.read_text() for path in self.output.iterdir())
        self.assertNotIn('/home/private', published)
        self.assertNotIn('/private/checkpoint', published)
        self.assertNotIn('training_pid', published)
        self.assertNotIn('verification_pid', published)
        metadata = json.loads((self.output/'experiment.json').read_text())
        self.assertEqual(metadata['counts']['learning_conditions'], 2)
        self.assertIn('remain unresolved', metadata['limitations'][0])

    def test_summary_must_bind_every_condition_to_its_exact_saved_report(self):
        selection = self.learning_fixture()
        value = json.loads((self.source/'summary.json').read_text())
        value['runs']['concurrent']['report_sha256'] = '0'*64
        selection['summary'] = self.write('summary.json', value)
        with self.assertRaisesRegex(ValueError, 'summary/report source binding differs'):
            self.export(selection)
        self.assertFalse(self.output.exists())

    def test_final_source_hash_and_validation_equivalence_reports_keep_exact_science(self):
        measurements = [
            ('numerical-equivalence', {'source_hash_updates': [
                {'source': 'algorithm.rs', 'before': '1'*64, 'after': '2'*64, 'occurrences': 1},
                {'source': 'partition.rs', 'before': '3'*64, 'after': '4'*64, 'occurrences': 1}],
                'all_other_output_bytes_identical': True,
                'expected_sha256': '5'*64, 'actual_sha256': '5'*64}),
            ('validation-equivalence', {'same_audit_content_except_paths_and_source_hashes': True,
                'fresh_teacher_attempts': 0, 'cpu_budget': 24, 'source_binding_seconds': 102.1,
                'audit_seconds': 95.4, 'historical_serial_audit_seconds': 514.1,
                'timing_qualification': 'Different caches; descriptive only.'}),
        ]
        for kind, value in measurements:
            self.output = self.root/kind
            source = self.write(kind+'.json', value)
            self.export({'profile': 'performance-study', 'kind': kind,
                         'reports': [{'id': kind, **source}]})
            self.assertEqual(self.rows('results.jsonl')[0]['data'], value)


if __name__ == '__main__':
    unittest.main()
