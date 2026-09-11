# Scientific interpretation after failure review

The frozen experiment and its formal `21/24` result remain unchanged. This
document records the later review of what those three failed comparisons
actually tested.

## Retirement comparison

The selected text communicates that something is beginning a
non-consumption-based retirement. The failed comparison required the vector to
prefer a greenhouse-specific refinement over a minimalism-specific refinement.
Both are valid refinements of the selected meaning, and the note does not
establish the exact greenhouse relationship asserted by the preferred
references. This comparison is non-diagnostic for SSE.

## Rooftop comparison

The constructed input removed the original note's explicit statement that the
objects were solar panels. The preferred references retained the omitted
`solar` and `photovoltaic` meaning. Requiring SSE to recover evidence removed
from the constructed input does not provide a clean context-grounding test.
This comparison is non-diagnostic for SSE.

## Miner comparison

The selected vector remained strongly aligned with starting a miner when
surplus solar energy is available. It lost the frozen median comparison by
`0.0123` to the adjacent meaning of measuring that miner's solar-energy use,
but won the same comparison under the mean. The reverse measurement vector
correctly preferred measurement. This is reference-aggregation sensitivity,
not evidence that another part of the note replaced the selected meaning.

## Valid evidence

- All three self-contained baselines preserved their selected meaning.
- All six unrelated-context interventions preserved their selected meaning.
- The same ambiguous control phrase changed correctly between technology
  surveillance and financial control when its resolving context changed.
- Every selected meaning in the two mixed real notes remained strongly aligned
  with its intended meaning. No valid case showed unrelated note content taking
  over a selected vector.

## Conclusion

> Within this small pilot, SSE produced separate, context-grounded vectors for
> the supplied masks without any valid observed blending failure.

This is feasibility evidence conditional on the supplied masks. This run
obtained those masks through its frozen takeaway pipeline; it does not establish
corpus-wide reliability, automatic extraction quality, fine-region formation,
region labeling, or hierarchy construction.

A later pilot tested whether these vectors could be hard-partitioned into
coherent fine semantic regions. It found real recurring semantic cores but did
not validate one global hard partition; its result is recorded in
[`../../docs/recommendation-engine/experiments/sse-fine-region-partition-pilot.md`](../../docs/recommendation-engine/experiments/sse-fine-region-partition-pilot.md).
