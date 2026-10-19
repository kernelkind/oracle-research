# Note-subset recovery of candidate root sections

Experimental numerical investigation, 2026-10-18. **Do not adopt as a HiGen
policy.** The current target is six useful root sections retaining at least 90%
of original corpus notes, with each section representing at least 10% of the
original corpus. Earlier measurements below retain their original 80% target.
The user prefers cut A
and explicitly accepts broad root topics because deeper levels provide
narrowing. Root breadth alone is not a failure criterion. Recovery under note
removal provides a diagnostic, without establishing better browsing choices.
No prompts, canonical hierarchies or review UIs changed. No model calls,
training or paid resources were used in the original resampling probes.
The latest full-meaning follow-up adds local frozen-SSE encodings, with no LLM
calls or training, and reaches 91% in six complete branches.

## Approved requirements for the next smaller iteration

The user directed reusing an existing 100-note run, rather than drawing a new
subset of HR38. Use HR22's saved ASv6.100/Bootstrap-v133 original inputs. The
2,000-note corpus remains available for checking promising rules. The numerical
requirements are:

- Exactly six sections.
- At least 90% of the original corpus's distinct notes represented across them.
- Each section represents at least 10% of that original corpus's distinct notes.

For 100 notes, every section must represent at least ten notes and their union
must represent at least 90. Deduplicate note IDs within each section and across
the union separately; section note sets can overlap. Use the original corpus
size as denominator, rather than only the notes with usable inputs.

Stopping an ordinary linkage tree at six branches alone does not enforce the
per-section minimum. The user rejected searching a prebuilt tree for branches
meeting these counts and authorized investigating direct six-way partitioning.
Average-linkage and Ward complete cuts can remain descriptive controls, rather
than the candidate construction rule. These numerical requirements do not
qualify section membership or deeper narrowing. Current HiGen behavior and
historical results are unchanged.

### Direct partition candidate: distinct-note-constrained cosine clustering

`sse_multivector/direct_section_partition.py` partitions original entries
directly. All supplied entries participate, including originally unassigned
ones. Existing fine groups are not indivisible constraints in this candidate.
This changes the unit from the preceding group-centroid probes; controls use
exactly the same entry vectors as the candidate.

