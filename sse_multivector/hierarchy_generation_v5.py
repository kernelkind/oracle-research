"""Recursive V5 through V5.3 selection using native definitions and saved trees.

This module prepares work and consumes receipts. The shared runner remains the
only teacher executor; the ordinary hierarchy coordinator submits ready work.
"""

import json
from pathlib import Path

from . import hierarchy_generation as generation
from . import hierarchy_hdbscan as hdbscan
from . import experiment as workflow


def _originals(state, ids):
    return sorted({o for i in ids for o in state['items'][i]['original_ids']})


def _notes(state, originals):
    return sorted({state['originals'][int(o[1:])-1]['local']['note_id'] for o in originals})


def _include_original_unassigned(state):
    return (state['generation_policy'] in (generation.POLICY_V51, generation.POLICY_V52,
                                         generation.POLICY_V53)
            or state.get('v5_options', {}).get('include_original_unassigned', False))


def _definition_key(members, parent, stage):
    return workflow.inputs.digest(dict(members=members, parent=parent, stage=stage))


def _definition(state, members, parent, stage):
    """One group's definition is already the one-group section's definition."""
    if len(members) == 1:
        return members[0]
    definitions = state['v5']['definitions']
    key = _definition_key(members, parent, stage)
    if key not in definitions:
        definitions[key] = dict(members=list(members), parent=parent, stage=stage,
                                payload=generation._payload(state, members, parent))
    return definitions[key].get('item')


def _collect_definitions(state):
    changed = False
    for definition in state['v5']['definitions'].values():
        if 'item' in definition or 'producer' not in definition:
            continue
        producer = definition['producer']
        answer = state['experiments'][producer['experiment']].get('answers', {}).get(producer['case'], {})
        if answer.get('status') != 'valid':
            continue
        value = answer['output']
        identifier = f"T{len(state['items']):06d}"
        state['items'][identifier] = dict(
            subject=value['title'], meaning=value['meaning'],
            group=definition['members'], parent=definition['parent'],
            original_ids=_originals(state, definition['members']), producer=producer)
        definition['item'] = identifier
        changed = True
    return changed


def _prepare_definitions(directory, state):
    ready = [(k, d) for k, d in state['v5']['definitions'].items() if 'producer' not in d]
    if not ready:
        return False
    by_parent = {}
    for key, definition in ready:
        by_parent.setdefault(definition['parent'], []).append((key, definition))
    for definitions in by_parent.values():
        cases = [dict(id='D'+key, inputs=dict(INPUT_JSON=json.dumps(d['payload'], ensure_ascii=False)),
                      evidence=dict(stage=d['stage'], members=d['members'], parent=d['parent']))
                 for key, d in definitions]
        index = generation._experiment(directory, state, 'consolidation', state['consolidation_spec'],
                                       dict(cases=cases), 'hierarchy_group_consolidation')
        for key, definition in definitions:
            definition['producer'] = dict(experiment=index, case='D'+key)
    return True


def proposals(state, round_, max_siblings=6):
    """Rank sections by notes, excluding existing siblings' notes from V5.2."""
    items = state['items']
    existing = {items[i]['owner']: i for i in round_['current'] if 'owner' in items[i]}
    sections = round_['selection']['sections']
    amendments, available, conflicts = [], [], []
    for section in sections:
        groups = [g-1 for g in section['groups']]
        members = [i for g in groups for i in round_['groups'][g]]
        owners = sorted({items[i]['owner'] for i in members if 'owner' in items[i]})
        row = dict(groups=groups, members=members, owner=owners[0] if len(owners) == 1 else None)
        if len(owners) > 1:
            # A numerical join is not permission to merge canonical meanings.
            conflicts.append(dict(groups=groups, owners=owners))
        elif owners:
            if set(_originals(state, members)) - set(items[existing[owners[0]]]['original_ids']):
                amendments.append(row)
        else:
            available.append(row)
    remaining = max_siblings-len(existing)
    covered = (set(_notes(state, _originals(state, existing.values())))
               if state.get('generation_policy') in (generation.POLICY_V52, generation.POLICY_V53)
               else set())

    def score(proposal):
        return len(set(_notes(state, _originals(state, proposal['members']))) - covered)

    if round_['selection']['rule'] == 'largest-groups-v5':
        available.sort(key=lambda p: -score(p))
        selected = available[:remaining]
    elif len(available) <= remaining:
        selected = available
    else:
        selected = [max(available, key=score)]
    return dict(proposals=amendments+selected, conflicting_sections=conflicts)


