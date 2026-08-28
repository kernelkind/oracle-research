#!/usr/bin/env python3
"""Run isolated, auditable model prompts through codex exec."""

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
PIPELINE_SCHEMA_VERSION = 2
REUSE_PIPELINE_SCHEMA_VERSION = 3
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODEX_HOME = Path("~/.local/state/oracle-mvp/codex-home").expanduser()
TAKEAWAY_ENVELOPE_VERSION = "xml-post-v1"
TAKEAWAY_INPUT_NORMALIZATION_VERSION = "remove-long-ascii-nip19-identifiers-v2"
MINIMAL_MODEL_INSTRUCTIONS = "Follow the user's instructions.\n"
RUNTIME_CONTEXT_OVERRIDES = (
    "agents.enabled=false",
    "include_permissions_instructions=false",
    "include_apps_instructions=false",
    "include_collaboration_mode_instructions=false",
    "include_environment_context=false",
    "skills.include_instructions=false",
)
URL_FREE_MASK_PROMPT_VERSIONS = frozenset({"MPv3.4"})
URL_SCHEME_PATTERN = re.compile(r"(?:https?|wss?)://", re.IGNORECASE)
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
NIP19_IDENTIFIER = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?ai:(?:nostr:)?(?:nprofile|nevent|nrelay|naddr|npub|nsec|note)1"
    r"[023456789acdefghjklmnpqrstuvwxyz]{20,})"
    r"(?:[?#][^\s<>\"']*)?(?=$|[^A-Za-z0-9_])"
)

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
PROMINENCE_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "prominence": {"type": "integer", "minimum": 0, "maximum": 100}
    },
    "required": ["prominence"],
    "additionalProperties": False,
}


class RunnerError(Exception):
    """A user-actionable wrapper failure."""


class NewJobLimitReached(Exception):
    """The caller-requested limit on newly spawned Codex jobs was reached."""


@dataclass
class RetryDirective:
    job_key: str
    reason: str
    matched: bool = False


@dataclass
class NewJobBudget:
    limit: int | None
    used: int = 0
    completed_notes: int = 0
    completed_takeaways: int = 0

    @property
    def exhausted(self) -> bool:
        return self.limit is not None and self.used >= self.limit

    def claim(self) -> None:
        if self.limit is not None and self.used >= self.limit:
            raise NewJobLimitReached
        self.used += 1


@dataclass(frozen=True)
class PipelineRunOutcome:
    complete: bool
    new_jobs: int
    completed_notes: int
    completed_takeaways: int
    output: dict[str, object] | None


@dataclass(frozen=True)
class RunnerProvenance:
    initial_wrapper_sha256: str
    active_wrapper_sha256: str
    boundaries: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class PreparedManifest:
    manifest_sha256: str
    provenance: RunnerProvenance
    pending_wrapper_sha256: str | None
    pending_reason: str | None


@dataclass(frozen=True)
class ReuseSourceConfig:
    input_path: Path
    input_sha256: str
    run_directory: Path
    manifest_sha256: str
    results_sha256: str
    runner_upgrades_sha256: str | None
    output_sha256: str

    @classmethod
    def load(cls, raw: object, base: Path) -> "ReuseSourceConfig":
        value = _expect_object(raw, "reuse_source")
        _expect_fields(
            value,
            "reuse_source",
            {
                "input_path",
                "input_sha256",
                "run_directory",
                "manifest_sha256",
                "results_sha256",
                "runner_upgrades_sha256",
                "output_sha256",
            },
        )
        upgrades = value["runner_upgrades_sha256"]
        if upgrades is not None:
            upgrades = _expect_sha256(
                upgrades, "reuse_source.runner_upgrades_sha256"
            )
        return cls(
            input_path=_resolve_path(
                value["input_path"], "reuse_source.input_path", base
            ),
            input_sha256=_expect_sha256(
                value["input_sha256"], "reuse_source.input_sha256"
            ),
            run_directory=_resolve_path(
                value["run_directory"], "reuse_source.run_directory", base
            ),
            manifest_sha256=_expect_sha256(
                value["manifest_sha256"], "reuse_source.manifest_sha256"
            ),
            results_sha256=_expect_sha256(
                value["results_sha256"], "reuse_source.results_sha256"
            ),
            runner_upgrades_sha256=upgrades,
            output_sha256=_expect_sha256(
                value["output_sha256"], "reuse_source.output_sha256"
            ),
        )

    def manifest_value(self) -> dict[str, object]:
        return {
            "input_path": str(self.input_path),
            "input_sha256": self.input_sha256,
            "run_directory": str(self.run_directory),
            "manifest_sha256": self.manifest_sha256,
            "results_sha256": self.results_sha256,
            "runner_upgrades_sha256": self.runner_upgrades_sha256,
            "output_sha256": self.output_sha256,
        }


@dataclass(frozen=True)
class SourceResultReference:
    line: int
    sha256: str
    attempt: int


@dataclass(frozen=True)
class SourceStageContract:
    prompt_version: str
    prompt: str
    prompt_sha256: str
    model: str
    reasoning_effort: str
    response_schema_sha256: str


@dataclass(frozen=True)
class ReusableJob:
    note_text: str
    rendered_prompt_sha256: str
    response: list[str] | int
    reference: SourceResultReference


@dataclass(frozen=True)
class LoadedReuseSource:
    config: ReuseSourceConfig
    stages: dict[str, SourceStageContract]
    jobs: dict[str, ReusableJob]


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


def _expect_sha256(value: object, name: str) -> str:
    digest = _expect_string(value, name)
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise RunnerError(f"`{name}` must be a lowercase SHA-256 digest")
    return digest


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
    schema_version: int
    config_path: Path
    codex_binary: Path
    codex_home: Path
    input_path: Path
    run_directory: Path
    takeaway: StageConfig
    prominence: StageConfig | None
    mask: StageConfig
    reuse_source: ReuseSourceConfig | None

    @classmethod
    def load(cls, path: Path) -> "RunnerConfig":
        config_path = path.expanduser().resolve()
        base = config_path.parent
        value = _expect_object(_load_json(config_path, "config"), "config")
        raw_schema_version = value.get("schema_version")
        if isinstance(raw_schema_version, bool) or not isinstance(
            raw_schema_version, int
        ):
            raise RunnerError("unsupported pipeline config schema version")
        if raw_schema_version == SCHEMA_VERSION:
            schema_version = SCHEMA_VERSION
            expected_fields = {
                "schema_version",
                "codex_binary",
                "codex_home",
                "input_path",
                "run_directory",
                "takeaway",
                "mask",
            }
        elif raw_schema_version == PIPELINE_SCHEMA_VERSION:
            schema_version = PIPELINE_SCHEMA_VERSION
            expected_fields = {
                "schema_version",
                "codex_binary",
                "codex_home",
                "input_path",
                "run_directory",
                "takeaway",
                "prominence",
                "mask",
            }
        elif raw_schema_version == REUSE_PIPELINE_SCHEMA_VERSION:
            schema_version = REUSE_PIPELINE_SCHEMA_VERSION
            expected_fields = {
                "schema_version",
                "codex_binary",
                "codex_home",
                "input_path",
                "run_directory",
                "takeaway",
                "prominence",
                "mask",
                "reuse_source",
            }
        else:
            raise RunnerError("unsupported pipeline config schema version")
        _expect_fields(value, "config", expected_fields)
        config = cls(
            schema_version=schema_version,
            config_path=config_path,
            codex_binary=_resolve_executable(
                value["codex_binary"], "codex_binary", base
            ),
            codex_home=_resolve_path(value["codex_home"], "codex_home", base),
            input_path=_resolve_path(value["input_path"], "input_path", base),
            run_directory=_resolve_path(value["run_directory"], "run_directory", base),
            takeaway=StageConfig.load(value["takeaway"], "takeaway", base),
            prominence=(
                None
                if schema_version == SCHEMA_VERSION
                else StageConfig.load(value["prominence"], "prominence", base)
            ),
            mask=StageConfig.load(value["mask"], "mask", base),
            reuse_source=(
                None
                if schema_version != REUSE_PIPELINE_SCHEMA_VERSION
                else ReuseSourceConfig.load(value["reuse_source"], base)
            ),
        )
        _validate_codex_home(config.codex_home)
        if (
            config.reuse_source is not None
            and config.run_directory == config.reuse_source.run_directory
        ):
            raise RunnerError(
                "reuse_source.run_directory must differ from run_directory"
            )
        return config


