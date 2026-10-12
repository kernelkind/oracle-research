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
