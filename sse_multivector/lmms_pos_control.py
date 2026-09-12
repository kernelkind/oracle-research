"""Rescore frozen USM01 vectors with original-word/POS candidates; no encoder."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from lmms_occurrence_probe import PARTS, candidate_keys, digest, peak_rss_kib, rank_conditions, read_inventory


def validate_sources(inputs, encoded, targets, wordnet, archive):
    if wordnet.get_version() != '3.0':
        raise ValueError('dictionary version changed')
    loaded = getattr(getattr(wordnet.root, 'zipfile', None), 'filename', None)
    if loaded is None or Path(loaded).resolve() != archive.resolve():
        raise ValueError('loaded dictionary differs from verified archive')
    if len(inputs) != len(encoded) or len({r['row'] for r in inputs}) != len(inputs):
        raise ValueError('source rows differ')
    expected = []
    for source, record in zip(inputs, encoded):
        if any(record.get(key) != value for key, value in source.items()):
            raise ValueError('encoded source description, note or mask changed')
        indices = [i for i, word in enumerate(record['words']) if word['upos'] in PARTS]
        if indices != record['targets']:
            raise ValueError('encoded target selection changed')
        for index in indices:
            word = record['words'][index]
            if source['subject'][word['start_char']:word['end_char']] != word['text']:
                raise ValueError('target offsets do not recover source word')
            expected.append(dict(row=source['row'], note=source['note'],
                                 subject=source['subject'], word_index=index, word=word))
    actual = [{key: target[key] for key in ('row', 'note', 'subject', 'word_index', 'word')}
              for target in targets]
    if actual != expected:
        raise ValueError('saved target identities or order changed')


def score_saved(targets, vectors, labels, matrix, wordnet):
    if vectors.shape != (len(targets), matrix.shape[1]) or len(labels) != matrix.shape[0]:
        raise ValueError('saved target/inventory dimensions differ')
    if not np.isfinite(vectors).all() or not np.isfinite(matrix).all():
        raise ValueError('finite vectors required')
    if len(targets) * len(labels) * 8 > 512 * 1024 ** 2:
        raise ValueError('score allocation exceeds diagnostic limit')
    all_scores = (matrix @ vectors.T).T
    results = []
    comparisons, values, maximum = 0, 0, 0.
    for target, scores in zip(targets, all_scores):
        word = target['word']
        candidates = {c:candidate_keys(word['text'],word['lemma'],word['upos'],c,wordnet)
                      for c in ('saved','surface','unrestricted','surface_pos')}
        ranked = rank_conditions(labels, scores, candidates)
        for condition in ('saved','surface','unrestricted'):
            existing = target['matches'][condition]
            current = ranked[condition]
            if [v['key'] for v in existing] != [key for key,_ in current]:
                raise ValueError('USM01 match identities changed')
            for old, (_,score) in zip(existing,current):
                delta = abs(old['cosine'] - score)
                maximum = max(maximum, delta)
                if delta > 1e-12:
                    raise ValueError('USM01 score replay changed')
                values += 1
            comparisons += 1
        selected = candidates['surface_pos']
        results.append(dict(row=target['row'],note=target['note'],subject=target['subject'],
                            word_index=target['word_index'],word=word,
                            candidate_keys=sorted(selected),
                            matches=[dict(key=key,cosine=score,
                                          synset=wordnet.lemma_from_key(key).synset().name(),
                                          definition=wordnet.lemma_from_key(key).synset().definition())
                                     for key,score in ranked['surface_pos']]))
    return results, dict(comparisons=comparisons,cosines=values,maximum_cosine_difference=maximum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source','assets','plan','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous results')
    from nltk.corpus import wordnet as wn
    config = json.loads((args.source/'config.json').read_bytes())
    verification = json.loads((args.source.parent/'verification.json').read_bytes())
    execution = json.loads((args.source.parent/'execution.json').read_bytes())
    paths = dict(vectors=args.source/'target-vectors.npz',scores=args.source/'scores.json',
                 inputs=args.source/'inputs.json',config=args.source/'config.json',
                 tokenization=args.source/'tokenization.json',
                 inventory=args.assets/'lmms-sp-usm.bert-large-cased.vectors.zip',
                 wordnet=Path(execution['wordnet']['archive']))
    expected = dict(vectors=verification['target_vectors_sha256'],
                    inventory=config['assets'][paths['inventory'].name],
                    wordnet=execution['wordnet']['sha256'])
    actual = {key:digest(path) for key,path in paths.items()}
    if any(actual[key]!=value for key,value in expected.items()):
        raise ValueError('source/resource hash mismatch')
    if digest(args.source/'inputs.json')!=config['input_sha256'] or wn.get_version()!='3.0':
        raise ValueError('source descriptions or dictionary version changed')
    memory = {line.split(':')[0]:int(line.split()[1]) for line in
              Path('/proc/meminfo').read_text().splitlines()}
    if memory['MemAvailable'] < 6 * 1024 ** 2:
        raise RuntimeError('less than 6 GiB available; do not load inventory')
    started = time.monotonic()
    targets = json.loads(paths['scores'].read_bytes())
    validate_sources(json.loads(paths['inputs'].read_bytes()),
                     json.loads(paths['tokenization'].read_bytes()), targets, wn, paths['wordnet'])
    vectors = np.load(paths['vectors'],allow_pickle=False)['vectors']
    labels,matrix,info = read_inventory(paths['inventory'])
    results,replay = score_saved(targets,vectors,labels,matrix,wn)
    summary = dict(run_id='USM02',source_run='USM01',condition='surface_pos',
                   targets=len(results),descriptions=len({r['row'] for r in results}),
                   notes=len({r['note'] for r in results}),
                   empty=sum(not r['matches'] for r in results),replay=replay,
                   normalization_matching_seconds=time.monotonic()-started,
                   peak_rss_kib=peak_rss_kib(),
                   source_hashes=actual,inventory=info,wordnet_version=wn.get_version(),
                   plan_sha256=digest(args.plan),runner_sha256=digest(Path(__file__)),
                   helper_sha256=digest(Path(__file__).with_name('lmms_occurrence_probe.py')),
                   model_encoding=False,paid_resource_cost_usd=0)
    args.output.mkdir(parents=True)
    for name,value in [('scores.json',results),('config.json',summary)]:
        with (args.output/name).open('x') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    for source in (Path(__file__),Path(__file__).with_name('lmms_occurrence_probe.py'),args.plan):
        with (args.output/source.name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
