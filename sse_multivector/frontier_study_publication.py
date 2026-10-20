"""Compact final evidence from explicitly selected frontier comparison sources.

Native receipts establish answers and attempt outcomes. Review packets retain
their comments and case membership, but their rendered answer views are not new
model responses. No calls, decoding, semantic repair, or verdicts are performed.
"""
import hashlib
import json
from pathlib import Path
import re

from . import mask_goal_publication as mask


_PRIVATE = {'authorization', 'authorization_header', 'api_token', 'refresh_token',
            'session_id', 'thread_id', 'generation_id', 'response_id',
            'event_trace', 'stdout', 'stdout_json', 'stderr', 'argv',
            'request_body', 'raw_events', 'is_byok', 'reservation_id'}
_REQUEST = {'model', 'stream', 'store', 'reasoning', 'max_output_tokens',
            'temperature', 'top_p', 'max_tokens', 'tools', 'tool_choice',
            'parallel_tool_calls', 'response_format', 'text', 'provider',
            'instructions'}
_RESULT = {'client', 'node_version', 'runner_version', 'pi_ai_version',
           'runner_sha256', 'provider', 'model', 'reasoning', 'prompt_sha256',
           'schema_sha256', 'request_body_sha256', 'elapsed_ms', 'timing',
           'done_received', 'http_status', 'upstream_request', 'finish_reason',
           'response_status', 'usage', 'local_abort', 'stop_reason',
           'raw_stop_reason', 'response_model', 'provider_thinking_level',
           'http_attempts', 'diagnostics', 'error', 'valid', 'validation_error',
           'usage_note', 'event_trace_dropped'}
_RECEIPT = {'status', 'attempt', 'elapsed_seconds', 'exit_code', 'error',
            'model', 'provider', 'reasoning_effort', 'prompt_sha256',
            'request_sha256', 'response_schema_sha256', 'runner_sha256',
            'runner_version', 'wrapper_sha256', 'usage', 'reused_from',
            'retry_reason', 'execution'}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def _require(value, message):
    if not value:
        raise ValueError('frontier study publication: ' + message)


def _binding(declaration):
    return {key: declaration[key] for key in ('path', 'sha256')}


def _without_private(value, key=''):
    if isinstance(value, dict):
        return {name: _without_private(child, name) for name, child in value.items()
                if name not in _PRIVATE and name != 'request_id'
                and not (name == 'id' and key == 'provider_responses')}
    if isinstance(value, list):
        return [_without_private(child, key) for child in value]
    return value


def _project(value, sources, *, key=''):
    """Preserve selected scientific objects; remove concrete transport fields."""
    # The shared projector preserves scientific execution/isolation controls.
    return mask._project(_without_private(value), sources, key=key)


def _factor(text):
    # Some compatibility calls supply literal short text, without post blocks.
    if '<post>\n' in text:
        return mask._factor(text)[:2]
    return text, {}


def _result(value, sources):
    result = {key: _project(value[key], sources, key=key) for key in _RESULT if key in value}
    if 'response_metadata' in value:
        result['response_metadata'] = _project({key: child for key, child in value['response_metadata'].items()
            if key not in {'id', 'request_id'}}, sources)
    return result


def _at(value, fields):
    for field in fields:
        _require((type(field) is int and isinstance(value, list) and 0 <= field < len(value))
                 or (isinstance(field, str) and isinstance(value, dict) and field in value),
                 'selected source field is missing')
        value = value[field]
    return value


def _view(subjects, style):
    _require(isinstance(subjects, list), 'review source lacks subjects')
    if style == 'numbered_subjects':
        return '\n\n'.join(str(i + 1) + '. ' + row['subject'] for i, row in enumerate(subjects))
    if style == 'hierarchy':
        return '\n'.join('  ' * (len(row['number'].split('.')) - 1) + row['number'] +
                         '  ' + row['subject'] for row in subjects)
    if style == 'contexts':
        return '\n\n'.join(row['number'] + '  ' + row['subject'] + '\n' + row['context']
                           for row in subjects)
    raise ValueError('frontier study publication: unsupported saved review transform')


