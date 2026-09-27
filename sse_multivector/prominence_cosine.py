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
    from .experiment_inputs import prepare_prominence
    from .prominence_ranking import ranking_scores
except ImportError:
    import experiment
    from experiment_inputs import prepare_prominence
    import worker
    from prominence_ranking import ranking_scores


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
        row.update(ranking_scores(row))
    keys = ["prominence", "cosine", "product", "linear_product"]
    if any('inverse_cosine' in row or 'full_post_cosine' in row for row in rows):
        if any('inverse_product' not in row for row in rows):
            raise ValueError('incomplete inverse comparison')
        keys += ['inverse_product', 'full_post_score']
    return {key: [r["id"] for r in sorted(rows, key=lambda r: (-r[key], r["id"]))]
            for key in keys}


def inverse_spans(text, spans):
    """Exact UTF-8 complement, without rewriting the post or filtering its text."""
    result, cursor = [], 0
    for start, end in spans:
        worker._byte_span_to_character_span(text, (start, end))
        if start < cursor:
            raise ValueError('overlapping or unordered spans')
        if start > cursor:
            result.append([cursor, start])
        cursor = end
    if cursor < len(text.encode()):
        result.append([cursor, len(text.encode())])
    return result


def decode(path, dimensions, code):
    raw = Path(path).read_bytes()
    size = struct.calcsize(code)
    if len(raw) % (size * dimensions):
        raise ValueError("invalid vector byte length")
    return list(struct.iter_unpack("<" + code * dimensions, raw))


def load_vectors(vectors):
    """Read either preserved normalized vectors or a refresh worker's raw vectors."""
    protected = {}
    rows = read(vectors / "vector-map.json")["vectors"]
    if (vectors / "manifest.json").exists():
        manifest = read(vectors / "manifest.json")
        for name in ("vector-map.json", "normalized-vectors.f64le", "encoder.json"):
            path = vectors / name
            if sha(path) != manifest["files"][name]["sha256"]:
                raise ValueError(f"saved vector artifact changed: {name}")
            protected[str(path)] = sha(path)
        encoder = read(vectors / "encoder.json")
        vector_file, code = vectors / "normalized-vectors.f64le", "d"
    else:
        receipt_path = vectors / "worker-result/worker-receipt.json"
        encoder = read(receipt_path)
        request_path = vectors / "worker-request.json"
        request = read(request_path)
        vector_file, code = vectors / "worker-result/raw-vectors.f32le", "f"
        if (sha(request_path) != encoder["request_sha256"]
                or request["proposal_sha256"] != encoder["proposal_sha256"]
                or sha(vector_file) != encoder["files"][vector_file.name]["sha256"]):
            raise ValueError("refresh vector/request hash mismatch")
        requested = [(n, s) for n in request["notes"] for s in n["subjects"]]
        if not len(rows) == len(requested) == len(encoder["rows"]) == encoder["row_count"]:
            raise ValueError("refresh vector row count mismatch")
        for ordinal, (row, measured, (post, subject)) in enumerate(zip(rows, encoder["rows"], requested)):
            if (measured["ordinal"] != ordinal
                    or row["note_id"] != measured["note_id"] or row["note_id"] != post["note_id"]
                    or row["worker_subject_id"] != measured["subject_id"]
                    or row["worker_subject_id"] != subject["subject_id"]):
                raise ValueError("refresh vector row identity mismatch")
            if (row["byte_spans"] != subject["byte_spans"] or row["fragments"] !=
                    [post["text"].encode()[a:b].decode() for a, b in subject["byte_spans"]]):
                raise ValueError("refresh vector span mismatch")
            row["ordinal"] = ordinal
        for path in (vectors / "vector-map.json", receipt_path, request_path, vector_file):
            protected[str(path)] = sha(path)
    if len(decode(vector_file, encoder["model"]["dimensions"], code)) != len(rows):
        raise ValueError("vector byte count differs from mapping")
    return rows, encoder, vector_file, code, protected


