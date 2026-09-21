"""Prepare the approved paired batch; reuse existing diagnostic collection."""
import hashlib
import importlib.util
from pathlib import Path
import re
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
    template = prompt_path.read_text()
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    assert all(template.count("{" + key + "}") == 1 for key in ("POST", "INDEXED_POST", "SUBJECT"))
    cases = read(baseline / "cases.json")
    config = read(baseline / "config.json")
    for field in ("model", "reasoning_effort", "provider", "auth_file"):
        assert config[field] == plan[field]
    saved_prompts = {item["prompt_id"]: item["text"] for item in config["prompts"]}
    prompts = []
    for case in cases:
        assert hashlib.sha256(case["text"].encode()).hexdigest() == case["source_text_sha256"]
        values = {"POST": case["text"], "INDEXED_POST": study.selection.index_post(case["text"]),
                  "SUBJECT": case["subject"]}
        rendered = re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda match: values[match[1]], template)
        assert rendered.split("<post>", 1)[1] == saved_prompts[case["id"]].split("<post>", 1)[1]
        prompts.append({"prompt_id": case["id"], "text": rendered})
    assert len(prompts) == len({case["id"] for case in cases}) == plan["calls"]
    assert len({case["note_id"] for case in cases}) == 8
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", {**config, "run_directory": "run", "prompts": prompts})
    evidence = [ROOT / "plan.json", ROOT / "study.py", prompt_path, ROOT / "cases.json", ROOT / "config.json"]
    evidence.extend(baseline / name for name in (
        "cases.json", "config.json", "comparison.json", "assessment.json", "run/manifest.json", "run/results.jsonl"
    ))
    save(ROOT / "input-hashes.json", {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} unchanged pairs from eight posts; no baseline calls.")


if __name__ == "__main__":
    {"prepare": prepare, "collect": study.collect}[sys.argv[1]]()
