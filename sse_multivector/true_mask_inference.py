"""TRUE12 native mask-membership inference, isolated from immutable TRUE02.

Checkpoint loading, tokenization, generation and scoring match the historical
TRUE runner. This experiment has no containment cutoff or containment report.
"""
import importlib.metadata
import json
import resource
import time

from hierarcaps_mask_probe import save_json, sha256
from true_category_probe import MODEL_ID, REVISION, WEIGHT_HASHES, score_generation


def run_inference(snapshot, inputs, output, batch_size, started):
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
    config = dict(experiment='TRUE12', model_id=MODEL_ID, revision=REVISION,
        parameter_count=sum(p.numel() for p in model.parameters()),
        label_token_ids=label_ids, dtype='float32', device='cpu', threads=4,
        batch_size=batch_size, max_input_tokens=512, truncation=False,
        decision='complete native greedy output, EOS required, no score cutoff',
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
                results.append(result)
                stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            print(f'{len(results)}/{len(inputs)} pairs; batch {elapsed:.1f}s; peak RSS '
                  f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2:.1f} GiB', flush=True)
    with (output / 'first-token-logits.npy').open('xb') as stream:
        np.save(stream, np.concatenate(logits_batches), allow_pickle=False)
    save_json(output / 'completion.json', dict(pairs=len(results),
        inference_seconds=time.monotonic()-loaded, total_seconds=time.monotonic()-started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scores_sha256=sha256(output / 'scores.jsonl'),
        logits_sha256=sha256(output / 'first-token-logits.npy')))
