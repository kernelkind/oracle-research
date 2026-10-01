"""Offline prominence × title-cosine diagnostic using the existing SSE worker.

prepare freezes saved experiment scores, exact mask identities and encoder inputs.
Run worker.py on the produced config, then collect. No prompt/model API calls.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

try:
    from . import experiment, worker
    from .experiment_inputs import prepare_prominence, prepare_context_prominence, union_spans
    from .prominence_ranking import ranking_scores
    from .extraction_pipeline import NIP19_IDENTIFIER, URL_SCHEME_PATTERN
except ImportError:
    import experiment
    from experiment_inputs import prepare_prominence, prepare_context_prominence, union_spans
    import worker
    from prominence_ranking import ranking_scores
    from extraction_pipeline import NIP19_IDENTIFIER, URL_SCHEME_PATTERN


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


def excluded_reference_spans(text):
    """Versioned URL/NIP-19/64-hex detection; returns merged UTF-8 spans."""
    url = re.compile(URL_SCHEME_PATTERN.pattern + r'''[^\s<>"']+''', URL_SCHEME_PATTERN.flags)
    hexadecimal = re.compile(r'(?<![A-Za-z0-9_])[a-fA-F0-9]{64}(?![A-Za-z0-9_])')
    spans = []
    for pattern in (url, NIP19_IDENTIFIER, hexadecimal):
        for match in pattern.finditer(text):
            start, end = match.span()
            if pattern is url:
                # Keep sentence punctuation and unmatched enclosing brackets in the post selection.
                while end > start:
                    last = text[end - 1]
                    unmatched = last in ')]}' and text[start:end].count(last) > text[start:end].count(
                        {')': '(', ']': '[', '}': '{'}[last])
                    if last not in '.,;!?' and not unmatched:
                        break
                    end -= 1
            spans.append([len(text[:start].encode()), len(text[:end].encode())])
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def subtract_spans(spans, excluded):
    """Subtract ordered disjoint exclusions without joining distant source text."""
    result = []
    for start, end in spans:
        cursor = start
        for left, right in excluded:
            if right <= cursor:
                continue
            if left >= end:
                break
            if left > cursor:
                result.append([cursor, left])
            cursor = min(end, right)
        if cursor < end:
            result.append([cursor, end])
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
    pooling = getattr(args, 'pooling', None)
    if pooling and args.replay:
        raise ValueError('pooling override cannot use original mask replays')
    include_subject = getattr(args, 'include_subject', False)
    exclude_references = getattr(args, 'exclude_references', False)
    if exclude_references and not getattr(args, 'include_inverse', False):
        raise ValueError('--exclude-references requires --include-inverse')
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output already exists")
    encoding_source = getattr(args, 'reuse_encoding', None)
    if encoding_source:
        encoding_source = encoding_source.resolve()
        reuse_notes = read(encoding_source/'worker-request.json')['notes']
        reuse_rows = [(n, s) for n in reuse_notes for s in n['subjects']]
        reuse_replays = read(encoding_source/'plan.json')['replays']
    vectors = args.vectors.resolve() if args.vectors else None
    if vectors:
        rows, encoder, vector_file, vector_code, protected = load_vectors(vectors)
    else:
        if args.replay:
            raise ValueError('mask replays require --vectors')
        rows, vector_file, vector_code, protected = [], None, None, {}
        encoder = read(args.worker_config)
    lookup = {r["short_id"]: r for r in rows}
    if len(lookup) != len(rows) or any(r["ordinal"] != i for i, r in enumerate(rows)):
        raise ValueError("vector map has duplicate IDs or unexpected row order")
    cases, titles, originals, evidence = [], {}, {}, {}
    selected_nodes = set(getattr(args, "node", None) or [])
    selected_cases = set(getattr(args, 'only', None) or [])
    source_texts = {}
    for case_id, text in getattr(args, 'relevance_source_text', None) or []:
        if case_id in source_texts:
            raise ValueError(f'duplicate relevance source text: {case_id}')
        source_texts[case_id] = text
    source_replacements = {}
    for case_id, before, after in getattr(args, 'relevance_source_replace', None) or []:
        if case_id in source_replacements:
            raise ValueError(f'duplicate relevance source replacement: {case_id}')
        source_replacements[case_id] = (before, after)
    if source_replacements.keys() - source_texts.keys():
        raise ValueError('--relevance-source-replace requires --relevance-source-text for each case')
    if source_texts and getattr(args, 'include_inverse', False):
        raise ValueError('source-text relevance has no literal inverse')
    if include_subject and source_texts:
        raise ValueError('--include-subject cannot combine with --relevance-source-text')
    for directory in args.experiments:
        directory = directory.resolve()
        plan, _, _ = experiment.load(directory)
        context_input = plan['dataset']['adapter'] == 'subject_contexts'
        if include_subject and not context_input:
            raise ValueError('--include-subject requires saved SP subjects and contexts')
        if context_input and getattr(args, 'include_inverse', False):
            raise ValueError('subject context relevance has no literal inverse')
        if plan["dataset"]["adapter"] not in ("prominence", "generic", 'subject_contexts'):
            raise ValueError("expected prominence inputs with saved mask evidence")
        report = experiment.report(directory)
        for name in (directory / "experiment.json", Path(plan["run_directory"]) / "results.jsonl"):
            protected[str(name)] = sha(name)
        for case in report["cases"]:
            if selected_nodes and case.get("evidence", {}).get("node_id") not in selected_nodes:
                continue
            if selected_cases and case['id'] not in selected_cases:
                continue
            if case["status"] != "valid":
                raise ValueError(f"unscored or invalid case: {case['id']}")
            e = case["evidence"]
            saved_context = context_input and 'subject_id' in e
            if not vectors and not saved_context:
                raise ValueError('saved mask comparisons require --vectors')
            if saved_context:
                for reference in e['source'].values():
                    path = Path(reference['path'])
                    expected = protected.get(str(path))
                    if expected is None:
                        expected = sha(path)
                    if expected != reference['sha256']:
                        raise ValueError(f'saved context source changed: {path}')
                    protected[str(path)] = expected
            fields = ("id", "node_id", "node_title", "note_id", "text")
            fields += ('subject_id', 'source') if saved_context else ('mask_ids', 'byte_spans')
            if context_input:
                fields += ('subject', 'context')
                if not saved_context:
                    fields += ('subject_number',)
            source = {"cases": [{key: e[key] for key in fields}]}
            verified = (prepare_context_prominence(source, plan['dataset'].get('prominence_basis', 'context'))
                        if context_input else prepare_prominence(source))[0]
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
            masks = []
            for mid in e.get("mask_ids", []):
                saved = lookup[mid]
                if not plan['dataset'].get('combine_masks', False) and saved['byte_spans'] != e['byte_spans']:
                    raise ValueError(f"mask differs from saved vector: {mid}")
                if (e["note_id"] not in (saved["note_short_id"], saved["note_id"])
                        or saved["fragments"] != [e["text"].encode()[a:b].decode() for a,b in saved['byte_spans']]):
                    raise ValueError(f"mask differs from saved vector: {mid}")
                original = dict(e, mask_ids=[mid], byte_spans=saved['byte_spans'])
                prepare_prominence({'cases': [{key: original[key] for key in
                    ('id', 'node_id', 'node_title', 'note_id', 'text', 'mask_ids', 'byte_spans')}]})
                if context_input and not any(
                        s['number'] == e['subject_number'] and s['subject'] == e['subject']
                        and s['context'] == e['context'] for s in saved.get('subject_entries', [])):
                    raise ValueError('context differs from saved SP subject')
                originals[mid] = original
                masks.append(saved)
            if not saved_context and union_spans([span for mask in masks for span in mask['byte_spans']]) != union_spans(e['byte_spans']):
                raise ValueError(f"mask union differs from saved vectors: {case['id']}")
            exact = next((mask for mask in masks if mask['byte_spans'] == e['byte_spans']), None)
            evidence[case['id']] = e
            cases.append(dict(id=case["id"], node_id=nid, title=title,
                              mask_ids=e.get("mask_ids", []), note_id=e["note_id"],
                              fragments=[e['text'].encode()[a:b].decode() for a,b in e.get('byte_spans', [])],
                              ordinal=exact['ordinal'] if exact else None,
                              prominence=score))
            if context_input:
                cases[-1].update(ordinal=None,
                                 representation='subject_context' if include_subject else 'context',
                                 context=e['context'],
                                 subject=e['subject'],
                                 prominence_basis=plan['dataset'].get('prominence_basis', 'context'))
                identity = 'subject_id' if saved_context else 'subject_number'
                cases[-1][identity] = e[identity]
            if case['id'] in source_texts:
                text = source_texts[case['id']]
                start = e['text'].find(text)
                if not text.strip() or start < 0:
                    raise ValueError(f'relevance source text must be an exact nonempty post fragment: {case["id"]}')
                byte_start = len(e['text'][:start].encode())
                cases[-1].update(ordinal=None, representation='source_text',
                                 relevance_source_text=text,
                                 relevance_source_spans=[[byte_start, byte_start + len(text.encode())]])
                if case['id'] in source_replacements:
                    before, after = source_replacements[case['id']]
                    if not before.strip() or before == after:
                        raise ValueError(f'relevance source replacement must change a nonempty phrase: {case["id"]}')
                    if text.count(before) != 1:
                        raise ValueError(f'relevance source replacement phrase must occur exactly once: {case["id"]}')
                    replaced = text.replace(before, after, 1)
                    if not replaced.strip():
                        raise ValueError(f'replacement must leave nonempty relevance text: {case["id"]}')
                    cases[-1].update(relevance_source_replacement=dict(before=before, after=after),
                                     relevance_text=replaced)
    if selected_cases - {case['id'] for case in cases}:
        raise ValueError(f"unknown requested cases: {sorted(selected_cases - {case['id'] for case in cases})}")
    if selected_nodes - titles.keys():
        raise ValueError(f"unknown requested node: {sorted(selected_nodes - titles.keys())}")
    if source_texts.keys() - {case['id'] for case in cases}:
        raise ValueError(f"unknown relevance source cases: {sorted(source_texts.keys() - {case['id'] for case in cases})}")
    if not cases:
        raise ValueError("no prominence cases selected")
    post_order = getattr(args, 'post_order', None)
    if post_order and (post_order != 'highest'
                       or any(c.get('representation') not in ('context', 'subject_context', 'source_text')
                              for c in cases)):
        raise ValueError('highest post order requires context or source-text cases')
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("duplicate case IDs")
    notes, title_rows, replays = [], {}, {}
    for nid, title in titles.items():
        title_rows[nid] = len(notes)
        notes.append(dict(note_id=hashlib.sha256(title.encode()).hexdigest(), text=title,
                          subjects=[dict(subject_id=hashlib.sha256(nid.encode()).hexdigest()[:16],
                                         byte_spans=[[0, len(title.encode())]])]))
    for mid in args.replay:
        if mid in originals:
            e = originals[mid]
        elif encoding_source and mid in reuse_replays:
            replay = reuse_replays[mid]
            note, subject = reuse_rows[replay['row']]
            saved = lookup[mid]
            if (replay['ordinal'] != saved['ordinal'] or note['note_id'] != saved['note_id']
                    or subject['byte_spans'] != saved['byte_spans']
                    or [note['text'].encode()[a:b].decode() for a, b in subject['byte_spans']]
                    != saved['fragments']):
                raise ValueError(f'reused replay differs from saved mask: {mid}')
            e = dict(text=note['text'], byte_spans=subject['byte_spans'])
        else:
            raise ValueError(f'replay mask unavailable: {mid}')
        replays[mid] = dict(row=len(notes), ordinal=lookup[mid]["ordinal"])
        notes.append(dict(note_id=lookup[mid]["note_id"], text=e["text"],
                          subjects=[dict(subject_id=hashlib.sha256(mid.encode()).hexdigest()[:16],
                                         byte_spans=e["byte_spans"])]))
    if getattr(args, 'include_inverse', False) or any(c['ordinal'] is None for c in cases):
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
            e = evidence[case['id']]
            note_id = lookup[case['mask_ids'][0]]['note_id'] if case['mask_ids'] else case['note_id']
            if case['ordinal'] is None:
                if case.get('representation') in ('context', 'subject_context', 'source_text'):
                    if case['representation'] == 'source_text':
                        text = case.get('relevance_text', case['relevance_source_text'])
                    elif case['representation'] == 'subject_context':
                        text = case['subject'] + '\n' + case['context']
                    else:
                        text = case['context']
                    case['mask_row'] = selection(hashlib.sha256(text.encode()).hexdigest(),
                                                 text, [[0, len(text.encode())]])
                else:
                    case['mask_row'] = selection(note_id, e['text'], e['byte_spans'])
            if not getattr(args, 'include_inverse', False):
                continue
            spans = inverse_spans(e['text'], e['byte_spans'])
            full_spans = [[0, len(e['text'].encode())]]
            if exclude_references:
                excluded = excluded_reference_spans(e['text'])
                case['excluded_spans'] = excluded
                spans = subtract_spans(spans, excluded)
                full_spans = subtract_spans(full_spans, excluded)
            if not ''.join(e['text'].encode()[a:b].decode() for a, b in full_spans).strip():
                raise ValueError(f"empty full-post selection: {case['id']}")
            content = ''.join(e['text'].encode()[a:b].decode() for a, b in spans)
            if not content.strip() and case['prominence'] != 100:
                raise ValueError(f"empty inverse with missing meaning: {case['id']}")
            case['inverse_spans'] = spans
            case['full_post_spans'] = full_spans
            case['inverse_row'] = selection(note_id, e['text'], spans) if content.strip() else None
            case['full_post_row'] = selection(note_id, e['text'], full_spans)
        notes = list(grouped.values())
        indices = {s['subject_id']: i for i, (_, s) in enumerate(
            (n, s) for n in notes for s in n['subjects'])}
        title_rows = {nid: indices[old_rows[index]] for nid, index in title_rows.items()}
        for replay in replays.values():
            replay['row'] = indices[old_rows[replay['row']]]
        for case in cases:
            if 'mask_row' in case:
                case['mask_row'] = indices[case['mask_row']]
            if 'inverse_row' in case:
                case['inverse_row'] = indices[case['inverse_row']] if case['inverse_row'] is not None else None
                case['full_post_row'] = indices[case['full_post_row']]
    config = read(args.worker_config)
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "note_batch_size"):
        if config[key] != encoder[key]:
            raise ValueError(f"encoder differs: {key}")
    if (config["device"] != "cpu" or ("worker_sha256" in encoder
            and sha(Path(worker.__file__)) != encoder["worker_sha256"])):
        raise ValueError("expected original CPU worker")
    if pooling:
        if any(c['ordinal'] is not None for c in cases):
            raise ValueError('pooling override requires newly encoded relevance rows')
        model = dict(config['model'], pooling=pooling)
        worker.ModelDescriptor.from_json(model)
        config['model'] = model
        encoder = dict(encoder, model=model)
    if encoding_source:
        reused_encoder = read(encoding_source/'plan.json')['encoder']
        for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model', 'note_batch_size'):
            if encoder[key] != reused_encoder[key]:
                raise ValueError(f'reused encoder identity differs: {key}')
        indices = {json.dumps([n['note_id'], n['text'], s], sort_keys=True): i
                   for i, (n, s) in enumerate(reuse_rows)}
        try:
            mapping = [indices[json.dumps([n['note_id'], n['text'], s], sort_keys=True)]
                       for n in notes for s in n['subjects']]
        except KeyError as error:
            raise ValueError('reused encoder notes differ from current context selections') from error
        title_rows = {nid: mapping[row] for nid, row in title_rows.items()}
        for replay in replays.values():
            replay['row'] = mapping[replay['row']]
        for case in cases:
            for key in ('mask_row', 'inverse_row', 'full_post_row'):
                if case.get(key) is not None:
                    case[key] = mapping[case[key]]
        notes = reuse_notes
        previous = read(encoding_source/'comparison.json')
        for key, name in (('worker_receipt_sha256', 'result/worker-receipt.json'),
                          ('raw_vectors_sha256', 'result/raw-vectors.f32le')):
            if previous[key] != sha(encoding_source/name):
                raise ValueError('reused encoding differs from saved comparison')
        for name in ('plan.json', 'worker-request.json', 'comparison.json',
                     'result/worker-receipt.json', 'result/raw-vectors.f32le'):
            path = encoding_source/name
            protected[str(path)] = sha(path)
    for path in (Path(__file__).resolve(), Path(worker.__file__).resolve(),
                 Path(__file__).with_name('experiment_inputs.py').resolve(),
                 Path(__file__).with_name('prominence_ranking.py').resolve(), args.worker_config.resolve()):
        protected[str(path)] = sha(path)
    if exclude_references:
        path = Path(__file__).with_name('extraction_pipeline.py').resolve()
        protected[str(path)] = sha(path)
    output.mkdir(parents=True)
    plan = dict(schema_version=1, cases=cases, title_rows=title_rows, replays=replays,
                vectors=str(vectors) if vectors else None, protected=protected, encoder=encoder,
                vector_file=str(vector_file) if vector_file else None, vector_code=vector_code,
                formula="prominence (0..100) * raw cosine; no clipping or fitted calibration",
                linear_formula="prominence * (clip(cosine, -1, 1) + 1) / 2; not calibrated relevance",
                parity_min_cosine=0.999999, parity_max_normalized_component_error=0.00001)
    if post_order:
        plan['post_order'] = post_order
    if encoding_source:
        plan['encoding_source'] = str(encoding_source)
    if getattr(args, 'include_inverse', False):
        plan['inverse_formula'] = 'linear_product + (100 - prominence) * (clip(inverse_cosine, -1, 1) + 1) / 2'
        plan['full_post_formula'] = '100 * (clip(full_post_cosine, -1, 1) + 1) / 2'
        plan['inverse_policy'] = 'Exact byte complement in unchanged post; URLs and identifiers remain; whitespace-only inverse has no vector and requires prominence 100.'
        if exclude_references:
            plan['reference_exclusion'] = 'url-nip19-hex64-v1'
            plan['inverse_policy'] = ('Inverse and full-post selections exclude scheme URLs, NIP-19 identifiers '
                                      'and standalone 64-hex identifiers. Original masks, prominence and full '
                                      'post context remain unchanged; empty inverse requires prominence 100.')
    save(output / "plan.json", plan)
    save(output / "worker-request.json", dict(schema_version=1, proposal_sha256=sha(output / "plan.json"), notes=notes))
    worker._load_request(output / "worker-request.json")
    config.update(request_path=str(output / "worker-request.json"),
                  request_sha256=sha(output / "worker-request.json"), output_path=str(output / "result"))
    save(output / "worker-config.json", config)
    print(f"Prepared {len(titles)} titles, {len(replays)} replays; {len(cases)} cases; "
          f"{sum(len(n['subjects']) for n in notes)} encoder rows. No inference.")
    if encoding_source:
        print(f"Reusing saved encoding from {encoding_source}; collect without running the worker.")


def collect(output):
    output = output.resolve()
    plan = read(output / "plan.json")
    for path, expected in plan["protected"].items():
        if sha(path) != expected:
            raise ValueError(f"protected artifact changed: {path}")
    encoding_source = Path(plan.get('encoding_source', str(output)))
    if encoding_source != output:
        request = read(output/'worker-request.json')
        if (request['notes'] != read(encoding_source/'worker-request.json')['notes']
                or request['proposal_sha256'] != sha(output/'plan.json')):
            raise ValueError('reused encoder request differs')
    receipt = read(encoding_source / "result/worker-receipt.json")
    if (receipt["request_sha256"] != sha(encoding_source / "worker-request.json")
            or receipt["proposal_sha256"] != sha(encoding_source / "plan.json")):
        raise ValueError("worker input provenance mismatch")
    for key in ("checkpoint_sha256", "base_model_artifact_tree_sha256", "model", "note_batch_size"):
        if receipt[key] != plan["encoder"][key]:
            raise ValueError(f"worker identity differs: {key}")
    _, requests = worker._load_request(output / "worker-request.json")
    if [(r["note_id"], r["subject_id"]) for r in receipt["rows"]] != [(n.note_id,s.subject_id) for n in requests for s in n.subjects]:
        raise ValueError("worker rows differ from request")
    dim = plan["encoder"]["model"]["dimensions"]
    fresh = decode(encoding_source / "result/raw-vectors.f32le", dim, "f")
    saved = []
    if plan['vectors'] is not None:
        vector_file = plan.get('vector_file') or str(Path(plan['vectors']) / 'normalized-vectors.f64le')
        saved = decode(Path(vector_file), dim, plan.get('vector_code', 'd'))
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
        mask = fresh[case['mask_row']] if 'mask_row' in case else saved[case['ordinal']]
        scores = {nid: cosine(mask, fresh[index]) for nid,index in plan["title_rows"].items()}
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
                  worker_receipt_sha256=sha(encoding_source / "result/worker-receipt.json"),
                  raw_vectors_sha256=sha(encoding_source / "result/raw-vectors.f32le"))
    if encoding_source != output:
        result['encoding_source'] = str(encoding_source)
    if plan.get('post_order') == 'highest':
        result['post_order'] = 'highest'
        result['posts'], result['post_rankings'] = {}, {}
        keys = ('prominence', 'linear_product')
        for nid, rows in groups.items():
            by_post = {}
            for row in rows:
                by_post.setdefault(row['note_id'], []).append(row)
            posts = []
            for note_id, contexts in sorted(by_post.items()):
                post = dict(note_id=note_id, context_count=len(contexts))
                for key in keys:
                    winner = min(contexts, key=lambda r: (-r[key], r['id']))
                    post[key], post[key + '_case'] = winner[key], winner['id']
                posts.append(post)
            result['posts'][nid] = posts
            result['post_rankings'][nid] = {
                key: [p['note_id'] for p in sorted(posts, key=lambda p: (-p[key], p['note_id']))]
                for key in keys}
    for key in ('inverse_formula', 'full_post_formula', 'inverse_policy', 'reference_exclusion'):
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
    prep.add_argument('--only', action='append', metavar='CASE_ID',
                      help='select a saved case; repeat to compare cases from several experiments')
    prep.add_argument('--relevance-source-text', action='append', nargs=2,
                      metavar=('CASE_ID', 'TEXT'),
                      help='encode an exact saved-post fragment as standalone relevance text; repeat per case')
    prep.add_argument('--relevance-source-replace', action='append', nargs=3,
                      metavar=('CASE_ID', 'OLD', 'NEW'),
                      help='replace one unique phrase in selected source text; freeze the original and diagnostic copy')
    prep.add_argument('--include-subject', action='store_true',
                      help='encode the saved SP subject, a newline, and its unchanged context together')
    prep.add_argument('--pooling', choices=(worker.POOLING_RULE, worker.MEAN_POOLING_RULE),
                      help='override pooling for newly encoded relevance rows; cannot use original mask replays')
    prep.add_argument("--vectors", type=Path, help='required for saved MP masks or mask replay controls')
    prep.add_argument("--worker-config", type=Path, required=True)
    prep.add_argument("--replay", nargs="+", default=[], help='original MP-mask controls from --vectors')
    prep.add_argument('--include-inverse', action='store_true',
                      help='also encode exact inverse masks and one full-post selection per post')
    prep.add_argument('--exclude-references', action='store_true',
                      help='exclude scheme URLs, NIP-19 and 64-hex IDs from inverse/full selections only')
    prep.add_argument('--post-order', choices=('highest',),
                      help='compare each post\'s highest prominence and highest SP-context sorting score')
    prep.add_argument('--reuse-encoding', type=Path,
                      help='reuse completed encoding rows matching exact notes and selections, including a subset')
    c = sub.add_parser("collect")
    c.add_argument("output", type=Path)
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        collect(args.output)


if __name__ == "__main__":
    main()
