"""Replay the frozen SGC03 construction and enumerate its complete audit evidence."""

from collections import deque
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'construction'
sys.path.insert(0, str(SOURCE))
from semantic_graph_patterns import construct
from semantic_graph_probe import save
from semantic_ontology_order import augment
from semantic_ontology_comparison import compare_condition


def read(path):
    data = path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix(path.suffix + '.gz').read_bytes())
    return json.loads(data)


def verify():
    result, config = read(SOURCE / 'result.json'), read(SOURCE / 'config.json')
    repo = HERE.parents[2]
    for name, expected in config['source_hashes'].items():
        assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == expected
    for name, expected in config['frozen_sha256'].items():
        assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == expected
    base = HERE.parent / 'SGC01' / 'construction'
    inputs, graphs = read(base / 'inputs.json'), read(base / 'graphs.json')
    lexicon = read(base / 'lexicon.json')['senses']
    assert result['inputs'] == inputs and result['graphs'] == graphs
    assert result['excluded_rows'] == read(HERE.parent / 'SGC02' / 'construction' / 'result.json')['excluded_rows']
    records = [r for r in inputs if r['row'] in {g['row'] for g in graphs}]
    ontology, mappings = read(SOURCE / 'ontology.json'), read(SOURCE / 'mappings.json')
    reports = []
    for condition in result['conditions']:
        if condition['id'] == 'wordnet':
            senses = lexicon
        else:
            again = augment(lexicon, mappings, ontology, ['n'] if condition['id'] == 'nouns' else ['n', 'v'])
            assert again == condition['augmentation']
            senses = again['senses']
        assert construct(records, graphs, senses, relation_policy='connection') == condition['result']
        current = condition['result']['conditions'][1]
        patterns = {p['id']: p for p in current['patterns']}
        successors, degree = {p: [] for p in patterns}, dict.fromkeys(patterns, 0)
        for edge in current['edges']:
            parent, child = edge['parent'], edge['child']
            assert set(patterns[child]['rows']) <= set(patterns[parent]['rows'])
            assert set(patterns[child]['notes']) <= set(patterns[parent]['notes'])
            successors[parent].append(child)
            degree[child] += 1
        pending, visited = [p for p, d in degree.items() if d == 0], 0
        while pending:
            visited += 1
            for child in successors[pending.pop()]:
                degree[child] -= 1
                if degree[child] == 0:
                    pending.append(child)
        assert visited == len(patterns)
        representatives = sorted({p for g in current['recurring_groups'] for p in g['most_specific_pattern_ids']})
        report = dict(id=condition['id'], replay=True, acyclic=True, support_containment=True,
                      representatives=[patterns[p] for p in representatives])
        if condition['id'] == 'nouns_and_verbs':
            by_key = {tuple(p['key']): p['id'] for p in patterns.values()}
            def path(keys):
                waypoints = [by_key[tuple(sorted(k))] for k in keys]
                ids = [waypoints[0]]
                for start, end in zip(waypoints, waypoints[1:]):
                    queue, seen = deque([[start]]), {start}
                    while queue:
                        current_path = queue.popleft()
                        if current_path[-1] == end:
                            ids.extend(current_path[1:])
                            break
                        for child in sorted(successors[current_path[-1]]):
                            if child not in seen:
                                seen.add(child)
                                queue.append(current_path + [child])
                    else:
                        raise AssertionError(('absent path', start, end))
                return dict(patterns=[patterns[p] for p in ids], transitions=[dict(
                    parent=a, child=b, removed_notes=sorted(set(patterns[a]['notes']) - set(patterns[b]['notes'])),
                    same_note_set=patterns[a]['notes'] == patterns[b]['notes']) for a, b in zip(ids, ids[1:])])
            food, activity = ['SUMO:Food'], ['SUMO:Food', 'SUMO:IntentionalProcess']
            report['paths'] = {
                'food_activity_preservation': path([food, activity, ['SUMO:Food', 'preservation.n.01']]),
                'food_activity_preparation_bread': path([food, activity, ['SUMO:Food', 'preparation.n.01'], ['bread.n.01', 'preparation.n.01']]),
                'food_activity_preparation_steak': path([food, activity, ['SUMO:Food', 'preparation.n.01'], ['steak.n.01', 'preparation.n.01']]),
                'food_activity_cooking_brisket': path([food, activity, ['SUMO:Food', 'cook.v.01'], ['brisket.n.01', 'cook.v.01']]),
            }
        reports.append(report)
    by_name = {c['id']: c for c in result['conditions']}
    for comparison in result['comparisons']:
        before, after = comparison['before'], comparison['after']
        replay = compare_condition(by_name[before]['result']['conditions'][1],
                                   by_name[after]['result']['conditions'][1],
                                   allow_sumo_support_changes=before != 'wordnet')
        assert replay == {k: v for k, v in comparison.items() if k not in {'before', 'after'}}
    return dict(run_id='SGC03', hashes_match=True, complete_replay=True,
                source_inputs_unchanged=True, conditions=reports)


