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
reads have their own surrounding scope. Model receipt verdicts are not retained
across advancements. Numerical validation now has a separate run-scoped cache,
described below. Original receipt and bound-review checks remain in place.

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
and cuts. Successful numerical checks can now be reused within a run while
their evidence and controls remain unchanged, as described below. No model
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
passes 122 tests; the relevant Rust suite passes 50 tests.

Membership construction now also uses the numerical process workers, replacing
the thread pool. This includes request preparation and large JSON result
processing, which otherwise shares one Python GIL after the Rust jobs finish.
The same local CPU budget is divided across native clusterings. Sibling-order
collection and atomic membership application are preserved; failures retain
other completed results for resume.

A native test first recorded one shared parent process for all three sibling
jobs, then passed with three distinct worker parents. Concurrent-start and
failure/resume tests also pass. Reusing the six complete real root results
through the process-based production path took 10.758 seconds and returned
every saved round, request hash and result hash exactly, without another
clustering invocation or teacher call. This is a reuse-path check, not a fresh
construction benchmark. Evidence is retained under
`target/membership-process-checks/` in `oracle-mvp-hierarchy-hr35-results`.

### Observed costs at HR35 completion

HR35 completed on source `835f91dc` with the 24-CPU allocation and four CPUs
left for other work. Multicore execution did not remove all runtime costs.
One late advancement processing several lineups took 1,095.170 seconds.
After the first advancement returned `complete`, two further advancements of
the unchanged completed graph took 302.802 and 306.911 seconds. The coordinator
advances after collecting finished jobs and again after its loop; each call
checks the retained numerical evidence before and after collection. The
native timing log (original native evidence)
preserves these events. They are observations with different amounts of work,
not matched runtime comparisons.
Batches prepared during an advancement are submitted only after it returns,
so independent model work can wait behind the local checks.

Large diagnostic tables are still serialized into numerical outputs and fully
decoded before `_hierarchy_fields` retains the consumed fields. The saved
676,422,679-byte result and 2,036,262-byte retained view quantify that excess.
Worker processes also rebuild their read scopes for validation. The completed
run retained the unused output and repeated completed-state advancements;
the subsequent fixes are described below. The successful
kernel and replay measurements above do not establish an end-to-end speedup.

## Compact numerical output and unchanged-evidence validation

The user approved all three fixes: compact numerical output, reuse of successful
checks for unchanged evidence, and stopping advancement once construction is
complete. Generation policies, prompts, numerical parameters and membership
rules are unchanged. No model requests or hierarchy regeneration were required.

`fine-segmentation-candidate REQUEST.json --hierarchy-output` returns
`hdbscan-hierarchy-output-v1`. It retains selected groups, their condensed tree,
input/alias mappings and source/configuration metadata. The artifact builder
hashes the compact result directly; it does not first serialize the dense
distance table. The original full-output command remains supported. HiGen
requests compact output for newly computed rounds and accepts both formats.
A historical executable that rejects the new flag with its exact old usage
message falls back to its original command. Existing requests/results stay
unchanged. The compact-output benefit requires the updated executable;
continuations use the existing reviewed binary-upgrade mechanism.

Successful numerical checks are retained only inside the current source scope,
which spans one automatic construction run. Each identity includes frozen
source bindings and executable, numerical policy/configuration, sibling limit,
the round's inputs/groups/cases/unassigned entries/selection, vector references
and complete encoding-job records. Request, result, encoding config/request,
receipt and raw-vector files are checked by device, inode, size and nanosecond
modification/change times. New or changed dependencies trigger full validation;
files changed during validation are rejected. Only successful checks are
retained. Structural and model-receipt checks still run normally. A new process
or standalone operation starts empty, and the transition to `complete` performs
an independent full numerical validation before saving. Explicit audits outside
a running construction do not inherit its successful checks.

The coordinator drains remaining jobs and writes accounting after completion,
without another advancement. It also no longer performs an unconditional final
advancement after leaving its scheduling loop. Production-path tests cover
already-complete runs and completion while another submitted job is draining.

### Saved HR35 checks

Measurements use the exact 6,059-entry C00001 membership request, SHA-256
`03be56dc247c8d6674e59cab9789fbaf2b13999ff02de33b088be88554161de9`.
The same release binary ran full/compact/compact/full, with 24 threads on CPUs
0–23. These are two observations per format under ordinary host load.

| Measurement | Full output | Compact output | Reduction |
| --- | ---: | ---: | ---: |
| Output bytes | 676,422,678 | 2,621,160 | 99.61% |
| Mean command wall time | 3.205 s | 1.095 s | 65.83% |
| Mean command peak RSS | 1,910,392 KiB | 1,064,250 KiB | 44.29% |

All consumed result fields, including groups, tree, aliases and memberships,
match between formats and the original saved HR35 result. Compact response
identity and its result checksum differ intentionally. Output size differs
slightly from the earlier 2,036,262-byte reader projection because the complete
compact artifact also retains selected-output metadata and unassigned IDs.

The full saved HR35 state then passed production `check_state` with all 215
numerical rounds: 141.846 seconds. A second check of that unchanged state within
the same run scope passed in 2.793 seconds. Original source bindings and receipts
remain frozen; offline checking verifies those files while allowing the new
checkout to execute the check.
This measures initial full validation versus successful-check reuse, not a
matched old/new end-to-end generation. HR35's state SHA-256 remains
`aac564fa745ac4a1d753e3f96af0a8bfa56c9bafe9b751a992a8cd5f81d2dd79`.

Numerical comparison (original native evidence),
validation comparison (original native evidence)
and native compact-round check (original native evidence)
are retained in the task worktree with the original numerical outputs. The
native round used the identical request hash, returned identical groups and
unassigned entries, and passed the production result validator in 6.621 seconds
including vector loading, preparation and saved-result validation.

Final verification passes 130 Python and 27 Rust checks, including changed
results with restored modification times, altered vectors/rounds, fresh-scope
revalidation, historical-binary fallback and completion while jobs drain.
An initial 129-test Python run had one extra-backoff-count failure in an
existing runner-outage test; its isolated rerun and final full 130-test run
passed. Retry policy was not changed. No
end-to-end hierarchy runtime, semantic-quality or model-cost improvement is
claimed from these component measurements. The existing HR35 review UI and
718-note coverage are unchanged.


## Selected performance results

The [bundle catalog](../publications.csv) includes these exact measured outputs:

| Measurement | Bundle |
| --- | --- |
| Full versus compact numerical output | `numerical/performance-14d5a2332fd69bf3` |
| Native parallel-membership equivalence | `numerical/performance-43300c0d64d62822` |
| Full validation versus unchanged-evidence reuse | `numerical/performance-9185acbe0dac3c95` |
| Compact native-round check | `numerical/performance-e44d338db0c16322` |

Restore them using the [dataset guide](../reproduce.md#verify-and-restore-the-dataset).
The original timing logs and receipt directories are not reconstructed by those
compact reports. They retain the final measurements and their scientific scope.
