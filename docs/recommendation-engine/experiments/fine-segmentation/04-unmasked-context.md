# Experiment 4: unmasked-context membership

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

When the same selected text is encoded alone and inside notes with different
unmasked contexts, does each context-loaded vector retain the no-context
control's relationships to the recovered subjects when each context change is
tested independently?

## Design

The same frozen vectors are used in ten exact input conditions. Each condition
is repeated in two fresh candidate invocations:

1. One **anchor-only baseline** contains the nine fully masked target anchors
   and nine fully masked context anchors.
2. Nine independent **treatment runs** each contain those same 18 anchors plus
   exactly one mixed target.

The anchor-only baseline establishes six reference subjects and one six-subject
relationship profile for each exact no-context control. A control is usable
only when that profile is one-hot: it has a relationship to its declared target
subject and no relationship to the other five subjects.

Each treatment run then asks one question. After the added mixed vector enters,
do the six references and the exact control's one-hot profile remain available,
and does the mixed vector have that same profile? A changed control or missing
reference withholds that treatment's focal verdict; it does not become evidence
that the mixed vector itself changed because of context.

Each target reference contains one fully masked anchor whose selected text is
exactly the same as its three mixed targets' masks, plus two independent
paraphrases. The exact anchor supplies the no-context control inside every
treatment collection; the paraphrases prevent literal repetition from defining
the reference by itself.

Testing one mixed target per run prevents treatment vectors from moving one
another, jointly reinforcing their masked subject, or jointly changing the
control and references used to score them. No all-nine treatment run is part of
this experiment because it cannot supply the missing per-target counterfactual.

## Lexical controls

- Every anchor's substantive text is fully masked. Terminal punctuation stays
  outside the selected span, matching the mixed-target masks. There is no
  repeated unmasked carrier in the anchor cohorts.
- Each target-subject cohort contains one exact fully masked control and two
  semantic paraphrases. The exact control supplies one fixed-wording anchor;
  the paraphrases prevent the subject reference from being established by
  literal repetition alone. Scoring compares each mixed target with that exact
  control, subject by subject, in the same treatment output. The mixed target
  and control need not share one segment directly.
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
- The control and mixed target select identical UTF-8 bytes, but their selected
  token IDs, selected-piece counts, and contextual token representations may
  differ when the complete notes are tokenized and encoded. Those differences
  are legitimate effects of unmasked context under the frozen SSE boundary.
  Preserve them as diagnostics; do not use equality as a prerequisite.

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

The declared target-subject identities are:

```text
COFFEE-CONTROL, COFFEE-ANCHOR-2, COFFEE-ANCHOR-3,
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT

BICYCLE-CONTROL, BICYCLE-ANCHOR-2, BICYCLE-ANCHOR-3,
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT

WATERCOLOR-CONTROL, WATERCOLOR-ANCHOR-2, WATERCOLOR-ANCHOR-3,
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
```

The frozen within-run control matches are:

```text
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT
  -> COFFEE-CONTROL
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT
  -> BICYCLE-CONTROL
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
  -> WATERCOLOR-CONTROL
```

The declared context-anchor identities are:

```text
TELESCOPE-ANCHOR-1, TELESCOPE-ANCHOR-2, TELESCOPE-ANCHOR-3
SOURDOUGH-ANCHOR-1, SOURDOUGH-ANCHOR-2, SOURDOUGH-ANCHOR-3
PASSPORT-ANCHOR-1, PASSPORT-ANCHOR-2, PASSPORT-ANCHOR-3
```

For each mixed target, the three anchors belonging to its unmasked context are
its matching context anchors. For example, the matching context anchors for
`COFFEE-TELESCOPE` are `TELESCOPE-ANCHOR-1` through
`TELESCOPE-ANCHOR-3`. There are 27 such target-to-context-anchor pairs.

Each mixed target also retains its masked-subject, context-subject, and outer-form
labels as scorer-only diagnostic metadata. After the nine independent focal
verdicts are fixed, summarize failures by each of those three dimensions. A
repeated pattern may motivate a smaller follow-up, but it never replaces or
changes an individual treatment verdict.

## Anchor-supported membership

Each of the six declared subjects has exactly three independently worded
anchors. A segment is **supported by a subject** when it contains at least two
of that subject's anchors. Support does not imply purity: the same segment may
also contain vectors declared as other subjects.

A **reference segment** for one subject is supported by that subject and
subject-pure: every vector in it has that same declared atomic subject. In a
treatment run, a target reference segment may therefore contain that run's
single mixed vector when its mask declares the same target subject. A context
reference segment cannot contain that mixed vector, because the vector's
declared atomic subject is its mask, not its unmasked context.

For each subject, construct an undirected three-vertex **anchor graph**. Its
vertices are that subject's anchors. Connect two anchors when they co-occur in
one reference segment for that subject. The subject's reference is recovered
when this graph is connected. This permits either one segment containing all
three anchors or overlapping pure segments that connect them in pairs.

