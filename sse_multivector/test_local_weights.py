"""Native checkpoint identity and text-only multimodal loading checks."""
import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import local_weight_model, distillation_run


class LocalWeightTests(unittest.TestCase):
    def test_choice_prompt_retains_state_and_order_for_both_readouts(self):
        state = 'All original instructions\n{"A": [], "B": []}'
        question = {'instructions': 'Apply the state',
                    'criteria': {'second': 'Second meaning', 'first': 'First meaning'}}
        for readout in ('generation', 'options'):
            prompt = local_weight_model.choice_prompt(state, question, readout)
            self.assertTrue(prompt.startswith(state))
            self.assertIn('(A) second: Second meaning\n(B) first: First meaning', prompt)
        with self.assertRaises(ValueError):
            local_weight_model.choice_prompt(state, question, 'unknown')
        with self.assertRaises(ValueError):
            local_weight_model.choice_prompt(state, {**question, 'criteria': {'only': 'One'}}, 'options')

    def test_pointer_identity_names_the_learned_adapter(self):
        config = {'kind': 'pointer', 'model': 'Qwen/base', 'revision': 'a'*40,
                  'adapter': 'owner/decision', 'adapter_revision': 'b'*40}
        self.assertEqual(local_weight_model.checkpoint_name(config, 'c'*64),
                         'owner/decision/'+'b'*40+'/'+'c'*64)


