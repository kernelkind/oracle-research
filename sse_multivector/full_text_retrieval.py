"""Compare a saved local meaning with full original posts using native SSE.

Offline search evidence only: no teacher calls, comparisons or graph changes.
Selecting an entire text for pooling does not create an MP-selected mask.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sse_multivector import worker
from sse_multivector.ancestor_cosine_probe import cosine, load_vectors


def prepare(state_path, step_index, worker_config_path, destination):
    state_path, worker_config_path, destination = (
        Path(p).resolve() for p in (state_path, worker_config_path, destination))
    if destination.exists():
        raise FileExistsError(destination)
    state = json.loads(state_path.read_bytes())
    step = next(s for s in state['steps'] if s['index'] == step_index)
    meaning = step['selected_meaning']
    if not isinstance(meaning, str) or not meaning.strip():
        raise ValueError('nonempty saved meaning required')
    corpus_path = Path(state['corpus']).resolve()
    corpus = {n['note_id']: n for n in json.loads(corpus_path.read_bytes())['notes']}
    note_ids = list(dict.fromkeys(s['local']['note_id'] for s in state['steps']))
    query_id = hashlib.sha256(('meaning\0' + meaning).encode()).hexdigest()
    rows = []

    def add(nid, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('nonempty full text required')
        end = len(text.encode())
        sid = hashlib.sha256((nid + f':0:{end}').encode()).hexdigest()[:16]
        rows.append(dict(note_id=nid, text=text,
                         subjects=[dict(subject_id=sid, byte_spans=[[0, end]])]))
        return [nid, sid]

    query = dict(local=step['local'], meaning=meaning, vector_key=add(query_id, meaning))
    notes = []
    for nid in note_ids:
        text = corpus[nid]['text']
        support = [dict(id=n['id'], subject=n['subject']) for n in step['before']
                   if any(e['note_id'] == nid for e in n['entries'])]
        notes.append(dict(note_id=nid, text=text, vector_key=add(nid, text),
                          canonical_support=support))
    protected = {str(p): worker._sha256_file(p) for p in (
        state_path, corpus_path, worker_config_path, Path(__file__).resolve(),
        Path(worker.__file__).resolve())}
    plan = dict(schema_version=1, state=str(state_path), step_index=step_index,
                query=query, notes=notes, protected_sha256=protected, teacher_calls=0,
                interpretation='Entire-text auxiliary SSE representations; no MP masks or placements.')
    destination.mkdir(parents=True)
    worker._write_json(destination / 'inputs.json', plan)
    worker._write_json(destination / 'worker-request.json', dict(schema_version=1,
        proposal_sha256=worker._sha256_file(destination / 'inputs.json'), notes=rows))
    worker._load_request(destination / 'worker-request.json')
    config = json.loads(worker_config_path.read_bytes())
    config.update(request_path=str(destination / 'worker-request.json'),
                  request_sha256=worker._sha256_file(destination / 'worker-request.json'),
                  output_path=str(destination / 'worker-result'))
    worker._write_json(destination / 'worker-config.json', config)
    worker.WorkerConfig.load(destination / 'worker-config.json')
    return dict(note_count=len(notes), vector_rows=len(rows), teacher_calls=0)


def rank(directory):
    directory = Path(directory).resolve()
    plan = json.loads((directory / 'inputs.json').read_bytes())
    for path, expected in plan['protected_sha256'].items():
        if worker._sha256_file(Path(path)) != expected:
            raise ValueError('source changed: ' + path)
    config = worker.WorkerConfig.load(directory / 'worker-config.json')
    vectors, receipt = load_vectors(directory / 'worker-result')
    if receipt['proposal_sha256'] != worker._sha256_file(directory / 'inputs.json'):
        raise ValueError('worker proposal binding differs')
    expected_request = worker._sha256_file(directory / 'worker-request.json')
    if receipt['request_sha256'] != expected_request or config.request_sha256 != expected_request:
        raise ValueError('worker request binding differs')
    expected_model = dict(checkpoint_sha256=config.checkpoint_sha256,
        base_model_artifact_tree_sha256=config.base_model_artifact_tree_sha256,
        model=config.model.to_json(), dimensions=config.model.dimensions)
    for key, expected in expected_model.items():
        if receipt[key] != expected:
            raise ValueError('worker model identity differs: ' + key)
    query = plan['query']
    expected_rows = {tuple(n['vector_key']) for n in [query, *plan['notes']]}
    if set(vectors) != expected_rows:
        raise ValueError('worker rows differ from full-text inputs')
    scores = [dict(n, cosine=cosine(vectors[tuple(query['vector_key'])],
                                   vectors[tuple(n['vector_key'])]),
                   incoming_note=n['note_id'] == query['local']['note_id']) for n in plan['notes']]
    scores.sort(key=lambda r: (-r['cosine'], r['note_id']))
    for index, row in enumerate(scores, 1):
        row['rank'] = index
    bound = dict(plan['protected_sha256'])
    for name in ('inputs.json', 'worker-config.json', 'worker-request.json',
                 'worker-result/worker-receipt.json', 'worker-result/raw-vectors.f32le'):
        p = directory / name
        bound[str(p)] = worker._sha256_file(p)
    return dict(schema_version=1, query=query, rows=scores, sources=bound,
                worker_identity=expected_model, teacher_calls=0,
                interpretation='Cosine-ranked original posts, not containment judgments.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--step', type=int, required=True)
    p.add_argument('--worker-config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('rank')
    p.add_argument('--vectors', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.state, args.step, args.worker_config, args.output)))
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        report = rank(args.vectors)
        worker._write_json(args.output, report)
        print(json.dumps(dict(note_count=len(report['rows']), teacher_calls=0, output=str(args.output))))


if __name__ == '__main__':
    main()
