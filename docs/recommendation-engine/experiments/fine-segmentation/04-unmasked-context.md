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

The same frozen vectors are used in two input conditions. Each condition is
repeated in two fresh candidate invocations:

1. An **anchor-only baseline** contains the nine fully masked target anchors
   and nine fully masked context anchors.
2. A **joint coexistence run** contains those 18 anchors plus the nine mixed
   targets crossing every target subject with every context subject.

The anchor-only baseline establishes six reference subjects before mixed
vectors can affect the candidate's output. The joint run then tests whether
those references survive and whether each mixed vector enters the reference
for its masked subject instead of a competing reference supported by its
unmasked context.

The anchor-only baseline does not replace the joint run. Comparing separately
clustered control and treatment collections could conceal a split in which
bare and context-loaded instances form different regions while each collection
looks internally coherent. Both views are required: the baseline establishes
the references, and the joint run tests coexistence against them.

## Lexical controls

- Every anchor's substantive text is fully masked. Terminal punctuation stays
  outside the selected span, matching the mixed-target masks. There is no
  repeated unmasked carrier in the anchor cohorts.
- Each target-subject cohort contains one exact fully masked control and two
  semantic paraphrases. The exact control supplies one fixed-wording anchor;
  the paraphrases prevent the subject reference from being established by
  literal repetition alone. Scoring uses their connected anchor-supported
  subject reference rather than requiring every mixed target to share one
  segment directly with the exact control.
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

The declared target-subject identities are:

```text
COFFEE-CONTROL, COFFEE-ANCHOR-2, COFFEE-ANCHOR-3,
COFFEE-TELESCOPE, COFFEE-SOURDOUGH, COFFEE-PASSPORT

BICYCLE-CONTROL, BICYCLE-ANCHOR-2, BICYCLE-ANCHOR-3,
BICYCLE-TELESCOPE, BICYCLE-SOURDOUGH, BICYCLE-PASSPORT

WATERCOLOR-CONTROL, WATERCOLOR-ANCHOR-2, WATERCOLOR-ANCHOR-3,
WATERCOLOR-TELESCOPE, WATERCOLOR-SOURDOUGH, WATERCOLOR-PASSPORT
```

The declared context-anchor identities are:

```text
TELESCOPE-ANCHOR-1, TELESCOPE-ANCHOR-2, TELESCOPE-ANCHOR-3
SOURDOUGH-ANCHOR-1, SOURDOUGH-ANCHOR-2, SOURDOUGH-ANCHOR-3
PASSPORT-ANCHOR-1, PASSPORT-ANCHOR-2, PASSPORT-ANCHOR-3
```

The frozen context-lure groups are:

```text
COFFEE-TELESCOPE, BICYCLE-TELESCOPE, WATERCOLOR-TELESCOPE
COFFEE-SOURDOUGH, BICYCLE-SOURDOUGH, WATERCOLOR-SOURDOUGH
COFFEE-PASSPORT, BICYCLE-PASSPORT, WATERCOLOR-PASSPORT
```

The frozen form-lure groups are:

```text
COFFEE-TELESCOPE, WATERCOLOR-SOURDOUGH, BICYCLE-PASSPORT
BICYCLE-TELESCOPE, COFFEE-SOURDOUGH, WATERCOLOR-PASSPORT
WATERCOLOR-TELESCOPE, BICYCLE-SOURDOUGH, COFFEE-PASSPORT
```

A frozen lure group is **supported** when at least two of its three members
co-occur in one returned segment.

For each mixed target, the three anchors belonging to its unmasked context are
its matching context anchors. For example, the matching context anchors for
`COFFEE-TELESCOPE` are `TELESCOPE-ANCHOR-1` through
`TELESCOPE-ANCHOR-3`. There are 27 such target-to-context-anchor pairs.

## Anchor-supported membership

Each of the six declared subjects has exactly three independently worded
anchors. A segment is **supported by a subject** when it contains at least two
of that subject's anchors. Support does not imply purity: the same segment may
also contain vectors declared as other subjects.

A **reference segment** for one subject is supported by that subject and
subject-pure: every vector in it has that same declared atomic subject. A
target reference segment may therefore contain any of that target's mixed
vectors. A context reference segment cannot contain a mixed vector, because a
mixed vector's declared atomic subject is its mask, not its unmasked context.

For each subject, construct an undirected three-vertex **anchor graph**. Its
vertices are that subject's anchors. Connect two anchors when they co-occur in
one reference segment for that subject. The subject's reference is recovered
when this graph is connected. This permits either one segment containing all
three anchors or overlapping pure segments that connect them in pairs.

A vector has **meaningful membership** in a subject when it belongs to at
least one reference segment for that subject. A vector has **competing
supported membership** when it belongs to any segment supported by another
subject, whether or not that competing segment is pure.

One-vector segments and segments without two same-subject anchors remain part
of the candidate output and the diagnostic record, but they do not define
meaningful or competing supported membership here. Evidence is not aggregated
across separate one-anchor segments.

This is deliberately a subject-level membership test. It does not require all
anchors and mixed vectors for one subject to appear in one six-vector segment,
nor does it require their complete sets of segment IDs to match. Different
anchor-supported pure segments can represent the same declared subject.

## Anchor-only baseline

The anchor-only baseline is valid only when the reference anchor graph for
each of the six subjects is connected. Other baseline segments, including
singletons and unsupported overlaps, remain in the diagnostic record. They do
not establish or invalidate a reference subject by themselves.

