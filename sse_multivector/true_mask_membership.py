"""TRUE12: original source masks against the frozen TRUE11 Coffee and Tea titles."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import time

import hierarcaps_category_probe
import hierarcaps_mask_probe
import true_category_probe
import true_mask_inference
from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION


TITLES = ('Coffee', 'Tea as a beverage')
MASK_COUNT = 945
ROOT = Path(__file__).resolve().parent
DATA_PATHS = {
    'vector-map.json': ROOT / 'real-note-fine-segmentation-v1/vectors/vector-map.json',
    'reviewed-input.json': ROOT / 'real-note-fine-segmentation-v1/reviewed-input.json',
    'native-graph.json': ROOT / 'navigation-research-v1/TRUE11/native-graph.json',
    'native-notes.json': ROOT / 'navigation-research-v1/TRUE11/native-notes.json',
}


def _unique(records, key):
    result = {}
    for row in records:
        value = row.get(key)
        if not isinstance(value, str) or not value or value in result:
            raise ValueError('unique nonempty ' + key + ' required')
        result[value] = row
    return result


def _categories(graph, baseline):
    graph_nodes = _unique(graph['nodes'], 'group')
    baseline_nodes = _unique(baseline['nodes'], 'group')
    result = []
    for title in TITLES:
        matches = [node for node in graph_nodes.values() if node['title'] == title]
        if len(matches) != 1:
            raise ValueError('one exact category title required: ' + title)
        node = matches[0]
        old = baseline_nodes.get(node['group'])
        if old is None or old['title'] != title:
            raise ValueError('baseline category title changed: ' + title)
        for field in ('own_note_ids', 'recursive_note_ids'):
            values = old[field]
            if (not isinstance(values, list) or len(set(values)) != len(values)
                    or any(not isinstance(value, str) or not value for value in values)):
                raise ValueError('unique baseline note IDs required')
        if not set(old['own_note_ids']) <= set(old['recursive_note_ids']):
            raise ValueError('recursive baseline must contain own notes')
        result.append(deepcopy(old))
    return dict(experiment='TRUE11', nodes=result)


def prepare_inputs(original, reviewed, graph, baseline):
    """Validate original bytes; join with one space; preserve all aliases and provenance."""
    vectors = original['vectors']
    if original['vector_count'] != MASK_COUNT or len(vectors) != MASK_COUNT:
        raise ValueError('all 945 original masks required')
    by_mask = _unique(vectors, 'short_id')
    if set(by_mask) != {f'V{index:03d}' for index in range(1, MASK_COUNT + 1)}:
        raise ValueError('original V001 through V945 mask IDs required')
    notes = _unique(reviewed['notes'], 'note_id')
    source_notes = _unique(original['notes'], 'note_id')
    for note_id, source in source_notes.items():
        if note_id not in notes:
            raise ValueError('missing source note: ' + note_id)
        text = notes[note_id]['text']
        if hashlib.sha256(text.encode('utf-8')).hexdigest() != source['text_sha256']:
            raise ValueError('source note bytes changed: ' + note_id)
    if any(vector['note_id'] not in source_notes for vector in vectors):
        raise ValueError('original mask refers to unknown source note')
    aliases = [dict(vector, text=notes[vector['note_id']]['text']) for vector in vectors]
    validated = hierarcaps_mask_probe.prepare_inputs(
        [dict(aliases=aliases)], original, list(by_mask))
    frozen_baseline = _categories(graph, baseline)
    if any(note_id not in notes for node in frozen_baseline['nodes']
           for note_id in node['recursive_note_ids']):
        raise ValueError('baseline contains unknown source note')
    rows = {}
    for mask in validated:
        original_mask = by_mask[mask['short_id']]
        for node in frozen_baseline['nodes']:
            premise = mask['model_input']
            model_input = f"premise: {premise} hypothesis: This text is about {node['title']}."
            if model_input not in rows:
                rows[model_input] = dict(id='M' + hashlib.sha256(model_input.encode()).hexdigest(),
                    category_id=node['group'], category_title=node['title'],
                    premise=premise, model_input=model_input, masks=[])
            provenance = deepcopy(original_mask)
            provenance['note_text_sha256'] = source_notes[mask['note_id']]['text_sha256']
            rows[model_input]['masks'].append(provenance)
    return list(rows.values()), frozen_baseline


def freeze_inputs(paths, output):
    """Create a new experiment directory only, before any checkpoint access."""
    if output.exists():
        raise FileExistsError('output exists; preserve earlier or interrupted runs')
    if set(paths) != set(DATA_PATHS):
        raise ValueError('all four original and TRUE11 baseline sources required')
    raw = {name: path.read_bytes() for name, path in paths.items()}
    rows, baseline = prepare_inputs(*(json.loads(raw[name]) for name in DATA_PATHS))
    output.mkdir(parents=True, exist_ok=False)
    (output / 'data').mkdir()
    (output / 'source').mkdir()
    for name, content in raw.items():
        with (output / 'data' / name).open('xb') as stream:
            stream.write(content)
    source_hashes = {}
    for module in (Path(__file__), Path(true_mask_inference.__file__),
                   Path(true_category_probe.__file__), Path(hierarcaps_mask_probe.__file__),
                   Path(hierarcaps_category_probe.__file__)):
        target = output / 'source' / module.name
        with target.open('xb') as stream:
            stream.write(module.read_bytes())
        source_hashes[module.name] = sha256(target)
    save_json(output / 'inputs.json', rows)
    save_json(output / 'baseline.json', baseline)
    manifest = dict(experiment='TRUE12', baseline_experiment='TRUE11',
        model_id=MODEL_ID, revision=REVISION, task='source-mask category membership',
        input_format='premise: {source fragments joined by ONE space} hypothesis: '
                     'This text is about {exact category title}.',
        titles=list(TITLES), original_masks=MASK_COUNT, mask_category_pairs=MASK_COUNT * len(TITLES),
        unique_inputs=len(rows), decision='native complete greedy 1/0 with EOS; no score cutoff',
        note_membership='OR over all mask verdicts for the same source note and category',
        dtype='float32', device='cpu', threads=4, interop_threads=1, batch_size=4,
        max_input_tokens=512, truncation=False, offline=True,
        data_paths={name: str(path.resolve()) for name, path in paths.items()},
        data_sha256={name: sha256(output / 'data' / name) for name in paths},
        source_sha256=source_hashes, inputs_sha256=sha256(output / 'inputs.json'),
        baseline_sha256=sha256(output / 'baseline.json'))
    save_json(output / 'started.json', manifest)
    return rows


def load_frozen_inputs(output):
    """Verify data, baseline, inputs and executing source before checkpoint loading."""
    manifest = json.loads((output / 'started.json').read_text())
    if manifest['experiment'] != 'TRUE12' or manifest['revision'] != REVISION:
        raise ValueError('frozen TRUE12 experiment and pinned checkpoint required')
    for field, directory in (('data_sha256', 'data'), ('source_sha256', 'source')):
        for name, digest in manifest[field].items():
            if sha256(output / directory / name) != digest:
                raise ValueError('frozen ' + directory + ' changed: ' + name)
            if directory == 'source' and sha256(Path(__file__).parent / name) != digest:
                raise ValueError('executing source changed: ' + name)
    for name in ('inputs', 'baseline'):
        if sha256(output / (name + '.json')) != manifest[name + '_sha256']:
            raise ValueError('frozen ' + name + ' changed')
    rows = json.loads((output / 'inputs.json').read_text())
    if (len(rows) != manifest['unique_inputs']
            or sum(len(row['masks']) for row in rows) != MASK_COUNT * len(TITLES)):
        raise ValueError('frozen input coverage changed')
    for name in ('scores.jsonl', 'model-files.json', 'config.json', 'completion.json'):
        if (output / name).exists():
            raise FileExistsError('preserve earlier or interrupted inference: ' + name)
    return rows


def validate_snapshot(snapshot):
    snapshot = snapshot.resolve(strict=True)
    if (snapshot.name != REVISION or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('exact pinned model snapshot required')
    return snapshot


def infer(output, snapshot):
    started = time.monotonic()
    rows = load_frozen_inputs(output)
    snapshot = validate_snapshot(snapshot)
    true_mask_inference.run_inference(snapshot, rows, output, 4, started)


def derive_note_memberships(scored_rows, baseline, *, threshold=None):
    """OR all masks per note, including identical-input aliases, against TRUE11.

    Additions mean absent from the baseline, not false positives: correctness
    requires the independently reviewed answer key. A supplied cutoff is strict;
    without one, only complete native answers are used. No input is modified.
    """
    if threshold is not None and (not math.isfinite(threshold) or not 0 <= threshold <= 1):
        raise ValueError('finite explicit probability threshold required')
    categories = _unique(baseline['nodes'], 'group')
    notes = {group: {} for group in categories}
    seen_rows, seen_masks = set(), set()
    for row in scored_rows:
        if row['id'] in seen_rows:
            raise ValueError('duplicate scored input')
        seen_rows.add(row['id'])
        group = row['category_id']
        if group not in categories or row['category_title'] != categories[group]['title']:
            raise ValueError('scored category differs from baseline')
        score = row['entailment_score']
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('finite entailment probability required')
        native = row['predicted']
        if native is not None and type(native) is not bool:
            raise ValueError('Boolean or unresolved native verdict required')
        decision = native if threshold is None else score > threshold
        if not row['masks']:
            raise ValueError('mask aliases required for scored input')
        for mask in row['masks']:
            key = (group, mask['short_id'])
            if key in seen_masks:
                raise ValueError('duplicate category/mask verdict')
            seen_masks.add(key)
            note = notes[group].setdefault(mask['note_id'], dict(note_id=mask['note_id'],
                mask_ids=[], accepted_mask_ids=[], unresolved_mask_ids=[], maximum_score=0.0))
            note['mask_ids'].append(mask['short_id'])
            if decision is True:
                note['accepted_mask_ids'].append(mask['short_id'])
            elif decision is None:
                note['unresolved_mask_ids'].append(mask['short_id'])
            note['maximum_score'] = max(note['maximum_score'], score)
    nodes = []
    for group, old in categories.items():
        own, recursive = set(old['own_note_ids']), set(old['recursive_note_ids'])
        if not recursive <= notes[group].keys():
            raise ValueError('baseline notes missing from scored coverage')
        per_note = list(notes[group].values())
        for note in per_note:
            note['predicted'] = (True if note['accepted_mask_ids'] else
                                 None if note['unresolved_mask_ids'] else False)
            note['baseline_own'] = note['note_id'] in own
            note['baseline_recursive'] = note['note_id'] in recursive
        accepted = [note['note_id'] for note in per_note if note['predicted'] is True]
        nodes.append(dict(group=group, title=old['title'], notes=per_note,
            baseline_own_note_ids=list(old['own_note_ids']),
            baseline_recursive_note_ids=list(old['recursive_note_ids']), accepted_note_ids=accepted,
            added_note_ids=[note for note in accepted if note not in recursive],
            missing_baseline_note_ids=[note for note in old['recursive_note_ids']
                                       if note not in accepted]))
    return dict(decision='native' if threshold is None else 'explicit score cutoff',
                threshold=threshold, nodes=nodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare', help='freeze original inputs and TRUE11 baseline')
    prepare.add_argument('--output', type=Path, required=True)
    run = commands.add_parser('infer', help='verify frozen inputs and run the pinned offline checkpoint')
    run.add_argument('--output', type=Path, required=True)
    cache = Path(os.environ.get('HF_HUB_CACHE', Path.home() / '.cache/huggingface/hub'))
    run.add_argument('--snapshot', type=Path, default=cache /
        ('models--' + MODEL_ID.replace('/', '--')) / 'snapshots' / REVISION)
    args = parser.parse_args()
    if args.command == 'prepare':
        rows = freeze_inputs(DATA_PATHS, args.output)
        print(f'Frozen {MASK_COUNT * len(TITLES)} mask/category pairs in {len(rows)} unique inputs.')
    else:
        infer(args.output, args.snapshot)


if __name__ == '__main__':
    main()
