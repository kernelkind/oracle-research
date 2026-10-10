"""Small, reviewed canonical construction using native experiment receipts.

Preparation and application are offline. Optional execution delegates to experiment.run.
Each incoming local node is compared against one frozen canonical state.
"""
from copy import deepcopy
from graphlib import TopologicalSorter, CycleError
import hashlib
import json
from pathlib import Path

try:
    from . import experiment as workflow
except ImportError:
    import experiment as workflow


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _check(state):
    for path, digest in state['sources'].items():
        if _hash(path) != digest:
            raise ValueError('trial source changed: ' + path)
    if state.get('comparison_policy'):
        from .canonical_comparison_policy import check_state
        check_state(state)
    if state.get('graph_search'):
        from .canonical_graph_policy import check_state
        check_state(state)
    if 'queue' in state:
        expected = _legacy_queue(state)
        queue = state['queue']
        if (not isinstance(queue, list) or len(queue) != len(expected)
                or any(not isinstance(row, dict) or set(row) != {'local', 'mapped_parent'}
                       for row in queue)):
            raise ValueError('invalid canonical execution queue')
        def keyed(rows):
            return {(row['local']['note_id'], row['local']['number']): row for row in rows}
        try:
            if keyed(queue) != keyed(expected) or len(keyed(queue)) != len(queue):
                raise ValueError('canonical queue differs from roots and children')
        except (KeyError, TypeError) as exc:
            raise ValueError('invalid canonical execution queue') from exc
        if (type(state['index']) is not int or state['index'] != len(state['steps'])
                or not 0 <= state['index'] <= len(queue)
                or queue[:state['index']] != [
                    {'local': step['local'], 'mapped_parent': step.get('mapped_parent')}
                    for step in state['steps']]):
            raise ValueError('canonical execution queue differs from processed history')


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


def _save_once(path, value):
    if path.exists():
        if workflow.read(path) != value:
            raise ValueError('prepared step differs from saved state')
    else:
        workflow.write(path, value)


def _legacy_queue(state):
    return [{'local': local, 'mapped_parent': None} for local in state['roots']] + state.get('children', [])


def execution_queue(state):
    """The processed prefix keeps its indices when new roots follow children."""
    return state['queue'] if 'queue' in state else _legacy_queue(state)


def _incoming(state):
    row = execution_queue(state)[state['index']]
    return row['local'], row['mapped_parent']


