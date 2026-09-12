"""RSE01: released RSE directional scoring on the unchanged HRC03 descriptions."""
import argparse
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import time

from hierarcaps_category_probe import prepare_inputs
from hierarcaps_mask_probe import save_json, sha256


MODEL_ID = 'binwang/RSE-RoBERTa-large-10-relations'
MODEL_REVISION = 'b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5'
WEIGHTS_SHA256 = '76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39'
FIXTURE_SHA256 = 'd3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35'
AUTHOR_REVISION = '2fc202227bf95bd12ce3b41acbbfefb1a45c983f'


def pair_scores(first, second, relation):
    if not first or not (len(first) == len(second) == len(relation)):
        raise ValueError('equal nonempty vector dimensions required')
    if not all(math.isfinite(x) for values in (first, second, relation) for x in values):
        raise ValueError('finite vectors required')
    translated = [x + r for x, r in zip(first, relation)]
    first_norm, second_norm, translated_norm = (
        math.hypot(*first), math.hypot(*second), math.hypot(*translated))
    if min(first_norm, second_norm, translated_norm) < 1e-8:
        raise ValueError('nonzero source and translated vectors required')
    cosine = sum(a * b for a, b in zip(first, second)) / (first_norm * second_norm)
    entailment = sum(a * b for a, b in zip(translated, second)) / (translated_norm * second_norm)
    return dict(cosine=cosine, entailment=entailment)


def project_cls(hidden, weight, bias):
    import torch.nn.functional as functional
    return functional.linear(hidden[:, 0, :], weight, bias).tanh()


def analyze_scores(rows, vectors, relation):
    if not rows or len(rows) != len(vectors) or len(rows) % 6:
        raise ValueError('one vector per input and two three-role wordings per case required')
    pairs = [dict(first=a['id'], second=b['id'], **pair_scores(x, y, relation))
             for a, x in zip(rows, vectors) for b, y in zip(rows, vectors)]
    lookup = {(pair['first'], pair['second']): pair for pair in pairs}

    def compare(broader, narrower, alternative):
        b, n, a = broader['id'], narrower['id'], alternative['id']
        forward, reverse, other = lookup[n, b], lookup[b, n], lookup[n, a]
        return dict(case=broader['case'], domain=broader['domain'],
                    broader=b, narrower=n, alternative=a,
                    broader_wording=broader['wording'], narrower_wording=narrower['wording'],
                    alternative_wording=alternative['wording'],
                    broader_entailment=forward['entailment'], alternative_entailment=other['entailment'],
                    broader_minus_alternative_entailment=forward['entailment']-other['entailment'],
                    reverse_entailment=reverse['entailment'],
                    forward_minus_reverse=forward['entailment']-reverse['entailment'],
                    broader_cosine=forward['cosine'], alternative_cosine=other['cosine'],
                    broader_minus_alternative_cosine=forward['cosine']-other['cosine'])

    matched = [compare(*rows[start:start+3]) for start in range(0, len(rows), 3)]
    crossed = []
    for start in range(0, len(rows), 6):
        case_rows = rows[start:start+6]
        for b, n, a in itertools.product((0, 1), repeat=3):
            crossed.append(compare(case_rows[3*b], case_rows[3*n+1], case_rows[3*a+2]))
    return dict(pairs=pairs, candidate_comparisons=matched, cross_wording_comparisons=crossed)


