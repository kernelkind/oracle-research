"""Compare native-answer and fixed-cutoff graphs using saved TRUE10 outputs.

No inference, score edits, new equivalence decisions, or semantic edge repairs.
"""
import json
from collections import Counter, deque
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
BASE = HERE.parent / 'TRUE10'
sys.path.insert(0, str(CODE))
from hierarcaps_mask_probe import save_json, sha256
from true_category_graph import build_graph
from true_graph_notes import derive_note_memberships


def read(path):
    return json.loads(path.read_text())


def path_to(graph, a, b):
    adjacency = {n['group']: [] for n in graph['nodes']}
    for edge in graph['raw_edges']:
        adjacency[edge['a_id']].append(edge['b_id'])
    pending, seen = deque([[a]]), {a}
    while pending:
        path = pending.popleft()
        for child in adjacency[path[-1]]:
            if child == b:
                return path + [child]
            if child not in seen:
                seen.add(child)
                pending.append(path + [child])
    return None


def root_coverage(graph, notes):
    reachable = set(graph['roots'])
    for key in graph['roots']:
        reachable.update(graph['reachability'][key])
    note_ids = sorted({key for n in notes['nodes'] if n['group'] in reachable
                       for key in n['own_note_ids']})
    return dict(categories=len(reachable), notes=len(note_ids), note_ids=note_ids,
                caveat='Reachability from indegree-zero roots, not semantic validation or a deployed UI measurement.')


