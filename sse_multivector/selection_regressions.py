"""Freeze and evaluate offline selection cases using native saved comparisons.

No inference, new embeddings, graph writes or semantic approvals. Run this file
as a script: the reference project owns the frozen production readers/guards.
"""
import argparse
from collections import Counter
from graphlib import TopologicalSorter, CycleError
import hashlib
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


def evaluate_case(frame, selection, study, modules, *, history=None):
    selected = checked_selection(frame, selection, study)
    unknown = sorted(set(selected) - frame['known'].keys())
    if unknown:
        row = dict(index=frame['step']['index'], queried=selected, verification={},
                   unresolved=unknown, reason=None, same_graph=False,
                   retained_cases=len(selected), original_cases=len(frame['known']))
        observed = {}
    else:
        row = study.evaluate(frame, selected, len(selected), modules, history=history)
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
    return row


def load_frames(paths):
    if __package__:
        from . import candidate_ranking_study as study
    else:
        import candidate_ranking_study as study
    state, frames, provenance, modules = study.read_frames(
        paths['reference_project'], paths['trial'], paths['vectors'], paths['subject_probe'])
    return study, state, frames, provenance, modules


def freeze(args):
    paths = {k: str(getattr(args, k).resolve()) for k in
             ('reference_project', 'trial', 'vectors', 'subject_probe', 'cost_audit')}
    _, state, frames, provenance, _ = load_frames(paths)
    audit = read(paths['cost_audit'])
    if audit['state_sha256'] != provenance['state_sha256']:
        raise ValueError('cost audit uses a different hierarchy')
    corpus = read(state['corpus'])
    selected_notes = {s['local']['note_id'] for s in state['steps']}
    versions = sorted({n['origin']['prompt_version'] for n in corpus['notes']
                       if n['note_id'] in selected_notes})
    if not versions or any(not v.startswith('ASv6.') or not v[5:].isdigit() for v in versions):
        raise ValueError('unknown subject provenance')
    protected = dict(read(Path(paths['vectors']) / 'inputs.json')['protected_sha256'])
    protected.update(provenance['reference_code_sha256'])
    for path in (provenance['source_state'], paths['cost_audit'],
                 str(Path(paths['vectors']) / 'inputs.json'),
                 str(Path(paths['vectors']) / 'worker-result/worker-receipt.json')):
        protected[path] = digest(path)
    suite = dict(schema_version=1, id=args.id, paths=paths, protected_sha256=protected,
        provenance=provenance, subject_versions=versions,
        data_status=('historical_deprecated' if any(int(v[5:]) < 100 for v in versions)
                     else 'requires_current_pipeline_qualification'),
        note_count=len(selected_notes), local_entry_count=len(state['steps']),
        case_count=len(frames), cases=[expectation(f) for f in frames],
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
    if suite.get('schema_version') != 1:
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
        selected = {f['step']['index']: study.select_candidates(f['rows'], study.orders(f)[args.method],
            limit=args.limit, mapped_parent=f['step'].get('mapped_parent')) for f in frames}
        selection_source = dict(method=args.method, limit=args.limit)
    rows = [evaluate_case(f, selected[f['step']['index']], study, modules) for f in frames]
    # Single-case results always use their own original graph/history. The
    # sequential check instead removes skipped answers and stops at divergence.
    history, sequence = [], []
    by_index = {f['step']['index']: f for f in frames}
    for step in state['steps']:
        if step['index'] not in by_index:
            history.append(step)
            continue
        row = evaluate_case(by_index[step['index']], selected[step['index']], study, modules, history=history)
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
    audited_comparison = sum(audit['cost_by_kind'][k]['known_catalog_cost_estimate_usd']
                             for k in ('comparison', 'verification'))
    if abs(audited_comparison - baseline['known_catalog_cost_estimate_usd']) > 1e-8:
        raise ValueError('native accounting differs from frozen cost audit')
    overhead = sum(v['known_catalog_cost_estimate_usd'] for k, v in audit['cost_by_kind'].items()
                   if k not in ('comparison', 'verification'))
    original = baseline['known_catalog_cost_estimate_usd'] + overhead
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
            original_attempts_without_usage=sum(v['attempts_without_usage'] for v in audit['cost_by_kind'].values()),
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
    for name in ('reference-project', 'trial', 'vectors', 'subject-probe', 'cost-audit'):
        prepare.add_argument('--' + name, type=Path, required=True)
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
    if args.command == 'evaluate' and (args.limit < 1 or (args.profile and not args.selection_report)):
        parser.error('positive limit required; --profile requires --selection-report')
    (freeze if args.command == 'freeze' else evaluate)(args)


if __name__ == '__main__':
    main()
