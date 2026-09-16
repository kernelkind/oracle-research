"""Package TRUE12 Coffee/Tea memberships in the existing category browser.

Read saved results only. Preserve the TRUE11 category links and child contents;
add notes and mask evidence using the previously tested strict 0.142 cutoff.
Both focused baseline and expanded views are saved without replacing originals.
"""

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'navigation-research-v1/TRUE12'
BASELINE = ROOT / 'navigation-research-v1/TRUE11/categories.json'
THRESHOLD = 0.142


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_views(baseline, source_bytes, scores):
    if baseline['source_sha256'] != hashlib.sha256(source_bytes).hexdigest():
        raise ValueError('original source checksum differs from baseline')
    source = {n['note_id']: n['text'] for n in json.loads(source_bytes)['notes']}
    nodes = {n['node_id']: n for n in baseline['nodes']}
    groups = list(dict.fromkeys(row['category_id'] for row in scores))
    if not groups or any(key not in nodes or key == baseline['root_node_id'] for key in groups):
        raise ValueError('scored categories must exist in the saved hierarchy')

    selected = set()

    def visit(key, path):
        if key in path:
            raise ValueError('category graph contains a cycle')
        if key in selected:
            return
        selected.add(key)
        for child in nodes[key]['children']:
            visit(child, path | {key})

    for key in groups:
        visit(key, set())
    if any(set(nodes[key]['children']) & set(groups) for key in selected):
        raise ValueError('focus categories must be separate branches')

    registry = {n['note_short_id']: n['note_id'] for n in baseline['notes']}
    reverse = {note_id: short for short, note_id in registry.items()}
    additions = {key: {} for key in groups}
    seen_rows, seen_masks = set(), set()
    counts = dict.fromkeys(groups, 0)
    for row in scores:
        group = row['category_id']
        if row['id'] in seen_rows:
            raise ValueError('duplicate scored row')
        seen_rows.add(row['id'])
        score = row['entailment_score']
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('invalid saved score')
        if row['category_title'] != nodes[group]['label'] or not row['masks']:
            raise ValueError('scored title or mask evidence differs from saved category')
        for mask in row['masks']:
            pair = (group, mask['short_id'])
            if pair in seen_masks:
                raise ValueError('duplicate category/mask record')
            seen_masks.add(pair)
            short, note_id = mask['note_short_id'], mask['note_id']
            if (registry.get(short, note_id) != note_id
                    or reverse.get(note_id, short) != short):
                raise ValueError('conflicting source note identifiers')
            registry[short], reverse[note_id] = note_id, short
            encoded = source[note_id].encode('utf-8')
            if hashlib.sha256(encoded).hexdigest() != mask['note_text_sha256']:
                raise ValueError('mask source text changed')
            spans, fragments = mask['byte_spans'], mask['fragments']
            if not spans or len(spans) != len(fragments):
                raise ValueError('each fragment requires its source range')
            for span, fragment in zip(spans, fragments):
                if (len(span) != 2 or any(type(i) is not int for i in span)
                        or not 0 <= span[0] < span[1] <= len(encoded)
                        or encoded[span[0]:span[1]].decode('utf-8') != fragment):
                    raise ValueError('mask must preserve exact original source ranges')
            expected_input = (f'premise: {" ".join(fragments)} '
                              f'hypothesis: This text is about {row["category_title"]}.')
            if row['model_input'] != expected_input:
                raise ValueError('saved score does not describe these mask fragments')
            if score > THRESHOLD:
                counts[group] += 1
                additions[group].setdefault(short, set()).update(tuple(span) for span in spans)

    def view(expand):
        spec = deepcopy(baseline)
        spec['hierarchy_id'] = 'TRUE12 Coffee/Tea · ' + ('expanded memberships' if expand else 'TRUE11 baseline')
        spec['nodes'] = [dict(node_id='root', label='Coffee and tea', children=groups,
                              note_ids=[], analysis='Focused view of the two tested branches. '
                              'Category links and child memberships are unchanged.')]
        spec['nodes'].extend(deepcopy(n) for n in baseline['nodes'] if n['node_id'] in selected)
        spec['note_masks'] = {key: deepcopy(baseline['note_masks'][key]) for key in sorted(selected)}
        by_id = {n['node_id']: n for n in spec['nodes']}
        if expand:
            for group in groups:
                masks = spec['note_masks'][group]
                new_notes = set(additions[group]) - set(masks)
                by_id[group]['note_ids'] = sorted(set(by_id[group]['note_ids']) | new_notes)
                for short, spans in additions[group].items():
                    masks[short] = [list(span) for span in sorted(
                        {tuple(span) for span in masks.get(short, [])} | spans)]
                by_id[group]['analysis'] = (
                    f'Existing category links and children unchanged. '
                    f'{len(new_notes)} notes added by saved TRUE12 scores > {THRESHOLD}; '
                    f'{len(masks)} notes including descendants. '
                    'Highlights combine original category masks with all passing membership masks. '
                    'Existing notes remain even when TRUE rejects them.')
        root_masks = {}
        for group in groups:
            for short, spans in spec['note_masks'][group].items():
                root_masks.setdefault(short, set()).update(tuple(span) for span in spans)
        spec['note_masks']['root'] = {
            short: [list(span) for span in sorted(spans)] for short, spans in sorted(root_masks.items())}
        spec['notes'] = [dict(note_id=registry[short], note_short_id=short) for short in sorted(root_masks)]
        return spec

    return view(False), view(True), counts


def package(output):
    if output.exists():
        raise FileExistsError(f'refusing to replace saved view: {output}')
    paths = {'baseline': BASELINE, 'source': RUN / 'data/reviewed-input.json',
             'scores': RUN / 'scores.jsonl', 'packager': Path(__file__).resolve()}
    hashes = {key: digest(path) for key, path in paths.items()}
    scores = [json.loads(line) for line in paths['scores'].read_text().splitlines()]
    baseline, expanded, counts = build_views(read(BASELINE), paths['source'].read_bytes(), scores)
    if hashes != {key: digest(path) for key, path in paths.items()}:
        raise ValueError('inputs changed during packaging')
    output.mkdir(parents=True, exist_ok=False)
    for name, spec in [('baseline-categories.json', baseline), ('categories.json', expanded)]:
        with (output / name).open('x') as stream:
            json.dump(spec, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    manifest = dict(source='TRUE12 saved membership scores; no new inference',
                    threshold=THRESHOLD, rule='strictly greater; additive to TRUE11',
                    category_edges_changed=False, accepted_mask_counts=counts,
                    input_sha256=hashes,
                    output_sha256={name: digest(output / name)
                                   for name in ('baseline-categories.json', 'categories.json')})
    with (output / 'manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print(f'Saved Coffee/Tea baseline and expanded views to {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=RUN / 'hierarchy')
    package(parser.parse_args().output)


if __name__ == '__main__':
    main()
