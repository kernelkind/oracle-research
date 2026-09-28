"""Render saved original/title/mask merge choices in the existing hierarchy UI.

Offline only. Validate native experiment receipts, compare the same original
edges, retain untested edges, and never overwrite a source or an earlier export.
"""
import argparse
from copy import deepcopy
import hashlib
from pathlib import Path

from category_mask_instances import reconstruct
from experiment import load, report
from hierarchy_build import artifact_directory, read, save
from merge_tree_nesting import (
    _contract_judged_edges, contract, validate_decisions, validate_equivalence_decisions,
)
from true_graph_categories import render_categories
from true_graph_notes import derive_note_memberships


def descendants(edges, root):
    children = {}
    for a, b in edges:
        children.setdefault(a, []).append(b)
    reached, pending = set(), [root]
    while pending:
        group = pending.pop()
        if group in reached:
            raise ValueError('comparison requires a tree with distinct branches')
        reached.add(group)
        pending.extend(children.get(group, []))
    return reached


def render_comparison(tree, titles, branches, directed, equivalent, source, mapping,
                      *, label, assessments=None):
    root = tree['root']
    edges = {(a, b) for a, b in tree['edges'] if a != root}
    if not equivalent or not set(equivalent) <= edges:
        raise ValueError('mask decisions must identify original edges')
    if any(v not in {'yes', 'no', 'uncertain'} for v in equivalent.values()):
        raise ValueError('invalid native equivalence choice')
    branch_roots = [b['root'] for b in branches]
    if (len(set(branch_roots)) != len(branch_roots)
            or set(branch_roots) != {b for a, b in tree['edges'] if a == root}
            or descendants(tree['edges'], root) != set(tree['members'])):
        raise ValueError('branches must cover the complete comparison tree')
    if set(titles) != set(tree['members']) - {root}:
        raise ValueError('exact saved title inventory required')
    native = {(j['parent'], j['child']): j for j in contract(tree, directed)['judgments']}
    title_judgments, mask_judgments = {}, {}
    for a, b in edges:
        untested = dict(parent=a, child=b, status='untested')
        title_judgments[a, b] = native[a, b] if (a, b) in equivalent else untested
        mask_judgments[a, b] = (
            dict(parent=a, child=b, same_topic=equivalent[a, b],
                 status={'yes':'equivalent', 'no':'distinct', 'uncertain':'uncertain'}[equivalent[a, b]])
            if (a, b) in equivalent else untested)
    projections = {
        'original': dict(root=root, edges=deepcopy(tree['edges']),
                         members=deepcopy(tree['members']),
                         representative={g:g for g in tree['members']}, judgments=[]),
        'title': _contract_judged_edges(tree, title_judgments),
        'mask': _contract_judged_edges(tree, mask_judgments),
    }
    nodes, packets, links, analyses = [], [], [], {}

    def add(key, title, masks=(), analysis=''):
        instances = [tree['instances'][m] for m in masks]
        nodes.append(dict(group=key, title=title, instances=[
            dict(instance=i['instance'], fragments=i['fragments']) for i in instances]))
        packets.append(dict(packet=key, instances=instances))
        analyses[key] = analysis

    notice = ('Saved mask-set nesting, not validated semantic parent placement. '
              'Only the same tested original pairs may merge in either method. '
              'Untested links remain separate; no additional browser collapsing. ')
    for mode, projection in projections.items():
        for group, masks in projection['members'].items():
            if group == root:
                continue
            originals = [g for g, rep in projection['representative'].items() if rep == group]
            detail = [notice, f'{len(originals)} original group(s): ' +
                      ', '.join(titles[g] for g in originals) + '.']
            judgments = projection['judgments'] if mode != 'original' else list(mask_judgments.values())
            for j in judgments:
                if projection['representative'][j['child']] != group:
                    continue
                pair = f'{titles[j["parent"]]} / {titles[j["child"]]}'
                if j['status'] == 'untested':
                    detail.append(f'Untested original link: {pair}; kept in both methods.')
                elif mode == 'title':
                    detail.append(f'Titles: {pair}; forward {j["forward"]}, reverse {j["reverse"]}; {j["status"]}.')
                else:
                    detail.append(f'Masks: {pair}; same_topic {j["same_topic"]}; {j["status"]}.' +
                                  (' Original view does not apply this decision.' if mode == 'original' else ''))
                for review in (assessments or {}).get((j['parent'], j['child']), []):
                    detail.append('Agent assessment of the mask-based answer (not a user verdict): ' + review)
            add(f'{mode}:{group}', titles[group], masks, '\n'.join(detail))
        links += [(f'{mode}:{a}', f'{mode}:{b}') for a, b in projection['edges'] if a != root]

    focused, other, counts = [], [], []
    for i, branch in enumerate(branches):
        groups = descendants(tree['edges'], branch['root'])
        total = sum(a in groups for a, _ in edges)
        tested = sum(a in groups for a, _ in equivalent)
        menu = f'branch:{i}'
        (focused if branch.get('focus', False) else other).append(menu)
        add(menu, branch['label'], analysis=notice +
            'Choose a view. ? on a node shows saved decisions and agent comments. '
            'N: all posts; D: direct posts; O: masks outside children, with IDs.')
        row = dict(branch=branch['label'], tested=tested, pairs=total)
        for mode, title in [('original','Original groups'), ('title','Title-based merges'),
                            ('mask','Mask-based merges')]:
            count = len({projections[mode]['representative'][g] for g in groups})
            row[mode] = count
            key = f'{menu}:{mode}'
            title = f'{title} — {count} groups' + (f' · {tested}/{total} pairs tested' if mode != 'original' else '')
            add(key, title, analysis=notice)
            links += [(menu, key), (key, f'{mode}:{branch["root"]}')]
        counts.append(row)
    if other:
        add('other', 'Other tested topics', analysis=notice)
        links += [('other', key) for key in other]
        focused.append('other')
    reach = {n['group']:sorted(descendants(links, n['group']) - {n['group']}) for n in nodes}
    graph = dict(nodes=nodes, roots=focused, reachability=reach,
                 transitive_reduced_edges=[dict(a_id=a, b_id=b) for a, b in links])
    memberships = derive_note_memberships(graph, dict(packets=packets))
    result = render_categories(graph, memberships, source, mapping, hierarchy_id=label,
                               connection_description=notice)
    result = reconstruct(result, memberships, [], Path(source).read_bytes())
    for node in result['nodes']:
        if node['node_id'] == 'root':
            node['label'] = 'Saved merge comparison'
            node['analysis'] = notice + 'These topic and view menus are navigation only, not generated hierarchy nodes.'
        else:
            node['analysis'] = analyses[node['node_id']]
    return result, dict(branches=counts, projections=projections,
                        compared_pairs=len(equivalent), untested_pairs=len(edges)-len(equivalent))


