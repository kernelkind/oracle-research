"""Serialize hierarchy snapshots as unsigned records or signed offline events."""
import hashlib
import json
from graphlib import CycleError, TopologicalSorter
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

try:
    from .canonical_hierarchy import read_hierarchy
except ImportError:
    from canonical_hierarchy import read_hierarchy


ENTRY_KIND = 18680
NODE_KIND = 8680
# Names are local node IDs within one hierarchy file, not global graph identity.
UNSIGNED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, 'urn:oracle-mvp:hierarchy:unsigned:v1')


def unsigned_events(state):
    """Yield unsigned snapshot records, preserving definitions and saved edges.

    UUIDv5 uses the fixed ``urn:oracle-mvp:hierarchy:unsigned:v1`` URL namespace
    and each saved local node ID. References are scoped to the resulting file.
    They do not identify signed Nostr events. Source IDs may be any nonempty
    strings, including IDs from historical synthetic experiments.

    Only notes absent from every child subtree appear directly on a node.
    Descendant membership sets are released after their final parent uses them;
    a last consumer can reuse a child's set rather than copy a whole subtree.
    Work follows graph edges and propagated membership references, never pairs
    of corpus notes. Records are yielded individually after graph validation.
    """
    if not isinstance(state, dict):
        raise ValueError('hierarchy state must be an object')
    menu = state.get('menu', {})
    if not isinstance(menu, dict):
        raise ValueError('hierarchy menu must be an object')
    rows = menu.get('nodes', state.get('nodes', []))
    if not isinstance(rows, list):
        raise ValueError('hierarchy nodes must be a list')
    nodes = {}
    for node in rows:
        if not isinstance(node, dict):
            raise ValueError('hierarchy nodes must be objects')
        identifier = node.get('id')
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('node IDs must be nonempty strings')
        if identifier in nodes:
            raise ValueError('node IDs must be unique')
        for field, description in [('subject', 'title'), ('meaning', 'meaning')]:
            if not isinstance(node.get(field), str) or not node[field].strip():
                raise ValueError(f'node {description} must be a nonempty string')
        parents = node.get('parents')
        if (not isinstance(parents, list)
                or any(not isinstance(parent, str) or not parent.strip() for parent in parents)):
            raise ValueError('node parents must be a list of nonempty IDs')
        if len(parents) != len(set(parents)):
            raise ValueError('node parent references must be unique')
        entries, note_ids = node.get('entries', []), node.get('note_ids', [])
        if (not isinstance(entries, list) or any(
                not isinstance(entry, dict) or not isinstance(entry.get('note_id'), str)
                or not entry['note_id'].strip() for entry in entries)
                or not isinstance(note_ids, list) or any(
                    not isinstance(note, str) or not note.strip() for note in note_ids)):
            raise ValueError('node memberships must contain nonempty source note IDs')
        nodes[identifier] = node
    children = {identifier: [] for identifier in nodes}
    for identifier, node in nodes.items():
        for parent in node['parents']:
            if parent not in nodes:
                raise ValueError('node parent references an unknown node')
            children[parent].append(identifier)
    try:
        order = list(TopologicalSorter({identifier: node['parents']
                                       for identifier, node in nodes.items()}).static_order())
    except CycleError as error:
        raise ValueError('hierarchy graph contains a cycle') from error
    shape = state.get('shape', {})
    if not isinstance(shape, dict):
        raise ValueError('hierarchy shape must be an object')
    roots = [identifier for identifier, node in nodes.items() if not node['parents']]
    saved_roots = shape.get('roots', roots)
    if (not isinstance(saved_roots, list)
            or any(not isinstance(root, str) for root in saved_roots)
            or len(saved_roots) != len(set(saved_roots)) or set(saved_roots) != set(roots)):
        raise ValueError('hierarchy roots differ from saved parents')
    node_uuids = {identifier: str(uuid.uuid5(UNSIGNED_NAMESPACE, identifier))
                  for identifier in nodes}
    memberships = {}
    remaining = {identifier: len(node['parents']) for identifier, node in nodes.items()}
    for identifier in reversed(order):
        node = nodes[identifier]
        links = children[identifier]
        reusable = [child for child in links if remaining[child] == 1]
        largest = max(reusable, key=lambda child: len(memberships[child]), default=None)
        below = memberships[largest] if largest is not None else set()
        for child in links:
            if child != largest:
                below.update(memberships[child])
        own = dict.fromkeys(entry['note_id'] for entry in node.get('entries', []))
        own.update(dict.fromkeys(node.get('note_ids', [])))
        direct = [note for note in own if note not in below]
        below.update(own)
        for child in links:
            remaining[child] -= 1
            if not remaining[child]:
                del memberships[child]
        if remaining[identifier]:
            memberships[identifier] = below
        tags = [['d', node_uuids[identifier]], ['title', node['subject']]]
        tags.extend(['child', node_uuids[child]] for child in links)
        tags.extend(['e', note] for note in direct)
        yield dict(kind=NODE_KIND, tags=tags, content=node['meaning'])
    yield dict(kind=ENTRY_KIND, tags=[['child', node_uuids[root]] for root in saved_roots],
               content='')


