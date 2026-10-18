"""Offline, source-bound corpus sampling and protected train/validation/test splits."""
import hashlib
import json
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

FORMS = set('NEWS OPINION REPORT PERSONAL PROMO CAPTION RESOURCE QUOTE EXPLANATION ADVICE SOCIAL QUESTION HUMOR CREATIVE FACT METADATA'.split())
POINTER = re.compile(r'https?://\S+|(?:nostr:)?(?:npub|nprofile|note|nevent|naddr|nsec)1[a-zA-Z0-9]+')
NOTE_POINTER = re.compile(r'(?i)(?:nostr:)?(?:note|nevent|naddr)1[a-z0-9]+|nostr:[0-9a-f]{64}')
ID = re.compile(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    # JSON strings may contain literal Unicode line separators; only LF frames JSONL.
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]


def count_tokens(source, tokenizer, output):
    """Use the worker's complete original-post tokenization, never truncate."""
    if output.exists():
        raise ValueError('token receipt already exists')
    from transformers import AutoTokenizer
    tokenizer = tokenizer.resolve()
    tok = AutoTokenizer.from_pretrained(str(tokenizer), local_files_only=True, use_fast=True)
    records = [dict(note_id=r['note_id'], text_sha256=text_sha(r['text']),
                    tokens=len(tok(r['text'], add_special_tokens=True, truncation=False,
                                   padding=False)['input_ids'])) for r in rows(source)]
    receipt = dict(schema_version=1, source_sha256=sha(source), maximum_tokens=512,
                   tokenizer_files={str(p): sha(p) for p in sorted(tokenizer.iterdir())
                                    if p.is_file() and p.suffix in {'.json', '.model'}},
                   add_special_tokens=True, truncation=False, padding=False, records=records)
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, receipt)
    return dict(records=len(records), over_limit=sum(r['tokens'] > 512 for r in records),
                receipt=str(output), source_sha256=receipt['source_sha256'])


def ordinals(value):
    selected = set()
    for part in value.split(','):
        if not part:
            continue
        bounds = part.split('-')
        start, end = (int(bounds[0]), int(bounds[-1]))
        if len(bounds) > 2 or start < 1 or end < start:
            raise ValueError('invalid review ordinal range')
        selected.update(range(start, end + 1))
    return selected


def review(source, output, accept, reject, forms, reason):
    """Record explicit agent English/form decisions, bound to original source text."""
    candidates = rows(source)
    yes, no = ordinals(accept), ordinals(reject)
    if yes & no or not yes | no or max(yes | no) > len(candidates) or not reason.strip():
        raise ValueError('invalid or overlapping review selection')
    assignments = defaultdict(list)
    for specification in forms:
        code, indices = specification.split(':', 1)
        if code not in FORMS:
            raise ValueError('unknown writing form')
        for i in ordinals(indices):
            if i not in yes:
                raise ValueError('form assignment must belong to an accepted post')
            assignments[i].append(code)
    if any(not assignments[i] for i in yes):
        raise ValueError('accepted posts require at least one reviewed writing form')
    existing = {r['note_id'] for r in rows(output)} if output.exists() else set()
    records = []
    digest = sha(source)
    for i in sorted(yes | no):
        r = candidates[i - 1]
        if r['note_id'] in existing:
            raise ValueError('post already has a saved review')
        records.append(dict(note_id=r['note_id'], pubkey=r['pubkey'], text_sha256=text_sha(r['text']),
                            source_sha256=digest, include_in_pool=i in yes,
                            forms=assignments[i], reason=reason, reviewer='agent'))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('a') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return dict(saved_reviews=len(records), accepted=len(yes), rejected=len(no), output=str(output))


def body(text):
    return re.sub(r'\s+', ' ', re.sub(r'\d+', '_', POINTER.sub('_', text).casefold())).strip()


def shingles(text):
    words = re.findall(r'\w+', POINTER.sub(' ', text).casefold())
    return set(tuple(words[i:i+4]) for i in range(len(words)-3)), len(words)


