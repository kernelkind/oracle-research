"""Bound saved manual SSE diagnostics; do not rerun their encoder or compiler.

Analysis JSON is already the compact scientific result, including unrounded
comparisons. Its native fields are retained. The compound study additionally
requires its saved (rounded) full CSV matrix. Other all-pairs tables and vector
files are working data, not required by those studies' frozen result contracts.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re


_LIMIT = 4 * 1024 * 1024
_PROPOSAL = set('schema_version experiment_id review_status question frozen_components '
    'carrier mask_rule families metrics record scope notes primary_comparisons comparison_rule '
    'overall_rule secondary_diagnostics comparisons items overall_gate requirements tests '
    'design mask_origin source ablation counterfactual'.split())
_ANALYSIS = set('schema_version experiment_id experiment_sha256 worker_input_sha256 dimensions '
    'vector_count overall_supportive families vector_order cosine_matrix primary_comparisons '
    'overall_passed secondary_diagnostics note_count raw_vectors_sha256 results worker_config_sha256 '
    'worker_receipt_sha256 comparison_count directions minimum_margin wins comparisons '
    'fixture_id fixture_sha256 request_sha256 target_reference_cosine_count group_median_count '
    'predictions verdicts'.split())
_FIXTURE = set('schema_version fixture_id review_status inference_authorized originating_assumption '
    'current_interpretation question stage sse_execution_contract target_contract counts rules '
    'verdicts source_artifacts source_notes reference_groups self_contained_cases '
    'context_resolution_cases mixed_note_cases stage_2_boundary'.split())
_PRIVATE = {'authorization', 'headers', 'api_key', 'api_token', 'password', 'credentials',
            'account', 'billing', 'environment', 'env', 'endpoint', 'secret', 'access_token',
            'auth_file', 'auth_path', 'codex_home', 'provider_base_url', 'base_url', 'refresh_token'}
_IDS = {'mask-fidelity-'+name for name in (
    'compound-subject-neighborhood-v1', 'location-v1', 'multifragment-requirements-v1',
    'multifragment-v1', 'real-note-transfer-v5', 'relationship-v1',
    'single-fragment-boundary-v1', 'single-fragment-factorial-v3',
    'solar-context-ablation-v4', 'telemetry-mask-counterfactual-v1')}


def _require(condition, message):
    if not condition:
        raise ValueError('representation publication: '+message)


def _science(value, allowed):
    _require(isinstance(value, dict) and not (value.keys()-allowed),
             'unsupported scientific document fields')
    _equal(value,'schema_version',1,False)

    def visit(item, depth=0):
        _require(depth < 64, 'scientific document exceeds nesting limit')
        if isinstance(item, dict):
            _require(not (_PRIVATE & {key.lower().replace('-', '_') for key in item}),
                     'private configuration in scientific document')
            for key, child in item.items():
                if key == 'path' or key.endswith('_path'):
                    _require(isinstance(child, str) and not child.startswith(('/', '~'))
                             and '..' not in Path(child).parts and '://' not in child,
                             'nonportable scientific source reference')
                visit(child, depth+1)
        elif isinstance(item, list):
            for child in item:
                visit(child, depth+1)
        elif isinstance(item, float):
            _require(math.isfinite(item), 'nonfinite scientific measurement')
    visit(value)
    return value


def _stamp(path):
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value),
             'invalid SHA256 binding')
    return value


def _equal(record, key, expected, required=True):
    if required or key in record:
        _require(record.get(key) == expected, key+' binding mismatch')


def _settings(value):
    """Only encoder settings, never arbitrary worker configuration containers."""
    _equal(value,'schema_version',1)
    result = {}
    for key in ('schema_version', 'request_sha256', 'checkpoint_sha256',
                'base_model_artifact_tree_sha256', 'device', 'note_batch_size',
                'container_image'):
        if key in value:
            result[key] = value[key]
    for key in ('request_sha256', 'checkpoint_sha256', 'base_model_artifact_tree_sha256'):
        if key in result:
            _digest(result[key])
    _require(result.get('device') in ('cpu', 'cuda') or
             re.fullmatch(r'cuda:\d+', str(result.get('device'))), 'unsupported device')
    _require(type(result.get('note_batch_size')) is int and result['note_batch_size'] > 0,
             'invalid batch size')
    _require(isinstance(result.get('container_image'), str) and re.fullmatch(
        r'[A-Za-z0-9_./:-]+@sha256:[0-9a-f]{64}', result['container_image']),
        'invalid container identity')
    model = value.get('model')
    _require(isinstance(model, dict), 'missing encoder model')
    result['model'] = {key:model[key] for key in
        ('base_model', 'dimensions', 'maximum_tokens', 'pooling') if key in model}
    _require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',
                         str(result['model'].get('base_model'))), 'invalid model identity')
    _require(re.fullmatch(r'[A-Za-z0-9_.-]+', str(result['model'].get('pooling'))),
             'invalid pooling identity')
    for key in ('dimensions', 'maximum_tokens'):
        _require(type(result['model'].get(key)) is int and result['model'][key] > 0,
                 'invalid model '+key)
    return result


def _rows(receipt, expected=None):
    rows = receipt.get('rows')
    _require(isinstance(rows, list) and receipt.get('row_count') == len(rows),
             'receipt row count mismatch')
    identities = []
    seen = set()
    for ordinal, row in enumerate(rows):
        _require(isinstance(row, dict), 'invalid receipt row')
        key = (row.get('note_id'), row.get('subject_id'))
        _digest(key[0])
        _require(isinstance(key[1], str) and re.fullmatch('[0-9a-f]{16}', key[1]),
                 'invalid subject row identity')
        _require(row.get('ordinal') == ordinal and key not in seen,
                 'duplicate or unordered receipt row identity')
        seen.add(key)
        if expected is not None:
            _require(ordinal < len(expected) and key == expected[ordinal],
                     'receipt/input row identity mismatch')
        _require(type(row.get('token_count')) is int and row['token_count'] > 0,
                 'invalid receipt token count')
        identities.append({name:row[name] for name in
                           ('ordinal', 'note_id', 'subject_id', 'token_count')})
    if expected is not None:
        _require(len(rows) == len(expected), 'receipt/input row count mismatch')
    return identities


def _request(value):
    _require(isinstance(value, dict) and value.keys() == {'schema_version', 'proposal_sha256', 'notes'}
             and value['schema_version'] == 1 and isinstance(value['notes'], list),
             'unsupported worker input')
    identities, seen = [], set()
    for note in value['notes']:
        _require(isinstance(note, dict) and note.keys() == {'note_id', 'text', 'subjects'},
                 'unsupported encoded input fields')
        _digest(note['note_id'])
        _require(note['note_id'] not in seen and isinstance(note['text'], str)
                 and isinstance(note['subjects'], list) and note['subjects'], 'invalid encoded note')
        seen.add(note['note_id'])
        raw = note['text'].encode('utf-8')
        subjects = set()
        for subject in note['subjects']:
            _require(isinstance(subject, dict) and subject.keys() == {'subject_id', 'byte_spans'},
                     'unsupported encoded subject fields')
            identifier, spans = subject['subject_id'], subject['byte_spans']
            _require(isinstance(identifier, str) and re.fullmatch('[0-9a-f]{16}',identifier)
                     and identifier not in subjects and isinstance(spans,list) and spans,
                     'invalid input subject identity or spans')
            subjects.add(identifier)
            end = 0
            for span in spans:
                _require(isinstance(span,list) and len(span) == 2 and all(type(x) is int for x in span)
                         and end <= span[0] < span[1] <= len(raw), 'invalid input byte spans')
                try:
                    raw[:span[0]].decode('utf-8')
                    raw[span[0]:span[1]].decode('utf-8')
                except UnicodeDecodeError:
                    raise ValueError('representation publication: byte span splits UTF-8') from None
                end = span[1]
            identities.append((note['note_id'], identifier))
    return identities


def _context_rows(fixture, analysis, rows):
    """Validate saved target/reference identities, without compiling a request."""
    targets = []

    def target(identifier, text, masks):
        _require(isinstance(identifier,str) and identifier and identifier not in targets
                 and isinstance(text,str) and isinstance(masks,list) and masks,
                 'invalid context target or manually supplied spans')
        targets.append(identifier)
        for mask in masks:
            fragment, occurrence = mask.get('text'), mask.get('occurrence')
            _require(isinstance(fragment,str) and fragment and type(occurrence) is int
                     and 0 < occurrence <= len(text), 'invalid context mask occurrence')
            start = -1
            for _ in range(occurrence):
                start = text.find(fragment,start+1)
                _require(start >= 0,'context mask fragment not in text')

    for name in ('self_contained_cases','context_resolution_cases'):
        for case in fixture.get(name,[]):
            for variant in case['variants']:
                target(variant['fixture_note_id'],variant['text'],variant['mask'])
    for case in fixture.get('mixed_note_cases',[]):
        for meaning in case['meanings']:
            target(meaning['meaning_id'],case['text'],meaning['mask'])
    references = []
    for group in fixture.get('reference_groups',[]):
        _require(isinstance(group['references'],list) and all(
            isinstance(text,str) and text for text in group['references']), 'invalid context references')
        references.extend((group['group_id'],index+1) for index in range(len(group['references'])))
    _equal(fixture.get('counts',{}),'target_vectors',len(targets))
    _equal(fixture.get('counts',{}),'reference_vectors',len(references))
    _require(len(rows) == len(targets)+len(references),'context receipt count mismatch')
    predictions = analysis.get('predictions')
    _require(isinstance(predictions,list) and len(predictions) == len(targets),
             'context prediction count mismatch')
    for ordinal,(identifier,prediction) in enumerate(zip(targets,predictions)):
        _require(prediction.get('target_id') == identifier and prediction.get('target_ordinal') == ordinal,
                 'context target identity mismatch')
        saved = prediction.get('reference_cosines')
        _require(isinstance(saved,dict) and set(saved) == {name for name,_ in references},
                 'context reference groups mismatch')
        for index,(group,reference_index) in enumerate(references,len(targets)):
            values = saved[group]
            _require(isinstance(values,list) and len(values) == sum(
                name == group for name,_ in references),'context reference count mismatch')
            value = values[reference_index-1]
            for key,expected in (('reference_index',reference_index),('reference_ordinal',index),
                                 ('reference_note_id',rows[index]['note_id']),
                                 ('reference_subject_id',rows[index]['subject_id'])):
                _equal(value,key,expected)
    _equal(analysis,'target_reference_cosine_count',len(targets)*len(references),False)
    _equal(analysis,'group_median_count',len(targets)*len(fixture.get('reference_groups',[])),False)


def _runtime(value):
    result = {'worker_sha256':_digest(value.get('worker_sha256'))}
    for key in ('python','encoder_class'):
        if key in value:
            _require(isinstance(value[key],str) and re.fullmatch(r'[A-Za-z0-9_.+-]+',value[key]),
                     'invalid encoder runtime '+key)
            result[key] = value[key]
    packages = value.get('packages',{})
    _require(isinstance(packages,dict),'invalid encoder packages')
    result['packages'] = {}
    for name in ('torch','transformers','tokenizers'):
        if name in packages:
            version = packages[name]
            _require(isinstance(version,str) and re.fullmatch(r'[A-Za-z0-9_.+-]+',version),
                     'invalid encoder package version')
            result['packages'][name] = version
    return result


def export_records(sources, directory, metadata):
    """Return the existing numerical writer's results and inputs iterables."""
    directory = Path(directory)
    stamps, sizes = {}, {}

    def read(name, path):
        path = Path(path)
        stamps[path] = _stamp(path)
        _require(stamps[path][1] <= _LIMIT, 'source exceeds 4 MiB limit')
        with sources.read(path) as stream:
            raw = stream.read(_LIMIT+1)
        _require(len(raw) <= _LIMIT, 'source exceeds 4 MiB limit')
        sizes[name] = len(raw)
        return raw

    def load(name, path):
        def pairs(items):
            result = {}
            for key,value in items:
                _require(key not in result, 'duplicate JSON field')
                result[key] = value
            return result
        value = json.loads(read(name,path), object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON value')))
        _require(isinstance(value,dict), 'source must be a JSON object')
        return value

    context = (directory/'analysis.json').is_file() and not (directory/'experiment.json').is_file()
    result_dir = directory if context else directory/'result'
    manifest = load('manifest.json', result_dir/'manifest.json')
    _equal(manifest,'schema_version',1)
    analysis = _science(load('analysis.json', result_dir/'analysis.json'), _ANALYSIS)
    receipt = load('worker-receipt.json', result_dir/'worker-receipt.json')
    hashes = metadata['sources']
    for name in ('analysis.json', 'worker-receipt.json'):
        binding = manifest.get('files',{}).get(name,{})
        _equal(binding, 'sha256', hashes[name])
        _equal(binding, 'bytes', sizes[name])
    if context:
        proposal_name = 'context-counterfactual-v1.json'
        proposal = _science(load(proposal_name,directory.parent/proposal_name), _FIXTURE)
        identifier = proposal.get('fixture_id')
        _require(identifier == 'sse-context-counterfactual-v1', 'unsupported context fixture')
        _equal(manifest, 'fixture_id', identifier)
        _equal(analysis, 'fixture_id', identifier)
        _equal(manifest, 'fixture_sha256', hashes[proposal_name])
        _digest(manifest.get('compile_manifest_sha256'))
        _equal(analysis, 'fixture_sha256', hashes[proposal_name])
        _equal(receipt, 'proposal_sha256', hashes[proposal_name])
        _digest(manifest.get('request_sha256'))
        _equal(analysis, 'request_sha256', manifest['request_sha256'])
        _equal(receipt, 'request_sha256', manifest['request_sha256'])
        settings = _settings(receipt)
        contract = proposal.get('sse_execution_contract',{})
        for key in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'container_image',
                    'device', 'note_batch_size', 'dimensions', 'maximum_tokens', 'pooling'):
            expected = settings['model'].get(key, settings.get(key))
            _equal(contract, key, expected)
        _equal(contract, 'base_model', settings['model']['base_model'])
        source_notes = load('context-counterfactual-source-notes-v1.json',
                            directory.parent/'context-counterfactual-source-notes-v1.json')
        _require(len(proposal.get('source_artifacts',[])) == 1, 'unsupported context source artifacts')
        artifact = proposal['source_artifacts'][0]
        _equal(artifact, 'path', 'sse_multivector/context-counterfactual-source-notes-v1.json')
        _equal(artifact, 'sha256', hashes['context-counterfactual-source-notes-v1.json'])
        _science(source_notes, {'schema_version','evidence_id','notes'})
        _require(isinstance(source_notes.get('notes'),list),'invalid context source posts')
        source_ids = set()
        for post in source_notes['notes']:
            _require(isinstance(post,dict) and post.keys() == {'note_id','text'}
                     and isinstance(post['text'],str) and post['note_id'] not in source_ids,
                     'invalid context source post')
            source_ids.add(_digest(post['note_id']))
        rows = _rows(receipt)
        _equal(proposal.get('counts',{}), 'total_vectors', len(rows))
        _context_rows(proposal,analysis,rows)
        input_records = [dict(type='fixture',data=proposal),dict(type='source_posts',data=source_notes)]
        metadata['binding_limitations'] = [
            'The compiled context request and compile manifest are not present. Their hashes are '
            'recorded bindings; the original fixture hash and saved result/receipt joins are verified. '
            'The Rust request compiler is not rerun.']
    else:
        proposal_name = 'experiment.json'
        proposal = _science(load(proposal_name,directory/proposal_name), _PROPOSAL)
        identifier = proposal.get('experiment_id')
        _require(identifier in _IDS, 'unsupported manual representation study')
        _equal(manifest,'experiment_id',identifier)
        _equal(analysis,'experiment_id',identifier,False)
        _equal(manifest,'experiment_sha256',hashes[proposal_name])
        request = load('worker-input.json',directory/'worker-input.json')
        expected = _request(request)
        settings = _settings(load('worker-config.json',directory/'worker-config.json'))
        for record in (request,receipt):
            _equal(record,'proposal_sha256',hashes[proposal_name])
        for record,key in ((settings,'request_sha256'),(receipt,'request_sha256'),
                           (manifest,'worker_input_sha256')):
            _equal(record,key,hashes['worker-input.json'])
        _equal(manifest,'worker_config_sha256',hashes['worker-config.json'])
        _equal(_settings(receipt),'model',settings['model'])
        for key in ('checkpoint_sha256','base_model_artifact_tree_sha256','device',
                    'container_image','note_batch_size'):
            _equal(receipt,key,settings[key])
        rows = _rows(receipt,expected)
        if 'compile_manifest_sha256' in manifest:
            compiled = load('compile-manifest.json',directory/'compile-manifest.json')
            _equal(manifest,'compile_manifest_sha256',hashes['compile-manifest.json'])
            for key in ('experiment_id','experiment_sha256','worker_input_sha256','worker_config_sha256'):
                _equal(compiled,key,manifest[key])
            compile_rows = compiled.get('rows',[])
            _require(len(compile_rows) == len(rows),'compile row count mismatch')
            for row,worker in zip(compile_rows,rows):
                _require(row.keys() == {'ordinal','experiment_note_id','worker_note_id',
                                       'worker_subject_id','byte_spans'}, 'unsupported compile row fields')
                for key,other in (('ordinal','ordinal'),('worker_note_id','note_id'),
                                  ('worker_subject_id','subject_id')):
                    _equal(row,key,worker[other])
            spans = {(note['note_id'],subject['subject_id']):subject['byte_spans']
                     for note in request['notes'] for subject in note['subjects']}
            for row in compile_rows:
                _equal(row,'byte_spans',spans[(row['worker_note_id'],row['worker_subject_id'])])
            input_records = [dict(type='proposal',data=proposal),dict(type='encoded_inputs',data=request),
                             dict(type='compile_rows',data=compile_rows)]
        else:
            input_records = [dict(type='proposal',data=proposal),dict(type='encoded_inputs',data=request)]
        for key,name in (('experiment_sha256',proposal_name),('worker_input_sha256','worker-input.json'),
                         ('worker_config_sha256','worker-config.json'),
                         ('worker_receipt_sha256','worker-receipt.json')):
            _equal(analysis,key,hashes[name],False)
    _equal(analysis,'dimensions',settings['model']['dimensions'],False)
    _equal(receipt,'dimensions',settings['model']['dimensions'])
    _equal(analysis,'vector_count',len(rows),False)
    _equal(receipt,'vector_format','row-major-f32le-v1')
    runtime = _runtime(receipt.get('runtime',{}))
    worker_sha = runtime['worker_sha256']
    _equal(manifest,'worker_sha256',worker_sha,False)
    _equal(manifest,'checkpoint_sha256',settings['checkpoint_sha256'],False)
    _equal(manifest,'base_model_artifact_tree_sha256',settings['base_model_artifact_tree_sha256'],False)
    _equal(manifest,'container_image_id','sha256:'+settings['container_image'].rsplit(':',1)[1],False)
    if context:
        _equal(proposal['sse_execution_contract'],'worker_sha256',worker_sha)
    raw_binding = receipt.get('files',{}).get('raw-vectors.f32le',{})
    _digest(raw_binding.get('sha256'))
    _equal(raw_binding,'bytes',len(rows)*settings['model']['dimensions']*4)
    if 'raw-vectors.f32le' in manifest.get('files',{}):
        _equal(manifest['files']['raw-vectors.f32le'],'sha256',raw_binding['sha256'])
        _equal(manifest['files']['raw-vectors.f32le'],'bytes',raw_binding['bytes'])
    _equal(analysis,'raw_vectors_sha256',raw_binding['sha256'],False)
    metadata.update(experiment_id=identifier,
        source_id=hashlib.sha256((identifier+':'+hashes[proposal_name]).encode()).hexdigest(),
        parameters=settings, recorded_review_status=proposal.get('review_status'),
        input=dict(subject_generation='not_applicable',span_origin='manually_supplied',
                   identity='Worker note IDs identify encoded fixtures; proposal source-post IDs '
                            'are separate references and may describe modified-text interventions.'),
        receipt=dict(row_count=len(rows),runtime=runtime,
            vector_format=receipt['vector_format'],
            raw_vectors={key:raw_binding[key] for key in ('sha256','bytes')}),
        exporter_sources={'representation_publication.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    final_manifest = _science({key:manifest[key] for key in
        ('overall_passed','overall_supportive','family_results') if key in manifest},
        {'overall_passed','overall_supportive','family_results'})
    if 'tree_hash_rule' in receipt:
        _equal(receipt,'tree_hash_rule','sorted-relative-path-type-size-content-sha256-v1')
        metadata['receipt']['tree_hash_rule'] = receipt['tree_hash_rule']
    matrix = None
    if identifier == 'mask-fidelity-compound-subject-neighborhood-v1':
        raw = read('cosine-matrix.csv',result_dir/'cosine-matrix.csv')
        binding = manifest.get('files',{}).get('cosine-matrix.csv',{})
        _equal(binding,'sha256',hashes['cosine-matrix.csv'])
        _equal(binding,'bytes',len(raw))
        matrix = list(csv.reader(io.StringIO(raw.decode('utf-8'))))
        order = matrix[0][1:]
        _require(len(order) == len(rows) and len(set(order)) == len(order)
                 and len(matrix) == len(order)+1,'matrix identity/count mismatch')
        for index,row in enumerate(matrix[1:]):
            _require(len(row) == len(order)+1 and row[0] == order[index], 'matrix row order mismatch')
            _require(all(math.isfinite(float(value)) for value in row[1:]),'invalid matrix value')

    def results():
        yield dict(type='analysis',data=analysis)
        if final_manifest:
            yield dict(type='recorded_manifest_outcome',data=final_manifest)
        if matrix is not None:
            yield dict(type='cosine_matrix',order=matrix[0][1:],values=[row[1:] for row in matrix[1:]],
                       precision='original saved CSV decimal strings')
        for path,stamp in stamps.items():
            _require(_stamp(path) == stamp,'source changed during export')
        metadata['source_snapshot_sha256'] = hashlib.sha256(json.dumps(
            hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()

    input_records.append(dict(type='encoded_row_identities',data=rows))
    return results(), iter(input_records)
