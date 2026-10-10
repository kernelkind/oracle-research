"""Native graph-search phases for one local node against a fixed graph."""
from pathlib import Path

from .canonical_graph_search import GraphSearch
from . import experiment as workflow


def enable(state):
    if state['schema_version'] != 2 or not state.get('independent_meanings') or 'shape' in state:
        raise ValueError('graph search requires a raw independent-meaning schema 2 trial')
    if state.get('comparison_policy'):
        state['previous_comparison_policy'] = state.pop('comparison_policy')
    state['graph_search'] = True
    for name in ('canonical_graph_policy.py', 'canonical_graph_search.py', 'canonical_trial.py'):
        path = Path(__file__).with_name(name).resolve()
        digest = workflow.engine._sha256_file(path)
        if str(path) in state['sources'] and state['sources'][str(path)] != digest:
            raise ValueError('frozen graph-search code changed: ' + str(path))
        state['sources'][str(path)] = digest


def _binding(state):
    from .canonical_trial import _incoming, _eligible
    local, parent = _incoming(state)
    return dict(local=local, mapped_parent=parent,
                graph_sha256=workflow.inputs.digest(state['nodes']),
                comparison_spec_sha256=workflow.inputs.digest(state['comparison_spec']),
                eligible=[node['id'] for node in _eligible(state, local, parent)],
                meaning=state['local_meanings'][str(state['index'])])


def check_state(state):
    if state.get('graph_search') is not True or state.get('comparison_policy'):
        raise ValueError('invalid canonical graph-search configuration')
    record = state.get('graph_search_steps', {}).get(str(state['index']))
    if record is not None and record['binding'] != _binding(state):
        raise ValueError('canonical graph-search inputs changed')


def _source(state, record, identifiers):
    meaning = record['binding']['meaning']
    return dict(schema_version=state['schema_version'], corpus=state['corpus'],
        canonical_states={'current': state['nodes']}, pairs=[dict(
            id=identifier, local=record['binding']['local'],
            canonical={'state': 'current', 'id': identifier}, review={},
            local_meaning_from={key: meaning[key] for key in ('experiment', 'case')})
            for identifier in identifiers])


def checked_cases(state, current_cases=None):
    """Re-read every native phase and validate its source and saved receipts."""
    check_state(state)
    record = state['graph_search_steps'][str(state['index'])]
    cases = []
    seen = set()
    for phase in record['phases']:
        identifiers = phase['queried']
        if not identifiers or len(set(identifiers)) != len(identifiers) or seen.intersection(identifiers):
            raise ValueError('graph search repeated a canonical comparison')
        seen.update(identifiers)
        source_path = Path(phase['experiment']).parent / 'source.json'
        plan, _, _ = workflow.load(phase['experiment'])
        if (workflow.read(source_path) != _source(state, record, identifiers)
                or plan['sources'].get(str(source_path)) != workflow.engine._sha256_file(source_path)):
            raise ValueError('graph-search phase source differs from frozen inputs')
        rows = (current_cases if current_cases is not None and phase['experiment'] == state['experiment']
                else workflow.report(phase['experiment'], include_request_preview=False)['cases'])
        if [row['id'] for row in rows] != identifiers:
            raise ValueError('graph-search phase IDs changed')
        answers = [dict(id=row['id'], output=row.get('parsed'), receipt=row.get('receipt'),
                        status=row['status']) for row in rows]
        if 'answers' in phase and phase['answers'] != answers:
            raise ValueError('completed graph-search phase answers changed')
        for row in rows:
            if row['status'] == 'valid' and row['parsed']['meaning'] != record['binding']['meaning']['meaning']:
                raise ValueError('graph-search comparison changed the fixed local meaning')
            cases.append({**row, 'experiment': phase['experiment']})
    return cases


def _search(state, record):
    binding = record['binding']
    search = GraphSearch(state['nodes'], eligible=binding['eligible'],
                         required=() if binding['mapped_parent'] is None else (binding['mapped_parent'],))
    for phase in record['phases']:
        if search.candidates() != phase['queried']:
            raise ValueError('graph-search frontier differs from frozen phase')
        if 'answers' not in phase:
            break
        search.record({row['id']: row['output']['relation'] for row in phase['answers']})
    return search


def select(state, eligible):
    check_state(state)
    records = state.setdefault('graph_search_steps', {})
    record = records.setdefault(str(state['index']), dict(binding=_binding(state), phases=[]))
    if record['phases']:
        checked_cases(state)
    identifiers = _search(state, record).candidates()
    if not identifiers:
        raise ValueError('completed graph search cannot prepare another phase')
    by_id = {node['id']: node for node in eligible}
    return [by_id[identifier] for identifier in identifiers]


def bind_experiment(state, experiment, eligible):
    record = state['graph_search_steps'][str(state['index'])]
    phase = dict(experiment=str(experiment), queried=[node['id'] for node in eligible])
    if record['phases'] and 'answers' not in record['phases'][-1]:
        if record['phases'][-1] != phase:
            raise ValueError('canonical graph-search experiment changed')
    else:
        record['phases'].append(phase)


def finish_phase(state, cases):
    """Freeze validated outputs, then expose the next frontier without graph edits."""
    record = state['graph_search_steps'][str(state['index'])]
    current = [row for row in cases if row['experiment'] == state['experiment']]
    if any(row['status'] != 'valid' for row in current):
        raise ValueError('graph search requires valid native phase answers')
    record['phases'][-1]['answers'] = [dict(id=row['id'], output=row['parsed'],
        receipt=row['receipt'], status=row['status']) for row in current]
    result = _search(state, record).result()
    record['result'] = result
    return result
