"""Bounded shared-attribute proposals; not a certified semantic hierarchy.

Add attribute-concept closures to unchanged complete-mask candidates. Output is
JSON on stdout; frozen source evidence and browser artifacts are never written.
"""
import argparse
import hashlib
import json
from pathlib import Path

from mask_candidate_coverage import inventory
from mask_description_hierarchy import descriptions_from_masks, description_relations


def shared_descriptions(evidence):
    baseline = descriptions_from_masks(evidence, keep_symbols=True)
    recurring = inventory(evidence)
    postings = {d['feature']: set(d['rows']) for d in recurring}
    descriptions = {tuple(d['features']): d for d in baseline}
    seeds = {}
    for feature in recurring:
        rows = postings[feature['feature']]
        # Every feature shared by >=2-note support must itself be recurrent.
        closure = tuple(sorted(w for w, support in postings.items() if rows <= support))
        if set.intersection(*(postings[w] for w in closure)) != rows:
            raise ValueError('closure changed support')
        if closure not in descriptions:
            identifier = 'D' + hashlib.sha256(json.dumps(list(closure), ensure_ascii=False).encode()).hexdigest()[:12]
            descriptions[closure] = dict(id=identifier, features=list(closure), seed_rows=[],
                                         rows=sorted(rows), notes=feature['notes'])
        seeds.setdefault(descriptions[closure]['id'], []).append(feature['feature'])
    ordered = [descriptions[key] for key in sorted(descriptions)]
    if len({d['id'] for d in ordered}) != len(ordered):
        raise ValueError('descriptor ID collision')
    return dict(descriptions=ordered, recurring_features=len(recurring),
                shared_seeds={k: sorted(v) for k, v in sorted(seeds.items())},
                baseline_ids=sorted(d['id'] for d in baseline))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_bytes())
    baseline = json.loads(args.baseline.read_bytes())
    if descriptions_from_masks(evidence, keep_symbols=True) != baseline:
        parser.error('recomputed MDH02 candidates differ from saved baseline')
    result = shared_descriptions(evidence)
    paths = (args.evidence, args.baseline, Path(__file__), *(Path(__file__).with_name(name) for name in
             ('mask_candidate_coverage.py', 'mask_description_hierarchy.py',
              'select_mask_distinctions.py', 'select_note_categories.py')))
    result.update(run_id='CAP02', baseline_reproduced=True, canonical_masks=len(evidence),
                  sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  relations=description_relations(result['descriptions'])['descriptor_extension'],
                  limitations=['descriptors and inclusion are not certified subject meanings',
                               'single-feature closures omit some recurring combinations',
                               'literal matching does not establish exhaustive subject membership',
                               'no browser artifact changed'])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
