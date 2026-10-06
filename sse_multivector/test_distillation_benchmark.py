"""Exercise benchmark admission before any model or CUDA allocation."""
import os
import tempfile
import unittest
from pathlib import Path

from sse_multivector import distillation_benchmark
from sse_multivector.distillation_run import write_json


class DistillationBenchmarkTests(unittest.TestCase):
    def config(self):
        return dict(model="jhu-clsp/ettin-encoder-400m", revision="a" * 40,
                    architecture="encoder", method="full", lengths=[256, 512],
                    train_batch_size=1, inference_batch_sizes=[1, 4], steps=4,
                    warmup_steps=1, repetitions=3, learning_rate=2e-5,
                    memory_budget_gib=8, reserve_gib=8, seed=17)

    def test_unpinned_model_is_rejected(self):
        config = self.config()
        config["revision"] = "main"
        with self.assertRaisesRegex(ValueError, "immutable"):
            distillation_benchmark.validate_config(config)

    def test_capacity_checks_require_synthetic_workload_lengths(self):
        config = self.config()
        config["lengths"] = [256, 0]
        with self.assertRaisesRegex(ValueError, "positive"):
            distillation_benchmark.validate_config(config)

    def test_admission_preserves_memory_for_existing_work(self):
        config = self.config()
        with self.assertRaisesRegex(ValueError, "available system memory"):
            distillation_benchmark.admit(config, 15 * 2 ** 30)
        distillation_benchmark.admit(config, 17 * 2 ** 30)

    def test_decoder_full_training_is_not_silently_substituted_for_lora(self):
        config = self.config()
        config["architecture"] = "causal_lm"
        with self.assertRaisesRegex(ValueError, "LoRA"):
            distillation_benchmark.validate_config(config)

    def test_nf4_is_an_explicit_causal_lora_workload(self):
        config = {**self.config(), "architecture": "causal_lm", "method": "lora", "quantization": "nf4"}
        distillation_benchmark.validate_config(config)
        config["architecture"] = "encoder"
        with self.assertRaisesRegex(ValueError, "causal"):
            distillation_benchmark.validate_config(config)

    def test_pointer_training_requires_its_pinned_native_configuration(self):
        config = {**self.config(), 'architecture': 'pointer', 'method': 'lora',
                  'quantization': 'nf4', 'pointer_config': 'diagnostic-kev9b.json'}
        distillation_benchmark.validate_config(config)
        del config['pointer_config']
        with self.assertRaisesRegex(ValueError, 'pointer_config'):
            distillation_benchmark.validate_config(config)


@unittest.skipUnless(os.environ.get("RUN_BENCHMARK_GPU_TESTS") == "1", "explicit CUDA integration run")
class BenchmarkGPUIntegrationTests(unittest.TestCase):
    def test_pointer_optimization_checkpoints_the_extracted_quantized_backbone(self):
        import sys
        import torch
        from types import SimpleNamespace
        from unittest.mock import patch
        from transformers import Qwen2Config, Qwen2ForCausalLM
        from peft import LoraConfig, get_peft_model
        from sse_multivector.distillation_run import load_model, read_json, sha256
        source = read_json(Path(__file__).parent / 'distillation/diagnostic-kev9b.json')
        upstream = Path(source['upstream_path'])
        self.assertEqual(sha256(upstream/'kev/model.py'), source['upstream_model_sha256'])
        sys.path.insert(0, str(upstream))
        from kev.model import PointerHead
        self.assertTrue(torch.cuda.is_available())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tiny = Qwen2ForCausalLM(Qwen2Config(vocab_size=2048, hidden_size=64,
                intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                num_key_value_heads=2, max_position_embeddings=256))
            tiny.save_pretrained(root/'base')
            del tiny
            config = {**DistillationBenchmarkTests().config(), 'model': str(root/'base'),
                'architecture': 'pointer', 'method': 'lora', 'quantization': 'nf4',
                'lengths': [32], 'inference_batch_sizes': [1, 2], 'steps': 2,
                'memory_budget_gib': 2, 'pointer_config': 'pointer.json'}
            write_json(root/'pointer.json', {**source, **{k: config[k] for k in
                       ('model', 'revision', 'quantization', 'memory_budget_gib', 'reserve_gib')}})
            write_json(root/'config.json', config)
            loaded = []
            def native_pointer(path):
                base = load_model(dict(config, device='cuda', max_length=32))
                model = get_peft_model(base.model, LoraConfig(task_type='FEATURE_EXTRACTION',
                                      target_modules='all-linear', r=16, lora_alpha=32))
                loaded.append(model)
                return SimpleNamespace(model=model, head=PointerHead(64, dp=16).to('cuda'))
            with patch('sse_multivector.local_weight_model.LocalWeights', side_effect=native_pointer):
                trained = distillation_benchmark.run(root/'config.json', root/'benchmark', stage='train')
                self.assertFalse(trained['complete'])
                self.assertTrue(trained['checkpoint_saved'])
                result = distillation_benchmark.run(root/'config.json', root/'benchmark', stage='verify')
            self.assertTrue(result['complete'])
            self.assertTrue(result['reload_matches'])
            self.assertTrue(all(m.is_gradient_checkpointing for m in loaded),
                            'extracted NF4 backbones must checkpoint training activations')

    def test_nf4_counts_logical_parameters_and_verifies_a_real_checkpoint(self):
        import torch
        from transformers import Qwen2Config, Qwen2ForCausalLM
        self.assertTrue(torch.cuda.is_available())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = Qwen2ForCausalLM(Qwen2Config(vocab_size=2048, hidden_size=64,
                intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                num_key_value_heads=2, max_position_embeddings=256))
            model.save_pretrained(root / "base")
            del model
            config = {**DistillationBenchmarkTests().config(), "model": str(root / "base"),
                "architecture": "causal_lm", "method": "lora", "quantization": "nf4",
                "lengths": [32], "inference_batch_sizes": [1, 2], "steps": 2}
            path = root / "config.json"
            write_json(path, config)
            result = distillation_benchmark.run(path, root / "benchmark")
            self.assertTrue(result["complete"])
            self.assertTrue(result["reload_matches"])
            self.assertEqual(len(result["inference"]), 2)
            self.assertGreater(result["parameters"]["total"], result["parameters"]["stored_tensor_elements"])


if __name__ == "__main__":
    unittest.main()
