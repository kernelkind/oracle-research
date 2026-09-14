"""Fixed-mask, CPU-only diagnostic of released HierarCaps text geometry. No training."""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import time


def prepare_inputs(evidence, original, requested):
    aliases = {}
    for record in evidence:
        for alias in record['aliases']:
            key = alias['short_id']
            if key in aliases:
                raise ValueError('duplicate evidence vector: ' + key)
            aliases[key] = alias
    originals = {}
    for vector in original['vectors']:
        key = vector['short_id']
        if key in originals:
            raise ValueError('duplicate original vector: ' + key)
        originals[key] = vector
    if not requested or len(set(requested)) != len(requested):
        raise ValueError('nonempty, unique requested vector IDs required')
    rows = []
    for key in requested:
        if key not in aliases or key not in originals:
            raise ValueError('unknown vector: ' + key)
        alias = aliases[key]
        for field in ('vector_id', 'note_id', 'note_short_id', 'fragments', 'byte_spans'):
            if alias[field] != originals[key][field]:
                raise ValueError('original mask differs: ' + key + ' / ' + field)
        fragments, spans = alias['fragments'], alias['byte_spans']
        if not fragments or len(fragments) != len(spans):
            raise ValueError('one exact source range per nonempty fragment required')
        raw = alias['text'].encode('utf-8')
        previous_end = 0
        for fragment, (start, end) in zip(fragments, spans):
            if not (previous_end <= start < end <= len(raw)):
                raise ValueError('source ranges must be ordered and nonoverlapping')
            if raw[start:end].decode('utf-8') != fragment:
                raise ValueError('fragment differs from source bytes: ' + key)
            previous_end = end
        row = {field: alias[field] for field in (
            'short_id', 'vector_id', 'note_id', 'note_short_id', 'fragments', 'byte_spans', 'text')}
        row['model_input'] = ' '.join(fragments)
        rows.append(row)
    return rows


def pair_scores(root, a, b):
    if not root or len(a) != len(root) or len(b) != len(root):
        raise ValueError('equal nonzero vector dimensions required')
    for vector in (root, a, b):
        if not all(math.isfinite(x) for x in vector) or not math.isclose(
                math.sqrt(sum(x*x for x in vector)), 1., abs_tol=1e-5):
            raise ValueError('finite, unit-normalized embeddings required')
    outward = [x-r for x, r in zip(a, root)]
    edge = [y-x for x, y in zip(a, b)]
    denominator = math.sqrt(sum(x*x for x in outward) * sum(x*x for x in edge))
    angle = None if denominator <= 1e-12 else math.acos(max(-1., min(1.,
        sum(x*y for x, y in zip(outward, edge)) / denominator)))
    return dict(cosine=sum(x*y for x, y in zip(a, b)), angle_radians=angle,
                angle_degrees=None if angle is None else math.degrees(angle))


