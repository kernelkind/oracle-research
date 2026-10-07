# Fine-tuning pilot

For the experiment's sequence—shared data, untuned baselines, training,
evaluation, and model comparison—start with
[the pilot walkthrough](../docs/planning/fine-tuning-pilot-process.md).
Implementation and deployment details are recorded below.

## Status and scope

**October 2 subjects-only decision:** the larger pilot trains and evaluates
subject discovery and hierarchy only. One teacher hierarchy per training note
yields 1,000 examples and 125 updates per student, 25 per 200-note block. No
mask labeling, training or generation belongs to this pilot. The combined
preliminary experiment remains historical evidence; the eventual mask-based
release task below has its separate scope. Two 96GB RTX PRO 6000 cards are
approved for the combined rental up to $285; actual GPU fit and speed remain
pending. Thinking stays off throughout
preparation, training and evaluation, approved October 2.

**Primary comparison approved October 5:** compare all three final 1,000-note
adapters with their untuned baselines on the same 200 held-out test notes.
Collect the 1,200 test responses during the main rental, sealed through local
validation review and model selection. Keep all five 100-note validation stages
to show learning progress; earlier checkpoints are retained diagnostics.
Final-test collection and completeness checks are implemented locally; automatic
reports exclude test answers and semantic scores. The full ASv6.100 workload is
packaged and conditionally priced (October 5 section below); hardware checks
remain pending; the combined rental is approved up to $285.

**Release-plan tracking:** the preliminary 100-note experiment below is task
**29 · Run preliminary 100-note fine-tuning experiment**, in progress. The larger
model-selection pilot is **06 · Choose model through larger fine-tuning pilot**,
waiting for larger-run preparation and semantic scoring. Its data is frozen.
The planned pilot includes a comparison trained on
1,000 notes, approved September 30. On October 1 the user requested three
continuing student training runs, replacing separate fresh starts at each size,
and approved validation checkpoints at 200, 400, 600, 800, and 1,000 training
notes. The 1,000 train / 100 validation / 200 test split was approved October 4.
Task 18's preliminary training setup
is complete. The subjects-only continuing worker is implemented locally;
GPU fit remains open. The background copier
is implemented locally.
Task 29 needs 01 + 18, not the larger-pilot data
in 05, and its findings inform 06 without becoming a new completion gate.
Splitting the tracking does not change the experiments or spending approvals.

**Separate preparation agreed October 1; confirmed October 3:** use existing
notes for a small GPU preparation run while the larger pilot data is pending.
Prepare the minimal hardware checks and rehearse the packaged workflow locally
before booking. Training, checkpoint reload/merge, batched generation and
restored training are the proposed checks, with thinking off throughout.
Evidence applies only to tested input/output memory bounds; audit the actual
pilot data's token lengths against those bounds when it is ready. Future answer
completeness is not established by this preparation. The local preparation
mode, frozen input package and VM rehearsal are ready. The user approved
proceeding with the $5 preparation on October 3. The tested image is published
and verified private. A refreshed compatible 600 W quote fits the approved
$5: $1.4522/hour, or $4.41 for three planned hours including transfer allowances.
The $7 request is withdrawn. Vast rejected the request with HTTP 400.
The specific rejection explanation was not retained. The user approved revised
selection filters and proceeding within $5. A better refreshed 96GB/600 W offer on the host costs $1.4656/hour, or $4.40 for three planned hours
including transfers. A new frozen operation uses the unchanged tested image and package.
All 125 available work files and six startup files were reverified. Qwen completed all checks; Gemma
dense has only its first checkpoint, and MoE did not start. The local per-layer
dimension fix is committed; its rebuilt VM passed all 56 tests. Reuse was
approved, then cancelled by the deletion instruction before implementation.
This attempt left the Gemma checks incomplete; the repaired run below completed
them. The final resource cost was $1.620.
**GPU preparation completed October 3:** Qwen's verified earlier checks are reused;
Gemma dense and MoE both completed two updates, save/reload/merge, 20 brief subject
responses, native maximum-output cache checks and restored training on the preparation run
(96GB/600 W, $1.4153/hour including storage). All 210 work files and six startup files
were retrieved and independently rehashed. The local response review ran at 21:04 UTC,
full completeness review passed at 21:17:21 UTC. This rental lasted 65.5 minutes.
The final preparation costs were $1.756 and $1.620 ($3.376 combined).

Direct SSH copying was slow; the verified provider proxy route completed retrieval using
the unchanged native transfer code. Small sealed responses and measurements were copied
ahead of remaining checkpoints. Frozen remote code, inputs and operation contract stayed
unchanged. The October 3 launcher update selects the provider proxy from the start
for new distillation operations, honoring an explicit direct SSH setting when supplied.
Both progressive and final transfers prioritize small sealed outputs, copying each
completion marker after its files. Streams carry at most 64 MiB; the background
copier rediscovers sealed files between streams so newly saved responses can
precede an unfinished checkpoint. Partial files are retained and checked
against the complete saved SHA256 before publication. New launches require a fresh
package and image from the updated source; historical operations stay frozen. Future
pilot data must fit the measured training and cache shapes. Rentals below $1.60/hour
need no further approval for the authorized prep; straightforward failures are repaired
promptly, otherwise available data is verified and the prep rental explicitly deleted.
No automatic timeout or deletion.

GPU checks passed for the measured cases below; actual pilot data must fit those bounds.

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
The larger pilot freezes prep and pilot stages together. Successful prep
continues on the same rental with fresh pilot adapters; failed prep preserves
verified evidence before deletion and local repair.

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

Verification now defaults to **cached** mode. It automatically reuses successful
candidate, workflow and deployment stages when their source/test/dependency
hashes match and every saved evidence file verifies. A controller-only edit
reruns deployment checks while retaining model checks. Model, runtime or
unclassified dependency changes invalidate the dependent checks. Optional
preflight inputs are snapshotted and hashed; changed inputs rerun deployment.
When the VM boots, reuse also requires the exact installed Docker `runtime`
image ID, including system and Python dependencies.

Use **`--full`** to force every check to run; Docker build caching remains active.
Agents may choose either mode, but cannot override evidence validation. A new
`--directory` still provides a clean-machine check. Legacy attempts without the
new stage receipts cannot supply cached test evidence.

Stages are sealed only after their commands and cleanup succeed. An export or
collection failure can therefore reuse any intact, retrieved successful stages
on the next invocation. Partial exports are removed; failed stages rerun.
An unchanged complete attempt verifies locally and returns its existing result
without booting QEMU.

Each new attempt records executed/reused stages and timings in
`verification.json`. Stage logs and hashed receipts live under
`results/stages/{candidates,workflow,deployment}/`; `complete.json` identifies
the workflow report and hashes the final archive and image metadata. These
checks establish the local workflow; full-size CUDA fit still needs GPU prep.

**October 6 verification:** 53 host checks and 109 VM checks passed, with five
expected VM skips (four exercised in their separate volume phases, one requiring
an optional tokenizer package). The cold full rehearsal took 14.5 minutes;
an unchanged cached invocation took 2.24 seconds. With the local archive
temporarily withheld and preserved, a real export retry reused all three stages
and completed in 99.6 seconds. Both VM attempts stopped and their results verified.

**October 6 cutover:** integrated into `main`. The matching verified attempt
is copied to `target/distillation-vm-clean-deployment/`; the normal cached
invocation verifies in 2.22 seconds and all 53 host regressions pass there.
The Dockerfile now names its dependency-only `runtime` stage. Future
launch images and packages must use this updated Dockerfile; earlier frozen
inputs and private publication evidence remain intact.

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
retain it without starting training. Historical bounded packages request a stop
and retrieval on expiry, controller errors or interruption. The current
timeout-free preparation package keeps its job running in all three cases.
The returned result reports that
billing remains possible and manual stop is recommended.

The explicit `stop` command stops the workload, retrieves available results and
**deletes the instance**, confirming absence twice. This is the command operator
action required to end the rental. A retained instance continues billing; stopping
the worker does not stop rental charges or enforce the $25 ceiling. Budget
admission, cost warnings and worker runtime limits remain in force.
For the current timeout-free package, stop/delete additionally requires a
completeness review and verified local data, or explicit user approval to stop
incomplete work. Cost and elapsed-time thresholds call for review.

The September 29 informal operation preserves its first session deadline across restarts and leaves
15 minutes for retrieval and explicit deletion before the approved 13-hour
ceiling. An operator must act within that allowance. Run supervision in a
persistent local session; if the local process or host dies, an operator must
resume it. That historical worker separately enforces its frozen runtime limit across all
candidates and kills download/training subprocess groups on timeout or stop.
The current timeout-free package has no such runtime limit.
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

Optional `evaluation_tasks: ["subjects"]` skips mask generation during evaluation.
Legacy joint training uses the two-task dataset; the continuing subjects-only
configuration below uses one teacher hierarchy per training note.
Optional `subject_batching` enables memory-based grouping for one complete,
unquantized model on one device. Its explicit integer fields are `budget_bytes`,
`workspace_bytes`, `prefill_bytes_per_token` and `attention_matrix_count`. They
freeze the memory ceiling, fixed scratch/headroom, per-token prefill allowance
and attention-score buffer count. No numeric GPU defaults are inferred.
The calculation counts actual resident tensors, full/sliding KV caches, Qwen
recurrent/convolution state, cache updates, padded prefill and decode attention,
and the full output allowance. Unsupported cache or generation settings fail
before model calls. Tokenize once and seal `subject-batches.json` before
generation. Save one `subjects-NNNN.json` receipt with all answers and measured
batch duration before publishing separate `subjects.json` and
`subjects-result.json` files per note. Parse each note before starting the next
batch. Saved malformed/truncated answers remain failures. A saved receipt can
finish interrupted publication; a started generation without a receipt blocks
automatic retry. Batch estimates require GPU preparation evidence; CPU tests
do not establish CUDA fit.

October 2 verification passed 24 host checks and 39 tests in the pinned VM
container. Tests exercised short/long inputs, full output reservations, missing
responses, interrupted publication, CLI resume and frozen-policy rejection,
small versions of all three architectures before/after adapter training, and
shared SSH deployment with verified retrieval. All four retrieved dynamic
baseline/trained stages reverified locally. The VM is stopped and its container
export is retained under `target/distillation-vm-clean-deployment/`. Numeric
96GB GPU allowances remained open; the continuing training implementation
is described below.

Subject and position-mask decoding accept bare JSON or one complete Markdown
code fence labelled `json` (case-insensitive) or unlabelled. Existing field,
duplicate-key, hierarchy, verdict and position validation still apply. Raw
answers are retained. Parser changes do not rewrite a completed evaluation;
apply the same decoder to both baseline and trained answers in a separate
evaluation before comparing their scores.

The legacy two-task JSON config requires explicit model/revision, prepared-data and mask-prompt
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

For continuing subjects-only training, set `training_milestones` (the pilot uses
`[200, 400, 600, 800, 1000]`), supply subjects-only data and `subject_batching`,
and retain the shared model, precision and LoRA settings. Omit `mask_prompt`,
`mask_batch_size`, `subject_fraction`, `max_steps` and `save_steps`;
`max_new_tokens` contains only `subjects`. Physical `batch_size` times
`gradient_accumulation_steps` must equal eight. Prepare this data through
`distillation_data.py --tasks subjects`; no mask labels or prompt are needed.
The worker freezes `training-plan.json`, shuffles within the configured blocks,
and visits every note once. It normalizes each physical group against the
entire update's teacher-token count, uses AdamW and a constant schedule, and
records loss, gradient norm, supervised tokens, note IDs and CUDA allocated/
reserved memory. Each `checkpoints/checkpoint-N` contains the unmerged FP32
adapter, `training-state.pt`, tokenizer, counters/coverage and file seal. Verify
required files, identities, counts and hashes before use. Release training,
reload and verify the adapter on a fresh original base, merge that disposable
copy, and save raw/parsed subjects under `evaluations/checkpoint-N`. Check
response accounting before restoring the full training state, including random
state after reconstruction. Keep every milestone checkpoint. `--through train`
includes milestone evaluations and skips the aggregate report. The report
contains response reliability and returned-subject counts; semantic scoring
remains local and separate.

October 2 continuing-worker verification passed **29 host checks and 48 VM
tests** (3 architecture, 28 worker/data and 17 deployment/Vast/data tests).
Scaled five-milestone jobs completed through the full CLI and shared SSH
deployment/retrieval. The same CPU updates with and without intervening merged
evaluation produced exactly equal adapters, Adam state, schedule and random
state. Interrupted response publication resumed without regenerating baseline
answers or changing training state; all five recovered adapter files matched
the original hashes. Unequal-length teacher answers with physical groups of
one and eight used the same 382 supervised tokens and loss within 1e-5;
adapter tensors agreed within 1e-6 absolute / 1e-4 relative tolerance. Missing
responses, even under a valid file seal, and wrong update counts blocked
advancement. Both retrieved runs retained five checkpoints and twelve total
baseline/checkpoint evaluation stages; all seals and expected raw/parsed
responses reverified locally. All three tiny architectures retained frozen
original weights, including MoE routers, and supported expert-adapter merge.
The VM is stopped. Full-size BF16 GPU fit and throughput remain unverified.

The command workload supports optional `progressive_copy` with positive integer
`poll_seconds`, `bytes_per_second` and `timeout_seconds`. Distillation
specifications freeze software defaults of 5 seconds, 8 MiB/s and 900 seconds;
settings can supply other controls before freezing. These defaults are not GPU
throughput measurements. `run --watch` starts one local copier, with separate
locks and status under `progressive/`. It records failures and allows three
automatic restarts; the fourth failure requires inspection. The worker seals
root `manifest.json`/`training-plan.json` provenance before loading weights, and
publishes named completion records for batch plans, started calls and receipts
before the whole stage completes. Discovery includes those immutable subsets,
prioritizing their files before their markers. The worker seals each raw/parsed subject
response before the next generation batch; completed checkpoints already have
atomic directory publication. Discovery reads completion records and file
sizes, without repeatedly hashing large remote tensors. Exclude partial
checkpoint directories. Transfer processes use remote nice 19 and idle disk
priority, and stream at the frozen bandwidth limit. Both progressive and final
retrieval prioritize sealed directories by total saved bytes, then path. Each
directory's completion marker follows its files, including nested sealed
directories; unsealed files use their individual sizes. This keeps small
responses ahead of checkpoints without advertising incomplete local directories
as complete. Each stream carries at most 64 MiB and 32 files. The watcher
rediscovers seals after each completed stream,
without sleeping while data remains, so newly published responses precede the
rest of a large checkpoint. The configured polling interval applies when no
new bytes or files were copied. New responses can be prioritized after the
current stream rather than after the entire checkpoint; response backlog,
connection setup, discovery, hashing and link speed still affect delay. A
64 MiB payload at the default 8 MiB/s cap takes at least eight seconds; actual
transfer time can be longer. This chunk size amortizes the costly proxy SSH
setup observed during preparation. New distillation launch settings select
the provider SSH proxy
from the start, using the existing managed key and authentication loop;
explicit direct SSH settings remain supported. No slow direct-route trial or
hardcoded endpoint wrapper is needed under the new default.

