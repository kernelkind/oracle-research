# SSE Multi-Vector Isolation Experiment

## Status

The neutral 32-note input is frozen in
[`sse-multivector-note-set-v2.json`](./sse-multivector-note-set-v2.json). It
contains 32 real Nostr notes from 32 authors and presupposes no subjects.

Subject enumeration and independent mask generation have run over every raw
note using the approved minimal prompts. Each note used a fresh subject call,
and every resulting subject used a separate fresh mask call. Their audited,
source-bound output was saved as
`sse_multivector/subject-mask-proposal-v3.json`:

- 190 subjects generated;
- 187 subjects retained after the primary agent inspected every proposal;
- 248 exact text fragments;
- zero `unsupported` mask results.

The audit removed three incidental subjects, corrected four labels, and
narrowed masks that contained text belonging to another subject. The prompts
are recorded verbatim in the artifact.

SSE inference and the diagnostic analysis are complete. The run used the
released full-dimensional Sentence-T5-base checkpoint:

- 768 output dimensions;
- checkpoint SHA-256
  `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`;
- `sentence-transformers/sentence-t5-base` tokenizer and configuration at
  revision `fc5d4628481afbbaaacd7af6bb07cf9d3865f781`;
- base-model artifact-tree SHA-256
  `bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d`;
- immutable local container image ID
  `a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa`.

The intended full-dimensional Sentence-T5-large checkpoint is not among the
authors' released checkpoints. The full-dimensional base checkpoint avoids
substituting their released 64-dimensional large model into a geometry
experiment.

