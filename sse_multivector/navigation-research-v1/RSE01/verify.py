"""Independently verify RSE01 with the pinned author's model implementation.

Read-only verification: emit JSON to stdout; preserve the original artifacts.
The caller stores the emitted report separately after successful completion.
"""
import gc
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
from pathlib import Path
import sys
import time
import types
import urllib.request


HERE = Path(__file__).resolve().parent
REVISION = '2fc202227bf95bd12ce3b41acbbfefb1a45c983f'
MODEL_REVISION = 'b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5'
FIXTURE_HASH = 'd3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35'
WEIGHTS_HASH = '76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39'
SOURCE_BLOBS = {
    'rse_src/model.py': 'a70cc8ff11ba47b8d773fdd8b6ea357c9f941a0a',
    'rse_src/model_utils.py': '802ec550c89f1f682028ab23535acccb97225d4f',
    'rse_src/inference.py': 'e8bd897f51f8a3000a6b6b34b60841879dd72e0f',
    'scripts/demo_inference_local.sh': '1e6cad04d729067f77eeb1c3f925c729ba6e3b9c',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_json(name):
    return json.loads((HERE / name).read_text())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    started = time.monotonic()
    artifact_names = ('config.json', 'fixture.json', 'inputs.json', 'embeddings.json',
                      'scores.json', 'checks.json', 'rse_category_probe.py')
    before = {name: digest(HERE / name) for name in artifact_names}
    config, fixture, rows, saved, scores, checks = (
        read_json(name) for name in artifact_names[:6])
    require(before['fixture.json'] == config['fixture_sha256'] == FIXTURE_HASH,
            'frozen fixture identity')
    require(before['fixture.json'] == digest(HERE.parent / 'hrc03-fixture.json'),
            'original HRC03 fixture identity')
    require(before['inputs.json'] == config['inputs_sha256'], 'input artifact hash')
    require(before['rse_category_probe.py'] == config['runner_sha256'], 'frozen runner hash')
    require(digest(HERE.parent.parent / 'hierarcaps_category_probe.py') ==
            config['input_preparation_sha256'], 'input preparation source hash')
    require(config['model_revision'] == MODEL_REVISION and config['author_revision'] == REVISION,
            'pinned revisions')
    require(config['model_id'] == 'binwang/RSE-RoBERTa-large-10-relations', 'model identity')
    expected_rows = []
    for case in fixture['cases']:
        for wording, descriptions in enumerate(case['wordings'], 1):
            for role in ('broader', 'narrower', 'alternative'):
                text = descriptions[role]
                expected_rows.append(dict(id=f"{case['id']}-w{wording}-{role}",
                                          case=case['id'], domain=case['domain'],
                                          wording=wording, role=role, text=text,
                                          model_input=text))
    require(rows == expected_rows and len(rows) == 180, 'independently rebuilt plain inputs')
    ids = [row['id'] for row in rows]
    require(len(set(ids)) == len(ids), 'unique input IDs')
    for row, record in zip(rows, saved['vectors'], strict=True):
        require({key: record[key] for key in row} == row, 'embedding metadata matches input')
    require(saved['relation_index'] == config['relation_index'] == 0, 'entailment row zero')

    cgroup_relative = next(line.split(':', 2)[2] for line in
                           Path('/proc/self/cgroup').read_text().splitlines()
                           if line.startswith('0::'))
    cgroup = Path('/sys/fs/cgroup') / cgroup_relative.lstrip('/')
    limits = {name: (cgroup / name).read_text().strip()
              for name in ('memory.max', 'memory.swap.max', 'cpu.max')}
    require(limits['memory.max'] == str(6 * 1024**3), '6 GiB cgroup limit')
    require(limits['memory.swap.max'] == '0', 'no swap cgroup limit')
    quota, period = map(int, limits['cpu.max'].split())
    require(quota / period == 2, 'two CPU cgroup quota')

    sources, provenance = {}, {}
    for name, expected_blob in SOURCE_BLOBS.items():
        url = f'https://raw.githubusercontent.com/BinWang28/RSE/{REVISION}/{name}'
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(blob == expected_blob, 'pinned author source blob: ' + name)
        sources[name] = raw.decode()
        provenance[name] = dict(url=url, git_blob=blob, sha256=hashlib.sha256(raw).hexdigest(),
                                bytes=len(raw))
    removed_import = 'from turtle import forward\n'
    require(sources['rse_src/model_utils.py'].count(removed_import) == 1,
            'only the audited unused turtle import is removed')
    source_utils = sources['rse_src/model_utils.py'].replace(removed_import, '', 1)
    provenance['rse_src/model_utils.py']['executed_sha256'] = hashlib.sha256(
        source_utils.encode()).hexdigest()
    provenance['rse_src/model_utils.py']['in_memory_change'] = (
        'Remove exactly one unused line: from turtle import forward; no other source changes.')
    utilities = types.ModuleType('model_utils')
    utilities.__file__ = provenance['rse_src/model_utils.py']['url']
    sys.modules['model_utils'] = utilities
    exec(compile(source_utils, utilities.__file__, 'exec'), utilities.__dict__)
    author = types.ModuleType('rse01_author_model')
    author.__file__ = provenance['rse_src/model.py']['url']
    exec(compile(sources['rse_src/model.py'], author.__file__, 'exec'), author.__dict__)

    import numpy as np
    import torch
    from transformers import AutoTokenizer, RobertaConfig
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    snapshot = Path(config['snapshot']).resolve(strict=True)
    require(snapshot.name == MODEL_REVISION, 'snapshot revision directory')
    for name, checksum in config['model_files'].items():
        require(digest(snapshot / name) == checksum, 'model file checksum: ' + name)
    require(config['model_files']['pytorch_model.bin'] == WEIGHTS_HASH, 'published weight checksum')
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    lengths = [len(tokenizer(row['model_input'], truncation=False)['input_ids']) for row in rows]
    require(max(lengths) <= 32, 'all sentences fit author demo setting without truncation')
    require(lengths == [record['token_count'] for record in saved['vectors']], 'all token counts')

    state = torch.load(snapshot / 'pytorch_model.bin', weights_only=True, map_location='cpu', mmap=True)
    model_config = RobertaConfig.from_pretrained(snapshot, local_files_only=True)
    model_config._attn_implementation = 'eager'
    positions = state.pop('roberta.embeddings.position_ids')
    require(torch.equal(positions, torch.arange(model_config.max_position_embeddings).expand(1, -1)),
            'legacy saved position IDs are exactly the reconstructed current buffer')
    model_args = types.SimpleNamespace(mode='RSE', pooler_type='cls', num_rel=10, mlp_only_train=False)
    model = author.RoBERTaForRSE(model_config, args=model_args)
    loading = model.load_state_dict(state, strict=True)
    require(not loading.missing_keys and not loading.unexpected_keys, 'strict complete author model loading')
    parameters = sum(parameter.numel() for parameter in model.parameters())
    require(parameters == config['parameters'] == 355369984, 'complete parameter count')
    model.eval()
    relation = model.rel_emb.embedding.weight[0].detach().clone()
    expected_relation = torch.tensor(saved['relation'], dtype=torch.float32)
    require(torch.equal(relation, expected_relation), 'exact saved learned entailment relation')
    loaded = time.monotonic()
    print('Author model strictly loaded; independently encoding all 180 inputs.', flush=True)
    pieces = []
    with torch.inference_mode():
        for start in range(0, len(rows), 4):
            texts = [row['model_input'] for row in rows[start:start+4]]
            # Author demo calls batch_encode_plus with max_length=32. Every input
            # was checked above, so this must not truncate any fixture text.
            tokens = tokenizer.batch_encode_plus(texts, return_tensors='pt', padding=True,
                                                  truncation=True, max_length=32)
            require(tokens['attention_mask'].sum(dim=1).tolist() == lengths[start:start+4],
                    'no input was truncated or otherwise reformatted')
            outputs = model(**tokens, output_hidden_states=True, return_dict=False, sent_emb=True)
            pieces.append(outputs[1].clone())
    embeddings = torch.cat(pieces)
    expected_embeddings = torch.tensor([record['embedding'] for record in saved['vectors']],
                                       dtype=torch.float32)
    embedding_difference = (embeddings - expected_embeddings).abs().max().item()
    require(torch.equal(embeddings, expected_embeddings), 'bit-identical author embeddings for every input')
    encoded = time.monotonic()
    del model, state, outputs, pieces, positions
    gc.collect()

    raw = embeddings.numpy().astype(np.float64)
    shifted = raw + relation.numpy().astype(np.float64)
    normalized = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    normalized_shifted = shifted / np.linalg.norm(shifted, axis=1, keepdims=True)
    cosines = normalized @ normalized.T
    entailments = normalized_shifted @ normalized.T
    author_cosine = torch.nn.CosineSimilarity(dim=-1)
    with torch.inference_mode():
        tensor_entailments = torch.stack([author_cosine(vector + relation, embeddings)
                                         for vector in embeddings]).numpy()
        tensor_cosines = torch.stack([author_cosine(vector, embeddings)
                                     for vector in embeddings]).numpy()
    indexes = {identifier: index for index, identifier in enumerate(ids)}
    require(len(scores) == len(ids)**2 == 32400, 'complete ordered pair count')
    seen, pair_errors = set(), {'cosine': 0.0, 'entailment': 0.0}
    for score in scores:
        pair = score['first'], score['second']
        require(pair not in seen, 'no duplicate saved pair')
        seen.add(pair)
        first, second = map(indexes.__getitem__, pair)
        for field, matrix in (('cosine', cosines), ('entailment', entailments)):
            error = abs(score[field] - float(matrix[first, second]))
            pair_errors[field] = max(pair_errors[field], error)
            require(error < 1e-12, 'independent score replay: ' + repr(pair))

    def comparison(case, broader_wording, narrower_wording, alternative_wording):
        broader = f"{case['id']}-w{broader_wording}-broader"
        narrower = f"{case['id']}-w{narrower_wording}-narrower"
        alternative = f"{case['id']}-w{alternative_wording}-alternative"
        b, n, a = (indexes[identifier] for identifier in (broader, narrower, alternative))
        forward, reverse, other = entailments[n, b], entailments[b, n], entailments[n, a]
        return dict(case=case['id'], domain=case['domain'], broader=broader, narrower=narrower,
                    alternative=alternative, broader_wording=broader_wording,
                    narrower_wording=narrower_wording, alternative_wording=alternative_wording,
                    broader_entailment=float(forward), reverse_entailment=float(reverse),
                    alternative_entailment=float(other), forward_minus_reverse=float(forward-reverse),
                    broader_minus_alternative_entailment=float(forward-other),
                    broader_cosine=float(cosines[n, b]), alternative_cosine=float(cosines[n, a]),
                    broader_minus_alternative_cosine=float(cosines[n, b]-cosines[n, a]))

    expected_checks = {
        'candidate_comparisons': [comparison(case, wording, wording, wording)
                                  for case in fixture['cases'] for wording in (1, 2)],
        'cross_wording_comparisons': [comparison(case, *wordings) for case in fixture['cases']
                                     for wordings in itertools.product((1, 2), repeat=3)],
    }
    comparison_errors, precision_changes = {}, {}
    for kind, expected in expected_checks.items():
        require(len(checks[kind]) == len(expected), 'comparison count: ' + kind)
        maximum_error, choice_changes, direction_changes, cosine_changes = 0.0, [], [], []
        for actual, replay in zip(checks[kind], expected, strict=True):
            require(set(actual) == set(replay), 'comparison fields')
            for key, value in replay.items():
                if isinstance(value, float):
                    error = abs(actual[key] - value)
                    maximum_error = max(maximum_error, error)
                    require(error < 1e-12, 'comparison scalar: ' + key)
                else:
                    require(actual[key] == value, 'comparison identity: ' + key)
            b, n, a = (indexes[replay[key]] for key in ('broader', 'narrower', 'alternative'))
            identity = {key: replay[key] for key in ('broader', 'narrower', 'alternative')}
            def sign(value):
                return (value > 0) - (value < 0)
            for changes, field, new in (
                (choice_changes, 'broader_minus_alternative_entailment',
                 float(tensor_entailments[n, b] - tensor_entailments[n, a])),
                (direction_changes, 'forward_minus_reverse',
                 float(tensor_entailments[n, b] - tensor_entailments[b, n])),
                (cosine_changes, 'broader_minus_alternative_cosine',
                 float(tensor_cosines[n, b] - tensor_cosines[n, a])),
            ):
                if sign(actual[field]) != sign(new):
                    changes.append(dict(**identity, saved_margin=actual[field], author_float32_margin=new))
        comparison_errors[kind] = maximum_error
        precision_changes[kind] = dict(parent_choice_changes=choice_changes,
                                        direction_changes=direction_changes,
                                        baseline_cosine_choice_changes=cosine_changes)
    precision_errors = dict(
        entailment=float(np.max(np.abs(tensor_entailments.astype(np.float64) - entailments))),
        cosine=float(np.max(np.abs(tensor_cosines.astype(np.float64) - cosines))))
    require(max(precision_errors.values()) < 1e-5, 'float32 and float64 cosine agreement')
    after = {name: digest(HERE / name) for name in artifact_names}
    require(after == before, 'all original run artifacts preserved')
    memory = next(line.split() for line in Path('/proc/self/status').read_text().splitlines()
                  if line.startswith('VmHWM:'))
    require(memory[2] == 'kB', 'peak RSS units')
    report = dict(
        experiment_id='RSE01', status='pass', verifier_sha256=digest(Path(__file__)),
        original_artifact_hashes=before, original_artifacts_unchanged=True,
        author_revision=REVISION, author_sources=provenance,
        model_revision=MODEL_REVISION, weight_sha256=WEIGHTS_HASH,
        implementation='Actual pinned RoBERTaForRSE.forward -> author sentemb_forward; '
                       'strict load_state_dict; no copied runner encoding or scoring functions.',
        loading=dict(missing_keys=loading.missing_keys, unexpected_keys=loading.unexpected_keys,
                     validated_removed_legacy_position_ids=True, parameters=parameters,
                     mode='RSE', pooler_type='cls', num_rel=10, mlp_only_train=False),
        fixture_sha256=FIXTURE_HASH, inputs=180, cases=len(fixture['cases']),
        domains=len({case['domain'] for case in fixture['cases']}),
        plain_inputs_independently_rebuilt=True, all_token_counts_identical=True,
        minimum_tokens=min(lengths), maximum_tokens=max(lengths), truncated_inputs=0,
        token_counts=lengths, author_embeddings_bit_identical=True,
        embedding_maximum_absolute_difference=embedding_difference,
        learned_entailment_relation_bit_identical=True, dimensions=int(embeddings.shape[1]),
        ordered_scores_replayed=len(scores), independent_float64_score_max_abs_errors=pair_errors,
        matched_comparisons_replayed=len(expected_checks['candidate_comparisons']),
        cross_wording_comparisons_replayed=len(expected_checks['cross_wording_comparisons']),
        comparison_max_abs_errors=comparison_errors,
        author_float32_vs_independent_float64_max_abs_errors=precision_errors,
        author_float32_decision_changes=precision_changes,
        cgroup_limits=limits, cpu_threads=torch.get_num_threads(),
        cpu_interop_threads=torch.get_num_interop_threads(), batch_size=4, device='cpu',
        dtype='float32', attention_implementation='eager', training=False,
        packages={package: importlib.metadata.version(package) for package in
                  ('torch', 'transformers', 'huggingface_hub', 'tokenizers', 'numpy')},
        source_and_loading_seconds=loaded-started, author_inference_seconds=encoded-loaded,
        total_seconds=time.monotonic()-started, peak_rss_kib=int(memory[1]),
        limitation='Numerical/runtime verification, not evidence that expected category judgments '
                   'or general-category transfer are universally correct.')
    print('VERIFICATION_JSON=' + json.dumps(report, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
