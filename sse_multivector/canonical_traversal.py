"""Native, resumable construction using the approved traversal-v24 policy.

Preparation and advancement are offline. The run command executes their loop
through the shared runner, which owns admission, caching, retries and accounting.
Three local searches may overlap; graph changes are serialized and guarded.
"""
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextvars import copy_context
from copy import deepcopy
from graphlib import TopologicalSorter
from pathlib import Path
import json
import fcntl
import sys

from . import canonical_trial as trial
from . import experiment as workflow
from .canonical_graph_search import GraphSearch, RELATIONS
from .hierarchy_node_pairs import project_fixed_meanings, project_symmetric_fixed_meanings, validate
from .canonical_receipts import _failure_receipts, _producer_hold


POLICY = 'traversal-v24'
_CODE_FILES = ('canonical_traversal.py', 'canonical_graph_search.py', 'canonical_trial.py',
               'hierarchy_node_pairs.py', 'canonical_receipts.py', 'experiment_inputs.py',
               'experiment_extension.py')


def validate_consolidation(raw, payload):
    value = json.loads(raw, object_pairs_hook=workflow.engine._position_decoder().unique_object)
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'title', 'meaning', 'children'}:
        raise ValueError('consolidation must return null or title, meaning and children')
    for field in ('title', 'meaning'):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError('consolidation '+field+' must be nonempty text')
    children = value['children']
    offered = {n['id'] for n in payload['siblings']}
    if (not isinstance(children, list) or any(not isinstance(c, str) for c in children)
            or len(set(children)) != len(children) or not 2 <= len(children) < len(offered)
            or not set(children) <= offered):
        raise ValueError('consolidation children must be a proper subset of at least two offered siblings')
    return value


def _inventory(notes):
    levels = {}
    for note in notes:
        seen = set()
        for entry in note['subjects']:
            number = entry['number']
            parts = number.split('.')
            if number in seen or any(not p.isdigit() or int(p) < 1 for p in parts):
                raise ValueError('invalid or duplicate local number')
            seen.add(number)
            levels.setdefault(len(parts), {}).setdefault(note['note_id'], []).append(
                dict(local=dict(note_id=note['note_id'], number=number), subject=entry['subject']))
        if any('.' in n and n.rsplit('.', 1)[0] not in seen for n in seen):
            raise ValueError('missing original local parent')
    result = []
    for level in sorted(levels):
        pending = deque(deque(rows) for rows in levels[level].values())
        while pending:
            rows = pending.popleft()
            result.append(rows.popleft())
            if rows:
                pending.append(rows)
    return result


def check_state(state):
    if state.get('traversal_policy') != POLICY:
        raise ValueError('unknown traversal policy')
    for path, digest in state['sources'].items():
        if trial._hash(path) != digest:
            raise ValueError('trial source changed: '+path)
    if (len(state['searches']) > 3 or state['index'] != len(state['steps'])
            or not 0 <= state['cursor'] <= len(state['inventory'])):
        raise ValueError('invalid traversal construction state')
    selected = [s['local'] for s in state['steps'] if s['local'] is not None] + [
        s['local'] for s in state['searches']]
    if selected != [r['local'] for r in state['inventory'][:state['cursor']]]:
        raise ValueError('traversal selection order differs from saved history')
    trial._ancestors(state['nodes'])


def check_synthetic(node):
    """Synthetic nodes have native proposal evidence instead of invented notes."""
    reference = node['synthetic']
    if not isinstance(reference, dict) or set(reference) != {'experiment', 'case', 'receipt'}:
        raise ValueError('invalid synthetic producer reference')
    cases = workflow.report(reference['experiment'], only=[reference['case']],
                            include_request_preview=False)['cases']
    if (len(cases) != 1 or cases[0]['status'] != 'valid'
            or cases[0].get('receipt') != reference['receipt']
            or (cases[0].get('parsed') or {}).get('title') != node['subject']
            or (cases[0].get('parsed') or {}).get('meaning') != node['meaning']):
        raise ValueError('synthetic meaning does not match native producer evidence')


