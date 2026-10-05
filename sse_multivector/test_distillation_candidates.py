"""Candidate architecture checks using tiny weights, through production paths."""
import tempfile
import unittest
import subprocess
import sys
import os
import copy
from unittest.mock import patch
from pathlib import Path

from sse_multivector import distillation_run as runner


class ChatTemplateTests(unittest.TestCase):
    def test_efficient_attention_excludes_math_and_restores_backend_flags(self):
        import torch
        flags = lambda: (torch.backends.cuda.flash_sdp_enabled(),
                         torch.backends.cuda.mem_efficient_sdp_enabled(),
                         torch.backends.cuda.math_sdp_enabled(), torch.backends.cuda.cudnn_sdp_enabled())
        original = flags()
        with self.assertRaisesRegex(RuntimeError, "interrupted forward"):
            with runner.attention_context({"device": "cuda", "efficient_attention": True}):
                self.assertEqual(flags(), (True, True, False, False))
                raise RuntimeError("interrupted forward")
        self.assertEqual(flags(), original)
        with runner.attention_context({"device": "cpu", "efficient_attention": True}):
            self.assertEqual(flags(), original)

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
        subprocess.run([sys.executable, "-c", "from sse_multivector.distillation_run import load_gpu_packages; "
            "load_gpu_packages({'device': 'cuda'}); "
            "from liger_kernel.transformers.monkey_patch import apply_liger_kernel_to_gemma4_text, "
            "apply_liger_kernel_to_qwen3_5; "
            "from importlib.metadata import version; assert version('liger-kernel') == '0.8.4'"],
            check=True, timeout=60)


