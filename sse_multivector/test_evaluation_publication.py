"""Compact final evaluation results follow the production saved output paths."""
import hashlib
import gzip
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_run as run


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + '\n')


class EvaluationPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = patch.dict(os.environ, {
            'ORACLE_EXPERIMENT_BACKOFF_DIRECTORY': str(self.root / 'admission')})
        environment.start()
        self.addCleanup(environment.stop)

    def rows(self, path):
        return [json.loads(line) for line in path.read_text().splitlines()]

    def fixture(self):
        answer = dict(raw='{"subjects":[{"number":"1","subject":"Tea","context":"Tea is named."}]}',
                      tokens=18, truncated=False, seconds=0.2)
        data = dict(evaluation=[dict(note_id='post-1', messages=[dict(role='user', content='PRIVATE EXPANDED REQUEST')])],
                    references={'post-1': {'text': 'Tea.', 'subjects': []}})
        return answer, data, dict(evaluation_tasks=['subjects'], model='fixture/model', revision='a' * 40,
                                 data='/home/private/account/data', seed=17)

    def test_evaluate_automatically_exports_final_answers_without_changing_seals(self):
        from sse_multivector import evaluation_publication as publication
        answer, data, config = self.fixture()
        directory = self.root / 'run/baseline'
        with patch.object(run, 'generate', return_value=answer):
            expected = run.evaluate(None, None, data, config, directory)
        output = directory.parent / 'publication/evaluations/baseline'
        rows = self.rows(output / 'results.jsonl')
        self.assertEqual(rows[0]['answer'], answer)
        self.assertEqual(rows[0]['result'], expected[0])
        self.assertEqual(rows[0]['note_id'], 'post-1')
        self.assertTrue(run.verify_saved(directory))
        self.assertNotIn('PRIVATE EXPANDED REQUEST', (output / 'results.jsonl').read_text())
        self.assertNotIn('/home/private', (output / 'experiment.json').read_text())
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
        publication.export_evaluation(directory, config=config, note_ids=['post-1'])
        self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})

    def test_interrupted_evaluation_exports_saved_partial_answers_and_excludes_test(self):
        from sse_multivector import evaluation_publication as publication
        answer, data, config = self.fixture()
        data['evaluation'].append(dict(note_id='post-2', messages=[]))
        data['references']['post-2'] = data['references']['post-1']
        directory = self.root / 'run/evaluations/checkpoint-200'
        with patch.object(run, 'generate', side_effect=[answer, RuntimeError('temporary failure /private/path')]):
            with self.assertRaisesRegex(RuntimeError, 'temporary failure'):
                run.evaluate(None, None, data, config, directory)
        output = self.root / 'run/publication/evaluations/checkpoint-200'
        meta = json.loads((output / 'experiment.json').read_text())
        self.assertEqual(meta['execution_status'], 'failed')
        self.assertEqual(meta['input']['note_ids'], ['post-1', 'post-2'])
        self.assertEqual(len(self.rows(output / 'results.jsonl')), 1)
        self.assertNotIn('temporary failure', (output / 'experiment.json').read_text())
        sealed = self.root / 'run/test/checkpoint-200'
        write(sealed / 'subjects.json', {'answer': {'raw': 'SEALED ANSWER'}})
        with self.assertRaisesRegex(ValueError, 'test'):
            publication.export_evaluation(sealed)
        exported = publication.export_evaluations(self.root / 'run')
        self.assertEqual(len(exported['evaluations']), 1)
        self.assertFalse((self.root / 'run/publication/evaluations/test').exists())

    def test_partial_subject_results_keep_the_original_mask_task_subject_limit(self):
        answer, data, config = self.fixture()
        answer['raw'] = '{"subjects":[' + ','.join(
            json.dumps(dict(number=str(i), subject='Tea', context='Tea.')) for i in (1, 2)) + ']}'
        data['evaluation'].append(dict(note_id='post-2', messages=[]))
        data['references']['post-2'] = data['references']['post-1']
        config.update(evaluation_tasks=['subjects', 'mask'], max_subjects=1)
        directory = self.root / 'run/baseline'
        with patch.object(run, 'generate', side_effect=[answer, RuntimeError('stopped')]):
            with self.assertRaises(RuntimeError):
                run.evaluate(None, None, data, config, directory)
        row = self.rows(directory.parent / 'publication/evaluations/baseline/results.jsonl')[0]
        self.assertEqual(row['result']['errors'], [{'task': 'subjects', 'error': 'subject count exceeds configured limit'}])

    def test_grades_include_actual_referenced_judgments_and_explicit_missing_evidence(self):
        from sse_multivector import evaluation_publication as publication
        ledger = self.root / 'native/run/results.jsonl'
        raw = '{"valid":true,"reason":"Supported."}'
        record = dict(case='case-1', input_sha256='i' * 64, output=raw,
                      status='complete', messages='PRIVATE REQUEST', provider={'auth': 'SECRET'})
        digest = hashlib.sha256((json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()
        write(ledger, record)
        # Receipt digests bind the decoded native record using its established JSON digest.
        from experiment_runner import inputs
        digest = inputs.digest(record)
        nested_record = dict(record, output='{"valid":false,"reason":"Not supported."}')
        nested_ledger = self.root / 'nested/results.jsonl'
        write(nested_ledger, nested_record)
        premise = dict(case_id='case-1', input_sha256='i' * 64,
                       output_sha256=hashlib.sha256(raw.encode()).hexdigest(), origin=None,
                       receipt=dict(results_path=str(ledger), record_sha256=digest),
                       reviews=[dict(actor='user', role='user', verdict='accept', current=True, reason='Reviewed.',
                                     comment='Recorded user comment.', time='2026-10-01T12:00:00Z')], audits=[])
        missing = dict(premise, case_id='missing', receipt=dict(results_path=str(self.root / 'missing.jsonl'), record_sha256='f' * 64))
        derived = dict(case_id='derived', origin='derived', receipt=None,
            automatic_equivalence_premise=dict(premise,
                output_sha256=hashlib.sha256(nested_record['output'].encode()).hexdigest(),
                receipt=dict(results_path=str(nested_ledger), record_sha256=inputs.digest(nested_record))),
            mechanical_evidence=dict(teacher_paths=[['1', '1.1']], teacher_relationships=[dict(parent='1', child='1.1')]))
        agent_path = self.root / 'agent-adjudication.json'
        write(agent_path, dict(schema_version=1, actor='agent', check='support', decision={'valid': False},
            reason='Independent agent assessment.', rule='Quoted generation rule.',
            original_decision_classification='incorrect', sources={str(self.root): 'secret'},
            original={'inputs': {'POST': 'PRIVATE EXPANDED INPUT'}}))
        adjudicated = dict(case_id='agent-case', origin='adjudicated', receipt=None,
            adjudication=dict(path=str(agent_path), sha256=run.sha256(agent_path), actor='agent'))
        report = self.root / 'automatic/grades.json'
        write(report, dict(schema_version=1, automatic_status='complete', policy='grading', sources={},
            random=dict(answers=[dict(id='answer-1', note_id='post-1', scoring=dict(status='valid', scores={}),
                                      premises=[premise, dict(premise, case_id='reused-case'), missing, derived, adjudicated], dependencies=[])]),
                           challenge=dict(answers=[])))
        publication.export_grades(report)
        output = report.parent / 'publication'
        judgments = self.rows(output / 'judgments.jsonl')
        self.assertEqual(len(judgments), 4, 'unique native judgments plus the explicit agent assessment')
        self.assertEqual(judgments[0]['output'], raw)
        self.assertEqual(judgments[0]['evidence_status'], 'saved')
        self.assertEqual(judgments[1]['evidence_status'], 'missing')
        self.assertEqual(judgments[2]['output'], nested_record['output'])
        self.assertEqual(judgments[3]['actor'], 'agent')
        self.assertIs(judgments[3]['decision']['valid'], False)
        exported = (output / 'results.jsonl').read_text() + (output / 'judgments.jsonl').read_text()
        self.assertNotIn(str(self.root), exported)
        self.assertNotIn('PRIVATE REQUEST', exported)
        self.assertNotIn('SECRET', exported)
        self.assertEqual(self.rows(output / 'results.jsonl')[0]['premises'][0]['reviews'][0]['actor'], 'user')
        review = self.rows(output / 'results.jsonl')[0]['premises'][0]['reviews'][0]
        self.assertEqual(review['comment'], 'Recorded user comment.')
        self.assertEqual(review['time'], '2026-10-01T12:00:00Z')
        self.assertEqual(self.rows(output / 'results.jsonl')[0]['premises'][3]['mechanical_evidence']['teacher_paths'], [['1', '1.1']])

    def test_l1_and_native_grade_comparisons_and_effort_results_are_final_records(self):
        from sse_multivector import evaluation_publication as publication
        cases = [
            ('l1.json', dict(schema_version=1, scope='L1 only', aggregation='note means', sources={}, results={
                'qwen-pass3': dict(model='Qwen/model', version='pass3', stats={'notes': 1},
                    notes=[dict(note_id='p', answer_id='a', correctness=1., root_groups=[])])})),
            ('comparison.json', dict(schema_version=1, analysis_only=True, qualification='Paired comparison.',
                sources={}, random={'answers': 1, 'versions': {'qwen-pass3': {'answers': 1,
                    'statuses': {'automated': {'malformed': 1}, 'reference': {'valid': 1}}}}},
                challenge={'answers': 0}, paired_answers={
                    'random': [dict(id='a', note_id='p', automated_scores={}, reference_scores={}, score_differences={})],
                    'challenge': []})),
            ('effort.json', dict(schema_version=1, stage=5, inference_calls=0, basis='Verdict agreement.',
                summary={'paired_complete': True}, rows=[dict(key='k', input_sha256='i' * 64,
                    prompt_sha256='p' * 64, aliases=[], results={}, paired={'high': 'agree'})])),
        ]
        for filename, value in cases:
            with self.subTest(filename=filename):
                source = self.root / filename
                write(source, value)
                output = self.root / (filename + '-publication')
                publication.export_comparison(source, output)
                rows = self.rows(output / 'results.jsonl')
                self.assertEqual(len(rows), 1)
                self.assertNotIn(str(self.root), (output / 'experiment.json').read_text())
                if filename == 'comparison.json':
                    summary = json.loads((output / 'experiment.json').read_text())['parameters']['random']
                    self.assertEqual(summary['versions']['qwen-pass3']['statuses']['automated']['malformed'], 1)

    def test_legacy_final_coverage_collection_preserves_recorded_grades_without_inventing_policy(self):
        from sse_multivector import evaluation_publication as publication
        from experiment_runner import inputs
        ledger = self.root / 'native/run/results.jsonl'
        raw = '{"valid":true,"reason":"Supported in the post."}'
        record = dict(case='case-1', input_sha256='i' * 64, output=raw, status='complete')
        write(ledger, record)
        scores = dict(correctness=dict(numerator=1, denominator=1, value=1.0),
                      coverage=dict(numerator=1, denominator=2, value=0.5))
        source = self.root / 'final-reviewed-collected-review.json'
        result = dict(schema_version=1, coverage=str(self.root / 'coverage'), output=str(source),
            sources={str(ledger): run.sha256(ledger)}, inference_calls=0,
            random=dict(answers=[dict(id='answer-1', note_id='post-1',
                scoring=dict(status='complete', scores=scores), dependencies=[],
                premises=[dict(case_id='case-1', input_sha256='i' * 64,
                    output_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                    receipt=dict(results_path=str(ledger), record_sha256=inputs.digest(record)))],
                coverage_inconsistencies=[])]), challenge=dict(answers=[]))
        write(source, result)
        output = self.root / 'publication'
        publication.export_grades(source, output)
        self.assertEqual(self.rows(output / 'results.jsonl')[0]['scoring']['scores'], scores)
        self.assertEqual(self.rows(output / 'judgments.jsonl')[0]['output'], raw)
        self.assertNotIn('policy', json.loads((output / 'experiment.json').read_text())['parameters'])
        for field, invalid in [('schema_version', 2), ('coverage', {}), ('sources', []), ('inference_calls', 1)]:
            with self.subTest(field=field):
                broken = self.root / (field + '.json')
                write(broken, {**result, field: invalid})
                with self.assertRaisesRegex(ValueError, 'final grading report'):
                    publication.export_grades(broken, self.root / (field + '-publication'))

    def test_final_effort_reference_measurements_survive_plain_and_gzipped_sources(self):
        from sse_multivector import evaluation_publication as publication
        counts = dict(agrees_reference=3, disagrees_reference=1, unresolved_reference=2)
        references = dict(status='agrees_reference', resolved_occurrences=1,
                          unresolved_occurrences=0, labels=[None, True])
        result = dict(schema_version=1, stage=60, inference_calls=0,
            summary=dict(raw_agent_reference=dict(xhigh=counts)),
            rows=[dict(key='question-1', input_sha256='i' * 64,
                       raw_agent_reference=dict(xhigh=references))])
        for compressed in (False, True):
            with self.subTest(compressed=compressed):
                source = self.root / ('effort.json.gz' if compressed else 'effort.json')
                if compressed:
                    with gzip.open(source, 'wt') as stream:
                        json.dump(result, stream)
                else:
                    write(source, result)
                before = (source.read_bytes(), source.stat().st_mtime_ns)
                output = self.root / ('gzip-publication' if compressed else 'plain-publication')
                publication.export_comparison(source, output)
                self.assertEqual(self.rows(output / 'results.jsonl')[0]['raw_agent_reference']['xhigh'], references)
                metadata = json.loads((output / 'experiment.json').read_text())
                self.assertEqual(metadata['parameters']['summary']['raw_agent_reference']['xhigh'], counts)
                self.assertEqual(metadata['source']['report_sha256'], run.sha256(source))
                self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), before)

    def test_older_receipts_without_separate_output_hash_remain_distinct_from_hash_conflicts(self):
        from sse_multivector import evaluation_publication as publication
        from experiment_runner import inputs
        ledger = self.root / 'native/run/results.jsonl'
        records = [dict(case='case-' + str(i), input_sha256='i' * 64,
                        final_output_raw='{"valid":true,"reason":"Evidence ' + str(i) + '."}',
                        status='complete') for i in range(3)]
        ledger.parent.mkdir(parents=True)
        ledger.write_text(''.join(json.dumps(record) + '\n' for record in records))
        premises = [dict(case_id=record['case'], input_sha256=record['input_sha256'],
                         receipt=dict(results_path=str(ledger), record_sha256=inputs.digest(record)))
                    for record in records]
        premises[1]['output_sha256'] = 'f' * 64
        premises.append({**premises[2],
            'output_sha256': hashlib.sha256(records[2]['final_output_raw'].encode()).hexdigest()})
        source = self.root / 'grades.json'
        write(source, dict(schema_version=1, policy='Recorded grading policy', sources={},
            random=dict(answers=[dict(id='answer-1', note_id='post-1',
                                     scoring={}, premises=premises, dependencies=[])]),
            challenge=dict(answers=[])))
        output = self.root / 'publication'
        publication.export_grades(source, output)
        rows = self.rows(output / 'judgments.jsonl')
        self.assertEqual([row['evidence_status'] for row in rows], ['saved', 'mismatch', 'saved'])
        self.assertEqual([row['output_binding'] for row in rows],
                         ['receipt_only', 'receipt_and_output_hash', 'receipt_and_output_hash'])
        self.assertEqual(rows[0]['output'], records[0]['final_output_raw'])
        self.assertNotIn('output', rows[1])
        self.assertEqual(rows[2]['output'], records[2]['final_output_raw'])
        self.assertNotIn('output_sha256', self.rows(output / 'results.jsonl')[0]['premises'][0])

    def test_final_effort_source_assessment_retains_accuracy_bounds_and_attributed_adjudication(self):
        from sse_multivector import evaluation_publication as publication
        adjudication = self.root / 'private/adjudication.json'
        write(adjudication, dict(schema_version=1, key='question-1', actor='agent',
            status='resolved', accepted_verdicts=[{'valid': True}], reason='The post supplies the restriction.',
            gold_status='Source assessment, not human-certified truth.',
            final_paired_receipt_reconciliation_required=True,
            evidence={'/home/private/account/auth.json': 'SECRET'}))
        measures = dict(N=2, same_decision=1, H=1, G=0, A=0, both_correct=1, both_wrong=0,
            net_loss_count=1, loss_range_count=[1, 1], loss_range_percentage_points=[50., 50.],
            upper_within_2pp=False)
        deletion = dict(method='Omit one source component from the measurements.', source_contexts=2,
            components=2, full_point_loss_percentage_points=50.,
            deletion_point_range_percentage_points=[0., 100.], largest_absolute_point_change_percentage_points=50.,
            deletion_truth_envelope_percentage_points=[0., 100.], rows=[dict(note_ids=['post-1'],
                removed_prompts=1, remaining=measures, by_check={'matching': measures},
                by_role={'matching': measures}, by_cohort={'random': measures})])
        result = dict(schema_version=1, status='source_assessed', effort='high', stage=10,
            accuracy_basis='Agent source judgments; unresolved truth remains unscored.',
            paired={'path': '/home/private/paired.json', 'sha256': 'b' * 64}, sources={},
            summary=measures, by_check={'matching': measures}, by_role={'matching': measures},
            by_cohort={'random': measures}, new_prompts=measures, prior_prompts=measures,
            role_overlap={'actual_and_compatibility': 1, 'note': 'The roles overlap.'},
            evidence_verification={'current_adjudications': 1, 'linked_files': 1, 'all_hashes_verified': True},
            source_component_deletion=deletion, limitations=['A selected panel, not population accuracy.'],
            rows=[dict(key='question-1', classification='H', roles=['matching'], cohorts=['random'],
                baseline_normalized_verdict=True, candidate_normalized_verdict=False, in_prior_stage_5=False,
                source_adjudication=dict(path=str(adjudication), sha256=run.sha256(adjudication),
                    status='resolved', accepted_normalized_verdicts=[True])),
                  dict(key='question-2', classification='same_decision', roles=['matching'],
                       cohorts=['random'], source_adjudication=None)])
        source = self.root / 'stage-10-high-source-assessment.json'
        write(source, result)
        output = self.root / 'publication'
        publication.export_comparison(source, output)
        metadata = json.loads((output / 'experiment.json').read_text())
        self.assertEqual(metadata['parameters']['summary'], measures)
        self.assertEqual(metadata['parameters']['by_check']['matching'], measures)
        self.assertEqual(metadata['parameters']['source_component_deletion'], deletion)
        row = self.rows(output / 'results.jsonl')[0]
        self.assertIs(row['baseline_normalized_verdict'], True)
        self.assertIs(row['candidate_normalized_verdict'], False)
        self.assertEqual(row['source_adjudication']['sha256'], run.sha256(adjudication))
        judgment = self.rows(output / 'judgments.jsonl')[0]
        self.assertEqual(judgment['actor'], 'agent')
        self.assertEqual(judgment['evidence_status'], 'saved')
        self.assertEqual(judgment['reason'], 'The post supplies the restriction.')
        self.assertEqual(judgment['accepted_verdicts'], [{'valid': True}])
        self.assertIs(judgment['final_paired_receipt_reconciliation_required'], True)
        exported = ''.join(p.read_text() for p in output.iterdir())
        self.assertNotIn('/home/private', exported)
        self.assertNotIn('SECRET', exported)
        self.assertTrue(adjudication.is_file(), 'Deletion measurements must never delete source files.')
        write(adjudication, {**json.loads(adjudication.read_text()), 'reason': 'Changed after the source was frozen.'})
        publication.export_comparison(source, output)
        self.assertEqual(self.rows(output / 'judgments.jsonl')[0]['evidence_status'], 'mismatch')
        for field, invalid in [('schema_version', 2), ('effort', 'unknown'), ('summary', {})]:
            with self.subTest(field=field):
                invalid_source = self.root / (field + '.json')
                write(invalid_source, {**result, field: invalid})
                with self.assertRaisesRegex(ValueError, 'source assessment'):
                    publication.export_comparison(invalid_source, self.root / (field + '-publication'))
        saved = json.loads(adjudication.read_text())
        saved.pop('actor')
        write(adjudication, saved)
        result['rows'][0]['source_adjudication']['sha256'] = run.sha256(adjudication)
        write(source, result)
        publication.export_comparison(source, output)
        self.assertEqual(self.rows(output / 'judgments.jsonl')[0]['actor'], 'not_recorded')

    def test_source_assessment_cannot_publish_changed_bytes_under_an_earlier_hash(self):
        from sse_multivector import evaluation_publication as publication
        adjudication = self.root / 'adjudication.json'
        write(adjudication, dict(actor='agent', reason='Frozen assessment.'))
        source = self.root / 'assessment.json'
        write(source, dict(schema_version=1, stage=5, effort='high', accuracy_basis='Source assessment.',
            paired={'sha256': 'b' * 64}, summary=dict(N=1, H=0, G=0, A=1),
            rows=[dict(key='question-1', classification='A',
                source_adjudication=dict(path=str(adjudication), sha256=run.sha256(adjudication)))]))
        original_hash = publication._hash

        def change_after_hash(path):
            checksum = original_hash(path)
            if Path(path) == adjudication:
                write(adjudication, dict(actor='agent', reason='Changed after hashing.'))
            return checksum

        output = self.root / 'publication'
        with patch.object(publication, '_hash', side_effect=change_after_hash):
            publication.export_comparison(source, output)
        judgment = self.rows(output / 'judgments.jsonl')[0]
        self.assertEqual(judgment['evidence_status'], 'saved')
        self.assertEqual(judgment['reason'], 'Frozen assessment.')

    def test_saved_result_note_identity_must_match_its_answer_and_selection(self):
        from sse_multivector import evaluation_publication as publication
        directory = self.root / 'run/baseline'
        write(directory / 'results.json', [dict(note_id='B', subjects=[], errors=[], masks=[])])
        write(directory / 'note-0000/subjects.json', dict(note_id='A', answer=dict(raw='{"subjects":[]}', tokens=3, truncated=False)))
        with self.assertRaisesRegex(ValueError, 'note.*identity'):
            publication.export_evaluation(directory, note_ids=['A'])
        self.assertFalse((directory.parent / 'publication/evaluations/baseline').exists())

    def test_saved_final_legacy_measurements_are_retained(self):
        from sse_multivector import evaluation_publication as publication
        answer, data, config = self.fixture()
        directory = self.root / 'run/baseline'
        with patch.object(run, 'generate', return_value=answer):
            results = run.evaluate(None, None, data, config, directory)
        measurements = dict(notes=1, precision_80=0.75, recall_80=0.5, f1_80=0.6)
        write(directory.parent / 'report.json', dict(status='complete', baseline=measurements,
            scoring='Micro average over source-word selections.'))
        publication.export_evaluation(directory, config=config, note_ids=['post-1'])
        metadata = json.loads((directory.parent / 'publication/evaluations/baseline/experiment.json').read_text())
        self.assertEqual(metadata['measurements'], measurements)

    def test_native_assembled_review_preserves_scores_judgments_and_selected_answers(self):
        from sse_multivector import evaluation_publication as publication
        from experiment_runner import inputs
        raw = '{"valid":true,"reason":"Named in the post."}'
        ledger = self.root / 'native/run/results.jsonl'
        record = dict(status='succeeded', final_output_raw=raw)
        write(ledger, record)
        selection = self.root / 'selection.json'
        write(selection, dict(dataset={'sha256': 'd' * 64}, selection_policy=dict(seed='fixture', random_count=1, hard_count=0),
            random=dict(answers=[dict(id='a', note_id='p', model='fixture/model', revision='a' * 40,
                version='checkpoint-200', raw_answer=dict(raw='{"subjects":[]}', tokens=3, truncated=False),
                task_prompt='TASK INSTRUCTION', generation={'sha256': 'g' * 64}),
                dict(id='sealed-unselected', note_id='unused', raw_answer={'raw': 'SEALED UNUSED ANSWER'})]),
            challenge=dict(answers=[])))
        report = self.root / 'native-evaluation.json'
        write(report, dict(schema_version=1, selection=dict(path=str(selection), sha256=run.sha256(selection)),
            summary={'random': {'answers': 1, 'checks': {'support': {'occurrences': 1, 'semantic': 1,
                'distinct_semantic_inputs': 1, 'roles': {'support': {'unresolved': 0}}}}}},
            sources={}, random=dict(answers=[dict(id='a', note_id='p',
                status='complete', scores={'correctness': {'value': 1.}}, expected_scores={'correctness': {'value': 1.}},
                qualification={'basis': 'agent_assessed', 'status': 'failed', 'checked': 1,
                    'incorrect_cases': ['check-1'], 'unresolved': [], 'skipped_cases': [],
                    'score_differences': {'correctness': {'actual': 0.5, 'expected': 1.}}},
                checks={'support': [dict(id='check-1', input_sha256='i' * 64, output=raw,
                    status='valid', parsed={'valid': True, 'reason': 'Named in the post.'}, qualification={'passed': False},
                    receipt=dict(results_path=str(ledger), record_sha256=inputs.digest(record)),
                    inputs={'POST': 'PRIVATE EXPANDED INPUT'}, prompt='PRIVATE EXPANDED REQUEST'),
                    dict(id='failed-check', status='failed', failure_kind='provider_transient',
                         error='provider failed at /home/private/account/auth.json SECRET'),
                    dict(id='invalid-check', status='invalid_receipt',
                         error='invalid receipt /home/private/account/auth.json SECRET')],
                    'matching': [], 'relationship': []})]), challenge=dict(answers=[])))
        publication.export_review_evaluation(report)
        output = report.parent / 'publication' / report.stem
        row = self.rows(output / 'results.jsonl')[0]
        self.assertEqual(row['scores']['correctness']['value'], 1.)
        self.assertEqual(row['expected_scores']['correctness']['value'], 1.)
        self.assertEqual(row['qualification']['incorrect_cases'], ['check-1'])
        self.assertEqual(row['qualification']['score_differences']['correctness'], {'actual': 0.5, 'expected': 1.})
        self.assertTrue(row['checks']['support'][0]['parsed']['valid'])
        self.assertIs(row['checks']['support'][0]['qualification']['passed'], False)
        self.assertTrue(all('error' not in case for case in row['checks']['support']))
        self.assertEqual(row['checks']['support'][1]['status'], 'failed')
        self.assertEqual(row['checks']['support'][1]['failure_kind'], 'provider_transient')
        self.assertEqual(row['checks']['support'][2]['status'], 'invalid_receipt')
        summary = json.loads((output / 'experiment.json').read_text())['parameters']['summary']
        self.assertEqual(summary['random']['checks']['support']['semantic'], 1)
        self.assertEqual(summary['random']['checks']['support']['roles']['support']['unresolved'], 0)
        self.assertEqual(self.rows(output / 'judgments.jsonl')[0]['output'], raw)
        self.assertEqual(len(self.rows(output / 'answers.jsonl')), 1)
        data = ''.join(p.read_text() for p in output.iterdir())
        self.assertNotIn('PRIVATE EXPANDED', data)
        self.assertNotIn('SEALED UNUSED', data)
        self.assertNotIn(str(self.root), data)
        self.assertNotIn('/home/private/account', data)
        self.assertNotIn('SECRET', data)

    def test_guest_package_exports_without_ijson_or_sibling_runner_checkout(self):
        from sse_multivector import distillation_vm as vm
        package = self.root / 'guest'
        vm.prepare_package(Path(vm.__file__).resolve().parents[1], package)
        container = self.root / 'container'
        # Recreate the production Dockerfile's /work COPY payload, then execute
        # that payload with a clean interpreter. No Docker daemon is required.
        dockerfile = package / 'sse_multivector/distillation/Dockerfile'
        for line in dockerfile.read_text().replace('\\\n', ' ').splitlines():
            parts = shlex.split(line)
            if not parts or parts[0] != 'COPY' or not parts[-1].startswith('/work/'):
                continue
            destination = container / parts[-1][len('/work/'):]
            destination.mkdir(parents=True, exist_ok=True)
            for name in parts[1:-1]:
                source = package / name
                if source.is_dir():
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    shutil.copyfile(source, destination / source.name)
        script = '''
import sys
sys.path.insert(0, sys.argv[1])
sys.modules['ijson'] = None
from sse_multivector import evaluation_publication as publication
from sse_multivector import distillation_run as run
from pathlib import Path
p=Path(sys.argv[2])/'baseline'
p.mkdir(parents=True)
run.write_json(p/'note-0000/subjects.json', {'answer': {'raw':'{"subjects":[]}','tokens':3,'truncated':False}})
publication.export_evaluation(p, results=[{'note_id':'p','subjects':[],'errors':[],'masks':[]}], note_ids=['p'])
assert (p.parent/'publication/evaluations/baseline/results.jsonl').is_file()
'''
        result = subprocess.run([sys.executable, '-I', '-c', script, str(container), str(self.root / 'work')],
            cwd=self.root, env={k: v for k, v in os.environ.items() if k != 'EXPERIMENT_RUNNER_ROOT'},
            capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_automatic_grading_writes_publication_after_final_grades(self):
        from sse_multivector.test_distillation_review_automatic import DistillationAutomaticTests
        fixture = DistillationAutomaticTests()
        fixture.root = self.root
        fixture.test_fresh_evaluation_finishes_with_one_native_run_and_no_matrix()
        output = self.root / 'fresh-automatic/publication'
        self.assertTrue((output / 'results.jsonl').is_file())
        self.assertTrue((output / 'judgments.jsonl').is_file())
        metadata = json.loads((output / 'experiment.json').read_text())
        self.assertEqual(metadata['execution_status'], 'complete')
        self.assertEqual(metadata['input']['status'], 'saved')
        answers = self.rows(output / 'answers.jsonl')
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]['id'], self.rows(output / 'results.jsonl')[0]['id'])
        self.assertIn('Different cable', answers[0]['answer']['raw'])
        self.assertIn('model', answers[0])
        self.assertTrue(self.rows(output / 'judgments.jsonl'))
        state = json.loads((output.parent / 'state.json').read_text())
        self.assertTrue(state['experiments'])
        for entry in state['experiments']:
            child = Path(entry['path'])
            self.assertEqual(json.loads((child / 'experiment.json').read_text())['plan']['publication_role'],
                             'internal')
            self.assertFalse((child / 'publication').exists())

    def test_native_evaluation_run_exports_partial_assembly_without_a_full_report_copy(self):
        from sse_multivector import distillation_review_evaluation as evaluation
        from sse_multivector.test_distillation_review_evaluation import DistillationReviewEvaluationTests
        fixture = DistillationReviewEvaluationTests()
        fixture.root = self.root
        selection = fixture.selection()
        directory = self.root / 'native-evaluation'
        prepared = evaluation.prepare(selection, directory, runner_binary=fixture.worker(), actual_edges_only=True)
        self.assertTrue(prepared['experiments'])
        for entry in prepared['experiments']:
            child = Path(entry['path'])
            self.assertEqual(json.loads((child / 'experiment.json').read_text())['plan']['publication_role'],
                             'internal')
        result = evaluation.run(directory, answer_ids=[])
        output = directory / 'publication'
        self.assertTrue((output / 'results.jsonl').is_file())
        self.assertEqual(len(self.rows(output / 'results.jsonl')), len(result['random']['answers']))
        self.assertFalse((directory / 'report.json').exists())
        self.assertFalse((self.root / 'calls.json').exists())
        metadata = json.loads((output / 'experiment.json').read_text())
        self.assertEqual(metadata['source']['preparation_sha256'], run.sha256(directory / 'evaluation.json'))
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / 'calls.json')):
            evaluation.run(directory)
        self.assertTrue(self.rows(output / 'judgments.jsonl'))
        for entry in prepared['experiments']:
            self.assertFalse((Path(entry['path']) / 'publication').exists())

    def test_interrupted_automatic_grading_keeps_last_partial_scores(self):
        from sse_multivector import distillation_review_automatic as automatic
        from sse_multivector.test_distillation_review_automatic import DistillationAutomaticTests
        fixture = DistillationAutomaticTests()
        fixture.root = self.root
        _, _, coverage, _, _ = fixture.fixture('publication-interrupted')
        directory = self.root / 'automatic'
        automatic.prepare(coverage, directory, runner_binary=self.root / 'fake-runner')
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / 'calls.json')):
            with patch.object(automatic, '_collect', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    automatic.run(directory)
        metadata = json.loads((directory / 'publication/experiment.json').read_text())
        self.assertEqual(metadata['execution_status'], 'stopped')
        self.assertEqual(json.loads((directory / 'state.json').read_text())['status'], 'prepared')
        calls = (self.root / 'calls.json').read_bytes()
        with patch.dict(os.environ, FAKE_RUNNER_LOG=str(self.root / 'calls.json')):
            self.assertEqual(automatic.run(directory)['status'], 'complete')
        self.assertEqual((self.root / 'calls.json').read_bytes(), calls)


if __name__ == '__main__':
    unittest.main()
