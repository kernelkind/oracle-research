"""Replace a saved epsilon section with its native synthetic definition.

Preparation reuses every remaining original vector, including unassigned ones.
Run the ordinary SSE worker on the single prepared encoding, then collect to
rerun the original HDBSCAN configuration and the unchanged epsilon rule.
No teacher calls or saved hierarchy edits are performed.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

from . import hdbscan_epsilon_review as review
from . import hierarchy_generation as generation
from . import worker
from . import experiment as workflow


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(directory, experiment, case_id):
    directory = Path(directory).resolve()
    experiment = Path(experiment).resolve()
    native, _, _ = workflow.load(experiment)
    if native['dataset']['adapter'] != 'hierarchy_group_consolidation':
        raise ValueError('replacement requires a native grouped-consolidation section')
    with workflow.report_scope(isolated=True):
        result = workflow.report(experiment, only={case_id}, include_request_preview=False)
    if len(result['cases']) != 1 or result['cases'][0]['status'] != 'valid':
        raise ValueError('replacement requires one valid native synthetic meaning')
    case = result['cases'][0]
    evidence = case.get('evidence', {})
    if not {'epsilon_review', 'state', 'section', 'groups'} <= set(evidence):
        raise ValueError('replacement requires source-bound epsilon section evidence')
    sources = {}

    def read_bytes(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if str(path) in sources and sources[str(path)] != digest:
            raise ValueError('replacement source changed during preparation: ' + str(path))
        sources[str(path)] = digest
        return raw

    def read(path):
        return json.loads(read_bytes(path))

    expected, _ = review.prepare_section_source(dict(schema_version=1,
        epsilon_review=evidence['epsilon_review'], section=evidence['section']),
        experiment, read, read_bytes)
    if (expected[0]['id'] != case_id or expected[0]['inputs'] != case['inputs']
            or expected[0]['evidence'] != evidence):
        raise ValueError('replacement producer differs from the original section')
    state = read(evidence['state'])
    analysis = read(evidence['epsilon_review'])
    groups = {g['id']: g for g in analysis['groups']}
    removed = sorted(i for g in evidence['groups'] for i in groups[g]['original_ids'])
    removed_set = set(removed)
    original_ids = state['families'][0]['rounds'][0]['current']
    if len(removed_set) != len(removed) or not removed_set <= set(original_ids):
        raise ValueError('replacement membership is not a unique original subset')
    retained = [i for i in original_ids if i not in removed_set]
    for path, expected_hash in {**native['sources'], **{
            str(experiment/name): value for name, value in native['files'].items()}}.items():
        if hashlib.sha256(read_bytes(path)).hexdigest() != expected_hash:
            raise ValueError('native replacement producer changed: ' + str(path))
    for path in [experiment/'experiment.json', Path(native['run_directory'])/'manifest.json',
                 case['receipt']['results_path'], state['hdbscan_binary']]:
        read_bytes(path)
    for path in [Path(__file__), Path(review.__file__), Path(generation.__file__),
                 Path(worker.__file__), Path(review.hdbscan.__file__)]:
        read_bytes(path)
    replacement = dict(subject=case['parsed']['title'], meaning=case['parsed']['meaning'],
                       original_ids=removed)
    pool = dict(generation_policy=state['generation_policy'], originals=state['originals'],
                note_ids=state['note_ids'], worker_config=state['worker_config'],
                items={i: deepcopy(state['items'][i]) for i in retained},
                encodings=deepcopy(state['encodings']), vectors=deepcopy(state['vectors']),
                sources={str(Path(worker.__file__).resolve()): sha(worker.__file__)})
    pool['items']['R00001'] = replacement
    directory.mkdir(parents=True, exist_ok=False)
    first_new_encoding = len(pool['encodings'])
    generation._prepare_encoding(directory, pool, ['R00001'])
    plan = dict(schema_version=1, experiment=str(experiment), case=case_id,
                receipt=case['receipt'], source_state=evidence['state'],
                source_review=evidence['epsilon_review'], removed_ids=removed,
                current_ids=retained+['R00001'], first_new_encoding=first_new_encoding,
                hdbscan_binary=state['hdbscan_binary'], sources=sources, pool=pool)
    workflow.write(directory/'replacement.json', dict(plan=plan, sha256=workflow.inputs.digest(plan)))
    return dict(removed_entries=len(removed), reused_vectors=len(retained),
                updated_entries=len(retained)+1, worker_configs=[j['config'] for j in
                pool['encodings'][first_new_encoding:]])


def collect(directory, *, name='reclustered-sections'):
    directory = Path(directory).resolve()
    envelope = workflow.read(directory/'replacement.json')
    plan = envelope['plan']
    if workflow.inputs.digest(plan) != envelope['sha256']:
        raise ValueError('prepared replacement changed')
    for path, expected in plan['sources'].items():
        if sha(path) != expected:
            raise ValueError('replacement source changed: ' + path)
    pool = plan['pool']
    generation._collect_encodings(pool)
    if any(not j['complete'] for j in pool['encodings']):
        raise ValueError('replacement SSE encoding is incomplete')
    ids = plan['current_ids']
    vectors = generation._vectors(pool, ids)
    request, mapping = review.hdbscan.request_for(pool, ids, vectors)
    request_path, result_path = directory/'request.json', directory/'result.json'
    generation.trial._save_once(request_path, request)
    if not result_path.exists():
        executed = subprocess.run([plan['hdbscan_binary'], str(request_path)],
                                  capture_output=True, check=False)
        (directory/'stderr.txt').write_bytes(executed.stderr)
        if executed.returncode:
            raise ValueError('HDBSCAN command failed: ' + executed.stderr.decode(errors='replace'))
        response = json.loads(executed.stdout)
        review.hdbscan.members(response, request, mapping)
        generation.trial._save_once(result_path, response)
    response = workflow.read(result_path)
    provenance = dict(source_state=plan['source_state'], source_review=plan['source_review'],
        replacement_experiment=plan['experiment'], replacement_case=plan['case'],
        replacement_receipt=plan['receipt'], sources=plan['sources'],
        configuration=request['hdbscan_configuration'], request=str(request_path),
        request_sha256=sha(request_path), result=str(result_path), result_sha256=sha(result_path),
        new_model_calls=0, new_encodings=sum(len(j['keys']) for j in
            pool['encodings'][plan['first_new_encoding']:]), reused_vectors=len(ids)-1,
        encoder_receipts=[dict(config=j['config'], receipt_sha256=j['receipt_sha256'])
                          for j in pool['encodings']])
    result = review.group_review(response, request, mapping, pool, provenance)
    group = next((g for g in result['groups'] if 'R00001' in g['original_ids']), None)
    section = next((f'S{i+1:02d}' for i, s in enumerate(result['sections'])
                    if group and group['id'] in s['groups']), None)
    original_notes = {o['id']: o['local']['note_id'] for o in pool['originals']}
    result.update(encoded_entries=len(ids), assigned_entries=sum(g['entries'] for g in result['groups']),
        replacement=dict(id='R00001', title=pool['items']['R00001']['subject'],
            meaning=pool['items']['R00001']['meaning'], original_ids=plan['removed_ids'],
            note_ids=sorted({original_notes[i] for i in plan['removed_ids']}),
            group=group['id'] if group else None, section=section))
    review.write_review(result, directory, title='HDBSCAN after synthetic section replacement', name=name)
    return dict(groups=len(result['groups']), sections=len(result['sections']),
        epsilon=result['selection']['epsilon'], represented_notes=result['represented_notes'],
        replacement_group=result['replacement']['group'], replacement_section=section,
        svg=str(directory/(name+'.svg')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('directory', type=Path)
    prepare_parser.add_argument('--experiment', required=True, type=Path)
    prepare_parser.add_argument('--case', required=True)
    collect_parser = commands.add_parser('collect')
    collect_parser.add_argument('directory', type=Path)
    collect_parser.add_argument('--name', default='reclustered-sections')
    args = parser.parse_args()
    result = (prepare(args.directory, args.experiment, args.case) if args.command == 'prepare'
              else collect(args.directory, name=args.name))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
