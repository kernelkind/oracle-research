# MPv3.43 mask-call cost probe — MiMo high and Muse high

Status: completed 2026-09-22 UTC. This is the cost/caching probe for
teacher selection (SP + MP scope), not a quality comparison. It measured
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

Sixteen fresh calls completed (eight per candidate); every successful
receipt passes `validate_prompt_receipt`. Two earlier launch attempts per
candidate failed locally with zero HTTP attempts and zero usage during the
credential-sandbox outage described below; those receipts are preserved and
bound to the validated requests by request identity.

| Captured per mask call | MiMo V2.6 Pro high | Muse Spark 1.3 Contributor high |
| --- | --- | --- |
| Cost (provider-reported) | $0.00030–0.00143 (avg **$0.00070**) | $0.00039–0.00073 (avg **$0.00048**) |
| Input tokens | 2,202 cold; 23–27 warm | 2,055–2,058 every call |
| Cache-read tokens | 2,176 on 6 of 7 warm calls (one mid-batch miss) | none (route reports no caching) |
| Cache-read share of input | **74.2%** | 0% |
| Output incl. reasoning | 184–1,323 (avg 511; 3,452 of 4,086 are reasoning) | 924–2,604 (avg 1,372; 10,164 of 10,973 are reasoning) |
| Wall time per call | 6.9–37.3 s | 13.6–37.3 s |
| Total, 8 calls | $0.005580 | $0.003840 |

The two open questions are answered: **MiMo's prefix caching engages at the
mask-batch shape** (cache-read priced at $0.0036/M in the receipts), and
MiMo-high reasoning on mask calls is moderate (~430 tokens/call) while
Muse-high reasoning is heavy (~1,270 tokens/call).

Scale implication, per 1,000 notes (9,820 mask calls plus 1,000 subject
calls at Astra's measured volume shape): Astra ≈ $7.2 with its measured
62.6% caching; **MiMo high ≈ $8–9.5** (≈1.3× Astra, approaching parity if
cache misses are rarer at scale); **Muse high ≈ $5.8–6.4** (≈0.8× Astra).
Mask-call costs are measured; candidate subject-call costs remain
extrapolated from the saved ASv6.48 subject runs.

## Launch-context note

Before the successful pass, launches failed at `agent-account exec pi`'s
nested Bubblewrap overlay (`Can't bind mount … models.json`) with zero HTTP
attempts and zero usage: inside any Pi credential view that path is already
a read-only bind of an unlinked temp file, and the per-launch overlay
cannot mount over it. The batches completed when launched from a plain
namespace via `systemd-run --user`, with the same runner and the same
credential-service routing. The preserved failure receipts remain in the
run directories.
