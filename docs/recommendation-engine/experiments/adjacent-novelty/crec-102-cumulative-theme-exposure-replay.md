# CREC-102: Cumulative Theme-Exposure Replay

## Question

Before each of the genuine first `140` Phase 4 presentations, could the frozen
Oracle vectors detect that the current note's broad theme had appeared
repeatedly in recent presentation history?

This was a mechanism check. It did not test human saturation, an exposure
budget, adjacent candidates, or recommendation quality.

## Method

The replay used the exact chronological presentations `1–140`, their stored
document vectors, and both sealed CREC-101 label sets. It did not use ratings,
authors, timestamps, personalizer state, or paid compute.

For presentation `t`, every prior presentation `i` contributed:

`max(0, cosine(v_t, v_i) - m) × 2^(-(t-i)/H)`

where `m` was the median cosine across all unique vector pairs in the frozen
140-note prefix. The primary half-life was `20` presentations. Half-lives `10`
and `40` were directional sensitivity checks.

The human reference used the same decay but counted prior notes carrying the
current note's labeled family. Spearman correlation was measured only at
presentations carrying that family.

At the primary half-life, every result was compared with `10,000`
deterministic permutations. Labels and chronology stayed fixed; complete
document-vector identities were shuffled across presentation positions. This
preserved the real temporal clustering and broke only the relationship between
content and its vector.

## Frozen Decision Rule

Proceed only when:

- both label sets' macro correlations exceeded their null thresholds;
- at least two of the same families exceeded their individual null thresholds
  under both label sets; and
- both sensitivity half-lives remained positive for each macro and every
  family significant under both label sets.

If both macros were testable and neither exceeded its null, stop the formula.
Every other outcome was underdetermined.

## Result

The frozen rule yielded `ProceedToLiveProbe`.

All `10,000` primary null draws were valid for every null-tested metric.

| Label set | Macro Spearman | Null 95th percentile | p-value |
| --- | ---: | ---: | ---: |
| A | `0.8019` | `0.4756` | `0.0001` |
| B | `0.7703` | `0.4726` | `0.0001` |

Every tested family exceeded its vector-identity null under both label sets:

| Family | A rho | A null 95 | A p | B rho | B null 95 | B p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nostr | `0.8122` | `0.6158` | `0.0001` | `0.8122` | `0.6158` | `0.0001` |
| Cryptocurrency | `0.9585` | `0.5831` | `0.0001` | `0.9494` | `0.5747` | `0.0001` |
| LLM/AI | `0.6352` | `0.5429` | `0.0209` | `0.5495` | `0.5385` | `0.0479` |

The LLM/AI result under label set B cleared the frozen threshold narrowly. It
still passed the rule fixed before the result was read.

All macro and family correlations remained positive at both sensitivity
half-lives. Macro rho ranged from `0.6995` to `0.8285`.

## Conclusion

On this frozen sequence, the vector-only score tracked recent recurrence of
the three broad labeled theme families better than unrelated vector
assignments did. This clears the specific prerequisite for testing a short
live adjacent-novelty mechanism.

It does **not** establish that:

- high score means the person is saturated;
- the full-prefix median is a deployable live baseline;
- any particular exposure budget should block a candidate;
- useful underexposed adjacent candidates exist; or
- applying this score improves recommendations.

Those remain separate questions. The two label sets test annotation
robustness, not statistical replication.

## Artifacts

The independently reproduced local run is:

`damus_snapshot/runs/crec-102-cumulative-theme-exposure-replay-v1`

Important identities:

- config SHA-256:
  `c3020456fe598edd6d29e02441df654e0b4303c59cca553946ade9154acab45f`
- JSON report SHA-256:
  `b7e376ccdbc20946977be61c3ec8f494a4b8379c2b3ac1f966f405ffec95803d`
- source CREC-101 report SHA-256:
  `5273e99c555ddc6f6e825b3a8810b1d65ea707a6f48c8fbb73ef186165606297`

The artifact contains exact settings, verified source identities, all
presentation-level exposure traces for half-lives `10`, `20`, and `40`, null
summaries, and the frozen decision. CREC-101 and the full representation were
opened read-only and remain unchanged.
