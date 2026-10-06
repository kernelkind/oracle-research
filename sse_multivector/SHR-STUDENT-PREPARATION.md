# SHR student preparation while the prompt is unfinished

The user authorized three preparation tasks: GB10 feasibility checks, evaluation
design, and an audit of the existing 1,300-note corpus. Work lives on
`research/shr-student-prep-v1`, in `oracle-mvp-shr-student-prep-v1`.
SHR-single-v26 remains the user-approved prompt reference. No final student,
new prompt, SHR teacher labels, paid run, or release-plan decision is approved
by these preparation results. See [model research](SHR-FINETUNING-MODEL-RESEARCH.md).

## Current outcome, October 6

The authorized model investigation is complete enough to prioritize a matched
training comparison: Kev-9B and its actual Qwen Base control, with Ettin-1B as
the low-cost arm. Nimble-9B offers the standard LM adapter alternative; Gemma-12B
is the independent foundation. Six published checkpoints completed both
relation-only code orders on 70 developmental cases, alongside generated-output
controls and verified local capacity paths. See the consolidated
[recommendation and measured tables](SHR-FINETUNING-MODEL-RESEARCH.md#recommendation).
No post-finetuning winner is established. Suitable complete SHR training labels
and reviewed evaluation roles remain the next dependency; none of these
provisional cases was used for fitting. The final capacity check below closes
the larger Qwen reference, without expanding to additional model families.

Final read-only native `show` checks confirm that all six original-order paths
have identical case IDs, complete prompt text and input hashes, with 70 valid
single-attempt answers each. Their relation metrics match the consolidated
table. The last behavior-change regression suite reports 127 tests, OK with
10 optional skips; all six native weight tests pass on GB10. Historical failed
and unavailable checks remain recorded below. No behavior changes followed
those passing checks. All GPU experiment workers stopped.

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
treated a recipe step as necessary. Agent review leaves a broader field/person
judgment unresolved; agreement with that teacher answer is not acceptance of its
semantics. The reviewed cases and comments remain in native experiment files.

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
The Culture/person whole-topic judgment remains unresolved in agent review,
as it was for Kev. Teacher disagreement alone does not settle that judgment.

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
cluster, not twelve independent observations. The Culture/person judgment
remains unresolved; teacher disagreement alone is not semantic rejection.

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
far, without claiming order invariance or semantic accuracy. The Culture/person
teacher judgment remains unresolved in the existing agent review.

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
FP32 rotary buffers. Quality and full-size capacity results are pending.

The same published checkpoint will also receive a BF16 inference control in
both option orders, using `diagnostic-kev27b-bf16.json` and
`diagnostic-kev27b-options-rotate-bf16.json`. These configurations change only
quantization and the declared process budget (72 GiB, with the same 8 GiB
reserve). This tests precision sensitivity without new downloads, teacher
generation or SHR fitting. The original service remains stopped.

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
