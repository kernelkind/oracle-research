"""Compare saved teachers' masks against one fixed, other-note SSE reference.

No teacher calls, clustering, thresholds, or semantic correctness decisions.
Preparation validates experiment receipts and reuses exact saved masks. The
ordinary SSE worker encodes new masks plus one replay control per query note.
"""
import argparse
from pathlib import Path

from sse_multivector import experiment
from sse_multivector.ancestor_cosine_probe import load_vectors, cosine
from sse_multivector.hierarchy_refresh import encode_inputs, read, save, sha


def mask_inputs(cases):
    notes = {}
    for case in cases:
        if case['status'] not in ('valid', 'empty'):
            raise ValueError('all candidate mask receipts must be valid or empty')
        nid, text = case['evidence']['note_id'], case['inputs']['POST']
        note = notes.setdefault(nid, dict(note_id=nid, text=text, subjects=[]))
        if note['text'] != text:
            raise ValueError('conflicting text for note ID')
        note['subjects'].append(dict(subject=case['inputs']['SUBJECT'], case_id=case['id']))
    # encode_inputs expects checks in the grouped subject order.
    ordered = [c for nid in notes for c in cases if c['evidence']['note_id'] == nid]
    checks = [dict(item_id=f'M{i:03}', status='valid', ranges=c['ranges'])
              for i, c in enumerate(ordered, 1)]
    return encode_inputs(dict(notes=list(notes.values())), checks)


def best_connections(baseline, candidate, vectors, query_notes):
    import numpy as np
    cohort = set(query_notes)
    reference = [r for r in baseline if r['note_id'] not in cohort]
    if not reference:
        raise ValueError('nonempty other-note reference required')
    ids = list(dict.fromkeys(r['vector_id'] for r in baseline + candidate))
    values = np.array([vectors[k] for k in ids], dtype=np.float64)
    norms = np.linalg.norm(values, axis=1)
    if not np.isfinite(values).all() or not np.isfinite(norms).all() or (norms == 0).any():
        raise ValueError('finite nonzero vectors required')
    values /= norms[:, None]
    positions = {k: i for i, k in enumerate(ids)}
    anchors = values[[positions[r['vector_id']] for r in reference]]
    results = []
    for note in query_notes:
        arms = []
        for rows in (baseline, candidate):
            selected = [r for r in rows if r['note_id'] == note]
            if not selected:
                arms.append([None] * len(reference))
                continue
            scores = anchors @ values[[positions[r['vector_id']] for r in selected]].T
            best = scores.argmax(axis=1)
            arms.append([dict(vector_id=selected[j]['vector_id'], cosine=float(scores[i, j]))
                         for i, j in enumerate(best)])
        for r, a, b in zip(reference, *arms, strict=True):
            results.append(dict(query_note=note, reference_id=r['vector_id'],
                                baseline=a, candidate=b))
    return results


def prepare(source, candidate, output):
    if output.exists():
        raise ValueError('output already exists')
    validated = experiment.report(candidate)
    request, mapping, preserved = mask_inputs(validated['cases'])
    base = read(source / 'vector-map.json')
    base_notes = {n['note_id']: n for n in read(source / 'masked-posts.json')['notes']}
    for note in preserved['notes']:
        if note['note_id'] not in base_notes or note['text'] != base_notes[note['note_id']]['text']:
            raise ValueError('candidate note text must exactly match baseline')
    known = {r['vector_id'] for r in base['vectors']}
    controls, requests = [], []
    source_requests = {n['note_id']: n for n in read(source / 'worker-request.json')['notes']}
    for note in request:
        control = next(r for r in base['vectors'] if r['note_id'] == note['note_id'])
        controls.append(control)
        new = [s for s in note['subjects'] if not any(
            r['worker_subject_id'] == s['subject_id'] and r['vector_id'] in known
            for r in mapping['vectors'])]
        old = next(s for s in source_requests[note['note_id']]['subjects']
                   if s['subject_id'] == control['worker_subject_id'])
        requests.append(dict(note_id=note['note_id'], text=note['text'], subjects=[old] + new))
    protected = [source / n for n in ('vector-map.json', 'masked-posts.json', 'worker-config.json',
                 'worker-request.json', 'worker-result/worker-receipt.json', 'worker-result/raw-vectors.f32le')]
    plan = read(candidate / 'experiment.json')['plan']
    protected += [candidate / 'experiment.json', Path(plan['run_directory']) / 'results.jsonl']
    output.mkdir(parents=True)
    save(output / 'inputs.json', dict(source=str(source), candidate=str(candidate), controls=controls,
         query_notes=[n['note_id'] for n in preserved['notes']],
         protected_sha256={str(p): sha(p) for p in protected},
         interpretation='Fixed reference excludes every query note. Cosines are not correctness labels.'))
    save(output / 'vector-map.json', mapping)
    save(output / 'masked-posts.json', preserved)
    save(output / 'worker-request.json', dict(schema_version=1,
         proposal_sha256=sha(output / 'inputs.json'), notes=requests))
    config = read(source / 'worker-config.json')
    config.update(request_path=str(output / 'worker-request.json'),
                  request_sha256=sha(output / 'worker-request.json'), output_path=str(output / 'worker-result'))
    save(output / 'worker-config.json', config)
    print(dict(candidate_vectors=len(mapping['vectors']),
               reused=sum(r['vector_id'] in known for r in mapping['vectors']),
               controls=len(controls), new_worker_rows=sum(len(n['subjects']) for n in requests)))


def collect(output):
    from sse_multivector.real_note_segmentation import _validate_tokens
    inputs = read(output / 'inputs.json')
    for path, expected in inputs['protected_sha256'].items():
        if sha(Path(path)) != expected:
            raise ValueError(f'protected source changed: {path}')
    source = Path(inputs['source'])
    old, old_receipt = load_vectors(source / 'worker-result')
    new, new_receipt = load_vectors(output / 'worker-result')
    for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model', 'runtime',
                'device', 'note_batch_size'):
        if old_receipt[key] != new_receipt[key]:
            raise ValueError(f'encoder identity changed: {key}')
    if (new_receipt['request_sha256'] != sha(output / 'worker-request.json') or
            new_receipt['proposal_sha256'] != sha(output / 'inputs.json')):
        raise ValueError('worker inputs mismatch')
    for receipt in (old_receipt, new_receipt):
        for i, row in enumerate(receipt['rows']):
            _validate_tokens(row, receipt['model']['maximum_tokens'], i)
    base = read(source / 'vector-map.json')['vectors']
    candidate = read(output / 'vector-map.json')['vectors']
    vectors = {r['vector_id']: old[(r['note_id'], r['worker_subject_id'])] for r in base}
    controls = []
    for row in inputs['controls']:
        key = row['note_id'], row['worker_subject_id']
        score = cosine(old[key], new[key])
        difference = max(abs(a-b) for a, b in zip(old[key], new[key], strict=True))
        if score < .999999 or difference > 1e-5:
            raise ValueError('replay control changed materially')
        controls.append(dict(vector_id=row['vector_id'], cosine=score, max_abs_difference=difference))
    for row in candidate:
        if row['vector_id'] not in vectors:
            vectors[row['vector_id']] = new[(row['note_id'], row['worker_subject_id'])]
    result = best_connections(base, candidate, vectors, inputs['query_notes'])
    save(output / 'connections.json', dict(controls=controls, connections=result))
    print(dict(connections=len(result), controls=len(controls)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('collect')
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.source.resolve(), args.candidate.resolve(), args.output.resolve())
    else:
        collect(args.output.resolve())


if __name__ == '__main__':
    main()