def development_ids(paths):
    ids, hashes, authors, templates = set(), {}, set(), set()
    for value in paths:
        path = Path(value).resolve()
        hashes[str(path)] = sha(path)
        # Streaming with overlap also covers large native prepared-input files.
        overlap = ''
        with path.open() as f:
            for block in iter(lambda: f.read(1024 * 1024), ''):
                text = overlap + block
                ids.update(ID.findall(text))
                overlap = text[-65:]
        pending = [read(path)]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                for key in ('pubkey', 'author_pubkey'):
                    if isinstance(value.get(key), str) and ID.fullmatch(value[key]):
                        authors.add(value[key])
                if value.get('note_id') and isinstance(value.get('text', value.get('content')), str):
                    templates.add(body(value.get('text', value.get('content'))))
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
    return ids, hashes, authors, templates


def choose_groups(groups, size, seed):
    """Exact-size subset of complete author groups; deterministic hash tie order."""
    ordered = sorted(groups, key=lambda a: text_sha(seed + '/' + a))
    reachable = {0: ()}
    for author in ordered:
        count = len(groups[author])
        for total, chosen in sorted(list(reachable.items()), reverse=True):
            new = total + count
            if new <= size and new not in reachable:
                reachable[new] = chosen + (author,)
        if size in reachable:
            return set(reachable[size])
    raise ValueError('cannot make exact split counts with complete author groups')


def sample_inputs(cfg):
    """Validate shared source/token bindings before either selection mode."""
    source = Path(cfg['candidates']).resolve()
    candidates = rows(source)
    digest = sha(source)
    token_path = Path(cfg['token_counts']).resolve()
    receipt = read(token_path)
    if receipt['source_sha256'] != digest or receipt['maximum_tokens'] != 512:
        raise ValueError('token receipt source/limit differs')
    token_records = {r['note_id']: r for r in receipt['records']}
    if len(token_records) != len(candidates) or len({r['note_id'] for r in candidates}) != len(candidates):
        raise ValueError('duplicate/missing source or token records')
    if candidates != sorted(candidates, key=lambda r: (r['selection_order_sha256'], r['note_id'])):
        raise ValueError('candidate hash order differs')
    return source, candidates, digest, token_path, token_records


def freeze_automatic(cfg, spec, destination):
    """Take the first mechanically eligible posts, without review or balancing."""
    if set(cfg) != {'selection_mode', 'candidates', 'token_counts', 'candidate_manifest', 'seed', 'count'}:
        raise ValueError('automatic sample requires only source, token, seed and count settings')
    if type(cfg['count']) is not int or cfg['count'] < 1 or not isinstance(cfg['seed'], str) or not cfg['seed']:
        raise ValueError('automatic sample requires a positive count and nonempty seed')
    source, candidates, digest, token_path, token_records = sample_inputs(cfg)
    export_path = Path(cfg['candidate_manifest']).resolve()
    exported = read(export_path)
    if exported['candidates_sha256'] != digest or exported['canonical_event_ids_verified'] is not True:
        raise ValueError('candidate export receipt differs')
    if exported['config']['selection_domain'] != cfg['seed']:
        raise ValueError('candidate selection domain differs from seed')
    selected, rejected = [], Counter()
    for ordinal, row in enumerate(candidates, 1):
        rank = hashlib.sha256(cfg['seed'].encode() + bytes.fromhex(row['note_id'])).hexdigest()
        if rank != row['selection_order_sha256']:
            raise ValueError('candidate hash rank differs from seed')
        tokens = token_records[row['note_id']]
        if tokens['text_sha256'] != text_sha(row['text']):
            raise ValueError('token receipt text differs')
        if row['canonical_event_id_verified'] is not True:
            raise ValueError('unverified source event')
        if not row['root_non_quote']:
            reason = 'reply_or_quote'
        elif not row['text'].strip():
            reason = 'empty_text'
        elif tokens['tokens'] > 512:
            reason = 'over_512_tokens'
        elif row['language_decision'] not in {'keep_english', 'keep_language_neutral'}:
            reason = 'source_language_filter'
        else:
            reason = None
        if reason:
            rejected[reason] += 1
            continue
        selected.append(dict(row, tokens=tokens['tokens']))
        if len(selected) == cfg['count']:
            break
    if len(selected) != cfg['count']:
        raise ValueError('automatic sample has insufficient eligible candidates')
    summary = dict(selected=len(selected), required=cfg['count'], review_needed=0,
        exclusions=dict(rejected), examined_candidates=ordinal, source_sha256=digest, inference_calls=0)
    notes = [dict(note_id=r['note_id'], pubkey=r['pubkey'], text=r['text'], origin=dict(
        pubkey=r['pubkey'], candidate_source=str(source), candidate_source_sha256=digest,
        selection_order_sha256=r['selection_order_sha256'], text_sha256=text_sha(r['text']),
        tokens=r['tokens'])) for r in selected]
    manifest = dict(schema_version=1, **summary, selection_mode='automatic', seed=cfg['seed'],
        selection='first eligible original posts in domain-separated event-ID hash order; no manual reviews or topic/author quotas',
        eligibility=dict(root_non_quote=True, nonempty_text=True, maximum_tokens=512,
            language_decisions=['keep_english', 'keep_language_neutral']),
        authors=len({r['pubkey'] for r in selected}),
        candidate_export=exported,
        protected_sources={str(source): digest, str(token_path): sha(token_path),
            str(export_path): sha(export_path), str(spec.resolve()): sha(spec)})
    publish_sample(destination, {'notes.json': dict(schema_version=1, notes=notes),
        'manifest.json': manifest, 'original-events.jsonl': [r['event'] for r in selected]})
    return dict(**summary, destination=str(destination))


