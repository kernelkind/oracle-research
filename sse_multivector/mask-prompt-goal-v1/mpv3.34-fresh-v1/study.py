"""Prepare fresh saved pairs; reuse MPv3.34 decoding/collection without model calls."""
import hashlib
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
    source_path = (ROOT / plan["subject_source"]).resolve()
    source = read(source_path)
    subjects = {subject["id"]: (note, subject) for note in source["notes"] for subject in note["subjects"]}
    cases = []
    for selected in plan["selection"]:
        note, subject = subjects[selected["source_subject_id"]]
        assert subject["judgment"] == "accepted"
        assert subject["provenance"]["correction"] is None
        assert subject["subject"] == subject["provenance"]["raw_subject"]
        cases.append({**selected, "text": note["text"], "note_id": note["note_id"],
                      "subject": subject["subject"], "subject_origin": plan["subject_origin"],
                      "subject_provenance": subject["provenance"],
                      "source_text_sha256": hashlib.sha256(note["text"].encode()).hexdigest()})
    assert len(cases) == plan["calls"] == 6
    assert len({case["note_id"] for case in cases}) == 4
    prior_cases = read(ROOT / plan["baseline_directory"] / "cases.json")
    assert not {case["note_id"] for case in cases} & {case["note_id"] for case in prior_cases}
    prompt_path = ROOT.parent / "mpv3.34-draft-v1/mask-prompt.md"
    schema_path = ROOT.parent / "mpv3.34-draft-v1/output-schema.json"
    template = prompt_path.read_text()
    assert hashlib.sha256(prompt_path.read_bytes()).hexdigest() == plan["prompt_sha256"]
    for placeholder in ("{POST}", "{INDEXED_POST}", "{SUBJECT}"):
        assert template.count(placeholder) == 1
    config = read(ROOT / plan["baseline_directory"] / "config.json")
    assert config["output_schema"] == read(schema_path)
    for field in ("model", "reasoning_effort", "provider", "auth_file"):
        assert config[field] == plan[field]
    config.update(run_directory="run", prompts=[])
    for case in cases:
        values = {"POST": case["text"], "INDEXED_POST": study.selection.index_post(case["text"]),
                  "SUBJECT": case["subject"]}
        rendered = re.sub(r"\{(POST|INDEXED_POST|SUBJECT)\}", lambda match: values[match[1]], template)
        config["prompts"].append({"prompt_id": case["id"], "text": rendered})
    save(ROOT / "cases.json", cases)
    save(ROOT / "config.json", config)
    evidence = [source_path, prompt_path, schema_path, ROOT / "plan.json",
                ROOT / plan["baseline_directory"] / "comparison.json"]
    save(ROOT / "input-hashes.json", {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in evidence
    })
    study.pipeline.PromptRunnerConfig.load(ROOT / "config.json")
    print(f"Prepared {len(cases)} unchanged saved subjects from four notes; no inference.")


def review():
    cases = {case["id"]: case for case in read(ROOT / "cases.json")}
    rows = {row["id"]: row for row in read(ROOT / "comparison.json")["results"]}
    items = []
    for judgment in read(ROOT / "assessment.json")["items"]:
        if "review_comment" not in judgment:
            continue
        case, row = cases[judgment["id"]], rows[judgment["id"]]
        assert row["format_valid"]
        fragments = []
        for span in row["ranges"]:
            text = case["text"][span["start"]:span["end"]]
            matches = list(re.finditer(re.escape(text), case["text"]))
            positions = [match.span() for match in matches]
            occurrence = positions.index((span["start"], span["end"])) + 1
            fragments.append({"text": text, "occurrence": occurrence})
        diagnostic = row["diagnostics"]
        items.append({"item_id": "MPv3.34-" + case["id"], "note_id": case["note_id"],
                      "subject": case["subject"], "note": case["text"], "fragments": fragments,
                      "assessment": judgment["review_comment"],
                      "details": "MPv3.34 model diagnostics (not the reviewer's judgment):\nMeaning: "
                      + diagnostic["meaning"] + "\nExpressible: " + str(diagnostic["expressible"])
                      + "\nEvidence: " + diagnostic["evidence"]})
    save(ROOT / "review-questionable.json", {"schema_version": 1, "batch_id": "MPv3.34-fresh-v1", "items": items})
    print(f"Prepared {len(items)} review item(s); no decisions or inference.")


if __name__ == "__main__":
    {"prepare": prepare, "collect": study.collect, "review": review}[sys.argv[1]]()
