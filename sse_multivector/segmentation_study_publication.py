"""Publish frozen real-note segment selections without working vector arrays."""
import hashlib
import json
from pathlib import Path
import re

import ijson
from ijson.common import ObjectBuilder

from . import real_note_segmentation as segmentation
from . import worker


_PRIVATE = {'auth_file', 'authentication', 'credentials', 'api_key', 'account',
            'account_id', 'codex_home', 'codex_binary', 'argv', 'stderr',
            'stdout', 'stdout_jsonl', 'thread_id', 'session_id', 'cli',
            'checkpoint_path', 'worker_path', 'base_model_artifact_path'}
_LOCAL = re.compile(r'(?<![:\w])/(?:home|Users|tmp|dev/shm|mnt|nix|private|run|root|opt|var)/[^\s\"\'<>\]\[(){},;`]*')
_LITERAL = {'text', 'subject', 'context', 'fragments', 'raw_subject', 'raw_mask',
            'raw_fragments', 'comment', 'user_response', 'response_verbatim'}
_VECTOR_FIELDS = {'note_short_id', 'ordinal', 'reviewed_note_index',
    'reviewed_subject_id', 'reviewed_subject_index', 'selected_token_ids',
    'selected_token_indices', 'short_id',
    'token_count', 'vector_id', 'worker_subject_id'}
_HIERARCHY = ('artifact.result.algorithm_result.condensed_tree',
              'artifact.result.algorithm_result.single_linkage_tree',
              'artifact.result.alias_groups', 'artifact.result.canonical_unique_ids')


