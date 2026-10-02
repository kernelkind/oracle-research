"""Candidate architecture checks using tiny weights, through production paths."""
import tempfile
import unittest
import subprocess
import sys
import os
from unittest.mock import patch
from pathlib import Path

from sse_multivector import distillation_run as runner


class ChatTemplateTests(unittest.TestCase):
    def test_training_uses_disabled_thinking_prefix_and_native_turn_end(self):
        from tokenizers import Tokenizer, models, pre_tokenizers
        from transformers import PreTrainedTokenizerFast
        special = ["<unk>", "<user>", "<model>", "<thought>", "</thought>", "<turn>", "<eos>"]
        backend = Tokenizer(models.WordLevel({s: i for i, s in enumerate(special + ["question", "answer"])},
                                             unk_token="<unk>"))
        backend.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
        # Gemma's template adds an empty thought channel only to generation prompts.
        template = ("{% for m in messages %}{{ '<user>' if m.role == 'user' else '<model>' }}"
                    "{{ m.content }}<turn>{% endfor %}{% if add_generation_prompt %}<model>"
                    "{% if not enable_thinking %}<thought></thought>{% endif %}{% endif %}")
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, eos_token="<eos>",
            additional_special_tokens=special, chat_template=template)
        row = {"prompt": [{"role": "user", "content": "question"}],
               "completion": [{"role": "assistant", "content": "answer"}]}
        prefix = tokenizer.apply_chat_template(row["prompt"], add_generation_prompt=True,
            enable_thinking=False, return_dict=False)
        encoded = runner.encode_example(tokenizer, row, 100)
        self.assertEqual(encoded["input_ids"][:len(prefix)], prefix)
        self.assertEqual(encoded["labels"][:len(prefix)], [-100] * len(prefix))
        self.assertEqual(encoded["labels"][len(prefix):], tokenizer.encode("answer<turn>", add_special_tokens=False))
        data = {"train": [{**row, "task": "subjects"}, {**row, "task": "mask"}],
                "evaluation": [{"messages": row["prompt"]}]}
        config = {"max_length": 100, "max_new_tokens": {"subjects": 10, "mask": 5}}
        report = runner.preflight(tokenizer, data, config)
        self.assertEqual(report["training"]["subjects"]["examples"], 1)
        config["max_new_tokens"]["subjects"] = 99
        with self.assertRaisesRegex(ValueError, "allowance"):
            runner.preflight(tokenizer, data, config)


class GPUPackageTests(unittest.TestCase):
    def test_cuda_attention_can_be_imported_without_affecting_cpu_process(self):
        import importlib.util
        self.assertIsNone(importlib.util.find_spec("fla"))
        subprocess.run([sys.executable, "-c", "from sse_multivector.distillation_run import load_gpu_packages; "
            "load_gpu_packages({'device': 'cuda'}); "
            "from fla.ops.gated_delta_rule import chunk_gated_delta_rule, fused_recurrent_gated_delta_rule; "
            "from importlib.metadata import version; assert version('fla-core') == '0.5.2'"],
            check=True, timeout=60,
            env={k: v for k, v in os.environ.items() if k != "DISTILLATION_GPU_PACKAGES"})


