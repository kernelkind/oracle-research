# AVv1 — saved-vector ancestor-voting diagnostic

The user approved testing ancestor-based scoring on saved subject vectors and
SP relationships, hiding a small selection of known relationships and separately
inspecting the missing Food relationships. This is a diagnostic, not adoption of
a placement algorithm. It makes no model calls, new embeddings, merges, or
placements, and does not alter the original hierarchy or browser exports.

The scoring and holdout rules are recorded separately as HD19 and HD20 in the
[SP-based hierarchy rule register](../docs/planning/release-decisions.md#sp-based-hierarchy-rules).
AVv1 is tested but not adopted; its exclusions are evaluation choices, not
instructions to remove subjects from the real hierarchy.

## Inputs and scoring

Reuse the six SOv1 posts, their saved standalone subject-text SSE vectors, and
the 116 SMv1 nodes with their mapped SP relationships. Original mask/source
references remain in the output. Mask vectors are **not** used in these scores.

For each queried node:

1. In a temporary scoring graph, exclude the query and all its descendants.
   Also exclude other nodes containing those exact subject strings, and their
   descendants; repeat to closure. This prevents repeated copies of a held-out
   subject or its branch from trivially revealing its saved parent. No source
   data is removed. The same exclusion applies to the missing-link cases.
2. Find the nearest `k` distinct subject strings among remaining nodes, using
   subject-to-subject cosine. A multi-name SMv1 node uses the maximum over its
   constituent subject comparisons, not a blended vector. Keep positive scores
   and all numerical ties at the kth score; no semantic cutoff is fitted.
3. Each retrieved subject string votes to its remaining **strict ancestors**,
   not to itself. Its contribution is `cosine * decay ** (hops - 1)`.
   Count an exact string once per candidate ancestor, using its shortest path
   across all remaining occurrences. These occurrences remain separate nodes;
   this voting deduplication does not authorize semantic merging.
4. Sum those contributions separately for each candidate. Compare ranks with
   direct subject-to-subject cosine over the same remaining candidate nodes.
   Zero support has no voting rank. Ties share rank. Save every contributing
   subject, its originating nodes, path length, cosine, and weighted vote.

`k = 3, 5, 10` and `decay = 0.5, 1.0` are fixed exploratory settings. They are
not optimized on the answers. Report all six combinations, not a selected
winner. Path length is a provisional weighting assumption, **not** a claim that
local SP depths measure global generality. No score becomes a placement.

The voting idea is adapted from [Yamada et al. (2009)](https://aclanthology.org/D09-1097/).
The original paper uses distributional noun-context similarity, not SSE.
[Vedula et al. (2018)](https://researchrepository.ucd.ie/rest/bitstreams/40766/retrieve)
also propagates neighbor cosine scores to ancestors, but its complete trained
ranking system is not used here. Neither paper validates this adaptation on
SP topic/subtopic relationships.

## Evaluation boundaries

The eight illustrative hidden-link queries are Bread, Sourdough bread, Soda
bread, Rosemary, Music in coffee shops, Laptops, Irish baking, and High-altitude
baking website. Their targets are their saved direct parents, not newly labeled
ground truth. All incoming links are unavailable when scoring the query.
Food preparation, Food ingredients, and Food appreciation are separate
missing-link inspections and are not counted as hidden-link recovery cases.

The exclusion is deliberately stricter than hiding one arrow. Sometimes it
removes a parent's only remaining child, leaving no way for that parent to
receive votes. Report those cases; do not remove them from the denominator.
This tests evidence independent of the held-out branch, not the full value of
SP links or equivalent-subject matching. Other valid parents may rank above
the saved parent, so exact-parent recovery is not semantic placement accuracy.
Six familiar posts do not establish generalization or million-post scalability.
Missing edges remain unknown, and multiple candidate parents remain visible.

## Reproduce

Output is isolated under ignored `target/`. An existing output directory is
never overwritten. Source/vector hashes, original subjects and edges, scoring
settings, case references, and implementation hash accompany the results.
The runner checks source hashes before and after, and repeats scoring for
determinism. `results.json` contains evidence; `summary.json` contains computed
recovery counts. Agent interpretation, if saved, belongs in a separate ignored
assessment, not in the reusable method definition or the planning decisions.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m sse_multivector.ancestor_voting_probe \
  --probe target/subject-order-v1/run \
  --matching target/subject-matching-v1/run \
  --output target/ancestor-voting-v1/replay \
  --holdout N015:3 \
  --holdout N015:3.1 \
  --holdout N072:2.1 \
  --holdout N037:2.2 \
  --holdout N038:1.2 \
  --holdout N065:3.1 \
  --holdout N072:1.1 \
  --holdout N072:7.1 \
  --inspect N015:2 \
  --inspect N037:2 \
  --inspect N037:3
```

Tests exercise the actual scorer and saved-vector CLI, including multiple
parents, repeated wording, hidden-branch leakage, no-support cases, ties,
input corruption, and overwrite prevention:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 -m unittest \
  sse_multivector.test_ancestor_voting_probe \
  sse_multivector.test_subject_matching_probe \
  sse_multivector.test_ancestor_cosine_probe
```
