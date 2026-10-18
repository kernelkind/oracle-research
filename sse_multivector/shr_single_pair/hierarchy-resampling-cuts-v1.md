# Note-subset recovery of candidate root sections

Experimental numerical investigation, 2026-10-18. **Do not adopt as a HiGen
policy.** The task is six useful root sections retaining strictly more than 80%
of original corpus notes. Recovery under note removal provides a diagnostic but
did not produce satisfactory root choices. No prompts, canonical hierarchies or
review UIs changed. No model calls, encodings, training or paid resources.

## Question and controlled inputs

Does removing different notes break the previously flagged sports/war/politics
mixture, and can repeatability select better roots? These mixtures are agent
concerns, not new human semantic gold.

Use the same exact saved full-meaning vectors and original HDBSCAN group
identities as the preceding retention-cut probe. Exclude the previously audited
contexts with no recognized lexical tokens, identically for all controls.
Meanings are from the existing ASv6.100-derived source runs. No unmatched entry
inherits its group's placement. These are partial original groups when only
some members have saved full-meaning vectors.

| Corpus | Total notes | Available matched notes | Available groups |
|---|---:|---:|---:|
| HR36 | 1,000 | 853 | 425 |
| HR37 | 1,000 | 828 | 410 |
| HR38 | 2,000 | 1,714 | 779 |

This rebuilds broad **Ward trees**, holding original fine-group identities
fixed. It does not rerun HDBSCAN or measure the stability of initial group
discovery. All input/state/vector hashes are retained and verified.

## Measurement

1. Independently select 80% of available notes without replacement 64 times
   per corpus, seed `20261019`. All entries from a selected note stay together.
   The 80% sampling fraction is a diagnostic setting, not an admission cutoff.
2. Recompute unit group centroids from surviving members, then rebuild the Ward
   tree. A surviving original group keeps its identity even with one member.
3. For each original branch, restrict its membership to surviving groups. Find
   the sampled branch with the greatest Jaccard agreement: shared groups divided
   by the union of groups. Fewer than two surviving groups are uninformative.
4. Use the first 32 subsets to select roots; report recovery on the other 32
   without using them for selection. This is within-corpus replication, not
   untouched-corpus generalization.

The selection minimizes `group_count * (1 - mean_recovery)`, summed over six
disjoint original-tree branches, subject to the actual union of note IDs
exceeding 80% of the whole corpus. Omissions are allowed. Singleton branches
have no nontrivial connection to test and zero instability cost; their reported
recovery value of one is a bookkeeping convention, not empirical evidence.
The mixed-integer solver has a 1% relative objective tolerance, not an exact
optimality guarantee or semantic similarity cutoff.

The control minimizes within-section squared differences of group centroids
under identical tree, membership and coverage constraints.

## Result: repeatability alone favors a broad catch-all

| Corpus | Variance control | Recovery selection | Largest recovery section |
|---|---:|---:|---:|
| HR36 | 802 / 1,000 | 819 / 1,000 | 761 notes; 381 groups |
| HR37 | 802 / 1,000 | 801 / 1,000 | 711 notes; 358 groups |
| HR38 | 1,603 / 2,000 | 1,607 / 2,000 | 1,428 notes; 654 groups |

All choices have six sections and exceed the numerical retention floor. But
the recovery objective selects a large mixed section and five tiny sections,
mostly financial/cryptocurrency topics. HR38's large section includes AI, news,
people, countries, art, greetings and technology. This does not resolve useful
browsing categories. Its held-out recovery remains high (0.962), so merely
checking fresh subsets does not remove the problem.

## Shuffle control for the size advantage

Large branches match other broad branches well even without informative group
identity. For each of the same 64 sampled trees, independently shuffle surviving
group IDs eight times, preserving tree shape and branch sizes. Repeat the
**same best-branch search** for every shuffle. Adjust observed recovery by
`(observed - mean_null) / (1 - mean_null)`. A guaranteed match under the null,
including the complete tree, contributes zero evidence. Negative adjusted
values are retained. Shuffle seeds are `20261019 + 1000000 + repeat`.

