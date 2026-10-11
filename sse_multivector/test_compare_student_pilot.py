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
