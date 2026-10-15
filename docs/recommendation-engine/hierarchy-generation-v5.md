# HiGen V5 — recursive HDBSCAN construction

V5 is the default for new native hierarchy definitions. It implements the
approved recursive replacement process. Bootstrap-v133 supplies original L1
titles and explicit meanings. Grouped-consolidation-v1 names groups and broader
sections. Offline native-workflow tests cover construction and recovery.
The first matched-control run, [HR27](hierarchy-runs.md#hr27--hr21-controls-with-higen-v5),
completed with 22 nodes and 46/50 reachable notes; semantic quality remains
for review.

| Setting | V5 value |
| --- | --- |
| Frozen policy | `hierarchy-generation-v5` |
| HDBSCAN distance | Angular mutual reachability |
| `min_samples` | 3 |
| `min_cluster_size` | 2 |
| Group selection | Excess of mass |
| SSE input | Title, two newlines, explicit meaning; pool only title tokens |
| Maximum canonical siblings | 6 |
| Bootstrap | Hierarchy-bootstrap-v133 |
| Consolidation | Hierarchy-consolidated-grouped-v1 |

## Construction

Start with all non-null original L1 definitions. Run HDBSCAN and keep only
originally grouped entries as eligible inputs. Originally unassigned entries
stay excluded. Later unassigned inputs remain eligible and stay in the pool.

Project the condensed tree onto its selected groups. For more than six groups,
choose the positive bend in the middle 80% of distinct merge-distance levels,
then cut between that distance and the next smaller one. All tied merges split
together. These temporary sections may exceed six. If the bend is unavailable,
use V4's last cut before exceeding six sections. If a tied split makes that
impossible, select the six groups with the most distinct notes as leaves.
The remaining groups' notes stay directly on the parent. Below-line bends are
a future investigation; V5 does not select them by absolute deviation.

Select the largest section without an existing synthetic representative by
distinct supporting notes. Expand representatives to their original note
associations and deduplicate note IDs. Preserve saved section order for ties.
If all remaining sections fit the unused sibling slots, create all of them.

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
Keep notes from unclaimed eligible entries directly on the
parent, including the display container above the roots. Canonical nodes retain
all their supporting note associations, not just the notes left outside their
children. The existing viewer export includes root-container notes.

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
Set `generation_policy: hierarchy-generation-v5` explicitly for reproducibility;
omission selects V5 for new preparation. Optional `bootstrap_hierarchy` reuses a
matching saved Bootstrap-v133 checkpoint and original vectors.
Completed Bootstrap answers can be reused before encoding finishes; V5 reuses
completed encoder jobs and schedules the missing vectors normally. A longer
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

Historical V3/V4 definitions retain their frozen policies and settings on
resume. They do not acquire V5's algorithm or parameters. HR27 and V5's
version description are recorded in the hierarchy workbook.

## Experimental roots-only iterations

V5 definitions may freeze an optional `v5_options` object. Both supported
fields are booleans and default to false:

- `roots_only`: finish after the root lineup, without preparing children.
- `include_original_unassigned`: keep all non-null original entries eligible,
  including entries unassigned by the first root clustering. The first tree
  and root selection are unchanged; subsequent root pools retain those entries.

These controls support isolated chat iterations, not a new official HiGen
version or a change to V5 defaults. Bootstrap meanings and original vectors
can be reused through `bootstrap_hierarchy`; identical consolidation requests
still use native answer reuse. Reports must count distinct notes under the
actual roots separately from notes left outside those roots. Top-container
access does not establish root coverage. The user rejected treating direct
top-container notes as approved root placement; this iteration does not
resolve the final handling of root leftovers.
