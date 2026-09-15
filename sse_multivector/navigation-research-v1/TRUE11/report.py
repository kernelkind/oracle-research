"""Render the native graph and the changed decisions, keeping source masks visible."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'TRUE10'


def read(path):
    return json.loads(path.read_text())


def main():
    graph=read(HERE/'native-graph.json')
    notes=read(HERE/'native-notes.json')['nodes']
    by={n['group']:n for n in notes}
    title=lambda key: by[key]['title']+' ('+key+')'
    reduced=graph['transitive_reduced_edges']
    if reduced is None:
        raise ValueError('native graph is not acyclic')
    lines=['# TRUE11 — Native-answer hierarchy', '',
        'Every connection below comes from a saved native Yes. No semantic corrections were made. Twelve redundant connections were removed without changing any paths or available notes. Multiple parents remain.', '',
        'This graph is acyclic, not semantically certified. Masks below belong directly to each category; available-note counts also include its children recursively. Full original notes and exact masks are preserved in [native-notes.json](./native-notes.json).', '',
        '## Starting categories', '']
    lines += ['- '+title(key) for key in graph['roots']]
    for node in notes:
        key=node['group']
        parents=[e['a_id'] for e in reduced if e['b_id']==key]
        children=[e['b_id'] for e in reduced if e['a_id']==key]
        lines += ['', '## '+title(key), '',
            f'Notes directly represented: {node["own_note_count"]}. Including descendants: {node["recursive_note_count"]}.', '',
            'Parents: '+('; '.join(map(title,parents)) or 'none')+'.', '', 'Children:', '']
        lines += ['- '+title(c) for c in children] or ['- None.']
        lines += ['', 'Source masks:', '']
        for mask in node['matched_instances']:
            lines.append('- '+mask['instance']+': '+' '.join('⟦'+f.replace('\n','<br>')+'⟧' for f in mask['fragments']))
    (HERE/'GRAPH.md').write_text('\n'.join(lines)+'\n')

    initial=read(BASE/'derived/semantic-comparison.json')
    aliases={n['group']:n['group'] for n in notes}
    for approval in read(BASE/'analysis-plan.json')['main_equivalence_judgments']:
        aliases.update({key:approval['canonical'] for key in approval['members']})
    judgments={}
    for row in initial:
        judgments.setdefault((aliases[row['a_id']],aliases[row['b_id']]),[]).append(
            ('Initial assistant review', row['independent_judgment'],row['reason']))
    for row in read(BASE/'additional-semantic-review.json')['directions']:
        judgments.setdefault((aliases[row['a_id']],aliases[row['b_id']]),[]).append(
            ('Additional post-score assistant review',row['judgment'],row['reason']))
    comparisons={(r['a_id'],r['b_id']):r for r in read(HERE/'semantic-comparison.json')}
    lines=['# TRUE11 — All 40 changed decisions', '',
        'Every direction here is cutoff Yes / native No. Earlier assistant judgments are reproduced for context, not adopted as user-approved truth. The fresh semantic assessment and its cautions are in [RESULTS.md](./RESULTS.md).', '',
        'For each A and B, TRUE saw only `premise: This text is about {B}. hypothesis: This text is about {A}.` The masks below are inspection evidence; TRUE did not see them.', '']
    for row in read(HERE/'changed-decisions.json'):
        a,b=row['a_id'],row['b_id']
        lines += ['## '+row['a']+' → '+row['b'], '',
            f'A: {a}. B: {b}. Score: {row["entailment_score"]}. Native: No. Cutoff: Yes.', '']
        seen=set()
        for source,expected,reason in judgments.get((a,b),[]):
            if (source,expected,reason) in seen: continue
            seen.add((source,expected,reason))
            label='Uncertain' if expected is None else 'Yes' if expected else 'No'
            lines += [f'{source}: {label}. {reason}', '']
        compare=comparisons.get((a,b))
        if compare:
            for rule in ['cutoff','native']:
                item=compare[rule]
                path=' → '.join(map(title,item['path'])) if item['path'] else 'No route.'
                lines += [rule.capitalize()+' route: '+path,
                    f'Child’s own notes available under A: {len(item["available_child_note_ids"])}/{item["child_own_notes"]}.', '']
        for key,label in [(a,'A'),(b,'B')]:
            lines += [label+' masks:', '']
            for mask in by[key]['matched_instances']:
                lines.append('- '+mask['instance']+': '+' '.join('⟦'+f.replace('\n','<br>')+'⟧' for f in mask['fragments']))
            lines.append('')
    (HERE/'CHANGED-DECISIONS.md').write_text('\n'.join(lines).rstrip()+'\n')


if __name__=='__main__':
    main()
