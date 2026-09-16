"""TRUE14: add scored Coffee-child memberships to the unchanged TRUE13 DAG.

The original masks, source bytes, six-target coverage and saved scores are
validated before exporting the existing hierarchy viewer's file format.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


CODE = Path(__file__).resolve().parent
RESEARCH = CODE / 'navigation-research-v1'
THRESHOLD = 0.142
MASK_IDS = {f'V{index:03d}' for index in range(1, 946)}
PARENT_TITLES = ('Coffee', 'Tea as a beverage')
CHILD_TITLES = ('Coffee Bean Preparation', 'Having drunk coffee',
                'Appreciating Coffee for Its Flavour', '#coffeechain')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique(rows, field):
    result = {}
    for row in rows:
        key = row[field]
        if not isinstance(key, str) or not key.strip() or key in result:
            raise ValueError('unique nonempty ' + field + ' required')
        result[key] = row
    return result


def mask_key(mask):
    return mask['note_id'], tuple(map(tuple, mask['byte_spans']))


def validated_inputs(baseline, source_bytes, inputs, reused, fresh):
    if digest(source_bytes) != baseline['source_sha256']:
        raise ValueError('original source checksum differs from baseline')
    originals = unique(json.loads(source_bytes)['notes'], 'note_id')
    nodes = unique(baseline['nodes'], 'node_id')
    root = baseline['root_node_id']
    if len(nodes) != 60 or root not in nodes:
        raise ValueError('all 59 categories plus navigation root required')
    targets = {}
    for title in PARENT_TITLES + CHILD_TITLES:
        matches = [key for key, node in nodes.items() if node['label'] == title]
        if len(matches) != 1:
            raise ValueError('one exact category title required: ' + title)
        targets[title] = matches[0]
    children = {targets[title] for title in CHILD_TITLES}
    if set(nodes[targets['Coffee']]['children']) != children:
        raise ValueError('the four original Coffee children are required')
    completed = set()

    def visit(key, path):
        if key in path:
            raise ValueError('baseline category graph contains a cycle')
        if key not in nodes:
            raise ValueError('unknown child category: ' + key)
        if key not in completed:
            node = nodes[key]
            if (len(node['children']) != len(set(node['children']))
                    or len(node['note_ids']) != len(set(node['note_ids']))):
                raise ValueError('duplicate child or direct note in baseline')
            for child in node['children']:
                visit(child, path | {key})
            completed.add(key)

    visit(root, set())
    if completed != set(nodes):
        raise ValueError('unreachable baseline categories')
    rows = unique(inputs, 'id')
    seen = {key: set() for key in targets.values()}
    masks, aliases, short_ids = {}, {}, {}
    for row in rows.values():
        group = row['category_id']
        if group not in seen or row['category_title'] != nodes[group]['label']:
            raise ValueError('input category differs from the six frozen targets')
        model_input = f'premise: {row["premise"]} hypothesis: This text is about {row["category_title"]}.'
        if row['model_input'] != model_input or row['id'] != 'M' + digest(model_input.encode()):
            raise ValueError('model input or input ID changed')
        if not row['masks']:
            raise ValueError('source mask aliases required')
        for mask in row['masks']:
            identifier, note = mask['short_id'], mask['note_id']
            if identifier in seen[group]:
                raise ValueError('duplicate category/mask input')
            seen[group].add(identifier)
            if note not in originals:
                raise ValueError('mask refers to unknown source note')
            encoded = originals[note]['text'].encode('utf-8')
            if mask['note_text_sha256'] != digest(encoded) or not mask['vector_id']:
                raise ValueError('original mask source identity changed')
            short = mask['note_short_id']
            if (not isinstance(short, str) or not short.strip()
                    or short_ids.get(note, short) != short):
                raise ValueError('conflicting source note short ID')
            short_ids[note] = short
            spans, fragments = mask['byte_spans'], mask['fragments']
            if not spans or len(spans) != len(fragments):
                raise ValueError('every source fragment requires its original byte span')
            previous_end = -1
            for span, fragment in zip(spans, fragments):
                if (len(span) != 2 or any(type(value) is not int for value in span)
                        or not 0 <= span[0] < span[1] <= len(encoded)
                        or span[0] < previous_end
                        or encoded[span[0]:span[1]].decode('utf-8') != fragment):
                    raise ValueError('mask fragment differs from original source bytes')
                previous_end = span[1]
            if row['premise'] != ' '.join(fragments):
                raise ValueError('model input differs from original mask fragments')
            if identifier in masks and masks[identifier] != mask:
                raise ValueError('conflicting original mask alias provenance')
            masks[identifier] = mask
            aliases.setdefault(mask_key(mask), set()).add(identifier)
    if any(covered != MASK_IDS for covered in seen.values()):
        raise ValueError('all 945 original masks required for each of six targets')
    if len(set(short_ids.values())) != len(short_ids):
        raise ValueError('different source notes cannot share a short ID')
    scored = {}
    for evidence, allowed in ((reused, set(targets.values()) - children), (fresh, children)):
        for row in evidence:
            identifier = row['id']
            if identifier in scored:
                raise ValueError('duplicate scored input')
            expected = rows.get(identifier)
            if (expected is None or row['category_id'] not in allowed
                    or any(row.get(key) != value for key, value in expected.items())):
                raise ValueError('score metadata differs from frozen input or score source')
            score = row['entailment_score']
            if type(score) not in (float, int) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError('finite entailment probability required')
            scored[identifier] = row
    if set(scored) != set(rows):
        raise ValueError('scores must cover every frozen six-target input exactly once')
    return nodes, originals, short_ids, masks, aliases, scored, children, seen


def expand(baseline, source_bytes, inputs, reused, fresh):
    nodes, originals, short_ids, masks, aliases, scored, children, seen = validated_inputs(
        baseline, source_bytes, inputs, reused, fresh)
    root = baseline['root_node_id']
    declared = unique(baseline['notes'], 'note_id')
    for note, reference in declared.items():
        if note not in originals or short_ids.get(note) != reference['note_short_id']:
            raise ValueError('baseline source note reference changed')
    by_short = {short: note for note, short in short_ids.items()}
    if set(baseline['mask_instances']) != set(nodes) or set(baseline['note_masks']) != set(nodes):
        raise ValueError('baseline masks must cover all original categories')
    existing = {}
    for group, node in nodes.items():
        category = {}
        for short, records in baseline['mask_instances'][group].items():
            if short not in by_short or by_short[short] not in declared or not records:
                raise ValueError('baseline individual mask note is not declared')
            for record in records:
                key = by_short[short], tuple(map(tuple, record['byte_spans']))
                if key in category or not record['ids'] or set(record['ids']) != aliases.get(key):
                    raise ValueError('baseline individual mask aliases differ from original masks')
                if any(identifier not in masks or mask_key(masks[identifier]) != key
                       for identifier in record['ids']):
                    raise ValueError('baseline individual mask ID has changed source bytes')
                category[key] = deepcopy(record)
        expected = {short: sorted({tuple(span) for record in records for span in record['byte_spans']})
                    for short, records in baseline['mask_instances'][group].items()}
        saved = {short: sorted(set(map(tuple, spans)))
                 for short, spans in baseline['note_masks'][group].items()}
        if expected != saved:
            raise ValueError('baseline individual masks differ from original highlights')
        if not set(node['note_ids']) <= set(expected):
            raise ValueError('baseline direct note lacks original masks')
        existing[group] = category
    for group, node in nodes.items():
        for child in node['children']:
            if not existing[child].keys() <= existing[group].keys():
                raise ValueError('baseline parent omits child individual masks')
    result = deepcopy(baseline)
    result['hierarchy_id'] = 'TRUE14 · all categories · Coffee-child membership additions'
    result_nodes = {node['node_id']: node for node in result['nodes']}
    expanded = deepcopy(existing)
    additions = []
    for row in scored.values():
        group = row['category_id']
        if group not in children or row['entailment_score'] <= THRESHOLD:
            continue
        for mask in row['masks']:
            key = mask_key(mask)
            if key in expanded[group]:
                continue
            note, spans = key
            record = dict(ids=sorted(aliases[key]), byte_spans=[list(span) for span in spans])
            expanded[group][key] = record
            result_nodes[group]['note_ids'] = sorted(set(result_nodes[group]['note_ids']) | {short_ids[note]})
            evidence = {name: deepcopy(value) for name, value in row.items() if name != 'masks'}
            evidence['masks'] = [deepcopy(masks[identifier]) for identifier in record['ids']]
            additions.append(dict(category_id=group, category_title=nodes[group]['label'],
                note_id=note, note_short_id=short_ids[note], **deepcopy(record),
                score_source='run/scores.jsonl', evidence=evidence))
    inherited = set()

    def inherit(group):
        if group in inherited:
            return
        for child in nodes[group]['children']:
            inherit(child)
            expanded[group].update(expanded[child])
        inherited.add(group)

    inherit(root)
    for group, category in expanded.items():
        by_note = {}
        for (note, _), record in category.items():
            by_note.setdefault(short_ids[note], []).append(record)
        result['mask_instances'][group] = {
            short: sorted(records, key=lambda record: record['ids'])
            for short, records in sorted(by_note.items())}
        result['note_masks'][group] = {
            short: [list(span) for span in sorted({tuple(span) for record in records
                                                 for span in record['byte_spans']})]
            for short, records in sorted(by_note.items())}
        count = len(by_note)
        result_nodes[group]['analysis'] = (
            f'Original TRUE13 categories and links retained. {count} notes including children. '
            'Original memberships retained; only Coffee-child masks scoring > 0.142 added. '
            'Coffee/Tea direct memberships retained; child masks inherited upward only.')
    reachable = {note for note, _ in expanded[root]}
    if not set(declared) <= reachable:
        raise ValueError('original source note became unreachable')
    result['notes'] = [dict(note_id=note, note_short_id=short_ids[note])
                       for note in sorted(reachable, key=short_ids.__getitem__)]
    additions.sort(key=lambda row: (row['category_id'], row['note_short_id'], row['ids']))
    changes = dict(experiment='TRUE14', threshold=THRESHOLD,
        decision='strict entailment_score > 0.142; additive child memberships only', additions=additions,
        categories=[dict(category_id=group, category_title=nodes[group]['label'],
            added_direct_note_ids=sorted(set(result_nodes[group]['note_ids']) - set(nodes[group]['note_ids'])),
            added_recursive_note_ids=sorted(set(result['note_masks'][group]) - set(baseline['note_masks'][group])),
            added_mask_instances=[dict(note_id=note, note_short_id=short_ids[note], **expanded[group][note, spans])
                for note, spans in sorted(expanded[group].keys() - existing[group].keys())])
            for group in nodes],
        added_note_ids=sorted(reachable - set(declared)), removed_note_ids=[])
    coverage = dict(original_masks=len(masks), targets=len(seen), mask_category_pairs=sum(map(len, seen.values())),
        scored_inputs=len(scored), reused_inputs=len(reused), new_inputs=len(fresh),
        masks_per_category={group: len(ids) for group, ids in seen.items()},
        source_notes=len(originals), baseline_notes=len(declared), reachable_notes=len(reachable),
        unassigned_source_notes=len(originals) - len(reachable))
    return result, changes, coverage


def package(run, baseline=RESEARCH / 'TRUE13/categories-with-mask-ids.json',
            source=CODE / 'real-note-fine-segmentation-v1/reviewed-input.json',
            reused_scores=RESEARCH / 'TRUE12/scores.jsonl'):
    run = Path(run)
    outputs = {name: run / name for name in ('categories.json', 'membership-changes.json', 'packaging-manifest.json')}
    for path in outputs.values():
        if path.exists():
            raise FileExistsError('preserve existing packaging output: ' + str(path))
    paths = dict(baseline=Path(baseline), source=Path(source), inputs=run / 'inputs.json',
                 reused_scores=Path(reused_scores), scores=run / 'run/scores.jsonl',
                 new_inputs=run / 'new-inputs.json', plan=run / 'plan.json',
                 frozen=run / 'frozen.json', verification=run / 'verification.json',
                 completion=run / 'run/completion.json', execution=run / 'run/execution.json')
    raw = {key: path.read_bytes() for key, path in paths.items()}
    # The unchanged runner validates both prepared inputs and all preserved
    # source/implementation files. A successful verification is necessary but
    # not sufficient: bind it to the actual score bytes being packaged now.
    from true_branch_membership import verify as verify_frozen

    frozen = json.loads(raw['frozen'])
    if not {'inputs.json', 'new-inputs.json', 'plan.json'} <= frozen.keys():
        raise ValueError('complete frozen input and plan checksums required')
    verify_frozen(run)
    plan, verification, completion, execution = (
        json.loads(raw[key]) for key in ('plan', 'verification', 'completion', 'execution'))
    if plan['experiment'] != 'TRUE14' or plan['threshold'] != THRESHOLD:
        raise ValueError('frozen TRUE14 plan and unchanged threshold required')
    preserved = {(CODE.parent / name).resolve(): value
                 for name, value in plan['preservation_sha256'].items()}
    for key in ('baseline', 'source', 'reused_scores'):
        if preserved.get(paths[key].resolve()) != digest(raw[key]):
            raise ValueError('packaging source is not preserved in frozen plan: ' + key)
    if (verification['experiment'] != 'TRUE14'
            or any(verification.get(key) is not True for key in
                   ('cache_identity_matches', 'old_scores_unchanged', 'exact_coverage'))):
        raise ValueError('successful TRUE14 verification required')
    if (verification['new_scores_sha256'] != digest(raw['scores'])
            or completion['scores_sha256'] != digest(raw['scores'])):
        raise ValueError('verified or completed score checksum differs from current scores')
    if (execution['experiment'] != 'TRUE14'
            or execution['frozen_sha256'] != digest(raw['frozen'])):
        raise ValueError('completed execution differs from frozen TRUE14 inputs')
    inputs, new_inputs = json.loads(raw['inputs']), json.loads(raw['new_inputs'])
    if (new_inputs != [row for row in inputs if row['category_title'] in CHILD_TITLES]
            or plan['unique_inputs'] != len(inputs)
            or plan['new_inputs'] != len(new_inputs)
            or verification['new_inputs'] != len(new_inputs)
            or execution['inputs'] != len(new_inputs)
            or verification['old_inputs'] != plan['reused_inputs']):
        raise ValueError('verified coverage differs from frozen plan and inputs')
    result, changes, coverage = expand(json.loads(raw['baseline']), raw['source'], json.loads(raw['inputs']),
        [json.loads(line) for line in raw['reused_scores'].splitlines()],
        [json.loads(line) for line in raw['scores'].splitlines()])
    if (completion['pairs'] != coverage['new_inputs']
            or plan['reused_inputs'] != coverage['reused_inputs']):
        raise ValueError('completed score coverage differs from frozen plan')
    encoded = {name: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
               for name, value in (('categories.json', result), ('membership-changes.json', changes))}
    manifest = dict(experiment='TRUE14', baseline_experiment='TRUE13', threshold=THRESHOLD,
        category_count=len(result['nodes']) - 1, graph_unchanged=True, baseline_memberships_preserved=True,
        coffee_tea_direct_memberships_unchanged=True, added_child_mask_instances=len(changes['additions']),
        coverage=coverage, input_paths={key: str(path.resolve()) for key, path in paths.items()},
        input_sha256={key: digest(value) for key, value in raw.items()},
        output_sha256={name: digest(value) for name, value in encoded.items()})
    encoded['packaging-manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    if any(path.read_bytes() != raw[key] for key, path in paths.items()):
        raise ValueError('frozen evidence changed during packaging')
    verify_frozen(run)
    for name, value in encoded.items():
        with outputs[name].open('xb') as stream:
            stream.write(value)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=RESEARCH / 'TRUE14')
    parser.add_argument('--baseline', type=Path, default=RESEARCH / 'TRUE13/categories-with-mask-ids.json')
    parser.add_argument('--source', type=Path, default=CODE / 'real-note-fine-segmentation-v1/reviewed-input.json')
    parser.add_argument('--reused-scores', type=Path, default=RESEARCH / 'TRUE12/scores.jsonl')
    args = parser.parse_args()
    print(json.dumps(package(args.run, args.baseline, args.source, args.reused_scores), indent=2))


if __name__ == '__main__':
    main()
