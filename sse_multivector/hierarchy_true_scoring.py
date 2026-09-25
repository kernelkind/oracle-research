#!/usr/bin/env python3
"""Freeze, score and collect current-title TRUE inputs using verified saved caches.

The scorer and native-answer rules are unchanged. Only infer performs inference.
A cache bundle supplies the already-verified plan/reference/run from a prior run.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

from hierarchy_build import artifact_directory, read, save, consolidate_nodes, titles_from_report
from hierarcaps_mask_probe import sha256
from true_category_graph import prepare_inputs, build_graph
from true_graph_merge import POLICIES
from true_score_reuse import plan_reuse, assemble_scores, validate_cache_identity

CODE = Path(__file__).resolve().parent
ROOT = CODE.parent
SHARED = ('true_holdout_probe.py', 'true_category_probe.py', 'hierarcaps_mask_probe.py')


def path(value):
    return (ROOT / value).resolve()


def run_identity(run, sources):
    return dict(config=read(run/'config.json'), model_files_sha256=sha256(run/'model-files.json'),
                source_sha256=sources)


def prepare(titles_directory, cache_bundle, output):
    titles_directory, cache_bundle = Path(titles_directory).resolve(), Path(cache_bundle).resolve()
    nodes = read(titles_directory/'nodes.json')
    if consolidate_nodes(nodes['source']) != nodes:
        raise ValueError('saved node consolidation changed')
    titles = titles_from_report(nodes['source_packets'], read(titles_directory/'title-report.json'))
    inputs = prepare_inputs(titles)
    if titles != read(titles_directory/'titles.json') or inputs != read(titles_directory/'true-inputs.json'):
        raise ValueError('saved titles or TRUE inputs changed')
    reference = read(cache_bundle/'reference.json')
    sources = {n:sha256(CODE/n) for n in SHARED}
    if sources != reference['source_sha256']:
        raise ValueError('TRUE scorer differs from saved reference')
    old_plan = read(cache_bundle/'plan.json')
    if sha256(cache_bundle/'plan.json') != read(cache_bundle/'run/started.json')['plan_sha256']:
        raise ValueError('cache bundle plan changed')
    old_protected = {str(path(p)):h for p,h in old_plan['protected_sha256'].items()}
    if any(old_protected.get(str(CODE/n)) != sources[n] for n in SHARED):
        raise ValueError('cache bundle does not attest the current scorer')
    protected = {}

    def protect(p):
        p = Path(p).resolve()
        digest = sha256(p)
        if str(p) in old_protected and old_protected[str(p)] != digest:
            raise ValueError('cache bundle protected file changed: ' + str(p))
        protected[str(p)] = digest

    caches = []
    for source in old_plan['cache_sources'] + [str(cache_bundle/'run/scores.jsonl')]:
        source = path(source); run = source.parent
        validate_cache_identity(run_identity(run, sources), reference)
        if sha256(source) != read(run/'completion.json')['scores_sha256']:
            raise ValueError('cached scores changed: ' + str(source))
        for filename in ('scores.jsonl','config.json','model-files.json','completion.json'):
            protect(run/filename)
        caches.append((str(source), [json.loads(line) for line in source.read_text().splitlines()]))
    reuse = plan_reuse(inputs, caches)
    for p in [cache_bundle/'plan.json', cache_bundle/'reference.json', cache_bundle/'run/started.json',
              *(titles_directory/n for n in ('nodes.json','title-report.json','titles.json','true-inputs.json')),
              *(CODE/n for n in (*SHARED,'hierarchy_true_scoring.py','hierarchy_build.py',
                                  'true_score_reuse.py','true_category_graph.py'))]:
        protect(p)
    out = artifact_directory(output)
    save(out/'inputs.json', inputs)
    save(out/'reuse.json', reuse)
    save(out/'reference.json', reference)
    for filename in ('inputs.json','reuse.json','reference.json'):
        protect(out/filename)
    plan = dict(schema_version=1, experiment='HRv1-full-v38', title_directory=str(titles_directory),
                policies=POLICIES, nodes=len(titles['groups']), directions=len(inputs),
                distinct_inputs=reuse['distinct_inputs'], reused_inputs=len(reuse['reused']),
                fresh_inputs=len(reuse['missing_inputs']), conflicts=len(reuse['conflicts']),
                protected_sha256=protected, resources=dict(device='cpu',threads=4,batch_size=4),
                scope='All saved nodes; no membership expansion, cosine filtering or semantic repairs.')
    save(out/'plan.json', plan)
    save(out/'frozen.json', dict(plan_sha256=sha256(out/'plan.json')))
    return plan


def verify(output):
    output = Path(output)
    if sha256(output/'plan.json') != read(output/'frozen.json')['plan_sha256']:
        raise ValueError('frozen scoring plan changed')
    plan = read(output/'plan.json')
    for name, digest in plan['protected_sha256'].items():
        if sha256(Path(name)) != digest:
            raise ValueError('protected input changed: ' + name)
    return plan


def infer(output):
    output = Path(output)
    plan = verify(output)
    inputs = read(output/'reuse.json')['missing_inputs']
    if not inputs:
        return
    reference = read(output/'reference.json')
    for name, version in reference['config']['packages'].items():
        if importlib.metadata.version(name) != version:
            raise ValueError('inference package differs: ' + name)
    available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    if available < 70 * 1024**2:
        raise ValueError('TRUE requires 70 GiB available memory before loading')
    from true_category_probe import REVISION
    from true_holdout_probe import run_inference
    snapshot = Path.home()/'.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots'/REVISION
    run = artifact_directory(output/'run')
    save(run/'inputs.json', inputs)
    save(run/'started.json', dict(plan_sha256=sha256(output/'plan.json'),
                                 inputs_sha256=sha256(run/'inputs.json'), python_executable=sys.executable))
    run_inference(snapshot.resolve(strict=True), inputs, run, 4, time.monotonic(), experiment=plan['experiment'])
    validate_cache_identity(run_identity(run, reference['source_sha256']), reference)


def collect(output):
    output = Path(output)
    plan = verify(output)
    reuse = read(output/'reuse.json')
    fresh_path = output/'run/scores.jsonl'
    fresh = []
    if reuse['missing_inputs']:
        run = fresh_path.parent
        if sha256(fresh_path) != read(run/'completion.json')['scores_sha256']:
            raise ValueError('fresh scores changed or incomplete')
        reference = read(output/'reference.json')
        validate_cache_identity(run_identity(run, reference['source_sha256']), reference)
        fresh = [json.loads(line) for line in fresh_path.read_text().splitlines()]
    rows = assemble_scores(read(output/'inputs.json'),reuse,fresh,str(fresh_path.resolve()))
    graph = build_graph(read(Path(plan['title_directory'])/'titles.json'),rows,decision_rule='native')
    if graph['unresolved_native_rows']:
        raise ValueError('unresolved TRUE answers require recovery, not No labels')
    save(output/'scores.json',rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='phase',required=True)
    p = sub.add_parser('prepare')
    for arg in ('titles','cache_bundle','output'): p.add_argument(arg,type=Path)
    for phase in ('infer','collect','verify'): sub.add_parser(phase).add_argument('output',type=Path)
    args = parser.parse_args()
    try:
        if args.phase == 'prepare':
            plan = prepare(args.titles,args.cache_bundle,args.output)
            print(json.dumps({k:plan[k] for k in ('nodes','directions','distinct_inputs','reused_inputs','fresh_inputs','conflicts')}))
        elif args.phase == 'infer': infer(args.output)
        elif args.phase == 'collect': print('Collected',len(collect(args.output)),'directed answers')
        else: verify(args.output); print('Frozen scoring inputs verified')
    except (ValueError,KeyError,OSError) as error:
        parser.exit(1,f'{error}\n')


if __name__ == '__main__': main()
