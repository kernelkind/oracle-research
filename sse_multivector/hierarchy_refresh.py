"""Rebuild the fixed 100-post collection without mask-membership expansion.

Saved-batch execution remains in extraction_pipeline. This module prepares and
collects immutable experiment artifacts; it never repairs generated semantics.
"""
import argparse
from dataclasses import replace
import hashlib
import json
import math
import struct
import subprocess
import sys
import time
from pathlib import Path

from . import extraction_pipeline as pipeline

ROOT = Path(__file__).resolve().parent.parent
SSE = ROOT / "sse_multivector"
DEFAULT = SSE / "hierarchy-refresh-v1"
AS = SSE / "subject-prompt-goal-v1/asv6.48/ASv6.48.md"
MP = SSE / "mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md"
TITLE = SSE / "hdbv2-node-description-probe-v21/prompt.txt"
SOURCE = SSE / "real-note-fine-segmentation-v1/reviewed-input.json"
BASELINE = SSE / "navigation-research-v1/TRUE13/baseline-categories.json"


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def receipt(config_path, prompt_id):
    config = pipeline.PromptRunnerConfig.load(config_path)
    prompt = next(p for p in config.prompts if p.prompt_id == prompt_id)
    manifest = read(config.run_directory / "manifest.json")
    records = [json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines()]
    record = next(r for r in reversed(records) if r["note_id"] == prompt_id)
    pipeline.validate_prompt_receipt(replace(config, prompts=(prompt,)), manifest, record)
    if record["status"] != "succeeded":
        raise ValueError(f"unsuccessful saved subject: {prompt_id}")
    value = json.loads(record["final_output_raw"])
    seen = set()
    for entry in value["subjects"]:
        number = entry["number"]
        if number in seen or ("." in number and number.rsplit(".", 1)[0] not in seen):
            raise ValueError(f"invalid subject numbering: {prompt_id}/{number}")
        seen.add(number)
    return value["subjects"], {"config_path": str(config_path), "prompt_id": prompt_id,
        "results_path": str(config.run_directory / "results.jsonl"),
        "request_sha256": record["request_sha256"], "prompt_sha256": hashlib.sha256(prompt.text.encode()).hexdigest()}


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    if (output / "plan.json").exists():
        raise FileExistsError(output)
    if sha(AS) != "e1d5740e68b5f5c29e139ad3fbb37839f91784784aaa31b3bdbdc4a829a4bacc" or sha(MP) != "75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03":
        raise ValueError("frozen extraction prompt changed")
    original = read(SOURCE)
    posts = {n["note_id"]: n for n in original["notes"]}
    if len(posts) != 100:
        raise ValueError("expected original 100-post collection")
    seeds = {}
    directory = SSE / "subject-prompt-goal-v1/asv6.48-remaining-six-v1"
    for item in read(directory / "ten-note-sources.json")["sources"]:
        config_path = (directory / item["output_path"]).resolve().parent.parent / "config.json"
        subjects, origin = receipt(config_path, item["prompt_id"])
        cases = read(config_path.parent / "cases.json")
        case = next(c for c in cases["cases"] if c["note_id"] == item["note_id"])
        if case["text"] != posts[item["note_id"]]["text"] or cases["prompt_sha256"] != sha(AS):
            raise ValueError("saved subject source or prompt changed")
        seeds[item["note_id"]] = {"note_id": item["note_id"], "text": case["text"], "subjects": subjects, "origin": origin}
    directory = SSE / "mask-prompt-goal-v1/mpv3.43-handoff-v1"
    for post in read(directory / "posts.json"):
        subjects, origin = receipt(directory / "subject-config.json", f'N{post["selection_rank"]:03}')
        if posts[post["note_id"]]["text"] != post["text"]:
            raise ValueError("saved handoff source changed")
        seeds[post["note_id"]] = {"note_id": post["note_id"], "text": post["text"], "subjects": subjects, "origin": origin}
    config = read(SSE / "subject-prompt-goal-v1/asv6.48-remaining-six-v1/config.json")
    config.update(auth_file=None, run_directory=str(output / "subject-run"), concurrency=3,
                  prompts=[{"prompt_id": f"N{i:03}", "text": AS.read_text().rstrip() + "\n\n<post>\n" + n["text"] + "\n</post>"}
                           for i, n in enumerate(original["notes"], 1) if n["note_id"] not in seeds])
    plan = {"experiment": "HRv1", "status": "prepared", "source_posts": 100,
        "scope": "Full hierarchy, coffee/tea comparison to TRUE13 before membership expansion. No mask/category membership inference, prompt tuning, generated-title filtering or manual semantic repairs.",
        "subject_prompt": "ASv6.48", "mask_prompt": "MPv3.43", "title_prompt": "v21",
        "model": "gpt-6-astra", "reasoning_effort": "low", "new_subject_calls": len(config["prompts"]),
        "saved_subject_posts": len(seeds), "true_rule": "native complete answer; no cutoff",
        "grouping": "unchanged HDBv2 hdbscan_cross_note settings; all 100 posts",
        "limits": "Retain valid empty subjects without vectors. Keep original baseline and all generated outputs. Failures/cycles remain visible; no repairs or inference retries are authorized by this plan.",
        "protected_sha256": {str(p): sha(p) for p in (SOURCE, BASELINE, AS, MP, TITLE)}}
    save(output / "plan.json", plan)
    save(output / "source.json", original)
    save(output / "saved-subjects.json", {"schema_version": 1, "notes": list(seeds.values())})
    save(output / "subject-config.json", config)
    pipeline.PromptRunnerConfig.load(output / "subject-config.json")
    print(json.dumps({"posts": 100, "saved_subjects": len(seeds), "new_subject_calls": len(config["prompts"])}))


