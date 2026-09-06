from pathlib import Path
import hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from sse_multivector import codex_exec as r
p=root/'sse_multivector/subject-prompt-goal-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()
plan=json.loads((p/'plan.json').read_text())
assert sha((p/'plan.json').read_bytes())=='64c5e1a8b2897573f4e7f861173fc13a6a9734bda2a40d6d4fb42023d4a1f3fa'
for name in ['plan.json','selection.json','development-input.json','development-repeat-input.json','final-input.json','final-repeat-input.json']:
 committed=subprocess.check_output(['git','show','ace3fa2667494f314bcc280f54aaf4c34e242fdc:sse_multivector/subject-prompt-goal-v1/'+name],cwd=root)
 assert (p/name).read_bytes()==committed,name
registry=root/'sse_multivector/atomic-subject-prompt-versions.json'
assert sha(registry.read_bytes())=='357772ff8c7f673982af976bf43d13a6c4ec5031f6b06ec2361046b9c8e4b95f'
assert json.loads(registry.read_text())['frozen_atomic_subject_prompt_version']=='ASv6.8'
assert sha((root/plan['unchanged']['runner']).read_bytes())==plan['unchanged']['runner_sha256']
baseline=json.loads((root/'sse_multivector/atomic-subject-asv6.11-test-v1/run/manifest.json').read_text())
threads=set(); workdirs=set(); totals={}; run_reports=[]
prior_paths=list((root/'sse_multivector').glob('atomic-subject-*/**/results.jsonl'))
prior_rows=[json.loads(l) for q in prior_paths for l in q.read_text().splitlines()]
prior_threads={x['thread_id'] for x in prior_rows if x.get('thread_id')}
prior_dirs={x['argv'][x['argv'].index('--cd')+1] for x in prior_rows if x.get('argv') and '--cd' in x['argv']}
for v,run,config_name in [('asv6.12','run','config.json'),('asv6.12','diagnostic-2','diagnostic-2-config.json'),('asv6.12','diagnostic-3','diagnostic-3-config.json'),('asv6.13','run','config.json')]:
 d=p/v/run; c=r.SubjectRunnerConfig.load(p/v/config_name); notes=r._load_notes(c.input_path)
 m=json.loads((d/'manifest.json').read_text()); mh=sha((d/'manifest.json').read_bytes()); out=json.loads((d/'output.json').read_text()); rows=[json.loads(l) for l in (d/'results.jsonl').read_text().splitlines()]
 assert len(notes)==len(rows)==len(out['notes'])
 assert out['manifest_sha256']==mh
 assert c.subject.prompt==(p/v/(v.upper().replace('ASV','ASv')+'.md')).read_text().removesuffix('\n')
 assert m['subject']['prompt']==c.subject.prompt
 assert sha(c.input_path.read_bytes())==m['input_sha256']
 for key in ['wrapper_sha256','isolation','codex_binary','codex_version','subject_envelope_version','subject_input_normalization_version']: assert m[key]==baseline[key],key
 for key in ['model','reasoning_effort','response_schema','response_schema_sha256']: assert m['subject'][key]==baseline['subject'][key],key
 assert sha((d/'model-instructions.md').read_bytes())==m['isolation']['model_instructions_sha256']
 assert json.loads((d/'subject-output-schema.json').read_text())==m['subject']['response_schema']
 for n,x,pub in zip(notes,rows,out['notes']):
  assert n.note_id==x['note_id']==pub['note_id'] and n.text==pub['text']
  assert x['status']=='succeeded' and x['exit_code']==0 and x['attempt']==1
  assert x['manifest_sha256']==mh and x['wrapper_sha256']==m['wrapper_sha256']
  assert x['model']=='gpt-5.6-sol' and x['reasoning_effort']=='low'
  assert x['prompt_sha256']==sha(r._render_subject_prompt(c.subject.prompt,n).encode())
  for value,key in [('final_output_raw','final_output_sha256'),('stdout_jsonl','stdout_sha256'),('stderr','stderr_sha256')]: assert sha(x[value].encode())==x[key]
  assert json.loads(x['final_output_raw'])['subjects']==x['response']==[s['text'] for s in pub['subjects']]
  assert [s['source_index'] for s in pub['subjects']]==list(range(len(x['response'])))
  ev=[json.loads(l) for l in x['stdout_jsonl'].splitlines()]
  assert sum(e['type']=='turn.started' for e in ev)==1 and sum(e['type']=='turn.completed' for e in ev)==1
  assert all(e['item']['type']=='agent_message' for e in ev if 'item' in e)
  assert [e['thread_id'] for e in ev if e['type']=='thread.started']==[x['thread_id']]
  argv=x['argv']; assert all(flag in argv for flag in ['--ephemeral','--ignore-rules','--ignore-user-config','--strict-config']) and 'resume' not in argv
  cd=argv[argv.index('--cd')+1]
  assert cd not in workdirs and cd not in prior_dirs
  assert x['thread_id'] not in threads and x['thread_id'] not in prior_threads
  threads.add(x['thread_id']);workdirs.add(cd)
  for k,num in x['usage'].items():totals[k]=totals.get(k,0)+num
 if run=='run':
  review=json.loads((p/v/'review.json').read_text())
 else:
  review=next(a for a in json.loads((p/v/'diagnostic-review.json').read_text())['reviews'] if a['run']==run)
 assert len(review['notes'])==len(notes)
 for pub,rev in zip(out['notes'],review['notes']):
  assert pub['note_id']==rev['note_id']
  assert rev['coverage'] in ['accepted','error','unresolved'] and rev['coverage_reason']
  assert [{k:s[k] for k in ['source_index','text']} for s in rev['subjects']]==pub['subjects']
  assert all(s['status'] in ['accepted','error','unresolved'] for s in rev['subjects'])
  assert all(s.get('reason') and s.get('evidence') for s in rev['subjects'] if s['status']!='accepted')
 run_reports.append({'version':v,'run':run,'calls':len(rows),'subjects':sum(len(x['response']) for x in rows),'clean_note_outputs_as_recorded':sum(n['coverage']=='accepted' and all(s['status']=='accepted' for s in n['subjects']) for n in review['notes']),'manifest_sha256':mh})
print(json.dumps({'schema_version':1,'runs':run_reports,'new_calls':len(threads),'unique_threads':len(threads),'unique_workdirs':len(workdirs),'prior_calls_checked_for_reuse':len(prior_rows),'shared_threads_or_workdirs':0,'one_turn_each':True,'no_tool_events':True,'raw_hashes_and_exports_verified':True,'every_output_has_semantic_review':True,'plan_and_inputs_unchanged':True,'canonical_registry_unchanged':True,'usage':totals,'review_correction':'review-corrections.json changes ASv6.12 D14 to an error; historical review preserved.','pending':'ASv6.13 diagnostic calls not launched: host I/O admission guard.'},indent=2))