def _experiment(directory, state, role, spec, source, *, adapter='generic', local=None):
    step = directory / f"batch-{len(state['experiments']):05}"
    step.mkdir(exist_ok=True)
    spec = deepcopy(spec)
    spec['dataset'] = dict(adapter=adapter, path='source.json')
    trial._save_once(step/'source.json', source)
    trial._save_once(step/'spec.json', spec)
    experiment = step/'experiment'
    if not experiment.exists():
        args = workflow.parser().parse_args(['prepare', str(experiment), '--spec',
            str(step/'spec.json'), '--history-root', state['history_root']])
        workflow.prepare(args, include_request_preview=False)
    plan, _, _ = workflow.load(experiment)
    record = dict(role=role, experiment=str(experiment), local=local,
                  inputs={c['id']: c['inputs'] for c in plan['cases']})
    state['experiments'].append(record)
    return len(state['experiments'])-1


def _collect(state):
    """Validate native receipts on every advancement, including saved answers."""
    from experiment_runner.scheduling import snapshot
    for record in state['experiments']:
        if 'answers' not in record:
            _, config, _ = workflow.load(record['experiment'])
            if snapshot(config.run_directory)['state'] in ('running', 'pausing'):
                # A failed attempt may still be awaiting its native provider retry.
                continue
        cases = workflow.report(record['experiment'], include_request_preview=False)['cases']
        if {c['id']: c['inputs'] for c in cases} != record['inputs']:
            raise ValueError('traversal experiment input changed')
        answers = [dict(id=c['id'], output=c.get('parsed'), receipt=c.get('receipt'),
                        status=c['status'], experiment=record['experiment']) for c in cases]
        failures = _failure_receipts(record['experiment'], cases)
        if any(c['status'] == 'invalid_receipt' for c in cases) or failures is None:
            raise ValueError('invalid traversal receipt')
        if 'answers' in record and answers != record['answers']:
            raise ValueError('saved traversal answers changed')
        retryable = any(workflow.engine.provider_retry_delay(failure) is not None
                        for failure in failures)
        if not any(c['status'] == 'unrun' for c in cases) and not retryable:
            record['answers'] = answers
            if record['role'] in ('meaning', 'consolidation'):
                record['producer_hold'] = _producer_hold(record['experiment'], cases)


def _canonical_input(nodes, identifier):
    """Build recursive evidence only for a reached comparison, not every node."""
    by_id = {n['id']: n for n in nodes}
    children = {k: [] for k in by_id}
    for node in nodes:
        for parent in node['parents']:
            children[parent].append(node['id'])
    result = {k: by_id[identifier][k] for k in ('id', 'subject', 'meaning', 'parents')}
    for kind, links in (('ancestors', {k: n['parents'] for k, n in by_id.items()}),
                        ('descendants', children)):
        reached, pending = set(), list(links[identifier])
        while pending:
            other = pending.pop()
            if other not in reached:
                reached.add(other)
                pending.extend(links[other])
        result[kind] = [{k: other[k] for k in ('id', 'subject', 'meaning', 'parents')}
                        for other in nodes if other['id'] in reached]
    return result


def _payload(slot, canonical):
    original = dict(local=dict(entry=dict(subject=slot['subject']), meaning=slot['meaning']),
                    canonical=canonical)
    case = dict(id=canonical['id'], inputs={'INPUT_JSON': json.dumps(original, ensure_ascii=False)})
    project = project_symmetric_fixed_meanings if slot.get('symmetric') else project_fixed_meanings
    return project(case)['inputs']


def _symmetric(state):
    return 'A_contains_B' in state['comparison_spec']['runner']['output_schema'][
        'properties']['relation']['enum']


def _comparison_output(slot, output):
    if slot.get('symmetric'):
        validate(json.dumps(output), diagnostics=True, symmetric=True)
        return dict(output, meaning=slot['meaning'], relation={
            'A_contains_B': 'local_contains_canonical',
            'B_contains_A': 'canonical_contains_local'}.get(output['relation'], output['relation']))
    return output


def _new_search(directory, state, row, ordinal):
    slot = dict(**deepcopy(row), ordinal=ordinal, snapshot=deepcopy(state['nodes']),
                cache={}, experiments=[], meaning=None, symmetric=_symmetric(state))
    source = dict(schema_version=state['local_schema_version'], corpus=state['corpus'],
                  nodes=[dict(id='meaning', local=row['local'], review={})])
    slot['producer'] = _experiment(directory, state, 'meaning', state['bootstrap_spec'],
                                  source, adapter='hierarchy_local_nodes', local=row['local'])
    return slot