def prepare(sources, selection, metadata):
    """Return the four payloads required by the historical publisher."""
    inputs, answers, judgments, results = [], [], [], []
    templates, input_ids, answer_keys = {}, set(), set()
    counts = dict(raw_successful_answers=0, raw_partial_answers=0,
                  already_selected_answers=0, failed_attempts=0,
                  not_recorded_cases=0, review_cells=0)
    helper = Path(mask.__file__)
    metadata['exporter_sources']['sse_multivector/' + helper.name] = _sha(helper.read_bytes())
    versions = selection.get('subject_versions', [])
    parsed_versions = [re.fullmatch(r'ASv6\.(\d+)', value) for value in versions]
    deprecated = True if any(match and int(match[1]) < 100 for match in parsed_versions) else (
        False if versions and all(parsed_versions) and not selection.get('subject_lineage_unknown') else None)
    metadata.update(historical=True, status=selection.get('status', 'historical'),
                    selection_basis=selection.get('selection_basis', 'Saved final and partial study evidence.'),
                    limitations=selection.get('limitations', []), counts=counts,
                    input=dict(subject_prompt_versions=versions,
                               generated_subjects_deprecated=deprecated,
                               lineage_complete=bool(versions) and not selection.get('subject_lineage_unknown', False),
                               subject_provenance_status=selection.get('subject_provenance_status',
                                   'known' if versions else 'unknown'),
                               raw_posts_deprecated=False,
                               status='Historical evidence, not current-pipeline validation.'))
    if selection.get('collection_status'):
        metadata['collection_status'] = selection['collection_status']

    def supplied(text, source):
        _require(isinstance(text, str), 'supplied prompt is not text')
        template, variables = _factor(text)
        template_id = _sha(template.encode())
        templates.setdefault(template_id, template)
        identity = _sha(_canonical(dict(template_id=template_id, variables=variables)))
        if identity not in input_ids:
            inputs.append(dict(type='prompt_input', input_id=identity,
                               prompt_template_id=template_id, variables=variables,
                               source=source))
            input_ids.add(identity)
        return identity

    for declaration in selection.get('parameters', []):
        inputs.append(dict(type='study_parameters', source=_binding(declaration),
                           data=_project(sources.read(declaration['path']), sources)))
    for declaration in selection.get('posts', []):
        notes = sources.read(declaration['path'])['notes']
        by_id = {note['id']: note for note in notes}
        _require(len(by_id) == len(notes), 'duplicate source-post case identity')
        for case in declaration['cases']:
            _require(case in by_id, 'selected source-post identity is missing')
            note = by_id[case]
            _require(isinstance(note.get('text'), str), 'source post is not text')
            inputs.append(dict(type='source_post', source=_binding(declaration),
                               data={key: note[key] for key in ('id', 'note_id', 'text') if key in note}))
    for declaration in selection.get('inputs', []):
        value = sources.read(declaration['path'])
        # The AS23 selection saves parsed Astra answers alongside each input.
        # Replace only proven previously selected copies, retaining all methods.
        if declaration.get('astra_references'):
            by_id = declaration['astra_references']
            value = json.loads(json.dumps(value))
            for note in value['notes']:
                reference = by_id[note['id']]
                saved = note['astra']
                _require(saved['output_sha256'] == reference['source_sha256'],
                         'saved Astra source binding differs')
                body = sources.read(reference['source']['path'])
                selected = [row['response'] for row in body['responses']
                            if row['prompt_id'] == reference['case_id']]
                _require(len(selected) == 1 and json.loads(selected[0]) == saved['output'],
                         'saved Astra parsed answer differs')
                saved.pop('output')
                saved['answer_reference'] = {k: v for k, v in reference.items() if k != 'source'}
                if 'prompt' in note:
                    note['input_ref'] = supplied(note.pop('prompt'),
                        dict(**_binding(declaration), case_id=note['id']))
        inputs.append(dict(type='saved_input', source=_binding(declaration),
                           data=_project(value, sources)))

    for run in selection.get('native_runs', []):
        frozen = run['manifest']
        manifest = sources.read(frozen['path'])
        _require(manifest.get('schema_version') == 1, 'unsupported native manifest')
        if run.get('input'):
            _require(manifest.get('input_sha256') == run['input']['sha256'], 'native input hash differs')
        config_decl = run.get('configuration')
        if config_decl:
            config = sources.read(config_decl['path'])
            _require(manifest.get('config_sha256') == config_decl['sha256'], 'configuration hash differs')
            for key in ('model', 'provider', 'reasoning_effort'):
                if key in config and key in manifest:
                    _require(config[key] == manifest[key], 'configuration setting differs: ' + key)
            if 'prompts' in config:
                _require(config['prompts'] == manifest.get('prompts'), 'configuration prompt differs')
        prompts = {}
        for prompt in manifest.get('prompts', []):
            _require(set(prompt) == {'prompt_id', 'text'} and prompt['prompt_id'] not in prompts,
                     'duplicate or malformed frozen prompt')
            prompts[prompt['prompt_id']] = prompt['text']
        _require(prompts, 'manifest lacks frozen prompts')
        controls = {key: manifest[key] for key in ('isolation', 'request_reuse',
                    'response_schema', 'concurrency', 'timeout_seconds', 'mask_format',
                    'position_decoder_sha256', 'prompt_sha256', 'max_output_tokens',
                    'response_schema_sha256') if key in manifest}
        settings = mask._settings(manifest)
        if 'codex_version' in manifest:
            _require(isinstance(manifest['codex_version'], str), 'invalid saved runner version')
            settings['codex_version'] = manifest['codex_version']
        inputs.append(dict(type='run_parameters', source=_binding(frozen),
                           settings=settings, controls=_project(controls, sources)))
        prompt_inputs = {case: supplied(text, dict(**_binding(frozen), prompt_id=case))
                         for case, text in prompts.items()}
        receipt_decl = run['receipt']
        successful, attempted = {}, set()
        for line_number, row in mask._receipts(sources, receipt_decl, frozen['sha256']):
            case = row.get('note_id')
            _require(case in prompts, 'receipt refers to an unknown prompt')
            _require(row.get('prompt_sha256') == _sha(prompts[case].encode()),
                     'receipt prompt hash differs')
            attempted.add(case)
            raw = row.get('final_output_raw')
            if isinstance(raw, str) and raw:
                _require(row.get('final_output_sha256') == _sha(raw.encode()),
                         'receipt answer hash differs')
            origin = dict(**_binding(receipt_decl), line=line_number)
            measured = {key: _project(row[key], sources, key=key) for key in _RECEIPT if key in row}
            if isinstance(row.get('model_result'), dict):
                native = row['model_result']
                measured['model_result'] = _result(native, sources)
                body = native.get('request', {}).get('body')
                if isinstance(body, dict):
                    measured['request_controls'] = _project({key: body[key] for key in _REQUEST if key in body}, sources)
                    measured['request_body_sha256'] = _sha(json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode())
                    messages = body.get('messages', body.get('input', []))
                    if isinstance(messages, list):
                        supplied_text = [message['content'] for message in messages
                                         if message.get('role') == 'user']
                        if supplied_text and isinstance(supplied_text[-1], str):
                            _require(supplied_text[-1] == prompts[case], 'actual native request prompt differs')
            measured.update(type='attempt', case_id=case, input_ref=prompt_inputs[case],
                            source=origin)
            if row.get('status') != 'succeeded':
                counts['failed_attempts'] += 1
                if isinstance(raw, str) and raw:
                    measured.update(partial_response=raw, partial_response_sha256=_sha(raw.encode()))
                    counts['raw_partial_answers'] += 1
                results.append(measured)
                continue
            _require(isinstance(raw, str), 'successful receipt lacks exact raw response')
            _require(case not in successful, 'multiple successful answers in one selected native run')
            successful[case] = (raw, origin, measured)
        output_decl = run.get('output')
        if output_decl:
            output = sources.read(output_decl['path'])
            _require(output.get('manifest_sha256') == frozen['sha256'], 'output manifest hash differs')
            saved = output.get('responses')
            _require(isinstance(saved, list), 'unsupported native output')
            by_case = {}
            for row in saved:
                _require(set(row) == {'prompt_id', 'response'} and row['prompt_id'] not in by_case,
                         'duplicate or malformed saved output')
                by_case[row['prompt_id']] = row['response']
            _require(by_case == {case: value[0] for case, value in successful.items()},
                     'saved output and successful receipt answers differ')
        previous = run.get('already_selected')
        if previous:
            _require(previous['manifest_sha256'] == frozen['sha256'], 'existing publication manifest differs')
            imported = sources.read(previous['imported_experiment']['path'])['plan']
            _require(imported.get('imported') is True
                     and imported.get('manifest_sha256') == frozen['sha256']
                     and mask._portable(imported.get('run_directory', ''), sources) ==
                     str(Path(frozen['path']).parent), 'existing import source differs')
        for case, (raw, origin, measured) in successful.items():
            key = frozen['path'] + '#' + case
            _require(key not in answer_keys, 'duplicate selected native answer')
            answer_keys.add(key)
            common = dict(answer_id=key, case_id=case, input_ref=prompt_inputs[case],
                          source=origin, manifest=_binding(frozen), settings=settings,
                          raw_response_sha256=_sha(raw.encode()), receipt=measured)
            if previous:
                mapped = previous['answers'][case]
                _require(mapped['raw_response_sha256'] == _sha(raw.encode()),
                         'existing publication raw answer differs')
                results.append(dict(type='existing_answer_reference', **common,
                                    publication=previous['publication'],
                                    published_case_id=mapped['case_id']))
                counts['already_selected_answers'] += 1
            else:
                answers.append(dict(role=run['task'] + '_answer', status='succeeded',
                                    raw_response=raw, **common))
                counts['raw_successful_answers'] += 1
        for case in prompts:
            if case not in attempted:
                results.append(dict(type='case_outcome', source=_binding(frozen),
                                    case_id=case, input_ref=prompt_inputs[case], outcome='not_recorded',
                                    scope='This frozen run only; later continuation runs are separate sources.'))
                counts['not_recorded_cases'] += 1

    def request(body, origin):
        _require(isinstance(body, dict), 'request body is not an object')
        controls = {key: body[key] for key in _REQUEST if key in body and key != 'text'}
        messages = body.get('messages', body.get('input'))
        controls['message_context'] = []
        input_refs = []
        if isinstance(messages, list):
            for index, message in enumerate(messages):
                _require(isinstance(message, dict) and set(message) <= {'role', 'type', 'content'}
                         and isinstance(message.get('role'), str), 'unsupported saved request message')
                context = {key: message[key] for key in ('role', 'type') if key in message}
                content = message.get('content')
                if isinstance(content, str):
                    if message['role'] == 'user':
                        input_refs.append(supplied(content, dict(**origin, message=index)))
                        context['input_ref'] = input_refs[-1]
                    else:
                        context['content'] = content
                else:
                    _require(isinstance(content, list), 'unsupported saved request content')
                    context['parts'] = []
                    for part_index, part in enumerate(content):
                        _require(isinstance(part, dict) and set(part) == {'type', 'text'}
                                 and part['type'] in {'text', 'input_text', 'output_text'}
                                 and isinstance(part['text'], str), 'unsupported saved request text part')
                        projected = dict(type=part['type'])
                        if message['role'] == 'user':
                            input_refs.append(supplied(part['text'], dict(**origin, message=index, part=part_index)))
                            projected['input_ref'] = input_refs[-1]
                        else:
                            projected['text'] = part['text']
                        context['parts'].append(projected)
                controls['message_context'].append(context)
        elif isinstance(messages, str):
            input_refs.append(supplied(messages, origin))
        # Responses API uses text.format for the same scientific schema control.
        if isinstance(body.get('text'), dict):
            controls['text'] = body['text']
        inputs.append(dict(type='request_parameters', source=origin,
                           data=_project(controls, sources)))
        return input_refs

    for declaration in selection.get('http_results', []):
        value = sources.read(declaration['path'])
        context = []
        position = []
        for field in declaration.get('field', []):
            if isinstance(value, dict):
                other = {key: child for key, child in value.items() if key != field}
                if other:
                    context.append(dict(field=list(position), data=_project(other, sources)))
            value = _at(value, [field])
            position.append(field)
        origin = _binding(declaration)
        if declaration.get('field'):
            origin['field'] = declaration['field']
        identity = declaration['path'] + '#' + _canonical(declaration.get('field', [])).decode()
        _require(identity not in answer_keys, 'duplicate selected HTTP result')
        answer_keys.add(identity)
        _require(isinstance(value, dict), 'saved HTTP result is not an object')
        attempt_decl = declaration.get('attempt')
        attempt = sources.read(attempt_decl['path']) if attempt_decl else {}
        body = attempt.get('request', value.get('request', {})).get('body')
        refs = []
        if isinstance(body, dict):
            body_hash = _sha(json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode())
            for candidate in (attempt.get('request_body_sha256'), value.get('request_body_sha256')):
                if candidate is not None:
                    _require(candidate == body_hash, 'HTTP request body hash differs')
            refs = request(body, _binding(attempt_decl) if attempt_decl else origin)
        elif declaration.get('input_manifest'):
            manifest_decl = declaration['input_manifest']
            manifest = sources.read(manifest_decl['path'])
            prompt = next((p for p in manifest['prompts'] if p['prompt_id'] == declaration['case_id']), None)
            _require(prompt is not None, 'HTTP result lacks its saved prompt')
            refs = [supplied(prompt['text'], dict(**_binding(manifest_decl), prompt_id=prompt['prompt_id']))]
        data = _result(value, sources)
        results.append(dict(type='transport_result', source=origin, input_refs=refs,
                            context=context, data=data))
        completed = (value.get('stop_reason') == 'stop') if 'stop_reason' in value else (
            value.get('done_received') is True and not value.get('local_abort')
            and (value.get('finish_reason') == 'stop' or value.get('response_status') == 'completed'))
        if not completed or value.get('valid') is False:
            counts['failed_attempts'] += 1
        raw = value.get('raw_text')
        if isinstance(raw, str) and raw:
            answers.append(dict(answer_id=identity, role=declaration.get('task', 'subject') + '_answer',
                                status='completed' if completed else 'saved_partial',
                                source=origin, input_refs=refs, raw_response=raw,
                                raw_response_sha256=_sha(raw.encode())))
            counts['raw_successful_answers' if completed else 'raw_partial_answers'] += 1

    for declaration in selection.get('records', []):
        role = declaration['role']
        row = dict(type=role, source=_binding(declaration),
                   data=_project(sources.read(declaration['path']), sources))
        (judgments if role in {'assessment', 'scores'} else results).append(row)

    reference_cache = {}

    def read_reference(path):
        if path not in reference_cache:
            reference_cache[path] = sources.read(path)
        return reference_cache[path]

    def referenced_answer(declaration):
        style = declaration['format']
        value = None if style == 'receipt' else _at(read_reference(declaration['path']), declaration.get('field', []))
        ref = dict(source=_binding(declaration))
        if declaration.get('field'):
            ref['source']['field'] = declaration['field']
        if style == 'output':
            rows = [row for row in value['responses'] if row['prompt_id'] == declaration['case_id']]
            _require(len(rows) == 1, 'review source answer is not unique')
            raw = rows[0]['response']
            parsed = json.loads(raw)
            ref.update(case_id=declaration['case_id'], raw_response_sha256=_sha(raw.encode()))
        elif style == 'parsed':
            parsed = value
            ref['saved_parsed_sha256'] = _sha(_canonical(parsed))
        elif style == 'http':
            raw = value['raw_text']
            parsed = json.loads(raw)
            ref['raw_response_sha256'] = _sha(raw.encode())
        elif style == 'receipt':
            lines = sources.raw(declaration['path']).splitlines()
            line_number = declaration['line']
            _require(type(line_number) is int and 0 < line_number <= len(lines), 'review receipt line is missing')
            value = json.loads(lines[line_number - 1])
            raw = value['final_output_raw']
            _require(value['status'] == 'succeeded' and value['final_output_sha256'] == _sha(raw.encode()),
                     'review receipt is not a successful bound answer')
            parsed = json.loads(raw)
            ref.update(case_id=value['note_id'], raw_response_sha256=_sha(raw.encode()))
            ref['source']['line'] = line_number
        else:
            raise ValueError('frontier study publication: unsupported review answer source')
        if declaration.get('manifest'):
            frozen = declaration['manifest']
            manifest = read_reference(frozen['path'])
            if 'manifest_sha256' in value:
                _require(value['manifest_sha256'] == frozen['sha256'], 'review manifest hash differs')
            prompt = next((row['text'] for row in manifest['prompts']
                           if row['prompt_id'] == declaration['case_id']), None)
            _require(isinstance(prompt, str), 'review source prompt is missing')
            post = _factor(prompt)[1].get('post')
        elif declaration.get('post'):
            frozen = declaration['post']
            post = _at(read_reference(frozen['path']), frozen['field'])
        else:
            request_body = value.get('request', {}).get('body', {})
            messages = request_body.get('messages', request_body.get('input', []))
            supplied_messages = [message['content'] for message in messages
                                 if isinstance(message, dict) and message.get('role') == 'user']
            post = _factor(supplied_messages[-1])[1].get('post') if supplied_messages else None
        _require(isinstance(post, str), 'review source lacks a source-post binding')
        if declaration.get('canonical_post') or declaration.get('supplied_post'):
            _require(declaration.get('canonical_post') and declaration.get('supplied_post'),
                     'full/supplied source-post binding is incomplete')
            canonical, supplied_decl = declaration['canonical_post'], declaration['supplied_post']
            supplied_post = _at(read_reference(supplied_decl['path']), supplied_decl['field'])
            _require(post == supplied_post, 'review supplied post differs from the frozen request')
            canonical_post = _at(read_reference(canonical['path']), canonical['field'])
            _require(isinstance(canonical_post, str), 'review canonical source post is not text')
            ref.update(canonical_post_source=canonical, supplied_post_source=supplied_decl,
                       canonical_post_sha256=_sha(canonical_post.encode()),
                       supplied_post_sha256=_sha(supplied_post.encode()))
            post = canonical_post
        if declaration.get('publication'):
            ref['publication'] = declaration['publication']
        for key in ('published_answer_id', 'published_case_id', 'experiment_id'):
            if key in declaration:
                ref[key] = declaration[key]
        return parsed, post, ref

    for declaration in selection.get('review_packets', []):
        packet = sources.read(declaration['path'])
        _require(isinstance(packet.get('notes'), list), 'unsupported review packet')
        bindings = {(row['case_id'], row['model']): row for row in declaration.get('cells', [])}
        _require(len(bindings) == len(declaration.get('cells', [])), 'duplicate review cell binding')
        actor = declaration.get('actor', dict(kind='unknown'))
        if actor['kind'] != 'unknown':
            _require(actor['kind'] in {'assistant', 'user'} and actor.get('source') and actor.get('evidence'),
                     'recorded actor lacks source attribution')
            _require(actor['evidence'] in sources.raw(actor['source']['path']).decode('utf-8'),
                     'recorded actor evidence is absent')
        for note in packet['notes']:
            _require(set(note) <= {'id', 'title', 'text', 'results', 'model_input'}, 'unknown review note field')
            for cell in note['results']:
                _require(set(cell) == {'model', 'output', 'comment'}, 'unknown review cell field')
                _require(isinstance(cell['output'], str), 'review display is not text')
                bound = bindings.pop((note['id'], cell['model']), None)
                _require(bound is not None, 'review cell lacks an explicit evidence binding')
                row = dict(type='recorded_review', source=_binding(declaration),
                    case_id=note['id'], model=cell['model'], comment=cell['comment'],
                    display_sha256=_sha(cell['output'].encode()),
                    display_role='Derived review view; not an additional raw model answer.',
                    actor=actor)
                if bound['view'] in {'finding', 'recorded_outcome'}:
                    _require(bound['display_sha256'] == row['display_sha256'], 'recorded review finding differs')
                    row['recorded_' + bound['view']] = cell['output']
                else:
                    parsed, post, ref = referenced_answer(bound['answer'])
                    _require(post == note['text'], 'review source post differs')
                    if 'model_input' in note and 'supplied_post_sha256' in ref:
                        _require(_sha(note['model_input'].encode()) == ref['supplied_post_sha256'],
                                 'review supplied-input field differs')
                    _require(_view(parsed['subjects'], bound['view']) == cell['output'],
                             'review display differs from its bound answer')
                    row.update(answer_ref=ref, view=bound['view'])
                judgments.append(row)
                counts['review_cells'] += 1
        _require(not bindings, 'selected review cell is absent from saved packet')
    for declaration in selection.get('blind_packets', []):
        packet, mapping = sources.read(declaration['path']), sources.read(declaration['mapping']['path'])
        final = sources.read(declaration['results']['path'])
        sp_cases = sources.read(declaration['sp_cases']['path'])
        mask_cases = {row['id']: row for row in final['mask_cases']}
        subject_cases = {row['id']: row for row in sp_cases}
        for row in packet['items']:
            _require(set(row) <= {'slot', 'kind', 'post', 'subject', 'answer', 'rubric'},
                     'unknown blinded packet field')
            _require(row['slot'] in mapping and row['kind'] == mapping[row['slot']]['kind'],
                     'blinded packet mapping differs')
            mapped = mapping[row['slot']]
            case_id, arm = mapped['case_id'], mapped['arm']
            if mapped['kind'] == 'mask':
                case = mask_cases[case_id]
                _require(row['post'] == case['text'] and row['subject'] == case['subject'],
                         'blinded packet source input differs')
                candidate, _, repeat = arm.partition('#')
                spans = case['reference_spans'] if arm == 'astra-low' else (
                    final['mask'][candidate][case_id + ('#' + repeat if repeat else '')]['spans'])
                if spans:
                    pieces, cursor = [], 0
                    for start, end in sorted(spans):
                        _require(type(start) is int and type(end) is int and cursor <= start <= end <= len(case['text']),
                                 'invalid saved blinded mask range')
                        pieces.extend([case['text'][cursor:start], '⟦' + case['text'][start:end] + '⟧'])
                        cursor = end
                    expected = ''.join(pieces) + case['text'][cursor:]
                else:
                    expected = '(empty mask)' if spans is not None else '(output failed mechanical validation)'
            else:
                _require(mapped['kind'] == 'sp', 'unknown blinded scientific task')
                case = subject_cases[case_id]
                _require(row['post'] == case['text'], 'blinded packet source input differs')
                subjects = (case['astra_subjects'] if arm == 'astra-low' else
                            case['muse_subjects'] if arm == 'muse-high' else final['sp']['mimo-high'][case_id]['subjects'])
                expected = [subject['number'] + ' ' + subject['subject'] + ' — ' + subject['context']
                            for subject in subjects]
            _require(row['answer'] == expected, 'blinded packet answer differs from mapped final result')
            judgments.append(dict(type='blinded_review_case', source=_binding(declaration),
                slot=row['slot'], answer_ref=mapping[row['slot']], rubric=row['rubric'],
                display_sha256=_sha(_canonical(row['answer'])), actor=dict(kind='unknown')))
    for identifier, template in templates.items():
        inputs.append(dict(type='prompt_template', prompt_template_id=identifier, text=template))
    expected = selection.get('expected_counts', {})
    for key, value in expected.items():
        _require(counts.get(key) == value, 'selected ' + key + ' count differs')
    return {'inputs.jsonl': inputs, 'answers.jsonl': answers,
            'judgments.jsonl': judgments, 'results.jsonl': results}
