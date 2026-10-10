"""Freeze and evaluate offline selection cases using native saved comparisons.

No inference, new embeddings, graph writes or semantic approvals. Run this file
as a script: the reference project owns the frozen production readers/guards.
"""
import argparse
from collections import Counter
from graphlib import TopologicalSorter, CycleError
import hashlib
import importlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def relationships(nodes, target, existing):
    """Read the local placement's reachable relationships to existing nodes."""
    parents = {n['id']: set(n['parents']) for n in nodes}
    if len(parents) != len(nodes) or any(p not in parents for ps in parents.values() for p in ps):
        raise ValueError('duplicate node or unknown parent')
    ancestors = {}
    try:
        for node in TopologicalSorter(parents).static_order():
            ancestors[node] = set(parents[node])
            for parent in parents[node]:
                ancestors[node].update(ancestors[parent])
    except CycleError as error:
        raise ValueError('canonical cycle') from error
    if target not in ancestors or set(existing) - ancestors.keys():
        raise ValueError('unknown placement or existing node')
    result = {}
    for identifier in existing:
        relation = ('equivalent' if identifier == target else
                    'canonical_contains_local' if identifier in ancestors[target] else
                    'local_contains_canonical' if target in ancestors[identifier] else None)
        if relation:
            result[identifier] = relation
    return result


def assess(expected, reason, unresolved, observed):
    """Historical preservation, allowing different edges with the same routes."""
    missing = {k: v for k, v in expected['relationships'].items() if observed.get(k) != v}
    if unresolved:
        outcome = 'unresolved'
    elif expected['status'] == 'held':
        outcome = 'matched' if reason else 'missed_hold'
    elif reason:
        outcome = 'unexpected_hold'
    else:
        outcome = 'missed_relationship' if missing else 'matched'
    return dict(outcome=outcome, missing=missing)


def expectation(frame):
    step = frame['step']
    required = ({} if step['status'] == 'held' else
                relationships(step['after'], step['canonical_id'], frame['ids']))
    return dict(index=step['index'], local=dict(step['local'], subject=frame['local_subject'],
                meaning=step['selected_meaning']), status=step['status'],
                original_reason=step.get('reason'), relationships=required,
                expectation_basis='historical_native_construction', human_reviewed=False)


def checked_selection(frame, selection, study):
    if (not isinstance(selection, list) or any(not isinstance(k, str) for k in selection)
            or len(selection) != len(set(selection)) or set(selection) - set(frame['eligible'])):
        raise ValueError('selection requires unique eligible canonical IDs')
    if not selection and frame['step'].get('mapped_parent'):
        raise ValueError('empty selection cannot omit the required mapped parent')
    # Apply the same existing mapped-parent rule as native selection/evaluation.
    return study.select_candidates(frame['rows'], selection, limit=len(selection),
                                   mapped_parent=frame['step'].get('mapped_parent'))


def apply_review_hold(row, review):
    """Carry an explicit saved review only when its whole answer set survives."""
    if row['reason']:
        return
    available = set(row['queried']) | set(row['verification'])
    missing = sorted(set(review['comparison_ids']) - available)
    if missing:
        row.update(unresolved=missing, same_graph=False)
    else:
        # The original review stopped placement before any further implied
        # comparisons. Do not price or invent answers for those requests.
        verification = {k: v for k, v in row['verification'].items() if k in review['comparison_ids']}
        row.update(reason=review['reason'], same_graph=True, source_review_hold=True,
                   unresolved=[], verification=verification,
                   retained_cases=len(set(row['queried']) | set(verification)))


def evaluate_case(frame, selection, study, modules, *, history=None, review=None):
    selected = checked_selection(frame, selection, study)
    unknown = sorted(set(selected) - frame['known'].keys())
    if unknown:
        row = dict(index=frame['step']['index'], queried=selected, verification={},
                   unresolved=unknown, reason=None, same_graph=False,
                   retained_cases=len(selected), original_cases=len(frame['known']))
        observed = {}
    else:
        row = study.evaluate(frame, selected, len(selected), modules, history=history)
        if review:
            apply_review_hold(row, review)
        observed = {}
        if not row['reason'] and not row['unresolved']:
            values = {k: frame['known'][k]['parsed'] for k in
                      set(row['queried']) | set(row['verification'])}
            snapshot = frame['snapshot'] if history is None else dict(frame['snapshot'], steps=history)
            nodes, target, reason, _ = modules[1]._placement(snapshot, frame['step']['local'],
                                                           frame['step']['selected_meaning'], values)
            if reason:
                raise ValueError('native evaluation and placement disagree: ' + reason)
            observed = relationships(nodes, target, frame['ids'])
    row.update(assess(expectation(frame), row['reason'], row['unresolved'], observed),
               observed_relationships=observed)
    if row.get('source_review_hold'):
        row['outcome'] = 'source_review_hold'
    return row