def _search_work(directory, state, slot):
    """Apply unchanged saved answers before preparing another reached frontier."""
    if slot.get('hold'):
        return True, {}
    producer = state['experiments'][slot['producer']]
    if producer.get('producer_hold'):
        slot['hold'] = producer['producer_hold']
        return True, {}
    if slot['meaning'] is None:
        producer = state['experiments'][slot['producer']]
        if 'answers' not in producer:
            return False, {}
        case = producer['answers'][0]
        meaning = (case['output'] or {}).get('meaning')
        if case['status'] != 'valid' or not isinstance(meaning, str) or not meaning.strip():
            slot['hold'] = 'local meaning unresolved; manual review required'
            return True, {}
        slot['meaning'] = meaning
    for number in slot['experiments']:
        record = state['experiments'][number]
        if 'answers' not in record:
            return False, {}
        for answer in record['answers']:
            try:
                output = _comparison_output(slot, answer['output'] or {})
            except ValueError:
                slot['hold'] = 'invalid comparison diagnostics; manual review required'
                return True, {}
            if (answer['status'] != 'valid' or output.get('relation') not in RELATIONS
                    or 'meaning' in output and output['meaning'] != slot['meaning']):
                slot['hold'] = 'invalid comparison or changed fixed meaning; manual review required'
                return True, {}
            slot['cache'][workflow.inputs.digest(record['inputs'][answer['id']])] = deepcopy(answer)
    inputs = {}
    search = GraphSearch(slot['snapshot'])
    values = {}
    while search.candidates():
        ready = search.candidates()
        for identifier in ready:
            if identifier not in inputs:
                inputs[identifier] = _canonical_input(slot['snapshot'], identifier)
        saved = {identifier: slot['cache'].get(workflow.inputs.digest(_payload(slot, inputs[identifier])))
                 for identifier in ready}
        cached = {identifier: answer for identifier, answer in saved.items() if answer is not None}
        if cached:
            for identifier, answer in cached.items():
                values[identifier] = dict(_comparison_output(slot, answer['output']), meaning=slot['meaning'])
            search.record({identifier: values[identifier]['relation'] for identifier in cached})
            continue
        cases = [dict(id=identifier, inputs=_payload(slot, inputs[identifier]),
                      evidence=dict(local=slot.get('local'), snapshot_sha256=workflow.inputs.digest(slot['snapshot']),
                                    producer=slot['producer'])) for identifier in ready]
        number = _experiment(directory, state, 'comparison', state['comparison_spec'],
                             dict(cases=cases), local=slot.get('local'))
        slot['experiments'].append(number)
        return False, {}
    result = search.result()
    slot['search_result'] = result
    if result['held']:
        slot['hold'] = 'uncertain relationship; manual review required'
    for identifier, relation in result['inferred'].items():
        values[identifier] = dict(meaning=slot['meaning'], relation=relation)
    return True, values


def _note_sets(nodes):
    parents = {n['id']: n['parents'] for n in nodes}
    children = {n: [] for n in parents}
    represented = {n['id']: {e['note_id'] for e in n['entries']} for n in nodes}
    for child, links in parents.items():
        for parent in links:
            children[parent].append(child)
    for parent in reversed(tuple(TopologicalSorter(parents).static_order())):
        for child in children[parent]:
            represented[parent].update(represented[child])
    return represented, children


def _stopping(state):
    represented, children = _note_sets(state['nodes'])
    isolated = {next(iter(notes)) for notes in represented.values() if len(notes) == 1}
    equal = [dict(parent=parent, child=child) for parent, kids in children.items()
             for child in kids if not represented[child] < represented[parent]]
    multi = [dict(id=identifier, note_ids=sorted(notes))
             for identifier, notes in represented.items() if not children[identifier] and len(notes) > 1]
    return dict(individual_access=set(state['note_ids']) <= isolated, strict_edges=not equal,
                single_note_leaves=all(len(notes) == 1 for identifier, notes in represented.items()
                                       if not children[identifier]), multi_note_leaves=multi,
                missing_individual=sorted(set(state['note_ids'])-isolated), equal_note_edges=equal)


