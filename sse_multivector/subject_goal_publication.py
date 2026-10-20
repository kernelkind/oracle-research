"""Publish saved subject-prompt answers and their recorded scientific reviews.

The selection names immutable source files.  Transport wrappers are read only to
verify bindings and recover exact final answers; they are never publication rows.
"""
import hashlib
import json
from pathlib import Path
import posixpath
import re

from ._runner_bootstrap import shared


_PRIVATE = set('''auth auth_file authentication api_key access_token refresh_token
authorization_header credentials password account account_id codex_home codex_binary
argv stderr stderr_sha256 stdout stdout_jsonl stdout_sha256 thread_id session_id
environment env imported_from source_root working_directory config_path command
review_command ui_command authentication_check'''.split())
_WORKING = {'excluded_note_ids', 'exclusion_files'}
_LOCAL = re.compile(r'(?<![:\w])/(?:home|tmp|mnt|nix|root|run|private|opt|var)/[^\s\"\'<>),;`]*')
_SETTINGS = {'model', 'provider', 'reasoning_effort', 'max_output_tokens',
             'subject_envelope_version', 'subject_input_normalization_version',
             'wrapper_sha256', 'response_schema_sha256'}
_CONTEXT = {
    'execution': set('''admission all_outputs_schema_valid application_instructions
application_system_instructions automatic_retries baseline_calls batches
batch_timeout_seconds cache_reuse cached_input_tokens calls calls_per_batch concurrency_max conversation_history
effort elapsed_first_admission_to_observed_completion_seconds enumerated_subjects
enumerated_subjects_retained_verbatim fresh_calls fresh_context_per_call fresh_isolated_process
fresh_process_per_call generated_outputs_modified generated_subjects_modified hierarchy_entries
history http_attempts_per_call input_tokens isolation mask_calls max_concurrency max_concurrent_calls
maximum_poll_gap_seconds memory_max_per_call memory_max_per_call_gib memory_swap_max
min_available_gib model model_tools no_automatic_retries one_user_message ordering output_keys output_tokens
provider reasoning reasoning_effort reasoning_tokens_included_in_output request_timeout_seconds
requested_model resource_caveat resource_sample_seconds runner_sha256
runtime_max_per_batch_seconds scheduler_sha256 structurally_valid structurally_valid_responses
subject_count subjects successful_calls swap_max_per_call timeout_seconds_per_call
tools total_tokens total_tokens_new_calls unique_threads unique_workdirs
usage usage_caveat user_messages_per_call valid_responses waves'''.split()),
    'runtime': set('''includes maximum_io_psi maximum_memory_psi minimum_available_gib
resource_samples seconds'''.split()),
    'billing': {'additional_paid_api_spend_cents'},
    'accounting': {'route', 'additional_paid_api_spend'},
    'source_binding': set('''path sha256 source_sha256 prompt_sha256 input_sha256
output_sha256 manifest_sha256 note_id case_id trial version prompt_id label text'''.split()),
    'resources': set('''batch_timeout_seconds concurrency limit_caveat max_concurrency
max_concurrent_calls memory_max_per_call_gib new_paid_api_or_rental no_new_paid_api_or_rental
no_retries request_timeout_seconds swap_max_per_call'''.split())}


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _clean(value, key=None):
    """Keep native scientific maps, excluding named transport/account fields.

    Arbitrary subject/version/rubric keys are data, rather than a field whitelist.
    Repository references lose the host prefix; other local paths are omitted.
    """
    if isinstance(value, dict):
        result = {}
        for name, item in value.items():
            if (name.lower() in _PRIVATE or name in _WORKING
                    or (key in _CONTEXT and name not in _CONTEXT[key])
                    or (name == 'error' and key in {'execution', 'failed_call', 'failures'})):
                continue
            if key in {'billing', 'accounting'}:
                valid = (isinstance(item, str) and item in {'subscription', 'api', 'paid_api', 'openrouter'}
                         if name == 'route' else type(item) in (int, float) and item >= 0)
                if not valid:
                    raise ValueError(key + ' requires a scientific route or numeric experiment cost')
            if key == 'source_binding' and item is not None and type(item) not in (str, int, float, bool):
                raise ValueError('source binding values must be scalars')
            if name == 'eligible_notes' and (type(item) is not int or item < 0):
                continue
            if key == 'execution':
                if name in {'unique_threads', 'unique_workdirs'} and (
                        type(item) is not int or item < 0):
                    continue
                if name in {'tools', 'model_tools', 'conversation_history', 'history',
                            'one_user_message'} and not isinstance(item, bool):
                    continue
                if name in {'application_instructions', 'application_system_instructions'} and item != '':
                    continue
                if name in {'isolation', 'admission'} and not isinstance(item, str):
                    continue
                if name in {'batches', 'waves'} and not (
                        (type(item) is int and item >= 0)
                        or (isinstance(item, list) and all(
                            type(size) is int and size >= 0 for size in item))):
                    continue
            portable = _clean(name)
            if portable in result:
                raise ValueError('scientific source references collide after local path removal')
            result[portable] = _clean(item, name)
        return result
    if isinstance(value, list):
        # A source-reference list publishes scientific bindings, never the
        # provider's account-linked response identifiers beside those bindings.
        return [_clean(item, 'source_binding' if key == 'sources' else key) for item in value]
    if isinstance(value, str):
        def reference(match):
            text = match.group()
            marker = '/oracle-mvp/'
            return text.split(marker, 1)[1] if marker in text else '[local path omitted]'
        return _LOCAL.sub(reference, value)
    return value


