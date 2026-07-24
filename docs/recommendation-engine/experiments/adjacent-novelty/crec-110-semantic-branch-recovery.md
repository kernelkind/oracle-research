# CREC-110: Semantic-Branch Recovery

## Question

Does the frozen single-vector Oracle preserve at least two recoverable semantic
directions around one already-valued note that contains several explicit
themes?

This is a representation-and-candidate-supply diagnostic. It does not test a
branch-selection algorithm, a feed, adaptive learning, or recommendation
quality.

## Frozen Source

The source note was selected from prior positive ratings by its text alone,
before its neighbors or vectors were inspected. It was rated `6`:

> You need 3 daily wins:
> * A physical win (walking, running, lifting, swimming)
> * A Mental win (Reading, writing, creating, learning)
> * A Spiritual win (Praying, meditating, studying, growing)
> --Brendon Burchard

Its event ID is
`e66fbd85be2c2333e7f598361fe22647783674dc3a2db03b11825afa169d0b60`.
The cached `similar_notes` response contains the requested top `1,024`
candidates from all `3,530,455` represented notes.

## Method

- Deterministically sample `40` candidates from each `256`-rank quartile of
  the cached response.
- Give two independent labelers differently ordered text-only packets. Hide
  event IDs, ranks, scores, vectors, and the other label set.
- Independence was enforced procedurally with separate context-isolated
  labelers. The sealed artifact proves that two separately ordered, complete
  label sets existed; it cannot prove producer identity or context isolation.
- Label each note with every substantive `physical`, `mental`, and
  `spiritual` theme. An empty set means neither. Unreadable, primarily
  non-English, or context-dependent text is unusable.
- Seal both complete label sets before reading any vectors.
- Use only notes assigned exactly one theme in the primary geometry test.
  Multi-theme notes remain supply facts but cannot act as exclusive anchors.
- Require at least `8` exclusive notes for a theme to qualify.
- Remove candidate distance from the hidden query center before comparing
  directions. For candidate document vectors `xᵢ`, `xⱼ` and their cached
  query cosines `cᵢ`, `cⱼ`, the directional cosine is:

  `(xᵢ·xⱼ - cᵢcⱼ) / (sqrt(1-cᵢ²) sqrt(1-cⱼ²))`

- Measure mean-anchor AUROC and compare it with `10,000` deterministic label
  permutations constrained within rank quartiles.
- Test every qualifying theme pair directly against one another. Do not infer
  pairwise separation merely because both themes separate from a third.

The frozen decision could be:

- `RecoverableBranches`: both label sets support at least one common,
  statistically separated theme pair;
- `NoRecoverableBranches`: enough exclusive supply exists, but the required
  separation does not;
- `Underdetermined`: the sample lacks enough common exclusive supply to test a
  pair.

## Result

The frozen decision was `Underdetermined`.

The two label sets agreed exactly on `137/160` complete multi-label judgments.
Their supply was:

| Label set | Physical only | Mental only | Spiritual only | Multi-theme | Neither | Unusable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | `4` | `57` | `6` | `35` | `57` | `1` |
| B | `5` | `60` | `7` | `36` | `50` | `2` |

Physical and spiritual content was not absent. Counting both exclusive and
multi-theme assignments, labeler A found each in `27` notes; labeler B found
physical in `29` and spiritual in `28`. However, neither theme reached the
predeclared minimum of eight exclusive notes under either label set.

Mental/learning was the only qualifying theme. Among exclusive-theme notes,
its geometry was above the rank-stratified permutation null under both label
sets:

| Label set | Mental AUROC | Null 95th percentile | Permutation p-value |
| --- | ---: | ---: | ---: |
| A | `0.6525` | `0.5817` | `0.0018` |
| B | `0.6937` | `0.5779` | `0.0001` |

After the decision was fixed, unblinded review confirmed clear physical-only
and spiritual-only examples at multiple ranks. It also confirmed why exclusive
supply was sparse: many retrieved notes combined exercise, learning,
mindfulness, religion, or self-improvement in the same text.

## Meaning

The diagnostic provides evidence that, among the sampled exclusive-theme
notes, the Oracle preserves a separable mental/learning direction around this
source note. It does not establish a second recoverable direction.

It also does not show that physical or spiritual directions are absent. The
predeclared test could not evaluate them because the `160`-note sample contained
too few exclusive anchors. Therefore this is neither a pass nor a failure of
the single-vector branch hypothesis.

No branch-walking mechanism is authorized by this result. A possible later
test could increase the blind, rank-balanced sample from the same already
computed top-`1,024` response while retaining the same labels and decision
method. That successor has not been approved.

## Artifacts

The auditable local run is:

`damus_snapshot/runs/crec-110-semantic-branches-v1`

The report is bound to the sealed labels, private mapping, cached response,
ordered event IDs, and representation version. The original Phase 3 corpus,
response, ordered IDs, and rented representation remained unchanged.

The published report was recomputed through the sealed inputs and Oracle
vectors without writing any artifact. Its SHA-256 is
`55ee862328f21a1a925e93b0f9fc31234047bd4e8ca1a697d9ecdd40e81e35ad`.
