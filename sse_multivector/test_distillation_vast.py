"""Rental lifecycle checks; the provider boundary never contacts Vast."""
import os
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from sse_multivector import distillation_vast as vast
from sse_multivector import distillation_deploy as deploy
from sse_multivector.distillation_run import read_json, write_json


class Provider:
    def __init__(self, target):
        self.target = target
        self.rows = []
        self.creates = self.destroys = 0
        self.ambiguous = False
        self.lost_destroy = False

    def create(self, offer, image, label, key, settings, output):
        self.creates += 1
        (output / "create-attempted").write_text("attempted")
        self.rows = [{**offer, "id": 456, "label": label, "image_uuid": image,
            "actual_status": "running", "intended_status": "running",
            "public_ipaddr": self.target["host"].removeprefix("root@"),
            "ports": {"22/tcp": [{"HostPort": str(self.target["port"])}]},
            "inet_down_billed": 0, "inet_up_billed": 0}]
        if self.ambiguous:
            raise ConnectionError("lost create response")
        write_json(output / "create-outcome.json", {"success": True, "new_contract": 456})

    def instances(self):
        return self.rows

    def destroy(self, instance_id):
        self.destroys += 1
        self.rows = [r for r in self.rows if r["id"] != instance_id]
        if self.lost_destroy:
            raise ConnectionError("lost destroy response")


def quote():
    settings = read_json(Path(__file__).parent / "distillation/vast-launch.json")
    return settings, {**settings["offer_equals"], **settings["offer_minimums"],
        **settings["offer_maximums"], "id": 123, "machine_id": 12, "bundle_id": 23,
        "driver_version": "595.58.03", "dph_base": 1.5, "storage_cost": .24,
        "storage_total_cost": .1}


