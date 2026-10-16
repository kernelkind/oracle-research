# Hierarchy advancement: shared evidence reads

User-authorized performance fix, October 12, 2026. It changes evidence-reading
work, not selection, prompts, meanings, relationships, retries or allowances.

Every advancement still checks the saved construction sources and validates
all retained experiment answers, including failed receipts and the original
producer behind exact reuse. Previously, reporting reread and parsed result
ledgers, and each reused producer review reloaded large prepared plans and
rebuilt the receipt index. Those operations repeated across cases in a batch.

The shared runner now provides operation-scoped parsed files, validated frozen
plans and receipt indexes. Changed file metadata invalidates the cached read.
Collection uses one isolated scope per experiment batch: its producer files
are shared across that batch's cases, then released. Advancement's remaining
reads have their own surrounding scope. No validation verdict survives an
advancement. All original receipt and bound-review checks remain in place.

## Matched offline measurement

A frozen copy of HR10 contained 665 experiment records; 662 already had saved
answers and were used in both measurements. Only native collection ran, with
no advancement, placements, inference, live experiment writes or UI changes.
The original source was the frozen HR10 continuation and runner. The candidate
used the performance fix. Both validated experiment lists have SHA-256
`266fdebe740954d2e26f90c9cea2fc13b706876471be35ea76cd3056f8a0726e`.

| Measurement | Original | Fixed |
| --- | ---: | ---: |
| Collection wall time | 137.557 s | 14.975 s |
| Collection CPU time | 136.861 s | 14.382 s |
| Peak process RSS | 417,252 KiB | 333,608 KiB |

Wall time fell 89.1% (9.19 times faster); peak RSS fell 20.0%. This measures
receipt collection, not full advancement or end-to-end hierarchy generation.
Other active work could affect wall time. Generated snapshot and measurement
artifacts remain ignored under `target/advancement-reads-v1/` in the performance
task worktree.

Native-path regressions check one ledger read per advancement, shared reads
across reused-source reports, in-scope prepared-file change detection and
receipt tampering on a subsequent advancement. Existing producer-review,
failure-receipt, constructor and resume checks remain required.

## Existing frozen runs

Landing this fix did not change HR10's process or either of its frozen source
checkouts. HR10 was subsequently stopped by the user without adopting this fix.

Adoption requires a recorded continuation using updated
runner/project source bindings after active native batches finish. Preserve
all original inputs, prompt versions, graph history, receipts and the existing
attempt counter. Never edit the currently bound source in place or start a
second constructor against the active trial. The existing native
`--runner-upgrade-reason` path records reviewed code changes.

## HR35: larger clustering evidence and independent membership jobs

The 1,000-note V5.3 run exposed two further runtime costs. Its six root
membership clusterings originally ran serially. One saved result was
676,422,679 bytes; its compact retained view was 2,036,262 bytes. Multiple
root-generation and membership views exceeded the ordinary reader's 16 MiB
budget, causing eviction and repeated decoding of the large raw results.

Independent sibling membership jobs now start concurrently on local CPUs.
Each reads the same frozen input and writes its own directory. Results remain
collected in sibling order and applied atomically after the whole pass. Existing
completed results survive failures and are reused on resume. Teacher work still
uses the shared provider queue without an outer submission cap.

Hierarchy HDBSCAN views use a 1 GiB serialized retention budget, allocated only
as files are read. Both native `run-hierarchy` and standalone advancement use
the same scoped reader. Whole-source hashes, changed-file invalidation, receipt
checks and numerical/graph validation remain required. This budget does not
bound Python process RSS. Shared runner commit `132a0cd` adds the configurable
projected-view limit while preserving the ordinary 16 MiB default.

A no-inference replay used HR35's exact pre-membership checkpoint and frozen
clustering binary. All six requests and all six result files matched the
serial run byte-for-byte; six simultaneous clustering processes were observed.
Evidence is ignored under `target/parallel-membership-replay-v1/` in
`oracle-mvp-hr35-validation-performance-v1`. The replay is a numerical
equivalence check, not a semantic accuracy or model-cost improvement claim.

Production-path tests first reproduced serialized-job failure and compact-view
eviction. The final 118 hierarchy/HDBSCAN/V3 checks and 24 shared receipt-reader
checks pass, including corruption detection and completed-result recovery.

## Multicore continuation

The user authorized using 24 of this machine's 28 CPUs, leaving four for other
work. Native `run-hierarchy --cpu-workers 24` records the runtime budget; its
default leaves four available CPUs. Linux affinity is limited for the
coordinator and inherited by newly started children, then restored on exit.
Simultaneous membership clusterings divide this budget. Provider queue
admission remains separate.

Independent saved HDBSCAN rounds and their section cuts are rechecked in
worker processes when their combined input count reaches 1,024 vectors. Small
checks stay inline. Workers receive the same immutable state snapshot, rebuild
the expected requests, hash complete evidence files and reproduce all groups
and cuts; validation verdicts are not retained between advancements. No model
request or placement depends on the numerical worker-completion order.

An explicit `--hdbscan-binary` replacement requires a reviewed
`--runner-upgrade-reason` and settled teacher batches. The native upgrade
records old and new paths/hashes and the unchanged graph hash, preserving
the original executable and saved results. It does not edit frozen definitions.
The shared source launcher requires commit `38561fe` or later: multiprocessing
imports it as `__mp_main__`, which must not dispatch the parent CLI command.
A real project-extension process-pool regression reproduces the earlier
worker-startup failure and passes with its `__main__` guard. The first HR35
multicore launch exposed this entry-point issue before any teacher calls; its
failed invocation is preserved and the guarded launcher is now on local main.

### Saved 1,000-note input checks

The exact C00001 membership request contains 6,059 vectors. The optimized
executable took 8.807 seconds with one thread and 3.287 seconds with 24 threads
(62.7% less wall time), including request parsing and result serialization.
All 24 numerical threads accumulated CPU time; they were confined to CPUs
0–23. One- and 24-thread outputs are byte-identical. This is one sequential
timing contrast under other host load, not an end-to-end construction estimate.

Compared with the original executable, the 676,422,679-byte saved output differs
only in its declared HDBSCAN and preprocessing implementation source hashes.
Replacing exactly those two old hash values with the new source hashes makes
every other output byte identical, including all numerical diagnostics,
groups, hierarchy links and scores. Old receipts are not rewritten.

The same frozen six-root checkpoint also passed the native structural audit
using process-based numerical validation. Audit contents matched the earlier
report exactly after excluding its trial path and source hashes. Wall time
was 95.438 seconds versus the earlier 514.106 seconds. Cache behavior,
coordinator implementation and host load differ, so this does not isolate a
multicore-only effect. Initial source rebinding took a separate 102.066 seconds.
No teacher requests were made for these checks.

Evidence remains ignored under `target/multicore-validation-replay-v1/`,
`target/multicore-numerical-replay-v1/` and
`target/multicore-numerical-replay-v2/` in
`oracle-mvp-hr35-multicore-replay-v1`. Native hierarchy regression verification
on local main passes 121 tests; the relevant Rust suite passes 50 tests.
