# TRUE01 — Promising scores; native answers miss valid relationships

TRUE is worth investigating further for category containment. Its native answers accepted no invalid relationship in this small test, but missed several valid ones. More importantly, with the sentence input format, its scores placed every valid relationship above every invalid one. That is useful evidence—not a validated deployment rule.

## What we tested

Ten constructed category families across food, software, economics, political ideas, and interpersonal relationships. Each family had two existing wordings. We tested 20 broader–narrower inclusions, their 20 reversals, 40 related alternatives in both directions, and ten directions of five reviewed equivalent descriptions. Expected answers were frozen before inference.

The question was **does A contain B?**, not “which proposed parent scores higher?” TRUE received B as premise and A as hypothesis. Two fixed formats were tested separately:

- Primary: `premise: This text is about {B}. hypothesis: This text is about {A}.`
- Secondary: `premise: {B} hypothesis: {A}`

Only the descriptions were supplied. No original notes, masks, expected answers, demonstrations, or agent context entered the model. There were 90 decisions per format, but only ten constructed families—not 90 independent examples.

## Native answers

These counts use TRUE’s complete greedy generated `0` or `1` answer, not a tuned numerical cutoff.

| Test | Descriptions in sentences | Bare descriptions |
|---|---:|---:|
| Valid broader–narrower inclusions accepted | 14/20 | 9/20 |
| Valid equivalence directions accepted | 8/10 | 8/10 |
| Invalid directions/alternatives rejected | 60/60 | 60/60 |
| Unresolved output | 0/90 | 0/90 |

The primary format gets 82/90 answers right, but that total conceals eight missed valid relationships. For example, it says No to **Vegetarian meals containing Lentil stew made entirely from plant ingredients**. It also misses the expanded GPL/source-code-permissions relationship and one wording of central-bank rate increases under monetary policy. [All unexpected answers, with complete descriptions and analysis](ERRORS.md).

The sentence wrapper changes eleven answers relative to bare text: eight improve and three worsen. In the primary format, only five of ten families have their forward inclusion accepted in both original wordings. Wording sensitivity remains real.

## The important score result

We also saved the probability of TRUE’s first output token being `1`. This is not cosine, a complete-label probability, or calibrated category confidence.

With descriptions in sentences:

- Lowest score for a valid relationship: **0.144155**. A = “Software whose source code users may inspect, modify, and redistribute”; B = “Software distributed under the GPL.”
- Highest score for an invalid relationship: **0.140235**. A = “Memory performance”; B = “Preventing access to freed memory.”

**Every valid relationship scores above every invalid relationship in this fixed sample.** The narrowest gap is only **0.003920**. A cutoff could separate these observed examples, but selecting it here would fit this same sample. We did not select or apply one, and have not shown that the separation transfers to unseen descriptions.

Bare descriptions do not have that separation: their lowest valid score is 0.048672 and highest invalid score is 0.138809. Seven positive–negative score orderings are reversed. This is a concrete difference between the input formats, not proof that the wrapper solves general category containment.

## What this leaves us with

The native No answers do not justify discarding TRUE’s score. Conversely, zero false containments among these 60 negatives does not establish a reliable graph-construction rule. These are clear constructed categories previously used with other models, not an unseen sample of actual generated HDBSCAN descriptions. The NLI-to-topic-membership adaptation, category ambiguity, equivalence, and larger-graph consistency remain separate limitations.

A justified next test would choose a decision rule using one set of category pairs, freeze it, and test it on a separate unseen set. No neural-model training is needed for that. It was **not** performed in TRUE01. No hierarchy was built or changed.

This is not an apples-to-apples accuracy comparison with HRC03/RSE01: those studies primarily tested forced parent preference, while this one tests individual containment decisions on a smaller selected subset.

[Every decision](DECISIONS.md) · [All unexpected answers](ERRORS.md) · [Frozen plan](../TRUE01-PLAN.md) · [Execution and verification](EXECUTION.md) · [Raw scores and complete inputs](scores.jsonl).
