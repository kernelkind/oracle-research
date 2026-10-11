"""Shape saved canonical menus using existing nodes and witnessed containments.

A shaped candidate is separate from construction history and is not semantic gold.
"""
from collections import deque
from copy import deepcopy
from graphlib import CycleError, TopologicalSorter
import hashlib
import json
from pathlib import Path

try:
    from . import canonical_trial
    from .canonical_hierarchy_audit import audit_trial
except ImportError:
    import canonical_trial
    from canonical_hierarchy_audit import audit_trial


def finish_nodes(nodes):
    """Bypass equal-note-set parents, retaining deeper nodes and their evidence.

    Other children reconnect to surviving ancestors, never to an equal sibling.
    Rebuild from the raw graph so later note growth can restore a broad heading.
    """
    represented, children = canonical_trial._note_sets(nodes)
    omitted = {parent for parent, kids in children.items()
               if any(represented[parent] == represented[child] for child in kids)}
    parents = {n['id']: n['parents'] for n in nodes}
    surviving = {}
    for identifier in TopologicalSorter(parents).static_order():
        surviving[identifier] = ({identifier} if identifier not in omitted else
            {ancestor for parent in parents[identifier] for ancestor in surviving[parent]})
    result = []
    for node in nodes:
        if node['id'] not in omitted:
            copied = deepcopy(node)
            copied['parents'] = sorted({ancestor for parent in node['parents']
                                        for ancestor in surviving[parent]})
            result.append(copied)
    return result


