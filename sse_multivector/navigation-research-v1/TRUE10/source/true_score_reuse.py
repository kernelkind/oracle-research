"""Reuse verified TRUE outputs by exact input text, without merging category IDs.

The caller must verify cached checkpoint, inference configuration and scorer
identity before supplying runs. No expected labels are used or propagated.
"""
from true_category_probe import model_input
from true_holdout_probe import threshold_decision


MEASUREMENTS = (
    'token_ids', 'batch_seconds', 'generated_text', 'generated_token_ids',
    'eos_terminated', 'predicted', 'entailment_score', 'threshold_predicted',
    'logit_0_first_token', 'logit_1_first_token', 'probability_0_first_token',
    'first_token_binary_score', 'first_token_binary_label',
    'label_prefix_probability_mass', 'argmax_token_id',
)


def validate_cache_identity(candidate, reference):
    """Require the same model manifest, scoring source and inference settings."""
    def settings(record):
        return {k: v for k, v in record['config'].items()
                if k not in ('experiment', 'load_seconds')}
    if settings(candidate) != settings(reference):
        raise ValueError('cache inference configuration differs')
    for key in ('model_files_sha256', 'source_sha256'):
        if candidate[key] != reference[key]:
            raise ValueError('cache identity differs: ' + key)


def _validate_score(row):
    if row.get('format') != 'topic' or row.get('model_input') != model_input(row, 'topic'):
        raise ValueError('cached/fresh score has inconsistent exact topic input')
    if row.get('threshold_predicted') is not threshold_decision(row['entailment_score']):
        raise ValueError('cached/fresh score differs from fixed cutoff')
    if row.get('predicted') is not None and type(row['predicted']) is not bool:
        raise ValueError('native decision must be Boolean or unresolved')


def plan_reuse(inputs, cached_runs):
    """First supplied source wins only when all repetitions agree in decisions.

    cached_runs is an ordered sequence of (source path, rows). Small numerical
    differences remain in the provenance; any native/cutoff disagreement causes
    that input to be freshly scored instead of selecting a favorable result.
    """
    unique = {}
    for row in inputs:
        unique.setdefault(row['model_input'], row)
    candidates = {}
    for source, rows in cached_runs:
        for index, row in enumerate(rows):
            _validate_score(row)
            key = row['model_input']
            if key in unique:
                candidates.setdefault(key, []).append(dict(
                    source=source, row_index=index, row_id=row['id'],
                    score=row['entailment_score'], native=row['predicted'],
                    cutoff=row['threshold_predicted'],
                    measurements={k: row[k] for k in MEASUREMENTS if k in row}))
    reused, conflicts, missing = {}, [], []
    for key, row in unique.items():
        matches = candidates.get(key, [])
        answers = {(r['native'], r['cutoff']) for r in matches}
        if len(answers) == 1:
            reused[key] = dict(chosen=matches[0], alternatives=[
                {k: v for k, v in r.items() if k != 'measurements'} for r in matches[1:]])
        else:
            missing.append(row)
            if len(answers) > 1:
                conflicts.append(dict(model_input=key, matches=[
                    {k: v for k, v in r.items() if k != 'measurements'} for r in matches]))
    return dict(total_directions=len(inputs), distinct_inputs=len(unique),
                reused=reused, conflicts=conflicts, missing_inputs=missing)


def assemble_scores(inputs, reuse_plan, fresh_scores, fresh_source):
    """Expand scored exact strings back to every original directed category pair."""
    expected = {r['model_input'] for r in reuse_plan['missing_inputs']}
    fresh = {}
    for index, row in enumerate(fresh_scores):
        _validate_score(row)
        key = row['model_input']
        if key not in expected or key in fresh:
            raise ValueError('unexpected or duplicate fresh input')
        fresh[key] = dict(source=fresh_source, row_index=index, row_id=row['id'],
                          measurements={k: row[k] for k in MEASUREMENTS if k in row})
    if set(fresh) != expected:
        raise ValueError('missing fresh scores; unscored must never become No')
    assembled = []
    for row in inputs:
        key = row['model_input']
        reused = reuse_plan['reused'].get(key)
        origin = reused['chosen'] if reused else fresh[key]
        base = {k: v for k, v in row.items() if k != 'expected'}
        assembled.append(dict(base, **origin['measurements'], score_origin=dict(
            source=origin['source'], row_index=origin['row_index'], row_id=origin['row_id'],
            reused=reused is not None)))
    return assembled
