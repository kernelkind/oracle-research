"""Frozen category-description transfer check using the cached HierarCaps encoder."""
import argparse
import importlib.metadata
import json
import math
from pathlib import Path
import time

import hierarcaps_mask_probe
from hierarcaps_mask_probe import pair_scores, verify_loading, sha256, save_json


MODEL_ID = 'malper/hierarcaps-clip-l'
MODEL_REVISION = 'e3aa199d94c438f98628c9697a0b64ef5760b03c'
ROLES = ('broader', 'narrower', 'alternative')


def prepare_inputs(fixture):
    if not isinstance(fixture, dict):
        raise ValueError('fixture must be an object')
    for field, expected in (('experiment_id', 'HRC03'), ('model_id', MODEL_ID),
                            ('model_revision', MODEL_REVISION)):
        if fixture.get(field) != expected:
            raise ValueError('unexpected frozen ' + field)
    cases = fixture.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('nonempty cases required')
    rows, ids = [], set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('case must be an object')
        for field in ('id', 'domain', 'rationale'):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError('nonempty string case ' + field + ' required')
        if case['id'] in ids:
            raise ValueError('duplicate case ID: ' + case['id'])
        ids.add(case['id'])
        wordings = case.get('wordings')
        if not isinstance(wordings, list) or len(wordings) != 2:
            raise ValueError('exactly two wordings per case required')
        for index, wording in enumerate(wordings, 1):
            if not isinstance(wording, dict):
                raise ValueError('wording must be an object')
            for role in ROLES:
                text = wording.get(role)
                if not isinstance(text, str) or not text.strip():
                    raise ValueError('nonempty verbatim string required: ' + case['id'] + ' / ' + role)
                # strip() is only an emptiness check: never change the frozen model input.
                rows.append(dict(id=case['id'] + '-w' + str(index) + '-' + role,
                                 case=case['id'], domain=case['domain'], wording=index,
                                 role=role, text=text, model_input=text))
    return rows


