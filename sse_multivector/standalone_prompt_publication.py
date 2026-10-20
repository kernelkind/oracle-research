"""Saved early TP/MP trials using the common historical publication writer.

The mask-study helpers retain their existing contract. This profile adds the
older fixed-``takeaway`` input and saved receipt-only partial trials, without
turning preparation or missing results into additional trials.
"""
import json
from pathlib import Path
import re

from . import mask_goal_publication as saved


def _factor(prompt, task):
    template, variables, _ = saved._factor(prompt)
    if task == 'mask' and '<takeaway>\n' in template:
        opening, closing = '<takeaway>\n', '\n</takeaway>'
        start = template.rfind(opening)+len(opening)
        end = template.find(closing,start)
        saved._require(end >= start,'unclosed supplied takeaway block')
        variables['takeaway'] = template[start:end]
        template = template[:start]+'{{takeaway}}'+template[end:]
    saved._require(task in ('mask','takeaway'),'unsupported early prompt task')
    saved._require('post' in variables,'missing supplied post')
    if task == 'mask':
        saved._require(('takeaway' in variables) != ('subject' in variables),
                       'mask input requires one fixed subject or takeaway')
    else:
        saved._require('subject' not in variables and 'takeaway' not in variables,
                       'takeaway generation has an unexpected fixed meaning')
    restored = template
    for name,value in variables.items():
        restored = restored.replace('{{'+name+'}}',value)
    saved._require(restored == prompt,'early prompt reconstruction differs')
    return template,variables,'mask_answer' if task=='mask' else 'takeaway_answer'


def _manifest(sources, declaration):
    binding = declaration['manifest']
    manifest = sources.read(binding['path'])
    saved._require(isinstance(manifest,dict) and manifest.get('schema_version')==1,
                   'unsupported early manifest')
    config = declaration.get('configuration')
    if config:
        configuration = sources.read(config['path'])
        saved._require(manifest.get('config_sha256')==config['sha256'],
                       'configuration binding differs')
        for key in ('model','provider','reasoning_effort','prompts'):
            if key in configuration and key in manifest:
                saved._require(configuration[key]==manifest[key],'saved configuration differs: '+key)
    prompts = manifest.get('prompts')
    saved._require(isinstance(prompts,list),'early manifest requires prompts')
    by_id = {}
    for prompt in prompts:
        saved._require(isinstance(prompt,dict) and set(prompt)=={'prompt_id','text'}
            and isinstance(prompt['prompt_id'],str) and isinstance(prompt['text'],str)
            and prompt['prompt_id'] not in by_id,'malformed or duplicate early prompt')
        by_id[prompt['prompt_id']] = prompt['text']
    return manifest,by_id


def _receipt_summary(line,row,declaration,sources):
    result = saved._receipt_record(line,row,declaration,sources)
    if 'exit_code' in row:
        result['exit_code'] = row['exit_code']
    # Error bodies may contain local account diagnostics. Native status and
    # exit code remain recorded evidence; no inferred failure reason is added.
    return result


def _compact(value):
    # These native review hashes use serde's field order, not sorted keys.
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()


def _parameters(value):
    """A concrete local launcher is not part of the recorded experiment method."""
    if isinstance(value,dict):
        return {key:_parameters(child) for key,child in value.items() if not (
            key=='cli' and isinstance(child,str) and child.startswith('/'))}
    if isinstance(value,list):
        return [_parameters(child) for child in value]
    return value


def _deprecated(versions):
    if not versions:
        return None
    parsed=[re.fullmatch(r'ASv(\d+)(?:\.(\d+))?',version) for version in versions]
    saved._require(all(parsed),'invalid recorded AS prompt version')
    return any((int(match[1]),int(match[2] or 0))<(6,100) for match in parsed)


def _lineage(sources, selection):
    provenance=selection.get('subject_provenance',dict(status='unknown',versions=[]))
    status,versions=provenance.get('status'),provenance.get('versions')
    saved._require(status in ('known','unknown') and isinstance(versions,list)
        and all(isinstance(version,str) for version in versions),'invalid subject provenance')
    recorded=[]
    for declaration in provenance.get('version_sources',[]):
        value=sources.read(declaration['path'])
        for key in declaration['field']:
            saved._require(isinstance(value,dict) and key in value,'AS version source field is missing')
            value=value[key]
        saved._require(isinstance(value,str),'AS version source is not a version string')
        recorded.append(value)
    for declaration in provenance.get('used_inputs',[]):
        sources.raw(declaration['path'])
    saved._require((status=='known' and versions and set(recorded)==set(versions)) or
        (status=='unknown' and not versions and not recorded),'recorded AS versions differ from provenance')
    return dict(lineage_status=status,subject_prompt_versions=versions,
        generated_subjects_deprecated=_deprecated(versions),raw_posts_deprecated=False,
        current_pipeline_validation=False)


