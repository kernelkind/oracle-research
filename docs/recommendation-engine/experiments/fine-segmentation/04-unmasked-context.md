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

Three fixed context-anchor cohorts represent the telescope, sourdough, and
passport meanings directly. They appear unchanged in both runs. Without these
anchors, the fixture contains no corresponding context region for a target to
enter. It could therefore pass even if that target would be misassigned in a
corpus containing telescope, sourdough, or passport vectors. The anchors make
that possible membership error observable.

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

## Fixed context-anchor notes and masks

These nine vectors appear unchanged in both runs.

### Anchor subject `TELESCOPE`: aligning an equatorial telescope mount

**TELESCOPE-ANCHOR-1**

> ⟦I aligned the telescope's equatorial mount.⟧

**TELESCOPE-ANCHOR-2**

> ⟦I adjusted the telescope's equatorial mount until its axes were aligned.⟧

**TELESCOPE-ANCHOR-3**

> ⟦I completed the alignment of an equatorial telescope mount.⟧

### Anchor subject `SOURDOUGH`: feeding a sourdough starter

**SOURDOUGH-ANCHOR-1**

> ⟦I fed my sourdough starter with flour and water.⟧

**SOURDOUGH-ANCHOR-2**

> ⟦Fresh flour and water were added to feed the sourdough starter.⟧

**SOURDOUGH-ANCHOR-3**

> ⟦I refreshed the sourdough culture by giving it flour and water.⟧

### Anchor subject `PASSPORT`: submitting passport-renewal paperwork

**PASSPORT-ANCHOR-1**

> ⟦I submitted the paperwork to renew my passport.⟧

**PASSPORT-ANCHOR-2**

> ⟦I filed a passport-renewal application.⟧

**PASSPORT-ANCHOR-3**

> ⟦I sent in the required forms to have my passport renewed.⟧

## Frozen relationships

The required neutral same-subject groups are:

```text
COFFEE-NEUTRAL-1, COFFEE-NEUTRAL-2, COFFEE-NEUTRAL-3
BICYCLE-NEUTRAL-1, BICYCLE-NEUTRAL-2, BICYCLE-NEUTRAL-3
WATERCOLOR-NEUTRAL-1, WATERCOLOR-NEUTRAL-2, WATERCOLOR-NEUTRAL-3
```

The required treatment same-subject groups are:

```text
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
```

The required fixed anchor groups are:

```text
TELESCOPE-ANCHOR-1, TELESCOPE-ANCHOR-2, TELESCOPE-ANCHOR-3
SOURDOUGH-ANCHOR-1, SOURDOUGH-ANCHOR-2, SOURDOUGH-ANCHOR-3
PASSPORT-ANCHOR-1, PASSPORT-ANCHOR-2, PASSPORT-ANCHOR-3
```

The three context lures are:

```text
COFFEE-TELESCOPE, BICYCLE-TELESCOPE, WATERCOLOR-TELESCOPE
COFFEE-SOURDOUGH, BICYCLE-SOURDOUGH, WATERCOLOR-SOURDOUGH
COFFEE-PASSPORT, BICYCLE-PASSPORT, WATERCOLOR-PASSPORT
```

Vectors in a context lure share exact unmasked wording but have different
masked atomic subjects. That shared context must not create a fine segment.

Each treatment target must also remain separate from every anchor vector for
its own unmasked context. For example, `COFFEE-TELESCOPE` must not share a fine
segment with any `TELESCOPE-ANCHOR-*` vector. Such a membership would show that
the telescope context, rather than the coffee mask, determined a fine-region
assignment even if the three telescope-conditioned targets did not group with
one another.

## Frozen hypothesis

1. In the neutral prerequisite, all three neutral subjects and all three fixed
   anchor subjects will be cleanly recovered, and no two different subjects
   will share a fine segment.
2. In the crossover treatment, all three masked-subject groups and all three
   fixed anchor groups will be cleanly recovered as complete three-vector fine
   segments.
3. In the treatment, no two vectors from different declared subjects will
   share a fine segment. This includes every pair inside the three context
   lures and every target-to-matching-anchor pair.

A subject is **cleanly recovered** when one segment contains all three of its
vectors and no vector from another declared subject. Other pure subsets may
overlap that segment.

## Frozen system boundary

Use the shared 768-dimensional Sentence-T5-base SSE checkpoint identified in:

README.md

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all 27 notes, masks, subject identities, and
   expected relationships.
