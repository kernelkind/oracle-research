"""Observe raw-node and unchanged-note-set durations; no semantic filtering.

Adjacent nodes with equal note sets are combined only for this measurement.
The native tree is unchanged. Duration is conditional on this run's clock,
not H0 barcode lifetime, semantic confidence, or an automatic retention rule.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from geometric_experiment import write_json

results = {}
for run in ['GDC02', 'GDC07', 'GDC08', 'GDC09']:
    tree = json.loads((ROOT/run/'hierarchy.json').read_text())
    nodes = {n['id']: n for n in tree['nodes']}
    parents = {c: n['id'] for n in tree['nodes'] for c in n['children']}
    representatives = {i: i for i in nodes}

    def find(i):
        while representatives[i] != i:
            representatives[i] = representatives[representatives[i]]
            i = representatives[i]
        return i

    for i, parent in parents.items():
        if nodes[i]['note_ids'] == nodes[parent]['note_ids']:
            a, b = find(i), find(parent)
            representatives[max(a, b)] = min(a, b)
    components = {}
    for i in nodes:
        components.setdefault(find(i), []).append(i)
    records = []
    growth = [h['iteration'] for h in tree['stats']['history']
              if h['epsilon'] != h['next_epsilon']]
    for members in components.values():
        member_set = set(members)
        top = [i for i in members if parents.get(i) not in member_set]
        assert len(top) == 1
        top = top[0]
        note_ids = nodes[top]['note_ids']
        assert all(nodes[i]['note_ids'] == note_ids for i in members)
        assert all(parents[i] in member_set for i in members if i != top)
        birth = min(nodes[i]['iteration'] for i in members)
        parent = parents.get(top)
        death = nodes[parent]['iteration'] if parent is not None else None
        observed_end = death if death is not None else tree['stats']['steps']
        records.append(dict(
            native_nodes=sorted(members), top_node=top, note_ids=note_ids,
            first_birth=birth, next_different_note_parent=parent,
            next_different_note_parent_birth=death,
            duration=death-birth if death is not None else None,
            observed_duration_lower_bound=observed_end-birth,
            crosses_bandwidth_change=any(birth <= t < observed_end for t in growth),
            raw_node_durations={str(i): nodes[parents[i]]['iteration']-nodes[i]['iteration']
                                if i in parents else None for i in members}))
    assert sum(len(r['native_nodes']) for r in records) == len(nodes)
    results[run] = records

known = [1487, 1598, 1401, 1419, 1533, 1557, 1574, 1629, 1671, 1693,
         1700, 1665, 1686, 1751]
selected = {str(i): next(r for r in results['GDC09'] if i in r['native_nodes'])
            for i in known}
# Independently checked edge intervals and unchanged coffee note membership.
assert selected['1487']['duration'] == 129
assert selected['1487']['raw_node_durations']['1487'] == 8
assert selected['1419']['duration'] == 1
assert selected['1665']['duration'] == 2287
assert selected['1751']['duration'] == 1
write_json(ROOT/'note-set-duration.json', dict(
    diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    definition='Connected components of native edges with identical note sets; interval from earliest member birth to birth of first different-note-set parent. Root intervals are censored. No nodes removed from native results.',
    warning='Iterations are not calibrated semantic confidence or directly comparable across changed dynamics. Selection examples were semantically reviewed before consulting duration.',
    reviewed_GDC09_examples=selected, all_runs=results))
for i, r in selected.items():
    print(i, 'raw', r['raw_node_durations'][i], 'note_set', r['duration'],
          'notes', len(r['note_ids']), 'component', r['native_nodes'],
          'bandwidth_change', r['crosses_bandwidth_change'])
print('Longest unchanged multi-note sets, excluding censored roots:')
for r in sorted((r for r in results['GDC09'] if len(r['note_ids']) > 1
                 and r['duration'] is not None), key=lambda r: -r['duration'])[:20]:
    print(r['top_node'], r['duration'], len(r['note_ids']), r['note_ids'])
