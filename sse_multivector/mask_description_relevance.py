"""Score the frozen NLI diagnostic pairs with a local query/passage reranker."""
import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time

from mask_description_nli import sha256


def prepare_queries(saved):
    seen = set()
    rows = []
    for pair in saved:
        key = (pair['vector'], pair['description'])
        if key in seen:
            raise ValueError('duplicate pair')
        seen.add(key)
        passage = ' '.join(pair['source']['fragments'])
        if passage != pair['premise']:
            raise ValueError('saved premise differs from source fragments')
        rows.append(dict(vector=pair['vector'], description=pair['description'],
                         query=pair['description'], passage=passage, source=pair['source']))
    return rows


def relevance_scores(logits):
    scores = []
    for row in logits:
        if len(row) != 1 or not math.isfinite(row[0]):
            raise ValueError('one finite relevance logit required')
        x = row[0]
        scores.append(1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x)))
    return scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    pairs = prepare_queries(json.loads(args.input.read_bytes()))
    fixture = json.loads(args.fixture.read_bytes())

    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    print('Loading pinned reranker on CPU with two threads', flush=True)
    snapshot = Path(snapshot_download(
        fixture['model_id'], revision=fixture['model_revision'], cache_dir=str(args.cache),
        token=False, max_workers=1, allow_patterns=['*.json', '*.model', 'model.safetensors']))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        snapshot, local_files_only=True, use_safetensors=True, trust_remote_code=False).cpu().eval()
    if model.config.num_labels != 1:
        raise ValueError('expected single-logit relevance model')
    loading_seconds = time.monotonic() - started
    started = time.monotonic()
    print('Scoring ' + str(len(pairs)) + ' fixed query/passage pairs', flush=True)
    for start in range(0, len(pairs), 4):
        batch = pairs[start:start + 4]
        tokens = tokenizer([p['query'] for p in batch], [p['passage'] for p in batch],
                           padding=True, truncation=False, return_tensors='pt')
        if tokens['input_ids'].shape[1] > 512:
            raise ValueError('input exceeds experiment limit; no silent truncation')
        with torch.inference_mode():
            raw = model(**tokens).logits.tolist()
        for pair, logits, score, length in zip(batch, raw, relevance_scores(raw),
                                              tokens['attention_mask'].sum(dim=1).tolist()):
            pair.update(logits=logits, score=score, token_count=length)
    seconds = time.monotonic() - started
    config = dict(model_id=fixture['model_id'], model_revision=fixture['model_revision'],
                  model_files={str(p.relative_to(snapshot)): sha256(p)
                               for p in sorted(snapshot.rglob('*')) if p.is_file()},
                  parameters=sum(p.numel() for p in model.parameters()),
                  input_sha256=sha256(args.input), fixture_sha256=sha256(args.fixture),
                  source_sha256={name: sha256(Path(__file__).with_name(name)) for name in
                                 ['mask_description_relevance.py', 'mask_description_nli.py']},
                  packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
                  torch_threads=2, batch_size=4, seed=0, device='cpu', dtype='float32',
                  loading_seconds=loading_seconds, inference_seconds=seconds,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  notes='Raw relevance logits and independent sigmoid scores; not calibrated membership probabilities or cosine. No hierarchy changes.')
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for name, path in [('fixture.json', args.fixture), ('input.json', args.input),
                       ('mask_description_relevance.py', Path(__file__)),
                       ('mask_description_nli.py', Path(__file__).with_name('mask_description_nli.py'))]:
        with (args.output / name).open('xb') as stream:
            stream.write(path.read_bytes())
    print(json.dumps(dict(pairs=len(pairs), inference_seconds=seconds,
                          parameters=config['parameters'], peak_rss_kib=config['peak_rss_kib'])))


if __name__ == '__main__':
    main()
