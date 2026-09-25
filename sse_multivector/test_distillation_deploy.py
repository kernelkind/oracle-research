"""Exercise the production deployment package and SSH operator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sse_multivector import distillation_deploy as deploy
from sse_multivector.distillation_run import read_json, write_json, sha256
from sse_multivector.test_distillation_data import DistillationDataTests


class PackageTests(unittest.TestCase):
    def test_offer_checks_returned_storage_inclusive_price_and_total_budget(self):
        settings = read_json(Path(__file__).parent / "distillation/vast-launch.json")
        offer = {**settings["offer_equals"], **settings["offer_minimums"],
                 **settings["offer_maximums"], "id": 123, "driver_version": "595.58.03",
                 "dph_base": 1.5, "storage_cost": .24, "storage_total_cost": .1}
        self.assertEqual(deploy.check_offer(settings, offer)["maximum_charge_usd"], "24.60")
        for key, value in (("dph_total", 1.61), ("gpu_ram", 48000), ("inet_up_cost", float("nan")),
                           ("storage_total_cost", 0), ("driver_version", "570.00.00")):
            with self.subTest(field=key), self.assertRaises(ValueError):
                deploy.check_offer(settings, {**offer, key: value})

    def test_frozen_package_is_portable_and_rejects_changed_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            DistillationDataTests().prepare(root)
            model = root / "model"
            model.mkdir()
            (model / "weights").write_bytes(b"model payload")
            config = root / "candidate.json"
            write_json(config, {"data": str(root / "prepared"), "mask_prompt": str(root / "masks.txt"),
                                "model": str(model), "revision": None})
            package = root / "package"
            deploy.prepare([config], package, 600)
            job = deploy.verify_package(package)
            copied = read_json(package / job["runs"][0])
            for key in ("data", "mask_prompt", "model"):
                self.assertTrue(copied[key].startswith("package/"))
                self.assertNotIn(str(root), copied[key])
            self.assertEqual(job["timeout_seconds"], 600)
            self.assertFalse(any(p.suffix == ".py" for p in package.rglob("*")))
            mask = package.parent / copied["mask_prompt"]
            mask.write_text("changed")
            with self.assertRaisesRegex(ValueError, "manifest"):
                deploy.verify_package(package)


@unittest.skipUnless(os.environ.get("DISTILLATION_SSH_TARGET"), "requires the local deployment VM")
class SSHDeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["DISTILLATION_DEPLOY_OUTPUT"])
        cls.root.mkdir(parents=True)
        cls.target = read_json(os.environ["DISTILLATION_SSH_TARGET"])
        cls.fixture = Path(os.environ["DISTILLATION_TEST_OUTPUT"])

    def command(self, package, output, *extra):
        return [sys.executable, "-m", "sse_multivector.distillation_deploy", "run",
                "--package", str(package), "--output", str(output),
                "--host", self.target["host"], "--port", str(self.target["port"]),
                "--identity", self.target["identity"], *extra]

    def test_remote_job_survives_operator_exit_and_retrieves_verified_results(self):
        config = read_json(self.fixture / "config.json")
        configs = []
        for name in ("first", "second"):
            path = self.root / (name + ".json")
            write_json(path, config)
            configs.append(path)
        package, output = self.root / "package", self.root / "deployment"
        deploy.prepare(configs, package, 600)
        started = subprocess.run(self.command(package, output, "--start-only"),
                                 capture_output=True, text=True, timeout=60, check=True)
        self.assertIn('"state": "running"', started.stdout)
        # A new local process reconnects; it must attach to the same remote job.
        subprocess.run(self.command(package, output), check=True, timeout=600)
        result = read_json(output / "result" / "deployment.json")
        self.assertEqual(result["state"], "complete")
        self.assertEqual(result["starts"], 1)
        for name in ("first", "second"):
            report = read_json(output / "result" / name / "report.json")
            self.assertTrue(report["training"]["reload_matches"])
        before = sha256(output / "result" / "manifest.json")
        subprocess.run(self.command(package, output), check=True, timeout=30)
        self.assertEqual(sha256(output / "result" / "manifest.json"), before)

    def test_failed_training_returns_logs_without_retrying(self):
        config = read_json(self.fixture / "config.json")
        config["max_length"] = 8
        path = self.root / "failure.json"
        write_json(path, config)
        package, output = self.root / "bad-package", self.root / "failed-deployment"
        deploy.prepare([path], package, 60)
        failed = subprocess.run(self.command(package, output), capture_output=True, text=True, timeout=120)
        self.assertNotEqual(failed.returncode, 0)
        result = read_json(output / "result" / "deployment.json")
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["starts"], 1)
        self.assertIn("invalid sampling, learning rate or length", (output / "result" / "failure.log").read_text())
        subprocess.run(self.command(package, output), capture_output=True, timeout=30)
        self.assertEqual(read_json(output / "result" / "deployment.json"), result)

    def test_runtime_limit_stops_the_job_and_retrieves_failure(self):
        config = read_json(self.fixture / "config.json")
        config["max_steps"] = 1000000
        path = self.root / "limited.json"
        write_json(path, config)
        package, output = self.root / "limited-package", self.root / "limited-deployment"
        deploy.prepare([path], package, 1)
        failed = subprocess.run(self.command(package, output), capture_output=True, text=True, timeout=60)
        self.assertNotEqual(failed.returncode, 0)
        result = read_json(output / "result" / "deployment.json")
        self.assertEqual(result["state"], "failed")
        self.assertLess(result["finished"] - result["deadline"], 10)


if __name__ == "__main__":
    unittest.main()
