import json
import os
import tempfile
import unittest
from pathlib import Path

from topic_map.prepare_resource_preflight import prepare_resource_preflight


class PrepareResourcePreflightTests(unittest.TestCase):
    def test_preparation_is_bounded_and_self_consistent(self) -> None:
        runtime_directory = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"))
        with tempfile.TemporaryDirectory(
            prefix="crec113-prepare-test.", dir=runtime_directory
        ) as temporary:
            root = Path(temporary) / "run"

            config_path = prepare_resource_preflight(
                root,
                learning_rows=6,
                evaluation_rows=2,
                dimensions=4,
                dictionary_size=8,
                average_k=2,
                batch_size=2,
                steps=2,
            )

            config = json.loads(config_path.read_text())
            self.assertEqual(128, (root / "vectors.f32le").stat().st_size)
            self.assertEqual(256, (root / "note-ids.bin").stat().st_size)
            self.assertEqual(
                384, config["io_budget"]["max_source_read_bytes"]
            )
            self.assertEqual(str(root / "output" / "relation"), config["output_path"])


if __name__ == "__main__":
    unittest.main()
