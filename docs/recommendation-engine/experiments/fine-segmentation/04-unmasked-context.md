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

When the same selected text is encoded alone and inside notes with different
unmasked contexts, does each context-loaded vector retain the no-context
control's relationships to the recovered subjects?

## Design

The same frozen vectors are used in two input conditions. Each condition is
repeated in two fresh candidate invocations:

1. An **anchor-only baseline** contains the nine fully masked target anchors
   and nine fully masked context anchors.
2. A **joint coexistence run** contains those 18 anchors plus the nine mixed
   targets crossing every target subject with every context subject.

The anchor-only baseline establishes six reference subjects before mixed
vectors can affect the candidate's output. In the joint run, compare each mixed
target with its exact no-context control separately against each recovered
subject. This asks whether unmasked context changed a relationship; it does not
require the control's relationships themselves to be ideal.

Each target reference contains one fully masked anchor whose selected text is
exactly the same as its three mixed targets' masks, plus two independent
paraphrases. The exact anchor ensures that the no-context version of the mask
is present in the joint collection; the paraphrases prevent literal repetition
from defining the reference by itself.

The subject being compared must qualify in the baseline. The masked-subject
comparison always requires that subject's joint reference. A foreign-subject
comparison additionally requires its joint reference only when both
relationships are absent; a directly present foreign relationship can be
compared without that pure reference. The existing anchors provide these
checks; no additional arm is required.

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
  literal repetition alone. Scoring compares each mixed target with that exact
  control, subject by subject, in the same joint output. The mixed target and
  control need not share one segment directly.
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

A vector whose declared subject is `S` has a **relationship to `S`** when it
belongs to at least one reference segment for `S`. A vector whose declared
subject is not `S` has a **relationship to `S`** when it belongs to any
returned segment containing at least one other vector whose declared subject
is `S`. This applies identically whether that other vector is an anchor or a
mixed target: the candidate itself proposed the cross-subject relationship,
while the separately recovered reference establishes what `S` means.

For a mixed target, its relationship to its unmasked-context subject is the
**matching-context relationship**. Relationships to the four remaining
foreign subjects are recorded separately. A segment containing mixed targets
with different masked subjects creates a relationship for each represented
target to the other's declared subject; each relationship is scored under its
own prerequisites.

One-vector segments and segments without two same-subject anchors do not
define a reference subject. They remain part of the candidate output. A
multi-vector segment containing a tested vector and another vector with a
different declared subject is a direct returned relationship and is scored as
described above. Evidence is not aggregated across separate segments.

This is deliberately a subject-level membership test. It does not require all
anchors and mixed vectors for one subject to appear in one six-vector segment,
nor does it require their complete sets of segment IDs to match. Different
anchor-supported pure segments can represent the same declared subject.

## Anchor-only baseline qualification

First apply the shared output-validity and repeatability checks. In a valid,
repeatable anchor-only baseline, qualify each declared subject independently.
One subject qualifies when its reference anchor graph is connected.

Other baseline segments, including cross-subject segments, singletons, and
same-subject overlaps, remain in the diagnostic record. They do not erase an
otherwise connected pure reference.

Each qualified graph and its reference segments form that subject's baseline
reference. An invalid raw output is an **output-contract failure** and
disagreeing valid repetitions are a **repeatability failure**; either blocks
all six baseline subjects. In a valid, repeatable output, a subject whose pure
reference graph is disconnected has a **local baseline prerequisite failure**.
For a failed subject `S`, every target-to-`S` comparison is withheld. A mixed
target masked as `S` also lacks a complete six-subject result, but its five
foreign-subject comparisons remain independently scoreable when their own
prerequisites hold. Baseline qualification uses only output preserved before
the mixed vectors enter the joint candidate run.

## Frozen hypothesis

In the joint coexistence run, a subject's reference is available when its pure
joint anchor graph is connected. Cross-subject anchor overlaps are recorded as
collection diagnostics; they do not erase a pure connected reference.

For each mixed target, compare it with the exact no-context control for its
masked text against each of the six declared subjects. Only the subject being
compared must qualify in the anchor-only baseline. Failure of the masked
subject's own baseline or joint-reference prerequisite withholds its
masked-subject comparison and its complete six-subject result, but it does not
erase independently scoreable foreign-subject comparisons.