Minimum-size constraints during assignment follow the approach in
[Bradley, Bennett and Demiriz, Constrained K-Means Clustering](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2000-65.pdf).
Cosine distances and normalized center updates follow
[Spherical k-Means Clustering](https://www.jstatsoft.org/article/view/v050i10).
The distinct-note counting below is an adaptation for this task, not a claimed
result from either paper or a new trained encoder.

For six fixed centers, minimize summed entry-to-center cosine dissimilarity.
Each original entry is assigned once. A note/section witness can count at most
once and requires an assigned entry from that note. Each section requires at
least ten witnesses. This is a sparse minimum-cost-flow linear program; the
implementation uses SciPy's dual-simplex solver and independently checks
integral assignments, optimal fixed-center cost and actual distinct-note
counts. Shared notes across sections remain permitted. It does not replace
distinct-note counts with entry counts or constrain all six sections to be
equal in size.

Alternate assignment and normalized mean-center updates. Eight fixed starts
use the same initial centers for the constrained and unconstrained controls;
choose the lowest summed cosine dissimilarity, without looking at semantic
review labels. Preserve all starts and records of entries displaced from their
closest final center. The objective is local and is not semantic certification.
Sparse assignment storage grows with `sections * (entries + notes)`; vector
comparison grows with `entries * sections * dimensions` per update. There is
no all-pairs matrix, teacher call, training or HiGen activation.

Before real data, production-path tests compare the assignment to exhaustive
optima and cover repeated notes, multi-section note support, infeasibility,
deterministic clustering, monotone costs and the native numerical CLI.

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

## Result: repeatability favors one large section and five small sections

| Corpus | Variance control | Recovery selection | Largest recovery section |
|---|---:|---:|---:|
| HR36 | 802 / 1,000 | 819 / 1,000 | 761 notes; 381 groups |
| HR37 | 802 / 1,000 | 801 / 1,000 | 711 notes; 358 groups |
| HR38 | 1,603 / 2,000 | 1,607 / 2,000 | 1,428 notes; 654 groups |

All choices have six sections and exceed the numerical retention floor. But
the recovery objective selects a large mixed section and five tiny sections,
mostly financial/cryptocurrency topics. HR38's large section includes AI, news,
people, countries, art, greetings and technology. Its held-out recovery remains
high (0.962). This reproduces the size imbalance; it does not establish whether
subsequent narrowing makes the hierarchy useful. The user's later review
accepts broad roots and must not be described as a rejection of root breadth.

## Shuffle control for the size advantage

Large branches match other broad branches well even without informative group
identity. For each of the same 64 sampled trees, independently shuffle surviving
group IDs eight times, preserving tree shape and branch sizes. Repeat the
**same best-branch search** for every shuffle. Adjust observed recovery by
`(observed - mean_null) / (1 - mean_null)`. A guaranteed match under the null,
including the complete tree, contributes zero evidence. Negative adjusted
values are retained. Shuffle seeds are `20261019 + 1000000 + repeat`.

This was specified after seeing the raw selection's section-size imbalance; it is an
adaptive diagnostic, not a prospectively chosen primary result.

| Corpus | Adjusted selection | Largest section |
|---|---:|---:|
| HR36 | 826 / 1,000 (82.6%) | 761 notes; 381 groups |
| HR37 | 801 / 1,000 (80.1%) | 711 notes; 358 groups |
| HR38 | 1,602 / 2,000 (80.1%) | 1,428 notes; 654 groups |

Correction changes some small sections but retains the same large section
in every corpus. It does not materially change the root choices. Eight
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
does distinguish some more-repeatable smaller sections from less-repeatable
broader branches. That distinction is not a semantic or usability judgment.

Using fixed agent-selected headings only for inspection:

- The smallest branch containing Basketball and Sports also contains War in
  **1 of 64** subsets. All three groups survive in all 64.
- Adding Association football and American football as sports anchors includes
  War in **2 of 64** subsets. All four sports anchors survive in 63 subsets;
  only three survive in the remaining subset.

The broad tree therefore usually has a sports branch separate from War before
the six-section choice. The cut selects their broader ancestor. This localizes
the combined placement to the branch choice in this probe; it does not prove
individual notes caused the merge or establish a general semantic boundary.
The user's later review explicitly accepts this broad-root choice in A.

## Visual comparison of two six-section cuts

A manual alternative from the same saved tree separates the sports and
war/politics children while combining the greetings and technology/news/art
branches at their existing common ancestor. That ancestor also includes a
54-group branch with Data, Analysis, Scientists, Life, Testing, Rankings and
other topics. No canonical definition was generated or changed.

| Choice | Sections | Distinct notes | Coverage | Change from A |
|---|---:|---:|---:|---|
| A: earlier variance cut | 6 | 1,603 | 80.15% | Baseline |
| B: separate sports; combine the other branches | 6 | 1,633 | 81.65% | 30 gained, zero lost |

A selects saved tree nodes `1516,1533,1544,1547,1551,1553`; B selects
`1516,1533,1506,1543,1551,1554`. Node numbers refer only to the frozen
779-group Ward tree. Group memberships remain disjoint within each cut;
note memberships can overlap. A's 202-note sports/war branch becomes
49-note sports and 159-note war/politics branches. Its 247-note greetings
and 810-note technology/news/art branches become a single 1,037-note branch
also containing the 54 additional groups. These per-branch counts must not be
summed as distinct-note coverage.

This illustrates an actual trade between available cuts, not a new automatic
selection rule or a claim that B is semantically superior. Both meet the
numerical requirements. The user reviewed the PNGs, preferred A, and explained
that broad root topics are acceptable because deeper levels provide narrowing.
This is a research preference, not activation of a new HiGen policy. The official
HR38 HiGen hierarchy is untouched.

Ignored review artifacts alongside `note-resampling-v1/`, in
`competing-cuts-review-v1/`, contain the side-by-side PNG, collapsed-tree PNG,
exact note/group memberships, input hashes and the single-comparison renderer.
Image filenames are `hr38-competing-six-section-cuts-v1.png` and
`hr38-competing-cut-branches-v1.png`. Actual set-union checks verify all counts,
30 gained notes, zero lost notes and exactly six disjoint branches in both cuts.

## Ninety-percent coverage probe

The user next requested exploration of 90% coverage. The fixed original
975 HDBSCAN groups contain only 1,778/2,000 notes (88.9%): no cut over just
those groups can reach 90%. The original clustering input also contains 3,580
unassigned entries. Together, all 10,188 valid native inputs represent
1,829 notes (91.45%). The other 171 notes have no entry in this saved native
clustering input; this probe assigns no fault for their absence.

The three saved full-meaning banks have exact matches for 4,648 original
entries across 1,778 notes, also below 90%. This follow-up therefore uses the
complete **native title-pooled vectors with each meaning as context**, uniformly
for groups and unassigned entries. A used full-meaning pooling and partial
original groups. Both representation and eligibility change, so the resulting
coverage is not a matched quality improvement over A.

Keep each original HDBSCAN group intact with all original members. Make each
originally unassigned entry an additional eligible singleton unit; none is
automatically admitted. Construct unit centroids, rebuild the Ward tree and
reuse the variance cut objective with six disjoint branches and at least 1,800
distinct original note IDs. No HDBSCAN parameter changes, new encodings or
teacher calls. No mixture of title-pooled and meaning-pooled vectors.

| Eligible units and cut | Sections | Distinct notes | Coverage |
|---|---:|---:|---:|
| Original groups only; complete six-way cut | 6 | 1,778 | 88.9% |
| Original groups plus unassigned entries; constrained cut | 6 | 1,800 | 90.0% |
| Same expanded pool; complete six-way cut | 6 | 1,829 | 91.45% |

The constrained result selects 739 original groups and 2,643 originally
unassigned entries. It gains 42 notes outside the original grouped-note set
and omits 20 of that original set: a net gain of 22. Relative to A it gains
214 notes and loses 17, but the changed representation/eligibility prevent a
controlled causal attribution. Per-section note counts are 329, 1,074, 713,
776, 931 and 441; these overlap and must not be added. The complete cut keeps
all available native notes and loses none of A's represented notes. Neither
result establishes the usefulness of a complete hierarchy with deeper levels.

Plans, exact memberships, vector/tree arrays and numerical results are ignored
under `ninety-percent-cut-v1/attempt-2/`, beside the other probes. A first local
attempt stopped on NumPy integer JSON serialization before optimization; its
source, plan and failure status are retained. The corrected numerical run
finished in 18.4 seconds and reached a 0.61% solver objective gap. Its coverage
and disjointness are independently checked from original entry/note IDs.

Numerically, 90% is attainable using existing vectors once unassigned entries
are eligible. A fair comparison with A's pooling needs additional frozen-SSE
meaning encodings; none were performed in this probe.

## Matched full-meaning follow-up: 91% in six complete branches

The user authorized completing the full-meaning vectors and repeating the
expanded-pool test. This follow-up restores A's exact representation: context
is `title + two newlines + complete explicit meaning`, pooling the complete
meaning. It does not pool the original post, shorten the definition, rewrite
headings or meanings, train a model, or call an LLM.

### Completion and validation

Reuse 4,648 exact original-entry vectors from the three existing banks. The
remaining 5,540 entries have 5,505 distinct contexts. The existing native
`title_selection_probe` adapter now accepts an ASv6.100 native hierarchy state
and prepares contextual whole-title/whole-meaning views. It binds the original
entries, corpus, model settings and source files; deprecated AS versions and
non-original native inputs are rejected. The normal native `worker.py` and
adapter `collect` paths run and validate the encoding; no separate execution
service or teacher runner is introduced.

The local offline CPU worker encodes 5,505 missing contexts plus eight
deterministically selected cached replay contexts, producing 11,026 span
vectors. Title and meaning vectors share each encoder forward pass. The frozen
checkpoint, base-model artifacts and pooling rule are unchanged. New encoding
uses native batch size eight; the prior meaning banks used 32. Replay checks
verify the resulting numerical agreement rather than assuming identical runtime
settings. CPU affinity allows 24 of the machine's 28 CPUs, leaving four.

| Check | Result |
|---|---:|
| Newly encoded title contexts checked against native vectors | 5,513 |
| Maximum normalized title-vector absolute difference | 1.16e-7 |
| Cached full-meaning replay contexts | 8 |
| Maximum normalized meaning-vector absolute difference | 6.85e-8 |

Frozen pre-result bounds were 1e-5 maximum absolute difference and 1e-6 cosine
error, matching the earlier replay checks. All checks pass; the model is not
refitted or otherwise changed.

### Matched numerical comparison

Apply A's zero-known-lexical-context check to both representations. It excludes
37 original entries, leaving 10,151 entries representing 1,820 notes. The
eligible units are identical for title and meaning: 975 original HDBSCAN groups
with eligible members, plus 3,580 eligible originally unassigned entries as
singleton units. No fine groups are reclustered. Unit weights, Ward algorithm,
root count and numerical objective are identical between the two views.

| Representation | Cut | Sections | Distinct notes | Coverage |
|---|---|---:|---:|---:|
| Title | Variance objective with 90% floor | 6 | 1,800 | 90.0% |
| Full meaning | Same objective and floor | 6 | 1,800 | 90.0% |
| Title | Complete six-way tree cut | 6 | 1,820 | 91.0% |
| Full meaning | Complete six-way tree cut | 6 | 1,820 | 91.0% |

The complete cuts cover the same notes by construction; these equal totals do
not show that either representation is semantically better. Their branch
memberships differ. For example, the largest complete meaning section represents
1,170 notes, versus 1,666 for title. Root breadth alone is not an error under
the user's clarified goal. No lower-level narrowing or finished-hierarchy
quality is established by this root-only probe.

With broad roots acceptable, the **complete six-way cut removes the need to
prune toward a 90% target**. It retains all 1,820 usable input notes, preserving
all of A's 1,603 represented notes and adding 217. Of those additions, 164 have
eligible routes through original groups omitted by A, and 53 require an
originally unassigned entry after the common lexical check. The constrained
90% meaning cut instead gains 211 and loses 14 relative to A, so it is not
necessary for this coverage goal.

The six complete meaning branches represent 665, 861, 630, 917, 512 and 1,170
notes respectively. These overlap; the total is the union, not their sum.
Remaining omissions are 171 notes without any saved native clustering input
and nine whose available contexts have no recognized lexical tokens in the
frozen encoder. No fault or new semantic rejection is assigned to those notes.

### Evidence and status

All new artifacts are ignored under `meaning-completion-v1/`, alongside the
earlier probes. They include preparation/preflight plans, exact cache bindings,
native worker inputs/config/receipt, raw span vectors, complete normalized
meaning vectors, replay checks, matched unit centroids, both trees and cuts,
independent note/group membership checks, and
`hr38-full-meaning-91-percent-six-sections-v1.png`. Data stays on the external
drive. All protected source hashes remain unchanged. Eighteen adapter/worker
tests pass in the actual cached CPU environment with no skips, including the
native-source and pooling paths.

This is a successful numerical coverage result using A's pooling, not an
official HiGen run or policy activation. Missing meaning vectors were computed
locally; LLM calls, training and paid resources remain zero. Inspecting the next
level of the broad branches is the next useful check before claiming useful
hierarchy narrowing.

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
