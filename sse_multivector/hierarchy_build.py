#!/usr/bin/env python3
"""Offline hierarchy stages using frozen title experiments and saved TRUE answers.

No command here performs inference. Title requests use experiment.py; TRUE
inputs use the existing scorer. Historical hierarchy_refresh artifacts stay put.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from category_mask_instances import reconstruct
from prepare_category_title_inputs import prepare
from true_category_graph import prepare_inputs
from true_graph_categories import render_categories
from true_graph_merge import _digest, merge_graph, union_packet
from true_graph_notes import derive_note_memberships

SSE = Path(__file__).resolve().parent
TITLE = SSE / 'hdbv2-node-description-probe-v38/prompt.txt'
TITLE_SPEC = SSE / 'experiment_specs/title-v38-full-luna-max.json'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def artifact_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    (path / '.gitignore').write_text('*\n')
    return path


def consolidate_nodes(source):
    """Merge equal sets of exact masks before titles/TRUE; retain strict subsets."""
    prepared = prepare(source, '{NUMBERED_INSTANCES}', [])
    if not prepared:
        raise ValueError('nonempty node inventory required')
    classes = {}
    for node in prepared:
        key = frozenset((s['note_id'], tuple(map(tuple, s['byte_spans'])))
                        for s in node['sources'])
        classes.setdefault(key, []).append(node['group'])
    by_id = {p['packet']: p for p in source['packets']}
    if any(not isinstance(key, str) or not key.strip() for key in by_id):
        raise ValueError('nonempty string node IDs required')
    mapping, originals, replacements = {}, {}, {}
    for members in classes.values():
        members = sorted(members)
        group = 'merged-' + _digest(members) if len(members) > 1 else members[0]
        if group in originals or (len(members) > 1 and group in by_id):
            raise ValueError('consolidated node ID collision')
        originals[group] = members
        mapping.update({m: group for m in members})
        replacements[group] = (union_packet(group, members, {m: by_id[m]['instances'] for m in members})
                               if len(members) > 1 else deepcopy(by_id[group]))
    # Preserve untouched input ordering so the saved v38 requests still match.
    packets = [replacements[g] for g in dict.fromkeys(mapping[p['packet']] for p in source['packets'])]
    return dict(schema_version=1, policy='equal-ordered-byte-span-mask-sets-v1',
                source=deepcopy(source), source_sha256=_digest(source),
                source_packets=dict(deepcopy(source), packets=packets), member_to_group=mapping,
                original_members=originals)


def titles_from_report(packets, report, *, include_reviews=False):
    """Bind a receipt-validated experiment report to these exact title inputs."""
    settings = {k: report.get('settings', {}).get(k)
                for k in ('provider', 'model', 'reasoning_effort')}
    if (report.get('prompt_id') != 'v38' or report.get('adapter') != 'titles'
            or settings['provider'] != 'openai-codex'
            or (settings['model'], settings['reasoning_effort']) not in
               {('gpt-6-luna', 'max'), ('gpt-6-astra', 'low')}):
        raise ValueError('frozen v38/Luna-max or v38/Astra-low title experiment required')
    prepared = prepare(packets, TITLE.read_text(), [])
    packet_by_id = {p['packet']: p for p in packets['packets']}
    cases = report['cases']
    by_id = {c['id']: c for c in cases}
    if len(by_id) != len(cases) or set(by_id) != {g['group'] for g in prepared}:
        raise ValueError('title experiment inventory differs from node inventory')
    groups = []
    for group in prepared:
        case = by_id[group['group']]
        title = case.get('parsed', {}).get('title')
        if (case.get('status') != 'valid' or not case.get('receipt')
                or case.get('prompt') != group['prompt']
                or case.get('evidence', {}).get('instances') != group['instances']
                or case.get('evidence', {}).get('packet') != packet_by_id[group['group']]
                or not isinstance(title, str) or not title.strip() or '\n' in title):
            raise ValueError('missing, invalid or mismatched title: ' + group['group'])
        groups.append(dict(group, title=title, receipt=deepcopy(case['receipt'])))
        if include_reviews and case.get('reviews'):
            groups[-1]['reviews'] = deepcopy(case['reviews'])
    return dict(prompt_version='v38', settings=settings, report_sha256=_digest(report), groups=groups)


def validate_merge(merged):
    expected = merge_graph(**merged['source'])
    if 'node_consolidation' in merged:
        nodes = merged['node_consolidation']
        if (consolidate_nodes(nodes['source']) != nodes
                or nodes['source_packets'] != merged['source']['source_packets']
                or nodes['original_members'] != merged['source'].get('original_members')):
            raise ValueError('pre-TRUE node consolidation differs from saved merge inputs')
        expected['node_consolidation'] = nodes
    if expected != merged:
        raise ValueError('saved merge differs from replay of its original evidence')


def name_merge(merged, report):
    """Apply verified naming outputs without changing any saved relationship."""
    validate_merge(merged)
    pending = merged['naming_source_packets']
    names = {}
    if pending['packets']:
        if report is None:
            raise ValueError('merged titles are pending; a completed naming experiment is required')
        names = {n['group']: n['title'] for n in titles_from_report(pending, report)['groups']}
    elif report is not None:
        raise ValueError('no merged nodes require naming')
    graph = deepcopy(merged['graph'])
    for node in graph['nodes']:
        if node['group'] in names:
            node.update(title=names[node['group']], title_status='generated')
    memberships = derive_note_memberships(graph, merged['source_packets'])
    return dict(graph=graph, memberships=memberships, naming_report=deepcopy(report),
                merge_sha256=_digest(merged))


def _original_instances(mask):
    if mask.get('origins'):
        for origin in mask['origins']:
            yield from _original_instances(origin['source_instance'])
    else:
        yield mask


def package_merge(merged, report, source, mapping, output):
    named = name_merge(merged, report)
    spec = render_categories(named['graph'], named['memberships'], source, mapping,
                             hierarchy_id='Reversible native TRUE hierarchy · no membership expansion')
    # Browser masks display the original IDs, including aliases across both
    # merge stages, rather than only the derived union's synthetic instance ID.
    original_masks = deepcopy(named['memberships'])
    for node in original_masks['nodes']:
        node['matched_instances'] = [i for m in node['matched_instances'] for i in _original_instances(m)]
    spec = reconstruct(spec, original_masks, [], Path(source).read_bytes())
    nodes = {n['group']: n for n in named['graph']['nodes']}
    rejected_titles = {}
    for original in merged['source']['titles']['groups']:
        users = [r for r in original.get('reviews', [])
                 if r.get('role') == 'user' and r.get('current')]
        if users and users[-1].get('verdict') == 'reject':
            group = merged['member_to_group'][original['group']]
            rejected_titles.setdefault(group, []).append(original['title'])
    for node in spec['nodes']:
        if node['node_id'] in nodes:
            members = nodes[node['node_id']]['source_group_ids']
            node['analysis'] += ' Original nodes: ' + ', '.join(members) + '. Merging is provisional; displayed names do not change saved TRUE answers.'
            for title in rejected_titles.get(node['node_id'], []):
                node['analysis'] += ' User rejected original title: ' + title + '. Node retained; TRUE used this wording.'
    out = artifact_directory(output)
    save(out / 'named-graph.json', named)
    save(out / 'categories.json', spec)
    save(out / 'provenance.json', dict(merge=merged, source_path=str(Path(source).resolve()),
                                     mapping_path=str(Path(mapping).resolve()), mapping_sha256=_digest(read(mapping))))
    return spec


def title_spec(packets_path):
    spec = read(TITLE_SPEC)
    spec['prompt']['path'] = str(TITLE)
    spec['dataset']['path'] = str(Path(packets_path).resolve())
    return spec


def prepare_nodes(source_path, output):
    nodes = consolidate_nodes(read(source_path))
    out = artifact_directory(output)
    save(out / 'nodes.json', nodes)
    save(out / 'source-packets.json', nodes['source_packets'])
    save(out / 'title-spec.json', title_spec(out / 'source-packets.json'))
    return nodes


def collect_titles(nodes_path, experiment_path, output):
    # Re-read/validate real receipts through the existing experiment workflow;
    # do not trust an independently editable cached report.json.
    from experiment import report as experiment_report
    nodes = read(nodes_path)
    if consolidate_nodes(nodes['source']) != nodes:
        raise ValueError('saved node consolidation differs from source')
    report = experiment_report(experiment_path)
    titles = titles_from_report(nodes['source_packets'], report)
    pairs = prepare_inputs(titles)
    out = artifact_directory(output)
    save(out / 'nodes.json', nodes)
    save(out / 'title-report.json', report)
    save(out / 'titles.json', titles)
    save(out / 'true-inputs.json', pairs)
    return pairs


def prepare_naming(merged, output):
    validate_merge(merged)
    out = artifact_directory(output)
    save(out / 'merge.json', merged)
    save(out / 'naming-source-packets.json', merged['naming_source_packets'])
    if merged['naming_source_packets']['packets']:
        save(out / 'naming-spec.json', title_spec(out / 'naming-source-packets.json'))


def merge_saved(title_directory, scores_path, output):
    directory = Path(title_directory)
    nodes = read(directory / 'nodes.json')
    if consolidate_nodes(nodes['source']) != nodes:
        raise ValueError('saved node consolidation differs from source')
    titles = titles_from_report(nodes['source_packets'], read(directory / 'title-report.json'))
    if titles != read(directory / 'titles.json') or prepare_inputs(titles) != read(directory / 'true-inputs.json'):
        raise ValueError('saved TRUE inputs differ from frozen titles')
    titles = titles_from_report(nodes['source_packets'], read(directory / 'title-report.json'),
                                include_reviews=True)
    merged = merge_graph(titles, read(scores_path), nodes['source_packets'],
                         original_members=nodes['original_members'])
    merged['node_consolidation'] = nodes
    prepare_naming(merged, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='stage', required=True)
    for command, names in (
            ('nodes', ('source', 'output')),
            ('true-inputs', ('nodes', 'experiment', 'output')),
            ('merge', ('titles_directory', 'scores', 'output')),
            ('naming', ('merge', 'output')),
            ('package', ('merge', 'source', 'mapping', 'output'))):
        sub = commands.add_parser(command)
        for name in names:
            sub.add_argument(name, type=Path)
        if command == 'package':
            sub.add_argument('--naming-experiment', type=Path)
    args = parser.parse_args()
    try:
        if args.stage == 'nodes': prepare_nodes(args.source, args.output)
        elif args.stage == 'true-inputs': collect_titles(args.nodes, args.experiment, args.output)
        elif args.stage == 'merge': merge_saved(args.titles_directory, args.scores, args.output)
        elif args.stage == 'naming': prepare_naming(read(args.merge), args.output)
        else:
            from experiment import report as experiment_report
            report = experiment_report(args.naming_experiment) if args.naming_experiment else None
            package_merge(read(args.merge), report, args.source, args.mapping, args.output)
        print('Saved offline stage:', args.output)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