def freeze(spec, destination, preview=False):
    if destination.exists():
        raise ValueError('sample output already exists')
    cfg = read(spec)
    mode = cfg.get('selection_mode', 'reviewed')
    if mode == 'automatic':
        if preview:
            raise ValueError('automatic sampling has no manual review preview')
        return freeze_automatic(cfg, spec, destination)
    if mode != 'reviewed':
        raise ValueError('unknown post sample selection mode')
    source, candidates, digest, token_path, token_records = sample_inputs(cfg)
    prior_path = Path(cfg['prior_review']).resolve()
    prior = {r['note_id']: r for r in read(prior_path)['notes']
             if r.get('source', {}).get('origin') == 'frozen-1000'}
    review_path = Path(cfg['reviews']).resolve()
    new_reviews = rows(review_path) if review_path.exists() else []
    reviews = {r['note_id']: r for r in new_reviews}
    if len(reviews) != len(new_reviews):
        raise ValueError('duplicate saved post reviews')
    exposed, exposure_hashes, exposed_authors, exposed_templates = development_ids(cfg['development_sources'])
    exposed_authors.update(r['pubkey'] for r in candidates if r['note_id'] in exposed)
    exposed_templates.update(body(r['text']) for r in candidates if r['note_id'] in exposed)
    sizes = cfg['splits']
    if set(sizes) != {'train', 'validation', 'test'} or any(type(n) is not int or n < 1 for n in sizes.values()):
        raise ValueError('invalid three-way split sizes')
    target = sum(sizes.values())
    selected, rejected, seen_bodies, indexed, pending = [], Counter(), set(), defaultdict(set), []
    signatures = []
    for ordinal, r in enumerate(candidates, 1):
        tokens = token_records[r['note_id']]
        if tokens['text_sha256'] != text_sha(r['text']):
            raise ValueError('token receipt text differs')
        reason = None
        if not r['canonical_event_id_verified']:
            raise ValueError('unverified source event')
        if not r['root_non_quote']:
            reason = 'reply_or_quote'
        elif NOTE_POINTER.search(r['text']):
            reason = 'inline_note_reference'
        elif tokens['tokens'] > 512:
            reason = 'over_512_tokens'
        elif r['language_decision'] not in {'keep_english', 'keep_language_neutral'}:
            reason = 'source_language_filter'
        elif not re.search(r'[A-Za-z]', POINTER.sub('', r['text'])):
            reason = 'no_readable_english_text'
        reviewed = reviews.get(r['note_id']) or prior.get(r['note_id'])
        if reviewed:
            if reviewed['pubkey'] != r['pubkey'] or (reviewed.get('text_sha256', text_sha(reviewed.get('text', ''))) != text_sha(r['text'])):
                raise ValueError('saved English review text/author differs')
            if 'source_sha256' in reviewed and reviewed['source_sha256'] != digest:
                raise ValueError('saved English review source differs')
            if not reviewed['include_in_pool']:
                reason = reason or 'english_review_excluded'
            elif not set(reviewed['forms']) <= FORMS or not reviewed['forms']:
                raise ValueError('invalid reviewed writing forms')
        signature, length = shingles(r['text'])
        template = body(r['text'])
        if not reason and template in seen_bodies:
            reason = 'repeated_template'
        if not reason and signature:
            comparisons = set().union(*(indexed[s] for s in signature))
            for i in comparisons:
                other, other_length = signatures[i]
                if min(length, other_length) / max(length, other_length) >= .7 and len(signature & other) / len(signature | other) >= .8:
                    reason = 'near_copy'
                    break
        if reason:
            rejected[reason] += 1
            continue
        if not reviewed:
            pending.append(dict(ordinal=ordinal, **r, tokens=tokens['tokens']))
        seen_bodies.add(template)
        for s in signature:
            indexed[s].add(len(signatures))
        signatures.append((signature, length))
        selected.append(dict(**r, forms=reviewed['forms'] if reviewed else [], tokens=tokens['tokens']))
        if len(selected) == target:
            break
    summary = dict(selected=len(selected), required=target, review_needed=len(pending), exclusions=dict(rejected),
                   examined_candidates=ordinal, source_sha256=digest, inference_calls=0)
    if not preview and (pending or len(selected) != target):
        raise ValueError(f'sample incomplete: {summary}; preview and review remaining original posts first')
    protected = {str(source): digest, str(token_path): sha(token_path), str(prior_path): sha(prior_path),
                 str(spec.resolve()): sha(spec), **exposure_hashes}
    if review_path.exists():
        protected[str(review_path)] = sha(review_path)
    if preview:
        files = {'review-needed.jsonl': pending, 'summary.json': summary}
    else:
        groups = defaultdict(list)
        for r in selected:
            groups[r['pubkey']].append(r)
        forced = {a for a, group in groups.items() if a in exposed_authors or
                  any(r['note_id'] in exposed or body(r['text']) in exposed_templates for r in group)}
        available = {a: group for a, group in groups.items() if a not in forced}
        test = choose_groups(available, sizes['test'], cfg['seed'] + '/test')
        validation = choose_groups({a: g for a, g in available.items() if a not in test}, sizes['validation'], cfg['seed'] + '/validation')
        notes = [dict(note_id=r['note_id'], pubkey=r['pubkey'], text=r['text'], origin=dict(
            pubkey=r['pubkey'], split='test' if r['pubkey'] in test else 'validation' if r['pubkey'] in validation else 'train',
            candidate_source=str(source), candidate_source_sha256=digest, selection_order_sha256=r['selection_order_sha256'],
            text_sha256=text_sha(r['text']), forms=r['forms'], tokens=r['tokens'],
            prompt_development_note=r['note_id'] in exposed)) for r in selected]
        split_counts = dict(Counter(n['origin']['split'] for n in notes))
        if split_counts != sizes:
            raise ValueError('split counts differ')
        manifest = dict(schema_version=1, **summary, split_counts=split_counts, seed=cfg['seed'],
            selection='first eligible original posts in corpus hash order; no writing-form/topic quotas',
            protected_sources=protected, authors=len(groups), development_authors_training=len(forced),
            writing_forms=dict(Counter(f for r in selected for f in r['forms'])),
            writing_forms_by_split={s: dict(Counter(f for n in notes if n['origin']['split'] == s for f in n['origin']['forms'])) for s in sizes},
            near_copy_policy=dict(word_shingles=4, minimum_jaccard=.8, minimum_length_ratio=.7),
            development_exposure_policy='prior input IDs, known authors and repeated text templates excluded from holdouts; saved sources hash-bound')
        files = {'notes.json': dict(schema_version=1, notes=notes), 'manifest.json': manifest,
                 'original-events.jsonl': [r['event'] for r in selected if 'event' in r]}
        for s in sizes:
            files[s + '.json'] = dict(schema_version=1, sources=[dict(path=str(destination.resolve()/'notes.json'),
                format='posts', select=[n['note_id'] for n in notes if n['origin']['split']==s])])
    publish_sample(destination, files, include_manifest=not preview)
    return dict(**summary, destination=str(destination))


def publish_sample(destination, files, include_manifest=True):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.post-sample-', dir=destination.parent) as temporary:
        stage = Path(temporary)
        for name, value in files.items():
            if name.endswith('.jsonl'):
                (stage/name).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in value))
            else:
                write(stage/name, value)
        if include_manifest:
            files['manifest.json']['files'] = {p.name: sha(p) for p in stage.iterdir() if p.name != 'manifest.json'}
            write(stage/'manifest.json', files['manifest.json'])
        stage.rename(destination)
