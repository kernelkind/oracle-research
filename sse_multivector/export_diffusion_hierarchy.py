"""Export saved diffusion groups for the read-only exact-containment viewer.

Native internal IDs, memberships, and child order stay unchanged. Singleton
point leaves are the viewer's direct vectors, not additional group nodes.
No coordinates are read and no clustering or subject labeling is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from geometric_experiment import overlay, validate_tree


def read_json(path):
    return json.loads(Path(path).read_bytes())


def source(path, expected):
    path = Path(path)
    blob = path.read_bytes()
    checksum = hashlib.sha256(blob).hexdigest()
    if checksum != expected['sha256']:
        raise ValueError(f'source checksum mismatch: {path.name}')
    return json.loads(blob), dict(path=str(path.resolve()), sha256=checksum)


def original_vectors(mapping, notes):
    """Validate original masks before checking the saved evidence against them."""
    by_note = {}
    for note in notes['notes']:
        note_id = note['note_id']
        if not isinstance(note_id, str) or not note_id or note_id in by_note:
            raise ValueError('source note IDs must be nonempty and unique')
        if not isinstance(note['text'], str):
            raise ValueError('source note text must be a string')
        by_note[note_id] = note['text']
    by_vector, short_ids, note_short_ids, short_notes = {}, set(), {}, {}
    for vector in mapping['vectors']:
        vector_id, short_id = vector['vector_id'], vector['short_id']
        note_id, note_short_id = vector['note_id'], vector['note_short_id']
        if (not all(isinstance(value, str) and value.strip()
                    for value in (vector_id, short_id, note_id, note_short_id))
                or vector_id in by_vector or short_id in short_ids):
            raise ValueError('source vector and short IDs must be nonempty and unique')
        if note_id not in by_note:
            raise ValueError('source vector names a missing note')
        if (note_short_ids.setdefault(note_id, note_short_id) != note_short_id
                or short_notes.setdefault(note_short_id, note_id) != note_id):
            raise ValueError('source note short IDs must identify notes unambiguously')
        text = by_note[note_id]
        spans, fragments = vector['byte_spans'], vector['fragments']
        if (not spans or len(spans) != len(fragments)
                or any(len(span) != 2 or any(type(i) is not int for i in span)
                       for span in spans)):
            raise ValueError('source masks need matching nonempty byte spans and fragments')
        try:
            overlay(text, spans)
        except (UnicodeError, ValueError) as error:
            raise ValueError('source mask has invalid UTF-8 byte spans') from error
        raw = text.encode('utf-8')
        if [raw[a:b].decode('utf-8') for a, b in spans] != fragments:
            raise ValueError('source mask fragments differ from original note byte spans')
        short_ids.add(short_id)
        by_vector[vector_id] = dict(vector, text=text)
    return by_vector


def canonical_rows(evidence, originals, count, expected_hash):
    if len(evidence) != count:
        raise ValueError('evidence count must match vector_count')
    aliases, canonical, seen = [], [], set()
    mask_fields = ('vector_id', 'short_id', 'note_id', 'note_short_id',
                   'byte_spans', 'fragments', 'text')
    for row, record in enumerate(evidence):
        if type(record['row']) is not int or record['row'] != row:
            raise ValueError('evidence rows must preserve canonical order')
        entries = record['aliases']
        if not entries or record['canonical_id'] != entries[0]['vector_id']:
            raise ValueError('canonical ID must be the first alias')
        row_aliases = []
        for entry in entries:
            vector_id = entry['vector_id']
            if vector_id in seen or vector_id not in originals:
                raise ValueError('aliases must partition original vector IDs exactly once')
            if any(entry[field] != originals[vector_id][field] for field in mask_fields):
                raise ValueError(f'evidence differs from original source mask: {vector_id}')
            seen.add(vector_id)
            row_aliases.append(vector_id)
        aliases.append(row_aliases)
        canonical.append(record['canonical_id'])
    if seen != set(originals):
        raise ValueError('aliases must cover every original vector ID')
    checksum = hashlib.sha256('\n'.join(canonical).encode('utf-8')).hexdigest()
    if checksum != expected_hash:
        raise ValueError('canonical ordering checksum mismatch')
    return aliases, canonical


def export(run, vector_map, notes, output):
    """Validate immutable saved inputs, then exclusively create one viewer file."""
    run, output = Path(run), Path(output)
    if output.exists():
        raise FileExistsError(output)
    configuration = read_json(run / 'configuration.json')
    hierarchy = read_json(run / 'hierarchy.json')
    evidence = read_json(run / 'evidence.json')
    if configuration['method'] != 'diffusion':
        raise ValueError('only saved diffusion hierarchies are supported')
    run_id, count = configuration['run_id'], configuration['vector_count']
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError('saved run_id must be nonempty')
    if type(count) is not int or count < 2:
        raise ValueError('saved diffusion hierarchy must have at least two vectors')
    roots, nodes = hierarchy['roots'], hierarchy['nodes']
    if len(roots) != 1:
        raise ValueError('saved diffusion hierarchy must have exactly one root; forests are unsupported')
    for node in nodes:
        if (type(node['id']) is not int or node['id'] < 0
                or any(type(i) is not int or i < 0 for i in node['children'])
                or any(type(i) is not int for i in node['members'])):
            raise ValueError('native IDs and members must be nonnegative integers')
        if node['children']:
            if node['id'] < count:
                raise ValueError('native internal node IDs must be outside point IDs')
        elif node['id'] >= count or node['members'] != [node['id']]:
            raise ValueError('native point leaves must preserve their canonical row IDs')
    if type(roots[0]) is not int or roots[0] < count:
        raise ValueError('saved root must be a native internal node')
    validate_tree(nodes, roots, count)
    mapping, map_source = source(vector_map, configuration['sources']['mapping'])
    saved_notes, note_source = source(notes, configuration['sources']['notes'])
    originals = original_vectors(mapping, saved_notes)
    aliases, canonical = canonical_rows(evidence, originals, count,
                                        configuration['canonical_order_sha256'])
    internal = {node['id'] for node in nodes if node['children']}
    parents = {child: node['id'] for node in nodes for child in node['children']}
    groups = []
    for node in nodes:
        vectors = [originals[alias] for row in node['members'] for alias in aliases[row]]
        note_short_ids = sorted({vector['note_short_id'] for vector in vectors})
        if node['note_ids'] != note_short_ids:
            raise ValueError(f'native note membership mismatch for node {node["id"]}')
        if node['id'] not in internal:
            continue
        is_root = node['id'] == roots[0]
        groups.append(dict(id=node['id'], kind='root' if is_root else 'persistent',
                           vector_ids=node['members'],
                           note_ids=sorted({vector['note_id'] for vector in vectors}),
                           parents=[] if is_root else [parents[node['id']]],
                           children=[child for child in node['children'] if child in internal]))
    result = dict(schema_version='containment-hierarchy-v1', run_id=run_id,
                  root=roots[0], vector_count=count, canonical_unique_ids=canonical,
                  alias_groups=aliases, sources=dict(vector_map=map_source, notes=note_source),
                  groups=groups)
    with output.open('x', encoding='utf-8') as file:
        json.dump(result, file, indent=2, ensure_ascii=False, allow_nan=False)
        file.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--vector-map', type=Path, required=True)
    parser.add_argument('--notes', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        export(args.run, args.vector_map, args.notes, args.output)
    except (KeyError, TypeError, ValueError, OSError) as error:
        parser.error(str(error))
    print(f'Exported saved diffusion hierarchy to {args.output}')


if __name__ == '__main__':
    main()
