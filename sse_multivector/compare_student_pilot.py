"""Prepare reviewed, source-bound relation-only Compare development targets.

Native teacher collection/review remains authoritative. This offline preparation
does not call teachers, alter meanings, relabel uncertain reviews, or construct
a hierarchy. Missing class/branch coverage remains explicit.
"""
import argparse
from collections import Counter, defaultdict
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import string
import sys
import time

from .compare_student_inputs import accepted, validate_answer
from .distillation_run import file_hashes, read_json, sha256, write_json
from .experiment_inputs import digest, render


LABELS = ('equivalent', 'local_contains_canonical', 'canonical_contains_local', 'neither', 'uncertain')
INVERSE = dict(zip(LABELS, (LABELS[0], LABELS[2], LABELS[1], LABELS[3], LABELS[4])))


def reviewed_targets(bundle, producers):
    """Derive the same complete targets during preparation and before fitting."""
    if (bundle.get('schema_version') != 1 or producers.get('schema_version') != 1
            or producers.get('inference_calls') != 0):
        raise ValueError('expected native offline Compare collection')
    receipts = {}
    for producer in producers['experiments']:
        for case in producer['cases']:
            key = (producer['experiment'], case['id'])
            if key in receipts:
                raise ValueError('duplicate native producer identity')
            receipts[key] = (producer['prompt_id'], case['receipt'])
    groups, identities = defaultdict(list), set()
    roles = {name: {} for name in ('note', 'author', 'post')}
    for case in bundle['cases']:
        key = (case['experiment'], case['case_id'])
        if key in identities:
            raise ValueError('duplicate Compare decision identity')
        identities.add(key)
        if receipts.get(key) != (case['prompt_id'], case['receipt']):
            raise ValueError('Compare collection differs from native producer provenance')
        prompt = bundle['prompts'][case['prompt_sha256']]
        if (hashlib.sha256(prompt['text'].encode()).hexdigest() != case['prompt_sha256']
                or case['prompt_id'] not in prompt['prompt_ids']
                or digest(case['inputs']) != case['input_sha256']):
            raise ValueError('Compare prompt or input binding differs')
        payload = json.loads(case['inputs']['INPUT_JSON'])
        validate_answer(case['answer'], payload['local']['meaning'])
        evidence = case['evidence']
        role = evidence.get('role')
        if evidence.get('split') != 'train' or role not in {'train', 'evaluation'}:
            raise ValueError('pilot cases must retain original TRAIN and development roles')
        for side in ('local', 'canonical'):
            for value, name in ((evidence[side]['note_id'], 'note'),
                                (evidence[side]['pubkey'], 'author')):
                if value in roles[name] and roles[name][value] != role:
                    raise ValueError('Compare pilot crosses a note/author/content group')
                roles[name][value] = role
        text = ' '.join(payload['local']['post'].split())
        if text in roles['post'] and roles['post'][text] != role:
            raise ValueError('Compare pilot crosses a note/author/content group')
        roles['post'][text] = role
        groups[(role, evidence['family_id'])].append(case)
    data = dict(schema_version=1, task='compare', labels=LABELS, train=[], evaluation=[], excluded=[])
    for (role, _), cases in groups.items():
        signatures = [(c['evidence']['local']['case_id'], c['evidence']['canonical']['case_id'])
                      for c in cases]
        self_pair = len(cases) == 1 and signatures[0][0] == signatures[0][1]
        if not self_pair and (len(cases) != 2 or signatures[0] != signatures[1][::-1]):
            raise ValueError('Compare pilot requires complete reciprocal families')
        reason = None
        if not all(accepted(c['reviews']) for c in cases):
            reason = 'At least one current review is missing, rejected or unresolved.'
        elif (self_pair and cases[0]['answer']['relation'] != 'equivalent'
              or not self_pair and cases[1]['answer']['relation'] != INVERSE[cases[0]['answer']['relation']]):
            reason = 'Saved teacher decisions violate identity or reciprocal consistency.'
        for case in cases:
            identity = dict(experiment=case['experiment'], case_id=case['case_id'],
                            input_sha256=case['input_sha256'], receipt=case['receipt'])
            if reason:
                data['excluded'].append(dict(**identity, role=role, reason=reason))
                continue
            data[role].append(dict(**identity, state=render(
                bundle['prompts'][case['prompt_sha256']]['text'], case['inputs']),
                target=case['answer']['relation'], evidence=case['evidence'],
                reviews=case['reviews'], prompt_sha256=case['prompt_sha256']))
    if not data['train'] or not data['evaluation']:
        raise ValueError('reviewed targets must leave both development roles nonempty')
    return data


def prepare(collection, provenance, output):
    collection, provenance, output = map(Path, (collection, provenance, output))
    if output.exists():
        raise FileExistsError(output)
    bundle, producers = read_json(collection), read_json(provenance)
    data = reviewed_targets(bundle, producers)
    counts = {role: dict(Counter(row['target'] for row in data[role]))
              for role in ('train', 'evaluation')}
    branch_counts = {role: sum(bool(json.loads(c['inputs']['INPUT_JSON'])['canonical'][name])
        for c in bundle['cases'] if c['evidence']['role'] == role
        for name in ('parents', 'ancestors', 'descendants')) for role in counts}
    manifest = dict(schema_version=1, task='compare', labels=LABELS,
        sources={name: dict(path=str(p.resolve()), sha256=sha256(p))
                 for name, p in [('collection', collection), ('provenance', provenance)]},
        code_sha256={str(Path(__file__).resolve()): sha256(__file__)},
        prompt_sha256=sorted(bundle['prompts']), counts=counts,
        excluded=len(data['excluded']), all_five_labels=all(set(c) == set(LABELS) for c in counts.values()),
        canonical_branches=all(n > 0 for n in branch_counts.values()),
        branch_fields=branch_counts, application_allowed=False,
        semantic_status='Provisional agent-reviewed development targets; not human gold, '
                        'final prompt supervision or complete task qualification.')
    write_json(output/'data.json', data)
    manifest['data_sha256'] = sha256(output/'data.json')
    write_json(output/'manifest.json', manifest)
    return manifest


