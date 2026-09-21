"""Offline non-food experiment adapter; reuse runner, decoder and handoff collector."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fresh_study", ROOT.parent / "mpv3.43-fresh-v1/study.py")
fresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fresh)
fresh.ROOT = ROOT
study = fresh.study
study.ROOT = ROOT
read, save = study.read, study.save


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_subjects():
    assert not (ROOT / "subject-config.json").exists()
    plan = read(ROOT / "plan.json")
    roots = [ROOT.parent, ROOT.parents[1] / "mask-prompt-probe-v1", ROOT.parents[1] / "subject-prompt-goal-v1"]
    posts, sources = [], []
    for selected in plan["selection"]:
        source = (ROOT / selected["source"]).resolve()
        matches = [n for n in read(source)["notes"] if n["note_id"] == selected["note_id"]]
        assert len(matches) == 1
        result = subprocess.run(["rg", "--no-ignore", "--hidden", "-l", "-F", "-g", "*.json", "-g", "*.jsonl",
                                 "-g", f"!**/{ROOT.name}/**", selected["note_id"], *map(str, roots)], capture_output=True, text=True)
        assert result.returncode == 1 and not result.stdout, (result.stdout, result.stderr)
        posts.append({**selected, "text": matches[0]["text"], "original_source_entry": matches[0]})
        sources.append(source)
    prompt_path = ROOT.parents[1] / "subject-prompt-goal-v1/asv6.48/ASv6.48.md"
    assert sha(prompt_path) == plan["subject_prompt_sha256"]
    config = read(ROOT.parent / "mpv3.43-handoff-v1/subject-config.json")
    config.update(run_directory="subject-run", prompts=[{"prompt_id": p["id"],
        "text": prompt_path.read_text().rstrip() + "\n\n<post>\n" + p["text"] + "\n</post>"} for p in posts])
    for field in ("model", "reasoning_effort", "provider", "auth_file", "timeout_seconds"):
        assert config[field] == plan[field]
    save(ROOT / "posts.json", posts)
    save(ROOT / "subject-config.json", config)
    save(ROOT / "freshness.json", {"scope": plan["freshness_scope"], "roots": list(map(str, roots)),
        "checks": [{"note_id": p["note_id"], "matching_files": []} for p in posts]})
    evidence = sources + [prompt_path, ROOT.parent / "mpv3.43-handoff-v1/plan.json",
        ROOT.parent / "mpv3.43-handoff-v1/collect.py"] + [ROOT / n for n in
        ("plan.json", "study.py", "posts.json", "subject-config.json", "freshness.json")]
    save(ROOT / "subject-input-hashes.json", {str(p): sha(p) for p in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "subject-config.json")
    print(f"Prepared {len(posts)} subject calls; no inference.")


def prepare_masks():
    assert not (ROOT / "config.json").exists()
    plan = read(ROOT / "plan.json")
    for path, expected in read(ROOT / "subject-input-hashes.json").items():
        assert sha(Path(path)) == expected, path
    config = study.pipeline.PromptRunnerConfig.load(ROOT / "subject-config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    assert len(records) == len({r["note_id"] for r in records}) == len(plan["selection"])
    records = {r["note_id"]: r for r in records}
    posts = {p["id"]: p for p in read(ROOT / "posts.json")}
    notes, cases = [], []
    for prompt in config.prompts:
        record, post = records[prompt.prompt_id], posts[prompt.prompt_id]
        study.pipeline.validate_prompt_receipt(dataclasses.replace(config, prompts=(prompt,)), manifest, record)
        assert record["status"] == "succeeded" and record["attempt"] == 1
        result = json.loads(record["final_output_raw"])
        seen = set()
        for i, subject in enumerate(result["subjects"], 1):
            number = subject["number"]
            assert number not in seen and ("." not in number or number.rsplit(".", 1)[0] in seen)
            seen.add(number)
            cases.append({"id": f'{post["id"]}-{i:03}', "note_id": post["note_id"], "text": post["text"],
                "subject": subject["subject"], "subject_entry": subject,
                "source_text_sha256": hashlib.sha256(post["text"].encode()).hexdigest()})
        notes.append({**post, "subjects": result["subjects"], "subject_request_sha256": record["request_sha256"]})
    template_path = ROOT.parent / "mpv3.43-draft-v1/mask-prompt.md"
    assert sha(template_path) == plan["prompt_sha256"]
    template = template_path.read_text()
    assert all(template.count("{" + k + "}") == 1 for k in ("POST", "INDEXED_POST", "SUBJECT"))
    mask_config = read(ROOT.parent / "mpv3.43-handoff-v1/config.json")
    mask_config.update(run_directory="run", prompts=[])
    for case in cases:
        values = {"POST": case["text"], "INDEXED_POST": study.selection.index_post(case["text"]), "SUBJECT": case["subject"]}
        mask_config["prompts"].append({"prompt_id": case["id"], "text": re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda m: values[m[1]], template)})
    save(ROOT / "subjects.json", {"schema_version": 1, "notes": notes})
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", mask_config)
    evidence = [template_path, config.run_directory / "results.jsonl", config.run_directory / "manifest.json"]
    evidence += [ROOT / n for n in ("plan.json", "study.py", "subjects.json", "cases.json", "config.json", "subject-input-hashes.json")]
    save(ROOT / "input-hashes.json", {str(p): sha(p) for p in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared all {len(cases)} subjects from {len(posts)} posts; no masking inference.")


def collect():
    runpy.run_path(str(ROOT.parent / "mpv3.43-handoff-v1/collect.py"), run_name="__main__")


if __name__ == "__main__":
    {"prepare-subjects": prepare_subjects, "prepare-masks": prepare_masks,
     "collect": collect, "review": fresh.review}[sys.argv[1]]()
