import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


DRIVER = Path(__file__).with_name("run_comparison.py")


class ComparisonDriverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self.output = self.root / "output"
        self.environment = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ['PATH']}",
            "FAKE_SYSTEMD_ROOT": str(self.root),
        }
        runner = self.bin / "systemd-run"
        runner.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "root = Path(os.environ['FAKE_SYSTEMD_ROOT'])\n"
            "args = sys.argv[1:]\n"
            "unit = args[args.index('--unit') + 1]\n"
            "(root / (unit + '.pid')).write_text(str(os.getpid()))\n"
            "with (root / 'calls.jsonl').open('a') as stream:\n"
            "    stream.write(json.dumps(args) + '\\n')\n"
            "command = args[args.index('--') + 1:]\n"
            "os.execvpe(command[0], command, os.environ)\n"
        )
        runner.chmod(0o755)
        controller = self.bin / "systemctl"
        controller.write_text(
            f"#!{sys.executable}\n"
            "import json, os, signal, sys\n"
            "from pathlib import Path\n"
            "root = Path(os.environ['FAKE_SYSTEMD_ROOT'])\n"
            "with (root / 'stops.jsonl').open('a') as stream:\n"
            "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "for unit in sys.argv[sys.argv.index('stop') + 1:]:\n"
            "    try:\n"
            "        os.kill(int((root / (unit + '.pid')).read_text()), signal.SIGTERM)\n"
            "    except (FileNotFoundError, ProcessLookupError):\n"
            "        pass\n"
        )
        controller.chmod(0o755)

    def config(self, commands):
        jobs = [
            {
                "id": f"job-{index}",
                "unit": f"comparison-test-{index}",
                "cwd": str(self.root),
                "command": [sys.executable, "-c", command],
            }
            for index, command in enumerate(commands)
        ]
        path = self.root / "jobs.json"
        path.write_text(json.dumps({"jobs": jobs}))
        return path

    def invoke(self, config):
        return subprocess.run(
            [sys.executable, str(DRIVER), str(config), "--output", str(self.output)],
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_limits_concurrent_execution_and_monitor_during_slow_job(self):
        config = self.config([
            "import time; print('slow started', flush=True); time.sleep(6.2); print('slow done')",
            "import sys; print('fast done'); print('fast error', file=sys.stderr)",
        ])
        completed = self.invoke(config)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        results = json.loads((self.output / "results.json").read_text())
        jobs = results["jobs"]
        self.assertEqual([job["status"] for job in jobs], ["succeeded", "succeeded"])
        self.assertLess(jobs[1]["finished_monotonic"], jobs[0]["finished_monotonic"])
        self.assertIn("slow done", (self.output / "job-0.stdout").read_text())
        self.assertEqual((self.output / "job-1.stderr").read_text(), "fast error\n")
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(calls), 2)
        for call in calls:
            for flag in ["--user", "--wait", "--pipe", "--quiet"]:
                self.assertIn(flag, call)
            for value in ["MemoryMax=2G", "MemorySwapMax=0", "RuntimeMaxSec=900"]:
                self.assertIn(value, call)
        self.assertEqual(len(set(results["owned_units"])), 2)
        samples = [json.loads(line) for line in (self.output / "resources.jsonl").read_text().splitlines()]
        self.assertEqual(sum(sample["reason"] == "before_launch" for sample in samples), 2)
        self.assertEqual(samples[-1]["reason"], "after_last_completion")
        self.assertTrue(any(
            sample["reason"] == "periodic"
            and jobs[0]["started_monotonic"] + 4 < sample["monotonic"] < jobs[0]["finished_monotonic"]
            for sample in samples
        ), samples)
        self.assertLess(results["max_sample_interval_seconds"], 6)
        self.assertTrue(all(sample["mem_available_bytes"] > 0 for sample in samples))

    def test_failure_is_terminal_without_retry(self):
        completed = self.invoke(self.config(["import sys; sys.exit(7)"]))
        self.assertNotEqual(completed.returncode, 0)
        results = json.loads((self.output / "results.json").read_text())
        self.assertEqual(results["jobs"][0]["exit_code"], 7)
        self.assertEqual(results["jobs"][0]["status"], "failed")
        self.assertEqual(len(self.log.read_text().splitlines()), 1)

    def test_invalid_job_rejected_before_launch(self):
        config = self.config(["pass"])
        value = json.loads(config.read_text())
        value["jobs"][0]["command"][0] = "python"
        config.write_text(json.dumps(value))
        completed = self.invoke(config)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("absolute", completed.stderr)
        self.assertFalse(self.log.exists())

    def test_duplicate_normalized_units_rejected(self):
        config = self.config(["pass", "pass"])
        value = json.loads(config.read_text())
        value["jobs"][1]["unit"] = value["jobs"][0]["unit"] + ".service"
        config.write_text(json.dumps(value))
        completed = self.invoke(config)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unique", completed.stderr)
        self.assertFalse(self.log.exists())

    def test_thirteen_jobs_rejected_before_launch(self):
        completed = self.invoke(self.config(["pass"] * 13))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("between 1 and 12", completed.stderr)
        self.assertFalse(self.log.exists())

    def module(self):
        spec = importlib.util.spec_from_file_location("run_comparison", DRIVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_resource_readings_fail_closed(self):
        config = self.config(["pass"])
        module = self.module()
        original_read = Path.read_text

        def read(path, *args, **kwargs):
            if str(path) == "/proc/pressure/memory":
                raise OSError("missing pressure reading")
            return original_read(path, *args, **kwargs)

        with patch.dict(os.environ, self.environment), patch.object(Path, "read_text", read):
            code = module.main([str(config), "--output", str(self.output)])
        self.assertNotEqual(code, 0)
        self.assertFalse(self.log.exists())
        results = json.loads((self.output / "results.json").read_text())
        self.assertEqual(results["jobs"][0]["status"], "not_launched")
        self.assertIn("missing pressure reading", results["stop_reason"])

    def test_admission_thresholds(self):
        module = self.module()
        sample = {
            "mem_available_bytes": 16 * module.GIB,
            "memory_some_avg10": 1,
            "io_some_avg10": 10,
        }
        self.assertTrue(module.admitted(sample))
        for field, value in [
            ("mem_available_bytes", 16 * module.GIB - 1),
            ("memory_some_avg10", 1.01),
            ("io_some_avg10", 10.01),
        ]:
            self.assertFalse(module.admitted({**sample, field: value}))
        self.assertFalse(module.admitted({"error": "missing reading"}))

    def test_emergency_during_job_stops_owned_unit(self):
        config = self.config(["import time; time.sleep(30)"])
        module = self.module()
        original_read = Path.read_text

        def read(path, *args, **kwargs):
            value = original_read(path, *args, **kwargs)
            if str(path) == "/proc/meminfo" and self.log.exists():
                return "MemAvailable:       1024 kB\n"
            return value

        with patch.dict(os.environ, self.environment), patch.object(Path, "read_text", read):
            code = module.main([str(config), "--output", str(self.output)])
        self.assertNotEqual(code, 0)
        results = json.loads((self.output / "results.json").read_text())
        self.assertEqual(results["stop_reason"], "emergency: MemAvailable below 8 GiB")
        self.assertEqual(results["jobs"][0]["status"], "cancelled")
        stops = [json.loads(line) for line in (self.root / "stops.jsonl").read_text().splitlines()]
        self.assertEqual(stops, [["--user", "stop", *results["owned_units"]]])

    def test_sigterm_stops_only_owned_units(self):
        config = self.config(["import time; time.sleep(30)"])
        process = subprocess.Popen(
            [sys.executable, str(DRIVER), str(config), "--output", str(self.output)],
            env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        deadline = time.monotonic() + 5
        while not self.log.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(self.log.exists(), "job did not start")
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        self.assertNotEqual(process.returncode, 0, stdout + stderr)
        results = json.loads((self.output / "results.json").read_text())
        stops = [json.loads(line) for line in (self.root / "stops.jsonl").read_text().splitlines()]
        self.assertEqual(stops, [["--user", "stop", *results["owned_units"]]])
        self.assertEqual(results["jobs"][0]["status"], "cancelled")
        samples = [json.loads(line) for line in (self.output / "resources.jsonl").read_text().splitlines()]
        self.assertEqual(samples[-1]["reason"], "after_last_completion")


if __name__ == "__main__":
    unittest.main()
