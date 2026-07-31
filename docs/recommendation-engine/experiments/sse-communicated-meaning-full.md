# SSE Communicated-Meaning Full Diagnostic

## Question

Does representing each coherent point a note communicates avoid the failures
caused by representing every narrow subject fragment, while retaining useful
semantic relationships across notes?

This is an exploratory diagnostic over the same frozen 32 notes as the
narrowest-subject run. It is not an accuracy estimate or a pass/fail gate.

## Inputs

The locked takeaway prompt and locked takeaway-mask prompt were applied to all
32 notes. They produced:

- 73 communicated takeaways;
- 94 exact supporting fragments;
- zero `unsupported` masks.

No generated takeaway or mask received a subjective correction pass. The
production validator mechanically verified the frozen note order and content,
the exact prompt pair, unique IDs and labels, and every fragment's presence,
occurrence, source order, and non-overlap.

The complete source-bound input is
[`communicated-meaning-full-proposal-v1.json`](../../../sse_multivector/communicated-meaning-full-proposal-v1.json).
The schema retains the historical field name `subjects`, but every label in
this proposal is a communicated takeaway. Labels are report metadata and never
enter the encoder.

## Execution

The run reused the exact worker, immutable container, tokenizer, pooling rule,
and full-dimensional Sentence-T5-base SSE checkpoint used by the earlier
32-note and three-note runs. It produced 73 finite, nonzero 768-dimensional
vectors and all 2,628 unordered cosine values. Deterministic replay succeeded.

The immutable run is preserved at
[`communicated-meaning-full-v1`](../../../sse_multivector/baselines/communicated-meaning-full-v1/).

## Measurements

The new run contains 96 same-note pairs and 2,532 cross-note pairs. All 96
same-note pairs use disjoint selected tokens; the coherent takeaways eliminated
the overlapping and nested masks present in the narrowest-subject run.

| Pair group | Count | Median | Mean | p95 |
|---|---:|---:|---:|---:|
| Takeaway, cross-note | 2,532 | 0.0536 | 0.0760 | 0.3314 |
| Narrowest subject, cross-note | 16,753 | 0.0266 | 0.0454 | 0.2699 |
| Takeaway, same-note disjoint | 96 | 0.2088 | 0.2454 | 0.5461 |
| Narrowest subject, same-note disjoint | 522 | 0.1945 | 0.2145 | 0.5550 |

Cross-note cosine shifted upward generally. That is not itself evidence of
better accuracy: the representation units and number of comparisons changed,
and no independently labeled expected-neighbor set exists.

### Previously observed lexical failures

The following comparisons target four concrete failures discovered in the
earlier run. The coherent-takeaway value uses the corresponding combined
meaning rather than the earlier isolated fragment.

| Comparison | Narrow subject | Takeaway |
|---|---:|---:|
| Day/night miner control versus finishing a book tonight | 0.4513 | 0.2994 |
| Four rooftop panels versus the book title *The Fourth Revolution* | 0.4281 | 0.0691 |
| Charging a car versus switching a child's car seat | 0.4828 | 0.1169 |
| Ledger tracking code versus Molly containing no proprietary code | 0.5444 | 0.3150 |

These four values fell from a mean of `0.4767` to `0.2001`. They are post-hoc
diagnostic cases, not a representative error rate.

### Semantic controls

Four previously useful relationships remained strong:

| Comparison | Narrow subject | Takeaway |
|---|---:|---:|
| FOSS sovereignty versus an almost entirely FOSS software stack | 0.7181 | 0.7177 |
| Proprietary-OS telemetry versus Ledger interaction tracking | 0.6258 | 0.5954 |
| Recurring BitAxe fan noise versus Avalon/Bitaxe noise trends | 0.7064 | 0.6724 |
| Future solar generation versus a solar-powered greenhouse | 0.7394 | 0.6769 |

Their mean changed from `0.6974` to `0.6656`. Within this small, inspected set,
coherent takeaways reduced the targeted lexical failures substantially while
retaining most of the useful semantic signal.

## Qualitative Findings

Some cross-note relationships were precise and useful:

- recurring BitAxe fan noise versus an Avalon growing louder despite cleaning:
  `0.6724`;
- FOSS as technological sovereignty versus an almost entirely FOSS software
  stack: `0.7177`;
- two quiet parent-child reading experiences: `0.4394`.

The complete analysis also contains strong incorrect or overly coarse
neighbors:

- an easy-to-prepare affogato versus a picky-eating child: `0.5487`;
- a repeatedly loud fan versus a long-chirping wren: `0.4665`;
- unspecified actors wanting control versus automatic backups: `0.4175`;
- timed miner control versus automatic app locking: `0.4040`.

The complete notes, generated takeaways, masks, rankings, and analysis for
these failures are collected in
[Five SSE Failures](./sse-communicated-meaning-failure-cases.md).

Some results are also consistent with unrelated surrounding-note context
affecting masked vectors. A takeaway about choices made without pressure ranked
several coffee takeaways high while its source note also discussed coffee. A
non-consumption-based retirement takeaway remained close to solar and miner
takeaways while its source note discussed a greenhouse.

## Interpretation

The run provides strong directional evidence for coherent communicated
takeaways over maximally narrow subject fragments. It removes redundant mask
overlap, sharply weakens the four known lexical failures, and preserves the
four semantic controls.

It does not establish that this SSE checkpoint reliably represents the exact
meaning being communicated. Its geometry still follows broad subject matter,
surface analogies, and unselected full-note context often enough to produce
wrong reciprocal nearest neighbors even when better candidates exist.

The defensible conclusion is:

> Coherent takeaways are better SSE inputs than overly atomic subject
> fragments, but the released SSE representation is not yet a reliable map of
> communicated meaning.

The remaining load-bearing ambiguity is whether the largest errors primarily
come from the model's use of complete-note context or from its underlying
semantic geometry.