def _review_state(sources, session, batch):
    state = sources.read(session['path'])
    frozen = sources.read(batch['path'])
    saved._require(isinstance(state,dict) and set(state)=={'schema_version','state_sha256','session'}
        and isinstance(state['session'],dict),'unsupported review state')
    saved._require(state['state_sha256']==saved._sha(_compact(state['session'])),
                   'review state hash differs')
    saved._require(state['session'].get('batch_sha256')==saved._sha(_compact(frozen)),
                   'review batch hash differs')
    saved._require(isinstance(frozen.get('items'),list),'review batch requires items')
    items={item['item_id']:item for item in frozen['items']}
    saved._require(len(items)==len(frozen['items']),'duplicate review batch identity')
    decisions=state['session'].get('decisions')
    saved._require(isinstance(decisions,dict) and set(decisions)<=items.keys(),
                   'review decision has no frozen batch item')
    for decision in decisions.values():
        saved._require(isinstance(decision,dict) and set(decision)=={'outcome','comment'}
            and decision['outcome'] in (None,'approved','rejected')
            and isinstance(decision['comment'],str),'unsupported scientific review decision')
    return state,frozen,items


def _review_records(sources, selection, answers, prompt_inputs):
    decisions=[]
    by_id={answer['id']:answer for answer in answers}
    for declaration in selection.get('review_sessions',[]):
        state,batch,items=_review_state(sources,declaration,declaration['batch'])
        preparation={}
        if declaration.get('preparation'):
            prepared=sources.read(declaration['preparation']['path'])
            preparation={item['item_id']:item for item in prepared.get('items',[])}
        for identifier,decision in state['session']['decisions'].items():
            item=items[identifier]
            candidates=[answer for answer in by_id.values() if
                answer['source']['path'] in declaration['answer_sources'] and answer['prompt_id']==identifier]
            saved._require(len(candidates)==1,'review item lacks a unique original answer')
            answer=candidates[0]
            supplied=prompt_inputs[answer['input_ref']]['variables']
            saved._require(item['note']==supplied['post'] and
                item['subject']==supplied.get('subject',supplied.get('takeaway')),
                'review post/meaning differs from the original supplied input')
            raw=json.loads(answer['raw_response'])
            fragments=[fragment['text'] for fragment in item['fragments']]
            mapping=None
            if raw!=fragments:
                prepared=preparation.get(identifier,{})
                mapping=prepared.get('generated_fragment_numbers_in_display_order')
                saved._require(isinstance(raw,list) and isinstance(mapping,list) and
                    sorted(mapping)==list(range(1,len(raw)+1)) and
                    prepared.get('generated_fragments')==raw and
                    prepared.get('display_fragments')==item['fragments'] and
                    [raw[index-1] for index in mapping]==fragments,
                    'review display differs without a recorded permutation')
            record=dict(type='user_decision',role='user_review',item_id=identifier,
                outcome=decision['outcome'],comment=decision['comment'],
                raw_answer_ref=answer['id'],raw_sha256=answer['raw_sha256'],
                source=saved._binding(declaration),original_batch=saved._binding(declaration['batch']),
                state_sha256=state['state_sha256'],batch_sha256=state['session']['batch_sha256'])
            record['id']=saved._sha(_compact([record['state_sha256'],record['batch_sha256'],identifier]))
            if mapping is not None:
                record['display_fragment_numbers']=mapping
                record['display_preparation']=saved._binding(declaration['preparation'])
            decisions.append(record)
    return decisions


