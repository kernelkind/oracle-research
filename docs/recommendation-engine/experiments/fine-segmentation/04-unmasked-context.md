# Experiment 4: unmasked-context coexistence

Status: **draft; all notes, masks, and expected relationships require human
approval before encoding**.

## Assumption under test

> Holding the resolved atomic subject fixed, unmasked material does not
> materially change membership.

SSE processes the complete note before pooling the selected token positions.
Unmasked text can therefore influence the vector. The requirement is not zero
numeric influence. It is that the surrounding material must not determine the
vector's fine-segment membership.

## Question

When several vectors have the exact same masked atomic subject but different
unmasked contexts, do they enter the region for the masked subject and remain
outside the regions represented only by those contexts?

## Design

All 27 vectors coexist in one candidate run:

- nine fully masked anchors for the three target subjects;
- nine fully masked anchors for the three context subjects;
- nine mixed targets crossing every target subject with every context subject.

The anchor cohorts establish six recoverable fine-subject regions. The mixed
targets then have both a correct destination and a competing context
destination in the same vector collection.

There is no separate neutral run. Separate runs could conceal a split in which
bare and context-loaded instances form different regions while each run looks
internally coherent.

## Lexical controls

- Every anchor's substantive text is fully masked. Terminal punctuation stays
  outside the selected span, matching the mixed-target masks. There is no
  repeated unmasked carrier in the anchor cohorts.
- Each target-subject cohort contains one exact fully masked control and two
  semantic paraphrases. The control holds the selected token text fixed when
  its membership is compared with the mixed targets.
- The three context-subject anchors express that subject with different
  wording.
- The three mixed contexts representing one context subject use different
  clauses. No complete source clause is copied from another mixed note or from
  an anchor. Subject-defining words and short phrases may repeat when removing
  them would distort the meaning.
- Three outer sentence forms are assigned as a Latin square. Each form appears
  once with every target subject and once with every context subject. Sentence
  form is therefore not associated with either semantic factor.
- Necessary content words such as `telescope`, `sourdough`, and `passport` are
  not artificially removed. The test avoids copied phrases; it does not turn
  the notes into unnatural thesaurus substitutions.

The three outer forms are:

```text
A: After <context>, I spent the evening <masked subject>.
B: Once <context>, I moved on to <masked subject>.
C: I finished the day <masked subject> after <context>.
```

## Fully masked target-subject anchors

### `COFFEE`: roasting green coffee beans

**COFFEE-CONTROL**

> ⟦roasting green coffee beans⟧.

**COFFEE-ANCHOR-2**

> ⟦Applying heat to unroasted coffee beans until they become roasted⟧.

**COFFEE-ANCHOR-3**

> ⟦Turning raw coffee beans into roasted beans⟧.

### `BICYCLE`: repairing a bicycle drivetrain

**BICYCLE-CONTROL**

> ⟦repairing a bicycle drivetrain⟧.

**BICYCLE-ANCHOR-2**

> ⟦Fixing the drivetrain of a bicycle⟧.

**BICYCLE-ANCHOR-3**

> ⟦Restoring a bike's chain-and-gear drive system to working order⟧.

### `WATERCOLOR`: painting a watercolor landscape

**WATERCOLOR-CONTROL**

> ⟦painting a watercolor landscape⟧.

**WATERCOLOR-ANCHOR-2**

> ⟦Creating a landscape picture with watercolor paint⟧.

**WATERCOLOR-ANCHOR-3**

> ⟦Rendering landscape scenery in watercolors⟧.

## Fully masked context-subject anchors

### `TELESCOPE`: aligning an equatorial telescope mount

**TELESCOPE-ANCHOR-1**

> ⟦Aligning the equatorial mount of a telescope⟧.

**TELESCOPE-ANCHOR-2**

> ⟦Setting a telescope's equatorial mounting axis parallel to Earth's rotation
> axis⟧.

**TELESCOPE-ANCHOR-3**

> ⟦Adjusting an equatorial telescope mount for correct polar alignment⟧.

### `SOURDOUGH`: feeding a sourdough starter

**SOURDOUGH-ANCHOR-1**

