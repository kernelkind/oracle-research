"""Exploratory description/membership relations independent of a saved tree.

Descriptors are complete source-mask feature sets, NOT certified subject names.
No existing browsing artifact or original evidence is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from select_mask_distinctions import mask_words


def descriptions_from_masks(evidence, *, keep_symbols):
    features, notes = [], []
    for row, record in enumerate(evidence):
        if record['row'] != row or not record['aliases']:
            raise ValueError('ordered evidence rows with aliases required')
        alternatives, note_ids = [], set()
        for alias in record['aliases']:
            tokens = mask_words(alias['fragments'])
            if keep_symbols:
                # A deliberately limited control, not grapheme/sense analysis.
                tokens.update(c for f in alias['fragments'] for c in f
                              if unicodedata.category(c).startswith('S'))
            alternatives.append(frozenset(tokens))
            note_ids.add(alias['note_short_id'])
        if len(note_ids) != 1 or any(w != alternatives[0] for w in alternatives):
            raise ValueError('canonical aliases disagree on note or features')
        features.append(alternatives[0])
        notes.append(next(iter(note_ids)))

    postings = {}
    seeds = {}
    for row, tokens in enumerate(features):
        seeds.setdefault(tokens, []).append(row)
        for token in tokens:
            postings.setdefault(token, set()).add(row)
    result = []
    for tokens in sorted(seeds, key=lambda t: sorted(t)):
        if not tokens:
            continue
        rows = set.intersection(*(postings[w] for w in tokens))
        note_ids = {notes[r] for r in rows}
        if len(note_ids) < 2:
            continue
        ordered = sorted(tokens)
        identifier = 'D' + hashlib.sha256(json.dumps(ordered, ensure_ascii=False).encode()).hexdigest()[:12]
        result.append(dict(id=identifier, features=ordered, seed_rows=seeds[tokens],
                           rows=sorted(rows), notes=sorted(note_ids)))
    if len({d['id'] for d in result}) != len(result):
        raise ValueError('descriptor ID collision')
    return result


def description_relations(descriptions):
    nodes = {d['id']: d for d in descriptions}
    if len(nodes) != len(descriptions):
        raise ValueError('duplicate descriptor IDs')
    notes = {i: set(d['notes']) for i, d in nodes.items()}
    features = {i: set(d['features']) for i, d in nodes.items()}
    result = {}
    for rule in ('note_subset', 'descriptor_extension'):
        edges = {(a, b) for a in nodes for b in nodes if notes[b] < notes[a]
                 and (rule == 'note_subset' or features[a] < features[b])}
        # Both relations are strict partial orders. Remove edges already
        # explained by another candidate between the same endpoints.
        immediate = {(a, b) for a, b in edges
                     if not any((a, c) in edges and (c, b) in edges for c in nodes)}
        children = {b for _, b in edges}
        result[rule] = dict(all_edges=[list(e) for e in sorted(edges)],
                            immediate_edges=[list(e) for e in sorted(immediate)],
                            roots=sorted(set(nodes) - children))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--features', choices=['words', 'words-and-symbols'], required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    raw = args.evidence.read_bytes()
    evidence = json.loads(raw)
    descriptions = descriptions_from_masks(evidence, keep_symbols=args.features == 'words-and-symbols')
    relations = description_relations(descriptions)
    rows = sorted({r for d in descriptions for r in d['rows']})
    covered = {n for d in descriptions for n in d['notes']}
    all_notes = {a['note_short_id'] for r in evidence for a in r['aliases']}
    snapshots = {name: Path(__file__).with_name(name).read_bytes() for name in
                 ('mask_description_hierarchy.py', 'select_mask_distinctions.py', 'select_note_categories.py')}
    artifacts = {
        'descriptions.json': descriptions,
        'relations.json': relations,
        'review.json': [evidence[r] for r in rows],
        'config.json': dict(run_id=args.run_id, features=args.features,
                           unicode_version=unicodedata.unidata_version,
                           source=dict(path=str(args.evidence.resolve()), sha256=hashlib.sha256(raw).hexdigest()),
                           code_sha256={k: hashlib.sha256(v).hexdigest() for k, v in snapshots.items()},
                           seed_rule='each_complete_mask_feature_set', minimum_distinct_notes=2,
                           membership_rule='all_descriptor_features_present_in_mask',
                           descriptors=len(descriptions), covered_notes=sorted(covered),
                           uncovered_notes=sorted(all_notes - covered), matched_rows=len(rows),
                           limitations=['feature sets are not verified meanings',
                                        'no order, punctuation or contextual reference resolution',
                                        'symbol control retains Unicode S codepoints, not complete grapheme semantics',
                                        'literal membership misses unstated abstractions and paraphrases',
                                        'note containment is not proof of semantic narrowing',
                                        'no browsing hierarchy is adopted']),
    }
    args.output.mkdir(parents=True)
    for filename, value in artifacts.items():
        with (args.output / filename).open('x') as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write('\n')
    source_dir = args.output / 'source'
    source_dir.mkdir()
    for filename, content in snapshots.items():
        with (source_dir / filename).open('xb') as file:
            file.write(content)
    print(json.dumps(dict(run_id=args.run_id, descriptors=len(descriptions),
                          covered_notes=len(covered), matched_rows=len(rows),
                          edges={r: len(v['immediate_edges']) for r, v in relations.items()})))


if __name__ == '__main__':
    main()
