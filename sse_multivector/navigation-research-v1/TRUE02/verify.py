"""Independently replay saved TRUE02 calculations; no neural model or writes."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parent
SNAPSHOT = Path('/home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988')
FIXTURE_HASH = 'a514757d32adc0c31f859d0d8a912870cec4c7296ee07d231d9edc7608098e21'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    fixture = json.loads((ROOT / 'fixture.json').read_text())
    inputs = json.loads((ROOT / 'inputs.json').read_text())
    rows = [json.loads(line) for line in (ROOT / 'scores.jsonl').read_text().splitlines()]
    started = json.loads((ROOT / 'started.json').read_text())
    config = json.loads((ROOT / 'config.json').read_text())
    completion = json.loads((ROOT / 'completion.json').read_text())
    analysis = json.loads((ROOT / 'analysis.json').read_text())
    assert digest(ROOT / 'fixture.json') == started['fixture_sha256'] == FIXTURE_HASH
    assert digest(ROOT.parent / 'true02-fixture.json') == FIXTURE_HASH
    assert digest(ROOT / 'inputs.json') == started['inputs_sha256']
    for filename, field in (('scores.jsonl', 'scores_sha256'),
                            ('first-token-logits.npy', 'logits_sha256'),
                            ('analysis.json', 'analysis_sha256'),
                            ('DECISIONS.md', 'decisions_sha256')):
        assert digest(ROOT / filename) == completion[field]
    for name, expected in started['source_sha256'].items():
        assert digest(ROOT / name) == expected
        assert digest(ROOT.parent.parent / name) == expected
    prior_config = json.loads((ROOT.parent / 'TRUE01/config.json').read_text())
    for field in ('model_id', 'revision', 'parameter_count', 'label_token_ids', 'dtype',
                  'device', 'threads', 'batch_size', 'max_input_tokens', 'truncation',
                  'decision', 'displayed_score', 'seed', 'packages'):
        assert config[field] == prior_config[field], field
    assert config['threshold'] == started['threshold'] == fixture['threshold'] == 0.142
    assert config['generation'] == dict(do_sample=False, num_beams=1, max_new_tokens=3,
                                        return_dict_in_generate=True, output_logits=True)
    assert json.loads((ROOT / 'model-files.json').read_text()) == json.loads(
        (ROOT.parent / 'TRUE01/model-files.json').read_text())
    assert not any(config['loading'].get(key) for key in
                   ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs'))
    assert len(inputs) == len(rows) == started['pairs'] == completion['pairs'] == 150

    expected_rows = []
    for domain in fixture['domains']:
        positives = {tuple(pair) for pair in domain['contains']}
        for a_id, b_id in itertools.permutations(domain['categories'], 2):
            a, b = domain['categories'][a_id], domain['categories'][b_id]
            positive = (a_id, b_id) in positives
            reverse = (b_id, a_id) in positives
            kind = ('equivalent' if reverse else 'strict-containment') if positive else (
                'reversed-containment' if reverse else 'noncontaining')
            expected_rows.append(dict(id=f'{a_id}-contains-{b_id}', domain=domain['id'],
                a_id=a_id, b_id=b_id, a=a, b=b, expected=positive, kind=kind, format='topic',
                model_input=f'premise: This text is about {b}. hypothesis: This text is about {a}.'))
    assert inputs == expected_rows
    prior_inputs = json.loads((ROOT.parent / 'TRUE01/inputs.json').read_text())
    previous_pairs = {(row['a'], row['b']) for row in prior_inputs}
    assert not any((row['a'], row['b']) in previous_pairs for row in rows)

    tokenizer = AutoTokenizer.from_pretrained(SNAPSHOT, local_files_only=True, trust_remote_code=False)
    assert {s: tokenizer.encode(s, add_special_tokens=False) for s in ('0', '1')} == {
        '0': [3, 632], '1': [209]}
    logits = np.load(ROOT / 'first-token-logits.npy', allow_pickle=False)
    assert logits.shape == (150, 32128) and logits.dtype == np.float32
    assert np.isfinite(logits).all()
    shifted = logits.astype(np.float64) - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    probabilities = exp / exp.sum(axis=1, keepdims=True)
    numeric_error = 0.0
    for index, (original, row) in enumerate(zip(expected_rows, rows)):
        assert all(row[key] == value for key, value in original.items())
        assert tokenizer.encode(row['model_input']) == row['token_ids']
        assert len(row['token_ids']) <= 512
        generated = row['generated_token_ids']
        assert generated[0] == 0 and generated[1] == int(logits[index].argmax())
        text = tokenizer.decode(generated, skip_special_tokens=True)
        assert text == row['generated_text']
        terminated = 1 in generated[1:]
        predicted = {'0': False, '1': True}.get(text) if terminated else None
        assert row['predicted'] is predicted and row['eos_terminated'] is terminated
        assert row['logit_0_first_token'] == float(logits[index, 3])
        assert row['logit_1_first_token'] == float(logits[index, 209])
        replay_score = float(probabilities[index, 209])
        numeric_error = max(numeric_error, abs(row['entailment_score'] - replay_score))
        assert row['threshold_predicted'] is (replay_score > 0.142)
    assert numeric_error < 1e-12

    def confusion(subset, field):
        result = dict(total=len(subset), correct=sum(r[field] == r['expected'] for r in subset),
            positive=sum(r['expected'] for r in subset), negative=sum(not r['expected'] for r in subset),
            true_positive=sum(r[field] is True and r['expected'] for r in subset),
            true_negative=sum(r[field] is False and not r['expected'] for r in subset),
            false_positive=sum(r[field] is True and not r['expected'] for r in subset),
            false_negative=sum(r[field] is False and r['expected'] for r in subset),
            unresolved=sum(r[field] is None for r in subset))
        result['accuracy'] = result['correct'] / result['total']
        return result

    diagnostics = {}
    for label, subset in [('overall', rows)] + [(d['id'], [r for r in rows if r['domain'] == d['id']])
                                                for d in fixture['domains']]:
        observed = {name: confusion(subset, field) for name, field in
                    (('native', 'predicted'), ('cutoff', 'threshold_predicted'))}
        assert observed == (analysis['overall'] if label == 'overall' else analysis['domain'][label])
        positive = [r for r in subset if r['expected']]
        negative = [r for r in subset if not r['expected']]
        low = min(positive, key=lambda r: r['entailment_score'])
        high = max(negative, key=lambda r: r['entailment_score'])
        inversions = sum(p['entailment_score'] < n['entailment_score'] for p in positive for n in negative)
        ties = sum(p['entailment_score'] == n['entailment_score'] for p in positive for n in negative)
        ordering = analysis['score_ordering']['overall'] if label == 'overall' else analysis['score_ordering']['domain'][label]
        assert ordering['inversions'] == inversions and ordering['ties'] == ties
        assert ordering['minimum_positive']['score'] == low['entailment_score']
        assert ordering['maximum_negative']['score'] == high['entailment_score']
        assert ordering['separation_gap'] == low['entailment_score'] - high['entailment_score']
        pairs = {}
        for row in subset:
            pairs.setdefault(tuple(sorted((row['a_id'], row['b_id']))), []).append(row)
        pair_counts = analysis['unordered_pairs']['overall'] if label == 'overall' else analysis['unordered_pairs']['domain'][label]
        assert pair_counts['total'] == len(pairs) and all(len(pair) == 2 for pair in pairs.values())
        for name, field in (('native', 'predicted'), ('cutoff', 'threshold_predicted')):
            assert pair_counts[name+'_correct'] == sum(all(r[field] == r['expected'] for r in pair)
                                                       for pair in pairs.values())
        diagnostics[label] = dict(**observed, lowest_positive={k: low[k] for k in ('id', 'a', 'b', 'entailment_score')},
            highest_negative={k: high[k] for k in ('id', 'a', 'b', 'entailment_score')}, inversions=inversions,
            ties=ties, strictly_separated=low['entailment_score'] > high['entailment_score'])
    for kind, expected in analysis['kind'].items():
        subset = [r for r in rows if r['kind'] == kind]
        assert expected == {name: confusion(subset, field) for name, field in
                            (('native', 'predicted'), ('cutoff', 'threshold_predicted'))}
    print(json.dumps(dict(verified_pairs=len(rows), no_model_loaded=True,
        fixture_input_and_source_hashes_match=True, configuration_matches_TRUE01=True,
        unseen_pairs=True, tokenization_generation_and_native_answers_match=True,
        frozen_cutoff_and_analysis_match=True, max_score_replay_error=numeric_error,
        diagnostics=diagnostics), indent=2))


if __name__ == '__main__':
    main()
