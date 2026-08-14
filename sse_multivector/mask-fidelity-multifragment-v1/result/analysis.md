# Multi-fragment mask fidelity

## Question

If the same subject is selected as either one continuous span or two separated
fragments, does SSE produce the same useful neighborhood?

Each source sentence was encoded four times while its text and tokenization
remained identical. For example:

> This index entry concerns Python tools for data visualization.

| Mode | Selected text |
|---|---|
| Complete | ⟦Python tools for data visualization⟧ |
| Fragmented | ⟦Python tools⟧ for ⟦data visualization⟧ |
| First component | ⟦Python tools⟧ |
| Second component | ⟦data visualization⟧ |

The test used five phrasings of each of three subjects: Python data
visualization, solar greenhouse heating, and electric-vehicle battery
recycling. Comparisons excluded every alternate mask of the same sentence, so
identical source text could not win retrieval by itself.

## Result

**The strict overall criterion failed in one of three families. The evidence
does not show fragmentation causing that failure.**

| Family | Complete/fragmented distinguishable from components | Neighborhood agreement | Base neighborhood useful | Strict result |
|---|---:|---:|---:|---|
| Python data visualization | 5/5 | Pass | Pass | Pass |
| Solar greenhouse heating | 5/5 | Pass | Pass | Pass |
| Electric-vehicle battery recycling | 5/5 | Pass | Fail | Fail |

Across all 15 sentences:

- Complete-to-fragmented cosine ranged from `0.980665` to `0.998667`.
- Every complete/fragmented pair was closer than either component-only mask of
  its own sentence. The smallest margin was `+0.078536`.
- Their top-four neighbor sets overlapped by at least three items in every
  comparison.
- The minimum positive-versus-component ordering agreement was `0.90625`.

Thus, changing only the mask from one span to two fragments did not materially
change any tested neighborhood.

## Why the strict result still failed

Both mask forms failed on the same electric-vehicle phrase:

> This index entry concerns ⟦battery recovery from electric vehicles⟧.

Fragmented form:

> This index entry concerns ⟦battery recovery⟧ from ⟦electric vehicles⟧.

For the gallery using complete masks, the nearest four were:

| Complete query | Fragmented query | Candidate | Class |
|---:|---:|---|---|
| `0.955869` | `0.955876` | `battery recycling for electric vehicles` | Complete subject |
| `0.934319` | `0.925690` | `recycling batteries from electric vehicles` | Complete subject |
| `0.924210` | `0.930579` | `electric-vehicle batteries` | Component only |
| `0.921424` | `0.931260` | `electric-vehicle batteries` | Component only |

The complete and fragmented queries therefore made essentially the same
mistake: both returned two complete peers and two component-only controls,
rather than the required three complete peers.

This may reflect the phrasing `battery recovery`, the strength of
`electric-vehicle batteries`, or SSE's geometry. This experiment does not
separate those explanations. It does show that removing connector words from
the mask was not the observed cause.

## What this establishes

For the tested two-fragment masks, fragmentation preserved the behavior of the
corresponding contiguous mask. Two subject families also formed useful local
neighborhoods under both forms. The strict pilot remains a failure because the
third subject family was not a useful neighborhood under either form.

This does not test masks with three or more fragments, real Nostr language,
automatic mask generation, or segmentation.

The complete fixtures, rankings, and unrounded metrics are in
`experiment.json` and `analysis.json`; the full 60-by-60 cosine matrix is in
`cosine-matrix.csv`.
