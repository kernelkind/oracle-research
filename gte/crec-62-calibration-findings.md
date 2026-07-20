# CREC-62 GTE calibration findings

## Purpose

This records what the first paid production calibration established, what went
wrong operationally, and what remains unknown. Future runs should use this as
the factual baseline instead of reconstructing the result from chat history.

The run artifacts are under:

`../damus_snapshot/runs/crec-62-gte-calibration`

## Conclusion

The exact full-quality GTE representation is comfortably affordable. The
original post-calibration projection was **$39.21 total**, but it used a `$1`
artifact allowance and a provisional live charge. The final CREC-72 launch
audit replaced those assumptions with the finalized provider invoice and a
conservative `$10` non-worker allowance. The current complete-build projection
is **$48.27 lifetime total**. Compute cost is therefore not a reason to reduce
model quality, vector dimensions, or numeric precision for the Oracle MVP.

This run established computational and operational feasibility only. It did
not test semantic-neighbor quality, personalization, or recommendation quality.

## Exact configuration

- Model: `Alibaba-NLP/gte-Qwen2-7B-instruct`
- Revision: `a8d08b36ada9cacfe34c4d6f80957772a025daf2`
- Execution: deterministic IEEE FP32 with eager attention
- Output: one finite, L2-normalized, 3,584-dimensional FP32 vector per note
- Batch size: 32 notes
- Output shard size: 16,384 notes
- Container image:
  `docker.io/kernelkind/oracle-mvp@sha256:96a60fd4caf87afadf0546636af6eeefee72d327dc95dde1714f86ea14fb435a`
- PyTorch: 2.12.1
- Transformers: 4.41.2
- CUDA: 13.0.2
- GPU: one NVIDIA RTX PRO 6000 Blackwell Workstation Edition, about 96 GB VRAM
- GPU power limit: 600 W
- Host: AMD Ryzen 9 9950X, about 202 GB RAM, 200 GB local NVMe
- Vast offer: `45236567`, Texas, US
- Rental instance: `[private ID removed]`
- Raw total rental rate: $1.359259259.../hour
- Conservative identity and future-offer gate: $1.359260/hour

This was embedding inference, not model training or fine-tuning.

## Measured production shard

The worker completed production shard 157 and exited successfully.

- Notes: 16,384
- Batches: 512
- Effective tokens: 1,381,640
- Padded tokens: 1,389,888
- Padding overhead: about 0.6%
- Batch execution time: 397.734 seconds
- Model cold start: 21.132 seconds
- Shard setup: 0.004 seconds
- Checkpoint publication: 0.116 seconds
- Finalization: 1.726 seconds
- Complete measured pipeline: 420.711 seconds

Batch-only throughput was 41.19 notes/second and 3,473.78 effective
tokens/second. Including startup and finalization, throughput was 38.94
notes/second and 3,284 effective tokens/second.

Batch latency depended strongly on token length:

- Minimum: 0.087 seconds
- Median: 0.598 seconds
- 95th percentile: 2.21 seconds
- Maximum: 4.678 seconds

Every planned token-length range through 513 model tokens ran successfully at
batch size 32. There was no OOM, CUDA failure, invalid shape, non-finite value,
or normalization failure. The longest range contained only two measured
batches, so its evidence is valid but relatively sparse.

Length-sorted batching was effective. Padding overhead was about 0.6% in both
the calibration shard and the complete plan.

## Artifact result

The shard contains 234,881,024 bytes of vectors: 14,336 bytes for every
3,584-value FP32 vector. It is a valid, reusable part of the final
representation and must not be recomputed merely because it originated in the
calibration.

- Representation build identity:
  `9531c232e7ad8e3c18e46f5d51aba5102930ff879639fe6bdfd12691cd73a21e`
- Vector shard SHA-256:
  `9dbc6eeadc4446ee3d135bbece07765d2c67a163afef6025826b1f9300c4dd49`
- Calibration evidence SHA-256:
  `e4e1dcb0917751da70a8f56055502cc5226cbf9be5128b7b775f29e86e38a4f3`

