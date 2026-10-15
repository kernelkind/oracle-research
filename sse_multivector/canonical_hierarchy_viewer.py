"""Export saved canonical graphs for the existing original-note review UI."""
import hashlib
import json
from graphlib import TopologicalSorter
from pathlib import Path

try:
    from . import canonical_trial
except ImportError:
    import canonical_trial


def export_viewer(directory, output):
    """Preserve canonical nodes and their notes; the display container has no notes."""
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('viewer output must not exist')
    state_path = directory / 'state.json'
    state_bytes = state_path.read_bytes()
    state = json.loads(state_bytes)
    canonical_trial._check(state, verify_current_code=False)
    rows = state.get('menu', {}).get('nodes', state['nodes'])
    nodes = {node['id']: node for node in rows}
    if not nodes or len(nodes) != len(rows) or 'VIEW_ROOT' in nodes:
        raise ValueError('invalid canonical viewer node IDs')
    children = {identifier: [] for identifier in nodes}
    for node in nodes.values():
        for parent in node['parents']:
            children[parent].append(node['id'])
    tuple(TopologicalSorter({node['id']: node['parents'] for node in nodes.values()}).static_order())
    roots = [node['id'] for node in nodes.values() if not node['parents']]
    roots = state.get('shape', {}).get('roots', roots)
    if (len(roots) != len(set(roots)) or
            set(roots) != {node['id'] for node in nodes.values() if not node['parents']}):
        raise ValueError('canonical viewer roots differ from saved parents')
    selected = {note for node in nodes.values()
                for note in [*(e['note_id'] for e in node['entries']), *node.get('note_ids', [])]}
    corpus_path = Path(state['corpus'])
    if str(corpus_path) not in state['sources']:
        raise ValueError('canonical viewer corpus is not source-bound')
    corpus = json.loads(corpus_path.read_bytes())['notes']
    originals, references, short_ids, used_short_ids = [], [], {}, set()
    for index, note in enumerate(corpus, 1):
        if note['note_id'] not in selected:
            continue
        short = note.get('note_short_id') or f"N{index:03d}"
        if note['note_id'] in short_ids or short in used_short_ids:
            raise ValueError('canonical viewer note references must be unique')
        short_ids[note['note_id']] = short
        used_short_ids.add(short)
        originals.append({'note_id': note['note_id'], 'text': note['text']})
        references.append({'note_id': note['note_id'], 'note_short_id': short})
    if set(short_ids) != selected:
        raise ValueError('canonical viewer source notes are missing')
    notes_bytes = (json.dumps({'notes': originals}, ensure_ascii=False, indent=2) + '\n').encode()
    qualification = state.get('shape', {}).get('qualification', '')
    view_nodes = [{'node_id': 'VIEW_ROOT', 'label': directory.name,
        'children': roots, 'note_ids': [], 'analysis':
        'Display-only container for canonical roots. Not a canonical node.\n\n'
        f"Source: {state_path}\nState SHA-256: {hashlib.sha256(state_bytes).hexdigest()}\n"
        f"Status: {state['status']}; not human gold.\n"
        f'{len(nodes)} canonical nodes; {len(originals)} notes.\n{qualification}'}]
    for node in nodes.values():
        support = list(dict.fromkeys(short_ids[entry['note_id']] for entry in node['entries']))
        direct = list(dict.fromkeys([*support, *(short_ids[n] for n in node.get('note_ids', []))]))
        view_nodes.append({'node_id': node['id'],
            'label': f"{node['subject']} ({node['id']})",
            'children': children[node['id']], 'note_ids': direct, 'analysis':
            f"Canonical ID: {node['id']}\nHeading: {node['subject']}\n"
            f"Fixed meaning: {node['meaning']}\n"
            f"Canonical parents: {', '.join(node['parents']) or '(root)'}"})
    hierarchy = {'schema_version': 2, 'hierarchy_id': directory.name,
        'source_sha256': hashlib.sha256(notes_bytes).hexdigest(), 'root_node_id': 'VIEW_ROOT',
        'notes': references, 'nodes': view_nodes}
    output.mkdir(parents=True)
    (output / 'notes.json').write_bytes(notes_bytes)
    (output / 'hierarchy.json').write_text(json.dumps(hierarchy, ensure_ascii=False, indent=2) + '\n')
    return {'hierarchy': str(output / 'hierarchy.json'), 'notes': str(output / 'notes.json'),
            'nodes': len(nodes), 'roots': len(roots), 'note_count': len(originals)}
