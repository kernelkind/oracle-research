"""Compare pair recurrence with no order, source order, and token adjacency.

Patterns are not certified subjects. This standalone diagnostic neither changes
the input evidence nor builds or filters a browsing hierarchy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from subject_description_construction import text_features


def compare_patterns(inputs):
    tokens, spans = [], []
    postings = {name: {} for name in ('unordered', 'ordered', 'adjacent')}
    for row, record in enumerate(inputs):
        if record['row'] != row or not record['note']:
            raise ValueError('ordered input records and note owners required')
        text = record['subject'].casefold()
        matches = [m for m in re.finditer(r'[^\W_]+|[^\w\s]', text)
                   if m.group().isalnum() or
                   unicodedata.category(m.group()[0]).startswith('S')]
        words = [m.group() for m in matches]
        if set(words) != text_features([record['subject']]):
            raise ValueError('token sequence differs from CAP03 feature set')
        tokens.append(words)
        spans.append([[m.start(), m.end()] for m in matches])
        for i, a in enumerate(words):
            for j in range(i + 1, len(words)):
                b = words[j]
                if a == b:
                    continue
                pairs = [('unordered', tuple(sorted((a, b)))), ('ordered', (a, b))]
                if j == i + 1:
                    pairs.append(('adjacent', (a, b)))
                for family, pair in pairs:
                    postings[family].setdefault(pair, {}).setdefault(row, []).append([i, j])

    for pair, rows in postings['ordered'].items():
        if not set(rows) <= set(postings['unordered'][tuple(sorted(pair))]):
            raise ValueError('ordered support not contained in unordered support')
    for pair, rows in postings['adjacent'].items():
        if not set(rows) <= set(postings['ordered'][pair]):
            raise ValueError('adjacent support not contained in ordered support')

    result = dict(tokens=tokens, casefolded_character_spans=spans)
    for family, patterns in postings.items():
        result[family] = []
        for pair, rows in sorted(patterns.items()):
            notes = sorted({inputs[row]['note'] for row in rows})
            if len(notes) < 2:
                continue
            digest = hashlib.sha256(json.dumps([family, pair], ensure_ascii=False).encode()).hexdigest()
            result[family].append(dict(id='P' + digest[:12], tokens=list(pair),
                                       rows=sorted(rows), notes=notes,
                                       positions=[[r, rows[r]] for r in sorted(rows)]))
    identifiers = [p['id'] for name in postings for p in result[name]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('pattern ID collision')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='frozen CAP03 result.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier results')
    raw = args.input.read_bytes()
    inputs = json.loads(raw)['inputs']
    result = compare_patterns(inputs)
    files = [Path(__file__).with_name(name) for name in (
        'subject_pattern_candidates.py', 'subject_description_construction.py',
        'shared_mask_descriptions.py', 'mask_description_hierarchy.py',
        'select_mask_distinctions.py', 'select_note_categories.py')]
    result.update(run_id='CAP04', inputs=inputs, minimum_distinct_notes=2,
                  input_source=dict(path=str(args.input.resolve()), sha256=hashlib.sha256(raw).hexdigest()),
                  code_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  unicode_version=unicodedata.unidata_version,
                  limitations=['patterns are not certified meanings',
                               'positions index the case-folded token sequence, not original mask ranges',
                               'punctuation is ignored as in CAP03; adjacency is not a syntactic boundary',
                               'two distinct tokens only; not an exhaustive semantic candidate family',
                               'no browser or baseline changed'])
    args.output.mkdir(parents=True)
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    source = args.output / 'source'
    source.mkdir()
    for path in files:
        (source / path.name).write_bytes(path.read_bytes())
    print(json.dumps({name: len(result[name]) for name in ('unordered', 'ordered', 'adjacent')}))


if __name__ == '__main__':
    main()