The representation manifest intentionally remains incomplete with 16,384
completed rows. A later build can add the remaining shards under the same build
identity.

## Complete-corpus facts

The frozen semantic corpus contains:

- 3,530,455 eligible notes
- 301,902,943 effective tokens
- 303,651,600 padded tokens
- 110,327 planned batches
- 216 output shards

The complete vector matrix will be exactly 50,612,602,880 bytes, or about
50.61 GB / 47.14 GiB. The event-ID index and ordered-ID file add about 240 MB.
The model is about 30.46 GB and the corpus database is about 3.92 GB. A 200 GB
rental disk should therefore have ample capacity, although the complete build
did not directly exercise that final disk footprint.

This build produces one vector per note. It does not precompute a note-to-note
graph; similarity remains lazy.

## Projection method

The full-build estimate is deliberately not `one shard time × shard count`.
The projector:

1. Separates the exact complete batch plan into 16 token-length ranges.
2. Uses the slowest measured production batch in each range.
3. Charges every remaining planned batch in that range at that maximum time.
4. Adds all remaining shard setup and checkpoint work.
5. Extrapolates full-corpus finalization.
6. Adds another model startup and reserves for one restart and one lost shard.

Projected remaining time:

- Batch work: about 96,718 seconds
- Remaining shard setup: about 1 second
- Remaining checkpoints: about 25 seconds
- Full finalization: about 372 seconds
- New model startup: about 21 seconds
- Total: about 97,137 seconds, or 26.98 hours

Because every future batch is charged at the maximum observed time in its
range, this is an upper-biased estimate rather than an expected average. It
still cannot predict multi-hour provider instability or thermal throttling.

## Cost result

The measured resource-cost estimate was:

- Provider runtime snapshot: about $0.924
- Provider transfer charge: about $0.272
- Conservative resource charge: $1.205996

The final provider-reported resource cost was `$1.262`.

`launch/finalized-charge-reconciliation-result.json` and
`launch/current-full-build-projection.json` are authoritative.
`launch/provisional-artifacts-superseded.json` identifies the older provisional
settlement and projection artifacts retained only as audit history.


The original additional projection was `$37.998327`; its `$1` artifact
allowance is superseded. The current CREC-72 projection is:

- Remaining compute: $36.676185
- Artifact storage, transfer, preparation, and teardown allowance: $10.00
- One cold-restart reserve: $0.148419
- One lost-shard reserve: $0.173723
- Additional total: $46.998327
- Projected total including finalized calibration: **$48.27**

The `$10` allowance bounds the exact image, compressed transport, direct model
download, complete 50.61 GB result retrieval, storage, preparation, and
teardown at the admitted network-price ceilings. It is a reservation, not a
spending target.

## Operational findings

### Input staging dominated the calibration

The instance existed for about 41 minutes, while the measured embedding
pipeline occupied about seven minutes. Only about $0.16 of rental time
corresponded to that pipeline. Setup, transfer, verification, and live debugging
dominated the small run.

Uploading the complete 34.65 GB package directly was not viable. The first
transfer ran at roughly 2.5 MB/s and disconnected after about 136 MB.

The successful recovery was:

1. Download the exact pinned model directly on the rental.
2. Verify its payload against the model lock.
3. Compress the 3.92 GB NostrDB locally to about 1.93 GB.
4. Upload the compressed database and small supporting artifacts.
5. Replace the remote database atomically.
6. Verify the reconstructed package against the original manifest.

The compressed database upload took about 13 minutes at roughly 2.3 MB/s.
Retrieving about 362 MB of results took about 13 seconds at roughly 25.7 MB/s.
Input staging, not result retrieval, was the operational bottleneck.

CREC-72 now makes this exact transfer and reconstruction path explicit and
locally verifies the package and transport manifests before launch.

### Model cache metadata is not stable identity

A fresh download at the same pinned model revision changed 25 files, all under
`.huggingface/download/*.metadata`. Every actual model payload remained
identical. Cache-download metadata should not determine model identity; future
packaging should bind the real model payload and required configuration.

