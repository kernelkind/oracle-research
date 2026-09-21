"""Offline preparation/collection only; inference uses extraction_pipeline.py prompt."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
import extraction_pipeline as pipeline

spec = importlib.util.spec_from_file_location("selection_v6", ROOT.parent / "position-selection-v6/selection.py")
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text() != text:
            raise ValueError(f"Refusing to replace differing evidence: {path}")
    else:
        with path.open("x") as handle:
            handle.write(text)


def prepare():
    plan = read(ROOT / "plan.json")
    source = {case["id"]: case for case in read(ROOT / plan["case_source"])}
    cases = [source[identifier] for identifier in plan["case_ids"]]
    save(ROOT / "cases.json", cases)
    baseline = read(ROOT.parent / "mpv3.31-probe-v1/config.json")
    schema = read(ROOT / plan["output_schema"])
    for version, expected_hash in plan["versions"].items():
        template = (ROOT.parent / f"{version.lower()}-draft-v1/mask-prompt.md").read_text()
        assert hashlib.sha256(template.encode()).hexdigest() == expected_hash
        for placeholder in ("{POST}", "{INDEXED_POST}", "{SUBJECT}"):
            assert template.count(placeholder) == 1
        prompts = []
        for case in cases:
            values = {"{POST}": case["text"], "{INDEXED_POST}": selection.index_post(case["text"]),
                      "{SUBJECT}": case["subject"]}
            rendered = template
            for placeholder, value in values.items():
                rendered = rendered.replace(placeholder, value)
            prompts.append({"prompt_id": case["id"], "text": rendered})
        config = {**baseline, "run_directory": version.lower() + "-run", "prompts": prompts}
        assert config["output_schema"] == schema
        assert config["provider"] == plan["provider"] and config["auth_file"] is None
        assert config["model"] == plan["model"] and config["reasoning_effort"] == plan["reasoning_effort"]
        destination = ROOT / (version.lower() + "-config.json")
        save(destination, config)
        pipeline.PromptRunnerConfig.load(destination)
    print(f"Prepared {len(cases)} pairs, {len(cases) * 2} prompts; no model calls.")


def collect():
    plan, cases = read(ROOT / "plan.json"), read(ROOT / "cases.json")
    by_id = {case["id"]: case for case in cases}
    rows, totals = [], {}
    for version in plan["versions"]:
        config = pipeline.PromptRunnerConfig.load(ROOT / (version.lower() + "-config.json"))
        manifest = read(config.run_directory / "manifest.json")
        records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
        assert len(records) == len(config.prompts)
        records_by_id = {record["note_id"]: record for record in records}
        assert len(records_by_id) == len(config.prompts)
        totals[version] = {key: 0 for key in ("input", "output", "reasoning", "cacheRead", "cacheWrite", "totalTokens")}
        for prompt in config.prompts:
            record = records_by_id[prompt.prompt_id]
            pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
            assert record["status"] == "succeeded"
            assert record["attempt"] == 1
            case, raw = by_id[prompt.prompt_id], record["final_output_raw"]
            error, ranges = None, None
            try:
                ranges = selection.decode(raw, case["text"])
            except ValueError as failure:
                error = str(failure)
            fragments = None if ranges is None else [case["text"][s["start"]:s["end"]] for s in ranges]
            inline = case["text"]
            for span in reversed(ranges or []):
                inline = inline[:span["start"]] + "⟦" + inline[span["start"]:span["end"]] + "⟧" + inline[span["end"]:]
            usage = record.get("usage")
            assert isinstance(usage, dict), "Missing usage must not be treated as zero"
            for key in totals[version]:
                totals[version][key] += usage[key]
            rows.append({"version": version, "id": case["id"], "subject": case["subject"],
                         "raw": raw, "format_valid": error is None, "decode_error": error,
                         "ranges": ranges, "fragments": fragments, "inline_mask": inline,
                         "receipt_path": str(config.run_directory / "results.jsonl"),
                         "request_sha256": record["request_sha256"],
                         "execution": record.get("execution", "new_call"), "usage": usage})
    save(ROOT / "comparison.json", {"versions": plan["versions"], "usage": totals, "results": rows,
                                    "semantic_assessment": "Separate; mechanical validation is not approval."})
    for case in cases:
        print(case["id"], case["subject"])
        for row in rows:
            if row["id"] == case["id"]:
                print(" ", row["version"], row["fragments"] if row["format_valid"] else row["decode_error"])
    print(json.dumps({"validated_receipts": len(rows), "format_valid": sum(row["format_valid"] for row in rows),
                      "reused": sum(row["execution"] == "cross_run_reuse" for row in rows), "usage": totals}))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
