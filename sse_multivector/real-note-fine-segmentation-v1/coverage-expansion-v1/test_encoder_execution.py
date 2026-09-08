import json
import tempfile
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

from encoder_execution import _pressure, _sample, prepare, run


EXPERIMENT = Path(__file__).resolve().parents[1]
PREPARED = EXPERIMENT / "smoke-test/prepared"


def read(path):
    return json.loads(path.read_bytes())


class EncoderExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.plan = self.root / "plan"
        self.output = self.root / "encoder-run"

    def test_preparation_reuses_saved_config_and_changes_only_mounts_and_name(self):
        result = prepare(PREPARED, self.plan, self.output)
        baseline = read(EXPERIMENT / "encoder-run/execution-plan.json")
        actual = result["argv"]
        expected = baseline["argv"][:]
        expected[expected.index("--name") + 1] = result["container_name"]
        replacements = {
            str(EXPERIMENT / "encoder-input/worker-request.json"): str(
                PREPARED / "worker-request.json"
            ),
            str(EXPERIMENT / "encoder-run/worker-config.json"): str(
                self.plan / "worker-config.json"
            ),
            str(EXPERIMENT / "encoder-run"): str(self.output),
        }
        for index, argument in enumerate(expected):
            for source, destination in replacements.items():
                argument = argument.replace(source, destination)
            expected[index] = argument
        self.assertEqual(expected, actual)
        config = read(self.plan / "worker-config.json")
        reference = read(EXPERIMENT / "encoder-run/worker-config.json")
        config.pop("request_sha256")
        reference.pop("request_sha256")
        self.assertEqual(reference, config)
        self.assertEqual(
            {"cpus": 4, "memory_bytes": 8589934592, "swap_bytes": 0},
            result["resource_limits"],
        )
        self.assertFalse(self.output.exists())
        with self.assertRaisesRegex(ValueError, "already exists"):
            prepare(PREPARED, self.plan, self.output)

    def test_existing_run_or_changed_plan_refuses_before_starting_docker(self):
        prepare(PREPARED, self.plan, self.output)
        self.output.mkdir()
        with patch("encoder_execution.subprocess.Popen") as launch:
            with self.assertRaisesRegex(ValueError, "already exists"):
                run(self.plan)
            launch.assert_not_called()
        self.output.rmdir()
        (self.plan / "worker-config.json").write_text("{}\n")
        with patch("encoder_execution.subprocess.Popen") as launch:
            with self.assertRaisesRegex(ValueError, "changed|differs"):
                run(self.plan)
            launch.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_preparation_refuses_a_changed_saved_resource_limit(self):
        baseline_path = EXPERIMENT / "encoder-run/execution-plan.json"
        baseline = read(baseline_path)
        baseline["argv"][baseline["argv"].index("--memory") + 1] = "16g"
        with patch(
            "encoder_execution.read",
            side_effect=lambda path: baseline if path == baseline_path else read(path),
        ):
            with self.assertRaisesRegex(ValueError, "resource|frozen|limit"):
                prepare(PREPARED, self.plan, self.output)
        self.assertFalse(self.plan.exists())

    def test_actual_cgroup_file_parser_and_rolling_some_total_diagnostic(self):
        cgroup = self.root / "cgroup"
        cgroup.mkdir()
        (cgroup / "memory.current").write_text("12345\n")
        (cgroup / "memory.events").write_text(
            "low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n"
        )
        (cgroup / "io.pressure").write_text(
            "some avg10=0.00 avg60=0.00 avg300=0.00 total=500000\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=12\n"
        )
        sample = _sample(cgroup)
        self.assertEqual(12345, sample["memory_current"])
        self.assertEqual(500000, sample["io_some_total_microseconds"])
        window = deque()
        self.assertIsNone(_pressure(window, 0.0, 0))
        self.assertEqual(25.0, _pressure(window, 2.0, 500000))
        self.assertIsNone(_pressure(window, 2.25, 1))

    def test_one_planned_invocation_records_diagnostics_and_return_code(self):
        prepare(PREPARED, self.plan, self.output)

        class Completed:
            returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

        with patch(
            "encoder_execution.subprocess.Popen", return_value=Completed()
        ) as launch:
            result = run(self.plan)
        self.assertEqual(1, launch.call_count)
        self.assertEqual(
            read(self.plan / "execution-plan.json")["argv"], launch.call_args.args[0]
        )
        self.assertEqual(0, result["exit_code"])
        self.assertTrue(result["diagnostics_only"])
        self.assertFalse(result["additional_work_admitted_during_encoding"])
        self.assertTrue((self.output / "execution.json").is_file())
        self.assertTrue((self.output / "resources.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
