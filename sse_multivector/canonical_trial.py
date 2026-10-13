"""Canonical graph checks shared by construction and saved-data tools."""
from copy import deepcopy
from graphlib import TopologicalSorter, CycleError
import hashlib
from pathlib import Path

try:
    from . import experiment as workflow
except ImportError:
    import experiment as workflow


def _check(state):
    if state.get('generation_policy'):
        from .hierarchy_generation import check_state
        check_state(state)
        return
    for path, digest in state['sources'].items():
        if _hash(path) != digest:
            raise ValueError('trial source changed: ' + path)
    _ancestors(state['nodes'])


def execution_queue(state):
    """Read the saved local selection order without constructing new work."""
    if 'inventory' in state:
        return [dict(local=row['local'], mapped_parent=None) for row in state['inventory']]
    if 'queue' in state:
        return state['queue']
    return [dict(local=local, mapped_parent=None)
        for local in state['roots']] + state.get('children', [])


def _incoming(state):
    row = execution_queue(state)[state['index']]
    return row['local'], row['mapped_parent']


def _eligible(state, local, mapped_parent):
    return list(state['nodes'])


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _ancestors(nodes):
    parents = {n['id']: set(n['parents']) for n in nodes}
    if any(p not in parents for ps in parents.values() for p in ps):
        raise ValueError('unknown canonical parent')
    result = {}
    for node in TopologicalSorter(parents).static_order():
        result[node] = set(parents[node])
        for parent in parents[node]:
            result[node].update(result[parent])
    return result


def _note_sets(nodes):
    parents = {n['id']: n['parents'] for n in nodes}
    children = {n: [] for n in parents}
    represented = {n['id']: {e['note_id'] for e in n['entries']} | set(n.get('note_ids', []))
                   for n in nodes}
    for child, links in parents.items():
        for parent in links:
            children[parent].append(child)
    for parent in reversed(tuple(TopologicalSorter(parents).static_order())):
        for child in children[parent]:
            represented[parent].update(represented[child])
    return represented, children


def _save_once(path, value):
    if path.exists():
        if workflow.read(path) != value:
            raise ValueError('prepared step differs from saved state')
    else:
        workflow.write(path, value)


def _settled_relation_contradiction(state, target, ancestors, *, equivalent=False):
    """A new placement cannot change a settled pair between fixed meanings."""
    current = {node['id']: node for node in state['nodes']}
    before_ancestors = _ancestors(state['nodes'])
    changed = {identifier for identifier in current
               if ancestors[identifier].intersection(current) != before_ancestors[identifier]}
    if not changed:
        return None
    reverse = {'equivalent': 'equivalent', 'neither': 'neither',
               'canonical_contains_local': 'local_contains_canonical',
               'local_contains_canonical': 'canonical_contains_local'}

    def relation(source, other, branches):
        return ('canonical_contains_local' if other in branches[source] else
                'local_contains_canonical' if source in branches[other] else 'neither')

    for step in state['steps']:
        source = step.get('canonical_id')
        if (step['status'] not in ('added', 'equivalent') or source not in current
                or source not in changed and not any(a['id'] in changed for a in step['answers'])):
            continue
        after = {node['id']: node for node in step['after']}
        before = {node['id']: node for node in step['before']}
        if after.get(source, {}).get('meaning') != current[source]['meaning']:
            continue
        for answer in step['answers']:
            other = answer['id']
            output = answer.get('output')
            previous = output.get('relation') if output else None
            symmetric = isinstance(output, dict) and set(output) == {
                'questions', 'answers', 'relation', 'reason'}
            if symmetric:
                previous = {'A_contains_B': 'local_contains_canonical',
                            'B_contains_A': 'canonical_contains_local'}.get(previous, previous)
            if (answer.get('status') != 'valid' or previous not in reverse
                    or not (answer.get('receipt') or {}).get('record_sha256')
                    or not symmetric and output.get('meaning') != step['selected_meaning']
                    or other not in current or other == source
                    or before.get(other, {}).get('meaning') != current[other]['meaning']):
                continue
            prior_graph = relation(source, other, before_ancestors)
            actual = relation(source, other, ancestors)
            if prior_graph == actual or previous == actual:
                continue
            witness = {'source': source, 'other': other,
                       'previous_step': step['index'],
                       'previous_experiment': answer.get('experiment', step['experiment']),
                       'previous_answer': deepcopy(answer),
                       'previous_relation': previous, 'before_relation': prior_graph,
                       'current_relation': actual, 'current_relation_from': 'proposed_graph'}
            if equivalent and target in (source, other):
                witness['equivalent_to'] = target
                if other == target:
                    witness.update(source=target, other=source, previous_relation=reverse[previous],
                                   before_relation=reverse[prior_graph], current_relation=reverse[actual])
            return witness
    return None


def _placement(state, local, meaning, values, *, subject=None):
    """Build and check a prospective graph without changing the frozen state."""
    nodes = deepcopy(state['nodes'])
    equivalent = [identifier for identifier, answer in values.items()
                  if answer.get('relation') == 'equivalent']
    target = equivalent[0] if len(equivalent) == 1 else f"C{state['index'] + 1:03}"
    if equivalent:
        node = next(n for n in nodes if n['id'] == target)
        if local is not None and local not in node['entries']:
            node['entries'].append(local)
    else:
        if subject is None:
            note = next(n for n in workflow.read(state['corpus'])['notes'] if n['note_id'] == local['note_id'])
            entry = next(s for s in note['subjects'] if s['number'] == local['number'])
            subject = entry['subject']
        node = dict(id=target, subject=subject, meaning=meaning,
                    entries=[] if local is None else [local], parents=[])
        nodes.append(node)
    by_id = {n['id']: n for n in nodes}
    for identifier, answer in values.items():
        if answer.get('relation') == 'canonical_contains_local':
            node['parents'] = sorted(set(node['parents']) | {identifier})
        elif answer.get('relation') == 'local_contains_canonical':
            other = by_id[identifier]
            other['parents'] = sorted(set(other['parents']) | {target})
    try:
        ancestors = _ancestors(nodes)
    except CycleError:
        return nodes, target, 'proposed placement creates a cycle', None
    for identifier, answer in values.items():
        if identifier == 'bootstrap':
            continue
        actual = ('equivalent' if identifier == target else
                  'canonical_contains_local' if identifier in ancestors[target] else
                  'local_contains_canonical' if target in ancestors[identifier] else 'neither')
        if actual != answer['relation']:
            return nodes, target, (f"contradiction at {identifier}: graph implies {actual}, "
                                   f"answer says {answer['relation']}"), None
    witness = _settled_relation_contradiction(state, target, ancestors, equivalent=bool(equivalent))
    if witness:
        kind = 'equivalence' if equivalent else 'settled relation'
        reason = (f"{kind} contradiction at {witness['other']}: settled answer is "
                  f"{witness['previous_relation']}, graph changes {witness['before_relation']} "
                  f"to {witness['current_relation']}; manual review required")
        return nodes, target, reason, witness
    for n in nodes:
        parents = n['parents']
        n['parents'] = [p for p in parents if not any(p in ancestors[q] for q in parents if q != p)]
    return nodes, target, None, None