Before the real run, the worker reproduced the two similarities published in
the official Dracula example: `0.29089065` and `0.71797654`, which round to the
published `0.2909` and `0.7180`. The real run then generated all 187 vectors.
Its deterministic replay verified every source binding and generated file. The
original archive and verification records are described by the
[`narrowest-subject-v1` baseline](../../../sse_multivector/baselines/narrowest-subject-v1/README.md).
The archive remains with the local research originals. Selected final
measurements are prepared for Hugging Face Datasets; see the
[publication files](../../../sse_multivector/baselines/narrowest-subject-v1/README.md#publication-files)
and [reproduction guide](../../experiments/reproduce.md#archived-baseline-checks).

The upstream release provides neither a checkpoint checksum nor an explicit
license. This repository does not redistribute the checkpoint. The recorded
hash binds this run to the file obtained from the authors' official Drive ID,
name, and advertised byte size; it does not independently authenticate the
publisher.

## Question Tested

Given audited subjects and their exact supporting text, can SSE produce
a useful separate vector for each subject expressed within a note?

This requires more than broad topical similarity. A mask vector must retain
the meaning of its selected text in the original post context while excluding
the post's other meanings.

## Input Preparation

The controlled inputs were prepared in this order:

1. One isolated call enumerated the subjects for each complete note.
2. One isolated call generated the mask for each subject.
3. The coordinator rejected schema errors, changed note text, absent
   substrings, and out-of-order substrings.
4. The primary agent read every subject and mask, then corrected only concrete
   overstatement, negation, incidental-subject, and cross-subject-mask errors.

The complete note remains encoder context. Only the audited exact span or
spans are pooled into that subject's vector. Discontinuous spans are allowed
only when every span directly expresses the same subject.

## What This Establishes

This audit makes the set usable as controlled inputs. It does not establish
that subject enumeration or masking can operate autonomously.

The SSE analysis asks whether separate masks from one note lead to
meaningfully separate semantic representations. That analysis does not cover
corpus-wide subject discovery, hierarchy construction, content recommendation,
or ranking.

## Diagnostic Analysis

This is exploratory analysis, not a pass/fail evaluation. It characterizes the
geometry produced by SSE so that a later experiment can ask a precise question
without inventing a threshold first.

The first analysis uses only the 187 audited subject masks:

1. Pin the SSE checkpoint, tokenizer, revision, pooling behavior, runtime
   configuration, and artifact hashes.
2. Generate one vector for each subject by giving SSE the complete note and
   that subject's mask. Subject labels are report metadata and must never be
   encoder input.
3. Verify one consistent dimension, finite values, and nonzero norms, then
   retain both the raw and L2-normalized vectors.
4. Calculate the complete exact cosine matrix: 17,391 unordered pairs,
   consisting of 638 same-note pairs and 16,753 cross-note pairs.
5. For every same-note pair, record its cosine and selected-token overlap.
   Disjoint masks must be interpreted separately from overlapping or nested
   masks.
6. For every subject, report its five nearest subjects from other notes with
   their labels, exact fragments, cosine values, and global cross-note
   percentile.
7. Summarize the raw same-note and cross-note similarity distributions. Split
   same-note pairs by mask overlap, and report whether each subject's nearest
   overall neighbor came from its own note or another note.
8. Retain the complete matrix and rankings so the five-neighbor display is not
   a data cutoff.

The written report must keep measurements separate from interpretation. It
should identify concrete examples of:

- useful separation: subjects from one note lead to different external
  neighborhoods;
- useful convergence: independently worded subjects from different notes are
  close;
- blending: distinct masks from one note remain effectively inseparable;
- context or lexical leakage: neighbors reflect surrounding or shared wording
  instead of the masked subject.

Same-note subjects may legitimately be related, and overlapping masks
mechanically share evidence. The generated labels are audited descriptions,
not independent ground truth. The 32 notes are diagnostic cases, not a
representative Nostr sample, and cosine has no universal semantic cutoff.

Do not add a pass threshold, expected-positive pair labels, clustering,
hierarchy construction, model comparison, whole-note or span-only baselines,
or dimensionality-reduction plots to the first analysis. Add a narrower
follow-up only when the first report exposes a specific ambiguity it can
resolve.

## Measurements

The completed analysis contains:

- 187 finite, nonzero 768-dimensional vectors;
- 17,391 unique unordered pairs;
- 638 same-note pairs and 16,753 cross-note pairs;
- complete cross-note rankings for every subject.

Measured cosine distributions:

| Pair group | Count | Median | Mean | p95 |
|---|---:|---:|---:|---:|
| Cross-note | 16,753 | 0.0266 | 0.0454 | 0.2699 |
| Same-note | 638 | 0.2434 | 0.2822 | 0.7373 |
| Same-note, disjoint selected tokens | 522 | 0.1945 | 0.2145 | 0.5550 |
| Same-note, overlapping or nested selected tokens | 116 | 0.5911 | 0.5867 | 0.8539 |

The nearest overall vector came from the same note for 118 subjects and from
another note for 69. Of the 118 same-note cases, 76 shared selected tokens and
42 used disjoint selected tokens.

High cross-note similarity was sparse: 95 of 16,753 cross-note pairs reached
`0.5`, and 15 reached `0.7`.

These are measurements, not quality thresholds. In particular, selecting the
best result from many candidates makes even an incorrect nearest neighbor rank
highly within the global cross-note distribution.

## Concrete Observations

### Useful separation

Some disjoint masks from the same complete note produced clearly different
vectors:

- “Regular posts about useful open-source technology” versus “Passphrase
  encryption for messages”: `-0.1116`.
- “The mismatch between public agreement and private agreement” versus “The
  appeal of flavored coffee”: `-0.0484`.

This demonstrates that complete-note context does not always collapse
unrelated masked subjects into one representation.

### Useful cross-note convergence

Some independently written subjects converged strongly:

- free and open-source software as the path to technological sovereignty
  versus nearing a completely free and open-source software stack: `0.7181`;
- pervasive operating-system telemetry versus Ledger Live tracking every user
  action: `0.6258`;
- excessive BitAxe fan noise versus an Avalon/Bitaxe noise comparison:
  `0.7064`;
- future solar generation versus solar power for a greenhouse: `0.7394`.

These examples show genuine reusable semantic signal. They do not establish an
accuracy rate because the 32-note set has no independently labeled expected
pairs.

### Strong false neighbors

Several high-ranked pairs matched surface wording rather than the intended
subjects:

- “A day/night miner operating mode” versus wanting to finish a book
  “tonight”: `0.4513`;
- “Four working rooftop solar panels” versus the book title *The Fourth
  Revolution*: `0.4281`;
- charging a car versus switching a child's car seat: `0.4828`;
- tracking code versus “No proprietary blobs/code”: `0.5444`.

All four are above the 98th percentile of cross-note similarities in this run.
That percentile alone does not establish quality because each subject was
compared with many candidates. The fragments themselves establish the
surface-word mismatch; the cosine values show that the mismatch is not
represented as distant by this geometry.

### Same-note influence

Selected-token overlap had a large mechanical effect. Overlapping or nested
masks had a median same-note cosine of `0.5911`, compared with `0.1945` for
disjoint masks.

Disjoint same-note vectors also remained closer than cross-note vectors in
aggregate. This is consistent with whole-note context influencing the output,
but it is not by itself proof of harmful leakage: atomic subjects expressed
together are often legitimately related. The strongest high-similarity
same-note examples were themselves related, so this run does not support a
clean numerical estimate of harmful blending.

## Interpretation

The run supports a limited conclusion:

> The released SSE model can produce distinct subject-conditioned vectors
> from one note and can recover some recognizable subjects across notes.

It does not support the stronger conclusion that its geometry is already a
reliable atomic-subject map. Surface-word false matches and measurable
same-note influence could create incorrect fine-region assignments if cosine
were used uncritically.

The run left one specific ambiguity: how much of each vector represented the
masked subject, and how much represented surface wording or surrounding note
context? This run alone did not justify clustering, hierarchy construction, or
corpus-scale processing.


## Mask-fidelity evidence

The following controlled experiments test masks supplied to SSE. They do not
validate autonomous subject extraction or complete hierarchy generation. Their
original cases, pass rules, measurements and limitations are retained below.

## Evidence overview

### Scope

These experiments test whether SSE vectors preserve the atomic-subject
relationships needed by the content hierarchy.

SSE does not discover masks. For each input, another process supplies:

1. the complete note; and
2. the selected source-token positions.

SSE processes the complete note, averages the contextual token representations
at the selected positions, and applies its learned output transformation.

The evidence below is conditional on the supplied masks. It does not validate
automatic subject extraction, fine segmentation, hierarchy construction, or
navigation quality. The later fine-segmentation suite contains two integration
experiments that re-encode controlled text changes through SSE and then inspect
candidate memberships; those results qualify the frozen SSE-plus-candidate
combination rather than either component alone.

### Controlled Synthetic Evidence

#### Single-fragment masks

- The
  [`../../sse_multivector/mask-fidelity-single-fragment-factorial-v3/result/analysis.md`](../../../sse_multivector/mask-fidelity-single-fragment-factorial-v3/result/analysis.md)
  passed all 432 predeclared context, paraphrase, and different-subject
  comparisons.
- The
  [`../../sse_multivector/mask-fidelity-single-fragment-boundary-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-single-fragment-boundary-v1/result/analysis.md)
  passed all 72 comparisons.
- The complete readable cases are also recorded in
  [single-fragment cases](#single-fragment-mask-experiments).

These results show strong behavior on the tested synthetic subjects. They do
not establish arbitrary real-note performance.

#### Multi-fragment masks

- The
  [`../../sse_multivector/mask-fidelity-multifragment-requirements-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-multifragment-requirements-v1/result/analysis.md)
  passed its fragment-count, boundary, wording, redundancy, and unselected-text
  comparisons.
- A stricter
  [`../../sse_multivector/mask-fidelity-multifragment-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-multifragment-v1/result/analysis.md)
  failed one of three families, but complete and fragmented masks behaved
  similarly; the evidence did not attribute the family failure to
  fragmentation.
- The complete readable cases are also recorded in
  [multi-fragment cases](#multi-fragment-mask-experiments).

#### Known limits

- [`../../sse_multivector/mask-fidelity-location-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-location-v1/result/analysis.md)
  passed all four predeclared comparisons despite unrelated surrounding text.
- [`../../sse_multivector/mask-fidelity-relationship-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-relationship-v1/result/analysis.md)
  failed all four comparisons: SSE did not reliably distinguish who chased
  whom when the same entities and action appeared in reversed relationships.
- [`../../sse_multivector/mask-fidelity-compound-subject-neighborhood-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-compound-subject-neighborhood-v1/result/analysis.md)
  passed two of three subject families. The solar-powered-greenhouse family
  narrowly failed its local-neighbor rule.

The synthetic evidence therefore supports some subject relationships but not a
general claim that SSE preserves every relation expressed by selected text.

### Fine-segmentation integration run

The controlled HDBSCAN*/SNN suite completed on 2026-09-01. Its Experiment 3
and 4 results qualify the frozen SSE-plus-candidate combinations rather than
SSE alone. HDBSCAN* passed all three lexical traps and six of nine
unmasked-context treatments; three context treatments had no verdict after a
local relationship stopped qualifying. SNN's local baselines did not qualify
for either integration experiment. Both candidates exceeded the frozen
semantic-review cap. See the
[complete result](fine-segmentation/controlled-run-v1-results.md).

### Real-Note Evidence

The exploratory
[`SSE Multi-Vector Isolation Experiment`](#sse-multi-vector-isolation-experiment)
encoded 187 manually audited atomic-subject masks from 32 real notes. It found
useful within-note separation and cross-note convergence, alongside
surface-word false neighbors and measurable same-note influence. It was a
diagnostic, not a pass/fail validation.

The
[real-note holdout experiment](#real-note-holdout-mask-experiment)
passed three of four predeclared comparisons. The hard Windows/Linux case
failed, leaving nearby technical-subject resolution unresolved.

The later
[`../../sse_multivector/mask-fidelity-real-note-transfer-v5/result/analysis.md`](../../../sse_multivector/mask-fidelity-real-note-transfer-v5/result/analysis.md)
passed six of eight comparisons and failed its strict overall criterion:

- mining-hardware noise passed;
- pervasive software telemetry passed one of two comparisons; and
- solar-powered mining passed three of four comparisons.

Two counterfactuals clarified those failures without erasing them:

- Selecting the direct telemetry statement made the intended telemetry edge
  strongest in its comparison
  ([`../../sse_multivector/mask-fidelity-telemetry-mask-counterfactual-v1/result/analysis.md`](../../../sse_multivector/mask-fidelity-telemetry-mask-counterfactual-v1/result/analysis.md)).
- Removing unselected context moved the solar-mining comparison to an almost
  exact tie with its solar-only control
  ([`../../sse_multivector/mask-fidelity-solar-context-ablation-v4/result/analysis.md`](../../../sse_multivector/mask-fidelity-solar-context-ablation-v4/result/analysis.md)).

The earlier
[`SSE context counterfactual experiment`](../../../sse_multivector/context-counterfactual-result-v1/README.md)
formally passed 21 of 24 targets and failed its strict overall rule. A later
[`scientific review`](../../../sse_multivector/context-counterfactual-result-v1/scientific-interpretation.md)
found two failed comparisons non-diagnostic and the third sensitive to the
reference aggregation rule; no valid case showed unrelated note content taking
over a selected vector. This remains small, hand-supplied-mask evidence rather
than general validation.

### Conclusion from these experiments

Within these bounded tests, SSE often preserves recognizable atomic-subject
similarity across wording, mask boundaries, multiple fragments, and changed
surrounding text. It also has observed failures, especially for reversed
relationships, surface-word false matches, and some nearby or compound
subjects.

That is enough to continue testing the architecture, not enough to treat SSE
geometry as validated. Subject-mask generation remains a separate upstream
problem. The controlled fine-segmentation test evaluated the frozen HDBSCAN and
SNN candidates against the same frozen SSE vectors and synthetic suite while
preserving each experiment's stated scope. No hierarchy method was selected by these mask-fidelity tests.

## Single-fragment mask experiments

### 1.1) Same mask, different surrounding context

#### Experiment 1.1.1: N01 vs N03

**Description:** N01 is the control. N03 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `on a quiet beach`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Changed context — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Result:** Cosine `0.982316`. The hypothesis was supported for this comparison.

---

#### Experiment 1.1.2: N02 vs N04

**Description:** N02 is the control. N04 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `beside a calm shoreline`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Changed context — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.984553`. The hypothesis was supported for this comparison.

---

#### Experiment 1.1.3: N05 vs N07

**Description:** N05 is the control. N07 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `in a windowless office`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Changed context — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Result:** Cosine `0.980081`. The hypothesis was supported for this comparison.

---

#### Experiment 1.1.4: N06 vs N08

**Description:** N06 is the control. N08 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `inside an office without windows`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Changed context — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.971089`. The hypothesis was supported for this comparison.

### 1.2) Paraphrased mask, same surrounding context

#### Experiment 1.2.1: N01 vs N02

**Description:** N01 is the control. N02 changes only the selected mask from `on a quiet beach` to `beside a calm shoreline`. Both masks describe the same beach location, and the unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Paraphrased mask — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.855579`. The hypothesis was supported for this comparison.

---

#### Experiment 1.2.2: N03 vs N04

**Description:** N03 is the control. N04 changes only the selected mask from `on a quiet beach` to `beside a calm shoreline`. Both masks describe the same beach location, and the unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Paraphrased mask — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.822117`. The hypothesis was supported for this comparison.

---

#### Experiment 1.2.3: N05 vs N06

**Description:** N05 is the control. N06 changes only the selected mask from `in a windowless office` to `inside an office without windows`. Both masks describe the same office location, and the unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Paraphrased mask — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Result:** Cosine `0.946553`. The hypothesis was supported for this comparison.

---

#### Experiment 1.2.4: N07 vs N08

**Description:** N07 is the control. N08 changes only the selected mask from `in a windowless office` to `inside an office without windows`. Both masks describe the same office location, and the unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Paraphrased mask — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.969186`. The hypothesis was supported for this comparison.

### 1.3) Different mask, same surrounding context

#### Experiment 1.3.1: N01 vs N05

**Description:** N01 is the control. N05 changes only the selected mask from the beach location `on a quiet beach` to the office location `in a windowless office`. The unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Different mask — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Result:** Cosine `0.116487`. The hypothesis was supported for this comparison.

---

#### Experiment 1.3.2: N02 vs N06

**Description:** N02 is the control. N06 changes only the selected mask from the beach location `beside a calm shoreline` to the office location `inside an office without windows`. The unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Different mask — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Result:** Cosine `0.086605`. The hypothesis was supported for this comparison.

---

#### Experiment 1.3.3: N03 vs N07

**Description:** N03 is the control. N07 changes only the selected mask from the beach location `on a quiet beach` to the office location `in a windowless office`. The unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Different mask — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Result:** Cosine `0.149702`. The hypothesis was supported for this comparison.

---

#### Experiment 1.3.4: N04 vs N08

**Description:** N04 is the control. N08 changes only the selected mask from the beach location `beside a calm shoreline` to the office location `inside an office without windows`. The unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Different mask — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.081676`. The hypothesis was supported for this comparison.

### Combined Result

- Same masks under different surrounding contexts produced cosine `0.971089–0.984553`.
- Paraphrased masks expressing the same location produced cosine `0.822117–0.969186`.
- Different masked locations under identical surrounding contexts produced cosine `0.081676–0.149702`.

> For explicit narrow masks, SSE can isolate selected meaning without substantial contamination from the rest of the note.

This conclusion is limited to the simple beach-versus-office location distinction tested here.

### 1.4) Same atomic subject under different mask boundaries

#### Experiment 1.4.1: Dog and cat mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The dog and cat notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each dog or cat mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Dog note**
> This story is about the ⟦dog⟧.
>
> This story is about ⟦the dog⟧.
>
> This story is ⟦about the dog⟧.
>
> This story is ⟦about the dog.⟧

**Cat note**
> This story is about the ⟦cat⟧.
>
> This story is about ⟦the cat⟧.
>
> This story is ⟦about the cat⟧.
>
> This story is ⟦about the cat.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.931409–0.994477`; matched different-subject cosines were `0.494654–0.625200`. The smallest margin was `+0.364795`.

---

#### Experiment 1.4.2: Coffee and tea mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The coffee and tea notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each coffee or tea mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Coffee note**
> This discussion is about the ⟦coffee⟧.
>
> This discussion is about ⟦the coffee⟧.
>
> This discussion is ⟦about the coffee⟧.
>
> This discussion is ⟦about the coffee.⟧

**Tea note**
> This discussion is about the ⟦tea⟧.
>
> This discussion is about ⟦the tea⟧.
>
> This discussion is ⟦about the tea⟧.
>
> This discussion is ⟦about the tea.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.954442–0.997088`; matched different-subject cosines were `0.455609–0.550715`. The smallest margin was `+0.446341`.

---

#### Experiment 1.4.3: Bicycle and car mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The bicycle and car notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each bicycle or car mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Bicycle note**
> This report is about the ⟦bicycle⟧.
>
> This report is about ⟦the bicycle⟧.
>
> This report is ⟦about the bicycle⟧.
>
> This report is ⟦about the bicycle.⟧

**Car note**
> This report is about the ⟦car⟧.
>
> This report is about ⟦the car⟧.
>
> This report is ⟦about the car⟧.
>
> This report is ⟦about the car.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.931499–0.995233`; matched different-subject cosines were `0.359477–0.479524`. The smallest margin was `+0.492452`.

### Mask-boundary result

All 72 predeclared comparisons passed. The weakest comparison still favored the unchanged subject by `+0.364795` cosine.

> For these three common matched subject pairs, adding a determiner, preposition, or terminal punctuation to a single-fragment mask affected the SSE vector much less than replacing the atomic subject.

This fills the previously untested single-fragment boundary case. It does not establish the same behavior for arbitrary language, real Nostr notes, or masks containing multiple fragments.

The frozen inputs, every unrounded comparison, and the complete cosine matrix are in `sse_multivector/mask-fidelity-single-fragment-boundary-v1/`.

## Multi-fragment mask experiments

These experiments test the following requirements:

1. Changing the wording, number, boundaries, or redundancy of mask fragments must not materially change the vector when the intended atomic subject remains the same.
2. Changing only text outside the mask should affect the vector less than changing the atomic subject.
3. When changing a fragment changes the human-defined atomic subject, the resulting vector should also become distinguishable from the original vector.

Every control, changed input, and pass condition was frozen before SSE ran. The complete note was given to SSE, but only the text inside `⟦...⟧` was pooled into each vector.

### 2.1) Changing the fragment count without changing the selected words

#### Experiment 2.1.1: Dividing dog playing fetch into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦dog playing fetch⟧.

**Changed — two fragments**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

---

#### Experiment 2.1.2: Dividing child painting a picture into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦child painting a picture⟧.

**Changed — two fragments**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

---

#### Experiment 2.1.3: Dividing car being washed by hand into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦car being washed by hand⟧.

**Changed — two fragments**
> This entry is about the ⟦car⟧ ⟦being washed by hand⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

### 2.2) Changing fragment boundaries without changing the atomic subject

#### Experiment 2.2.1: Dog activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `dog` and the activity. The changed masks add only the adjacent determiner, preposition, or terminal punctuation. Dog sleeping indoors is the matched atomic-subject change for dog playing fetch, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Dog playing fetch**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.
>
> This entry is about ⟦the dog⟧ ⟦playing fetch⟧.
>
> This entry is ⟦about the dog⟧ ⟦playing fetch⟧.
>
> This entry is ⟦about the dog⟧ ⟦playing fetch.⟧

**Dog sleeping indoors**
> This entry is about the ⟦dog⟧ ⟦sleeping indoors⟧.
>
> This entry is about ⟦the dog⟧ ⟦sleeping indoors⟧.
>
> This entry is ⟦about the dog⟧ ⟦sleeping indoors⟧.
>
> This entry is ⟦about the dog⟧ ⟦sleeping indoors.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.988242–0.998627`; changed-subject cosines were `0.224933–0.281705`. The smallest margin was `+0.711649`.

---

#### Experiment 2.2.2: Child activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `child` and the activity. The changed masks add only the adjacent determiner, preposition, or terminal punctuation. Child reading a book is the matched atomic-subject change for child painting a picture, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Child painting a picture**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.
>
> This entry is about ⟦the child⟧ ⟦painting a picture⟧.
>
> This entry is ⟦about the child⟧ ⟦painting a picture⟧.
>
> This entry is ⟦about the child⟧ ⟦painting a picture.⟧

**Child reading a book**
> This entry is about the ⟦child⟧ ⟦reading a book⟧.
>
> This entry is about ⟦the child⟧ ⟦reading a book⟧.
>
> This entry is ⟦about the child⟧ ⟦reading a book⟧.
>
> This entry is ⟦about the child⟧ ⟦reading a book.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.991441–0.999379`; changed-subject cosines were `0.441327–0.468807`. The smallest margin was `+0.529465`.

---

#### Experiment 2.2.3: Car activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `car` and the activity. The changed masks add only the adjacent determiner, preposition, auxiliary verb, or terminal punctuation. Car repair is the matched atomic-subject change for washing a car by hand, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Car being washed by hand**
> This entry is about the ⟦car⟧ being ⟦washed by hand⟧.
>
> This entry is about ⟦the car⟧ being ⟦washed by hand⟧.
>
> This entry is ⟦about the car⟧ ⟦being washed by hand⟧.
>
> This entry is ⟦about the car⟧ ⟦being washed by hand.⟧

**Car being repaired in a garage**
> This entry is about the ⟦car⟧ being ⟦repaired in a garage⟧.
>
> This entry is about ⟦the car⟧ being ⟦repaired in a garage⟧.
>
> This entry is ⟦about the car⟧ ⟦being repaired in a garage⟧.
>
> This entry is ⟦about the car⟧ ⟦being repaired in a garage.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.991952–0.999328`; changed-subject cosines were `0.368443–0.428111`. The smallest margin was `+0.571172`.

### 2.3) Changing fragment wording and atomic subject

#### Experiment 2.3.1: Dog playing fetch

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves dog playing fetch or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.

**First fragment — same subject**
> This entry is about the ⟦canine⟧ ⟦playing fetch⟧.

**First fragment — changed subject**
> This entry is about the ⟦child⟧ ⟦playing fetch⟧.

**Second fragment — same subject**
> This entry is about the ⟦dog⟧ ⟦retrieving a thrown ball⟧.

**Second fragment — changed subject**
> This entry is about the ⟦dog⟧ ⟦sleeping indoors⟧.

**Both fragments — same subject**
> This entry is about the ⟦canine⟧ ⟦retrieving a thrown ball⟧.

**Both fragments — changed subject**
> This entry is about the ⟦child⟧ ⟦sleeping indoors⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.983086` | `0.774015` | `+0.209072` |
| Second fragment | `0.761176` | `0.211456` | `+0.549720` |
| Both fragments | `0.752066` | `0.004272` | `+0.747794` |

**Result:** All three comparisons passed.

---

#### Experiment 2.3.2: Child painting a picture

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves child painting a picture or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.

**First fragment — same subject**
> This entry is about the ⟦kid⟧ ⟦painting a picture⟧.

**First fragment — changed subject**
> This entry is about the ⟦robot⟧ ⟦painting a picture⟧.

**Second fragment — same subject**
> This entry is about the ⟦child⟧ ⟦making a painting⟧.

**Second fragment — changed subject**
> This entry is about the ⟦child⟧ ⟦reading a book⟧.

**Both fragments — same subject**
> This entry is about the ⟦kid⟧ ⟦making a painting⟧.

**Both fragments — changed subject**
> This entry is about the ⟦robot⟧ ⟦reading a book⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.990198` | `0.600571` | `+0.389627` |
| Second fragment | `0.960052` | `0.439388` | `+0.520664` |
| Both fragments | `0.951676` | `0.117733` | `+0.833943` |

**Result:** All three comparisons passed.

---

#### Experiment 2.3.3: Car being washed by hand

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves a car being washed by hand or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦car⟧ being ⟦washed by hand⟧.

**First fragment — same subject**
> This entry is about the ⟦automobile⟧ being ⟦washed by hand⟧.

**First fragment — changed subject**
> This entry is about the ⟦bicycle⟧ being ⟦washed by hand⟧.

**Second fragment — same subject**
> This entry is about the ⟦car⟧ being ⟦cleaned manually⟧.

**Second fragment — changed subject**
> This entry is about the ⟦car⟧ being ⟦repaired in a garage⟧.

**Both fragments — same subject**
> This entry is about the ⟦automobile⟧ being ⟦cleaned manually⟧.

**Both fragments — changed subject**
> This entry is about the ⟦bicycle⟧ being ⟦repaired in a garage⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.997523` | `0.892023` | `+0.105500` |
| Second fragment | `0.883891` | `0.361299` | `+0.522592` |
| Both fragments | `0.887655` | `0.316613` | `+0.571042` |

**Result:** All three comparisons passed. The first-fragment comparison was the weakest wording result, but it still favored the unchanged atomic subject by `+0.105500`.

### 2.4) Adding redundant or unrelated meaning to the mask

#### Experiment 2.4.1: Redundant dog-fetch meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for dog playing fetch. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant dog-fetch fragment will affect the vector less than adding the unrelated child-painting fragment.

**Control**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described a canine retrieving a thrown ball. A child painted a picture nearby.

**Added redundant meaning**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described ⟦a canine retrieving a thrown ball⟧. A child painted a picture nearby.

**Added unrelated meaning**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described a canine retrieving a thrown ball. ⟦A child painted a picture⟧ nearby.

**Result:** Control-to-redundant cosine was `0.892011`; control-to-unrelated cosine was `0.330721`. The hypothesis passed by `+0.561290`.

---

#### Experiment 2.4.2: Redundant child-painting meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for a child painting a picture. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant child-painting fragment will affect the vector less than adding the unrelated dog-sleeping fragment.

**Control**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described a kid making a painting. A dog slept indoors nearby.

**Added redundant meaning**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described ⟦a kid making a painting⟧. A dog slept indoors nearby.

**Added unrelated meaning**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described a kid making a painting. ⟦A dog slept indoors⟧ nearby.

**Result:** Control-to-redundant cosine was `0.967705`; control-to-unrelated cosine was `0.445399`. The hypothesis passed by `+0.522306`.

---

#### Experiment 2.4.3: Redundant hand-washed-car meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for a car being washed by hand. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant hand-washed-car fragment will affect the vector less than adding the unrelated bicycle-repair fragment.

**Control**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described an automobile being cleaned manually. A bicycle needed a new tire nearby.

**Added redundant meaning**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described ⟦an automobile being cleaned manually⟧. A bicycle needed a new tire nearby.

**Added unrelated meaning**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described an automobile being cleaned manually. ⟦A bicycle needed a new tire⟧ nearby.

**Result:** Control-to-redundant cosine was `0.967867`; control-to-unrelated cosine was `0.623034`. The hypothesis passed by `+0.344833`.

### 2.5) Changing only text outside the mask

#### Experiment 2.5.1: Dog activities under different surrounding text

**Description:** The mask remains exactly `dog` plus the activity while the neutral text outside the mask changes. Dog playing fetch and dog sleeping indoors provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Dog playing fetch**
> The first note about the ⟦dog⟧ ⟦playing fetch⟧ was filed yesterday.
>
> An archived memo about the ⟦dog⟧ ⟦playing fetch⟧ was reviewed today.
>
> This short report about the ⟦dog⟧ ⟦playing fetch⟧ was copied twice.

**Dog sleeping indoors**
> The first note about the ⟦dog⟧ ⟦sleeping indoors⟧ was filed yesterday.
>
> An archived memo about the ⟦dog⟧ ⟦sleeping indoors⟧ was reviewed today.
>
> This short report about the ⟦dog⟧ ⟦sleeping indoors⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.995244–0.998576`; changed-subject cosines were `0.250671–0.285189`. The smallest margin was `+0.712164`.

---

#### Experiment 2.5.2: Child activities under different surrounding text

**Description:** The mask remains exactly `child` plus the activity while the neutral text outside the mask changes. Painting a picture and reading a book provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Child painting a picture**
> The first note about the ⟦child⟧ ⟦painting a picture⟧ was filed yesterday.
>
> An archived memo about the ⟦child⟧ ⟦painting a picture⟧ was reviewed today.
>
> This short report about the ⟦child⟧ ⟦painting a picture⟧ was copied twice.

**Child reading a book**
> The first note about the ⟦child⟧ ⟦reading a book⟧ was filed yesterday.
>
> An archived memo about the ⟦child⟧ ⟦reading a book⟧ was reviewed today.
>
> This short report about the ⟦child⟧ ⟦reading a book⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.992030–0.997193`; changed-subject cosines were `0.375291–0.414937`. The smallest margin was `+0.581214`.

---

#### Experiment 2.5.3: Car activities under different surrounding text

**Description:** The mask remains exactly `car` plus the activity while the neutral text outside the mask changes. Washing a car by hand and repairing it in a garage provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Car being washed by hand**
> The first note about the ⟦car⟧ being ⟦washed by hand⟧ was filed yesterday.
>
> An archived memo about the ⟦car⟧ being ⟦washed by hand⟧ was reviewed today.
>
> This short report about the ⟦car⟧ being ⟦washed by hand⟧ was copied twice.

**Car being repaired in a garage**
> The first note about the ⟦car⟧ being ⟦repaired in a garage⟧ was filed yesterday.
>
> An archived memo about the ⟦car⟧ being ⟦repaired in a garage⟧ was reviewed today.
>
> This short report about the ⟦car⟧ being ⟦repaired in a garage⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.993667–0.997870`; changed-subject cosines were `0.386410–0.404772`. The smallest margin was `+0.589299`.

### Combined result

| Requirement-focused test | Result |
|---|---:|
| Same selected words divided into one or two fragments | 3/3 exact |
| Changed fragment boundaries, same atomic subject | 72/72 |
| Paraphrased fragments versus subject-changing fragments | 9/9 |
| Added redundant meaning versus unrelated meaning | 3/3 |
| Changed text outside the mask versus changed atomic subject | 36/36 |

All five tests passed every predeclared comparison.

> For these controlled synthetic examples, multi-fragment masks preserved the intended atomic subject under changes to fragment count, boundaries, wording, redundancy, and surrounding text, while remaining sensitive to changes in the atomic subject.

This establishes the required behavior only for these common synthetic examples. It does not establish the same behavior for real Nostr language, automatically generated masks, fine segmentation, or hierarchy construction.

The frozen inputs, every unrounded comparison, and the complete cosine matrix are in `sse_multivector/mask-fidelity-multifragment-requirements-v1/`.

## Real-note holdout mask experiment

### Question

Do manually selected atomic-subject masks preserve the expected local semantic relationship in previously unused real Nostr notes?

### Setup

The experiment used 12 real notes in four comparisons. Each comparison contained:

- A and B: masks expected to represent the same narrow subject.
- C: a related mask expected to represent a different subject.

The notes, masks, and expected result were approved before any of their SSE vectors were generated. None of the 12 note IDs appeared in the frozen 1,000-note sample or the prior SSE experiment records checked during selection.

Only these 12 vectors were encoded. A comparison passed when:

`cosine(A, B) > cosine(A, C)` and `cosine(A, B) > cosine(B, C)`

All vectors used the frozen Sentence-T5-base SSE checkpoint with SHA-256 `ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d`.

### 1) Camera bird feeders

#### Description

A and B concern bird feeders with cameras. C concerns wild eagles returning to England.

#### Hypothesis

The A–B cosine will be higher than both control cosines.

#### A

> The Smart Bird Feeders Everyone’s Talking About (and Actually Buying) (2026)
>
> These ⟦bird feeders come with cameras and connected apps⟧ to let you see and learn about the birds in your neighborhood.
>
> https://www.wired.com/story/best-smart-bird-feeders/

#### B

> My wife got a ⟦camera bird feeder⟧, and I have to say, I do not mind getting these notifications.
>
> https://mograph.social/system/media_attachments/files/116/127/500/431/041/174/original/b26c7f899642eeaf.png

#### C

> ⟦Golden eagles are returning to English skies for the first time in centuries.⟧ Sometimes things that seemed gone for good find their way back. If you're in a season that feels like everything has disappeared — your energy, your hope, your sense of who you are — you don't have to rush the return. Even the eagles needed time, and the right winds. The sky is still there. ♡

#### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.568817` |
| A–C | `-0.058361` |
| B–C | `0.171170` |

The hypothesis passed. A–B exceeded both controls by at least `0.397646`.

### 2) Moving from Windows to Linux

#### Description

A and B concern adopting Linux instead of Windows. C concerns running Windows applications on Linux while retaining the Windows software.

This was deliberately a hard comparison. Before encoding, we agreed that a pass would be strong evidence, but a failure would not be definitive because the frozen model might not know this technical distinction well enough.

#### Hypothesis

The A–B cosine will be higher than both control cosines.

#### A

> ⟦Windows 12 could be the tipping point that finally pushes you to Linux⟧ - here's why
> https://www.zdnet.com/article/windows-12-rumors-linux-migration/

#### B

> Hey nostr:nprofile1qyvhwumn8ghj7un9d3shjtnyd9mxjmn99emxjer9duhsqgyt29lcuuq8ql0afk8fwn6k6xphzxtc6u3sxp3sxz3kqjge86n5ty8j9k4f since you seem up on this stuff I'm interested in potentially ⟦getting a home Linux mini-PC⟧... do they make those pre-installed with Linux or does it make more sense to just get one off the shelf and ⟦scoop out the Windows slop⟧ myself?

#### C

> ⟦How to run Windows apps on Linux with Wine⟧ - it's easy
> https://www.zdnet.com/article/how-to-run-windows-apps-on-linux-with-wine/

#### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.665970` |
| A–C | `0.580301` |
| B–C | `0.701669` |

The hypothesis failed. A was closer to B than to C, but B was closer to C than to A by `0.035699`.

This comparison does not support SSE distinguishing Linux adoption from Windows-software compatibility. It does not identify whether the cause was mask behavior, limited model knowledge, or another property of the frozen encoder.

### 3) Explicit air-fryer masks

#### Description

A and B explicitly mask `air fryer`. C masks `Olive Oil Dispenser`, while unmasked text later in C mentions an air-fryer toaster oven.

This was an easy control. A failure would show a fundamental context-isolation problem. A pass provides only weak evidence by itself.

#### Hypothesis

The A–B cosine will be higher than both control cosines.

#### A

> ⟦air fryer⟧ kebab sandwiches have been proven a success

#### B

> Cooking Meatloaf In The ⟦Air Fryer⟧ Will Give You The Best Texture Yet https://www.diningandcooking.com/2534044/cooking-meatloaf-in-the-air-fryer-will-give-you-the-best-texture-yet/ #AirFryer #ClassicMeatloaf #Cooking #DavidMiller #MeatloafRecipe #PerWitchel #TastingTable #VioletWitchel
>
> https://media.vive.im/media_attachments/files/116/148/355/361/148/257/original/e28f5e646d3fa45a.jpeg

#### C

> This ⟦Olive Oil Dispenser⟧ Is the ‘Rare Perfect Product’
>
> One of the pantry ingredients I reach for most is olive oil. I use it to roast chicken or make crisp French fries in my air fryer toaster oven, crank out batches of popcorn in my stovetop popcorn maker, and fry slices of sweet peppers in my stainless steel skillet…
> #dining #cooking #diet #food #MediterraneanOliveOil #OliveOil #Mediterranean #Olive
> https://www.diningandcooking.com/2323894/this-olive-oil-dispenser-is-the-rare-perfect-product/
>
> https://media.vive.im/media_attachments/files/115/344/843/075/050/924/original/81e3277f5dc4da86.jpg

#### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.882650` |
| A–C | `0.196801` |
| B–C | `0.103369` |

The hypothesis passed. A–B exceeded both controls by at least `0.685849`.

### 4) Off-grid mesh networking

#### Description

A and B concern off-grid mesh networking. B also contains unmasked solar language. C masks a solar-power headline without mesh networking.

#### Hypothesis

The A–B cosine will be higher than both control cosines.

#### A

> I love what this guy @ DataSlayer is doing with Reticulum—an open-source protocol that could allow anyone to ⟦build networks without relying on traditional internet infrastructure⟧.
>
> “In this video, I start with a simple setup inside my house and begin pushing the limits—testing communication across rooms, neighborhoods, and beyond ⟦using WiFi HaLow and mesh networking⟧. The goal is simple: see if it’s possible to send real messages across distance without depending on ISPs, centralized servers, or the internet as we know it.”
>
> https://youtu.be/6ibr7gm8uVA?si=ph7K75ZnjRr7BTAH
>
> #reticulum #meshnetworking #technology #communication

#### B

> Solar powered ⟦mesh networks⟧ are the new atomic reactors, powering communities away from corporate surveillance. #MeshTheResistance
>
> ⟦Decentralized off-grid computing⟧ is key to protecting privacy and fostering autonomy. Imagine a world where no single corporation controls your data.
>
> MeshTheResistance OffGridPower SolarNetworks

#### C

> ⟦US Builders Are Still Pushing The Solar Power Envelope⟧
>
> US Builders Are Still Pushing The Solar Power Envelope
>
> Sector: Real Infrastructure | Confidence: 98%
> Source: https://www.reddit.com/r/energy/comments/1rm69aa/us_builders_are_still_pushing_the_solar_power/
>
> #FIRE #Circle #infrastructure

#### Result

| Pair | Cosine |
|---|---:|
| A–B | `0.791757` |
| A–C | `0.094671` |
| B–C | `0.256172` |

The hypothesis passed. A–B exceeded both controls by at least `0.535586`.

### Findings

Three of the four comparisons passed their predeclared ordering test.

The passing comparisons show that SSE can expose the expected narrow semantic relationship in some previously unused real notes, including notes with different wording, multiple mask fragments, and potentially distracting text outside the mask.

The failed Windows/Linux comparison shows that this behavior is not yet reliable for nearby subjects. Its result cannot distinguish a general SSE limitation from insufficient technical knowledge in the frozen model.

This experiment therefore supports continuing to test SSE mask fidelity, but does not establish that the necessary semantic structure is reliable across real Nostr content.
