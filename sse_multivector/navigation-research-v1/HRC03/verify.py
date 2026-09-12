"""Independent, offline HRC03 artifact verification; does not import either runner.

Run using the cached runtime in a systemd user scope with MemoryMax=6G,
MemorySwapMax=0 and CPUQuota=200%. Only verification.json is produced; the
exclusive write preserves an existing report. This does not change semantic
judgments or create additional scientific observations.
"""

from collections import Counter
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
MODEL_ID = 'malper/hierarcaps-clip-l'
REVISION = 'e3aa199d94c438f98628c9697a0b64ef5760b03c'
FROZEN_SHA256 = 'd3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35'
SCORE_TOLERANCE = 1e-10
EMBEDDING_TOLERANCE = 1e-7
AUTHOR_ANGLE_TOLERANCE = 2e-6


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read(name):
    return json.loads((HERE / name).read_bytes())


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def compare(actual, expected, differences, path=''):
    """Check exact structure/labels; allow only bounded numeric roundoff."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), path)
        for key in expected:
            compare(actual[key], expected[key], differences, path + '/' + key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), path)
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, differences, path + '/' + str(index))
    elif isinstance(expected, float):
        require(isinstance(actual, (int, float)) and math.isfinite(actual), path)
        error = abs(actual - expected)
        differences.append(error)
        require(error <= SCORE_TOLERANCE, path + ': numeric mismatch ' + str(error))
    else:
        require(actual == expected, path)


def resource_limits():
    required_env = dict(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                        TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='2',
                        MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    for key, value in required_env.items():
        require(os.environ.get(key) == value, 'required environment: ' + key)
    raw = Path('/proc/self/cgroup').read_text()
    require('oracle-hrc03-verify.scope' in raw, 'dedicated verification scope required')
    report = dict(environment=required_env, proc_self_cgroup=raw.strip())
    relative = next(line.split(':', 2)[2] for line in raw.splitlines()
                    if line.startswith('0::'))
    directory = Path('/sys/fs/cgroup') / relative.lstrip('/')
    observed = {}
    for name in ('memory.max', 'memory.swap.max', 'cpu.max', 'memory.peak'):
        try:
            observed[name] = (directory / name).read_text().strip()
        except OSError as error:
            observed[name] = dict(unavailable=str(error))
    if isinstance(observed['memory.max'], str):
        require(observed['memory.max'] == str(6 * 1024**3), 'memory limit')
    if isinstance(observed['memory.swap.max'], str):
        require(observed['memory.swap.max'] == '0', 'swap limit')
    if isinstance(observed['cpu.max'], str):
        quota, period = map(int, observed['cpu.max'].split())
        require(quota / period == 2, 'CPU limit')
    report['cgroup_limits'] = observed
    report['systemd_invocation_id'] = subprocess.check_output([
        'systemctl', '--user', 'show', 'oracle-hrc03-verify.scope',
        '--property=InvocationID', '--value'], text=True).strip()
    report['python_command'] = Path('/proc/self/cmdline').read_bytes().decode().split('\0')[:-1]
    return report


def verify():
    started = time.monotonic()
    resources = resource_limits()
    require(not (HERE / 'verification.json').exists(), 'preserve existing verification.json')
    config, fixture = read('config.json'), read('fixture.json')
    inputs, embeddings = read('inputs.json'), read('embeddings.json')
    provenance = read('input-provenance.json')
    file_fields = dict(fixture_sha256='fixture.json', inputs_sha256='inputs.json',
                       runner_sha256='hierarcaps_category_probe.py',
                       mask_runner_sha256='hierarcaps_mask_probe.py')
    require(provenance.keys() == file_fields.keys(), 'provenance fields')
    for field, name in file_fields.items():
        require(digest(HERE / name) == config[field] == provenance[field], name + ' hash')
    require(config['fixture_sha256'] == FROZEN_SHA256, 'frozen fixture hash')
    require((HERE / 'fixture.json').read_bytes() ==
            (HERE.parent / 'hrc03-fixture.json').read_bytes(), 'external frozen fixture bytes')
    for name in ('hierarcaps_category_probe.py', 'hierarcaps_mask_probe.py'):
        require((HERE / name).read_bytes() == (HERE.parents[1] / name).read_bytes(),
                name + ' source snapshot')
    require(fixture['experiment_id'] == 'HRC03' and fixture['model_id'] == MODEL_ID and
            fixture['model_revision'] == REVISION, 'fixture identity')
    require(fixture['status'] == 'frozen_before_scoring', 'fixture status')
    require(len(fixture['cases']) == 30, '30 frozen cases')
    domains = Counter(case['domain'] for case in fixture['cases'])
    require(len(domains) == 5 and set(domains.values()) == {6}, 'six cases in each domain')
    reconstructed = []
    for case in fixture['cases']:
        require(len(case['wordings']) == 2, 'two frozen wordings')
        for number, wording in enumerate(case['wordings'], 1):
            for role in ('broader', 'narrower', 'alternative'):
                text = wording[role]
                require(isinstance(text, str) and bool(text.strip()), 'nonempty frozen text')
                reconstructed.append(dict(id=f"{case['id']}-w{number}-{role}",
                                          case=case['id'], domain=case['domain'],
                                          wording=number, role=role, text=text, model_input=text))
    require(inputs == reconstructed and len(inputs) == 180, 'all verbatim inputs and order')
    require(len({row['id'] for row in inputs}) == 180, 'unique input IDs')
    required_config = dict(experiment_id='HRC03', model_id=MODEL_ID, model_revision=REVISION,
                           parameters=123650304, dimension=768, max_tokens=77,
                           cpu_threads=2, cpu_interop_threads=1, batch_size=4,
                           dtype='float32', device='cpu', seed=0,
                           attention_implementation='eager', local_files_only=True,
                           trust_remote_code=False, weights_only=True, truncation=False,
                           peak_rss_source='/proc/self/status VmHWM')
    for key, value in required_config.items():
        require(config[key] == value, 'configuration: ' + key)
    packages = {name: importlib.metadata.version(name) for name in config['packages']}
    require(packages == config['packages'], 'package versions')
    snapshot = Path(config['snapshot']).resolve(strict=True)
    require(snapshot.name == REVISION and snapshot.parent.name == 'snapshots' and
            snapshot.parent.parent.name == 'models--' + MODEL_ID.replace('/', '--'),
            'exact cached snapshot')
    model_files = {str(path.relative_to(snapshot)): digest(path)
                   for path in sorted(snapshot.rglob('*')) if path.is_file()}
    require(model_files == config['model_files'], 'all checkpoint/tokenizer file hashes')

    import numpy as np
    root = np.asarray(embeddings['root'], dtype=np.float64)
    records = embeddings['vectors']
    require(len(records) == len(inputs), 'embedding record count')
    vectors = np.asarray([record['embedding'] for record in records], dtype=np.float64)
    all_vectors = np.vstack([root, vectors])
    require(all_vectors.shape == (181, 768) and np.isfinite(all_vectors).all(),
            'finite 768-dimensional vectors')
    norm_error = float(np.max(np.abs(np.linalg.norm(all_vectors, axis=1) - 1)))
    require(norm_error <= 1e-5, 'unit-normalized embeddings')
    distances = np.linalg.norm(vectors - root, axis=1)
    distance_errors = []
    for row, record, distance in zip(inputs, records, distances):
        require(record.keys() == row.keys() | {'embedding', 'token_count', 'distance_from_root'},
                'embedding record fields')
        require({key: record[key] for key in row} == row, 'embedding metadata and exact text')
        compare(record['distance_from_root'], float(distance), distance_errors, row['id'])
    require(embeddings['root_text'] == '' and embeddings['root_token_count'] == 2,
            'empty-string root')
    saved_pairs = read('scores.json')
    require(len(saved_pairs) == 32400, 'complete ordered-pair count')
    independent, errors = {}, []
    undefined_self, undefined_other = 0, 0
    for index, (row, vector) in enumerate(zip(inputs, vectors)):
        outward, edges = vector - root, vectors - vector
        denominator = np.linalg.norm(outward) * np.linalg.norm(edges, axis=1)
        cosine = vectors @ vector
        for other, target in enumerate(inputs):
            radians = None
            if denominator[other] > 1e-12:
                value = float(np.dot(outward, edges[other]) / denominator[other])
                radians = math.acos(min(1., max(-1., value)))
            else:
                undefined_self += int(index == other)
                undefined_other += int(index != other)
            expected = dict(a=row['id'], b=target['id'], cosine=float(cosine[other]),
                            angle_radians=radians,
                            angle_degrees=None if radians is None else math.degrees(radians))
            compare(saved_pairs[index * len(inputs) + other], expected, errors, 'pair')
            independent[row['id'], target['id']] = expected
    require(undefined_self == 180 and undefined_other == 0, 'only self angles undefined')
    direction, comparisons = [], []
    for case in fixture['cases']:
        for number in (1, 2):
            b, n, a = [f"{case['id']}-w{number}-{role}"
                       for role in ('broader', 'narrower', 'alternative')]
            forward, reverse, alternative = independent[b, n], independent[n, b], independent[a, n]
            f, r, c = [pair['angle_degrees'] for pair in (forward, reverse, alternative)]
            context = dict(case=case['id'], domain=case['domain'], wording=number)
            direction.append(dict(**context, broader=b, narrower=n, forward_degrees=f,
                                  reverse_degrees=r, reverse_minus_forward=r-f,
                                  forward_cosine=forward['cosine'], reverse_cosine=reverse['cosine']))
            comparisons.append(dict(**context, broader=b, narrower=n, alternative=a,
                                    broader_degrees=f, alternative_degrees=c,
                                    alternative_minus_broader_degrees=c-f,
                                    broader_cosine=forward['cosine'],
                                    alternative_cosine=alternative['cosine'],
                                    broader_minus_alternative_cosine=forward['cosine']-alternative['cosine']))
    check_errors = []
    compare(read('checks.json'), dict(direction=direction, candidate_comparisons=comparisons),
            check_errors, 'checks')
    print('Verified frozen inputs, hashes, norms, all 32,400 scores and 120 saved checks.', flush=True)

    import torch
    from transformers import AutoTokenizer, CLIPModel
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model, loading = CLIPModel.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, weights_only=True,
        use_safetensors=False, output_loading_info=True, attn_implementation='eager',
        torch_dtype=torch.float32)
    require(all(not value for value in loading.values()), 'complete full-model checkpoint loading')
    require(all(not config['loading'][key] for key in ('missing_keys', 'mismatched_keys', 'error_msgs')),
            'complete original text checkpoint loading')
    expected_unused = {name for name in model.state_dict()
                       if not name.startswith(('text_model.', 'text_projection.'))}
    require(set(config['loading']['unexpected_keys']) == expected_unused,
            'original omitted parameters are exactly full-model non-text parameters')
    text_parameters = sum(parameter.numel() for name, parameter in model.named_parameters()
                          if name.startswith(('text_model.', 'text_projection.')))
    require(text_parameters == config['parameters'], 'text parameter count')
    require(model.config.projection_dim == config['dimension'] and
            model.config.text_config.max_position_embeddings == config['max_tokens'],
            'model dimensions and token limit')
    model = model.to(device='cpu', dtype=torch.float32).eval()
    loaded = time.monotonic()
    fresh, token_counts = [], []
    texts = [''] + [row['model_input'] for row in reconstructed]
    print('Reproducing all 181 embeddings through full CLIPModel.get_text_features offline.', flush=True)
    with torch.inference_mode():
        for start in range(0, len(texts), 4):
            tokens = tokenizer(texts[start:start+4], padding=True, truncation=False, return_tensors='pt')
            require(tokens['input_ids'].shape[1] <= model.config.text_config.max_position_embeddings,
                    'no token truncation')
            features = model.get_text_features(**tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            fresh.extend(features.tolist())
            token_counts.extend(tokens['attention_mask'].sum(dim=1).tolist())
    encoded = time.monotonic()
    require(token_counts == [embeddings['root_token_count']] + [row['token_count'] for row in records],
            'all token counts')
    fresh_array = np.asarray(fresh, dtype=np.float64)
    embedding_error = float(np.max(np.abs(fresh_array - all_vectors)))
    require(embedding_error <= EMBEDDING_TOLERANCE, 'full-model embedding reproduction')
    fresh_tensor = torch.tensor(fresh, dtype=torch.float32)
    author_angle_errors = []
    for index, row in enumerate(inputs):
        outward = fresh_tensor[index + 1] - fresh_tensor[0]
        edges = fresh_tensor[1:] - fresh_tensor[index + 1]
        cosine = torch.nn.functional.cosine_similarity(outward.unsqueeze(0), edges, dim=-1)
        angles = torch.acos(cosine.clamp(-1, 1)).tolist()
        for other, target in enumerate(inputs):
            if index != other:
                author_angle_errors.append(abs(angles[other] -
                    saved_pairs[index * len(inputs) + other]['angle_radians']))
    require(max(author_angle_errors) <= AUTHOR_ANGLE_TOLERANCE, 'author-style float32 angles')
    # Refresh the cgroup peak after inference; the startup sample is not a run peak.
    resources = resource_limits()
    resources['cgroup_snapshot_stage'] = 'after full-model inference and numerical verification'
    memory = next(line.split() for line in Path('/proc/self/status').read_text().splitlines()
                  if line.startswith('VmHWM:'))
    require(memory[2] == 'kB', 'VmHWM unit')
    artifact_names = [*file_fields.values(), 'input-provenance.json', 'config.json',
                      'embeddings.json', 'scores.json', 'checks.json']
    return dict(
        experiment_id='HRC03', verification_passed=True,
        scope='Independent numerical/provenance verification only; no semantic relabeling.',
        verifier_sha256=digest(Path(__file__)),
        artifact_sha256={name: digest(HERE / name) for name in artifact_names},
        frozen_fixture_and_source_snapshots_match=True,
        exact_verbatim_inputs_verified=len(inputs), cases_by_domain=dict(domains),
        checkpoint_hashes_match=True, model_files=model_files,
        configuration_verified=required_config, packages=packages,
        saved_embeddings_verified=len(all_vectors), max_unit_norm_error=norm_error,
        max_root_distance_absolute_difference=max(distance_errors),
        independently_recomputed_pairs=len(saved_pairs), undefined_self_angles=undefined_self,
        undefined_nonself_angles=undefined_other, max_score_absolute_difference=max(errors),
        score_absolute_tolerance=SCORE_TOLERANCE,
        independently_recomputed_direction_checks=len(direction),
        independently_recomputed_candidate_comparisons=len(comparisons),
        max_check_absolute_difference=max(check_errors),
        full_model_class='transformers.CLIPModel', full_model_loading=loading,
        full_model_parameters=sum(parameter.numel() for parameter in model.parameters()),
        original_loading_unused_parameters_verified=len(expected_unused),
        independent_full_model_embeddings_compared=len(fresh),
        full_model_embeddings_bit_identical=bool(np.array_equal(fresh_array, all_vectors)),
        max_embedding_absolute_difference=embedding_error,
        embedding_absolute_tolerance=EMBEDDING_TOLERANCE,
        token_counts_verified=True, maximum_token_count=max(token_counts),
        independent_author_style_float32_angles_compared=len(author_angle_errors),
        max_author_style_angle_difference_radians=max(author_angle_errors),
        author_style_angle_tolerance_radians=AUTHOR_ANGLE_TOLERANCE,
        full_model_inference_seconds=encoded-loaded, runtime_seconds=time.monotonic()-started,
        current_process_vm_hwm_kib=int(memory[1]), peak_rss_source='/proc/self/status VmHWM',
        resources=resources, downloads=False, paid_resources=False)


if __name__ == '__main__':
    report = verify()
    with (HERE / 'verification.json').open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in (
        'verification_passed', 'independently_recomputed_pairs',
        'independent_full_model_embeddings_compared', 'max_embedding_absolute_difference',
        'max_author_style_angle_difference_radians', 'current_process_vm_hwm_kib')}), flush=True)
