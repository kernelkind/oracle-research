"""Offline preparation and reversible nesting projection for saved mask groups.

All inference belongs to experiment.py. Never rewrites input trees, prompts or
other experiments. Contraction needs mutual containment Yes or direct equivalence
Yes on an existing edge; those native judgment types remain separate.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from experiment import report as experiment_report, load as experiment_load
from experiment_inputs import render
from hierarchy_build import artifact_directory, read, save
from prepare_category_title_inputs import prepare as prepare_titles
from true_graph_categories import render_categories
from true_graph_notes import derive_note_memberships
from category_mask_instances import reconstruct

SSE = Path(__file__).resolve().parent
EXPERIMENT_ID = 'HR02-M06-MUSE-JEV-v1'
TITLE = SSE / 'hdbv2-node-description-probe-v38/prompt.txt'
JEV = SSE / 'node-subsumption-prompt-jev-v3/prompt.txt'


def project(history, mapping, posts):
    """Mirror load_merge_history_with_min_notes(..., 2), without changing merges."""
    vectors = {v['vector_id']: v for v in mapping['vectors']}
    texts = {p['note_id']: p['text'] for p in posts['notes']}
    aliases = history['alias_groups']
    n = history['vector_count']
    if n < 2 or len(aliases) != n or history['canonical_unique_ids'] != [a[0] for a in aliases]:
        raise ValueError('invalid canonical vectors')
    flat = [v for a in aliases for v in a]
    if len(set(flat)) != len(flat) or set(flat) != set(vectors):
        raise ValueError('aliases differ from complete vector inventory')
    instances = {}
    for v in vectors.values():
        sid = v['short_id']
        if sid in instances: raise ValueError('duplicate mask ID')
        instances[sid] = dict(instance=sid, vector_id=v['vector_id'], note_id=v['note_id'],
                              text=texts[v['note_id']], fragments=v['fragments'], byte_spans=v['byte_spans'])
    members = {i: {vectors[v]['short_id'] for v in a} for i, a in enumerate(aliases)}
    notes = {i: {vectors[v]['note_id'] for v in a} for i, a in enumerate(aliases)}
    parents, active, retained = {}, set(range(n)), {2*n-2}
    for offset, r in enumerate(history['merges']):
        g, a, b = r['id'], r['left'], r['right']
        if g != n+offset or a == b or not {a,b} <= active:
            raise ValueError('invalid merge order')
        members[g], notes[g] = members[a] | members[b], notes[a] | notes[b]
        active.difference_update([a,b]); active.add(g)
        for c in [a,b]:
            parents[c] = g
            if c >= n and len(notes[c]) >= 2 and notes[c] != notes[g]: retained.add(c)
    sizes = {i:1 for i in range(n)}
    for r in history['merges']:
        sizes[r['id']] = sizes[r['left']] + sizes[r['right']]
        if sizes[r['id']] != r['size']: raise ValueError('invalid merge size')
    root = 2*n-2
    if len(history['merges']) != n-1 or active != {root}: raise ValueError('incomplete merge tree')
    name = lambda g: f'M06-{g}'
    edges = []
    for g in sorted(retained - {root}):
        p = parents[g]
        while p not in retained: p = parents[p]
        edges.append([name(p),name(g)])
    tree = dict(root=name(root), edges=edges,
                members={name(g):sorted(members[g]) for g in sorted(retained)},
                instances=instances, source_rule='min-two-posts; equal-immediate-parent-posts-collapsed')
    packets = dict(packets=[dict(packet=name(g), instances=[instances[i] for i in sorted(members[g])])
                            for g in sorted(retained - {root})])
    prepare_titles(packets, TITLE.read_text(), [])  # Validate all exact source spans.
    return tree, packets


def pair_cases(tree, titles):
    escaped = {g:json.dumps(title,ensure_ascii=False)[1:-1] for g,title in titles.items()}
    return [dict(id=f'{a}-contains-{b}', inputs=dict(A_TITLE=escaped[a], B_TITLE=escaped[b]),
                 evidence=dict(original_a_id=a, original_b_id=b))
            for parent,child in tree['edges'] if parent != tree['root']
            for a,b in [(parent,child),(child,parent)]]


def validate_decisions(tree, titles, report, prompt):
    return _validate_choices(pair_cases(tree,titles), report, prompt, 'contains')


def mask_pair_cases(tree, packets):
    """One direct-equivalence input per non-root edge, using exact source masks."""
    groups = set(tree['members']) - {tree['root']}
    prepared = prepare_titles(packets, '{NUMBERED_INSTANCES}', sorted(groups))
    source = {p['packet']:p for p in packets['packets']}
    for g in groups:
        if set(tree['members'][g]) != {i['instance'] for i in source[g]['instances']}:
            raise ValueError('mask membership mismatch '+g)
    masks = {g['group']:json.dumps([i['fragments'] for i in g['instances']],
                                  ensure_ascii=False) for g in prepared}
    return [dict(id=f'{a}-same-topic-{b}',
                 inputs=dict(A_MASKS_JSON=masks[a], B_MASKS_JSON=masks[b]),
                 evidence=dict(original_a_id=a, original_b_id=b))
            for a,b in tree['edges'] if a != tree['root']]


def validate_equivalence_decisions(tree, packets, report, prompt):
    return _validate_choices(mask_pair_cases(tree,packets), report, prompt, 'same_topic')


def _validate_choices(expected, report, prompt, question):
    for c in expected:
        try: json.loads(render(prompt['text'],c['inputs']))
        except (ValueError, TypeError) as e: raise ValueError('input cannot render unchanged Jev JSON') from e
    if report.get('prompt_id') != prompt['id'] or any(report.get('settings',{}).get(k)!=v for k,v in
            dict(provider='openrouter',model='typesafe/jev-1.13',reasoning_effort='provider-default').items()):
        raise ValueError('Jev prompt/settings mismatch')
    cases = {c['id']:c for c in report['cases']}
    if len(cases)!=len(report['cases']) or set(cases)!={c['id'] for c in expected}:
        raise ValueError('decision inventory mismatch')
    result={}
    for e in expected:
        c=cases[e['id']];choice=c.get('parsed',{}).get(question,{}).get('choice')
        if (c['status']!='valid' or not c.get('receipt') or c['inputs']!=e['inputs'] or
            c['prompt']!=render(prompt['text'],e['inputs']) or choice not in {'yes','no','uncertain'}):
            raise ValueError('invalid or mismatched decision '+e['id'])
        result[e['evidence']['original_a_id'],e['evidence']['original_b_id']]=choice
    return result


def contract(tree, decisions):
    """Apply native directed containment judgments without changing their meaning."""
    edges = [(p,c) for p,c in tree['edges'] if p != tree['root']]
    expected = {(a,b) for p,c in edges for a,b in [(p,c),(c,p)]}
    if set(decisions) != expected: raise ValueError('exact edge decisions required')
    judgments = {}
    for p,c in edges:
        forward,reverse = decisions[p,c],decisions[c,p]
        if forward not in {'yes','no','uncertain'} or reverse not in {'yes','no','uncertain'}:
            raise ValueError('unknown decision')
        status = ('equivalent' if forward == reverse == 'yes' else
                  'uncertain' if 'uncertain' in (forward,reverse) else
                  'retained' if forward == 'yes' else 'reversed' if reverse == 'yes' else 'rejected')
        judgments[p,c] = dict(parent=p,child=c,forward=forward,reverse=reverse,status=status)
    return _contract_judged_edges(tree, judgments)


def contract_equivalence(tree, decisions):
    """Apply direct same-topic answers; never manufacture containment answers."""
    expected = {(p,c) for p,c in tree['edges'] if p != tree['root']}
    if set(decisions) != expected: raise ValueError('exact edge decisions required')
    statuses = {'yes':'equivalent', 'no':'distinct', 'uncertain':'uncertain'}
    judgments = {}
    for (p,c),choice in decisions.items():
        if choice not in statuses: raise ValueError('unknown decision')
        judgments[p,c] = dict(parent=p,child=c,same_topic=choice,status=statuses[choice])
    return _contract_judged_edges(tree, judgments)


def _contract_judged_edges(tree, edge_judgments):
    root=tree['root'];children={g:[] for g in tree['members']}
    for a,b in tree['edges']: children[a].append(b)
    representative={root:root};judgments=[];pending=[root]
    while pending:
        p=pending.pop()
        for c in children[p]:
            same=False
            if p!=root:
                judgment=edge_judgments[p,c]
                same=judgment['status']=='equivalent'
                judgments.append(deepcopy(judgment))
            representative[c]=representative[p] if same else c
            pending.append(c)
    if set(representative)!=set(tree['members']): raise ValueError('disconnected tree')
    edges=[]
    for a,b in tree['edges']:
        edge=[representative[a],representative[b]]
        if edge[0]!=edge[1] and edge not in edges: edges.append(edge)
    groups={g:[] for g in set(representative.values())}
    for g,r in representative.items(): groups[r].append(g)
    members={g:sorted({m for old in olds for m in tree['members'][old]}) for g,olds in groups.items()}
    return dict(root=root,edges=edges,members=members,representative=representative,judgments=judgments)


def normalize_title_reports(reports, accepted_plain_titles):
    """Apply only explicitly accepted format normalizations to derived copies."""
    pending=set(accepted_plain_titles)
    if len(pending)!=len(accepted_plain_titles):raise ValueError('duplicate normalization approval')
    derived=deepcopy(reports);normalizations=[]
    for report in derived:
        for case in report['cases']:
            if case['id'] not in pending or case['status']!='malformed':continue
            text=case.get('output');receipt=case.get('receipt') or {}
            if (not isinstance(text,str) or not text.strip() or len(text.splitlines())!=1
                or text.lstrip().startswith(('{','[','"','```')) or not receipt.get('record_sha256')):
                raise ValueError('not an exact plain title: '+case['id'])
            normalizations.append(dict(case_id=case['id'],receipt=deepcopy(receipt),
                original_output=text,title=text,operation='user-approved plain title to JSON object'))
            case['status']='valid';case['parsed']={'title':text}
            pending.remove(case['id'])
    if pending:raise ValueError('normalization approval has no malformed response: '+','.join(sorted(pending)))
    return derived,normalizations


def bind_title_reports(packets, reports):
    """Keep earlier valid results, filling gaps only from a complete continuation."""
    titles={}
    inventory={p['packet']:p for p in packets['packets']}
    for index,report in enumerate(reports):
        cases=[c for c in report['cases'] if c['status']=='valid']
        if index==len(reports)-1 and len(cases)!=len(report['cases']):
            raise ValueError('continuation still has incomplete titles')
        keys=[c['id'] for c in cases]
        if len(set(keys))!=len(keys) or not set(keys)<=inventory.keys() or set(keys)&titles.keys():
            raise ValueError('unknown or duplicate successful title')
        subset={'packets':[inventory[k] for k in keys]}
        titles.update(bind_titles(subset,dict(report,cases=cases)))
    if titles.keys()!=inventory.keys():raise ValueError('incomplete combined title inventory')
    return titles


def bind_titles(packets, report):
    settings=report.get('settings',{})
    profile=tuple(settings.get(k) for k in ('provider','model','reasoning_effort'))
    if report.get('prompt_id')!='v38' or report.get('adapter')!='titles' or profile not in {
        ('openrouter','meta/muse-spark-1.3-contributor','high'),
        ('openai-codex','gpt-6-luna','max'),
    }:
        raise ValueError('approved Muse-high or Luna-max v38 title report required')
    prepared=prepare_titles(packets,TITLE.read_text(),[])
    cases={c['id']:c for c in report['cases']};source={p['packet']:p for p in packets['packets']}
    if len(cases)!=len(report['cases']) or set(cases)!=set(source): raise ValueError('title inventory mismatch')
    titles={}
    for g in prepared:
        c=cases[g['group']];title=c.get('parsed',{}).get('title')
        if (c['status']!='valid' or not c.get('receipt') or c['prompt']!=g['prompt'] or
            c['evidence']['packet']!=source[g['group']] or not isinstance(title,str) or not title.strip()):
            raise ValueError('invalid title '+g['group'])
        titles[g['group']]=title
    return titles


def view(tree, titles, source, mapping, *, label, judgments=()):
    root=tree['root'];keys=set(tree['members'])-{root}
    children={g:[] for g in tree['members']}
    for a,b in tree['edges']:children[a].append(b)
    reach={}
    def descend(g):
        if g not in reach: reach[g]=sorted({c for child in children[g] for c in [child,*descend(child)]})
        return reach[g]
    descend(root)
    packets={'packets':[dict(packet=g,instances=[tree['instances'][i] for i in tree['members'][g]])
                        for g in sorted(keys)]}
    nodes=[dict(group=p['packet'],title=titles[p['packet']],
                instances=[dict(instance=i['instance'],fragments=i['fragments']) for i in p['instances']])
           for p in packets['packets']]
    graph=dict(nodes=nodes, roots=children[root],reachability={g:reach[g] for g in keys},
               transitive_reduced_edges=[dict(a_id=a,b_id=b) for a,b in tree['edges'] if a!=root])
    memberships=derive_note_memberships(graph,packets)
    result=render_categories(graph,memberships,source,mapping,hierarchy_id=label,
                             connection_description='M06 links preserved except mutually accepted equivalent steps; not a Jev-generated hierarchy.')
    result=reconstruct(result,memberships,[],Path(source).read_bytes())
    # The navigation root also owns masks outside every retained child.
    shorts={v['note_id']:v['note_short_id'] for v in read(mapping)['vectors']}
    result['notes']=sorted([dict(note_id=n,note_short_id=s) for n,s in shorts.items()],key=lambda x:x['note_short_id'])
    root_masks={}
    for sid in tree['members'][root]:
        m=tree['instances'][sid];short=shorts[m['note_id']];spans=m['byte_spans']
        entry=next((e for e in root_masks.setdefault(short,[]) if e['byte_spans']==spans),None)
        if entry:entry['ids'].append(sid)
        else:root_masks[short].append(dict(ids=[sid],byte_spans=spans))
    result['mask_instances']['root']=root_masks
    result['note_masks']['root']={s:sorted({tuple(span) for m in ms for span in m['byte_spans']}) for s,ms in root_masks.items()}
    result['nodes'][0]['note_ids']=sorted(root_masks)
    flags={}
    representative=tree.get('representative',{})
    for j in judgments:
        if j['status'] in {'rejected','reversed','uncertain'}:
            child=representative.get(j['child'],j['child'])
            flags.setdefault(child,[]).append(f"Original parent {titles[j['parent']]}: {j['status']} (forward {j['forward']}, reverse {j['reverse']}).")
    for n in result['nodes']:
        if n['node_id'] in flags:n['analysis']+=' '+' '.join(flags[n['node_id']])
    return result


def check_sources(base):
    manifest=read(base/'sources.json')
    for name,e in manifest.items():
        if hashlib.sha256(Path(e['path']).read_bytes()).hexdigest()!=e['sha256']:
            raise ValueError('source changed: '+name)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('prepare')
    for k in ['history','mapping','posts','output']:s.add_argument('--'+k,type=Path,required=True)
    for command in ['pairs','package']:
        s=sub.add_parser(command);s.add_argument('directory',type=Path);s.add_argument('--titles',type=Path,action='append',required=True)
        s.add_argument('--accept-plain-title',action='append',default=[],metavar='CASE_ID',
                       help='explicitly approved exact plain-title normalization; preserves native receipts')
        if command=='package':s.add_argument('--decisions',type=Path,required=True)
    a=p.parse_args()
    if a.command=='prepare':
        tree,packets=project(read(a.history),read(a.mapping),read(a.posts))
        out=artifact_directory(a.output)
        save(out/'tree.json',tree);save(out/'source-packets.json',packets)
        save(out/'sources.json',{k:dict(path=str(v.resolve()),sha256=hashlib.sha256(v.read_bytes()).hexdigest())
             for k,v in dict(history=a.history,mapping=a.mapping,posts=a.posts,title_prompt=TITLE,jev_prompt=JEV).items()})
        print(f'{len(packets["packets"])} title groups; {2*sum(p!=tree["root"] for p,c in tree["edges"])} judgments; no inference')
        return
    base=a.directory;sources=check_sources(base);tree=read(base/'tree.json');packets=read(base/'source-packets.json')
    replay,replay_packets=project(*(read(sources[k]['path']) for k in ['history','mapping','posts']))
    if tree!=replay or packets!=replay_packets:raise ValueError('saved projection changed')
    reports=[experiment_report(path) for path in a.titles]
    derived,normalizations=normalize_title_reports(reports,a.accept_plain_title)
    titles=bind_title_reports(packets,derived)
    label=EXPERIMENT_ID
    if any(r['settings']['model']=='gpt-6-luna' for r in reports):
        label+=' (Muse high + Luna max titles)'
    prompt=dict(id='NSP-Jev-v3',text=JEV.read_text())
    cases=pair_cases(tree,titles)
    for c in cases:
        state=json.loads(render(prompt['text'],c['inputs']))['state']
        if state!=dict(A=titles[c['evidence']['original_a_id']],B=titles[c['evidence']['original_b_id']]):raise ValueError('title JSON mismatch')
    if a.command=='pairs':
        save(base/'titles.json',titles);save(base/'title-reports.json',reports);save(base/'cases.json',dict(cases=cases))
        save(base/'title-normalizations.json',normalizations)
        save(base/'original-categories.json',view(tree,titles,sources['posts']['path'],sources['mapping']['path'],label=label+' original'))
        print(f'{len(cases)} directional cases; original titled view saved; no inference');return
    if titles!=read(base/'titles.json'):raise ValueError('titles changed')
    if normalizations!=read(base/'title-normalizations.json'):raise ValueError('title normalizations changed')
    plan,_,_=experiment_load(a.decisions)
    if plan['prompt']['id']!=prompt['id'] or plan['prompt']['text']!=prompt['text']:raise ValueError('decision prompt changed')
    decisions_report=experiment_report(a.decisions)
    decisions=validate_decisions(tree,titles,decisions_report,prompt)
    result=contract(tree,decisions);result['instances']=tree['instances']
    out=artifact_directory(base/'simplified')
    save(out/'tree.json',result);save(out/'decision-report.json',decisions_report)
    save(out/'categories.json',view(result,titles,sources['posts']['path'],sources['mapping']['path'],label=label+' equivalent steps collapsed',judgments=result['judgments']))
    print(json.dumps(dict(groups=len(result['members'])-1,judgments=Counter(j['status'] for j in result['judgments']))))


if __name__=='__main__':main()
