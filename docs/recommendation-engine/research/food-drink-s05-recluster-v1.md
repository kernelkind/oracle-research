# Food & Drink reclustering after S05 replacement

Status: authorized experimental replacement and numerical rerun. The user
approved replacing all original local entries represented by S05 with its
single synthetic definition, then redoing HDBSCAN and epsilon selection.
Previously unassigned entries remain eligible. This does not activate a
production HiGen policy or alter HR22.

The source is the [100-note epsilon review](food-drink-hundred-epsilon-v1.md)
and its [completed S05 synthetic-root trial](food-drink-s05-root-v1.md).
The existing title and meaning, Food and domestic animals, are reused exactly.
All 113 original S05 entries are removed from clustering input. Their 58-note
union and original-entry associations are attached to one replacement item.

## Controls and preparation

The original 728 encoded entries become **616 inputs**: 615 unchanged original
entries plus one synthetic entry. All 361 previously unassigned encoded
entries are retained. The five original null Bootstrap meanings remain absent.
Only the replacement requires encoding; existing original vectors are reused
byte-for-byte from validated native worker receipts.

Its SSE input is the synthetic title followed by two newlines and the complete
explicit meaning. Only title bytes are selected for pooling. The same pinned
checkpoint, sentence-T5-base artifact, 768 dimensions, 512-token limit, CPU
device and learned pooling layers are used. The replacement counts as one
vector for density calculations; it is not replicated or weighted by 113.
Note counts expand its retained original associations and deduplicate IDs.

The reusable project CLI, `sse_multivector.hdbscan_section_replacement`, validates
the native consolidation receipt, exact section input, original HDBSCAN result,
state and source hashes. It prepares the existing SSE worker path and collects
that worker's validated receipt before numerical reclustering. No teacher
requests, prompt changes or paid resources are added.

HDBSCAN uses the unchanged angular-distance configuration: `min_samples=3`,
`min_cluster_size=2`, excess-of-mass selection. The 10%-trimmed bend epsilon
rule is unchanged and applied anew to the newly selected groups. Group and
section IDs refer to this rerun, not the old review. Unassigned inputs are
reported without inventing assignments or retaining old group labels.

## Reproduce

Run from the retained task worktree, with the original source worktrees kept
available for their absolute hash-bound references:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-s05-recluster-v1
python3 -m sse_multivector.hdbscan_section_replacement prepare \
  target/food-drink-s05-recluster-v1 \
  --experiment ../oracle-mvp-food-drink-s05-root-v1/target/food-drink-s05-root-v1/experiment \
  --case S05
```

Run the ordinary `sse_multivector.worker` on the emitted worker config using
the pinned local Torch 2.13.0+cpu / Transformers 4.57.1 runtime, then collect:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-s05-recluster-v1
python3 -m sse_multivector.hdbscan_section_replacement collect \
  target/food-drink-s05-recluster-v1 \
  --name food-drink-100-after-s05
```

The ignored output contains the frozen replacement plan, one encoding job,
new HDBSCAN request/result, complete analysis, compact group/section table,
and uniquely named colored SVG. The synthetic node's assignment or unassigned
status is explicit. This trial names no additional sections and refreshes no
hierarchy UI.

## Verification

A production-path test initially failed because section replacement was
unavailable. It now uses native preparation and saved receipts, runs the real
worker path with a controlled external encoder, and collects through the
numerical HDBSCAN interface. It verifies exact removal, retention of previous
unassigned inputs, unchanged original vectors, title-only pooling, expanded
note support, source immutability and rejection of changed evidence.
All 15 replacement, native source, epsilon and HDBSCAN checks pass.

The task worktree remains for its new vector, frozen source paths and review
artifacts. Generated data is ignored. No semantic quality claim follows from
these mechanical checks.
