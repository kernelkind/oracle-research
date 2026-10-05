"""Exercise benchmark admission before any model or CUDA allocation."""
import unittest

from sse_multivector import distillation_benchmark


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


if __name__ == "__main__":
    unittest.main()
