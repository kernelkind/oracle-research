"""Offline gap-statistic screen over a frozen section-count panel.

Reuse observed assignments. Reference data is uniform in the full nonzero PCA
box, translated back to the original coordinates. The existing partitioner
normalizes inputs internally; squared-Euclidean within-group dispersion is
measured on the supplied coordinates, as in the published gap definition.
This tests a reference-distribution assumption, not semantic correctness.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from . import direct_section_partition as direct
from . import section_count_panel as panel


def dispersion(vectors, labels):
    """Sum squared distances to each group's arithmetic mean, without pairs."""
    vectors, labels = np.asarray(vectors), np.asarray(labels)
    total = 0.
    for label in np.unique(labels):
        group = vectors[labels == label]
        total += float(((group - group.mean(axis=0)) ** 2).sum())
    return total


def select_count(counts, observed, references, *, method='adjacent'):
    """Compare published decision rules using identical saved gap statistics.

    The default adjacent rule and population SD remain unchanged. Global rules
    match cluster::maxSE's selection formulas, without changing the dispersion
    or reference uncertainty to R's different variance convention.
    """
    observed, references = np.asarray(observed), np.asarray(references)
    if (observed.shape != (len(counts),) or references.ndim != 2
            or references.shape[1] != len(counts) or len(references) < 2
            or not np.isfinite(observed).all() or not np.isfinite(references).all()
            or np.any(observed <= 0) or np.any(references <= 0)):
        raise ValueError('Finite positive observed and reference dispersions required')
    log_reference = np.log(references)
    gap = log_reference.mean(axis=0) - np.log(observed)
    s = np.sqrt(1 + 1 / len(references)) * log_reference.std(axis=0, ddof=0)
    if method == 'adjacent':
        chosen = next((i for i in range(len(counts) - 1)
                       if gap[i] >= gap[i + 1] - s[i + 1]), len(counts) - 1)
    elif method in ['globalmax', 'globalSEmax']:
        peak = int(gap.argmax())
        chosen = peak if method == 'globalmax' else next(
            (i for i in range(peak) if gap[i] >= gap[peak] - s[peak]), peak)
    else:
        raise ValueError('Unknown gap decision method')
    return dict(selected_count=int(counts[chosen]), gap=gap.tolist(), s=s.tolist(),
                log_observed=np.log(observed).tolist(),
                mean_log_reference=log_reference.mean(axis=0).tolist(),
                at_largest_tested_count=chosen == len(counts) - 1)


