"""Frozen offline child-count comparisons using the existing cosine partitioner.

Prepare fixes sections, source rows and development/reserved roles. Run computes
only the explicitly named case. Count one is the unsplit numerical baseline,
never an instruction to add a same-note-set child. No count selector is fitted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from . import direct_section_partition as direct


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    return json.loads(Path(path).read_text())


def _write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def _check_files(files):
    for path, expected in files.items():
        if _sha(path) != expected:
            raise ValueError('Frozen source changed: ' + path)


def _load_source(source):
    for path in [source['input'], source['entries'], *source.get('labels', {}).values()]:
        if path not in source['files']:
            raise ValueError('Every consumed source file requires a frozen hash')
    _check_files(source['files'])
    with np.load(source['input'], allow_pickle=False) as packet:
        vectors, notes = packet['vectors'], packet['notes']
    entries = _read(source['entries'])
    if (vectors.ndim != 2 or notes.ndim != 1 or not len(notes)
            or len(vectors) != len(notes) or len(entries) != len(notes)
            or not np.all(np.isfinite(vectors))
            or not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-8)
            or len({e['id'] for e in entries}) != len(entries)
            or [e['note_id'] for e in entries] != notes.tolist()):
        raise ValueError('Finite normalized vectors and aligned unique original entries required')
    return vectors, notes, entries


def prepare(specification, output):
    specification, output = Path(specification).resolve(), Path(output).resolve()
    spec = _read(specification)
    if (spec['counts'] != sorted(set(spec['counts'])) or not spec['counts']
            or spec['counts'][0] != 1 or spec['counts'][-1] > 6
            or not all(type(k) is int for k in spec['counts'])
            or not spec['seeds'] or len(set(spec['seeds'])) != len(spec['seeds'])
            or not all(type(s) is int and s >= 0 for s in spec['seeds'])
            or type(spec['max_iterations']) is not int or spec['max_iterations'] < 1
            or not np.isfinite(spec['time_limit']) or spec['time_limit'] <= 0):
        raise ValueError('Counts starting at one through at most six, fixed seeds and valid limits required')
    sources = {name: _load_source(source) for name, source in spec['sources'].items()}
    cases, identifiers, label_cache = [], set(), {}
    role_notes = {'development': set(), 'reserved': set()}
    for cfg in spec['cases']:
        identifier, role = cfg['id'], cfg['role']
        if (not re.fullmatch(r'[A-Za-z0-9_-]+', identifier) or identifier in identifiers
                or role not in role_notes or type(cfg['minimum_notes']) is not int
                or cfg['minimum_notes'] < 0):
            raise ValueError('Unique safe case IDs, development/reserved roles and valid minima required')
        identifiers.add(identifier)
        vectors, notes, entries = sources[cfg['source']]
        selector = cfg['selector']
        if selector['kind'] == 'all':
            indices = np.arange(len(notes))
        elif selector['kind'] == 'labels':
            key = (cfg['source'], selector['mode'])
            if key not in label_cache:
                path = spec['sources'][cfg['source']]['labels'][selector['mode']]
                label_cache[key] = np.asarray(_read(path)['best']['labels'])
            labels = label_cache[key]
            if labels.shape != notes.shape:
                raise ValueError('Saved labels must align with the original entries')
            indices = np.flatnonzero(labels == selector['value'])
        elif selector['kind'] == 'source_group':
            indices = np.array([i for i, e in enumerate(entries)
                                if e.get('source_group') == selector['value']], dtype=int)
        else:
            raise ValueError('Unknown section selector')
        if not len(indices):
            raise ValueError('Selected section is empty')
        selected_notes = sorted(set(notes[indices].tolist()))
        counts = [k for k in spec['counts'] if k <= len(indices)]
        if len(selected_notes) < cfg['minimum_notes'] or len(indices) < max(counts) * cfg['minimum_notes']:
            raise ValueError('Section cannot supply the configured minimum note witnesses')
        role_notes[role].update(selected_notes)
        for reuse in cfg.get('reuse', {}).values():
            _check_files(reuse['files'])
        cases.append(dict(cfg, indices=indices.tolist(),
                          entry_ids=[entries[i]['id'] for i in indices],
                          note_ids=selected_notes, notes=len(selected_notes),
                          entries=len(indices), counts=counts))
    if role_notes['development'] & role_notes['reserved']:
        raise ValueError('Development and reserved cases share original notes')
    output.mkdir(parents=True, exist_ok=False)
    plan = dict(status='Frozen research panel; no child-count or stopping policy adopted',
                specification=str(specification), specification_sha256=_sha(specification),
                spec=spec, cases=cases,
                code_files={str(Path(p).resolve()): _sha(p)
                            for p in [__file__, direct.__file__]},
                distinct_role_notes={role: len(notes) for role, notes in role_notes.items()},
                development_reserved_note_overlap=0)
    _write(output / 'plan.json', plan)
    return plan


def _verify(panel, vectors, notes, count, minimum, seeds):
    normalized = vectors / np.linalg.norm(vectors, axis=1)[:, None]
    if [t['seed'] for t in panel['trials']] != seeds:
        raise ValueError('Saved trials disagree with the fixed seeds')
    for trial in panel['trials']:
        labels, centers = np.asarray(trial['labels']), np.asarray(trial['centers'])
        if (labels.shape != notes.shape or labels.dtype.kind not in 'iu'
                or labels.min() < 0 or labels.max() >= count
                or centers.shape != (count, vectors.shape[1]) or not np.isfinite(centers).all()):
            raise ValueError('Invalid saved assignments or centers')
        counts = direct.note_counts(labels, notes, count)
        cost = float(np.clip(1 - np.einsum('ij,ij->i', normalized, centers[labels]), 0, 2).sum())
        if (counts != trial['section_notes'] or min(counts) < minimum
                or not np.isclose(cost, trial['objective'], rtol=1e-9, atol=1e-9)):
            raise ValueError('Saved cost or distinct-note counts disagree with original inputs')
        for k in range(count):
            total = normalized[labels == k].sum(axis=0)
            if np.linalg.norm(total) > 1e-14 and not np.allclose(
                    centers[k], total / np.linalg.norm(total), atol=1e-9):
                raise ValueError('Saved center is not its normalized assigned mean')
    if panel['best'] != min(panel['trials'], key=lambda t: (t['objective'], t['seed'])):
        raise ValueError('Saved best trial violates the fixed within-count objective')


def _import_panel(reuse, vectors, notes, count, minimum, spec):
    _check_files(reuse['files'])
    for path in [reuse['plan'], reuse['result']]:
        if path not in reuse['files']:
            raise ValueError('Reused producers require frozen plans and results')
    native = _read(reuse['plan'])
    native_minimum = 0 if reuse['mode'] == 'unconstrained' else native['minimum_notes']
    if (reuse['mode'] not in ['constrained', 'unconstrained']
            or native['sections'] != count or native_minimum != minimum
            or native['seeds'] != spec['seeds'] or native['max_iterations'] != spec['max_iterations']
            or native['assignment_time_limit_seconds'] != spec['time_limit']
            or native['source_sha256'] != _sha(direct.__file__)
            or _sha(native['input']) != native['input_sha256']):
        raise ValueError('Reused producer settings or input identity disagree')
    with np.load(native['input'], allow_pickle=False) as packet:
        if not np.array_equal(packet['vectors'], vectors) or not np.array_equal(packet['notes'], notes):
            raise ValueError('Reused producer has different original input rows')
    return _read(reuse['result'])


def run(output, case_id):
    output = Path(output).resolve()
    plan_path = output / 'plan.json'
    plan = _read(plan_path)
    _check_files(plan['code_files'])
    cfg = next((c for c in plan['cases'] if c['id'] == case_id), None)
    if cfg is None:
        raise ValueError('Unknown frozen case ID')
    spec = plan['spec']
    vectors, notes, entries = _load_source(spec['sources'][cfg['source']])
    indices = cfg['indices']
    vectors, notes = vectors[indices], notes[indices]
    if [entries[i]['id'] for i in indices] != cfg['entry_ids']:
        raise ValueError('Frozen case entry identities disagree')
    destination = output / case_id
    destination.mkdir(exist_ok=True)
    rows = []
    for count in cfg['counts']:
        binding = dict(plan_sha256=_sha(plan_path), case_id=case_id, count=count)
        path = destination / f'count-{count}.json'
        completed = path.exists()
        reused = cfg.get('reuse', {}).get(str(count))
        if completed:
            saved = _read(path)
            if saved['binding'] != binding:
                raise ValueError('Completed count has different frozen bindings')
            panel = saved['panel']
        else:
            if reused:
                panel = _import_panel(reused, vectors, notes, count, cfg['minimum_notes'], spec)
            else:
                trials = [direct.partition(vectors, notes, sections=count,
                          minimum_notes=cfg['minimum_notes'], seed=seed,
                          max_iterations=spec['max_iterations'], time_limit=spec['time_limit'])
                          for seed in spec['seeds']]
                panel = dict(best=min(trials, key=lambda t: (t['objective'], t['seed'])), trials=trials)
        _verify(panel, vectors, notes, count, cfg['minimum_notes'], spec['seeds'])
        if not completed:
            _write(path, dict(binding=binding, reused_from=reused, panel=panel))
        best = panel['best']
        sets = [set(notes[np.asarray(best['labels']) == k].tolist()) for k in range(count)]
        valid = all(0 < len(s) < cfg['notes'] for s in sets) and len({frozenset(s) for s in sets}) == count
        rows.append(dict(count=count, no_split=count == 1, notes_per_child=best['section_notes'],
                         nonempty_children=sum(bool(s) for s in sets),
                         valid_refinement=None if count == 1 else valid,
                         objective=best['objective'], seed=best['seed'],
                         converged=best['converged'], trials_converged=sum(t['converged'] for t in panel['trials']),
                         reused_producer=bool(reused)))
    result = dict(case_id=case_id, role=cfg['role'], entries=cfg['entries'],
                  notes=cfg['notes'], counts=rows, automatic_count_selection=None)
    _write(destination / 'summary.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('spec', type=Path)
    prep.add_argument('output', type=Path)
    execute = commands.add_parser('run')
    execute.add_argument('output', type=Path)
    execute.add_argument('case')
    args = parser.parse_args()
    result = prepare(args.spec, args.output) if args.command == 'prepare' else run(args.output, args.case)
    print(json.dumps({k: v for k, v in result.items() if k in ['case_id', 'entries', 'notes', 'counts', 'distinct_role_notes']}))


if __name__ == '__main__':
    main()
