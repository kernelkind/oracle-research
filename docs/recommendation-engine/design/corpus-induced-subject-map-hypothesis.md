# Corpus-Induced Subject Map Hypothesis

## Status

Working technical hypothesis. This document records the project's current
prescription and the reasoning behind it. It is not a literature finding, an
approved architecture, or an approved experiment.

The neutral evidence record is
[Corpus-Induced Semantic Region Discovery](../research/semantic-region-discovery-and-labeling.md).
The citations below establish properties of individual methods. They do not
establish that the proposed composition will work for Nostr.

## Goal

Derive a public semantic structure from the complete public Nostr note corpus
so a person can deliberately move among understandable subjects instead of
being trapped in repeatedly expanded note neighborhoods.

The structure must:

- derive subjects from the corpus rather than a predefined taxonomy;
- keep every eligible note addressable;
- let one note belong to several subjects with different strengths;
- support broad and narrow views;
- preserve uncertainty instead of forcing a false narrow subject;
- generate descriptions only after the semantic structure exists;
- remain independent of private ratings.

Private evidence may order or select among public subjects locally. It does not
define those subjects.

## Current Hypothesis

The simplest architecture worth testing is a corpus-trained sparse semantic
representation over purpose-selected whole-note embeddings.

This proposal starts from the raw public notes. The existing Oracle matrix is
one optional representation candidate, not a constraint. It is reused only if
it proves suitable for subject recovery.

### Existing Oracle artifact

The existing matrix contains 3,530,455 normalized, 3,584-dimensional FP32 note
vectors and occupies about 47.1 GiB. GTE-Qwen2 was selected for semantic
retrieval; the project did not validate its geometry for topic decomposition or
hierarchy construction.

These facts affect the cost of evaluating that matrix. They do not make it the
input to this hypothesis.

### 1. Select a representation for subject recovery

Choose or train a text representation by testing whether it preserves the
subjects people perceive in Nostr notes. Semantic-search performance alone
does not answer this question.

The test material must include:

- notes with one clear subject;
- notes with several subjects;
- short and ambiguous notes;
- code, URLs, jargon, and informal language;
- rare meanings and genuine outliers.

### 2. Learn sparse semantic components from the corpus

Train a sparse autoencoder over the chosen note embeddings.

