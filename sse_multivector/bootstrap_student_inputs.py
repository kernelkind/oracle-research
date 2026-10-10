"""Bounded Bootstrap pilot inputs from selected SP and TRAIN-only post text.

SP entries supply inputs, never Bootstrap targets. Original TRAIN membership
is preserved; the pilot's training and evaluation roles use distinct authors
and normalized post texts inside that membership. No upstream paths are followed.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

from . import extraction_pipeline as engine
from .hierarchy_inputs import validate_subjects


def prepare(source, base):
    engine._expect_fields(source, 'Bootstrap student input selection', {
        'schema_version', 'registry', 'manifest', 'split_manifest', 'posts',
        'seed', 'train_notes', 'evaluation_notes', 'entries_per_note', 'role'})
    if source['schema_version'] != 1 or type(source['schema_version']) is not int:
        raise ValueError('expected Bootstrap input selection schema 1')
    if source['role'] not in {'train', 'evaluation'}:
        raise ValueError('expected train or evaluation data role')
    for key in ('train_notes', 'evaluation_notes', 'entries_per_note'):
        if type(source[key]) is not int or not 1 <= source[key] <= 1000:
            raise ValueError(f'{key} must be an integer from 1 to 1000')
    seed = engine._expect_string(source['seed'], 'selection seed')
    protected = {}

    def load(key):
        ref = source[key]
        fields = {'path', 'sha256'} | ({'format'} if key == 'posts' and 'format' in ref else set())
        engine._expect_fields(ref, key, fields)
        if not isinstance(ref['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256']):
            raise ValueError(f'{key} requires a SHA-256 binding')
        path = engine._resolve_path(ref['path'], key, Path(base))
        raw = path.read_bytes()
        if engine._sha256_bytes(raw) != ref['sha256']:
            raise ValueError(f'{key} hash mismatch')
        protected[str(path)] = ref['sha256']
        if key == 'posts' and ref.get('format') == 'subject_train_jsonl':
            return raw, path
        if key == 'posts' and ref.get('format', 'posts') != 'posts':
            raise ValueError('expected posts or subject_train_jsonl format')
        return json.loads(raw), path

    splits, _ = load('split_manifest')
    if splits.get('schema_version') != 2 or splits.get('tasks') != {'subjects': 'ASv6.100'}:
        raise ValueError('expected frozen ASv6.100 subjects-only split metadata')
    assignments = {}
    for split, key in [('train', 'train_note_ids'), ('validation', 'evaluation_note_ids'),
                       ('test', 'test_note_ids')]:
        for nid in engine._validate_string_array(splits[key], key, allow_empty=False):
            if nid in assignments:
                raise ValueError('source split rosters overlap or repeat a note')
            assignments[nid] = split
    registry, registry_path = load('registry')
    manifest, _ = load('manifest')
    if (registry.get('schema_version') != 1 or manifest.get('schema_version') != 1
            or manifest.get('files', {}).get(registry_path.name) != source['registry']['sha256']):
        raise ValueError('selected registry manifest does not bind registry bytes')
    registry_posts = {}
    for post in registry['posts']:
        nid = post['note_id']
        if (nid in registry_posts or post.get('split') not in {'train', 'validation'}
                or post['split'] != assignments.get(nid)):
            raise ValueError('registry post differs from allowed source membership')
        registry_posts[nid] = post
    by_note = defaultdict(list)
    for index, row in enumerate(registry['subjects']):
        nid = row['note_id']
        if (type(row['index']) is not int or row['index'] != index or nid not in registry_posts
                or row['split'] != registry_posts[nid]['split']):
            raise ValueError('subject identity or split differs from selected registry')
        if row['split'] == 'train':
            by_note[nid].append({k: row[k] for k in ('number', 'subject', 'context')})
    for rows in by_note.values():
        validate_subjects({'subjects': rows})
    posts, _ = load('posts')
    if source['posts'].get('format') == 'subject_train_jsonl':
        if splits.get('outputs', {}).get('train.jsonl') != source['posts']['sha256']:
            raise ValueError('TRAIN JSONL differs from frozen split manifest')
        # Check identity headers for every row before decoding any prompt or answer.
        lines = posts.splitlines()
        header = re.compile(rb'^\s*\{\s*"note_id"\s*:\s*("(?:[^"\\]|\\.)*")\s*,')
        identifiers = []
        for line in lines:
            match = header.match(line)
            if match is None:
                raise ValueError('expected first-field TRAIN note_id headers')
            identifiers.append(json.loads(match[1]))
        if (len(identifiers) != len(set(identifiers))
                or set(identifiers) != {nid for nid, split in assignments.items() if split == 'train'}):
            raise ValueError('post source must be exactly the frozen TRAIN-only JSONL')
        originals = []
        for line, nid in zip(lines, identifiers):
            row = json.loads(line)
            messages = row.get('prompt')
            if (row.get('task') != 'subjects' or not isinstance(messages, list) or len(messages) != 1
                    or messages[0].get('role') != 'user'):
                raise ValueError('expected original subjects-only TRAIN prompt')
            content = messages[0]['content']
            instruction, separator, text = content.partition('\n\n<post>\n')
            if (not separator or not text.endswith('\n</post>')
                    or engine._sha256_bytes(instruction.encode()) != splits['subject_instruction_sha256']):
                raise ValueError('TRAIN post framing or ASv6.100 instruction differs')
            originals.append(dict(note_id=nid, pubkey=registry_posts[nid]['pubkey'],
                                  text=text[:-len('\n</post>')]))
        posts = dict(schema_version=1, notes=originals)
    if posts.get('schema_version') != 1 or not isinstance(posts.get('notes'), list):
        raise ValueError('expected a TRAIN-only post collection with schema 1')
    originals = {}
    for post in posts['notes']:
        nid = post['note_id']
        if (assignments.get(nid) != 'train' or nid in originals or nid not in registry_posts
                or post.get('split', 'train') != 'train'):
            raise ValueError('post collection must be TRAIN-only without repeated identities')
        saved = registry_posts[nid]
        text = engine._expect_string(post['text'], 'original post text')
        if (post.get('pubkey') != saved['pubkey']
                or hashlib.sha256(text.encode()).hexdigest() != saved['text_sha256']):
            raise ValueError('post text or author differs from selected SP source')
        originals[nid] = post

    def rank(value):
        return hashlib.sha256(engine._canonical_json_bytes([seed, value])).hexdigest()

    selected, seen_authors, seen_texts = [], set(), set()
    for nid in sorted(originals, key=rank):
        post = originals[nid]
        author = engine._expect_string(post['pubkey'], 'post author')
        normalized = ' '.join(post['text'].split())
        roots = defaultdict(list)
        for row in by_note[nid]:
            roots[row['number'].split('.')[0]].append(row)
        eligible = [r for r, rows in roots.items() if len(rows) >= source['entries_per_note']]
        if not eligible or author in seen_authors or normalized in seen_texts:
            continue
        root = min(eligible, key=lambda r: rank([nid, r]))
        rows = sorted(roots[root], key=lambda row: tuple(map(int, row['number'].split('.'))))
        leaf = min(rows, key=lambda row: (-row['number'].count('.'), rank([nid, row['number']])))
        numbers = list(dict.fromkeys([root, leaf['number']]))
        parts = leaf['number'].split('.')
        numbers.extend('.'.join(parts[:depth]) for depth in range(len(parts)-1, 1, -1))
        numbers.extend(row['number'] for row in sorted(rows, key=lambda row: rank([nid, row['number']])))
        numbers = list(dict.fromkeys(numbers))[:source['entries_per_note']]
        selected.append((post, rows, numbers))
        seen_authors.add(author)
        seen_texts.add(normalized)
        if len(selected) == source['train_notes'] + source['evaluation_notes']:
            break
    if len(selected) != source['train_notes'] + source['evaluation_notes']:
        raise ValueError('not enough distinct TRAIN authors/texts with complete selected trees')
    roles = {'train': selected[:source['train_notes']], 'evaluation': selected[source['train_notes']:]}
    cases = []
    for post, rows, numbers in roles[source['role']]:
        for number in numbers:
            payload = {'local': {'post': post['text'], 'hierarchy': {'selected': number, 'entries': rows}}}
            identity = engine._sha256_bytes(engine._canonical_json_bytes(payload))
            cases.append(dict(id='bootstrap-' + identity,
                inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                evidence=dict(local={'note_id': post['note_id'], 'number': number},
                    pubkey=post['pubkey'], split='train', role=source['role'],
                    source_registry=source['registry'], source_posts=source['posts'],
                    application_allowed=False, semantic_status='Unlabelled Bootstrap input; SP is not a meaning target.')))
    return cases, protected, dict(method='bootstrap_student_inputs', role=source['role'], seed=seed,
        train_note_ids=[p['note_id'] for p, _, _ in roles['train']],
        evaluation_note_ids=[p['note_id'] for p, _, _ in roles['evaluation']],
        entries_per_note=source['entries_per_note'], cases=len(cases),
        source_split='train', target_answers=0, application_allowed=False)