def training_data(data_path, *, current_code=True, fit_code=None):
    """Validate original reviewed supervision, including its frozen implementation."""
    data_path = Path(data_path)
    manifest = read_json(data_path/'manifest.json')
    if manifest.get('task') != 'compare' or sha256(data_path/'data.json') != manifest['data_sha256']:
        raise ValueError('Compare pilot dataset hash differs')
    for reference in manifest['sources'].values():
        if sha256(reference['path']) != reference['sha256']:
            raise ValueError('Compare pilot teacher source hash differs')
    fitter_paths = [path for path in manifest['code_sha256'] if Path(path).name == Path(__file__).name]
    if fit_code is not None and (current_code or len(fitter_paths) != 1):
        raise ValueError('fitter source relocation requires one original Compare fitter in evaluation')
    for path, expected in manifest['code_sha256'].items():
        relocated = fit_code is not None and path == fitter_paths[0]
        verified = Path(fit_code if relocated else path)
        if not verified.is_file() or sha256(verified) != expected:
            raise ValueError('Compare pilot relocated fitter code differs' if relocated else
                             'Compare pilot frozen preparation code differs')
    if current_code and sha256(__file__) not in manifest['code_sha256'].values():
        raise ValueError('Compare pilot preparation code differs')
    data = read_json(data_path/'data.json')
    if data['task'] != 'compare' or tuple(data['labels']) != LABELS:
        raise ValueError('Compare target definition differs')
    collection = read_json(manifest['sources']['collection']['path'])
    expected = reviewed_targets(collection, read_json(manifest['sources']['provenance']['path']))
    if digest(data) != digest(expected):
        raise ValueError('prepared targets differ from reviewed teacher collection')
    return manifest, data, collection


