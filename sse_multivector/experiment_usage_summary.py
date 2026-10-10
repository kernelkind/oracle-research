"""Native cross-experiment accounting, without inference or source writes."""

from collections import Counter
import json
from pathlib import Path

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


VERSION = 'experiment-usage-summary-v3'
STATUSES = ('valid', 'empty', 'malformed', 'invalid_receipt', 'failed', 'unrun')
TOKENS = ('input_tokens', 'cached_input_tokens', 'cache_write_tokens',
          'output_tokens', 'reasoning_tokens')
SETTINGS = ('provider', 'model', 'reasoning_effort', 'transport',
            'timeout_seconds', 'max_output_tokens', 'concurrency')
COUNTS = ('experiments', 'imported_experiments', 'cases', 'attempts', 'reused',
          'failed_attempts', 'recovered_failed_attempts', 'retry_attempts',
          'attempts_without_usage', 'attempts_without_cost_estimate',
          'known_catalog_cost_estimate_usd', *STATUSES, *('known_' + key for key in TOKENS))


def _empty():
    return dict.fromkeys(COUNTS, 0)


def _add(total, values):
    for key in COUNTS:
        total[key] += values[key]


def _cost_total(total):
    total['catalog_cost_estimate_usd'] = (None if total['attempts_without_cost_estimate']
                                         else total['known_catalog_cost_estimate_usd'])


def _generation_usage(originals, local_keys):
    """Union validated originals across experiments, including reuse-source retries."""
    try:
        from .experiment import usage_summary
    except ImportError:
        from experiment import usage_summary
    ledgers, costs, calls, warmup_calls, sources = {}, {}, [], [], []
    for (path, number), receipt in originals.items():
        if path not in ledgers:
            lines = path.read_bytes().splitlines(keepends=True)
            records = [json.loads(line) for line in lines]
            manifest_bytes = (path.parent / 'manifest.json').read_bytes()
            manifest = json.loads(manifest_bytes)
            ledgers[path] = (lines, records, engine._sha256_bytes(manifest_bytes),
                             manifest.get('cache_warmup', False))
            costs[path] = engine.load_reconciled_costs(path.parent, records)
        lines, records, manifest_hash, warmup = ledgers[path]
        if not 1 <= number <= len(lines) or engine._sha256_bytes(lines[number - 1]) != receipt['result_sha256']:
            raise ValueError('summary original generation source changed')
        record = records[number - 1]
        if record.get('manifest_sha256') != manifest_hash:
            raise ValueError('summary original generation manifest changed')
        (warmup_calls if warmup else calls).append(
            (record, engine.provider_cost(record, costs[path])))
        sources.append({**receipt, 'added_from_reuse': (path, number) not in local_keys})
    usage = usage_summary(calls, strict=True, warmup_calls=warmup_calls)
    return {**usage, 'original_calls': len(originals),
            'source_calls_added': len(originals.keys() - local_keys),
            'failed_calls': sum(s['status'] == 'failed' for s in sources),
            'usage_complete': usage['attempts_without_usage'] == 0,
            'reasoning_included_in_output': True, 'sources': sources}


