"""Experimental complete tree from a frozen six-section numerical panel.

Finish at the inherited intact groups when at most six remain. Larger pools
receive one local reciprocal/frozen-attachment pass and, if still necessary,
the unchanged six-section fit. This does not generate canonical definitions,
activate HiGen behavior, or specify review-UI note display.
"""
import argparse
from collections import Counter, deque
from pathlib import Path

import numpy as np

from . import direct_section_partition as direct
from . import section_count_panel as panel


def _root(directory, case_id):
    path = Path(directory).resolve() / 'plan.json'
    plan = panel._read(path)
    panel._check_files(plan['code_files'])
    cfg = next((c for c in plan['cases'] if c['id'] == case_id), None)
    if (cfg is None or 6 not in cfg['counts'] or not cfg.get('preserve_groups')
            or not cfg.get('reciprocal_nearest') or not cfg.get('attach_nearest')
            or cfg['minimum_notes'] != 0):
        raise ValueError('A frozen whole-group six-section reciprocal/attachment case is required')
    panel._check_files(cfg.get('grouping_files', {}))
    vectors, notes, entries = panel._load_source(plan['spec']['sources'][cfg['source']])
    indices = np.asarray(cfg['indices'])
    if (indices.ndim != 1 or indices.dtype.kind not in 'iu'
            or len(set(indices)) != len(indices) or not len(indices)
            or indices.min() < 0 or indices.max() >= len(notes)
            or [entries[i]['id'] for i in indices] != cfg['entry_ids']):
        raise ValueError('Invalid original row mapping in root case')
    result = path.parent / case_id / 'count-6.json'
    saved = panel._read(result)
    if saved['binding'] != dict(plan_sha256=panel._sha(path), case_id=case_id, count=6):
        raise ValueError('Root result has different frozen bindings')
    panel._verify(saved['panel'], vectors[indices], notes[indices], 6, 0,
                  plan['spec']['seeds'], cfg['groups'])
    return plan, cfg, vectors, notes, entries, saved['panel']


def prepare(directory, case_id, output, *, corpus_notes, minimum_root_notes):
    if (type(corpus_notes) is not int or corpus_notes < 1
            or type(minimum_root_notes) is not int or minimum_root_notes < 0):
        raise ValueError('Positive original-corpus size and nonnegative root minimum required')
    directory, output = Path(directory).resolve(), Path(output).resolve()
    root, cfg, _, notes, _, _ = _root(directory, case_id)
    if len(set(notes[cfg['indices']])) > corpus_notes:
        raise ValueError('Covered notes exceed the original corpus size')
    files = {str(directory / name): panel._sha(directory / name)
             for name in ['plan.json', f'{case_id}/count-6.json']}
    plan = dict(status='Frozen complete numerical research construction; no HiGen activation',
                root_panel=str(directory), case_id=case_id, files=files,
                corpus_notes=corpus_notes, minimum_root_notes=minimum_root_notes,
                max_children=6, seeds=root['spec']['seeds'],
                max_iterations=root['spec']['max_iterations'], time_limit=root['spec']['time_limit'],
                stopping='Expose at most six inherited groups before another matching pass; '
                         'one group is already a leaf. No separate one-note stopping condition.',
                code_files={str(Path(p).resolve()): panel._sha(p)
                            for p in [__file__, panel.__file__, direct.__file__]})
    output.mkdir(parents=True, exist_ok=False)
    panel._write(output / 'plan.json', plan)
    return plan


def _number(groups):
    identifiers = {}
    return [identifiers.setdefault(int(g), len(identifiers)) for g in groups]


def _fit(output, plan, binding, vectors, notes, groups):
    path = output / 'fits' / (binding['node'] + '.json')
    if path.exists():
        saved = panel._read(path)
        if saved['binding'] != binding:
            raise ValueError('Completed partition has different frozen bindings')
        result = saved['panel']
    else:
        trials = [direct.partition(vectors, notes, sections=6, minimum_notes=0,
                  seed=seed, max_iterations=plan['max_iterations'],
                  time_limit=plan['time_limit'], groups=groups) for seed in plan['seeds']]
        result = dict(best=min(trials, key=lambda t: (t['objective'], t['seed'])), trials=trials)
    panel._verify(result, vectors, notes, 6, 0, plan['seeds'], groups)
    if not path.exists():
        panel._write(path, dict(binding=binding, panel=result))
    return result


