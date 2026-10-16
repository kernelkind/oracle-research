"""Export the toy hierarchy snapshot protocol as signed, offline JSONL events."""
import hashlib
import json
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
