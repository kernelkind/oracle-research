"""Recover individual category masks from saved TRUE13 and TRUE12 evidence.

Keep every existing category, note and combined highlight unchanged. Membership
comes only from native matched instances and saved Coffee/Tea scores > 0.142;
byte-range containment is never used to infer membership. No inference is run.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


THRESHOLD = 0.142
MEMBERSHIP_TITLES = {'Coffee', 'Tea as a beverage'}


def reconstruct(categories, native_notes, scores, source_bytes):
    if hashlib.sha256(source_bytes).hexdigest() != categories['source_sha256']:
        raise ValueError('original source checksum differs from category view')
    originals = {note['note_id']: note['text'] for note in json.loads(source_bytes)['notes']}
    short_ids = {note['note_id']: note['note_short_id'] for note in categories['notes']}
    if (len(short_ids) != len(categories['notes'])
            or len(set(short_ids.values())) != len(short_ids)):
        raise ValueError('unique source and short note IDs required')
    nodes = {node['node_id']: node for node in categories['nodes']}
    root = categories['root_node_id']
    native = {node['group']: node for node in native_notes['nodes']}
    if (len(nodes) != len(categories['nodes']) or root not in nodes
            or len(native) != len(native_notes['nodes'])
            or set(native) != set(nodes) - {root}):
        raise ValueError('native category inventory differs from category view')
    own = {key: set() for key in nodes}
    aliases, identities = {}, {}

    def register(mask, identifier):
        note = mask['note_id']
        text = originals[note]
        encoded = text.encode('utf-8')
        if ('text' in mask and mask['text'] != text
                or 'note_text_sha256' in mask
                and mask['note_text_sha256'] != hashlib.sha256(encoded).hexdigest()):
            raise ValueError('mask source text changed: ' + identifier)
        if ('note_short_id' in mask and note in short_ids
                and mask['note_short_id'] != short_ids[note]):
            raise ValueError('mask short note ID changed: ' + identifier)
        spans, fragments = mask['byte_spans'], mask['fragments']
        if not spans or len(spans) != len(fragments):
            raise ValueError('each original mask fragment needs a byte range')
        for span, fragment in zip(spans, fragments):
            if (len(span) != 2 or any(type(offset) is not int for offset in span)
                    or not 0 <= span[0] < span[1] <= len(encoded)
                    or encoded[span[0]:span[1]].decode('utf-8') != fragment):
                raise ValueError('mask fragment differs from original bytes: ' + identifier)
        if not isinstance(identifier, str) or not identifier or not mask['vector_id']:
            raise ValueError('original mask and vector IDs required')
        key = note, tuple(sorted(set(map(tuple, spans))))
        identity = key, mask['vector_id']
        if identifier in identities and identities[identifier] != identity:
            raise ValueError('conflicting original mask ID: ' + identifier)
        identities[identifier] = identity
        aliases.setdefault(key, set()).add(identifier)
        return key

    for key, node in native.items():
        if node['title'] != nodes[key]['label']:
            raise ValueError('native category title changed: ' + key)
        for mask in node['matched_instances']:
            own[key].add(register(mask, mask['instance']))

    seen = set()
    for row in scores:
        key = row['category_id']
        if (key not in nodes or row['category_title'] not in MEMBERSHIP_TITLES
                or row['category_title'] != nodes[key]['label'] or not row['masks']):
            raise ValueError('saved scores must describe the Coffee/Tea categories')
        if row['id'] in seen:
            raise ValueError('duplicate saved score row')
        seen.add(row['id'])
        score = row['entailment_score']
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('invalid saved membership score')
        for mask in row['masks']:
            mask_key = register(mask, mask['short_id'])
            expected = (f'premise: {" ".join(mask["fragments"])} '
                        f'hypothesis: This text is about {row["category_title"]}.')
            if row['model_input'] != expected:
                raise ValueError('saved score input differs from original mask fragments')
            if score > THRESHOLD:
                own[key].add(mask_key)

    inherited = {}

    def inherit(key, path):
        if key in path:
            raise ValueError('category graph contains a cycle')
        if key not in nodes:
            raise ValueError('unknown child category: ' + key)
        if key not in inherited:
            masks = set(own[key])
            for child in nodes[key]['children']:
                masks.update(inherit(child, path | {key}))
            inherited[key] = masks
        return inherited[key]

    result = deepcopy(categories)
    instances = {}
    for key in nodes:
        by_note = {}
        for note, spans in inherit(key, set()):
            if note not in short_ids:
                raise ValueError('mask note is missing from the category view: ' + note)
            by_note.setdefault(short_ids[note], []).append(dict(
                ids=sorted(aliases[note, spans]), byte_spans=[list(span) for span in spans]))
        by_note = {short: sorted(masks, key=lambda mask: mask['ids'])
                   for short, masks in sorted(by_note.items())}
        combined = {short: sorted({tuple(span) for mask in masks for span in mask['byte_spans']})
                    for short, masks in by_note.items()}
        saved = {short: sorted(set(map(tuple, spans)))
                 for short, spans in categories['note_masks'][key].items()}
        if combined != saved:
            differing = sorted(short for short in set(combined) | set(saved)
                               if combined.get(short) != saved.get(short))
            raise ValueError(f'individual masks differ from saved highlights: {key}/{differing}')
        instances[key] = by_note
    result['mask_instances'] = instances
    return result


def package(categories, native_notes, scores, source, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    paths = [Path(path) for path in (categories, native_notes, scores, source)]
    before = [path.read_bytes() for path in paths]
    categories, native_notes = map(json.loads, before[:2])
    scores = [json.loads(line) for line in before[2].splitlines()]
    enriched = reconstruct(categories, native_notes, scores, before[3])
    if before != [path.read_bytes() for path in paths]:
        raise ValueError('saved inputs changed during packaging')
    with output.open('x') as stream:
        json.dump(enriched, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return enriched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('categories', 'native-notes', 'scores', 'source', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = package(args.categories, args.native_notes, args.scores, args.source, args.output)
    print(f'Saved original mask IDs for {len(result["nodes"])} categories to {args.output}')


if __name__ == '__main__':
    main()
