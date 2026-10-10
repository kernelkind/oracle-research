"""Exercise meaning-only Bootstrap preparation and fitting through real paths."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import test_compare_student_inputs as inputs


class BootstrapStudentPilotTests(unittest.TestCase):
    setUp = inputs.CompareStudentInputTests.setUp
    write = inputs.CompareStudentInputTests.write
    cli = inputs.CompareStudentInputTests.cli
    prepare = inputs.CompareStudentInputTests.prepare
    show = inputs.CompareStudentInputTests.show
    calls = inputs.CompareStudentInputTests.calls
    selection = inputs.CompareStudentInputTests.selection

    def teachers(self, **kwargs):
        inputs.CompareStudentInputTests.source(self, **kwargs)

    def pilot(self, ok=True, collection='bootstrap-collected'):
        result = subprocess.run([sys.executable, '-m', 'sse_multivector.bootstrap_student_pilot',
            'prepare', '--collection', str(self.root/collection/'bootstrap.json'),
            '--provenance', str(self.root/collection/'provenance.json'),
            '--output', str(self.root/'pilot')], text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stderr)
        return result

    def test_native_targets_keep_complete_inputs_and_only_supervise_meaning(self):
        self.teachers()
        before = self.log.read_bytes()
        self.pilot()
        data = json.loads((self.root/'pilot/data.json').read_text())
        self.assertEqual([len(data[r]) for r in ('train', 'evaluation')], [3, 3])
        for role in ('train', 'evaluation'):
            teachers = {c['id']: c for c in self.show('bootstrap-'+role)['cases']}
            for row in data[role]:
                self.assertEqual(json.loads(row['completion'][0]['content']), {'meaning': 'Plants'})
                self.assertIn(teachers[row['case_id']]['inputs']['INPUT_JSON'], row['prompt'][0]['content'])
                self.assertEqual(row['evidence'], teachers[row['case_id']]['evidence'])
                self.assertIn('only the `meaning` field', row['prompt'][0]['content'])
        self.assertEqual(self.log.read_bytes(), before)

    def test_nulls_remain_targets_and_human_rejection_cannot_be_overridden(self):
        self.teachers(meaning=None, user_reject=True)
        case = self.show('bootstrap-train')['cases'][2]
        self.cli('review', 'bootstrap-train', '--case', case['id'], '--role', 'agent',
                 '--verdict', 'uncertain', '--comment', 'Fixture unresolved meaning.')
        self.cli('collect', 'bootstrap-train', 'bootstrap-evaluation', '--output', 'reviewed')
        self.pilot(collection='reviewed')
        data = json.loads((self.root/'pilot/data.json').read_text())
        self.assertEqual([len(data[r]) for r in ('train', 'evaluation', 'excluded')], [1, 3, 2])
        self.assertEqual(json.loads(data['train'][0]['completion'][0]['content']), {'meaning': None})

    def test_resealed_target_is_refused_before_loading_a_model(self):
        self.teachers()
        self.pilot()
        from sse_multivector.distillation_run import sha256
        path = self.root/'pilot/data.json'
        data = json.loads(path.read_text())
        data['train'][0]['completion'][0]['content'] = '{"meaning":"Invented target"}'
        path.write_text(json.dumps(data))
        manifest = self.root/'pilot/manifest.json'
        value = json.loads(manifest.read_text())
        value['data_sha256'] = sha256(path)
        manifest.write_text(json.dumps(value))
        config = dict(model='must-not-be-loaded', revision='a'*40, quantization='nf4',
            max_length=512, epochs=[1], batch_size=1, learning_rate=.001, seed=17,
            memory_budget_gib=8, reserve_gib=8)
        self.write('config.json', config)
        result = subprocess.run([sys.executable, '-m', 'sse_multivector.bootstrap_student_pilot',
            'train', '--config', str(self.root/'config.json'), '--data', str(self.root/'pilot'),
            '--output', str(self.root/'fit'), '--stage', 'train'], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('targets differ from reviewed teacher collection', result.stderr)
        self.assertFalse((self.root/'fit').exists())

    def test_native_generation_evaluation_preserves_selected_inputs_and_student_schema(self):
        self.teachers()
        self.pilot()
        from sse_multivector.distillation_run import sha256
        source = self.root/'bootstrap-evaluation'
        self.write('student-inputs.json', dict(prepared_experiment=dict(
            path=str(source), sha256=sha256(source/'experiment.json'))))
        teacher = self.show('bootstrap-evaluation')['cases'][0]
        spec = json.loads(self.spec.read_text())
        spec['prompt'] = dict(id='fixture-meaning-only-v1', path='pilot/student-prompt.txt')
        spec['dataset'] = dict(adapter='generic', path='student-inputs.json', select=[teacher['id']])
        schema = Path(__file__).parent/'distillation/bootstrap-pilot-meaning-v1.output.schema.json'
        spec['runner']['output_schema_path'] = str(schema)
        self.write('student-spec.json', spec)
        self.cli('prepare', 'student', '--spec', self.root/'student-spec.json')
        self.cli('run', 'student', env={'FAKE_RUNNER_PROMPT_RESPONSE': '{"meaning":"Plants"}'})
        result = self.show('student')['cases']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['inputs'], teacher['inputs'])
        self.assertEqual(result[0]['evidence'], teacher['evidence'])
        self.assertEqual(result[0]['parsed'], {'meaning': 'Plants'})
        self.assertIsNone(result[0]['baseline'])
        self.assertEqual(result[0]['prompt'], json.loads((self.root/'pilot/data.json').read_text())
                         ['evaluation'][0]['prompt'][0]['content'])


@unittest.skipUnless(os.environ.get('RUN_BOOTSTRAP_PILOT_GPU_TESTS') == '1', 'explicit CUDA integration run')
class BootstrapStudentPilotGPUIntegrationTests(unittest.TestCase):
    def test_causal_and_expert_adapters_fit_masked_targets_and_reload_in_fresh_processes(self):
        import torch
        from tokenizers.pre_tokenizers import ByteLevel
        from transformers import Qwen2Config, Qwen2ForCausalLM, Qwen2Tokenizer, Gemma4TextConfig, Gemma4ForCausalLM
        from sse_multivector import bootstrap_student_pilot as pilot
        from sse_multivector.distillation_run import write_json, read_json, encode_example, subject_training_model
        from safetensors.torch import load_file
        for kind in ('qwen', 'gemma_moe'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                torch.manual_seed(17)
                if kind == 'qwen':
                    model = Qwen2ForCausalLM(Qwen2Config(vocab_size=512, hidden_size=32,
                        intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
                        num_key_value_heads=1, max_position_embeddings=2048,
                        eos_token_id=2, pad_token_id=1, bos_token_id=2))
                else:
                    model = Gemma4ForCausalLM(Gemma4TextConfig(vocab_size=512, hidden_size=64,
                        intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                        num_key_value_heads=2, head_dim=16, layer_types=['sliding_attention', 'full_attention'],
                        sliding_window=32, max_position_embeddings=2048, hidden_size_per_layer_input=0,
                        enable_moe_block=True, num_experts=4, top_k_experts=2, moe_intermediate_size=32,
                        eos_token_id=2, pad_token_id=1, bos_token_id=2))
                model.save_pretrained(root/'base')
                words = ['[UNK]', '[PAD]', '[EOS]', *sorted(ByteLevel.alphabet())]
                tokenizer = Qwen2Tokenizer(vocab=dict(zip(words, range(len(words)))), merges=[],
                    unk_token='[UNK]', pad_token='[PAD]', eos_token='[EOS]')
                tokenizer.chat_template = ('{% for message in messages %}{{message["content"]}}'
                    '{% if message["role"] == "user" %}\nassistant\n{% else %}[EOS]{% endif %}{% endfor %}')
                tokenizer.save_pretrained(root/'base')
                text = 'Define the selected topic.\n{INPUT_JSON}'
                from hashlib import sha256
                prompt_hash = sha256(text.encode()).hexdigest()
                cases, producers = [], []
                for role in ('train', 'evaluation'):
                    inputs_ = dict(INPUT_JSON=json.dumps(dict(local=dict(post=role+' Plants', entry={}))))
                    receipt = dict(results_path='fixture-only', record_sha256=sha256(role.encode()).hexdigest())
                    cases.append(dict(experiment=role, case_id=role, prompt_id='fixture',
                        prompt_sha256=prompt_hash, input_sha256=pilot.digest(inputs_), inputs=inputs_,
                        answer=dict(meaning=None if role == 'train' else 'Plants',
                                    ambiguities=[], resolutions=[], evidence=[]),
                        evidence=dict(local=dict(note_id=role, number='1'), pubkey=role,
                                      role=role, split='train', application_allowed=False), receipt=receipt,
                        reviews=[dict(role='agent', current=True, verdict='accept')]))
                    producers.append(dict(experiment=role, prompt_id='fixture', cases=[dict(id=role, receipt=receipt)]))
                write_json(root/'bootstrap.json', dict(schema_version=1, cases=cases,
                    prompts={prompt_hash: dict(text=text, prompt_ids=['fixture'])}))
                write_json(root/'provenance.json', dict(schema_version=1, experiments=producers, inference_calls=0))
                pilot.prepare(root/'bootstrap.json', root/'provenance.json', root/'data')
                row = encode_example(tokenizer, read_json(root/'data/data.json')['train'][0], 2048)
                first = next(i for i,v in enumerate(row['labels']) if v != -100)
                self.assertGreater(first, 0)
                # The exact production suffix objective must equal complete
                # causal masked loss; preceding input tokens never become targets.
                model.to('cuda').eval()
                tensors = {k: torch.tensor([v], device='cuda') for k,v in row.items()}
                with torch.inference_mode():
                    full = model(**tensors).loss
                    partial = model(**tensors, logits_to_keep=torch.arange(first-1,
                        len(row['input_ids'])-1, device='cuda'), shift_labels=tensors['labels'][:, first:]).loss
                torch.testing.assert_close(partial, full, rtol=1e-6, atol=1e-6)
                del model, tensors
                torch.cuda.empty_cache()
                config = dict(model=str(root/'base'), revision='a'*40, quantization='nf4',
                    max_length=2048, epochs=[1,2], batch_size=1, learning_rate=.001,
                    seed=17, memory_budget_gib=8, reserve_gib=8)
                write_json(root/'config.json', config)
                reference = subject_training_model(dict(config, device='cuda', efficient_attention=True,
                    lora_target_modules='all-linear', lora_rank=16, lora_alpha=32,
                    gradient_checkpointing=True)).eval()
                evaluation_row = encode_example(tokenizer, read_json(root/'data/data.json')['evaluation'][0], 2048)
                tensors = {k: torch.tensor([v], device='cuda') for k,v in evaluation_row.items()}
                with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                    expected_baseline = reference(**tensors).loss.item()
                del reference, tensors
                torch.cuda.empty_cache()
                command = [sys.executable, '-m', 'sse_multivector.bootstrap_student_pilot', 'train',
                    '--config', str(root/'config.json'), '--data', str(root/'data'), '--output', str(root/'fit')]
                for stage in ('train', 'verify'):
                    result = subprocess.run(command+['--stage', stage], text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                report = read_json(root/'fit/report.json')
                self.assertTrue(report['complete'])
                self.assertNotEqual(report['training_pid'], report['verification_pid'])
                self.assertEqual(report['updates'], 2)
                self.assertAlmostEqual(report['baseline']['mean_token_loss'], expected_baseline, places=4)
                self.assertEqual(report['training_examples_seen'], 2)
                self.assertEqual(report['supervised_tokens'], 2*sum(v != -100 for v in row['labels']))
                self.assertEqual([c['epoch'] for c in report['checkpoints']], [1,2])
                self.assertTrue(all(c['reload_matches'] for c in report['checkpoints']))
                self.assertTrue(all([v['case_id'] for v in c['evaluation']['cases']] == ['evaluation']
                                    for c in report['checkpoints']))
                weights = load_file(root/'fit/checkpoints/epoch-2/adapter_model.safetensors')
                self.assertTrue(any(v.norm() > 0 for k,v in weights.items() if 'lora_B' in k))
                from sse_multivector.local_weight_model import LocalWeights
                from sse_multivector.distillation_run import sha256
                adapter = root/'fit/checkpoints/epoch-2'
                write_json(root/'native.json', dict(schema_version=1, kind='causal_lm',
                    model=config['model'], revision=config['revision'], quantization='nf4',
                    max_input_tokens=2048, max_new_tokens=8, memory_budget_gib=8, reserve_gib=8,
                    adapter=str(adapter), adapter_revision='local-epoch-2',
                    adapter_sha256=sha256(adapter/'adapter_model.safetensors')))
                native = LocalWeights(root/'native.json')
                reply = native.complete(dict(model=native.name, messages=read_json(root/'data/data.json')
                    ['evaluation'][0]['prompt'], max_tokens=8))
                self.assertIsInstance(reply['raw_text'], str)
                self.assertEqual(reply['model'], native.name)
                del native
                torch.cuda.empty_cache()


if __name__ == '__main__':
    unittest.main()
