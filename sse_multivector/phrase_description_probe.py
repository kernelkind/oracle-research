"""Encode frozen subject descriptions; inspect affinity without assigning a hierarchy."""

import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import time

import numpy as np

MODELS = {
    'base': ('sentence-transformers/bert-base-nli-stsb-mean-tokens',
             'c1e99553cc170c78b16717e93e8042552f5bef20', 'model.safetensors'),
    'phrase': ('whaleloops/phrase-bert',
               '6f68f4dc2d28aadefa038c79023dc7dfd51f6495', 'pytorch_model.bin'),
}
NATIVE = ['play an active role', 'participate actively', 'active lifestyle']
QUERIES = [258, 669, 572, 484]


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_inputs(source):
    rows = copy.deepcopy(source['inputs'])
    if not rows or any(r.get('row') != i or not isinstance(r.get('subject'), str)
                       or not r['subject'].strip() or not r.get('note')
                       for i, r in enumerate(rows)):
        raise ValueError('ordered source rows with nonempty subjects and note IDs required')
    lookup = {}
    indices = []
    for row in rows:
        lookup.setdefault(row['subject'], len(lookup))
        indices.append(lookup[row['subject']])
    return rows, list(lookup), indices


def pair_scores(vectors):
    v = np.asarray(vectors, dtype=np.float64)
    if v.ndim != 2 or not all(v.shape) or not np.isfinite(v).all():
        raise ValueError('finite, nonempty matrix required')
    norms = np.linalg.norm(v, axis=1)
    if (norms == 0).any():
        raise ValueError('zero vector has no cosine')
    dots = v @ v.T
    squared = norms**2
    euclidean = np.sqrt(np.maximum(squared[:, None] + squared[None, :] - 2*dots, 0))
    np.fill_diagonal(euclidean, 0)
    cosine = np.clip(dots / (norms[:, None] * norms[None, :]), -1, 1)
    return dict(euclidean=euclidean, cosine=cosine)


def nearest_notes(rows, query, scores, metric, limit):
    scores = np.asarray(scores)
    if (scores.shape != (len(rows),) or not np.isfinite(scores).all()
            or metric not in ('euclidean', 'cosine') or limit < 1):
        raise ValueError('one finite score per row, known metric and positive limit required')
    sign = -1 if metric == 'cosine' else 1
    ordered = sorted(range(len(rows)), key=lambda i: (sign * scores[i], i))
    seen = {rows[query]['note']}
    neighbors = []
    for i in ordered:
        if rows[i]['note'] not in seen:
            seen.add(rows[i]['note'])
            neighbors.append(dict(row=i, note=rows[i]['note'], score=float(scores[i])))
            if len(neighbors) == limit:
                break
    return neighbors