@dataclass(frozen=True)
class Note:
    note_id: str
    text: str


@dataclass(frozen=True)
class PromptJob:
    prompt_id: str
    text: str


@dataclass(frozen=True)
class PromptRunnerConfig:
    config_path: Path
    codex_binary: Path
    codex_home: Path
    run_directory: Path
    model: str
    reasoning_effort: str
    prompts: tuple[PromptJob, ...]

    @classmethod
    def load(cls, path: Path) -> "PromptRunnerConfig":
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
                "run_directory",
                "model",
                "reasoning_effort",
                "prompts",
            },
        )
        if value["schema_version"] != SCHEMA_VERSION:
            raise RunnerError("unsupported config schema version")
        raw_prompts = value["prompts"]
        if not isinstance(raw_prompts, list) or not raw_prompts:
            raise RunnerError("`config.prompts` must be a nonempty array")
        prompts: list[PromptJob] = []
        seen_ids: set[str] = set()
        for index, raw_prompt in enumerate(raw_prompts):
            name = f"config.prompts[{index}]"
            prompt = _expect_object(raw_prompt, name)
            _expect_fields(prompt, name, {"prompt_id", "text"})
            prompt_id = _expect_identifier(prompt["prompt_id"], f"{name}.prompt_id")
            if prompt_id in seen_ids:
                raise RunnerError(f"duplicate prompt_id `{prompt_id}`")
            seen_ids.add(prompt_id)
            prompts.append(
                PromptJob(
                    prompt_id=prompt_id,
                    text=_expect_string(prompt["text"], f"{name}.text"),
                )
            )
        config = cls(
            config_path=config_path,
            codex_binary=_resolve_executable(
                value["codex_binary"], "codex_binary", base
            ),
            codex_home=_resolve_path(value["codex_home"], "codex_home", base),
            run_directory=_resolve_path(
                value["run_directory"], "run_directory", base
            ),
            model=_expect_identifier(value["model"], "config.model"),
            reasoning_effort=_expect_identifier(
                value["reasoning_effort"], "config.reasoning_effort"
            ),
            prompts=tuple(prompts),
        )
        _validate_codex_home(config.codex_home)
        return config


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


def _codex_version(config: RunnerConfig | PromptRunnerConfig) -> str:
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


def _isolation_manifest() -> dict[str, object]:
    return {
        "fresh_process_per_job": True,
        "ephemeral": True,
        "sterile_working_directory_per_job": True,
        "ignore_user_config": True,
        "ignore_rules": True,
        "approval_policy": "never",
        "sandbox": "read-only",
        "web_search": "disabled",
        "shell_environment_inherit": "none",
        "model_instructions": MINIMAL_MODEL_INSTRUCTIONS,
        "model_instructions_sha256": _sha256_bytes(
            MINIMAL_MODEL_INSTRUCTIONS.encode("utf-8")
        ),
        "runtime_context_overrides": list(RUNTIME_CONTEXT_OVERRIDES),
        "disabled_features": list(DISABLED_FEATURES),
    }


def _build_manifest(
    config: RunnerConfig,
    codex_version: str,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "schema_version": config.schema_version,
        "wrapper_sha256": _sha256_file(Path(__file__).resolve()),
        "codex_binary": str(config.codex_binary),
        "codex_version": codex_version,
        "codex_home": str(config.codex_home),
        "input_path": str(config.input_path),
        "input_sha256": _sha256_file(config.input_path),
        "takeaway_envelope_version": TAKEAWAY_ENVELOPE_VERSION,
        "takeaway_input_normalization_version": (
            TAKEAWAY_INPUT_NORMALIZATION_VERSION
        ),
        "takeaway": _stage_manifest(config.takeaway, TAKEAWAY_SCHEMA),
        "mask": _stage_manifest(config.mask, MASK_SCHEMA),
        "isolation": _isolation_manifest(),
    }
    if config.prominence is not None:
        manifest["prominence"] = _stage_manifest(
            config.prominence,
            PROMINENCE_SCHEMA,
        )
        manifest["prominence_envelope_version"] = (
            "xml-complete-post-takeaway-v1"
        )
        manifest["prominence_input_normalization_version"] = (
            TAKEAWAY_INPUT_NORMALIZATION_VERSION
        )
    if config.reuse_source is not None:
        manifest["reuse_source"] = config.reuse_source.manifest_value()
    return manifest


def _build_prompt_manifest(
    config: PromptRunnerConfig,
    codex_version: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "prompt",
        "wrapper_sha256": _sha256_file(Path(__file__).resolve()),
        "config_path": str(config.config_path),
        "config_sha256": _sha256_file(config.config_path),
        "codex_binary": str(config.codex_binary),
        "codex_version": codex_version,
        "codex_home": str(config.codex_home),
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "prompts": [
            {"prompt_id": prompt.prompt_id, "text": prompt.text}
            for prompt in config.prompts
        ],
        "isolation": _isolation_manifest(),
    }


def _load_runner_upgrades(
    run_directory: Path,
    *,
    manifest_sha256: str,
    initial_wrapper_sha256: str,
) -> RunnerProvenance:
    path = run_directory / "runner-upgrades.jsonl"
    if not path.exists():
        return RunnerProvenance(initial_wrapper_sha256, initial_wrapper_sha256, ())
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise RunnerError(f"could not read runner upgrade ledger {path}: {error}") from error
    current_wrapper = initial_wrapper_sha256
    previous_first_result_line = 0
    result_path = run_directory / "results.jsonl"
    result_bytes = result_path.read_bytes() if result_path.exists() else b""
    result_line_count = len(result_bytes.splitlines())
    boundaries: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as error:
            raise RunnerError(
                f"runner upgrade ledger line {line_number} is not valid JSON: {error}"
            ) from error
        record = _expect_object(raw, f"runner upgrade ledger line {line_number}")
        _expect_fields(
            record,
            f"runner upgrade ledger line {line_number}",
            {
                "schema_version",
                "manifest_sha256",
                "from_wrapper_sha256",
                "to_wrapper_sha256",
                "first_result_line",
                "results_prefix_bytes",
                "results_prefix_sha256",
                "reason",
            },
        )
        if record["schema_version"] != 2:
            raise RunnerError(
                f"runner upgrade ledger line {line_number} has unsupported schema"
            )
        if record["manifest_sha256"] != manifest_sha256:
            raise RunnerError(
                f"runner upgrade ledger line {line_number} belongs to another manifest"
            )
        from_wrapper = _expect_sha256(
            record["from_wrapper_sha256"],
            f"runner upgrade ledger line {line_number}.from_wrapper_sha256",
        )
        to_wrapper = _expect_sha256(
            record["to_wrapper_sha256"],
            f"runner upgrade ledger line {line_number}.to_wrapper_sha256",
        )
        if from_wrapper != current_wrapper or to_wrapper == from_wrapper:
            raise RunnerError(
                f"runner upgrade ledger line {line_number} does not continue its chain"
            )
        first_result_line = record["first_result_line"]
        prefix_bytes = record["results_prefix_bytes"]
        if (
            isinstance(first_result_line, bool)
            or not isinstance(first_result_line, int)
            or first_result_line < 1
            or first_result_line < previous_first_result_line
            or first_result_line > result_line_count + 1
            or isinstance(prefix_bytes, bool)
            or not isinstance(prefix_bytes, int)
            or prefix_bytes < 0
            or prefix_bytes > len(result_bytes)
        ):
            raise RunnerError(
                f"runner upgrade ledger line {line_number} has invalid first_result_line"
            )
        prefix = result_bytes[:prefix_bytes]
        if (
            _expect_sha256(
                record["results_prefix_sha256"],
                f"runner upgrade ledger line {line_number}.results_prefix_sha256",
            )
            != _sha256_bytes(prefix)
            or len(prefix.splitlines()) != first_result_line - 1
            or (prefix and not prefix.endswith(b"\n"))
        ):
            raise RunnerError(
                f"runner upgrade ledger line {line_number} does not match its results prefix"
            )
        _expect_string(
            record["reason"], f"runner upgrade ledger line {line_number}.reason"
        )
        current_wrapper = to_wrapper
        previous_first_result_line = first_result_line
        boundaries.append((first_result_line, to_wrapper))
    return RunnerProvenance(
        initial_wrapper_sha256,
        current_wrapper,
        tuple(boundaries),
    )