def verify(output):
    for path, digest in read(output / "plan.json")["protected_sha256"].items():
        if sha(path) != digest:
            raise ValueError(f"protected input changed: {path}")


def masks(output):
    verify(output)
    seeds = {n["note_id"]: n for n in read(output / "saved-subjects.json")["notes"]}
    notes = []
    for i, post in enumerate(read(output / "source.json")["notes"], 1):
        if post["note_id"] in seeds:
            entry = seeds[post["note_id"]]
        else:
            subjects, origin = receipt(output / "subject-config.json", f"N{i:03}")
            entry = {"note_id": post["note_id"], "text": post["text"], "subjects": subjects, "origin": origin}
        notes.append(entry)
    save(output / "subjects.json", {"schema_version": 1, "notes": notes})
    old = read(SSE / "mask-prompt-goal-v1/mpv3.43-probe-v1/config.json")
    config = {k: old[k] for k in ("schema_version", "runner_binary", "provider", "auth_file", "model", "reasoning_effort", "timeout_seconds", "output_schema")}
    config.update(input_path=str(output / "subjects.json"), prompt_path=str(MP), run_directory=str(output / "mask-run"),
                  concurrency=3, mask_format="word_positions")
    save(output / "mask-config.json", config)
    parsed, metadata, _ = pipeline._load_mask_batch(output / "mask-config.json")
    print(json.dumps({"posts": len(notes), "subject_entries": len(parsed.prompts),
                      "distinct_requests": len({p.text for p in parsed.prompts})}))


