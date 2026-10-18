"""Prepare/collect paired local SSE views of explicitly optional example tails.

This research adapter retains original meanings and fixed group membership.
It prepares the existing native SSE worker; it contains no inference loop,
semantic labeling, automatic meaning rewrite or hierarchy admission policy.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sse_multivector import worker

VIEWS = ('full', 'core_selected', 'core_context')
OPTIONAL_MARKER = ', including but not limited to '


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def core_prefix(meaning):
    """Remove only the exact explicit nonrestrictive suffix, for this probe."""
    return meaning.partition(OPTIONAL_MARKER)[0]


def unchanged(sources):
    for path, expected in sources.items():
        if worker._sha256_file(Path(path)) != expected:
            raise ValueError('source changed: ' + path)


def prepare(study, root, group, output):
    """Prepare source-bound views from one previously frozen fusion group."""
    study, output = Path(study).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    source = read(study / 'plan.json')
    if source.get('as_version') != 'ASv6.100':
        raise ValueError('approved ASv6.100 provenance required')
    sources = {str(Path(p).resolve()): h for p, h in source['sources'].items()}
    for path in [study/'plan.json', study/'group-composition.json',
                 study/'worker-config.json', Path(__file__), Path(worker.__file__)]:
        sources[str(path.resolve())] = worker._sha256_file(path)
    unchanged(sources)
    matches = [g for g in read(study/'group-composition.json')
               if g['root'] == root and g['group'] == group]
    if len(matches) != 1 or len(matches[0]['members']) < 2:
        raise ValueError('one saved group with at least two members required')
    template = read(study/'worker-config.json')
    worker.WorkerConfig.load(study/'worker-config.json')
    contexts, records = {}, []

    def add(text, start, end):
        note_id = hashlib.sha256(text.encode()).hexdigest()
        subject_id = digest([note_id, start, end])[:16]
        note = contexts.setdefault(note_id, dict(note_id=note_id, text=text, subjects=[]))
        subject = dict(subject_id=subject_id, byte_spans=[[start, end]])
        if subject not in note['subjects']:
            note['subjects'].append(subject)
        return dict(note_id=note_id, subject_id=subject_id)

    for item in matches[0]['members']:
        title, meaning = item['title'], item['meaning']
        if not title or not meaning:
            raise ValueError('nonempty title and meaning required')
        core = core_prefix(meaning)
        if not core.strip():
            raise ValueError('optional tail has no preceding definition')
        prefix = title + '\n\n'
        start = len(prefix.encode())
        original, shortened = prefix + meaning, prefix + core
        records.append(dict(**item, core=core, removed_tail=meaning[len(core):],
            views=dict(full=add(original, start, len(original.encode())),
                       core_selected=add(original, start, len(shortened.encode())),
                       core_context=add(shortened, start, len(shortened.encode())))))
    inputs = dict(status='Frozen example-tail diagnostic; original meanings unchanged',
        root=root, group=group, source_study=str(study), sources=sources,
        optional_marker=OPTIONAL_MARKER, records=records,
        views=dict(full='Pool entire meaning in original title/meaning context',
                   core_selected='Pool prefix only; optional tail stays in context',
                   core_context='Pool identical prefix in context without optional tail'),
        restrictions='No changed groups, outsider texts, labels, encoder or admission algorithm')
    output.mkdir(parents=True)
    write(output/'inputs.json', inputs)
    request = dict(schema_version=1,
        proposal_sha256=worker._sha256_file(output/'inputs.json'),
        notes=list(contexts.values()))
    write(output/'worker-request.json', request)
    config = dict(template, request_path=str(output/'worker-request.json'),
        request_sha256=worker._sha256_file(output/'worker-request.json'),
        output_path=str(output/'worker-result'))
    write(output/'worker-config.json', config)
    worker._load_request(output/'worker-request.json')
    worker.WorkerConfig.load(output/'worker-config.json')
    return dict(records=len(records), changed=sum(bool(r['removed_tail']) for r in records),
                contexts=len(contexts), rows=sum(len(n['subjects'])for n in contexts.values()))


def collect(directory):
    """Validate native receipts and publish normalized paired reference views."""
    import numpy as np
    directory = Path(directory).resolve()
    inputs = read(directory/'inputs.json')
    unchanged(inputs['sources'])
    config = worker.WorkerConfig.load(directory/'worker-config.json')
    if worker._sha256_file(config.request_path) != config.request_sha256:
        raise ValueError('worker request hash differs')
    proposal, notes = worker._load_request(config.request_path)
    if proposal != worker._sha256_file(directory/'inputs.json'):
        raise ValueError('worker proposal differs from frozen inputs')
    receipt = read(config.output_path/'worker-receipt.json')
    raw_path = config.output_path/'raw-vectors.f32le'
    for key, expected in dict(proposal_sha256=proposal,
            request_sha256=config.request_sha256, checkpoint_sha256=config.checkpoint_sha256,
            base_model_artifact_tree_sha256=config.base_model_artifact_tree_sha256,
            model=config.model.to_json(), dimensions=config.model.dimensions).items():
        if receipt[key] != expected:
            raise ValueError('worker identity differs: ' + key)
    if (receipt['runtime']['worker_sha256'] != worker._sha256_file(Path(worker.__file__))
            or receipt['files'][raw_path.name]['sha256'] != worker._sha256_file(raw_path)):
        raise ValueError('worker source or vector bytes differ')
    keys = [(n.note_id, s.subject_id) for n in notes for s in n.subjects]
    if keys != [(r['note_id'], r['subject_id']) for r in receipt['rows']]:
        raise ValueError('worker row mapping differs')
    raw = np.fromfile(raw_path, dtype='<f4').reshape(len(keys), config.model.dimensions)
    if not np.isfinite(raw).all() or (np.linalg.norm(raw, axis=1) == 0).any():
        raise ValueError('finite nonzero vectors required')
    raw = raw.astype(float)
    raw /= np.linalg.norm(raw, axis=1)[:, None]
    lookup = {k: i for i, k in enumerate(keys)}
    files = {}
    for view in VIEWS:
        indices = [lookup[(r['views'][view]['note_id'], r['views'][view]['subject_id'])]
                   for r in inputs['records']]
        path = directory/(view+'-vectors.npy')
        values = raw[indices]
        if path.exists():
            if not np.array_equal(np.load(path, allow_pickle=False), values):
                raise ValueError('existing collected vectors differ')
        else:
            np.save(path, values, allow_pickle=False)
        files[path.name] = worker._sha256_file(path)
    report = dict(records=len(inputs['records']), dimensions=config.model.dimensions,
        views=list(VIEWS), files=files,
        inputs_sha256=worker._sha256_file(directory/'inputs.json'),
        receipt_sha256=worker._sha256_file(config.output_path/'worker-receipt.json'))
    path = directory/'collected.json'
    if path.exists() and read(path) != report:
        raise ValueError('existing collection receipt differs')
    if not path.exists():
        write(path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('study', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--root', required=True)
    p.add_argument('--group', required=True)
    p = sub.add_parser('collect')
    p.add_argument('directory', type=Path)
    args = parser.parse_args()
    result = (prepare(args.study, args.root, args.group, args.output)
              if args.command == 'prepare' else collect(args.directory))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
