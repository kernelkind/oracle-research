"""Compare exact roles with witnessed undirected connections on frozen SGC01."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import time

from semantic_graph_patterns import construct
from semantic_graph_probe import digest, save


def compare(exact, connected):
    for field in ['source_rows', 'source_notes']:
        if exact[field] != connected[field]:
            raise ValueError('comparison requires identical source identities')
    before = {c['id']: c for c in exact['conditions']}
    after = {c['id']: c for c in connected['conditions']}
    if before.keys() != after.keys():
        raise ValueError('comparison requires identical lexical conditions')
    comparisons = []
    for name, condition in after.items():
        original = before[name]
        singleton = lambda c: {p['id']: p for p in c['patterns'] if p['kind'] == 'singleton'}
        if singleton(original) != singleton(condition):
            raise ValueError('singleton evidence changed across relation policies')
        counterparts = defaultdict(list)
        for pattern in original['patterns']:
            if pattern['kind'] == 'role':
                a, _, b = pattern['key']
                counterparts[tuple(sorted([a, b]))].append(pattern)
        previous_sets = {tuple(p['notes']) for p in original['patterns']}
        recurring = []
        for pattern in condition['patterns']:
            if pattern['kind'] != 'connection' or len(pattern['notes']) < 2:
                continue
            matches = counterparts[tuple(pattern['key'])]
            if not matches or set(pattern['notes']) != set().union(*(set(p['notes']) for p in matches)):
                raise ValueError('connection support differs from its exact edge witnesses')
            complete = sorted(p['id'] for p in matches if p['notes'] == pattern['notes'])
            recurring.append(dict(
                id=pattern['id'], key=pattern['key'], notes=pattern['notes'], rows=pattern['rows'],
                complete_exact_counterpart_ids=complete,
                expanded_beyond_each_exact_counterpart=not complete,
                note_set_absent_from_exact=tuple(pattern['notes']) not in previous_sets,
                exact_counterparts=[{k: p[k] for k in ['id', 'key', 'notes', 'rows']}
                                    for p in sorted(matches, key=lambda p: (p['notes'], p['id']))]))
        comparisons.append(dict(
            id=name, singletons_unchanged=True,
            exact_patterns=len(original['patterns']), connection_patterns=len(condition['patterns']),
            exact_links=len(original['edges']), connection_links=len(condition['edges']),
            exact_recurring_note_sets=len(original['recurring_groups']),
            connection_recurring_note_sets=len(condition['recurring_groups']),
            recurring_connections=recurring))
    return dict(conditions=comparisons)


def inventory(result, comparison):
    lines = ['# SGC02 connected-pattern inventory', '',
             'These are candidate meanings, not approved category labels. Each pair',
             'requires a real source edge but ignores its label and direction.',
             'All original directions and roles remain in the saved witnesses.', '',
             'All recurring note sets and their most-specific patterns are listed.',
             'An expanded pair has more notes than any one exact-role counterpart;',
             'that is a structural observation, not a semantic improvement.', '']
    comparisons = {c['id']: c for c in comparison['conditions']}
    for condition in result['conditions']:
        patterns = {p['id']: p for p in condition['patterns']}
        compared = {p['id']: p for p in comparisons[condition['id']]['recurring_connections']}
        lines += [f"## {condition['id']}", '']
        for group in condition['recurring_groups']:
            lines += [f"### {' '.join(group['notes'])}", '']
            for identifier in group['most_specific_pattern_ids']:
                p = patterns[identifier]
                key = ' connected to '.join(p['key']) if p['kind'] == 'connection' else p['key'][0]
                extra = 'expanded pair' if identifier in compared and compared[identifier]['expanded_beyond_each_exact_counterpart'] else 'existing note support'
                lines += [f"- `{identifier}`: {key}; rows {', '.join(map(str, p['rows']))}; {extra}."]
            lines += ['']
    return '\n'.join(lines).rstrip() + '\n'


def run(args):
    if args.output.exists():
        raise ValueError('output already exists; preserve previous results')
    started = time.monotonic()
    paths = {name: args.baseline / name for name in ['inputs.json', 'graphs.json', 'lexicon.json', 'result.json']}
    inputs = json.loads(paths['inputs.json'].read_bytes())
    graphs = json.loads(paths['graphs.json'].read_bytes())
    rows = {g['row'] for g in graphs}
    records = [r for r in inputs if r['row'] in rows]
    lexicon = json.loads(paths['lexicon.json'].read_bytes())
    exact = construct(records, graphs, lexicon['senses'])
    baseline = json.loads(paths['result.json'].read_bytes())
    expected = {k: v for k, v in baseline.items() if k not in {'run_id', 'excluded_rows'}}
    if exact != expected:
        raise ValueError('exact policy no longer reproduces frozen SGC01')
    connected = construct(records, graphs, lexicon['senses'], relation_policy='connection')
    comparison = compare(exact, connected)
    connected.update(run_id='SGC02', excluded_rows=baseline['excluded_rows'])
    comparison.update(run_id='SGC02', baseline_run='SGC01')
    args.output.mkdir(parents=True)
    save(args.output / 'result.json', connected)
    save(args.output / 'comparison.json', comparison)
    save(args.output / 'inputs.json', inputs)
    (args.output / 'INVENTORY.md').write_text(inventory(connected, comparison))
    sources = ['semantic_graph_patterns.py', 'semantic_graph_probe.py', Path(__file__).name]
    for name in sources:
        (args.output / name).write_bytes((Path(__file__).parent / name).read_bytes())
    save(args.output / 'config.json', dict(
        run_id='SGC02', baseline_directory=str(args.baseline),
        baseline_sha256={name: digest(path) for name, path in paths.items()},
        relation_policies=['exact', 'connection'], lexical_relations=lexicon['source']['relations'],
        no_new_inference=True, no_source_repairs=True,
        elapsed_seconds=time.monotonic() - started,
        source_hashes={name: digest(args.output / name) for name in sources}))
    print(json.dumps([{k: v for k, v in c.items() if k != 'recurring_connections'} |
                      {'expanded_recurring_connections': sum(p['expanded_beyond_each_exact_counterpart']
                         for p in c['recurring_connections'])} for c in comparison['conditions']]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
