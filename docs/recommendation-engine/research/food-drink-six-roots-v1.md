# Continue manual section replacement to six roots

Status: authorized experimental continuation, not an activated HiGen version.
The user requested continuing the same process until six roots exist, then
observing that result before settling complete-coverage or sixth-root rules.
The protected `MY-NOTES_10-12.md` is read-only and remains unedited.

Start from the [completed S10 replacement](food-drink-s10-synthetic-grouped-v1.md):
217 inputs, two retained synthetic roots, 39 HDBSCAN groups and 32 sections.
S07 contains the second synthetic root and four mental-state entries; it amends
root 2. S04 is the proposed third root, subject to the intervening rerun.

Keep the largest-section rule used in these trials: count distinct supporting
notes, expand synthetic nodes to original support, and use saved section order
for ties. A selected section containing an existing synthetic root amends that
root; one without an existing synthetic root creates another root. Recluster
after each replacement. Stop this trial when six synthetic roots are retained;
this does not assert coverage of every eligible note or local entry.

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

Source-changing work and all new runs use the isolated worktree
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-drink-six-roots-v1`.
Retain its ignored `target/food-drink-six-roots-v1` evidence and referenced source
worktrees. Native usage summaries distinguish fresh calls from exact saved
definitions; API-equivalent cost is not an incremental subscription bill.
