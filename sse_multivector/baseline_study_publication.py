"""Publish final baseline evidence through verified extracted source counterparts.

The maintained selection records the independently audited archive/member map.
Export verifies those hash bindings; it does not decode or copy the archives.
"""
import itertools
import struct

import ijson
from ijson.common import ObjectBuilder


_PRIVATE = {'codex_binary', 'codex_home', 'api_key', 'auth_file', 'authentication',
            'credentials', 'access_token', 'refresh_token', 'session_id', 'thread_id',
            'argv', 'stderr', 'stdout', 'working_directory'}
_HEADER = {'schema_version', 'diagnostic_id', 'proposal_sha256', 'note_count',
           'subject_count', 'dimensions', 'rules', 'pair_counts', 'distributions',
           'nearest_overall_from_same_note', 'nearest_overall_from_other_note'}
_SUBJECT = {'ordinal', 'note_id', 'subject_id', 'label', 'fragments',
            'selected_token_indices', 'raw_norm', 'nearest_overall'}


def _require(condition, message):
    if not condition:
        raise ValueError('baseline publication: ' + message)


def _safe(value):
    """Keep scientific parameters and hashes, excluding native local locations."""
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()
                if key not in _PRIVATE and not key.endswith(('_path', '_directory'))}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    return value


def _mask(text, fragments, spans):
    _require(isinstance(fragments, list) and isinstance(spans, list)
             and len(fragments) == len(spans), 'mask fragment/span count differs')
    raw, end = text.encode('utf-8'), 0
    for fragment, span in zip(fragments, spans):
        _require(isinstance(span, list) and len(span) == 2
                 and all(type(number) is int for number in span), 'invalid source byte span')
        start, stop = span
        if isinstance(fragment, dict):
            occurrence, fragment = fragment.get('occurrence'), fragment.get('text')
            _require(type(occurrence) is int and 0 < occurrence <= len(text)
                     and isinstance(fragment, str) and fragment, 'invalid fragment occurrence')
            position = -1
            for _ in range(occurrence):
                position = text.find(fragment, position+1)
                _require(position >= 0, 'fragment occurrence is absent')
            _require([len(text[:position].encode()), len(text[:position+len(fragment)].encode())] == span,
                     'fragment occurrence differs from frozen request span')
        _require(end <= start < stop <= len(raw) and isinstance(fragment, str)
                 and raw[start:stop] == fragment.encode('utf-8'), 'mask differs from exact source bytes')
        end = stop


