"""TRUE01: independently decide directed category containment with frozen TRUE NLI."""
import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time

from hierarcaps_category_probe import prepare_inputs
from hierarcaps_mask_probe import save_json, sha256


MODEL_ID = 'google/t5_xxl_true_nli_mixture'
REVISION = 'aa6cfe1dd4257853bfdd772992045f41bfc14988'
FIXTURE_HASH = 'd3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35'
CASES = ('F02', 'F06', 'S03', 'S05', 'E02', 'E06', 'P01', 'P03', 'R02', 'R03')
EQUIVALENT = (('F02', 'broader'), ('S05', 'narrower'), ('E02', 'alternative'),
              ('P03', 'broader'), ('R03', 'alternative'))
WEIGHT_HASHES = (
    'dd1fccd740a717f82578a8fec4912772d36e0d3951ff6c57c0ea1ce76a018bb1',
    'b6d133eade2bafc61c0ca5cc323044ae6d008b38096e97928506f0a49613905e',
    '1705a1c6a4f5913cc681b48aa3f3e388bceb5a037cc966b6319d011be76641be',
    'f68e2b1d98819f84b505355cd3e362b974356f98b28e4ce57c01047b590aece7',
    '1f21dc75d2ad64c139b11310ae4b784659f464c59a24752e0515f6ecf3f7ddd3')


def make_pairs(fixture):
    prepare_inputs(fixture)  # Reuse the frozen fixture's original strict validation.
    cases = {case['id']: case for case in fixture['cases']}
    if not set(CASES) <= cases.keys():
        raise ValueError('missing selected case')
    pairs = []
    for case_id in CASES:
        case = cases[case_id]
        for index, wording in enumerate(case['wordings'], 1):
            for kind, a, b, expected in (
                    ('forward', 'broader', 'narrower', True),
                    ('reverse', 'narrower', 'broader', False),
                    ('alternative', 'alternative', 'narrower', False),
                    ('alternative-reverse', 'narrower', 'alternative', False)):
                pairs.append(dict(id=f'{case_id}-w{index}-{kind}', case=case_id,
                                  domain=case['domain'], kind=kind, wording=index,
                                  a=wording[a], b=wording[b], expected=expected))
    for case_id, role in EQUIVALENT:
        case = cases[case_id]
        for i, j in ((0, 1), (1, 0)):
            pairs.append(dict(id=f'{case_id}-equivalent-{i+1}-{j+1}', case=case_id,
                              domain=case['domain'], kind='equivalent', role=role,
                              a=case['wordings'][i][role], b=case['wordings'][j][role],
                              expected=True))
    return pairs


def model_input(pair, form):
    if form not in ('topic', 'bare'):
        raise ValueError('unknown input format')
    def render(category):
        return 'This text is about ' + category + '.' if form == 'topic' else category
    # A subsumes B iff membership in B entails membership in A. Never reverse this.
    return 'premise: ' + render(pair['b']) + ' hypothesis: ' + render(pair['a'])


def score_logits(values, zero_id, one_id):
    """First-token diagnostics only: IDs need not encode complete class strings."""
    if (not values or not all(math.isfinite(v) for v in values)
            or zero_id == one_id or not 0 <= zero_id < len(values)
            or not 0 <= one_id < len(values)):
        raise ValueError('finite vocabulary logits and distinct valid class IDs required')
    zero, one = values[zero_id], values[one_id]
    largest = max(values)
    total = math.fsum(math.exp(value - largest) for value in values)
    p_zero, p_one = (math.exp(value - largest) / total for value in (zero, one))
    pair_max = max(zero, one)
    normalized = math.exp(one - pair_max) / (math.exp(zero - pair_max) + math.exp(one - pair_max))
    argmax = max(range(len(values)), key=values.__getitem__)
    predicted = {zero_id: False, one_id: True}.get(argmax)
    return dict(logit_0=zero, logit_1=one, probability_0=p_zero, probability_1=p_one,
                entailment_score=normalized, label_probability_mass=p_zero+p_one,
                binary_label=int(one > zero), argmax_token_id=argmax, predicted=predicted)


