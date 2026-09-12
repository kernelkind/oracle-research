"""Change only the descriptions in a fixed sense-relation diagnostic."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path

from mask_description_nli import sha256
from sense_relation_probe import prepare_pairs, score_pairs


def prepare_control(source, definitions):
    previous = [p for p in source if p['condition'] == 'manual']
    lookup = {(p['child_group'], p['parent_group']): p for p in previous}
    ids = [g['id'] for g in definitions['groups']]
    if len(ids) < 2 or len(set(ids)) != len(ids) or len(lookup) != len(previous):
        raise ValueError('distinct groups and baseline pairs required')
    pairs = prepare_pairs([], definitions, [])
    if set(lookup) != {(p['child_group'], p['parent_group']) for p in pairs}:
        raise ValueError('all original group pairs must remain unchanged')
    for pair in pairs:
        pair['condition'] = 'definitions'
        pair['baseline'] = copy.deepcopy(lookup[pair['child_group'], pair['parent_group']])
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'definitions', 'cache', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous experiments')
    definitions = json.loads(args.definitions.read_bytes())
    pairs = prepare_control(json.loads(args.source.read_bytes()), definitions)
    metrics = score_pairs(pairs, args.cache)
    paths = {'source.json': args.source, 'definitions.json': args.definitions,
             'sense_definition_control.py': Path(__file__),
             'sense_relation_probe.py': Path(__file__).with_name('sense_relation_probe.py'),
             'mask_description_nli.py': Path(__file__).with_name('mask_description_nli.py')}
    config = dict(**metrics, run_id=definitions['run_id'], input_files={k: sha256(v) for k, v in paths.items()},
                  note='Manual definition-input diagnostic only; groups, masks, notes and model unchanged.')
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('config.json', config),
                        ('summary.json', dict(Counter(p['prediction'] for p in pairs)))]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for name, source in paths.items():
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(Counter(p['prediction'] for p in pairs))))


if __name__ == '__main__':
    main()
