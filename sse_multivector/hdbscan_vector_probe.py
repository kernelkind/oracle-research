"""Matched native HDBSCAN controls using saved title and meaning vectors.

Select original groups or all entries before execution. Keep opaque point
identities fixed between views; run no encoder, teacher, bend cut or hierarchy.
"""
import argparse
import json
from pathlib import Path
import re
import time

import numpy as np

from . import hierarchy_hdbscan as hdbscan
from . import section_count_panel as panel


def prepare(specification, output):
    specification, output = Path(specification).resolve(), Path(output).resolve()
    spec = panel._read(specification)
    if spec['as_version'] != 'ASv6.100':
        raise ValueError('Current ASv6.100 source required')
    vectors, notes, entries = panel._load_source(spec['source'])
    for path in [spec['native_state'], spec['native_request']]:
        if path not in spec['source']['files']:
            raise ValueError('Native title sources require frozen hashes')
    state, native = panel._read(spec['native_state']), panel._read(spec['native_request'])
    if native['hdbscan_configuration'] != hdbscan.CONFIG:
        raise ValueError('Matched native HDBSCAN configuration required')
    originals = {e['id']: e for e in state['originals']}
    titles = {e['opaque_id']: e['normalized_vector'] for e in native['inputs']}
    available = {e.get('source_group') for e in entries}
    cases, identifiers = [], set()
    for cfg in spec['cases']:
        name, groups = cfg['id'], cfg.get('groups')
        all_entries = cfg.get('all_entries', False)
        if (type(all_entries) is not bool or
                (all_entries and 'groups' in cfg) or
                (not all_entries and not groups)):
            raise ValueError('Exactly one selector: all_entries true or original groups required')
        if (not re.fullmatch(r'[A-Za-z0-9_-]+', name) or name in identifiers
                or (not all_entries and (any(not isinstance(g, str) for g in groups)
                    or len(set(groups)) != len(groups) or not set(groups) <= available))):
            raise ValueError('Unique safe cases and existing original groups required')
        identifiers.add(name)
        indices = [i for i, e in enumerate(entries)
                   if all_entries or e.get('source_group') in groups]
        selected, title_vectors = [], []
        for i in indices:
            e = entries[i]
            o = originals[e['id']]
            if (o.get('title', o['subject']) != e['title'] or o['meaning'] != e['meaning']
                    or o['local']['note_id'] != e['note_id']):
                raise ValueError('Original evidence differs between saved vector views')
            opaque = hdbscan.workflow.inputs.digest([e['id'], state['items'][e['id']]['vector_key']])
            title_vectors.append(titles[opaque])
            selected.append({k: e[k] for k in ['id', 'title', 'meaning', 'note_id', 'source_group']})
        title_vectors = np.asarray(title_vectors)
        if (title_vectors.shape != vectors[indices].shape or not np.isfinite(title_vectors).all()
                or not np.allclose(np.linalg.norm(title_vectors, axis=1), 1, atol=1e-8)):
            raise ValueError('Aligned finite normalized title vectors required')
        cases.append(dict(id=name, groups=groups, all_entries=all_entries, indices=indices, entries=selected,
                          title=title_vectors, meaning=vectors[indices], notes=notes[indices]))
    if not cases:
        raise ValueError('At least one explicit case required')
    binary = Path(spec['binary']).resolve()
    sources = dict(spec['source']['files'], **{str(specification): panel._sha(specification)})
    files = {str(binary): panel._sha(binary)}
    output.mkdir(parents=True, exist_ok=False)
    for cfg in cases:
        path = output / (cfg['id'] + '.npz')
        np.savez(path, title=cfg.pop('title'), meaning=cfg.pop('meaning'), notes=cfg.pop('notes'))
        cfg['data'] = str(path)
        files[str(path)] = panel._sha(path)
    plan = dict(status='Frozen saved-vector grouping probe; no HiGen activation',
                cases=cases, files=files, sources=sources, binary=str(binary),
                configuration=hdbscan.CONFIG,
                code_files={str(Path(p).resolve()): panel._sha(p) for p in
                            [__file__, panel.__file__, hdbscan.__file__,
                             hdbscan.trial.__file__, hdbscan.workflow.inputs.__file__]})
    panel._write(output / 'plan.json', plan)
    return plan


def run(output, case_id, view, *, workers=1):
    if view not in ['title', 'meaning', 'combined'] or type(workers) is not int or workers < 1:
        raise ValueError('A saved title/meaning/combined view and positive CPU worker count required')
    output = Path(output).resolve()
    plan = panel._read(output / 'plan.json')
    panel._check_files(plan['files'])
    panel._check_files(plan['code_files'])
    cfg = next((c for c in plan['cases'] if c['id'] == case_id), None)
    if cfg is None:
        raise ValueError('Unknown frozen grouping case')
    with np.load(cfg['data'], allow_pickle=False) as data:
        # Concatenating unit vectors gives equal-weight mean cosine before
        # the native route converts cosine to angular distance.
        vectors = (np.concatenate((data['title'], data['meaning']), axis=1) / np.sqrt(2)
                   if view == 'combined' else data[view])
    ids = [e['id'] for e in cfg['entries']]
    # One paired producer identity keeps canonical point order identical across
    # views. The request's vector digest binds which actual view was supplied.
    state = dict(hdbscan_binary=plan['binary'], items={i: dict(vector_key=
        hdbscan.workflow.inputs.digest([plan['files'][cfg['data']], i])) for i in ids})
    destination = output / case_id / view
    destination.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    native = hdbscan.round_for(destination, state,
        dict(id=case_id, current=ids, rounds=[]), vectors.tolist(), workers=workers)
    by_id = {e['id']: e for e in cfg['entries']}
    report = dict(binding=dict(plan_sha256=panel._sha(output / 'plan.json'), case=case_id, view=view),
                  native=native, groups=native['groups'], unassigned=native['unassigned'],
                  input_entries=len(ids), input_notes=len({e['note_id'] for e in by_id.values()}),
                  grouped_notes=len({by_id[i]['note_id'] for g in native['groups'] for i in g}))
    path = destination / 'result.json'
    if path.exists():
        saved = panel._read(path)
        if any(saved.get(k) != v for k, v in report.items()):
            raise ValueError('Saved grouping report differs from frozen native evidence')
        return saved
    report['elapsed_seconds'] = time.monotonic() - started
    panel._write(path, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('spec', type=Path)
    prep.add_argument('output', type=Path)
    execute = commands.add_parser('run')
    execute.add_argument('output', type=Path)
    execute.add_argument('case')
    execute.add_argument('view', choices=['title', 'meaning', 'combined'])
    execute.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.spec, args.output)
        print(json.dumps(dict(cases=len(result['cases']))))
    else:
        result = run(args.output, args.case, args.view, workers=args.workers)
        print(json.dumps({k: result[k] for k in ['binding', 'input_entries', 'input_notes', 'grouped_notes']} |
                         dict(groups=len(result['groups']), unassigned=len(result['unassigned']))))


if __name__ == '__main__':
    main()