def _actor(data):
    label = data.get('reviewer') if isinstance(data, dict) else None
    if isinstance(label, str):
        kind = 'assistant' if any(word in label.lower() for word in ('assistant', 'agent')) else 'unknown'
        if label.lower() in {'user', 'human', 'actual user'}:
            kind = 'user'
        return {'kind': kind, 'recorded': _clean(label)}
    return {'kind': 'unknown'}


def _notes(data):
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict) and isinstance(row.get('text'), str)]
    if isinstance(data, dict):
        if isinstance(data.get('text'), str):
            return [data]
        rows = []
        for key in ('notes', 'cases'):
            if key in data:
                rows.extend(_notes(data[key]))
        return rows
    return []


def _raw_case(manifest, case):
    frozen = {row['prompt_id']: row['text'] for row in manifest.get('prompts', [])}
    if len(frozen) != len(manifest.get('prompts', [])):
        raise ValueError('duplicate frozen prompt identity')
    rendered = frozen.get(case)
    if not isinstance(rendered, str) or '<post>' not in rendered or '</post>' not in rendered:
        raise ValueError('saved raw answer lacks a source-post prompt binding')
    before, tail = rendered.rsplit('<post>', 1)
    content, after = tail.split('</post>', 1)
    if not content.startswith('\n') or not content.endswith('\n'):
        raise ValueError('unsupported frozen source-post delimiter')
    return rendered, content[1:-1], {
        'before_post': before + '<post>\n', 'after_post': '\n</post>' + after}