def _crec(sources, selection, read, metadata):
    posts, generation, answers = read('posts'), read('generation'), read('answers')
    mapping, vm = read('vector_map'), read('vector_manifest')
    segments, sm = read('segments'), read('segment_manifest')
    bindings = selection['members']
    digest = lambda name: bindings[name]['member_sha256']
    _require(answers.get('schema_version') in (2, 3) and answers.get('manifest_sha256') == digest('generation')
             and generation.get('input_sha256') == digest('posts'), 'assembled answer/input manifest differs')
    post_rows = posts.get('notes', [])
    by_note = {row['note_id']: row['text'] for row in post_rows}
    _require(len(by_note) == len(post_rows) and [row['note_id'] for row in answers['notes']]
             == [row['note_id'] for row in post_rows], 'assembled answer note order/identity differs')
    final = {row['note_id']: row for row in answers['notes']}
    _require(mapping.get('generation_output_sha256') == digest('answers')
             and vm.get('generation_output_sha256') == digest('answers')
             and vm.get('files', {}).get('vector-map.json', {}).get('sha256') == digest('vector_map')
             and sm.get('vector_manifest_sha256') == digest('vector_manifest')
             and sm.get('vector_map_sha256') == digest('vector_map')
             and sm.get('files', {}).get('segments.json', {}).get('sha256') == digest('segments'),
             'final segment/vector source binding differs')
    vectors = mapping['vectors']
    _require(len(vectors) == mapping.get('vector_count') == vm.get('vector_count')
             == segments.get('source_vector_count'), 'final vector counts differ')
    expected = [(row['note_id'], index, answer) for row in answers['notes']
                for index, answer in enumerate(row['takeaways'])]
    _require(len(expected) == len(vectors), 'accepted answer/vector count differs')
    inputs = [{'type': 'post', **row} for row in post_rows]
    by_supplied = {key: [] for key in by_note}
    for ordinal, (vector, (note_id, index, answer)) in enumerate(zip(vectors, expected)):
        _require(vector['ordinal'] == ordinal and vector['note_id'] == note_id
                 and vector['takeaway_index'] == index and vector['takeaway'] == answer['text']
                 and vector['prominence'] == answer['prominence']
                 and vector['fragments'] == answer['fragments'], 'vector differs from assembled final answer')
        _mask(by_note[note_id], answer['fragments'], vector['byte_spans'])
        by_supplied[note_id].append({'subject_id': vector['subject_id'], 'byte_spans': vector['byte_spans']})
        inputs.append({'type': 'mask_identity', **{key: vector[key] for key in (
            'ordinal', 'subject_id', 'note_id', 'takeaway_index', 'byte_spans')}})
    if 'request' in bindings:
        request, encoder = read('request'), read('encoder')
        expected_notes = [{**note, 'subjects': by_supplied[note['note_id']]}
                          for note in post_rows if by_supplied[note['note_id']]]
        _require(encoder.get('request_sha256') == digest('request')
                 and request.get('proposal_sha256') == digest('answers')
                 and request.get('notes') == expected_notes, 'encoder request differs from accepted source masks')
    floor = segments['pairwise_min_cosine']
    _require(sm.get('pairwise_min_cosine_bits') == struct.unpack('<Q', struct.pack('<d', floor))[0]
             and sm.get('selection_rule') == segments.get('selection_rule'), 'final floor/selection rule differs')
    results, assigned = [], set()
    for segment in segments['segments']:
        ordinals = segment['vector_ordinals']
        _require(len(ordinals) == len(set(ordinals)) and not assigned.intersection(ordinals)
                 and all(type(number) is int and 0 <= number < len(vectors) for number in ordinals),
                 'invalid final segment membership')
        _require(segment['members'] == [vectors[number] for number in ordinals]
                 and set(segment['note_ids']) == {vectors[number]['note_id'] for number in ordinals},
                 'segment member text/identity differs from final source map')
        assigned.update(ordinals)
        results.append({'type': 'segment', **{key: value for key, value in segment.items() if key != 'members'}})
    _require(segments.get('segment_count') == len(results)
             and segments.get('represented_vector_count') == len(assigned)
             and segments.get('represented_note_count') == len({vectors[i]['note_id'] for i in assigned}),
             'final segment accounting differs')
    metadata['parameters']['segment_selection'] = {key: value for key, value in segments.items() if key != 'segments'}
    baseline = ({key: bindings['baseline_'+key]['source'] for key in ('posts', 'answers', 'generation')}
                if 'baseline_posts' in bindings else None)
    reused = set()
    if baseline:
        previous_posts = sources.read(baseline['posts']['path'])
        previous_answers = sources.read(baseline['answers']['path'])
        previous_generation = sources.read(baseline['generation']['path'])
        source = generation.get('reuse_source', {})
        _require(source.get('input_sha256') == baseline['posts']['sha256']
                 and source.get('output_sha256') == baseline['answers']['sha256']
                 and source.get('manifest_sha256') == baseline['generation']['sha256']
                 and previous_answers.get('manifest_sha256') == baseline['generation']['sha256']
                 and previous_generation.get('input_sha256') == baseline['posts']['sha256'],
                 'reuse source hash chain differs')
        prior_text = {row['note_id']: row['text'] for row in previous_posts['notes']}
        prior_answers = {row['note_id']: row for row in previous_answers['notes']}
        reused = set(by_note) & set(prior_text)
        _require(all(by_note[key] == prior_text[key] and final[key] == prior_answers[key] for key in reused),
                 'reused note/assembled answer differs')
        stages = 1 + int('prominence' in generation)
        jobs = lambda ids: sum(1 + stages*len(final[key]['takeaways']) for key in ids)
        metadata['reuse'] = {'source': baseline, 'reused_notes': len(reused),
            'new_notes': len(by_note)-len(reused), 'reused_final_jobs': jobs(reused),
            'new_final_jobs': jobs(set(by_note)-reused),
            'status': 'Reused final answers are preserved baseline evidence, not new independent samples; job counts exclude superseded attempts.'}
    outputs = [{'representation': 'parsed_assembled_answer', 'note_id': row['note_id'],
                'execution': 'reused' if row['note_id'] in reused else 'not_recorded', 'data': row}
               for row in answers['notes']]
    metadata['counts'] = {'notes': len(by_note), 'takeaways': len(vectors), 'segments': len(results)}
    return inputs, outputs, results


