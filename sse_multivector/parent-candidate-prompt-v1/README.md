# PCPv1: broader-parent candidate diagnostic

[PCPv1](PCPv1.md) nominates possible broader parents for one top-level hierarchy
node. It does not judge equivalence, authorize placements, or change the HG rules.
Its output is a possible input to a separately authorized BCPv4 comparison.
Status: tested in the separate three-root diagnostic; not frozen or adopted.

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
