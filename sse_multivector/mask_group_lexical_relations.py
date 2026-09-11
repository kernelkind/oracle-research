"""Propose lexical relations between frozen mask groups; never changes membership."""
import argparse
from collections import deque
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import time


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_groups(descriptions, evidence):
    by_row = {r['row']: r for r in evidence}
    if len(by_row) != len(evidence):
        raise ValueError('duplicate evidence row')
    if len({d['id'] for d in descriptions}) != len(descriptions):
        raise ValueError('duplicate group ID')
    groups = []
    for d in descriptions:
        if not d['seed_rows'] or not set(d['seed_rows']) <= set(d['rows']):
            raise ValueError('seed rows must be nonempty members')
        records = [by_row[r] for r in d['rows']]
        notes = {a['note_short_id'] for r in records for a in r['aliases']}
        if notes != set(d['notes']):
            raise ValueError('group note set differs from evidence')
        seeds = [dict(row=r, source=a) for r in d['seed_rows'] for a in by_row[r]['aliases']]
        # Use complete source phrases, never alphabetical feature order or guessed heads.
        queries = sorted({'_'.join(' '.join(s['source']['fragments']).casefold().split())
                          for s in seeds})
        groups.append(dict(id=d['id'], queries=queries, seeds=seeds,
                           source_group=d, evidence=records))
    return groups


def load_wordnet(queries, root):
    import nltk.data
    from nltk.corpus.reader.wordnet import WordNetCorpusReader
    from nltk.data import ZipFilePathPointer
    archive = root / 'corpora' / 'wordnet.zip'
    # NLTK's reader also loads index.sense through its standard corpus lookup.
    # Restrict that lookup to this pinned corpus instead of any user installation.
    nltk.data.path[:] = [str(root)]
    reader = WordNetCorpusReader(ZipFilePathPointer(str(archive), 'wordnet/'), None)
    senses, matches = {}, {}
    pending = deque()
    for query in sorted(queries):
        hits = reader.synsets(query)
        matches[query] = sorted(s.name() for s in hits)
        pending.extend(hits)
    while pending:
        s = pending.popleft()
        if s.name() in senses:
            continue
        parents = s.hypernyms()
        senses[s.name()] = dict(definition=s.definition(), lemmas=s.lemma_names(),
                                examples=s.examples(), pos=s.pos(),
                                hypernyms=sorted(p.name() for p in parents))
        pending.extend(parents)
    return dict(queries=matches, senses=dict(sorted(senses.items())),
                source=dict(name='Princeton WordNet', version=reader.get_version(),
                            archive_sha256=digest(archive), nltk_version=importlib.metadata.version('nltk'),
                            relation='hypernyms only; instance and part-whole links excluded'))


def ancestor_paths(start, senses):
    paths = {start: [start]}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for parent in sorted(senses[current]['hypernyms']):
            if parent not in paths:
                paths[parent] = paths[current] + [parent]
                pending.append(parent)
    del paths[start]
    return paths


def lexical_relations(groups, lexicon):
    senses = {g['id']: sorted({s for q in g['queries'] for s in lexicon['queries'].get(q, [])})
              for g in groups}
    paths = {s: ancestor_paths(s, lexicon['senses']) for ss in senses.values() for s in ss}
    pairs, broader, equivalent = [], [], []
    for child in groups:
        cid = child['id']
        for parent in groups:
            pid = parent['id']
            if cid == pid:
                continue
            shared = sorted(set(senses[cid]) & set(senses[pid]))
            witnesses = [dict(child_sense=c, parent_sense=p, path=paths[c][p])
                         for c in senses[cid] for p in senses[pid] if p in paths[c]]
            pairs.append(dict(child=cid, parent=pid, shared_senses=shared,
                              broader_witnesses=witnesses,
                              unknown=not senses[cid] or not senses[pid]))
            if witnesses:
                broader.append(dict(parent=pid, child=cid, witnesses=witnesses,
                                    notes_already_contained=set(child['source_group']['notes']) <=
                                        set(parent['source_group']['notes'])))
            if shared and cid < pid:
                equivalent.append(dict(groups=[cid, pid], sense_ids=shared))
    return dict(group_senses=senses, pairs=pairs, broader_candidates=broader,
                equivalent_candidates=equivalent,
                unknown_groups=sorted(g for g, ss in senses.items() if not ss),
                interpretation='Sense-level proposals only. All group masks require semantic audit. '
                'No relation is not evidence of unrelatedness. No membership, equivalence or ancestry adopted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--lexicon', type=Path)
    source.add_argument('--wordnet-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous results')
    started = time.monotonic()
    groups = prepare_groups(json.loads(args.groups.read_bytes()), json.loads(args.evidence.read_bytes()))
    lexicon = (json.loads(args.lexicon.read_bytes()) if args.lexicon else
               load_wordnet({q for g in groups for q in g['queries']}, args.wordnet_root))
    result = lexical_relations(groups, lexicon)
    config = dict(run_id=args.run_id, groups_sha256=digest(args.groups),
                  evidence_sha256=digest(args.evidence), runner_sha256=digest(Path(__file__)),
                  lexicon_input_sha256=digest(args.lexicon or args.wordnet_root / 'corpora' / 'wordnet.zip'),
                  elapsed_seconds=time.monotonic() - started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  group_count=len(groups), ordered_pairs=len(result['pairs']),
                  note_count=len({n for g in groups for n in g['source_group']['notes']}),
                  unknown_group_count=len(result['unknown_groups']),
                  broader_candidates=len(result['broader_candidates']),
                  equivalent_candidates=len(result['equivalent_candidates']))
    args.output.mkdir(parents=True)
    for name, data in [('groups.json', groups), ('relations.json', result),
                       ('lexicon.json', lexicon), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    with (args.output / Path(__file__).name).open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    print(json.dumps(config))


if __name__ == '__main__':
    main()
