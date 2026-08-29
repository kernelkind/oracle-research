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

Each mixed target is compared with its target subject's exact fully masked
control in that same joint run. This matched control separates a collection-wide
change caused by adding nine vectors from a change specific to the mixed
target's unmasked context. The three controls already declared below provide
all nine comparisons; no additional input condition or control arm is needed.

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
  control in the same joint output. Meaningful membership still uses the
  anchor-supported subject reference; the mixed target and control need not
  share one segment directly.
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

## Anchor-only baseline qualification

First apply the shared output-validity and repeatability checks. A valid,
repeatable anchor-only baseline qualifies only when:

1. the reference anchor graph for each of the six declared subjects is
   connected; and
2. no anchor has competing supported membership in another declared subject.

Other baseline segments, including singletons and unsupported overlaps,
remain in the diagnostic record. They do not establish or invalidate a
reference subject by themselves.

The six connected anchor graphs and their reference segments are the baseline
references. An invalid raw output is an **output-contract failure**; disagreeing
valid repetitions are a **repeatability failure**; a valid, repeatable baseline
that fails either qualification above is a **prerequisite failure**. None
receives a semantic verdict. Baseline qualification uses only output preserved
before the mixed vectors enter the joint candidate run.

## Frozen hypothesis

In the joint coexistence run, each mixed target is scored only after its
matched exact fully masked control qualifies. A control qualifies when it has
meaningful membership in its declared target subject and no competing
supported membership. Once that control qualifies:

1. the mixed target has meaningful membership in its masked target subject;
2. the mixed target has no competing supported membership in one of the other
   five declared subjects; and
3. no control-qualified cross-target mixed segment occurs.

If a control that qualified in the anchor-only baseline loses meaningful
membership in its target subject or gains competing supported membership in
the joint run, classify **collection instability** and withhold the
unmasked-context verdict for each mixed target matched to that control. Do not
use a mixed target's result to reinterpret its failed control.

The second condition includes the matching unmasked-context subject. It also
catches support from an unrelated target or context subject. Complete
segment-ID signatures are not compared: an auxiliary singleton or unsupported
overlap does not by itself show that unmasked material changed meaningful
subject membership. The third condition is different: mixed vectors with
different masked subjects recurring together form a treatment-only
cross-subject region even without anchors. The frozen context-lure and
form-lure groups identify two specific mechanisms for such a failure; other
cross-target mixed segments catch generic compound-note framing and
unanticipated interactions. Such a segment is a context failure only when the
matched controls for every represented target subject qualify; otherwise it
remains diagnostic while the failed control supplies the collection-instability
classification.

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
   Qualify the anchor-only baseline before scoring the matched controls and
   mixed targets in a valid, repeatable joint output. Preserve and verify all
   artifacts even when scoring is withheld.

## Pass rule

An anchor-only output-contract or repeatability failure blocks baseline
qualification and every dependent semantic verdict. A joint output-contract or
repeatability failure preserves any independent baseline qualification but
produces no joint-control or unmasked-context verdict. A valid, repeatable
anchor-only output that does not qualify is a prerequisite failure and also
produces no semantic verdict.

Once the anchor-only baseline qualifies, score the valid, repeatable joint
output in this order:

1. For each mixed target, inspect its matched exact fully masked control in the
   same joint output. If the control lacks meaningful membership in its target
   subject or has competing supported membership, record collection
   instability and withhold the context verdict for that mixed target.
2. When the matched control qualifies, fail that mixed target if it lacks
   meaningful membership in its masked target subject or has competing
   supported membership. Otherwise its membership comparison passes.
3. A segment containing mixed targets from different declared target subjects
   is a context failure only when the matched controls for every represented
   target subject qualify. If any such control does not qualify, preserve the
   segment as a diagnostic; it does not override the collection-instability
   classification or create a context verdict.