def prepare(source, output, *, references=32, seed=20261101, cases=None,
            role='development', method='adjacent'):
    source, output = Path(source).resolve(), Path(output).resolve()
    if (type(references) is not int or references < 4 or references % 2
            or type(seed) is not int or seed < 0):
        raise ValueError('An even reference count of at least four and a nonnegative seed required')
    if role not in ['development', 'reserved']:
        raise ValueError('Unknown panel role')
    rules = dict(adjacent='Smallest k with gap(k) >= gap(k+1) - s(k+1); otherwise largest tested k',
                 globalmax='First k attaining the largest gap over all tested counts',
                 globalSEmax='Smallest k no later than the first maximum with gap(k) >= gap(maximum) - s(maximum)')
    if method not in rules:
        raise ValueError('Unknown gap decision method')
    if role == 'reserved' and cases is None:
        raise ValueError('Reserved validation requires explicit case IDs')
    original = panel._read(source / 'plan.json')
    panel._check_files(original['code_files'])
    eligible = {c['id'] for c in original['cases'] if c['role'] == role}
    if cases is not None and (not cases or len(set(cases)) != len(cases) or not set(cases) <= eligible):
        raise ValueError(f'Select unique existing {role} cases only')
    requested = eligible if cases is None else set(cases)
    output.mkdir(parents=True, exist_ok=False)
    sources, selected_cases = {}, []
    files = {str(source / 'plan.json'): panel._sha(source / 'plan.json')}
    for cfg in original['cases']:
        if cfg['id'] not in requested:
            continue
        name = cfg['source']
        if name not in sources:
            src = original['spec']['sources'][name]
            sources[name] = panel._load_source(src)
            files.update(src['files'])
        raw, rawnotes, entries = sources[name]
        vectors, notes = raw[cfg['indices']], rawnotes[cfg['indices']]
        if [entries[i]['id'] for i in cfg['indices']] != cfg['entry_ids']:
            raise ValueError('Original selected entries disagree')
        counts = [k for k in cfg['counts'] if k < len(vectors)]
        observed, consumed = [], {}
        for k in cfg['counts']:
            path = source / cfg['id'] / f'count-{k}.json'
            saved = panel._read(path)
            if saved['binding'] != dict(plan_sha256=files[str(source / 'plan.json')], case_id=cfg['id'], count=k):
                raise ValueError('Observed count has different frozen bindings')
            panel._verify(saved['panel'], vectors, notes, k, cfg['minimum_notes'], original['spec']['seeds'])
            consumed[str(path)] = panel._sha(path)
            if k in counts:
                best = saved['panel']['best']
                observed.append(dict(count=k, dispersion=dispersion(vectors, best['labels']),
                    objective=best['objective'], seed=best['seed'], labels=best['labels'],
                    notes_per_child=best['section_notes']))
        files.update(consumed)
        one = dispersion(vectors, np.zeros(len(vectors), dtype=int))
        tolerance = 64 * np.finfo(float).eps * max(1., float((vectors ** 2).sum()))
        if one <= tolerance:
            status = 'zero observed dispersion'
        elif len(counts) < 2:
            status = 'no nonsaturated alternative'
        elif any(r['dispersion'] <= tolerance for r in observed):
            status = 'zero dispersion prevents logarithmic comparison'
        else:
            status = 'ready'
        destination = output / cfg['id']
        destination.mkdir()
        center = vectors.mean(axis=0)
        if status == 'ready':
            _, singular, rotation = np.linalg.svd(vectors - center, full_matrices=False)
            rank = int(np.sum(singular > singular[0] * max(vectors.shape) * np.finfo(float).eps))
            rotation = rotation[:rank]
            coordinates = (vectors - center) @ rotation.T
            low, high = coordinates.min(axis=0), coordinates.max(axis=0)
        else:
            rank = 0
            rotation, low, high = np.empty((0, vectors.shape[1])), np.empty(0), np.empty(0)
        data = destination / 'input.npz'
        np.savez(data, vectors=vectors, notes=notes, center=center,
                 rotation=rotation, low=low, high=high)
        files[str(data)] = panel._sha(data)
        selected_cases.append(dict(id=cfg['id'], status=status, original_case=cfg, counts=counts,
                          observed=observed, data=str(data), rank=rank))
    plan = dict(status='Frozen gap screen; no HiGen integration or count policy',
        source=str(source), cases=selected_cases, files=files,
        references=references, reference_seed=seed, role=role, method=method,
        reference_distribution='Uniform full nonzero PCA box plus original mean; no radial projection',
        dispersion='Sum of squared Euclidean distances to arithmetic group means on supplied coordinates',
        clustering='Unchanged spherical partitioner, original note minima and starts; lowest cosine objective',
        rule=rules[method],
        uncertainty='Population SD of reference log dispersions times sqrt(1+1/B)',
        singular_cases='No split for zero total dispersion; k >= entry count excluded; other zero dispersions unresolved',
        settings=original['spec'],
        code_files={str(Path(p).resolve()): panel._sha(p)
                    for p in [__file__, panel.__file__, direct.__file__]})
    panel._write(output / 'plan.json', plan)
    return plan


def _reference(task):
    destination, binding, cfg, settings, seed = task
    started = time.monotonic()
    with np.load(cfg['data'], allow_pickle=False) as data:
        count = len(data['notes'])
        rng = np.random.default_rng(seed)
        vectors = rng.uniform(data['low'], data['high'], size=(count, cfg['rank'])) @ data['rotation'] + data['center']
        notes = data['notes']
    rows = []
    for k in cfg['counts']:
        if k == 1:
            unit = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
            rows.append(dict(count=1, dispersion=dispersion(vectors, np.zeros(count, dtype=int)),
                best_seed=None, labels=[0] * count,
                objective=float(count - np.linalg.norm(unit.sum(axis=0))),
                notes_per_child=[len(np.unique(notes))], converged=True, trials=[]))
            continue
        trials = []
        for fit_seed in settings['seeds']:
            t = direct.partition(vectors, notes, sections=k,
                minimum_notes=cfg['original_case']['minimum_notes'], seed=fit_seed,
                max_iterations=settings['max_iterations'], time_limit=settings['time_limit'])
            trials.append(t)
        best = min(trials, key=lambda t: (t['objective'], t['seed']))
        rows.append(dict(count=k, dispersion=dispersion(vectors, best['labels']),
            best_seed=best['seed'], labels=best['labels'], objective=best['objective'],
            notes_per_child=best['section_notes'], converged=best['converged'],
            trials=[{key: t[key] for key in ['seed', 'objective', 'converged', 'iterations']}
                    for t in trials]))
    saved = dict(binding=binding, seed=seed,
        reference_matrix_sha256=hashlib.sha256(vectors.tobytes()).hexdigest(),
        rows=rows, elapsed_seconds=time.monotonic() - started)
    panel._write(destination, saved)
    return str(destination)


