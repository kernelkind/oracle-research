# Single-fragment factorial mask fidelity

## Question

When a mask selects one recognizable subject, can SSE:

1. ignore a change in the unselected carrier text;
2. recognize a differently worded version of the selected subject; and
3. distinguish that subject from a different subject?

These three changes were varied independently rather than changing wording and
context at the same time.

## Inputs

The experiment used three matched subject pairs, each with three phrasings:

| Subject | Phrasings |
|---|---|
| Beach | `a quiet beach`; `a calm shoreline`; `a peaceful seaside` |
| Windowless office | `a windowless office`; `an office without windows`; `an enclosed workplace` |
| Coffee roasting | `roasting coffee beans`; `heating green coffee beans`; `turning green beans into roasted coffee` |
| Bread baking | `baking a loaf of bread`; `making bread in an oven`; `turning dough into a baked loaf` |
| Bicycle repair | `repairing a bicycle`; `fixing a broken bike`; `performing bicycle maintenance` |
| Watercolor painting | `painting with watercolors`; `creating watercolor artwork`; `making a picture with watercolor paints` |

Every phrase appeared in each of three neutral carriers. For example:

> The first note about ⟦a quiet beach⟧ was filed yesterday.
>
> An archived memo about ⟦a quiet beach⟧ was reviewed today.
>
> This short report about ⟦a quiet beach⟧ was copied twice.

Only the text inside `⟦...⟧` was pooled. The rest remained available to the
encoder as unselected context.

For each vector, the comparison held the candidate wording and context fixed:

> cosine(anchor, same subject) − cosine(anchor, matched different subject)

A positive margin is the desired result. The frozen gate allowed at most one
failure among 18 context-only comparisons, at most one among 18
paraphrase-only comparisons, and at most three among 36 comparisons changing
both.

## Result

**The experiment passed. All 432 predeclared comparisons had positive
margins.**

| Direction | Context changes | Paraphrase changes | Both changes | Smallest margin |
|---|---:|---:|---:|---:|
| Beach | 18/18 | 18/18 | 36/36 | `+0.558456` |
| Windowless office | 18/18 | 18/18 | 36/36 | `+0.321355` |
| Coffee roasting | 18/18 | 18/18 | 36/36 | `+0.304855` |
| Bread baking | 18/18 | 18/18 | 36/36 | `+0.317769` |
| Bicycle repair | 18/18 | 18/18 | 36/36 | `+0.639052` |
| Watercolor painting | 18/18 | 18/18 | 36/36 | `+0.902676` |

The weakest observed comparison still favored the correct subject by more
than `0.30` cosine.

## What this establishes

For these six synthetic, single-fragment subjects, SSE's selected vector was
stable under the tested carrier and wording changes and remained clearly
distinguishable from its matched different subject.

It does not establish the same behavior for arbitrary subjects, real Nostr
language, multiple selected fragments, automatic mask generation, or later
segmentation. Those are separate tests.

The complete fixtures and every unrounded margin are in `experiment.json` and
`analysis.json`; the full 54-by-54 cosine matrix is in `cosine-matrix.csv`.