def encode_inputs(source, checks):
    """Preserve every heading; only exact nonempty masks enter the encoder."""
    checks = {c["item_id"]: c for c in checks}
    request, vectors, notes, preserved = [], [], [], []
    counter = 0
    for index, post in enumerate(source["notes"], 1):
        short = f"N{index:03}"
        notes.append({"note_id": post["note_id"], "short_id": short})
        distinct, entries = {}, []
        for entry in post["subjects"]:
            counter += 1
            check = checks[f"M{counter:03}"]
            if check["status"] != "valid":
                raise ValueError(f"invalid mask M{counter:03}; never repair or silently omit")
            ranges = check["ranges"]
            text = post["text"]
            spans = [[len(text[:r["start"]].encode()), len(text[:r["end"]].encode())] for r in ranges]
            fragments = [text[r["start"]:r["end"]] for r in ranges]
            record = {**entry, "id": f"M{counter:03}", "byte_spans": spans, "fragments": fragments,
                      "semantic_status": "generated, not independently approved", "diagnostics": check.get("diagnostics")}
            entries.append(record)
            if not spans:
                continue
            key = tuple(map(tuple, spans))
            if key not in distinct:
                identifier = hashlib.sha256(json.dumps([post["note_id"], text, spans], ensure_ascii=False).encode()).hexdigest()
                row = {"vector_id": identifier, "worker_subject_id": identifier[:16],
                       "note_id": post["note_id"], "note_short_id": short, "byte_spans": spans,
                       "fragments": fragments, "subject_entries": [], "short_id": f"V{len(vectors)+1:04}"}
                distinct[key] = row
                vectors.append(row)
            distinct[key]["subject_entries"].append(record)
        preserved.append({"note_id": post["note_id"], "text": post["text"], "subjects": entries})
        if distinct:
            request.append({"note_id": post["note_id"], "text": post["text"], "subjects": [
                {"subject_id": row["worker_subject_id"], "byte_spans": row["byte_spans"]} for row in distinct.values()]})
    if counter != len(checks):
        raise ValueError("mask count does not match subject entries")
    return request, {"schema_version": 1, "notes": notes, "vectors": vectors, "vector_count": len(vectors)}, {"schema_version": 1, "notes": preserved}


def vectors(output):
    verify(output)
    validation = read(output / "mask-run/validation.json")
    request, mapping, preserved = encode_inputs(read(output / "subjects.json"), validation["checks"])
    save(output / "masked-posts.json", preserved)
    save(output / "vector-map.json", mapping)
    save(output / "worker-request.json", {"schema_version": 1, "proposal_sha256": sha(output / "masked-posts.json"), "notes": request})
    from .worker import _load_request
    _load_request(output / "worker-request.json")
    config = read(SSE / "mask-prompt-goal-v1/pronoun-sse-v1/run/worker-config.json")
    config.update(request_path=str(output / "worker-request.json"), request_sha256=sha(output / "worker-request.json"),
                  output_path=str(output / "worker-result"))
    save(output / "worker-config.json", config)
    print(json.dumps({"source_posts": len(preserved["notes"]), "vectors": len(mapping["vectors"]),
                      "empty_masks": validation["empty"]}))


