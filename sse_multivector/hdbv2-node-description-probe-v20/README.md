# V20 shared-subject title test

V20 did not establish an improvement. It produced five titles I judge incorrect; the fresh v16 comparison produced three failures and one uncertain title. These judgments concern six reused groups, not general accuracy.

## Results

| Group | V16 trial 1 / trial 2 | V20 trial 1 / trial 2 | Assessment |
|---|---|---|---|
| Dogs | Dogs / Text strings beginning with “dog” | Dogs / Dogs | V16 trial 2 labels spelling, not the subject |
| Art | Visual art / Visual art | Visual Art / Visual Art | All four over-narrow the standalone art mask |
| Wine | Wine / Wine | Wine / Wine | All usable |
| Coffee | Coffee Bean Preparation / Coffee Preparation | Grinding and Roasting Coffee Beans / Coffee Bean Preparation | V20 trial 1 combines separate activities instead of naming their shared subject |
| Tea | Tea / Tea | Tea / Tea | All usable; no urination added |
| Someone's day | Casual expressions about one’s day / Casual well-being and positive-day conversation | Positive Mood Check-Ins / Positive Well-Being Today | Both v20 titles add unsupported positivity; v16 trial 2 is uncertain |

V16: eight accepted, three rejected, one uncertain. V20: seven accepted, five rejected. These are assistant assessments, independently reviewed—not user decisions. No answers were edited, retried or selected away.

The v20 opening explicitly asks for a shared subject, but failures remain:

- Coffee masks say ⟦grind coffee beans⟧; ⟦Rise⟧ ⟦grind coffee beans⟧; and ⟦coffee⟧ ⟦Roasting your own beans⟧. The first candidate combines grinding and roasting. My objection is to combining different activities instead of naming their shared subject, not to the word “and” in every category title.
- Day masks say ⟦How are you today?⟧; ⟦gonna⟧ ⟦great day⟧; and ⟦today's been pretty solid⟧. The neutral question does not establish a positive mood/day.
- Art masks include ⟦Photography⟧, painting-related instances, and standalone ⟦art⟧. We previously agreed that the last instance does not independently support Visual Art.

The baseline day title remains uncertain: it may be an ordinary umbrella for conversation about well-being and one's day, or it may combine topics not independently shared. Its communication wording and the word “and” are not automatically failures.

The [complete comparison](./comparison.json) contains every exact title, all masks, individual reasons and raw-result paths.

## Review

The default review presents **all eight failed outputs from both versions, plus the one uncertain output**. Version and trial appear in each item ID. All masks are shown; assistant reasoning has a separate comment section. B displays the other version's answer from the same trial. No user decisions are prefilled.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v20/run-review.sh
```

[run-review-all.sh](./run-review-all.sh) presents all 24 outputs, including successes, in a separate session.

## What was tested

The user approved [prompt.txt](./prompt.txt), byte-identical to the reviewed v20 draft. Compared with [v16](./baseline-prompt.txt), it rewrites the opening to distinguish shared subject from a group-wide summary and states independent support there, replacing the old membership question. Other wording remains unchanged. The v18 social-media sentence is not included. V19 was rejected and unrun.

The same six complete source groups, mask fragments, duplication and instance order were retained from v18. One numbered instance represents one vector; its quoted fragments are joined with semicolons. Full notes and IDs are retained in [source-packets.json](./source-packets.json) for provenance, not sent to generation. No examples, expected answers or prior titles entered the prompts.

[run-plan.json](./run-plan.json) was saved before generation. Both versions received two fresh Sol-low calls per group. The first call ran alone, then the remaining calls ran in waves of at most three. All 24 succeeded on attempt 1. No additional model calls were made.

Same pinned Codex 0.153.0, unchanged wrapper and dedicated account home. Each call used a fresh isolated process, thread and empty workspace; tools and web were disabled, with no output schema or resumed conversation. [Independent verification](./verification.json) found no input, hash, response or isolation mismatch. Prior runs and review sessions remain untouched.

Usage: 43,784 input tokens; 988 output tokens, including 813 reasoning tokens. No cached input. Existing subscription only; no purchases, rentals or new API billing. Credentials were not accessed or changed.

## Interpretation

Dogs worked in both v20 trials, while the baseline repeated its spelling-based failure once. Tea worked in both versions. Those observations do not prove a reliable gain: art still failed, and v20 introduced combined-activity and positivity problems in these trials.

Do not adopt or freeze v20 on this result. No further prompt revision or experiment was performed. The next action is user review of the concrete judgments, not an automatic additional run.

The [official Sol guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed keeping the comparison controlled; it does not establish a cause for these outputs.

CREC-127 remains the tracking card. Plane tools were unavailable in this session, so its external status/comment could not be updated.
