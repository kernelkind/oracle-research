#!/usr/bin/env python3
"""Observe Codex account usage around individually audited generation jobs."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, Sequence


WEEKLY_WINDOW_MINUTES = 7 * 24 * 60
TRACKER_SCHEMA_VERSION = 1
RUNNER = Path(__file__).with_name("codex_exec.py")


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _isolated_environment(codex_home: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("CODEX_", "OPENAI_", "CHATGPT_"))
    }
    environment["CODEX_HOME"] = str(codex_home)
    return environment


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class RateLimitSnapshot:
    limit_id: str
    used_percent: int
    window_duration_minutes: int
    resets_at: int
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_rate_limit(cls, raw: object) -> "RateLimitSnapshot":
        value = _object(raw, "rate limit")
        limit_id = _string(value.get("limitId"), "rate limit.limitId")
        if limit_id != "codex":
            raise ValueError(f"expected the default `codex` limit, received `{limit_id}`")
        primary = _object(value.get("primary"), "rate limit.primary")
        used_percent = _integer(
            primary.get("usedPercent"), "rate limit.primary.usedPercent"
        )
        if used_percent > 100:
            raise ValueError("rate limit.primary.usedPercent must not exceed 100")
        window = _integer(
            primary.get("windowDurationMins"),
            "rate limit.primary.windowDurationMins",
            minimum=1,
        )
        if window != WEEKLY_WINDOW_MINUTES:
            raise ValueError(
                "default Codex rate limit is not the expected 10,080-minute weekly window"
            )
        return cls(
            limit_id=limit_id,
            used_percent=used_percent,
            window_duration_minutes=window,
            resets_at=_integer(
                primary.get("resetsAt"), "rate limit.primary.resetsAt", minimum=1
            ),
            raw=value,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "limit_id": self.limit_id,
            "used_percent": self.used_percent,
            "window_duration_minutes": self.window_duration_minutes,
            "resets_at": self.resets_at,
            "raw": self.raw,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "RateLimitSnapshot":
        value = _object(raw, "rate-limit snapshot")
        return cls(
            limit_id=_string(value.get("limit_id"), "snapshot.limit_id"),
            used_percent=_integer(
                value.get("used_percent"), "snapshot.used_percent"
            ),
            window_duration_minutes=_integer(
                value.get("window_duration_minutes"),
                "snapshot.window_duration_minutes",
                minimum=1,
            ),
            resets_at=_integer(value.get("resets_at"), "snapshot.resets_at", minimum=1),
            raw=_object(value.get("raw"), "snapshot.raw"),
        )


class CodexAppServer:
    """Minimal JSONL client for the official Codex app-server rate-limit API."""

    def __init__(
        self,
        *,
        codex_binary: Path,
        codex_home: Path,
        stderr_path: Path,
    ) -> None:
        self.codex_binary = codex_binary.resolve()
        self.codex_home = codex_home.resolve()
        self.stderr_path = stderr_path.resolve()
        self._process: subprocess.Popen[str] | None = None
        self._stderr: IO[str] | None = None
        self._next_request_id = 0

    def __enter__(self) -> "CodexAppServer":
        self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self._stderr = self.stderr_path.open("a", encoding="utf-8")
        try:
            self._process = subprocess.Popen(
                [
                    str(self.codex_binary),
                    "app-server",
                    "-c",
                    'cli_auth_credentials_store="file"',
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._stderr,
                text=True,
                bufsize=1,
                env=_isolated_environment(self.codex_home),
            )
            self._request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "oracle_mvp_usage_calibrator",
                        "title": "Oracle MVP Usage Calibrator",
                        "version": "1.0",
                    }
                },
            )
            self._notify("initialized", {})
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        process = self._process
        self._process = None
        if process is not None:
            if process.stdin is not None:
                process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if process.stdout is not None:
                process.stdout.close()
        if self._stderr is not None:
            self._stderr.close()
            self._stderr = None

    def _send(self, value: object) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Codex app-server is not running")
        self._process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self._process.stdin.flush()

    def _notify(self, method: str, params: object) -> None:
        self._send({"method": method, "params": params})

    def _request(self, method: str, params: object | None = None) -> object:
        request_id = self._next_request_id
        self._next_request_id += 1
        request: dict[str, object] = {"method": method, "id": request_id}
        if params is not None:
            request["params"] = params
        self._send(request)
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Codex app-server is not running")
        for line in self._process.stdout:
            try:
                response = _object(json.loads(line), "app-server message")
            except json.JSONDecodeError as error:
                raise RuntimeError(f"Codex app-server emitted invalid JSON: {error}") from error
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(
                    f"Codex app-server request `{method}` failed: {response['error']}"
                )
            if "result" not in response:
                raise RuntimeError(
                    f"Codex app-server response to `{method}` has no result"
                )
            return response["result"]
        return_code = self._process.poll()
        raise RuntimeError(
            f"Codex app-server closed before responding to `{method}`"
            + ("" if return_code is None else f" (exit status {return_code})")
        )

    def read_weekly_rate_limit(self) -> RateLimitSnapshot:
        result = _object(
            self._request("account/rateLimits/read"), "rate-limit response"
        )
        default_limit = result.get("rateLimits")
        if default_limit is None:
            by_id = _object(
                result.get("rateLimitsByLimitId"),
                "rate-limit response.rateLimitsByLimitId",
            )
            default_limit = by_id.get("codex")
        return RateLimitSnapshot.from_rate_limit(default_limit)


@dataclass(frozen=True)
class JobObservation:
    job_key: str
    stage: str
    note_id: str
    takeaway_index: int | None
    usage: dict[str, int]
    rate_limit: RateLimitSnapshot
    observed_at_utc: str
    completed_notes: int
    completed_takeaways: int

    def to_dict(self) -> dict[str, object]:
        return {
            "job_key": self.job_key,
            "stage": self.stage,
            "note_id": self.note_id,
            "takeaway_index": self.takeaway_index,
            "usage": self.usage,
            "rate_limit": self.rate_limit.to_dict(),
            "observed_at_utc": self.observed_at_utc,
            "completed_notes": self.completed_notes,
            "completed_takeaways": self.completed_takeaways,
        }

    @classmethod
    def from_dict(cls, raw: object) -> "JobObservation":
        value = _object(raw, "job observation")
        raw_index = value.get("takeaway_index")
        if raw_index is not None:
            raw_index = _integer(raw_index, "observation.takeaway_index")
        raw_usage = _object(value.get("usage"), "observation.usage")
        usage = {
            _string(key, "usage key"): _integer(item, f"usage.{key}")
            for key, item in raw_usage.items()
        }
        return cls(
            job_key=_string(value.get("job_key"), "observation.job_key"),
            stage=_string(value.get("stage"), "observation.stage"),
            note_id=_string(value.get("note_id"), "observation.note_id"),
            takeaway_index=raw_index,
            usage=usage,
            rate_limit=RateLimitSnapshot.from_dict(value.get("rate_limit")),
            observed_at_utc=_string(
                value.get("observed_at_utc"), "observation.observed_at_utc"
            ),
            completed_notes=_integer(
                value.get("completed_notes"), "observation.completed_notes"
            ),
            completed_takeaways=_integer(
                value.get("completed_takeaways"),
                "observation.completed_takeaways",
            ),
        )


@dataclass
class CalibrationTracker:
    baseline: RateLimitSnapshot
    started_at_utc: str
    observations: list[JobObservation] = field(default_factory=list)
    status: str = "waiting_for_first_boundary"
    start_boundary_index: int | None = None
    end_boundary_index: int | None = None
    ended_at_utc: str | None = None
    invalid_reason: str | None = None

    @classmethod
    def start(
        cls, baseline: RateLimitSnapshot, started_at_utc: str
    ) -> "CalibrationTracker":
        if baseline.used_percent >= 100:
            raise ValueError("weekly Codex usage is already at 100 percent")
        return cls(baseline=baseline, started_at_utc=_string(started_at_utc, "start"))

    @property
    def start_boundary_job_key(self) -> str | None:
        if self.start_boundary_index is None:
            return None
        return self.observations[self.start_boundary_index].job_key

    @property
    def end_boundary_job_key(self) -> str | None:
        if self.end_boundary_index is None:
            return None
        return self.observations[self.end_boundary_index].job_key

    def _measured_observations(self) -> list[JobObservation]:
        start = 0 if self.start_boundary_index is None else self.start_boundary_index + 1
        end = (
            len(self.observations)
            if self.end_boundary_index is None
            else self.end_boundary_index + 1
        )
        return self.observations[start:end]

    @property
    def measured_job_keys(self) -> list[str]:
        return [item.job_key for item in self._measured_observations()]

    @property
    def measured_usage(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for observation in self._measured_observations():
            for key, value in observation.usage.items():
                if key.endswith("_tokens"):
                    totals[key] = totals.get(key, 0) + value
        return dict(sorted(totals.items()))

    @property
    def measured_completions(self) -> dict[str, int]:
        if not self.observations:
            return {"notes": 0, "takeaways": 0}
        before = (
            None
            if self.start_boundary_index is None
            else self.observations[self.start_boundary_index]
        )
        after = self._measured_observations()
        if not after:
            return {"notes": 0, "takeaways": 0}
        last = after[-1]
        notes_before = 0 if before is None else before.completed_notes
        takeaways_before = 0 if before is None else before.completed_takeaways
        return {
            "notes": last.completed_notes - notes_before,
            "takeaways": last.completed_takeaways - takeaways_before,
        }

    def _invalidate(self, reason: str, observed_at_utc: str) -> None:
        self.status = "invalid"
        self.invalid_reason = reason
        self.ended_at_utc = observed_at_utc

    def observe(self, observation: JobObservation) -> None:
        if self.status not in {"waiting_for_first_boundary", "measuring"}:
            raise ValueError(f"cannot append an observation after status `{self.status}`")
        if any(item.job_key == observation.job_key for item in self.observations):
            raise ValueError(f"duplicate job_key `{observation.job_key}`")
        previous_completed_notes = (
            0 if not self.observations else self.observations[-1].completed_notes
        )
        previous_completed_takeaways = (
            0 if not self.observations else self.observations[-1].completed_takeaways
        )
        self.observations.append(observation)
        if (
            observation.completed_notes < previous_completed_notes
            or observation.completed_takeaways < previous_completed_takeaways
        ):
            self._invalidate(
                "generation completion counts decreased",
                observation.observed_at_utc,
            )
            return
        rate = observation.rate_limit
        if rate.limit_id != self.baseline.limit_id:
            self._invalidate("rate-limit identity changed", observation.observed_at_utc)
            return
        if rate.window_duration_minutes != self.baseline.window_duration_minutes:
            self._invalidate("rate-limit window duration changed", observation.observed_at_utc)
            return
        if rate.resets_at != self.baseline.resets_at:
            self._invalidate("rate-limit reset timestamp changed", observation.observed_at_utc)
            return
        previous_percent = (
            self.baseline.used_percent
            if len(self.observations) == 1
            else self.observations[-2].rate_limit.used_percent
        )
        if rate.used_percent < previous_percent:
            self._invalidate("used percentage decreased", observation.observed_at_utc)
            return
        if rate.used_percent == previous_percent:
            return
        if rate.used_percent != previous_percent + 1:
            self._invalidate(
                "one job crossed more than one displayed percentage boundary",
                observation.observed_at_utc,
            )
            return
        index = len(self.observations) - 1
        if self.start_boundary_index is None:
            self.start_boundary_index = index
            self.status = "measuring"
            return
        self.end_boundary_index = index
        self.status = "complete"
        self.ended_at_utc = observation.observed_at_utc

    def timeout(self, ended_at_utc: str) -> None:
        if self.status not in {"waiting_for_first_boundary", "measuring"}:
            raise ValueError(f"cannot time out calibration after status `{self.status}`")
        self.status = "timed_out"
        self.ended_at_utc = _string(ended_at_utc, "timeout")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": TRACKER_SCHEMA_VERSION,
            "status": self.status,
            "started_at_utc": self.started_at_utc,
            "ended_at_utc": self.ended_at_utc,
            "baseline": self.baseline.to_dict(),
            "observations": [item.to_dict() for item in self.observations],
            "start_boundary_job_key": self.start_boundary_job_key,
            "end_boundary_job_key": self.end_boundary_job_key,
            "measured_job_keys": self.measured_job_keys,
            "measured_usage": self.measured_usage,
            "measured_completions": self.measured_completions,
            "invalid_reason": self.invalid_reason,
        }
        if self.status == "complete":
            result["one_percentage_point_approximation"] = {
                "job_keys": self.measured_job_keys,
                "usage": self.measured_usage,
                "completions": self.measured_completions,
                "qualification": (
                    "excludes the job that first crossed a displayed integer boundary "
                    "and includes the job that crossed the next boundary"
                ),
            }
        elif self.status == "timed_out" and self.start_boundary_index is not None:
            result["lower_bound"] = {
                "job_keys": self.measured_job_keys,
                "usage": self.measured_usage,
                "completions": self.measured_completions,
                "meaning": (
                    "the recorded usage did not cross the next displayed integer "
                    "boundary, so one percentage point requires more than this amount"
                ),
            }
        elif self.status == "timed_out":
            result["unchanged_display_observation"] = {
                "job_keys": self.measured_job_keys,
                "usage": self.measured_usage,
                "completions": self.measured_completions,
                "meaning": (
                    "all recorded jobs completed while the displayed used percentage "
                    "remained unchanged; no percentage boundary was observed"
                ),
            }
        return result

    @classmethod
    def from_dict(cls, raw: object) -> "CalibrationTracker":
        value = _object(raw, "calibration tracker")
        if value.get("schema_version") != TRACKER_SCHEMA_VERSION:
            raise ValueError("unsupported calibration tracker schema version")
        observations_raw = value.get("observations")
        if not isinstance(observations_raw, list):
            raise ValueError("calibration observations must be an array")
        observations = [JobObservation.from_dict(item) for item in observations_raw]
        start_key = value.get("start_boundary_job_key")
        end_key = value.get("end_boundary_job_key")

        def find_index(key: object, name: str) -> int | None:
            if key is None:
                return None
            expected = _string(key, name)
            matches = [
                index for index, item in enumerate(observations) if item.job_key == expected
            ]
            if len(matches) != 1:
                raise ValueError(f"{name} does not identify one observation")
            return matches[0]

        tracker = cls(
            baseline=RateLimitSnapshot.from_dict(value.get("baseline")),
            started_at_utc=_string(value.get("started_at_utc"), "started_at_utc"),
            observations=observations,
            status=_string(value.get("status"), "status"),
            start_boundary_index=find_index(
                start_key, "start_boundary_job_key"
            ),
            end_boundary_index=find_index(end_key, "end_boundary_job_key"),
            ended_at_utc=value.get("ended_at_utc"),
            invalid_reason=value.get("invalid_reason"),
        )
        if tracker.to_dict() != value:
            raise ValueError("calibration tracker contains inconsistent derived fields")
        return tracker


def _load_pipeline_runtime(config_path: Path) -> tuple[Path, Path, Path]:
    try:
        from codex_exec import RunnerConfig
    except ImportError:
        from sse_multivector.codex_exec import RunnerConfig

    config = RunnerConfig.load(config_path)
    return config.codex_binary, config.codex_home, config.run_directory


@dataclass(frozen=True)
class ResultLedgerState:
    exists: bool
    device: int | None
    inode: int | None
    byte_count: int


def _result_ledger_state(path: Path) -> ResultLedgerState:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return ResultLedgerState(False, None, None, 0)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("generation results ledger must be a regular file")
    return ResultLedgerState(
        True,
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
    )


def _read_single_appended_result(
    path: Path,
    before: ResultLedgerState,
) -> dict[str, Any]:
    after = _result_ledger_state(path)
    if not after.exists or after.byte_count <= before.byte_count:
        raise ValueError("bounded generation did not append one result record")
    if before.exists and (after.device, after.inode) != (before.device, before.inode):
        raise ValueError("bounded generation replaced its results ledger")
    with path.open("rb") as source:
        source.seek(before.byte_count)
        appended = source.read()
    if len(appended) != after.byte_count - before.byte_count:
        raise ValueError("generation results ledger changed while reading its append")
    if not appended.endswith(b"\n") or appended.count(b"\n") != 1:
        raise ValueError("bounded generation must append exactly one JSONL record")
    try:
        return _object(json.loads(appended), "appended generation result")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"appended generation result is invalid JSON: {error}") from error


def _require_empty_new_calibration(results_path: Path, output_path: Path) -> None:
    state = _result_ledger_state(results_path)
    if state.byte_count != 0 or output_path.exists():
        raise ValueError(
            "generation run already contains progress; use its existing calibration ledger"
        )


def _observation_from_record(
    record: dict[str, Any],
    rate_limit: RateLimitSnapshot,
    *,
    completed_notes: int,
    completed_takeaways: int,
) -> JobObservation:
    if record.get("status") != "succeeded":
        raise ValueError("the newly appended generation job did not succeed")
    raw_usage = _object(record.get("usage"), "generation result usage")
    usage = {
        _string(key, "usage key"): _integer(value, f"usage.{key}")
        for key, value in raw_usage.items()
    }
    raw_index = record.get("takeaway_index")
    if raw_index is not None:
        raw_index = _integer(raw_index, "takeaway_index")
    return JobObservation(
        job_key=_string(record.get("job_key"), "job_key"),
        stage=_string(record.get("stage"), "stage"),
        note_id=_string(record.get("note_id"), "note_id"),
        takeaway_index=raw_index,
        usage=usage,
        rate_limit=rate_limit,
        observed_at_utc=_utc_now(),
        completed_notes=completed_notes,
        completed_takeaways=completed_takeaways,
    )


def run_calibration(
    config_path: Path,
    ledger_path: Path,
    *,
    max_seconds: float,
) -> dict[str, object]:
    if max_seconds <= 0:
        raise ValueError("--max-seconds must be greater than zero")
    config_path = config_path.resolve()
    ledger_path = ledger_path.resolve()
    codex_binary, codex_home, run_directory = _load_pipeline_runtime(config_path)
    results_path = run_directory / "results.jsonl"
    if ledger_path.exists():
        tracker = CalibrationTracker.from_dict(
            json.loads(ledger_path.read_text(encoding="utf-8"))
        )
        if tracker.status in {"complete", "timed_out", "invalid"}:
            return {
                "calibration_status": tracker.status,
                "generation_complete": (run_directory / "output.json").is_file(),
            }
    else:
        tracker = None
        _require_empty_new_calibration(results_path, run_directory / "output.json")

    stderr_path = ledger_path.with_suffix(".app-server.stderr.log")
    generation_complete = False
    started = time.monotonic()
    with CodexAppServer(
        codex_binary=codex_binary,
        codex_home=codex_home,
        stderr_path=stderr_path,
    ) as app_server:
        current = app_server.read_weekly_rate_limit()
        if tracker is None:
            tracker = CalibrationTracker.start(current, _utc_now())
            _atomic_write_json(ledger_path, tracker.to_dict())
        else:
            expected = (
                tracker.baseline
                if not tracker.observations
                else tracker.observations[-1].rate_limit
            )
            if current != expected:
                tracker._invalidate(
                    "rate-limit state changed while calibration was not running",
                    _utc_now(),
                )
                _atomic_write_json(ledger_path, tracker.to_dict())
                return {
                    "calibration_status": tracker.status,
                    "generation_complete": (run_directory / "output.json").is_file(),
                }

        while tracker.status in {"waiting_for_first_boundary", "measuring"}:
            if time.monotonic() - started >= max_seconds:
                tracker.timeout(_utc_now())
                _atomic_write_json(ledger_path, tracker.to_dict())
                break
            before = _result_ledger_state(results_path)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "run",
                    str(config_path),
                    "--max-new-jobs",
                    "1",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "bounded generation failed; inspect its results ledger: "
                    + completed.stderr.strip()
                )
            try:
                runner_status = _object(json.loads(completed.stdout), "runner status")
            except json.JSONDecodeError as error:
                raise RuntimeError(f"bounded generation returned invalid JSON: {error}") from error
            new_jobs = _integer(runner_status.get("new_jobs"), "runner new_jobs")
            completed_notes = _integer(
                runner_status.get("completed_notes"), "runner completed_notes"
            )
            completed_takeaways = _integer(
                runner_status.get("completed_takeaways"),
                "runner completed_takeaways",
            )
            generation_complete = runner_status.get("complete") is True
            if new_jobs == 0:
                if not generation_complete:
                    raise RuntimeError("bounded generation neither ran a job nor completed")
                if _result_ledger_state(results_path) != before:
                    raise RuntimeError(
                        "bounded generation changed its results ledger without running a job"
                    )
                tracker.timeout(_utc_now())
                _atomic_write_json(ledger_path, tracker.to_dict())
                break
            if new_jobs != 1:
                raise RuntimeError(
                    "bounded generation did not run exactly one audited job"
                )
            appended = _read_single_appended_result(results_path, before)
            rate_limit = app_server.read_weekly_rate_limit()
            tracker.observe(
                _observation_from_record(
                    appended,
                    rate_limit,
                    completed_notes=completed_notes,
                    completed_takeaways=completed_takeaways,
                )
            )
            _atomic_write_json(ledger_path, tracker.to_dict())
            if generation_complete and tracker.status not in {"complete", "invalid"}:
                tracker.timeout(_utc_now())
                _atomic_write_json(ledger_path, tracker.to_dict())
                break

    return {
        "calibration_status": tracker.status,
        "generation_complete": generation_complete
        or (run_directory / "output.json").is_file(),
    }


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one isolated generation job per Codex weekly-usage observation"
    )
    parser.add_argument("config", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--max-seconds", type=float, default=3600.0)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed = _argument_parser().parse_args(arguments)
    try:
        result = run_calibration(
            parsed.config,
            parsed.ledger,
            max_seconds=parsed.max_seconds,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Codex usage calibration failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