def prepare(args):
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output already exists")
    vectors = args.vectors.resolve()
    rows, encoder, vector_file, vector_code, protected = load_vectors(vectors)
    lookup = {r["short_id"]: r for r in rows}
    if len(lookup) != len(rows) or any(r["ordinal"] != i for i, r in enumerate(rows)):
        raise ValueError("vector map has duplicate IDs or unexpected row order")
    cases, titles, originals = [], {}, {}
    selected_nodes = set(getattr(args, "node", None) or [])
    for directory in args.experiments:
        directory = directory.resolve()
        plan, _, _ = experiment.load(directory)
        if plan["dataset"]["adapter"] not in ("prominence", "generic"):
            raise ValueError("expected prominence inputs with saved mask evidence")
        report = experiment.report(directory)
        for name in (directory / "experiment.json", Path(plan["run_directory"]) / "results.jsonl"):
            protected[str(name)] = sha(name)
        for case in report["cases"]:
            if selected_nodes and case.get("evidence", {}).get("node_id") not in selected_nodes:
                continue
            if case["status"] != "valid":
                raise ValueError(f"unscored or invalid case: {case['id']}")
            e = case["evidence"]
            fields = ("id", "node_id", "node_title", "note_id", "text", "mask_ids", "byte_spans")
            verified = prepare_prominence({"cases": [{key: e[key] for key in fields}]})[0]
            if (case["id"] != e["id"] or set(case["inputs"]) != {"INPUT_JSON"}
                    or json.loads(case["inputs"]["INPUT_JSON"]) !=
                    json.loads(verified["inputs"]["INPUT_JSON"])):
                raise ValueError(f"model input differs from saved mask evidence: {case['id']}")
            score = case["parsed"].get("prominence")
            if type(score) is not int or not 0 <= score <= 100:
                raise ValueError(f"invalid prominence score: {case['id']}")
            nid, title = e["node_id"], e["node_title"]
            if nid in titles and titles[nid] != title:
                raise ValueError("conflicting node titles")
            titles[nid] = title
            for mid in e["mask_ids"]:
                saved = lookup[mid]
                if (saved["byte_spans"] != e["byte_spans"] or e["note_id"] not in (saved["note_short_id"], saved["note_id"])
                        or saved["fragments"] != [e["text"].encode()[a:b].decode() for a,b in e["byte_spans"]]):
                    raise ValueError(f"mask differs from saved vector: {mid}")
                originals[mid] = e
            cases.append(dict(id=case["id"], node_id=nid, title=title,
                              mask_ids=e["mask_ids"], note_id=e["note_id"],
                              fragments=lookup[e["mask_ids"][0]]["fragments"],
                              ordinal=lookup[e["mask_ids"][0]]["ordinal"],
                              prominence=score))
    if selected_nodes - titles.keys():
        raise ValueError(f"unknown requested node: {sorted(selected_nodes - titles.keys())}")
    if not cases:
        raise ValueError("no prominence cases selected")
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
    if getattr(args, 'include_inverse', False):
        # Group selections by post so the encoder contextualizes each post once.
        grouped, selections = {}, {}

        def selection(note_id, text, spans, subject_id=None):
            key = (note_id, tuple(map(tuple, spans)))
            note = grouped.setdefault(note_id, dict(note_id=note_id, text=text, subjects=[]))
            if note['text'] != text:
                raise ValueError('conflicting text for post')
            if key not in selections:
                sid = subject_id or hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
                note['subjects'].append(dict(subject_id=sid, byte_spans=spans))
                selections[key] = sid
            return selections[key]

        old_rows = []
        for note in notes:
            for subject in note['subjects']:
                old_rows.append(selection(note['note_id'], note['text'], subject['byte_spans'],
                                          subject['subject_id']))
        for case in cases:
            e = originals[case['mask_ids'][0]]
            note_id = lookup[case['mask_ids'][0]]['note_id']
            spans = inverse_spans(e['text'], e['byte_spans'])
            content = ''.join(e['text'].encode()[a:b].decode() for a, b in spans)
            if not content.strip() and case['prominence'] != 100:
                raise ValueError(f"empty inverse with missing meaning: {case['id']}")
            case['inverse_spans'] = spans
            case['inverse_row'] = selection(note_id, e['text'], spans) if content.strip() else None
            case['full_post_row'] = selection(note_id, e['text'], [[0, len(e['text'].encode())]])
        notes = list(grouped.values())
        indices = {s['subject_id']: i for i, (_, s) in enumerate(
            (n, s) for n in notes for s in n['subjects'])}
        title_rows = {nid: indices[old_rows[index]] for nid, index in title_rows.items()}
        for replay in replays.values():
            replay['row'] = indices[old_rows[replay['row']]]
        for case in cases:
            case['inverse_row'] = indices[case['inverse_row']] if case['inverse_row'] is not None else None
            case['full_post_row'] = indices[case['full_post_row']]
    config = read(args.worker_config)
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "note_batch_size"):
        if config[key] != encoder[key]:
            raise ValueError(f"encoder differs: {key}")
    if (config["device"] != "cpu" or ("worker_sha256" in encoder
            and sha(Path(worker.__file__)) != encoder["worker_sha256"])):
        raise ValueError("expected original CPU worker")
    for path in (Path(__file__).resolve(), Path(worker.__file__).resolve(),
                 Path(__file__).with_name('prominence_ranking.py').resolve(), args.worker_config.resolve()):
        protected[str(path)] = sha(path)
    output.mkdir(parents=True)
    plan = dict(schema_version=1, cases=cases, title_rows=title_rows, replays=replays,
                vectors=str(vectors), protected=protected, encoder=encoder,
                vector_file=str(vector_file), vector_code=vector_code,
                formula="prominence (0..100) * raw cosine; no clipping or fitted calibration",
                linear_formula="prominence * (clip(cosine, -1, 1) + 1) / 2; not calibrated relevance",
                parity_min_cosine=0.999999, parity_max_normalized_component_error=0.00001)
    if getattr(args, 'include_inverse', False):
        plan['inverse_formula'] = 'linear_product + (100 - prominence) * (clip(inverse_cosine, -1, 1) + 1) / 2'
        plan['full_post_formula'] = '100 * (clip(full_post_cosine, -1, 1) + 1) / 2'
        plan['inverse_policy'] = 'Exact byte complement in unchanged post; URLs and identifiers remain; whitespace-only inverse has no vector and requires prominence 100.'
    save(output / "plan.json", plan)
    save(output / "worker-request.json", dict(schema_version=1, proposal_sha256=sha(output / "plan.json"), notes=notes))
    worker._load_request(output / "worker-request.json")
    config.update(request_path=str(output / "worker-request.json"),
                  request_sha256=sha(output / "worker-request.json"), output_path=str(output / "result"))
    save(output / "worker-config.json", config)
    print(f"Prepared {len(titles)} titles, {len(replays)} replays; {len(cases)} saved masks; "
          f"{sum(len(n['subjects']) for n in notes)} encoder rows. No inference.")


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
    saved = decode(Path(plan.get("vector_file", str(Path(plan["vectors"]) / "normalized-vectors.f64le"))),
                   dim, plan.get("vector_code", "d"))
    if len(fresh) != len(receipt["rows"]):
        raise ValueError("vector count differs from receipt")
    parity = {}
    for mid, p in plan["replays"].items():
        a,b = fresh[p["row"]],saved[p["ordinal"]]
        norm = math.sqrt(math.fsum(x*x for x in a))
        saved_norm = math.sqrt(math.fsum(x*x for x in b))
        similarity = cosine(a,b)
        error = max(abs(x/norm-y/saved_norm) for x,y in zip(a,b))
        parity[mid] = dict(cosine=similarity, maximum_normalized_component_error=error)
        if similarity < plan["parity_min_cosine"] or error > plan["parity_max_normalized_component_error"]:
            raise ValueError(f"replay failed: {mid}: {parity[mid]}")
    groups = {}
    for case in plan["cases"]:
        scores = {nid: cosine(saved[case["ordinal"]],fresh[index]) for nid,index in plan["title_rows"].items()}
        row = dict(case, cosine=scores[case["node_id"]], title_cosines=scores)
        if 'inverse_row' in case:
            title = fresh[plan['title_rows'][case['node_id']]]
            row['inverse_cosine'] = (cosine(fresh[case['inverse_row']], title)
                                     if case['inverse_row'] is not None else None)
            row['full_post_cosine'] = cosine(fresh[case['full_post_row']], title)
        groups.setdefault(case["node_id"], []).append(row)
    rankings = {nid:rank_rows(rows) for nid,rows in groups.items()}
    result = dict(parity=parity, groups=groups, rankings=rankings, formula=plan["formula"],
                  linear_formula=plan.get("linear_formula", "prominence * (clip(cosine, -1, 1) + 1) / 2"),
                  worker_receipt_sha256=sha(output / "result/worker-receipt.json"),
                  raw_vectors_sha256=sha(output / "result/raw-vectors.f32le"))
    for key in ('inverse_formula', 'full_post_formula', 'inverse_policy'):
        if key in plan:
            result[key] = plan[key]
    save(output / "comparison.json", result)
    print(json.dumps(dict(parity=parity, masks=sum(map(len,groups.values())))))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("output", type=Path)
    prep.add_argument("--experiments", type=Path, nargs="+", required=True)
    prep.add_argument("--node", action="append", help="select a node ID; repeat for multiple nodes")
    prep.add_argument("--vectors", type=Path, required=True)
    prep.add_argument("--worker-config", type=Path, required=True)
    prep.add_argument("--replay", nargs="+", required=True)
    prep.add_argument('--include-inverse', action='store_true',
                      help='also encode exact inverse masks and one full-post selection per post')
    c = sub.add_parser("collect")
    c.add_argument("output", type=Path)
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        collect(args.output)


if __name__ == "__main__":
    main()