### Vast offer lookup is volatile

Qualifying offers disappeared and reappeared during selection. Vast CLI's
provider-side exact `id=` filtering also returned no row for an offer that was
still present in the full constrained query.

Future launches must refresh the identical constrained offer list immediately
before launch, select the approved ID locally, and require it to appear exactly
once. Commit `ea9c29f` implements this rule.

### Direct-launch instance records may omit `bundle_id`

The selected offer contained a bundle ID, but the live direct-launched instance
reported `null`. The original identity gate rejected that provider omission.
Commit `13ea4c4` accepts only the omission while continuing to reject every
non-null mismatch.

The immutable image used for embedding predates that fix. Rebuilding it would
change the image digest, which is part of the representation identity, and
would make shard 157 unusable in the complete build. The complete build must
therefore keep the calibrated image unchanged and checksum-pin the corrected
identity helper and full-build controller separately.

### Destruction must be confirmed from live state

Vast returned an empty destroy result even though destruction succeeded. The
reliable proof was that instance `[private ID removed]` disappeared from the provider's
live instance list. Future teardown must check absence rather than trusting the
destroy response body.

### The safety and audit path worked

- The private immutable image launched successfully without a Vast template.
- The exact model, corpus, batch plan, execution identity, vector shard, and
  evidence remained cryptographically bound.
- The one-shot worker claimed the existing reservation exactly once.
- Preparation and calibration exited successfully.
- Retrieved checksums passed.
- The instance was destroyed and independently confirmed absent.
- Ephemeral SSH material and the temporary transport archive were removed.
- Commit `b031209` recorded the settlement; 46 targeted budget tests passed.

### CREC-72 closed the partial-artifact API gap

A later free local smoke test used the exact frozen controller, image, GTE
model, corpus, and calibrated shard on a disposable copy. `vectors_for_notes`
returned the exact stored 3,584-dimensional vector. `similar_notes` performed a
real query-role encoding, scanned the 16,384 represented rows once, excluded
the source, and returned five ranked candidates. The source artifact was not
modified.

This proves both production operations behave correctly on the calibrated
shard. It does not estimate complete-matrix latency or recommendation quality.
The exact event IDs, scores, timings, and artifact identities are recorded in
`../damus_snapshot/runs/crec-72-gte-full-build/preflight/report.json`.

## What remains unknown

This calibration did not test:

- Whether GTE retrieves high-quality semantic neighbors.
- Whether its geometry preserves distinctions such as technical depth,
  usefulness, stance, style, originality, or humor.
- Whether private positive and negative evidence can become accurate personal
  recommendations over this geometry.
- Complete-matrix `similar_notes` latency. A free CREC-72 smoke test proved
  query-role encoding, exact scan, source exclusion, and ranked output over the
  calibrated shard only.
- Local personalization, adaptive learning, feed construction, or final ratings.
- GTE quality relative to another embedding model.
- Stability, restart/resume behavior, and exact cost across a continuous
  approximately 27-hour build.
- Peak VRAM, utilization, temperature, actual power draw, or batch-size
  headroom. No such telemetry was retained.

Only one of 216 shards ran. The calibration validates the exact production path
and gives a conservative cost estimate; it does not prove full-run stability or
recommendation quality.

## Implications for future runs

- Do not add FP16, quantization, dimensionality reduction, model downgrades, or
  GPU comparison work merely to satisfy the budget. The exact FP32 build already
  fits comfortably.
- Preserve and reuse shard 157.
- Keep the calibrated private image unchanged and transport the corrected,
  checksum-pinned identity helper and controller separately.
- Replace the naïve complete-package upload with the verified remote-model plus
  compressed-corpus staging path.
- Bind model identity to stable payloads rather than Hugging Face cache metadata.
- Refresh and validate the complete constrained offer list immediately before
  launch.
- Recalculate transfer allowance from the selected offer before authorizing the
  full build.
- Confirm destruction by querying live instance state.
- Treat recommendation quality as the next fundamental uncertainty. More cost
  optimization cannot answer it.