def _require(condition, message):
    if not condition:
        raise ValueError('segmentation publication: ' + message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode()


def _binding(value):
    return {key: value[key] for key in ('path', 'sha256')}


def _portable(text):
    def replace(match):
        value = match.group()
        if '/oracle-mvp/' in value:
            return value.split('/oracle-mvp/', 1)[1]
        return 'local-artifact:' + Path(value).name + '[sha256:' + _sha(value.encode()) + ']'
    return _LOCAL.sub(replace, text)


def _project(value, evidence, field=None):
    """Preserve scientific objects and decisions, replacing repeated source text."""
    if isinstance(value, dict):
        if {'vector_id', 'text', 'note_id'} <= value.keys():
            original = evidence.get(value['vector_id'])
            _require(original is not None, 'review names an unknown vector')
            _require(value['text'] == original['text'] and value['note_id'] == original['note_id'],
                     'review vector source text/identity differs')
            if 'byte_spans' in value:
                _require(value['byte_spans'] == original['byte_spans'],
                         'review vector mask spans differ')
            value = {key: item for key, item in value.items()
                     if key not in {'text', 'note_id', 'byte_spans'}}
        result = {}
        for key, item in value.items():
            if key in _PRIVATE:
                continue
            public_key = _portable(key)
            _require(public_key not in result, 'portable scientific field collision')
            result[public_key] = _project(item, evidence, key)
        return result
    if isinstance(value, list):
        return [_project(item, evidence, field) for item in value]
    if isinstance(value, str) and field not in _LITERAL:
        return _portable(value)
    return value


def _response(sources, declaration):
    wanted = {'artifact.manifest', 'artifact.result.fine_output'}
    if declaration.get('full_hierarchy'):
        wanted.update(_HIERARCHY)
    values, builder, depth, name = {}, None, 0, None
    # One complete parse, including discarded dense arrays; memory follows final fields.
    with sources.stream(declaration['response']['path']) as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if builder is not None:
                builder.event(event, value)
                depth += (event in ('start_map', 'start_array')) - (event in ('end_map', 'end_array'))
                if depth == 0:
                    values[name] = builder.value
                    builder = None
            elif prefix in wanted and event != 'map_key':
                _require(prefix not in values, 'duplicate final response field')
                name, builder = prefix, ObjectBuilder()
                builder.event(event, value)
                depth = int(event in ('start_map', 'start_array'))
                if not depth:
                    values[name] = builder.value
                    builder = None
    _require(wanted <= values.keys(), 'saved response omits selected final fields')
    return values


def prepare(sources, selection, metadata):
    inputs, answers, judgments, results = [], [], [], []
    datasets, runs, evidence, notes = {}, {}, {}, {}
    versions, reused = set(), []
    for module in (segmentation, worker):
        path = Path(module.__file__)
        stat = path.stat()
        reused.append((path, (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)))
        metadata['exporter_sources']['sse_multivector/' + path.name] = _sha(path.read_bytes())
    for declaration in selection.get('datasets', []):
        identifier = declaration['id']
        _require(identifier not in datasets, 'duplicate input dataset')
        reviewed = sources.read(declaration['reviewed_input']['path'])
        mapping = sources.read(declaration['vector_map']['path'])
        manifest = sources.read(declaration['manifest']['path'])
        encoder = sources.read(declaration['encoder']['path'])
        segmentation._validate_encoder(encoder)
        package = sources.read(declaration['subject_package']['path'])
        version = package.get('version')
        _require(isinstance(version, str), 'subject package lacks a recorded version')
        versions.add(version)
        package_keys = ['reviewed_input', 'vector_map', 'manifest', 'encoder', 'subject_package']
        mask_version, mask_package = None, None
        if 'mask_package' in declaration:
            mask_package = sources.read(declaration['mask_package']['path'])
            mask_version = mask_package.get('version')
            _require(isinstance(mask_version, str), 'mask package lacks a recorded version')
            package_keys.append('mask_package')
        package_origins = {}
        for kind in ('subject', 'mask'):
            key = kind + '_package_origin'
            if key in declaration:
                origin = declaration[key]
                sources.raw(origin['path'])
                _require(origin['sha256'] == declaration[kind + '_package']['sha256'],
                         'upstream package origin differs from frozen copy')
                package_origins[kind] = _binding(origin)
        _, expected = segmentation._compile_inputs(reviewed, declaration['reviewed_input']['sha256'])
        vectors = mapping.get('vectors')
        _require(isinstance(vectors, list) and len(vectors) == len(expected['vectors'])
                 == manifest.get('vector_count') == mapping.get('vector_count'),
                 'vector map count differs from reviewed inputs')
        for name in (key for key in package_keys if key != 'manifest'):
            binding = declaration[name]
            entry = manifest.get('files', {}).get(Path(binding['path']).name, {})
            _require(entry.get('sha256') == binding['sha256'], 'vector manifest source hash differs')
        _require(mapping.get('dimensions') == manifest.get('dimensions') == encoder['model']['dimensions'],
                 'encoder/vector dimensions differ')
        _require(mapping.get('notes') == expected['notes'] and mapping.get('excluded') == expected['excluded'],
                 'vector map excluded inputs or note identity differs')
        references = []
        for note in reviewed['notes']:
            public = _project({key: value for key, value in note.items() if key != 'pubkey'}, {})
            ref = _sha(_compact(public))
            notes.setdefault(ref, {'type': 'reviewed_note', 'id': ref, 'data': public})
            references.append(ref)
        by_id = {}
        for actual, compiled in zip(vectors, expected['vectors']):
            _require(all(actual.get(key) == value for key, value in compiled.items()),
                     'vector identity/mask differs from compiled source inputs')
            vector_id = actual['vector_id']
            _require(vector_id not in by_id, 'duplicate vector identity')
            note = reviewed['notes'][actual['reviewed_note_index']]
            item = {'text': note['text'], 'note_id': note['note_id'], 'byte_spans': actual['byte_spans']}
            _require(vector_id not in evidence or evidence[vector_id] == item,
                     'same vector identity has conflicting source evidence')
            evidence[vector_id] = item
            by_id[vector_id] = actual
            public = {key: actual[key] for key in _VECTOR_FIELDS if key in actual}
            if 'reviewed_subjects' in actual:
                public['reviewed_subjects'] = [
                    {key: row[key] for key in _VECTOR_FIELDS if key in row}
                    for row in actual['reviewed_subjects']]
            inputs.append({'type': 'vector_mapping', 'dataset': identifier,
                           'input_ref': references[actual['reviewed_note_index']], 'data': public})
        datasets[identifier] = {'vectors': by_id, 'declaration': declaration,
                                'reviewed': reviewed, 'manifest': manifest}
        inputs.append({'type': 'input_dataset', 'id': identifier, 'notes': references,
                       'sources': {key: _binding(declaration[key]) for key in package_keys},
                       'accounting': _project(reviewed.get('accounting', {}), evidence),
                       'provenance': _project(reviewed.get('provenance', {}), evidence),
                       'encoder': _project(encoder, evidence),
                       'vector_manifest': _project(manifest, evidence),
                       'upstream_package_role': 'Frozen upstream methods and prior validation; not new segmentation outcomes.',
                       'upstream_package_origins': package_origins,
                       'subject_package': _project(package, evidence),
                       'mask_package': _project(mask_package, evidence),
                       'subject_prompt_version': version, 'mask_prompt_version': mask_version})
    inputs[:0] = list(notes.values())
    for declaration in selection.get('runs', []):
        identifier, dataset_id = declaration['id'], declaration['dataset']
        _require(identifier not in runs and dataset_id in datasets, 'invalid selected run/dataset identity')
        values = _response(sources, declaration)
        manifest, fine = values['artifact.manifest'], values['artifact.result.fine_output']
        dataset = datasets[dataset_id]
        _require(isinstance(fine, dict) and set(fine) == {'segments', 'unassigned'}
                 and isinstance(fine['segments'], list) and isinstance(fine['unassigned'], list),
                 'unsupported final segment selection')
        _require(all(isinstance(group, list) and group for group in fine['segments']),
                 'invalid final segment membership')
        assigned = [member for group in fine['segments'] for member in group] + fine['unassigned']
        _require(all(isinstance(member, str) for member in assigned)
                 and len(assigned) == len(set(assigned))
                 and set(assigned) == set(dataset['vectors']), 'final selection does not partition input vectors')
        _require(manifest.get('source_vector_manifest_sha256') == dataset['declaration']['manifest']['sha256']
                 and manifest.get('vector_count') == len(assigned), 'response input manifest differs')
        _require(manifest.get('fine_output_sha256') == _sha(_compact(fine)),
                 'final selection content hash differs')
        run = {'type': 'segmentation', 'run_id': identifier, 'dataset': dataset_id,
               'source': _binding(declaration['response']), 'manifest': _project(manifest, evidence),
               'fine_output': fine}
        if declaration.get('full_hierarchy'):
            run['hierarchy'] = {name.rsplit('.', 1)[1]: values[name] for name in _HIERARCHY}
        runs[identifier] = run
        results.append(run)

    reviews = {}
    def review(binding, dataset_id, run_id=None, complete=False):
        key = (binding['path'], dataset_id)
        if key not in reviews:
            value = sources.read(binding['path'])
            _require(isinstance(value, dict) and isinstance(value.get('review_set'), str)
                     and isinstance(value.get('packets'), list), 'unsupported review packet set')
            packets = {}
            for packet in value['packets']:
                identifier = packet['packet']
                _require(identifier not in packets, 'duplicate review packet identity')
                _require(isinstance(packet.get('instances'), list) and packet['instances'],
                         'review packet has no source instances')
                for instance in packet['instances']:
                    _require(instance.get('vector_id') in datasets[dataset_id]['vectors'],
                             'review packet names a vector outside its input dataset')
                _project(packet, evidence)
                packets[identifier] = packet
            reviews[key] = (value, packets)
            inputs.append({'type': 'review_set', 'dataset': dataset_id, 'source': _binding(binding),
                           'data': _project(value, evidence)})
        value, packets = reviews[key]
        if run_id:
            _require(run_id in runs and runs[run_id]['dataset'] == dataset_id, 'review run binding differs')
            expected = {frozenset(group) for group in runs[run_id]['fine_output']['segments']}
            actual = {frozenset(row['vector_id'] for row in packet['instances']) for packet in packets.values()}
            _require(actual <= expected and (not complete or actual == expected),
                     'review packet memberships differ from selected final segments')
        return value, packets

    for declaration in selection.get('runs', []):
        if declaration.get('review'):
            review(declaration['review'], declaration['dataset'], declaration['id'], True)
    for declaration in selection.get('review_packets', []):
        review(declaration['source'], declaration['dataset'], declaration.get('run'),
               declaration.get('complete', False))
    for declaration in selection.get('records', []):
        value = sources.read(declaration['path'])
        if declaration.get('review'):
            packet_set, packets = review(declaration['review'], declaration['dataset'], declaration.get('run'))
            expected_set = packet_set['review_set']
            for key in ('review_set', 'source_review_set'):
                _require(value.get(key, expected_set) == expected_set,
                         'assessment review-set identity differs')
            for key in ('source_review_sha256', 'input_sha256'):
                _require(value.get(key, declaration['review']['sha256']) == declaration['review']['sha256'],
                         'assessment review-source hash differs')
            if isinstance(value.get('input'), dict):
                _require(value['input'].get('sha256') == declaration['review']['sha256']
                         and value['input'].get('review_set', expected_set) == expected_set,
                         'assessment review-source hash differs')
            for row in value.get('judgments', []) + value.get('assessments', []):
                _require(row.get('packet') in packets, 'assessment names an unknown review packet')
                instances = packets[row['packet']]['instances']
                vectors = {instance['vector_id'] for instance in instances}
                ids = {instance['instance'] for instance in instances}
                note_ids = {instance['note_id'] for instance in instances}
                for key, expected in (('reviewed_vector_ids', vectors),
                                      ('reviewed_instance_ids', ids), ('reviewed_note_ids', note_ids)):
                    if key in row:
                        _require(set(row[key]) <= expected, 'assessment reviewed identity differs')
                for key in ('instances', 'reviewed_instances'):
                    if isinstance(row.get(key), list):
                        for instance in row[key]:
                            _require((instance in ids) if isinstance(instance, str) else (
                                instance.get('instance') in ids and instance.get('vector_id') in vectors),
                                'assessment instance differs from original packet')
        row = {'role': declaration['role'], 'source': _binding(declaration),
               'data': _project(value, evidence)}
        (results if declaration['role'] in {'comparison', 'measurements', 'parameters'} else judgments).append(row)
    recorded, not_recorded = 0, 0
    for declaration in selection.get('user_reviews', []):
        value = sources.read(declaration['source']['path'])
        packet_set, packets = review(declaration['review'], declaration['dataset'], declaration.get('run'))
        _require(value.get('review_set') == packet_set['review_set']
                 and isinstance(value.get('judgments'), list), 'user review packet-set binding differs')
        decisions = {}
        for row in value['judgments']:
            identifier = row.get('packet')
            _require(identifier in packets and identifier not in decisions
                     and row.get('verdict') in {'valid', 'invalid', 'uncertain'}
                     and isinstance(row.get('comment', ''), str), 'invalid user review identity/verdict')
            decisions[identifier] = row
        for identifier in packets:
            decision = decisions.get(identifier)
            recorded += decision is not None
            not_recorded += decision is None
            judgments.append({'type': 'packet_review', 'actor': 'user',
                'review_set': packet_set['review_set'], 'packet': identifier,
                'status': 'recorded' if decision else 'not_recorded',
                'verdict': decision['verdict'] if decision else None,
                'comment': decision.get('comment', '') if decision else '',
                'source': _binding(declaration['source']),
                'review_source': _binding(declaration['review'])})
    known = [re.fullmatch(r'ASv(\d+)\.(\d+)(?:\.\d+)?', value) for value in versions]
    historical = [match is not None and tuple(map(int, match.groups())) < (6, 100)
                  for match in known]
    deprecated = True if any(historical) else (False if known and all(known) else None)
    metadata.update(subject_provenance={'versions': sorted(versions),
        'generated_subjects_deprecated': deprecated, 'raw_posts_deprecated': False},
        input_status='Final curated/encoding-admitted subjects and masks, including excluded/unresolved records; not untouched model answers.',
        authored_context={'role': 'Separate authored research records and subsequent corrections.',
            'status': 'Structured user reviews retain original saved states; later chat corrections remain in the separate authored records and are not applied to frozen responses or counted as new structured judgments.',
            'sources': [_binding(item) for item in selection.get('authored_context', [])]},
        counts={'runs': len(runs), 'datasets': len(datasets), 'reviewed_notes': len(notes),
                'recorded_user_judgments': recorded, 'user_outcomes_not_recorded': not_recorded})

    def checked_results():
        yield from results
        for path, stamp in reused:
            stat = path.stat()
            _require((stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) == stamp,
                     'reused source validator changed during publication')
    return {'inputs.jsonl': iter(inputs), 'answers.jsonl': iter(answers),
            'judgments.jsonl': iter(judgments), 'results.jsonl': checked_results()}