def prepare(sources, selection, metadata):
    """Return compact evidence iterables for the shared atomic publisher."""
    inputs, prompts, answers, reused = {}, {}, [], []
    versions, unknown_lineage = set(selection.get('subject_versions', [])), False
    engine = shared('extraction_pipeline')
    metadata['exporter_sources']['experiment_runner/extraction_pipeline.py'] = _sha(
        Path(engine.__file__).read_bytes())
    catalog = {}
    counts = {'answers': 0, 'raw_answers': 0, 'parsed_only_answers': 0,
              'judgment_records': 0, 'result_records': 0}
    metadata.update(status=selection.get('status', 'historical'),
                    historical=True, counts=counts,
                    limitations=selection.get('limitations', []))
    metadata['selection_basis'] = selection.get('selection_basis', 'Saved final evidence; no inference.')
    if selection.get('correction_record_study'):
        metadata['correction_record_study'] = selection['correction_record_study']
    for binding in selection.get('inputs', []):
        for note in _notes(sources.read(binding['path'])):
            catalog.setdefault(note['text'], []).append((note, binding['sha256']))
            normalized = engine._takeaway_input(note['text'])
            if normalized != note['text']:
                catalog.setdefault(normalized, []).append((note, binding['sha256']))

    def post(text, note=None, source_sha=None):
        identifier = _sha(text.encode())
        row = {'kind': 'post', 'input_id': identifier, 'text': text}
        if note:
            for key in ('note_id', 'source_note_id', 'id', 'origin', 'label', 'check'):
                if key in note:
                    row[key] = note[key]
            if 'origin' not in row and note.get('source_type'):
                row['origin'] = note['source_type']
            if note['text'] != text:
                row['source_text'] = note['text']
        if source_sha:
            row['source_sha256'] = source_sha
        if identifier in inputs:
            old = inputs[identifier]
            if old.get('note_id') and row.get('note_id') and old['note_id'] != row['note_id']:
                # Identical public text can occur in distinct posts; preserve identities.
                identifier += ':' + str(row['note_id'])
                row['input_id'] = identifier
        inputs.setdefault(identifier, row)
        return identifier

    def prompt(value):
        identifier = _sha(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode())
        prompts.setdefault(identifier, {'kind': 'prompt', 'prompt_id': identifier, **value})
        return identifier

    def original(text):
        candidates = catalog.get(text, [])
        canonical = {item[0].get('note_id') for item in candidates if item[0].get('note_id')}
        if len(canonical) > 1:
            raise ValueError('ambiguous saved post identity')
        return candidates[0] if candidates else (None, None)

    for binding in selection.get('answers', []):
        output = sources.read(binding['path'])
        frozen = binding['manifest']
        manifest = sources.read(frozen['path'])
        if output.get('manifest_sha256') != frozen['sha256']:
            raise ValueError('saved answer manifest binding does not match')
        settings = {key: manifest[key] for key in _SETTINGS if key in manifest}
        base = {'run_id': binding['path'], 'source_sha256': binding['sha256'], 'manifest_sha256': frozen['sha256'],
                'settings': settings, 'origin': 'saved_final_answer'}
        if 'notes' in output:
            input_binding = binding.get('input')
            if not input_binding or manifest.get('input_sha256') != input_binding['sha256']:
                raise ValueError('saved answer input hash binding does not match')
            input_rows = {row['note_id']: row for row in _notes(sources.read(input_binding['path']))}
            spec = manifest.get('subject', {})
            if isinstance(spec.get('prompt_version'), str):
                versions.add(spec['prompt_version'])
            else:
                unknown_lineage = True
            body = spec.get('prompt')
            if not isinstance(body, str) or _sha(body.encode()) != spec.get('prompt_sha256'):
                raise ValueError('saved subject prompt hash does not match')
            prompt_id = prompt({key: spec[key] for key in (
                'prompt', 'prompt_version', 'prompt_sha256', 'response_schema',
                'response_schema_sha256') if key in spec})
            settings.update({key: spec[key] for key in _SETTINGS if key in spec})
            receipts = {}
            if binding.get('receipts'):
                receipt_binding = binding['receipts']
                for line in sources.raw(receipt_binding['path']).splitlines():
                    receipt = json.loads(line)
                    if receipt.get('status') == 'succeeded' and receipt.get('manifest_sha256') == frozen['sha256']:
                        receipts.setdefault(receipt.get('note_id'), []).append(receipt)
            for note in output['notes']:
                saved = input_rows.get(note.get('note_id'))
                if saved is None or saved.get('text') != note.get('text'):
                    raise ValueError('saved answer input binding has mismatched note identity/text')
                row = {**base, 'answer_id': binding['sha256'] + ':' + note['note_id'],
                       'case_id': note['note_id'], 'note_id': note['note_id'],
                       'input_id': post(note['text'], saved, input_binding['sha256']),
                       'prompt_id': prompt_id, 'subjects': note['subjects'],
                       'raw_status': 'not_saved_in_selected_source'}
                matches = receipts.get(note['note_id'], [])
                if binding.get('receipts') and not matches:
                    raise ValueError('missing matching saved final answer receipt')
                for receipt in matches:
                    raw = receipt.get('final_output_raw')
                    if not isinstance(raw, str) or _sha(raw.encode()) != receipt.get('final_output_sha256'):
                        raise ValueError('saved final answer raw hash does not match')
                    rendered = engine._render_subject_prompt(body, engine.Note(note['note_id'], note['text']))
                    if receipt.get('prompt_sha256') != _sha(rendered.encode()):
                        raise ValueError('saved final answer rendered prompt binding does not match')
                    parsed = json.loads(raw)
                    if parsed.get('subjects') != [subject['text'] for subject in note['subjects']]:
                        raise ValueError('saved final answer differs from parsed subjects')
                    row.update(raw=raw, raw_sha256=receipt['final_output_sha256'],
                               raw_status='saved', receipt_source_sha256=binding['receipts']['sha256'])
                    if receipt.get('prompt_sha256'):
                        row['rendered_prompt_sha256'] = receipt['prompt_sha256']
                answers.append(row)
        elif 'responses' in output:
            if binding.get('subject_version'):
                versions.add(binding['subject_version'])
            else:
                unknown_lineage = True
            if binding.get('config'):
                config_binding = binding['config']
                config = sources.read(config_binding['path'])
                if (manifest.get('config_sha256') not in (None, config_binding['sha256'])
                        or config.get('prompts') != manifest.get('prompts')):
                    raise ValueError('saved raw answer config binding does not match')
            receipts = {}
            if binding.get('receipts'):
                for line in sources.raw(binding['receipts']['path']).splitlines():
                    if not line.strip():
                        continue
                    receipt = json.loads(line)
                    if receipt.get('status') == 'succeeded':
                        case = receipt.get('note_id')
                        if case in receipts:
                            raise ValueError('ambiguous saved raw answer receipt binding')
                        receipts[case] = receipt
            seen = set()
            for response in output['responses']:
                case = response['prompt_id']
                if case in seen:
                    raise ValueError('duplicate saved answer identity')
                seen.add(case)
                rendered, text, template = _raw_case(manifest, case)
                note, input_sha = original(text)
                prompt_id = prompt(template)
                raw = response['response']
                if not isinstance(raw, str):
                    raise ValueError('saved response is not exact raw text')
                row = {**base, 'answer_id': binding['sha256'] + ':' + case,
                       'case_id': case, 'input_id': post(text, note, input_sha),
                       'prompt_id': prompt_id, 'rendered_prompt_sha256': _sha(rendered.encode()),
                       'raw': raw, 'raw_sha256': _sha(raw.encode()), 'raw_status': 'saved'}
                if binding.get('receipts'):
                    receipt = receipts.get(case, {})
                    if (receipt.get('manifest_sha256') != frozen['sha256']
                            or receipt.get('prompt_sha256') != row['rendered_prompt_sha256']
                            or receipt.get('final_output_raw') != raw
                            or receipt.get('final_output_sha256') != row['raw_sha256']):
                        raise ValueError('saved raw answer receipt binding does not match final answer')
                    row['receipt_source_sha256'] = binding['receipts']['sha256']
                if note and note.get('note_id'):
                    row['note_id'] = note['note_id']
                else:
                    row['note_identity_status'] = 'not_saved_in_selected_input'
                answers.append(row)
        else:
            raise ValueError('unsupported saved subject answer format')
    for binding in selection.get('reused_answers', []):
        output = sources.read(binding['path'])
        manifest = sources.read(binding['manifest']['path'])
        case = binding['case_id']
        if output.get('manifest_sha256') != binding['manifest']['sha256']:
            raise ValueError('reused answer manifest binding does not match')
        rows = [row for row in output.get('responses', []) if row.get('prompt_id') == case]
        if len(rows) != 1 or not isinstance(rows[0].get('response'), str):
            raise ValueError('reused saved answer identity does not match')
        if binding.get('reference_source'):
            source = binding['reference_source']
            ref = sources.read(source['path'])[binding['reference_index']]
            expected_path = posixpath.normpath(posixpath.join(
                posixpath.dirname(source['path']), ref.get('output_path', '')))
            if (expected_path != binding['path'] or ref.get('prompt_id') != case
                    or ref.get('note_id') != binding['note_id']):
                raise ValueError('reused source reference binding does not match')
        _, text, _ = _raw_case(manifest, case)
        note, input_sha = original(text)
        if not note or note.get('note_id') != binding['note_id']:
            raise ValueError('reused saved post identity does not match')
        reused.append({'role': 'reused_answer_reference', 'case_id': case,
                       'note_id': binding['note_id'], 'source_sha256': binding['sha256'],
                       'manifest_sha256': binding['manifest']['sha256'],
                       'raw_sha256': _sha(rows[0]['response'].encode()),
                       'input_id': post(text, note, input_sha),
                       'answer_status': 'reused_saved_answer', 'new_model_call': False})
    counts['answers'] = len(answers)
    counts['raw_answers'] = sum(row['raw_status'] == 'saved' for row in answers)
    counts['parsed_only_answers'] = counts['answers'] - counts['raw_answers']
    if selection.get('expected_answer_records', counts['answers']) != counts['answers']:
        raise ValueError('selected subject final answer count does not match')
    historical = [re.fullmatch(r'ASv6\.(\d+)(?:\.\d+)?(?:-[\w.-]+)?', version) for version in versions]
    known_deprecated = bool(versions) and not unknown_lineage and all(
        match and int(match.group(1)) < 100 for match in historical)
    metadata['subject_provenance'] = {
        'status': 'deprecated' if known_deprecated else 'unknown',
        'recorded_versions': sorted(versions),
        'basis': 'Explicit saved/selected AS versions; unknown lineage remains unknown.',
        'source_posts': 'not deprecated by subject-version status'}

    def records():
        for binding in selection.get('records', []):
            if binding.get('encoding') == 'text':
                data = {'text': sources.raw(binding['path']).decode('utf-8')}
            else:
                data = sources.read(binding['path'])
            counts['judgment_records'] += 1
            yield {'role': binding.get('role', 'assessment'),
                   'source_sha256': binding['sha256'], 'source': binding['path'],
                   'actor': _actor(data), 'data': _clean(data)}

    def results():
        for row in reused:
            counts['result_records'] += 1
            yield row
        for binding in selection.get('parameters', []):
            data = sources.read(binding['path'])
            if binding.get('projection') == 'case_settings':
                if not isinstance(data, dict):
                    raise ValueError('case settings must be an object')
                data = {key: value for key, value in data.items() if key not in {'notes', 'cases'}}
            elif binding.get('projection') is not None:
                raise ValueError('unsupported subject parameter projection')
            counts['result_records'] += 1
            yield {'role': 'saved_parameters', 'source_sha256': binding['sha256'],
                   'source': binding['path'], 'data': _clean(data)}
        counts['result_records'] += 1
        yield {'role': 'publication_summary', 'status': selection.get('status', 'historical'),
               'answer_records': counts['answers'], 'raw_answer_records': counts['raw_answers'],
               'parsed_only_answer_records': counts['parsed_only_answers'],
               'independent_call_count': selection.get('independent_call_count'),
               'call_count_basis': 'Only explicitly recorded independent counts; answer rows are not new calls.'}

    return {'inputs.jsonl': iter([*inputs.values(), *prompts.values()]),
            'answers.jsonl': iter(answers), 'judgments.jsonl': records(), 'results.jsonl': results()}
