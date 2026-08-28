# Experiment 4: unmasked-context crossover

Status: **draft; notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Holding the resolved atomic subject fixed, unmasked material does not
> materially change membership.

SSE processes the complete note before pooling the selected token positions.
Unmasked text can therefore influence the vector. The requirement is not zero
numeric influence; it is that the surrounding material does not determine the
fine-segment membership.

## Question

When the exact same masked subject appears inside three very different
contexts, does returned membership follow the masked atomic subject rather
than the shared unmasked material?

## Why this fixture exists

This is a balanced `3 × 3` crossover:

- three exact masked subjects;
- three exact unmasked contexts;
- every masked subject appears once in every context;
- every context surrounds all three masked subjects.

The design creates both the desired subject grouping and an equally repeated
but invalid context grouping. No mask wording, subject frequency, or sentence
shape changes across a subject's three treatment instances.

A separate neutral-context prerequisite uses the same three masked subjects.
It first establishes that the candidate separates these subjects when no
competing substantive context is present. Without that prerequisite, a
treatment failure could be ordinary over-merging rather than an effect of the
unmasked material.

## Neutral-context prerequisite notes and masks

### Neutral subject `COFFEE`: roasting green coffee beans

**COFFEE-NEUTRAL-1**

> This note concerns ⟦roasting green coffee beans⟧.

**COFFEE-NEUTRAL-2**

> The selected topic is ⟦roasting green coffee beans⟧.

**COFFEE-NEUTRAL-3**

> The subject here is ⟦roasting green coffee beans⟧.

### Neutral subject `BICYCLE`: repairing a bicycle drivetrain

**BICYCLE-NEUTRAL-1**

> This note concerns ⟦repairing a bicycle drivetrain⟧.

**BICYCLE-NEUTRAL-2**

> The selected topic is ⟦repairing a bicycle drivetrain⟧.

**BICYCLE-NEUTRAL-3**

> The subject here is ⟦repairing a bicycle drivetrain⟧.

### Neutral subject `WATERCOLOR`: painting a watercolor landscape

**WATERCOLOR-NEUTRAL-1**

> This note concerns ⟦painting a watercolor landscape⟧.

**WATERCOLOR-NEUTRAL-2**

> The selected topic is ⟦painting a watercolor landscape⟧.

**WATERCOLOR-NEUTRAL-3**

> The subject here is ⟦painting a watercolor landscape⟧.

## Crossover treatment notes and masks

### Masked subject `COFFEE`: roasting green coffee beans

**COFFEE-TELESCOPE**

> After aligning the telescope's equatorial mount, I spent the evening
> ⟦roasting green coffee beans⟧.

**COFFEE-SOURDOUGH**

> After feeding a sourdough starter with flour and water, I spent the evening
> ⟦roasting green coffee beans⟧.

**COFFEE-PASSPORT**

> After submitting the paperwork to renew my passport, I spent the evening
> ⟦roasting green coffee beans⟧.

### Masked subject `BICYCLE`: repairing a bicycle drivetrain

**BICYCLE-TELESCOPE**

> After aligning the telescope's equatorial mount, I spent the evening
> ⟦repairing a bicycle drivetrain⟧.

**BICYCLE-SOURDOUGH**

> After feeding a sourdough starter with flour and water, I spent the evening
> ⟦repairing a bicycle drivetrain⟧.

**BICYCLE-PASSPORT**

> After submitting the paperwork to renew my passport, I spent the evening
> ⟦repairing a bicycle drivetrain⟧.

### Masked subject `WATERCOLOR`: painting a watercolor landscape

**WATERCOLOR-TELESCOPE**

> After aligning the telescope's equatorial mount, I spent the evening
> ⟦painting a watercolor landscape⟧.

**WATERCOLOR-SOURDOUGH**

> After feeding a sourdough starter with flour and water, I spent the evening
> ⟦painting a watercolor landscape⟧.

**WATERCOLOR-PASSPORT**

> After submitting the paperwork to renew my passport, I spent the evening
> ⟦painting a watercolor landscape⟧.

The three masked-subject identities are scoring data. The telescope,
sourdough, and passport text is deliberately unmasked.