def _prepare_manifest_directory(
    run_directory: Path,
    manifest: dict[str, object],
    *,
    runner_upgrade_reason: str | None = None,
) -> PreparedManifest:
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
        existing = _expect_object(
            _load_json(manifest_path, "run manifest"), "run manifest"
        )
        existing_bytes = _canonical_json_bytes(existing)
        manifest_sha256 = _sha256_bytes(existing_bytes)
        existing_without_wrapper = dict(existing)
        proposed_without_wrapper = dict(manifest)
        existing_wrapper = _expect_sha256(
            existing_without_wrapper.pop("wrapper_sha256", None),
            "run manifest.wrapper_sha256",
        )
        proposed_wrapper = _expect_sha256(
            proposed_without_wrapper.pop("wrapper_sha256", None),
            "proposed run manifest.wrapper_sha256",
        )
        if existing_without_wrapper != proposed_without_wrapper:
            raise RunnerError(
                "run manifest does not match this configuration; use a new "
                "run_directory for different inputs, prompts, models, or effort"
            )
        provenance = _load_runner_upgrades(
            run_directory,
            manifest_sha256=manifest_sha256,
            initial_wrapper_sha256=existing_wrapper,
        )
        pending_wrapper: str | None = None
        pending_reason: str | None = None
        if provenance.active_wrapper_sha256 != proposed_wrapper:
            if runner_upgrade_reason is None:
                raise RunnerError(
                    "run was created by another wrapper version; inspect the code "
                    "change and use --runner-upgrade-reason to append an audited "
                    "runner transition"
                )
            pending_wrapper = proposed_wrapper
            pending_reason = runner_upgrade_reason
        elif runner_upgrade_reason is not None:
            raise RunnerError(
                "--runner-upgrade-reason was provided, but this run already uses "
                "the current wrapper"
            )
        manifest_bytes = existing_bytes
    else:
        if runner_upgrade_reason is not None:
            raise RunnerError(
                "--runner-upgrade-reason requires an existing run from another wrapper"
            )
        _atomic_write(manifest_path, manifest_bytes)
        manifest_sha256 = _sha256_bytes(manifest_bytes)
        proposed_wrapper = _expect_sha256(
            manifest["wrapper_sha256"], "proposed run manifest.wrapper_sha256"
        )
        provenance = RunnerProvenance(proposed_wrapper, proposed_wrapper, ())
        pending_wrapper = None
        pending_reason = None
    _atomic_write(
        run_directory / "model-instructions.md",
        MINIMAL_MODEL_INSTRUCTIONS.encode("utf-8"),
    )
    return PreparedManifest(
        manifest_sha256,
        provenance,
        pending_wrapper,
        pending_reason,
    )


def _prepare_run_directory(
    config: RunnerConfig,
    manifest: dict[str, object],
    *,
    runner_upgrade_reason: str | None = None,
) -> PreparedManifest:
    prepared = _prepare_manifest_directory(
        config.run_directory,
        manifest,
        runner_upgrade_reason=runner_upgrade_reason,
    )
    _atomic_write(
        config.run_directory / "takeaway-output-schema.json",
        _canonical_json_bytes(TAKEAWAY_SCHEMA),
    )
    _atomic_write(
        config.run_directory / "mask-output-schema.json",
        _canonical_json_bytes(MASK_SCHEMA),
    )
    if config.prominence is not None:
        _atomic_write(
            config.run_directory / "prominence-output-schema.json",
            _canonical_json_bytes(PROMINENCE_SCHEMA),
        )
    return prepared


