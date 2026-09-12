"""Fixed-input native category-classification diagnostic; no hierarchy edits."""

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import subprocess
import sys
import time


MODEL = 'knowledgator/gliclass-base-v3.0'
REVISION = '77a70e6cd52e602ed18184ef37d18bdd3741e3d5'
SOURCE_REVISION = '5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae'


def make_requests(records, labels, conditions=('joint', 'reversed', 'single')):
    if (not records or len({r['row'] for r in records}) != len(records)
            or any(not isinstance(r['subject'], str) or not r['subject'].strip()
                   for r in records)
            or not labels or len(set(labels)) != len(labels)
            or any(not isinstance(label, str) or not label.strip() for label in labels)):
        raise ValueError('distinct rows, nonempty subjects and distinct labels required')
    if (not conditions or len(set(conditions)) != len(conditions)
            or any(c not in ('joint', 'reversed', 'single') for c in conditions)):
        raise ValueError('distinct known conditions required')
    groups = []
    for condition in conditions:
        if condition == 'single':
            groups.extend(('single', [label]) for label in labels)
        else:
            groups.append((condition, list(labels if condition == 'joint' else reversed(labels))))
    return [dict(row=r['row'], text=r['subject'], condition=condition, labels=group)
            for condition, group in groups for r in records]


def attach_scores(request, logits):
    if len(logits) != len(request['labels']) or not all(math.isfinite(v) for v in logits):
        raise ValueError('one finite logit per requested category required')
    scores = []
    for label, logit in zip(request['labels'], logits):
        score = 1 / (1 + math.exp(-logit)) if logit >= 0 else math.exp(logit) / (1 + math.exp(logit))
        scores.append(dict(label=label, logit=logit, score=score, accepted=score >= 0.5))
    return scores


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--labels', nargs='+', required=True)
    parser.add_argument('--conditions', nargs='+', choices=['joint', 'reversed', 'single'],
                        default=['joint', 'reversed', 'single'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('preserve previous outputs; choose a new directory')
    records = json.loads(args.input.read_text())
    requests = make_requests(records, args.labels, args.conditions)
    source_revision = subprocess.check_output(
        ['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip()
    if source_revision != SOURCE_REVISION or subprocess.check_output(
            ['git', '-C', str(args.source), 'status', '--porcelain'], text=True).strip():
        raise ValueError('clean pinned native source required')
    if importlib.metadata.version('transformers') != '4.48.2':
        raise ValueError('use the pinned native-supported Transformers runtime')
    sys.path.insert(0, str(args.source.resolve()))
    import torch
    from gliclass import GLiClassModel, ZeroShotClassificationPipeline
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from transformers import AutoTokenizer

    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    print('Loading pinned public checkpoint; CPU only, two threads', flush=True)
    snapshot = Path(snapshot_download(
        MODEL, revision=REVISION, cache_dir=str(args.cache), token=False,
        max_workers=1, local_files_only=args.offline,
        allow_patterns=['*.json', '*.model', 'model.safetensors']))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model, loading = GLiClassModel.from_pretrained(
        snapshot, local_files_only=True, use_safetensors=True,
        attn_implementation='eager', output_loading_info=True)
    if any(loading.get(k) for k in ['missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs']):
        raise ValueError('inexact weight loading: ' + str(loading))
    # Check keys and shapes independently of native ignored-key filters.
    weights = load_file(str(snapshot / 'model.safetensors'))
    state = model.state_dict()
    if weights.keys() != state.keys() or any(weights[k].shape != state[k].shape for k in weights):
        raise ValueError('checkpoint and instantiated model differ')
    del weights, state
    model.cpu().eval()
    if (model.config.architecture_type != 'uni-encoder'
            or tokenizer.convert_tokens_to_ids('<<LABEL>>') != model.config.class_token_index
            or tokenizer.convert_tokens_to_ids('<<SEP>>') != model.config.text_token_index):
        raise ValueError('native architecture or special tokens differ')
    pipeline = ZeroShotClassificationPipeline(
        model, tokenizer, classification_type='multi-label', device='cpu',
        max_length=512, progress_bar=False)
    loading_seconds = time.monotonic() - started

    def score(batch):
        texts, labels = [r['text'] for r in batch], [r['labels'] for r in batch]
        rendered = [pipeline.pipe.prepare_input(t, ls) for t, ls in zip(texts, labels)]
        tokens = tokenizer(rendered, padding=True, truncation=False, return_tensors='pt')
        if tokens['input_ids'].shape[1] > 512:
            raise ValueError('would truncate input')
        native = pipeline.pipe.prepare_inputs(texts, labels, same_labels=False)
        if tokens.keys() != native.keys() or any(not torch.equal(tokens[k], native[k]) for k in tokens):
            raise ValueError('native tokenization mismatch')
        with torch.inference_mode():
            logits = model(**native).logits.tolist()
        for r, raw, rendered_text, token_ids, attention in zip(
                batch, logits, rendered, tokens['input_ids'].tolist(), tokens['attention_mask'].tolist()):
            if len(raw) != len(r['labels']):
                raise ValueError('this diagnostic batches identical category lists only')
            r.update(rendered=rendered_text,
                     token_ids=[i for i, present in zip(token_ids, attention) if present],
                     scores=attach_scores(r, raw))

    native = dict(text='One day I will see the world!',
                  labels=['travel', 'dreams', 'sport', 'science', 'politics'])
    score([native])
    reference = pipeline(native['text'], native['labels'], threshold=0.0, batch_size=1)[0]
    if any(a['label'] != b['label'] or abs(a['score'] - b['score']) > 1e-6
           for a, b in zip(native['scores'], reference)) or len(reference) != len(native['labels']):
        raise ValueError('native pipeline/direct-score disagreement')
    native['pipeline_scores'] = reference

    print('Scoring ' + str(len(requests)) + ' fixed requests', flush=True)
    started = time.monotonic()
    # Each condition has one fixed label list; never mix differently sized lists.
    for group_start in range(0, len(requests), len(records)):
        group = requests[group_start:group_start + len(records)]
        for i in range(0, len(group), 4):
            score(group[i:i + 4])
    inference_seconds = time.monotonic() - started
    metadata = dict(
        model=MODEL, model_revision=REVISION, source_revision=SOURCE_REVISION,
        source_files={str(p.relative_to(args.source)): digest(p)
                      for p in sorted((args.source / 'gliclass').rglob('*.py'))},
        model_files={str(p.relative_to(snapshot)): digest(p)
                     for p in sorted(snapshot.rglob('*')) if p.is_file()},
        input_sha256=digest(args.input), code_sha256=digest(__file__),
        parameters=sum(p.numel() for p in model.parameters()), loading=loading,
        native=native, device='cpu', threads=2, batch_size=4, threshold=0.5,
        loading_seconds=loading_seconds, inference_seconds=inference_seconds,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()})
    args.output.mkdir(parents=True)
    for name, value in [('inputs.json', records), ('scores.json', requests), ('config.json', metadata)]:
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(requests=len(requests), scores=sum(len(r['scores']) for r in requests),
                          inference_seconds=inference_seconds, peak_rss_kib=metadata['peak_rss_kib'])))


if __name__ == '__main__':
    main()
