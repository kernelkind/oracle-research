# Hierarchy implementation and research

For the project goals, walkthrough and results, start with the
[project README](../../README.md). The [generation guide](../generate-hierarchy.md)
covers the complete supported workflow.

## Current implementation

- [HiGen V5.3](hierarchy-generation-v5.md): recursive hierarchy construction,
  membership additions, stopping rules and native commands.
- [Subject navigation](design/semantic-region-navigation.md): the intended
  browsing behavior and the boundary between public hierarchies and local state.
- [Toy snapshot protocol](design/hierarchy-serving-protocol-decisions.md):
  experimental events for local or private Notedeck testing.
- [Official hierarchy runs](hierarchy-runs.md): recorded inputs, outcomes,
  source revisions and coverage, including failed and superseded runs.
- [Hierarchy parameters and review commands](hierarchy-review-commands.md):
  the settings used by each recorded run. Original local paths describe the
  research environment; see the [reproduction guide](../experiments/reproduce.md)
  for the published data workflow.
- [Hierarchy advancement performance](hierarchy-advancement-performance.md):
  measured changes to evidence reads, clustering and concurrency.

The [experiment index](../experiments/README.md) connects the retained studies to
their inputs and final results. Earlier algorithms and prompt versions are
research evidence; they are not defaults for a new run.

## Earlier hierarchy and representation experiments

- [HiGen V3–V3.2](hierarchy-generation-v3.md) and
  [V4–V4.4](hierarchy-generation-v4.md): construction rules and recorded trials
  for the versions still needed to interpret saved runs.
- [SSE multi-vector isolation and mask-fidelity evidence](experiments/sse-multivector-isolation.md):
  supplied-mask controls, real-note comparisons and observed representation
  failures. These experiments do not validate subject extraction or hierarchy
  quality.
- [Controlled fine-segmentation results](experiments/fine-segmentation/controlled-run-v1-results.md)
  and [frozen protocols](experiments/fine-segmentation/README.md).
- [Communicated-meaning extraction](experiments/sse-communicated-meaning-extraction.md),
  [hard-partition pilot](experiments/sse-fine-region-partition-pilot.md) and
  [complete segment review](experiments/sse-fine-region-complete-merge-review.md):
  the earlier TEv4.1 representation and its limitations.
- [HR09 investigation](hr09-investigation.md): case-level observations from an earlier
  construction run.

AS versions before ASv6.100 and their derived results are historical evidence,
not current pipeline inputs or validation. Raw source posts are unaffected.

## Research background

- [Fine-segmentation vector-space requirements](research/fine-segmentation-vector-space-requirements.md)
- [Corpus-induced regions and labeling](research/semantic-region-discovery-and-labeling.md)
- [Hierarchy methods for semantic groups](research/hierarchical-grouping-of-fine-semantic-segments.md)
- [Hierarchy construction from SSE vectors](research/sse-vector-note-hierarchy-candidates.md)
- [Direct note-to-mask extraction](research/direct-note-to-mask-extractor.md)
- [Nostr semantic recommendation prior art](research/nostr-semantic-recommendation-prior-art.md)
- [Existing Nostr recommendation systems](research/existing-nostr-recommendation-systems.md)
- [General semantic recommendation systems](research/general-semantic-recommendation-systems.md)
- [Leading content recommendation systems](research/leading-content-recommendation-systems.md)
- [Nostr relay storage](research/nostr-relay-storage-research.md)

These literature surveys describe the evidence available when written. Their
alternative methods and proposed comparisons are not the current generation
workflow. Numerical epsilon and section-replacement studies are linked from the
[HiGen V5 record](hierarchy-generation-v5.md) and the experiment index.