def _load_latest_results(
    path: Path,
    manifest_sha256: str,
    provenance: RunnerProvenance,
    references: dict[str, SourceResultReference] | None = None,
) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    try:
        lines = path.read_bytes().splitlines(keepends=True)
    except (OSError, UnicodeError) as error:
        raise RunnerError(f"could not read results ledger {path}: {error}") from error
    active_wrapper = provenance.initial_wrapper_sha256
    boundary_index = 0
    for line_number, line in enumerate(lines, start=1):
        while (
            boundary_index < len(provenance.boundaries)
            and provenance.boundaries[boundary_index][0] <= line_number
        ):
            active_wrapper = provenance.boundaries[boundary_index][1]
            boundary_index += 1
        try:
            raw = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RunnerError(
                f"results ledger line {line_number} is not valid JSON: {error}"
            ) from error
        record = _expect_object(raw, f"results ledger line {line_number}")
        if record.get("manifest_sha256") != manifest_sha256:
            raise RunnerError(
                f"results ledger line {line_number} belongs to another manifest"
            )
        recorded_wrapper = record.get("wrapper_sha256")
        if recorded_wrapper is None:
            if active_wrapper != provenance.initial_wrapper_sha256:
                raise RunnerError(
                    f"results ledger line {line_number} has invalid wrapper provenance"
                )
        elif _expect_sha256(
            recorded_wrapper, f"results ledger line {line_number}.wrapper_sha256"
        ) != active_wrapper:
            raise RunnerError(
                f"results ledger line {line_number} has invalid wrapper provenance"
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
        if references is not None:
            references[job_key] = SourceResultReference(
                line=line_number,
                sha256=_sha256_bytes(line),
                attempt=attempt,
            )
    return latest


def _verify_pinned_reuse_file(
    path: Path,
    expected_sha256: str,
    label: str,
) -> None:
    try:
        actual_sha256 = _sha256_file(path)
    except OSError as error:
        raise RunnerError(f"could not verify reuse source {label} at {path}: {error}")
    if actual_sha256 != expected_sha256:
        raise RunnerError(
            f"reuse source {label} hash does not match its pinned SHA-256"
        )


def _verify_reuse_source_hashes(config: ReuseSourceConfig) -> None:
    _verify_pinned_reuse_file(
        config.input_path,
        config.input_sha256,
        "input",
    )
    _verify_pinned_reuse_file(
        config.run_directory / "manifest.json",
        config.manifest_sha256,
        "manifest",
    )
    _verify_pinned_reuse_file(
        config.run_directory / "results.jsonl",
        config.results_sha256,
        "results",
    )
    upgrades_path = config.run_directory / "runner-upgrades.jsonl"
    if config.runner_upgrades_sha256 is None:
        if upgrades_path.exists():
            raise RunnerError(
                "reuse source runner upgrades exist but no SHA-256 was pinned"
            )
    else:
        _verify_pinned_reuse_file(
            upgrades_path,
            config.runner_upgrades_sha256,
            "runner upgrades",
        )
    _verify_pinned_reuse_file(
        config.run_directory / "output.json",
        config.output_sha256,
        "output",
    )


def _source_stage_contracts(
    manifest: dict[str, Any],
) -> dict[str, SourceStageContract]:
    stages: dict[str, SourceStageContract] = {}
    for stage_name in ("takeaway", "prominence", "mask"):
        stage = _expect_object(
            manifest.get(stage_name), f"reuse source manifest.{stage_name}"
        )
        prompt = _expect_string(
            stage.get("prompt"), f"reuse source manifest.{stage_name}.prompt"
        )
        prompt_sha256 = _expect_sha256(
            stage.get("prompt_sha256"),
            f"reuse source manifest.{stage_name}.prompt_sha256",
        )
        if prompt_sha256 != _sha256_bytes(prompt.encode("utf-8")):
            raise RunnerError(
                f"reuse source manifest.{stage_name} prompt hash is invalid"
            )
        response_schema = _expect_object(
            stage.get("response_schema"),
            f"reuse source manifest.{stage_name}.response_schema",
        )
        response_schema_sha256 = _expect_sha256(
            stage.get("response_schema_sha256"),
            f"reuse source manifest.{stage_name}.response_schema_sha256",
        )
        if response_schema_sha256 != _sha256_bytes(
            _canonical_json_bytes(response_schema)
        ):
            raise RunnerError(
                f"reuse source manifest.{stage_name} response schema hash is invalid"
            )
        stages[stage_name] = SourceStageContract(
            prompt_version=_expect_string(
                stage.get("prompt_version"),
                f"reuse source manifest.{stage_name}.prompt_version",
            ),
            prompt=prompt,
            prompt_sha256=prompt_sha256,
            model=_expect_identifier(
                stage.get("model"), f"reuse source manifest.{stage_name}.model"
            ),
            reasoning_effort=_expect_identifier(
                stage.get("reasoning_effort"),
                f"reuse source manifest.{stage_name}.reasoning_effort",
            ),
            response_schema_sha256=response_schema_sha256,
        )
    return stages


def _compile_reusable_job(
    *,
    latest: dict[str, dict[str, Any]],
    references: dict[str, SourceResultReference],
    source_codex_version: str,
    stage_name: str,
    stage: SourceStageContract,
    note: Note,
    takeaway_index: int | None,
    rendered_prompt: str,
    output_response: list[str] | int,
) -> ReusableJob:
    job_key = _job_key(stage_name, note.note_id, takeaway_index)
    record = latest.get(job_key)
    if record is None or record.get("status") != "succeeded":
        raise RunnerError(
            f"reuse source output has no successful result for `{job_key}`"
        )
    if (
        record.get("schema_version") != SCHEMA_VERSION
        or record.get("execution") is not None
        or record.get("job_key") != job_key
        or record.get("stage") != stage_name
        or record.get("note_id") != note.note_id
        or record.get("takeaway_index") != takeaway_index
    ):
        raise RunnerError(f"reuse source result `{job_key}` has invalid job identity")
    rendered_prompt_sha256 = _sha256_bytes(rendered_prompt.encode("utf-8"))
    if record.get("model") != stage.model:
        raise RunnerError(f"reuse source result `{job_key}` has an invalid model")
    if record.get("reasoning_effort") != stage.reasoning_effort:
        raise RunnerError(
            f"reuse source result `{job_key}` has invalid reasoning effort"
        )
    if record.get("response_schema_sha256") != stage.response_schema_sha256:
        raise RunnerError(
            f"reuse source result `{job_key}` has an invalid response schema"
        )
    if record.get("prompt_sha256") != rendered_prompt_sha256:
        raise RunnerError(
            f"reuse source result `{job_key}` has an invalid rendered prompt hash"
        )
    if record.get("codex_version") != source_codex_version:
        raise RunnerError(
            f"reuse source result `{job_key}` has an invalid Codex version"
        )
    if record.get("response") != output_response:
        raise RunnerError(
            f"reuse source result `{job_key}` does not match its output artifact"
        )
    reference = references.get(job_key)
    if reference is None:
        raise RunnerError(f"reuse source result `{job_key}` has no ledger reference")
    return ReusableJob(
        note_text=note.text,
        rendered_prompt_sha256=rendered_prompt_sha256,
        response=output_response,
        reference=reference,
    )


def _load_reuse_source(
    config: ReuseSourceConfig,
    target_notes: list[Note],
) -> LoadedReuseSource:
    _verify_reuse_source_hashes(config)
    source_notes = _load_notes(config.input_path)
    manifest = _expect_object(
        _load_json(config.run_directory / "manifest.json", "reuse source manifest"),
        "reuse source manifest",
    )
    if manifest.get("schema_version") != PIPELINE_SCHEMA_VERSION:
        raise RunnerError("reuse source manifest must use pipeline schema version 2")
    if manifest.get("isolation") != _isolation_manifest():
        raise RunnerError("reuse source isolation contract is incompatible")
    _expect_string(manifest.get("input_path"), "reuse source manifest.input_path")
    if manifest.get("input_sha256") != config.input_sha256:
        raise RunnerError(
            "reuse source manifest input hash does not match the pinned input"
        )
    initial_wrapper_sha256 = _expect_sha256(
        manifest.get("wrapper_sha256"), "reuse source manifest.wrapper_sha256"
    )
    if manifest.get("takeaway_envelope_version") != TAKEAWAY_ENVELOPE_VERSION:
        raise RunnerError("reuse source takeaway envelope is incompatible")
    if (
        manifest.get("takeaway_input_normalization_version")
        != TAKEAWAY_INPUT_NORMALIZATION_VERSION
    ):
        raise RunnerError("reuse source takeaway normalization is incompatible")
    if manifest.get("prominence_envelope_version") != "xml-complete-post-takeaway-v1":
        raise RunnerError("reuse source prominence envelope is incompatible")
    if (
        manifest.get("prominence_input_normalization_version")
        != TAKEAWAY_INPUT_NORMALIZATION_VERSION
    ):
        raise RunnerError("reuse source prominence normalization is incompatible")
    stages = _source_stage_contracts(manifest)
    source_codex_version = _expect_string(
        manifest.get("codex_version"), "reuse source manifest.codex_version"
    )

    provenance = _load_runner_upgrades(
        config.run_directory,
        manifest_sha256=config.manifest_sha256,
        initial_wrapper_sha256=initial_wrapper_sha256,
    )
    results_path = config.run_directory / "results.jsonl"
    references: dict[str, SourceResultReference] = {}
    latest = _load_latest_results(
        results_path,
        config.manifest_sha256,
        provenance,
        references,
    )

    output = _expect_object(
        _load_json(config.run_directory / "output.json", "reuse source output"),
        "reuse source output",
    )
    _expect_fields(
        output,
        "reuse source output",
        {"schema_version", "manifest_sha256", "notes"},
    )
    if output["schema_version"] != PIPELINE_SCHEMA_VERSION:
        raise RunnerError("reuse source output must use pipeline schema version 2")
    if output["manifest_sha256"] != config.manifest_sha256:
        raise RunnerError(
            "reuse source output does not belong to the pinned manifest"
        )
    raw_output_notes = output["notes"]
    if not isinstance(raw_output_notes, list):
        raise RunnerError("reuse source output.notes must be an array")
    if len(raw_output_notes) != len(source_notes):
        raise RunnerError(
            "reuse source output note order does not match its pinned input"
        )
    target_note_texts = {note.note_id: note.text for note in target_notes}
    jobs: dict[str, ReusableJob] = {}
    for index, (source_note, raw_note) in enumerate(
        zip(source_notes, raw_output_notes, strict=True)
    ):
        output_note = _expect_object(
            raw_note, f"reuse source output.notes[{index}]"
        )
        _expect_fields(
            output_note,
            f"reuse source output.notes[{index}]",
            {"note_id", "takeaways"},
        )
        note_id = _expect_string(
            output_note["note_id"], f"reuse source output.notes[{index}].note_id"
        )
        if note_id != source_note.note_id:
            raise RunnerError(
                "reuse source output note order does not match its pinned input"
            )
        raw_takeaways = output_note["takeaways"]
        if not isinstance(raw_takeaways, list):
            raise RunnerError(
                f"reuse source output.notes[{index}].takeaways must be an array"
            )
        if target_note_texts.get(note_id) != source_note.text:
            continue
        takeaway_texts: list[str] = []
        validated_takeaways: list[tuple[str, int, list[str]]] = []
        for takeaway_index, raw_takeaway in enumerate(raw_takeaways):
            name = (
                f"reuse source output note `{note_id}` takeaway {takeaway_index}"
            )
            takeaway = _expect_object(raw_takeaway, name)
            _expect_fields(
                takeaway, name, {"text", "prominence", "fragments"}
            )
            text = _expect_string(takeaway["text"], f"{name}.text")
            prominence = _validate_result_items(
                "prominence",
                takeaway["prominence"],
                source_note.text,
                stages["prominence"].prompt_version,
            )
            fragments = _validate_result_items(
                "mask",
                takeaway["fragments"],
                source_note.text,
                stages["mask"].prompt_version,
            )
            if not isinstance(prominence, int) or not isinstance(fragments, list):
                raise AssertionError("validated reuse source output has invalid types")
            takeaway_texts.append(text)
            validated_takeaways.append((text, prominence, fragments))
        takeaway_response = _validate_result_items(
            "takeaway",
            takeaway_texts,
            source_note.text,
            stages["takeaway"].prompt_version,
        )
        if not isinstance(takeaway_response, list):
            raise AssertionError("validated reuse source takeaways are not an array")
        takeaway_key = _job_key("takeaway", note_id, None)
        jobs[takeaway_key] = _compile_reusable_job(
            latest=latest,
            references=references,
            source_codex_version=source_codex_version,
            stage_name="takeaway",
            stage=stages["takeaway"],
            note=source_note,
            takeaway_index=None,
            rendered_prompt=_render_takeaway_prompt(
                stages["takeaway"].prompt, source_note
            ),
            output_response=takeaway_response,
        )
        for takeaway_index, (text, prominence, fragments) in enumerate(
            validated_takeaways
        ):
            for stage_name, response, rendered_prompt in (
                (
                    "prominence",
                    prominence,
                    _render_prominence_prompt(
                        stages["prominence"].prompt, source_note, text
                    ),
                ),
                (
                    "mask",
                    fragments,
                    _render_mask_prompt(stages["mask"].prompt, source_note, text),
                ),
            ):
                job_key = _job_key(stage_name, note_id, takeaway_index)
                jobs[job_key] = _compile_reusable_job(
                    latest=latest,
                    references=references,
                    source_codex_version=source_codex_version,
                    stage_name=stage_name,
                    stage=stages[stage_name],
                    note=source_note,
                    takeaway_index=takeaway_index,
                    rendered_prompt=rendered_prompt,
                    output_response=response,
                )

    return LoadedReuseSource(
        config=config,
        stages=stages,
        jobs=jobs,
    )


def _append_runner_upgrade(
    run_directory: Path,
    prepared: PreparedManifest,
) -> RunnerProvenance:
    if prepared.pending_wrapper_sha256 is None:
        return prepared.provenance
    if prepared.pending_reason is None:
        raise AssertionError("pending runner upgrade has no audit reason")
    results_path = run_directory / "results.jsonl"
    result_bytes = results_path.read_bytes() if results_path.exists() else b""
    first_result_line = len(result_bytes.splitlines()) + 1
    _append_json_line(
        run_directory / "runner-upgrades.jsonl",
        {
            "schema_version": 2,
            "manifest_sha256": prepared.manifest_sha256,
            "from_wrapper_sha256": prepared.provenance.active_wrapper_sha256,
            "to_wrapper_sha256": prepared.pending_wrapper_sha256,
            "first_result_line": first_result_line,
            "results_prefix_bytes": len(result_bytes),
            "results_prefix_sha256": _sha256_bytes(result_bytes),
            "reason": prepared.pending_reason,
        },
    )
    return RunnerProvenance(
        prepared.provenance.initial_wrapper_sha256,
        prepared.pending_wrapper_sha256,
        prepared.provenance.boundaries
        + ((first_result_line, prepared.pending_wrapper_sha256),),
    )


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
    prompt_version: str,
) -> list[str] | int:
    if stage_name == "takeaway":
        return _validate_string_array(value, "takeaway", allow_empty=True)
    if stage_name == "prominence":
        if isinstance(value, bool) or not isinstance(value, int):
            raise RunnerError("codex prominence response must be an integer")
        if not 0 <= value <= 100:
            raise RunnerError(
                "codex prominence response must be between 0 and 100"
            )
        return value
    fragments = _validate_string_array(value, "mask", allow_empty=False)
    if prompt_version in URL_FREE_MASK_PROMPT_VERSIONS:
        for index, fragment in enumerate(fragments):
            if URL_SCHEME_PATTERN.search(fragment):
                raise RunnerError(
                    f"mask fragment {index} must not contain a URL under "
                    f"the frozen {prompt_version} contract"
                )
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
    prompt_version: str,
) -> list[str] | int:
    response_object = _expect_object(value, f"codex {stage_name} response")
    field = {
        "takeaway": "takeaways",
        "prominence": "prominence",
        "mask": "fragments",
    }[stage_name]
    _expect_fields(response_object, f"codex {stage_name} response", {field})
    return _validate_result_items(
        stage_name,
        response_object[field],
        note_text,
        prompt_version,
    )


