#!/usr/bin/env python3
"""Export before/after cycle-merge evidence for the existing read-only viewer.

Consumes a hierarchy_build package; no inference, approvals or graph edits.
"""
import argparse
from pathlib import Path

from hierarchy_build import _original_instances, name_merge, read, save
from true_graph_notes import derive_note_memberships


def marked_post(mask):
    """Highlight exact UTF-8 ranges, coalescing overlap only within this mask."""
    spans = []
    for start, end in sorted(mask['byte_spans']):
        if spans and start <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], end)
        else:
            spans.append([start, end])
    text = mask['text'].encode('utf-8')
    parts, cursor = [], 0
    for start, end in spans:
        parts.extend([text[cursor:start].decode(), '⟦', text[start:end].decode(), '⟧'])
        cursor = end
    return ''.join(parts) + text[cursor:].decode()


def group_masks(node):
    """Retain group boundaries; show identical same-post masks once with aliases."""
    masks = {}
    for selected in node['matched_instances']:
        for mask in _original_instances(selected):
            key = (mask['note_id'], tuple(map(tuple, mask['byte_spans'])))
            if key not in masks:
                masks[key] = (mask, [])
            if mask['instance'] not in masks[key][1]:
                masks[key][1].append(mask['instance'])
    return list(masks.values())


