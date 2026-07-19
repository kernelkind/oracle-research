import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from full_build_package import (
    model_payload_identity,
    reconstruct_corpus,
    restore_model_metadata,
    verify_manifest,
    verify_model_payload,
    write_manifest,
    write_model_payload_identity,
)
from model_bundle import verify_bundle, write_lock


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FullBuildPackageTest(unittest.TestCase):
    def test_runbook_preserves_the_calibrated_identity_and_paid_boundary(self):
        runbook = Path(__file__).with_name("vast-full-build-runbook.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a",
            runbook,
        )
        self.assertIn("PAID BOUNDARY -- STOP HERE DURING CREC-72", runbook)
        self.assertIn("rental rate at most 1.359259 USD/hour", runbook)
        self.assertNotIn("1.359260", runbook)
        self.assertIn("/usr/bin/gzip", runbook)
        self.assertNotIn("zstd", runbook)
        self.assertIn("gte-oracle run-full-build \\", runbook)
        self.assertIn("run-full-build takes no shard ordinal", runbook)
        self.assertIn("only on the same Vast\n  instance", runbook)
        self.assertIn("No watchdog is used", runbook)
        stable = runbook.index("verify-model-payload")
        metadata = runbook.index("restore-model-metadata")
        production = runbook.index("verify package.next/bundle")
        self.assertLess(stable, metadata)
        self.assertLess(metadata, production)

    def test_model_payload_identity_ignores_cache_metadata_but_not_payload_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            metadata = model / ".huggingface" / "download"
            metadata.mkdir(parents=True)
            (model / "config.json").write_bytes(b"config\n")
            (model / "weights.safetensors").write_bytes(b"weights\n")
            (metadata / "config.json.metadata").write_bytes(b"first metadata\n")
            lock = root / "model-lock.json"
            lock.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "model_id": "Alibaba-NLP/gte-Qwen2-7B-instruct",
                        "model_revision": "a8d08b36ada9cacfe34c4d6f80957772a025daf2",
                        "files": [
                            {
                                "path": "config.json",
                                "bytes": 7,
                                "sha256": sha256(b"config\n"),
                            },
                            {
                                "path": "weights.safetensors",
                                "bytes": 8,
                                "sha256": sha256(b"weights\n"),
                            },
                            {
                                "path": ".huggingface/download/config.json.metadata",
                                "bytes": 15,
                                "sha256": sha256(b"first metadata\n"),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            identity_path = root / "model-payload.json"

            identity = write_model_payload_identity(lock, identity_path)
            self.assertEqual(len(identity["files"]), 2)
            self.assertEqual(
                verify_model_payload(model, lock, identity_path), identity
            )

            (metadata / "config.json.metadata").write_bytes(b"different metadata\n")
            self.assertEqual(
                verify_model_payload(model, lock, identity_path), identity,
                "download cache metadata is not runtime model payload",
            )

            lock_document = json.loads(lock.read_text(encoding="utf-8"))
            lock_document["files"][2] = {
                "path": ".huggingface/download/config.json.metadata",
                "bytes": 19,
                "sha256": sha256(b"different metadata\n"),
            }
            lock.write_text(json.dumps(lock_document), encoding="utf-8")
            self.assertEqual(
                model_payload_identity(lock),
                identity,
                "cache records in the legacy lock must not define stable identity",
            )
            self.assertEqual(verify_model_payload(model, lock, identity_path), identity)

            (model / "weights.safetensors").write_bytes(b"changed\n")
            with self.assertRaisesRegex(ValueError, "payload file"):
                verify_model_payload(model, lock, identity_path)

    def test_manifest_verifies_exact_files_and_rejects_lmdb_lock_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "control").mkdir()
            (root / "control" / "gte-oracle").write_bytes(b"controller")
            (root / "corpus").mkdir()
            (root / "corpus" / "data.mdb.zst").write_bytes(b"compressed")
            manifest_path = root / "transport-manifest.json"
            manifest_path.with_name(".transport-manifest.json.next").write_bytes(
                b"interrupted manifest"
            )

            manifest = write_manifest(root, manifest_path, "gte-full-build-transport")
            self.assertEqual(verify_manifest(root, manifest_path), manifest)
            (root / "control" / "gte-oracle").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_manifest(root, manifest_path)

            (root / "control" / "gte-oracle").write_bytes(b"controller")
            (root / "corpus" / "lock.mdb").write_bytes(b"transient")
            with self.assertRaisesRegex(ValueError, "lock.mdb"):
                write_manifest(root, manifest_path, "gte-full-build-transport")

    def test_corpus_reconstruction_publishes_only_exact_decompressed_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "data.mdb"
            source.write_bytes((b"nostr corpus\n" * 4096) + b"end")
            compressed = root / "data.mdb.gz"
            with compressed.open("wb") as output:
                subprocess.run(
                    ["gzip", "--no-name", "--stdout", str(source)],
                    check=True,
                    stdout=output,
                )
            expected = source.read_bytes()
            destination = root / "published" / "data.mdb"

            reconstruct_corpus(
                compressed,
                destination,
                len(expected),
                sha256(expected),
                Path("gzip"),
            )
            self.assertEqual(destination.read_bytes(), expected)
            self.assertEqual(
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )["sha256"],
                sha256(expected),
                "an exact published corpus is a read-only resume",
            )

            destination.write_bytes(b"wrong existing corpus")
            with self.assertRaisesRegex(ValueError, "existing corpus"):
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )

            destination.unlink()
            corrupted = bytearray(compressed.read_bytes())
            corrupted[len(corrupted) // 2] ^= 1
            compressed.write_bytes(corrupted)
            with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                reconstruct_corpus(
                    compressed,
                    destination,
                    len(expected),
                    sha256(expected),
                    Path("gzip"),
                )
            self.assertFalse(destination.exists())
            self.assertFalse(destination.with_name("data.mdb.next").exists())

    def test_exact_legacy_metadata_restores_the_production_model_verifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "legacy"
            fresh = root / "fresh"
            for model in (legacy, fresh):
                (model / ".huggingface" / "download").mkdir(parents=True)
                (model / "config.json").write_bytes(b"config\n")
                (model / "weights.safetensors").write_bytes(b"weights\n")
            legacy_metadata = legacy / ".huggingface"
            (legacy_metadata / "download" / "config.json.metadata").write_bytes(
                b"legacy metadata\n"
            )
            (fresh / ".huggingface" / "download" / "config.json.metadata").write_bytes(
                b"fresh metadata\n"
            )
            lock = root / "model-lock.json"
            write_lock(legacy, lock)
            identity_path = root / "model-payload.json"
            write_model_payload_identity(lock, identity_path)

            self.assertEqual(
                verify_model_payload(fresh, lock, identity_path)["files"],
                model_payload_identity(lock)["files"],
            )
            with self.assertRaisesRegex(ValueError, "does not match its lock"):
                verify_bundle(fresh, lock)

            transported_metadata = root / "transported-huggingface"
            shutil.copytree(legacy_metadata, transported_metadata)
            restore_model_metadata(fresh, transported_metadata)
            self.assertEqual(verify_bundle(fresh, lock)["files"], write_lock(legacy, lock)["files"])


if __name__ == "__main__":
    unittest.main()
