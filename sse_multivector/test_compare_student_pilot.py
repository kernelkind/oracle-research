"""Exercise reviewed Compare target preparation through the native workflows."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import test_compare_student_inputs as inputs
from sse_multivector import test_bootstrap_student_inputs as bootstrap_inputs


class CompareStudentPilotTests(unittest.TestCase):
    setUp = inputs.CompareStudentInputTests.setUp
    write = inputs.CompareStudentInputTests.write
    cli = inputs.CompareStudentInputTests.cli
    prepare = inputs.CompareStudentInputTests.prepare
    show = inputs.CompareStudentInputTests.show
    calls = inputs.CompareStudentInputTests.calls
    selection = inputs.CompareStudentInputTests.selection

    def teachers(self):
        selection = inputs.CompareStudentInputTests.source(self)
        for role in ('train', 'evaluation'):
            selection['role'] = role
            self.write('compare-'+role+'-selection.json', selection)
            spec = json.loads((self.root/'compare-spec.json').read_text())
            spec['dataset']['path'] = 'compare-'+role+'-selection.json'
            self.write('compare-'+role+'-spec.json', spec)
            name = 'compare-'+role
            self.cli('prepare', name, '--spec', self.root/('compare-'+role+'-spec.json'))
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(dict(
                meaning='Plants', relation='equivalent', reason='Fixture same fixed meanings.'))})
            for case in self.show(name)['cases']:
                self.cli('review', name, '--case', case['id'], '--role', 'agent',
                         '--verdict', 'accept', '--comment', 'Provisional fixture assessment.')

    def collect(self):
        self.cli('collect', 'compare-train', 'compare-evaluation', '--output', 'collected')

    def pilot(self, ok=True):
        env = dict(os.environ, EXPERIMENT_RUNNER_ROOT=os.environ.get('EXPERIMENT_RUNNER_ROOT',
            str(Path(__file__).resolve().parents[2]/'experiment-runner')))
        result = subprocess.run([sys.executable, '-m', 'sse_multivector.compare_student_pilot',
            'prepare', '--collection', str(self.root/'collected/compare.json'),
            '--provenance', str(self.root/'collected/provenance.json'),
            '--output', str(self.root/'pilot')], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_prepare_preserves_complete_inputs_and_relation_only_targets_without_inference(self):
        self.teachers()
        self.collect()
        before = self.log.read_bytes()
        self.pilot()
        data = json.loads((self.root/'pilot/data.json').read_text())
        self.assertEqual([len(data[r]) for r in ('train', 'evaluation')], [3, 3])
        for role in ('train', 'evaluation'):
            teachers = {c['id']: c for c in self.show('compare-'+role)['cases']}
            for row in data[role]:
                self.assertEqual(row['target'], 'equivalent')
                self.assertIn(teachers[row['case_id']]['inputs']['INPUT_JSON'], row['state'])
                self.assertNotIn('Fixture same fixed meanings.', row['state'])
                self.assertEqual(row['evidence'], teachers[row['case_id']]['evidence'])
        manifest = json.loads((self.root/'pilot/manifest.json').read_text())
        self.assertFalse(manifest['all_five_labels'])
        self.assertFalse(manifest['canonical_branches'])
        self.assertIn('Provisional', manifest['semantic_status'])
        self.assertEqual(self.log.read_bytes(), before)

    def test_current_human_rejection_excludes_entire_reciprocal_family(self):
        self.teachers()
        pair = self.show('compare-train')['cases'][1]
        self.cli('review', 'compare-train', '--case', pair['id'], '--role', 'user',
                 '--verdict', 'reject', '--comment', 'Fixture human rejects this target.')
        self.cli('review', 'compare-train', '--case', pair['id'], '--role', 'agent',
                 '--verdict', 'accept', '--comment', 'Cannot override human rejection.')
        self.collect()
        self.pilot()
        data = json.loads((self.root/'pilot/data.json').read_text())
        self.assertEqual(len(data['train']), 1)
        self.assertEqual(len(data['excluded']), 2)

    def test_native_producer_receipt_must_match_collection(self):
        self.teachers()
        self.collect()
        path = self.root/'collected/compare.json'
        value = json.loads(path.read_text())
        value['cases'][0]['receipt']['record_sha256'] = '0'*64
        path.write_text(json.dumps(value))
        error = self.pilot(ok=False)
        self.assertIn('producer provenance', error.stderr)
        self.assertFalse((self.root/'pilot').exists())

    def test_changed_target_cannot_be_resealed_into_reviewed_supervision(self):
        self.teachers()
        self.collect()
        self.pilot()
        from hashlib import sha256
        path = self.root/'pilot/data.json'
        data = json.loads(path.read_text())
        data['train'][0]['target'] = 'neither'
        path.write_text(json.dumps(data))
        manifest = self.root/'pilot/manifest.json'
        value = json.loads(manifest.read_text())
        value['data_sha256'] = sha256(path.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(value))
        config = dict(model='must-not-be-loaded', revision='a'*40,
            max_length=256, epochs=[1], batch_size=1, learning_rate=.001,
            seed=17, memory_budget_gib=8, reserve_gib=8)
        from sse_multivector.compare_student_pilot import LABELS
        self.write('native.json', dict(model=config['model'], revision=config['revision'],
            kind='causal_lm', readout='options', quantization='nf4', max_input_tokens=256,
            memory_budget_gib=8, reserve_gib=8, question=dict(instructions='Compare fixed meanings.',
                criteria={label: label for label in LABELS}, output_field='relation')))
        for settings in (config, dict(config, local_model_config='native.json'),
                         dict(config, input_format='input_json')):
            with self.subTest(native='local_model_config' in settings):
                self.write('fit-config.json', settings)
                result = subprocess.run([sys.executable, '-m', 'sse_multivector.compare_student_pilot',
                    'train', '--config', str(self.root/'fit-config.json'), '--data', str(self.root/'pilot'),
                    '--output', str(self.root/'fit'), '--stage', 'train'], text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('targets differ from reviewed teacher collection', result.stderr)
                self.assertFalse((self.root/'fit').exists())


class CompareCheckpointEvaluationTests(CompareStudentPilotTests):
    def evaluation_sources(self, bootstrap_id='Hierarchy-bootstrap-v96'):
        """Produce every teacher/input receipt through the shared native CLI."""
        selection, posts = bootstrap_inputs.BootstrapStudentInputTests.source(self)
        self.prompt.write_text('GENERIC PROMPT: define the selected topic.\n{INPUT_JSON}')
        spec = json.loads(self.spec.read_text())
        spec['prompt']['id'] = bootstrap_id
        self.write('spec.json', spec)
        self.prepare('bootstrap-train')
        selection['role'] = 'evaluation'
        self.write('evaluation-selection.json', selection)
        spec['dataset']['path'] = 'evaluation-selection.json'
        self.write('evaluation-spec.json', spec)
        self.cli('prepare', 'bootstrap-evaluation', '--spec', self.root/'evaluation-spec.json')
        answer = dict(meaning='Plants', ambiguities=[], resolutions=[], evidence=[])
        for role in ('train', 'evaluation'):
            name = 'bootstrap-'+role
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
            for case in self.show(name)['cases']:
                self.cli('review', name, '--case', case['id'], '--role', 'agent',
                         '--verdict', 'accept', '--comment', 'Provisional fixture meaning.')
        selection = self.selection()
        compare_prompt = self.root/'compare-prompt.txt'
        compare_prompt.write_text('GENERIC PROMPT: compare the exact fixed meanings.\n{INPUT_JSON}')
        for role in ('train', 'evaluation'):
            selection['role'] = role
            self.write('compare-'+role+'-selection.json', selection)
            spec = json.loads((self.root/'compare-spec.json').read_text())
            spec['prompt'] = dict(id='Hierarchy-compare-v48', path=str(compare_prompt))
            spec['dataset']['path'] = 'compare-'+role+'-selection.json'
            self.write('compare-'+role+'-spec.json', spec)
            self.cli('prepare', 'compare-'+role, '--spec', self.root/('compare-'+role+'-spec.json'))
            self.cli('run', 'compare-'+role, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(dict(
                meaning='Plants', relation='equivalent', reason='Provisional fixture same meanings.'))})
            for case in self.show('compare-'+role)['cases']:
                self.cli('review', 'compare-'+role, '--case', case['id'], '--role', 'agent',
                         '--verdict', 'accept', '--comment', 'Provisional fixture relation.')
        self.collect()
        self.pilot()
        return posts

    def evaluation_cli(self, *extra, ok=True, experiment='compare-evaluation', output='evaluation-data'):
        command = [sys.executable, '-m', 'sse_multivector.compare_student_pilot',
            'prepare-evaluation', '--experiment', str(self.root/experiment),
            '--training-data', str(self.root/'pilot'), '--bootstrap-prompt', str(self.prompt),
            '--output', str(self.root/output), *map(str, extra)]
        result = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_evaluation_preparation_reuses_frozen_inputs_without_answers_or_inference(self):
        self.evaluation_sources()
        before = self.log.read_bytes()
        self.evaluation_cli()
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        source = self.show('compare-evaluation')['cases']
        self.assertEqual([r['case_id'] for r in data['evaluation']], [r['id'] for r in source])
        for row, original in zip(data['evaluation'], source):
            self.assertEqual(row['input_json'], original['inputs']['INPUT_JSON'])
            self.assertEqual(row['state'], original['prompt'])
            self.assertEqual(row['evidence'], original['evidence'])
            self.assertIsNone(row['target'])
        self.assertEqual(sum(r['identity_control'] for r in data['evaluation']), 1)
        self.assertEqual(self.log.read_bytes(), before)

    def test_optional_teacher_diagnostics_keep_unreviewed_answers_provisional(self):
        self.evaluation_sources()
        self.cli('prepare', 'diagnostic-teacher', '--from', self.root/'compare-evaluation', '--repeat')
        self.cli('run', 'diagnostic-teacher', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(dict(
            meaning='Plants', relation='equivalent', reason='Unreviewed fixture teacher.'))})
        self.evaluation_cli('--teacher-experiment', self.root/'diagnostic-teacher')
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        for row in data['evaluation']:
            self.assertEqual(row['target'], 'equivalent')
            self.assertEqual(row['teacher']['reviews'], [])
            self.assertIn('Unreviewed fixture teacher.', row['teacher']['output'])
        manifest = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        self.assertTrue(manifest['teacher_answers'])
        self.assertIn('Provisional teacher agreement', manifest['semantic_status'])

    def evaluation_fit_fixture(self):
        """Metadata-only fixture for guards that must fire before a model load."""
        from sse_multivector.distillation_run import file_hashes, sha256
        config = dict(model='must-not-be-loaded', revision='a'*40, max_length=256,
            epochs=[1], batch_size=1, learning_rate=.001, seed=17, memory_budget_gib=8, reserve_gib=8)
        self.write('fit-config.json', config)
        (self.root/'fit/checkpoints/epoch-1').mkdir(parents=True)
        self.write('fit/checkpoints/epoch-1/fixture.json', dict(non_model_payload=True))
        manifest = json.loads((self.root/'pilot/manifest.json').read_text())
        binding = dict(config_sha256=sha256(self.root/'fit-config.json'), data_sha256=manifest['data_sha256'],
            manifest_sha256=sha256(self.root/'pilot/manifest.json'), code_sha256=sha256(Path(__file__).with_name('compare_student_pilot.py')))
        report = dict(config=config, binding=binding, complete=True, training_finished=True, checkpoints=[dict(
            epoch=1, path='checkpoints/epoch-1', reload_matches=True,
            hashes=file_hashes(self.root/'fit/checkpoints/epoch-1'))])
        self.write('fit/report.json', report)
        return report

    def evaluate_cli(self, *extra, ok=False):
        result = subprocess.run([sys.executable, '-m', 'sse_multivector.compare_student_pilot', 'evaluate',
            '--config', str(self.root/'fit-config.json'), '--training-data', str(self.root/'pilot'),
            '--fit', str(self.root/'fit'), '--data', str(self.root/'evaluation-data'),
            '--output', str(self.root/'evaluated'), '--epochs', '1', *map(str, extra)],
            text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_unverified_fit_and_changed_checkpoint_are_refused_before_loading(self):
        self.evaluation_sources()
        self.evaluation_cli()
        report = self.evaluation_fit_fixture()
        report['complete'] = False
        self.write('fit/report.json', report)
        failure = self.evaluate_cli()
        self.assertIn('unchanged verified original training', failure.stderr)
        report['complete'] = True
        self.write('fit/report.json', report)
        self.write('fit/checkpoints/epoch-1/fixture.json', dict(changed=True))
        failure = self.evaluate_cli()
        self.assertIn('saved hashes differ', failure.stderr)
        self.assertFalse((self.root/'evaluated').exists())

    def test_resealed_evaluation_target_is_rederived_before_loading(self):
        self.evaluation_sources()
        self.evaluation_cli()
        self.evaluation_fit_fixture()
        from sse_multivector.distillation_run import sha256
        path = self.root/'evaluation-data/data.json'
        data = json.loads(path.read_text())
        data['evaluation'][0]['target'] = 'neither'
        self.write('evaluation-data/data.json', data)
        manifest = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        manifest['data_sha256'] = sha256(path)
        self.write('evaluation-data/manifest.json', manifest)
        failure = self.evaluate_cli()
        self.assertIn('prepared evaluation differs from native inputs and teacher evidence', failure.stderr)
        self.assertFalse((self.root/'evaluated').exists())

    def test_teacher_rejection_and_conflicting_reviews_remain_diagnostic_evidence(self):
        self.evaluation_sources()
        self.cli('prepare', 'diagnostic-teacher', '--from', self.root/'compare-evaluation', '--repeat')
        self.cli('run', 'diagnostic-teacher', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(dict(
            meaning='Plants', relation='equivalent', reason='Disputed fixture teacher.'))})
        first = self.show('diagnostic-teacher')['cases'][0]['id']
        for role, verdict in [('user', 'reject'), ('agent', 'accept')]:
            self.cli('review', 'diagnostic-teacher', '--case', first, '--role', role,
                     '--verdict', verdict, '--comment', 'Keep this diagnostic disagreement.')
        self.evaluation_cli('--teacher-experiment', self.root/'diagnostic-teacher')
        row = json.loads((self.root/'evaluation-data/data.json').read_text())['evaluation'][0]
        self.assertEqual(row['target'], 'equivalent')
        self.assertEqual({r['verdict'] for r in row['teacher']['reviews']}, {'reject', 'accept'})

    def test_preparation_rejects_original_training_exposure(self):
        self.evaluation_sources()
        failure = self.evaluation_cli(experiment='compare-train', ok=False)
        self.assertIn('training note/author/content exposure', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())

    def test_preparation_rejects_other_bootstrap_and_compare_versions(self):
        self.evaluation_sources(bootstrap_id='Hierarchy-bootstrap-v95')
        failure = self.evaluation_cli(ok=False)
        self.assertIn('Bootstrap-v96 producer provenance', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())
        self.cli('prepare', 'other-version', '--from', self.root/'compare-evaluation',
                 '--prompt', self.root/'compare-prompt.txt',
                 '--prompt-id', 'Hierarchy-compare-v49')
        failure = self.evaluation_cli(experiment='other-version', ok=False)
        self.assertIn('exact Compare-v48', failure.stderr)

    def branch_experiment(self, *, omit_descendant_proof=False, extra_proof=False):
        original = self.show('compare-evaluation')['cases'][0]
        payload = json.loads(original['inputs']['INPUT_JSON'])
        meanings = {r['id']: r for r in self.show('bootstrap-evaluation')['cases']}
        evidence = {k:v for k,v in original['evidence'].items()
                    if k not in ('source_bootstrap', 'source_provenance')}
        def proof(source):
            row = meanings[source['case_id']]
            return dict(experiment=str(self.root/'bootstrap-evaluation'), case=row['id'], receipt=row['receipt'])
        evidence['local_meaning_from'] = proof(evidence['local'])
        canonical = payload['canonical']
        parent = dict(id='parent', subject='Plants', meaning='Plants', parents=[])
        child = dict(id='child', subject='Plants', meaning='Plants', parents=[canonical['id']])
        canonical.update(parents=['parent'], ancestors=[parent], descendants=[child])
        reference = proof(evidence['canonical'])
        evidence['canonical_meaning_from'] = {n['id']: reference for n in [canonical, parent, child]
            if not omit_descendant_proof or n['id'] != 'child'}
        if extra_proof:
            evidence['canonical_meaning_from']['unused-state-node'] = reference
        evidence['review'] = dict(source_role='synthetic_incompatible_diagnostic_fixture')
        case = dict(id='full-branch', inputs=dict(INPUT_JSON=json.dumps(payload)), evidence=evidence)
        self.write('branch-inputs.json', dict(cases=[case]))
        spec = json.loads((self.root/'compare-evaluation-spec.json').read_text())
        spec['dataset'] = dict(adapter='generic', path='branch-inputs.json')
        self.write('branch-spec.json', spec)
        self.cli('prepare', 'branch', '--spec', self.root/'branch-spec.json')
        return case

    def test_complete_branches_preserve_producer_and_synthetic_fixture_evidence(self):
        self.evaluation_sources()
        case = self.branch_experiment()
        self.evaluation_cli(experiment='branch')
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        self.assertEqual(data['evaluation'][0]['input_json'], case['inputs']['INPUT_JSON'])
        self.assertEqual(data['evaluation'][0]['evidence'], case['evidence'])
        self.assertTrue(data['evaluation'][0]['identity_control'])

    def test_unused_graph_producer_evidence_is_preserved_without_becoming_input(self):
        self.evaluation_sources()
        case = self.branch_experiment(extra_proof=True)
        self.evaluation_cli(experiment='branch')
        row = json.loads((self.root/'evaluation-data/data.json').read_text())['evaluation'][0]
        self.assertEqual(row['evidence'], case['evidence'])
        self.assertNotIn('unused-state-node', row['input_json'])

    def test_changed_bootstrap_snapshot_cannot_be_used_for_fitted_train_meanings(self):
        self.evaluation_sources()
        other = self.root/'different-bootstrap.txt'
        other.write_text('Another Bootstrap-v96 snapshot.\n{INPUT_JSON}')
        failure = self.evaluation_cli('--bootstrap-prompt', other, ok=False)
        self.assertIn('exact Bootstrap-v96 producer instructions', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())

    def test_historical_fit_code_is_checked_separately_from_new_evaluation_code(self):
        self.evaluation_sources()
        from sse_multivector.distillation_run import sha256
        frozen = self.root/'frozen-original-fit.py'
        frozen.write_text('"""Distinct immutable original fit implementation fixture."""\n')
        manifest = json.loads((self.root/'pilot/manifest.json').read_text())
        manifest['code_sha256'] = {str(frozen):sha256(frozen)}
        self.write('pilot/manifest.json', manifest)
        self.evaluation_cli()
        report = self.evaluation_fit_fixture()
        report['binding']['code_sha256'] = sha256(frozen)
        self.write('fit/report.json', report)
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        data['evaluation'][0]['target'] = 'neither'
        self.write('evaluation-data/data.json', data)
        evaluation_manifest = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        evaluation_manifest['data_sha256'] = sha256(self.root/'evaluation-data/data.json')
        self.write('evaluation-data/manifest.json', evaluation_manifest)
        failure = self.evaluate_cli()
        self.assertIn('prepared evaluation differs from native inputs and teacher evidence', failure.stderr)
        frozen.write_text('Changed immutable original fit implementation.\n')
        failure = self.evaluate_cli()
        self.assertIn('frozen preparation code differs', failure.stderr)

    def test_historical_mutable_fitter_requires_exact_read_only_source_relocation(self):
        self.evaluation_sources()
        from sse_multivector.distillation_run import sha256
        declared = self.root/'old-runtime/compare_student_pilot.py'
        snapshot = self.root/'immutable-fit/compare_student_pilot.py'
        old_source = '"""Historical fitted implementation fixture."""\n'
        declared.parent.mkdir()
        snapshot.parent.mkdir()
        declared.write_text(old_source)
        snapshot.write_text(old_source)
        original_sha = sha256(snapshot)
        manifest = json.loads((self.root/'pilot/manifest.json').read_text())
        manifest['code_sha256'] = {str(declared):original_sha}
        self.write('pilot/manifest.json', manifest)
        declared.write_text('"""New implementation now occupies the historical path."""\n')
        original_manifest = (self.root/'pilot/manifest.json').read_bytes()
        failure = self.evaluation_cli(ok=False)
        self.assertIn('frozen preparation code differs', failure.stderr)
        self.evaluation_cli('--fit-code', snapshot)
        prepared = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        self.assertEqual(prepared['fitter_code'], dict(declared_path=str(declared),
            path=str(snapshot), sha256=original_sha))
        self.assertEqual((self.root/'pilot/manifest.json').read_bytes(), original_manifest)
        report = self.evaluation_fit_fixture()
        report['binding']['code_sha256'] = original_sha
        self.write('fit/report.json', report)
        self.write('fit/checkpoints/epoch-1/fixture.json', dict(changed=True))
        failure = self.evaluate_cli('--fit-code', snapshot)
        self.assertIn('saved hashes differ', failure.stderr)
        snapshot.write_text('"""Wrong fitted implementation."""\n')
        failure = self.evaluation_cli('--fit-code', snapshot, output='wrong-snapshot', ok=False)
        self.assertIn('relocated fitter code differs', failure.stderr)
        self.assertFalse((self.root/'wrong-snapshot').exists())

    def test_portable_evaluation_refuses_resealed_targets_against_external_manifest_sha(self):
        self.evaluation_sources()
        self.evaluation_cli()
        self.evaluation_fit_fixture()
        from sse_multivector.distillation_run import sha256
        frozen_sha = sha256(self.root/'evaluation-data/manifest.json')
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        data['evaluation'][0]['target'] = 'neither'
        self.write('evaluation-data/data.json', data)
        manifest = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        manifest['data_sha256'] = sha256(self.root/'evaluation-data/data.json')
        self.write('evaluation-data/manifest.json', manifest)
        failure = self.evaluate_cli('--evaluation-manifest-sha256', frozen_sha)
        self.assertIn('externally bound evaluation manifest differs', failure.stderr)
        self.assertFalse((self.root/'evaluated').exists())

    def external_experiment(self, note_id, name='external', *, extra_note_id=None):
        source = self.show('bootstrap-evaluation')['cases'][0]
        payload = json.loads(source['inputs']['INPUT_JSON'])
        corpus = self.write(name+'-corpus.json', dict(schema_version=1, notes=[dict(
            note_id=note_id, pubkey='external-author', text=payload['local']['post'],
            provenance=dict(source_split='evaluation'))]))
        identity = dict(note_id=note_id, number=source['evidence']['local']['number'])
        cases = [dict(id='external-meaning', inputs=source['inputs'],
            evidence=dict(local=identity, corpus=str(corpus)))]
        if extra_note_id is not None:
            cases.append(dict(id='unreferenced-meaning', inputs=source['inputs'], evidence=dict(
                local=dict(note_id=extra_note_id, number=identity['number']), corpus=str(corpus))))
        self.write(name+'-meanings-inputs.json', dict(cases=cases))
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='generic', path=name+'-meanings-inputs.json')
        self.write(name+'-meanings-spec.json', spec)
        producer = name+'-meanings'
        self.cli('prepare', producer, '--spec', self.root/(name+'-meanings-spec.json'))
        self.cli('run', producer, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(dict(
            meaning='Plants', ambiguities=[], resolutions=[], evidence=[]))})
        receipt = self.show(producer)['cases'][0]['receipt']
        reference = dict(experiment=str(self.root/producer), case='external-meaning', receipt=receipt)
        original = self.show('compare-evaluation')['cases'][0]
        inputs = json.loads(original['inputs']['INPUT_JSON'])
        evidence = dict(local=identity, canonical=identity, local_meaning_from=reference,
            canonical_meaning_from={inputs['canonical']['id']:reference},
            review=dict(source_role='external_diagnostic'))
        self.write(name+'-inputs.json', dict(cases=[dict(id='external-case',
            inputs=original['inputs'], evidence=evidence)]))
        spec = json.loads((self.root/'compare-evaluation-spec.json').read_text())
        spec['dataset'] = dict(adapter='generic', path=name+'-inputs.json')
        self.write(name+'-spec.json', spec)
        self.cli('prepare', name, '--spec', self.root/(name+'-spec.json'))
        return corpus

    def original_roster(self):
        return self.write('original-roster.json', dict(schema_version=2, tasks={'subjects':'ASv6.100'},
            train_note_ids=[f'{i:064x}' for i in range(1,1001)],
            evaluation_note_ids=[f'{i:064x}' for i in range(1001,1101)],
            test_note_ids=[f'{i:064x}' for i in range(1101,1301)]))

    def test_original_roster_allows_external_evaluation_partition_diagnostics(self):
        self.evaluation_sources()
        corpus = self.external_experiment('f'*64)
        original = corpus.read_bytes()
        failure = self.evaluation_cli(experiment='external', ok=False)
        self.assertIn('explicit TRAIN/learning population evidence', failure.stderr)
        roster = self.original_roster()
        self.evaluation_cli('--split-manifest', roster, experiment='external')
        data = json.loads((self.root/'evaluation-data/data.json').read_text())
        self.assertTrue(all(producer['source_role'] == 'external_diagnostic' and
            producer['source_population'] == 'evaluation' for producer in data['evaluation'][0]['producers']))
        manifest = json.loads((self.root/'evaluation-data/manifest.json').read_text())
        self.assertIn(str(roster), manifest['sources'])
        self.assertEqual(corpus.read_bytes(), original)

    def test_original_roster_rejects_validation_and_reserved_test_producers(self):
        self.evaluation_sources()
        roster = self.original_roster()
        for name, ordinal in [('original-validation',1001), ('reserved-test',1101)]:
            self.external_experiment(f'{ordinal:064x}', name)
            failure = self.evaluation_cli('--split-manifest', roster, experiment=name,
                output=name+'-data', ok=False)
            self.assertIn('original validation/final-test producer is reserved', failure.stderr)
            self.assertFalse((self.root/(name+'-data')).exists())

    def test_mixed_bootstrap_producer_is_refused_before_whole_experiment_answers(self):
        self.evaluation_sources()
        roster = self.original_roster()
        self.external_experiment('f'*64, extra_note_id=f'{1001:064x}')
        failure = self.evaluation_cli('--split-manifest', roster, experiment='external', ok=False)
        self.assertIn('original validation/final-test producer is reserved', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())

    def test_collected_identity_evidence_must_match_native_bootstrap_producer(self):
        self.evaluation_sources()
        from sse_multivector.distillation_run import sha256
        case = self.show('compare-evaluation')['cases'][0]
        ref = case['evidence']['source_bootstrap']
        path = self.root/ref['path']
        bundle = json.loads(path.read_text())
        identity = case['evidence']['local']
        saved = next(row for row in bundle['cases'] if (row['experiment'], row['case_id']) ==
            (identity['experiment'], identity['case_id']))
        saved['evidence']['pubkey'] = 'forged-author'
        forged = self.write('forged-bootstrap.json', bundle)
        case['evidence']['source_bootstrap'] = dict(path=str(forged), sha256=sha256(forged))
        self.write('forged-inputs.json', dict(cases=[{key:case[key] for key in ('id','inputs','evidence')}]))
        spec = json.loads((self.root/'compare-evaluation-spec.json').read_text())
        spec['dataset'] = dict(adapter='generic', path='forged-inputs.json')
        self.write('forged-spec.json', spec)
        self.cli('prepare', 'forged', '--spec', self.root/'forged-spec.json')
        failure = self.evaluation_cli(experiment='forged', ok=False)
        self.assertIn('Bootstrap collection evidence differs from native producer', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())

    def test_unqualified_teacher_plan_is_rejected_before_reading_its_ledger(self):
        self.evaluation_sources()
        self.cli('prepare', 'wrong-teacher', '--from', self.root/'compare-evaluation',
            '--prompt', self.root/'compare-prompt.txt', '--prompt-id', 'Hierarchy-compare-v49')
        (self.root/'wrong-teacher/run/results.jsonl').write_text('unqualified ledger must not be read\n')
        failure = self.evaluation_cli('--teacher-experiment', self.root/'wrong-teacher', ok=False)
        self.assertIn('teacher diagnostics differ from frozen Compare-v48 cases', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())

    def test_reserved_input_producer_is_rejected_before_compare_teacher_answers(self):
        self.evaluation_sources()
        roster = self.original_roster()
        self.external_experiment(f'{1001:064x}')
        (self.root/'external/run/results.jsonl').write_text('unqualified ledger must not be read\n')
        failure = self.evaluation_cli('--split-manifest', roster,
            '--teacher-experiment', self.root/'external', experiment='external', ok=False)
        self.assertIn('original validation/final-test producer is reserved', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())
        self.assertFalse((self.root/'evaluated').exists())

    def test_incomplete_branch_producer_provenance_is_refused(self):
        self.evaluation_sources()
        self.branch_experiment(omit_descendant_proof=True)
        failure = self.evaluation_cli(experiment='branch', ok=False)
        self.assertIn('every canonical ancestor/descendant requires Bootstrap-v96 provenance', failure.stderr)
        self.assertFalse((self.root/'evaluation-data').exists())


@unittest.skipUnless(os.environ.get('RUN_COMPARE_PILOT_GPU_TESTS') == '1', 'explicit CUDA integration run')
class CompareCheckpointEvaluationGPUIntegrationTests(CompareCheckpointEvaluationTests):
    def test_saved_encoder_option_and_pointer_evaluate_native_branches_without_training(self):
        import torch
        from tokenizers import Tokenizer, models, pre_tokenizers
        from tokenizers.pre_tokenizers import ByteLevel
        from transformers import (ModernBertConfig, ModernBertForSequenceClassification,
            PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM, Qwen2Model, Qwen2Tokenizer)
        from sse_multivector import compare_student_pilot as pilot
        from sse_multivector.distillation_run import file_hashes, read_json, sha256, subject_training_model
        from sse_multivector.local_weight_model import LocalWeights, choice_prompt
        from peft import PeftModel, prepare_model_for_kbit_training
        self.evaluation_sources()
        case = self.branch_experiment()
        self.evaluation_cli(experiment='branch')
        row = read_json(self.root/'evaluation-data/data.json')['evaluation'][0]
        # Train and verify through an older, differently hashed module;
        # retain its exact snapshot after new source occupies the original path.
        from shutil import copytree
        frozen_runtime = self.root/'frozen-fit-runtime'
        package = frozen_runtime/'sse_multivector'
        package.mkdir(parents=True)
        source_package = Path(pilot.__file__).parent
        (package/'__init__.py').write_text('__path__.append('+repr(str(source_package))+')\n')
        frozen_code = package/'compare_student_pilot.py'
        frozen_code.write_text(Path(pilot.__file__).read_text()+'\n# Immutable prior fit implementation fixture.\n')
        original_source = frozen_code.read_bytes()
        fitter_snapshot = self.root/'immutable-original-fitter.py'
        fitter_snapshot.write_bytes(original_source)
        training_path = self.root/'frozen-training-data'
        copytree(self.root/'pilot', training_path)
        manifest = read_json(training_path/'manifest.json')
        manifest['code_sha256'] = {str(frozen_code):sha256(frozen_code)}
        self.write('frozen-training-data/manifest.json', manifest)
        fit_environment = dict(os.environ, PYTHONPATH=str(frozen_runtime)+os.pathsep+str(source_package.parent))
        evaluation_environment = dict(os.environ, PYTHONPATH=str(source_package.parent))
        pointer_source = read_json(Path(__file__).parent/'distillation/compare-relation-only-kev27b-default-v1.json')
        sys.path.insert(0, pointer_source['upstream_path'])
        from kev.model import PointerHead, SPECIAL
        for kind in ('encoder', 'encoder_input_json', 'causal_lm', 'pointer'):
            with self.subTest(kind=kind):
                torch.manual_seed(17)
                base = self.root/('base-'+kind)
                if kind.startswith('encoder'):
                    backend = Tokenizer(models.WordLevel({'<pad>':0, '<unk>':1, 'Plants':2}, unk_token='<unk>'))
                    backend.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
                    tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, pad_token='<pad>', unk_token='<unk>')
                    model = ModernBertForSequenceClassification(ModernBertConfig(vocab_size=3, hidden_size=32,
                        intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
                        max_position_embeddings=4096, num_labels=5, pad_token_id=0,
                        bos_token_id=2, eos_token_id=2, cls_token_id=2, sep_token_id=2))
                else:
                    model_config = Qwen2Config(vocab_size=512, hidden_size=32, intermediate_size=64,
                        num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
                        max_position_embeddings=4096)
                    model = (Qwen2Model if kind == 'pointer' else Qwen2ForCausalLM)(model_config)
                    words = ['[UNK]', '[PAD]', *sorted(ByteLevel.alphabet())]
                    tokenizer = Qwen2Tokenizer(vocab=dict(zip(words, range(len(words)))), merges=[],
                        unk_token='[UNK]', pad_token='[PAD]', additional_special_tokens=SPECIAL)
                    tokenizer.chat_template = ('{% for message in messages %}{{message["content"]}}'
                        '{% endfor %}{% if add_generation_prompt %}\nassistant\n{% endif %}')
                model.save_pretrained(base)
                tokenizer.save_pretrained(base)
                del model
                config = dict(model=str(base), revision='a'*40, max_length=4096, epochs=[1,4], batch_size=1,
                    learning_rate=.001, seed=17, memory_budget_gib=8, reserve_gib=8)
                native_path = self.root/('native-'+kind+'.json')
                if kind == 'encoder_input_json':
                    config['input_format'] = 'input_json'
                if kind in ('causal_lm', 'pointer'):
                    question = dict(instructions='Compare the fixed meanings.',
                        criteria={label:label for label in reversed(pilot.LABELS)}, output_field='relation')
                    native = dict(pointer_source, model=str(base), revision='a'*40, kind=kind,
                        quantization='nf4', max_input_tokens=4096, memory_budget_gib=8, reserve_gib=8,
                        question=question, readout='options')
                    if kind == 'causal_lm':
                        native['answer_prefix'] = 'Answer: ('
                    else:
                        head = PointerHead(32, 16)
                        torch.save(dict(base='tiny-foundation', base_revision='a'*40, weights='full',
                            head=head.state_dict(), head_dim=16, temperature=1.3), base/'head.pt')
                        native.update(base_model='tiny-foundation', base_revision='a'*40)
                    self.write(native_path.name, native)
                    config['local_model_config'] = native_path.name
                config_path = self.write('fit-config-'+kind+'.json', config)
                fit = self.root/('fit-'+kind)
                fit_command = [sys.executable, '-P', '-m', 'sse_multivector.compare_student_pilot', 'train',
                    '--config', str(config_path), '--data', str(training_path), '--output', str(fit)]
                for stage in ('train', 'verify'):
                    result = subprocess.run(fit_command+['--stage', stage], env=fit_environment,
                        text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                frozen_code.write_bytes(Path(pilot.__file__).read_bytes())
                evaluation_path = self.root/('relocated-evaluation-'+kind)
                self.evaluation_cli('--training-data', training_path, '--fit-code', fitter_snapshot,
                    experiment='branch', output=evaluation_path.name)
                before = file_hashes(fit)
                output = self.root/('evaluated-'+kind)
                command = [sys.executable, '-P', '-m', 'sse_multivector.compare_student_pilot', 'evaluate',
                    '--config', str(config_path), '--training-data', str(training_path), '--fit', str(fit),
                    '--data', str(evaluation_path), '--output', str(output), '--epochs', '1', '4',
                    '--fit-code', str(fitter_snapshot), '--evaluation-manifest-sha256',
                    sha256(evaluation_path/'manifest.json')]
                # The native Anvil preparation is frozen; its owner input tree
                # is deliberately unavailable to portable checkpoint execution.
                owner_panel = self.root/'branch'
                parked_panel = self.root/'branch-not-mounted'
                owner_panel.rename(parked_panel)
                result = subprocess.run(command, env=evaluation_environment, text=True, capture_output=True)
                parked_panel.rename(owner_panel)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = read_json(output/'report.json')
                self.assertTrue(report['complete'])
                self.assertEqual(report['binding']['original_fit_binding']['code_sha256'], sha256(fitter_snapshot))
                self.assertEqual(report['data']['fitter_code'], dict(declared_path=str(frozen_code),
                    path=str(fitter_snapshot), sha256=sha256(fitter_snapshot)))
                self.assertEqual(report['binding']['code_sha256'], sha256(pilot.__file__))
                self.assertNotEqual(report['binding']['code_sha256'],
                                    report['binding']['original_fit_binding']['code_sha256'])
                self.assertEqual(report['updates'], 0)
                self.assertEqual(report['binding']['caller_evaluation_manifest_sha256'],
                                 sha256(evaluation_path/'manifest.json'))
                self.assertIn('validated on Anvil', report['evaluation_source_verification'])
                self.assertEqual(report['training_examples_seen'], 0)
                self.assertEqual([r['epoch'] for r in report['checkpoints']], [1,4])
                self.assertEqual(file_hashes(fit), before)
                checkpoint = fit/'checkpoints/epoch-4'
                with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                    if kind.startswith('encoder'):
                        model = ModernBertForSequenceClassification.from_pretrained(checkpoint,
                            dtype=torch.float32, attn_implementation='sdpa').cuda().eval()
                        state = row['input_json'] if kind == 'encoder_input_json' else row['state']
                        tokens = tokenizer(state, return_tensors='pt', truncation=False)
                        logits = model(**{k:v.cuda() for k,v in tokens.items() if k != 'token_type_ids'}).logits
                        expected = pilot.LABELS[logits.argmax().item()]
                    elif kind == 'causal_lm':
                        model = subject_training_model(dict(native, device='cuda', max_length=4096,
                            efficient_attention=True, lora_target_modules='all-linear', lora_rank=16,
                            lora_alpha=32, gradient_checkpointing=True), checkpoint).eval()
                        prompt = tokenizer.apply_chat_template([dict(role='user', content=choice_prompt(
                            row['state'], question, 'options'))], add_generation_prompt=True,
                            enable_thinking=False, tokenize=False)+native['answer_prefix']
                        tokens = tokenizer(prompt, add_special_tokens=False, return_tensors='pt')
                        ids = [tokenizer.encode(code, add_special_tokens=False)[0] for code in 'ABCDE']
                        logits = model(**{k:v.cuda() for k,v in tokens.items()}, use_cache=False,
                            logits_to_keep=1).logits[:, -1, ids].float()
                        expected = list(question['criteria'])[logits.argmax().item()]
                    else:
                        pointer = LocalWeights(native_path)
                        backbone = prepare_model_for_kbit_training(pointer.model, use_gradient_checkpointing=True)
                        pointer.model = PeftModel.from_pretrained(backbone, checkpoint, is_trainable=False).eval()
                        saved = torch.load(checkpoint/'head.pt', map_location='cpu', weights_only=True)
                        self.assertEqual(saved['source_config_sha256'], sha256(native_path))
                        pointer.head.load_state_dict(saved['head'], strict=True)
                        pointer.head.temperature = saved['temperature']
                        pointer.head.eval()
                        keys = list(question['criteria'])
                        encoded = pointer.encoder(tokenizer, dict(state=row['state'], questions=[dict(
                            instr=question['instructions'], options=[f'{key}: {question["criteria"][key]}'
                                for key in keys], label=0)]), max_state=4096, max_branch=4096, strict=True)
                        expected = keys[pointer.pointer_logits(encoded).argmax().item()]
                        del pointer, backbone
                    if kind != 'pointer':
                        self.assertTrue(all(p.grad is None for p in model.parameters()))
                        del model
                decision = report['checkpoints'][-1]['evaluation']['decisions'][0]
                self.assertEqual(decision['relation'], expected)
                self.assertEqual(decision['evidence'], case['evidence'])
                self.assertIsNone(report['checkpoints'][-1]['evaluation']['teacher_agreement'])
                self.assertEqual(file_hashes(fit), before)
                torch.cuda.empty_cache()

                # A complete, source-bound synthetic branch input must be refused
                # before loading a model when it exceeds the original recipe cap.
                long_case = json.loads(json.dumps(case))
                payload = json.loads(long_case['inputs']['INPUT_JSON'])
                payload['canonical']['ancestors'][0]['subject'] = 'Plants '*5000
                long_case['inputs']['INPUT_JSON'] = json.dumps(payload)
                self.write('long-inputs-'+kind+'.json', dict(cases=[long_case]))
                spec = read_json(self.root/'branch-spec.json')
                spec['dataset']['path'] = 'long-inputs-'+kind+'.json'
                self.write('long-spec-'+kind+'.json', spec)
                self.cli('prepare', 'long-'+kind, '--spec', self.root/('long-spec-'+kind+'.json'))
                self.evaluation_cli('--training-data', training_path, '--fit-code', fitter_snapshot,
                    experiment='long-'+kind, output='long-data-'+kind)
                long_command = list(command)
                long_command[long_command.index('--data')+1] = str(self.root/('long-data-'+kind))
                long_command[long_command.index('--output')+1] = str(self.root/('long-evaluated-'+kind))
                long_command[long_command.index('--evaluation-manifest-sha256')+1] = sha256(
                    self.root/('long-data-'+kind)/'manifest.json')
                result = subprocess.run(long_command, env=evaluation_environment, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(result.stderr, 'exceeds configured maximum|exceeds.*limit|overlength|too long|state exceeds 4096 tokens')
                self.assertFalse((self.root/('long-evaluated-'+kind)).exists())
                frozen_code.write_bytes(original_source)


@unittest.skipUnless(os.environ.get('RUN_COMPARE_PILOT_GPU_TESTS') == '1', 'explicit CUDA integration run')
class CompareStudentPilotGPUIntegrationTests(unittest.TestCase):
    def test_finite_zero_loss_and_gradient_do_not_abort_a_confident_correct_example(self):
        import torch
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import ModernBertConfig, ModernBertForSequenceClassification, PreTrainedTokenizerFast
        from sse_multivector.distillation_run import write_json, read_json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backend = Tokenizer(models.WordLevel({'<pad>': 0, '<unk>': 1, 'Plants': 2}, unk_token='<unk>'))
            backend.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
            tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, pad_token='<pad>', unk_token='<unk>')
            tokenizer.save_pretrained(root/'base')
            model = ModernBertForSequenceClassification(ModernBertConfig(vocab_size=3,
                hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
                max_position_embeddings=256, num_labels=5, pad_token_id=0,
                bos_token_id=2, eos_token_id=2, cls_token_id=2, sep_token_id=2))
            with torch.no_grad():
                model.classifier.weight.zero_()
                model.classifier.bias.zero_()
                model.classifier.bias[0] = 1000.
            model.save_pretrained(root/'base')
            self.targets(root)
            write_json(root/'config.json', dict(model=str(root/'base'), revision='a'*40,
                max_length=256, epochs=[1, 2], batch_size=1, learning_rate=.001, seed=17,
                memory_budget_gib=8, reserve_gib=8))
            command = [sys.executable, '-m', 'sse_multivector.compare_student_pilot', 'train',
                '--config', str(root/'config.json'), '--data', str(root/'data'), '--output', str(root/'fit')]
            for stage in ('train', 'verify'):
                result = subprocess.run(command+['--stage', stage], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            report = read_json(root/'fit/report.json')
            self.assertTrue(report['complete'])
            self.assertEqual(report['updates'], 2)
            self.assertEqual(report['zero_loss_updates'], 2)
            self.assertTrue(all(c['mean_epoch_loss'] == 0. and c['reload_matches']
                                for c in report['checkpoints']))
            from unittest.mock import patch
            from sse_multivector import compare_student_pilot as pilot
            original = ModernBertForSequenceClassification.from_pretrained
            for failure in ('nonfinite_gradient', 'zero_gradient_with_nonzero_loss'):
                with self.subTest(failure=failure):
                    if failure == 'zero_gradient_with_nonzero_loss':
                        with torch.no_grad():
                            model.classifier.bias.zero_()
                        model.save_pretrained(root/'base')

                    def load_with_invalid_gradient(*args, **kwargs):
                        loaded = original(*args, **kwargs)
                        for parameter in loaded.parameters():
                            parameter.register_hook(lambda gradient: torch.full_like(
                                gradient, float('nan') if failure == 'nonfinite_gradient' else 0.))
                        return loaded

                    output = root/failure
                    with patch.object(ModernBertForSequenceClassification, 'from_pretrained',
                                      side_effect=load_with_invalid_gradient):
                        with self.assertRaisesRegex(ValueError, 'nonfinite loss/gradient or zero gradient'):
                            pilot.train(root/'config.json', root/'data', output, 'train')
                    failed = read_json(output/'report.json')
                    self.assertFalse(failed['complete'])
                    self.assertEqual(failed['updates'], 0)
                    self.assertEqual(failed['failed_update']['case_ids'], ['train-fixture'])
                    self.assertEqual(failed['failed_update']['gradient_norm'],
                                     'nan' if failure == 'nonfinite_gradient' else 0.)
                    if failure == 'zero_gradient_with_nonzero_loss':
                        self.assertGreater(failed['failed_update']['loss'], 0.)

    def test_native_option_and_pointer_fits_reload_their_real_adapters_and_head(self):
        import torch
        from tokenizers.pre_tokenizers import ByteLevel
        from transformers import Qwen2Config, Qwen2Model, Qwen2ForCausalLM, Qwen2Tokenizer
        from sse_multivector import compare_student_pilot as pilot
        from sse_multivector.distillation_run import write_json, read_json
        source = read_json(Path(__file__).parent/'distillation/compare-relation-only-kev27b-default-v1.json')
        sys.path.insert(0, source['upstream_path'])
        from kev.model import PointerHead, SPECIAL
        for kind in ('causal_lm', 'pointer'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                torch.manual_seed(17)
                model_config = Qwen2Config(vocab_size=512, hidden_size=32, intermediate_size=64,
                    num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
                    max_position_embeddings=4096)
                model = (Qwen2Model if kind == 'pointer' else Qwen2ForCausalLM)(model_config)
                model.save_pretrained(root/'base')
                words = ['[UNK]', '[PAD]', *sorted(ByteLevel.alphabet())]
                tokenizer = Qwen2Tokenizer(vocab=dict(zip(words, range(len(words)))), merges=[],
                    unk_token='[UNK]', pad_token='[PAD]', additional_special_tokens=SPECIAL)
                tokenizer.chat_template = ('{% for message in messages %}{{message["content"]}}'
                    '{% endfor %}{% if add_generation_prompt %}\nassistant\n{% endif %}')
                tokenizer.save_pretrained(root/'base')
                question = dict(instructions='Compare fixed meanings.',
                    criteria={label: label for label in reversed(pilot.LABELS)}, output_field='relation')
                native = dict(source, model=str(root/'base'), revision='a'*40, kind=kind,
                    quantization='nf4', max_input_tokens=2048, memory_budget_gib=8,
                    reserve_gib=8, question=question, readout='options')
                if kind == 'causal_lm':
                    native['answer_prefix'] = 'Answer: ('
                if kind == 'pointer':
                    head = PointerHead(32, 16)
                    torch.save(dict(base='tiny-foundation', base_revision='a'*40,
                        weights='full', head=head.state_dict(), head_dim=16, temperature=1.3), root/'base/head.pt')
                    native.update(base_model='tiny-foundation', base_revision='a'*40)
                write_json(root/'native.json', native)
                self.targets(root)
                config = dict(model=str(root/'base'), revision='a'*40, max_length=2048,
                    epochs=[1, 2], batch_size=1, learning_rate=.001, seed=17,
                    memory_budget_gib=8, reserve_gib=8, local_model_config='native.json')
                write_json(root/'config.json', config)
                command = [sys.executable, '-m', 'sse_multivector.compare_student_pilot', 'train',
                    '--config', str(root/'config.json'), '--data', str(root/'data'), '--output', str(root/'fit')]
                for stage in ('train', 'verify'):
                    result = subprocess.run(command+['--stage', stage], text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                report = read_json(root/'fit/report.json')
                self.assertTrue(report['complete'])
                self.assertEqual(report['architecture'], kind)
                self.assertEqual(report['training_examples_seen'], 2)
                self.assertEqual(report['supervised_class_decisions'], 2)
                self.assertNotEqual(report['training_pid'], report['verification_pid'])
                self.assertTrue(all(c['reload_matches'] for c in report['checkpoints']))
                self.assertLess(report['trainable_parameters'], report['parameters'])
                from sse_multivector.local_weight_model import LocalWeights
                native_readout = LocalWeights(root/'native.json')
                state = read_json(root/'data/data.json')['evaluation'][0]['state']
                reply = native_readout.complete(dict(model=native_readout.name,
                    messages=[dict(role='user', content=state)]))
                self.assertEqual(report['baseline']['decisions'][0]['relation'],
                                 json.loads(reply['raw_text'])['relation'])
                del native_readout
                torch.cuda.empty_cache()
                for checkpoint in report['checkpoints']:
                    decisions = checkpoint['evaluation']['decisions']
                    self.assertEqual([d['case_id'] for d in decisions], ['evaluation-fixture'])
                    self.assertEqual(checkpoint['evaluation']['label_order'], list(pilot.LABELS))
                from safetensors.torch import load_file
                weights = load_file(root/'fit/checkpoints/epoch-2/adapter_model.safetensors')
                self.assertTrue(any(v.norm() > 0 for k,v in weights.items() if 'lora_B' in k))
                if kind == 'pointer':
                    saved = torch.load(root/'fit/checkpoints/epoch-2/head.pt', weights_only=True)
                    self.assertTrue(any(not torch.equal(head.state_dict()[k], v.cpu())
                                        for k,v in saved['head'].items()))

    def targets(self, root):
        from sse_multivector import compare_student_pilot as pilot
        from sse_multivector.distillation_run import write_json
        cases, producers = [], []
        text = 'Compare these fixed meanings.\n{INPUT_JSON}'
        from hashlib import sha256
        prompt_hash = sha256(text.encode()).hexdigest()
        for role in ('train', 'evaluation'):
            identity = role+'-fixture'
            payload = dict(local=dict(meaning='Plants', post=role+' Plants', entry={}),
                canonical=dict(id=identity, subject='Plants', meaning='Plants', entries=[],
                               parents=[], ancestors=[], descendants=[]))
            inputs_ = dict(INPUT_JSON=json.dumps(payload))
            receipt = dict(results_path='fixture-only', record_sha256=sha256(identity.encode()).hexdigest())
            support = dict(case_id=identity, note_id=identity, pubkey=identity, number='1')
            cases.append(dict(experiment=identity, case_id=identity, prompt_id='fixture',
                prompt_sha256=prompt_hash, input_sha256=pilot.digest(inputs_), inputs=inputs_,
                answer=dict(meaning='Plants', relation='equivalent', reason='Fixture identical meanings.'),
                evidence=dict(local=support, canonical=support, role=role, split='train', family_id=identity,
                              family='same_entry_control', application_allowed=False), receipt=receipt,
                reviews=[dict(role='agent', current=True, verdict='accept')]))
            producers.append(dict(experiment=identity, prompt_id='fixture',
                                  cases=[dict(id=identity, receipt=receipt)]))
        write_json(root/'compare.json', dict(schema_version=1,
            prompts={prompt_hash: dict(text=text, prompt_ids=['fixture'])}, cases=cases))
        write_json(root/'provenance.json', dict(schema_version=1, experiments=producers, inference_calls=0))
        pilot.prepare(root/'compare.json', root/'provenance.json', root/'data')

    def test_encoder_fits_only_train_and_verifies_saved_checkpoints_in_fresh_process(self):
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import ModernBertConfig, ModernBertForSequenceClassification, PreTrainedTokenizerFast
        from sse_multivector import compare_student_pilot as pilot
        from sse_multivector.distillation_run import write_json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backend = Tokenizer(models.WordLevel({'<pad>': 0, '<unk>': 1, 'Plants': 2}, unk_token='<unk>'))
            backend.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
            tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, pad_token='<pad>', unk_token='<unk>')
            tokenizer.save_pretrained(root/'base')
            model = ModernBertForSequenceClassification(ModernBertConfig(vocab_size=3,
                hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
                max_position_embeddings=256, num_labels=5, pad_token_id=0,
                bos_token_id=2, eos_token_id=2, cls_token_id=2, sep_token_id=2))
            model.save_pretrained(root/'base')
            self.targets(root)
            token_totals = {}
            for input_format in ('full_state', 'input_json'):
                config = dict(model=str(root/'base'), revision='a'*40, max_length=256,
                    epochs=[1, 2], batch_size=1, learning_rate=.001, seed=17,
                    memory_budget_gib=8, reserve_gib=8, input_format=input_format)
                write_json(root/'config.json', config)
                command = [sys.executable, '-m', 'sse_multivector.compare_student_pilot', 'train',
                    '--config', str(root/'config.json'), '--data', str(root/'data'), '--output', str(root/('fit-'+input_format))]
                for stage in ('train', 'verify'):
                    result = subprocess.run(command+['--stage', stage], text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads((root/('fit-'+input_format)/'report.json').read_text())
                self.assertTrue(report['complete'])
                self.assertEqual(report['input_format'], input_format)
                token_totals[input_format] = report['input_tokens']['train']['total']
                self.assertNotEqual(report['training_pid'], report['verification_pid'])
                self.assertEqual(report['updates'], 2)
                self.assertEqual(report['training_examples_seen'], 2)
                self.assertEqual([c['epoch'] for c in report['checkpoints']], [1, 2])
                self.assertTrue(all(c['reload_matches'] for c in report['checkpoints']))
                for checkpoint in report['checkpoints']:
                    self.assertEqual(checkpoint['evaluation']['cases'], 1)
                    self.assertEqual(checkpoint['evaluation']['decisions'][0]['case_id'], 'evaluation-fixture')
            self.assertLess(token_totals['input_json'], token_totals['full_state'])


if __name__ == '__main__':
    unittest.main()
