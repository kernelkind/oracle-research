"""Project saved diffusion groups into named, read-only note categories.

Equal recursive note sets collapse only along parent-child edges. The highest
native group remains; narrower children keep their saved order. Groups with
fewer than two notes are not choices, but their notes remain at every retained
ancestor. Native memberships, vector groups, and source files never change.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from export_diffusion_hierarchy import export as export_viewer, read_json


def project(viewer):
    """Return ordered category groups and aliases from a validated saved tree."""
    groups = {group['id']: group for group in viewer['groups']}
    if len(groups) != len(viewer['groups']):
        raise ValueError('saved groups must have unique native IDs')
    memberships = {native: set(group['note_ids']) for native, group in groups.items()}
    retained, native_to_retained, seen = [], {}, set()

    def mark(native, target):
        if native in seen or native not in groups:
            raise ValueError('saved groups contain a cycle, shared child, or missing group')
        seen.add(native)
        native_to_retained[str(native)] = target['node_id']

    def hide(native, target):
        mark(native, target)
        for child in groups[native]['children']:
            hide(child, target)

    def add(native):
        group = dict(node_id=str(native), native_node_ids=[native], children=[],
                     note_ids=sorted(memberships[native]))
        retained.append(group)
        mark(native, group)
        descend(native, group)
        return group

    def descend(native, target):
        for child in groups[native]['children']:
            if child not in groups or not memberships[child] <= memberships[native]:
                raise ValueError('saved children must preserve native note containment')
            if memberships[child] == set(target['note_ids']):
                mark(child, target)
                target['native_node_ids'].append(child)
                descend(child, target)
            elif len(memberships[child]) < 2:
                hide(child, target)
            else:
                target['children'].append(add(child)['node_id'])

    root = add(viewer['root'])
    if seen != set(groups):
        raise ValueError('saved root must reach every native group')
    by_id = {group['node_id']: group for group in retained}
    reconstructed = {}
    for group in reversed(retained):
        child_notes = set().union(*(reconstructed[child] for child in group['children']))
        full_notes = set(group['note_ids'])
        group['direct_note_ids'] = sorted(full_notes - child_notes)
        reconstructed[group['node_id']] = child_notes | set(group['direct_note_ids'])
        if reconstructed[group['node_id']] != full_notes:
            raise ValueError('projection changed a retained group note membership')
        if any(set(by_id[child]['note_ids']) == full_notes for child in group['children']):
            raise ValueError('projection retained an equal-note-set edge')
    return dict(root_node_id=root['node_id'], retained_groups=retained,
                native_to_retained=native_to_retained)


def file_source(path):
    path = Path(path)
    return dict(path=str(path.resolve()), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def export(run, vector_map, notes, titles, output, projection_output):
    """Validate saved sources and exclusively create categories plus provenance."""
    run, output, projection_output = Path(run), Path(output), Path(projection_output)
    if output.resolve() == projection_output.resolve():
        raise ValueError('categories and projection outputs must be distinct')
    for path in (output, projection_output):
        if path.exists():
            raise FileExistsError(path)

    # Reuse the exact-containment exporter's original-mask, canonical-alias,
    # source-checksum, and native-tree validation. No coordinates are loaded.
    with TemporaryDirectory(prefix='diffusion-category-validation-') as temporary:
        validated_path = Path(temporary) / 'viewer.json'
        export_viewer(run, vector_map, notes, validated_path)
        validated = read_json(validated_path)
    viewer_path = run / 'viewer.json'
    viewer = read_json(viewer_path)
    # Saved source paths are provenance, not a requirement to retain the same
    # checkout location. All other saved fields must match the validated export.
    for name in validated['sources']:
        validated['sources'][name]['path'] = viewer['sources'][name]['path']
    if viewer != validated:
        raise ValueError('saved viewer differs from validated native hierarchy and evidence')

    projected = project(viewer)
    labels = read_json(titles)
    retained_ids = {group['node_id'] for group in projected['retained_groups']}
    if not isinstance(labels, dict) or set(labels) != retained_ids:
        missing = sorted(retained_ids - set(labels)) if isinstance(labels, dict) else sorted(retained_ids)
        extra = sorted(set(labels) - retained_ids) if isinstance(labels, dict) else []
        raise ValueError(f'titles must identify every retained group exactly once; missing={missing}, extra={extra}')
    for native, title in labels.items():
        if isinstance(title, str):
            title = dict(label=title)
        if (not isinstance(title, dict) or set(title) - {'label', 'analysis'}
                or not isinstance(title.get('label'), str) or not title['label'].strip()
                or not isinstance(title.get('analysis', ''), str)):
            raise ValueError(f'invalid title for native group {native}')
        labels[native] = dict(label=title['label'], analysis=title.get('analysis', ''))

    mapping = read_json(vector_map)
    note_shorts = {vector['note_id']: vector['note_short_id'] for vector in mapping['vectors']}
    original_notes = {note['note_id']: note['text'] for note in read_json(notes)['notes']}
    root_notes = next(group['note_ids'] for group in projected['retained_groups']
                      if group['node_id'] == projected['root_node_id'])
    if any(not original_notes[note].strip() for note in root_notes):
        raise ValueError('category source notes must be nonempty')
    references = sorted((dict(note_id=note, note_short_id=note_shorts[note])
                         for note in root_notes), key=lambda reference: reference['note_short_id'])
    nodes = [dict(node_id=group['node_id'], **labels[group['node_id']],
                  children=group['children'],
                  note_ids=sorted(note_shorts[note] for note in group['direct_note_ids']))
             for group in projected['retained_groups']]
    result = dict(schema_version=1, hierarchy_id=f'{viewer["run_id"]}-note-categories',
                  source_sha256=viewer['sources']['notes']['sha256'],
                  root_node_id=projected['root_node_id'], notes=references, nodes=nodes)
    blob = json_bytes(result)

    retained = []
    for group in projected['retained_groups']:
        short_ids = sorted(note_shorts[note] for note in group['note_ids'])
        retained.append(dict(node_id=group['node_id'], native_node_ids=group['native_node_ids'],
                             children=group['children'], note_ids=short_ids,
                             note_ids_sha256=hashlib.sha256('\n'.join(short_ids).encode('utf-8')).hexdigest()))
    retained_native = {group['native_node_ids'][0] for group in projected['retained_groups']}
    aliased_native = {native for group in projected['retained_groups']
                      for native in group['native_node_ids'][1:]}
    native_groups = []
    for group in viewer['groups']:
        native = group['id']
        disposition = ('retained' if native in retained_native else
                       'equal-note-set' if native in aliased_native else 'fewer-than-two-notes')
        native_groups.append(dict(native_node_id=native,
                                  retained_node_id=projected['native_to_retained'][str(native)],
                                  disposition=disposition, vector_ids=group['vector_ids'],
                                  note_ids=sorted(note_shorts[note] for note in group['note_ids'])))
    sources = {name: file_source(run / f'{name}.json')
               for name in ('configuration', 'hierarchy', 'evidence', 'viewer')}
    sources.update(vector_map=file_source(vector_map), notes=file_source(notes), titles=file_source(titles))
    provenance = dict(schema_version='diffusion-categories-projection-v1', run_id=viewer['run_id'],
                      root_node_id=projected['root_node_id'],
                      policy=dict(equal_note_sets='collapse-parent-child-edges', minimum_choice_note_count=2,
                                  retained_native_id='highest-ancestor', child_order='saved-order',
                                  direct_notes='full-membership-minus-retained-child-union'),
                      sources=sources, categories_sha256=hashlib.sha256(blob).hexdigest(),
                      native_to_retained=projected['native_to_retained'],
                      retained_groups=retained, native_groups=native_groups)
    provenance_blob = json_bytes(provenance)

    created = []
    try:
        with ExitStack() as stack:
            files = []
            for path in (output, projection_output):
                files.append(stack.enter_context(path.open('xb')))
                created.append(path)
            files[0].write(blob)
            files[1].write(provenance_blob)
    except BaseException:
        for path in created:
            path.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--vector-map', type=Path, required=True)
    parser.add_argument('--notes', type=Path, required=True)
    parser.add_argument('--titles', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--projection-output', type=Path, required=True)
    args = parser.parse_args()
    try:
        export(args.run, args.vector_map, args.notes, args.titles, args.output, args.projection_output)
    except (KeyError, TypeError, ValueError, OSError) as error:
        parser.error(str(error))
    print(f'Exported saved diffusion note categories to {args.output}')
    print(f'Exported native group provenance to {args.projection_output}')


if __name__ == '__main__':
    main()
