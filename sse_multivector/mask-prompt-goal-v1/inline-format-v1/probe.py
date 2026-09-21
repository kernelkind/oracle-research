"""Isolated output-format probe; production extraction code is unchanged."""

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SSE = HERE.parents[1]
sys.path.insert(0, str(SSE))
import extraction_pipeline as pipeline

BASE = HERE.parent / "mpv3.7-draft-v1/mask-prompt.md"
BASE_SHA256 = "9b62ef2cf699a1e14dec1bddb612ce67f6d66e8584686cc9bcc94082c49e2a17"
OLD_FORMAT = "Return only a JSON array of exact substrings copied from the post, in source order."
NEW_FORMAT = (
    "Return the complete original post, inserting ⟦ immediately before each mask fragment "
    "and ⟧ immediately after it. Preserve every original character, including whitespace, "
    "exactly. Add nothing else."
)


def parse_inline(source, response):
    """Return source ranges, rejecting alterations rather than repairing them."""
    if "⟦" in source or "⟧" in source:
        raise ValueError("source contains reserved mask delimiters")
    copied, ranges, start = [], [], None
    for character in response:
        if character == "⟦":
            if start is not None:
                raise ValueError("nested opening mask delimiter")
            start = len(copied)
        elif character == "⟧":
            if start is None:
                raise ValueError("unmatched closing mask delimiter")
            if start == len(copied):
                raise ValueError("empty mask fragment")
            ranges.append((start, len(copied)))
            start = None
        else:
            copied.append(character)
    if start is not None:
        raise ValueError("unclosed mask delimiter")
    if "".join(copied) != source:
        raise ValueError("removing mask delimiters does not reproduce the exact source")
    return [
        {
            "start": start,
            "end": end,
            "byte_start": len(source[:start].encode("utf-8")),
            "byte_end": len(source[:end].encode("utf-8")),
            "text": source[start:end],
        }
        for start, end in ranges
    ]


def read_json(path):
    return json.loads(path.read_text())


def write_new_json(path, value):
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare():
    original = BASE.read_bytes()
    if hashlib.sha256(original).hexdigest() != BASE_SHA256:
        raise ValueError("MPv3.7 baseline changed")
    template_path = HERE / "mask-prompt.md"
    print(pipeline.revise_prompt(BASE, template_path, {
        "base_sha256": BASE_SHA256,
        "edits": [{"old": OLD_FORMAT, "new": NEW_FORMAT}],
    }))
    template = template_path.read_text()
    if template.replace(NEW_FORMAT, OLD_FORMAT).encode() != original:
        raise ValueError("non-format instructions changed")
    cases = [
        {
            "id": "F01", "kind": "synthetic", "subject": "Trains",
            "note": "I train dogs every morning. The train arrived late. Another train leaves at noon.",
            "question": "Mark both train nouns, not the identical verb train.",
        },
        {
            "id": "F02", "kind": "synthetic", "subject": "Train delays",
            "note": "I train at the gym. My train arrived twenty minutes behind schedule. The next train was late too. I finished a detective novel today.",
            "question": "Cover both train-delay occurrences using multiple fragments; exclude training, the specific duration, and the novel.",
        },
        {
            "id": "F03", "kind": "synthetic", "subject": "Art",
            "note": "I started a new puzzle after lunch.\n\n#artblog #dailyart",
            "question": "Mark art inside both hashtags, not art inside started; exclude blog and daily.",
        },
        {
            "id": "F04", "kind": "synthetic", "subject": "Bicycles",
            "note": "🙂  My bicycle is blue.\r\n\tThe café sign says “open”; I wrote cafe\u0301 in my notebook.\r\n\r\nAnother bicycle waits outside.  ",
            "question": "Mark both bicycle occurrences; preserve emoji, combining accent, CRLF, tab, double spaces and trailing spaces exactly.",
        },
    ]
    previous = HERE.parent / "mpv3.7-reviewed-probe-v1"
    prior_analysis = read_json(previous / "analysis.json")
    prior_notes = {n["note_id"]: n for n in read_json(previous / "subjects-input.json")["notes"]}
    selected = [("F05", "M002"), ("F06", "M004"), ("F07", "M008"), ("F08", "M009")]
    for identifier, item_id in selected:
        item = next(i for i in prior_analysis["items"] if i["item_id"] == item_id)
        note = prior_notes[item["note_id"]]
        cases.append({
            "id": identifier, "kind": "saved-real-note", "subject": item["subject"],
            "note": note["text"], "note_id": note["note_id"],
            "question": item["question"], "baseline_item_id": item_id,
            "saved_mpv3_7_fragments": item["raw_fragments"],
            "baseline_run": str(previous),
        })
    # Expectations and previous answers are saved for assessment, never sent.
    for case in cases:
        parse_inline(case["note"], case["note"])
    write_new_json(HERE / "cases.json", cases)
    runtime = read_json(previous / "masks-config.json")
    config = {key: runtime[key] for key in (
        "schema_version", "runner_binary", "provider", "auth_file", "model", "reasoning_effort"
    )}
    config.update({
        "run_directory": "run", "timeout_seconds": 300,
        "prompts": [
            {"prompt_id": c["id"], "text": template.replace("{POST}", c["note"]).replace("{SUBJECT}", c["subject"])}
            for c in cases
        ],
    })
    write_new_json(HERE / "config.json", config)
    write_new_json(HERE / "plan.json", {
        "version": "MPv3.7-inline-format-v1", "baseline_sha256": BASE_SHA256,
        "prompt_sha256": hashlib.sha256(template.encode()).hexdigest(),
        "model": config["model"], "reasoning": config["reasoning_effort"],
        "calls": 8, "trials_per_case": 1, "concurrency": 4,
        "baseline_calls": 0, "automatic_retries": 0,
        "format_checks": ["balanced, nonempty, unnested markers", "exact source preservation including whitespace", "positions derived only from inline markers"],
        "semantic_check": "Manually assess each returned mask against its fixed subject; report independently of format validity.",
        "limitations": ["small development probe, not a reliability estimate", "no reruns of baseline or rejected responses", "delimiter collisions rejected before inference", "no production pipeline or frozen-prompt changes"],
    })


