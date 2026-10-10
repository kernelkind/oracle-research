"""Offline comparison selection on validated historical canonical snapshots.

Saved answers are withheld until their candidate is selected. No semantic gold,
new model outputs, placements, or changed construction histories are produced.
Text retrieval is a small-corpus reference, not a production search index.
"""
from collections import Counter
from copy import deepcopy
from graphlib import CycleError
import math
import re

try:
    from . import canonical_trial as trial
except ImportError:
    import canonical_trial as trial


POSITIVE = {'equivalent', 'canonical_contains_local', 'local_contains_canonical'}
_WORDS = re.compile(r'\w+', re.UNICODE)
_STOP = frozenset('a an and as at be by for from in is it of on or that the their '
                  'these this to used using was were which with'.split())


def _features(text):
    words = [w for w in _WORDS.findall(text.casefold()) if w not in _STOP]
    return Counter(words + [' '.join(pair) for pair in zip(words, words[1:])])


def _ranking(step):
    """Rank only original headings and fixed meanings, without future answers."""
    nodes = {n['id']: n for n in step['before']}
    ids = [a['id'] for a in step['answers']]
    local = step['local_input']
    heading = local['entry']['subject']
    query = _features(heading + ' ' + heading + ' ' + step['selected_meaning'])
    documents = {k: _features(nodes[k]['subject'] + ' ' + nodes[k]['subject']
                              + ' ' + nodes[k]['meaning']) for k in ids}
    frequencies = Counter(word for words in documents.values() for word in words)
    idf = {word: math.log((1 + len(ids)) / (1 + frequencies[word])) + 1
           for word in set(query).union(frequencies)}

    def vector(words):
        row = {word: (1 + math.log(count)) * idf[word] for word, count in words.items()}
        norm = math.sqrt(sum(value * value for value in row.values())) or 1
        return {word: value / norm for word, value in row.items()}

    q = vector(query)
    scores = {k: sum(q.get(word, 0) * value for word, value in vector(words).items())
              for k, words in documents.items()}
    return sorted(ids, key=lambda k: (-scores[k], k)), scores


def _label(bits):
    if any(len(values) != 1 for values in bits):
        return None
    canonical, local = (next(iter(values)) for values in bits)
    return ('equivalent' if canonical and local else 'canonical_contains_local'
            if canonical else 'local_contains_canonical' if local else 'neither')


def _select(step, ranking, *, limit=None, closure=False, structure_first=False):
    nodes = {n['id']: n for n in step['before']}
    ancestors = trial._ancestors(step['before'])
    descendants = {k: {q for q in nodes if k in ancestors[q]} for k in nodes}
    answers = {a['id']: a for a in step['answers']}
    bits = {k: [set(), set()] for k in nodes}
    facts = {k: [{}, {}] for k in nodes}
    asked, unresolved, conflicts = [], [], []

    def put(node, direction, value, source):
        if not closure:
            return
        old = bits[node][direction]
        if (not value) in old:
            conflicts.append(dict(node=node, direction=('canonical_contains_local'
                if direction == 0 else 'local_contains_canonical'),
                sources=sorted(set(facts[node][direction].values()) | {source})))
        old.add(value)
        facts[node][direction].setdefault(value, source)

    positions = {k: i for i, k in enumerate(ranking)}
    remaining = set(ranking)
    mapped = step.get('mapped_parent')
    while remaining and (limit is None or len(asked) < limit):
        candidates = [k for k in remaining if not closure or _label(bits[k]) is None]
        if not candidates:
            break
        if mapped in candidates:
            selected = mapped
        elif structure_first:
            # Structural priority uses graph reachability, never saved labels.
            selected = min(candidates, key=lambda k: (
                -sum(not bits[q][0] for q in descendants[k] if q in answers)
                -sum(not bits[q][1] for q in ancestors[k] if q in answers),
                positions[k]))
        else:
            selected = min(candidates, key=positions.get)
        remaining.remove(selected)
        asked.append(selected)
        answer = answers[selected]
        label = (answer.get('output') or {}).get('relation')
        if answer['status'] != 'valid' or label == 'uncertain':
            unresolved.append(selected)
            continue
        values = (label in {'equivalent', 'canonical_contains_local'},
                  label in {'equivalent', 'local_contains_canonical'})
        for direction, value in enumerate(values):
            put(selected, direction, value, selected)
            if not closure:
                continue
            others = (ancestors[selected] if value else descendants[selected]) if direction == 0 \
                else (descendants[selected] if value else ancestors[selected])
            for other in others:
                put(other, direction, value, selected)
        if closure and label == 'equivalent':
            # Existing strict edges rule out equality with proper ancestors/descendants.
            for other in ancestors[selected]:
                put(other, 1, False, selected)
            for other in descendants[selected]:
                put(other, 0, False, selected)

    inferred = {k: dict(relation=_label(bits[k]),
                       sources=sorted(set(source for row in facts[k] for source in row.values())))
                for k in answers if k not in asked and closure and _label(bits[k]) is not None}
    return dict(asked=asked, inferred=inferred, unresolved=unresolved, conflicts=conflicts)


