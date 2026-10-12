"""Receipt-bound consistency checks for isolated fixed-meaning comparisons.

This consumes validated native reports, never assigns semantic gold or changes
a hierarchy. Each orientation is checked separately; unqueried relationships
are unknown, and displayed canonical branches are not pooled with isolated pairs.
Conflict witnesses can overlap; their counts are not independent semantic errors.
"""
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path


REVERSED = {'equivalent': 'equivalent', 'neither': 'neither',
            'local_contains_canonical': 'canonical_contains_local',
            'canonical_contains_local': 'local_contains_canonical',
            'A_contains_B': 'B_contains_A', 'B_contains_A': 'A_contains_B'}
VERSION = 'hierarchy-node-pair-consistency-v4'


def _reference(case):
    parsed = case.get('parsed') or {}
    reference = {'case_id': case['id'], 'input_sha256': case['input_sha256'],
            'status': case['status'], 'receipt': case.get('receipt'),
            'relation': parsed.get('relation'), 'reason': parsed.get('reason')}
    issue = _unresolved_reason(case)
    if issue:
        reference['unresolved_reason'] = issue
    return reference


def _endpoint(producer, meaning):
    if (not isinstance(producer, dict) or not isinstance(meaning, str)
            or not meaning.strip() or not producer.get('experiment')
            or not producer.get('case') or not producer.get('receipt')):
        return None
    identity = {key: producer[key] for key in ('experiment', 'case', 'receipt')}
    identity['meaning'] = meaning
    return hashlib.sha256(json.dumps(identity, sort_keys=True,
        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def _saved_comparison_endpoints(evidence, payload):
    """Bind each original role to its native receipt, without cross-source joins."""
    saved = evidence.get('saved_comparison')
    if not isinstance(saved, dict):
        return None
    selection, original, receipt = (saved.get(key) for key in
                                     ('selection', 'original_input', 'receipt'))
    if (not isinstance(selection, dict) or type(selection.get('reverse')) is not bool
            or not isinstance(original, dict) or set(original) != {'A', 'B'}
            or not isinstance(receipt, dict) or not receipt.get('results_path')
            or not receipt.get('record_sha256') or not saved.get('experiment')
            or not selection.get('case_id') or not saved.get('input_sha256')):
        return None
    for node in original.values():
        if (not isinstance(node, dict) or set(node) != {'subject', 'meaning'}
                or any(not isinstance(value, str) or not value.strip() for value in node.values())):
            return None
    reverse = selection['reverse']
    expected = {'A': original['B'], 'B': original['A']} if reverse else original
    role = 'isolated-reverse' if reverse else 'isolated-forward'
    if payload != expected or evidence.get('review', {}).get('comparison_role') != role:
        return None
    endpoints = []
    for role in ('A', 'B'):
        identity = dict(experiment=saved['experiment'], case=selection['case_id'],
                        receipt=receipt, original_role=role, node=original[role])
        endpoints.append(hashlib.sha256(json.dumps(identity, sort_keys=True,
            ensure_ascii=False, separators=(',', ':')).encode()).hexdigest())
    return tuple(endpoints[::-1] if reverse else endpoints)


def _unresolved_reason(case):
    if case['status'] != 'valid':
        return case['status']
    if not case.get('receipt'):
        return 'missing_compare_receipt'
    parsed = case.get('parsed') or {}
    payload = json.loads(case['inputs']['INPUT_JSON'])
    if set(payload) != {'A', 'B'} and parsed.get('meaning') != payload['local'].get('meaning'):
        return 'returned_local_meaning_differs'
    if parsed.get('relation') not in REVERSED:
        return parsed.get('relation') or 'missing_relation'
    return None


def _settled(case):
    return _unresolved_reason(case) is None


def _direction(rows):
    facts = {case['id']: (case, local, canonical)
             for case, local, canonical in rows if _settled(case)}
    adjacency = defaultdict(list)
    for identifier, (case, local, canonical) in facts.items():
        relation = case['parsed']['relation']
        if local == canonical:
            continue
        if relation == 'equivalent':
            adjacency[local].append((canonical, identifier, False))
            adjacency[canonical].append((local, identifier, False))
        elif relation != 'neither':
            parent, child = ((local, canonical) if relation in ('local_contains_canonical', 'A_contains_B')
                             else (canonical, local))
            adjacency[parent].append((child, identifier, True))
    for edges in adjacency.values():
        edges.sort()

    def path(start, end, *, strict=False):
        initial = (start, False)
        pending, previous = deque([initial]), {initial: None}
        while pending:
            node, has_strict = state = pending.popleft()
            if node == end and previous[state] is not None and (has_strict or not strict):
                witness = []
                while previous[state] is not None:
                    state, identifier = previous[state]
                    witness.append(identifier)
                return witness[::-1]
            for child, identifier, is_strict in adjacency.get(node, ()):
                next_state = (child, has_strict or is_strict)
                if next_state not in previous:
                    previous[next_state] = (state, identifier)
                    pending.append(next_state)
        return None

    conflicts = []
    for identifier, (case, local, canonical) in facts.items():
        relation = case['parsed']['relation']
        if local == canonical:
            if relation != 'equivalent':
                conflicts.append({'kind': 'identity_conflict', 'comparison': _reference(case),
                                  'witness': [_reference(case)]})
            continue
        witness = None
        if relation == 'neither':
            witness = path(local, canonical) or path(canonical, local)
            kind = ('equivalence_substitution_conflict' if witness and any(
                facts[key][0]['parsed']['relation'] == 'equivalent' for key in witness)
                else 'transitivity_conflict')
        elif relation == 'equivalent':
            witness = path(local, canonical, strict=True) or path(canonical, local, strict=True)
            kind = 'equivalence_conflict'
        else:
            parent, child = ((local, canonical) if relation in ('local_contains_canonical', 'A_contains_B')
                             else (canonical, local))
            witness, kind = path(child, parent), 'cycle_conflict'
        if witness:
            conflicts.append({'kind': kind, 'comparison': _reference(case),
                'witness': [_reference(facts[key][0])
                            for key in dict.fromkeys([*witness, identifier])]})
    return {'settled_cases': len(facts), 'conflicts': conflicts,
            'unresolved_cases': [_reference(case) for case, _, _ in rows if not _settled(case)]}


def summarize(cases):
    """Check producer-bound isolated pairs in a validated shared-runner report."""
    pairs, directions, endpoints, skipped = {}, {'forward': [], 'reverse': []}, set(), []
    for case in cases:
        payload = json.loads(case['inputs']['INPUT_JSON'])
        evidence = case.get('evidence', {})
        symmetric = set(payload) == {'A', 'B'}
        local, canonical = ((payload['A'], payload['B']) if symmetric else
                            (payload['local'], payload['canonical']))
        if symmetric:
            original_canonical = evidence.get('unprojected_input', evidence.get('source_input', {})).get(
                'canonical', {})
        else:
            original_canonical = (evidence.get('unprojected_input', {}).get('canonical', {})
                                  if evidence.get('input_view') == 'fixed_meanings' else canonical)
        metadata = evidence.get('review', {})
        role = metadata.get('comparison_role')
        pair_id = metadata.get('reversal_pair')
        if evidence.get('input_view') == 'meanings':
            reason = 'meaning_only_projection'
        elif not symmetric and (any(canonical.get(key) for key in ('parents', 'ancestors', 'descendants'))
                                or len(original_canonical.get('entries', [])) != 1):
            reason = 'canonical_branch_snapshot'
        elif role not in ('isolated-forward', 'isolated-reverse') or not pair_id:
            reason = 'missing_isolated_pair_metadata'
        elif 'saved_comparison' in evidence:
            saved_endpoints = _saved_comparison_endpoints(evidence, payload) if symmetric else None
            if saved_endpoints:
                local, other = saved_endpoints
                reason = None
            else:
                reason = 'invalid_saved_comparison_binding'
        else:
            local = _endpoint(evidence.get('local_meaning_from'), local.get('meaning'))
            canonical_id = original_canonical.get('id') if symmetric else canonical['id']
            other = _endpoint(evidence.get('canonical_meaning_from', {}).get(canonical_id),
                              canonical.get('meaning'))
            reason = None if local and other else 'missing_fixed_meaning_producer_receipt'
        if reason:
            skipped.append({'case_id': case['id'], 'reason': reason})
            continue
        direction = role.removeprefix('isolated-')
        if direction in pairs.setdefault(pair_id, {}):
            raise ValueError('duplicate isolated comparison orientation: ' + str(pair_id))
        pairs[pair_id][direction] = (case, local, other)
        directions[direction].append((case, local, other))
        endpoints.update((local, other))

    complete_pairs, conflicts, unresolved = 0, [], []
    request_pairs = defaultdict(list)
    for pair_id, rows in pairs.items():
        if set(rows) == {'forward', 'reverse'}:
            forward, reverse = rows['forward'], rows['reverse']
            if forward[1:] != reverse[1:][::-1]:
                raise ValueError('isolated reversal endpoint identities differ: ' + str(pair_id))
        if set(rows) != {'forward', 'reverse'} or not all(_settled(row[0]) for row in rows.values()):
            unresolved.append({'pair_id': pair_id,
                'missing_directions': sorted({'forward', 'reverse'} - rows.keys()),
                'cases': [_reference(rows[direction][0]) for direction in sorted(rows)]})
            continue
        complete_pairs += 1
        request_identity = tuple(sorted(row[0]['input_sha256'] for row in rows.values()))
        request_pairs[request_identity].append({'pair_id': pair_id,
            'cases': [_reference(rows[direction][0]) for direction in sorted(rows)]})
        if REVERSED[forward[0]['parsed']['relation']] != reverse[0]['parsed']['relation']:
            conflicts.append({'pair_id': pair_id, 'forward': _reference(forward[0]),
                              'reverse': _reference(reverse[0])})
    return {'schema_version': 1,
            'implementation': {'version': VERSION,
                               'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'eligible_cases': sum(map(len, directions.values())),
            'endpoints': len(endpoints), 'skipped_cases': skipped,
            'complete': bool(pairs) and not unresolved and not skipped,
            'reversals': {'complete_pairs': complete_pairs,
                          'unique_complete_request_pairs': len(request_pairs),
                          'duplicate_request_pair_witnesses': [
                              {'pair_ids': sorted(row['pair_id'] for row in group),
                               'witnesses': group}
                              for group in request_pairs.values() if len(group) > 1],
                          'conflicts': conflicts,
                          'unresolved_pairs': unresolved},
            'directions': {direction: _direction(rows) for direction, rows in directions.items()},
            'qualification': 'Checks supplied settled relationships between exact producer-bound meanings '
                             'or receipt-bound saved comparison roles. Saved comparison endpoints stay scoped '
                             'to the original receipt and role; coincident wording across original cases is '
                             'not joined or certified as a complete chain. Missing comparisons are unknown; '
                             'consistency is not semantic accuracy. '
                             'Conflict witnesses may overlap and are not independent semantic errors.'}