def run():
    # Reuse the saved-batch implementation and its cache, receipts and isolation.
    config = pipeline.PromptRunnerConfig.load(HERE / "config.json")
    manifest = pipeline._build_prompt_manifest(config, pipeline._runner_version(config))
    pipeline._request_history_options(config, manifest, repeat=False, history_root=SSE.parent)
    result = pipeline._execute_prompt_batch(config, manifest, retry_failed=False, concurrency=4)
    print(json.dumps({"completed": len(result["responses"])}))


def collect():
    config = pipeline.PromptRunnerConfig.load(HERE / "config.json")
    manifest = read_json(HERE / "run/manifest.json")
    records = [json.loads(line) for line in (HERE / "run/results.jsonl").read_text().splitlines()]
    jobs = {job.prompt_id: job for job in config.prompts}
    cases = read_json(HERE / "cases.json")
    totals, items = {}, []
    for case in cases:
        record = next(r for r in records if r["note_id"] == case["id"])
        pipeline.validate_prompt_receipt(replace(config, prompts=(jobs[case["id"]],)), manifest, record)
        raw = record["final_output_raw"]
        try:
            spans, error = parse_inline(case["note"], raw), None
        except ValueError as problem:
            spans, error = None, str(problem)
        items.append({
            **case, "raw_response": raw, "format_valid": error is None,
            "format_error": error, "ranges": spans,
            "semantic_assessment": None, "usage": record["usage"],
            "duration_seconds": record["elapsed_seconds"],
            "execution": record.get("execution", "new_call"),
        })
        for key in ("input", "output", "cacheRead", "cacheWrite", "totalTokens"):
            value = (record["usage"] or {}).get(key)
            if value is not None:
                totals[key] = totals.get(key, 0) + value
    result = {
        "version": "MPv3.7-inline-format-v1", "items": items,
        "format_valid_count": sum(i["format_valid"] for i in items),
        "count": len(items), "usage": totals,
        "semantic_assessment": "pending manual assessment; format validity is not semantic correctness",
    }
    write_new_json(HERE / "results.json", result)
    print(json.dumps({key: result[key] for key in ("count", "format_valid_count", "usage")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "run", "collect"])
    arguments = parser.parse_args()
    {"prepare": prepare, "run": run, "collect": collect}[arguments.action]()
