"""Offline candidate measurements from validated native construction snapshots."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

try:
    from . import canonical_trial as trial
    from . import experiment as workflow
    from .canonical_receipts import _failure_receipts
    from .canonical_candidate_selection import evaluate_snapshots
except ImportError:
    import canonical_trial as trial
    import experiment as workflow
    from canonical_receipts import _failure_receipts
    from canonical_candidate_selection import evaluate_snapshots


def measure(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('canonical candidate measurement output already exists')
    source_bytes = source.read_bytes()
    cfg = json.loads(source_bytes)
    required = {'schema_version', 'trial', 'candidate_limits'}
    if (not isinstance(cfg, dict) or set(cfg) not in (required, required | {'menu'})
            or type(cfg['schema_version']) is not int or cfg['schema_version'] != 1
            or not isinstance(cfg['candidate_limits'], list) or not cfg['candidate_limits']
            or any(type(n) is not int or not 1 <= n <= 512 for n in cfg['candidate_limits'])
            or len(set(cfg['candidate_limits'])) != len(cfg['candidate_limits'])
            or any(not isinstance(cfg[key], str) or not cfg[key].strip()
                   for key in ('trial', 'menu') if key in cfg)):
        raise ValueError('invalid canonical candidate measurement source')
    directory = workflow.resolve(cfg['trial'], source.parent)
    state_path = directory / 'state.json'
    if state_path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('canonical candidate reference state exceeds 64 MiB limit')
    state_bytes = state_path.read_bytes()
    state = json.loads(state_bytes)
    if state.get('independent_meanings') is not True:
        raise ValueError('candidate measurement requires independently established local meanings')
    if (len(state['nodes']) > 512
            or any(len(step[field]) > 512 for step in state['steps'] for field in ('before', 'after'))):
        raise ValueError('canonical candidate reference exceeds 512 nodes per snapshot')
    pair_cases = sum(len(step['answers']) for step in state['steps']
                     if any(answer['id'] != 'bootstrap' for answer in step['answers']))
    if pair_cases > 50000:
        raise ValueError('canonical candidate reference exceeds 50000 pair cases')
    trial._check(state)
    queue = trial.execution_queue(state)
    if ('shape' in state or state['status'] != 'complete'
            or type(state['index']) is not int or state['index'] != len(queue)
            or len(state['steps']) != len(queue)
            or [step['index'] for step in state['steps']] != list(range(len(queue)))
            or queue != [{'local': step['local'], 'mapped_parent': step.get('mapped_parent')}
                         for step in state['steps']]):
        raise ValueError('candidate measurement requires a completed raw canonical trial')
    sources = {**state['sources'], str(source): hashlib.sha256(source_bytes).hexdigest(),
               str(state_path): hashlib.sha256(state_bytes).hexdigest()}

    def bind(path, expected=None):
        path = Path(path).resolve()
        actual = sources.get(str(path)) or trial._hash(path)
        if expected is not None and actual != expected:
            raise ValueError('native measurement source changed: ' + str(path))
        if str(path) in sources and sources[str(path)] != actual:
            raise ValueError('native measurement source changed: ' + str(path))
        sources[str(path)] = actual

    for path in (__file__, trial.__file__, evaluate_snapshots.__code__.co_filename):
        bind(path)

    steps = []
    previous = []
    for step in state['steps']:
        if step['before'] != previous:
            raise ValueError('canonical graph snapshots differ from saved transition history')
        trial._ancestors(step['before'])
        trial._ancestors(step['after'])
        experiment = Path(step['experiment']).resolve()
        native = workflow.report(experiment, include_request_preview=False)
        if _failure_receipts(experiment, native['cases']) is None:
            raise ValueError('saved canonical answer differs from validated native failure receipt')
        plan_path = experiment / 'experiment.json'
        plan = workflow.read(plan_path)['plan']
        bind(plan_path)
        for path, digest in plan['sources'].items():
            bind(path, digest)
        source_path = workflow.resolve(plan['dataset']['path'], experiment)
        prepared = workflow.read(source_path)
        if Path(prepared['corpus']).resolve() != Path(state['corpus']).resolve():
            raise ValueError('native corpus differs from canonical history')
        if native['adapter'] == 'hierarchy_node_pairs':
            eligible = trial._eligible({'nodes': step['before']}, step['local'], step.get('mapped_parent'))
            if (prepared['canonical_states'] != {'current': step['before']}
                    or [pair['id'] for pair in prepared['pairs']] != [node['id'] for node in eligible]
                    or any(pair['local'] != step['local'] or pair['canonical'] != {
                        'state': 'current', 'id': pair['id']} for pair in prepared['pairs'])):
                raise ValueError('native graph inputs differ from canonical snapshot')
        elif native['adapter'] == 'hierarchy_local_nodes':
            if prepared['nodes'] != [{'id': 'bootstrap', 'local': step['local'], 'review': {}}]:
                raise ValueError('native local input differs from canonical history')
        else:
            raise ValueError('canonical measurement requires native hierarchy inputs')
        if [answer['id'] for answer in step['answers']] != [case['id'] for case in native['cases']]:
            raise ValueError('saved canonical answers differ from native cases')
        payloads = []
        for answer, case in zip(step['answers'], native['cases']):
            if (case['status'] in ('unrun', 'invalid_receipt') or not case.get('receipt')
                    or answer['status'] != case['status']
                    or answer.get('output') != case.get('parsed')
                    or answer.get('receipt') != case['receipt']
                    or case['evidence']['local'] != step['local']):
                raise ValueError('saved canonical answer differs from validated native receipt')
            bind(case['receipt']['results_path'])
            payloads.append(json.loads(case['inputs']['INPUT_JSON']))
        if not payloads or any(p['local'] != payloads[0]['local'] for p in payloads):
            raise ValueError('native cases do not share one local input')
        if native['adapter'] == 'hierarchy_node_pairs' and state.get('independent_meanings'):
            frozen = state['local_meanings'].get(str(step['index']))
            if (frozen != step.get('local_meaning_from')
                    or step['selected_meaning'] != payloads[0]['local'].get('meaning')
                    or frozen['meaning'] != step['selected_meaning']
                    or any(case['evidence'].get('local_meaning_from') != {
                        key: frozen[key] for key in ('experiment', 'case', 'receipt')}
                        for case in native['cases'])):
                raise ValueError('saved fixed meaning differs from native comparison input')
        elif step['selected_meaning'] != next((case.get('parsed') or {}).get('meaning')
                                             for case in native['cases'] if case['id'] == step['meaning_case']):
            raise ValueError('saved selected meaning differs from native answer')
        steps.append({**deepcopy(step), 'adapter': native['adapter'],
                      'local_input': payloads[0]['local'],
                      'prompt_bytes': {case['id']: len(case['prompt'].encode('utf-8'))
                                       for case in native['cases']},
                      'canonical_inputs': {case['id']: payload['canonical']
                          for case, payload in zip(native['cases'], payloads) if 'canonical' in payload}})
        previous = step['after']
    if previous != state['nodes']:
        raise ValueError('canonical graph snapshots differ from final saved graph')

    menu_nodes, menu = None, None
    if 'menu' in cfg:
        menu = workflow.resolve(cfg['menu'], source.parent)
        menu_path = menu / 'state.json'
        if menu_path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('canonical candidate reference state exceeds 64 MiB limit')
        shaped = workflow.read(menu_path)
        trial._check(shaped)
        original = {node['id']: node for node in state['nodes']}
        if (shaped['status'] != 'shaped_candidate' or 'shape' not in shaped
                or shaped['sources'].get(str(state_path)) != sources[str(state_path)]
                or shaped['corpus'] != state['corpus'] or shaped['roots'] != state['roots']
                or any(node['id'] not in original or any(node[field] != original[node['id']][field]
                       for field in ('subject', 'meaning', 'entries')) for node in shaped['nodes'])):
            raise ValueError('menu must preserve nodes from this exact raw canonical trial')
        trial._ancestors(shaped['nodes'])
        shape_source = workflow.read(shaped['shape']['source'])
        expected_parents = {identifier: [] for identifier in shape_source['roots']}
        for parent, children in shape_source['children'].items():
            expected_parents.setdefault(parent, [])
            for child in children:
                expected_parents.setdefault(child, []).append(parent)
        original_ancestors = trial._ancestors(state['nodes'])
        if (len(shaped['nodes']) != len(expected_parents)
                or {node['id']: node['parents'] for node in shaped['nodes']} != {
                    identifier: sorted(parents) for identifier, parents in expected_parents.items()}
                or any(parent not in original_ancestors[node['id']]
                       for node in shaped['nodes'] for parent in node['parents'])):
            raise ValueError('menu graph differs from its native shape source')
        sources.update(shaped['sources'])
        bind(menu_path)
        menu_nodes = shaped['nodes']
    result = {'schema_version': 1, 'source': str(source), 'trial': str(directory),
              'menu': str(menu) if menu is not None else None,
              'sources': sources, 'inference_calls': 0,
              **evaluate_snapshots(steps, cfg['candidate_limits'], menu_nodes=menu_nodes)}
    for path, expected in sources.items():
        if trial._hash(path) != expected:
            raise ValueError('native measurement source changed: ' + path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result