def analyze_scores(rows, root, vectors):
    if not rows or len(rows) != len(vectors):
        raise ValueError('one embedding per prepared input required')
    pairs = [dict(a=a['id'], b=b['id'], **pair_scores(root, x, y))
             for a, x in zip(rows, vectors) for b, y in zip(rows, vectors)]
    lookup = {(pair['a'], pair['b']): pair for pair in pairs}
    direction, comparisons = [], []
    for start in range(0, len(rows), 3):
        broader, narrower, alternative = rows[start:start+3]
        context = {key: broader[key] for key in ('case', 'domain', 'wording')}
        b, n, a = broader['id'], narrower['id'], alternative['id']
        forward, reverse, candidate = lookup[b, n], lookup[n, b], lookup[a, n]
        f, r, c = (pair['angle_degrees'] for pair in (forward, reverse, candidate))
        direction.append(dict(
            **context, broader=b, narrower=n, forward_degrees=f, reverse_degrees=r,
            reverse_minus_forward=None if f is None or r is None else r-f,
            forward_cosine=forward['cosine'], reverse_cosine=reverse['cosine']))
        comparisons.append(dict(
            **context, broader=b, narrower=n, alternative=a,
            broader_degrees=f, alternative_degrees=c,
            alternative_minus_broader_degrees=None if f is None or c is None else c-f,
            broader_cosine=forward['cosine'], alternative_cosine=candidate['cosine'],
            broader_minus_alternative_cosine=forward['cosine']-candidate['cosine']))
    return dict(pairs=pairs, direction=direction, candidate_comparisons=comparisons)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('fixture', 'output', 'snapshot'):
        parser.add_argument('--' + flag, type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    if args.output.exists():
        parser.error('output exists; preserve previous runs')
    frozen_fixture = args.fixture.read_bytes()
    fixture = json.loads(frozen_fixture)
    rows = prepare_inputs(fixture)
    snapshot = args.snapshot.resolve(strict=True)
    if (not snapshot.is_dir() or snapshot.name != MODEL_REVISION
            or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('snapshot must be the exact cached model ID and revision')
    if not (snapshot / 'pytorch_model.bin').is_file():
        raise ValueError('cached released pytorch_model.bin is required')
    model_files = {str(path.relative_to(snapshot)): sha256(path)
                   for path in sorted(snapshot.rglob('*')) if path.is_file()}
    runner = Path(__file__).resolve()
    mask_runner = Path(hierarcaps_mask_probe.__file__).resolve()
    provenance = dict(fixture_sha256=sha256(args.fixture), runner_sha256=sha256(runner),
                      mask_runner_sha256=sha256(mask_runner))
    args.output.mkdir(parents=True, exist_ok=False)
    save_json(args.output / 'inputs.json', rows)
    for name, content in (('fixture.json', frozen_fixture), (runner.name, runner.read_bytes()),
                          (mask_runner.name, mask_runner.read_bytes())):
        with (args.output / name).open('xb') as stream:
            stream.write(content)
    provenance['inputs_sha256'] = sha256(args.output / 'inputs.json')
    save_json(args.output / 'input-provenance.json', provenance)

    import torch
    from transformers import AutoTokenizer, CLIPTextModelWithProjection
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    print('Inputs frozen. Loading the cached released encoder offline; CPU, two threads.', flush=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model, loading = CLIPTextModelWithProjection.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, weights_only=True,
        use_safetensors=False, output_loading_info=True, attn_implementation='eager',
        torch_dtype=torch.float32)
    verify_loading(loading)
    model = model.to(device='cpu', dtype=torch.float32).eval()
    # Same author-defined empty-string origin as HRC02, not a category description.
    texts = [''] + [row['model_input'] for row in rows]
    embeddings, token_counts = [], []
    loaded = time.monotonic()
    print('Encoding ' + str(len(rows)) + ' verbatim descriptions and the empty-string root.', flush=True)
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
    analysis = analyze_scores(rows, root, vectors)
    embedding_records = [dict(**row, token_count=count, embedding=vector,
                              distance_from_root=math.dist(root, vector))
                         for row, vector, count in zip(rows, vectors, token_counts[1:])]
    save_json(args.output / 'embeddings.json', dict(root=root, root_text='',
                                                   root_token_count=token_counts[0],
                                                   vectors=embedding_records))
    save_json(args.output / 'scores.json', analysis.pop('pairs'))
    save_json(args.output / 'checks.json', analysis)
    # /proc reports this process's actual high-water mark, unlike inherited ru_maxrss.
    memory = next(line.split() for line in Path('/proc/self/status').read_text().splitlines()
                  if line.startswith('VmHWM:'))
    if memory[2] != 'kB':
        raise ValueError('unexpected /proc/self/status VmHWM units')
    config = dict(
        **provenance, experiment_id='HRC03', model_id=MODEL_ID, model_revision=MODEL_REVISION,
        snapshot=str(snapshot), model_files=model_files,
        parameters=sum(parameter.numel() for parameter in model.parameters()), dimension=len(root),
        loading=loading, max_tokens=model.config.max_position_embeddings,
        packages={package: importlib.metadata.version(package) for package in
                  ('torch', 'transformers', 'huggingface_hub', 'tokenizers', 'safetensors')},
        cpu_threads=2, cpu_interop_threads=1, batch_size=4, dtype='float32', device='cpu', seed=0,
        attention_implementation='eager', local_files_only=True, trust_remote_code=False,
        weights_only=True, truncation=False, loading_seconds=loaded-started,
        inference_seconds=encoded-loaded, runtime_seconds=time.monotonic()-started,
        peak_rss_kib=int(memory[1]), peak_rss_source='/proc/self/status VmHWM',
        score_definition='Angle between A-root and B-A for normalized text embeddings. '
                         'Lower supports A as broader than B. Not a probability or calibrated cutoff.',
        comparison_definition='Positive reverse-minus-forward angle supports the declared direction. '
                              'Positive alternative-minus-broader angle supports the declared broader '
                              'candidate; positive broader-minus-alternative cosine supports that '
                              'candidate by symmetric similarity.',
        scope='Category-description transfer diagnostic. No masks, notes, training, '
              'membership changes, or hierarchy construction.')
    save_json(args.output / 'config.json', config)
    print(json.dumps(dict(descriptions=len(rows), pairs=len(rows)**2,
                          inference_seconds=config['inference_seconds'],
                          runtime_seconds=config['runtime_seconds'], peak_rss_kib=config['peak_rss_kib'])))


if __name__ == '__main__':
    main()
