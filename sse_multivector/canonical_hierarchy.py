"""Read the saved graph and original-note references used by hierarchy exports."""
import hashlib
import json
from graphlib import TopologicalSorter
from pathlib import Path

try:
    from . import canonical_trial
except ImportError:
    import canonical_trial


def _verify_export(directory, state, state_bytes, exported):
    """Reuse a verified export of these exact state/corpus bytes, not its history."""
    exported = Path(exported).resolve()
    provenance = json.loads((exported/'provenance.json').read_bytes())
    if (Path(provenance['state']).resolve() != directory/'state.json'
            or provenance['state_sha256'] != hashlib.sha256(state_bytes).hexdigest()):
        raise ValueError('verified viewer state changed')
    files = {}
    for name in ['hierarchy.json','notes.json']:
        files[name] = (exported/name).read_bytes()
        if hashlib.sha256(files[name]).hexdigest() != provenance['files'][name]:
            raise ValueError('verified viewer checksum mismatch: '+name)
    if json.loads(files['hierarchy.json'])['source_sha256'] != hashlib.sha256(files['notes.json']).hexdigest():
        raise ValueError('verified viewer note binding differs')
    corpus = Path(state['corpus'])
    if (str(corpus) not in state['sources']
            or hashlib.sha256(corpus.read_bytes()).hexdigest() != state['sources'][str(corpus)]):
        raise ValueError('verified viewer corpus changed')


def read_hierarchy(directory, *, verified_export=None):
    directory = Path(directory).resolve()
    state_bytes = (directory / 'state.json').read_bytes()
    state = json.loads(state_bytes)
    if verified_export is None:
        canonical_trial._check(state, verify_current_code=False)
    else:
        _verify_export(directory, state, state_bytes, verified_export)
    rows = state.get('menu', {}).get('nodes', state['nodes'])
    nodes = {node['id']: node for node in rows}
    if not nodes or len(nodes) != len(rows) or 'VIEW_ROOT' in nodes:
        raise ValueError('invalid canonical viewer node IDs')
    children = {identifier: [] for identifier in nodes}
    for node in nodes.values():
        for parent in node['parents']:
            children[parent].append(node['id'])
    order = list(TopologicalSorter({node['id']: node['parents'] for node in nodes.values()}).static_order())
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
    notes, short_ids, used_short_ids = [], {}, set()
    for index, note in enumerate(corpus, 1):
        if note['note_id'] not in selected:
            continue
        short = note.get('note_short_id') or f"N{index:03d}"
        if note['note_id'] in short_ids or short in used_short_ids:
            raise ValueError('canonical viewer note references must be unique')
        short_ids[note['note_id']] = short
        used_short_ids.add(short)
        notes.append({'note_id': note['note_id'], 'text': note['text']})
    if set(short_ids) != selected:
        raise ValueError('canonical viewer source notes are missing')
    return dict(state=state, state_bytes=state_bytes, nodes=nodes, children=children,
                roots=roots, order=order, notes=notes, note_short_ids=short_ids)