class LifecycleTests(unittest.TestCase):
    def test_loading_instance_waits_for_runtime_metadata_before_validation(self):
        from sse_multivector.test_distillation_data import DistillationDataTests
        settings, offer = quote()
        provider = Provider({"host": "root@target", "port": 22})
        instances = provider.instances
        def loading_first():
            if not getattr(provider, "seen", False):
                provider.seen = True
                row = provider.rows[0]
                return [{"id": row["id"], "label": row["label"], "actual_status": "loading"}]
            return instances()
        provider.instances = loading_first
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            DistillationDataTests().prepare(root)
            (root / "model").mkdir()
            config = root / "candidate.json"
            write_json(config, {"data": str(root / "prepared"), "mask_prompt": str(root / "masks.txt"),
                "model": str(root / "model"), "revision": None})
            package, output = root / "package", root / "rental"
            deploy.prepare([config], package, 60, through="preflight")
            saved = {"state": "complete", "package_sha256": deploy.sha256(package / "manifest.json")}
            def completed_operator(*args, **kwargs):
                result = output / "deployment/result"
                write_json(result / "deployment.json", saved)
                deploy.write_manifest(result, result / "manifest.json", "distillation-results")
                return SimpleNamespace(poll=lambda: 0)
            with patch.object(vast.time, "sleep"), patch.object(vast.subprocess, "Popen", side_effect=completed_operator):
                outcome = vast.run_rental(package, output, settings,
                    settings["image_repository"] + "@sha256:" + "4" * 64, offer, root / "key", provider)
            self.assertEqual(outcome["state"], "complete", outcome)
            self.assertEqual(provider.creates, 1)
            self.assertEqual(provider.destroys, 1)

    def test_launch_requires_committed_reservation_bound_to_output_image_and_package(self):
        settings, _ = quote()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "package"
            package.mkdir()
            (package / "manifest.json").write_text("{}")
            output = root / "rental"
            ledger = {"schema_version": 3, "currency": "USD", "scope": "Entire oracle MVP effort",
                "lifetime_cap_cents": 100000, "actual_spend_cents": 100, "outstanding_commitments_cents": 2500,
                "reserved_remaining_work_cents": 0, "entries": [{"kind": "distillation_reservation",
                    "reservation_id": "pilot", "image": "image", "package_sha256": deploy.sha256(package / "manifest.json"),
                    "deployment_directory": str(output), "reserved_maximum_charge_cents": 2500}]}
            data = json.dumps(ledger).encode()
            (root / "budget-ledger.json").write_bytes(data)
            with patch.object(deploy, "CODE_ROOT", root), patch.object(vast.subprocess, "run", return_value=SimpleNamespace(stdout=data)):
                vast.require_reservation(package, output, "image", settings, "pilot")
                with self.assertRaises(ValueError):
                    vast.require_reservation(package, output, "wrong-image", settings, "pilot")
                with self.assertRaises(ValueError):
                    vast.require_reservation(package, root / "second-rental", "image", settings, "pilot")
                (root / "budget-ledger.json").write_bytes(data + b"\n")
                with self.assertRaisesRegex(ValueError, "committed"):
                    vast.require_reservation(package, output, "image", settings, "pilot")

    def test_cleanup_verifies_disappearance_after_lost_destroy_reply(self):
        provider = Provider({"host": "root@target", "port": 22})
        provider.rows = [{"id": 456, "label": "owned"}, {"id": 999, "label": "other"}]
        provider.lost_destroy = True
        with tempfile.TemporaryDirectory() as directory, patch.object(vast.time, "sleep"):
            vast.destroy_owned(provider, "owned", Path(directory), 60)
            self.assertEqual(provider.destroys, 1)
            self.assertEqual(provider.rows, [{"id": 999, "label": "other"}])
            self.assertTrue(read_json(Path(directory) / "destroyed.json")["verified"])

    def test_instance_validation_rejects_wrong_image_and_transfer_overrun(self):
        settings, offer = quote()
        image = settings["image_repository"] + "@sha256:" + "4" * 64
        provider = Provider({"host": "root@target", "port": 22})
        with tempfile.TemporaryDirectory() as directory:
            provider.create(offer, image, "owned", None, settings, Path(directory))
            row = provider.rows[0]
            vast.validate_instance(row, offer, image, "owned", settings)
            with self.assertRaises(ValueError):
                vast.validate_instance({**row, "image_uuid": image[:-1] + "5"}, offer, image, "owned", settings)
            with self.assertRaises(ValueError):
                vast.validate_instance({**row, "inet_down_billed": 201}, offer, image, "owned", settings)


@unittest.skipUnless(os.environ.get("DISTILLATION_SSH_TARGET"), "requires the local deployment VM")
class RentalSSHTests(unittest.TestCase):
    def test_create_run_retrieve_destroy_and_resume_with_ambiguous_responses(self):
        target = read_json(os.environ["DISTILLATION_SSH_TARGET"])
        fixture = Path(os.environ["DISTILLATION_TEST_OUTPUT"])
        root = Path(os.environ["DISTILLATION_DEPLOY_OUTPUT"]) / "lifecycle"
        root.mkdir(parents=True)
        settings, offer = quote()
        image = settings["image_repository"] + "@sha256:" + "4" * 64
        for failure in (False, True):
            with self.subTest(failure=failure):
                config = read_json(fixture / "config.json")
                if failure:
                    config["max_length"] = 8
                path = root / f"candidate-{str(failure).lower()}.json"
                write_json(path, config)
                package = root / f"package-{failure}"
                deploy.prepare([path], package, 60, through="preflight")
                output = root / f"rental-{failure}"
                provider = Provider(target)
                provider.ambiguous = provider.lost_destroy = True
                state = vast.run_rental(package, output, settings, image, offer,
                    Path(target["identity"]), provider)
                self.assertEqual(state["state"], "failed" if failure else "complete")
                self.assertEqual(provider.creates, 1)
                self.assertEqual(provider.destroys, 1)
                self.assertTrue((output / "deployment/result/manifest.json").exists())
                vast.run_rental(package, output, settings, image, offer, Path(target["identity"]), provider)
                self.assertEqual(provider.creates, 1)


if __name__ == "__main__":
    unittest.main()
