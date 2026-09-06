"""Read-only verification of the ASv6.11 test; makes no model calls."""

import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from sse_multivector import codex_exec as runner


def read_json(path):
    return json.loads(path.read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


config = runner.SubjectRunnerConfig.load(HERE / "config.json")
notes = runner._load_notes(config.input_path)
manifest = read_json(HERE / "run/manifest.json")
manifest_hash = sha((HERE / "run/manifest.json").read_bytes())
output = read_json(HERE / "run/output.json")
records = [json.loads(line) for line in (HERE / "run/results.jsonl").read_text().splitlines()]
baseline_dir = HERE.parent / "atomic-subject-asv6.8-vs-asv6.10-holdout-v1/asv6.10/run"
baseline = read_json(baseline_dir / "manifest.json")
protected = read_json(HERE / "protected-before.json")["sha256"]
prior_paths = [ROOT / path for path in protected if path.endswith("/results.jsonl")]
prior_records = [json.loads(line) for path in prior_paths for line in path.read_text().splitlines()]

assert len(notes) == len(records) == len(output["notes"]) == 20
assert output["manifest_sha256"] == manifest_hash
assert config.subject.prompt == (HERE.parent / "atomic-subject-asv6.11-proposal-v1/ASv6.11.md").read_text().removesuffix("\n")
assert sha(config.input_path.read_bytes()) == manifest["input_sha256"]
unchanged_fields = ["input_sha256", "wrapper_sha256", "isolation", "codex_binary", "codex_version", "subject_envelope_version", "subject_input_normalization_version"]
for field in unchanged_fields:
    assert manifest[field] == baseline[field], field
for field in ["model", "reasoning_effort", "response_schema", "response_schema_sha256"]:
    assert manifest["subject"][field] == baseline["subject"][field], field
assert sha((ROOT / "sse_multivector/codex_exec.py").read_bytes()) == manifest["wrapper_sha256"]
assert sha((HERE / "run/model-instructions.md").read_bytes()) == manifest["isolation"]["model_instructions_sha256"]
assert read_json(HERE / "run/subject-output-schema.json") == manifest["subject"]["response_schema"]

threads = set()
workdirs = set()
for note, record, published in zip(notes, records, output["notes"]):
    assert record["note_id"] == note.note_id == published["note_id"]
    assert published["text"] == note.text
    assert record["status"] == "succeeded" and record["exit_code"] == 0 and record["attempt"] == 1
    assert record["manifest_sha256"] == manifest_hash
    assert record["model"] == "gpt-5.6-sol" and record["reasoning_effort"] == "low"
    assert record["wrapper_sha256"] == manifest["wrapper_sha256"]
    assert record["prompt_sha256"] == sha(runner._render_subject_prompt(config.subject.prompt, note).encode())
    for value, hash_key in [("final_output_raw", "final_output_sha256"), ("stdout_jsonl", "stdout_sha256"), ("stderr", "stderr_sha256")]:
        assert sha(record[value].encode()) == record[hash_key], (note.note_id, value)
    raw_subjects = json.loads(record["final_output_raw"])["subjects"]
    assert raw_subjects == record["response"] == [item["text"] for item in published["subjects"]]
    assert [item["source_index"] for item in published["subjects"]] == list(range(len(raw_subjects)))
    events = [json.loads(line) for line in record["stdout_jsonl"].splitlines()]
    assert sum(event["type"] == "turn.started" for event in events) == 1
    assert sum(event["type"] == "turn.completed" for event in events) == 1
    assert all(event["item"]["type"] == "agent_message" for event in events if "item" in event)
    assert [event["thread_id"] for event in events if event["type"] == "thread.started"] == [record["thread_id"]]
    argv = record["argv"]
    assert all(flag in argv for flag in ["--ephemeral", "--ignore-rules", "--ignore-user-config", "--strict-config"])
    assert "resume" not in argv
    workdir = argv[argv.index("--cd") + 1]
    assert record["thread_id"] not in threads and workdir not in workdirs
    threads.add(record["thread_id"])
    workdirs.add(workdir)

prior_threads = {record["thread_id"] for record in prior_records}
prior_workdirs = {record["argv"][record["argv"].index("--cd") + 1] for record in prior_records}
assert not threads.intersection(prior_threads)
assert not workdirs.intersection(prior_workdirs)
changed = [path for path, digest in protected.items() if sha((ROOT / path).read_bytes()) != digest]
allowed_docs = {
    "sse_multivector/atomic-subject-asv6.8-vs-asv6.10-holdout-v1/README.md",
    "sse_multivector/atomic-subject-asv6.8-vs-asv6.10-holdout-v1/status.json",
}
assert not set(changed) - allowed_docs, changed
report = (HERE / "results.md").read_text()
old_output = read_json(baseline_dir / "output.json")
sections = report.split("\n## N")[1:]
assert len(sections) == len(notes)
for index, (note, old_note, new_note, section) in enumerate(zip(notes, old_output["notes"], output["notes"], sections), 1):
    assert section.startswith(f"{index:02d}\n")
    assert note.note_id == old_note["note_id"] == new_note["note_id"]
    assert "\n".join(("> " + line).rstrip(" \t") for line in note.text.split("\n")) in section
    for version, published in [("ASv6.10", old_note), ("ASv6.11", new_note)]:
        block = version + ":\n\n" + "\n".join(f"{i}. {item['text']}" for i, item in enumerate(published["subjects"], 1))
        assert block in section
for path in HERE.rglob("*.json"):
    read_json(path)
usage_keys = set().union(*(record["usage"].keys() for record in records))
summary = {
    "schema_version": 1,
    "completed_calls": len(records),
    "subjects": sum(len(record["response"]) for record in records),
    "distinct_threads": len(threads),
    "distinct_workdirs": len(workdirs),
    "prior_calls_checked_for_reuse": len(prior_records),
    "shared_threads_or_workdirs": 0,
    "one_turn_per_call": True,
    "no_tool_events": True,
    "rendered_prompt_and_raw_hashes_verified": True,
    "unedited_subject_exports": True,
    "full_report_notes_and_all_subjects_verified": True,
    "baseline_input_and_execution_settings_unchanged": True,
    "protected_files": len(protected),
    "unchanged_protected_files": len(protected) - len(changed),
    "only_allowed_documentation_updates": changed,
    "usage": {key: sum(record["usage"].get(key, 0) for record in records) for key in sorted(usage_keys)},
    "summed_call_seconds": sum(record["elapsed_seconds"] for record in records),
}
print(json.dumps(summary, indent=2))
