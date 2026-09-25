"""Exercise the production deployment package and SSH operator."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_multivector import distillation_deploy as deploy
from sse_multivector.distillation_run import read_json, write_json, sha256
from sse_multivector.test_distillation_data import DistillationDataTests


class PackageTests(unittest.TestCase):
    def test_connection_retry_is_bounded_and_does_not_retry_application_errors(self):
        with patch.object(deploy.time, "sleep"), patch.object(deploy.time, "time", return_value=0):
            with patch.object(deploy, "remote_json", side_effect=[ConnectionError("dropped"), {"state": "running"}]) as call:
                result = deploy.retry_connection(lambda: deploy.remote_json(None, None, None, None), 10)
                self.assertEqual(result["state"], "running")
                self.assertEqual(call.call_count, 2)
        with patch.object(deploy.time, "time", return_value=0), self.assertRaisesRegex(RuntimeError, "bad code"):
            deploy.retry_connection(lambda: (_ for _ in ()).throw(RuntimeError("bad code")), 10)
        with patch.object(deploy.time, "time", return_value=20), self.assertRaises(TimeoutError):
            deploy.retry_connection(lambda: None, 10)

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
            deploy.prepare([config], package, 600, through="preflight")
            job = deploy.verify_package(package)
            copied = read_json(package / job["runs"][0])
            for key in ("data", "mask_prompt", "model"):
                self.assertTrue(copied[key].startswith("package/"))
                self.assertNotIn(str(root), copied[key])
            self.assertEqual(job["timeout_seconds"], 600)
            self.assertEqual(job["through"], "preflight")
            self.assertFalse(any(p.suffix == ".py" for p in package.rglob("*")))
            output = root / "deployment"
            write_json(output / "deadline.json", {"deadline": 1})
            saved = {"state": "complete", "package_sha256": sha256(package / "manifest.json")}
            write_json(output / "result/deployment.json", saved)
            deploy.write_manifest(output / "result", output / "result/manifest.json", "distillation-results")
            self.assertEqual(deploy.operate(package, output, {"host": "unused"}), saved)
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

    def test_cuda_preflight_and_runtime_environment_through_image_entrypoint(self):
        config = read_json(self.fixture / "config.json")
        config["device"] = "cuda"
        path = self.root / "cuda.json"
        write_json(path, config)
        package, output = self.root / "cuda-package", self.root / "cuda-deployment"
        deploy.prepare([path], package, 60, through="preflight")
        subprocess.run(self.command(package, output), check=True, timeout=120)
        manifest = read_json(output / "result/cuda/manifest.json")
        self.assertEqual(manifest["packages"]["fla-core"], "0.5.2")
        self.assertTrue((output / "result/cuda/preflight.json").exists())
        command = deploy.ssh_command(self.target, output, "_status", "/unused")
        command[-1] = "cd /work && python -c 'import os,sys; assert sys.prefix == \"/opt/distillation-venv\"; assert \"/usr/local/nvidia/lib64\" in os.environ[\"LD_LIBRARY_PATH\"]; from sse_multivector.distillation_run import load_gpu_packages; load_gpu_packages({\"device\":\"cuda\"}); from fla.ops.gated_delta_rule import chunk_gated_delta_rule'"
        subprocess.run(command, check=True, timeout=60)

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
        write_json(output / "deadline.json", {"deadline": 1})
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

    def test_early_stop_retrieves_partial_results(self):
        config = read_json(self.fixture / "config.json")
        config["max_steps"] = 1000000
        path = self.root / "stopped.json"
        write_json(path, config)
        package, output = self.root / "stopped-package", self.root / "stopped-deployment"
        deploy.prepare([path], package, 600)
        subprocess.run(self.command(package, output, "--start-only"), check=True, timeout=60)
        result = subprocess.run(self.command(package, output, "--stop"), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 1)
        state = read_json(output / "result/deployment.json")
        self.assertEqual(state["state"], "failed")
        self.assertIn("stopped by controller", state["error"])


if __name__ == "__main__":
    unittest.main()