@unittest.skipUnless(os.environ.get('RUN_LOCAL_WEIGHT_TESTS') == '1', 'native weight integration environment')
class LocalWeightIntegrationTests(unittest.TestCase):
    def test_decider_uses_native_segmented_tokens_without_chat_wrapping(self):
        import importlib.util
        from types import SimpleNamespace
        import torch
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
        tokenizer = Tokenizer(models.WordLevel(
            {'[UNK]': 0, '[PAD]': 1, 'A': 2, 'B': 3, 'C': 4, 'pair': 5}, unk_token='[UNK]'))
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer, unk_token='[UNK]',
            pad_token='[PAD]', chat_template="{% for m in messages %}{{ m['content'] }}{% endfor %}\n")
        spec = importlib.util.spec_from_file_location('decider_prompt',
            Path('target/shr-student-diagnostics-v1/upstream/decider/prompt.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        backend = object.__new__(local_weight_model.LocalWeights)
        question = {'instructions': 'Compare pair', 'criteria': {'left': 'Left broader', 'right': 'Right broader'},
                    'output_field': 'relation', 'empty_fields': ['reason']}
        backend.config = {'kind': 'causal_lm', 'readout': 'options', 'prompt_layout': 'decider',
            'reserve_gib': 1, 'quantization': 'none', 'max_input_tokens': 512,
            'max_new_tokens': 8, 'question': question}
        backend.config_sha256, backend.name = 'a'*64, 'tiny-native-decider'
        backend.tokenizer = tokenizer
        backend.model = Qwen2ForCausalLM(Qwen2Config(vocab_size=16, hidden_size=32,
            intermediate_size=64, num_hidden_layers=1, num_attention_heads=2,
            num_key_value_heads=1, max_position_embeddings=512)).cuda().eval()
        backend.head = backend.encoder = backend.choice_encoder = None
        backend.decider_encoder = module.build
        body = {'model': backend.name, 'messages': [{'role': 'user', 'content': 'pair\n'}]}
        native = module.build(SimpleNamespace(context='pair\n', qs=[SimpleNamespace(text=question['instructions'],
            options=['left: Left broader', 'right: Right broader'], gold=0)]), tokenizer,
            rng=SimpleNamespace(shuffle=lambda options: None), max_options=2, max_ctx_tokens=512)
        reply = backend.complete(body)
        self.assertEqual(reply['metadata']['input_tokens'], len(native['ids']))
        ids = torch.tensor([native['ids']], device='cuda')
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            logits = backend.model(input_ids=ids, attention_mask=torch.ones_like(ids),
                use_cache=False, logits_to_keep=1).logits[0, -1, [2, 3]].float()
        torch.testing.assert_close(torch.tensor(list(reply['metadata']['probabilities'].values())),
                                   logits.softmax(-1).cpu())
        backend.config['max_input_tokens'] = 2
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            backend.complete(body)

    def test_causal_adapter_loads_exact_saved_weights_with_text_prefix_conversion(self):
        import torch
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from safetensors.torch import load_file, save_file
        from tokenizers import Tokenizer, models
        from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = Qwen2ForCausalLM(Qwen2Config(vocab_size=16, hidden_size=32,
                intermediate_size=64, num_hidden_layers=1, num_attention_heads=2,
                num_key_value_heads=1, max_position_embeddings=512))
            base.save_pretrained(root/'base')
            tokenizer = PreTrainedTokenizerFast(tokenizer_object=Tokenizer(models.WordLevel(
                {'[UNK]': 0, '[PAD]': 1, 'A': 2, 'B': 3}, unk_token='[UNK]')),
                unk_token='[UNK]', pad_token='[PAD]')
            tokenizer.save_pretrained(root/'base')
            base = Qwen2ForCausalLM.from_pretrained(root/'base')
            tuned = get_peft_model(base, LoraConfig(task_type='CAUSAL_LM',
                target_modules=['q_proj', 'v_proj'], r=2, lora_alpha=4))
            with torch.no_grad():
                for name, tensor in tuned.named_parameters():
                    if 'lora_B' in name:
                        tensor.fill_(0.25)
            expected = {k: v.clone() for k, v in get_peft_model_state_dict(tuned).items()}
            tuned.save_pretrained(root/'adapter')
            weights = root/'adapter/adapter_model.safetensors'
            saved = load_file(weights)
            save_file({k.replace('base_model.model.model.', 'base_model.model.model.language_model.'): v
                       for k, v in saved.items()}, weights)
            config = {'kind': 'causal_lm', 'model': str(root/'base'), 'revision': 'a'*40,
                'adapter': str(root/'adapter'), 'adapter_revision': 'b'*40,
                'adapter_sha256': distillation_run.sha256(weights),
                'adapter_key_mapping': {r'^model\.language_model\.': 'model.'},
                'quantization': 'none', 'max_input_tokens': 512, 'max_new_tokens': 8,
                'memory_budget_gib': 2, 'reserve_gib': 1}
            path = root/'config.json'
            path.write_text(json.dumps(config))
            actual = local_weight_model.LocalWeights(path)
            self.assertTrue(hasattr(actual.model, 'peft_config'), 'causal checkpoint must load its learned adapter')
            observed = get_peft_model_state_dict(actual.model)
            self.assertEqual(set(observed), set(expected))
            for name in expected:
                torch.testing.assert_close(observed[name].cpu(), expected[name], rtol=0, atol=0)
            self.assertTrue(actual.name.startswith(str(root/'adapter')+'/'))
            path.write_text(json.dumps({**config, 'adapter_sha256': '0'*64}))
            with self.assertRaisesRegex(ValueError, 'adapter.*hash'):
                local_weight_model.LocalWeights(path)

    def test_complete_scores_native_single_token_options_and_preserves_mapping(self):
        import torch
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
        vocabulary = {word: i for i, word in enumerate(
            ['[UNK]', '[PAD]', 'A', 'B', 'C', 'D', 'E', 'pair', 'broader'])}
        tokenizer = Tokenizer(models.WordLevel(vocabulary, unk_token='[UNK]'))
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer, unk_token='[UNK]',
            pad_token='[PAD]', chat_template="{% for m in messages %}{{ m['content'] }}{% endfor %}\n")
        backend = object.__new__(local_weight_model.LocalWeights)
        backend.config = {'kind': 'causal_lm', 'readout': 'options', 'reserve_gib': 1,
            'quantization': 'none', 'max_input_tokens': 512, 'max_new_tokens': 8,
            'question': {'instructions': 'Compare pair',
                'criteria': {'left': 'left broader', 'right': 'right broader', 'same': 'same pair'},
                'output_field': 'relation', 'empty_fields': ['reason']}}
        backend.config_sha256, backend.name = 'a'*64, 'tiny-options'
        backend.tokenizer = tokenizer
        torch.manual_seed(17)
        backend.model = Qwen2ForCausalLM(Qwen2Config(vocab_size=16, hidden_size=32,
            intermediate_size=64, num_hidden_layers=1, num_attention_heads=2,
            num_key_value_heads=1, max_position_embeddings=512)).cuda().eval()
        backend.encoder = backend.head = None
        body = {'model': backend.name, 'messages': [{'role': 'user', 'content': 'pair'}]}
        with patch.object(backend.model, 'generate', side_effect=AssertionError('must not decode')):
            reply = backend.complete(body)
        prompt = reply['metadata']['choice_prompt']
        self.assertTrue(prompt.startswith('pair'))
        ids = tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}],
            add_generation_prompt=True, return_dict=True, return_tensors='pt')
        ids = {k: v.cuda() for k, v in ids.items() if k != 'token_type_ids'}
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            logits = backend.model(**ids, use_cache=False, logits_to_keep=1).logits[0, -1].float()
        codes = [tokenizer.encode(c, add_special_tokens=False)[0] for c in 'ABC']
        expected = logits[codes].softmax(-1).cpu().tolist()
        observed = reply['metadata']['probabilities']
        self.assertEqual(list(observed), ['left', 'right', 'same'])
        torch.testing.assert_close(torch.tensor(list(observed.values())), torch.tensor(expected))
        self.assertEqual(reply['raw_text'], json.dumps(
            {'relation': list(observed)[logits[codes].argmax().item()], 'reason': ''}))
        self.assertEqual(reply['usage']['output'], 0)
        with patch.object(tokenizer, 'encode', return_value=[2, 3]):
            with self.assertRaisesRegex(ValueError, 'single tokens'):
                backend.complete(body)
        backend.config['prompt_layout'] = 'schema'
        import sys
        upstream = Path('target/shr-student-prep-v1/huggingface/hub/models--bespokelabs--Bespoke-Nimble-9B/snapshots/bd792f44ec8e265be861bfcdf4e05967ffe0e858')
        sys.path.insert(0, str(upstream.resolve()))
        from serving_schema import prepare_prompts
        backend.choice_encoder = prepare_prompts
        question = backend.config['question']
        schema = {question['output_field']: {'type': 'enum', 'description': question['instructions'],
            'choices': list(question['criteria']), 'choice_descriptions': question['criteria']}}
        prepared = prepare_prompts(tokenizer, 'pair', schema, 512)
        reply = backend.complete(body)
        self.assertEqual(reply['metadata']['input_tokens'], len(prepared.full_ids[0]))
        native = torch.tensor([prepared.full_ids[0]], device='cuda')
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            z = backend.model(input_ids=native, attention_mask=torch.ones_like(native),
                use_cache=False, logits_to_keep=1).logits[0, -1, prepared.candidate_ids[0]].float()
        torch.testing.assert_close(torch.tensor(list(reply['metadata']['probabilities'].values())),
                                   z.softmax(-1).cpu())
        backend.config['max_input_tokens'] = 2
        with self.assertRaisesRegex(ValueError, 'exceeds|limit'):
            backend.complete(body)

    def test_gemma_unified_loads_complete_text_weights_without_multimodal_modules(self):
        import torch
        from transformers import (Gemma4UnifiedConfig, Gemma4UnifiedTextConfig,
                                  Gemma4UnifiedForConditionalGeneration)
        text = Gemma4UnifiedTextConfig(vocab_size=2048, hidden_size=64, intermediate_size=128,
            num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
            num_global_key_value_heads=1, head_dim=16, global_head_dim=16,
            layer_types=['sliding_attention', 'full_attention'], sliding_window=32,
            max_position_embeddings=128, hidden_size_per_layer_input=0)
        config = Gemma4UnifiedConfig(text_config=text,
            vision_config={'mm_embed_dim': 64, 'output_proj_dims': 64, 'mm_posemb_size': 16},
            audio_config={'audio_embed_dim': 8})
        original = Gemma4UnifiedForConditionalGeneration(config).eval()
        tokens = torch.arange(5, 21).unsqueeze(0)
        with torch.inference_mode():
            expected = original(input_ids=tokens).logits
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            original.save_pretrained(path)
            actual = distillation_run.load_model({'model': str(path), 'revision': 'a'*40,
                'device': 'cpu', 'quantization': 'none', 'max_length': 32, 'efficient_attention': True}).eval()
            self.assertEqual(actual.config.model_type, 'gemma4_unified_text')
            self.assertFalse(any('vision' in name or 'audio' in name for name, _ in actual.named_parameters()))
            with torch.inference_mode():
                observed = actual(input_ids=tokens).logits
            torch.testing.assert_close(observed, expected, rtol=1e-5, atol=1e-5)


if __name__ == '__main__':
    unittest.main()
