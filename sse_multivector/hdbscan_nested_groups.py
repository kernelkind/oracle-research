"""Offline saved-HDBSCAN group selection, exact-answer reuse and merge export.

No command performs inference. The experiment runner owns model execution,
receipts, retries, usage and reviews. Original groups and sources are immutable.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from experiment import load, report
from experiment_inputs import render
from hierarchy_build import artifact_directory, read, save, titles_from_report
from merge_tree_nesting import (TITLE, _validate_choices, check_sources,
                               contract_equivalence, mask_pair_cases, view)
from prepare_category_title_inputs import prepare as prepare_titles

SSE = Path(__file__).resolve().parent
MERGE = SSE / 'node-merge-prompt-jev-v2/prompt.txt'
MERGE_PROMPT = dict(id='NMP-Jev-v2',text=MERGE.read_text())
PROFILE = ('openai-codex','gpt-6-astra','low')


def project(result, mapping, posts):
    """Keep EOM roots and strict formation-distance steps inside each root."""
    vectors={v['vector_id']:v for v in mapping['vectors']}
    texts={p['note_id']:p['text'] for p in posts['notes']}
    aliases=result['alias_groups'];algorithm=result['algorithm_result']
    n=algorithm['vector_count'];flat=[v for a in aliases for v in a]
    if (n<2 or len(aliases)!=n or any(not a for a in aliases) or
        result['canonical_unique_ids']!=[a[0] for a in aliases] or
        len(vectors)!=len(mapping['vectors']) or len(flat)!=len(set(flat)) or
        set(flat)!=set(vectors)):
        raise ValueError('inconsistent canonical vector inventory')
    members={i:frozenset([i]) for i in range(n)}
    parents={};distances={};active=set(range(n))
    rows=algorithm['single_linkage_tree']
    for offset,r in enumerate(rows):
        g,a,b=r['id'],r['left'],r['right'];d=r['mutual_reachability_distance']
        if (g!=n+offset or a==b or not {a,b}<=active or
            not math.isfinite(d) or d<0 or
            any(d<distances.get(c,0) for c in [a,b])):
            raise ValueError('invalid raw merge or formation distance')
        members[g]=members[a]|members[b]
        if r['size']!=len(members[g]):raise ValueError('invalid raw merge size')
        parents[a]=parents[b]=g;distances[g]=d
        active.difference_update([a,b]);active.add(g)
    if len(rows)!=n-1 or active!={2*n-2}:raise ValueError('incomplete raw tree')
    by_members={m:g for g,m in members.items() if g>=n}
    roots={};covered=set()
    for c in algorithm['clusters']:
        m=frozenset(c['members'])
        if m not in by_members or len(m)!=len(c['members']) or covered&m:
            raise ValueError('EOM groups must be disjoint exact raw groups')
        roots[by_members[m]]=c['id'];covered.update(m)
    retained={}
    for root in roots:
        for g in distances:
            if members[g]<=members[root] and (g==root or distances[g]<distances[parents[g]]):
                retained[g]=root
    instances={}
    for vid,v in sorted(vectors.items()):
        sid=v['short_id']
        if sid in instances:raise ValueError('duplicate mask ID')
        instances[sid]=dict(instance=sid,vector_id=vid,note_id=v['note_id'],
                            text=texts[v['note_id']],fragments=v['fragments'],byte_spans=v['byte_spans'])
    expanded={g:sorted(v for i in members[g] for v in aliases[i]) for g in retained}
    names={g:'S'+hashlib.sha256('\n'.join(ids).encode()).hexdigest()[:10]
           for g,ids in expanded.items()}
    if len(set(names.values()))!=len(names):raise ValueError('group ID collision')
    edges=[];groups={};packets=[]
    for g in sorted(retained):
        root=retained[g];name=names[g]
        if g==root:p='root'
        else:
            ancestor=parents[g]
            while ancestor not in retained:ancestor=parents[ancestor]
            p=names[ancestor]
        edges.append([p,name])
        groups[name]=dict(raw_tree_id=g,eom_root=names[root],
                          eom_cluster_id=roots[root],formation_distance=distances[g],
                          parent_distance=distances.get(parents.get(g)))
        packets.append(dict(packet=name,instances=[instances[vectors[v]['short_id']] for v in expanded[g]]))
    packets={'packets':packets}
    # Also validate exact spans on ungrouped masks, which remain visible at root.
    prepare_titles({'packets':[dict(packet='all',instances=list(instances.values()))]},TITLE.read_text(),[])
    tree=dict(root='root',edges=edges,instances=instances,groups=groups,
              members={'root':list(instances),**{p['packet']:[i['instance'] for i in p['instances']]
                                                for p in packets['packets']}},
              source_rule='EOM roots plus strict-below-immediate-raw-parent formation distance')
    return tree,packets


def answer_catalog(paths, kind):
    """Read and validate native receipts; retain exact prompt and answer provenance."""
    catalog={}
    for path in paths:
        plan,_,_=load(path);r=report(path)
        expected=MERGE_PROMPT if kind=='merges' else dict(id='v38',text=TITLE.read_text())
        if (any(plan['prompt'][k]!=v for k,v in expected.items()) or
            tuple(r['settings'].get(k) for k in ('provider','model','reasoning_effort'))!=PROFILE):
            raise ValueError('unexpected prompt or model: '+str(path))
        if kind=='merges':
            _validate_choices(r['cases'],r,expected,'same_topic')
        else:
            packets={'packets':[c['evidence']['packet'] for c in r['cases']]}
            titles_from_report(packets,r)
        for c in r['cases']:
            value=c['parsed']['same_topic']['choice'] if kind=='merges' else c['parsed']['title']
            catalog.setdefault(c['prompt'],[]).append(dict(id=c['id'],prompt=c['prompt'],
                value=value,receipt=c['receipt'],experiment=str(Path(path).resolve()),
                reviews=c.get('reviews',[])))
    return catalog


def bind_saved(expected, catalog):
    """Exact prompt only; prefer an existing answer for the same original ID."""
    found={};missing=[]
    for e in expected:
        matches=catalog.get(e['prompt'],[])
        if matches:found[e['id']]=next((m for m in matches if m['id']==e['id']),matches[0])
        else:missing.append(e)
    return found,missing


def expected_merges(tree, packets):
    return [dict(c,prompt=render(MERGE_PROMPT['text'],c['inputs']))
            for c in mask_pair_cases(tree,packets)]


def expected_titles(packets):
    return [dict(id=g['group'],prompt=g['prompt']) for g in prepare_titles(packets,TITLE.read_text(),[])]


def missing_title_packets(tree, packets, bindings):
    """Do not generate titles for removed groups or duplicate rendered inputs."""
    survivors=set(tree['members'])-{tree['root']}
    wanted={e['id']:e for e in expected_titles(packets)};seen=set();selected=[]
    for p in packets['packets']:
        g=p['packet'];prompt=wanted[g]['prompt']
        if g in survivors and g not in bindings and prompt not in seen:
            selected.append(p);seen.add(prompt)
    return dict(packets=selected)


def source_state(manifest_path):
    manifest_path=Path(manifest_path).resolve();spec=read(manifest_path)
    resolve=lambda p:(manifest_path.parent/p).resolve()
    paths={k:resolve(v) for k,v in spec['sources'].items()}
    paths.update(manifest=manifest_path,title_prompt=TITLE,merge_prompt=MERGE)
    spec['merges']=[resolve(p) for p in spec['merges']]
    spec['titles']=[resolve(p) for p in spec['titles']]
    spec['sample_plans']=[resolve(p) for p in spec['sample_plans']]
    for i,p in enumerate(spec['sample_plans']):paths[f'sample_{i}']=p
    for sample in spec['sample_plans']:
        for path,sha in read(sample)['inputs_sha256'].items():
            p=(SSE.parent/path).resolve()
            if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('saved sample source changed: '+path)
            paths[str(p)]=p
    sources={k:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for k,p in paths.items()}
    tree,packets=project(read(paths['hdbscan'])['artifact']['result'],read(paths['mapping']),read(paths['posts']))
    for path in spec['sample_plans']:
        for g in read(path)['groups']:
            if tree['members'].get(g['group'])!=g['mask_ids']:
                raise ValueError('saved sample membership/order mismatch: '+g['group'])
    original=read(paths['original_packets'])
    packet_by_id={p['packet']:p for p in packets['packets']}
    if any(packet_by_id.get(p['packet'])!=p for p in original['packets']):
        raise ValueError('original EOM packets changed')
    if {b for a,b in tree['edges'] if a=='root'}!={p['packet'] for p in original['packets']}:
        raise ValueError('original EOM root inventory changed')
    return spec,sources,tree,packets


def prepare(manifest, output):
    spec,sources,tree,packets=source_state(manifest)
    saved,missing=bind_saved(expected_merges(tree,packets),answer_catalog(spec['merges'],'merges'))
    titles,_=bind_saved(expected_titles(packets),answer_catalog(spec['titles'],'titles'))
    out=artifact_directory(output)
    for name,value in [('tree',tree),('source-packets',packets),('sources',sources),
                       ('saved-merges',saved),('saved-titles',titles),
                       ('cases',dict(cases=[{k:v for k,v in c.items() if k!='prompt'} for c in missing]))]:
        save(out/(name+'.json'),value)
    counts=dict(groups=len(packets['packets']),eom_roots=sum(a=='root' for a,b in tree['edges']),
                adjacent_pairs=len(saved)+len(missing),saved_merge_answers=len(saved),new_merge_cases=len(missing),
                saved_titles=len(titles),untitled_groups=len(packets['packets'])-len(titles))
    save(out/'counts.json',counts)
    print(json.dumps(counts))


def replay(directory):
    base=Path(directory);sources=check_sources(base)
    spec,current,tree,packets=source_state(sources['manifest']['path'])
    if sources!=current or tree!=read(base/'tree.json') or packets!=read(base/'source-packets.json'):
        raise ValueError('saved preparation differs from source replay')
    return spec,sources,tree,packets


def merge(directory, experiment):
    base=Path(directory);spec,sources,tree,packets=replay(base)
    expected=expected_merges(tree,packets)
    saved,_=bind_saved(expected,answer_catalog(spec['merges'],'merges'))
    if saved!=read(base/'saved-merges.json'):raise ValueError('saved merge bindings changed')
    bindings,missing=bind_saved(expected,answer_catalog([*spec['merges'],experiment],'merges'))
    if missing:raise ValueError(f'{len(missing)} unresolved merge inputs; no contraction exported')
    choices={(c['evidence']['original_a_id'],c['evidence']['original_b_id']):bindings[c['id']]['value'] for c in expected}
    result=contract_equivalence(tree,choices);result['instances']=tree['instances']
    titles,_=bind_saved(expected_titles(packets),answer_catalog(spec['titles'],'titles'))
    if titles!=read(base/'saved-titles.json'):raise ValueError('saved title bindings changed')
    needed=missing_title_packets(result,packets,titles)
    out=artifact_directory(base/'merged')
    save(out/'tree.json',result);save(out/'merge-bindings.json',bindings)
    save(out/'title-packets.json',needed)
    save(out/'merge-experiment.json',dict(path=str(Path(experiment).resolve())))
    counts=dict(original_groups=len(packets['packets']),surviving_groups=len(result['members'])-1,
                decisions=Counter(choices.values()),new_title_cases=len(needed['packets']))
    save(out/'counts.json',counts);print(json.dumps(counts))


def package(directory, title_experiment):
    base=Path(directory);spec,sources,tree,packets=replay(base)
    merged=base/'merged';merge_run=read(merged/'merge-experiment.json')['path']
    bindings,missing=bind_saved(expected_merges(tree,packets),answer_catalog([*spec['merges'],merge_run],'merges'))
    if missing or bindings!=read(merged/'merge-bindings.json'):raise ValueError('merge bindings changed')
    choices={(c['evidence']['original_a_id'],c['evidence']['original_b_id']):bindings[c['id']]['value']
             for c in expected_merges(tree,packets)}
    result=contract_equivalence(tree,choices);result['instances']=tree['instances']
    if result!=read(merged/'tree.json'):raise ValueError('contraction replay differs')
    survivors={'packets':[p for p in packets['packets'] if p['packet'] in result['members']]}
    paths=[*spec['titles'],*title_experiment]
    title_bindings,missing=bind_saved(expected_titles(survivors),answer_catalog(paths,'titles'))
    if missing:raise ValueError(f'{len(missing)} surviving groups lack valid titles')
    titles={g:b['value'] for g,b in title_bindings.items()}
    label=spec['experiment_id']+' · saved HDBSCAN nesting, Astra-low merges'
    categories=view(result,titles,sources['posts']['path'],sources['mapping']['path'],label=label,
        connection_description='Saved HDBSCAN nesting; only same-topic Yes steps collapsed. Parent placement is not semantically validated.')
    grouped=set().union(*(set(tree['members'][b]) for a,b in tree['edges'] if a=='root'))
    notice=(f'{len(packets["packets"])} original groups; {len(titles)} after Astra-low same-topic merges. '
            f'{len(grouped)} source masks are in groups; {len(tree["instances"])-len(grouped)} are outside every group. '
            'Original groups, answers and mappings remain saved. No new parent placement or membership expansion.')
    originals={g:[] for g in titles}
    for old,g in result['representative'].items():
        if g in originals:originals[g].append(old)
    for node in categories['nodes']:
        g=node['node_id']
        if g in originals:
            node['analysis']+='\nOriginal groups represented here: '+', '.join(sorted(originals[g]))+'.'
            uncertain=[j for j in result['judgments'] if j['same_topic']=='uncertain' and
                       result['representative'][j['child']]==g]
            if uncertain:node['analysis']+='\nAstra answered Uncertain on equivalence with the original parent; both groups remain.'
        else:node['analysis']+='\n'+notice
    out=artifact_directory(base/'view')
    save(out/'categories.json',categories);save(out/'title-bindings.json',title_bindings)
    save(out/'verification.json',dict(experiment_id=spec['experiment_id'],sources=sources,
        original_groups=len(packets['packets']),surviving_groups=len(titles),
        grouped_masks=len(grouped),ungrouped_masks=len(tree['instances'])-len(grouped),
        decisions=Counter(choices.values()),representative=result['representative']))
    check_sources(base)
    print(notice)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('prepare');s.add_argument('manifest',type=Path);s.add_argument('output',type=Path)
    s=sub.add_parser('merge');s.add_argument('directory',type=Path);s.add_argument('--experiment',type=Path,required=True)
    s=sub.add_parser('package');s.add_argument('directory',type=Path);s.add_argument('--titles',type=Path,action='append',default=[])
    a=p.parse_args()
    if a.command=='prepare':prepare(a.manifest,a.output)
    elif a.command=='merge':merge(a.directory,a.experiment)
    else:package(a.directory,a.titles)


if __name__=='__main__':main()