def score_generation(values, text, generated_ids, label_ids, eos_id=1):
    prefix = score_logits(values, label_ids['0'][0], label_ids['1'][0])
    if len(generated_ids) < 2 or generated_ids[1] != prefix['argmax_token_id']:
        raise ValueError('native generation disagrees with raw first-token argmax')
    terminated = eos_id in generated_ids[1:]
    # Complete native output decides the class. In TRUE, '0' is [3, 632],
    # so its initial whitespace token must never itself count as a No answer.
    predicted = {'0': False, '1': True}.get(text) if terminated else None
    return dict(generated_text=text, generated_token_ids=generated_ids,
                eos_terminated=terminated, predicted=predicted,
                entailment_score=prefix['probability_1'],
                logit_0_first_token=prefix['logit_0'], logit_1_first_token=prefix['logit_1'],
                probability_0_first_token=prefix['probability_0'],
                first_token_binary_score=prefix['entailment_score'],
                first_token_binary_label=prefix['binary_label'],
                label_prefix_probability_mass=prefix['label_probability_mass'],
                argmax_token_id=prefix['argmax_token_id'])


def summarize(rows):
    def counts(items):
        return dict(total=len(items), correct=sum(r['predicted'] == r['expected'] for r in items),
                    positive=sum(r['expected'] for r in items),
                    negative=sum(not r['expected'] for r in items),
                    false_positive=sum(r['predicted'] is True and not r['expected'] for r in items),
                    false_negative=sum(r['predicted'] is False and r['expected'] for r in items),
                    unresolved=sum(r['predicted'] is None for r in items))
    result = {}
    for form in sorted({r['format'] for r in rows}):
        items = [r for r in rows if r['format'] == form]
        result[form] = dict(overall=counts(items))
        for field in ('domain', 'kind'):
            result[form][field] = {value: counts([r for r in items if r[field] == value])
                                   for value in sorted({r[field] for r in items})}
    return result


