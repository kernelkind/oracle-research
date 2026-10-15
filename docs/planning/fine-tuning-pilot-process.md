# Fine-tuning pilot process

Compare **Qwen3.8-27B, Gemma 4 31B, and Gemma 4 26B-A4B**: how much does
learning from teacher answers improve quality, and what does it cost?

**Subjects only, approved October 2:** train and evaluate subject discovery and
hierarchy. Generate no masks for this pilot. Thinking stays **off** throughout
preparation, training and evaluation, approved October 2.

**Grading complete, October 14:** all 1,800 validation answers and all 1,200
reserved-test answers now have correctness and coverage grades, with no manual
review queue. The [200-note test results](#completed-test-grading-october-14)
compare each final 1,000-note adapter with its untuned baseline. Model selection
for continued subject training is now Qwen, as approved below. The completed
comparison itself performed no additional training or student generation.

## Approved Qwen continuation (October 14)

The user selected **Qwen3.8-27B**, approved **two additional complete passes over
the same 1,000 training notes**, and chose **one 96GB RTX PRO 6000**. The approved
schedule generates both checkpoints' validation and test answers during one
continuous rental, retrieves and verifies all required work, then terminates
the rental before local semantic grading. The new experiment's maximum charge
is **$43**, raised from $30 with the user's launch approval, including
preparation, failed attempts, storage and transfers;
the project's $1,000 lifetime cap and ledger admission still apply.
 The approved rental limit and project ledger still govern
every paid resource.

This is continued training from the existing final 1,000-note checkpoint,
including optimizer, schedule and RNG state. It is not a fresh adapter or a
new 3,000-note dataset. Keep the frozen Qwen revision, full **ASv6.100** including
its examples, 1,000/100/200 splits, thinking off, unquantized BF16 base,
FP32 rank-16/alpha-32 adapters, eight examples per update, token-averaged
answer-only loss and constant 0.0001 learning rate. Full training-data volume,
new labels, masks, preference training, rank changes and thinking-on training
are outside this continuation.

| Saved version | Total training-note uses | Distinct training notes | Total updates | New validation answers | New test answers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing pass 1 | 1,000 | 1,000 | 125 | Already saved | Already saved |
| End of pass 2 | 2,000 | 1,000 | 250 | 100 | 200 |
| End of pass 3 | 3,000 | 1,000 | 375 | 100 | 200 |

Generate **600 new answers: 200 validation and 400 test**. Test answers receive
mechanical accounting, parsing and integrity checks only while on the rental;
keep their content and semantic grades out of checkpoint selection. After
retrieval and termination, grade validation locally using the completed pilot's
semantic workflow, choose using correctness and coverage, then grade only the
selected checkpoint's saved 200 test answers. Existing pass-1 results remain
the comparison. The existing 200 test notes have already been examined; this
does not create a fresh untouched final test set.

For evaluation, load the saved adapter on a fresh BF16 base and merge the
evaluation copy. Verify that evaluation leaves the unmerged training checkpoint
unchanged, then restore its complete training state for the next pass. Preserve
both new checkpoints and the original checkpoint; freeze each pass's example
order and record every use without duplicating the underlying training rows.

**Estimate, not a reservation:** Qwen's saved pilot measured 2.8045 hours per
training pass, 2.0485 hours per 100-note validation generation and 4.1728 hours
per 200-note test generation. Two passes, two validations and two tests total
**18.05 GPU hours** before preparation, loading and transfers. The October 14
single-card server quote was $1.125/hour including 150GB instance disk, before
the persistent-volume decision. Allow roughly **20–24 rental hours**. Obtain a
fresh quote for the required volume and 30GB instance disk under the combined
**$43 maximum** below. Longer answers, host throughput and recovery can change
these estimates. Local grading needs
no rented GPU and does not extend the rental.

### Pilot failure audit and continuation requirements

The audit below traces the October 3–8 runtime failures and the completed
grading handoff to current production code and its regressions. The dated
three-family/two-GPU rules below describe the completed comparison; this
continuation packages Qwen only and has no Gemma preparation or baseline gate.

| Pilot evidence | Requirement for this continuation |
| --- | --- |
| Full ASv6.100 inputs exceeded the old context and 4,096-token output allowance; seven teacher hierarchies exceeded the 128-node guard. | Reuse the validated 20,480-token context, 10,240-token output allowance and subjects-only parser without the old node guard. Verify complete examples; do not truncate notes, prompt examples or teacher answers. |
| Dense attention/logit buffers made the full inputs impractical; CPU checks alone did not establish CUDA behavior. | Retain enforced efficient CUDA attention with no math fallback and the pinned fused linear cross-entropy training path. Rehearse the exact source/runtime locally and confirm actual Qwen CUDA loss/gradient agreement, longest-example updates and maximum-output cache shapes before main training. |
| An inference memory allowance was incorrectly applied as a training cutoff. Gemma-specific gradient and cache failures caused further replacement rentals. | Keep training measurements separate from inference batch admission. Preserve numerical checks and tolerances. Run matched Qwen preparation only; do not repeat the three-family qualification. |
| The old deployment assigns Qwen to GPU 1. Its required-card count is the highest assigned index plus one. | Freeze a Qwen-only package using logical GPU 0; copying the old assignment would still require two cards. Download only the pinned Qwen model. |
| Host DNS prevented SSH; a startup gate also charged the full transfer allowance against an inadequate local startup bound. | Verify image/driver, SSH route, host RAM, disk and complete storage/transfer pricing. Freeze setup and work allowances inside the approved $43 total; do not reuse the earlier $1 startup allowance. |
| A persistent-volume request used an unsupported mount path and was rejected. | Require a persistent local volume mounted at the provider-supported `/workspace` path, keep work under its child directory, and verify attachment, write/read and free space on the selected machine. A separate download rental is not part of this schedule. |
| Direct copying was slow; large checkpoints could delay small responses. | Use the tested provider-proxy route and progressive copier. Prioritize sealed responses, copy checkpoint files in bounded chunks, verify hashes before publishing completion markers, and reuse verified copies in final retrieval. |
| A controller can exit while a training child remains alive. Interrupted calls and partial publication must not be mistaken for finished work. | Retain worker locks through child lifetime. Reconcile the live worker before a recorded continuation; reuse complete checkpoints and saved receipts. Never regenerate a saved invalid answer or treat an unsealed partial checkpoint as resumable. Copier/observer failure must not stop training. |
| The generic `distillation/vast-launch.json` still sets a 43,200-second worker timeout. | Do not inherit a 12-hour cutoff for a 20–24-hour run. Freeze the approved no-automatic-timeout behavior, monitor cost/time, and complete retrieval verification before the approved normal termination. |
| A successful transfer or `report.json` alone did not prove experiment completeness. | Verify the parent and both continuing checkpoints, exact note uses and updates, all 600 raw/parsed answers, generation receipts, input bindings and seals before recording completion and deleting the rental. |
| Long-form DSRv1/DSRv2 grading failed qualification; the later automatic workflow completed validation and test grading. | Reuse DSMv3/DSSv2/DSLv10/DCSv1 and the completed role-specific settings. Keep teacher requirement groups fixed, identities out of semantic requests and invalid outputs in denominators. Missing reviewer work remains ungraded. No new grader design or paid API fallback is proposed. |
| Grading exposed shared-runner scheduling, history growth and overload recovery problems. | Use the landed runner fixes and native shared 30-request admission, with all ready batches submitted. Keep grading local in the established memory boundary; do not add an outer batch cap or hold the GPU for grading. |
| Budget admission | Reconcile current commitments before any paid work. A price quote or a deleted-instance report does not establish a current project balance. |

**Current implementation, audited October 14:** the saved parent checkpoint
passes `subject_checkpoint_metadata` with 1,000 distinct consumed notes,
125 updates and 1,658,323 supervised answer tokens. Its adapter and training-state
files verify against the saved seals. The original training order reproduces
exactly through `subject_training_plan` from the existing prepared dataset.

**Continuation implementation, October 14:** `distillation_deploy
prepare-continuation` derives one model's configuration from its saved parent,
verifies the same dataset and recipe, and freezes the parent manifest, plan and
checkpoint seals. The package carries the parent checkpoint and existing
baselines; it omits unused earlier checkpoints. Qwen uses logical GPU 0 and
matched Qwen preparation. New plans preserve the original note order, then
shuffle each additional full pass separately using seeds 18 and 19. The original
checkpoint, optimizer and RNG state remain unchanged; new checkpoints bind to
the new manifest and extended plan after verifying the original state identity.

Both new checkpoints collect validation and reserved test answers. Completion
verification requires both collections, their raw/parsed answers and receipts,
and all planned training-note uses and updates. Reruns reuse saved answers and
complete checkpoints, including when publication of the first test is interrupted.

**Local recovery approved October 14:** save training state every 16 optimizer
updates (128 notes) within each pass and retain only the two latest verified
recovery checkpoints. They contain adapters, Adam/schedule state, RNG and the
exact consumed-note cursor; they do not duplicate the base model. The launch
binds `ORACLE_RUN_RECOVERY_DIR` to
`/workspace/oracle-full-build/recovery-checkpoints`, with each run identified by
its frozen manifest hash. This directory is on the mounted local volume,
outside `work`, so intermediate checkpoints enter neither progressive SSH
copying nor terminal retrieval. Keep the permanent 2,000/3,000-note checkpoints
and their existing retrieval and evaluation behavior.

Write, sync and verify a new checkpoint before publishing it and removing the
oldest recovery. On continuation, reuse the newest verified recovery for the
unfinished block; ignore corrupt or incomplete saves and fall back to the
preceding valid checkpoint. Abandoned partial writes are cleaned before
resuming. Only updates since the recovery need repeating. The saved Qwen
checkpoint is 1,421,963,152 bytes: two recoveries use about 2.8GB, temporarily
4.3GB while writing a replacement, separately from permanent checkpoints.
SSH traffic does not increase for these intermediate saves. This protects
worker/container recovery while the local volume remains usable.

Remote continuation preparation requires `--cache-manifest`. It selects only
the parent's pinned model and revision from the pilot's existing manifest and
freezes `download_cache` in the package. On the same rental, before any model
preparation or training, the worker verifies its volume identity and write/read
access, checks free space, downloads missing files and repairs corrupt files
using the existing cache workflow. Good files are reused. Required free space
includes all missing files, the largest temporary file and the manifest's
32GiB reserve for saved work. Qwen's 26 pinned files total 55,586,035,724 bytes;
the package includes no Gemma downloads. All model subprocesses then run with
Hub access disabled. Offline completion verification also requires complete
download/checksum receipts and the selected volume's identity.

Use [the Qwen continuation Vast profile](../../sse_multivector/distillation/qwen-continuation-v1.vast.json)
with one 96GB card, 30GB instance disk and a persistent local volume for the
model cache, inputs, checkpoints and results. Plan for a 150GB volume; select it
with the GPU host, since a Vast local volume only attaches on its physical
machine. The profile rejects an unbound volume. Supply
`--local-volume-id`, `--local-volume-machine-id` and `--volume-reservation-id`
when creating the workload specification, or bind the corresponding launch
settings. A different machine is rejected before any provider action. The existing shared
launcher uses `--link-volume` with `--mount-path /workspace`, verifies the mount
and volume identity, and keeps work under `/workspace/oracle-full-build` with
`HF_HOME=/workspace/oracle-full-build/model-cache`.

The 24-hour instance allowance is at most $1.66/hour including instance disk,
with 80GB inbound and 10GB outbound transfers. Reserve **$41.50 for the instance
and transfers plus $1.50 separately for the volume**, within the same **$43
total**, including failed attempts. `check_offer` includes both allowances;
the frozen instance contract receives only the $41.50 ceiling. Reconcile and
record the volume's separate ledger commitment before creation or continued
retention. The profile requires at least 150GB and a 36-hour storage reservation
within $1.50, including detached time after instance deletion. Native launch
preparation queries `show volumes --raw` and requires a created, detached volume
on the selected machine, sufficient capacity and a known hourly rate covered
by one matching committed `vast_volume_reservation`. The entry must identify
the volume directly or through its `vast_volume_created` receipt, fund the full
allowance separately from the instance, and leave at least the full planned
rental before its retention deadline. These checks run again before GPU
creation, including when an instance reservation was already recorded. A
changed price, capacity, attachment, funding or expired retention blocks
creation. Fresh provider facts and a reconciled ledger are still needed.
The setup allowance is $5; $27 of instance spending calls for cost review.
Work has no automatic timeout. Machine 146170 is excluded. The profile uses
managed SSH with
`ssh-keygen -A && service ssh start`, the provider proxy and progressive copying.
There is no separate download rental. Replacement on the same host retains
the cache and saved work; verified retrieval and destruction of the previous
instance are still required before recorded recovery. Reusing an old pilot
volume for this different workload requires the existing explicit recovery flow
with `reuse_work=false` and a recorded reason, preserving its cache while
archiving prior work. Do not silently adopt the old three-family worker state.
Pass this profile explicitly with `distillation_vast --settings`; the default
settings file still describes the historical informal pilot.

The clean-container rehearsal found that the project input/parser entry points
now depend on the separate shared runner. VM build contexts include those five
shared Python modules and `_runner_bootstrap.py`; run/package identities hash
the actual shared source. A clean import test prevents a sibling checkout from
hiding a missing image dependency. The shared source for this preparation is
isolated at `experiment-runner-qwen-continuation-v1`, commit `1cfdd6a7`.

The real input package was prepared locally and mechanically verified: one Qwen
run, one preparation, 1,000 distinct training notes, 3,000 total note uses,
milestones 2,000/3,000, expected final 375 updates and 600 new answers. Artifacts
belong in the task worktree under `target/qwen-continuation-v1/`; `inputs-v8` is
the current package with the Qwen-only cache manifest and download enabled.
These corrections change the runtime identity; earlier packages and images
must not be used for this launch. The preceding image passes the interrupted-pass
and container-replacement rehearsal with local recovery. The current image
changes only the frozen launch-profile hash; every other input and runtime
source file matches the previous verified package.

To prepare another immutable package, use a fresh output directory:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-qwen-continuation-v1
export EXPERIMENT_RUNNER_ROOT=/home/dev/src/notedeck_worktrees/algos/experiment-runner-qwen-continuation-v1
pilot=../oracle-mvp/target/distillation-pilot-v1/main-pilot-memory-workspace-20261006
dataset=ee734d39ec007fb832763b273e96f24c250c32f0ef79a018e8cc08ac0b941349
python3 -m sse_multivector.distillation_deploy prepare-continuation \
  --parent-run "$pilot/operation/result/work/results/qwen" \
  --data "$pilot/pilot-package/data/$dataset" \
  --preparation-config "$pilot/source-configs/preparation-configs/qwen.json" \
  --cache-manifest "$pilot/pilot-package/model-cache.json" \
  --name qwen --additional-passes 2 \
  --output target/qwen-continuation-v1/inputs-next
```

**Verification complete, October 14:** local recovery passes 92 local contract
and data checks, plus the exact-training continuation test. The shared controller
and CLI are unchanged from the preceding 153 controller regressions and nine
pinned-CLI checks. The pinned PyTorch **2.12.1+cu130** VM verifies 10 architecture
and 52 workflow tests. Its updated deployment batch passes with 62 tests, nine
skipped; four cache tests and eight explicit volume/replacement/download/handoff
tests also pass. Those eight handoffs cover eight deployment skips. These
model rehearsals use tiny CPU models. Qwen's saved tokenizer separately passes
the actual 1,000 training, 100 validation and 200 test inputs: maximum complete
training length 18,114, answer length 8,452 and validation/test prompts
9,608/9,584 tokens. Thinking remains off. No full model weights are loaded for
this tokenizer check.

The real SSH continuation uses the current one-card profile and a mounted
volume, cold-downloads its pinned model, runs matched preparation, continues
its sealed parent and produces both checkpoints and both reserved test
collections. A replacement container then recovers the same volume with the
download server unavailable, reuses every cached file and preserves all saved
Qwen results byte for byte. Completion approval rejects missing first-pass test
answers, missing cache receipts and a mismatched volume identity. The VM is
stopped and its verified image export is at
`target/qwen-continuation-v1/vm/attempt-1792029436887070644/results/container.tar.gz`.
Every prepared `inputs-v6` runtime source hash matches that image's frozen build
context. The host's older PyTorch 2.8 reproduces an existing physical-batch
numerical tolerance failure on unchanged `main`; that same test passes in the
pinned VM without relaxing its tolerance.

The local recovery test injects a mid-pass failure after three intermediate
saves, verifies two-checkpoint retention, rejects a failed replacement save and
falls back after corrupting the newest checkpoint. Resumed adapters, Adam,
schedule and RNG match uninterrupted training exactly. The SSH rehearsal then
interrupts before the first permanent checkpoint, verifies that neither SSH
inventory includes recovery files, replaces the container and resumes from the
latest volume checkpoint. Its first new update follows that saved cursor, with
only the remaining updates performed before the required milestones and both
test collections pass completion review.

The cold-start watcher now
keeps polling `instance_starting` until the same instance runs and its results
are retrieved. Its production-flow regression verifies one instance creation,
one worker start and retrieval without a second invocation. Volume admission
rejects changed capacity before GPU creation, and cache admission checks free
space before starting any model subprocess, reusing valid files and repairing
only corrupt files.

**Launch preparation, October 14:** the user authorized proceeding. The matching
image is published privately at
`docker.io/kernelkind/oracle-mvp@sha256:028b43f6208ce87d91853e0d51f66a63a361e7dd73e12c22dff0258d7a8a2fa6`.
All 23 runtime source hashes match `inputs-v8`; anonymous manifest access is
denied. Publication receipts are in the task worktree at
`target/qwen-continuation-v1/launch-20261014/`. 
Credential permission checks recorded mode 0600. Pull authentication and the private image manifest checks returned HTTP 200, while a push-scope request returned HTTP 401.  Authenticate with pull scope first: a rejected push-scope request does not establish that the token is invalid. Do not send a write credential to the provider. The user subsequently approved the $43 total ceiling
and proceeding with launch.

The approved Server profile passes 68 local tests, with 20 fixture-dependent
skips. Its matching pinned VM passes 64 deployment tests, with nine phase skips,
four cache tests and all eight explicit SSH/volume/recovery phases. The unchanged
10 architecture and 52 workflow tests are revalidated from their sealed evidence.
The current verified export is
`target/qwen-continuation-v1/vm/attempt-1792034896840606891/results/container.tar.gz`;
its archive SHA-256 is
`3b5d14baf3fe6f48a3b180c0f000dec508d4c7e99a2e2fb81cec2092cf61d4cc`.
The exact published image matches this qualified VM image and all `inputs-v8`
runtime hashes. The VM is stopped. Actual Qwen CUDA preparation remains the
first model gate on the paid rental.

 The main pilot's GPU
charge is $133.907. The final backup storage cost was $0.888. The posted working-storage charge was $16.361.  

The user approved the $43 ceiling with a $1.66 hourly limit, covering the
unchanged 24-hour allowance, transfer allowances and separate $1.50 storage
reserve. The earlier workstation offer disappeared. The continuation configuration uses a single 600W RTX PRO 6000 Server card quoted at $1.413889/hour, 193,450 MB host RAM, and a 150GB volume at $0.041667/hour. The
profile now selects this same card type as the pilot, preserving every RAM,
reliability, driver and transfer check.  The October 15 continuation used a **150GB local volume** and a 30GB instance disk.    Worker attempt **001** downloaded Qwen's pinned files to the local volume.

**Continuation complete, October 15:** matched CUDA preparation, both additional
passes and all 600 new answers completed on that same worker attempt. Local
verification accounts for all 250 additional updates and 2,000 note uses, both
permanent checkpoints including optimizer/RNG state, changed finite adapter
weights, every raw/parsed answer, receipts, input bindings and file seals.
Checkpoint 2,000 has 100 validation answers, including two invalid outputs;
checkpoint 3,000 has 100 validation answers with no parsing failures. These
counts do not establish semantic completeness. New test contents and scores
remain sealed.    The conservative rental/transfer estimate plus the full storage allowance is **$29.35 of $43**. The verification record is
`oracle-mvp-qwen-continuation-v1/target/qwen-continuation-v1/launch-20261014/final-operation-verification.json`.

The user authorized local validation grading, comparison with pass 1, checkpoint
selection and then grading only the selected checkpoint's saved 200 test answers.
Use the existing teacher requirements and DSMv3/DSSv2/DSLv10/DCSv1 settings.
No new grading result or checkpoint selection is established yet. Retain the
training worktree and isolated runner for artifact paths and frozen bindings;
perform grading in `oracle-mvp-qwen-continuation-grading-v1`, with a separate
isolated runner. The native review importer verifies the continuation's parent
hashes and exact repeated-note plan. `--parent-run` resolves the saved rental
path to the unchanged local parent; `--model-version` fixes which saved
checkpoint may be opened. Continuation test preparation requires exactly one
explicit checkpoint, leaving other test collections sealed. Grading requires
no GPU rental or regenerated answers.

The native volume-setup path sends the full 1.53GB transport twice: first to
its staging directory for volume admission, then to the working directory.
The first copy completed and passed all manifest checks. The second connection
nearly stalled around 0.35GB; the host had ample free space and no disk or memory
pressure. Before any model worker started, the local watcher and stalled upload
were stopped, the partial copy was preserved, and the complete verified staging
copy was copied within the same volume. The native `_remote-verify-transfer` command then rechecked every transport file, launch binding and reserved-ledger receipt before the exact local transfer receipt was recorded and `run --watch` restarted. Native verification passed; no GPU replacement, model recipe change or training restart occurred. Receipts
are in `launch-20261014/transfer-repair/`. This was an operational recovery;
the frozen controller still contains the duplicate-upload behavior.

**Two-GPU execution approved October 5:** keep each complete student on one
**96GB RTX PRO 6000**. GPU 0 runs Gemma dense; GPU 1 runs Qwen, then Gemma MoE.
All three prep checks and all three baselines must pass before training starts.
Keeping both GPUs on one main rental was reconfirmed October 6 after comparing
separate rentals; retain the locally tested deployment and shared checks.

The collection and recovery flow is implemented locally. The combined prep→pilot
inputs are frozen and match the rebuilt, tested VM runtime. The user approved
private image publication and a **$285 combined prep→pilot budget** on October 5.
The image is published and verified private. The preparation failed: Qwen passed, dense Gemma exceeded its cache-memory guard, and Gemma MoE failed gradient agreement. No
main baseline or training started. All 86 available files (4.35 GB) were retrieved and independently rehashed.
Preliminary charges are **$1.974** against the original $285 total. Local repairs
pass 94 VM tests and six native tokenizer preflights; one VM tokenizer test was
skipped and covered by the separate preflights. The corrected image is published
and verified private. A replacement failed during container startup because host DNS prevented SSH. One reboot did not fix it. All necessary startup evidence was saved and hashed; no inputs, baseline or training reached the worker. Its preliminary cost was **$0.76**, bringing the two failed attempts to **$2.74**, within the original $285 experiment maximum. Both attempts failed.  A different compatible two-card configuration quotes $2.9389/hour.
Native launch preparation passed. The preparation configuration cost **$2.9389/hour** and was observed through startup, prep and verified retrieval; no pilot work started.
Machine 146170 is excluded. The local $1 startup gate counted the complete
transfer allowance and refused worker admission after successful SSH/input
verification. The refusal was reproduced, then admission was retried with a $5 local setup allowance. Worker attempt 001 started; no remote code, frozen inputs or experimental recipe changed.
Qwen prep passed. Dense completed its updates but hit an erroneous **88 GiB**
training cutoff; MoE failed its gradient check. All **101 available files / 5.85 GB** were verified.
Preliminary cost was **$2.543**, subsequently updated to **$2.687**. 
The local fix removes the training cutoff and keeps inference checks. The MoE
reference also now matches Liger’s gradient-scaling order; the local regression
passes without relaxing tolerances. The local workflow suite passes 89 tests;
12 VM-only checks were skipped. Full CUDA confirmation remains pending;
the runtime is rebuilt below.

**Recovery storage approved:** keep model downloads and compatible saved work
on a persistent local volume. Use a compatible two-GPU configuration for the next attempt, approved October 6; check current GPU and volume availability before booking. The launcher now preserves model downloads and verified work
across replacement, using the same image/data/recipe
and continuing the saved worker attempts. It requires verified retrieval and
confirmed deletion of the previous instance. If a repair changes the runtime,
retain downloads, archive the previous work and start a fresh comparison.
The storage rate was **$0.0833/hour**.
The download requests were rejected before allocating a GPU; no GPU charge or
training. The retry identified an invalid mount path. The launcher now mounts
at `/workspace`, keeping files under `/workspace/oracle-full-build`; local
checks and all 109 VM checks pass. The private runtime passes native preparation.
**Download stage completed October 6:** actual mounting and write/read checks
passed. All **42 files / 169.8 GB** were checksum verified on the volume; local completion review passed.  The preliminary GPU/transfer cost was **$0.455**. Full concurrent CUDA prep and MoE confirmation are still next.
The controller now retries slow image startup on the same instance. Local
regressions, VM rehearsal and private publication pass. Main launch reattaches
this volume to two GPUs for prep.

**Deleted-rental accounting approved October 6:** after verified deletion, release
the unused run budget immediately. Retain only unbooked rent for elapsed time at
the approved maximum rate plus the full transfer allowance, floored by posted
charges. Final invoices are reconciled separately and do not block the next
rental.  
The original $285 experiment total still includes every attempt and storage;
its remaining allowance is conservatively **$274.48** before a new commitment.

  Each 300GB volume costs $0.0833/hour.
 Repeat the tested one-GPU download and
verified retrieval stage on the new host, then launch its two-GPU prep/pilot
with unchanged prompts, data, models and training recipe.
The download cache held all **42 files / 169.8 GB**, checksum verified. The download completed successfully; local completeness review verified the retrieved evidence.
Its preliminary bill is $1.22, with 28 cents retained under the $1.50 bound.
The two-GPU run passed cache attachment and offline verification. Qwen and
Gemma dense passed full CUDA prep; Gemma MoE still failed gradient agreement.
**No pilot baseline or training started.** All **97 work files / 5.85 GB** and six preparation files were retrieved and independently rehashed. Preliminary charges were **$1.445**.
 The one-GPU diagnostic completed both cases without training updates. All **20 files / 3.17 MB**, including all four saved head-state/gradient pairs, were retrieved, independently rehashed and opened.  The preliminary diagnostic cost was **$0.21**.
 Head relative L2 error is **0.294–0.321%** with identical inputs;
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
The preparation passed Qwen and dense Gemma full prep. MoE stopped on its
seven-note native generation-cache probe: **88.080 GiB reserved versus 88 GiB
budget**, without OOM. **No pilot baseline or training started.** All **116 work files / 6.82 GB**, six preparation files, five sealed checkpoints and the three gradient-check reports were retrieved, independently rehashed and reviewed.  Preliminary charges were **$1.361**.  The corrected two-GPU configuration cost **$2.8139/hour**. Only MoE inference workspace changes **4 → 12 GiB**, consistently
in prep and pilot; total inference budget stays 88 GiB and the widest predicted
batch falls **seven → five**. Exact image, code, prompts, data, models and
training recipe are unchanged. Package verification and native preparation pass.
The replacement passed all three full CUDA preps and started baselines in the same run. The widest real cache probes reserve **76.28 GiB Qwen
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

**Training progress verified, October 7 13:58 UTC:** Qwen has completed
400 distinct notes in 50 continuing updates; dense Gemma has completed 200 notes
in 25 updates. All three saved checkpoints, including adapter and optimizer/RNG
state, are local and passed hashes, exact note coverage and counter checks.
Qwen's two training blocks took 34.9 and 33.2 minutes; dense Gemma's first took
92.9 minutes. Both Qwen validation sets are fully retrieved and verified against
the same 100 inputs and batch plan as baseline. Each has 2 parsing failures,
versus 13 untuned; the two failures at 400 notes hit the output limit. Generation
took 121.4 and 143.1 minutes, versus 128.1 untuned. Semantic correctness/coverage
remain ungraded. Qwen continued training toward 600 notes; dense Gemma is
validating after 200 and MoE remains queued. Reserved test semantics remain
unreviewed. Receipts:
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/gemma-dense-checkpoint-200-integrity.json`,
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-200-validation-integrity.json` and
`target/distillation-pilot-v1/main-pilot-memory-workspace-20261006/operation/observations/qwen-checkpoint-400-validation-integrity.json`.


Preliminary backup storage charges were **$0.884**.   

**Download stage approved October 6:** rent one GPU on the chosen machine,
verify attachment, and download all three pinned models onto the persistent
volume. Verify every required file and retrieve the evidence before deleting
that container. Keep the volume. Reattach it to the two-GPU rental, verify the
cache offline, then run full concurrent prep and the pilot. The one-GPU stage
collects no baseline or training results.
Save the download log, file sizes/checksums and a volume/machine receipt with
write/read and free-space checks. Verify the retrieved evidence locally before
deleting the download container. The two-card startup rejects missing or corrupt
cached files before prep; model loading stays offline throughout prep and pilot.

**October 6 recovery planning estimate:** singleton dense-Gemma evaluation gives
roughly **53–83 hours / $159–248** at the saved **$2.99/hour** two-card quote,
including storage, transfer and prep. A slower sensitivity case gives
**93 hours / $279**; including the failed prep’s preliminary bill gives $281.
These use older workstation timings and teacher-length proxies. Prep must
establish actual server-card fit and throughput; student answer lengths remain
unknown. The replacement uses the remaining original $285 approval.

**Local rehearsal → one-GPU downloads and volume verification → two-GPU Vast
prep → baselines/training/validation and sealed test
answers on the same rental → verified retrieval → local validation review →
unseal and score test answers.**

Freeze both stages locally. Prep checks the longest complete training example,
two continuing updates, save/reload/merge, brief generation, and full native
caches covering validation and reserved-test input shapes, using synthetic
continuations. It also checks the fused CUDA loss and adapter gradients against
native computation on short inputs, with Liger's FP32 softcap reference.
If all checks pass, discard prep adapters and start fresh pilot adapters on the
same rental. If prep needs substantial repair, retrieve and verify its evidence,
delete, and fix locally before renting again. Keep prep cheap and capture timing.

The October 3 prep used older, shorter inputs. Full ASv6.100 CUDA preparation
passed October 6 on the current two-GPU rental; full-run timing is being measured.

**Dynamic subject evaluation batches are approved.** Before each batch,
tokenize the waiting notes and choose how many fit the frozen per-GPU memory
budget. Account for resident weights, padding, caches through the allowed
output length, temporary buffers and headroom. Short notes can form larger
batches; long notes get smaller ones. The worker now implements this calculation
and saves batch receipts plus separate raw/parsed answers per note. GPU
preparation checks numeric memory allowances. Brief generation timing alone does
not establish the full pilot's runtime.

**Hardware preparation completed October 3:** all three students passed the
tested save/reload/merge/generate/restore cycle on the 96GB card. Results were
verified before explicit deletion. Check actual pilot data against the measured
lengths and memory bounds. See the technical plan for measurements.

## 1. Freeze shared inputs — locally

Freeze shared training, validation, and final test notes, checked teacher
answers, prompts, model revisions, and training settings. Keep authors and duplicates
within one split.

**SP frozen October 4:** use full
[ASv6.100](../../sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md),
including every worked example, in training and every evaluation. The technical
plan records its source hash.

**Input check, October 5:** the actual dataset needs up to **18,396 tokens**
per training example; some answers exceed the old 4,096-token output limit.
Seven training hierarchies also exceed the old 128-node limit. The new candidate
settings use **20,480-token context / 10,240-token output**, with no node-count
cap for subjects-only evaluation. Memory-efficient attention and fused training
loss are implemented and checked locally. The current CUDA preparation passed
long-input training and full native cache checks October 6; full-run timing
is being measured.

**1,000 training notes**, with validation checkpoints at **200, 400, 600, 800,
and 1,000**, plus **100 validation** and **200 final test** notes, are approved.
Keep final test notes out of development.

**Data selection approved October 4:** extend the existing random hash draw from
the fresh English corpus. Keep readable English root posts with no quote/reply
tags or inline references to other notes, and at most 512 SSE tokens in the full
original text. Preserve ordinary short and difficult posts. Use natural writing-form
proportions; check coverage with the existing 16-form review. Keep authors and
related copies within one split, with known prompt-development authors in training.
Freeze all 1,300 notes and splits before labels. The October 4 selection is now
frozen and verified; all 16 writing forms occur in the full sample.
Validation has no CREATIVE-form notes in this natural draw.

Generate all subject teacher labels using full frozen **ASv6.100**, **GPT-6.1 Sol /
medium**, through the subscription runner. Start at **32 concurrent calls**,
reducing to 24 if provider limits or transport errors arise. Save original responses,
parsed hierarchies and receipts; no masks or paid API fallback. Student thinking
stays off. This selects the teacher for these pilot labels; general teacher
comparison remains separate.

**Labels complete October 5:** all 1,300 passed structural and receipt checks:
1,000 train / 100 validation / 200 final test. Original responses and receipts
are saved; semantic review has not been performed.

## 2. Generate untuned baselines — Vast

Save one **thinking-off** baseline per candidate on the shared validation notes.
Each model generates its own subject hierarchy. Preserve original responses.
Also collect each baseline's answers on the 200 reserved test notes; keep those
answers sealed through local validation review.
Generate independent notes in batches whose size follows the memory budget.
Freeze the thinking-off batching policy per student; use it for that
student's baseline and trained checkpoints. Check and save each answer separately.

**Verify all three complete baselines before any pilot training.**
Check each answer as it arrives. Reparse raw responses and reconcile each note
with its generation receipt; count invalid/truncated model answers as failures.
The parser is checked against saved teacher answers, including JSON fences,
before weights load. Missing work, broken metadata or inconsistent parsing blocks progress.

A bad model answer is a measured failure. Missing work or a parser bug blocks
the affected comparison from advancing.

## 3. Continue training and evaluate checkpoints — Vast

Start **one continuing training run per student**:

1. Initialize its adapter and optimizer from the original model once.
2. Learn from **note → teacher subject hierarchy**: one training example per note.
3. After using every training example from the first 200 notes, save and verify
   the complete training checkpoint. Unload training from the GPU; load the
   saved adapter on a fresh BF16 base and bake its changes into this evaluation copy.
   Verify reloads under that policy. Generate subject hierarchies on the
   **same 100 validation notes**; save raw and parsed outputs and
   check response accounting immediately.
4. Discard the evaluation copy and restore the complete training state, including
   the exact next example. Continue through **400, 600, 800, and 1,000 notes**,
   saving and evaluating at each milestone. Keep all five complete checkpoints.
   Validation leaves the saved adapter, optimizer, schedule, and random state intact.

While each final 1,000-note evaluation copy is loaded, also generate its answers
on the 200 reserved test notes and keep them sealed. Earlier checkpoints generate
validation answers only. The primary comparison uses the three final adapters
and their corresponding untuned baselines.

**One complete pass is approved:** use every subject training example
once, without replacement, in five new 200-note blocks. Earlier notes and labels
remain saved; their examples are not repeated at later milestones. Within each
block, shuffle the subject examples using a fixed random seed.
Use the next **8 prompt–answer examples for one adapter update** on the selected
GPU, retaining a smaller final group when needed. With 1,000 notes, this
is **125 updates per student, 25 per checkpoint block**. Physical training groups
may vary with memory while preserving the same eight-example update and loss.
**Starting settings approved October 1:** learning rate
**0.0001, constant with no warmup; LoRA rank 16 / alpha 32** for ordinary adapters.
**Gemma MoE also adapts its routed experts at rank 2 / alpha 32**, retaining
rank 16 / alpha 32 for attention and shared MLP adapters. Original model and router
weights stay frozen. These are starting choices, not established optima.
**Numerical setup:** AdamW with no weight decay and gradient clipping 1;
unquantized BF16 base and mixed precision computation, FP32 adapter weights,
gradients, and optimizer state. LoRA dropout 0, frozen biases, standard initialization.
**Training loss:** average prediction error over all teacher-answer and native
turn-ending tokens in each update, excluding prompts and padding. No extra
answer or note weighting; longer answers contribute more tokens within an update.
Block membership, seed **17**, and the model settings are frozen in the candidate configurations.
Record loss, resource telemetry, and actual example coverage at each stage.
This compares
the tested configurations under a modest budget; one pass is not established as
optimal training for every student.

## 4. Retrieve verified results — Vast to local

One background copier transfers subject responses and checkpoints
as soon as saving finishes, while the experiment continues. Use Vast's SSH proxy
and copy small response files first. Check for new results between checkpoint
chunks. Completion markers follow verified files. Verify local copies
and retain remote originals at least until verification. Limit transfer bandwidth
and disk activity. The copier starts automatically beside the observer; final
retrieval reuses verified copies. Frozen run metadata, batch plans, started-call
records and saved batch receipts transfer before whole stages finish. The copier
automatically retries up to three times after failure; exhausted retries stay
visible and require inspection. Transfer failures never stop training.

For the full pilot, complete all necessary work before stopping the job or
deleting its rental
and verify that its data is fully retrieved locally. A successful transfer
alone does not establish completeness. Offline verification must account for all
three baselines, fifteen checkpoint evaluations, continuing training coverage,
all saved checkpoints, and six complete 200-note test collections before recording
the completion review required for deletion. If something is missing, keep the
resource and add that work. If stopping is preferable, ask for user approval
first. Automatic job timeouts, stops on watcher errors, and deletion are disabled;
time/cost thresholds call for review. I inspect validation responses as they
arrive and monitor training and GPU telemetry until explicit deletion. Test
responses receive mechanical accounting, parsing and file checks; their content
and semantic scores stay out of review and selection until validation review ends.

**Prep only:** repair straightforward failures immediately. If recovery needs
substantial work, retrieve and verify available data, then delete the rental
under the user's standing approval. Completing all prep checks is not required.

**Pilot recovery approved October 5:** diagnose and repair errors autonomously,
including necessary code or recipe corrections. Record changes and interruptions,
resume from verified saved state, and rerun affected comparisons when a repair
changes their conditions. Repair itself needs no further user approval. Preserve
original evidence; the completeness/deletion and spending rules still apply.

After interruption, reconcile the existing worker first. A failed worker needs
an explicit, recorded continuation on the same rental. Preserve its evidence,
reuse saved answers and complete training checkpoints, and verify a fresh
retrieval and completion review. Never regenerate a saved bad answer. An
interrupted call with no saved answer can run again only through that recorded
continuation. Keep monitoring GPU use, memory, disk space, updates and response
counts; save observations locally without opening test content.

## 5. Score and compare — locally, after the rental

Measure output reliability mechanically. Current semantic review defaults use
**GPT-6.1 Sol / xhigh** through the existing subscription transport. The
[approved eight-hour direction](../../sse_multivector/distillation-review-v1/README.md#eight-hour-review-direction-approved-october-11)
qualifies matching/support at xhigh and relationship checks at high separately;
it does not yet change deployed defaults. Review
findings for each note and model version refer to the complete post, frozen
ASv6.100, trusted teacher answer, candidate hierarchy and mechanical exact
subject matches. Model/checkpoint identities stay outside semantic requests.
Treat ASv6.100 as correct.
Explicit subject, immediate-link and coverage findings feed code-calculated
**correctness** and **coverage** scores. Correctness counts entries with valid
subjects and incoming links; coverage counts required teacher meanings preserved
completely at every compatible returned heading occurrence. Optional broader
headings are not mandatory; equivalent wording and valid extra headings are allowed.
Keep teacher meaning groups fixed across versions and average per-note scores equally.

**Prompt-development iteration approved October 10:** use 12–16 distinct
complete review inputs for the prompt being changed, covering observed failures,
correct positive and negative decisions, and earlier regressions. Establish
source-assessed decisions and evidence before candidate calls. Check further
cases and the
[four-note workflow](../../sse_multivector/distillation-review-v1/README.md#regression-scope-reduced-to-four-notes-october-11)
after that development set passes; the
original 50 random plus ten challenge answers remain the very final validation.
The ten-note DSLv4 run has finished generation unchanged and preserves its raw
report before formal audit reviews. [DSLv5](../../sse_multivector/distillation-review-v1/README.md#dslv5-definition-and-counterexample-draft-october-10)
has completed its approved 14-case Sol/xhigh development trial: all Booleans
agree with prepared targets, with two named-reference interpretations unresolved.
Complete records receive nine accepts, two rejects and three uncertainties in
both agent audits. The set does not pass; qualification and adoption remain pending.
The approved [DSLv6 scope trial](../../sse_multivector/distillation-review-v1/README.md#dslv6-scope-draft-october-10)
has completed 14 fresh first attempts. All Booleans retain the DSLv5 decisions;
two named-reference interpretations remain uncertain. Complete records receive
ten accepts, one reject and three uncertainties in both audits; the mothers/MILFs
record still adds human-only scope. The set does not pass; qualification and
adoption remain pending. The AS rule and schema stay fixed.
The subsequent approved [controlled scope diagnostic](../../sse_multivector/distillation-review-v1/README.md#dslv6-controlled-scope-diagnostic-october-10)
completed eight authored human/animal comparisons and six exact saved natural
controls with unchanged DSLv6 at Sol/xhigh. Both audits accept all 14 Booleans
and complete records; controls retain saved decisions. Native first attempts
reconcile at 14/28 with no reuse, retry or warming. The authored targets are
agent assessments kept outside model inputs, not human gold. The original
MILFs explanation and named-reference/list uncertainties remain unresolved.
Synthetic success does not qualify natural-case accuracy; broader qualification
and lower-effort testing remain pending.
The user approved the exact [DSLv7 wording](../../sse_multivector/distillation-review-v1/README.md#dslv7-post-interpretation-draft-october-10)
using the original post to interpret supplied wording, with the AS parent-child
rule and output contract fixed. Native preparation now supplies the bound post
when the template requests it, for actual edges and coverage compatibility.
The approved DSLv7 diagnostic completed fourteen fresh Sol/xhigh first attempts
from nine source notes in the agreed 60-answer sample. Booleans agree with all
twelve frozen pre-call targets; two remain unscored. Both output audits give
eleven accepts, two uncertainties and one rejected explanation. Keke Palmer's
record adds named-reference uncertainty despite target agreement; Family Ties'
witness invents unestablished fixed-work facts. The set does not pass, and
12/12 target agreement is not established correctness. Legacy labels remain
provenance; no targets were changed after outputs. The 71-token prefix is
ineligible; there was no warming, reuse or retry, and the allowance ends at
14/28. That recommendation led to the user-authorized
[DSLv8 revision and diagnostic](../../sse_multivector/distillation-review-v1/README.md#dslv8-reference-boundary-diagnostic-october-10).
DSLv8 uses the post to interpret existing wording without restoring omitted
facts through reference identity. Fourteen fresh first attempts retain all
twelve frozen targets; the two originally unscored cases remain unscored.
Both output audits give twelve accepts, one rejected explanation and one
uncertainty. The rollover verdict now excludes the omitted posted action, but
its counterexample only changes what is discussed. The MILF tag's lexical scope
was unresolved in that review. All native receipts and preserved inputs pass; allowance
usage is 14/28 with no reuse, retry or warming. The development set does not pass.
The subsequent deep audit found the trusted maternal interpretation missing
from DSL inputs and a compulsory-counterexample requirement that obscures
missing restrictions. The user authorized the
[DSLv9 draft](../../sse_multivector/distillation-review-v1/README.md#dslv9-evidence-requirements-draft-october-11):
restore AS's subject-wording guidance, supply selected trusted source contexts
for interpreting existing words, and make counterexamples optional. The exact
wording and [fourteen-case diagnostic](../../sse_multivector/distillation-review-v1/README.md#dslv9-approved-diagnostic-october-11)
were approved. All fourteen fresh Sol/xhigh first attempts match the seven valid
and seven invalid pre-call assessments; both audits accept all complete records.
The independent auditor assessed inputs before viewing candidates, without
targets or prior reviews. This passes the development panel, not unseen accuracy
or production adoption. The run takes 64.714 seconds with no retries or reuse;
the 76-token prefix is ineligible, so no caching or warming is used. Three new
preparation tests pass; broader failures reproduce on unchanged code. Native
bulk-runner migration is now tested; the
[four-note native regression](../../sse_multivector/distillation-review-v1/README.md#four-note-native-regression-october-11)
uses R02, R15, R21 and R14, all three checks, original sealed sources, verified
saved-request reuse and automatic queue admission. It completes in 15 min 7 s
with 99 fresh judgments, two warmups and two recovered stream interruptions.
Mechanical, receipt and score-assembly audits pass. Complete-output audit finds
one DSL explanation that expands an English-practice timing restriction and two
related uncertain explanations; no definite DSL Boolean error is identified.
The regression fails its complete-output gate. Three reused matching/support
inputs also retain uncertainty over `on Nostr` versus `with Nostr`. Lower-effort
testing remains paused; the final sixty remain pending.
The user subsequently authorizes a
[DSLv10 timing-scope draft](../../sse_multivector/distillation-review-v1/README.md#dslv10-timing-scope-draft-october-11).
It replaces one explanatory paragraph and prepares twelve native cases offline:
three prior scope findings, five accepted controls and four authored local/shared
timing contrasts. Independent input review agrees on five valid and seven
invalid targets. The user subsequently approves the wording and
[twelve-case diagnostic](../../sse_multivector/distillation-review-v1/README.md#dslv10-timing-scope-diagnostic-october-11).
Both agent audits accept all decisions and complete explanations: the earlier
scope findings are resolved on these cases and all controls pass. Native source, receipt and
accounting checks pass; twelve fresh first attempts take 1 min 27 s, with no
retries, reuse, warming or cache hits. DSLv10 remains experimental. The separate
matching/support Nostr questions remain unresolved; the final-sixty validation
remains pending.
The subsequent [Nostr source audit](../../sse_multivector/distillation-review-v1/README.md#nostr-relationship-source-audit-october-11)
makes no calls or prompt changes. The three saved conservative judgments already
match initial input assessments, but an independent contextual-reading challenge
warrants retaining their unresolved status. No definite reviewer error or
instruction defect is established; these are not correctness targets settled
by agreement. Historical outputs and labels stay fixed, with uncertainties
reported separately from resolved judgments in further development checks.
The subsequently authorized
[DSLv10 four-note regression](../../sse_multivector/distillation-review-v1/README.md#dslv10-four-note-regression-october-11)
completes the same four answers and all three checks in 22 min 51 s. It uses
98 fresh relationship judgments, two warmups and two recovered failed attempts;
61 successful historical requests supply unchanged matching, support and three
DSL records. Root and independent agent audits accept all 156 resolved distinct
model decisions and their full explanations; three distinct Nostr judgments
remain unresolved. All 25 mechanical proofs and score-assembly checks pass.
This passes the resolved development regression, without establishing unseen
accuracy or settling Nostr. Historical labels remain fixed. The next recommended
step was a small balanced lower-reasoning trial; no lower-effort calls or final
sixty-note validation start in this regression.
The user subsequently expands the same workflow to
[eight notes at xhigh](../../sse_multivector/distillation-review-v1/README.md#dslv10-eight-note-regression-october-11):
retain the four answers and add the first four other valid answers in the frozen
random order (R01, R03, R04, R05). Prompts, mechanical rules, verified reuse,
eligible caching and original source assessments remain fixed. Input-first
review precedes candidate inspection; interpretation uncertainties remain
separate. Generation completes in 28 min 35 s: 784 completed occurrences and
553 justified relationship skips, with 160 successful fresh comparisons, five
warmups and two recovered failed attempts. All 77 mechanical proofs, stopping
dependencies, receipt/budget checks and frozen source bindings pass. Complete
original model-output audits give **380 accepts, one reject and 15 uncertainties**
across 396 full versions of 395 semantic inputs. The sole rejection concerns
R05's humorous account of morning odd jobs around town beneath morning outings.
A subsequent independent source-first audit challenges its home-work witness:
client locality may change the established meaning of jobs around town, and
the account's actor relationship remains disputed. This record is now unresolved;
no definite error is established. The saved labels, raw report and review history
remain unchanged. The current assessment retains 380 accepted full records and
16 unresolved records; qualification remains pending.
Known successful receipts cache 7.82% of input tokens; warmup overhead
makes net catalog savings negative by about two cents. Full cost is unknown
because the two failed receipts lack usage. The authorized small
[outings diagnostic](../../sse_multivector/distillation-review-v1/README.md#dslv10-outings-diagnostic-october-11)
then completes with DSLv10 unchanged: eight balanced authored controls pass
full-output audit, the simple original repeats sound false, and the rich
original repeats true but remains disputed. Two sound saved controls reuse
without calls. Native validation and the shared 11/22 attempt reconciliation
pass, with ten fresh judgments, one warmup and no failures or retries.
No prompt revision is justified by the disputed original alone. Lower-effort
testing, qualification and final-sixty validation remain pending.
The subsequent authorized
[four-note high comparison](../../sse_multivector/distillation-review-v1/README.md#four-note-high-versus-xhigh-comparison-october-11)
pauses after one support decision error and two matching explanation errors.
All 92 completed relationship outputs and 25 mechanical proofs pass; one answer
retains 12 distinct pending requests. Fresh xhigh confirmations correct all
three errors; software-runtime interpretation joins the three Nostr uncertainties
outside correctness counts. On 142 resolved shared inputs, high decision loss
is 0.70 percentage points and full-output loss is 2.11 points. This partial,
exposed panel does not qualify high. Prompts and mechanical rules remain fixed;
minimum reasoning effort, reviewer qualification and final-sixty validation
remain open.
The unchanged xhigh development regression subsequently finishes on
[24 notes from the agreed sixty](../../sse_multivector/distillation-review-v1/README.md#dslv10-twenty-four-note-regression-october-11),
retaining the previous eight and adding sixteen structurally valid random
answers. Native parallel evaluations retain all three checks, mechanical rules,
stopping and eligible-prefix caching. Three agents audit 1,621 complete output
versions, confirming three support errors and keeping 45 uncertainties separate.
All 423 prepared mechanical proofs reproduce in production. Qualification and
minimum reasoning effort remain open; the sixty remain the final validation.
Historical DSLv8 outputs, reviews and targets remain unchanged.
Qualification remains pending and production defaults to DSLv2.
Sol/xhigh, subscription SSE, trusted ASv6.100,
implemented mechanical rules and schemas remain fixed. The completed ten-note
run retains its frozen concurrency of 16; the current shared runner uses automatic
queue admission for future dispatch. Lower-effort qualification remains pending. Native
selected preparations shrink the
case plan and subsequent reports while retaining full production inputs and
baseline receipts. Audit explanations as well as decisions; keep ambiguities
explicit and disclose development exposure. This is separate from the sealed
pilot test split. See the [process and prepared reference](../../sse_multivector/distillation-review-v1/README.md#case-level-prompt-development-approved-october-10).

**Eight-hour direction approved October 11:** retain all **1,800 validation
outputs**, all three semantic checks and required-meaning coverage at every
compatible subject occurrence. Model generation must fit within **eight hours**,
assuming resolved backoff and at most 30 concurrent requests. The six-hour
model-work target leaves two hours of headroom; it is not a measured forecast.
The final fifty random plus ten challenge answers and accepted maximum
two-percentage-point correctness loss remain unchanged.
The user approves **DCSv1** wording for a four-note xhigh trial: search uncovered student subjects
for one compatible placement of an already-matched required teacher meaning,
then verify any positive witness with the existing relationship check. A
negative search must establish that every supplied candidate is incompatible.
Its numbered evidence must account for every candidate; candidate membership
does not certify the semantic reasons. Test the new search at xhigh first,
against independently audited pair evidence on four existing notes, keeping
that comparison separate from high qualification for single-pair DSLv10.
Retain actual-edge judgments and matched-subject consistency checks. Separately
qualify high for relationships and reuse of positive semantic premises for
support/relationship judgments, retaining model-dependent provenance. Do not
propagate negative support verdicts. The
[four-note xhigh DCSv1 trial](../../sse_multivector/distillation-review-v1/README.md#dcsv1-four-note-coverage-search-trial-october-11)
finishes ten fresh searches and four eligible warmups in approximately 75
seconds. Three full-output audits accept nine negatives and one missing-placement
witness; unchanged DSLv10 verifies the witness through exact-input reuse with
zero new calls. The small, development-exposed panel has only one positive
case. The authorized
[four-note positive-placement challenge](../../sse_multivector/distillation-review-v1/README.md#dcsv1-four-note-positive-placement-challenge-october-11)
then completes 38 searches and four warmups in approximately 118 seconds.
Full-output audits record 34 accepts, two errors and two uncertainties.
Unchanged DSLv10 verifies all 18 returned witnesses: 17 valid pairs and one
invalid pair, using 16 exact-input reuses and two fresh calls. It catches the
invalid incest witness; the missed television placement remains a false
negative. Read-only analysis finds accepted complete matching plus trusted
teacher paths could settle four searches, including that miss. The user then
approves the [conditional reuse implementation](../../sse_multivector/distillation-review-v1/README.md#conditional-matchingpath-reuse-october-11).
Native offline preparation verifies 38 searches become 34, with all 89 self
guards and remaining reviewer inputs unchanged. Reuse requires current native
acceptance or exact-input/output bound audit acceptance; it records the matching
receipt and actual teacher path/context, leaves separate matching uncertainties
unresolved and makes no new model calls. DCSv1 is unqualified, and further expansion unchanged
is not recommended. Remaining interpretation contexts and the eight-hour
runtime remain open; production stays DSLv2. See the
[evidence and qualification direction](../../sse_multivector/distillation-review-v1/README.md#eight-hour-review-direction-approved-october-11).

**Mechanical decisions approved October 9:** all three checks use mechanical
results wherever trusted inputs settle the question. An exact teacher subject
match supplies meaning agreement and support for the same original post. An
exact ordered pair copied from an actual trusted teacher link supplies local
parent-child validity. Identical parent and child wording also retains every
parent restriction. Record these results without model calls; matching both
endpoints separately is insufficient to certify their relationship. No exact
match leaves a semantic question, not an automatic rejection; a validated empty
teacher catalog establishes no complete match. Record mechanical evidence and
zero model attempts. Share identical saved review results with frozen source,
prompt and runtime bindings while retaining every numbered placement; explicit
fresh repeats remain fresh calls. Existing parsing and student/reviewer failure
rules remain distinct. The subsequently authorized implementation supplies
source-bound selected-case routing and native zero-attempt results for all three
checks. Mixed runs dispatch only remaining semantic cases; explicit fresh repeats
bypass mechanical completion. Reports retain evidence and distinguish mechanical
comparisons from model checks. See the [rules and implementation](../../sse_multivector/distillation-review-v1/README.md#mechanical-decisions-for-all-three-checks-october-9).
Prompts, scoring and semantic qualification status retain their existing state;
implementation verification adds no real model calls. A21 remains a discrepancy
against an unadjudicated agent label:
its new parent and nonmatching child do not reproduce a trusted teacher link.

**Complete validation workload preview subsequently authorized October 9:**
the user's `proceed` authorizes counting all saved validation outputs offline
through the shared launcher. The reusable command verifies frozen source and
stage receipts and applies production mechanical rules without model calls.
Across 18 versions and 1,800 outputs, 142 invalid answers remain separate failures.
Matching and support each settle 7,446 of 44,284 occurrences mechanically,
leaving 36,838 semantic occurrences and 9,820 distinct input questions per check.
Relationships settle 1,841 of 33,817 occurrences, leaving 31,976 semantic
occurrences and 16,670 distinct inputs. The total is 36,310 distinct remaining
questions under fixed prompts/settings, before saved-answer reuse, warmups and
retries. This historical count excludes coverage-placement comparisons and is
not the complete-evaluation workload. The [native report and method](../../sse_multivector/distillation-review-v1/README.md#complete-validation-workload-preview-october-9)
retain per-note/version/model denominators. Mixed reference identity headers are
checked before decoding only evaluation content; reserved files and checkpoint
weights are not opened. This counts work without preparing reviewer requests,
qualifying DSMv3/DSSv2/DSLv2, adjudicating A21 or changing scoring.

**Offline token and runtime estimate subsequently authorized October 9:** the
same command accepts `--estimate` and repeated `--timing-experiment` paths, with
`tiktoken` available in its Python runtime. The [native estimate and reproduction command](../../sse_multivector/distillation-review-v1/README.md#validation-review-token-and-runtime-estimate-october-9)
bind unchanged prompts and verified fresh saved receipts. Distinct questions
contain 24.195 million rendered input-text tokens; all remaining occurrences
contain 79.399 million. Both exclude provider instructions, framing and schema overhead.
The 59 current-prompt verdicts project 15.050 million output tokens, including
reasoning once, and 15.34 hours with eight continuously occupied slots. Small
selected samples, mixed message roles and partial slot occupancy prevent treating
this as measured batch wall time; warmups, throttling, retries and review work
are additional. This historical estimate excludes coverage-placement questions
and does not estimate the complete evaluation. Current automatic template
prefixes are below the caching threshold; separate natural-prefix opportunities
promise no hits and adopt no
cache change. This adds no inference, scoring, qualification or A21 adjudication.

**Coverage-matching qualification scope agreed October 8:** target required
complete teacher meanings; optional derived teacher headings are not mandatory
coverage targets. Still review every student heading and immediate parent-child
link, and every compatible occurrence for placement of required meanings,
including general student headings. Establish required/optional flags from the
trusted teacher answer and post independently of candidates, then freeze them
across note versions. Those flags and revised cases remain to be established;
the current matching adapter, prompts and saved trials are unchanged. See the
[agreed scope](../../sse_multivector/distillation-review-v1/README.md#coverage-matching-qualification-scope-agreed-october-8).

The subsequently authorized
[teacher-relative qualification case preview](../../sse_multivector/distillation-review-v1/README.md#teacher-relative-qualification-case-preview-october-8)
compares all teacher wordings in six controlled cable variants, without new
requirement labels or scores. It includes the omitted-heading disagreement and
two separate DSMv2 non-exact matching inputs. The legacy DSRv2 renderer is used
only for whole-case inspection. This preview does not adopt a revised pilot
rubric or change the scorer/prompts; structural allowances, adoption and new
calls remain open.

The user subsequently accepted the expected judgments for all six cases in
conversation: equivalent wording passes all three checks; reversed negation
fails teacher agreement and post support; a wrong parent fails teacher
agreement and link validity; a missing general teacher heading fails teacher
agreement while remaining subjects/links stay valid; consistent renumbering
passes and should be checked mechanically. The unchanged-answer control passes
all three checks by definition because the teacher is trusted, and should also
be checked mechanically. These authored expectations are not
measured model verdicts or adoption of a revised scoring rule; no new calls,
prompt changes or scorer changes occurred. See the
[decision record](release-decisions.md).

On October 9 the user approved the unchanged
[DSMv2 meaning-matching instructions](../../sse_multivector/distillation-review-v1/README.md#dsmv2-matching-instructions-approved-october-9).
One generated subject is compared with the complete distinct teacher list;
the decision is one JSON object with `teacher_id` and `reason`. Subject support
and parent-child validity remain separate judgments. Qualification, new calls
and final scoring remain open; R05 is not resolved by approving the wording.

The subsequently authorized [DSSv1 draft](../../sse_multivector/distillation-review-v1/README.md#dssv1-subject-support-prompt-draft-october-9)
judges post support for one unmatched subject from the full post, returning
Boolean `valid` and string `reason`. The proposed `Lengths` / `4 m cable A`
controls and support inheritance await approval. Two initial support inputs
from already-agreed cases are prepared below and now initially tested. Pilot
scoring is unchanged.
The user then approved reusing ASv6.100's support rules unchanged instead of
paraphrasing them. The revised DSSv1 wrapper adds only the narrow review task
and output format around `ASV6_100_SUPPORT_RULES`, to be loaded verbatim from
the original source during shared-workflow preparation. The adapter added below
now supplies that variable. The user subsequently accepted the revised
wrapper's exact wording after seeing it in full. DSSv1 now passes its two initial
cases in the subsequently authorized trial below;
controls, qualification and proposed support inheritance remain open. No
inference or bulk adoption is authorized by accepting the instructions.

The user then authorized drafting
[DSLv1 for parent-child validity](../../sse_multivector/distillation-review-v1/README.md#dslv1-parent-child-validity-prompt-draft-october-9)
before qualification. Its input is one actual immediate pair's parent and child
subject strings; ASv6.100's parent-child rule is supplied verbatim from the
original source. The post and surrounding hierarchy are excluded under that
rule. It returns Boolean `valid` and string `reason`, with a lost restriction
and possible counterexample for invalid pairs. Post support and teacher
agreement remain separate checks. The user subsequently approved the unchanged
DSLv1 wording after seeing the full instructions. Its three initial inputs now
pass in the subsequently authorized trial below, using the shared Boolean schema.
Pilot scoring is unchanged. Wording approval does not qualify the reviewer or
authorize new calls.

The user then accepted adding ASv6.100's subject-wording guidance verbatim to
complete-meaning matching before qualifying a new version. Native `revise`
creates [DSMv3](../../sse_multivector/distillation-review-v1/README.md#dsmv3-asv6100-wording-guidance-draft-october-9)
from approved DSMv2, changing only the version label and an interpretive block
containing the original subject-wording paragraph. The trusted teacher reference,
inputs, matching criteria, response contract, case expectations and saved
evidence are unchanged. The user approved the exact DSMv3 wording after seeing
the full instructions. The unchanged draft now passes its two initial cases
below; broader qualification is pending. Wording approval alone authorized no
calls or accuracy/cost measurement.
Previous results do not qualify DSMv3, and the disputed R05 match remains open.

The user subsequently authorized preparing and showing
[first three-check development inputs](../../sse_multivector/distillation-review-v1/README.md#first-three-check-development-inputs-october-9)
before model calls. Seven native requests reuse the agreed cable judgments:
two DSMv3 matching, two DSSv1 support and three DSLv1 immediate parent-child
checks. The source-bound `distillation_verdict` adapter loads the original
ASv6.100 rules verbatim, derives immediate parents from student numbering and
keeps expected Boolean judgments outside model input. Shared schema/validation
and qualification reporting are tested with an offline executable fixture.
The original offline preparations remain unrun. The initial trial below uses
separate native-prefix preparations with GPT-6.1 Sol / xhigh / subscription SSE and
concurrency 8. The prompts, final scoring and sealed test data are unchanged.
These controls isolate the three judgments; they do not establish reviewer
reliability at scale. The exact seven inputs and expectations were then shown
in conversation and accepted, then run after the user authorized the initial
xhigh trial and prefix warming. Three warmups and seven verdicts completed
without failure, retry or reuse; all seven verdicts and reasons pass the initial
checks. Cached input and cache writes are zero throughout; these small inputs
are below the documented caching minimum. See the
[initial trial record](../../sse_multivector/distillation-review-v1/README.md#initial-warmed-three-check-trial-october-9)
for native receipts, actual usage, warmup overhead and latency. The larger
training controls and fresh repeat below extend this evidence; broader
qualification remains necessary before bulk use. The user wants to compare
lower reasoning levels later, after establishing xhigh reliability. Cases, expected judgments and prompts should
stay fixed while measuring semantic errors, latency and actual token usage,
including cached tokens. Initial settings remain unchanged; recording that
future intent adds no lower-effort experiment or model calls.

The user subsequently authorized preparing
[larger training controls](../../sse_multivector/distillation-review-v1/README.md#larger-training-controls-prepared-october-9)
for presentation before new model calls. Seven controlled changes use three
existing ranked training extremes: maximum entries, maximum distinct catalog,
and longest answer. Unchanged DSMv3/DSSv1/DSLv1 preparations contain 6/6/4
requests, initially unrun, with authored judgments outside prompts. LC03’s
matching, support and link expectations, LC04’s matching and support failures, and
LC07’s invalid link have explicit user acceptance. The user delegated review
of LC01, LC02, LC05 and LC06 to the agent; those expectation assessments are
complete without changes to the authored labels. The trusted teacher catalog
and post stay complete; link inputs derive actual student parents. The
accepted LC03 loses a three-day restriction while retaining post support; its
teacher match and link fail. LC07 moves Dr. Abu Safiya beneath a parent that
explicitly excludes him; its trusted exact subject strings need no matching or
support calls. The accepted LC04 changes `rather than printing money` to `and
printing money`, contradicting both teacher wording and the post. In the
delegated assessments, LC01 and LC05 preserve meaning; LC02’s changed count
and LC06’s first-ban wording fail the relevant checks. The agent inspected
complete native inputs, including actual selected parents; no material
ambiguity remained. No further individual user review of these controls is
required. The user then authorized the
[larger trial](../../sse_multivector/distillation-review-v1/README.md#larger-three-check-trial-october-9)
at unchanged Sol / xhigh / concurrency 8. Native qualification passes 6/6
matching, 6/6 support and 4/4 links, and all 16 reasons have native agent
acceptances. Every request completed on its first attempt, with no reuse or
reported cached tokens. The user then authorized a
[fresh xhigh repeat with eligible prefixes](../../sse_multivector/distillation-review-v1/README.md#larger-three-check-repeat-with-eligible-prefixes-october-9),
requiring sufficiently large shared prefixes before caching or warming.
All 16 fresh verdicts agree with the expected and baseline judgments, with
native agent acceptance of every reason. Exact naturally shared prefixes
qualify for two matching groups and one support group; small prefixes and
singleton cases receive no explicit caching or warmup. The two matching groups
report 6,528 and 4,480 cached input tokens; support L6 reports none despite its
eligible prefix. All 16 verdicts and three warmups complete on first attempts,
without reuse. Prompts, inputs, labels and Sol / xhigh / concurrency 8 are fixed;
the prefix route changes the role split for seven verdicts. Warmup overhead and
per-experiment usage are recorded, without a causal cache-savings claim. This
repeats the same authored training controls. Broader qualification and
lower-effort comparison remain open; no bulk grading or test unsealing is adopted.

The user subsequently approved a
[broader actual-output trial](../../sse_multivector/distillation-review-v1/README.md#actual-validation-preparation-approved-october-9)
at xhigh for all three checks. Shared preparation now binds saved validation
generations to the frozen post, teacher and task; support uses the post and
relationships derive the actual student parent. Agent expectations remain
unverified, and unresolved labels receive no semantic pass/fail. Freeze the
sample and expectations before calls. These are now frozen for 20 distinct
subjects from 16 previously unused validation notes. All 60 verdicts and two
eligible warmups now complete on first attempts, without reuse or mechanical
failure. Agreement with frozen agent expectations is matching 17/19 (A15
unscored), support 19/20 and links 17/20. Semantic disagreements remain;
qualification stays pending, and A19 was disputed before calls. Matching caching
produces hits; support caching none. Prompts, scoring, lower-effort work and
sealed test data retain their existing status.

The authorized [fresh confirmation](../../sse_multivector/distillation-review-v1/README.md#fresh-confirmation-of-four-rejected-cases-october-9)
repeats four rejected cases and four accepted contrasts with unchanged prompts,
inputs and Sol / xhigh settings. All eight complete on first attempts without
reuse or warmup. Matching A01 and link A03 now agree; support A20 and link A21
repeat errors. All contrasts stay accepted; native agent review records six
accept and two reject. Qualification stays pending, with agent expectations
unverified. No prompt change, lower-effort comparison, scoring or test unsealing
is adopted.

The subsequently authorized [DSSv2 draft](../../sse_multivector/distillation-review-v1/README.md#dssv2-exception-clarification-draft-october-9)
addresses the repeated support exception error with one claim-scope clarification
after the intact ASv6.100 excerpt. The offline A08/A20 preview preserves cases
and settings and makes no calls. The user subsequently approves the wording and
[bounded support trial](../../sse_multivector/distillation-review-v1/README.md#dssv2-bounded-support-trial-october-9)
on 20 existing cases and three same-post variants, with four fresh DSSv1
comparisons. Only the three long-post cases receive an eligible warmup; the
shared 56-attempt limit includes provider retries. The completed trial matches
20/20 actual DSSv2 labels and 3/3 DSSv2 controls; fresh DSSv1 matches 4/4.
All 27 verdicts and reasons pass native agent review. All 28 requests, including
warmup, finish on first attempts without reuse or retries. Fresh DSSv1 correctly
rejects the original exception case after two identical-request failures;
these results do not isolate an improvement caused by DSSv2. No cached tokens
are recorded; the sole warmup adds $0.005884 in catalog API-equivalent cost.
Qualification remains pending on unverified agent expectations, and all other
review checks, scoring and sealed test data retain their status. The remaining
repeated DSLv1 error is the recommended next issue. The user subsequently
authorizes [DSLv2 drafting](../../sse_multivector/distillation-review-v1/README.md#dslv2-parent-restriction-clarification-draft-october-9)
and showing the wording before calls. The untested clarification forbids an
added presentation/action requirement absent from the parent and accepts a
retained restriction in a clause or modifier while rejecting mere mention that
drops its meaning. The AS rule, pair inputs, verdict/counterexample contract,
labels and settings remain unchanged. No experiment is prepared or model called;
wording approval, semantic testing and qualification remain pending at this
drafting stage. The user subsequently approves the exact wording and
[bounded parent-child trial](../../sse_multivector/distillation-review-v1/README.md#dslv2-bounded-parent-child-trial-october-9):
19 original pairs, seven training controls and four fresh unchanged DSLv1
comparisons, preserving model/settings/AS wording and source labels. A06 remains
excluded; A12's interpretation issue is recorded before calls and separated
from the 25 uncontested DSLv2 assessments without relabelling. Thirty verdicts
share a 60-attempt limit. Prefixes are short, so no warming occurs. DSLv2 agrees
with 24/25 assessed expectations; A12 is separately uncertain and A21 still
fails. Fresh DSLv1 also fails A21, agreeing on 3/4 comparisons. All 30 first
attempts complete without reuse or retries; native reviews give 27 accept, two
reject and one uncertain. Training controls pass native qualification; broader
qualification remains pending. The clarification does not resolve the failure
at Sol/xhigh. Reconsidering the check against trusted teacher relationships is
recommended; no new method is adopted and other checks/sealed data stay intact.

[DSRv1](../../sse_multivector/distillation-review-v1/README.md) is the draft prompt,
report schema and qualification specification. Qualification checks trusted
examples, controlled valid/invalid changes and full-size training hierarchies
before bulk review. If GPT-6.1 Sol / xhigh cannot perform this reliably, rethink
the approach. Drafting this specification does not authorize qualification calls,
bulk reviews or test unsealing; reusable implementation and actual reliability
were still pending when the draft was recorded. The subsequent authorized
offline implementation adds source-bound preparation, report validation,
scoring and qualification checks through the shared experiment workflow.
All 29 cases can be prepared without inference, and an authored Q17 report
provides a concrete preview. The user requested stress inputs from the largest
saved ASv6.100 generations. Offline sizing of all 1,300 labels selects eight
training notes: the union of the top five by entry count and canonical answer
length. They include the overall maxima of 145 entries and 35,966 answer bytes;
final-test labels contribute aggregate sizes only. Complete stress reports
establish completion, while known-result controls test semantic behavior.
After seeing the preview,
the user authorized qualification calls October 8. Initial requests were rejected
with HTTP 400 and no generated reports; the request schema was corrected while
retaining application duplicate checks. The corrected requests produce complete
large reports, but qualification has failed: Q04 penalizes a trusted unchanged
example, and Q21/Q22 change unrelated judgments across controlled variants.
Q23's stream closes with an unfinished report near fifteen minutes; this is
an ungraded transport failure, not evidence of a model output limit.
All 29 cases were attempted once: 28 complete reports and one interrupted
report. Seven of eight largest generations completed. The user subsequently
directed concurrency 8 with existing exponential backoff; the original trial's
concurrency 1 receipts remain unchanged.
The [DSRv1 qualification evidence](../../sse_multivector/distillation-review-v1/README.md#october-8-qualification-evidence)
records the findings. Bulk grading remains unqualified; process revisions and
test unsealing require separate authorization.

The user subsequently authorized drafting and preparing
[DSRv2](../../sse_multivector/distillation-review-v1/README.md#dsrv2-draft-and-offline-preview)
before further model calls. It makes the authority of ASv6.100's worked examples
explicit and supplies the original Q20 receipt's same 66 groups / 44 required
flags to Q20–Q22. These are provisional consistency inputs, not accepted pilot
classifications. The shared adapter verifies the receipt and exact task, post
and teacher binding; the existing all-placements scoring remains unchanged.
DSRv1's failed trial is preserved. After receiving the preview and test sequence,
the user authorized real DSRv2 qualification with Sol / xhigh and concurrency 8.
Q04 passes `8/8` correctness and `2/2` coverage with both meanings required.
The small set finishes with 17 passes, Q14's semantic regression (`6/10` instead
of `8/10` correctness), and Q01's ungraded stream interruption. DSRv2 qualification
has failed. At concurrency 8, four of eight unchanged large hierarchies and both
controlled variants complete; four large streams are interrupted and ungraded.
Both variants fail consistency: the untouched Money transfers link and
compatible headings change despite the fixed groups / flags. All 29 distinct
cases are attempted once across the preserved subsets, yielding 24 complete
reports and five ungraded interruptions. No failed request is retried.
Adoption remains open; bulk review and test unsealing are not authorized.

The October 8 matching discussion next authorizes an offline
[DSMv1 preview](../../sse_multivector/distillation-review-v1/README.md#matching-only-offline-preview)
before calls: one generated subject against its fixed teacher list, with exact
matches handled mechanically and authored expectations outside the prompt.
Separate-note development and confirmation controls include the largest saved
training generations. This tests complete-meaning matching alone; it does not
audit ASv6.100, accept provisional required flags, or replace the full review
process. Sol / xhigh and concurrency 8 stay fixed. After seeing the preview,
the user authorized running the 16 development controls. All 16 pass on their
first attempt: eight matches and eight nonmatches, with no failures, retries or
reuse. This initial controlled result does not establish pilot-wide reliability.
The [DSMv1 development evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-development-trial-october-8)
records actual usage and findings. The user then accepted running the reserved
confirmation set with DSMv1 unchanged: all 16 pass on their first attempt,
without failures, retries or reuse. Both sets pass 32/32 authored controls on
separate source notes. See the [confirmation evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-confirmation-trial-october-8).
The user subsequently authorized an independent repeat of the confirmation set
with identical inputs/settings and saved-response reuse disabled. All 16 fresh
calls pass and preserve the original teacher IDs/null; only explanation wording
changes in 15 reports. The [repeat evidence](../../sse_multivector/distillation-review-v1/README.md#dsmv1-independent-confirmation-repeat-october-8)
records measured usage. This supports repeatability on the controls, not
accuracy on actual distilled wording or the other semantic review questions.
The accepted next step prepares an offline matching preview from actual saved
validation wording, with DSMv1 and settings unchanged. Baseline and final
checkpoint selections across all three models yield 22 distinct inputs: eight
agent-assessed matches, thirteen agent-assessed nonmatches and one unresolved
case. The user accepted the assessed nonmatch for `Fakery` under DSMv1's
existing complete-meaning rule; `Club symbols` remains unresolved. Acceptance
does not independently verify gold. Native
qualification remains pending, and unresolved placeholders are not nonmatches.
Preparation made zero reviewer calls. See the
[actual-wording preview](../../sse_multivector/distillation-review-v1/README.md#actual-distilled-wording-offline-preview-october-8).
Independent verification, resolving the meaning boundaries, additional calls,
effort/batching comparisons, full review adoption and final-test unsealing remain
subsequent decisions.

The user then accepted allowing the original post to clarify the sense of
wording already present in either subject, while still forbidding missing
restrictions to be supplied from the post. Draft
[DSMv2](../../sse_multivector/distillation-review-v1/README.md#dsmv2-post-interpretation-draft-october-8)
implements this distinction and prepares the same 22 targets offline with
zero calls. DSMv1's tested prompt remains preserved. Sol / xhigh, concurrency 8,
complete-meaning matching and trusted ASv6.100 references remain unchanged.
The authorized offline club assessment sets R19's expected match to T06 for
DSMv2, with no lost restriction in the card-suit sense selected by the post's
`♣`. A separate source definition preserves DSMv1's unresolved expectation.
The authorized offline self-custody check retains R16's expected nonmatch:
`Self-custody` omits the Bitcoin asset restriction even when the post identifies
the guide as about Bitcoin. Its DSMv2 reason is clarified without changing the
expected ID or assessment status. This matching judgment does not judge support
for the general heading. All expectations remain unverified and qualification
is pending.
The user subsequently authorized the
[two-case DSMv2 trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-two-case-post-interpretation-trial-october-8).
Two fresh Sol / xhigh calls return the expected T06 for R19 and null for R16,
with valid reports, no retries and no response reuse. This shows the intended
distinction in these calls; repeat stability and general reliability remain
open. It does not authorize the other 20 calls, bulk review or test unsealing.
The user then authorized the
[remaining offline post checks](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-post-visible-expectations-october-8).
All 20 expected verdicts are retained: eight matches and twelve nonmatches.
Their recorded reasons now account for the visible posts; all complete inputs,
expected IDs and assessment statuses remain unchanged. A fresh full-set preview
makes zero calls. This completes the post recheck, not independent gold
verification or semantic qualification. Further reviewer calls remain a separate
decision.
The user then authorized the
[remaining 20-case trial](../../sse_multivector/distillation-review-v1/README.md#dsmv2-remaining-20-case-trial-october-8)
using the shared launcher and unchanged Sol / xhigh, concurrency 8 settings.
All 20 final reports are valid; nineteen agree with the recorded expectations.
R05 returns `Inauthenticity` for `Fakery` instead of expected null and is marked
agent-uncertain pending adjudication. There is one successful provider-overload
retry and no response reuse. Prompts and expected labels are preserved;
qualification remains pending. This does not select a revised prompt or
authorize additional calls, bulk review or test unsealing.
The subsequent authorized [eight action/property controls](../../sse_multivector/distillation-review-v1/README.md#dsmv2-actionproperty-controls-october-8)
pass all four paraphrase matches and four nonmatches with unchanged DSMv2 /
Sol / xhigh, concurrency 8. Their explanations preserve the explicit action
versus property distinction. These small-catalog diagnostics were authored
after R05's disagreement; they do not settle its short-wording equivalence,
establish production reliability or change the prompt. R05's expected null
and uncertain review remain preserved. Further calls remain a separate decision.
The subsequently authorized [single-case fresh repeat](../../sse_multivector/distillation-review-v1/README.md#dsmv2-r05-fresh-repeat-october-8)
inherits R05's identical prompt, inputs, evidence and settings with response
reuse excluded. It again returns T17 with a different explanation, without
retry. This reproduces the disputed verdict in two calls but does not settle
its semantic correctness or independently qualify the reviewer. The repeat
has an agent-uncertain review; expected null remains unchanged. Further calls,
prompt revisions and bulk review remain separate decisions.

Compare quality before/after training and across data sizes, with failures,
speed, and cost visible. Invalid/truncated output and an empty answer to a
required task receive both zeros; a correct empty answer passes. Missing or
incomplete reviewer judgments are ungraded evaluation failures. Missing output
or provenance mismatches block evaluation rather than becoming model-output zeros.
Assess the returned subject hierarchies before model selection.
Use the final 1,000-note validation versions for primary model selection; the
five checkpoints show learning progress and regressions. Check the semantic
grader locally and freeze the review criteria before unsealing test answers.

## 6. Confirm on the final test

After validation review and model selection are fixed, unseal the saved test
answers. Score **all three final 1,000-note adapters and all three untuned
baselines** on the same 200 notes: **1,200 test responses**, collected during
the main rental with thinking off. Report each student's gains, failures, speed
and cost, with uncertainty; a close or unconfirmed gain can remain inconclusive.

This compares the tested recipes after the same 1,000 training notes. It does
not establish each student's best possible checkpoint. An earlier validation
peak remains evidence in the learning curve; confirming that earlier version
on the test notes would require additional inference. Test results do not revise
the experiment or choose another checkpoint.

Test collection and completeness checks passed the local VM rehearsal. Separate test
files stayed outside content review until the user authorized the six-version
test grading. Earlier automatic collection reports exposed only their counts
and locations. The combined rental was approved up to $285; its measured
execution and recovery evidence is recorded above.

### Completed test grading (October 14)

The authorized local run finished at approximately **09:37 EDT October 14**.
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

Four reviewed shared-runner fixes were necessary during execution:

- `f0b7a60`: remove duplicate scheduling-state cleanup while preserving the
  locked transaction; measured critical CPU work falls from 27.89 to 16.73 ms.
- `1fd278e`: omit the global experiment inventory from each batch's scheduling
  history, retaining its own events; sampled history entries shrink by 98.7%.
- `cc0fbb8`: allocate vacant request slots among owners that actually have a
  registered ready request; preserve the existing fairness rules and 30-slot cap.
- `9575d04`: retry temporary model overloads per request with exponential delay
  and Retry-After, while retaining account-wide recovery for explicit limits
  and transport recovery for HTTP/2 failures.

All four changes are committed on the shared runner's local `main`. Their
production-path regressions and combined-main checks passed, including the
unchanged isolated rerun of one test's cleanup timeout. Two environment-bound
memory integration checks were unavailable. Runner handovers drained active
calls and preserved saved successful receipts before resuming. The prompts,
grading policy and model settings were frozen throughout.

All ready batches submitted immediately through shared 30-request admission.
The workload stayed inside a **32 GiB, zero-swap systemd boundary**. During
the coverage transition it reached that limit and reclaimed clean file cache;
monitoring recorded **zero OOM events**. Later HTTP/2 GOAWAY waves temporarily
reduced concurrency through the existing recovery policy and resumed
automatically. No speculative proxy or transport-policy change was made.
The initial launch was approximately 00:33 EDT and completion 09:37 EDT:
about **nine hours elapsed**, including repair handovers and provider waits.
This run does not establish the earlier eight-hour fresh-run target.

Independent streaming verification checks the exact answer set, identical
note IDs across cohorts, score fractions, completion checkpoint and **8,967
protected source hashes**. It completes in 7.17 seconds with 43.4 MiB peak RSS.
The final report SHA-256 is
`d6d040c9f2f98e1a2ce17827132efc679cfdffab0ccdb70221783424ab0146f6`.
The ignored artifacts are retained under
`oracle-mvp-test-grading/target/distillation-review-v1/grading/test-1200/`:
`automatic/grades.json`, `completion-summary.json`, saved native receipts,
observer logs and memory/retry evidence. That worktree remains frozen at
Oracle `a9c074a4`; `experiment-runner-test-grading` remains frozen at
runner `9575d04`. Both are retained for artifact paths, provenance and
receipt-safe reuse. The four runner fix worktrees retain their ignored audit
artifacts for the measured fixes above.

### Approved Qwen thinking screen (October 14)

The user authorized a seeded random **20-note validation subset** for the final `Qwen/Qwen3.8-27B` adapter, generated manually on GX10 with thinking on, then handed separately to the unchanged grader. The seed is
`Qwen-thinking-20-20261014`; original validation indices are
0, 6, 7, 14, 20, 34, 36, 41, 44, 51, 60, 68, 70, 71, 73, 74, 76, 91, 95, 96.
The comparison reuses the saved thinking-off grades for these exact notes;
it does not regenerate the pilot or use the reserved test set.

Base revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, final checkpoint
1,000, BF16 weights, greedy decoding and original ASv6.100 inputs remain fixed.
The native thinking template receives `reasoning_effort=xhigh`, a 16,384-token
thought allowance and the pilot's 10,240-token final-answer allowance inside
40,960 context tokens. The measured inputs contain 9,248–9,466 tokens, requiring
36,091 tokens at the maximum combined allowance. Local generation runs at most
eight requests concurrently inside a 96 GiB, zero-swap systemd boundary;
immediate per-note receipts permit resumption without regenerating completed notes.
The grader imports the completed manual collection through
`prepare-distillation-review-trial --saved-generations`, retaining original
inputs, model/checkpoint/policy identities and invalid-output zero scores.
The grader has its own isolated worktree and existing 32 GiB memory boundary.

GX10 preflight found missing Python headers and CPU duplication during weight
loading. Matching Python 3.12 headers were extracted into the experiment
directory without a system installation. The stock Transformers loader's
Linux `mmap` path retains anonymous CPU pages after transferring weights on
this unified-memory host. A production-sized 178 MB BF16 tensor probe verifies
bit-identical GPU values with safetensors' native `pread` backend and no file
mapping. Selecting `pread` inside the unchanged Transformers loader and
disabling asynchronous materialization loads the full model in **53.5 seconds**.
The selection is scoped to model loading and restored afterwards. CUDA
allocations are capped at 80 GiB, and an independent one-second watchdog stops
only this job if host available RAM falls below 20 GiB. Earlier setup attempts
stopped before generation; the host records no OOM.

The first SDPA generation launch ran for approximately 100 minutes without a
completed batch; it did not log individual token progress. Its masked attention
path repeats four key/value heads into 24 query heads. Generation was stopped
with zero saved answers, preserving its source, runtime and log. Its replacement
used native FlashAttention2 pinned to
`db6b51744f0cd7061386442c09df890fc6d9f47e`, loaded through an isolated
`kernels==0.16.2` installation. Actual BF16, left-padded Q24/KV4 attention and a
small native Qwen model with cached decoding pass the comparison against SDPA;
the cached-decode comparison is bit-identical. No custom attention bridge is
used. The native loader resolves the pinned kernel online from its existing
cache; base and adapter weights remain pinned and local-only.

That Transformers runtime retained the correct PyTorch causal-convolution
reference path. A prebuilt kernel passed raw
BF16 convolution probes, but its native configuration failed a combined model
check and is not enabled. A brief loading attempt was stopped before generation;
the failed check and logs are preserved. No bridge or source build was added.

That stopped FlashAttention2 launch logged generated steps every 15 seconds.
Full-model loading took 49.4 seconds, the first generated token followed 78.65
seconds of prefill, and the first measured decode intervals advanced at
approximately **2.40 steps/second**
across eight rows (about 19.2 tokens/second while all rows generate). Host
available RAM is approximately 38 GiB after prefill, with no OOM or swap. These
measurements establish advancing generation; they do not measure the original
launch's decode speed or prove the attention path caused its full delay.
The native Qwen template supports thinking levels `low`, `medium` and `xhigh`
(default); the current screen uses `xhigh`. The thought-token allowance is a
separate bound, not a reasoning level.

The user stopped generation on October 14 to fix avoidable full-cache copying
and audit the execution settings. The stopped attempt has zero saved answers;
its input, script, runtime, log and stop receipt are retained under
`stopped-flash-copy-audit/`. Grading has not started. Source inspection confirms
cached single-token decoding and GPU placement, but the padded Transformers
path repeatedly concatenates, clones and gathers the growing full-attention
cache. These additional passes plausibly explain much of the observed speed;
the traffic estimate is not a profiler measurement. Live hardware checks found
no contention, swapping or active thermal/power throttling.

The replacement uses stock vLLM **0.31.0 / Torch 2.13.0+cu130** in a separate
run-owned ARM64 environment, with native paged hybrid attention and continuous
batching. The original Torch/Transformers environment is untouched. The exact
20 notes, original AS inputs, greedy decoding, xhigh, BF16 model/cache precision,
FP32 recurrent states and token bounds remain fixed. The original GPU merge was
exported as standard text-only safetensors: 851 BF16 tensors, 50.10 GiB, with
hashed source/export receipts and atomic publication. Native eager safetensors
loading avoids the former CPU mapping duplication. The engine uses one CPU
thread, Triton attention/prefill, a native CUDA GDN decode kernel, and a fixed
**22 GiB** cache pool. Eighteen GiB would not fit eight near-limit requests plus
their recurrent states without relying on prefix sharing. The CUDA allocator
remains capped at 80 GiB in the same process; the 96 GiB, zero-swap CPU boundary
and independent 20 GiB host-memory watchdog remain active. No quantization,
CPU offload, dynamic adapter or custom cache bridge is used.

The native regression reproduces 16 KV concatenations and 16 gathers in the
former padded HF path. The replacement emits the same sixteen greedy tokens on
the identical four-layer hybrid fixture, with maximum selected-token
log-probability difference 0.003969 and zero history-copy operations. An
8,192-token prefix trial reuses 7,840 tokens and matches uncached continuation.
Production driver tests cover thought/final boundaries, stop tokens, reordered
rows, atomic individual saves, interrupted/completed resumption and rejection
of an unexpected saved note. The real importer retains malformed/truncated
answers as invalid outputs, preserves the exact twenty input identities, and
binds every runtime receipt through collection source hashes.

The full-model eager benchmark measures **3.96 decode steps/second / 31.7
output tokens/second** on eight original 9,276–9,466-token prompts and **3.19
steps/second / 25.5 output tokens/second** on eight diagnostic 36,000-token
contexts. These are 32 steady decode steps per measurement, not complete-answer
timings. Cache addresses remain fixed; GPU reservation peaks at **72.4 GiB**,
host available RAM stays approximately **42 GiB**, and safetensors mappings
remain absent. The synthetic late contexts are performance probes, not graded
answers. Native decode-only CUDA graphs for batch sizes 1, 2, 4 and 8 pass
prefix/state tests and reproduce all **256** checked full-model greedy tokens.
The short-context graph benchmark reaches **32.3 output tokens/second**, a
modest 1.8% increase, with approximately 64 MiB extra GPU reservation. Torch
Inductor compilation remains disabled; the engine's native kernel warmup stays
enabled. Optional FlashInfer random-sampler warmup is disabled for this
greedy-only run. Native CuBLAS BF16 linear operations are appropriate for
SM12.1; the optional SM100-only BF16 GEMM backend is ineligible. Asynchronous
scheduling remains disabled to keep stopping and receipt handling synchronous.
Hardware checks find no throttle, contention or swap activity; the model still
must read approximately 51 GB of weights per decode step.

The [pinned Qwen template](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/chat_template.jinja)
implements `xhigh` through a reasoning instruction, without assigning a numerical
token limit. The 16,384-token thought cap belongs to this experiment. The current
driver aborts a request that reaches that cap before `</think>`, retaining its
reasoning and an empty, truncated final answer. Early results include both these
cutoffs and a natural completion using 15,012 thought tokens plus 5,173 final
tokens. A capped trace ends with “Now need final JSON”; hitting the cap does not
establish a reasoning loop. The unchanged grader counts these empty outputs as
invalid, so its overall score measures this bounded configuration rather than
unrestricted `xhigh` capability. No larger-budget policy is approved yet.

The [Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B#best-practices)
recommends sampled thinking (`temperature=1.0`, `top_p=0.95`, `top_k=20`), which
differs from the frozen greedy screen. This recommendation does not establish
that sampling would fix the observed cutoffs. The pinned base also contains
approximately 0.79 GiB of MTP tensors; the text-only merged export omits them.
Native vLLM supports Qwen MTP, but its draft acceptance, greedy equivalence and
memory/performance on this fine tune remain untested. It is not enabled in the
stopped run. Any budget, sampling or MTP change requires a separately recorded
configuration and validation; this run's source and policy remain frozen.

The manually launched twenty-note generation restarts at **19:35 UTC on
October 14** with this validated configuration and immediate individual saves.
The user stops this configuration at approximately **22:00 UTC** after fifteen
records are saved: eight completed JSON answers and seven empty final answers
caused by the thought cutoff. Notes 71, 73, 74, 91 and 96 remain unfinished.
The generation unit and its memory watchdog are inactive; host available RAM
returns to approximately 118 GiB. The fifteen records, runtime receipt and stop
receipt are preserved remotely and locally. The capped configuration must not
be resumed unchanged. No replacement policy has been applied.

The user requires a high GPU memory allowance for the replacement, while the
standing instruction to protect the host remains in force. The GX10's
[128 GB is coherent unified CPU/GPU memory](https://rog.asus.com/in/support/faq/1056142/),
not a separate VRAM allocation. The measured host exposes 121.6 GiB total and
approximately 118 GiB available while idle. The approved replacement raises the
CUDA allocator ceiling from 80 to **96 GiB** and the fixed hybrid cache pool from
22 to approximately **40 GiB**, retaining the **20 GiB host-available watchdog**.
Adding eighteen GiB to the measured cache configuration predicts approximately
90.4 GiB GPU reservation and 24 GiB host availability. These are sizing estimates;
the larger pool and actual allocation must be validated before launch. Raising
the allocator ceiling alone does not increase the engine's fixed cache capacity.
The stopped driver's settings and receipts remain unchanged.

The user approves natural EOS generation inside the model's native **262,144**
total context, with no separate thought or final-answer cutoff. Preserve the
eight naturally completed answers and regenerate notes 6, 7, 14, 20, 34, 36,
51, 71, 73, 74, 91 and 96. The reusable manual driver is
`sse_multivector/distillation_manual_generation.py`; it validates the original
inputs and merged weights once, imports completed records without rewriting
them, and saves each new answer atomically. Six production-path tests cover
natural completion beyond the old bounds, unchanged reused records, input and
runtime tampering, completed resumption without a model load, and cache counters.
The native manual importer accepts a source-bound per-answer policy override;
twenty import/trial regression tests pass. `SamplingParams(max_tokens=None)`
explicitly selects native remaining context instead of vLLM's sixteen-token
default. Context exhaustion remains a reported truncation.

The policy permits up to eight model-runner slots. The documented execution
option `--max-num-active-seqs` can lower concurrent admissions after a stopped
run if measured cache pressure warrants it, without changing frozen inputs or
completed records. Actual engine settings remain in each invocation's receipt.
Progress includes saved-note percentage, generated tokens, running/waiting
requests, cache use and cumulative preemption counts. Native cache preemption
can reset computed history; retained prefixes may reduce the ensuing work.
The replacement uses `qwen-thinking-20-natural-20261014` paths. Generation is
manually launched and grading remains a separate handoff after all twenty
answers are available.

The larger-memory benchmark passes on October 14: **90.5 GiB peak CUDA
reservation**, approximately **24 GiB host availability**, and zero preemptions.
All **128** checked greedy tokens match the earlier runtime. Eight original
prompts reach **32.2 output tokens/second**; a diagnostic batch containing one
70,000-token context and seven original prompts reaches **29.7 tokens/second**.
Both measurements use sixteen steady decode steps. Cache addresses stay fixed,
safetensors mappings are absent, and the allocator fraction remains set in the
same worker process. Model initialization and both benchmark phases take
209 seconds, excluding input verification. Diagnostic outputs are not graded.
The manual twelve-note generation starts at **22:43 UTC**, preserving eight
answers for an initial **8/20 (40%)**. Its source copy, policy and input hashes
are frozen separately from the repository checkout; grading had not started at
that launch.

**Provisional audit and status — October 15, 10:55 UTC.** The latest verified
snapshot at 10:55:42 UTC has **15/20 saved (75%)**: eight reused answers and
seven new natural completions, with four requests running and one waiting.
Long generations are approximately **131,000 tokens**; note 74 is waiting at
115,006 generated tokens after one cache preemption. GPU reservation is
**90.42 GiB**, with approximately **23.5 GiB host RAM available**. The seven new
records have parseable final JSON, one closing thinking marker, natural EOS and
no truncation. Their reasoning spans 5,143–20,837 tokens; four exceed the old
16,384-token cap. Repeated outline drafts occur in completed reasoning, but do
not establish a decoder loop. Unfinished reasoning text is unavailable, so
length alone does not establish repetition or its cause.

Inputs and export metadata bind `Qwen/Qwen3.8-27B` revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`. Its exported generation defaults enable
sampling at `temperature=1.0`, `top_p=0.95`, `top_k=20`; the
[exact pinned model card](https://huggingface.co/Qwen/Qwen3.8-27B/blob/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/README.md#best-practices)
recommends those thinking settings with `presence_penalty=0.0` and
`repetition_penalty=1.0`. The controlled thinking screen and saved thinking-off
baseline instead use greedy decoding; the current driver explicitly selects
`temperature=0`, `top_p=1`, `top_k=-1`. The exact card discusses reducing endless
repetition but does not explicitly prohibit greedy decoding. The
[official older-Qwen3 quickstart](https://qwen.readthedocs.io/en/latest/getting_started/quickstart.html#transformers)
does warn that greedy thinking can degrade performance and cause endless
repetition. This is related-family evidence, not a demonstrated cause of these
unfinished Qwen3.8 generations.

Existing handling marks native context-limit stops as truncated and
automatically assigns zero correctness and coverage. Only the final answer is
graded; reasoning drafts remain evidence artifacts.

**Approved sampler diagnostic — October 15.** The user approves stopping the
five unfinished greedy attempts while preserving all fifteen saved answers,
and a **separate two-note diagnostic on notes 20 and 34**. Its sampler uses
`temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
`presence_penalty=0.0`, `repetition_penalty=1.0`. Weights, original prompts,
`xhigh`, natural EOS within 262,144 context tokens, the 96 GiB CUDA ceiling,
40 GiB cache pool and 20 GiB host-memory watchdog remain fixed. Diagnostic
outputs and receipts remain separate from the fifteen greedy answers; no
saved greedy record is replaced. That initial approval covered only **two
diagnostic generation calls**; the full twenty-note sampled comparison was
not yet approved.

The greedy stop is verified at **14:02:46 UTC**: all fifteen local and remote
saved-answer hashes remain unchanged, the generation unit is inactive, and no
GPU compute process remains. Idle host available RAM returns to **117.9 GiB**.
The stop receipt is retained under
`target/qwen-thinking-20-natural-20261014/generation.stopped-sampler-change.json`.
The separate `qwen-thinking-20-sampled-20261015` generation unit launches at
**14:09:40 UTC**, with its memory watchdog active and independently frozen
source and inputs.

The sampled collection freezes all twenty original note identities with **no
greedy-answer reuse**. The launch selects only `--note-index 20 --note-index 34`
and `--max-num-active-seqs 2`; the configured GPU sequence ceiling remains eight.
Resuming with those selectors validates and skips their saved answers without
generating the other notes. The full `generation.complete.json` marker requires
all twenty answers, so completing this two-note diagnostic does not mark the
full collection complete or authorize the remaining eighteen generations.

**Two-note diagnostic results — October 15.** Both selected notes finish at
natural EOS with `truncated=false`:

| Note | Thought tokens | Final tokens | Total tokens | Subjects | Elapsed generation seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 34 | 7,519 | 761 | 8,281 | 17 | 2,006.68 |
| 20 | 15,221 | 4,444 | 19,666 | 90 | 4,700.15 |

Elapsed times share the generation-session start. The unit exits successfully
with status 0 at approximately **15:30:24 UTC**, about **81 minutes** after
launch; generation takes **78.3 minutes**. There are zero cache preemptions,
GPU reservation reaches **90.48 GiB**, and host available RAM is approximately
23.5 GiB during steady decoding (sampled minimum **23.39 GiB**). After exit,
no GPU compute process remains and idle host availability returns to 117.9 GiB.
Local/remote answer hashes match; native metadata, prompt, policy, runtime,
token/EOS and output-format validation pass. At diagnostic completion, only two
sampled answers existed; eighteen remained pending and no full-collection
completion marker had been written.

Both notes were still unfinished at **159,427 greedy tokens** when the user
approved stopping them. These two sampled completions do not establish
causality, semantic quality or generalization. At diagnostic completion, no
semantic grading had run and the remaining eighteen generations were not yet
authorized.

**Approved twenty-note sampled comparison — October 15.** The user then approves
generating the remaining **eighteen sampled answers**, followed by grading all
twenty with the existing grader. The sampler, `xhigh`, original prompts, weights
and memory limits remain unchanged; model selection remains open.

Generation resumes at **15:49:05 UTC** under the same sampled unit, with frozen
source and inputs unchanged. The note 20 and 34 hashes remain unchanged and
their saved answers are validated and skipped. Concurrent GPU admissions return
to eight, with the fixed **40 GiB** cache, **96 GiB** CUDA and CPU limits, and
active **20 GiB** host-memory watchdog. The separate stdout log is
`generation-remaining-20261015.log`; the local receipt is
`target/qwen-thinking-20-sampled-20261015/remaining-launch.json`.

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
semantic grading was still pending at generation completion.

The separate manual handoff uses native `prepare-distillation-review-trial
--saved-generations GENERATIONS --model-output MODEL --generation-version VERSION`.
It requires the complete frozen cohort and `generation.complete.json`, binds
the actual input, answer and runtime hashes, and derives its collection index
without constructing review data manually. Additional immutable receipts use
`--generation-source`; failed validation publishes no selection directory.

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
thinking compute does not improve mean correctness; model selection remains open.

These exposed validation notes provide a small screen, not unseen-note
accuracy or proof that the full test exceeds 90%. Different generation hardware
and the changed thinking sampler prevent attributing every difference to
thinking alone.
Selecting a family, expanding the screen and the real fine-tune remain open.
Ignored artifacts are retained in
`oracle-mvp-qwen-thinking-gx10/target/qwen-thinking-20-20261014/` and
`gx10:/home/dev/experiments/qwen-thinking-20-20261014/`.

## Historical conditional batched cost reference — October 3

Using prep's **ASv6.48** input/batch shapes, saved historical answer lengths,
**100 validation / 200 final test notes** (proposed), and only the winner's
final comparison:

- **Training:** about **5.6 GPU hours** across all three continuing runs.
- **Baselines and evaluations:** about **22–24.5 GPU hours**, including all
  five checkpoints per student and the winner's final baseline/trained comparison.
- **Total planning allowance:** about **36–40 hours / $51–58** at the prep's
  **$1.4153/hour**, including 1–2 hours extra overhead, 25% headroom and $1
  transfer fees. At an illustrative $1.60/hour, this is **$58–65**.

These historical projections use the former winner-only test scope and brief
generation/one-token decode measurements. They are not a measured full pilot or
a spending cap and **do not price the frozen ASv6.100 pilot or the now-approved
six-version test collection**. Update and validate the context/output/memory
setup and reprice that complete workload before launch.
Teacher labels and local review assume the existing subscription; paid APIs add cost.

The earlier October 3 preparation cost **$3.376**, including its failed attempt; those already-incurred charges are separate.


[Technical details and prerequisites](../../sse_multivector/EXTRACTOR-FINETUNING-PILOT-PLAN.md)
· [Decision record](release-decisions.md#two-separate-model-pilots).
