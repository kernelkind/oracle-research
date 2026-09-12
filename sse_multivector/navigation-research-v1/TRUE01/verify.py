"""Read-only, independent replay of TRUE01 inputs, generation, logits, and counts.

No model loading or network access. Prints JSON; never rewrites the run.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parent
SNAPSHOT = Path('/home/dev/.cache/huggingface/hub/models--google--t5_xxl_true_nli_mixture/snapshots/aa6cfe1dd4257853bfdd772992045f41bfc14988')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    inputs = json.loads((ROOT / 'inputs.json').read_text())
    rows = [json.loads(line) for line in (ROOT / 'scores.jsonl').read_text().splitlines()]
    start = json.loads((ROOT / 'started.json').read_text())
    completion = json.loads((ROOT / 'completion.json').read_text())
    config = json.loads((ROOT / 'config.json').read_text())
    analysis = json.loads((ROOT / 'analysis.json').read_text())
    fixture = json.loads((ROOT / 'fixture.json').read_text())
    cases = {case['id']: case for case in fixture['cases']}
    assert digest(ROOT / 'fixture.json') == start['fixture_sha256']
    assert digest(ROOT / 'inputs.json') == start['inputs_sha256']
    assert digest(ROOT / 'scores.jsonl') == completion['scores_sha256']
    assert digest(ROOT / 'first-token-logits.npy') == completion['logits_sha256']
    assert digest(ROOT.parent.parent / 'true_category_probe.py') == start['runner_sha256']
    assert len(inputs) == len(rows) == completion['pairs'] == 180
    assert config['label_token_ids'] == {'0': [3, 632], '1': [209]}
    tokenizer = AutoTokenizer.from_pretrained(SNAPSHOT, local_files_only=True, trust_remote_code=False)
    logits = np.load(ROOT / 'first-token-logits.npy', allow_pickle=False)
    assert logits.shape == (180, 32128) and logits.dtype == np.float32
    assert np.isfinite(logits).all()
    shifted = logits.astype(np.float64) - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    probabilities = exp / exp.sum(axis=1, keepdims=True)
    numeric_error = 0.
    role_pairs = {'forward': ('broader', 'narrower'), 'reverse': ('narrower', 'broader'),
                  'alternative': ('alternative', 'narrower'),
                  'alternative-reverse': ('narrower', 'alternative')}
    equivalence_roles = {'F02': 'broader', 'S05': 'narrower', 'E02': 'alternative',
                         'P03': 'broader', 'R03': 'alternative'}
    for i, (original, row) in enumerate(zip(inputs, rows)):
        assert all(row[key] == value for key, value in original.items())
        case = cases[row['case']]
        if row['kind'] in role_pairs:
            a_role, b_role = role_pairs[row['kind']]
            wording = case['wordings'][row['wording']-1]
            assert row['a'] == wording[a_role] and row['b'] == wording[b_role]
            assert row['expected'] == (row['kind'] == 'forward')
        else:
            assert row['kind'] == 'equivalent' and row['expected'] is True
            a_index, b_index = (int(v)-1 for v in row['id'].split('-')[-2:])
            role = equivalence_roles[row['case']]
            assert row['a'] == case['wordings'][a_index][role]
            assert row['b'] == case['wordings'][b_index][role]
        a, b = row['a'], row['b']
        if row['format'] == 'topic':
            a, b = 'This text is about ' + a + '.', 'This text is about ' + b + '.'
        else:
            assert row['format'] == 'bare'
        assert row['model_input'] == 'premise: ' + b + ' hypothesis: ' + a
        assert tokenizer.encode(row['model_input']) == row['token_ids']
        generated = row['generated_token_ids']
        assert generated[0] == 0 and generated[1] == int(logits[i].argmax())
        text = tokenizer.decode(generated, skip_special_tokens=True)
        assert text == row['generated_text'] and 1 in generated[1:]
        assert row['predicted'] == {'0': False, '1': True}[text]
        assert row['logit_0_first_token'] == float(logits[i, 3])
        assert row['logit_1_first_token'] == float(logits[i, 209])
        numeric_error = max(numeric_error, abs(row['entailment_score']-float(probabilities[i, 209])))
    assert numeric_error < 1e-12
    diagnostics = {}
    for form in ('topic', 'bare'):
        subset = [r for r in rows if r['format'] == form]
        positives = [r for r in subset if r['expected']]
        negatives = [r for r in subset if not r['expected']]
        observed = dict(total=len(subset), positive=len(positives), negative=len(negatives),
            correct=sum(r['predicted'] == r['expected'] for r in subset),
            false_positive=sum(r['predicted'] for r in negatives),
            false_negative=sum(not r['predicted'] for r in positives), unresolved=0)
        assert observed == analysis[form]['overall']
        low = min(positives, key=lambda r: r['entailment_score'])
        high = max(negatives, key=lambda r: r['entailment_score'])
        diagnostics[form] = dict(**observed,
            lowest_positive={k: low[k] for k in ('id', 'a', 'b', 'entailment_score')},
            highest_negative={k: high[k] for k in ('id', 'a', 'b', 'entailment_score')},
            positive_minus_negative_boundary=low['entailment_score']-high['entailment_score'],
            positive_negative_score_inversions=sum(p['entailment_score'] <= n['entailment_score']
                                                  for p in positives for n in negatives))
    print(json.dumps(dict(verified_pairs=180, fixture_and_artifact_hashes_match=True,
        model_inputs_and_token_ids_match=True, complete_native_labels_and_eos_match=True,
        raw_argmax_matches_native_generation=True, max_probability_replay_error=numeric_error,
        no_model_loaded=True, diagnostics=diagnostics), indent=2))


if __name__ == '__main__':
    main()
