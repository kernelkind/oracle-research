import tempfile
import unittest
from pathlib import Path

from model_bundle import verify_bundle, write_lock


class ModelBundleTest(unittest.TestCase):
    def test_lock_verifies_exact_files_and_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n", encoding="utf-8")
            (model / "weights.safetensors").write_bytes(b"fixed weights")
            lock = root / "model-lock.json"

            write_lock(model, lock)
            verified = verify_bundle(model, lock)
            self.assertEqual(verified["model_revision"], "a8d08b36ada9cacfe34c4d6f80957772a025daf2")
            self.assertEqual(len(verified["files"]), 2)

            (model / "weights.safetensors").write_bytes(b"mutated")
            with self.assertRaisesRegex(ValueError, "does not match its lock"):
                verify_bundle(model, lock)


if __name__ == "__main__":
    unittest.main()