def load_frames(paths):
    if __package__:
        from . import candidate_ranking_study as study
    else:
        import candidate_ranking_study as study
    if paths.get('vectors'):
        state, frames, provenance, modules = study.read_frames(
            paths['reference_project'], paths['trial'], paths['vectors'], paths['subject_probe'])
    else:
        state, frames, provenance, modules = study.read_native_frames(paths['reference_project'], paths['trial'])
    return study, state, frames, provenance, modules


def cost_reference(audit, state_sha256, baseline):
    comparison = baseline['known_catalog_cost_estimate_usd']
    if 'cost_by_kind' in audit:
        if audit['state_sha256'] != state_sha256:
            raise ValueError('cost audit uses a different hierarchy')
        kinds = audit['cost_by_kind']
        audited = sum(kinds[k]['known_catalog_cost_estimate_usd'] for k in ('comparison', 'verification'))
        if abs(audited - comparison) > 1e-8:
            raise ValueError('native accounting differs from frozen cost audit')
        total = sum(v['known_catalog_cost_estimate_usd'] for v in kinds.values())
        missing = sum(v['attempts_without_usage'] for v in kinds.values())
    elif audit.get('summary_version') == 'experiment-usage-summary-v2':
        total = audit['generation_usage']['known_catalog_cost_estimate_usd']
        missing = audit['generation_usage']['attempts_without_usage']
        if comparison > total + 1e-8:
            raise ValueError('comparison subtotal exceeds original generation cost')
    else:
        raise ValueError('unsupported native cost reference')
    return dict(overhead_usd=max(0.0, total-comparison), known_total_usd=total,
                attempts_without_usage=missing)


def validate_usage_reference(audit, frames):
    """Validate the existing native generation accounting without inference."""
    if 'cost_by_kind' in audit:
        return {}
    if audit.get('summary_version') != 'experiment-usage-summary-v2' or not audit['complete']:
        raise ValueError('complete native usage summary required')
    source = audit['source']
    if digest(source['path']) != source['sha256']:
        raise ValueError('native usage inventory changed')
    inventory = {str(Path(p).resolve()) for group in read(source['path'])['groups'].values() for p in group}
    phases = {str(Path(p['experiment']).resolve()) for f in frames for p in f['step']['comparison_phases']}
    if phases - inventory:
        raise ValueError('native usage inventory omits comparison phases')
    usage = importlib.import_module('sse_multivector.experiment_usage_summary')
    originals = {(Path(s['results_path']).resolve(), s['result_line']): s
                 for s in audit['generation_usage']['sources']}
    if len(originals) != len(audit['generation_usage']['sources']):
        raise ValueError('native generation source repeats an attempt')
    local = {key for key, s in originals.items() if not s['added_from_reuse']}
    checked = usage._generation_usage(originals, local)
    for key in ('input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens',
                'reasoning_tokens', 'attempts_without_usage', 'attempts_without_cost_estimate', 'original_calls'):
        if checked[key] != audit['generation_usage'][key]:
            raise ValueError('native generation accounting differs: ' + key)
    if abs(checked['known_catalog_cost_estimate_usd'] - audit['generation_usage']['known_catalog_cost_estimate_usd']) > 1e-8:
        raise ValueError('native generation cost differs')
    return {source['path']: source['sha256'], usage.__file__: digest(usage.__file__)}


