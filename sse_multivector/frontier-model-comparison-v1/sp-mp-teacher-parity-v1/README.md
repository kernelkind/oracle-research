# SP/MP teacher-parity round — MiMo high and Muse high vs saved Astra

Status: prepared; inference runs pending. This is the teacher-selection quality
round for the SP + MP scope (prominence and node titles are other agents'
workstreams). It measures **error-rate parity** against the prompt requirements:
Astra is an arm of the study, not ground truth, and its errors count as errors.

Prompts are frozen and byte-identical across arms: **MPv3.43**
(`../mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md`, SHA-256
`75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03`, frozen
working baseline) and **ASv6.48** (frozen subject baseline; the ten saved
renders are hash-verified against `asv6.48-muse-v1/cases.json`). No prompt
adaptation in this round.

## Design (predeclared in `plan.json`, seed 20260922)

- **Arms:** Astra low (saved outputs only, zero Astra calls), Muse high
  (`meta/muse-spark-1.3-contributor`), MiMo high (`xiaomi/mimo-v2.6-pro`).
- **MP arm:** 60 note–subject pairs — the 18 mpv3.43-probe-v1 pairs including
  the known failure set, plus 42 seeded draws from HRv1 entries at non-dev
  posts stratified 10 empty / 12 single-fragment / 12 multi-fragment /
  8 repeated-fragment. One trial per pair per candidate; a predeclared 15-pair
  subset gets a second trial for within-model variance only (75 mask calls per
  candidate).
- **SP arm:** the ten saved ASv6.48 notes. Astra and Muse-high outputs are
  saved; MiMo high is called once per note (10 calls).
- **Parity rule:** candidate acceptable-rate within 10 points of Astra's, no
  new recurring failure category, format compliance ≈ 100%. With 60 pairs x 1
  trial this resolves gross regressions (roughly 15+ points) and recurring
  failure categories, not small differences.

Mask rubric: acceptable / scope_concern / incorrect / uncertain; error tags
`extra_meaning, missing_meaning, missing_repetition, false_empty,
unjustified_nonempty, wrong_fragment`. SP rubric: acceptable / concern /
incorrect / uncertain; error tags `unsupported_content, missing_context,
attribution_loss, missing_subject, redundant`. Full criteria text is in
`plan.json` and inside every scoring packet.

## Commands

Prepare (offline, refuses to overwrite evidence):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/sp-mp-teacher-parity-v1/study.py prepare
```

New experiments use [the shared experiment workflow](../../model-runner.md#prompt-experiments-one-supported-workflow).
The old saved-batch CLI is retired. Preserve these inputs and receipts as evidence;
import them with an explicit template/input mapping rather than rerunning the baseline.
The preparation/collection scripts below describe this saved study, not a second
supported workflow for new prompt experiments.

Collect (verifies pinned inputs and every saved receipt, decodes masks with
the pinned decoder, extracts usage and cost):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/sp-mp-teacher-parity-v1/study.py collect
```

Build blind scoring packets and the unblinding map:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/sp-mp-teacher-parity-v1/study.py packets
```

Scoring: each scorer reads one packet (`packet-a.json`, `packet-b.json`) and
writes `score-a.json` / `score-b.json` as
`{"scores": [{"slot": "S001", "verdict": "...", "tags": [...]}]}`. Packets are
blind: arm identity lives only in `blind-map.json`, which scorers must not
read. Twenty-four overlap slots are scored by both scorers for consistency.
Scoring is judgment work, separate from collection; no model calls.

Unblind and evaluate the parity rule:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/sp-mp-teacher-parity-v1/study.py report
```

## Limits

- One trial per pair for 45 of 60 pairs; the repeat subset estimates variance
  only. Reused posts (dev set) and one frozen pool limit transfer claims.
- MP pairs carry Astra-phrased subjects; the SP arm covers each model's own
  subject style. Cross-style masking is not tested.
- Blind scoring strips model-supplied diagnostics; verdicts judge masks and
  subject sets only. One scorer per packet with an overlap consistency check
  is not a multi-rater study.
- This round does not compare prominence or resulting hierarchies. Its label
  parity verdict alone cannot select teachers; task 17 also requires an A/B
  comparison of hierarchies built from candidate outputs.

## Findings

Interim, from the completed first scoring pass (packet A: 129 of 234 blind
slots, roughly half the items per arm). Packet B and the parity verdict await
the second scorer; N080/N096 await the background subject retry.

| Acceptable rate (packet-A subset) | Astra low (saved) | Muse high | MiMo high |
| --- | ---: | ---: | ---: |
| MPv3.43 masks | 91.4% (n=35) | 89.5% (n=38) | 87.8% (n=41) |
| ASv6.48 subject sets | 100% (n=4) | 60% (n=5) | 83% (n=6) |

- **Format compliance is 100% for both candidates** (all 150 mask outputs
  decode mechanically). An earlier run of this collection reported massive
  format failures; that was a collector bug (an order-based item/case mapping
  that paired outputs with the wrong posts), fixed in `collect` by binding
  items to cases on (note, subject) identity. Prompts and requests were always
  correct and unchanged. The fix is recorded in `results.json`'s
  `collector_changes`.
- Mask quality is close to Astra on this sample — inside the predeclared
  10-point margin. Error signatures seen: wrong-scope additions (Looking and
  reaching retained for interest-only subjects) and one missed repetition.
  Astra itself fails too (one false-empty-class error among 35).
- SP subject sets show more variance at tiny n: the recurring candidate error
  is a dual reading of `#grownostr` (plain meaning plus an asserted
  "documenting children's growth" reading). Two notes (N080, N096) are
  excluded pending retry.
- Cost captured this round: MiMo high $0.592 (masks $0.334 + subjects $0.258)
  at 4,481 output tokens per mask call (vs 431 in the cost probe — these pairs
  elicit far heavier reasoning); Muse high $0.064 at 3,188 per call. Combined
  with the cost probe: Muse stays ~0.8x Astra; MiMo rises to roughly 1.1-1.5x
  Astra once hard pairs and its transport retries are included.
- **Feasibility finding:** MiMo high dropped 14 of 97 attempts mid-generation
  ("Network connection lost", provider timeouts) and needs >30 minutes for the
  largest subject sets; Muse high completed 75/75 without a failure but its
  subject sets carry the dual-reading concern.

Pending: packet-B scoring and consistency check on the 24-slot overlap, the
N080/N096 retry outcome (a 3600-second attempt is running), and the final
parity-rule verdict.

## Publication files

Selected evidence retains the interim summary, later successful subject-answer receipts, saved masks, scores and blinded review membership. The interim summary counts eight subject answers; native receipts retain ten. No final parity verdict is recorded.

`historical-studies/frontier-sp-mp-teacher-parity-v1` appears in the
[catalog](../../../docs/experiments/publications.csv) and [dataset manifest](../../../docs/experiments/downloads.md#dataset-manifest).
These files are prepared locally for Hugging Face Datasets; downloads are not
available yet. Recorded pre-ASv6.100 derivatives remain deprecated historical evidence.
