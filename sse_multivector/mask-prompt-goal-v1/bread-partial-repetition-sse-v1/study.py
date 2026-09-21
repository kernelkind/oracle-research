"""BPRv1: fixed-note partial-repetition intervention through the existing SSE worker."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from sse_multivector.worker import _load_request

SOURCE = HERE.parent / "mpv3.34-fresh-v1"
CASES = SOURCE / "cases.json"
PARITY = ROOT / "sse_multivector/mask-fidelity-coffee-shop-v1"
ENCODER = ROOT / "sse_multivector/fine-segmentation-suite-encoder-v1.json"

# Hand-authored diagnostic anchors, fixed before inference; not corpus notes or gold clusters.
ANCHORS = {
    "success": [
        "I recently tried an Irish soda bread recipe and was delighted with how well it turned out.",
        "The Irish soda bread recipe I tested recently was a great success, which made me very happy.",
        "I felt really pleased because the Irish soda bread recipe I had just tried worked wonderfully.",
    ],
    "failure": [
        "I recently tried an Irish soda bread recipe and was disappointed with how badly it turned out.",
        "The Irish soda bread recipe I tested recently was a failure, which made me very unhappy.",
        "I felt really disappointed because the Irish soda bread recipe I had just tried did not work.",
    ],
    "general": ["Soda bread.", "Irish soda bread.", "Soda bread recipes."],
    "website": [
        "I recently found a high-altitude baking website and was delighted to discover it.",
        "Discovering a website about baking at high elevations made me very happy.",
        "I felt really pleased because I had just found a site for high-altitude baking.",
    ],
}


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def span(text, context, selected):
    if text.count(context) != 1 or context.count(selected) != 1:
        raise ValueError("span specification is not unique")
    start = text.index(context) + context.index(selected)
    return [len(text[:start].encode()), len(text[:start + len(selected)].encode())]


def prepare(output):
    if (output / "inputs.json").exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    case = next(row for row in read(CASES) if row["id"] == "F05")
    saved = next(row for row in read(SOURCE / "comparison.json")["results"] if row["id"] == "F05")
    text = case["text"]
    raw_text = text.encode()
    base = [[r["start"], r["end"]] for r in saved["ranges"]]
    assert [raw_text[a:b].decode() for a, b in base] == saved["fragments"]
    tags = [span(text, "#bread", "bread"), span(text, "#sodabread", "sodabread")]
    generic = [span(text, "Soda bread usually has currants", "Soda bread")]
    old = [span(text, "The soda bread I usually made", "soda bread")]
    additions = {"base": [], "tags": tags, "generic": generic,
                 "tags_generic": tags + generic, "all_bread": tags + generic + old}
    variants, subjects = {}, []
    for name, extra in additions.items():
        ranges = sorted(base + extra)
        sid = digest(("BPRv1/" + name).encode())[:16]
        subjects.append({"subject_id": sid, "byte_spans": ranges})
        variants[name] = {"subject_id": sid, "byte_spans": ranges,
                          "fragments": [raw_text[a:b].decode() for a, b in ranges],
                          "added_fragments": [raw_text[a:b].decode() for a, b in sorted(extra)]}
    # The seven saved coffee vectors are an intentional runtime parity check, not new evidence.
    notes = read(PARITY / "worker-request.json")["notes"]
    notes.append({"note_id": case["note_id"], "text": text, "subjects": subjects})
    anchors = []
    for family, texts in ANCHORS.items():
        for index, anchor in enumerate(texts):
            sid = digest(f"BPRv1/{family}/{index}".encode())[:16]
            nid = digest(anchor.encode())
            notes.append({"note_id": nid, "text": anchor, "subjects": [
                {"subject_id": sid, "byte_spans": [[0, len(anchor.encode())]]}]})
            anchors.append({"family": family, "index": index, "text": anchor, "subject_id": sid})
    protected = [CASES, SOURCE / "comparison.json", ENCODER, ROOT / "sse_multivector/worker.py",
                 PARITY / "worker-request.json", PARITY / "result/worker-receipt.json",
                 PARITY / "result/raw-vectors.f32le", HERE / "study.py", HERE / "PLAN.md"]
    inputs = {"version": "BPRv1", "source_sha256": sha(CASES),
              "subject": case["subject"], "subject_origin": case["subject_origin"],
              "note_id": case["note_id"], "text": text,
              "variants": variants, "anchors": anchors,
              "protected_sha256": {str(p): sha(p) for p in protected}}
    save(output / "inputs.json", inputs)
    request = {"schema_version": 1, "proposal_sha256": sha(output / "inputs.json"), "notes": notes}
    save(output / "worker-request.json", request)
    _load_request(output / "worker-request.json")
    encoder = read(ENCODER)
    config = {"schema_version": 1, "request_path": str(output / "worker-request.json"),
              "request_sha256": sha(output / "worker-request.json"),
              "checkpoint_path": str(ROOT / encoder["checkpoint_path"]),
              "base_model_artifact_path": str(ROOT / encoder["base_model_artifact_path"]),
              "device": "cpu", "output_path": str(output / "result")}
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "container_image", "model", "note_batch_size"):
        config[key] = encoder[key]
    save(output / "worker-config.json", config)
    return inputs


def cosine(left, right):
    norm = math.sqrt(sum(x*x for x in left) * sum(x*x for x in right))
    if norm == 0:
        raise ValueError("zero vector")
    return sum(x*y for x, y in zip(left, right, strict=True)) / norm


def vectors(path):
    receipt = read(path / "worker-receipt.json")
    raw = (path / "raw-vectors.f32le").read_bytes()
    assert digest(raw) == receipt["files"]["raw-vectors.f32le"]["sha256"]
    assert len(raw) == receipt["row_count"] * receipt["dimensions"] * 4
    rows = list(struct.iter_unpack("<" + "f" * receipt["dimensions"], raw))
    return {r["subject_id"]: v for r, v in zip(receipt["rows"], rows, strict=True)}, receipt


def collect(output):
    inputs = read(output / "inputs.json")
    for name, expected in inputs["protected_sha256"].items():
        assert sha(Path(name)) == expected, f"changed protected input: {name}"
    rows, receipt = vectors(output / "result")
    assert receipt["request_sha256"] == sha(output / "worker-request.json")
    assert receipt["proposal_sha256"] == sha(output / "inputs.json")
    _, request_notes = _load_request(output / "worker-request.json")
    assert [(r["note_id"], r["subject_id"]) for r in receipt["rows"]] == [
        (n.note_id, s.subject_id) for n in request_notes for s in n.subjects]
    old, old_receipt = vectors(PARITY / "result")
    old_meta = {r["subject_id"]: r for r in old_receipt["rows"]}
    metadata = {r["subject_id"]: r for r in receipt["rows"]}
    parity = []
    for sid, vector in old.items():
        error = max(abs(x-y) for x, y in zip(vector, rows[sid], strict=True))
        same_tokens = all(metadata[sid][field] == old_meta[sid][field] for field in (
            "selected_token_indices", "selected_token_ids", "token_count"))
        similarity = cosine(vector, rows[sid])
        parity.append({"subject_id": sid, "cosine": similarity, "max_component_error": error,
                       "same_tokenization": same_tokens,
                       "passes": same_tokens and similarity >= 1 - 1e-9 and error <= 1e-6})
    result = {"version": "BPRv1", "parity": parity, "parity_passed": all(x["passes"] for x in parity),
              "runtime": receipt["runtime"], "variants": {}}
    for name, variant in inputs["variants"].items():
        sid = variant["subject_id"]
        scores = {family: [cosine(rows[sid], rows[a["subject_id"]]) for a in inputs["anchors"]
                           if a["family"] == family] for family in ANCHORS}
        means = {family: sum(values) / len(values) for family, values in scores.items()}
        margins = {family: means["success"] - means[family] for family in ("failure", "general", "website")}
        result["variants"][name] = {
            "selected_tokens": len(metadata[sid]["selected_token_indices"]),
            "cosine_to_base": cosine(rows[sid], rows[inputs["variants"]["base"]["subject_id"]]),
            "scores": scores, "means": means, "success_minus": margins,
            "matched_success_over_failure": sum(a > b for a, b in zip(scores["success"], scores["failure"], strict=True)),
            "ranking": sorted([(a["family"], a["index"], cosine(rows[sid], rows[a["subject_id"]]))
                               for a in inputs["anchors"]], key=lambda r: -r[2]),
        }
    base = result["variants"]["base"]
    for variant in result["variants"].values():
        variant["delta_mean"] = {k: v-base["means"][k] for k, v in variant["means"].items()}
        variant["delta_margin"] = {k: v-base["success_minus"][k] for k, v in variant["success_minus"].items()}
    save(output / "comparison.json", result)
    print(json.dumps({"parity_passed": result["parity_passed"], "variants": {
        k: {key: value for key, value in v.items() if key not in ("scores", "ranking")}
        for k, v in result["variants"].items()}}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "collect"])
    parser.add_argument("--output", type=Path, default=HERE / "run")
    args = parser.parse_args()
    globals()[args.command](args.output.resolve())
