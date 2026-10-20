"""Offline publication of source-bound, reviewed historical prompt studies.

This adapter understands the saved call/review layouts, not transport envelopes.
It verifies their mechanical bindings without rerunning or approving the study.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re

from ._runner_bootstrap import shared


FORMAT = 'prompt-study-publication-v1'
_LIMIT = 32 * 1024 * 1024
_PARAMETERS = set('''question hypothesis prompts model reasoning_effort provider
repeats_per_prompt_per_note total_calls calls calls_per_note asv623_calls
no_baseline_generation candidate candidate_sha256 selection coverage_probes
additional_predeclared_probes detailed_meanings coverage_judgment coverage fidelity
review decision task_scope scope_limit limits changed unchanged baseline comparisons
historical_evidence'''.split())
_ASSESSMENT = set('''all_subjects_reviewed accepted_subject_indices issues coverage
detailed_coverage comment other_independent_broad_subjects subjects_reviewed evidence
definite_fidelity_errors uncertain_fidelity_items fidelity source_topic_coverage
definite_errors unresolved fidelity_reason subject_count reviewed_subject_indices
fidelity_accepted_subject_indices definite_error_indices title caveat'''.split())
_REVIEW_CONTEXT = set('''reviewer review_method coverage_caveat scope coverage_statuses
interpretation interpretation_notes review_limit coverage_scope prior_measurement_note
method subject_count definite_unsupported_subjects_found all_subjects_read
coverage_scoring conclusion recommended_next_step limits'''.split())
_SUMMARY = set('''schema_version experiment date baseline outcome calls model
reasoning_effort prompt_totals notes other_observation definite_fidelity_issues
fidelity_conclusion review_method usage recommendation scope_limit limitations
status by_prompt decision finding limits subjects_reviewed by_version review_limits
measurement_note unchanged_default next_step_proposed_not_run total_usage candidate
asv623_calls successful_calls attempts subjects reasoning usage_note
definite_unsupported_subjects_found conclusion recommended_next_step
automatic_followup_authorized'''.split())
_SUMMARY_CHILD = _SUMMARY | set('''id note_id coverage probe prompts present partial
narrower absent trials trial review_id status subject_indices reason subject note
predeclared_probe independent_entries meaning outputs definite_fidelity_errors
definite_errors unresolved input output cacheRead cacheWrite totalTokens'''.split())
_DYNAMIC = {'by_prompt', 'by_version', 'prompt_totals', 'prompts', 'coverage',
            'independent_entries'}
_SETTINGS = {'provider', 'model', 'reasoning_effort', 'timeout_seconds',
             'max_output_tokens', 'response_schema_sha256', 'runner_version',
             'runner_sha256', 'wrapper_sha256'}


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            raise ValueError('duplicate JSON object key in saved study')
        result[key] = value
    return result


def _json(raw):
    return json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError('non-finite JSON value in saved study')))


def _stamp(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


class _Sources:
    def __init__(self, directory, metadata):
        self.directory, self.metadata, self.stamps = directory, metadata, {}

    def local(self, name):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('saved call path must stay inside the study')
        path = self.directory / relative
        if not path.resolve().is_relative_to(self.directory):
            raise ValueError('saved call path escapes the study')
        return path

    def raw(self, path, label):
        if not path.is_file():
            raise ValueError('missing saved study source: ' + label)
        before = _stamp(path)
        if before[2] > _LIMIT:
            raise ValueError('saved study metadata/call exceeds 32 MiB read limit')
        with path.open('rb') as stream:
            raw = stream.read(_LIMIT + 1)
        if len(raw) > _LIMIT or before != _stamp(path):
            raise ValueError('saved study source changed during export')
        self.stamps[path] = before
        self.metadata['sources'][label] = _sha(raw)
        return raw

    def read(self, name):
        return _json(self.raw(self.local(name), str(Path(name))))

    def check(self):
        if any(not path.is_file() or _stamp(path) != stamp
               for path, stamp in self.stamps.items()):
            raise ValueError('saved study source changed during export')


@contextmanager
def _snapshot(source):
    lock = source / '.lock'
    if not lock.is_file():
        yield
    else:
        with lock.open('rb') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError('saved study is active; export after it stops') from error
            yield


def _unique(rows, key, label):
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError('invalid saved ' + label)
    result = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value or value in result:
            raise ValueError('ambiguous or missing ' + label + ' identity')
        result[value] = row
    return result


def _summary(value, field=None):
    if isinstance(value, list):
        return [_summary(item, '_record' if field in _DYNAMIC else field) for item in value]
    if not isinstance(value, dict):
        return value
    if field in _DYNAMIC:
        return {key: _summary(item, '_record') for key, item in value.items()}
    fields = _SUMMARY if field is None else _SUMMARY_CHILD
    return {key: _summary(item, key) for key, item in value.items() if key in fields}


def _attribution(review):
    label = review.get('reviewer')
    evidence = [(key, review[key]) for key in ('reviewer', 'method', 'review_method')
                if isinstance(review.get(key), str)]
    for key, text in evidence:
        if re.search(r'\bassistant\b|\bagent\b', text, re.I):
            return dict(actor='agent', reviewer=label, attribution_basis=key)
        if key == 'reviewer' and text.strip().lower() == 'user':
            return dict(actor='user', reviewer=label, attribution_basis=key)
    return dict(actor='unknown', reviewer=label,
                attribution_basis='review artifact does not explicitly identify the actor role')


def _prompt(sources, plan, version):
    bindings = {**plan.get('frozen_hashes', {}), **plan.get('protected_sha256', {})}
    matches = [(name, digest) for name, digest in bindings.items()
               if Path(name).suffix == '.md' and Path(name).stem.lower() == version.lower()]
    if len(matches) != 1:
        raise ValueError('prompt version needs one saved source hash')
    name, expected = matches[0]
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('unsafe saved prompt binding')
    roots = [sources.directory]
    roots += [parent.parent for parent in sources.directory.parents if parent.name == 'sse_multivector']
    roots.append(Path(__file__).resolve().parents[1])
    candidates = list(dict.fromkeys(root / relative for root in roots))
    for path in candidates:
        if path.is_file():
            raw = sources.raw(path, 'prompt:' + version)
            if _sha(raw) != expected:
                raise ValueError('saved prompt source hash does not match')
            return raw.decode('utf-8'), dict(source=name, sha256=expected)
    raise ValueError('missing saved prompt source for ' + version)


def _prepare(sources):
    plan, inputs, saved_calls = (sources.read(name) for name in
                                ('plan.json', 'input.json', 'calls.json'))
    notes = _unique(inputs.get('notes'), 'id', 'input note')
    calls = _unique(saved_calls if isinstance(saved_calls, list) else saved_calls.get('calls'),
                    'id', 'call')
    if not calls:
        raise ValueError('saved study has no calls')
    for call in calls.values():
        short = call.get('note', call.get('note_id'))
        if short not in notes or not isinstance(notes[short].get('text'), str):
            raise ValueError('call is not bound to an input post')
        if not isinstance(notes[short].get('note_id'), str) or not notes[short]['note_id']:
            raise ValueError('input post has no canonical note ID')
        if (not isinstance(call.get('prompt', call.get('version')), str)
                or type(call.get('trial')) is not int or call['trial'] < 1):
            raise ValueError('call needs a saved prompt version and positive trial')
    fresh = sources.local('review.json').is_file()
    if fresh:
        if any(sources.local(name).exists() for name in ('review-key.json', 'review-judgments.json')):
            raise ValueError('ambiguous saved review layout')
        review = sources.read('review.json')
        judgments = _unique(review.get('notes'), 'call_id', 'review call')
        if set(judgments) != set(calls):
            raise ValueError('orphaned or missing saved call assessments')
        return plan, notes, calls, review, judgments, None, None
    key = sources.read('review-key.json')
    keys = _unique(key if isinstance(key, list) else key.get('entries', key.get('mapping')),
                   'review_id', 'review key')
    if set(row.get('id') for row in keys.values()) != set(calls) or len(keys) != len(calls):
        raise ValueError('review key must bind every call exactly once')
    review = sources.read('review-judgments.json')
    judgments = _unique(review.get('outputs'), 'review_id', 'assessment')
    views = sources.read('review-input.json')
    if 'notes' in views and 'outputs' not in views:
        outputs = []
        for note in views['notes']:
            original = notes.get(note.get('id'))
            if original is None or any(note.get(k) != original.get(k) for k in ('text', 'note_id')):
                raise ValueError('review post does not match the saved input')
            outputs.extend(dict(output, note=note['id']) for output in note['outputs'])
    else:
        outputs = views.get('outputs')
        if 'notes' in views:
            for note in views['notes']:
                original = notes.get(note.get('id'))
                if original is None or any(note.get(k) != original.get(k) for k in ('text', 'note_id')):
                    raise ValueError('review post does not match the saved input')
    outputs = _unique(outputs, 'review_id', 'review input')
    if set(keys) != set(judgments) or set(keys) != set(outputs):
        raise ValueError('orphaned or missing saved review identity')
    return plan, notes, calls, review, judgments, keys, outputs


def export_results(source, output=None):
    """Export a saved, reviewed prompt study without inference or source writes."""
    source = Path(source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError('prompt study source must be a saved study directory')
    output = Path(output) if output is not None else source.parent / (source.name + '-publication')
    if output.is_symlink():
        raise ValueError('publication destination must not be a symlink')
    destination = output.resolve()
    if source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('publication destination must be outside the saved study')
    metadata = dict(schema_version=1, format=FORMAT, experiment_id=source.name,
                    source_id=_sha(str(source).encode()), sources={}, prompts={}, settings={},
                    exporter_sha256=_sha(Path(__file__).read_bytes()),
                    interpretation='Saved historical answers and assessments; no new semantic validation or user approval.')
    with _snapshot(source):
        sources = _Sources(source, metadata)
        plan, notes, calls, review, judgments, keys, views = _prepare(sources)
        summary = sources.read('summary.json')
        parameters = {key: value for key, value in plan.items() if key in _PARAMETERS}
        parameters['notes'] = [{key: value for key, value in note.items()
                               if key in {'id', 'note_id', 'source_index', 'selection_reason',
                                          'coverage_probes', 'fidelity_checks'}}
                               for note in plan.get('notes', [])]
        metadata['parameters'] = parameters
        bindings = {**plan.get('frozen_hashes', {}), **plan.get('protected_sha256', {})}
        commit = plan.get('git_head_at_preparation')
        metadata['code'] = dict(commit=commit if isinstance(commit, str)
            and re.fullmatch('[0-9a-f]{40}', commit) else None,
            frozen_sources={name: digest for name, digest in bindings.items()
                if not Path(name).is_absolute() and '..' not in Path(name).parts
                and (Path(name).suffix in {'.py', '.sh', '.js', '.mjs'}
                     or Path(name).name == 'package-lock.json')
                and isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest)})
        metadata['review'] = {key: value for key, value in review.items()
                              if key in _REVIEW_CONTEXT and key != 'interpretation_notes'}
        attribution = _attribution(review)
        metadata['assessment_attribution'] = attribution
        metadata['recorded_status'] = summary.get('status', 'not_recorded')
        versions = sorted({call.get('prompt', call.get('version')) for call in calls.values()})
        known_as = [re.fullmatch(r'ASv6\.(\d+)', version, re.I) for version in versions]
        metadata['input'] = dict(subject_prompt_versions=versions,
            generated_subjects_deprecated=any(int(match[1]) < 100 for match in known_as if match)
                if all(known_as) else None,
            raw_posts_deprecated=False)
        prompts = {}
        for version in versions:
            prompts[version], metadata['prompts'][version] = _prompt(sources, plan, version)
        original_by_call = {}
        key_by_call = {row['id']: row for row in keys.values()} if keys else {}
        counts = dict(calls=0, subjects=0)
        metadata['counts'] = counts

        def answers():
            for call_id, call in calls.items():
                short = call.get('note', call.get('note_id'))
                note = notes[short]
                version = call.get('prompt', call.get('version'))
                config_name = call.get('config')
                if not isinstance(config_name, str):
                    raise ValueError('call is missing its saved configuration')
                config = sources.read(config_name)
                directory = Path(config_name).parent
                manifest_name, output_name = str(directory/'run/manifest.json'), str(directory/'run/output.json')
                if 'output' in call and call['output'] != output_name:
                    raise ValueError('call output path disagrees with its saved configuration')
                manifest = sources.read(manifest_name)
                if manifest.get('config_sha256') != metadata['sources'][config_name]:
                    raise ValueError('saved configuration hash does not match the manifest')
                expected = prompts[version].rstrip() + '\n\n<post>\n' + note['text'] + '\n</post>'
                request = [dict(prompt_id=call_id, text=expected)]
                if config.get('prompts') != request or manifest.get('prompts') != request:
                    raise ValueError('saved request does not match the prompt and input post')
                output = sources.read(output_name)
                if output.get('manifest_sha256') != metadata['sources'][manifest_name]:
                    raise ValueError('saved output manifest hash does not match')
                responses = output.get('responses')
                if (not isinstance(responses, list) or len(responses) != 1
                        or responses[0].get('prompt_id') != call_id
                        or not isinstance(responses[0].get('response'), str)):
                    raise ValueError('saved output does not bind exactly one call')
                raw = responses[0]['response']
                parsed = _json(raw)
                subjects = parsed.get('subjects')
                if (not isinstance(subjects, list) or any(not isinstance(subject, dict)
                        or not isinstance(subject.get('subject'), str) for subject in subjects)):
                    raise ValueError('saved answer has no usable final subject list')
                digest = _sha(raw.encode())
                receipt_name = str(directory/'run/results.jsonl')
                receipt_bytes = sources.raw(sources.local(receipt_name), receipt_name)
                receipts = [_json(line) for line in receipt_bytes.splitlines() if line.strip()]
                if not receipts:
                    raise ValueError('saved call has no receipts')
                final = receipts[-1]
                if (final.get('status') != 'succeeded' or final.get('final_output_raw') != raw
                        or final.get('final_output_sha256') != digest
                        or final.get('manifest_sha256') != metadata['sources'][manifest_name]
                        or final.get('prompt_sha256') != _sha(expected.encode())):
                    raise ValueError('saved final answer does not match its receipt')
                if keys:
                    key = key_by_call[call_id]
                    rid = key['review_id']
                    for field, expected_value in (('note', short), ('note_id', short),
                                                  ('prompt', version), ('version', version),
                                                  ('trial', call['trial'])):
                        if field not in key:
                            continue
                        same = (isinstance(key[field], str) and key[field].lower() == expected_value.lower()
                                if isinstance(expected_value, str) else key[field] == expected_value)
                        if not same:
                            raise ValueError('review key disagrees with its saved call')
                    view = views[rid]
                    if (view.get('note', view.get('note_id')) not in (short, note['note_id'])
                            or view.get('subjects') != [subject['subject'] for subject in subjects]
                            or 'text' in view and view['text'] != note['text']
                            or 'raw_sha256' in key and key['raw_sha256'] != digest):
                        raise ValueError('reviewed subjects do not match the saved answer')
                    assessment = judgments[rid]
                else:
                    assessment = judgments[call_id]
                    if assessment.get('id') != short:
                        raise ValueError('fresh assessment is bound to a different input post')
                if any(field in assessment and assessment[field] not in (short, note['note_id'])
                       for field in ('note', 'note_id')):
                    raise ValueError('assessment is bound to a different input post')
                expected_count = assessment.get('subjects_reviewed', assessment.get('subject_count'))
                if expected_count is not None and expected_count != len(subjects):
                    raise ValueError('assessment subject count does not match the saved answer')
                for field in ('accepted_subject_indices', 'reviewed_subject_indices',
                              'fidelity_accepted_subject_indices', 'definite_error_indices'):
                    if field in assessment and any(type(index) is not int or not 1 <= index <= len(subjects)
                                                   for index in assessment[field]):
                        raise ValueError('assessment has an out-of-range subject reference')
                settings = {key: value for data in (config, manifest) for key, value in data.items()
                            if key in _SETTINGS}
                setting_id = _sha(json.dumps(settings, sort_keys=True, separators=(',', ':')).encode())
                metadata['settings'][setting_id] = settings
                original_by_call[call_id] = dict(note_id=note['note_id'], short_label=short)
                counts['calls'] += 1
                counts['subjects'] += len(subjects)
                yield dict(call_id=call_id, note_id=note['note_id'], short_label=short,
                           version=version, trial=call['trial'], output=raw,
                           output_sha256=digest, settings_ref=setting_id,
                           request_sha256=_sha(expected.encode()),
                           attempts=len(receipts), status=final['status'])

        def used_inputs():
            used = {}
            for call in calls.values():
                short = call.get('note', call.get('note_id'))
                note = notes[short]
                previous = used.setdefault(note['note_id'], dict(note_id=note['note_id'],
                    text=note['text'], short_labels=[]))
                if previous['text'] != note['text']:
                    raise ValueError('one canonical note ID has conflicting source text')
                if short not in previous['short_labels']:
                    previous['short_labels'].append(short)
            counts['posts'] = len(used)
            yield from used.values()

        def assessments():
            for identity, assessment in judgments.items():
                call_id = keys[identity]['id'] if keys else identity
                yield dict(type='assessment', call_id=call_id, **original_by_call[call_id],
                    **attribution, review_id=identity if keys else None,
                    assessment={key: value for key, value in assessment.items() if key in _ASSESSMENT})
            for interpretation in review.get('interpretation_notes', []):
                refs = interpretation.get('review_ids', [interpretation.get('review_id')])
                if not keys or not refs or any(ref not in keys for ref in refs):
                    raise ValueError('orphaned shared review interpretation')
                yield dict(type='interpretation', call_ids=[keys[ref]['id'] for ref in refs],
                           review_ids=refs, **attribution,
                           assessment={key: value for key, value in interpretation.items()
                                       if key in {'subjects', 'note'}})

        def results():
            yield _summary(summary)
            sources.check()
            metadata['source_snapshot_sha256'] = _sha(json.dumps(
                metadata['sources'], sort_keys=True, separators=(',', ':')).encode())

        return shared('publication_files').write_publication(destination, metadata, {
            'inputs.jsonl': used_inputs(), 'answers.jsonl': answers(),
            'judgments.jsonl': assessments(), 'results.jsonl': results()})
