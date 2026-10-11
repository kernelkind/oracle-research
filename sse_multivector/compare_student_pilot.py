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


def train(config_path, data_path, output, stage):
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
    manifest = read_json(data_path/'manifest.json')
    if manifest.get('task') != 'compare' or sha256(data_path/'data.json') != manifest['data_sha256']:
        raise ValueError('Compare pilot dataset hash differs')
    for reference in manifest['sources'].values():
        if sha256(reference['path']) != reference['sha256']:
            raise ValueError('Compare pilot teacher source hash differs')
    if sha256(__file__) not in manifest['code_sha256'].values():
        raise ValueError('Compare pilot preparation code differs')
    data = read_json(data_path/'data.json')
    if data['task'] != 'compare' or tuple(data['labels']) != LABELS:
        raise ValueError('Compare target definition differs')
    collection = read_json(manifest['sources']['collection']['path'])
    expected = reviewed_targets(collection, read_json(manifest['sources']['provenance']['path']))
    if digest(data) != digest(expected):
        raise ValueError('prepared targets differ from reviewed teacher collection')
    source_inputs = {(case['experiment'], case['case_id']): case['inputs']['INPUT_JSON']
                     for case in collection['cases']} if input_format == 'input_json' else None
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
    for role in ('train', 'evaluation'):
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
    output.mkdir(parents=True, exist_ok=stage == 'verify')
    if stage == 'verify':
        report = read_json(output/'report.json')
        if (report['binding'] != binding or report['complete']
                or report['training_pid'] == os.getpid() or not report.get('training_finished')):
            raise ValueError('verification requires unchanged completed training in a fresh process')
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
                    target = LABELS.index(row['target'])
                    confusion[target][choice] += 1
                    decisions.append(dict(case_id=row['case_id'], relation=LABELS[choice], target=row['target'],
                                          identity_control=row['evidence']['family'] == 'same_entry_control'))
        torch.cuda.synchronize()
        seconds = time.perf_counter()-start
        correct = sum(d['relation'] == d['target'] for d in decisions)
        nonself = [d for d in decisions if not d['identity_control']]
        per_label = {}
        for i, label in enumerate(LABELS):
            support, predicted = sum(confusion[i]), sum(row[i] for row in confusion)
            tp = confusion[i][i]
            per_label[label] = dict(support=support, predicted=predicted,
                recall=tp/support if support else None,
                precision=tp/predicted if predicted else None,
                f1=2*tp/(support+predicted) if support+predicted else None)
        return dict(cases=len(decisions), teacher_agreement=correct/len(decisions),
            non_identity_cases=len(nonself), non_identity_teacher_agreement=(
                sum(d['relation'] == d['target'] for d in nonself)/len(nonself) if nonself else None),
            per_label=per_label, confusion=confusion, label_order=LABELS, decisions=decisions,
            seconds=seconds, examples_per_second=len(decisions)/seconds)

    publish()
    try:
        if stage == 'verify':
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
    command = commands.add_parser('train', help='fit an encoder or native decision readout and verify saved weights')
    for name in ('config', 'data', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command.add_argument('--stage', choices=('train', 'verify'), required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.collection, args.provenance, args.output)
        print(json.dumps({key: result[key] for key in ('counts', 'excluded', 'all_five_labels', 'canonical_branches')}))
    else:
        result = train(args.config, args.data, args.output, args.stage)
        print(json.dumps({key: result[key] for key in ('complete', 'updates', 'training_examples_seen')}))


if __name__ == '__main__':
    main()
