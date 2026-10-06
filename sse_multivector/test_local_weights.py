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
        backend.config['max_input_tokens'] = 2
        with self.assertRaisesRegex(ValueError, 'exceeds'):
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