def _mapped_parent(state, slot):
    local = slot.get('local')
    if local is None or '.' not in local['number']:
        return None
    original = dict(note_id=local['note_id'], number=local['number'].rsplit('.', 1)[0])
    matches = [n['id'] for n in state['nodes'] if original in n['entries']]
    if len(matches) > 1:
        raise ValueError('original parent mapped to multiple canonical nodes')
    return matches[0] if matches else None


def _triggers(state, target):
    by_id = {n['id']: n for n in state['nodes']}
    for parent in by_id[target]['parents'] or [None]:
        siblings = [n['id'] for n in state['nodes'] if parent in n['parents']] if parent else [
                        n['id'] for n in state['nodes'] if not n['parents']]
        if len(siblings) >= 6:
            pending = next((g for g in state['pending_groups'] if g['parent'] == parent), None)
            if pending is None:
                state['pending_groups'].append(dict(parent=parent, added=target))
            else:
                pending['added'] = target


def _apply(state, slot, values, comment, *, group=None):
    reason = slot.get('hold')
    parent = _mapped_parent(state, slot)
    if not reason and parent and values.get(parent, {}).get('relation') not in (
            'canonical_contains_local', 'equivalent'):
        reason = 'original parent containment unchecked or contradicted; manual review required'
    equivalent = [k for k, v in values.items() if v['relation'] == 'equivalent']
    if len(equivalent) > 1:
        reason = reason or 'multiple canonical equivalents require review; no canonical merge'
    before = deepcopy(state['nodes'])
    prospective, target, witness = before, None, None
    if not reason:
        prospective, target, reason, witness = trial._placement(
            state, slot.get('local'), slot['meaning'], values, subject=slot['subject'])
    if not reason and group is not None:
        offered = group['siblings']
        contained = [k for k in offered if values.get(k, {}).get('relation') == 'local_contains_canonical']
        parent = group['parent']
        if (parent and values.get(parent, {}).get('relation') != 'canonical_contains_local'
                or not set(slot['nominated']) <= set(contained)
                or not 2 <= len(contained) < len(offered)):
            reason = 'synthetic target or nominated-child containment not established'
        else:
            represented, children = _note_sets(prospective)
            previous_edges = {(p, n['id']) for n in before for p in n['parents']}
            new_edges = [(p, n['id']) for n in prospective for p in n['parents']
                         if target in (p, n['id']) and (p, n['id']) not in previous_edges]
            if any(not represented[c] < represented[p] for p, c in new_edges):
                reason = 'synthetic grouping does not strictly narrow note sets'
            after_choices = len(children[parent]) if parent else sum(not n['parents'] for n in prospective)
            if after_choices >= len(offered):
                reason = reason or 'synthetic grouping does not reduce immediate choices'
    if not reason:
        state['nodes'] = prospective
        if group is not None and not equivalent:
            node = next(n for n in state['nodes'] if n['id'] == target)
            producer = state['experiments'][slot['producer']]
            node['synthetic'] = dict(experiment=producer['experiment'], case='consolidate',
                                     receipt=producer['answers'][0]['receipt'])
    answers = []
    for identifier in slot.get('search_result', {}).get('queried', []):
        inputs = _payload(slot, _canonical_input(slot['snapshot'], identifier))
        answers.append(deepcopy(slot['cache'][workflow.inputs.digest(inputs)]))
    state['steps'].append(dict(index=state['index'], local=slot.get('local'),
        selected_meaning=slot['meaning'], status='held' if reason else 'equivalent' if equivalent else 'added',
        reason=reason, canonical_id=None if reason else target, before=before,
        after=deepcopy(state['nodes']), answers=answers, comment=comment,
        reviewer='agent', experiment=state['experiments'][slot['producer']]['experiment'],
        graph_search=slot.get('search_result'), mapped_parent=parent,
        settled_relation_contradiction=witness))
    state['index'] += 1
    if not reason and not equivalent:
        _triggers(state, target)
    return reason


