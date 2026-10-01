# PCPv1: broader-parent candidate diagnostic

[PCPv1](PCPv1.md) nominates possible broader parents for one top-level hierarchy
node. It does not judge equivalence, authorize placements, or change the HG rules.
Its output is a possible input to a separately authorized BCPv4 comparison.
Status: tested in separate three-root and ten-root diagnostics; not frozen or adopted.

The shared experiment runner's `parent_candidates` adapter gathers the input
directly from saved SP entries, a saved hierarchy, and current saved judgments.
The selection file names those three sources and the query node IDs. Preparation
hashes every source; it sends A's distinct subject/context pairs and the original
distinct subject wordings of every eligible existing hierarchy node. Candidates
can be below other nodes. It excludes A, nodes already related to A by ancestry,
and already-judged pairs (including neither and uncertain). No vector shortlist,
name-based merging, candidate count limit, or candidate contexts are used.

Responses must contain only the candidates array, with one supplied ID and a
nonempty reason per nomination. Unknown IDs, duplicate nominations, invalid JSON
and duplicate JSON keys fail validation. These checks establish format, not
semantic correctness. The saved hierarchy remains unchanged.

The three-root diagnostic selects Joy, Haiti and Chemotherapy from the saved
100-post hierarchy. It uses Astra low through the subscription provider, without
a paid API fallback. Reusable source references and settings are in
[three-roots-selection.json](three-roots-selection.json) and
[three-roots-spec.json](three-roots-spec.json). Generated inputs, responses and
receipts remain ignored under `target/parent-candidate-v1/`.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare \
  target/parent-candidate-v1/pcpv1-three-roots-v1 \
  --spec sse_multivector/parent-candidate-prompt-v1/three-roots-spec.json \
  --history-root target/parent-candidate-v1
```

Only the separately authorized `experiment.py run` command sends model requests.
Inspect answers with `experiment.py show EXPERIMENT --case NODE_ID`.

## Checking saved nominations with BCPv4

The `subject_pairs` adapter also accepts `parent_candidates`: a list of completed
candidate-discovery experiment directories instead of hand-written `pairs`.
It validates their receipts and source hashes, prepares each distinct nominated
node pair, and preserves nomination reasons and receipts as review-only evidence.
BCPv4 sees only the two nodes' original subject/context arrays, including the
candidate node's contexts omitted from PCPv1. It does not see PCPv1's reason or
the rest of its catalogue. Multiple nominations of the same unordered pair
produce one comparison while preserving all nomination evidence.

[bcpv4-nominations-selection.json](bcpv4-nominations-selection.json) references
the completed three-root discovery. [bcpv4-nominations-spec.json](bcpv4-nominations-spec.json)
uses unchanged BCPv4 and Astra-low subscription settings. This prepares seven
pair comparisons without rerunning PCPv1 or applying relationships to the graph.
It is a separate diagnostic, not a new canonical HG selection rule.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py prepare \
  target/branch-comparison-v1/bcpv4-pcpv1-seven-nominations-v1 \
  --spec sse_multivector/parent-candidate-prompt-v1/bcpv4-nominations-spec.json \
  --history-root target/branch-comparison-v1
```

## Ten additional top-level nodes

[ten-roots-selection.json](ten-roots-selection.json) records a deliberately
varied diagnostic sample: Paraguay, Meat cutting and trimming, Sandwiches,
Restaurant closures, Cookware handles, Dog feeding, Audiobooks, Infant age
milestones, Social-media communities and Exercise. These are ten distinct,
previously untested query nodes, not a random sample or an automatic selection
rule. They use the same saved hierarchy, full eligible catalogue, unchanged
PCPv1 and unchanged Astra-low subscription settings through
[ten-roots-spec.json](ten-roots-spec.json).

Discovery is isolated in `target/parent-candidate-v1/pcpv1-ten-roots-v1`.
[bcpv4-ten-roots-selection.json](bcpv4-ten-roots-selection.json) derives pairs
from those completed nominations, and
[bcpv4-ten-roots-spec.json](bcpv4-ten-roots-spec.json) retains unchanged BCPv4
and settings. Checks are isolated in
`target/branch-comparison-v1/bcpv4-pcpv1-ten-roots-v1`. Neither step reruns the
three-root baseline or applies answers to the hierarchy.

## Separate saved-answer hierarchy export

The authorized follow-up applies the ten-root diagnostic's 43 broader-parent
answers to a fresh test output, retaining the two `neither` answers as judgments
without adding links. It uses the saved third-pass hierarchy as its exact base;
the three-root diagnostic's answers are not included. This changes the separate
test graph, not the canonical HG selection rules or the earlier exports.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/experiment.py export-hierarchy \
  target/branch-comparison-v1/bcpv4-pcpv1-ten-roots-v1 \
  --base target/branch-comparison-v1/bcpv4-hg4-third-pass-v1/hierarchy \
  --source sse_multivector/hierarchy-refresh-v1 \
  --output target/branch-comparison-v1/bcpv4-pcpv1-ten-roots-applied-v1
```

The output must not already exist. Export sends no requests, retains every
original node/subject/mask and direct post membership, preserves SP ancestry,
and omits only redundant direct browsing links. It revalidates the nomination
experiments and receipts before retaining their proofs alongside BCPv4 answers.
Cycle and `neither`/ancestry conflicts still stop export without repair.

Replay accepts only the historical metadata difference between omitted default
`settings.transport` and explicit `sse`; all other evidence remains exact, and
a genuinely different transport is rejected. Old artifacts are not rewritten.

Inspect the isolated output with the existing browser:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
target/infomap-review-build/debug/sse-subject-navigation \
  --categories target/branch-comparison-v1/bcpv4-pcpv1-ten-roots-applied-v1/categories.json \
  sse_multivector/hierarchy-refresh-v1/masked-posts.json
```

Whether to adopt broader-parent discovery into the canonical process remains
open. Do not infer approval from this separate export.
