"""EDSv1: remove only the named extra detail using the unchanged SSE worker."""
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
SOURCE = HERE.parent / "mpv3.43-probe-v1"
PRIOR = HERE.parent / "pronoun-sse-v1/run"
FAMILIES = ("target", "contrast", "contextual")


def prepare(output):
    if (output / "inputs.json").exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    cases = {c["id"]: c for c in bpr.read(SOURCE / "cases.json")}
    saved = {r["id"]: r for r in bpr.read(SOURCE / "comparison.json")["results"]}
    plan = bpr.read(HERE / "plan.json")
    inputs, notes, anchors_notes = [], {}, []
    for cid, definition in plan["cases"].items():
        case, result = cases[cid], saved[cid]
        text, variants, anchors = case["text"], {}, []
        assert case["subject"] == definition["target"][0] == result["subject"]
        assert bpr.digest(text.encode()) == case["source_text_sha256"]
        assert result["format_valid"]
        current = [(r["start"], r["end"]) for r in result["ranges"]]
        assert [text[a:b] for a, b in current] == result["fragments"]
        remove = definition["remove"]
        assert text.count(remove) == 1
        start, end = text.index(remove), text.index(remove) + len(remove)
        assert sum(a <= start < end <= b for a, b in current) == 1
        removed = []
        for a, b in current:
            pieces = [(a, start), (end, b)] if a <= start < end <= b else [(a, b)]
            for left, right in pieces:
                while left < right and text[left].isspace():
                    left += 1
                while right > left and text[right-1].isspace():
                    right -= 1
                if left < right:
                    removed.append((left, right))
        note = notes.setdefault(case["note_id"], {"note_id": case["note_id"], "text": text, "subjects": []})
        assert note["text"] == text
        for name, ranges in {"current": current, "removed": removed}.items():
            sid = bpr.digest(f"EDSv1/{cid}/{name}".encode())[:16]
            spans = [[len(text[:a].encode()), len(text[:b].encode())] for a, b in ranges]
            note["subjects"].append({"subject_id": sid, "byte_spans": spans})
            variants[name] = {"subject_id": sid, "byte_spans": spans, "fragments": [text[a:b] for a, b in ranges]}
        for family in FAMILIES:
            for index, anchor in enumerate(definition[family]):
                sid = bpr.digest(f"EDSv1/{cid}/{family}/{index}".encode())[:16]
                anchors_notes.append({"note_id": bpr.digest(anchor.encode()), "text": anchor,
                                      "subjects": [{"subject_id": sid, "byte_spans": [[0, len(anchor.encode())]]}]})
                anchors.append({"family": family, "index": index, "text": anchor, "subject_id": sid})
        inputs.append({"id": cid, "note_id": case["note_id"], "text": text, "subject": case["subject"],
                       "subject_origin": case["subject_origin"], "saved_fragments": result["fragments"],
                       "variants": variants, "anchors": anchors})
    protected = [SOURCE / "cases.json", SOURCE / "comparison.json", HERE / "study.py", HERE / "plan.json",
                 HERE / "run-local.sh", HERE / "test_study.py", BREAD / "study.py", BREAD / "run/comparison.json",
                 PRIOR / "result/worker-receipt.json", PRIOR / "worker-config.json", bpr.ENCODER,
                 ROOT / "sse_multivector/worker.py", HERE.parent / "mpv3.43-draft-v1/mask-prompt.md",
                 ROOT / "sse_multivector/subject-prompt-goal-v1/asv6.48/ASv6.48.md"]
    value = {"version": "EDSv1", "cases": inputs, "protected_sha256": {str(p): bpr.sha(p) for p in protected}}
    bpr.save(output / "inputs.json", value)
    bpr.save(output / "worker-request.json", {"schema_version": 1, "proposal_sha256": bpr.sha(output / "inputs.json"),
                                              "notes": list(notes.values()) + anchors_notes})
    bpr._load_request(output / "worker-request.json")
    config = bpr.read(PRIOR / "worker-config.json")
    config.update(request_path=str(output / "worker-request.json"), request_sha256=bpr.sha(output / "worker-request.json"),
                  output_path=str(output / "result"))
    bpr.save(output / "worker-config.json", config)
    return value


def collect(output):
    inputs = bpr.read(output / "inputs.json")
    for path, expected in inputs["protected_sha256"].items():
        assert bpr.sha(Path(path)) == expected, path
    vectors, receipt = bpr.vectors(output / "result")
    assert receipt["request_sha256"] == bpr.sha(output / "worker-request.json")
    assert receipt["proposal_sha256"] == bpr.sha(output / "inputs.json")
    _, request = bpr._load_request(output / "worker-request.json")
    assert [(r["note_id"], r["subject_id"]) for r in receipt["rows"]] == [(n.note_id, s.subject_id) for n in request for s in n.subjects]
    prior = bpr.read(PRIOR / "result/worker-receipt.json")
    assert bpr.read(BREAD / "run/comparison.json")["parity_passed"]
    for field in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "device", "note_batch_size", "runtime"):
        assert receipt[field] == prior[field], field
    assert inputs["protected_sha256"][str(ROOT / "sse_multivector/worker.py")] == bpr.read(PRIOR / "inputs.json")["protected_sha256"][str(ROOT / "sse_multivector/worker.py")]
    metadata = {r["subject_id"]: r for r in receipt["rows"]}
    results = []
    for case in inputs["cases"]:
        variants = {}
        for name, variant in case["variants"].items():
            vector = vectors[variant["subject_id"]]
            scores = {f: [bpr.cosine(vector, vectors[a["subject_id"]]) for a in case["anchors"] if a["family"] == f]
                      for f in FAMILIES}
            means = {f: sum(values)/len(values) for f, values in scores.items()}
            meta = metadata[variant["subject_id"]]
            variants[name] = {"scores": scores, "means": means,
                "matched_margins": [t-c for t, c in zip(scores["target"], scores["contrast"], strict=True)],
                "mean_target_minus_contrast": means["target"]-means["contrast"],
                "cosine_to_current": bpr.cosine(vector, vectors[case["variants"]["current"]["subject_id"]]),
                "selected_token_indices": meta["selected_token_indices"], "selected_token_ids": meta["selected_token_ids"]}
        before, after = variants["current"], variants["removed"]
        assert set(after["selected_token_indices"]) < set(before["selected_token_indices"])
        results.append({"id": case["id"], "subject": case["subject"], "anchors": case["anchors"], "variants": variants,
            "target_deltas": [a-b for a, b in zip(after["scores"]["target"], before["scores"]["target"], strict=True)],
            "delta_mean_target": after["means"]["target"]-before["means"]["target"],
            "delta_mean_margin": after["mean_target_minus_contrast"]-before["mean_target_minus_contrast"]})
    value = {"version": "EDSv1", "row_count": receipt["row_count"], "runtime_matches_parity_checked_prior": True,
             "runtime": receipt["runtime"], "cases": results}
    bpr.save(output / "comparison.json", value)
    print(json.dumps({"rows": receipt["row_count"], "cases": [{k: c[k] for k in
          ("id", "subject", "target_deltas", "delta_mean_target", "delta_mean_margin")} for c in results]}, indent=2))
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "collect"])
    parser.add_argument("--output", type=Path, default=HERE / "run")
    args = parser.parse_args()
    globals()[args.command](args.output.resolve())
