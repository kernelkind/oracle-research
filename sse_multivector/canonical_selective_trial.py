"""Bounded selection of useful original entries for native canonical trials.

Preparation is offline. Similarity nominates comparisons, never relationships.
This small-trial policy is not a production ANN index or semantic certification.
"""
from copy import deepcopy
import hashlib
from pathlib import Path

from . import canonical_trial as trial
from . import experiment as workflow
from .canonical_selection_ranking import MAX_ROWS, rank_candidates


def _graph(nodes):
    ancestors = trial._ancestors(nodes)
    children = {node['id']: [] for node in nodes}
    notes = {node['id']: {entry['note_id'] for entry in node['entries']} for node in nodes}
    for node in nodes:
        for parent in node['parents']:
            children[parent].append(node['id'])
    for node in sorted(nodes, key=lambda node: -len(ancestors[node['id']])):
        for parent in node['parents']:
            notes[parent].update(notes[node['id']])
    roots = sorted(node['id'] for node in nodes if not node['parents'])
    return dict(notes=notes, children=children, roots=roots,
                reachable=set().union(*(notes[root] for root in roots)) if roots else set())


def _mapping(nodes):
    mapping = {}
    for node in nodes:
        for entry in node['entries']:
            key = (entry['note_id'], entry['number'])
            if key in mapping and mapping[key] != node['id']:
                raise ValueError('original entry maps to multiple canonical nodes')
            mapping[key] = node['id']
    return mapping


def _mapped_parent(local, mapping):
    return mapping.get((local['note_id'], local['number'].rsplit('.', 1)[0])) \
        if '.' in local['number'] else None


def _config(path, state, corpus):
    cfg = workflow.read(path)
    if isinstance(cfg, dict) and type(cfg.get('schema_version')) is int and cfg['schema_version'] == 2:
        fields = {'schema_version', 'max_choices', 'max_entries',
                  'local_candidate_limit', 'comparison_policy'}
        if not fields <= set(cfg) or set(cfg) - fields - {'history_root'}:
            raise ValueError('discovery selection requires bounds and one comparison policy, without expected groups')
        for field in ('max_choices', 'max_entries', 'local_candidate_limit'):
            if type(cfg[field]) is not int or not 1 <= cfg[field] <= 512:
                raise ValueError('canonical selection bounds must be integers from 1 through 512')
        if not isinstance(cfg['comparison_policy'], str) or not cfg['comparison_policy'].strip():
            raise ValueError('discovery selection comparison_policy must be a path')
        from .canonical_comparison_policy import load_policy
        policy = load_policy(workflow.resolve(cfg['comparison_policy'], path.parent))
        if state.get('comparison_policy') and state['comparison_policy'] != policy:
            raise ValueError('cannot replace a frozen canonical comparison policy')
        cfg = dict(cfg, comparison_policy=policy, subject_probe=policy['subject_probe'])
        if 'history_root' in cfg:
            if not isinstance(cfg['history_root'], str) or not cfg['history_root'].strip():
                raise ValueError('discovery selection history_root must be a path')
            cfg['history_root'] = str(workflow.resolve(cfg['history_root'], path.parent))
        frozen = state.get('candidate_selection')
        if frozen and frozen.get('schema_version') == 2 and frozen != cfg:
            raise ValueError('cannot replace a frozen discovery selection')
        return cfg
    required = {'schema_version', 'max_choices', 'max_entries', 'canonical_limit',
                'local_candidate_limit', 'topic_groups'}
    if (not isinstance(cfg, dict) or not required <= cfg.keys()
            or set(cfg) - required - {'subject_probe'}
            or type(cfg['schema_version']) is not int or cfg['schema_version'] != 1):
        raise ValueError('invalid canonical selection spec')
    for field in required - {'schema_version', 'topic_groups'}:
        if type(cfg[field]) is not int or not 1 <= cfg[field] <= 512:
            raise ValueError('canonical selection bounds must be integers from 1 through 512')
    selected = {entry['note_id'] for entry in state['roots']}
    if not isinstance(cfg['topic_groups'], list):
        raise ValueError('topic_groups must be a list')
    for task in cfg['topic_groups']:
        if (not isinstance(task, dict) or set(task) != {'local', 'note_ids'}
                or not isinstance(task['local'], dict)
                or set(task['local']) != {'note_id', 'number'}
                or not isinstance(task['note_ids'], list)
                or len(task['note_ids']) < 2 or len(set(task['note_ids'])) != len(task['note_ids'])
                or set(task['note_ids']) - selected
                or task['local']['note_id'] not in selected
                or task['local']['number'] not in corpus[task['local']['note_id']]):
            raise ValueError('topic group requires an existing local anchor and distinct selected notes')
    cfg = deepcopy(cfg)
    if 'subject_probe' in cfg:
        cfg['subject_probe'] = str(workflow.resolve(cfg['subject_probe'], path.parent))
    return cfg


