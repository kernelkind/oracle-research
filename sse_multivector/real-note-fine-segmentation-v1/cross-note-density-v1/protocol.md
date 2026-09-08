# Cross-note density: full-partition trial

The user approved recomputing the entire HDBSCAN result, not only the omitted pairs, and explicitly required preserving previous results.

## Question

Does measuring density using the nearest vector from a different note recover useful multi-note segments without damaging the previously accepted groupings?

## Control and change

The control is the saved `hdbscan-baseline` result: all 945 frozen vectors, angular distance, `min_samples=2` (including the point itself), `min_cluster_size=2`, and excess-of-mass selection.

In the control, the core distance is the distance to the nearest other unique vector. In the trial, it is the distance to the nearest vector from another source note. Source note IDs come from the verified frozen vector map. They affect this calculation only.

Exact duplicate vectors remain collapsed before clustering, as in the baseline. All source notes represented by an alias group are retained for the new calculation. If an identical vector occurs in two notes, its cross-note core distance is zero. Aliases still count as one point for cluster size and stability; their original IDs are restored afterward.

Recompute all mutual-reachability distances, the minimum spanning tree, the hierarchy, condensation, and EOM selection. Their formulas and tie rules remain unchanged. Do not remove same-note edges, force any reviewed pair to merge, alter the vectors, or change a prompt. This trial supports `min_samples=2` only; it does not define a general note-weighted HDBSCAN estimator.

## Comparison

- Compare every baseline and trial segment, including one-note segments and noise.
- Report exact unchanged membership, all changed baseline multi-note groups, and newly grouped or ungrouped vectors.
- Track the six user-approved omitted pairs and the five user-rejected pairs separately. Sharing a new segment does not establish that the whole segment is valid.
- Inspect the actual masks in every new multi-note segment. Assistant judgments remain separate from user judgments.
- Present only new or changed multi-note segments in the existing unnamed masks-only reviewer. Retain unchanged segments in the complete trial output. Do not create titles or automatically populate user answers.

This is a controlled development trial on already examined data. Neither a higher group count nor recovery of the six known pairs alone establishes improvement or overall recall.

## Preservation and execution

`preserved-before.json` freezes 65 existing result, input, and review files before the trial. It includes baseline, leaf, density, the complete vector artifact, the prior review handoff, and omission-review records. Check every listed file again after execution.

The new result goes in `../hdbscan-cross-note/`; comparison and a separate user-review artifact go here. Artifact writers refuse existing output paths. Previous results and decisions are not rewritten.

Run the pinned executable twice in fresh processes and require identical complete parsed responses before review packaging. Record the exact candidate identity, source-note-map digest, source hashes, binary digest, and invocations. No subject, mask, SSE, or LLM generation is needed. Use local CPU with bounded memory and concurrency.
