# Pair-consolidation-owl-v6: consumer and purpose check

The user authorized testing [v6](pair-consolidation-owl-v6.md) on the same
human-food comparison in both orders. This record fixes the checks before
inference. It does not authorize further prompt edits or hierarchy activation.

## Fixed inputs and assessment

Use the saved v5 pilot's `11-consumer-boundary` and reversal's
`11-consumer-boundary-reversed`, prepared with native `prepare --from` and only
the prompt replaced. They are authored synthetic controls, not original-post
hierarchy evidence or independently validated human gold. Model and reasoning
remain GPT-6.1 Sol medium on the subscription route; no caching warmup or paid
fallback is added.

Human food's fixed meaning is "Substances intended to be eaten or drunk by
people for nourishment." Evening meals' fixed meaning is "Meals served in the
evening." Neither input has a supplied parent. The reversal changes only their
order. Expected checks remain outside the model input:

- Each restriction in the human-food meaning must appear in the formal
  expression or a supporting formal class: intended consumption, human consumer
  and nourishment purpose. The eating-or-drinking alternative must likewise be
  represented formally. A composite name whose conditions exist only in an
  English glossary does not satisfy the new rule.
- Evening meals must retain the served-in-evening condition without borrowing
  the human-food consumer or purpose restriction.
- Check the requested JSON layout, resolved vocabulary and unchanged reused
  definitions separately from semantic assessment. Allow different names and
  equivalent formal decompositions; do not require one exact expression.
- Review translation fidelity, coverage of both translations, and agreement
  between consolidated logic and natural-language meaning separately. No
  machine-reasoner proof or unique consolidated heading is claimed.

Use the saved v5 answers as baselines without rerunning them. Native attributed
agent reviews and accounting remain separate from user decisions. Completed
plans, source bindings and receipts remain in the isolated experiment worktree;
all generated data stays under ignored `target/`.

## Completed findings — 2026-10-13

Both native requests completed with one fresh attempt each, on GPT-6.1 Sol
medium. Inputs match their saved v5 baselines exactly; only the prompt is
replaced. The calls used fresh single-user-message contexts, without a prior
response reference or earlier model output in their inputs. They ran through
the shared queue concurrently; neither warmed a cache or reused an answer.

| Check under agent review | Human food first | Human food second |
|---|---|---|
| JSON layout, vocabulary and reused definitions | Pass | Pass |
| Human consumer formally represented | Pass | Pass |
| Nourishment purpose formally represented | Pass | Pass |
| Eating-or-drinking alternative formally represented | **Fail** | Pass |
| Evening meals avoid human-food consumer/purpose transfer | Pass | Pass |

The forward translation uses `intendedConsumer SOME Person` and `hasPurpose
SOME Nourishment` inside intended consumption. However, `EatingOrDrinking` has
no supporting formal definition. Its glossary reads "An activity of ingesting
something by eating or drinking, including a planned activity." The explicit
alternative remains solely in English, violating the new v6 rule.

The reversed human-food translation is:

```text
Substance AND (intendedToBeConsumedIn SOME ((Eating OR Drinking) AND (performedBy SOME Person) AND (hasPurpose SOME Nourishment)))
```

It exposes the consumption alternative, consumer and purpose formally. This
corrects the representation problem in the one reversed v5 witness, whose
`HumanNourishingConsumption` primitive had carried those conditions only in
English. One sample per orientation does not establish a reliable wording effect.

Native attributed reviews record one agent reject for formal-rule noncompliance
and one qualified agent accept. No human judgments are assigned. Manual review
finds both consolidations cover their returned translations, with matching
English scope. It does not establish complete translation fidelity or provide
machine-reasoner verification. Meal interpretation differs: the forward answer
admits food and meal occasions; the reversed answer defines Meal through a
food/drink portion intended for consumption. That remains a lexical qualification,
not a separately established semantic failure.

This is a partial fix: the consumer and purpose conditions are formal in both
answers, but the full restriction-and-alternative rule is not followed in both.
The proposed next revision should make the alternative instruction operational:
use `OR` for stated alternatives, including within supporting class definitions;
a combined name with only an English glossary does not expose an alternative.
No v7 prompt, additional calls or hierarchy activation is included in this check.

## Native accounting and evidence

The native `experiment-usage-summary-v3` report is complete, with no accounting
warnings or missing usage. It reports two fresh attempts, zero provider failures,
retries, reuses or warmups, 6,202 input tokens and 2,301 output tokens. The 1,320
reasoning tokens are already included in output. Cached input and reported cache
writes are both zero. Saved API-equivalent cost is **$0.035414**; it is a catalogue
estimate, not a subscription invoice. Old v5 answers were not rerun or charged
to this test's fresh generation accounting.

The retained task worktree is:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v6-consumer-v1
```

Frozen plans and receipt validation require that worktree and the earlier v5
pilot worktree's original input bindings. Ignored native evidence is:

- `target/pair-consolidation-owl-v6-consumer-forward-v1`
- `target/pair-consolidation-owl-v6-consumer-reversed-v1`
- `target/pair-consolidation-owl-v6-consumer-checks-v1.json`
- `target/pair-consolidation-owl-v6-consumer-usage-source-v1.json`
- `target/pair-consolidation-owl-v6-consumer-usage-summary-v1.json`

Prompt v6, both original inputs and all earlier receipts remain unchanged.