> ⟦Feeding a sourdough starter with flour and water⟧.

**SOURDOUGH-ANCHOR-2**

> ⟦Refreshing a sourdough culture by adding fresh flour and water⟧.

**SOURDOUGH-ANCHOR-3**

> ⟦Adding flour and water to keep a sourdough starter active⟧.

### `PASSPORT`: submitting passport-renewal paperwork

**PASSPORT-ANCHOR-1**

> ⟦Submitting paperwork to renew a passport⟧.

**PASSPORT-ANCHOR-2**

> ⟦Filing the forms required for passport renewal⟧.

**PASSPORT-ANCHOR-3**

> ⟦Sending in a passport-renewal application⟧.

## Mixed targets

The masked text is identical across all three contexts for a target subject.
The context is deliberately unmasked.

### Telescope context

**COFFEE-TELESCOPE · form A**

> After pointing my telescope mount's right-ascension axis toward the celestial
> pole for accurate tracking, I spent the evening ⟦roasting green coffee
> beans⟧.

**BICYCLE-TELESCOPE · form B**

> Once I had aimed the polar axis of my stargazing mount at the fixed point
> around which the stars appear to turn, I moved on to ⟦repairing a bicycle
> drivetrain⟧.

**WATERCOLOR-TELESCOPE · form C**

> I finished the day ⟦painting a watercolor landscape⟧ after correcting the
> orientation of my star-tracking mount toward the celestial pole.

### Sourdough context

**COFFEE-SOURDOUGH · form B**

> Once I had mixed a fresh portion of flour and water into my sourdough
> starter, I moved on to ⟦roasting green coffee beans⟧.

**BICYCLE-SOURDOUGH · form C**

> I finished the day ⟦repairing a bicycle drivetrain⟧ after giving my
> sourdough culture its regular meal of flour and water.

**WATERCOLOR-SOURDOUGH · form A**

> After replenishing my sourdough starter with new flour and water, I spent
> the evening ⟦painting a watercolor landscape⟧.

### Passport context

**COFFEE-PASSPORT · form C**

> I finished the day ⟦roasting green coffee beans⟧ after mailing the completed
> forms for my passport renewal.

**BICYCLE-PASSPORT · form A**

> After lodging an application to have my passport renewed, I spent the
> evening ⟦repairing a bicycle drivetrain⟧.

**WATERCOLOR-PASSPORT · form B**

> Once I had sent in the documents required to renew my passport, I moved on
> to ⟦painting a watercolor landscape⟧.

## Frozen relationships

Each mixed target's declared atomic subject is its masked subject. Its
unmasked context is not an additional vector subject.

The required target-subject groups are:

```text
COFFEE-CONTROL, COFFEE-ANCHOR-2, COFFEE-ANCHOR-3,
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT

BICYCLE-CONTROL, BICYCLE-ANCHOR-2, BICYCLE-ANCHOR-3,
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT

WATERCOLOR-CONTROL, WATERCOLOR-ANCHOR-2, WATERCOLOR-ANCHOR-3,
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
```

The required context-anchor groups are:

```text
TELESCOPE-ANCHOR-1, TELESCOPE-ANCHOR-2, TELESCOPE-ANCHOR-3
SOURDOUGH-ANCHOR-1, SOURDOUGH-ANCHOR-2, SOURDOUGH-ANCHOR-3
PASSPORT-ANCHOR-1, PASSPORT-ANCHOR-2, PASSPORT-ANCHOR-3
```

The invalid context-lure groups are:

```text
COFFEE-TELESCOPE, BICYCLE-TELESCOPE, WATERCOLOR-TELESCOPE
COFFEE-SOURDOUGH, BICYCLE-SOURDOUGH, WATERCOLOR-SOURDOUGH
COFFEE-PASSPORT, BICYCLE-PASSPORT, WATERCOLOR-PASSPORT
```

The invalid form-lure groups are:

```text
COFFEE-TELESCOPE, WATERCOLOR-SOURDOUGH, BICYCLE-PASSPORT
BICYCLE-TELESCOPE, COFFEE-SOURDOUGH, WATERCOLOR-PASSPORT
WATERCOLOR-TELESCOPE, BICYCLE-SOURDOUGH, COFFEE-PASSPORT
```