def _job_key(
    stage_name: str,
    note_id: str,
    takeaway_index: int | None,
) -> str:
    if stage_name == "prompt":
        return f"prompt:{note_id}"
    if stage_name == "takeaway":
        return f"takeaway:{note_id}"
    if takeaway_index is None:
        raise AssertionError(f"{stage_name} job requires a takeaway index")
    return f"{stage_name}:{note_id}:{takeaway_index}"


def _build_exec_argv(
    config: RunnerConfig | PromptRunnerConfig,
    stage: StageConfig | PromptRunnerConfig,
    workspace: Path,
    schema_path: Path | None,
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
        "model_instructions_file="
        f"{json.dumps(str(config.run_directory / 'model-instructions.md'))}",
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
    for override in RUNTIME_CONTEXT_OVERRIDES:
        arguments.extend(("-c", override))
    for feature in DISABLED_FEATURES:
        arguments.extend(("--disable", feature))
    if schema_path is not None:
        arguments.extend(("--output-schema", str(schema_path)))
    arguments.extend(
        (
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
    config: RunnerConfig | PromptRunnerConfig,
    manifest_sha256: str,
    codex_version: str,
    stage_name: str,
    stage: StageConfig | PromptRunnerConfig,
    note: Note,
    takeaway_index: int | None,
    prompt: str,
    schema_path: Path | None,
    schema: dict[str, object] | None,
    results_path: Path,
    latest: dict[str, dict[str, Any]],
    retry_failed: bool,
    execution_wrapper_sha256: str,
    retry_directive: RetryDirective | None = None,
    new_job_budget: NewJobBudget | None = None,
    reuse_source: LoadedReuseSource | None = None,
) -> list[str] | int | str:
    job_key = _job_key(stage_name, note.note_id, takeaway_index)
    previous = latest.get(job_key)
    prompt_sha256 = _sha256_bytes(prompt.encode("utf-8"))
    retry_reason: str | None = None
    if previous is not None and previous["status"] == "succeeded":
        _validate_cached_reuse_record(
            previous,
            reuse_source,
            job_key=job_key,
            stage_name=stage_name,
            stage=stage,
            note=note,
            takeaway_index=takeaway_index,
            prompt_sha256=prompt_sha256,
            schema=schema,
        )
        if retry_directive is not None and retry_directive.job_key == job_key:
            retry_directive.matched = True
            retry_reason = retry_directive.reason
        elif previous.get("prompt_sha256") != prompt_sha256:
            if not retry_failed:
                if new_job_budget is not None and new_job_budget.exhausted:
                    raise NewJobLimitReached
                raise RunnerError(
                    f"cached result for job `{job_key}` has a rendered prompt changed "
                    "by an upstream retry; inspect the superseding output and rerun "
                    "with --retry-failed"
                )
            retry_reason = "upstream rendered prompt changed"
        else:
            if stage_name == "prompt":
                response = previous.get("response")
                if not isinstance(response, str) or not response.strip():
                    raise RunnerError(
                        f"saved response for job `{job_key}` is not nonempty text"
                    )
                return response
            return _validate_result_items(
                stage_name,
                previous.get("response"),
                note.text,
                stage.prompt_version,
            )
    if previous is not None and not retry_failed:
        if retry_reason is None:
            raise RunnerError(
                f"job `{job_key}` previously failed; inspect results.jsonl and "
                "rerun with --retry-failed to create a new audited attempt"
            )
    if previous is not None and retry_reason is None:
        retry_reason = "retry after failed attempt"
    if (
        previous is None
        and reuse_source is not None
        and isinstance(stage, StageConfig)
        and schema is not None
    ):
        reusable = _find_reusable_response(
            reuse_source,
            stage_name=stage_name,
            stage=stage,
            note=note,
            takeaway_index=takeaway_index,
            prompt_sha256=prompt_sha256,
            schema=schema,
        )
        if reusable is not None:
            response, reference = reusable
            _append_reused_result(
                source=reuse_source,
                manifest_sha256=manifest_sha256,
                execution_wrapper_sha256=execution_wrapper_sha256,
                stage_name=stage_name,
                stage=stage,
                note=note,
                takeaway_index=takeaway_index,
                prompt_sha256=prompt_sha256,
                schema=schema,
                response=response,
                reference=reference,
                results_path=results_path,
                latest=latest,
            )
            return response
    if new_job_budget is not None:
        new_job_budget.claim()
    attempt = 1 if previous is None else previous["attempt"] + 1
    workspace_root = config.codex_home / "job-workspaces"
    output_raw: str | None = None
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    thread_id: str | None = None
    usage: object = None
    response: list[str] | int | str | None = None
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
            if stage_name == "prompt":
                if not output_raw.strip():
                    raise RunnerError("codex final response is empty")
                response = output_raw
            else:
                try:
                    raw_response = json.loads(output_raw)
                except json.JSONDecodeError as error:
                    raise RunnerError(
                        f"codex final response is not valid JSON: {error}"
                    ) from error
                response = _validate_response(
                    stage_name,
                    raw_response,
                    note.text,
                    stage.prompt_version,
                )
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
        "wrapper_sha256": execution_wrapper_sha256,
        "prompt_sha256": prompt_sha256,
        "response_schema_sha256": (
            None
            if schema is None
            else _sha256_bytes(_canonical_json_bytes(schema))
        ),
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
    if retry_reason is not None:
        record["retry_reason"] = retry_reason
    _append_json_line(results_path, record)
    latest[job_key] = record
    if error_message is not None:
        raise RunnerError(error_message)
    if response is None:
        raise AssertionError("successful job is missing a response")
    return response


def _takeaway_input(text: str) -> str:
    return NIP19_IDENTIFIER.sub("", text)


def _render_takeaway_prompt(prompt: str, note: Note) -> str:
    return f"{prompt}\n\n<post>\n{_takeaway_input(note.text)}\n</post>"


def _render_prominence_prompt(prompt: str, note: Note, takeaway: str) -> str:
    return (
        f"{prompt}\n\n<complete_post>\n{_takeaway_input(note.text)}"
        f"\n</complete_post>\n\n<takeaway>\n{takeaway}\n</takeaway>"
    )


def _render_mask_prompt(prompt: str, note: Note, takeaway: str) -> str:
    replacements = {"{POST}": note.text, "{TAKEAWAY}": takeaway}
    return re.sub(
        r"\{POST\}|\{TAKEAWAY\}",
        lambda match: replacements[match.group(0)],
        prompt,
    )


def _find_reusable_response(
    source: LoadedReuseSource,
    *,
    stage_name: str,
    stage: StageConfig,
    note: Note,
    takeaway_index: int | None,
    prompt_sha256: str,
    schema: dict[str, object],
) -> tuple[list[str] | int, SourceResultReference] | None:
    job_key = _job_key(stage_name, note.note_id, takeaway_index)
    reusable = source.jobs.get(job_key)
    if reusable is None or reusable.note_text != note.text:
        return None
    source_stage = source.stages[stage_name]
    target_schema_sha256 = _sha256_bytes(_canonical_json_bytes(schema))
    if (
        source_stage.prompt_version != stage.prompt_version
        or source_stage.model != stage.model
        or source_stage.reasoning_effort != stage.reasoning_effort
        or source_stage.response_schema_sha256 != target_schema_sha256
        or source_stage.prompt_sha256 != stage.prompt_sha256
        or reusable.rendered_prompt_sha256 != prompt_sha256
    ):
        return None
    response = _validate_result_items(
        stage_name,
        reusable.response,
        note.text,
        stage.prompt_version,
    )
    return response, reusable.reference


def _append_reused_result(
    *,
    source: LoadedReuseSource,
    manifest_sha256: str,
    execution_wrapper_sha256: str,
    stage_name: str,
    stage: StageConfig,
    note: Note,
    takeaway_index: int | None,
    prompt_sha256: str,
    schema: dict[str, object],
    response: list[str] | int,
    reference: SourceResultReference,
    results_path: Path,
    latest: dict[str, dict[str, Any]],
) -> None:
    job_key = _job_key(stage_name, note.note_id, takeaway_index)
    empty_sha256 = _sha256_bytes(b"")
    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "job_key": job_key,
        "stage": stage_name,
        "note_id": note.note_id,
        "takeaway_index": takeaway_index,
        "attempt": 1,
        "status": "succeeded",
        "execution": "reused",
        "model": stage.model,
        "reasoning_effort": stage.reasoning_effort,
        "codex_version": None,
        "wrapper_sha256": execution_wrapper_sha256,
        "prompt_sha256": prompt_sha256,
        "response_schema_sha256": _sha256_bytes(_canonical_json_bytes(schema)),
        "argv": [],
        "exit_code": None,
        "elapsed_seconds": 0.0,
        "thread_id": None,
        "usage": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        },
        "stdout_jsonl": "",
        "stdout_sha256": empty_sha256,
        "stderr": "",
        "stderr_sha256": empty_sha256,
        "final_output_raw": None,
        "final_output_sha256": None,
        "response": response,
        "error": None,
        "reused_from": {
            "input_sha256": source.config.input_sha256,
            "manifest_sha256": source.config.manifest_sha256,
            "results_sha256": source.config.results_sha256,
            "output_sha256": source.config.output_sha256,
            "result_line": reference.line,
            "result_sha256": reference.sha256,
            "result_attempt": reference.attempt,
        },
    }
    _append_json_line(results_path, record)
    latest[job_key] = record


