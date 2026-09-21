"""GPRv1: partial repetition at two subject levels, with unchanged SSE code."""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BREAD = HERE.parent / "bread-partial-repetition-sse-v1"
spec = importlib.util.spec_from_file_location("bread_study", BREAD / "study.py")
bpr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bpr)
ROOT = bpr.ROOT
CASES = HERE.parent / "mpv3.31-probe-v1/cases.json"
SAVED = HERE.parent / "mpv3.32-vs-mpv3.33-v1/comparison.json"

# Fixed before inference. General/other-instrument surface forms are sensitivity
# checks, not statistically independent examples or gold hierarchy categories.
ANCHORS = {
    "general": ["Guitars.", "The guitar as a musical instrument.", "Guitars in general."],
    "other_instrument": ["Violins.", "The violin as a musical instrument.", "Violins in general."],
    "detailed": [
        "Retuning a guitar when a capo is attached or removed.",
        "Readjusting a guitar's tuning after putting on or taking off its capo.",
        "Tuning a guitar again whenever a capo is added or removed.",
    ],
    "other_trigger": [
        "Retuning a guitar when its strings are replaced.",
        "Readjusting a guitar's tuning after replacing its strings.",
        "Tuning a guitar again whenever new strings are fitted.",
    ],
    "without_retuning": [
        "Attaching or removing a capo on a guitar without retuning it.",
        "Putting on or taking off a guitar's capo without readjusting the tuning.",
        "Adding or removing a capo without tuning the guitar again.",
    ],
}


def prepare(output):
    if (output / "inputs.json").exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    cases = {r["id"]: r for r in bpr.read(CASES) if r["id"] in ("T03", "T04")}
    saved = {r["id"]: r for r in bpr.read(SAVED)["results"]
             if r["version"] == "MPv3.32" and r["id"] in cases}
    text = cases["T03"]["text"]
    assert text == cases["T04"]["text"]
    assert bpr.digest(text.encode()) == cases["T03"]["source_text_sha256"]
    full = {key: [[r["start"], r["end"]] for r in saved[key]["ranges"]] for key in saved}
    for key, ranges in full.items():
        assert [text.encode()[a:b].decode() for a, b in ranges] == saved[key]["fragments"]
    # Occurrence in the retuning clause is the common core for BOTH levels.
    primary = bpr.span(text, "retune your guitar every time", "guitar")
    assert primary == full["T03"][1]
    extras = [r for r in full["T03"] if r != primary]
    additions = {"core": [], "hashtag": [extras[-1]], "prose": extras[:-1], "all": extras}
    cores = {"broad": [primary], "detailed": [r for r in full["T04"] if r not in extras]}
    variants, subjects = {}, []

    def add(name, level, ranges, single=False):
        ranges = sorted(ranges)
        sid = bpr.digest(("GPRv1/" + name).encode())[:16]
        subjects.append({"subject_id": sid, "byte_spans": ranges})
        variants[name] = {"subject_id": sid, "level": level, "single_mention": single,
                          "byte_spans": ranges,
                          "fragments": [text.encode()[a:b].decode() for a, b in ranges]}

    for level, core in cores.items():
        for treatment, extra in additions.items():
            add(f"{level}_{treatment}", level, core + extra, level == "broad" and treatment == "core")
    for index, occurrence in enumerate(full["T03"], 1):
        if occurrence != primary:
            add(f"broad_single_{index}", "broad", [occurrence], True)
    assert variants["broad_all"]["byte_spans"] == full["T03"]
    assert variants["detailed_all"]["byte_spans"] == full["T04"]
    notes = [{"note_id": cases["T03"]["note_id"], "text": text, "subjects": subjects}]
    anchors = []
    for family, texts in ANCHORS.items():
        for index, anchor in enumerate(texts):
            sid = bpr.digest(f"GPRv1/{family}/{index}".encode())[:16]
            notes.append({"note_id": bpr.digest(anchor.encode()), "text": anchor, "subjects": [
                {"subject_id": sid, "byte_spans": [[0, len(anchor.encode())]]}]})
            anchors.append({"family": family, "index": index, "text": anchor, "subject_id": sid})
    protected = [CASES, SAVED, HERE / "study.py", HERE / "PLAN.md", HERE / "run-local.sh",
                 BREAD / "study.py", BREAD / "run/comparison.json", bpr.ENCODER,
                 ROOT / "sse_multivector/worker.py"]
    inputs = {"version": "GPRv1", "text": text, "note_id": cases["T03"]["note_id"],
              "subjects": {k: {"subject": c["subject"], "origin": c["subject_origin"]} for k, c in cases.items()},
              "source_mask_version": "MPv3.32", "saved_broad_ranges": full["T03"],
              "saved_detailed_ranges": full["T04"], "variants": variants, "anchors": anchors,
              "protected_sha256": {str(p): bpr.sha(p) for p in protected}}
    bpr.save(output / "inputs.json", inputs)
    bpr.save(output / "worker-request.json", {"schema_version": 1, "proposal_sha256": bpr.sha(output / "inputs.json"), "notes": notes})
    bpr._load_request(output / "worker-request.json")
    config = bpr.read(BREAD / "run/worker-config.json")
    config.update(request_path=str(output / "worker-request.json"),
                  request_sha256=bpr.sha(output / "worker-request.json"), output_path=str(output / "result"))
    bpr.save(output / "worker-config.json", config)
    return inputs


