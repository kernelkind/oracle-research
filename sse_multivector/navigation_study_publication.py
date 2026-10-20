"""Offline publication of fixed navigation diagnostics and saved final analyses."""
import hashlib
import json
import math
from pathlib import Path

from . import mask_goal_publication as mask


_OPERATIONAL = {'snapshot', 'rendered', 'token_ids', 'input_ids', 'wordpiece_ranges',
    'session_id', 'thread_id', 'execution_command', 'working_directory',
    'quota_remaining_percent_before_run', 'wrap_up_signal_percent_remaining',
    'authorization', 'authorization_header', 'request_id', 'generation_id'}


def _require(condition, message):
    if not condition:
        raise ValueError('navigation study publication: ' + message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _binding(value):
    return {key: value[key] for key in ('path', 'sha256')}


def _clean(value, sources):
    def filtered(item):
        if isinstance(item, dict):
            return {key: filtered(child) for key, child in item.items() if key not in _OPERATIONAL}
        if isinstance(item, list):
            return [filtered(child) for child in item]
        return item
    return mask._project(filtered(value), sources)


def _items(sources, declaration):
    import ijson
    with sources.stream(declaration['path']) as stream:
        yield from ijson.items(stream, 'item', use_float=True)


def _jsonl(sources, declaration):
    return [json.loads(line) for line in sources.raw(declaration['path']).splitlines() if line.strip()]


def prepare(sources, selection, metadata):
    kind = selection['kind']
    _require(kind in {'gliclass', 'rse', 'lmms', 'lmms-pos'}, 'unsupported native diagnostic')
    helper = Path(mask.__file__)
    metadata['exporter_sources']['sse_multivector/' + helper.name] = _sha(helper.read_bytes())
    counts = dict(input_cases=0, score_records=0, measurements=0, analysis_records=0,
                  judgment_records=0, empty_rankings=0)
    metadata.update(kind=kind, historical=True, recorded_status='completed', counts=counts,
        execution_status='not_recorded', limitations=selection.get('limitations', []),
        input=dict(subject_prompt_versions=[], generated_subjects_deprecated=None,
                   raw_posts_deprecated=False, subject_provenance_status=(
                       'not_applicable' if kind == 'rse' else 'unknown'),
                   status='Historical diagnostic evidence; not current-pipeline validation.'))
    config = sources.read(selection['configuration']['path'])
    source_inputs = sources.read(selection['inputs']['path'])
    _require(isinstance(source_inputs, list) and source_inputs, 'saved inputs must be a nonempty array')
    identifier = 'id' if kind == 'rse' else 'row'
    by_id = {row[identifier]: row for row in source_inputs}
    input_order = list(by_id)
    _require(len(by_id) == len(source_inputs), 'duplicate saved input identity')
    declared_input_hash = config.get('inputs_sha256', config.get('input_sha256'))
    if kind != 'lmms-pos':
        _require(declared_input_hash == selection['inputs']['sha256'], 'configuration input hash differs')
    producer = selection.get('producer')
    if producer:
        _require(config.get('runner_sha256', config.get('code_sha256')) == producer['sha256'],
                 'saved producer hash differs')
    if selection.get('helper'):
        _require(config.get('helper_sha256') == selection['helper']['sha256'], 'saved helper hash differs')
    reference = selection.get('existing_inputs')
    published = {}
    if reference:
        published = {row[identifier]: row for row in _jsonl(sources, reference)}
        _require(len(published) == reference['rows'], 'existing input record count differs')
    grounding = selection.get('existing_grounding')
    aliases = {}
    if grounding:
        records = _jsonl(sources, grounding)
        aliases = {row['row']: row for row in records}
        _require(len(aliases) == grounding['rows'], 'existing canonical record count differs')
    metadata['references'] = {name: dict(publication=value['publication'], source=_binding(value))
        for name, value in (('descriptors', reference), ('grounding', grounding)) if value}
    metadata['input']['source'] = _binding(selection['inputs'])
    inputs = [dict(type='study_parameters', source=_binding(selection['configuration']),
                   data=_clean(config, sources))]
    for row in source_inputs:
        key = row[identifier]
        if reference:
            expected = {name: row[name] for name in ('id', 'case', 'domain', 'wording', 'role',
                        'subject', 'note', 'row') if name in row}
            expected['description'] = row['text']
            _require(published.get(key) == expected, 'existing descriptor/post input differs')
            data = dict(input_id=key, descriptor_reference='descriptors')
            if kind == 'rse':
                _require(row['model_input'] == row['text'], 'saved RSE input is not the plain description')
            elif grounding:
                canonical = aliases.get(row['canonical_row'])
                matched = [alias for alias in canonical['aliases'] if alias['short_id'] in row['alias_ids']] if canonical else []
                _require(len(matched) == len(row['alias_ids']) and all(
                    alias['subject'] == row['subject'] and alias['fragments'] == row['fragments']
                    and alias['note_short_id'] == row['note'] for alias in matched),
                    'existing mask/alias grounding differs')
                data['grounding'] = dict(canonical_row=row['canonical_row'], alias_ids=row['alias_ids'])
            else:
                data['grounding'] = {name: row[name] for name in ('canonical_row', 'alias_ids', 'fragments') if name in row}
        else:
            data = _clean(row, sources)
        inputs.append(dict(type='case_input', data=data))
    counts['input_cases'] = len(source_inputs)
    for declaration in selection.get('parameters', []):
        inputs.append(dict(type='study_parameters', source=_binding(declaration),
                           data=_clean(sources.read(declaration['path']), sources)))
    if selection.get('candidates'):
        candidates = sources.read(selection['candidates']['path'])
        inputs.append(dict(type='category_candidates', source=_binding(selection['candidates']), data=candidates))
    if selection.get('encoder_words'):
        words = sources.read(selection['encoder_words']['path'])
        _require([row['row'] for row in words] == list(by_id), 'encoder word input order differs')
        for row in words:
            _require(row['subject'] == by_id[row['row']]['subject'], 'encoder description differs')
            for word in row['words']:
                _require(row['subject'][word['start_char']:word['end_char']] == word['text'],
                         'encoder word offset differs')
            inputs.append(dict(type='encoder_words', source=_binding(selection['encoder_words']),
                               row=row['row'], words=row['words'], targets=row['targets']))
    previous_targets = None
    if kind == 'lmms-pos':
        previous = selection['source_scores']
        _require(config['source_hashes']['scores'] == previous['sha256'], 'reused LMMS score hash differs')
        previous_targets = sources.read(previous['path'])
        metadata['reuse'] = dict(source_experiment=selection['source_experiment'],
                               source_scores=_binding(previous), model_encoding=False)
    judgments, analyses = [], []
    for declaration in selection.get('records', []):
        value = sources.read(declaration['path'])
        row = dict(type=declaration['role'], source=_binding(declaration), data=_clean(value, sources))
        if declaration['role'] in {'judgments', 'assessment'}:
            judgments.append(row)
            counts['judgment_records'] += 1
        else:
            analyses.append(row)
            counts['analysis_records'] += 1
    if selection.get('analysis_binding'):
        analysis_config = sources.read(selection['analysis_binding']['path'])
        _require(analysis_config['scores_source']['sha256'] == selection['scores']['sha256']
                 and analysis_config['inputs_sha256'] == selection['inputs']['sha256']
                 and analysis_config['candidates_sha256'] == selection['candidates']['sha256'],
                 'final membership analysis source binding differs')

    def results():
        seen = set()
        for ordinal, row in enumerate(_items(sources, selection['scores'])):
            counts['score_records'] += 1
            if kind == 'gliclass':
                _require(set(row) == {'row', 'text', 'condition', 'labels', 'rendered', 'token_ids', 'scores'},
                         'unsupported native classification score shape')
                _require(row['row'] in by_id and row['text'] == by_id[row['row']]['subject'],
                         'classification score input differs')
                _require(row['condition'] in {'joint', 'reversed', 'single'}
                         and isinstance(row['labels'], list) and len(set(row['labels'])) == len(row['labels'])
                         and [score['label'] for score in row['scores']] == row['labels'],
                         'native category order differs')
                key = (row['row'], row['condition'], tuple(row['labels']))
                _require(key not in seen, 'duplicate native classification request')
                seen.add(key)
                for value in row['scores']:
                    _require(set(value) == {'label', 'logit', 'score', 'accepted'}
                             and all(type(value[name]) in (int, float) and math.isfinite(value[name])
                                     for name in ('logit', 'score'))
                             and type(value['accepted']) is bool, 'malformed native classification measurement')
                counts['measurements'] += len(row['scores'])
                yield dict(type='classification_scores', row=row['row'],
                           condition=row['condition'], scores=row['scores'])
            elif kind == 'rse':
                _require(set(row) == {'first', 'second', 'cosine', 'entailment'}, 'unsupported RSE pair shape')
                _require(ordinal < len(input_order)**2 and row['first'] == input_order[ordinal//len(input_order)]
                         and row['second'] == input_order[ordinal%len(input_order)], 'ordered RSE pair identity differs')
                _require(all(type(row[name]) in (int, float) and math.isfinite(row[name])
                             for name in ('cosine', 'entailment')), 'nonfinite RSE measurement')
                counts['measurements'] += 2
                yield dict(type='ordered_pair', **row)
            else:
                required = {'row', 'note', 'subject', 'word_index', 'word', 'matches'}
                extra = {'candidates'} if kind == 'lmms' else {'candidate_keys'}
                _require(set(row) == required | extra, 'unsupported LMMS result shape')
                _require(row['row'] in by_id and all(row[name] == by_id[row['row']][name]
                         for name in ('subject', 'note')), 'LMMS source context differs')
                word = row['word']
                _require(row['subject'][word['start_char']:word['end_char']] == word['text'],
                         'LMMS source word offset differs')
                key = (row['row'], row['word_index'])
                _require(key not in seen, 'duplicate LMMS target identity')
                seen.add(key)
                if previous_targets is not None:
                    _require(ordinal < len(previous_targets) and all(row[name] == previous_targets[ordinal][name]
                        for name in required - {'matches'}), 'reused LMMS target context differs')
                    matches = {'surface_pos': row['matches']}
                else:
                    _require(set(row['matches']) == {'saved', 'surface', 'unrestricted'}, 'LMMS conditions differ')
                    matches = row['matches']
                for values in matches.values():
                    _require(isinstance(values, list) and len(values) <= 5, 'invalid LMMS ranking')
                    for value in values:
                        _require(set(value) == {'key', 'cosine', 'synset', 'definition'}
                                 and type(value['cosine']) in (int, float) and math.isfinite(value['cosine']),
                                 'invalid LMMS sense score')
                    counts['measurements'] += len(values)
                    counts['empty_rankings'] += not values
                yield dict(type='sense_matches', **row)
        if kind == 'rse':
            _require(counts['score_records'] == len(by_id)**2, 'incomplete ordered RSE score matrix')
        if previous_targets is not None:
            _require(counts['score_records'] == len(previous_targets), 'incomplete reused LMMS targets')
        for key, expected in selection.get('expected_counts', {}).items():
            _require(counts[key] == expected, 'saved ' + key + ' count differs')
        yield from analyses

    return {'inputs.jsonl': inputs, 'answers.jsonl': [],
            'judgments.jsonl': judgments, 'results.jsonl': results()}
