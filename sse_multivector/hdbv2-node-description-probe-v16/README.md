# V16 node-title test

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

Three of the four previously failed groups now have usable titles in both trials. The dog group still receives a title about strings. The user accepted the only uncertain title, “Temporal deceleration.” No focused review questions remain. V16 remains unfrozen.

## Results

| Group | Saved v15 title | V16 trial 1 | V16 trial 2 | Initial assistant assessment |
|---|---|---|---|---|
| S0eafedb82e | Two numbered Recipes answers | Carrot Recipes | Recipes Containing Carrots | Both usable; one title per group |
| S18bc272886 | Strings prefixed with “dog” | Strings beginning with “dog” | Strings Beginning with “dog” | Both repeat the wording-based failure |
| S78e7660d1d | Tea-related statements | Tea | Desire for Tea | Both usable |
| S83f6ab41f0 | Everyday English expressions | Casual conversation about one’s day | Current Well-Being and Positive Day Assessments | Both usable; second is wordier |
| S07d0857008 | Successful recipe results | Recipes and Cooking Results | Recipes and Cooking Experiences | Both usable |
| S6621c8eaa9 | Rate reduction | Reduced temporal urgency | Temporal deceleration | Trial 2 uncertain |
| Sa6996b199f | Foods with “cheese” in the name | Cheese-Based Foods | Cheese-Based Foods | Both usable |
| S7dd75e5388 | Brisket smoking | Smoking brisket | Smoking brisket | Both usable |
| S6088798e3d | Daily greetings | Greetings by Time of Day | Daytime greetings | Both usable |

All 18 responses contain one unnumbered title. My initial judgments were 15 accepted, two rejected and one uncertain, not an accuracy estimate. The uncertain title is now explicitly user-approved; the other judgments remain assistant assessments. Both raw trials remain saved; no best-of selection or output repair occurred.

The dog masks are ⟦dogstr⟧ and ⟦dog⟧. Neither discusses strings or prefixes. V16 therefore has not eliminated the failure the user confirmed.

For the initially uncertain title, the masks are ⟦Find a way to slow things down⟧ and ⟦Lower⟧ ⟦time preference⟧. My concern was that “Temporal deceleration” might suggest time itself slowing down, rather than less urgency or willingness to wait for future benefits. The user accepted the title; that concern is retained as the original assessment, not an outstanding objection. The earlier approval of “Rate reduction” also remains intact.

## Review

The user approved `S6621c8eaa9-trial-2`, “Temporal deceleration,” with an empty TUI comment and confirmed in chat: “ehh ig it's fine.” The saved session is `target/hdbv2-node-description-v16-review-session.json`, SHA256 `d406c46e3ca45e5faedcbc6f6c675b2ff477ec5c3f3f6e3f9da55b7ae36b1998`. It contains exactly that one approval; its batch hash matches the unchanged review. This does not approve either dog output or freeze the prompt.

The default review now reopens this accepted title, with all masks and the original assistant concern in a separate comment. No further review is required for it.

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-description-probe-v16/run-review.sh
```

`run-review-problems.sh` shows both dog responses. `run-review-all.sh` shows all 18 responses. Each has a separate session. B shows the exact saved v15 answer. No decisions were prefilled; the focused session now contains the user's actual approval.

I read every mask and response. Before user review, an independent semantic review agreed on both dog failures and the uncertain time title, but also questioned “Casual conversation about one’s day.” I accept that title because it describes the communication about someone's day, rather than merely classifying English expressions. The initial disagreement is preserved in `./assessment-audit.json`, not concealed as unanimous agreement. The subsequent user approval is recorded above without rewriting those earlier assessments.

## What changed

Only the approved prompt changed from v15: distinguish the communicated subject from wording or format, and return one unnumbered title for the entire group. [prompt.txt](./prompt.txt) is byte-identical to the reviewed proposal. The registry adds v16 without changing v1–v15 or the frozen version, v1.

The four failures were confirmed by the user in chat, not saved reject clicks. The five controls were previously accepted. We did not reopen those earlier approvals or demand their exact titles recur.

## Fixed inputs and execution

- Nine complete groups, 29 instances, two calls per group. Source membership, fragments, duplicate masks and order match the original HDBv2 artifact and saved v15 inputs.
- One numbered instance per vector; its exact fragments remain quoted and joined with semicolons. No full notes, IDs, earlier titles, comments, expected answers or examples enter the generation prompt.
- Same gpt-5.6-sol / low, pinned Codex 0.153.0 and unchanged wrapper. Eighteen fresh processes, threads and empty workspaces; all completed on attempt 1. The launcher capped concurrency at three; manifests alone cannot independently reconstruct peak concurrency.
- Same minimal runner instruction and service context; tools/web disabled, no response schema or resumed conversations.
- Usage: 32,792 input tokens, including 6,656 cached input tokens; 1,680 output tokens, including 1,509 reasoning tokens. Four calls reported provider prefix caching, not conversation or response reuse.
- Existing subscription only; no new API billing, credential changes, model downloads or rentals.

Independent provenance checks passed for exact prompts, all masks and byte spans, settings, distinct threads/workspaces, response hashes and preservation of earlier versions. Focused and full reviews were smoke-tested using temporary sessions without approve/reject decisions.

## Interpretation and evidence

This is a same-case development retest against historical v15 outputs, not a concurrent v15 comparison or an unseen-data test. Two trials give limited repetition evidence; they do not establish causality, general reliability or justify freezing v16.

[run-plan.json](./run-plan.json) was saved before generation. `./comparison.json` preserves every response, complete masks, historical baseline and main assessment. `./source-packets.json` retains full notes and byte spans for provenance only. Each `trial-{1,2}/<group>/run/` retains the raw call, output, usage and hashes. `./verification.json` records integrity and packaging checks.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the targeted edit and controlled retest, not the semantic judgments.

The [complete v15 artifact](../hdbv2-node-titles-v15/README.md) remains unchanged as generation evidence. V16 is not frozen or installed as the complete 61-group title set. The time-title review is resolved.

The user then approved a [hashtag-input diagnostic](../hdbv2-node-description-v16-hashtag-diagnostic-v1/README.md) on the dog group, keeping v16 and Sol-low fixed. Three fresh original-input calls produced one “Dogs” and two string-based titles; restoring the original `#` markers produced “Dogs” three times. This supports omitted hashtag context as a contributor for this group, not a general fix or a reason to overwrite the earlier failures. Canonical masks, prior outputs, prompt and freeze state remain unchanged. Any permanent input change or broader test remains a separate decision.

The user rejected both hashtag-specific preprocessing and the unrun v17 proposal to remove the per-instance check. The subsequently authorized [v18 test](../hdbv2-node-description-probe-v18/README.md) keeps that check and every mask unchanged, adding only that the quoted text comes from social-media posts. After 24 initial quota failures, all 24 fresh comparison calls succeeded. Both versions returned Dogs twice; v18 introduced two unsupported tea-and-urination titles, and both versions produced Visual Art where the strict criterion supports only Art. The added sentence has no demonstrated benefit in this comparison. Previous results and failures remain preserved; neither prompt is frozen.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v16` is selected as `title-studies/hdbv2-node-description-probe-v16` in the [publication catalog](../../docs/experiments/publications.csv), with [exact files and hashes](../../docs/experiments/publication-files.csv). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
