"""Build a category graph from complete, frozen TRUE directed outputs.

An edge A -> B records that TRUE's score for A contains B exceeds 0.142.
Group IDs remain distinct, including equal titles. Native labels are retained
separately. Cycles are diagnostics, never evidence of semantic equivalence.
An explicit native mode instead selects the saved generated positive class.
"""
from copy import deepcopy
import math

from true_category_probe import model_input
from true_holdout_probe import THRESHOLD, threshold_decision


def prepare_inputs(titles, *, source_group_ids=None, consolidations=()):
    """Use all titles, optionally checking the complete upstream group inventory.

    Title judgments never remove groups. Only explicit, already-approved
    consolidations account for multiple source groups with one category.
    """
    groups = titles.get('groups') if isinstance(titles, dict) else None
    if not isinstance(groups, list) or not groups:
        raise ValueError('nonempty generated title groups required')
    by_id = {}
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError('generated title group object required')
        key, title = group.get('group'), group.get('title')
        if not isinstance(key, str) or not key.strip() or key in by_id:
            raise ValueError('nonempty unique generated title group IDs required')
        if not isinstance(title, str) or not title.strip():
            raise ValueError('nonempty exact generated titles required')
        by_id[key] = title
    if source_group_ids is not None:
        sources = set(source_group_ids)
        if len(sources) != len(source_group_ids) or not sources:
            raise ValueError('nonempty unique source group IDs required')
        represented = {key: key for key in sources}
        consolidated = set()
        for item in consolidations:
            canonical, members = item['canonical'], item['source_group_ids']
            if (canonical not in members or not members
                    or len(set(members)) != len(members)
                    or not set(members) <= sources or consolidated & set(members)):
                raise ValueError('invalid or overlapping explicit consolidation')
            consolidated.update(members)
            represented.update({key: canonical for key in members})
        expected = set(represented.values())
        missing, unexpected = expected - by_id.keys(), by_id.keys() - expected
        if missing or unexpected:
            raise ValueError(f'category inventory mismatch: missing {sorted(missing)}; '
                             f'unexpected {sorted(unexpected)}')
    elif consolidations:
        raise ValueError('consolidations require the source inventory')
    rows = []
    for a_id, a in by_id.items():
        for b_id, b in by_id.items():
            if a_id == b_id:
                continue
            row = dict(id=f'{a_id}-contains-{b_id}', a_id=a_id, b_id=b_id,
                       a=a, b=b, domain='generated-titles', format='topic')
            row['model_input'] = model_input(row, 'topic')
            rows.append(row)
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('generated pair IDs must be unique')
    return rows


def _validated_scores(inputs, scores):
    """Require one matching score and explicit native-output provenance per input."""
    if not isinstance(scores, list):
        raise ValueError('complete score row list required')
    expected = {row['id']: row for row in inputs}
    by_id = {}
    for row in scores:
        if not isinstance(row, dict):
            raise ValueError('score row object required')
        key = row.get('id')
        if not isinstance(key, str) or key not in expected:
            raise ValueError('known input pair ID required for every score')
        if key in by_id:
            raise ValueError('duplicate score pair: ' + key)
        for field, value in expected[key].items():
            if row.get(field) != value:
                raise ValueError(f'score does not match frozen input {key}: {field}')
        score = row.get('entailment_score')
        if (type(score) not in (int, float) or not math.isfinite(score)
                or not 0 <= score <= 1):
            raise ValueError('finite entailment probability required: ' + key)
        if row.get('threshold_predicted') is not threshold_decision(score):
            raise ValueError('score cutoff label does not match frozen threshold: ' + key)
        predicted = row.get('predicted')
        text, token_ids = row.get('generated_text'), row.get('generated_token_ids')
        terminated = row.get('eos_terminated')
        if ('predicted' not in row or (predicted is not None and type(predicted) is not bool)
                or not isinstance(text, str) or type(terminated) is not bool
                or not isinstance(token_ids, list) or len(token_ids) < 2
                or any(type(token) is not int or token < 0 for token in token_ids)):
            raise ValueError('complete native generation provenance required: ' + key)
        # The pinned TRUE release uses EOS 1. No EOS or a non-class string is
        # unresolved, not a native No; the score cutoff is a separate decision.
        if terminated is not (1 in token_ids[1:]):
            raise ValueError('native EOS flag disagrees with generated tokens: ' + key)
        native = {'0': False, '1': True}.get(text) if terminated else None
        if predicted is not native:
            raise ValueError('native label disagrees with complete generated output: ' + key)
        by_id[key] = row
    missing = expected.keys() - by_id.keys()
    if missing:
        raise ValueError(f'missing {len(missing)} ordered pair scores')
    return [by_id[row['id']] for row in inputs]


