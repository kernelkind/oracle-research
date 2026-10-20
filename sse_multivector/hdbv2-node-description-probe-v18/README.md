# V18 source-description test

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The comparison completed after the initial quota failures. The added sentence did not demonstrate an improvement: both versions returned Dogs twice; v18 introduced two tea-title failures. Neither prompt is frozen.

The original 24 quota failures remain saved. All 24 comparison calls succeeded on their first attempt in separate runs; no generated answer was retried or selected away.

## Results

| Group | Fresh v16, trials 1 / 2 | V18, trials 1 / 2 | My assessment |
|---|---|---|---|
| Dogs | Dogs / Dogs | Dogs / Dogs | Both versions work; no demonstrated improvement |
| Art | Visual Art / Visual art | Visual art / Visual Art | Both fail the approved rule: art alone does not establish visual art |
| Wine | Wine / Wine | Wine / Wine | Both versions work |
| Coffee preparation | Coffee Preparation / Coffee Preparation | Coffee Bean Preparation / Coffee Bean Preparation | Both supported; no added home restriction |
| Tea | Tea / Tea | Desire for Tea and Urination / Desire for tea and urination | V18 fails: two instances say only that the author wants tea |
| Someone's day | Daily well-being / Casual expressions about well-being and the day | Casual well-being updates / Casual Well-Being Updates | V16 usable; v18 uncertain because How are you today? asks, rather than updates |

My judgments: v16 has 10 accepted and two rejected outputs; v18 has six accepted, four rejected and two uncertain. These are assistant judgments on six reused groups, not user decisions or general accuracy estimates. Every exact answer and all masks are in the comparison (`./main-account/comparison.json`).

For tea, the masks are:

1. ⟦I⟧ ⟦want⟧ ⟦hot tea⟧ ⟦too⟧
2. ⟦I want⟧ ⟦hot tea too⟧
3. ⟦morning⟧ ⟦tea⟧ ⟦wee⟧ ⟦in that order⟧
4. ⟦got me out of bed⟧ ⟦plus the need for tea and a wee⟧

Urination is supported by only the latter two. Adding it to the shared title breaks the every-instance requirement. This does not justify editing those masks during this comparison.

The default review (`./review.json`) shows the one distinct uncertainty, with every mask and my reasoning in a separate comment. Both day trials differ only in capitalization, so that question is shown once; both raw answers remain in the complete review. `run-review-all.sh` shows all 12 v18 titles with the corresponding fresh v16 title available; `run-review-problems.sh` shows the four rejected v18 titles. No user decisions are prefilled.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v18/run-review.sh
```

## Authorized change

V18 adds only this sentence after v16's opening:

> The quoted text comes from social-media posts.

The strict per-instance check is unchanged. So are all source masks, including `dogstr` and `dog` without added hashtag markers. No examples, suggested titles or full-note context were inserted.

V17 was the rejected, unrun proposal to remove the check. It was not tested or added to the registry. V18 is a separate version and remains unfrozen.

## Fixed comparison

Six complete previously used groups: dogs, art, wine, coffee preparation, tea, and comments about someone's day. Each receives two fresh v16 calls and two fresh v18 calls: 24 calls total.

The comparison checks whether identifying the text's source reduces text-format titles while preserving scope. The art, wine and coffee examples also check for unsupported restrictions; success on dogs alone would not establish that the change is safe.

Both versions use gpt-5.6-sol / low and the unchanged isolated wrapper. Each input keeps every mask in its original order, with quoted fragments together inside one numbered instance.

## Initial blocked attempt

Preflight verified exact prompt rendering, the one-sentence insertion, preservation of the check and prior versions, and six complete source packets. Every attempted call failed on attempt 1, before any response item. Raw events identify 24 distinct threads; failed wrapper records leave their top-level thread fields null. Usage was not reported, not measured as zero.

The launcher's queue continued after the first usage-limit errors, so all 24 attempted calls received that same error before the main agent processed completion output. No retries were made. Before resuming, check one call succeeds and stop new submissions if a shared account error recurs.

No account credentials were inspected or changed during that initial attempt; no model switch, purchases, downloads, rentals or new API billing was introduced.

## Completed comparison run

Successful comparison calls used a separate isolated runner directory. The original configurations and failed records remain untouched.

One planned call succeeded before further dispatch. Remaining calls ran in waves of at most three; no retries were needed. All 24 successful calls used distinct threads and empty workspaces, the same pinned Sol-low model and CLI, no tools or response schema, and unchanged prompts and masks. Independent checks found no artifact or isolation mismatch; see verification (`./main-account/verification.json`).

Usage: 44,000 input tokens, including 1,664 cached tokens; 1,034 output tokens, including 859 reasoning tokens. The original failed calls reported no usage. Existing subscription only; no new purchases or API billing.

## Evidence and next action

[run-plan.json](./run-plan.json) and all configs were saved before execution. `./source-packets.json` preserves the complete notes and byte spans for provenance only; full notes were not sent to generation. `./status.json` records the initial failure and each raw event path. The original `v16/` and `v18/` directories preserve those failures. `./main-account/status.json` records completion; its sibling directories preserve every successful raw call and output.

[prompt.txt](./prompt.txt) and [baseline-prompt.txt](./baseline-prompt.txt) preserve the exact templates. [The earlier v16 results](../hdbv2-node-description-probe-v16/README.md) remain intact.

Do not adopt v18 on this evidence. The dog failure did not recur in either fresh condition, so this run cannot show the new sentence fixed it. Tea regressed, and art remained unsupported under both prompts. This small comparison does not isolate why those behaviors occurred. No further prompt edit or experiment was performed during this comparison.

The user subsequently rejected the unrun v19 draft and approved the [v20 comparison](../hdbv2-node-description-probe-v20/README.md). V20 starts from v16 and states the shared-subject task and independent-support requirement in its opening. All 24 new calls completed, but v20 still has art, combined-activity and positivity failures. The v20 review exposes all eight failed outputs across both versions plus one uncertain baseline title. Neither version was frozen; this v18 record and its raw results remain unchanged apart from this follow-up link.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the one-change comparison, not its semantic judgments.

CREC-127 remains the tracking card. Plane tools were not available in this session, so its external status/comment could not be updated.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v18` is selected as `title-studies/hdbv2-node-description-probe-v18` in the [publication catalog](../../docs/experiments/publications.csv), with [exact files and hashes](../../docs/experiments/publication-files.csv). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
