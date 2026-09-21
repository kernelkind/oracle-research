"""Offline PPv10 input preparation and receipt collection; no model execution."""
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "sse_multivector"))
import extraction_pipeline as pipeline


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def character_spans(text, byte_spans):
    source = text.encode("utf-8")
    result = []
    for start, end in byte_spans:
        if not 0 <= start < end <= len(source):
            raise ValueError("invalid byte span")
        left = len(source[:start].decode("utf-8"))
        right = left + len(source[start:end].decode("utf-8"))
        result.append((left, right))
    return result


def render_input(text, spans):
    if not spans or "⟦" in text or "⟧" in text:
        raise ValueError("empty mask or source collides with mask markers")
    fragments, parts, cursor = [], [], 0
    for start, end in spans:
        if not 0 <= cursor <= start < end <= len(text):
            raise ValueError("invalid, overlapping, or unsorted span")
        fragment = text[start:end]
        fragments.append(fragment)
        parts.extend((text[cursor:start], "⟦", fragment, "⟧"))
        cursor = end
    parts.append(text[cursor:])
    return {"mask": fragments, "marked_post": "".join(parts)}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode_score(raw):
    value = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != {"prominence"}:
        raise ValueError("expected exactly one prominence field")
    score = value["prominence"]
    if type(score) is not int or not 0 <= score <= 100:
        raise ValueError("prominence must be an integer from 0 through 100")
    return score


def load_case(case):
    document = read(REPO / case["source"])
    if case["format"] == "corpus":
        matches = [(note, subject) for note in document["notes"]
                   for subject in note["subjects"] if subject["id"] == case["source_id"]]
        if len(matches) != 1:
            raise ValueError("source ID must be unique")
        note, item = matches[0]
        text, note_id = note["text"], note["note_id"]
        spans = character_spans(text, item["byte_spans"])
    elif case["format"] == "assessment":
        matches = [item for item in document.get("items", document.get("results", []))
                   if item["id"] == case["source_id"]]
        if len(matches) != 1:
            raise ValueError("source ID must be unique")
        item = matches[0]
        if not item["format_valid"]:
            raise ValueError("source mask is invalid")
        text = item.get("source_text", item.get("text"))
        note_id = item["note_id"]
        spans = [(s["start"], s["end"]) for s in item.get("decoded_ranges", item.get("ranges"))]
    else:
        raise ValueError("unsupported saved source format")
    data = render_input(text, spans)
    if data["mask"] != item["fragments"]:
        raise ValueError("saved spans and saved fragments disagree")
    if "inline_mask" in item and data["marked_post"] != item["inline_mask"]:
        raise ValueError("saved inline mask and reconstructed selections disagree")
    if data["marked_post"].replace("⟦", "").replace("⟧", "") != text:
        raise ValueError("renderer altered source text")
    return dict(case, note_id=note_id, text=text, character_spans=spans, input=data)


def prepare():
    plan = read(ROOT / "plan.json")
    prompt_path = (ROOT / plan["prompt_path"]).resolve()
    if digest(prompt_path) != plan["prompt_sha256"]:
        raise ValueError("PPv10 hash mismatch")
    template = prompt_path.read_text()
    if template.count("{INPUT_JSON}") != 1:
        raise ValueError("expected one input placeholder")
    cases = [load_case(case) for case in plan["cases"]]
    prompts = [{"prompt_id": case["id"], "text": template.replace(
        "{INPUT_JSON}", json.dumps(case["input"], ensure_ascii=False, indent=2))} for case in cases]
    config = {
        "schema_version": 1, "runner_binary": str(REPO / "sse_multivector/run-model.sh"),
        "provider": plan["provider"], "auth_file": None, "run_directory": "run",
        "model": plan["model"], "reasoning_effort": plan["reasoning_effort"], "prompts": prompts,
    }
    save(ROOT / "inputs.json", cases)
    save(ROOT / "config.json", config)
    save(ROOT / "preview-request.json", {
        "provider": config["provider"], "model": config["model"],
        "reasoning": config["reasoning_effort"], "prompt": prompts[0]["text"],
    })
    paths = {REPO / case["source"] for case in cases}
    paths.update((prompt_path, ROOT / "plan.json", ROOT / "inputs.json", ROOT / "config.json"))
    save(ROOT / "input-hashes.json", {str(p): digest(p) for p in sorted(paths)})
    pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(json.dumps({"prepared": len(cases), "model_calls": 0,
                      "all_saved_fragments_and_occurrences_verified": True}))


def collect():
    for path, expected in read(ROOT / "input-hashes.json").items():
        if digest(Path(path)) != expected:
            raise ValueError("pinned input changed: " + path)
    plan = read(ROOT / "plan.json")
    cases = {case["id"]: case for case in read(ROOT / "inputs.json")}
    config = pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    if len(records) != len(cases) or len({r["note_id"] for r in records}) != len(cases):
        raise ValueError("expected exactly one saved attempt per case")
    by_id = {r["note_id"]: r for r in records}
    results = []
    for prompt in config.prompts:
        record = by_id[prompt.prompt_id]
        pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
        score, error = None, record.get("error")
        if record["status"] == "succeeded":
            try:
                score = decode_score(record["final_output_raw"])
            except ValueError as failure:
                error = str(failure)
        else:
            error = error or record["status"]
        results.append({"id": prompt.prompt_id, "label": cases[prompt.prompt_id]["label"],
                        "score": score, "error": error, "raw": record["final_output_raw"],
                        "request_sha256": record["request_sha256"], "usage": record.get("usage"),
                        "execution": record.get("execution", "new_call")})
    scores = {r["id"]: r["score"] for r in results}
    comparisons = []
    for comparison in plan["comparisons"]:
        high, low = scores[comparison["higher"]], scores[comparison["lower"]]
        outcome = "unscorable" if high is None or low is None else (
            "expected_order" if high > low else "tie" if high == low else "reversal")
        comparisons.append(dict(comparison, higher_score=high, lower_score=low, outcome=outcome))
    totals = {key: sum(r["usage"][key] for r in results)
              for key in ("input", "output", "reasoning", "cacheRead", "cacheWrite", "totalTokens")
              if all(isinstance(r["usage"], dict) and key in r["usage"] for r in results)}
    summary = {"experiment": plan["experiment"], "prompt_sha256": plan["prompt_sha256"],
               "model": plan["model"], "reasoning_effort": plan["reasoning_effort"],
               "cases": len(results), "valid_scores": sum(r["score"] is not None for r in results),
               "new_calls": sum(r["execution"] != "cross_run_reuse" for r in results),
               "usage": totals, "results": results, "comparisons": comparisons,
               "limitations": plan["limitations"]}
    save(ROOT / "results.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
