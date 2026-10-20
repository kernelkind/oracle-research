"""Read-only readers for saved Codex-format experiment evidence.

No login, model execution, batch execution, or transport is provided here.
Retired source bytes are read from the pinned Git revision, never executed.
Standalone model calls belong to run-model.sh; prompt experiments to experiment.py.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LEGACY_REVISION = "b1649eb2f7b38ccea7d60e2e55bf70f5d7d85bcd"
LEGACY_WRAPPER_SHA256 = "ebf1942737069a49146d7336c6936dd2fa5cdd8d4b6a2b24274f01bc9f83e2fe"
TAKEAWAY_ENVELOPE_VERSION = "xml-post-v1"
TAKEAWAY_INPUT_NORMALIZATION_VERSION = "remove-long-ascii-nip19-identifiers-v2"
MINIMAL_MODEL_INSTRUCTIONS = "Follow the user's instructions.\n"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$")

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
NIP19_IDENTIFIER = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"(?ai:(?:nostr:)?(?:nprofile|nevent|nrelay|naddr|npub|nsec|note)1"
    r"[023456789acdefghjklmnpqrstuvwxyz]{20,})"
    r"(?:[?#][^\s<>\"']*)?(?=$|[^A-Za-z0-9_])"
)

SUBJECT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "subjects": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        }
    },
    "required": ["subjects"],
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
    """Invalid historical evidence."""


@lru_cache(maxsize=128)
def _resolve_revision(repository: Path, revision: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", revision):
        return revision
    mapping = repository / "docs/experiments/commit-map.txt"
    if not mapping.exists():
        return revision
    rows = mapping.read_text().splitlines()
    if not rows or rows[0].split() != ["old", "new"]:
        raise RunnerError("Invalid Git commit mapping header")
    matches = []
    for row in rows[1:]:
        fields = row.split()
        if len(fields) != 2 or any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in fields):
            raise RunnerError("Invalid Git commit mapping row")
        if fields[0].startswith(revision.lower()):
            matches.append(fields)
    if len(matches) > 1:
        raise RunnerError(f"Ambiguous original Git revision: {revision}")
    if not matches:
        return revision
    original, rewritten = matches[0]
    available = subprocess.run(
        ["git", "--no-replace-objects", "cat-file", "-e", original + "^{commit}"],
        cwd=repository, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return original if available.returncode == 0 else rewritten


def source_at_revision(path: Path, revision: str) -> bytes:
    """Read original Git bytes, resolving rewritten commits with the bundled map."""
    path = Path(path)
    relative = path.relative_to(REPOSITORY_ROOT) if path.is_absolute() else path
    resolved = _resolve_revision(REPOSITORY_ROOT, revision)
    return subprocess.check_output(
        ["git", "--no-replace-objects", "show", resolved + ":" + relative.as_posix()],
        cwd=REPOSITORY_ROOT,
    )


@lru_cache(maxsize=1)
def _retired_source() -> bytes:
    payload = source_at_revision(REPOSITORY_ROOT / "sse_multivector/codex_exec.py", LEGACY_REVISION)
    if hashlib.sha256(payload).hexdigest() != LEGACY_WRAPPER_SHA256:
        raise RunnerError("retired runner source hash mismatch")
    return payload


def source_bytes(path: Path) -> bytes:
    path = Path(path).resolve()
    if path == REPOSITORY_ROOT / "sse_multivector/codex_exec.py":
        return _retired_source()
    return path.read_bytes()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(source_bytes(path)).hexdigest()


def _resolve_executable(value: object, name: str, base: Path) -> Path:
    # Historical metadata only: no executable lookup, login, or invocation.
    return _resolve_path(value, name, base)


@dataclass(frozen=True)
class RunnerProvenance:
    initial_wrapper_sha256: str
    active_wrapper_sha256: str
    boundaries: tuple[tuple[int, str], ...]

@dataclass(frozen=True)
class SourceResultReference:
    line: int
    sha256: str
    attempt: int

@dataclass(frozen=True)
class Note:
    note_id: str
    text: str

@dataclass(frozen=True)
class PromptJob:
    prompt_id: str
    text: str

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
class SubjectRunnerConfig:
    config_path: Path
    codex_binary: Path
    codex_home: Path
    input_path: Path
    run_directory: Path
    subject: StageConfig

    @classmethod
    def load(cls, path: Path) -> "SubjectRunnerConfig":
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
                "subject",
            },
        )
        schema_version = value["schema_version"]
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version != SCHEMA_VERSION
        ):
            raise RunnerError("unsupported subject config schema version")
        config = cls(
            config_path=config_path,
            codex_binary=_resolve_executable(
                value["codex_binary"], "codex_binary", base
            ),
            codex_home=_resolve_path(value["codex_home"], "codex_home", base),
            input_path=_resolve_path(value["input_path"], "input_path", base),
            run_directory=_resolve_path(
                value["run_directory"], "run_directory", base
            ),
            subject=StageConfig.load(value["subject"], "subject", base),
        )
        return config

@dataclass(frozen=True)
class PromptRunnerConfig:
    config_path: Path
    codex_binary: Path
    codex_home: Path
    run_directory: Path
    model: str
    reasoning_effort: str
    prompts: tuple[PromptJob, ...]
    output_schema: dict[str, object] | None = None

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
            } | ({"output_schema"} & value.keys()),
        )
        if value["schema_version"] != SCHEMA_VERSION:
            raise RunnerError("unsupported config schema version")
        output_schema = None
        if "output_schema" in value:
            output_schema = _expect_object(
                value["output_schema"], "config.output_schema"
            )
            if output_schema.get("type") != "object":
                raise RunnerError("`config.output_schema.type` must be `object`")
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
            output_schema=output_schema,
        )
        return config

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

def _ordered_json_bytes(value: object) -> bytes:
    """Preserve property order for caller-supplied structured output schemas."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")

