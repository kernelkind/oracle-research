"""Tests of the production distillation workflow; integration runs inside the VM."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from sse_multivector import distillation_run
from sse_multivector.test_distillation_data import DistillationDataTests
from sse_multivector import distillation_data


class DataContractTests(unittest.TestCase):
    def test_subject_parser_accepts_a_complete_json_code_fence(self):
        subjects = [{"number": "1", "context": "Tea is named.", "subject": "Tea"}]
        raw = json.dumps({"subjects": subjects})
        for opening in ("```json", "```", "```JSON"):
            with self.subTest(opening=opening):
                self.assertEqual(distillation_run.parse_subjects(f" \n{opening}\n{raw}\n```\n"), subjects)

    def test_fences_do_not_hide_invalid_subject_responses(self):
        raw = '{"subjects":[]}'
        invalid = [f"Here is the JSON:\n```json\n{raw}\n```",
                   f"```json\n{raw}\n```\nExplanation",
                   f"```json\n{raw}",
                   f"```python\n{raw}\n```",
                   f"```json\n{raw}\n```\n```json\n{raw}\n```",
                   '```json\n{"subjects":[],"subjects":[]}\n```',
                   '```json\n{"subjects":[{"number":"1.1","context":"Tea","subject":"Tea"}]}\n```']
        for response in invalid:
            with self.subTest(response=response), self.assertRaises(ValueError):
                distillation_run.parse_subjects(response)

    def test_mask_fences_preserve_empty_verdict_and_position_validation(self):
        mask = {"meaning": "Tea", "expressible": False, "evidence": "Only a drink is named.", "mask": []}
        for opening in ("```json", "```"):
            with self.subTest(opening=opening):
                self.assertEqual(distillation_run.decode(f"{opening}\n{json.dumps(mask)}\n```", "Drink"),
                                 (mask, []))
        invalid = [json.dumps({**mask, "expressible": True}),
                   json.dumps({**mask, "expressible": True, "mask": [[1, 1], [1, 1]]}),
                   '{"meaning":"Tea","expressible":false,"evidence":"Drink","mask":[],"mask":[]}']
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                distillation_run.decode(f"```json\n{raw}\n```", "Drink")

    def test_saved_fenced_subjects_proceed_to_fenced_mask_generation(self):
        subjects = [{"number": "1", "context": "Tea is named.", "subject": "Tea"}]
        messages = [{"role": "user", "content": "Subjects?"}]
        data = {"evaluation": [{"note_id": "a", "messages": messages}],
                "references": {"a": {"text": "Tea tastes good."}},
                "mask_prompt": "{POST}\n{INDEXED_POST}\nSubject: {SUBJECT}"}
        mask = {"meaning": "Tea", "expressible": True, "evidence": "Tea is named.", "mask": [[1, 1]]}
        answer = {"raw": f"```json\n{json.dumps(mask)}\n```", "truncated": False, "tokens": 10}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            distillation_run.write_json(output / "note-0000/subjects.json", {"messages": messages,
                "answer": {"raw": f"```json\n{json.dumps({'subjects': subjects})}\n```", "truncated": False}})
            original_hash = distillation_run.sha256(output / "note-0000/subjects.json")
            with patch.object(distillation_run, "generate", side_effect=AssertionError("repeated subjects")), \
                    patch.object(distillation_run, "generate_batch", return_value={"answers": [answer], "seconds": 1}) as calls:
                results = distillation_run.evaluate(None, None, data,
                    {"mask_batch_size": 4, "max_subjects": 8}, output)
            self.assertEqual(results[0]["subjects"], subjects)
            self.assertEqual(results[0]["errors"], [])
            self.assertEqual(results[0]["masks"][0]["spans"], [{"start": 0, "end": 3}])
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(distillation_run.sha256(output / "note-0000/subjects.json"), original_hash)
            self.assertTrue(distillation_run.verify_saved(output))

    def test_mask_batches_preserve_subject_order_and_resume_without_repeating_saved_answers(self):
        subjects = [{"number": str(i + 1), "context": "Tea is named.", "subject": f"Tea {i}"}
                    for i in range(5)]
        data = {"evaluation": [{"note_id": "a", "messages": [{"role": "user", "content": "Subjects?"}]}],
                "references": {"a": {"text": "Tea tastes good.", "subjects": [{"subject": "Teacher only"}]}},
                "mask_prompt": "{POST}\n{INDEXED_POST}\nSubject: {SUBJECT}"}
        subject_answer = {"raw": json.dumps({"subjects": subjects}), "truncated": False}
        valid = json.dumps({"meaning": "Tea", "expressible": True, "evidence": "Tea", "mask": [[1, 1]]})
        empty = json.dumps({"meaning": "Drink", "expressible": False, "evidence": "Only tea", "mask": []})
        def batch(raw):
            return {"answers": [{"raw": r, "tokens": 10, "truncated": False} for r in raw], "seconds": 1.0}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            config = {"mask_batch_size": 2, "max_subjects": 8}
            with patch.object(distillation_run, "generate", return_value=subject_answer), \
                    patch.object(distillation_run, "generate_batch", side_effect=[batch([valid, "bad JSON"]), RuntimeError("interrupted")]):
                with self.assertRaisesRegex(RuntimeError, "interrupted"):
                    distillation_run.evaluate(None, None, data, config, output)
            saved = distillation_run.file_hashes(output)
            with patch.object(distillation_run, "generate", side_effect=AssertionError("repeated subjects")), \
                    patch.object(distillation_run, "generate_batch", side_effect=[batch([empty, valid]), batch([valid])]) as calls:
                results = distillation_run.evaluate(None, None, data, config, output)
            self.assertEqual([len(call.args[2]) for call in calls.call_args_list], [2, 1])
            self.assertEqual([m["subject"]["number"] for m in results[0]["masks"]], ["1", "3", "4", "5"])
            self.assertEqual(results[0]["errors"][0]["subject"]["number"], "2")
            for name, digest in saved.items():
                self.assertEqual(distillation_run.sha256(output / name), digest)
            for path in (output / "note-0000").glob("masks-*.json"):
                saved_batch = distillation_run.read_json(path)
                for messages in saved_batch["messages"]:
                    self.assertNotIn("Teacher only", messages[0]["content"])
            with patch.object(distillation_run, "generate_batch", side_effect=AssertionError("repeated complete batch")):
                self.assertEqual(distillation_run.evaluate(None, None, data, config, output), results)

    def test_changed_training_data_is_rejected_before_loading_a_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            data = root / "prepared"
            loaded = distillation_run.load_data(data, root / "masks.txt")
            self.assertEqual(len(loaded["train"]), 16)
            with (data / "train.jsonl").open("a") as output:
                output.write(json.dumps({"unexpected": True}) + "\n")
            with self.assertRaisesRegex(ValueError, "hash"):
                distillation_run.load_data(data, root / "masks.txt")

    def test_subject_hierarchy_and_matching_validation(self):
        with self.assertRaisesRegex(ValueError, "parent"):
            distillation_run.parse_subjects('{"subjects":[{"number":"1.1","context":"Tea","subject":"Tea"}]}')
        self.assertEqual(distillation_run.matched_count([{1, 2}, {1}], [{1}, {1, 2}], .5), 2)
        self.assertEqual(distillation_run.matched_count([{1}], [{1}, {1}], 1), 1)

    def test_partial_word_is_not_an_exact_source_match(self):
        data = {"references": {"a": {"text": "Teapot", "subjects": [{"byte_spans": [[0, 6]]}]}}}
        notes = [{"note_id": "a", "subjects": [], "errors": [],
                  "masks": [{"spans": [{"start": 0, "end": 3}]}]}]
        summary = distillation_run.summarize(notes, data)
        self.assertEqual(summary["exact_matches"], 0)


class TinyWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
        from transformers import PreTrainedTokenizerFast, LlamaConfig, LlamaForCausalLM
        torch.set_num_threads(2)
        cls.temporary = None
        if os.environ.get("DISTILLATION_TEST_OUTPUT"):
            cls.root = Path(os.environ["DISTILLATION_TEST_OUTPUT"])
            cls.root.mkdir(parents=True, exist_ok=True)
        else:
            cls.temporary = tempfile.TemporaryDirectory()
            cls.root = Path(cls.temporary.name)
        root = cls.root
        subject_prompt = root / "subjects.txt"
        subject_prompt.write_text("Return the subject hierarchy as JSON.")
        mask_prompt = root / "masks.txt"
        mask_prompt.write_text("Return the mask as JSON.\n{POST}\n{INDEXED_POST}\nSubject: {SUBJECT}")
        source = {"notes": [{"note_id": str(i), "pubkey": str(i), "text": f"Tea tastes good {i}."}
                            for i in range(8)]}
        annotations = {"notes": [{**note, "subjects": [
            {"id": "a", "number": "1", "subject": "Tea", "context": "Tea is named.",
             "byte_spans": [[0, 3]], "fragments": ["Tea"],
             "diagnostics": {"meaning": "Tea", "expressible": True, "evidence": "Tea is named."}},
            {"id": "b", "number": "2", "subject": "Drinks", "context": "Tea is a drink.",
             "byte_spans": [], "fragments": [],
             "diagnostics": {"meaning": "Drinks", "expressible": False, "evidence": "Only tea is named."}}
        ]} for note in source["notes"]]}
        distillation_run.write_json(root / "source.json", source)
        distillation_run.write_json(root / "annotations.json", annotations)
        distillation_data.prepare(root / "source.json", root / "annotations.json", subject_prompt,
                                  mask_prompt, "AS-test", "MP-test", 2, "test", root / "data")
        data = distillation_run.load_data(root / "data", mask_prompt)
        template = ("{% for m in messages %}{{ '<' + m['role'] + '>' + m['content'] }}"
                    "{% if m['role'] == 'assistant' %}{{ '<eos>' }}{% endif %}{% endfor %}"
                    "{% if add_generation_prompt %}{{ '<assistant>' }}{% endif %}")
        special = ["<pad>", "<unk>", "<eos>", "<user>", "<assistant>"]
        backend = Tokenizer(models.BPE(unk_token="<unk>"))
        backend.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        backend.decoder = decoders.ByteLevel()
        backend.train_from_iterator([m["content"] for row in data["train"]
                                     for m in row["prompt"] + row["completion"]],
                                    trainers.BpeTrainer(vocab_size=400, special_tokens=special,
                                        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(), show_progress=False))
        tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, pad_token="<pad>",
                                           eos_token="<eos>", unk_token="<unk>", chat_template=template)
        torch.manual_seed(7)
        model = LlamaForCausalLM(LlamaConfig(vocab_size=len(tokenizer), hidden_size=64,
            intermediate_size=128, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
            max_position_embeddings=512, eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id, bos_token_id=None))
        model.save_pretrained(root / "model")
        tokenizer.save_pretrained(root / "model")
        cls.config = {"model": str(root / "model"), "revision": None, "data": str(root / "data"),
            "mask_prompt": str(mask_prompt), "device": "cpu", "quantization": "none", "seed": 17,
            "max_length": 512, "max_new_tokens": {"subjects": 120, "mask": 120}, "max_subjects": 8, "max_steps": 240,
            "save_steps": 20, "batch_size": 4, "mask_batch_size": 4, "gradient_accumulation_steps": 1,
            "learning_rate": .01, "subject_fraction": .5, "lora_rank": 16, "lora_alpha": 32, "threads": 2,
            "gradient_checkpointing": False, "lora_target_modules": "all-linear"}
        distillation_run.write_json(root / "config.json", cls.config)
        cls.tokenizer = tokenizer

    @classmethod
    def tearDownClass(cls):
        if cls.temporary:
            cls.temporary.cleanup()

    def command(self, output):
        return [sys.executable, "-m", "sse_multivector.distillation_run", str(self.root / "config.json"),
                "--output", str(output)]

    def test_answer_only_loss_and_no_truncation(self):
        data = distillation_run.load_data(self.root / "data", self.root / "masks.txt")
        for row in data["train"]:
            encoded = distillation_run.encode_example(self.tokenizer, row, 512)
            answer_ids = [label for label in encoded["labels"] if label != -100]
            self.assertEqual(self.tokenizer.decode(answer_ids, skip_special_tokens=True), row["completion"][0]["content"])
            self.assertEqual(answer_ids[-1], self.tokenizer.eos_token_id)
            with self.assertRaisesRegex(ValueError, "exceeds"):
                distillation_run.encode_example(self.tokenizer, row, len(encoded["input_ids"]) - 1)

    def test_batched_generation_handles_left_padding_stop_tokens_and_output_limits(self):
        import torch
        from transformers import LogitsProcessor
        tokenizer = self.tokenizer
        model = distillation_run.load_model(self.config)
        eos, other_eos = tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<user>")
        token = tokenizer.encode("Tea", add_special_tokens=False)[0]
        model.generation_config.eos_token_id = [eos, other_eos]
        messages = [[{"role": "user", "content": text}] for text in ("Tea", "Tea tastes good.", "Tea is a drink. Tea tastes good.")]
        encoded = [tokenizer.encode(distillation_run.generation_prompt(tokenizer, m), add_special_tokens=False) for m in messages]
        width = max(map(len, encoded))
        sequences = [[token, eos], [token, token, other_eos], [token] * 4]
        class Stops(LogitsProcessor):
            def __call__(self, ids, scores):
                step = ids.shape[1] - width
                scores.fill_(-torch.inf)
                for index, sequence in enumerate(sequences):
                    scores[index, sequence[min(step, len(sequence) - 1)]] = 0
                return scores
        original = model.generate
        def controlled(**kwargs):
            return original(**kwargs, logits_processor=[Stops()])
        old_pad = tokenizer.pad_token
        try:
            tokenizer.pad_token = tokenizer.eos_token
            with patch.object(model, "generate", side_effect=controlled) as generation:
                result = distillation_run.generate_batch(model, tokenizer, messages,
                    {**self.config, "max_new_tokens": {"subjects": 120, "mask": 4}}, "mask")
            self.assertEqual(generation.call_count, 1)
            inputs = generation.call_args.kwargs
            for i, row in enumerate(encoded):
                self.assertEqual(inputs["input_ids"][i].tolist(), [eos] * (width - len(row)) + row)
                self.assertEqual(inputs["attention_mask"][i].tolist(), [0] * (width - len(row)) + [1] * len(row))
            self.assertEqual([a["tokens"] for a in result["answers"]], [2, 3, 4])
            self.assertEqual([a["truncated"] for a in result["answers"]], [False, False, True])
            self.assertEqual([a["raw"] for a in result["answers"]], [tokenizer.decode(s, skip_special_tokens=True) for s in sequences])
            self.assertGreater(result["seconds"], 0)
            self.assertEqual(tokenizer.padding_side, "right")
            with self.assertRaisesRegex(ValueError, "exceeds"):
                distillation_run.generate_batch(model, tokenizer, messages, {**self.config, "max_length": width}, "mask")
        finally:
            tokenizer.pad_token = old_pad

    def test_training_resume_reload_and_two_step_evaluation(self):
        from safetensors.torch import load_file
        import torch
        root = self.root
        full, interrupted = root / "full", root / "interrupted"
        with (root / "full.log").open("w") as log:
            subprocess.run(self.command(full), stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
        with (root / "interrupted.log").open("w") as log:
            process = subprocess.Popen(self.command(interrupted), stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 180
                while not list((interrupted / "checkpoints").glob("checkpoint-*/complete.json")):
                    if process.poll() is not None or time.monotonic() > deadline:
                        self.fail("training failed to publish a checkpoint before interruption")
                    time.sleep(.1)
                process.kill()
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
        baseline_before = distillation_run.file_hashes(interrupted / "baseline")
        partial = interrupted / "checkpoints" / "checkpoint-999"
        partial.mkdir()
        (partial / "adapter_model.safetensors").write_bytes(b"incomplete checkpoint")
        with (root / "resume.log").open("w") as log:
            subprocess.run(self.command(interrupted), stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
        self.assertEqual(baseline_before, distillation_run.file_hashes(interrupted / "baseline"))
        left = load_file(str(full / "adapter" / "adapter_model.safetensors"))
        right = load_file(str(interrupted / "adapter" / "adapter_model.safetensors"))
        for key in left:
            torch.testing.assert_close(left[key], right[key], rtol=0, atol=0)
        self.assertTrue(any(torch.count_nonzero(v) for key, v in left.items() if "lora_B" in key))
        report = distillation_run.read_json(interrupted / "report.json")
        self.assertTrue(report["training"]["reload_matches"])
        self.assertIsNotNone(report["training"]["resumed_from"])
        self.assertEqual(report["trained"]["notes"], 2)
        self.assertEqual(report["baseline"]["subject_failures"], 2)
        self.assertGreater(report["trained"]["valid_masks"], 0)
        self.assertGreater(report["trained"]["empty_masks"], 0)
        results = distillation_run.read_json(interrupted / "trained" / "results.json")
        for index, result in enumerate(results):
            note_directory = interrupted / "trained" / f"note-{index:04}"
            if any(e["task"] == "subjects" for e in result["errors"]):
                self.assertFalse(list(note_directory.glob("masks-*.json")))
                continue
            generated = distillation_run.read_json(note_directory / "subjects.json")["answer"]["raw"]
            subjects = distillation_run.parse_subjects(generated)
            messages = [messages for path in sorted(note_directory.glob("masks-*.json"))
                        for messages in distillation_run.read_json(path)["messages"]]
            self.assertEqual(len(messages), len(subjects))
            for subject, prompt in zip(subjects, messages):
                self.assertIn("Subject: " + subject["subject"], prompt[0]["content"])
        before = distillation_run.file_hashes(interrupted)
        with (root / "repeat.log").open("w") as log:
            subprocess.run(self.command(interrupted), stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        self.assertEqual(before, distillation_run.file_hashes(interrupted))
        changed = root / "changed.json"
        distillation_run.write_json(changed, {**self.config, "learning_rate": .02})
        outcome = subprocess.run([sys.executable, "-m", "sse_multivector.distillation_run", str(changed),
                                  "--output", str(interrupted)], capture_output=True, text=True, timeout=120)
        self.assertNotEqual(outcome.returncode, 0)
        self.assertIn("frozen run differs", outcome.stderr)
        # Conflicting teacher subjects must not enter the model's mask inputs.
        data = distillation_run.load_data(root / "data", root / "masks.txt")
        for row in data["evaluation"]:
            data["references"][row["note_id"]]["subjects"] = [{"subject": "Teacher-only subject"}]
        model = distillation_run.load_model(self.config, interrupted / "adapter")
        separate = root / "own-subjects"
        distillation_run.evaluate(model, self.tokenizer, data, self.config, separate)
        calls = list(separate.glob("note-*/masks-*.json"))
        self.assertTrue(calls)
        for path in calls:
            for messages in distillation_run.read_json(path)["messages"]:
                self.assertNotIn("Teacher-only subject", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
