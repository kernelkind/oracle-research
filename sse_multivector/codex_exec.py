#!/usr/bin/env python3
"""Run isolated, auditable takeaway and mask generation through codex exec."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


SCHEMA_VERSION = 1
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODEX_HOME = Path("~/.local/state/oracle-mvp/codex-home").expanduser()
TAKEAWAY_ENVELOPE_VERSION = "xml-post-v1"
DISABLED_FEATURES = (
    "shell_tool",
    "unified_exec",
    "multi_agent",
    "apps",
    "plugins",
    "browser_use",
    "computer_use",
    "image_generation",
)
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")

TAKEAWAY_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "takeaways": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        }
    },
    "required": ["takeaways"],
    "additionalProperties": False,
}
MASK_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "fragments": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
        }
    },
    "required": ["fragments"],
    "additionalProperties": False,
}


class RunnerError(Exception):
    """A user-actionable wrapper failure."""


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _expect_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunnerError(f"`{name}` must be an object")
    return value


def _expect_fields(
    value: dict[str, Any],
    name: str,
    expected: set[str],
) -> None:
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing:
        raise RunnerError(f"`{name}.{missing[0]}` is required")
    if unexpected:
        raise RunnerError(f"`{name}.{unexpected[0]}` is not supported")


def _expect_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise RunnerError(f"`{name}` must be a nonempty string")
    if "\x00" in value:
        raise RunnerError(f"`{name}` must not contain a NUL byte")
    return value


def _expect_identifier(value: object, name: str) -> str:
    identifier = _expect_string(value, name)
    if not IDENTIFIER.fullmatch(identifier):
        raise RunnerError(f"`{name}` contains unsupported characters")
    return identifier


def _resolve_path(value: object, name: str, base: Path) -> Path:
    raw = Path(_expect_string(value, name)).expanduser()
    if not raw.is_absolute():
        raw = base / raw
    return raw.resolve()


def _load_json(path: Path, name: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RunnerError(f"`{name}` does not exist: {path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RunnerError(f"could not read `{name}` at {path}: {error}") from error


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _append_json_line(path: Path, value: object) -> None:
    payload = _canonical_json_bytes(value)
    with path.open("ab") as destination:
        destination.write(payload)
        destination.flush()
        os.fsync(destination.fileno())


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_codex_home(path: Path) -> None:
    normal_home = (Path.home() / ".codex").resolve()
    if path == normal_home:
        raise RunnerError(
            "a dedicated CODEX_HOME is required; the normal ~/.codex home "
            "is forbidden"
        )
    if _is_within(path, REPOSITORY_ROOT):
        raise RunnerError(
            "the dedicated CODEX_HOME must be outside the repository so its "
            "credentials cannot enter version control"
        )
    if _is_within(Path.home().resolve(), path) or _is_within(REPOSITORY_ROOT, path):
        raise RunnerError(
            "the dedicated CODEX_HOME must not contain the user's home or "
            "the repository"
        )


def _prepare_codex_home(path: Path) -> None:
    _validate_codex_home(path)
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise RunnerError(f"dedicated CODEX_HOME is not a directory: {path}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if existed and mode != 0o700:
        raise RunnerError(
            f"existing dedicated CODEX_HOME must have mode 0700, not {mode:04o}"
        )
    if not existed:
        os.chmod(path, 0o700)
    workspaces = path / "job-workspaces"
    workspaces_existed = workspaces.exists()
    workspaces.mkdir(mode=0o700, exist_ok=True)
    workspace_mode = stat.S_IMODE(workspaces.stat().st_mode)
    if workspaces_existed and workspace_mode != 0o700:
        raise RunnerError(
            "existing CODEX_HOME job-workspaces must have mode 0700, not "
            f"{workspace_mode:04o}"
        )
    if not workspaces_existed:
        os.chmod(workspaces, 0o700)


def _validate_file_credentials(codex_home: Path) -> None:
    auth_path = codex_home / "auth.json"
    if not auth_path.is_file():
        raise RunnerError(f"dedicated CODEX_HOME auth.json is missing: {auth_path}")
    mode = stat.S_IMODE(auth_path.stat().st_mode)
    if mode != 0o600:
        raise RunnerError(
            "dedicated CODEX_HOME auth.json must have mode 0600, not "
            f"{mode:04o}"
        )


def _isolated_environment(codex_home: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("CODEX_", "OPENAI_", "CHATGPT_"))
    }
    environment["CODEX_HOME"] = str(codex_home)
    return environment


def _resolve_executable(value: object, name: str, base: Path) -> Path:
    raw = _expect_string(value, name)
    if os.sep in raw:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = base / path
        path = path.resolve()
    else:
        found = shutil.which(raw)
        if found is None:
            raise RunnerError(f"could not find `{name}` executable `{raw}`")
        path = Path(found).resolve()
    try:
        mode = path.stat().st_mode
    except OSError as error:
        raise RunnerError(f"could not inspect `{name}` executable {path}: {error}")
    if not stat.S_ISREG(mode) or not os.access(path, os.X_OK):
        raise RunnerError(f"`{name}` is not an executable regular file: {path}")
    return path


@dataclass(frozen=True)
class StageConfig:
    prompt_registry_path: Path
    prompt_version: str
    prompt: str
    prompt_registry_sha256: str
    prompt_sha256: str
    model: str
    reasoning_effort: str

    @classmethod
    def load(
        cls,
        raw: object,
        name: str,
        base: Path,
    ) -> "StageConfig":
        value = _expect_object(raw, name)
        _expect_fields(
            value,
            name,
            {
                "prompt_registry_path",
                "prompt_version",
                "model",
                "reasoning_effort",
            },
        )
        registry_path = _resolve_path(
            value["prompt_registry_path"],
            f"{name}.prompt_registry_path",
            base,
        )
        registry = _expect_object(
            _load_json(registry_path, f"{name}.prompt_registry_path"),
            f"{name} prompt registry",
        )
        version = _expect_string(value["prompt_version"], f"{name}.prompt_version")
        if version not in registry:
            raise RunnerError(
                f"`{name}.prompt_version` `{version}` is absent from {registry_path}"
            )
        prompt = _expect_string(registry[version], f"{name} prompt `{version}`")
        if name == "mask":
            for placeholder in ("{POST}", "{TAKEAWAY}"):
                if placeholder not in prompt:
                    raise RunnerError(
                        f"mask prompt `{version}` is missing placeholder `{placeholder}`"
                    )
        return cls(
            prompt_registry_path=registry_path,
            prompt_version=version,
            prompt=prompt,
            prompt_registry_sha256=_sha256_file(registry_path),
            prompt_sha256=_sha256_bytes(prompt.encode("utf-8")),
            model=_expect_identifier(value["model"], f"{name}.model"),
            reasoning_effort=_expect_identifier(
                value["reasoning_effort"], f"{name}.reasoning_effort"
            ),
        )


@dataclass(frozen=True)
class RunnerConfig:
    config_path: Path
    codex_binary: Path
    codex_home: Path
    input_path: Path
    run_directory: Path
    takeaway: StageConfig
    mask: StageConfig

    @classmethod
    def load(cls, path: Path) -> "RunnerConfig":
        config_path = path.expanduser().resolve()
        base = config_path.parent
        value = _expect_object(_load_json(config_path, "config"), "config")
        _expect_fields(
            value,
            "config",
            {
                "schema_version",
                "codex_binary",
                "codex_home",
                "input_path",
                "run_directory",
                "takeaway",
                "mask",
            },
        )
        if value["schema_version"] != SCHEMA_VERSION:
            raise RunnerError("unsupported config schema version")
        config = cls(
            config_path=config_path,
            codex_binary=_resolve_executable(
                value["codex_binary"], "codex_binary", base
            ),
            codex_home=_resolve_path(value["codex_home"], "codex_home", base),
            input_path=_resolve_path(value["input_path"], "input_path", base),
            run_directory=_resolve_path(value["run_directory"], "run_directory", base),
            takeaway=StageConfig.load(value["takeaway"], "takeaway", base),
            mask=StageConfig.load(value["mask"], "mask", base),
        )
        _validate_codex_home(config.codex_home)
        return config


@dataclass(frozen=True)
class Note:
    note_id: str
    text: str


def _load_notes(path: Path) -> tuple[Note, ...]:
    value = _expect_object(_load_json(path, "input_path"), "input")
    _expect_fields(value, "input", {"schema_version", "notes"})
    if value["schema_version"] != SCHEMA_VERSION:
        raise RunnerError("unsupported input schema version")
    raw_notes = value["notes"]
    if not isinstance(raw_notes, list) or not raw_notes:
        raise RunnerError("`input.notes` must be a nonempty array")
    notes: list[Note] = []
    seen: set[str] = set()
    for index, raw_note in enumerate(raw_notes):
        name = f"input.notes[{index}]"
        note = _expect_object(raw_note, name)
        _expect_fields(note, name, {"note_id", "text"})
        note_id = _expect_string(note["note_id"], f"{name}.note_id")
        text = _expect_string(note["text"], f"{name}.text")
        if note_id in seen:
            raise RunnerError(f"duplicate note_id `{note_id}`")
        seen.add(note_id)
        notes.append(Note(note_id=note_id, text=text))
    return tuple(notes)


def _codex_version(config: RunnerConfig) -> str:
    completed = subprocess.run(
        [str(config.codex_binary), "--version"],
        check=False,
        capture_output=True,
        text=True,
        env=_isolated_environment(config.codex_home),
    )
    if completed.returncode != 0:
        raise RunnerError(
            f"codex --version exited with status {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )
    version = completed.stdout.strip()
    if not version:
        raise RunnerError("codex --version returned no version")
    return version


def _stage_manifest(
    stage: StageConfig,
    response_schema: dict[str, object],
) -> dict[str, object]:
    schema_bytes = _canonical_json_bytes(response_schema)
    return {
        "prompt_registry_path": str(stage.prompt_registry_path),
        "prompt_registry_sha256": stage.prompt_registry_sha256,
        "prompt_version": stage.prompt_version,
        "prompt": stage.prompt,
        "prompt_sha256": stage.prompt_sha256,
        "model": stage.model,
        "reasoning_effort": stage.reasoning_effort,
        "response_schema": response_schema,
        "response_schema_sha256": _sha256_bytes(schema_bytes),
    }


def _build_manifest(
    config: RunnerConfig,
    codex_version: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "wrapper_sha256": _sha256_file(Path(__file__).resolve()),
        "codex_binary": str(config.codex_binary),
        "codex_version": codex_version,
        "codex_home": str(config.codex_home),
        "input_path": str(config.input_path),
        "input_sha256": _sha256_file(config.input_path),
        "takeaway_envelope_version": TAKEAWAY_ENVELOPE_VERSION,
        "takeaway": _stage_manifest(config.takeaway, TAKEAWAY_SCHEMA),
        "mask": _stage_manifest(config.mask, MASK_SCHEMA),
        "isolation": {
            "fresh_process_per_job": True,
            "ephemeral": True,
            "sterile_working_directory_per_job": True,
            "ignore_user_config": True,
            "ignore_rules": True,
            "approval_policy": "never",
            "sandbox": "read-only",
            "web_search": "disabled",
            "shell_environment_inherit": "none",
            "disabled_features": list(DISABLED_FEATURES),
        },
    }


def _prepare_run_directory(
    config: RunnerConfig,
    manifest: dict[str, object],
) -> str:
    run_directory = config.run_directory
    manifest_path = run_directory / "manifest.json"
    if run_directory.exists() and not run_directory.is_dir():
        raise RunnerError(f"run_directory is not a directory: {run_directory}")
    if run_directory.exists() and not manifest_path.exists():
        try:
            next(run_directory.iterdir())
        except StopIteration:
            pass
        else:
            raise RunnerError(
                "run_directory is nonempty but has no manifest; refusing to "
                "adopt unknown artifacts"
            )
    run_directory.mkdir(parents=True, exist_ok=True)
    manifest_bytes = _canonical_json_bytes(manifest)
    if manifest_path.exists():
        existing = _load_json(manifest_path, "run manifest")
        if existing != manifest:
            raise RunnerError(
                "run manifest does not match this configuration; use a new "
                "run_directory for different inputs, prompts, models, or effort"
            )
    else:
        _atomic_write(manifest_path, manifest_bytes)
    _atomic_write(
        run_directory / "takeaway-output-schema.json",
        _canonical_json_bytes(TAKEAWAY_SCHEMA),
    )
    _atomic_write(
        run_directory / "mask-output-schema.json",
        _canonical_json_bytes(MASK_SCHEMA),
    )
    return _sha256_bytes(manifest_bytes)


def _load_latest_results(path: Path, manifest_sha256: str) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise RunnerError(f"could not read results ledger {path}: {error}") from error
    for line_number, line in enumerate(lines, start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as error:
            raise RunnerError(
                f"results ledger line {line_number} is not valid JSON: {error}"
            ) from error
        record = _expect_object(raw, f"results ledger line {line_number}")
        if record.get("manifest_sha256") != manifest_sha256:
            raise RunnerError(
                f"results ledger line {line_number} belongs to another manifest"
            )
        job_key = _expect_string(
            record.get("job_key"), f"results ledger line {line_number}.job_key"
        )
        if record.get("status") not in {"succeeded", "failed"}:
            raise RunnerError(f"results ledger line {line_number} has invalid status")
        attempt = record.get("attempt")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise RunnerError(f"results ledger line {line_number} has invalid attempt")
        previous = latest.get(job_key)
        if previous is not None and attempt != previous["attempt"] + 1:
            raise RunnerError(
                f"results ledger has a nonconsecutive attempt for `{job_key}`"
            )
        latest[job_key] = record
    return latest


def _parse_event_stream(stdout: str) -> tuple[str, object]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise RunnerError(
                f"codex JSONL line {line_number} is not valid JSON: {error}"
            ) from error
        if not isinstance(value, dict):
            raise RunnerError(f"codex JSONL line {line_number} is not an object")
        events.append(value)
    started = [event for event in events if event.get("type") == "thread.started"]
    if len(started) != 1 or not isinstance(started[0].get("thread_id"), str):
        raise RunnerError("codex event stream must contain one thread.started")
    if any(event.get("type") == "turn.failed" for event in events):
        raise RunnerError("codex event stream contains turn.failed")
    completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(completed) != 1:
        raise RunnerError("codex event stream must contain one turn.completed")
    return started[0]["thread_id"], completed[0].get("usage")


def _validate_string_array(
    value: object,
    name: str,
    *,
    allow_empty: bool,
) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        qualifier = "an array" if allow_empty else "a nonempty array"
        raise RunnerError(f"codex {name} response must be {qualifier} of strings")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise RunnerError(
                f"codex {name} response item {index} must be a nonempty string"
            )
        result.append(item)
    return result


def _validate_result_items(
    stage_name: str,
    value: object,
    note_text: str,
) -> list[str]:
    if stage_name == "takeaway":
        return _validate_string_array(value, "takeaway", allow_empty=True)
    fragments = _validate_string_array(value, "mask", allow_empty=False)
    cursor = 0
    for index, fragment in enumerate(fragments):
        position = note_text.find(fragment, cursor)
        if position < 0:
            raise RunnerError(
                f"mask fragment {index} `{fragment}` is not present in the "
                "source note after the preceding fragment"
            )
        cursor = position + len(fragment)
    return fragments


def _validate_response(
    stage_name: str,
    value: object,
    note_text: str,
) -> list[str]:
    response_object = _expect_object(value, f"codex {stage_name} response")
    field = "takeaways" if stage_name == "takeaway" else "fragments"
    _expect_fields(response_object, f"codex {stage_name} response", {field})
    return _validate_result_items(stage_name, response_object[field], note_text)


def _job_key(
    stage_name: str,
    note_id: str,
    takeaway_index: int | None,
) -> str:
    if takeaway_index is None:
        return f"takeaway:{note_id}"
    return f"mask:{note_id}:{takeaway_index}"


def _build_exec_argv(
    config: RunnerConfig,
    stage: StageConfig,
    workspace: Path,
    schema_path: Path,
    response_path: Path,
) -> list[str]:
    arguments = [
        str(config.codex_binary),
        "exec",
        "--strict-config",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--cd",
        str(workspace),
        "--sandbox",
        "read-only",
        "--model",
        stage.model,
        "-c",
        f'model_reasoning_effort="{stage.reasoning_effort}"',
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        "project_root_markers=[]",
        "-c",
        'shell_environment_policy.inherit="none"',
        "-c",
        'cli_auth_credentials_store="file"',
    ]
    for feature in DISABLED_FEATURES:
        arguments.extend(("--disable", feature))
    arguments.extend(
        (
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(response_path),
            "--json",
            "--color",
            "never",
            "-",
        )
    )
    return arguments


def _run_job(
    *,
    config: RunnerConfig,
    manifest_sha256: str,
    codex_version: str,
    stage_name: str,
    stage: StageConfig,
    note: Note,
    takeaway_index: int | None,
    prompt: str,
    schema_path: Path,
    schema: dict[str, object],
    results_path: Path,
    latest: dict[str, dict[str, Any]],
    retry_failed: bool,
) -> list[str]:
    job_key = _job_key(stage_name, note.note_id, takeaway_index)
    previous = latest.get(job_key)
    if previous is not None and previous["status"] == "succeeded":
        return _validate_result_items(
            stage_name,
            previous.get("response"),
            note.text,
        )
    if previous is not None and not retry_failed:
        raise RunnerError(
            f"job `{job_key}` previously failed; inspect results.jsonl and "
            "rerun with --retry-failed to create a new audited attempt"
        )
    attempt = 1 if previous is None else previous["attempt"] + 1
    workspace_root = config.codex_home / "job-workspaces"
    output_raw: str | None = None
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    thread_id: str | None = None
    usage: object = None
    response: list[str] | None = None
    error_message: str | None = None
    argv: list[str] = []
    started_at = time.monotonic()

    with tempfile.TemporaryDirectory(
        prefix=f"{stage_name}-", dir=workspace_root
    ) as temporary:
        workspace = Path(temporary).resolve()
        response_path = workspace / "response.json"
        argv = _build_exec_argv(config, stage, workspace, schema_path, response_path)
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                check=False,
                capture_output=True,
                text=True,
                cwd=workspace,
                env=_isolated_environment(config.codex_home),
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
            if response_path.exists():
                output_raw = response_path.read_text(encoding="utf-8")
            if completed.returncode != 0:
                raise RunnerError(
                    f"codex exec exited with status {completed.returncode}"
                )
            thread_id, usage = _parse_event_stream(stdout)
            if output_raw is None:
                raise RunnerError("codex exec did not write its final response")
            try:
                raw_response = json.loads(output_raw)
            except json.JSONDecodeError as error:
                raise RunnerError(
                    f"codex final response is not valid JSON: {error}"
                ) from error
            response = _validate_response(stage_name, raw_response, note.text)
        except (OSError, UnicodeError, RunnerError) as error:
            error_message = str(error)

    elapsed_seconds = time.monotonic() - started_at
    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "job_key": job_key,
        "stage": stage_name,
        "note_id": note.note_id,
        "takeaway_index": takeaway_index,
        "attempt": attempt,
        "status": "failed" if error_message is not None else "succeeded",
        "model": stage.model,
        "reasoning_effort": stage.reasoning_effort,
        "codex_version": codex_version,
        "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
        "response_schema_sha256": _sha256_bytes(_canonical_json_bytes(schema)),
        "argv": argv,
        "exit_code": exit_code,
        "elapsed_seconds": elapsed_seconds,
        "thread_id": thread_id,
        "usage": usage,
        "stdout_jsonl": stdout,
        "stdout_sha256": _sha256_bytes(stdout.encode("utf-8")),
        "stderr": stderr,
        "stderr_sha256": _sha256_bytes(stderr.encode("utf-8")),
        "final_output_raw": output_raw,
        "final_output_sha256": (
            None if output_raw is None else _sha256_bytes(output_raw.encode("utf-8"))
        ),
        "response": response,
        "error": error_message,
    }
    _append_json_line(results_path, record)
    latest[job_key] = record
    if error_message is not None:
        raise RunnerError(error_message)
    if response is None:
        raise AssertionError("successful job is missing a response")
    return response


def _render_takeaway_prompt(prompt: str, note: Note) -> str:
    return f"{prompt}\n\n<post>\n{note.text}\n</post>"


def _render_mask_prompt(prompt: str, note: Note, takeaway: str) -> str:
    replacements = {"{POST}": note.text, "{TAKEAWAY}": takeaway}
    return re.sub(
        r"\{POST\}|\{TAKEAWAY\}",
        lambda match: replacements[match.group(0)],
        prompt,
    )


def run(config_path: Path, *, retry_failed: bool) -> dict[str, object]:
    config = RunnerConfig.load(config_path)
    notes = _load_notes(config.input_path)
    _prepare_codex_home(config.codex_home)
    _validate_file_credentials(config.codex_home)
    codex_version = _codex_version(config)
    manifest = _build_manifest(config, codex_version)
    manifest_sha256 = _prepare_run_directory(config, manifest)
    results_path = config.run_directory / "results.jsonl"
    latest = _load_latest_results(results_path, manifest_sha256)
    (config.run_directory / "output.json").unlink(missing_ok=True)
    output_notes: list[dict[str, object]] = []

    for note in notes:
        takeaways = _run_job(
            config=config,
            manifest_sha256=manifest_sha256,
            codex_version=codex_version,
            stage_name="takeaway",
            stage=config.takeaway,
            note=note,
            takeaway_index=None,
            prompt=_render_takeaway_prompt(config.takeaway.prompt, note),
            schema_path=config.run_directory / "takeaway-output-schema.json",
            schema=TAKEAWAY_SCHEMA,
            results_path=results_path,
            latest=latest,
            retry_failed=retry_failed,
        )
        output_takeaways: list[dict[str, object]] = []
        for index, takeaway in enumerate(takeaways):
            fragments = _run_job(
                config=config,
                manifest_sha256=manifest_sha256,
                codex_version=codex_version,
                stage_name="mask",
                stage=config.mask,
                note=note,
                takeaway_index=index,
                prompt=_render_mask_prompt(config.mask.prompt, note, takeaway),
                schema_path=config.run_directory / "mask-output-schema.json",
                schema=MASK_SCHEMA,
                results_path=results_path,
                latest=latest,
                retry_failed=retry_failed,
            )
            output_takeaways.append({"text": takeaway, "fragments": fragments})
        output_notes.append({"note_id": note.note_id, "takeaways": output_takeaways})

    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "notes": output_notes,
    }
    _atomic_write(config.run_directory / "output.json", _canonical_json_bytes(output))
    return output


def login(codex_home: Path, codex_binary: str) -> int:
    resolved_home = codex_home.expanduser().resolve()
    binary = _resolve_executable(codex_binary, "codex_binary", Path.cwd())
    _prepare_codex_home(resolved_home)
    completed = subprocess.run(
        [
            str(binary),
            "login",
            "-c",
            'cli_auth_credentials_store="file"',
        ],
        check=False,
        env=_isolated_environment(resolved_home),
    )
    return completed.returncode


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run takeaway and exact-mask prompts through isolated codex exec jobs"
        )
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    run_parser = subcommands.add_parser("run", help="run or resume a batch")
    run_parser.add_argument("config", type=Path)
    run_parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="explicitly retry the latest failed attempt for each failed job",
    )
    login_parser = subcommands.add_parser(
        "login", help="authenticate the dedicated Codex home"
    )
    login_parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    login_parser.add_argument("--codex-binary", default="codex")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed = _argument_parser().parse_args(arguments)
    try:
        if parsed.command == "login":
            return login(parsed.codex_home, parsed.codex_binary)
        output = run(parsed.config, retry_failed=parsed.retry_failed)
        takeaway_count = sum(len(note["takeaways"]) for note in output["notes"])
        print(
            json.dumps(
                {
                    "notes": len(output["notes"]),
                    "takeaways": takeaway_count,
                },
                sort_keys=True,
            )
        )
        return 0
    except RunnerError as error:
        print(f"codex exec wrapper failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
