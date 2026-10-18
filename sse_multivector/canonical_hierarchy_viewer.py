"""Export saved canonical graphs for the existing original-note review UI."""
import hashlib
import json
from pathlib import Path

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


def export_viewer(directory, output, *, root_admissions=None, base_viewer=None):
    """Preserve canonical nodes and their notes; the display container has no notes."""
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('viewer output must not exist')
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
    references = [{'note_id': note, 'note_short_id': short} for note, short in short_ids.items()]
    notes_bytes = (json.dumps({'notes': originals}, ensure_ascii=False, indent=2) + '\n').encode()
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
    hierarchy = {'schema_version': 2, 'hierarchy_id': output.name if preview else directory.name,
        'source_sha256': hashlib.sha256(notes_bytes).hexdigest(), 'root_node_id': 'VIEW_ROOT',
        'notes': references, 'nodes': view_nodes}
    output.mkdir(parents=True)
    (output / 'notes.json').write_bytes(notes_bytes)
    (output / 'hierarchy.json').write_text(json.dumps(hierarchy, ensure_ascii=False, indent=2) + '\n')
    if preview:
        (output/'root-admissions.json').write_text(json.dumps(preview,ensure_ascii=False,indent=2)+'\n')
    return {'hierarchy': str(output / 'hierarchy.json'), 'notes': str(output / 'notes.json'),
            'nodes': len(nodes), 'roots': len(roots), 'note_count': len(originals)}