def _tasks(state, cfg):
    graph, mapping = _graph(state['nodes']), _mapping(state['nodes'])
    selected = sorted({entry['note_id'] for entry in state['roots']})
    missing = [note for note in selected if note not in graph['reachable']]
    isolated = set().union(*(notes for notes in graph['notes'].values() if len(notes) == 1)) \
        if graph['notes'] else set()
    individuals = [note for note in selected if note not in isolated]
    groups = []
    for task in cfg.get('topic_groups', []):
        anchor = mapping.get((task['local']['note_id'], task['local']['number']))
        actual = graph['notes'].get(anchor, set())
        groups.append(dict(local=task['local'], node=anchor,
                           expected=task['note_ids'], actual=sorted(actual),
                           missing=sorted(set(task['note_ids']) - actual),
                           extra=sorted(actual - set(task['note_ids']))))
    pressure = ([dict(node=None, choices=graph['roots'])]
                if len(graph['roots']) > cfg['max_choices'] else [])
    pressure.extend(dict(node=identifier, choices=sorted(children))
                    for identifier, children in sorted(graph['children'].items())
                    if len(children) > cfg['max_choices'])
    equal = [dict(parent=parent, child=child)
             for parent, children in graph['children'].items() for child in children
             if graph['notes'][parent] == graph['notes'][child]]
    return dict(missing=missing, not_isolated=individuals, topic_groups=groups,
                overcrowded=pressure, equal_note_set_edges=equal)