For the masked-subject comparison, the joint target reference must also be
available. For a foreign-subject comparison, first compute the control's and
mixed target's direct relationship booleans. If either relationship is
present, their equality or difference is directly observable even when the
foreign subject's pure joint reference disconnected. If both are absent, the
foreign joint reference must be available before that shared absence can count
as a pass; otherwise the comparison has no verdict.

For an available comparison, equal booleans are a
**subject-relationship pass**. Different booleans are a
**context-membership-change failure**, recorded as either a gained or lost
relationship.

This is a difference test. An unrelated control relationship does not suppress
a comparison with another subject, and a relationship shared by the control
and mixed target is stable for this experiment even if it is undesirable for
another reason. Requiring every control to be globally clean would conflate
unmasked-context sensitivity with general segmentation quality and erase
independent evidence.

The comparison against the masked target subject tests retention. The
comparison against the declared unmasked-context subject is the
matching-context comparison. The other four comparisons detect unrelated
gained or lost relationships. A mixed target passes completely only when all
six comparisons are available and pass. A failure in one comparison remains
scoreable when another comparison lacks its own subject reference.

Complete segment-ID signatures are not compared: an auxiliary singleton or
same-subject overlap does not by itself show that unmasked material changed a
subject relationship. The frozen context-lure and form-lure groups remain
diagnostics for patterns across multiple failures; they do not replace the
subject-by-subject verdicts.

## Frozen system boundary

Use the shared execution contract and 768-dimensional Sentence-T5-base SSE
checkpoint in [README.md](README.md).

Preserve its raw outputs exactly. Any normalization, distance, or other
preprocessing belongs to the candidate's frozen configuration.

The candidate receives only opaque IDs and vectors. It may return overlapping
fine segments and leave vectors unassigned. Scoring consumes only its
predeclared fine-segment collection; coarser parents are excluded.

This is a visible development fixture, not held-out confirmation.

## Protocol

1. Obtain human approval of all 27 notes, masks, subject identities, and
   expected relationships.
2. Freeze this document and the complete candidate identity, and document the
   candidate's construction-level permutation invariance.
3. Apply the shared opaque-ID blinding and frozen-order rules once to all 27
   fixture IDs. The anchor-only input is the 18-anchor subsequence of that one
   frozen order; the joint input is the full 27-vector order.
4. Freeze the SSE boundary and exact input bytes, then generate all 27
   full-note vectors once and record their dimensions and hashes.
5. Give the 18 anchors to two separately
   initialized candidate invocations with identical configuration and
   candidate seed. Preserve both complete anchor-only outputs.
6. Give all 27 vectors to two more separately initialized
   invocations with that same configuration and candidate seed. Preserve both
   complete joint outputs.
7. While identities remain hidden, validate every raw output under the shared
   output contract. An empty segment, unknown ID, repeated member within a
   segment, or duplicate member set is an output-contract failure. Do not
   canonicalize an invalid output or derive a semantic verdict from it.
8. For each valid identical-input pair, compare the shared canonical JSON
   bytes. A mismatch is a repeatability failure and receives no semantic
   verdict.
9. After all four outputs are immutable, reveal and verify the fixture mapping.
   Qualify each anchor-only subject reference, then each corresponding joint
   reference. Compare each mixed target with its exact control against all six
   subjects under the local prerequisites above. Preserve and verify all
   artifacts even when one comparison is withheld.

## Pass rule

An anchor-only output-contract or repeatability failure blocks baseline
qualification and every dependent semantic verdict. A joint output-contract or
repeatability failure preserves any independent baseline qualification but
produces no joint-reference or unmasked-context verdict. In a valid,
repeatable anchor-only output, a subject that does not qualify has a local
baseline prerequisite failure; only comparisons that depend on that subject
receive no verdict.

In a valid, repeatable joint output, make each subject's pure anchor graph. Its
joint reference is available when that graph is connected. A disconnected
pure graph is a **local joint-reference prerequisite failure** for that
subject. Cross-subject anchor overlaps remain diagnostics; they do not erase
an otherwise connected pure reference.

For each mixed target, score in this order:

1. For each declared subject `S`, require `S` to qualify in the anchor-only
   baseline. If it did not, only the target-to-`S` comparison has no verdict.
