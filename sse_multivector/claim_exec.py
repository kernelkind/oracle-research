#!/usr/bin/env python3
"""Generate source-bound claims without changing the preserved subject runner."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import codex_exec as engine


CLAIM_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        }
    },
    "required": ["claims"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class ClaimRunnerConfig:
    config_path: Path
    codex_binary: Path
    codex_home: Path
    input_path: Path
    run_directory: Path
    claim: engine.StageConfig

    @classmethod
    def load(cls, path: Path) -> "ClaimRunnerConfig":
        config_path = path.expanduser().resolve()
        base = config_path.parent
        value = engine._expect_object(
            engine._load_json(config_path, "config"), "config"
        )
        engine._expect_fields(
            value,
            "config",
            {
                "schema_version",
                "codex_binary",
                "codex_home",
                "input_path",
                "run_directory",
                "claim",
            },
        )
        if value["schema_version"] != engine.SCHEMA_VERSION:
            raise engine.RunnerError("unsupported claim config schema version")
        config = cls(
            config_path=config_path,
            codex_binary=engine._resolve_executable(
                value["codex_binary"], "codex_binary", base
            ),
            codex_home=engine._resolve_path(value["codex_home"], "codex_home", base),
            input_path=engine._resolve_path(value["input_path"], "input_path", base),
            run_directory=engine._resolve_path(
                value["run_directory"], "run_directory", base
            ),
            claim=engine.StageConfig.load(value["claim"], "claim", base),
        )
        engine._validate_codex_home(config.codex_home)
        return config


def _manifest(config: ClaimRunnerConfig, codex_version: str) -> dict[str, object]:
    return {
        "schema_version": engine.SCHEMA_VERSION,
        "mode": "claim_generation",
        "wrapper_sha256": engine._sha256_file(Path(__file__).resolve()),
        "engine_sha256": engine._sha256_file(Path(engine.__file__).resolve()),
        "codex_binary": str(config.codex_binary),
        "codex_version": codex_version,
        "codex_home": str(config.codex_home),
        "input_path": str(config.input_path),
        "input_sha256": engine._sha256_file(config.input_path),
        "claim_envelope_version": "exact-note-text-v1",
        "claim_input_normalization_version": "none-v1",
        "claim": engine._stage_manifest(config.claim, CLAIM_SCHEMA),
        "isolation": engine._isolation_manifest(),
    }


def _render_prompt(prompt: str, note: engine.Note) -> str:
    return f"{prompt}\n\nText:\n{note.text}"


def _validate_claims(value: object) -> list[str]:
    response = engine._expect_object(value, "codex claim response")
    engine._expect_fields(response, "codex claim response", {"claims"})
    return engine._validate_string_array(
        response["claims"], "claim", allow_empty=True
    )


def _saved_claims(
    record: dict[str, Any],
    *,
    manifest_sha256: str,
    wrapper_sha256: str,
    codex_version: str,
    stage: engine.StageConfig,
    note: engine.Note,
    rendered_prompt: str,
) -> list[str]:
    job_key = f"claim:{note.note_id}"
    schema_sha256 = engine._sha256_bytes(engine._canonical_json_bytes(CLAIM_SCHEMA))
    if (
        record.get("manifest_sha256") != manifest_sha256
        or record.get("job_key") != job_key
        or record.get("stage") != "claim"
        or record.get("note_id") != note.note_id
        or record.get("wrapper_sha256") != wrapper_sha256
        or record.get("codex_version") != codex_version
        or record.get("model") != stage.model
        or record.get("reasoning_effort") != stage.reasoning_effort
        or record.get("prompt_sha256")
        != engine._sha256_bytes(rendered_prompt.encode("utf-8"))
        or record.get("response_schema_sha256") != schema_sha256
    ):
        raise engine.RunnerError(
            f"cached result for job `{job_key}` does not match its claim contract"
        )
    claims = engine._validate_string_array(
        record.get("response"), "claim", allow_empty=True
    )
    raw = record.get("final_output_raw")
    if not isinstance(raw, str):
        raise engine.RunnerError(f"cached result for job `{job_key}` has no final output")
    if record.get("final_output_sha256") != engine._sha256_bytes(raw.encode("utf-8")):
        raise engine.RunnerError(
            f"cached result for job `{job_key}` has invalid final output provenance"
        )
    try:
        final = json.loads(raw)
    except json.JSONDecodeError as error:
        raise engine.RunnerError(
            f"cached result for job `{job_key}` final output is invalid JSON"
        ) from error
    if final != {"claims": claims}:
        raise engine.RunnerError(
            f"cached result for job `{job_key}` final output does not match its response"
        )
    return claims


def _run_claim(
    *,
    config: ClaimRunnerConfig,
    manifest_sha256: str,
    wrapper_sha256: str,
    codex_version: str,
    note: engine.Note,
    latest: dict[str, dict[str, Any]],
    retry_failed: bool,
    budget: engine.NewJobBudget,
) -> list[str]:
    job_key = f"claim:{note.note_id}"
    prompt = _render_prompt(config.claim.prompt, note)
    previous = latest.get(job_key)
    if previous is not None and previous.get("status") == "succeeded":
        return _saved_claims(
            previous,
            manifest_sha256=manifest_sha256,
            wrapper_sha256=wrapper_sha256,
            codex_version=codex_version,
            stage=config.claim,
            note=note,
            rendered_prompt=prompt,
        )
    if previous is not None and not retry_failed:
        raise engine.RunnerError(
            f"job `{job_key}` previously failed; inspect results.jsonl and rerun "
            "with --retry-failed to create a new audited attempt"
        )
    budget.claim()
    attempt = 1 if previous is None else previous["attempt"] + 1
    workspace_root = config.codex_home / "job-workspaces"
    schema_path = config.run_directory / "claim-output-schema.json"
    output_raw: str | None = None
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    thread_id: str | None = None
    usage: object = None
    claims: list[str] | None = None
    error_message: str | None = None
    argv: list[str] = []
    started_at = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="claim-", dir=workspace_root) as temporary:
        workspace = Path(temporary).resolve()
        response_path = workspace / "response.json"
        argv = engine._build_exec_argv(
            config, config.claim, workspace, schema_path, response_path
        )
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                check=False,
                capture_output=True,
                text=True,
                cwd=workspace,
                env=engine._isolated_environment(config.codex_home),
            )
            stdout = completed.stdout
            stderr = completed.stderr
            exit_code = completed.returncode
            if response_path.exists():
                output_raw = response_path.read_text(encoding="utf-8")
            if exit_code != 0:
                raise engine.RunnerError(f"codex exec exited with status {exit_code}")
            thread_id, usage = engine._parse_event_stream(stdout)
            if output_raw is None:
                raise engine.RunnerError("codex exec did not write its final response")
            try:
                response = json.loads(output_raw)
            except json.JSONDecodeError as error:
                raise engine.RunnerError(
                    f"codex final response is not valid JSON: {error}"
                ) from error
            claims = _validate_claims(response)
        except (OSError, UnicodeError, engine.RunnerError) as error:
            error_message = str(error)

    record: dict[str, object] = {
        "schema_version": engine.SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "job_key": job_key,
        "stage": "claim",
        "note_id": note.note_id,
        "attempt": attempt,
        "status": "failed" if error_message is not None else "succeeded",
        "model": config.claim.model,
        "reasoning_effort": config.claim.reasoning_effort,
        "codex_version": codex_version,
        "wrapper_sha256": wrapper_sha256,
        "prompt_sha256": engine._sha256_bytes(prompt.encode("utf-8")),
        "response_schema_sha256": engine._sha256_bytes(
            engine._canonical_json_bytes(CLAIM_SCHEMA)
        ),
        "argv": argv,
        "exit_code": exit_code,
        "elapsed_seconds": time.monotonic() - started_at,
        "thread_id": thread_id,
        "usage": usage,
        "stdout_jsonl": stdout,
        "stdout_sha256": engine._sha256_bytes(stdout.encode("utf-8")),
        "stderr": stderr,
        "stderr_sha256": engine._sha256_bytes(stderr.encode("utf-8")),
        "final_output_raw": output_raw,
        "final_output_sha256": (
            None
            if output_raw is None
            else engine._sha256_bytes(output_raw.encode("utf-8"))
        ),
        "response": claims,
        "error": error_message,
    }
    if previous is not None:
        record["retry_reason"] = "retry after failed attempt"
    engine._append_json_line(config.run_directory / "results.jsonl", record)
    latest[job_key] = record
    if error_message is not None:
        raise engine.RunnerError(error_message)
    assert claims is not None
    return claims


def run_claims(
    config_path: Path,
    *,
    retry_failed: bool,
    max_new_jobs: int | None,
) -> dict[str, object]:
    if max_new_jobs is not None and max_new_jobs < 1:
        raise engine.RunnerError("--max-new-jobs must be at least 1")
    config = ClaimRunnerConfig.load(config_path)
    notes = engine._load_notes(config.input_path)
    engine._prepare_codex_home(config.codex_home)
    engine._validate_file_credentials(config.codex_home)
    codex_version = engine._codex_version(config)
    manifest = _manifest(config, codex_version)
    prepared = engine._prepare_manifest_directory(config.run_directory, manifest)
    engine._atomic_write(
        config.run_directory / "claim-output-schema.json",
        engine._canonical_json_bytes(CLAIM_SCHEMA),
    )
    latest = engine._load_latest_results(
        config.run_directory / "results.jsonl",
        prepared.manifest_sha256,
        prepared.provenance,
    )
    (config.run_directory / "output.json").unlink(missing_ok=True)
    budget = engine.NewJobBudget(max_new_jobs)
    output_notes: list[dict[str, object]] = []
    try:
        for note in notes:
            claims = _run_claim(
                config=config,
                manifest_sha256=prepared.manifest_sha256,
                wrapper_sha256=prepared.provenance.active_wrapper_sha256,
                codex_version=codex_version,
                note=note,
                latest=latest,
                retry_failed=retry_failed,
                budget=budget,
            )
            output_notes.append(
                {
                    "note_id": note.note_id,
                    "text": note.text,
                    "claims": [
                        {"source_index": index, "text": claim}
                        for index, claim in enumerate(claims)
                    ],
                }
            )
            budget.completed_notes += 1
    except engine.NewJobLimitReached:
        return {
            "complete": False,
            "new_jobs": budget.used,
            "completed_notes": budget.completed_notes,
        }
    output: dict[str, object] = {
        "schema_version": engine.SCHEMA_VERSION,
        "manifest_sha256": prepared.manifest_sha256,
        "notes": output_notes,
    }
    engine._atomic_write(
        config.run_directory / "output.json", engine._canonical_json_bytes(output)
    )
    status: dict[str, object] = {
        "notes": len(output_notes),
        "claims": sum(len(note["claims"]) for note in output_notes),
    }
    if max_new_jobs is not None:
        status.update(
            {
                "complete": True,
                "new_jobs": budget.used,
                "completed_notes": budget.completed_notes,
            }
        )
    return status


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate isolated, auditable claims")
    subcommands = parser.add_subparsers(dest="command", required=True)
    claims = subcommands.add_parser("claims", help="generate claims for each note")
    claims.add_argument("config", type=Path)
    claims.add_argument("--retry-failed", action="store_true")
    claims.add_argument("--max-new-jobs", type=int)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        status = run_claims(
            parsed.config,
            retry_failed=parsed.retry_failed,
            max_new_jobs=parsed.max_new_jobs,
        )
        print(json.dumps(status, sort_keys=True))
        return 0
    except engine.RunnerError as error:
        print(f"claim exec wrapper failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