def _nak(binary, arguments, *, data, environment=None):
    try:
        result = subprocess.run([binary, *arguments], input=data, text=True,
                                capture_output=True, env=environment, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError('could not run the local nak signer') from error
    if result.returncode:
        # Signer diagnostics can contain private input. Never relay them.
        raise ValueError(f'nak {arguments[0]} failed (exit {result.returncode})')
    return result.stdout


def _signed_event(binary, environment, pubkey, created_at, kind, tags):
    fields = dict(pubkey=pubkey, created_at=created_at, kind=kind, tags=tags, content='')
    encoded = _nak(binary, ['event', '--kind', str(kind), '--created-at', str(created_at)],
                   data=json.dumps(fields, ensure_ascii=False) + '\n', environment=environment)
    try:
        event = json.loads(encoded)
    except json.JSONDecodeError as error:
        raise ValueError('nak returned an invalid event') from error
    if (not isinstance(event, dict) or set(event) != {*fields, 'id', 'sig'}
            or any(event.get(key) != value for key, value in fields.items())
            or not isinstance(event['id'], str) or not re.fullmatch('[0-9a-f]{64}', event['id'])
            or not isinstance(event['sig'], str) or not re.fullmatch('[0-9a-f]{128}', event['sig'])):
        raise ValueError('nak changed the requested event fields')
    serialized = json.dumps([0, pubkey, created_at, kind, tags, ''],
                            ensure_ascii=False, separators=(',', ':')).encode()
    if hashlib.sha256(serialized).hexdigest() != event['id']:
        raise ValueError('nak returned an event with a different canonical ID')
    return event


def export_nostr(directory, output, secret_key_file, *, nak='nak', created_at=None,
                 uuid_namespace=None):
    """Preserve graph order; list only posts absent from every child subtree."""
    directory, output = Path(directory).resolve(), Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError('Nostr export output must not exist')
    if directory in output.parents:
        raise ValueError('Nostr export output must be outside the saved hierarchy')
    binary = shutil.which(str(nak))
    if binary is None:
        raise ValueError('nak is required for offline Nostr signing')
    secret = Path(secret_key_file).expanduser().read_text().strip()
    if not re.fullmatch('[0-9a-fA-F]{64}', secret):
        raise ValueError('secret key file must contain one 64-character hexadecimal key')
    pubkey = _nak(binary, ['key', 'public'], data=secret + '\n').strip()
    if not re.fullmatch('[0-9a-f]{64}', pubkey):
        raise ValueError('nak did not return one public key')
    created_at = int(time.time()) if created_at is None else created_at
    if type(created_at) is not int or created_at < 0:
        raise ValueError('created_at must be a nonnegative integer timestamp')
    namespace = (uuid.UUID(str(uuid_namespace)) if uuid_namespace is not None else
                 uuid.uuid5(uuid.NAMESPACE_URL, f'nostr:{pubkey}:{directory.as_uri()}'))
    saved = read_hierarchy(directory)
    if saved['state'].get('status') != 'complete':
        raise ValueError('Nostr export requires a complete saved hierarchy')
    nodes, children, roots = saved['nodes'], saved['children'], saved['roots']
    short_ids = saved['note_short_ids']
    if any(len(links) != len(set(links)) for links in children.values()):
        raise ValueError('node child references must be unique')
    if any(not isinstance(note, str) or not re.fullmatch('[0-9a-f]{64}', note) for note in short_ids):
        raise ValueError('source note IDs must be full lowercase hexadecimal Nostr event IDs')
    memberships, direct = {}, {}
    for identifier in reversed(saved['order']):
        node = nodes[identifier]
        if not isinstance(node['subject'], str) or not node['subject'].strip():
            raise ValueError('node title must be nonempty')
        own = {entry['note_id'] for entry in node['entries']} | set(node.get('note_ids', []))
        below = set().union(*(memberships[child] for child in children[identifier]))
        memberships[identifier] = own | below
        direct[identifier] = sorted(own - below, key=short_ids.__getitem__)
        if len(direct[identifier]) > 500:
            raise ValueError(f'node {identifier} exceeds 500 direct note IDs')
    node_uuids = {identifier: str(uuid.uuid5(namespace, identifier)) for identifier in nodes}
    environment = {**os.environ, 'NOSTR_SECRET_KEY': secret}
    events, event_ids = [], {}
    for identifier in reversed(saved['order']):
        tags = [['d', node_uuids[identifier]], ['title', nodes[identifier]['subject']]]
        tags += [['child', node_uuids[child], event_ids[child]] for child in children[identifier]]
        tags += [['e', note] for note in direct[identifier]]
        event = _signed_event(binary, environment, pubkey, created_at, NODE_KIND, tags)
        events.append(event)
        event_ids[identifier] = event['id']
    entry = _signed_event(binary, environment, pubkey, created_at, ENTRY_KIND,
                          [['child', node_uuids[root], event_ids[root]] for root in roots])
    events.append(entry)
    encoded = ''.join(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n'
                      for event in events)
    _nak(binary, ['verify'], data=encoded)
    # Link a complete file into place, refusing races with another export.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                                     prefix='.nostr-', delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(encoded)
            temporary.flush()
            os.fsync(temporary.fileno())
            os.link(temporary_path, output)
        finally:
            temporary_path.unlink(missing_ok=True)
    return dict(output=str(output), pubkey=pubkey, starting_event=entry['id'],
                node_events=len(nodes), roots=len(roots),
                source_notes=len(set().union(*(set(notes) for notes in direct.values()))),
                max_notes_per_node=max(map(len, direct.values())),
                uuid_namespace=str(namespace), created_at=created_at,
                source_state_sha256=hashlib.sha256(saved['state_bytes']).hexdigest())
