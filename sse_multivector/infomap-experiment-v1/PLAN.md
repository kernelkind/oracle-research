# Infomap comparison

Approved 2026-09-10. Stop after the four saved configurations, nested TUI inspection, and evidence-backed analysis. A poor result is a valid stopping outcome. No new prompts, masks, vectors, generated titles, manual group repairs, or final algorithm selection.

## Fixed inputs

100 real notes, 916 canonical SSE vectors, 945 original mask records. Reuse the four source files recorded by M07, checking their SHA-256 hashes before every run. Preserve their ordered canonical IDs and every alias.

M07's graph connects all eligible cross-note pairs with weight `1 - angle / pi`. The saved HDBv3 distances equal original angular distances on those eligible pairs. Same-note pairs remain absent. Do not use M07's merge scores as graph edges.

## Runs fixed before inspecting output

| Run | Connections |
| --- | --- |
| I01 | Exact dense M07 graph |
| I02 | Each vector chooses its 5 nearest eligible vectors |
| I03 | Each vector chooses its 10 nearest eligible vectors |
| I04 | Each vector chooses its 20 nearest eligible vectors |

For I02–I04, keep an undirected connection if either endpoint chooses it. Break exact distance ties by canonical node ID. Retain the exact M07 weight on every retained edge. These are nearest vectors, not nearest distinct notes; multiple vectors from another note can occupy the list. No new edge or connection between disconnected components is introduced.

Infomap 2.15.1; undirected flow; native hierarchical mode; seed 123; ten internal trials, keeping Infomap's shortest-description result. Other algorithm settings stay at that release's defaults. NumPy 2.3.4; one OpenMP/BLAS thread; run configurations sequentially. No paid compute or model inference. Save the input graph, configuration, source/code checksums, native tree/JSON, complete memberships, trial scores, elapsed time, and peak memory. Refuse to overwrite an output directory.

Five, ten, and twenty are exploratory neighborhood settings, not established semantic thresholds. Compare all three without choosing a favorable setting after seeing one example. Internal trials reduce search randomness but do not constitute a semantic reliability estimate. Codelengths from different graphs are not directly comparable quality scores.

## Inspection

Preserve the native module nesting, including one-note modules and equal-note parent/child transitions, so the experiment does not hide what Infomap produced. Do not fabricate binary merges or distances to fit the viewer. Show exact masks, N/V IDs, full original notes, and an option to reveal parent masks normally hidden because their note already appears recursively below.

Read the complete module memberships and inspect originals for questionable cases. Record supported broad-to-narrow organization, questionable placements, useful groups lost or mixed, and uneven coverage. Treat labels as interpretations, never evidence. The accepted manual coffee example is one valid arrangement, not a uniquely correct target. Distinguish problems in masks/vectors from grouping errors when the evidence allows; otherwise leave the cause unresolved.

Compare I01 with existing M07 to change only the hierarchy algorithm. Compare I02–I04 with I01 to change only the retained connections. Keeping SSE frozen does not establish that every vector is correct. A negative dense-graph result alone does not invalidate Infomap with other graphs.