def _consolidate(directory, state, comment):
    active = state.get('consolidation')
    if active is None and state['pending_groups']:
        event = state['pending_groups'].pop(0)
        parent = event['parent']
        siblings = [n for n in state['nodes'] if parent in n['parents']] if parent else [
            n for n in state['nodes'] if not n['parents']]
        if len(siblings) < 6:
            return True
        def supplied(n):
            return dict(id=n['id'], title=n['subject'], meaning=n['meaning'])
        payload = dict(parent=None if parent is None else supplied(next(
            n for n in state['nodes'] if n['id'] == parent)), siblings=[supplied(n) for n in siblings])
        number = _experiment(directory, state, 'consolidation', state['consolidation_spec'],
            dict(cases=[dict(id='consolidate', inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False)})]),
            adapter='canonical_consolidation')
        active = dict(parent=parent, siblings=[n['id'] for n in siblings], producer=number,
                      snapshot=deepcopy(state['nodes']))
        state['consolidation'] = active
    if active is None:
        return True
    record = state['experiments'][active['producer']]
    if 'answers' not in record:
        return False
    answer = record['answers'][0]
    output = answer['output']
    if 'slot' not in active:
        if record.get('producer_hold'):
            active['outcome'] = record['producer_hold']
        elif output is None or answer['status'] != 'valid':
            active['outcome'] = 'null' if answer['status'] == 'valid' else 'invalid'
        else:
            active['slot'] = dict(local=None, subject=output['title'], meaning=output['meaning'],
                nominated=output['children'], producer=active['producer'], cache={}, experiments=[],
                snapshot=active['snapshot'], symmetric=_symmetric(state))
    if 'slot' in active:
        complete, values = _search_work(directory, state, active['slot'])
        if not complete:
            return False
        reason = _apply(state, active['slot'], values, comment, group=active)
        active['outcome'] = reason or 'placed'
    state['consolidations'].append(deepcopy(active))
    state['consolidation'] = None
    return True


def _schedule(directory, state, comment):
    # Advance independent snapshots even while consolidation blocks placements.
    for slot in state['searches']:
        _search_work(directory, state, slot)
    while state['status'] != 'complete':
        if state.get('consolidation') or state['pending_groups']:
            if not _consolidate(directory, state, comment):
                break
            continue
        if state.pop('check_stopping', False):
            state['stopping'] = _stopping(state)
            if (state['stopping']['individual_access'] and state['stopping']['strict_edges']
                    and state['stopping']['single_note_leaves']):
                state['status'] = 'complete'
                _stop_dispatch(state)
                break
        while len(state['searches']) < 3 and state['cursor'] < len(state['inventory']):
            ordinal = state['cursor']
            state['searches'].append(_new_search(directory, state, state['inventory'][ordinal], ordinal))
            state['cursor'] += 1
        if not state['searches']:
            state['status'] = 'exhausted'
            break
        slot = state['searches'][0]
        complete, values = _search_work(directory, state, slot)
        if not complete:
            break
        if not slot.get('hold') and slot['snapshot'] != state['nodes']:
            slot['snapshot'] = deepcopy(state['nodes'])
            complete, values = _search_work(directory, state, slot)
            if not complete:
                break
        _apply(state, slot, values, comment)
        state['searches'].pop(0)
        state['check_stopping'] = True
    workflow.write(directory/'state.json', state)
    return summary(state)


def _stop_dispatch(state, reason='traversal stopping conditions met'):
    """Use the runner's existing pause contract; admitted calls may finish."""
    from experiment_runner.scheduling import snapshot, pause
    for record in state['experiments']:
        if 'answers' in record:
            continue
        _, config, _ = workflow.load(record['experiment'])
        if snapshot(config.run_directory)['state'] in ('running', 'pausing'):
            try:
                pause(config.run_directory, reason=reason)
            except ValueError:
                if snapshot(config.run_directory)['state'] in ('running', 'pausing'):
                    raise


def summary(state):
    return dict(status=state['status'], index=state['index'], selected=state['cursor'],
                canonical_nodes=len(state['nodes']), active_searches=len(state['searches']),
                held=sum(s['status'] == 'held' for s in state['steps']),
                stopping=state.get('stopping'),
                experiments=[] if state['status'] == 'complete' else [
                    r['experiment'] for r in state['experiments'] if 'answers' not in r])


