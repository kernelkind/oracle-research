# Continue manual section replacement to six roots

Status: authorized experimental continuation, not an activated HiGen version.
The user requested continuing the same process until six roots exist, then
observing that result before settling complete-coverage or sixth-root rules.
The protected `MY-NOTES_10-12.md` is read-only and remains unedited.

Start from the [completed S10 replacement](food-drink-s10-synthetic-grouped-v1.md):
217 inputs, two retained synthetic roots, 39 HDBSCAN groups and 32 sections.
S07 contains the second synthetic root and four mental-state entries; it amends
root 2. S04 is the proposed third root, subject to the intervening rerun.

The user tentatively approved this round rule after Slot2v2 grouped with People
and related entries. Freeze one clustering and choose its largest section
without an existing synthetic root as the next new root. Also amend existing
roots that grouped with new entries in that clustering. Count distinct
supporting notes, expand synthetic nodes to original support, and use saved
section order for ties. Existing-root amendments do not occupy another slot.

The new-root and amendment definitions use disjoint sections of that same saved
pool, so their ready model batches can run concurrently. Validate all results,
apply the selected disjoint replacements together, encode only missing vectors,
then recluster. Stop after a completed round retains six synthetic roots. This
is a provisional experiment rule, not an assertion of complete coverage of
eligible notes or local entries.

Keep originally grouped inputs, even if a later run leaves them unassigned.
Exclude the 361 originally unassigned entries throughout. Preserve all original
associations, fixed definitions, native receipts and reused SSE vectors. An
unassigned synthetic root remains a root and a clustering input.

Use unchanged Hierarchy-consolidated-grouped-v1 and GPT-6.1 Sol medium through
the shared runner. For multiple groups, reuse exact native group definitions,
generate only missing group definitions, then consolidate those definitions.
For a one-group section, its group consolidation is already the root definition;
do not send an unnecessary one-definition consolidation. An exact existing
native group result can directly supply this replacement with its original
receipt and validated current membership, without a model call.

The replacement CLI's `roots` command exports retained roots separately from
current clustering assignments, with original support, distinct-note coverage,
and root-slot amendment history. Its SVG and full-definition Markdown do not
omit a root merely because HDBSCAN currently leaves it unassigned. These are
experimental views, not a refresh of the hierarchy UI or an official HR run.

The offline `sse_multivector.hdbscan_root_round prepare DIRECTORY --source FILE`
validates native section results sharing one exact frozen review and rejects
overlapping membership before creating the new pool. Its source contains
`schema_version: 1`, `replacement_review`, and a `proposals` array of native
`experiment`/`case` references. A proposal's optional `section` identifies an
exact saved original group reused directly in the current review. Each change
retains its producer receipt, removed inputs, original support and amendment
history. Model execution stays in the shared runner.

The initial continuation uses the isolated worktree
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-six-roots-v1`.
Its frozen model bindings remain unchanged. Round-support source work and later
runs use `oracle-mvp-food-drink-six-roots-rounds-v1` under the same directory.
Retain both worktrees' ignored `target/food-drink-six-roots-v1` evidence and their
referenced sources. Native usage summaries distinguish fresh calls from exact
saved definitions; API-equivalent cost is not an incremental subscription bill.
