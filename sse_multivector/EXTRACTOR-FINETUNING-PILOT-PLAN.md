# Fine-tuning pilot

For the experiment's sequence—shared data, untuned baselines, training,
evaluation, and model comparison—start with
[the pilot walkthrough](../docs/planning/fine-tuning-pilot-process.md).
Implementation and deployment details are recorded below.

## Status and scope

**Release-plan tracking:** the preliminary 100-note experiment below is task
**29 · Run preliminary 100-note fine-tuning experiment**, in progress. The larger
model-selection pilot is **06 · Choose model through larger fine-tuning pilot**,
waiting for its data in 05. The planned pilot includes a comparison trained on
1,000 notes, approved September 30. On October 1 the user requested three
continuing student training runs, replacing separate fresh starts at each size,
and approved validation checkpoints at 200, 400, 600, 800, and 1,000 training
notes. Validation/test counts remain open. Task 18's preliminary training setup
is complete; continuation across expanding datasets still needs implementation
and verification.
Task 29 needs 01 + 18, not the larger-pilot data
in 05, and its findings inform 06 without becoming a new completion gate.
Splitting the tracking does not change the experiments or spending approvals.

**October 1 preparation decision:** a separate paid GPU preparation step is agreed
in principle. Prepare candidate settings and agree on required GPU checks, then
rehearse the packaged workflow locally before booking. Test subject/mask output
limits with thinking off and on for completion, truncation, memory and runtime
on representative and long notes. Select and freeze limits after preparation,
before the larger pilot starts. Preparation scope, hardware, maximum charge, and launch
remain open.

**September 25: start an informal subject-and-mask pilot.** The user approved
using the data already on hand with the latest subject and mask prompts,
establishing untuned baselines and testing fine-tuning without prominence.
The user subsequently approved **one fine-tune per candidate, learning both
prompted tasks**. Subject examples pair ASv6.48 + the complete note with the
teacher's subject hierarchy. Mask examples pair MPv3.43 + the complete note +
one subject with the teacher's full mask response. Both tasks update the same
model or adapter. At evaluation, that model generates subjects first, then
runs the mask prompt for each of its own generated subjects. Establish the
untuned baseline with this same process. Direct-mask generation is deferred.
This first experiment can proceed while prominence and final teacher selection
remain unfinished. It does not select the release model or settle the larger
pilot's dataset sizes, training recipe, or spending allocation.

The available starting package is the refreshed 100-post collection, generated
with ASv6.48 and the frozen MPv3.43 working baseline using Astra low: 2,383
subject entries, 252 valid empty masks, and 1,674 distinct nonempty masks.
These are saved teacher outputs, not individually approved semantic labels.
The initial local preparation uses 80 training notes and 20 evaluation notes,
keeping same-author and identical-content notes together. The split is an
implementation choice for this informal experiment, not a new release gate.
Close paraphrases still require inspection before training.

The prepared training dataset contains **80 subject examples and 1,860 mask
examples**. The task prompts distinguish which answer the model should produce;
these are two tasks within one fine-tune, not separately trained models.
Subject responses retain numbering, context and subject text. Mask responses
retain meaning, expressible, evidence and word-position selections, including
valid empty results. The existing production mask-input preparation excludes
the teacher's diagnostic context from mask inputs. Equivalent source selections
are canonicalized without changing their selected text. No semantic repair or
deduplication across different subjects is applied to the training examples.
The frozen informal recipe samples 20% subject examples and 80% mask examples
with replacement, using the same seeded schedule for every candidate.

The superseded DPv1 draft has been removed. Its earlier ignored export at
`target/distillation-pilot-v1/data` is not the active dataset. The new export
below preserves exactly the same 80/20 note split and the original annotations.

Offline preparation is reproducible with:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 -m sse_multivector.distillation_data \
  --source sse_multivector/hierarchy-refresh-v1/source.json \
  --annotations sse_multivector/hierarchy-refresh-v1/masked-posts.json \
  --subject-prompt sse_multivector/subject-prompt-goal-v1/asv6.48/ASv6.48.md \
  --mask-prompt sse_multivector/mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md \
  --subject-prompt-id ASv6.48 \
  --mask-prompt-id MPv3.43 \
  --evaluation-notes 20 \
  --seed informal-pilot-v1 \
  --output target/distillation-pilot-v1/two-task-data