def _proposal_guard(step, selected, history):
    """Apply existing reachability guards to a hypothetical sparse proposal.

    This is a frozen-step diagnostic. Its graph is discarded; later steps retain
    their original inputs. History contains only that profile's queried receipts.
    """
    answers = {a['id']: a for a in step['answers']}
    labels = {k: answers[k]['output']['relation'] for k in selected['asked']
              if answers[k]['status'] == 'valid'}
    labels.update({k: v['relation'] for k, v in selected['inferred'].items()})
    if selected['unresolved']:
        return 'unresolved_selected_answer'
    mapped = step.get('mapped_parent')
    if mapped is not None and labels.get(mapped) not in {'canonical_contains_local', 'equivalent'}:
        return 'mapped_parent'
    equivalents = [k for k, value in labels.items() if value == 'equivalent']
    if len(equivalents) > 1:
        return 'multiple_equivalents'
    target = equivalents[0] if equivalents else f"C{step['index'] + 1:03}"
    nodes = deepcopy(step['before'])
    by_id = {node['id']: node for node in nodes}
    if target not in by_id:
        node = dict(id=target, subject=step['local_input']['entry']['subject'],
                    meaning=step['selected_meaning'], entries=[step['local']], parents=[])
        nodes.append(node)
        by_id[target] = node
    for identifier, relation in labels.items():
        if relation == 'canonical_contains_local':
            by_id[target]['parents'] = sorted(set(by_id[target]['parents']) | {identifier})
        elif relation == 'local_contains_canonical':
            by_id[identifier]['parents'] = sorted(set(by_id[identifier]['parents']) | {target})
    try:
        ancestors = trial._ancestors(nodes)
    except CycleError:
        return 'cycle'
    for identifier, expected in labels.items():
        actual = ('equivalent' if identifier == target else
                  'canonical_contains_local' if identifier in ancestors[target] else
                  'local_contains_canonical' if target in ancestors[identifier] else 'neither')
        if actual != expected:
            return 'incoming_graph_contradiction'
    if trial._settled_relation_contradiction(
            dict(nodes=step['before'], steps=history), target, ancestors, equivalent=bool(equivalents)):
        return 'settled_relation_contradiction'
    return None


