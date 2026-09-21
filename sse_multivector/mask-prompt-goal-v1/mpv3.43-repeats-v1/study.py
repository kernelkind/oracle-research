"""Prepare exact repeat inputs and reuse the existing receipt/mask collector."""
import hashlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "diagnostic_study", ROOT.parent / "mpv3.34-probe-v1/study.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
study.ROOT = ROOT
read, save = study.read, study.save


def prepare():
    plan = read(ROOT / "plan.json")
    baseline = ROOT / plan["baseline_directory"]
    prompt_path = ROOT.parent / "mpv3.43-draft-v1/mask-prompt.md"
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    source_cases = {case["id"]: case for case in read(baseline / "cases.json")}
    config = read(baseline / "config.json")
    for field in ("model", "reasoning_effort", "provider", "auth_file"):
        assert config[field] == plan[field]
    source_prompts = {item["prompt_id"]: item["text"] for item in config["prompts"]}
    prompts, cases = [], []
    for trial in plan["additional_trials"]:
        for case_id in plan["case_ids"]:
            job_id = f"{case_id}-t{trial}"
            case = source_cases[case_id]
            assert hashlib.sha256(case["text"].encode()).hexdigest() == case["source_text_sha256"]
            cases.append({**case, "id": job_id, "case_id": case_id, "trial": trial})
            prompts.append({"prompt_id": job_id, "text": source_prompts[case_id]})
    assert len(cases) == len({case["id"] for case in cases}) == plan["calls"]
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", {**config, "run_directory": "run", "prompts": prompts})
    evidence = [ROOT / "plan.json", ROOT / "study.py", prompt_path, ROOT / "cases.json", ROOT / "config.json"]
    evidence.extend(baseline / name for name in (
        "cases.json", "config.json", "comparison.json", "assessment.json", "run/manifest.json", "run/results.jsonl"
    ))
    save(ROOT / "input-hashes.json", {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} exact repeat prompts; no model calls.")


def collect():
    study.collect()
    plan = read(ROOT / "plan.json")
    baseline = ROOT / plan["baseline_directory"]
    initial = {row["id"]: row for row in read(baseline / "comparison.json")["results"]}
    new = read(ROOT / "comparison.json")
    cases = {case["id"]: case for case in read(ROOT / "cases.json")}
    manifest = read(ROOT / "run/manifest.json")
    assert manifest["request_reuse"]["intentional_repeat"] is True
    grouped = {case_id: [] for case_id in plan["case_ids"]}
    fields = ("subject", "format_valid", "decode_error", "fragments", "inline_mask", "diagnostics", "request_sha256", "receipt_path")
    for case_id in grouped:
        grouped[case_id].append({"trial": 1, "id": case_id, **{key: initial[case_id][key] for key in fields}})
    for row in new["results"]:
        case = cases[row["id"]]
        first = initial[case["case_id"]]
        assert row["execution"] != "cross_run_reuse"
        for field in ("request_sha256", "runner_sha256", "wrapper_sha256"):
            assert row[field] == first[field], (row["id"], field)
        grouped[case["case_id"]].append({"trial": case["trial"], "id": row["id"], **{key: row[key] for key in fields}})
    assert all([row["trial"] for row in rows] == [1, 2, 3] for rows in grouped.values())
    save(ROOT / "results.json", {"version": plan["version"], "new_call_summary": new["summary"], "cases": grouped,
                                "semantic_assessment": "Separate; three saved outputs per case, not an accuracy estimate."})
    print("Verified eight fresh calls with identical request, runner and wrapper hashes; grouped all three trials per case.")


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
