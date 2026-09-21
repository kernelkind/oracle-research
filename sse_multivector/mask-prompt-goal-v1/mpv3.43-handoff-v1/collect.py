"""Collect this handoff, accounting for zero-new-usage reused receipts explicitly.

The older collector requires reasoning/totalTokens on reused records, whose
documented zero-new-usage representation has only four counters. Keep all old
code, prepared inputs and raw receipts unchanged; reuse validation and decoding.
"""
import dataclasses
import hashlib
import json
from pathlib import Path
import study as handoff

ROOT, read, save, study = handoff.ROOT, handoff.read, handoff.save, handoff.study
for path, expected in read(ROOT / "input-hashes.json").items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
cases = {c["id"]: c for c in read(ROOT / "cases.json")}
records = [json.loads(line) for line in (ROOT / "run/results.jsonl").read_text().splitlines()]
assert len(records) == len({r["note_id"] for r in records}) == len(cases)
by_id = {r["note_id"]: r for r in records}
config = study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
manifest = read(ROOT / "run/manifest.json")
rows = []
for prompt in config.prompts:
    record, case = by_id[prompt.prompt_id], cases[prompt.prompt_id]
    study.pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
    assert record["status"] == "succeeded" and record["attempt"] == 1
    original = (study.pipeline._read_request_source(record["reused_from"], record["request_sha256"])
                if record.get("execution") == "cross_run_reuse" else record)
    response, ranges = study.decode_response(record["final_output_raw"], case["text"])
    inline = case["text"]
    for span in reversed(ranges):
        inline = inline[:span["start"]] + "⟦" + inline[span["start"]:span["end"]] + "⟧" + inline[span["end"]:]
    rows.append({"id": case["id"], "subject": case["subject"], "subject_entry": case["subject_entry"],
                 "format_valid": True, "decode_error": None, "ranges": ranges,
                 "fragments": [case["text"][s["start"]:s["end"]] for s in ranges], "inline_mask": inline,
                 "raw": record["final_output_raw"], "diagnostics": {k: response[k] for k in ("meaning", "expressible", "evidence")},
                 **{k: record[k] for k in ("request_sha256", "wrapper_sha256", "usage")},
                 "runner_sha256": original["runner_sha256"],
                 "execution": record.get("execution") or "new_call", "reused_from": record.get("reused_from"),
                 "receipt_path": str(ROOT / "run/results.jsonl"), "baseline": []})


def summarize(receipts):
    fresh = [r for r in receipts if r.get("execution") != "cross_run_reuse"]
    reused = [r for r in receipts if r.get("execution") == "cross_run_reuse"]
    assert all(r["usage"] == {"cacheRead": 0, "cacheWrite": 0, "input": 0, "output": 0} for r in reused)
    # Missing usage on real calls raises rather than being assumed zero.
    usage = {key: sum(r["usage"][key] for r in fresh) for key in
             ("input", "output", "reasoning", "cacheRead", "cacheWrite", "totalTokens")}
    return {"entries": len(receipts), "new_calls": len(fresh), "reused": len(reused), "usage": usage}


summary = {**summarize(records), "cases": len(rows), "format_valid": len(rows),
           "empty_entries": sum(not r["ranges"] for r in rows)}
save(ROOT / "comparison.json", {"version": read(ROOT / "plan.json")["version"], "summary": summary,
                                "results": rows, "semantic_assessment": "Separate; mechanical validity is not semantic approval."})
subject_records = [json.loads(line) for line in (ROOT / "subject-run/results.jsonl").read_text().splitlines()]
save(ROOT / "execution-summary.json", {"subjects": summarize(subject_records), "masks": summary,
                                       "combined": summarize(subject_records + records),
                                       "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                       "collector_note": __doc__})
print(json.dumps(read(ROOT / "execution-summary.json")))
