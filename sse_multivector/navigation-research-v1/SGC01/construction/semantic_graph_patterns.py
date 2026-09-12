"""Construct witnessed singleton and directed one-role semantic graph patterns.

The caller supplies contextual senses, canonical directed roles and their source
rows. This module neither selects senses nor normalizes roles. Generalization
uses only the supplied ancestor order. Links form a sparse generating graph,
not necessarily its global transitive reduction. Patterns describe topics;
source contexts remain in witnesses, not assertions that every event occurred.
"""

from collections import defaultdict
import hashlib
from itertools import product
import json


def _integer(value, description):
    if type(value) is not int:
        raise ValueError(f'{description} must be an integer')
    return value


def _text(value, description):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{description} must be a nonempty string')
    return value


def _rows(items, description):
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f'{description} entries must be objects')
        row = _integer(item.get('row'), f'{description} row')
        if row in result:
            raise ValueError(f'duplicate {description} row {row}')
        result[row] = item
    return result


def _sources(records, graphs):
    records, graphs = _rows(records, 'record'), _rows(graphs, 'graph')
    if records.keys() != graphs.keys():
        raise ValueError('record and graph row identities must match exactly')
    sources = {}
    for row in sorted(records):
        note = _text(records[row].get('note'), f'record {row} note')
        graph = graphs[row]
        if 'note' in graph and graph['note'] != note:
            raise ValueError(f'graph {row} note does not match its record')
        if not isinstance(graph.get('nodes'), list) or not isinstance(graph.get('edges'), list):
            raise ValueError(f'graph {row} requires nodes and edges lists')
        nodes = {}
        for node in graph['nodes']:
            if not isinstance(node, dict):
                raise ValueError(f'graph {row} nodes must be objects')
            identifier = _integer(node.get('id'), f'graph {row} node id')
            if identifier in nodes:
                raise ValueError(f'duplicate graph {row} node id {identifier}')
            nodes[identifier] = {
                'sense': _text(node.get('sense'), f'graph {row} node sense'),
                'context': _integer(node.get('context'), f'graph {row} node context'),
            }
        edges = set()
        for edge in graph['edges']:
            if not isinstance(edge, dict):
                raise ValueError(f'graph {row} edges must be objects')
            source = _integer(edge.get('source'), f'graph {row} edge source')
            target = _integer(edge.get('target'), f'graph {row} edge target')
            role = _text(edge.get('role'), f'graph {row} edge role')
            if source not in nodes or target not in nodes:
                raise ValueError(f'graph {row} edge has an unknown endpoint')
            edges.add((source, role, target))
        sources[row] = {'note': note, 'nodes': nodes, 'edges': sorted(edges)}
    return sources


def _sense_order(sources, lexicon):
    if not isinstance(lexicon, dict):
        raise ValueError('lexicon must map senses to entries')
    pending = {node['sense'] for source in sources.values() for node in source['nodes'].values()}
    ancestors = {}
    while pending:
        sense = min(pending)
        pending.remove(sense)
        if sense in ancestors:
            continue
        entry = lexicon.get(sense)
        if entry is None:
            values = [sense]
        else:
            if not isinstance(entry, dict) or not isinstance(entry.get('ancestors'), list):
                raise ValueError(f'lexicon {sense} requires an ancestors list')
            values = entry['ancestors']
        values = frozenset(_text(value, f'ancestor of {sense}') for value in values)
        if sense not in values:
            raise ValueError(f'ancestors of {sense} must include itself')
        ancestors[sense] = values
        pending.update(values - ancestors.keys())
    for sense, values in ancestors.items():
        for ancestor in values - {sense}:
            if sense in ancestors[ancestor]:
                raise ValueError(f'cyclic ancestor order at {sense} and {ancestor}')
            if not ancestors[ancestor] <= values:
                raise ValueError(f'ancestor closure is incomplete for {sense}')
    immediate = {}
    for sense, values in ancestors.items():
        broader = values - {sense}
        non_immediate = set()
        for ancestor in broader:
            non_immediate.update(ancestors[ancestor] - {ancestor})
        immediate[sense] = sorted(broader - non_immediate)
    return {sense: sorted(values) for sense, values in ancestors.items()}, immediate


