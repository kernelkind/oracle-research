# SSE Evidence Index

## Scope

These experiments test whether SSE vectors preserve the atomic-subject
relationships needed by the content hierarchy.

SSE does not discover masks. For each input, another process supplies:

1. the complete note; and
2. the selected source-token positions.

SSE processes the complete note, averages the contextual token representations
at the selected positions, and applies its learned output transformation.

The evidence below is conditional on the supplied masks. It does not validate
automatic subject extraction, fine segmentation, hierarchy construction, or
navigation quality.

## Controlled Synthetic Evidence

### Single-fragment masks

- The
  [`../../sse_multivector/mask-fidelity-single-fragment-factorial-v3/result/analysis.md`](../../sse_multivector/mask-fidelity-single-fragment-factorial-v3/result/analysis.md)
  passed all 432 predeclared context, paraphrase, and different-subject
  comparisons.
- The
  [`../../sse_multivector/mask-fidelity-single-fragment-boundary-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-single-fragment-boundary-v1/result/analysis.md)
  passed all 72 comparisons.
- The complete readable cases are also recorded in
  [`SSE-SINGLE-FRAGMENT-MASK-EXPERIMENTS.md`](SSE-SINGLE-FRAGMENT-MASK-EXPERIMENTS.md).

These results show strong behavior on the tested synthetic subjects. They do
not establish arbitrary real-note performance.

### Multi-fragment masks

- The
  [`../../sse_multivector/mask-fidelity-multifragment-requirements-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-multifragment-requirements-v1/result/analysis.md)
  passed its fragment-count, boundary, wording, redundancy, and unselected-text
  comparisons.
- A stricter
  [`../../sse_multivector/mask-fidelity-multifragment-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-multifragment-v1/result/analysis.md)
  failed one of three families, but complete and fragmented masks behaved
  similarly; the evidence did not attribute the family failure to
  fragmentation.
- The complete readable cases are also recorded in
  [`SSE-MULTI-FRAGMENT-MASK-EXPERIMENTS.md`](SSE-MULTI-FRAGMENT-MASK-EXPERIMENTS.md).

### Known limits

- [`../../sse_multivector/mask-fidelity-location-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-location-v1/result/analysis.md)
  passed all four predeclared comparisons despite unrelated surrounding text.
- [`../../sse_multivector/mask-fidelity-relationship-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-relationship-v1/result/analysis.md)
  failed all four comparisons: SSE did not reliably distinguish who chased
  whom when the same entities and action appeared in reversed relationships.
- [`../../sse_multivector/mask-fidelity-compound-subject-neighborhood-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-compound-subject-neighborhood-v1/result/analysis.md)
  passed two of three subject families. The solar-powered-greenhouse family
  narrowly failed its local-neighbor rule.

The synthetic evidence therefore supports some subject relationships but not a
general claim that SSE preserves every relation expressed by selected text.

## Real-Note Evidence

The
[`SSE-REAL-NOTE-HOLDOUT-EXPERIMENT.md`](SSE-REAL-NOTE-HOLDOUT-EXPERIMENT.md)
passed three of four predeclared comparisons. The hard Windows/Linux case
failed, leaving nearby technical-subject resolution unresolved.

The later
[`../../sse_multivector/mask-fidelity-real-note-transfer-v5/result/analysis.md`](../../sse_multivector/mask-fidelity-real-note-transfer-v5/result/analysis.md)
passed six of eight comparisons and failed its strict overall criterion:

- mining-hardware noise passed;
- pervasive software telemetry passed one of two comparisons; and
- solar-powered mining passed three of four comparisons.

Two counterfactuals clarified those failures without erasing them:

- Selecting the direct telemetry statement made the intended telemetry edge
  strongest in its comparison
  ([`../../sse_multivector/mask-fidelity-telemetry-mask-counterfactual-v1/result/analysis.md`](../../sse_multivector/mask-fidelity-telemetry-mask-counterfactual-v1/result/analysis.md)).
- Removing unselected context moved the solar-mining comparison to an almost
  exact tie with its solar-only control
  ([`../../sse_multivector/mask-fidelity-solar-context-ablation-v4/result/analysis.md`](../../sse_multivector/mask-fidelity-solar-context-ablation-v4/result/analysis.md)).

## Current Conclusion

Within these bounded tests, SSE often preserves recognizable atomic-subject
similarity across wording, mask boundaries, multiple fragments, and changed
surrounding text. It also has observed failures, especially for reversed
relationships and some nearby or compound subjects.

That is enough to continue testing the architecture, not enough to treat SSE
geometry as validated. The current dependency is to fix the subject-mask
generation boundary and then evaluate one frozen fine-segmentation candidate
with the synthetic suite.