def evaluation_data(experiment, training_path, bootstrap_prompt, teacher_experiment=None, fit_code=None,
                    split_manifest=None):
    """Derive complete native evaluation cases, never trusting copied targets."""
    experiment, training_path, bootstrap_prompt = map(Path, (experiment, training_path, bootstrap_prompt))
    original, fitted, collection = training_data(training_path, current_code=False, fit_code=fit_code)
    if len(original['prompt_sha256']) != 1:
        raise ValueError('evaluation requires one frozen Compare training prompt')
    compare_hash = original['prompt_sha256'][0]
    bootstrap_hash = sha256(bootstrap_prompt)
    protected = {}

    def protect(path, expected=None):
        path = Path(path).resolve()
        actual = sha256(path)
        if expected is not None and actual != expected:
            raise ValueError('evaluation source hash differs: ' + str(path))
        if str(path) in protected and protected[str(path)] != actual:
            raise ValueError('evaluation source changed while preparing: ' + str(path))
        protected[str(path)] = actual
        return path

    fitter_code = None
    if fit_code is not None:
        declared = next(path for path in original['code_sha256'] if Path(path).name == Path(__file__).name)
        fitter_code = dict(declared_path=declared, path=str(protect(fit_code, original['code_sha256'][declared])),
                           sha256=original['code_sha256'][declared])

    populations = None
    if split_manifest is not None:
        roster = read_json(protect(split_manifest))
        if roster.get('schema_version') != 2 or roster.get('tasks') != {'subjects':'ASv6.100'}:
            raise ValueError('expected frozen original ASv6.100 split-roster metadata')
        populations = {}
        for key, role, count in [('train_note_ids','train',1000), ('evaluation_note_ids','validation',100),
                                 ('test_note_ids','test',200)]:
            values = roster.get(key)
            if (not isinstance(values, list) or len(values) != count or
                    any(not isinstance(nid, str) or not nid for nid in values)):
                raise ValueError('original split roster must preserve 1000/100/200 membership')
            for nid in values:
                if nid in populations:
                    raise ValueError('original split rosters overlap or repeat a note')
                populations[nid] = role

    def producer_population(note_id, source_population):
        if populations is None:
            return dict(source_role='train', source_population=source_population)
        role = populations.get(note_id)
        if role in {'validation', 'test'}:
            raise ValueError('original validation/final-test producer is reserved')
        return dict(source_role='original_train' if role == 'train' else 'external_diagnostic',
                    source_population=source_population)

    from ._runner_bootstrap import shared
    native_experiments = shared('experiment')
    plans, reports, corpora, bundles = {}, {}, {}, {}

    def native(directory, *, answers=False):
        directory = Path(directory).resolve()
        if directory not in plans:
            plan, _, _ = native_experiments.load(directory)
            for path, expected in plan['sources'].items():
                protect(path, expected)
            for name, expected in plan['files'].items():
                protect(directory/name, expected)
            protect(directory/'experiment.json')
            protect(Path(plan['run_directory'])/'manifest.json')
            plans[directory] = plan
        if answers and directory not in reports:
            if plans[directory]['prompt']['id'].startswith('Hierarchy-bootstrap-'):
                # Native reporting reads the whole result ledger. Qualify all
                # producer identities before asking it to consume any answers.
                for case in plans[directory]['cases']:
                    evidence = case['evidence']
                    note_id = evidence['local']['note_id']
                    producer_population(note_id, evidence.get('split'))
                    if populations is None:
                        if evidence.get('split', 'train') != 'train':
                            raise ValueError('Bootstrap producer requires original TRAIN population evidence')
                        if 'corpus' in evidence:
                            note = corpus(evidence['corpus']).get(note_id)
                            partition = (note or {}).get('provenance', {}).get('source_split', (note or {}).get('split'))
                            if partition not in {'train', 'learning'}:
                                raise ValueError('Bootstrap producer corpus requires explicit TRAIN/learning population evidence')
                        elif evidence.get('split') != 'train':
                            raise ValueError('Bootstrap producer requires original TRAIN population evidence')
            result = native_experiments.report(directory, include_request_preview=False)
            for row in result['cases']:
                if row.get('receipt'):
                    protect(row['receipt']['results_path'])
            for path in (directory/'reviews.jsonl', directory/'execution-settings.jsonl',
                         directory/'code-upgrades.jsonl', Path(plans[directory]['run_directory'])/'runner-upgrades.jsonl'):
                if path.exists():
                    protect(path)
            reports[directory] = {row['id']: row for row in result['cases']}
        return plans[directory], reports.get(directory)

    def corpus(path):
        path = protect(path)
        if path not in corpora:
            value = read_json(path)
            notes = value.get('notes', [])
            if not notes or len({n['note_id'] for n in notes}) != len(notes):
                raise ValueError('evaluation corpus requires unique original notes')
            corpora[path] = {n['note_id']: n for n in notes}
        return corpora[path]

    def source_bundle(evidence, base):
        reference, producer = evidence['source_bootstrap'], evidence['source_provenance']
        path = protect(base/reference['path'], reference['sha256'])
        producer_path = protect(base/producer['path'], producer['sha256'])
        if path not in bundles:
            bundle, provenance = read_json(path), read_json(producer_path)
            if (bundle.get('schema_version') != 1 or provenance.get('schema_version') != 1
                    or provenance.get('inference_calls') != 0 or len(bundle.get('prompts', {})) != 1
                    or bootstrap_hash not in bundle['prompts']
                    or hashlib.sha256(bundle['prompts'][bootstrap_hash]['text'].encode()).hexdigest() != bootstrap_hash):
                raise ValueError('evaluation requires exact Bootstrap-v96 producer instructions')
            receipts = {(p['experiment'], c['id']): (p['prompt_id'], c['receipt'])
                        for p in provenance['experiments'] for c in p['cases']}
            if len(receipts) != sum(len(p['cases']) for p in provenance['experiments']):
                raise ValueError('duplicate Bootstrap-v96 producer identity')
            saved = {}
            for row in bundle['cases']:
                producer_population(row['evidence']['local']['note_id'], row['evidence'].get('split'))
                if populations is None and row['evidence'].get('split') != 'train':
                    raise ValueError('Bootstrap producer requires original TRAIN population evidence')
                producer_plan, _ = native(row['experiment'])
                planned = next((case for case in producer_plan['cases'] if case['id'] == row['case_id']), None)
                if planned is None or planned['evidence'] != row['evidence']:
                    raise ValueError('Bootstrap collection evidence differs from native producer')
                if (row['prompt_id'] != 'Hierarchy-bootstrap-v96'
                        or producer_plan['prompt']['id'] != 'Hierarchy-bootstrap-v96'
                        or hashlib.sha256(producer_plan['prompt']['text'].encode()).hexdigest() != bootstrap_hash
                        or row['prompt_sha256'] != bootstrap_hash
                        or digest(row['inputs']) != row['input_sha256']
                        or receipts.get((row['experiment'], row['case_id'])) !=
                           (row['prompt_id'], row['receipt'])):
                    raise ValueError('Bootstrap-v96 producer provenance differs')
                saved[(row['experiment'], row['case_id'])] = row
            if len(saved) != len(bundle['cases']):
                raise ValueError('duplicate Bootstrap-v96 meaning identity')
            bundles[path] = saved
        return bundles[path]

    def meaning_proof(reference, value, evidence, base):
        if 'source_bootstrap' in evidence:
            rows = source_bundle(evidence, base)
            key = (reference['experiment'], reference['case_id'])
            saved = rows.get(key)
            if saved is None or saved['receipt'] != reference['receipt']:
                raise ValueError('Bootstrap-v96 meaning receipt differs')
            support = saved['evidence']['local']
            population = producer_population(support['note_id'], saved['evidence'].get('split'))
            if populations is None and saved['evidence'].get('split') != 'train':
                raise ValueError('Bootstrap producer requires original TRAIN population evidence')
            producer_plan, actual_rows = native(reference['experiment'], answers=True)
            actual_row = actual_rows.get(reference['case_id'])
            if (producer_plan['prompt']['id'] != 'Hierarchy-bootstrap-v96'
                    or hashlib.sha256(producer_plan['prompt']['text'].encode()).hexdigest() != bootstrap_hash
                    or actual_row is None or actual_row['status'] != 'valid'
                    or actual_row['evidence'] != saved['evidence']
                    or actual_row.get('receipt') != saved['receipt'] or actual_row['inputs'] != saved['inputs']
                    or (actual_row.get('parsed') or json.loads(actual_row['output'])) != saved['answer']):
                raise ValueError('Bootstrap-v96 collection differs from native producer evidence')
            local = json.loads(saved['inputs']['INPUT_JSON'])['local']
            support = saved['evidence']['local']
            identity = dict(note_id=support['note_id'], pubkey=saved['evidence']['pubkey'], post=local['post'])
            actual = saved['answer']['meaning']
        else:
            plan, _ = native(reference['experiment'])
            if (plan['prompt']['id'] != 'Hierarchy-bootstrap-v96'
                    or hashlib.sha256(plan['prompt']['text'].encode()).hexdigest() != bootstrap_hash):
                raise ValueError('evaluation requires exact Bootstrap-v96 producer instructions')
            planned = next((r for r in plan['cases'] if r['id'] == reference['case']), None)
            if planned is None:
                raise ValueError('Bootstrap producer requires original TRAIN population evidence')
            population = producer_population(planned['evidence']['local']['note_id'],
                                             planned['evidence'].get('split'))
            if populations is None and planned['evidence'].get('split', 'train') != 'train':
                raise ValueError('Bootstrap producer requires original TRAIN population evidence')
            if 'corpus' in planned['evidence']:
                note = corpus(planned['evidence']['corpus']).get(planned['evidence']['local']['note_id'])
                source_population = (note or {}).get('provenance', {}).get('source_split', (note or {}).get('split'))
                population = producer_population(planned['evidence']['local']['note_id'], source_population)
                if populations is None and source_population not in {'train', 'learning'}:
                    raise ValueError('Bootstrap producer corpus requires explicit TRAIN/learning population evidence')
            elif populations is None and planned['evidence'].get('split') != 'train':
                raise ValueError('Bootstrap producer requires original TRAIN population evidence')
            _, rows = native(reference['experiment'], answers=True)
            saved = rows.get(reference['case'])
            if (saved is None or saved['status'] != 'valid'
                    or saved.get('receipt') != reference['receipt']):
                raise ValueError('Bootstrap-v96 meaning receipt differs')
            support = saved['evidence']['local']
            local = json.loads(saved['inputs']['INPUT_JSON'])['local']
            if 'corpus' in saved['evidence']:
                note = corpus(saved['evidence']['corpus']).get(support['note_id'])
                if note is None or local['post'] != note['text'] or not note.get('pubkey'):
                    raise ValueError('Bootstrap producer original note/author/post differs')
                identity = dict(note_id=note['note_id'], pubkey=note['pubkey'], post=note['text'])
            else:
                if ((populations is None and saved['evidence'].get('split') != 'train')
                        or not saved['evidence'].get('pubkey')):
                    raise ValueError('Bootstrap producer requires original TRAIN note/author provenance')
                identity = dict(note_id=support['note_id'], pubkey=saved['evidence']['pubkey'], post=local['post'])
            actual = (saved.get('parsed') or json.loads(saved['output']))['meaning']
        if not isinstance(actual, str) or not actual.strip() or actual != value:
            raise ValueError('evaluation meaning differs from Bootstrap-v96 producer')
        if reference.get('note_id', support['note_id']) != support['note_id']:
            raise ValueError('Bootstrap producer supporting note differs')
        if (reference.get('number', support['number']) != support['number']
                or reference.get('local', support) != support):
            raise ValueError('Bootstrap producer supporting entry differs')
        identity['number'] = support['number']
        identity.update(population)
        return identity

    protect(bootstrap_prompt)
    protect(training_path/'manifest.json')
    protect(training_path/'data.json')
    plan, _ = native(experiment)
    if (plan['prompt']['id'] != 'Hierarchy-compare-v48'
            or hashlib.sha256(plan['prompt']['text'].encode()).hexdigest() != compare_hash):
        raise ValueError('evaluation requires exact Compare-v48 training instructions')
    train_notes, train_authors, train_texts = set(), set(), set()
    original_cases = {(r['experiment'], r['case_id']): r for r in collection['cases']}
    for row in fitted['train']:
        original_case = original_cases[(row['experiment'], row['case_id'])]
        payload = json.loads(original_case['inputs']['INPUT_JSON'])
        original_plan, _ = native(original_case['experiment'])
        base = Path(original_plan['dataset']['path']).parent
        if 'source_bootstrap' not in original_case['evidence']:
            raise ValueError('original training requires frozen Bootstrap-v96 meaning provenance')
        for side in ('local', 'canonical'):
            meaning_proof(original_case['evidence'][side], payload[side]['meaning'], original_case['evidence'], base)
        train_texts.add(' '.join(payload['local']['post'].split()))
        for side in ('local', 'canonical'):
            train_notes.add(row['evidence'][side]['note_id'])
            train_authors.add(row['evidence'][side]['pubkey'])
    teacher_rows = None
    if teacher_experiment is not None:
        teacher_plan, _ = native(teacher_experiment)
        if (teacher_plan['prompt']['id'] != 'Hierarchy-compare-v48'
                or hashlib.sha256(teacher_plan['prompt']['text'].encode()).hexdigest() != compare_hash
                or [(r['id'], r['inputs']) for r in teacher_plan['cases']] !=
                   [(r['id'], r['inputs']) for r in plan['cases']]):
            raise ValueError('teacher diagnostics differ from frozen Compare-v48 cases')
    rows = []
    for case in plan['cases']:
        if 'mechanical' in case:
            raise ValueError('evaluation requires input-only native cases, not mechanical answers')
        payload = json.loads(case['inputs']['INPUT_JSON'])
        evidence, local, canonical = case['evidence'], payload['local'], payload['canonical']
        if evidence.get('split', 'train') != 'train':
            raise ValueError('evaluation must not expose reserved or validation populations')
        if not all(name in canonical for name in ('parents', 'ancestors', 'descendants')):
            raise ValueError('evaluation requires complete canonical branches')
        proofs = []
        base = Path(plan['dataset']['path']).parent
        if 'source_bootstrap' in evidence:
            proofs.append(meaning_proof(evidence['local'], local['meaning'], evidence, base))
            if canonical['parents'] or canonical['ancestors'] or canonical['descendants']:
                raise ValueError('canonical branch meanings require native Bootstrap producer provenance')
            proofs.append(meaning_proof(evidence['canonical'], canonical['meaning'], evidence, base))
        else:
            if 'local_meaning_from' not in evidence or 'canonical_meaning_from' not in evidence:
                raise ValueError('all evaluation meanings require native Bootstrap-v96 producer provenance')
            proofs.append(meaning_proof(evidence['local_meaning_from'], local['meaning'], evidence, base))
            nodes = [canonical, *canonical['ancestors'], *canonical['descendants']]
            by_id = {n['id']: n for n in nodes}
            if len(by_id) != len(nodes) or set(canonical['parents']) - set(by_id):
                raise ValueError('canonical branches contain duplicate or missing nodes')
            references = evidence['canonical_meaning_from']
            if set(by_id) - set(references):
                raise ValueError('every canonical ancestor/descendant requires Bootstrap-v96 provenance')
            for node in nodes:
                proofs.append(meaning_proof(references[node['id']], node['meaning'], evidence, base))
        if (proofs[0]['post'] != local['post'] or proofs[0]['note_id'] != evidence['local']['note_id']
                or proofs[0]['number'] != evidence['local']['number']):
            raise ValueError('evaluation local input differs from original Bootstrap source')
        for identity in proofs:
            if (identity['note_id'] in train_notes or identity['pubkey'] in train_authors
                    or ' '.join(identity['post'].split()) in train_texts):
                raise ValueError('evaluation overlaps original training note/author/content exposure')
        rows.append(dict(experiment=str(experiment.resolve()), case_id=case['id'],
            input_sha256=digest(case['inputs']), state=render(plan['prompt']['text'], case['inputs']),
            input_json=case['inputs']['INPUT_JSON'], evidence=evidence, target=None, teacher=None,
            identity_control=all(proofs[0][key] == proofs[1][key] for key in ('note_id', 'number')),
            producers=[{key:proof[key] for key in ('note_id', 'number', 'source_role', 'source_population')}
                       for proof in proofs]))
    if not rows:
        raise ValueError('evaluation requires nonempty native cases')
    if teacher_experiment is not None:
        _, teacher_rows = native(teacher_experiment, answers=True)
        for row, case in zip(rows, plan['cases']):
            saved = teacher_rows.get(case['id'])
            if (saved is None or saved['status'] != 'valid' or not saved.get('receipt')
                    or saved['inputs'] != case['inputs']):
                raise ValueError('teacher diagnostics require complete valid identical native inputs')
            answer = saved.get('parsed') or json.loads(saved['output'])
            validate_answer(answer, json.loads(row['input_json'])['local']['meaning'])
            row['target'] = answer['relation']
            row['teacher'] = {key:saved.get(key) for key in ('parsed', 'output', 'reviews', 'receipt', 'evidence')}
    data = dict(schema_version=1, task='compare', labels=LABELS, evaluation=rows)
    manifest = dict(schema_version=1, task='compare_evaluation', sources=protected,
        preparation=dict(experiment=str(experiment.resolve()), training_data=str(training_path.resolve()),
            bootstrap_prompt=str(bootstrap_prompt.resolve()),
            teacher_experiment=str(Path(teacher_experiment).resolve()) if teacher_experiment is not None else None,
            fit_code=str(Path(fit_code).resolve()) if fit_code is not None else None,
            split_manifest=str(Path(split_manifest).resolve()) if split_manifest is not None else None),
        fitter_code=fitter_code,
        training_data_sha256=original['data_sha256'], compare_prompt_sha256=compare_hash,
        bootstrap_prompt_sha256=bootstrap_hash, cases=len(rows), teacher_answers=teacher_rows is not None,
        application_allowed=False, semantic_status='Provisional teacher agreement diagnostics; '
        'teacher answers and reviews remain evidence, not gold accuracy or training supervision.')
    return data, manifest