def prepare(spec_path, directory, history_root=None):
    spec_path, directory = Path(spec_path).resolve(), Path(directory).resolve()
    cfg = workflow.read(spec_path)
    fields = {'schema_version', 'corpus', 'note_ids', 'local_schema_version',
              'bootstrap_spec', 'comparison_spec', 'consolidation_spec'}
    if (not isinstance(cfg, dict) or set(cfg) != fields or type(cfg['schema_version']) is not int
            or cfg['schema_version'] != 1 or type(cfg['local_schema_version']) is not int
            or cfg['local_schema_version'] not in (1, 3, 4)
            or not isinstance(cfg['note_ids'], list) or not cfg['note_ids']
            or any(not isinstance(n, str) or not n for n in cfg['note_ids'])
            or len(set(cfg['note_ids'])) != len(cfg['note_ids'])):
        raise ValueError('invalid canonical traversal spec')
    corpus = workflow.resolve(cfg['corpus'], spec_path.parent)
    rows = workflow.read(corpus)['notes']
    notes = {n['note_id']: n for n in rows}
    if len(notes) != len(rows) or set(cfg['note_ids']) - notes.keys():
        raise ValueError('unknown or duplicate corpus note')
    inventory = _inventory([notes[n] for n in cfg['note_ids']])
    if any(not notes[n]['subjects'] for n in cfg['note_ids']):
        raise ValueError('selected note has no local nodes')
    sources = {str(spec_path): trial._hash(spec_path), str(corpus): trial._hash(corpus)}
    state = dict(schema_version=2, traversal_policy=POLICY, corpus=str(corpus),
        note_ids=cfg['note_ids'], local_schema_version=cfg['local_schema_version'], inventory=inventory,
        roots=[r['local'] for r in inventory if '.' not in r['local']['number']],
        nodes=[], steps=[], index=0, cursor=0, searches=[], experiments=[],
        pending_groups=[], consolidation=None, consolidations=[], status='constructing', sources=sources,
        history_root=str(Path(history_root).resolve() if history_root else directory.parent))
    for field in ('bootstrap_spec', 'comparison_spec', 'consolidation_spec'):
        path = workflow.resolve(cfg[field], spec_path.parent)
        value = workflow.read(path)
        runner = value['runner']
        if 'output_schema_path' in runner:
            if 'output_schema' in runner:
                raise ValueError('choose output_schema or output_schema_path')
            schema_path = workflow.resolve(runner.pop('output_schema_path'), path.parent)
            runner['output_schema'] = workflow.read(schema_path)
            sources[str(schema_path)] = trial._hash(schema_path)
        if 'runner_binary' in runner:
            runner['runner_binary'] = str(workflow.engine._resolve_executable(
                runner['runner_binary'], 'runner_binary', path.parent))
        if runner.get('auth_file'):
            runner['auth_file'] = str(workflow.resolve(runner['auth_file'], path.parent))
        schema = value.get('runner', {}).get('output_schema')
        if field != 'consolidation_spec' and not isinstance(schema, dict):
            raise ValueError(field+' requires a JSON output schema')
        if field == 'consolidation_spec' and schema is not None:
            raise ValueError('consolidation_spec must omit output_schema; its adapter validates null or proposal')
        if field == 'comparison_spec' and set(schema.get('properties', {}).get(
                'relation', {}).get('enum', [])) not in (RELATIONS,
                    {'equivalent', 'A_contains_B', 'B_contains_A', 'neither', 'uncertain'}):
            raise ValueError('comparison_spec must use local/canonical or symmetric A/B relation labels')
        prompt = workflow.resolve(value['prompt']['path'], path.parent)
        value['prompt']['path'] = str(prompt)
        sources.update({str(path): trial._hash(path), str(prompt): trial._hash(prompt)})
        state[field] = value
    for name in _CODE_FILES:
        path = Path(__file__).with_name(name).resolve()
        sources[str(path)] = trial._hash(path)
    if directory.exists():
        raise ValueError('traversal destination already exists')
    directory.mkdir(parents=True)
    workflow.write(directory/'state.json', state)
    return _schedule(directory, state, 'Initial native preparation')


def advance(directory, comment):
    if not isinstance(comment, str) or not comment.strip():
        raise ValueError('an advancement comment is required')
    directory = Path(directory).resolve()
    with workflow.locked(directory):
        state = workflow.read(directory/'state.json')
        check_state(state)
        _collect(state)
        if state['status'] == 'complete':
            # Finish retaining already-dispatched results; no new work or placement.
            workflow.write(directory/'state.json', state)
            return summary(state)
        return _schedule(directory, state, comment)


