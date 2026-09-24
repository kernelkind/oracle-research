#!/usr/bin/env python3
"""Reversibly contract native TRUE cycles, without inference or title repair.

This is an opt-in derived graph, not a replacement set of TRUE score rows.
HD02/HD03 remain provisional: paths may disagree with saved direct No answers.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from prepare_category_title_inputs import prepare
from true_category_graph import _reachability, build_graph
from true_graph_notes import _matched_instance, derive_note_memberships


POLICIES = {
    'HD01': 'native-complete-yes-v1',
    'HD02': 'strongly-connected-components-v1',
    'HD03': 'union-accepted-external-edges-v1',
    'HD04': 'combined-exact-masks-pending-title-v1',
    'HD05': 'sha256-sorted-original-member-ids-v1',
}


def _digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def union_packet(group, members, evidence):
    """Union exact masks, retaining complete member-scoped source records."""
    masks = {}
    for member in members:
        for item in evidence[member]:
            key = (item['note_id'], tuple(tuple(span) for span in item['byte_spans']))
            if key not in masks:
                record = deepcopy(item)
                if len(members) > 1:
                    record['instance'] = 'mask-' + _digest(key)
                record['origins'] = []
                masks[key] = record
            elif (masks[key]['text'] != item['text']
                  or masks[key]['fragments'] != item['fragments']):
                raise ValueError('conflicting text for identical mask')
            masks[key]['origins'].append(dict(source_group_id=member,
                                              source_instance=deepcopy(item)))
    return dict(packet=group, instances=[masks[key] for key in sorted(masks)])


def merge_graph(titles, scores, source_packets, *, original_members=None):
    """Keep raw inputs and return an SCC-contracted DAG with mask/edge origins.

    Singleton IDs/titles survive. New IDs hash sorted original member IDs; new
    titles are None/pending, never a member's arbitrarily chosen title. Naming
    packets can go straight to the existing title preparation adapter. All
    selected original masks survive in origins; same-post equal ordered byte
    spans appear only once in each output node, retaining all their aliases.
    Other packet masks remain in the raw inputs, not the merged membership.
    When exact-mask-set consolidation ran first, original_members carries its
    mapping so cycle IDs hash original nodes rather than intermediate IDs.

    Complete native answers are required. Missing/unresolved results must be
    recovered upstream, not interpreted as No. This stage performs no retries.
    Original score rows are never relabeled with new IDs or generated titles.
    """
    raw = build_graph(titles, scores, decision_rule='native')
    if raw['unresolved_native_rows']:
        raise ValueError('unresolved native answers: recover them before merging')
    original_memberships = derive_note_memberships(raw, source_packets)
    by_id = {n['group']: n for n in titles['groups']}
    originals = original_members if original_members is not None else {key: [key] for key in by_id}
    if set(originals) != set(by_id):
        raise ValueError('original-member mapping must cover the TRUE node inventory')
    seen = set()
    for members in originals.values():
        if (not isinstance(members, list) or not members
                or any(not isinstance(m, str) or not m for m in members)
                or len(set(members)) != len(members) or seen.intersection(members)):
            raise ValueError('original-member lists must be nonempty and disjoint')
        seen.update(members)
    evidence = {n['group']: n for n in original_memberships['nodes']}
    packet_by_id = {p['packet']: p for p in source_packets['packets']}
    # Title preparation shows each exact mask once. Preserve the source aliases
    # of those masks too, without admitting any additional mask identities.
    origins = {}
    for member in by_id:
        selected = {(i['note_id'], tuple(map(tuple, i['byte_spans'])))
                    for i in evidence[member]['matched_instances']}
        rows = packet_by_id[member]['instances']
        origins[member] = [
            _matched_instance(i, rows, member) for i in rows
            if (i['note_id'], tuple(map(tuple, i['byte_spans']))) in selected]
    components = sorted(sorted(c) for c in raw['strongly_connected_components'])
    mapping, nodes, packets = {}, [], []
    for members in components:
        merged = len(members) > 1
        original_ids = sorted(m for member in members for m in originals[member])
        group = ('merged-' + _digest(original_ids)) if merged else members[0]
        if merged and group in by_id:
            raise ValueError('merged ID collides with original ID: ' + group)
        if group in mapping.values():
            raise ValueError('merged ID collision: ' + group)
        mapping.update({member: group for member in members})
        packet = union_packet(group, members, origins)
        instances = packet['instances']
        node = {} if merged else deepcopy(by_id[members[0]])
        node.update(group=group, source_group_ids=original_ids,
                    title=None if merged else by_id[members[0]]['title'],
                    title_status='pending' if merged else 'original',
                    instances=[dict(instance=i['instance'], fragments=i['fragments'])
                               for i in instances])
        nodes.append(node)
        packets.append(packet)

    # Reuse the title adapter's exact-mask validation, including cross-packet
    # source-text consistency. Only selected instances participate.
    merged_packets = dict(packets=packets)
    prepare(merged_packets, '{NUMBERED_INSTANCES}', [])

    contributors = {}
    internal = []
    for row in raw['raw_edges']:
        a, b = mapping[row['a_id']], mapping[row['b_id']]
        if a == b:
            internal.append(row['id'])
        else:
            contributors.setdefault((a, b), []).append(row['id'])
    edges = [dict(a_id=a, b_id=b, source_score_ids=sorted(origins))
             for (a, b), origins in sorted(contributors.items())]
    ids = [node['group'] for node in nodes]
    adjacency = {group: set() for group in ids}
    for edge in edges:
        adjacency[edge['a_id']].add(edge['b_id'])
    reached = _reachability(adjacency)
    if any(group in reached[group] for group in ids):
        raise ValueError('SCC contraction must produce an acyclic graph')
    reduced = [edge for edge in edges if not any(
        child != edge['b_id'] and edge['b_id'] in reached[child]
        for child in adjacency[edge['a_id']])]
    children = {edge['b_id'] for edge in edges}
    graph = dict(
        nodes=nodes, raw_edges=edges, roots=[g for g in ids if g not in children],
        reachability={g: [other for other in ids if other in reached[g]] for g in ids},
        transitive_reduction_status='complete', transitive_reduced_edges=reduced,
        stats=dict(nodes=len(nodes), merged_components=sum(len(c) > 1 for c in components),
                   raw_edges=len(edges), transitive_reduced_edges=len(reduced)))
    memberships = derive_note_memberships(graph, merged_packets)

    # Verify exact path preservation modulo component identity, and preserve the
    # complete recursive post sets. These checks are independent of title text.
    merged_memberships = {n['group']: n for n in memberships['nodes']}
    for original, group in mapping.items():
        expected = {mapping[n] for n in raw['reachability'][original]} - {group}
        if expected != reached[group]:
            raise ValueError('contraction changed external reachability: ' + original)
        if (set(evidence[original]['recursive_note_ids'])
                != set(merged_memberships[group]['recursive_note_ids'])):
            raise ValueError('contraction changed recursive post membership: ' + original)
    source = dict(titles=titles, scores=scores, source_packets=source_packets)
    if original_members is not None:
        source['original_members'] = original_members
    result = dict(
        schema_version=1, policies=POLICIES,
        source_sha256={name: _digest(value) for name, value in source.items()},
        source=source, raw_graph=raw, graph=graph, member_to_group=mapping,
        internal_accepted_score_ids=sorted(internal), source_packets=merged_packets,
        memberships=memberships,
        naming_source_packets=dict(packets=[p for p, n in zip(packets, nodes)
                                           if n['title_status'] == 'pending']))
    return deepcopy(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('titles', type=Path)
    parser.add_argument('scores', type=Path)
    parser.add_argument('source_packets', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        source = {name: json.loads(getattr(args, name).read_text())
                  for name in ('titles', 'scores', 'source_packets')}
        result = merge_graph(**source)
        with args.output.open('x') as destination:
            json.dump(result, destination, ensure_ascii=False, indent=2)
            destination.write('\n')
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