def _publish(state, family, item_id, groups, owner=None, *, leaf=False):
    item = state['items'][item_id]
    if owner is None:
        owner = f"C{len(state['nodes'])+1:05d}"
        node = dict(id=owner, parents=[] if family['parent'] is None else [family['parent']],
                    family=family['id'], versions=[])
        state['nodes'].append(node)
        family['nodes'].append(owner)
    else:
        node = next(n for n in state['nodes'] if n['id'] == owner)
    producer = item['producer']
    record = state['experiments'][producer['experiment']]
    item['owner'] = owner
    node.update(subject=item['subject'], meaning=item['meaning'], item=item_id,
                original_ids=item['original_ids'],
                entries=[state['originals'][int(i[1:])-1]['local'] for i in item['original_ids']],
                groups=groups, leaf=leaf,
                synthetic=dict(experiment=record['experiment'], case=producer['case'],
                               receipt=record['answers'][producer['case']]['receipt']))
    node['versions'].append(dict(item=item_id, groups=groups, leaf=leaf))
    return owner


def _membership_additions(round_, existing, untracked):
    existing, untracked = set(existing), set(untracked)
    return sorted({i for group in round_['groups'] if existing.intersection(group)
                   for i in group if i in untracked})


def _add_memberships(directory, state, family):
    """Freeze one global pool for all siblings; preserve native definition evidence."""
    nodes = {n['id']: n for n in state['nodes']}
    passes = state['v5'].setdefault('membership_passes', [])
    if 'membership_pass' not in family:
        claimed = {i for node in nodes.values() for i in node['original_ids']}
        untracked = [i for i in state['v5']['eligible_ids'] if i not in claimed]
        family['membership_pass'] = len(passes)
        passes.append(dict(family=family['id'], canonical_items=[n['item'] for n in state['nodes']],
                           untracked_ids=untracked, rounds={}, additions={}, applied=False))
        # Persist the snapshot before external work. A failed run must not rebuild
        # its global pool after unrelated model batches finish in the meantime.
        if untracked and family['nodes']:
            _prepare_definitions(directory, state)
            generation.check_state(state, verify_receipts=False)
            workflow.write(directory/'state.json', state)
    record = passes[family['membership_pass']]
    untracked = record['untracked_ids']
    if untracked:
        for identifier in family['nodes']:
            node = nodes[identifier]
            ids = sorted(set(node['original_ids']) | set(untracked))
            inputs = dict(id=family['id']+'-'+identifier, current=ids, rounds=[])
            destination = directory/family['id']/'memberships'/identifier
            destination.mkdir(parents=True, exist_ok=True)
            round_ = hdbscan.round_for(destination, state, inputs, generation._vectors(state, ids))
            record['rounds'][identifier] = round_
            record['additions'][identifier] = _membership_additions(
                round_, node['original_ids'], untracked)
    # Apply together: a match with one sibling must not remove another sibling's input.
    for identifier, added in record['additions'].items():
        node = nodes[identifier]
        node['original_ids'] = sorted(set(node['original_ids']) | set(added))
        node['entries'] = [state['originals'][int(i[1:])-1]['local'] for i in node['original_ids']]
    record['applied'] = True