def _resume_sources(directory, reason):
    """Record an explicitly reviewed code fix; frozen data remains unchanged."""
    if reason is None:
        return
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('runner upgrade reason must be nonempty text')
    with workflow.locked(directory):
        state = workflow.read(directory/'state.json')
        allowed = {str(Path(__file__).with_name(name).resolve()) for name in _CODE_FILES}
        before, after = {}, {}
        for path, digest in state['sources'].items():
            current = trial._hash(path)
            if current != digest:
                if path not in allowed:
                    raise ValueError('trial source changed: '+path)
                before[path], after[path] = digest, current
        if after:
            from experiment_runner.scheduling import snapshot
            for record in state['experiments']:
                _, config, _ = workflow.load(record['experiment'])
                if snapshot(config.run_directory)['state'] in ('running', 'pausing'):
                    raise ValueError('finish active experiments before a construction code upgrade')
            state.setdefault('source_upgrades', []).append(dict(
                reason=reason, before=before, after=after, index=state['index'],
                graph_sha256=workflow.inputs.digest(state['nodes'])))
            state['sources'].update(after)
        check_state(state)
        if after:
            workflow.write(directory/'state.json', state)


def run(directory, attempt_budget, comment='Automated traversal construction',
        runner_upgrade_reason=None):
    """Run native batches and advance after each completion until stopped.

    Four batch coordinators allow three local searches and consolidation to
    overlap. They do not set provider concurrency; the shared runner does that.
    Each batch is launched at most once per invocation, including partial runs.
    """
    directory, attempt_budget = Path(directory).resolve(), Path(attempt_budget).resolve()
    budget = workflow.engine.PersistentAttemptBudget(attempt_budget)
    budget.remaining()  # Validate the existing allowance before any dispatch.
    with (directory/'.traversal-run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('traversal execution is already active') from error
        settings = dict(attempt_budget=str(attempt_budget))
        trial._save_once(directory/'execution-settings.json', settings)
        _resume_sources(directory, runner_upgrade_reason)
        active, attempted, errors = {}, set(), {}
        result = advance(directory, comment)
        stopped = False
        with ThreadPoolExecutor(max_workers=4) as pool:
            try:
                while True:
                    terminal = result['status'] in ('complete', 'exhausted')
                    if not terminal and not stopped:
                        for experiment in result['experiments']:
                            if experiment not in attempted and len(active) < 4:
                                context = copy_context()
                                future = pool.submit(context.run, workflow.run, Path(experiment),
                                    attempt_budget_path=attempt_budget, include_request_preview=False,
                                    runner_upgrade_reason=runner_upgrade_reason)
                                active[future] = experiment
                                attempted.add(experiment)
                    if not active:
                        break
                    finished, _ = wait(active, return_when=FIRST_COMPLETED)
                    completed = []
                    for future in finished:
                        experiment = active.pop(future)
                        completed.append(experiment)
                        try:
                            future.result()
                        except (workflow.engine.RunnerError, ValueError, OSError) as error:
                            errors[experiment] = str(error)
                    result = advance(directory, comment)
                    # Successful partial results are collected. Do not repeatedly
                    # relaunch unfinished cases after pause, exhausted allowance or
                    # infrastructure failure. Resume explicitly with this command.
                    if set(completed) & set(result['experiments']):
                        stopped = True
                    print('Traversal: '+json.dumps({k: result[k] for k in
                        ('status', 'index', 'canonical_nodes', 'held')}), file=sys.stderr)
            finally:
                if active:
                    for future in active:
                        future.cancel()
                    _stop_dispatch(workflow.read(directory/'state.json'),
                                   reason='traversal execution stopped')
        # All admitted calls have drained. Collect their receipts without changing
        # a completed graph; unfinished batches remain available for native resume.
        result = advance(directory, comment)
        result['execution_status'] = (result['status'] if result['status'] != 'constructing'
            else 'attempt_budget_exhausted' if budget.remaining() == 0 else 'blocked')
        result['blocked_experiments'] = result['experiments'] if stopped else []
        result['errors'] = [dict(experiment=path, error=error) for path, error in errors.items()]
        workflow.write(directory/'run-summary.json', result)
        return result
