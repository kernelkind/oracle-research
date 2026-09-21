"""One-call PPv10 probe: the saved MPv3.43 Astra mask H15, scored by Muse 1.3 high.

Offline prepare and collect only; inference runs through the canonical saved
batch runner. No new mask calls: the mask comes from the frozen probe receipt.
"""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PROBE = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.43-probe-v1"
CASE_ID = "H15"
EXPERIMENT = "PPv10-mpv3.43-muse13high-v1"
MODEL = "meta/muse-spark-1.3-contributor"
REASONING = "high"
PROMPT = REPO / "sse_multivector/prominence-prompt-goal-v1/ppv10-draft-v1/PPv10.md"
PROMPT_SHA256 = "d40835fb0b104865727c0b0a2bde4074afb642991d9bddc424d5379ef4b038ea"

sys.path.insert(0, str(REPO / "sse_multivector"))
import extraction_pipeline as pipeline

sys.path.insert(0, str(REPO / "sse_multivector/prominence-prompt-goal-v1/ppv10-ranking-v1"))
import study as ranking


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def position_decoder():
    path = REPO / "sse_multivector/mask_positions.py"
    spec = importlib.util.spec_from_file_location("mask_positions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def saved_mask_receipt():
    for line in (PROBE / "run/results.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record["job_key"] == "prompt:" + CASE_ID:
            return record
    raise ValueError("saved MPv3.43 mask receipt missing for " + CASE_ID)


def prepared_case():
    case = next(c for c in read(PROBE / "cases.json") if c["id"] == CASE_ID)
    mask_decoder, decoder_path = position_decoder()
    receipt = saved_mask_receipt()
    _, ranges = mask_decoder.decode(receipt["final_output_raw"], case["text"])
    spans = [(r["start"], r["end"]) for r in ranges]
    if not spans:
        raise ValueError("saved mask is empty; nothing to score")
    data = ranking.render_input(case["text"], spans)
    return case, data, spans, receipt, decoder_path


def prepare():
    if digest(PROMPT) != PROMPT_SHA256:
        raise ValueError("PPv10 hash mismatch")
    template = PROMPT.read_text()
    if template.count("{INPUT_JSON}") != 1:
        raise ValueError("expected one input placeholder")
    case, data, spans, receipt, decoder_path = prepared_case()
    prompt = [{"prompt_id": CASE_ID, "text": template.replace(
        "{INPUT_JSON}", json.dumps(data, ensure_ascii=False, indent=2))}]
    plan = {
        "experiment": EXPERIMENT, "case": CASE_ID,
        "scope": "One PPv10 call on Muse 1.3 high using the frozen MPv3.43 Astra-low"
                 " mask for probe case H15. No new mask or subject calls, no prompt"
                 " changes, no semantic expectations predeclared beyond a valid score.",
        "prompt_path": str(PROMPT), "prompt_sha256": PROMPT_SHA256,
        "mask_provenance": {"directory": str(PROBE), "job_key": receipt["job_key"],
                            "request_sha256": receipt["request_sha256"]},
        "provider": "openrouter", "model": MODEL, "reasoning_effort": REASONING,
    }
    config = {
        "schema_version": 1, "runner_binary": str(REPO / "sse_multivector/run-model.sh"),
        "provider": "openrouter", "auth_file": None, "run_directory": "run",
        "model": MODEL, "reasoning_effort": REASONING, "timeout_seconds": 900,
        "prompts": prompt,
    }
    save(ROOT / "plan.json", plan)
    save(ROOT / "inputs.json", {"id": CASE_ID, "note_id": case["note_id"],
                                "subject": case["subject"], "text": case["text"],
                                "character_spans": spans, "input": data,
                                "mask_request_sha256": receipt["request_sha256"]})
    save(ROOT / "config.json", config)
    save(ROOT / "preview-request.json", {"provider": "openrouter", "model": MODEL,
                                         "reasoning": REASONING, "prompt": prompt[0]["text"]})
    paths = [PROMPT, PROBE / "cases.json", PROBE / "run/results.jsonl",
             decoder_path, ROOT / "plan.json", ROOT / "inputs.json", ROOT / "config.json"]
    save(ROOT / "input-hashes.json", {str(p): digest(p) for p in paths})
    pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(json.dumps({"prepared": 1, "model_calls": 0, "fragments": data["mask"]}))


def collect():
    for path, expected in read(ROOT / "input-hashes.json").items():
        if digest(Path(path)) != expected:
            raise ValueError("pinned input changed: " + path)
    inputs = read(ROOT / "inputs.json")
    config = pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in
               (config.run_directory / "results.jsonl").read_text().splitlines()]
    if len(records) != 1 or records[0].get("job_key") != "prompt:" + CASE_ID:
        raise ValueError("expected exactly one saved attempt")
    record = records[0]
    pipeline.validate_prompt_receipt(
        dataclasses.replace(config, prompts=(config.prompts[0],)), manifest, record)
    score, error = None, record.get("error")
    if record["status"] == "succeeded":
        try:
            score = ranking.decode_score(record["final_output_raw"])
        except ValueError as failure:
            error = str(failure)
    else:
        error = error or record["status"]
    usage = record.get("usage")
    results = {"experiment": EXPERIMENT, "case": CASE_ID, "subject": inputs["subject"],
               "fragments": inputs["input"]["mask"], "model": MODEL,
               "reasoning_effort": REASONING, "prompt_sha256": PROMPT_SHA256,
               "score": score, "error": error, "raw": record["final_output_raw"],
               "request_sha256": record["request_sha256"], "usage": usage,
               "mask_request_sha256": inputs["mask_request_sha256"]}
    save(ROOT / "results.json", results)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
