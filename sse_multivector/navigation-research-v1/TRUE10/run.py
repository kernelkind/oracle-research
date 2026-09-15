"""TRUE10: freeze current-title coverage, infer missing strings, build raw graph."""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION
from true_category_graph import prepare_inputs, build_graph
from true_score_reuse import plan_reuse, assemble_scores, validate_cache_identity
from true_holdout_probe import run_inference

SHARED = ('true_holdout_probe.py', 'true_category_probe.py', 'hierarcaps_mask_probe.py')
TITLES = CODE / 'hdbv2-node-titles-v21-astra-low/titles.json'
TITLES_SHA = '693223548b17e439ac433dd2f9aaba9b830a2c97d5e68798379e8f784fb66799'
EXCLUDED = 'Sf5a4b23523'
REFERENCE = HERE.parent / 'TRUE09/run'
SNAPSHOT = Path('/home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots') / REVISION


def read(path):
    return json.loads(path.read_text())


def identity(path):
    return dict(config=read(path / 'config.json'),
                model_files_sha256=sha256(path / 'model-files.json'),
                source_sha256={name: sha256(path / name) for name in SHARED})


def prepare():
    if (HERE / 'plan.json').exists():
        raise ValueError('experiment already prepared; preserve it')
    if sha256(TITLES) != TITLES_SHA:
        raise ValueError('current title artifact changed')
    titles = read(TITLES)
    if len(titles['groups']) != 61 or sum(g['group'] == EXCLUDED for g in titles['groups']) != 1:
        raise ValueError('unexpected source categories')
    selected = dict(titles, groups=[g for g in titles['groups'] if g['group'] != EXCLUDED])
    inputs = prepare_inputs(selected)
    reference = identity(REFERENCE)
    if reference['source_sha256'] != {name: sha256(CODE / name) for name in SHARED}:
        raise ValueError('current scoring source changed from TRUE09')
    cache_runs, cache_records, preserve = [], [], {str(TITLES.relative_to(ROOT)): TITLES_SHA}
    # Fixed newest-to-oldest precedence, never select by favorable score.
    for number in range(9, 3, -1):
        path = HERE.parent / f'TRUE{number:02}'
        if number != 4:
            path = path / 'run'
        actual = identity(path)
        validate_cache_identity(actual, reference)
        started, completion = read(path / 'started.json'), read(path / 'completion.json')
        for name in SHARED:
            if started['source_sha256'][name] != actual['source_sha256'][name]:
                raise ValueError('saved source manifest differs: ' + str(path / name))
        for name, field in [('scores.jsonl', 'scores_sha256'), ('first-token-logits.npy', 'logits_sha256')]:
            if sha256(path / name) != completion[field]:
                raise ValueError('saved raw results changed: ' + str(path / name))
        for name in ('config.json', 'model-files.json', 'started.json', 'completion.json',
                     'scores.jsonl', 'first-token-logits.npy', *SHARED):
            preserve[str((path / name).relative_to(ROOT))] = sha256(path / name)
        source = str((path / 'scores.jsonl').relative_to(ROOT))
        rows = [json.loads(line) for line in (path / 'scores.jsonl').read_text().splitlines()]
        cache_runs.append((source, rows))
        cache_records.append(dict(path=source, rows=len(rows), identity=actual))
    reuse = plan_reuse(inputs, cache_runs)
    source_hashes = {}
    code_paths = [Path(__file__), *(CODE / name for name in
                 (*SHARED, 'true_score_reuse.py', 'true_category_graph.py'))]
    snapshot_dir = HERE / 'source'
    snapshot_dir.mkdir(exist_ok=False)
    for path in code_paths:
        shutil.copyfile(path, snapshot_dir / path.name)
        source_hashes[str(path.relative_to(ROOT))] = sha256(path)
    preserve.update(source_hashes)
    plan = dict(experiment='TRUE10', approval='User approved the provisional current-title graph process.',
        base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        tracking_card='CREC-127', source_titles=str(TITLES.relative_to(ROOT)), source_titles_sha256=TITLES_SHA,
        excluded=[dict(group=EXCLUDED, reason='Previously rejected coffee-chain category; unchanged exclusion.')],
        groups=len(selected['groups']), distinct_titles=len({g['title'] for g in selected['groups']}),
        directions=len(inputs), distinct_inputs=reuse['distinct_inputs'],
        reused_distinct_inputs=len(reuse['reused']), fresh_distinct_inputs=len(reuse['missing_inputs']),
        repeated_input_conflicts=len(reuse['conflicts']),
        threshold=0.142, threshold_rule='entailment_score > 0.142',
        model_id=MODEL_ID, revision=REVISION, snapshot=str(SNAPSHOT),
        scope='Current exact titles; every distinct group-ID direction; no cosine filter; no new labels or nodes.',
        interpretation='Uncorrected provisional graph, not proof that TRUE or the category hierarchy is adequate.',
        cycles='Flag all mutual acceptance/cycles. Never infer equivalence merely from scores or matching titles.',
        reduction='Remove redundant edges only in an acyclic graph; preserve raw edges and reachability.',
        semantics='Independent collection-level analysis. Uncertainty is not correctness; do not auto-fill unknown judgments.',
        cache_policy='Exact model_input equality plus matching model/scorer/config. Fixed latest-first precedence. Conflicting native/cutoff decisions are rescored. Expand identical strings to all distinct group IDs.',
        source_priority=cache_records, preservation_sha256=preserve,
        resources=dict(local=True, offline=True, paid_calls=0, model_processes=1,
                       memory_max_gib=60, memory_swap_max=0, cpu_quota_percent=400,
                       threads=4, batch_size=4, dtype='float32'),
        out_of_scope=['new frontier judge', 'prompt revision', 'cutoff tuning', 'mask changes',
                      'invented parents', 'semantic repairs', 'new UI'])
    save_json(HERE / 'titles.json', selected)
    save_json(HERE / 'inputs.json', inputs)
    save_json(HERE / 'reuse.json', reuse)
    save_json(HERE / 'plan.json', plan)
    frozen_names = ['titles.json', 'inputs.json', 'reuse.json', 'plan.json', 'run.py']
    save_json(HERE / 'frozen.json', dict(experiment='TRUE10',
        frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        files={name: sha256(HERE / name) for name in frozen_names}))
    print(json.dumps({k: plan[k] for k in ('groups', 'distinct_titles', 'directions', 'distinct_inputs',
          'reused_distinct_inputs', 'fresh_distinct_inputs', 'repeated_input_conflicts')}, indent=2), flush=True)