def _geometry_header(sources, path):
    """Select headers/identities in one pass without building repeated rankings."""
    header, subjects, subject = {}, [], None
    builder, depth, destination, field = None, 0, None, None
    with sources.stream(path) as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if builder is not None:
                builder.event(event, value)
                depth += (event in ('start_map', 'start_array')) - (event in ('end_map', 'end_array'))
                if not depth:
                    destination[field] = builder.value
                    builder = None
            elif prefix == 'subjects.item' and event == 'start_map':
                subject = {}
            elif prefix == 'subjects.item' and event == 'end_map':
                subjects.append(subject)
                subject = None
            elif event != 'map_key' and (prefix in _HEADER or (
                    prefix.startswith('subjects.item.') and prefix.removeprefix('subjects.item.') in _SUBJECT)):
                destination = header if prefix in _HEADER else subject
                field = prefix if prefix in _HEADER else prefix.removeprefix('subjects.item.')
                _require(destination is not None and field not in destination, 'duplicate diagnostic field')
                builder, depth = ObjectBuilder(), int(event in ('start_map', 'start_array'))
                builder.event(event, value)
                if not depth:
                    destination[field] = builder.value
                    builder = None
    _require(_HEADER <= header.keys() and header['schema_version'] == 1,
             'unsupported geometry diagnostic header')
    return header, subjects


