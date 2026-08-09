import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from sse_multivector.codex_usage_calibration import (
    CalibrationTracker,
    CodexAppServer,
    JobObservation,
    RateLimitSnapshot,
    _require_empty_new_calibration,
    _result_ledger_state,
    _read_single_appended_result,
)


FAKE_APP_SERVER = r"""#!/usr/bin/env python3
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    if request.get("method") == "initialize":
        print(json.dumps({"id": request["id"], "result": {"codexHome": "fixture"}}), flush=True)
    elif request.get("method") == "initialized":
        continue
    elif request.get("method") == "account/rateLimits/read":
        print(json.dumps({"method": "fixture/notification", "params": {}}), flush=True)
        print(json.dumps({
            "id": request["id"],
            "result": {
                "rateLimits": {
                    "limitId": "codex",
                    "primary": {
                        "usedPercent": 54,
                        "windowDurationMins": 10080,
                        "resetsAt": 2000000000
                    },
                    "secondary": None
                },
                "rateLimitsByLimitId": {
                    "codex_bengalfox": {
                        "limitId": "codex_bengalfox",
                        "primary": {
                            "usedPercent": 0,
                            "windowDurationMins": 10080,
                            "resetsAt": 2000000100
                        }
                    }
                }
            }
        }), flush=True)
"""

FAKE_COMBINED_CODEX = r"""#!/usr/bin/env python3
import json
import sys
from pathlib import Path

if "--version" in sys.argv:
    print("codex-cli fixture-1.0")
    raise SystemExit(0)

if len(sys.argv) > 1 and sys.argv[1] == "app-server":
    reads = 0
    percentages = [53, 54, 54, 55]
    for line in sys.stdin:
        request = json.loads(line)
        if request.get("method") == "initialize":
            print(json.dumps({"id": request["id"], "result": {"codexHome": "fixture"}}), flush=True)
        elif request.get("method") == "initialized":
            continue
        elif request.get("method") == "account/rateLimits/read":
            percent = percentages[min(reads, len(percentages) - 1)]
            reads += 1
            print(json.dumps({
                "id": request["id"],
                "result": {
                    "rateLimits": {
                        "limitId": "codex",
                        "primary": {
                            "usedPercent": percent,
                            "windowDurationMins": 10080,
                            "resetsAt": 2000000000
                        }
                    }
                }
            }), flush=True)
    raise SystemExit(0)

prompt = sys.stdin.read()
arguments = sys.argv[1:]
output_path = Path(arguments[arguments.index("--output-last-message") + 1])
if prompt.startswith("TAKEAWAY"):
    response = {"takeaways": ["Rust is discussed."]}
elif prompt.startswith("PROMINENCE"):
    response = {"prominence": 88}
else:
    response = {"fragments": ["Rust"]}
output_path.write_text(json.dumps(response), encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": "fixture-thread"}))
print(json.dumps({
    "type": "turn.completed",
    "usage": {
        "input_tokens": 100,
        "cached_input_tokens": 0,
        "output_tokens": 20,
        "reasoning_output_tokens": 5
    }
}))
"""


def snapshot(percent: int, *, resets_at: int = 2_000_000_000) -> RateLimitSnapshot:
    return RateLimitSnapshot(
        limit_id="codex",
        used_percent=percent,
        window_duration_minutes=10_080,
        resets_at=resets_at,
    )


def observation(job_key: str, tokens: int, percent: int) -> JobObservation:
    return JobObservation(
        job_key=job_key,
        stage="takeaway",
        note_id="note-1",
        takeaway_index=None,
        usage={
            "input_tokens": tokens,
            "cached_input_tokens": 0,
            "output_tokens": tokens // 2,
            "reasoning_output_tokens": tokens // 4,
        },
        rate_limit=snapshot(percent),
        observed_at_utc=f"2026-08-06T00:00:0{tokens}Z",
        completed_notes=0,
        completed_takeaways=0,
    )