2. Freeze this document and the candidate's implementation, preprocessing,
   configuration, fine-output rule, and seed.
3. Generate all 27 full-note SSE vectors once and preserve their exact
   bytes.
4. Run the nine neutral-context vectors and nine fixed anchors in the frozen
   position order below.
5. If the neutral prerequisite fails, record that failure and stop. There is no
   valid separated baseline from which to attribute a treatment change.
6. If it passes, replace each neutral vector with its paired treatment vector
   at the same position and rerun with the unchanged anchors, candidate, and
   seed.
7. Preserve both complete fine-segment collections and the shared position
   order.
8. Reveal the identities and score the masked-subject groups, fixed anchor
   groups, context lures, and target-to-matching-anchor relationships.

The candidate receives the stable opaque IDs `P01` through `P18`. Positions
`P01` through `P09` retain their IDs while their neutral vectors are replaced
by the paired treatment vectors. Positions `P10` through `P18` contain the
same anchor vectors in both runs.

The shared positions are:

| Candidate ID | Neutral run | Treatment run |
|---:|---|---|
| `P01` | `COFFEE-NEUTRAL-1` | `COFFEE-TELESCOPE` |
| `P02` | `BICYCLE-NEUTRAL-1` | `BICYCLE-TELESCOPE` |
| `P03` | `WATERCOLOR-NEUTRAL-1` | `WATERCOLOR-TELESCOPE` |
| `P04` | `COFFEE-NEUTRAL-2` | `COFFEE-SOURDOUGH` |
| `P05` | `BICYCLE-NEUTRAL-2` | `BICYCLE-SOURDOUGH` |
| `P06` | `WATERCOLOR-NEUTRAL-2` | `WATERCOLOR-SOURDOUGH` |
| `P07` | `COFFEE-NEUTRAL-3` | `COFFEE-PASSPORT` |
| `P08` | `BICYCLE-NEUTRAL-3` | `BICYCLE-PASSPORT` |
| `P09` | `WATERCOLOR-NEUTRAL-3` | `WATERCOLOR-PASSPORT` |
| `P10` | `TELESCOPE-ANCHOR-1` | `TELESCOPE-ANCHOR-1` |
| `P11` | `SOURDOUGH-ANCHOR-1` | `SOURDOUGH-ANCHOR-1` |
| `P12` | `PASSPORT-ANCHOR-1` | `PASSPORT-ANCHOR-1` |
| `P13` | `TELESCOPE-ANCHOR-2` | `TELESCOPE-ANCHOR-2` |
| `P14` | `SOURDOUGH-ANCHOR-2` | `SOURDOUGH-ANCHOR-2` |
| `P15` | `PASSPORT-ANCHOR-2` | `PASSPORT-ANCHOR-2` |
| `P16` | `TELESCOPE-ANCHOR-3` | `TELESCOPE-ANCHOR-3` |
| `P17` | `SOURDOUGH-ANCHOR-3` | `SOURDOUGH-ANCHOR-3` |
| `P18` | `PASSPORT-ANCHOR-3` | `PASSPORT-ANCHOR-3` |

Input order therefore cannot explain a difference between the two runs.

## Pass rule

The neutral prerequisite passes only if all three neutral subjects and all
three fixed anchor subjects are cleanly recovered, with no shared
fine-segment membership between different subjects.

The experiment passes only if that prerequisite passes and then:

- all three masked-subject groups and all three fixed anchor groups are
  cleanly recovered;
- no pair from different declared subjects shares a fine segment.

Report context-lure false merges, target-to-matching-anchor merges, and other
cross-subject merges separately. One failure is not averaged away.

## Required record

Preserve:

- recovery status for every masked subject;
- recovery status for every fixed anchor subject;
- all returned segments, overlaps, and omissions in both runs;
- every same-subject split;
- every context-lure merge;
- every target-to-matching-anchor merge;
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
membership for three exact masked subjects, form a context-lure segment, or
pull a target into the matching fixed context region. It does not show that
unmasked text has no effect on vector coordinates.

After a passing neutral prerequisite, a treatment failure is evidence that the
complete treatment framing changed a required fine relationship in this
fixture. It does not by itself isolate whether semantic context, carrier
wording, sentence length, or another changed property caused the failure. A
shared-context lure or target-to-matching-anchor merge identifies context
attraction more specifically. A later experiment can isolate the cause if this
fixture fails.

This does not test masks whose meaning requires surrounding context, automatic
mask generation, natural correlated notes, unequal density, or hierarchy
quality.