def _eligible(state, local, mapped_parent):
    if mapped_parent is not None and not any(n['id'] == mapped_parent for n in state['nodes']):
        raise ValueError('unknown mapped canonical parent')
    return [node for node in state['nodes'] if node['id'] == mapped_parent or all(
        entry['note_id'] != local['note_id'] for entry in node['entries'])]


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
            if (answer.get('status') != 'valid' or previous not in reverse
                    or not (answer.get('receipt') or {}).get('record_sha256')
                    or output.get('meaning') != step['selected_meaning']
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


def _run_following(result, run_next, max_new_attempts, attempt_budget_path):
    if run_next and result['experiment'] is not None:
        batch = workflow.run(Path(result['experiment']), max_new_attempts,
                             attempt_budget_path=attempt_budget_path, include_request_preview=False)
        payloads = [json.loads(c['inputs']['INPUT_JSON']) for c in batch['cases']]
        result['next_review'] = {
            'local': payloads[0]['local'], 'summary': batch['summary'],
            'cases': [{**{k: c[k] for k in ('id', 'status', 'parsed', 'receipt',
                                          'reused', 'error', 'failure_kind',
                                          'elapsed_seconds') if k in c},
                       **({'canonical': p['canonical']} if 'canonical' in p else {})}
                      for c, p in zip(batch['cases'], payloads)]}
    return result


def _prepare(directory, state):
    _check(state)
    if state['index'] == len(execution_queue(state)):
        state.update(status='complete', experiment=None)
        if state.get('independent_meanings'):
            state['phase'] = 'complete'
    else:
        step = directory / f"step-{state['index']:03}"
        step.mkdir(exist_ok=True)
        local, mapped_parent = _incoming(state)
        source = {'schema_version': state.get('local_schema_version', 1), 'corpus': state['corpus']}
        eligible = _eligible(state, local, mapped_parent)
        meaning = state.get('local_meanings', {}).get(str(state['index']))
        if state.get('independent_meanings'):
            state['phase'] = 'comparison' if meaning else 'meaning'
            if meaning is None:
                step = step / 'meaning'
                step.mkdir(exist_ok=True)
                eligible = []
        if eligible and meaning and state.get('graph_search'):
            from .canonical_graph_policy import select
            eligible = select(state, eligible)
            record = state['graph_search_steps'][str(state['index'])]
            number = len(record['phases']) - int(bool(record['phases']) and 'answers' not in record['phases'][-1])
            step = step / f'graph-search-{number:03}'
            step.mkdir(exist_ok=True)
        if eligible and meaning and state.get('candidate_selection') and not state.get('comparison_policy') and not state.get('graph_search'):
            from .canonical_selective_trial import select_comparisons
            eligible = select_comparisons(state, local, meaning['meaning'], eligible)
        if eligible and meaning and state.get('comparison_policy'):
            from .canonical_comparison_policy import select
            eligible = select(state, local, mapped_parent, meaning, eligible)
            if state['comparison_policy_steps'][str(state['index'])]['phase'] == 'verification':
                step = step / 'verification'
                step.mkdir(exist_ok=True)
        spec = deepcopy(state['comparison_spec'] if eligible else state['bootstrap_spec'])
        if eligible:
            source['schema_version'] = state['schema_version']
            source.update(canonical_states={'current': state['nodes']}, pairs=[
                {'id': node['id'], 'local': local,
                 'canonical': {'state': 'current', 'id': node['id']}, 'review': {}}
                for node in eligible])
            if state.get('independent_meanings'):
                for pair in source['pairs']:
                    pair['local_meaning_from'] = {k: meaning[k] for k in ('experiment', 'case')}
            adapter = 'hierarchy_node_pairs'
        else:
            source['nodes'] = [{'id': 'bootstrap', 'local': local, 'review': {}}]
            adapter = 'hierarchy_local_nodes'
        spec['dataset'] = {'adapter': adapter, 'path': 'source.json'}
        _save_once(step / 'source.json', source)
        _save_once(step / 'spec.json', spec)
        exp = step / 'experiment'
        if not exp.exists():
            args = workflow.parser().parse_args([
                'prepare', str(exp), '--spec', str(step / 'spec.json'),
                '--history-root', state.get('history_root', str(directory.parent))])
            workflow.prepare(args, include_request_preview=False)
        else:
            workflow.report(exp, include_request_preview=False)  # Validate existing receipts on resume.
        state.update(status='awaiting_review', experiment=str(exp))
        if eligible and meaning and state.get('comparison_policy'):
            from .canonical_comparison_policy import bind_experiment
            bind_experiment(state, exp)
        if eligible and meaning and state.get('graph_search'):
            from .canonical_graph_policy import bind_experiment
            bind_experiment(state, exp, eligible)
    workflow.write(directory / 'state.json', state)
    return summary(state)


def summary(state):
    return {key: state[key] for key in ('status', 'index', 'experiment')} | {
        'roots': len(state['roots']), 'canonical_nodes': len(state['nodes']),
        'children': len(state.get('children', [])),
        'held': sum(s['status'] == 'held' for s in state['steps']),
        'last_step': state['steps'][-1] if state['steps'] else None} | (
            {'phase': state['phase']} if state.get('independent_meanings') else {})


def prepare_trial(spec_path, directory, base_trial=None, comparison_policy=None, history_root=None, graph_search=False):
    spec_path, directory = Path(spec_path).resolve(), Path(directory).resolve()
    cfg = workflow.read(spec_path)
    required = {'schema_version', 'corpus', 'bootstrap_spec', 'comparison_spec'}
    fields = set(cfg) - {'independent_meanings', 'local_schema_version'}
    if (fields not in (required | {'note_ids'}, required | {'roots'})
            or type(cfg.get('independent_meanings', False)) is not bool
            or type(cfg['schema_version']) is not int or cfg['schema_version'] not in (1, 2)):
        raise ValueError('invalid canonical trial spec')
    local_schema = cfg.get('local_schema_version', 1)
    if (type(local_schema) is not int or local_schema not in (1, 3, 4)
            or local_schema != 1 and not cfg.get('independent_meanings')):
        raise ValueError('tree inputs require a supported local schema and independent meanings')
    corpus = workflow.resolve(cfg['corpus'], spec_path.parent)
    notes = {n['note_id']: n for n in workflow.read(corpus)['notes']}
    roots = []
    if 'roots' in cfg:
        if not isinstance(cfg['roots'], list) or not cfg['roots']:
            raise ValueError('trial requires unique existing local roots')
        seen = set()
        for local in cfg['roots']:
            if (not isinstance(local, dict) or set(local) != {'note_id', 'number'}
                    or not all(isinstance(value, str) for value in local.values())):
                raise ValueError('trial requires unique existing local roots')
            key = (local['note_id'], local['number'])
            if (key in seen or local['note_id'] not in notes or '.' in local['number']
                    or not any(s['number'] == local['number']
                               for s in notes[local['note_id']]['subjects'])):
                raise ValueError('trial requires unique existing local roots')
            seen.add(key)
            roots.append(dict(local))
    else:
        if not isinstance(cfg['note_ids'], list) or not cfg['note_ids'] or len(set(cfg['note_ids'])) != len(cfg['note_ids']):
            raise ValueError('trial requires unique note IDs')
        for note_id in cfg['note_ids']:
            if note_id not in notes:
                raise ValueError('unknown note ID')
            selected = sorted((s for s in notes[note_id]['subjects'] if '.' not in s['number']),
                              key=lambda s: int(s['number']))
            roots.extend({'note_id': note_id, 'number': s['number']} for s in selected)
    if not roots:
        raise ValueError('no local roots')
    sources = {str(spec_path): _hash(spec_path), str(corpus): _hash(corpus)}
    state = {'schema_version': cfg['schema_version'], 'corpus': str(corpus), 'roots': roots,
             'index': 0, 'nodes': [], 'steps': [], 'sources': sources,
             'status': 'preparing', 'experiment': None}
    if cfg.get('independent_meanings'):
        state.update(independent_meanings=True, local_meanings={})
    if 'local_schema_version' in cfg:
        state['local_schema_version'] = local_schema
    if history_root is not None:
        state['history_root'] = str(Path(history_root).resolve())
    for field in ('bootstrap_spec', 'comparison_spec'):
        path = workflow.resolve(cfg[field], spec_path.parent)
        spec = workflow.read(path)
        prompt = workflow.resolve(spec['prompt']['path'], path.parent)
        spec['prompt']['path'] = str(prompt)
        sources.update({str(path): _hash(path), str(prompt): _hash(prompt)})
        state[field] = spec
    if base_trial is not None:
        base_trial = Path(base_trial).resolve()
        base_path = base_trial / 'state.json'
        base_bytes = base_path.read_bytes()
        base = json.loads(base_bytes)
        _check(base)
        if (base['status'] != 'complete' or base['schema_version'] != 2
                or state['schema_version'] != 2 or not base.get('independent_meanings')
                or not state.get('independent_meanings') or 'shape' in base
                or base['index'] != len(execution_queue(base))
                or [step['index'] for step in base['steps']] != list(range(base['index']))):
            raise ValueError('growth requires a completed raw independent-meaning schema 2 trial')
        _ancestors(base['nodes'])
        if state.get('local_schema_version', 1) != base.get('local_schema_version', 1):
            raise ValueError('growth cannot replace the frozen local input schema')
        if state['corpus'] != base['corpus']:
            raise ValueError('growth requires the same frozen corpus')
        for path, digest in sources.items():
            if path in base['sources'] and base['sources'][path] != digest:
                raise ValueError('growth cannot replace a frozen base source')
        old_entries = {(row['local']['note_id'], row['local']['number'])
                       for row in execution_queue(base)}
        if any((local['note_id'], local['number']) in old_entries for local in roots):
            raise ValueError('growth roots must not replay previously selected local entries')
        specs = {field: state[field] for field in ('bootstrap_spec', 'comparison_spec')}
        state = deepcopy(base)
        state.update(specs)
        if history_root is not None:
            state['history_root'] = str(Path(history_root).resolve())
        state['queue'] = deepcopy(execution_queue(base)) + [
            {'local': local, 'mapped_parent': None} for local in roots]
        state['roots'].extend(roots)
        state['sources'].update(sources)
        state['sources'][str(base_path)] = hashlib.sha256(base_bytes).hexdigest()
        state.update(status='preparing', experiment=None, base_trial=str(base_trial))
    if comparison_policy is not None or state.get('comparison_policy'):
        from .canonical_comparison_policy import prepare_policy
        prepare_policy(state, comparison_policy)
    if graph_search:
        if comparison_policy is not None:
            raise ValueError('graph search cannot combine with a shortlist policy')
        from .canonical_graph_policy import enable
        enable(state)
    if directory.exists():
        raise ValueError('trial destination already exists')
    directory.mkdir(parents=True)
    workflow.write(directory / 'state.json', state)
    return _prepare(directory, state)


def fork_trial(source, directory, *, graph_search=False, at_step=None):
    """Preserve a raw trial and optionally restart at a saved construction step."""
    source, directory = Path(source).resolve(), Path(directory).resolve()
    with workflow.locked(source):
        source_path = source / 'state.json'
        source_bytes = source_path.read_bytes()
        state = json.loads(source_bytes)
        if at_step is not None:
            if type(at_step) is not int or not 0 <= at_step < len(state['steps']):
                raise ValueError('snapshot requires an existing construction step')
            step = state['steps'][at_step]
            state.update(index=at_step, nodes=deepcopy(step['before']),
                         steps=state['steps'][:at_step], status='preparing', experiment=None)
            for name in ('comparison_policy_steps', 'comparison_selections', 'graph_search_steps'):
                if name in state:
                    state[name] = {key: value for key, value in state[name].items() if int(key) < at_step}
        if graph_search:
            from .canonical_graph_policy import enable
            enable(state)
        _check(state)
        queue = execution_queue(state)
        if ('shape' in state or state['status'] not in ('preparing', 'awaiting_review')
                or type(state['index']) is not int or not 0 <= state['index'] < len(queue)
                or state['index'] != len(state['steps'])
                or [step['index'] for step in state['steps']] != list(range(state['index']))
                or queue[:state['index']] != [
                    {'local': step['local'], 'mapped_parent': step.get('mapped_parent')}
                    for step in state['steps']]):
            raise ValueError('fork requires an unfinished raw canonical trial')
        _ancestors(state['nodes'])
        if directory.exists():
            raise ValueError('trial destination already exists')
        state = deepcopy(state)
        state['sources'][str(source_path)] = hashlib.sha256(source_bytes).hexdigest()
        state.update(status='preparing', experiment=None)
        directory.mkdir(parents=True)
        workflow.write(directory / 'state.json', state)
        return _prepare(directory, state)


def prepare_child_trial(base_trial, directory, note_ids=None, comparison_policy=None, graph_search=False):
    """Freeze one immediate unprocessed child level from a completed trial.

    All immediate local children remain candidates, including children of held
    originals. The finished graph's one-note rule does not filter candidates.
    """
    base_trial, directory = Path(base_trial).resolve(), Path(directory).resolve()
    base_path = base_trial / 'state.json'
    base_bytes = base_path.read_bytes()
    state = json.loads(base_bytes)
    _check(state)
    if state['status'] != 'complete' or state['schema_version'] != 2:
        raise ValueError('child trial requires a completed schema 2 canonical trial')
    _ancestors(state['nodes'])  # Validate the saved graph without changing it.
    corpus = {n['note_id']: n for n in workflow.read(state['corpus'])['notes']}
    if note_ids is not None:
        selected_notes = {local['note_id'] for local in state['roots']}
        if not note_ids or len(set(note_ids)) != len(note_ids) or set(note_ids) - selected_notes:
            raise ValueError('child scope requires unique notes already selected in the trial')
    processed = {(step['local']['note_id'], step['local']['number']) for step in state['steps']}
    children, seen = [], {}
    parents = [{'id': node['id'], 'entries': node['entries']} for node in state['nodes']]
    parents.extend({'id': None, 'entries': [step['local']]} for step in state['steps']
                   if step['status'] == 'held')
    for node in parents:
        for entry in node['entries']:
            if note_ids is not None and entry['note_id'] not in note_ids:
                continue
            selected = sorted((row for row in corpus[entry['note_id']]['subjects']
                               if '.' in row['number'] and row['number'].rsplit('.', 1)[0] == entry['number']),
                              key=lambda row: tuple(int(n) for n in row['number'].split('.')))
            for row in selected:
                key = (entry['note_id'], row['number'])
                if key in processed:
                    continue
                if key in seen:
                    if seen[key] != node['id']:
                        raise ValueError('local child has multiple mapped canonical parents')
                    continue
                seen[key] = node['id']
                children.append({'local': {'note_id': entry['note_id'], 'number': row['number']},
                                 'mapped_parent': node['id']})
    if directory.exists():
        raise ValueError('trial destination already exists')
    state = deepcopy(state)
    state.setdefault('children', []).extend(children)
    if 'queue' in state:
        state['queue'].extend(deepcopy(children))
    state['sources'][str(base_path)] = hashlib.sha256(base_bytes).hexdigest()
    state.update(status='preparing', experiment=None, base_trial=str(base_trial))
    if comparison_policy is not None or state.get('comparison_policy'):
        from .canonical_comparison_policy import prepare_policy
        prepare_policy(state, comparison_policy)
    if graph_search:
        if comparison_policy is not None:
            raise ValueError('graph search cannot combine with a shortlist policy')
        from .canonical_graph_policy import enable
        enable(state)
    directory.mkdir(parents=True)
    workflow.write(directory / 'state.json', state)
    return _prepare(directory, state)


def _placement(state, local, meaning, values):
    """Build and check a prospective graph without changing the frozen state."""
    nodes = deepcopy(state['nodes'])
    equivalent = [identifier for identifier, answer in values.items()
                  if answer.get('relation') == 'equivalent']
    target = equivalent[0] if len(equivalent) == 1 else f"C{state['index'] + 1:03}"
    if equivalent:
        node = next(n for n in nodes if n['id'] == target)
        if local not in node['entries']:
            node['entries'].append(local)
    else:
        note = next(n for n in workflow.read(state['corpus'])['notes'] if n['note_id'] == local['note_id'])
        entry = next(s for s in note['subjects'] if s['number'] == local['number'])
        node = dict(id=target, subject=entry['subject'], meaning=meaning, entries=[local], parents=[])
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
    if state.get('candidate_selection') and state['candidate_selection'].get('schema_version') != 2:
        from .canonical_selective_trial import placement_improves
        if not placement_improves(state, nodes):
            return nodes, target, 'selected entry does not improve its declared browsing task; graph preserved', None
    return nodes, target, None, None


def advance_trial(directory, meaning_case, comment, hold=None, concurrency=None, *,
                  run_next=False, max_new_attempts=None, attempt_budget_path=None,
                  automatic=False, expected_experiment=None):
    if concurrency is not None and concurrency < 1:
        raise ValueError("concurrency must be positive")
    if run_next:
        if max_new_attempts is None or max_new_attempts < 1:
            raise ValueError('--run-next requires positive --max-new-attempts')
    elif max_new_attempts is not None or attempt_budget_path is not None:
        raise ValueError('execution options require --run-next')
    directory = Path(directory).resolve()
    with workflow.locked(directory):
        state = workflow.read(directory / 'state.json')
        _check(state)
        if expected_experiment is not None and state['experiment'] != str(expected_experiment):
            raise ValueError('trial experiment changed before automatic application')
        if state['status'] == 'complete':
            return summary(state)
        if state['experiment'] is None:
            return _prepare(directory, state)
        if not comment or not comment.strip():
            raise ValueError('a meaning/placement review comment is required')
        if hold is not None and not hold.strip():
            raise ValueError('an explicit hold reason is required')
        result = workflow.report(state['experiment'], include_request_preview=False)
        cases = result['cases']
        graph_record = None
        if state.get('graph_search') and state.get('phase') == 'comparison':
            from .canonical_graph_policy import checked_cases
            graph_record = state['graph_search_steps'][str(state['index'])]
            cases = checked_cases(state, cases)
        policy_record = None
        if state.get('comparison_policy') and state.get('phase') == 'comparison':
            from .canonical_comparison_policy import checked_cases
            policy_record = state['comparison_policy_steps'][str(state['index'])]
            cases = checked_cases(state, cases)
            if any(case['status'] == 'unrun' for case in cases):
                raise ValueError('canonical comparison verification is pending; cannot advance')
        if any(c['status'] != 'valid' for c in cases) and not hold:
            raise ValueError('all comparisons must be valid before review/application')
        values = {c['id']: c['parsed'] for c in cases if c['status'] == 'valid'}
        if meaning_case not in {c['id'] for c in cases}:
            raise ValueError('select a returned meaning case')
        reason = hold
        if graph_record is not None and not reason and all(
                case['status'] == 'valid' and case['parsed']['relation'] != 'uncertain' for case in cases):
            from .canonical_graph_policy import finish_phase
            if not finish_phase(state, cases)['complete']:
                state.update(experiment=None, status='preparing')
                return _run_following(_prepare(directory, state), run_next,
                                      max_new_attempts, attempt_budget_path)
        if policy_record is not None:
            from .canonical_comparison_policy import verification_hold
            reason = reason or verification_hold(state, cases)
        local, mapped_parent = _incoming(state)
        frozen = None
        if state.get('independent_meanings'):
            if state['phase'] == 'meaning':
                case = cases[0]
                if case['status'] == 'valid':
                    frozen = {'experiment': state['experiment'], 'case': case['id'],
                              'meaning': case['parsed']['meaning'], 'receipt': case['receipt'],
                              'local': local, 'comment': comment}
                    if automatic:
                        frozen.update(reviewer='automatic', semantic_review='pending')
                    state['local_meanings'][str(state['index'])] = frozen
                if not reason and frozen['meaning'] is not None and _eligible(state, local, mapped_parent):
                    if concurrency is not None:
                        for field in ('bootstrap_spec', 'comparison_spec'):
                            state[field]['runner']['concurrency'] = concurrency
                        frozen['next_concurrency'] = concurrency
                    state.update(experiment=None, status='preparing')
                    return _run_following(_prepare(directory, state), run_next,
                                          max_new_attempts, attempt_budget_path)
            else:
                frozen = state['local_meanings'][str(state['index'])]
                if any(v['meaning'] != frozen['meaning'] for v in values.values()):
                    reason = reason or 'comparison did not copy the independently fixed local meaning'
        if not reason and mapped_parent is not None and state.get('phase') != 'meaning' and values[mapped_parent]['relation'] not in (
                'canonical_contains_local', 'equivalent'):
            reason = reason or 'local child does not fit its mapped canonical parent; manual review required'
        if any(v['meaning'] is None or v.get('relation') == 'uncertain' for v in values.values()):
            reason = reason or 'uncertain meaning or relationship'
        equivalent = [k for k, v in values.items() if v.get('relation') == 'equivalent']
        if len(equivalent) > 1:
            reason = reason or 'multiple canonical equivalents require review; no canonical merge'
        before = deepcopy(state['nodes'])
        nodes = deepcopy(before)
        meaning = frozen['meaning'] if frozen is not None else values.get(meaning_case, {}).get('meaning')
        target = equivalent[0] if len(equivalent) == 1 else f"C{state['index'] + 1:03}"
        settled_contradiction = None
        if not reason:
            nodes, target, reason, settled_contradiction = _placement(state, local, meaning, values)
        if not reason and policy_record is not None:
            from .canonical_comparison_policy import start_verification
            if start_verification(state, nodes, target, cases):
                if concurrency is not None:
                    for field in ('bootstrap_spec', 'comparison_spec'):
                        state[field]['runner']['concurrency'] = concurrency
                state.update(experiment=None, status='preparing')
                return _run_following(_prepare(directory, state), run_next,
                                      max_new_attempts, attempt_budget_path)
        if reason:
            nodes = before
        step = {'index': state['index'], 'local': local, 'experiment': state['experiment'],
                'status': 'held' if reason else 'equivalent' if equivalent else 'added',
                'reason': reason, 'meaning_case': meaning_case, 'selected_meaning': meaning,
                'reviewer': 'automatic' if automatic else 'agent',
                'comment': comment, 'canonical_id': None if reason else target,
                'before': before, 'after': deepcopy(nodes),
                'answers': [{'id': c['id'], 'output': c.get('parsed'),
                             'receipt': c.get('receipt'), 'status': c['status'],
                             **{k: c[k] for k in ('error', 'failure_kind', 'reused',
                                                 'elapsed_seconds', 'experiment') if k in c}}
                            for c in cases]}
        if automatic:
            step['semantic_review'] = 'pending'
        if settled_contradiction is not None:
            step['settled_relation_contradiction'] = settled_contradiction
            if equivalent:
                step['equivalence_contradiction'] = deepcopy(settled_contradiction)
        if frozen is not None:
            step['local_meaning_from'] = deepcopy(frozen)
        if mapped_parent is not None:
            step['mapped_parent'] = mapped_parent
        if str(state['index']) in state.get('comparison_selections', {}):
            step['comparison_selection'] = deepcopy(state['comparison_selections'][str(state['index'])])
        if policy_record is not None:
            step['comparison_selection'] = deepcopy(policy_record)
            queried = [case['id'] for case in cases]
            step['comparison_selection'].update(queried=queried,
                omitted=[identifier for identifier in policy_record['plan']['binding']['eligible']
                         if identifier not in queried], omitted_relation='unknown')
            step['comparison_phases'] = deepcopy(policy_record['comparison_phases'])
            step['comparison_experiments'] = [phase['experiment'] for phase in policy_record['comparison_phases']]
        if graph_record is not None:
            step['graph_search'] = deepcopy(graph_record.get('result', dict(complete=False)))
            step['comparison_experiments'] = [phase['experiment'] for phase in graph_record['phases']]
        if concurrency is not None:
            for field in ('bootstrap_spec', 'comparison_spec'):
                state[field]['runner']['concurrency'] = concurrency
            step['next_concurrency'] = concurrency
        state['steps'].append(step)
        state.update(nodes=nodes, index=state['index'] + 1, experiment=None, status='preparing')
        workflow.write(directory / 'state.json', state)
        result = _prepare(directory, state)
        return _run_following(result, run_next, max_new_attempts, attempt_budget_path)