Receive partial bytes under `progressive/partial`, verify the complete file
SHA256 and size, then atomically publish it under `result.next/work`. Separate
receipts record successful verification and local modification time. Resumption
uses received offsets and previously verified files; do not replace changed or
corrupt evidence. A missing receipt after successful file publication is
reconstructed after one integrity check. Copy failures are visible in
`progressive/status.json` and ordinary status, without stopping training.
Terminal retrieval stops new copy batches, seals the stopped remote tree,
reuses already verified work files, retrieves missing files and preparation
evidence, and verifies the complete final file set. The copier never removes
remote originals or deletes the rental. Full checkpoint sizes and transfer
charges must be included in the larger pilot's separately approved allowance.
GPU preparation must measure the transfer effect on workload throughput.

October 2 copying verification passed **129 controller regression tests, 27
host distillation checks and 50 pinned-container VM tests** (3 architecture,
29 worker/data and 18 deployment/Vast/data). Production reception resumed a
truncated byte stream, rejected corrupt contents and recovered a missing
verification receipt without repeated large-file hashing. The controller
reported copier startup, status-write and process-exit failures without
stopping training. Real SSH execution saved subject responses and a complete
checkpoint locally while the worker was running. Final retrieval reused 174
files (4,322,227 bytes), and all 246 terminal work files plus six preparation
files reverified locally. Both students retained all five complete checkpoints,
with all twelve evaluation stages and twenty-four raw/parsed responses verified.
The copier and VM stopped, the container export passed, and the final source
hashes match the VM snapshot. During repeated rehearsals, accumulated artifacts
filled the local 64 GiB disk during export; expanding that reused disk to
128 GiB preserved earlier evidence and allowed the export to finish. The fresh
VM default remains 64 GiB. These checks do not establish full-size GPU impact.

October 3 transfer automation passed **59 command-workload regressions and
58 VM tests** (4 architecture, 30 worker/data and 24 deployment/Vast/data),
with no VM skips. A new production-path test reproduced premature local
completion-marker publication; ordering now publishes each marker after its
verified files. Real SSH copied a 128 MiB checkpoint in bounded streams while
retrieving a newly sealed response before checkpoint completion. Live training
and terminal retrieval checks passed. Routing settings survive preparation;
new distillation launch defaults select the provider proxy. The broader
controller suite retains one source-comparison failure, also reproduced on
committed HEAD, for earlier command-stopping changes to `remote_supervise`,
`remote_stop` and `destroy_instance`; its 80 other checks passed. Artifacts are
under `target/distillation-transfer-v1/`; `verification.json` records source
hashes and copy receipts. The VM stopped and its image export completed;
current source files match the VM snapshot. The archive SHA256 is
`7b69803b70f0a5b19ea0535885482e218347bef37cc1c4ec38f5640e47926863`.
This is an archive hash, not a published registry digest. No rented hardware
was used.

The automatic report separates malformed subject/mask outputs, valid empty
masks and reference agreement. Token overlap uses whitespace-delimited source
words (any selected part includes that word), with one-to-one matching and
micro averaging over unique nonempty selections per note. Exact matching uses
selected non-whitespace source characters. These mechanical measurements do
not establish semantic correctness or approval; the semantic-review rubric remains open.

