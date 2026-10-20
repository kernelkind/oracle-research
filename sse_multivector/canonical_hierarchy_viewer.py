"""Export saved canonical graphs for the existing original-note review UI."""
import hashlib
import json
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
import uuid

try:
    from .canonical_hierarchy import read_hierarchy
except ImportError:
    from canonical_hierarchy import read_hierarchy


def _root_admissions(saved, directory, study):
    """Read only frozen conservative decisions bound to this exact source graph."""
    study = Path(study).resolve()
    certificate_path = study/'final-verification.json'
    certificate = json.loads(certificate_path.read_bytes())
    def bound(name):
        raw = (study/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != certificate['artifacts'][name]:
            raise ValueError('admission source checksum mismatch: '+name)
        return json.loads(raw)
    plan, decisions = bound('plan.json'), bound('query-root-results.json')
    state = saved['state']
    source_state = Path(plan['source_state'])
    if (plan.get('as_version') != 'ASv6.100'
            or source_state.resolve() != directory/'state.json'
            or plan['sources'].get(str(source_state)) != hashlib.sha256(saved['state_bytes']).hexdigest()
            or Path(plan['corpus']).resolve() != Path(state['corpus']).resolve()):
        raise ValueError('admissions must bind the exact saved hierarchy and corpus')
    if set(plan['roots']) != set(saved['roots']):
        raise ValueError('admission roots differ from existing roots')
    records = {r['id']:r for r in plan['records']}
    originals = {r['id']:r for r in state['originals']}
    covered = set(saved['note_short_ids'])
    additions = {root:[] for root in saved['roots']}
    rows, seen = [], set()
    for row in decisions:
        if row['method'] != 'MM_note_bend' or not row['proposed']:
            continue
        prefix = directory.name+':'
        root = row['root'].removeprefix(prefix)
        if (row['corpus'] != directory.name or not row['root'].startswith(prefix)
                or root not in additions):
            raise ValueError('admission target must be an existing root')
        entry = records.get(row['entry'])
        original = originals.get(row['entry'])
        if (entry is None or original is None or not row['groups']
                or row['source_note_id'] != entry['source_note_id']
                or entry['source_note_id'] != original['local']['note_id']
                or any(entry[k] != original[k] for k in ['title','meaning'])
                or entry['source_note_id'] in covered):
            raise ValueError('admission entry evidence differs or note is already covered')
        key = (root,entry['id'])
        if key in seen:
            raise ValueError('duplicate saved admission decision')
        seen.add(key)
        additions[root].append(entry['source_note_id'])
        rows.append(dict(root=root,entry=entry['id'],note_id=entry['source_note_id'],
                         title=entry['title'],meaning=entry['meaning'],groups=row['groups']))
    additions = {root:list(dict.fromkeys(notes)) for root,notes in additions.items()}
    return dict(status='Experimental saved root-admission preview; not a HiGen run or semantic certification',
        method='MM_note_bend',source_study=str(study),
        source_state_sha256=hashlib.sha256(saved['state_bytes']).hexdigest(),
        source_hashes={name:certificate['artifacts'][name] for name in ['plan.json','query-root-results.json']},
        notes_by_root=additions,entries=rows,
        additional_notes=len({n for notes in additions.values() for n in notes}),
        new_root_placements=sum(len(notes) for notes in additions.values()))


def _payload_lines(directory, record, name):
    digest = hashlib.sha256()
    with (directory / name).open('rb') as stream:
        for line in stream:
            digest.update(line)
            yield line
    if digest.hexdigest() != record['files'].get(name):
        raise ValueError('published hierarchy checksum mismatch: ' + name)


def _published_graph(directory):
    """Read the published graph itself, without reconstructing native state."""
    from .canonical_hierarchy_nostr import ENTRY_KIND, NODE_KIND
    from .hierarchy_publication import FORMAT

    record = json.loads((directory / 'experiment.json').read_bytes())
    if (not isinstance(record, dict)
            or record.get('format') != FORMAT or record.get('schema_version') != 1
            or not isinstance(record.get('experiment_id'), str)
            or not record['experiment_id'].strip()
            or not isinstance(record.get('files'), dict)
            or not isinstance(record.get('input'), dict)
            or type(record['input'].get('count')) is not int):
        raise ValueError('expected a hierarchy-publication-v1 directory')
    selected = set()
    for line in _payload_lines(directory, record, 'input-note-ids.txt'):
        note = line.decode('utf-8').rstrip('\r\n')
        if not note.strip() or note in selected:
            raise ValueError('published input note IDs must be nonempty and unique')
        selected.add(note)
    if len(selected) != record['input']['count']:
        raise ValueError('published input count differs from its selection')
    nodes, roots = {}, None
    for line in _payload_lines(directory, record, 'hierarchy.jsonl'):
        event = json.loads(line)
        if (not isinstance(event, dict) or set(event) != {'kind', 'tags', 'content'}
                or event['kind'] not in (NODE_KIND, ENTRY_KIND)
                or not isinstance(event['content'], str)
                or not isinstance(event['tags'], list)):
            raise ValueError('invalid unsigned hierarchy record')
        tags = {}
        allowed = {'d', 'title', 'child', 'e'} if event['kind'] == NODE_KIND else {'child'}
        for tag in event['tags']:
            if (not isinstance(tag, list) or len(tag) != 2
                    or any(not isinstance(value, str) or not value.strip() for value in tag)
                    or tag[0] not in allowed):
                raise ValueError('invalid unsigned hierarchy tag')
            tags.setdefault(tag[0], []).append(tag[1])
        if any(len(values) != len(set(values)) for values in tags.values()):
            raise ValueError('published hierarchy repeats a tag reference')
        if event['kind'] == ENTRY_KIND:
            if roots is not None or event['content']:
                raise ValueError('published hierarchy requires one empty root entry')
            roots = tags.get('child', [])
            continue
        if (len(tags.get('d', [])) != 1 or len(tags.get('title', [])) != 1
                or not event['content'].strip()):
            raise ValueError('published nodes require one ID, title and nonempty definition')
        identifier = tags['d'][0]
        if str(uuid.UUID(identifier)) != identifier or identifier in nodes:
            raise ValueError('published node UUIDs must be unique and canonical')
        nodes[identifier] = dict(node_id=identifier, label=tags['title'][0],
            children=tags.get('child', []), note_ids=tags.get('e', []),
            meaning=event['content'])
    if roots is None:
        raise ValueError('published hierarchy root entry is missing')
    if not nodes:
        raise ValueError('published hierarchy has no nodes to browse')
    parents = {identifier: [] for identifier in nodes}
    needed = set()
    for identifier, node in nodes.items():
        needed.update(node['note_ids'])
        for child in node['children']:
            if child not in nodes:
                raise ValueError('published hierarchy references an unknown child')
            parents[child].append(identifier)
    try:
        list(TopologicalSorter(parents).static_order())
    except CycleError as error:
        raise ValueError('published hierarchy contains a cycle') from error
    if set(roots) != {identifier for identifier, links in parents.items() if not links}:
        raise ValueError('published hierarchy roots differ from the graph')
    if not needed <= selected:
        raise ValueError('published hierarchy references a post outside its input selection')
    if record.get('outcome') != dict(nodes=len(nodes), roots=len(roots), represented_notes=len(needed)):
        raise ValueError('published hierarchy counts differ from experiment.json')
    return record, nodes, roots, parents, needed


def _published_posts(path, needed):
    """Stream once; retain only the posts referenced by the saved graph."""
    import ijson

    notes, short_ids = [], {}
    with Path(path).open('rb') as stream:
        rows = (json.loads(line) for line in stream) if Path(path).suffix == '.jsonl' else (
            ijson.items(stream, 'notes.item'))
        for index, row in enumerate(rows, 1):
            if (not isinstance(row, dict) or not isinstance(row.get('note_id'), str)
                    or not row['note_id'].strip() or not isinstance(row.get('text'), str)):
                raise ValueError('source posts require note_id and text strings')
            identifier = row['note_id']
            if identifier not in needed:
                continue
            if identifier in short_ids:
                raise ValueError('source posts repeat a referenced note ID: ' + identifier)
            if not row['text'].strip():
                raise ValueError('referenced source post text is empty: ' + identifier)
            short_ids[identifier] = f'N{index:03d}'
            notes.append(dict(note_id=identifier, text=row['text']))
    if set(short_ids) != needed:
        raise ValueError('source posts are missing referenced note IDs: '
                         + ', '.join(sorted(needed - short_ids.keys())[:5]))
    return notes, short_ids


def _write_viewer(output, identifier, originals, short_ids, nodes, roots):
    notes_bytes = (json.dumps({'notes': originals}, ensure_ascii=False, indent=2) + '\n').encode()
    hierarchy = dict(schema_version=2, hierarchy_id=identifier,
        source_sha256=hashlib.sha256(notes_bytes).hexdigest(), root_node_id='VIEW_ROOT',
        notes=[dict(note_id=note, note_short_id=short) for note, short in short_ids.items()],
        nodes=nodes)
    output.mkdir(parents=True)
    (output / 'notes.json').write_bytes(notes_bytes)
    (output / 'hierarchy.json').write_text(json.dumps(hierarchy, ensure_ascii=False, indent=2) + '\n')
    return dict(hierarchy=str(output / 'hierarchy.json'), notes=str(output / 'notes.json'),
                nodes=len(nodes) - 1, roots=len(roots), note_count=len(originals))


def _export_published_viewer(directory, output, posts):
    record, nodes, roots, parents, needed = _published_graph(directory)
    originals, short_ids = _published_posts(posts, needed)
    provenance = 'Subject prompt versions: ' + json.dumps(record['input'].get('subject_prompt_versions'))
    if record['input'].get('deprecated') is True:
        provenance += '\nHistorical evidence: derived subjects predate ASv6.100 and are deprecated.'
    view_nodes = [dict(node_id='VIEW_ROOT', label=record['experiment_id'],
        children=roots, note_ids=[], analysis=
        'Display-only container for published roots. Not a hierarchy node.\n\n'
        f"Source: {directory / 'hierarchy.jsonl'}\n"
        f"SHA-256: {record['files']['hierarchy.jsonl']}\n"
        f"Status: {record.get('status', 'unknown')}; not human gold.\n{provenance}\n"
        f"{len(nodes)} nodes; {len(originals)} represented posts; "
        f"{record['input']['count']} input posts.")]
    for identifier, node in nodes.items():
        view_nodes.append(dict(node_id=identifier, label=node['label'],
            children=node['children'], note_ids=[short_ids[note] for note in node['note_ids']],
            analysis=f"Published UUID: {identifier}\nHeading: {node['label']}\n"
                     f"Fixed meaning: {node['meaning']}\n"
                     f"Parents: {', '.join(parents[identifier]) or '(root)'}"))
    return _write_viewer(output, record['experiment_id'], originals, short_ids, view_nodes, roots)


def export_viewer(directory, output, *, posts=None, root_admissions=None, base_viewer=None):
    """Preserve canonical nodes and their notes; the display container has no notes."""
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('viewer output must not exist')
    if posts is not None:
        if root_admissions is not None or base_viewer is not None:
            raise ValueError('published hierarchies do not accept native admission previews')
        return _export_published_viewer(directory, output, posts)
    if base_viewer is not None and root_admissions is None:
        raise ValueError('base viewer is only supported for saved admission previews')
    state_path = directory / 'state.json'
    saved = read_hierarchy(directory, verified_export=base_viewer)
    state, state_bytes = saved['state'], saved['state_bytes']
    nodes, children, roots = saved['nodes'], saved['children'], saved['roots']
    originals, short_ids = saved['notes'], saved['note_short_ids']
    preview = _root_admissions(saved,directory,root_admissions) if root_admissions else None
    if preview:
        base_count = len(originals)
        selected = set(short_ids) | {n for notes in preview['notes_by_root'].values() for n in notes}
        raw = Path(state['corpus']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != state['sources'][state['corpus']]:
            raise ValueError('admission corpus source changed')
        corpus = json.loads(raw)['notes']
        originals, short_ids, used = [], {}, set()
        for index,note in enumerate(corpus,1):
            if note['note_id'] not in selected:
                continue
            short = note.get('note_short_id') or f'N{index:03d}'
            if note['note_id'] in short_ids or short in used:
                raise ValueError('admission note references must be unique')
            short_ids[note['note_id']] = short
            used.add(short)
            originals.append(dict(note_id=note['note_id'],text=note['text']))
        if set(short_ids) != selected:
            raise ValueError('admission source notes are missing')
        preview.update(base_covered_notes=base_count,preview_covered_notes=len(originals),
                       corpus_notes=len(corpus))
    qualification = state.get('shape', {}).get('qualification', '')
    if preview:
        qualification += '\nExperimental preview includes saved conservative root additions; original hierarchy unchanged.'
    view_nodes = [{'node_id': 'VIEW_ROOT', 'label': directory.name,
        'children': roots, 'note_ids': [], 'analysis':
        'Display-only container for canonical roots. Not a canonical node.\n\n'
        f"Source: {state_path}\nState SHA-256: {hashlib.sha256(state_bytes).hexdigest()}\n"
        f"Status: {state['status']}; not human gold.\n"
        f'{len(nodes)} canonical nodes; {len(originals)} notes.\n{qualification}'}]
    for node in nodes.values():
        support = list(dict.fromkeys(short_ids[entry['note_id']] for entry in node['entries']))
        added = preview['notes_by_root'].get(node['id'],[]) if preview else []
        direct = list(dict.fromkeys([*support, *(short_ids[n] for n in node.get('note_ids', [])),
                                    *(short_ids[n] for n in added)]))
        view_nodes.append({'node_id': node['id'],
            'label': f"{node['subject']} ({node['id']})",
            'children': children[node['id']], 'note_ids': direct, 'analysis':
            f"Canonical ID: {node['id']}\nHeading: {node['subject']}\n"
            f"Fixed meaning: {node['meaning']}\n"
            f"Canonical parents: {', '.join(node['parents']) or '(root)'}"})
    if preview:
        view_nodes[0]['label'] = directory.name+' (conservative root-admission preview)'
    result = _write_viewer(output, output.name if preview else directory.name,
                           originals, short_ids, view_nodes, roots)
    if preview:
        (output/'root-admissions.json').write_text(json.dumps(preview,ensure_ascii=False,indent=2)+'\n')
    return result
