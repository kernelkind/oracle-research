# Release-plan viewer

[Release decisions and open questions](release-decisions.md) records the planning
discussion, including corpus scope, validation, Vast.ai compute and rented hosting.
[Scalability findings and decisions](scalability.md) records the separate
read-only investigation, the low-memory HDBSCAN discussion and unapproved next steps.

`october-18-release.drawio` is the editable source. `index.html` displays it
read-only using draw.io's renderer. Refresh the browser after saving changes;
no export or copied preview is needed. The page fetches the source and renderer
from its own host only.

The viewer opens in dark mode, including the diagram and page/zoom toolbar,
using the bundled renderer's native dark-mode setting. The diagram uses native
`light-dark()` color pairs: original light colors plus an explicit dark palette.
Lighter charcoal cards, off-white task text and visible borders distinguish tasks
from the canvas and subtly shaded workstreams. Green and blue status accents
remain; waiting tasks do not have dimmed body text. Layout, content and dependency
meanings are unchanged. No renderer patch or custom color-conversion code is used.

Both pages open at readable size instead of shrinking the entire diagram to
fit the window. Scroll horizontally and vertically to explore; the page and
zoom controls stay visible. Switching pages starts at the top-left. Zoom out
for an overview; **100%** restores readable size. Cards and connector captions
have separate space; layout changes do not change task wording or dependencies.

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

Page 1 highlights readiness: green means ready to start, blue means in progress,
and grey means waiting, blocked, paused or complete, as labeled. If preparation can start
but later work cannot, show them as separate nodes linked by a dependency—not
as one partly ready task. Node 18 is green for preparing training code for the
fine-tuning pilot: fine-tune each candidate, save/reload trained weights and
generate outputs for evaluation. Final training-example formatting and
mask/prominence evaluation remain in 06, after the agreed output format,
criteria and reviewed pilot data are available. The 05 + 18 dependencies on
06 are unchanged. Node 17 is blue and in progress: the user reports comparing
Muse high and Astra low. No teacher is selected. Completing the
comparison still requires validated prompts (01 + 04); prominence remains
unfinished. Comparison planning is part of 17, not a separate task.
Node 01 is complete: the subject and mask prompts are finished, as confirmed by
the user on September 20. On September 21, the user reported the 100-note build
blocked by an inadequate node-title prompt. Node 02 is grey and marked
blocked: TRUE needs accurate node titles for placement. Hierarchy
review and validation remain pending. Node 23, fixing and validating the
node-title prompt, is blue and in progress, confirmed by the user. Its solid
arrow to 02 makes the blocking work explicit; this does not reopen the subject
or mask prompts. Additional rows expose the remaining construction work;
lower lanes and connector routes have space for these additions.
Node 04 (mask prominence) is grey and marked paused, reconfirmed by the user on
September 23. Earlier experimental work does not establish that it is active
now. Its mask-prompt prerequisite is satisfied. It need not wait for
the 100-note hierarchy or title correction. Its prompt and validation are not
complete. The top summary names only the green workstreams. Readiness
does not authorize research, implementation, agent assignment or spending.

Nodes 24–25 are ready but not started: recover missing memberships and handle
node equivalence and TRUE cycles. Node 26 is grey: its navigation collapse is
implemented and regression-tested; validation on the rebuilt hierarchy is
pending. It is not in the ready-to-start summary.
Node 27 turns mask prominence into node-note ordering and needs 04.
These four results are required to complete the 500-note validation in 03;
they do not expand the current limited 100-note diagnostic or prevent preliminary
200/300-note work. The original 04 → 03 dependency is now explicit as 04 → 27 → 03.
No membership algorithm, cycle-resolution method or ranking formula is selected.

The September 23 user checkpoint also confirms 02 remains blocked on 23,
17 and 23 are in progress, 13 and 18 have not started, and 21–22 have made no
further progress. Dates and dependencies are unchanged. See the
[confirmed status table](release-decisions.md#status-confirmed-with-the-user--september-23).

Node 28 is separate from scale measurements: implement and validate a runnable
launch-scale build, including cosine-filtered TRUE and handling large-group
title inputs. It needs the validated small-corpus workflow (03) and findings
from 21 and 22, and is required before completing full-build feasibility (10).
The early assessment (20) does not wait for 28. Recovery measurements from 24
are a dashed input to 20; include graph-processing costs from the hierarchy
builds too. Neither measurement nor a planning card authorizes implementation.

Pilot 06 includes a small hierarchy built from pilot-model outputs before model
selection. Final-model verification in 11 remains required. The second page
lists these completion dependencies separately from week assignments; dates
have not changed.

Page 2 shows protocol, service and Notedeck work in a separate parallel track
alongside hierarchy and model development. Its cards show dependencies, not
new week assignments: service testing needs the protocol and 100-note snapshot;
Notedeck can start from the protocol, and integration needs the service. Launch
still needs the final snapshot. Exact start/completion dates remain open.

The fine-tuning pilot (06) informs the training-volume decision required to
complete the full training data (07). Its dashed arrow does not require the whole pilot to
finish before any bulk generation can start. The agreed 03 + 17 gates remain.
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
