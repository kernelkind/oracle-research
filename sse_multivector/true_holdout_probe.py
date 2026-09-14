"""TRUE02: all frozen unseen in-domain category pairs, with TRUE01 inference."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time

import hierarcaps_mask_probe
import true_category_probe
from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION, WEIGHT_HASHES, model_input, score_generation


THRESHOLD = 0.142


def prepare_inputs(fixture):
    """Validate the complete frozen relation; never infer or repair expected labels."""
    if (not isinstance(fixture, dict) or fixture.get('experiment') != 'TRUE02'
            or fixture.get('threshold') != THRESHOLD):
        raise ValueError('TRUE02 fixture with the frozen threshold 0.142 required')
    domains = fixture.get('domains')
    if not isinstance(domains, list) or len(domains) != 5:
        raise ValueError('exactly five domains required')
    seen_domains, seen_categories, rows = set(), set(), []
    for domain in domains:
        if not isinstance(domain, dict):
            raise ValueError('domain object required')
        domain_id = domain.get('id')
        if not isinstance(domain_id, str) or not domain_id.strip() or domain_id in seen_domains:
            raise ValueError('nonempty unique domain IDs required')
        seen_domains.add(domain_id)
        categories = domain.get('categories')
        if not isinstance(categories, dict) or len(categories) != 6:
            raise ValueError('exactly six category strings per domain required')
        for key, title in categories.items():
            if not isinstance(key, str) or not key.strip() or key in seen_categories:
                raise ValueError('nonempty globally unique category IDs required')
            if not isinstance(title, str) or not title.strip():
                raise ValueError('nonempty category titles required')
            seen_categories.add(key)
        rationale = domain.get('rationale')
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError('nonempty pre-inference rationale required')
        contains = domain.get('contains')
        if not isinstance(contains, list):
            raise ValueError('explicit positive pair list required')
        positives = set()
        for pair in contains:
            if (not isinstance(pair, list) or len(pair) != 2
                    or not all(isinstance(key, str) and key in categories for key in pair)
                    or pair[0] == pair[1] or tuple(pair) in positives):
                raise ValueError('unique distinct in-domain positive pairs required')
            positives.add(tuple(pair))
        for a, b in positives:
            for middle, c in positives:
                if b == middle and a != c and (a, c) not in positives:
                    raise ValueError(f'positive closure missing: {a} contains {c}')
        for a_id, a in categories.items():
            for b_id, b in categories.items():
                if a_id == b_id:
                    continue
                expected, reverse = (a_id, b_id) in positives, (b_id, a_id) in positives
                kind = ('equivalent' if reverse else 'strict-containment') if expected else (
                    'reversed-containment' if reverse else 'noncontaining')
                row = dict(id=f'{a_id}-contains-{b_id}', domain=domain_id, a_id=a_id,
                           b_id=b_id, a=a, b=b, expected=expected, kind=kind, format='topic')
                row['model_input'] = model_input(row, 'topic')
                rows.append(row)
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('generated pair IDs must be unique')
    return rows


def freeze_inputs(fixture_path, expected_sha256, output):
    """Persist exact inputs and source identity before checkpoint hashing or loading."""
    raw = fixture_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('frozen fixture bytes changed')

    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate JSON key: ' + key)
            value[key] = item
        return value

    inputs = prepare_inputs(json.loads(raw, object_pairs_hook=unique_keys))
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'fixture.json').open('xb') as stream:
        stream.write(raw)
    save_json(output / 'inputs.json', inputs)
    source_hashes = {}
    for source in (Path(__file__), Path(true_category_probe.__file__),
                   Path(hierarcaps_mask_probe.__file__)):
        with (output / source.name).open('xb') as stream:
            stream.write(source.read_bytes())
        source_hashes[source.name] = sha256(output / source.name)
    save_json(output / 'started.json', dict(experiment='TRUE02', model_id=MODEL_ID,
        revision=REVISION, fixture_sha256=digest, inputs_sha256=sha256(output / 'inputs.json'),
        runner_sha256=source_hashes[Path(__file__).name],
        scorer_sha256=source_hashes[Path(true_category_probe.__file__).name],
        source_sha256=source_hashes, primary_format='topic', threshold=THRESHOLD,
        threshold_rule='entailment_score > 0.142', pairs=len(inputs)))
    return inputs


def threshold_decision(score):
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('finite entailment probability required')
    return score > THRESHOLD


def has_expected_labels(rows):
    """An answer key is either complete and Boolean or absent, never inferred."""
    if not rows:
        raise ValueError('nonempty scored rows required')
    present = ['expected' in row for row in rows]
    if any(present) and (not all(present) or any(type(row['expected']) is not bool for row in rows)):
        raise ValueError('complete explicit Boolean answer key or wholly unlabeled rows required')
    return all(present)


def summarize(rows):
    labeled = has_expected_labels(rows)

    def counts(items, field):
        correct = sum(row[field] == row['expected'] for row in items)
        return dict(total=len(items), correct=correct, accuracy=correct / len(items),
            positive=sum(row['expected'] for row in items),
            negative=sum(not row['expected'] for row in items),
            true_positive=sum(row[field] is True and row['expected'] for row in items),
            true_negative=sum(row[field] is False and not row['expected'] for row in items),
            false_positive=sum(row[field] is True and not row['expected'] for row in items),
            false_negative=sum(row[field] is False and row['expected'] for row in items),
            unresolved=sum(row[field] is None for row in items))

    def both_counts(items):
        return dict(native=counts(items, 'predicted'), cutoff=counts(items, 'threshold_predicted'))

    def pair_counts(items):
        pairs = {}
        for row in items:
            key = (row['domain'], *sorted((row['a_id'], row['b_id'])))
            pairs.setdefault(key, []).append(row)
        for pair in pairs.values():
            if (len(pair) != 2 or pair[0]['a_id'] != pair[1]['b_id']
                    or pair[0]['b_id'] != pair[1]['a_id']):
                raise ValueError('both distinct directions required for unordered pair accuracy')
        native = sum(all(row['predicted'] == row['expected'] for row in pair)
                     for pair in pairs.values())
        cutoff = sum(all(row['threshold_predicted'] == row['expected'] for row in pair)
                     for pair in pairs.values())
        return dict(total=len(pairs), native_correct=native, cutoff_correct=cutoff,
                    native_accuracy=native / len(pairs), cutoff_accuracy=cutoff / len(pairs))

    def score_ordering(items):
        positive = [row for row in items if row['expected']]
        negative = [row for row in items if not row['expected']]

        def extreme(group, operation):
            if not group:
                return None
            value = operation(row['entailment_score'] for row in group)
            return dict(score=value, ids=[row['id'] for row in group if row['entailment_score'] == value])

        minimum_positive, maximum_negative = extreme(positive, min), extreme(negative, max)
        gap = None if not positive or not negative else (
            minimum_positive['score'] - maximum_negative['score'])
        return dict(positive=len(positive), negative=len(negative), comparisons=len(positive)*len(negative),
            inversions=sum(p['entailment_score'] < n['entailment_score'] for p in positive for n in negative),
            ties=sum(p['entailment_score'] == n['entailment_score'] for p in positive for n in negative),
            minimum_positive=minimum_positive, maximum_positive=extreme(positive, max),
            minimum_negative=extreme(negative, min), maximum_negative=maximum_negative,
            separation_gap=gap, strictly_separated=None if gap is None else gap > 0)

    for row in rows:
        if row['threshold_predicted'] is not threshold_decision(row['entailment_score']):
            raise ValueError('saved threshold verdict differs from frozen cutoff')
    if not labeled:
        if any(row['predicted'] is not None and type(row['predicted']) is not bool for row in rows):
            raise ValueError('native verdict must be Boolean or unresolved')

        def prediction_counts(field):
            return dict(total=len(rows), yes=sum(row[field] is True for row in rows),
                        no=sum(row[field] is False for row in rows),
                        unresolved=sum(row[field] is None for row in rows))

        return dict(threshold=THRESHOLD, threshold_rule='entailment_score > 0.142',
                    labeled=False, overall=dict(native=prediction_counts('predicted'),
                                                cutoff=prediction_counts('threshold_predicted')))
    result = dict(threshold=THRESHOLD, threshold_rule='entailment_score > 0.142',
                  overall=both_counts(rows))
    for field in ('domain', 'kind'):
        result[field] = {value: both_counts([row for row in rows if row[field] == value])
                         for value in sorted({row[field] for row in rows})}
    domains = {value: [row for row in rows if row['domain'] == value]
               for value in sorted({row['domain'] for row in rows})}
    result['unordered_pairs'] = dict(overall=pair_counts(rows),
                                    domain={key: pair_counts(items) for key, items in domains.items()})
    result['score_ordering'] = dict(overall=score_ordering(rows),
                                   domain={key: score_ordering(items) for key, items in domains.items()})
    return result


def render_decisions(rows, experiment='TRUE02'):
    labeled = has_expected_labels(rows)

    def cell(value):
        return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')

    def answer(value):
        return 'Unresolved' if value is None else ('Yes' if value else 'No')

    subject = 'holdout' if labeled else 'title'
    lines = [f'# {experiment} — Every frozen {subject} decision', '',
        'Each row asks **A contains B?** B is the premise; A is the hypothesis. '
        'All inputs use the unchanged TRUE01 topic sentence wrapper.', '',
        'Native answers are complete greedy labels with EOS required. Score is full-vocabulary '
        'probability of the first output token being `1`, not calibrated category confidence. '
        'The separately frozen cutoff verdict is **score > 0.142**; no cutoff was fitted here.', '']
    if not labeled:
        lines.extend(['No answer key is attached; these are model verdicts, not measured accuracy.', '',
                      '| ID | A | B | Native | Score | Cutoff |',
                      '|---|---|---|---|---|---|'])
        for row in rows:
            lines.append('| ' + ' | '.join(map(cell, (row['id'], row['a'], row['b'],
                answer(row['predicted']), f"{row['entailment_score']:.6f}",
                answer(row['threshold_predicted'])))) + ' |')
        return '\n'.join(lines) + '\n'
    lines.extend([
        '| ID | A | B | Expected | Native | Score | Cutoff |',
        '|---|---|---|---|---|---|---|'])
    for row in rows:
        lines.append('| ' + ' | '.join(map(cell, (row['id'], row['a'], row['b'],
            answer(row['expected']), answer(row['predicted']), f"{row['entailment_score']:.6f}",
            answer(row['threshold_predicted'])))) + ' |')
    for title, field in (('Native errors', 'predicted'), ('Cutoff errors', 'threshold_predicted')):
        errors = [row for row in rows if row[field] != row['expected']]
        lines.extend(['', f'## {title} ({len(errors)})', ''])
        lines.extend(f"- {cell(row['id'])}: expected {answer(row['expected'])}; "
                     f"got {answer(row[field])}; score {row['entailment_score']:.6f}."
                     for row in errors)
        if not errors:
            lines.append('None.')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('fixture', 'output', 'snapshot'):
        parser.add_argument('--' + field, type=Path, required=True)
    parser.add_argument('--fixture-sha256', required=True)
    parser.add_argument('--batch-size', type=int, default=4, choices=(1, 2, 4))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; earlier or interrupted runs must be preserved')
    started = time.monotonic()
    snapshot = args.snapshot.resolve(strict=True)
    if (snapshot.name != REVISION or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('exact pinned model snapshot required')
    inputs = freeze_inputs(args.fixture, args.fixture_sha256, args.output)
    run_inference(snapshot, inputs, args.output, args.batch_size, started)


def run_inference(snapshot, inputs, output, batch_size, started, experiment='TRUE02'):
    print(f'Frozen {len(inputs)} inputs before inference. Hashing the pinned checkpoint.', flush=True)
    files = {path.name: sha256(path) for path in sorted(snapshot.iterdir()) if path.is_file()}
    for index, expected in enumerate(WEIGHT_HASHES, 1):
        if files.get(f'pytorch_model-{index:05d}-of-00005.bin') != expected:
            raise ValueError('weight shard differs from the release manifest')
    save_json(output / 'model-files.json', files)

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
    config = dict(experiment=experiment, model_id=MODEL_ID, revision=REVISION,
        parameter_count=sum(p.numel() for p in model.parameters()),
        label_token_ids=label_ids, dtype='float32', device='cpu', threads=4,
        batch_size=batch_size, max_input_tokens=512, truncation=False,
        decision='complete native greedy output, EOS required, no score cutoff',
        threshold=THRESHOLD, threshold_decision='entailment_score > 0.142',
        displayed_score='full-vocabulary probability of first output token 209',
        generation=dict(do_sample=False, num_beams=1, max_new_tokens=3,
                        return_dict_in_generate=True, output_logits=True),
        load_seconds=loaded-started, loading=loading, seed=0,
        packages={name: importlib.metadata.version(name) for name in
                  ('torch', 'transformers', 'huggingface_hub', 'numpy', 'safetensors')})
    save_json(output / 'config.json', config)
    with (output / 'scores.jsonl').open('x') as stream, torch.inference_mode():
        for start in range(0, len(inputs), batch_size):
            batch = inputs[start:start+batch_size]
            tokens = tokenizer([row['model_input'] for row in batch], padding=True,
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
                result = dict(**row,
                    token_ids=tokens['input_ids'][i][tokens['attention_mask'][i].bool()].tolist(),
                    batch_seconds=elapsed, **score_generation(logits[i].tolist(),
                        tokenizer.decode(generated.sequences[i], skip_special_tokens=True),
                        generated.sequences[i].tolist(), label_ids, model.config.eos_token_id))
                result['threshold_predicted'] = threshold_decision(result['entailment_score'])
                results.append(result)
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            print(f'{len(results)}/{len(inputs)} pairs; batch {elapsed:.1f}s; peak RSS '
                  f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2:.1f} GiB', flush=True)
    with (output / 'first-token-logits.npy').open('xb') as stream:
        np.save(stream, np.concatenate(logits_batches), allow_pickle=False)
    analysis = summarize(results)
    save_json(output / 'analysis.json', analysis)
    with (output / 'DECISIONS.md').open('x') as stream:
        stream.write(render_decisions(results, experiment=experiment))
    save_json(output / 'completion.json', dict(pairs=len(results),
        inference_seconds=time.monotonic()-loaded, total_seconds=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scores_sha256=sha256(output / 'scores.jsonl'),
        logits_sha256=sha256(output / 'first-token-logits.npy'),
        analysis_sha256=sha256(output / 'analysis.json'),
        decisions_sha256=sha256(output / 'DECISIONS.md')))
    print(json.dumps(analysis, indent=2), flush=True)


if __name__ == '__main__':
    main()