def _profile(steps, *, limit=None, closure=False, structure_first=False, menu_nodes=None):
    totals = Counter()
    evidence, history = [], []
    recovered_edges, recovered_equivalences = set(), set()
    for step in steps:
        if step['adapter'] != 'hierarchy_node_pairs':
            history.append(step)
            continue
        ranking, scores = _ranking(step)
        selection = _select(step, ranking, limit=limit, closure=closure,
                            structure_first=structure_first)
        answers = {a['id']: a for a in step['answers']}
        observed = {k: (a.get('output') or {}).get('relation') for k, a in answers.items()}
        positive = {k for k in answers if answers[k]['status'] == 'valid' and observed[k] in POSITIVE}
        recovered = set(selection['asked']) & positive
        recovered |= {k for k, v in selection['inferred'].items()
                      if k in positive and v['relation'] == observed[k]}
        disagreements = [dict(id=k, inferred=v['relation'], observed=observed[k], sources=v['sources'])
                         for k, v in selection['inferred'].items()
                         if answers[k]['status'] == 'valid' and observed[k] != v['relation']]
        guard = _proposal_guard(step, selection, history)
        hidden_hold = step['status'] == 'held' and guard is None
        totals.update(cases=len(answers), asked=len(selection['asked']),
                      prompt_bytes_queried=sum(step['prompt_bytes'][k] for k in selection['asked']),
                      inferred=len(selection['inferred']), positive=len(positive),
                      recovered_positive=len(recovered), missed_positive=len(positive - recovered),
                      inferred_disagreements=len(disagreements),
                      withheld_uncertain=sum(observed[k] == 'uncertain' for k in answers
                                             if k not in selection['asked']),
                      withheld_failed=sum(answers[k]['status'] != 'valid' for k in answers
                                          if k not in selection['asked']),
                      held_pair_steps=step['status'] == 'held',
                      held_pair_steps_without_guard=hidden_hold,
                      successful_pair_steps=step['status'] != 'held')
        if step['status'] != 'held':
            totals.update(applied_positive=len(positive), recovered_applied_positive=len(recovered),
                          changed_successful_proposal=guard is not None or recovered != positive)
            target = step['canonical_id']
            for k in recovered:
                if observed[k] == 'canonical_contains_local':
                    recovered_edges.add((k, target))
                elif observed[k] == 'local_contains_canonical':
                    recovered_edges.add((target, k))
                else:
                    recovered_equivalences.add((step['local']['note_id'], step['local']['number']))
        evidence.append(dict(index=step['index'], local=step['local'], status=step['status'],
            mapped_parent=step.get('mapped_parent'), asked=selection['asked'],
            prompt_bytes_queried=sum(step['prompt_bytes'][k] for k in selection['asked']),
            inferred=selection['inferred'], conflicts=selection['conflicts'],
            missed_positive=sorted(positive - recovered), inferred_disagreements=disagreements,
            observed_hold_reason=step.get('reason') if step['status'] == 'held' else None,
            frozen_proposal_guard=guard, observed_hold_without_guard=hidden_hold,
            ranking_scores={k: scores[k] for k in selection['asked']}))
        # Earlier unasked original receipts must not protect later proposals.
        history.append({**step, 'answers': [a for a in step['answers'] if a['id'] in selection['asked']]})

    result = dict(limit=limit, transitive_deductions=closure,
                  structural_priority=structure_first, totals=dict(totals), steps=evidence)
    result['comparisons_avoided'] = totals['cases'] - totals['asked']
    result['positive_recall'] = totals['recovered_positive'] / totals['positive'] if totals['positive'] else None
    if menu_nodes is not None:
        original_equivalences = {(st['local']['note_id'], st['local']['number']) for st in steps
                                 if st['status'] == 'equivalent'}
        parents = {node['id']: set() for node in menu_nodes}
        # Retain all historical canonical IDs for path proofs, including omitted menu nodes.
        for st in steps:
            if st['canonical_id'] is not None:
                parents.setdefault(st['canonical_id'], set())
        for parent, child in recovered_edges:
            parents.setdefault(child, set()).add(parent)
            parents.setdefault(parent, set())
        proof_nodes = [dict(id=k, parents=sorted(v)) for k, v in parents.items()]
        ancestors = trial._ancestors(proof_nodes)
        missing_edges = [[parent, node['id']] for node in menu_nodes for parent in node['parents']
                         if parent not in ancestors[node['id']]]
        missing_support = [dict(node=node['id'], local=entry) for node in menu_nodes for entry in node['entries']
                           if (entry['note_id'], entry['number']) in original_equivalences
                           and (entry['note_id'], entry['number']) not in recovered_equivalences]
        result['historical_menu_witnesses'] = dict(
            edges=sum(len(node['parents']) for node in menu_nodes),
            missing_edge_paths=missing_edges, missing_equivalent_support=missing_support,
            navigation='unchanged historical menu; counterfactual construction not generated')
    return result


def evaluate_snapshots(steps, candidate_limits, *, menu_nodes=None):
    """Compare bounded text selection and conditional graph inference offline."""
    baseline = _profile(steps, menu_nodes=menu_nodes)
    profiles = [dict(id='graph-closure', **_profile(
        steps, closure=True, structure_first=True, menu_nodes=menu_nodes))]
    for limit in candidate_limits:
        for closure in (False, True):
            profiles.append(dict(id=f'text-{limit}' + ('-closure' if closure else ''),
                **_profile(steps, limit=limit, closure=closure, menu_nodes=menu_nodes)))
    return dict(
        method=dict(ranking='TF-IDF cosine of words and adjacent word pairs; heading doubled',
                    required_candidate='mapped original parent when present',
                    ranking_evidence='own original heading and fixed meaning; no saved labels or future nodes',
                    retrieval='exact scan on each small historical snapshot; not a production index'),
        baseline=baseline, profiles=profiles,
        qualifications=[
            'These are original frozen-step measurements, not regenerated hierarchies.',
            'Saved labels are execution witnesses, not independently validated semantic gold.',
            'Transitive deductions require semantically valid fixed-meaning canonical edges.',
            'Unselected, unresolved relationships remain unknown; omission never means neither.',
            'Changed proposals invalidate using later historical answers for a real counterfactual build.',
            'Sparse-history guards use only queried original receipts, not withheld or inferred receipts.',
            'Menu measures recoverability of historical edge/support witnesses, not new navigation quality.',
            'Prompt bytes are UTF-8 rendered-input sizes, not token counts or billed usage.',
            'Comparisons avoided are case counts, not newly saved paid attempts or measured wall time.'])
