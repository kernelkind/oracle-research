"""TRUE04: all distinct original HDBv2 title pairs, with unchanged TRUE03 inference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import hierarcaps_mask_probe
import true_category_probe
import true_holdout_probe
from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION, model_input
from true_holdout_probe import THRESHOLD, run_inference


def prepare_inputs(titles):
    """Preserve all 61 groups and exact strings; include both distinct ID directions."""
    groups = titles.get('groups') if isinstance(titles, dict) else None
    if not isinstance(groups, list) or len(groups) != 61:
        raise ValueError('exactly 61 original generated title groups required')
    by_id = {}
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError('generated title group object required')
        key, title = group.get('group'), group.get('title')
        if not isinstance(key, str) or not key.strip() or key in by_id:
            raise ValueError('nonempty unique generated title group IDs required')
        if not isinstance(title, str) or not title.strip():
            raise ValueError('nonempty exact generated titles required')
        by_id[key] = title
    rows = []
    for a_id, a in by_id.items():
        for b_id, b in by_id.items():
            if a_id == b_id:
                continue
            row = dict(id=f'{a_id}-contains-{b_id}', a_id=a_id, b_id=b_id, a=a, b=b,
                       domain='generated-titles', format='topic')
            row['model_input'] = model_input(row, 'topic')
            rows.append(row)
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('generated pair IDs must be unique')
    return rows


def freeze_inputs(titles_path, expected_sha256, output):
    """Freeze all title/input/source bytes before checkpoint hashing or loading."""
    raw = titles_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('frozen source title bytes changed')

    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate JSON key: ' + key)
            value[key] = item
        return value

    inputs = prepare_inputs(json.loads(raw, object_pairs_hook=unique_keys))
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'titles.json').open('xb') as stream:
        stream.write(raw)
    save_json(output / 'inputs.json', inputs)
    source_hashes = {}
    for source in (Path(__file__), Path(true_holdout_probe.__file__),
                   Path(true_category_probe.__file__), Path(hierarcaps_mask_probe.__file__)):
        with (output / source.name).open('xb') as stream:
            stream.write(source.read_bytes())
        source_hashes[source.name] = sha256(output / source.name)
    save_json(output / 'started.json', dict(experiment='TRUE04', model_id=MODEL_ID,
        python_version=sys.version, python_executable=sys.executable,
        revision=REVISION, source_titles_sha256=digest,
        inputs_sha256=sha256(output / 'inputs.json'),
        runner_sha256=source_hashes[Path(__file__).name],
        scorer_sha256=source_hashes[Path(true_category_probe.__file__).name],
        source_sha256=source_hashes, primary_format='topic', threshold=THRESHOLD,
        threshold_rule='entailment_score > 0.142', groups=61, pairs=len(inputs),
        unordered_pairs=len(inputs)//2, batch_size=4, dtype='float32', device='cpu', threads=4))
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('titles', 'output'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--titles-sha256', required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--prepare-only', action='store_true',
                        help='freeze inputs and source bytes without loading a model')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; earlier or interrupted runs must be preserved')
    started = time.monotonic()
    if not args.prepare_only:
        if args.snapshot is None:
            parser.error('--snapshot is required unless --prepare-only is used')
        snapshot = args.snapshot.resolve(strict=True)
        if (snapshot.name != REVISION or snapshot.parent.name != 'snapshots'
                or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
            raise ValueError('exact pinned model snapshot required')
    inputs = freeze_inputs(args.titles, args.titles_sha256, args.output)
    if args.prepare_only:
        print(f'Frozen {len(inputs)} inputs; no model loaded.', flush=True)
        return
    run_inference(snapshot, inputs, args.output, 4, started, experiment='TRUE04')


if __name__ == '__main__':
    main()
