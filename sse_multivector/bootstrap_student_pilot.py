"""Source-bound meaning-only Bootstrap development targets and local LoRA fits.

Teacher answers and native reviews stay intact. These pilots use original TRAIN
posts with separate development roles; neither prompt freeze nor final student
qualification follows from teacher-forced loss or checkpoint integrity.
"""
import argparse
from collections import Counter
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

from .bootstrap_student_inputs import validate_answer
from .compare_student_inputs import accepted
from .distillation_run import (encode_example, file_hashes, read_json, sha256,
                               subject_training_model, write_json)
from .experiment_inputs import digest, render


STUDENT_CONTRACT = '\n\nStudent response contract (Bootstrap meaning-only pilot):\n' \
    'Apply the semantic rules above. Return a JSON object with only the `meaning` field. ' \
    'Its value must be the standalone meaning string, or null when the meaning cannot be ' \
    'established. This response contract replaces the response fields above. ' \
    'Do not output ambiguities, resolutions, evidence, Markdown fences or additional text.\n'


def prepare_prompt(teacher_prompt, output):
    """Preserve teacher instructions while selecting the meaning-only response."""
    teacher_prompt, output = map(Path, (teacher_prompt, output))
    source = teacher_prompt.read_bytes()
    text = source.decode('utf-8')
    if not text.strip():
        raise ValueError('Bootstrap teacher prompt must be nonempty')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        stream.write(text + STUDENT_CONTRACT)
    return dict(teacher_prompt=str(teacher_prompt.resolve()),
        teacher_prompt_sha256=hashlib.sha256(source).hexdigest(),
        student_prompt=str(output.resolve()), student_prompt_sha256=sha256(output),
        inference_calls=0)


def reviewed_targets(bundle, producers):
    if (bundle.get('schema_version') != 1 or producers.get('schema_version') != 1
            or producers.get('inference_calls') != 0 or len(bundle['prompts']) != 1):
        raise ValueError('expected native offline Bootstrap collection with one prompt snapshot')
    receipts = {}
    for producer in producers['experiments']:
        for case in producer['cases']:
            key = (producer['experiment'], case['id'])
            if key in receipts:
                raise ValueError('duplicate native producer identity')
            receipts[key] = (producer['prompt_id'], case['receipt'])
    data = dict(schema_version=1, task='bootstrap', output_fields=['meaning'],
                train=[], evaluation=[], excluded=[])
    identities, groups = set(), {name: {} for name in ('note', 'author', 'post')}
    for case in bundle['cases']:
        key = (case['experiment'], case['case_id'])
        if key in identities:
            raise ValueError('duplicate Bootstrap target identity')
        identities.add(key)
        if receipts.get(key) != (case['prompt_id'], case['receipt']):
            raise ValueError('Bootstrap collection differs from native producer provenance')
        prompt = bundle['prompts'][case['prompt_sha256']]
        if (hashlib.sha256(prompt['text'].encode()).hexdigest() != case['prompt_sha256']
                or case['prompt_id'] not in prompt['prompt_ids']
                or digest(case['inputs']) != case['input_sha256']):
            raise ValueError('Bootstrap prompt or input binding differs')
        local = json.loads(case['inputs']['INPUT_JSON'])['local']
        validate_answer(case['answer'], local['post'])
        evidence, role = case['evidence'], case['evidence'].get('role')
        if evidence.get('split') != 'train' or role not in {'train', 'evaluation'}:
            raise ValueError('Bootstrap cases must retain original TRAIN and development roles')
        for value, name in ((evidence['local']['note_id'], 'note'), (evidence['pubkey'], 'author'),
                            (' '.join(local['post'].split()), 'post')):
            if value in groups[name] and groups[name][value] != role:
                raise ValueError('Bootstrap pilot crosses a note/author/content group')
            groups[name][value] = role
        identity = dict(experiment=case['experiment'], case_id=case['case_id'],
                        input_sha256=case['input_sha256'], receipt=case['receipt'])
        if not accepted(case['reviews']):
            data['excluded'].append(dict(**identity, role=role,
                reason='Current review is missing, rejected or unresolved.'))
            continue
        data[role].append(dict(**identity, prompt=[dict(role='user', content=render(
            prompt['text'] + STUDENT_CONTRACT, case['inputs']))], completion=[dict(
                role='assistant', content=json.dumps(dict(meaning=case['answer']['meaning']),
                                                     ensure_ascii=False))],
            evidence=evidence, reviews=case['reviews'], prompt_sha256=case['prompt_sha256']))
    if not data['train'] or not data['evaluation']:
        raise ValueError('reviewed Bootstrap targets must leave both development roles nonempty')
    return data