def verify_frozen():
    for name, digest in read(HERE / 'frozen.json')['files'].items():
        if sha256(HERE / name) != digest:
            raise ValueError('frozen file changed: ' + name)
    for name, digest in read(HERE / 'plan.json')['preservation_sha256'].items():
        if sha256(ROOT / name) != digest:
            raise ValueError('preserved source changed: ' + name)


def infer():
    started = time.monotonic()
    verify_frozen()
    output = HERE / 'run'
    output.mkdir(exist_ok=False)
    inputs = read(HERE / 'reuse.json')['missing_inputs']
    save_json(output / 'inputs.json', inputs)
    save_json(output / 'started.json', dict(experiment='TRUE10',
        frozen_sha256=sha256(HERE / 'frozen.json'), inputs_sha256=sha256(output / 'inputs.json'),
        source_sha256={p.name: sha256(p) for p in (HERE / 'source').iterdir()},
        python_version=sys.version, python_executable=sys.executable))
    run_inference(SNAPSHOT.resolve(strict=True), inputs, output, 4, started, experiment='TRUE10')
    actual = dict(identity(REFERENCE), config=read(output / 'config.json'),
                  model_files_sha256=sha256(output / 'model-files.json'))
    validate_cache_identity(actual, identity(REFERENCE))


def assemble():
    verify_frozen()
    output = HERE / 'graph'
    if not (HERE / 'run/completion.json').exists():
        raise ValueError('inference is incomplete; unscored is not No')
    fresh_path = HERE / 'run/scores.jsonl'
    if sha256(fresh_path) != read(HERE / 'run/completion.json')['scores_sha256']:
        raise ValueError('fresh scores changed')
    fresh = [json.loads(line) for line in fresh_path.read_text().splitlines()]
    rows = assemble_scores(read(HERE / 'inputs.json'), read(HERE / 'reuse.json'),
                           fresh, str(fresh_path.relative_to(ROOT)))
    graph = build_graph(read(HERE / 'titles.json'), rows)
    output.mkdir(exist_ok=False)
    save_json(output / 'scores.json', rows)
    save_json(output / 'graph.json', graph)
    save_json(output / 'completion.json', dict(experiment='TRUE10',
        scores_sha256=sha256(output / 'scores.json'), graph_sha256=sha256(output / 'graph.json'),
        graph_code_sha256=sha256(CODE / 'true_category_graph.py'), stats=graph['stats']))
    print(json.dumps(graph['stats'], indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'infer', 'assemble'])
    args = parser.parse_args()
    {'prepare': prepare, 'infer': infer, 'assemble': assemble}[args.phase]()
