"""Host checks for candidate settings supplied separately from the runtime image."""
from pathlib import Path
import unittest
from unittest.mock import patch

from sse_multivector.distillation_run import read_json


class CandidateSettingsTests(unittest.TestCase):
    def test_dense_gpu_settings_reserve_scratch_for_the_measured_full_prompt(self):
        from sse_multivector import distillation_run
        from sse_multivector.test_distillation_run import DataContractTests
        config = read_json(Path(__file__).resolve().parents[1] / "sse_multivector/distillation/subject-pilot-gemma-dense-v1.json")
        model, tokenizer, data, _config, _answer = DataContractTests().subject_batch_fixture((1, 1))
        # Shapes measured on the full loaded 31B model during the October 5 prep.
        memory = {"resident_bytes": 61394693754, "kv_bytes_per_token": 81920,
                  "sliding_bytes_per_token": 819200, "sliding_window": 1024,
                  "state_bytes_per_note": 0, "full_layer_bytes_per_token": 8192,
                  "sliding_layer_bytes_per_token": 16384, "recurrent_layer_bytes": 0,
                  "attention_heads": 32, "vocab_size": 262144}
        with patch.object(distillation_run, "subject_batch_memory", return_value=memory), \
             patch.object(tokenizer, "encode", return_value=[1] * 9442):
            plan, _encoded = distillation_run.subject_batch_plan(model, tokenizer, data["evaluation"], config)
        self.assertEqual([len(batch["indices"]) for batch in plan["batches"]], [1, 1])
        self.assertTrue(all(batch["estimated_bytes"] <= config["subject_batching"]["budget_bytes"]
                            for batch in plan["batches"]))
