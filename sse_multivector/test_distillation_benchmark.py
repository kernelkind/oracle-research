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

    def test_causal_capacity_can_supervise_a_complete_output_suffix(self):
        config = {**self.config(), 'architecture': 'causal_lm', 'method': 'lora',
                  'supervised_output_tokens': 64}
        distillation_benchmark.validate_config(config)
        for count in (0, 256, True):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, 'output suffix'):
                distillation_benchmark.validate_config({**config, 'supervised_output_tokens': count})
        with self.assertRaisesRegex(ValueError, 'causal'):
            distillation_benchmark.validate_config({**config, 'architecture': 'encoder'})

    def test_pointer_training_requires_its_pinned_native_configuration(self):
        config = {**self.config(), 'architecture': 'pointer', 'method': 'lora',
                  'quantization': 'nf4', 'pointer_config': 'diagnostic-kev9b.json'}
        distillation_benchmark.validate_config(config)
        del config['pointer_config']
        with self.assertRaisesRegex(ValueError, 'pointer_config'):
            distillation_benchmark.validate_config(config)

    def test_model_failure_automatically_exports_saved_measurements_and_failure_type(self):
        import json
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        torch = MagicMock()
        torch.cuda.get_device_properties.return_value = SimpleNamespace(total_memory=64*2**30)
        torch.cuda.get_device_name.return_value = 'Fixture GPU'
        modules = {'torch': torch, 'transformers': MagicMock(), 'peft': MagicMock(), 'ijson': None}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {**self.config(), 'architecture': 'causal_lm', 'method': 'lora'}
            write_json(root/'config.json', config)
            with (patch.dict('sys.modules', modules),
                  patch.object(distillation_benchmark, 'available_memory', return_value=64*2**30),
                  patch.object(distillation_benchmark.importlib.metadata, 'version', return_value='fixture'),
                  patch.object(distillation_benchmark, 'subject_training_model',
                               side_effect=ValueError('fixture model load failure'))):
                with self.assertRaisesRegex(ValueError, 'fixture model load failure'):
                    distillation_benchmark.run(root/'config.json', root/'benchmark')
            metadata = json.loads((root/'benchmark/publication/experiment.json').read_text())
            self.assertEqual(metadata['family'], 'performance')
            self.assertEqual(metadata['status'], 'failed')
            self.assertEqual(metadata['failure_type'], 'ValueError')


