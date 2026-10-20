"""Source-bound final answers and recorded reviews for legacy atomic studies."""
import json
from pathlib import Path
import re

from ._runner_bootstrap import shared
from .historical_study_publication import _canonical
from .prompt_study_publication import _json, _sha


_PLAN = set('''schema_version question comparison notes trials_per_note_and_prompt
planned_calls hypothesis primary_targets open_interpretation_cases retention_controls
unchanged judgments guidance baseline_version baseline_policy new_version
planned_new_calls note_order trials model reasoning_effort sequential max_attempts
no_retries_or_repairs no_generation_output_edits checks interpretation_rules limitations
note_count calls_per_note_per_version versions execution_order no_output_edits
calls_per_note baseline_rerun prompt_normalization max_attempts_per_note retries output_edits
same_prompts_model_input_schema_and_normalization planned_successful_outputs'''.split())
_PLAN.update('''review execution source_commit status status_at_creation runs outputs
approved_by_user user_authorization prompt_file_sha256 runtime'''.split())
_PLAN_REFERENCES = set('''prompt_path input_path selection_path baseline_run_directories
input prompt_source saved_baseline subject_registry prompt_sources'''.split())
_RUNTIME = {'model', 'reasoning_effort', 'sequential', 'max_attempts', 'no_retry',
            'no_retries', 'max_new_jobs_per_batch'}
_RUNTIME_OPERATIONAL = set('''memory_max_bytes swap_max_bytes runtime_max_seconds_per_batch
paid_api_or_rental launcher_memory_max_bytes launcher_swap_max_bytes
launcher_runtime_max_seconds_per_trial launcher_runtime_max_seconds_per_version
launcher_runtime_max_seconds_per_batch cap_scope host_checks budget_ledger
resource_checks pressure_check budget'''.split())
_ANALYSIS = set('''schema_version status user_approvals_recorded conclusion counts
notes limits unchanged_decisions basis prompts_unchanged frozen_default conclusions
reviewer scope baseline_subjects candidate_subjects human_decisions_added focus items'''.split())
_PRIVATE = {'account', 'codex_home', 'codex_binary', 'runtime', 'argv', 'stderr',
            'stdout', 'stdout_jsonl', 'thread_id', 'auth_file', 'credentials',
            'authentication_check', 'command', 'review_command', 'ui_command'}


