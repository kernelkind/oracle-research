"""Compare completed policy trials using native receipts and browsing audits.

This reports mechanical task preservation, not semantic gold. Unknown failed
usage stays unknown; reused generation and new execution are separate measures.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

from . import canonical_trial as trial
from . import experiment as workflow
from .canonical_continuation import _failure_receipts
from .canonical_hierarchy_audit import audit_trial
from .canonical_hierarchy_shape import shape_trial


def _tokenizer():
    try:
        import tiktoken
        return tiktoken.get_encoding('o200k_base')
    except ImportError:
        return None


def _references(step):
    paths = [step.get('experiment')]
    paths.extend(step.get('comparison_experiments', []))
    paths.extend(p['experiment'] for p in step.get('comparison_phases', []))
    frozen = step.get('local_meaning_from')
    if frozen:
        paths.append(frozen['experiment'])
    return list(dict.fromkeys(str(Path(p).resolve()) for p in paths if p))


def _usage(sources, records):
    native = workflow.usage_summary(((records[key], None) for key in sources), strict=True)
    native['total_input_tokens'] = sum(native[k] for k in
        ('input_tokens', 'cached_input_tokens', 'cache_write_tokens'))
    native['total_tokens'] = native['total_input_tokens'] + native['output_tokens']
    native['usage_complete'] = native['attempts_without_usage'] == 0
    native['original_calls'] = len(sources)
    native['reasoning_included_in_output'] = True
    return native


def _ratio(baseline, candidate, complete):
    return (100 * (baseline - candidate) / baseline
            if complete and baseline > 0 else None)


def _inference_definition(spec):
    runner = {key: value for key, value in spec['runner'].items() if key != 'concurrency'}
    prompt = {'id': spec['prompt']['id'], 'sha256': trial._hash(spec['prompt']['path'])}
    return dict(prompt=prompt, runner=runner)


def evaluate_source(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('canonical policy evaluation output already exists')
    cfg = workflow.read(source)
    independent = isinstance(cfg, dict) and cfg.get('schema_version') == 3
    required = {'schema_version', 'baseline', 'candidate', 'baseline_menu'}
    if not independent:
        required.add('base_trial')
    if (not isinstance(cfg, dict) or not required <= set(cfg)
            or not set(cfg) <= required | {'candidate_menu'}
            or type(cfg['schema_version']) is not int or cfg['schema_version'] not in (1, 2, 3)
            or any(not isinstance(cfg[k], str) or not cfg[k].strip()
                   for k in set(cfg) - {'schema_version'})):
        raise ValueError('invalid canonical policy evaluation source')
    paths = {k: workflow.resolve(v, source.parent) for k, v in cfg.items()
             if k != 'schema_version'}
    sources, records, loaded, ledger_lines = {}, {}, {}, {}

    def bind(path, expected=None):
        path = Path(path).resolve()
        actual = trial._hash(path)
        if expected is not None and actual != expected:
            raise ValueError('canonical policy source changed: ' + str(path))
        if str(path) in sources and sources[str(path)] != actual:
            raise ValueError('canonical policy source changed: ' + str(path))
        sources[str(path)] = actual

    def state_at(directory):
        path = directory / 'state.json'
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('canonical policy state exceeds 64 MiB limit')
        state = workflow.read(path)
        trial._check(state)
        trial._ancestors(state['nodes'])
        if len(state['nodes']) > 512 or len(state.get('steps', [])) > 512:
            raise ValueError('canonical policy trial exceeds bounded evaluation limit')
        bind(path)
        for original, digest in state['sources'].items():
            bind(original, digest)
        return state

    bind(source)
    for path in (__file__, workflow.__file__, trial.__file__, audit_trial.__code__.co_filename,
                 shape_trial.__code__.co_filename, _failure_receipts.__code__.co_filename):
        bind(path)
    names = ('baseline', 'candidate') if independent else ('base_trial', 'baseline', 'candidate')
    states = {name: state_at(paths[name]) for name in names}
    baseline, candidate = (states[name] for name in ('baseline', 'candidate'))
    base = baseline if independent else states['base_trial']
    if (base['status'] != 'complete' or any('shape' in state for state in states.values())
            or any(state.get('independent_meanings') is not True for state in states.values())):
        raise ValueError('canonical policy evaluation requires raw trials and completed checkpoint')
    checkpoint = 0 if independent else base['index']
    baseline_queue, candidate_queue = (trial.execution_queue(s) for s in (baseline, candidate))
    base_queue = [] if independent else trial.execution_queue(base)
    selective = cfg['schema_version'] in (2, 3)
    if (any(type(s['index']) is not int or s['index'] != len(s['steps'])
            or not 0 <= s['index'] <= len(trial.execution_queue(s))
            or [st['index'] for st in s['steps']] != list(range(s['index']))
            for s in states.values())
            or checkpoint != len(base_queue) or not independent and len(base['steps']) != checkpoint
            or not selective and baseline_queue != candidate_queue
            or any(trial.execution_queue(s)[:checkpoint] != base_queue for s in (baseline, candidate))
            or any(s['steps'][:checkpoint] != base['steps'][:checkpoint] for s in (baseline, candidate))
            or any(s['corpus'] != base['corpus'] for s in (baseline, candidate))):
        raise ValueError('canonical policy trials must preserve checkpoint and scheduled suffix')
    if selective:
        selected_notes = {local['note_id'] for local in base['roots']}
        originals = {(note['note_id'], row['number'])
                     for note in workflow.read(base['corpus'])['notes']
                     for row in note['subjects']}
        for state in (baseline, candidate):
            queue = trial.execution_queue(state)
            identities = [(item['local']['note_id'], item['local']['number']) for item in queue]
            if (len(identities) != len(set(identities)) or set(identities) - originals
                    or {local['note_id'] for local in state['roots']} != selected_notes
                    or any(note_id not in selected_notes for note_id, _ in identities)):
                raise ValueError('selective schedules require unique original entries from the same selected notes')
            if any(_inference_definition(state[field]) != _inference_definition(base[field])
                   for field in ('bootstrap_spec', 'comparison_spec')):
                raise ValueError('selective trials must preserve prompt and inference settings')
    if baseline['status'] != 'complete' or baseline['index'] != len(baseline_queue):
        raise ValueError('canonical policy baseline must be completed')
    complete = candidate['status'] == 'complete' and candidate['index'] == len(candidate_queue)
    encoder = _tokenizer()

    def load_native(directory):
        directory = Path(directory).resolve()
        if directory in loaded:
            return loaded[directory]
        report = workflow.report(directory, generation_costs=True, include_request_preview=False)
        if report['imported'] or any(c['status'] == 'invalid_receipt' for c in report['cases']):
            raise ValueError('policy accounting requires valid native receipts')
        if _failure_receipts(directory, report['cases']) is None:
            raise ValueError('policy failed answer differs from validated native receipt')
        plan_path = directory / 'experiment.json'
        plan = workflow.read(plan_path)['plan']
        bind(plan_path)
        for path, digest in plan['sources'].items():
            bind(path, digest)
        report['_prepared'] = workflow.read(workflow.resolve(plan['dataset']['path'], directory))
        for original in report['generation_usage']['sources']:
            path = Path(original['results_path']).resolve()
            if path not in ledger_lines:
                bind(path)
                ledger_lines[path] = path.read_bytes().splitlines(keepends=True)
            lines = ledger_lines[path]
            line = lines[original['result_line'] - 1]
            if hashlib.sha256(line).hexdigest() != original['result_sha256']:
                raise ValueError('policy generation source changed')
            key = (str(path), original['result_line'])
            record = json.loads(line)
            if key in records and records[key] != record:
                raise ValueError('policy generation source changed')
            records[key] = record
        loaded[directory] = report
        return report

    def assess_arm(name, start=checkpoint):
        state = states[name]
        queue = trial.execution_queue(state)
        previous = [] if start == 0 else base['nodes']
        references, answer_rows = {}, []
        for step in state['steps'][start:]:
            index = step['index']
            if (step['before'] != previous or step['local'] != queue[index]['local']
                    or step.get('mapped_parent') != queue[index]['mapped_parent']):
                raise ValueError('policy graph snapshots or local schedule differ')
            trial._ancestors(step['before'])
            trial._ancestors(step['after'])
            frozen = step.get('local_meaning_from')
            if frozen and (step.get('selected_meaning') != frozen['meaning']
                    or state['local_meanings'].get(str(index)) != frozen):
                raise ValueError('saved policy fixed meaning differs')
            before_nodes = {n['id']: n for n in step['before']}
            if (step['status'] == 'held' and step['after'] != step['before']
                    or any(n['id'] in before_nodes and any(n[k] != before_nodes[n['id']][k]
                           for k in ('subject', 'meaning')) for n in step['after'])):
                raise ValueError('policy transition changed an immutable node or held graph')
            for directory in _references(step):
                references.setdefault(directory, step)
            answer_rows.extend((step, answer) for answer in step['answers'])
            previous = step['after']
        if previous != state['nodes']:
            raise ValueError('policy history differs from final graph')
        if not complete and name == 'candidate' and state['index'] < len(candidate_queue):
            pending = {'index': state['index'], 'local': candidate_queue[state['index']]['local'],
                       'mapped_parent': candidate_queue[state['index']]['mapped_parent'],
                       'before': state['nodes'], 'local_meaning_from': state.get('local_meanings', {}).get(str(state['index']))}
            for directory in _references({**pending, 'experiment': state.get('experiment')}):
                references.setdefault(directory, pending)
            selected = state.get('comparison_policy_steps', {}).get(str(state['index']), {})
            for phase in selected.get('comparison_phases', []):
                references.setdefault(phase['experiment'], pending)
        generation, actual = set(), set()
        kinds = {kind: {'cases': 0, 'unrun': 0, 'rendered_input_tokens': 0 if encoder else None,
                        'generation': set(), 'actual': set()} for kind in ('meanings', 'comparisons')}
        native_answers, experiments = {}, []
        for directory, step in references.items():
            report = load_native(directory)
            prepared = report['_prepared']
            adapter = report['adapter']
            if adapter not in ('hierarchy_local_nodes', 'hierarchy_node_pairs'):
                raise ValueError('policy accounting requires native hierarchy inputs')
            kind = 'meanings' if adapter == 'hierarchy_local_nodes' else 'comparisons'
            if selective:
                spec_path = Path(directory).parent / 'spec.json'
                bind(spec_path)
                expected = state['bootstrap_spec' if kind == 'meanings' else 'comparison_spec']
                # The shared checkpoint may predate the current prompts. Its
                # unchanged history and native provenance remain fully checked.
                if (step['index'] >= checkpoint
                        and _inference_definition(workflow.read(spec_path)) != _inference_definition(expected)):
                    raise ValueError('native selective prompt and inference settings differ')
            if Path(prepared['corpus']).resolve() != Path(state['corpus']).resolve():
                raise ValueError('native policy corpus differs')
            if adapter == 'hierarchy_node_pairs':
                if prepared['canonical_states'] != {'current': step['before']}:
                    raise ValueError('native policy graph differs from saved snapshot')
                eligible = {n['id'] for n in trial._eligible({'nodes': step['before']},
                            step['local'], step.get('mapped_parent'))}
                if set(c['id'] for c in report['cases']) - eligible:
                    raise ValueError('native policy comparison is not eligible')
            for case in report['cases']:
                if case['evidence']['local'] != step['local']:
                    raise ValueError('native policy local input differs')
                payload = json.loads(case['inputs']['INPUT_JSON'])
                frozen = step.get('local_meaning_from')
                if adapter == 'hierarchy_node_pairs' and frozen and (
                        payload['local'].get('meaning') != frozen['meaning']):
                    raise ValueError('native policy fixed meaning differs')
                if adapter == 'hierarchy_local_nodes' and frozen and (
                        case.get('receipt') != frozen['receipt']
                        or (case.get('parsed') or {}).get('meaning') != frozen['meaning']):
                    raise ValueError('native independent meaning differs from its receipt')
                kinds[kind]['cases'] += 1
                if sum(v['cases'] for v in kinds.values()) > 50000:
                    raise ValueError('canonical policy evaluation exceeds 50000 native cases')
                kinds[kind]['unrun'] += case['status'] == 'unrun'
                if encoder:
                    kinds[kind]['rendered_input_tokens'] += len(encoder.encode(case['prompt'], disallowed_special=()))
                if case.get('receipt'):
                    key = (case['id'], case['receipt']['results_path'], case['receipt']['record_sha256'])
                    native_answers[key] = case
            for receipt in report['generation_usage']['sources']:
                key = (receipt['results_path'], receipt['result_line'])
                generation.add(key)
                kinds[kind]['generation'].add(key)
                if not receipt['added_from_reuse']:
                    actual.add(key)
                    kinds[kind]['actual'].add(key)
            experiments.append({key: report[key] for key in ('experiment', 'prompt_id', 'settings', 'summary')})
        for step, answer in answer_rows:
            receipt = answer.get('receipt') or {}
            key = (answer['id'], receipt.get('results_path'), receipt.get('record_sha256'))
            case = native_answers.get(key)
            # Earlier reviewed checkpoints omitted status for successful answers.
            # The bound receipt must still validate successfully and match the
            # saved output; an absent status cannot admit a failed native case.
            if (case is None or answer.get('status', 'valid') != case['status']
                    or answer.get('output') != case.get('parsed')):
                raise ValueError('saved policy answer differs from validated native receipt')
        report = {'trial': str(paths[name]), 'status': state['status'],
                  'processed_entries': state['index'] - start, 'experiments': experiments,
                  'generation_usage': _usage(generation, records),
                  'actual_usage': _usage(actual, records), 'kinds': {}}
        for kind, values in kinds.items():
            report['kinds'][kind] = {k: v for k, v in values.items() if k not in ('generation', 'actual')}
            report['kinds'][kind]['generation_usage'] = _usage(values['generation'], records)
            report['kinds'][kind]['actual_usage'] = _usage(values['actual'], records)
        report['prepared_inputs'] = {'tokenizer': 'o200k_base' if encoder else None,
            'rendered_input_tokens': sum(v['rendered_input_tokens'] for v in kinds.values()) if encoder else None,
            'qualification': 'Rendered prompt tokens per prepared case; excludes response tokens, retries and transport framing.'}
        return report

    arms = {name: assess_arm(name) for name in ('baseline', 'candidate')}
    warnings = []
    if not encoder:
        warnings.append('tiktoken unavailable; rendered input token counts are unknown')
    if not complete:
        warnings.append('Candidate schedule incomplete; reduction percentages are not final')
    if any(not arm['generation_usage']['usage_complete'] for arm in arms.values()):
        warnings.append('Generation tokens are known subtotals; missing failed usage is not zero')
    if selective and any(arm['generation_usage']['catalog_cost_estimate_usd'] is None
                         for arm in arms.values()):
        warnings.append('Catalog cost percentage is unknown because original attempt costs are missing')

    def checked_menu(name, directory):
        shaped = state_at(directory)
        original = {n['id']: n for n in states[name]['nodes']}
        state_path = paths[name] / 'state.json'
        if ('shape' not in shaped or shaped['sources'].get(str(state_path)) != sources[str(state_path)]
                or shaped['roots'] != states[name]['roots'] or shaped['corpus'] != states[name]['corpus']
                or any(n['id'] not in original or any(n[k] != original[n['id']][k]
                       for k in ('subject', 'meaning', 'entries')) for n in shaped['nodes'])):
            raise ValueError('policy menu must preserve its exact native trial')
        ancestors = trial._ancestors(states[name]['nodes'])
        if any(p not in ancestors[n['id']] for n in shaped['nodes'] for p in n['parents']):
            raise ValueError('policy menu edge lacks native containment')
        shape = workflow.read(shaped['shape']['source'])
        expected = {n: [] for n in shape['roots']}
        for p, children in shape['children'].items():
            expected.setdefault(p, [])
            for c in children:
                expected.setdefault(c, []).append(p)
        if {n['id']: n['parents'] for n in shaped['nodes']} != {n: sorted(v) for n, v in expected.items()}:
            raise ValueError('policy menu differs from native shape definition')
        return shaped

    baseline_menu = checked_menu('baseline', paths['baseline_menu'])
    with tempfile.TemporaryDirectory(prefix='canonical-policy-evaluation-') as temporary:
        temporary = Path(temporary)
        audit_trial(paths['baseline_menu'], temporary / 'baseline-audit.json')
        baseline_audit = workflow.read(temporary / 'baseline-audit.json')
        if not baseline_audit['structural_constraints_met']:
            raise ValueError('policy baseline menu does not meet saved structural requirements')
        candidate_menu_path = paths.get('candidate_menu')
        shape_error = None
        if candidate_menu_path is None and complete:
            shape_cfg = deepcopy(workflow.read(baseline_menu['shape']['source']))
            shape_cfg['trial'] = str(paths['candidate'])
            workflow.write(temporary / 'shape.json', shape_cfg)
            try:
                shape_trial(temporary / 'shape.json', temporary / 'menu')
                candidate_menu_path = temporary / 'menu'
            except ValueError as error:
                shape_error = str(error)
        if candidate_menu_path is not None:
            if 'candidate_menu' in paths:
                checked_menu('candidate', candidate_menu_path)
            audit_trial(candidate_menu_path, temporary / 'candidate-audit.json')
            candidate_audit = workflow.read(temporary / 'candidate-audit.json')
        else:
            audit_trial(paths['candidate'], temporary / 'candidate-audit.json')
            candidate_audit = workflow.read(temporary / 'candidate-audit.json')
        individual, groups = [], []
        individuals = {r['note_id']: r for r in candidate_audit['individual_tasks']}
        for expected in baseline_audit['individual_tasks']:
            current = individuals.get(expected['note_id'])
            preserved = bool(current and current['status'] == 'within_choice_limit'
                and len(current['path']) <= len(expected['path']))
            individual.append({'note_id': expected['note_id'], 'preserved': preserved,
                               'baseline': expected, 'candidate': current})
        for expected in baseline_audit['topic_group_tasks']:
            alternatives = [r for r in candidate_audit['topic_group_tasks']
                            if r['subject'] == expected['subject'] and r['meaning'] == expected['meaning']]
            current = next((r for r in alternatives if r['note_ids'] == expected['note_ids']), None)
            preserved = bool(current and current['status'] == 'within_choice_limit'
                and len(current['path']) <= len(expected['path']))
            groups.append({'subject': expected['subject'], 'meaning': expected['meaning'],
                           'expected_notes': expected['note_ids'], 'preserved': preserved,
                           'baseline': expected, 'candidate': current, 'other_memberships': alternatives})
        quality = {'preserved': complete and shape_error is None
                   and candidate_audit['structural_constraints_met']
                   and all(r['preserved'] for r in individual + groups),
                   'shape_error': shape_error, 'individual_tasks': individual, 'topic_group_tasks': groups,
                   'baseline_metrics': baseline_audit['metrics'], 'candidate_metrics': candidate_audit['metrics'],
                   'candidate_violations': candidate_audit['violations'],
                   'semantic_graded': False,
                   'qualification': 'Measured structural and saved-menu task preservation only; '
                   'saved labels and manual holds are not semantic gold or global minimization proof.'}
    decision_changes = []
    keyed_steps = {name: {(step['local']['note_id'], step['local']['number']): step
                         for step in states[name]['steps'][checkpoint:]}
                   for name in ('baseline', 'candidate')}
    for identity in dict.fromkeys([*keyed_steps['baseline'], *keyed_steps['candidate']]):
        baseline_step, candidate_step = (keyed_steps[name].get(identity)
                                        for name in ('baseline', 'candidate'))
        values = [{k: step.get(k) for k in ('status', 'selected_meaning', 'reason')}
                  if step is not None else None for step in (baseline_step, candidate_step)]
        if values[0] != values[1]:
            step = baseline_step if baseline_step is not None else candidate_step
            decision_changes.append({'index': step['index'], 'local': step['local'],
                                     'baseline': values[0], 'candidate': values[1]})
    b, c = arms['baseline'], arms['candidate']
    reductions = {'comparison_requests_percent': _ratio(b['kinds']['comparisons']['cases'],
        c['kinds']['comparisons']['cases'], complete),
        'total_tokens_percent': _ratio(b['generation_usage']['total_tokens'],
            c['generation_usage']['total_tokens'], complete and all(a['generation_usage']['usage_complete'] for a in arms.values())),
        'comparison_tokens_percent': _ratio(b['kinds']['comparisons']['generation_usage']['total_tokens'],
            c['kinds']['comparisons']['generation_usage']['total_tokens'], complete and all(
                a['kinds']['comparisons']['generation_usage']['usage_complete'] for a in arms.values())),
        'rendered_input_tokens_percent': _ratio(b['prepared_inputs']['rendered_input_tokens'],
            c['prepared_inputs']['rendered_input_tokens'], complete and encoder is not None)}
    if selective:
        costs = [arm['generation_usage']['catalog_cost_estimate_usd'] for arm in arms.values()]
        reductions['catalog_cost_estimate_percent'] = (_ratio(costs[0], costs[1], complete)
                                                       if all(cost is not None for cost in costs) else None)
    result = {'schema_version': cfg['schema_version'], 'source': str(source), 'sources': sources, 'inference_calls': 0,
              'schedule': {'matched': baseline_queue == candidate_queue, 'checkpoint_index': checkpoint,
                  'scheduled_entries': len(baseline_queue) - checkpoint,
                  'candidate_complete': complete}, **arms, 'reductions': reductions,
              'quality': quality, 'decision_changes': decision_changes, 'warnings': warnings,
              'accounting': 'Generation usage deduplicates validated original calls, including reused '
              'sources and retries, within each arm. Actual usage measures only new local attempts. '
              'Input includes cached reads and cache writes; output already includes reasoning.'}
    if selective:
        result['schedule'].update(baseline_scheduled_entries=len(baseline_queue) - checkpoint,
                                  candidate_scheduled_entries=len(candidate_queue) - checkpoint)
        result['accounting'] += (' Costs and reductions cover the scheduled suffixes only; '
                                 'the shared checkpoint generation is excluded from both arms. '
                                 'Catalog cost percentages require complete saved original-call '
                                 'estimates, including cache reads, cache writes and output.')
        whole = {name: assess_arm(name, start=0) for name in ('baseline', 'candidate')}
        whole_costs = [arm['generation_usage']['catalog_cost_estimate_usd'] for arm in whole.values()]
        if any(cost is None for cost in whole_costs):
            warnings.append('Whole-construction catalog cost percentage is unknown; checkpoint '
                            'or suffix original-call estimates are missing')
        whole['reductions'] = {
            'catalog_cost_estimate_percent': (_ratio(whole_costs[0], whole_costs[1], complete)
                if all(cost is not None for cost in whole_costs) else None),
            'total_tokens_percent': _ratio(whole['baseline']['generation_usage']['total_tokens'],
                whole['candidate']['generation_usage']['total_tokens'], complete and all(
                    arm['generation_usage']['usage_complete'] for arm in whole.values()))}
        whole['accounting'] = ('Whole construction includes the shared checkpoint and each arm\'s '
                               'suffix, deduplicating validated original receipt lines within '
                               'each arm. Original generation includes exact saved-answer reuse; '
                               'actual usage counts original non-reused execution records. '
                               'Missing original-call cost estimates remain unknown.')
        if independent:
            whole['accounting'] = ('Whole construction starts from each independently empty graph, '
                'deduplicating validated original receipt lines within each arm. Original generation '
                'includes exact saved-answer reuse; actual usage counts non-reused execution records. '
                'Missing original-call cost estimates remain unknown.')
        result['whole_construction'] = whole
    for path, digest in sources.items():
        if trial._hash(path) != digest:
            raise ValueError('canonical policy source changed: ' + path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result
