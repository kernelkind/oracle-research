"""Reproduce this completed experiment's historical input/job records, not new calls.

Printed job commands are archival Codex-format evidence. For new executions use
run-model.sh or extraction_pipeline.py with explicit runtime configuration.
"""
from pathlib import Path
import json, hashlib, re, importlib.util, sys
R=Path("/home/dev/src/notedeck_worktrees/algos/oracle-mvp"); G=R/"sse_multivector/subject-prompt-goal-v1"; V=G/"asv6.23-validation-v1"
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda s:" ".join(s.split())
sel=json.loads((G/"selection.json").read_text()); raw=(G/"final-input.json").read_text(); old=json.loads(raw)["notes"]
source=json.loads((R/sel["source"]).read_text())["notes"]
assert sha((R/sel["source"]).read_bytes())==sel["source_sha256"]
assert len(old)==60
hits=[(i+1,json.loads(line.strip().removesuffix(",").split(":",1)[1])) for i,line in enumerate(raw.splitlines()) if re.match(r'\s*"note_id":',line)]
last=[x for x in hits if x[0]<=190][-1]; exposed=last[1]
assert exposed in {n["note_id"] for n in old}
exp=next(n for n in old if n["note_id"]==exposed)
excluded=set(sel["excluded_note_ids"])
texts={norm(n["text"]) for n in source if n["note_id"] in excluded}
inventory=[]
def walk(o):
 if isinstance(o,dict):
  if isinstance(o.get("text"),str): texts.add(norm(o["text"]))
  for v in o.values(): walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
for item in sel["exclusion_files"]:
 p=R/item["path"]; assert sha(p.read_bytes())==item["sha256"],str(p); walk(json.loads(p.read_text()));inventory.append(item)
band=lambda n:0 if len(n["text"])<=160 else 1 if len(n["text"])<=600 else 2
key=lambda n:sha(("subject-prompt-goal-v1/final/"+n["note_id"]).encode())
eligible=[n for n in source if n["note_id"] not in excluded and norm(n["text"]) not in texts]
assert len(eligible)==sel["eligible_notes"],(len(eligible),sel["eligible_notes"])
counts=[sum(band(n)==b for n in eligible) for b in range(3)]
assert counts==sel["eligible_counts_by_length_band"]
def pick(ns,k):
 result=[]
 for b in range(3): result.extend(sorted([n for n in ns if band(n)==b],key=key)[:k])
 seen={n["note_id"] for n in result}
 if len(result)<3*k:result.extend(sorted([n for n in ns if n["note_id"] not in seen],key=key)[:3*k-len(result)])
 return result
baseline=pick(eligible,20)
assert {n["note_id"] for n in baseline}=={n["note_id"] for n in old}
eligible2=[n for n in eligible if n["note_id"]!=exposed and norm(n["text"])!=norm(exp["text"])]
chosen=pick(eligible2,20)
oldids={n["note_id"] for n in old}; newids={n["note_id"] for n in chosen}
assert oldids-newids=={exposed}
assert len(newids-oldids)==1
replacement=next(n for n in chosen if n["note_id"] not in oldids)
assert band(replacement)==band(exp)
# Retain previous labels and source order; only the exposed slot changes.
repaired=[replacement if n["note_id"]==exposed else n for n in old]
repeats=pick(repaired,4);repeatids={n["note_id"] for n in repeats}
assert len(repeatids)==12
original_repeat=json.loads((G/"final-repeat-input.json").read_text())["notes"]
assert {n["note_id"] for n in original_repeat}=={n["note_id"] for n in pick(old,4)}
sys.path.insert(0,str(R))
from sse_multivector import generation_history as m
template=json.loads((V/"repeat/D03-t2/config.json").read_text())
prompt=(G/"asv6.23/ASv6.23.md").read_text().rstrip("\n")
schema=json.loads((G/"asv6.23/output-schema.json").read_text())
files={"input.json":{"schema_version":1,"notes":repaired},"repeat-input.json":{"schema_version":1,"notes":repeats}}
jobs=[]; entries=[]
for i,n in enumerate(repaired,1):
 label=f"H{i:02d}"; entries.append({"label":label,"note_id":n["note_id"],"source_row":source.index(n)+1,"chars":len(n["text"]),"band":band(n),"text_sha256":sha(n["text"].encode()),"repeat":n["note_id"] in repeatids})
for t in [1,2,3]:
 for entry,n in zip(entries,repaired):
  if t>1 and not entry["repeat"]:continue
  job=f"{entry['label']}-t{t}"; cfg=dict(template);cfg["prompts"]=[{"prompt_id":job,"text":m._render_subject_prompt(prompt,m.Note(note_id=n["note_id"],text=n["text"]))}]
  files[f"{job}/config.json"]=cfg
  jobs.append({"id":job,"unit":"as23final-"+job.lower(),"cwd":str(R),"command":["/etc/profiles/per-user/dev/bin/python3",str(R/"sse_multivector/codex_exec.py"),"prompt",str(V/"final"/job/"config.json")]})
assert len(jobs)==84
for b in range(7):files[f"batch-{b+1:02d}.json"]={"jobs":jobs[b*12:(b+1)*12]}
files["selection.json"]={"schema_version":1,"prior_selection":"../../selection.json","prior_selection_sha256":sha((G/"selection.json").read_bytes()),"source":sel["source"],"source_sha256":sel["source_sha256"],"normalization":"collapse whitespace using str.split for exclusion only; source text unchanged","excluded_note_ids":sorted(excluded|{exposed}),"prior_exclusion_files_verified":inventory,"original_final_input_sha256":sha((G/"final-input.json").read_bytes()),"original_repeat_input_sha256":sha((G/"final-repeat-input.json").read_bytes()),"repair":{"reported_location":"../../final-input.json:190","containing_note_id_line":last[0],"exposed_note_id":exposed,"replacement_note_id":replacement["note_id"],"band":band(exp),"other_59_unchanged":True,"selection_reproduced_before_repair":True,"repeat_set_recomputed":True},"entries":entries,"counts_by_length_band":[sum(band(n)==b for n in repaired) for b in range(3)],"repeat_note_ids":[n["note_id"] for n in repeats],"final_generation_calls":84,"final_prompt_frozen_before_selection":sha((G/"asv6.23/ASv6.23.md").read_bytes())}
print(json.dumps(files,ensure_ascii=False))
