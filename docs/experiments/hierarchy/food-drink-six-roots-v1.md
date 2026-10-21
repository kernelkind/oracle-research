# Continue manual section replacement to six roots

Status: completed six-root experiment, stopped at the requested observation
point; not an activated HiGen version.
The user requested continuing the same process until six roots exist, then
observing that result before settling complete-coverage or sixth-root rules.

The later recursive algorithm is documented in [HiGen V5.3](../../design/hierarchy-generation.md).
This manual precursor generated six roots without recursive children.

## Starting evidence and round construction

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
Their original source identities remain bound to the saved evidence. Native usage summaries distinguish fresh calls from exact
saved definitions; API-equivalent cost is not an incremental subscription bill.

## Completed six-root snapshot

All four growth rounds completed. Slot2v2 was established first from the four
mental-state additions. The first growth round created Nostr and amended slot 2
with the ten People/Humans entries; the second created Coffee; the third created
Biology and daily life and amended Coffee; the fourth created Cognition and
expression and amended the first root. No deeper canonical level was generated.

| Slot | Version | Final title | Distinct notes | Original entries |
|---|---:|---|---:|---:|
| 1 | 2 | Food and Domestic Life | 58 | 117 |
| 2 | 3 | Humans and human life | 34 | 53 |
| 3 | 1 | Nostr ecosystem | 24 | 26 |
| 4 | 2 | Biological products and beverages | 29 | 38 |
| 5 | 1 | Biology and daily life | 21 | 28 |
| 6 | 1 | Cognition and expression | 20 | 26 |

Note counts overlap. The six roots together represent **89 of 94 eligible
notes**, with **288 of 367 originally grouped entries** associated with a root.
The remaining **79 original entries**, including five eligible notes absent
from all roots, remain in the input pool. All 367 original associations are
preserved exactly across roots plus remaining entries; the original 361
unassigned entries stay excluded. The source corpus contains 100 notes; the
original grouped-only inclusion rule makes 94 eligible for this experiment.
Reaching six roots therefore did not complete either note or entry coverage.

| Checkpoint | Input vectors | Selected groups | Sections | Epsilon | Notes under retained roots |
|---|---:|---:|---:|---:|---:|
| S10 starting point | 217 | 39 | 32 | 0.942519 | 71 |
| Slot2v2 amendment | 213 | 38 | 31 | 0.942519 | 73 |
| Round 1: three roots | 178 | 35 | 29 | 0.942519 | 76 |
| Round 2: four roots | 153 | 32 | 20 | 1.093721 | 82 |
| Round 3: five roots | 114 | 24 | 15 | 1.144814 | 86 |
| Round 4: six roots | 85 | 18 | 5 | 1.288263 | 89 |

The six retained roots and latest clustering are separate views. In the final
clustering G09 contains roots 1, 2 and 5, and S01 contains fourteen selected
groups. Roots 3, 4 and 6 are currently unassigned by HDBSCAN but remain accepted
roots and clustering inputs. This is not a semantic equivalence or containment
judgment. The selected epsilon increased as the pool changed; no isolated
experiment establishes which change caused the broader sections.

The names and scopes also broadened during construction. For example, Coffee
beverages became Biological products and beverages after joining tea,
tomatoes/tallow and drinking-related entries. Biology and daily life came from
chicken/egg and breakfast/morning/sleep groups. Preserve these actual outcomes
for review rather than silently substituting different groups or definitions.

## Actual cost and verification

The native `usage-final.json` summary covers the Slot2v2 amendment and four new
growth rounds: **10 fresh attempts, 10 valid results, zero failures, retries,
warmups or missing usages**. All use unchanged grouped-v1/Sol 6.1 medium.
There are 18,223 input tokens, zero cache reads/writes, and 6,094 output tokens
including 4,249 reasoning tokens. Fresh API-equivalent catalog cost is
**$0.097386**; incremental subscription cash charge is zero.

Seventeen distinct native original group definitions are reused as inputs.
These are source references, not seventeen reused dispatch cases; the runner's
case-reuse count is zero. Their historical costs, original Bootstrap work and
earlier S05/S10 calls are outside the fresh subtotal. Eight synthetic vectors
are newly encoded across five SSE jobs; retained input vectors are reused.
This is not a matched end-hierarchy quality or operational-savings comparison.