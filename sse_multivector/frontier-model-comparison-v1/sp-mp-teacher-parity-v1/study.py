"""SP/MP teacher-parity round: MiMo high and Muse high against saved Astra.

Offline prepare, collect, packets and report only; inference runs through the
canonical saved batch runner. One MPv3.43 trial per case for all candidates,
plus a predeclared repeat subset, with saved Astra outputs as a third arm (no
Astra calls). Blind scoring packets carry no arm identity. Semantic scoring is
separate from collection and lives in score-*.json files.
"""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

sys.path.insert(0, str(REPO / "sse_multivector"))
import extraction_pipeline as pipeline

EXPERIMENT = "SP-MP-teacher-parity-v1"
SEED = 20260922
REPEAT_TRIALS = 15
PACKET_OVERLAP = 24

PROMPT_VERSION = "MPv3.43"
PROMPT_STATUS = "frozen working baseline (not a production rollout)"
SP_PROMPT_VERSION = "ASv6.48"
SP_PROMPT_STATUS = "frozen subject baseline"

PROMPT = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md"
PROMPT_SHA256 = "75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03"
SCHEMA = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.34-draft-v1/output-schema.json"
SCHEMA_SHA256 = "accf073dd53239dc3ec70f0c458fb8287766f28b201e29f3e5d5cd3c37ca3fe9"
DECODER = REPO / "sse_multivector/mask_positions.py"
DECODER_SHA256 = "690bc72e9a372562b35b2604d57c168440c3675915b1a229447f6d8bebe3dc8e"
PIPELINE_SHA256 = "f132d1febfe4c8323b34278a6d1b6518def0f12e4bc72f44c88ecfc8bcc71025"

DEV_CASES = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.43-probe-v1/cases.json"
DEV_RUN = REPO / "sse_multivector/mask-prompt-goal-v1/mpv3.43-probe-v1/run/results.jsonl"
MASKED = REPO / "sse_multivector/hierarchy-refresh-v1/masked-posts.json"
MASKED_SHA256 = "380e6eb4a2035ec714bd9a1304c77d35bbd5bff04f71e0a018082f1d465369f8"
SUBJECTS = REPO / "sse_multivector/hierarchy-refresh-v1/subjects.json"
SUBJECTS_SHA256 = "60f0cce913554b6f424ec67b488d242fc934325444fbffc8123db903e2f70228"
SP_NOTES_JSON = REPO / "sse_multivector/mask-prompt-goal-v1/asv6.37-corpus-ten-v1/notes.json"
SP_MANIFEST = REPO / "sse_multivector/hierarchy-refresh-v1/subject-run/manifest.json"
MUSE_CASES = REPO / ("sse_multivector/frontier-model-comparison-v1/"
                     "asv6.48-muse-v1/cases.json")
MUSE_SP_DIR = REPO / ("sse_multivector/frontier-model-comparison-v1/"
                      "asv6.48-muse-xhigh-v1/high-ten-note-v1")

SP_NOTES = ("N004", "N029", "N031", "N038", "N052",
            "N061", "N065", "N080", "N094", "N096")

CANDIDATES = (
    {"name": "mimo-high", "model": "xiaomi/mimo-v2.6-pro", "reasoning_effort": "high"},
    {"name": "muse-high", "model": "meta/muse-spark-1.3-contributor",
     "reasoning_effort": "high"},
)
STRATA = {"empty": 10, "single": 12, "multi": 12, "multi-repeat": 8}
PROVIDER = "openrouter"
TIMEOUT_SECONDS = 1800
CONCURRENCY = 12

PARITY_RULE = {
    "acceptable_rate_margin_points": 10,
    "new_recurring_failure_category_allowed": False,
    "format_compliance_required_percent": 100,
    "resolution_note": "60 pairs x 1 trial detects gross regressions "
                       "(roughly 15+ points) and recurring failure categories, "
                       "not small differences; the 15-pair repeat subset "
                       "estimates within-model variance only.",
}