def collect(output):
    inputs = bpr.read(output / "inputs.json")
    for name, expected in inputs["protected_sha256"].items():
        assert bpr.sha(Path(name)) == expected, f"changed protected input: {name}"
    rows, receipt = bpr.vectors(output / "result")
    assert receipt["request_sha256"] == bpr.sha(output / "worker-request.json")
    assert receipt["proposal_sha256"] == bpr.sha(output / "inputs.json")
    _, request = bpr._load_request(output / "worker-request.json")
    assert [(r["note_id"], r["subject_id"]) for r in receipt["rows"]] == [
        (n.note_id, s.subject_id) for n in request for s in n.subjects]
    previous = bpr.read(BREAD / "run/comparison.json")
    assert previous["parity_passed"] and receipt["runtime"] == previous["runtime"]
    previous_receipt = bpr.read(BREAD / "run/result/worker-receipt.json")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "device", "note_batch_size"):
        assert receipt[key] == previous_receipt[key]
    metadata = {r["subject_id"]: r for r in receipt["rows"]}
    result = {"version": "GPRv1", "runtime_matches_checked_BPRv1": True,
              "runtime": receipt["runtime"], "variants": {}}
    for name, variant in inputs["variants"].items():
        sid, level = variant["subject_id"], variant["level"]
        target = "general" if level == "broad" else "detailed"
        contrasts = ["other_instrument", "detailed"] if level == "broad" else ["general", "other_trigger", "without_retuning"]
        scores = {family: [bpr.cosine(rows[sid], rows[a["subject_id"]])
                           for a in inputs["anchors"] if a["family"] == family] for family in ANCHORS}
        means = {k: sum(v)/len(v) for k, v in scores.items()}
        result["variants"][name] = {"level": level, "selected_tokens": len(metadata[sid]["selected_token_indices"]),
            "scores": scores, "means": means,
            "target_minus": {k: means[target]-means[k] for k in contrasts},
            "matched_wins": {k: sum(a>b for a,b in zip(scores[target], scores[k], strict=True)) for k in contrasts},
            "ranking": sorted([(a["family"], a["index"], bpr.cosine(rows[sid], rows[a["subject_id"]]))
                               for a in inputs["anchors"]], key=lambda r: -r[2])}
    for name, variant in result["variants"].items():
        base = result["variants"][variant["level"] + "_core"]
        variant["delta_mean"] = {k: v-base["means"][k] for k,v in variant["means"].items()}
        variant["delta_margin"] = {k: v-base["target_minus"][k] for k,v in variant["target_minus"].items()}
    bpr.save(output / "comparison.json", result)
    print(json.dumps({k: {f:v[f] for f in ("selected_tokens", "means", "target_minus", "matched_wins")}
                      for k,v in result["variants"].items()}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "collect"])
    parser.add_argument("--output", type=Path, default=HERE / "run")
    args = parser.parse_args()
    globals()[args.command](args.output.resolve())
