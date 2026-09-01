# Oracle MVP Content Discovery

## Current Status

Oracle MVP v1 is frozen at the local `oracle-mvp-v1` Git tag. Its exact
whole-note Oracle and private-personalizer experiment missed its approved
quality criterion. Git preserves that implementation and its reports.

The approved direction is now a separate, user-directed content-discovery
system. It does not try to infer which subject a person wants next. It builds a
public subject hierarchy, lets the person narrow through explicit choices, and
then shows notes from the selected fine subject.

The current implemented preparation pipeline is:

```text
public note
  -> TP-generated takeaways
  -> MP-selected source masks
  -> PP prominence scores
  -> one SSE vector per mask
```

Those components are experimental. The downstream representation is intended
to describe atomic subjects, and the current prompts do not yet establish that
they do so reliably. Two fine-segmentation configurations are frozen for
controlled qualification: HDBSCAN* with `min_samples = 2`,
`min_cluster_size = 2`, and excess-of-mass selection, and SNN with
`neighbor_count = 5`, `minimum_shared_neighbor_count = 2`, and
`minimum_core_neighbor_count = 3`. They run the complete suite as separate
candidate instances over the same frozen inputs. The final fine-segmentation
contract and algorithm, hierarchy algorithm, and production-scale extractor
remain open.

The suite's exact semantic fixtures, scoring rules, and prerequisite graph were
approved on 2026-08-31. The user is its primary human semantic reviewer, with
an Experiment 2 limit of 100 unique cross-subject packets per candidate.
Technical identity and protocol-hash freezes remain incomplete, and the suite
has not run.

## Goal

Build a public, corpus-derived content-discovery hierarchy that helps a person
reach content about a subject they explicitly choose, including niche subjects
and notes from unknown authors.

The hierarchy is a discovery tool, not a replacement for the separate local
recommendation system. The v1-style recommender may still be useful later, but
it must not control this hierarchy or infer the person's current subject from
private behavior.

## Hard Constraints

- Shared computation may analyze only public Nostr data.
- The public hierarchy must not depend on private ratings, inferred
  preferences, or current intent.
- Subjects must emerge from the corpus rather than a predefined ontology.
- One note may contribute to several fine subjects.
- A hierarchy choice must narrow the content set relative to the complete path
  above it; an independent label that can be interpreted many ways is not a
  useful refinement.
- No indispensable external provider may control which public content can be
  discovered.
- Production constraints are deferred until the scientific assumptions work,
  but the repository-wide `$500` paid-compute ceiling remains binding.

## Work Order

The next fine-segmentation stages are intentionally dependency-ordered:

1. Technically freeze the shared SSE inputs, bind the approved fixtures and
   scoring rules by hash, freeze the orders and both complete candidate
   identities, then run the synthetic suite separately for HDBSCAN* and SNN.
   Experiments 3 and 4 qualify each SSE-plus-candidate combination because their
   text interventions are re-encoded through SSE before the candidate receives
   them. Semantic failures remain evidence and do not halt later local tests;
   an integrity failure blocks only the affected candidate input and dependent
   conclusions.
2. Present the two complete records side by side. The assistant may recommend
   an outcome; the user alone selects and final-freezes a candidate, requests a
   revision, or stops the approach.
3. If the user selects a candidate, test that exact identity on a hand-selected
   real-note collection from one niche subject area.
4. Only after useful fine subjects are demonstrated, compare and freeze a
   hierarchy-construction method.
5. Construct and label the hierarchy, then build the navigation TUI.

The temporary TP, MP, and prominence generation boundary remains separate
upstream work. It must be resolved before an end-to-end system can produce
atomic-subject inputs from arbitrary notes, but it is not a prerequisite for
this suite's hand-authored synthetic masks.

Do not scale the corpus or build a later stage to conceal an unresolved earlier
stage.

## Document Map

### Current sources

- [`../notes/MY-NOTES.md`](../notes/MY-NOTES.md)
- [`design/atomic-vector-subject-hierarchy.md`](design/atomic-vector-subject-hierarchy.md)
- [`design/semantic-region-navigation.md`](design/semantic-region-navigation.md)
- [`../notes/SSE-EXPERIMENTS.md`](../notes/SSE-EXPERIMENTS.md)
- [`research/fine-segmentation-vector-space-requirements.md`](research/fine-segmentation-vector-space-requirements.md)
- [`experiments/fine-segmentation/README.md`](experiments/fine-segmentation/README.md)
- [`research/hierarchical-grouping-of-fine-semantic-segments.md`](research/hierarchical-grouping-of-fine-semantic-segments.md)

### Supporting research

- [`research/direct-note-to-mask-extractor.md`](research/direct-note-to-mask-extractor.md)
- [`research/semantic-region-discovery-and-labeling.md`](research/semantic-region-discovery-and-labeling.md)
- [`research/leading-content-recommendation-systems.md`](research/leading-content-recommendation-systems.md)
- [`research/general-semantic-recommendation-systems.md`](research/general-semantic-recommendation-systems.md)
- [`research/existing-nostr-recommendation-systems.md`](research/existing-nostr-recommendation-systems.md)
- [`research/nostr-semantic-recommendation-prior-art.md`](research/nostr-semantic-recommendation-prior-art.md)
- [`research/nostr-relay-storage-research.md`](research/nostr-relay-storage-research.md)

### Operational guidance

- [`disk-io-pressure-control.md`](disk-io-pressure-control.md)
