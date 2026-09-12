"""Construct singleton and same-description pair candidates from frozen meanings."""

import argparse
from itertools import combinations
import json
from pathlib import Path
import time

from lmms_pos_control import validate_sources
from lmms_occurrence_probe import peak_rss_kib
from semantic_graph_patterns import construct
from semantic_graph_probe import digest, normalize_senses, save
from semantic_ontology_comparison import compare_condition


def source_graphs(inputs, scores, *, pairs):
    sources = {r['row']: r for r in inputs}
    if len(sources) != len(inputs):
        raise ValueError('duplicate source descriptions')
    graphs = {row:dict(row=row, note=r['note'], nodes=[], edges=[])
              for row,r in sources.items()}
    seen = set()
    for target in scores:
        row, index = target['row'], target['word_index']
        if row not in sources or (row,index) in seen:
            raise ValueError('unknown description or duplicate word occurrence')
        seen.add((row,index))
        source = sources[row]
        word = target['word']
        if (target['note'] != source['note'] or target['subject'] != source['subject']
                or source['subject'][word['start_char']:word['end_char']] != word['text']):
            raise ValueError('source identity or word offsets changed')
        if target['matches']:
            graphs[row]['nodes'].append(dict(id=index, context=0,
                                             sense=target['matches'][0]['synset']))
    for graph in graphs.values():
        graph['nodes'].sort(key=lambda n:n['id'])
        if pairs:
            graph['edges'] = [dict(source=a['id'],target=b['id'],role='same_description')
                              for a,b in combinations(graph['nodes'],2)
                              if a['sense'] != b['sense']]
    return [graphs[row] for row in sorted(graphs)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source','original','wordnet-root','plan','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier construction')
    from nltk.corpus import wordnet as wn
    inputs = json.loads((args.original/'inputs.json').read_bytes())
    encoded = json.loads((args.original/'tokenization.json').read_bytes())
    scores = json.loads((args.source/'scores.json').read_bytes())
    config = json.loads((args.source/'config.json').read_bytes())
    archive = args.wordnet_root/'corpora'/'wordnet.zip'
    if digest(archive) != config['source_hashes']['wordnet']:
        raise ValueError('WordNet archive changed')
    original_config = json.loads((args.original/'config.json').read_bytes())
    if digest(args.original/'inputs.json') != original_config['input_sha256']:
        raise ValueError('original input descriptions changed')
    validate_sources(inputs,encoded,scores,wn,archive)
    available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    if available < 4 * 1024 ** 2:
        raise RuntimeError('less than 4 GiB available; defer construction')
    started = time.monotonic()
    graphs, lexicon = normalize_senses(source_graphs(inputs,scores,pairs=True),args.wordnet_root)
    baseline_graphs = [dict(g,edges=[]) for g in graphs]
    baseline = construct(inputs,baseline_graphs,lexicon['senses'],'connection')
    paired = construct(inputs,graphs,lexicon['senses'],'connection')
    comparison = [compare_condition(a,b) for a,b in zip(baseline['conditions'],paired['conditions'])]
    result = dict(run_id='USC01',source='USM02 surface_pos top1; all targets',
                  pair_meaning='two distinct assigned concepts in one description, not event roles',
                  baseline=baseline,paired=paired,comparison=comparison)
    args.output.mkdir(parents=True)
    for name,value in [('result.json',result),('inputs.json',inputs),('graphs.json',graphs),
                       ('lexicon.json',lexicon)]:
        save(args.output/name,value)
    sources = [Path(__file__),Path(__file__).with_name('semantic_graph_patterns.py'),
               Path(__file__).with_name('semantic_graph_probe.py'),
               Path(__file__).with_name('semantic_ontology_comparison.py'),
               Path(__file__).with_name('lmms_pos_control.py'),
               Path(__file__).with_name('lmms_occurrence_probe.py'),args.plan]
    for source in sources:
        (args.output/source.name).write_bytes(source.read_bytes())
    details = dict(run_id='USC01',source_occurrences=len(scores),
                   assigned_occurrences=sum(bool(t['matches']) for t in scores),
                   descriptions=len(inputs),notes=len({r['note'] for r in inputs}),
                   source_pairs=sum(len(g['edges']) for g in graphs),
                   elapsed_seconds=time.monotonic()-started,
                   peak_rss_kib=peak_rss_kib(),
                   input_hashes={str(p):digest(p) for p in
                                 [args.original/'inputs.json',args.original/'tokenization.json',
                                  args.source/'scores.json',args.source/'config.json',archive]},
                   source_hashes={p.name:digest(p) for p in sources},
                   model_encoding=False,paid_resource_cost_usd=0)
    save(args.output/'config.json',details)
    print(json.dumps(dict(details,conditions=[
        {k:c[k] for k in ('id','baseline_patterns','augmented_patterns',
                         'baseline_recurring_note_sets','augmented_recurring_note_sets')}
        for c in comparison])),flush=True)


if __name__ == '__main__':
    main()