For each mixed target, the three anchors belonging to its unmasked context are
its matching context anchors. For example, the matching context anchors for
`COFFEE-TELESCOPE` are `TELESCOPE-ANCHOR-1` through
`TELESCOPE-ANCHOR-3`. There are 27 such target-to-context-anchor pairs.

## Prerequisites

The candidate must already have passed the experiments for recovering repeated
subjects and resolving distinct subjects. In this fixture:

1. each exact target control and its two paraphrase anchors must share at least
   one segment;
2. each three-vector context-anchor cohort must share at least one segment;
3. every segment containing an exact target control must also contain at least
   one of its two correct paraphrase anchors and no vector declared as another
   atomic subject.

These conditions establish that each exact control already has a recovered,
semantically supported reference membership. If a prerequisite fails,
Experiment 4 has no verdict. Record which prerequisite failed instead of
attributing that failure to unmasked context.

## Frozen hypothesis

For each target subject, the exact fully masked control and all three mixed
targets will have identical, nonempty fine-segment membership signatures.

A vector's **membership signature** is the set of returned fine-segment IDs
that contain it. Comparing every mixed target directly with the exact control
detects context-specific, sentence-form-specific, and mixed-only segments even
when a complete correct-subject segment also exists.

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
   configuration, fine-output rule, and candidate seed.
3. Generate all 27 full-note SSE vectors once and preserve their exact bytes.
4. After freezing the candidate, draw one 32-byte blinding seed from the
   operating system CSPRNG. Draw it exactly once. Derive each opaque ID as
   `HMAC-SHA-256(seed, "experiment-4-id-v1\0" || fixture_id_utf8)` and its order
   key as
   `HMAC-SHA-256(seed, "experiment-4-order-v1\0" || fixture_id_utf8)`.
5. Record
   `SHA-256("experiment-4-blinding-v1\0" || seed)` in the run manifest. Keep
   the seed and fixture mapping in the scorer's private artifact, which the
   candidate cannot read. Sort by ascending order key. Reveal the seed and
   mapping only after preserving the candidate output.
6. Give all 27 vectors to one freshly initialized candidate invocation in that
   frozen order.
7. Require the candidate to be deterministic for identical input,
   configuration, and candidate seed before interpreting this run.
8. Preserve the complete returned fine-segment collection.
9. Reveal the fixture identities, check the prerequisites, and then score the
   frozen hypothesis when the prerequisites hold.

## Pass rule

The experiment passes only if all three prerequisites hold and the frozen
hypothesis holds for all three target subjects. Report these result classes
separately:

- target-subject prerequisite failure;
- context-subject prerequisite failure;
- different control-versus-mixed membership signatures within one masked
  subject;
- an empty shared signature;
- a target-to-matching-context-anchor merge;
- context-lure merges;
- form-lure merges;
- every other cross-subject merge.

One control-versus-mixed signature mismatch is not averaged away.

## Required record

Preserve:

- the complete returned fine-segment collection;
- every vector's complete membership signature;
- prerequisite status for every target-subject and context-anchor group;
- every control-versus-mixed signature difference;
- every target-to-matching-context-anchor merge;
- every context-lure, form-lure, and other cross-subject merge;
- the exact opaque-ID mapping and candidate input order;
- the blinding seed, its pre-run commitment, and successful post-run
  verification of every derived ID and order key;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the candidate configuration and candidate seed.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that, in this fixture, adding each lexically varied unmasked
context left the vector's complete fine-segment membership identical to the
semantically supported exact control.

A control-versus-mixed signature difference directly shows that some part of
the complete unmasked framing changed membership. A prerequisite failure has
no Experiment 4 interpretation. The recorded lure classes provide diagnostics,
not a mechanism proof. A smaller matched follow-up should isolate semantic
meaning, syntax, length, or position only after a failure occurs.

This experiment does not test automatically generated masks, natural
correlated notes, unequal density, every possible context position, or
hierarchy quality.