@unittest.skipUnless(os.environ.get("RUN_BENCHMARK_GPU_TESTS") == "1", "explicit CUDA integration run")
class BenchmarkGPUIntegrationTests(unittest.TestCase):
    def test_gemma_moe_adapts_all_experts_with_frozen_router_and_reloads(self):
        import torch
        from peft.tuners.lora.layer import ParamWrapper
        from transformers import Gemma4TextConfig, Gemma4ForCausalLM
        from sse_multivector import distillation_run
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = Gemma4TextConfig(vocab_size=2048, hidden_size=64, intermediate_size=128,
                num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                head_dim=16, layer_types=['sliding_attention', 'full_attention'],
                sliding_window=32, max_position_embeddings=128, hidden_size_per_layer_input=0,
                enable_moe_block=True, num_experts=4, top_k_experts=2, moe_intermediate_size=32)
            Gemma4ForCausalLM(config).save_pretrained(root/'base')
            training = dict(model=str(root/'base'), revision='a'*40, device='cuda',
                quantization='nf4', max_length=64, efficient_attention=True,
                lora_target_modules='all-linear', lora_rank=16, lora_alpha=32,
                gradient_checkpointing=True)
            model = distillation_run.subject_training_model(training)
            router = [p for n, p in model.named_parameters() if '.router.' in n]
            self.assertTrue(router)
            self.assertFalse(any(p.requires_grad for p in router))
            self.assertFalse(any('.router.' in n and 'lora_' in n for n, _ in model.named_parameters()))
            targets = model.peft_config['default'].target_parameters
            self.assertEqual(len(targets), 4)
            for suffix in ('.experts.gate_up_proj', '.experts.down_proj'):
                self.assertEqual(sum(n.endswith(suffix) for n in targets), 2)
            wrappers = [m for m in model.modules() if isinstance(m, ParamWrapper)]
            self.assertEqual(len(wrappers), 4)
            self.assertTrue(all(m.r['default'] == 2 and m.lora_alpha['default'] == 32 for m in wrappers))
            trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
            self.assertTrue(all('lora_' in n and p.dtype == torch.float32 for n, p in trainable))
            before = {n: p.detach().clone() for n, p in trainable}
            tokens = torch.arange(5, 21, device='cuda').unsqueeze(0)
            optimizer = torch.optim.AdamW([p for _, p in trainable], lr=1e-3)
            with torch.autocast('cuda', dtype=torch.bfloat16):
                loss = model(input_ids=tokens, labels=tokens).loss
            loss.backward()
            self.assertTrue(torch.isfinite(loss))
            self.assertTrue(all(torch.isfinite(m.lora_B['default'].weight.grad).all()
                                and m.lora_B['default'].weight.grad.norm() > 0 for m in wrappers))
            optimizer.step()
            self.assertTrue(any(not torch.equal(before[n], p) for n, p in trainable))
            model.eval()
            with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                expected = model(input_ids=tokens).logits.cpu()
            model.save_pretrained(root/'adapter')
            del optimizer, model, trainable, router, wrappers
            torch.cuda.empty_cache()
            reloaded = distillation_run.subject_training_model(training, root/'adapter').eval()
            with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                observed = reloaded(input_ids=tokens).logits.cpu()
            torch.testing.assert_close(observed, expected, rtol=1e-4, atol=1e-4)

    def test_causal_output_suffix_trains_and_reloads_native_nf4_adapters(self):
        import torch
        from unittest.mock import patch
        from transformers import Qwen2Config, Qwen2ForCausalLM
        self.assertTrue(torch.cuda.is_available())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = Qwen2ForCausalLM(Qwen2Config(vocab_size=2048, hidden_size=64,
                intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                num_key_value_heads=2, max_position_embeddings=256))
            model.save_pretrained(root/'base')
            del model
            config = {**DistillationBenchmarkTests().config(), 'model': str(root/'base'),
                'architecture': 'causal_lm', 'method': 'lora', 'quantization': 'nf4',
                'lengths': [32], 'inference_batch_sizes': [1], 'steps': 1,
                'supervised_output_tokens': 8}
            path = root/'config.json'
            write_json(path, config)
            projections, loaded = [], []
            native_loader = distillation_benchmark.subject_training_model
            def capture_model(*args, **kwargs):
                native = native_loader(*args, **kwargs)
                native.get_output_embeddings().register_forward_hook(
                    lambda module, args, output: projections.append(output.shape[-2]))
                loaded.append(native)
                return native
            with patch.object(distillation_benchmark, 'subject_training_model', side_effect=capture_model):
                trained = distillation_benchmark.run(path, root/'benchmark', stage='train')
            self.assertEqual(projections[:2], [8, 8],
                             'unsupervised prefix positions need no vocabulary projection')
            self.assertTrue(trained['checkpoint_saved'])
            self.assertEqual(trained['training'][0]['supervised_tokens_per_example'], 8)
            self.assertIn('causal', trained['workload'])
            # A newly initialized 2,048-word model has a much larger native
            # token loss than a five-label classifier. Catch the old readout
            # being timed while merely reporting a different workload.
            self.assertGreater(trained['training'][0]['losses'][0], 4.6)
            # The smaller projection must preserve the complete native masked
            # causal loss, including the first output token's preceding state.
            native = loaded[0].eval()
            ids = torch.arange(20, 52, device='cuda').unsqueeze(0)
            labels = ids.clone()
            labels[:, :-8] = -100
            with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                full = native(input_ids=ids, labels=labels).loss
                selected = native(input_ids=ids, labels=labels,
                                  logits_to_keep=torch.arange(23, 31, device='cuda'),
                                  shift_labels=labels[:, -8:]).loss
            torch.testing.assert_close(selected, full, rtol=1e-4, atol=1e-4)
            verified = distillation_benchmark.run(path, root/'benchmark', stage='verify')
            self.assertTrue(verified['complete'])
            self.assertTrue(verified['reload_matches'])

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
