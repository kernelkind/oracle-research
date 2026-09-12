"""Local, fixed-input mask/description diagnostic; never edits a hierarchy."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time


def prepare_pairs(evidence, fixture):
    aliases = {}
    for record in evidence:
        for alias in record['aliases']:
            if alias['short_id'] in aliases:
                raise ValueError('duplicate vector ID in evidence')
            aliases[alias['short_id']] = alias
    if len(set(fixture['vectors'])) != len(fixture['vectors']):
        raise ValueError('duplicate requested vector')
    if len(set(fixture['descriptions'])) != len(fixture['descriptions']):
        raise ValueError('duplicate description')
    pairs = []
    for vector in fixture['vectors']:
        if vector not in aliases:
            raise ValueError('unknown vector: ' + vector)
        alias = aliases[vector]
        for description in fixture['descriptions']:
            pairs.append(dict(vector=vector, description=description,
                              premise=' '.join(alias['fragments']),
                              hypothesis=fixture['template'].format(description),
                              source=alias))
    return pairs


def independent_scores(logits, entailment_index):
    if entailment_index not in (0, 1):
        raise ValueError('binary entailment index required')
    result = []
    for row in logits:
        if len(row) != 2 or not all(math.isfinite(x) for x in row):
            raise ValueError('finite binary logits required')
        exps = [math.exp(x - max(row)) for x in row]
        result.append(exps[entailment_index] / sum(exps))
    return result


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    fixture = json.loads(args.fixture.read_bytes())
    pairs = prepare_pairs(json.loads(args.evidence.read_bytes()), fixture)

    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    print('Downloading/loading pinned public model; CPU only, two threads', flush=True)
    snapshot = Path(snapshot_download(
        fixture['model_id'], revision=fixture['model_revision'],
        cache_dir=str(args.cache), token=False, max_workers=1,
        allow_patterns=['*.json', '*.model', 'model.safetensors'],
        ignore_patterns=['onnx/*']))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        snapshot, local_files_only=True, use_safetensors=True, trust_remote_code=False).cpu().eval()
    mapping = model.config.id2label
    entailment = [i for i, label in mapping.items() if label.lower() == 'entailment']
    if len(mapping) != 2 or len(entailment) != 1:
        raise ValueError('expected a binary entailment classifier')
    loading_seconds = time.monotonic() - started
    started = time.monotonic()
    print('Scoring ' + str(len(pairs)) + ' fixed pairs', flush=True)
    for start in range(0, len(pairs), 4):
        batch = pairs[start:start + 4]
        tokens = tokenizer([p['premise'] for p in batch],
                           [p['hypothesis'] for p in batch],
                           padding=True, truncation=False, return_tensors='pt')
        if tokens['input_ids'].shape[1] > 512:
            raise ValueError('input exceeds supported length; no silent truncation')
        with torch.inference_mode():
            logits = model(**tokens).logits.tolist()
        for pair, raw, score, length in zip(
                batch, logits, independent_scores(logits, entailment[0]),
                tokens['attention_mask'].sum(dim=1).tolist()):
            pair.update(logits=raw, score=score, token_count=length)
    seconds = time.monotonic() - started
    scores = {(p['vector'], p['description']): p['score'] for p in pairs}
    checks = [dict(vector=v, preferred=a, other=b,
                   preferred_score=scores[v, a], other_score=scores[v, b],
                   difference=scores[v, a] - scores[v, b])
              for v, a, b in fixture['checks']]
    config = dict(
        model_id=fixture['model_id'], model_revision=fixture['model_revision'],
        model_files={str(p.relative_to(snapshot)): sha256(p)
                     for p in sorted(snapshot.rglob('*')) if p.is_file()},
        model_labels=mapping, parameters=sum(p.numel() for p in model.parameters()),
        evidence_sha256=sha256(args.evidence), fixture_sha256=sha256(args.fixture),
        runner_sha256=sha256(Path(__file__)),
        packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
        torch_threads=2, batch_size=4, seed=0, device='cpu',
        loading_seconds=loading_seconds, inference_seconds=seconds,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        notes='Scores are independent across descriptions, not calibrated probabilities. No membership or hierarchy changed.')
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('checks.json', checks), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for name, source in [('fixture.json', args.fixture), ('mask_description_nli.py', Path(__file__))]:
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(pairs=len(pairs), positive_orderings=sum(c['difference'] > 0 for c in checks),
                          checks=len(checks), inference_seconds=seconds,
                          peak_rss_kib=config['peak_rss_kib'])))


if __name__ == '__main__':
    main()