The six connected anchor graphs and their reference segments are the baseline
references. If the anchor-only baseline is invalid, Experiment 4 has no
verdict. Baseline eligibility uses only output preserved before the mixed
vectors enter the joint candidate run.

## Frozen hypothesis

In the joint coexistence run:

1. every baseline reference subject still has a connected reference anchor
   graph;
2. every mixed target has meaningful membership in its masked target subject;
3. no mixed target has competing supported membership in one of the other
   five declared subjects; and
4. no returned segment contains mixed targets from two or more different
   declared target subjects.

The third condition includes the matching unmasked-context subject. It also
catches support from an unrelated target or context subject. Complete
segment-ID signatures are not compared: an auxiliary singleton or unsupported
overlap does not by itself show that unmasked material changed meaningful
subject membership. The fourth condition is different: mixed vectors with
different masked subjects recurring together form a treatment-only
cross-subject region even without anchors. The frozen context-lure and
form-lure groups identify two specific mechanisms for such a failure; other
cross-target mixed segments catch generic compound-note framing and
unanticipated interactions.

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
6. Give the 18 anchors, filtered from that frozen order, to two separately
   initialized candidate invocations with identical configuration and
   candidate seed. Preserve both complete anchor-only outputs.
7. Give all 27 vectors in the frozen order to two more separately initialized
   invocations with that same configuration and candidate seed. Preserve both
   complete joint outputs.
8. Within each identical-input pair, canonicalize the output as an unordered
   collection of unordered member-ID sets. The two canonical outputs must be
   identical. Otherwise record a repeatability failure and do not score the
   semantic hypothesis.
9. After all four outputs are immutable, reveal the fixture identities and
   verify the blinding derivations. If repeatability succeeded, validate the
   anchor-only baseline and score the joint-run hypothesis only when that
   baseline is valid. Preserve and verify the artifacts even when repeatability
   failed.

Before canonicalization, require every returned segment to be a nonempty set
of IDs present in that invocation. To canonicalize one output:

1. encode every 32-byte opaque ID as 64 lowercase hexadecimal characters;
2. sort the IDs inside each segment by their underlying bytes;
3. encode each segment as a compact JSON array of those strings;
4. sort those segment encodings lexicographically by their UTF-8 bytes while
   retaining duplicate member sets as separate entries; and
5. encode the outer list as compact UTF-8 JSON with no trailing newline and
   compute SHA-256 over those exact bytes.

Repeatability compares those canonical bytes, not only their hashes. The hash
is retained for the run record.

## Pass rule

An invalid anchor-only baseline or a repeatability failure produces no
Experiment 4 verdict. Once the baseline is valid, apply the following order:

1. A competing supported membership or cross-target mixed segment fails the
   experiment, even if a joint reference graph is disconnected.
2. Otherwise, a disconnected joint reference graph produces no verdict. It
   shows that adding the mixed vectors globally changed the candidate's
   reference structure, but does not isolate unmasked context from general
   collection instability.
3. With all six joint reference graphs connected, a mixed target missing
   meaningful membership in its masked subject fails the experiment.
4. The experiment passes only when every mixed target has its required
   meaningful membership and none of the failure conditions above occurs.

Report these result classes separately:

- missing anchor-only reference;
- repeatability failure;
- disconnected reference graph in the joint run;
- mixed target missing meaningful membership in its masked subject;
- mixed target receiving competing support from its matching unmasked context;
- mixed target receiving support from any other competing subject;
- cross-target mixed segment, classified when applicable as context-lure or
  form-lure support;
- other unsupported auxiliary segments.

One missing target membership or one competing supported membership is not
averaged away. One cross-target mixed segment also fails the experiment. Other
unsupported auxiliary segments are diagnostic and do not decide the verdict.

## Required record

Preserve:

- the complete returned fine-segment collection from all four invocations;
- every segment's projection onto the 18 anchor IDs;
- anchor-only validity, all reference segments, and all six anchor graphs;
- all joint reference segments and anchor graphs;
- every mixed target's meaningful and competing supported segments;
- every context-lure, form-lure, and other cross-subject merge;
- the exact opaque-ID mapping and input order for both input conditions;
- canonical output hashes and equality results for both identical-input pairs;
- the blinding seed, its pre-run commitment, and successful post-run
  verification of every derived ID and order key;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the candidate configuration and candidate seed.

If either identical-input pair disagrees, preserve all four raw outputs and
the repeatability evidence, but mark anchor validity, reference graphs,
memberships, and the semantic verdict as unevaluated rather than choosing one
of the conflicting outputs.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that, in this fixture, the candidate first recovered six clean
anchor-supported references, preserved connected versions of those references
when the mixed vectors were added, placed every mixed vector in its masked
subject's reference, placed none in a segment supported by a competing
subject, and produced no treatment-only segment spanning different masked
subjects.

An invalid anchor-only baseline or repeatability failure has no Experiment 4
interpretation. A disconnected joint reference graph is also inconclusive
unless direct competing membership or a cross-target mixed segment
independently establishes a failure. Once the joint references remain
connected, missing target membership or competing supported membership is a
failure. Unsupported auxiliary segments remain diagnostic because their
existence alone does not establish a recurring subject.

The recorded lure classes and raw-vector geometry can help explain a failure,
but do not prove its mechanism. A smaller matched follow-up should isolate
semantic meaning, syntax, length, or position only after a failure occurs.

This experiment does not test automatically generated masks, natural
correlated notes, unequal density, every possible context position,
input-order or candidate-seed invariance, context-loaded paraphrases of the
target masks, or hierarchy quality.
