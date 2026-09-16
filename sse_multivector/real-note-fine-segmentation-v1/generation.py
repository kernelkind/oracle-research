#!/usr/bin/env python3
"""Prepare frozen per-call prompt jobs and collect their saved results; never execute them."""

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sse_multivector import extraction_pipeline as runner  # noqa: E402
from sse_multivector import generation_history as history  # noqa: E402


def sha(path):
    return history._sha256_file(Path(path))


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    with Path(path).open("xb") as destination:
        destination.write(runner._ordered_json_bytes(value))


def new_directory(path):
    if path.exists() or path.is_symlink():
        raise ValueError(
            f"output already exists: {path}; resume the saved runner jobs instead"
        )
    path.mkdir(parents=True, exist_ok=False)


def load_packages():
    subject_root = ROOT / "sse_multivector/subject-prompt-goal-v1/asv6.23"
    mask_root = ROOT / "sse_multivector/mask-prompt-goal-v1"
    subject = read(subject_root / "frozen.json")
    mask = read(mask_root / "frozen.json")
    paths = {
        subject_root
        / "frozen.json": "54f87aa49fbed73f401eba1bf7a5b792fec9d989d0371c35ee7dd96689534d01",
        mask_root
        / "frozen.json": "b16a4bb31c8fc6bcf824f625d298b00c65b6fe33a5fe007f99e760197e1a2d69",
        subject_root / subject["prompt"]["path"]: subject["prompt"]["sha256"],
        subject_root / subject["output_schema"]["path"]: subject["output_schema"][
            "file_sha256"
        ],
        mask_root / mask["prompt"]["path"]: mask["prompt"]["sha256"],
        ROOT / "sse_multivector/codex_exec.py": subject["input_processing"][
            "wrapper_sha256"
        ],
        (mask_root / mask["driver"]["path"]).resolve(): mask["driver"]["sha256"],
    }
    for path, expected in paths.items():
        if sha(path) != expected:
            raise ValueError(f"frozen package hash mismatch: {path}")
    subject_config = read(subject_root / subject["generation"]["example_config"])
    mask_config = read(mask_root / mask["runner"]["reference_config"])
    schema = read(subject_root / subject["output_schema"]["path"])
    if hashlib.sha256(runner._ordered_json_bytes(schema)).hexdigest() != subject[
        "output_schema"
    ]["ordered_transport_sha256"] or runner._ordered_json_bytes(
        schema
    ) != runner._ordered_json_bytes(subject_config["output_schema"]):
        raise ValueError("frozen ordered subject schema differs from reference config")
    for config, package in ((subject_config, subject), (mask_config, mask)):
        if (
            config["model"] != package["model"]
            or config["reasoning_effort"] != package["reasoning_effort"]
            or config["codex_binary"] != mask["runner"]["codex_binary"]
        ):
            raise ValueError("reference config differs from frozen model settings")
    if "output_schema" in mask_config or mask["runner"]["sha256"] != sha(
        ROOT / "sse_multivector/codex_exec.py"
    ):
        raise ValueError("mask reference runner contract differs from frozen package")
    return {
        "subject_root": subject_root,
        "mask_root": mask_root,
        "subject_prompt": (subject_root / subject["prompt"]["path"]).read_text(),
        "mask_prompt": (mask_root / mask["prompt"]["path"]).read_text(),
        "subjects": subject_config,
        "masks": mask_config,
        "codex_version": mask["runner"]["codex_version"],
        "driver": str((mask_root / mask["driver"]["path"]).resolve()),
        "files": {str(path.resolve()): expected for path, expected in paths.items()},
    }


def native_config(config, *, auth_file, runner_binary=runner.DEFAULT_RUNNER):
    """Keep the frozen model/prompt settings; select new execution explicitly."""
    if auth_file is None:
        raise ValueError("new generation requires an explicit auth_file")
    value = {
        key: item
        for key, item in config.items()
        if key not in {"codex_binary", "codex_home"}
    }
    value.update(
        provider="openai-codex",
        auth_file=str(Path(auth_file).expanduser().resolve()),
        runner_binary=str(Path(runner_binary).expanduser().resolve()),
    )
    return value


def receipt_engine(config_path):
    return runner if "runner_binary" in read(config_path) else history


def prompt_manifest(engine, config, saved, legacy_version):
    version = saved["runner_version"] if engine is runner else legacy_version
    return engine._build_prompt_manifest(config, version)


def add_usage(total, counts, *, native):
    for name, count in (counts or {}).items():
        if native and name == "cost":
            continue  # SDK catalog cost estimates are not incurred charges.
        if type(count) is not int or count < 0:
            raise ValueError("saved receipt has invalid usage")
        total[name] = total.get(name, 0) + count