2. Compute the no-context control's relationship to `S` and the mixed target's
   relationship to `S`.
3. If `S` is the masked target subject, require its joint reference to be
   available. If `S` is foreign and both relationships are absent, require its
   joint reference to be available. A missing required joint reference gives
   only that comparison no verdict.
4. For every available comparison, equal booleans pass. Unequal booleans fail
   and are recorded as a gained or lost relationship.

The experiment fails when any eligible subject-by-subject comparison differs.
It passes only when all 54 mixed-target-to-subject comparisons are available
and pass. Those comparisons already require every baseline reference and every
joint reference needed to interpret an absent relationship. If no eligible
comparison fails but any comparison is withheld, the experiment has no overall
context verdict. Do not average targets or subjects.

Report these result classes separately:

- output-contract failure;
- repeatability failure;
- local anchor-only prerequisite failure for each subject;
- local joint-reference prerequisite failure for each subject;
- context-membership-change failure for each eligible gained or lost
  relationship, classified as masked-subject, matching-context, or other
  subject;
- stable subject relationship for each eligible equal control/mixed result,
  preserving whether both relationships were present or both were absent;
- cross-target mixed segment, with a separate scoped result for every mixed
  target represented and classification when applicable as context-lure or
  form-lure support;
- subject comparison withheld because the compared subject failed a local
  prerequisite;
- other joint-output shape changes that do not alter a local chain, as
  collection diagnostics;
- other unsupported auxiliary segments.

One eligible gained or lost relationship is not averaged away. Other output
shape changes that preserve all scored subject relationships are diagnostic
and do not decide the verdict.

## Required record

Preserve:

- the complete returned fine-segment collection from all four invocations;
- for each valid output, every segment's projection onto the 18 anchor IDs;
- every raw output-validity result and, for each valid output, its canonical
  JSON byte string and hash;
- both repeatability comparisons;
- every subject's anchor-only qualification, every anchor in a cross-subject
  segment, all reference segments, and all six anchor graphs;
- each subject's pure joint anchor graph, reference segments, and resulting
  reference availability;
- for every mixed-target-to-subject comparison, its exact no-context control,
  both vectors' complete supporting segments, both relationship booleans, all
  local prerequisite states, the equal/different result, and the gained/lost
  classification when different;
- every mixed target's six subject comparisons and complete target result;
- every context-lure, form-lure, and other cross-subject merge;
- the exact opaque-ID mapping and input order for both input conditions;
- the shared blinding seed, its pre-run commitment, and successful post-run
  verification of every derived ID and order key;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the complete candidate identity required by the shared contract.

If the anchor-only pair has an output-contract or repeatability failure,
preserve all four raw outputs and mark baseline qualification and every
dependent result as **no verdict because anchor-only integrity failed**. If
only the joint pair has an output-contract or repeatability failure, preserve
every independently valid per-subject baseline qualification and mark joint
reference graphs, subject comparisons, and context verdicts as **no verdict
because joint-input integrity failed**. Never repair an output or choose one of
two conflicting outputs.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that, in this fixture, the candidate recovered all six baseline
references and gave each context-loaded vector the same relationship to every
declared subject as its exact no-context control. Every joint reference needed
to interpret an absent relationship remained available.

An output-contract or repeatability failure has no Experiment 4 semantic
interpretation. A local anchor-only prerequisite failure blocks only mixed
targets whose specific comparison needs that subject. A local joint-reference
prerequisite failure means an anchor subject that qualified in the baseline no
longer provides an interpretable joint reference. It withholds that subject's
masked-subject comparison and any foreign comparison that relies on shared
absence; directly present foreign relationships remain comparable. A
context-membership-change failure means the mixed vector gained or lost one
subject relationship that its exact no-context control did not. Unchanged but
undesirable relationships are not Experiment 4 failures; this protocol tests
sensitivity to unmasked context, not general segment correctness. Auxiliary
shape changes remain diagnostic.

The recorded lure classes and raw-vector geometry can help explain a failure,
but do not prove its mechanism. A smaller matched follow-up should isolate
semantic meaning, syntax, length, or position only after a failure occurs.

This experiment does not test automatically generated masks, natural
correlated notes, unequal density, every possible context position,
input-order or candidate-seed invariance, context-loaded paraphrases of the
target masks, or hierarchy quality.
