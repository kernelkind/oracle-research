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
from types import SimpleNamespace

from sse_multivector import distillation_run
from sse_multivector.test_distillation_data import DistillationDataTests
from sse_multivector import distillation_data


class DataContractTests(unittest.TestCase):
    def test_recovery_requires_a_verified_volume_outside_retrieved_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            volume = Path(temporary)
            output = volume / 'work/results/qwen'
            distillation_run.write_json(output / 'manifest.json', {'frozen': True})
            with patch.dict(os.environ, {'HF_HOME': str(volume / 'model-cache'),
                                        'ORACLE_RUN_RECOVERY_DIR': str(volume / 'recovery-checkpoints')}):
                with self.assertRaisesRegex(ValueError, 'verified persistent volume'):
                    distillation_run.subject_recovery_directory(output)
                distillation_run.write_json(volume / 'volume-identity.json', {'id': 881, 'machine_id': 12})
                self.assertEqual(distillation_run.subject_recovery_directory(output),
                    volume / 'recovery-checkpoints' / distillation_run.sha256(output / 'manifest.json'))
                with patch.dict(os.environ, {'ORACLE_RUN_RECOVERY_DIR': str(output / 'recovery')}), \
                        self.assertRaisesRegex(ValueError, 'outside work'):
                    distillation_run.subject_recovery_directory(output)

    def test_preparation_memory_checks_include_reserved_test_input_shapes(self):
        data = {"train": [{"note_id": str(i)} for i in range(3)],
                "evaluation": [{"note_id": "validation"}], "test": [{"note_id": "reserved-test"}]}
        config = {"training_milestones": [1, 3], "max_new_tokens": {"subjects": 120},
                  "preparation": {"max_new_tokens": 4, "cache_fill_tokens": 16,
                                  "train_note_ids": ["0", "1", "2"],
                                  "evaluation_note_ids": ["validation"]}}
        selected = distillation_run.preparation_data(data, config)
        self.assertEqual([row["note_id"] for row in selected["full_evaluation"]],
                         ["validation", "reserved-test"])
        self.assertEqual([row["note_id"] for row in selected["evaluation"]], ["validation"])
        self.assertNotIn("test", selected)

    def test_subject_training_provenance_is_published_before_baseline_progression(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            distillation_run.write_json(output / 'manifest.json', {'frozen': True})
            config = {'seed': 17, 'batch_size': 1, 'gradient_accumulation_steps': 8, 'training_milestones': [1]}
            data = {'train': [{'note_id': 'one', 'task': 'subjects'}]}
            with self.assertRaises(FileNotFoundError):
                distillation_run.run_subject_pilot(config, None, data, output, 'report')
            seal = distillation_run.read_json(output / 'provenance.complete.json')
            self.assertEqual(seal['manifest.json'], distillation_run.sha256(output / 'manifest.json'))
            self.assertEqual(seal['training-plan.json'], distillation_run.sha256(output / 'training-plan.json'))

    def test_explicit_worker_continuation_reconciles_unsaved_generation_without_retrying_saved_answers(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(distillation_run, 'generate_batch', side_effect=RuntimeError('worker interrupted')):
                with self.assertRaisesRegex(RuntimeError, 'worker interrupted'):
                    distillation_run.evaluate(model, tokenizer, data, config, directory)
            original = (directory / 'subjects-0000.started.json').read_bytes()
            with patch.dict(os.environ, {'ORACLE_RUN_ATTEMPT_ID': '002', 'ORACLE_RUN_PREVIOUS_ATTEMPT_ID': '001',
                                        'ORACLE_RUN_CONTINUATION_REASON': 'Resume after a recorded worker interruption'}), \
                    patch.object(distillation_run, 'generate_batch', return_value={'answers': [answer], 'seconds': 1.}) as generate:
                distillation_run.evaluate(model, tokenizer, data, config, directory)
                self.assertEqual(generate.call_count, 1)
                distillation_run.evaluate(model, tokenizer, data, config, directory)
                self.assertEqual(generate.call_count, 1)
            self.assertEqual((directory / 'subjects-0000.started.json').read_bytes(), original)
            self.assertTrue((directory / 'subjects-0000.resume-002.started.json').is_file())
            self.assertTrue((directory / 'subjects-0000.complete.json').is_file())
            self.assertTrue((directory / 'subject-batches.complete.json').is_file())

    def test_preflight_checks_reserved_test_allowance_without_using_test_in_preparation(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                return "".join(m["content"] for m in messages) + ("!" if not kwargs.get("add_generation_prompt") else "")
            def encode(self, text, **kwargs):
                return list(text.encode())
        data = {"train": [{"note_id": "train", "task": "subjects",
                          "prompt": [{"role": "user", "content": "x"}],
                          "completion": [{"role": "assistant", "content": "y"}]}],
                "evaluation": [{"messages": [{"role": "user", "content": "x"}]}],
                "test": [{"messages": [{"role": "user", "content": "x" * 90}]}]}
        config = {"max_length": 100, "max_new_tokens": {"subjects": 20}}
        with self.assertRaisesRegex(ValueError, "test input exceeds generation allowance"):
            distillation_run.preflight(Tokenizer(), data, config)
        result = distillation_run.preflight(Tokenizer(), data, {**config, "preparation": {}})
        self.assertNotIn("test_notes", result)

    def test_preparation_preflight_requires_the_longest_complete_training_example(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                return "".join(m["content"] + "!" for m in messages) + ("?" if kwargs.get("add_generation_prompt") else "")
            def encode(self, text, **kwargs):
                return list(text.encode())
        rows = [{"note_id": str(i), "task": "subjects", "prompt": [{"role": "user", "content": "x" * width}],
                 "completion": [{"role": "assistant", "content": '{"subjects":[]}'}]}
                for i, width in enumerate((4, 8, 80))]
        data = {"train": rows[:2], "full_train": rows, "evaluation": [{"messages": rows[0]["prompt"]}]}
        config = {"max_length": 200, "max_new_tokens": {"subjects": 100}, "preparation": {}}
        with self.assertRaisesRegex(ValueError, "longest complete training example"):
            distillation_run.preflight(Tokenizer(), data, config)

    def test_subject_stage_reparses_raw_answers_even_when_files_are_resealed(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        with tempfile.TemporaryDirectory() as temporary, patch.object(distillation_run, "generate_batch",
                return_value={"answers": [answer], "seconds": 1.}):
            root = Path(temporary)
            distillation_run.evaluate(model, tokenizer, data, config, root)
            parsed = {"note_id": "0", "subjects": [], "errors": [{"task": "subjects", "error": "parser defect"}]}
            distillation_run.write_json(root / "note-0000/subjects-result.json", parsed)
            distillation_run.write_json(root / "results.json", [{**parsed, "masks": []}])
            distillation_run.write_json(root / "note-0000/complete.json", distillation_run.file_hashes(root / "note-0000"))
            distillation_run.write_json(root / "complete.json", distillation_run.file_hashes(root))
            with self.assertRaisesRegex(ValueError, "parsed subject result differs from raw"):
                distillation_run.subject_stage_summary(root, data)

    def test_subject_stage_rechecks_generation_receipt(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        with tempfile.TemporaryDirectory() as temporary, patch.object(distillation_run, "generate_batch",
                return_value={"answers": [answer], "seconds": 1.}):
            root = Path(temporary)
            distillation_run.evaluate(model, tokenizer, data, config, root)
            receipt = distillation_run.read_json(root / "subjects-0000.json")
            receipt["answers"] = []
            distillation_run.write_json(root / "subjects-0000.json", receipt)
            distillation_run.write_json(root / "complete.json", distillation_run.file_hashes(root))
            with self.assertRaisesRegex(ValueError, "receipt"):
                distillation_run.subject_stage_summary(root, data)

    def test_invalid_generation_metadata_is_not_a_model_failure(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        for key, value in (("raw", None), ("tokens", -1), ("truncated", "false")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary, \
                    patch.object(distillation_run, "generate_batch", return_value={
                        "answers": [{**answer, key: value}], "seconds": 1.}):
                with self.assertRaisesRegex(ValueError, "generation answer contract"):
                    distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))
                self.assertFalse((Path(temporary) / "complete.json").exists())

    def test_malformed_model_answers_remain_counted_results(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        answer["raw"] = "not JSON"
        with tempfile.TemporaryDirectory() as temporary, patch.object(distillation_run, "generate_batch",
                return_value={"answers": [answer], "seconds": 1.}):
            root = Path(temporary)
            distillation_run.evaluate(model, tokenizer, data, config, root)
            self.assertEqual(distillation_run.subject_stage_summary(root, data)["subject_failures"], 1)

    def test_subjects_only_evaluation_preserves_a_large_valid_hierarchy(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        subjects = [{"number": str(i), "context": "Tea", "subject": f"Tea topic {i}"}
                    for i in range(1, 146)]
        answer["raw"] = json.dumps({"subjects": subjects})
        with tempfile.TemporaryDirectory() as temporary, patch.object(distillation_run, "generate_batch",
                return_value={"answers": [answer], "seconds": 1.}):
            results = distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))
            self.assertEqual(results[0]["errors"], [])
            self.assertEqual(len(results[0]["subjects"]), 145)
            self.assertTrue(distillation_run.verify_saved(temporary))
        config["evaluation_tasks"] = ["subjects", "mask"]
        with tempfile.TemporaryDirectory() as temporary, patch.object(distillation_run, "generate_batch",
                return_value={"answers": [answer], "seconds": 1.}):
            results = distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))
            self.assertEqual(results[0]["errors"], [{"task": "subjects", "error": "subject count exceeds configured limit"}])

    def test_zero_attention_matrices_require_enforced_efficient_cuda_attention(self):
        for device, enabled in (("cpu", False), ("cpu", True), ("cuda", False)):
            model, tokenizer, data, config, _ = self.subject_batch_fixture((4,))
            config["device"] = device
            config["efficient_attention"] = enabled
            config["subject_batching"]["attention_matrix_count"] = 0
            with self.subTest(device=device, enabled=enabled):
                with self.assertRaisesRegex(ValueError, "zero attention matrices require efficient CUDA attention"):
                    distillation_run.subject_batch_memory(model, config)

    def test_subject_response_is_sealed_before_next_generation_batch(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            calls = []
            def generate(model, tokenizer, messages, config, task, **kwargs):
                if calls:
                    for index in calls[-1]:
                        self.assertTrue(distillation_run.verify_saved(root / f"note-{index:04}"))
                start = sum(len(indices) for indices in calls)
                calls.append(list(range(start, start + len(messages))))
                return {"answers": [dict(answer) for _ in messages], "seconds": 1.}
            with patch.object(distillation_run, "generate_batch", side_effect=generate):
                distillation_run.evaluate(model, tokenizer, data, config, root)
            self.assertTrue(all(distillation_run.verify_saved(root / f"note-{i:04}") for i in range(5)))

    def test_subject_checkpoint_with_wrong_update_count_blocks_advancement(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,))
        data["train"] = [{"note_id": "train", "task": "subjects"}]
        config.update(seed=7, batch_size=1, gradient_accumulation_steps=8, training_milestones=[1])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            distillation_run.write_json(root / "manifest.json", {"identity": "test"})
            plan = distillation_run.subject_training_plan(data, config)
            distillation_run.write_json(root / "training-plan.json", plan)
            with patch.object(distillation_run, "generate_batch", return_value={"answers": [answer], "seconds": 1.}):
                distillation_run.evaluate(model, tokenizer, data, config, root / "baseline")
            checkpoint = root / "checkpoints/checkpoint-1"
            checkpoint.mkdir(parents=True)
            for name in ("training-state.pt", "adapter_model.safetensors", "adapter_config.json"):
                (checkpoint / name).write_bytes(b"fixture checkpoint payload")
            distillation_run.write_json(checkpoint / "training.json", {"cursor": 1, "updates": 2,
                "supervised_tokens": 1, "consumed_note_ids": ["train"],
                "manifest_sha256": distillation_run.sha256(root / "manifest.json"),
                "plan_sha256": distillation_run.sha256(root / "training-plan.json")})
            distillation_run.write_json(checkpoint / "complete.json", distillation_run.file_hashes(checkpoint))
            with patch.object(distillation_run, "load_model", side_effect=AssertionError("advanced corrupt checkpoint")):
                with self.assertRaisesRegex(ValueError, "checkpoint update count differs"):
                    distillation_run.run_subject_pilot(config, tokenizer, data, root, "report")

    def test_subject_training_plan_shuffles_within_blocks_and_uses_every_note_once(self):
        data = {"train": [{"note_id": str(i), "task": "subjects"} for i in range(15)]}
        config = {"seed": 7, "batch_size": 1, "gradient_accumulation_steps": 8,
                  "training_milestones": [3, 6, 9, 12, 15]}
        plan = distillation_run.subject_training_plan(data, config)
        self.assertEqual(len(set(plan["note_ids"])), 15)
        self.assertEqual(plan["milestones"], config["training_milestones"])
        for start in range(0, 15, 3):
            self.assertEqual(set(plan["note_ids"][start:start+3]), {str(i) for i in range(start, start+3)})
        self.assertEqual(plan, distillation_run.subject_training_plan(data, config))
        data["train"][0]["task"] = "mask"
        with self.assertRaisesRegex(ValueError, "one subject example"):
            distillation_run.subject_training_plan(data, config)

    def subject_batch_fixture(self, lengths=(4, 4, 20, 4, 4)):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                return messages[0]["content"]

            def encode(self, text, **kwargs):
                return list(range(len(text)))

        class Tensor:
            device = SimpleNamespace(type="cpu")

            def numel(self):
                return 16

            def element_size(self):
                return 4

        class Model:
            config = SimpleNamespace(model_type="llama", num_hidden_layers=1,
                num_attention_heads=1, num_key_value_heads=1, head_dim=1)
            generation_config = SimpleNamespace(num_beams=1, num_return_sequences=1,
                                                cache_implementation=None)

            def parameters(self):
                return iter([Tensor()])

            def buffers(self):
                return iter([])

            def get_input_embeddings(self):
                return SimpleNamespace(weight=Tensor())

        data = {"evaluation": [{"note_id": str(i), "messages": [{"role": "user", "content": "x" * n}]}
                               for i, n in enumerate(lengths)],
                "references": {str(i): {"text": "Tea"} for i in range(len(lengths))}}
        config = {"device": "cpu", "quantization": "none", "max_length": 100,
                  "max_new_tokens": {"subjects": 4}, "max_subjects": 8,
                  "evaluation_tasks": ["subjects"],
                  "subject_batching": {"budget_bytes": 20000, "workspace_bytes": 0,
                                       "prefill_bytes_per_token": 32, "attention_matrix_count": 4}}
        answer = {"raw": '{"subjects":[]}', "tokens": 3, "truncated": False}
        return Model(), Tokenizer(), data, config, answer

    def test_subject_batches_follow_memory_budget_and_preserve_each_note(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture()
        def batch(model, tokenizer, messages, config, task, **kwargs):
            return {"answers": [dict(answer) for _ in messages], "seconds": 1.}

        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(distillation_run, "generate", return_value=answer), \
                patch.object(distillation_run, "generate_batch", side_effect=batch) as calls:
            results = distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))
            self.assertEqual([len(call.args[2]) for call in calls.call_args_list], [2, 1, 2])
            self.assertEqual([row["note_id"] for row in results], [str(i) for i in range(5)])
            for i in range(5):
                saved = distillation_run.read_json(Path(temporary) / f"note-{i:04}/subjects.json")
                self.assertEqual(saved["messages"], data["evaluation"][i]["messages"])
                self.assertEqual(saved["answer"], answer)
            self.assertTrue(distillation_run.verify_saved(temporary))

    def test_subject_batch_size_reserves_the_entire_output_allowance(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture((4,)*5)
        config["subject_batching"]["budget_bytes"] = 3000
        for allowance, expected in ((4, [4, 1]), (50, [1]*5)):
            with self.subTest(allowance=allowance), tempfile.TemporaryDirectory() as temporary:
                config["max_new_tokens"]["subjects"] = allowance
                def batch(model, tokenizer, messages, config, task, **kwargs):
                    return {"answers": [dict(answer) for _ in messages], "seconds": 1.}
                with patch.object(distillation_run, "generate_batch", side_effect=batch) as calls:
                    distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))
                self.assertEqual([len(call.args[2]) for call in calls.call_args_list], expected)


    def test_subject_batch_resume_uses_receipt_after_partial_note_publication(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture()
        valid = {**answer, "raw": '{"subjects":[{"number":"1","context":"Tea is named.","subject":"Tea"}]}'}
        malformed = {**answer, "raw": "bad JSON"}
        truncated = {**valid, "truncated": True}
        publish = distillation_run.write_json
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def interrupted(path, value):
                if Path(path) == root / "note-0001/subjects.json":
                    self.assertTrue((root / "subjects-0000.json").exists())
                    raise OSError("publication interrupted")
                return publish(path, value)
            with patch.object(distillation_run, "generate_batch", return_value={
                    "answers": [valid, malformed], "seconds": 1.}) as calls, \
                    patch.object(distillation_run, "write_json", side_effect=interrupted):
                with self.assertRaisesRegex(OSError, "publication interrupted"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)
                self.assertEqual(calls.call_count, 1)
            saved = distillation_run.file_hashes(root)
            def batch(model, tokenizer, messages, config, task, **kwargs):
                # Completed first-batch answers must already be parsed before
                # another expensive generation call starts.
                self.assertTrue((root / "note-0001/subjects-result.json").exists())
                replies = [truncated] if len(messages) == 1 else [answer, valid]
                return {"answers": replies, "seconds": 1.}
            with patch.object(distillation_run, "generate", side_effect=AssertionError("serial subject call")), \
                    patch.object(distillation_run, "generate_batch", side_effect=batch) as calls:
                results = distillation_run.evaluate(model, tokenizer, data, config, root)
            self.assertEqual([len(call.args[2]) for call in calls.call_args_list], [1, 2])
            self.assertTrue(all(call.args[4] == "subjects" for call in calls.call_args_list))
            self.assertEqual([bool(row["errors"]) for row in results], [False, True, True, False, False])
            self.assertEqual(results[0]["subjects"][0]["subject"], "Tea")
            self.assertFalse(list(root.glob("note-*/masks-*.json")))
            for name, digest in saved.items():
                self.assertEqual(distillation_run.sha256(root / name), digest)
            with patch.object(distillation_run, "generate_batch", side_effect=AssertionError("repeated completed evaluation")):
                self.assertEqual(distillation_run.evaluate(model, tokenizer, data, config, root), results)

    def test_incomplete_subject_generation_is_not_automatically_retried(self):
        model, tokenizer, data, config, _ = self.subject_batch_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(distillation_run, "generate_batch", side_effect=RuntimeError("GPU failure")) as calls:
                with self.assertRaisesRegex(RuntimeError, "GPU failure"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)
                self.assertEqual(calls.call_count, 1)
            with patch.object(distillation_run, "generate_batch", side_effect=AssertionError("automatic retry")):
                with self.assertRaisesRegex(ValueError, "unfinished generation attempt"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)

    def test_bad_subject_batch_count_is_preserved_and_blocks_completion(self):
        model, tokenizer, data, config, answer = self.subject_batch_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(distillation_run, "generate_batch", return_value={"answers": [answer], "seconds": 1.}):
                with self.assertRaisesRegex(ValueError, "answer count differs"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)
            self.assertEqual(distillation_run.read_json(root / "subjects-0000.json")["answers"], [answer])
            self.assertFalse((root / "complete.json").exists())
            with patch.object(distillation_run, "generate_batch", side_effect=AssertionError("retrying count defect")):
                with self.assertRaisesRegex(ValueError, "answer count differs"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)

    def test_subject_batch_policy_change_is_rejected_on_resume(self):
        model, tokenizer, data, config, _ = self.subject_batch_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(distillation_run, "generate_batch", side_effect=RuntimeError("interrupted")):
                with self.assertRaisesRegex(RuntimeError, "interrupted"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)
            config["subject_batching"]["budget_bytes"] += 1
            with patch.object(distillation_run, "generate_batch", side_effect=AssertionError("changed frozen policy")):
                with self.assertRaisesRegex(ValueError, "batch plan differs"):
                    distillation_run.evaluate(model, tokenizer, data, config, root)

    def test_subject_batch_limits_fail_before_any_generation(self):
        for change, message in ((lambda c: c["subject_batching"].update(budget_bytes=1), "cannot fit"),
                                (lambda c: c.update(max_length=10), "max_length"),
                                (lambda c: c["subject_batching"].update(attention_matrix_count=True), "invalid subject batching")):
            model, tokenizer, data, config, _ = self.subject_batch_fixture()
            change(config)
            with self.subTest(error=message), tempfile.TemporaryDirectory() as temporary, \
                    patch.object(distillation_run, "generate_batch", side_effect=AssertionError("generation before validation")):
                with self.assertRaisesRegex(ValueError, message):
                    distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))

    def test_subject_memory_policy_rejects_generation_that_multiplies_or_retains_state(self):
        for setting, value in (("num_beams", 2), ("num_return_sequences", 2),
                               ("cache_implementation", "static"), ("output_scores", True),
                               ("output_hidden_states", True)):
            model, tokenizer, data, config, _ = self.subject_batch_fixture()
            model.generation_config = SimpleNamespace(num_beams=1, num_return_sequences=1,
                                                     cache_implementation=None)
            setattr(model.generation_config, setting, value)
            with self.subTest(setting=setting), tempfile.TemporaryDirectory() as temporary, \
                    patch.object(distillation_run, "generate_batch", side_effect=AssertionError("unsupported generation")):
                with self.assertRaisesRegex(ValueError, "unsupported subject generation settings"):
                    distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))

    def test_subject_budget_reserves_decode_attention_for_short_inputs_and_long_answers(self):
        model, tokenizer, data, config, _ = self.subject_batch_fixture((4,))
        config["max_new_tokens"]["subjects"] = 80
        config["subject_batching"]["budget_bytes"] = 3000
        with tempfile.TemporaryDirectory() as temporary, \
                patch.object(distillation_run, "generate_batch", side_effect=AssertionError("underbudgeted decode")):
            with self.assertRaisesRegex(ValueError, "cannot fit"):
                distillation_run.evaluate(model, tokenizer, data, config, Path(temporary))

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
                "answer": {"raw": f"```json\n{json.dumps({'subjects': subjects})}\n```", "truncated": False, "tokens": 10}})
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
        subject_answer = {"raw": json.dumps({"subjects": subjects}), "truncated": False, "tokens": 10}
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

    def test_fused_loss_rejects_unsupported_architecture_before_training(self):
        config = {**self.config, "fused_linear_cross_entropy": True}
        with self.assertRaisesRegex(ValueError, "unsupported fused training loss model"):
            distillation_run.subject_training_model(config)

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

    def test_dynamic_subject_baseline_runs_through_the_cli_and_freezes_its_policy(self):
        config = {**self.config, "evaluation_tasks": ["subjects"],
                  "subject_batching": {"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                                       "prefill_bytes_per_token": 1024, "attention_matrix_count": 4}}
        path, output = self.root / "dynamic-config.json", self.root / "dynamic-baseline"
        distillation_run.write_json(path, config)
        command = [sys.executable, "-B", "-m", "sse_multivector.distillation_run", str(path),
                   "--output", str(output), "--through", "baseline"]
        with (self.root / "dynamic-baseline.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        self.assertTrue(distillation_run.verify_saved(output / "baseline"))
        data = distillation_run.load_data(config["data"], config["mask_prompt"])
        receipt = distillation_run.read_json(output / "baseline/subjects-0000.json")
        self.assertEqual(receipt["note_ids"], [row["note_id"] for row in data["evaluation"]])
        self.assertEqual(len(receipt["answers"]), len(data["evaluation"]))
        self.assertFalse(list(output.glob("baseline/note-*/masks-*.json")))
        self.assertFalse((output / "adapter").exists())
        before = distillation_run.file_hashes(output)
        subprocess.run(command, capture_output=True, check=True, timeout=120)
        self.assertEqual(before, distillation_run.file_hashes(output))
        config["subject_batching"]["budget_bytes"] += 1
        distillation_run.write_json(path, config)
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("frozen run differs", result.stderr)
        self.assertEqual(before, distillation_run.file_hashes(output))

    def test_subject_pilot_retains_five_checkpoints_and_continues_once_through_every_note(self):
        import torch
        prepared = self.root / "subject-pilot-data"
        distillation_data.prepare(self.root / "source.json", self.root / "annotations.json",
            self.root / "subjects.txt", None, "AS-test", None, 2, "test", prepared, tasks=("subjects",))
        removed = {"mask_prompt", "max_steps", "save_steps", "subject_fraction", "mask_batch_size"}
        config = {key: value for key, value in self.config.items() if key not in removed}
        config.update(data=str(prepared), training_milestones=[1, 2, 3, 4, 6],
            batch_size=1, gradient_accumulation_steps=8, evaluation_tasks=["subjects"],
            max_new_tokens={"subjects": self.config["max_new_tokens"]["subjects"]},
            subject_batching={"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                              "prefill_bytes_per_token": 1024, "attention_matrix_count": 4})
        path, output = self.root / "subject-pilot.json", self.root / "subject-pilot"
        distillation_run.write_json(path, config)
        command = [sys.executable, "-B", "-m", "sse_multivector.distillation_run", str(path),
                   "--output", str(output)]
        with (self.root / "subject-pilot.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        data = distillation_run.load_data(prepared, None)
        plan = distillation_run.read_json(output / "training-plan.json")
        self.assertEqual(set(plan["note_ids"]), set(data["manifest"]["train_note_ids"]))
        self.assertEqual(len(plan["note_ids"]), 6)
        for update, milestone in enumerate(config["training_milestones"], 1):
            checkpoint = output / "checkpoints" / f"checkpoint-{milestone}"
            self.assertTrue(distillation_run.verify_saved(checkpoint))
            state = torch.load(checkpoint / "training-state.pt", weights_only=True)
            self.assertEqual(state["cursor"], milestone)
            self.assertEqual(state["updates"], update)
            self.assertEqual(state["consumed_note_ids"], plan["note_ids"][:milestone])
            self.assertTrue(all(int(value["step"]) == update for value in state["optimizer"]["state"].values()))
            stage = output / "evaluations" / f"checkpoint-{milestone}"
            self.assertTrue(distillation_run.verify_saved(stage))
            self.assertEqual(len(list(stage.glob("note-*/subjects-result.json"))), 2)
            self.assertFalse(list(stage.glob("note-*/masks-*.json")))
        # Run the same production block updates without intervening generation.
        # Evaluation must leave the next update, Adam moments and random state identical.
        reference = self.root / "subject-pilot-reference"
        reference.mkdir()
        distillation_run.write_json(reference / "manifest.json", distillation_run.read_json(output / "manifest.json"))
        distillation_run.write_json(reference / "training-plan.json", plan)
        previous = None
        for milestone in config["training_milestones"]:
            previous = distillation_run.train_subject_block(config, self.tokenizer, data, reference, plan, milestone, previous)
            from safetensors.torch import load_file
            checkpoint = output / "checkpoints" / f"checkpoint-{milestone}"
            actual_weights = load_file(str(checkpoint / "adapter_model.safetensors"))
            reference_weights = load_file(str(previous / "adapter_model.safetensors"))
            for name in actual_weights:
                torch.testing.assert_close(actual_weights[name], reference_weights[name], rtol=0, atol=0)
            actual = torch.load(checkpoint / "training-state.pt", weights_only=True)
            expected = torch.load(previous / "training-state.pt", weights_only=True)
            torch.testing.assert_close(actual["optimizer"], expected["optimizer"], rtol=0, atol=0)
            torch.testing.assert_close(actual["random"]["torch"], expected["random"]["torch"], rtol=0, atol=0)
            self.assertEqual(actual["random"]["python"], expected["random"]["python"])
            self.assertEqual(actual["random"]["numpy"], expected["random"]["numpy"])
            self.assertEqual(actual["schedule"], expected["schedule"])
        self.assertEqual(distillation_run.read_json(output / "report.json")["training"]["examples"], 6)
        before = distillation_run.file_hashes(output)
        subprocess.run(command, capture_output=True, check=True, timeout=180)
        self.assertEqual(before, distillation_run.file_hashes(output))
        import shutil
        resumed = self.root / "subject-pilot-resumed"
        resumed.mkdir()
        for name in ("manifest.json", "training-plan.json"):
            shutil.copyfile(output / name, resumed / name)
        shutil.copytree(output / "baseline", resumed / "baseline")
        shutil.copytree(output / "checkpoints/checkpoint-1", resumed / "checkpoints/checkpoint-1")
        partial = resumed / "evaluations/checkpoint-1"
        shutil.copytree(output / "evaluations/checkpoint-1", partial)
        (partial / "complete.json").unlink()
        (partial / "results.json").unlink()
        for file in (partial / "note-0001").iterdir():
            file.unlink()
        first_before = distillation_run.file_hashes(resumed / "checkpoints/checkpoint-1")
        baseline_before = distillation_run.file_hashes(resumed / "baseline")
        resumed_command = [*command[:-1], str(resumed)]
        with (self.root / "subject-pilot-resumed.log").open("w") as log:
            subprocess.run(resumed_command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        self.assertEqual(first_before, distillation_run.file_hashes(resumed / "checkpoints/checkpoint-1"))
        self.assertEqual(baseline_before, distillation_run.file_hashes(resumed / "baseline"))
        actual = torch.load(output / "checkpoints/checkpoint-6/training-state.pt", weights_only=True)
        recovered = torch.load(resumed / "checkpoints/checkpoint-6/training-state.pt", weights_only=True)
        for key in ("identity", "cursor", "updates", "supervised_tokens", "consumed_note_ids", "schedule"):
            self.assertEqual(actual[key], recovered[key])
        torch.testing.assert_close(actual["optimizer"], recovered["optimizer"], rtol=0, atol=0)
        torch.testing.assert_close(actual["random"]["torch"], recovered["random"]["torch"], rtol=0, atol=0)
        self.assertEqual(actual["random"]["python"], recovered["random"]["python"])
        self.assertEqual(actual["random"]["numpy"], recovered["random"]["numpy"])
        broken = self.root / "subject-pilot-missing-response"
        broken.mkdir()
        shutil.copyfile(output / "manifest.json", broken / "manifest.json")
        shutil.copytree(output / "baseline", broken / "baseline")
        (broken / "baseline/note-0001/subjects-result.json").unlink()
        distillation_run.write_json(broken / "baseline/complete.json", distillation_run.file_hashes(broken / "baseline"))
        result = subprocess.run([*command[:-1], str(broken)], capture_output=True, text=True, timeout=120)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("subjects-result.json", result.stderr)
        self.assertFalse((broken / "checkpoints").exists())
        config["subject_batching"]["budget_bytes"] += 1
        distillation_run.write_json(path, config)
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("frozen run differs", result.stderr)
        self.assertEqual(before, distillation_run.file_hashes(output))

    def test_subject_pilot_collects_only_baseline_and_final_reserved_test_and_resumes(self):
        import shutil
        import torch
        root = self.root
        splits = root / "reserved-splits.json"
        distillation_run.write_json(splits, {"train": ["0", "1", "2", "3"],
                                            "validation": ["4", "5"], "test": ["6", "7"]})
        prepared = root / "reserved-data"
        distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
            None, "AS-test", None, 2, "test", prepared, tasks=("subjects",), splits_path=splits)
        config = {k: v for k, v in self.config.items() if k not in
                  ("mask_prompt", "max_steps", "save_steps", "subject_fraction", "mask_batch_size")}
        config.update(data=str(prepared), training_milestones=[2, 4], batch_size=1,
            gradient_accumulation_steps=8, evaluation_tasks=["subjects"], max_new_tokens={"subjects": 120},
            subject_batching={"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                              "prefill_bytes_per_token": 1024, "attention_matrix_count": 4})
        path, output = root / "reserved-config.json", root / "reserved-run"
        distillation_run.write_json(path, config)
        with patch.object(distillation_run, "load_model", wraps=distillation_run.load_model) as loads:
            distillation_run.run(path, output)
        self.assertTrue(distillation_run.verify_saved(output / "test/baseline"))
        self.assertTrue(distillation_run.verify_saved(output / "test/checkpoint-4"))
        self.assertFalse((output / "test/checkpoint-2").exists())
        self.assertEqual(loads.call_count, 5)  # base, two training loads, two merged evaluation loads
        data = distillation_run.load_data(prepared)
        checked = distillation_run.verify_subject_run(output, data, config)
        self.assertEqual(checked["test"]["review_status"], "sealed")
        for stage in ("baseline", "checkpoint-4"):
            rows = distillation_run.read_json(output / "test" / stage / "results.json")
            self.assertEqual([r["note_id"] for r in rows], ["6", "7"])
            self.assertEqual(checked["test"][stage]["notes"], 2)
            self.assertNotIn("subject_failures", checked["test"][stage])
        state = torch.load(output / "checkpoints/checkpoint-4/training-state.pt", weights_only=True)
        self.assertEqual(set(state["consumed_note_ids"]), {"0", "1", "2", "3"})
        before = distillation_run.file_hashes(output)
        with patch.object(distillation_run, "load_model", side_effect=AssertionError("repeated completed work")):
            distillation_run.run(path, output)
        self.assertEqual(before, distillation_run.file_hashes(output))
        # Recover a missing baseline test before entering the training loop.
        shutil.rmtree(output / "test/baseline")
        with patch.object(distillation_run, "train_subject_block", side_effect=AssertionError("retrained")), \
                patch.object(distillation_run, "load_model", wraps=distillation_run.load_model) as loads:
            distillation_run.run(path, output)
        self.assertEqual(loads.call_count, 1)
        distillation_run.verify_subject_run(output, data, config)
        # Recover a final test after validation was already sealed; never train again.
        saved = root / "reserved-test-backup"
        shutil.copytree(output / "test/checkpoint-4", saved)
        shutil.rmtree(output / "test/checkpoint-4")
        with self.assertRaises((ValueError, FileNotFoundError)):
            distillation_run.verify_subject_run(output, data, config)
        with patch.object(distillation_run, "train_subject_block", side_effect=AssertionError("retrained")), \
                patch.object(distillation_run, "load_model", wraps=distillation_run.load_model) as loads:
            distillation_run.run(path, output)
        self.assertEqual(loads.call_count, 1)
        distillation_run.verify_subject_run(output, data, config)
        # A resealed collection cannot claim the wrong checkpoint.
        stage = output / "test/checkpoint-4"
        binding = distillation_run.read_json(stage / "test-collection.json")
        binding["checkpoint"] = "checkpoints/checkpoint-2"
        distillation_run.write_json(stage / "test-collection.json", binding)
        distillation_run.write_json(stage / "complete.json", distillation_run.file_hashes(stage))
        with self.assertRaisesRegex(ValueError, "test collection source differs"):
            distillation_run.verify_subject_run(output, data, config)

    def test_continuation_preserves_optimizer_and_collects_both_tests_without_new_baselines(self):
        import shutil
        import torch
        from safetensors.torch import load_file
        root = self.root
        splits = root / "continuation-splits.json"
        distillation_run.write_json(splits, {"train": ["0", "1", "2", "3"],
                                           "validation": ["4", "5"], "test": ["6", "7"]})
        prepared = root / "continuation-data"
        distillation_data.prepare(root / "source.json", root / "annotations.json", root / "subjects.txt",
            None, "AS-test", None, 2, "test", prepared, tasks=("subjects",), splits_path=splits)
        original = {k: v for k, v in self.config.items() if k not in
                    ("mask_prompt", "max_steps", "save_steps", "subject_fraction", "mask_batch_size")}
        original.update(data=str(prepared), training_milestones=[2, 4], batch_size=1,
            gradient_accumulation_steps=8, evaluation_tasks=["subjects"], max_new_tokens={"subjects": 120},
            subject_batching={"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                              "prefill_bytes_per_token": 1024, "attention_matrix_count": 4})
        parent = root / "continuation-parent"
        path = root / "continuation-parent.json"
        distillation_run.write_json(path, original)
        distillation_run.run(path, parent)
        source = parent / "checkpoints/checkpoint-4"
        before = distillation_run.file_hashes(parent)
        config = {**original, "training_milestones": [8, 12], "continuation": {
            "parent_run": str(parent), "manifest_sha256": distillation_run.sha256(parent / "manifest.json"),
            "plan_sha256": distillation_run.sha256(parent / "training-plan.json"),
            "checkpoint_sha256": distillation_run.sha256(source / "complete.json")}}
        path, output = root / "continuation.json", root / "continuation"
        distillation_run.write_json(path, config)
        distillation_run.run(path, output)
        self.assertEqual(before, distillation_run.file_hashes(parent))
        self.assertFalse((output / "baseline").exists())
        self.assertFalse((output / "test/baseline").exists())
        data = distillation_run.load_data(prepared)
        checked = distillation_run.verify_subject_run(output, data, config)
        self.assertEqual(checked["training"], {"examples": 12, "updates": 4})
        self.assertEqual(set(checked["test"]), {"review_status", "baseline", "checkpoint-8", "checkpoint-12"})
        for milestone in (8, 12):
            self.assertEqual(checked["test"][f"checkpoint-{milestone}"]["notes"], 2)
            self.assertTrue(distillation_run.verify_saved(output / f"evaluations/checkpoint-{milestone}"))
        # Compare actual weights and Adam moments with identical production updates
        # performed without any evaluation in between.
        reference = root / "continuation-reference"
        reference.mkdir()
        for name in ("manifest.json", "training-plan.json"):
            shutil.copyfile(output / name, reference / name)
        plan = distillation_run.read_json(output / "training-plan.json")
        previous = source
        for update, milestone in enumerate((8, 12), 3):
            previous = distillation_run.train_subject_block(config, self.tokenizer, data,
                reference, plan, milestone, previous)
            checkpoint = output / f"checkpoints/checkpoint-{milestone}"
            actual = torch.load(checkpoint / "training-state.pt", weights_only=True)
            expected = torch.load(previous / "training-state.pt", weights_only=True)
            self.assertEqual(actual["updates"], update)
            self.assertTrue(all(int(value["step"]) == update for value in actual["optimizer"]["state"].values()))
            self.assertEqual(actual["consumed_note_ids"], plan["note_ids"][:milestone])
            torch.testing.assert_close(load_file(str(checkpoint / "adapter_model.safetensors")),
                                       load_file(str(previous / "adapter_model.safetensors")), rtol=0, atol=0)
            torch.testing.assert_close(actual["optimizer"], expected["optimizer"], rtol=0, atol=0)
            torch.testing.assert_close(actual["random"]["torch"], expected["random"]["torch"], rtol=0, atol=0)
            for key in ("python", "numpy", "cuda"):
                self.assertEqual(actual["random"][key], expected["random"][key])
            self.assertEqual(actual["schedule"], expected["schedule"])
        completed = distillation_run.file_hashes(output)
        with patch.object(distillation_run, "load_model", side_effect=AssertionError("repeated completed work")):
            distillation_run.run(path, output)
        self.assertEqual(completed, distillation_run.file_hashes(output))
        # A missing first-pass test must block completion even when the final
        # report exists. Recover its publication from the saved batch receipt.
        stage = output / "test/checkpoint-8"
        (stage / "complete.json").unlink()
        (stage / "results.json").unlink()
        shutil.rmtree(stage / "note-0001")
        with self.assertRaises((ValueError, FileNotFoundError)):
            distillation_run.verify_subject_run(output, data, config)
        with patch.object(distillation_run, "train_subject_block", side_effect=AssertionError("retrained")), \
                patch.object(distillation_run, "generate_batch", side_effect=AssertionError("regenerated saved answer")):
            distillation_run.run(path, output)
        distillation_run.verify_subject_run(output, data, config)
        self.assertEqual(before, distillation_run.file_hashes(parent))
        # The rented machine cannot see the original local parent directory.
        # Packaging must carry the sealed parent, without its unused checkpoints.
        from sse_multivector import distillation_deploy as deploy
        package = root / "continuation-package"
        preparation = {**original, "training_milestones": [1, 3], "preparation": {
            "max_new_tokens": 4, "cache_fill_tokens": 16, "train_note_ids": ["0", "1", "2"],
            "evaluation_note_ids": ["4"]}}
        preparation_path = root / "continuation-preparation.json"
        distillation_run.write_json(preparation_path, preparation)
        subprocess.run([sys.executable, "-m", "sse_multivector.distillation_deploy", "prepare-continuation",
            "--parent-run", str(parent), "--data", str(prepared), "--preparation-config", str(preparation_path),
            "--name", "continuation", "--output", str(package)], check=True, capture_output=True, timeout=30)
        self.assertEqual(deploy.verify_package(package)["gpu_assignments"], {"continuation": 0})
        self.assertEqual(deploy.verify_package(package)["preparation_runs"], ["preparation-configs/continuation.json"])
        self.assertIsNone(deploy.verify_package(package)["timeout_seconds"])
        packaged = distillation_run.read_json(package / "configs/continuation.json")
        self.assertTrue(packaged["continuation"]["parent_run"].startswith("parents/"))
        copied_parent = package / packaged["continuation"]["parent_run"]
        self.assertEqual(sorted(p.name for p in (copied_parent / "checkpoints").iterdir()), ["checkpoint-4"])
        parent.rename(root / "continuation-parent-archived")
        retrieved = root / "continuation-package-results"
        self.assertEqual(deploy.execute(package, retrieved)["state"], "complete")
        checked = deploy.verify_results(package, retrieved)
        self.assertEqual(checked["candidates"]["continuation"]["training"], {"examples": 12, "updates": 4})
        self.assertFalse((retrieved / "continuation/baseline").exists())

        # A public-model parent must carry its pinned cache files and download
        # them in the same rental. Keep this real parent for the SSH rehearsal.
        from sse_multivector.test_distillation_cache import fixture_hub
        files = {str(p.relative_to(Path(original['model']))): p.read_bytes()
                 for p in Path(original['model']).rglob('*') if p.is_file()}
        remote = {**original, 'model': 'fixture/cached', 'revision': 'a'*40}
        remote_path = root / 'remote-continuation-parent.json'
        remote_parent = root / 'remote-continuation-parent'
        distillation_run.write_json(remote_path, remote)
        distillation_run.write_json(root / 'remote-parent-volume/volume-identity.json',
                                   {'id': 880, 'machine_id': 12})
        with fixture_hub(files) as (port, requests):
            env = {**os.environ, 'HF_HOME': str(root / 'remote-parent-volume/model-cache'),
                   'HF_ENDPOINT': f'http://127.0.0.1:{port}',
                   'HF_HUB_OFFLINE': '0', 'TRANSFORMERS_OFFLINE': '0'}
            commands = [[sys.executable, '-m', 'sse_multivector.distillation_cache', 'prepare',
                '--config', str(remote_path), '--reserve-bytes', str(32*1024*1024),
                '--output', str(root / 'remote-continuation-cache')],
                [sys.executable, '-m', 'sse_multivector.distillation_cache', 'download',
                 '--package', str(root / 'remote-continuation-cache'),
                 '--output', str(root / 'remote-parent-download')]]
            for command in commands:
                result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([sys.executable, '-m', 'sse_multivector.distillation_run', str(remote_path),
                '--output', str(remote_parent)], env={**env, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'},
                capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
        # The parent is sealed and the SSH phase starts with its own cold cache.
        # Keep Hub symlinks out of the workflow's immutable evidence package.
        shutil.rmtree(root / 'remote-parent-volume')
        remote_preparation = {**preparation, 'model': remote['model'], 'revision': remote['revision']}
        remote_prep_path = root / 'remote-continuation-preparation.json'
        distillation_run.write_json(remote_prep_path, remote_preparation)
        with self.assertRaisesRegex(ValueError, 'cache manifest'):
            deploy.prepare_continuation(remote_parent, prepared, remote_prep_path,
                root / 'remote-without-cache', name='qwen')
        cache_path = root / 'remote-continuation-cache/model-cache.json'
        manifest = distillation_run.read_json(cache_path)
        manifest['models'].append({**manifest['models'][0], 'model': 'fixture/unused'})
        distillation_run.write_json(cache_path, manifest)
        remote_package = root / 'remote-continuation-package'
        subprocess.run([sys.executable, '-m', 'sse_multivector.distillation_deploy', 'prepare-continuation',
            '--parent-run', str(remote_parent), '--data', str(prepared),
            '--preparation-config', str(remote_prep_path), '--name', 'qwen',
            '--cache-manifest', str(cache_path), '--output', str(remote_package)],
            check=True, capture_output=True, timeout=30)
        self.assertTrue(deploy.verify_package(remote_package)['download_cache'])
        selected = distillation_run.read_json(remote_package / 'model-cache.json')
        self.assertEqual([m['model'] for m in selected['models']], ['fixture/cached'])
        self.assertEqual(selected['reserve_bytes'], 32*1024*1024)

    def test_local_recovery_rotates_two_checkpoints_and_resumes_exact_training(self):
        import shutil
        import torch
        from safetensors.torch import load_file
        root = self.root / 'local-recovery'
        source = distillation_run.read_json(self.root / 'source.json')['notes'][0]
        annotated = distillation_run.read_json(self.root / 'annotations.json')['notes'][0]
        for filename, row in [('source.json', source), ('annotations.json', annotated)]:
            distillation_run.write_json(root / filename, {'notes': [
                {**row, 'note_id': str(i), 'pubkey': str(i), 'text': row['text'] + f' {i}'}
                for i in range(642)]})
        splits = root / 'splits.json'
        distillation_run.write_json(splits, {'train': list(map(str, range(640))),
            'validation': ['640'], 'test': ['641']})
        prepared = root / 'data'
        distillation_data.prepare(root / 'source.json', root / 'annotations.json',
            self.root / 'subjects.txt', None, 'AS-test', None, 1, 'test', prepared,
            tasks=('subjects',), splits_path=splits)
        original = {k: v for k, v in self.config.items() if k not in
            ('mask_prompt', 'max_steps', 'save_steps', 'subject_fraction', 'mask_batch_size')}
        original.update(data=str(prepared), training_milestones=[640], batch_size=1,
            gradient_accumulation_steps=8, evaluation_tasks=['subjects'], max_new_tokens={'subjects': 120},
            subject_batching={'budget_bytes': 8*1024*1024, 'workspace_bytes': 0,
                             'prefill_bytes_per_token': 1024, 'attention_matrix_count': 4})
        parent = root / 'parent'
        config_path = root / 'parent.json'
        distillation_run.write_json(config_path, original)
        distillation_run.run(config_path, parent)
        previous = parent / 'checkpoints/checkpoint-640'
        config = {**original, 'training_milestones': [1280], 'continuation': {
            'parent_run': str(parent), 'manifest_sha256': distillation_run.sha256(parent / 'manifest.json'),
            'plan_sha256': distillation_run.sha256(parent / 'training-plan.json'),
            'checkpoint_sha256': distillation_run.sha256(previous / 'complete.json')}}
        config_path = root / 'continuation.json'
        distillation_run.write_json(config_path, config)
        reference, output = root / 'reference', root / 'interrupted'
        for directory in (reference, output):
            distillation_run.run(config_path, directory, 'preflight')
        selected = distillation_run.load_data(prepared)
        plan = distillation_run.read_json(output / 'training-plan.json')
        expected = distillation_run.train_subject_block(config, self.tokenizer, selected, reference,
                                                        plan, 1280, previous)
        volume = root / 'volume'
        distillation_run.write_json(volume / 'volume-identity.json', {'id': 881, 'machine_id': 12})
        environment = {'ORACLE_RUN_RECOVERY_DIR': str(volume / 'recovery-checkpoints'),
                       'HF_HOME': str(volume / 'model-cache')}
        native_step = torch.optim.AdamW.step
        completed = []
        def interrupted_step(optimizer, *args, **kwargs):
            if len(completed) == 49:
                raise RuntimeError('injected mid-pass failure')
            result = native_step(optimizer, *args, **kwargs)
            completed.append(True)
            return result
        with patch.dict(os.environ, environment):
            with patch.object(torch.optim.AdamW, 'step', interrupted_step), \
                    self.assertRaisesRegex(RuntimeError, 'injected mid-pass failure'):
                distillation_run.train_subject_block(config, self.tokenizer, selected, output,
                                                    plan, 1280, previous)
            recovery = volume / 'recovery-checkpoints' / distillation_run.sha256(output / 'manifest.json')
            saved = sorted(recovery.glob('checkpoint-*'), key=lambda p: int(p.name.split('-')[1]))
            self.assertEqual([p.name for p in saved], ['checkpoint-896', 'checkpoint-1024'])
            before = {p.name: distillation_run.file_hashes(p) for p in saved}
            native_verify = distillation_run.verify_saved
            def failed_publication(directory):
                return False if '.partial-' in Path(directory).name else native_verify(directory)
            with patch.object(distillation_run, 'verify_saved', side_effect=failed_publication), \
                    self.assertRaisesRegex(ValueError, 'publication hash mismatch'):
                distillation_run.train_subject_block(config, self.tokenizer, selected, output,
                                                    plan, 1280, previous)
            self.assertEqual({p.name: distillation_run.file_hashes(p) for p in saved}, before)
            # A killed writer may leave a partial directory. A corrupt newest
            # complete checkpoint must fall back to the preceding verified one.
            partial = recovery / 'checkpoint-1152.partial-interrupted'
            partial.mkdir()
            (partial / 'adapter_model.safetensors').write_bytes(b'incomplete')
            (saved[-1] / 'adapter_model.safetensors').write_bytes(b'corrupt')
            resumed_steps = []
            def resumed_step(optimizer, *args, **kwargs):
                resumed_steps.append(True)
                return native_step(optimizer, *args, **kwargs)
            with patch.object(torch.optim.AdamW, 'step', resumed_step):
                actual = distillation_run.train_subject_block(config, self.tokenizer, selected, output,
                                                              plan, 1280, previous)
            self.assertEqual(len(resumed_steps), 48)
            self.assertEqual(sorted(p.name for p in recovery.iterdir()),
                             ['checkpoint-1024', 'checkpoint-1152'])
            self.assertTrue(all(native_verify(p) for p in recovery.iterdir()))
        torch.testing.assert_close(load_file(str(actual / 'adapter_model.safetensors')),
                                   load_file(str(expected / 'adapter_model.safetensors')), rtol=0, atol=0)
        actual_state, expected_state = [torch.load(p / 'training-state.pt', weights_only=True)
                                        for p in (actual, expected)]
        for key in ('optimizer', 'schedule'):
            torch.testing.assert_close(actual_state[key], expected_state[key], rtol=0, atol=0)
        torch.testing.assert_close(actual_state['random']['torch'], expected_state['random']['torch'], rtol=0, atol=0)
        for key in ('python', 'numpy', 'cuda'):
            self.assertEqual(actual_state['random'][key], expected_state['random'][key])
        self.assertEqual(len(distillation_run.read_json(actual / 'training.json')['updates_this_block']), 80)
        self.assertEqual([p.name for p in (output / 'checkpoints').iterdir()], ['checkpoint-1280'])
        preparation = {**original, 'training_milestones': [1, 3], 'preparation': {
            'max_new_tokens': 4, 'cache_fill_tokens': 16, 'train_note_ids': ['0', '1', '2'],
            'evaluation_note_ids': ['640']}}
        distillation_run.write_json(root / 'preparation.json', preparation)

    def test_subject_preparation_saves_cache_measurement_before_memory_rejection(self):
        import shutil
        prepared = self.root / "failed-cache-data"
        distillation_data.prepare(self.root / "source.json", self.root / "annotations.json",
            self.root / "subjects.txt", None, "AS-test", None, 2, "test", prepared, tasks=("subjects",))
        data = distillation_run.load_data(prepared)
        removed = {"mask_prompt", "max_steps", "save_steps", "subject_fraction", "mask_batch_size"}
        config = {key: value for key, value in self.config.items() if key not in removed}
        config.update(data=str(prepared), training_milestones=[1, 3], batch_size=1,
            gradient_accumulation_steps=8, evaluation_tasks=["subjects"], max_new_tokens={"subjects": 120},
            subject_batching={"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                              "prefill_bytes_per_token": 1024, "attention_matrix_count": 4},
            preparation={"max_new_tokens": 4, "cache_fill_tokens": 16,
                         "train_note_ids": [row["note_id"] for row in data["train"]][:3],
                         "evaluation_note_ids": [row["note_id"] for row in data["evaluation"]]})
        path, output = self.root / "failed-cache.json", self.root / "failed-cache"
        distillation_run.write_json(path, config)
        # Save real checkpoints and preparation through the production CLI first.
        subprocess.run([sys.executable, "-B", "-m", "sse_multivector.distillation_run", str(path),
                        "--output", str(output), "--through", "preparation"],
                       check=True, capture_output=True, timeout=120)
        shutil.move(output / "preparation", self.root / "previous-cache-preparation")
        (output / "report.json").unlink()
        cpu_data = distillation_run.preparation_data(data, config)
        original_load = distillation_run.load_model
        original_plan = distillation_run.subject_batch_plan
        original_generate = distillation_run.generate_batch
        original_check = distillation_run.generation_cache_check
        original_metadata = distillation_run.subject_checkpoint_metadata
        cuda_config = {**config, "device": "cuda"}
        # Emulate only the unavailable GPU and its measured peak. Tokenization,
        # native-cache execution, adapter reload and output publication stay real.
        def cache(model, tokenizer, encoded, cfg, chunk):
            return {**original_check(model, tokenizer, encoded, {**cfg, "device": "cpu"}, chunk),
                    "peak_cuda_allocated_bytes": config["subject_batching"]["budget_bytes"] - 1,
                    "peak_cuda_reserved_bytes": config["subject_batching"]["budget_bytes"] + 1}
        with patch.object(distillation_run, "load_model", side_effect=lambda cfg, adapter=None:
                original_load({**cfg, "device": "cpu"}, adapter)), \
             patch.object(distillation_run, "subject_batch_plan", side_effect=lambda m, t, rows, cfg:
                original_plan(m, t, rows, {**cfg, "device": "cpu"})), \
             patch.object(distillation_run, "generate_batch", side_effect=lambda m, t, rows, cfg, task, **kw:
                original_generate(m, t, rows, {**cfg, "device": "cpu"}, task, **kw)), \
             patch.object(distillation_run, "generation_cache_check", side_effect=cache), \
             patch.object(distillation_run, "subject_checkpoint_metadata", side_effect=lambda *args:
                {**original_metadata(*args), "peak_cuda_reserved_bytes": 0}), \
             patch.object(distillation_run, "cuda_measurement", return_value={
                "peak_cuda_allocated_bytes": 0, "peak_cuda_reserved_bytes": 0}):
            with self.assertRaisesRegex(ValueError, "generation cache peak"):
                distillation_run.run_subject_preparation(cuda_config, self.tokenizer, cpu_data, output)
        check = distillation_run.read_json(output / "preparation/cache-0000.json")
        self.assertEqual(check["peak_cuda_reserved_bytes"], config["subject_batching"]["budget_bytes"] + 1)
        self.assertTrue((output / "preparation/full-validation-batches.json").is_file())
        self.assertFalse((output / "preparation/complete.json").exists())
        self.assertFalse((output / "report.json").exists())
        self.assertTrue(distillation_run.verify_saved(output / "checkpoints/checkpoint-1"))

    def test_subject_preparation_cli_checks_cache_and_restores_training_without_full_evaluations(self):
        prepared = self.root / "preparation-data"
        distillation_data.prepare(self.root / "source.json", self.root / "annotations.json",
            self.root / "subjects.txt", None, "AS-test", None, 2, "test", prepared, tasks=("subjects",))
        data = distillation_run.load_data(prepared)
        removed = {"mask_prompt", "max_steps", "save_steps", "subject_fraction", "mask_batch_size"}
        config = {key: value for key, value in self.config.items() if key not in removed}
        config.update(data=str(prepared), training_milestones=[3, 6], batch_size=1,
            gradient_accumulation_steps=8, evaluation_tasks=["subjects"],
            max_new_tokens={"subjects": 120},
            subject_batching={"budget_bytes": 8*1024*1024, "workspace_bytes": 0,
                              "prefill_bytes_per_token": 1024, "attention_matrix_count": 4},
            preparation={"max_new_tokens": 4, "cache_fill_tokens": 16,
                         "train_note_ids": [row["note_id"] for row in data["train"]],
                         "evaluation_note_ids": [row["note_id"] for row in data["evaluation"]]})
        path, output = self.root / "preparation.json", self.root / "preparation"
        distillation_run.write_json(path, config)
        command = [sys.executable, "-m", "sse_multivector.distillation_run", str(path),
                   "--output", str(output), "--through", "preparation"]
        preflight_command = [*command[:-3], str(output.with_name('preparation-preflight')),
                             '--through', 'preflight']
        preflight = subprocess.run(preflight_command, capture_output=True, text=True, timeout=30)
        self.assertEqual(preflight.returncode, 0, preflight.stderr + preflight.stdout)
        self.assertIn('no model weights loaded', preflight.stdout)
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = distillation_run.read_json(output / "report.json")
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["training"], {"examples": 6, "updates": 2})
        self.assertEqual(report["preparation"]["subject_answers"], 2)
        self.assertEqual(report["preparation"]["max_new_tokens"], 4)
        self.assertFalse((output / "baseline").exists())
        self.assertFalse((output / "evaluations").exists())
        for milestone in (3, 6):
            self.assertTrue(distillation_run.verify_saved(output / "checkpoints" / f"checkpoint-{milestone}"))
        self.assertTrue(distillation_run.verify_saved(output / "preparation"))
        # Training may use more memory than the inference batch budget. Reuse
        # real sealed checkpoints, emulating only the unavailable GPU peak.
        (output / "report.json").unlink()
        original_metadata = distillation_run.subject_checkpoint_metadata
        with patch.object(distillation_run, "subject_checkpoint_metadata", side_effect=lambda *args:
                {**original_metadata(*args), "peak_cuda_reserved_bytes":
                 config["subject_batching"]["budget_bytes"] + 1}):
            distillation_run.run_subject_preparation({**config, "device": "cuda"}, self.tokenizer,
                distillation_run.preparation_data(data, config), output)
        self.assertEqual(distillation_run.read_json(output / "report.json")["training"],
                         {"examples": 6, "updates": 2})
        for index, row in enumerate(data["evaluation"]):
            note = output / "preparation" / f"note-{index:04}"
            saved = distillation_run.read_json(note / "subjects.json")
            self.assertEqual(saved["messages"], row["messages"])
            self.assertLessEqual(saved["answer"]["tokens"], 4)
            self.assertTrue((note / "subjects-result.json").exists())
        for check in report["preparation"]["cache_checks"]:
            self.assertEqual(check["cached_tokens"], check["prompt_width"] + 120)
            self.assertGreater(check["fill_calls"], 1)
            self.assertGreater(check["decode_seconds"], 0)
        replay = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(replay.returncode, 0, replay.stderr + replay.stdout)
        self.assertIn("preparation complete (reused)", replay.stdout)
        (output / "preparation/note-0000/subjects.json").unlink()
        broken = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn("preparation hash mismatch", broken.stderr)

    def test_subject_update_loss_is_independent_of_physical_group_size(self):
        import torch
        from safetensors.torch import load_file
        annotations = distillation_run.read_json(self.root / "annotations.json")
        for i, note in enumerate(annotations["notes"]):
            note["subjects"][0]["context"] = "Tea is named. " * (i+1)
        labels = self.root / "weighted-labels.json"
        distillation_run.write_json(labels, annotations)
        prepared = self.root / "weighted-data"
        distillation_data.prepare(self.root / "source.json", labels, self.root / "subjects.txt",
            None, "AS-test", None, 2, "test", prepared, tasks=("subjects",))
        data = distillation_run.load_data(prepared)
        checkpoints = []
        for size in (1, 8):
            config = {**self.config, "batch_size": size, "gradient_accumulation_steps": 8//size,
                      "training_milestones": [6], "data": str(prepared)}
            plan = distillation_run.subject_training_plan(data, config)
            output = self.root / f"weighted-group-{size}"
            distillation_run.write_json(output / "manifest.json", {"config": config, "dataset": data["manifest"]})
            distillation_run.write_json(output / "training-plan.json", plan)
            checkpoints.append(distillation_run.train_subject_block(config, self.tokenizer, data, output, plan, 6))
        left, right = [load_file(str(path / "adapter_model.safetensors")) for path in checkpoints]
        for name in left:
            torch.testing.assert_close(left[name], right[name], rtol=1e-4, atol=1e-6)
        a, b = [distillation_run.read_json(path / "training.json")["updates_this_block"][0] for path in checkpoints]
        self.assertEqual(a["note_ids"], b["note_ids"])
        self.assertEqual(a["supervised_tokens"], b["supervised_tokens"])
        self.assertAlmostEqual(a["loss"], b["loss"], places=5)

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