class CodexAppServerTests(unittest.TestCase):
    def test_new_calibration_rejects_preexisting_generation_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "results.jsonl"
            output = root / "output.json"

            _require_empty_new_calibration(results, output)
            results.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already contains"):
                _require_empty_new_calibration(results, output)

    def test_reads_only_the_single_appended_result_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "results.jsonl"
            path.write_bytes(b"an intentionally unreadable old record\n")
            before = _result_ledger_state(path)
            expected = {"job_key": "mask:note-1:0", "status": "succeeded"}
            with path.open("ab") as destination:
                destination.write((json.dumps(expected) + "\n").encode("utf-8"))

            self.assertEqual(expected, _read_single_appended_result(path, before))

            before = _result_ledger_state(path)
            with path.open("ab") as destination:
                destination.write(b"{}\n{}\n")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                _read_single_appended_result(path, before)

    def test_reads_the_default_weekly_codex_limit_and_ignores_notifications(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "codex"
            binary.write_text(FAKE_APP_SERVER, encoding="utf-8")
            binary.chmod(0o755)
            codex_home = root / "codex-home"
            codex_home.mkdir()
            stderr_path = root / "app-server.stderr.log"

            with CodexAppServer(
                codex_binary=binary,
                codex_home=codex_home,
                stderr_path=stderr_path,
            ) as client:
                result = client.read_weekly_rate_limit()

            self.assertEqual(snapshot(54), result)
            self.assertEqual(54, result.raw["primary"]["usedPercent"])
            self.assertTrue(stderr_path.is_file())

    def test_cli_runs_one_new_job_per_poll_and_stops_at_the_second_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "codex"
            binary.write_text(FAKE_COMBINED_CODEX, encoding="utf-8")
            binary.chmod(0o755)
            codex_home = root / "codex-home"
            codex_home.mkdir(mode=0o700)
            (codex_home / "auth.json").write_text("fixture", encoding="utf-8")
            (codex_home / "auth.json").chmod(0o600)
            notes = root / "notes.json"
            notes.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "notes": [{"note_id": "note-1", "text": "Rust"}],
                    }
                ),
                encoding="utf-8",
            )
            takeaway_prompts = root / "takeaway-prompts.json"
            takeaway_prompts.write_text(json.dumps({"TP": "TAKEAWAY"}), encoding="utf-8")
            prominence_prompts = root / "prominence-prompts.json"
            prominence_prompts.write_text(
                json.dumps({"PP": "PROMINENCE"}), encoding="utf-8"
            )
            mask_prompts = root / "mask-prompts.json"
            mask_prompts.write_text(
                json.dumps(
                    {
                        "MP": (
                            "MASK\n<post>\n{POST}\n</post>\n"
                            "<takeaway>\n{TAKEAWAY}\n</takeaway>"
                        )
                    }
                ),
                encoding="utf-8",
            )
            run_directory = root / "generation"
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "codex_binary": str(binary),
                        "codex_home": str(codex_home),
                        "input_path": str(notes),
                        "run_directory": str(run_directory),
                        "takeaway": {
                            "prompt_registry_path": str(takeaway_prompts),
                            "prompt_version": "TP",
                            "model": "fixture/model",
                            "reasoning_effort": "max",
                        },
                        "prominence": {
                            "prompt_registry_path": str(prominence_prompts),
                            "prompt_version": "PP",
                            "model": "fixture/model",
                            "reasoning_effort": "max",
                        },
                        "mask": {
                            "prompt_registry_path": str(mask_prompts),
                            "prompt_version": "MP",
                            "model": "fixture/model",
                            "reasoning_effort": "max",
                        },
                    }
                ),
                encoding="utf-8",
            )
            ledger = root / "calibration.json"
            environment = os.environ.copy()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("codex_usage_calibration.py")),
                    str(config),
                    str(ledger),
                    "--max-seconds",
                    "30",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
                timeout=30,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            status = json.loads(completed.stdout)
            self.assertEqual("complete", status["calibration_status"])
            self.assertTrue(status["generation_complete"])
            state = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual("takeaway:note-1", state["start_boundary_job_key"])
            self.assertEqual("mask:note-1:0", state["end_boundary_job_key"])
            self.assertEqual(
                ["prominence:note-1:0", "mask:note-1:0"],
                state["measured_job_keys"],
            )
            self.assertEqual(200, state["measured_usage"]["input_tokens"])
            self.assertEqual(
                {"notes": 1, "takeaways": 1},
                state["measured_completions"],
            )
            self.assertTrue((run_directory / "output.json").is_file())