def write_records(audit):
    result = read(SOURCE / 'result.json')
    lines = ['# SGC03 candidate inventory', '',
             'Every recurring note set and its most-specific patterns is listed.',
             'These are generated pattern meanings, not approved category titles.',
             'A slash denotes a witnessed connection, with direction and role ignored.',
             'Source rows refer to [the complete masked notes](./SOURCE-EVIDENCE.md).',
             'All less-specific and one-note patterns remain in the compressed result.', '']
    for condition in audit['conditions']:
        lines += ['## ' + condition['id'], '', '| Pattern | Meaning | Notes | Source rows |', '| --- | --- | --- | --- |']
        for p in sorted(condition['representatives'], key=lambda p: (p['notes'], p['key'])):
            lines += [f"| {p['id']} | {' / '.join(p['key'])} | {' '.join(p['notes'])} | " +
                      ' '.join(f"[{row}](./SOURCE-EVIDENCE.md#row-{row})" for row in p['rows']) + ' |']
        lines += ['']
    (HERE / 'INVENTORY.md').write_text('\n'.join(lines))
    lines = ['# SGC03 source evidence', '',
             'Unchanged complete notes, masks, descriptions and native graph edges.',
             'Brackets mark the source fragments; each complete fragment list is also saved.',
             'Descriptions are frozen parser inputs, not new annotations.', '']
    graphs = {g['row']: g for g in result['graphs']}
    for record in result['inputs']:
        text, end, pieces = record['text'], 0, []
        for fragment in record['fragments']:
            start = text.find(fragment, end)
            assert start >= 0, (record['row'], fragment)
            pieces.extend([text[end:start], '⟦', fragment, '⟧'])
            end = start + len(fragment)
        pieces.append(text[end:])
        lines += [f"## Row {record['row']}", '', record['note'], '',
                  '> ' + '\n> '.join(''.join(pieces).splitlines()), '',
                  '**Frozen description:** ' + record['subject'], '',
                  '**Exact fragments:** ' + json.dumps(record['fragments'], ensure_ascii=False), '']
        if record['row'] not in graphs:
            lines += ['Native output is malformed and remains excluded.', '']
        else:
            graph = graphs[record['row']]
            nodes = {n['id']: n['sense'] for n in graph['nodes']}
            lines += ['**Native edges:**', ''] + [
                f"- {nodes[e['source']]} → {e['role']} → {nodes[e['target']]}" for e in graph['edges']] + ['']
    (HERE / 'SOURCE-EVIDENCE.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    audit = verify()
    save(HERE / 'audit.json', audit)
    write_records(audit)
    print(json.dumps(dict(replay=audit['complete_replay'], representatives={c['id']:len(c['representatives']) for c in audit['conditions']})))
