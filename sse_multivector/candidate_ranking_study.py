"""Offline candidate-ranking research on validated, fixed native snapshots.

No teacher requests or graph writes. The reference project owns its frozen
reader/guards; this module owns only experimental ranking and measurement.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys

import numpy as np


def unit_rows(rows):
    rows = np.asarray(rows, dtype=np.float64)
    norms = np.linalg.norm(rows, axis=-1, keepdims=True)
    if not np.isfinite(rows).all() or np.any(norms == 0):
        raise ValueError('finite nonzero vectors required')
    return rows / norms


def score_order(ids, scores):
    return sorted(ids, key=lambda k: (-float(scores[ids.index(k)]), k))


def descendant_scores(scores, descendants):
    return np.array([max(scores[i] for i in group) for group in descendants])


def late_interaction(query, candidates):
    """Mean best-match across heading/meaning views, not ColBERT token vectors."""
    return np.einsum('qd,nvd->nqv', query, candidates).max(axis=2).mean(axis=1)


def density_corrected(scores, vectors, *, neighbors=10):
    """One-space CSLS-inspired correction; never a containment judgment."""
    if len(vectors) < 2:
        return 2 * np.asarray(scores)
    similarities = vectors @ vectors.T
    np.fill_diagonal(similarities, -np.inf)
    count = min(neighbors, len(vectors)-1)
    density = np.sort(similarities, axis=1)[:, -count:].mean(axis=1)
    return 2 * np.asarray(scores) - density


def history_step(step, retained):
    """Keep original receipts, removing answers this replay never requested."""
    result = deepcopy(step)
    result['answers'] = [a for a in result['answers'] if a['id'] in retained]
    return result


def verify_vector_binding(directory, receipt):
    directory = Path(directory)
    for field, filename in (('proposal_sha256', 'inputs.json'), ('request_sha256', 'worker-request.json')):
        if receipt[field] != hashlib.sha256((directory / filename).read_bytes()).hexdigest():
            raise ValueError('auxiliary vector binding differs: ' + field)


def select_candidates(rows, order, *, limit, mapped_parent=None, heading_groups=False):
    by_id = {r['id']: r for r in rows}
    if mapped_parent is not None:
        order = [mapped_parent] + [k for k in order if k != mapped_parent]
    if not heading_groups:
        return order[:limit]
    headings = list(dict.fromkeys(by_id[k]['subject'] for k in order))[:limit]
    return [k for heading in headings for k in order if by_id[k]['subject'] == heading]


def note_split(notes):
    ordered = sorted(set(notes), key=lambda n: (hashlib.sha256(n.encode()).hexdigest(), n))
    count = max(1, len(ordered) // 5)
    return dict(development=ordered[:-count], test=ordered[-count:])


def fit_logistic(x, y, *, penalty=10.):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-9] = 1
    a = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    beta = np.zeros(a.shape[1])
    ridge = np.eye(a.shape[1]) * penalty
    ridge[0, 0] = 0
    if y.min() == y.max():
        return dict(mean=mean, scale=scale, beta=beta, constant=float(y[0]))
    for _ in range(40):
        prob = 1 / (1 + np.exp(-np.clip(a @ beta, -30, 30)))
        curvature = np.maximum(prob * (1-prob), 1e-7)
        gradient = a.T @ (prob-y) + ridge @ beta
        hessian = a.T @ (a * curvature[:, None]) + ridge
        delta = np.linalg.solve(hessian, gradient)
        beta -= delta
        if np.max(np.abs(delta)) < 1e-7:
            break
    return dict(mean=mean, scale=scale, beta=beta, constant=None)


def predict_logistic(model, x):
    if model['constant'] is not None:
        return np.full(len(x), model['constant'])
    x = (np.asarray(x) - model['mean']) / model['scale']
    return 1 / (1 + np.exp(-np.clip(model['beta'][0] + x @ model['beta'][1:], -30, 30)))


def _reference(root):
    """Use the source project's production readers without copying dependencies."""
    root = Path(root).resolve()
    existing = sys.modules.get('sse_multivector')
    if existing is not None and str(root / 'sse_multivector') not in existing.__path__:
        raise ValueError('invoke this study as a script with its frozen reference project')
    sys.path.insert(0, str(root))
    return tuple(importlib.import_module('sse_multivector.' + name) for name in (
        'experiment', 'canonical_trial', 'canonical_comparison_policy',
        'canonical_selection_ranking', 'subject_matching_probe', 'ancestor_cosine_probe'))