def prepare(collection, provenance, output):
    collection, provenance, output = map(Path, (collection, provenance, output))
    if output.exists():
        raise FileExistsError(output)
    bundle = read_json(collection)
    data = reviewed_targets(bundle, read_json(provenance))
    counts = {role: dict(Counter('null' if json.loads(r['completion'][0]['content'])['meaning']
                        is None else 'meaning' for r in data[role])) for role in ('train', 'evaluation')}
    manifest = dict(schema_version=1, task='bootstrap', output_fields=['meaning'],
        sources={name: dict(path=str(p.resolve()), sha256=sha256(p))
                 for name, p in [('collection', collection), ('provenance', provenance)]},
        code_sha256={str(Path(__file__).resolve()): sha256(__file__)},
        teacher_prompt_sha256=next(iter(bundle['prompts'])), counts=counts,
        excluded=len(data['excluded']), application_allowed=False,
        semantic_status='Provisional agent-reviewed development targets; not human gold '
                        'or frozen-prompt supervision. Generation requires separate semantic review.')
    write_json(output/'data.json', data)
    # This exact template also lets the native experiment runner evaluate a
    # checkpoint on preserved teacher inputs with the student response schema.
    (output/'student-prompt.txt').write_text(next(iter(bundle['prompts'].values()))['text'] + STUDENT_CONTRACT)
    manifest.update(data_sha256=sha256(output/'data.json'),
                    student_prompt_sha256=sha256(output/'student-prompt.txt'))
    write_json(output/'manifest.json', manifest)
    return manifest


