"""Promotion-only navigation experiment over frozen category memberships.

This changes which saved descendants are offered, not their meaning or members.
Its count-based cost proxy is not a semantic-quality or browsing-time estimate.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path


def memberships(categories):
    nodes = {n['node_id']: n for n in categories['nodes']}
    if len(nodes) != len(categories['nodes']):
        raise ValueError('duplicate node IDs')
    full, seen = {}, set()

    def visit(i):
        if i in seen or i not in nodes:
            raise ValueError('cycle, shared child, or missing category')
        seen.add(i)
        result = set(nodes[i]['note_ids'])
        for child in nodes[i]['children']:
            result |= visit(child)
        full[i] = result
        return result

    visit(categories['root_node_id'])
    if seen != set(nodes):
        raise ValueError('root must reach every category')
    return full


def select_categories(categories, *, max_choices=8):
    if max_choices is not None and max_choices < 2:
        raise ValueError('choice bound must be at least two')
    full = memberships(categories)
    result = deepcopy(categories)
    nodes = {n['node_id']: n for n in result['nodes']}
    trace, order = [], []

    def visit(parent):
        node = nodes[parent]
        bound = max(max_choices, len(node['children'])) if max_choices is not None else None
        while True:
            choices = []
            for position, child in enumerate(node['children']):
                grandchildren = nodes[child]['children']
                k = len(grandchildren)
                if not k or (bound is not None and len(node['children']) - 1 + k > bound):
                    continue
                gain = len(full[child]) * (1 + k) - len(full[parent]) * (k - 1)
                if gain > 0:
                    choices.append((gain, -position, child))
            if not choices:
                break
            gain, negative_position, child = max(choices)
            position = -negative_position
            promoted = nodes[child]['children']
            node['children'][position:position + 1] = promoted
            trace.append(dict(parent=parent, removed=child, promoted=promoted.copy(), gain=gain))
            del nodes[child]
        node['note_ids'] = sorted(full[parent] - set().union(*(full[c] for c in node['children'])))
        order.append(parent)
        for child in node['children']:
            visit(child)

    visit(result['root_node_id'])
    result['nodes'] = [nodes[i] for i in order]
    if 'note_masks' in result:
        result['note_masks'] = {i: result['note_masks'][i] for i in order}
    if memberships(result) != {i: full[i] for i in order}:
        raise ValueError('selection changed retained memberships')
    original_leaves = {n['node_id'] for n in categories['nodes'] if not n['children']}
    if not original_leaves <= set(order):
        raise ValueError('selection removed a leaf destination')
    return result, trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('categories', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--max-choices', type=int, default=8,
                        help='0 is the explicitly unbounded comparison')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    original_bytes = args.categories.read_bytes()
    categories = json.loads(original_bytes)
    selected, trace = select_categories(categories, max_choices=args.max_choices or None)
    selected['hierarchy_id'] += '-' + args.run_id
    args.output.mkdir(parents=True)
    with (args.output / 'categories.json').open('x') as file:
        json.dump(selected, file, ensure_ascii=False, indent=2)
        file.write('\n')
    with (args.output / 'selection.json').open('x') as file:
        json.dump(dict(run_id=args.run_id, source=str(args.categories.resolve()),
                       source_sha256=hashlib.sha256(original_bytes).hexdigest(),
                       code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       max_choices=args.max_choices or None,
                       count_before=len(categories['nodes']), count_after=len(selected['nodes']),
                       promotions=trace), file, indent=2)
        file.write('\n')
    print(json.dumps(dict(run_id=args.run_id, before=len(categories['nodes']),
                          after=len(selected['nodes']), removed=len(trace))))


if __name__ == '__main__':
    main()
