"""Read and validate saved shortlist comparison evidence; no construction."""
import hashlib
from pathlib import Path
from . import experiment as workflow
from . import canonical_selection_ranking as ranking

MAX_CANONICAL_ROWS = 512


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_policy(path):
    path = Path(path).resolve()
    source = workflow.read(path)
    if (not isinstance(source, dict)
            or set(source) - {'schema_version', 'limit', 'subject_probe'}
            or not {'schema_version', 'limit'} <= set(source)
            or type(source['schema_version']) is not int or source['schema_version'] != 1
            or type(source['limit']) is not int or not 1 <= source['limit'] <= MAX_CANONICAL_ROWS):
        raise ValueError('invalid canonical comparison policy')
    sources = {str(path): _hash(path),
               str(Path(__file__).resolve()): _hash(Path(__file__).resolve()),
               str(Path(ranking.__file__).resolve()): _hash(Path(ranking.__file__).resolve())}
    probe = None
    if 'subject_probe' in source:
        if not isinstance(source['subject_probe'], str) or not source['subject_probe'].strip():
            raise ValueError('comparison policy subject_probe must be a path')
        probe = workflow.resolve(source['subject_probe'], path.parent)
        _, _, protected = ranking._saved_vectors(str(probe))
        sources.update(protected)
        for function in (ranking.load_subject_vectors, ranking.load_vectors,
                         ranking.cosine, ranking._load_request):
            code = Path(function.__code__.co_filename).resolve()
            sources[str(code)] = _hash(code)
        for filename, digest in sources.items():
            if _hash(filename) != digest:
                raise ValueError('saved comparison policy source changed: ' + filename)
    return dict(schema_version=1, path=str(path), limit=source['limit'],
                subject_probe=None if probe is None else str(probe), sources=sources)


def _binding(state, local, mapped_parent, eligible, meaning):
    return dict(local=local, mapped_parent=mapped_parent,
                graph_sha256=workflow.inputs.digest(state['nodes']),
                eligible=[node['id'] for node in eligible],
                meaning_sha256=workflow.inputs.digest(meaning),
                policy_sha256=workflow.inputs.digest(state['comparison_policy']))


def check_state(state):
    """Reject changed policy configuration and changed frozen phase inputs."""
    config = state.get('comparison_policy')
    if config is None:
        return
    if load_policy(config['path']) != config:
        raise ValueError('canonical comparison policy changed')
    record = state.get('comparison_policy_steps', {}).get(str(state['index']))
    if record is None:
        return
    from . import canonical_trial as trial
    local, mapped_parent = trial._incoming(state)
    meaning = state['local_meanings'][str(state['index'])]
    plan = record['plan']
    if (workflow.inputs.digest(plan) != record['sha256']
            or plan['binding'] != _binding(state, local, mapped_parent,
                                          trial._eligible(state, local, mapped_parent), meaning)):
        raise ValueError('canonical comparison phase plan or frozen inputs changed')
    eligible, queried = plan['binding']['eligible'], plan['queried']
    if (len(queried) != len(set(queried)) or not queried
            or len(queried) > config['limit'] or set(queried) - set(eligible)
            or plan['omitted'] != [identifier for identifier in eligible if identifier not in queried]
            or mapped_parent is not None and mapped_parent not in queried):
        raise ValueError('invalid frozen canonical shortlist')
    if record['phase'] not in ('shortlist', 'verification'):
        raise ValueError('invalid canonical comparison phase')
    if record['phase'] == 'verification':
        guard = dict(plan_sha256=record['sha256'], expected=record['guard_expected'],
                     shortlist_answers=record['shortlist_answers'])
        if workflow.inputs.digest(guard) != record['verification_sha256']:
            raise ValueError('canonical verification plan changed')
        if not record['guard_expected'] or set(record['guard_expected']) - set(plan['omitted']):
            raise ValueError('canonical verification includes an ineligible or repeated comparison')


def checked_cases(state, current_cases=None):
    """Re-read all phase receipts before application, preserving their origin."""
    check_state(state)
    record = state['comparison_policy_steps'][str(state['index'])]
    cases = []
    expected_phases = ['shortlist'] + (['verification'] if record['phase'] == 'verification' else [])
    if [phase['phase'] for phase in record['comparison_phases']] != expected_phases:
        raise ValueError('canonical comparison phases differ from frozen plan')
    for phase in record['comparison_phases']:
        expected_ids = (record['plan']['queried'] if phase['phase'] == 'shortlist'
                        else list(record['guard_expected']))
        if phase['queried'] != expected_ids:
            raise ValueError('canonical comparison phase IDs changed')
        source_path = Path(phase['experiment']).parent / 'source.json'
        meaning = state['local_meanings'][str(state['index'])]
        expected_source = dict(schema_version=state['schema_version'], corpus=state['corpus'],
            canonical_states={'current': state['nodes']}, pairs=[dict(
                id=identifier, local=record['plan']['binding']['local'],
                canonical={'state': 'current', 'id': identifier}, review={},
                local_meaning_from={key: meaning[key] for key in ('experiment', 'case')})
                for identifier in expected_ids])
        native_plan, _, _ = workflow.load(phase['experiment'])
        if (workflow.read(source_path) != expected_source
                or native_plan['sources'].get(str(source_path)) != _hash(source_path)):
            raise ValueError('canonical phase source differs from frozen graph, local entry, or meaning')
        rows = (current_cases if current_cases is not None and phase['experiment'] == state['experiment']
                else workflow.report(phase['experiment'], include_request_preview=False)['cases'])
        if [row['id'] for row in rows] != phase['queried']:
            raise ValueError('canonical phase cases differ from frozen plan')
        if any(row['status'] == 'invalid_receipt' for row in rows):
            raise ValueError('invalid canonical comparison phase receipt')
        if any(row['status'] == 'failed' for row in rows):
            from .canonical_receipts import _failure_receipts
            if _failure_receipts(Path(phase['experiment']), rows) is None:
                raise ValueError('invalid canonical comparison failure receipt')
        if phase['experiment'] != state['experiment'] and any(row['status'] != 'valid' for row in rows):
            raise ValueError('previous canonical comparison phase is no longer valid')
        cases.extend(dict(row, experiment=phase['experiment']) for row in rows)
    if len({row['id'] for row in cases}) != len(cases):
        raise ValueError('canonical comparison phases repeat a case')
    if record['phase'] == 'verification':
        previous = [{'id': row['id'], 'output': row.get('parsed'), 'receipt': row.get('receipt')}
                    for row in cases if row['experiment'] != state['experiment']]
        if previous != record['shortlist_answers']:
            raise ValueError('shortlist receipts differ from frozen verification plan')
        from .canonical_trial import _placement
        values = {row['id']: row['output'] for row in previous}
        if any(value['meaning'] != meaning['meaning'] for value in values.values()):
            raise ValueError('shortlist did not copy the frozen local meaning')
        nodes, target, reason, _ = _placement(state, record['plan']['binding']['local'],
                                              meaning['meaning'], values)
        if reason or _implied(record, nodes, target) != record['guard_expected']:
            raise ValueError('canonical verification is not the complete eligible implied closure')
    return cases


def _implied(record, nodes, target):
    from .canonical_trial import _ancestors
    ancestors = _ancestors(nodes)
    expected = {}
    for identifier in record['plan']['omitted']:
        relation = ('canonical_contains_local' if identifier in ancestors[target] else
                    'local_contains_canonical' if target in ancestors[identifier] else None)
        if relation is not None:
            expected[identifier] = relation
    return expected
