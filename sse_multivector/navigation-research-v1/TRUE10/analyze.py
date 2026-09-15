"""Build the reviewed-equivalence view and descriptive TRUE10 comparison artifacts.

This composes tested graph operations. It never changes scores, titles, or
non-equivalence links, and never treats unreviewed judgments as negative labels.
"""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

from hierarcaps_mask_probe import save_json, sha256
from true_category_graph import build_graph
from true_graph_equivalence import consolidate_verified_equivalents
from true_graph_notes import derive_note_memberships


def read(path):
    return json.loads(path.read_text())


def main():
    output = HERE / 'derived'
    if output.exists():
        raise ValueError('derived output exists; preserve prior analysis')
    plan = read(HERE / 'analysis-plan.json')
    source = ROOT / plan['source_packets']['path']
    review_path = HERE / plan['independent_semantic_review']['file']
    if sha256(source) != plan['source_packets']['sha256']:
        raise ValueError('source packets changed')
    if sha256(review_path) != plan['independent_semantic_review']['sha256']:
        raise ValueError('independent review changed')
    raw_completion = read(HERE / 'graph/completion.json')
    for name, field in [('scores.json', 'scores_sha256'), ('graph.json', 'graph_sha256')]:
        if sha256(HERE / 'graph' / name) != raw_completion[field]:
            raise ValueError('raw graph artifact changed: ' + name)
    raw_graph, raw_scores = read(HERE / 'graph/graph.json'), read(HERE / 'graph/scores.json')
    packets, titles = read(source), read(HERE / 'titles.json')
    raw_notes = derive_note_memberships(raw_graph, packets)
    canonical = consolidate_verified_equivalents(
        titles, raw_scores, packets, plan['main_equivalence_judgments'])
    graph = build_graph(canonical['titles'], canonical['scores'])
    notes = derive_note_memberships(graph, canonical['source_packets'])
    alias = {n['group']: n['group'] for n in raw_graph['nodes']}
    for approval in plan['main_equivalence_judgments']:
        alias.update({key: approval['canonical'] for key in approval['members']})
    # Folding approved equivalent IDs must preserve the raw paths to other classes.
    for old, canonical_id in alias.items():
        before = {alias[k] for k in raw_graph['reachability'][old]} - {canonical_id}
        after = set(graph['reachability'][canonical_id]) - {canonical_id}
        if before != after:
            raise ValueError('equivalence consolidation changed non-self reachability')
    if set(n for row in raw_notes['nodes'] for n in row['own_note_ids']) != set(
            n for row in notes['nodes'] for n in row['own_note_ids']):
        raise ValueError('equivalence consolidation lost source notes')

    by_score = {(r['a_id'], r['b_id']): r for r in raw_scores}
    by_notes = {n['group']: n for n in raw_notes['nodes']}
    judgments = {}
    comparisons = []
    for pair in read(review_path)['pairs']:
        for a, b, field in [(pair['a_id'], pair['b_id'], 'a_contains_b'),
                            (pair['b_id'], pair['a_id'], 'b_contains_a')]:
            key = (a, b)
            if key in judgments:
                raise ValueError('duplicate independent direction')
            judgments[key] = pair[field]
            row = by_score[key]
            if (row['a'], row['b']) != ((pair['a'], pair['b']) if field == 'a_contains_b'
                                       else (pair['b'], pair['a'])):
                raise ValueError('independent title mismatch')
            expected = pair[field]
            parent_available = set(by_notes[a]['recursive_note_ids'])
            child_own = set(by_notes[b]['own_note_ids'])
            comparisons.append(dict(
                a_id=a, b_id=b, a=row['a'], b=row['b'],
                independent_judgment=expected, reason=pair['reason'],
                native=row['predicted'], cutoff=row['threshold_predicted'], score=row['entailment_score'],
                raw_category_reachable=b in raw_graph['reachability'][a],
                same_verified_category=alias[a] == alias[b],
                child_own_notes=len(child_own),
                child_own_notes_already_available=len(child_own & parent_available),
                child_own_note_ids_not_available=sorted(child_own - parent_available),
                caveat='Reachability and note availability reflect the uncorrected graph, not semantic validation of every intervening edge.'))
    unreviewed_accepted = [row for row in raw_graph['raw_edges']
                          if (row['a_id'], row['b_id']) not in judgments]
    output.mkdir()
    for name, value in [('canonical.json', canonical), ('graph.json', graph),
                        ('raw-notes.json', raw_notes), ('notes.json', notes),
                        ('semantic-comparison.json', comparisons),
                        ('unreviewed-accepted.json', unreviewed_accepted)]:
        save_json(output / name, value)
    files = {p.name: sha256(p) for p in output.iterdir() if p.is_file()}
    save_json(output / 'completion.json', dict(experiment='TRUE10', files=files,
        inputs_sha256={str(p.relative_to(ROOT)): sha256(p) for p in
                      (Path(__file__), HERE / 'analysis-plan.json', review_path, source,
                       CODE / 'true_graph_notes.py', CODE / 'true_graph_equivalence.py',
                       CODE / 'true_category_graph.py')},
        raw_stats=raw_graph['stats'], canonical_stats=graph['stats'],
        note_stats=notes['stats'], independent_directions=len(comparisons),
        unreviewed_accepted_edges=len(unreviewed_accepted),
        equivalence_preserves_reachability_and_notes=True))
    print(json.dumps(dict(raw_graph=raw_graph['stats'], canonical_graph=graph['stats'],
                          notes=notes['stats'], independent_directions=len(comparisons),
                          unreviewed_accepted=len(unreviewed_accepted)), indent=2), flush=True)


if __name__ == '__main__':
    main()