## Frozen relationships

The required same-subject groups are:

```text
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
```

The three context lures are:

```text
COFFEE-TELESCOPE, BICYCLE-TELESCOPE, WATERCOLOR-TELESCOPE
COFFEE-SOURDOUGH, BICYCLE-SOURDOUGH, WATERCOLOR-SOURDOUGH
COFFEE-PASSPORT, BICYCLE-PASSPORT, WATERCOLOR-PASSPORT
```

Vectors in a context lure share exact unmasked wording but have different
masked atomic subjects. That shared context must not create a fine segment.

## Frozen hypothesis

1. In the neutral prerequisite, each subject will be cleanly recovered and no
   two different subjects will share a fine segment.
2. In the crossover treatment, each masked-subject group will be cleanly
   recovered as one complete three-vector fine segment.
3. In the treatment, no two vectors with different masked subjects will share
   a fine segment, including every pair inside the three context lures.

A subject is **cleanly recovered** when one segment contains all three of its
vectors and no vector from another declared subject. Other pure subsets may
overlap that segment.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in
the [suite index](README.md). Preserve its raw outputs exactly. Any
normalization, distance, or other preprocessing belongs to the candidate's
frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all eighteen notes, masks, subject identities, and
   expected relationships.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output rule, and seed.
3. Generate all eighteen full-note SSE vectors once and preserve their exact
   bytes.
4. Run the nine neutral-context vectors in the frozen position order below.
5. If the neutral prerequisite fails, record that failure and stop. There is no
   valid separated baseline from which to attribute a treatment change.
6. If it passes, replace each neutral vector with its paired treatment vector
   at the same position and rerun with the unchanged candidate and seed.
7. Preserve both complete fine-segment collections and the shared position
   order.
8. Reveal the identities and score the masked-subject groups and context lures.

The shared positions are:

| Position | Neutral run | Treatment run |
|---:|---|---|
| 1 | `COFFEE-NEUTRAL-1` | `COFFEE-TELESCOPE` |
| 2 | `BICYCLE-NEUTRAL-1` | `BICYCLE-TELESCOPE` |
| 3 | `WATERCOLOR-NEUTRAL-1` | `WATERCOLOR-TELESCOPE` |
| 4 | `COFFEE-NEUTRAL-2` | `COFFEE-SOURDOUGH` |
| 5 | `BICYCLE-NEUTRAL-2` | `BICYCLE-SOURDOUGH` |
| 6 | `WATERCOLOR-NEUTRAL-2` | `WATERCOLOR-SOURDOUGH` |
| 7 | `COFFEE-NEUTRAL-3` | `COFFEE-PASSPORT` |
| 8 | `BICYCLE-NEUTRAL-3` | `BICYCLE-PASSPORT` |
| 9 | `WATERCOLOR-NEUTRAL-3` | `WATERCOLOR-PASSPORT` |

Input order therefore cannot explain a difference between the two runs.

## Pass rule

The experiment passes only if the neutral prerequisite passes and then:

- all three masked-subject groups are cleanly recovered;
- no pair from different masked subjects shares a fine segment.

Report context-lure false merges separately from other cross-subject false
merges. One failure is not averaged away.

## Required record

Preserve:

- recovery status for every masked subject;
- all returned segments, overlaps, and omissions in both runs;
- every same-subject split;
- every context-lure merge;
- every other treatment cross-subject merge;
- the exact shared position order;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the within-subject cosines across changing contexts;
- the different-subject cosines under identical contexts;
- the raw SSE artifact and hashes;
- the candidate configuration and seed.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that these three strong, repeated context signals did not overturn
membership for three exact masked subjects. It does not show that unmasked text
has no effect on vector coordinates.

After a passing neutral prerequisite, a treatment failure is evidence that the
substantive unmasked material changed a required fine relationship in this
controlled fixture. A shared-context lure identifies the intended failure
mechanism more specifically; another treatment merge still violates the
assumption but is not necessarily caused by repeated context attraction.

This does not test masks whose meaning requires surrounding context, automatic
mask generation, natural correlated notes, unequal density, or hierarchy
quality.