MASK_RUBRIC = {
    "verdicts": ["acceptable", "scope_concern", "incorrect", "uncertain"],
    "error_tags": ["extra_meaning", "missing_meaning", "missing_repetition",
                   "false_empty", "unjustified_nonempty", "wrong_fragment"],
    "criteria": [
        "Exact generality: the selection expresses the supplied subject at its "
        "level of generality, adding no meaning the subject does not require.",
        "Complete joint meaning: together the fragments express the whole "
        "subject, including every genuine repetition or joint contribution.",
        "Empty results are correct only when no combination of exact source "
        "fragments can express the subject at its level.",
        "Judge the mask only; diagnostics are withheld.",
    ],
}

SP_RUBRIC = {
    "verdicts": ["acceptable", "concern", "incorrect", "uncertain"],
    "error_tags": ["unsupported_content", "missing_context", "attribution_loss",
                   "missing_subject", "redundant"],
    "criteria": [
        "Groundedness: every subject is supported by the post; no URL- or "
        "metadata-derived or invented claims.",
        "Standalone: each subject is understandable without its context field; "
        "named entities and services retained where the post names them.",
        "Attribution: disputed or reported claims keep their attribution.",
        "Coverage: the post's substantive content is represented; different "
        "legitimate hierarchies and repetitions are not errors.",
    ],
}


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def pinned_inputs():
    return {
        PROMPT: PROMPT_SHA256,
        SCHEMA: SCHEMA_SHA256,
        DECODER: DECODER_SHA256,
        REPO / "sse_multivector/extraction_pipeline.py": PIPELINE_SHA256,
        MASKED: MASKED_SHA256,
        SUBJECTS: SUBJECTS_SHA256,
        MUSE_CASES: digest(MUSE_CASES),
    }


def check_pins():
    for path, expected in pinned_inputs().items():
        if digest(path) != expected:
            raise ValueError("pinned input changed: " + str(path))


