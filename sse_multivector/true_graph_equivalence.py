"""Consolidate only explicitly reviewed, same-title TRUE10 equivalences.

The complete raw graph remains a separate artifact. This view removes approved
aliases, not arbitrary cycles, and selects existing score rows without combining
or repairing decisions. Equal titles alone never authorize consolidation.
"""
from copy import deepcopy

from true_category_graph import build_graph, prepare_inputs
from true_graph_notes import derive_note_memberships


def _approved_classes(groups, approvals):
    if not isinstance(approvals, list):
        raise ValueError('explicit equivalence approval list required')
    by_id = {group['group']: group for group in groups}
    assigned, classes = set(), []
    for approval in approvals:
        if not isinstance(approval, dict):
            raise ValueError('explicit equivalence approval object required')
        canonical, members = approval.get('canonical'), approval.get('members')
        reason = approval.get('reason')
        if (not isinstance(members, list) or len(members) < 2
                or any(not isinstance(member, str) or member not in by_id for member in members)
                or len(set(members)) != len(members)
                or not isinstance(canonical, str) or canonical not in members
                or assigned.intersection(members)):
            raise ValueError('disjoint known equivalence members and included canonical ID required')
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('explicit equivalence review reason required')
        title = by_id[canonical]['title']
        if (approval.get('title') != title
                or any(by_id[member]['title'] != title for member in members)):
            raise ValueError('reviewed equivalence requires the same exact title')
        # Preserve canonical instances first, then other groups in source order;
        # approval-list ordering must not reorder observed membership.
        ordered = [canonical] + [key for key in by_id if key in members and key != canonical]
        classes.append((approval, ordered))
        assigned.update(members)
    return classes


def _union_instances(groups):
    """Retain distinct masks, sharing an ID only for identical full payloads."""
    instances, contributors = {}, {}
    for group, rows in groups:
        for row in rows:
            key = row['instance']
            if key in instances and instances[key] != row:
                raise ValueError(f'conflicting instance payload: {key}')
            instances[key] = row
            contributors.setdefault(key, []).append(group)
    return list(instances.values()), contributors


def consolidate_verified_equivalents(titles, scores, source_packets, approvals):
    """Return canonical titles, scores, source packets, and review provenance.

    Approvals are disjoint objects with canonical, members, exact title, and a
    nonempty review reason. Every ordered distinct pair within each approved
    class must pass the frozen cutoff. External entailment scores, native labels,
    cutoff labels, and complete generated outputs must agree exactly with the
    existing canonical row, including rejected directions and other classes.

    Canonical group/packet positions and other payload fields remain unchanged.
    Instances are unioned by ID, canonical first, without deduplicating masks by
    note. Only current matched evidence enters the canonical packet; complete
    original groups/packets remain in consolidation provenance. Non-equivalent
    groups, packets, and score rows are retained unchanged. All mutable output
    payloads are independent of the inputs. No files or raw artifacts are edited.
    """
    raw_graph = build_graph(titles, scores)
    classes = _approved_classes(titles['groups'], approvals)
    memberships = derive_note_memberships(raw_graph, source_packets)
    by_pair = {(row['a_id'], row['b_id']): row for row in scores}
    ordered_scores = [by_pair[row['a_id'], row['b_id']] for row in prepare_inputs(titles)]
    canonical_ids = {group['group']: group['group'] for group in titles['groups']}
    for approval, members in classes:
        for a in members:
            canonical_ids[a] = approval['canonical']
            for b in members:
                if a != b and not by_pair[a, b]['threshold_predicted']:
                    raise ValueError(f'every distinct equivalence pair must be accepted: {a}/{b}')

    output_fields = ('entailment_score', 'threshold_predicted', 'predicted',
                     'generated_text', 'generated_token_ids', 'eos_terminated')
    score_contributors = {}
    for row in ordered_scores:
        a, b = canonical_ids[row['a_id']], canonical_ids[row['b_id']]
        if a == b:
            continue
        canonical = by_pair[a, b]
        if any(row[field] != canonical[field] for field in output_fields):
            raise ValueError(f'external equivalent score outputs disagree: {row["id"]}')
        score_contributors.setdefault(canonical['id'], []).append(row['id'])

    aliases = {key for key, canonical in canonical_ids.items() if key != canonical}
    retained_scores = [row for row in ordered_scores
                       if row['a_id'] not in aliases and row['b_id'] not in aliases]
    groups = {group['group']: group for group in titles['groups']}
    packets = {packet['packet']: packet for packet in source_packets['packets']}
    evidence = {node['group']: node['matched_instances'] for node in memberships['nodes']}
    replacements, packet_replacements, consolidations = {}, {}, []
    for approval, members in classes:
        canonical = approval['canonical']
        instances, contributors = _union_instances(
            [(key, groups[key]['instances']) for key in members])
        matched, evidence_contributors = _union_instances([(key, evidence[key]) for key in members])
        metadata = dict(source_group_ids=members, instance_contributors=contributors)
        replacements[canonical] = dict(groups[canonical], instances=instances, **metadata)
        packet_replacements[canonical] = dict(
            packets[canonical], instances=matched, source_group_ids=members,
            instance_contributors=evidence_contributors)
        class_aliases = set(members) - {canonical}
        consolidations.append(dict(
            canonical=canonical, title=groups[canonical]['title'], approval=approval,
            source_group_ids=members, instance_contributors=contributors,
            source_groups=[groups[key] for key in members],
            source_packets=[packets[key] for key in members],
            removed_score_ids=[row['id'] for row in ordered_scores
                               if row['a_id'] in class_aliases or row['b_id'] in class_aliases],
            score_contributors={row['id']: score_contributors[row['id']]
                                for row in retained_scores
                                if row['a_id'] == canonical or row['b_id'] == canonical}))

    return deepcopy(dict(
        titles=dict(titles, groups=[replacements.get(group['group'], group)
                                   for group in titles['groups'] if group['group'] not in aliases]),
        scores=retained_scores,
        source_packets=dict(source_packets, packets=[packet_replacements.get(packet['packet'], packet)
                            for packet in source_packets['packets'] if packet['packet'] not in aliases]),
        consolidations=consolidations))
