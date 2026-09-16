"""TRUE14: complete the corrected Coffee/Tea branches using unchanged TRUE12 inference."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION
import true_mask_membership
import true_mask_inference
from true_score_reuse import validate_cache_identity

CODE = Path(__file__).resolve().parent
ROOT = CODE.parent
RESEARCH = CODE / 'navigation-research-v1'
REFERENCE = RESEARCH / 'TRUE12'
DEFAULT = RESEARCH / 'TRUE14'
BASELINE = RESEARCH / 'TRUE13/categories-with-mask-ids.json'
SOURCE = CODE / 'real-note-fine-segmentation-v1/reviewed-input.json'
MAPPING = CODE / 'real-note-fine-segmentation-v1/vectors/vector-map.json'
SHARED = ('true_mask_inference.py', 'true_category_probe.py',
          'hierarcaps_mask_probe.py', 'hierarcaps_category_probe.py', 'true_mask_membership.py')


def read(path):
    return json.loads(path.read_text())


def score_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def validate_scores(inputs, scores):
    expected = {r['id']: r for r in inputs}
    if len(expected) != len(inputs) or len(scores) != len(inputs):
        raise ValueError('complete unique input/score coverage required')
    seen = set()
    for row in scores:
        key = row['id']
        if key in seen or key not in expected or any(row.get(k) != v for k, v in expected[key].items()):
            raise ValueError('score changed, missing, duplicated or mismatched input')
        seen.add(key)
        score = row['entailment_score']
        if (not math.isfinite(score) or not 0 <= score <= 1
                or row['predicted'] is not None and type(row['predicted']) is not bool):
            raise ValueError('invalid saved score')


def plan_inputs(categories, reference_inputs, reference_scores):
    validate_scores(reference_inputs, reference_scores)
    nodes = {n['node_id']: n for n in categories['nodes']}
    roots = []
    for title in ('Coffee', 'Tea as a beverage'):
        matches = [n['node_id'] for n in nodes.values() if n['label'] == title]
        if len(matches) != 1:
            raise ValueError('one exact category required: ' + title)
        roots.extend(matches)
    selected = []

    def visit(key, path):
        if key in path:
            raise ValueError('cycle in category graph')
        if key not in selected:
            selected.append(key)
            for child in nodes[key]['children']:
                visit(child, path | {key})

    for root in roots:
        visit(root, set())
    expected_masks = {f'V{i:03d}' for i in range(1, 946)}
    for root in roots:
        rows = [r for r in reference_inputs if r['category_id'] == root]
        aliases = [m['short_id'] for row in rows for m in row['masks']]
        if (len(aliases) != 945 or set(aliases) != expected_masks
                or any(r['category_title'] != nodes[root]['label'] for r in rows)):
            raise ValueError('all original masks required for each reference category')
    if {r['category_id'] for r in reference_inputs} != set(roots):
        raise ValueError('reference contains unexpected categories')
    template = [r for r in reference_inputs if r['category_id'] == roots[0]]
    cached = {r['id']: r for r in reference_inputs}
    all_inputs, missing = [], []
    for key in selected:
        for original in template:
            row = deepcopy(original)
            row['category_id'], row['category_title'] = key, nodes[key]['label']
            row['model_input'] = f'premise: {row["premise"]} hypothesis: This text is about {row["category_title"]}.'
            row['id'] = 'M' + hashlib.sha256(row['model_input'].encode()).hexdigest()
            if row['id'] in cached:
                if row != cached[row['id']]:
                    raise ValueError('cached mask provenance differs')
            else:
                missing.append(row)
            all_inputs.append(row)
    return all_inputs, missing, [dict(id=k, title=nodes[k]['label']) for k in selected]


def prepare(output):
    if output.exists():
        raise FileExistsError(output)
    reference_inputs = read(REFERENCE / 'inputs.json')
    reference_scores = score_rows(REFERENCE / 'scores.jsonl')
    if sha256(REFERENCE / 'scores.jsonl') != read(REFERENCE / 'completion.json')['scores_sha256']:
        raise ValueError('reference scores changed')
    validated, _ = true_mask_membership.prepare_inputs(read(MAPPING), read(SOURCE),
        read(RESEARCH / 'TRUE13/native-graph.json'), read(RESEARCH / 'TRUE13/native-notes.json'))
    if validated != reference_inputs:
        raise ValueError('original input bytes or mask provenance changed')
    for name in SHARED:
        if sha256(CODE / name) != sha256(REFERENCE / 'source' / name):
            raise ValueError('inference implementation differs from TRUE12: ' + name)
    all_inputs, missing, targets = plan_inputs(read(BASELINE), reference_inputs, reference_scores)
    if len(all_inputs) != 5388 or len(missing) != 3592 or len(targets) != 6:
        raise ValueError('unexpected corrected branch inventory')
    paths = [BASELINE, SOURCE, MAPPING, RESEARCH / 'TRUE13/native-graph.json',
        RESEARCH / 'TRUE13/native-notes.json', REFERENCE / 'inputs.json',
        REFERENCE / 'scores.jsonl', REFERENCE / 'completion.json',
        REFERENCE / 'config.json', REFERENCE / 'model-files.json',
        *(REFERENCE / 'source' / name for name in SHARED),
        *(CODE / name for name in (*SHARED, 'true_score_reuse.py', 'true_holdout_probe.py')),
        Path(__file__)]
    plan = dict(experiment='TRUE14', tracking_card='CREC-127',
        purpose='Complete mask membership for the corrected Coffee/Tea branches, not new hierarchy edges.',
        created_utc=datetime.now(timezone.utc).isoformat(), targets=targets,
        original_masks=945, source_notes=100, unique_inputs=len(all_inputs),
        reused_inputs=len(reference_inputs), new_inputs=len(missing),
        logical_pairs=5670, new_logical_pairs=3780,
        model_id=MODEL_ID, revision=REVISION, threshold=0.142,
        decision='strict score > 0.142, additive; native answers retained separately',
        input_format='premise: {original fragments joined by one space} hypothesis: This text is about {exact category title}.',
        inference_implementation='Unchanged TRUE12 runner; its config.experiment remains TRUE12 as implementation identity. This experiment is TRUE14.',
        review='Agent analysis plus user inspection in existing hierarchy UI; no separate uncertainty queue.',
        resources=dict(local=True, offline=True, paid_calls=0, memory_max_gib=60,
            memory_swap_max=0, cpu_quota_percent=400, threads=4, batch_size=4),
        preservation_sha256={str(p.relative_to(ROOT)): sha256(p) for p in paths})
    output.mkdir(parents=True, exist_ok=False)
    save_json(output / 'inputs.json', all_inputs)
    save_json(output / 'new-inputs.json', missing)
    save_json(output / 'plan.json', plan)
    save_json(output / 'frozen.json', {n: sha256(output / n) for n in ('inputs.json', 'new-inputs.json', 'plan.json')})
    print(f'TRUE14 prepared: {len(targets)} categories, {len(reference_inputs)} reused, {len(missing)} new inputs.')


def verify(output):
    for name, expected in read(output / 'frozen.json').items():
        if sha256(output / name) != expected:
            raise ValueError('frozen input changed: ' + name)
    for name, expected in read(output / 'plan.json')['preservation_sha256'].items():
        if sha256(ROOT / name) != expected:
            raise ValueError('preserved input or implementation changed: ' + name)


def identity(run, sources):
    return dict(config=read(run / 'config.json'), model_files_sha256=sha256(run / 'model-files.json'),
        source_sha256={name: sha256(sources / name) for name in SHARED})


def infer(output):
    verify(output)
    available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    if available < 70 * 1024**2:
        raise ValueError('at least 70 GiB available memory required')
    cgroup = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    limits = {name: (cgroup / name).read_text().strip() for name in ('memory.max', 'memory.swap.max', 'cpu.max')}
    if limits['memory.max'] == 'max' or int(limits['memory.max']) > 60 * 1024**3 or limits['memory.swap.max'] != '0':
        raise ValueError('requires MemoryMax <=60GiB and MemorySwapMax=0')
    quota, period = limits['cpu.max'].split()
    if quota == 'max' or int(quota) > 4 * int(period):
        raise ValueError('requires CPUQuota <=400%')
    snapshot = true_mask_membership.validate_snapshot(Path.home() / '.cache/huggingface/hub' /
        ('models--' + MODEL_ID.replace('/', '--')) / 'snapshots' / REVISION)
    rows = read(output / 'new-inputs.json')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    maximum = max(len(ids) for ids in tokenizer([r['model_input'] for r in rows], truncation=False)['input_ids'])
    if maximum > 512:
        raise ValueError('input exceeds fixed token limit')
    target = output / 'run'
    target.mkdir(exist_ok=False)
    save_json(target / 'execution.json', dict(experiment='TRUE14', started_utc=datetime.now(timezone.utc).isoformat(),
        executable=sys.executable, argv=sys.argv, frozen_sha256=sha256(output / 'frozen.json'),
        cgroup=str(cgroup), enforced_limits=limits, maximum_tokens=maximum,
        inputs=len(rows), inference_implementation='Unmodified TRUE12', paid_resources=False))
    true_mask_inference.run_inference(snapshot, rows, target, 4, time.monotonic())
    validate_cache_identity(identity(target, CODE), identity(REFERENCE, REFERENCE / 'source'))
    validate_scores(rows, score_rows(target / 'scores.jsonl'))
    verify(output)
    save_json(output / 'verification.json', dict(experiment='TRUE14', cache_identity_matches=True,
        old_inputs=1796, new_inputs=len(rows), old_scores_unchanged=True,
        new_scores_sha256=sha256(target / 'scores.jsonl'), exact_coverage=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'verify', 'infer'))
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    globals()[args.phase](args.output)
