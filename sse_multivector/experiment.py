#!/usr/bin/env python3
"""Prepare, run, compare, revise and review preserved prompt experiments.

Only `run` performs inference. See model-runner.md for the supported workflow.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
import fcntl
import json
import math
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

try:
    from . import extraction_pipeline as engine
    from . import experiment_inputs as inputs
except ImportError:
    import extraction_pipeline as engine
    import experiment_inputs as inputs


def read(path):
    return engine._load_json(Path(path), str(path))


def write(path, value):
    # Schema property order is part of request identity; do not sort nested keys.
    engine._atomic_write(Path(path), engine._ordered_json_bytes(value))


def resolve(path, base):
    path = Path(path).expanduser()
    return (base / path).resolve() if not path.is_absolute() else path.resolve()


@contextmanager
def locked(directory):
    with (directory / ".experiment.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("experiment is already active") from error
        yield


def load(directory):
    directory = Path(directory).resolve()
    envelope = read(directory / "experiment.json")
    plan = envelope["plan"]
    if inputs.digest(plan) != envelope["sha256"]:
        raise ValueError("prepared experiment changed; prepare a new experiment")
    for name, expected in plan["files"].items():
        if engine._sha256_file(directory / name) != expected:
            raise ValueError(f"prepared {name} changed; prepare a new experiment")
    config = engine.PromptRunnerConfig.load(directory / "runner-config.json")
    manifest = read(Path(plan["run_directory"]) / "manifest.json")
    if inputs.digest(manifest) != plan["manifest_sha256"]:
        raise ValueError("prepared run manifest changed")
    return plan, config, manifest


def spec_setup(path):
    path = Path(path).resolve()
    spec = read(path)
    engine._expect_fields(
        spec, "experiment spec", {"schema_version", "prompt", "dataset", "runner"}
    )
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("expected experiment schema_version 1")
    prompt = spec["prompt"]
    engine._expect_fields(prompt, "prompt", {"id", "path"})
    prompt_path = resolve(prompt["path"], path.parent)
    prompt = {
        "id": engine._expect_identifier(prompt["id"], "prompt.id"),
        "text": prompt_path.read_bytes().decode(),
        "source_path": str(prompt_path),
    }
    dataset = spec["dataset"]
    engine._expect_fields(
        dataset,
        "dataset",
        {"adapter", "path"} | ({"select", "mask_format"} & dataset.keys()),
    )
    source_path = resolve(dataset["path"], path.parent)
    cases, sources = inputs.prepare_file(dataset, source_path, prompt["text"])
    runner = dict(spec["runner"])
    runner["runner_binary"] = str(
        engine._resolve_executable(
            runner.get("runner_binary", str(engine.DEFAULT_RUNNER)),
            "runner_binary",
            path.parent,
        )
    )
    runner["auth_file"] = (
        str(resolve(runner["auth_file"], path.parent))
        if runner.get("auth_file")
        else None
    )
    return {
        "prompt": prompt,
        "dataset": {k: v for k, v in dataset.items() if k != "path"},
        "cases": cases,
        "runner": runner,
        "sources": {
            **sources,
            str(path): engine._sha256_file(path),
            str(prompt_path): engine._sha256_file(prompt_path),
        },
    }


def request_preview(plan, manifest, cases):
    pending = [case for case in cases if case.get("status", "unrun") == "unrun"]
    reusable = 0
    if pending and not manifest["request_reuse"]["intentional_repeat"]:
        history = engine.RequestHistory(
            Path(manifest["request_reuse"]["history_root"]),
            exclude_run=Path(plan["run_directory"]),
        )
        for case in pending:
            for _, source in history.matches(
                engine._prompt_request_key(manifest, case["prompt"])
            ):
                try:
                    inputs.validate(
                        plan["dataset"],
                        case,
                        source["final_output_raw"],
                        plan["runner"].get("output_schema"),
                    )
                except (ValueError, engine.RunnerError):
                    continue
                reusable += 1
                break
    unrun = len(pending)
    return {
        "unrun": unrun,
        "reusable": reusable,
        "new": unrun - reusable,
        "note": "lookup at inspection time; run rechecks verified receipts",
    }


def prepare(args):
    destination = args.destination.expanduser().resolve()
    if destination.exists():
        raise ValueError("experiment destination already exists")
    inherited_history = None
    if args.from_experiment:
        old, _, old_manifest = load(args.from_experiment)
        inherited_history = old_manifest.get("request_reuse", {}).get("history_root")
        setup = {k: old[k] for k in ("prompt", "dataset", "cases", "runner", "sources")}
        baseline = report(Path(args.from_experiment).resolve())
    else:
        setup = spec_setup(args.spec)
        baseline = report(args.baseline.resolve()) if args.baseline else None
    if args.only:
        requested = set(args.only)
        unknown = requested - {c["id"] for c in setup["cases"]}
        if unknown:
            raise ValueError(f"unknown --only case IDs: {', '.join(sorted(unknown))}")
        setup["cases"] = [c for c in setup["cases"] if c["id"] in requested]
        if baseline is not None:
            baseline = {**baseline, "cases": [c for c in baseline["cases"] if c["id"] in requested]}
    # Job IDs from historical batches are not the candidate's stable case IDs.
    setup["cases"] = [
        {k: v for k, v in c.items() if k != "job_id"} for c in setup["cases"]
    ]
    overrides = {
        k: getattr(args, k)
        for k in (
            "model",
            "reasoning_effort",
            "provider",
            "concurrency",
            "max_output_tokens",
        )
        if getattr(args, k) is not None
    }
    setup["runner"] = {**setup["runner"], **overrides}
    if args.prompt:
        if not args.prompt_id:
            raise ValueError("--prompt requires --prompt-id")
        path = args.prompt.expanduser().resolve()
        setup["prompt"] = {
            "id": args.prompt_id,
            "text": path.read_bytes().decode(),
            "source_path": str(path),
        }
        setup["sources"] = {**setup["sources"], str(path): engine._sha256_file(path)}
        setup["cases"] = [
            {**c, "prompt": inputs.render(setup["prompt"]["text"], c["inputs"])}
            for c in setup["cases"]
        ]
    elif args.prompt_id:
        raise ValueError("--prompt-id requires --prompt")
    if args.import_config and (
        args.from_experiment or args.baseline or args.prompt or args.repeat or args.only or overrides
    ):
        raise ValueError(
            "--import-config requires an exact spec, without baseline, prompt override, repeat or --only"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".experiment-prepare-", dir=destination.parent
    ) as temporary:
        staged = Path(temporary)
        # Preserve the immediate baseline, not an ever-growing chain of old comparisons.
        snapshot = (
            None
            if baseline is None
            else {
                "experiment": baseline["experiment"],
                "prompt_id": baseline["prompt_id"],
                "cases": [
                    {k: v for k, v in c.items() if k not in {"baseline", "reviews"}}
                    for c in baseline["cases"]
                ],
            }
        )
        plan = {
            "schema_version": 1,
            **setup,
            "imported": bool(args.import_config),
            "baseline": snapshot,
            "baseline_prompt_id": baseline["prompt_id"] if baseline else None,
        }
        config_value = {
            "schema_version": 1,
            **setup["runner"],
            "run_directory": str(destination / "run"),
            "prompts": [
                {"prompt_id": c["id"], "text": c["prompt"]} for c in setup["cases"]
            ],
        }
        if args.import_config:
            config, manifest, cases = import_setup(args.import_config, setup)
            config_value["run_directory"] = str(config.run_directory)
            config_value["prompts"] = [
                {"prompt_id": p.prompt_id, "text": p.text} for p in config.prompts
            ]
            plan["cases"] = cases
        write(staged / "runner-config.json", config_value)
        config = engine.PromptRunnerConfig.load(staged / "runner-config.json")
        if not args.import_config:
            manifest = engine._build_prompt_manifest(
                config, engine._runner_version(config)
            )
            manifest["config_path"] = str(destination / "runner-config.json")
            engine._request_history_options(
                config,
                manifest,
                repeat=args.repeat,
                history_root=args.history_root
                or (
                    Path(inherited_history) if inherited_history else destination.parent
                ),
            )
            (staged / "run").mkdir()
            engine._atomic_write(
                staged / "run" / "manifest.json", engine._canonical_json_bytes(manifest)
            )
        plan["run_directory"] = str(config.run_directory)
        plan["manifest_sha256"] = inputs.digest(manifest)
        plan["files"] = {
            "runner-config.json": engine._sha256_file(staged / "runner-config.json")
        }
        plan["code"] = {
            p.name: engine._sha256_file(p)
            for p in (
                Path(__file__),
                Path(inputs.__file__),
                Path(inputs.grouped_masks.__file__),
                Path(engine.__file__),
                Path(__file__).with_name("mask_positions.py"),
            )
        }
        plan["requests_at_prepare"] = (
            request_preview(plan, manifest, plan["cases"])
            if not args.import_config
            else None
        )
        write(staged / "experiment.json", {"sha256": inputs.digest(plan), "plan": plan})
        # Every artifact in this directory is generated, never reusable source.
        (staged / ".gitignore").write_text("*\n")
        # Reserve the destination exclusively; never replace someone else's experiment.
        destination.mkdir()
        for child in staged.iterdir():
            child.rename(destination / child.name)
    result = report(destination)
    write(destination / "report.json", result)
    return result


def import_setup(path, setup):
    """Import only a demonstrated template→inputs→saved-prompt mapping, never guess."""
    path = path.expanduser().resolve()
    value = read(path)
    if "prompts" in value:
        config = engine.PromptRunnerConfig.load(path)
    else:
        config, _, _ = engine._load_mask_batch(path)
    manifest = read(config.run_directory / "manifest.json")
    saved_prompts = {p["prompt_id"]: p["text"] for p in manifest["prompts"]}
    if saved_prompts != {p.prompt_id: p.text for p in config.prompts}:
        raise ValueError("legacy config does not match saved manifest prompts")
    for name in (
        "model",
        "reasoning_effort",
        "provider",
        "max_output_tokens",
        "timeout_seconds",
    ):
        expected = setup["runner"].get(name, {"timeout_seconds": 600}.get(name))
        if expected != getattr(config, name) or expected != manifest.get(name):
            raise ValueError(f"legacy setting mismatch: {name}")
    if setup["runner"].get(
        "output_schema"
    ) != config.output_schema or config.output_schema != manifest.get(
        "response_schema"
    ):
        raise ValueError("legacy schema mismatch")
    by_prompt = {}
    for prompt in config.prompts:
        by_prompt.setdefault(prompt.text, []).append(prompt.prompt_id)
    cases = []
    for case in setup["cases"]:
        matches = by_prompt.get(case["prompt"], [])
        if case["id"] in matches:
            identifier = case["id"]
        elif len(matches) == 1:
            identifier = matches[0]
        else:
            raise ValueError(
                f"cannot verify unique saved input mapping for {case['id']}"
            )
        cases.append({**case, "job_id": identifier})
    if len({c["job_id"] for c in cases}) != len(config.prompts) or len(cases) != len(
        config.prompts
    ):
        raise ValueError("spec must account for every saved prompt exactly once")
    manifest_hash = inputs.digest(manifest)
    provenance = engine._load_runner_upgrades(
        config.run_directory,
        manifest_sha256=manifest_hash,
        initial_wrapper_sha256=manifest["wrapper_sha256"],
    )
    latest = engine._load_latest_results(
        config.run_directory / "results.jsonl", manifest_hash, provenance
    )
    for job in config.prompts:
        record = latest.get("prompt:" + job.prompt_id)
        if record and record["status"] == "succeeded":
            engine.validate_prompt_receipt(
                replace(config, prompts=(job,)), manifest, record
            )
    return config, manifest, cases


def report(directory):
    directory = Path(directory).resolve()
    files = engine.ReceiptFiles()
    plan, config, manifest = load(directory)
    manifest_hash = inputs.digest(manifest)
    provenance = engine._load_runner_upgrades(
        config.run_directory,
        manifest_sha256=manifest_hash,
        initial_wrapper_sha256=manifest["wrapper_sha256"],
    )
    ledger = config.run_directory / "results.jsonl"
    latest = engine._load_latest_results(ledger, manifest_hash, provenance)
    records = (
        [json.loads(line) for line in ledger.read_bytes().splitlines()]
        if ledger.exists()
        else []
    )
    reconciled_costs = engine.load_reconciled_costs(config.run_directory, records)
    reviews_path = directory / "reviews.jsonl"
    comments_path = directory / "ui-comments.json"
    comments = (
        inputs.prominence_comments(read(comments_path))
        if plan["dataset"]["adapter"] in {"prominence", "generic"} and comments_path.exists()
        else {}
    )
    reviews = (
        [json.loads(line) for line in reviews_path.read_bytes().splitlines()]
        if reviews_path.exists()
        else []
    )
    ui_path = directory / "review-ui.json"
    if ui_path.exists():
        for binding in read(ui_path):
            session_path = directory / binding["session_path"]
            if session_path.exists():
                reviews.extend(
                    inputs.ui_reviews(
                        binding,
                        read(directory / binding["batch_path"]),
                        read(session_path),
                    )
                )
    baseline = (
        {c["id"]: c for c in plan["baseline"]["cases"]} if plan["baseline"] else {}
    )
    cases, comparisons = [], Counter()
    for case in plan["cases"]:
        job = engine.PromptJob(case.get("job_id", case["id"]), case["prompt"])
        record = latest.get("prompt:" + job.prompt_id)
        row = {**case, "status": "unrun", "output": None, "baseline": None}
        if record:
            row["receipt"] = {
                "results_path": str(ledger),
                "record_sha256": inputs.digest(record),
            }
            row["reused"] = record.get("execution") == "cross_run_reuse"
            if record["status"] == "failed":
                row.update(
                    status="failed",
                    error=record.get("error"),
                    failure_kind=engine.prompt_failure_kind(record),
                    output=record.get("final_output_raw"),
                )
            else:
                row["output"] = record.get("final_output_raw")
                try:
                    engine.validate_prompt_receipt(
                        replace(config, prompts=(job,)), manifest, record, files=files
                    )
                except engine.RunnerError as error:
                    row.update(status="invalid_receipt", error=str(error))
                else:
                    try:
                        row.update(
                            inputs.validate(
                                plan["dataset"],
                                case,
                                record["final_output_raw"],
                                config.output_schema,
                            )
                        )
                    except (ValueError, engine.RunnerError) as error:
                        row.update(status="malformed", error=str(error))
        prior = baseline.get(case["id"])
        if prior is None:
            row["comparison"] = "missing_baseline"
        elif prior["inputs"] != case["inputs"]:
            row["comparison"] = "input_mismatch"
        else:
            row["baseline"] = {
                k: v
                for k, v in prior.items()
                if k not in {"baseline", "reviews", "evidence"}
            }
            if prior["status"] not in {"valid", "empty"} or row["status"] not in {
                "valid",
                "empty",
            }:
                row["comparison"] = "not_comparable"
            else:
                row["comparison"] = (
                    "unchanged" if row["output"] == prior["output"] else "changed"
                )
        row["reviews"] = [
            {
                **r,
                "current": r["input_sha256"] == case["input_sha256"]
                and r["output_sha256"] == inputs.digest(row["output"]),
            }
            for r in reviews
            if r["case_id"] == case["id"]
        ]
        row["reviews"].extend(
            {"case_id": case["id"], "role": "user", "verdict": "comment",
             "comment": comment["comment"], "source": comments_path.name,
             "current": key == inputs.prominence_comment_key(row)}
            for key, comment in comments.items()
            if comment["note_id"] == case["id"] and comment["comment"]
        )
        comparisons[row["comparison"]] += 1
        cases.append(row)
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "attempts_without_usage": 0,
        "catalog_cost_estimate_usd": 0,
        "attempts_without_cost_estimate": 0,
        "provider_reported_cost_usd": 0,
        "attempts_without_provider_cost": 0,
    }
    attempts = [r for r in records if r.get("execution") != "cross_run_reuse"]
    for record in attempts:
        charge = engine.provider_cost(record, reconciled_costs)
        if type(charge) in (int, float) and math.isfinite(charge) and charge >= 0:
            usage["provider_reported_cost_usd"] += charge
        else:
            usage["attempts_without_provider_cost"] += 1
        saved = record.get("usage")
        if not isinstance(saved, dict):
            usage["attempts_without_usage"] += 1
            usage["attempts_without_cost_estimate"] += 1
            continue
        for field, sdk, legacy in (
            ("input_tokens", "input", "input_tokens"),
            ("cached_input_tokens", "cacheRead", "cached_input_tokens"),
            ("cache_write_tokens", "cacheWrite", "cache_write_tokens"),
            ("output_tokens", "output", "output_tokens"),
            ("reasoning_tokens", "reasoning", "reasoning_output_tokens"),
        ):
            usage[field] += saved.get(sdk, saved.get(legacy, 0)) or 0
        estimate = (saved.get("cost") or {}).get("total")
        if estimate is None:
            usage["attempts_without_cost_estimate"] += 1
        else:
            usage["catalog_cost_estimate_usd"] += estimate
    if usage["attempts_without_cost_estimate"]:
        usage["catalog_cost_estimate_usd"] = None
    if usage["attempts_without_provider_cost"]:
        usage["provider_reported_cost_usd"] = None
    summary = {
        s: sum(c["status"] == s for c in cases)
        for s in ("valid", "empty", "malformed", "invalid_receipt", "failed", "unrun")
    }
    summary.update(
        cases=len(cases),
        attempts=len(attempts),
        reused=sum(c.get("reused", False) for c in cases),
    )
    result = {
        "experiment": str(directory),
        "prompt_id": plan["prompt"]["id"],
        "settings": {
            **plan["runner"],
            "timeout_seconds": config.timeout_seconds,
            "max_output_tokens": config.max_output_tokens,
            "concurrency": config.concurrency,
        },
        "imported": plan["imported"],
        "adapter": plan["dataset"]["adapter"],
        "summary": summary,
        "usage": usage,
        "comparison": dict(comparisons),
        "cases": cases,
        "baseline_only": sorted(set(baseline) - {c["id"] for c in cases}),
    }
    result["requests"] = (
        request_preview(plan, manifest, cases) if not plan["imported"] else None
    )
    if result["adapter"] == "masks":
        result["posts"] = len({c["evidence"]["note_id"] for c in cases})
    return result


def execution_upgrade(directory, plan, reason):
    """Audit an explicitly approved code transition without rewriting frozen inputs."""
    active = plan["code"]
    current = {name: engine._sha256_file(Path(__file__).with_name(name)) for name in active}
    path = directory / "code-upgrades.jsonl"
    results_path = Path(plan["run_directory"]) / "results.jsonl"
    results = results_path.read_bytes() if results_path.exists() else b""
    for line in path.read_bytes().splitlines() if path.exists() else []:
        entry = json.loads(line)
        if (entry["from"] != active or set(entry["to"]) != set(active)
                or entry["results_prefix_bytes"] > len(results)
                or entry["results_prefix_bytes"] < 0
                or engine._sha256_bytes(results[:entry["results_prefix_bytes"]]) != entry["results_prefix_sha256"]):
            raise ValueError("invalid execution code upgrade history")
        active = entry["to"]
    if current != active:
        if not reason or not reason.strip():
            raise ValueError("experiment code changed; inspect it and supply --runner-upgrade-reason, or prepare a new experiment")
        engine._append_json_line(path, {
            "from": active, "to": current, "reason": reason,
            "results_prefix_bytes": len(results),
            "results_prefix_sha256": engine._sha256_bytes(results),
        })


def reconcile_costs(directory):
    """Read missing OpenRouter charges; never rewrite original model receipts."""
    directory = Path(directory).resolve()
    with locked(directory):
        plan, config, manifest = load(directory)
        if config.provider != 'openrouter' or plan['imported']:
            raise ValueError('cost lookup requires a native OpenRouter experiment')
        report(directory)  # Verify saved experiment and receipt provenance first.
        path = config.run_directory / 'results.jsonl'
        records = [json.loads(line) for line in path.read_bytes().splitlines()] if path.exists() else []
        costs = engine.load_reconciled_costs(config.run_directory, records)
        pending = [r for r in records if r.get('execution') != 'cross_run_reuse'
                   and engine.provider_cost(r, costs) is None
                   and (r.get('model_result') or {}).get('response_metadata', {}).get('id')]
        if pending:
            ids = list(dict.fromkeys(r['model_result']['response_metadata']['id'] for r in pending))
            node = shutil.which('node')
            argv = ([node] if node else ['nix', 'shell', 'nixpkgs#nodejs_24', '--command', 'node'])
            argv += [str(Path(__file__).with_name('frontier_runner') / 'billing.mjs')]
            result = subprocess.run(argv, input=json.dumps(ids), text=True, capture_output=True,
                                    timeout=60 + 35 * len(ids))
            if result.returncode:
                raise ValueError('cost lookup failed; original reserves retained')
            rows = json.loads(result.stdout)
            if not isinstance(rows, list) or len(rows) != len(ids):
                raise ValueError('invalid cost lookup response')
            by_id = {r.get('id'): r for r in rows}
            if set(by_id) != set(ids):
                raise ValueError('cost lookup generation IDs differ')
            for row in rows:
                if 'error' not in row:
                    cost = row.get('total_cost')
                    if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                        raise ValueError('invalid cost lookup charge')
            for record in pending:
                row = by_id[record['model_result']['response_metadata']['id']]
                if 'error' in row:
                    continue  # Missing bills remain explicitly unknown.
                engine._append_json_line(config.run_directory / 'cost-receipts.jsonl', {
                    'source': 'openrouter/generation', 'record_sha256': inputs.digest(record),
                    'generation': row, 'looked_up_at_utc': datetime.now(timezone.utc).isoformat(),
                })
        return report(directory)


def run(directory, max_new_attempts=None, runner_upgrade_reason=None, *,
        max_cost_usd=None, max_request_cost_usd=None):
    directory = directory.resolve()
    with locked(directory):
        plan, config, manifest = load(directory)
        if plan["imported"]:
            raise ValueError(
                "imported experiments are read-only; prepare --from this experiment to run a candidate"
            )
        identity = engine._runner_identity(config)
        if any(identity[k] != manifest[k] for k in ("runner_version", "runner_sha256")):
            raise ValueError("model runner changed since preparation")
        engine._validate_auth_file(config.auth_file)
        execution_upgrade(directory, plan, runner_upgrade_reason)
        provenance = engine._load_runner_upgrades(
            config.run_directory, manifest_sha256=inputs.digest(manifest),
            initial_wrapper_sha256=manifest["wrapper_sha256"],
        )
        wrapper_changed = provenance.active_wrapper_sha256 != engine._sha256_file(Path(engine.__file__))
        error = None
        cases = {c["id"]: c for c in plan["cases"]}

        def validate_output(job, raw):
            inputs.validate(
                plan["dataset"], cases[job.prompt_id], raw, config.output_schema
            )

        try:
            engine._execute_prompt_batch(
                config,
                manifest,
                retry_failed=False,
                concurrency=config.concurrency,
                validate_output=validate_output,
                max_new_attempts=max_new_attempts,
                max_cost_usd=max_cost_usd,
                max_request_cost_usd=max_request_cost_usd,
                runner_upgrade_reason=runner_upgrade_reason if wrapper_changed else None,
            )
        except engine.RunnerError as caught:
            error = caught
        finally:
            result = report(directory)
            write(directory / "report.json", result)
        if error:
            raise engine.RunnerError(
                f"{error}; partial results: {directory / 'report.json'}"
            ) from error
        return result


def review(args):
    directory = args.experiment.resolve()
    if args.cosine_comparison and not args.ui:
        raise ValueError("--cosine-comparison requires --ui")
    if args.flagged_only and not args.ui:
        raise ValueError("--flagged-only requires --ui")
    if args.only and not args.ui:
        raise ValueError("--only requires --ui")
    if (args.view or args.node or args.ordering or args.check) and not args.ui:
        raise ValueError("--view/--node/--ordering/--check require --ui")
    if args.ordering and not args.cosine_comparison:
        raise ValueError("--ordering requires --cosine-comparison")
    with locked(directory):
        result = report(directory)
        if args.ui:
            if any((args.case, args.role, args.verdict, args.comment)):
                raise ValueError("--ui cannot record a CLI judgment")
            plan, _, _ = load(directory)
            prominence_view = args.view == "prominence" or plan["dataset"]["adapter"] == "prominence"
            if (args.node or args.check) and not prominence_view:
                raise ValueError("--node/--check require the prominence view")
            if args.node:
                available = {c.get("evidence", {}).get("node_id") for c in result["cases"]}
                unknown = set(args.node) - available
                if unknown:
                    raise ValueError(f"unknown --node IDs: {', '.join(sorted(unknown))}")
                result = {**result, "cases": [c for c in result["cases"]
                          if c.get("evidence", {}).get("node_id") in args.node]}
            selected = None
            if args.flagged_only or args.only:
                if not prominence_view and plan["dataset"]["adapter"] not in {"titles", "masks"}:
                    raise ValueError("--flagged-only/--only support titles, masks and prominence")
                requested = set(args.only or [])
                unknown = requested - {c["id"] for c in result["cases"]}
                if unknown:
                    raise ValueError(f"unknown --only case IDs: {', '.join(sorted(unknown))}")
                selected = [
                    c["id"] for c in result["cases"]
                    if (not requested or c["id"] in requested)
                    and (not args.flagged_only or inputs.is_flagged(c))
                ]
                if not selected:
                    print("No flagged cases. No model calls or review decisions changed.")
                    return
                if prominence_view or plan["dataset"]["adapter"] == "titles":
                    result = {**result, "cases": [c for c in result["cases"] if c["id"] in selected]}
            batch, excluded = inputs.review_batch(plan, result, view=args.view)
            if args.cosine_comparison:
                if not prominence_view:
                    raise ValueError("--cosine-comparison requires prominence cases")
                try:
                    from .prominence_ranking import add_rankings
                except ImportError:
                    from prominence_ranking import add_rankings
                batch = add_rankings(batch, result, read(args.cosine_comparison))
                if args.ordering:
                    if args.ordering not in {order["name"] for order in batch["orderings"]}:
                        raise ValueError(f"unknown ordering: {args.ordering}")
                    batch["orderings"].sort(key=lambda order: order["name"] != args.ordering)
            if prominence_view:
                # Comments are separate from approval sessions and model outputs.
                batch_path = directory / ("ui-" + inputs.digest(batch)[:16] + ".json")
                write(batch_path, batch)
                binary = (
                    args.ui_binary
                    or Path(__file__).resolve().parents[1]
                    / "target/release/model-output-review"
                )
                print(
                    f"UI: {len(batch['notes'])} mask entries; c: comment. No model calls or implied decisions."
                )
                viewer_options = (["--check"] if args.check else
                                  ["--comments", str(directory / "ui-comments.json")])
                completed = subprocess.run(
                    [str(binary), str(batch_path), *viewer_options],
                    check=False,
                )
                if completed.returncode:
                    raise ValueError(f"review UI exited with {completed.returncode}")
                write(directory / "report.json", report(directory))
                return
            print(
                f"UI: {len(selected) if selected is not None else len(batch['items'])} cases; "
                f"{len(excluded)} not supported by this UI (still in show/report.json)."
            )
            for item in excluded:
                print(f"  {item['id']}: {item['reason']}")
            if not batch["items"]:
                raise ValueError(
                    "no compatible UI cases; use show --case and review --case"
                )
            # A content-addressed session cannot misapply old decisions to changed outputs.
            name = "ui-" + inputs.digest(batch)[:16]
            batch_path = directory / (name + ".json")
            write(batch_path, batch)
            ui_path = directory / "review-ui.json"
            bindings = read(ui_path) if ui_path.exists() else []
            session_name = name + "-session.json"
            if not any(b["session_path"] == session_name for b in bindings):
                included = {item["item_id"] for item in batch["items"]}
                bindings.append(
                    {
                        "batch_path": batch_path.name,
                        "batch_sha256": inputs.digest(batch),
                        "session_path": session_name,
                        "cases": {
                            c["id"]: {
                                "input_sha256": c["input_sha256"],
                                "output_sha256": inputs.digest(c["output"]),
                            }
                            for c in result["cases"]
                            if c["id"] in included
                        },
                    }
                )
                write(ui_path, bindings)
            binary = (
                args.ui_binary
                or Path(__file__).resolve().parents[1]
                / "target/release/sse-mask-review"
            )
            command = (
                "review-titles"
                if plan["dataset"]["adapter"] == "titles"
                else "review-masks"
            )
            completed = subprocess.run(
                [
                    str(binary),
                    command,
                    str(batch_path),
                    str(directory / (name + "-session.json")),
                    *(["--only", ",".join(selected)]
                      if selected is not None and plan["dataset"]["adapter"] == "masks" else []),
                ],
                check=False,
            )
            if completed.returncode:
                raise ValueError(f"review UI exited with {completed.returncode}")
            write(directory / "report.json", report(directory))
            return
        if not all((args.case, args.role, args.verdict, args.comment)):
            raise ValueError(
                "recording review requires --case, --role agent|user, --verdict and --comment"
            )
        case = next((c for c in result["cases"] if c["id"] == args.case), None)
        if case is None:
            raise ValueError("unknown case")
        engine._append_json_line(
            directory / "reviews.jsonl",
            {
                "case_id": args.case,
                "role": args.role,
                "verdict": args.verdict,
                "comment": args.comment,
                "time": datetime.now(timezone.utc).isoformat(),
                "input_sha256": case["input_sha256"],
                "output_sha256": inputs.digest(case["output"]),
            },
        )
        write(directory / "report.json", report(directory))
        print(f"Recorded {args.role} review for {args.case}. Model calls made: 0")


def compact(result, *, prepared=False):
    print(f"{'Prepared' if prepared else 'Experiment'}: {result['experiment']}")
    print(f"Prompt: {result['prompt_id']}")
    settings = result["settings"]
    print(
        f"Model: {settings['provider']} / {settings['model']}; reasoning: {settings['reasoning_effort']}"
    )
    available = sum(
        c["baseline"] is not None and c["baseline"]["status"] in {"valid", "empty"}
        for c in result["cases"]
    )
    print(f"Saved baseline results available: {available}/{len(result['cases'])}")
    if result["adapter"] == "masks":
        print(f"Posts: {result['posts']}; subjects/calls: {result['summary']['cases']}")
    print("Cases: " + ", ".join(f"{k}={v}" for k, v in result["summary"].items()))
    print("Comparison (text changes, not quality): " + json.dumps(result["comparison"]))
    if result["baseline_only"]:
        print(
            "Baseline-only cases (not in this experiment): "
            + ", ".join(result["baseline_only"])
        )
    if result["requests"]:
        print(
            f"Requests remaining: {result['requests']['new']} new, {result['requests']['reusable']} reusable"
        )
    if prepared:
        print("Model calls made: 0")
    else:
        print(
            "Usage (new attempts only; reasoning already included in output): "
            + json.dumps(result["usage"])
        )
    for case in result["cases"]:
        print(f"  {case['id']}: {case['status']}; {case['comparison']}")
    action = "show" if result["imported"] or not result["summary"]["unrun"] else "run"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        action,
        result["experiment"],
    ]
    if action == "show":
        command += ["--case", result["cases"][0]["id"]]
    print("Next: " + shlex.join(command))
    if action == "run":
        print(
            "Inference requires user authorization; preparation is not authorization."
        )


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    p = commands.add_parser(
        "prepare", help="freeze inputs/settings and baseline; no inference"
    )
    p.add_argument("destination", type=Path)
    start = p.add_mutually_exclusive_group(required=True)
    start.add_argument("--spec", type=Path)
    start.add_argument("--from", dest="from_experiment", type=Path)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--only", action="append", metavar="CASE_ID",
                   help="prepare only this case (repeat for several); preserves exact inputs and matching baseline")
    p.add_argument("--prompt", type=Path)
    p.add_argument("--prompt-id")
    p.add_argument("--repeat", action="store_true")
    p.add_argument("--history-root", type=Path)
    p.add_argument("--model")
    p.add_argument("--reasoning-effort")
    p.add_argument("--provider", choices=("openai-codex", "openrouter"))
    p.add_argument("--concurrency", type=int)
    p.add_argument("--max-output-tokens", type=int)
    p.add_argument(
        "--import-config",
        type=Path,
        help="verify/import a historical batch without running it",
    )
    p = commands.add_parser(
        "run",
        help="execute a prepared experiment; retry only temporary provider errors",
    )
    p.add_argument("experiment", type=Path)
    p.add_argument("--max-new-attempts", type=int,
                   help="cap newly sent attempts, including provider retries; reserve spending for this allowance")
    p.add_argument("--max-cost-usd", type=float,
                   help="cumulative experiment spending allowance; includes prior attempts, never truncates responses")
    p.add_argument("--max-request-cost-usd", type=float,
                   help="caller-verified maximum cost reserved for each in-flight call; required with --max-cost-usd")
    p.add_argument("--runner-upgrade-reason", help="explicitly approve and audit a workflow-code upgrade; frozen inputs/settings remain immutable")
    p = commands.add_parser('reconcile-costs', help='lookup missing OpenRouter charges; no inference')
    p.add_argument('experiment', type=Path)
    p = commands.add_parser(
        "show", help="inspect all cases, or exact case evidence; no inference"
    )
    p.add_argument("experiment", type=Path)
    p.add_argument("--case")
    p.add_argument("--json", action="store_true")
    p = commands.add_parser(
        "revise",
        help="create a version from exact edits and print its full diff",
        description='No model calls. Edits JSON: {"edits":[{"old":"exact original text","new":"replacement"}]}. '
        "Optional base_sha256 pins the original; otherwise it is computed. "
        "Matches must be unique and nonoverlapping. Original bytes are preserved; "
        "destinations cannot exist. Prints only the full-context diff to stdout.",
    )
    p.add_argument("base", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--edits", required=True, help="JSON file or - for stdin")
    p = commands.add_parser(
        "review", help="record attributed judgments or open an existing task UI"
    )
    p.add_argument("experiment", type=Path)
    p.add_argument("--case")
    p.add_argument("--role", choices=("agent", "user"))
    p.add_argument("--verdict", choices=("accept", "reject", "uncertain"))
    p.add_argument("--comment")
    p.add_argument("--ui", action="store_true")
    p.add_argument("--view", choices=("prominence",),
                   help="render saved generic prominence diagnostics in the existing mask viewer")
    p.add_argument("--node", action="append", metavar="NODE_ID",
                   help="prominence UI: show all masks of this node; repeat for several")
    p.add_argument("--ordering", help="start in a named saved cosine-comparison ordering")
    p.add_argument("--check", action="store_true",
                   help="validate the prominence UI batch without opening a terminal")
    p.add_argument("--flagged-only", action="store_true",
                   help="title/mask/prominence UI: current reject/uncertain reviews and unresolved failures")
    p.add_argument("--only", action="append", metavar="CASE_ID",
                   help="title/mask/prominence UI: show this case (repeat for several); intersects --flagged-only")
    p.add_argument("--ui-binary", type=Path)
    p.add_argument("--cosine-comparison", type=Path,
                   help="saved prominence_cosine/centroid comparison; adds offline ranking orders")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            if args.from_experiment and args.baseline:
                raise ValueError("--from already specifies the baseline")
            compact(prepare(args), prepared=True)
        elif args.command == "run":
            if args.max_new_attempts is not None and args.max_new_attempts < 1:
                raise ValueError("--max-new-attempts must be positive")
            if args.runner_upgrade_reason is not None and not args.runner_upgrade_reason.strip():
                raise ValueError("--runner-upgrade-reason must not be blank")
            result = run(args.experiment, args.max_new_attempts, args.runner_upgrade_reason,
                         max_cost_usd=args.max_cost_usd, max_request_cost_usd=args.max_request_cost_usd)
            compact(result)
            return int(
                any(
                    result["summary"][s]
                    for s in ("malformed", "invalid_receipt", "failed", "unrun")
                )
            )
        elif args.command == 'reconcile-costs':
            compact(reconcile_costs(args.experiment))
        elif args.command == "show":
            result = report(args.experiment)
            if args.case:
                case = next((c for c in result["cases"] if c["id"] == args.case), None)
                if case is None:
                    raise ValueError("unknown case")
                result = {"settings": result["settings"], **case}
            if args.json or args.case:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                compact(result)
        elif args.command == "revise":
            try:
                request = (
                    json.load(sys.stdin) if args.edits == "-" else read(args.edits)
                )
            except (ValueError, UnicodeError) as error:
                raise ValueError(f"could not read edits JSON: {error}") from error
            # The CLI computes the base hash; a supplied hash is still enforced.
            if "base_sha256" not in request:
                request["base_sha256"] = engine._sha256_file(args.base)
            sys.stdout.write(engine.revise_prompt(args.base, args.destination, request))
            print(
                f"Created {args.destination}; provenance: {args.destination}.revision.json",
                file=sys.stderr,
            )
        else:
            review(args)
        return 0
    except (ValueError, KeyError, TypeError, OSError, engine.RunnerError) as error:
        print(f"Experiment failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
