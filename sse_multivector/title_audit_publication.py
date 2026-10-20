"""Publish native fine-region title inputs, saved answers and recorded decisions."""
from pathlib import Path

from .historical_study_publication import _canonical
from .prompt_study_publication import _json, _sha
from .subject_goal_publication import _clean


_SETTINGS = ('model', 'reasoning_effort', 'codex_version', 'wrapper_sha256')


def _index(rows, key, label):
    if not isinstance(rows, list):
        raise ValueError('invalid title-audit ' + label)
    result = {}
    for row in rows:
        value = row.get(key) if isinstance(row, dict) else None
        if value is None or value in result:
            raise ValueError('ambiguous title-audit ' + label)
        result[value] = row
    return result


def _plain_title(text):
    text = text.strip()
    return text[2:-2] if text.startswith('**') and text.endswith('**') else text


def _supplied(fragment, mode):
    if mode == 'exact_source':
        return fragment
    if mode == 'saved_display_normalization':
        return ' '.join(fragment.strip('"“”').split())
    raise ValueError('unsupported saved title fragment mode')


def _numbered(rows):
    return '\n'.join(str(index) + '. ' + '; '.join('“' + part + '”' for part in row)
                     for index, row in enumerate(rows, 1))


def _mask(vector):
    text = vector.get('source_note')
    selected = vector.get('selected_source_fragments')
    if not isinstance(text, str) or not isinstance(selected, list) or not selected:
        raise ValueError('invalid title-audit source mask')
    fragments, characters, byte_spans = [], [], []
    for part in selected:
        fragment, occurrence = part.get('text'), part.get('occurrence')
        if not isinstance(fragment, str) or not fragment or type(occurrence) is not int or occurrence < 1:
            raise ValueError('invalid title-audit source fragment occurrence')
        start = -1
        for _ in range(occurrence):
            start = text.find(fragment, start + 1)
            if start < 0:
                raise ValueError('title-audit source fragment occurrence is absent')
        end = start + len(fragment)
        fragments.append(fragment)
        characters.append([start, end])
        byte_spans.append([len(text[:start].encode()), len(text[:end].encode())])
    return dict(kind='mask', vector_ordinal=vector['ordinal'], note_id=vector['note_id'],
        subject_id=vector.get('subject_id'), takeaway=vector.get('takeaway'),
        fragments=fragments, fragment_occurrences=[part['occurrence'] for part in selected],
        character_spans=characters, byte_spans=byte_spans)


def _cutoff_groups(selection, partition, template, requests):
    vectors = _index(partition.get('vectors'), 'ordinal', 'source vector ordinal')
    declared = _index(selection.get('groups'), 'prompt_id', 'selected group')
    if set(declared) != set(requests):
        raise ValueError('title-audit selected group/request identities differ')
    groups = {}
    for identity, request in requests.items():
        binding = declared[identity]
        members = binding.get('members')
        if (not isinstance(members, list) or not members or len(set(members)) != len(members)
                or any(member not in vectors for member in members)):
            raise ValueError('invalid selected title-audit source members')
        matches = []
        minimum = None
        for reference in binding.get('source_regions', []):
            resolutions = [row for row in partition['resolutions']
                           if row['level']['percentile'] == reference['percentile']]
            if len(resolutions) != 1:
                raise ValueError('ambiguous title-audit source resolution')
            resolution = resolutions[0]
            regions = [row for row in resolution['complete_linkage']['regions']
                       if row['region_index'] == reference['region_index']]
            if len(regions) != 1 or regions[0].get('members') != members:
                raise ValueError('title-audit selected members differ from native region')
            value = regions[0].get('minimum_within_cosine')
            if type(value) not in (int, float) or minimum is not None and minimum != value:
                raise ValueError('title-audit source minimum cosine mismatch')
            minimum = value
            matches.append(dict(percentile=reference['percentile'], region_index=reference['region_index'],
                resolution=resolution['level'], minimum_within_cosine=value))
        if not matches:
            raise ValueError('title-audit group has no native region binding')
        mode = request['fragment_mode']
        supplied = [[_supplied(part['text'], mode) for part in vectors[member]['selected_source_fragments']]
                    for member in members]
        if template.replace('{NUMBERED_INSTANCES}', _numbered(supplied)) != request['text']:
            raise ValueError('title-audit request differs from exact supplied source instances')
        percentile = request.get('percentile')
        if percentile is not None and not any(row['percentile'] == percentile for row in matches):
            raise ValueError('title-audit saved percentile lacks a source region binding')
        groups[identity] = dict(kind='title_input', id=identity, instance_kind='mask',
            vector_ordinals=members, supplied_fragments=supplied, fragment_mode=mode,
            source_regions=matches, minimum_within_cosine=minimum, percentile=percentile)
    return groups, vectors, {}