def groups(output):
    verify(output)
    from .real_note_segmentation import _validate_tokens
    receipt_value = read(output / "worker-result/worker-receipt.json")
    config = read(output / "worker-config.json")
    prior = read(SSE / "mask-prompt-goal-v1/pronoun-sse-v1/run/result/worker-receipt.json")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "device", "note_batch_size", "runtime"):
        if receipt_value[key] != prior[key]:
            raise ValueError(f"SSE identity changed: {key}")
    if receipt_value["request_sha256"] != sha(output / "worker-request.json"):
        raise ValueError("SSE request hash mismatch")
    raw = (output / "worker-result/raw-vectors.f32le").read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt_value["files"]["raw-vectors.f32le"]["sha256"]:
        raise ValueError("SSE vector hash mismatch")
    mapping = read(output / "vector-map.json")
    dims = config["model"]["dimensions"]
    rows = list(struct.iter_unpack(f"<{dims}f", raw))
    candidate = []
    normalized = bytearray()
    for ordinal, (row, measured, vector) in enumerate(zip(mapping["vectors"], receipt_value["rows"], rows, strict=True)):
        if (row["worker_subject_id"], row["note_id"]) != (measured["subject_id"], measured["note_id"]):
            raise ValueError("SSE row identity mismatch")
        _validate_tokens(measured, config["model"]["maximum_tokens"], ordinal)
        norm = math.sqrt(sum(float(v)*float(v) for v in vector))
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("invalid SSE vector")
        values = [float(v)/norm for v in vector]
        normalized.extend(struct.pack(f"<{dims}d", *values))
        candidate.append({"opaque_id": row["vector_id"], "normalized_vector": values})
    old = SSE / "real-note-fine-segmentation-v1/hdbscan-cross-note"
    proof = read(old / "replay-proof.json")
    binary = Path(proof["candidate_binary"])
    if sha(binary) != proof["candidate_binary_sha256"]:
        raise ValueError("frozen HDBSCAN binary changed")
    request = {"schema_version": 1, "candidate": "hdbscan_cross_note", "inputs": candidate,
        "source_note_ids": {r["vector_id"]: r["note_id"] for r in mapping["vectors"]},
        "source_vector_manifest_sha256": sha(output / "worker-result/worker-receipt.json"),
        "normalized_vector_sha256": hashlib.sha256(normalized).hexdigest()}
    save(output / "hdbscan-request.json", request)
    with (output / "hdbscan-response.json").open("xb") as stdout, (output / "hdbscan.stderr").open("xb") as stderr:
        subprocess.run([str(binary), str(output / "hdbscan-request.json")], stdout=stdout, stderr=stderr, check=True)
    artifact = read(output / "hdbscan-response.json")["artifact"]
    baseline = read(old / "response.json")["artifact"]
    if artifact["canonical_configuration_json"] != baseline["canonical_configuration_json"]:
        raise ValueError("HDBSCAN settings changed")
    for key in ("algorithm_version", "algorithm_implementation_source_sha256", "input_contract_version", "fine_output_selector_version"):
        if artifact["manifest"][key] != baseline["manifest"][key]:
            raise ValueError(f"HDBSCAN implementation changed: {key}")
    source = {n["note_id"]: n["text"] for n in read(output / "subjects.json")["notes"]}
    by_id = {r["vector_id"]: r for r in mapping["vectors"]}
    packets = []
    for members in artifact["result"]["fine_output"]["segments"]:
        key = "S" + hashlib.sha256("\n".join(sorted(members)).encode()).hexdigest()[:10]
        packets.append({"packet": key, "instances": [{"instance": by_id[m]["short_id"], "vector_id": m,
            "note_id": by_id[m]["note_id"], "text": source[by_id[m]["note_id"]],
            "fragments": by_id[m]["fragments"], "byte_spans": by_id[m]["byte_spans"]} for m in members]})
    from .prepare_category_title_inputs import prepare as prepare_titles
    prepared = prepare_titles({"packets": packets}, TITLE.read_text(), [])
    save(output / "source-packets.json", {"packets": packets})
    save(output / "title-inputs.json", {"groups": prepared})
    config = read(output / "subject-config.json")
    config.pop("output_schema", None)
    config.update(run_directory=str(output / "title-run"), timeout_seconds=600,
                  prompts=[{"prompt_id": g["group"], "text": g["prompt"]} for g in prepared])
    save(output / "title-config.json", config)
    print(json.dumps({"groups": len(packets), "unassigned_vectors": len(artifact["result"]["fine_output"]["unassigned"]),
                      "title_calls": len(prepared)}))


def true_prepare(output):
    verify(output)
    sys.path.insert(0, str(SSE))
    from true_category_graph import prepare_inputs
    from true_score_reuse import plan_reuse
    from true_inventory_restore import identity, REFERENCE, REFERENCE_SOURCE, SHARED
    reference = identity(REFERENCE, REFERENCE_SOURCE)
    if {name: sha(SSE / name) for name in SHARED} != reference["source_sha256"]:
        raise ValueError("TRUE inference implementation changed")
    config = pipeline.PromptRunnerConfig.load(output / "title-config.json")
    manifest = read(config.run_directory / "manifest.json")
    records = {r["note_id"]: r for r in (json.loads(line) for line in (config.run_directory / "results.jsonl").read_text().splitlines())}
    inputs = {g["group"]: g for g in read(output / "title-inputs.json")["groups"]}
    titles = []
    for job in config.prompts:
        record = records[job.prompt_id]
        pipeline.validate_prompt_receipt(replace(config, prompts=(job,)), manifest, record)
        if record["status"] != "succeeded" or not record["final_output_raw"].strip():
            raise ValueError("missing generated title")
        title = record["final_output_raw"].strip()
        if "\n" in title:
            raise ValueError("title output is not a single title; no automatic repair")
        titles.append({**inputs[job.prompt_id], "title": title, "semantic_status": "generated, not independently approved"})
    titled = {"prompt_version": "v21", "groups": titles}
    pairs = prepare_inputs(titled, source_group_ids=list(inputs))
    old_path = SSE / "navigation-research-v1/TRUE13/canonical.json"
    old = read(old_path)
    # TRUE13 already binds both the original and restored-category scores to this runtime.
    from true_score_reuse import validate_cache_identity
    validate_cache_identity(identity(SSE / "navigation-research-v1/TRUE13/run", SSE), reference)
    reuse = plan_reuse(pairs, [(str(old_path), old["scores"])])
    save(output / "titles.json", titled)
    save(output / "true-inputs.json", pairs)
    save(output / "true-reuse.json", reuse)
    save(output / "true-missing-inputs.json", reuse["missing_inputs"])
    save(output / "true-reference.json", reference)
    print(json.dumps({"categories": len(titles), "directed_pairs": len(pairs),
                      "distinct_inputs": reuse["distinct_inputs"], "cached_inputs": len(reuse["reused"]),
                      "new_inputs": len(reuse["missing_inputs"])}))


