#!/usr/bin/env python3
"""Generate source-bound claims through the shared extraction workflow."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import extraction_pipeline as engine


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
    runner_binary: Path
    auth_file: Path | None
    provider: str
    timeout_seconds: float
    max_output_tokens: int | None
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
                "runner_binary",
                "auth_file",
                "input_path",
                "run_directory",
                "claim",
            }
            | (engine.RUNTIME_FIELDS & value.keys()),
        )
        if value["schema_version"] != engine.SCHEMA_VERSION:
            raise engine.RunnerError("unsupported claim config schema version")
        config = cls(
            config_path=config_path,
            runner_binary=engine._resolve_executable(
                value["runner_binary"], "runner_binary", base
            ),
            **engine._runtime_options(value, base),
            input_path=engine._resolve_path(value["input_path"], "input_path", base),
            run_directory=engine._resolve_path(
                value["run_directory"], "run_directory", base
            ),
            claim=engine.StageConfig.load(value["claim"], "claim", base),
        )
        engine._validate_auth_file(config.auth_file)
        return config


def _manifest(config: ClaimRunnerConfig, runner_version: str) -> dict[str, object]:
    return {
        "schema_version": 2,
        "mode": "claim_generation",
        **engine._runtime_manifest(config),
        "wrapper_sha256": engine._sha256_file(Path(__file__).resolve()),
        "engine_sha256": engine._sha256_file(Path(engine.__file__).resolve()),
        "runner_binary": str(config.runner_binary),
        "runner_version": runner_version,
        "auth_file": None if config.auth_file is None else str(config.auth_file),
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
    response = engine._expect_object(value, "model claim response")
    engine._expect_fields(response, "model claim response", {"claims"})
    return engine._validate_string_array(response["claims"], "claim", allow_empty=True)


def _saved_claims(
    record: dict[str, Any],
    *,
    manifest_sha256: str,
    wrapper_sha256: str,
    runner_version: str,
    stage: engine.StageConfig,
    note: engine.Note,
    rendered_prompt: str,
    config: ClaimRunnerConfig,
) -> list[str]:
    engine.validate_model_receipt(
        config,
        stage,
        rendered_prompt,
        CLAIM_SCHEMA,
        engine._load_json(config.run_directory / "manifest.json", "run manifest"),
        record,
    )
    job_key = f"claim:{note.note_id}"
    schema_sha256 = engine._sha256_bytes(engine._canonical_json_bytes(CLAIM_SCHEMA))
    if (
        record.get("manifest_sha256") != manifest_sha256
        or record.get("job_key") != job_key
        or record.get("stage") != "claim"
        or record.get("note_id") != note.note_id
        or record.get("wrapper_sha256") != wrapper_sha256
        or record.get("runner_version") != runner_version
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
        raise engine.RunnerError(
            f"cached result for job `{job_key}` has no final output"
        )
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
    runner_version: str,
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
            runner_version=runner_version,
            stage=config.claim,
            note=note,
            rendered_prompt=prompt,
            config=config,
        )
    if previous is not None and not retry_failed:
        raise engine.RunnerError(
            f"job `{job_key}` previously failed; inspect results.jsonl and rerun "
            "with --retry-failed to create a new audited attempt"
        )
    budget.claim()
    attempt = 1 if previous is None else previous["attempt"] + 1
    attempt_result = engine._invoke_model(config, config.claim, prompt, CLAIM_SCHEMA)
    error_message = attempt_result["error"]
    claims = None
    if error_message is None:
        try:
            claims = _validate_claims(json.loads(attempt_result["final_output_raw"]))
        except (json.JSONDecodeError, engine.RunnerError) as error:
            error_message = str(error)

    record: dict[str, object] = {
        "schema_version": 2,
        "manifest_sha256": manifest_sha256,
        "job_key": job_key,
        "stage": "claim",
        "note_id": note.note_id,
        "attempt": attempt,
        "status": "failed" if error_message is not None else "succeeded",
        "model": config.claim.model,
        "reasoning_effort": config.claim.reasoning_effort,
        "runner_version": runner_version,
        "wrapper_sha256": wrapper_sha256,
        "prompt_sha256": engine._sha256_bytes(prompt.encode("utf-8")),
        "response_schema_sha256": engine._sha256_bytes(
            engine._canonical_json_bytes(CLAIM_SCHEMA)
        ),
        **attempt_result,
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
    runner_version = engine._runner_version(config)
    manifest = _manifest(config, runner_version)
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
                runner_version=runner_version,
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
