"""Prepare saved fresh subjects and reuse existing mask collection/review formats."""
import hashlib
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("diagnostic_study", ROOT.parent / "mpv3.34-probe-v1/study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
study.ROOT = ROOT
read, save = study.read, study.save


def prepare():
    plan = read(ROOT / "plan.json")
    source_path = (ROOT / plan["subject_source"]).resolve()
    source = read(source_path)
    subjects = {s["id"]: (n, s) for n in source["notes"] for s in n["subjects"]}
    cases = []
    for selected in plan["selection"]:
        note, subject = subjects[selected["source_subject_id"]]
        assert subject["judgment"] == "accepted" and subject["provenance"]["correction"] is None
        assert subject["subject"] == subject["provenance"]["raw_subject"]
        cases.append({**selected, "note_id": note["note_id"], "text": note["text"],
                      "subject": subject["subject"], "subject_provenance": subject["provenance"],
                      "source_text_sha256": hashlib.sha256(note["text"].encode()).hexdigest()})
    assert len(cases) == len({c["id"] for c in cases}) == plan["calls"]
    note_ids = sorted({c["note_id"] for c in cases})
    assert len(note_ids) == plan["posts"]
    roots = [ROOT.parent, ROOT.parents[1] / "mask-prompt-probe-v1"]
    checks = []
    for note_id in note_ids:
        command = ["rg", "--no-ignore", "--hidden", "-l", "-F", "--glob", "*.json", "--glob", "*.jsonl",
                   "--glob", f"!**/{ROOT.name}/**", note_id, *map(str, roots)]
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode in (0, 1), result.stderr
        assert not result.stdout, (note_id, result.stdout)
        checks.append({"note_id": note_id, "matching_files": []})
    save(ROOT / "freshness.json", {"scope": plan["freshness_scope"], "roots": list(map(str, roots)),
                                   "ignored_files_included": True, "excluded_directory": str(ROOT), "checks": checks})
    prompt_path = ROOT.parent / "mpv3.43-draft-v1/mask-prompt.md"
    template = prompt_path.read_text()
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    assert all(template.count("{" + key + "}") == 1 for key in ("POST", "INDEXED_POST", "SUBJECT"))
    baseline = ROOT / plan["baseline_directory"]
    config = read(baseline / "config.json")
    for field in ("model", "reasoning_effort", "provider", "auth_file"):
        assert config[field] == plan[field]
    prompts = []
    for case in cases:
        values = {"POST": case["text"], "INDEXED_POST": study.selection.index_post(case["text"]), "SUBJECT": case["subject"]}
        rendered = re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda m: values[m[1]], template)
        prompts.append({"prompt_id": case["id"], "text": rendered})
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", {**config, "run_directory": "run", "prompts": prompts})
    evidence = [source_path, prompt_path, baseline / "config.json", baseline / "comparison.json"]
    evidence.extend(ROOT / name for name in ("plan.json", "study.py", "cases.json", "config.json", "freshness.json"))
    save(ROOT / "input-hashes.json", {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} unchanged subjects from {len(note_ids)} fresh posts; no model calls.")


def review():
    plan = read(ROOT / "plan.json")
    cases = {c["id"]: c for c in read(ROOT / "cases.json")}
    rows = {r["id"]: r for r in read(ROOT / "comparison.json")["results"]}
    judgments = read(ROOT / "assessment.json")["items"]
    assert len(judgments) == len(cases) and {j["id"] for j in judgments} == cases.keys()
    items, separate = [], []
    for judgment in judgments:
        if "review_comment" not in judgment:
            continue
        case, row = cases[judgment["id"]], rows[judgment["id"]]
        if not row["format_valid"] or not row["ranges"]:
            separate.append({"id": case["id"], "subject": case["subject"], "note": case["text"],
                             "raw": row["raw"], "assessment": judgment["review_comment"]})
            continue
        fragments = []
        for span in row["ranges"]:
            text = case["text"][span["start"]:span["end"]]
            positions = [m.span() for m in re.finditer(re.escape(text), case["text"])]
            fragments.append({"text": text, "occurrence": positions.index((span["start"], span["end"])) + 1})
        items.append({"item_id": plan["version"] + "-" + case["id"], "note_id": case["note_id"],
                      "subject": case["subject"], "note": case["text"], "fragments": fragments,
                      "assessment": judgment["review_comment"],
                      "details": "Model diagnostics, not review decisions:\n" + "\n".join(f"{k}: {v}" for k, v in row["diagnostics"].items())})
    save(ROOT / "review-questionable.json", {"schema_version": 1, "batch_id": ROOT.name, "items": items})
    save(ROOT / "review-separate.json", {"reason": "The existing UI cannot display empty or invalid masks; no highlights fabricated.", "items": separate})
    print(f"Prepared {len(items)} UI items and {len(separate)} separate empty/invalid results; no user decisions written.")


if __name__ == "__main__":
    {"prepare": prepare, "collect": study.collect, "review": review}[sys.argv[1]]()
