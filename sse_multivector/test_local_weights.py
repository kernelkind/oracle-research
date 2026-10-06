"""Native checkpoint identity and text-only multimodal loading checks."""
import os
from pathlib import Path
import tempfile
import unittest

from sse_multivector import local_weight_model, distillation_run


class LocalWeightTests(unittest.TestCase):
    def test_pointer_identity_names_the_learned_adapter(self):
        config = {'kind': 'pointer', 'model': 'Qwen/base', 'revision': 'a'*40,
                  'adapter': 'owner/decision', 'adapter_revision': 'b'*40}
        self.assertEqual(local_weight_model.checkpoint_name(config, 'c'*64),
                         'owner/decision/'+'b'*40+'/'+'c'*64)


@unittest.skipUnless(os.environ.get('RUN_LOCAL_WEIGHT_TESTS') == '1', 'native weight integration environment')
class LocalWeightIntegrationTests(unittest.TestCase):
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
