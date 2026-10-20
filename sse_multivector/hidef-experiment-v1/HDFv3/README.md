# HDFv3 — finer resolutions on the original graph

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

The added range exposes useful groups that the old range missed, but it does not repair the hierarchy as a whole. The clean Satoshi/Satoshis pair now appears during clustering in every repeat, then disappears at the unchanged persistence step. Some useful new choices coexist with unrelated associations and levels that return the same notes. No algorithm or new viewer default is adopted. CREC-124.

## What changed

Each run reuses all 242 saved original-graph partitions through resolution 25, then adds 72 resolutions through 190. Notes, masks, vectors, connections, weights, clustering objective, persistence, containment, and display rules are unchanged. The old resolutions, seeds, memberships, scores, timings, and candidate IDs were preserved exactly—not regenerated.

The endpoint was calculated from the original graph's objective, not selected after viewing results. At 190 every raw group is a single vector, as expected. These one-note groups remain hidden in the TUI; reaching them does not mean we want singleton navigation destinations. [PLAN.md](./PLAN.md) was frozen before all three corpus runs, SHA256 `e95c8302d1c7694a457834332935b470de9a032f30e494218ce8cbca7b8b2760`.

| Result | Seed 123 | Seed 124 | Seed 125 |
| --- | ---: | ---: | ---: |
| Earlier multi-note groups, excluding root | 239 | 235 | 243 |
| HDFv3 multi-note groups, excluding root | 873 | 853 | 859 |
| Notes represented | 100 | 100 | 100 |
| Clean Satoshi-pair raw occurrences | 4 | 3 | 4 |
| Persistent groups containing both Satoshi vectors, excluding root | 0 | 0 | 0 |
| Parent–child edges returning the same notes | 63 | 66 | 62 |
| Elapsed seconds | 18.18 | 17.93 | 18.14 |
| Peak process memory, MiB | 725.8 | 723.9 | 723.8 |

The primary run adds 675 multi-note memberships and loses 41 previous ones; 198 previous multi-note memberships remain exact. All old raw results remain, but additional candidates can change the memberships produced by persistence. Counts do not measure semantic quality.

## What we learned

**The old range missed a useful candidate.** Canonical vectors 187 and 691 are V189/N024, ⟦satoshi⟧, and V433/N054, ⟦Satoshis⟧. They never formed an exact raw pair in the original range. In the primary extension they do at resolutions 60.715, 66.7704, 86.037, and 88.8072. Their appearances form two separate two-candidate components in HiDeF's candidate graph. Neither can meet the unchanged persistence requirement of five. The repeats likewise have too little connected support. No threshold was changed to rescue them.

**Some new retained groups are useful.** In seed 123, group 1498 joins a second coffee with wanting another coffee, directly under the unchanged 15-note coffee group 951. The same two-vector membership appears in both repeats. Group 1058 collects five notes with tomato buying, preparation, and cooking masks. Group 996 is a more coherent kitchen-appliance/use group than the previous storage/appliance mixture. These are local findings, not approval of every ancestor.

**More resolution does not ensure better organization.** The original mixed Satoshi group remains as 1047. New group 1532 pairs ⟦satoshi⟧ with ⟦Sorrento's Savory Stroll⟧ ⟦easy⟧. Within coffee, group 1605 pairs a cream-versus-half-and-half distinction with iced coffee served in ice; both are coffee-related, but a useful further refinement is not established. Groups 1028 → 1071 return the same six egg notes, and 996 → 1049 return the same three appliance/use notes.

Thus the experiment identifies a real omission in candidate generation and shows a concrete candidate lost during persistence. It does **not** establish that lowering persistence is the right remedy or that useful parent–child relationships now emerge reliably. The frozen sample, positives, and concerns are recorded in [inspection.md](./inspection.md); numerical lineage and exact memberships are in `./comparison.json`.

## Handoff

The user requested results directly in chat rather than a TUI. No new viewer interface is included; the existing viewer remains unchanged. This changes the handoff specified in the pre-run plan, not the computational experiment or its inspection sample. The complete saved memberships, masks, and evidence remain in the run artifacts and [inspection.md](./inspection.md).

## Preservation and reproduction

All 120 saved HDFv1/HDFv2 run files remain byte-identical to the preceding commit. No extraction, SSE inference, paid services, graph modification, label generation, or manual membership repair occurred. Each HDFv3 directory saves every stage and its hashes, including the exact source run's manifest and the additional resolutions.

Reproduce into a new directory; an existing destination is rejected:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
sse_multivector/run-hidef-experiment.sh 123 /tmp/hdfv3-repeat \
  --extend-from /home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hidef-experiment-v1/HDFv2/original/seed123 \
  --maxres 190
```

Add `--plan` to validate and inspect configuration without clustering. Each extension uses the existing sampler on [25, 190], excluding 25, and joins old and new resolution neighborhoods. New samples continue the original seed-plus-index policy. Merely rerunning the old command with a larger endpoint would generate a different lower-range schedule; this extension does not do that.

The independent checker verified all source/graph/manifest hashes, exact preserved prefixes and old graph relationships, all 1,668 baseline-plus-extension partition scores, consensus memberships, strict containment, and all-singleton endpoints. Fifty Python regression tests and four launcher tests passed, with expected new-test failures verified before implementation. These are implementation checks, not semantic approvals.

The saved comparison can be recomputed without clustering:

```bash
python3 sse_multivector/compare_hidef_resolution_extension.py --output /tmp/hdfv3-comparison.json
```

The output path must not already exist. Analyst review covers the preselected cases and four mechanically selected new primary groups, plus targeted follow-up examples—not all 873 displayed primary groups. User inspection and the broader hierarchy decision remain open.

**Selected release data:** The [publication catalog](../../../docs/experiments/publications.csv) identifies the compact final-result export derived from the saved source:

- `numerical/comparison-57fb1c0a8acd9334` — original `comparison.json`, bound by its recorded source SHA-256.

The export uses the publication format; the original files referenced above remain outside this checkout. Downloads are still being prepared.
