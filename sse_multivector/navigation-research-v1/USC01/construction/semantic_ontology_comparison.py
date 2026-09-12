"""Compare additional ontology ancestors without changing frozen source evidence.

The reports describe structural changes, not semantic improvements. In
particular, a new meaning is retained even when its note set already existed.
"""

from collections import defaultdict
from copy import deepcopy
import re
import xml.etree.ElementTree as ET


def resource_names(xml):
    """Return the unique, safe constituent filenames of the declared SUMO KB."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise ValueError('invalid SUMO resource configuration') from error
    knowledge_bases = [kb for kb in root.findall('.//kb') if kb.get('name') == 'SUMO']
    if len(knowledge_bases) != 1:
        raise ValueError('resource configuration must declare exactly one SUMO kb')
    names = [item.get('filename') for item in knowledge_bases[0].findall('constituent')]
    if not names:
        raise ValueError('SUMO resource configuration has no constituents')
    for name in names:
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.kif', name):
            raise ValueError(f'unsafe SUMO resource filename: {name!r}')
    if len(names) != len(set(names)):
        raise ValueError('duplicate SUMO resource constituents')
    return sorted(names)


def _patterns(condition):
    patterns = {pattern['id']: pattern for pattern in condition['patterns']}
    if len(patterns) != len(condition['patterns']):
        raise ValueError('comparison requires unique pattern identities')
    return patterns


def _representatives(condition, patterns):
    identifiers = {identifier for group in condition['recurring_groups']
                   for identifier in group['most_specific_pattern_ids']}
    if not identifiers <= patterns.keys():
        raise ValueError('recurring representatives must identify existing patterns')
    return identifiers


def compare_condition(before, after, *, allow_sumo_support_changes=False):
    """Check unchanged baseline patterns and report every new recurring meaning.

    Inputs are one lexical condition from ``semantic_graph_patterns.construct``.
    By default the entire old pattern, including each native witness, must remain
    identical. ``allow_sumo_support_changes`` permits evidence changes for old
    SUMO-containing patterns when comparing two ontology interventions; every
    WordNet-only pattern and every existing pattern identity remain unchanged.
    Generating links and most-specific status may change and are compared
    separately. Paired-pattern controls intersect endpoint singleton *rows*, not
    note aliases; those rows need not contain a connecting source edge.
    """
    if before['id'] != after['id']:
        raise ValueError('comparison requires the same baseline lexical condition')
    original, augmented = _patterns(before), _patterns(after)
    changed_ids = []
    evidence_fields = {'rows', 'notes', 'witnesses'}
    for identifier, pattern in original.items():
        current = augmented.get(identifier)
        if current == pattern:
            continue
        endpoints = [pattern['key'][0], pattern['key'][-1]]
        has_sumo = any(sense.startswith('SUMO:') for sense in endpoints)
        unchanged_fields = lambda item: {key: value for key, value in item.items()
                                        if key not in evidence_fields}
        if (current is None or not allow_sumo_support_changes or not has_sumo or
                unchanged_fields(current) != unchanged_fields(pattern)):
            raise ValueError(f'baseline pattern changed or missing: {identifier}')
        changed_ids.append(identifier)

    baseline_sets = defaultdict(list)
    for identifier, pattern in original.items():
        baseline_sets[tuple(pattern['notes'])].append(identifier)
    singleton = {pattern['key'][0]: pattern for pattern in augmented.values()
                 if pattern['kind'] == 'singleton'}
    old_singleton = {pattern['key'][0]: pattern for pattern in original.values()
                     if pattern['kind'] == 'singleton'}

    def summary(pattern, singletons=singleton):
        result = deepcopy(pattern)
        same_support = sorted(baseline_sets.get(tuple(pattern['notes']), ()))
        result.update(same_note_set_in_baseline=bool(same_support),
                      baseline_same_note_set_pattern_ids=same_support)
        if pattern['kind'] in {'connection', 'role'}:
            endpoints = [pattern['key'][0], pattern['key'][-1]]
            if any(sense not in singletons for sense in endpoints):
                raise ValueError(f'missing endpoint singleton for {pattern["id"]}')
            controls = [singletons[sense] for sense in endpoints]
            intersection = set(controls[0]['rows']) & set(controls[1]['rows'])
            if not set(pattern['rows']) <= intersection:
                raise ValueError(f'pair support exceeds singleton row intersection: {pattern["id"]}')
            result.update(
                endpoint_singletons=[{field: deepcopy(control[field])
                                      for field in ['id', 'key', 'notes', 'rows']}
                                     for control in controls],
                singleton_row_intersection=sorted(intersection),
                connection_excluded_rows=sorted(intersection - set(pattern['rows'])))
        return result

    before_representatives = _representatives(before, original)
    after_representatives = _representatives(after, augmented)
    new_ids = augmented.keys() - original.keys()
    recurring = [summary(augmented[identifier]) for identifier in sorted(new_ids)
                 if len(augmented[identifier]['notes']) >= 2]
    changed_recurring = []
    for identifier in sorted(changed_ids):
        previous, current = original[identifier], augmented[identifier]
        if max(len(previous['notes']), len(current['notes'])) < 2:
            continue
        change = {'before': deepcopy(previous), 'after': summary(current)}
        for field in ['rows', 'notes']:
            change['added_' + field] = sorted(set(current[field]) - set(previous[field]))
            change['removed_' + field] = sorted(set(previous[field]) - set(current[field]))
        changed_recurring.append(change)
    old_sets = {tuple(pattern['notes']) for pattern in original.values() if len(pattern['notes']) >= 2}
    new_sets = {tuple(pattern['notes']) for pattern in augmented.values() if len(pattern['notes']) >= 2}

    old_edges = {(edge['parent'], edge['child']): edge for edge in before['edges']}
    new_edges = {(edge['parent'], edge['child']): edge for edge in after['edges']}
    added_edges = [deepcopy(edge) for key, edge in sorted(new_edges.items())
                   if old_edges.get(key) != edge]
    removed_edges = [deepcopy(edge) for key, edge in sorted(old_edges.items())
                     if new_edges.get(key) != edge]

    return {
        'id': after['id'], 'baseline_patterns_unchanged': not changed_ids,
        'wordnet_patterns_unchanged': True,
        'baseline_patterns': len(original), 'augmented_patterns': len(augmented),
        'baseline_links': len(before['edges']), 'augmented_links': len(after['edges']),
        'baseline_recurring_note_sets': len(before['recurring_groups']),
        'augmented_recurring_note_sets': len(after['recurring_groups']),
        'new_recurring_patterns': recurring,
        'changed_recurring_patterns': changed_recurring,
        'new_recurring_note_sets': [list(notes) for notes in sorted(new_sets - old_sets)],
        'removed_recurring_note_sets': [list(notes) for notes in sorted(old_sets - new_sets)],
        'new_most_specific_patterns': [summary(augmented[identifier])
                                       for identifier in sorted(after_representatives - before_representatives)],
        'removed_most_specific_patterns': [summary(original[identifier], old_singleton)
                                           for identifier in sorted(before_representatives - after_representatives)],
        'added_edges': added_edges, 'removed_edges': removed_edges,
    }
