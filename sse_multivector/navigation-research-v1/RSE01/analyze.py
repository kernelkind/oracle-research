"""Rebuild RSE01 descriptive summaries and complete case tables from saved scores."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def main():
    fixture = read(HERE / 'fixture.json')
    rows = read(HERE / 'inputs.json')
    rse = read(HERE / 'checks.json')
    hrc = read(HERE.parent / 'HRC03/checks.json')
    hrc_pairs = {(x['a'], x['b']): x for x in read(HERE.parent / 'HRC03/scores.json')}
    old = {(x['case'], x['wording']): x for x in hrc['candidate_comparisons']}
    inputs = {x['id']: x for x in rows}
    matched = {(x['case'], x['broader_wording']): x for x in rse['candidate_comparisons']}
    groups = defaultdict(list)
    for row in rse['cross_wording_comparisons']:
        groups[row['case']].append(row)
    domains = []
    for domain in dict.fromkeys(x['domain'] for x in rows):
        subset = [x for x in rse['candidate_comparisons'] if x['domain'] == domain]
        case_ids = list(dict.fromkeys(x['case'] for x in subset))
        domains.append(dict(
            domain=domain, comparisons=len(subset),
            rse_entailment=sum(x['broader_minus_alternative_entailment'] > 0 for x in subset),
            rse_cosine=sum(x['broader_minus_alternative_cosine'] > 0 for x in subset),
            hrc_angle=sum(old[x['case'], x['broader_wording']]['alternative_minus_broader_degrees'] > 0
                          for x in subset),
            hrc_cosine=sum(old[x['case'], x['broader_wording']]['broader_minus_alternative_cosine'] > 0
                           for x in subset),
            rse_forward_direction=sum(x['forward_minus_reverse'] > 0 for x in subset),
            rse_both_matched_wordings=sum(all(x['broader_minus_alternative_entailment'] > 0
                                                for x in subset if x['case'] == case) for case in case_ids),
            rse_all_eight_wordings=sum(all(x['broader_minus_alternative_entailment'] > 0
                                             for x in groups[case]) for case in case_ids)))

    def choice(value):
        return 'intended' if value > 0 else 'alternative' if value < 0 else 'tie'

    transitions = []
    for x in rse['candidate_comparisons']:
        previous = old[x['case'], x['broader_wording']]
        transitions.append(dict(case=x['case'], wording=x['broader_wording'],
                                rse=choice(x['broader_minus_alternative_entailment']),
                                rse_cosine=choice(x['broader_minus_alternative_cosine']),
                                hierarcaps=choice(previous['alternative_minus_broader_degrees'])))
    stability = []
    for case, combinations in groups.items():
        hrc_wins = sum(hrc_pairs[x['alternative'], x['narrower']]['angle_degrees'] >
                       hrc_pairs[x['broader'], x['narrower']]['angle_degrees'] for x in combinations)
        stability.append(dict(case=case, rse=sum(x['broader_minus_alternative_entailment'] > 0 for x in combinations),
                              rse_cosine=sum(x['broader_minus_alternative_cosine'] > 0 for x in combinations),
                              hierarcaps=hrc_wins))
    result = dict(domains=domains, transitions=transitions, wording_stability=stability,
                  source_sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                 for name in ('fixture.json', 'inputs.json', 'checks.json', 'scores.json')})
    (HERE / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')

    lines = [
        '# RSE01 — Every category comparison', '',
        'These are the exact constructed category descriptions from HRC03, not original notes or masks. '
        'S/E/P/R/F identify software, economics, political ideas, relationships and food cases. '
        'Each case has two wordings. “Intended” records the frozen pre-score judgment; it is not a model output.', '',
        'RSE entailment: higher favors the proposed parent. RSE cosine: higher means more similar, without direction. '
        'HierarCaps angle: lower favors the proposed parent. Do not compare numerical scales between models. '
        'All columns use the exact child and candidate text shown.', '',
        'The eight-combination table also mixes the two wordings of the child, intended parent and alternative. '
        'Its numbers identify wording 1 or 2 immediately above it. These are wording checks, not independent examples.', '',
        'Qualified interpretations remain in [the HRC03 review](../HRC03/RESULTS.md#all-unexpected-matched-choices). '
        'RSE01 does not silently rewrite those judgments.', '']
    for case in fixture['cases']:
        lines += ['## ' + case['id'], '', case['rationale'], '']
        for index, wording in enumerate(case['wordings'], 1):
            x = matched[case['id'], index]
            lines += ['### Wording ' + str(index), '', '**Child:** ' + wording['narrower'], '',
                      '| Proposed parent | RSE entailment ↑ | RSE cosine ↑ | HierarCaps angle ↓ |',
                      '| --- | ---: | ---: | ---: |']
            for role in ('broader', 'alternative'):
                text = inputs[x[role]]['text'].replace('|', '\\|')
                hrc_angle = hrc_pairs[x[role], x['narrower']]['angle_degrees']
                lines.append('| ' + text + ' | ' + f"{x[role + '_entailment']:.6f} | " +
                             f"{x[role + '_cosine']:.6f} | {hrc_angle:.4f}° |")
            lines += ['', 'RSE selected the **' + choice(x['broader_minus_alternative_entailment']) +
                      '** candidate. Forward-minus-reverse entailment: ' + f"{x['forward_minus_reverse']:+.6f}.", '']
        lines += ['### Changing the wording independently', '',
                  '| Child wording | Intended-parent wording | Alternative wording | RSE intended | RSE alternative | RSE choice |',
                  '| ---: | ---: | ---: | ---: | ---: | --- |']
        for x in groups[case['id']]:
            lines.append(f"| {x['narrower_wording']} | {x['broader_wording']} | {x['alternative_wording']} | " +
                         f"{x['broader_entailment']:.6f} | {x['alternative_entailment']:.6f} | " +
                         choice(x['broader_minus_alternative_entailment']) + ' |')
        lines += ['']
    (HERE / 'CASES.md').write_text('\n'.join(lines).rstrip() + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