def prepare_selection(spec_path, base_trial, directory, graph_search=False):
    spec_path, base_trial, directory = map(lambda path: Path(path).resolve(),
                                           (spec_path, base_trial, directory))
    if directory.exists():
        raise ValueError('trial destination already exists')
    base_path = base_trial / 'state.json'
    base_bytes = base_path.read_bytes()
    state = workflow.read(base_path)
    trial._check(state)
    if (state['status'] != 'complete' or state['schema_version'] != 2
            or not state.get('independent_meanings') or 'shape' in state
            or state['index'] != len(trial.execution_queue(state))):
        raise ValueError('selection requires a completed raw independent-meaning schema 2 trial')
    selected_notes = {entry['note_id'] for entry in state['roots']}
    corpus = {note['note_id']: {row['number']: row for row in note['subjects']}
              for note in workflow.read(state['corpus'])['notes'] if note['note_id'] in selected_notes}
    if (set(corpus) != selected_notes or sum(map(len, corpus.values())) > MAX_ROWS
            or len(state['nodes']) > 512):
        raise ValueError(f'bounded selection requires at most {MAX_ROWS} local entries '
                         'and 512 canonical nodes')
    cfg = _config(spec_path, state, corpus)
    discovery = cfg['schema_version'] == 2
    if not discovery and state.get('comparison_policy'):
        raise ValueError('legacy browsing selection cannot truncate a guarded comparison policy; use schema 2')
    tasks = _tasks(state, cfg)
    mapping, graph = _mapping(state['nodes']), _graph(state['nodes'])
    by_id = {node['id']: node for node in state['nodes']}
    processed = {(step['local']['note_id'], step['local']['number']) for step in state['steps']}
    available = {(note_id, number): row for note_id, rows in corpus.items()
                 for number, row in rows.items() if (note_id, number) not in processed}
    active_notes = {key[0] for key in available}
    problem = None
    missing = [note for note in tasks['missing'] if not discovery or note in active_notes]
    individuals = [note for note in tasks['not_isolated'] if not discovery or note in active_notes]
    if missing:
        problem = dict(kind='coverage', note_id=missing[0])
    elif individuals:
        problem = dict(kind='isolation', note_id=individuals[0])
    else:
        group = next((group for group in tasks['topic_groups'] if group['missing']), None)
        if group:
            problem = dict(kind='topic_group', group=group,
                           note_id=group['missing'][0], node=group['node'])
        elif tasks['overcrowded'] and not discovery:
            problem = dict(kind='choices', **tasks['overcrowded'][0])
    if discovery and problem is None and available:
        problem = dict(kind='discovery')
    status = ('requirements_met' if problem is None and not tasks['equal_note_set_edges']
              and not any(group['extra'] for group in tasks['topic_groups']) else 'unresolved')
    report = dict(schema_version=1, status=status, tasks=tasks, problem=problem,
                  semantic_review='pending', minimization_review='pending',
                  untested_relationships='unknown',
                  qualification='Fixed task and structural checks, not global optimality or semantic certification.')
    if discovery:
        report.update(status='unresolved' if available else 'inventory_exhausted', remaining_entries=len(available),
                      qualification='Bounded discovery without expected memberships. Budget or inventory '
                      'exhaustion does not establish finished-menu quality or global optimality.')
    sources = {str(spec_path): trial._hash(spec_path),
               str(base_path): hashlib.sha256(base_bytes).hexdigest()}
    if discovery:
        sources.update(cfg['comparison_policy']['sources'])
        sources[str(Path(__file__).resolve())] = trial._hash(__file__)
    chosen = None
    next_query = None
    if problem is not None and state['index'] >= cfg['max_entries']:
        report['status'] = 'entry_limit'
    elif problem is not None:
        pool = [(key, row) for key, row in available.items()
                if problem['kind'] in ('choices', 'discovery') or key[0] == problem['note_id']]
        queries = []
        if problem['kind'] == 'topic_group' and problem['node'] is not None:
            queries = [by_id[problem['node']]]
        elif problem['kind'] == 'isolation':
            queries = [node for node in state['nodes']
                       if problem['note_id'] in graph['notes'][node['id']]
                       and any(entry['note_id'] == problem['note_id'] for entry in node['entries'])]
        elif problem['kind'] == 'choices':
            queries = [by_id[identifier] for identifier in problem['choices'][:cfg['max_choices'] + 1]]
        elif problem['kind'] == 'discovery':
            queries = list(state['nodes'])
            # Advancing the entry index alongside node growth would repeatedly
            # choose the first topic. Keep the next stable node ID instead.
            if queries:
                identifiers = [node['id'] for node in queries]
                cursor = state.get('discovery_next_query')
                offset = identifiers.index(cursor) if cursor in identifiers else 0
                queries = queries[offset:] + queries[:offset]
        if not queries:
            anchor = problem.get('group', {}).get('local')
            row = corpus[anchor['note_id']][anchor['number']] if anchor else \
                next(iter(corpus[problem['note_id']].values()))
            queries = [dict(subject=row['subject'], meaning='')]
        rows = [dict(id=f'{key[0]}:{key[1]}', subject=row['subject'], meaning='') for key, row in pool]
        eligible = {f'{key[0]}:{key[1]}': {node['id'] for node in trial._eligible(
                        state, dict(note_id=key[0], number=key[1]),
                        _mapped_parent(dict(note_id=key[0], number=key[1]), mapping))}
                    for key, _ in pool} if discovery and problem['kind'] == 'discovery' else {}
        streams, order, seen, provenance = [], [], set(), []
        for query in queries:
            query_rows = [row for row in rows if query['id'] in eligible[row['id']]] \
                if eligible and 'id' in query else rows
            if not query_rows:
                continue
            ancestors = []
            for entry in query.get('entries', []):
                number = entry['number']
                while '.' in number:
                    number = number.rsplit('.', 1)[0]
                    ancestors.append(corpus[entry['note_id']][number]['subject'])
            ranked, evidence = rank_candidates(query['subject'], query['meaning'], query_rows,
                subject_probe=cfg.get('subject_probe'), query_ancestors=ancestors)
            if discovery:
                evidence['query_canonical_id'] = query.get('id')
            provenance.append(evidence)
            sources.update(evidence['sources'])
            streams.append(iter(ranked))
        while streams:
            active = []
            for stream in streams:
                identifier = next((item for item in stream if item not in seen), None)
                if identifier is not None:
                    seen.add(identifier)
                    order.append(identifier)
                    active.append(stream)
            streams = active
        keyed = {f'{key[0]}:{key[1]}': key for key, _ in pool}
        if problem['kind'] == 'isolation':
            order.sort(key=lambda identifier: _mapped_parent(
                dict(note_id=keyed[identifier][0], number=keyed[identifier][1]), mapping) is None)
        nominees = order[:cfg['local_candidate_limit']]
        report.update(nominees=nominees, ranking=provenance)
        if discovery and problem['kind'] == 'discovery' and provenance:
            identifiers = [node['id'] for node in queries]
            current = provenance[0]['query_canonical_id']
            next_query = identifiers[(identifiers.index(current) + 1) % len(identifiers)]
            report['next_discovery_query'] = next_query
        if nominees:
            key = keyed[nominees[0]]
            local = dict(note_id=key[0], number=key[1])
            chosen = dict(local=local, mapped_parent=_mapped_parent(local, mapping))
            report.update(status='selected', selected=chosen)
    trial._check(state)
    if base_path.read_bytes() != base_bytes:
        raise ValueError('canonical selection base changed during preparation')
    directory.mkdir(parents=True)
    report_path = directory / 'selection.json'
    workflow.write(report_path, report)
    if chosen is None:
        return dict(status=report['status'], report=str(report_path), tasks=tasks)
    state = deepcopy(state)
    graph_search = graph_search or state.get('graph_search', False)
    if next_query is not None:
        state['discovery_next_query'] = next_query
    state['queue'] = deepcopy(trial.execution_queue(state)) + [chosen]
    if '.' in chosen['local']['number']:
        state.setdefault('children', []).append(chosen)
    else:
        state['roots'].append(chosen['local'])
    state.update(candidate_selection=cfg, selection_report=str(report_path),
                 status='preparing', experiment=None, base_trial=str(base_trial))
    if discovery:
        if 'history_root' in cfg:
            state['history_root'] = cfg['history_root']
        if not graph_search:
            state['comparison_policy'] = deepcopy(cfg['comparison_policy'])
            from .canonical_comparison_policy import prepare_policy
            prepare_policy(state)
    sources[str(report_path)] = trial._hash(report_path)
    state['sources'].update(sources)
    if graph_search:
        from .canonical_graph_policy import enable
        enable(state)
    workflow.write(directory / 'state.json', state)
    return trial._prepare(directory, state) | dict(selection=report, report=str(report_path))


