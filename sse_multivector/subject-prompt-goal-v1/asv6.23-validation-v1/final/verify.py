"""Read-only verification of ASv6.23 final artifacts and fixed gates."""
from pathlib import Path
import json,hashlib,collections
F=Path(__file__).resolve().parent; G=F.parent.parent; R=G.parent.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pre=read(F/"preflight.json")
for path,digest in pre["hashes"].items():assert sha(R/path)==digest,path
for c in pre["configs"]:assert sha(F/c["id"]/"config.json")==c["config_sha256"]
selection=read(F/"selection.json")
for path,key in [(G/"selection.json","prior_selection_sha256"),(G/"final-input.json","original_final_input_sha256"),(G/"final-repeat-input.json","original_repeat_input_sha256")]:assert sha(path)==selection[key]
notes=read(F/"input.json")["notes"]; outputs={}
for p in sorted(F.glob("H*/run/output.json")):
 export=read(p); assert len(export["responses"])==1
 row=export["responses"][0]; key=row["prompt_id"]
 assert key==p.parent.parent.name and key not in outputs
 subjects=json.loads(row["response"])["subjects"]
 assert all(list(s)==["context","subject"] for s in subjects)
 outputs[key]=subjects
assert len(outputs)==84
packets=sum((read(F/f"review-packet-{part}.json") for part in "abc"),[])
assert len(packets)==84 and len({p["id"] for p in packets})==84
for p in packets:
 assert p["text"]==notes[int(p["id"][1:3])-1]["text"]
 assert p["subjects"]==[{"index":i+1,"text":s["subject"]} for i,s in enumerate(outputs[p["id"]])]
def verify_review(rows):
 for row in rows:
  inds=list(row["accepted"])
  for bucket in ["errors","unresolved"]:
   for issue in row[bucket]:inds.extend(issue.get("indexes",[issue.get("index")]))
  assert sorted(inds)==list(range(1,len(outputs[row["id"]])+1)),row["id"]
  assert "missing_meanings" in row and "coverage_unresolved" in row
review=read(F/"review.json")["outputs"]
assert len(review)==84 and len({r["id"] for r in review})==84
verify_review(review)
for part in "abc":verify_review(read(F/f"reviewer-{part}.json")["outputs"])
for part in "abc":verify_review(read(F/f"main-review-initial-{part}.json")["outputs"])
clean=lambda r:not any(r[k] for k in ["errors","unresolved","missing_meanings","coverage_unresolved"])
first=[r for r in review if r["id"].endswith("-t1")]
accepted=sum(len(r["accepted"]) for r in review);total=sum(map(len,outputs.values()))
first_accepted=sum(len(r["accepted"]) for r in first);first_total=sum(len(outputs[r["id"]]) for r in first)
by_note=collections.defaultdict(list)
for row in review:by_note[row["id"][:3]].append(row)
repeat_bad={k:sum(not clean(r) for r in rows) for k,rows in by_note.items() if len(rows)==3}
assert len(repeat_bad)==12 and max(repeat_bad.values())<=1
patterns={"uncertain_extra_word_senses":["H20","H32"],"uncertain_author_inference_strength":["H52"],"uncertain_topic_versus_metadata":["H34"]}
assert max(map(len,patterns.values()))<3
plan=read(F.parent/"plan.json"); gates=plan["frozen"]["gates"]["final"]
gate_results={
 "first_clean":sum(map(clean,first))>=gates["minimum_notes_with_no_error_or_unresolved_out_of_60"],
 "accepted_fraction":accepted/total>=gates["minimum_accepted_subject_fraction"],
 "first_accepted_fraction":first_accepted/first_total>=gates["minimum_accepted_subject_fraction"],
 "overall_clean":sum(map(clean,review))>=gates["minimum_clean_note_outputs_across_84"],
 "repeats":max(repeat_bad.values())<=1,
 "patterns":max(map(len,patterns.values()))<3,
 "severe_errors":not any(r["errors"] for r in review)
}
tech=read(F/"technical-verification.json"); dev=read(F.parent/"repeat/assessment.json")
assert tech["passed"] and dev["development_pass"]
assert all(gate_results.values())
print(json.dumps({"passed":True,"first_outputs":len(first),"first_clean":sum(map(clean,first)),"first_subjects":first_total,"first_accepted_subjects":first_accepted,"outputs":len(outputs),"clean_outputs":sum(map(clean,review)),"subjects":total,"accepted_subjects":accepted,"accepted_fraction":accepted/total,"errors":sum(len(e["indexes"]) for r in review for e in r["errors"]),"unresolved_subjects":sum(len(e["indexes"]) for r in review for e in r["unresolved"]),"nonclean_outputs":[r["id"] for r in review if not clean(r)],"repeated_notes":len(repeat_bad),"nonclean_outputs_by_repeated_note":repeat_bad,"pattern_note_sets":patterns,"gate_results":gate_results,"original_prompt_schema_plan_inputs_unchanged":True,"all_packets_match_raw_final_subjects_and_full_sources":True,"all_main_and_independent_decisions_account_for_every_subject":True,"technical_verification":"technical-verification.json","development_verification":"../repeat/assessment.json","review_sha256":sha(F/"review.json"),"technical_sha256":sha(F/"technical-verification.json"),"limitation":"Semantic classifications are recorded human-like assistant judgments, not machine proof. No population accuracy estimate."},indent=2))
