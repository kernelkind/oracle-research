"""Export the uncorrected TRUE10 graph for inspection; no inference or repairs."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    graph = read('derived/graph.json')
    notes = read('derived/notes.json')['nodes']
    by_id = {n['group']: n for n in notes}
    comparisons = read('derived/semantic-comparison.json')
    reachable = set(graph['roots'])
    for root in graph['roots']:
        reachable.update(graph['reachability'][root])
    root_notes = {key for node in reachable for key in by_id[node]['own_note_ids']}
    all_notes = {key for node in notes for key in node['own_note_ids']}
    counts = {}
    for rule in ['native', 'cutoff']:
        counts[rule] = {name: dict(Counter(
            'Yes' if row[rule] is True else 'No' if row[rule] is False else 'unresolved'
            for row in comparisons if row['independent_judgment'] is expected))
            for name, expected in [('expected_yes', True), ('expected_no', False), ('uncertain', None)]}
    result = dict(experiment='TRUE10', status='Provisional graph; two non-equivalence cycles remain.',
        raw_stats=read('graph/graph.json')['stats'], canonical_stats=graph['stats'],
        source_masks=len([m for n in notes for m in n['matched_instances']]),
        source_notes=len(all_notes), root_reachable_categories=len(reachable),
        root_unreachable_categories=sorted(set(by_id) - reachable),
        root_reachable_notes=len(root_notes), root_unreachable_note_ids=sorted(all_notes-root_notes),
        root_caveat='Diagnostic of entering only through zero-parent nodes in this cyclic graph; not deletion of data or a deployed UI result.',
        independent_comparison=counts,
        comparison_caveat='Assistant judgments, not user-approved ground truth or general accuracy. Repeated categories/directions are dependent. All uncertain directions remain visible; unlisted pairs remain unjudged. Additional post-score review is recorded separately.',
        main_findings=[
            'Coffee connects to Coffee Bean Preparation, Having drunk coffee, and Appreciating Coffee for Its Flavour.',
            'Valid local paths include Food -> Food Preparation and Dining -> Cooking Times, and Food -> Tomatoes -> Breakfast foods made with tomatoes.',
            'Food consumption -> Food and Dishes with Toppings or Seasonings -> Prepared foods are incorrect reverse links, not equivalences. Both are native No but accepted by the fixed cutoff.',
            'Food consumption and Food each inherit 58 notes; Prepared foods and Dishes with Toppings or Seasonings each inherit 35. Identical inherited memberships here are consequences of cycles, not evidence of equivalence.',
            'Foods featuring meat or seafood still has no route to Steak; neither Steak source note is available there.',
            'Food Preparation and Dining has no route to Carrots as a food ingredient; one of its two notes is already available through other categories, the other is missing there.',
            'The missing Bitcoin -> Satoshis route does not lose those source notes under Bitcoin, because its existing masks already represent both notes.',
            'No non-equivalence links were repaired. Transitive reduction was withheld because the graph remains cyclic.'
        ],
        next_step_suggestion='Compare the native-answer graph with this fixed-cutoff graph using the saved outputs, without another model run. Both incorrect cycle-closing links are native No, but native answers also miss more independently judged valid links. Assess actual paths and missing notes rather than choose a rule from accuracy alone. Do not tune or adopt a replacement rule without approval.')
    (HERE / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    lines = ['# TRUE10 — Complete category connections', '',
        'This is the uncorrected graph after the two reviewed equivalence consolidations. It is not an acyclic hierarchy: two cycles remain. All 88 accepted connections are shown; no redundant links have been removed.', '',
        'A child listed here was accepted by score > 0.142. That is not a guarantee of semantic correctness. “Own notes” come from this category’s masks; “including descendants” also follows every accepted connection, including incorrect ones.', '',
        'Full original notes, exact masks and byte ranges: [notes.json](./derived/notes.json). Raw decisions and origins: [scores.json](./graph/scores.json).', '']
    for node in notes:
        key = node['group']
        incoming = [e for e in graph['raw_edges'] if e['b_id'] == key]
        outgoing = [e for e in graph['raw_edges'] if e['a_id'] == key]
        lines += [f'## {node["title"]} — {key}', '',
            f'Own notes: {node["own_note_count"]}. Including descendants: {node["recursive_note_count"]}.', '',
            'Parents: '+('; '.join(f'{e["a"]} ({e["a_id"]})' for e in incoming) or 'none')+'.', '', 'Accepted children:', '']
        lines += ([f'- {e["b"]} ({e["b_id"]}) — {e["entailment_score"]:.6f}' for e in outgoing] or ['- None.'])
        lines += ['', 'Source masks:', '']
        for mask in node['matched_instances']:
            lines.append('- '+mask['instance']+': '+' '.join('⟦'+f.replace('\n', '<br>')+'⟧' for f in mask['fragments']))
        lines.append('')
    (HERE / 'GRAPH.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