def build_review(package, decisions=None):
    package = Path(package)
    merged = read(package/'provenance.json')['merge']
    named = read(package/'named-graph.json')
    # Replay the production stage: never explain stale or edited derived links.
    if named != name_merge(merged, named['naming_report']):
        raise ValueError('named graph differs from its saved merge and naming evidence')
    original = {n['group']: n for n in derive_note_memberships(
        merged['raw_graph'], merged['source']['source_packets'])['nodes']}
    nodes = {n['group']: n for n in named['graph']['nodes']}
    memberships = {n['group']: n for n in named['memberships']['nodes']}
    mapping = merged['member_to_group']
    # Imported user decisions label the review; they never alter the graph.
    if decisions is not None and (not isinstance(decisions, dict)
            or set(decisions) != {'decisions'} or not isinstance(decisions['decisions'], list)):
        raise ValueError('expected a decisions list')
    known = {}
    merge_members = {tuple(sorted(n['source_group_ids'])) for n in nodes.values()
                     if sum(g == n['group'] for g in mapping.values()) > 1}
    for decision in (decisions or {}).get('decisions', []):
        if not isinstance(decision, dict):
            raise ValueError('expected a user decision object')
        members = decision.get('members', [])
        if (not isinstance(members, list) or not all(isinstance(m, str) for m in members)
                or len(set(members)) != len(members)):
            raise ValueError('decision members must be distinct node IDs')
        key = tuple(sorted(members))
        if (key not in merge_members or key in known
                or decision.get('decision') not in ('keep_separate', 'merge')
                or not isinstance(decision.get('source'), str) or not decision['source'].strip()):
            raise ValueError('decision must match one saved merge and cite the user decision')
        known[key] = decision
    scores = merged['source']['scores']
    accepted = {r['id'] for r in merged['raw_graph']['raw_edges']}
    notes = []
    for group, after in nodes.items():
        members = sorted(m for m, destination in mapping.items() if destination == group)
        if len(members) < 2:
            continue
        labels = {m: f'Group {i}' for i, m in enumerate(members, 1)}

        def reference(member):
            if member in labels:
                return labels[member]
            title = original[member]['title']
            peers = sorted(m for m in original if mapping[m] == mapping[member]
                           and original[m]['title'] == title)
            suffix = f' (group {peers.index(member)+1} of {len(peers)})' if len(peers) > 1 else ''
            return '“' + title + '”' + suffix

        before, posts = [], []
        for member in members:
            node = original[member]
            masks = group_masks(node)
            heading = f'{labels[member]} — {node["title"]}'
            summary = f'{len(masks)} masks · {node["own_note_count"]} directly represented posts'
            before.extend([heading, summary])
            posts.extend([heading, summary])
            for mask, ids in masks:
                identity = ', '.join(ids)
                before.append(identity + ': ' + ' '.join('⟦' + f + '⟧' for f in mask['fragments']))
                posts.extend([identity, marked_post(mask), ''])
            before.append('')
            posts.append('')

        counts = memberships[group]
        output = [after['title'],
                  f'{len(members)} separate groups → 1 node',
                  f'{counts["own_note_count"]} directly represented posts; '
                  f'{counts["recursive_note_count"]} including descendants.', '',
                  'Question: redundant distinction removed, or useful distinction lost?', '',
                  'The new title names the combined masks. It does not justify the merge.', '',
                  'Links after merging (indirect links omitted):']
        for heading, side, other in [('Parents', 'b_id', 'a_id'), ('Children', 'a_id', 'b_id')]:
            output.append(heading)
            edges = [e for e in named['graph']['transitive_reduced_edges'] if e[side] == group]
            if not edges:
                output.append('  None')
            for edge in edges:
                output.append('  ' + nodes[edge[other]]['title'])
                # Both Yes contributors and conflicting direct No answers remain visible.
                for row in sorted(scores, key=lambda r: (r['a_id'], r['b_id'])):
                    if (mapping[row['a_id']], mapping[row['b_id']]) == (edge['a_id'], edge['b_id']):
                        answer = 'Yes' if row['id'] in accepted else 'No'
                        output.append(f'    {reference(row["a_id"])} contains '
                                      f'{reference(row["b_id"])}: {answer}')
            output.append('')
        output.extend(['An accepted link from any member survives the merge, even if another member said No.',
                       'The browser may also hide equal-post navigation steps; this review shows the saved graph links.',
                       'Read-only: no merge is approved or reversed here.'])

        internal = sorted((r for r in scores if r['a_id'] in labels and r['b_id'] in labels),
                          key=lambda r: (r['a_id'], r['b_id']))
        evidence = [f'{labels[m]}: {original[m]["title"]}' for m in members] + ['']
        evidence += [f'{labels[r["a_id"]]} contains {labels[r["b_id"]]}: '
                     + ('Yes' if r['id'] in accepted else 'No') for r in internal]
        evidence.extend(['', 'Rule being tested: every group can reach every other through Yes links, '
                         'so merge them. This does not prove they mean the same thing.',
                         'TRUE saw the original titles, not the masks or the new combined title.',
                         'Native generated 1 = Yes; 0 = No. No score cutoff.', '', 'Exact saved TRUE inputs:'])
        for row in internal:
            evidence.extend([f'{labels[row["a_id"]]} contains {labels[row["b_id"]]}',
                             row['model_input'], 'Generated: ' + row['generated_text'], ''])
        decision = known.get(tuple(sorted(after['source_group_ids'])))
        status = 'Not yet decided.'
        if decision:
            status = 'Known decision: ' + ('Keep separate.' if decision['decision'] == 'keep_separate' else 'Merge.')
            evidence.extend(['Prior user decision: ' + status, decision['source']])
        summary = ['We merged these groups:', '']
        summary += [f'  {i}. {original[m]["title"]}' for i, m in enumerate(members, 1)]
        summary += ['', 'Into one node: ' + after['title'], '', 'Should they stay separate?', '', status]
        notes.append(dict(id=f'M{len(notes)+1:02}',
                          title=' + '.join(original[m]['title'] for m in members) + ' → ' + after['title'],
                          text='\n'.join(before), model_input='\n'.join(posts),
                          summary='\n'.join(summary),
                          results=[dict(model='Saved merge', output='\n'.join(output), comment='\n'.join(evidence))]))
    if not notes:
        raise ValueError('no cycle merges in this package')
    return dict(schema_version=1, title='Merge review · before / after',
                labels=dict(source='Before · separate groups', alternate_source='Full posts',
                            output='After · merged node', comment='TRUE answers · why merged',
                            item='Merge', variant='Result'), notes=notes)


def export_review(package, output, decisions=None):
    review = build_review(package, decisions)
    save(Path(output), review)
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--decisions', type=Path, help='saved user decisions; display only')
    args = parser.parse_args()
    try:
        review = export_review(args.package, args.output, read(args.decisions) if args.decisions else None)
        print(f'Saved {len(review["notes"])} merges for read-only review: {args.output}')
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