def shape_trial(source_path, output_directory, work_budget=200000, max_choices=6):
    if type(work_budget) is not int or work_budget < 1:
        raise ValueError('work_budget must be positive')
    if type(max_choices) is not int or max_choices < 1:
        raise ValueError('max_choices must be positive')
    source_path, output = Path(source_path).resolve(), Path(output_directory).resolve()
    if output.exists():
        raise ValueError('canonical shape output already exists')
    source_bytes = source_path.read_bytes()
    cfg = json.loads(source_bytes)
    if (not isinstance(cfg, dict) or set(cfg) != {'schema_version', 'trial', 'roots', 'children'}
            or type(cfg['schema_version']) is not int or cfg['schema_version'] != 1):
        raise ValueError('invalid canonical shape source')
    reference = cfg['trial']
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError('canonical shape requires a trial path')
    trial = (source_path.parent / reference).resolve()
    state_path = trial / 'state.json' if trial.is_dir() else trial
    state_bytes = state_path.read_bytes()
    state = json.loads(state_bytes)
    canonical_trial._check(state)
    used = 0

    def charge(amount=1):
        nonlocal used
        used += amount
        if used > work_budget:
            raise ValueError('canonical shape work budget exceeded')

    def identifiers(values, name):
        if (not isinstance(values, list) or not all(isinstance(v, str) and v for v in values)
                or len(set(values)) != len(values)):
            raise ValueError(name + ' requires unique node IDs')
        charge(len(values))
        return values

    rows = state['nodes']
    charge(len(rows))
    original, original_children = {}, {}
    for row in rows:
        identifier = row['id']
        if not isinstance(identifier, str) or identifier in original:
            raise ValueError('invalid or duplicate original node ID')
        identifiers(row['parents'], 'original parents')
        original[identifier] = row
        original_children[identifier] = []
    for row in rows:
        for parent in row['parents']:
            if parent not in original:
                raise ValueError('unknown original parent')
            original_children[parent].append(row['id'])
    try:
        tuple(TopologicalSorter({n: row['parents'] for n, row in original.items()}).static_order())
    except CycleError as exc:
        raise ValueError('original canonical graph contains a cycle') from exc
    roots = identifiers(cfg['roots'], 'shape roots')
    if not roots or not isinstance(cfg['children'], dict):
        raise ValueError('canonical shape requires roots and children object')
    selected, edges = set(roots), set()
    for parent, targets in cfg['children'].items():
        if not isinstance(parent, str) or not parent:
            raise ValueError('invalid shape parent')
        selected.add(parent)
        for child in identifiers(targets, 'shape children'):
            if child == parent:
                raise ValueError('canonical shape cannot contain a self-link')
            selected.add(child)
            edges.add((parent, child))
    if selected - original.keys():
        raise ValueError('unknown canonical shape node')
    parents = {n: [] for n in selected}
    for parent, child in sorted(edges):
        parents[child].append(parent)
    try:
        tuple(TopologicalSorter(parents).static_order())
    except CycleError as exc:
        raise ValueError('canonical shape contains a cycle') from exc
    if set(roots) != {n for n, ps in parents.items() if not ps}:
        raise ValueError('shape roots must exactly match retained parentless nodes')
    witnesses = []
    for parent in sorted(cfg['children']):
        targets = set(cfg['children'][parent])
        if not targets:
            continue
        previous, pending = {parent: None}, deque([parent])
        outstanding = set(targets)
        while pending and outstanding:
            current = pending.popleft()
            for child in sorted(original_children[current]):
                charge()
                if child not in previous:
                    previous[child] = current
                    pending.append(child)
                    outstanding.discard(child)
        if outstanding:
            raise ValueError('selected edge is not an original transitive containment')
        for target in sorted(targets):
            path, current = [], target
            while current is not None:
                charge()
                path.append(current)
                current = previous[current]
            witnesses.append({'parent': parent, 'child': target, 'original_path': path[::-1]})
    charge(len(state['roots']))
    expected_notes = {entry['note_id'] for entry in state['roots']}
    covered_notes = set()
    for identifier in selected:
        charge(len(original[identifier]['entries']))
        covered_notes.update(entry['note_id'] for entry in original[identifier]['entries'])
    if expected_notes - covered_notes:
        raise ValueError('canonical shape drops selected notes: ' + ', '.join(sorted(expected_notes - covered_notes)))
    original_edges = {(p, row['id']) for row in rows for p in row['parents']}
    shaped_nodes = []
    for row in rows:
        if row['id'] in selected:
            copied = deepcopy(row)
            copied['parents'] = parents[row['id']]
            shaped_nodes.append(copied)
    shape = {
        'source': str(source_path), 'base_trial': str(state_path.parent),
        'roots': roots, 'edges': witnesses, 'omitted_nodes': sorted(original.keys() - selected),
        'omitted_edges': [{'parent': p, 'child': c} for p, c in sorted(original_edges - edges)],
        'semantic_certified': False, 'group_task_coverage': 'unknown',
        'qualification': 'Retained meanings and supporting entries are unchanged. '
                         'Edges use original graph reachability, assuming transitive containment. '
                         'Omitted nodes or edges are menu choices, not negative judgments or merges. '
                         'Original construction history remains in the source trial.'}
    shaped = {'schema_version': state['schema_version'], 'corpus': state['corpus'],
              'roots': deepcopy(state['roots']), 'nodes': shaped_nodes,
              'sources': {**state['sources'], str(state_path): hashlib.sha256(state_bytes).hexdigest(),
                          str(source_path): hashlib.sha256(source_bytes).hexdigest()},
              'status': 'shaped_candidate', 'shape': shape}
    canonical_trial._check(shaped)
    output.mkdir(parents=True, exist_ok=False)
    published_state = output / 'state.json'
    audit_path = output / 'audit.json'
    try:
        with published_state.open('x') as stream:
            json.dump(shaped, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        remaining = work_budget - used
        if remaining < 1:
            raise ValueError('canonical shape work budget exceeded')
        audit = audit_trial(output, audit_path, max_choices=max_choices, work_budget=remaining)
    except Exception:
        published_state.unlink(missing_ok=True)
        audit_path.unlink(missing_ok=True)
        output.rmdir()
        raise
    return {'done': False, 'candidate': str(output), 'state': str(published_state),
            'nodes': len(shaped_nodes), 'edges': len(edges), 'roots': len(roots),
            'shape_work_used': used, 'audit': audit,
            'semantic_certified': False, 'group_task_coverage': 'unknown'}