def export(spec_path, output):
    spec_path = Path(spec_path).resolve()
    spec = read(spec_path)
    if spec['schema_version'] != 1:
        raise ValueError('expected comparison schema version 1')
    hashes = {str(spec_path): hashlib.sha256(spec_path.read_bytes()).hexdigest()}

    def path(value):
        return (spec_path.parent / value).resolve()

    def document(value):
        p = path(value)
        hashes[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        return read(p)

    datasets = {}
    for name, entry in spec['datasets'].items():
        tree, titles, packets = [document(entry[k]) for k in ('tree','titles','packets')]
        plan, _, _ = load(path(entry['title_experiment']))
        decisions = validate_decisions(tree, titles, report(path(entry['title_experiment'])), plan['prompt'])
        datasets[name] = dict(tree=tree, titles=titles, packets=packets, decisions=decisions)
    equivalent, assessments = {}, {}
    for entry in spec['mask_tests']:
        tree = document(entry['tree'])
        packets = dict(packets=[p for name in entry['datasets'] for p in datasets[name]['packets']['packets']])
        plan, _, _ = load(path(entry['experiment']))
        r = report(path(entry['experiment']))
        choices = validate_equivalence_decisions(tree, packets, r, plan['prompt'])
        if set(choices) & set(equivalent):
            raise ValueError('repeated mask decision')
        equivalent.update(choices)
        for c in r['cases']:
            pair = c['evidence']['original_a_id'], c['evidence']['original_b_id']
            assessments[pair] = [v['comment'] for v in c['reviews']
                                 if v['role']=='agent' and v['verdict'] in {'reject','uncertain'}]
    combined = dict(root='comparison-root', edges=[], members={}, instances={})
    titles, directed, branches = {}, {}, []
    for branch in spec['branches']:
        data = datasets[branch['dataset']]
        groups = descendants(data['tree']['edges'], branch['root'])
        if set(combined['members']) & groups:
            raise ValueError('overlapping comparison branches')
        packets = {p['packet']:p for p in data['packets']['packets']}
        for g in sorted(groups):
            combined['members'][g] = data['tree']['members'][g]
            if set(combined['members'][g]) != {i['instance'] for i in packets[g]['instances']}:
                raise ValueError('saved packet membership changed')
            titles[g] = data['titles'][g]
            for instance in packets[g]['instances']:
                old = combined['instances'].get(instance['instance'])
                if old is not None and old != instance:
                    raise ValueError('conflicting source mask')
                combined['instances'][instance['instance']] = instance
        combined['edges'].append([combined['root'], branch['root']])
        for a, b in data['tree']['edges']:
            if a in groups and b in groups:
                combined['edges'].append([a,b])
                for pair in ((a,b),(b,a)):
                    directed[pair] = data['decisions'][pair]
        branches.append(branch)
    combined['members'][combined['root']] = sorted(combined['instances'])
    source, mapping = path(spec['source']), path(spec['mapping'])
    for p in (source, mapping):
        hashes[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    categories, evidence = render_comparison(combined, titles, branches, directed, equivalent,
                                             source, mapping, label=spec['id'], assessments=assessments)
    evidence['input_sha256'] = hashes
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):
        raise ValueError('input changed while packaging comparison')
    out = artifact_directory(output)
    save(out/'categories.json', categories)
    save(out/'verification.json', evidence)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = export(args.spec, args.output)
    print(f'{len(result["branches"])} topics; {result["compared_pairs"]} tested pairs; '
          f'{result["untested_pairs"]} untested links kept separate. No inference.')


if __name__ == '__main__':
    main()