def _finish(directory, state, family):
    if state['generation_policy'] == generation.POLICY_V53:
        _add_memberships(directory, state, family)
    nodes = {n['id']: n for n in state['nodes']}
    covered = {o for n in family['nodes'] for o in nodes[n]['original_ids']}
    eligible = set(state['v5']['eligible_ids'])
    family['direct_original_ids'] = [i for i in family['original_ids'] if i in eligible and i not in covered]
    direct = _notes(state, family['direct_original_ids'])
    if family['parent'] is None:
        state['direct_note_ids'] = direct
    else:
        nodes[family['parent']]['direct_note_ids'] = direct
    family['complete'] = True
    if state.get('v5_options', {}).get('roots_only'):
        return
    for identifier in family['nodes']:
        node = nodes[identifier]
        if node['leaf']:
            continue
        generation._new_family(state, identifier, node['original_ids'])
        child_family = state['families'][-1]
        if (len(node['versions']) == 1 and len(node['groups']) <= state['max_siblings']
                and node['original_ids'] == state['items'][node['item']]['original_ids']):
            # Already-known groups are the leaf stopping case, not a new section level.
            child_family['leaf_groups'] = list(node['groups'])
        # Otherwise the next level starts from original entries and gets a fresh tree.


def _step(directory, state, family):
    if family['complete']:
        return False
    family.setdefault('nodes', [])
    if 'leaf_groups' in family:
        for item in family['leaf_groups']:
            _publish(state, family, item, [item], leaf=True)
        family['current'] = list(family['leaf_groups'])
        _finish(directory, state, family)
        return True
    if family['rounds'] and not family['rounds'][-1].get('applied'):
        round_ = family['rounds'][-1]
    else:
        if (len(family['nodes']) >= state['max_siblings'] or not family['current']
                or family['nodes'] and all('owner' in state['items'][i] for i in family['current'])):
            _finish(directory, state, family)
            return True
        generation._prepare_encoding(directory, state, family['current'])
        if any(state['items'][i]['vector_key'] not in state['vectors'] for i in family['current']):
            return False
        destination = directory/family['id']
        destination.mkdir(exist_ok=True)
        vectors = generation._vectors(state, family['current'])
        round_ = hdbscan.round_for(destination, state, family, vectors)
        if not round_['groups']:
            if family['parent'] is None and 'eligible_ids' not in state['v5']:
                state['v5']['eligible_ids'] = (list(round_['current']) if
                    _include_original_unassigned(state) else [])
                state['v5']['original_unassigned_ids'] = list(round_['current'])
                family['current'] = []
            family['rounds'].append(dict(round_, selection=None, proposals=[], applied=True,
                                         after=list(family['current'])))
            _finish(directory, state, family)
            return True
        request, mapping = hdbscan.request_for(state, round_['current'], vectors)
        tree = hdbscan.project(hdbscan.read_result(round_['hdbscan']['result']), request, mapping)
        round_['selection'] = hdbscan.select_sections(tree, state['max_siblings'])
        round_.update(proposals(state, round_, state['max_siblings']))
        family['rounds'].append(round_)
        if family['parent'] is None and 'eligible_ids' not in state['v5']:
            state['v5']['eligible_ids'] = _originals(state, round_['current'] if
                _include_original_unassigned(state) else
                [i for g in round_['groups'] for i in g])
            state['v5']['original_unassigned_ids'] = list(round_['unassigned'])
    if not round_['proposals']:
        round_.update(applied=True, after=list(family['current']))
        _finish(directory, state, family)
        return True
    changed = False
    for proposal in round_['proposals']:
        if 'item' in proposal:
            continue
        groups = [_definition(state, round_['groups'][g], family['parent'], 'group')
                  for g in proposal['groups']]
        if any(i is None for i in groups):
            continue
        item = _definition(state, groups, family['parent'], 'section')
        if item is not None:
            proposal.update(item=item, group_items=groups)
            changed = True
    if not all('item' in p for p in round_['proposals']):
        return changed
    removed, added = set(), []
    for proposal in round_['proposals']:
        removed.update(proposal['members'])
        item = proposal['item']
        leaf = (len(proposal['groups']) == 1 and proposal['owner'] is None
                or round_['selection']['rule'] == 'largest-groups-v5')
        proposal['leaf'] = leaf
        proposal['node'] = _publish(state, family, item, proposal['group_items'],
                                    proposal['owner'], leaf=leaf)
        added.append(item)
    current = [i for i in family['current'] if i not in removed]
    if family['parent'] is None and len(family['rounds']) == 1:
        current = [i for i in current if i in state['v5']['eligible_ids']]
    family['current'] = current+added
    round_.update(applied=True, after=list(family['current']))
    if (len(family['nodes']) >= state['max_siblings']
            or round_['selection']['rule'] in ('largest-groups-v5', 'group-leaves-v5')):
        _finish(directory, state, family)
    return True


