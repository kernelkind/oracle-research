"""Export a saved native TRUE graph for the existing category-and-note browser.

Revalidate the graph against its saved model outputs before changing only its
file representation. No inference, category selection, label edits or merging.
"""
import argparse
import hashlib
import json
from pathlib import Path

from true_category_graph import build_graph
from true_graph_notes import derive_note_memberships


def read(path):
    return json.loads(Path(path).read_text())


def export(canonical_path, graph_path, memberships_path, source_path, mapping_path,
           output_path, *, hierarchy_id='TRUE native answers'):
    output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    canonical, graph, memberships = map(read, (canonical_path, graph_path, memberships_path))
    expected_graph = build_graph(canonical['titles'], canonical['scores'], decision_rule='native')
    if graph != expected_graph:
        raise ValueError('saved graph differs from the native model outputs')
    if graph['transitive_reduced_edges'] is None:
        raise ValueError('category browsing requires an acyclic graph')
    expected_notes = derive_note_memberships(graph, canonical['source_packets'])
    if memberships != expected_notes:
        raise ValueError('saved memberships differ from the graph and source masks')

    source_bytes = Path(source_path).read_bytes()
    originals = {}
    for note in json.loads(source_bytes)['notes']:
        if note['note_id'] in originals:
            raise ValueError('source repeats a note ID')
        originals[note['note_id']] = note['text']
    short_ids = {}
    for vector in read(mapping_path)['vectors']:
        note, short = vector['note_id'], vector['note_short_id']
        if not isinstance(short, str) or not short.strip():
            raise ValueError('nonempty source note short IDs required')
        if note in short_ids and short_ids[note] != short:
            raise ValueError('conflicting short IDs for the same note')
        short_ids[note] = short
    if len(set(short_ids.values())) != len(short_ids):
        raise ValueError('different notes cannot share a short ID')

    by_id = {node['group']: node for node in memberships['nodes']}
    if 'root' in by_id:
        raise ValueError('source category conflicts with navigation root ID')
    children = {key: [] for key in by_id}
    parents = {key: [] for key in by_id}
    for edge in graph['transitive_reduced_edges']:
        children[edge['a_id']].append(edge['b_id'])
        parents[edge['b_id']].append(edge['a_id'])

    all_notes = set()
    for node in by_id.values():
        for mask in node['matched_instances']:
            note = mask['note_id']
            if note not in short_ids or originals.get(note) != mask['text']:
                raise ValueError('mask must match a complete original note and its short ID')
            all_notes.add(note)

    def masks_for(groups):
        masks = {}
        for key in groups:
            for mask in by_id[key]['matched_instances']:
                masks.setdefault(short_ids[mask['note_id']], set()).update(
                    tuple(span) for span in mask['byte_spans'])
        return {note: sorted(spans) for note, spans in sorted(masks.items())}

    nodes = [dict(node_id='root', label='All notes', children=graph['roots'], note_ids=[],
                  analysis='Navigation root only. Categories, connections and source memberships are unchanged. Shared categories are accessible under every saved parent.')]
    masks = {'root': masks_for(by_id)}
    for key, node in by_id.items():
        parent_names = ', '.join(f'{by_id[p]["title"]} [{p}]' for p in parents[key])
        nodes.append(dict(node_id=key, label=node['title'], children=children[key],
            note_ids=sorted(short_ids[n] for n in node['own_note_ids']),
            analysis=f'Saved native TRUE connections; not manually corrected. '
                     f'{node["own_note_count"]} notes directly represented; '
                     f'{node["recursive_note_count"]} including descendants. '
                     f'Parent categories: {parent_names or "none (shown under All notes)"}.'))
        masks[key] = masks_for([key, *graph['reachability'][key]])
        if set(masks[key]) != {short_ids[n] for n in node['recursive_note_ids']}:
            raise ValueError('category masks do not cover exactly its recursive notes')

    spec = dict(schema_version=2, hierarchy_id=hierarchy_id,
                source_sha256=hashlib.sha256(source_bytes).hexdigest(),
                root_node_id='root',
                notes=sorted((dict(note_id=n, note_short_id=short_ids[n]) for n in all_notes),
                             key=lambda n: n['note_short_id']),
                nodes=nodes, note_masks=masks)
    with output_path.open('x') as stream:
        json.dump(spec, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('canonical', 'graph', 'memberships', 'source', 'mapping', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--hierarchy-id', default='TRUE native answers')
    args = parser.parse_args()
    spec = export(args.canonical, args.graph, args.memberships, args.source, args.mapping,
                  args.output, hierarchy_id=args.hierarchy_id)
    print(f'{len(spec["nodes"])-1} categories plus navigation root; '
          f'{len(spec["notes"])} original notes. Saved to {args.output}')


if __name__ == '__main__':
    main()