def _snapshot_references(value, declaration, sources, selection):
    for reference in selection.get('review_snapshot_references',[]):
        if reference['source']['path']!=declaration['path']:
            continue
        saved._require(reference['source']['sha256']==declaration['sha256'],
                       'review snapshot source binding differs')
        state,_,_=_review_state(sources,reference['session'],reference['batch'])
        path=reference['field']
        saved._require(isinstance(path,list) and path and all(isinstance(key,str) for key in path),
                       'invalid review snapshot field path')
        cursor=value
        for key in path:
            saved._require(isinstance(cursor,dict) and key in cursor,'review snapshot field is absent')
            cursor=cursor[key]
        saved._require(cursor==state,'embedded review snapshot differs from the original state')
        cursor=value
        for key in path[:-1]:cursor=cursor[key]
        cursor[path[-1]]=dict(type='review_snapshot_reference',
            source=saved._binding(reference['session']),batch=saved._binding(reference['batch']),
            state_sha256=state['state_sha256'],batch_sha256=state['session']['batch_sha256'])
    return value


def prepare(sources, selection, metadata):
    helper = Path(saved.__file__)
    before = helper.stat()
    helper_stamp = before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns
    metadata['exporter_sources']['sse_multivector/mask_goal_publication.py'] = saved._sha(helper.read_bytes())
    inputs,answers,judgments,results = [],[],[],[]
    settings,templates,input_ids,answer_ids = {},{},set(),set()
    selected_subjects = []
    counts = dict(saved_responses=0,mask_answer=0,takeaway_answer=0,configured_cases=0,
                  not_recorded=0,recorded_unsuccessful=0,reused_receipt_rows=0,setup_notes=0)
    baseline_outputs = []
    lineage=_lineage(sources,selection)

    def subject_inputs(value):
        if isinstance(value,dict):
            if {'note_id','subject','note'} <= value.keys() and isinstance(value['subject'],str):
                selected_subjects.append(value)
            for child in value.values():subject_inputs(child)
        elif isinstance(value,list):
            for child in value:subject_inputs(child)

    for declaration in selection.get('inputs',[]):
        value = sources.read(declaration['path'])
        subject_inputs(value)
        omitted = []
        if isinstance(value,dict):
            omitted = [name for name in ('previous_note_ids','exclusion_source_files') if name in value]
            value = {name:item for name,item in value.items() if name not in omitted}
        inputs.append(dict(type='saved_input',source=saved._binding(declaration),
                           data=saved._project(value,sources),omitted_unused_inventories=omitted))
    for declaration in selection.get('parameters',[]):
        value,origin = saved._parameter_fields(sources.read(declaration['path']),declaration)
        inputs.append(dict(type='study_parameters',source=origin,
                           data=saved._project(_parameters(value),sources)))
    for declaration in selection.get('baseline_references',[]):
        value = sources.read(declaration['path'])
        output = value.get('output',value) if isinstance(value,dict) else value
        if declaration.get('source'):
            original=sources.read(declaration['source']['path'])
            saved._require(value.get('source_sha256')==declaration['source']['sha256'] and output==original,
                           'baseline snapshot differs from original bound source')
        saved._require(isinstance(output,dict) and
            (isinstance(output.get('notes'),list) or isinstance(output.get('responses'),list)),
            'unsupported saved baseline reference')
        if declaration.get('manifest'):
            sources.read(declaration['manifest']['path'])
            saved._require(output.get('manifest_sha256')==declaration['manifest']['sha256'],
                           'baseline manifest binding differs')
        if 'notes' in output:
            baseline_outputs.append((declaration,output))
        inputs.append(dict(type='baseline_reference',source=saved._binding(declaration),
            recorded_source_sha256=value.get('source_sha256'),
            recorded_source=saved._reference(value['source_path'],sources) if 'source_path' in value else None))

    for receipt_only,key in ((False,'answers'),(True,'receipt_only_answers')):
        for declaration in selection.get(key,[]):
            manifest,prompts = _manifest(sources,declaration)
            manifest_sha = declaration['manifest']['sha256']
            receipt_decl = declaration if receipt_only else declaration.get('receipt')
            receipts = saved._receipts(sources,receipt_decl,manifest_sha)
            counts['reused_receipt_rows'] += sum('reused_from' in row for _,row in receipts)
            if receipt_only:
                responses = []
                seen = set()
                for _,row in receipts:
                    if row.get('status') != 'succeeded':
                        continue
                    identifier,raw = row.get('note_id'),row.get('final_output_raw')
                    saved._require(identifier in prompts and isinstance(raw,str)
                        and identifier not in seen,'ambiguous receipt-only successful answer')
                    seen.add(identifier)
                    responses.append(dict(prompt_id=identifier,response=raw))
            else:
                output = sources.read(declaration['path'])
                saved._require(isinstance(output,dict) and set(output)=={
                    'schema_version','manifest_sha256','responses'} and output['schema_version']==1
                    and isinstance(output['responses'],list),'unsupported saved early output')
                saved._require(output['manifest_sha256']==manifest_sha,'output manifest binding differs')
                responses = output['responses']
            setting = saved._settings(manifest)
            setting_id = saved._sha(json.dumps(setting,sort_keys=True,separators=(',',':')).encode())
            settings[setting_id] = setting
            response_ids = set()
            inputs_by_prompt = {}
            for identifier,prompt in prompts.items():
                template,variables,role = _factor(prompt,declaration['task'])
                template_id = saved._sha(template.encode())
                templates[template_id] = template
                input_ref = saved._sha(json.dumps(dict(template_id=template_id,variables=variables),
                    sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
                inputs_by_prompt[identifier] = (input_ref,template_id,role)
                if input_ref not in input_ids:
                    input_ids.add(input_ref)
                    inputs.append(dict(type='prompt_input',id=input_ref,prompt_template_id=template_id,
                        variables=variables,canonical_note_id=None,
                        source=dict(**declaration['manifest'],prompt_id=identifier)))
                counts['configured_cases'] += 1
            for response in responses:
                saved._require(isinstance(response,dict) and set(response)=={'prompt_id','response'}
                    and response['prompt_id'] in prompts and response['prompt_id'] not in response_ids
                    and isinstance(response['response'],str),'invalid early response row')
                identifier,raw = response['prompt_id'],response['response']
                response_ids.add(identifier)
                prompt_sha,raw_sha = saved._sha(prompts[identifier].encode()),saved._sha(raw.encode())
                matched = []
                for line,row in receipts:
                    if row.get('note_id') != identifier or row.get('prompt_sha256') != prompt_sha:
                        continue
                    if row.get('final_output_raw',row.get('response')) != raw:
                        continue
                    saved._require(row.get('final_output_sha256')==raw_sha,'receipt response hash differs')
                    matched.append(_receipt_summary(line,row,receipt_decl,sources))
                if receipt_decl:
                    saved._require(matched,'early answer lacks matching receipt')
                input_ref,template_id,role = inputs_by_prompt[identifier]
                answer_id=declaration['path']+'#'+identifier
                saved._require(answer_id not in answer_ids,'duplicate final answer identity')
                answer_ids.add(answer_id)
                answers.append(dict(id=answer_id,prompt_id=identifier,role=role,
                    raw_response=raw,raw_sha256=raw_sha,prompt_sha256=prompt_sha,
                    input_ref=input_ref,prompt_template_id=template_id,settings_ref=setting_id,
                    source=saved._binding(declaration),receipts=matched))
                counts['saved_responses'] += 1
                counts[role] += 1
            for identifier in prompts:
                if identifier in response_ids:
                    continue
                rows = [(line,row) for line,row in receipts if row.get('note_id')==identifier]
                outcome = 'recorded_unsuccessful' if rows else 'not_recorded'
                counts[outcome] += 1
                results.append(dict(type='case_outcome',prompt_id=identifier,
                    input_ref=inputs_by_prompt[identifier][0],outcome=outcome,
                    receipts=[_receipt_summary(line,row,receipt_decl,sources) for line,row in rows],
                    source=saved._binding(declaration['manifest'])))

    failed=selection.get('failed_attempt')
    if failed:
        manifest,prompts=_manifest(sources,failed)
        rows=saved._receipts(sources,failed,failed['manifest']['sha256'])
        identifier=failed['case_id']
        selected=[(line,row) for line,row in rows if row.get('note_id')==identifier]
        saved._require(identifier in prompts and selected and
            all(row.get('status')!='succeeded' for _,row in selected),'invalid failed case selection')
        results.append(dict(type='case_outcome',prompt_id=identifier,outcome='recorded_unsuccessful',
            source=saved._binding(failed),receipts=[_receipt_summary(line,row,failed,sources)
                                                  for line,row in selected]))
        counts['recorded_unsuccessful']+=1
        counts['configured_cases']+=1

    setup = {}
    setup_sources = []
    for declaration,output in baseline_outputs:
        for note in output['notes']:
            for subject in note['subjects']:
                setup[(note['note_id'],subject['source_index'],subject['text'])]=note['text']
    for declaration in selection.get('setup_outputs',[]):
        output = sources.read(declaration['path'])
        manifest = sources.read(declaration['manifest']['path'])
        saved._require(output.get('manifest_sha256')==declaration['manifest']['sha256'],
                       'setup output manifest binding differs')
        if 'input' in declaration:
            sources.raw(declaration['input']['path'])
            saved._require(manifest.get('input_sha256')==declaration['input']['sha256'],
                           'setup input binding differs')
        rows = saved._receipts(sources,declaration.get('receipt'),declaration['manifest']['sha256'])
        for note in output['notes']:
            counts['setup_notes'] += 1
            for subject in note['subjects']:
                item=(note['note_id'],subject['source_index'],subject['text'])
                saved._require(item not in setup or setup[item]==note['text'],
                               'conflicting subject setup context')
                setup[item]=note['text']
            matches = 0
            for _,row in rows:
                if row.get('note_id')!=note['note_id'] or row.get('status')!='succeeded':
                    continue
                raw = row.get('final_output_raw')
                saved._require(isinstance(raw,str) and saved._sha(raw.encode())==row.get('final_output_sha256'),
                               'setup raw answer hash differs')
                parsed=json.loads(raw)
                saved._require(parsed.get('subjects')==[subject['text'] for subject in note['subjects']],
                               'setup parsed subjects differ from saved raw answer')
                matches += 1
            if declaration.get('receipt'):
                saved._require(matches==1,'setup note lacks a unique successful source receipt')
        subject = manifest.get('subject',{})
        setup_sources.append(dict(source=saved._binding(declaration),manifest=declaration['manifest'],
            recorded_subject_settings={key:subject[key] for key in
                ('prompt_version','prompt_sha256','model','reasoning_effort','response_schema_sha256') if key in subject},
            generated_subjects_deprecated=_deprecated([subject['prompt_version']]) if
                subject.get('prompt_version') else None,
            input_normalization_version=manifest.get('subject_input_normalization_version')))
    # Setup is validation evidence for selected inputs, never extra model-answer
    # rows or a publication of every unused subject from its preparation calls.
    if setup:
        for item in selected_subjects:
            key=(item['note_id'],item.get('source_index'),item['subject'])
            # A study may combine a separately preserved baseline with setup.
            # Its exact baseline reference remains explicit rather than guessed.
            available=any(note_id==key[0] for note_id,_,_ in setup)
            if lineage['lineage_status']=='known':
                saved._require(available,'selected subject has no bound AS source')
            if available:
                matches=[text for (note_id,index,subject),text in setup.items() if note_id==key[0]
                    and subject==key[2] and ('source_index' not in item or index==key[1])]
                saved._require(matches,'selected subject differs from its setup source')
                saved._require(item.get('note') in matches,'selected post differs from its setup source')
    prompt_inputs={record['id']:record for record in inputs if record['type']=='prompt_input'}
    judgments.extend(_review_records(sources,selection,answers,prompt_inputs))
    for declaration in selection.get('records',[]):
        role = declaration['role']
        value=_snapshot_references(sources.read(declaration['path']),declaration,sources,selection)
        record = dict(role=role,source=saved._binding(declaration),data=saved._project(value,sources))
        (results if role in ('mechanical','measurements','comparison') else judgments).append(record)
    metadata.update(settings=settings,counts=counts,setup_sources=setup_sources,input=lineage,
        provenance=dict(AS_status='Unknown unless explicitly bound by saved subject-generation evidence; '
            'TP/MP version numbers do not establish AS lineage.',
            preparation='Setup outputs are verified source bindings for used inputs, not standalone trials.',
            post_identity='Factored prompt IDs do not assert Nostr IDs; canonical IDs remain in saved source inputs where recorded.',
            decisions='Saved user decisions, agent assessments and undecided cases retain their original roles.'))
    if 'expected_final_answers' in selection:
        saved._require(counts['saved_responses']==selection['expected_final_answers'],
                       'final answer count differs from frozen selection')
    input_records = [dict(type='prompt_template',id=identifier,text=text)
                     for identifier,text in sorted(templates.items())]+inputs

    def checked_results():
        yield from results
        after = helper.stat()
        saved._require((after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)==helper_stamp,
                       'reused publication helper changed during export')
    return {'inputs.jsonl':iter(input_records),'answers.jsonl':iter(answers),
            'judgments.jsonl':iter(judgments),'results.jsonl':checked_results()}