def _validate_cached_reuse_record(
    record: dict[str, Any],
    source: LoadedReuseSource | None,
    *,
    job_key: str,
    stage_name: str,
    stage: StageConfig | PromptRunnerConfig,
    note: Note,
    takeaway_index: int | None,
    prompt_sha256: str,
    schema: dict[str, object] | None,
) -> None:
    execution = record.get("execution")
    if source is None:
        if execution is None:
            return
        raise RunnerError(f"cached result for job `{job_key}` has invalid reuse provenance")
    if not isinstance(stage, StageConfig) or schema is None:
        raise RunnerError(f"cached result for job `{job_key}` has invalid reuse stage")
    reusable_response = _find_reusable_response(
        source,
        stage_name=stage_name,
        stage=stage,
        note=note,
        takeaway_index=takeaway_index,
        prompt_sha256=prompt_sha256,
        schema=schema,
    )
    if execution is None:
        if reusable_response is not None and record.get("attempt") == 1:
            raise RunnerError(
                f"cached result for job `{job_key}` is missing required reuse provenance"
            )
        return
    if execution != "reused" or reusable_response is None:
        raise RunnerError(f"cached result for job `{job_key}` has invalid reuse provenance")
    reusable = source.jobs[job_key]
    reference = reusable.reference
    expected_provenance = {
        "input_sha256": source.config.input_sha256,
        "manifest_sha256": source.config.manifest_sha256,
        "results_sha256": source.config.results_sha256,
        "output_sha256": source.config.output_sha256,
        "result_line": reference.line,
        "result_sha256": reference.sha256,
        "result_attempt": reference.attempt,
    }
    empty_sha256 = _sha256_bytes(b"")
    expected_fields: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "job_key": job_key,
        "stage": stage_name,
        "note_id": note.note_id,
        "takeaway_index": takeaway_index,
        "attempt": 1,
        "status": "succeeded",
        "execution": "reused",
        "model": stage.model,
        "reasoning_effort": stage.reasoning_effort,
        "codex_version": None,
        "prompt_sha256": prompt_sha256,
        "response_schema_sha256": _sha256_bytes(_canonical_json_bytes(schema)),
        "argv": [],
        "exit_code": None,
        "elapsed_seconds": 0.0,
        "thread_id": None,
        "usage": {
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
        },
        "stdout_jsonl": "",
        "stdout_sha256": empty_sha256,
        "stderr": "",
        "stderr_sha256": empty_sha256,
        "final_output_raw": None,
        "final_output_sha256": None,
        "response": reusable.response,
        "error": None,
        "reused_from": expected_provenance,
    }
    if any(record.get(field) != value for field, value in expected_fields.items()):
        raise RunnerError(
            f"cached result for job `{job_key}` does not match its reuse source"
        )


