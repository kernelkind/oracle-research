"""Controlled input rendering of already-scored subject pairs; no hierarchy edits."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

from group_description_relations import score_pairs
from mask_description_nli import sha256


def prepare_controls(pairs):
    prefix = 'This text is about '
    controls = []
    for index, pair in enumerate(pairs):
        if pair['kind'] != 'subject':
            continue
        texts = []
        for name in ['premise', 'hypothesis']:
            rendered = pair[name]
            if not rendered.startswith(prefix) or not rendered.endswith('.'):
                raise ValueError('expected the frozen GDR02 input wrapper')
            original = rendered[len(prefix):-1]
            if not original.strip():
                raise ValueError('empty original subject')
            texts.append(original)
        premise, hypothesis = texts
        punctuation = lambda text: '' if text.endswith(('.', '!', '?')) else '.'
        normalized_hypothesis = prefix + hypothesis + punctuation(hypothesis)
        base = {k: v for k, v in pair.items() if k not in {'score', 'logits', 'token_count'}}
        for condition, rendered_premise in [
                ('punctuation', prefix + premise + punctuation(premise)),
                ('direct_premise', premise)]:
            controls.append(dict(base, condition=condition, source_pair=index,
                                 baseline_score=pair['score'], premise=rendered_premise,
                                 hypothesis=normalized_hypothesis))
    if not controls:
        raise ValueError('no source subject pairs')
    return controls


def summarize_controls(pairs):
    groups = defaultdict(list)
    for pair in pairs:
        groups[pair['condition'], pair['measurement']].append(pair)
    return [dict(condition=condition, measurement=measurement, pairs=len(rows),
                 positive=sum(p['score'] > .5 for p in rows),
                 became_positive=sum(p['score'] > .5 >= p['baseline_score'] for p in rows),
                 became_negative=sum(p['baseline_score'] > .5 >= p['score'] for p in rows))
            for (condition, measurement), rows in sorted(groups.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    source_names = ['scores.json', 'config.json', 'fixture.json', 'groups.json', 'candidates.json']
    inputs = {name: args.source / name for name in source_names}
    source_config = json.loads(inputs['config.json'].read_bytes())
    fixture = json.loads(inputs['fixture.json'].read_bytes())
    if source_config['run_id'] != 'GDR02' or fixture['run_id'] != 'GDR02':
        parser.error('this control requires the frozen GDR02 run')
    pairs = prepare_controls(json.loads(inputs['scores.json'].read_bytes()))
    metrics = score_pairs(pairs, fixture, args.cache)
    sources = [Path(__file__), Path(__file__).with_name('group_description_relations.py'),
               Path(__file__).with_name('mask_description_nli.py')]
    config = dict(**metrics, run_id='GDR03',
                  input_hashes={name: sha256(path) for name, path in inputs.items()},
                  source_hashes={p.name: sha256(p) for p in sources},
                  notes='Input-rendering control only. Baseline scores retained. No semantic edits or hierarchy changes.')
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('summary.json', summarize_controls(pairs)),
                        ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for source in sources:
        with (args.output / source.name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(pairs=len(pairs), inference_seconds=metrics['inference_seconds'])))


if __name__ == '__main__':
    main()
