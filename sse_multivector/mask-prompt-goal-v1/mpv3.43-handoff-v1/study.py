"""Small offline adapter; reuse saved-batch inference and diagnostic mask decoding."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import re
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
    assert not (ROOT / "subject-config.json").exists(), "Preserve prepared evidence"
    plan = read(ROOT / "plan.json")
    source = (ROOT / plan["subject_source"]).resolve()
    posts = [n for n in read(source)["notes"] if n["selection_rank"] in plan["selection_ranks"]]
    assert [n["selection_rank"] for n in posts] == plan["selection_ranks"]
    roots = [ROOT.parent, ROOT.parents[1] / "mask-prompt-probe-v1", ROOT.parents[1] / "subject-prompt-goal-v1"]
    for post in posts:
        result = subprocess.run(["rg", "--no-ignore", "--hidden", "-l", "-F", "-g", "*.json", "-g", "*.jsonl",
                                 "-g", f"!**/{ROOT.name}/**", post["note_id"], *map(str, roots)], capture_output=True, text=True)
        assert result.returncode == 1 and not result.stdout, (post["note_id"], result.stdout, result.stderr)
    prompt_path = ROOT.parents[1] / "subject-prompt-goal-v1/asv6.48/ASv6.48.md"
    assert sha(prompt_path) == plan["subject_prompt_sha256"]
    config = read(ROOT.parents[1] / "subject-prompt-goal-v1/asv6.48-remaining-six-v1/config.json")
    config.update(auth_file=None, timeout_seconds=plan["timeout_seconds"], run_directory="subject-run",
                  prompts=[{"prompt_id": f'N{n["selection_rank"]:03}',
                            "text": prompt_path.read_text().rstrip() + "\n\n<post>\n" + n["text"] + "\n</post>"} for n in posts])
    save(ROOT / "posts.json", [{k: n[k] for k in ("selection_rank", "note_id", "text")} for n in posts])
    save(ROOT / "freshness.json", {"scope": plan["freshness_scope"], "roots": list(map(str, roots)),
                                   "checks": [{"note_id": n["note_id"], "matching_files": []} for n in posts]})
    save(ROOT / "subject-config.json", config)
    evidence = [source, prompt_path] + [ROOT / n for n in ("plan.json", "study.py", "posts.json", "freshness.json", "subject-config.json")]
    save(ROOT / "subject-input-hashes.json", {str(p): sha(p) for p in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "subject-config.json")
    print("Prepared two subject calls; no inference.")


def prepare_masks():
    assert not (ROOT / "config.json").exists(), "Preserve prepared evidence"
    plan = read(ROOT / "plan.json")
    for path, expected in read(ROOT / "subject-input-hashes.json").items():
        assert sha(Path(path)) == expected, path
    config = study.pipeline.PromptRunnerConfig.load(ROOT / "subject-config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    assert len(records) == 2
    records = {r["note_id"]: r for r in records}
    posts = {f'N{n["selection_rank"]:03}': n for n in read(ROOT / "posts.json")}
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
            cases.append({"id": f'I{post["selection_rank"]:03}-{i:03}', "note_id": post["note_id"], "text": post["text"],
                          "subject": subject["subject"], "subject_entry": subject,
                          "source_text_sha256": hashlib.sha256(post["text"].encode()).hexdigest()})
        notes.append({**post, "subjects": result["subjects"], "subject_request_sha256": record["request_sha256"]})
    template_path = ROOT.parent / "mpv3.43-draft-v1/mask-prompt.md"
    assert sha(template_path) == plan["prompt_sha256"]
    template = template_path.read_text()
    assert all(template.count("{" + key + "}") == 1 for key in ("POST", "INDEXED_POST", "SUBJECT"))
    mask_config = read(ROOT.parent / "mpv3.43-fresh-v1/config.json")
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
    print(f"Prepared all {len(cases)} subjects from two posts; no masking inference.")


if __name__ == "__main__":
    {"prepare-subjects": prepare_subjects, "prepare-masks": prepare_masks,
     "collect": study.collect, "review": fresh.review}[sys.argv[1]]()
