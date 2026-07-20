import hashlib
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from full_build_package import (
    finalize_provider_invoice,
    freeze_full_build_offer,
    merge_provider_invoice_pages,
    model_payload_identity,
    reconstruct_corpus,
    restore_model_metadata,
    verify_manifest,
    verify_model_payload,
    validate_provider_invoice_page,
    write_manifest,
    write_model_payload_identity,
)
from model_bundle import verify_bundle, write_lock


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FullBuildPackageTest(unittest.TestCase):
    def test_provider_invoice_page_validation_rejects_cli_error_output(self):
        valid = {
            "success": True,
            "count": 1,
            "total": 3,
            "next_token": "next-page",
            "results": [{"amount": "1.25", "source": "instance-1"}],
        }
        with tempfile.TemporaryDirectory() as temporary:
            page = Path(temporary) / "page.json"
            page.write_text(json.dumps(valid), encoding="utf-8")
            self.assertEqual(validate_provider_invoice_page(page), valid)

            for invalid in (
                "",
                "not JSON",
                json.dumps({"success": False, "msg": "temporary API error"}),
                json.dumps(dict(valid, count=0)),
                json.dumps(dict(valid, total=0)),
                json.dumps(dict(valid, next_token="")),
            ):
                with self.subTest(invalid=invalid):
                    page.write_text(invalid, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "invoice page"):
                        validate_provider_invoice_page(page)

    def test_full_build_offer_is_frozen_only_after_every_paid_gate_passes(self):
        offer = {
            "id": 45236567,
            "machine_id": 37297,
            "bundle_id": 1075352023,
            "gpu_name": "RTX PRO 6000 WS",
            "num_gpus": 1,
            "gpu_max_power": 600.0,
            "reliability": 0.998,
            "cpu_arch": "amd64",
            "cpu_ram": 192708,
            "disk_space": 6409.4,
            "disk_bw": 12083.2,
            "inet_down": 2327.2,
            "inet_down_cost": 0.0078125,
            "inet_up": 2348.4,
            "inet_up_cost": 0.0078125,
            "direct_port_count": 299,
            "driver_version": "595.80",
            "duration": 172800,
            "rentable": True,
            "rented": False,
            "is_bid": False,
            "verification": "verified",
            "vericode": 1,
            "dph_total": 1.3592592592592592,
        }
        invalid = {
            "gpu_name": "RTX 4090",
            "num_gpus": 2,
            "gpu_max_power": 599,
            "reliability": 0.994,
            "cpu_arch": "arm64",
            "cpu_ram": 137438,
            "disk_space": 199,
            "disk_bw": 999,
            "inet_down": 499,
            "inet_down_cost": 0.020001,
            "inet_up": 99,
            "inet_up_cost": 0.020001,
            "direct_port_count": 0,
            "driver_version": "580.95.04",
            "duration": 172799,
            "rentable": False,
            "rented": True,
            "is_bid": True,
            "verification": "unverified",
            "vericode": 0,
            "dph_total": 1.3592600001,
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "offers.json"
            output = root / "offer.json"
            source.write_text(json.dumps([offer]), encoding="utf-8")
            self.assertEqual(
                freeze_full_build_offer(source, str(offer["id"]), output), [offer]
            )

            for field, value in invalid.items():
                with self.subTest(field=field):
                    rejected = dict(offer)
                    rejected[field] = value
                    source.write_text(json.dumps([rejected]), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        freeze_full_build_offer(source, str(offer["id"]), output)

            for field, value in (("machine_id", 0), ("bundle_id", -1)):
                with self.subTest(field=field):
                    rejected = dict(offer)
                    rejected[field] = value
                    source.write_text(json.dumps([rejected]), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, field):
                        freeze_full_build_offer(source, str(offer["id"]), output)

            rejected = dict(offer)
            rejected["gpu_max_power"] = 601
            source.write_text(json.dumps([rejected]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gpu_max_power"):
                freeze_full_build_offer(source, str(offer["id"]), output)

            refreshed = dict(offer)
            refreshed["machine_id"] += 1
            source.write_text(json.dumps([refreshed]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approved offer"):
                freeze_full_build_offer(
                    source, str(offer["id"]), output, approved_offer_path=output
                )

            for field, value in (
                ("dph_total", 1.3592593),
                ("inet_down_cost", 0.008),
                ("inet_up_cost", 0.008),
            ):
                with self.subTest(refreshed_field=field):
                    refreshed = dict(offer)
                    refreshed[field] = value
                    source.write_text(json.dumps([refreshed]), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "approved offer"):
                        freeze_full_build_offer(
                            source,
                            str(offer["id"]),
                            root / f"refreshed-{field}.json",
                            approved_offer_path=output,
                        )

    def test_finalized_invoice_is_complete_exact_and_retryable(self):
        rows = [
            {
                "amount": "1.200001",
                "source": "instance-900000024",
                "type": "instance",
                "metadata": {"label": "crec-72-gte-full-build"},
            },
            {
                "amount": "0.062",
                "source": "instance-900000024",
                "type": "instance",
                "metadata": {"label": "crec-72-gte-full-build"},
            },
            {
                "amount": "99",
                "source": "instance-other",
                "type": "instance",
                "metadata": {"label": "other"},
            },
        ]
        document = {
            "success": True,
            "count": len(rows),
            "total": len(rows),
            "next_token": None,
            "results": rows,
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "invoice.json"
            confirmation = root / "invoice-confirmation.json"
            output = root / "charge.json"
            source.write_text(json.dumps(document), encoding="utf-8")
            confirmation.write_text(json.dumps(document), encoding="utf-8")
            output.with_name(f".{output.name}.next").write_text(
                "interrupted", encoding="utf-8"
            )

            result = finalize_provider_invoice(
                source,
                confirmation,
                "900000024",
                "crec-72-gte-full-build",
                "2026-07-20T00:30:00Z",
                "2026-07-20T00:31:00Z",
                "2026-07-20T00:36:00Z",
                output,
            )
            self.assertEqual(result["actual_charge_micro_usd"], 1_262_001)
            self.assertEqual(result["invoice_rows"], 2)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)

            unlabeled = dict(document)
            unlabeled["results"] = [rows[0], dict(rows[1], metadata={})]
            unlabeled["count"] = unlabeled["total"] = 2
            source.write_text(json.dumps(unlabeled), encoding="utf-8")
            confirmation.write_text(json.dumps(unlabeled), encoding="utf-8")
            result = finalize_provider_invoice(
                source,
                confirmation,
                "900000024",
                "crec-72-gte-full-build",
                "2026-07-20T00:30:00Z",
                "2026-07-20T00:31:00Z",
                "2026-07-20T00:36:00Z",
                output,
            )
            self.assertEqual(result["actual_charge_micro_usd"], 1_262_001)
            self.assertEqual(result["invoice_rows"], 2)

            for field, value in (
                ("success", False),
                ("next_token", "next"),
                ("count", len(rows) - 1),
                ("total", len(rows) + 1),
            ):
                with self.subTest(field=field):
                    invalid = dict(document)
                    invalid[field] = value
                    source.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "complete"):
                        finalize_provider_invoice(
                            source,
                            confirmation,
                            "900000024",
                            "crec-72-gte-full-build",
                            "2026-07-20T00:30:00Z",
                            "2026-07-20T00:31:00Z",
                            "2026-07-20T00:36:00Z",
                            output,
                        )

            for field, value in (("type", "gpu"), ("metadata", {"label": "wrong"})):
                with self.subTest(match_field=field):
                    invalid = dict(document)
                    invalid["results"] = [dict(rows[0], **{field: value})]
                    invalid["count"] = invalid["total"] = 1
                    source.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "instance row"):
                        finalize_provider_invoice(
                            source,
                            confirmation,
                            "900000024",
                            "crec-72-gte-full-build",
                            "2026-07-20T00:30:00Z",
                            "2026-07-20T00:31:00Z",
                            "2026-07-20T00:36:00Z",
                            output,
                        )

            invalid = dict(document)
            invalid["results"] = [dict(rows[0], source="instance-wrong")]
            invalid["count"] = invalid["total"] = 1
            source.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not available"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            invalid = dict(document)
            invalid["results"] = [dict(rows[0], amount="0.0000001")]
            invalid["count"] = invalid["total"] = 1
            source.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "micro-USD"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            source.write_text(json.dumps(document), encoding="utf-8")
            confirmation.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not-before"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:29:59Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

            with self.assertRaisesRegex(ValueError, "five minutes"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:35:59Z",
                    output,
                )

            changed = dict(document)
            changed["results"] = [rows[0], dict(rows[1], amount="0.063")]
            changed["count"] = changed["total"] = 2
            confirmation.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not stable"):
                finalize_provider_invoice(
                    source,
                    confirmation,
                    "900000024",
                    "crec-72-gte-full-build",
                    "2026-07-20T00:30:00Z",
                    "2026-07-20T00:31:00Z",
                    "2026-07-20T00:36:00Z",
                    output,
                )

    def test_provider_invoice_pages_are_merged_only_when_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "000001.json"
            second = root / "000002.json"
            output = root / "merged.json"
            rows = [
                {
                    "source": "instance-900000024",
                    "type": "instance",
                    "metadata": {"label": "crec-72-gte-full-build"},
                    "amount": "1.000000",
                    "start": 1,
                },
                {
                    "source": "instance-900000024",
                    "type": "instance",
                    "metadata": {"label": "crec-72-gte-full-build"},
                    "amount": "2.000000",
                    "start": 2,
                },
            ]
            first.write_text(
                json.dumps(
                    {
                        "success": True,
                        "count": 1,
                        "total": 2,
                        "next_token": "page-two",
                        "results": rows[:1],
                    }
                ),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "success": True,
                        "count": 1,
                        "total": 2,
                        "next_token": None,
                        "results": rows[1:],
                    }
                ),
                encoding="utf-8",
            )

            merged = merge_provider_invoice_pages([first, second], output)
            self.assertEqual(merged["results"], rows)
            self.assertEqual(merged["count"], 2)
            self.assertEqual(merged["total"], 2)
            self.assertIsNone(merged["next_token"])

            with self.assertRaisesRegex(ValueError, "terminal"):
                merge_provider_invoice_pages([first], output)

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
