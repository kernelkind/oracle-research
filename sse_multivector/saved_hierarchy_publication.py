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
            'stdout', 'stdout_json', 'environment_variables'}
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


def prepare(sources, selection, metadata):
    kind = selection.get('kind')
    _require(kind in ('categories', 'infomap', 'reference'), 'unsupported saved hierarchy selection')
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
    if kind == 'categories':
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
            'judgments.jsonl': iter(()), 'results.jsonl': iter(results)}