```

The destination must be new. The manifest records input/output hashes and
note IDs; evaluation starts with subject-prompt inputs containing no teacher
answers. Its mask inputs must use the candidate's generated subjects. Data stays ignored
under `target/`. Conversion checks every selection using the existing mask
decoder. The first rental stopped after a local monitoring error, before any
baseline output or training completed. Its files were retrieved and the instance
was deleted. After rebuilding and verifying the image, the user approved a
replacement rental. All three candidates completed their
20-note baseline attempts, 128-step training, matching adapter reloads and
20-note trained evaluations. The worker exited successfully on September 30 at
02:56:58 UTC.
Retrieval of 671 work files was hash-verified at 03:08:17 UTC; local output verification passed. This
verifies execution; semantic review and model selection remain open. Evidence
is in `target/distillation-pilot-v1/launch-20260929-v2/operation/`, including
`result/work/results/*/report.json`, `launch/retrieval-verification.json`,
`launch/destruction-confirmation.json` and `observations/`.

The note-sorting mechanism is still being developed. Whether the release model
needs prominence or other additional outputs is undecided. The requirements
below describe the larger evaluation and release decision; this informal
experiment's frozen subject/mask tasks remain unchanged. The user accepted the
proposed **$25 total maximum**
for GPU setup, untuned baselines and initial fine-tunes across the three
candidates. This includes storage, transfers and failed attempts, within the
existing lifetime cap. The informal settings and Vast limits below are frozen
locally; ledger admission is required before accepting any paid commitment.

This document contains our experimental plan, decisions, preparation findings,
and open questions. Published model evidence belongs in
[Model research](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md); published data-volume
evidence belongs in [Training-data research](SUBJECT-MASK-TRAINING-DATA-RESEARCH.md).

This pilot selects the model we will fine-tune and release (the distilled
model), not the teachers that write its training data. The separate
[teacher-comparison pilot](../docs/planning/release-decisions.md#two-separate-model-pilots)
has Muse Spark 1.3 Contributor as its leading, unselected candidate. Existing
[teacher research](TOKEN-USAGE-ESTIMATE-1M-NOTES.md#lower-cost-annotation-models)
and the [12-note subject diagnostic](frontier-model-comparison-v1/asv6.23-diagnostic-v2/results.md)
inform that choice; they do not establish mask or prominence quality.
The [teacher-comparison pilot](../docs/planning/release-decisions.md#teacher-comparison-pilot-evaluation-plan)
compares candidate subjects, masks, any agreed additional outputs and resulting
hierarchies, as well as generation speed, cost and training-data feasibility.
Its experimental procedure and treatment of unsuitable annotations remain open.
This fine-tuning pilot informs the training-volume decision and schedule check;
the teacher comparison does not determine how much training data the distilled
model needs.

Approved requirements:

- Compare Qwen3.8-27B, Gemma 4 31B instruction-tuned, and Gemma 4 26B-A4B
  instruction-tuned.
- Include a baseline without task-specific fine-tuning for every model.
- Check a small hierarchy built from pilot-model outputs before model selection,
  rather than leaving the first downstream check until after final training.
- Confirm permission to release fine-tuned weights during model selection (06),
  before committing to the larger training run. Training-data provider
  permissions remain part of the teacher-comparison pilot (17).
- Measure unseen-note quality before and after training, improvement as training
  data increases, actual training resources and cost, and batched generation
  speed. Evaluate masks and any agreed additional outputs; sorting-related
  model outputs remain undecided.
- Start automatic mask matching with an 80% token-overlap cutoff, alongside
  separate exact-match scores. Details are in [Evaluation and decisions](#evaluation-and-decisions).
- The total oracle MVP spending ceiling is $1,000, replacing—not supplementing—
  the old $500 ceiling. Existing spending and commitments still count.
- Protect the larger fine-tune's budget with a provisional pilot spending
  ceiling. See [Pilot budget](#pilot-budget--approved-approach); no amount or
  percentage is approved yet.

The staged experimental design below is only partly approved. The 1,000-note
training comparison and checkpoints every 200 notes are included; validation/test
counts, remaining training settings, hardware allocations, and individual spending
authorizations remain open for that larger design. The first informal rental below
started and was deleted on September 29 after the monitoring error recorded
below. No baseline or training completed.

The release plan's **18 · Prepare training code for the fine-tuning pilot** is
complete for setup: local VM rehearsals cover each candidate family, training,
interruption/resume, save/reload and SSH deployment. The image is published and
verified. Final training-example formatting and output-quality evaluation remain
in **06 · Choose model through larger fine-tuning pilot**, which needs the agreed
output format, quality criteria and reviewed pilot data to complete release-model
selection. Additional model outputs needed for sorting remain undecided.
Preliminary candidate execution and subject/mask quality review belong to 29,
not completion of 06. The informal
experiment above is authorized to begin preparation without prominence. The user subsequently
approved building and testing the automated workflow in a local VM before
deploying it on rented hardware. The implementation uses Transformers Trainer
and PEFT in a pinned PyTorch container. The user clarified that this must
rehearse deployment as previously done on Vast, with no manual code editing
on the rented server. Candidate training settings and Vast launch limits are
now frozen locally. On September 29 the user authorized publication and one
Vast rental, then approved up to $1.66/hour and 13 hours total within $25.
For that completed informal run, GPU compatibility was checked during its rental.
The larger pilot uses the separate preparation step agreed above.

### Frozen informal settings

The maintained configurations are [Qwen](distillation/qwen.json),
[Gemma dense](distillation/gemma-dense.json) and
[Gemma MoE](distillation/gemma-moe.json). Their exact checkpoint revisions are:

| Candidate | Hugging Face revision |
|---|---|
| `Qwen/Qwen3.8-27B` | `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` |
| `google/gemma-4-31B-it` | `842da3794eaa0b77d5f08bae87a17459d91ff475` |
| `google/gemma-4-26B-A4B-it` | `4d7ae4984b7db7de8f8457170b3f1a419ee76d52` |

All three use these starting settings. They are implementation choices for this
short experiment, not claims of optimal settings or the larger pilot's recipe.

| Setting | Value |
|---|---|
| Frozen base weights | BF16; no quantization |
| LoRA | Rank 16, alpha 32, dropout 0 |
| Updates | 128 optimizer steps; batch 1, accumulation 8 |
| Optimizer | AdamW; constant learning rate 0.0001, no warmup or weight decay; gradient clipping 1 |
| Task sampling | 20% subjects, 80% masks; seed 17; with replacement |
| Memory | Gradient checkpointing with `use_reentrant=False`; training KV cache disabled |
| Training context | 8,192 tokens; reject overlength examples |
| Generation | Greedy, thinking disabled; up to 4,096 subject tokens or 512 mask tokens |
| Evaluation batches | Generate subjects for one note, then up to four independent mask prompts per batch; identical settings before and after training |
| Subject limit | 128 per note; exceeding it is an evaluation failure |
| Checkpoints | Every 32 steps; retain two resumable checkpoints |

The seeded schedule draws **211 subject rows (74 distinct) and 813 mask rows
(659 distinct)**. This short run does not cover every row and is not one epoch.
The subject share gives the smaller task repeated exposure while most updates
still concern masks. Rank 16 and learning rate 0.0001 are conservative starting
choices; a single short run cannot determine the best recipe.

Adapters target attention and shared MLP projections. Qwen also adapts its
linear-attention projections. Gemma MoE's router and expert tensors remain
frozen; this tests that adapter recipe, not adaptation of every expert.
All candidates load their text model from the original multimodal checkpoint,
checking that every required text weight loaded. The image includes pinned
FLA Core 0.5.2 for Qwen's CUDA path in a separately locked package directory;
the runner adds that directory only for CUDA execution. CPU runs use the
reference implementation. The VM also checks that the CUDA functions import.
No optional compiled causal-convolution extension is required.

The user approved batching evaluation mask requests for efficiency. Each note's
subjects are generated first, then its mask prompts are processed in their
original order in groups of at most four (`mask_batch_size`). Training batch
size and accumulation are unchanged. Generation uses left padding with an
explicit attention mask; training retains right padding. Each answer stops at
its first model stop token, excluding later batch padding from decoding and
token counts. CPU checks compare single-request and batched answers on all
three tiny candidate architectures before and after adapter training. Full-size
GPU numerical equivalence, throughput and memory use remain unmeasured.

BF16 avoids uncertain quantization of Gemma's bare expert tensors. The selected
96 GB GPU provides room beyond the roughly 52–63 GB checkpoint weights, but
full-size training memory use and speed have not been measured. All three
candidates use the same precision, sampling schedule and evaluation process.

The actual pinned tokenizers pass preparation for all 1,940 rows and the 20
evaluation inputs. Maximum training lengths are 6,531 tokens for Qwen and
6,440 for both Gemmas; maximum saved subject answers are 3,370/3,352 tokens,
and mask answers 216/214. Generation allowances fit the evaluation inputs.
Training uses the exact thinking-disabled generation prefix, the saved answer,
and the native turn ending; only the answer and turn ending receive loss.
This handles Gemma's template, which inserts its empty thought channel into
generation prompts but omits it when rendering saved answers.

### Local VM workflow

**September 25 validation:** local workflow tests cover
real LoRA updates, exact weight equality after interruption/resume,
save/reload, valid and malformed outputs, empty masks, and exclusion of teacher
subjects from evaluation mask calls. Batching tests additionally cover left
padding, multiple stop tokens, output limits, stable answer ordering, partial
final batches and reuse after interruption. Earlier preparation also passed
87 extraction tests and 10 planning-viewer tests, including the Firefox check.
Candidate checks additionally exercise tiny versions of Qwen hybrid attention,
Gemma dense and Gemma MoE: original text-weight loading, real adapter updates,
gradient checkpointing and save/reload. The deployment rehearsal passed in a
fresh VM and passed again for the updated image: package verification,
two sequential runs, reconnect, completed-result reuse, failure retrieval and
runtime-limit enforcement. The SSH target received its inputs exclusively
through the production operator; it had no shared source or input volume.
**September 28 integration:** distillation now uses `vast/runner.py`, imported
from the successful September 27 grouping deployment (`bce43ef2`). The separate
distillation provider controller and SSH operator are removed. The shared runner
owns creation, key attachment, transfer, detached execution, result sealing,
retrieval and verified destruction. `distillation_deploy.py` only freezes inputs
and executes the candidate sequence; `distillation_vast.py` describes that work.
The model recipes, prompts, data, batching and $25 total maximum are unchanged.
The first published image reached Vast, but that rental ended before any
baseline or training completed. The rebuilt image is now published and verified
private; the approved 450 W replacement rental completed all three candidates'
baseline attempts, training, matching reloads and trained evaluations. Results were
retrieved and verified before explicit deletion. Semantic review remains outside
the completed setup task.

The failure audit reproduced empty successful destroy output, distinct live
and offer bundle IDs, and missing/null transfer counters in the old controller.
The shared implementation handles these cases, uses the exact selected quote
without depending on a second search, and confirms deletion with two complete
absent inventories. Billing estimates include elapsed rental and the full frozen
transfer allowance; missing counters or invoices never establish a zero charge.

Vast managed SSH replaces the image entrypoint. The launch uses the proven
`ssh-keygen -A && service ssh start` hook, explicit key attachment and the current
direct TCP 22 mapping. Local SSH ignores inherited configuration and is parsed
before creation. The workload selects the absolute venv Python and explicitly
sets PATH, the NVIDIA library path and Python import path. GPU packages resolve
from the interpreter prefix. The VM models the managed entrypoint override and
key attachment, then exercises the shared transfer/worker/retrieval code over
real SSH. It cannot reproduce Vast's provider infrastructure or prove GPU execution.

`target/distillation-pilot-v1/launch-preparation.json` records the current
exported image, `package-v9` and validation evidence. The September 29 rebuild
includes the manual-deletion policy and passed all 24 VM tests in
`target/distillation-vm-clean-deployment/attempt-1790699869508347098`.
It reused the VM disk and dependency cache with a new source snapshot. All
three candidate preflight reports, tiny-model adapter weights and evaluation
metrics match the previous rehearsal exactly. The VM is stopped. The rebuilt
image is published and verified private as
`docker.io/kernelkind/oracle-mvp@sha256:ec161e009f607fdeb6e714c525e1c8eae07a562cd4d205c2579ad9b65c72f0db`.
Source hashes, filesystem layers and runtime configuration match the VM export;
read-only rental credentials can pull the digest, and anonymous manifest access
returns HTTP 401. Evidence is under
`target/distillation-pilot-v1/launch-20260929-v2/publication/`.
Historical image/package receipts
are preserved; changed code requires a new image and package.
The previous image was published and verified on September 29 as
`docker.io/kernelkind/oracle-mvp@sha256:f6bafc128b7fed0eda387f56b34900bc794800cf9e38871b59a7c1679498f956`.
The registry config digest, filesystem layers, runtime configuration and source
hashes match the VM export. Read-only registry credentials successfully pulled
this immutable reference using cached local layers; this does not measure a
cold pull. VM containerd reports the manifest digest as its image ID, while
local legacy Docker reports the config digest; the publication receipt records
both. Full-size candidate execution was interrupted by the local monitoring
error below, before baseline output or training completed. Evidence is under
`target/distillation-pilot-v1/launch-20260929/`, including
`publication/publication-receipt.json`.
Validation passed 117 shared-controller tests, seven pinned-CLI checks and
24 VM tests, including actual candidate preflights and real SSH training/retrieval.
The tiny adapter weights and evaluation metrics match the earlier rehearsal.

Run from the repository root:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 -m sse_multivector.distillation_vm \
  --directory target/distillation-vm
```

The host needs QEMU, KVM access, `qemu-img`, `genisoimage`, SSH and SCP. It does
not need a Docker daemon or root access. A checksum-pinned Ubuntu image runs
Docker inside a VM with four virtual CPUs, 12 GiB RAM and a sparse 64 GiB disk.
SSH binds only to loopback. The package contains an explicit source-file list;
credentials and annotation artifacts are not copied into the build context. Each attempt gets
a source snapshot, serial/build logs and a result directory. Use a new
`--directory` for a clean-machine test; reusing it retains the stopped VM disk
and Docker cache. The launcher collects results and stops the VM on exit.

The container's CUDA/PyTorch base is pinned by digest, and Python dependencies
are version/hash locked. The same container runs CPU validation locally and
can later run on a GPU. Tests run with networking disabled, using a generated
tiny model and synthetic subject/mask examples. They exercise the real dataset
export, answer-only training, baseline generation, checkpointing, adapter
save/reload and two-step evaluation. The interruption test kills training,
resumes it and compares weights with an uninterrupted run. A successful VM run
exports `results/container.tar.gz` for local import and registry publication; the VM
disk, image, model weights, data and logs remain ignored under `target/`.

`distillation_deploy prepare --through preflight` freezes a package that only
checks tokenization and dependencies. For offline validation of real candidates,
use their cached pinned tokenizer directories as the local model paths; no full
weights are required. Pass that package to the VM with `--preflight-package`.
It runs through the same uploaded-package SSH path, on the actual pilot data.

The SSH target has no source checkout or shared input volume. The shared runner
uploads and verifies frozen inputs, starts a detached command, seals terminal
results, downloads them and verifies their hashes. Tests exercise two sequential
training jobs, failure logs, worker timeout, stop, completed-worker reuse and
actual candidate tokenizers on the pilot data. Provider lifecycle tests remain
local simulations; real CLI serialization is tested with only the paid API call
intercepted. No code edits or package installs belong on a rental.

Prepare the frozen candidate package locally. Filenames become run names;
the candidates execute sequentially in the order below:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 -m sse_multivector.distillation_deploy prepare \
  --config sse_multivector/distillation/qwen.json \
  --config sse_multivector/distillation/gemma-dense.json \
  --config sse_multivector/distillation/gemma-moe.json \
  --timeout-seconds 43200 \
  --output target/distillation-pilot-v1/package-v9
```

The output must be new. The package contains data, mask prompts, configurations
and optional local model files. Remote model IDs require immutable revisions.
Input paths are relative to the frozen package; the worker resolves them after upload.

After verifying publication, describe the workload with
`python3 -m sse_multivector.distillation_vast --package ... --offer ... --image ... --output ...`.
The offer file contains one selected, validated quote; the image must be a registry
digest. Freeze that specification with `python3 vast/package.py --spec ... --root ... --ledger ...`.
Run the copied `transport/control/vast_full_build.py` with `--root` and `--config`:
`prepare` checks local SSH, image and budget and writes an approval plan;
`run --approve HASH --watch` uses its committed reservation and supervises execution.
Bind the verified registry digest before freezing the operation.

`run --watch` repeatedly resumes the shared runner through execution and
retrieval. **Command workloads never automatically delete the instance.**
Successful and failed jobs retain the instance after retrieval. Startup failures
retain it without starting training. On expiry, controller errors or interruption,
the watcher requests a workload stop and attempts retrieval, preserving the
instance even when SSH or retrieval fails. The returned result reports that
billing remains possible and manual stop is recommended.

The explicit `stop` command stops the workload, retrieves available results and
**deletes the instance**, confirming absence twice. This is the command operator
action required to end the rental. A retained instance continues billing; stopping
the worker does not stop rental charges or enforce the $25 ceiling. Budget
admission, cost warnings and worker runtime limits remain in force.

The watcher preserves its first session deadline across restarts and leaves
15 minutes for retrieval and explicit deletion before the approved 13-hour
ceiling. An operator must act within that allowance. Run supervision in a
persistent local session; if the local process or host dies, an operator must
resume it. The worker separately enforces its frozen runtime limit across all
candidates and kills download/training subprocess groups on timeout or stop.
Application failures are retrieved without retrying training.

`distillation_run.py CONFIG --output DIRECTORY` performs baseline → training →
reload → evaluation → report. Invoke it as
`python -m sse_multivector.distillation_run` inside the container. Passing
`--through preflight` checks real tokenization without loading model weights;
`--through baseline` or `--through train` stops there. Repeating the same command
resumes. Config, input hashes, source hashes and library versions are frozen.
Changed settings require a new output directory. Completed calls, including
malformed responses, are preserved without automatic retries. Only fully
written checkpoints with verified hashes are eligible for training resume.
Mask answers are saved together in one atomic `masks-NNNN.json` file per batch,
including every prompt and one measured generation duration for the batch.
Resuming reuses the whole saved batch, including malformed and empty answers;
the final incomplete group can contain fewer than four requests.

Subject and position-mask decoding accept bare JSON or one complete Markdown
code fence labelled `json` (case-insensitive) or unlabelled. Existing field,
duplicate-key, hierarchy, verdict and position validation still apply. Raw
answers are retained. Parser changes do not rewrite a completed evaluation;
apply the same decoder to both baseline and trained answers in a separate
evaluation before comparing their scores.

The JSON config requires explicit model/revision, prepared-data and mask-prompt
paths; CPU/CUDA and none/NF4 quantization; seed, sequence and per-task output
limits, subject limit, steps, checkpoint interval, training batch size,
evaluation `mask_batch_size`, gradient
accumulation, learning rate, subject sampling fraction, LoRA rank/alpha/targets,
gradient checkpointing and CPU thread count. Remote models require a commit
revision. The tiny test's values are test-fixture
settings, not selected recipes for the three candidates. Sampling uses a seeded
schedule with the configured subject probability and records realized counts.
The candidate files specify the adapted projections. Overlength examples fail;
the runner does not truncate training answers.

The automatic report separates malformed subject/mask outputs, valid empty
masks and reference agreement. Token overlap uses whitespace-delimited source
words (any selected part includes that word), with one-to-one matching and
micro averaging over unique nonempty selections per note. Exact matching uses
selected non-whitespace source characters. These mechanical measurements do
not establish semantic correctness or approval; the semantic-review rubric remains open.

For the next pilot, response failures must be reported when they occur and
baseline coverage checked before training proceeds. The current evaluation
records failed notes and continues; a sealed directory can therefore lack mask
calls. The stronger reporting and stage checks in
[the walkthrough](../docs/planning/fine-tuning-pilot-process.md#2-generate-untuned-baselines--vast)
require implementation and verification. Semantic review of saved results runs
from the local workspace after retrieval, outside the GPU rental. The proposed
teacher reviewer is an evaluation method, not another fine-tune. The
[approved review structure](#semantic-review--approved-structure) uses one
prompt with separate correctness and coverage scores; its rubric, reviewer
model, and use in model selection remain open for design discussion.

CPU VM validation cannot establish candidate quality, CUDA kernel compatibility,
full-model memory requirements or speed. Those are checked during the actual
pilot; there is no separate throwaway GPU training run. The first attempt
reached Qwen weight loading, then the local monitoring error stopped it. No
baseline or training result is available.

### Vast launch configuration — first rental stopped

[The launch configuration](distillation/vast-launch.json) freezes the search,
create options and admission limits. It reuses the existing private Docker Hub
repository `docker.io/kernelkind/oracle-mvp`, with tag `distillation-pilot-v1`.
The eventual create command must use its published **registry digest**. The
local image ID is not a registry digest; one does not exist before publication.
The user lifted the publication hold on September 29. The launch-specific
`approved-settings-450w.json` in `launch-20260929-v2/` overrides the hourly
ceiling, total rental time and user-approved 450 W power requirement, with
matching search filters. The tested image and maintained source configuration
remain frozen; use this settings file for the replacement launch.

- One on-demand RTX PRO 6000 WS, 450 W, 96 GB; at least 128 GiB host RAM,
  eight effective CPU cores, 300 GB disk, direct SSH and NVIDIA driver 580.95.05.
- Run Qwen, Gemma dense and Gemma MoE sequentially in the same container.
  Downloads total approximately 170 GB before image/input transfers; keep the
  pinned Hugging Face weights cached on the instance for baseline, training
  and reload. Anonymous HEAD requests to one pinned weight shard per candidate
  returned HTTP 200 on September 25; no Hugging Face token is required by this setup.
- Maximum returned price **$1.66/hour including 300 GB storage**, for at most
  **13 hours from instance creation**. The worker gets up to 12 hours for all
  three runs including model downloads; setup and retrieval share the remaining
  hour. The session deadline takes priority if setup consumes that allowance.
- Transfer allowances: **200 GB inbound and 20 GB outbound**, each at no more
  than $0.01/GB. These are decimal GB. Maximum planned charge is
  `13 × $1.66 + 200 × $0.01 + 20 × $0.01 = $23.78`.
- The approved $25 covers the entire experiment, including failures. Any retry
  consumes its remaining allowance; it does not receive another $25. No retry,
  longer rental, larger disk or higher rate is authorized by these files.

A read-only September 25 search returned offer 44375763 at **$1.55/hour with
300 GB storage**. This is a quote, not a reservation; refresh it before launch.
The search's rate filter can be applied before storage is added, so validate
its returned total with the production checker:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
python3 -m sse_multivector.distillation_deploy check-offer \
  --settings sse_multivector/distillation/vast-launch.json \
  --offers target/distillation-pilot-v1/candidate-research/vast-offers.json \
  --offer-id 44375763
```

The checker verifies hardware, driver, availability, duration, storage-inclusive
price and the total allowance. It performs no paid action and does not establish
ledger admission. Refresh offers using the configuration's `search_query` and
`search_options`; refresh/check again immediately before accepting a rental.

For the authorized deployment: publish the exact VM-exported image,
select and validate an available quote, freeze the shared operation, and run
`prepare`. Reconcile the budget ledger, add its matching `vast_run_reservation`
(kind, plan SHA, operation evidence path, maximum charge 2500 cents, reserved
status), and commit before accepting the paid commitment. Local preparation
does not create a reservation. No replacement rental is authorized after a
failed run without discussing the failure with the user.

The shared runner uses the pinned Vast 1.4.1 CLI. The registry pull token enters
`gte/vast_private_create.py` through stdin from the local terminal; the Vast API
credential stays local. Creation is attempted at most once with `--cancel-unavail`;
an ambiguous reply is recovered from saved identity/label evidence, never by
renting a replacement. A live bundle ID need not equal the selected quote ID.
Hardware validation and cleanup ownership are separate, so rejecting hardware
does not prevent deleting the instance created by this operation.

Successful and failed command jobs lead to verified result retrieval while
retaining the instance. The explicit `stop` command performs deletion. The
shared runner preserves sealed evidence across interrupted transfers and
confirms requested deletion twice. Posted invoices are reconciled separately;
early or missing invoices are not final charges. A failed host or unreachable
provider can still prevent retrieval or explicit deletion. CPU rehearsal does
not establish GPU compatibility, full-model memory use or completion within
the allowance. The 13-hour limit requires operator deletion; it is not a runtime
estimate or an automatic billing cutoff.

The later final fine-tune (08) also prepares trained weights, necessary
supporting files, usage instructions and evaluation results for publication.
Verify that the intended release files load and generate masks and any agreed
additional outputs; the pilot setup's internal save/reload check does not
establish that release usability. Preparation can accompany development, with final verification on
the actual release artifacts. Node 16 publishes these prepared outputs. File
formats and publishing locations remain open, and publishing the training
dataset is not required. See [publication preparation](../docs/planning/release-decisions.md#publication-preparation).

## Task and training annotations

The informal and larger subject/mask pilots preserve both prompted tasks. The
intended direct release task below remains a later experiment, outside these
pilots' training-output contracts.

```text
complete original note → complete set of grouped source-text masks
additional outputs for note sorting, if needed: undecided
```

The distilled model must discover subjects as well as locate their evidence. The
input does not supply a subject list. Masks may contain separated fragments,
overlap other masks, and vary in number. The production output need not include
the intermediate English subject descriptions. Masks feed unchanged SSE.
The node-sorting workstream determines the scoring method and whether it needs
additional teacher/model outputs. Neither prominence nor mask-level scoring is
prescribed here; existing prominence experiments retain their own frozen inputs.

Use the subject and mask prompts validated by the current extraction work, not
the superseded ASv6.23 / MPv3.5 commitment. Freeze the exact prompt versions,
teacher model settings, output format and reviewed labels for each controlled
comparison. This plan does not select successor prompt versions. Preserve the
per-note subject hierarchies, raw annotations and review findings for diagnosis;
do not silently mix outputs from different annotation policies.

The note-sorting mechanism, any additional annotation/model outputs it needs,
and their evaluation criteria still need to be settled. Report earlier mask-only
results as mask-only evidence; they cannot establish the quality or cost of
additional outputs. Starting full training-data generation requires both
successful completion of the 500-note hierarchy validation and teacher
selection in the [release plan](../docs/planning/release-decisions.md). The
same teachers must write both the larger pilot training data and the full training
data, per the user's direction of September 21, 2026. The September 25 informal
experiment may reuse current saved annotations before that selection. Work that consumes no
labels may use any data and need not wait for the teacher selection.

The earlier training-data readiness target was **September 27, 2026**, including
masks and prominence with training/evaluation separation. That earlier scope
does not decide the current sorting-related output requirements. The checks and
handling of unsuitable annotations remain open;
a correction workflow is not assumed. Dataset size and the time required to
produce suitable data also remain open. The target does not establish
feasibility or change the pilot's proposed sizes.

The pilot includes a small hierarchy built from its outputs before model
selection, using the hierarchy construction and note-sorting methods being
validated. This does not authorize changes to the title prompt, SSE, grouping
method or segmentation. Distinguish
distilled-model errors from failures in the shared downstream pipeline; a parsing or
mask-overlap score alone does not establish hierarchy quality. Release-plan
task 11 still checks the final distilled model. This early check does not replace
the separate scale measurements or establish the full build's cost.

## Models and required untuned baselines

| Model | Proposed adaptation | Role |
|---|---|---|
| Qwen3.8-27B | QLoRA | General-model candidate |
| Gemma 4 31B instruction-tuned | QLoRA | Different pretrained foundation |
| Gemma 4 26B-A4B instruction-tuned | Open; published adapter-training path | Mixture-of-experts quality–cost comparison |

The user approved these three candidates on September 24, 2026, replacing
T5Gemma 9B–9B PrefixLM instruction-tuned with Gemma 4 26B-A4B instruction-tuned.
The MoE candidate tests whether lower active computation can reduce corpus
generation cost while preserving mask quality and any agreed additional output
quality. Its actual batched speed and task quality remain unmeasured; fewer
active parameters do
not establish lower training memory or cost. See the
[published evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#gemma-4-26b-a4b).
This selects candidates, not a training recipe or spending amount.

For each model, evaluate its original released checkpoint before training on
our annotations. Its existing pretraining and instruction tuning remain intact.

Within that model's before/after comparison, keep these unchanged:

- Evaluation notes and task instruction.
- Output format and input preprocessing.
- Decoding settings and inference precision.
- Semantic review criteria and mechanical checks.

Both versions begin with the original note, without reference subjects or masks.
For the informal two-step pilot, the subsequent mask calls receive subjects
generated by that same candidate version. Teacher-supplied subjects may support
separate mask diagnostics, but do not establish end-to-end extraction quality.
Preserve all original outputs. The untuned result is the zero-training-note
point on that model's learning curve. The Astra pipeline is a separate reference,
not a replacement for these three baselines.

Different models can use appropriate training settings and native input
formatting. Comparing their practical quality and cost does not isolate the
effect of architecture alone. A Qwen-only setup test cannot establish that
either Gemma checkpoint's training setup works.

## Proposed data

| Set | Distinct notes | Purpose |
|---|---:|---|
| First training checkpoint | 200 | First trained validation point for all three students |
| Second training checkpoint | 400 | Measure improvement along the same training run |
| Third training checkpoint | 600 | Measure improvement along the same training run |
| Fourth training checkpoint | 800 | Measure improvement along the same training run |
| Fifth training checkpoint | 1,000 | Included comparison, approved September 30 |
| Validation set | 100 | Compare development runs and select settings |
| Final test set | 200 | Evaluate selected candidates after development stops |

The user approved inclusion of the 1,000-note training comparison on September 30,
validation every 200 training notes on October 1, and one complete training pass
after the October 1 research. Validation/test counts
remain proposed. These are for the larger pilot, separate from the informal
100-note experiment. Each student has five trained validation points plus its
untuned baseline.

Each larger training set retains all earlier notes and labels, adding 200 notes.
All models receive the same sets. Choose broadly varied real notes while keeping
topic, writing-style, and length mixtures similar across sizes. Do not simply
use our food/music-heavy existing annotations as evidence of broad coverage.
The informal experiment deliberately starts with available data; its findings
must be described in terms of that selected collection.

Split before training. Keep duplicate, closely related, and same-author material
within one split. Reserve the final test notes now, but defer their annotation
until needed. Do not use test outputs to revise the experiment.

Mechanically check every training mask and deduplicate exact masks. Semantically
review a varied sample of training annotations and every validation/test
annotation. Annotation checks belong to local preparation before training.
The review method and uncertainty handling remain design choices; the user's
role is reviewing that design, not supplying example labels or adjudications.
Review of saved candidate outputs follows the
[approved structure](#semantic-review--approved-structure), occurs after retrieval
outside the rental, and does not feed judgments back into training. The detailed
rubric and release acceptance requirements remain open.
How unsuitable annotations are handled remains open; preserve teacher outputs
separately from review findings and any subsequent changes.

## Proposed run sequence and controls

1. **Check each training setup on a small sample.** Verify complete-note input,
   the agreed output format, source alignment, working training, GPU memory use,
   and measured speed. Record whether prominence is included. Training loss and
   successful parsing are setup diagnostics, not evidence of semantic quality.
2. **Measure the three untuned baselines.** Use thinking off on the shared
   validation notes and preserve their outputs before fine-tuning.
3. **Start one continuing training run per student.** Initialize the adapter
   and optimizer from the original pretrained model once. Use every frozen
   subject and mask example from the first 200-note block once, without
   replacement. Save a complete checkpoint after finishing that block and
   generate subjects and masks
   on the shared validation notes, without updating weights from those notes.
4. **Continue through 400, 600, and 800 training notes.** Carry the adapter,
   optimizer, learning-rate schedule, random state and data-order position
   forward. Train once on each new 200-note block; do not replay earlier blocks.
   Save and evaluate a checkpoint after completing each block. Record cumulative
   updates and which examples were used; restarting the optimizer or schedule is a recipe change.
5. **Continue to 1,000 notes.** This comparison's inclusion was approved
   September 30. Save and evaluate its checkpoint using the same validation
   notes and thinking-off generation settings. Finish the last block's examples,
   completing
   one pass through all frozen training examples. Extra repetition requires a
   separate design decision; milestones do not impose a wall-clock training limit.
   These checkpoints measure progression through one training history, including
   both added data and accumulated training; they do not isolate data size alone.
6. **Append the approved thinking evaluation.** For each student, evaluate the
   same saved 1,000-note adapter once with thinking on, on the same validation
   notes. Compare against its existing thinking-off answers; do not train again.
7. **Confirm decision-critical comparisons.** Repeat with a different random
   seed when a small gain or model difference would determine the next action.
   Keep the same evaluation notes and report uncertainty rather than treating
   each mask as an independent observation.
8. **Use the final test after selection.** Compare selected fine-tuned
   candidates with their corresponding untuned baselines on the reserved notes,
   using the same selected thinking mode for both.

### GPU preparation cases and checks — draft

Proposed scope for the separate preparation rental; case selection, trial
profiles, hardware and maximum charge still require agreement. Use the same
pinned models, approved adapter recipe and intended GPU allocation as the pilot.
Prepare the package and all trial profiles locally and rehearse their production
paths in the VM before booking. The current informal worker does not implement
the larger pilot's expert adapters or full milestone lifecycle.

**Cases:** start with these three historical notes, whose N labels follow the
preliminary held-out order. Use training/preparation notes for the larger pilot;
keep its reserved final test out of these trials.

| Case | What it exercises |
| --- | --- |
| N18, long diary (`eaa6a5e…`) | Dense hierarchy and termination: all three trained students hit the old subject cap here. |
| N00, soda bread (`03313183…`) | Negation, qualifiers, disjoint/partial selections and a previously capped mask. |
| N15, gianduja/store (`b3c0ab8f…`) | Short complete subject-to-mask path and saved empty/nonempty mask examples. |

Tokenize the actual candidate corpus and prompts locally. Add a distinct case
only when these notes miss a maximum needed for training or generation: full
teacher hierarchy/mask sequence, rendered input, or proposed batched shape.
Reuse a note that covers several maxima. The historical training maximum,
`05f275f4…`, was 6,531 Qwen / 6,440 Gemma tokens; historical short notes alone do
not establish fit for the larger corpus. Freeze source IDs, prompt versions,
row IDs and profile identities before execution.

**Combined GPU sequence, once per student:**

1. **Load and generate:** verify model revision, kernels, dtypes and adapter
   targets. Exercise the untuned thinking-off subject-to-own-subject-mask path.
   Save both responses and account for every dependent call immediately.
2. **Prepare two small complete note blocks and train the first:** use every
   teacher subject/mask example once, with the approved eight examples per update.
   Include at least two full updates and a smaller final group before the first
   checkpoint; choose whole notes rather than dropping masks to create that group.
   Measure the longest relevant training rows after Adam moments are allocated.
   Check finite losses/gradients, actual adapter changes, frozen base/router,
   gradient flow in activated expert adapters and exact example/supervised-token
   accounting.
3. **Save, merge, evaluate and resume:** seal the full first-block checkpoint.
   Record one reference next-block update from that saved state, then unload
   the trial training model from the GPU. Reload a fresh BF16 base, merge the saved first-block
   adapter and evaluate one short note with thinking off. Discard evaluation,
   restore the untouched full training
   state and repeat the same next update. Require exact counters, example order,
   cursor and restored random state; compare loss, adapter and Adam state under
   declared numerical tolerances. Finish the second block, save its complete
   checkpoint and retain both checkpoints. Local tests establish update/loss equivalence through the same
   production path before this GPU check.
4. **Test output limits and batching:** unload training and load the final saved
   preparation adapter on a fresh BF16 base, merging for evaluation. Use thinking
   off/on on the cases above. Generate subjects and one
   mask response for every valid returned subject. Record complete final answers,
   truncation, reasoning/final channels, counts, tokens and elapsed time for each
   declared profile. Compare one small set of identical mask requests individually
   and in the proposed batch, preserving raw/parsed differences and a smaller
   final batch. Separately exercise the proposed maximum generation/cache shape
   if natural answers stop before reaching it; early termination proves only the
   memory use actually reached. Trial caps and physical batch sizes remain proposals.
5. **Retrieve while running:** exercise the background copier with responses and
   a complete checkpoint, verify local hashes and confirm transfer leaves the
   continuing run intact. Reconnect/reconcile without duplicate work. I observe
   responses, training and telemetry through verified retrieval and explicit
   deletion; automatic deletion stays off.

**Local replay cases:** accepted JSON fences, malformed/truncated hierarchies,
valid empty masks, invalid source positions, missing dependent calls, partial
checkpoints and interrupted transfers. Use saved responses and production paths;
these checks do not need additional full-model inference.

**Preparation report:** per-phase peak CUDA allocated/reserved memory, sampled
GPU usage/utilization/power, host memory/disk, training/generation throughput,
reload/merge/copy overhead, call accounting and verified files. Choose output
limits and batch allocation from that evidence, then freeze the main pilot
configuration and revise its cost estimate. This establishes tested execution
and resource bounds; final-adapter reasoning lengths and learning quality remain
questions for the main pilot. Numeric acceptance tolerances, case membership,
trial count, hardware, implementation and spending remain open.

### Execution and failure handling (draft)

The [process walkthrough](../docs/planning/fine-tuning-pilot-process.md) maps
where each stage runs. This is a proposed execution contract for the larger
pilot, not a claim that the current worker enforces it.

- **Local preparation:** freeze note splits, nested training sets, teacher
  answers, prompt versions, model revisions, and each candidate's recipe. Prepare
  code and candidate generation settings locally. Test subject/mask output limits
  with thinking off and on during separate GPU preparation, using representative
  and long notes; measure complete answers, truncation, GPU memory and runtime.
  Select and freeze generation limits after those checks, before the main pilot.
- **GPU execution:** one thinking-off untuned validation baseline and one
  continuing training run per
  candidate. Reuse that baseline across checkpoints. Initialize the adapter and
  optimizer once, and retain complete training state as the dataset expands.
  Mix one subject-hierarchy example per note with one mask example per labeled
  teacher subject: the complete note plus that one subject yields its teacher
  mask response. Both tasks update the same adapter. At each milestone save and
  verify the complete unmerged training checkpoint containing its adapter; retain
  all five milestone checkpoints. Release training from the GPU. Load the saved
  adapter on a fresh original BF16 base, merge it into this disposable evaluation
  copy, and verify reload under that policy. Generate validation subjects and
  request a separate mask response for each generated subject from the saved
  checkpoint. Discard evaluation and restore the full untouched training state,
  including the exact next-example position, before the next block. Untuned
  baselines use the same single-subject mask format, approved October 1.
  Independent prompts may still share a GPU batch.
  Save both complete responses, raw and parsed, with note/subject links and
  failures. Validation must not update weights or reset the ongoing training
  state. Use each frozen training example once in its new 200-note block.
  Shuffle the block's subject and mask examples together using a fixed seed;
  take consecutive groups of 8 examples total across all GPUs for one adapter
  update, retaining a smaller final group when needed. This batch construction was approved
  October 1; the task mix varies between updates. Check exact coverage before
  the checkpoint; do not consume later-block notes early or repeat earlier
  blocks. Use the same held-out notes and thinking-off generation settings at
  every ordinary milestone. Training targets are teacher answers without
  reasoning traces.
- **Terminal thinking evaluation — approved October 2:** after the final ordinary
  evaluation, use the same saved 1,000-note adapter and merged BF16 inference
  policy for one thinking-on validation evaluation per student. Keep the same
  notes and task prompts; generate its own subjects and their separate masks
  with thinking on for both tasks. Preserve raw thought and final-answer channels
  separately, parsing only final answers as subject/mask data. Save frozen mode
  settings, call links, failures, time and total token usage. Apply the same
  immediate accounting and verified background transfer. Compare against already
  saved thinking-off final outputs; no further training or thinking-on untuned
  validation baseline is added. This tests thinking only at the final adapter.
  Thinking limits/batching, implementation and added runtime remain open.
- **Checks during execution:** account for every validation note and dependent
  call as responses arrive. For valid generated subjects, account for every
  requested mask response. An invalid subject response records that the mask
  stage was prevented, without inventing its unknown request count. Fewer
  generated subjects alone does not prove skipped work. Valid empty masks
  remain saved responses. Check baseline accounting
  before advancing to training and trained-output accounting before advancing
  the affected run.
- **Live observation — approved October 1:** observe from launch through
  verified retrieval and explicit deletion. Inspect actual baseline subject and
  mask responses before training, training progress and GPU telemetry, and
  trained outputs as they arrive, alongside automatic response/call checks.
- **Progressive retrieval — approved design October 1:** one background copier
  transfers each subject response, mask batch, and checkpoint as soon as saving
  finishes while execution continues. Verify local copies using file hashes;
  retain remote originals at least until verification, including checkpoints
  awaiting transfer. Limit bandwidth and disk activity to protect throughput.
  Before explicit deletion, verify both expected work and all required local
  files. Preserve original responses, parsed outputs, failures, adapters,
  configuration, and telemetry. Automatic deletion stays off. An incomplete
  run remains marked incomplete.
- **Local scoring:** after the rental, calculate mechanical reliability and
  mask agreement, and run the agreed per-note correctness/coverage review.
  Compare the same notes across baseline and trained versions. Keep semantic
  findings, model failures, and missing reviewer verdicts distinct.
- **Final test:** keep it out of development comparisons. Review it only after
  model, checkpoint and generation mode are fixed from validation. Match the
  selected mode between untuned and trained final-test outputs. Whether to
  generate its GPU outputs
  during the main rental and seal them, or in a later job, remains open.

Proposed handling of failures:

| What happened | Response |
|---|---|
| The model returned an invalid or truncated answer under the frozen settings | Preserve it, count the failure, record any prevented mask stage, and continue independently evaluable notes. |
| Required work was skipped, parsing is defective, inputs are wrong, or files are damaged | Stop advancing affected work, preserve/retrieve evidence, and mark the comparison incomplete. A pipeline defect is not a candidate quality score. |
| Execution or observation was interrupted | Reconcile the existing worker first to avoid duplicate starts. Reuse completed responses; resume training only from a verified checkpoint for that run under its original configuration. |
| A reviewer response is missing or invalid | Report an evaluation failure separately; do not assign that failure as a candidate correctness/coverage score. |

Parser corrections can re-evaluate saved baseline and trained outputs
consistently, without regenerating them. Missing dependent calls still require
actual generation. Changed generation settings require a separately identified,
matched evaluation. Preserve original responses; do not silently regenerate a
malformed answer or edit code on the rental.
A sealed `complete.json` establishes saved-file integrity, not that every
required model call occurred. Current sealed-result retrieval and checkpoint
resume exist; the stronger stage accounting and approved background copier
above still require implementation and verification. Transfer mechanism and
resource limits remain implementation choices.

With three candidates and five checkpoints per student, ordinary thinking-off
validation has eighteen versions: three untuned and fifteen saved checkpoints.
The terminal thinking-on addition contributes three versions at final weights.
For N shared validation notes, this is **18N + 3N = 21N** note/model outputs and
semantic reviews; at the proposed 100 notes, **2,100**, including 300 added by
thinking on. The addition requires 3N subject calls; mask-call counts depend on
each version's own subjects. Check total generation/review tokens,
full-note review input length, stored adapters, and transfer volume before
launch; include long notes and notes with many subjects. A reviewer input that
exceeds its limit must be reported, not silently truncated. Additional final-test
work depends on the still-open generation arrangement. Rental grouping,
runtime limits, and spending require separate decisions.

**Complete-pass budget approved October 1:** each frozen subject and mask
training example is used once, without replacement, in five new 200-note blocks.
This guarantees example coverage under a modest training budget; it does not
establish optimum training or each model's maximum capability. Batch construction
uses the approved shuffle within each block. **Starting settings approved
October 1 after comparable-experiment research:** 8 prompt–answer examples per
adapter update total across all GPUs, constant learning rate 0.0001 with no
warmup, and LoRA rank 16 / alpha 32 for ordinary adapters. Gemma MoE's routed
expert adapters use rank 2 / alpha 32, subsequently approved October 1, with
original model and router weights frozen. Retain smaller final groups; no
checkpoint resets the training state. These are a shared starting
recipe, not established optima. Numerical defaults were subsequently approved
below. Block membership, seed value and checkpoint selection remain open.
The approved larger-pilot MoE route adds adapters to
`experts.gate_up_proj` and `experts.down_proj` in all 30 layers at rank 2 / alpha 32,
keeping existing attention/shared MLP adapters at rank 16 / alpha 32. This follows
the [controlled MoE study's active-expert rank convention](https://thinkingmachines.ai/blog/lora/),
not a Gemma task-specific optimum. At the pinned model shapes it adds 59,473,920
parameters, for 78,059,520 total. With the approved FP32 adapter/gradient/Adam
state policy, static adapter training state is about 1.16 GiB, an increase of
0.89 GiB. Lower rank does not remove full adapted expert-weight buffers; exact
GPU fit and generation limits/batching remain unresolved. The merged evaluation
policy was approved October 2 below. Explicit expert targeting still
needs implementation. The current worker leaves routed experts frozen and uses
the preliminary 128-step replacement sampler, not the approved larger-pilot
continuation.

**Optimizer, precision and LoRA defaults approved October 1:** retain the
preliminary numerical approach and record the settings explicitly:

| Setting | Larger-pilot design |
| --- | --- |
| Optimizer | PyTorch AdamW (`adamw_torch`); beta1 0.9, beta2 0.999, epsilon 1e-8, weight decay 0 |
| Clipping | Aggregate trainable gradient norm at most 1, after accumulation and before the update |
| Base and computation | Frozen unquantized BF16 base; BF16 mixed precision computation with normal FP32-sensitive operations |
| Trainable state | FP32 LoRA weights, gradients and Adam moments |
| LoRA defaults | Dropout 0; frozen biases (`bias="none"`, `lora_bias=False`); standard initialization (`init_lora_weights=True`, Kaiming-uniform A, zero B); ordinary alpha/r scaling |

The adapter initially contributes zero. These are supported starting choices;
[Trainer defaults](https://huggingface.co/docs/transformers/v5.17.0/en/main_classes/trainer)
and [PEFT precision guidance](https://huggingface.co/docs/peft/v0.21.0/en/developer_guides/troubleshooting#selecting-the-dtype-of-the-adapter)
do not establish their optimality for this task. Physical batching must retain
the approved eight examples total per update; one-example batches accumulated
eight times apply only when that student trains on one GPU. GPU allocation,
generation limits/batching and remaining runtime choices stay open; merged BF16
checkpoint evaluation/resume and the terminal thinking comparison were approved
October 2. Ordinary generation stays thinking off.
Exact memory fit of the expanded MoE configuration must be checked during
separate GPU preparation. The larger-pilot worker still needs implementation
and production-path verification.

**Checkpoint lifecycle approved October 2:** complete each 200-note block's
final update, including any smaller final group, then save the full unmerged
training checkpoint. Seal completion only after all files and their hashes are
complete. Each of the five retained milestone checkpoints includes its adapter,
optimizer, schedule, Python/NumPy/Torch/CUDA random state, cumulative update
count, exact data-order position and frozen run identities. Save the actual
next-example position; multiplying update count by eight would skip examples
when a block ends with a smaller group.

Release training objects from the GPU, then load a fresh pinned original BF16
base plus the saved adapter and merge the adapter into this disposable evaluation
copy. All three students use this same inference policy at every trained
milestone; untuned baselines retain the original base. Verify adapter reloads
under the chosen merged policy, without requiring merged/unmerged text equality.
The [PEFT expert-adapter guidance](https://huggingface.co/docs/peft/v0.21.0/en/package_reference/lora#targeting-nnparameter-directly)
recommends merging to remove repeated packed-weight work during generation.
Preserve the unmerged FP32 adapter and full training checkpoint; do not merge and
unmerge the continuing BF16 training base. Each checkpoint's evaluation outputs
are tied to that checkpoint and inference settings. Preserve all responses and
resume incomplete evaluation from completed saved calls under the same settings.
Check dependent-call accounting as responses arrive, before advancing the
candidate; completed files transfer through the approved background copier.

After evaluation, discard its model and restore trainable adapters, optimizer,
schedule, counters and the exact next-example position from the untouched
training checkpoint. Restore random state after reconstructing the model and optimizer, then
continue training with training mode, cache off and training checkpointing
restored. No validation answer updates the adapter. This lifecycle keeps one
copy of a given student's model resident at a time and adds cached-base reloads at transitions.
Separate GPU preparation must measure that overhead and merge peak memory, and
verify continuation across the full transition. The current worker evaluates an
unmerged adapter only at training's endpoint and retains two rolling checkpoints;
five-stage continuation, milestone retention and merging still need implementation
and production-path verification. Additional recovery-checkpoint cadence,
generation limits/batching, hardware and spending remain open.

**Training loss approved October 1:** ordinary cross-entropy on teacher-answer
and native turn-ending tokens, summed across the actual adapter update and
divided by its actual supervised-token count. The prompt, note, supplied subject,
and padding receive no loss. Do not average separately normalized batch losses;
GPU partitioning and accumulation must preserve the same update-level objective.
Smaller final groups use their own denominator. No extra task, answer, or note
weights are applied. Longer answers contribute more tokens within an update;
this does not establish equal subject/mask influence or an optimal task mixture.
The [normalization guidance](https://huggingface.co/blog/gradient_accumulation)
and [comparable extraction implementation](https://github.com/hitz-zentroa/GoLLIE/blob/164c611743fdc1befe71bbdf03e08c5eb4e35957/src/trainer.py#L288-L300)
support this starting objective. Its exact behavior in the larger-pilot worker
still needs production-path verification.

The preliminary 20% subject / 80% mask replacement sampler is a different recipe.
At the old subject-count average, a natural pass is about 4% subject rows and
96% mask rows. On the saved 80-note training set, production-encoder accounting
gives subjects about 30% of response-token volume in a complete pass, versus
73% in the old draws; neither percentage measures gradient contribution.
Check the effective loss normalization and report per-task loss, target tokens,
updates and consumed rows at each milestone. The preliminary 128 updates are
not the larger-pilot budget. Freeze the full ordering, schedule, checkpoint
save/evaluation procedure and selection rule before launch; do not restart
learning-rate decay at a milestone. Record recipe changes and interruptions;
preserve the actual training history for every checkpoint. The current
replacement sampler and stage/resume handling still need implementation changes
and production-path verification for this approved design.

There are **three main continuing fine-tunes**, each with five approved
milestone checkpoints, alongside untuned baselines, setup checks and any
separately justified confirmation work. The 1,000-note comparison is included;
validation/test counts, GPU grouping and spending remain open. Four GPUs cannot
run four independent milestone training jobs when one student's later stage
depends on its earlier stage; checkpoint generation could
provide other parallel work, with scheduling still to be designed and tested.

## Evaluation and decisions

### Initial automatic mask scoring — approved

Within each note, match generated masks to reference masks one-to-one,
independently of their list order. Treat all fragments of each mask together
as a set of source-token positions.

```text
overlap = tokens selected by both masks / tokens selected by either mask
```

Count a match when overlap is at least 0.80. For example, five selected tokens
versus four of those same tokens gives 4/5 = 80%. Calculate precision, recall,
and F1 using this rule, with exact-match scores calculated separately.

This follows the matching approach in
[PropSegmEnt, sections 3.2 and 5.1](https://aclanthology.org/2023.findings-acl.565.pdf).
The 80% cutoff is an initial mask-matching rule, not a required model accuracy.
For the larger pilot, source tokenization, score averaging and the score used
to select training checkpoints remain open. The informal automated workflow's
mechanical scoring is specified above; it trains for a fixed number of steps
and does not select checkpoints using these scores.

### Semantic review — approved structure

One review prompt per note and model version receives the full note, task
prompt, and that version's subjects, hierarchy, and masks. It returns separate
**correctness** and **coverage** scores with evidence for each. Correctness
assesses returned content; coverage assesses missing required content.
Output reliability is checked mechanically. Review runs after retrieval,
outside the rental, and is evaluation only. The scoring scale, rubric, reviewer
model, reliability checks, and score aggregation remain open.

### Required pilot measurements

| Measurement | Required evidence | Decision it informs |
|---|---|---|
| Quality on unseen notes | Before/after subject coverage, mask correctness and quality of any agreed additional outputs on the same held-out notes | Whether training improves the intended task |
| Improvement with more training data | Quality at each tested data size, under the controls above | Which models and additional annotations merit investment |
| Actual training resources and cost | GPU configuration, peak memory, training time and total rental cost, including setup and evaluation | Feasible hardware and measured inputs to larger-training estimates |
| Batched generation speed | Notes processed per second, output lengths, peak memory and failures on representative notes | Time and cost to process the proposed launch corpus |

Measure semantic quality separately from output reliability:

- **Correctness:** how correct are the returned subjects, hierarchy relationships,
  and masks for their supplied subjects?
- **Coverage:** which required subjects or relevant information are missing?
- **Additional outputs, if required by the chosen sorting method:** how well do
  they meet their agreed meaning? Freeze review criteria before comparing
  models; do not infer correctness from valid numbers or combine these errors
  with mask errors into one score.
- **Output reliability (mechanical):** missing responses, truncation, malformed
  outputs, and masks that cannot be located correctly in the original note.

For resource measurements, record the exact checkpoint, training or inference
configuration, batch size, input/output lengths and billed rental interval.
Separate training time from downloading, loading, checkpointing and evaluation;
include all of them in total cost. Record failed attempts and retries rather than
reporting only the successful run.

Measure generation in batches on a representative mix of real notes, including
long notes and notes producing many masks. Report those cases separately as well
as the overall rate. Include failed outputs and retries in elapsed time, and
report unresolved failures separately; do not count them as completed notes.
Repeat the measurement with the selected release model and final output format
before committing the full corpus build.

Valid alternative masks and harmless redundancy are acceptable. Exact copying
is necessary for source alignment, but agreement with one teacher mask list is
not the definition of semantic correctness. Teacher mistakes remain annotation
issues rather than automatically becoming student errors.

The assistant reviews outputs with model identities hidden and preserves
concrete examples of improvements and regressions. Summaries must distinguish
semantic findings from parsing success, training loss, and token-overlap scores.

For each model, show quality before fine-tuning and as training data increases,
including the gain from each added batch. Do not extrapolate a final required
dataset size from two or three points. If improvement shrinks, examine label
quality, missing coverage, model capability, and training behavior before
generating more of the same data.

Compare quality against total training-and-generation cost at the proposed
launch volume, not training cost alone. Keep annotation, storage and transfer
costs visible, and distinguish measured costs from extrapolations. Do not project
one corpus-wide rate from only short, easy notes or infer the final data
requirement from a small learning curve. No universal accuracy threshold or
claim of production readiness has been approved.

## Preparation findings

The read-only annotation audit found these complete-note packages:

| Package | Notes | Distinct accepted masks after exact deduplication |
|---|---:|---:|
| [Food/drink](real-note-fine-segmentation-v1/reviewed-input.json) | 100 | 918 |
| [Coverage expansion](real-note-fine-segmentation-v1/coverage-expansion-v1/masks-reviewed/reviewed-input.json) | 48 | 400 |
| [Music](real-note-fine-segmentation-v1/music-generation-v1/masks-effective-mapped/reviewed-input.json) | 100 | 1,058 |
| Total | 248 | 2,376 |

The files contain 2,434 accepted masks before deduplication and 58 exact
duplicates. Their byte ranges match their source fragments. That is mechanical
validity, not semantic approval of every annotation: one food subject remains
unresolved without a saved mask, and the music review records semantic concerns.
The packages are starting material, not 248 automatically approved training
examples. Do not silently turn an incomplete annotation set into a complete
training target by dropping the unresolved item.

The notes average about 312 characters; original note plus compact grouped-mask
JSON averages about 841 characters after exact deduplication. These are character
counts from a selected corpus, not model-token counts or a forecast for every
new topic. These older annotations and counts do not establish the coverage,
output lengths or any additional labels needed by the chosen sorting method.

## Compute estimates and spending constraints

### Pilot budget — approved approach

Reserve enough of the remaining budget to train the selected model on more
data and evaluate it, with room for reruns. Set a provisional ceiling for the
three-model pilot around that reserve. Reassess the proposed allocation using
measured costs and whether further comparisons could change the model choice.
Any spending still requires the approvals specified below.

Distinguish reusable expenditure, such as training annotations and working
infrastructure, from the additional compute spent comparing candidates. Count
all paid expenditure against the lifetime ceiling, regardless of reuse.

The pilot ceiling is a financial guardrail, not a spending target or evidence
that the pilot is scientifically sufficient. Its amount and the final-training
reserve remain open; one complete training pass is approved. No fixed pilot/rest
ratio has been adopted.

### Larger pilot cost estimate — October 1, provisional

Full cash cost and elapsed time must be recalculated from **cumulative training
work across three continuing student runs** and the selected GPU schedule. The
approved five checkpoints per student increase validation generation and
review work; the selected final-test comparison is the same size. The October 2
terminal thinking addition adds three validation versions; its GPU runtime is
unmeasured and excluded from the thinking-off extrapolations below. Training uses
one complete pass through the frozen subject/mask examples. Actual row/token
counts and remaining recipe choices determine its update count and runtime.
The component estimates below are provisional and authorize no spending.

A read-only Vast search on October 1 found a comparable verified 450 W RTX PRO
6000 WS with 96 GB VRAM and 300 GB storage at **$1.4167/hour**, matching the
completed preliminary rental's price. Inbound/outbound transfer rates were
$0.0078125/$0.0091146 per GB. No offer was reserved. Prices and availability can
change; [Vast bills compute, storage and transfers](https://docs.vast.ai/guides/instances/pricing).

Saved preliminary-run durations project approximately **116.5 GPU hours / $165**
for 1,800 thinking-off validation note/model outputs: three baselines plus fifteen
frozen
checkpoints. The two extra checkpoints per student add 600 evaluations, about
42 GPU hours / $60 at the previous rental's speed and price, already included in
the 116.5-hour estimate above, before extra checkpoint checks and transfers.
The selected candidate's final comparison adds
400 outputs, roughly 16.5–25 hours / $23–35. Gemma baseline mask times are inferred from trained mask
throughput because those baseline calls never happened. Truncated or malformed
subjects also prevented some trained mask work. These are workload extrapolations,
not measurements of a complete larger pilot.

Together, thinking-off validation and a thinking-off selected final comparison
project to **133–142 GPU hours / $188–200 before training, setup, headroom and
transfers**. This excludes the terminal thinking-on evaluation; its extra
reasoning, changed subject counts and runtime need measurement. Selecting
thinking on for the final test would also require revising that component's
estimate and generating a matching untuned baseline. Training
hours can be estimated from the measured 128-update trainer times:

```text
training hours ≈ (52.2 × Qwen updates + 80.6 × dense Gemma updates
                  + 24.8 × MoE updates) / (128 × 60)
```

Each update count is the **total across that student's entire continuing run**,
not a fresh budget at every milestone. The measured trainer times already
include periodic checkpoint writes/hashing; add only stage export/reload work
not included in those times. The earlier 2.55-hour projection assumed fifteen
checks resembling the preliminary terminal save/reload. It does not estimate
the approved fresh-base merged evaluation and full training-restoration flow;
measure that transition in separate GPU preparation before pricing its overhead.
Three continuing runs do not imply a two-thirds compute saving: retaining the
same total updates retains approximately the same trainer work. Savings depend
on the chosen schedule and avoiding unnecessary repeated work.

These projections assume comparable batch sizes, sequence lengths and
throughput; they do not establish adequate training. An illustrative 25%
headroom can cover startup and workload uncertainty, with another $3–10 for
transfers at comparable host rates, to be recalculated for the fifteen complete
checkpoints. Neither is a confidence interval or cap.
GPU grouping, shared resources, downloads, output lengths and checkpoint
frequency affect the final estimate. Testing all three candidates against their
baselines on the final test would add roughly $58–69 of generation cost over
one selected candidate, before headroom and extra reviews.

Teacher labeling and semantic review assume the existing subscription route,
with **zero incremental API cash charge**, excluding the already-paid
subscription. This is not free unlimited capacity; quota and completion time
must be planned. Paid API fallback is neither selected nor included in the
component generation estimate. Mechanical scoring runs locally. Reviewer,
final-test collection, GPU grouping and remaining runtime choices remain open.

For scale, the current 100-note teacher data has 23.83 subjects per note. Latest
native receipts average 2,631 uncached input / 1,108 output tokens per subject
call, and 2,095 uncached + 282 cached input / 105 output per actually sent mask
call. Reused-answer receipts with zero new usage are excluded from these means.
At those lengths, 1,300 newly labeled notes require about 32,279 calls / 81.7M
tokens. Training subsets share labels; do not charge their nested notes twice.
The older 9.82-subject sample cannot be reused as the current workload estimate.

At the proposed split sizes, one review per note/version gives **2,100 validation
reviews plus 400** for the winner's trained/untuned final comparison. This includes
300 added reviews for the terminal thinking evaluation. An illustrative review workload uses 7,000–10,000 input and 500–1,500 output tokens per review, including reasoning, plus labeling. No review prompt or reviewer is selected.

As a separate cash scenario, using the October 1 recorded
[Astra Standard API rates](https://developers.openai.com/api/docs/models/gpt-6-astra)
of $10/M input, $1/M cached input and $50/M output, all 1,300 labels at the
measured token lengths would cost about $926–1,005. The illustrative **2,500
reviews** would add **$238–438**, including approximately $29–53 for the 300
new reviews. These are API sensitivity estimates, not subscription
charges or approved fallback spending; different reviewer models, reasoning,
cache writes and actual request lengths can change them.

Evidence: per-response timings and training records under
`target/distillation-pilot-v1/launch-20260929-v2/operation/result/work/results/`;
previous analysis `target/distillation-pilot-v1/results-deep-dive-20260930.md`.
The following older estimates remain historical scenarios and do not describe
this measured BF16 workload.

### GPU alternatives and duration — October 1, provisional

A read-only search compared verified on-demand offers with the previous driver,
CPU-memory, disk, connectivity and reliability constraints. Single-GPU rates
include 300 GB storage. These are observed quotes, not selected or reserved
hardware; the cheaper Max-Q offer was absent on the refresh a few minutes later.

| Configuration observed | Dollars/hour | Whole-workload speed required to beat the previous $1.4167/hour rental |
| --- | ---: | ---: |
| RTX PRO 6000 Max-Q, 96 GB, 300 W | $1.1311 | More than 79.8% of previous throughput; less than 25.3% longer |
| RTX PRO 6000 WS, 96 GB, 500 W | $1.4722 | More than 3.9% faster |
| RTX PRO 6000 Server, 96 GB, 600 W | $1.5222 | More than 7.5% faster |
| H200, 141 GB | $5.2281 | More than 3.69 times as fast |
| B200, 180 GB | $6.3281 | More than 4.47 times as fast |

Break-even calculation: `alternative hours / previous hours < previous hourly
rate / alternative hourly rate`, before differences in setup and transfers.
No measured run establishes these speed changes. A broad search returned a
600 W workstation at $1.31/hour, but its older driver and slower download link
failed the current host constraints; its price is not a compatible-run quote.

The 500 W workstation is a simple candidate for both lower cost and shorter
duration if it clears the small speed threshold. Max-Q is a plausible cost
candidate but may take longer. Both workstation variants have 96 GB and the
same published 1,792 GB/s bandwidth; [NVIDIA Max-Q specifications](https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/professional-desktop-gpus/rtx-pro-6000-max-q/workstation-datasheet-blackwell-rtx-pro-6000-max-q-nvidia-3519233.pdf),
[workstation specifications](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/).
The server variant's bandwidth is 1,597 GB/s, so its higher power does not
establish faster generation. [Server specifications](https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/)
H200/B200 have higher published bandwidth and capacity, but those ratios are
not whole-run speedups. [HGX specifications](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory-h100-h200-b200/latest/components.html)

Prior telemetry supports caution on Max-Q: training/save/reload power medians
were approximately 450/450/445 W for Qwen/dense Gemma/MoE. Qwen and dense Gemma
baseline subject/generation samples exceeded 300 W most of the time, whereas
MoE evaluation medians were approximately 178–184 W. Qwen trained evaluation
median was 245 W, dense Gemma 299 W. These are periodic samples, not energy
integrals or isolated decoding benchmarks. They do not prove unchanged speed
under a 300 W limit. The full unchanged workload also exceeded 80 GB: dense
Gemma allocated 85.34 GiB of CUDA tensors, with sampled overall GPU use peaking
at 94.32 GiB. An 80 GB H100/A100 is therefore not a substitute for this recipe.

At the measured 450 W throughput, thinking-off validation and the winner's
thinking-off final comparison alone project to approximately 133–142 GPU hours.
The terminal thinking-on addition is unmeasured. Add cumulative training work,
checkpoint checks and setup before applying any headroom. GPU-hours are total
work; elapsed rental time depends on the actual schedule.

There are three student training paths, each with dependent
200/400/600/800/1,000-note stages. The earlier nine-independent-training-job
packing does not apply.
Different students could train concurrently. A fourth GPU could generate answers
from frozen checkpoints or process independent validation-note subsets, but
that schedule, resource isolation and implementation remain open. Preserve the
same per-response generation settings and complete call accounting. Do not
claim a two- or four-GPU duration merely by dividing total GPU-hours.

Teacher labeling and local semantic review/selection add elapsed time outside
the rental. Separate rentals can end independently; multi-GPU hosts charge for
idle GPUs. The two/four-GPU server quotes showed little per-GPU discount. No
parallel implementation or hardware choice is approved by this price comparison;
prepare and test the selected launch configuration locally before renting.

Offer evidence is saved in `target/distillation-pilot-v1/cost-estimate-20261001/`;
GPU telemetry is under the completed operation's `observations/progress-*.json`.
These duration scenarios do not establish adequate training or a spending cap.

### Runtime estimates — not measured

The following September 15 estimates predate the current subject hierarchy and
later prominence experiments. They are not measured runtimes for the release task.
They assume 1,000 short training notes, three passes, compact mask-only outputs,
and no CPU offloading. Use pilot measurements to replace these assumptions before
allocating larger-run spending:

| Model | Proposed GPU | Estimated training time |
|---|---|---:|
| Qwen3.8-27B, QLoRA | One A6000 48GB | 1–4 hours |
| Gemma 4 31B, QLoRA | One A6000 48GB | 2–6 hours |
| Gemma 4 26B-A4B, method open | Open | Not estimated |

Allow an additional 1–3 hours per model for downloading, loading, checkpointing,
and evaluation, excluding annotation work and troubleshooting. The earlier
T5Gemma runtime estimate does not transfer to Gemma 4 26B-A4B. The
[published hardware evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#published-training-hardware-and-weight-storage)
does not establish measured memory use for this particular workload.

Read-only Vast offer searches on 2026-09-15 found A6000 48GB offers around
$0.54–0.56/hour and H100 80GB offers around $2.19–2.59/hour, including 200GB
storage and excluding transfers. The remaining calculations below use a rounded
planning rate of $0.60/hour for an A6000. Availability and
prices can change; no offer was reserved. See [Vast pricing](https://docs.vast.ai/guides/instances/pricing).

### Larger-training cost scenarios — provisional

Saved on 2026-09-15 for reference, not as approved dataset sizes or spending.
Each cell estimates one training run with three passes through the data,
using the model and GPU pairing above.

| Training notes | Qwen3.8-27B | Gemma 4 31B | Gemma 4 26B-A4B |
|---:|---:|---:|---:|
| 10,000 | $6–24 | $12–36 | Not estimated |
| 25,000 | $15–60 | $30–90 | Not estimated |
| 50,000 | $30–120 | $60–180 | Not estimated |

These are linear extrapolations from the unmeasured runtime ranges above:

```text
training cost = hours per 1,000 notes × (training notes / 1,000) × hourly rate
```

They assume similar note and mask lengths and unchanged training throughput.
The ranges are not measured confidence intervals or guaranteed upper bounds.
Three passes is a costing assumption, not a frozen training protocol. Setup,
evaluation, transfers, troubleshooting, and annotation generation are additional.

### Approved allocation

The user approved one shared **$1,000 lifetime budget** and **$0 reserved for
future work**. The subsequent approval permits up to **$25 total** for the
informal pilot's GPU setup, baselines and initial fine-tunes. No commitment has
yet been accepted or entered for that work; record it before renting. No amount
is earmarked for the larger fine-tune.
The previously proposed $500 fine-tuning reserve was not approved. Model and
training-cost estimates above remain planning scenarios, not spending authority.
Any paid annotation work shares the same lifetime budget.

Use [budget-ledger.json](../budget-ledger.json) for current spending and
outstanding commitments for this pilot. Hosting costs and reserves stay outside
that ledger, as recorded in the [release decisions](../docs/planning/release-decisions.md#compute-hosting-and-budget).
No per-run spending approval is implied by the training estimates or the
unallocated budget.

### Spending constraints

The [repository budget rules](../AGENTS.md) govern every paid action. The $1,000
ceiling covers the entire effort, including previous costs, failed runs,
evaluation, storage, and transfers. It is not a per-model allowance or a target.
There is no separate parameter-count, GPU-memory, or single-machine ceiling.

The spending code and ledger enforce the approved $1,000 cap. The repository
rules give standing approval for user-requested OpenRouter work roughly estimated
at $1 or less, without a provider-side cap. Other paid runs need an explicitly
approved maximum charge. Provider-enforced spending caps are not required;
ledger accounting and the lifetime ceiling still apply.

## Next step

The informal dataset is prepared for one fine-tune per candidate on both
existing prompted tasks. The deletion-policy change is included in the rebuilt
image and frozen `package-v9`; all 24 local VM tests passed, including training
and SSH deployment. The rebuilt private image is published and verified.
The user approved proceeding and required continuous observation throughout the
rental. After the 600 W availability watch, the user approved the 450 W
workstation offer. All other frozen checks pass.
The recorded rental rate was $1.4167/hour including 300 GB storage.
The new immutable operation is
`target/distillation-pilot-v1/launch-20260929-v2/operation/`. All three candidates
completed in the frozen image and package. The worker exited with status zero
on September 30 at **02:56:58 UTC**. Retrieval of **671 work files** was
hash-verified at **03:08:17 UTC**, and local output verification passed at
03:08:20 UTC. Rental time was about **9 hours 28 minutes**, below the approved
13-hour limit; the 12-hour worker timeout did not fire. The local watcher was
resumed after chat interruptions while the same remote attempt continued.

| Candidate | Baseline `f1_80` with fences accepted | Trained `f1_80` | Trained subject / mask failures | Training minutes |
| --- | ---: | ---: | ---: | ---: |
| Qwen | 0.344 | 0.346 | 2 / 3 | 52.2 |
| Gemma dense | Pending mask generation | 0.397 | 1 / 5 | 80.6 |
| Gemma MoE | Pending mask generation | 0.313 | 3 / 13 | 24.8 |

These are teacher-agreement scores on 20 held-out notes, with one-to-one matching
of unique nonempty source-word selections; semantic correctness remains pending.
All 20 baseline subject answers from each Gemma candidate were wrapped in
Markdown code fences and failed strict JSON parsing. Their zero scores reflect
formatting failure, and no baseline mask calls were made. The user subsequently
requested accepting fenced JSON to recover those baselines. The updated subject
and mask decoder was applied to saved Qwen baseline and all three trained
outputs, using the same production evaluation and scoring paths without new
inference. Eleven Qwen baseline masks were recovered: its baseline F1 rises
from 0.333 to 0.344, with mask failures now 11 before and 3 after training. All
trained scores remain identical. The separate replay and source provenance are
saved under `target/distillation-pilot-v1/fenced-json-reparse-20260930/`.
All 40 saved Gemma subject answers now validate, yielding 290 dense and 328 MoE
subjects. Their 618 masks need generation with the untuned models before a
baseline quality comparison is possible. Training need not be repeated; any
new paid run needs maximum-charge approval under the repository spending rules.
Each candidate trained on 211 sampled subject examples and 813 mask examples;
all saved adapters reproduced their pre-save answers after reload. The training
times above exclude saving and the reload comparison.

The observation directory contains **553 periodic GPU samples** recording
utilization, VRAM, power draw and power limit from September 29 at 17:46 UTC
through September 30 at 02:56 UTC. Four sampling gaps exceeded two minutes;
the longest was about 6.7 minutes. Maximum sampled VRAM use was 96,581 MiB.

The preliminary resource charge was **$13.392**. Evidence is
`observations/preliminary-charge-summary.json` and its native invoice snapshot. Including
the earlier failed rental's $0.338, posted charges total **$13.73** across both
rentals; unposted charges remain unresolved. The next steps are completing the
Gemma baseline mask generation and semantic review before candidate selection.
The old frozen launch retains its
original code. Candidate recipes and Vast limits are unchanged. The prior
publication and one rental were authorized within $25, at up to $1.66/hour for
at most 13 hours.
The saved split inspection found no clear complete-note duplicates or close paraphrases across
the 80/20 split; topical overlaps remain recorded and this is an informal test.
Registry verification of the previous image completed before the first launch.
The availability watch found a compatible offer. The shared runner
passed preparation.
The recorded rental rate was $1.6555555556/hour including 300 GB storage. The immutable operation is
`target/distillation-pilot-v1/launch-20260929/operation/`. Its persistent local
supervisor stopped the first attempt after a local monitoring error. Image
startup, direct SSH, frozen-input verification and automatic worker start passed.
Qwen preflight and weight download completed; no baseline output or training
completed.

At 15:58:47 UTC the agent imported the frozen local runner while reading remote
progress, without disabling Python bytecode writes. Python created
`transport/control/__pycache__/vast_full_build.cpython-313.pyc`. The next
supervisor manifest check rejected the unexpected file and invoked `stop`. This
was caused by the agent's local monitoring command; no GPU failure was reported.
Retrieval of 15 work files was verified at 15:59:17 UTC, and deletion was confirmed
by two absent inventories at **15:59:27 UTC**. A separate inventory was also
empty. No remote code edits or dependency installs occurred.

The accidental cache is preserved in `operation/monitoring-failure/`; moving it
out restored the original frozen transport hashes and file set. A local
`python3 -B` import then passed the production manifest checks without creating
cache files. All future inspection of frozen Python modules must disable
bytecode writes before import. This verification is local and incurred no rental.

The preliminary resource charge was **$0.338**. The supervisor has exited.
Following this failure, the user explicitly requested removal of automatic
deletion. The current shared command runner preserves instances on completion,
errors, expiry and interruption; only an explicit `stop` command deletes them.
Regression coverage includes the unexpected-cache failure, failed jobs, deadline
expiry without SSH, hardware rejection, result retrieval and explicit deletion.
The legacy GTE path retains its previous behavior. The failed frozen operation
and published image are historical evidence and have not been modified.

The failure was discussed with the user, who requested manual deletion and
then approved proceeding with continuous observation. Reconcile the first
rental's final bill when eligible. No baseline/training comparison or candidate selection can
be made from this attempt.