def true_infer(output):
    verify(output)
    sys.path.insert(0, str(SSE))
    from true_holdout_probe import run_inference
    from true_category_probe import REVISION
    from true_inventory_restore import identity
    from true_score_reuse import validate_cache_identity
    available = next(int(line.split()[1]) for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))
    if available < 70 * 1024**2:
        raise ValueError("TRUE requires at least 70 GiB currently available memory")
    run = output / "true-run"
    run.mkdir(exist_ok=False)
    inputs = read(output / "true-missing-inputs.json")
    if inputs:
        snapshot = Path("/home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots") / REVISION
        run_inference(snapshot.resolve(strict=True), inputs, run, 4, time.monotonic(), experiment="HRv1")
        validate_cache_identity(identity(run, SSE), read(output / "true-reference.json"))
    else:
        (run / "scores.jsonl").touch(exist_ok=False)


def package(output):
    verify(output)
    sys.path.insert(0, str(SSE))
    from true_score_reuse import assemble_scores
    from true_category_graph import build_graph
    from true_graph_notes import derive_note_memberships
    from true_graph_categories import export
    from category_mask_instances import reconstruct
    fresh = [json.loads(line) for line in (output / "true-run/scores.jsonl").read_text().splitlines()]
    scores = assemble_scores(read(output / "true-inputs.json"), read(output / "true-reuse.json"), fresh, str(output / "true-run/scores.jsonl"))
    titles, packets = read(output / "titles.json"), read(output / "source-packets.json")
    canonical = {"titles": titles, "scores": scores, "source_packets": packets}
    graph = build_graph(titles, scores, decision_rule="native")
    memberships = derive_note_memberships(graph, packets)
    save(output / "canonical.json", canonical)
    save(output / "native-graph.json", graph)
    save(output / "native-notes.json", memberships)
    if graph["transitive_reduced_edges"] is None:
        save(output / "blocked.json", {"reason": "TRUE produced cycles; graph and all scores preserved. No edge deletion or automatic equivalence is authorized.", "stats": graph["stats"], "cycle_components": graph["cycle_components"]})
        raise ValueError("TRUE graph has cycles; saved for inspection, not silently repaired")
    categories = export(output / "canonical.json", output / "native-graph.json", output / "native-notes.json",
                        output / "masked-posts.json", output / "vector-map.json", output / "categories-without-mask-ids.json",
                        hierarchy_id="HRv1 · refreshed 100-post hierarchy · no membership expansion")
    save(output / "categories.json", reconstruct(categories, memberships, [], (output / "masked-posts.json").read_bytes()))
    baseline = reconstruct(read(BASELINE), read(BASELINE.parent / "native-notes.json"), [], SOURCE.read_bytes())
    save(output / "baseline-categories.json", baseline)
    save(output / "completion.json", {"experiment": "HRv1", "source_posts": 100,
        "represented_posts": len(categories["notes"]), "categories": len(titles["groups"]), "graph_stats": graph["stats"],
        "membership_expansion": False, "manual_title_repairs": False,
        "baseline_caveat": "TRUE13 includes the historical user-supplied #coffeechain title; HRv1 retains generated titles.",
        "outputs_sha256": {name: sha(output / name) for name in ("categories.json", "baseline-categories.json", "canonical.json", "native-graph.json")}})
    print(json.dumps(read(output / "completion.json")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "masks", "vectors", "groups", "true_prepare", "true_infer", "package"])
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    globals()[args.phase](args.output.resolve())
