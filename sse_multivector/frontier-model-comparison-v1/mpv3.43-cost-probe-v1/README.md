# MPv3.43 mask-call cost probe — MiMo high and Muse high

Status: prepared; inference runs pending. This is the cost/caching probe for
teacher selection (SP + MP scope), not a quality comparison. It measures
per-call usage, prefix-cache engagement and provider-reported cost at the
production mask-batch shape so the teacher-cost estimate can replace its
assumption bands with captured numbers.

Prompt under test: **MPv3.43** (`../mask-prompt-goal-v1/mpv3.43-draft-v1/mask-prompt.md`,
SHA-256 `75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03`),
status: frozen working baseline (not a production rollout). The prompt is
unchanged and byte-identical across both candidates and to production
rendering (production mask batch path, `word_positions`, shared MPv3.34 output
schema). Candidates: `xiaomi/mimo-v2.6-pro` at reasoning `high` and
`meta/muse-spark-1.3-contributor` at reasoning `high`, via OpenRouter.

Inputs: the complete saved ASv6.48 subject set (eight subjects) of one HRv1
note, N029 (hashtag post, 301 characters), from
`../hierarchy-refresh-v1/subjects.json`. Eight fresh mask calls per candidate,
sequential at `concurrency` 1 so the shared prompt-plus-post prefix is sent
before each varying subject, timeout 1800 seconds, no output-token cap, fresh
sends explicitly requested with `--repeat`. The saved Astra MPv3.43 masks in
`../hierarchy-refresh-v1/masked-posts.json` are reference evidence only: this
probe makes **no Astra calls** and no semantic quality claims.

Prepare (offline, refuses to overwrite evidence):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/mpv3.43-cost-probe-v1/study.py prepare
```

Run one candidate's eight saved-batch calls:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/extraction_pipeline.py masks \
  sse_multivector/frontier-model-comparison-v1/mpv3.43-cost-probe-v1/config-mimo-high.json \
  --repeat
```

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/extraction_pipeline.py masks \
  sse_multivector/frontier-model-comparison-v1/mpv3.43-cost-probe-v1/config-muse-high.json \
  --repeat
```

Collect (verifies pinned inputs and every saved receipt, decodes masks with
the pinned `mask_positions.py` decoder, and extracts usage, cache and cost):

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
python3 sse_multivector/frontier-model-comparison-v1/mpv3.43-cost-probe-v1/study.py collect
```

## Limits of this probe

- One short note (301 characters): per-call input is below the measured
  2,472-token Astra mask-call average, so absolute per-call costs understate
  typical calls. Cache fractions and reasoning output per call are the findings
  that transfer.
- Sequential calls at concurrency 1 are the best-case cache shape. Production
  mask batches ran with up to 12 workers; their cache-hit rate can be lower.
  The Astra comparison figure (62.6% of mask input cached) was measured under
  those production conditions.
- One answer per subject; no reliability or quality claims. Mask outputs are
  decoded only for mechanical validity.

## Findings

Pending the runs. Recorded per candidate: captured cost per call and per
mask-call input/output split, `cacheRead` engagement across the eight
same-prefix calls, and reasoning-token share of output.