def train(config_path, data_path, output, stage):
    config_path, data_path, output = map(Path, (config_path, data_path, output))
    config = read_json(config_path)
    fields = {'model', 'revision', 'quantization', 'max_length', 'epochs', 'batch_size',
              'learning_rate', 'seed', 'memory_budget_gib', 'reserve_gib'}
    if (set(config) != fields or not isinstance(config['model'], str) or not config['model']
            or not isinstance(config['revision'], str) or len(config['revision']) != 40
            or any(c not in '0123456789abcdef' for c in config['revision'])
            or config['quantization'] not in {'none', 'nf4'}
            or type(config['max_length']) is not int or config['max_length'] <= 0
            or type(config['seed']) is not int or type(config['batch_size']) is not int
            or config['batch_size'] != 1):
        raise ValueError('expected pinned batch-one Bootstrap pilot configuration')
    if (not isinstance(config['epochs'], list) or not config['epochs']
            or any(type(n) is not int or n <= 0 for n in config['epochs'])
            or config['epochs'] != sorted(set(config['epochs']))):
        raise ValueError('expected increasing positive checkpoint epochs')
    for name in ('learning_rate', 'memory_budget_gib', 'reserve_gib'):
        if type(config[name]) not in (int, float) or not math.isfinite(config[name]) or config[name] <= 0:
            raise ValueError('expected positive finite pilot rates and memory limits')
    manifest = read_json(data_path/'manifest.json')
    if (manifest.get('task') != 'bootstrap' or manifest.get('output_fields') != ['meaning']
            or sha256(data_path/'data.json') != manifest['data_sha256']
            or sha256(data_path/'student-prompt.txt') != manifest['student_prompt_sha256']):
        raise ValueError('Bootstrap data or student prompt binding differs')
    for ref in manifest['sources'].values():
        if sha256(ref['path']) != ref['sha256']:
            raise ValueError('Bootstrap source hash differs')
    for path, checksum in manifest['code_sha256'].items():
        if sha256(path) != checksum:
            raise ValueError('Bootstrap preparation code differs')
    data = read_json(data_path/'data.json')
    bundle = read_json(manifest['sources']['collection']['path'])
    expected = reviewed_targets(bundle, read_json(manifest['sources']['provenance']['path']))
    if digest(data) != digest(expected):
        raise ValueError('prepared targets differ from reviewed teacher collection')
    template = next(iter(bundle['prompts'].values()))['text'] + STUDENT_CONTRACT
    if (data_path/'student-prompt.txt').read_text() != template:
        raise ValueError('prepared student prompt differs from teacher snapshot and output contract')
    if stage == 'train' and output.exists():
        raise FileExistsError(output)
    from .distillation_benchmark import admit, available_memory
    admit(config, available_memory())
    import torch
    from transformers import AutoTokenizer
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise ValueError('Bootstrap pilot requires BF16 CUDA')
    torch.set_num_threads(4)
    torch.manual_seed(config['seed'])
    torch.cuda.set_per_process_memory_fraction(min(1., config['memory_budget_gib']*2**30 /
                                                  torch.cuda.get_device_properties(0).total_memory))
    tokenizer = AutoTokenizer.from_pretrained(config['model'], revision=config['revision'])
    encoded = {role: [encode_example(tokenizer, row, config['max_length']) for row in data[role]]
               for role in ('train', 'evaluation')}
    model_config = dict(config, device='cuda', efficient_attention=True,
        lora_target_modules='all-linear', lora_rank=16, lora_alpha=32, gradient_checkpointing=True)
    binding = dict(config_sha256=sha256(config_path), manifest_sha256=sha256(data_path/'manifest.json'),
        code_sha256={str(Path(__file__).resolve()): sha256(__file__),
                     str(Path(__file__).with_name('distillation_run.py').resolve()):
                     sha256(Path(__file__).with_name('distillation_run.py'))})
    if stage == 'verify':
        report = read_json(output/'report.json')
        if (report['binding'] != binding or not report['training_finished'] or report['complete']
                or report['training_pid'] == os.getpid()):
            raise ValueError('verification requires unchanged completed training in a fresh process')
    else:
        report = dict(schema_version=1, binding=binding, config=config, data=manifest,
            training_pid=os.getpid(), training_finished=False, complete=False, updates=0,
            training_examples_seen=0, supervised_tokens=0, checkpoints=[], optimizer_step_seconds=0.,
            workload='Meaning-only Bootstrap development learning; teacher-forced loss is not semantic quality.',
            tokens={role: dict(examples=len(rows), total=sum(len(r['input_ids']) for r in rows),
                maximum=max(len(r['input_ids']) for r in rows),
                supervised=sum(sum(v != -100 for v in r['labels']) for r in rows))
                for role, rows in encoded.items()})

    def publish():
        write_json(output/'report.json', report)

    def reserve():
        if available_memory() < config['reserve_gib']*2**30:
            raise ValueError('system memory fell below Bootstrap pilot reserve')

    def forward(model, row):
        inputs = {key: torch.tensor([value], device='cuda') for key, value in row.items()}
        first = next(i for i, v in enumerate(row['labels']) if v != -100)
        positions = torch.arange(first-1, len(row['input_ids'])-1, device='cuda')
        return model(**inputs, use_cache=False, logits_to_keep=positions,
                     shift_labels=inputs['labels'][:, first:])

    def evaluate(model):
        model.eval()
        cases, total_loss, total_tokens = [], 0., 0
        torch.cuda.synchronize()
        start = time.perf_counter()
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            for original, row in zip(data['evaluation'], encoded['evaluation']):
                reserve()
                loss = forward(model, row).loss.item()
                if not math.isfinite(loss):
                    raise ValueError('nonfinite Bootstrap evaluation loss')
                count = sum(v != -100 for v in row['labels'])
                cases.append(dict(case_id=original['case_id'], mean_token_loss=loss, tokens=count))
                total_loss += loss*count
                total_tokens += count
        torch.cuda.synchronize()
        return dict(cases=cases, mean_token_loss=total_loss/total_tokens,
                    supervised_tokens=total_tokens, seconds=time.perf_counter()-start)

    def probe(model):
        model.eval()
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
            values = forward(model, encoded['evaluation'][0])
        return dict(logits=values.logits[:, :, :32].float().cpu(), loss=values.loss.float().cpu())

    publish()
    try:
        if stage == 'verify':
            for checkpoint in report['checkpoints']:
                directory = output/checkpoint['path']
                if file_hashes(directory) != checkpoint['hashes']:
                    raise ValueError('saved Bootstrap checkpoint hash differs')
                reserve()
                model = subject_training_model(model_config, directory)
                saved, actual = torch.load(directory/'probe.pt', weights_only=True), probe(model)
                for key in saved:
                    torch.testing.assert_close(actual[key], saved[key], rtol=1e-4, atol=1e-4)
                checkpoint['reload_matches'] = True
                del model, saved, actual
                gc.collect()
                torch.cuda.empty_cache()
                publish()
            report.update(verification_pid=os.getpid(), complete=True)
        else:
            start = time.perf_counter()
            model = subject_training_model(model_config)
            parameters = [p for p in model.parameters() if p.requires_grad]
            report.update(load_seconds=time.perf_counter()-start,
                parameters=model.get_nb_trainable_parameters()[1],
                trainable_parameters=sum(p.numel() for p in parameters), baseline=evaluate(model))
            optimizer = torch.optim.AdamW(parameters, lr=config['learning_rate'])
            started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats()
            publish()
            for epoch in range(1, max(config['epochs'])+1):
                model.train()
                order = list(range(len(encoded['train'])))
                random.Random(config['seed']+epoch).shuffle(order)
                losses = []
                for index in order:
                    reserve()
                    torch.cuda.synchronize()
                    start = time.perf_counter()
                    optimizer.zero_grad(set_to_none=True)
                    row = encoded['train'][index]
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        loss = forward(model, row).loss
                    loss.backward()
                    norm = torch.nn.utils.clip_grad_norm_(parameters, 1.)
                    if not torch.isfinite(loss) or not torch.isfinite(norm) or norm <= 0:
                        raise ValueError('nonfinite loss/gradient or zero Bootstrap pilot gradient')
                    optimizer.step()
                    torch.cuda.synchronize()
                    report['optimizer_step_seconds'] += time.perf_counter()-start
                    losses.append(loss.item())
                    report['updates'] += 1
                    report['training_examples_seen'] += 1
                    report['supervised_tokens'] += sum(v != -100 for v in row['labels'])
                    if report['updates'] % 10 == 0:
                        publish()
                if epoch in config['epochs']:
                    optimizer.zero_grad(set_to_none=True)
                    evaluation = evaluate(model)
                    directory = output/'checkpoints'/f'epoch-{epoch}'
                    model.save_pretrained(directory)
                    tokenizer.save_pretrained(directory)
                    torch.save(probe(model), directory/'probe.pt')
                    report['checkpoints'].append(dict(epoch=epoch, path=str(directory.relative_to(output)),
                        hashes=file_hashes(directory), updates=report['updates'],
                        mean_epoch_loss=sum(losses)/len(losses), evaluation=evaluation,
                        optimizer_step_seconds=report['optimizer_step_seconds'],
                        elapsed_training_seconds=time.perf_counter()-started,
                        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(), reload_matches=False))
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
    command = commands.add_parser('prepare', help='prepare native reviewed meaning targets; no inference')
    for name in ('collection', 'provenance', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command = commands.add_parser('prepare-prompt', help='derive a meaning-only generation prompt; no targets or inference')
    for name in ('teacher-prompt', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command = commands.add_parser('train', help='fit causal adapters and separately verify saved weights')
    for name in ('config', 'data', 'output'):
        command.add_argument('--'+name, required=True, type=Path)
    command.add_argument('--stage', choices=('train', 'verify'), required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        result = prepare(args.collection, args.provenance, args.output)
    elif args.command == 'prepare-prompt':
        result = prepare_prompt(args.teacher_prompt, args.output)
    else:
        result = train(args.config, args.data, args.output, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