def _scientific(value, omitted=None, prefix=''):
    if isinstance(value, list):
        return [_scientific(item, omitted, prefix + '[]') for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            field = prefix + '.' + key if prefix else key
            if key in _PRIVATE or key.endswith(('_path', '_directory')):
                if omitted is not None:
                    omitted.append(field)
            else:
                result[key] = _scientific(item, omitted, field)
        return result
    return value


def _portable_references(value):
    if isinstance(value, dict):
        return {key: _portable_references(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable_references(item) for item in value]
    if (not isinstance(value, str) or not value or value.startswith('/')
            or '\\' in value or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', value)):
        raise ValueError('atomic plan source references must be portable relative paths/hashes')
    return value


def _plan(native):
    if not isinstance(native, dict):
        raise ValueError('atomic plan must be a JSON object')
    unknown = set(native) - _PLAN - _PLAN_REFERENCES - _PRIVATE
    if unknown:
        raise ValueError('unsupported atomic plan fields: ' + ', '.join(sorted(unknown)))
    selected, omitted = {}, []
    for key, value in native.items():
        if key in _PLAN_REFERENCES:
            selected[key] = _portable_references(value)
        elif key == 'runtime':
            if not isinstance(value, dict) or set(value) - _RUNTIME - _RUNTIME_OPERATIONAL - _PRIVATE:
                raise ValueError('unsupported atomic plan runtime fields')
            selected[key] = {name: item for name, item in value.items() if name in _RUNTIME}
            omitted.extend('runtime.' + name for name in value if name not in _RUNTIME)
        elif key in _PRIVATE:
            omitted.append(key)
        else:
            selected[key] = _scientific(value, omitted, key)
    return selected, omitted


def _unique(rows, label):
    if not isinstance(rows, list):
        raise ValueError('invalid atomic ' + label)
    result = {}
    for row in rows:
        key = row.get('note_id') if isinstance(row, dict) else None
        if not isinstance(key, str) or not key or key in result:
            raise ValueError('ambiguous atomic ' + label + ' identity')
        result[key] = row
    return result


def _relative(source, value):
    if not isinstance(value, str) or Path(value).is_absolute():
        raise ValueError('atomic config needs a relative input/registry binding')
    # Old configs use ../ for shared frozen inputs; normalize, then require a declared source.
    parts = []
    for part in (Path(source).parent / value).parts:
        if part == '..':
            if not parts:
                raise ValueError('atomic config path escapes source root')
            parts.pop()
        elif part != '.':
            parts.append(part)
    return '/'.join(parts)


def _session_decisions(sources, binding, run, input_rows, output_rows):
    saved = sources.read(binding['path'])
    session = saved.get('session')
    if not isinstance(session, dict) or saved.get('schema_version') != 1:
        raise ValueError('invalid atomic user review state')
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    if _sha(compact(session)) != saved.get('state_sha256'):
        raise ValueError('atomic user review state hash mismatch')
    identity = dict(review_protocol='atomic-subject-review-v1',
                    manifest_sha256=sources.hashes[run['manifest']],
                    input_sha256=sources.hashes[run['input']],
                    results_sha256=sources.hashes[run['receipt']],
                    output_sha256=sources.hashes[run['output']])
    generation = _sha(compact(identity))
    if (session.get('review_protocol') != 'atomic-subject-review-v2'
            or session.get('generation_run_sha256') != generation):
        raise ValueError('atomic user review is bound to a different generation')
    notes = session.get('notes')
    if not isinstance(notes, list) or [n.get('note_id') for n in notes] != list(output_rows):
        raise ValueError('atomic user review note identities mismatch')
    judgments = []
    for note in notes:
        note_id = note['note_id']
        subjects = output_rows[note_id]['subjects']
        text = input_rows[note_id]['text']
        expected = _sha(compact([generation, 'subject_list', note_id, text,
                                [item['text'] for item in subjects]]))
        if (note.get('list_item_id') != 'subject-list:' + note_id
                or note.get('list_item_sha256') != expected
                or len(note.get('subjects', [])) != len(subjects)):
            raise ValueError('atomic user review subject-list binding mismatch')
        for index, (item, subject) in enumerate(zip(note['subjects'], subjects)):
            expected = _sha(compact([generation, 'subject', note_id, text, index, subject['text']]))
            if (item.get('item_id') != 'subject:' + note_id + ':' + str(index)
                    or item.get('item_sha256') != expected):
                raise ValueError('atomic user review subject binding mismatch')
            if item.get('outcome') not in (None, 'accepted', 'rejected'):
                raise ValueError('invalid atomic user review outcome')
            if item.get('outcome') is not None or item.get('comment'):
                judgments.append(dict(kind='subject_review', actor='user',
                    attribution_basis='source-bound atomic-subject-review-v2 state',
                    run_id=run['output'], note_id=note_id, source_index=index,
                    verdict=item.get('outcome'), comment=item.get('comment', ''),
                    item_sha256=expected, source=binding['path']))
        for field in ('coverage', 'distinctness'):
            if note.get(field) is not None or note.get(field + '_comment'):
                judgments.append(dict(kind=field + '_review', actor='user',
                    attribution_basis='source-bound atomic-subject-review-v2 state',
                    run_id=run['output'], note_id=note_id, verdict=note.get(field),
                    comment=note.get(field + '_comment', ''), source=binding['path']))
    return judgments


def prepare(sources, selection, metadata):
    runs = selection.get('runs')
    if not isinstance(runs, list) or not runs:
        raise ValueError('atomic study requires selected final runs')
    engine = shared('extraction_pipeline')
    metadata['exporter_sources']['experiment_runner/extraction_pipeline.py'] = _sha(
        Path(engine.__file__).read_bytes())
    metadata.update(deprecation=dict(status='deprecated_historical_evidence',
        reason='Subject prompt versions precede ASv6.100; raw source posts are not deprecated'),
        binding_limitations=[], prompts={}, settings=[], dependencies=selection.get('dependencies', []))
    inputs, answers, judgments, results = {}, [], [], []
    seen_runs, execution_threads = set(), set()
    for run in runs:
        if not isinstance(run, dict) or not all(isinstance(run.get(key), str)
                for key in ('output', 'manifest', 'input', 'registry')):
            raise ValueError('invalid selected atomic run')
        output_path = run['output']
        if output_path in seen_runs:
            raise ValueError('duplicate atomic final run')
        seen_runs.add(output_path)
        output = sources.read(output_path)
        manifest = sources.read(run['manifest'])
        native_input = sources.read(run['input'])
        if not all(isinstance(value, dict) for value in (output, manifest, native_input)):
            raise ValueError('atomic final sources must be JSON objects')
        input_rows = _unique(native_input.get('notes'), 'input note')
        output_rows = _unique(output.get('notes'), 'output note')
        subject = manifest.get('subject', {})
        version, prompt = subject.get('prompt_version'), subject.get('prompt')
        registry = sources.read(run['registry'])
        if (not isinstance(registry, dict) or manifest.get('schema_version') != 1
                or output.get('schema_version') != 1 or manifest.get('mode') != 'atomic_subject_generation'
                or output.get('manifest_sha256') != sources.hashes[run['manifest']]
                or manifest.get('input_sha256') != sources.hashes[run['input']]
                or not isinstance(prompt, str) or registry.get(version) != prompt
                or subject.get('prompt_registry_sha256') != sources.hashes[run['registry']]
                or subject.get('prompt_sha256') != _sha(prompt.encode())
                or subject.get('response_schema_sha256') != _sha(
                    engine._canonical_json_bytes(subject.get('response_schema')))
                or list(input_rows) != list(output_rows)):
            raise ValueError('atomic frozen manifest/input/prompt binding mismatch')
        if (manifest.get('subject_envelope_version') != 'xml-post-v1'
                or manifest.get('subject_input_normalization_version')
                != 'remove-long-ascii-nip19-identifiers-v2'):
            raise ValueError('unsupported saved atomic request rendering')
        if 'config' in run:
            config = sources.read(run['config'])
            configured = config.get('subject', {})
            if (any(configured.get(key) != subject.get(key) for key in
                    ('prompt_version', 'model', 'reasoning_effort'))
                    or _relative(run['config'], config.get('input_path')) != run['input']
                    or _relative(run['config'], configured.get('prompt_registry_path')) != run['registry']):
                raise ValueError('atomic config binding mismatch')
        receipts = {}
        if run.get('receipt'):
            for line in sources.raw(run['receipt']).splitlines():
                if not line.strip():
                    continue
                row = _json(line)
                if (not isinstance(row, dict) or row.get('stage') != 'subject'
                        or row.get('note_id') not in input_rows):
                    raise ValueError('orphaned atomic receipt')
                if row.get('status') != 'succeeded':
                    continue
                if row['note_id'] in receipts:
                    raise ValueError('ambiguous atomic successful receipt')
                receipts[row['note_id']] = row
            if set(receipts) != set(output_rows):
                raise ValueError('missing atomic final receipt')
        else:
            metadata['binding_limitations'].append(dict(run_id=output_path,
                limitation='Raw receipts unavailable; preserved original parsed final subjects only'))
        settings = {key: subject.get(key) for key in ('model', 'reasoning_effort', 'response_schema_sha256')}
        settings.update({key: manifest.get(key) for key in ('wrapper_sha256', 'codex_version',
            'subject_envelope_version', 'subject_input_normalization_version')})
        settings_id = _sha(_canonical(settings))
        if not any(item['id'] == settings_id for item in metadata['settings']):
            metadata['settings'].append(dict(id=settings_id, **settings))
        if version in metadata['prompts'] and metadata['prompts'][version]['text'] != prompt:
            raise ValueError('conflicting atomic prompt version')
        metadata['prompts'][version] = dict(text=prompt, sha256=subject['prompt_sha256'])
        for note_id, out in output_rows.items():
            original = input_rows[note_id]
            subjects = out.get('subjects')
            if (out.get('text') != original.get('text') or not isinstance(subjects, list)
                    or any(not isinstance(item, dict) or item.get('source_index') != index
                           or not isinstance(item.get('text'), str)
                           for index, item in enumerate(subjects))):
                raise ValueError('atomic parsed output/input binding mismatch')
            data = dict(note_id=note_id, text=original['text'])
            if note_id in inputs and inputs[note_id] != data:
                raise ValueError('atomic input note ID has conflicting text')
            inputs[note_id] = data
            answer = dict(run_id=output_path, note_id=note_id, prompt_version=version,
                trial=run.get('trial'), settings_id=settings_id, subject_count=len(subjects),
                independent_trial=None)
            receipt = receipts.get(note_id)
            if receipt:
                raw = receipt.get('final_output_raw')
                request = engine._render_subject_prompt(prompt, engine.Note(note_id, original['text']))
                if (not isinstance(raw, str) or _sha(raw.encode()) != receipt.get('final_output_sha256')
                        or _json(raw) != {'subjects': [item['text'] for item in subjects]}
                        or receipt.get('response') != [item['text'] for item in subjects]
                        or receipt.get('manifest_sha256') != sources.hashes[run['manifest']]
                        or receipt.get('prompt_sha256') != _sha(request.encode())
                        or any(receipt.get(key) != subject.get(key) for key in
                               ('model', 'reasoning_effort', 'response_schema_sha256'))
                        or receipt.get('wrapper_sha256') != manifest.get('wrapper_sha256')):
                    raise ValueError('atomic raw answer/request binding mismatch')
                answer.update(output=raw, output_sha256=receipt['final_output_sha256'],
                    representation='raw_response', attempt=receipt.get('attempt'),
                    usage={key: value for key, value in receipt.get('usage', {}).items()
                           if key in ('input_tokens', 'output_tokens', 'total_tokens',
                                      'cached_input_tokens', 'cache_write_input_tokens',
                                      'reasoning_output_tokens')})
                thread = receipt.get('thread_id')
                if thread is not None:
                    if not isinstance(thread, str) or not thread or thread in execution_threads:
                        raise ValueError('atomic trials reuse an execution identity')
                    execution_threads.add(thread)
                    answer['independent_trial'] = True
                    answer['independence_basis'] = 'distinct saved execution thread; identity withheld'
            else:
                answer.update(subjects=subjects, representation='original_parsed_subjects')
            answers.append(answer)
        if run.get('user_review'):
            judgments.extend(_session_decisions(sources, run['user_review'], run, input_rows, output_rows))
    metadata['input_selection'] = []
    for binding in selection.get('input_selections', []):
        native = sources.read(binding['path'])
        for row in native.get('notes', []):
            note_id = row.get('note_id')
            if note_id not in inputs:
                raise ValueError('orphaned atomic input selection')
            if ('text' in row and row['text'] != inputs[note_id]['text']
                    or 'text_sha256' in row and row['text_sha256']
                    != _sha(inputs[note_id]['text'].encode())):
                raise ValueError('atomic selection/input text mismatch')
            inputs[note_id].update({key: row[key] for key in
                ('key', 'label', 'role', 'source_row_1based', 'previous_item_id', 'previous_subject')
                if key in row})
        metadata['input_selection'].append(dict(source=binding['path'], values={
            key: native[key] for key in ('selection_rule', 'source_sha256', 'source_note_count',
                'source_excluded_count', 'eligible_count', 'frozen_at_utc') if key in native}))
    metadata['parameters'] = []
    for binding in selection.get('parameters', []):
        native = sources.read(binding['path'])
        values, omitted = _plan(native)
        parameters = dict(source=binding['path'], values=values)
        if 'approved_by_user' in values or 'user_authorization' in values:
            parameters['authorization_scope'] = 'Recorded task execution authorization, not result approval'
        metadata['parameters'].append(parameters)
        if omitted:
            metadata.setdefault('omitted_operational_fields', []).append(dict(
                source=binding['path'], fields=omitted))
    for binding in selection.get('records', []):
        native = sources.read(binding['path'])
        unknown = set(native) - _ANALYSIS - _PRIVATE
        if unknown:
            raise ValueError('unsupported atomic final-assessment fields: ' + ', '.join(sorted(unknown)))
        omitted = []
        cleaned = _scientific(native, omitted)
        if omitted:
            metadata.setdefault('omitted_operational_fields', []).append(dict(
                source=binding['path'], fields=omitted))
        selected = {key: value for key, value in cleaned.items() if key in _ANALYSIS}
        explicit = next((key for key in ('reviewer', 'status', 'basis')
            if isinstance(native.get(key), str)
            and re.search(r'\bassistant\b|\bagent\b|assistant_analysis', native[key], re.I)), None)
        judgments.append(dict(kind=binding.get('role', 'assistant_assessment'),
            actor='agent' if explicit else 'unknown',
            attribution_basis=('saved artifact ' + explicit if explicit
                else 'Saved review artifact does not explicitly identify the actor role'),
            source=binding['path'], answer_runs=sorted(seen_runs), assessment=selected))
    results.append(dict(kind='record_counts', input_notes=len(inputs), new_answers=len(answers),
                        runs=len(runs), user_decisions=sum(j.get('actor') == 'user' for j in judgments)))
    return {'inputs.jsonl': inputs.values(), 'answers.jsonl': answers,
            'judgments.jsonl': judgments, 'results.jsonl': results}