The subjects-only worker checks baseline response accounting before training
and checkpoint response accounting before advancing. Invalid/truncated model
answers remain measured failures; missing raw/parsed responses or invalid
checkpoint coverage block advancement even if a directory has a file seal.
The legacy combined evaluation can omit mask calls after failed subjects, as
seen in the preliminary run.
[The walkthrough](../docs/planning/fine-tuning-pilot-process.md#2-generate-untuned-baselines--vast)
records the larger pilot's response requirements. Semantic review of saved results runs
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

The informal experiment trained both prompted tasks. The larger pilot now
trains subjects only: complete original note → teacher subject hierarchy. The
intended direct release task below remains a later experiment, outside the
subjects-only pilot contract.

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

The user froze full ASv6.100 for the larger subject-only pilot on October 4,
as recorded below. The eventual mask task requires its separately validated
mask prompt; the superseded ASv6.23 / MPv3.5 commitment does not select that prompt.
Freeze teacher model settings, output format and reviewed labels for each
controlled comparison. Preserve the
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

The subjects-only pilot assesses the generated subject hierarchy before model
selection. It supplies no evidence about mask quality or the downstream
mask/SSE hierarchy build. Release-plan task 11 still checks the final distilled
model. This pilot does not replace scale measurements or establish full-build cost.

## Models and required untuned baselines

| Model | Proposed adaptation | Role |
|---|---|---|
| Qwen3.8-27B | BF16 LoRA | General-model candidate |
| Gemma 4 31B instruction-tuned | BF16 LoRA | Different pretrained foundation |
| Gemma 4 26B-A4B instruction-tuned | BF16 LoRA including routed experts | Mixture-of-experts quality–cost comparison |

The user approved these three candidates on September 24, 2026, replacing
T5Gemma 9B–9B PrefixLM instruction-tuned with Gemma 4 26B-A4B instruction-tuned.
The MoE candidate tests whether lower active computation can reduce corpus
generation cost while preserving subject correctness, coverage and hierarchy
quality in this pilot. Its actual batched speed and task quality remain unmeasured; fewer
active parameters do
not establish lower training memory or cost. See the
[published evidence](EXTRACTOR-FINETUNING-MODEL-RESEARCH.md#gemma-4-26b-a4b).
The later approved recipe is recorded below; selecting candidates does not
approve spending.

For each model, evaluate its original released checkpoint before training on
our annotations. Its existing pretraining and instruction tuning remain intact.

Within that model's before/after comparison, keep these unchanged:

- Evaluation notes and task instruction.
- Output format and input preprocessing.
- Decoding settings and inference precision.
- Semantic review criteria and mechanical checks.

Both versions begin with the original note and generate its subject hierarchy.
No reference subjects are supplied during evaluation. The completed informal
experiment also requested masks for its generated subjects; that mask stage is
outside the larger pilot.
Preserve all original outputs. The untuned result is the zero-training-note
point on that model's learning curve. The Astra pipeline is a separate reference,
not a replacement for these three baselines.

Different models can use appropriate training settings and native input
formatting. Comparing their practical quality and cost does not isolate the
effect of architecture alone. A Qwen-only setup test cannot establish that
either Gemma checkpoint's training setup works.

## Approved pilot data

| Set | Distinct notes | Purpose |
|---|---:|---|
| First training checkpoint | 200 | First trained validation point for all three students |
| Second training checkpoint | 400 | Measure improvement along the same training run |
| Third training checkpoint | 600 | Measure improvement along the same training run |
| Fourth training checkpoint | 800 | Measure improvement along the same training run |
| Fifth training checkpoint | 1,000 | Included comparison, approved September 30 |
| Validation set | 100 | Track learning progress and select among final 1,000-note versions |
| Final test set | 200 | Compare all three final adapters and untuned baselines after validation review |

The user approved inclusion of the 1,000-note training comparison on September 30,
validation every 200 training notes on October 1, and one complete training pass
after the October 1 research. The 100 validation / 200 test counts were approved
October 4. These are for the larger pilot, separate from the informal
100-note experiment. Each student has five trained validation points plus its
untuned baseline.

Each larger training set retains all earlier notes and labels, adding 200 notes.
All models receive the same sets. Choose broadly varied real notes while keeping
topic, writing-style, and length mixtures similar across sizes. Do not simply
use our food/music-heavy existing annotations as evidence of broad coverage.
The informal experiment deliberately starts with available data; its findings
must be described in terms of that selected collection.

Split before training. Keep duplicate, closely related, and same-author material
within one split. The final test notes and their teacher labels are frozen;
keep their outputs out of development and selection. Do not use test outputs
to revise the experiment.

Mechanically check every teacher subject hierarchy and note/example identity.
Semantically review a varied sample of training annotations and every
validation/test annotation. Annotation checks belong to local preparation before training.
The review method and uncertainty handling remain design choices; the user's
role is reviewing that design, not supplying example labels or adjudications.
Review of saved candidate outputs follows the
[approved structure](#semantic-review--approved-structure), occurs after retrieval
outside the rental, and does not feed judgments back into training. The detailed
rubric and release acceptance requirements remain open.
How unsuitable annotations are handled remains open; preserve teacher outputs
separately from review findings and any subsequent changes.

## Proposed run sequence and controls

1. **Freeze and rehearse paired prep/pilot stages locally.** Check the actual
   longest complete pilot examples and planned cache shapes on the selected
   GPU. If all prep checks pass, discard prep adapters and continue into fresh
   pilot adapters on the same rental. Training loss and successful parsing are
   setup diagnostics, not evidence of semantic quality.
2. **Measure the three untuned baselines.** Use thinking off on the shared
   validation notes and preserve their outputs before fine-tuning. While each
   untuned base is loaded, also collect its 200 test answers and keep them sealed.
3. **Start one continuing training run per student.** Initialize the adapter
   and optimizer from the original pretrained model once. Use every frozen
   subject example from the first 200-note block once, without
   replacement. Save a complete checkpoint after finishing that block and
   generate subject hierarchies
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
6. **Complete and verify sealed test collection on the main rental.** Generate
   the 200 reserved notes for each final 1,000-note adapter, using thinking off,
   alongside the untuned test answers collected above. Collect final-adapter test
   answers while its evaluation copy is loaded. Check accounting/parsing/files
   immediately; keep test content
   and semantic scores out of review and selection. Verify all 1,200 test
   responses and all other required work locally before explicit deletion.
7. **Review validation, then unseal the test locally.** Use the final 1,000-note
   validation versions for primary model selection. Score and report all three
   final adapter/baseline comparisons on the same test notes. Freeze review
   criteria and check the grader before unsealing. Report uncertainty without
   treating subjects within one note as independent observations. One seed
   does not measure training-seed variance; extra trials require a separate
   decision if a small difference would determine the next action.

The primary comparison is fixed at 1,000 notes; it does not establish each
student's best possible checkpoint. Keep earlier validation peaks in the
learning curves. Confirming an earlier checkpoint on the test notes requires
additional inference, not retraining; do not select it from test results.

**Research basis for this scoped comparison:** [GuideX](https://arxiv.org/html/2506.00649v1)
reports untuned/trained variants on shared held-out extraction tasks.
[September 2026 checkpoint-selection research](https://arxiv.org/html/2609.36569v1)
finds no clear overall gain over the final checkpoint in its math/commonsense
experiments; that is not proof for subject hierarchies. Fixing the primary
comparison at 1,000 notes is a practical pilot decision, not a claim that the
last checkpoint is universally best. [NLP evaluation research](https://aclanthology.org/2020.emnlp-main.745/)
warns that small evaluation sets can exaggerate differences. The local grader
also needs checks for biases such as rewarding verbosity, documented in
[LLM-as-a-judge research](https://arxiv.org/html/2306.05685v4).

### GPU preparation cases and checks — draft

**Two-GPU execution approved October 5:** keep each complete student on one
**96GB RTX PRO 6000**. GPU 0 runs Gemma dense; GPU 1 runs Qwen, then Gemma MoE.
All preparation results and baselines are verified before training. Matched prep
cases and numeric settings are frozen. Private publication and up to $285 are
approved for a compatible two-card 96GB/600 W RTX PRO 6000 Server rental within
the $3.10/hour ceiling; actual GPU fit/throughput remains pending.
Use the same pinned models and approved subject-only adapter recipe as the
pilot. Prepare locally and rehearse production paths in the VM before booking.
The worker now supports subjects-only preparation/training, expert adapters,
memory-based subject batching and the save/merge/evaluate/restore lifecycle.
The background copier is implemented locally. Preparation and the pilot use
thinking off throughout.

**Preparation cost priority approved October 3:** minimize total billed cost.
Collect update, generation and save/reload/merge/restore timings during the same
minimum cycle to project a pilot duration/cost range; separate cold setup from
repeated work. Keep parser/recovery testing and automation rehearsal local.
Compare qualifying 96GB offers by expected total charge, including startup,
storage and transfers. After checks, finish verified retrieval and explicit
deletion promptly when prep is separate. The current matched prep scope is
frozen and the combined prep→pilot rental is approved up to $285.

Use existing notes; preparation is not blocked by the future 1,000-note dataset.
Historical N18 (long diary), N00 (soda bread) and N15 (short gianduja/store note)
are candidate cases, not an approved three-note evaluation set. Tokenize the
available cases and declare the maximum training sequence, rendered input and
generation/cache shapes to test. Freeze source IDs, prompt versions, example
IDs and profile identities locally. The final cases and shape-testing method
remain open. When the pilot data arrives, audit its token lengths against the
tested bounds locally; reconsider out-of-bounds configurations before booking.
Keep reserved final test notes out of preparation. A few existing notes cannot
prove that future trained subject hierarchies finish within an output limit.

**Dynamic evaluation batching approved October 2:** prepare a per-GPU memory
budget locally under the actual model placement. Before each generation batch,
tokenize waiting notes and choose how many fit that budget. Account for resident BF16
weights, per-note cache and recurrent state at maximum admitted prompt plus
output length, padded prefill/decoding tensors, kernel temporary buffers and
allocator headroom. Account for sliding-window caches and Qwen's recurrent
layers rather than assuming every layer stores a full-context KV cache.
Reserve for generation through the allowed output length, not just initial free
memory. Each batch's count can change with its token lengths; choose the count
before generating. The worker now implements the calculation with explicit
frozen allowances; numeric GPU budgets remain open.
Freeze the thinking-off batching policy per student and match baseline/checkpoints;
preserve per-note outputs. The proposed small preparation checks execution and
peak memory; brief timing is not a complete-answer throughput estimate. No
standalone batch-size rental sweep is prescribed. Historical recipes retain
serial subject generation unless the new `subject_batching` policy is supplied.

**Proposed minimum GPU cycle, once per student; exact cases/counts remain open:**

1. Verify model revision, kernels, dtypes and adapter targets. Perform one
   eight-example adapter update with existing teacher subject hierarchies;
   record finite loss/gradients, adapter changes, frozen base/router, expert
   gradients and actual example/token accounting.
2. Save and seal the full checkpoint. Unload training, reload a fresh BF16 base
   with the saved adapter, and merge it. Record reload/merge time and peak memory.
3. Run brief thinking-off batched generation; save raw/parsed responses, tokens,
   timing and peak memory. Check every expected response immediately. Separately
   exercise the maximum admitted generation/cache shape on the GPU if the brief
   answers end early. That brief shape-check method must be implemented and
   rehearsed locally before booking; a short answer alone cannot verify it.
4. Discard evaluation, restore full training state and perform a further update,
   exercising the declared training length with Adam state resident. Verify
   restored counters, order, cursor and random state; retain verified checkpoints.

The existing worker performs full subject-evaluation stages. The proposed brief
generation, maximum-shape check and merge/generation peak measurements still
need local implementation and rehearsal. Use the production training and
save/merge/restore paths. Do not add complete baseline/checkpoint hierarchy
comparisons, semantic review or tuning sweeps to this paid preparation.

Keep parser, missing-response, partial-checkpoint, continuation-equivalence and
interrupted-transfer checks local through production paths. The copier still
transfers preparation files as they become complete. Observe responses, training
and telemetry until verified retrieval and explicit deletion; automatic deletion
stays off. Record allocated/reserved CUDA peaks, GPU utilization/power, host
memory/disk, lifecycle timing, call accounting and verified files. A failure
preserves evidence for retrieval; fix and rehearse locally before any new rental.
Numeric memory budgets, caps, exact checks, implementation and spending remain open.

### Execution and failure handling (draft)

The [process walkthrough](../docs/planning/fine-tuning-pilot-process.md) maps
where each stage runs. Subjects-only training, ordinary checkpoint evaluations
and stage accounting are implemented. Ongoing response/checkpoint copying is
implemented locally. Thinking stays off throughout the pilot. The legacy
informal configuration still uses both tasks.

- **Local preparation:** freeze note splits, teacher subject hierarchies, prompt
  versions, model revisions, data order and approved recipe. Rehearse locally;
  use paired GPU prep to cover the finalized longest training example and full
  validation cache shapes. Freeze admitted lengths and thinking-off output limits before launch;
  brief GPU preparation does not establish future answer completeness.
- **GPU execution:** generate one thinking-off untuned validation baseline per
  student using batched independent notes under the frozen policy. Use the same
  policy for its trained checkpoints and preserve each note's answer separately.
  Verify all three complete baselines before any pilot training. Initialize one
  adapter and optimizer per student; learn each new 200-note block once. Shuffle
  its 200 subject examples with a fixed seed and take consecutive groups of
  eight total across all GPUs: 25 updates per block and 125 through 1,000 notes.
  Save and verify every complete milestone checkpoint, unload training, load a
  fresh pinned BF16 base with its saved adapter and merge this evaluation copy.
  Generate subject hierarchies on the same validation notes, saving raw/parsed
  answers and failures immediately. Discard evaluation and restore untouched
  training state and exact next-example position before continuing. Validation
  does not update training weights. Teacher targets contain no reasoning traces.
- **Checks and live observation:** account for one subject response per expected
  evaluation note as it arrives. Invalid model answers are measured failures;
  missing work or parser/pipeline defects block advancement of affected work.
  Observe actual baselines before training, training progress/GPU telemetry and
  trained answers through verified retrieval and explicit deletion.
- **Progressive retrieval — approved design:** one background copier transfers
  each saved subject response and complete checkpoint while execution continues.
  Verify local hashes and retain remote originals at least until verification;
  limit bandwidth/disk activity to protect throughput. Before explicit deletion,
  verify expected work and required local files. Preserve responses, failures,
  adapters, configuration and telemetry. Automatic deletion stays off.
- **Local scoring:** mechanically check output reliability; review subject and
  hierarchy correctness/coverage after retrieval. Keep model failures, semantic
  findings and missing reviewer verdicts distinct.
- **Final test — approved October 5:** collect all three final 1,000-note
  adapters and all three untuned baselines on the main rental, with thinking
  off. Keep answers sealed through local validation review/model selection.
  Then score all three paired comparisons; verify test collection completeness
  before deletion. Earlier checkpoints remain learning-curve diagnostics.

| What happened | Response |
|---|---|
| Invalid or truncated model answer under frozen settings | Preserve it, count the failure and continue independently evaluable notes. |
| Missing work, defective parsing, wrong inputs or damaged files | Stop advancing affected work, preserve/retrieve evidence and mark the comparison incomplete. |
| Interrupted execution or observation | Reconcile the existing worker before starting anything; reuse saved responses and resume only a verified checkpoint under original settings. |
| Missing or invalid reviewer answer | Record an evaluation failure separately from candidate correctness/coverage. |

Parser fixes can re-evaluate saved answers consistently; missing responses need
actual generation. Changed settings require a separately identified matched
comparison. Preserve originals and prepare fixes locally. A sealed
`complete.json` verifies files, not completion of every required call. The
subject-response and checkpoint accounting and background copying are
implemented locally. Full-size GPU behavior still needs preparation evidence.

With three students and five checkpoints each, thinking-off validation has
18 versions (three bases and fifteen checkpoints). For N validation notes,
**18N subject responses and semantic reviews**; at 100 notes, **1,800**. The
approved six-version 200-note final test adds **1,200**, for **3,000 total**
student responses and semantic reviews. Freeze generation/review lengths, stored adapters, transfer
volumes and resource allocation before launch. Report over-limit reviewer
inputs rather than truncating them. Test generation is assigned to the main
rental; implementation/verification, runtime and spending remain open.

**Complete-pass budget approved October 1, scoped to subjects October 2:** each frozen subject
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
GPU fit, generation limits and numeric batching budgets remain unresolved.
The merged evaluation policy was approved October 2 below. The subjects-only
worker targets both packed expert weights in every layer at the approved rank
and alpha, preserving frozen original parameters and router. The legacy
128-step recipe retains its earlier expert coverage and replacement sampler.

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
the approved eight examples total per update. Physical groups may vary with
memory while preserving update membership, example order and the update-level
supervised-token denominator. One model replica can accumulate eight one-example
groups on its assigned 96GB RTX PRO 6000. Generation limits and numeric
batching budgets are frozen in the candidate configurations; merged BF16
checkpoint evaluation/resume was approved October 2. All preparation,
training and evaluation use thinking off.
Exact memory fit of the expanded MoE configuration must be checked during
separate GPU preparation. The ordinary continuing training and merged
checkpoint lifecycle and background copier are implemented locally.

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
Check expected subject-response accounting as answers arrive, before advancing the
candidate; completed files transfer through the approved background copier.

After evaluation, discard its model and restore trainable adapters, optimizer,
schedule, counters and the exact next-example position from the untouched
training checkpoint. Restore random state after reconstructing the model and optimizer, then
continue training with training mode, cache off and training checkpointing
restored. No validation answer updates the adapter. This lifecycle keeps one
copy of a given student's model resident at a time and adds cached-base reloads at transitions.
Separate GPU preparation must measure that overhead and merge peak memory, and
verify continuation across the full transition. The subjects-only worker now
retains every milestone checkpoint and restores its full unmerged state after
evaluating a disposable merged copy. Legacy two-task configurations retain
their unmerged endpoint evaluation and two rolling checkpoints. Additional
recovery-checkpoint cadence remains open. Generation limits and numeric
batching budgets are frozen; the combined rental is approved up to $285.

**Training loss approved October 1:** ordinary cross-entropy on teacher-answer
and native turn-ending tokens, summed across the actual adapter update and
divided by its actual supervised-token count. The prompt, note
and padding receive no loss. Do not average separately normalized batch losses;
GPU partitioning and accumulation must preserve the same update-level objective.
Smaller final groups use their own denominator. No extra task, answer, or note
weights are applied. Longer answers contribute more tokens within an update.
The [normalization guidance](https://huggingface.co/blog/gradient_accumulation)
and [comparable extraction implementation](https://github.com/hitz-zentroa/GoLLIE/blob/164c611743fdc1befe71bbdf03e08c5eb4e35957/src/trainer.py#L288-L300)
support this starting objective. The continuing worker scales each physical
group's mean loss by its supervised-token count divided by the update's total;
prompt and padding tokens remain masked.

The preliminary 20% subject / 80% mask replacement sampler is a different
recipe. The subjects-only pilot uses 1,000 unique note/hierarchy examples per
student, once each: 125 updates at global eight. Record loss, supervised tokens,
updates and consumed examples at each milestone. Freeze ordering, checkpoint
procedure and selection rule; preserve actual training history and interruptions.
The continuing subjects-only path implements that stream and full-state
restoration; legacy configurations retain the replacement sampler.

There are **three main continuing fine-tunes**, each with five approved
milestone checkpoints, alongside untuned baselines, setup checks and any
separately justified confirmation work. The 1,000-note comparison is included.
Two 96GB RTX PRO 6000 cards run independent students concurrently: Gemma dense
on one, Qwen then Gemma MoE on the other. Each later milestone continues its
preceding checkpoint. The 100 validation / 200 final test counts and up to $285
for the combined rental are approved.

## Evaluation and decisions

### Semantic review — approved structure

One review prompt per note and model version receives the full note, task
prompt, and that version's subjects and hierarchy. It returns separate
**correctness** and **coverage** scores with evidence for each. Correctness
assesses returned content; coverage assesses missing required content.
Output reliability is checked mechanically. Review runs after retrieval,
outside the rental, and is evaluation only. The scoring scale, rubric, reviewer
model, reliability checks, and score aggregation remain open.

### Required pilot measurements

| Measurement | Required evidence | Decision it informs |
|---|---|---|
| Quality on unseen notes | Before/after subject correctness, coverage and hierarchy quality on the same held-out notes | Whether training improves subject discovery |
| Improvement with more training data | Quality at each tested data size, under the controls above | Which models and additional annotations merit investment |
| Actual training resources and cost | GPU configuration, peak memory, training time and total rental cost, including setup and evaluation | Feasible hardware and measured inputs to larger-training estimates |
| Batched generation speed | Notes processed per second, output lengths, peak memory and failures on representative notes | Time and cost to process the proposed launch corpus |

Measure semantic quality separately from output reliability:

- **Correctness:** how correct are the returned subjects and hierarchy
  relationships for the note?
- **Coverage:** which required subjects or relevant information are missing?
- **Output reliability (mechanical):** missing responses, truncation, malformed
  hierarchy outputs and schema violations.

For resource measurements, record the exact checkpoint, training or inference
configuration, batch size, input/output lengths and billed rental interval.
Separate training time from downloading, loading, checkpointing and evaluation;
include all of them in total cost. Record failed attempts and retries rather than
reporting only the successful run.

Measure generation in batches on a representative mix of real notes, including
long notes and notes producing many subjects. Report those cases separately as well
as the overall rate. Include failed outputs and retries in elapsed time, and
report unresolved failures separately; do not count them as completed notes.
Repeat the measurement with the selected release model and final output format
before committing the full corpus build.

Valid alternative subject wording and hierarchy choices need semantic review;
exact copying of a teacher hierarchy is not the definition of correctness.
Teacher mistakes remain annotation issues rather than automatically student errors.

The assistant reviews outputs with model identities hidden and preserves
concrete examples of improvements and regressions. Summaries must distinguish
semantic findings from parsing success and training loss.

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

## Small GPU preparation — local package ready October 3

`distillation_run --through preparation` uses the existing subjects-only export
and normal training, adapter, generation, checkpoint and retrieval paths. The
frozen proposal is under `target/distillation-pilot-v1/subject-preparation-20261003-v2/`.
ASv6.48 and the existing informal 80/20 split are retained; no future pilot
validation or final test data is used.

Per student, the package selects 16 existing training notes and saves at 8 and
16 notes, giving exactly two eight-example updates. The second block includes
the longest training note after full optimizer/schedule/RNG restoration. Actual
maximum training lengths are 6,531 Qwen tokens and 6,440 Gemma tokens.
After the first save it reloads and verifies the adapter, merges into a fresh
BF16 base, and saves brief subject responses for the 20 existing evaluation
notes in dynamically calculated batches. Generation stops at 64 new tokens;
truncation or parsing failure in these brief outputs is preserved, not treated
as a quality result. There are no full baselines or checkpoint evaluations.

Memory checks use native model forwards to prefill real prompts, fill caches
with synthetic continuation tokens in chunks of 128, then decode one token at
the configured 4,096-token output allowance. They do not generate or judge a
full hierarchy. Longest prompts are 3,232 Qwen tokens and 3,149 Gemma tokens.
The proposed policy budgets 88 GiB, reserves 4 GiB workspace, allows 256 KiB
prefill scratch per token and four attention-matrix buffers. The tested
cache shapes passed this preparation allowance. It is not an approved guarantee
for longer training sequences or future main-pilot data.
Record actual batch shapes, stage timings, raw/parsed responses and peak allocated
and reserved CUDA memory. Compare future data and planned batch/cache shapes
against the measured cases before booking the main pilot.

The production-path CLI test first failed on the missing preparation mode.
The revised VM rehearsal passed 55 tests: tiny models exercise Qwen's linear/full
cache and both Gemma sliding/full caches, adapter merge, training restoration,
real pinned tokenizer preflights, managed SSH deployment and verified retrieval.
The local controller/contract checks passed 65 tests, including refusal to
stop/delete with missing or changed local data, watcher expiry/error/interrupt
preservation, an actual worker without an inherited deadline, and recorded
user approval for incomplete stops. No paid GPU evidence is claimed. The exact
VM export is now published privately as
`docker.io/kernelkind/oracle-mvp@sha256:04628fd9d099cc3deb1d999d0664d000fb4b4ce6ba0a6b9cddc38931fba6832b`.
Filesystem layers, runtime configuration and source hashes match the VM;
read-only rental credentials can pull it and an anonymous-token manifest request
is rejected with HTTP 401. Publication evidence is in the proposal directory's
`publication/publication-receipt.json`. Local test evidence:
`target/distillation-vm-clean-deployment/attempt-1791046788404742039/`.

Proposed rental controls are one 600 W / 96GB RTX PRO 6000 WS, 300 GB disk,
and a three-hour cost-planning/review window. The approved maximum is $5.
The refreshed selected quote is a compatible offer, at
$1.4522/hour including storage. Three planned hours plus 200 GB inbound and
10 GB outbound allowances cost $4.41. The earlier $7 request is withdrawn.
The rejected operation is `operation-5usd/` under the proposal directory.
No GPU checks ran, and the quote is now unavailable. The secret-safe helper
retained HTTP 400 but discarded the provider explanation; the cause is unknown.
The user rejected the 2.5-hour worker stop: the current package freezes
`timeout_seconds: null` and `work_seconds: null`. No execution timeout, watcher
expiry/error/interrupt or budget alert may kill the job. Observation must
continue through verified retrieval and explicit deletion. Prep failures use
the standing prep stopping approval below; preserve all available data.
The latest October 3 offers did not meet
the original very low transfer-fee filter. That filter was an unnecessarily
strict proxy for total cost. The revised approved floors are 125 GiB host RAM
and 450 Mbps download. The new $1.47/hour, $0.00261/GB inbound and $0.00391/GB
outbound ceilings jointly total $4.9711 for three hours and 200/10 GB, within
$5. The refreshed selected quote is a compatible offer, at
$1.4656/hour and $4.40 for those planning quantities; it satisfies the original
hardware floors too. `operation-5usd-r1/` is a separately frozen operation,
using the unchanged native package and private registry digest. Never reuse the rejected attempt.

The constraint review found that 600 W is a preference and 128 GiB host RAM is
unmeasured headroom, not demonstrated minimum requirements. The existing 99.5%
reliability, CPU-core, disk and network thresholds are conservative selection
criteria. The rejected launch satisfied all those hardware filters; none was weakened.
A current 600 W quote with about 126 GiB host RAM and 479 Mbps download costs
about $4.81 for three planned hours including transfers. It is excluded by the
128 GiB/500 Mbps floors and per-GB fee ceilings despite fitting the total budget.
The user approved revising those cutoffs and proceeding. The subsequent better
quote selected above has more host RAM, faster download and lower transfer fees.
The image uses CUDA runtime 13.0.96 and NVRTC 13.0.88, corresponding to CUDA 13.0
Update 2; retain its driver floor of 580.95.05 ([NVIDIA release notes](https://docs.nvidia.com/cuda/archive/13.0.2/cuda-toolkit-release-notes/index.html)).

**October 3 preparation evidence and local repair:** Qwen completed both
eight-example updates, checkpoint restore, merge, 20 brief saved responses and
four maximum-output cache checks. The largest cache shape reached 7,328 tokens;
maximum reserved generation memory across the checks was about 60.4 GiB. Its
second training update recorded about 93.7 GiB reserved, leaving little memory
headroom on this card. These observations cover the actual tested shapes only.
Gemma dense completed its first eight-example update but failed before batched
generation because `head_dim` is a per-layer configuration attribute. The
original tiny-model test used equal full/sliding dimensions and missed that
condition. MoE did not start. All available files and checkpoint seals are
verified locally; that failed attempt did not complete the required Gemma work.
The local fix sums cache sizes from each attention layer rather than accessing
ambiguous global dimensions. A minimal production-path test fails with the
original exception and passes for both Gemma variants after the fix. Existing
integrated lifecycle checks now use different full/sliding head dimensions.
Pinned-image local tests: 50 pass, nine SSH/deployment-VM tests skipped. The
subsequent rebuilt VM passed all 56 tests, including the nine SSH checks and
actual candidate tokenizer preflights. Its source hashes match the committed
repair; evidence is under
`target/distillation-vm-clean-deployment/attempt-1791054641206410906/`. The old
image, package and results are unchanged. Corrected deployment subsequently
completed the remaining Gemma work, as recorded below. The partial first run
did not establish a full pilot cost or cover future data lengths. The user approved
reuse, then explicitly instructed deletion before any deployment support was
implemented. All available files were rehashed again.
The preliminary resource charge was $1.56. Evidence:
`operation-5usd-r1/observations/available-data-integrity-review.json` and
`closure-evidence.json` in the proposal directory.

**Completed hardware measurements, October 3:** all candidates used the same
16 existing training notes and 20 brief evaluation notes, thinking off. Qwen
measurements come from the verified earlier run; Gemmas from the repaired run.

| Student | Two update durations | Generated batch sizes | Max reserved cache memory | Longest training / cached sequence |
|---|---:|---|---:|---:|
| Qwen3.8-27B | 84.4 / 48.9 s | 6, 7, 6, 1 | 60.4 GiB | 6,531 / 7,328 tokens |
| Gemma 4 31B | 50.8 / 86.6 s | 3, 3, 3, 3, 3, 3, 2 | 79.4 GiB | 6,440 / 7,245 tokens |
| Gemma 4 26B-A4B | 21.1 / 29.7 s | 9, 9, 2 | 64.7 GiB | 6,440 / 7,245 tokens |

Twenty 64-token responses took 46.0 s, 56.7 s and 18.2 s respectively,
including batching and prefill. All are intentionally truncated; these
are hardware samples, not quality baselines. Full-output timing still
depends on actual pilot output lengths. Synthetic 128-token cache fills
are parallel forwards and must not be counted as autoregressive decoding.
Update-end reserved memory reached 93.7 GiB for Qwen, 90.9 GiB for dense
and 80.1 GiB for MoE; these snapshots are not exact training peaks.
Qwen and dense have little training headroom. The main data preflight must
compare actual token lengths with the measured cases before rental.

The repaired operation is under `subject-preparation-20261003-v3/`, with
`results-summary.json`, `closure-evidence.json`, and the operation's
`observations/full-pre-deletion-integrity-review.json`. The tested image
digest is `sha256:9bc15608524a0796ecfb5c9d570a4e9c6a7b639bee6e6accdc1b2ee5e34108e8`.
Direct copying transferred only kilobytes per second; the provider proxy
transferred 8 MiB in 10.3 s including connection setup. Prioritizing 148
small sealed response/measurement files put all 40 Gemma raw answers and
parse outcomes locally before the remaining checkpoints finished. Native
verification covers all 210 work files and six startup files. These
operational recovery steps used unchanged frozen code. The subsequent local
launcher update uses the provider proxy by default and prioritizes small
sealed outputs between bounded checkpoint streams.

**Prep stopping exception, approved October 3:** repair straightforward failures
immediately. If recovery requires substantial work, preserve and verify all
available data, then delete the rental promptly. This is standing user approval
to stop incomplete prep work; completing all prep checks is not required. Do not
hold paid hardware idle for substantial new development or renewed permission.
Judge repair scope rather than imposing a fixed time cutoff.

**Autonomous pilot recovery approved October 5:** diagnose and fix errors
without requesting approval for the repair, including necessary code or recipe
corrections. Preserve original frozen inputs and failure evidence, record every
change and interruption, restore verified saved state, and rerun comparisons
affected by changed conditions. The approved spending and complete-data
requirements before stopping/deletion still apply.

**Full pilot stopping rule:** retain the job and rental while
necessary data is missing. Add missing work; if stopping is preferable, obtain
explicit user approval first. Spending approvals still apply; request any
needed extension early instead of treating a financial threshold as permission
to terminate incomplete work. The previously asked approval containing a
2.5-hour job stop is withdrawn. The user explicitly prohibited terminating a
rental merely because spending exceeds the planning budget: report overruns
directly in chat and retain incomplete work unless explicitly instructed to stop.
Questions and approval requests must be asked directly in chat; do not use
question tools.

The shared operator refuses `stop` and direct deletion for this timeout-free
workload without `launch/completion-review.json`. That review records a positive
completeness finding, the checks performed, instance identity, and hashes of the
operation contract and verified retrieval receipt. It must follow actual
response/checkpoint/measurement accounting; exit status zero and file hashes
alone cannot establish all required work. The operator rechecks the retrieved
files before deletion. Missing or changed files block it.
Only an explicit user-approved exception may use `--incomplete-stop-approval`,
recording the actual approval reason locally and with the remote stop request.
For a prep failure requiring substantial recovery, record the user's standing
prep-only approval and the concrete repair assessment with this flag. This flag
is not permission to invent an approval. Preserve original frozen inputs and
defect evidence while adding any necessary repair work.

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

**Subject prompt frozen October 4:** use full
[ASv6.100](subject-prompt-goal-v1/asv6.100/ASv6.100.md), including every worked
example, for training, untuned baselines, checkpoint validation and the final test.
Source SHA-256:
`76aa2c831ab6d65802de4c76a960f8618c7ec7ee4cd62e619621ec8a453b095d`.
Future pilot data/package manifests must pin this version and hash. Historical
ASv6.48 inputs and results remain immutable evidence. The pilot notes, splits
and all ASv6.100 teacher labels are now frozen; context/output/memory settings
and the launch estimate remain pending.

**Pilot data approved October 4:** freeze 1,000 training, 100 validation and 200
final test notes. Extend the original 1,000-note fresh-corpus SHA-256 draw using
its exact domain and frozen eligible ID ordering. Export complete original
events read-only, verifying canonical IDs and tags. Exclude replies, address-tag
replies, quote posts, inline note/nevent/naddr references, mixed-language prose
and complete posts above 512 SSE tokens. Reuse the original reviewed sample
where text/author match; review newly selected English prose and writing forms.
Keep natural corpus proportions instead of the earlier balanced form quotas.
Freeze authors in one split, remove repeated templates and near copies, and keep
known development authors/templates in training. Hash-bind all selection inputs.

Labels use full ASv6.100 and its tested GPT-6.1 Sol / medium subscription
configuration. Native `experiment.py prepare/run/collect` preserves original
responses, parsed subjects and receipts. Start at 32 concurrent requests and
reduce to 24 if provider/transport problems arise. At most one provider-transient
retry per case; no quality retries, output cap or paid fallback. Teacher medium
reasoning does not change the approved thinking-off student configuration.
General teacher comparison remains a separate decision. Generation authorization
is for these 1,300 SP notes, not masks or additional experiments.

**Selection frozen October 4:** the saved bundle is
`target/distillation-pilot-v1/pilot-data-asv6.100-20261004/sample-final/`.
It contains 1,000 train / 100 validation / 200 final test notes from 686 authors,
with zero author overlap. Original event content and authors match the bounded
read-only export. Canonical event IDs are verified; full-post SSE token lengths
are 2–505 (median 92), with no truncation. All 16 forms occur overall; validation
contains no CREATIVE-form notes, and final test contains six. Categories overlap
and form counts are descriptive, not a measured semantic accuracy score.
The exposure audit binds 716 native and historical input/plan files, including
the saved 90-ID exclusion list; known development IDs/authors/templates are
absent from both holdouts. It does not establish absence from model pretraining.
The final selection verification and exact source/split hashes are saved beside
the bundle. Earlier provisional splits and one unused teacher preparation are
preserved as evidence; no inference occurred on them. Teacher generation uses
`asv6.100-subject-pilot-teacher-v1.json` and the final bundle.

**Teacher generation complete — October 5:** `asv6.100-final-v1` saved 39 valid
WebSocket answers and 99 failed handshakes at concurrency 32. Failed calls saved
zero frames/bytes; proxy logs reported HTTP 403. The native classifier treats
them as unknown causes, ineligible for automatic retry. All 138 attempt receipts
are preserved. `asv6.100-sse-v1` completed the 1,162 previously unattempted notes
over SSE transport at concurrency 24, with 1,162 valid answers and no failed
attempts or retries.

The user explicitly approved completing the missing 99 over SSE at 24 concurrency
on October 5. This authorizes that exception to the unknown-cause retry restriction.
`asv6.100-sse-completion-v1` completed those 99 notes with 99 valid answers, normal
stop reasons and no failures or retries. Its exact rendered prompts, inputs,
schema, teacher model and reasoning setting match the initial preparation.
`asv6.100-websocket-saved-v1` reused the earlier 39 answers with no new inference.

Native collection published `teacher-labels-final-v1/subjects.json` and
`provenance.json` beside `sample-final/`: **all 1,300 labels (1,000 train /
100 validation / 200 final test)**. `teacher-labels-final-verification.json`
verifies original text/author/split preservation, zero duplicate or missing IDs,
zero author overlap, structural numbering and all twelve protected collection
sources. All successful responses report normal stop reasons. The earlier
1,201 collected label records are preserved exactly; partial collections and
original failure receipts remain saved. The persistent attempt budget records
1,399 claimed calls and saved attempt receipts, including the initial 99 failures;
cached reuse adds no claims.

The full collection has not undergone semantic review. No rental, paid API fallback
or additional cash commitment was used. Full-pilot context/memory checks and
packaging remain open. `subjects.json` SHA-256:
`aca9b45674730a33d7c869c69403e7f4b1143c19ff418a41bb230b04e647ec9e`.


### Full pilot input audit — October 5

Offline checks use all **1,000 train / 100 validation / 200 final test** notes and
actual ASv6.100 teacher answers. The prep's pinned Transformers **5.17.0** and
Tokenizers **0.23.2** run the production `generation_prompt`, `encode_example`
and `preflight` paths with thinking off. Every saved native prepared prompt
matches production's full SP plus complete post. Native reports revalidate all
1,300 successful raw responses. Canonical targets use production's
`json.dumps({"subjects": [...]}, ensure_ascii=False)` formatting, preserving
number, context and subject. Counts include native assistant turn endings;
no input or answer is truncated, and the three frozen splits are preserved.
Final-test content was checked only for capacity, with no student predictions
or semantic quality scoring.

| Token measure, actual 1,300 notes | Qwen3.8-27B | Both Gemma students |
| --- | ---: | ---: |
| Prompt range | 9,206–9,684 | 9,037–9,515 |
| Canonical prompt + answer range | 9,238–18,114 | 9,069–18,396 |
| Largest canonical answer, including turn ending | 8,452 | 8,881 |
| Canonical answers above 4,096, all splits | 66/1,300 | 70/1,300 |
| Canonical answers above 4,096, training | 53/1,000 | 57/1,000 |
| Canonical answers above 4,096, validation / final test | 5/100 / 8/200 | 5/100 / 8/200 |
| Training sequences above 16,384 | 5/1,000 | 3/1,000 |
| Largest raw teacher answer, including turn ending | 7,672 | 8,226 |

All 1,300 prompts exceed the frozen 8,192-token context before answers.
Native preflights reject 8,192; 16,384 and 32,768 also reject when retaining the
4,096-token output allowance. Diagnostic fixed output allowances of 8,452 Qwen /
8,881 Gemma, with contexts of 18,136 / 18,396 respectively, pass native token
checks on the 1,000 training and 100 validation examples and the 200 test inputs.
These data-derived minima cover the saved canonical answers, not arbitrary future
student responses. All three model configs advertise 262,144 positions, but
that architectural limit does not establish GPU capacity. No runtime setting
was changed or approved by these diagnostics.

Seven **training** hierarchies contain more than the worker's `max_subjects=128`;
the maximum is **145** (median 28, 95th percentile 75 across all 1,300). Neither
holdout exceeds 128. This is a conflict with the generation output guard, not
an invalid teacher receipt or a semantic quality finding. Keep complete labels.

Replaying the production planner arithmetic against the saved prep measurements
reproduces **all 4 Qwen, 7 dense Gemma and 3 MoE Gemma batch estimates exactly**.
Using the current policy on actual pilot prompt widths:

| Student | One-note estimate, current 4,096 output allowance | Inputs over 88-GiB budget | Estimate using observed canonical output maximum |
| --- | ---: | ---: | ---: |
| Qwen3.8-27B | 88.30–91.74 GiB | 1,300/1,300 | 88.58–92.02 GiB |
| Gemma 4 31B | 110.66–115.48 GiB | 1,300/1,300 | 110.66–115.48 GiB |
| Gemma 4 26B-A4B | 75.26–77.66 GiB | 0/1,300 | 75.26–77.66 GiB |

These are conservative planner estimates, **not measured current-input GPU
allocations or proof of OOM**. No weights were loaded and no training/inference
or rental occurred. MoE's estimated evaluation fit does not prove its training
fit. The prior GPU checks used shorter ASv6.48 examples and cannot validate these
new shapes. Resolve context, output/node guards and the actual attention/cache
memory allowance locally before a new hardware check or pilot launch. The
selected one-96GB-GPU design and all frozen configurations remain unchanged;
the historical ASv6.48 cost reference still does not price this dataset.

Evidence: `target/distillation-pilot-v1/pilot-data-asv6.100-20261004/input-audit-20261005/`
contains the exact offline invocation, `tokenizer-audit.json`,
`per-note-token-counts.json` and `memory-policy-audit.json`. All **38** bound
source files were rehashed after analysis, including prompt, notes, labels,
split references, native ledgers, worker/data code, tokenizer metadata and prep
batch plans. Token audit SHA-256:
`c612d1d8bf7d7fada9f8d47ea2d437b7dc65795997232253db3db45b7f8f749a`;
per-note counts:
`c8430fdef36411909bf137e543a2ee06a12ff8ef9b784ded506c6acdce5d77c4`;
memory audit:
`09e033d85ea5218e547bf4740febbce77fd41d3b50cb0ac019a02cba5101f79b`.
Teacher answers have structural/receipt checks; semantic review remains open.

### Local runtime memory investigation — October 5

The authorized local investigation separates generation planning from training
loss allocations. It uses the pinned **PyTorch 2.12.1+cu130 / Transformers 5.17.0**
runtime recorded by GPU prep, all actual pilot token counts, saved prep allocations
and versioned primary source. No worker, dependency or frozen input changed.

**Attention:** the worker supplies no attention override. Transformers defaults
these supported models to SDPA; CUDA chooses a kernel for each call. The old
receipts do not record that choice. Qwen's full heads are 256-dimensional; Gemma
uses 256-dimensional sliding heads and **512-dimensional global heads**.
PyTorch 2.12.1's CUDA Flash path caps dimensions at 256, and its cuDNN gate also
rejects 512. Its memory-efficient path and generated BF16 forward/backward kernels
include 512 and SM120 in their source eligibility ranges. Transformers repeats
Gemma's K/V heads before SDPA at dimension 512, satisfying that path's equal-head
requirement. Source eligibility still does not prove the image has the kernels
or that the real GPU/masks/layouts launch successfully.
[PyTorch 2.12.1 CUDA selection](https://github.com/pytorch/pytorch/blob/v2.12.1/aten/src/ATen/native/transformers/cuda/sdp_utils.cpp),
[forward kernels](https://github.com/pytorch/pytorch/blob/v2.12.1/aten/src/ATen/native/transformers/cuda/mem_eff_attention/kernels/cutlassF.h),
[backward kernels](https://github.com/pytorch/pytorch/blob/v2.12.1/aten/src/ATen/native/transformers/cuda/mem_eff_attention/kernels/cutlassB.h),
[Transformers SDPA adapter](https://github.com/huggingface/transformers/blob/v5.17.0/src/transformers/integrations/sdpa_attention.py).

The existing four headwise attention-matrix allowance contributes **33.54 GiB
Qwen / 43.17 dense Gemma / 21.59 MoE** at the longest prompt, plus separate mask
allowance. Replaying the same arithmetic with zero headwise score matrices,
while retaining masks, resident weights, caches, 4-GiB workspace and per-token
prefill buffers, gives the following **conditional generation estimates** with
10,240 output tokens:

| Student | One-note conditional estimate | Native BF16 training score tensor | Native FP32 training score tensor |
| --- | ---: | ---: | ---: |
| Qwen3.8-27B | 58.39–58.60 GiB | 8.38 GiB | 16.76 GiB |
| Gemma 4 31B | 71.73–72.32 GiB | 8.98 GiB | 17.96 GiB |
| Gemma 4 26B-A4B | 55.79–56.07 GiB | 8.98 GiB | 17.96 GiB |

This calculation is not a replacement policy or GPU measurement. Retaining the
old numeric scratch allowances does not validate them for a different kernel.
A future implementation must select SDPA's compatible Flash/memory-efficient
backends explicitly and exclude silent math fallback before budgeting without
those matrices. GPU prep must test both prefill and the full output cache.

**Training loss:** current `model(**batch, use_cache=False).loss` computes a
sequence-by-vocabulary score tensor for all positions, including ignored prompt
positions. Native loss casts it to FP32 and computes log-softmax/NLL. Gemma also
retains a softcap result for backward. Ordinary unfused tensor-lifetime projections
for the longest training examples give about **41.89 GiB Qwen / 53.89 GiB Gemma**
for the overlapping head/loss buffers, before decoder activations, LoRA state and
allocator overhead. These are source-based projections, not observed allocations.
The old GPU prep reached 74.19 / 85.34 / 71.58 GiB allocated during training at only
6,531 / 6,440 / 6,440 tokens; it does not validate the new 18K sequences.
[Native loss](https://github.com/huggingface/transformers/blob/v5.17.0/src/transformers/loss/loss_utils.py),
[PyTorch cross-entropy](https://github.com/pytorch/pytorch/blob/v2.12.1/aten/src/ATen/native/LossNLL.cpp).

**Implementation candidate:** use released **Liger 0.8.4 fused linear
cross-entropy only**, disabling its other replacements. Its Qwen and Gemma
integrations pass full decoder hidden states into a chunked classifier/loss,
with ignored-label masking, mean over supervised targets, frozen classifier
weights and Gemma's softcap 30 preserved. The current worker's token-weighted
accumulation can then retain the same objective. At default chunk settings,
transient BF16 score chunks are **0.237 / 0.250 / 0.125 GiB** for the respective
longest examples; these are just score-buffer sizes, not total training memory.
The Gemma helper emits an eager-attention recommendation, so combining it with
the proposed SDPA backend needs explicit numerical verification. The native
Gemma attention path has no attention-logit softcap; its final classifier softcap
must remain intact. MoE's decoder/expert adapters also need their own check.
[Released integrations](https://github.com/linkedin/Liger-Kernel/blob/v0.8.4/src/liger_kernel/transformers/monkey_patch.py),
[Gemma forward](https://github.com/linkedin/Liger-Kernel/blob/v0.8.4/src/liger_kernel/transformers/model/gemma4.py),
[fused-loss implementation](https://github.com/linkedin/Liger-Kernel/blob/v0.8.4/src/liger_kernel/ops/fused_linear_cross_entropy.py).

Before adoption, verify pinned imports and native forward compatibility locally;
compare loss/adapter gradients with the ordinary path, including ignored prompt
positions, Gemma softcap and token-weighted updates. Rehearse checkpoint reload,
merge and restoration. A brief GPU check must then verify selected kernels,
finite gradients and peak memory on the longest real training examples and
planned generation batches through the full cache allowance. CUDA equivalence
and fit cannot be established with this source inspection. No candidate kernel
or dependency was installed or executed in this investigation.

The discussed 20,480-context / 10,240-output bounds cover every saved example
arithmetically; student output sufficiency still needs checking. Removal of the
128-node guard for this subjects-only pilot remains an implementation proposal.
Preserve complete prompts, notes, teacher labels, the continuing training recipe
and the selected one-96GB-GPU design. Repricing follows measured new throughput.

Evidence: `target/distillation-pilot-v1/asv6.100-runtime-memory-audit-20261005/`
contains `runtime-memory-audit.json`, the exact offline invocation and **18**
versioned primary-source snapshots. Five installed Transformers files match the
release tag byte-for-byte. All **77** bound files were rehashed, including all
38 frozen files from the prior audit, and 3,900 saved per-note planner estimates
were reproduced exactly. Runtime audit SHA-256:
`b5bd2fb35c8788e66b143ac00a67c102fd9eeb47aeb8b50f962479d68241ce41`.

### Runtime implementation and local verification — October 5

The user approved implementing the attention/loss candidate and testing it
locally before preparing another GPU check. New reusable candidate settings live
in `sse_multivector/distillation/subjects/`: **20,480 context / 10,240 output**,
subjects only, no `max_subjects` cap, existing five continuing checkpoints and
unchanged training recipe. The shared workflow has now populated `prepared`
from the preserved 1,000/100/200 split without repartitioning; final test data stays
reserved. Historical packages/configurations remain intact.

`efficient_attention` selects native SDPA and restricts CUDA calls to Flash and
memory-efficient backends during generation, cache checks, training forward and
checkpointed backward. Math and cuDNN fallback are excluded. Zero headwise
attention matrices require that CUDA configuration and SDPA without attention
outputs. Existing 88-GiB budget, mask, workspace and prefill allowances remain
**candidate numerical settings requiring hardware validation**.

`fused_linear_cross_entropy` patches only the training model instance using
**Liger 0.8.4**. Its other kernel replacements are disabled; fresh evaluation
loads native model code before adapter merge. GPU dependencies remain isolated
from CPU execution, hash locked, and checked against the immutable image's
Torch/Triton and core dependencies. Prompt/target masking, token-weighted updates,
classifier freezing, Gemma softcap 30, expert LoRA and full-state continuation
remain unchanged. Legacy subject/mask runs retain their subject-count guard.

Local checks reproduced the original node-limit and missing attention-policy
guard failures before implementation. Pinned **2.12.1+cu130 / 5.17.0 / 0.21.0**
container suites passed: **6 candidate, 33 workflow, 24 deployment tests**; one
optional candidate-tokenizer SSH preflight was skipped because no package was
supplied. The loss check exercises real Qwen/Gemma/MoE Liger forwards and PEFT,
including 512-dimensional Gemma global heads, comparing loss and adapter
gradients against native eager attention. **Only the CUDA loss calculation is
replaced with a CPU reference in that test.** It checks prompt masking, softcap,
unequal answer-token weighting, adapter save/restore and native merged evaluation;
it does not execute or validate Triton numerics. Existing tests cover continuing
optimizer/random state, all checkpoints, raw/parsed response seals and shared
SSH copying/retrieval/recovery. The first VM attempt exposed GPU import state
leaking into a later CPU test; that check now runs in a separate process.

The older host **Torch 2.8.0+cpu** regression run had one tight numerical-tolerance
failure in the existing physical-batch weighting check (maximum mismatch
2.08e-6); the same unchanged check passed in the pinned container. No tolerance
was relaxed. All **3,900** saved shapes fit the candidate context/output bounds,
and **76** bound input/source files were rehashed unchanged, including all frozen
notes, teacher labels, splits and old configurations.

Evidence: `target/distillation-pilot-v1/asv6.100-runtime-implementation-20261005/`
and VM attempt `target/distillation-vm-clean-deployment/attempt-1791223686198026208/`.
No paid action or image publication occurred. Actual CUDA kernel/loss/gradient
agreement, full long-example training memory, full generation cache allowance
and throughput still require the brief hardware check; these local results do
not establish 96GB fit or a revised price/duration.

### Experiment integrity safeguards — October 5

The user authorized fixing paths that can train without producing a valid
comparison. Semantic correctness/coverage grading remains local and does not
block GPU execution; its rubric and reviewer remain open.

- The shared data preparation accepts frozen three-way splits. Loading verifies
  target/teacher agreement, full instruction/source-note bindings, exact response
  IDs, author/content separation, hashes, and canonical/fenced parser behavior.
  The 200 final test notes cannot enter prep or pilot training/validation.
- CUDA fused-loss pilot packages require paired preparation configs with the
  same dataset, model revision and training/generation recipe. Prep output has its
  own directory; passing prep continues into fresh pilot adapters on that rental.
- Preflight covers all examples and requires prep to include the longest complete
  training sequence. Actual native cache checks cover every full-validation batch
  shape by testing the largest combinations of batch size and padded width. Brief
  generation remains a memory/timing check, not a baseline quality result.
- Before prep's first update, the loaded training model compares actual fused and
  native loss/backward on short inputs, with ignored prompt labels and unequal
  token weights. RNG, instance forward and gradients are restored; no optimizer
  update is added. BF16 mean-loss tolerances follow
  [Liger 0.8.4 correctness tests](https://github.com/linkedin/Liger-Kernel/blob/v0.8.4/test/transformers/test_fused_linear_cross_entropy.py).
- All candidates finish and verify their full baselines before any pilot training.
  Every checkpoint evaluation is verified before continuation. Bad model answers
  remain counted; missing work, invalid generation metadata, receipt mismatches,
  and raw/parsed inconsistencies block progress.
- `distillation_deploy verify-results` rechecks every required stage and checkpoint
  locally, including training coverage and unchanged batching. With
  `--operation-root`, it verifies the retrieved tree and records the shared
  completion review required before explicit deletion. It neither rents nor deletes.

Pinned VM validation passed **78 tests**, with one optional tokenizer-package
SSH preflight skipped: 6 candidate, 40 workflow and 33 deployment tests (32 passed).
The suites include actual prep-to-pilot execution over SSH, fresh pilot adapters,
continuation, live copying, offline completeness review and rejection of corrupt
retrieved results. CPU tests replace the CUDA loss kernel with a reference; they
also demonstrate that a wrong loss blocks the production numerical check.
Native-tokenizer preflight also passed on the actual prepared data for all three
candidates: 1,000 full training examples and 100 validation prompts each, without
loading weights. Maxima reproduce 18,114 Qwen / 18,396 Gemma training tokens and
8,452 / 8,881 answer tokens. Source labels and the exact 1,000/100/200 split order
were reverified unchanged. The final test remains reserved.
The VM is stopped. Evidence is `target/distillation-pilot-v1/pilot-integrity-20261005/`
and VM attempt `target/distillation-vm-clean-deployment/attempt-1791226564765712096/`.
No rental or image publication occurred.

These checks establish compute/data completeness, not semantic quality or a
clear winner. Actual CUDA agreement, long-example fit and throughput remain
hardware checks. Final-test collection on the main rental is now implemented
as described below; launch spending remains open. No real student inference
on the reserved test notes has occurred.

### Reserved final-test collection — October 5

For subjects-only pilots, the prepared test split requires one untuned and one
final-adapter test collection per candidate. Collect the untuned test while its
base is loaded, then the final test while the last disposable merged evaluation
copy is loaded. Earlier checkpoints generate validation only; no additional
training pass or scheduled model load is introduced. Prep removes the test
split from its execution view. Pilot preflight checks reserved prompt lengths
without generation.

Save test work separately under `test/baseline/` and `test/checkpoint-1000/`.
Retain native batch plans/receipts, raw and parsed answers, and per-note/stage
file seals. `test-collection.json` binds the stage to the frozen run manifest
and final checkpoint seal. Hash seals protect transfer integrity. Keep content
review postponed until validation and model selection are recorded. Automatic reports
and offline integrity summaries expose only collection counts/locations and
`review_status: sealed`, with no answers, subject counts or semantic scores.
The local semantic grader/unsealing procedure remains separate, unimplemented
work; settle its rubric and selection before opening the test.

All baseline validation/test work is checked before any pilot training. Offline
verification requires both test stages, their exact reserved IDs, raw/parsed
agreement, batch receipts, source binding and matched baseline/final batching.
Completion review cannot accept missing test work. Completed collections are
reused; an interrupted final test can finish from its saved adapter without
retraining, even when final validation is already sealed.

Minimal production-path checks first failed for missing test collection, ignored
test token allowances, and training advancing without baseline test work. The
corrected pinned VM rehearsal passed **81 tests**, with one optional
candidate-tokenizer SSH preflight skipped (6 candidate, 42 workflow, 34
deployment tests including the skip). The combined real-SSH prep/pilot test
retrieved baseline/final test answers, verified both candidates, and rejected a
missing test response before completion review. A first rehearsal correctly
rejected that missing file but failed because the test expected a checksum-error
message; only that assertion changed before the successful rerun.

All three native-tokenizer preflights also passed against the actual frozen
**1,000 train / 100 validation / 200 test** data without loading weights. Maximum
test prompt lengths are **9,584 Qwen / 9,404 Gemma** tokens, within the
20,480 context and 10,240 output bounds. Twelve source/prepared files were
rehashed unchanged. These checks establish collection/recovery/completeness and
token limits; actual CUDA execution, fit and speed remain hardware checks.
Evidence: `target/distillation-pilot-v1/final-test-design-20261005/` and VM
attempt `target/distillation-vm-clean-deployment/attempt-1791231456496036400/`.
No rental, publication or real reserved-test inference occurred.

### Final integrity audit and recovery — October 5

The final audit confirmed input/split bindings, rejected 13 corrupted or
incomplete result copies, and checked that test batch shapes are covered by the
planned validation-cache shapes. Those are offline checks, not measured GPU fit.
Its actionable gaps were terminal-worker recovery, stale retrieval reuse,
progressive provenance coverage and command-workload observation. The user
authorized local fixes; the frozen data and training recipe stay unchanged.

Subject pilot specifications now opt into explicit `resume --reason ...` on
the existing instance. First reconcile a terminal/orphaned worker and checksum
verify its available results. Archive its local result and receipts under
`retrieval-attempts/<attempt>/`; preserve remote attempt evidence and retrieval
manifests. Reuse only published immutable files in the next retrieval tree.
The recorded invocation survives interruptions during archiving or delivery,
so repeating the same continuation reconciles its original attempt. A running
worker cannot be replaced. Frozen transport and installed inputs are checked;
normal starts still cannot execute a second committed worker.

Saved malformed answers and answer-count defects are never regenerated. A call
interrupted before saving its answer may run again only under a new recorded
worker continuation, retaining its original started-call evidence. Training
restores the latest complete checkpoint, including optimizer/RNG/cursor state.
Work after that checkpoint can be recomputed; discarded updates do not accumulate
in restored weights. Per-update JSONL records carry the attempt ID, so they are
diagnostic history rather than the authority for completed training coverage.

Every continuation needs a new sealed retrieval and offline completeness review.
Old receipts/reviews cannot authorize stopping or deleting newer work. Frozen
status commands report saved validation counts/failures, checkpoint cursors,
latest updates and progress age. Local observations also save GPU utilization,
GPU memory and disk space. Reserved-test status reports counts only, with no
answers, subject counts or failure totals. Copier failures permit three bounded
restarts without stopping training; exhausted failures require operator attention.

Final verification passed **148 controller regressions and 85 pinned-VM tests**;
one optional candidate-tokenizer SSH test was skipped because no package was
supplied. The actual frozen data passed production loading again, with unchanged
ASv6.100/data hashes and the exact 1,000/100/200 counts. Real SSH interruption
and continuation preserved **96 published files**, produced a new retrieval,
and completed both tiny candidates' validation/final-test collections. A real
SSH copy resumed after 100 received bytes, with no incomplete checkpoint
publication. Initial rehearsals exposed SSH reason quoting and overlapping-seal
discovery defects, corrected before this final pass; the new transfer test also
needed a missing import. All **22 packaged runtime files** match the final VM
snapshot; the container export is verified and the VM is stopped. Evidence is
VM attempt `target/distillation-vm-clean-deployment/attempt-1791236491666470396/`.
No rental, publication or real reserved-test inference occurred.

Evidence: `target/distillation-pilot-v1/final-integrity-audit-20261005/` and
`target/distillation-pilot-v1/final-integrity-fixes-20261005/`.
Real ASv6.100 CUDA numerical agreement, long-example fit, cache allowances and
timing remain the next hardware checks. The paired input package and revised
transfer draft are frozen below; private image publication and a $285 combined
rental budget are approved. These controls cannot guarantee recovery of unexfiltrated work after
sudden host/storage loss.

### Frozen two-GPU package and conditional cost — October 5

The approved local update assigns Gemma dense to GPU 0 and Qwen followed by
Gemma MoE to GPU 1. Each subprocess holds one complete model and receives its
own `CUDA_VISIBLE_DEVICES` binding. The shared controller runs one process per
card, preserves inherited device masks, and records active candidates and their
GPU assignments. All three prep verifications finish before baselines; all three
complete validation/test baselines finish before any main training.
A failure blocks queued work while other active work finishes and is preserved.
An explicit stop reaches both child process groups. Hardware observations identify
each GPU by index/UUID with separate utilization and memory metrics; single-GPU
GTE observation behavior is retained.

The shared `distillation_deploy prepare` workflow froze the combined package at
`target/distillation-pilot-v1/two-gpu-implementation-20261005/package/`, with manifest
SHA-256 `26d9727104c40cde72707a59ce08d3c04f7847724768a45401f4c91cd93ca764`.
The reusable assignment file is `sse_multivector/distillation/subject-gpu-assignments.json`.
All six pilot/prep configurations and datasets are byte-identical to the passed
October 5 native preflights. Token encoding/training code is unchanged. Each main
plan uses every note once, with 125 updates and the five approved milestones.
Only deployment, Vast workload validation and shared hardware observation changed.
No timeout is configured; the old single-card package remains frozen evidence.

Matched prep selects three existing training notes: two median-length examples
and the longest complete example for every candidate. Its first partial update
initializes Adam state on one example. Restore that checkpoint, then accumulate
gradients on another example before training on the longest example in the
second partial update. These adapters are discarded before the fresh main runs,
which retain eight examples per update. Brief generation uses one validation
note per candidate with a 64-token limit. Production preparation independently
checks full native caches covering validation/test batch shapes and actual
CUDA fused-loss/adapter-gradient agreement. Reserved test inputs contribute only
native lengths and synthetic cache shapes; prep never trains on, generates, or
semantically reviews their answers.
Actual concurrent hardware fit and speed remain unmeasured.

The rebuilt VM passed **91 tests**, with **one optional native-tokenizer check
skipped** because no tokenizer package was supplied. The unchanged six native
preflights are bound by exact config/data hashes. **149 shared-controller** and
**30 host package/data** tests also passed. The CPU VM does not emulate GPU
kernels. Its real concurrent workers verified checkpoint restoration, continuation,
progressive copies from both candidates, all required raw/parsed/test responses,
and complete local retrieval/review; missing or changed data blocks review.
The first rehearsal exposed a timing assumption in its test: the tiny main run
finished before a main checkpoint copy, although both baselines and prep
checkpoints had already copied. The corrected test verifies those early seals
from both workers and all main checkpoints at final retrieval. No transfer
runtime repair was needed. The complete rehearsal then passed.

All 15 frozen runtime source/config hashes match the stopped VM snapshot at
`target/distillation-vm-clean-deployment/attempt-1791242606321467393/`.
The exported image archive SHA-256 is
`b9ffbcecb8c47cc35364a1970f23899dcb7fd258765926e4b44ab511ff3c0b69`;
this is an archive hash, not a registry digest. The tested image is published as
`docker.io/kernelkind/oracle-mvp@sha256:58dd4c3c256b13724f5fb79b59373e4b43fca2c8cba0cb1439c25c36d061ea64`.
Loaded filesystem/runtime configuration and all 15 source hashes match the VM;
read-only pulling succeeds and anonymous manifest access returns HTTP 401.

The refreshed read-only quote, a compatible offer, supplies two **96GB/600 W RTX PRO 6000
Server** cards for **$2.9889/hour including 300 GB storage**. It has about
387 GB host RAM, 32 effective CPU cores, driver 580.173.02 and reliability 0.9966.
The model/checkpoint projection remains **169.72 GB + 27.25 GB**; 300 GB leaves
about 103 GB before image, responses and logs. Allow **200 GB inbound / 60 GB
outbound**, about **$0.77** at the saved transfer rates. No offer is reserved.
The server cards' throughput has not been measured; the calculation conditionally
uses the old 600 W workstation measurements. Shared CPU/disk contention is also
unmeasured. Preserve the same batches and recipe on each GPU.

| Arithmetic scenario | One-GPU hours | Two-GPU hours, with headroom | Conditional cost at two-card quote |
| --- | ---: | ---: | ---: |
| Linear training scaling, old decode latency | 78.46 | 40.43 | $122 |
| Linear training scaling, cache-length-scaled decode | 127.09 | 65.71 | $197 |
| Quadratic training sensitivity, cache-length-scaled decode | 151.43 | 79.60 | $239 |

These are scheduling scenarios, not measured ASv6.100 throughput, confidence
intervals or runtime bounds. Compute each model's baseline and trained stages;
for each stage use the longer of dense Gemma versus Qwen plus Gemma MoE, keeping
the global baseline gate. Add shared lifecycle time once and 25% headroom once,
then transfer fees once. Generation uses each batch's longest teacher answer
as a proxy; actual student lengths and new-kernel speed are unknown. Count all
**1,800 validation + 1,200 test** responses once. No training restarts, duplicated
responses, masks, thinking evaluation or separate winner rental are added.
Prep alone is projected at **0.5–1.5 hours / $2.30–5.30**, already included in
combined lifecycle. Current two-card scenarios give about **1.9×** speedup.

Evidence: `target/distillation-pilot-v1/two-gpu-review-20261005/` contains saved
quotes and `schedule-comparison.json`; `two-gpu-implementation-20261005/` contains
the frozen package, `freeze-verification.json`, test logs and a copied cost report.
The user approved **$285** for private publication and the combined rental.
The frozen plan allows **90 hours at up to $3.10/hour**, plus **$2.60** transfer
allowance: $281.60 in planning quantities, within the approval. The 90 hours and
cost thresholds are review parameters, not automatic stop/deletion limits.
The recorded rental rate was $2.9889/hour. Qwen prep completed both updates and its
maximum-output native-cache check. Dense Gemma saved checkpoint 1 and a brief
response, then exceeded the frozen 88 GiB reserved-memory guard without CUDA
OOM. Gemma MoE failed fused/native adapter-gradient agreement before its first
update. Neither failed check persisted its numerical diagnostic, so repairs
must preserve these measurements before rejecting work. The global prep gate
blocked every main baseline and training run. All 80 work and six startup files
(4,346,589,909 bytes), available checkpoints and failure logs were retrieved
and independently rehashed.
The preliminary resource charge was **$1.974**. Repairs were completed
locally and the original image/
input/operation are preserved.

**Local recovery — October 6:** before rejecting a cache peak, write its full
measurement and admitted batch plan. `training-loss-check.json` now preserves
failed losses and parameter-specific gradient differences, including maximum
absolute error, failing-element counts and relative L2 error. The short Gemma
native reference promotes projected logits to FP32 before softcapping, matching
[Liger 0.8.4 TorchLMHeadCE](https://github.com/linkedin/Liger-Kernel/blob/v0.8.4/test/transformers/test_fused_linear_cross_entropy.py).
The native head, weights, gradients, RNG and forward are restored after the
check. CUDA `atol=.005` / `rtol=.05` are unchanged; the training loss/kernel and
evaluation computation are unchanged. BF16 CPU reproductions verify the
reference correction and still reject deliberately corrupted loss/gradients.
This does not prove the full MoE CUDA check now passes.

Dense inference now reserves **12 GiB workspace**, keeping the **88 GiB** budget
and full output allowance. With the measured resident/cache shapes and a
9,442-token prompt, this admits one note per batch. Qwen/MoE retain 4 GiB.
The same candidate policy governs baseline and every trained collection.
Preparation covers both validation and reserved-test input lengths using native
caches with synthetic continuation tokens; only validation notes receive brief
prep responses. Freeze new paired configs/image rather than editing the failed
operation. All teacher data, update membership, optimization and saved original
evidence are retained. **94 VM tests pass** (one native tokenizer test skipped
and covered separately), all **six native tokenizer preflights pass**, and the
host settings test confirms dense singleton admission through the real planner.
The VM integration exercises continuing updates, saved adapter reload, parallel
prep/baseline gates, live copying and verified retrieval. Actual GPU checks remain
required before main training.

`two-gpu-recovery-20261006/revised-cost-estimate.json` prices dense singleton
generation using the nearest old measured batch-two decode latency, without
assuming a singleton speedup. Qwen/MoE, update counts and response counts are
unchanged. Conditional replacement scenarios become **53.11 / 82.61 / 93.07 hours**
and **$159.51 / $247.69 / $278.94** at the saved $2.9889/hour quote. Including the
failed prep’s recorded provisional $1.98 gives **$161.49 / $249.67 / $280.92**.
They retain teacher-answer-length proxies, old workstation kernel timings, the
global baseline gate and 25% headroom once; they do not measure current throughput
or bound runtime. The replacement experiment allowance is at most **$281**. Review planning
uses 89 hours at the $3.10/hour ceiling plus transfer quantities; this creates
no automatic stop or deletion.

The corrected VM export is published and verified private at
`sha256:c376ec124faabd71c018e52044faf9ee6bbc4b02b6d7a48bf90f1cbfa8f806e5`.
The exported archive is `a198d81a029af0449137ba81d7744607a5e7fbc79960ce5144bb63cfde940efd`;
all filesystem layers, runtime defaults and 15 source hashes match the passed VM.
Docker export normalizes empty metadata fields; execution settings are identical.
Read-only pulling succeeds and anonymous manifest access returns HTTP 401.
New frozen package manifest:
`8e7018275fa7cbdc3f05231d6c676ae5049daf9e8f30e5bb378e07038f19f50a`.
The recorded rental rate was $2.9889/hour including 300 GB storage. Container
DNS failed before SSH, inputs or worker startup. One provider reboot did not
repair it. All necessary available startup logs and direct/proxy diagnostics
were saved and independently hashed. No experiment data was produced. The preliminary resource charge was **$0.76**; the two failed attempts had a rounded preliminary cost total of **$2.74**. The next search excludes machine 146170. A different
compatible offer quotes $2.9389/hour including 300 GB
storage for two 96GB/600 W server cards. Native frozen preparation passed.
The recorded rental rate was $2.9389/hour including 300 GB storage. Startup/
GPU prep were observed. The verified image, package, all 15 runtime
source hashes and recipe are unchanged. Continuous observation, live copying and complete-data
deletion rules apply. New launch evidence is
`target/distillation-pilot-v1/launch-20261006-two-gpu-r2/`.
At 02:15:54 UTC, a local $1 setup gate refused worker admission after successful
SSH, transfer and remote preparation: estimated rental $0.314536 plus the whole
planned $0.755209 transfer allowance exceeded $1. A production-path reproduction
confirmed the refusal. A recorded local Context with $5 startup allowance started attempt 001. A second call returned the same attempt. No remote code, original
Context/contract/transport, data, prompts or model recipe was changed; hashes
were verified again. The original frozen supervisor/observer were restarted.
Failure evidence, old supervisor receipts, effective local configuration and
repair verification are in `operation/launch/startup-recovery/001/`. Future
launch settings use $5 startup allowance. Main baselines/training had not
started; no comparison was changed.

**Verified closure, October 6:** Qwen prep completed. Dense completed both
updates, saved checkpoints, verified reload/merge, brief generation and cache
checks. Its **94,948,556,800-byte / 88.43-GiB** training reservation exceeded the
**88-GiB inference budget**, despite fitting the GPU without CUDA OOM. Applying
that inference allowance to completed training was incorrect. The local fix
removes the training rejection only; measured training peaks remain recorded,
and inference batching/cache limits stay enforced. The production-path test
first reproduced the rejection and then passed; the cache-rejection test also
passed. Local exact-image tests with the source mounted read-only passed
**73 tests**, with **12 deployment-VM checks skipped**. This source fix is not
yet published or newly VM/CUDA validated.
MoE failed native/fused gradient agreement before its first optimizer update.
The actual CUDA measurement is saved: loss 2.59095550 versus 2.59095573; six of
360,448 finite adapter-gradient elements failed the existing atol=0.005 /
rtol=0.05 check, maximum absolute error 0.015625, relative L2 error 0.035727.
The cause is unresolved; no tolerance or training recipe was changed. No main
baseline, validation, final-test collection or pilot training started.
All **95 work and 6 startup files / 5,849,177,916 bytes** were retrieved and
independently rehashed before deletion. Four available checkpoints and their
response/cache seals, complete Qwen prep and both failures were inspected.
The preliminary resource charge was **$2.543**. The rounded preliminary failed-attempt cost total was **$5.29**. No replacement rental
or remote code edit was made.
Evidence: `launch-20261006-two-gpu-r2/closure-evidence.json`, the operation’s
`observations/full-pre-deletion-integrity-review.json`,
`observations/training-memory-guard-local-repair.json`, and
`observations/preliminary-billing/summary.json`. MoE CUDA confirmation remains
required before main pilot work; the subsequent local repair and rebuilt runtime
are recorded below.

**Subsequent local MoE reference repair — October 6:** Liger’s mean loss
computes and rounds the hidden-state gradient during forward, then multiplies
it by the note’s scalar weight during backward. The native reference instead
multiplied CE before LM-head backward. This changes BF16 rounding even when
losses agree. A real tiny BF16 Gemma MoE/PEFT reproduction, emulating only the
unavailable CUDA loss, fails the old production check. Matching scalar
application after native LM-head backward makes every adapter gradient equal
in that reproduction. Keep the actual training forward, token normalization,
optimizer and numerical tolerances unchanged. Restore the temporary head and
tensor hooks, gradients, RNG and forward on success/failure. The report records
`reference_gradient_scaling: after_lm_head`. Corrupted gradients still fail.
The regression runs locally with PyTorch 2.12.1 CPU, Transformers 5.17.0, PEFT
0.21.0 and Liger 0.8.4; it is not a replay of the full original CUDA model.
The full local suite passes 89 tests, with 12 deployment-VM-only checks skipped.
Confirm the full CUDA check before main pilot work; the rebuilt/frozen runtime
is recorded below. Evidence:
`target/distillation-pilot-v1/moe-gradient-repair-20261006/`.

**Persistent-volume recovery approved:** retain model downloads plus compatible
saved work on a local volume across container replacement. The volume stays
on its physical machine and does not reserve GPUs. The launcher mounts the
frozen volume ID at the same
operation path and sets `HF_HOME` to its persistent model cache. Replacement
freezing verifies the previous local retrieval and deletion, identical volume,
image, workload and input manifest. Remote preparation rechecks all saved work,
archives old launch/transport/preparation receipts, preserves worker attempts
and resumes with the next attempt ID. For a repaired runtime, freeze
`reuse_work: false` with a `recovery_reason`: archive the entire previous work
tree, retain the model cache and start fresh under the new image/configuration.
The previous retrieval and deletion are still required. Interrupted setup
can be redelivered.
The controller passes its worker-lock descriptor through each candidate; abrupt
controller death cannot seal changing files or admit another worker. A CPU
heartbeat regression first reproduced the orphan/sealing defect and now passes.
Host regressions pass 137 checks (16 VM/optional-SDK skips); all eight pinned
SDK checks pass. The exact rebuilt VM passes 101 checks, including independent
container replacement: all 242 saved data files are unchanged, logs preserve
their prefixes, both students retain four updates, and a real HF cache lookup
succeeds offline. The two volume tests run separately after their ordinary-suite
skips; one optional native-tokenizer check remains covered by prior unchanged
input preflights. The exported image verifies the new frozen package; all six
configurations and data are byte-identical to the previous package. Evidence:
`target/distillation-pilot-v1/downstream-recovery-20261006/`, including
`package-v2/` and `freeze-verification-v2.json`; VM/export evidence:
`target/distillation-vm-clean-deployment/attempt-1791260449813548697/`.
Import into the local Docker version normalizes absent/default configuration
fields; all 16 filesystem layers and the effective runtime configuration match
the passed VM. Both image IDs and that normalization are saved in the verification
record. Full MoE CUDA replay and new private publication remain pending; no
volume or new rental exists.
**Host choice approved October 6:** use a cheaper compatible Bulgarian host with
a local volume for the next attempt, keeping the two-card configuration and
existing spending limits. The read-only candidate is the host, quoted at
$2.7611/hour for two GPUs, 30 GB container storage and a 300 GB volume, before
transfer charges. Recheck the actual offers before creation; this is not a
reservation. Do not pay the Texas premium solely for additional spare GPUs.
Actual provider attachment remains untested. Startup checks the mount before
setup or training; the VM replacement verifies the recovery logic separately.
**Main rental layout reconfirmed October 6:** keep one rental with two GPUs
after the one-card download stage. Separate rentals project about $9–14 saved
at the selected host's saved prices, or $19–26 against fresh alternative offers,
with similar completion time. These savings do not justify changing the tested
storage and shared prep/baseline checks. Estimates include storage and 25%
headroom; prior charges, transfers and extra split-specific setup are excluded.
No new host is selected or reserved by this comparison. Evidence:
`target/distillation-pilot-v1/separate-rentals-comparison-20261006/comparison.json`.
**One-GPU download stage approved October 6:** use a one-card offer on the same
machine and the actual 300 GB volume to verify attachment and cache all three
frozen model revisions. The 42 required files total 169.81 GB, including weight
shards listed in the index and tokenizer/configuration/chat-template files.
Check free space for missing downloads, a temporary shard and 32 GiB for saved work.
Verify all required weight shards,
tokenizer/configuration files and completion receipts, retrieving evidence
locally before explicit container deletion. Retain the volume and reattach it
to the two-card rental. Verify cache completeness with networking disabled for
model access, then run the full concurrent GPU preparation before baselines or
training. The one-card stage downloads only; it does not replace concurrent
hardware checks. The observed one-card quote is $1.3444/hour plus $0.0833/hour
for the 300 GB volume, before transfers. Count downloads once, include the
additional startup and retained-volume charges, and keep all paid stages within
the existing combined approval.
This stage is implemented and VM-tested, with no paid execution yet. It saves
the download log, file sizes/checksums and a volume receipt recording the
machine, mount path, free space and write/read check. Local `verify-results`
checks every required file and transfer integrity before completion review.
The VM rehearsal retrieves those receipts, destroys the download container,
reattaches its volume and completes prep and fresh pilot execution with two
workers. The Hub endpoint is unreachable and model access stays offline.
Missing/corrupt cache files block every worker before prep. Host regressions
pass 181 checks (16 VM-only skips); the VM passes 109 checks. Four skipped checks
are exercised separately; only the optional native-tokenizer check remains
skipped. The new download/pilot packages match the exported runtime; all six
configurations and data are byte-identical to the previous package. Evidence:
`target/distillation-pilot-v1/model-cache-stage-20261006/`.
The rebuilt image is published and verified private at
`docker.io/kernelkind/oracle-mvp@sha256:d85666da177a3a3459059e0f5409db689d29e0b4e6b6d9cdb64fc1668770f0b7`.
All filesystem layers/configuration match the VM; the rental credential pulls
it and anonymous manifest access returns HTTP 401. Actual Vast attachment and
full MoE CUDA confirmation remain pending.
The recorded resource rate was $0.0833/hour. The separate $5 download GPU create request was
rejected with HTTP 400. The discarded provider message leaves the rejection reason
unknown. The helper now preserves bounded credential-redacted reasons; nine
pinned CLI tests and 68 controller checks pass. Updated VM rehearsal passed
before another creation request. Model/recipe/data are unchanged. The three-hour
download allowance remains for planning/review only; no automatic stop/deletion.
The retry captured its HTTP 400 cause: invalid volume mount path, before GPU
allocation. The fix mounts
`/workspace` and keeps the experiment/cache paths beneath it. Nine CLI, 149
controller/generalization, four cache and 13 workload-spec checks pass. Updated
VM rehearsal passed all 109 checks, including parent mounting and offline
handoff; the private immutable publication matches it and native prepare passes.
The recorded resource rate was $1.4278/hour. The preparation run completed
the download stage: all 42 pinned files (169,808,998,964 bytes) are checksum
verified on the actual volume in 768.797 seconds. Parent mounting, selected
volume identity and write/read checks pass. All 12 work and six preparation
files were retrieved and verified; production completion review passed.
The preliminary resource charge was $0.455.
Slow cold image startup exceeded the readiness window; preserved original
evidence and a guarded unchanged-controller retry recovered the same instance,
without a second create or remote edits. Future command startup remains pending
and retries after each bounded readiness window. The CLI regression failed
first and now passes; 176 local tests succeed (three VM-only skips). Rebuilt
packages preserve all six configs, data and model file requirements byte for
byte, changing only the controller runtime hash. Updated VM rehearsal and
private publication pass. The first export filled the 64GB VM disk after all
checks passed; five verified duplicate archives were removed from the VM while
preserving their host copies. The standard rerun passes 109 checks, separately
covers four earlier volume/cache skips, exports the verified image and stops
cleanly. The unchanged optional candidate-tokenizer check is not rerun.
Current main runtime/package evidence is under
`target/distillation-pilot-v1/startup-retry-20261006/`. Its private digest is
`docker.io/kernelkind/oracle-mvp@sha256:b99b4e9f23211bada17f37a5c73c8e26b1fde3bc66a1403783aee2d774567d1a`;
VM layers/runtime/source and both packages match, read-only pull succeeds and
anonymous manifest access is HTTP 401. Actual concurrent CUDA prep remains
before main baseline/training.
No pilot baseline or training yet.

Bound remaining
exposure using elapsed time from the earlier reservation timestamp through
deleted-at at the approved maximum hourly rate plus the entire approved transfer
allowance, rounding upward and flooring at posted exact-instance charges. Book
only increases above prior bookings and hold only the unbooked difference.
Final invoices still need their delayed complete-snapshot confirmation; later
settlement subtracts every prior booking and releases only the remaining hold.
No frozen image/package or training recipe changes are needed. Active resource
reservations, the $1,000 lifetime cap and original $285 total remain in force.
The four closed attempts had a conservative cost bound of $8.52. The two production-path budget
and exposure checks failed before correction and pass afterward. Evidence:
`target/distillation-pilot-v1/deleted-rental-budget-20261006/`.

**Host switch and retained backup, approved October 6:** the host has
only one rentable GPU. The available compatible pair on the host costs
$2.8139/hour plus $0.0833/hour for 300GB persistent storage. All storage, transfers and failed attempts remain inside $285. Use the existing
tested single-GPU cache-download/retrieval/deletion stage, then the new volume
and unchanged two-GPU package for concurrent CUDA prep and pilot. No source,
model, prompt, data or recipe changes. No automatic deletion/cutoff. Evidence:
`target/distillation-pilot-v1/host-switch-20261006/`.
The model-cache volume on the host holds all **42 files / 169.8 GB**,
checksum verified. The download stage completed successfully; local completeness review was performed.
The preliminary resource charge was $1.22.
The two-GPU preparation passed cache attachment and offline verification. Qwen and
Gemma dense passed full CUDA prep; Gemma MoE still failed gradient agreement.
**No pilot baseline or training started.** All **97 work files / 5.85 GB** and
six preparation files were retrieved and independently rehashed.
The preliminary resource charge was **$1.445**. The one-GPU diagnostic completed both cases
without training updates. All **20 files / 3.17 MB**, including all four saved
head-state/gradient pairs, were retrieved, independently rehashed and opened.
The preliminary resource charge was **$0.21**. Head relative L2 error is **0.294–0.321%** with identical inputs;
296 of 156,119,040 adapter-gradient elements fail pointwise tolerance after
backpropagation. Disabling reduced-precision reductions improves head agreement
but does not resolve the deep comparison. A locally tested reference correction
checks head gradients separately, then compares native/fused adapter gradients
using the identical incoming head gradient. It adds a relative L2 check using
the existing rtol, so absolute tolerance cannot hide corrupted tiny gradients.
Both new production-path regressions failed before repair and pass afterward;
all five fused-loss tests pass. Full VM validation now passes: 10 candidate,
46 workflow, 48 deployment, four cache and four explicit replacement/handoff
checks; all four deployment skips are covered separately. Candidate tokenizer
preflight uses verified offline metadata. Caching reuses passed stages; the exact
VM export and refreshed package are published privately and verified, at image
digest `afa90bc64233b227da5db36f1336d7395138d9528bfb8c0d3a7dadc5f7256bad`.
All three actual CUDA loss/head/adapter-gradient checks now pass, with zero
backbone-gradient differences using the verified identical head gradient.
The preparation run passed Qwen and dense Gemma full prep. MoE stopped on its
seven-note native generation-cache probe: **88.080 GiB reserved versus 88 GiB
budget**, without OOM. **No pilot baseline or training started.** All **116 work
files / 6.82 GB**, six preparation files, five sealed checkpoints and the three
gradient-check reports were retrieved, independently rehashed and reviewed.
The preliminary resource charge was **$1.361**.
The recorded resource rate was $2.8139/hour. Only MoE inference workspace changes **4 → 12 GiB**, consistently
in prep and pilot; total inference budget stays 88 GiB and the widest predicted
batch falls **seven → five**. Exact image, code, prompts, data, models and
training recipe are unchanged. Package verification and native preparation pass.
The replacement run passed all three full CUDA preps and started baselines
on the same rental. The widest real cache probes reserve **76.28 GiB Qwen
(seven notes), 77.07 GiB dense Gemma (one), and 76.80 GiB MoE (five)**, all below
88 GiB. Loss/gradient checks, merge/generation, long-input updates and saved
continuation checks pass for every student. No pilot training starts until
all three baselines pass. Observe continuously and progressively retrieve
frozen responses/checkpoints. Archive all verified prior work and retain the
model cache. No automatic stop or deletion. Evidence:
`target/distillation-pilot-v1/main-pilot-loss-boundary-20261006/` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/`.

**Baseline integrity, October 7 00:07 UTC:** Qwen and dense Gemma's 100-note
validation baselines are retrieved and verified locally: hashes, full inputs,
raw/parsed answers and batch receipts agree. Qwen's 13 and Gemma's two invalid
answers remain counted. Both 200-note test collections are underway and sealed.
MoE is queued; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-validation-baseline-integrity.json`.

**Qwen and dense Gemma baselines complete, October 7 05:36 UTC:** each
student has 100 validation and 200 reserved test responses verified locally by
the production checks. Full prompts, raw/parsed answers, batch receipts and
checksums agree. Reserved test content and quality remain unreviewed. MoE is
starting its baseline; no main training has started. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-reserved-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-reserved-baseline-integrity.json`.

**All baselines verified, October 7 08:23 UTC:** each student has 100 validation
and 200 reserved test responses retrieved and checked locally by the production
validators. Prompts, raw/parsed answers, batch receipts and hashes agree; all invalid
answers remain counted. Reserved test semantics remain unreviewed. The pipeline
advanced to Qwen and dense Gemma training concurrently; MoE follows Qwen. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-validation-baseline-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-moe-reserved-baseline-integrity.json`.

**Training progress verified, October 7 11:40 UTC:** Qwen has completed
400 distinct notes in 50 continuing updates; dense Gemma has completed 200 notes
in 25 updates. All three saved checkpoints, including adapter and optimizer/RNG
state, are fully local and passed hashes, exact note coverage and counter checks.
Qwen's two training blocks took 34.9 and 33.2 minutes; dense Gemma's first took
92.9 minutes. Qwen's validation after 200 notes is fully retrieved and verified
against the same 100 inputs and batch plan as its baseline: 2 parsing failures
versus 13 untuned. This measures output reliability; semantic correctness/coverage
remain ungraded. Validation took 121.4 minutes versus 128.1 untuned. Qwen is now
validating after 400 notes; dense Gemma is validating after 200 and MoE remains
queued. Reserved test semantics remain unreviewed. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-checkpoint-200-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-200-validation-integrity.json`.

The preliminary backup storage charge was **$0.884**. The storage rate was **$0.0833/hour**, or **$2/day**.
Evidence: `target/distillation-pilot-v1/backup-volume-removal-20261007/`.

Current evidence: `target/distillation-pilot-v1/workspace-volume-20261006/`.
Previous publication evidence:
`target/distillation-pilot-v1/model-cache-stage-20261006/publication/publication-receipt.json`.
No automatic time/budget stop or deletion. Previous failure evidence is under
`target/distillation-pilot-v1/launch-20261006-two-gpu-recovery/`.
Launch evidence is under `target/distillation-pilot-v1/launch-20261005-two-gpu/`.
Actual execution and fit passed CUDA preparation October 6. Pilot throughput
is being measured. Observation continues through complete local retrieval/review and explicit
deletion. No automatic time/budget kill or deletion.

### Historical conditional subjects-only batched cost reference — October 3

This replaces the serial reference with a **projection**, using measured prep
batch shapes under **ASv6.48** and historical complete/truncated subject-answer
lengths. It assumes 1,000 distinct training notes per student, one continuing
pass, the proposed 100 validation / 200 final test notes, thinking off, and
only the selected student's final baseline/trained comparison. It does not price
the frozen full ASv6.100 pilot or authorize spending.

| Component | Projected GPU hours | Counted work |
| --- | ---: | --- |
| Training, all three students | 5.58 | 125 updates each; no checkpoint restarts |
| Validation baselines and checkpoints | 19.11 | 3 baselines + 15 trained stages, 100 notes each |
| Winner's final comparison | 2.74–5.39 | 200 notes before and after training |
| Extra lifecycle, startup and final retrieval | Allowance 1–2 | Model fetch/load, merge, checkpoint restoration/publication, retrieval tail |
| Total after 25% headroom | 35.54–40.10 | Headroom applied once to the combined hours |

At the prep's historical **$1.4153/hour including storage**, add $1 transfer
fees for about **$51–58**. At an illustrative $1.60/hour, about **$58–65**.
These are planning allowances, not confidence intervals or a selected offer.
The $3.26 preliminary prep charges already incurred are separate.

**Method:** for each measured batch, use its 64-token generation duration plus
`max(0, longest saved answer in the batch - 64) × measured incremental-token seconds`.
Use the incremental-token timing at the filled native cache; exclude parallel
synthetic cache-fill time. Retain historical truncated 4,096-token answers at
their saved length without claiming completeness. Reuse the observed 20-note
batch layout arithmetically five times for 100 notes and ten times for 200 notes,
including its small tail batch. Actual pilot notes will be distinct. Average
answer length alone would hide time spent waiting for each batch's longest answer.
Use old baseline lengths for baselines and old trained lengths for all five
checkpoints; no larger-pilot answer lengths exist yet.

Extrapolate the mean of two measured eight-example updates to 125 per student.
Their observed minimum/maximum sensitivity gives **4.20–6.97 total training hours**,
versus the 5.58-hour mean projection. Combining that sensitivity with the other
allowances yields **33.81–41.83 total hours**, about **$49–60** at the historical
rate or **$55–68** at $1.60/hour. Two updates do not establish a runtime bound.
The prep's first training-stage overhead already includes its initial model
fetch/load; do not add the earlier 838-second download observation again.
Progressive transfers overlap computation. Fifteen checkpoints extrapolate to
about 19.5 GB; at the historical offer's transfer rates, an illustrative 300 GB
in / 30 GB out costs about $0.90, rounded to $1. Transfer time is covered by the
extra allowance and headroom, rather than counted once per overlapping copy.

If all three final baseline/trained comparisons are generated before local
selection, the same projection is **45.84–47.09 hours / $66–68** at the historical
rate. The October 5 decision adopts that six-version test scope on the main
rental; neither historical projection prices ASv6.100 or approves spending.
Full autoregressive generation is unmeasured under the new lifecycle; short
samples and a single incremental step cannot guarantee full-output throughput.
New prompts/data may reduce batch sizes, increase training time, or need a
changed configuration. Reprice after those inputs are selected.

**ASv6.100 input audit, October 4:** offline native chat-template/tokenizer checks
used all 80 existing subject training examples and 20 held-out notes. The full
prompt matches the frozen source hash above. Old teacher answers were paired
with ASv6.100 solely for length checks; they are not adopted as pilot labels.
No new model calls, paid resources or pilot-note selection occurred.

| Token measure | Qwen3.8-27B | Both Gemma students |
| --- | ---: | ---: |
| Full ASv6.100 prompt, existing 100 notes | 9,210–9,651 | 9,041–9,495 |
| Longest prompt plus 4,096-token output allowance | 13,747 | 13,591 |
| Longest diagnostic training sequence with old teacher answer | 12,950 | 12,764 |
| Diagnostic training examples exceeding 8,192 | 80/80 | 80/80 |
| Prompts plus allowance exceeding 8,192 | 100/100 | 100/100 |

All three native 8,192-token preflights reject this input, as expected. All three
16,384-token preflights pass **token checks only** on the diagnostic collection.
That does not establish GPU fit, sufficient output allowance for future teacher
labels, or the context needed by the eventual pilot notes. Do not truncate the
full prompt, complete notes or teacher answers to force them into old bounds.

Using the saved planner memory constants and existing 88-GiB budget:

| Student | Calculated memory for one existing note | Current policy |
| --- | ---: | --- |
| Qwen3.8-27B | 88.32–91.50 GiB | Rejects even one note |
| Gemma 4 31B | 110.70–115.27 GiB | Rejects even one note |
| Gemma 4 26B-A4B | 75.27–77.55 GiB | One-note estimate is within budget |

The arithmetic reproduces every saved prep batch estimate exactly. These are
planner estimates, not observed GPU allocations or proof of OOM. Changing only
`max_length` leaves the worker's Qwen/dense memory rejection intact. Examine the
actual attention/cache workspace and update context/memory settings locally
before another hardware preparation. Preserve the selected one-96GB-GPU design,
complete BF16 models and full prompt; no new runtime configuration is approved
by these diagnostic calculations. The old hardware checks tested training only
through 6,531 Qwen / 6,440 Gemma tokens and generation caches through 7,328 / 7,245.
The actual pilot-data audit is recorded above; revised settings still require
validation. Pilot notes and all selected-teacher labels are now frozen.

The approved splits require **1,300 teacher subject calls**, now complete,
with training labels shared across checkpoints. The approved comparison has
**1,800 validation reviews plus 1,200 final reviews**. Reviewer selection, the
review prompt and actual token lengths are required to price reviews. The existing subscription route
assumes zero incremental API cash; paid API work would be additional and requires
separate admission/approval.

Evidence: `target/distillation-pilot-v1/asv6.100-input-audit-20261004/` contains
`tokenizer-audit.json` with the frozen prompt hash/native preflights and
`memory-policy-audit.json` with verified planner arithmetic. The earlier
`batched-cost-and-input-audit-20261003/` retains the reproducible historical
ASv6.48 cost calculation and superseded ASv6.98 length diagnostic. Native prep
receipts are under `subject-preparation-20261003-v2/` (Qwen) and
`subject-preparation-20261003-v3/` (Gemmas), plus saved subject answers from
`launch-20260929-v2/`.
The older hardware/runtime scenarios below do not price this subjects-only recipe.

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

At the measured 450 W subject-generation throughput, thinking-off validation
and the winner's thinking-off final comparison project to approximately 76–80 GPU hours.
Add cumulative training work, checkpoint checks and setup before applying any
headroom. GPU-hours are total work; elapsed rental time depends on the actual
schedule.

There are three student training paths, each with dependent
200/400/600/800/1,000-note stages. The earlier nine-independent-training-job
packing does not apply.
The selected pilot uses two 96GB RTX PRO 6000 cards, with a complete model on
each: Gemma dense on GPU 0, Qwen then Gemma MoE on GPU 1. Preserve the same per-response
generation settings and complete call accounting; dynamic batching controls
how many independent notes that GPU evaluates together.

Teacher labeling and local semantic review/selection add elapsed time outside
the rental. The historical price comparison does not reserve a specific offer
or authorize spending. Prepare and test the selected two-GPU launch
configuration locally before renting.

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

The final resource cost was **$13.392**. Evidence is
`observations/preliminary-charge-summary.json` and its native invoice snapshot.
The earlier failed rental's final resource cost was $0.395, bringing the combined final cost to **$13.787**. The next steps are completing the
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

The preliminary resource charge was **$0.338**.
The final resource cost was **$0.395**. The supervisor has exited.
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
