# Oracle experiment adapters

Oracle uses the separate [Experiment runner](../docs/generate-hierarchy.md#1-install-the-runtime)
for prompt execution, request reuse, receipts, cost accounting and review.
This repository supplies its prompts, input adapters, hierarchy construction
and local model support. `experiment-runner.json` selects the Oracle adapters.

Start with [hierarchy generation](../docs/generate-hierarchy.md) to build a
hierarchy, or the [experiment index](../docs/experiments/README.md) to inspect
published evidence. [Reproduction](../docs/experiments/reproduce.md) covers
saved results, local fine-tuned extraction and training. Those guides contain
the supported example configurations.

## Preparing and running experiments

Use `../experiment-runner/bin/experiment-runner` from this checkout, its
installed command with `--project-root`, or the compatibility entry point
`python3 sse_multivector/experiment.py`.

| Command | Effect |
| --- | --- |
| `prepare --spec FILE` | Validate and freeze prompt, cases, source hashes and model settings; make no model calls. |
| `prepare --from OLD --prompt FILE --prompt-id ID` | Inherit cases/settings and use saved outputs as the baseline; do not rerun the baseline. |
| `run EXPERIMENT` | Execute the frozen requests. This is the inference step. |
| `show EXPERIMENT --case ID` | Inspect the exact input, answer, validation and evidence for one case. |
| `review EXPERIMENT` | Record attributed assessments or open a supported review UI. |
| `collect EXPERIMENT --output OUT` | Collect validated saved subject/mask answers into source-bound inputs without inference. |
| `revise` | Create a new version from an explicit base and show the complete change. |
| `verify EXPERIMENT` | Check complete native plans, sources and receipts without credentials or inference. |
| `reconcile-costs EXPERIMENT` | Retrieve missing recorded provider charges without inference. |

Paths in a specification resolve relative to that file. A prompt needs an
explicit version ID, complete template and compatible schema. Generic cases
supply named uppercase variables; substitution is single-pass and does not
interpret placeholder-looking text inside a post. `evidence` stays separate
from model input. Same-ID cases with different variable values are reported as
`input_mismatch`, rather than compared as if they were identical.

Only intentional independent repeats use `--repeat`; identical requests
otherwise reuse their saved answers. Prepare a new directory for changed
inputs/settings. Do not modify a frozen experiment or manually assemble
rendered batches, receipt collections or usage totals. Output directories and
local credentials stay outside Git.

Authentication, provider configuration, retry behavior and the general CLI are
documented in the runner README. The project-specific `run-model.sh` delegates
to that transport for non-experiment callers. Preparing requests does not
validate credentials, authorize inference or establish semantic quality.

## Input adapters

| Adapter | Input and model-visible content |
| --- | --- |
| `posts`, `subjects` | A notes document with stable `note_id` and exact `text`; `{POST}` receives the complete post. Subject answers preserve numbered `number`, `context`, `subject` entries. |
| `masks` | Complete posts and saved subjects. Each subject becomes a separate request; the model receives the post and supplied subject, without diagnostic context. |
| `grouped_masks` | One request per post containing its saved subjects. Answers preserve subject IDs/order; masks use the production word-position decoder. |
| `titles` | Source packets containing exact source fragments. Only numbered mask fragments go to the title model; full posts and IDs remain review evidence. |
| `prominence` | One saved mask plus its complete marked post. Scores are integers from 0 through 100; invalid scores remain visible as failures. |
| `subject_contexts` | A selected node/post/subject collection with optional shared node descriptions; used for the content-ranking comparisons. |
| `hierarchy_local_nodes` | Source-bound selected subjects and their original post/hierarchy context for Bootstrap. |
| `hierarchy_node_pairs` | Source-bound fixed meanings and the selected containment/comparison view. |
| `node_descriptions`, `node_sorting` | Selected saved node membership for shared-description and direct-score studies. |
| Distillation review adapters | Saved generation/reference bindings for matching, support, relationship and coverage checks. See the [grading protocol](distillation-review-v1/README.md). |

Masks, subject vectors and mask vectors are different. A mask contains only
source-post fragments selected for a supplied subject. A subject vector encodes
subject wording by itself. A mask vector encodes an MP-selected mask in its
original post context. Whole-post, title, definition and SP-context encodings
used by diagnostics do not become new masks.

For larger input collections, use existing source adapters rather than copying
posts, IDs or model answers into hand-built cases. Extend shared preparation
when necessary; execution and transport remain in Experiment runner.

## Hierarchy construction and saved results

The [generation guide](../docs/generate-hierarchy.md) uses ASv6.100,
**Hierarchy-bootstrap-v133**, **Hierarchy-consolidated-grouped-v1** and
HiGen V5.3. Earlier or numerically later experimental prompts do not silently
replace those choices. The maintained example files describe new inputs;
original author-local run specifications are preserved at commit `03bd9e45`
under `sse_multivector/hierarchy-runs/`.

Ordinary native preparation freezes sources. Advancing an existing native run
requires its bound source version or an explicit recorded source upgrade.
Published compact hierarchy bundles use `experiment.json`,
`input-note-ids.txt` and unsigned `hierarchy.jsonl`; they preserve final graph
structure and post references, without recreating the original constructor's
intermediate state or receipts.

`export-canonical-viewer` accepts a restored compact hierarchy plus its posts
and validates payload hashes, graph structure and recorded counts. It needs no
model or credentials. The [Nostr export guide](../docs/generate-hierarchy.md#8-export-as-nostr-notes)
describes unsigned toy-protocol events and local browsing; use the documented
private/local relay workflow rather than propagating these experiments to
public relays.

For paid or subscription inference, review the selected account/model first.
There is no shared default model-attempt cap for current Bootstrap, Compare or
hierarchy work. Historical attempt counts and original limits remain evidence;
they do not impose new execution limits.

## Paired definition-writing prompts

Bootstrap and consolidation share one versioned definition-writing source.
Native preparation validates paired assembly manifests for Bootstrap-v129+,
Consolidation-v21+ and the managed pair-consolidation family. It freezes both
complete prompts, their manifests and their file-backed wrapper/shared parts.
The shared rules occur exactly once in each compiled prompt. Evidence and
null behavior remain task-specific wrapper rules.

`prompt_assembly.py check MANIFEST` validates existing source hashes and output
bytes without changing them. `prompt_assembly.py sync` publishes both new
versioned prompts after a shared-rule change; it preserves old versions and
refuses output collisions. Wrapper-only revisions may retain the same shared
rules. Passing assembly/schema checks does not activate a new prompt or prove
semantic quality.

The retained `prompt_sources/*before.md` and `*after.md` files are actual
wrapper parts, not disposable before/after screenshots. Completed edit patches
and revision receipts are preserved through Git history; preparation uses the
canonical prompt/assembly sources directly.

## Review and local models

Keep agent assessments, mechanical checks and actual user decisions separate.
`review --case ID --role agent --verdict accept|reject|uncertain` records an
assessment bound to exact input/output hashes. Use `--role user` only for a
real user decision. A UI comment does not imply approval or rejection.

Title/mask/prominence UIs are optional saved-evidence views. Failed, malformed,
invalid-receipt and unrun results remain visible. Generic tasks use `show` and
attributed CLI review. Input/output changes make earlier reviews stale; they
do not silently apply the old decision to a new answer.

Local weights use the same experiment preparation/run/review path through
`run-local-model.sh`. The local server binds model/checkpoint/configuration
identity, preserves exact rendered requests, rejects overlength input and
retains failure responses. It has no paid fallback. Adapter/readout diagnostics
remain specific to their precision, input contract and checkpoint; teacher
agreement is not independently established accuracy.

The [content-ranking studies](../docs/experiments/content-ranking.md) record
prominence/SSE scoring comparisons and their limitations. The
[student comparison](../docs/experiments/hierarchy/student-comparison.md)
records Bootstrap/Compare checkpoint evidence. The
[semantic grading protocol](distillation-review-v1/README.md) explains the
current saved-answer checks.

## Evidence and source versions

Compact publication datasets retain selected inputs, parameters and final
answers/measurements. `verify-publication-dataset` validates that package;
`restore-publication-dataset` restores compact bundles, not complete native
experiment directories. Native `verify`, `show` and `review` require the full
original native evidence and its source bindings. A compact export cannot be
passed off as that original execution state.

`generation_history.source_at_revision` and the bundled
[commit map](../docs/experiments/commit-map.txt) resolve recorded original
revision aliases without replacement refs. The pre-cleanup commit `03bd9e45`
also preserves the exact current source/configuration files retired from this
tip. That later preserved copy is distinct from a verified original experiment
producer. Keep original hashes and unknown provenance explicit.
