# Fine-tuning pilot

## Status and scope

**Release-plan tracking:** the preliminary 100-note experiment below is task
**29 · Run preliminary 100-note fine-tuning experiment**, in progress. The larger
model-selection pilot is **06 · Choose model through larger fine-tuning pilot**,
waiting for its data in 05; its exact dataset size remains open. Task 18's
training setup is complete. Task 29 needs 01 + 18, not the larger-pilot data
in 05, and its findings inform 06 without becoming a new completion gate.
Splitting the tracking does not change the experiments or spending approvals.

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
20-note baselines, 128-step training, matching adapter reloads and 20-note trained
evaluations. The worker exited successfully on September 30 at 02:56:58 UTC.
Retrieval of 671 work files was hash-verified at 03:08:17 UTC; local output verification passed. This
verifies execution; semantic review and model selection remain open. Evidence
is in `target/distillation-pilot-v1/launch-20260929-v2/operation/`, including
`result/work/results/*/report.json`, `launch/retrieval-verification.json`,
`launch/destruction-confirmation.json` and `observations/`.

The release model still needs prominence. The requirements below describe the
larger evaluation and release decision; prominence is excluded only from this
initial informal experiment. The user accepted the proposed **$25 total maximum**
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
compares the quality of candidate subjects, masks, prominence and resulting
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
  speed. Include both masks and prominence in the release-model evaluation.