def load_checkpoint(snapshot):
    import torch
    from transformers import RobertaConfig, RobertaModel

    config = RobertaConfig.from_pretrained(snapshot, local_files_only=True)
    config._attn_implementation = 'eager'
    state = torch.load(snapshot / 'pytorch_model.bin', map_location='cpu', weights_only=True, mmap=True)
    encoder_state = {key.removeprefix('roberta.'): value for key, value in state.items()
                     if key.startswith('roberta.')}
    extras = set(state) - {'roberta.' + key for key in encoder_state}
    expected = {'mlp.dense.weight', 'mlp.dense.bias', 'rel_emb.embedding.weight'}
    if extras != expected:
        raise ValueError('unexpected checkpoint heads: ' + repr(extras))
    # Transformers 4.21 persisted position_ids; 4.57 reconstructs the same buffer.
    old_positions = encoder_state.pop('embeddings.position_ids', None)
    if old_positions is not None and not torch.equal(
            old_positions, torch.arange(config.max_position_embeddings).expand((1, -1))):
        raise ValueError('unexpected saved position IDs')
    model = RobertaModel(config, add_pooling_layer=False)
    loading = model.load_state_dict(encoder_state, strict=True)
    weight, bias, relations = (state[key] for key in
                              ('mlp.dense.weight', 'mlp.dense.bias', 'rel_emb.embedding.weight'))
    dimension = config.hidden_size
    if weight.shape != (dimension, dimension) or bias.shape != (dimension,) or relations.shape != (10, dimension):
        raise ValueError('unexpected RSE head dimensions')
    return model.eval(), weight, bias, relations, dict(
        missing_keys=loading.missing_keys, unexpected_keys=loading.unexpected_keys,
        validated_legacy_position_buffer=old_positions is not None,
        state_tensors=len(state), encoder_tensors=len(encoder_state))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('fixture', 'output', 'snapshot'):
        parser.add_argument('--' + flag, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve prior results')
    started = time.monotonic()
    if sha256(args.fixture) != FIXTURE_SHA256:
        raise ValueError('requires the unchanged HRC03 fixture')
    rows = prepare_inputs(json.loads(args.fixture.read_text()))
    snapshot = args.snapshot.resolve(strict=True)
    if (snapshot.name != MODEL_REVISION or snapshot.parent.name != 'snapshots'
            or snapshot.parent.parent.name != 'models--' + MODEL_ID.replace('/', '--')):
        raise ValueError('requires the pinned RSE snapshot')
    files = {str(path.relative_to(snapshot)): sha256(path)
             for path in sorted(snapshot.rglob('*')) if path.is_file()}
    if files.get('pytorch_model.bin') != WEIGHTS_SHA256:
        raise ValueError('checkpoint checksum mismatch')

    import torch
    from transformers import AutoTokenizer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    lengths = [len(tokenizer(row['model_input'], truncation=False)['input_ids']) for row in rows]
    if max(lengths) > 32:
        raise ValueError('fixture exceeds author 32-token setting; truncation forbidden')
    args.output.mkdir(parents=True, exist_ok=False)
    save_json(args.output / 'inputs.json', rows)
    for name, data in (('fixture.json', args.fixture.read_bytes()),
                       (Path(__file__).name, Path(__file__).read_bytes())):
        with (args.output / name).open('xb') as output:
            output.write(data)
    print('Inputs frozen. Loading RSE: CPU, two threads, batch four.', flush=True)
    model, weight, bias, relations, loading = load_checkpoint(snapshot)
    loaded = time.monotonic()
    vectors = []
    with torch.inference_mode():
        for start in range(0, len(rows), 4):
            tokens = tokenizer([row['model_input'] for row in rows[start:start+4]],
                               padding=True, truncation=False, return_tensors='pt')
            hidden = model(**tokens).last_hidden_state
            vectors.extend(project_cls(hidden, weight, bias).tolist())
            if (start + 4) % 40 == 0:
                print('Encoded ' + str(start + 4) + '/' + str(len(rows)), flush=True)
    encoded = time.monotonic()
    relation = relations[0].tolist()
    save_json(args.output / 'embeddings.json', dict(
        relation_index=0, relation_name='Entailment', relation=relation,
        vectors=[dict(**row, token_count=count, embedding=vector)
                 for row, count, vector in zip(rows, lengths, vectors)]))
    print('Encoding complete. Scoring every ordered pair.', flush=True)
    analysis = analyze_scores(rows, vectors, relation)
    save_json(args.output / 'scores.json', analysis.pop('pairs'))
    save_json(args.output / 'checks.json', analysis)
    memory = next(line.split() for line in Path('/proc/self/status').read_text().splitlines()
                  if line.startswith('VmHWM:'))
    config = dict(
        experiment_id='RSE01', fixture_experiment_id='HRC03', fixture_sha256=FIXTURE_SHA256,
        model_id=MODEL_ID, model_revision=MODEL_REVISION, snapshot=str(snapshot), model_files=files,
        author_revision=AUTHOR_REVISION, runner_sha256=sha256(Path(__file__)),
        input_preparation_sha256=sha256(Path(__file__).with_name('hierarcaps_category_probe.py')),
        inputs_sha256=sha256(args.output / 'inputs.json'),
        parameters=sum(p.numel() for p in model.parameters()) + weight.numel() + bias.numel() + relations.numel(),
        dimension=len(relation), relation_index=0, loading=loading, max_tokens=32,
        packages={package: importlib.metadata.version(package) for package in
                  ('torch', 'transformers', 'huggingface_hub', 'tokenizers', 'safetensors')},
        cpu_threads=2, cpu_interop_threads=1, batch_size=4, dtype='float32', device='cpu', seed=0,
        attention_implementation='eager', local_files_only=True, trust_remote_code=False,
        weights_only=True, truncation=False, normalized_before_translation=False,
        loading_seconds=loaded-started, inference_seconds=encoded-loaded,
        runtime_seconds=time.monotonic()-started, peak_rss_kib=int(memory[1]),
        peak_rss_source='/proc/self/status VmHWM',
        score_definition='cosine(z(child) + relation[0], z(parent)); raw CLS-linear-tanh vectors. '
                         'Higher favors entailment; not a probability or calibrated cutoff.',
        scope='Frozen category-description transfer diagnostic. No training or hierarchy changes.')
    save_json(args.output / 'config.json', config)
    print(json.dumps({key: config[key] for key in
                      ('parameters', 'dimension', 'inference_seconds', 'runtime_seconds', 'peak_rss_kib')}))


if __name__ == '__main__':
    main()
