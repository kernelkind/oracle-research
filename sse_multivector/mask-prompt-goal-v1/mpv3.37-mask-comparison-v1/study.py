"""Offline comparison preparation and receipt collection; existing runner sends calls."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
import extraction_pipeline as pipeline

spec = importlib.util.spec_from_file_location("selection", ROOT.parent / "position-selection-v6/selection.py")
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        assert path.read_text() == content, f"Refusing to overwrite {path}"
    else:
        with path.open("x") as handle:
            handle.write(content)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline(source, ranges):
    assert "⟦" not in source and "⟧" not in source
    previous = 0
    for span in ranges:
        assert previous <= span["start"] < span["end"] <= len(source)
        previous = span["end"]
    result = source
    for span in reversed(ranges):
        start, end = span["start"], span["end"]
        result = result[:start] + "⟦" + result[start:end] + "⟧" + result[end:]
    assert result.replace("⟦", "").replace("⟧", "") == source
    return result


def replace_fragments(source, ranges, replacements):
    result, used = [], set()
    for span in ranges:
        fragment = source[span["start"]:span["end"]]
        if fragment not in replacements:
            result.append(span)
            continue
        used.add(fragment)
        for piece in replacements[fragment]:
            assert piece and fragment.count(piece) == 1
            start = span["start"] + fragment.index(piece)
            result.append({"start": start, "end": start + len(piece)})
    assert used == replacements.keys()
    inline(source, result)
    return result


def prepare():
    plan = read(ROOT / "plan.json")
    baseline = ROOT / plan["baseline"]
    prompt = ROOT.parent / "mpv3.37-draft-v1/mask-prompt.md"
    assert sha(prompt) == plan["baseline_prompt_sha256"]
    template = (ROOT / "comparison-prompt.md").read_text()
    assert all(template.count("{" + key + "}") == 1 for key in ("SUBJECT", "A", "B"))
    cases = {case["id"]: case for case in read(baseline / "cases.json")}
    rows = {row["id"]: row for row in read(baseline / "comparison.json")["results"]}
    comparisons = []
    for identifier, replacements in plan["corrections"].items():
        case, row = cases[identifier], rows[identifier]
        source = case["text"]
        assert hashlib.sha256(source.encode()).hexdigest() == case["source_text_sha256"]
        assert case["subject"] == row["subject"]
        decoded = selection.decode(json.dumps({"mask": json.loads(row["raw"])["mask"]}), source)
        assert decoded == row["ranges"]
        original = {"ranges": decoded, "inline": inline(source, decoded)}
        assert original["inline"] == row["inline_mask"]
        corrected_ranges = replace_fragments(source, decoded, replacements)
        corrected = {"ranges": corrected_ranges, "inline": inline(source, corrected_ranges)}
        common = {"case_id": identifier, "subject": case["subject"], "note_id": case["note_id"], "source_text": source}
        comparisons.append({**common, "comparison_id": identifier, "kind": "excess_wording", "expected": "corrected",
                            "candidates": {"original": original, "corrected": corrected}})
        if identifier in plan["controls"]:
            remove = plan["controls"][identifier]["remove"]
            shorter_ranges = replace_fragments(source, corrected_ranges, {remove: []})
            shorter = {"ranges": shorter_ranges, "inline": inline(source, shorter_ranges)}
            comparisons.append({**common, "comparison_id": identifier + "-required-detail", "kind": "required_detail",
                                "expected": "corrected", "candidates": {"shortened": shorter, "corrected": corrected}})
    jobs, prompts = [], []
    for comparison in comparisons:
        names = list(comparison["candidates"])
        for order in (names, names[::-1]):
            job_id = comparison["comparison_id"] + ("-AB" if order == names else "-BA")
            labels = dict(zip(("A", "B"), order))
            values = {key: comparison["candidates"][name]["inline"] for key, name in labels.items()}
            values["SUBJECT"] = comparison["subject"]
            rendered = re.sub(r"\{(SUBJECT|A|B)\}", lambda match: values[match[1]], template)
            prompts.append({"prompt_id": job_id, "text": rendered})
            jobs.append({"id": job_id, "comparison_id": comparison["comparison_id"], "kind": comparison["kind"],
                         "labels": labels, "expected": next(label for label, name in labels.items() if name == comparison["expected"])})
    assert len(prompts) == len({item["text"] for item in prompts}) == plan["calls"]
    schema = {"type": "object", "properties": {"explanation": {"type": "string", "minLength": 1},
              "choice": {"type": "string", "enum": ["A", "B", "both", "neither", "uncertain"]}},
              "required": ["explanation", "choice"], "additionalProperties": False}
    config = {"schema_version": 1, "runner_binary": str(ROOT.parents[1] / "run-model.sh"), "auth_file": None,
              "run_directory": "run", "timeout_seconds": 300, "output_schema": schema, "prompts": prompts,
              **{key: plan[key] for key in ("provider", "model", "reasoning_effort")}}
    save(ROOT / "cases.json", {"comparisons": comparisons, "jobs": jobs})
    save(ROOT / "config.json", config)
    evidence = [ROOT / name for name in ("plan.json", "comparison-prompt.md", "study.py", "cases.json", "config.json")]
    evidence += [prompt, baseline / "cases.json", baseline / "comparison.json"]
    save(ROOT / "input-hashes.json", {str(path.resolve()): sha(path) for path in evidence})
    pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared and checked {len(comparisons)} comparisons, {len(jobs)} order-balanced prompts. No inference.")


def collect():
    for path, expected in read(ROOT / "input-hashes.json").items():
        assert sha(Path(path)) == expected, path
    config = pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    manifest = read(config.run_directory / "manifest.json")
    receipts = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    records = {record["note_id"]: record for record in receipts}
    jobs = {job["id"]: job for job in read(ROOT / "cases.json")["jobs"]}
    assert len(receipts) == len(records) == len(jobs) == len(config.prompts)
    results = []
    totals = dict.fromkeys(("input", "output", "reasoning", "cacheRead", "cacheWrite", "totalTokens"), 0)
    for prompt in config.prompts:
        record, job = records[prompt.prompt_id], jobs[prompt.prompt_id]
        pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
        assert record["attempt"] == 1
        output = json.loads(record["final_output_raw"]) if record["status"] == "succeeded" else None
        for key in totals:
            totals[key] += record["usage"][key]
        choice = None if output is None else output["choice"]
        results.append({**job, "output": output, "status": record["status"], "error": record.get("error"),
                        "selected": job["labels"].get(choice, choice), "agrees_with_predeclared_expectation": choice == job["expected"],
                        "request_sha256": record["request_sha256"], "execution": record.get("execution", "new_call")})
    summary = {"calls": len(results), "successful_responses": sum(row["status"] == "succeeded" for row in results),
               "new_calls": sum(row["execution"] != "cross_run_reuse" for row in results), "usage": totals}
    for kind in ("excess_wording", "required_detail"):
        subset = [row for row in results if row["kind"] == kind]
        summary[kind] = {"responses": len(subset), "agree": sum(row["agrees_with_predeclared_expectation"] for row in subset)}
    save(ROOT / "results.json", {"version": "MCv1", "summary": summary, "results": results,
                                "receipt_path": str(config.run_directory / "results.jsonl"),
                                "interpretation": "Automatic agreement counts only. Inspect explanations before drawing conclusions."})
    print(json.dumps(summary))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
