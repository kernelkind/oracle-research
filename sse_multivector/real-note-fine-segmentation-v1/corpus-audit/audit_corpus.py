#!/usr/bin/env python3
"""Bounded text-only corpus audit; does not read generation or vector artifacts."""

import argparse
import collections
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/dev/shm/oracle-mvp-crec113-granite-r2-v1/formal-v1/sample')
AREAS = {
    'bitcoin': r'\b(?:bitcoin\w*|btc|satoshi\w*|bitaxe|lightning network)\b',
    'nostr': r'\b(?:nostr\w*|damus|primal|amethyst|nsec|npub|nips?[- ]?\d+)\b',
    'ai': r'\b(?:AI|LLMs?|GPT[- ]?\d*|ChatGPT|OpenAI|DeepSeek|artificial intelligence|language models?)\b',
    'food': r'\b(?:food\w*|meals?|eating|eat|bread|steaks?|beef|chicken|eggs?|salads?|cheese|pizza|tea|milk|caffeine|cooking|cooked|cooks|cook|baking|baked|bake|recipe\w*|coffee|espresso|cappuccino|sourdough|barbecue|bbq|breakfast|dinner|lunch|roast\w*|ferment\w*)\b',
    'gardening': r'\b(?:garden\w*|compost\w*|seedling\w*|mulch\w*|greenhouse\w*|harvest\w*|permaculture|raised beds?|planting)\b',
}
EXPOSED_PRIOR_IDS = {
    '84aba98daa2c1ce749395dc7c2249e5072c3c84d73573e37f61e15228fc0ae9d',
    'dcd6544eba8ec98a2a535ac0bd40c7b5e02e2457fa86d46fff2437ca8fa56bdb',
    'e09b8c19f52ae0ed68f05874c91e2982eb9a9684a812a49e67d872cb805caa39',
    '7adcfe1ab26f770b6ff5968fda1d6ef7d5a0fe63a946af714d44178a3470712e',
    'ae8091a7b44d6612f721fd347e0bfeb9a966ca7fe241706adefd08e01f4d1d54',
    '6635a341ab0d45e1b714c8660f4d36ff1141c4f01da8fd8a5ccda1a2b90445e4',
    '7e2e4e93cf8f88476ffe5fe2d4f6c89e6af1efed33de7e18802d6cbcee0f7a13',
    '74694da41f367535d230dec539a9316b3c6536f4f295f61743a7a5b51d97aa99',
    '974dd5c02c7a9ca9b89685e344d8d103abbbab420e0faf22875f9d08e1c0534a',
}


def visible_words(text):
    text = re.sub(r'https?://\S+|(?:nostr:)?(?:npub|nprofile|nevent|note|naddr|nsec)1[a-zA-Z0-9]+', ' ', text)
    text = unicodedata.normalize('NFC', text).casefold()
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", text, re.UNICODE)


def order(note):
    return hashlib.sha256(b'oracle-mvp/real-note-fine-segmentation-v1/corpus-audit\0' + note['note_id'].encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--area', choices=tuple(AREAS))
    parser.add_argument('--min-words', type=int, default=18)
    parser.add_argument('--max-words', type=int, default=300)
    parser.add_argument('--max-candidates', type=int)
    args = parser.parse_args()
    assert 1 <= args.min_words <= args.max_words <= 300
    assert args.max_candidates is None or args.max_candidates > 0
    areas_to_check = {args.area: AREAS[args.area]} if args.area else AREAS
    manifest = json.loads((args.source / 'manifest.json').read_text())
    path = args.source / manifest['sample']['file']
    assert path.stat().st_size == manifest['sample']['bytes'] <= 32 * 1024 * 1024
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == manifest['sample']['sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == manifest['sample']['records'] == 51200
    assert len({row['note_id'] for row in rows}) == len(rows)
    pools = {area: [] for area in areas_to_check}
    matches = collections.Counter()
    eligible = 0
    for rank, row in enumerate(rows, 1):
        words = visible_words(row['content'])
        visible = ' '.join(words)
        areas = [area for area, pattern in areas_to_check.items() if re.search(pattern, visible, re.I)]
        matches.update(areas)
        # These are audit retrieval bounds, not a final semantic accept decision.
        if not (args.min_words <= len(words) <= args.max_words and len(row['content']) <= 2500):
            continue
        if row['note_id'] in EXPOSED_PRIOR_IDS:
            continue
        eligible += 1
        for area in areas:
            pools[area].append({**row, 'source_row': rank, 'visible_word_count': len(words), 'audit_area': area})
    summary = {
        'schema_version': 1,
        'source_path_read': str(path),
        'durable_source_path': 'target/crec-113-formal-v1/sample/sample.jsonl',
        'source_manifest': manifest,
        'source_bytes_sha256_verified': True,
        'all_rows': len(rows),
        'eligible_length_rows': eligible,
        'areas_are_lexical_retrieval_not_semantic_labels': True,
        'all_original_content_preserved': True,
        'ordering': 'sha256(domain + event_id_ascii); domain in source code',
        'retrieval_filters': f'{args.min_words}..{args.max_words} visible words; complete original note <=2500 Unicode codepoints; URLs and NIP-19 refs ignored for lexical screening only',
        'word_floor_is_convenience_screen_not_semantic_requirement': True,
        'max_candidates_per_area': args.max_candidates,
        'copy_control': 'after domain-hash order: exact normalized visible words, or 4-word-shingle Jaccard >=0.8 with word length ratio >=0.7; no maximum author activity upstream',
        'author_control': 'after copy screening, maximum two notes per pubkey in each candidate pool',
        'prior_example_quarantine': sorted(EXPOSED_PRIOR_IDS),
        'not_final_100_selection': True,
        'areas': {},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for area, pool in pools.items():
        retained = []
        exact = set()
        shingles = []
        authors = collections.Counter()
        skips = collections.Counter()
        for row in sorted(pool, key=order):
            words = visible_words(row['content'])
            normalized = ' '.join(words)
            fingerprint = set(zip(words, words[1:], words[2:], words[3:]))
            if normalized in exact:
                skips['exact_copy'] += 1
                continue
            copied = False
            for previous_count, previous in shingles:
                if min(previous_count, len(words)) / max(previous_count, len(words)) < .7:
                    continue
                if len(fingerprint & previous) / len(fingerprint | previous) >= .8:
                    copied = True
                    break
            if copied:
                skips['near_copy'] += 1
                continue
            if authors[row['pubkey']] >= 2:
                skips['author_over_two'] += 1
                continue
            authors[row['pubkey']] += 1
            exact.add(normalized)
            shingles.append((len(words), fingerprint))
            row['candidate_rank'] = len(retained) + 1
            retained.append(row)
            if args.max_candidates is not None and len(retained) == args.max_candidates:
                break
        summary['areas'][area] = {
            'regex': AREAS[area],
            'raw_keyword_hits': matches[area],
            'length_eligible_hits': len(pool),
            'eligible_authors': len({row['pubkey'] for row in pool}),
            'retained_candidates': len(retained),
            'retained_authors': len(authors),
            'skips': dict(skips),
            'max_notes_per_retained_author': max(authors.values(), default=0),
            'candidate_file': f'{area}-candidates.jsonl',
        }
        with (args.output / f'{area}-candidates.jsonl').open('w') as handle:
            for row in retained:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    (args.output / 'audit-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary['areas'], indent=2))


if __name__ == '__main__':
    main()
