# SSE Multi-Vector Isolation Experiment

## Status

The neutral 32-note input is frozen in
[`sse-multivector-note-set-v2.json`](./sse-multivector-note-set-v2.json). It
contains 32 real Nostr notes from 32 authors and presupposes no subjects.

Subject enumeration and independent mask generation have run over every raw
note using the approved minimal prompts. Each note used a fresh subject call,
and every resulting subject used a separate fresh mask call. Their audited,
source-bound output is
[`subject-mask-proposal-v3.json`](../../../sse_multivector/subject-mask-proposal-v3.json):

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
Its deterministic replay verified every source binding and generated file.
Local artifacts are under
`target/sse-multivector-diagnostic-v1/analysis/`.

The upstream release provides neither a checkpoint checksum nor an explicit
license. This repository does not redistribute the checkpoint. The recorded
hash binds this run to the file obtained from the authors' official Drive ID,
name, and advertised byte size; it does not independently authenticate the
publisher.

## Current Question

Given audited subjects and their exact supporting text, can SSE produce
a useful separate vector for each subject expressed within a note?

This requires more than broad topical similarity. A subject vector must retain
the meaning of its selected text while excluding the note's other meanings.

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

The remaining ambiguity is specific: how much of each vector represents the
masked subject, and how much represents surface wording or surrounding note
context? A later focused comparison may test that ambiguity. This run alone
does not justify clustering, hierarchy construction, or corpus-scale
processing.

## Follow-up

The separate
[communicated-meaning triplet](./sse-communicated-meaning-triplet.md) records a
small follow-up using semantic takeaways rather than narrow subject labels. It
does not modify or replace this baseline.

The later
[full communicated-meaning diagnostic](./sse-communicated-meaning-full.md)
applies the locked takeaway representation to all 32 frozen notes and compares
the resulting geometry with this preserved baseline.
