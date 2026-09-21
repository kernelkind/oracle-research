"""Prepare a paired MPv3.37 batch; reuse the existing diagnostic collector."""
import hashlib
from collections import Counter
import importlib.util
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("diagnostic_study", ROOT.parent / "mpv3.34-probe-v1/study.py")
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
study.ROOT = ROOT
read, save = study.read, study.save


def prepare():
    plan = read(ROOT / "plan.json")
    for name in ("config.json", "cases.json", "input-hashes.json", "saved-baseline"):
        assert not (ROOT / name).exists(), f"Refusing to overwrite {name}"
    prompt_path = ROOT.parent / "mpv3.37-draft-v1/mask-prompt.md"
    schema_path = ROOT.parent / "mpv3.34-draft-v1/output-schema.json"
    template = prompt_path.read_text()
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    assert all(template.count("{" + key + "}") == 1 for key in ("POST", "INDEXED_POST", "SUBJECT"))
    cases, baseline_rows, prompts = [], [], []
    evidence = [ROOT / "plan.json", prompt_path, schema_path]
    config = None
    for source in plan["baseline_sources"]:
        directory = ROOT / source
        old_config = read(directory / "config.json")
        for field in ("model", "reasoning_effort", "provider", "auth_file"):
            assert old_config[field] == plan[field]
        assert old_config["output_schema"] == read(schema_path)
        if config is None:
            config = {**old_config, "run_directory": "run", "prompts": prompts}
        else:
            assert {k:v for k,v in old_config.items() if k not in ("prompts", "run_directory")} == {
                k:v for k,v in config.items() if k not in ("prompts", "run_directory")}
        rows = {row["id"]: row for row in read(directory / "comparison.json")["results"]}
        saved_prompts = {item["prompt_id"]:item["text"] for item in old_config["prompts"]}
        for case in read(directory / "cases.json"):
            assert hashlib.sha256(case["text"].encode()).hexdigest() == case["source_text_sha256"]
            assert rows[case["id"]]["subject"] == case["subject"]
            values = {"POST":case["text"], "INDEXED_POST":study.selection.index_post(case["text"]), "SUBJECT":case["subject"]}
            rendered = re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda m: values[m[1]], template)
            # The source, its word numbering and fixed subject must match the saved request exactly.
            assert rendered.split("<post>", 1)[1] == saved_prompts[case["id"]].split("<post>", 1)[1]
            prompts.append({"prompt_id":case["id"], "text":rendered})
            cases.append({**case, "baseline_directory":source})
            baseline_rows.append({**rows[case["id"]], "baseline_directory":source})
        evidence.extend(directory / name for name in ("config.json", "cases.json", "comparison.json", "assessment.json", "run/manifest.json", "run/results.jsonl"))
    assert len(cases) == len({case["id"] for case in cases}) == plan["calls"]
    assert len({case["note_id"] for case in cases}) == 8
    (ROOT / "saved-baseline").mkdir()
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", config)
    save(ROOT / "saved-baseline/comparison.json", {"version":"MPv3.34", "results":baseline_rows})
    evidence.extend(ROOT / name for name in ("cases.json", "config.json", "saved-baseline/comparison.json"))
    save(ROOT / "input-hashes.json", {str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence})
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} unchanged pairs from eight notes; no baseline calls.")


def review():
    cases = {case["id"]:case for case in read(ROOT / "cases.json")}
    rows = {row["id"]:row for row in read(ROOT / "comparison.json")["results"]}
    judgments = read(ROOT / "assessment.json")["items"]
    assert len(judgments) == len(cases) and {j["id"] for j in judgments} == cases.keys()
    items, empty_results = [], []
    for judgment in judgments:
        if "review_comment" not in judgment:
            continue
        case, row = cases[judgment["id"]], rows[judgment["id"]]
        assert row["format_valid"], "Invalid outputs require a separate format-failure report"
        if not row["ranges"]:
            empty_results.append({"id":case["id"], "subject":case["subject"], "note":case["text"],
                                  "raw":row["raw"], "assessment":judgment["review_comment"]})
            continue
        fragments = []
        for span in row["ranges"]:
            text = case["text"][span["start"]:span["end"]]
            positions = [match.span() for match in re.finditer(re.escape(text), case["text"])]
            fragments.append({"text":text, "occurrence":positions.index((span["start"], span["end"])) + 1})
        baseline = row["baseline"][0]
        items.append({"item_id":"MPv3.37-" + case["id"], "note_id":case["note_id"],
                      "subject":case["subject"], "note":case["text"], "fragments":fragments,
                      "assessment":judgment["review_comment"],
                      "details":"Saved MPv3.34 fragments: " + repr(baseline["fragments"])
                      + "\n\nMPv3.37 diagnostics (model claims, not the review judgment):\n"
                      + "\n".join(f"{key}: {value}" for key, value in row["diagnostics"].items())})
    save(ROOT / "review-questionable.json", {"schema_version":1, "batch_id":"MPv3.37-probe-v1", "items":items})
    save(ROOT / "review-empty-results.json", {
        "reason":"The existing mask-review UI rejects empty fragment lists. These actual empty outputs remain separate; no highlights are fabricated.",
        "items":empty_results
    })
    save(ROOT / "assessment-summary.json", {
        "cases":len(cases),
        "MPv3.37":dict(Counter(j["verdict"] for j in judgments)),
        "MPv3.34_under_current_policy":dict(Counter(j["baseline_verdict"] for j in judgments)),
        "changes":dict(Counter(j["change"] for j in judgments)),
        "review_items":len(items),
        "empty_results_reported_separately":len(empty_results),
        "limits":"Selected reused inputs with one answer each; not a general accuracy or reliability estimate."
    })
    print(f"Prepared {len(items)} UI items and {len(empty_results)} separate empty-output cases; user decisions untouched.")


if __name__ == "__main__":
    {"prepare":prepare, "collect":study.collect, "review":review}[sys.argv[1]]()