def freeze(args):
    paths = {k: None if getattr(args, k) is None else str(getattr(args, k).resolve()) for k in
             ('reference_project', 'trial', 'vectors', 'subject_probe', 'cost_audit')}
    study, state, frames, provenance, modules = load_frames(paths)
    audit = read(paths['cost_audit'])
    usage_sources = validate_usage_reference(audit, frames)
    baseline = study.comparison_costs(frames, {f['step']['index']: set(f['known']) for f in frames}, modules[0])
    cost_reference(audit, provenance['state_sha256'], baseline)
    corpus = read(state['corpus'])
    selected_notes = {s['local']['note_id'] for s in state['steps']}
    versions = sorted({n['origin']['prompt_version'] for n in corpus['notes']
                       if n['note_id'] in selected_notes})
    if not versions or any(not v.startswith('ASv6.') or not v[5:].isdigit() for v in versions):
        raise ValueError('unknown subject provenance')
    protected = dict(state['sources'])
    protected.update(usage_sources)
    vector_sources = []
    if paths['vectors']:
        protected.update(read(Path(paths['vectors']) / 'inputs.json')['protected_sha256'])
        vector_sources = [str(Path(paths['vectors']) / 'inputs.json'),
                          str(Path(paths['vectors']) / 'worker-result/worker-receipt.json')]
    protected.update(provenance['reference_code_sha256'])
    for path in (provenance['source_state'], paths['cost_audit'], *vector_sources):
        protected[path] = digest(path)
    reviews = {}
    for frame in frames:
        original = study.evaluate(frame, frame['pool'], len(frame['pool']), modules)
        step = frame['step']
        if step['status'] == 'held' and not original['reason']:
            if step['reviewer'] != 'agent' or not step.get('reason') or not step.get('comment'):
                raise ValueError('original hold lacks native or explicit review evidence')
            reviews[str(step['index'])] = dict(reason=step['reason'], comment=step['comment'],
                                             comparison_ids=list(frame['known']), attribution='agent')
    suite = dict(schema_version=2, id=args.id, paths=paths, protected_sha256=protected,
        provenance=provenance, subject_versions=versions,
        data_status=('historical_deprecated' if any(int(v[5:]) < 100 for v in versions)
                     else 'requires_current_pipeline_qualification'),
        note_count=len(selected_notes), local_entry_count=len(state['steps']),
        case_count=len(frames), cases=[expectation(f) for f in frames],
        source_review_holds=reviews,
        human_reviewed_cases=0, new_teacher_calls=0,
        interpretation='Historical preservation tests; not semantic gold or end-hierarchy acceptance.')
    write_once(args.output, suite)
    print(json.dumps({k: suite[k] for k in ('id', 'note_count', 'case_count', 'data_status')}))


def selections_from_report(path, profile, state_sha256, indices):
    report = read(path)
    if report.get('provenance', {}).get('state_sha256', report.get('state_sha256')) != state_sha256:
        raise ValueError('selection report uses a different frozen hierarchy')
    if profile is None:
        rows = report['steps']
    else:
        profiles = dict(report.get('profiles', {}), **report.get('extended_profiles', {}))
        rows = profiles[profile]['steps']
    selections = {r['index']: r['queried'] for r in rows}
    if len(selections) != len(rows) or set(selections) != set(indices):
        raise ValueError('selection report must cover every frozen case exactly once')
    return selections


