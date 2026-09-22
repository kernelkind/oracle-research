"""MPv3.43 mask-call cost probe: one saved ASv6.48 subject set on two candidates.

Offline prepare and collect only; inference runs through the canonical saved
batch runner (`extraction_pipeline.py masks`). The probe measures per-call
usage, cache engagement and provider-reported cost at the production
mask-batch shape. It makes no semantic quality claims, calls no Astra model,
and changes no prompt.
"""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

sys.path.insert(0, str(REPO / "sse_multivector"))
import extraction_pipeline as pipeline

EXPERIMENT = "MPv3.43-cost-probe-v1"
PROMPT_VERSION = "MPv3.43"
PROMPT_STATUS = "frozen working baseline (not a production rollout)"

PROMPT = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md"
PROMPT_SHA256 = "75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03"
SCHEMA = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.34-draft-v1/output-schema.json"
SCHEMA_SHA256 = "accf073dd53239dc3ec70f0c458fb8287766f28b201e29f3e5d5cd3c37ca3fe9"
SUBJECTS = REPO / "sse_multivector/hierarchy-refresh-v1/subjects.json"
SUBJECTS_SHA256 = "60f0cce913554b6f424ec67b488d242fc934325444fbffc8123db903e2f70228"
MASKED = REPO / "sse_multivector/hierarchy-refresh-v1/masked-posts.json"
MASKED_SHA256 = "380e6eb4a2035ec714bd9a1304c77d35bbd5bff04f71e0a018082f1d465369f8"
DECODER = REPO / "sse_multivector/mask_positions.py"
DECODER_SHA256 = "690bc72e9a372562b35b2604d57c168440c3675915b1a229447f6d8bebe3dc8e"
PIPELINE_SHA256 = "f132d1febfe4c8323b34278a6d1b6518def0f12e4bc72f44c88ecfc8bcc71025"

NOTE_ID = "862486d8ab23753c39aa9484b1beb52b51e59369f91eb037f2898c5ed9b1f75e"
NOTE_LABEL = "N029 (hashtag post)"
SUBJECT_COUNT = 8

CANDIDATES = (
    {"name": "mimo-high", "model": "xiaomi/mimo-v2.6-pro", "reasoning_effort": "high"},
    {"name": "muse-high", "model": "meta/muse-spark-1.3-contributor",
     "reasoning_effort": "high"},
)
PROVIDER = "openrouter"
TIMEOUT_SECONDS = 1800
CONCURRENCY = 1


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def pinned_inputs():
    return {
        PROMPT: PROMPT_SHA256,
        SCHEMA: SCHEMA_SHA256,
        SUBJECTS: SUBJECTS_SHA256,
        MASKED: MASKED_SHA256,
        DECODER: DECODER_SHA256,
        REPO / "sse_multivector/extraction_pipeline.py": PIPELINE_SHA256,
    }


def check_pins():
    for path, expected in pinned_inputs().items():
        if digest(path) != expected:
            raise ValueError("pinned input changed: " + str(path))


def config_path(name):
    return ROOT / f"config-{name}.json"


def run_directory(name):
    return ROOT / f"run-{name}"


