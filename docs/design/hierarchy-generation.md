# HiGen V5.3 — recursive HDBSCAN construction

See [Generate a hierarchy](../generate-hierarchy.md) for environment setup,
portable configurations and the complete workflow from your own posts to browsing.

V5.3 is the default for new native hierarchy definitions. After each sibling
lineup finishes, it runs the additional membership clustering described below,
using global untracked original entries. V5.2 retains its frozen behavior without
this pass. At every level, V5.2 and V5.3 rank sections by distinct notes not
already covered by existing siblings in that lineup. V5.1 ranked by total
distinct notes. V5.2 and V5.3 retain V5.1's eligibility
rule: entries left unassigned by the first root clustering remain available for
subsequent root rounds.
Historical V5 excludes those entries unless its experimental eligibility
option was explicitly enabled. The recursive replacement process, prompts,
clustering parameters, cuts and stopping rules are otherwise unchanged. Recorded comparisons and semantic findings for V5 through V5.3 are in the
[official runs](../experiments/hierarchy/runs.md). Coverage gains did not by
themselves establish semantic quality. Bootstrap-v133 supplies original L1 titles
and explicit meanings; Consolidated-grouped-v1 names groups and broader sections.

| Setting | V5.3 value |
| --- | --- |
| Frozen policy | `hierarchy-generation-v5.3` |
| Section ranking | Distinct notes not already covered by existing siblings in the same lineup |
| Original root eligibility | All non-null original L1 definitions, including initially unassigned entries |
| After each sibling lineup | Add global untracked entries sharing an HDBSCAN group with a sibling's existing original members |
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

After the entire sibling lineup and its membership pass finish, descend into
its final nodes. An unamended node with no membership additions and two through
six assigned groups exposes those named
groups directly as leaf nodes. A one-group canonical node is already a leaf.
Leaf groups expose notes, without expanding into original L1 or local L2 nodes.

For further section construction, build a fresh HDBSCAN tree from that node's
accumulated original entries, including amendments. Never use its own synthetic
representative as a substitute for those entries or splice earlier trees
together. An amended node takes this fresh-tree path so its latest group
containing the representative cannot replace its earlier internal entries.
Repeat the same selection, consolidation and replacement process recursively.
If local clustering leaves entries unassigned, their notes remain on the parent.

## Approved membership additions after a sibling lineup

Implemented in V5.3; frozen V5 through V5.2 runs keep their original behavior.

After completing a sibling lineup, run an additional HDBSCAN clustering for
each canonical node in that lineup. Its inputs are that node's accumulated
original local entries, including amendments, plus the global untracked original
entries. Global untracked means entries not belonging to any canonical node in
the hierarchy; it is not limited to leftovers from the current parent's local
pool. These entries may already belong to HDBSCAN groups that were never added
to a canonical node. Freeze the same global pool for every sibling in this
pass, so an entry matching several siblings can join each one.

When a selected HDBSCAN group contains both an existing original member of the
current canonical node and a global untracked entry, add that untracked entry
to the current node's membership. A group containing only untracked entries
does not establish an addition. A connection higher in the HDBSCAN tree is not
the shared-group criterion. Use original entries rather than synthetic
representatives, without a bend cut for this additional clustering.

Apply this after root lineups and non-root sibling lineups, before constructing
their children. Preserve every existing membership, including when an existing
member becomes ungrouped in the additional clustering. The pass adds no teacher
calls or encodings: it uses saved original vectors. It does not regenerate
canonical titles, meanings or their original producer evidence.

Record the frozen global pool, canonical item snapshot, per-node HDBSCAN
requests/results and exact additions in `v5.membership_passes`. Canonical
`original_ids` and `entries` include the additions; the original construction
items and version histories remain unchanged. Ancestors reach the added notes
through their descendant relationships. A node requiring further subdivision
starts its child tree from its expanded membership.

Checkpoint the validated snapshot before clustering. Resume a pending pass
before advancing other lineups, reuse completed clustering results, and apply
all siblings' additions together. A failed or interrupted pass preserves its
inputs rather than rebuilding them from a later global pool. Native validation
reproduces every addition from its shared-group evidence.

