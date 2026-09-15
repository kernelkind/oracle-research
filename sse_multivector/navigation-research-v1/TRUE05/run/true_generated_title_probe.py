"""TRUE03: frozen actual generated-title pairs, with unchanged TRUE02 inference."""
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


def prepare_inputs(fixture, titles):
    """Resolve exact source titles; never infer, repair, or expose expected labels."""
    if (not isinstance(fixture, dict) or fixture.get('experiment') != 'TRUE03'
            or fixture.get('threshold') != THRESHOLD):
        raise ValueError('TRUE03 fixture with the frozen threshold 0.142 required')
    digest = fixture.get('source_titles_sha256')
    if (not isinstance(digest, str) or len(digest) != 64
            or any(character not in '0123456789abcdef' for character in digest)):
        raise ValueError('source title SHA-256 required')
    groups = titles.get('groups') if isinstance(titles, dict) else None
    if not isinstance(groups, list) or not groups:
        raise ValueError('nonempty generated title groups required')
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
    pairs = fixture.get('pairs')
    if not isinstance(pairs, list) or not pairs:
        raise ValueError('nonempty frozen pair list required')
    seen_ids, seen_pairs, rows = set(), set(), []
    for pair in pairs:
        if not isinstance(pair, dict):
            raise ValueError('pair object required')
        pair_id = pair.get('id')
        if not isinstance(pair_id, str) or not pair_id.strip() or pair_id in seen_ids:
            raise ValueError('nonempty unique pair IDs required')
        a_id, b_id = pair.get('a_id'), pair.get('b_id')
        if (not all(isinstance(key, str) and key in by_id for key in (a_id, b_id))
                or a_id == b_id):
            raise ValueError('two distinct known generated title IDs required')
        key = tuple(sorted((a_id, b_id)))
        if key in seen_pairs:
            raise ValueError('duplicate unordered generated title pair')
        forward, reverse = pair.get('a_contains_b'), pair.get('b_contains_a')
        if not all(type(value) is bool for value in (forward, reverse)):
            raise ValueError('both explicit Boolean containment judgments required')
        rationale = pair.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError('nonempty pre-inference rationale required')
        seen_ids.add(pair_id)
        seen_pairs.add(key)
        for direction, a, b, expected, opposite in (
                ('a-contains-b', a_id, b_id, forward, reverse),
                ('b-contains-a', b_id, a_id, reverse, forward)):
            kind = ('equivalent' if opposite else 'strict-containment') if expected else (
                'reversed-containment' if opposite else 'noncontaining')
            row = dict(id=f'{pair_id}-{direction}', a_id=a, b_id=b, a=by_id[a], b=by_id[b],
                domain='generated-titles', kind=kind, format='topic', expected=expected)
            row['model_input'] = model_input(row, 'topic')
            rows.append(row)
    return rows


def freeze_inputs(fixture_path, expected_sha256, titles_path, output):
    """Freeze all input and implementation bytes before checkpoint hashing or loading."""
    raw = fixture_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('frozen fixture bytes changed')

    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate JSON key: ' + key)
            value[key] = item
        return value

    fixture = json.loads(raw, object_pairs_hook=unique_keys)
    title_bytes = titles_path.read_bytes()
    title_digest = hashlib.sha256(title_bytes).hexdigest()
    if not isinstance(fixture, dict) or title_digest != fixture.get('source_titles_sha256'):
        raise ValueError('frozen source title bytes changed')
    inputs = prepare_inputs(fixture, json.loads(title_bytes, object_pairs_hook=unique_keys))
    output.mkdir(parents=True, exist_ok=False)
    for name, content in (('fixture.json', raw), ('titles.json', title_bytes)):
        with (output / name).open('xb') as stream:
            stream.write(content)
    save_json(output / 'inputs.json', inputs)
    source_hashes = {}
    for source in (Path(__file__), Path(true_holdout_probe.__file__),
                   Path(true_category_probe.__file__), Path(hierarcaps_mask_probe.__file__)):
        with (output / source.name).open('xb') as stream:
            stream.write(source.read_bytes())
        source_hashes[source.name] = sha256(output / source.name)
    save_json(output / 'started.json', dict(experiment='TRUE03', model_id=MODEL_ID,
        python_version=sys.version, python_executable=sys.executable,
        revision=REVISION, fixture_sha256=digest, source_titles_sha256=title_digest,
        inputs_sha256=sha256(output / 'inputs.json'),
        runner_sha256=source_hashes[Path(__file__).name],
        scorer_sha256=source_hashes[Path(true_category_probe.__file__).name],
        source_sha256=source_hashes, primary_format='topic', threshold=THRESHOLD,
        threshold_rule='entailment_score > 0.142', pairs=len(inputs),
        unordered_pairs=len(fixture['pairs'])))
    return inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('fixture', 'titles', 'output', 'snapshot'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--fixture-sha256', required=True)
    parser.add_argument('--batch-size', type=int, default=4, choices=(1, 2, 4))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; earlier or interrupted runs must be preserved')
    started = time.monotonic()
    snapshot = args.snapshot.resolve(strict=True)
    if (snapshot.name != REVISION or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('exact pinned model snapshot required')
    inputs = freeze_inputs(args.fixture, args.fixture_sha256, args.titles, args.output)
    run_inference(snapshot, inputs, args.output, args.batch_size, started, experiment='TRUE03')


if __name__ == '__main__':
    main()
