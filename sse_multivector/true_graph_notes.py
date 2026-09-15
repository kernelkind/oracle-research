"""Derive note availability from canonical TRUE10 nodes and frozen source masks.

Category reachability and note availability remain separate: an unreachable
category can have notes already present through a different reachable category.
This module neither changes graph edges nor infers category membership.
"""
from copy import deepcopy


def _matched_instance(canonical, source, group):
    instance = canonical.get('instance') if isinstance(canonical, dict) else None
    if not isinstance(instance, str) or not instance:
        raise ValueError(f'canonical instance ID required: {group}')
    matches = [row for row in source if isinstance(row, dict)
               and row.get('instance') == instance]
    if len(matches) != 1:
        raise ValueError(f'exactly one source instance required: {group}/{instance}')
    row = matches[0]
    fragments = canonical.get('fragments')
    if (not isinstance(fragments, list) or not fragments
            or any(not isinstance(fragment, str) or not fragment for fragment in fragments)
            or row.get('fragments') != fragments):
        raise ValueError(f'exact canonical fragments required: {group}/{instance}')
    if any(not isinstance(row.get(key), str) or not row[key]
           for key in ('note_id', 'text', 'vector_id')):
        raise ValueError(f'full source note and vector data required: {group}/{instance}')
    spans = row.get('byte_spans')
    if not isinstance(spans, list) or len(spans) != len(fragments):
        raise ValueError(f'one byte range per fragment required: {group}/{instance}')
    encoded = row['text'].encode('utf-8')
    for span, fragment in zip(spans, fragments):
        if (not isinstance(span, list) or len(span) != 2
                or any(type(offset) is not int for offset in span)
                or not 0 <= span[0] < span[1] <= len(encoded)):
            raise ValueError(f'valid UTF-8 byte range required: {group}/{instance}')
        try:
            decoded = encoded[span[0]:span[1]].decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError(f'UTF-8 range splits a character: {group}/{instance}') from error
        if decoded != fragment:
            raise ValueError(f'byte range differs from exact fragment: {group}/{instance}')
    return row


def derive_note_memberships(graph, source_packets):
    """Return per-category own/recursive note IDs, counts, and exact mask evidence.

    Match each graph node's canonical instance ID only within its source packet,
    requiring unchanged fragments and UTF-8 ranges. Ignore source instances not
    present in that node. Preserve every matched source record in full, including
    multiple masks of one note; deduplicate only the note ID lists.

    Recursive membership is the union of own notes and notes of groups in the
    supplied reachability mapping, including cycles safely. IDs are ordered own
    first, then by source node/instance order. No traversal recomputes the supplied
    reachability, and no input or mutable source payload is changed or shared.
    """
    nodes = graph.get('nodes') if isinstance(graph, dict) else None
    packets = source_packets.get('packets') if isinstance(source_packets, dict) else None
    if not isinstance(nodes, list) or not nodes:
        raise ValueError('nonempty graph nodes required')
    if not isinstance(packets, list):
        raise ValueError('source packet list required')
    groups = [node.get('group') if isinstance(node, dict) else None for node in nodes]
    if (any(not isinstance(group, str) or not group for group in groups)
            or len(set(groups)) != len(groups)):
        raise ValueError('unique graph group IDs required')
    reachability = graph.get('reachability')
    if (not isinstance(reachability, dict) or set(reachability) != set(groups)
            or any(not isinstance(reached, list)
                   or any(not isinstance(group, str) or group not in groups for group in reached)
                   for reached in reachability.values())):
        raise ValueError('complete reachability with known graph groups required')
    by_packet = {}
    for packet in packets:
        group = packet.get('packet') if isinstance(packet, dict) else None
        if (not isinstance(group, str) or not group or group in by_packet
                or not isinstance(packet.get('instances'), list)):
            raise ValueError('unique source packet IDs with instance lists required')
        by_packet[group] = packet['instances']

    result = []
    for node in nodes:
        group, canonical = node['group'], node.get('instances')
        if group not in by_packet or not isinstance(canonical, list):
            raise ValueError(f'canonical instances and matching source packet required: {group}')
        matched = [_matched_instance(row, by_packet[group], group) for row in canonical]
        if len({row['instance'] for row in matched}) != len(matched):
            raise ValueError(f'unique canonical instances required: {group}')
        own = list(dict.fromkeys(row['note_id'] for row in matched))
        result.append(dict(group=group, title=node['title'], own_note_ids=own,
                           own_note_count=len(own), matched_instances=matched))

    for node in result:
        reached = set(reachability[node['group']]) - {node['group']}
        recursive = dict.fromkeys(node['own_note_ids'])
        for descendant in result:
            if descendant['group'] in reached:
                recursive.update(dict.fromkeys(descendant['own_note_ids']))
        node['recursive_note_ids'] = list(recursive)
        node['recursive_note_count'] = len(recursive)
    return deepcopy(dict(nodes=result, stats=dict(
        nodes=len(result), matched_instances=sum(len(node['matched_instances']) for node in result),
        unique_note_count=len({note for node in result for note in node['own_note_ids']}))))