Independent sibling membership clusterings run concurrently on local CPUs,
using the same frozen pool and separate output directories. Request preparation,
clustering, and large-result parsing/writing run in separate worker processes,
so Python's GIL does not serialize siblings' result handling. Results are
collected in sibling order and applied together. A failed sibling preserves
other completed results for resume. This local concurrency does not limit
teacher submissions or change the shared runner's provider queue.
The local CPU budget is divided across simultaneous membership jobs, rather
than allocating the full budget to each job. `run-hierarchy --cpu-workers 24`
uses at most 24 available CPUs; its default leaves four available CPUs for
other work. On Linux the coordinator and newly started children inherit the
limited CPU affinity. Independent saved numerical checks use worker processes
for large inputs, preserving all request, result, group and cut checks. Small
inputs are checked inline.

## Native workflow

Use the ordinary `prepare-hierarchy`, `advance-hierarchy` and `run-hierarchy`
commands through the shared runner. The schema-1
definition supplies `corpus`, ordered `note_ids`, `local_schema_version: 4`,
`bootstrap_spec`, `consolidation_spec`, `worker_config` and `hdbscan_binary`.
Set `generation_policy: hierarchy-generation-v5.3` explicitly for reproducibility;
omission selects V5.3 for new preparation. Optional `bootstrap_hierarchy` reuses a
matching saved Bootstrap-v133 checkpoint and original vectors.
Completed Bootstrap answers can be reused before encoding finishes. V5 versions
reuse completed encoder jobs and schedule the missing vectors normally. A longer
client timeout is also compatible with completed Bootstrap reuse when every
other input and control matches. Original producer receipts retain their actual
timeout. HR30 sets one-hour timeouts for new Bootstrap and consolidation requests.

A valid empty AS subject list remains in the frozen note inventory, produces
no Bootstrap request and is reported in `notes_without_original_l1s`. HDBSCAN
construction continues from the other notes; an input with no original L1
subjects fails before preparing teacher calls. Nonempty malformed local trees
remain invalid. Structural audits count the complete frozen input-note inventory,
including empty-subject notes, when reporting coverage.

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
The coordinator and standalone advancement retain up to 1 GiB of compact
serialized HDBSCAN views, releasing them when their scope ends. This is a
retention budget, not a process-memory limit. The current multicore runtime
requires shared runner commit `38561fe` or later, including the configurable
reader limit from `132a0cd`; ordinary receipt readers keep their 16 MiB default.

Transient advancement failures retry through the fresh shared CLI and its
existing exponential backoff, so a repaired runner can be loaded. Teacher
execution keeps that fresh CLI path. No outer coordinator or provider cap is
introduced.

Historical definitions retain their frozen policies and settings on resume.
They do not acquire a later version's eligibility or ranking rules. HR27 and V5's
version description are recorded in the hierarchy workbook.
An explicitly reviewed numerical executable replacement uses
`run-hierarchy --hdbscan-binary PATH --runner-upgrade-reason REASON`. Source
upgrades record its old and new paths and hashes and the unchanged graph hash;
both executables remain source-bound. Existing numerical results are reused.
Exact-output verification is required before adopting a runtime replacement.

## Experimental roots-only iterations

V5 through V5.3 definitions may freeze an optional `v5_options` object. Both supported
fields are booleans:

- `roots_only`: finish after the root lineup, without preparing children;
  defaults to false. All V5 versions normally construct the full recursive hierarchy.
- `include_original_unassigned`: keep all non-null original entries eligible,
  including entries unassigned by the first root clustering. The first tree
  and root selection are unchanged; subsequent root pools retain those entries.
  This legacy trial option defaults to false in V5. V5.1 through V5.3 always retain those
  entries without an option and reject an explicit false override.

The [roots-only eligibility checks](../experiments/hierarchy/runs.md#roots-only-eligibility-checks)
record the earlier observations and their limits. These options do not establish
semantic quality or approve unclaimed notes as root placement.