def render_decisions(rows):
    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ')
    def answer(row):
        label = 'Unresolved' if row['predicted'] is None else ('Yes' if row['predicted'] else 'No')
        return f"{label} ({row['entailment_score']:.6f})"
    by_id = {}
    for row in rows:
        by_id.setdefault(row['id'], {})[row['format']] = row
    lines = ['# TRUE01 — Every category decision', '',
        'Each row asks **A contains B?** In other words: does belonging to B warrant belonging to A?', '',
        'Expected answers were recorded before inference. Scores in parentheses are the probability of '
        'the first output token being `1`, not cosine, complete-label probability, or calibrated '
        'category confidence. Answers come from complete native greedy output with EOS, not a score cutoff. '
        '“Topic sentence” uses `This text is about …`; “Bare text” uses the unchanged category strings. '
        'Both are inside the released `premise: … hypothesis: …` format, with B as premise.', '',
        '| ID | A | B | Expected | Topic sentence | Bare text |',
        '|---|---|---|---|---|---|']
    for key, formats in by_id.items():
        topic, bare = formats['topic'], formats['bare']
        lines.append('| ' + ' | '.join(map(cell, (key, topic['a'], topic['b'],
            'Yes' if topic['expected'] else 'No', answer(topic), answer(bare)))) + ' |')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('fixture', 'output', 'snapshot'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--batch-size', type=int, default=4, choices=(1, 2, 4))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; earlier or interrupted runs must be preserved')
    started = time.monotonic()
    if sha256(args.fixture) != FIXTURE_HASH:
        raise ValueError('frozen fixture bytes changed')
    fixture = json.loads(args.fixture.read_text())
    pairs = make_pairs(fixture)
    inputs = [dict(**pair, format=form, model_input=model_input(pair, form))
              for form in ('topic', 'bare') for pair in pairs]
    snapshot = args.snapshot.resolve(strict=True)
    if (snapshot.name != REVISION or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('exact pinned model snapshot required')
    args.output.mkdir(parents=True, exist_ok=False)
    save_json(args.output / 'inputs.json', inputs)
    with (args.output / 'fixture.json').open('xb') as stream:
        stream.write(args.fixture.read_bytes())
    save_json(args.output / 'started.json', dict(model_id=MODEL_ID, revision=REVISION,
        fixture_sha256=sha256(args.fixture), inputs_sha256=sha256(args.output / 'inputs.json'),
        runner_sha256=sha256(Path(__file__)), primary_format='topic', secondary_format='bare'))
    print(f'Frozen {len(inputs)} inputs before inference. Hashing the pinned checkpoint.', flush=True)
    files = {}
    for path in sorted(snapshot.iterdir()):
        if path.is_file():
            files[path.name] = sha256(path)
    for index, expected in enumerate(WEIGHT_HASHES, 1):
        if files.get(f'pytorch_model-{index:05d}-of-00005.bin') != expected:
            raise ValueError('weight shard differs from the release manifest')
    save_json(args.output / 'model-files.json', files)

    import numpy as np
    import torch
    from transformers import AutoTokenizer, T5ForConditionalGeneration
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    label_ids = {label: tokenizer.encode(label, add_special_tokens=False) for label in ('0', '1')}
    if label_ids != {'0': [3, 632], '1': [209]}:
        raise ValueError('label tokenization differs from the verified pinned release')
    print('Loading TRUE offline: CPU float32, four threads, no training or quantization.', flush=True)
    model, loading = T5ForConditionalGeneration.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, weights_only=True,
        use_safetensors=False, output_loading_info=True, dtype=torch.float32)
    for key in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs'):
        if loading.get(key):
            raise ValueError('checkpoint loading is incomplete: ' + key + ': ' + str(loading[key]))
    model.eval()
    if {p.dtype for p in model.parameters()} != {torch.float32}:
        raise ValueError('all parameters must remain in float32')
    loaded = time.monotonic()
    results, logits_batches = [], []
    config = dict(model_id=MODEL_ID, revision=REVISION, parameter_count=sum(p.numel() for p in model.parameters()),
        label_token_ids=label_ids, dtype='float32', device='cpu', threads=4,
        batch_size=args.batch_size, max_input_tokens=512, truncation=False,
        decision='complete native greedy output, EOS required, no score cutoff',
        displayed_score='full-vocabulary probability of first output token 209',
        load_seconds=loaded-started, loading=loading, seed=0,
        packages={name: importlib.metadata.version(name) for name in
                  ('torch', 'transformers', 'huggingface_hub', 'numpy', 'safetensors')})
    save_json(args.output / 'config.json', config)
    with (args.output / 'scores.jsonl').open('x') as stream, torch.inference_mode():
        for start in range(0, len(inputs), args.batch_size):
            batch = inputs[start:start+args.batch_size]
            tokens = tokenizer([r['model_input'] for r in batch], padding=True,
                               truncation=False, return_tensors='pt')
            if tokens['input_ids'].shape[1] > 512:
                raise ValueError('input exceeds declared limit; never truncate')
            before = time.monotonic()
            generated = model.generate(**tokens, do_sample=False, num_beams=1,
                max_new_tokens=3, return_dict_in_generate=True, output_logits=True)
            logits = generated.logits[0].float()
            logits_batches.append(logits.numpy().copy())
            elapsed = time.monotonic()-before
            for i, row in enumerate(batch):
                result = dict(**row, token_ids=tokens['input_ids'][i][tokens['attention_mask'][i].bool()].tolist(),
                    batch_seconds=elapsed, **score_generation(logits[i].tolist(),
                        tokenizer.decode(generated.sequences[i], skip_special_tokens=True),
                        generated.sequences[i].tolist(), label_ids, model.config.eos_token_id))
                results.append(result)
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            print(f'{len(results)}/{len(inputs)} pairs; batch {elapsed:.1f}s; peak RSS '
                  f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2:.1f} GiB', flush=True)
    with (args.output / 'first-token-logits.npy').open('xb') as stream:
        np.save(stream, np.concatenate(logits_batches), allow_pickle=False)
    save_json(args.output / 'analysis.json', summarize(results))
    with (args.output / 'DECISIONS.md').open('x') as stream:
        stream.write(render_decisions(results))
    save_json(args.output / 'completion.json', dict(pairs=len(results),
        inference_seconds=time.monotonic()-loaded, total_seconds=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scores_sha256=sha256(args.output / 'scores.jsonl'),
        logits_sha256=sha256(args.output / 'first-token-logits.npy')))
    print(json.dumps(summarize(results), indent=2), flush=True)


if __name__ == '__main__':
    main()
