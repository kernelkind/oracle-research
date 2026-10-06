# SHR student preparation while the prompt is unfinished

The user authorized three preparation tasks: GB10 feasibility checks, evaluation
design, and an audit of the existing 1,300-note corpus. Work lives on
`research/shr-student-prep-v1`, in `oracle-mvp-shr-student-prep-v1`.
The user selected SHR-single-v79 for the current provisional teacher pilot.
Earlier model comparisons and the first teacher pilot retain their v26 reference.
A final student and accepted training corpus remain open; release-plan choices
are unchanged. See
[model research](SHR-FINETUNING-MODEL-RESEARCH.md).

## Current outcome, October 6

Seven published checkpoints completed both NF4 relation-only option orders
on the earlier 70 v26 development cases and the new 60 v79 TRAIN coverage
cases. On the new panel Qwen3.8-27B gives 53/60 in both orders, Kev-27B gives
53/60 and 51/60, and Kev-9B gives 44/60 and 40/60. The earlier compact lead
does not transfer; no final student or SHR training plan is selected. Results
support a larger quality reference in future matched supervision,
with compact and cheap training comparisons. See the consolidated
[recommendation and measured tables](SHR-FINETUNING-MODEL-RESEARCH.md#recommendation).

The requested Kev-27B follow-up completed 280 valid single-attempt answers
covering NF4 and BF16 in both orders. Its 51/70 NF4 and 49/70 BF16 agreement
in each order do not improve on Kev-9B's 61/70 and 60/70. This does not isolate
model size or establish a post-finetuning plateau. Suitable complete SHR
training labels and reviewed evaluation roles remain the next dependency;
none of these provisional cases entered gradients or the reserved final test.

The latest workflow/collection regression run completed 167 tests: 161 passed
and six optional tests skipped. All 15 native loader/benchmark tests passed
earlier on GB10. Historical failures remain recorded below. The larger pointer
capacity check passed training, save, fresh-process reload and six inference
shapes at 512, 2,048 and 3,072 tokens; the latter exceeds the complete v26 inputs'
maximum 2,684 tokens.
All experiment workers stopped.
 Current v79 inference uses
longer sequences than the earlier synthetic training checks.

The October 6 input-selection follow-up prepared 640 nomination
families / 1,280 exact A/B orientations from 576 TRAIN notes and 292 authors.
Twenty source-bound input reviews and nineteen additional diagnostic assessments
are saved locally. Six corrective reviews subsequently resolve the named-musician
case against v26's explicit named-painter example; the Food/crop-attack case
remains open. That input-selection phase added no validation cases, training
targets, model calls or SHR fitting. See [TRAIN pair preparation](#train-pair-preparation) and
[the rule review](#rule-review-against-shr-single-v26).

The shared offline collector now supports SHR relation answers with complete
source identity, prompt versions and attributed review history. It retains
disputed decisions without making them accepted training targets. The authorized
**SHR-single-v26 / GPT-6.1 Sol medium** pilot completed 40 new calls on 20 of those
TRAIN families, with 40 current agent reviews and 20/20 consistent reversals.
The remaining 620 families are unlabelled. There are eight equivalence answers,
eight directed parent answers and 24 neither answers; none is uncertain.
See [the teacher pilot](#provisional-shr-single-v26-teacher-pilot).

The authorized coverage follow-up prepared 20 additional diagnostic families /
60 unrun cases from 35 original TRAIN entries, 27 notes and 25 authors.
All 60 have source-bound native input reviews. The panel adds differently worded
pairs, name-ambiguity candidates, related-topic contrasts, and consistent
and intentionally conflicting multi-entry groups with reversal/order controls.
It supplies no new answers or accepted training targets. See
[coverage input preparation](#coverage-input-preparation).

The user subsequently chose **SHR-single-v79** for labeling this panel. All 60
new teacher answers are valid, with no failures, retries or reuse. All 30 exact
A/B reversals and 20 reordered-case checks agree, including all eight
multi-entry families. All 60 attributed native agent reviews support the answers
under v79; supervision remains provisional. See
[the v79 coverage pilot](#provisional-shr-single-v79-coverage-pilot).

## Authorized provisional v26 comparison

The user subsequently authorized comparing candidate behavior on the existing
v26 diagnostic cases and checking training support for additional promising
checkpoints. This phase is local and provisional. It does not require completed
SHR training labels. Untuned encoders with a new SHR head cannot give meaningful
five-relation predictions; their existing capacity checks remain useful.

The user subsequently authorized autonomous continuation until there is
sufficient model evidence. The next local comparison preserves all 70 v26
inputs and compares an added explicit choice question with generated JSON,
direct option-token scoring, and reversed option order. The original prompt
and options stay visible; the scoring variant explicitly replaces only its
answer format. This checks a readout and output-contract hypothesis, not a
matched test of pretraining or head architecture. A decision-trained alternative
and a larger foundation will be measured if needed to resolve the shortlist.
This authorization does not supply completed SHR training labels or permit
reserved final-test access, paid resources, or a release model decision.

The native option-scoring integration test first failed because the old path
decoded text. Its production forward-pass replacement passed all four local
weight tests on GB10. The shared workflow/local/production regression run passed
212 tests with eight optional skips. The initial regression command named a
nonexistent input-test module; that invocation error is preserved, and the
corrected suite passed. Scored answers use no generated reason; their logits,
code mapping and actual rendered choice prompt remain in native receipts.

The comparison uses Qwen3.5-9B instruct, Gemma-4-12B-it, and Kev-9B's native
pointer head with its published adapter. All use explicit NF4 loading. Qwen
and Kev were measured with the separate serving process resident; Gemma used
the subsequently human-authorized pause described below. Each receives the
unchanged saved SHR-single-v26 prompt. Kev additionally receives a configured
choice question
and returns the highest-scoring native option with an empty diagnostic reason.
That different readout contract and its probabilities must remain visible.

The selected existing experiments are `v26-regression-original` (40 cases),
`v26-regression-scope` (8) and `v26-regression-transfer` (22), in the read-only
`oracle-mvp-shr-single-pair-v1/target/shr-single-iteration-v1/` worktree. They
contain 70 directed cases / 35 reversal pairs per checkpoint. They are prompt
development diagnostics, separate from the ASv6.100 split. The old teacher
answers are comparison evidence, not semantic gold. No ASv6.100 final-test
records, new teacher calls or validation gradients are involved.

Preparation uses native `experiment.py prepare --from` with the owned local
runner; `run`, `show` and `review` retain native provenance and case evidence.
Source configurations are in `distillation/diagnostic-*.json`; model weights,
review artifacts and upstream source snapshots stay ignored under
`target/shr-student-diagnostics-v1/`. Qwen instruct is pinned to `c202236`,
Gemma to `707f0a3`, Kev's adapter to `db029f0`, and its Qwen base to `68c46c4`;
the configurations retain full immutable revisions. Kev source is pinned to
GitHub `5e42a7a` with an implementation hash. This verifies a composed native
NF4 path in our environment, not upstream's different declared Torch environment.

At the transport checkpoint, all 203 shared experiment/extraction tests passed
with six optional skips, and all four local HTTP integration tests passed.
Those tests exercise actual preparation, CLI execution, exact prompt/schema
preservation, receipt reuse, invalid output and identity rejection. Inference
and additional training measurements are pending at this checkpoint.

The subsequent shared report adds relation-only baseline agreement/confusion
and exact-input reversal diagnostics. All 215 shared workflow/local/benchmark
tests passed with seven optional skips. Native GB10 tests first exposed that
the existing loader selected Gemma-4's complete unified multimodal model;
the corrected production loader selects `gemma4_unified_text`, remaps the
saved language-model keys and checks all text weights. A tiny native unified
checkpoint now reproduces its original text logits without audio/vision
modules. These two checkpoint/identity tests passed on GB10.

The first Gemma load was stopped when available memory crossed its reserve;
its execution config also predated the frozen source config. It produced no
student answers. The first Kev experiment rejected all 40 requests before
inference because its execution config's memory-budget field differed, giving
a different model identity. Those failed receipts remain unchanged. Corrected
source files/configs are checked by hash before new calls. Kev's new native
experiment names the learned adapter rather than the base model; its identity
and request differ from the failed experiment. Failed cases are not resumed or
automatically retried. No inference output from either failed path is scored.

The capacity runner now supports native pointer heads alongside encoder and
causal-LM paths. It measures synthetic five-option positions through the native
batched pointer head, trains published LoRA weights plus the head, and verifies
saved adapter/head reload logits. The shared pointer configuration binds the
foundation, quantization, memory limits and upstream implementation. Its
synthetic positions are capacity inputs, not SHR labels or a convergence test.
Pinned capacity configurations cover Kev-9B and Gemma-4-12B-it at 512 and
2,048 tokens. Full candidate measurements remain pending at this checkpoint.

The first full Kev optimization exceeded its 12 GiB allocator cap before any
completed updates. Extracting the backbone loses the outer LM's k-bit marker;
PEFT's preparation therefore did not enable checkpointing automatically. A
small native NF4/LoRA/pointer optimization and save/reload test reproduced
disabled checkpointing. The production path now explicitly enables native
checkpointing on that backbone with `use_reentrant=False` and disables its
training cache. All eight capacity tests passed on GB10, including both native
CUDA integration tests. The 44 production distillation tests also passed;
the earlier combined run's sole error was the tiny GPU benchmark's admission
while Kev inference was resident. Its separate nonresident rerun passed.
The CPU-only Anvil check cannot run the Torch-dependent distillation class;
that missing-package result is retained rather than counted as a pass.

### Provisional comparison results

The 140 Qwen/Kev calls in this table used published checkpoints, not the
synthetic optimization checkpoints. Each had one attempt and a valid
five-relation JSON answer. Baseline agreement ignores diagnostic reason
wording. No paid calls
or SHR teacher-label generation occurred.

| Checkpoint/readout, NF4 | Original teacher agreement / reversal consistency | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Qwen3.5-9B instruct, greedy JSON | 25/40; 15/20 | 4/8; 1/4 | 7/22; 6/11 | 36/70; 22/35 |
| Kev-9B published adapter and pointer head | 33/40; 18/20 | 6/8; 2/4 | 22/22; 11/11 | 61/70; 31/35 |

These are development diagnostics, not accuracy or a ranking after equal SHR
training. Repeated topics and related cases are not independent samples.
Kev's explicit choice question, decision training and readout differ from
Qwen's generation contract. Its published temperature is not SHR calibration;
option probabilities do not redefine semantic `uncertain`.

Native agent reviews record concrete failures: Qwen narrowed Music using a
context hashtag, confused parent direction despite a correct scope explanation,
and treated an omelette as a cooking activity. Kev handled those broad-field
and direction controls better, but still merged Music recording with Music
recordings, imported an author restriction from context, and inconsistently
treated a recipe step as necessary. The earlier field/person uncertainty is
superseded by [the v26 rule review](#rule-review-against-shr-single-v26): the
named-painter example supports named-musician containment. Agreement with a
teacher answer alone does not establish semantic gold. The reviewed cases and
comments remain in native experiment files.

A roster-only check of the 22 source-note IDs attached to the saved development
cases found zero matches in ASv6.100 training, validation or reserved final-test
membership. It read the prepared manifest's IDs, not final-test content or
references. This phase does not erase the earlier exposure record below.

Gemma-4-12B-it's earlier complete and corrected text-only loads were stopped
when co-resident CPU memory pressure caused heavy swapping. The user then
explicitly authorized a temporary pause while preserving the serving system.
The co-resident serving process was paused for the subsequent capacity checks.

### Gemma decisions and output contract

The paused-server window allowed the unchanged pinned Gemma text model to load
with the existing 12 GiB CUDA allocation cap. Available system memory before
loading was about 118 GiB. It completed all 70 saved v26 cases, each in one
attempt. Every response enclosed its JSON answer in a Markdown fence, violating
v26's explicit no-Markdown instruction. All 70 remain native failed receipts;
none was repaired, retried, converted into a valid output or used for fitting.
`relation_diagnostics` therefore reports no validated Gemma decisions.

Read-only inspection of the raw answers gives a separate development assessment:

| Raw-label inspection | Teacher agreement | Reversal consistency |
| --- | ---: | ---: |
| Original | 32/40 | 18/20 |
| Scope | 6/8 | 3/4 |
| Transfer | 10/22 | 11/11 |
| Total | 48/70 | 32/35 |

This is an agent inspection of raw labels, not the native validated-output
metric or semantic gold. The original disagreements are `P03-forward`,
`P05-forward`, both `B01`, both `B03` and both `B06` directions; scope differs
on both `R05` directions; transfer differs on both directions of `R10` through
`R15`. Inconsistent raw reversals are `P03`, `P05` and `R05`. All other displayed
raw labels match the saved baseline and its reversed order. Repeated Culture
cases do not supply twelve independent observations.

Native agent reviews preserve concrete evidence. Gemma's Music/Jazz and
Science/Psychology decisions preserve the broad fields. Coffee/Coffee drinking
and general/specific puzzlement each have a forward parent-label error despite
an explanation identifying the broader topic. It treats an omelette as beneath
Cooking and merges the recording activity with its resulting works. Pollan's
author/advice limit is imported into an unrestricted eating principle. On the
Culture transfer cases it returns `neither` in both directions, sometimes
reasoning that Culture includes other activities or is not limited to the
narrower topic; those facts do not refute narrower-to-broader containment.
The [v26 rule review](#rule-review-against-shr-single-v26) now supports the
named-musician containment from the prompt's named-painter example. The earlier
uncertain reviews remain recorded; teacher disagreement alone is not gold.

Fresh native experiments are `gemma-{original,scope,transfer}-v3`; the unused
v2 plans predate final serving-loader cleanup and remain preserved. Preparing
v3 froze the committed runner identity while retaining the exact saved v26
inputs, prompt, greedy settings and teacher baseline. The initial missing
history-directory preparation error made no calls and is retained. Full
native `show --json` views remain ignored at `gemma-*-v3-show.json`.
The three `run/results.jsonl` SHA-256 bindings, in original/scope/transfer order,
are `e5f3ef7df1ca384f831778672aa86efacd77494f8a5d740f909e57cafb0c0054`,
`0ac9e4e56d6fcb9fc54dd2c277306740a3a458f55a15e64f8022d2c841a9cbf7`, and
`f404c79b425b286767601bbc2496790ea79e26f65c16ff34d05658870b0de0ca`.

Kev remains the better-supported provisional decision warm start. Gemma's
raw-label assessment exceeds Qwen instruct's validated agreement, but its
published checkpoint still exhibits scope and direction failures. Its output
formatting can change with task training; these results do not disqualify the
foundation or rank students after matched SHR training. High reversal
consistency alone does not establish correct containment.

### Qwen readout and option-order controls

The autonomous continuation completed 210 new Qwen calls, all valid in one
attempt. The explicit option definitions match the Kev configuration. Generated
JSON still requests a reason; scoring explicitly replaces that output contract
with an option letter and returns an empty reason through the native adapter.
All original v26 rules, examples and final supplied inputs are preserved.

| Qwen3.5-9B instruct, NF4 | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Added choices, generated JSON | 25/40; 14/20 | 2/8; 0/4 | 7/22; 5/11 | 34/70; 19/35 |
| Direct option scoring, original order | 25/40; 7/20 | 1/8; 0/4 | 8/22; 4/11 | 34/70; 11/35 |
| Direct option scoring, rotated order | 25/40; 15/20 | 5/8; 2/4 | 6/22; 9/11 | 36/70; 26/35 |

The original generated-JSON comparison was 36/70 and 22/35. These new interfaces
do not establish an improvement. Rotation changes every code: the original
order is equivalent, A-parent, B-parent, neither, uncertain; the rotated order
is B-parent, neither, uncertain, equivalent, A-parent. Reversing five choices
alone leaves the middle code unchanged, so those initially prepared reversal
plans were not run.

The two scored orders preserve only 32/70 decisions: 19/40 original, 0/8 scope,
13/22 transfer. The original order never selects A-parent; the rotation never
selects B-parent. Similar aggregate agreement hides different directional
failures. Native agent reviews reject a parent edge between equivalent Cooking
topics and a reversed edge between Coffee and Coffee drinking. This is evidence
against using untuned letter scoring as Qwen's default, not evidence that it
cannot learn a stable relation output after task-specific training.

Native experiments are `qwen-{choices-json,options,options-rotate}-{original,
scope,transfer}-v1`. Rotation experiments use the completed normal-order answers
as their immediate baseline, measuring option-order stability. The separate
`qwen-options-rotate-teacher-*-v1` views inherited the old teacher baseline and
reused all 70 rotated answers with **zero new attempts**. They supply the rotated
teacher-agreement row without duplicate inference or manual comparison files.
The local serving source is `06fb274c`; rotation configurations are at
`b9135f7e`. Full native reports and failed command invocations remain ignored.

### Gemma option-order controls

The autonomous continuation also completed 140 new Gemma scored calls, all
valid in one attempt. Its published NF4 weights and all v26 inputs remain the
same; the two choice orders are the same as Qwen's controls above.

| Gemma-4-12B-it, NF4 | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Direct scoring, original order | 25/40; 10/20 | 1/8; 2/4 | 11/22; 1/11 | 37/70; 13/35 |
| Direct scoring, rotated order | 34/40; 16/20 | 6/8; 3/4 | 14/22; 5/11 | 54/70; 24/35 |

Only 38/70 decisions survive rotation: 27/40 original, 1/8 scope and 10/22
transfer. Selecting the better order after observing these diagnostics would
overstate generalization. The original order incorrectly calls Coffee and
Coffee drinking equivalent; rotation fixes that case but introduces a parent
label between two unrestricted Food subjects. These are native agent reviews,
not user approvals. Neither readout supplies SHR fitting targets.

The rotated run additionally records full-vocabulary scoring evidence. Allowed
letter mass ranges from 0.0000465 to 0.161, with median 0.00180. The unrestricted
top token is `(` in 56 cases, a JSON opener in 13 and a Markdown fence in one.
Thus most next-token probability lies outside the requested standalone letters.
The conditional option probabilities alone do not show reliable output-format
compliance or semantic confidence. This observation motivates retaining the
generated-label comparison for chat foundations; it does not establish their
quality after task training. Restricted-code decision training has a different
loss and need not assign high full-vocabulary mass to its codes.

Native experiments are `gemma-options-{original,scope,transfer}-v1` and
`gemma-options-rotate-*-v1`; the latter use the first order as immediate baseline.
The `gemma-options-rotate-teacher-*-v1` views reuse all 70 rotated answers with
zero new attempts. Reports, reviews and receipts remain ignored under the owned
diagnostic directory. Scoring metadata and saved usage/stop reasons are exposed
through native `show`, with production HTTP/report tests and all six GB10 native
weight tests passing. The final experiment regression passed 117 tests with six
optional skips; the ten local tests passed with four native-weight skips on
Anvil. An initial test assertion expected twelve fixture input tokens although
the fixture returns ten; the corrected test passed without a production change.

The next comparison adds the current Nimble adapter, native decider-4b v2.1 and
Qwen3.8-27B as a larger foundation, while checking Gemma's same readout controls.
Native format tests first exposed the missing causal adapter and the different
schema/segmented input layouts. Their replacements verify exact learned tensors
and native single-pass logits. These additions use published weights, not SHR
training or synthetic benchmark checkpoints. Continued SHR fitting and final
student selection still require accepted relationship supervision and semantic
evaluation beyond these related development cases.

The final expanded workflow regression passed 214 tests with ten optional
skips; all six native weight tests passed on GB10. Nimble's tokenizer files
have different hashes from its Qwen foundation, but vocabulary mappings and
all 70 full native schema inputs/candidate IDs are identical. That exact-input
parity check made no model calls. The current 12,026-row/8,192-token Nimble
release replaces the initial report's attribution of the original smaller
release. No published score is silently reassigned to the new checkpoint.

### Current Nimble native comparison

The pinned v3-12026 Nimble adapter completed all 70 v26 cases with its native
schema builder and NF4 Qwen3.5-9B instruct foundation. Every answer is valid
in one attempt; reasons are empty by design. This is a published-checkpoint
comparison, not continued SHR training.

| Nimble native schema readout | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Original option order | 29/40; 15/20 | 6/8; 4/4 | 21/22; 10/11 | 56/70; 29/35 |
| Rotated option order | 28/40; 14/20 | 6/8; 4/4 | 17/22; 6/11 | 51/70; 24/35 |

All 70 rotated answers are also valid in one attempt. The two orders preserve
61/70 decisions: 35/40 original, 8/8 scope and 18/22 transfer. Native rotation
experiments use the first order as baseline; the teacher-baseline views reuse
all 70 rotated answers with zero new attempts. This is more stable than the
chat-model letter controls but still introduces directional inconsistencies.
The original order's median full-vocabulary code mass is 0.9986, with all
unrestricted top tokens among the five allowed letters. Output-format failure
does not explain these original-order semantic disagreements. Full native schema
inputs range from 3,443 to 3,533 tokens; median reported inference is 1.62 seconds.
This warmed diagnostic rate is not deployment throughput or a training forecast.

Agent reviews reject `neither` for Music versus an unidentified `#coffeechain`,
and the parent link placing unrestricted Cooking below Kitchen work. The latter
assumption fails for outdoor cooking, including the supplied rocket-stove
context. It also reverses the Coffee/Coffee drinking direction and treats two
unrestricted Food subjects asymmetrically. The strong transfer count includes
the related Culture cluster; these remain development evidence, not independent
gold examples. The rotated order is retained without selecting the better one.

Native experiments are `nimble9b-{original,scope,transfer}-v1`. Full reports,
source receipts and agent reviews remain ignored. The source-bound native
builder treats context as data; v26 is supplied as context and a separate
question directs applying those rules to the final input. This interface is
different from Qwen/Gemma chat and Kev's pointer state. Exact adapter tensors
and all 70 tokenizer inputs/candidate IDs were verified before inference.
Continued optimization of this particular adapter is not yet measured; the
verified native warm-start optimization remains Kev's.

Native rotation experiments are `nimble-options-rotate-*-v1`; teacher-baseline
views are `nimble-options-rotate-teacher-*-v1`. Pinned synthetic capacity
configurations also now cover decider-4b and Qwen3.8-27B. Their measurements
remain pending at this checkpoint; configuration validation is not a passed
training or quality test.

### Decider-4b native comparison

The pinned v2.1 merged decision checkpoint completed all 70 cases through its
native plain state-first builder, without chat wrapping, shuffling or truncation.
NF4 weights give a valid relation-only result in one attempt for every case.
Its published choice temperature 1.110 is preserved, not calibrated on SHR.

| Decider-4b native readout | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Original option order | 30/40; 17/20 | 5/8; 2/4 | 10/22; 9/11 | 45/70; 28/35 |
| Rotated option order | 29/40; 17/20 | 5/8; 2/4 | 8/22; 11/11 | 42/70; 30/35 |

All 70 rotated answers are also valid in one attempt. The orders preserve
58/70 decisions: 34/40 original, 4/8 scope and 20/22 transfer. Higher rotated
reversal consistency accompanies more rejected containment links; consistency
alone is not correctness. The original 40 cases have median full-vocabulary
code mass 0.561, and all unrestricted top tokens are allowed letters.

Agent reviews reject merging Music recording as an activity with Music
recordings as works, and reversing the parent direction between a specified
writer's puzzlement and unrestricted Puzzlement. It also rejects the Culture /
Song creation parent link, missing v26's preservation of creative activities
within a general field. Most transfer disagreements are the related Culture
cluster, not twelve independent observations. The
[v26 rule review](#rule-review-against-shr-single-v26) now supports the
named-musician containment from the prompt's named-painter example; that
assessment does not turn teacher agreement into independently approved gold.

Native experiments are `decider4b-{original,scope,transfer}-v1` and
`decider-options-rotate-*-v1`. Teacher-baseline views named
`decider-options-rotate-teacher-*-v1` reuse all 70 rotated answers with zero
new attempts. Published direct-decision
behavior supports retaining this small model as a cheaper training candidate,
below the tested 9B warm starts; it does not rank it after SHR adaptation.

Its native NF4 LoRA capacity check now passes with 32,464,896 FP32 adapter
parameters over the published merged checkpoint. Frozen nonquantized parameters
remain BF16, with BF16 autocast and native gradient checkpointing. Updates take
0.613 seconds at 512 tokens and 2.241 at 2,048, with allocated peaks 3.62 and
4.17 GiB. Batch-eight inference gives 6.08 and 1.62 examples/sec, with peaks
3.58 and 5.12 GiB. Load/save/fresh reload take 51.29/1.25/58.01 seconds.
The separate workers `1480212` / `1518386` verify matching saved logits and
finite five-way inference. Synthetic targets establish capacity, not SHR
convergence; these trained probes are not the checkpoint used for diagnostics.
The owned local report copy is `decider4b-training-v1-report.json`, SHA-256
`52a6ccf9acfd458b78e9192c4c961f749eb03f782567424536dde1081c2b1ad0`.

### Chat answer-prefix control

Bare-letter scoring is not a matched substitute for a model that wants to
begin its answer with punctuation. The next control prefills `Answer: (` after
the native chat generation template, retaining the complete v26 state and the
same choice definitions. It scores the letter at that answer position without
generating or repairing text. Both criterion orders are frozen for Qwen-9B,
Gemma-12B and Qwen-27B; the latter is also retained with unmodified generated JSON.
These are new experiments, not retries of failed formatting receipts.

The native production test first fails on 47 input tokens versus the expected
50, reproducing the ignored prefix. After implementation all six native weight
tests pass on GB10; 127 shared workflow/local tests pass with ten optional skips.
The real tokenizers confirm that `Answer: (` preserves standalone A–E tokens
for all three checkpoints; bare `(` does not for Qwen. Each complete input is
also checked at inference for code-boundary agreement and input length. The
actual prefix and rendered scoring prompt remain in native response metadata.
The Qwen-9B prefix controls are complete: 140 new valid one-attempt answers.
All original-order unrestricted top tokens are A–E; median allowed-code mass
is 0.99945, with full inputs 2,638–2,724 tokens. The prefix fixes the measured
format mismatch but does not close the semantic gap to the decision warm starts.

| Qwen-9B with `Answer: (` | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Original option order | 24/40; 14/20 | 1/8; 0/4 | 10/22; 6/11 | 35/70; 20/35 |
| Rotated option order | 26/40; 16/20 | 6/8; 2/4 | 7/22; 10/11 | 39/70; 28/35 |

Only 47/70 decisions survive rotation: 28/40 original, 3/8 scope and 16/22
transfer. This improves stability over the earlier bare-code controls but
remains below Kev's 66/70 and Nimble's 61/70. The original generated-JSON path
gave 36/70 and 22/35. These comparisons support a semantic benefit hypothesis
for decision specialization without isolating the effects of base pretraining,
task data, prompt layout and head architecture or predicting post-SHR tuning.

Native experiments are `qwen-options-prefix-*-v1` and
`qwen-options-prefix-rotate-*-v1`. The teacher-baseline views
`qwen-options-prefix-rotate-teacher-*-v1` reuse all 70 rotated answers with zero
new attempts. The later larger-Qwen section records its completed prefix comparison.

Gemma's original-order prefix run now completes all 70 cases with valid
one-attempt answers. It gives 34/40 agreement and 20/20 reversals on the original
cases, 6/8 and 3/4 on scope, and 9/22 and 10/11 on transfer: **49/70 and 33/35**
overall. Median allowed-code mass is 0.999987; every unrestricted top token is
one of A–E. The position correction fixes the simple Coffee and puzzlement
direction errors seen in its raw generated labels, but preserves the recording
activity/product merger, an unsupported Cooking/omelette edge, and most Culture
containment failures. Native agent reviews record the omelette error and the
missed Cats/Nature direction. These are new scored results, not repaired versions
of the earlier Markdown-fenced responses.

| Gemma-12B with `Answer: (` | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Original option order | 34/40; 20/20 | 6/8; 3/4 | 9/22; 10/11 | 49/70; 33/35 |
| Rotated option order | 35/40; 19/20 | 7/8; 3/4 | 12/22; 9/11 | 54/70; 31/35 |

All 70 rotated answers are also valid in one attempt. The corrected readout
preserves 65/70 decisions across orders: 39/40 original, 7/8 scope, 19/22 transfer.
Its old bare-letter controls preserved only 38/70. Answer position therefore
accounts for much of the previously observed order sensitivity; the corrected
semantic disagreements remain meaningful development evidence. The two orders
are both retained without selecting the more favorable one.

Native experiments are `gemma-options-prefix-*-v2` and
`gemma-options-prefix-rotate-*-v2`. Teacher-baseline views
`gemma-options-prefix-rotate-teacher-*-v2` reuse all 70 rotated answers with zero
new attempts. Unrun older prefix-free alternatives and all failed generated-JSON
receipts remain unchanged. These corrected controls retain Gemma as an independent
training foundation, below Kev's current diagnostic lead without ranking them
after matched SHR adaptation.

### Larger Qwen reference

The pinned Qwen3.8-27B native NF4 path completed 70 new single-attempt calls
with the unchanged v26 generation prompt. There were 69 valid JSON answers and
one failed output; failed receipts are preserved without repair or retry.

| Qwen-27B greedy JSON | Teacher agreement / comparable cases | Reversal consistency / comparable pairs |
| --- | --- | --- |
| Original | 30/40 | 16/20 |
| Scope | 3/8 | 1/4 |
| Transfer | 9/21 valid; one failed attempt | 7/10; one noncomparable pair |
| Total | 42/69 valid; 70 attempted | 24/34 |

The failed `C06-forward` output hit the 512-token limit during a repetitive
Nature/Cats explanation. Its initial `neither` judgment also treats the
unrestricted Nature field as excluding animals; native agent review rejects
both the invalid answer and this scope reasoning. Other native reviews reject
Coffee/Coffee drinking's reversed relation despite an explanation identifying
Coffee as broader, and the Cooking/omelette answer that imports an activity
into the product topic. The larger checkpoint repeats activity/product and
broad Culture failures, so its additional capacity has not established a
quality advantage on these development cases.

Native experiments are `qwen27b-json-{original,scope,transfer}-v2`. Config-bound
identity uses revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` and configuration
SHA `046bcb0b111d0711f662472025ed63d2c6060d2b449077b4db5b07fe6c930bf0`.
Median reported inference times were 7.728, 9.368 and 9.799 seconds by case
group, including each group's output generation. They are single-request
observations, not warmed batched deployment throughput. Full prompt input was
preserved. Internal thinking was disabled, as in the other chat controls;
these results do not evaluate bounded reasoning or SHR finetuning.

Checked answer-prefix scoring now completes both code orders, with 140 new
valid one-attempt answers. The prefix remains `Answer: (`; no generated answer
or reason is repaired. The teacher-baseline views reuse all 70 rotated answers
with zero new attempts.

| Qwen-27B checked scored readout | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| Original code order | 32/40; 20/20 | 6/8; 2/4 | 15/22; 6/11 | 53/70; 28/35 |
| Rotated code order | 33/40; 19/20 | 6/8; 2/4 | 13/22; 6/11 | 52/70; 27/35 |
| Same decision across code orders | 39/40 | 8/8 | 12/22 | 59/70 |

Median allowed-code vocabulary mass is 0.998767 / 0.998723 in the two orders;
all unrestricted top tokens are allowed A–E codes. Thus the remaining gap is
not the earlier bare-letter punctuation mismatch. Both medians of reported
inference time are 2.980 seconds, with full inputs 2,638–2,724 tokens. These are
single-request timings, not a batched deployment comparison.

The readout fixes Coffee and the other simple parent-direction mistakes,
plus the generated Nature/Cats failure in its original order. It retains
Cooking/product, recording activity/works and food-damage errors. Native agent
review rejects Cooking/Kitchen work's imported kitchen restriction and the
Culture/Song creation field-scope error. Rotation changes ten transfer answers:
four Culture forward answers become parents while five reverse answers become
`neither`; Nature/Cats reverse also becomes `neither`. The Culture cases are
related diagnostics, not ten independent failures. The larger foundation's
additional size does not establish an advantage over Kev's 61/70 and 60/70
on this provisional evidence. This does not rank post-finetuning models.

Native experiments are `qwen27b-options-prefix-{part}-v2`,
`qwen27b-options-prefix-rotate-{part}-v2` and the zero-call teacher views
`qwen27b-options-prefix-rotate-teacher-{part}-v2`. Config SHA values are
`59e55d1efe562309ecf82ba960fb3e6c24e6878fd29d701a1f528ab387241c2e`
and `510800c41181d78ac0a214a76145314b7eaddd702c4a21ee91d5367592fb975b`.
All use the published pinned weights rather than synthetic optimization
checkpoints. The completed native capacity path is recorded below.

### Kev option-order check

The published native Kev pointer path completed all 70 rotated v26 cases in
one attempt each. It preserves 66/70 first-order decisions: 37/40 original,
7/8 scope and 22/22 transfer. Its teacher agreement changes from 61/70 to
60/70; reversal consistency stays 31/35.

| Kev native pointer, rotated criteria | Teacher agreement | Reversal consistency |
| --- | ---: | ---: |
| Original | 31/40 | 17/20 |
| Scope | 7/8 | 3/4 |
| Transfer | 22/22 | 11/11 |
| Total | 60/70 | 31/35 |

The changed cases are `P03-forward`, `B01-forward`, `B02-forward` and
`R06-reverse`. Rotation introduces a reversed parent direction for Coffee and
Coffee drinking, despite preserving the whole related Culture cluster. These
results support Kev as the strongest tested compact decision warm start so
far, without claiming order invariance or semantic accuracy. The earlier
Culture/person uncertainty is superseded by
[the v26 rule review](#rule-review-against-shr-single-v26).

Native experiments are `kev-options-rotate-*-v1`; teacher-baseline views are
`kev-options-rotate-teacher-*-v1`. The latter reuse all 70 answers with zero new
attempts. The original `kev-*-v2` answers, prior failures, native reviews and
configurations remain unchanged.

### Verified Kev capacity path

The full native NF4/LoRA/head check passed at 512 and 2,048 tokens with the
existing server resident. It trained 45.38 million parameters, including a
2.10 million-parameter pointer head. K-bit preparation promotes nonquantized
base parameters to FP32; LoRA/head parameters are FP32 with BF16 autocast.
The base LM's vocabulary head is absent from this pointer path.

| Synthetic complete input | Seconds/update | Peak allocated GiB, training | Examples/sec, batch 8 | Peak allocated GiB, batch-8 inference |
| --- | ---: | ---: | ---: | ---: |
| 512 tokens | 1.47 | 8.30 | 3.25 | 8.43 |
| 2,048 tokens | 4.77 | 9.82 | 0.84 | 11.72 |

Each length used one warmup update, four measured updates and five warmed
inference repetitions. These are capacity measurements, not SHR convergence,
deployment throughput or a comparison at identical nonquantized precision.
The correct reference causal convolution was used; this is not an optimized
throughput ceiling. Short samples do not forecast a full training run.

Checkpoint validation uses separate workers when needed:

```bash
python3 -m sse_multivector.distillation_benchmark \
  --config sse_multivector/distillation/benchmark-kev9b-nf4.json \
  --output target/shr-student-diagnostics-v1/kev-training-v3 --stage train
python3 -m sse_multivector.distillation_benchmark \
  --config sse_multivector/distillation/benchmark-kev9b-nf4.json \
  --output target/shr-student-diagnostics-v1/kev-training-v3 --stage verify
```

The training worker saves a source-bound synthetic input/logit probe alongside
adapter/head weights. Verification checks configuration, code and checkpoint
hashes before loading, then requires matching probe logits and finite five-way
batched outputs. It performs no repeated training. The verified workers had
different PIDs; the report records both. Single-worker save/reload remains the
default for smaller paths. Memory admission and reserve checks occur before
loading and between workloads; they are not a continuous CPU-load limit.

The fully verified report is ignored at `kev-training-v3/report.json` on GB10,
with an owned Anvil copy `kev-training-v3-report.json`. Its SHA-256 is
`7a57d03a782ee6622ade4c3d630603b3a32483db2a0703e5bb730ecc6baf0d3d`.
Source at `a56fc473` reproduces its recorded implementation hashes; later
cleanup removes an unused serving-loader training flag, with optimization
controlled solely by the tested capacity path. The prior OOM and reload
admission reports remain unchanged. All eight native capacity tests passed
after adding staged verification. The final full shared CPU suite passed
218 tests with nine optional skips; the subsequent focused source checks
passed 14 tests with three native-weight/CUDA skips. Native GB10 coverage also
includes the 44 production distillation tests and two checkpoint/identity tests.

### Verified Gemma capacity path

The pinned NF4 Gemma text model also passed native LoRA optimization, save,
fresh-worker reload/probe-logit agreement, and all four finite five-way
inference shapes. Its 65,568,768 trainable parameters are FP32 LoRA weights;
the shared subject-training loader requests a BF16 frozen base and the
benchmark uses BF16 autocast with native gradient checkpointing. It does not
apply the pointer path's k-bit preparation. The five synthetic scores come
from arbitrary vocabulary IDs through the native one-position projection,
not a trained SHR head or generated reasons.

| Synthetic complete input | Seconds/update | Peak allocated GiB, training | Examples/sec, batch 8 | Peak allocated GiB, batch-8 inference |
| --- | ---: | ---: | ---: | ---: |
| 512 tokens | 1.57 | 8.44 | 2.58 | 8.02 |
| 2,048 tokens | 6.33 | 9.44 | 0.64 | 9.93 |

The same one-warmup/four-update and five-inference-repetition protocol was
used. Training and verification workers were PIDs 1409658 and 1410442. The
report is complete, reload logits match, and no error is recorded. Load and
reload took about 148 and 190 seconds. This model path fits the existing
12 GiB CUDA cap when the serving container is paused; loading memory remains
a separate issue. It is a successful synthetic capacity check, not an SHR
training result or full-run forecast. The Kev and Gemma paths differ in their
head, frozen-weight preparation and serving contention, so these timings are
not a controlled architecture comparison.

The ignored GB10 report is `gemma-training-paused-v1/report.json`, with an
owned Anvil copy `gemma-training-paused-v1-report.json`. Its SHA-256 is
`9623f99781de43c44cbb03f2bfdb43a7336c12ede4ce8e80b5c1f68536afb9dd`.
Source at `e7d3dc5e` reproduces the recorded code hashes and configuration.
All experiment workers stopped after the check; system availability returned to about 118 GiB.
The service script and Compose file fingerprints match their pre-pause
values. 

### Verified full Ettin-1B capacity with the service stopped

The existing 20 GiB full-training configuration exceeded its allocator cap
before completing an update, even after the service stop. Its failed report
remains unchanged. A fresh configuration changes only the cap to 32 GiB,
preserving the 8 GiB system reserve, model pin and synthetic workload. That
native full-training path passes all three lengths, saves the checkpoint, and
reloads it in a different worker with matching logits. It updates all
1,031,272,709 parameters in FP32, with BF16 autocast and native checkpointing.

| Complete synthetic input | Seconds/update | Peak allocated GiB, training | Examples/sec, batch 8 |
| --- | ---: | ---: | ---: |
| 256 tokens | 0.582 | 19.27 | 56.41 |
| 512 tokens | 0.628 | 19.27 | 28.17 |
| 2,048 tokens | 1.055 | 19.27 | 6.73 |

Batch-one inference gives 23.98, 18.85 and 6.16 examples/sec at those lengths.
Maximum batch-eight allocated memory is 4.89 GiB at 2,048 tokens. The allocator
cap includes reserved memory beyond the reported allocated peak; the failed
20 GiB run does not imply that the GB10 cannot train this model. Loading,
saving and fresh-worker reloading take 19.19, 32.61 and 33.62 seconds. The
synthetic labels verify finite optimization and reload, not SHR convergence.
The earlier LoRA/co-resident measurements are a different precision/optimization
and contention condition, not a controlled full-versus-LoRA speed experiment.

Configuration: `distillation/benchmark-ettin1b-full-paused.json`. The completed
GB10 report is `ettin1b-full-paused-v2/report.json`, with an owned local copy
`ettin1b-full-paused-v2-report.json`; SHA-256 is
`1564c61bbae04c03489d93a92ecae624f12cd92a5e423f80fdd6a0bd5c91a3c1`.
Training worker `1475815` and verification worker `1476572` are distinct.
The service remains stopped as the human requested; this check does not alter
its configuration or restart policy.

### Verified larger Qwen capacity

The pinned Qwen3.8-27B native NF4 LoRA path passes 512- and 2,048-token
optimization, checkpoint saving, a fresh-worker reload with matching logits,
and batch-one/batch-eight inference at both lengths. Logical parameters total
27,012,726,272; 116,727,808 trainable parameters are FP32 LoRA, enforced by the
shared subject-training loader. The loader requests BF16 for the frozen nonquantized base, with
BF16 autocast and native gradient checkpointing. Five arbitrary vocabulary
positions supply synthetic targets; no SHR labels or cases enter optimization.

| Complete synthetic input | Seconds/update | Peak allocated GiB, training | Examples/sec, batch 8 | Peak allocated GiB, batch-8 inference |
| --- | ---: | ---: | ---: | ---: |
| 512 tokens | 3.150 | 18.80 | 1.391 | 17.72 |
| 2,048 tokens | 9.985 | 20.07 | 0.388 | 20.08 |

Batch-one inference gives 1.032 and 0.332 examples/sec at those lengths.
The same one-warmup/four-update and five-inference-repetition protocol applies.
Loading, saving and reloading take 411.97, 4.02 and 326.61 seconds. Initial
512-token warmup takes 16.33 seconds; steady update medians exclude it.
The correct reference PyTorch causal convolution is used because the optional
optimized kernel is absent. These are observations of this stack, not an
optimized GB10 ceiling or a matched architecture speed ranking.

Configuration `distillation/benchmark-qwen27b-nf4.json` retains a 32 GiB
allocator budget plus an 8 GiB system reserve. It succeeds with the service
stopped, showing that the model has a usable local fitting path. The measured
2,048-token training workload is shorter than the full 2,638–2,724-token
zero-shot scored prompt; it does not certify all future training-input lengths.
The 27B checkpoint's additional cost has not established better developmental
SHR decisions than Kev-9B. No convergence or final accuracy claim follows.

GB10 report: `qwen27b-training-v1/report.json`; owned Anvil copy:
`qwen27b-training-v1-report.json`. SHA-256:
`e35e8c71e5179036066b1ab47017143766484943fea367964b01fb3ea8518c23`.
Configuration SHA-256:
`e81c6c33eaf0fa49696782913dd612634c685c50c0624888bf8a0a918fb363c9`.
Training worker `1572240` and verification worker `1578205` are distinct.
The report is complete and reload logits match. The existing service remains
stopped as the user requested; all owned GPU workers have exited.

### Kev-27B benchmark preparation

The human requested a Kev-27B benchmark on October 6. The pinned public
checkpoint is `jaredpalmer/kev-27b@af0e6d551bdc2cc724f3e9d7a8bee1cd4fb8f7bf`.
Its `head.pt` identifies `Qwen/Qwen3.8-27B` at
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` as the foundation, but supplies a
**learned full backbone**, rather than Kev-9B's adapter. The full checkpoint's
native text-backbone keys must load through `AutoModel`, without creating a
vocabulary head or replacing the learned weights with the foundation.

The shared local loader now supports both full and adapter pointer checkpoints,
checks foundation and checkpoint metadata, and retains the native encoder and
head. The capacity runner adds rank-16 all-linear LoRA to a full pointer
backbone and saves/reloads that adapter with the updated head. This remains
synthetic capacity measurement, not full-weight optimization or SHR fitting.
Reusable configurations preserve the existing v26 readout and its rotated
criteria, NF4 precision, 32 GiB process budget and 8 GiB system reserve.

The new native production-path test first failed on the old loader's missing
vocabulary-head weights. All 15 native loader/benchmark tests now pass,
including exact saved-weight checks, independent native pointer probabilities,
NF4 optimization and adapter/head reload. The shared CPU suite passed 147 tests
with 13 optional native/dependency skips. Initial fixture failures are retained:
the fixture needed a native Qwen tokenizer and BF16 loading that preserves
FP32 rotary buffers. The completed full-size capacity check follows below.

The same published checkpoint also received a BF16 inference control in
both option orders, using `diagnostic-kev27b-bf16.json` and
`diagnostic-kev27b-options-rotate-bf16.json`. These configurations change only
quantization and the declared process budget (72 GiB, with the same 8 GiB
reserve). This tests precision sensitivity without new downloads, teacher
generation or SHR fitting. The original service remains stopped.

### Kev-27B published-checkpoint results

Both NF4 orders completed 140 new valid single-attempt answers; both BF16
orders completed another 140. All retain the exact saved v26 prompt and input
hashes. Teacher agreement is diagnostic, not semantic gold or held-out
accuracy. These developmental inputs were not used for gradients.

| Native pointer path | Original agreement / reversal | Scope | Transfer | Total |
| --- | --- | --- | --- | --- |
| NF4, original order | 33/40; 19/20 | 5/8; 3/4 | 13/22; 10/11 | 51/70; 32/35 |
| NF4, rotated order | 34/40; 18/20 | 6/8; 2/4 | 11/22; 10/11 | 51/70; 30/35 |
| BF16, original order | 33/40; 19/20 | 5/8; 3/4 | 11/22; 10/11 | 49/70; 32/35 |
| BF16, rotated order | 33/40; 19/20 | 6/8; 2/4 | 10/22; 11/11 | 49/70; 32/35 |

NF4 rotation preserves 66/70 decisions, matching Kev-9B's order-stability
count. It changes `B02-forward`, `R05-forward`, `R10-forward` and `R13-reverse`.
The first two corrections leave their reversed inputs wrong. BF16 preserves
68/70 original-order NF4 decisions; `R10-forward` and `R13-forward` change from
Culture-parent answers to `neither`, reducing teacher agreement. BF16 rotation
preserves 68/70 decisions, changing `R05-forward` and `R13-reverse`. Its greater
order stability does not produce better teacher agreement. Reversal
consistency can include two consistently wrong answers.

The comparison with Kev-9B preserves 54/70 first-order decisions. Native agent
reviews reject the Kitchen work/Cooking containment, the omelette/activity
containment, the author restriction imported into an eating practice, and the
Culture/song-creation field-scope error. The
[v26 rule review](#rule-review-against-shr-single-v26) also rejects both
Culture/person `neither` answers using the explicit named-painter precedent.
Nine first-order transfer disagreements with the teacher belong to the related
Culture cluster; they are not nine independent failures. Prompt-grounded agent
assessments remain distinct from independently approved semantic gold.

Median first-order reported inference time is 2.883 seconds in NF4 and 2.599
seconds in BF16. Peak first-order CUDA allocation is approximately 14.65 GiB
and 48.29 GiB respectively. These are individual complete v26 requests, not
batched deployment throughput. Fresh-process loading takes several minutes.
Higher precision has not demonstrated a quality benefit on this evidence.

Native experiments are `kev27b-{part}-v1`,
`kev27b-options-rotate-{part}-v1`, and
`kev27b-options-rotate-teacher-{part}-v1`. The latter reuse all 70 rotated
answers with zero new attempts. `kev27b-vs-kev9-{part}-v1` similarly reuses
all 70 normal answers to preserve the direct cross-model comparison.
BF16 normal runs are `kev27b-bf16-{part}-v1`; their
`kev27b-bf16-vs-nf4-{part}-v1` views reuse all 70 answers. Config SHA values
are `d9acc421ef836666bc6acb93760efab20f6235bbfdaafae5d4b3082ae156bc57`
and `23c395a3105f6a7b57069372f1d2f45db029306d367319bb7bf54ca194e41bfd`
for NF4, and `59730cdf2b6201af9fcec7f143cd4e006a0383a233cfe77ff8d993f4fe96bfe2`
and `3d5fdb7f9f7b0ed33858833d7b475d7f9607ea509fe8958f152eb15eda823394`
for BF16. All live under the owned diagnostics history root. Their checkpoints,
configs, receipts and native reviews remain preserved.

The corresponding BF16 rotated and teacher-view experiments are
`kev27b-bf16-options-rotate-{part}-v1` and
`kev27b-bf16-options-rotate-teacher-{part}-v1`; teacher views reuse all 70
answers with zero new attempts. Their median reported inference time is 2.594
seconds. The two published Kev releases have different foundations and prior
training; this comparison does not isolate capacity or establish either
student's plateau after matched SHR supervision.

### Verified Kev-27B native capacity

The full native NF4 path passed LoRA/head updates, checkpoint save,
fresh-process reload and finite five-way inference at both batch sizes for
all three lengths. It trains 119,349,760 FP32 parameters, including a
2,621,952-parameter pointer head, with BF16 autocast. Rank-16 all-linear LoRA
is added over the **published learned full backbone**, while the learned head
continues training. The logical parameter total including LoRA/head is
25,743,949,824; no vocabulary head is created. K-bit preparation promotes
nonquantized base parameters to FP32. This does not perform full-weight
optimization or fit any SHR labels.

| Synthetic complete input | Seconds/update | Peak allocated GiB, training | Examples/sec, batch 8 | Peak allocated GiB, batch-8 inference |
| --- | ---: | ---: | ---: | ---: |
| 512 tokens | 4.134 | 19.02 | 1.005 | 18.52 |
| 2,048 tokens | 13.750 | 21.86 | 0.274 | 23.23 |
| 3,072 tokens | 19.954 | 23.77 | 0.177 | 26.36 |

Each length has one warmup and four measured updates, then five warmed
inference repetitions per shape. All losses and gradients are finite, and
the saved probe logits match after reload within `rtol=atol=1e-4`. Training
PID `1925879` and verification PID `1927821` are distinct and have exited.
Load/reload take 331.936/405.154 seconds; saving takes 3.731 seconds.
The 32 GiB allocator budget and 8 GiB system reserve remain intact. Available
system memory after the three training workloads is 94.33/91.44/87.13 GiB.
The original service remains stopped, and no other GPU worker is present.

Configuration is `distillation/benchmark-kev27b-nf4.json`. The fully verified
native report lives in `target/shr-student-diagnostics-v1/kev27b-training-v1/`
on GB10; the owned Anvil copy is `kev27b-training-v1-report.json`. Both have
SHA-256 `fd96bb797c67c8d740797f63be25b407a9ab004445506eb88e3d9bd612624dc9`.
All recorded source/config hashes match the owned checkout; the report also
binds native checkpoint files and upstream pointer source. Artifacts and
published model caches remain ignored and preserved.

The native stack and correct reference PyTorch causal convolution match the
earlier capacity path. Optimized causal convolution remains absent, so these
are current-stack observations. Kev-9B's earlier 512/2,048-token update times
were 1.467/4.774 seconds with the service resident. Kev-27B's measured update
times are about 2.8–2.9 times longer, with different service contention and
prior training. Hardware supports the larger warm start, but neither its
NF4 nor BF16 v26 decisions demonstrate a quality benefit for that cost.
Matched SHR supervision and independently reviewed evaluation remain the
useful next step; no final model choice is made by this benchmark.

## TRAIN pair preparation

The human authorized selecting and organizing complete TRAIN pair inputs and
reviewing existing diagnostic disagreements while the prompt remains unfinished.
The shared `subject_pairs` adapter now reads a hash-bound registry selection
directly; it does not require an accepted hierarchy, vectors or SHR answers.
It verifies the selected registry, its manifest and prepared split roster;
checks author separation; and retains original entry indices, post IDs,
subject numbers, authors, split membership and teacher provenance in evidence.
Original subject/context strings are rendered in full, with no truncation.
Only TRAIN entries are nominated. Embedded upstream paths are never followed.

The maintained [selection specification](distillation/shr-train-pair-selection-v1.json)
sets seed `SHR-TRAIN-PAIR-SELECTION-v1`, 128 families per rule, at most four
selected families per source note and eight per casefolded subject wording.
Cross-post equal-wording groups use one source-bound representative per note;
lexical postings above 64 occurrences are skipped. Hashed adjacent pairs avoid
quadratic enumeration within large groups. These are nomination controls,
not estimated deployment frequencies or balanced relation supervision.

| Nomination rule | Bounded candidate pairs | Selected families |
| --- | ---: | ---: |
| Saved SP parent/child links | 26,465 | 128 |
| Siblings under a saved SP parent | 7,131 | 128 |
| Same subject wording across notes | 3,363 | 128 |
| Cross-post lexical overlap | 36,846 | 128 |
| Hash-selected cross-post controls | 33,190 | 128 |

This selection produced 640 distinct families, each with an exact A/B reversal,
from 576 notes and 292 authors. The observed maximum is four families per note
and seven per subject wording. Nomination produced no SHR relation labels;
[the subsequent teacher pilot](#provisional-shr-single-v26-teacher-pilot)
supplies 40 provisional answers for 20 families. SP numbering, equal strings,
lexical matches and random controls cannot supply those answers. The existing
100 validation posts retain their 32-diagnostic/68-calibration
allocation; none is nominated here. No final-test content was reopened, and the
earlier input exposure remains disclosed in the dataset audit below.

```bash
python3 sse_multivector/experiment.py prepare \
  target/shr-student-pairs-v1/train-inputs \
  --spec sse_multivector/distillation/shr-train-pair-preparation-v1.json
```

The [preparation specification](distillation/shr-train-pair-preparation-v1.json)
uses **SHR-single-v26**, the approved reference still under development, and
copies the existing Kev-9B diagnostic runner settings. Preparing those inputs
is not approval to run the model or a final student decision. The original
1,280-case plan remains unrun; the separately authorized teacher pilot reuses
40 exact inputs in its own experiment. The native plan/report retain source hashes, code bindings,
nomination statistics, complete evidence and reversal family IDs. Generated
artifacts are ignored under `target/shr-student-pairs-v1/`; source specifications,
the reusable adapter, tests and these maintained records are committed.

Twenty native agent input reviews inspect four examples from each rule. Their
pending review verdicts describe input relevance, not semantic `uncertain`
targets. The samples include national/author/object restrictions, activity and
product distinctions, same-named entities in different contexts, shared-word
controls and unrelated-looking topics. Lexical overlap includes incidental
words such as heavy and resulting; it does not establish semantic proximity.
This collection does not establish aliases, all-five-relation coverage,
accepted multi-entry nodes, multilingual quality or a new evaluation split.

Nineteen additional native agent assessments review ten existing Kev-27B/Kev-9B
diagnostic families. They preserve prior reviews and receipts. Puzzlement scope,
kitchen restrictions, recording activity/products, Pollan attribution and
explicitly musical topics provide useful regressions. Food versus squirrel
attacks on tomatoes remains a rule question. The earlier Culture/person
uncertainty is corrected in the rule review below. These diagnostic assessments
assign no accepted training target. Reversal
failures in the recording and Culture/song-creation cases can be identified
without an independently accepted gold answer. Culture variants remain
correlated. Existing Kev-9B omelette and recipe-technique reviews were inspected
without new model calls. Detailed evidence is in the ignored
`target/shr-student-pairs-v1/diagnostic-review.md` and native experiment reviews.
The ignored Markdown is the earlier assessment snapshot; the appended native
reviews and current analysis below correct its Culture/person conclusion.

### Rule review against SHR-single-v26

The approved reference explicitly places **Mara Vale**, identified as a painter,
beneath **Visual art**. Its general-field rule includes works and ordinary
creative activities. Those instructions support **Culture / Jesus Molina**,
whose entry identifies a jazz musician: `a_parent_of_b` forward and
`b_parent_of_a` reverse. The prompt does not require every biographical fact
about the named creator to concern the broader field. The earlier agent
uncertainty missed this example.

All three relevant frozen experiment templates exactly match
[SHR-single-v26](../../oracle-mvp-shr-single-pair-v1/sse_multivector/shr_single_pair/SHR-single-v26.md),
SHA-256 `6d4fca680aef4f809eeb0a98a558159203df10b843876a4d11c5c1e1299771b4`,
and both orientations retain that example. Six appended native agent reviews
accept Kev-9B's two containment answers and reject Kev-27B's two `neither`
answers in its direct and Kev-9B comparison views. The experiments are
`kev-transfer-v2`, `kev27b-transfer-v1` and `kev27b-vs-kev9-transfer-v1`.
Earlier assessments and model receipts remain preserved. These are corrected
prompt-grounded assessments, not new inference, independent semantic gold or
evidence that the prompt is finished. Measured agreement totals are unchanged.

**Food / Squirrel attacks on tomatoes** has no equally direct precedent. Its
entries do not distinguish damage to tomato plants from eating edible produce.
Whether Food contains the complete crop-attack topic remains a requested scope
decision. Keep both directions unscored until that decision is resolved;
review uncertainty does not assign SHR's semantic `uncertain` label.

### Preparation checks

The minimal CLI test initially failed because registry-based pair selection
was unsupported. With the adapter, 140 shared experiment/selection/audit tests
pass, with six optional skips, using the existing isolated check environment.
The system Python lacked `tiktoken`; the cached check environment resolves it.
A mistyped test-module name also failed discovery before the corrected suite
passed. No production regression was hidden or worked around. Tests exercise
native preparation, deterministic selection, complete entry preservation,
reversal families, provenance bindings, source/wording caps and refusal of
changed hashes, validation selection, extra source paths and cross-split edges.

The remaining dependency is stable relation rules and reviewed SHR targets.
The prepared inputs can be reused under a later accepted prompt with
`prepare --from`; no prompt revision, target generation or fitting was done.

### SHR answer collection

The user authorized proceeding toward reviewed labels and matched training.
The existing `collect` command now supports complete saved `subject_pairs`
experiments without inference. It writes `relationships.json` with exact input
variables, complete original evidence, family/split identities, relation/reason
answers, source-bound reviews and receipts. Prompt templates are stored once
per hash rather than copied into each decision. Existing provenance records
the model settings and protects the source files, reviews and collection code.

Every exported answer remains provisional. A review verdict is distinct from
the semantic relation: rejecting a teacher's `neither` does not turn it into
`uncertain`. Collection preserves inconsistent reversals and separate prompt
versions for later review rather than repairing or combining their labels.
It refuses incomplete runs, unsupported relation/reason contracts, repeated
experiment/case identities and changed protected sources. No validation or
final-test population is selected or assigned a new role by this capability.

The minimal production CLI test first failed because SHR collection was
unsupported. Five CLI integration checks now cover identity preservation,
current/stale review bindings, semantic `uncertain`, refusal paths, unchanged
sources, conflicting reversals and separate prompt versions. Test fixtures
make no actual model calls. The prepared 1,280 real inputs still have no saved
answers; no teacher labels or trained student are supplied by this change.
Collection of that real unrun set fails as expected before publishing an output.
The experiment/selection, node-description, hierarchy-input and node-sorting
regression suites completed 163 tests: 157 passed, six optional skips.

The user subsequently approved generating and reviewing the 20-family pilot
under **SHR-single-v26**, documented below. The Food/crop-attack scope question
remains open; no pilot pair uses that disputed case. The next model-quality
comparison still requires broader reviewed targets and a separately defined
evaluation role.

### Provisional SHR-single-v26 teacher pilot

The [teacher specification](distillation/shr-train-teacher-pilot-v26.json) selects
the 20 previously input-reviewed TRAIN families, four from each nomination
rule, with both orientations. They cover 31 source notes and 25 authors.
Preparation verified that every complete input, context, evidence record,
rendered v26 prompt and input hash exactly matches the original nomination.
All source identities and frozen split membership remain intact.

The pilot used **GPT-6.1 Sol medium**, subscription SSE, concurrency two,
1,800-second timeouts and a 40-total-attempt limit. All 40 answers are valid,
with no failures, retries, answer reuse or unresolved cases. All 20 exact
reversals agree. This is consistency on selected development inputs, not
semantic accuracy or final prompt acceptance.

| Relation | Directed answers |
| --- | ---: |
| equivalent | 8 |
| a_parent_of_b | 4 |
| b_parent_of_a | 4 |
| neither | 24 |
| uncertain | 0 |

All 40 inputs, answers and reasons received attributed native agent reviews;
all are supported under v26. These assessments are not independent human gold
or acceptance of an SHR training corpus. The source notes remain TRAIN; no
validation or final-test data was selected, and no student fitting occurred.
The review preserves the explicit country/transfer restrictions, context-only
named-entity examples, the hashrate topic's growth-plus-stabilization conditions,
and the Writing/Flash fiction activity/product distinction. Shared subject
matter alone does not merge the two article assessments or the two trading
claims. The lexical and hash-selected cross-post controls are largely easy
unrelated topics; they do not establish difficult-negative coverage.

Native `collect` publishes all 40 provisional answers and their current reviews
under `target/shr-student-pairs-v1/teacher-pilot-v26-collected/`, retaining prompt,
source, receipt and review bindings. All eleven protected file hashes verify;
the original 1,280-case plan's hash is unchanged. Experiment artifacts, labels,
reviews and installed runner dependencies remain ignored. No source dataset or
other owner's worktree was edited.

Artifact bindings:

- Experiment: `target/shr-student-pairs-v1/teacher-pilot-v26/experiment.json`,
  SHA-256 `00a979c3636e335e282065abcbfff77415b06d83e35d1db3bd5a12775a9b4690`.
- Collected relationships: SHA-256
  `f953730f693469afb725aade97a2dfbdac6b68ed5a65e9605e9dcc04dade31e6`.
- Native reviews: SHA-256
  `a79d05481dc28bb84ad091dd322996773dd19435c8fd737b5cca9f184b9db1e0`.
- Native usage: 84,476 input tokens, 10,880 cached input tokens, 2,576 output
  tokens including 403 reasoning tokens. These are the runner's reported
  counters, not a subscription invoice or an assumed caching rate.

Initial preparation stopped before inference because this worktree lacked the
pinned runner dependencies. Installing them with
`nix shell nixpkgs#nodejs_24 --command npm ci --ignore-scripts` preserved the
package lock. Repeated native preparation and all input/receipt/collection
checks passed. No transport or retry implementation changed.

The user subsequently authorized preparing and reviewing the coverage extension
below. The singleton pilot still supplies no measured behavior on ambiguous
names or multi-entry groups.

### Coverage input preparation

The [coverage selection](distillation/shr-train-coverage-selection-v1.json)
names original TRAIN registry indices rather than copying or rewriting their
subject/context strings. The shared registry adapter now accepts explicit A/B
entry groups as well as bounded singleton nominations. Both paths use the same
source-hash, frozen-roster, author-separation and original-entry validation.
No upstream provenance path is followed. The explicit groups are diagnostic
inputs, not accepted hierarchy nodes or inferred memberships.

The [preparation specification](distillation/shr-train-coverage-preparation-v1.json)
uses the unchanged **SHR-single-v26** template and the previous pilot's
GPT-6.1 Sol medium runner settings. These settings do not authorize inference.
Native `prepare` produced 20 families and 60 complete unrun cases, retaining
35 distinct original entries from 27 TRAIN notes and 25 authors.

| Coverage purpose | Families | Cases including controls |
| --- | ---: | ---: |
| Different wording | 4 | 8 |
| Name ambiguity | 4 | 8 |
| Related-topic contrasts | 4 | 8 |
| Consistent multi-entry candidates | 4 | 20 |
| Deliberately conflicting multi-entry groups | 4 | 16 |
| Total | 20 | 60 |

The differently worded pairs compare Bitcoin/BTC-expanded wording, Lightning/
Bitcoin Lightning Network, short/full United States names and Photographs/Photos.
The ambiguity candidates include an unexplained numeric hashtag, an operation
whose type is omitted, America's geographical extent, and a football entry
whose own context omits its code. General knowledge may resolve some names;
these are candidates for review, not guaranteed `uncertain` targets.

The related-topic pairs preserve independent noncustodial/frictionless trading
qualifiers, attribution of the same view to different people, dated photography
versus a camera used in its context, and book recommendations versus writing.
The multi-entry controls propose consistent network, Bitcoin, mining and photo
topics, then deliberately mix different football codes, independent trading
qualifiers, photographic products with their field, and Bitcoin with mining.
Each conflicting group is constructed from unchanged real entries. Its role
does not imply that the source SP collection made that grouping or that such
groups occur at the same rate in deployment.

Every family has an exact A/B reversal. Multi-entry sides also receive a reverse
entry-order control; the two-sided Lightning case reverses each side separately
and both together. These controls retain one source-bound family identity and
are not independent samples. The adapter never enumerates all permutations or
all corpus pairs: it scans the permitted registry once, then renders at most
eight controls per specified pair. Limits are 10,000 explicit pairs and 64
entries per side; actual request context still needs its own budget review.
This panel uses at most three entries on a side.

All 60 exact native case views were checked against original entry indices,
identities, full subject/context strings and TRAIN membership. Native agent
input reviews record the purpose and any unresolved interpretation. Their
pending `uncertain` review verdict means no answer is approved; it is not a
semantic relation label. There are no model calls, receipts with answers,
new collected labels or student fitting in this phase. The existing 100
validation posts keep their 32-diagnostic/68-calibration roles and the final
200 remain sealed.

The original 1,280-case plan, 40-answer teacher pilot, its reviews and collected
answers are unchanged. All six new protected source-file hashes verify.
The ignored artifact directory is
`target/shr-student-pairs-v1/coverage-inputs-v1/`, with bindings:

- Experiment SHA-256
  `383ac64887f694f5f1b956bde3c3b60a19fc2e5bf3a81c660ac0d5bd91d4fa7f`.
- Native input-review SHA-256
  `bac646fffdd5744c472798fd7761ea0ec9a3fc3e33e668342577fa5d01551d60`.

The first production CLI test failed because explicit groups were unsupported.
Four new integration tests now exercise complete entry preservation,
reversal/order controls, TRAIN-only refusal, invalid indices and target fields,
duplicate families/IDs, and the existing saved-answer collector with grouped
inputs. The relevant regression run completed 167 tests: 161 passed and six
optional tests skipped. No provider calls occur in the fixtures.

The user subsequently authorized the teacher pilot using v79, documented below.
The original v26 preparation remains unrun, with its input reviews unchanged.

### Provisional SHR-single-v79 coverage pilot

The user chose **SHR-single-v79** following this agent's read-only check of newer
prompt-development evidence. V79 is that investigation's working experimental
prompt, with
replicated local gains and remaining broader consistency failures. The saved
30-pair focused v79/v94 comparison completed 60 answers per arm, with four
reversal conflicts in each. V94 has not established an improvement from that
count. Those are separate development inputs from this coverage panel; their
answers, reviews and prompt-owner files were not modified by this task.
The selection is a provisional teacher-pilot choice, not a completed prompt
acceptance gate or release decision.

The [v79 teacher specification](distillation/shr-train-teacher-coverage-v79.json)
uses the same frozen coverage selectors and previous runner settings:
**GPT-6.1 Sol medium**, subscription SSE, concurrency two, 1,800-second timeout,
and the relation/reason JSON contract. Native preparation compared all 60
inputs/evidence records to the original v26 preparation and found them exactly
unchanged. The v79 template SHA-256 is
`eab2ac5dcaa48c777f357aa5caeb99e36f01520e9640083dd9b6d847bf4294d8`.
The 120-attempt ceiling allowed the normal two-attempt provider-only recovery;
the actual run used **60 attempts for 60 valid new answers**, with zero failures,
retries, reuse or unresolved cases. No transport, retry or workflow code changed.

| Relation | Directed answers |
| --- | ---: |
| equivalent | 24 |
| a_parent_of_b | 2 |
| b_parent_of_a | 2 |
| neither | 8 |
| uncertain | 24 |

All 30 exact reversal pairs agree; all 20 additional reordered cases retain
their original-orientation relation. The differently worded and consistent
multi-entry equivalents retain the named entities/photographic-image scope.
Bitcoin contains the three-entry Bitcoin-mining activity in both entry orders.
All four related-topic contrasts remain neither: trading qualifiers, named
attributions, camera versus dated photography, and recommendation versus writing
preserve their separate meanings. All four name ambiguities and all four
constructed conflicting groups remain uncertain. These controls represent
20 families, not 60 independent examples or deployment frequencies.

Every exact case view, complete input, answer and reason received an attributed
native agent semantic review; all 60 current reviews support the saved decision
under v79. They do not establish independent human gold or approval of an SHR
training corpus. The source is still 35 original TRAIN entries from 27 notes
and 25 authors. No validation/final-test selection, student fitting or final
model decision occurred in that teacher phase. The separately authorized local
comparison below checks whether earlier v26 student rankings transfer to v79.

Native `collect` preserves all 60 answers, current reviews, prompt and original
source/split/receipt identities in
`target/shr-student-pairs-v1/teacher-coverage-v79-reviewed-collected/`.
All eleven protected source-file hashes verify. The original nomination plan,
coverage preparation/input reviews and v26 teacher pilot/collection are unchanged.
An earlier export was made before review writes finished: it contains all
60 answers but only 42 reviewed cases. It is preserved at
`target/shr-student-pairs-v1/teacher-coverage-v79-collected/` as a historical
snapshot; its review-file binding is superseded by the completed review history.
Use only the final reviewed collection for this pilot's complete evidence.
All experiment outputs and snapshots remain ignored.

Artifact bindings:

- Experiment: `target/shr-student-pairs-v1/teacher-coverage-v79/experiment.json`,
  SHA-256 `a4d3a222e4df20f06c5304b0c53dc116b2e8758b447f480a3cfea60372d638bb`.
- Native results: SHA-256
  `eb4252f796da09c208d186e22f1e09473bc72bbda60e09c7a81d586b67068124`.
- Native reviews: SHA-256
  `68844bd6653fd5a45790cdeb94abc4bf22a5cc5aabc8899cde916df1c54f1877`.
- Final collected relationships: SHA-256
  `38b9acf031f1db5cc318ee288ba80658c5617db35e35fc9be0e17081709f3bf7`.
- Final provenance: SHA-256
  `4bee94e0d0659744ebbd83875c84a17baf8ee0e64ffc64163fccb110208ee854`.

Native preparation, receipt validation, input/control checks, review bindings and
collection checks passed. The unchanged workflow's latest regression remains
167 tests: 161 passed and six optional skips; no new software behavior was added
in this phase. Native usage reports 34,104 input tokens, 165,888 cached input
tokens and 4,467 output tokens including 791 reasoning tokens. These are native
counters, not a subscription invoice; no paid fallback was used.

The user subsequently authorized the matched local diagnostic below. The extra
controls and semantic uncertainty improve coverage, but this TRAIN panel cannot
establish held-out accuracy. Prompt development, accepted training targets and
separately reviewed evaluation roles remain open.

## Provisional SHR-single-v79 published-checkpoint comparison

The user authorized comparing the previously benchmarked seven checkpoints on
these exact 60 v79 TRAIN cases. Native `prepare --from` freezes the completed
teacher experiment as baseline; all fourteen plans preserve the complete prompt,
inputs and evidence. Each checkpoint uses its unchanged pinned NF4 configuration
and both previous option orders. Native `run` is bounded to 60 new attempts per
experiment, concurrency one, with the loopback local runner. All 840 answers are
valid in one attempt each, with no failures, retries or reuse. No new teachers,
validation/final-test inputs, fitting, model downloads or paid providers were used.

| Checkpoint | Teacher agreement, two orders /60 | Original orientations /40 | A/B reversals /30 | Decisions unchanged by option rotation /60 | Reordered cases retaining original decision /20 |
| --- | --- | --- | --- | --- | --- |
| Qwen3.8-27B | 53; 53 | 37; 38 | 27; 28 | 57 | 18; 17 |
| Kev-27B | 53; 51 | 37; 36 | 29; 27 | 58 | 18; 18 |
| Kev-9B | 44; 40 | 27; 26 | 18; 14 | 52 | 16; 17 |
| Gemma 4 12B-it | 42; 40 | 30; 28 | 25; 27 | 56 | 18; 18 |
| Nimble-9B | 36; 37 | 25; 25 | 23; 22 | 52 | 17; 15 |
| Decider-4B | 36; 34 | 24; 23 | 23; 22 | 53 | 19; 19 |
| Qwen3.5-9B instruct | 33; 39 | 21; 27 | 17; 23 | 38 | 17; 18 |

The 40 original orientations are two directions for each of 20 families. The
additional 20 cases test entry order, so all 60 are not independent samples.
The source remains 35 TRAIN entries from 27 notes and 25 authors. Constructed
conflict groups are diagnostic inputs, not accepted hierarchy nodes. Teachers
and reviews remain provisional; these scores measure agreement, not held-out
accuracy or quality after SHR finetuning.

| Checkpoint | Families with both original directions agreeing /20, two option orders |
| --- | --- |
| Qwen3.8-27B | 18; 19 |
| Kev-27B | 18; 17 |
| Kev-9B | 10; 9 |
| Gemma 4 12B-it | 13; 13 |
| Nimble-9B | 11; 11 |
| Decider-4B | 11; 10 |
| Qwen3.5-9B instruct | 9; 12 |

Both 27B checkpoints match all 36 non-uncertain teacher answers in both option
orders. Their seven first-order misses are all uncertain cases; five overlap,
including all four differently qualified trading cases. Qwen-27B's two-order
agreement is at least as competitive as the larger pointer model's. Neither
native readout has established superiority after matched SHR supervision.

The compact models have different weaknesses. Gemma matches 29/32 original
orientations outside the intentionally conflicting groups in its first order,
versus Kev-9B's 21/32. Inside those groups, Kev matches 6/8 and Gemma 1/8.
Kev-9B also has weaker reversals and misses the Lightning alias in one direction.
Nimble and Decider each match only 4/24 uncertain answers in their first order.
Qwen-9B reverses both clear Bitcoin/mining reverse cases in its first order;
only 38/60 decisions survive option rotation. Thus no compact checkpoint is a
uniform quality winner across the earlier v26 and current v79 diagnostics.

Nine native agent reviews assess exact case evidence: eight reject observed
alias, scope, attribution, consistency or directional errors; one accepts
Kev-27B's mixed-football uncertainty. All are attributed assessments under
provisional v79, not independent human gold or approved supervision. Gemma's
Bitcoin/mining conflict error has about 0.9997 conditional option probability;
a simple low-score cutoff would not catch it. These scores are not calibrated
semantic confidence. Qwen-27B repeats the inconsistent-trading error through
a different readout, so it is not a demonstrated pointer-specific defect.

The Kev-9B lead on the earlier 70 v26 development cases does not transfer to
this panel. That comparison changes both prompt and cases; it cannot attribute
the difference solely to v79, model size or architecture. The two Kev releases
also have different foundations and published training histories. No measured
post-finetuning plateau or final student choice follows from these results.

| Checkpoint | Complete input tokens | Median native seconds/case, two orders | Maximum allocated CUDA GiB |
| --- | --- | --- | --- |
| Qwen3.8-27B | 3,633–3,729 | 3.852; 3.848 | 17.21 |
| Kev-27B | 3,593–3,689 | 3.771; 3.803 | 14.84 |
| Kev-9B | 3,593–3,689 | 1.844; 1.844 | 6.10 |
| Gemma 4 12B-it | 3,662–3,759 | 2.563; 2.556 | 7.64 |
| Nimble-9B | 4,719–4,820 | 2.176; 2.176 | 7.97 |
| Decider-4B | 3,605–3,701 | 0.856; 0.860 | 3.40 |
| Qwen3.5-9B instruct | 3,633–3,729 | 1.278; 1.274 | 7.66 |

The separate service is stopped throughout, unlike some earlier compact-model
capacity runs. Cold loads take minutes and are separate from these inference
timings. All complete inputs fit their unchanged 8,192-token limits without
truncation. Nimble's schema overhead increases its token count. These are
published-checkpoint/readout measurements, not a matched architecture speed
ranking or a forecast for a distilled model receiving shorter pair-only inputs.
Complete v79 inference does not extend the earlier synthetic training-capacity
checks to these longer sequences or establish convergence.

Artifacts live under `target/shr-student-diagnostics-v79/`. Native experiments
are `experiments/{qwen27b,kev27b,kev9b,gemma12b,nimble9b,decider4b,qwen9b}-{original,rotate}-v1`;
each retains its frozen `experiment.json`, `run/manifest.json`,
`run/results.jsonl`, native report and any reviews. The source configurations
remain the existing `distillation/diagnostic-*.json` files: checked chat answer
prefixes for Qwen/Gemma, native schema for Nimble, native plain layout for
Decider and native pointer heads for Kev. No rendered batches or comparison
JSON were manually assembled. Receipt bindings:

| Experiment prefix | Original results SHA-256 | Rotated results SHA-256 |
| --- | --- | --- |
| qwen27b | `cb0d8f52e2b1637a8f0f6d06f7ba94d215b3a123895aa49552103a8e690d43de` | `d9052f5c5c5966ad8a449a329cf46a16cbcd2bd8e8fba17a226de1b816451d84` |
| kev27b | `a9e00a78ca29b94c5d7b34ef245c3fbba9d02a1cad247f11bbb5061b025d89af` | `9a68f20c100107383255a05b9229ce2c103975bf344a494896476985692cdcee` |
| kev9b | `80a1fb94627f6b9ae5a7623d1098e8d3d7d64e4c5b0259c3be0b47fb4238c4d1` | `a1acdd20bc2a50ed69fb0f0113c58f98436b9200520361956217998f27b25b74` |
| gemma12b | `394657057a3e9666089189d7332a223630f3619084be6b01bec5e93fbd851602` | `02f6b02f340d13dc7a5b92e60b94876e9b8cf3bb767c942d59c2c070c4f5df07` |
| nimble9b | `84387e1d026ccaf1a0545f3abf69fd923b44ade1e244c020a4c0d777a322ad4f` | `2706690fc72faf91ff7fe466996cca707650c38b5c013551ce11d4ee431a0357` |
| decider4b | `9dc1deb517e08bc39e5e8b44b080fc6de622f141ad3c9cab1501573cbe8f1560` | `0ef669e4fe2b7f3af62e3cb31c64c5fea72c85dadc83409e1982ddf35e082936` |
| qwen9b | `f5005d0688e3f8e8011ff7a1048426029c45abb43c182c5ad6cbe770079a1e2d` | `e0761922a1ed479969fc65191238e1591e2c6a75f9a7a2739961b2d5335d3ba6` |

Source configuration hashes and all five shared model-loading files match the
isolated GB10 checkout before calls. Final verification checks all 840 succeeded,
single-HTTP-attempt receipts; all fourteen native reports; each plan digest,
frozen source case/prompt/preparation, local provider and NF4 metadata; current
code hashes and six protected input source bindings. The source teacher plan,
results and reviews remain byte-identical to the preceding pilot. The unchanged
workflow's earlier passing regression remains applicable; this follow-up adds
no software behavior or accepted training targets. The initial orchestration
check read a nonexistent `counts` key instead of native `summary`; correcting
that check preserved completed answers without rerunning them. One review
command needed corrected shell quoting before native review succeeded.

All experiment workers stopped. GB10 reports no
compute process and about 118 GiB system availability; its isolated checkout
remains clean. 
Checkpoint commit `88e6082b` preserves the first three-model findings; this
completed panel supersedes its pending status without changing earlier evidence.

The most useful next preparation is reusable real-data SHR relation-only
training support for the shortlisted native pointer, standard LM and encoder
paths. `distillation_run.load_data` currently accepts only `subjects` or
`subjects`/`mask`, so the synthetic capacity checks and offline SHR collector
do not yet constitute a real SHR fitting workflow. This engineering dependency
can be removed while prompt development continues. Subsequent matched fitting
should retain a larger quality reference, the compact Kev/Base comparison and
the cheap Ettin arm, with source-bound targets and separately reviewed evaluation
roles. That next implementation/fitting is proposed, not begun or authorized by
this diagnostic; accepted training targets and the final student remain open.

## Dataset audit

The immutable ASv6.100 bundle is at
`oracle-mvp/target/distillation-pilot-v1/pilot-data-asv6.100-20261004/`.
The source review confirmed its provenance
and read-only reuse boundary. SP teachers are **ASv6.100 / GPT-6.1 Sol medium**;
ASv6.48 is historical. The split remains 1,000 training, 100 validation and
200 reserved final-test posts. All final-test content, SP/MP answers, embeddings
and student outputs are sealed. Roster metadata does not permit opening those
records, and selection files must not be followed into mixed source files.

**Exposure record:** before this boundary handoff, the first mechanical audit
read all 1,300 source posts and the input-only final-test prompts. It did not
open final-test teacher answers or student outputs, or judge their semantic
quality. The ignored original `data-audit.json` preserves that run; it is not
evidence of untouched final-test content. No further final-test content was
opened. The revised audit below uses only the authenticated 1,100-post VC15
registry and saved training/validation prompts. Final-test content exposure
must remain disclosed in any later evaluation claim.

```bash
python3 -m sse_multivector.distillation_audit \
  --registry ../oracle-mvp-vector-hierarchy-v1/target/subject-collection-vectors-v1/VC15-asv6.100-subject-vectors-v1/inputs.json \
  --prepared ../oracle-mvp/target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared \
  --output target/shr-student-prep-v1/data-audit-selected-v2.json
```

The audit validates posts through the shared input adapter and training answers
through the production subject parser. It checks registry/output hashes, frozen
membership and order, complete instruction/post preservation, author separation
and duplicate content **within training/validation**. The instruction hash
identifies the saved post boundary; each recovered post must match its VC15
text hash. The audit opens the registry, its adjacent manifest, the prepared
manifest, `train.jsonl` and `evaluation.jsonl`. It never follows source pointers
or opens mixed notes/labels, `test.jsonl`, validation references or student
outputs. The supplied registry contains validation SP entries; those are
allowed source inputs, and are not scored as SHR evaluation answers.

| Split | Notes | Authors | Median post characters | Maximum post characters |
| --- | ---: | ---: | ---: | ---: |
| Training | 1,000 | 458 | 261 | 1,707 |
| Validation | 100 | 78 | 191 | 1,605 |

The reserved final-test roster contains 200 IDs; the revised audit reports
only their count. Training and validation have no author overlap or exact
whitespace-normalized content duplication. A bounded inverted-index search
examined 3,584 nominated pairs within these two partitions and found no
word-5-shingle Jaccard similarity of at least 0.8. Five overly common shingles
were skipped; this heuristic is not an exhaustive near-duplicate or pretraining
contamination check.

The **training** partition supplies 33,234 SP subject/context entries:

| Inventory | Result | What it can establish |
| --- | ---: | --- |
| Entries per note | median 28; p95 76; maximum 145 | Several scope levels are available within many posts. |
| Parent/child candidates from SP numbering | 26,465 | Places to seek SHR comparisons; SP numbering is not an SHR answer. |
| Casefolded subject strings recurring across notes | 991 groups | Cross-post equivalence/polysemy candidates, requiring semantic review. |
| Exactly repeated subject/context across notes | 42 groups | Candidate duplication; text identity alone does not establish node membership. |
| Entry JSON characters, subject and context only | median 175; p95 320; maximum 559 | Capacity can be tested with complete entries; these are not model token counts. |
| SHR relation labels in the prepared SP training bundle | 0 | SP supervision does not supply five-way SHR targets. |

The deployment relation frequencies, multi-entry group lengths, aliases, conflicting
meanings and false-parent difficulty are **unknown**. They cannot be inferred
from SP answer counts. English, short, natural notes limit language/length
coverage; this corpus does not establish multilingual or long-input quality.
Dataset-derived development pairs can initially use only training notes.
The existing vector comparison reserves 32 validation query posts for its
diagnostic pilot and uses the remaining 68 for separate calibration. Reusing
that evidence must preserve this layout. A different SHR evaluation split or
label role requires a separate scope decision; this proposal does not assign
validation records to fitting or selection.

The handoff identifies **VC16** as 256 inspected diagnostic judgments on 32
complete eight-candidate lists: 20 candidate-parent, 21 query-parent,
4 equivalent, 210 neither and 1 uncertain. These are existing diagnostics,
not training labels, gold or final accuracy; no duplicate pilot calls are
needed. The separately nominated training collection remains incomplete:
4,096 frozen nominations, 3,136 returned answers and 960 unanswered, with
no strict `relationships.json` published. The approved recovery is pending;
the separately approved 1,024-question calibration is not a returned-label
corpus. Counts, partial receipts, missing answers and validation judgments
cannot substitute for completed training targets.

The VC15 registry inventories 36,030 SP occurrences (33,234 training / 2,796
validation) and 28,651 local links (26,465 / 2,186). Its existing 14,416 unique
768D wording encodings need no regeneration. If reused later, encoding IDs
must map through saved receipt ordinals; entry index is not the vector row.
The optional normalized bank is input data, not a trained student. This audit
does not read or transform either vector bank or any MP-mask inventory.

Artifact identity:

- VC15 manifest SHA-256: `c2c34d54fe77cb3a6bfe2efdb84e53a5cd89d26fa12983c2534daf714ee83d2d`.
- VC15 inputs SHA-256: `85d97e6b36493f3726b7869e9b98ab6905bf629c05ca1f2f68332345fa95d696`.
- Prepared manifest SHA-256 and each opened file hash are recorded in the
  selected audit artifact, along with the exact source paths. Both VC15 hashes
  match the owner's handoff. Mixed source hashes are provenance only; their
  content is not reopened to verify them.
- Training SHA-256: `f166371c5051b2ea95eb9591510544ade59ef8b1ef3b94826ed4baab92d1e681`.

## Evaluation design

This is a proposed protocol, not a frozen test set or accepted numerical gate.
The purpose is to test whether relation-only inference builds useful hierarchy
nodes, and whether a cheaper student can replace a larger one without damaging
that behavior. SP's full-hierarchy JSON generation is a different output task;
its student winner need not win these comparisons.

Keep two collections distinct. Prompt-development examples, including the v26
examples and any cases already used to revise prompts, are regression cases.
They are useful for diagnosing errors but cannot provide a clean final accuracy
claim. An independent corpus-derived collection measures generalization after
the prompt's rules stabilize. Preserve source-note IDs, author IDs, complete
subject/context entries, nomination method, and prompt/label revision for every
case using `experiment.py prepare` and its shared adapters. Add missing reusable
preparation support there; do not hand-build rendered experiment batches.

Split source families before generating comparisons. Every original comparison,
its A/B reversal, context controls, paraphrases, duplicated entries and all
multi-entry variants belong to one partition. Keep connected source notes and
authors together. Record repeated subject strings across partitions rather than
declaring all shared words leakage: common topics need to generalize. Also keep
an unseen-topic-family slice to test reliance on memorized entities. Never move
cases between partitions because a student gets them wrong. This proposed
family split does not supersede the existing VC16 32/68 validation layout or
the sealed final-test boundary described above.

| Case family | Concrete change to test | What to report |
| --- | --- | --- |
| Both parent directions | Books/Bookshops; reverse A and B | Directional confusion and reversal agreement. |
| Equivalent wording | Different names for the same meaning, versus the same name for different meanings | Equivalence precision and recall. |
| Context-only restriction | Steel context mentions a fork; subject still names Steel | False parent/equivalence decisions after context changes. |
| Explicit subject limits | Add/remove an author, purpose, exclusion or relationship in the subject | Accuracy on the contrast and its unchanged companion. |
| Whole-field scope | Literature versus Artistic creation | False containment caused by comparing only the shared activity. |
| Activities and products | Making sound effects versus Sound effects | Preserve the named activity/product distinction. |
| Multiple entries | Consistent synonyms versus Bread baking combined with Loaves of bread | `uncertain` recall for actual conflicts; entry-order agreement. |
| Missing meaning | An unresolved hashtag versus an identified name | Semantic `uncertain` accuracy, separately from low confidence. |
| Related neighbours | Shared materials, places or purposes without containment | False positive rates for equivalence and each parent direction. |
| Input robustness | Duplicate/reorder entries; quoted instructions in context; complete long groups | Agreement, invalid outputs and rejected/overlength inputs. |

Nominate pairs from SP edges, recurring subjects, shared siblings, local
hierarchy mistakes and unrelated controls. Report accuracy separately by
nomination source. A balanced diagnostic panel reveals rare-label errors;
a held-out sample from the actual nomination distribution estimates deployment
behavior. Do not confuse either with all possible pairs. No corpus-wide
quadratic pair enumeration is needed.

After rules stabilize, teachers may supply relation labels and diagnostic
reasons. Independently review a stratified sample and disagreements to detect
teacher mistakes. Store provisional/accepted/disputed status separately from
the relation. A disputed example is not automatically an `uncertain` example.
Preserve teacher probabilities only when the provider actually supplies them;
do not invent soft targets from reasons or disagreement counts.

Compare students on the same accepted cases and training budget. Start with
relation-only targets. Add diagnostic-reason supervision as an ablation only
if it improves held-out relations enough to justify the extra training or
inference cost. Encoder NLI labels and confidence cannot be mapped directly to
SHR's five relations. A fixed-task encoder may take complete A/B entries alone;
an LM may use the instruction prompt and direct label scoring. Report these
input contracts explicitly, plus full-token coverage and overlength exclusions.

Measure per-label precision/recall, macro-F1, deployment-weighted accuracy,
parent-direction confusion, reversal/order agreement, and calibration of
confidence separately from semantic `uncertain`. Use paired resampling over
source families for model differences, not independent resampling of variants.
Record inference batch size, complete input-token distribution, examples/sec,
latency and peak memory. An inference implementation that scores one token is
already one forward pass; adding a classifier head alone does not prove a
large speed advantage.

Finally, replay the same bounded hierarchy construction with each candidate's
relations: inspect incorrect merges, incorrect parent placements, incompatible
ancestry and reader-visible topic scope. Good pair scores alone do not accept
a student. Numerical tolerances and final model choice remain user decisions.

## GB10 feasibility checks

The GB10 test system runs Ubuntu 24.04.4,
ARM64, Python 3.12.3 and NVIDIA driver 580.173.02. On initial inspection its
Qwen3.8 Flash Next serving process occupied 95,896 MiB, while system available
memory was about 22 GiB. NVIDIA's unified-memory GPU reports total/used GPU
memory as unavailable; record system availability as well as PyTorch peaks.

Preparation
and appropriately bounded small-model checks can proceed without a pause.

Use an isolated environment and ignored artifacts within the owned checkout;
do not change the serving container, global Python or authentication. First
verify CUDA matmul/backward on the actual ARM64 wheel. Then measure model load,
a short optimization, checkpoint save/reload agreement and batched inference.
Synthetic token workloads can measure capacity before labels are ready; they
must be labelled as hardware checks, with no SHR quality or convergence claim.
Installation/download/first-kernel times and steady optimization times are
separate measurements. Co-resident serving means throughput is not an idle
machine estimate. No projected full-training time should be reported without
stating its dataset size, input lengths, batch and measured step count.

The compact feasibility order is Ettin-400M for the environment smoke check,
Ettin-1B and the DeBERTa NLI warm start for encoder comparisons, then a 9B
language-model path when memory permits. The 400M check does not replace the
1B quality candidate. Kev's custom head needs its own validated training path;
a Qwen backbone timing cannot be reported as a tested Kev implementation.
Larger quality controls remain candidates regardless of a 96 GB threshold.

The reusable capacity command is:

```bash
python3 -m sse_multivector.distillation_benchmark \
  --config sse_multivector/distillation/benchmark-ettin400m.json \
  --output target/shr-student-prep-v1/ettin400m
```

Pinned configurations also cover Ettin-1B full/LoRA, the DeBERTa warm start,
and Qwen3.5-9B-Base LoRA. The benchmark admits runs only when available system
memory exceeds its declared budget plus reserve, caps this process's CUDA
allocator, and checks the reserve between workloads. Encoder full training uses
FP32 parameters/AdamW states with BF16 autocast; these numbers must not be
described as a BF16-parameter or quantized training run. LoRA uses rank 16.
The five-column DeBERTa output replaces its original NLI head, as SHR requires
five relations. Causal-LM loading and LoRA reuse `distillation_run`; it needs
the existing FLA CUDA dependency before a Qwen training check can run.

Every accepted run requires finite nonzero gradients, checkpoint hash recording,
reload-logit agreement and finite five-column batched outputs. Failed admission
does not download or load model weights. Benchmark output includes cold-load,
warmup/steady optimization, save/reload and inference timings separately.
An explicit NF4 Qwen configuration tests whether the 9B path can coexist with
serving. This is a different precision experiment from BF16 LoRA, not a silent
change to that configuration or an assertion that their quality is equal.

### Measured results, 2026-10-05

These runs used the live GB10 with its existing server still resident. The
workload has synthetic IDs and cyclic five-way targets; it tests execution,
not SHR accuracy or convergence. Each length used one warmup update and four
measured updates, batch size one, gradient checkpointing, BF16 autocast and
AdamW. Inference values below are medians of five warmed batches of eight at
512 tokens. No tokenizer, prompt-rendering, request transport or data-loading
time is included in those inference values.

| Model/path | Seconds/update, 512 tokens | Peak allocated GiB, training | Examples/sec, batch 8, 512 tokens | Save/reload and five-way inference |
| --- | ---: | ---: | ---: | --- |
| Ettin-400M, full FP32 | 0.249 | 7.44 | 56.9 | Passed |
| Ettin-1B, FP32 base plus LoRA | 0.196 | 4.26 | 18.1 | Passed |
| DeBERTa NLI warm start, full FP32 and new five-way head | 0.408 | 8.17 | 23.0 | Passed |
| Qwen3.5-9B-Base, NF4 plus FP32 LoRA | 1.021 | 8.08 | 4.2 | Passed |

Ettin-1B's quicker optimization than Ettin-400M here is **not** a controlled
model-size comparison: it trains 11.65 million parameters through LoRA, whereas
the 400M run updates all 395.84 million. DeBERTa updates 435.07 million.
The original NLI output head is replaced rather than mapped to SHR labels.
The Ettin runs also passed complete 2,048-token training and inference; training
took 0.457 sec/update for 400M and 0.755 sec/update for 1B LoRA. Their peaks at
that length were 7.44 and 4.75 GiB respectively. DeBERTa is limited to 512
positions. These are short capacity samples, not full training-time forecasts.

The FP32 Ettin-1B full-training configuration correctly refused admission while
the server was resident: it reserves a 20 GiB process budget plus 8 GiB for
other work. This established contention in that window, not a GB10 hardware limit.
BF16 Qwen-9B similarly has an intentionally larger admission budget. Those
original configurations have not passed a training run. The subsequent paused
Ettin full-training check above passes with a fresh 32 GiB configuration.
Qwen-9B NF4 passed all requested
checks, including 3,072-token training and batches of eight at that length,
while the original serving process stayed resident. No service pause was needed.

For the longer Qwen workload, optimization took 4.830 sec/update with a 9.38 GiB
peak; batch-eight inference produced 0.77 examples/sec with a 10.65 GiB peak.
The run used the correct reference PyTorch causal-convolution implementation
because the optional `causal_conv1d` optimized kernel was absent. These are
measurements of that path, not an optimized Qwen throughput ceiling. Native FLA
CUDA kernels were present. Compilation/setup contributed 38.2 sec to the first
256-token update and 17.0 sec to the first 3,072-token update; those times are
recorded separately from steady updates. NF4 results do not establish equal
quality to BF16 training or validate Kev's separate decision head.

Evidence remains ignored under `target/shr-student-prep-v1/`; report identities:

- `ettin400m-report.json`: `eda0742300d8becc27ba435fc2f69ca51f6f254e66de8f4f4061b226186ed0b3`.
- `ettin1b-lora-report.json`: `98e2a1587a84752ba98cf36e0474978a66bbdad3136b5e2a1650f21372a10b37`.
- `deberta-report.json`: `cd6723c6e211b37aed39019f381216e147aa19256a282f0ecd20022ee78d9137`.
- `qwen9b-nf4-report.json`: `0f36d462a687629e2eaa45ff44e454c8adfd3ecb3eed38667711358125c28d1e`.

Each report contains exact per-step/per-batch timings, loss/gradient checks,
model/config/code identities, package versions and checkpoint file hashes.
Cold load timings include uncached downloads where needed: 7.6 sec (400M),
139.0 sec (1B), 18.7 sec (DeBERTa). They are not an architecture comparison.
Save/reload took 20.1/8.8, 1.2/14.6 and 15.5/13.2 sec respectively.
Qwen's weights were downloaded before its load timer: load/save/reload took
55.2/2.0/59.6 sec. Its original report's `parameters.total` counts packed tensor
elements, not logical four-bit parameters. A subsequent tested metadata fix
uses PEFT's logical count and records stored tensor elements separately; the
original measurement artifact is unchanged. Its 43.28 million trainable
parameter count is unaffected.

### Isolated GB10 environment

The working directory on GB10 is an isolated execution checkout at the same
absolute path as the Anvil worktree. Its shallow snapshot preserves source
bytes; imported commit IDs differ because parent history was omitted. Model
revisions and file hashes, rather than assuming those commit IDs match, bind
benchmark evidence to source. Nothing in the serving repository was changed.

The verified native stack is Python 3.12.3, `torch==2.12.1+cu130`,
`transformers==5.17.0`, `peft==0.21.0`, `accelerate==1.15.0` and
`fla-core==0.5.2`. The explicit four-bit trial adds `bitsandbytes==0.50.2`.
The [official CUDA-13 PyTorch index](https://download.pytorch.org/whl/cu130/torch/)
provided the ARM64 wheel. BF16 CUDA matmul/backward passed on SM 12.1, and FLA's
gated-delta CUDA forward/backward passed as a separate environment check.

The host lacks Python development headers. FLA imported with a CPU fallback
until the headers were available, so a successful import alone was insufficient.
Download/extract `libpython3.12-dev` inside ignored artifacts and set `CPATH`
to its `usr/include` and `usr/include/python3.12` directories. No privileged
installation is needed. The initial ModernBERT run also exposed an obsolete
`reference_compile` loader option; removing that option restored native loading.
Both failed artifacts are preserved separately from the accepted runs.

Use this layout to reproduce the environment, from the execution checkout:

```bash
python3 -m venv target/shr-student-prep-v1/venv
target/shr-student-prep-v1/venv/bin/python -m pip install \
  --cache-dir target/shr-student-prep-v1/pip-cache \
  torch==2.12.1 --index-url https://download.pytorch.org/whl/cu130
target/shr-student-prep-v1/venv/bin/python -m pip install \
  --cache-dir target/shr-student-prep-v1/pip-cache \
  transformers==5.17.0 peft==0.21.0 accelerate==1.15.0 \
  fla-core==0.5.2 bitsandbytes==0.50.2
```

Keep `HF_HOME`, `TRITON_CACHE_DIR`, `TORCHINDUCTOR_CACHE_DIR` and scratch
`TMPDIR` within `target/shr-student-prep-v1/`. For the Qwen check, include the
extracted-header `CPATH`. Pin every model download to the configuration's
revision. Record the resolved environment; the saved `requirements-resolved`
artifact is evidence of this run, not a universal ARM/CUDA environment lock.

Repository validation after the selected-source audit change: 17
audit/data/benchmark tests passed; the CUDA test was skipped in the local CPU
environment. The new boundary test first failed because the original auditor
required the mixed source. It now passes with the mixed source, final-test
prompts, combined labels and validation references absent, and rejects any
attempt to open those paths. The revised production CLI also completed on the
authenticated 1,100-post registry. The full shared
experiment suite passed 115 tests with six optional-dependency skips after
`tiktoken` was installed in an isolated check environment. The original
missing-dependency failure is recorded separately from this passing run.
A separate CUDA integration test uses a small native Qwen model through the
same benchmark loader, NF4/LoRA optimization, checkpoint save/reload and batched
five-way inference. It also checks logical versus packed parameter counting;
enable it with `RUN_BENCHMARK_GPU_TESTS=1` on the GPU environment. It requires
CUDA. All six benchmark tests passed with the GPU integration enabled. The
existing serving process retained PID 3440281 and its `/health` endpoint
returned HTTP 200 after the runs.