def decoder_module():
    spec = importlib.util.spec_from_file_location("mask_positions", DECODER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config_path(name):
    return ROOT / f"config-{name}.json"


def run_directory(name):
    return ROOT / f"run-{name}"


def char_spans(text, fragments, byte_spans):
    """Resolve stored spans to character offsets, verifying against fragments."""
    if [text[a:b] for a, b in byte_spans] == fragments:
        return [[a, b] for a, b in byte_spans]
    raw = text.encode("utf-8")
    spans = []
    for fragment, (a, b) in zip(fragments, byte_spans):
        chunk = raw[a:b].decode("utf-8")
        if chunk != fragment:
            raise ValueError("stored spans do not match stored fragments")
        start = len(raw[:a].decode("utf-8"))
        spans.append([start, start + len(fragment)])
    return spans


def marked(text, spans):
    ordered = sorted(spans)
    pieces, cursor = [], 0
    for a, b in ordered:
        pieces += [text[cursor:a], "⟦" + text[a:b] + "⟧"]
        cursor = b
    pieces.append(text[cursor:])
    return "".join(pieces)


def dev_cases(decoder):
    cases = read(DEV_CASES)
    outputs = {}
    for line in DEV_RUN.read_text().splitlines():
        record = json.loads(line)
        if record.get("status") == "succeeded":
            outputs[record["job_key"].removeprefix("prompt:")] = record
    selected = []
    for case in cases:
        record = outputs[case["id"]]
        _, ranges = decoder.decode(record["final_output_raw"], case["text"])
        spans = [[r["start"], r["end"]] for r in ranges]
        selected.append({
            "id": case["id"], "source": "dev", "note_id": case["note_id"],
            "text": case["text"], "subject": case["subject"],
            "reference_spans": spans,
            "reference_fragments": [case["text"][a:b] for a, b in spans],
            "expected_mask": case.get("expected_mask"),
        })
    return selected


def fresh_cases(decoder):
    masked = read(MASKED)
    dev_posts = {case["note_id"] for case in read(DEV_CASES)}
    strata = {"empty": [], "single": [], "multi": [], "multi-repeat": []}
    for note in masked["notes"]:
        if note["note_id"] in dev_posts:
            continue
        for entry in note["subjects"]:
            spans = char_spans(note["text"], entry["fragments"], entry["byte_spans"])
            if not spans:
                kind = "empty"
            elif len(spans) == 1:
                kind = "single"
            elif len(entry["fragments"]) != len(set(entry["fragments"])):
                kind = "multi-repeat"
            else:
                kind = "multi"
            strata[kind].append({
                "note_id": note["note_id"], "text": note["text"],
                "subject": entry["subject"], "reference_spans": spans,
                "reference_fragments": entry["fragments"],
                "expected_mask": "empty" if not spans else "nonempty",
            })
    rng = random.Random(SEED)
    selected = []
    for kind, count in STRATA.items():
        pool = sorted(strata[kind], key=lambda c: (c["note_id"], c["subject"]))
        chosen = rng.sample(pool, count)
        for case in chosen:
            case["stratum"] = kind
        selected.extend(chosen)
    for index, case in enumerate(sorted(
            selected, key=lambda c: (c["note_id"], c["subject"]))):
        case["id"] = f"FR{index + 1:02d}"
        case["source"] = "fresh"
    return selected


def sp_source(label):
    direct = MUSE_SP_DIR / label / "attempt.json"
    if direct.exists():
        return MUSE_SP_DIR / label
    reused = MUSE_SP_DIR.parent / "high-uncapped-v1"
    if label == "N031" and (reused / "attempt.json").exists():
        return reused
    raise ValueError(f"{label}: no saved ASv6.48 request found")


def sp_cases():
    entries = {entry["id"]: entry for entry in read(SP_NOTES_JSON)["notes"]}
    by_note_id = {note["note_id"]: note for note in read(SUBJECTS)["notes"]}
    expected = {request["id"]: request["prompt_sha256"]
                for request in read(MUSE_CASES)["requests"]}
    cases = []
    for label in SP_NOTES:
        entry = entries[label]
        source = sp_source(label)
        attempt = read(source / "attempt.json")
        content = attempt["request"]["body"]["messages"][0]["content"]
        if isinstance(content, list):
            content = content[0]["text"]
        checks = [hashlib.sha256(content.encode()).hexdigest()]
        if attempt.get("prompt_sha256") is not None:
            checks.append(attempt["prompt_sha256"])
        for recorded in checks:
            if recorded != expected[label]:
                raise ValueError(f"{label}: saved ASv6.48 render hash mismatch")
        note = by_note_id[entry["note_id"]]
        if note["text"] != entry["text"]:
            raise ValueError(f"{label}: note text mismatch between saved sources")
        cases.append({
            "id": label, "note_id": entry["note_id"], "text": entry["text"],
            "prompt": content,
            "astra_subjects": [
                {"number": s["number"], "context": s["context"],
                 "subject": s["subject"]} for s in note["subjects"]],
        })
    muse = {}
    for label in SP_NOTES:
        record = read(sp_source(label) / "result.json")
        muse[label] = json.loads(record["raw_text"])["subjects"]
    for case in cases:
        case["muse_subjects"] = muse[case["id"]]
    return cases, read(SP_MANIFEST)["response_schema"]


def mask_input(cases):
    notes, seen = [], {}
    for case in cases:
        entry = seen.setdefault(case["note_id"], {
            "note_id": case["note_id"], "text": case["text"], "subjects": []})
        entry["subjects"].append(case["subject"])
    return {"schema_version": 1, "notes": list(notes or seen.values())}


def prepare():
    check_pins()
    decoder = decoder_module()
    cases = dev_cases(decoder) + fresh_cases(decoder)
    if len(cases) != sum(STRATA.values()) + 18:
        raise ValueError("unexpected case count")
    repeat_ids = sorted(random.Random(SEED + 1).sample(
        [case["id"] for case in cases], REPEAT_TRIALS))
    sp, sp_schema = sp_cases()
    save(ROOT / "cases.json", {"mask_cases": cases, "repeat_ids": repeat_ids})
    save(ROOT / "sp-cases.json", sp)
    t1 = cases
    t2 = [case for case in cases if case["id"] in set(repeat_ids)]
    save(ROOT / "mask-input-t1.json", mask_input(t1))
    save(ROOT / "mask-input-t2.json", mask_input(t2))
    order1 = [(case, index) for index, case in enumerate(t1)]
    order2 = [(case, index) for index, case in enumerate(t2)]
    jobs = []
    for candidate in CANDIDATES:
        for trial, order, items in (("t1", order1, t1), ("t2", order2, t2)):
            name = f"{candidate['name']}-mp-{trial}"
            config = {
                "schema_version": 1,
                "runner_binary": str(REPO / "sse_multivector/run-model.sh"),
                "provider": PROVIDER,
                "auth_file": None,
                "input_path": str(ROOT / f"mask-input-{trial}.json"),
                "prompt_path": str(PROMPT),
                "run_directory": str(run_directory(name)),
                "model": candidate["model"],
                "reasoning_effort": candidate["reasoning_effort"],
                "timeout_seconds": TIMEOUT_SECONDS,
                "concurrency": CONCURRENCY,
                "mask_format": "word_positions",
                "output_schema": read(SCHEMA),
            }
            save(config_path(name), config)
            _, metadata, _ = pipeline._load_mask_batch(config_path(name))
            mapping = {entry["item_id"]: items[index]["id"]
                       for index, entry in enumerate(metadata["items"])}
            jobs.append({"run": name, "candidate": candidate["name"],
                         "trial": trial, "cases": [c["id"] for c in items],
                         "item_to_case": mapping})
    sp_config = {
        "schema_version": 1,
        "runner_binary": str(REPO / "sse_multivector/run-model.sh"),
        "provider": PROVIDER,
        "auth_file": None,
        "run_directory": str(run_directory("mimo-high-sp")),
        "model": "xiaomi/mimo-v2.6-pro",
        "reasoning_effort": "high",
        "timeout_seconds": TIMEOUT_SECONDS,
        "concurrency": 6,
        "output_schema": sp_schema,
        "prompts": [{"prompt_id": case["id"], "text": case["prompt"]} for case in sp],
    }
    save(config_path("mimo-high-sp"), sp_config)
    pipeline.PromptRunnerConfig.load(config_path("mimo-high-sp"))
    plan = {
        "experiment": EXPERIMENT,
        "scope": "SP/MP teacher-parity round (teacher selection, SP + MP scope). "
                 "MPv3.43 and ASv6.48 unchanged and byte-identical across arms. "
                 "One trial per case per candidate plus a predeclared 15-case "
                 "repeat subset; saved Astra outputs are the third arm with zero "
                 "Astra calls. Blind scoring packets carry no arm identity.",
        "seed": SEED,
        "strata": STRATA,
        "repeat_ids": repeat_ids,
        "mask_cases": len(cases),
        "sp_notes": list(SP_NOTES),
        "parity_rule": PARITY_RULE,
        "mask_rubric": MASK_RUBRIC,
        "sp_rubric": SP_RUBRIC,
        "candidates": list(CANDIDATES),
        "arms": ["astra-low (saved)", "muse-high", "mimo-high"],
        "jobs": jobs,
        "prompt_version": PROMPT_VERSION,
        "prompt_status": PROMPT_STATUS,
        "sp_prompt_version": SP_PROMPT_VERSION,
        "sp_prompt_status": SP_PROMPT_STATUS,
    }
    save(ROOT / "plan.json", plan)
    evidence = [ROOT / name for name in (
        "study.py", "cases.json", "sp-cases.json", "mask-input-t1.json",
        "mask-input-t2.json", "plan.json",
    )] + [config_path(f"{c['name']}-mp-{t}") for c in CANDIDATES
          for t in ("t1", "t2")] + [config_path("mimo-high-sp")] + list(pinned_inputs())
    save(ROOT / "input-hashes.json", {str(path): digest(path) for path in evidence})
    print(json.dumps({"mask_calls_per_candidate": len(cases) + len(t2),
                      "sp_calls_mimo": len(sp), "model_calls": 0}))


def collect_mask_run(name, cases_by_id, decoder, suffix=""):
    config, metadata, _ = pipeline._load_mask_batch(config_path(name))
    manifest = read(run_directory(name) / "manifest.json")
    records = [json.loads(line) for line in
               (run_directory(name) / "results.jsonl").read_text().splitlines()]
    by_id = {job.prompt_id: job for job in config.prompts}
    grouped = {}
    for record in records:
        item_id = record.get("job_key", "").removeprefix("prompt:")
        if record.get("execution") == "cross_run_reuse":
            raise ValueError(f"{name}:{item_id}: reused answer, not a fresh send")
        grouped.setdefault(item_id, []).append(record)
    rows = {}
    for item_id, attempts in grouped.items():
        succeeded = [r for r in attempts if r.get("status") == "succeeded"]
        if not succeeded:
            raise ValueError(f"{name}:{item_id}: no successful attempt")
        record = succeeded[-1]
        pipeline.validate_prompt_receipt(
            dataclasses.replace(config, prompts=(by_id[item_id],)), manifest, record)
        for other in attempts:
            if other is not record and (
                    other.get("prompt_sha256") != record.get("prompt_sha256")
                    or other.get("request_sha256") != record.get("request_sha256")):
                raise ValueError(f"{name}:{item_id}: failed attempt identity differs")
        entry = next(e for e in metadata["items"] if e["item_id"] == item_id)
        matches = [case_id for case_id, case in cases_by_id.items()
                   if case["note_id"] == entry["note_id"]
                   and case["subject"] == entry["subject"]]
        if len(matches) != 1:
            raise ValueError(
                f"{name}:{item_id}: expected exactly one case for this note and "
                f"subject, found {matches}")
        case_id = matches[0]
        case = cases_by_id[case_id]
        row = {
            "attempts": len(attempts),
            "failed_attempts_without_usage": len(attempts) - len(succeeded),
            "usage": record.get("usage"),
            "elapsed_seconds": record.get("elapsed_seconds"),
        }
        try:
            response, ranges = decoder.decode(record["final_output_raw"], case["text"])
        except ValueError as failure:
            row.update(spans=None, decode_error=str(failure))
        else:
            row.update(spans=[[r["start"], r["end"]] for r in ranges])
        rows[case_id + suffix] = row
    return rows


def collect_sp_run(decoder):
    rows = {}
    for name in ("mimo-high-sp", "mimo-high-sp-retry"):
        if not (run_directory(name) / "results.jsonl").exists():
            continue
        config = pipeline.PromptRunnerConfig.load(config_path(name))
        manifest = read(run_directory(name) / "manifest.json")
        records = [json.loads(line) for line in
                   (run_directory(name) / "results.jsonl").read_text().splitlines()]
        by_id = {job.prompt_id: job for job in config.prompts}
        grouped = {}
        for record in records:
            label = record.get("job_key", "").removeprefix("prompt:")
            if record.get("execution") == "cross_run_reuse":
                raise ValueError(f"{name}:{label}: reused answer, not a fresh send")
            grouped.setdefault(label, []).append(record)
        for label, attempts in grouped.items():
            succeeded = [r for r in attempts if r.get("status") == "succeeded"]
            if not succeeded or label in rows:
                continue
            record = succeeded[-1]
            pipeline.validate_prompt_receipt(
                dataclasses.replace(config, prompts=(by_id[label],)), manifest, record)
            for other in attempts:
                if other is not record and (
                        other.get("prompt_sha256") != record.get("prompt_sha256")
                        or other.get("request_sha256") != record.get("request_sha256")):
                    raise ValueError(
                        f"{name}:{label}: failed attempt identity differs")
            rows[label] = {
                "subjects": json.loads(record["final_output_raw"])["subjects"],
                "usage": record.get("usage"),
                "elapsed_seconds": record.get("elapsed_seconds"),
                "attempts": len(attempts),
                "failed_attempts_without_usage": len(attempts) - len(succeeded),
                "run": name,
            }
    return rows


def collect():
    check_pins()
    collector_changes = {}
    for path, expected in read(ROOT / "input-hashes.json").items():
        actual = digest(Path(path))
        if actual == expected:
            continue
        if Path(path) == ROOT / "study.py":
            collector_changes[path] = {
                "sha256_at_prepare": expected, "sha256_at_collect": actual,
                "reason": "collect binds items to cases by (note_id, subject) "
                         "identity after prepare's order-based item_to_case "
                         "mapping proved wrong (note-grouped runner order "
                         "differs from flat case order); requests and prompts "
                         "are unchanged and were always correct",
            }
            continue
        raise ValueError("pinned input changed: " + path)
    decoder = decoder_module()
    saved = read(ROOT / "cases.json")
    cases = {case["id"]: case for case in saved["mask_cases"]}
    collected = {"mask": {}, "sp": {}}
    for candidate in CANDIDATES:
        for trial, suffix in (("t1", ""), ("t2", "#t2")):
            name = f"{candidate['name']}-mp-{trial}"
            collected["mask"].setdefault(candidate["name"], {}).update(
                collect_mask_run(name, cases, decoder, suffix))
    collected["sp"]["mimo-high"] = collect_sp_run(decoder)
    totals = {}
    for candidate, rows in collected["mask"].items():
        usage = {"input": 0, "cacheRead": 0, "output": 0, "reasoning": 0,
                 "cost_usd": 0.0, "failed_attempts_without_usage": 0}
        for row in rows.values():
            u = row["usage"] or {}
            usage["input"] += u.get("input") or 0
            usage["cacheRead"] += u.get("cacheRead") or 0
            usage["output"] += u.get("output") or 0
            usage["reasoning"] += u.get("reasoning") or 0
            usage["cost_usd"] += ((u.get("cost") or {}).get("total")) or 0
            usage["failed_attempts_without_usage"] += (
                row["failed_attempts_without_usage"])
        totals[candidate] = usage
    sp_usage = {"input": 0, "output": 0, "reasoning": 0, "cost_usd": 0.0}
    for row in collected["sp"]["mimo-high"].values():
        u = row["usage"] or {}
        sp_usage["input"] += u.get("input") or 0
        sp_usage["output"] += u.get("output") or 0
        sp_usage["reasoning"] += u.get("reasoning") or 0
        sp_usage["cost_usd"] += ((u.get("cost") or {}).get("total")) or 0
    results = {
        "experiment": EXPERIMENT,
        "collector_changes": collector_changes,
        "mask": collected["mask"],
        "sp": collected["sp"],
        "mask_totals": totals,
        "sp_totals_mimo_high": sp_usage,
        "mask_cases": saved["mask_cases"],
        "repeat_ids": saved["repeat_ids"],
    }
    save(ROOT / "results.json", results)
    print(json.dumps({"mask_totals": totals, "sp_totals_mimo_high": sp_usage},
                     indent=2))


RUBRIC = {"mask": MASK_RUBRIC, "sp": SP_RUBRIC}


def packets():
    results = read(ROOT / "results.json")
    items = []
    for case in results["mask_cases"]:
        arms = {"astra-low": {"spans": case["reference_spans"]}}
        for candidate in ("mimo-high", "muse-high"):
            arms[candidate] = {"spans": results["mask"][candidate][case["id"]]["spans"],
                               "decode_error": results["mask"][candidate][case["id"]].get("decode_error")}
            if case["id"] in set(results["repeat_ids"]):
                again = results["mask"][candidate][case["id"] + "#t2"]
                arms[f"{candidate}#t2"] = {"spans": again["spans"],
                                          "decode_error": again.get("decode_error")}
        for arm, payload in arms.items():
            spans = payload["spans"]
            if spans:
                answer = marked(case["text"], spans)
            elif spans is not None:
                answer = "(empty mask)"
            else:
                answer = "(output failed mechanical validation)"
            items.append({
                "kind": "mask", "case_id": case["id"], "arm": arm,
                "post": case["text"], "subject": case["subject"], "answer": answer,
            })
    sp = read(ROOT / "sp-cases.json")
    excluded = []
    for case in sp:
        mimo = results["sp"]["mimo-high"].get(case["id"])
        if not mimo or not mimo.get("subjects"):
            excluded.append(case["id"])
            continue
        arms = {"astra-low": case["astra_subjects"], "muse-high": case["muse_subjects"],
                "mimo-high": mimo["subjects"]}
        for arm, subjects in arms.items():
            items.append({
                "kind": "sp", "case_id": case["id"], "arm": arm,
                "post": case["text"],
                "answer": [f"{s['number']} {s['subject']} — {s['context']}"
                           for s in subjects],
            })
    rng = random.Random(SEED + 2)
    rng.shuffle(items)
    blind = {}
    packet_a, packet_b = [], []
    for index, item in enumerate(items):
        slot = f"S{index + 1:03d}"
        blind[slot] = {"arm": item["arm"], "case_id": item["case_id"],
                       "kind": item["kind"]}
        entry = {"slot": slot, "kind": item["kind"], "post": item["post"],
                 "subject": item.get("subject"), "answer": item["answer"],
                 "rubric": RUBRIC[item["kind"]]}
        (packet_a if index % 2 == 0 else packet_b).append(entry)
        if index < PACKET_OVERLAP:
            (packet_b if index % 2 == 0 else packet_a).append(entry)
    save(ROOT / "blind-map.json", blind)
    save(ROOT / "packet-a.json", {"items": packet_a})
    save(ROOT / "packet-b.json", {"items": packet_b})
    print(json.dumps({"items": len(items), "packet_a": len(packet_a),
                      "packet_b": len(packet_b), "overlap": PACKET_OVERLAP,
                      "excluded_sp_cases": excluded}))


def report():
    blind = read(ROOT / "blind-map.json")
    scores = {}
    for name in ("score-a.json", "score-b.json"):
        path = ROOT / name
        if not path.exists():
            continue
        for entry in read(path)["scores"]:
            scores.setdefault(entry["slot"], {})[name] = entry["verdict"]
    rates = {}
    for slot, verdicts in scores.items():
        meta = blind[slot]
        arm = meta["arm"].split("#")[0]
        verdict = verdicts.get("score-a.json") or verdicts.get("score-b.json")
        entry = rates.setdefault((meta["kind"], arm), {"n": 0, "acceptable": 0})
        entry["n"] += 1
        entry["acceptable"] += verdict == "acceptable"
    summary = [{"kind": kind, "arm": arm, "n": v["n"],
                "acceptable_rate": v["acceptable"] / v["n"]}
               for (kind, arm), v in sorted(rates.items())]
    results = read(ROOT / "results.json")
    format_failures = {
        candidate: sorted(key for key, row in rows.items()
                          if row.get("decode_error"))
        for candidate, rows in results["mask"].items()}
    print(json.dumps({"rates": summary, "parity_rule": PARITY_RULE,
                      "format_failures": format_failures,
                      "scored_slots": len(scores)}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect,
     "packets": packets, "report": report}[sys.argv[1]]()
