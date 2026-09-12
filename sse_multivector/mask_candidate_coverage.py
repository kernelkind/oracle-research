"""Audit recurring features excluded by MDH02's whole-mask candidate rule.

Outputs evidence inventory, not categories, memberships, or semantic judgments.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from mask_description_hierarchy import descriptions_from_masks
from select_mask_distinctions import mask_words


def inventory(evidence):
    # Reuse the production path for alias validation and actual candidate status.
    baseline = descriptions_from_masks(evidence, keep_symbols=True)
    singletons = {d['features'][0] for d in baseline if len(d['features']) == 1}
    postings, whole_masks, notes = {}, {}, {}
    for record in evidence:
        row = record['row']
        alias = record['aliases'][0]
        features = mask_words(alias['fragments'])
        features.update(c for f in alias['fragments'] for c in f
                        if unicodedata.category(c).startswith('S'))
        notes[row] = alias['note_short_id']
        for feature in features:
            postings.setdefault(feature, []).append(row)
        if len(features) == 1:
            whole_masks.setdefault(next(iter(features)), []).append(row)
    result = []
    for feature, rows in postings.items():
        source_notes = sorted({notes[row] for row in rows})
        if len(source_notes) >= 2:
            result.append(dict(feature=feature, rows=rows, notes=source_notes,
                               whole_mask_rows=whole_masks.get(feature, []),
                               mdh02_candidate=feature in singletons))
    return sorted(result, key=lambda d: (-len(d['notes']), d['feature']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_bytes())
    baseline = json.loads(args.baseline.read_bytes())
    if descriptions_from_masks(evidence, keep_symbols=True) != baseline:
        parser.error('recomputed MDH02 candidates differ from saved baseline')
    records = inventory(evidence)
    sources = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in (args.evidence, args.baseline, Path(__file__),
                            Path(__file__).with_name('mask_description_hierarchy.py'),
                            Path(__file__).with_name('select_mask_distinctions.py'),
                            Path(__file__).with_name('select_note_categories.py'))}
    print(json.dumps(dict(run_id='CAP01', baseline_reproduced=True,
                          canonical_masks=len(evidence), mdh02_candidates=len(baseline),
                          recurring_features=len(records),
                          excluded_features=sum(not d['mdh02_candidate'] for d in records),
                          sources=sources, features=records), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
