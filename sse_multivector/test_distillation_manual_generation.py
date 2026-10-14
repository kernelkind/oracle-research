"""Production-path regressions for manual generation."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from sse_multivector import distillation_manual_generation as manual


class Tokenizer:
    def convert_tokens_to_ids(self, text):
        return 11

    def encode(self, text, **kwargs):
        if text == "</think>":
            return [11]
        if all(piece.isdigit() for piece in text.split()):
            return [int(piece) for piece in text.split()]
        return [7, 8]

    def decode(self, tokens, skip_special_tokens=True):
        return " ".join(str(token) for token in tokens if not skip_special_tokens or token not in (11, 12))

    def apply_chat_template(self, messages, **kwargs):
        return messages[0]["content"] + "<think>\n"


def fixture(directory, reuse=True):
    old, new = Path(directory) / "old", Path(directory) / "new"
    notes = [dict(index=i, note_id=f"note-{i}", messages=[dict(role="user", content=f"post{i}")]) for i in (0, 6)]
    old_policy = dict(thought_budget_tokens=4, final_budget_tokens=3, max_context_tokens=20,
                      batch_size=8, enable_thinking=True, do_sample=False, reasoning_effort="xhigh")
    original = dict(seed="fixed", model="fixture", revision="pinned", checkpoint=1000,
                    checkpoint_sha256="adapter", dataset_sha256="dataset", notes=notes, generation_policy=old_policy)
    manual.write(old / "inputs.json", original)
    manual.write(old / "merged-model/config.json", dict(max_position_embeddings=20))
    manual.write(old / "merged-model/generation_config.json", dict(eos_token_id=[12]))
    files = {p.name: dict(size=p.stat().st_size, sha256=manual.digest(p)) for p in (old / "merged-model").iterdir()}
    manual.write(old / "merged-model/export-provenance.json", dict(status="complete",
        inputs_sha256=manual.digest(old / "inputs.json"), checkpoint_sha256="adapter", files=files))
    inputs = copy.deepcopy(original)
    inputs["original_inputs"] = dict(path="../old/inputs.json", sha256=manual.digest(old / "inputs.json"))
    inputs["generation_policy"].update(thought_budget_tokens=None, final_budget_tokens=None,
        stop_policy="natural_eos", gpu_memory_limit_bytes=96 * 1024**3, kv_cache_memory_bytes=40 * 1024**3)
    inputs["reused_generations"] = []
    if reuse:
        runtime = dict(input_sha256=manual.digest(old / "inputs.json"), generation_policy=old_policy,
            model="fixture", revision="pinned", checkpoint_sha256="adapter", eos_token_ids=[12], closing_think_token_id=11)
        manual.write(old / "runtime.json", runtime)
        prompt_sha = manual.hashlib.sha256(Tokenizer().apply_chat_template(notes[0]["messages"]).encode()).hexdigest()
        record = dict(notes[0], model="fixture", revision="pinned", checkpoint_sha256="adapter",
            generation_policy_sha256=manual.policy_digest(old_policy), rendered_prompt_sha256=prompt_sha,
            runtime_receipt=dict(path="runtime.json", sha256=manual.digest(old / "runtime.json")),
            answer=dict(raw="8", tokens=2, truncated=False), reasoning="7", reasoning_tokens=1,
            total_generated_tokens=4, raw_response="7 11 8 12")
        path = old / "generations/note-0000/subjects.json"
        manual.write(path, record)
        inputs["reused_generations"].append(dict(path="../old/generations/note-0000/subjects.json",
            sha256=manual.digest(path), index=0, note_id="note-0", generation_policy=old_policy))
    manual.write(new / "inputs.json", inputs)
    return old, new, inputs


class ManualGenerationTests(unittest.TestCase):
    def test_thinking_continues_past_former_limit_then_finishes(self):
        state = manual.GeneratedTokens(11, [12])
        state.feed([7, 8, 9, 10, 7, 11, 8, 12])
        self.assertEqual(state.split(), ([7, 8, 9, 10, 7], [8, 12], False))

    def test_final_continues_past_former_limit_and_length_is_truncated(self):
        state = manual.GeneratedTokens(11, [12])
        state.feed([7, 11, 8, 9, 10, 7, 8, 12, 9])
        self.assertEqual(state.split(), ([7], [8, 9, 10, 7, 8, 12], False))
        self.assertTrue(state.split("length")[2])
        missing = manual.GeneratedTokens(11, [12]); missing.feed([7, 12])
        self.assertEqual(missing.split(), ([7, 12], [], True))

    def test_original_export_reused_answer_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            old, new, inputs = fixture(directory)
            before = manual.digest(old / "generations/note-0000/subjects.json")
            loaded, merged, _, _, pending, paths = manual.prepare(new, Tokenizer())
            self.assertEqual(set(pending), {"6"})
            self.assertEqual(merged, old / "merged-model")
            self.assertEqual(len(paths), 2)
            self.assertEqual(manual.digest(paths[0]), before)
            manual.write(new / "generations/note-0999/subjects.json", {})
            with self.assertRaisesRegex(ValueError, "Unexpected saved answer"):
                manual.prepare(new, Tokenizer())
            (new / "generations/note-0999/subjects.json").unlink()
            runtime = old / "runtime.json"; runtime.write_text("{}")
            with self.assertRaisesRegex(ValueError, "Runtime receipt changed"):
                manual.prepare(new, Tokenizer())

    def test_context_and_original_input_change_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            old, new, inputs = fixture(directory, reuse=False)
            inputs["generation_policy"]["max_context_tokens"] = 19
            manual.write(new / "inputs.json", inputs)
            with self.assertRaisesRegex(ValueError, "native model context"):
                manual.load_inputs(new)
            inputs["generation_policy"]["max_context_tokens"] = 20
            inputs["notes"][0]["messages"][0]["content"] = "changed"
            manual.write(new / "inputs.json", inputs)
            with self.assertRaisesRegex(ValueError, "Original inputs changed: notes"):
                manual.load_inputs(new)

    def test_generation_and_completed_resume_use_actual_control_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            old, new, inputs = fixture(directory)
            class Engine:
                def __init__(self):
                    self.added = []; self.position = 0
                    scheduler = types.SimpleNamespace(requests={}, running=[], waiting=[],
                        kv_cache_manager=types.SimpleNamespace(usage=0.1))
                    self.engine_core = types.SimpleNamespace(engine_core=types.SimpleNamespace(scheduler=scheduler))
                def add_request(self, key, prompt, sampling):
                    self.added.append(key)
                    self.sampling = sampling
                def has_unfinished_requests(self):
                    return self.position < 2
                def step(self):
                    self.position += 1
                    delta = [7, 8, 9, 10, 7] if self.position == 1 else [11, 8, 12]
                    return [types.SimpleNamespace(request_id="6", finished=self.position == 2,
                        outputs=[types.SimpleNamespace(token_ids=delta, finish_reason="stop" if self.position == 2 else None)])]
            engine = Engine(); loads = []; arguments = []
            def create(*args, **kwargs):
                loads.append(1)
                arguments.append(args[0])
                return engine
            torch = types.ModuleType("torch"); torch.set_num_threads = torch.manual_seed = lambda *args: None
            torch.backends = types.SimpleNamespace(cuda=types.SimpleNamespace(matmul=types.SimpleNamespace(
                allow_tf32=False, allow_bf16_reduced_precision_reduction=True)))
            fractions = []
            torch.cuda = types.SimpleNamespace(set_per_process_memory_fraction=lambda value, device: fractions.append(value),
                get_device_properties=lambda *args: types.SimpleNamespace(total_memory=128 * 1024**3),
                get_device_name=lambda *args: "fixture", memory_reserved=lambda: 0)
            vllm = types.ModuleType("vllm"); vllm.EngineArgs = vllm.SamplingParams = lambda **kwargs: types.SimpleNamespace(**kwargs)
            vllm.LLMEngine = types.SimpleNamespace(from_engine_args=create)
            params = types.ModuleType("vllm.sampling_params"); params.RequestOutputKind = types.SimpleNamespace(DELTA="delta")
            transformers = types.ModuleType("transformers")
            transformers.AutoTokenizer = types.SimpleNamespace(from_pretrained=lambda *args, **kwargs: Tokenizer())
            modules = {"torch": torch, "vllm": vllm, "transformers": transformers, "vllm.sampling_params": params}
            with patch.dict(sys.modules, modules), patch.dict(os.environ, {"VLLM_ENABLE_V1_MULTIPROCESSING": "0"}), \
                    patch.object(manual.importlib.metadata, "version", return_value="fixture"), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(sys, "argv", ["manual-generation", str(new), "--max-num-active-seqs", "4"]):
                    manual.main()
                self.assertEqual(engine.added, ["6"])
                self.assertEqual(arguments[0].max_num_seqs, 8)
                self.assertEqual(arguments[0].max_num_active_seqs, 4)
                self.assertEqual(arguments[0].compilation_config["cudagraph_capture_sizes"], [1, 2, 4, 8])
                self.assertIsNone(engine.sampling.max_tokens)
                self.assertEqual(fractions, [0.75])
                marker = manual.read(new / "generation.complete.json")
                self.assertEqual(len(marker), 2)
                self.assertIn("../old/generations/note-0000/subjects.json", marker)
                record = manual.read(new / "generations/note-0006/subjects.json")
                self.assertFalse(record["answer"]["truncated"])
                self.assertEqual(record["reasoning_tokens"], 5)
                saved = manual.digest(new / "generations/note-0006/subjects.json")
                manual.run(new, max_num_active_seqs=2)
                self.assertEqual(loads, [1])
                self.assertEqual(fractions, [0.75])
                self.assertEqual(manual.digest(new / "generations/note-0006/subjects.json"), saved)

    def test_preemption_snapshot_keeps_finished_counts(self):
        request = types.SimpleNamespace(num_preemptions=2, num_computed_tokens=8)
        scheduler = types.SimpleNamespace(requests={"6": request}, running=[request], waiting=[],
            kv_cache_manager=types.SimpleNamespace(usage=0.4))
        engine = types.SimpleNamespace(engine_core=types.SimpleNamespace(engine_core=types.SimpleNamespace(scheduler=scheduler)))
        seen = {}
        self.assertEqual(manual.cache_snapshot(engine, seen)["cumulative_preemptions"], 2)
        scheduler.requests.clear(); scheduler.running.clear()
        snapshot = manual.cache_snapshot(engine, seen)
        self.assertEqual(snapshot["cumulative_preemptions"], 2)
        self.assertEqual(snapshot["request_counters"]["6"]["num_computed_tokens"], 8)


if __name__ == "__main__":
    unittest.main()