def read_frames(root, trial_path, vector_path, subject_probe):
    w, t, p, ranking, subject_vectors, vector_reader = _reference(root)
    state_path = Path(trial_path).resolve() / 'state.json'
    state = w.read(state_path)
    t._check(state)
    vp = w.read(Path(vector_path) / 'inputs.json')
    for path, expected in vp['protected_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('auxiliary vector source changed: ' + path)
    values, receipt = vector_reader.load_vectors(Path(vector_path) / 'worker-result')
    verify_vector_binding(vector_path, receipt)
    headers, original_receipt, protected = subject_vectors.load_subject_vectors(Path(subject_probe))
    for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model', 'dimensions'):
        if receipt[key] != original_receipt[key]:
            raise ValueError('SSE identity differs: ' + key)
    controls = []
    for text, key in vp['controls'].items():
        digest = hashlib.sha256(text.encode()).hexdigest()
        old, new = headers[(digest, digest[:16])], values[tuple(key)]
        normalized_error = float(np.max(np.abs(unit_rows(old) - unit_rows(new))))
        similarity = vector_reader.cosine(old, new)
        if similarity < .999999 or normalized_error > 1e-5:
            raise ValueError('original heading replay differs: ' + text)
        controls.append(dict(subject=text, cosine=similarity, max_normalized_error=normalized_error))
    pair_by_id = {pair['id']: pair for pair in vp['pairs']}

    def header(text):
        digest = hashlib.sha256(text.encode()).hexdigest()
        return unit_rows(headers[(digest, digest[:16])])

    def representation(key, name):
        pair = pair_by_id[vp['references'][key]]
        return unit_rows(values[tuple(pair['representations'][name])])

    corpus = {n['note_id']: n for n in w.read(state['corpus'])['notes']}
    stages, frames = {}, []
    projection = np.random.default_rng(7021).normal(size=(receipt['dimensions'], 16))
    projection /= np.linalg.norm(projection, axis=0)
    for step in state['steps']:
        record = state.get('comparison_policy_steps', {}).get(str(step['index']))
        if record is None:
            continue
        stage_path = str(Path(step['comparison_phases'][0]['experiment']).parent.parent / 'state.json')
        if stage_path not in stages:
            stages[stage_path] = w.read(stage_path)
        snapshot = dict(stages[stage_path], index=step['index'], nodes=step['before'],
                        steps=state['steps'][:step['index']], experiment=step['experiment'], phase='comparison')
        cases = p.checked_cases(snapshot)
        if any(c['status'] != 'valid' for c in cases):
            raise ValueError('ranking study requires complete native comparison receipts')
        if [(c['id'], c['parsed']) for c in cases] != [(a['id'], a['output']) for a in step['answers']]:
            raise ValueError('step answers differ from checked native receipts')
        nodes = step['before']
        ids = [n['id'] for n in nodes]
        local = step['local']
        entry = next(e for e in corpus[local['note_id']]['subjects'] if e['number'] == local['number'])
        qh = header(entry['subject'])
        qm, qc, qcm = (representation('step:' + str(step['index']), name) for name in (
            'meaning', 'contextual_heading', 'contextual_meaning'))
        head = np.array([header(n['subject']) for n in nodes])
        means = np.array([representation('node:' + n['id'], 'meaning') for n in nodes])
        context = np.array([representation('node:' + n['id'], 'contextual_heading') for n in nodes])
        context_means = np.array([representation('node:' + n['id'], 'contextual_meaning') for n in nodes])
        ancestors = t._ancestors(nodes)
        descendants = [[i for i, n in enumerate(nodes) if n['id'] == k or k in ancestors[n['id']]] for k in ids]
        ancestor_headings = record['plan']['provenance']['query_headings']
        heading_scores = head @ qh
        scores = dict(heading=heading_scores, meaning=means @ qm, contextual_heading=context @ qc,
                      contextual_meaning=context_means @ qcm,
                      heading_ancestors=np.max(head @ np.array([header(x) for x in ancestor_headings]).T, axis=1))
        scores['late_interaction'] = late_interaction(np.array([qh, qc, qcm]),
            np.stack([head, context, context_means], axis=1))
        scores['density_contextual'] = density_corrected(scores['contextual_heading'], context)
        for k, saved in record['plan']['provenance']['sse_scores'].items():
            if abs(scores['heading_ancestors'][ids.index(k)] - saved) > 1e-6:
                raise ValueError('original SSE nomination cannot be reproduced')
        eligible = record['plan']['binding']['eligible']
        text_scores = record['plan']['provenance']['text_scores']
        scores['text'] = np.array([text_scores.get(k, 0) for k in ids])
        scores['meaning_descendants'] = descendant_scores(scores['meaning'], descendants)
        scores['heading_descendants'] = descendant_scores(scores['heading'], descendants)
        scores['contextual_descendants'] = descendant_scores(scores['contextual_heading'], descendants)
        def first_definition(text):
            return text.split('including but not limited to')[0].split('including, but not limited to')[0]
        _, defscores = ranking.rank_text(entry['subject'], first_definition(step['selected_meaning']),
            [dict(id=n['id'], subject=n['subject'], meaning=first_definition(n['meaning']))
             for n in nodes if n['id'] in eligible])
        scores['definition_text'] = np.array([defscores.get(k, 0) for k in ids])
        scalars = [scores[k] for k in ('heading', 'heading_ancestors', 'meaning', 'contextual_heading',
            'contextual_meaning', 'text', 'definition_text', 'meaning_descendants', 'heading_descendants')]
        scalars += [np.log1p([len(ancestors[k]) for k in ids]),
                    np.log1p([len(v) for v in descendants]),
                    np.log1p([len(n['entries']) for n in nodes]),
                    np.array([n['subject'].casefold() == entry['subject'].casefold() for n in nodes], float)]
        qsmall, csmall = qcm @ projection, context_means @ projection
        interactions = np.column_stack([np.tile(qsmall, (len(ids), 1)), csmall,
                                       csmall-qsmall, csmall*qsmall])
        features = np.column_stack([*scalars, interactions])
        known = {c['id']: c for c in cases}
        frames.append(dict(step=step, snapshot=snapshot, ids=ids, rows=nodes, local_subject=entry['subject'],
            eligible=eligible, pool=record['plan']['queried'], record=record, scores=scores,
            features=features, known=known, note_id=local['note_id']))
    return state, frames, dict(controls=controls, auxiliary_rows=receipt['row_count'],
        study_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_code_sha256={m.__file__: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
                               for m in (w, t, p, ranking, subject_vectors, vector_reader)},
        auxiliary_worker_receipt=str(Path(vector_path) / 'worker-result/worker-receipt.json'),
        source_state=str(state_path), state_sha256=hashlib.sha256(state_path.read_bytes()).hexdigest(),
        checkpoint_sha256=receipt['checkpoint_sha256'], new_teacher_calls=0), (w, t, p)


def orders(frame, learned=None):
    ids, scores = frame['ids'], frame['scores']
    pool = set(frame['pool'])
    def order(score):
        return [k for k in score_order(ids, score) if k in pool]
    result = dict(baseline=frame['pool'])
    for key in ('heading', 'meaning', 'contextual_heading', 'contextual_meaning', 'meaning_descendants',
                'heading_descendants', 'contextual_descendants', 'definition_text',
                'late_interaction', 'density_contextual'):
        result[key] = order(scores[key])
    result['meaning_hybrid'] = order(.5*scores['heading'] + .5*scores['meaning'])
    result['contextual_hybrid'] = order(.5*scores['contextual_heading'] + .5*scores['contextual_meaning'])
    result['graph_hybrid'] = order(.5*scores['meaning'] + .25*scores['contextual_heading']
                                 + .25*scores['meaning_descendants'])
    result['heading_groups'] = frame['pool']
    if learned is not None:
        result['learned'] = order(learned)
    return result


def evaluate(frame, order, limit, modules, *, heading_groups=False, history=None):
    w, t, p = modules
    step = frame['step']
    queried = select_candidates(frame['rows'], order, limit=limit,
        mapped_parent=step.get('mapped_parent'), heading_groups=heading_groups)
    answers = {k: c['parsed'] for k, c in frame['known'].items()}
    values = {k: answers[k] for k in queried}
    reason = None
    if step.get('mapped_parent') and values[step['mapped_parent']]['relation'] not in ('canonical_contains_local', 'equivalent'):
        reason = 'mapped_parent'
    if any(v['meaning'] is None or v['relation'] == 'uncertain' for v in values.values()):
        reason = reason or 'uncertain'
    if sum(v['relation'] == 'equivalent' for v in values.values()) > 1:
        reason = reason or 'multiple_equivalents'
    snapshot = frame['snapshot'] if history is None else dict(frame['snapshot'], steps=history)
    nodes, target, required, unknown = step['before'], None, {}, []
    if not reason:
        nodes, target, reason, _ = t._placement(snapshot, step['local'], step['selected_meaning'], values)
        if not reason:
            record = deepcopy(frame['record'])
            record['plan']['omitted'] = [k for k in frame['eligible'] if k not in queried]
            required = p._implied(record, nodes, target)
            unknown = [k for k in required if k not in answers]
            if any(answers[k]['relation'] != expected for k, expected in required.items() if k in answers):
                reason = 'verification_contradiction'
            if not unknown and not reason:
                values.update({k: answers[k] for k in required})
                nodes, target, reason, _ = t._placement(snapshot, step['local'], step['selected_meaning'], values)
    if reason:
        nodes, target = step['before'], None
    retained = set(queried) | set(required)
    positives = {k for k, v in answers.items() if v['relation'] in (
        'canonical_contains_local', 'local_contains_canonical', 'equivalent')}
    return dict(index=step['index'], local_subject=frame['local_subject'], queried=queried,
        verification=required, unresolved=unknown, reason=reason, same_graph=not unknown and nodes == step['after'],
        hidden_hold=step['status'] == 'held' and not reason and not unknown,
        saved_positives=len(positives), recovered_positives=len(positives & retained),
        original_cases=len(answers), retained_cases=len(retained),
        historical_status=step['status'], discarded_positive=sorted(positives-retained))


def exact_prefix(state, frames, profile, modules):
    """Stop before reusing any saved pair whose construction graph has changed."""
    by_index = {f['step']['index']: f for f in frames}
    selections = {r['index']: r for r in profile['steps']}
    history, rows = [], []
    for step in state['steps']:
        if step['index'] not in by_index:
            history.append(deepcopy(step))
            continue
        previous = selections[step['index']]
        row = evaluate(by_index[step['index']], previous['queried'], len(previous['queried']),
                       modules, history=history)
        rows.append(row)
        if not row['same_graph']:
            break
        history.append(history_step(step, set(row['queried']) | set(row['verification'])))
    complete = len(history) == len(state['steps'])
    return dict(complete=complete, matched_local_entries=len(history), steps=rows,
                first_divergence=None if complete else rows[-1], new_teacher_calls=0)


def comparison_costs(frames, selected, workflow):
    """Use the native accounting function over receipt-validated original calls."""
    ledgers, calls, seen = {}, [], set()
    for frame in frames:
        keys = selected[frame['step']['index']]
        for key in keys:
            case = frame['known'].get(key)
            if case is None:
                raise ValueError('cannot price an unobserved verification request')
            receipt = case['receipt']
            path = Path(receipt['results_path']).resolve()
            if path not in ledgers:
                lines = path.read_bytes().splitlines(keepends=True)
                records = [json.loads(line) for line in lines]
                hashes = [hashlib.sha256(line).hexdigest() for line in lines]
                ledgers[path] = (records, hashes)
            records, hashes = ledgers[path]
            if hashes.count(receipt['record_sha256']) != 1:
                raise ValueError('receipt does not identify one exact native record')
            end = hashes.index(receipt['record_sha256'])
            job = records[end]['job_key']
            for number, record in enumerate(records[:end+1]):
                if record['job_key'] != job or (path, number) in seen:
                    continue
                seen.add((path, number))
                calls.append((record, workflow.engine.provider_cost(record)))
    return dict(actual_source_attempts=len(calls), **workflow.usage_summary(calls, strict=True))


def note_predictions(frames, development, columns=None):
    """Train on development notes; their predictions exclude their own fold."""
    columns = list(range(frames[0]['features'].shape[1])) if columns is None else list(columns)
    def train(notes):
        x, y = [], []
        for frame in frames:
            if frame['note_id'] not in notes:
                continue
            for key in frame['pool']:
                relation = frame['known'][key]['parsed']['relation']
                if relation == 'uncertain':
                    continue
                x.append(frame['features'][frame['ids'].index(key), columns])
                y.append(relation != 'neither')
        return fit_logistic(np.array(x), np.array(y, float))
    model = train(development)
    predictions = {f['step']['index']: predict_logistic(model, f['features'][:, columns]) for f in frames}
    ordered = sorted(development)
    for i in range(4):
        fold = set(ordered[i::4])
        fitted = train(development-fold)
        for frame in frames:
            if frame['note_id'] in fold:
                predictions[frame['step']['index']] = predict_logistic(fitted, frame['features'][:, columns])
    return model, predictions


def observed_training(frame, retained, columns):
    """Only answers actually requested at this earlier construction step."""
    x, y = [], []
    for key in sorted(retained):
        relation = frame['known'][key]['parsed']['relation']
        if relation != 'uncertain':
            x.append(frame['features'][frame['ids'].index(key), columns])
            y.append(relation != 'neither')
    return x, y


def online_replay(state, frames, modules, *, semantic_only=False):
    """Refit on past observed answers; never continue after graph divergence."""
    columns = [i for i in range(frames[0]['features'].shape[1])
               if not semantic_only or i not in (7, 8, 9, 10, 11)]
    by_index = {f['step']['index']: f for f in frames}
    history, details, x, y = [], [], [], []
    for step in state['steps']:
        if step['index'] not in by_index:
            history.append(deepcopy(step))
            continue
        frame = by_index[step['index']]
        if step['index'] < 50:
            selected = frame['pool']
        else:
            model = fit_logistic(np.array(x), np.array(y, float))
            scores = predict_logistic(model, frame['features'][:, columns])
            learned = orders(frame, scores)['learned']
            selected = list(dict.fromkeys(frame['pool'][:12] + learned[:8]))
        row = evaluate(frame, selected, len(selected), modules, history=history)
        details.append(row)
        if not row['same_graph']:
            break
        retained = set(row['queried']) | set(row['verification'])
        a, b = observed_training(frame, retained, columns)
        x.extend(a)
        y.extend(b)
        history.append(history_step(step, retained))
    return dict(steps=details, online=True, warmup_local_entries=50,
        matched_local_entries=len(history), complete=len(history)==len(state['steps']),
        observed_training_pairs=len(y), feature_columns=columns,
        first_divergence=None if len(history)==len(state['steps']) else details[-1])


def analyze_study(args):
    state, frames, provenance, modules = read_frames(args.reference_project, args.trial,
                                                   args.vectors, args.subject_probe)
    report = json.loads(args.analyze.read_bytes())
    if report['provenance']['state_sha256'] != provenance['state_sha256']:
        raise ValueError('screen uses a different original hierarchy')
    audit = json.loads(args.cost_audit.read_bytes()) if args.cost_audit else None
    if audit is not None and audit['state_sha256'] != provenance['state_sha256']:
        raise ValueError('cost audit uses a different original hierarchy')
    if args.online:
        for name, semantic_only in (('online-full-dual-12-8', False), ('online-semantic-dual-12-8', True)):
            report['profiles'][name] = online_replay(state, frames, modules, semantic_only=semantic_only)
    if args.ablations:
        dimensions = frames[0]['features'].shape[1]
        for name, columns in (
                ('scalar-12', range(13)),
                ('no-graph-12', [0, 1, 2, 3, 4, 5, 6, 12, *range(13, dimensions)]),
                ('no-meaning-vectors-12', [0, 1, 5, 6, 8, 9, 10, 11, 12]),
                ('similarities-only-12', range(7))):
            _, predictions = note_predictions(frames, set(report['split']['development']), columns)
            details = [evaluate(f, orders(f, predictions[f['step']['index']])['learned'], 12, modules)
                       for f in frames]
            report['profiles'][name] = dict(steps=details, feature_columns=list(columns),
                totals=dict(all=dict(steps=len(details), same_graph=sum(r['same_graph'] for r in details),
                    hidden_holds=sum(r['hidden_hold'] for r in details),
                    retained_cases=sum(r['retained_cases'] for r in details))))
    # A second screen fits only already-observed first-50-entry labels, then
    # freezes one model for later entries. Its first 50 steps keep guarded16.
    if args.extensions:
        x, y = [], []
        for frame in frames:
            if frame['step']['index'] >= 50:
                continue
            for key in frame['pool']:
                relation = frame['known'][key]['parsed']['relation']
                if relation != 'uncertain':
                    x.append(frame['features'][frame['ids'].index(key)])
                    y.append(relation != 'neither')
        prefix_model = fit_logistic(np.array(x), np.array(y, float))
        report['prefix_fitted_model'] = {k: v.tolist() if isinstance(v, np.ndarray) else v
                                        for k, v in prefix_model.items()}
        graph_columns = {7, 8, 9, 10, 11}
        semantic_columns = [i for i in range(len(x[0])) if i not in graph_columns]
        prefix_semantic_model = fit_logistic(np.array(x)[:, semantic_columns], np.array(y, float))
        for name, baseline_count, learned_count in (
                ('dual-12-8', 12, 8), ('dual-12-12', 12, 12),
                ('prefix-learned-12', 0, 12), ('prefix-dual-12-8', 12, 8),
                ('graph-dual-12-4', 12, 0), ('graph-dual-12-8', 12, 0),
                ('context-dual-12-4', 12, 0), ('prefix-triple-12-8-4', 12, 8),
                ('prefix-semantic-12', 0, 12), ('prefix-semantic-dual-12-8', 12, 8)):
            details = []
            for frame in frames:
                if name.startswith('prefix-'):
                    scores = (predict_logistic(prefix_semantic_model, frame['features'][:, semantic_columns])
                              if name.startswith('prefix-semantic-') else
                              predict_logistic(prefix_model, frame['features']))
                    learned = orders(frame, scores)['learned']
                else:
                    scores = np.array(report['learned_predictions'][str(frame['step']['index'])])
                    learned = orders(frame, scores)['learned']
                selected = list(dict.fromkeys(frame['pool'][:baseline_count] + learned[:learned_count]))
                if name.startswith('graph-') or name.startswith('prefix-triple-'):
                    graph_count = 8 if name == 'graph-dual-12-8' else 4
                    selected = list(dict.fromkeys(selected + orders(frame)['contextual_descendants'][:graph_count]))
                elif name.startswith('context-'):
                    selected = list(dict.fromkeys(selected + orders(frame)['contextual_heading'][:4]))
                if name.startswith('prefix-') and frame['step']['index'] < 50:
                    selected = frame['pool']
                details.append(evaluate(frame, selected, len(selected), modules))
            report['profiles'][name] = dict(steps=details,
                totals=dict(all=dict(steps=len(details), same_graph=sum(r['same_graph'] for r in details),
                    hidden_holds=sum(r['hidden_hold'] for r in details),
                    retained_cases=sum(r['retained_cases'] for r in details))))
    baseline = comparison_costs(frames, {f['step']['index']: set(f['known']) for f in frames}, modules[0])
    if audit is not None:
        expected = sum(audit['cost_by_kind'][key]['known_catalog_cost_estimate_usd']
                       for key in ('comparison', 'verification'))
        if abs(expected - baseline['known_catalog_cost_estimate_usd']) > 1e-8:
            raise ValueError('native comparison subtotal differs from the original cost audit')
    outputs = {}
    for name in args.profile or [report['selected_on_development']]:
        profile = report['profiles'][name]
        replay = profile if profile.get('online') else exact_prefix(state, frames, profile, modules)
        selected = {r['index']: set(r['queried']) | set(r['verification']) for r in profile['steps']}
        priced_frames = [f for f in frames if f['step']['index'] in selected]
        projected = (None if any(r['unresolved'] for r in profile['steps']) else
                     comparison_costs(priced_frames, selected, modules[0]))
        value = dict(exact_prefix=replay, frozen_snapshot_cost=projected)
        if projected is not None and (not profile.get('online') or profile['complete']):
            value['known_comparison_cost_reduction_percent'] = 100 * (1 -
                projected['known_catalog_cost_estimate_usd'] / baseline['known_catalog_cost_estimate_usd'])
            if audit is not None:
                overhead = sum(v['known_catalog_cost_estimate_usd'] for key, v in audit['cost_by_kind'].items()
                               if key not in ('comparison', 'verification'))
                total = overhead + baseline['known_catalog_cost_estimate_usd']
                candidate = overhead + projected['known_catalog_cost_estimate_usd']
                value['known_all_in_projection'] = dict(baseline_usd=total, candidate_usd=candidate,
                    reduction_percent=100*(1-candidate/total), retained_original_overhead_usd=overhead,
                    original_attempts_without_usage=sum(v['attempts_without_usage'] for v in audit['cost_by_kind'].values()),
                    complete_total_usd=None,
                    interpretation='Conditional saved-token projection; original meaning and warmup overhead retained. Not a fresh build or a measured policy saving.')
        outputs[name] = value
        print(name, 'complete', replay['complete'], 'matched', replay['matched_local_entries'],
              'all_in', value.get('known_all_in_projection'), flush=True)
    # Rank every originally eligible node for selected witnesses. Unknown
    # outcomes remain unknown, even when the new scorer moves them upward.
    model_scores = report.get('learned_predictions', {})
    witnesses = []
    for frame in frames:
        if frame['step']['index'] not in (25, 65, 75, 81, 137, 159):
            continue
        learned = np.asarray(model_scores[str(frame['step']['index'])]) if model_scores else None
        original_scores = frame['record']['plan']['provenance']['scores']
        full_order = sorted(frame['eligible'], key=lambda k: (-original_scores[k], k))
        full_order = select_candidates(frame['rows'], full_order, limit=len(full_order),
                                       mapped_parent=frame['step'].get('mapped_parent'))
        if full_order[:len(frame['pool'])] != frame['pool']:
            raise ValueError('full original nomination order does not reproduce its shortlist')
        all_orders = orders(dict(frame, pool=full_order), learned)
        witnesses.append(dict(index=frame['step']['index'], local_subject=frame['local_subject'],
            candidates=[dict(id=n['id'], subject=n['subject'], meaning=n['meaning'],
                saved_relation=(frame['known'][n['id']]['parsed']['relation'] if n['id'] in frame['known'] else None),
                ranks={k: v.index(n['id'])+1 for k, v in all_orders.items() if n['id'] in v})
                for n in frame['rows'] if n['id'] in frame['eligible']]))
    result = dict(schema_version=1, provenance=provenance, screen=str(args.analyze.resolve()),
        screen_sha256=hashlib.sha256(args.analyze.read_bytes()).hexdigest(),
        cost_audit=None if args.cost_audit is None else dict(path=str(args.cost_audit.resolve()),
            sha256=hashlib.sha256(args.cost_audit.read_bytes()).hexdigest()),
        baseline_comparison_cost=baseline, profiles=outputs, witnesses=witnesses,
        extended_profiles={k: v for k, v in report['profiles'].items() if k not in json.loads(args.analyze.read_bytes())['profiles']},
        prefix_fitted_model=report.get('prefix_fitted_model'),
        limitations=report['limitations'] + ['Exact replay filters previous settled answers and stops at the first graph difference.',
            'Historical ASv6.48 subjects are deprecated; current ASv6.100 data requires separate validation.',
            'New SSE compute is local CPU work; projected API-equivalent costs do not include future retrieval infrastructure.'])
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


def run_study(args):
    state, frames, provenance, modules = read_frames(args.reference_project, args.trial,
                                                   args.vectors, args.subject_probe)
    split = note_split([step['local']['note_id'] for step in state['steps']])
    development, test = set(split['development']), set(split['test'])
    model, predicted = note_predictions(frames, development)
    methods = list(orders(frames[-1], predicted[frames[-1]['step']['index']]))
    outputs = {}
    for name in methods:
        for limit in (8, 12, 16):
            profile = f'{name}-{limit}'
            details = []
            for frame in frames:
                order = orders(frame, predicted[frame['step']['index']])[name]
                details.append(evaluate(frame, order, limit, modules, heading_groups=name == 'heading_groups'))
            totals = {}
            for group, notes in (('development', development), ('test', test), ('all', development|test)):
                rows = [r for r, f in zip(details, frames) if f['note_id'] in notes]
                totals[group] = dict(steps=len(rows), same_graph=sum(r['same_graph'] for r in rows),
                    different_graph=sum(not r['same_graph'] and not r['unresolved'] for r in rows),
                    unresolved_steps=sum(bool(r['unresolved']) for r in rows),
                    hidden_holds=sum(r['hidden_hold'] for r in rows),
                    initial_cases=sum(len(r['queried']) for r in rows),
                    verification_cases=sum(len(r['verification']) for r in rows),
                    original_cases=sum(r['original_cases'] for r in rows),
                    retained_cases=sum(r['retained_cases'] for r in rows),
                    saved_positives=sum(r['saved_positives'] for r in rows),
                    recovered_positives=sum(r['recovered_positives'] for r in rows))
            outputs[profile] = dict(totals=totals, steps=details)
            print(profile, json.dumps(totals['all']), flush=True)
    winner = min(outputs, key=lambda key: (
        outputs[key]['totals']['development']['different_graph'] + outputs[key]['totals']['development']['unresolved_steps'],
        outputs[key]['totals']['development']['hidden_holds'],
        outputs[key]['totals']['development']['retained_cases'], key))
    provenance['study_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = dict(schema_version=1, provenance=provenance, split=split, profiles=outputs,
                  fitted_model={k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in model.items()},
                  learned_predictions={str(k): v.tolist() for k, v in predicted.items()},
                  selected_on_development=winner,
                  limitations=['Frozen original before-graphs; not new full hierarchies.',
                    'All rerankers use the original sixteen-candidate nomination pool, so unseen relationships remain unknown.',
                    'Historical teacher labels are not human semantic gold.',
                    'Later guarded snapshots use original prior query history, not reachable counterfactual histories.',
                    'Test notes are held out of model fitting and profile selection; this single exploratory corpus is not independent deployment proof.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print('SELECTED_ON_DEVELOPMENT', winner)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-project', type=Path, required=True)
    p.add_argument('--trial', type=Path, required=True)
    p.add_argument('--vectors', type=Path, required=True)
    p.add_argument('--subject-probe', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--analyze', type=Path)
    p.add_argument('--cost-audit', type=Path)
    p.add_argument('--profile', action='append')
    p.add_argument('--extensions', action='store_true', help='Also screen dual-ranking and chronologically trained profiles offline.')
    p.add_argument('--ablations', action='store_true', help='Retrain without feature groups using the same note split.')
    p.add_argument('--online', action='store_true', help='Replay models trained only on previously retained judgments.')
    args = p.parse_args()
    (analyze_study if args.analyze else run_study)(args)


if __name__ == '__main__':
    main()
