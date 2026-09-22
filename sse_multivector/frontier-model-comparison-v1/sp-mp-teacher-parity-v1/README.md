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

Inference runs use the canonical saved-batch runner. Launch them from a plain
namespace (`systemd-run --user`, see the credential-service sandbox blocker
recorded in `mpv3.43-cost-probe-v1/README.md`); the routing is unchanged:

```bash
systemd-run --user --pipe --wait --collect -E HOME=/home/dev -E PATH=/etc/profiles/per-user/dev/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/bin:/bin /run/current-system/sw/bin/bash -c 'cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && python3 sse_multivector/extraction_pipeline.py masks sse_multivector/frontier-model-comparison-v1/sp-mp-teacher-parity-v1/config-mimo-high-mp-t1.json --repeat'
```

(the same with `config-muse-high-mp-t1.json`, `config-mimo-high-sp.json`, and
the `*-t2.json` repeat batches afterwards.)

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

## Findings

Pending the runs and scoring.
