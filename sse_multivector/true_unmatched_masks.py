"""Show Coffee's exact masks absent from every descendant in the existing browser."""
import argparse
import hashlib
import json
from pathlib import Path

from hierarcaps_mask_probe import save_json, sha256

CODE = Path(__file__).resolve().parent
RUN = CODE / 'navigation-research-v1/TRUE13'
COFFEE = 'S9c440e7f47'
SOURCE = CODE / 'real-note-fine-segmentation-v1/reviewed-input.json'


def read(path):
    return json.loads(path.read_text())


def build_view(view, native, scores, source_bytes, category=COFFEE):
    if hashlib.sha256(source_bytes).hexdigest() != view['source_sha256']:
        raise ValueError('source notes changed')
    nodes = {n['node_id']: n for n in view['nodes']}
    descendants, pending = set(), list(nodes[category]['children'])
    while pending:
        key = pending.pop()
        if key == category:
            raise ValueError('category graph contains a cycle')
        if key not in descendants:
            descendants.add(key)
            pending.extend(nodes[key]['children'])
    relevant = descendants | {category}
    grouped = {n['group']: list(n['matched_instances']) for n in native['nodes'] if n['group'] in relevant}
    if set(grouped) != relevant:
        raise ValueError('missing source masks for category or descendant')
    for row in scores:
        if row['category_id'] in relevant and row['entailment_score'] > 0.142:
            if row['category_title'] != nodes[row['category_id']]['label']:
                raise ValueError('membership score title differs from category')
            grouped[row['category_id']].extend(row['masks'])
    source = {n['note_id']: n['text'] for n in json.loads(source_bytes)['notes']}
    shorts = {n['note_id']: n['note_short_id'] for n in view['notes']}
    unique = {key: {} for key in relevant}
    for group, masks in grouped.items():
        for mask in masks:
            key = (mask['note_id'], tuple(map(tuple, mask['byte_spans'])))
            text = source[mask['note_id']].encode('utf-8')
            if not mask['byte_spans'] or [text[a:b].decode('utf-8') for a, b in mask['byte_spans']] != mask['fragments']:
                raise ValueError('mask must preserve exact original text ranges')
            item = unique[group].setdefault(key, dict(
                ids=[], note_id=mask['note_id'], note_short_id=shorts[mask['note_id']],
                byte_spans=mask['byte_spans'], fragments=mask['fragments']))
            item['ids'].append(mask.get('instance', mask.get('short_id')))
    excluded = {key for child in descendants for key in unique[child]}
    remaining = [mask for key, mask in unique[category].items() if key not in excluded]
    remaining.sort(key=lambda m: (m['note_short_id'], m['ids'][0]))
    for mask in remaining:
        mask['ids'] = sorted(set(mask['ids']))
    if not remaining:
        raise ValueError('no unmatched masks to display')
    ranges = {}
    for mask in remaining:
        ranges.setdefault(mask['note_short_id'], set()).update(map(tuple, mask['byte_spans']))
    title = nodes[category]['label']
    analysis = ('Read-only selection from the saved hierarchy. Exact complete masks are compared by '
        'source note and byte ranges against every descendant before combining highlights. '
        'Shared notes and partial overlaps remain when the complete mask is different. '
        'This is not the D direct-note filter. No notes, masks, titles or relationships were changed.\n\n' +
        '\n'.join(f'{m["note_short_id"]}: {", ".join(m["ids"])} — ' +
                  ' '.join(f'⟦{fragment}⟧' for fragment in m['fragments']) for m in remaining))
    spec = dict(schema_version=2, source_sha256=view['source_sha256'], root_node_id=category,
        hierarchy_id=f'TRUE13 · {len(remaining)} {title} masks absent from children',
        nodes=[dict(node_id=category, label=f'{title} · masks absent from children', children=[],
                    note_ids=sorted(ranges), analysis=analysis)],
        notes=sorted([n for n in view['notes'] if n['note_short_id'] in ranges], key=lambda n: n['note_short_id']),
        note_masks={category: {short: [list(span) for span in sorted(spans)] for short, spans in sorted(ranges.items())}})
    return spec, remaining


def package(output):
    if output.exists():
        raise FileExistsError(output)
    paths = [RUN / 'categories.json', RUN / 'native-notes.json',
             CODE / 'navigation-research-v1/TRUE12/scores.jsonl', SOURCE, Path(__file__)]
    hashes = {str(p.relative_to(CODE.parent)): sha256(p) for p in paths}
    scores = [json.loads(line) for line in paths[2].read_text().splitlines()]
    view, masks = build_view(read(paths[0]), read(paths[1]), scores, SOURCE.read_bytes())
    if hashes != {str(p.relative_to(CODE.parent)): sha256(p) for p in paths}:
        raise ValueError('inputs changed while packaging')
    output.mkdir(parents=True, exist_ok=False)
    save_json(output / 'categories.json', view)
    save_json(output / 'masks.json', masks)
    save_json(output / 'manifest.json', dict(input_sha256=hashes,
        definition='Exact (note_id, complete byte_spans) difference against every descendant; aliases deduplicated.',
        category=COFFEE, masks=len(masks), notes=len(view['notes']),
        output_sha256={name: sha256(output / name) for name in ('categories.json', 'masks.json')}))
    print(f'{len(masks)} masks across {len(view["notes"])} notes: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=RUN / 'coffee-unmatched-masks')
    package(parser.parse_args().output)
