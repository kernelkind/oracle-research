"""PRSv1: contextual pronoun additions through the unchanged production SSE worker."""
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
SOURCE = HERE.parent / "mpv3.43-nonfood-v1"
GUITAR = HERE.parent / "guitar-partial-repetition-sse-v1"

# Fixed before inference. Contextual subjects are related, not absolute negatives.
SPEC = {
    "NF01-001": {
        "pronoun_context": "page, they should", "pronoun": "they",
        "target": ["Open source software projects", "Projects for open-source software", "Software projects that are open source"],
        "contrast": ["Closed source software projects", "Projects for closed-source software", "Software projects that are closed source"],
        "contextual": ["Donations to open source software projects"],
    },
    "NF02-006": {
        "pronoun_context": "work you to death", "pronoun": "you",
        "target": ["Employees", "People working for an employer", "Employed workers"],
        "contrast": ["Employers", "People who employ workers", "Those who hire employees"],
        "contextual": ["Overworked employees"],
    },
}


def prepare(output):
    if (output / "inputs.json").exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    cases = {c["id"]: c for c in bpr.read(SOURCE / "cases.json")}
    saved = {r["id"]: r for r in bpr.read(SOURCE / "comparison.json")["results"]}
    inputs, notes, anchor_notes = [], [], []
    for cid, definition in SPEC.items():
        case, result = cases[cid], saved[cid]
        text, variants, subjects, anchors = case["text"], {}, [], []
        assert case["subject"] == definition["target"][0]
        assert bpr.digest(text.encode()) == case["source_text_sha256"]
        current = [[len(text[:r["start"]].encode()), len(text[:r["end"]].encode())] for r in result["ranges"]]
        assert [text.encode()[a:b].decode() for a, b in current] == result["fragments"]
        pronoun = bpr.span(text, definition["pronoun_context"], definition["pronoun"])
        for name, spans in {"current": current, "with_pronoun": sorted(current + [pronoun]),
                            "pronoun_only": [pronoun], "full_post": [[0, len(text.encode())]]}.items():
            sid = bpr.digest(f"PRSv1/{cid}/{name}".encode())[:16]
            subjects.append({"subject_id": sid, "byte_spans": spans})
            variants[name] = {"subject_id": sid, "byte_spans": spans,
                              "fragments": [text.encode()[a:b].decode() for a, b in spans]}
        notes.append({"note_id": case["note_id"], "text": text, "subjects": subjects})
        for family in ("target", "contrast", "contextual"):
            for i, anchor in enumerate(definition[family]):
                sid = bpr.digest(f"PRSv1/{cid}/{family}/{i}".encode())[:16]
                anchor_notes.append({"note_id": bpr.digest(anchor.encode()), "text": anchor,
                                     "subjects": [{"subject_id": sid, "byte_spans": [[0, len(anchor.encode())]]}]})
                anchors.append({"family": family, "index": i, "text": anchor, "subject_id": sid})
        inputs.append({"id": cid, "note_id": case["note_id"], "text": text, "subject": case["subject"],
                       "saved_fragments": result["fragments"], "variants": variants, "anchors": anchors})
    protected = [SOURCE / "cases.json", SOURCE / "comparison.json", HERE / "study.py", HERE / "plan.json",
                 HERE / "run-local.sh", HERE / "test_study.py", BREAD / "study.py", BREAD / "run/comparison.json",
                 GUITAR / "run/result/worker-receipt.json", bpr.ENCODER, ROOT / "sse_multivector/worker.py"]
    value = {"version": "PRSv1", "cases": inputs, "protected_sha256": {str(p): bpr.sha(p) for p in protected}}
    bpr.save(output / "inputs.json", value)
    bpr.save(output / "worker-request.json", {"schema_version": 1, "proposal_sha256": bpr.sha(output / "inputs.json"),
                                              "notes": notes + anchor_notes})
    bpr._load_request(output / "worker-request.json")
    config = bpr.read(GUITAR / "run/worker-config.json")
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
    prior = bpr.read(GUITAR / "run/result/worker-receipt.json")
    assert bpr.read(BREAD / "run/comparison.json")["parity_passed"]
    for field in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "device", "note_batch_size", "runtime"):
        assert receipt[field] == prior[field], (field, receipt[field], prior[field])
    metadata = {r["subject_id"]: r for r in receipt["rows"]}
    results = []
    for case in inputs["cases"]:
        variants = {}
        for name, variant in case["variants"].items():
            vector = vectors[variant["subject_id"]]
            scores = {f: [bpr.cosine(vector, vectors[a["subject_id"]]) for a in case["anchors"] if a["family"] == f]
                      for f in ("target", "contrast", "contextual")}
            means = {f: sum(values)/len(values) for f, values in scores.items()}
            variants[name] = {"scores": scores, "means": means,
                "matched_margins": [t-c for t, c in zip(scores["target"], scores["contrast"], strict=True)],
                "mean_target_minus_contrast": means["target"]-means["contrast"],
                "cosine_to_current": bpr.cosine(vector, vectors[case["variants"]["current"]["subject_id"]]),
                "selected_tokens": len(metadata[variant["subject_id"]]["selected_token_indices"])}
        before, after = variants["current"], variants["with_pronoun"]
        results.append({"id": case["id"], "subject": case["subject"], "anchors": case["anchors"], "variants": variants,
            "target_deltas": [a-b for a,b in zip(after["scores"]["target"],before["scores"]["target"],strict=True)],
            "delta_mean_target": after["means"]["target"]-before["means"]["target"],
            "delta_mean_margin": after["mean_target_minus_contrast"]-before["mean_target_minus_contrast"]})
    value = {"version": "PRSv1", "row_count": receipt["row_count"], "runtime_matches_parity_checked_prior": True,
             "runtime": receipt["runtime"], "cases": results}
    bpr.save(output / "comparison.json", value)
    print(json.dumps(value, indent=2))
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "collect"])
    parser.add_argument("--output", type=Path, default=HERE / "run")
    args = parser.parse_args()
    globals()[args.command](args.output.resolve())
