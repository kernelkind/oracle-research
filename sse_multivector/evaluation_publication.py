"""Compact saved validation answers, final grades and final comparisons.

The GPU answer exporter uses only the standard library and already saved
per-note files. Historical host-side JSON arrays are streamed using ijson.
Original inputs, signed receipts and sealed test answers are never changed.
"""
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import re

_READ_LIMIT = 32 * 1024 * 1024
_SETTINGS = {
    'model', 'revision', 'device', 'quantization', 'seed', 'max_length',
    'max_new_tokens', 'batch_size', 'gradient_accumulation_steps', 'learning_rate',
    'lora_rank', 'lora_alpha', 'threads', 'gradient_checkpointing',
    'lora_target_modules', 'training_milestones', 'evaluation_tasks',
    'efficient_attention', 'fused_linear_cross_entropy', 'subject_batching',
    'max_steps', 'save_steps', 'subject_fraction', 'max_subjects', 'mask_batch_size',
}
_NESTED_SETTINGS = {'subjects', 'mask', 'budget_bytes', 'workspace_bytes',
    'prefill_bytes_per_token', 'attention_matrix_count'}
_CODE = {'distillation_run.py', 'distillation_data.py', 'extraction_pipeline.py',
    'mask_positions.py', '_runner_bootstrap.py', 'evaluation_publication.py'}
# All retained fields already occur in final evaluation/grade/comparison records.
_FIELDS = set('''
id note_id answer_id cohort version version_key stage status error reason task
subjects masks errors subject number context response meaning expressible evidence
mask spans start end text raw tokens truncated seconds scoring scores correctness
coverage findings skipped pending diagnostics_complete teacher_meanings teacher_numbers
required numerator denominator value incorrect_subjects invalid_relationships parent
child covered matched_student_numbers missing_heading_numbers pending_heading_numbers
heading_numbers relationships compatibility matching support student_number student_numbers
heading_number parent_number child_number teacher_id teacher_number dependencies premises
coverage_inconsistencies case_id check input_sha256 output_sha256 prompt_sha256 origin
receipt record_sha256 reviews audits actor role verdict current decision decision_conflicts
mechanical_evidence mechanical_sha256 rule correction coverage_subset adjudication
automatic_decision automatic_equivalence_premise original original_prompt_sha256
original_output_sha256 original_decision_classification classification automated_status
reference_status automated_scores reference_scores score_differences automated reference
automated_minus_reference reference_uncertainty reference_uncertain automated_pending
reference_pending automated_dependencies reference_dependencies invalid root_count
correct_root_count root_groups root_numbers matched_student_root_numbers all_root_covered
all_root_total required_root_covered required_root_total all_root_completeness
required_root_completeness key aliases alias results paired raw_verdicts raw_alias_variants
normalized_verdicts snapshot_states chosen raw_verdict normalized_verdict receipts
original_receipt reused reference_label raw_agent_reference xhigh high medium low valid
missing conflicting_verdicts agree discordant distinct_prompts paired_complete
baseline_frozen qualification_blocked summary roles cohorts roles_by_cohort metrics
metrics_without_uncertain_references answers statuses complete_pairs reference_uncertain_answers
paired_answers total_answers missing_automated missing_reference uncertain_reference_answers
excluded_uncertain_pairs changed_answers mean_signed_change_percentage_points
mean_absolute_change_percentage_points maximum_absolute_change_percentage_points notes
invalid_outputs mechanical_root_matches native_root_matches native_ledgers_checked
correctness_percent all_root_completeness_percent required_root_completeness_percent
notes_with_no_teacher_roots notes_with_no_required_teacher_roots
required_root_completeness_nonempty_note_percent correct_roots returned_roots
teacher_root_meanings matched_teacher_root_meanings required_teacher_root_meanings
matched_required_teacher_root_meanings full_hierarchy_correctness_percent
full_hierarchy_completeness_percent valid_empty_root_outputs final_matching_questions
final_coverage_questions manual_reviews records distinct_questions resolved_questions
unresolved_questions affected_occurrences affected_answers original_decision_classifications
correct incorrect uncertain schema_version policy automatic_status analysis_only
semantic_audits_applied corrections_applied adjudication_summary automatic_summary
sha256 snapshot_sha256 frozen_at_utc
teacher_relationships teacher_paths source_case_id current_input_sha256
current_prompt_sha256 retained_student_numbers removed_student_numbers
checks qualification expected_scores expected_score_basis scoring_basis
expected_teacher_number expected_teacher_id expected_valid actual_valid expected_reason
expectation_status expected_score_error score_evidence assembled_review
score_comparisons score_mismatches random challenge complete partial failed unrun empty
invalid_output output_failure inconsistent_verdicts skipped mechanical checked total
mechanical_failures incorrect_verdicts expected_match actual_match incorrect_matches
pending_cases unverified_agreements unverified_disagreements score_errors
'''.split())


