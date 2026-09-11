"""Diagnostic membership recovery from identical masked-word evidence.

Literal containment proposes membership; it does not establish semantic fit.
No hierarchy, mask, vector, or original membership is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from select_mask_distinctions import describe_categories, mask_words
from select_note_categories import memberships


def literal_memberships(categories, hierarchy, evidence):
    descriptions = describe_categories(categories, hierarchy, evidence)
    full = memberships(categories)
    words, notes = [], []
    for record in evidence:
        aliases = record['aliases']
        note_ids = {a['note_short_id'] for a in aliases}
        if len(note_ids) != 1:
            raise ValueError('canonical aliases must belong to one note')
        notes.append(next(iter(note_ids)))
        words.append(mask_words(aliases[0]['fragments']))

    seeds = {}
    for node_id, description in descriptions.items():
        rows = description['rows']
        native_notes = {notes[r] for r in rows}
        if native_notes != full[node_id]:
            raise ValueError('native and projected note memberships disagree')
        if len(set(rows)) != len(rows):
            raise ValueError('duplicate native evidence rows')
        common = tuple(description['common_words'])
        if (len(native_notes) >= 2 and common
                and all(tuple(w) == common for w in description['word_sets'])):
            family = seeds.setdefault(common, dict(categories=[], rows=set()))
            family['categories'].append(node_id)
            family['rows'].update(rows)

    # An inverted index makes each query an intersection of postings, rather
    # than computing vector pairs or enumerating every possible word subset.
    postings = {}
    for row, tokens in enumerate(words):
        for word in tokens:
            postings.setdefault(word, set()).add(row)
    result = []
    for common, seed in sorted(seeds.items()):
        matched = set.intersection(*(postings[w] for w in common))
        seed_notes = {notes[r] for r in seed['rows']}
        matched_notes = {notes[r] for r in matched}
        result.append(dict(words=list(common),
                           seed_categories=sorted(seed['categories']),
                           seed_rows=sorted(seed['rows']), seed_notes=sorted(seed_notes),
                           matched_rows=sorted(matched), matched_notes=sorted(matched_notes),
                           added_rows=sorted(matched - seed['rows']),
                           added_notes=sorted(matched_notes - seed_notes)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('categories', type=Path)
    parser.add_argument('--hierarchy', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    sources, loaded = {}, {}
    for key in ('categories', 'hierarchy', 'evidence'):
        path = getattr(args, key)
        raw = path.read_bytes()
        sources[key] = dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest())
        loaded[key] = json.loads(raw)
    families = literal_memberships(**loaded)
    rows = sorted({r for f in families for r in f['matched_rows']})
    snapshots = {}
    for name in ('literal_category_membership.py', 'select_mask_distinctions.py',
                 'select_note_categories.py'):
        snapshots[name] = Path(__file__).with_name(name).read_bytes()
    artifacts = {
        'results.json': families,
        'review.json': [loaded['evidence'][r] for r in rows],
        'config.json': dict(
            run_id=args.run_id, sources=sources,
            code_sha256={k: hashlib.sha256(v).hexdigest() for k, v in snapshots.items()},
            seed_rule='all_masks_have_identical_nonempty_word_sets_at_least_two_notes',
            membership_rule='mask_contains_every_seed_word',
            features='casefolded_unicode_words_no_stopwords',
            limitations=['literal containment is not semantic entailment',
                         'word senses, word order, punctuation, and symbols are not represented',
                         'paraphrases and context outside masks are not matched',
                         'saved hierarchy limits which subjects can supply seeds',
                         'no category or note membership is automatically adopted'],
            family_count=len(families), unique_matched_rows=len(rows),
            unique_matched_notes=len({n for f in families for n in f['matched_notes']})),
    }
    args.output.mkdir(parents=True)
    for filename, value in artifacts.items():
        with (args.output / filename).open('x') as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write('\n')
    source_dir = args.output / 'source'
    source_dir.mkdir()
    for filename, raw in snapshots.items():
        with (source_dir / filename).open('xb') as file:
            file.write(raw)
    print(json.dumps(dict(run_id=args.run_id, families=len(families),
                          unique_matched_rows=len(rows),
                          counts=[dict(words=f['words'], seed_notes=len(f['seed_notes']),
                                       matched_notes=len(f['matched_notes'])) for f in families])))


if __name__ == '__main__':
    main()