This was specified after seeing the raw selection's catch-all failure; it is an
adaptive diagnostic, not a prospectively chosen primary result.

| Corpus | Adjusted selection | Largest section |
|---|---:|---:|
| HR36 | 826 / 1,000 (82.6%) | 761 notes; 381 groups |
| HR37 | 801 / 1,000 (80.1%) | 711 notes; 358 groups |
| HR38 | 1,602 / 2,000 (80.1%) | 1,428 notes; 654 groups |

Correction changes some small sections but retains the same broad catch-all
in every corpus. It does not rescue this root-selection objective. Eight
shuffles are a finite diagnostic, not an exact null-distribution calculation.

## Sports/war diagnostic

HR38's variance-selected 87-group branch has two immediate children: a sports
branch of 17 groups/49 notes and a war/politics/institutions branch of 70
groups/159 notes. Their note sets overlap; counts must not be added as coverage.

| Original branch | Discovery agreement | Held-out agreement |
|---|---:|---:|
| Sports child | 0.708 | 0.727 |
| War/politics child | 0.483 | 0.475 |
| Combined parent | 0.456 | 0.446 |

These are mean best-branch Jaccard agreements, not semantic accuracy scores.
The smaller sports child is more reproducible than the selected parent, while
the 125-group finance section has held-out agreement 0.835. Thus the diagnostic
does distinguish some strong smaller sections from weak broad mixtures.

Using fixed agent-selected headings only for inspection:

- The smallest branch containing Basketball and Sports also contains War in
  **1 of 64** subsets. All three groups survive in all 64.
- Adding Association football and American football as sports anchors includes
  War in **2 of 64** subsets. All four sports anchors survive in 63 subsets;
  only three survive in the remaining subset.

The broad tree therefore usually has a sports branch separate from War before
the six-section choice. The cut selects their broader ancestor. This localizes
this failure to the branch choice in this probe; it does not prove individual
notes caused the merge, establish a general semantic boundary or imply six
useful roots are impossible.

## Reproduction and verification

Reusable numerical CLI: `sse_multivector/cluster_resampling_probe.py`; tests:
`sse_multivector/test_cluster_resampling_probe.py`. Input NPZ contains unit
`vectors`, aligned compact zero-based original `groups`, and aligned `notes`.
It has no inference or HiGen integration. Dense best-match matrices require
quadratic group-count space; this is a bounded research probe, not a proposed
large-corpus production step. Sixty-four repeats across 425–779 groups took
6–20 seconds per corpus in the recorded runs with one BLAS thread each.

Artifacts are ignored under the retained task worktree:

`target/food-halves-v1/hr38-six-branch-distance-probe-v1/note-resampling-v1/`

That directory is stored on the external drive. It includes frozen input
plans/hashes, numerical inputs, exact original-entry bindings, every sample's
notes, raw/null/adjusted agreements, discovery/held-out results, chosen group
and note memberships, source snapshots and independent verification. Raw and
shuffle controls use exactly identical note subsets and raw recovery arrays.
Four full-note controls recover all nontrivial original branches exactly.
Independent checks reconstruct selected-note unions and set-based Jaccard
values on fixed subsets in every corpus. Source states and vectors are unchanged.

Cluster recovery by resampling is established methodology; stable output still
does not establish semantic correctness. See [Hennig, Cluster-wise assessment
of cluster stability](https://www.homepages.ucl.ac.uk/~ucakche/papers/clusta.pdf).
The specific note-level sampling, constrained root objective and shuffle
adjustment above are experimental choices here, not claims from that paper.

**Conclusion:** retain resampling as diagnostic evidence. Neither raw nor
chance-adjusted recovery is justified as the automatic root-selection rule.
