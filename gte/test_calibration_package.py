import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from calibration_package import (
    HostSnapshot,
    build_execution_identity,
    freeze_create_result,
    freeze_instance_record,
    freeze_template_record,
    verify_package,
    write_package_manifest,
)

class CalibrationPackageTest(unittest.TestCase):
    def make_package(self, root):
        files = {
            "bundle/model-lock.json": b"model lock",
            "bundle/model/config.json": b"{}\n",
            "corpus-root/ndb/data.mdb": b"corpus",
            "run/semantic-corpus/manifest.json": b"{}\n",
            "run/semantic-corpus/ordered-event-ids.bin": b"ids",
            "run/token-audit-semantic-v3/manifest.json": b"{}\n",
            "run/batch-plan-semantic-v5/manifest.json": b"{}\n",
            "run/representation/index/index-manifest.json": b"{}\n",
            "run/representation/index/event-id-to-row.bin": b"index",
            "run/budget-ledger.json": b"{}\n",
            "run/calibration-config.json": b"{}\n",
            "run/vast-calibration-runbook.txt": b"exact commands\n",
        }
        for relative, contents in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)

    def test_manifest_verifies_the_exact_frozen_files_and_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_package(root)
            manifest_path = root / "package-manifest.json"

            manifest = write_package_manifest(root, manifest_path)
            self.assertEqual(manifest["artifact_kind"], "gte-calibration-package")
            self.assertEqual(len(manifest["files"]), 12)
            self.assertEqual(verify_package(root, manifest_path), manifest)

            (root / "run/calibration-config.json").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_package(root, manifest_path)

    def test_manifest_refuses_an_lmdb_lock_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_package(root)
            (root / "corpus-root/ndb/lock.mdb").write_bytes(b"local lock")

            with self.assertRaisesRegex(ValueError, "lock.mdb"):
                write_package_manifest(root, root / "package-manifest.json")

    def test_execution_identity_combines_the_offline_descriptor_offer_and_live_host(self):
        descriptor = {
            "model_id": "Alibaba-NLP/gte-Qwen2-7B-instruct",
            "model_revision": "a8d08b36ada9cacfe34c4d6f80957772a025daf2",
            "model_lock_sha256": "1" * 64,
            "worker_sha256": "2" * 64,
            "dependency_lock_sha256": "3" * 64,
            "container_image": "docker.io/kernelkind/oracle-mvp@sha256:" + "4" * 64,
            "torch_version": "2.12.1",
            "transformers_version": "4.41.2",
            "cuda_version": "13.0.2",
            "execution_device": "cuda",
            "dimensions": 3584,
            "model_token_ceiling": 32768,
            "document_input": "raw-note-content",
            "query_instruction": "fixed instruction",
            "pooling": "last-token",
            "normalization": "l2",
            "numeric_format": "f32le",
        }
        descriptor_json = json.dumps(
            descriptor, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        )
        descriptor_result = {
            "descriptor": dict(sorted(descriptor.items())),
            "descriptor_json": descriptor_json,
            "descriptor_sha256": hashlib.sha256(descriptor_json.encode("utf-8")).hexdigest(),
        }
        offer = {
            "id": 33693061,
            "machine_id": 21555,
            "bundle_id": 1075358098,
            "gpu_name": "RTX PRO 6000 WS",
            "gpu_max_power": 600.0,
            "num_gpus": 1,
            "driver_version": "595.84",
            "reliability": 0.99864,
            "disk_bw": 8615.0,
            "duration": 86400.9,
            "dph_total": 1.5407001,
            "is_bid": False,
            "rentable": True,
            "verification": "verified",
            "vericode": 1,
        }
        instance = {
            "id": 88001234,
            "machine_id": 21555,
            "bundle_id": 1075358098,
            "actual_status": "running",
            "intended_status": "running",
            "image_uuid": descriptor["container_image"],
            "gpu_name": "RTX PRO 6000 WS",
            "num_gpus": 1,
            "disk_space": 200.0,
            "dph_total": 1.6400001,
            "is_bid": False,
            "verification": "verified",
        }
        create_result = {"success": True, "new_contract": 88001234}
        host = HostSnapshot(
            gpu_model="NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
            gpu_device_uuid="GPU-real",
            gpu_count=1,
            gpu_power_limit_watts=600,
            driver_version="595.84",
            host_cpu="AMD EPYC",
            host_memory_bytes=192 * 1024**3,
            local_nvme_bytes=200_000_000_000,
        )

        identity = build_execution_identity(
            descriptor_result, offer, create_result, instance, host
        )
        self.assertEqual(identity["schema_version"], 2)
        self.assertEqual(
            identity["representation_descriptor_sha256"],
            descriptor_result["descriptor_sha256"],
        )
        self.assertEqual(identity["rental_offer_id"], "33693061")
        self.assertEqual(identity["rental_instance_id"], "88001234")
        self.assertEqual(identity["rental_rate_per_hour"], 1_640_001)
        self.assertEqual(identity["reliability_millionths"], 998_640)
        self.assertEqual(identity["local_nvme_bandwidth_bytes_per_second"], 8_615_000_000)
        self.assertEqual(identity["available_duration_seconds"], 86_400)

        instance["bundle_id"] = None
        identity = build_execution_identity(
            descriptor_result, offer, create_result, instance, host
        )
        self.assertEqual(identity["rental_instance_id"], "88001234")

        instance["bundle_id"] = 99999
        with self.assertRaisesRegex(ValueError, "actual Vast instance"):
            build_execution_identity(
                descriptor_result, offer, create_result, instance, host
            )

        instance["bundle_id"] = offer["bundle_id"]
        instance["machine_id"] = 99999
        with self.assertRaisesRegex(ValueError, "actual Vast instance"):
            build_execution_identity(
                descriptor_result, offer, create_result, instance, host
            )

        instance["machine_id"] = offer["machine_id"]
        offer["duration"] = 86399.9
        with self.assertRaisesRegex(ValueError, "approved calibration contract"):
            build_execution_identity(
                descriptor_result, offer, create_result, instance, host
            )

    def test_instance_record_binds_the_create_result_and_discards_secrets(self):
        create_result = {"success": True, "new_contract": 88001234}
        raw = {
            "instances": {
                "id": 88001234,
                "machine_id": 21555,
                "bundle_id": 1075358098,
                "actual_status": "running",
                "intended_status": "running",
                "image_uuid": "kernelkind/oracle-mvp@sha256:" + "4" * 64,
                "gpu_name": "RTX PRO 6000 WS",
                "num_gpus": 1,
                "disk_space": 200.0,
                "dph_total": 1.64,
                "is_bid": False,
                "verification": "verified",
                "jupyter_token": "must-not-survive",
            }
        }

        record = freeze_instance_record(create_result, raw)
        self.assertEqual(record["id"], 88001234)
        self.assertNotIn("jupyter_token", record)

        create_result["new_contract"] = 99999
        with self.assertRaisesRegex(ValueError, "create result"):
            freeze_instance_record(create_result, raw)

    def test_create_result_discards_instance_credentials(self):
        raw = {
            "success": True,
            "new_contract": 88001234,
            "instance_api_key": "must-not-survive",
        }

        record = freeze_create_result(raw)
        self.assertEqual(record, {"success": True, "new_contract": 88001234})

    def test_runbook_launches_the_private_image_directly_without_a_template(self):
        runbook = Path(__file__).with_name("vast-calibration-runbook.txt").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("PRIVATE_TEMPLATE_HASH", runbook)
        self.assertNotIn("search templates", runbook)
        self.assertNotIn("freeze-template", runbook)
        self.assertNotIn("template.json", runbook)
        self.assertNotIn("--template_hash", runbook)
        self.assertIn('--image "$IMAGE_REF"', runbook)
        self.assertIn('--login "$DOCKER_LOGIN"', runbook)
        self.assertIn("--disk 200", runbook)
        self.assertIn("--label crec-62-gte-calibration", runbook)
        self.assertIn("--ssh \\", runbook)
        self.assertIn("--direct \\", runbook)
        self.assertIn("--cancel-unavail", runbook)
        self.assertIn("--retry 1", runbook)
        self.assertIn("2> /dev/null", runbook)
        self.assertIn("freeze-create \\", runbook)
        self.assertIn("/dev/stdin \\", runbook)
        self.assertNotIn("create-result.raw.json", runbook)
        self.assertNotIn("create-result.stderr", runbook)
        self.assertIn('docker --config "$PULL_CONFIG" login', runbook)
        self.assertIn('if test -z "$DOCKER_PULL_PAT"; then', runbook)

        for marker in ("PREFLIGHT_AUTH", "DIRECT_LAUNCH"):
            block = runbook.split(f"<<'{marker}'\n", 1)[1].split(
                f"\n{marker}\n", 1
            )[0]
            subprocess.run(
                ["bash", "-n"], input=block, check=True, text=True
            )

    def test_runbook_selects_from_the_constrained_offer_list_and_refreshes_before_launch(self):
        runbook = Path(__file__).with_name("vast-calibration-runbook.txt").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("id=$OFFER_ID", runbook)
        self.assertIn(
            'export OFFER_QUERY="$BASE_QUERY geolocation in [US]"', runbook
        )
        self.assertEqual(runbook.count('    "$OFFER_QUERY" \\'), 2)
        self.assertIn(
            'printf \'%s\\n\' "$OFFER_QUERY" > '
            '"$LOCAL_ROOT/launch/offer-query.txt"',
            runbook,
        )
        selector = runbook.split("<<'SELECT_OFFER'\n", 1)[1].split(
            "\nSELECT_OFFER\n", 1
        )[0]
        self.assertEqual(runbook.count("<<'SELECT_OFFER'"), 1)
        self.assertEqual(
            runbook.count(
                'select_offer "$LOCAL_ROOT/launch/offers.json" \\\n'
                '    "$LOCAL_ROOT/launch/offer.json"'
            ),
            1,
        )
        self.assertEqual(
            runbook.count(
                'select_offer "$LOCAL_ROOT/launch/offers.refresh.json" \\\n'
                '    "$LOCAL_ROOT/launch/offer.json"'
            ),
            1,
        )
        refresh = runbook.index('> "$LOCAL_ROOT/launch/offers.refresh.json"')
        launch = runbook.index("env -u DOCKER_PULL_PAT bash <<'DIRECT_LAUNCH'")
        self.assertLess(refresh, launch)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            offers = root / "offers.json"
            selected = root / "offer.json"
            offers.write_text(
                json.dumps(
                    [
                        {"id": 11, "dph_total": 1.5},
                        {"id": 22, "dph_total": 1.2},
                    ]
                ),
                encoding="utf-8",
            )
            subprocess.run(
                ["python3", "-", str(offers), "22", str(selected)],
                input=selector,
                check=True,
                text=True,
            )
            self.assertEqual(
                json.loads(selected.read_text(encoding="utf-8")),
                [{"dph_total": 1.2, "id": 22}],
            )

            missing = subprocess.run(
                ["python3", "-", str(offers), "33", str(selected)],
                input=selector,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse(selected.exists())

            offers.write_text(
                json.dumps([{"id": 22}, {"id": 22}]), encoding="utf-8"
            )
            duplicate = subprocess.run(
                ["python3", "-", str(offers), "22", str(selected)],
                input=selector,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertFalse(selected.exists())

    def test_paid_launch_requires_the_refreshed_offer_record(self):
        runbook = Path(__file__).with_name("vast-calibration-runbook.txt").read_text(
            encoding="utf-8"
        )

        validator = runbook.split("<<'VALIDATE_OFFER'\n", 1)[1].split(
            "\nVALIDATE_OFFER\n", 1
        )[0]
        direct_launch = runbook.index(
            "env -u DOCKER_PULL_PAT bash <<'DIRECT_LAUNCH'"
        )
        validation = runbook.index("<<'VALIDATE_OFFER'", direct_launch)
        credential = runbook.index("read -rsp", direct_launch)
        paid_call = runbook.index('vastai create instance "$OFFER_ID"', direct_launch)
        self.assertLess(validation, credential)
        self.assertLess(validation, paid_call)

        with tempfile.TemporaryDirectory() as temporary:
            offer = Path(temporary) / "offer.json"
            offer.write_text(json.dumps([{"id": 22}]), encoding="utf-8")
            subprocess.run(
                ["python3", "-", str(offer), "22"],
                input=validator,
                check=True,
                text=True,
            )

            for path, offer_id in (
                (Path(temporary) / "missing.json", "22"),
                (offer, "33"),
            ):
                rejected = subprocess.run(
                    ["python3", "-", str(path), offer_id],
                    input=validator,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(rejected.returncode, 0)

            offer.write_text(json.dumps([{"id": -1}]), encoding="utf-8")
            invalid_id = subprocess.run(
                ["python3", "-", str(offer), "-1"],
                input=validator,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(invalid_id.returncode, 0)

    def test_template_record_binds_the_exact_private_image_without_retaining_login(self):
        image = "kernelkind/oracle-mvp@sha256:" + "4" * 64
        raw = [
            {
                "hash_id": "template-hash",
                "name": "oracle calibration",
                "image": image,
                "tag": None,
                "recommended_disk_space": 200.0,
                "private": True,
                "ssh_direct": True,
                "use_ssh": True,
                "runtype": "ssh",
                "env": "",
                "onstart": "",
                "args_str": "",
                "user": None,
                "use_jupyter_lab": False,
                "docker_login": "must-not-survive",
            }
        ]

        record = freeze_template_record(raw, "template-hash", "docker.io/" + image)
        self.assertEqual(record["hash_id"], "template-hash")
        self.assertEqual(record["effective_image"], image)
        self.assertNotIn("docker_login", record)

        raw[0]["image"] = "kernelkind/oracle-mvp@sha256:" + "5" * 64
        with self.assertRaisesRegex(ValueError, "exact calibration image"):
            freeze_template_record(raw, "template-hash", image)

        raw[0]["image"] = image
        raw[0]["use_ssh"] = False
        with self.assertRaisesRegex(ValueError, "SSH"):
            freeze_template_record(raw, "template-hash", image)

        raw[0]["use_ssh"] = True
        raw[0]["private"] = False
        with self.assertRaisesRegex(ValueError, "private"):
            freeze_template_record(raw, "template-hash", image)

        raw[0]["private"] = True
        raw[0]["onstart"] = "curl example.invalid"
        with self.assertRaisesRegex(ValueError, "startup overrides"):
            freeze_template_record(raw, "template-hash", image)

        raw[0]["onstart"] = ""
        raw[0]["image"] = "kernelkind/oracle-mvp:mutable"
        with self.assertRaisesRegex(ValueError, "immutable digest"):
            freeze_template_record(
                raw,
                "template-hash",
                "kernelkind/oracle-mvp:mutable",
            )


if __name__ == "__main__":
    unittest.main()