def _higher_groups(sources, selection, partition, template, requests):
    projection = sources.read(selection['projection']['path'])
    hierarchy = sources.read(selection['hierarchy']['path'])
    frozen = projection.get('inputs', {})
    if (frozen.get('partition_analysis_sha256') != sources.hashes[selection['partition']['path']]
            or frozen.get('hierarchy_analysis_sha256') != sources.hashes[selection['hierarchy']['path']]):
        raise ValueError('title-audit projection/analysis source hash mismatch')
    fine_reviews = sources.read(selection['fine_reviews']['path'])
    if frozen.get('fine_title_review_decisions_sha256') != sources.hashes[selection['fine_reviews']['path']]:
        raise ValueError('title-audit reused review source hash mismatch')
    fine_decisions = _index(fine_reviews['decisions'], 'segment_id', 'reused fine-title decision')
    fine_answers = {}
    for binding in selection.get('fine_outputs', []):
        document = sources.read(binding['path'])
        if frozen.get(binding['projection_hash_field']) != sources.hashes[binding['path']]:
            raise ValueError('title-audit reused output source hash mismatch')
        for identity, row in _index(document['responses'], 'prompt_id', 'reused fine title').items():
            if identity in fine_answers:
                raise ValueError('ambiguous reused title identity')
            fine_answers[identity] = row['response']
    fine_titles = _index(projection['fine_subject_titles'], 'fine_segment_id', 'projected fine title')
    fine_segments = _index(hierarchy['hierarchy']['fine_segments'], 'segment_id', 'fine segment')
    if set(fine_titles) != set(fine_segments):
        raise ValueError('title-audit projected fine segment identities mismatch')
    inputs = {}
    descendants = {identity: [identity] for identity in fine_segments}
    for identity, title in fine_titles.items():
        source_id = title['source_prompt_id']
        if (source_id not in fine_answers or source_id not in fine_decisions
                or fine_decisions[source_id].get('decision') != 'pass'
                or _plain_title(fine_answers[source_id]).casefold() != title['title'].casefold()):
            raise ValueError('title-audit projected fine title/reused evidence mismatch')
        inputs[identity] = dict(kind='fine_title', id=identity, title=title['title'],
            source_prompt_id=source_id, source_answer_sha256=_sha(fine_answers[source_id].encode()),
            vector_ordinals=fine_segments[identity]['members'])
    for merge in hierarchy['hierarchy']['merges']:
        identity = 'H' + str(merge['merge_index']).zfill(6)
        children = []
        for child in merge['children']:
            if child.get('kind') == 'merge' and type(child.get('id')) is int:
                child_id = 'H' + str(child['id']).zfill(6)
            elif child.get('kind') == 'fine_segment' and isinstance(child.get('id'), str):
                child_id = child['id']
            else:
                raise ValueError('invalid title-audit hierarchy child')
            if child_id not in descendants:
                raise ValueError('title-audit hierarchy has an unknown or forward child')
            children.extend(descendants[child_id])
        if len(set(children)) != len(children):
            raise ValueError('title-audit hierarchy repeats a descendant fine segment')
        descendants[identity] = sorted(children)
    selected = projection['mechanical_projection']['provisional_title_nodes']
    if selected != list(requests):
        raise ValueError('title-audit projected/request candidate identities mismatch')
    groups = {}
    for identity, request in requests.items():
        if identity not in descendants or identity == projection['rules']['implicit_root']:
            raise ValueError('invalid title-audit higher candidate')
        fine = descendants[identity]
        supplied = [[fine_titles[item]['title']] for item in fine]
        if template.replace('{NUMBERED_INSTANCES}', _numbered(supplied)) != request['text']:
            raise ValueError('title-audit higher request differs from descendant fine titles')
        members = sorted({member for item in fine for member in fine_segments[item]['members']})
        groups[identity] = dict(kind='title_input', id=identity, instance_kind='fine_title',
            fine_segment_ids=fine, vector_ordinals=members, supplied_fragments=supplied)
    return groups, _index(partition['vectors'], 'ordinal', 'source vector ordinal'), inputs