def summarize_experiments(source_path, *, load_report):
    """Summarize validated local attempts; reuse-source/import usage stays separate."""
    source_path = Path(source_path).expanduser().resolve()
    source_hash = engine._sha256_file(source_path)
    source = engine._load_json(source_path, 'experiment summary source')
    fields = {'schema_version', 'groups'}
    if 'attempt_budget' in source:
        fields.add('attempt_budget')
    engine._expect_fields(source, 'experiment summary source', fields)
    if type(source['schema_version']) is not int or source['schema_version'] != 1:
        raise ValueError('experiment summary schema_version must be 1')
    groups = source['groups']
    if not isinstance(groups, dict) or not groups or any(
            not isinstance(name, str) or not name.strip() for name in groups):
        raise ValueError('experiment summary groups must be named lists')
    directories, seen = {}, set()
    for name, paths in groups.items():
        paths = engine._validate_string_array(paths, 'experiment summary group', allow_empty=True)
        directories[name] = []
        for path in paths:
            directory = engine._resolve_path(path, 'summary experiment', source_path.parent)
            if directory in seen:
                raise ValueError(f'duplicate canonical experiment: {directory}')
            seen.add(directory)
            directories[name].append(directory)
    if not seen:
        raise ValueError('experiment summary requires at least one experiment')
    budget = source.get('attempt_budget')
    if budget is not None:
        engine._expect_fields(budget, 'summary attempt_budget', {'path', 'groups'})
        budget_groups = engine._validate_string_array(budget['groups'], 'budget groups', allow_empty=False)
        if len(set(budget_groups)) != len(budget_groups) or set(budget_groups) - set(groups):
            raise ValueError('budget groups must be distinct existing summary groups')
        budget_path = engine._resolve_path(budget['path'], 'summary attempt budget', source_path.parent)
    output = dict(schema_version=1, summary_version=VERSION,
        source=dict(path=str(source_path), sha256=source_hash), groups={}, totals=_empty(),
        models=[], reasoning_included_in_output=True, complete=True, usage_complete=True,
        warnings=[])
    native_ledgers, models, originals, local_keys = {}, {}, {}, set()
    for name, paths in directories.items():
        group = dict(experiments=[], totals=_empty())
        for path in paths:
            report = load_report(path, generation_costs=True, include_request_preview=False)
            if Path(report['experiment']).resolve() != path:
                raise ValueError('summary experiment report identity differs')
            summary, usage = report['summary'], report['usage']
            local = [s for s in report['generation_usage']['sources'] if not s['added_from_reuse']]
            if len(local) != summary['attempts']:
                raise ValueError('native local attempt count differs from report')
            for ledger in {Path(s['results_path']).resolve() for s in local}:
                if ledger in native_ledgers:
                    raise ValueError(f'duplicate native run-directory alias: {path} and {native_ledgers[ledger]}')
                native_ledgers[ledger] = path
            successes = {}
            per_job = Counter()
            for attempt in local:
                per_job[attempt['job_key']] += 1
                if attempt['status'] == 'succeeded':
                    successes[attempt['job_key']] = max(
                        successes.get(attempt['job_key'], 0), attempt['result_line'])
            totals = _empty()
            totals.update({key: summary[key] for key in ('cases', 'attempts', 'reused', *STATUSES)})
            totals.update(failed_attempts=sum(s['status'] == 'failed' for s in local),
                recovered_failed_attempts=sum(s['status'] == 'failed'
                    and s['result_line'] < successes.get(s['job_key'], 0) for s in local),
                retry_attempts=sum(count - 1 for count in per_job.values()),
                attempts_without_usage=usage['attempts_without_usage'])
            totals.update({key: usage[key] for key in
                           ('attempts_without_cost_estimate', 'known_catalog_cost_estimate_usd')})
            totals.update({'known_' + key: usage[key] for key in TOKENS})
            _cost_total(totals)
            settings = {key: report['settings'].get(key) for key in SETTINGS}
            entry = dict(experiment=str(path), prompt_id=report['prompt_id'], adapter=report['adapter'],
                imported=report['imported'], settings=settings, summary=dict(summary), totals=totals,
                usage_complete=usage['attempts_without_usage'] == 0,
                complete=not report['imported'] and not any(summary[key] for key in
                    ('malformed', 'invalid_receipt', 'failed', 'unrun')))
            if report['imported']:
                entry['historical_totals'] = totals
                entry['totals'] = _empty()
                entry['totals']['imported_experiments'] = 1
                output['warnings'].append(f'{path}: imported historical attempts excluded from new totals and budget reconciliation')
            else:
                for receipt in report['generation_usage']['sources']:
                    key = (Path(receipt['results_path']).resolve(), receipt['result_line'])
                    if key in originals and originals[key]['result_sha256'] != receipt['result_sha256']:
                        raise ValueError('summary original generation source changed')
                    originals[key] = receipt
                    if not receipt['added_from_reuse']:
                        local_keys.add(key)
            if not entry['complete'] and not report['imported']:
                output['warnings'].append(f'{path}: incomplete experiment; saved attempts still counted')
            entry['totals']['experiments'] = 1
            _cost_total(entry['totals'])
            group['experiments'].append(entry)
            _add(group['totals'], entry['totals'])
            key = tuple(settings.items())
            model = models.setdefault(key, dict(settings=settings, totals=_empty()))
            _add(model['totals'], entry['totals'])
            output['complete'] &= entry['complete']
        _cost_total(group['totals'])
        output['groups'][name] = group
        _add(output['totals'], group['totals'])
    output['models'] = list(models.values())
    for model in output['models']:
        _cost_total(model['totals'])
    _cost_total(output['totals'])
    output['generation_usage'] = _generation_usage(originals, local_keys)
    output['usage_complete'] = output['totals']['attempts_without_usage'] == 0
    if not output['usage_complete']:
        output['warnings'].append('Token values are known subtotals only; unknown-usage attempts are not zero-cost calls')
    if output['generation_usage']['attempts_without_cost_estimate']:
        output['warnings'].append('Generation catalog cost is a known subtotal only; missing estimates are not zero-cost calls')
    if budget is not None:
        counted = sum(output['groups'][name]['totals']['attempts'] for name in budget_groups)
        with engine.PersistentAttemptBudget(budget_path)._values() as (values, _):
            snapshot = dict(values[0][1])
        delta = snapshot['used'] - counted
        output['attempt_budget'] = dict(snapshot, path=str(budget_path), groups=list(budget_groups),
            counted_attempts=counted, delta=delta, status='reconciled' if delta == 0 else 'unreconciled',
            explanation=('Count matches the locked counter snapshot.' if delta == 0 else
                'Positive delta may reflect pending/crash-conservative reservations or omitted experiments; '
                'negative delta may reflect uncharged or misgrouped experiments. No refund is implied.'))
    if engine._sha256_file(source_path) != source_hash:
        raise ValueError('experiment summary source changed while reporting')
    return output


def compact_summary(result, output):
    return {key: result[key] for key in
            ('summary_version', 'totals', 'complete', 'usage_complete', 'warnings', 'reasoning_included_in_output')} | {
        'output': str(Path(output).resolve()), 'attempt_budget': result.get('attempt_budget'),
        'generation_usage': {key: value for key, value in result['generation_usage'].items()
                             if key != 'sources'}}
