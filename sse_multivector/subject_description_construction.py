"""Controlled CAP02 construction from masks versus their saved subject text.

Generated subjects are experimental representations, never source evidence.
Alternative subjects remain separate records with explicit source provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import unicodedata

from mask_description_hierarchy import features_from_masks, description_relations
from select_mask_distinctions import mask_words
from shared_mask_descriptions import shared_descriptions, shared_descriptions_from_features


def text_features(fragments):
    words = mask_words(fragments)
    words.update(c for f in fragments for c in f if unicodedata.category(c).startswith('S'))
    return frozenset(words)


def compare_representations(evidence):
    original_features, _ = features_from_masks(evidence, keep_symbols=True)
    inputs, mask_features, subject_features, notes = [], [], [], []
    for canonical_row, record in enumerate(evidence):
        alternatives = {}
        for alias in record['aliases']:
            subject = alias['subject']
            if not isinstance(subject, str) or not subject.strip():
                raise ValueError('every alias must have a nonempty saved subject')
            alternatives.setdefault(subject, []).append(alias)
        for subject, aliases in sorted(alternatives.items()):
            first = aliases[0]
            notes.append(first['note_short_id'])
            mask_features.append(original_features[canonical_row])
            subject_features.append(text_features([subject]))
            inputs.append(dict(row=len(inputs), canonical_row=canonical_row,
                               note=first['note_short_id'], subject=subject,
                               alias_ids=[a['short_id'] for a in aliases],
                               fragments=first['fragments'], text=first['text']))

    control = shared_descriptions_from_features(mask_features, notes)
    changed = shared_descriptions_from_features(subject_features, notes)
    mapped = []
    for descriptor in control['descriptions']:
        restored = dict(descriptor)
        for key in ('rows', 'seed_rows'):
            restored[key] = sorted({inputs[r]['canonical_row'] for r in descriptor[key]})
        mapped.append(restored)
    baseline = shared_descriptions(evidence)
    if mapped != baseline['descriptions']:
        raise ValueError('mask control does not reproduce canonical CAP02 memberships')
    for output in (control, changed):
        output['relations'] = description_relations(output['descriptions'])['descriptor_extension']
    return dict(inputs=inputs, mask=control, subjects=changed, control_reproduced=True,
                control_canonical_descriptions=mapped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve prior results')
    result = compare_representations(json.loads(args.evidence.read_bytes()))
    baseline = json.loads(args.baseline.read_bytes())
    if (result['control_canonical_descriptions'] != baseline['descriptions'] or
            result['mask']['relations'] != baseline['relations']):
        parser.error('control differs from frozen CAP02')
    code = [Path(__file__).with_name(name) for name in (
        'subject_description_construction.py', 'shared_mask_descriptions.py',
        'mask_description_hierarchy.py', 'select_mask_distinctions.py', 'select_note_categories.py')]
    sources = [args.evidence, args.baseline, *code]
    result.update(run_id='CAP03', sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sources},
                  unicode_version=unicodedata.unidata_version,
                  limitations=['saved subjects are not certified mask-grounded meanings',
                               'words and symbols do not encode full phrase relationships',
                               'bounded closure candidates are not a complete lattice',
                               'no browser or original evidence is modified'])
    args.output.mkdir(parents=True)
    (args.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    source_dir = args.output / 'source'
    source_dir.mkdir()
    for path in code:
        (source_dir / path.name).write_bytes(path.read_bytes())
    print(json.dumps({name: dict(candidates=len(result[name]['descriptions']),
                                edges=len(result[name]['relations']['immediate_edges']),
                                roots=len(result[name]['relations']['roots']))
                      for name in ('mask', 'subjects')}))


if __name__ == '__main__':
    main()
