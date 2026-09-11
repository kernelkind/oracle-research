"""Audit frozen seed-subject candidates without choosing labels or editing groups."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from group_description_relations import score_pairs
from mask_description_nli import sha256


def prepare_experiment(groups, evidence, fixture):
    by_row = {e['row']: e for e in evidence}
    if len(by_row) != len(evidence) or len({g['id'] for g in groups}) != len(groups):
        raise ValueError('duplicate source row or group')
    if len(groups) < 2:
        raise ValueError('at least two groups required')
    candidates = []
    for group in groups:
        members = {e['row'] for e in group['evidence']}
        if len(members) != len(group['evidence']):
            raise ValueError('duplicate group member')
        for e in group['evidence']:
            if e['row'] not in by_row or e != by_row[e['row']]:
                raise ValueError('group evidence differs from original source')
        variants = {}
        for seed in group['seeds']:
            if seed['row'] not in members or seed['source'] not in by_row[seed['row']]['aliases']:
                raise ValueError('seed is not a member of the original group')
            for alias in by_row[seed['row']]['aliases']:
                for kind, text in [('phrase', ' '.join(alias['fragments'])), ('subject', alias['subject'])]:
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError('nonempty source text required')
                    variants.setdefault((kind, text), {})[alias['short_id']] = alias
        if not variants:
            raise ValueError('group has no seed candidates')
        for (kind, text), sources in sorted(variants.items()):
            digest = hashlib.sha256(json.dumps([group['id'], kind, text], ensure_ascii=False).encode()).hexdigest()
            candidates.append(dict(id='C' + digest[:16], group=group['id'], kind=kind,
                                   text=text, sources=list(sources.values())))
    if len({c['id'] for c in candidates}) != len(candidates):
        raise ValueError('candidate identifier collision')
    groups_by_id = {g['id']: g for g in groups}
    pairs = []
    for candidate in candidates:
        for row in groups_by_id[candidate['group']]['evidence']:
            for alias in row['aliases']:
                pairs.append(dict(
                    measurement='coverage', kind=candidate['kind'], group=candidate['group'],
                    candidate=candidate['id'], row=row['row'], vector=alias['short_id'],
                    note=alias['note_short_id'],
                    premise=fixture['template'].format(alias['subject']),
                    hypothesis=fixture['template'].format(candidate['text'])))
    for child in candidates:
        for parent in candidates:
            if child['group'] == parent['group'] or child['kind'] != parent['kind']:
                continue
            pairs.append(dict(
                measurement='relation', kind=child['kind'],
                child_group=child['group'], parent_group=parent['group'],
                child_candidate=child['id'], parent_candidate=parent['id'],
                premise=fixture['template'].format(child['text']),
                hypothesis=fixture['template'].format(parent['text'])))
    return candidates, pairs


def summarize(candidates, pairs):
    coverage = defaultdict(list)
    relations = defaultdict(list)
    for pair in pairs:
        if pair['measurement'] == 'coverage':
            coverage[pair['candidate']].append(pair)
        else:
            relations[pair['kind'], pair['child_group'], pair['parent_group']].append(pair)
    summaries = []
    for candidate in candidates:
        rows = coverage[candidate['id']]
        positive = [p for p in rows if p['score'] > .5]
        failed_rows = {p['row'] for p in rows if p['score'] <= .5}
        summaries.append(dict(
            candidate=candidate['id'], group=candidate['group'], kind=candidate['kind'],
            text=candidate['text'], aliases=len(rows), rows=sorted({p['row'] for p in rows}),
            notes=sorted({p['note'] for p in rows}),
            supported_rows=sorted({p['row'] for p in positive}),
            unanimously_supported_rows=sorted({p['row'] for p in rows} - failed_rows),
            supported_notes=sorted({p['note'] for p in positive}),
            unsupported_vectors=[p['vector'] for p in rows if p['score'] <= .5],
            minimum=min(p['score'] for p in rows), maximum=max(p['score'] for p in rows)))
    relation_summary = []
    for (kind, child, parent), rows in sorted(relations.items()):
        relation_summary.append(dict(kind=kind, child_group=child, parent_group=parent,
                                     combinations=len(rows),
                                     positive_combinations=sum(p['score'] > .5 for p in rows),
                                     minimum=min(p['score'] for p in rows),
                                     maximum=max(p['score'] for p in rows)))
    return dict(coverage=summaries, relations=relation_summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    groups = json.loads(args.groups.read_bytes())
    evidence = json.loads(args.evidence.read_bytes())
    fixture = json.loads(args.fixture.read_bytes())
    candidates, pairs = prepare_experiment(groups, evidence, fixture)
    metrics = score_pairs(pairs, fixture, args.cache)
    summary = summarize(candidates, pairs)
    sources = [Path(__file__), Path(__file__).with_name('group_description_relations.py'),
               Path(__file__).with_name('mask_description_nli.py')]
    config = dict(**metrics, run_id=fixture['run_id'],
                  input_hashes={name: sha256(path) for name, path in
                                [('groups', args.groups), ('evidence', args.evidence), ('fixture', args.fixture)]},
                  source_hashes={p.name: sha256(p) for p in sources},
                  notes='Verbatim existing subject candidates, not certified group meanings. No hierarchy or membership changed.')
    args.output.mkdir(parents=True)
    for name, value in [('candidates.json', candidates), ('scores.json', pairs),
                        ('summary.json', summary), ('groups.json', groups), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for source in sources + [args.fixture]:
        name = 'fixture.json' if source == args.fixture else source.name
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(candidates=len(candidates), pairs=len(pairs),
                         positive_group_directions=sum(r['positive_combinations'] > 0 for r in summary['relations']),
                         inference_seconds=metrics['inference_seconds'])))


if __name__ == '__main__':
    main()
