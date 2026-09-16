#!/usr/bin/env python3
"""Replay the frozen, manually reviewed coverage selection. No model or network calls."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
RELATIVE = 'sse_multivector/frontier-model-comparison-v1/english-selection-v2'
SEED = 'frontier-english-form-coverage-v2/2026-09-16/'
TARGET = 60
POOL_HASH = '1430bd9e2983b364c0703be615e6354782fa83134960409331317a0d48cb8a6f'
PRIOR_HASH = '4f635af0456853760b8b8bc391aaca9ddd2289f540106abf8e328c6651d17613'
POINTER = re.compile(r'https?://\S+|(?:nostr:)?(?:npub|nprofile|note|nevent|naddr|nsec)1[a-zA-Z0-9]+')


def read_frozen(path, digest):
    data = path.read_bytes()
    if sha256(data).hexdigest() != digest:
        raise ValueError(f'Frozen input changed: {path.name}')
    return json.loads(data)


def rank(channel, value):
    return sha256((SEED + channel + '/' + value).encode()).hexdigest()


def template(text):
    value = re.sub(r'\d+', '_', POINTER.sub('_', text).casefold())
    return re.sub(r'\s+', ' ', value).strip()


def artifacts():
    pool = read_frozen(HERE / 'reviewed-pool.json', POOL_HASH)
    prior = set(read_frozen(HERE.parent / 'english-selection-v1/prior-prompt-note-ids.json', PRIOR_HASH)['note_ids'])
    originals = pool['notes']
    definitions = pool['definitions']
    if len({n['note_id'] for n in originals}) != len(originals):
        raise ValueError('Duplicate source note ID')
    rows, families = [], defaultdict(list)
    for index, note in enumerate(originals, 1):
        if not set(note['forms']) <= definitions.keys():
            raise ValueError(f'Unknown category: {note["id"]}')
        excluded = []
        if not note['include_in_pool']:
            excluded.append('not_retained_by_input_review')
        if note['note_id'] in prior:
            excluded.append('known_prompt_development_note')
        if not excluded and not note['forms']:
            raise ValueError(f'Reviewed note has no form: {note["id"]}')
        body = template(note['text'])
        row = dict(id=note['id'], note_id=note['note_id'], pubkey=note['pubkey'],
                   source_index=index, forms=note['forms'], exclude_reasons=excluded,
                   template_key=sha256(body.encode()).hexdigest(), selected_by=[], selected=False)
        rows.append(row)
        if not excluded:
            families[body].append(row)
    duplicate_groups = []
    for family in families.values():
        family.sort(key=lambda r: rank('template-representative', r['note_id']))
        for row in family:
            row['template_representative'] = family[0]['id']
        for row in family[1:]:
            row['exclude_reasons'].append('repeated_template')
        if len(family) > 1:
            duplicate_groups.append([r['id'] for r in family])
    eligible = [r for r in rows if not r['exclude_reasons']]
    draws, categories = {}, []
    for code, definition in definitions.items():
        candidates = [r for r in eligible if code in r['forms']]
        if len(candidates) < TARGET:
            raise ValueError(f'{code}: {len(candidates)} distinct reviewed notes; need {TARGET}')
        # Within each category, exhaust first notes from authors before their second, etc.
        authors = defaultdict(list)
        for row in candidates:
            authors[row['pubkey']].append(row)
        ordered = []
        for group in authors.values():
            group.sort(key=lambda r: rank(code, r['note_id']))
            ordered.extend((position, rank(code, r['note_id']), r) for position, r in enumerate(group))
        chosen = [r for _, _, r in sorted(ordered, key=lambda x: x[:2])[:TARGET]]
        draws[code] = [r['note_id'] for r in chosen]
        for row in chosen:
            row['selected_by'].append(code)
            row['selected'] = True
        categories.append(dict(id=code, description=definition, target_notes=TARGET,
                               eligible_notes=len(candidates), eligible_authors=len(authors),
                               draw_authors=len({r['pubkey'] for r in chosen}),
                               largest_author_draw_count=max(Counter(r['pubkey'] for r in chosen).values())))
    selected = [r for r in rows if r['selected']]
    notes = []
    for row in selected:
        original = originals[row['source_index'] - 1]
        notes.append(dict(id=row['id'], title='Original English post', note_id=row['note_id'],
                          text=original['text'], why='; '.join(definitions[c] for c in row['forms']),
                          source=dict(path=RELATIVE + '/reviewed-pool.json', index=row['source_index'])))
    by_id = {r['id']: r for r in selected}
    # A small viewing sample, not an accuracy estimate: cover forms before adding variety.
    covered, sample = set(), []
    available = sorted(notes, key=lambda n: rank('sampler', n['note_id']))
    while available and len(sample) < 12:
        note = max(available, key=lambda n: len(set(by_id[n['id']]['forms']) - covered))
        sample.append(note)
        covered.update(by_id[note['id']]['forms'])
        available.remove(note)
    for category in categories:
        actual = [r for r in selected if category['id'] in r['forms']]
        category['selected_notes'] = len(actual)
        category['selected_authors'] = len({r['pubkey'] for r in actual})
    words = [len(POINTER.sub('', n['text']).split()) for n in notes]
    purpose = ('Input review only. Original posts are unchanged. Coverage classifications are reviewer notes, '
               'not model instructions or expected answers. No comparison model calls have been made.')
    report = dict(schema_version=1, model_calls_made=False, reviewed_notes=len(originals),
                  reviewed_original_notes=sum(n['id'].startswith('E') for n in originals),
                  reviewed_additional_notes=sum(not n['id'].startswith('E') for n in originals),
                  eligible_distinct_templates=len(eligible), selected_notes=len(selected),
                  selected_authors=len({r['pubkey'] for r in selected}), viewer_notes=len(sample),
                  selected_sources=dict(Counter(originals[r['source_index']-1]['source']['origin'] for r in selected)),
                  categories=categories, draws=draws,
                  selected_length_bands=dict(Counter('0–10' if w <= 10 else '11–30' if w <= 30 else '31–100' if w <= 100 else '>100' for w in words)),
                  exclusions=dict(Counter(x for r in rows for x in r['exclude_reasons'])),
                  selection=dict(seed=SEED, target_per_category=TARGET,
                                 method='Choose 60 per each of 16 overlapping forms, spreading each draw across authors before reusing authors. Fixed hash orders break ties. Keep the union; no general/random extra quota.',
                                 template_rule='Keep one fixed-hash representative of full texts equal after pointer, number, case and whitespace normalization. Additional obvious near-template repetitions were rejected during review.',
                                 duplicate_groups=duplicate_groups),
                  input_hashes={'reviewed-pool.json': POOL_HASH, '../english-selection-v1/prior-prompt-note-ids.json': PRIOR_HASH},
                  limits=[
                      'The category counts overlap; a note is processed once. Sixty notes per category does not guarantee sixty examples of every subtype or combination.',
                      'This is deliberately balanced coverage screening, not a representative sample for corpus-wide accuracy or failure prevalence. No population selection probabilities are claimed.',
                      'Category and English judgments are manual and fallible. Factual-description labels do not certify the truth of assertions.',
                      'Template and author diversity reduce obvious repetition but do not prove statistical independence.',
                      'Known-prompt exclusions do not prove absence from all earlier experiments or model pretraining.',
                      'Sources are top-level corpus notes, not replies. Some posts depend on unseen images, quoted material or other context.',
                      'ASv6.23 and MPv3.5 remain unchanged. Subject and mask comparisons remain separate; use the same fixed subjects for mask comparison.',
                  ])
    return {'audit.json': dict(schema_version=1, notes=rows),
            'selection.json': dict(schema_version=1, title='English model-comparison inputs — coverage v2', purpose=purpose, notes=notes),
            'sampler.json': dict(schema_version=1, title='English input sample — 12 notes', purpose=purpose, notes=sample),
            'coverage.json': report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true', help='Create artifacts once; never overwrite frozen files')
    args = parser.parse_args()
    generated = artifacts()
    if args.check:
        for name, value in generated.items():
            if json.loads((HERE / name).read_text()) != value:
                raise ValueError(f'Saved artifact differs: {name}')
        print(f'Verified {generated["coverage.json"]["selected_notes"]} notes; 16 categories cover at least 60 notes each. No model calls.')
    elif args.write:
        if any((HERE / name).exists() for name in generated):
            raise FileExistsError('Refusing to overwrite frozen artifacts')
        for name, value in generated.items():
            with (HERE / name).open('x') as output:
                output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        print('Created frozen artifacts; no model calls.')
    else:
        print(json.dumps(generated, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