def prepare(
    stage,
    input_path,
    output_path,
    *,
    auth_file,
    runner_binary=runner.DEFAULT_RUNNER,
    start=1,
    stop=None,
):
    if stage not in ("subjects", "masks"):
        raise ValueError("stage must be subjects or masks")
    output = Path(output_path).resolve()
    if output.exists() or output.is_symlink():
        raise ValueError(
            f"output already exists: {output}; resume the saved runner jobs instead"
        )
    packages = load_packages()
    source = Path(input_path).resolve()
    document = read(source)
    notes = document.get("notes")
    if document.get("schema_version") != 1 or not isinstance(notes, list) or not notes:
        raise ValueError("input must contain schema_version 1 and nonempty notes")
    stop = len(notes) if stop is None else stop
    if (
        type(start) is not int
        or type(stop) is not int
        or not 1 <= start <= stop <= len(notes)
    ):
        raise ValueError(
            "note range must be one-based, inclusive, and inside the input"
        )
    configs, calls, excluded, seen = [], [], [], set()
    for note_index in range(start - 1, stop):
        note = notes[note_index]
        note_id = runner._expect_sha256(note.get("note_id"), "note_id")
        text = runner._expect_string(note.get("text"), "note.text")
        if note_id in seen:
            raise ValueError("input repeats a selected note ID")
        seen.add(note_id)
        if stage == "subjects":
            selected = [(None, None)]
        else:
            selected = []
            for subject_index, subject in enumerate(note.get("subjects", [])):
                judgment = subject.get("judgment")
                if judgment not in ("accepted", "rejected", "unresolved"):
                    raise ValueError("mask input requires explicit subject judgments")
                if judgment == "accepted":
                    selected.append(
                        (
                            subject_index,
                            runner._expect_string(
                                subject.get("subject"), "fixed subject"
                            ),
                        )
                    )
                else:
                    excluded.append(
                        {
                            "note_index": note_index,
                            "subject_index": subject_index,
                            "judgment": judgment,
                        }
                    )
        for subject_index, fixed_subject in selected:
            call_id = (
                f"N{note_index + 1:03d}-AS"
                if stage == "subjects"
                else f"N{note_index + 1:03d}-S{subject_index + 1:03d}-MP"
            )
            config = native_config(
                copy.deepcopy(packages[stage]),
                auth_file=auth_file,
                runner_binary=runner_binary,
            )
            if stage == "subjects":
                prompt = runner._render_subject_prompt(
                    packages["subject_prompt"].strip(), runner.Note(note_id, text)
                )
            else:
                replacements = {"{POST}": text, "{SUBJECT}": fixed_subject}
                prompt = re.sub(
                    r"\{POST\}|\{SUBJECT\}",
                    lambda match: replacements[match.group()],
                    packages["mask_prompt"],
                )
            config.update(
                run_directory="run", prompts=[{"prompt_id": call_id, "text": prompt}]
            )
            configs.append((call_id, config))
            calls.append(
                {
                    "id": call_id,
                    "note_index": note_index,
                    "note_id": note_id,
                    "subject_index": subject_index,
                    "config": f"{call_id}/config.json",
                }
            )
    if not calls:
        raise ValueError("range contains no calls to prepare")
    new_directory(output)
    with (output / "input.json").open("xb") as destination:
        destination.write(source.read_bytes())
    jobs = []
    for call, (call_id, config) in zip(calls, configs, strict=True):
        directory = output / call_id
        directory.mkdir()
        path = directory / "config.json"
        write(path, config)
        runner.PromptRunnerConfig.load(path)
        call["config_sha256"] = sha(path)
        jobs.append(
            {
                "id": call_id,
                "unit": f"real-note-{output.name}-{call_id}",
                "cwd": str(directory),
                "command": [
                    str(Path(sys.executable).resolve()),
                    str(ROOT / "sse_multivector/extraction_pipeline.py"),
                    "prompt",
                    str(path),
                ],
            }
        )
    batches = []
    for index in range(0, len(jobs), 12):
        name = f"jobs-{index // 12 + 1:03d}.json"
        write(output / name, {"jobs": jobs[index : index + 12]})
        batches.append(name)
    manifest = {
        "schema_version": 1,
        "stage": stage,
        "transport": "pi-ai",
        "input_path": str(source),
        "input_sha256": sha(output / "input.json"),
        "note_range": [start, stop],
        "calls": calls,
        "excluded": excluded,
        "job_batches": batches,
        "frozen_files": packages["files"],
        "driver": packages["driver"],
    }
    write(output / "manifest.json", manifest)
    return manifest


