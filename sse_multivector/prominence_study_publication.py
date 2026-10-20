"""Export final manual prominence studies without executing their old jobs."""
import json
from pathlib import Path
import re

from ._runner_bootstrap import shared
from .prompt_study_publication import _json, _sha
from .subject_goal_publication import _clean


_SETTINGS = ('provider', 'model', 'reasoning_effort', 'timeout_seconds',
             'max_output_tokens', 'runner_version', 'runner_sha256', 'wrapper_sha256')


def _index(rows, key, label):
    if not isinstance(rows, list):
        raise ValueError('invalid prominence ' + label)
    result = {}
    for row in rows:
        identity = row.get(key) if isinstance(row, dict) else None
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError('ambiguous prominence ' + label)
        result[identity] = row
    return result


def _render(text, spans):
    fragments, parts, cursor = [], [], 0
    if not isinstance(text, str) or '⟦' in text or '⟧' in text or not isinstance(spans, list) or not spans:
        raise ValueError('invalid prominence source mask')
    for span in spans:
        if (not isinstance(span, list) or len(span) != 2
                or any(type(value) is not int for value in span)):
            raise ValueError('invalid prominence character span')
        start, end = span
        if not 0 <= cursor <= start < end <= len(text):
            raise ValueError('invalid prominence character span')
        fragments.append(text[start:end])
        parts.extend((text[cursor:start], '⟦', text[start:end], '⟧'))
        cursor = end
    parts.append(text[cursor:])
    return dict(mask=fragments, marked_post=''.join(parts))


def _relative_source(name, sources):
    if not isinstance(name, str):
        raise ValueError('invalid prominence source reference')
    if Path(name).is_absolute():
        prefix = str(sources.root) + '/'
        if name.startswith(prefix):
            name = name[len(prefix):]
        elif '/oracle-mvp/' in name:
            name = name.split('/oracle-mvp/', 1)[1]
        else:
            raise ValueError('prominence source reference is outside the repository')
    if name not in sources.bindings:
        raise ValueError('prominence source reference is not selected')
    return name


def _origins(sources, selection, cases):
    expected, provenance = {}, {}
    for binding in selection.get('origin_sources', []):
        path, kind = binding['path'], binding['format']
        document = sources.read(path)
        wanted = {row.get('source_id') for row in cases.values() if row.get('source') == path}
        if kind == 'corpus':
            for note in document.get('notes', []):
                for item in note.get('subjects', []):
                    if item.get('id') not in wanted:
                        continue
                    raw = note['text'].encode('utf-8')
                    spans = []
                    for start, end in item['byte_spans']:
                        if not 0 <= start < end <= len(raw):
                            raise ValueError('invalid prominence source byte span')
                        left = len(raw[:start].decode('utf-8'))
                        spans.append([left, left + len(raw[start:end].decode('utf-8'))])
                    value = dict(note_id=note['note_id'], text=note['text'], character_spans=spans)
                    value['input'] = _render(value['text'], spans)
                    if value['input']['mask'] != item['fragments']:
                        raise ValueError('prominence source fragments mismatch')
                    key = (path, item['id'])
                    if key in expected:
                        raise ValueError('ambiguous prominence original selection')
                    expected[key] = value
                    provenance[key] = dict(version=None, status='unknown',
                        basis='Saved original selection does not identify its subject prompt version')
        elif kind == 'assessment':
            for item in document.get('items', document.get('results', [])):
                if item.get('id') not in wanted:
                    continue
                spans = [[row['start'], row['end']] for row in item.get('decoded_ranges', item.get('ranges', []))]
                text = item.get('source_text', item.get('text'))
                value = dict(note_id=item['note_id'], text=text, character_spans=spans,
                             input=_render(text, spans))
                if (item.get('format_valid') is not True
                        or value['input']['mask'] != item['fragments']
                        or 'inline_mask' in item and item['inline_mask'] != value['input']['marked_post']):
                    raise ValueError('prominence saved assessment mask mismatch')
                key = (path, item['id'])
                if key in expected:
                    raise ValueError('ambiguous prominence original selection')
                expected[key] = value
                match = re.search(r'ASv\d+\.\d+', str(item.get('subject_origin', '')))
                version = document.get('subject_prompt_version') or (match.group() if match else None)
                provenance[key] = dict(version=version,
                    status='deprecated' if version and re.fullmatch(r'ASv6\.(?:[0-9]|[1-9][0-9])', version)
                        else 'unknown', basis='Saved source assessment subject provenance')
        else:
            raise ValueError('unsupported prominence original selection format')
    for case in cases.values():
        if 'source' not in case:
            continue
        original = expected.get((case['source'], case.get('source_id')))
        if original is None or any(case.get(key) != value for key, value in original.items()):
            raise ValueError('prominence input differs from its original selection')
    return {identity: provenance.get((case.get('source'), case.get('source_id')))
            for identity, case in cases.items()}


