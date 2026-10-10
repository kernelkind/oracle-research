"""Source-bound auxiliary SSE vectors for fixed hierarchy meanings.

These encodings are search representations, not source-post masks or new
hierarchy nodes. Preparation and collection never call a teacher.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sse_multivector import worker


def _read(path):
    return json.loads(Path(path).read_bytes())


def _write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def prepare(state_path, worker_config_path, destination, *, controls=()):
    """Bind original headings/immutable strings to ordinary SSE worker inputs."""
    state_path, worker_config_path, destination = map(
        lambda p: Path(p).resolve(), (state_path, worker_config_path, destination))
    if destination.exists():
        raise FileExistsError(destination)
    state = _read(state_path)
    corpus_path = Path(state['corpus']).resolve()
    corpus = {n['note_id']: n for n in _read(corpus_path)['notes']}
    pairs, references = {}, {}

    def add(key, subject, meaning):
        if meaning is None:
            return
        if not all(isinstance(x, str) and x.strip() for x in (subject, meaning)):
            raise ValueError('heading and fixed meaning must be nonempty text')
        identity = hashlib.sha256((subject + '\0' + meaning).encode()).hexdigest()
        pairs.setdefault(identity, dict(id=identity, subject=subject, meaning=meaning))
        references[key] = identity

    for node in state['nodes']:
        add('node:' + node['id'], node['subject'], node['meaning'])
    for step in state['steps']:
        local = step['local']
        subject = next(e['subject'] for e in corpus[local['note_id']]['subjects']
                       if e['number'] == local['number'])
        add('step:' + str(step['index']), subject, step['selected_meaning'])
    if not pairs:
        raise ValueError('no fixed meanings to encode')
    notes = {}

    def row(text, start, end):
        nid = hashlib.sha256(text.encode()).hexdigest()
        sid = hashlib.sha256((nid + f':{start}:{end}').encode()).hexdigest()[:16]
        note = notes.setdefault(nid, dict(note_id=nid, text=text, subjects=[]))
        item = dict(subject_id=sid, byte_spans=[[start, end]])
        if item not in note['subjects']:
            note['subjects'].append(item)
        return [nid, sid]

    for pair in pairs.values():
        subject, meaning = pair['subject'], pair['meaning']
        text = subject + '\n' + meaning
        split = len(subject.encode())
        pair['representations'] = dict(
            meaning=row(meaning, 0, len(meaning.encode())),
            contextual_heading=row(text, 0, split),
            contextual_meaning=row(text, split + 1, len(text.encode())))
    control_rows = {text: row(text, 0, len(text.encode())) for text in dict.fromkeys(controls)}
    protected = dict(state.get('sources', {}))
    for path in (state_path, corpus_path, worker_config_path, Path(__file__).resolve(),
                 Path(worker.__file__).resolve()):
        protected[str(path)] = worker._sha256_file(path)
    for filename, expected in protected.items():
        if worker._sha256_file(Path(filename)) != expected:
            raise ValueError('source changed: ' + filename)
    plan = dict(schema_version=1, state=str(state_path), pairs=list(pairs.values()),
                references=references, controls=control_rows, protected_sha256=protected,
                interpretation='Auxiliary fixed-meaning encodings; no MP masks or semantic decisions.',
                teacher_calls=0)
    destination.mkdir(parents=True)
    _write(destination / 'inputs.json', plan)
    _write(destination / 'worker-request.json', dict(schema_version=1,
        proposal_sha256=worker._sha256_file(destination / 'inputs.json'), notes=list(notes.values())))
    worker._load_request(destination / 'worker-request.json')
    config = _read(worker_config_path)
    config.update(request_path=str(destination / 'worker-request.json'),
                  request_sha256=worker._sha256_file(destination / 'worker-request.json'),
                  output_path=str(destination / 'worker-result'))
    _write(destination / 'worker-config.json', config)
    worker.WorkerConfig.load(destination / 'worker-config.json')
    return dict(meaning_pairs=len(pairs), encoder_inputs=len(notes),
                vector_rows=sum(len(n['subjects']) for n in notes.values()), teacher_calls=0)


def validate_sources(directory):
    plan = _read(Path(directory) / 'inputs.json')
    for path, expected in plan['protected_sha256'].items():
        if worker._sha256_file(Path(path)) != expected:
            raise ValueError('source changed: ' + path)
    return plan


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--worker-config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--control', action='append', default=[])
    a = p.parse_args()
    print(json.dumps(prepare(a.state, a.worker_config, a.output, controls=a.control)))


if __name__ == '__main__':
    main()
