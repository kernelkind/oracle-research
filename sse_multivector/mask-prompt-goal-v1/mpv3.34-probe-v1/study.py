"""Offline diagnostic-prompt preparation/collection; existing runner does inference."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "prior_study", ROOT.parent / "mpv3.32-vs-mpv3.33-v1/study.py"
)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
read, save, selection, pipeline = prior.read, prior.save, prior.selection, prior.pipeline


def decode_response(raw, source):
    response = json.loads(raw, object_pairs_hook=selection.unique_object)
    if not isinstance(response, dict) or set(response) != {"meaning", "expressible", "evidence", "mask"}:
        raise ValueError("expected meaning, expressible, evidence and mask fields")
    for field in ("meaning", "evidence"):
        if not isinstance(response[field], str) or not response[field].strip():
            raise ValueError(f"{field} must be a nonempty string")
    if type(response["expressible"]) is not bool:
        raise ValueError("expressible must be boolean")
    ranges = selection.decode(json.dumps({"mask": response["mask"]}), source)
    if response["expressible"] != bool(ranges):
        raise ValueError("expressible verdict contradicts empty/nonempty mask")
    return response, ranges


def prepare():
    plan = read(ROOT / "plan.json")
    baseline = ROOT / plan["baseline_directory"]
    cases = read(baseline / "cases.json")
    assert [case["id"] for case in cases] == plan["case_ids"]
    template_path = ROOT.parent / "mpv3.34-draft-v1/mask-prompt.md"
    template = template_path.read_text()
    assert hashlib.sha256(template_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    for placeholder in ("{POST}", "{INDEXED_POST}", "{SUBJECT}"):
        assert template.count(placeholder) == 1
    config = read(baseline / "mpv3.33-config.json")
    config.update(run_directory="run", prompts=[], output_schema=read(
        ROOT.parent / "mpv3.34-draft-v1/output-schema.json"
    ))
    for field in ("model", "reasoning_effort", "provider", "auth_file"):
        assert config[field] == plan[field]
    for case in cases:
        assert hashlib.sha256(case["text"].encode()).hexdigest() == case["source_text_sha256"]
        values = {"POST": case["text"], "INDEXED_POST": selection.index_post(case["text"]),
                  "SUBJECT": case["subject"]}
        rendered = re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda m: values[m[1]], template)
        config["prompts"].append({"prompt_id": case["id"], "text": rendered})
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", config)
    evidence_paths = [baseline / name for name in (
        "plan.json", "cases.json", "comparison.json", "assessment.json"
    )] + [template_path, ROOT.parent / "mpv3.34-draft-v1/output-schema.json"]
    save(ROOT / "input-hashes.json", {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence_paths
    })
    pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} prompts; no model calls.")


def collect():
    plan, cases = read(ROOT / "plan.json"), read(ROOT / "cases.json")
    for path, expected in read(ROOT / "input-hashes.json").items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    by_id = {case["id"]: case for case in cases}
    config = pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    records_by_id = {record["note_id"]: record for record in records}
    assert len(records) == len(records_by_id) == len(cases)
    totals = {key: 0 for key in ("input", "output", "reasoning", "cacheRead", "cacheWrite", "totalTokens")}
    baseline = read(ROOT / plan["baseline_directory"] / "comparison.json")
    rows = []
    for prompt in config.prompts:
        record, case = records_by_id[prompt.prompt_id], by_id[prompt.prompt_id]
        pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
        assert record["attempt"] == 1
        raw = record["final_output_raw"]
        response, ranges, error = None, None, record.get("error")
        if record["status"] == "succeeded":
            try:
                response, ranges = decode_response(raw, case["text"])
            except (ValueError, TypeError) as failure:
                error = str(failure)
        elif not error:
            error = "runner status: " + record["status"]
        fragments = None if ranges is None else [case["text"][s["start"]:s["end"]] for s in ranges]
        inline = None if ranges is None else case["text"]
        for span in reversed(ranges or []):
            inline = inline[:span["start"]] + "⟦" + inline[span["start"]:span["end"]] + "⟧" + inline[span["end"]:]
        usage = record.get("usage")
        assert isinstance(usage, dict), "Missing usage must not be treated as zero"
        for key in totals:
            totals[key] += usage[key]
        previous = [row for row in baseline["results"] if row["id"] == case["id"]]
        rows.append({"id": case["id"], "subject": case["subject"], "raw": raw,
                     "diagnostics": None if response is None else {k: response[k] for k in ("meaning", "expressible", "evidence")},
                     "format_valid": error is None, "decode_error": error, "ranges": ranges,
                     "fragments": fragments, "inline_mask": inline, "baseline": previous,
                     "receipt_path": str(config.run_directory / "results.jsonl"),
                     "request_sha256": record["request_sha256"],
                     "runner_sha256": record["runner_sha256"], "wrapper_sha256": record["wrapper_sha256"],
                     "execution": record.get("execution", "new_call"), "usage": usage})
    summary = {"cases": len(rows), "format_valid": sum(row["format_valid"] for row in rows),
               "new_calls": sum(row["execution"] != "cross_run_reuse" for row in rows),
               "reused": sum(row["execution"] == "cross_run_reuse" for row in rows), "usage": totals}
    save(ROOT / "comparison.json", {"version": plan["version"], "summary": summary, "results": rows,
                                    "semantic_assessment": "Separate; diagnostics and mechanical validity are not semantic approval."})
    print(json.dumps(summary))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
