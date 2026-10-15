# HiGen V5.2 — recursive HDBSCAN construction

V5.2 is the default for new native hierarchy definitions. At every level, it
ranks sections by distinct notes not already covered by existing siblings in
that lineup. V5.1 ranked by total distinct notes. V5.2 retains V5.1's eligibility
rule: entries left unassigned by the first root clustering remain available for
subsequent root rounds.
Historical V5 excludes those entries unless its experimental eligibility
option was explicitly enabled. The recursive replacement process, prompts,
clustering parameters, cuts and stopping rules are otherwise unchanged. V5.2's
ranking is checked offline; no full V5.2 hierarchy has been generated yet.
Bootstrap-v133 supplies original L1
titles and explicit meanings. Consolidated-grouped-v1 names groups and broader
sections. Offline native-workflow tests cover construction and recovery.
The first V5 matched-control run, [HR27](hierarchy-runs.md#hr27--hr21-controls-with-higen-v5),
completed with 22 nodes and 46/50 reachable notes; semantic quality remains
for review. The first full V5.1 run, [HR31](hierarchy-runs.md#hr31--hr28-corpus-with-higen-v51),
completed on HR28’s exact corpus with 72 nodes and all 100 notes beneath its six
roots, compared with 87 under HR28’s roots. Its checked review UI is available;
this coverage result does not establish semantic approval.
On HR29’s 200-note corpus, [HR32](hierarchy-runs.md#hr32--hr29-corpus-with-higen-v51)
completed with 70 nodes and all 200 notes accessible, but only 176 beneath
actual roots and 24 top-only. Retaining initial noise does not guarantee root
coverage or a monotonic improvement over V5’s 177 notes beneath roots.

| Setting | V5.2 value |
| --- | --- |
| Frozen policy | `hierarchy-generation-v5.2` |
| Section ranking | Distinct notes not already covered by existing siblings in the same lineup |
| Original root eligibility | All non-null original L1 definitions, including initially unassigned entries |
| HDBSCAN distance | Angular mutual reachability |
| `min_samples` | 3 |
| `min_cluster_size` | 2 |
| Group selection | Excess of mass |
| SSE input | Title, two newlines, explicit meaning; pool only title tokens |
| Maximum canonical siblings | 6 |
| Bootstrap | Hierarchy-bootstrap-v133 |
| Consolidation | Hierarchy-consolidated-grouped-v1 |

## Construction

Start with all non-null original L1 definitions. Run HDBSCAN and retain all
of those entries as eligible inputs. Entries left unassigned by this first
clustering stay in the pool while subsequent roots are constructed. They may
become grouped in a later round; they do not become canonical nodes merely
because they were retained. Later unassigned inputs likewise stay in the pool.

Project the condensed tree onto its selected groups. For more than six groups,
choose the positive bend in the middle 80% of distinct merge-distance levels,
then cut between that distance and the next smaller one. All tied merges split
together. These temporary sections may exceed six. If the bend is unavailable,
use V4's last cut before exceeding six sections. If a tied split makes that
impossible, select groups as leaves using the same note ranking below, up to
the remaining sibling slots.
The remaining groups' notes stay directly on the parent. Below-line bends are
a future investigation; V5 versions do not select them by absolute deviation.

Select the section without an existing synthetic representative that adds the
most distinct notes not already covered by existing siblings. Expand the
representatives in the current frozen round to their original note associations
and deduplicate note IDs, including representatives left unassigned by HDBSCAN.
Subtract that union from each available section's distinct supporting notes.
Apply this rule both at the roots and within each parent's child lineup;
coverage in unrelated branches does not reduce a child section's score.
Preserve saved section order when uncovered-note counts tie. V5 and V5.1 retain
their original total-note ranking.
If all remaining sections fit the unused sibling slots, create all of them.

The HR32 inspection motivating V5.2 found two available 33-note sections for the
last root: Human life added two notes not under the existing five roots, while
the coffee/drinks section added ten. V5.1 selected Human life by saved order.
V5.2 selects the coffee/drinks section on that frozen round; this is an offline
selection check, not a regenerated hierarchy or proof of overall quality.

Generate each selected group's title and meaning from its member definitions.
Generate the canonical section's definition from those group definitions,
never directly from original L1 definitions. A one-group section reuses its
group definition without another one-input model request. Supply the enclosing
canonical parent's title and fixed meaning on requests below the roots.

A synthetic input remains associated with its canonical node. When its section
acquires new entries, amend that same node and retain its version history.
Replace the represented inputs with the new synthetic definition, encode only
missing vectors, and recluster. Prepare disjoint amendments and new nodes from
the same frozen round together. Do not merge existing canonical nodes merely
because their representatives cluster together. Such sections are reported in
`conflicting_sections`; their representatives remain in the pool and other
sections can still advance. Unclaimed original notes remain on the parent.

Finish the lineup at six children, when only existing representatives remain,
or when its sections provide no further new node or amendment. Do not encode
or recluster a finished lineup merely to regroup existing representatives.
The constructor keeps notes from unclaimed eligible entries directly on the
parent. At root level, those associations remain in the saved state's
`direct_note_ids`; they are not approved root placement. Retaining eligible
entries and ranking uncovered notes do not guarantee that every note will be
assigned to a root.
Canonical nodes retain all their supporting note associations, not just the
notes left outside their children.

New review exports give the display-only top container no direct notes and
include only notes represented beneath canonical roots. Notes outside children
remain available inside canonical nodes. This is a review-export rule: it does
not alter construction, canonical memberships or saved hierarchy evidence.
Historical exports may still expose top-container notes; their recorded coverage
remains historical evidence.

## Children and stopping

After the entire sibling lineup finishes, descend into its final nodes.
An unamended node with two through six assigned groups exposes those named
groups directly as leaf nodes. A one-group canonical node is already a leaf.
Leaf groups expose notes, without expanding into original L1 or local L2 nodes.

For further section construction, build a fresh HDBSCAN tree from that node's
accumulated original entries, including amendments. Never use its own synthetic
representative as a substitute for those entries or splice earlier trees
together. An amended node takes this fresh-tree path so its latest group
containing the representative cannot replace its earlier internal entries.
Repeat the same selection, consolidation and replacement process recursively.
If local clustering leaves entries unassigned, their notes remain on the parent.

## Native workflow

Use the ordinary `prepare-hierarchy`, `advance-hierarchy` and `run-hierarchy`
commands through the shared stable launcher from a task worktree. The schema-1
definition supplies `corpus`, ordered `note_ids`, `local_schema_version: 4`,
`bootstrap_spec`, `consolidation_spec`, `worker_config` and `hdbscan_binary`.
Set `generation_policy: hierarchy-generation-v5.2` explicitly for reproducibility;
omission selects V5.2 for new preparation. Optional `bootstrap_hierarchy` reuses a
matching saved Bootstrap-v133 checkpoint and original vectors.
Completed Bootstrap answers can be reused before encoding finishes. V5 versions
reuse completed encoder jobs and schedule the missing vectors normally. A longer
client timeout is also compatible with completed Bootstrap reuse when every
other input and control matches. Original producer receipts retain their actual
timeout. HR30 sets one-hour timeouts for new Bootstrap and consolidation requests.

A valid null Bootstrap answer is skipped and reported in `skipped_bootstrap`.
If it is a note's only topic, that note is reported in
`notes_not_in_hierarchy`; it does not block the other notes. The complete input
inventory and null answer remain evidence. Construction remains blocked when
no original topic has a usable meaning.

Ready definitions for each enclosing canonical parent form independent native
batches, so one branch can advance while another batch is running. Every ready
batch is submitted immediately; the shared runner owns provider concurrency,
exact answer reuse, usage and retry limits. Original and synthetic
vectors reuse identical text/span identities. Definitions preserve native
producer receipts and stage provenance. Atomic advancement validates saved
trees, cuts, original eligibility, replacement ownership, canonical versions,
parent fields and direct note associations before saving state. Local advancement runs in the existing coordinator, retaining a bounded compact
view of unchanged HDBSCAN evidence between steps. The raw files remain unchanged;
whole-file hashes and all membership, tree, cut and graph checks still run.
Unused distance matrices and numerical diagnostics are excluded from the read
cache. Binary vector reads expand only requested rows into Python floats.
`advance-timings.jsonl` records actual advancement durations and recovery mode.

Transient advancement failures retry through the fresh shared CLI and its
existing exponential backoff, so a repaired runner can be loaded. Teacher
execution keeps that fresh CLI path. No outer coordinator or provider cap is
introduced.

Historical definitions retain their frozen policies and settings on resume.
They do not acquire a later version's eligibility or ranking rules. HR27 and V5's
version description are recorded in the hierarchy workbook.

## Experimental roots-only iterations

V5 through V5.2 definitions may freeze an optional `v5_options` object. Both supported
fields are booleans:

- `roots_only`: finish after the root lineup, without preparing children;
  defaults to false. All V5 versions normally construct the full recursive hierarchy.
- `include_original_unassigned`: keep all non-null original entries eligible,
  including entries unassigned by the first root clustering. The first tree
  and root selection are unchanged; subsequent root pools retain those entries.
  This legacy trial option defaults to false in V5. V5.1 and V5.2 always retain those
  entries without an option and reject an explicit false override.

The user adopted the eligibility change as V5.1 after roots-only chat trials.
Those saved trial states remain labeled V5 with their experimental options;
they are not relabeled official hierarchy experiments. Bootstrap meanings and
original vectors can be reused through `bootstrap_hierarchy`; identical consolidation requests
still use native answer reuse. Reports must count distinct notes under the
actual roots separately from notes left outside those roots. Top-container
access does not establish root coverage. The user rejected treating direct
top-container notes as approved root placement; this iteration does not
resolve the final handling of root leftovers.

The [50-note trial](../../../oracle-mvp-hierarchy-fifty-roots-ungrouped-v1/target/fifty-roots-include-ungrouped-v1/roots/state.json)
increased actual-root coverage from 46 to 50 notes. The
[HR28-corpus trial](../../../oracle-mvp-hierarchy-hr28-roots-ungrouped-v1/target/hr28-roots-include-ungrouped-v1/roots/state.json)
increased it from 87 to 100. Both reused the baseline Bootstrap meanings and
original vectors. Consolidation was sampled again: one-hour client deadlines
prevented reuse of older shorter-deadline requests. These are observed chat
iteration results, not a controlled causal estimate or semantic certification.
Very broad generated headings remain a quality concern.
