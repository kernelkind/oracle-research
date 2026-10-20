"""Publish saved category views, native Infomap results and reference fixtures."""
import hashlib
import json
from pathlib import Path
import re
import uuid

from . import canonical_hierarchy_nostr as nostr


_PRIVATE = {'api_key', 'api_token', 'access_token', 'refresh_token', 'password',
            'credentials', 'auth_file', 'codex_home', 'authorization', 'headers',
            'account', 'account_id', 'session_id', 'thread_id', 'argv', 'stderr',
            'stdout', 'stdout_json', 'environment_variables', 'tracking_card'}
_LOCAL = re.compile(r'/(?:home|Users|tmp|mnt|private|run)/[^\s\"\x27<>\[\](){},;`]*')
_CATEGORY = {'schema_version', 'hierarchy_id', 'source_sha256', 'root_node_id',
             'notes', 'nodes', 'note_masks', 'mask_instances'}


def _require(condition, message):
    if not condition:
        raise ValueError('saved hierarchy publication: ' + message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _clean(value, sources):
    """Retain scientific settings, replacing only operational local locations."""
    if isinstance(value, dict):
        return {_clean(key, sources): _clean(item, sources)
                for key, item in value.items() if key not in _PRIVATE}
    if isinstance(value, list):
        return [_clean(item, sources) for item in value]
    if isinstance(value, str):
        def portable(match):
            text = match.group()
            for prefix in (str(sources.root), '/home/dev/src/notedeck-publication/oracle-mvp',
                           '/home/dev/src/notedeck_worktrees/algos/oracle-mvp'):
                if text.startswith(prefix + '/'):
                    return text[len(prefix) + 1:]
            return 'local-artifact:' + Path(text).name + '[sha256:' + _sha(text.encode()) + ']'
        return _LOCAL.sub(portable, value)
    return value


def _posts(sources, selection):
    declaration = selection.get('posts')
    if not declaration:
        return None
    value = sources.read(declaration['path'])
    rows = value.get('notes')
    _require(isinstance(rows, list), 'source posts must contain notes')
    posts = {}
    for row in rows:
        _require(isinstance(row.get('note_id'), str) and isinstance(row.get('text'), str)
                 and row['note_id'] not in posts, 'invalid or duplicate source post')
        posts[row['note_id']] = row['text']
    return posts


def _ranges(spans, text):
    _require(isinstance(spans, list), 'mask spans must be a list')
    raw = text.encode('utf-8')
    for span in spans:
        _require(isinstance(span, list) and len(span) == 2
                 and all(type(number) is int for number in span)
                 and 0 <= span[0] < span[1] <= len(raw), 'invalid source mask byte span')
        try:
            raw[span[0]:span[1]].decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError('saved hierarchy publication: mask cuts a UTF-8 character') from error


def _categories(sources, selection, metadata, value):
    _require(set(value) <= _CATEGORY and value.get('schema_version') in (1, 2),
             'unsupported category hierarchy fields')
    rows, notes = value.get('nodes'), value.get('notes')
    _require(isinstance(rows, list) and isinstance(notes, list), 'missing category nodes/notes')
    aliases, full_ids = {}, set()
    for note in notes:
        _require(set(note) == {'note_id', 'note_short_id'} and
                 all(isinstance(item, str) and item for item in note.values()), 'invalid note identity')
        _require(note['note_id'] not in full_ids, 'duplicate note identity')
        full_ids.add(note['note_id'])
        for key in note.values():
            _require(key not in aliases or aliases[key] == note['note_id'], 'ambiguous note identity')
            aliases[key] = note['note_id']
    posts = _posts(sources, selection)
    if posts is not None:
        _require(full_ids <= posts.keys() and value['source_sha256'] == selection['posts']['sha256'],
                 'saved source-post binding differs')
    by_id = {}
    for row in rows:
        _require(set(row) == {'node_id', 'label', 'analysis', 'children', 'note_ids'}
                 and isinstance(row['node_id'], str) and row['node_id']
                 and row['node_id'] not in by_id
                 and isinstance(row['label'], str) and row['label'].strip()
                 and isinstance(row['analysis'], str), 'invalid category node')
        for field in ('children', 'note_ids'):
            _require(isinstance(row[field], list) and all(isinstance(x, str) and x for x in row[field])
                     and len(row[field]) == len(set(row[field])), 'invalid category ' + field)
        _require(set(row['note_ids']) <= aliases.keys(), 'node names an unknown source note')
        by_id[row['node_id']] = row
    parents = {key: [] for key in by_id}
    for row in rows:
        for child in row['children']:
            _require(child in parents, 'unknown child node')
            parents[child].append(row['node_id'])
    _require(value['root_node_id'] in by_id and [key for key in parents if not parents[key]] ==
             [value['root_node_id']], 'saved navigation root differs')
    identities = {key: str(uuid.uuid5(nostr.UNSIGNED_NAMESPACE, key)) for key in by_id}
    by_uuid = {identities[key]: row for key, row in by_id.items()}
    inputs = [{'type': 'note_identities', 'notes': notes}]
    inputs.extend({'type': 'node_identity', 'source_node_id': key, 'node_uuid': identities[key],
                   'native_note_ids': row['note_ids']} for key, row in by_id.items())
    instance_ids = set()
    for kind in ('note_masks', 'mask_instances'):
        groups = value.get(kind, {})
        _require(isinstance(groups, dict) and set(groups) <= by_id.keys(), 'unknown mask group')
        for node, membership in groups.items():
            _require(isinstance(membership, dict) and set(membership) <= aliases.keys(),
                     'mask names an unknown source note')
            for note, masks in membership.items():
                if kind == 'mask_instances':
                    _require(isinstance(masks, list), 'mask instances must be a list')
                    for mask in masks:
                        _require(set(mask) == {'ids', 'byte_spans'} and isinstance(mask['ids'], list)
                                 and all(isinstance(x, str) and x for x in mask['ids'])
                                 and len(mask['ids']) == len(set(mask['ids'])), 'invalid mask identity')
                        instance_ids.update(mask['ids'])
                        if posts is not None:
                            _ranges(mask['byte_spans'], posts[aliases[note]])
                elif posts is not None:
                    _ranges(masks, posts[aliases[note]])
            inputs.append({'type': kind, 'source_node_id': node, 'data': membership})
    # The shared serializer validates graph/membership and removes ancestor duplicates.
    # Its nonempty-meaning contract uses the native title while validating; the
    # emitted content below is exactly the original analysis, including empty text.
    state = {'nodes': [{'id': key, 'subject': row['label'], 'meaning': row['label'],
                       'parents': parents[key], 'note_ids': [aliases[n] for n in row['note_ids']]}
                      for key, row in by_id.items()], 'shape': {'roots': [value['root_node_id']]}}

    def events():
        for event in nostr.unsigned_events(state):
            if event['kind'] == nostr.NODE_KIND:
                identity = next(tag[1] for tag in event['tags'] if tag[0] == 'd')
                row = by_uuid[identity]
                # Native DAG sibling orders need not agree with global row order.
                event['tags'] = [tag for tag in event['tags'] if tag[0] in ('d', 'title')] + [
                    ['child', identities[child]] for child in row['children']] + [
                    tag for tag in event['tags'] if tag[0] == 'e']
                event['content'] = row['analysis']
            yield event

    metadata.update(hierarchy_id=value['hierarchy_id'],
        representation='Unsigned kind/tags/content; content is saved analysis, not a new definition.',
        membership_rule='Canonical records omit ancestor duplicates. node_identity inputs retain every exact native note assignment.',
        counts={'nodes': len(rows), 'edges': sum(len(row['children']) for row in rows),
                'notes': len(notes),
                'original_mask_ids': len(instance_ids) if 'mask_instances' in value else None})
    return inputs, events()


def _infomap(sources, selection, metadata, value):
    _require(value.get('schema_version') == 'infomap-hierarchy-v1', 'unsupported Infomap hierarchy')
    paths, modules = value['paths'], value['modules']
    canonical, aliases = value['canonical_unique_ids'], value['alias_groups']
    _require(len(paths) == len(canonical) == len(aliases) == value['vector_count']
             and len(set(canonical)) == len(canonical), 'Infomap vector accounting differs')
    mapping = sources.read(selection['vector_map']['path'])
    _require(value['sources']['vector_map']['sha256'] == selection['vector_map']['sha256'],
             'selected vector source differs from native binding')
    by_vector = {row['vector_id']: row['note_id'] for row in mapping['vectors']}
    _require(len(by_vector) == len(mapping['vectors']), 'duplicate source vector identity')
    vector_notes = []
    for representative, group in zip(canonical, aliases):
        _require(isinstance(group, list) and group and representative == group[0]
                 and len(group) == len(set(group)) and set(group) <= by_vector.keys(),
                 'invalid canonical alias binding')
        vector_notes.append({by_vector[x] for x in group})
    _require(sum(map(len, aliases)) == len({x for group in aliases for x in group}) == len(by_vector),
             'Infomap alias partition differs from source vectors')
    by_id = {row['id']: row for row in modules}
    _require(len(by_id) == len(modules) and value['root'] in by_id, 'invalid Infomap modules')
    _require([row['node_id'] for row in paths] == list(range(len(paths))), 'Infomap paths omit vectors')
    for row in paths:
        _require(row['native_path'][:-1] == row['module_path'], 'native/module path differs')
    for row in modules:
        members = row['vector_ids']
        _require(len(members) == len(set(members)) and all(type(i) is int and 0 <= i < len(paths) for i in members),
                 'invalid module vector membership')
        _require(row['note_ids'] == sorted({n for i in members for n in vector_notes[i]}),
                 'module note membership differs from source aliases')
        _require(all(c in by_id and by_id[c]['parent'] == row['id'] for c in row['children']),
                 'Infomap module edges differ')
        _require(set(members) == set(row['direct_vectors']) | {
            i for c in row['children'] for i in by_id[c]['vector_ids']}, 'module descendant membership differs')
        _require(all(paths[i]['module_path'] == row['module_path'] for i in row['direct_vectors']),
                 'native path differs from module assignment')
    configuration = sources.read(selection['configuration']['path'])
    _require(configuration['run_id'] == value['run_id'] and configuration['sources'] == value['sources'],
             'Infomap configuration/source binding differs')
    metadata.update(parameters=_clean(configuration, sources),
                    representation='Native Infomap modules, paths and flow; no generated labels or definitions.',
                    counts={'nodes': len(modules), 'notes': value['summary']['notes'],
                            'canonical_vectors': len(paths), 'original_mask_ids': sum(map(len, aliases))})
    return [], [{'type': 'native_infomap_hierarchy', 'data': _clean(value, sources)}]


def _true_graph(sources, selection, metadata, raw_graph):
    """Keep native cyclic graphs and reference their already-published scores."""
    import ijson
    from ._runner_bootstrap import shared

    science = {'a', 'b', 'generated_text', 'generated_token_ids', 'eos_terminated',
               'predicted', 'entailment_score', 'threshold_predicted',
               'logit_0_first_token', 'logit_1_first_token', 'probability_0_first_token',
               'first_token_binary_score', 'first_token_binary_label',
               'label_prefix_probability_mass', 'argmax_token_id'}
    score_rows = []
    with sources.stream(selection['score_table']['path']) as stream:
        score_rows.extend(ijson.items(stream, 'item', use_float=True))
    needed = {}
    for row in score_rows:
        origin = row['score_origin']
        needed.setdefault(origin['source'], set()).add(origin['row_id'])
    published, publications = {}, {}
    for declaration in selection['published_scores']:
        source = declaration['source']
        _require(source not in publications, 'duplicate published score source')
        publications[source] = declaration['publication']
        found = {}
        with sources.stream(declaration['payload']['path']) as stream:
            for row in ijson.items(stream, '', multiple_values=True, use_float=True):
                if row.get('id') in needed.get(source, set()):
                    _require(row['id'] not in found, 'duplicate published score row')
                    found[row['id']] = {key: row[key] for key in science if key in row}
        _require(set(found) == needed.get(source, set()), 'published score reference is missing')
        published[source] = found
    _require(set(publications) == set(needed), 'unbound native score origin')

    def score_reference(row):
        origin = row['score_origin']
        _require(set(origin) == {'source', 'row_index', 'row_id', 'reused'}
                 and type(origin['reused']) is bool and type(origin['row_index']) is int
                 and origin['row_index'] >= 0, 'invalid recorded score origin')
        saved = published.get(origin['source'], {}).get(origin['row_id'])
        _require(saved is not None and science <= row.keys()
                 and saved == {key: row[key] for key in science},
                 'native score differs from the published scientific output')
        return {'id': row['id'], 'a_id': row['a_id'], 'b_id': row['b_id'],
                'score_ref': {'publication': publications[origin['source']],
                              'row_id': origin['row_id']}, 'score_origin': origin}

    directions = [dict(type='direction_reference', **score_reference(row)) for row in score_rows]
    _require(len({row['id'] for row in directions}) == len(directions), 'duplicate raw direction')
    posts = {}

    def project(value):
        if isinstance(value, dict):
            if 'score_origin' in value:
                return score_reference(value)
            if {'note_id', 'text', 'byte_spans'} <= value.keys():
                text, note = value['text'], value['note_id']
                _require(isinstance(text, str) and isinstance(note, str), 'invalid source mask input')
                digest = _sha(text.encode())
                _require(posts.get(note, digest) == digest, 'conflicting source post texts')
                posts[note] = digest
                _ranges(value['byte_spans'], text)
                value = {key: item for key, item in value.items() if key != 'text'}
                value['source_post_sha256'] = digest
            return {key: project(item) for key, item in value.items()
                    if key not in _PRIVATE and key not in {'model_input', 'token_ids', 'batch_seconds'}}
        if isinstance(value, list):
            return [project(item) for item in value]
        return _clean(value, sources)

    config = sources.read(selection['configuration']['path'])
    plan = sources.read(selection['plan']['path'])
    graph = sources.read(selection['derived_graph']['path'])
    completion = sources.read(selection['raw_completion']['path'])
    final = sources.read(selection['derived_completion']['path'])
    _require(completion['scores_sha256'] == selection['score_table']['sha256']
             and completion['graph_sha256'] == selection['hierarchy']['sha256']
             and completion['graph_code_sha256'] == selection['graph_code']['sha256']
             and completion['stats'] == raw_graph['stats'], 'raw completion binding differs')
    selected = {Path(declaration['path']).name: declaration['sha256'] for declaration in (
        selection['derived_graph'], selection['memberships'], selection['canonical'],
        *selection.get('derived_records', []))}
    _require(all(final['files'].get(name) == digest for name, digest in selected.items()),
             'derived completion binding differs')
    _require(final['raw_stats'] == raw_graph['stats'] and final['canonical_stats'] == graph['stats'],
             'final graph accounting differs')
    _require(plan['threshold'] == config['threshold'] == raw_graph['threshold'] == graph['threshold']
             and plan['model_id'] == config['model_id'] and plan['revision'] == config['revision'],
             'plan/config graph settings differ')
    projection = shared('json_projection')
    helper = Path(projection.__file__)
    metadata['exporter_sources']['experiment_runner/' + helper.name] = _sha(helper.read_bytes())
    with sources.stream(selection['canonical']['path']) as stream:
        canonical = projection.project(stream, {'titles', 'source_packets', 'consolidations'})
    with sources.stream(selection['canonical']['path']) as stream:
        canonical_count = sum(1 for row in ijson.items(stream, 'scores.item', use_float=True)
                              if score_reference(row))
    _require(canonical_count == graph['stats']['scored_ordered_pairs'], 'canonical direction count differs')
    results = directions + [{'type': 'raw_true_graph', 'data': project(raw_graph)},
                            {'type': 'canonical_true_graph', 'data': project(graph)}]
    memberships = sources.read(selection['memberships']['path'])
    _require(memberships['stats'] == final['note_stats'], 'final note membership accounting differs')
    results.append({'type': 'canonical_note_memberships', 'data': project(memberships)})
    inputs = [{'type': 'source_packets', 'data': project(canonical['source_packets'])}]
    for consolidation in canonical['consolidations']:
        # Original group/packet bodies are already retained by graphs/packet inputs.
        inputs.append({'type': 'recorded_consolidation', 'data': project({
            key: item for key, item in consolidation.items()
            if key not in {'source_groups', 'source_packets'}})})
    inputs.extend({'type': 'source_post_reference', 'note_id': note, 'sha256': digest}
                  for note, digest in posts.items())
    judgments = []
    for declaration in selection.get('assessments', []):
        judgments.append({'type': declaration['role'],
            'actor': {'kind': 'agent', 'basis': 'Saved TRUE10 scientific assessment; not a user verdict.'},
            'source': {key: declaration[key] for key in ('path', 'sha256')},
            'data': project(sources.read(declaration['path']))})
    for declaration in selection.get('derived_records', []):
        results.append({'type': declaration['role'], 'data': project(sources.read(declaration['path']))})
    metadata['parameters'].update(configuration=_clean(config, sources), plan=_clean(plan, sources),
        raw_completion=completion, derived_completion=_clean(final, sources),
        canonical_title_context=_clean({key: item for key, item in canonical['titles'].items()
                                        if key != 'groups'}, sources))
    metadata.update(representation='Native cyclic TRUE graphs; no unsigned DAG conversion or inferred repair.',
        counts={'raw_nodes': len(raw_graph['nodes']), 'raw_edges': len(raw_graph['raw_edges']),
                'raw_cycles': len(raw_graph['cycle_components']), 'raw_directions': len(directions),
                'canonical_nodes': len(graph['nodes']), 'canonical_edges': len(graph['raw_edges']),
                'canonical_cycles': len(graph['cycle_components']), 'canonical_directions': canonical_count,
                'note_memberships': len(memberships['nodes']), 'source_posts': len(posts)})
    return inputs, results, judgments


def prepare(sources, selection, metadata):
    kind = selection.get('kind')
    _require(kind in ('categories', 'infomap', 'reference', 'true-graph'), 'unsupported saved hierarchy selection')
    value = sources.read(selection['hierarchy']['path'])
    helper = Path(nostr.__file__)
    metadata['exporter_sources']['sse_multivector/' + helper.name] = _sha(helper.read_bytes())
    metadata.update(historical=True, status='saved_reference_input' if kind == 'reference' else 'saved_final',
        scientific_role='reference input' if kind == 'reference' else 'final hierarchy or partition',
        reused_inputs=selection.get('reused_inputs', {}), parameters={},
        subject_provenance={'versions': [], 'lineage_status': 'AS lineage unestablished for this saved view; no version or approval inferred.',
                            'generated_subjects_deprecated': None, 'raw_posts_deprecated': False})
    for declaration in selection.get('parameters', []):
        parameters = sources.read(declaration['path'])
        if 'fields' in declaration:
            fields = declaration['fields']
            _require(isinstance(fields, list) and isinstance(parameters, dict)
                     and all(isinstance(field, str) and field in parameters for field in fields),
                     'selected parameter field is missing')
            parameters = {field: parameters[field] for field in fields}
        metadata['parameters'][declaration['path']] = _clean(parameters, sources)
    judgments = []
    if kind == 'true-graph':
        inputs, results, judgments = _true_graph(sources, selection, metadata, value)
    elif kind == 'categories':
        inputs, results = _categories(sources, selection, metadata, value)
    elif kind == 'infomap':
        inputs, results = _infomap(sources, selection, metadata, value)
    else:
        _require(value.get('schema_version') == 1 and isinstance(value.get('nodes'), list),
                 'unsupported reference fixture')
        metadata['counts'] = {'nodes': len(value['nodes']),
                              'notes': len(value['notes']) if 'notes' in value else None}
        metadata['representation'] = 'Exact authored reference fixture; not an automatic hierarchy result or new user decision.'
        inputs, results = [{'type': 'reference_fixture', 'data': value}], []
    return {'inputs.jsonl': iter(inputs), 'answers.jsonl': iter(()),
            'judgments.jsonl': iter(judgments), 'results.jsonl': iter(results)}
