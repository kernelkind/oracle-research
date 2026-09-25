# Release-plan viewer

[Release decisions and open questions](release-decisions.md) records the planning
discussion, including corpus scope, validation, Vast.ai compute and rented hosting.
[Scalability findings and decisions](scalability.md) records the separate
read-only investigation, the low-memory HDBSCAN discussion and unapproved next steps.

`october-18-release.drawio` is the editable source. `index.html` displays it
read-only using draw.io's renderer. Refresh the browser after saving changes;
no export or copied preview is needed. The page fetches the source and renderer
from its own host only.

## Focusable graph prototype

Open [graph-prototype.html](graph-prototype.html) on the same tailnet host to try
an alternative, read-only dependency view. It reads the task cards and arrows
from the dependency page of `october-18-release.drawio` on every load; it does
not maintain another task list or change the draft plan. The current draw.io
viewer remains the baseline. Task statuses and wording mirror the diagram,
including any lag behind the written status checkpoint.

The prototype initially focuses on task 02. Choose another task or click a
node to refocus. Show zero to three steps in either or both directions, or
show all tasks. A `+N other links` label means the node has arrows not drawn in
the current view. The right panel always lists the selected task's direct links,
including those outside the view. Solid arrows mean prerequisites for finishing;
dashed arrows mean helpful inputs. Start conditions remain in task descriptions
because the existing diagram does not encode them separately. No user choice
or approval is inferred from a task's status.

