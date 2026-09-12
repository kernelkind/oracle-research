"""Compare fixed meanings with a pinned WordNet relation classifier, CPU only."""
import argparse
from collections import Counter
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time

from mask_description_nli import sha256

MODEL = 'ChangeIsKey/change-type-classifier'
REVISION = '5c833b8a1f6e1f6fc3e27c533ce16e21949c931e'
LABELS = {0: 'homonym', 1: 'hyponym', 2: 'hypernym', 3: 'co-hyponym', 4: 'antonym'}
NATIVE_SOURCE = ('https://raw.githubusercontent.com/ChangeIsKey/change-type-classification/'
                 '71ceac95188eb41eaed4ba831c1c2a212c004a76/data/test.jsonl')


def prepare_pairs(source, manual, native):
    def unwrap(value):
        prefix = 'This text is about '
        if not value.startswith(prefix) or not value.endswith('.'):
            raise ValueError('unexpected source wrapper')
        return value[len(prefix):-1]
    pairs = []
    for index, pair in enumerate(source):
        if pair['measurement'] == 'relation' and pair['kind'] == 'subject':
            pairs.append(dict(condition='subject', source_index=index,
                              child_group=pair['child_group'], parent_group=pair['parent_group'],
                              first=unwrap(pair['premise']), second=unwrap(pair['hypothesis'])))
    for child in manual['groups']:
        for parent in manual['groups']:
            if child['id'] != parent['id']:
                pairs.append(dict(condition='manual', child_group=child['id'], parent_group=parent['id'],
                                  first=child['description'], second=parent['description']))
    for pair in native:
        pairs.append(dict(condition='native', source_id=pair['id'], first=pair['definition1'],
                          second=pair['definition2'], expected_label=(
                              'homonym' if pair['label'] == 'negative' else pair['label'])))
    if any(not p['first'].strip() or not p['second'].strip() for p in pairs):
        raise ValueError('empty meaning')
    return pairs


def annotate_scores(pairs, logits, labels):
    if len(pairs) != len(logits) or set(labels) != set(range(len(labels))):
        raise ValueError('logit rows and label indices must match')
    for raw in logits:
        if len(raw) != len(labels) or not raw or not all(math.isfinite(x) for x in raw):
            raise ValueError('finite logits required for every label')
    for pair, raw in zip(pairs, logits):
        exps = [math.exp(value - max(raw)) for value in raw]
        total = sum(exps)
        scores = {labels[i]: value / total for i, value in enumerate(exps)}
        pair.update(logits=raw, scores=scores, prediction=max(scores, key=scores.get))


def select_native(rows):
    expected = {'negative', 'hyponym', 'hypernym', 'co-hyponym', 'antonym'}
    counts = Counter()
    selected = []
    for row in rows:
        if row['label'] in expected and counts[row['label']] < 2:
            selected.append(row)
            counts[row['label']] += 1
    if counts != Counter({label: 2 for label in expected}):
        raise ValueError('expected two native examples per class')
    return selected


def score_pairs(pairs, cache):
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    snapshot = Path(snapshot_download(MODEL, revision=REVISION, cache_dir=str(cache),
                                      local_files_only=True, token=False))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_safetensors=True).cpu().eval()
    if model.config.id2label != LABELS:
        raise ValueError('checkpoint label orientation differs from verified mapping')
    loading_seconds = time.monotonic() - started
    started = time.monotonic()
    print(f'Scoring {len(pairs)} fixed pairs; two CPU threads, batch size four', flush=True)
    for start in range(0, len(pairs), 4):
        batch = pairs[start:start + 4]
        tokens = tokenizer([p['first'] for p in batch], [p['second'] for p in batch],
                           padding=True, truncation=False, return_tensors='pt')
        if tokens['input_ids'].shape[1] > 512:
            raise ValueError('input exceeds supported length; no silent truncation')
        with torch.inference_mode():
            logits = model(**tokens).logits.tolist()
        annotate_scores(batch, logits, LABELS)
        for pair, count in zip(batch, tokens['attention_mask'].sum(dim=1).tolist()):
            pair['token_count'] = count
        if start % 200 == 0:
            print(f'{start + len(batch)}/{len(pairs)} pairs', flush=True)
    return dict(model_id=MODEL, model_revision=REVISION, model_labels=LABELS,
                model_files={p.name: sha256(p) for p in sorted(snapshot.iterdir()) if p.is_file()},
                parameters=sum(p.numel() for p in model.parameters()),
                packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
                device='cpu', torch_threads=2, batch_size=4, seed=0,
                loading_seconds=loading_seconds, inference_seconds=time.monotonic() - started,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ['source', 'manual', 'native', 'cache', 'output']:
        parser.add_argument('--' + arg, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous results')
    native = select_native(json.loads(line) for line in args.native.read_text().splitlines())
    pairs = prepare_pairs(json.loads(args.source.read_bytes()), json.loads(args.manual.read_bytes()), native)
    metrics = score_pairs(pairs, args.cache)
    config = dict(**metrics, run_id='SRR01', source_sha256=sha256(args.source),
                  manual_sha256=sha256(args.manual), native_sha256=sha256(args.native),
                  native_source=NATIVE_SOURCE, runner_sha256=sha256(Path(__file__)),
                  note='Hyponym means first narrower than second. No identity class. No hierarchy changed.')
    summary = {condition: dict(Counter(p['prediction'] for p in pairs if p['condition'] == condition))
               for condition in ['subject', 'manual', 'native']}
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('summary.json', summary), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for name, source in [('source.json', args.source), ('manual.json', args.manual),
                         ('native.jsonl', args.native), ('sense_relation_probe.py', Path(__file__)),
                         ('mask_description_nli.py', Path(__file__).with_name('mask_description_nli.py'))]:
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
