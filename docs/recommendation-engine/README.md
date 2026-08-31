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
they do so reliably. The fine-segmentation output contract, selected algorithm,
hierarchy algorithm, and production-scale extractor remain open.

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

The next stages are intentionally dependency-ordered:

1. Fix and freeze the temporary TP, MP, and prominence generation boundary.
2. Evaluate one frozen fine-segmentation candidate with the frozen SSE boundary
   on the approved synthetic suite. Experiments 3 and 4 qualify that combined
   boundary because their text interventions are re-encoded through SSE before
   the candidate receives them.
3. If that evidence supports proceeding, test the same candidate on a
   hand-selected real-note collection from one niche subject area.
4. Only after useful fine subjects are demonstrated, compare and freeze a
   hierarchy-construction method.
5. Construct and label the hierarchy, then build the navigation TUI.

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