def verify_loading(info):
    for key in ('missing_keys', 'mismatched_keys', 'error_msgs'):
        if info.get(key):
            raise ValueError('incomplete text checkpoint: ' + key + ': ' + str(info[key]))
    unexpected = [key for key in info.get('unexpected_keys', [])
                  if not key.startswith(('vision_model.', 'visual_projection.'))
                  and key != 'logit_scale']
    if unexpected:
        raise ValueError('unexpected non-vision parameters: ' + str(unexpected))


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('evidence', 'original', 'fixture', 'output', 'cache'):
        parser.add_argument('--' + flag, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve previous runs')
    fixture = json.loads(args.fixture.read_bytes())
    rows = prepare_inputs(json.loads(args.evidence.read_bytes()),
                          json.loads(args.original.read_bytes()), fixture['vectors'])
    ids = {row['short_id'] for row in rows}
    for a, b in fixture['direction_checks']:
        if a not in ids or b not in ids or a == b:
            raise ValueError('invalid direction check')
    for child, preferred, other in fixture['parent_comparisons']:
        if not {child, preferred, other} <= ids or len({child, preferred, other}) != 3:
            raise ValueError('invalid parent comparison')
    provenance = dict(evidence_sha256=sha256(args.evidence),
                      original_sha256=sha256(args.original),
                      fixture_sha256=sha256(args.fixture), runner_sha256=sha256(Path(__file__)))
    if provenance['original_sha256'] != fixture['original_sha256']:
        raise ValueError('frozen original artifact changed')
    args.output.mkdir(parents=True)
    save_json(args.output / 'inputs.json', rows)
    save_json(args.output / 'fixture.json', fixture)
    save_json(args.output / 'input-provenance.json', provenance)
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())

    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer, CLIPTextModelWithProjection
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    print('Inputs frozen. Downloading/loading one released text encoder; CPU, two threads.', flush=True)
    snapshot = Path(snapshot_download(
        fixture['model_id'], revision=fixture['model_revision'], cache_dir=str(args.cache),
        token=False, max_workers=1,
        allow_patterns=['config.json', 'pytorch_model.bin', 'tokenizer.json',
                        'tokenizer_config.json', 'special_tokens_map.json', 'vocab.json', 'merges.txt']))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model, loading = CLIPTextModelWithProjection.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, weights_only=True,
        output_loading_info=True, attn_implementation='eager')
    verify_loading(loading)
    model = model.cpu().eval()
    # Root is the author's empty-string origin, not a semantic instruction to the model.
    texts = [''] + [row['model_input'] for row in rows]
    embeddings, token_counts = [], []
    loaded = time.monotonic()
    print('Encoding ' + str(len(rows)) + ' exact masks and the empty-string root.', flush=True)
    with torch.inference_mode():
        for start in range(0, len(texts), 4):
            tokens = tokenizer(texts[start:start+4], padding=True, truncation=False, return_tensors='pt')
            if tokens['input_ids'].shape[1] > model.config.max_position_embeddings:
                raise ValueError('input exceeds checkpoint limit; truncation is forbidden')
            features = model(**tokens).text_embeds
            features = features / features.norm(dim=-1, keepdim=True)
            embeddings.extend(features.tolist())
            token_counts.extend(tokens['attention_mask'].sum(dim=1).tolist())
    encoded = time.monotonic()
    root, vectors = embeddings[0], embeddings[1:]
    pairs = [dict(a=a['short_id'], b=b['short_id'], **pair_scores(root, x, y))
             for a, x in zip(rows, vectors) for b, y in zip(rows, vectors)]
    lookup = {(p['a'], p['b']): p for p in pairs}
    direction_checks = []
    for a, b in fixture['direction_checks']:
        forward, reverse = lookup[a, b]['angle_degrees'], lookup[b, a]['angle_degrees']
        direction_checks.append(dict(broader=a, narrower=b, forward_degrees=forward,
                                     reverse_degrees=reverse, reverse_minus_forward=reverse-forward))
    comparisons = []
    for child, preferred, other in fixture['parent_comparisons']:
        p, o = lookup[preferred, child]['angle_degrees'], lookup[other, child]['angle_degrees']
        comparisons.append(dict(child=child, preferred=preferred, other=other,
                                preferred_degrees=p, other_degrees=o, other_minus_preferred=o-p))
    embedding_records = [dict(vector_id=row['short_id'], model_input=row['model_input'],
                              token_count=count, embedding=vector,
                              distance_from_root=math.dist(root, vector))
                         for row, vector, count in zip(rows, vectors, token_counts[1:])]
    save_json(args.output / 'embeddings.json', dict(root=root, root_token_count=token_counts[0],
                                                   vectors=embedding_records))
    save_json(args.output / 'scores.json', pairs)
    save_json(args.output / 'checks.json', dict(direction=direction_checks, parent_comparisons=comparisons))
    config = dict(**provenance, model_id=fixture['model_id'], model_revision=fixture['model_revision'],
                  model_files={str(p.relative_to(snapshot)): sha256(p)
                               for p in sorted(snapshot.rglob('*')) if p.is_file()},
                  parameters=sum(p.numel() for p in model.parameters()), dimension=len(root),
                  loading=loading, max_tokens=model.config.max_position_embeddings,
                  packages={p: importlib.metadata.version(p) for p in
                            ('torch', 'transformers', 'huggingface_hub', 'tokenizers', 'safetensors')},
                  cpu_threads=2, batch_size=4, dtype='float32', device='cpu', seed=0,
                  loading_seconds=loaded-started, inference_seconds=encoded-loaded,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  score_definition='Angle between A-root and B-A for normalized text embeddings. '
                                   'Lower supports A as broader than B. Not a probability or calibrated cutoff.',
                  scope='Mask-only text-geometry diagnostic. No training, membership changes, or hierarchy construction.')
    save_json(args.output / 'config.json', config)
    print(json.dumps(dict(masks=len(rows), pairs=len(pairs), parameters=config['parameters'],
                          inference_seconds=config['inference_seconds'], peak_rss_kib=config['peak_rss_kib'])))


if __name__ == '__main__':
    main()