def _execute_pipeline_jobs(
    *,
    config: RunnerConfig,
    notes: tuple[Note, ...],
    manifest_sha256: str,
    codex_version: str,
    results_path: Path,
    latest: dict[str, dict[str, Any]],
    retry_failed: bool,
    execution_wrapper_sha256: str,
    retry_directive: RetryDirective | None,
    new_job_budget: NewJobBudget,
    reuse_source: LoadedReuseSource | None,
) -> list[dict[str, object]]:
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
            execution_wrapper_sha256=execution_wrapper_sha256,
            retry_directive=retry_directive,
            new_job_budget=new_job_budget,
            reuse_source=reuse_source,
        )
        if not isinstance(takeaways, list) or not all(
            isinstance(takeaway, str) for takeaway in takeaways
        ):
            raise AssertionError("takeaway job returned an invalid response")
        output_takeaways: list[dict[str, object]] = []
        for index, takeaway in enumerate(takeaways):
            prominence: int | None = None
            if config.prominence is not None:
                prominence_result = _run_job(
                    config=config,
                    manifest_sha256=manifest_sha256,
                    codex_version=codex_version,
                    stage_name="prominence",
                    stage=config.prominence,
                    note=note,
                    takeaway_index=index,
                    prompt=_render_prominence_prompt(
                        config.prominence.prompt,
                        note,
                        takeaway,
                    ),
                    schema_path=(
                        config.run_directory / "prominence-output-schema.json"
                    ),
                    schema=PROMINENCE_SCHEMA,
                    results_path=results_path,
                    latest=latest,
                    retry_failed=retry_failed,
                    execution_wrapper_sha256=execution_wrapper_sha256,
                    retry_directive=retry_directive,
                    new_job_budget=new_job_budget,
                    reuse_source=reuse_source,
                )
                if isinstance(prominence_result, bool) or not isinstance(
                    prominence_result, int
                ):
                    raise AssertionError(
                        "prominence job returned an invalid response"
                    )
                prominence = prominence_result
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
                execution_wrapper_sha256=execution_wrapper_sha256,
                retry_directive=retry_directive,
                new_job_budget=new_job_budget,
                reuse_source=reuse_source,
            )
            output_takeaway: dict[str, object] = {
                "text": takeaway,
                "fragments": fragments,
            }
            if prominence is not None:
                output_takeaway["prominence"] = prominence
            output_takeaways.append(output_takeaway)
        output_notes.append({"note_id": note.note_id, "takeaways": output_takeaways})
        new_job_budget.completed_notes += 1
        new_job_budget.completed_takeaways += len(output_takeaways)

    return output_notes


def run(
    config_path: Path,
    *,
    retry_failed: bool,
    max_new_jobs: int | None = None,
    retry_job: str | None = None,
    retry_reason: str | None = None,
    runner_upgrade_reason: str | None = None,
) -> PipelineRunOutcome:
    if max_new_jobs is not None and max_new_jobs < 1:
        raise RunnerError("--max-new-jobs must be at least 1")
    config = RunnerConfig.load(config_path)
    notes = _load_notes(config.input_path)
    reuse_source = (
        None
        if config.reuse_source is None
        else _load_reuse_source(config.reuse_source, notes)
    )
    _prepare_codex_home(config.codex_home)
    _validate_file_credentials(config.codex_home)
    codex_version = _codex_version(config)
    manifest = _build_manifest(config, codex_version)
    prepared_manifest = _prepare_run_directory(
        config,
        manifest,
        runner_upgrade_reason=runner_upgrade_reason,
    )
    results_path = config.run_directory / "results.jsonl"
    latest = _load_latest_results(
        results_path,
        prepared_manifest.manifest_sha256,
        prepared_manifest.provenance,
    )
    execution_provenance = _append_runner_upgrade(
        config.run_directory,
        prepared_manifest,
    )
    manifest_sha256 = prepared_manifest.manifest_sha256
    retry_directive: RetryDirective | None = None
    if retry_job is not None:
        previous = latest.get(retry_job)
        if previous is None:
            raise RunnerError(f"--retry-job `{retry_job}` has no saved result")
        if previous.get("status") != "succeeded":
            raise RunnerError(
                f"--retry-job `{retry_job}` is not a successful result; use "
                "--retry-failed instead"
            )
        retry_directive = RetryDirective(retry_job, retry_reason or "")
    (config.run_directory / "output.json").unlink(missing_ok=True)
    new_job_budget = NewJobBudget(max_new_jobs)

    try:
        try:
            output_notes = _execute_pipeline_jobs(
                config=config,
                notes=notes,
                manifest_sha256=manifest_sha256,
                codex_version=codex_version,
                results_path=results_path,
                latest=latest,
                retry_failed=retry_failed,
                execution_wrapper_sha256=execution_provenance.active_wrapper_sha256,
                retry_directive=retry_directive,
                new_job_budget=new_job_budget,
                reuse_source=reuse_source,
            )
        except NewJobLimitReached:
            if retry_directive is not None and not retry_directive.matched:
                raise RunnerError(
                    f"--retry-job `{retry_directive.job_key}` was not reached before "
                    "--max-new-jobs"
                )
            return PipelineRunOutcome(
                complete=False,
                new_jobs=new_job_budget.used,
                completed_notes=new_job_budget.completed_notes,
                completed_takeaways=new_job_budget.completed_takeaways,
                output=None,
            )

        if retry_directive is not None and not retry_directive.matched:
            raise RunnerError(
                f"--retry-job `{retry_directive.job_key}` is not part of the current pipeline"
            )
        output: dict[str, object] = {
            "schema_version": config.schema_version,
            "manifest_sha256": manifest_sha256,
            "notes": output_notes,
        }
        _atomic_write(
            config.run_directory / "output.json", _canonical_json_bytes(output)
        )
        return PipelineRunOutcome(
            complete=True,
            new_jobs=new_job_budget.used,
            completed_notes=new_job_budget.completed_notes,
            completed_takeaways=new_job_budget.completed_takeaways,
            output=output,
        )
    finally:
        if config.reuse_source is not None:
            _verify_reuse_source_hashes(config.reuse_source)


