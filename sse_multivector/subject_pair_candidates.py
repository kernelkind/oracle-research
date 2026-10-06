"""Bounded, input-only SHR nominations from a hash-bound TRAIN SP registry.

No SP edge, wording match or nomination supplies an SHR relation label.
References in upstream provenance are retained as evidence and never followed.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import re

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


RULES = ('sp_edges', 'siblings', 'same_subject', 'lexical_overlap', 'random_cross_post')


def prepare(spec, base, read):
    explicit = 'pairs' in spec
    engine._expect_fields(spec, 'registry pair selection', {
        'schema_version', 'registry', 'manifest', 'split_manifest', 'split'} | (
        {'pairs', 'entry_order_controls'} if explicit else
        {'seed', 'per_rule', 'max_per_post', 'max_per_subject', 'posting_cap'}))
    if type(spec['schema_version']) is not int or spec['schema_version'] != 1:
        raise ValueError('expected registry pair selection schema_version 1')
    if spec['split'] != 'train':
        raise ValueError('registry pair selection supports TRAIN inputs only')
    if not explicit:
        seed = engine._expect_identifier(spec['seed'], 'selection seed')
        for key in ('per_rule', 'max_per_post', 'max_per_subject', 'posting_cap'):
            if type(spec[key]) is not int or not 1 <= spec[key] <= 10000:
                raise ValueError(f'{key} must be an integer from 1 to 10000')

    def load(key):
        ref = spec[key]
        engine._expect_fields(ref, key, {'path', 'sha256'})
        if not isinstance(ref['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256']):
            raise ValueError(f'{key} requires a SHA-256 binding')
        path = engine._resolve_path(ref['path'], key, Path(base))
        if engine._sha256_file(path) != ref['sha256']:
            raise ValueError(f'{key} hash mismatch')
        return read(path), path

    registry, registry_path = load('registry')
    manifest, _ = load('manifest')
    splits, _ = load('split_manifest')
    if (manifest.get('schema_version') != 1
            or manifest.get('files', {}).get(registry_path.name) != spec['registry']['sha256']):
        raise ValueError('selected registry manifest does not bind registry bytes')
    if registry.get('schema_version') != 1 or splits.get('schema_version') != 2:
        raise ValueError('expected registry schema 1 and prepared split manifest schema 2')
    assignments = {}
    for split, key in (('train', 'train_note_ids'), ('validation', 'evaluation_note_ids'),
                       ('test', 'test_note_ids')):
        ids = engine._validate_string_array(splits[key], key, allow_empty=False)
        for nid in ids:
            if nid in assignments:
                raise ValueError('frozen split rosters overlap or repeat a note')
            assignments[nid] = split
    posts, authors = {}, defaultdict(set)
    for post in registry['posts']:
        nid = engine._expect_identifier(post['note_id'], 'note_id')
        if (nid in posts or post.get('split') not in {'train', 'validation'}
                or post['split'] != assignments.get(nid)):
            raise ValueError('registry post differs from permitted frozen membership')
        author = engine._expect_string(post['pubkey'], 'pubkey')
        authors[author].add(post['split'])
        posts[nid] = post
    if (set(posts) != {nid for nid, split in assignments.items() if split != 'test'}
            or any(len(values) != 1 for values in authors.values())):
        raise ValueError('registry roster or author separation differs from frozen splits')

    subjects, numbers, entries = registry['subjects'], {}, {}
    for index, entry in enumerate(subjects):
        nid = entry['note_id']
        if (type(entry['index']) is not int or entry['index'] != index or nid not in posts
                or entry.get('split') != posts[nid]['split']):
            raise ValueError('subject index or split differs from registry post')
        if entry['split'] != 'train':
            continue
        engine._expect_string(entry['subject'], 'subject')
        engine._expect_string(entry['context'], 'context')
        number = entry['number']
        if not isinstance(number, str) or not re.fullmatch(r'[1-9][0-9]*(\.[1-9][0-9]*)*', number):
            raise ValueError('invalid source subject number')
        if (nid, number) in numbers:
            raise ValueError('repeated source subject number')
        numbers[nid, number] = index
        entries[index] = entry
    if len(entries) < 2:
        raise ValueError('need at least two TRAIN subject entries')

    children, saved_edges = defaultdict(list), set()
    for edge in registry['edges']:
        if (not isinstance(edge, list) or len(edge) != 2 or any(
                type(i) is not int or not 0 <= i < len(subjects) for i in edge)):
            raise ValueError('invalid registry SP edge')
        a, b = edge
        if subjects[a]['split'] != subjects[b]['split']:
            raise ValueError('SP edge crosses frozen splits')
        if a not in entries:
            continue
        if (entries[a]['note_id'] != entries[b]['note_id'] or
                entries[b]['number'].rsplit('.', 1)[0] != entries[a]['number']
                or '.' not in entries[b]['number'] or (a, b) in saved_edges):
            raise ValueError('SP edge differs from original note/number identities')
        saved_edges.add((a, b))
        children[a].append(b)

    if explicit:
        return _prepare_groups(spec, entries, posts)

    def rank(value):
        return hashlib.sha256(json.dumps([seed, value], ensure_ascii=False,
                                        separators=(',', ':')).encode()).hexdigest()

    pools = {rule: set() for rule in RULES}
    for a, b in saved_edges:
        pools['sp_edges'].add(tuple(sorted((a, b))))

    def neighbours(indices):
        """A hashed ring visits O(n) pairs, including large wording groups."""
        ordered = sorted(set(indices), key=rank)
        if len(ordered) < 2:
            return []
        return [tuple(sorted((a, b))) for a, b in zip(ordered, ordered[1:] + ordered[:1])]

    for siblings in children.values():
        pools['siblings'].update(neighbours(siblings))
    wordings, tokens = defaultdict(dict), defaultdict(list)
    stopwords = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'their', 'about'}
    for i, entry in entries.items():
        wording, nid = entry['subject'].casefold(), entry['note_id']
        # One source-bound representative per note avoids pairs of a note with itself.
        previous = wordings[wording].get(nid)
        if previous is None or rank(i) < rank(previous):
            wordings[wording][nid] = i
        for token in set(re.findall(r'\w{3,}', wording)) - stopwords:
            tokens[token].append(i)
    for group in wordings.values():
        pools['same_subject'].update(neighbours(group.values()))
    skipped_common = 0
    for indices in tokens.values():
        if len(indices) > spec['posting_cap']:
            skipped_common += 1
            continue
        for a, b in neighbours(indices):
            if (entries[a]['note_id'] != entries[b]['note_id'] and
                    entries[a]['subject'].casefold() != entries[b]['subject'].casefold()):
                pools['lexical_overlap'].add((a, b))
    for a, b in neighbours(entries):
        if (entries[a]['note_id'] != entries[b]['note_id'] and
                entries[a]['subject'].casefold() != entries[b]['subject'].casefold()):
            pools['random_cross_post'].add((a, b))

    selected, post_counts, wording_counts = {}, Counter(), Counter()
    selected_counts = Counter()
    for rule in RULES:
        for pair in sorted(pools[rule], key=lambda p: rank([rule, p])):
            if selected_counts[rule] >= spec['per_rule']:
                break
            nids = {entries[i]['note_id'] for i in pair}
            names = {entries[i]['subject'].casefold() for i in pair}
            if pair not in selected:
                if (any(post_counts[n] >= spec['max_per_post'] for n in nids) or
                        any(wording_counts[n] >= spec['max_per_subject'] for n in names)):
                    continue
                selected[pair] = []
                post_counts.update(nids)
                wording_counts.update(names)
            selected[pair].append(rule)
            selected_counts[rule] += 1
    cases = []
    for pair in sorted(selected, key=rank):
        family = 'SPPAIR-' + hashlib.sha256(json.dumps(
            [spec['registry']['sha256'], pair], separators=(',', ':')).encode()).hexdigest()[:24]
        rules = [rule for rule in RULES if pair in pools[rule]]
        for direction, (a, b) in (('forward', pair), ('reverse', pair[::-1])):
            payload = {side: [{k: entries[i][k] for k in ('subject', 'context')}]
                       for side, i in (('A', a), ('B', b))}
            evidence = dict(split='train', family_id=family, direction=direction,
                semantic_status='unlabelled candidate; nominations do not establish relations',
                nomination_rules=rules, selected_by=selected[pair],
                A=dict(subject_entries=[entries[a]]), B=dict(subject_entries=[entries[b]]),
                source_posts=[posts[n] for n in sorted({entries[a]['note_id'], entries[b]['note_id']})],
                source=spec['registry'])
            cases.append(dict(id=family + '-' + direction,
                inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False, indent=2)}, evidence=evidence))
    preparation = dict(method='registry_subject_pairs', split='train', seed=seed,
        train_posts=sum(p['split'] == 'train' for p in posts.values()), train_entries=len(entries),
        candidate_pairs_by_rule={r: len(pools[r]) for r in RULES},
        selected_pairs_by_rule={r: selected_counts[r] for r in RULES},
        selected_families=len(selected), directed_cases=len(cases), source_posts=len(post_counts),
        source_authors=len({posts[n]['pubkey'] for n in post_counts}),
        max_selected_pairs_per_post=max(post_counts.values(), default=0),
        max_selected_pairs_per_wording=max(wording_counts.values(), default=0),
        skipped_common_token_postings=skipped_common, relation_labels=0,
        validation_selected=False, final_test_content_opened=False,
        limits={k: spec[k] for k in ('per_rule', 'max_per_post', 'max_per_subject', 'posting_cap')},
        interpretation='Bounded nomination sample, not relation balance or deployment frequencies.')
    return cases, preparation


def _prepare_groups(spec, entries, posts):
    """Explicit source indices; bounded reverse-order controls, never permutations."""
    pairs = spec['pairs']
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= 10000:
        raise ValueError('registry groups require from 1 to 10000 explicit pairs')
    if type(spec['entry_order_controls']) is not bool:
        raise ValueError('entry_order_controls must be boolean')
    cases, seen_ids, seen_groups, selected_posts = [], set(), set(), set()
    coverage_counts = Counter()
    selected_entries = set()
    for pair in pairs:
        engine._expect_fields(pair, 'registry group pair', {'id', 'A', 'B', 'coverage', 'purpose'})
        selection_id = engine._expect_identifier(pair['id'], 'registry group pair id')
        if selection_id in seen_ids:
            raise ValueError('repeated registry group pair id')
        seen_ids.add(selection_id)
        coverage = engine._validate_string_array(pair['coverage'], 'coverage', allow_empty=False)
        purpose = engine._expect_string(pair['purpose'], 'purpose')
        for side in ('A', 'B'):
            indices = pair[side]
            if (not isinstance(indices, list) or not 1 <= len(indices) <= 64
                    or any(type(i) is not int or i not in entries for i in indices)):
                raise ValueError('registry group sides require 1 to 64 permitted TRAIN indices')
            if len(set(indices)) != len(indices):
                raise ValueError('registry group side repeats a source index')
        # A/B and entry order are controls of one source-bound family, not new samples.
        groups = sorted([sorted(pair['A']), sorted(pair['B'])])
        identity = json.dumps([spec['registry']['sha256'], groups], separators=(',', ':'))
        if identity in seen_groups:
            raise ValueError('repeated registry groups, including reversal or reordered entries')
        seen_groups.add(identity)
        family = 'SPGROUP-' + hashlib.sha256(identity.encode()).hexdigest()[:24]
        coverage_counts.update(coverage)
        selected_entries.update(pair['A'] + pair['B'])
        nids = {entries[i]['note_id'] for i in pair['A'] + pair['B']}
        selected_posts.update(nids)
        orders = [('original', pair['A'], pair['B'])]
        if spec['entry_order_controls']:
            if len(pair['A']) > 1:
                orders.append(('reverse_A', pair['A'][::-1], pair['B']))
            if len(pair['B']) > 1:
                orders.append(('reverse_B', pair['A'], pair['B'][::-1]))
            if len(pair['A']) > 1 and len(pair['B']) > 1:
                orders.append(('reverse_both', pair['A'][::-1], pair['B'][::-1]))
        for order, a, b in orders:
            for direction, left, right in (('forward', a, b), ('reverse', b, a)):
                payload = {side: [{k: entries[i][k] for k in ('subject', 'context')} for i in group]
                           for side, group in (('A', left), ('B', right))}
                evidence = dict(split='train', family_id=family, selection_id=selection_id,
                    direction=direction, entry_order=order, coverage=coverage, purpose=purpose,
                    semantic_status='unlabelled candidate; selection does not establish relations',
                    grouping_status='diagnostic input grouping; not an accepted hierarchy node',
                    A=dict(subject_entries=[entries[i] for i in left]),
                    B=dict(subject_entries=[entries[i] for i in right]),
                    source_posts=[posts[n] for n in sorted(nids)], source=spec['registry'])
                case_id = selection_id + ('-' + order if order != 'original' else '') + '-' + direction
                cases.append(dict(id=case_id,
                    inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False, indent=2)}, evidence=evidence))
    # Caller-chosen IDs must also remain unique after adding control suffixes.
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('registry group pair ids collide with generated control case ids')
    preparation = dict(method='registry_subject_pairs', selection_mode='explicit_groups', split='train',
        train_posts=sum(p['split'] == 'train' for p in posts.values()), train_entries=len(entries),
        selected_families=len(pairs), directed_cases=len(cases),
        coverage_families=dict(sorted(coverage_counts.items())), selected_entries=len(selected_entries),
        source_posts=len(selected_posts), source_authors=len({posts[n]['pubkey'] for n in selected_posts}),
        entry_order_controls=spec['entry_order_controls'], relation_labels=0,
        validation_selected=False, final_test_content_opened=False,
        limits=dict(max_pairs=10000, max_entries_per_side=64, max_control_cases_per_pair=8),
        interpretation='Explicit diagnostic input selection, not relation balance or deployment frequencies.')
    return cases, preparation
