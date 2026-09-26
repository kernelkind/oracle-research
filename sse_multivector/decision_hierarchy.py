"""Prepare title-pair decisions and export validated Jev answers to the existing UI.

Offline only. No fabricated TRUE scores, cycle repair, node merging, new titles,
membership expansion or inference. Use experiment.py for paid execution.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from category_mask_instances import reconstruct
from experiment_inputs import render
from hierarchy_build import artifact_directory, read, save, _original_instances
from true_category_graph import graph_from_decisions
from true_graph_categories import render_categories
from true_graph_notes import derive_note_memberships

SSE = Path(__file__).resolve().parent
PROMPT = SSE / 'node-subsumption-prompt-jev-v1/prompt.txt'


def make_cases(titles):
    groups = titles['groups']
    if not groups or len({g['group'] for g in groups}) != len(groups):
        raise ValueError('unique selected nodes required')
    return [dict(id=f'{a["group"]}-contains-{b["group"]}',
                 inputs=dict(A_TITLE=a['title'], B_TITLE=b['title']),
                 evidence=dict(original_a_id=a['group'], original_b_id=b['group']))
            for a in groups for b in groups if a['group'] != b['group']]


def prepare_section(titles_path, nodes_path, selected, output):
    titles, nodes = read(titles_path), read(nodes_path)
    inventory = {g['group']: g for g in titles['groups']}
    if not selected or len(set(selected)) != len(selected) or not set(selected) <= inventory.keys():
        raise ValueError('explicit unique known node IDs required')
    titles = dict(titles, groups=[inventory[key] for key in selected])
    packets = dict(nodes['source_packets'], packets=[p for p in nodes['source_packets']['packets'] if p['packet'] in selected])
    if {p['packet'] for p in packets['packets']} != set(selected):
        raise ValueError('every selected node needs original masks')
    cases = make_cases(titles)
    for case in cases:
        state = json.loads(render(PROMPT.read_text(), case['inputs']))['state']
        if state != dict(A=case['inputs']['A_TITLE'], B=case['inputs']['B_TITLE']):
            raise ValueError('JSON rendering changed a title')
    out = artifact_directory(output)
    save(out/'titles.json', titles)
    save(out/'source-packets.json', packets)
    save(out/'cases.json', dict(cases=cases))
    spec = read(SSE/'experiment_specs/nsp-jev-v1-hr02-diverse-pairs.json')
    spec['prompt']['path'] = str(PROMPT)
    spec['dataset']['path'] = str((out/'cases.json').resolve())
    save(out/'experiment-spec.json', spec)
    return cases


def graph_from_report(titles, report, *, prompt=None):
    if prompt is None:
        prompt = dict(id='NSP-Jev-v1', text=PROMPT.read_text())
    if report.get('prompt_id') != prompt['id'] or any(report.get('settings', {}).get(k) != v for k,v in
            dict(provider='openrouter', model='typesafe/jev-1.13', reasoning_effort='provider-default').items()):
        raise ValueError('matching prompt version / Jev provider-default report required')
    cases = report['cases']
    by_id = {c['id']: c for c in cases}
    expected = make_cases(titles)
    if len(by_id) != len(cases) or set(by_id) != {c['id'] for c in expected}:
        raise ValueError('complete exact pair inventory required')
    rows = []
    for row in expected:
        case = by_id[row['id']]
        choice = case.get('parsed', {}).get('contains', {}).get('choice')
        if (case.get('status') != 'valid' or not case.get('receipt') or
                case.get('inputs') != row['inputs'] or choice not in {'yes', 'no', 'uncertain'} or
                case.get('prompt') != render(prompt['text'], row['inputs'])):
            raise ValueError('missing, invalid or changed decision: ' + row['id'])
        rows.append(dict(id=row['id'], a_id=row['evidence']['original_a_id'], b_id=row['evidence']['original_b_id'],
                         predicted={'yes':True, 'no':False, 'uncertain':None}[choice],
                         answer=deepcopy(case['parsed']['contains']), receipt=deepcopy(case['receipt'])))
    graph = graph_from_decisions(titles['groups'], rows)
    graph.update(prompt_id=prompt['id'], decision_rule='choice', edge_rule='contains.choice == yes', decisions=rows)
    return graph


def package_view(titles, packets, report, source, mapping, output, *, prompt=None):
    graph = graph_from_report(titles, report, prompt=prompt)
    memberships = derive_note_memberships(graph, packets)
    out = artifact_directory(output)
    save(out/'graph.json', graph)
    save(out/'memberships.json', memberships)
    save(out/'provenance.json', dict(titles=titles, source_packets=packets, report=report,
                                   source_path=str(Path(source).resolve()), mapping_path=str(Path(mapping).resolve())))
    if graph['cycle_components']:
        raise ValueError('cycle prevents DAG browsing; all decisions saved in graph.json, no edges removed')
    spec = render_categories(graph, memberships, source, mapping,
                             hierarchy_id=f'HR02 Jev section · {graph["prompt_id"]} · original memberships',
                             connection_description='Saved Jev Choice answers; no manual corrections or membership expansion.')
    original = deepcopy(memberships)
    for node in original['nodes']:
        node['matched_instances'] = [i for m in node['matched_instances'] for i in _original_instances(m)]
    spec = reconstruct(spec, original, [], Path(source).read_bytes())
    save(out/'categories.json', spec)
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    for name in ['titles', 'nodes', 'output']: p.add_argument(name, type=Path)
    p.add_argument('--node', action='append', required=True)
    p = commands.add_parser('package')
    for name in ['section', 'experiment', 'source', 'mapping', 'output']: p.add_argument(name, type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        cases = prepare_section(args.titles, args.nodes, args.node, args.output)
        print(f'{len(args.node)} nodes; {len(cases)} directed comparisons; no inference')
    else:
        from experiment import load, report
        plan, _, _ = load(args.experiment)
        spec = package_view(read(args.section/'titles.json'), read(args.section/'source-packets.json'),
                            report(args.experiment), args.source, args.mapping, args.output, prompt=plan['prompt'])
        print(f'{len(spec["nodes"])-1} nodes and {len(spec["notes"])} posts; {args.output}/categories.json')


if __name__ == '__main__':
    main()