def encode(texts, model_key, cache):
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model_id, revision, weights = MODELS[model_key]
    files = [weights, 'config.json', 'tokenizer_config.json', 'tokenizer.json',
             'vocab.txt', 'special_tokens_map.json', 'modules.json',
             'sentence_bert_config.json', '1_Pooling/config.json']
    started = time.monotonic()
    print(f'Loading {model_key}; pinned public checkpoint; CPU only', flush=True)
    snapshot = Path(snapshot_download(model_id, revision=revision, cache_dir=str(cache),
                                     allow_patterns=files, token=False, max_workers=1))
    pool = json.loads((snapshot / '1_Pooling/config.json').read_text())
    modules = json.loads((snapshot / 'modules.json').read_text())
    if ([m['type'].rsplit('.', 1)[-1] for m in modules] != ['Transformer', 'Pooling']
            or not pool['pooling_mode_mean_tokens']
            or any(v for k, v in pool.items() if k.startswith('pooling_mode_')
                   and k != 'pooling_mode_mean_tokens')):
        raise ValueError('checkpoint does not use the verified mean-pooling path')
    maximum = json.loads((snapshot / 'sentence_bert_config.json').read_text())['max_seq_length']
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModel.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False,
                                     use_safetensors=weights.endswith('.safetensors'),
                                     attn_implementation='eager').cpu().eval()
    load_seconds = time.monotonic() - started

    def batches(values):
        embeddings, counts = [], []
        for start in range(0, len(values), 4):
            tokens = tokenizer(values[start:start+4], padding=True, truncation=False,
                               return_tensors='pt')
            if tokens['input_ids'].shape[1] > maximum:
                raise ValueError(f'input exceeds {maximum} tokens; no silent truncation')
            with torch.inference_mode():
                hidden = model(**tokens).last_hidden_state
                mask = tokens['attention_mask'].unsqueeze(-1).to(hidden.dtype)
                pooled = (hidden * mask).sum(1) / mask.sum(1)
            embeddings.append(pooled.numpy())
            counts.extend(tokens['attention_mask'].sum(1).tolist())
            if len(values) > 4 and start % 100 == 0:
                print(f'{min(start+4, len(values))}/{len(values)} descriptions', flush=True)
        return np.concatenate(embeddings), counts

    native, native_counts = batches(NATIVE)
    native_scores = pair_scores(native)
    expected = np.array([.8142536282539368, .6130303144454956, .584893524646759])
    actual = native_scores['cosine'][np.triu_indices(3, 1)]
    if model_key == 'phrase' and not np.allclose(actual, expected, rtol=0, atol=3e-5):
        raise ValueError(f'official implementation control differs: {actual.tolist()}')
    started = time.monotonic()
    embeddings, counts = batches(texts)
    metadata = dict(model_id=model_id, revision=revision,
                    model_files={str(p.relative_to(snapshot)): sha256(p)
                                 for p in sorted(snapshot.rglob('*')) if p.is_file()},
                    parameters=sum(p.numel() for p in model.parameters()),
                    pooling=pool, maximum_tokens=maximum, native_inputs=NATIVE,
                    native_token_counts=native_counts,
                    native_scores={k: v.tolist() for k, v in native_scores.items()},
                    native_reference_cosines=expected.tolist(),
                    native_reference_applies=model_key == 'phrase',
                    device='cpu', threads=2, batch_size=4, seed=0,
                    loading_seconds=load_seconds, inference_seconds=time.monotonic()-started,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    packages={name: importlib.metadata.version(name)
                              for name in ['torch', 'transformers', 'huggingface-hub', 'numpy']})
    return embeddings, counts, native, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ['input', 'cache', 'output']:
        parser.add_argument('--'+arg, required=True, type=Path)
    parser.add_argument('--model', choices=MODELS, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve prior results')
    source = json.loads(args.input.read_bytes())
    rows, texts, indices = prepare_inputs(source)
    if len(rows) != 945:
        parser.error('PPR01 requires all 945 frozen CAP04 inputs')
    embeddings, counts, native, metadata = encode(texts, args.model, args.cache)
    vectors = embeddings[indices]
    scores = pair_scores(vectors)
    neighborhoods = {str(q): {metric: nearest_notes(rows, q, matrix[q], metric, 10)
                              for metric, matrix in scores.items()} for q in QUERIES}
    config = dict(**metadata, run_id='PPR01', condition=args.model,
                  input_sha256=sha256(args.input), input_count=len(rows),
                  unique_subject_count=len(texts), model_input_field='subject',
                  encoded_texts=texts, row_to_encoded_input=indices,
                  token_counts=[counts[i] for i in indices], queries=QUERIES,
                  runner_sha256=sha256(Path(__file__)),
                  note='Affinity only. No equivalence, membership or hierarchy assignment.')
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in [('inputs.json', rows), ('config.json', config),
                        ('neighborhoods.json', neighborhoods)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    np.save(args.output / 'vectors.npy', vectors, allow_pickle=False)
    np.save(args.output / 'native-vectors.npy', native, allow_pickle=False)
    np.savez_compressed(args.output / 'scores.npz', **scores)
    with (args.output / Path(__file__).name).open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    print(json.dumps(dict(condition=args.model, rows=len(rows),
                          unique_subjects=len(texts), peak_rss_kib=config['peak_rss_kib'],
                          inference_seconds=config['inference_seconds'])), flush=True)


if __name__ == '__main__':
    main()