def decoder_module():
    spec = importlib.util.spec_from_file_location("mask_positions", DECODER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_note():
    notes = read(SUBJECTS)["notes"]
    matches = [note for note in notes if note["note_id"] == NOTE_ID]
    if len(matches) != 1:
        raise ValueError("expected exactly one saved subject set for the probe note")
    note = matches[0]
    if len(note["subjects"]) != SUBJECT_COUNT:
        raise ValueError("probe note subject count changed")
    return note


def saved_astra_masks():
    notes = read(MASKED)["notes"]
    matches = [note for note in notes if note["note_id"] == NOTE_ID]
    if len(matches) != 1:
        raise ValueError("expected exactly one saved Astra mask set for the probe note")
    return matches[0]


def prepare():
    check_pins()
    note = selected_note()
    astra = saved_astra_masks()
    cases = {
        "note_id": NOTE_ID,
        "note_label": NOTE_LABEL,
        "text": note["text"],
        "subjects": note["subjects"],
        "astra_reference": {
            "path": str(MASKED.relative_to(REPO)),
            "sha256": MASKED_SHA256,
            "saved_masks": [
                {"number": entry["number"], "subject": entry["subject"],
                 "byte_spans": entry["byte_spans"], "fragments": entry["fragments"]}
                for entry in astra["subjects"]
            ],
            "note": "Saved Astra MPv3.43 masks are reference evidence only. "
                    "No Astra call is made by this probe.",
        },
    }
    mask_input = {"schema_version": 1, "notes": [
        {"note_id": NOTE_ID, "text": note["text"], "subjects": note["subjects"]}]}
    save(ROOT / "cases.json", cases)
    save(ROOT / "mask-input.json", mask_input)
    rendered = {}
    for candidate in CANDIDATES:
        name = candidate["name"]
        config = {
            "schema_version": 1,
            "runner_binary": str(REPO / "sse_multivector/run-model.sh"),
            "provider": PROVIDER,
            "auth_file": None,
            "input_path": str(ROOT / "mask-input.json"),
            "prompt_path": str(PROMPT),
            "run_directory": str(run_directory(name)),
            "model": candidate["model"],
            "reasoning_effort": candidate["reasoning_effort"],
            "timeout_seconds": TIMEOUT_SECONDS,
            "concurrency": CONCURRENCY,
            "mask_format": "word_positions",
            "output_schema": read(SCHEMA),
        }
        save(config_path(name), config)
        loaded, metadata, _ = pipeline._load_mask_batch(config_path(name))
        if len(loaded.prompts) != SUBJECT_COUNT:
            raise ValueError("expected one rendered mask prompt per saved subject")
        rendered[name] = [job.text for job in loaded.prompts]
    if len({tuple(texts) for texts in rendered.values()}) != 1:
        raise ValueError("candidate requests must be byte-identical")
    plan = {
        "experiment": EXPERIMENT,
        "scope": "Cost/caching probe for teacher selection (SP + MP scope). Eight "
                 "fresh MPv3.43 mask calls per candidate over the complete saved "
                 "ASv6.48 subject set of one HRv1 note, rendered by the production "
                 "mask batch path (word_positions, shared MPv3.34 output schema). "
                 "Sequential calls at concurrency 1 to expose prefix-cache "
                 "engagement. No Astra calls, no prompt changes, no semantic "
                 "quality claims.",
        "prompt_version": PROMPT_VERSION,
        "prompt_status": PROMPT_STATUS,
        "prompt_path": str(PROMPT),
        "prompt_sha256": PROMPT_SHA256,
        "output_schema_path": str(SCHEMA),
        "output_schema_sha256": SCHEMA_SHA256,
        "note_id": NOTE_ID,
        "note_label": NOTE_LABEL,
        "subject_count": SUBJECT_COUNT,
        "subjects_sha256": SUBJECTS_SHA256,
        "candidates": list(CANDIDATES),
        "provider": PROVIDER,
        "timeout_seconds": TIMEOUT_SECONDS,
        "concurrency": CONCURRENCY,
        "output_token_cap": None,
        "fresh_sends": "extraction_pipeline.py masks ... --repeat",
    }
    save(ROOT / "plan.json", plan)
    evidence = [ROOT / name for name in (
        "study.py", "cases.json", "mask-input.json", "plan.json",
    )] + [config_path(c["name"]) for c in CANDIDATES] + list(pinned_inputs())
    save(ROOT / "input-hashes.json",
         {str(path): digest(path) for path in evidence})
    print(json.dumps({"prepared_calls": SUBJECT_COUNT * len(CANDIDATES),
                      "model_calls": 0, "candidates": [c["name"] for c in CANDIDATES]}))


def collect_one(candidate, note, decoder):
    name = candidate["name"]
    config, metadata, _ = pipeline._load_mask_batch(config_path(name))
    manifest = read(run_directory(name) / "manifest.json")
    records = [json.loads(line) for line in
               (run_directory(name) / "results.jsonl").read_text().splitlines()]
    if len(records) != SUBJECT_COUNT:
        raise ValueError(f"{name}: expected {SUBJECT_COUNT} saved attempts")
    by_id = {job.prompt_id: job for job in config.prompts}
    rows = []
    for record in records:
        item_id = record.get("job_key", "").removeprefix("prompt:")
        if record.get("execution") == "cross_run_reuse":
            raise ValueError(f"{name}:{item_id}: reused answer, not a fresh send")
        pipeline.validate_prompt_receipt(
            dataclasses.replace(config, prompts=(by_id[item_id],)), manifest, record)
        subject = next(entry for entry in metadata["items"]
                       if entry["item_id"] == item_id)
        row = {
            "item_id": item_id,
            "subject": subject["subject"],
            "status": record.get("status"),
            "error": record.get("error"),
            "elapsed_seconds": record.get("elapsed_seconds"),
            "usage": record.get("usage"),
        }
        if record.get("status") == "succeeded":
            response, ranges = decoder.decode(record["final_output_raw"], note["text"])
            row["diagnostics"] = {
                "meaning": response["meaning"],
                "expressible": response["expressible"],
                "evidence": response["evidence"],
            }
            row["fragment_count"] = len(ranges)
            row["empty_mask"] = not ranges
        rows.append(row)
    return {
        "model": candidate["model"],
        "reasoning_effort": candidate["reasoning_effort"],
        "calls": rows,
        "totals": usage_totals(rows),
    }


def usage_totals(rows):
    totals = {
        "attempts": len(rows),
        "succeeded": sum(1 for row in rows if row["status"] == "succeeded"),
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens_including_reasoning": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.0,
    }
    for row in rows:
        usage = row.get("usage") or {}
        totals["input_tokens"] += usage.get("input") or 0
        totals["cache_read_tokens"] += usage.get("cacheRead") or 0
        totals["cache_write_tokens"] += usage.get("cacheWrite") or 0
        totals["output_tokens_including_reasoning"] += usage.get("output") or 0
        totals["reasoning_tokens"] += usage.get("reasoning") or 0
        totals["cost_usd"] += ((usage.get("cost") or {}).get("total")) or 0
    seen = totals["input_tokens"] + totals["cache_read_tokens"]
    totals["cache_read_fraction_of_input"] = (
        totals["cache_read_tokens"] / seen if seen else None)
    totals["cost_usd_per_call"] = totals["cost_usd"] / len(rows) if rows else None
    return totals


def collect():
    check_pins()
    for path, expected in read(ROOT / "input-hashes.json").items():
        if digest(Path(path)) != expected:
            raise ValueError("pinned input changed: " + path)
    note = selected_note()
    decoder = decoder_module()
    if digest(DECODER) != DECODER_SHA256:
        raise ValueError("position decoder changed")
    candidates = {c["name"]: collect_one(c, note, decoder) for c in CANDIDATES}
    names = [c["name"] for c in CANDIDATES]
    prompt_hashes = [
        [row.get("prompt_sha256") for row in
         [json.loads(line) for line in
          (run_directory(name) / "results.jsonl").read_text().splitlines()]]
        for name in names
    ]
    if prompt_hashes[0] != prompt_hashes[1]:
        raise ValueError("candidate runs did not use identical rendered prompts")
    results = {
        "experiment": EXPERIMENT,
        "prompt_version": PROMPT_VERSION,
        "prompt_status": PROMPT_STATUS,
        "prompt_sha256": PROMPT_SHA256,
        "note_id": NOTE_ID,
        "note_label": NOTE_LABEL,
        "note_characters": len(note["text"]),
        "requests_byte_identical_across_candidates": True,
        "candidates": candidates,
    }
    save(ROOT / "results.json", results)
    summary = {name: {
        "cost_usd": value["totals"]["cost_usd"],
        "cost_usd_per_call": value["totals"]["cost_usd_per_call"],
        "cache_read_fraction_of_input": value["totals"]["cache_read_fraction_of_input"],
        "output_tokens_including_reasoning": (
            value["totals"]["output_tokens_including_reasoning"]),
        "reasoning_tokens": value["totals"]["reasoning_tokens"],
        "succeeded": value["totals"]["succeeded"],
    } for name, value in candidates.items()}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