def schedule(directory, state):
    state.setdefault('v5', dict(definitions={}))
    while True:
        pending = next((f for f in state['families']
                        if not f['complete'] and 'membership_pass' in f), None)
        if pending is not None:
            _finish(directory, state, pending)
            continue
        changed = _collect_definitions(state)
        for family in list(state['families']):
            changed = _step(directory, state, family) or changed
        changed = _prepare_definitions(directory, state) or changed
        if not changed:
            break
    if all(f['complete'] for f in state['families']):
        state['status'] = 'complete'


def _check_memberships(state):
    """Reproduce additions from the frozen global pool and unchanged group receipts."""
    nodes = {n['id']: n for n in state['nodes']}
    families = {f['id']: f for f in state['families']}
    passes = state['v5'].get('membership_passes', [])
    seen, completed, additions, previous_count = set(), set(), {}, 0
    for index, record in enumerate(passes):
        family = families.get(record['family'])
        if (family is None or family['id'] in seen or type(record.get('applied')) is not bool
                or family['complete'] != record['applied']
                or family.get('membership_pass') != index):
            raise ValueError('V5.3 membership pass differs from completed sibling lineup')
        seen.add(family['id'])
        items = record['canonical_items']
        if (len(items) < previous_count or len(items) > len(nodes)
                or any(i not in state['items'] for i in items)):
            raise ValueError('V5.3 membership snapshot changed')
        previous_count = len(items)
        owners = [state['items'][i].get('owner') for i in items]
        if owners != [n['id'] for n in state['nodes'][:len(items)]]:
            raise ValueError('V5.3 membership snapshot omitted canonical nodes')
        snapshot = dict(zip(owners, items, strict=True))
        if (any(i not in [v['item'] for v in nodes[n]['versions']] for n, i in snapshot.items())
                or any(snapshot.get(n) != nodes[n]['item'] for n in family['nodes'])):
            raise ValueError('V5.3 membership snapshot changed canonical definitions')
        claimed = {o for i in items for o in state['items'][i]['original_ids']}
        claimed.update(o for group in additions.values() for o in group)
        untracked = [i for i in state['v5']['eligible_ids'] if i not in claimed]
        if record['untracked_ids'] != untracked:
            raise ValueError('V5.3 global untracked membership pool changed')
        if not record['applied']:
            if index != len(passes)-1 or record['rounds'] or record['additions']:
                raise ValueError('V5.3 pending membership snapshot changed')
            continue
        completed.add(family['id'])
        expected_nodes = set(family['nodes']) if untracked else set()
        if set(record['rounds']) != expected_nodes or set(record['additions']) != expected_nodes:
            raise ValueError('V5.3 membership clustering omitted a sibling')
        for identifier in expected_nodes:
            before = state['items'][nodes[identifier]['item']]['original_ids']
            round_ = record['rounds'][identifier]
            ids = sorted(set(before) | set(untracked))
            if round_['current'] != ids:
                raise ValueError('V5.3 membership clustering inputs changed')
            inputs = dict(id=family['id']+'-'+identifier)
            hdbscan.check_round(state, inputs, round_, generation._vectors(state, ids))
            expected = _membership_additions(round_, before, untracked)
            if record['additions'][identifier] != expected:
                raise ValueError('V5.3 membership addition lacks a shared group')
            additions[identifier] = expected
    if completed != {f['id'] for f in state['families'] if f['complete']}:
        raise ValueError('V5.3 completed lineup lacks its membership pass')
    for family in state['families']:
        if ('membership_pass' in family) != (family['id'] in seen):
            raise ValueError('V5.3 membership pass reference changed')
    for identifier, node in nodes.items():
        expected = sorted(set(state['items'][node['item']]['original_ids'])
                          | set(additions.get(identifier, [])))
        if node['original_ids'] != expected:
            raise ValueError('V5.3 canonical membership differs from its shared groups')


