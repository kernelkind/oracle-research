"""Experimental full-tree epsilon review of saved native HDBSCAN results.

This makes no model requests and does not activate a construction policy.
Selected groups stay fixed; the 10%-trimmed bend determines only the display cut.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
from html import escape
import json
import math
from pathlib import Path
import subprocess

from . import hierarchy_hdbscan as hdbscan
from .hierarchy_generation import _vectors, check_state


def project(response, request, mapping):
    """Project the original condensed tree onto the fixed selected groups."""
    groups = hdbscan.members(response, request, mapping)
    # Use the native validator without imposing its ordinary six-way cut.
    hdbscan.section_plan(response, request, mapping, max(1, len(groups)))
    if not groups:
        raise ValueError('no selected HDBSCAN groups')
    algorithm = response['artifact']['result']['algorithm_result']
    count = algorithm['vector_count']
    selected = {c['id']: i + 1 for i, c in enumerate(algorithm['clusters'])}
    parents, children = {}, defaultdict(list)
    for edge in algorithm['condensed_tree']:
        parents[edge['child']] = (edge['parent'], edge['lambda'])
        if edge['child'] >= count:
            children[edge['parent']].append(edge['child'])
    needed = {count}
    for node in selected:
        while node not in needed:
            needed.add(node)
            node = parents[node][0]
    order, pending = [], [count]
    while pending:
        node = pending.pop()
        order.append(node)
        pending.extend(c for c in children[node] if c in needed)
    nodes, representative = {}, {}
    for node in reversed(order):
        below = [representative[c] for c in children[node] if c in needed]
        if node in selected:
            nodes[node] = dict(node=node, groups=[selected[node]], children=[])
        elif len(below) == 1:
            representative[node] = below[0]
            continue
        else:
            below.sort(key=lambda c: min(nodes[c]['groups']))
            nodes[node] = dict(node=node, children=below,
                               groups=sorted(g for c in below for g in nodes[c]['groups']),
                               distance=1 / parents[next(c for c in children[node]
                                                         if c in needed)][1])
        representative[node] = node
    return dict(root=representative[count], nodes=list(nodes.values()))


def curve(tree):
    splits = defaultdict(int)
    for node in tree['nodes']:
        if node['children']:
            splits[node['distance']] += len(node['children']) - 1
    distances = sorted(splits, reverse=True)
    points, count = [], 1
    for i, distance in enumerate(distances):
        count += splits[distance]
        following = distances[i + 1] if i + 1 < len(distances) else 0
        points.append(dict(distance=distance, following_distance=following,
                           section_count=count, midpoint=(distance + following) / 2))
    return points


def select_epsilon(tree):
    points = curve(tree)
    trim = math.ceil(.10 * len(points))
    retained = points[trim:len(points) - trim]
    if len(retained) < 3:
        raise ValueError('candidate needs at least three retained distance levels')
    first, last = retained[0], retained[-1]
    scored = []
    for point in retained:
        x = ((point['section_count'] - first['section_count']) /
             (last['section_count'] - first['section_count']))
        y = ((first['distance'] - point['distance']) /
             (first['distance'] - last['distance']))
        scored.append(dict(point, score=x-y))
    best = max(scored, key=lambda p: (p['score'], -p['section_count']))
    if best['score'] <= 0:
        raise ValueError('candidate needs a positive bend; no fallback is defined')
    return dict(rule='trimmed-bend-10-percent-v1', epsilon=best['midpoint'],
                omitted_levels_per_end=trim, selected_point=best,
                fitted_points=scored, curve=points)


def partition(tree, epsilon):
    nodes = {n['node']: n for n in tree['nodes']}
    sections, pending = [], [tree['root']]
    while pending:
        node = nodes[pending.pop()]
        if not node['children'] or node['distance'] <= epsilon:
            sections.append(node)
        else:
            pending.extend(reversed(node['children']))
    return sections


def render_svg(tree, sections, groups, epsilon, *, title, provenance):
    nodes = {n['node']: n for n in tree['nodes']}
    by_group = {g['id']: g for g in groups}
    section_ids = {g: i for i, s in enumerate(sections) for g in s['groups']}
    colors = [f'hsl({(i * 137.508) % 360:.1f},65%,36%)' for i in range(len(sections))]
    top = 150 + 34 * math.ceil(len(sections) / 3)
    stride, left, right, width = 40, 64, 930, 1710
    order, pending = [], [tree['root']]
    while pending:
        node = nodes[pending.pop()]
        if node['children']:
            pending.extend(reversed(node['children']))
        else:
            order.extend(node['groups'])
    bottom = top + stride * (len(order)-1)
    height = bottom + 110
    max_distance = math.ceil(max(n.get('distance', 0) for n in nodes.values()) * 5) / 5
    x = lambda d: left + (right-left) * (1-d/max_distance)
    ys = {g: top + i*stride for i, g in enumerate(order)}
    centers = {k: (min(ys[g] for g in n['groups']) + max(ys[g] for g in n['groups']))/2
               for k, n in nodes.items()}
    cut_x = x(epsilon)
    metadata = dict(provenance, epsilon=epsilon,
                    sections=[dict(id=f'S{i+1:02d}', groups=s['groups'], color=colors[i])
                              for i, s in enumerate(sections)])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             '<style>text{font-family:Arial,sans-serif}path,line{fill:none}</style>',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<metadata>'+escape(json.dumps(metadata, ensure_ascii=False))+'</metadata>',
             f'<text x="28" y="34" font-size="22" font-weight="bold">{escape(title)}</text>',
             f'<text x="28" y="59" font-size="14">{len(groups)} fixed groups · '
             f'{len(sections)} sections · automatic ε = {epsilon:.6f} · group membership unchanged</text>']
    for i, section in enumerate(sections):
        col, row = i % 3, i // 3
        label = ', '.join(f'G{g:02d}' for g in section['groups'])
        if len(label) > 67:
            label = label[:64]+'…'
        parts.append(f'<text x="{28+col*555}" y="{88+row*34}" font-size="13" '
                     f'fill="{colors[i]}"><title>{escape(str(section["groups"]))}</title>'
                     f'S{i+1:02d} · {label}</text>')
    parts.append(f'<line x1="{left}" y1="{top-30}" x2="{right}" y2="{top-30}" stroke="#777"/>')
    for i in range(7):
        d = max_distance*i/6
        parts.append(f'<text x="{x(d):.2f}" y="{top-42}" text-anchor="middle" font-size="11">{d:.2f}</text>')
    for name, y, target in [('top', top-27, top-7), ('bottom', bottom+32, bottom+12)]:
        sign = 1 if name == 'top' else -1
        parts.append(f'<g id="cutoff-arrow-{name}"><path d="M {cut_x:.2f},{y} V {target} '
                     f'M {cut_x-5:.2f},{target-7*sign} L {cut_x:.2f},{target} '
                     f'L {cut_x+5:.2f},{target-7*sign}" stroke="#151515" stroke-width="2"/></g>')
    for g in order:
        color = colors[section_ids[g]]
        parts.append(f'<rect x="{left-5}" y="{ys[g]-17}" width="{width-left-25}" '
                     f'height="34" fill="{color}" opacity="0.035"/>')
    for key, node in nodes.items():
        if not node['children']:
            continue
        nx, ny = x(node['distance']), centers[key]
        color = colors[section_ids[node['groups'][0]]] if node['distance'] <= epsilon else '#a8adb4'
        children = node['children']
        parts.append(f'<path data-parent="{key}" d="M {nx:.3f},{min(centers[c] for c in children):.3f} '
                     f'V {max(centers[c] for c in children):.3f}" stroke="{color}" stroke-width="2"/>')
        for child in children:
            cx, cy = x(nodes[child].get('distance', 0)), centers[child]
            endpoint_color = colors[section_ids[nodes[child]['groups'][0]]]
            if nx < cut_x < cx:
                parts.append(f'<path d="M {nx:.3f},{cy:.3f} H {cut_x:.3f}" stroke="#a8adb4" stroke-width="2"/>')
                nx2, edge_color = cut_x, endpoint_color
            else:
                nx2, edge_color = nx, color
            parts.append(f'<path data-child="{child}" d="M {nx2:.3f},{cy:.3f} H {cx:.3f}" '
                         f'stroke="{edge_color}" stroke-width="2"/>')
    for g in order:
        info, i = by_group[g], section_ids[g]
        names = '; '.join(info['titles'])
        short = names if len(names) <= 80 else names[:77]+'…'
        tip = f'G{g:02d}: {names} | {info["entries"]} entries | {info["notes"]} notes'
        parts.append(f'<text data-group="G{g:02d}" x="{right+14}" y="{ys[g]+5}" '
                     f'font-size="14" fill="{colors[i]}"><title>{escape(tip)}</title>'
                     f'G{g:02d} · S{i+1:02d} · {escape(short)} · {info["notes"]} notes</text>')
    parts.append(f'<text x="28" y="{bottom+70}" font-size="13">'
                 'Gray joins connect different sections. Colored branches belong to one section. '
                 'Hover over a group for its complete entry titles.</text></svg>')
    return '\n'.join(parts)+'\n'


def group_review(response, request, mapping, state, provenance):
    tree = project(response, request, mapping)
    selection = select_epsilon(tree)
    sections = partition(tree, selection['epsilon'])
    originals = {o['id']: o for o in state['originals']}
    groups = []
    for index, members in enumerate(hdbscan.members(response, request, mapping), 1):
        titles = Counter(state['items'][i]['subject'] for i in members)
        note_ids = sorted({originals[i]['local']['note_id'] for i in members})
        groups.append(dict(id=index, original_ids=members, entries=len(members),
                           titles=[f'{t} ({n})' if n>1 else t for t, n in titles.items()],
                           notes=len(note_ids), note_ids=note_ids))
    covered = {n for g in groups for n in g['note_ids']}
    return dict(provenance=provenance, tree=tree, selection=selection,
                sections=sections, groups=groups, input_notes=len(state['note_ids']),
                represented_notes=len(covered),
                omitted_note_ids=sorted(set(state['note_ids'])-covered))


def saved_review(state_path):
    state_path = Path(state_path).resolve()
    state = json.loads(state_path.read_text())
    check_state(state, verify_current_code=False)
    round_ = state['families'][0]['rounds'][0]
    ids = round_['current']
    vectors = _vectors(state, ids)
    hdbscan.check_round(state, state['families'][0], round_, vectors)
    request, mapping = hdbscan.request_for(state, ids, vectors)
    evidence = round_['hdbscan']
    response = json.loads(Path(evidence['result']).read_text())
    provenance = dict(state_path=str(state_path),
                      state_sha256=hashlib.sha256(state_path.read_bytes()).hexdigest(),
                      **evidence, configuration=request['hdbscan_configuration'])
    return group_review(response, request, mapping, state, provenance)


def combine_sources(states, notes_per_source):
    """Select original L1s by note, retaining their native meanings and vectors."""
    if type(notes_per_source) is not int or notes_per_source < 1 or not states:
        raise ValueError('notes per source must be a positive integer')
    combined = dict(generation_policy='hierarchy-generation-v4.1',
                    note_ids=[], originals=[], items={})
    vectors, selections, identity = [], [], None
    for index, state in enumerate(states, 1):
        check_state(state, verify_current_code=False)
        if not state['experiments'][0].get('complete'):
            raise ValueError('source Bootstrap is incomplete')
        bootstrap = state['bootstrap_spec']
        controls = dict(
            prompt_id=bootstrap['prompt']['id'],
            prompt_sha256=hashlib.sha256(Path(bootstrap['prompt']['path']).read_bytes()).hexdigest(),
            runner={k: v for k, v in bootstrap['runner'].items()
                    if k not in {'runner_binary', 'auth_file'}},
            encoder={k: state['worker_config'][k] for k in
                     ['checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model']})
        if controls['prompt_id'] != 'Hierarchy-bootstrap-v133':
            raise ValueError('source must use Bootstrap-v133 titles and meanings')
        if identity is not None and controls != identity:
            raise ValueError('source Bootstrap or encoder controls differ')
        identity = controls
        if len(state['note_ids']) < notes_per_source:
            raise ValueError('not enough notes in source')
        note_ids = state['note_ids'][:notes_per_source]
        if set(note_ids) & set(combined['note_ids']):
            raise ValueError('overlapping note IDs across sources')
        selected = set(note_ids)
        originals = [o for o in state['originals'] if o['local']['note_id'] in selected]
        valid = [o for o in originals if o.get('meaning') is not None]
        for original in valid:
            source_id = original['id']
            identifier = f'S{index:02d}-{source_id}'
            combined['originals'].append(dict(id=identifier, local=original['local']))
            combined['items'][identifier] = {
                k: state['items'][source_id][k] for k in ['subject', 'meaning', 'vector_key']}
        vectors.extend(_vectors(state, [o['id'] for o in valid]))
        combined['note_ids'].extend(note_ids)
        selections.append(dict(note_ids=note_ids, original_entries=len(originals),
                               encoded_entries=len(valid), controls=controls,
                               source_ids=[o['id'] for o in valid],
                               skipped=[dict(id=o['id'], subject=o['subject'], local=o['local'])
                                        for o in originals if o.get('meaning') is None]))
    return combined, vectors, selections


def source_review(state_paths, notes_per_source, output):
    """Recluster verified saved vectors; no teacher or encoder execution."""
    output = Path(output).resolve()
    paths = [Path(p).resolve() for p in state_paths]
    states = [json.loads(p.read_text()) for p in paths]
    combined, vectors, selections = combine_sources(states, notes_per_source)
    binaries = [Path(s['hdbscan_binary']).resolve() for s in states]
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in binaries]
    if len(set(hashes)) != 1:
        raise ValueError('source HDBSCAN executables differ')
    ids = list(combined['items'])
    request, mapping = hdbscan.request_for(combined, ids, vectors)
    provenance = dict(sources=[dict(state_path=str(p),
                                   state_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                                   selection=selection)
                              for p, selection in zip(paths, selections, strict=True)],
                      hdbscan_binary=str(binaries[0]), hdbscan_binary_sha256=hashes[0],
                      configuration=request['hdbscan_configuration'],
                      new_model_calls=0, new_encodings=0)
    output.mkdir(parents=True, exist_ok=False)
    (output/'sources.json').write_text(json.dumps(provenance, indent=2)+'\n')
    request_path = output/'request.json'
    request_path.write_text(json.dumps(request, ensure_ascii=False)+'\n')
    result = subprocess.run([str(binaries[0]), str(request_path)],
                            capture_output=True, check=False)
    (output/'stderr.txt').write_bytes(result.stderr)
    if result.returncode:
        raise ValueError('HDBSCAN command failed: '+result.stderr.decode(errors='replace'))
    response = json.loads(result.stdout)
    hdbscan.members(response, request, mapping)
    (output/'result.json').write_bytes(result.stdout)
    provenance.update(request=str(request_path),
                      request_sha256=hashlib.sha256(request_path.read_bytes()).hexdigest(),
                      result=str(output/'result.json'),
                      result_sha256=hashlib.sha256(result.stdout).hexdigest())
    review = group_review(response, request, mapping, combined, provenance)
    review.update(original_entries=sum(s['original_entries'] for s in selections),
                  encoded_entries=len(vectors),
                  assigned_entries=sum(g['entries'] for g in review['groups']))
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path, nargs='+')
    parser.add_argument('--notes-per-source', type=int,
                        help='recluster the first N notes of each saved source using their exact vectors')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--title', default='HDBSCAN groups · automatic epsilon candidate')
    args = parser.parse_args()
    if args.notes_per_source is not None:
        result = source_review(args.state, args.notes_per_source, args.output)
    else:
        if len(args.state) != 1:
            parser.error('multiple states require --notes-per-source')
        result = saved_review(args.state[0])
        args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'analysis.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    (args.output/'groups.svg').write_text(render_svg(result['tree'], result['sections'],
        result['groups'], result['selection']['epsilon'], title=args.title,
        provenance=result['provenance']))
    rows = ['| Group | Entry titles | Notes |', '|---|---|---:|']
    for group in result['groups']:
        names = '; '.join(group['titles']).replace('|', '\\|').replace('\n', ' ')
        rows.append(f'| G{group["id"]:02d} | {names} | {group["notes"]} |')
    rows += ['', '| Section | Groups | Distinct notes |', '|---|---|---:|']
    by_group = {g['id']: g for g in result['groups']}
    for i, section in enumerate(result['sections'], 1):
        note_ids = {n for g in section['groups'] for n in by_group[g]['note_ids']}
        rows.append(f'| S{i:02d} | '+', '.join(f'G{g:02d}' for g in section['groups'])+f' | {len(note_ids)} |')
    (args.output/'groups.md').write_text('\n'.join(rows)+'\n')
    print(json.dumps(dict(groups=len(result['groups']), sections=len(result['sections']),
                          epsilon=result['selection']['epsilon'],
                          represented_notes=result['represented_notes'],
                          input_notes=result['input_notes'], svg=str(args.output/'groups.svg'))))


if __name__ == '__main__':
    main()
