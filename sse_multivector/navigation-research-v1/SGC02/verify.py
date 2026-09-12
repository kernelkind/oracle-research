"""Replay SGC02 and preserve complete witnesses/paths used by its source audit.

Run from any directory with Python 3.11. This reads frozen evidence, invokes the
saved production constructor, and writes audit.json beside this file. No inference,
input correction, category selection, or browser changes occur.
"""

from collections import deque
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'construction'))
from semantic_graph_patterns import construct
from semantic_graph_probe import save


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect():
    base = HERE.parent / 'SGC01' / 'construction'
    current = HERE / 'construction'
    original = read(base / 'result.json')
    changed = read(current / 'result.json')
    config = read(current / 'config.json')
    assert all(sha(base / name) == value for name, value in config['baseline_sha256'].items())
    assert all(sha(current / name) == value
               for name, value in config['source_hashes'].items())
    assert (base / 'inputs.json').read_bytes() == (current / 'inputs.json').read_bytes()
    graphs = read(base / 'graphs.json')
    rows = {g['row'] for g in graphs}
    records = [r for r in read(base / 'inputs.json') if r['row'] in rows]
    lexicon = read(base / 'lexicon.json')['senses']
    for saved, policy in [(original, 'exact'), (changed, 'connection')]:
        replay = construct(records, graphs, lexicon, relation_policy=policy)
        assert replay == {k: v for k, v in saved.items() if k not in ['run_id', 'excluded_rows']}
    conditions = []
    for before, after in zip(original['conditions'], changed['conditions']):
        assert before['id'] == after['id']
        old = {p['id']: p for p in before['patterns']}
        new = {p['id']: p for p in after['patterns']}
        assert {k: p for k, p in old.items() if p['kind'] == 'singleton'} == {
            k: p for k, p in new.items() if p['kind'] == 'singleton'}
        edges = after['edges']
        successors = {k: [] for k in new}
        degree = dict.fromkeys(new, 0)
        for edge in edges:
            parent, child = edge['parent'], edge['child']
            assert set(new[child]['rows']) <= set(new[parent]['rows'])
            assert set(new[child]['notes']) <= set(new[parent]['notes'])
            successors[parent].append(child)
            degree[child] += 1
        pending = [k for k, d in degree.items() if d == 0]
        visited = 0
        while pending:
            visited += 1
            for child in successors[pending.pop()]:
                degree[child] -= 1
                if degree[child] == 0:
                    pending.append(child)
        assert visited == len(new)
        old_sets = {tuple(g['notes']) for g in before['recurring_groups']}
        new_sets = {tuple(g['notes']) for g in after['recurring_groups']}
        representative_ids = {k for g in after['recurring_groups'] for k in g['most_specific_pattern_ids']}
        removed = [g for g in before['recurring_groups'] if tuple(g['notes']) not in new_sets]
        condition = dict(
            id=after['id'], patterns=len(new), links=len(edges),
            acyclic=True, note_and_row_containment=True, singletons_unchanged=True,
            gained_note_sets=sorted(new_sets - old_sets), lost_note_sets=sorted(old_sets - new_sets),
            representatives=[new[k] for k in sorted(representative_ids)],
            lost_representatives=[old[k] for g in removed for k in g['most_specific_pattern_ids']])
        if after['id'] == 'generalized':
            by_key = {(p['kind'], *p['key']): p['id'] for p in new.values()}

            def path(waypoints):
                identifiers = [by_key[key] for key in waypoints]
                complete = [identifiers[0]]
                for start, end in zip(identifiers, identifiers[1:]):
                    queue = deque([[start]])
                    seen = {start}
                    while queue:
                        part = queue.popleft()
                        if part[-1] == end:
                            complete.extend(part[1:])
                            break
                        for child in sorted(successors[part[-1]]):
                            if child not in seen:
                                seen.add(child)
                                queue.append(part + [child])
                    else:
                        raise AssertionError(('missing saved path', start, end))
                pairs = set(zip(complete, complete[1:]))
                return dict(patterns=[new[k] for k in complete],
                            edges=[e for e in edges if (e['parent'], e['child']) in pairs])

            def single(sense):
                return ('singleton', sense)

            def connection(a, b):
                return ('connection', *sorted([a, b]))

            food = single('food.n.02')
            activity = connection('activity.n.01', 'food.n.02')
            preparation = connection('preparation.n.01', 'food.n.02')
            condition['inspected_paths'] = {
                'food_activity_preparation_bread': path([
                    food, activity, preparation, connection('preparation.n.01', 'bread.n.01')]),
                'food_activity_preparation_steak': path([
                    food, activity, preparation, connection('preparation.n.01', 'steak.n.01')]),
                'food_activity_preservation_beet': path([
                    food, activity, connection('preservation.n.01', 'food.n.02'),
                    connection('preservation.n.01', 'beet.n.02')]),
                'nutrient_activity_preservation': path([
                    single('food.n.01'), connection('activity.n.01', 'food.n.01'),
                    connection('preservation.n.01', 'food.n.01')]),
                'food_cooking_brisket': path([
                    food, connection('cook.v.01', 'food.n.02'), connection('cook.v.01', 'brisket.n.01')]),
            }
            compared = []
            for key in [activity, connection('activity.n.01', 'food.n.01'),
                        connection('preservation.n.01', 'matter.n.03')]:
                p = new[by_key[key]]
                one, two = [new[by_key[single(sense)]] for sense in p['key']]
                compared.append(dict(
                    pattern=p, all_exact_same_note_set=[q for q in old.values() if q['notes'] == p['notes']],
                    singleton_row_intersection=sorted(set(one['rows']) & set(two['rows'])),
                    singleton_note_intersection=sorted(set(one['notes']) & set(two['notes']))))
            condition['target_comparisons'] = compared
        conditions.append(condition)
    return dict(run_id='SGC02', all_frozen_hashes_match=True,
                both_production_policies_replay=True, source_input_bytes_unchanged=True,
                source_notes=changed['source_notes'], excluded_rows=changed['excluded_rows'],
                baseline_sha256=config['baseline_sha256'], conditions=conditions)


if __name__ == '__main__':
    result = inspect()
    save(HERE / 'audit.json', result)
    print(json.dumps([{k: c[k] for k in ['id', 'patterns', 'links', 'gained_note_sets', 'lost_note_sets']}
                      for c in result['conditions']]))