- Start automatic mask matching with an 80% token-overlap cutoff, alongside
  separate exact-match scores. Details are in [Evaluation and decisions](#evaluation-and-decisions).
- The total oracle MVP spending ceiling is $1,000, replacing—not supplementing—
  the old $500 ceiling. Existing spending and commitments still count.
- Protect the larger fine-tune's budget with a provisional pilot spending
  ceiling. See [Pilot budget](#pilot-budget--approved-approach); no amount or
  percentage is approved yet.

The staged experimental design below is proposed, not fully approved. Dataset
sizes, exact training settings, hardware allocations, and individual spending
authorizations remain open for that larger design. The first informal rental below
started and was deleted on September 29 after the monitoring error recorded
below. No baseline or training completed.

The release plan's **18 · Prepare training code for the fine-tuning pilot** is
complete for setup: local VM rehearsals cover each candidate family, training,
interruption/resume, save/reload and SSH deployment. The image is published and
verified. Final training-example formatting and mask/prominence quality evaluation
remain in **06 · Choose model through larger
fine-tuning pilot**, which needs the agreed output format, prominence criteria and reviewed pilot
data to complete release-model selection. Preliminary candidate execution and
subject/mask quality review belong to 29, not completion of 06. The informal
experiment above is authorized to begin preparation without prominence. The user subsequently
approved building and testing the automated workflow in a local VM before
deploying it on rented hardware. The implementation uses Transformers Trainer
and PEFT in a pinned PyTorch container. The user clarified that this must
rehearse deployment as previously done on Vast, with no manual code editing
on the rented server. Candidate training settings and Vast launch limits are
now frozen locally. On September 29 the user authorized publication and one
Vast rental, then approved up to $1.66/hour and 13 hours total within $25.
GPU compatibility is checked during the actual pilot.

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
baselines, training, matching reloads and trained evaluations. Results were
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
not establish semantic correctness or approval; semantic review remains open.

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
Verify that the intended release files load and generate masks and prominence;
the pilot setup's internal save/reload check does not establish that release
usability. Preparation can accompany development, with final verification on
the actual release artifacts. Node 16 publishes these prepared outputs. File
formats and publishing locations remain open, and publishing the training
dataset is not required. See [publication preparation](../docs/planning/release-decisions.md#publication-preparation).

## Task and training annotations

The informal pilot above preserves both prompted tasks. The intended direct
release task below remains a later experiment; it is not the informal pilot's
training-output contract.

```text
complete original note → complete set of grouped source-text masks + prominence per mask
```

The distilled model must discover subjects as well as locate their evidence. The
input does not supply a subject list. Masks may contain separated fragments,
overlap other masks, and vary in number. The production output need not include
the intermediate English subject descriptions. Masks feed unchanged SSE;
prominence supports ordering notes within nodes.

Assess prominence from the complete note and the particular mask, without
requiring a generated subject description. Prominence prompt development and
scoring calibration are a separate workstream from release planning.

Use the subject and mask prompts validated by the current extraction work, not
the superseded ASv6.23 / MPv3.5 commitment. Freeze the exact prompt versions,
teacher model settings, output format and reviewed labels for each controlled
comparison. This plan does not select successor prompt versions. Preserve the
per-note subject hierarchies, raw annotations and review findings for diagnosis;
do not silently mix outputs from different annotation policies.

The prominence definition, annotation prompt, output representation and evaluation
criteria still need to be settled. Report any earlier mask-only results as
mask-only evidence; they cannot establish prominence quality or the cost of
generating both outputs. Starting full training-data generation requires both
successful completion of the 500-note hierarchy validation and teacher
selection in the [release plan](../docs/planning/release-decisions.md). The
same teachers must write both the larger pilot training data and the full training
data, per the user's direction of September 21, 2026. The September 25 informal
experiment may reuse current saved annotations before that selection. Work that consumes no
labels may use any data and need not wait for the teacher selection.

The agreed readiness target for the larger fine-tune's training data is
**September 27, 2026**, including masks and prominence, with training/evaluation
separation. The checks and handling of unsuitable annotations remain open;
a correction workflow is not assumed. Dataset size and the time required to
produce suitable data also remain open. The target does not establish
feasibility or change the pilot's proposed sizes.

The pilot includes a small hierarchy built from its masks and prominence before
model selection, using the hierarchy construction being validated. This does not
authorize changes to the title prompt, SSE, grouping method or segmentation. Distinguish
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
generation cost while preserving mask and prominence quality. Its actual
batched speed and task quality remain unmeasured; fewer active parameters do
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
| Initial training set | 250 | First comparison across all three models |
| Expanded training set | 500 | Measure improvement from more notes |
| Further expansion | 1,000 | Conditional on the preceding results |
| Validation set | 100 | Compare development runs and select settings |
| Final test set | 200 | Evaluate selected candidates after development stops |

These counts are proposed measurement points for the larger pilot, not the
initial informal experiment using the available 100 notes or demonstrated requirements.
One thousand notes is not a prerequisite for the first training experiment.

The 500-note set retains the original 250; the 1,000-note set retains the 500.
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
annotation. The assistant performs the review and asks the user about genuinely
uncertain decisions. This review policy is proposed, not a release requirement.
How unsuitable annotations are handled remains open; preserve teacher outputs
separately from review findings and any subsequent changes.

## Proposed run sequence and controls

1. **Check each training setup on a small sample.** Verify complete-note input,
   the agreed output format, source alignment, working training, GPU memory use,
   and measured speed. Record whether prominence is included. Training loss and
   successful parsing are setup diagnostics, not evidence of semantic quality.
2. **Measure the three untuned baselines.** Use the shared validation notes and
   preserve their outputs before fine-tuning.
3. **Train all three models on 250 notes, then on 500.** Start each dataset-size
   experiment from the same original pretrained weights, not from the previous
   experiment's adapted model.
4. **Control training work within each model.** Keep its recipe fixed across
   dataset sizes and compare checkpoints after matched amounts of training.
   Otherwise, more notes also means more training, and an improvement cannot
   be attributed to additional distinct notes alone. Preserve earlier
   checkpoints so overtraining a small set does not manufacture that effect.
5. **Expand to 1,000 when justified.** Do not eliminate a model merely because
   its 250-note result is weaker. Examine its improvement at 500, remaining
   errors, training behavior, and cost before deciding on further investment.
6. **Confirm decision-critical comparisons.** Repeat with a different random
   seed when a small gain or model difference would determine the next action.
   Keep the same evaluation notes and report uncertainty rather than treating
   each mask as an independent observation.
7. **Use the final test after selection.** Compare selected fine-tuned
   candidates with their corresponding untuned baselines on the reserved notes.

The exact training-work budget, checkpoint schedule, and checkpoint-selection
rule must be specified before runs. The earlier three-pass runtime estimates
are not a frozen training protocol. Any recipe change needed to repair a
training problem must be recorded; it cannot silently enter a data-size
comparison as though only the number of notes changed.

At most nine main fine-tuning runs are proposed across the three dataset sizes,
in addition to untuned baselines, setup checks, and limited confirmation runs.
The 1,000-note stage and confirmations are conditional, not a mandate to spend
the remaining budget.

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

### Required pilot measurements

| Measurement | Required evidence | Decision it informs |
|---|---|---|
| Quality on unseen notes | Before/after subject coverage, mask correctness and prominence quality on the same held-out notes | Whether training improves the intended task |
| Improvement with more training data | Quality at each tested data size, under the controls above | Which models and additional annotations merit investment |
| Actual training resources and cost | GPU configuration, peak memory, training time and total rental cost, including setup and evaluation | Feasible hardware and measured inputs to larger-training estimates |
| Batched generation speed | Notes processed per second, output lengths, peak memory and failures on representative notes | Time and cost to process the proposed launch corpus |

Measure semantic quality separately from mechanical correctness:

- **Coverage:** which supported subjects received a faithful mask?
- **Mask errors:** which masks omit necessary meaning or add unrelated meaning?
- **Prominence:** how well do scores reflect the agreed meaning of prominence?
  Freeze its review criteria before comparing models; do not infer correctness
  from valid numbers or combine its errors with mask errors into one score.
- **Mechanical failures:** which outputs are malformed or cannot be located
  correctly in the original note?

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
output lengths or prominence labels required by the current extraction work.

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
that the pilot is scientifically sufficient. Its amount, the final-training
reserve, and the dataset-size schedule remain open; no fixed pilot/rest ratio
has been adopted.

### Runtime estimates — not measured

The following September 15 estimates predate the current subject hierarchy and
the addition of prominence. They are not measured runtimes for the release task.
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