def check_state(state, *, verify_current_code=True):
    """Validate ownership, fresh-tree inputs and immutable native evidence."""
    bound = [p for p in state['sources'] if Path(p).name == Path(__file__).name]
    if (len(bound) != 1 or verify_current_code and bound[0] != str(Path(__file__).resolve())):
        raise ValueError('V5 construction source binding changed')
    if not state['families']:
        if 'v5' in state:
            raise ValueError('V5 state appeared before Bootstrap')
        return
    data = state['v5']
    nodes = {n['id']: n for n in state['nodes']}
    families = {f['id']: f for f in state['families']}
    if len(families) != len(state['families']):
        raise ValueError('duplicate V5 family identity')
    definitions = data['definitions']
    cases = set()
    for key, d in definitions.items():
        expected_key = _definition_key(d['members'], d['parent'], d['stage'])
        if (key != expected_key or d['payload'] != generation._payload(state, d['members'], d['parent'])
                or d['stage'] not in ('group', 'section')):
            raise ValueError('V5 definition inputs changed')
        producer = d['producer']
        if type(producer['experiment']) is not int or not 1 <= producer['experiment'] < len(state['experiments']):
            raise ValueError('invalid V5 definition producer')
        record = state['experiments'][producer['experiment']]
        if (producer['case'] != 'D'+key or record['role'] != 'consolidation'
                or json.loads(record['inputs'][producer['case']]['INPUT_JSON']) != d['payload']):
            raise ValueError('V5 definition differs from its native producer')
        cases.add((producer['experiment'], producer['case']))
        if 'item' in d:
            item = state['items'][d['item']]
            if item['producer'] != producer or item['group'] != d['members'] or item['parent'] != d['parent']:
                raise ValueError('V5 definition item changed')
    produced = {d['item'] for d in definitions.values() if 'item' in d}
    originals = {o['id'] for o in state['originals'] if o.get('meaning') is not None}
    if set(state['items']) != originals | produced:
        raise ValueError('unexpected V5 construction item')
    if cases != {(i, c) for i, r in enumerate(state['experiments']) if i for c in r['inputs']}:
        raise ValueError('unexpected V5 native producer')
    canonical = set()
    events = {}
    for family in state['families']:
        parent = family['parent']
        expected = ([o['id'] for o in state['originals'] if o.get('meaning') is not None]
                    if parent is None else nodes[parent]['original_ids'])
        if family['original_ids'] != expected:
            raise ValueError('V5 child pool must use accumulated original entries')
        family_nodes = family.get('nodes', [])
        if (len(family_nodes) > state['max_siblings'] or canonical.intersection(family_nodes)
                or len(set(family_nodes)) != len(family_nodes)):
            raise ValueError('invalid V5 canonical sibling ownership')
        canonical.update(family_nodes)
        current = list(family['original_ids'])
        for round_ in family['rounds']:
            if round_['current'] != current:
                raise ValueError('V5 round does not follow previous replacement')
            vectors = generation._vectors(state, current)
            hdbscan.check_round(state, family, round_, vectors)
            if round_['groups']:
                request, mapping = hdbscan.request_for(state, current, vectors)
                tree = hdbscan.project(hdbscan.read_result(round_['hdbscan']['result']), request, mapping)
                if round_['selection'] != hdbscan.select_sections(tree, state['max_siblings']):
                    raise ValueError('V5 section cut changed')
                planned = proposals(state, round_, state['max_siblings'])
                actual = [{k: p[k] for k in ('groups', 'members', 'owner')} for p in round_['proposals']]
                if actual != planned['proposals'] or round_['conflicting_sections'] != planned['conflicting_sections']:
                    raise ValueError('V5 selection or representative ownership changed')
            if round_.get('applied'):
                for p in round_['proposals']:
                    groups = []
                    for g in p['groups']:
                        key = _definition_key(round_['groups'][g], parent, 'group')
                        groups.append(definitions[key]['item'])
                    key = _definition_key(groups, parent, 'section')
                    item = groups[0] if len(groups) == 1 else definitions[key]['item']
                    leaf = (len(groups) == 1 and p['owner'] is None
                            or round_['selection']['rule'] == 'largest-groups-v5')
                    if (p['item'] != item or p['group_items'] != groups or p['leaf'] != leaf
                            or p['owner'] is not None and p['node'] != p['owner']):
                        raise ValueError('V5 group definition or representative version changed')
                    events.setdefault(p['node'], []).append(dict(item=item, groups=groups, leaf=leaf))
                removed = {i for p in round_['proposals'] for i in p['members']}
                added = [p['item'] for p in round_['proposals']]
                current = [i for i in current if i not in removed]
                if parent is None and round_ is family['rounds'][0]:
                    current = [i for i in current if i in data['eligible_ids']]
                current += added
                if current != round_['after']:
                    raise ValueError('V5 replacement pool changed')
        if 'leaf_groups' in family:
            node = nodes[parent]
            if (len(node['versions']) != 1 or node['groups'] != family['leaf_groups']
                    or not 2 <= len(family['leaf_groups']) <= state['max_siblings']
                    or family['rounds']):
                raise ValueError('V5 leaf groups differ from the final parent')
            current = family['leaf_groups']
            if family['complete'] or 'membership_pass' in family:
                if len(family_nodes) != len(current):
                    raise ValueError('V5 leaf groups were not all exposed')
                for identifier, item in zip(family_nodes, current, strict=True):
                    events.setdefault(identifier, []).append(dict(item=item, groups=[item], leaf=True))
        if current != family['current']:
            raise ValueError('V5 current pool changed')
        for identifier in family_nodes:
            node = nodes[identifier]
            if (node['family'] != family['id'] or node['parents'] != ([] if parent is None else [parent])
                    or node['versions'][-1]['item'] != node['item']
                    or state['items'][node['item']].get('owner') != identifier):
                raise ValueError('V5 canonical node differs from its lineup')
        if family['complete']:
            covered = {o for n in family_nodes for o in nodes[n]['original_ids']}
            direct = [i for i in expected if i in data['eligible_ids'] and i not in covered]
            notes = state.get('direct_note_ids', []) if parent is None else nodes[parent]['direct_note_ids']
            if family['direct_original_ids'] != direct or notes != _notes(state, direct):
                raise ValueError('V5 leftover note associations changed')
    if canonical != set(nodes):
        raise ValueError('V5 canonical node appeared outside its lineup')
    for identifier, node in nodes.items():
        versions = events.get(identifier, [])
        if (node['versions'] != versions or not versions
                or any(node[k] != versions[-1][k] for k in ('groups', 'leaf'))):
            raise ValueError('V5 canonical groups or version history changed')
        if any(not set(state['items'][a['item']]['original_ids']) <= set(state['items'][b['item']]['original_ids'])
               for a, b in zip(versions, versions[1:])):
            raise ValueError('V5 amendment lost original associations')
    if state['generation_policy'] == generation.POLICY_V53:
        _check_memberships(state)
    elif 'membership_passes' in data or any('membership_pass' in f for f in state['families']):
        raise ValueError('membership passes require V5.3')
    child_parents = [f['parent'] for f in state['families'] if f['parent'] is not None]
    expected_parents = [n['id'] for n in state['nodes'] if not n['leaf']
                        and families[n['family']]['complete']
                        and not state.get('v5_options', {}).get('roots_only')]
    if sorted(child_parents) != sorted(expected_parents):
        raise ValueError('V5 unfinished child families changed')
    if 'eligible_ids' in data:
        first = state['families'][0]['rounds'][0]
        expected = _originals(state, first['current'] if
            _include_original_unassigned(state) else
            [i for group in first['groups'] for i in group])
        if data['eligible_ids'] != expected or data['original_unassigned_ids'] != first['unassigned']:
            raise ValueError('V5 original grouped eligibility changed')
    if (state['status'] == 'complete') != all(f['complete'] for f in state['families']):
        raise ValueError('V5 completion state changed')
