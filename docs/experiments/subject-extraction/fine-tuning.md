# Subject fine-tuning: methods and results

The pilot compared **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B** on learning
per-post subject hierarchies from ASv6.100 teacher answers. It trained subjects
only, with thinking off and no masks. All 1,800 validation answers and 1,200
reserved-test answers received correctness and coverage grades.

The current hierarchy generator uses **L1, the roots of each note's local SP
hierarchy**, so the L1-only comparison is the directly relevant extraction
result. The full-hierarchy evaluation and later thinking screen answer separate
questions. None establishes the quality of the resulting global hierarchy.

For commands, use the [training guide](../reproduce.md#run-subject-fine-tuning)
and [saved comparison guide](../reproduce.md#inspect-the-fine-tune-comparison).
This document records the experiments' methods and measured outcomes.

All 17 evaluated adapters are in the
[subject-adapter repository](https://huggingface.co/KernelKind/oracle-subject-adapters).
Prepared training inputs and saved evaluation results are part of the
[research dataset](https://huggingface.co/datasets/KernelKind/oracle-research),
whose private upload is in progress.

## L1-only test results (October 15)

This is an offline slice of the saved
grades on the **same 200 previously examined ASv6.100 test notes**, with no new
model calls, student generation or semantic judgments. It includes each family's
untuned baseline and final one-pass adapter, plus the validation-selected Qwen
pass-3 adapter. Qwen pass 2's test collection remains sealed.

L1 entries have numbers without a dot, such as `1` and `2`; `1.1` is excluded.
This matches the current hierarchy generator's original local L1 inventory.
Local roots need not have equal generality across notes or remain roots of the
global hierarchy.

- **L1 correctness:** supported returned L1 entries divided by returned L1
  entries, using the existing subject-support judgments. L1 has no incoming
  parent relationship to grade. A supported root can be correct without matching
  a teacher root.
- **All-root completeness:** teacher meaning groups containing at least one
  L1 entry that have an equivalent returned L1 entry, divided by all such groups.
  This includes broad roots marked optional in the full-hierarchy grader.
- **Required-root completeness:** the same calculation restricted to those
  root meaning groups already marked required. Existing meaning groups and
  required flags are preserved; duplicate teacher meanings count once.

Matching uses the accepted saved DSM equivalence judgments, including mechanical
exact-wording matches. A matching L2-or-deeper entry does not count. This slice
measures whether a meaning appears at L1; it excludes the full-hierarchy check
that the meaning appears beneath every compatible heading. The all-root view
measures coverage of the teacher's root choices; it does not make every optional
generalization mandatory.

All percentages are arithmetic means of per-note fractions over **all 200 notes**.
Invalid outputs score zero on both metrics. The one valid empty untuned-Qwen
answer also scores zero: the note has teacher roots and no returned roots.

| Model and checkpoint | L1 correctness | All-root completeness | Required-root completeness | Invalid outputs |
| --- | ---: | ---: | ---: | ---: |
| Qwen3.8-27B untuned | 66.96% | 42.12% | 58.13% | 43 |
| Qwen3.8-27B pass 1 / checkpoint 1,000 | 96.08% | 61.63% | 79.39% | 2 |
| Qwen3.8-27B selected pass 3 / checkpoint 3,000 | 97.51% | 57.07% | 76.99% | 0 |
| Gemma 4 31B dense untuned | 93.69% | 46.21% | 65.22% | 3 |
| Gemma 4 31B dense pass 1 / checkpoint 1,000 | 96.55% | 55.03% | 70.49% | 2 |
| Gemma 4 26B-A4B MoE untuned | 88.04% | 42.90% | 55.97% | 5 |
| Gemma 4 26B-A4B MoE pass 1 / checkpoint 1,000 | 89.81% | 55.75% | 73.64% | 11 |

The reference contains **1,293 root meaning groups**, of which **512 are
required**. All 200 notes have teacher roots, but **34 have no required root
meaning**. Following the existing empty-denominator rule, a valid answer scores
100% required-root completeness on those 34 notes; an invalid answer still scores
zero. To expose that effect, the same required-root metric averaged only over
the **166 notes with at least one required root** is:

| Model and checkpoint | Required-root completeness, 166-note subset |
| --- | ---: |
| Qwen3.8-27B untuned | 51.96% |
| Qwen3.8-27B pass 1 | 75.17% |
| Qwen3.8-27B selected pass 3 | 72.28% |
| Gemma 4 31B dense untuned | 58.10% |
| Gemma 4 31B dense pass 1 | 64.45% |
| Gemma 4 26B-A4B MoE untuned | 47.55% |
| Gemma 4 26B-A4B MoE pass 1 | 68.84% |

Qwen pass 1 has the highest observed L1 completeness under both denominators.
The extra two Qwen passes raise observed L1 correctness by **1.43 percentage
points**, while all-root completeness falls **4.56 points** and required-root
completeness falls **2.41 points**. Pass 3 returns 1,302 L1 entries across these
notes, versus pass 1's 1,430. This retrospective test slice does not revise the
checkpoint selection made on validation or establish production adoption.
The full-hierarchy measurements remain useful separate evidence.

The existing test reports retain their original source seals:
`test-1200/automatic/grades.json` SHA-256
`d6d040c9f2f98e1a2ce17827132efc679cfdffab0ccdb70221783424ab0146f6`,
and selected pass 3 SHA-256
`b146863c978675a72a9493f0046862e2efa83f088e27006ddedb44a7461157b8`.
The ignored per-note analysis and verification receipts are retained in
`oracle-mvp-qwen-continuation-grading-v1/target/pilot-l1-results-v1/` as
`analysis.json` and `verification.json`; the analysis SHA-256 is
`00606286eb66dbc8e3c3a54662bad102ffacc43d0fc30875dff6139aa284cc9d`.
The original source, policy and provider-receipt paths refer to the frozen
grading worktrees and runners. No additional GPU resource was used.

The [training instructions](../reproduce.md#run-subject-fine-tuning)
describe repeating the pilot recipes and continuing a reader's own Qwen run;
their offline input checks passed, while fresh GPU execution remains untested.

## 1. Freeze shared inputs — locally

The frozen dataset contains **1,000 training, 100 validation and 200 test notes**
from the fresh English corpus. Selection extended a deterministic random hash
draw: readable English root posts, no quote/reply tags or inline references to
other notes, and at most 512 SSE tokens in the full original text. Ordinary short
and difficult posts remained eligible. Authors and related copies stayed in one
split; known prompt-development authors went into training. All 16 writing forms
occur in the full sample, but the natural draw left no CREATIVE-form validation
notes.

The source corpus's recorded acquisition/filter counts were:

| Stage | Records |
| --- | ---: |
| Nine-relay kind-1 acquisition, September 24, 2025–July 24, 2026 | 15,782,558 |
| Root/non-quote and length filtering | 11,595,958 |
| Exact-content deduplication | 9,108,872 |
| English-or-language-neutral classification | 3,774,156 |
| Same pool with usable text, source of the frozen 1,000-note sample | 3,510,335 |

These are acquisition receipts' counts, not manually certified English labels or
the size of the published experiment sample. The separate older April 2025
Damus archive had 3,530,470 English-or-language-neutral posts. Original source
receipts are `damus_snapshot/runs/crec-105-fresh-corpus-v9/derivation/derivation-ledger.json`
and its `publication/10m-adcf8f016f6a-v1/global-deduplicated/manifest.json` and
`publication/10m-adcf8f016f6a-v1/english-eligible/manifest.json`. The usable-text
sample provenance is `semantic_map/crec-120-sample-v1/manifest.json`; the older
pool is recorded in
`damus_snapshot/runs/crec-9-complete-cpu-audit-v6/work/english-eligible/manifest.json`.
These original artifact references lie outside this checkout; see
[publication availability](../README.md#reading-the-research-records).

All 1,300 teacher answers used full
[ASv6.100](../../../sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md),
including its examples, with **GPT-6.1 Sol / medium**. Labels passed structural
and native-receipt checks; this was not independent semantic verification.
Original responses, parsed hierarchies and receipts are preserved.

The longest actual training example requires **18,396 tokens**. Some teacher
answers exceed 4,096 output tokens and seven exceed 128 nodes. The experiment
therefore used a **20,480-token context**, **10,240-token output allowance** and
no node-count cap for subjects-only parsing. Complete prompts, notes and teacher
answers were retained. Efficient CUDA attention and fused training loss were
checked against the native computation before training.

## 2. Generate untuned baselines — Vast

Each untuned model generated thinking-off answers on the same 100 validation
and 200 reserved-test notes before any main training. Each model retained one
frozen batching policy for baseline and trained evaluation. Batch admission
accounted for resident weights, padded input, caches through the output allowance,
temporary buffers and headroom; receipts preserve the actual batches.

Raw responses were reparsed and checked against input and generation receipts.
Invalid or truncated model answers count as failures, rather than being retried
until a valid answer appears. Missing work or inconsistent parsing does not count
as a completed comparison. Reserved-test contents stayed sealed through
validation review and selection.

## 3. Continue training and evaluate checkpoints — Vast

Each student had one continuing training run, initialized once from the original
model. Each note supplied one **note → teacher subject hierarchy** example. The
first pass used every training example once, without replacement, in five
200-note blocks shuffled with seed **17**. Checkpoints at **200, 400, 600, 800
and 1,000** notes preserve adapter, optimizer, schedule and RNG state.

The next **eight examples formed one optimizer update**, allowing smaller
physical groups when memory required them. This gave **125 updates per model,
25 per block**. The training loss averaged prediction error over teacher-answer
and native turn-ending tokens, excluding prompts and padding. Longer answers
therefore contribute more supervised tokens within an update; there was no
extra per-answer or per-note weighting.

| Setting | Frozen value |
| --- | --- |
| Base and compute | Unquantized BF16 base; mixed precision computation |
| Adapter weights, gradients and optimizer | FP32 |
| Optimizer | AdamW, no weight decay, gradient clipping 1 |
| Learning rate | 0.0001, constant, no warmup |
| Ordinary LoRA | Rank 16, alpha 32, dropout 0, frozen biases, standard initialization |
| Gemma MoE routed experts | Rank 2, alpha 32; attention and shared MLP retain rank 16 / alpha 32 |
| Frozen weights | Original base and router weights |

At each milestone, evaluation loaded the saved adapter on a fresh BF16 base and
merged that evaluation copy. The same 100 validation notes were generated, then
the evaluation copy was discarded and the full training state restored. The
final 1,000-note checkpoint also generated 200 sealed test answers. Earlier
checkpoints generated validation only. These are modest one-pass recipes, not
established optima for each model family.

The completed pilot used two **96 GB RTX PRO 6000** cards: dense Gemma on GPU 0,
Qwen followed by Gemma MoE on GPU 1. Full CUDA preparation checked long-input
updates, loss/gradient agreement, save/reload/merge, generation and native cache
shapes. Successful maximum cache probes reserved **76.28 GiB for Qwen (seven
notes), 77.07 GiB for dense Gemma (one), and 76.80 GiB for MoE (five)** under the
88 GiB inference allowance.

### Preparation failures and measured limits

Earlier attempts did not start main baselines or training. They exposed:

- An inference allowance incorrectly applied as a training cutoff.
- A Gemma MoE gradient-reference mismatch. The diagnostic measured **0.294–0.321%**
  head-relative L2 error and 296 failing adapter-gradient elements out of
  156,119,040. The repaired check compares native/fused adapter gradients with
  the identical incoming head gradient and checks head gradients separately.
  It passed on CUDA without loosening tolerances.
- MoE's seven-note cache probe reserving **88.080 GiB** against an 88 GiB
  allowance, without OOM. Raising its inference workspace estimate from **4 to
  12 GiB** reduced the predicted maximum batch from seven to five, keeping the
  same total allowance and training recipe.
- Host DNS preventing SSH, an unsupported persistent-volume mount path, and a
  setup admission gate charging the full transfer allowance against a $1 bound.
  These failed before model work, rather than constituting model results.

The October 3 preparation used shorter **ASv6.48** inputs and cost **$3.376**,
including a failed attempt. Its brief timings do not predict the later full
ASv6.100 pilot. Full ASv6.100 CUDA preparation passed October 6.

The full main pilot's recorded GPU charge was **$133.907**, with **$0.888**
final backup-storage cost and **$16.361** posted working-storage charge. Earlier
preparation attempts and separate resources are not included in that GPU charge.
The two-card configuration was quoted at $2.8139/hour, with a 300 GB volume
at $0.0833/hour. These dated rates are not current rental quotes.

Early training measurements recorded Qwen's first two blocks at **34.9 and
33.2 minutes**, and dense Gemma's first block at **92.9 minutes**. Qwen validation
generation after 200 and 400 notes took **121.4 and 143.1 minutes**, versus
**128.1 minutes** untuned. Parsing failures were two at each checkpoint versus
13 untuned; both 400-note failures hit the output limit. These timings and format
counts precede semantic grading and do not estimate all stages' runtime.

## 4. Retrieve verified results — Vast to local

Progressive retrieval copied responses and checkpoints while training continued,
using bounded chunks and prioritizing small response files. Local verification
accounted for all three baselines, fifteen checkpoint evaluations, every saved
checkpoint and exact training-note coverage, and all six 200-note test
collections. Transfers preserved raw answers, batch receipts, frozen inputs and
file seals. A transfer alone was not evidence of experiment completeness.

## 5. Score and compare — locally, after the rental

The completed grader used **DSMv3** meaning matching, **DSSv2** subject support,
**DSLv10** parent–child validity and **DCSv1** coverage search. Role-specific
settings were Sol/high for matching, relationships and ordinary coverage,
Sol/medium for support, and Sol/xhigh for final conflicts. Model/checkpoint
identities stayed outside semantic requests. The post, full ASv6.100, trusted
teacher answer and candidate hierarchy bound each judgment.

- **Correctness** counts returned entries with valid subjects and incoming links.
- **Coverage** counts required teacher meanings preserved completely at every
  compatible returned heading occurrence. Optional broader headings are not
  mandatory; equivalent wording and valid extra headings are allowed.

Teacher meaning groups were fixed across versions. Code calculated per-note
fractions from explicit judgments and averaged notes equally. Invalid outputs
received zero on both metrics. A missing or incomplete reviewer judgment is
ungraded, rather than a model-output zero; missing output or a provenance
mismatch blocks evaluation. A correct empty answer passes, while an empty
answer to a required task scores zero. Exact teacher wording and actual trusted links
supplied mechanical decisions where sufficient; matching both endpoints alone
did not certify their relationship. Mechanical decisions, reused semantic
answers and new model calls retained separate provenance.

The [review study](../../../sse_multivector/distillation-review-v1/README.md)
contains prompt qualification, rejected approaches, reviewer controls and the
source-bound scoring procedure. Its intermediate reviewer drafts are not the
settings of the completed pilot.

## 6. Confirm on the final test

The final three adapters were compared with their untuned baselines on the same
200 reserved notes, after validation review. This evaluates the frozen recipes
after 1,000 training notes; it does not independently optimize each family's
training or establish generalization outside the selected corpus.

### Completed test grading (October 14)

The local run finished at approximately **09:37 EDT October 14**.
All **1,200 answers** cover the same **200 distinct notes**, with 200 answers
for each of the six family/version combinations. Every answer has finite
correctness and coverage grades. There are **zero manual reviews, pending
judgments or agent adjudications**. All **40,607 prepared semantic judgments**
are saved across **911 completed native batches** and 529 collections.

These are arithmetic mean answer scores. Invalid student outputs remain in
each denominator and receive both zeros under the approved policy.

| Distilled model family | Baseline correctness | Final correctness | Baseline coverage | Final coverage | Invalid outputs, baseline → final |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-27B | 62.4% | 88.4% | 22.4% | 44.7% | 43 → 2 |
| Gemma 4 31B dense | 86.0% | 88.5% | 32.2% | 40.8% | 3 → 2 |
| Gemma 4 26B-A4B MoE | 79.5% | 83.3% | 23.2% | 39.4% | 5 → 11 |

On the same paired notes, coverage improves by **22.3 percentage points for
Qwen, 8.6 for dense Gemma and 16.2 for MoE Gemma**. Qwen has the highest
observed final coverage; its correctness is nearly tied with dense Gemma.
These measurements compare the frozen final recipes, not alternative
checkpoints or each family's best possible training recipe. They do not
establish uncertainty intervals or independently certify the semantic grader.
The user subsequently selected Qwen for the continuation above. The full
training-data volume and production adoption remain separate decisions.

The teacher-only inventory covers all 200 contexts, with 2,094 required and
985 optional exact-wording groups. Optional groups retain explicit ASv6.100
generalization justifications; candidate answers supplied no requirement
labels. The frozen prompts are DSMv3, DSSv2, DSLv10 and DCSv1, using Sol/high
for matching, relationships and ordinary coverage, Sol/medium for support,
and Sol/xhigh for final conflicts. Trusted mechanical decisions take
precedence. Eligible repeated prefixes receive native warming; short prefixes
receive no artificial padding. All saved student answers and grading inputs
remain unchanged.

Grading required scheduling and transport repairs without changing the frozen
prompts, policy or model settings. The recorded scheduler microbenchmark reduced
critical CPU work from 27.89 to 16.73 ms; omitting unrelated inventory reduced sampled
per-batch history entries by 98.7%. Ready-request admission and temporary overload
recovery were also corrected. These are runtime observations, not changes in
semantic grading criteria.

The prompts, grading policy and model settings were frozen throughout these
runner repairs. Runner handovers preserved successful receipts before resuming.

All ready batches submitted immediately through shared 30-request admission.
The workload stayed inside a **32 GiB, zero-swap systemd boundary**. During
the coverage transition it reached that limit and reclaimed clean file cache;
monitoring recorded **zero OOM events**. Later HTTP/2 GOAWAY waves temporarily
reduced concurrency through the existing recovery policy and resumed
automatically. No speculative proxy or transport-policy change was made.
The initial launch was approximately 00:33 EDT and completion 09:37 EDT:
about **nine hours elapsed**, including repair handovers and provider waits.
This run does not establish the earlier eight-hour fresh-run target.

## Qwen continuation (October 14)

The completed continuation added **two complete passes over the same 1,000
training notes**, starting from Qwen's final checkpoint, including optimizer,
schedule and RNG state. It used one **96 GB RTX PRO 6000**. The frozen Qwen
revision, full ASv6.100, original splits, thinking-off policy, BF16 base,
FP32 rank-16/alpha-32 adapters, eight-example updates and constant 0.0001
learning rate stayed fixed. The original order was preserved; the additional
passes used shuffle seeds **18 and 19**.

| Version | Training-note uses | Distinct training notes | Total updates |
| --- | ---: | ---: | ---: |
| Pass 1 / checkpoint 1,000 | 1,000 | 1,000 | 125 |
| Pass 2 / checkpoint 2,000 | 2,000 | 1,000 | 250 |
| Pass 3 / checkpoint 3,000 | 3,000 | 1,000 | 375 |

The runtime used **PyTorch 2.12.1+cu130**. The continuation's actual tokenizer
check found a maximum complete training length of **18,114**, maximum answer
length of **8,452**, and maximum validation/test prompts of **9,608/9,584** tokens.
These are Qwen-specific counts; the three-family maximum above is different.

Recovery snapshots were saved every **16 updates / 128 notes**, retaining the
two latest verified copies on the volume outside normal result retrieval. Each
contains adapter, optimizer/schedule, RNG and exact consumed-note cursor, not the
base model. A replacement is synced and verified before the oldest copy is
removed; a corrupt newest copy falls back to the preceding valid checkpoint.
The saved Qwen checkpoint was **1,421,963,152 bytes**: two recoveries use about
2.8 GB, temporarily 4.3 GB while writing. The interrupted-pass rehearsal matched
uninterrupted adapter, Adam, schedule and RNG state exactly.

The Qwen-only cache contained **26 pinned files / 55,586,035,724 bytes**. Cache
admission included the largest temporary file and a **32 GiB** saved-work
reserve; model subprocesses then ran with Hub access disabled. The actual
continuation used a 150 GB local volume and 30 GB instance disk, on one 600 W
RTX PRO 6000 Server card with 193,450 MB host RAM. The dated quote was
$1.413889/hour plus $0.041667/hour for the volume. Cache identity, pinned file
hashes and saved checkpoint seals bound the package to its parent.

Both new checkpoints generated 100 validation and 200 sealed test answers:
**600 new answers**. Verification accounts for 250 additional updates, 2,000
note uses, complete checkpoint state, finite changed adapters, raw/parsed
answers, receipts and file seals. The saved conservative rental/transfer
estimate plus the full storage allowance was **$29.35**; this is not a final
invoice. Original evidence is
`oracle-mvp-qwen-continuation-v1/target/qwen-continuation-v1/launch-20261014/final-operation-verification.json`.

**Validation grading complete, October 15:** both new checkpoints have all
100 shared validation answers graded, using the original teacher requirements
and the same grading prompts and role-specific settings. The comparison uses the existing pass-1 report. Arithmetic means include every answer;
pass 2's two invalid outputs receive both zeros.

| Qwen version | Validation correctness | Validation coverage | Invalid outputs |
| --- | ---: | ---: | ---: |
| Pass 1 / checkpoint 1,000 | 85.71% | 45.81% | 0 |
| Pass 2 / checkpoint 2,000 | 87.96% | 44.77% | 2 |
| Pass 3 / checkpoint 3,000 | 88.87% | 47.95% | 0 |

Pass 3 has the highest observed means on both metrics and was selected at
**21:51:25 UTC October 15**, before opening its test answers. Against pass 1,
its validation gain is **3.16 correctness points and 2.14 coverage points**.
Paired note-bootstrap 95% percentile intervals are **−1.43 to +7.91** and
**−2.61 to +7.11 points**, respectively (20,000 resamples, seed 20261015).
These intervals describe variation across the 100 paired notes, exclude grader
uncertainty and include zero; validation does not establish a reliable gain.
In validation, two additional passes have not produced the large completeness
increase sought.

The fixed validation inventory contains **845 required meaning groups**.
Pass 1 covers **341** and pass 3 covers **347**: six additional groups across
the 100 notes. These pooled counts differ from the primary score, which
averages each note's coverage equally. Of pass 3's **498 uncovered groups**,
**390** have no recorded matching returned subject; **108** have matches but
missing required headings. These are saved grader findings, not new semantic
adjudications. This does not establish a new training recipe.

Artifacts remain under
`oracle-mvp-qwen-continuation-grading-v1/target/qwen-continuation-grading-v1/`:
`validation/automatic/grades.json`, `validation/completion-verification.json`,
`validation/paired-differences.txt`, `validation/coverage-findings.txt` and the
dated `checkpoint-selection.txt`.
The validation report SHA-256 is
`a9a5be338027fa052c864a3347d5f07b99f8bf98620c2cd8f898a5ce5b125206`.
The grading worktree is frozen at Oracle `dc8c43f6` and its isolated runner at
`36dfcf63`; original source, prompt and receipt paths refer to them.
Only pass 3's saved **200 test answers** were opened after checkpoint selection,
using the same 200 teacher policies as the original test grading. Pass 2's test
collection remains sealed. These previously examined notes are a reused
benchmark rather than a fresh final holdout.

**Selected test grading complete, October 15:** all **200 pass-3 answers** now
have both finite grades, with zero manual reviews or pending judgments. Compare
the existing pass-1 grades on exactly the same 200 note IDs; both old invalid
answers remain in the denominator at zero.

| Qwen version | Test correctness | Test coverage | Invalid outputs |
| --- | ---: | ---: | ---: |
| Pass 1 / checkpoint 1,000 | 88.41% | 44.72% | 2 |
| Pass 3 / checkpoint 3,000 | 91.18% | 44.62% | 0 |

The test coverage change is **−0.10 percentage points**, with a paired
note-bootstrap 95% interval of **−3.09 to +3.01 points**. Correctness increases
by **2.77 points**, with an interval of **+0.20 to +5.35 points**. These are
20,000 paired resamples with seed 20261015, excluding grader uncertainty.
The additional passes improve observed correctness without improving
completeness on this benchmark. Test results do not revise the validation-based
checkpoint selection or establish production approval; the larger completeness
goal remains unmet.

Test artifacts are under the same grading root:
`selected-test/automatic/grades.json`,
`selected-test/completion-verification.json`,
`selected-test/paired-differences.txt` and the observer/retry evidence.
The selected-test report SHA-256 is
`b146863c978675a72a9493f0046862e2efa83f088e27006ddedb44a7461157b8`.
Original absolute source and receipt paths refer to the frozen grading worktree
and runner. The reused test set does not provide a fresh holdout.

### Qwen thinking screen (October 14)

A seeded **20-note validation subset** compared thinking-off answers with a
separate thinking-on collection for Qwen's final 1,000-note adapter. Seed:
`Qwen-thinking-20-20261014`; original validation indices:
0, 6, 7, 14, 20, 34, 36, 41, 44, 51, 60, 68, 70, 71, 73, 74, 76, 91, 95, 96.
The base revision was `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, with BF16
weights and original ASv6.100 inputs. The same saved thinking-off grades supplied
the paired comparison. Reserved test notes were not used.

#### Generation failures and runtime measurements

The first greedy Transformers/SDPA launch ran for about **100 minutes** without
a completed batch and was stopped with no saved answers. A native
FlashAttention2 replacement reached **2.40 decode steps/second** over eight
rows after 78.65 seconds of prefill. It also stopped with zero saved answers.
Source inspection found repeated concatenation, cloning and gathering of the
growing full-attention cache; this was not a profiler-based attribution of the
whole slowdown. Failed kernel compatibility checks and stopped outputs remain
part of the experiment evidence.

On the GX10 unified-memory host, the Transformers mmap loader retained anonymous
CPU pages after transfer. The safetensors native **pread** path loaded the full
model in **53.5 seconds**, with bit-identical tensor checks and no mappings. The
later standard text-only merged export contained **851 BF16 tensors / 50.10 GiB**.
Its omitted 0.79 GiB MTP tensors were not used; MTP behavior was not tested.

The replacement used stock **vLLM 0.31.0 / Torch 2.13.0+cu130** in an isolated
ARM64 environment, native paged hybrid attention, BF16 model/cache precision,
FP32 recurrent state, one CPU thread, Triton attention/prefill and a native CUDA
GDN decode kernel. An identical four-layer hybrid fixture reproduced sixteen
greedy tokens with maximum selected-token log-probability difference 0.003969
and zero history-copy operations. An 8,192-token prefix trial reused 7,840 tokens
and matched uncached continuation.

| Benchmark | Steady output tokens/second | Scope |
| --- | ---: | --- |
| Eager, eight original 9,276–9,466-token prompts | 31.7 | 32 decode steps |
| Eager, eight synthetic 36,000-token contexts | 25.5 | 32 decode steps |
| Native decode-only CUDA graphs, original prompts | 32.3 | 256 checked full-model greedy tokens match; about 64 MiB extra reservation |
| Larger cache, eight original prompts | 32.2 | 16 decode steps |
| Larger cache, one 70,000-token context plus seven original prompts | 29.7 | 16 decode steps |

The initial vLLM pool was **22 GiB**, with **72.4 GiB** peak GPU reservation and
about 42 GiB host availability. The larger **40 GiB** pool reached **90.5 GiB**
reservation and about 24 GiB host availability, with zero benchmark preemptions;
all 128 checked greedy tokens matched. CUDA allocation was capped at **96 GiB**,
with a 96 GiB zero-swap process boundary and an independent **20 GiB
host-available watchdog**. These short benchmarks are not complete-answer timings
or graded answers.

The initial greedy policy imposed **16,384 thought tokens** and **10,240 final
tokens** in 40,960 context. It stopped after saving eight natural completions
and seven empty final answers at the thought cutoff. The next greedy policy
used natural EOS within **262,144 total context**, preserving the eight natural
answers. It later stopped with fifteen saved answers; five notes remained
unfinished. Notes 20 and 34 had each generated **159,427 tokens** without
completion. A cutoff or long unfinished answer does not by itself prove a loop.
Saved greedy records were not overwritten.

The separate sampled collection used **temperature 1.0, top_p 0.95, top_k 20,
min_p 0, presence_penalty 0 and repetition_penalty 1**, `xhigh`, natural EOS within
262,144 context, and the same weights and original prompts. These match the
[pinned model card's thinking sampler](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md#best-practices).
The native template's `xhigh` instruction does not itself assign a token bound.
The sampled collection reused no greedy answers.

The first two sampled notes completed naturally:

| Note | Thought tokens | Final tokens | Total tokens | Subjects | Elapsed generation seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 34 | 7,519 | 761 | 8,281 | 17 | 2,006.68 |
| 20 | 15,221 | 4,444 | 19,666 | 90 | 4,700.15 |

Both elapsed times share the session start. These two outcomes did not establish
a causal explanation or semantic quality; the later complete comparison follows.

**Twenty-note generation complete — October 15.** All twenty sampled answers
finish at natural EOS without truncation. The native completion marker matches
every answer hash; the earlier nineteen hashes remain unchanged as the last
answer arrives. CPU validation passes the frozen prompt, policy, runtime,
source, export metadata, token accounting and production output format checks.
The collection contains **260,554 thought tokens**, **40,770 final tokens** and
twenty closing-think tokens: **301,344 generated tokens**, **832 subjects** and
**zero format errors**.

| Session | New answers | Generation minutes | Observed active wall minutes |
| --- | ---: | ---: | ---: |
| Initial diagnostic | 2 | 78.34 | 80.73 |
| Remaining notes | 18 | 203.63 | 205.98 |

Generation time is the last saved answer's elapsed session time; wall time spans
the watchdog's first active and first inactive observations. Both sessions exit
successfully, with zero cache preemptions. Across **1,709** watchdog samples,
available host RAM stays above **23.18 GiB**; peak logged CUDA reservation is
**90.48 GiB**. No GPU compute process remains after exit. The ignored receipt
`target/qwen-thinking-20-sampled-20261015/full-validation.json` retains hashes,
per-note counts and session evidence. This validates provenance and format;
semantic grading results follow below.

The native `prepare-distillation-review-trial --saved-generations` importer
bound the complete cohort's input, answer and runtime hashes to the grader.

**Completed sampled comparison — October 15.** The existing automatic grader
finishes all **20/20** answers with valid correctness and coverage scores and
**zero manual reviews**. Means below use the same twenty notes and the original
1,000-note checkpoint's saved thinking-OFF answers:

| Metric | Thinking OFF | Sampled thinking ON | Change, percentage points |
| --- | ---: | ---: | ---: |
| Correctness | 86.78% | 83.35% | -3.42 |
| Coverage | 38.54% | 38.78% | +0.24 |

The native run records **1,232 questions in 72 batches**, including fourteen
final matching and two final coverage judgments. It exits successfully at
**19:34:32 UTC**, about ten minutes after launch. The largest captured grader
memory peak is **7.82 GiB** within its **32 GiB** boundary; minimum recorded host
availability is **104.23 GiB**, with no OOM or swap use. Native grades are retained
at `target/qwen-thinking-20-sampled-20261015/grading/automatic/grades.json`.

Native usage records **186 reused reviewer answers** and **1,135 attempts**,
including 36 failed attempts that all recover, with zero final failures.
Known fresh grading usage is **878,420 input
tokens**, of which **554,112 (63.08%)** are cached, and **284,783 output tokens**.
The known catalogue-cost subtotal is **$4.66**, excluding 36 attempts without
usage; this is not a reconciled provider charge. Source-provenance calls and
older reused work are not counted as new work in these token totals.

Sampled thinking uses **301,344 generated tokens**, versus **25,450** for the
paired OFF answers (**11.84 times** as many), and **4 hours 47 minutes** of summed
active GX10 wall time across the two sessions. On this screen, the additional
thinking compute does not improve mean correctness; this does not establish production adoption.

These exposed validation notes provide a small screen, not unseen-note
accuracy or proof that the full test exceeds 90%. Different generation hardware
and the changed thinking sampler prevent attributing every difference to
thinking alone.
Ignored artifacts are retained in
`oracle-mvp-qwen-thinking-gx10/target/qwen-thinking-20-20261014/` and
`gx10:/home/dev/experiments/qwen-thinking-20-20261014/`.

## Published evidence

The [saved comparison and adapter/training guide](../reproduce.md#inspect-the-fine-tune-comparison)
uses the selected compact results. [models.csv](../models.csv) identifies all 17
adapters and their original training/base-model bindings. Native worktree and
receipt names above identify original evidence, not additional reader downloads.

The unchanged result seals are:

| Result | SHA-256 |
| --- | --- |
| Original 1,200-answer test grading | `d6d040c9f2f98e1a2ce17827132efc679cfdffab0ccdb70221783424ab0146f6` |
| Qwen continuation validation | `a9a5be338027fa052c864a3347d5f07b99f8bf98620c2cd8f898a5ce5b125206` |
| Selected Qwen pass 3 test | `b146863c978675a72a9493f0046862e2efa83f088e27006ddedb44a7461157b8` |
| L1-only analysis | `00606286eb66dbc8e3c3a54662bad102ffacc43d0fc30875dff6139aa284cc9d` |