def _check_reference(saved, binding, counts, seeds, reference_seed):
    if saved['binding'] != binding or [r['count'] for r in saved['rows']] != counts:
        raise ValueError('Reference has different frozen bindings or counts')
    if saved['seed'] != reference_seed + binding['reference_index']:
        raise ValueError('Saved reference seed disagrees with the frozen seed')
    for row in saved['rows']:
        if (not np.isfinite(row['dispersion']) or row['dispersion'] <= 0
                or [t['seed'] for t in row['trials']] != ([] if row['count'] == 1 else seeds)):
            raise ValueError('Invalid reference dispersion or trial selection')
        if row['count'] > 1 and row['best_seed'] != min(
                row['trials'], key=lambda t: (t['objective'], t['seed']))['seed']:
            raise ValueError('Invalid reference trial selection')


def run(output, *, workers=1):
    if type(workers) is not int or workers < 1:
        raise ValueError('Positive local CPU worker count required')
    output = Path(output).resolve()
    plan = panel._read(output / 'plan.json')
    panel._check_files(plan['code_files'])
    panel._check_files(plan['files'])
    plan_hash = panel._sha(output / 'plan.json')
    tasks = []
    for cfg in plan['cases']:
        if cfg['status'] != 'ready':
            continue
        for index in range(plan['references']):
            path = output / cfg['id'] / f'reference-{index:03d}.json'
            binding = dict(plan_sha256=plan_hash, case_id=cfg['id'], reference_index=index)
            if path.exists():
                _check_reference(panel._read(path), binding, cfg['counts'], plan['settings']['seeds'], plan['reference_seed'])
            else:
                tasks.append((path, binding, cfg, plan['settings'], plan['reference_seed'] + index))
    if workers == 1:
        for task in tasks:
            _reference(task)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_reference, task) for task in tasks]
            for i, future in enumerate(as_completed(futures), 1):
                future.result()
                if i % 32 == 0:
                    print(json.dumps(dict(completed_references=i, new_references=len(tasks))), flush=True)
    results = []
    for cfg in plan['cases']:
        result = dict(case_id=cfg['id'], status=cfg['status'], counts=cfg['counts'],
                      selected_count=1 if cfg['status'] == 'zero observed dispersion' else None,
                      references=[])
        if cfg['status'] == 'ready':
            values = []
            for index in range(plan['references']):
                path = output / cfg['id'] / f'reference-{index:03d}.json'
                binding = dict(plan_sha256=plan_hash, case_id=cfg['id'], reference_index=index)
                saved = panel._read(path)
                _check_reference(saved, binding, cfg['counts'], plan['settings']['seeds'], plan['reference_seed'])
                values.append([r['dispersion'] for r in saved['rows']])
                result['references'].append(dict(path=str(path), sha256=panel._sha(path)))
            observed = [r['dispersion'] for r in cfg['observed']]
            method = plan.get('method', 'adjacent')
            result.update(select_count(cfg['counts'], observed, values, method=method))
            half = len(values) // 2
            result['separate_halves'] = [select_count(cfg['counts'], observed, part, method=method)['selected_count']
                                        for part in [values[:half], values[half:]]]
        panel._write(output / cfg['id'] / 'result.json', result)
        results.append(result)
    summary = dict(status='Offline screen only; no automatic policy adopted',
                   cases=results, new_reference_samples=len(tasks))
    panel._write(output / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('source', type=Path)
    prep.add_argument('output', type=Path)
    prep.add_argument('--references', type=int, default=32)
    prep.add_argument('--seed', type=int, default=20261101)
    prep.add_argument('--cases', nargs='+', help='Explicit cases from the chosen role; required for reserved validation')
    prep.add_argument('--role', choices=['development', 'reserved'], default='development')
    prep.add_argument('--method', choices=['adjacent', 'globalmax', 'globalSEmax'], default='adjacent')
    execute = commands.add_parser('run')
    execute.add_argument('output', type=Path)
    execute.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.source, args.output, references=args.references, seed=args.seed,
                         cases=args.cases, role=args.role, method=args.method)
        print(json.dumps(dict(cases=len(result['cases']), references=result['references'])))
    else:
        result = run(args.output, workers=args.workers)
        print(json.dumps(dict(cases=[dict(id=c['case_id'], count=c['selected_count']) for c in result['cases']],
                              new_reference_samples=result['new_reference_samples'])))


if __name__ == '__main__':
    main()
