# V20 titles: Astra-low versus saved Sol-low

Astra-low produced 11 titles I judge usable and one I judge too narrow. The saved Sol-low run produced seven usable titles and five failures. This is an improvement on six reused groups, not an estimate of general accuracy or a reason to freeze the prompt/model.

## Exact results

Both models received the same unchanged v20 prompt and masks. Sol results are historical; Sol was not rerun.

| Group | Astra trial 1 | Astra trial 2 | Saved Sol trial 1 | Saved Sol trial 2 |
|---|---|---|---|---|
| Dogs | Dogs | Dogs | Dogs | Dogs |
| Art | Art | Art | Visual Art | Visual Art |
| Wine | Wine | Wine | Wine | Wine |
| Coffee | Coffee Bean Preparation | Coffee Bean Preparation | Grinding and Roasting Coffee Beans | Coffee Bean Preparation |
| Tea | Drinking tea | Wanting tea | Tea | Tea |
| Someone's day | How the Day Is Going | How the Day Is Going | Positive Mood Check-Ins | Positive Well-Being Today |

No generated titles were edited. These are assistant judgments, not user approvals.

## Remaining Astra problem

Title: **Wanting tea**, trial 2.

These are all the masks the model saw, one instance per vector:

- V334: ⟦I⟧ ⟦want⟧ ⟦hot tea⟧ ⟦too⟧
- V333: ⟦I want⟧ ⟦hot tea too⟧
- V731: ⟦morning⟧ ⟦tea⟧ ⟦wee⟧ ⟦in that order⟧
- V730: ⟦got me out of bed⟧ ⟦plus the need for tea and a wee⟧

V731 places tea in a morning sequence but does not itself express wanting it. The other instances cannot provide that missing desire under the same independent-support requirement used for Sol. I therefore judge the title too narrow.

“Drinking tea” is defensible as the activity these instances concern; it does not assert that drinking has already occurred. This distinguishes a category of interest from a claim made by every instance. The judgment is about these exact inputs, not an absolute rule that desire can never be implicit.

## What improved

- **Art:** Astra retained the broader scope of the standalone ⟦art⟧ mask instead of narrowing it using the other instances.
- **Coffee:** both Astra titles name the shared activity of preparing coffee beans, rather than listing grinding and roasting as if both were shared.
- **Someone's day:** both Astra titles cover the neutral question and the two favorable day statements without imposing positivity on every instance.

Dogs and wine remained usable. Tea shows a remaining instance-support problem. We cannot conclude that model capacity alone explains every difference: the comparison uses a small development sample and historical Sol calls, and outputs vary between calls. No fixed-title judging diagnostic or additional prompt revision was run.

## Review

[run-review.sh](./run-review.sh) shows all six judged failures: the one new Astra title and all five saved Sol failures. Every item contains the exact masks and a separate assistant comment. Press **B** to see the other model's title from the same trial.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v20-astra-low-v1/run-review.sh
```

[run-review-all.sh](./run-review-all.sh) shows all 24 outputs—12 new Astra titles and 12 saved Sol titles—in a separate session. No user decisions are prefilled.

[comparison.json](./comparison.json) contains every title, judgment, reason, mask, usage count and raw-result path.

## Reproducibility

[run-plan.json](./run-plan.json) and all 12 configs were saved before generation. Only the model field changed from each corresponding Sol config: `gpt-5.6-sol` → `gpt-6-astra`. Reasoning effort stayed `low`; [prompt.txt](./prompt.txt) and [source-packets.json](./source-packets.json) are byte-identical to the [v20 baseline](../hdbv2-node-description-probe-v20/README.md).

One numbered instance represents one vector; its exact fragments are curly-quoted and separated by semicolons. Notes, vector IDs, expected answers, earlier titles and reviewer comments were not sent to the model. Full notes and byte spans remain in source-packets only for provenance.

Generation used the unchanged wrapper, pinned Codex 0.153.0 and authorized dedicated account home. Every call had its own process, thread and temporary empty workspace, with tools, web, skills, repo instructions and user configuration disabled. No conversation was resumed. The first call ran alone, then the remaining calls ran in waves of at most three. All 12 succeeded on their first attempt; no answers were retried or selected away.

New Astra usage: 26,674 input tokens, including 1,920 cached input tokens; 559 output tokens, including 463 reasoning tokens. Cached input did not mean a reused conversation; thread IDs and runtime workspaces were distinct. Existing subscription only; no purchases, rentals or new API billing. Credentials were not read or changed.

[verification.json](./verification.json) records checks of inputs, isolation, raw outputs and the production review tool. All earlier artifacts and user review sessions are preserved.

CREC-127 is the existing tracking card. Plane tools were unavailable, so its external status/comment could not be updated.