def evaluate(args):
    suite = read(args.suite)
    if suite.get('schema_version') not in (1, 2):
        raise ValueError('unsupported selection regression suite')
    for path, expected in suite['protected_sha256'].items():
        if digest(path) != expected:
            raise ValueError('frozen selection source changed: ' + path)
    study, state, frames, provenance, modules = load_frames(suite['paths'])
    if [expectation(f) for f in frames] != suite['cases']:
        raise ValueError('frozen case expectations changed')
    if args.selection_report:
        selected = selections_from_report(args.selection_report, args.profile,
            provenance['state_sha256'], [f['step']['index'] for f in frames])
        selection_source = dict(path=str(args.selection_report.resolve()),
                                sha256=digest(args.selection_report), profile=args.profile)
    else:
        if args.method != 'baseline' and any('scores' not in f for f in frames):
            raise ValueError('this method needs auxiliary vectors; use baseline or a supplied selection report')
        selected = {f['step']['index']: study.select_candidates(f['rows'],
            f['pool'] if args.method == 'baseline' else study.orders(f)[args.method],
            limit=args.limit, mapped_parent=f['step'].get('mapped_parent')) for f in frames}
        selection_source = dict(method=args.method, limit=args.limit)
    reviews = suite.get('source_review_holds', {})
    rows = [evaluate_case(f, selected[f['step']['index']], study, modules,
                         review=reviews.get(str(f['step']['index']))) for f in frames]
    # Single-case results always use their own original graph/history. The
    # sequential check instead removes skipped answers and stops at divergence.
    history, sequence = [], []
    by_index = {f['step']['index']: f for f in frames}
    for step in state['steps']:
        if step['index'] not in by_index:
            history.append(step)
            continue
        row = evaluate_case(by_index[step['index']], selected[step['index']], study, modules,
                            history=history, review=reviews.get(str(step['index'])))
        sequence.append(row)
        if not row['same_graph']:
            break
        history.append(study.history_step(step, set(row['queried']) | set(row['verification'])))
    baseline = study.comparison_costs(frames, {f['step']['index']: set(f['known']) for f in frames}, modules[0])
    priced = None
    if not any(r['unresolved'] for r in rows):
        priced = study.comparison_costs(frames, {r['index']: set(r['queried']) | set(r['verification'])
                                               for r in rows}, modules[0])
    audit = read(suite['paths']['cost_audit'])
    validate_usage_reference(audit, frames)
    reference = cost_reference(audit, provenance['state_sha256'], baseline)
    overhead, original = reference['overhead_usd'], reference['known_total_usd']
    candidate = None if priced is None else priced['known_catalog_cost_estimate_usd'] + overhead
    report = dict(schema_version=1, suite_id=suite['id'], suite_sha256=digest(args.suite),
        data_status=suite['data_status'], subject_versions=suite['subject_versions'],
        selection=selection_source, new_teacher_calls=0, human_reviewed_cases=suite['human_reviewed_cases'],
        single_case_summary=dict(Counter(r['outcome'] for r in rows)), steps=rows,
        sequential_check=dict(complete=len(history) == len(state['steps']),
            matched_local_entries=len(history), steps=sequence,
            first_difference=None if len(history) == len(state['steps']) else sequence[-1]),
        frozen_snapshot_cost=dict(baseline_comparison=baseline, retained_comparison=priced,
            retained_original_overhead_usd=overhead, baseline_known_total_usd=original,
            candidate_known_total_usd=candidate,
            reduction_percent=None if candidate is None else 100 * (1-candidate/original),
            original_attempts_without_usage=reference['attempts_without_usage'],
            complete_total_usd=None,
            interpretation='Conditional saved-token projection, not realized whole-build savings.'),
        limitations=['Old teacher answers are not human semantic gold.',
            'Unqueried relationships remain unknown, not negative.',
            'Reachable historical relationships and holds are measured; full graph equality is reported separately.',
            'Sequential replay stops when the original graph changes; later fixed-case costs are projections.',
            'This suite is visible development data, not an untouched final test.'])
    write_once(args.output, report)
    print(json.dumps(dict(selection=selection_source, outcomes=report['single_case_summary'],
        complete=report['sequential_check']['complete'], matched=len(history),
        cost_reduction_percent=report['frozen_snapshot_cost']['reduction_percent'])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('freeze', help='Freeze native cases and historical expectations; no inference.')
    for name in ('reference-project', 'trial', 'cost-audit'):
        prepare.add_argument('--' + name, type=Path, required=True)
    for name in ('vectors', 'subject-probe'):
        prepare.add_argument('--' + name, type=Path)
    prepare.add_argument('--id', required=True)
    prepare.add_argument('--output', type=Path, required=True)
    run = commands.add_parser('evaluate', help='Evaluate a fixed selection against saved answers; no inference.')
    run.add_argument('--suite', type=Path, required=True)
    methods = run.add_mutually_exclusive_group(required=True)
    methods.add_argument('--method', choices=('baseline', 'heading', 'meaning', 'contextual_heading',
                                            'contextual_meaning', 'meaning_hybrid', 'late_interaction'))
    methods.add_argument('--selection-report', type=Path)
    run.add_argument('--limit', type=int, default=16)
    run.add_argument('--profile')
    run.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'freeze' and bool(args.vectors) != bool(args.subject_probe):
        parser.error('--vectors and --subject-probe must be supplied together')
    if args.command == 'evaluate' and (args.limit < 1 or (args.profile and not args.selection_report)):
        parser.error('positive limit required; --profile requires --selection-report')
    (freeze if args.command == 'freeze' else evaluate)(args)


if __name__ == '__main__':
    main()
