"""Export saved canonical graphs for the existing original-note review UI."""
import hashlib
import json
from pathlib import Path

try:
    from .canonical_hierarchy import read_hierarchy
except ImportError:
    from canonical_hierarchy import read_hierarchy


def export_viewer(directory, output):
    """Preserve canonical nodes and their notes; the display container has no notes."""
    directory, output = Path(directory).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('viewer output must not exist')
    state_path = directory / 'state.json'
    saved = read_hierarchy(directory)
    state, state_bytes = saved['state'], saved['state_bytes']
    nodes, children, roots = saved['nodes'], saved['children'], saved['roots']
    originals, short_ids = saved['notes'], saved['note_short_ids']
    references = [{'note_id': note, 'note_short_id': short} for note, short in short_ids.items()]
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
