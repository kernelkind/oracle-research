"""Reproducible geometry experiments over original frozen SSE coordinates.

Clustering modules receive only coordinates and explicit numerical options.
Masks and original notes are attached afterward for semantic inspection.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import platform
import resource
import time

import numpy as np


def canonical_rows(x, mapping, aliases):
    by_id = {row['vector_id']: row['ordinal'] for row in mapping}
    if len(by_id) != len(mapping) or sorted(by_id.values()) != list(range(len(x))):
        raise ValueError('vector map must identify every saved row exactly once')
    flat = [v for group in aliases for v in group]
    if len(flat) != len(set(flat)) or set(flat) != set(by_id) or any(not g for g in aliases):
        raise ValueError('aliases must partition every saved vector ID')
    indices = []
    for group in aliases:
        first = by_id[group[0]]
        if any(not np.array_equal(x[first], x[by_id[v]]) for v in group[1:]):
            raise ValueError('aliases do not have identical saved coordinates')
        indices.append(first)
    return x[indices].copy()


def overlay(text, spans):
    raw, parts, previous = text.encode('utf-8'), [], 0
    for start, end in spans:
        if not (previous <= start < end <= len(raw)):
            raise ValueError('mask fragments must be in source order without overlap')
        parts.extend((raw[previous:start].decode('utf-8'),
                      '⟦' + raw[start:end].decode('utf-8') + '⟧'))
        previous = end
    return ''.join(parts) + raw[previous:].decode('utf-8')


def validate_tree(nodes, roots, n):
    by_id = {node['id']: node for node in nodes}
    if len(by_id) != len(nodes) or not roots:
        raise ValueError('node IDs must be unique and roots nonempty')
    seen = set()

    def visit(i):
        if i in seen or i not in by_id:
            raise ValueError('tree contains a cycle, shared child, or missing node')
        seen.add(i)
        node = by_id[i]
        members = node['members']
        if not members or members != sorted(set(members)) or min(members) < 0 or max(members) >= n:
            raise ValueError('members must be nonempty unique sorted input rows')
        if node['children']:
            union = [v for c in node['children'] for v in visit(c)]
            if len(node['children']) < 2 or sorted(union) != members:
                raise ValueError('children must be an exact nontrivial disjoint partition')
        return members

    all_members = [v for r in roots for v in visit(r)]
    if sorted(all_members) != list(range(n)) or seen != set(by_id):
        raise ValueError('roots must cover all inputs once and reach every node')


def load_input(directory):
    directory = Path(directory)
    paths = dict(manifest=directory/'vectors/manifest.json',
                 vectors=directory/'vectors/normalized-vectors.f64le',
                 mapping=directory/'vectors/vector-map.json',
                 notes=directory/'reviewed-input.json',
                 aliases=directory/'hdbv3-cross-note-edges-v1/response.json')
    blobs = {name: path.read_bytes() for name, path in paths.items()}
    sources = {name: dict(path=str(path.resolve()), sha256=hashlib.sha256(blobs[name]).hexdigest())
               for name, path in paths.items()}
    manifest = json.loads(blobs['manifest'])
    for name in ('vectors', 'mapping', 'notes'):
        if sources[name]['sha256'] != manifest['files'][paths[name].name]['sha256']:
            raise ValueError(f'{name} differs from the frozen vector manifest')
    mapping = json.loads(blobs['mapping'])
    original = np.frombuffer(blobs['vectors'], dtype='<f8').reshape(
        manifest['vector_count'], manifest['dimensions'])
    if not np.isfinite(original).all() or not np.allclose(np.linalg.norm(original, axis=1), 1, atol=1e-12):
        raise ValueError('saved vectors must be finite unit vectors')
    baseline = json.loads(blobs['aliases'])['artifact']['result']
    aliases = baseline['alias_groups']
    if [g[0] for g in aliases] != baseline['canonical_unique_ids']:
        raise ValueError('canonical ID order changed')
    x = canonical_rows(original, mapping['vectors'], aliases)
    notes = json.loads(blobs['notes'])['notes']
    by_vector = {v['vector_id']: v for v in mapping['vectors']}
    records = []
    for i, group in enumerate(aliases):
        entries = []
        for vector_id in group:
            row = by_vector[vector_id]
            note = notes[row['reviewed_note_index']]
            text = note['text']
            fragments = [text.encode()[a:b].decode() for a, b in row['byte_spans']]
            if fragments != row['fragments']:
                raise ValueError('mask text no longer matches original note')
            entries.append(dict(vector_id=vector_id, short_id=row['short_id'],
                                note_id=row['note_id'], note_short_id=row['note_short_id'],
                                fragments=fragments, byte_spans=row['byte_spans'],
                                subject=row['subject'], text=text))
        records.append(dict(row=i, canonical_id=group[0], aliases=entries))
    return x, records, sources


def attach_notes(result, records):
    for node in result['nodes']:
        node['note_ids'] = sorted({entry['note_short_id'] for i in node['members']
                                   for entry in records[i]['aliases']})


def serializable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def detach_arrays(value):
    """Keep native fuzzy numerical evidence in NPZ, not huge JSON matrices."""
    arrays = {}

    def visit(item):
        if isinstance(item, np.ndarray):
            key = f'array_{len(arrays):04d}'
            arrays[key] = item
            return dict(array=key, shape=list(item.shape), dtype=str(item.dtype))
        if isinstance(item, dict):
            return {key: visit(v) for key, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [visit(v) for v in item]
        return item

    return visit(value), arrays


def write_json(path, value):
    with Path(path).open('x') as file:
        json.dump(value, file, indent=2, ensure_ascii=False, allow_nan=False, default=serializable)
        file.write('\n')


def inspect_group(run, node_id, *, full_notes=False):
    result = json.loads((run/'hierarchy.json').read_text())
    records = json.loads((run/'evidence.json').read_text())
    node = next(n for n in result['nodes'] if n['id'] == node_id)
    print(f"Node {node_id}; children {node['children']}; notes {' '.join(node['note_ids'])}")
    for i in node['members']:
        for entry in records[i]['aliases']:
            print(f"\n{entry['short_id']} · {entry['note_short_id']}")
            print(overlay(entry['text'], entry['byte_spans']) if full_notes else
                  ' '.join('⟦' + f + '⟧' for f in entry['fragments']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    run = sub.add_parser('run')
    run.add_argument('--data', type=Path, required=True)
    run.add_argument('--method', choices=('haus', 'fmc', 'diffusion'), required=True)
    run.add_argument('--config', default='{}')
    run.add_argument('--output', type=Path, required=True)
    run.add_argument('--run-id', required=True)
    inspect = sub.add_parser('inspect')
    inspect.add_argument('run', type=Path)
    inspect.add_argument('node', type=int)
    inspect.add_argument('--full-notes', action='store_true')
    args = parser.parse_args()
    if args.action == 'inspect':
        inspect_group(args.run, args.node, full_notes=args.full_notes)
        return
    if args.output.exists():
        parser.error('output exists; previous results must be preserved')
    config = json.loads(args.config)
    x, records, sources = load_input(args.data)
    module = importlib.import_module('geometric_' + args.method)
    start = time.monotonic()
    native = module.fit(x, **config)
    result = module.hard_projection(native) if args.method == 'fmc' else native
    elapsed = time.monotonic() - start
    validate_tree(result['nodes'], result['roots'], len(x))
    attach_notes(result, records)
    args.output.mkdir(parents=True, exist_ok=False)
    config_record = dict(run_id=args.run_id, method=args.method, config=config,
                         sources=sources, vector_count=len(x), dimensions=x.shape[1],
                         canonical_order_sha256=hashlib.sha256('\n'.join(
                             r['canonical_id'] for r in records).encode()).hexdigest(),
                         code={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (Path(__file__), Path(module.__file__))},
                         python=platform.python_version(), numpy=np.__version__,
                         elapsed_seconds=elapsed, max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(args.output/'configuration.json', config_record)
    write_json(args.output/'evidence.json', records)
    if args.method == 'fmc':
        encoded, arrays = detach_arrays(native)
        write_json(args.output/'native-fuzzy.json', encoded)
        np.savez_compressed(args.output/'native-fuzzy-arrays.npz', **arrays)
        result['method'] = 'fmc_per_transition_argmax_nested_projection'
    if 'final_coordinates' in result:
        np.save(args.output/'final-coordinates.npy', result.pop('final_coordinates'), allow_pickle=False)
    write_json(args.output/'hierarchy.json', result)
    summary = dict(run_id=args.run_id, nodes=len(result['nodes']), roots=result['roots'],
                   leaves=sum(not n['children'] for n in result['nodes']),
                   distinct_note_counts=dict(Counter(len(n['note_ids']) for n in result['nodes'])),
                   elapsed_seconds=elapsed, output=str(args.output))
    write_json(args.output/'summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