def prepare(sources, selection, metadata):
    metadata['exporter_sources']['sse_multivector/subject_goal_publication.py'] = _sha(
        Path(__file__).with_name('subject_goal_publication.py').read_bytes())
    partition = sources.read(selection['partition']['path'])
    registry = sources.read(selection['registry']['path'])
    version = selection.get('prompt_version')
    prompt = registry.get(version)
    if not isinstance(prompt, dict) or not isinstance(prompt.get('prompt_template'), str):
        raise ValueError('title-audit needs one explicit saved prompt version')
    template = prompt['prompt_template']
    if template.count('{NUMBERED_INSTANCES}') != 1:
        raise ValueError('title-audit prompt needs exactly one numbered input placeholder')
    requests, saved_answers, settings = {}, {}, {}
    threads = set()
    for run in selection.get('runs', []):
        config, manifest, output = (sources.read(run[key]['path'])
                                    for key in ('configuration', 'manifest', 'output'))
        configured = _index(config.get('prompts'), 'prompt_id', 'configured prompt')
        frozen = _index(manifest.get('prompts'), 'prompt_id', 'frozen prompt')
        responses = _index(output.get('responses'), 'prompt_id', 'saved response')
        receipts = _index([_json(line) for line in sources.raw(run['receipt']['path']).splitlines()
                           if line.strip()], 'note_id', 'saved receipt')
        if (config.get('prompts') != manifest.get('prompts')
                or any(set(rows) != set(configured) for rows in (frozen, responses, receipts))
                or manifest.get('config_sha256') != sources.hashes[run['configuration']['path']]
                or output.get('manifest_sha256') != sources.hashes[run['manifest']['path']]):
            raise ValueError('title-audit configuration/manifest/output identity mismatch')
        safe_settings = {key: manifest.get(key) for key in _SETTINGS}
        if 'isolation' in manifest:
            isolation = manifest['isolation']
            if not isinstance(isolation, dict):
                raise ValueError('invalid title-audit saved isolation')
            instructions = isolation.get('model_instructions')
            if instructions is not None and (not isinstance(instructions, str)
                    or isolation.get('model_instructions_sha256') != _sha(instructions.encode())):
                raise ValueError('title-audit saved model instructions hash mismatch')
            if run.get('model_instructions'):
                if not isinstance(instructions, str) or sources.raw(run['model_instructions']['path']) != instructions.encode():
                    raise ValueError('title-audit model instruction source mismatch')
            safe_settings['isolation'] = _clean(isolation)
        settings_ref = _sha(_canonical(safe_settings))
        settings[settings_ref] = safe_settings
        for identity, request in configured.items():
            if identity in requests:
                raise ValueError('duplicate title-audit answer identity across runs')
            receipt, raw = receipts[identity], responses[identity].get('response')
            if (not isinstance(raw, str) or receipt.get('stage') != 'prompt'
                    or receipt.get('job_key') != 'prompt:' + identity or receipt.get('status') != 'succeeded'
                    or receipt.get('error') is not None or receipt.get('exit_code') != 0
                    or receipt.get('manifest_sha256') != sources.hashes[run['manifest']['path']]
                    or receipt.get('prompt_sha256') != _sha(request.get('text', '').encode())
                    or receipt.get('final_output_raw') != raw or receipt.get('final_output_sha256') != _sha(raw.encode())
                    or receipt.get('response') != raw or receipt.get('response_schema_sha256') is not None
                    or any((key in config and config[key] != manifest.get(key))
                           or (key in receipt and receipt[key] != manifest.get(key))
                           for key in ('model', 'reasoning_effort', 'codex_version', 'wrapper_sha256'))):
                raise ValueError('title-audit saved receipt/answer/settings binding mismatch')
            thread = receipt.get('thread_id')
            if thread is not None:
                if not isinstance(thread, str) or not thread or thread in threads:
                    raise ValueError('title-audit reuses an execution identity')
                threads.add(thread)
            requests[identity] = dict(request, fragment_mode=run.get('fragment_mode'), percentile=run.get('percentile'))
            saved_answers[identity] = dict(call_id=identity, input_ref=identity, output=raw,
                output_sha256=_sha(raw.encode()), prompt_version=version, settings_ref=settings_ref,
                source_output=run['output']['path'], manifest_sha256=sources.hashes[run['manifest']['path']],
                status=receipt['status'], exit_code=receipt['exit_code'], error=receipt.get('error'),
                elapsed_seconds=receipt.get('elapsed_seconds'), response_schema_sha256=receipt.get('response_schema_sha256'),
                attempt=receipt.get('attempt'), usage={key: value for key, value in receipt.get('usage', {}).items()
                    if key in ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                               'reasoning_output_tokens', 'total_tokens')},
                independence_basis='distinct saved execution identity' if thread else 'not recorded')
    if not requests:
        raise ValueError('title-audit selection has no final requests')
    if selection.get('kind') == 'cutoff':
        groups, vectors, fine_inputs = _cutoff_groups(selection, partition, template, requests)
    elif selection.get('kind') == 'higher':
        groups, vectors, fine_inputs = _higher_groups(sources, selection, partition, template, requests)
    else:
        raise ValueError('unsupported title-audit study kind')
    posts, masks = {}, {}
    for group in groups.values():
        for ordinal in group['vector_ordinals']:
            if ordinal not in vectors:
                raise ValueError('title-audit selected context has an unknown vector ordinal')
            vector = vectors[ordinal]
            post = dict(kind='post', note_id=vector['note_id'], text=vector['source_note'])
            if posts.setdefault(vector['note_id'], post) != post:
                raise ValueError('title-audit source post identity has conflicting text')
            if ordinal not in masks:
                masks[ordinal] = _mask(vector)
    native_reviews = sources.read(selection['reviews']['path'])
    if native_reviews.get('decision_owner') not in ('user', 'agent', 'assistant'):
        raise ValueError('title-audit recorded decision owner is not explicit')
    actor = 'user' if native_reviews['decision_owner'] == 'user' else 'agent'
    key = 'segment_id' if selection['kind'] == 'cutoff' else 'candidate_id'
    decisions = _index(native_reviews.get('decisions'), key, 'recorded decision')
    judgments = []
    for identity, row in decisions.items():
        if identity not in saved_answers or row.get('decision') not in ('pass', 'fail', 'reject'):
            raise ValueError('orphaned or invalid title-audit recorded decision')
        if not isinstance(row.get('title_reviewed'), str):
            raise ValueError('title-audit review needs its original reviewed label')
        minimum_match = None
        if selection['kind'] == 'cutoff':
            recorded, actual = row.get('minimum_cosine'), groups[identity]['minimum_within_cosine']
            if recorded == actual:
                minimum_match = 'exact'
            elif type(recorded) in (int, float) and recorded == round(actual, 6):
                minimum_match = 'rounded_to_six_decimal_places'
            else:
                raise ValueError('title-audit reviewed/source minimum cosine mismatch')
        raw = saved_answers[identity]['output']
        judgments.append(dict(kind='recorded_decision', actor=actor,
            attribution_basis='saved review-decisions decision_owner', criterion=native_reviews.get('criterion'),
            source=selection['reviews']['path'], call_id=identity, raw_answer_sha256=_sha(raw.encode()),
            **_clean(row), reviewed_title_equals_raw_response=row['title_reviewed'] == raw,
            reviewed_title_matches_saved_answer=_plain_title(row['title_reviewed']).casefold() == _plain_title(raw).casefold(),
            minimum_cosine_match=minimum_match))
    unreviewed = [identity for identity in saved_answers if identity not in decisions]
    parameters = dict(prompt=prompt, partition_rules=partition.get('rules'),
        partition_parameters={key: value for key, value in partition.items()
            if key not in {'vectors', 'resolutions', 'rules', 'pairwise_cosines', 'cross_note_nearest_cosines'}},
        grouping_source=selection['partition']['path'], source_kind=selection['kind'])
    if selection['kind'] == 'higher':
        parameters['projection'] = _clean(sources.read(selection['projection']['path']))
        parameters['hierarchy_parameters'] = _clean({key: value for key, value in
            sources.read(selection['hierarchy']['path']).items() if key != 'hierarchy'})
        recorded_registry = parameters['projection']['inputs'].get('fine_title_prompt_registry_sha256')
        current_registry = sources.hashes[selection['registry']['path']]
        if recorded_registry and recorded_registry != current_registry:
            metadata['binding_limitations'] = [dict(source=selection['registry']['path'],
                recorded_sha256=recorded_registry, current_source_sha256=current_registry,
                historical_source_git_revision=selection.get('historical_registry_revision'),
                limitation='Registry bytes changed after generation. The selected v1 template reconstructs every saved request.')]
    metadata.update(parameters=parameters, settings=settings, prompt_version=version,
        AS_status='unknown; historical evidence, not current-pipeline validation; raw source posts are not deprecated',
        interpretation='Recorded group decisions and exact generated titles are separate facts. Label comparison removes only outer bold markers and ignores case; no semantic equivalence is inferred.',
        input_context='Post/mask records preserve original context; title_input records identify exactly what the model received.',
        review_contract=_clean({key: value for key, value in native_reviews.items() if key != 'decisions'}),
        dependencies=_clean(selection.get('dependencies', [])))
    result = dict(kind='record_counts', answers=len(saved_answers), recorded_decisions=len(judgments),
        unreviewed_call_ids=unreviewed, reviewed_label_mismatches=[row['call_id'] for row in judgments
            if not row['reviewed_title_matches_saved_answer']])
    return {'inputs.jsonl': [*posts.values(), *masks.values(), *fine_inputs.values(), *groups.values()],
            'answers.jsonl': saved_answers.values(), 'judgments.jsonl': judgments, 'results.jsonl': [result]}