def _identifier(key):
    encoded = json.dumps(key, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return 'G' + hashlib.sha256(encoded).hexdigest()[:20]


def _witness(identity, sources):
    kind, row, *parts = identity
    source = sources[row]
    if kind == 'singleton':
        node_ids, edge = parts, None
    else:
        start, role, target = parts
        node_ids = [start, target]
        edge = {'source': start, 'role': role, 'target': target}
    return {
        'row': row, 'note': source['note'], 'node_ids': node_ids,
        'contexts': [source['nodes'][identifier]['context'] for identifier in node_ids],
        'source_senses': [source['nodes'][identifier]['sense'] for identifier in node_ids],
        'edge': edge,
    }


def _condition(sources, ancestors, immediate, generalized):
    occurrences = defaultdict(set)
    for row, source in sources.items():
        for identifier, node in source['nodes'].items():
            senses = ancestors[node['sense']] if generalized else [node['sense']]
            for sense in senses:
                occurrences['singleton', sense].add(('singleton', row, identifier))
        for start, role, target in source['edges']:
            start_sense = source['nodes'][start]['sense']
            target_sense = source['nodes'][target]['sense']
            starts = ancestors[start_sense] if generalized else [start_sense]
            targets = ancestors[target_sense] if generalized else [target_sense]
            for broader_start, broader_target in product(starts, targets):
                occurrences['role', broader_start, role, broader_target].add(
                    ('role', row, start, role, target))

    identifiers = {key: _identifier(key) for key in sorted(occurrences)}
    if len(set(identifiers.values())) != len(identifiers):
        raise ValueError('pattern identifier hash collision')
    patterns = []
    for key, identifier in identifiers.items():
        witnesses = [_witness(identity, sources) for identity in sorted(occurrences[key])]
        patterns.append({
            'id': identifier, 'kind': key[0], 'key': list(key[1:]),
            'rows': sorted({witness['row'] for witness in witnesses}),
            'notes': sorted({witness['note'] for witness in witnesses}),
            'witnesses': witnesses,
        })

    links = defaultdict(set)

    def link(parent, child, operation):
        if parent in identifiers:
            links[identifiers[parent], identifiers[child]].add(operation)

    # Look up only coordinate refinements and endpoint projections. No scan over
    # unrelated pattern pairs is needed, including for recurring-pattern reports.
    for key in identifiers:
        if key[0] == 'singleton':
            if generalized:
                for broader in immediate[key[1]]:
                    link(('singleton', broader), key, 'broaden_singleton')
        else:
            _, start, role, target = key
            link(('singleton', start), key, 'drop_target')
            link(('singleton', target), key, 'drop_source')
            if generalized:
                for broader in immediate[start]:
                    link(('role', broader, role, target), key, 'broaden_source')
                for broader in immediate[target]:
                    link(('role', start, role, broader), key, 'broaden_target')
    edges = [{'parent': parent, 'child': child, 'operations': sorted(operations)}
             for (parent, child), operations in sorted(links.items())]

    groups = defaultdict(set)
    support = {}
    for pattern in patterns:
        notes = tuple(pattern['notes'])
        support[pattern['id']] = notes
        if len(notes) >= 2:
            groups[notes].add(pattern['id'])
    less_specific = set()
    for edge in edges:
        if support[edge['parent']] == support[edge['child']]:
            less_specific.add(edge['parent'])
    # Along each link the child's support is a subset of the parent's. If two
    # path endpoints have equal support, every intermediate pattern does too;
    # checking generating links therefore also detects non-immediate dominance.
    recurring_groups = [
        {'notes': list(notes), 'pattern_ids': sorted(group),
         'most_specific_pattern_ids': sorted(group - less_specific)}
        for notes, group in sorted(groups.items())
    ]
    return {'id': 'generalized' if generalized else 'literal', 'patterns': patterns,
            'edges': edges, 'recurring_groups': recurring_groups}


def construct(records, graphs, lexicon):
    """Return literal/generalized patterns, sparse links and support-set reports.

    ``records`` and ``graphs`` must have identical, unique integer row identities.
    Graph node IDs are local to a row; concepts and directed edges never combine
    across occurrences. A missing lexicon entry keeps its sense literal. Present
    entries supply a reflexive, transitively closed ``ancestors`` list; cycles
    and inconsistent closure are rejected rather than silently repaired.

    Relations and both endpoint senses remain explicit in role-pattern keys.
    Repeated note aliases increase witnesses, not the distinct-note support.
    Equal-support reporting never merges patterns or filters the full inventory.
    """
    sources = _sources(records, graphs)
    ancestors, immediate = _sense_order(sources, lexicon)
    return {
        'source_rows': sorted(sources),
        'source_notes': sorted({source['note'] for source in sources.values()}),
        'link_semantics': 'broader_to_narrower_sparse_generating_links_not_transitive_reduction',
        'conditions': [_condition(sources, ancestors, immediate, generalized)
                       for generalized in [False, True]],
    }
