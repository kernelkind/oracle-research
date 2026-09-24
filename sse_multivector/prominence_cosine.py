"""Offline prominence × title-cosine diagnostic using the existing SSE worker.

prepare freezes saved experiment scores, exact mask identities and encoder inputs.
Run worker.py on the produced config, then collect. No prompt/model API calls.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

try:
    from . import experiment, worker
except ImportError:
    import experiment
    import worker


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("vector dimensions differ")
    denominator = math.sqrt(math.fsum(x*x for x in a) * math.fsum(x*x for x in b))
    if not denominator or not math.isfinite(denominator):
        raise ValueError("zero or nonfinite vector norm")
    return math.fsum(x*y for x, y in zip(a, b)) / denominator


def rank_rows(rows):
    for row in rows:
        row["product"] = row["prominence"] * row["cosine"]
    return {key: [r["id"] for r in sorted(rows, key=lambda r: (-r[key], r["id"]))]
            for key in ("prominence", "cosine", "product")}


def decode(path, dimensions, code):
    raw = Path(path).read_bytes()
    size = struct.calcsize(code)
    if len(raw) % (size * dimensions):
        raise ValueError("invalid vector byte length")
    return list(struct.iter_unpack("<" + code * dimensions, raw))


def prepare(args):
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output already exists")
    vectors = args.vectors.resolve()
    manifest = read(vectors / "manifest.json")
    protected = {}
    for name in ("vector-map.json", "normalized-vectors.f64le", "encoder.json"):
        path = vectors / name
        if sha(path) != manifest["files"][name]["sha256"]:
            raise ValueError(f"saved vector artifact changed: {name}")
        protected[str(path)] = sha(path)
    mapping = read(vectors / "vector-map.json")
    rows = mapping["vectors"]
    lookup = {r["short_id"]: r for r in rows}
    if len(lookup) != len(rows) or any(r["ordinal"] != i for i, r in enumerate(rows)):
        raise ValueError("vector map has duplicate IDs or unexpected row order")
    cases, titles, originals = [], {}, {}
    for directory in args.experiments:
        directory = directory.resolve()
        plan, _, _ = experiment.load(directory)
        if plan["dataset"]["adapter"] != "prominence":
            raise ValueError("expected a prominence experiment")
        report = experiment.report(directory)
        for name in (directory / "experiment.json", Path(plan["run_directory"]) / "results.jsonl"):
            protected[str(name)] = sha(name)
        for case in report["cases"]:
            if case["status"] != "valid":
                raise ValueError(f"unscored or invalid case: {case['id']}")
            e = case["evidence"]
            nid, title = e["node_id"], e["node_title"]
            if nid in titles and titles[nid] != title:
                raise ValueError("conflicting node titles")
            titles[nid] = title
            for mid in e["mask_ids"]:
                saved = lookup[mid]
                if (saved["byte_spans"] != e["byte_spans"] or saved["note_short_id"] != e["note_id"]
                        or saved["fragments"] != [e["text"].encode()[a:b].decode() for a,b in e["byte_spans"]]):
                    raise ValueError(f"mask differs from saved vector: {mid}")
                originals[mid] = e
            cases.append(dict(id=case["id"], node_id=nid, title=title,
                              mask_ids=e["mask_ids"], note_id=e["note_id"],
                              fragments=lookup[e["mask_ids"][0]]["fragments"],
                              ordinal=lookup[e["mask_ids"][0]]["ordinal"],
                              prominence=case["parsed"]["prominence"]))
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("duplicate case IDs")
    notes, title_rows, replays = [], {}, {}
    for nid, title in titles.items():
        title_rows[nid] = len(notes)
        notes.append(dict(note_id=hashlib.sha256(title.encode()).hexdigest(), text=title,
                          subjects=[dict(subject_id=hashlib.sha256(nid.encode()).hexdigest()[:16],
                                         byte_spans=[[0, len(title.encode())]])]))
    for mid in args.replay:
        e = originals[mid]
        replays[mid] = dict(row=len(notes), ordinal=lookup[mid]["ordinal"])
        notes.append(dict(note_id=lookup[mid]["note_id"], text=e["text"],
                          subjects=[dict(subject_id=hashlib.sha256(mid.encode()).hexdigest()[:16],
                                         byte_spans=e["byte_spans"])]))
    encoder = read(vectors / "encoder.json")
    config = read(args.worker_config)
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "note_batch_size"):
        if config[key] != encoder[key]:
            raise ValueError(f"encoder differs: {key}")
    if config["device"] != "cpu" or sha(Path(worker.__file__)) != encoder["worker_sha256"]:
        raise ValueError("expected original CPU worker")
    for path in (Path(__file__).resolve(), Path(worker.__file__).resolve(), args.worker_config.resolve()):
        protected[str(path)] = sha(path)
    output.mkdir(parents=True)
    plan = dict(schema_version=1, cases=cases, title_rows=title_rows, replays=replays,
                vectors=str(vectors), protected=protected, encoder=encoder,
                formula="prominence (0..100) * raw cosine; no clipping or fitted calibration",
                parity_min_cosine=0.999999, parity_max_normalized_component_error=0.00001)
    save(output / "plan.json", plan)
    save(output / "worker-request.json", dict(schema_version=1, proposal_sha256=sha(output / "plan.json"), notes=notes))
    worker._load_request(output / "worker-request.json")
    config.update(request_path=str(output / "worker-request.json"),
                  request_sha256=sha(output / "worker-request.json"), output_path=str(output / "result"))
    save(output / "worker-config.json", config)
    print(f"Prepared {len(titles)} titles, {len(replays)} replays; {len(cases)} saved masks. No inference.")


def collect(output):
    output = output.resolve()
    plan = read(output / "plan.json")
    for path, expected in plan["protected"].items():
        if sha(path) != expected:
            raise ValueError(f"protected artifact changed: {path}")
    receipt = read(output / "result/worker-receipt.json")
    if (receipt["request_sha256"] != sha(output / "worker-request.json")
            or receipt["proposal_sha256"] != sha(output / "plan.json")):
        raise ValueError("worker input provenance mismatch")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "note_batch_size"):
        if receipt[key] != plan["encoder"][key]:
            raise ValueError(f"worker identity differs: {key}")
    _, requests = worker._load_request(output / "worker-request.json")
    if [(r["note_id"], r["subject_id"]) for r in receipt["rows"]] != [(n.note_id,s.subject_id) for n in requests for s in n.subjects]:
        raise ValueError("worker rows differ from request")
    dim = plan["encoder"]["model"]["dimensions"]
    fresh = decode(output / "result/raw-vectors.f32le", dim, "f")
    saved = decode(Path(plan["vectors"]) / "normalized-vectors.f64le", dim, "d")
    if len(fresh) != len(receipt["rows"]):
        raise ValueError("vector count differs from receipt")
    parity = {}
    for mid, p in plan["replays"].items():
        a,b = fresh[p["row"]],saved[p["ordinal"]]
        norm = math.sqrt(math.fsum(x*x for x in a))
        similarity = cosine(a,b)
        error = max(abs(x/norm-y) for x,y in zip(a,b))
        parity[mid] = dict(cosine=similarity, maximum_normalized_component_error=error)
        if similarity < plan["parity_min_cosine"] or error > plan["parity_max_normalized_component_error"]:
            raise ValueError(f"replay failed: {mid}: {parity[mid]}")
    groups = {}
    for case in plan["cases"]:
        scores = {nid: cosine(saved[case["ordinal"]],fresh[index]) for nid,index in plan["title_rows"].items()}
        row = dict(case, cosine=scores[case["node_id"]], title_cosines=scores)
        groups.setdefault(case["node_id"], []).append(row)
    rankings = {nid:rank_rows(rows) for nid,rows in groups.items()}
    result = dict(parity=parity, groups=groups, rankings=rankings, formula=plan["formula"],
                  worker_receipt_sha256=sha(output / "result/worker-receipt.json"),
                  raw_vectors_sha256=sha(output / "result/raw-vectors.f32le"))
    save(output / "comparison.json", result)
    print(json.dumps(dict(parity=parity, masks=sum(map(len,groups.values())))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("output", type=Path)
    prep.add_argument("--experiments", type=Path, nargs="+", required=True)
    prep.add_argument("--vectors", type=Path, required=True)
    prep.add_argument("--worker-config", type=Path, required=True)
    prep.add_argument("--replay", nargs="+", required=True)
    c = sub.add_parser("collect")
    c.add_argument("output", type=Path)
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        collect(args.output)


if __name__ == "__main__":
    main()
