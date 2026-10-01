# Release-plan task graph

[Release decisions and open questions](release-decisions.md) records the planning
discussion, including corpus scope, validation, Vast.ai compute and rented hosting.
[Scalability findings and decisions](scalability.md) records the separate
read-only investigation, the low-memory HDBSCAN discussion and unapproved next steps.

[Fine-tuning pilot process](fine-tuning-pilot-process.md) describes the experiment:
shared data, untuned baselines, training at increasing data sizes, evaluation,
and model comparison. Semantic review happens outside the GPU rental.

`release-plan.json` is the current task-and-dependency source for the focused
graph. Agents update it from explicitly approved planning changes; the user
does not need to edit it. Each task has a two-digit `id`, `title`, `status`,
`track`, and plain-text `description`. Links run from prerequisite `source` to
dependent `target`, with `kind` set to `required` (needed to finish) or `helpful` (an
input that does not block finishing); `label` is optional. The browser rejects
missing endpoints, duplicate IDs or links, and unknown statuses, tracks or
link kinds.
The written decision record remains the source for requirements, rationale,
approvals, and open questions. Task readiness is not authorization to begin.

The September 28 [release-shape revision](release-decisions.md#release-shape-revision--september-28-2026)
re-cut the deliverables: the release is the only must-deliver package — a
fully automated 2–5k-note snapshot with code and tested local serving
instructions. The open-weight model is the nice-to-have model track, and
operating the service is an optional demo. Task texts and statuses reflect
that revision.

Task 03 covers validation at 200 / 300 / 500 notes and the ~1–2k-note user-review
rung. Task 12 alone owns the final teacher-labeled, fully automated 2–5k build
and its user browsing review. Completion of 03 does not accept the release
snapshot; 12 requires the user's acceptance of that final snapshot.
Corpus preparation and Notedeck integration preparation are underway as of
September 30. Broader hierarchy tests and client implementation have not started;
their existing prerequisites and completion dependencies remain unchanged.

Whether HDBSCAN will be used remains open (September 29 clarification).
Task 21 is required only if the chosen workflow uses it. Its links to 20 and 28
are helpful while the choice is open; make them required if HDBSCAN is selected.
The chosen workflow's time and cost checks remain required. No algorithm is
selected by this tracking change.

Task 24's membership-recovery work is also required only if HDBSCAN is used.
Its link to 03 is helpful while the choice is open; make it required if HDBSCAN
is selected. Relevant-content coverage remains part of 03's required validation
for whichever workflow is used.

Task 23's completed title-prompt work is required for 02 only if the chosen
workflow uses separate node-title generation. Its link to 02 is helpful while
that choice is open; make it required if that stage is used. This does not
select a workflow or reopen the completed HR02 title work.

Task 25 remains complete for HR02. Its links to 02 and 03 have been removed:
the earlier exact-mask-set and TRUE-cycle rules do not gate the newer hierarchy.
Current merging and conflict decisions remain within 02; no replacement policy
is selected by this tracking change.

Task 26's earlier equal-note navigation collapse remains validation pending;
its link to 03 has been removed. Any reuse in the newer hierarchy needs an
explicit decision within 02. Understandable choices, meaningful narrowing and
relevant-content coverage remain required in 03, without mandating that rule.

Task 04 defines and validates the node sort score: one sorting score per note
within a hierarchy node. Prominence and relevance are candidate components,
not fixed requirements; the formula, inputs and any treatment of multiple masks
remain open. Task 27 implements and validates ordering using that definition.
Both remain in progress. The saved candidate matches the 11 clear
Coffee/Eggs/Music pair preferences, Photography's three-post order and the
accepted seven-post Eggs order. One Coffee comparison repeated successfully.
Either order is acceptable for the four about-equal Coffee pairs; identical
scores are not required. These selected reviews do not establish general
ordering quality. Broader-hierarchy validation and a production scoring method
remain open. The 04 → 27 → 03 completion
dependencies are unchanged. The sorting mechanism and any additional
teacher/model outputs it needs remain undecided; prominence outputs are not
required merely because earlier experiments used them.

Teacher comparison (17) remains in progress. Sol low is provisionally favored
for subject generation after assessment on 20 posts. Sol xhigh grouped masks
were assessed on 20 posts (684 masks), using saved Astra subjects. Agent reviews
found broadly comparable quality to Astra, with minor omissions and unresolved
cases; they do not establish corpus-wide parity or select teachers. The combined
Sol subject-and-mask process and resulting hierarchy comparison remain
unvalidated. Subscription quota use is unmeasured; mask and final teacher
selection stay open.

Task 22 measures SSE and the construction stages used in the chosen workflow.
Separate node-title generation, its input-growth measurements and the
corresponding large-input work in 28 are required only if that stage is used.
LG01 retains SP subject names; no production workflow is selected by this change.

Task 20 keeps separate estimates: teacher generation plus construction for the
required release, and pilot/distilled-model generation for the optional model
track. Shared construction measurements can inform both where applicable.
Model-track measurements do not block completing the release estimate. Checks
10 and 11 belong to the model track; neither blocks the teacher-built snapshot.

Task 02 tracks the SP-based hierarchy investigation on 100 posts. Later
authorized tests combined same-worded siblings, including Food preparation and
Food ingredients beneath Food, carried consistent saved judgments through
equivalences and completed two further bounded passes. The latest separate
test export has 1,740 hierarchy nodes; original subjects, masks and source
evidence remain represented. Food still reaches the same 50 posts.

The two existing pair-selection rules now find no unjudged pairs. That does
not establish complete parent relationships or browsing acceptance. Review
still includes links outside those rules, disconnected bagel-making/pie-making
branches, unresolved judgments such as the experimental Dietary practices /
Diets merge, and general conflict handling. Automatic repetition is not
implemented; further calls and production adoption remain unapproved.

The saved LG01 hierarchy is unchanged. Task 02 remains in progress until the
user accepts a useful 100-note hierarchy, not finished launch-scale construction.
Track and dependencies are unchanged. See the
[current stage record](../../sse_multivector/branch-comparison-prompt-v1/README.md#hierarchy-generation-stages).
Earlier HR02 results remain preserved, not the current next step.

Task 18 is complete for pilot setup. The rebuilt image is published and verified;
local VM rehearsals cover all three candidate families.

Task 29 tracks the preliminary 100-note fine-tuning experiment in progress. Its
replacement GPU run completed all three baseline attempts, 128-step training runs,
matching adapter reloads and trained evaluations. Results were hash-verified locally. The user requested accepting Markdown
JSON fences to recover the Gemma baselines. The parser now accepts them for
subjects and masks; all 40 saved Gemma subject answers validate, but their 618
baseline masks still need generation. Reparsed Qwen teacher-agreement F1 is
0.344 before and 0.346 after training. Semantic review remains pending; this does not complete candidate-quality review in 29 or model selection in the larger pilot, 06. That larger pilot remains waiting for its data and
includes a comparison trained on 1,000 notes, approved September 30. Remaining
data choices and execution details are open.

Task 13 remains in progress. The [protocol draft](../recommendation-engine/design/hierarchy-serving-protocol-decisions.md)
has restarted from how a client opens a hierarchy and currently contains only
that proposal, which awaits review. Node records, browsing requests/responses,
paths, ordered-note pagination and snapshot versions still need specification
and agreement. Service and Notedeck implementation remain dependent on the
protocol; integration preparation is already underway. Dependencies are unchanged.
This status correction selects no protocol design.

The task graph is the only release-plan viewer. The root URL opens it; the
obsolete draw.io diagram, viewer and renderer have been removed. Earlier
versions remain recoverable from Git, not as a competing planning view.

## Focused task graph

The track selector defaults to **Required release**. **Optional model** shows the
distillation work; **Both** includes the entire plan. Tasks marked **Shared**
appear in both track views as the same task, not duplicate records. Earlier
cycle/navigation experiments are marked **Historical experiment** and remain
accessible in Both, without becoming current prerequisites.

The `track` field is `release`, `model`, `shared`, or `historical`. It describes
which views include the task, not its readiness or dependency strength. Shared
HDBSCAN and separate-title work remains conditional on the chosen workflow.
Statuses, arrows, task scope and open method choices are unchanged.

Track selection filters the task picker and graph, including step expansion
and the all-matching view. It preserves the steps, direction and helpful-input
settings and composes with completed-task filtering. The details panel still
lists every direct link and labels tasks outside the selected track. Following
one switches to its track; Previous task restores the prior task and track.

Open [the planning root](index.html) on the tailnet host for the
read-only dependency view. It loads `release-plan.json` on every visit and
arranges the graph automatically. It does not change the draft plan.

ELK calculates both task positions and orthogonal connection routes. The viewer
uses those routes and attachment points so arrows entering a task remain
separate. Refocusing or changing filters recalculates the visible graph; no
task-specific coordinates are stored in the plan.

The graph initially focuses on task 02. Choose another task or click a
node to refocus. Show zero to three steps in either or both directions, or
show all tasks. A `+N other links` label means the node has arrows not drawn in
the current view. The right panel always lists the selected task's direct links,
including those outside the view. Solid arrows mean prerequisites for finishing;
dashed arrows mean helpful inputs. Start conditions remain in task descriptions
because task links do not encode them separately. No user choice
or approval is inferred from a task's status.

The browser uses local copies of Cytoscape.js 3.34.3 and ELK.js 0.12.0;
no external service or build step is needed. The bundles come from their
npm source tarballs:
[Cytoscape.js](https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz),
[ELK.js](https://registry.npmjs.org/elkjs/-/elkjs-0.12.0.tgz).
Their licenses are retained in `vendor/`.
SHA-256 (in that order):

```text
5f3b5b529546d5af1fc5628590af033b74511a5b6f789f5f4682845863228b91  cytoscape.min.js
1222e44f953ce7746af23801e723708f8e6f436b8b377a6a5fc7552f34a307b3  elk.bundled.js
```

## Planning conventions

Each task's title and description must identify the work and intended result
without tracing arrows. Name the model's role—teachers or the distilled model—
rather than saying only “the model.” Arrows explain prerequisites; they should
not supply a task's missing meaning.

Only add approved decisions to the task data and views. Permission to
investigate or draft a proposal does not approve its contents. Keep proposals
in the written plan until the user explicitly approves them for the graph.
The overall plan remains unapproved; approving a card or wording change does
not approve the full plan. Task readiness is not authorization to research,
implement, assign agents or spend.

Green means ready to start or resume, blue means in progress, grey means waiting,
and muted grey means complete. If preparation can start but later work cannot,
show them as separate tasks linked by a dependency.

## Earlier diagram-tooling investigation — September 20, 2026

The September 20 decision kept draw.io while no replacement had been selected.
The later focused graph now uses Cytoscape and ELK with JSON task data. The
findings below explain why other renderers were not selected at that point;
they do not describe the current graph's data source.

Retain these findings for a future upgrade:

- Standard Mermaid 12.0.0 with bundled ELK passed six layout cases without a
  renderer patch, preserving text, statuses and dependencies. Repeated SVGs were
  identical with fixed inputs and environment. Global wrapping and label-background
  settings were sufficient, but the baseline used about 24% more canvas at the
  same font size than the visually accepted patched beautiful-mermaid result.
- beautiful-mermaid 1.1.3 damaged valid ELK routes in two later cosmetic passes.
  Skipping those passes fixed the tested cases, but required a code change;
  maintaining that patch has not been approved.
- Direct ELK reproduced the accepted geometry but would require owning the
  text-measurement and rendering layer. It was not built into a complete renderer.

A future replacement should accept task content and dependencies without manual
coordinates or routing, preserve legibility, and produce
repeatable output. The tests do not guarantee every future graph will render well.
Detailed temporary evidence is in `/tmp/planning-mermaid-elk/` and
`/tmp/planning-beautiful-mermaid/`; those paths are not durable repository storage.

## Local access

From this directory, serve the planning files locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` in a browser on the same machine.

## Browser verification

`tests/test_planning_graph_prototype.py` opens the planning root in isolated
headless Firefox and verifies rendering, focus and step expansion, track views,
cross-track navigation, completed-task filtering, live task-data refresh and
invalid-input errors. It also checks that
the obsolete draw.io files and navigation link are absent. The test requires
Firefox and Python's `websocket-client` package; it uses only local resources.
