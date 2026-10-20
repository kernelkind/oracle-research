"""Publish final saved equivalence, runtime and classifier-learning evidence."""
from pathlib import PurePosixPath


_PRIVATE = {'path', 'directory', 'working_directory', 'codex_home', 'codex_binary',
            'api_key', 'credentials', 'authentication', 'auth_file', 'access_token',
            'refresh_token', 'thread_id', 'session_id', 'error', 'error_message',
            'argv', 'stdout', 'stderr'}
_REQUIRED = {
    'numerical-equivalence': {'source_hash_updates', 'all_other_output_bytes_identical',
                              'expected_sha256', 'actual_sha256'},
    'numerical-runtime-equivalence': {'rows', 'one_vs_24_output_byte_identical',
        'same_output_as_v1', 'wall_reduction_percent', 'timing_qualification'},
    'validation-equivalence': {'same_audit_content_except_paths_and_source_hashes',
        'fresh_teacher_attempts', 'cpu_budget', 'source_binding_seconds', 'audit_seconds',
        'historical_serial_audit_seconds', 'timing_qualification'},
    'learning-concurrency': {'schema_version', 'binding', 'config', 'data', 'complete',
        'training_finished', 'checkpoints', 'baseline', 'updates', 'workload'},
}


def _require(condition, message):
    if not condition:
        raise ValueError('performance publication: ' + message)


def _binding(value):
    return {key: value[key] for key in ('path', 'sha256')}


def _safe(value, field=None):
    """Retain native scientific values; remove local execution identities."""
    if isinstance(value, dict):
        if field == 'thread_cpu_ticks':
            # Keep every measured value, in saved order, without OS thread IDs.
            return list(value.values())
        result = {}
        for key, item in value.items():
            if key in _PRIVATE or key == 'pid' or key.endswith(('_pid', '_path', '_directory')):
                continue
            public_key = PurePosixPath(key).name if key.startswith('/') else key
            _require(public_key not in result, 'portable source field collision')
            result[public_key] = _safe(item, key)
        return result
    if isinstance(value, list):
        return [_safe(item, field) for item in value]
    return value


def prepare(sources, selection, metadata):
    kind = selection.get('kind')
    declarations = selection.get('reports')
    _require(kind in _REQUIRED and isinstance(declarations, list) and declarations,
             'unsupported final performance selection')
    records, native, baseline_decisions, checkpoint_decisions, cases = [], {}, 0, 0, set()
    for declaration in declarations:
        identifier = declaration.get('id')
        _require(isinstance(identifier, str) and identifier and identifier not in native,
                 'duplicate or missing condition identity')
        value = sources.read(declaration['path'])
        _require(isinstance(value, dict) and _REQUIRED[kind] <= value.keys(),
                 'unsupported final performance report')
        native[identifier] = value
        if kind == 'learning-concurrency':
            _require(value['schema_version'] == 1 and value['complete'] is True
                     and value['training_finished'] is True
                     and isinstance(value['checkpoints'], list) and value['checkpoints'],
                     'learning condition is not a completed saved report')
            before = value['baseline'].get('decisions', [])
            baseline_decisions += len(before)
            for checkpoint in value['checkpoints']:
                rows = checkpoint['evaluation']['decisions']
                checkpoint_decisions += len(rows)
                before_ids = [row['case_id'] for row in before]
                _require(before_ids == [row['case_id'] for row in rows]
                         and len(before_ids) == len(set(before_ids)),
                         'classifier checkpoint/baseline case identities differ')
                _require([row['target'] for row in before] == [row['target'] for row in rows],
                         'classifier checkpoint/baseline targets differ')
                cases.update(before_ids)
        records.append({'type': 'measurements', 'condition': identifier,
                        'source': _binding(declaration), 'data': _safe(value)})
    summary = selection.get('summary')
    if kind == 'learning-concurrency':
        _require(isinstance(summary, dict), 'learning comparison requires its final summary')
        comparison = sources.read(summary['path'])
        _require(isinstance(comparison, dict) and comparison.get('schema_version') == 1
                 and set(comparison.get('runs', {})) == set(native)
                 and all(comparison['runs'][item['id']].get('report_sha256') == item['sha256']
                         for item in declarations), 'summary/report source binding differs')
        records.append({'type': 'comparison', 'source': _binding(summary), 'data': _safe(comparison)})
    else:
        _require(len(native) == 1 and summary is None, 'equivalence unit must contain one final report')
    reused = selection.get('reused_inputs', [])
    _require(isinstance(reused, list), 'invalid selected input references')
    inputs = [{'type': 'published_input_reference', **item} for item in reused]
    metadata.update(category='performance', kind=kind,
        status='complete' if kind == 'learning-concurrency' else 'not_recorded',
        evidence_status='Recorded final measurements and predictions; no model, training, timing or numerical replay was performed for publication.',
        subject_provenance={'lineage_status': 'Historical resource/equivalence evidence; AS provenance is not established by runtime success.',
            'generated_subjects_deprecated': None, 'raw_posts_deprecated': False},
        limitations=selection.get('limitations', []),
        source_records=[_binding(item) for item in declarations],
        reused_inputs=reused,
        projection={'thread_cpu_ticks': 'Saved tick values in saved order; OS thread identifiers omitted.',
            'classifier_predictions': 'Native baseline and checkpoint decisions stay within their recorded conditions; repeated case IDs are not new independent samples.',
            'excluded': 'Local paths, account/process identifiers, execution errors/logs, weights and training state.'},
        counts={'reports': len(native), 'comparison_summaries': int(summary is not None),
            'learning_conditions': len(native) if kind == 'learning-concurrency' else 0,
            'baseline_decisions': baseline_decisions, 'checkpoint_decisions': checkpoint_decisions,
            'distinct_evaluation_cases': len(cases)})
    return {'inputs.jsonl': iter(inputs), 'answers.jsonl': iter(()),
            'judgments.jsonl': iter(()), 'results.jsonl': iter(records)}