def run_prompts(config_path: Path, *, retry_failed: bool) -> dict[str, object]:
    config = PromptRunnerConfig.load(config_path)
    _prepare_codex_home(config.codex_home)
    _validate_file_credentials(config.codex_home)
    codex_version = _codex_version(config)
    manifest = _build_prompt_manifest(config, codex_version)
    prepared_manifest = _prepare_manifest_directory(config.run_directory, manifest)
    manifest_sha256 = prepared_manifest.manifest_sha256
    results_path = config.run_directory / "results.jsonl"
    latest = _load_latest_results(
        results_path,
        manifest_sha256,
        prepared_manifest.provenance,
    )
    (config.run_directory / "output.json").unlink(missing_ok=True)
    responses: list[dict[str, str]] = []

    for prompt in config.prompts:
        response = _run_job(
            config=config,
            manifest_sha256=manifest_sha256,
            codex_version=codex_version,
            stage_name="prompt",
            stage=config,
            note=Note(note_id=prompt.prompt_id, text=""),
            takeaway_index=None,
            prompt=prompt.text,
            schema_path=None,
            schema=None,
            results_path=results_path,
            latest=latest,
            retry_failed=retry_failed,
            execution_wrapper_sha256=prepared_manifest.provenance.active_wrapper_sha256,
        )
        if not isinstance(response, str):
            raise AssertionError("successful prompt job returned structured output")
        responses.append({"prompt_id": prompt.prompt_id, "response": response})

    output: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "responses": responses,
    }
    _atomic_write(config.run_directory / "output.json", _canonical_json_bytes(output))
    return output


def run_direct_prompt(
    prompt: str,
    *,
    codex_binary: str,
    codex_home: Path,
    model: str | None,
    reasoning_effort: str | None,
) -> str:
    prompt = _expect_string(prompt, "--text")
    resolved_binary = _resolve_executable(
        codex_binary,
        "--codex-binary",
        Path.cwd(),
    )
    resolved_home = codex_home.expanduser().resolve()
    model = _expect_identifier(model, "--model")
    reasoning_effort = _expect_identifier(
        reasoning_effort,
        "--reasoning-effort",
    )

    with tempfile.TemporaryDirectory(prefix="codex-direct-") as temporary:
        temporary_root = Path(temporary).resolve()
        config_path = temporary_root / "config.json"
        run_directory = temporary_root / "run"
        _atomic_write(
            config_path,
            _canonical_json_bytes(
                {
                    "schema_version": SCHEMA_VERSION,
                    "codex_binary": str(resolved_binary),
                    "codex_home": str(resolved_home),
                    "run_directory": str(run_directory),
                    "model": model,
                    "reasoning_effort": reasoning_effort,
                    "prompts": [{"prompt_id": "direct", "text": prompt}],
                }
            ),
        )
        try:
            output = run_prompts(config_path, retry_failed=False)
        except RunnerError as error:
            results_path = run_directory / "results.jsonl"
            last_record: object = None
            if results_path.is_file():
                try:
                    lines = results_path.read_text(encoding="utf-8").splitlines()
                    if lines:
                        last_record = json.loads(lines[-1])
                except (OSError, UnicodeError, json.JSONDecodeError):
                    pass
            if isinstance(last_record, dict):
                detail = last_record.get("stderr")
                if isinstance(detail, str) and detail.strip():
                    raise RunnerError(f"{error}: {detail.strip()}") from error
            raise
        responses = output.get("responses")
        if not isinstance(responses, list) or len(responses) != 1:
            raise AssertionError("direct prompt returned an invalid response list")
        response = responses[0]
        if not isinstance(response, dict) or response.get("prompt_id") != "direct":
            raise AssertionError("direct prompt returned an invalid response record")
        text = response.get("response")
        if not isinstance(text, str) or not text.strip():
            raise AssertionError("direct prompt returned an empty response")
        return text


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
        description="Run isolated, auditable prompts through codex exec jobs"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    run_parser = subcommands.add_parser("run", help="run or resume a batch")
    run_parser.add_argument("config", type=Path)
    run_parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="explicitly retry the latest failed attempt for each failed job",
    )
    run_parser.add_argument(
        "--max-new-jobs",
        type=int,
        help="pause successfully after spawning at most this many uncached jobs",
    )
    run_parser.add_argument(
        "--retry-job",
        help="explicitly rerun one saved successful job after semantic review",
    )
    run_parser.add_argument(
        "--retry-reason",
        help="required audit reason for --retry-job",
    )
    run_parser.add_argument(
        "--runner-upgrade-reason",
        help="audit reason for resuming an existing run with changed wrapper code",
    )
    prompt_parser = subcommands.add_parser(
        "prompt", help="run one direct prompt or a preserved prompt batch"
    )
    prompt_parser.add_argument(
        "config",
        type=Path,
        nargs="?",
        help="batch configuration; omit when using --text",
    )
    prompt_parser.add_argument(
        "--text",
        help="direct prompt text, or - to read it from stdin",
    )
    prompt_parser.add_argument("--model")
    prompt_parser.add_argument("--reasoning-effort")
    prompt_parser.add_argument("--codex-home", type=Path)
    prompt_parser.add_argument("--codex-binary")
    prompt_parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="explicitly retry failed jobs in config-based batch mode",
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
        if parsed.command == "prompt":
            if parsed.text is not None:
                if parsed.config is not None:
                    raise RunnerError("use either a config path or --text, not both")
                if parsed.retry_failed:
                    raise RunnerError("--retry-failed is only valid with a config path")
                prompt = sys.stdin.read() if parsed.text == "-" else parsed.text
                response = run_direct_prompt(
                    prompt,
                    codex_binary=parsed.codex_binary or "codex",
                    codex_home=parsed.codex_home or DEFAULT_CODEX_HOME,
                    model=parsed.model,
                    reasoning_effort=parsed.reasoning_effort,
                )
                sys.stdout.write(response)
                return 0
            if parsed.config is None:
                raise RunnerError("provide a config path or use --text")
            if any(
                value is not None
                for value in (
                    parsed.model,
                    parsed.reasoning_effort,
                    parsed.codex_home,
                    parsed.codex_binary,
                )
            ):
                raise RunnerError(
                    "--model, --reasoning-effort, --codex-home, and "
                    "--codex-binary are only valid with --text"
                )
            output = run_prompts(parsed.config, retry_failed=parsed.retry_failed)
            print(json.dumps({"prompts": len(output["responses"])}, sort_keys=True))
            return 0
        if (parsed.retry_job is None) != (parsed.retry_reason is None):
            raise RunnerError("--retry-job and --retry-reason must be used together")
        if parsed.retry_job is not None and parsed.retry_failed:
            raise RunnerError("--retry-job cannot be combined with --retry-failed")
        if parsed.retry_reason is not None and not parsed.retry_reason.strip():
            raise RunnerError("--retry-reason must not be empty")
        if (
            parsed.runner_upgrade_reason is not None
            and not parsed.runner_upgrade_reason.strip()
        ):
            raise RunnerError("--runner-upgrade-reason must not be empty")
        outcome = run(
            parsed.config,
            retry_failed=parsed.retry_failed,
            max_new_jobs=parsed.max_new_jobs,
            retry_job=parsed.retry_job,
            retry_reason=parsed.retry_reason,
            runner_upgrade_reason=parsed.runner_upgrade_reason,
        )
        status: dict[str, object] = {}
        if parsed.max_new_jobs is not None:
            status.update(
                {
                    "complete": outcome.complete,
                    "new_jobs": outcome.new_jobs,
                    "completed_notes": outcome.completed_notes,
                    "completed_takeaways": outcome.completed_takeaways,
                }
            )
        if outcome.output is not None:
            notes = outcome.output["notes"]
            if not isinstance(notes, list):
                raise AssertionError("pipeline output contains invalid notes")
            status["notes"] = len(notes)
            status["takeaways"] = sum(len(note["takeaways"]) for note in notes)
        print(json.dumps(status, sort_keys=True))
        return 0
    except RunnerError as error:
        print(f"codex exec wrapper failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
