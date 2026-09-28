"""Offline, single-pass cross-branch comparison and reversible consolidation.

All inference, request reuse and receipts belong to experiment.py. No command
changes its input groups or adds a second round of comparison candidates.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from experiment import report, load
from hierarchy_build import artifact_directory, read, save, titles_from_report, prepare_naming
from decision_hierarchy import make_cases, merge_report
from experiment_inputs import render
from hdbscan_nested_groups import (replay, answer_catalog, expected_merges,
    expected_titles, bind_saved, MERGE_PROMPT, TITLE)
from merge_tree_nesting import mask_pair_cases, contract_equivalence, _validate_choices
from prepare_category_title_inputs import prepare as prepare_titles
from prominence_centroid import centroid
from prominence_cosine import cosine
from true_graph_merge import union_packet, _digest

PLACEMENT=Path(__file__).resolve().parent/'node-subsumption-prompt-jev-v3/prompt.txt'


def select_pairs(packets, titles, vectors, *, k=5):
    """Union two directed top-k lists, retaining deterministic selection evidence."""
    if type(k) is not int or k<1:
        raise ValueError('positive integer neighbor count required')
    ids=sorted(titles)
    if set(ids)!={p['packet'] for p in packets['packets']}:
        raise ValueError('titles must cover exactly the supplied groups')
    by_id={r['opaque_id']:r['normalized_vector'] for r in vectors}
    if len(by_id)!=len(vectors):
        raise ValueError('duplicate vector ID')
    means={};members={}
    for p in prepare_titles(packets,'{NUMBERED_INSTANCES}',ids):
        try:
            rows=[by_id[s['source_vector_ids'][0]] for s in p['sources']]
        except KeyError as error:
            raise ValueError('missing source vector') from error
        if any(not math.isclose(math.fsum(x*x for x in r),1,abs_tol=1e-5) for r in rows):
            raise ValueError('finite unit source vectors required')
        means[p['group']]=centroid(rows)
        members[p['group']]={(s['note_id'],tuple(map(tuple,s['byte_spans']))) for s in p['sources']}
    normalized={g:titles[g].strip().casefold() for g in ids}
    if any(not title for title in normalized.values()):
        raise ValueError('nonempty titles required')
    scores={(a,b):cosine(means[a],means[b]) for i,a in enumerate(ids) for b in ids[i+1:]
            if not members[a]&members[b]}
    selected={}
    for g in ids:
        neighbors=[h for h in ids if tuple(sorted((g,h))) in scores]
        neighbors.sort(key=lambda h:(-scores[tuple(sorted((g,h)))],h))
        same=[h for h in neighbors if normalized[g]==normalized[h]]
        for reason,ordered in [('nearest',neighbors),('same_title',same)]:
            for rank,h in enumerate(ordered[:k],1):
                pair=tuple(sorted((g,h)))
                row=selected.setdefault(pair,dict(groups=list(pair),cosine=scores[pair],reasons=[],nominations=[]))
                if reason not in row['reasons']:row['reasons'].append(reason)
                row['nominations'].append(dict(group=g,reason=reason,rank=rank))
    return [selected[pair] for pair in sorted(selected)]


def consolidate(packets, original_members, decisions, recorded_no):
    """Keep a whole Yes-connected component separate if any recorded No opposes it."""
    by_id={p['packet']:p for p in packets['packets']}
    if len(by_id)!=len(packets['packets']) or set(by_id)!=set(original_members):
        raise ValueError('exact original group inventory required')
    flat=[g for members in original_members.values() for g in members]
    if any(not v for v in original_members.values()) or len(flat)!=len(set(flat)):
        raise ValueError('original group identities must be nonempty and disjoint')
    neighbors={g:set() for g in by_id};negative=deepcopy(recorded_no);seen=set()
    for (a,b),choice in decisions.items():
        pair=frozenset((a,b))
        if len(pair)!=2 or not pair<=by_id.keys() or pair in seen or choice not in {'yes','no','uncertain'}:
            raise ValueError('invalid or duplicate equivalence decision')
        seen.add(pair)
        if choice=='yes':neighbors[a].add(b);neighbors[b].add(a)
        elif choice=='no':negative.append(dict(a=a,b=b,source='current'))
    if any(r['a'] not in by_id or r['b'] not in by_id for r in negative):
        raise ValueError('recorded No references an unknown group')
    remaining=set(by_id);components=[];blocked=[]
    while remaining:
        todo=[min(remaining)];component=set()
        while todo:
            g=todo.pop()
            if g in component:continue
            component.add(g);todo.extend(neighbors[g]-component)
        remaining-=component
        conflicts=[r for r in negative if r['a'] in component and r['b'] in component]
        if conflicts:
            blocked.append(dict(members=sorted(component),conflicts=conflicts))
            components.extend([[g] for g in sorted(component)])
        else:components.append(sorted(component))
    mapping={};originals={};output=[];naming=[]
    evidence={g:p['instances'] for g,p in by_id.items()}
    for members in sorted(components):
        old=sorted(o for g in members for o in original_members[g])
        g='merged-'+_digest(old) if len(members)>1 else members[0]
        if g in originals or (len(members)>1 and g in by_id):
            raise ValueError('merged group ID collision')
        originals[g]=old;mapping.update({m:g for m in members})
        p=union_packet(g,members,evidence) if len(members)>1 else deepcopy(by_id[g])
        output.append(p)
        if len(members)>1:naming.append(p)
    return dict(source_packets=dict(packets=output),naming_source_packets=dict(packets=naming),
                member_to_group=mapping,original_members=originals,blocked_components=blocked,
                components=sorted(components),decisions=[dict(a=a,b=b,choice=v) for (a,b),v in sorted(decisions.items())],
                recorded_no=deepcopy(recorded_no))


def identity(path):
    path=Path(path).resolve()
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def check_sources(state):
    for name,expected in state['sources'].items():
        if identity(expected['path'])!=expected:raise ValueError('changed source: '+name)


def prepare(directory, vectors, coffee_experiment, output):
    """Validate the accepted saved stage, then freeze exactly one candidate pass."""
    base=Path(directory);spec,sources,tree,packets=replay(base)
    merge_run=read(base/'merged/merge-experiment.json')['path']
    bindings,missing=bind_saved(expected_merges(tree,packets),answer_catalog([*spec['merges'],merge_run],'merges'))
    if missing or bindings!=read(base/'merged/merge-bindings.json'):
        raise ValueError('saved in-branch decisions changed')
    choices={(c['evidence']['original_a_id'],c['evidence']['original_b_id']):bindings[c['id']]['value']
             for c in expected_merges(tree,packets)}
    surviving=contract_equivalence(tree,choices);surviving['instances']=tree['instances']
    if surviving!=read(base/'merged/tree.json'):raise ValueError('saved contraction differs from replay')
    selected=dict(packets=[p for p in packets['packets'] if p['packet'] in surviving['members']])
    saved_titles=read(base/'view/title-bindings.json')
    catalog=answer_catalog(sorted({b['experiment'] for b in saved_titles.values()}),'titles')
    titles,missing=bind_saved(expected_titles(selected),catalog)
    if missing or any(titles[g]['value']!=b['value'] or titles[g]['receipt']!=b['receipt'] for g,b in saved_titles.items()):
        raise ValueError('saved surviving title bindings changed')
    names={g:b['value'] for g,b in titles.items()}
    comparisons=select_pairs(selected,names,read(vectors)['inputs'])
    cases=mask_pair_cases(surviving,selected,pairs=[r['groups'] for r in comparisons])
    originals={g:sorted(old for old,r in surviving['representative'].items() if r==g)
               for g in names}
    recorded_no=[dict(a=surviving['representative'][a],b=surviving['representative'][b],
                      source='saved in-branch',original_a=a,original_b=b)
                 for (a,b),choice in choices.items() if choice=='no']
    # Retain all fifteen Coffee answers, including a No outside the shortlist.
    coffee=report(coffee_experiment)
    coffee_pairs=[(c['evidence']['original_a_id'],c['evidence']['original_b_id']) for c in coffee['cases']]
    previous=_validate_choices(mask_pair_cases(surviving,selected,pairs=coffee_pairs),coffee,MERGE_PROMPT,'same_topic')
    recorded_no.extend(dict(a=a,b=b,source='saved cross-branch') for (a,b),v in previous.items() if v=='no')
    for name,path in [('vectors',vectors),('tree',base/'merged/tree.json'),('titles',base/'view/title-bindings.json')]:
        sources['cross_'+name]=identity(path)
    state=dict(experiment_id='HR02-NMP09',sources=sources,source_directory=str(base.resolve()),
        source_packets=selected,title_bindings=titles,original_members=originals,recorded_no=recorded_no,
        tree=surviving,comparisons=comparisons,policy=dict(k=5,passes=1,
        selection='union-nearest-and-same-title-top-k-v1',consolidation='yes-components-no-veto-v1'))
    out=artifact_directory(output)
    save(out/'state.json',state);save(out/'cases.json',dict(cases=cases))
    print(json.dumps(dict(groups=len(names),pairs=len(cases),policy=state['policy'])))


def merge(directory, experiment):
    base=Path(directory);state=read(base/'state.json');check_sources(state)
    expected=mask_pair_cases(state['tree'],state['source_packets'],pairs=[r['groups'] for r in state['comparisons']])
    if read(base/'cases.json')!=dict(cases=expected):raise ValueError('saved comparison inputs changed')
    decisions=_validate_choices(expected,report(experiment),MERGE_PROMPT,'same_topic')
    result=consolidate(state['source_packets'],state['original_members'],decisions,state['recorded_no'])
    out=artifact_directory(base/'merged')
    save(out/'result.json',result);save(out/'title-packets.json',result['naming_source_packets'])
    save(out/'experiment.json',dict(path=str(Path(experiment).resolve())))
    print(json.dumps(dict(groups=len(result['source_packets']['packets']),new_titles=len(result['naming_source_packets']['packets']),
        blocked_components=len(result['blocked_components']),decisions=Counter(decisions.values()))))


def replay_merge(directory):
    base=Path(directory);state=read(base/'state.json');check_sources(state)
    expected=mask_pair_cases(state['tree'],state['source_packets'],pairs=[r['groups'] for r in state['comparisons']])
    if read(base/'cases.json')!=dict(cases=expected):raise ValueError('saved comparison inputs changed')
    decisions=_validate_choices(expected,report(read(base/'merged/experiment.json')['path']),MERGE_PROMPT,'same_topic')
    result=consolidate(state['source_packets'],state['original_members'],decisions,state['recorded_no'])
    if result!=read(base/'merged/result.json'):raise ValueError('saved cross-branch merge differs from replay')
    return state,result


def assemble_titles(state, result, title_report):
    pending=result['naming_source_packets'];generated={}
    if pending['packets']:
        if title_report is None or any(title_report.get('settings',{}).get(k)!=v for k,v in
                dict(provider='openai-codex',model='gpt-6-astra',reasoning_effort='low').items()):
            raise ValueError('new merged titles require a completed v38/Astra-low report')
        generated={g['group']:g for g in titles_from_report(pending,title_report,include_reviews=True)['groups']}
    elif title_report is not None:
        raise ValueError('no new merged titles expected')
    groups=[]
    for p in prepare_titles(result['source_packets'],TITLE.read_text(),[]):
        g=p['group']
        if g in generated:groups.append(generated[g]);continue
        old=state['title_bindings'][g]
        if p['prompt']!=old['prompt']:raise ValueError('unchanged title no longer matches its masks')
        groups.append(dict(p,title=old['value'],receipt=deepcopy(old['receipt']),reviews=deepcopy(old.get('reviews',[]))))
    return dict(prompt_version='v38',settings=dict(provider='openai-codex',model='gpt-6-astra',reasoning_effort='low'),groups=groups)


def placement(directory, title_experiment=None):
    base=Path(directory);state,result=replay_merge(base)
    titles=assemble_titles(state,result,report(title_experiment) if title_experiment else None)
    cases=make_cases(titles)
    for c in cases:
        if json.loads(render(PLACEMENT.read_text(),c['inputs']))['state']!={'A':c['inputs']['A_TITLE'],'B':c['inputs']['B_TITLE']}:
            raise ValueError('placement rendering changed a title')
    out=artifact_directory(base/'placement')
    save(out/'titles.json',titles);save(out/'cases.json',dict(cases=cases))
    save(out/'title-experiment.json',dict(path=str(Path(title_experiment).resolve()) if title_experiment else None))
    print(json.dumps(dict(groups=len(titles['groups']),directed_pairs=len(cases))))


def placement_merge(directory, experiment):
    base=Path(directory);state,result=replay_merge(base)
    title_run=read(base/'placement/title-experiment.json')['path']
    titles=assemble_titles(state,result,report(title_run) if title_run else None)
    if titles!=read(base/'placement/titles.json') or read(base/'placement/cases.json')!=dict(cases=make_cases(titles)):
        raise ValueError('saved placement inputs changed')
    plan,_,_=load(experiment)
    if plan['prompt']['id']!='NSP-Jev-v3' or plan['prompt']['text']!=PLACEMENT.read_text():
        raise ValueError('unchanged NSP-Jev-v3 required')
    decisions=report(experiment)
    merged=merge_report(titles,result['source_packets'],decisions,prompt=plan['prompt'],
                        original_members=result['original_members'])
    out=base/'placed';prepare_naming(merged,out)
    save(out/'decision-experiment.json',dict(path=str(Path(experiment).resolve())))
    print(json.dumps(dict(groups=len(merged['graph']['nodes']),new_titles=len(merged['naming_source_packets']['packets']),
                          stats=merged['graph']['stats'])))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('prepare')
    for name in ['directory','vectors','coffee_experiment','output']:s.add_argument(name,type=Path)
    s=sub.add_parser('merge');s.add_argument('directory',type=Path);s.add_argument('experiment',type=Path)
    s=sub.add_parser('placement');s.add_argument('directory',type=Path);s.add_argument('--titles',type=Path)
    s=sub.add_parser('placement-merge');s.add_argument('directory',type=Path);s.add_argument('experiment',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.directory,a.vectors,a.coffee_experiment,a.output)
    elif a.command=='merge':merge(a.directory,a.experiment)
    elif a.command=='placement':placement(a.directory,a.titles)
    else:placement_merge(a.directory,a.experiment)


if __name__=='__main__':main()
