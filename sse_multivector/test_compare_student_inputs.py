"""Prepare Compare qualification inputs through the real shared workflow."""
import hashlib
import json
import unittest

from sse_multivector import test_bootstrap_student_inputs as bootstrap


class CompareStudentInputTests(unittest.TestCase):
    setUp = bootstrap.BootstrapStudentInputTests.setUp
    write = bootstrap.BootstrapStudentInputTests.write
    cli = bootstrap.BootstrapStudentInputTests.cli
    prepare = bootstrap.BootstrapStudentInputTests.prepare
    show = bootstrap.BootstrapStudentInputTests.show
    calls = bootstrap.BootstrapStudentInputTests.calls

    def source(self, meaning='Plants', user_reject=False):
        selection, _ = bootstrap.BootstrapStudentInputTests.source(self)
        self.prompt.write_text('GENERIC PROMPT\n{INPUT_JSON}')
        self.prepare('bootstrap-train')
        selection['role'] = 'evaluation'
        self.write('evaluation-selection.json', selection)
        spec = json.loads(self.spec.read_text())
        spec['dataset']['path'] = 'evaluation-selection.json'
        self.write('evaluation-spec.json', spec)
        self.cli('prepare', 'bootstrap-evaluation', '--spec', self.root/'evaluation-spec.json')
        answer = dict(ambiguities=[], resolutions=[], meaning=meaning, evidence=[])
        for role in ('train', 'evaluation'):
            name = 'bootstrap-'+role
            self.cli('run', name, env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
            for case in self.show(name)['cases']:
                self.cli('review', name, '--case', case['id'], '--role', 'agent',
                         '--verdict', 'accept', '--comment', 'Provisional fixture meaning review.')
        if user_reject:
            case = self.show('bootstrap-train')['cases'][1]
            self.cli('review', 'bootstrap-train', '--case', case['id'], '--role', 'user',
                     '--verdict', 'reject', '--comment', 'Fixture human rejection.')
            self.cli('review', 'bootstrap-train', '--case', case['id'], '--role', 'agent',
                     '--verdict', 'accept', '--comment', 'Cannot override the human decision.')
        return self.selection()

    def selection(self):
        self.cli('collect', 'bootstrap-train', 'bootstrap-evaluation', '--output', 'bootstrap-collected')
        refs = {key: dict(path='bootstrap-collected/'+name,
                         sha256=hashlib.sha256((self.root/'bootstrap-collected'/name).read_bytes()).hexdigest())
                for key, name in [('bootstrap', 'bootstrap.json'), ('provenance', 'provenance.json')]}
        selection = dict(schema_version=1, **refs, role='train', seed='compare-pilot',
                         max_pairs=2, self_pairs=1)
        self.write('compare-selection.json', selection)
        spec = json.loads(self.spec.read_text())
        spec['dataset'] = dict(adapter='compare_student_inputs', path='compare-selection.json')
        self.write('compare-spec.json', spec)
        return selection

    def test_native_preparation_preserves_meanings_and_roles_without_sp_relation_labels(self):
        self.source()
        calls = self.log.read_bytes()
        self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json')
        result = self.show('compare-train')
        sources = self.show('bootstrap-train')['cases']
        source_ids = {c['id'] for c in sources}
        self.assertEqual(len(result['cases']), 3)
        for case in result['cases']:
            data = json.loads(case['inputs']['INPUT_JSON'])
            self.assertEqual(data['local']['meaning'], 'Plants')
            self.assertEqual(data['canonical']['meaning'], 'Plants')
            self.assertEqual(data['canonical']['parents'], [])
            self.assertEqual(data['canonical']['ancestors'], [])
            self.assertEqual(data['canonical']['descendants'], [])
            self.assertEqual(case['evidence']['role'], 'train')
            for side in ('local', 'canonical'):
                self.assertIn(case['evidence'][side]['case_id'], source_ids)
            self.assertNotIn('relation', case['evidence'])
            self.assertFalse(case['evidence']['application_allowed'])
        plan = json.loads((self.root/'compare-train/experiment.json').read_text())['plan']
        self.assertIn('compare_student_inputs.py', plan['code'])
        self.assertEqual(plan['preparation']['target_answers'], 0)
        self.assertEqual(self.log.read_bytes(), calls)

    def test_null_bootstrap_answers_are_not_compare_targets(self):
        self.source(meaning=None)
        calls = self.log.read_bytes()
        error = self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json', ok=False)
        self.assertIn('not enough reviewed non-null', error.stderr)
        self.assertFalse((self.root/'compare-train').exists())
        self.assertEqual(self.log.read_bytes(), calls)

    def test_current_human_rejection_overrides_a_later_agent_accept(self):
        self.source(user_reject=True)
        rejected = self.show('bootstrap-train')['cases'][1]['id']
        calls = self.log.read_bytes()
        self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json')
        for case in self.show('compare-train')['cases']:
            self.assertNotIn(rejected, [case['evidence'][side]['case_id']
                                        for side in ('local', 'canonical')])
        self.assertEqual(self.log.read_bytes(), calls)

    def test_changed_collection_is_refused(self):
        self.source()
        path = self.root/'bootstrap-collected/bootstrap.json'
        path.write_text(path.read_text()+'\n')
        calls = self.log.read_bytes()
        error = self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json', ok=False)
        self.assertIn('bootstrap hash mismatch', error.stderr)
        self.assertEqual(self.log.read_bytes(), calls)

    def test_teacher_cannot_rewrite_the_frozen_local_meaning(self):
        self.source()
        self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json')
        before = len(self.calls())
        self.cli('run', 'compare-train', ok=False, env={'FAKE_RUNNER_PROMPT_RESPONSE':
            json.dumps(dict(meaning='Changed meaning', relation='neither', reason='Changed.'))})
        result = self.show('compare-train')
        self.assertEqual(result['summary']['malformed'], 3)
        self.assertEqual(len(self.calls())-before, 3)

    def test_native_collection_keeps_three_field_teachers_and_relation_only_is_separate(self):
        self.source()
        self.cli('prepare', 'compare-train', '--spec', self.root/'compare-spec.json')
        answer = dict(meaning='Plants', relation='neither', reason='Fixture teacher decision.')
        self.cli('run', 'compare-train', env={'FAKE_RUNNER_PROMPT_RESPONSE': json.dumps(answer)})
        calls = self.log.read_bytes()
        self.cli('collect', 'compare-train', '--output', 'compare-collected')
        data = json.loads((self.root/'compare-collected/compare.json').read_text())
        self.assertEqual(len(data['cases']), 3)
        self.assertIn('Provisional', data['semantic_status'])
        for case in data['cases']:
            self.assertEqual(case['answer'], answer)
            self.assertNotIn('accepted', case)
        self.assertEqual(self.log.read_bytes(), calls)
