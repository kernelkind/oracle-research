import hashlib
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import topic_map.encode_sample as encode_sample_module
from topic_map.encode_sample import (
    CANONICAL_TREE_HASH_RULE,
    EncoderDescriptor,
    RuntimeDescriptor,
    SampleEmbeddingConfig,
    _canonical_tree_sha256,
    encode_sample,
)


class DeterministicEncoder:
    def __init__(self, descriptor: EncoderDescriptor) -> None:
        self.descriptor = descriptor

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [
            [
                float(len(text)),
                float(sum(map(ord, text)) % 101),
                float(index + 1),
            ]
            for index, text in enumerate(texts)
        ]


class MutatingEncoder(DeterministicEncoder):
    def __init__(
        self,
        descriptor: EncoderDescriptor,
        *,
        path: Path,
        replacement: bytes,
    ) -> None:
        super().__init__(descriptor)
        self.path = path
        self.replacement = replacement
        self.calls = 0

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls == 1:
            self.path.write_bytes(self.replacement)
        return super().encode_batch(texts)


class SampleEncodingTests(unittest.TestCase):
    def test_binds_learning_first_sample_rows_to_frozen_encoder_vectors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            model.mkdir()
            (model / "weights.bin").write_bytes(b"frozen model")
            dependencies = root / "dependencies"
            dependencies.mkdir()
            (dependencies / "runtime.py").write_bytes(b"frozen runtime")
            sample_root = root / "sample"
            sample_root.mkdir()
            records = [
                {
                    "split": "learning",
                    "note_id": "11" * 32,
                    "pubkey": "aa" * 32,
                    "content": "Rust ownership and borrowing",
                },
                {
                    "split": "learning",
                    "note_id": "22" * 32,
                    "pubkey": "bb" * 32,
                    "content": "Growing tomatoes in containers",
                },
                {
                    "split": "evaluation",
                    "note_id": "33" * 32,
                    "pubkey": "cc" * 32,
                    "content": "Jazz harmony and improvisation",
                },
            ]
            sample_bytes = b"".join(
                (
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                ).encode()
                for record in records
            )
            (sample_root / "sample.jsonl").write_bytes(sample_bytes)
            sample_manifest = {
                "schema_version": 2,
                "selection_rule": (
                    "semantic-order-prefix-author-hash-text-copy-disjoint-"
                    "learning-first-v2"
                ),
                "learning_rows": 2,
                "evaluation_rows": 1,
                "sample": {
                    "file": "sample.jsonl",
                    "bytes": len(sample_bytes),
                    "records": 3,
                    "sha256": hashlib.sha256(sample_bytes).hexdigest(),
                },
            }
            manifest_path = sample_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(sample_manifest, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            descriptor = EncoderDescriptor(
                model_id="example/encoder",
                model_revision="0123456789abcdef",
                dimensions=3,
                pooling="cls-token-no-normalization-v1",
                maximum_tokens=64,
                numeric_type="float32",
            )
            runtime = RuntimeDescriptor(
                canonical_tree_hash_rule=CANONICAL_TREE_HASH_RULE,
                model_tree_sha256=_canonical_tree_sha256(model),
                dependencies_tree_sha256=_canonical_tree_sha256(dependencies),
                encoder_implementation_sha256=hashlib.sha256(
                    Path(encode_sample_module.__file__).read_bytes()
                ).hexdigest(),
                container_image=(
                    "pytorch/pytorch@sha256:"
                    "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26"
                    "bc469de4c8a28b427"
                ),
            )
            output_path = root / "embeddings"
            config = SampleEmbeddingConfig(
                schema_version=1,
                purpose="production-path-test",
                sample_manifest_path=manifest_path,
                model_path=model,
                dependencies_path=dependencies,
                encoder=descriptor,
                runtime=runtime,
                batch_size=2,
                io_maximum_sample_artifact_bytes=manifest_path.stat().st_size
                + len(sample_bytes),
                io_maximum_output_bytes=4096,
                output_path=output_path,
            )

            report = encode_sample(
                config,
                encoder=DeterministicEncoder(descriptor),
            )

            self.assertEqual(3, report.total_rows)
            self.assertEqual(2, report.learning_rows)
            self.assertEqual(1, report.evaluation_rows)
            self.assertEqual(
                manifest_path.stat().st_size + len(sample_bytes),
                report.sample_artifact_bytes_read,
            )
            self.assertEqual(
                bytes.fromhex("11" * 32 + "22" * 32 + "33" * 32),
                (output_path / "note-ids.bin").read_bytes(),
            )
            values = struct.unpack(
                "<9f", (output_path / "vectors.f32le").read_bytes()
            )
            self.assertEqual(
                (
                    float(len(records[0]["content"])),
                    float(sum(map(ord, records[0]["content"])) % 101),
                    1.0,
                    float(len(records[1]["content"])),
                    float(sum(map(ord, records[1]["content"])) % 101),
                    2.0,
                    float(len(records[2]["content"])),
                    float(sum(map(ord, records[2]["content"])) % 101),
                    1.0,
                ),
                values,
            )
            self.assertTrue(all(math.isfinite(value) for value in values))
            stored = json.loads((output_path / "manifest.json").read_text())
            self.assertEqual(descriptor.to_dict(), stored["encoder"])
            self.assertEqual(runtime.to_dict(), stored["runtime"])
            self.assertEqual(
                hashlib.sha256(sample_bytes).hexdigest(),
                stored["sample_sha256"],
            )
            self.assertEqual(3, stored["total_rows"])
            self.assertEqual(
                hashlib.sha256(
                    (output_path / "vectors.f32le").read_bytes()
                ).hexdigest(),
                stored["files"]["vectors.f32le"]["sha256"],
            )

    def test_rejects_runtime_tree_changed_during_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, descriptor, _, dependencies = self._small_config(root)
            encoder = MutatingEncoder(
                descriptor,
                path=dependencies / "runtime.py",
                replacement=b"mutated runtime",
            )

            with self.assertRaisesRegex(
                ValueError, "dependencies tree changed during encoding"
            ):
                encode_sample(config, encoder=encoder)

            self.assertFalse(config.output_path.exists())

    def test_hashes_the_exact_sample_bytes_consumed_by_the_encoder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, descriptor, sample_path, _ = self._small_config(
                root,
                large_records=True,
                batch_size=1,
            )
            original = sample_path.read_bytes()
            marker = b"B" * 128
            replacement_marker = b"C" * 128
            self.assertEqual(1, original.count(marker))
            mutated = original.replace(marker, replacement_marker)
            self.assertEqual(len(original), len(mutated))
            encoder = MutatingEncoder(
                descriptor,
                path=sample_path,
                replacement=mutated,
            )

            with self.assertRaisesRegex(
                ValueError, "sample bytes consumed differ from its manifest"
            ):
                encode_sample(config, encoder=encoder)

            self.assertFalse(config.output_path.exists())

    def _small_config(
        self,
        root: Path,
        *,
        large_records: bool = False,
        batch_size: int = 2,
    ) -> tuple[SampleEmbeddingConfig, EncoderDescriptor, Path, Path]:
        model = root / "model"
        model.mkdir()
        (model / "weights.bin").write_bytes(b"frozen model")
        dependencies = root / "dependencies"
        dependencies.mkdir()
        (dependencies / "runtime.py").write_bytes(b"frozen runtime")
        sample_root = root / "sample"
        sample_root.mkdir()
        padding = "A" * (1024 * 1024) if large_records else ""
        records = [
            {
                "split": "learning",
                "note_id": "11" * 32,
                "content": padding + " first",
            },
            {
                "split": "evaluation",
                "note_id": "22" * 32,
                "content": padding + ("B" * 128) + " second",
            },
        ]
        sample_bytes = b"".join(
            (
                json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            ).encode()
            for record in records
        )
        sample_path = sample_root / "sample.jsonl"
        sample_path.write_bytes(sample_bytes)
        manifest = {
            "schema_version": 2,
            "selection_rule": (
                "semantic-order-prefix-author-hash-text-copy-disjoint-"
                "learning-first-v2"
            ),
            "learning_rows": 1,
            "evaluation_rows": 1,
            "sample": {
                "file": sample_path.name,
                "bytes": len(sample_bytes),
                "records": 2,
                "sha256": hashlib.sha256(sample_bytes).hexdigest(),
            },
        }
        manifest_path = sample_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
        descriptor = EncoderDescriptor(
            model_id="example/encoder",
            model_revision="0123456789abcdef",
            dimensions=3,
            pooling="cls-token-no-normalization-v1",
            maximum_tokens=2_000_000,
            numeric_type="float32",
        )
        runtime = RuntimeDescriptor(
            canonical_tree_hash_rule=CANONICAL_TREE_HASH_RULE,
            model_tree_sha256=_canonical_tree_sha256(model),
            dependencies_tree_sha256=_canonical_tree_sha256(dependencies),
            encoder_implementation_sha256=hashlib.sha256(
                Path(encode_sample_module.__file__).read_bytes()
            ).hexdigest(),
            container_image=(
                "pytorch/pytorch@sha256:"
                "72f863fa1fe13d5d87a72d00db2c85fb2d43409ee08dd26"
                "bc469de4c8a28b427"
            ),
        )
        config = SampleEmbeddingConfig(
            schema_version=1,
            purpose="production-path-test",
            sample_manifest_path=manifest_path,
            model_path=model,
            dependencies_path=dependencies,
            encoder=descriptor,
            runtime=runtime,
            batch_size=batch_size,
            io_maximum_sample_artifact_bytes=(
                manifest_path.stat().st_size + len(sample_bytes)
            ),
            io_maximum_output_bytes=4096,
            output_path=root / "embeddings",
        )
        return config, descriptor, sample_path, dependencies


if __name__ == "__main__":
    unittest.main()