class FusedLossTests(unittest.TestCase):
    def test_training_forward_matches_native_loss_and_adapter_gradients(self):
        # GPU-package imports cache FLA modules. Keep that state out of the CPU
        # regression interpreter even after its search path has been restored.
        subprocess.run([sys.executable, "-c", "from sse_multivector.test_distillation_candidates import "
            "FusedLossTests; FusedLossTests().check_training_forward_matches_native_loss_and_adapter_gradients()"],
            check=True, timeout=120)

    def check_training_forward_matches_native_loss_and_adapter_gradients(self):
        """Exercise real Liger forwards/PEFT; replace only its CUDA loss kernel.

        CPU reference loss tests integration, masking, softcap, weighting and
        restoration. Actual Triton numerical agreement still requires a GPU.
        """
        import torch
        from transformers import (Gemma4TextConfig, Gemma4ForCausalLM,
                                  Qwen3_5TextConfig, Qwen3_5ForCausalLM)
        from sse_multivector import test_distillation_run as fixtures
        # Import the native CPU Qwen implementation before exposing FLA kernels.
        fixtures.TinyWorkflowTests.setUpClass()
        try:
            fixture = fixtures.TinyWorkflowTests
            common = dict(vocab_size=len(fixture.tokenizer), hidden_size=32, intermediate_size=64,
                num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1, head_dim=16,
                max_position_embeddings=512, eos_token_id=fixture.tokenizer.eos_token_id,
                pad_token_id=fixture.tokenizer.pad_token_id, bos_token_id=None)
            variants = [(Qwen3_5ForCausalLM, Qwen3_5TextConfig(**common,
                layer_types=["linear_attention", "full_attention"], linear_key_head_dim=16,
                linear_value_head_dim=16, linear_num_key_heads=1, linear_num_value_heads=2,
                rope_parameters={"rope_type": "default", "rope_theta": 10000.,
                                 "partial_rotary_factor": 1., "mrope_section": [2, 3, 3]}))]
            for moe in (False, True):
                variants.append((Gemma4ForCausalLM, Gemma4TextConfig(**common,
                    per_layer_config={1: {"head_dim": 512}},
                    layer_types=["sliding_attention", "full_attention"], sliding_window=64,
                    hidden_size_per_layer_input=0, final_logit_softcapping=30., enable_moe_block=moe,
                    num_experts=4 if moe else None, top_k_experts=2 if moe else None,
                    moe_intermediate_size=32 if moe else None)))
            with patch.object(sys, "path", list(sys.path)):
                runner.load_gpu_packages({"device": "cuda"})
                for model_class, text_config in variants:
                    with self.subTest(model=text_config.model_type, moe=getattr(text_config, "enable_moe_block", False)):
                        base = model_class(text_config)
                        base.set_attn_implementation("sdpa")
                        # Make Gemma's softcap numerically relevant rather than a near identity.
                        with torch.no_grad():
                            base.lm_head.weight.mul_(100.)
                        untouched_forward = model_class.forward
                        config = {**fixture.config, "fused_linear_cross_entropy": True,
                                  "gradient_checkpointing": True, "lora_target_modules":
                                  ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
                                   "in_proj_qkv", "in_proj_z", "in_proj_b", "in_proj_a", "out_proj"]}
                        original = copy.deepcopy(base)
                        with patch.object(runner, "load_model", return_value=base):
                            model = runner.subject_training_model(config)
                        self.assertTrue(model.get_base_model().forward.__module__.startswith("liger_kernel."))
                        self.assertIs(model_class.forward, untouched_forward)
                        self.assertFalse(model.get_base_model().lm_head.weight.requires_grad)
                        reference = copy.deepcopy(model)
                        reference.get_base_model().forward = untouched_forward.__get__(reference.get_base_model())
                        reference.set_attn_implementation("eager")
                        kernel_calls = []
                        def reference_kernel(hidden_states, lm_head_weight, labels, **kwargs):
                            kernel_calls.append(kwargs)
                            self.assertFalse(lm_head_weight.requires_grad)
                            logits = torch.nn.functional.linear(hidden_states, lm_head_weight)
                            cap = kwargs.get("final_logit_softcapping")
                            self.assertEqual(cap, getattr(text_config, "final_logit_softcapping", None))
                            if cap is not None:
                                logits = (logits / cap).tanh() * cap
                            return torch.nn.functional.cross_entropy(logits[:, :-1].float().reshape(-1, logits.shape[-1]),
                                labels[:, 1:].reshape(-1), ignore_index=-100)
                        module = "gemma4" if text_config.model_type == "gemma4_text" else "qwen3_5"
                        loss_name = f"liger_kernel.transformers.model.{module}.LigerForCausalLMLoss"
                        rows = [runner.encode_example(fixture.tokenizer,
                            {"prompt": [{"role": "user", "content": text}],
                             "completion": [{"role": "assistant", "content": answer}]}, 512)
                            for text, answer in (("Tea tastes good.", "Tea"), ("Tea", "Tea is a drink."))]
                        total = sum(sum(v != -100 for v in row["labels"][1:]) for row in rows)
                        with patch(loss_name, side_effect=reference_kernel):
                            for row in rows:
                                batch = {key: torch.tensor([value]) for key, value in row.items()}
                                weight = int((batch["labels"][:, 1:] != -100).sum()) / total
                                actual, expected = model(**batch, use_cache=False), reference(**batch, use_cache=False)
                                self.assertIsNone(actual.logits)
                                torch.testing.assert_close(actual.loss, expected.loss, rtol=1e-5, atol=1e-5)
                                (actual.loss * weight).backward()
                                (expected.loss * weight).backward()
                        self.assertEqual(len(kernel_calls), 2)
                        expected_parameters = dict(reference.named_parameters())
                        changed = False
                        for name, parameter in model.named_parameters():
                            if parameter.requires_grad:
                                self.assertIsNotNone(parameter.grad, name)
                                torch.testing.assert_close(parameter.grad, expected_parameters[name].grad,
                                                           rtol=2e-4, atol=2e-5, msg=name)
                                changed |= bool(parameter.grad.count_nonzero())
                            else:
                                self.assertIsNone(parameter.grad, name)
                        self.assertTrue(changed)
                        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
                        optimizer.step()
                        with tempfile.TemporaryDirectory() as temporary:
                            model.save_pretrained(temporary)
                            with patch.object(runner, "load_model", side_effect=lambda _: copy.deepcopy(original)):
                                restored = runner.subject_training_model(config, temporary)
                                self.assertTrue(restored.get_base_model().forward.__module__.startswith("liger_kernel."))
                                native = runner.load_model(config)
                                from peft import PeftModel
                                evaluation = PeftModel.from_pretrained(native, temporary).merge_and_unload(safe_merge=True)
                            self.assertFalse(evaluation.forward.__module__.startswith("liger_kernel."))
                            self.assertFalse(any("lora_" in name for name, _ in evaluation.named_parameters()))
        finally:
            fixtures.TinyWorkflowTests.tearDownClass()