def _summary(nodes, roots, plan):
    by_id = {n['id']: n for n in nodes}
    leaves = [n for n in nodes if not n['children']]
    covered = set(nodes[0]['note_ids'])
    rows = [i for n in leaves for i in n['indices']]
    if sorted(rows) != nodes[0]['indices']:
        raise ValueError('Leaf assignments must partition the original selected rows exactly once')
    non_narrowing, duplicate_menus = [], []
    for node in nodes:
        children = [by_id[c] for c in node['children']]
        if children and sorted(i for c in children for i in c['indices']) != node['indices']:
            raise ValueError('Children do not partition their original parent rows')
        for child in children:
            if not set(child['note_ids']) < set(node['note_ids']):
                non_narrowing.append([node['id'], child['id']])
        if len({tuple(c['note_ids']) for c in children}) < len(children):
            duplicate_menus.append(node['id'])
    per_note = []
    for note in sorted(covered):
        choices = [n for n in leaves if note in n['note_ids']]
        depths = [n['depth'] for n in choices]
        per_note.append(dict(note_id=note, shortest_leaf_depth=min(depths),
                             longest_leaf_depth=max(depths),
                             leaves=[n['id'] for n in choices]))
    shortest = [p['shortest_leaf_depth'] for p in per_note]
    unresolved = [n['id'] for n in nodes if n['mode'] == 'unresolved']
    root_counts = [by_id[r]['notes'] for r in roots]
    return dict(covered_notes=len(covered), original_corpus_notes=plan['corpus_notes'],
                coverage=len(covered) / plan['corpus_notes'],
                entries=len(rows), roots=len(roots), root_notes=root_counts,
                nodes=len(nodes) - 1, leaves=len(leaves),
                max_children=max(len(n['children']) for n in nodes),
                max_leaf_depth=max(n['depth'] for n in leaves),
                shortest_leaf_depth=dict(mean=float(np.mean(shortest)),
                     median=float(np.median(shortest)), p90=float(np.quantile(shortest, .9))),
                route_measure='Structural category edges only; no claim about actual user effort',
                non_narrowing_edges=non_narrowing, duplicate_note_set_menus=duplicate_menus,
                unresolved_nodes=unresolved, per_note=per_note,
                quality_requirements_pass=(not unresolved and not non_narrowing
                    and len(covered) >= .9 * plan['corpus_notes']
                    and min(root_counts) >= plan['minimum_root_notes']))


def run(output):
    output = Path(output).resolve()
    plan_path = output / 'plan.json'
    plan = panel._read(plan_path)
    panel._check_files(plan['files'])
    panel._check_files(plan['code_files'])
    root, cfg, vectors, notes, entries, root_fit = _root(plan['root_panel'], plan['case_id'])
    if (plan['seeds'] != root['spec']['seeds'] or plan['max_children'] != 6
            or plan['max_iterations'] != root['spec']['max_iterations']
            or plan['time_limit'] != root['spec']['time_limit']):
        raise ValueError('Tree settings disagree with the frozen root panel')
    (output / 'fits').mkdir(exist_ok=True)
    queue = deque([('0', 0, np.array(cfg['indices']), cfg['groups'])])
    nodes = []
    while queue:
        identifier, depth, indices, inherited = queue.popleft()
        groups = _number(inherited)
        inherited_count = len(set(groups))
        local, local_notes = vectors[indices], notes[indices]
        pairs, attachments, matching = [], [], False
        if identifier != '0' and inherited_count > 6:
            groups, pairs, attachments = panel._reciprocal_groups(local, groups, attach_nearest=True)
            matching = True
        count = len(set(groups))
        fitted = None
        if count == 1:
            mode, labels = 'leaf', None
        elif count <= 6:
            mode, labels = 'direct_groups', np.array(groups)
        else:
            binding = dict(plan_sha256=panel._sha(plan_path), node=identifier,
                           indices=indices.tolist(), groups=groups)
            fitted = root_fit if identifier == '0' else _fit(output, plan, binding, local, local_notes, groups)
            mode, labels = 'partition', np.array(fitted['best']['labels'])
            if len(set(labels)) < 2:
                mode, labels = 'unresolved', None
        children = []
        if labels is not None:
            for number, label in enumerate(sorted(set(labels)), 1):
                child = str(number) if identifier == '0' else identifier + '.' + str(number)
                selected = labels == label
                child_indices = indices[selected]
                if len(child_indices) >= len(indices):
                    raise ValueError('Subdivision must reduce original entry rows')
                queue.append((child, depth + 1, child_indices, np.array(groups)[selected].tolist()))
                children.append(child)
        titles = Counter(entries[i]['title'] for i in indices)
        nodes.append(dict(id=identifier, depth=depth, indices=indices.tolist(),
            entry_ids=[entries[i]['id'] for i in indices],
            note_ids=sorted(set(local_notes.tolist())), notes=len(set(local_notes)),
            headings=[dict(title=title, entries=n) for title, n in titles.most_common()],
            inherited_group_count=inherited_count, final_group_count=count,
            groups=groups, matching_applied=matching, reciprocal_pairs=pairs,
            nearest_attachments=attachments, mode=mode, children=children,
            fit=None if fitted is None else dict(seed=fitted['best']['seed'],
                objective=fitted['best']['objective'],
                converged_trials=sum(t['converged'] for t in fitted['trials']),
                trials=len(fitted['trials']), reused_root_panel=identifier == '0')))
    roots = nodes[0]['children']
    if not roots:
        raise ValueError('The supplied root panel did not create root choices')
    result = dict(status='Completed numerical research tree; semantic quality requires review',
                  plan_sha256=panel._sha(plan_path), roots=roots, nodes=nodes,
                  summary=_summary(nodes, roots, plan))
    path = output / 'tree.json'
    if path.exists():
        if panel._read(path) != result:
            raise ValueError('Completed tree differs from validated frozen construction')
    else:
        panel._write(path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('panel', type=Path)
    prep.add_argument('case')
    prep.add_argument('output', type=Path)
    prep.add_argument('--corpus-notes', type=int, required=True)
    prep.add_argument('--minimum-root-notes', type=int, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.panel, args.case, args.output, corpus_notes=args.corpus_notes,
                         minimum_root_notes=args.minimum_root_notes)
        print(result['status'])
    else:
        result = run(args.output)
        print({k: v for k, v in result['summary'].items() if k != 'per_note'})


if __name__ == '__main__':
    main()