def _project(value):
    value = _clean(value)
    if isinstance(value, dict) and isinstance(value.get('execution_notes'), str):
        value['execution_notes'] = re.sub(r'\bselected account\s+[^,.;\n]+',
            '[account omitted]', value['execution_notes'], flags=re.I)
    return value


def prepare(sources, selection, metadata):
    engine = shared('extraction_pipeline')
    for module, label in ((engine, 'experiment_runner/extraction_pipeline.py'),
            (engine.compatibility, 'experiment_runner/compatibility.py')):
        metadata['exporter_sources'][label] = _sha(Path(module.__file__).read_bytes())
    metadata['exporter_sources']['sse_multivector/subject_goal_publication.py'] = _sha(
        Path(__file__).with_name('subject_goal_publication.py').read_bytes())
    read = lambda key: sources.read(selection[key]['path'])
    plan, native_inputs, config, manifest, output, final = (
        read(key) for key in ('plan', 'inputs', 'configuration', 'manifest', 'output', 'result'))
    cases = _index(native_inputs if isinstance(native_inputs, list) else [native_inputs], 'id', 'case')
    configured = _index(config.get('prompts'), 'prompt_id', 'configured prompt')
    frozen = _index(manifest.get('prompts'), 'prompt_id', 'frozen prompt')
    published = _index(output.get('responses'), 'prompt_id', 'published response')
    receipts = _index([_json(line) for line in sources.raw(selection['receipt']['path']).splitlines()
                       if line.strip()], 'note_id', 'receipt')
    native_results = final.get('results') if 'results' in final else [dict(final, id=final.get('case'))]
    measured = _index(native_results, 'id', 'final measurement')
    if (any(set(value) != set(cases) for value in (configured, frozen, published, receipts, measured))
            or config.get('prompts') != manifest.get('prompts')
            or manifest.get('config_sha256') != sources.hashes[selection['configuration']['path']]
            or output.get('manifest_sha256') != sources.hashes[selection['manifest']['path']]):
        raise ValueError('prominence configuration/manifest/output identities mismatch')
    if 'cases' in plan:
        planned = _index(plan['cases'], 'id', 'planned case')
        if set(planned) != set(cases) or any(
                case.get(key) != value for identity, row in planned.items()
                for key, value in row.items() for case in (cases[identity],)):
            raise ValueError('prominence planned/input case binding mismatch')
    if 'comparisons' in final:
        if len(final['comparisons']) != len(plan.get('comparisons', [])):
            raise ValueError('prominence planned/final comparison count mismatch')
        for planned, comparison in zip(plan['comparisons'], final['comparisons']):
            if (any(comparison.get(key) != value for key, value in planned.items())
                    or comparison.get('higher') not in measured or comparison.get('lower') not in measured
                    or comparison.get('higher_score') != measured[comparison['higher']].get('score')
                    or comparison.get('lower_score') != measured[comparison['lower']].get('score')):
                raise ValueError('prominence comparison/score binding mismatch')
    template_raw = sources.raw(selection['prompt']['path'])
    template = template_raw.decode('utf-8')
    if (template.count('{INPUT_JSON}') != 1 or plan.get('prompt_sha256') != _sha(template_raw)
            or final.get('prompt_sha256') != plan['prompt_sha256']
            or any(config.get(key) != manifest.get(key) or plan.get(key) != manifest.get(key)
                   or final.get(key) != manifest.get(key) for key in ('model', 'reasoning_effort'))
            or config.get('provider') != manifest.get('provider') or plan.get('provider') != manifest.get('provider')):
        raise ValueError('prominence frozen prompt/settings mismatch')
    pinned = read('pinned_inputs')
    historical_code = selection.get('historical_code_pins', {})
    critical = {selection[key]['path'] for key in ('plan', 'inputs', 'configuration',
                'manifest', 'output', 'result', 'prompt', 'receipt')}
    for path, digest in historical_code.items():
        revision = selection.get('historical_code_revisions', {}).get(path)
        if (path not in sources.bindings or path in critical or Path(path).suffix != '.py'
                or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)
                or revision is not None and (not isinstance(revision, str)
                    or not re.fullmatch('[0-9a-f]{40}', revision))):
            raise ValueError('invalid prominence historical helper binding')
    limitations = []
    for name, digest in pinned.items():
        path = _relative_source(name, sources)
        actual = _sha(sources.raw(path))
        if actual != digest:
            if historical_code.get(path) != digest:
                raise ValueError('prominence pinned source hash mismatch')
            limitations.append(dict(source=path, recorded_sha256=digest,
                current_source_sha256=actual, limitation='Historical helper source changed; saved final inputs retained'))
            if path in selection.get('historical_code_revisions', {}):
                limitations[-1]['historical_source_git_revision'] = selection['historical_code_revisions'][path]
    provenance = _origins(sources, selection, cases)
    if selection.get('mask_source'):
        source = selection['mask_source']
        originals = _index(sources.read(source['cases']['path']), 'id', 'source mask case')
        mask_receipts = _index([_json(line) for line in sources.raw(source['receipt']['path']).splitlines()
                               if line.strip()], 'note_id', 'source mask receipt')
        decoder = shared('mask_positions')
        metadata['exporter_sources']['experiment_runner/mask_positions.py'] = _sha(Path(decoder.__file__).read_bytes())
        for identity, case in cases.items():
            original, receipt = originals.get(identity), mask_receipts.get(identity)
            if (original is None or receipt is None or receipt.get('status') != 'succeeded'
                    or any(case.get(key) != original.get(key) for key in ('note_id', 'text', 'subject'))
                    or case.get('mask_request_sha256') != receipt.get('request_sha256')
                    or receipt.get('final_output_sha256') != _sha(receipt.get('final_output_raw', '').encode())):
                raise ValueError('prominence source mask receipt binding mismatch')
            _, ranges = decoder.decode(receipt['final_output_raw'], case['text'])
            if [[row['start'], row['end']] for row in ranges] != case.get('character_spans'):
                raise ValueError('prominence source mask spans mismatch')
            match = re.search(r'ASv\d+\.\d+', str(original.get('subject_origin', '')))
            version = match.group() if match else None
            provenance[identity] = dict(version=version,
                status='deprecated' if version and re.fullmatch(r'ASv6\.(?:[0-9]|[1-9][0-9])', version)
                    else 'unknown', basis='Saved mask-source case subject_origin')
    inputs, answers, results = {}, [], []
    for identity, case in cases.items():
        masked = _render(case.get('text'), case.get('character_spans'))
        rendered = template.replace('{INPUT_JSON}', json.dumps(masked, ensure_ascii=False, indent=2))
        receipt, measurement = receipts[identity], measured[identity]
        raw = receipt.get('final_output_raw')
        if (masked != case.get('input') or frozen[identity].get('text') != rendered
                or receipt.get('stage') != 'prompt' or receipt.get('job_key') != 'prompt:' + identity
                or receipt.get('status') != 'succeeded' or receipt.get('exit_code') != 0
                or receipt.get('error') is not None or receipt.get('response_schema_sha256') is not None
                or receipt.get('manifest_sha256') != sources.hashes[selection['manifest']['path']]
                or receipt.get('prompt_sha256') != _sha(rendered.encode())
                or receipt.get('request_sha256') not in {engine._prompt_request_key(manifest, rendered),
                    engine._prompt_request_key(manifest, rendered, legacy=True)}
                or not isinstance(raw, str) or receipt.get('final_output_sha256') != _sha(raw.encode())
                or receipt.get('response') != raw or published[identity].get('response') != raw
                or measurement.get('raw') != raw or measurement.get('request_sha256') != receipt.get('request_sha256')
                or any(receipt.get(key) != manifest.get(key) for key in
                    ('provider', 'model', 'reasoning_effort', 'runner_version', 'runner_sha256', 'wrapper_sha256'))):
            raise ValueError('prominence raw answer/request binding mismatch')
        decoded = _json(raw)
        if (not isinstance(decoded, dict) or set(decoded) != {'prominence'}
                or type(decoded['prominence']) is not int or not 0 <= decoded['prominence'] <= 100
                or measurement.get('score') != decoded['prominence']
                or measurement.get('usage') != receipt.get('usage')):
            raise ValueError('prominence final score/usage binding mismatch')
        if (any(key in measurement and measurement[key] != case.get(key)
                for key in ('subject', 'mask_request_sha256'))
                or 'fragments' in measurement and measurement['fragments'] != masked['mask']):
            raise ValueError('prominence final mask/source binding mismatch')
        note_id = case.get('note_id')
        original = dict(note_id=note_id, text=case['text'])
        if not isinstance(note_id, str) or not note_id or note_id in inputs and inputs[note_id] != original:
            raise ValueError('ambiguous prominence source post identity')
        inputs[note_id] = original
        answers.append(dict(case_id=identity, note_id=note_id, prompt_version=plan.get('prompt_version', 'PPv10'),
            output=raw, output_sha256=receipt['final_output_sha256'], character_spans=case['character_spans'],
            mask_fragments=masked['mask'], subject=case.get('subject'),
            request_sha256=receipt['request_sha256'], mask_request_sha256=case.get('mask_request_sha256'),
            execution=measurement.get('execution'), receipt_execution=receipt.get('execution'),
            label=case.get('label'), source_id=case.get('source_id'),
            subject_provenance=provenance.get(identity) or dict(version=None,status='unknown')))
        result = {key: _project(value) for key, value in measurement.items()
                  if key not in {'raw', 'results', 'error'}}
        result.update(kind='score', case_id=identity, error=None if measurement.get('error') is None
                      else 'saved_error_details_omitted', raw_answer_sha256=receipt['final_output_sha256'])
        results.append(result)
    summary = {key: _project(value) for key, value in final.items()
               if key not in {'results', 'raw', 'error', 'score', 'request_sha256'}}
    results.append(dict(kind='study_summary', values=summary))
    judgments = []
    for binding in selection.get('assessments', []):
        if binding.get('format') == 'markdown':
            document = sources.raw(binding['path']).decode('utf-8')
            agent = bool(re.search(r'\bassistant assessments\b', document, re.I))
            data = dict(text=_project(document))
            basis = 'explicit assistant-assessments statement' if agent else 'actor not explicitly recorded'
        else:
            document = sources.read(binding['path'])
            label = document.get('assessor', '')
            agent = isinstance(label, str) and bool(re.search(r'\bassistant\b|\bagent\b', label, re.I))
            data, basis = _project(document), 'saved assessor field' if agent else 'actor not explicitly recorded'
        judgments.append(dict(kind='saved_assessment', actor='agent' if agent else 'unknown',
            attribution_basis=basis, source=binding['path'], assessment=data))
    metadata.update(parameters=_project(plan), settings={key: manifest.get(key) for key in _SETTINGS},
        prompt=dict(version=plan.get('prompt_version', 'PPv10'), text=template,
                    sha256=_sha(template_raw), source=selection['prompt']['path']),
        binding_limitations=limitations,
        subject_provenance=dict(versions=selection.get('subject_versions', []),
            status=selection.get('subject_provenance_status', 'unknown'),
            limitation='Historical prominence evidence; raw posts are not deprecated; unknown provenance is not current validation'),
        reuse=dict(intentional_repeat=manifest.get('request_reuse', {}).get('intentional_repeat'),
            recorded_new_calls=final.get('new_calls'),
            limitation='Missing execution fields remain unknown; saved answers are not additional independent trials'),
        receipt_validation='Source and request joins only; private transport envelopes are not republished')
    return {'inputs.jsonl': inputs.values(), 'answers.jsonl': answers,
            'judgments.jsonl': judgments, 'results.jsonl': results}