class CandidateArchitectureTests(unittest.TestCase):
    def test_subject_batch_memory_uses_each_gemma_attention_layer(self):
        from transformers import Gemma4TextConfig, Gemma4ForCausalLM
        for moe in (False, True):
            with self.subTest(moe=moe):
                config = Gemma4TextConfig(vocab_size=32, hidden_size=32, intermediate_size=64,
                    num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1, head_dim=16,
                    per_layer_config={1: {"head_dim": 32, "num_key_value_heads": 2}},
                    layer_types=["sliding_attention", "full_attention"], sliding_window=64,
                    hidden_size_per_layer_input=0, enable_moe_block=moe,
                    num_experts=4 if moe else None, top_k_experts=2 if moe else None,
                    moe_intermediate_size=32 if moe else None)
                model = Gemma4ForCausalLM(config)
                memory = runner.subject_batch_memory(model, {"device": "cpu", "quantization": "none",
                    "subject_batching": {"budget_bytes": 16*1024*1024, "workspace_bytes": 0,
                                         "prefill_bytes_per_token": 1024, "attention_matrix_count": 4}})
                self.assertEqual(memory["kv_bytes_per_token"], 2*2*32*4)
                self.assertEqual(memory["sliding_bytes_per_token"], 2*1*16*4)
                self.assertEqual(memory["attention_heads"], 2)

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
        probe_config = {**config, "max_new_tokens": {"subjects": 120}}
        encoded = [tokenizer.encode(runner.generation_prompt(tokenizer, prompt), add_special_tokens=False)
                   for prompt in messages]
        forward, calls = model.forward, []
        def record_forward(**kwargs):
            output = forward(**kwargs)
            calls.append((kwargs["input_ids"].shape[-1], int(output.past_key_values.get_seq_length())))
            return output
        with patch.object(model, "forward", side_effect=record_forward):
            check = runner.generation_cache_check(model, tokenizer, encoded, probe_config, 16)
        self.assertEqual(check["cached_tokens"], max(map(len, encoded))+120)
        self.assertEqual(calls[-1], (1, check["cached_tokens"]))
        self.assertTrue(all(width <= 16 for width, _ in calls[1:]))
        self.assertEqual(check["batch_size"], 4)
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
                    Gemma4TextConfig(**common, global_head_dim=32, num_global_key_value_heads=1,
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
                        from sse_multivector import distillation_data
                        prepared = root / "subject-data"
                        distillation_data.prepare(fixture.root / "source.json", fixture.root / "annotations.json",
                            fixture.root / "subjects.txt", None, "AS-test", None, 2, "test", prepared, tasks=("subjects",))
                        pilot_data = runner.load_data(prepared)
                        pilot_config = {**config, "batch_size": 1, "gradient_accumulation_steps": 8,
                                        "training_milestones": [2, 4, 6]}
                        plan = runner.subject_training_plan(pilot_data, pilot_config)
                        pilot_output = root / "pilot"
                        runner.write_json(pilot_output / "manifest.json", {"config": pilot_config,
                                          "dataset": pilot_data["manifest"]})
                        runner.write_json(pilot_output / "training-plan.json", plan)
                        previous = None
                        for milestone in plan["milestones"]:
                            previous = runner.train_subject_block(pilot_config, fixture.tokenizer, pilot_data,
                                pilot_output, plan, milestone, previous)
                        loaded = runner.load_model(pilot_config, previous)
                        runner.verify_adapter(loaded, previous)
                        # Every original parameter, including the router and packed
                        # expert weights, must still equal the immutable original.
                        from safetensors.torch import load_file
                        originals = load_file(str(root / "model.safetensors"))
                        for key, value in loaded.named_parameters():
                            if "lora_" in key:
                                continue
                            plain = key.removeprefix("base_model.model.")
                            while ".base_layer." in plain:
                                plain = plain.replace(".base_layer.", ".")
                            published = plain.replace("model.", "model.language_model.", 1) if plain.startswith("model.") else plain
                            self.assertTrue(torch.equal(value.detach().cpu(), originals[published]), key)
                        if name == "gemma-moe":
                            wrappers = [module for module in loaded.modules()
                                        if module.__class__.__name__ == "ParamWrapper"]
                            self.assertEqual(len(wrappers), 2 * text_config.num_hidden_layers)
                            self.assertTrue(all(module.r["default"] == 2 and module.lora_alpha["default"] == 32
                                                for module in wrappers))
                            self.assertTrue(any(torch.count_nonzero(module.lora_B["default"].weight)
                                                for module in wrappers))
                        checkpoint_hashes = runner.file_hashes(previous)
                        loaded = loaded.merge_and_unload(safe_merge=True)
                        self.assertFalse(any("lora_" in key for key, _ in loaded.named_parameters()))
                        self.assert_batch_matches_single(loaded, fixture.tokenizer, pilot_config)
                        self.assertEqual(checkpoint_hashes, runner.file_hashes(previous))
                        del loaded
        finally:
            fixtures.TinyWorkflowTests.tearDownClass()


if __name__ == "__main__":
    unittest.main()