[SAE-TM](https://arxiv.org/abs/2511.16309) provides the relevant mechanism:
the model learns reusable, unnamed topic atoms from document embeddings, and
each document can activate several atoms. Nothing supplies the subjects in
advance.

[BatchTopK](https://arxiv.org/abs/2412.06410) is the current sparsity
hypothesis because it allows different notes to activate different numbers of
components while controlling average sparsity.

For example, a note about writing Rust software for a Bitcoin wallet could
activate separate corpus-learned components corresponding to Rust, software
development, and Bitcoin, with different strengths. Those names would be
assigned only after examining what the components actually represent.

A learned component is not automatically a subject. It may instead represent
language, style, syntax, format, author patterns, or an embedding artifact. Only
components whose note memberships match human semantic interpretation become
subject candidates.

### 3. Preserve sparse membership and residual uncertainty

The public base representation would contain:

- sparse note-to-component activation weights;
- component-to-note inverted membership;
- a separately calibrated semantic-membership confidence, if one can be
  validated;
- representative notes and grounded phrases used to interpret each component;
- immutable corpus, encoder, and model version identifiers.

Every note remains addressable regardless of reconstruction error or assignment
confidence. Reconstruction error is not semantic uncertainty: a note can
reconstruct well from misleading components, or reconstruct poorly because of
model capacity. It may be retained as an audit metric, but it does not belong in
the mapping unless later evidence gives it a semantic use. A boundary,
coarse-only, residual, or outlier mapping requires semantic evidence rather
than an error threshold chosen for convenience.

### 4. Derive broader regions only after base membership works

If the learned components match human interpretation, broader and narrower
regions can be derived afterward.

The hierarchy hypothesis combines:

- semantic relatedness between components;
- their note-level co-activation patterns;
- asymmetric containment, where a narrower component appears largely within a
  broader semantic scope.

Co-activation establishes association, not containment. Sibling subjects may
co-activate frequently. It can propose relationships, but every parent-child
rule must separately demonstrate that the parent is semantically broader than
the child.

A subject may need several parents, so the result may be an overlapping graph
rather than a strict tree. [BoxTM](https://aclanthology.org/2024.tacl-1.77/)
supports asymmetric semantic containment as a broad-to-narrow model;
[Hierarchical Overlapping Clustering](https://proceedings.mlr.press/v267/pan25a.html)
demonstrates a scalable overlapping structure. Neither paper proves this
combination for Nostr.

No hierarchy mechanism is selected until the underlying note-to-component
membership is validated.

### 5. Describe regions after discovery

Descriptions would be generated from:

- diverse representative notes;
- phrases grounded in those notes;
- contrasts with parent, sibling, and nearby nonmember regions.

The description is metadata for navigation. It does not determine membership.

## Principal Competing Hypothesis

A whole-note embedding may blend several meanings before the sparse model sees
them. Sparse decomposition cannot recover information the embedding discarded.

The competing representation keeps several contextual spans or semantic units
per note. [Contextual-Top2Vec](https://aclanthology.org/2024.findings-emnlp.790/)
shows that contextual token embeddings can support topic spans, hierarchical
topics, and phrase labels.

This representation is more expensive and complex:

- one note produces several public vectors;
- segmentation or contextual-unit construction becomes a new failure point;
- storage, indexing, and note-level aggregation increase.

That complexity is justified only if it recovers human-recognized subjects that
the whole-note sparse representation loses.

## Proposed Prerequisite System Comparison

Before constructing a full corpus map, compare:

1. a purpose-selected whole-note representation plus a sparse topic model; and
2. a grounded contextual span or multi-vector representation.

Both complete pipelines must emit the same observable contract: weighted
note-to-component memberships, component exemplars, and an explicit
unassigned or uncertain state. The comparison asks:

> Which complete pipeline more faithfully recovers the subjects people
> recognize in short and mixed Nostr notes?

The existing Oracle matrix may participate as one whole-note representation.
It does not define the comparison.

This comparison does not isolate representation as the sole causal variable:
the pipelines also differ in their component-discovery and aggregation
machinery. A winning pipeline selects a better system candidate; it does not
prove which internal part caused the difference. A causal claim would require a
later controlled ablation.

Judge the two candidates separately on:

1. whether every claimed subject is actually present in a note;
2. whether every important subject in a mixed note is recovered;
3. whether stronger memberships reflect the note's emphasis;
4. whether ambiguous and outlier notes retain honest uncertainty.

Hierarchy, labels, navigation, and recommendation quality are later claims.
They must not decide this representation comparison.

## Decision Rule

- If the whole-note sparse representation faithfully recovers mixed-note
  subjects, retain it because it removes the span pipeline and its cost.
- If it consistently blends or loses subjects that the grounded representation
  recovers, retain the grounded pipeline as the stronger system candidate. This
  result alone does not prove that multi-vector representation caused the gain.
- If neither representation produces faithful membership, do not build a
  hierarchy on top of either one.

No sample size, model, threshold, budget, or implementation is approved by this
document.

## Main Risks

- The selected encoder may preserve retrieval similarity but not separable
  subjects.
- Sparse components may capture language, style, syntax, format, author
  patterns, or embedding artifacts instead of subjects.
- Sparse components may be coherent globally yet be falsely assigned to
  individual notes.
- Generic components may activate broadly and obscure specific meanings.
- Co-activation may mistake associated sibling subjects for parent-child
  containment.
- A hierarchy built from symmetric similarity may confuse “related” with
  “broader than.”
- Generated labels may sound plausible while misdescribing boundary members.
- Rare meanings may be absorbed, mislabeled, or left with excessive residual
  uncertainty.
