"""Publication projection for explicitly selected historical mask studies.

Source-bound response strings remain verbatim. Frozen prompt inputs are factored
from their supplied XML blocks, not regenerated. Later assessments/corrections
remain separate from original answers and do not create new user decisions.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re


_PRIVATE = {'auth_file','auth_path','codex_home','credentials','headers',
    'api_key','api_token','access_token','password','environment','env','endpoint','base_url',
    'argv','stdout_json','stdout_jsonl','stderr','thread_id','runner_binary','codex_binary',
    'command','cwd','workdir','accounts','account','account_id','auth_directory',
    'launcher','launchers','authentication_note','tracking_card'}
_SETTINGS = {'model','provider','reasoning_effort','max_output_tokens','timeout_seconds',
             'mode','runner_sha256','wrapper_sha256','runner_version','codex_version',
             'response_schema_sha256'}
_PATH_KEYS = {'path','receipt_path','source_directory','baseline_directory','baseline_run',
    'run_directory','config_path','output_path','input_path','results_path','source_job',
    'source_output','subject_output','baseline_path','source_path','review_file',
    'all_masks_review_file'}
_LITERAL = {'text','note','source_text','raw','raw_response','response','fragments',
            'fragment','subject','inline_mask','expected_mask','mask','quote',
            'user_message_verbatim'}
_ABSOLUTE = re.compile(r'(?<![A-Za-z0-9_.-])/(?:home|Users|tmp|mnt|private|run)/[^\s\]\[(){}<>"\x27,;]+')


def _require(value, message):
    if not value:
        raise ValueError('mask study publication: '+message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _binding(selection):
    return dict(path=selection['path'],sha256=selection['sha256'])


def _parameter_fields(value, declaration):
    """Select reviewed root fields while retaining the original source binding."""
    origin = _binding(declaration)
    if 'fields' in declaration:
        fields = declaration['fields']
        _require(isinstance(value,dict) and isinstance(fields,list) and fields,
                 'parameter field selection requires an object and nonempty root paths')
        selected = []
        for path in fields:
            _require(isinstance(path,list) and len(path)==1 and isinstance(path[0],str)
                     and path[0] in value,'selected parameter root field is missing or invalid')
            _require(path[0] not in selected,'selected parameter fields repeat')
            selected.append(path[0])
        value = {key:value[key] for key in selected}
        origin['fields'] = fields
    return value,origin


def _portable(text, sources):
    """Convert known repository prefixes without changing scientific wording."""
    prefixes = (str(sources.root),'/home/dev/src/notedeck_worktrees/algos/oracle-mvp',
                '/home/dev/src/notedeck-publication/oracle-mvp')
    for prefix in prefixes:
        text = text.replace(prefix.rstrip('/')+'/', '')
    return text


def _reference(text, sources):
    portable = _portable(text,sources)
    if portable.startswith('/'):
        return dict(local_artifact=PurePosixPath(portable).name,
                    original_reference_sha256=_sha(text.encode()))
    return portable


def _project(value, sources, *, key='', omissions=None):
    """Preserve methods and findings; exclude concrete private/runtime fields.

    Historical ``execution`` and ``transport`` fields also describe experimental
    methods, so their names never justify dropping their complete contents.
    """
    if isinstance(value,dict):
        result = {}
        for name,child in value.items():
            if name in _PRIVATE:
                if omissions is not None:
                    omissions[0] += 1
                continue
            portable_name = _portable(name,sources)
            if portable_name.startswith('/'):
                portable_name = 'local-artifact:'+PurePosixPath(name).name+'[sha256:'+_sha(name.encode())+']'
            _require(portable_name not in result,'portable scientific field collision')
            result[portable_name] = _project(child,sources,key=name,omissions=omissions)
        return result
    if isinstance(value,list):
        return [_project(child,sources,key=key,omissions=omissions) for child in value]
    if isinstance(value,str):
        if key in _LITERAL:
            return value
        if key in _PATH_KEYS or key.endswith('_path') or key.endswith('_directory'):
            return _reference(value,sources)
        portable = _portable(value,sources)
        # Embedded scientific reasons may cite a local filename. Preserve the
        # sentence and filename, replacing only an otherwise unportable prefix.
        return _ABSOLUTE.sub(lambda match:'local-artifact:'+PurePosixPath(match[0]).name+
                             '[sha256:'+_sha(match[0].encode())+']',portable)
    return value


def _settings(manifest):
    result = {}
    for key in _SETTINGS:
        value = manifest.get(key)
        if value is None:
            continue
        _require(type(value) in (str,int,float,bool),'unsupported scalar request setting')
        if isinstance(value,str):
            _require(not value.startswith(('/','~')) and '\n' not in value and '://' not in value,
                     'nonportable request setting')
        result[key] = value
    return result


def _factor(prompt):
    """Factor the last supplied blocks, leaving few-shot examples intact."""
    _require(isinstance(prompt,str),'prompt must be text')
    if '<candidate_A>\n' in prompt and '<candidate_B>\n' in prompt:
        names,role = ('subject','candidate_A','candidate_B'),'mask_comparison_answer'
    elif '<marked_original>\n' in prompt:
        names,role = ('marked_original','indexed_original'),'position_answer'
    else:
        names = ('post','indexed_post','subject')
        role = 'mask_answer' if '<subject>\n' in prompt else 'subject_input'
    spans,variables = [],{}
    for name in names:
        opening,closing = '<'+name+'>\n','\n</'+name+'>'
        start = prompt.rfind(opening)
        if start < 0:
            continue
        start += len(opening)
        end = prompt.find(closing,start)
        _require(end >= start,'unclosed supplied '+name+' block')
        spans.append((start,end,name))
        variables[name] = prompt[start:end]
    required = ('subject','candidate_A','candidate_B') if role=='mask_comparison_answer' else (
        ('marked_original','indexed_original') if role=='position_answer' else
        ('post','subject') if role=='mask_answer' else ('post',))
    _require(all(name in variables for name in required),'unsupported supplied prompt inputs')
    template = prompt
    for start,end,name in sorted(spans,reverse=True):
        template = template[:start]+'{{'+name+'}}'+template[end:]
    restored = template
    for name in sorted(variables,key=lambda name:prompt.rfind('<'+name+'>')):
        restored = restored.replace('{{'+name+'}}',variables[name])
    _require(restored == prompt,'factored prompt reconstruction differs')
    return template,variables,role


def _receipts(sources, declaration, manifest_sha):
    if declaration is None:
        return []
    rows = []
    for line_no,line in enumerate(sources.raw(declaration['path']).splitlines(),1):
        if not line.strip():
            continue
        row = json.loads(line)
        _require(isinstance(row,dict),'receipt must be a JSON object')
        _require(row.get('manifest_sha256') == manifest_sha,'receipt manifest binding differs')
        rows.append((line_no,row))
    return rows


def _receipt_record(line_no,row,declaration,sources):
    keep = {'status','attempt','prompt_sha256','request_sha256','final_output_sha256',
            'runner_sha256','wrapper_sha256','execution','elapsed_seconds','usage'}
    result = {key:_project(row[key],sources,key=key) for key in keep if key in row}
    result['source'] = dict(**_binding(declaration),line=line_no)
    if 'reused_from' in row:
        reused = row['reused_from']
        _require(isinstance(reused,dict),'invalid reuse binding')
        result['reused_from'] = {key:_project(reused[key],sources,key=key) for key in
            ('manifest_sha256','result_line','result_sha256','results_path') if key in reused}
    return result


def prepare(sources, selection, metadata):
    """Project a declared study through the common historical publication API."""
    inputs,answers,judgments,results = [],[],[],[]
    templates,settings = {},{}
    counts = dict(saved_responses=0,mask_answer=0,subject_input=0,
                  mask_comparison_answer=0,position_answer=0,receipt_rows=0,reused_receipt_rows=0)
    omissions = [0]
    for declaration in selection.get('inputs',[]):
        inputs.append(dict(type='saved_input',source=_binding(declaration),
            data=_project(sources.read(declaration['path']),sources,omissions=omissions)))
    for declaration in selection.get('parameters',[]):
        value,origin = _parameter_fields(sources.read(declaration['path']),declaration)
        inputs.append(dict(type='study_parameters',source=origin,
            data=_project(value,sources,omissions=omissions)))
    for declaration in selection.get('answers',[]):
        output = sources.read(declaration['path'])
        manifest_decl = declaration['manifest']
        manifest = sources.read(manifest_decl['path'])
        _require(isinstance(output,dict) and set(output)=={'schema_version','manifest_sha256','responses'}
                 and output['schema_version']==1 and isinstance(output['responses'],list),
                 'unsupported saved response envelope')
        _require(output['manifest_sha256']==manifest_decl['sha256'],'output manifest binding differs')
        config_decl = declaration.get('configuration')
        if config_decl:
            config = sources.read(config_decl['path'])
            _require(manifest.get('config_sha256')==config_decl['sha256'],'configuration binding differs')
            for key in ('model','provider','reasoning_effort'):
                if key in config and key in manifest:
                    _require(config[key]==manifest[key],'saved setting differs: '+key)
            if 'prompts' in config:
                _require(config['prompts']==manifest.get('prompts'),'configuration prompt bindings differ')
        setting = _settings(manifest)
        setting_id = _sha(json.dumps(setting,sort_keys=True,separators=(',',':')).encode())
        settings[setting_id] = setting
        prompts = manifest.get('prompts')
        _require(isinstance(prompts,list),'manifest requires saved prompts')
        by_id = {}
        for prompt in prompts:
            _require(isinstance(prompt,dict) and set(prompt)=={'prompt_id','text'}
                     and isinstance(prompt['prompt_id'],str) and prompt['prompt_id'] not in by_id,
                     'duplicate or malformed manifest prompt')
            by_id[prompt['prompt_id']] = prompt['text']
        receipt_decl = declaration.get('receipt')
        receipts = _receipts(sources,receipt_decl,manifest_decl['sha256'])
        counts['receipt_rows'] += len(receipts)
        counts['reused_receipt_rows'] += sum('reused_from' in row for _,row in receipts)
        seen = set()
        for row in output['responses']:
            _require(isinstance(row,dict) and set(row)=={'prompt_id','response'}
                     and row['prompt_id'] in by_id and row['prompt_id'] not in seen
                     and isinstance(row['response'],str),'invalid saved response row')
            identifier,response = row['prompt_id'],row['response']
            seen.add(identifier)
            prompt = by_id[identifier]
            template,variables,role = _factor(prompt)
            template_id = _sha(template.encode())
            templates[template_id] = template
            input_ref = _sha(json.dumps(dict(template_id=template_id,variables=variables),
                sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
            inputs.append(dict(type='prompt_input',id=input_ref,prompt_template_id=template_id,
                               variables=variables,source=dict(**manifest_decl,prompt_id=identifier)))
            prompt_sha,response_sha = _sha(prompt.encode()),_sha(response.encode())
            matched = []
            for line_no,receipt in receipts:
                if receipt.get('note_id',identifier) != identifier:
                    continue
                if receipt.get('prompt_sha256') != prompt_sha:
                    continue
                final = receipt.get('final_output_raw',receipt.get('response'))
                if final != response:
                    continue
                if 'final_output_sha256' in receipt:
                    _require(receipt['final_output_sha256']==response_sha,'receipt response hash differs')
                matched.append(_receipt_record(line_no,receipt,receipt_decl,sources))
            if receipt_decl:
                _require(matched,'saved response lacks an exact matching receipt')
            answers.append(dict(id=declaration['path']+'#'+identifier,role=role,
                prompt_id=identifier,input_ref=input_ref,prompt_template_id=template_id,
                settings_ref=setting_id,prompt_sha256=prompt_sha,raw_response=response,
                raw_sha256=response_sha,source=_binding(declaration),receipts=matched))
            counts['saved_responses'] += 1
            counts[role] += 1
    for declaration in selection.get('records',[]):
        role = declaration['role']
        _require(role in ('assessment','correction','comparison','measurements'),
                 'unknown scientific record role')
        record = dict(role=role,source=_binding(declaration),
            data=_project(sources.read(declaration['path']),sources,omissions=omissions))
        (judgments if role in ('assessment','correction') else results).append(record)
    failed = selection.get('failed_attempt')
    if failed:
        manifest = sources.read(failed['manifest']['path'])
        sources.read(failed['configuration']['path'])
        _require(manifest.get('config_sha256')==failed['configuration']['sha256'],
                 'failed attempt configuration binding differs')
        status = sources.read(failed['status']['path'])
        safe_status = {key:status[key] for key in ('prompt_version','prompt_status','status',
            'attempted_case_ids','not_started_case_ids','model_requests_sent','responses_generated','retries')
            if key in status}
        _require(safe_status.get('responses_generated')==0,'failed-attempt declaration has semantic outputs')
        rows = _receipts(sources,failed.get('receipt'),failed['manifest']['sha256'])
        safe_status['receipt_statuses'] = [dict(status=row.get('status'),attempt=row.get('attempt'))
                                         for _,row in rows]
        results.append(dict(role='failed_attempt',source=_binding(failed['status']),data=safe_status))
        metadata['settings_for_failed_attempt'] = _settings(manifest)
    # Inputs common to intentional repeats are stored once. Original source
    # records and response IDs still retain each recorded trial separately.
    unique_inputs = {}
    for record in inputs:
        key = record.get('id') if record['type']=='prompt_input' else record['source']['path']
        unique_inputs.setdefault((record['type'],key),record)
    input_records = [dict(type='prompt_template',id=identifier,text=text)
                     for identifier,text in sorted(templates.items())]+list(unique_inputs.values())
    metadata.update(settings=settings,counts=counts,
        provenance=dict(subject_generation='unknown_unless_explicitly_recorded_in_saved_inputs',
            AS_status='historical; preserve explicit source versions and unresolved lineage',
            decisions='Original recorded attribution only; corrections do not overwrite earlier judgments.'),
        omitted_operational_fields=omissions[0])
    return {'inputs.jsonl':iter(input_records),'answers.jsonl':iter(answers),
            'judgments.jsonl':iter(judgments),'results.jsonl':iter(results)}