def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

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

def _build_prompt_manifest(
    config: PromptRunnerConfig,
    codex_version: str,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "mode": "prompt",
        "wrapper_sha256": LEGACY_WRAPPER_SHA256,
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
    if config.output_schema is not None:
        manifest["response_schema"] = config.output_schema
        manifest["response_schema_sha256"] = _sha256_bytes(
            _ordered_json_bytes(config.output_schema)
        )
    return manifest

def _build_subject_manifest(
    config: SubjectRunnerConfig,
    codex_version: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "atomic_subject_generation",
        "wrapper_sha256": LEGACY_WRAPPER_SHA256,
        "codex_binary": str(config.codex_binary),
        "codex_version": codex_version,
        "codex_home": str(config.codex_home),
        "input_path": str(config.input_path),
        "input_sha256": _sha256_file(config.input_path),
        "subject_envelope_version": TAKEAWAY_ENVELOPE_VERSION,
        "subject_input_normalization_version": (
            TAKEAWAY_INPUT_NORMALIZATION_VERSION
        ),
        "subject": _stage_manifest(config.subject, SUBJECT_SCHEMA),
        "isolation": _isolation_manifest(),
    }

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

def _job_key(
    stage_name: str,
    note_id: str,
    takeaway_index: int | None,
) -> str:
    if stage_name == "prompt":
        return f"prompt:{note_id}"
    if stage_name == "subject":
        return f"subject:{note_id}"
    if stage_name == "takeaway":
        return f"takeaway:{note_id}"
    if takeaway_index is None:
        raise AssertionError(f"{stage_name} job requires a takeaway index")
    return f"{stage_name}:{note_id}:{takeaway_index}"

def _build_exec_argv(
    config: RunnerConfig | SubjectRunnerConfig | PromptRunnerConfig,
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

def _takeaway_input(text: str) -> str:
    return NIP19_IDENTIFIER.sub("", text)

def _render_subject_prompt(prompt: str, note: Note) -> str:
    return f"{prompt}\n\n<post>\n{_takeaway_input(note.text)}\n</post>"
