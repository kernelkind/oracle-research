import json,sys
from pathlib import Path
sys.path.insert(0,'sse_multivector')
from true_mask_membership import derive_note_memberships
p=Path('sse_multivector/navigation-research-v1/TRUE12')
scores=[json.loads(l) for l in (p/'scores.jsonl').read_text().splitlines()]
base=json.loads((p/'baseline.json').read_text())
native=json.loads((p/'memberships.json').read_text())
details=json.loads((p/'comparison-details.json').read_text())['masks']
cut=derive_note_memberships(scores,base,threshold=0.142)
out={'experiment':'TRUE12','diagnostic':'Historical strict score > 0.142 compared after observing native misses; no new inference, no fitted cutoff, not a validated membership threshold.','categories':[]}
def counts(rows):
 return {label:{'total':sum(r['expected']==label for r in rows),'yes':sum(r['expected']==label and r['predicted'] is True for r in rows),'no':sum(r['expected']==label and r['predicted'] is False for r in rows),'unresolved':sum(r['expected']==label and r['predicted'] is None for r in rows)} for label in ['positive','negative','uncertain']}
for n,c in zip(native['nodes'],cut['nodes']):
 assert n['group']==c['group']
 known={r['note_id']:r for r in n['notes']}
 ms=[r for r in details if r['category_id']==n['group']]
 entry={'title':n['title'],'group':n['group'],'baseline_note_ids':[known[i]['note_short_id'] for i in n['baseline_recursive_note_ids']],'rules':{}}
 for rule,node in [('native',n),('historical_cutoff',c)]:
  ns=[dict(r,expected=known[r['note_id']]['expected'],note_short_id=known[r['note_id']]['note_short_id']) for r in node['notes']]
  mr=[dict(r,predicted=r['predicted'] if rule=='native' else r['entailment_score']>0.142) for r in ms]
  accepted={r['note_id'] for r in ns if r['predicted'] is True}
  old=set(n['baseline_recursive_note_ids'])
  new=accepted-old
  expected={r['note_id'] for r in ns if r['expected']=='positive'}-old
  def short(ids): return sorted(known[i]['note_short_id'] for i in ids)
  entry['rules'][rule]={'note_counts':counts(ns),'mask_counts':counts(mr),'accepted_note_ids':short(accepted),'new_positive_notes':short(i for i in new if known[i]['expected']=='positive'),'new_negative_notes':short(i for i in new if known[i]['expected']=='negative'),'new_uncertain_notes':short(i for i in new if known[i]['expected']=='uncertain'),'missed_expected_additions':short(expected-accepted),'baseline_notes_rejected_by_rule':short(old-accepted),'notes_if_only_adding_to_baseline':short(old|accepted),'accepted_mask_ids':[r['mask_id'] for r in mr if r['predicted'] is True],'clear_positive_masks_missed':[r['mask_id'] for r in mr if r['expected']=='positive' and r['predicted'] is not True],'clear_negative_masks_accepted':[r['mask_id'] for r in mr if r['expected']=='negative' and r['predicted'] is True],'uncertain_masks_accepted':[r['mask_id'] for r in mr if r['expected']=='uncertain' and r['predicted'] is True]}
 pos=sorted((r for r in ms if r['expected']=='positive'),key=lambda r:r['entailment_score'])
 neg=sorted((r for r in ms if r['expected']=='negative'),key=lambda r:r['entailment_score'],reverse=True)
 def brief(r): return {k:r[k] for k in ['mask_id','note_short_id','fragments','entailment_score','expected','model_input']}
 entry['score_ordering']={'lowest_positive':brief(pos[0]),'highest_negative':brief(neg[0]),'perfect_threshold_can_separate_all_clear_masks':pos[0]['entailment_score']>neg[0]['entailment_score']}
 out['categories'].append(entry)
print(json.dumps(out,ensure_ascii=False,indent=2))