def main():
    if (HERE / 'plan.json').exists():
        raise ValueError('TRUE11 already exists; preserve its results')
    paths = [BASE / name for name in ['derived/canonical.json', 'derived/graph.json',
        'derived/notes.json', 'derived/completion.json', 'derived/semantic-comparison.json',
        'additional-semantic-review.json', 'analysis-plan.json', 'graph/scores.json']]
    for name, digest in read(BASE / 'derived/completion.json')['files'].items():
        if sha256(BASE / 'derived' / name) != digest:
            raise ValueError('TRUE10 derived artifact changed: '+name)
    code_paths = [Path(__file__), CODE/'true_category_graph.py', CODE/'true_graph_notes.py',
                  CODE/'true_category_probe.py', CODE/'true_holdout_probe.py']
    plan = dict(experiment='TRUE11', base_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True, cwd=ROOT).strip(), tracking_card='CREC-127',
        question='What changes in category paths and note availability when the graph uses native answers instead of the fixed 0.142 cutoff?',
        control='TRUE10 canonical cutoff graph, unchanged.',
        variable='Edge acceptance only: complete generated native class 1 rather than score strictly greater than 0.142.',
        interpretation='Retrospective deterministic comparison of saved outputs; prior pairwise results already suggested both cycle removal and lost useful links. This is not a blinded new model evaluation.',
        unchanged=['exact titles', 'source masks and notes', 'every saved model output',
                   'reviewed Coffee and Bitcoin equivalences', 'all 58 canonical categories'],
        measures=['raw and reduced connections', 'cycles and root access',
                  'all ordered category paths', 'per-category available notes',
                  'independent semantic judgments with uncertainties retained'],
        forbidden=['inference', 'cutoff tuning', 'new titles', 'new equivalences',
                   'semantic repairs', 'new UI', 'automatic selection of a replacement rule'],
        resources=dict(model_calls=0, paid_calls=0, algorithm='small in-memory graph operations'),
        inputs_sha256={str(p.relative_to(ROOT)):sha256(p) for p in paths},
        code_sha256={str(p.relative_to(ROOT)):sha256(p) for p in code_paths})
    save_json(HERE/'plan.json', plan)
    (HERE/'source').mkdir()
    for path in code_paths:
        shutil.copyfile(path, HERE/'source'/path.name)

    canonical = read(BASE/'derived/canonical.json')
    titles, rows = canonical['titles'], canonical['scores']
    cutoff = build_graph(titles, rows)
    if cutoff != read(BASE/'derived/graph.json'):
        raise ValueError('cutoff graph no longer reproduces TRUE10')
    native = build_graph(titles, rows, decision_rule='native')
    cutoff_notes = derive_note_memberships(cutoff, canonical['source_packets'])
    if cutoff_notes != read(BASE/'derived/notes.json'):
        raise ValueError('cutoff memberships no longer reproduce TRUE10')
    native_notes = derive_note_memberships(native, canonical['source_packets'])
    for old, new in zip(cutoff_notes['nodes'], native_notes['nodes']):
        for key in ['group', 'title', 'matched_instances', 'own_note_ids', 'own_note_count']:
            if old[key] != new[key]:
                raise ValueError('source membership changed')

    aliases = {g['group']: g['group'] for g in titles['groups']}
    raw_scores = {(r['a_id'],r['b_id']):r for r in read(BASE/'graph/scores.json')}
    for approval in read(BASE/'analysis-plan.json')['main_equivalence_judgments']:
        for a in approval['members']:
            aliases[a] = approval['canonical']
            for b in approval['members']:
                if a != b and raw_scores[a,b]['predicted'] is not True:
                    raise ValueError('reviewed equivalence not mutually accepted in native outputs')

    note_maps = {rule: {n['group']:n for n in memberships['nodes']}
                 for rule,memberships in [('cutoff',cutoff_notes),('native',native_notes)]}
    changed = [r for r in rows if r['predicted'] is not r['threshold_predicted']]
    route_changes = []
    for row in rows:
        a,b = row['a_id'],row['b_id']
        old,new = b in cutoff['reachability'][a], b in native['reachability'][a]
        if old != new:
            route_changes.append(dict(a_id=a,b_id=b,a=row['a'],b=row['b'],
                cutoff_path=path_to(cutoff,a,b), native_path=path_to(native,a,b)))
    note_changes=[]
    for node in titles['groups']:
        key=node['group']
        old=set(note_maps['cutoff'][key]['recursive_note_ids'])
        new=set(note_maps['native'][key]['recursive_note_ids'])
        note_changes.append(dict(group=key,title=node['title'],own_notes=note_maps['native'][key]['own_note_count'],
            cutoff_notes=len(old),native_notes=len(new),lost_note_ids=sorted(old-new),gained_note_ids=sorted(new-old)))

    judgments=[]
    initial=read(BASE/'derived/semantic-comparison.json')
    additional=read(BASE/'additional-semantic-review.json')['directions']
    for source, items in [('TRUE10 initial independent review', initial), ('TRUE10 additional post-score review', additional)]:
        for item in items:
            a,b=aliases[item['a_id']],aliases[item['b_id']]
            if a==b:
                continue
            expected=item['independent_judgment'] if source.startswith('TRUE10 initial') else item['judgment']
            detail=dict(a_id=a,b_id=b,a=item['a'],b=item['b'],original_a_id=item['a_id'],original_b_id=item['b_id'],
                expected=expected,reason=item['reason'],judgment_source=source)
            for rule,g in [('cutoff',cutoff),('native',native)]:
                available=set(note_maps[rule][a]['recursive_note_ids'])
                child=set(note_maps[rule][b]['own_note_ids'])
                detail[rule]=dict(path=path_to(g,a,b),child_own_notes=len(child),
                    available_child_note_ids=sorted(child & available),missing_child_note_ids=sorted(child-available))
            judgments.append(detail)

    if native['transitive_reduced_edges'] is not None:
        reduced_pairs={(e['a_id'],e['b_id']) for e in native['transitive_reduced_edges']}
        adjacency={n['group']:[] for n in titles['groups']}
        for a,b in reduced_pairs: adjacency[a].append(b)
        for a in adjacency:
            seen=set(); pending=list(adjacency[a])
            while pending:
                b=pending.pop()
                if b not in seen: seen.add(b); pending.extend(adjacency[b])
            if seen!=set(native['reachability'][a]): raise ValueError('reduction lost paths')

    summary=dict(experiment='TRUE11',cutoff_stats=cutoff['stats'],native_stats=native['stats'],
        own_membership_unchanged=True,mask_and_note_stats=native_notes['stats'],
        cutoff_root_coverage=root_coverage(cutoff,cutoff_notes),native_root_coverage=root_coverage(native,native_notes),
        changed_direct_decisions=len(changed),lost_category_routes=sum(r['native_path'] is None for r in route_changes),
        gained_category_routes=sum(r['cutoff_path'] is None for r in route_changes),
        categories_with_changed_notes=sum(bool(r['lost_note_ids'] or r['gained_note_ids']) for r in note_changes),
        reduced_native_paths_verified=native['transitive_reduced_edges'] is not None,
        caveat='Lost inherited notes may remove contamination or lose valid placements. Neither root access nor note counts establish semantic correctness. Assistant judgments are not user-approved truth; repeated alias directions remain explicitly identifiable.')
    for name,value in [('native-graph.json',native),('native-notes.json',native_notes),
            ('changed-decisions.json',changed),('route-changes.json',route_changes),
            ('note-changes.json',note_changes),('semantic-comparison.json',judgments),('comparison.json',summary)]:
        save_json(HERE/name,value)
    for path,digest in plan['inputs_sha256'].items():
        if sha256(ROOT/path)!=digest: raise ValueError('baseline mutated: '+path)
    save_json(HERE/'completion.json',dict(inputs_unchanged=True,
        files={p.name:sha256(p) for p in HERE.glob('*.json')},
        run_code_sha256=sha256(Path(__file__)),model_calls=0))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
