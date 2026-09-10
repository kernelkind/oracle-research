# Oracle MVP Content Discovery

## Current Status

Oracle MVP v1 is frozen at the local `oracle-mvp-v1` Git tag. Its exact
whole-note Oracle and private-personalizer experiment missed its approved
quality criterion. Git preserves that implementation and its reports.

The approved direction is now a separate, user-directed content-discovery
system. It does not try to infer which subject a person wants next. It builds a
public subject hierarchy, lets the person narrow through explicit choices, and
then shows notes from the selected subject. Subjects and discovered groups may
have different breadths; a uniformly fine layer is not a prerequisite for
hierarchy investigation.

The current [100-note real-data experiment](../../sse_multivector/real-note-fine-segmentation-v1/README.md)
uses this preparation pipeline:

```text
public note
  -> ASv6.23 subjects
  -> MPv3.5 source masks
  -> reviewed subjects and masks
  -> one SSE vector per mask
```

Both prompt packages are frozen for this experiment. ASv6.23 explicitly allows
broad, narrow, nested, and overlapping subjects. The older takeaway/prominence
orchestration remains implemented but is not this experiment's preparation
path. The final grouping contract and algorithm, hierarchy algorithm, and
production-scale extractor remain open.

The current hierarchy investigation compares the saved
[HDBv2/HDBv3 trees and an optional note-navigation view](../../sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/README.md),
without generated titles. The comparison derives choices from HDBv3's complete
merge history, omits one-note groups, and collapses transitions returning the
same notes. The original viewer and saved clustering results remain unchanged.
Useful groupings do not automatically validate their parent placements; neither
HDBv3 nor this simplification is selected as the final method.
The [merge-rule inspection package](../../sse_multivector/merge-rule-exploration-v1/inspection.md)
also includes an optional five-note display minimum for saved M06, alongside
the unchanged default view. It changes available group choices, not clustering
or note memberships; the minimum is still an experiment.
The separate [manual coffee example](../../sse_multivector/merge-rule-exploration-v1/inspection.md#manual-coffee-example)
lets the user inspect a small proposed hierarchy constructed from original
notes, not from an algorithm's nodes. The user accepted this example as a valid
arrangement, not the uniquely correct one. The
[Coffee preparation comparison](../../sse_multivector/merge-rule-exploration-v1/inspection.md#coffee-preparation-compared-with-m06)
now shows its five original notes beside relevant saved M06 branches. M06
preserves useful two-note preparation pairs, hidden by the five-note display
minimum, but its smallest group covering the five notes contains 19 notes.
Morning coffee has not been compared; no algorithm is approved by this judgment.
The earlier [controlled-run results](experiments/fine-segmentation/controlled-run-v1-results.md)
and their frozen protocols remain unchanged evidence, not a pending work order
that must be repeated before this investigation.

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
- One note may contribute to several subjects at different breadths.
- A hierarchy choice must narrow the content set relative to the complete path
  above it; an independent label that can be interpreted many ways is not a
  useful refinement.
- No indispensable external provider may control which public content can be
  discovered.
- Production constraints are deferred until the scientific assumptions work,
  but the repository-wide `$500` paid-compute ceiling remains binding.

## Investigation Boundaries

Keep source extraction, grouping, hierarchy placement, and navigation judgments
separate. An algorithm may produce both groups and a candidate hierarchy, but
coherent groups alone do not establish meaningful narrowing paths. A discovered
group is not presumed to be a maximally narrow or terminal subject.

Each experiment freezes its actual inputs and configuration. Preserve source
masks, memberships, and prior judgments when comparing outcomes. Read-only
inspection of candidate hierarchies may inform the next experiment; it does
not freeze an algorithm. Tree versus overlapping parent paths, grouping versus
separate hierarchy construction, and final labels remain open.

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
