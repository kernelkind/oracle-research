# ASv6.11 test

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The two reviewed examples improved in this run. The exchange note lost all 12 URL-derived chart subjects while retaining all 12 active instruments. The AeroGarden note now gives direct interpretations of execution rather than “Execution may mean…”, and no longer extracts Prime Day information from the URL.

Full original notes, every subject from both versions, and per-note analysis (`./results.md`)

## What was tested

The same 20 notes and order as the ASv6.10 comparison. The approved [ASv6.11 prompt](../atomic-subject-asv6.11-proposal-v1/ASv6.11.md) ran once per note, using the existing isolated runner, pinned CLI 0.153.0, Sol low. The comparison uses the 20 saved ASv6.10 calls; it does not rerun them. All 20 new calls succeeded on their first attempt.

Only the subject prompt changed. Input text, existing identifier normalization, response schema, model, effort and isolation settings stayed the same. URLs were still present in the supplied text; exclusion was a prompt instruction, not new preprocessing. No generated output was edited.

## What changed in the results

| Note | Saved ASv6.10 | New ASv6.11 |
| --- | --- | --- |
| N18 — exchange listing | 12 chart-page subjects derived from URLs. | No chart-page subjects; all 12 active instruments retained. |
| N03 — AeroGarden | “Execution may mean…” and a URL-derived Prime Day claim. | Direct implementation/business-performance interpretations; no Prime Day claim. |
| N07 — Musical Chairs | Uses a person's name found only in the LinkedIn URL. | Uses “the author”; retains the LinkedIn invitation stated outside the URL. |
| N04/N17 — Satoshi/Venezuela | Supported readings phrased with “may.” | Readings expressed directly. |
| N12 — satoshis | No newly calculated bitcoin conversion. | Still no conversion. |

I found no subject in the new output that depended on information available only inside a URL. That is an assistant assessment of these 153 subjects, not a proven general success rate. ASv6.10 returned 165 subjects; the lower count is not itself evidence of improvement. Broad, nested, overlapping and duplicate subjects remain allowed.

## What still needs attention

N10, subject 30:

> The post is tagged with FIRE, Circle, and artificial intelligence.

N16, subject 4:

> The post is categorized under World.

I would flag both as describing tags or posting categories rather than their meaning. They use text outside URLs, so they are separate from the URL-exclusion fix. These are assistant judgments for review, not new user rejections.

N19, subject 4:

> The discussed Bitcoin dashboard appears to depend on many technical pipelines that must be kept running over time.

The source says “Looks like lots of pipes to keep running over time.” Subject 5 also uses “appears.” This differs from the extractor adding uncertainty to its own interpretation: it repeats uncertainty expressed by the author. Nevertheless, uncertainty is still written inside the subjects, so this has not silently been counted as satisfying the broader no-uncertainty requirement.

N08's slang and N12's non-English phrase remain unresolved. Complete coverage across all 20 notes is not established. Every source and output is preserved in the full report; no canonical subject list or automatic human approval was imposed.

## Review only the three remaining concerns

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
./target/release/sse-mask-review iterate \
  sse_multivector/atomic-subject-asv6.11-test-v1/run \
  target/atomic-subject-asv6.11-test-v1-review-session.json \
  --only 10:30,16:4,19:4
```

Each screen shows one subject and its full original note. Left/right moves between these three items; up/down and Ctrl-D/U scroll; Ctrl-C saves/exits. The user session has no prefilled decisions. A separate temporary session verified loading, scrolling, navigation and safe exit without approving or rejecting anything.

## Verification and limits

Verification (`./verification.json`) checks 20 distinct threads and working directories, no overlap with 58 prior calls, one turn per call, no tool events, exact rendered prompts, raw-output hashes and unedited exports. All 59 protected files were unchanged at generation completion. The later documentation-only follow-up updates in the prior comparison README/status are listed separately by the same verifier. Earlier prompts, generated data, registries and review decisions remain unchanged.

The [pre-generation plan](./plan.json), exact prompt registry, configuration, raw run, assistant analysis (`./assistant-analysis.json`) and runtime observations (`./runtime.json`) are preserved. The read-only verification can be rerun with `PYTHONDONTWRITEBYTECODE=1 python3 sse_multivector/atomic-subject-asv6.11-test-v1/verify.py`.

Usage: 42,628 input tokens, including 5,760 cached; 6,699 output tokens, including 4,536 reasoning tokens. Four sequential batches took 345.586 seconds including a final launcher pause. Host disk pressure rose during the final batch; the launcher was paused, and its last already-exited model call was then collected without launching another. Final memory and I/O pressure readings were zero. Reported launcher memory peaks of 16.3–16.8M do not include separate Codex scopes. No paid API, rental or credential changes.

This is a development test on previously examined notes, with one new call per note and a saved nonconcurrent baseline. It does not establish repeatability or isolate the effects of the two changes. ASv6.8 remains frozen; ASv6.11 is not promoted.

## Follow-up

The user started a [subject-prompt goal](../subject-prompt-goal-v1/README.md). Routine semantic review and prompt iteration are now delegated to the assistant under a fixed validation plan. This test remains the starting evidence; its observations are not overwritten or converted into user decisions.

Selected final answers, recorded assessments and parameters: `historical-studies/atomic-subject-asv6.11-test-v1`. See the [publication catalog](../../docs/experiments/publications.csv) and [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest).
