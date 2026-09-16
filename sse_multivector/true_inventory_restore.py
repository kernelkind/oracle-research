"""TRUE13: restore the omitted source group, preserving previous experiments."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

from hierarcaps_mask_probe import save_json, sha256
from true_category_graph import prepare_inputs, build_graph
from true_category_probe import REVISION
from true_graph_notes import derive_note_memberships
from true_graph_categories import export
from true_holdout_probe import run_inference
from true_score_reuse import validate_cache_identity

CODE = Path(__file__).resolve().parent
ROOT = CODE.parent
RESEARCH = CODE / 'navigation-research-v1'
DEFAULT = RESEARCH / 'TRUE13'
OLD = RESEARCH / 'TRUE10/derived/canonical.json'
TITLES = CODE / 'hdbv2-node-titles-v21-astra-low/titles.json'
SOURCE_PACKETS = CODE / 'hdbv2-node-titles-v20-astra-low/source-packets.json'
SOURCE = CODE / 'real-note-fine-segmentation-v1/reviewed-input.json'
MAPPING = CODE / 'real-note-fine-segmentation-v1/vectors/vector-map.json'
REFERENCE = RESEARCH / 'TRUE10/run'
REFERENCE_SOURCE = RESEARCH / 'TRUE10/source'
SHARED = ('true_holdout_probe.py', 'true_category_probe.py', 'hierarcaps_mask_probe.py')
RESTORED = 'Sf5a4b23523'


def read(path):
    return json.loads(path.read_text())


def restore(canonical, source_titles):
    result = deepcopy(canonical)
    group = deepcopy(next(g for g in source_titles['groups'] if g['group'] == RESTORED))
    group['title_override'] = dict(previous_title=group['title'],
        source='User requested the missing #coffeechain category; restoration approved.',
        reason='The model title failed; the underlying group was not rejected. '
               'Generation metadata and original title judgment below concern the previous title.')
    group['title'] = '#coffeechain'
    result['titles']['groups'].append(group)
    inputs = prepare_inputs(result['titles'],
        source_group_ids=[g['group'] for g in source_titles['groups']],
        consolidations=result['consolidations'])
    existing = {r['id']: r for r in result['scores']}
    expected = {r['id']: r for r in inputs}
    for key, row in existing.items():
        if key not in expected or any(row.get(k) != v for k, v in expected[key].items()):
            raise ValueError('existing score input changed: ' + key)
    return result, [row for row in inputs if row['id'] not in existing]


def prepare(output):
    if output.exists():
        raise FileExistsError(output)
    original, titles = read(OLD), read(TITLES)
    source_ids = [p['packet'] for p in read(SOURCE_PACKETS)['packets']]
    # Independently verify that the title file itself retained all source groups.
    prepare_inputs(titles, source_group_ids=source_ids)
    canonical, missing = restore(original, titles)
    if len(missing) != 116 or len(canonical['titles']['groups']) != 59:
        raise ValueError('unexpected frozen experiment inventory')
    paths = [OLD, TITLES, SOURCE_PACKETS, SOURCE, MAPPING,
             RESEARCH / 'TRUE11/native-graph.json', RESEARCH / 'TRUE11/categories.json',
             RESEARCH / 'TRUE12/hierarchy/baseline-categories.json',
             RESEARCH / 'TRUE12/hierarchy/categories.json',
             REFERENCE / 'config.json', REFERENCE / 'model-files.json',
             *(REFERENCE_SOURCE / name for name in SHARED),
             Path(__file__), *(CODE / name for name in (*SHARED, 'true_category_graph.py',
                 'true_graph_notes.py', 'true_graph_categories.py', 'true_score_reuse.py'))]
    plan = dict(experiment='TRUE13', tracking_card='CREC-127',
        purpose='Restore a source group omitted because of a title failure. No category selection.',
        source_group_ids=source_ids, groups_before=58, groups_after=59,
        existing_scores=3306, new_scores=116, restored=RESTORED,
        title='#coffeechain', title_source='User-supplied category name, not a generated title.',
        previous_grouping_rejections='The three earlier user grouping rejections stay unchanged; '
            'the 61-group source inventory already excludes them. No new grouping rejection.',
        resources=dict(local=True, offline=True, paid_calls=0, memory_max_gib=60,
                       memory_swap_max=0, cpu_quota_percent=400, threads=4, batch_size=4),
        preservation_sha256={str(p.relative_to(ROOT)): sha256(p) for p in paths})
    output.mkdir(parents=True)
    save_json(output / 'pending-canonical.json', canonical)
    save_json(output / 'missing-inputs.json', missing)
    save_json(output / 'plan.json', plan)
    save_json(output / 'frozen.json', {name: sha256(output / name) for name in
                                     ('pending-canonical.json', 'missing-inputs.json', 'plan.json')})
    print('TRUE13 prepared: 59 categories; 3,306 preserved scores; 116 new directions.')


def verify(output):
    for name, expected in read(output / 'frozen.json').items():
        if sha256(output / name) != expected:
            raise ValueError('frozen input changed: ' + name)
    for name, expected in read(output / 'plan.json')['preservation_sha256'].items():
        if sha256(ROOT / name) != expected:
            raise ValueError('preserved source changed: ' + name)


def identity(path, sources):
    return dict(config=read(path / 'config.json'),
        model_files_sha256=sha256(path / 'model-files.json'),
        source_sha256={name: sha256(sources / name) for name in SHARED})


def infer(output):
    verify(output)
    if {n: sha256(CODE / n) for n in SHARED} != identity(REFERENCE, REFERENCE_SOURCE)['source_sha256']:
        raise ValueError('inference source differs from baseline')
    available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()
                     if line.startswith('MemAvailable:'))
    if available < 70 * 1024**2:
        raise ValueError('at least 70 GiB available memory required')
    target = output / 'run'
    target.mkdir(exist_ok=False)
    save_json(target / 'started.json', dict(experiment='TRUE13', executable=sys.executable,
        frozen_sha256=sha256(output / 'frozen.json'),
        source_sha256={name: sha256(CODE / name) for name in SHARED}))
    snapshot = Path('/home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots') / REVISION
    run_inference(snapshot.resolve(strict=True), read(output / 'missing-inputs.json'),
                  target, 4, time.monotonic(), experiment='TRUE13')
    validate_cache_identity(identity(target, CODE), identity(REFERENCE, REFERENCE_SOURCE))


def retain_membership_additions(spec, baseline, expanded):
    """Carry forward saved additive memberships without changing any graph links."""
    if not spec['source_sha256'] == baseline['source_sha256'] == expanded['source_sha256']:
        raise ValueError('membership views use different note sources')
    result = deepcopy(spec)
    nodes = {n['node_id']: n for n in result['nodes']}
    before = {n['node_id']: n for n in baseline['nodes']}
    for node in expanded['nodes']:
        key = node['node_id']
        if key == expanded['root_node_id']:
            continue
        if key not in nodes or key not in before or node['children'] != before[key]['children']:
            raise ValueError('membership expansion changed category inventory or links')
        additions = set(node['note_ids']) - set(before[key]['note_ids'])
        nodes[key]['note_ids'] = sorted(set(nodes[key]['note_ids']) | additions)
        for short, spans in expanded['note_masks'][key].items():
            new = set(map(tuple, spans)) - set(map(tuple, baseline['note_masks'][key].get(short, [])))
            if new:
                old = result['note_masks'][key].get(short, [])
                result['note_masks'][key][short] = [list(s) for s in sorted(set(map(tuple, old)) | new)]
    visited = set()

    def inherit(key, path):
        if key in path:
            raise ValueError('cannot package cyclic category graph')
        if key in visited:
            return
        for child in nodes[key]['children']:
            inherit(child, path | {key})
            for short, spans in result['note_masks'][child].items():
                old = result['note_masks'][key].get(short, [])
                result['note_masks'][key][short] = [list(s) for s in sorted(
                    set(map(tuple, old)) | set(map(tuple, spans)))]
        visited.add(key)

    inherit(result['root_node_id'], set())
    registry = {n['note_short_id']: n['note_id'] for n in result['notes']}
    for note in expanded['notes']:
        if registry.get(note['note_short_id'], note['note_id']) != note['note_id']:
            raise ValueError('conflicting note IDs')
        registry[note['note_short_id']] = note['note_id']
    result['notes'] = [dict(note_short_id=short, note_id=registry[short])
                       for short in sorted(result['note_masks'][result['root_node_id']])]
    return result


def package(output):
    verify(output)
    run = output / 'run'
    if sha256(run / 'scores.jsonl') != read(run / 'completion.json')['scores_sha256']:
        raise ValueError('fresh score checksum differs')
    validate_cache_identity(identity(run, CODE), identity(REFERENCE, REFERENCE_SOURCE))
    canonical = read(output / 'pending-canonical.json')
    fresh = [json.loads(line) for line in (run / 'scores.jsonl').read_text().splitlines()]
    canonical['scores'].extend(fresh)
    prepare_inputs(canonical['titles'], source_group_ids=read(output / 'plan.json')['source_group_ids'],
                   consolidations=canonical['consolidations'])
    graph = build_graph(canonical['titles'], canonical['scores'], decision_rule='native')
    memberships = derive_note_memberships(graph, canonical['source_packets'])
    save_json(output / 'canonical.json', canonical)
    save_json(output / 'native-graph.json', graph)
    save_json(output / 'native-notes.json', memberships)
    # Cycles are preserved as evidence, never removed to force a usable display.
    export(output / 'canonical.json', output / 'native-graph.json', output / 'native-notes.json',
           SOURCE, MAPPING, output / 'baseline-categories.json', hierarchy_id='TRUE13 · restored inventory')
    spec = retain_membership_additions(read(output / 'baseline-categories.json'),
        read(RESEARCH / 'TRUE12/hierarchy/baseline-categories.json'),
        read(RESEARCH / 'TRUE12/hierarchy/categories.json'))
    spec['hierarchy_id'] = 'TRUE13 · all categories · saved Coffee/Tea additions'
    for node in spec['nodes']:
        count = len(spec['note_masks'][node['node_id']])
        node['analysis'] = (f'Native TRUE category links, without manual repairs. {count} notes including children. '
            'Original masks retained; saved TRUE12 Coffee/Tea membership additions retained. '
            'The #coffeechain title was supplied by the user; its original seven masks are unchanged.')
    save_json(output / 'categories.json', spec)
    save_json(output / 'completion.json', dict(stats=graph['stats'], notes=len(spec['notes']),
        output_sha256={name: sha256(output / name) for name in ('canonical.json', 'native-graph.json',
            'native-notes.json', 'baseline-categories.json', 'categories.json')}))
    print(json.dumps(graph['stats'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'infer', 'package', 'verify'])
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    globals()[args.phase](args.output)