def _geometry(sources, selection, read, metadata):
    request, manifest = read('request'), read('manifest')
    encoder = read('encoder')
    _require(encoder.get('request_sha256') == selection['members']['request']['member_sha256']
             and encoder.get('checkpoint_sha256') == manifest.get('worker', {}).get('checkpoint_sha256'),
             'encoder/request source binding differs')
    declaration = selection['members']['analysis']
    _require(manifest.get('request_sha256') == selection['members']['request']['member_sha256']
             and manifest.get('files', {}).get('analysis.json', {}).get('sha256') == declaration['member_sha256'],
             'geometry analysis/request source binding differs')
    header, subjects = _geometry_header(sources, declaration['source']['path'])
    _require(header['proposal_sha256'] == request.get('proposal_sha256') == manifest.get('proposal_sha256')
             and header['subject_count'] == len(subjects) == manifest.get('subject_count')
             and header['note_count'] == len(request['notes']) == manifest.get('note_count')
             and header['dimensions'] == manifest.get('dimensions'), 'geometry source accounting differs')
    proposal_binding = selection.get('proposal')
    proposal = sources.read(proposal_binding['path']) if proposal_binding else read('proposal')
    proposal_sha = proposal_binding['sha256'] if proposal_binding else selection['members']['proposal']['member_sha256']
    _require(header['proposal_sha256'] == proposal_sha, 'geometry proposal hash differs')
    originals = {(note['note_id'], item['subject_id']): item for note in proposal['notes'] for item in note['subjects']}
    supplied = {(note['note_id'], item['subject_id']): (note['text'], item['byte_spans'])
                for note in request['notes'] for item in note['subjects']}
    _require(len(supplied) == len(subjects), 'geometry mask identity count differs')
    inputs = [{'type': 'post', 'note_id': note['note_id'], 'text': note['text']} for note in request['notes']]
    for ordinal, subject in enumerate(subjects):
        key = subject['note_id'], subject['subject_id']
        _require(_SUBJECT <= subject.keys() and subject['ordinal'] == ordinal
                 and key in supplied and key in originals
                 and subject['label'] == originals[key]['label']
                 and subject['fragments'] == originals[key]['fragments'], 'geometry subject/source identity differs')
        text, spans = supplied[key]
        _mask(text, subject['fragments'], spans)
        inputs.append({'type': 'diagnostic_subject', **subject, 'byte_spans': spans})
    metadata['parameters']['diagnostic'] = header
    metadata['parameters']['proposal'] = _safe({key: value for key, value in proposal.items() if key != 'notes'})
    if selection.get('reused_answers'):
        metadata['reused_answers'] = selection['reused_answers']
    metadata['excluded_redundant_views'] = ['subjects[].cross_note_ranking', 'subjects[].top_cross_note_neighbors']
    metadata['counts'] = {'notes': len(request['notes']), 'subjects': len(subjects), 'pairs': 0}

    def results():
        expected = iter(itertools.combinations(range(len(subjects)), 2))
        total, same = 0, 0
        with sources.stream(declaration['source']['path']) as stream:
            for row in ijson.items(stream, 'pairs.item', use_float=True):
                left, right = row['left_ordinal'], row['right_ordinal']
                _require((left, right) == next(expected, None), 'diagnostic pair order/coverage differs')
                for side, ordinal in (('left', left), ('right', right)):
                    _require(row[side+'_note_id'] == subjects[ordinal]['note_id']
                             and row[side+'_subject_id'] == subjects[ordinal]['subject_id'],
                             'diagnostic pair subject identity differs')
                _require(type(row['same_note']) is bool and row['same_note'] == (
                    subjects[left]['note_id'] == subjects[right]['note_id']), 'diagnostic pair note relation differs')
                total += 1
                same += row['same_note']
                result = {'type': 'pair', **{key: row[key] for key in (
                    'left_ordinal', 'right_ordinal', 'cosine', 'same_note')}}
                if 'token_overlap' in row:
                    result['token_overlap'] = row['token_overlap']
                yield result
        _require(next(expected, None) is None and header['pair_counts'] == {
            'all': total, 'same_note': same, 'cross_note': total-same}, 'diagnostic pair accounting differs')
        metadata['counts']['pairs'] = total
    return inputs, [], results()


def prepare(sources, selection, metadata):
    members = selection.get('members', {})
    _require(selection.get('kind') in ('crec', 'geometry') and members, 'unsupported baseline selection')
    for declaration in members.values():
        _require(declaration['source']['sha256'] == declaration['member_sha256'],
                 'archive member/counterpart hash differs')
    metadata.update(archive=selection['archive'], member_sources=members,
        archive_binding_status='Verifies the audited archive/member/counterpart hash bindings without decoding archives; member mapping was established and frozen in the maintained selection.',
        subject_provenance={'versions': [], 'lineage_status': 'AS version unknown; legacy TP or manual subject wording is not an AS version.',
            'generated_subjects_deprecated': None, 'raw_posts_deprecated': False}, parameters={})
    cache = {}
    def read(name):
        if name not in cache:
            cache[name] = sources.read(members[name]['source']['path'])
        return cache[name]
    data = {'posts', 'answers', 'vector_map', 'segments', 'analysis', 'request', 'proposal',
            'baseline_posts', 'baseline_answers'}
    for name in members.keys()-data:
        metadata['parameters'][name] = _safe(read(name))
    inputs, answers, results = (_crec if selection['kind'] == 'crec' else _geometry)(
        sources, selection, read, metadata)
    return {'inputs.jsonl': iter(inputs), 'answers.jsonl': iter(answers),
            'judgments.jsonl': iter(()), 'results.jsonl': iter(results)}
