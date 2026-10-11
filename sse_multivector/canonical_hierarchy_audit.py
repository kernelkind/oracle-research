"""Bounded, read-only structural checks on a saved canonical hierarchy.

These checks do not grade meanings or establish coverage of intended topic groups.
"""
from collections import deque
from graphlib import CycleError, TopologicalSorter
import hashlib
import json
from pathlib import Path

try:
    from . import canonical_trial
except ImportError:
    import canonical_trial


def audit_trial(directory, output, max_choices=6, work_budget=200000):
    if type(max_choices) is not int or max_choices < 1:
        raise ValueError('max_choices must be positive')
    if type(work_budget) is not int or work_budget < 1:
        raise ValueError('work_budget must be positive')
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('canonical audit output already exists')
    state_path = directory / 'state.json'
    state_bytes = state_path.read_bytes()
    state = json.loads(state_bytes)
    canonical_trial._check(state)
    used = 0

    def charge(amount=1):
        nonlocal used
        used += amount
        if used > work_budget:
            raise ValueError('canonical audit work budget exceeded; no report written')

    corpus_path = Path(state['corpus']).resolve()
    corpus_bytes = corpus_path.read_bytes()
    corpus = json.loads(corpus_bytes)
    available = {}
    for note in corpus['notes']:
        charge(1 + len(note['subjects']))
        identifier = note['note_id']
        if identifier in available:
            raise ValueError('duplicate corpus note ID')
        available[identifier] = {row['number'] for row in note['subjects']}
    charge(len(state['roots']))
    selected = {local['note_id'] for local in state['roots']}
    if selected - available.keys():
        raise ValueError('unknown selected note ID')
    nodes, children, direct = {}, {}, {}
    for row in state['nodes']:
        charge(1 + len(row['parents']) + len(row['entries']))
        identifier = row['id']
        if not isinstance(identifier, str) or identifier in nodes:
            raise ValueError('invalid or duplicate canonical node ID')
        if (not isinstance(row['parents'], list) or len(set(row['parents'])) != len(row['parents'])
                or not all(isinstance(p, str) for p in row['parents'])):
            raise ValueError('invalid canonical parents')
        if not isinstance(row['entries'], list) or not row['entries'] and not row.get('synthetic'):
            raise ValueError('canonical node requires supporting entries')
        if row.get('synthetic'):
            from .canonical_traversal import check_synthetic
            check_synthetic(row)
        seen = set()
        for entry in row['entries']:
            if not isinstance(entry, dict) or set(entry) != {'note_id', 'number'}:
                raise ValueError('invalid canonical supporting entry')
            key = (entry['note_id'], entry['number'])
            if (key in seen or key[0] not in available or key[1] not in available[key[0]]
                    or key[0] not in selected):
                raise ValueError('invalid canonical supporting entry')
            seen.add(key)
        nodes[identifier] = row
        children[identifier] = []
        direct[identifier] = {entry['note_id'] for entry in row['entries']}
    for identifier, row in nodes.items():
        for parent in row['parents']:
            if parent not in nodes:
                raise ValueError('unknown canonical parent')
            children[parent].append(identifier)
    try:
        order = list(TopologicalSorter({n: row['parents'] for n, row in nodes.items()}).static_order())
    except CycleError as exc:
        raise ValueError('canonical hierarchy contains a cycle') from exc
    represented = {}
    for identifier in reversed(order):
        notes = set(direct[identifier])
        for child in children[identifier]:
            charge(len(notes) + len(represented[child]))
            notes.update(represented[child])
        represented[identifier] = frozenset(notes)
    roots = sorted(n for n, row in nodes.items() if not row['parents'])
    reachable_notes = set()
    for root in roots:
        charge(len(represented[root]))
        reachable_notes.update(represented[root])
    violations, choice_warnings = [], []
    if len(roots) > max_choices:
        choice_warnings.append({'kind': 'too_many_roots', 'count': len(roots)})
    missing = sorted(selected - reachable_notes)
    if missing:
        violations.append({'kind': 'unreachable_notes', 'note_ids': missing})
    equal_edges, proper_edges = [], []
    for parent in order:
        if len(children[parent]) > max_choices:
            choice_warnings.append({'kind': 'too_many_children', 'node': parent,
                                    'count': len(children[parent])})
        if children[parent] and len(represented[parent]) == 1:
            violations.append({'kind': 'single_note_parent', 'node': parent})
        for child in children[parent]:
            charge(len(represented[parent]) + len(represented[child]))
            edge = {'parent': parent, 'child': child}
            if represented[child] == represented[parent]:
                equal_edges.append(edge)
                violations.append({'kind': 'equal_note_set_edge', **edge})
            elif represented[child] < represented[parent]:
                proper_edges.append(edge)
            else:
                raise ValueError('canonical child note set escapes parent')
    # One breadth-first traversal records shortest routes, without enumerating paths.
    previous = {root: None for root in roots}
    distances = {root: 1 for root in roots}
    pending = deque(roots)
    while pending:
        parent = pending.popleft()
        for child in sorted(children[parent]):
            charge()
            if child not in previous:
                previous[child] = parent
                distances[child] = distances[parent] + 1
                pending.append(child)

    def route(candidates):
        if not candidates:
            return {'status': 'not_isolated', 'node': None, 'path': [], 'option_counts': []}
        target = min(candidates, key=lambda n: (distances[n], n))
        path, current = [], target
        while current is not None:
            charge()
            path.append(current)
            current = previous[current]
        path.reverse()
        options = [len(roots)] + [len(children[n]) for n in path[:-1]]
        return {'status': 'within_choice_limit' if all(n <= max_choices for n in options)
                else 'exceeds_choice_limit', 'node': target, 'path': path,
                'option_counts': options}

    by_notes = {}
    for identifier in order:
        charge(len(represented[identifier]))
        by_notes.setdefault(represented[identifier], []).append(identifier)
    individual = []
    for note_id in sorted(selected):
        task = {'note_id': note_id, **route(by_notes.get(frozenset({note_id}), []))}
        individual.append(task)
        if task['status'] == 'not_isolated':
            violations.append({'kind': 'note_not_isolated', 'note_id': note_id})
    groups = [{'note_ids': sorted(notes), 'candidate_nodes': sorted(candidates), **route(candidates)}
              for notes, candidates in sorted(by_notes.items(), key=lambda pair: tuple(sorted(pair[0])))
              if len(notes) > 1]
    topic_groups = []
    for identifier in sorted(nodes):
        if len(represented[identifier]) > 1:
            charge(len(represented[identifier]))
            topic_groups.append({'id': identifier, 'subject': nodes[identifier]['subject'],
                                 'meaning': nodes[identifier]['meaning'],
                                 'note_ids': sorted(represented[identifier]), **route([identifier])})
    full_set = frozenset(selected)
    report = {
        'schema_version': 1, 'trial': str(directory), 'generation_status': state['status'],
        'sources': {**state['sources'], str(state_path): hashlib.sha256(state_bytes).hexdigest(),
                    str(corpus_path): hashlib.sha256(corpus_bytes).hexdigest()},
        'max_choices': max_choices, 'work': {'limit': work_budget, 'used': used},
        'done': False, 'structural_constraints_met': not violations,
        'metrics': {'nodes': len(nodes), 'edges': sum(len(v) for v in children.values()),
                    'roots': len(roots), 'max_children': max(map(len, children.values()), default=0),
                    'proper_subset_edges': len(proper_edges), 'equal_note_set_edges': len(equal_edges)},
        'nodes': {n: {'subject': nodes[n]['subject'], 'meaning': nodes[n]['meaning'],
                      'parents': nodes[n]['parents'], 'children': sorted(children[n]),
                      'direct_notes': sorted(direct[n]), 'recursive_notes': sorted(represented[n]),
                      'direct_note_count': len(direct[n]), 'recursive_note_count': len(represented[n])}
                  for n in sorted(nodes)},
        'root_menu': {'nodes': roots, 'option_count': len(roots),
                      'full_corpus_roots': [n for n in roots if represented[n] == full_set]},
        'note_coverage': {'selected': sorted(selected), 'reachable': sorted(reachable_notes),
                          'missing': missing, 'selected_count': len(selected),
                          'reachable_count': len(reachable_notes)},
        'edges': {'proper_subset': proper_edges, 'equal_note_set': equal_edges},
        'individual_tasks': individual, 'group_tasks': groups, 'topic_group_tasks': topic_groups,
        'group_task_coverage': {'status': 'unknown',
            'qualification': 'Only existing multi-note nodes and their observed note sets are tested. '
                             'Intended meaningful topic groups are unspecified; labels are not graded.'},
        'semantic_assessment': {'graded': False,
            'qualification': 'This structural audit does not establish semantic validity or completion.'},
        'violations': violations, 'choice_warnings': choice_warnings}
    canonical_trial._check(state)
    if state_path.read_bytes() != state_bytes or corpus_path.read_bytes() != corpus_bytes:
        raise ValueError('canonical audit source changed while auditing')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return {'done': False, 'structural_constraints_met': not violations,
            'report': str(output), **report['metrics'], 'violations': len(violations),
            'group_task_coverage': 'unknown', 'semantic_graded': False, 'work_used': used}