A vector whose declared subject is `S` has a **relationship to `S`** when it
belongs to at least one reference segment for `S`. A vector whose declared
subject is not `S` has a **relationship to `S`** when it belongs to any
returned segment containing at least one other vector whose declared subject
is `S`. This applies identically whether that other vector is an anchor or a
mixed target: the candidate itself proposed the cross-subject relationship,
while the separately recovered reference establishes what `S` means.

For a mixed target, its relationship to its unmasked-context subject is the
**matching-context relationship**. Relationships to the four remaining
foreign subjects are recorded separately.

One-vector segments and segments without two same-subject anchors do not
define a reference subject. They remain part of the candidate output. A
multi-vector segment containing a tested vector and another vector with a
different declared subject is a direct returned relationship and is scored as
described above. Evidence is not aggregated across separate segments.

This is deliberately a subject-level membership test. It does not require all
vectors declared as one subject in an input to appear in a single segment, nor
does it require their complete sets of segment IDs to match. Different
anchor-supported pure segments can represent the same declared subject.

## Anchor-only baseline qualification

First apply the shared execution-profile, output-validity, and repeatability
checks. In a valid, repeatable anchor-only baseline, qualify each declared
subject independently. One subject qualifies when its reference anchor graph
is connected.

For each exact target control, build a six-boolean profile in this frozen order:

```text
COFFEE, BICYCLE, WATERCOLOR, TELESCOPE, SOURDOUGH, PASSPORT
```

The control is usable only when all six subject references qualify and its
profile is one-hot: `true` for its declared target subject and `false` for the
other five. For example, `COFFEE-CONTROL` must have
`[true, false, false, false, false, false]`.

Other baseline segments, including cross-subject segments not involving a
scored control, singletons, and same-subject overlaps, remain diagnostics. They
do not erase an otherwise connected reference or usable control. A missing
subject reference is one **local baseline-reference prerequisite failure** and
makes all three control profiles unavailable. If all six references qualify but
one control's profile is not one-hot, that control has a **local control-profile
prerequisite failure**. Its three treatment runs receive no focal verdict. Do
not relabel a missing baseline reference as three control-profile failures;
neither prerequisite failure is an unmasked-context failure.

An invalid raw output, execution-profile mismatch, or disagreement between
valid repetitions is an integrity failure under the shared contract and blocks
every baseline-dependent result.

## Frozen hypothesis

In one treatment run, reconstruct all six pure anchor graphs and recompute the
exact control's six-boolean profile before scoring the mixed vector. That
treatment qualifies only when:

1. its exact control qualified in the anchor-only baseline;
2. all six treatment-run reference graphs are connected; and
3. the control's treatment-run profile exactly equals its frozen one-hot
   baseline profile.

A missing reference is a **local treatment-reference prerequisite failure**. A
changed control profile is a **local control-displacement prerequisite
failure**. Either gives only that treatment no focal verdict. This prevents an
added vector from moving the measurement control and then passing merely
because the mixed vector moved with it.

For a qualified treatment, compute the mixed vector's six-boolean profile. An
equal profile is a **subject-relationship pass**. Any difference is a
**context-membership-change failure**, recorded as each gained or lost
relationship. The target-subject comparison tests retention; the
unmasked-context-subject comparison tests the matching-context lure; the other
four comparisons detect unrelated gains or losses.

Complete segment-ID signatures are not compared. An auxiliary singleton or
same-subject overlap that leaves all references and the control profile intact
does not by itself show that unmasked material changed membership.

## Frozen system boundary

Use the shared execution contract and 768-dimensional Sentence-T5-base SSE
checkpoint in [README.md](README.md).

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This experiment qualifies the frozen SSE-plus-candidate combination. Its text
intervention passes through SSE and can change the vector before the candidate
organizes it. A failure cannot by itself identify SSE, candidate behavior, or
their interaction as the cause.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all 27 notes, masks, subject identities, and
   expected relationships.
2. Freeze this document, the complete candidate identity and execution profile,
   and the candidate's construction-level permutation-invariance argument.
3. Apply the shared opaque-ID blinding and frozen-order rules once to all 27
   fixture IDs. The anchor-only input is the 18-anchor subsequence of that one
   frozen order. Each treatment input is the same 18 anchors plus exactly one
   mixed target, filtered from that global order.
4. Freeze the SSE boundary and exact input bytes, then generate all 27
   full-note vectors once and record their dimensions and hashes. Also preserve
   each frozen byte span's mapping to selected token positions and verify it
   against the frozen byte-span-to-token rule. Preserve token IDs and piece
   counts as diagnostics without comparing positions, IDs, or counts between a
   control and mixed note.
5. Give the 18 anchors to two separately initialized candidate invocations with
   the frozen candidate seed and verified execution profile. Preserve both
   complete anchor-only outputs.
6. Run each of the nine 19-vector treatment inputs twice, each time in a
   separately initialized process with that same seed and verified profile.
   Preserve all 18 complete treatment outputs.
7. While identities remain hidden, verify each invocation's actual execution
   profile, then validate every raw output under the shared output contract. Do
   not canonicalize an invalid output or derive a semantic verdict from an
   integrity failure.