def _reachability(adjacency):
    """Positive-length reachability; a node reaches itself only through a cycle."""
    result = {}
    for source, children in adjacency.items():
        reached, pending = set(), list(children)
        while pending:
            node = pending.pop()
            if node not in reached:
                reached.add(node)
                pending.extend(adjacency[node] - reached)
        result[source] = reached
    return result


def build_graph(titles, scores, threshold=THRESHOLD, *, decision_rule='cutoff'):
    """Return lossless raw edges and graph diagnostics without semantic repairs.

    Nodes preserve the source group dictionaries, including note memberships.
    Edge rows retain all supplied score provenance. Reachability reports paths,
    not new TRUE decisions; reachable rejected pairs are exposed separately.
    SCCs describe only graph cycles, not interchangeable category meanings.
    Transitive reduction is returned only for an entirely acyclic raw graph.
    All output ordering follows source group/pair order, not score file order.
    Native mode uses the complete saved generated class, not a numerical cutoff;
    unresolved native outputs remain separate from rejected relationships.
    """
    if decision_rule not in ('cutoff', 'native'):
        raise ValueError('decision_rule must be cutoff or native')
    if type(threshold) not in (int, float) or threshold != THRESHOLD:
        raise ValueError('frozen threshold 0.142 required')
    inputs = prepare_inputs(titles)
    rows = _validated_scores(inputs, scores)
    nodes = titles['groups']
    ids = [node['group'] for node in nodes]
    field = 'threshold_predicted' if decision_rule == 'cutoff' else 'predicted'
    raw_edges = [row for row in rows if row[field] is True]
    adjacency = {key: set() for key in ids}
    parents = {key: set() for key in ids}
    by_pair = {}
    for row in raw_edges:
        a, b = row['a_id'], row['b_id']
        adjacency[a].add(b)
        parents[b].add(a)
        by_pair[a, b] = row
    reachable = _reachability(adjacency)

    # Full reachability is already required in the output. Its mutual relation
    # gives SCC membership directly, without a second graph traversal algorithm.
    components, assigned = [], set()
    for source in ids:
        if source in assigned:
            continue
        component = [key for key in ids if key == source
                     or (key in reachable[source] and source in reachable[key])]
        components.append(component)
        assigned.update(component)
    cycle_components = [component for component in components if len(component) > 1]
    component_index = {key: index for index, component in enumerate(components)
                       for key in component}
    cycle_edges = [row for row in raw_edges
                   if component_index[row['a_id']] == component_index[row['b_id']]]
    mutual = []
    for index, a in enumerate(ids):
        for b in ids[index + 1:]:
            if (a, b) in by_pair and (b, a) in by_pair:
                mutual.append(dict(a_id=a, b_id=b, a_contains_b=by_pair[a, b],
                                   b_contains_a=by_pair[b, a]))

    reduced = None
    if not cycle_components:
        # In a DAG, A -> B is redundant iff another child of A reaches B.
        # Removing precisely those edges preserves every path, without adding
        # edges or selecting one parent when multiple parents remain.
        reduced = [row for row in raw_edges if not any(
            child != row['b_id'] and row['b_id'] in reachable[child]
            for child in adjacency[row['a_id']])]
    roots = [key for key in ids if not parents[key]]
    unresolved = [row for row in rows if row['predicted'] is None]
    reachable_rejected = [row for row in rows if row[field] is False
                          and row['b_id'] in reachable[row['a_id']]]
    result = dict(
        threshold=THRESHOLD, threshold_rule='entailment_score > 0.142',
        nodes=nodes, raw_edges=raw_edges, roots=roots,
        strongly_connected_components=components, cycle_components=cycle_components,
        cycle_edges=cycle_edges, mutual_acceptance=mutual,
        transitive_reduction_status='blocked_by_cycles' if cycle_components else 'complete',
        transitive_reduced_edges=reduced,
        reachability={source: [key for key in ids if key in reachable[source]] for source in ids},
        reachable_rejected_pairs=reachable_rejected, unresolved_native_rows=unresolved,
        stats=dict(nodes=len(nodes), scored_ordered_pairs=len(rows), raw_edges=len(raw_edges),
                   roots=len(roots), strongly_connected_components=len(components),
                   cycle_components=len(cycle_components), cycle_edges=len(cycle_edges),
                   mutual_acceptance=len(mutual), native_unresolved=len(unresolved),
                   reachable_rejected_pairs=len(reachable_rejected),
                   transitive_reduced_edges=None if reduced is None else len(reduced)))
    if decision_rule == 'native':
        result.update(decision_rule='native', edge_rule='predicted is True',
                      threshold=None, threshold_rule=None)
    return deepcopy(result)
