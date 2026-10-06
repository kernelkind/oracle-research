# SHR student preparation while the prompt is unfinished

The user authorized three preparation tasks: GB10 feasibility checks, evaluation
design, and an audit of the existing 1,300-note corpus. Work lives on
`research/shr-student-prep-v1`, in `oracle-mvp-shr-student-prep-v1`.
SHR-single-v26 remains the user-approved prompt reference. No final student,
new prompt, SHR teacher labels, paid run, or release-plan decision is approved
by these preparation results. See [model research](SHR-FINETUNING-MODEL-RESEARCH.md).

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
other work. This establishes current contention, not a GB10 hardware limit.
BF16 Qwen-9B similarly has an intentionally larger admission budget. Those
configurations have not passed a training run. Qwen-9B NF4 passed all requested
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