def collect(prepared_path, output_path):
    prepared, output = Path(prepared_path).resolve(), Path(output_path).resolve()
    if output.exists() or output.is_symlink():
        raise ValueError(f"output already exists: {output}")
    packages = load_packages()
    manifest = read(prepared / "manifest.json")
    if manifest["frozen_files"] != packages["files"] or manifest["input_sha256"] != sha(
        prepared / "input.json"
    ):
        raise ValueError("prepared input or frozen package identity changed")
    document = read(prepared / "input.json")
    review_notes, usage, threads = {}, {}, set()
    for call in manifest["calls"]:
        config_path = prepared / call["config"]
        if sha(config_path) != call["config_sha256"]:
            raise ValueError("saved call config hash changed")
        engine = receipt_engine(config_path)
        config = engine.PromptRunnerConfig.load(config_path)
        note = review_notes.setdefault(
            call["note_index"], {**document["notes"][call["note_index"]], "outputs": []}
        )
        item = {
            "call_id": call["id"],
            "config_sha256": call["config_sha256"],
            "subject_index": call["subject_index"],
            "status": "not_run",
        }
        note["outputs"].append(item)
        run_manifest_path = config.run_directory / "manifest.json"
        if not run_manifest_path.exists():
            continue
        run_manifest = read(run_manifest_path)
        if run_manifest != prompt_manifest(
            engine, config, run_manifest, packages["codex_version"]
        ):
            raise ValueError(
                "saved runner manifest differs from exact frozen config/isolation"
            )
        manifest_sha = sha(run_manifest_path)
        wrapper = run_manifest["wrapper_sha256"]
        latest = engine._load_latest_results(
            config.run_directory / "results.jsonl",
            manifest_sha,
            engine.RunnerProvenance(wrapper, wrapper, ()),
        )
        receipt = latest.get("prompt:" + call["id"])
        if receipt is None:
            continue
        if engine is runner and receipt["status"] == "succeeded":
            runner.validate_prompt_receipt(config, run_manifest, receipt)
        raw = receipt.get("final_output_raw")
        thread = (
            receipt.get("model_result", {}).get("response_id")
            if engine is runner and receipt.get("model_result")
            else receipt.get("thread_id")
        )
        if thread is not None:
            if thread in threads:
                raise ValueError("saved calls repeat a thread ID")
            threads.add(thread)
        records = [
            json.loads(line)
            for line in (config.run_directory / "results.jsonl")
            .read_text()
            .splitlines()
        ]
        for record in records:
            add_usage(usage, record.get("usage"), native=engine is runner)
        item.update(
            status=receipt["status"],
            raw_response=raw,
            receipt=receipt,
            attempts=records,
            isolation=run_manifest["isolation"],
            run_manifest_sha256=manifest_sha,
            results_sha256=sha(config.run_directory / "results.jsonl"),
        )
        if raw is not None:
            if hashlib.sha256(raw.encode()).hexdigest() != receipt.get(
                "final_output_sha256"
            ):
                raise ValueError("saved raw response hash differs from receipt")
            try:
                item["parsed_response"] = json.loads(raw)
            except json.JSONDecodeError as error:
                item["parse_error"] = str(error)
    reviewed = {
        "schema_version": 1,
        "stage": manifest["stage"],
        "prepared_manifest_sha256": sha(prepared / "manifest.json"),
        "usage": usage,
        "notes": list(review_notes.values()),
    }
    new_directory(output)
    write(output / "review.json", reviewed)
    lines = [
        "Saved outputs for manual review. No semantic judgments have been added.",
        "",
    ]
    for note in reviewed["notes"]:
        lines.extend([note["note_id"], "COMPLETE ORIGINAL NOTE", note["text"], ""])
        for item in note["outputs"]:
            lines.extend(
                [
                    item["call_id"] + " — " + item["status"],
                    item.get("raw_response") or "No saved response.",
                    "",
                ]
            )
    with (output / "review.txt").open("x", encoding="utf-8") as destination:
        destination.write("\n".join(lines) + "\n")
    return reviewed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="stage", required=True)
    for stage in ("subjects", "masks"):
        command = commands.add_parser(stage)
        command.add_argument("input", type=Path)
        command.add_argument("output", type=Path)
        command.add_argument("--start", type=int, default=1)
        command.add_argument("--stop", type=int)
        command.add_argument("--auth-file", type=Path, required=True)
        command.add_argument(
            "--runner-binary", type=Path, default=runner.DEFAULT_RUNNER
        )
    command = commands.add_parser("collect")
    command.add_argument("prepared", type=Path)
    command.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.stage == "collect":
        result = collect(args.prepared, args.output)
        print(
            json.dumps({"note_count": len(result["notes"]), "usage": result["usage"]})
        )
    else:
        result = prepare(
            args.stage,
            args.input,
            args.output,
            start=args.start,
            stop=args.stop,
            auth_file=args.auth_file,
            runner_binary=args.runner_binary,
        )
        print(
            json.dumps(
                {
                    "call_count": len(result["calls"]),
                    "job_batches": result["job_batches"],
                    "driver": result["driver"],
                }
            )
        )


if __name__ == "__main__":
    main()