def prepare_evaluation(experiment, training_path, bootstrap_prompt, output, teacher_experiment=None, fit_code=None,
                       split_manifest=None):
    """Freeze input-only native cases and optional provisional teacher diagnostics."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    data, manifest = evaluation_data(experiment, training_path, bootstrap_prompt, teacher_experiment, fit_code, split_manifest)
    write_json(output/'data.json', data)
    manifest.update(data_sha256=sha256(output/'data.json'), code_sha256={str(Path(__file__).resolve()): sha256(__file__)})
    write_json(output/'manifest.json', manifest)
    return manifest


def train(config_path, data_path, output, stage, *, evaluation_path=None, fit_output=None, epochs=None, fit_code=None,
          evaluation_manifest_sha256=None):
    """Fit an encoder or native decision readout using only frozen TRAIN targets."""
    config_path, data_path, output = map(Path, (config_path, data_path, output))
    config = read_json(config_path)
    fields = {'model', 'revision', 'max_length', 'epochs', 'batch_size', 'learning_rate',
              'seed', 'memory_budget_gib', 'reserve_gib'}
    if (fields - set(config) or set(config) - fields - {'local_model_config', 'input_format'}
            or not isinstance(config['model'], str) or not config['model']
            or not isinstance(config['revision'], str) or len(config['revision']) != 40
            or any(c not in '0123456789abcdef' for c in config['revision'])):
        raise ValueError('expected pinned Compare pilot configuration')
    input_format = config.get('input_format', 'full_state')
    if not isinstance(input_format, str) or input_format not in {'full_state', 'input_json'}:
        raise ValueError('expected full_state or input_json student input')
    for name in ('max_length', 'batch_size'):
        if type(config[name]) is not int or config[name] <= 0:
            raise ValueError('expected positive pilot sizes')
    if (not isinstance(config['epochs'], list) or not config['epochs']
            or any(type(n) is not int or n <= 0 for n in config['epochs'])
            or config['epochs'] != sorted(set(config['epochs'])) or type(config['seed']) is not int):
        raise ValueError('expected increasing epoch checkpoints and integer seed')
    for name in ('learning_rate', 'memory_budget_gib', 'reserve_gib'):
        if not isinstance(config[name], (int, float)) or not math.isfinite(config[name]) or config[name] <= 0:
            raise ValueError('expected positive finite pilot settings')
    native_path = native = None
    kind = 'encoder'
    if 'local_model_config' in config:
        if input_format != 'full_state':
            raise ValueError('input_json currently requires the encoder pilot')
        native_path = (config_path.parent / config['local_model_config']).resolve()
        native = read_json(native_path)
        kind = native.get('kind')
        if (kind not in {'causal_lm', 'pointer'} or 'adapter' in native
                or kind == 'causal_lm' and native.get('readout') != 'options'
                or native.get('prompt_layout', 'chat') != 'chat'
                or native.get('quantization') not in {'none', 'nf4'}
                or any(native.get(key) != config[key] for key in
                       ('model', 'revision', 'memory_budget_gib', 'reserve_gib'))
                or native.get('max_input_tokens') != config['max_length']
                or config['batch_size'] != 1
                or set(native['question']['criteria']) != set(LABELS)
                or native['question']['output_field'] != 'relation'):
            raise ValueError('native pilot requires the pinned five-way batch-one readout')
    manifest, data, collection = training_data(data_path, current_code=stage != 'evaluate', fit_code=fit_code)
    fit_report = selected = evaluation_manifest = None
    if stage == 'evaluate':
        fit_output, evaluation_path = map(Path, (fit_output, evaluation_path))
        if (evaluation_manifest_sha256 is not None and
                sha256(evaluation_path/'manifest.json') != evaluation_manifest_sha256):
            raise ValueError('externally bound evaluation manifest differs')
        fit_report = read_json(fit_output/'report.json')
        expected_binding = dict(config_sha256=sha256(config_path), data_sha256=manifest['data_sha256'],
            manifest_sha256=sha256(data_path/'manifest.json'), code_sha256=fit_report['binding']['code_sha256'])
        if native_path:
            expected_binding['local_model_config_sha256'] = sha256(native_path)
        if (fit_report['binding'] != expected_binding or fit_report.get('config') != config
                or expected_binding['code_sha256'] not in manifest['code_sha256'].values()
                or fit_code is not None and expected_binding['code_sha256'] != sha256(fit_code)
                or not fit_report.get('complete') or not fit_report.get('training_finished')
                or fit_report.get('error')):
            raise ValueError('evaluation requires unchanged verified original training and frozen fit code')
        selected = [c for c in fit_report['checkpoints'] if c['epoch'] in epochs]
        if (not epochs or epochs != sorted(set(epochs)) or [c['epoch'] for c in selected] != epochs
                or any(c['path'] != f"checkpoints/epoch-{c['epoch']}" or not c.get('reload_matches')
                       or file_hashes(fit_output/c['path']) != c['hashes']
                       for c in selected)):
            raise ValueError('evaluation checkpoint selection, verification or saved hashes differ')
        evaluation_manifest = read_json(evaluation_path/'manifest.json')
        if (evaluation_manifest.get('task') != 'compare_evaluation'
                or evaluation_manifest['training_data_sha256'] != manifest['data_sha256']
                or [evaluation_manifest['compare_prompt_sha256']] != manifest['prompt_sha256']
                or sha256(evaluation_path/'data.json') != evaluation_manifest['data_sha256']):
            raise ValueError('Compare evaluation data or original training binding differs')
        if evaluation_manifest_sha256 is None:
            for path, expected in {**evaluation_manifest['sources'], **evaluation_manifest['code_sha256']}.items():
                if sha256(path) != expected:
                    raise ValueError('Compare evaluation source or preparation code differs')
        data = read_json(evaluation_path/'data.json')
        if data['task'] != 'compare' or tuple(data['labels']) != LABELS or not data['evaluation']:
            raise ValueError('Compare evaluation target definition differs')
        preparation = evaluation_manifest['preparation']
        if preparation['fit_code'] != (str(Path(fit_code).resolve()) if fit_code is not None else None):
            raise ValueError('evaluation fitter source relocation differs from its preparation')
        if evaluation_manifest_sha256 is None:
            expected_data, expected_manifest = evaluation_data(preparation['experiment'],
                preparation['training_data'], preparation['bootstrap_prompt'], preparation['teacher_experiment'], fit_code,
                preparation['split_manifest'])
            if (digest(data) != digest(expected_data) or
                    any(evaluation_manifest.get(key) != value for key, value in expected_manifest.items())):
                raise ValueError('prepared evaluation differs from native inputs and teacher evidence')
        if output.exists():
            raise FileExistsError(output)
    source_inputs = {(case['experiment'], case['case_id']): case['inputs']['INPUT_JSON']
                     for case in collection['cases']} if input_format == 'input_json' else None
    if stage == 'evaluate' and input_format == 'input_json':
        source_inputs = {(row['experiment'], row['case_id']): row['input_json'] for row in data['evaluation']}
    if stage == 'train' and output.exists():
        raise FileExistsError(output)
    from .distillation_benchmark import admit, available_memory
    admit(config, available_memory())
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise ValueError('Compare pilot requires BF16 CUDA')
    torch.set_num_threads(4)
    torch.manual_seed(config['seed'])
    torch.cuda.set_per_process_memory_fraction(min(1., config['memory_budget_gib']*2**30 /
                                                  torch.cuda.get_device_properties(0).total_memory))
    tokenizer = AutoTokenizer.from_pretrained(config['model'], revision=config['revision'])
    keys = list(native['question']['criteria']) if native else list(LABELS)
    candidate_ids = None
    pointer = None
    if kind == 'pointer':
        upstream = Path(native['upstream_path'])
        if sha256(upstream/'kev/model.py') != native['upstream_model_sha256']:
            raise ValueError('pointer source differs from its frozen binding')
        sys.path.insert(0, str(upstream))
        from kev.model import encode
    elif kind == 'causal_lm':
        from .local_weight_model import choice_prompt
        codes = list(string.ascii_uppercase[:5])
        ids = [tokenizer.encode(code, add_special_tokens=False) for code in codes]
        if (any(len(row) != 1 or row[0] in tokenizer.all_special_ids for row in ids)
                or len({row[0] for row in ids}) != 5):
            raise ValueError('native option codes must be distinct single tokens')
        candidate_ids = [row[0] for row in ids]
    encoded = {}
    for role in (('evaluation',) if stage == 'evaluate' else ('train', 'evaluation')):
        encoded[role] = []
        for row in data[role]:
            state = (source_inputs[(row['experiment'], row['case_id'])]
                     if source_inputs is not None else row['state'])
            if kind == 'pointer':
                question = native['question']
                record = dict(state=state, questions=[dict(instr=question['instructions'],
                    options=[f'{key}: {question["criteria"][key]}' for key in keys], label=0)])
                prepared = encode(tokenizer, record, max_state=config['max_length'],
                                  max_branch=config['max_length'], strict=True)
                ids = dict(input_ids=prepared['ids'], attention_mask=[1]*len(prepared['ids']),
                    position_ids=prepared['pos'], decide_idx=prepared['decide_idx'][0],
                    opt_idx=prepared['opt_idx'][0])
            elif kind == 'causal_lm':
                prompt = choice_prompt(state, native['question'], 'options')
                rendered = tokenizer.apply_chat_template([dict(role='user', content=prompt)],
                    add_generation_prompt=True, enable_thinking=False, tokenize=False) + native.get('answer_prefix', '')
                ids = tokenizer(rendered, add_special_tokens=False, truncation=False)
                if any(tokenizer.encode(rendered+code, add_special_tokens=False) != ids['input_ids']+[token]
                       for code, token in zip(codes, candidate_ids)):
                    raise ValueError('option code tokenization changes at the answer boundary')
            else:
                ids = tokenizer(state, truncation=False, add_special_tokens=True)
            if len(ids['input_ids']) > config['max_length']:
                raise ValueError('complete Compare input exceeds configured maximum; truncation is forbidden')
            encoded[role].append({key: value for key, value in ids.items() if key != 'token_type_ids'})
    binding = dict(config_sha256=sha256(config_path), data_sha256=manifest['data_sha256'],
                   manifest_sha256=sha256(data_path/'manifest.json'), code_sha256=sha256(__file__))
    if native_path:
        binding['local_model_config_sha256'] = sha256(native_path)
    if stage == 'evaluate':
        binding.update(fit_report_sha256=sha256(fit_output/'report.json'), original_fit_binding=fit_report['binding'],
            evaluation_manifest_sha256=sha256(evaluation_path/'manifest.json'))
        if evaluation_manifest_sha256 is not None:
            binding['caller_evaluation_manifest_sha256'] = evaluation_manifest_sha256
    output.mkdir(parents=True, exist_ok=stage == 'verify')
    if stage == 'verify':
        report = read_json(output/'report.json')
        if (report['binding'] != binding or report['complete']
                or report['training_pid'] == os.getpid() or not report.get('training_finished')):
            raise ValueError('verification requires unchanged completed training in a fresh process')
    elif stage == 'evaluate':
        report = dict(schema_version=1, binding=binding, config=config, data=evaluation_manifest,
            fit=str(fit_output.resolve()), evaluation_pid=os.getpid(), complete=False, checkpoints=[],
            architecture=kind, input_format=input_format, updates=0, training_examples_seen=0,
            workload='Inference-only saved Compare checkpoints; provisional teacher agreement, not gold accuracy.',
            evaluation_source_verification=('Native prepared panel validated on Anvil; remote execution bound '
                'to the caller-supplied frozen manifest SHA.' if evaluation_manifest_sha256 is not None else
                'Native input and teacher evidence rederived and source hashes verified at execution.'),
            input_tokens=dict(evaluation=dict(examples=len(encoded['evaluation']),
                total=sum(len(v['input_ids']) for v in encoded['evaluation']),
                maximum=max(len(v['input_ids']) for v in encoded['evaluation']))))
    else:
        report = dict(schema_version=1, binding=binding, config=config, data=manifest,
            training_pid=os.getpid(), complete=False, training_finished=False, updates=0,
            training_examples_seen=0, supervised_class_decisions=0, zero_loss_updates=0, checkpoints=[],
            architecture=kind, method='full' if kind == 'encoder' else 'lora', input_format=input_format,
            workload='Relation-only Compare development learning; provisional teacher agreement, not semantic gold.',
            input_tokens={role: dict(examples=len(values), total=sum(len(v['input_ids']) for v in values),
                                    maximum=max(len(v['input_ids']) for v in values))
                          for role, values in encoded.items()})

    def publish():
        write_json(output/'report.json', report)

    def reserve():
        if available_memory() < config['reserve_gib']*2**30:
            raise ValueError('system memory fell below pilot reserve')

    def batch(role, indexes):
        if kind == 'pointer':
            row = encoded[role][indexes[0]]
            return {key: torch.tensor([row[key]], device='cuda')
                    for key in ('input_ids', 'attention_mask', 'position_ids')}
        result = tokenizer.pad([encoded[role][i] for i in indexes], padding=True, return_tensors='pt')
        return {key: value.to('cuda') for key, value in result.items()}

    def load(checkpoint=None):
        nonlocal pointer
        if kind == 'encoder':
            options = dict(dtype=torch.float32, attn_implementation='sdpa')
            if not checkpoint:
                options.update(revision=config['revision'], num_labels=5, ignore_mismatched_sizes=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                checkpoint or config['model'], **options).to('cuda')
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            return model
        if kind == 'causal_lm':
            from .distillation_run import subject_training_model
            return subject_training_model(dict(native, device='cuda', max_length=config['max_length'],
                efficient_attention=True, lora_target_modules='all-linear', lora_rank=16,
                lora_alpha=32, gradient_checkpointing=True), checkpoint)
        from .local_weight_model import LocalWeights
        from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
        pointer = LocalWeights(native_path)
        base = prepare_model_for_kbit_training(pointer.model, use_gradient_checkpointing=True)
        model = (PeftModel.from_pretrained(base, checkpoint, is_trainable=True) if checkpoint else
            get_peft_model(base, LoraConfig(task_type='FEATURE_EXTRACTION', target_modules='all-linear',
                                          r=16, lora_alpha=32, lora_dropout=0.)))
        if checkpoint:
            saved = torch.load(checkpoint/'head.pt', map_location='cpu', weights_only=True)
            if saved['source_config_sha256'] != sha256(native_path):
                raise ValueError('saved pointer head source binding differs')
            pointer.head.load_state_dict(saved['head'], strict=True)
            pointer.head.temperature = saved['temperature']
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.config.use_cache = False
        pointer.model = model
        return model

    def mode(model, training):
        model.train(training)
        if pointer is not None:
            pointer.head.train(training)

    def scores(model, role, indexes):
        inputs = batch(role, indexes)
        if kind == 'encoder':
            return model(**inputs).logits
        if kind == 'causal_lm':
            values = model(**inputs, use_cache=False, logits_to_keep=1).logits[:, -1, candidate_ids].float()
        else:
            row = encoded[role][indexes[0]]
            h = model(**inputs).last_hidden_state[0].float()
            values = pointer.head(h[row['decide_idx']], h[row['opt_idx']]).unsqueeze(0)
        return values[:, [keys.index(label) for label in LABELS]]

    def evaluate(model):
        mode(model, False)
        decisions, confusion = [], [[0]*5 for _ in LABELS]
        torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            for start_index in range(0, len(data['evaluation']), config['batch_size']):
                reserve()
                indexes = list(range(start_index, min(start_index+config['batch_size'], len(data['evaluation']))))
                logits = scores(model, 'evaluation', indexes)
                if not torch.isfinite(logits).all():
                    raise ValueError('nonfinite Compare classification scores')
                for i, choice in zip(indexes, logits.argmax(-1).cpu().tolist()):
                    row = data['evaluation'][i]
                    if row['target'] is not None:
                        target = LABELS.index(row['target'])
                        confusion[target][choice] += 1
                    decisions.append(dict(case_id=row['case_id'], relation=LABELS[choice], target=row['target'],
                        identity_control=(row['identity_control'] if stage == 'evaluate' else
                            row['evidence'].get('family') == 'same_entry_control'),
                        **(dict(evidence=row['evidence'], teacher=row['teacher']) if stage == 'evaluate' else {})))
        torch.cuda.synchronize()
        seconds = time.perf_counter()-start
        labelled = [d for d in decisions if d['target'] is not None]
        correct = sum(d['relation'] == d['target'] for d in labelled)
        nonself = [d for d in decisions if not d['identity_control']]
        labelled_nonself = [d for d in nonself if d['target'] is not None]
        per_label = {}
        for i, label in enumerate(LABELS):
            support, predicted = sum(confusion[i]), sum(row[i] for row in confusion)
            tp = confusion[i][i]
            per_label[label] = dict(support=support, predicted=predicted,
                recall=tp/support if support else None,
                precision=tp/predicted if predicted else None,
                f1=2*tp/(support+predicted) if support+predicted else None)
        return dict(cases=len(decisions), teacher_cases=len(labelled),
            teacher_agreement=correct/len(labelled) if labelled else None,
            non_identity_cases=len(nonself), non_identity_teacher_cases=len(labelled_nonself),
            non_identity_teacher_agreement=(sum(d['relation'] == d['target'] for d in labelled_nonself)
                /len(labelled_nonself) if labelled_nonself else None),
            per_label=per_label, confusion=confusion, label_order=LABELS, decisions=decisions,
            seconds=seconds, examples_per_second=len(decisions)/seconds)

    publish()
    try:
        if stage == 'evaluate':
            for checkpoint in selected:
                directory = fit_output/checkpoint['path']
                model = load(directory)
                evaluation = evaluate(model)
                report['checkpoints'].append(dict(epoch=checkpoint['epoch'], original_path=checkpoint['path'],
                    hashes=checkpoint['hashes'], evaluation=evaluation,
                    peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated()))
                del model
                pointer = None
                gc.collect()
                torch.cuda.empty_cache()
                publish()
            if sha256(fit_output/'report.json') != binding['fit_report_sha256']:
                raise ValueError('original fit report changed during evaluation')
            for checkpoint in selected:
                if file_hashes(fit_output/checkpoint['path']) != checkpoint['hashes']:
                    raise ValueError('original checkpoint changed during evaluation')
            report['complete'] = True
        elif stage == 'verify':
            for checkpoint in report['checkpoints']:
                directory = output/checkpoint['path']
                if file_hashes(directory) != checkpoint['hashes']:
                    raise ValueError('saved encoder checkpoint hash differs')
                model = load(directory)
                mode(model, False)
                probe = torch.load(directory/'probe.pt', map_location='cpu', weights_only=True)
                with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                    actual = scores(model, 'evaluation', [0]).float().cpu()
                torch.testing.assert_close(actual, probe['logits'], rtol=1e-4, atol=1e-4)
                checkpoint['reload_matches'] = True
                del model, probe, actual
                pointer = None
                gc.collect()
                torch.cuda.empty_cache()
            report.update(verification_pid=os.getpid(), complete=True)
        else:
            start = time.perf_counter()
            model = load()
            limit = getattr(model.config, 'max_position_embeddings', None)
            if limit is not None and config['max_length'] > limit:
                raise ValueError('configured complete input exceeds model position limit')
            parameters = [p for p in model.parameters() if p.requires_grad]
            if pointer is not None:
                parameters += list(pointer.head.parameters())
            report.update(load_seconds=time.perf_counter()-start,
                gradient_checkpointing=model.is_gradient_checkpointing,
                parameters=(model.get_nb_trainable_parameters()[1] if native else
                            sum(p.numel() for p in model.parameters())) + (
                            sum(p.numel() for p in pointer.head.parameters()) if pointer is not None else 0),
                trainable_parameters=sum(p.numel() for p in parameters),
                baseline=evaluate(model))
            majority = Counter(row['target'] for row in data['train']).most_common(1)[0][0]
            report['train_majority_control'] = dict(relation=majority, evaluation_agreement=sum(
                row['target'] == majority for row in data['evaluation'])/len(data['evaluation']))
            publish()
            optimizer = torch.optim.AdamW(parameters, lr=config['learning_rate'])
            started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats()
            for epoch in range(1, max(config['epochs'])+1):
                mode(model, True)
                order = list(range(len(data['train'])))
                random.Random(config['seed']+epoch).shuffle(order)
                losses = []
                for offset in range(0, len(order), config['batch_size']):
                    reserve()
                    indexes = order[offset:offset+config['batch_size']]
                    labels = torch.tensor([LABELS.index(data['train'][i]['target']) for i in indexes], device='cuda')
                    optimizer.zero_grad(set_to_none=True)
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        loss = torch.nn.functional.cross_entropy(scores(model, 'train', indexes).float(), labels)
                    loss.backward()
                    norm = torch.nn.utils.clip_grad_norm_(parameters, 1.)
                    loss_value, norm_value = loss.item(), norm.item()
                    if (not math.isfinite(loss_value) or not math.isfinite(norm_value)
                            or norm_value <= 0 and loss_value != 0):
                        report['failed_update'] = dict(epoch=epoch,
                            case_ids=[data['train'][i]['case_id'] for i in indexes],
                            loss=loss_value if math.isfinite(loss_value) else str(loss_value),
                            gradient_norm=norm_value if math.isfinite(norm_value) else str(norm_value))
                        raise ValueError('nonfinite loss/gradient or zero gradient with nonzero loss')
                    if norm_value == 0:
                        report['zero_loss_updates'] += 1
                    optimizer.step()
                    losses.append(loss_value)
                    report['updates'] += 1
                    report['training_examples_seen'] += len(indexes)
                    report['supervised_class_decisions'] += len(indexes)
                if epoch in config['epochs']:
                    evaluation = evaluate(model)
                    directory = output/'checkpoints'/f'epoch-{epoch}'
                    model.save_pretrained(directory)
                    tokenizer.save_pretrained(directory)
                    if pointer is not None:
                        torch.save(dict(head=pointer.head.state_dict(), temperature=pointer.head.temperature,
                            source_config_sha256=sha256(native_path)), directory/'head.pt')
                    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
                        probe = scores(model, 'evaluation', [0]).float().cpu()
                    torch.save(dict(logits=probe), directory/'probe.pt')
                    report['checkpoints'].append(dict(epoch=epoch, path=str(directory.relative_to(output)),
                        hashes=file_hashes(directory), updates=report['updates'],
                        training_examples_seen=report['training_examples_seen'], mean_epoch_loss=sum(losses)/len(losses),
                        elapsed_training_seconds=time.perf_counter()-started,
                        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(), evaluation=evaluation,
                        reload_matches=False))
                    publish()
            report['training_finished'] = True
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        publish()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('prepare', help='prepare native reviewed targets; no inference')
    for name in ('collection', 'provenance', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command = commands.add_parser('prepare-evaluation', help='freeze native input-only cases and optional provisional teacher diagnostics')
    for name in ('experiment', 'training-data', 'bootstrap-prompt', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command.add_argument('--teacher-experiment', type=Path)
    command.add_argument('--fit-code', type=Path, help='read-only copy of the original fitter with its exact frozen SHA')
    command.add_argument('--split-manifest', type=Path, help='original 1000/100/200 ASv6.100 roster for external diagnostics')
    command = commands.add_parser('train', help='fit an encoder or native decision readout and verify saved weights')
    for name in ('config', 'data', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command.add_argument('--stage', choices=('train', 'verify'), required=True)
    command = commands.add_parser('evaluate', help='evaluate verified saved checkpoints without fitting or gradients')
    for name in ('config', 'training-data', 'fit', 'data', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command.add_argument('--epochs', required=True, type=int, nargs='+')
    command.add_argument('--fit-code', type=Path, help='same verified original fitter copy used in preparation')
    command.add_argument('--evaluation-manifest-sha256', help='externally frozen Anvil panel SHA for portable prepared-input execution')
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.collection, args.provenance, args.output)
        print(json.dumps({key: result[key] for key in ('counts', 'excluded', 'all_five_labels', 'canonical_branches')}))
    elif args.command == 'prepare-evaluation':
        result = prepare_evaluation(args.experiment, args.training_data, args.bootstrap_prompt,
                                    args.output, args.teacher_experiment, args.fit_code, args.split_manifest)
        print(json.dumps({key: result[key] for key in ('cases', 'teacher_answers', 'semantic_status')}))
    elif args.command == 'evaluate':
        result = train(args.config, args.training_data, args.output, 'evaluate',
                       evaluation_path=args.data, fit_output=args.fit, epochs=args.epochs, fit_code=args.fit_code,
                       evaluation_manifest_sha256=args.evaluation_manifest_sha256)
        print(json.dumps(dict(complete=result['complete'], checkpoints=len(result['checkpoints']), updates=result['updates'])))
    else:
        result = train(args.config, args.data, args.output, args.stage)
        print(json.dumps({key: result[key] for key in ('complete', 'updates', 'training_examples_seen')}))


if __name__ == '__main__':
    main()