8. For each valid identical-input pair, compare the shared canonical JSON
   bytes. A mismatch is a repeatability failure and receives no semantic
   verdict.
9. After all 20 outputs are immutable, reveal and verify the fixture mapping.
   Qualify the six baseline references and three exact control profiles. Then,
   for each treatment independently, qualify its six references, verify that
   its exact control retained the baseline profile, and compare the mixed
   vector's profile. Preserve every artifact even when a treatment is withheld.

## Pass rule

Any anchor-only integrity failure under the shared contract blocks baseline
qualification and every dependent semantic verdict. When the anchor-only pair
passes those checks, all six references and all three one-hot control profiles
must qualify before the experiment can produce a complete pass.

An integrity failure in one treatment preserves the baseline and every other
treatment's result but gives that treatment no focal verdict. For each valid,
repeatable treatment, score in this order:

1. require all six baseline references and that treatment's exact control
   profile to have qualified;
2. require all six treatment reference graphs to remain connected;
3. recompute the exact control's profile and require it to equal its frozen
   baseline profile; and
4. compare the mixed vector's six booleans with that preserved profile.

The experiment fails when any eligible mixed-vector profile differs. It passes
only when all nine treatments are eligible and all nine mixed profiles equal
their controls. If no eligible treatment fails but any treatment is withheld,
the experiment has no overall context verdict. Do not average treatments or
profile positions.

Report these result classes separately:

- integrity failure, with its shared-contract cause;
- local baseline-reference prerequisite failure for each subject;
- local control-profile prerequisite failure for each exact control;
- local treatment-reference prerequisite failure for each treatment;
- local control-displacement prerequisite failure for each treatment;
- context-membership-change failure for each eligible gained or lost
  relationship, classified as masked-subject, matching-context, or other
  subject;
- stable complete mixed-vector profile for each eligible equal comparison;
- treatment withheld because its baseline, reference, or preserved-control
  prerequisite failed;
- context-subject, masked-subject, and outer-form patterns across independent
  treatment results;
- other treatment-output shape changes that do not alter a reference or
  control profile, as collection diagnostics; and
- other unsupported auxiliary segments.

One eligible gained or lost relationship is not averaged away. Other output
shape changes that preserve all scored subject relationships are diagnostic
and do not decide the verdict.

## Required record

Preserve:

- the complete returned fine-segment collection from all 20 invocations;
- for each valid output, every segment's projection onto the 18 anchor IDs;
- every raw output-validity result and, for each valid output, its canonical
  JSON byte string and hash;
- all 10 repeatability comparisons;
- every subject's anchor-only qualification, every anchor in a cross-subject
  segment, all reference segments, and all six anchor graphs;
- every exact control's baseline profile and qualification;
- for each treatment, all six pure anchor graphs, the control's recomputed
  profile, every prerequisite state, the mixed vector's complete supporting
  segments and profile, and every gained/lost relationship;
- every context-subject, masked-subject, outer-form, and other diagnostic
  pattern across the nine independent treatment results;
- the exact opaque-ID mapping, global order, anchor-only input, and all nine
  treatment inputs;
- the shared blinding seed, its pre-run commitment, and successful post-run
  verification of every derived ID and order key;
- every frozen byte span, its selected token positions, and its verification
  against the frozen byte-span-to-token rule; selected token IDs and piece
  counts remain diagnostics without a control/mixed equality requirement;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the complete candidate identity and execution-profile manifest and hash, plus
  every invocation's actual-profile verification.

If the anchor-only pair has an integrity failure, preserve all 20 raw outputs
and mark baseline qualification and every dependent result as **no verdict
because anchor-only integrity failed**. If one treatment pair has an integrity
failure, preserve its raw outputs and every independently valid baseline and
treatment result, and mark only that treatment **no verdict because treatment
integrity failed**. Never repair an output or choose one of two conflicting
outputs.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that, in this fixture, the frozen SSE-plus-candidate combination
recovered all six baseline references, established a one-hot relationship
profile for every exact control, preserved that control in each independent
treatment, and gave every context-loaded vector the same six-subject profile.

An integrity failure has no Experiment 4 semantic interpretation. A baseline
reference or control-profile failure means the local state needed to test a
mixed target never existed. A treatment-reference or control-displacement
failure means adding that one mixed vector changed the measurement state, so
the mixed vector receives no focal verdict. A context-membership-change failure
means an eligible mixed vector gained or lost at least one relationship that
its preserved no-context control did not. Auxiliary shape changes remain
diagnostic.

Because the intervention passes through SSE before candidate execution, a
failure may arise from SSE geometry, the segmentation candidate, or their
interaction. The result does not identify that mechanism.

The recorded context, masked-subject, outer-form, and raw-vector diagnostics can
help explain a failure, but do not prove its mechanism. A smaller matched
follow-up should isolate semantic meaning, syntax, length, or position only
after a failure occurs.

This experiment does not test automatically generated masks, natural
correlated notes, unequal density, every possible context position,
input-order or candidate-seed invariance, context-loaded paraphrases of the
target masks, or hierarchy quality.