The experiment fails when any eligible mixed target fails its membership
comparison or any control-qualified cross-target mixed segment occurs. It
passes only when every mixed target receives and passes a context verdict and
no control-qualified cross-target mixed segment occurs. If no eligible target
fails but one or more target verdicts are withheld for collection instability,
the experiment has no overall context verdict. Do not average targets.

Report these result classes separately:

- output-contract failure;
- repeatability failure;
- anchor-only prerequisite failure, distinguishing a missing reference graph
  from an anchor with competing supported membership;
- collection instability for a matched fully masked control, distinguishing
  lost target membership from gained competing supported membership;
- mixed target missing meaningful membership in its masked subject;
- mixed target receiving competing support from its matching unmasked context;
- mixed target receiving support from any other competing subject;
- control-qualified cross-target mixed segment, classified when applicable as
  context-lure or form-lure support;
- cross-target mixed segment withheld by a nonqualifying matched control;
- disconnected reference graph in the joint run, as a collection diagnostic;
- other unsupported auxiliary segments.

One missing target membership or one competing supported membership after its
matched control qualifies is not averaged away. One cross-target mixed segment
whose represented-subject controls qualify also fails the experiment. Other
unsupported auxiliary segments are diagnostic and do not decide the verdict.

## Required record

Preserve:

- the complete returned fine-segment collection from all four invocations;
- for each valid output, every segment's projection onto the 18 anchor IDs;
- every raw output-validity result and, for each valid output, its canonical
  JSON byte string and hash;
- both repeatability comparisons;
- anchor-only qualification, every anchor with competing supported membership,
  every multiply supported segment, all reference segments, and all six anchor
  graphs;
- all joint reference segments and anchor graphs;
- each exact fully masked control's meaningful and competing supported
  segments and the resulting per-target control qualification;
- every mixed target's meaningful and competing supported segments and its
  matched context verdict;
- every context-lure, form-lure, and other cross-subject merge;
- the exact opaque-ID mapping and input order for both input conditions;
- the shared blinding seed, its pre-run commitment, and successful post-run
  verification of every derived ID and order key;
- cosine matrices and nearest-neighbor orders computed from immutable raw SSE
  outputs;
- the raw SSE artifact and hashes;
- the complete candidate identity required by the shared contract.

If the anchor-only pair is invalid or non-repeatable, preserve all four raw
outputs and mark baseline qualification and every dependent result
unevaluated. If only the joint pair is invalid or non-repeatable, preserve the
independently valid baseline qualification and mark joint reference graphs,
memberships, control comparisons, and context verdicts unevaluated. Never
repair an output or choose one of two conflicting outputs.

Cosine is diagnostic evidence. The verdict is determined by returned
fine-segment membership.

## What a result means

A pass shows that, in this fixture, the candidate first recovered six clean
anchor-supported baseline references, then kept each exact fully masked target
control in its target reference and out of competing supported memberships in
the joint collection. Against those same-run controls, every mixed target kept
its masked-subject membership, gained no competing supported membership, and
formed no control-qualified segment spanning different masked subjects.

An output-contract failure, repeatability failure, or anchor-only prerequisite
failure has no Experiment 4 semantic interpretation. Collection instability
means the exact fully masked control changed after the joint collection was
introduced, so the corresponding mixed target cannot isolate unmasked context
and its context verdict is withheld. Once that control qualifies, missing
target membership or competing supported membership in the mixed target is a
context failure. A cross-target mixed segment is a context failure only after
the controls for all represented target subjects qualify. Disconnected joint
reference graphs and unsupported auxiliary segments remain diagnostic unless
they produce one of those matched membership outcomes.

The recorded lure classes and raw-vector geometry can help explain a failure,
but do not prove its mechanism. A smaller matched follow-up should isolate
semantic meaning, syntax, length, or position only after a failure occurs.

This experiment does not test automatically generated masks, natural
correlated notes, unequal density, every possible context position,
input-order or candidate-seed invariance, context-loaded paraphrases of the
target masks, or hierarchy quality.