class CandidateArchitectureTests(unittest.TestCase):
    def assert_batch_matches_single(self, model, tokenizer, config):
        messages = [[{"role": "user", "content": text}] for text in
                    ("Tea", "Tea tastes good.", "Tea is a drink.", "Tea tastes good. Only tea is named.")]
        config = {**config, "max_new_tokens": {"subjects": 8, "mask": 8}}
        with patch.object(model, "generate", wraps=model.generate) as calls:
            batched = runner.generate_batch(model, tokenizer, messages, config, "mask")
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(calls.call_args.kwargs["input_ids"].shape[0], 4)
        for prompt, answer in zip(messages, batched["answers"]):
            single = runner.generate(model, tokenizer, prompt, config, "mask")
            self.assertEqual(answer, {key: single[key] for key in ("raw", "tokens", "truncated")})
        subject_config = {**config, "evaluation_tasks": ["subjects"],
                          "subject_batching": {"budget_bytes": 16*1024*1024, "workspace_bytes": 0,
                                               "prefill_bytes_per_token": 1024, "attention_matrix_count": 4}}
        data = {"evaluation": [{"note_id": str(i), "messages": prompt} for i, prompt in enumerate(messages)],
                "references": {str(i): {"text": prompt[0]["content"]} for i, prompt in enumerate(messages)}}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            with patch.object(model, "generate", wraps=model.generate) as calls:
                results = runner.evaluate(model, tokenizer, data, subject_config, output)
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(calls.call_args.kwargs["input_ids"].shape[0], 4)
            self.assertEqual([row["note_id"] for row in results], [str(i) for i in range(4)])
            self.assertFalse(list(output.glob("note-*/masks-*.json")))
            for i, prompt in enumerate(messages):
                saved = runner.read_json(output / f"note-{i:04}/subjects.json")
                single = runner.generate(model, tokenizer, prompt, config, "subjects")
                self.assertEqual(saved["answer"], {key: single[key] for key in ("raw", "tokens", "truncated")})
                self.assertTrue((output / f"note-{i:04}/subjects-result.json").exists())
            self.assertTrue(runner.verify_saved(output))

    def test_text_weights_training_checkpointing_and_reload(self):
        import torch
        from safetensors.torch import save_file
        from transformers import (Gemma4Config, Gemma4TextConfig, Gemma4ForCausalLM,
            Qwen3_5Config, Qwen3_5TextConfig, Qwen3_5ForCausalLM)
        from sse_multivector import test_distillation_run as fixtures
        fixtures.TinyWorkflowTests.setUpClass()
        try:
            fixture = fixtures.TinyWorkflowTests
            common = dict(vocab_size=len(fixture.tokenizer), hidden_size=32, intermediate_size=64,
                num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1, head_dim=16,
                max_position_embeddings=512, eos_token_id=fixture.tokenizer.eos_token_id,
                pad_token_id=fixture.tokenizer.pad_token_id, bos_token_id=None)
            variants = [
                ("qwen", Qwen3_5ForCausalLM, Qwen3_5Config, Qwen3_5TextConfig(**common,
                    layer_types=["linear_attention", "full_attention"], linear_key_head_dim=16,
                    linear_value_head_dim=16, linear_num_key_heads=1, linear_num_value_heads=2,
                    rope_parameters={"rope_type": "default", "rope_theta": 10000.,
                                     "partial_rotary_factor": 1., "mrope_section": [2, 3, 3]})),
            ]
            for moe in (False, True):
                variants.append(("gemma-moe" if moe else "gemma-dense", Gemma4ForCausalLM, Gemma4Config,
                    Gemma4TextConfig(**common, global_head_dim=16, num_global_key_value_heads=1,
                        layer_types=["sliding_attention", "full_attention"], sliding_window=64,
                        attention_k_eq_v=True, hidden_size_per_layer_input=0, enable_moe_block=moe,
                        num_experts=4 if moe else None, top_k_experts=2 if moe else None,
                        moe_intermediate_size=32 if moe else None)))
            with tempfile.TemporaryDirectory() as temporary:
                for name, model_class, root_class, text_config in variants:
                    with self.subTest(candidate=name):
                        root = Path(temporary) / name
                        root.mkdir()
                        original = model_class(text_config)
                        root_class(text_config=text_config).save_pretrained(root)
                        # The published checkpoints nest the text model under language_model.
                        state = {k.replace("model.", "model.language_model.", 1) if k.startswith("model.") else k:
                                 v.detach().clone() for k, v in original.state_dict().items()}
                        save_file(state, root / "model.safetensors")
                        original.generation_config.save_pretrained(root)
                        fixture.tokenizer.save_pretrained(root)
                        config = {**fixture.config, "model": str(root), "max_steps": 2, "save_steps": 1,
                                  "gradient_checkpointing": True, "lora_target_modules":
                                  ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
                                   "in_proj_qkv", "in_proj_z", "in_proj_b", "in_proj_a", "out_proj"]}
                        loaded = runner.load_model(config)
                        self.assertEqual(type(loaded), model_class)
                        for key, value in original.state_dict().items():
                            self.assertTrue(torch.equal(value, loaded.state_dict()[key]), key)
                        self.assert_batch_matches_single(loaded, fixture.tokenizer, config)
                        del loaded, original
                        data = runner.load_data(config["data"], config["mask_prompt"])
                        output = root / "run"
                        output.mkdir()
                        trained = runner.train(config, fixture.tokenizer, data, output)
                        self.assertTrue(runner.read_json(output / "adapter/training.json")["reload_matches"])
                        self.assertTrue(runner.read_json(output / "adapter/training.json")["gradient_checkpointing"])
                        changed = [p for n, p in trained.named_parameters() if "lora_B" in n]
                        self.assertTrue(any(torch.count_nonzero(p).item() for p in changed))
                        self.assertFalse(any("experts" in n or "router" in n
                                             for n, p in trained.named_parameters() if p.requires_grad))
                        self.assert_batch_matches_single(trained, fixture.tokenizer, config)
                        del trained
        finally:
            fixtures.TinyWorkflowTests.tearDownClass()


if __name__ == "__main__":
    unittest.main()