def _hash(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def _stamp(path):
    value = Path(path).stat()
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _read(path):
    path = Path(path)
    if path.stat().st_size > _READ_LIMIT:
        raise ValueError('evaluation per-note or metadata file exceeds bounded read limit')
    return json.loads(path.read_bytes())


def _items(path, prefix):
    import ijson
    with _open_json(path) as source:
        yield from ijson.items(source, prefix, use_float=True)


def _open_json(path):
    path = Path(path)
    return gzip.open(path, 'rb') if path.suffix == '.gz' else path.open('rb')


def _project(path, fields):
    from experiment_runner.json_projection import project
    with _open_json(path) as source:
        return project(source, fields)


_QUALIFICATION_FIELDS = {
    'basis', 'status', 'checked', 'incorrect_cases', 'unresolved', 'skipped_cases',
    'score_differences', 'passed', 'expected_valid', 'actual_valid', 'expected_match',
    'actual_match', 'expected_teacher_id', 'actual_teacher_id',
    'error',
}
_SUMMARY_FIELDS = {'occurrences', 'semantic', 'distinct_semantic_inputs',
    'incorrect_cases', 'unresolved', 'versions', 'unmatched_subjects'}
_MEASUREMENTS = {
    'notes', 'subjects', 'valid_masks', 'empty_masks', 'subject_failures', 'mask_failures',
    'predicted_nonempty', 'reference_nonempty', 'matches_80', 'exact_matches',
    'precision_80', 'recall_80', 'f1_80', 'returned_subjects',
}


def _counts(value):
    """Status/effort counters have dynamic labels and numeric leaves."""
    if isinstance(value, dict):
        return {key: _counts(item) for key, item in value.items()
                if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', key)
                and (isinstance(item, dict) or type(item) in (int, float, bool))}
    return value


def _clean(value, field=None, *, summary=False):
    """Project data by its saved result field, keeping measured maps intact."""
    summary = summary or field == 'summary'
    if isinstance(value, dict):
        if field in ('statuses', 'snapshot_states'):
            return _counts(value)
        if field == 'raw_agent_reference':
            return {effort: _clean(item, 'reference_measurements') for effort, item in value.items()
                    if effort in ('xhigh', 'high', 'medium', 'low')}
        if field in ('versions', 'roles', 'roles_by_cohort'):
            return {key: _clean(item, 'summary', summary=True) for key, item in value.items()
                    if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', key)}
        if field == 'score_differences':
            return {metric: {key: _clean(item, key) for key, item in comparison.items()
                    if key in ('actual', 'expected', 'automated', 'reference', 'automated_minus_reference')}
                    for metric, comparison in value.items()
                    if metric in ('correctness', 'coverage') and isinstance(comparison, dict)}
        fields = ({'status', 'resolved_occurrences', 'unresolved_occurrences', 'labels',
                   'agrees_reference', 'disagrees_reference', 'unresolved_reference'}
                    if field == 'reference_measurements' else
                  _QUALIFICATION_FIELDS if field == 'qualification' else
                  {'actor', 'role', 'verdict', 'comment', 'time', 'input_sha256',
                   'output_sha256', 'current', 'reason', 'check', 'prompt_sha256'}
                    if field in ('reviews', 'audits', 'assessment') else
                  {'valid', 'teacher_id', 'reason'} if field == 'parsed' else
                  _FIELDS | _SUMMARY_FIELDS if summary else _FIELDS)
        # Native findings/checked judgments have distinct, established schemas.
        if field == 'findings':
            fields = fields | {'unmatched_subjects'}
        if field == 'checks' and not summary:
            return {check: [_native_check(case) for case in cases]
                    for check, cases in value.items()
                    if check in ('matching', 'support', 'relationship', 'coverage_search')}
        elif field == 'checks':
            fields = {'matching', 'support', 'relationship', 'coverage_search'}
        else:
            fields = fields | {'parsed'}
        return {key: _clean(item, key, summary=summary) for key, item in value.items() if key in fields}
    if isinstance(value, list):
        return [_clean(item, field, summary=summary) for item in value]
    return value


def _native_check(case):
    """Native execution errors contain provider diagnostics, not research judgments."""
    fields = (_FIELDS | {'parsed'}) - {'error'}
    result = {key: _clean(item, key) for key, item in case.items() if key in fields}
    if case.get('failure_kind') in ('local', 'unknown', 'provider_fatal', 'provider_transient'):
        result['failure_kind'] = case['failure_kind']
    return result


def _metadata(path, kind, execution_status):
    return dict(schema_version=1, format=kind + '-publication-v1',
        source_id=hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest(),
        experiment_id=Path(path).name, execution_status=execution_status or 'not_recorded',
        exporter=dict(sha256=_hash(Path(__file__))))


def _write(output, metadata, payloads, source):
    from experiment_runner.publication_files import write_publication
    original, destination = Path(source).resolve(), Path(output).resolve()
    if original.is_relative_to(destination) or original.is_dir() and destination.is_relative_to(original):
        raise ValueError('publication destination would contain its source evidence')
    return write_publication(output, metadata, payloads)


def _retain_status(metadata, output, supplied):
    previous = Path(output) / 'experiment.json'
    if supplied is None and previous.is_file():
        prior = _read(previous)
        if (prior.get('source_id') == metadata['source_id']
                and prior.get('source', {}).get('report_sha256') == metadata['source']['report_sha256']):
            metadata['execution_status'] = prior.get('execution_status', 'not_recorded')


@contextmanager
def _snapshot(directory):
    """Use an existing run lock without creating historical evidence."""
    lock = Path(directory) / '.lock'
    if not lock.is_file():
        yield
        return
    with lock.open('rb') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('evaluation execution is active; export after it stops') from error
        yield


def _run_directory(stage):
    return stage.parent.parent if stage.parent.name == 'evaluations' else stage.parent


def _partial_rows(directory, note_ids, config):
    for note in sorted(directory.glob('note-*')):
        if not re.fullmatch(r'note-\d+', note.name) or not (note / 'subjects.json').is_file():
            continue
        index = int(note.name[5:])
        saved = _read(note / 'subjects.json')
        identifier = saved.get('note_id') or (note_ids[index] if index < len(note_ids) else None)
        parsed = note / 'subjects-result.json'
        if parsed.is_file():
            result = _read(parsed)
        else:
            from .distillation_run import subject_result
            limit = config.get('max_subjects') if 'mask' in config.get('evaluation_tasks', ['subjects', 'mask']) else None
            result = subject_result(identifier, saved['answer'], limit)
        yield dict(result, masks=[], _saved_index=index)


def _settings(config):
    result = {}
    for key, value in config.items():
        if key not in _SETTINGS:
            continue
        if key == 'model' and isinstance(value, str) and (value.startswith(('/', './', '../', '~'))):
            result['model_source'] = 'local model; original location omitted'
        elif isinstance(value, dict):
            result[key] = {k: v for k, v in value.items() if k in _NESTED_SETTINGS
                           and (v is None or type(v) in (str, bool, int, float))}
        elif value is None or type(value) in (str, bool, int, float):
            result[key] = value
        elif isinstance(value, list) and all(type(v) in (str, bool, int, float) for v in value):
            result[key] = value
    return result


def export_evaluation(directory, output=None, *, results=None, config=None, note_ids=None,
                      execution_status=None, failure_type=None):
    """Export one validation stage; evaluate callers already hold the run lock."""
    directory = Path(directory).resolve()
    if directory.parent.name == 'test' or directory.name == 'test':
        raise ValueError('sealed test answers are excluded from evaluation publication')
    run = _run_directory(directory)
    manifest_path = run / 'manifest.json'
    manifest = _read(manifest_path) if manifest_path.is_file() else {}
    config = manifest.get('config', {}) if config is None else config
    note_ids = manifest.get('dataset', {}).get('evaluation_note_ids', []) if note_ids is None else note_ids
    output = Path(output) if output is not None else run / 'publication/evaluations' / directory.name
    metadata = _metadata(directory, 'evaluation', execution_status)
    metadata.update(stage=directory.name, split='evaluation', parameters=_settings(config),
        input=dict(note_ids=note_ids),
        code={key: value for key, value in manifest.get('code', {}).items()
              if key in _CODE or key.startswith('experiment_runner/') and Path(key).name in _CODE},
        source=dict(manifest_sha256=_hash(manifest_path) if manifest else None),
        status='complete' if (directory / 'complete.json').is_file() else 'partial')
    metadata['input']['prepared_files'] = {
        name: checksum for name, checksum in manifest.get('dataset', {}).get('outputs', {}).items()
        if name in ('train.jsonl', 'evaluation.jsonl', 'references.jsonl', 'test.jsonl')}
    tasks = manifest.get('dataset', {}).get('tasks', {})
    metadata['input']['prompt_versions'] = {key: tasks[key] for key in ('subjects', 'mask') if key in tasks}
    version = tasks.get('subjects')
    parsed = re.fullmatch(r'ASv(\d+)(?:\.(\d+))?', version) if isinstance(version, str) else None
    metadata['input']['deprecated'] = (int(parsed[1]), int(parsed[2] or 0)) < (6, 100) if parsed else None
    if isinstance(config.get('continuation'), dict):
        metadata['parameters']['continuation'] = {key: value for key, value in config['continuation'].items()
            if key in ('manifest_sha256', 'plan_sha256', 'checkpoint_sha256')}
    previous = output / 'experiment.json'
    if execution_status is None and previous.is_file():
        prior = _read(previous)
        if prior.get('source_id') == metadata['source_id']:
            metadata['execution_status'] = prior.get('execution_status', 'not_recorded')
            if prior.get('failure_type'):
                metadata['failure_type'] = prior['failure_type']
    if failure_type:
        metadata['failure_type'] = failure_type
    if results is None:
        path = directory / 'results.json'
        results = _items(path, 'item') if path.is_file() else _partial_rows(directory, note_ids, config)

    def records():
        selected = []
        for index, result in enumerate(results):
            offset = result.get('_saved_index', index)
            note = directory / f"note-{offset:04}"
            saved = _read(note / 'subjects.json')
            identities = [result.get('note_id'), saved.get('note_id')]
            if note_ids:
                if not 0 <= offset < len(note_ids):
                    raise ValueError('evaluation note identity is outside the frozen selection')
                identities.append(note_ids[offset])
            if len({value for value in identities if value is not None}) > 1:
                raise ValueError('evaluation note identity differs between saved result, answer or selection')
            record = dict(note_id=result.get('note_id'), answer=_clean(saved['answer']),
                          result=_clean(result), source_sha256=_hash(note / 'subjects.json'))
            masks = []
            for path in sorted(note.glob('masks-*.json')):
                if re.fullmatch(r'masks-\d+\.json', path.name):
                    masks.extend(_clean(answer) for answer in _read(path).get('answers', []))
            if masks:
                record['mask_answers'] = masks
            selected.append(record['note_id'])
            yield record
        if not metadata['input']['note_ids']:
            metadata['input']['note_ids'] = selected
        path = directory / 'results.json'
        metadata['source']['results_sha256'] = _hash(path) if path.is_file() else None
        if (run / 'training-plan.json').is_file():
            metadata['source']['training_plan_sha256'] = _hash(run / 'training-plan.json')
        if directory.name.startswith('checkpoint-'):
            checkpoint = run / 'checkpoints' / directory.name
            for name in ('complete.json', 'adapter_config.json'):
                if (checkpoint / name).is_file():
                    metadata['source'][name.replace('.', '_') + '_sha256'] = _hash(checkpoint / name)
        report = run / 'report.json'
        if report.is_file():
            value = _read(report)
            measured = value.get(directory.name)
            if measured is None and directory.name.startswith('checkpoint-'):
                measured = next((row.get('evaluation') for row in value.get('checkpoints', [])
                    if Path(row.get('checkpoint', '')).name == directory.name), None)
            if isinstance(measured, dict):
                metadata['measurements'] = {key: item for key, item in measured.items()
                    if key in _MEASUREMENTS and type(item) in (int, float, bool)}
                metadata['source']['report_sha256'] = _hash(report)

    return _write(output, metadata, {'results.jsonl': records()}, directory)


def export_evaluations(directory, output=None, *, execution_status=None):
    """Export baseline and every saved validation checkpoint, never test/."""
    directory = Path(directory).resolve()
    output = Path(output) if output is not None else directory / 'publication/evaluations'
    stages = [directory / name for name in ('baseline', 'trained') if (directory / name).is_dir()]
    stages.extend(sorted((directory / 'evaluations').glob('checkpoint-*')))
    with _snapshot(directory):
        return dict(evaluations=[export_evaluation(stage, output / stage.name,
            execution_status=execution_status) for stage in stages if stage.is_dir()])


def _source_hashes(source):
    return sorted(set(value for value in source.values() if isinstance(value, str)
                      and re.fullmatch('[0-9a-f]{64}', value)))


def _grade_selection(header, base):
    """Find the exact selected answers without copying their expanded inputs."""
    information = dict(status='not_recorded')
    def bound(reference, base):
        if not isinstance(reference, dict) or not isinstance(reference.get('path'), str):
            return None
        path = Path(reference['path'])
        path = path if path.is_absolute() else base / path
        if not path.is_file():
            return None
        if _hash(path) != reference.get('sha256'):
            raise ValueError('grading selected-answer source changed')
        return path
    selection_ref = header.get('selection')
    if selection_ref is None:
        coverage = header.get('coverage')
        if not isinstance(coverage, str):
            return information, None
        coverage = Path(coverage)
        coverage = coverage if coverage.is_absolute() else base / coverage
        coverage = coverage / 'coverage-search.json'
        if not coverage.is_file():
            return dict(status='missing'), None
        information['coverage_sha256'] = _hash(coverage)
        expected = header.get('sources', {}).get(str(coverage))
        if expected is not None and expected != information['coverage_sha256']:
            raise ValueError('grading coverage preparation changed')
        evaluation_ref = _project(coverage, {'evaluation'}).get('evaluation')
        evaluation = bound(evaluation_ref, coverage.parent)
        if evaluation is None:
            return dict(information, status='missing'), None
        information['evaluation_sha256'] = evaluation_ref['sha256']
        selection_ref = _project(evaluation, {'selection'}).get('selection')
        base = evaluation.parent
    selection = bound(selection_ref, base)
    if selection is None:
        return dict(information, status='missing'), None
    information.update(status='saved', selection_sha256=selection_ref['sha256'])
    selected = _project(selection, {'dataset', 'selection_policy'})
    information['dataset_manifest_sha256'] = selected.get('dataset', {}).get('sha256')
    information['selection_policy'] = {key: value for key, value in selected.get('selection_policy', {}).items()
        if key in ('seed', 'random_count', 'hard_count') and type(value) in (str, int)}
    return information, selection


def _selected_answers(selection, wanted, information):
    remaining = set(wanted)
    if selection is None:
        information['unavailable_answer_ids'] = sorted(remaining)
        return
    for cohort in ('random', 'challenge'):
        for row in _items(selection, cohort + '.answers.item'):
            if row['id'] not in wanted:
                continue
            remaining.discard(row['id'])
            result = {key: row[key] for key in ('id', 'note_id', 'model', 'revision', 'version') if key in row}
            result.update(cohort=cohort, generation_sha256=row.get('generation', {}).get('sha256'),
                task_prompt_sha256=hashlib.sha256(row['task_prompt'].encode()).hexdigest()
                    if isinstance(row.get('task_prompt'), str) else None,
                answer=_clean(row.get('raw_answer', {})))
            yield result
    if _hash(selection) != information['selection_sha256']:
        raise ValueError('grading selected answers changed during export')
    information['unavailable_answer_ids'] = sorted(remaining)


def _digest(value):
    encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256()
    for part in encoder.iterencode(value):
        digest.update(part.encode())
    digest.update(b'\n')
    return digest.hexdigest()


def _answer_rows(report, cohort, result=None):
    return result[cohort]['answers'] if result is not None else _items(report, cohort + '.answers.item')


def _judgment_requests(report, result=None):
    requests = {}
    answers = set()
    assessments = {}
    def include(value):
        if isinstance(value, dict):
            adjudication = value.get('adjudication')
            if isinstance(adjudication, dict) and adjudication.get('path') and adjudication.get('sha256'):
                assessments[Path(adjudication['path'])] = adjudication['sha256']
            receipt = value.get('receipt') or {}
            if isinstance(receipt, dict):
                location, checksum = receipt.get('results_path'), receipt.get('record_sha256')
                if location and checksum:
                    output_hash = value.get('output_sha256')
                    if output_hash is None and isinstance(value.get('output'), str):
                        output_hash = hashlib.sha256(value['output'].encode()).hexdigest()
                    requests.setdefault(Path(location), {}).setdefault(checksum, set()).add(output_hash)
            for key, item in value.items():
                if key not in ('current_inputs', 'inputs', 'messages', 'post', 'teacher', 'student', 'task_prompt'):
                    include(item)
        elif isinstance(value, list):
            for item in value:
                include(item)
    for cohort in ('random', 'challenge'):
        for row in _answer_rows(report, cohort, result):
            answers.add(row['id'])
            include(row)
    return requests, answers, assessments


def _judgments(requests, assessments):
    """One sequential read per distinct ledger; no repeated whole-ledger scans."""
    for path, wanted in requests.items():
        remaining = dict(wanted)
        if path.is_file():
            with path.open('rb') as source:
                while True:
                    raw_line = source.readline(_READ_LIMIT + 1)
                    if not raw_line:
                        break
                    if len(raw_line) > _READ_LIMIT:
                        raise ValueError('native judgment record exceeds bounded read limit')
                    if not raw_line.strip():
                        continue
                    record = json.loads(raw_line)
                    checksum = _digest(record)
                    expected = remaining.pop(checksum, None)
                    if expected is None:
                        continue
                    raw = record.get('final_output_raw', record.get('output'))
                    recorded_hashes = expected - {None}
                    valid = isinstance(raw, str) and recorded_hashes <= {hashlib.sha256(raw.encode()).hexdigest()}
                    result = dict(record_sha256=checksum,
                        evidence_status='saved' if valid else 'mismatch',
                        output_binding='receipt_and_output_hash' if recorded_hashes else 'receipt_only')
                    if valid:
                        result['output'] = raw
                        result.update({key: record[key] for key in (
                            'provider', 'model', 'reasoning_effort', 'prompt_sha256',
                            'request_sha256', 'response_schema_sha256', 'status') if key in record
                            and (record[key] is None or type(record[key]) in (str, int, bool, float))})
                        result['reused'] = record.get('execution') == 'cross_run_reuse'
                    yield result
        for checksum in remaining:
            yield dict(record_sha256=checksum, evidence_status='missing')
    for path, checksum in assessments.items():
        result = dict(source_sha256=checksum, origin='adjudicated', actor='agent', evidence_status='missing')
        if path.is_file():
            if _hash(path) != checksum:
                result['evidence_status'] = 'mismatch'
            else:
                saved = _read(path)
                result.update({key: _clean(saved[key], key) for key in (
                    'actor', 'check', 'decision', 'reason', 'rule', 'original_decision_classification',
                    'original_output_sha256', 'original_prompt_sha256') if key in saved})
                result['evidence_status'] = 'saved'
        yield result


def export_grades(report_path, output=None, *, execution_status=None):
    """Export final/last partial scores and their supporting saved judgments."""
    report_path = Path(report_path).resolve()
    stamp = _stamp(report_path)
    run = report_path.parent.parent if report_path.parent.name == 'collections' else report_path.parent
    automatic = (run / 'automatic.json').is_file()
    output = Path(output) if output is not None else (run if automatic else report_path.parent) / 'publication'
    header = _project(report_path, {'schema_version', 'policy', 'automatic_status', 'analysis_only',
        'semantic_audits_applied', 'corrections_applied', 'adjudication_summary', 'automatic_summary',
        'sources', 'coverage', 'inference_calls'})
    legacy_collection = (header.get('schema_version') == 1
        and isinstance(header.get('coverage'), str) and bool(header['coverage'])
        and isinstance(header.get('sources'), dict)
        and type(header.get('inference_calls')) is int and header['inference_calls'] == 0)
    if 'policy' not in header and not legacy_collection:
        raise ValueError('expected saved final grading report')
    return _export_grading(report_path, output, header, execution_status,
        run if automatic else report_path, 'grading', stamp)


def export_review_evaluation(report_path, output=None, *, result=None, execution_status=None):
    """Export an explicitly saved assembled native grading-method report."""
    report_path = Path(report_path).resolve()
    stamp = _stamp(report_path)
    output = Path(output) if output is not None else report_path.parent / 'publication' / report_path.stem
    fields = {'schema_version', 'selection', 'summary', 'sources',
        'actual_edges_only', 'relationship_configuration'}
    header = ({key: value for key, value in result.items() if key in fields} if result is not None
              else _project(report_path, fields))
    if not isinstance(header.get('selection'), dict) or 'summary' not in header:
        raise ValueError('expected saved assembled native review evaluation')
    if result is not None and _project(report_path, {'selection'}).get('selection') != header['selection']:
        raise ValueError('native review report differs from its frozen selection')
    return _export_grading(report_path, output, header, execution_status,
        report_path, 'review-evaluation', stamp, result=result)


def _export_grading(report_path, output, header, execution_status, identity, kind, stamp, *, result=None):
    metadata = _metadata(identity, kind, execution_status)
    metadata.update(parameters={key: _clean(value, key) for key, value in header.items()
        if key not in ('sources', 'coverage', 'selection', 'relationship_configuration')},
        source=dict(report_sha256=_digest(result) if result is not None else _hash(report_path),
            evidence_sha256=_source_hashes(header.get('sources', {}))),
        evidence='Recorded model judgments, mechanical checks, agent assessments and user decisions remain distinct.')
    _retain_status(metadata, output, execution_status)
    if result is not None:
        metadata['source']['preparation_sha256'] = _hash(report_path)
    metadata['input'], selection = _grade_selection(header, report_path.parent)
    requests, answer_ids, assessments = _judgment_requests(report_path, result)

    def records():
        for cohort in ('random', 'challenge'):
            for row in _answer_rows(report_path, cohort, result):
                yield {**_clean(row), 'cohort': cohort}
        if _stamp(report_path) != stamp:
            raise ValueError('saved grading report changed during export')

    return _write(output, metadata, {'results.jsonl': records(), 'judgments.jsonl': _judgments(requests, assessments),
        'answers.jsonl': _selected_answers(selection, answer_ids, metadata['input'])}, report_path)


def _l1_records(source, models):
    import ijson
    version, capture, depth = None, None, 0
    with _open_json(source) as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if capture is not None:
                field, builder = capture
                builder.event(event, value)
                depth += int(event in ('start_map', 'start_array')) - int(event in ('end_map', 'end_array'))
                if depth == 0:
                    if field == 'stats':
                        models[version]['stats'] = _clean(builder.value)
                    else:
                        yield {**_clean(builder.value), 'version': version}
                    capture = None
            elif prefix == 'results' and event == 'map_key':
                version = value
                models[version] = {}
            elif version is not None:
                base = 'results.' + version + '.'
                if prefix in (base + 'model', base + 'version') and event == 'string':
                    models[version][prefix[len(base):]] = value
                elif prefix in (base + 'stats', base + 'notes.item') and event == 'start_map':
                    capture = ('stats' if prefix == base + 'stats' else 'note', ijson.ObjectBuilder())
                    capture[1].event(event, value)
                    depth = 1


def export_comparison(source, output=None, *, result=None, execution_status=None):
    """Native paired grades, historical L1 measurements or final effort analysis."""
    source = Path(source).resolve()
    stamp = _stamp(source)
    output = Path(output) if output is not None else source.parent / 'publication' / source.stem
    header_fields = {'schema_version', 'scope', 'aggregation', 'correctness', 'completeness',
        'qualification', 'score_units', 'reference_basis', 'inference_calls', 'stage',
        'summary', 'basis', 'panel', 'baseline_freeze', 'sources', 'random', 'challenge'}
    header = {key: value for key, value in result.items() if key in header_fields} if result is not None else _project(source, header_fields)
    metadata = _metadata(source, 'evaluation-comparison', execution_status)
    metadata.update(parameters={key: _clean(value, key, summary=key in ('random', 'challenge'))
        for key, value in header.items() if key != 'sources'},
        source=dict(report_sha256=_hash(source), evidence_sha256=_source_hashes(header.get('sources', {}))))
    _retain_status(metadata, output, execution_status)

    def records():
        if 'scope' in header:
            metadata['models'] = {}
            if result is None:
                yield from _l1_records(source, metadata['models'])
            else:
                for version, cell in result.get('results', {}).items():
                    metadata['models'][version] = dict(model=cell.get('model'), version=cell.get('version'),
                        stats=_clean(cell.get('stats', {})))
                    for row in cell.get('notes', []):
                        yield {**_clean(row), 'version': version}
        elif 'stage' in header and 'summary' in header:
            rows = result.get('rows', []) if result is not None else _items(source, 'rows.item')
            yield from (_clean(row) for row in rows)
        elif 'qualification' in header:
            for cohort in ('random', 'challenge'):
                rows = (result.get('paired_answers', {}).get(cohort, []) if result is not None
                        else _items(source, 'paired_answers.' + cohort + '.item'))
                yield from ({**_clean(row), 'cohort': cohort} for row in rows)
        else:
            raise ValueError('unrecognized final evaluation comparison format; snapshots are excluded')
        if _stamp(source) != stamp:
            raise ValueError('saved comparison changed during export')

    return _write(output, metadata, {'results.jsonl': records()}, source)