The browser uses local copies of Cytoscape.js 3.34.3, ELK.js 0.12.0 and
cytoscape-elk 2.3.0; no external service or build step is needed. The bundles
come from their npm source tarballs:
[Cytoscape.js](https://registry.npmjs.org/cytoscape/-/cytoscape-3.34.3.tgz),
[ELK.js](https://registry.npmjs.org/elkjs/-/elkjs-0.12.0.tgz), and
[cytoscape-elk](https://registry.npmjs.org/cytoscape-elk/-/cytoscape-elk-2.3.0.tgz).
Their licenses are retained in `vendor/`.
SHA-256 (in that order):

```text
5f3b5b529546d5af1fc5628590af033b74511a5b6f789f5f4682845863228b91  cytoscape.min.js
1222e44f953ce7746af23801e723708f8e6f436b8b377a6a5fc7552f34a307b3  elk.bundled.js
25acbb9dea9b0dc6fef0e79b697547ee56e579f0e1c22ae4353131e72c7e140a  cytoscape-elk.js
```

The viewer opens in dark mode, including the diagram and page/zoom toolbar,
using the bundled renderer's native dark-mode setting. The diagram uses native
`light-dark()` color pairs: original light colors plus an explicit dark palette.
Lighter charcoal cards, off-white task text and visible borders distinguish tasks
from the canvas and subtly shaded workstreams. Green and blue status accents
remain; waiting tasks do not have dimmed body text. Completed cards alone use
muted fill, border and text while retaining readable titles. Layout and
dependency meanings are unchanged. No renderer patch or custom color-conversion
code is used.

Both pages open at a fixed overview zoom, equivalent to pressing Zoom Out three
times from 100%, rather than fitting to the window. Scroll to explore; the page
and zoom controls stay visible. Switching pages restores that default zoom and
starts at the top-left. **100%** restores full-size text. Cards and connector
captions have separate space; layout changes do not change task wording or
dependencies.

Each task's title and description must identify the work and intended result
without tracing arrows. Name the model's role—teacher or
the distilled model—rather than saying only “the model.” Arrows
explain prerequisites; they should not supply a task's missing meaning.

Only add approved decisions to the diagram. Permission to investigate or draft
a proposal does not approve its contents. Keep proposals in the written plan
until the user explicitly approves them for the diagram.
The overall plan remains unapproved; approving a card or wording change does
not approve the full plan. This discussion concerns planning, not implementation
choices or execution. No workstream or agent assignment starts without explicit
authorization.

Page 1 highlights readiness: green means ready to start or resume, blue means in progress,
grey means waiting, blocked or paused, and muted grey means complete. If preparation can start
but later work cannot, show them as separate nodes linked by a dependency—not
as one partly ready task. Node 18 is green for preparing training code for the
fine-tuning pilot: fine-tune each candidate, save/reload trained weights and
generate outputs for evaluation. Final training-example formatting and
mask/prominence evaluation remain in 06, after the agreed output format,
criteria and reviewed pilot data are available. The 05 + 18 dependencies on
06 are unchanged. Node 17 is blue and in progress: the user reports comparing
Muse high and Astra low. No teacher is selected. Task 17 also requires an A/B
comparison of the resulting hierarchies on the same notes before selection;
label quality alone is insufficient. Completing the comparison still requires
validated prompts (01 + 04); prominence remains unfinished. Comparison
planning is part of 17, not a separate task.
Node 01 is complete: the subject and mask prompts are finished. On September 24,
the user confirmed that the node-title prompt is finished. Node 23 is complete,
and all 129 HDBSCAN groups have saved v38/Luna max titles. Node 02 resumed with
user approval on September 25: local TRUE scoring is underway for all 16,512
directed pairs, reusing verified identical inputs. The historical HRv1 path
remains on v21. TRUE placement, merged naming and minimal-scope correctness
review remain. Its solid 23 → 02 arrow records a satisfied
prerequisite. A valid title response is not a user-approved title. Additional
rows expose the remaining construction work.
This second 100-post experiment is **HR02**: generate a hierarchy the user is
pleased with, not optimize cost, speed or teacher selection. This goal does not
authorize model changes or comparison runs; the architecture is unchanged.
A separately authorized Astra-low title pass is now complete: unchanged v38,
the same 129 groups, all outputs valid, seven agent-review flags. Adopting those
titles for TRUE remains pending; the existing Luna-title scoring run continues.
Node 04 (mask prominence) is grey and marked paused, reconfirmed by the user on
September 23. Earlier experimental work does not establish that it is active
now. Its mask-prompt prerequisite is satisfied. It need not wait for
the 100-note hierarchy or title correction. Its prompt and validation are not
complete. The user plans to revisit its open questions during the 100-note
build as the hierarchy becomes clearer; the exact point is open. The top
summary names only the green workstreams. Readiness
does not authorize research, implementation, agent assignment or spending.

Node 24 is ready but not started: recover missing memberships. Node 25 is ready
to resume: both merge stages and naming/browser integration are implemented
and checked offline, with a four-node live naming/UI check complete.
Full rebuilt-hierarchy validation remains.
The merge policy is provisional, not proven equivalence.
Node 26 is grey: its navigation collapse is
implemented and regression-tested; validation on the rebuilt hierarchy is
pending. It is not in the ready-to-start summary.
Node 27 turns mask prominence into node-note ordering and needs 04.
Task 25 is also required to finish the 100-note result in 02; TRUE work can
begin before 25 is complete. All four results are required to complete the
500-note validation in 03. The 100-note run checks correctness at minimal
scope. The 200-note run adds prominence-based note ordering; the 300-note run
tests scalable construction, including whether filtering retains useful TRUE
links; the 500-note run validates the combined pipeline and profiles its build.
Membership recovery does not expand the limited 100-note diagnostic. The
200-note construction can start while prominence is paused, but its ordering
check needs 04 and 27; 300-note work need not wait for that check. The
04 → 27 → 03 completion dependency is unchanged.
No membership algorithm, cycle-resolution method or ranking formula is selected.

The September 23 user checkpoint confirmed 17 in progress, 13 and 18 not
started, and 21–22 without further progress. Tasks 02 and 23 were updated on
September 24; the later planning correction adds 25 → 02 as a finish dependency.
Dates are unchanged. See the
[status record](release-decisions.md#status-checkpoint--september-24).

Node 28 is separate from scale measurements: turn the strategies tested in 03
into a runnable launch-scale build, including cosine-filtered TRUE and handling
large-group title inputs. It needs the validated larger-corpus workflow (03)
and findings from 21 and 22, and is required before completing full-build
feasibility (10).
The early assessment (20) does not wait for 28. Recovery measurements from 24
are a dashed input to 20; include graph-processing costs from the hierarchy
builds too. Neither measurement nor a planning card authorizes implementation.

Pilot 06 includes a small hierarchy built from pilot-model outputs before model
selection. Final-model verification in 11 remains required. The second page
lists these completion dependencies separately from week assignments; dates
have not changed.

Page 2 shows protocol, service and Notedeck work in a separate parallel track
alongside hierarchy and model development. Its cards show dependencies, not
new week assignments: service development can begin after the protocol;
testing with a saved hierarchy needs the 100-note snapshot as well;
Notedeck can start from the protocol, and integration needs the service. Launch
still needs the final snapshot. Exact start/completion dates remain open.

The fine-tuning pilot (06) informs the training-volume decision required to
complete the full training data (07). Its dashed arrow does not require the
whole pilot to finish before bulk generation can start. But 07 cannot start
until the 500-note hierarchy validation (03) succeeds and the teachers are
selected (17).
The pipeline note distinguishes training-label generation from applying
the distilled model to the final corpus.

Node 22 is ready to measure SSE, node-title and TRUE processing time, memory
and cost using existing masks and nodes, including title input growth as
groups grow. It does not wait for 21, which
assesses whether our HDBSCAN grouping can meet the intended corpus size, budget
and deadline, and identifies work required without presuming replacement.
Node 20 combines these findings with mask/prominence generation measurements
from pilot 06 and mask/node/cosine-filtered-pair counts from the growing
hierarchy builds. It estimates full-build resources to inform launch-corpus
selection (09), and stays grey pending inputs from 21 and 22. The dashed inputs
from 06 and 03 allow available evidence to inform the assessment without
requiring either workstream to finish first. Measurement procedures remain open.

Node 10 needs the working build from 28, not just stage estimates. It checks whether
generating launch-corpus masks and prominence with
the distilled model, then constructing the full hierarchy, fits the remaining time
and budget. Node 11 tests a sample hierarchy built from that model's outputs.
These are distinct checks: full-build feasibility and hierarchy quality. Both
are needed before building the launch snapshot (12), with no imposed 10 → 11
sequence. They may share measurements; how they do so belongs to execution.

Publication preparation is explicit within existing tasks: 06 checks permission
to release fine-tuned weights before model selection; 08 prepares and verifies
usable model files with usage instructions and evaluation results; 12 prepares
runnable hierarchy code, instructions, architecture and the continual-update
path. Node 16 publishes those prepared outputs. Preparation can accompany
development; final verification needs the actual release artifacts. This does
not add a training-dataset publication requirement or select publishing formats
or locations. See [publication preparation](release-decisions.md#publication-preparation).

## Diagram tooling decision — September 20, 2026

Keep draw.io and the existing viewer for now. Renderer replacement is deferred;
no alternative has been selected. Resume release planning, not tooling work.

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
coordinates or routing, preserve legibility and both planning pages, and produce
repeatable output. The tests do not guarantee every future graph will render well.
Detailed temporary evidence is in `/tmp/planning-mermaid-elk/` and
`/tmp/planning-beautiful-mermaid/`; those paths are not durable repository storage.

## Local access

From this directory, serve the planning files locally:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` in a browser on the same machine.

## Bundled renderer

`vendor/viewer-static.min.js` is the unmodified draw.io v31.4.6 bundle from:

<https://raw.githubusercontent.com/jgraph/drawio/v31.4.6/src/main/webapp/js/viewer-static.min.js>

SHA-256: `e49a0d5d1eac05351c3d21a22d5278fcab5d20066bdbdf074edc0b9989c611cd`

The upstream license is retained in `vendor/LICENSE.drawio`. Bundling the
renderer avoids sending the planning document to an external viewer service.

`tests/test_planning_viewer.py` checks the actual page in isolated headless
Firefox: rendering, page switching, read-only controls, local resource loads,
readable default scale, scrolling, visible page controls, card-text containment,
connector-label clearance, dark surfaces and readable diagram text on both pages,
card/background, border and text contrast, refreshing changed source, and a visible error for
missing source. It requires Firefox and Python's `websocket-client` package.