def select_comparisons(state, local, meaning, eligible):
    cfg = state['candidate_selection']
    corpus = {note['note_id']: {row['number']: row for row in note['subjects']}
              for note in workflow.read(state['corpus'])['notes']}
    row = corpus[local['note_id']][local['number']]
    ranked, provenance = rank_candidates(row['subject'], meaning,
        [dict(id=node['id'], subject=node['subject'], meaning=node['meaning']) for node in eligible],
        subject_probe=cfg.get('subject_probe'))
    _, mapped = trial._incoming(state)
    if mapped is not None:
        ranked = [mapped] + [identifier for identifier in ranked if identifier != mapped]
    queried = ranked[:cfg['canonical_limit']]
    selected = dict(queried=queried, omitted=[node['id'] for node in eligible if node['id'] not in queried],
                    mapped_parent=mapped, provenance=provenance, omitted_relation='unknown')
    state.setdefault('comparison_selections', {})[str(state['index'])] = selected
    state['sources'].update(provenance['sources'])
    by_id = {node['id']: node for node in eligible}
    return [by_id[identifier] for identifier in queried]


def placement_improves(state, nodes):
    """A selected entry must improve its declared browsing problem, not its label."""
    problem = workflow.read(state['selection_report'])['problem']
    before, after = _graph(state['nodes']), _graph(nodes)
    kind = problem['kind']
    if kind == 'discovery':
        # A bounded discovery step may establish a new individual topic before
        # a later entry can share it. Semantic/implication guards still run;
        # useful groups and strict shrinking are assessed on the finished menu.
        return True
    if kind == 'coverage':
        return problem['note_id'] in after['reachable']
    if kind == 'isolation':
        return {problem['note_id']} in after['notes'].values()
    if kind == 'topic_group':
        anchor = problem['group']['local']
        key = (anchor['note_id'], anchor['number'])
        old = before['notes'].get(_mapping(state['nodes']).get(key), set())
        new = after['notes'].get(_mapping(nodes).get(key), set())
        return len(new.intersection(problem['group']['expected'])) > len(old.intersection(problem['group']['expected']))
    parent = problem['node']
    return (len(after['roots']) < len(before['roots']) if parent is None else
            len(after['children'][parent]) < len(before['children'][parent]))
