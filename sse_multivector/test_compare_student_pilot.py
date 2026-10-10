"""Exercise reviewed Compare target preparation through the native workflows."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import test_compare_student_inputs as inputs


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
        env = dict(os.environ, EXPERIMENT_RUNNER_ROOT=str(Path(__file__).resolve().parents[2]/'experiment-runner'))
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
        self.write('fit-config.json', dict(model='must-not-be-loaded', revision='a'*40,
            max_length=256, epochs=[1], batch_size=1, learning_rate=.001,
            seed=17, memory_budget_gib=8, reserve_gib=8))
        result = subprocess.run([sys.executable, '-m', 'sse_multivector.compare_student_pilot',
            'train', '--config', str(self.root/'fit-config.json'), '--data', str(self.root/'pilot'),
            '--output', str(self.root/'fit'), '--stage', 'train'], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('targets differ from reviewed teacher collection', result.stderr)
        self.assertFalse((self.root/'fit').exists())


@unittest.skipUnless(os.environ.get('RUN_COMPARE_PILOT_GPU_TESTS') == '1', 'explicit CUDA integration run')
class CompareStudentPilotGPUIntegrationTests(unittest.TestCase):
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
            config = dict(model=str(root/'base'), revision='a'*40, max_length=256,
                epochs=[1, 2], batch_size=1, learning_rate=.001, seed=17,
                memory_budget_gib=8, reserve_gib=8)
            write_json(root/'config.json', config)
            command = [sys.executable, '-m', 'sse_multivector.compare_student_pilot', 'train',
                '--config', str(root/'config.json'), '--data', str(root/'data'), '--output', str(root/'fit')]
            for stage in ('train', 'verify'):
                result = subprocess.run(command+['--stage', stage], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((root/'fit/report.json').read_text())
            self.assertTrue(report['complete'])
            self.assertNotEqual(report['training_pid'], report['verification_pid'])
            self.assertEqual(report['updates'], 2)
            self.assertEqual(report['training_examples_seen'], 2)
            self.assertEqual([c['epoch'] for c in report['checkpoints']], [1, 2])
            self.assertTrue(all(c['reload_matches'] for c in report['checkpoints']))
            for checkpoint in report['checkpoints']:
                self.assertEqual(checkpoint['evaluation']['cases'], 1)
                self.assertEqual(checkpoint['evaluation']['decisions'][0]['case_id'], 'evaluation-fixture')


if __name__ == '__main__':
    unittest.main()