class CalibrationTrackerTests(unittest.TestCase):
    def test_measures_only_jobs_between_two_observed_integer_boundaries(self) -> None:
        tracker = CalibrationTracker.start(snapshot(53), "2026-08-06T00:00:00Z")

        tracker.observe(observation("job-1", 10, 53))
        tracker.observe(observation("job-2", 20, 54))
        self.assertEqual("measuring", tracker.status)
        self.assertEqual("job-2", tracker.start_boundary_job_key)

        tracker.observe(observation("job-3", 30, 54))
        tracker.observations[-1] = JobObservation(
            **{
                **tracker.observations[-1].__dict__,
                "completed_notes": 1,
                "completed_takeaways": 2,
            }
        )
        restored = CalibrationTracker.from_dict(tracker.to_dict())
        final = observation("job-4", 40, 55)
        restored.observe(
            JobObservation(
                **{
                    **final.__dict__,
                    "completed_notes": 2,
                    "completed_takeaways": 5,
                }
            )
        )

        self.assertEqual("complete", restored.status)
        self.assertEqual("job-4", restored.end_boundary_job_key)
        self.assertEqual(["job-3", "job-4"], restored.measured_job_keys)
        self.assertEqual(
            {
                "input_tokens": 70,
                "cached_input_tokens": 0,
                "output_tokens": 35,
                "reasoning_output_tokens": 17,
            },
            restored.measured_usage,
        )
        self.assertEqual({"notes": 2, "takeaways": 5}, restored.measured_completions)

    def test_rejects_duplicate_jobs_and_invalidates_a_changed_window(self) -> None:
        tracker = CalibrationTracker.start(snapshot(53), "2026-08-06T00:00:00Z")
        tracker.observe(observation("job-1", 10, 53))

        with self.assertRaisesRegex(ValueError, "duplicate job_key"):
            tracker.observe(observation("job-1", 10, 53))

        changed = JobObservation(
            **{
                **observation("job-2", 20, 54).__dict__,
                "rate_limit": snapshot(54, resets_at=2_000_000_001),
            }
        )
        tracker.observe(changed)
        self.assertEqual("invalid", tracker.status)
        self.assertIn("reset timestamp changed", tracker.invalid_reason)

    def test_invalidates_decreasing_completion_counts(self) -> None:
        tracker = CalibrationTracker.start(snapshot(53), "2026-08-06T00:00:00Z")
        first = observation("job-1", 10, 53)
        tracker.observe(
            JobObservation(
                **{
                    **first.__dict__,
                    "completed_notes": 2,
                    "completed_takeaways": 5,
                }
            )
        )
        second = observation("job-2", 20, 53)
        tracker.observe(
            JobObservation(
                **{
                    **second.__dict__,
                    "completed_notes": 1,
                    "completed_takeaways": 5,
                }
            )
        )

        self.assertEqual("invalid", tracker.status)
        self.assertIn("completion counts decreased", tracker.invalid_reason)

    def test_timeout_records_only_the_supported_lower_bound(self) -> None:
        tracker = CalibrationTracker.start(snapshot(53), "2026-08-06T00:00:00Z")
        tracker.observe(observation("job-1", 100, 53))
        tracker.observe(observation("job-2", 200, 54))
        tracker.observe(observation("job-3", 300, 54))

        tracker.timeout("2026-08-06T01:00:00Z")

        self.assertEqual("timed_out", tracker.status)
        self.assertEqual(["job-3"], tracker.measured_job_keys)
        self.assertEqual(300, tracker.measured_usage["input_tokens"])
        encoded = json.dumps(tracker.to_dict(), sort_keys=True)
        self.assertIn("lower_bound", encoded)
        self.assertNotIn("estimate", encoded)


if __name__ == "__main__":
    unittest.main()
