# ASv6.50

Status: approved candidate, tested on GPT-6.1 Sol xhigh. Two of twelve answers
contain the parent-scope failure pattern. On
October 1, 2026, the user approved the full-context delta and authorized this
test. This supersedes the ASv6.49 draft. ASv6.48 remains the frozen subject
baseline. MPv3.43 remains the frozen mask working baseline. Adoption as the
subject baseline remains open.

The subsequent [ASv6.51 (approved candidate, tested on Sol xhigh)](../asv6.51/ASv6.51.md)
is now the last approved subject prompt. ASv6.50 and its saved answers remain
comparison evidence.

[ASv6.54 (draft, untested on models)](../asv6.54/ASv6.54.md) is the current
example-only revision for review. It replaces the overloaded railway example
with focused cases and covers the gaps found after ASv6.53's placement correction.
Its wording and model test remain open. The
[rule-to-case map](#example-correctness-and-rule-coverage) records each case's
instruction basis; the [draft audit](#asv654-focused-examples) records verification.

[ASv6.50.md](ASv6.50.md) replaces the existing hierarchy paragraph in
[ASv6.48](../asv6.48/ASv6.48.md). It makes the relationship explicit using the
`subject` headings: every post about the child subject must also be about the
parent. The existing requirements to retain every enumerated subject, combine
shared headings and include a subject in each applicable branch remain.

ASv6.48 already required refinement, broad-to-specific ordering and independently
understandable headings. ASv6.49 added a paragraph that substantially repeated
those instructions. ASv6.50 clarifies the existing paragraph without adding
another rule paragraph. All other instructions and both worked examples remain
byte-identical to ASv6.48.

The shared `experiment.py revise` command generated the draft and revision
receipt directly against ASv6.48 SHA-256
`e1d5740e68b5f5c29e139ad3fbb37839f91784784aaa31b3bdbdc4a829a4bacc`.
The ASv6.50 SHA-256 is
`2ab157eb34f49edd2a443799c439be8eff512fe61df96f6d508434f4d3807a1c`.
No model calls were made while preparing this draft. Mechanical checks do not
establish semantic improvement.

The [agreed regression set](../asv6.49/README.md#agreed-regression-set) remains
N063, N074, N096 and N100, using complete original posts and saved ASv6.48
outputs. The authorized comparison uses three independent candidate outputs
per post on GPT-6.1 Sol xhigh, reviewing complete hierarchies for preserved
coverage and new errors. Its setup and results are recorded below.

## Frozen-baseline reproduction on GPT-6.1 Sol xhigh

On October 1, 2026, the user authorized testing unchanged, frozen ASv6.48 on
the four regression posts with GPT-6.1 Sol xhigh before testing this draft.
The [reusable experiment spec](../../experiment_specs/sol61-xhigh-sp-scope-regression-v1.json)
uses the shared `subjects` adapter and the complete original posts. Each
rendered prompt's SHA-256 matches its original Astra-low request. The run used
the subscription WebSocket route, four concurrent requests, a 1,800-second
deadline, no output cap, no paid fallback and `--repeat` to prevent request reuse.

Four requests were sent, with three mechanically valid hierarchies and one
provider failure. That initial run made no retries or request reuses and did not
regenerate the baseline. The user then explicitly required retrying N063.
One additional request in
`sse_multivector/experiments/sol61-xhigh-sp-scope-regression-n063-retry-v1/`
returned a valid hierarchy. Shared `prepare --from ... --only N063 --repeat`
preserved the exact case and every runner setting; `run --max-new-attempts 1`
bounded the retry to one new call. The original failed receipt and the three
completed outputs and reviews remain unchanged.

This was a reproduction run, not a prompt A/B comparison. The initial cases
have no paired baseline; the retry records the failed first attempt as its
unavailable baseline. The agent assessed complete outputs against the original
posts and the saved Astra hierarchies, using headings to judge parent
relationships.

| Post | Original branch failure | Complete-output finding |
| --- | --- | --- |
| N063 | Not reproduced on the authorized retry | General culinary fats and oils remain in the food branch at 1.7, with general olive oil, extra virgin olive oil and butter plus dish-specific children. The dish-specific ingredient parent at 2.1.1.1 has 15 dish-qualified children. All named ingredients and their general subjects remain covered. The first attempt returned `server_is_overloaded` / `service_unavailable_error`, classified as `unknown`; it supplied no subject-quality evidence. |
| N074 | Reproduced | 9.1.2, Michael Pollan's combined real-food/moderation/mostly-plants advice, has single-part children at 9.1.2.1–9.1.2.3. Each drops the other restrictions. The separate general-advice branch correctly makes the individual recommendations siblings of the combination. |
| N096 | Not reproduced in its original form | The general cooking steps sit under general techniques. The same pattern appears at 3.3.1.1, sautéing finely chopped onion, celery and carrot in olive oil, → 3.3.1.1.2, adding garlic after sautéing those vegetables. The child drops olive oil and finely chopped. |
| N100 | Not reproduced in its original form | 3.3's byproduct-use children describe uses, with general materials preserved elsewhere. The same pattern appears at 7.1.2.1, providing chickens with cold water and sunflower seeds tomorrow, → separate water-only and seeds-only children. The combination also splits under 9.1. |

The completed outputs retain the original useful subjects and details: N074's
individual and combined recommendations, comparisons, controversy, parent/child
example and attribution; N096's ingredients, quantities, recipe/yield, preparation
steps, simmering heat/duration and packet instructions; N100's purchase, cutting,
trimming, materials and intended uses, chicken provisions, and sealer details.
Coverage is an agent assessment, not proof of exhaustive extraction. N100 also
leaves separate grounding uncertainties: interpreting the duplicated "some some"
as myoglobin for chickens, and inferring that the steaks were the vacuum-sealed
object. Neither uncertainty is needed to establish its conjunction failure.

After the retry, each regression post has one completed output. The same
parent-scope failure pattern appears in N074, N096 and N100; no clear instance
was found in the complete N063 retry output. This demonstrates recurrence in
three observed answers, not a failure rate or general model comparison.
Native receipts, complete answers and four initial agent reviews remain in
ignored `sse_multivector/experiments/sol61-xhigh-sp-scope-regression-v1/`; the
separate retry experiment retains its answer and one agent acceptance. User
authorization of the retry is not a semantic verdict on the output. There are
no new user semantic verdicts. This frozen-baseline run did not test ASv6.50.
The subsequently authorized candidate comparison uses these saved Sol outputs
without rerunning completed ASv6.48 cases.

## Frozen-baseline reproduction on GPT-6 Astra medium

On October 1, 2026, the user authorized one fresh ASv6.48 answer per regression
post with GPT-6 Astra medium. Shared `prepare --from` inherited the complete
posts, frozen prompt, schema and runner settings from the Sol experiment,
changing only model and reasoning effort. All four rendered prompt hashes
match the original Astra-low requests. Subscription WebSocket transport,
four concurrent requests, a 1,800-second deadline, no output cap and no paid
fallback remain. `--repeat` prevents reuse; `--max-new-attempts 4` bounds calls.

The first preparation, `astra-medium-sp-scope-regression-v1`, was refused
before inference because concurrent workspace work changed `experiment.py`.
Inspection found an unrelated offline-command addition. A fresh native
preparation, `astra-medium-sp-scope-regression-v2`, preserved identical prompt,
cases and runner settings and recorded the current code. It returned four
valid answers from four calls, with no failures, retries or reuse. Receipts
verify the actual request model `gpt-6-astra` and reasoning effort `medium`.
The original Sol plan, receipts, report and reviews remain byte-identical.

| Post | Entries | Parent-scope finding |
| --- | --- | --- |
| N063 | 45 | Original error avoided: 1.2.8, culinary fats and oils, is a sibling of 1.2.1, ingredients for mushroom risotto with shrimp. General olive oil, extra-virgin olive oil and butter remain. No clear instance of the same restriction-dropping pattern was found elsewhere. |
| N074 | 40 | Original error reproduced: 6.1, eating real food in moderation, mostly plants, has single-part children at 6.1.1–6.1.3. Attribution also drops between 6.2, Michael Pollan's dietary advice, and 6.2.1, the unqualified combined recommendation. |
| N096 | 66 | Original error reproduced: 4.1, preparing spaghetti Bolognaise, contains general sautéing at 4.1.1, gently frying ground beef without browning at 4.1.4, and cooking spaghetti according to packet instructions at 4.1.9. Those headings also describe preparation of other dishes. |
| N100 | 66 | Original general-material nesting avoided; the same pattern appears between 4, use of meat-preparation byproducts, and 4.1, tallow making. The child does not specify using byproducts. Its own child at 4.1.1 does specify trimmed beef fat. The chicken water/seeds combination stays intact, avoiding Sol's conjunction error. |

Coverage matters separately from the parent check. N063 names all 15 ingredients
individually in general branches, but combines their dish-specific instances into
one long ingredient-list heading at 1.2.1.1 instead of retaining separate entries.
Avoiding the original nesting therefore does not establish overall regression
acceptance. N096 retains its ingredient quantities, recipe/yield and preparation
instructions, but names salt and pepper only together. N100 retains purchase,
cutting, trimming, materials and intended uses, chicken provisions and sealer
details, but has no individual cold-water heading. Its myoglobin-for-chickens
interpretation remains a separate source ambiguity. N074 retains the individual
and combined recommendations, comparisons, parent/child example and attribution.
These coverage findings are agent assessments, not exhaustive-extraction proof.

The same parent-scope pattern occurs in three observed Astra-medium answers;
N063 avoids it with a coverage concern. This is one completed answer per post,
not a failure rate or evidence of a general model ranking. Four native agent
rejections record the relationship failures and N063's coverage concern; there
are no user semantic verdicts. Complete answers, receipts and reviews remain
ignored under `sse_multivector/experiments/astra-medium-sp-scope-regression-v2/`.
Native reported usage is 10,854 input tokens and 10,621 output tokens, including
309 reasoning tokens. The $0.63959 catalog reference estimate is not a bill or
measured subscription quota; incremental cash is zero.

This Astra-medium run did not test ASv6.50. The subsequent candidate test is
authorized on GPT-6.1 Sol xhigh; no Astra candidate inference is authorized.

## Frozen-baseline reproduction on GPT-6 Astra high

On October 1, 2026, the user authorized testing Astra high, then xhigh unless
an effort level returned no failures. Shared `prepare --from` inherited the
Astra-medium experiment's complete posts, frozen ASv6.48 prompt and runner
settings, changing only reasoning effort to `high`. Four fresh answers returned
from four calls, with no failures, retries or reuse. `--repeat` prevents reuse;
`--max-new-attempts 8` allows the shared policy's two-attempt maximum per case
if an eligible provider failure occurs. No retries were needed.

| Post | Entries | Complete-output finding |
| --- | --- | --- |
| N063 | 42 | Original fats-under-dish error avoided. New clear instance: 1.3.8, wine as a cooking ingredient, → 1.3.8.1, dry white wine, drops the cooking role. A post about drinking dry white wine fits the child without the parent. |
| N074 | 50 | Original conjunction error avoided: individual recommendations at 4.1–4.3 are siblings of the combined attributed advice at 4.4. New clear instance: 2.2.2, controversy over a mother telling her 10-year-old child to eat vegetables, → 2.2.2.1, a mother's instruction to eat vegetables as a childhood exception to the Nostr diet's lack of controversy, drops the age restriction. Possible book-source loss at 8.1 → 8.1.1 and 9.1.1 → 9.1.1.1 remains a separate uncertainty. |
| N096 | 82 | Original error reproduced: 4.3.1, preparing beef and tomato sauce for Spaghetti Bolognaise, → 4.3.1.2, gently frying ground beef without browning. The child drops sauce/dish scope. Sautéing children at 4.2.1.1 and 4.2.1.2 also lose restrictions from 4.2.1. |
| N100 | 74 | Original byproduct branch and Sol's chicken conjunction error avoided. New clear instance: 1, beef, → 1.6, myoglobin. The generic protein heading drops the beef restriction; its `context` cannot supply it. |

High therefore did not meet the user's stopping condition: all four completed
answers contain clear instances of the same pattern. N074's age restriction
drop was found during the subsequent xhigh review; a new native agent rejection
supersedes the earlier uncertain verdict while preserving its review history.
The possible book-source relationship is not needed for the rejection. Current
reviews are four agent rejections, with no user semantic verdicts.

Coverage remains a separate check. N063 retains all named general ingredients
but omits separate dish-specific ingredient subjects and the dish-specific
ingredient-list heading. N096 retains quantities, recipe/yield and preparation
details, with salt and pepper individually represented. N100 retains purchase,
cutting, trimming, materials and intended uses, individual water/cold water and
sunflower seeds, chicken provisions and sealer details. N074 retains individual
and combined advice, comparisons, controversy, the family example and attribution.
N100's myoglobin-for-chickens and vacuum-sealing-prepared-beef interpretations
remain separate grounding uncertainties. These are agent coverage assessments.

Complete answers, receipts and reviews remain ignored under
`sse_multivector/experiments/astra-high-sp-scope-regression-v1/`. Native usage is
10,854 input tokens and 14,679 output tokens, including 2,957 reasoning tokens.
The $0.84249 catalog reference estimate is not a bill or measured subscription
quota; incremental cash is zero. This Astra-high run did not test ASv6.50.

## Frozen-baseline reproduction on GPT-6 Astra xhigh

High's confirmed failures triggered the user's authorized xhigh test. Shared
`prepare --from` inherited the high experiment's complete inputs, frozen
ASv6.48 prompt and runner settings, changing only effort to `xhigh`. The run
used `--repeat` and `--max-new-attempts 8`. All four answers completed from
four calls, without failures, retries, reuse or baseline regeneration.

| Post | Entries | Complete-output finding |
| --- | --- | --- |
| N063 | 67 | No clear parent-scope failure found. General fats/oils are outside a dish-specific parent; wine → white wine → dry white wine fixes high's cooking-role loss. All 15 named ingredients have individual general subjects and separate dish-specific instances. |
| N074 | 71 | Original conjunction error avoided, and Food Rules is explicit in the combined advice, resolving high's book-source concern. New clear instance: 1.1.3, Nostr diet not stirring controversy like the carnivore diet, → 1.1.3.1, mother–child conflict over vegetables as an exception to the Nostr diet's lack of controversy, drops the carnivore-diet comparison. |
| N096 | 107 | Original general-steps-under-Bolognaise organization largely avoided. Clear instances remain at 3.2.1, tinned tomato products, → general chopped tomatoes and tomato purée at 3.2.1.1–3.2.1.2; combined vegetable chopping at 4.1.1.1 → single-vegetable children; and 4.2.1's sautéing → garlic addition at 4.2.1.2, losing finely chopped and olive oil. |
| N100 | 103 | Original byproduct-use/material error, high's generic myoglobin-under-beef error and Sol's chicken conjunction error avoided. New instance: 6.1.1, dog intended to receive beef trimmings and myoglobin, → 6.1.1.1, trimmings for the dog, and 6.1.1.2, myoglobin for dog food. Each child drops the other component of the combined plan. |

The agent accepted N063 and rejected the other three answers. N074's individual
and combined advice, comparisons, controversy, family example, Bitcoin narrative
and attribution remain covered. N096 retains general ingredients, individual
quantities, recipe/yield and preparation details. N100 retains general materials
and uses, quantities, animal provisions and sealer details. Its interpretation
of myoglobin for chickens remains a separate source ambiguity; this answer does
not assert that the sealer was used on the beef. No user semantic verdicts were
added. Coverage and relationship assessments describe these particular outputs.

All eight high/xhigh request receipts verify `gpt-6-astra` and the requested
effort in the actual serialized body. Each rendered prompt matches the original
Astra-low request's SHA-256, and hierarchy numbering is complete. Frozen ASv6.48
and ASv6.50 instructions remain unchanged. Native xhigh usage is 10,854 input tokens
and 51,520 output tokens, including 34,640 reasoning tokens. The $2.68454 catalog
reference estimate is not a bill or measured subscription quota; incremental
cash is zero. Complete answers, receipts and reviews remain ignored under
`sse_multivector/experiments/astra-xhigh-sp-scope-regression-v1/`.

Neither tested effort level returned a failure-free set. These are one-answer
trials per post and effort, not measured failure rates or a model ranking.
The authorized Astra effort escalation ended at xhigh. The user subsequently
approved ASv6.50 and testing it on GPT-6.1 Sol xhigh, as described below.

## Approved candidate comparison on GPT-6.1 Sol xhigh

The user approved ASv6.50's delta against frozen ASv6.48 and requested the
GPT-6.1 Sol xhigh test. The proposed regression design uses three fresh answers
for each of N063, N074, N096 and N100, compared with the saved Sol ASv6.48
answers. Shared `prepare --from ... --prompt ... --prompt-id ASv6.50 --repeat`
prepares three independent trials. Model, effort, schema, full original posts,
WebSocket transport, deadline and concurrency match the frozen-baseline Sol
experiment. Only the approved hierarchy paragraph changes in each rendered
request. Each trial uses `run --max-new-attempts 8`, allowing at most the shared
two-attempt policy per case for eligible provider failures. Baselines are not
rerun; paid API fallback and output caps remain absent.

The shared revision command derives the
[ASv6.50 post template](../../experiment_specs/asv6.50-hr01-post-template.txt)
from the existing ASv6.48 post template. Its instructions are byte-identical
to approved ASv6.50, followed by the same `<post>` wrapper and `{POST}` variable.
The revision receipt pins the baseline template and single approved edit.

Native comparisons pair N074, N096 and N100 with their saved Sol answers.
The original N063 attempt failed; its successful baseline is preserved in the
separate `sol61-xhigh-sp-scope-regression-n063-retry-v1` experiment. Review uses
that saved answer directly for N063 rather than constructing a combined report
or rerunning it. Complete hierarchies are assessed for parent relationships,
coverage of individual subjects and their particular instances, combinations,
and newly introduced errors. Approval of the prompt is not a user semantic
verdict on any returned answer.

The three ignored experiment directories are
`sse_multivector/experiments/asv6.50-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.50-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.50-sol61-xhigh-sp-scope-regression-t3/`.
All twelve answers completed from twelve calls, with no failures, retries or
reuse. Actual serialized request receipts verify `openai-codex`, `gpt-6.1-sol`,
reasoning effort `xhigh` and WebSocket transport. Every answer is mechanically
valid, with unique numbering and each parent listed before its children.
ASv6.48 and approved ASv6.50 prompt hashes, and the original Sol baseline
artifacts, remain unchanged.

| Post | Saved Sol ASv6.48 answer | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- | --- |
| N063 | Pass, 91 entries | Pass, 78 entries | Pass, 168 entries | Pass, 120 entries |
| N074 | Fail, 83 entries | Pass, 100 entries | Pass, 84 entries | Fail, 105 entries |
| N096 | Fail, 134 entries | Pass, 190 entries | Fail, 144 entries | Pass, 156 entries |
| N100 | Fail, 125 entries | Pass, 144 entries | Pass, 141 entries | Pass, 131 entries |

Pass/fail in this table describes the parent-scope check on the complete
hierarchy. Ten candidate answers pass that check; two contain the same failure
pattern. These observations do not establish a failure rate or measured
improvement: the baseline has one saved answer per post, and the candidate has
three. ASv6.50 does not eliminate the agreed regression.

N074 trial 3 fixes the saved conjunction failure but introduces an advice-role
loss:

```text
1.2.3     Advice to eat mostly plants
1.2.3.2   Mostly plant-based eating as an alternative to the Bitcoin–carnivore-diet narrative
```

A post describing someone's own dietary alternative without giving advice
fits the child heading without the parent. The child's source `context` calls
it a recommendation, but that context cannot constrain the standalone heading.
The relationship repeats at `1.1.2.2.1 → 1.1.2.2.1.2` and
`1.3.2.2.1 → 1.3.2.2.1.2`. Trials 1 and 2 retain the advice role; in all three
answers the combined, attributed Food Rules advice is narrower than the
individual recommendations rather than their parent.

N096 trial 2 reproduces the saved Sol failure:

```text
3.3.1.1     Sautéing finely chopped onion, celery and carrot in olive oil over medium heat in a large pan
3.3.1.1.1   Adding crushed garlic after a few minutes of sautéing onion, celery and carrot
```

The child drops finely chopped, olive oil, medium heat and large pan. A post
about adding garlic after sautéing those vegetables in butter fits the child
without fitting the olive-oil parent. Two further relationships drop dish scope:
`5.1.1`, large pan for preparing spaghetti bolognese sauce, → `5.1.1.1`, the
general vegetable sauté; and `4.1.1`, one tin of water for spaghetti bolognese
sauce, → `4.1.1.1`, adding tomato ingredients and water once beef is uniformly
coloured. Trials 1 and 3 place the garlic step separately from the restrictive
sauté, and their sauce-specific children retain sauce scope.

Coverage was assessed across each complete hierarchy. All three N063 answers
retain individual general subjects for all 15 ingredients and separate
dish-specific instances, with general fats outside the dish-specific ingredient
parent. N074 retains individual and combined advice, both sides of comparisons,
the ten-year-old/mother/vegetable exception, Bitcoin narrative and Food Rules
attribution. N096 retains individual ingredients and quantities, salt and pepper
separately and together, recipe/yield, preparation, heat/duration and packet
instructions. N100 retains purchase and steak quantities, trimming, general
materials and their uses, individual chicken provisions and their combination,
and the sealer comparison, discount and recommendation. Its use branches have
particular uses as children, and its combined chicken plan has no single-part
children. Different numbering, wording and repeated applicable branches are
accepted; coverage is an agent assessment rather than exhaustive-extraction
proof.

Two separate N100 grounding uncertainties remain. Trial 1 asserts that the
beef was vacuum-sealed, although the post names no object for the sealer's use
(`2.8.1`, `11.1.1` and repetitions). Trial 2 interprets the duplicated
"some some" as adding saved myoglobin to the chickens' cold water and sunflower
seeds (`2.1.6.2`, `4.1.5` and repetitions); simply putting out water and seeds
is also supported. These ambiguities were present in the saved baseline and
are separate from the parent check. Trial 3 asserts neither relationship.
The two answers therefore pass this regression check without establishing
acceptance of those source interpretations.

Native reviews record ten agent acceptances for the regression check and two
agent rejections, with the grounding uncertainties in their comments. No user
semantic verdicts have been added. Complete answers, receipts, reports and
reviews remain in the ignored experiment directories above.

| Trial | Input tokens | Cached input tokens | Output tokens | Reasoning tokens included in output | Catalog reference estimate |
| --- | --- | --- | --- | --- | --- |
| 1 | 5,910 | 4,992 | 75,042 | 49,689 | $0.7627392 |
| 2 | 10,902 | 0 | 76,177 | 50,716 | $0.783574 |
| 3 | 10,902 | 0 | 70,075 | 45,242 | $0.722554 |

These are the native per-trial usage totals. Catalog estimates are not bills or
measured subscription quota; provider-reported cost is unavailable and
incremental cash is zero. Adoption as the subject baseline remains open. The
subsequent agent review confirmed the two failing relationships and the user
authorized preparing the ASv6.51 revision below. The user subsequently authorized
its regression test and a fresh transfer check outside food if that set passes.

## ASv6.51 approved candidate

Status: approved candidate, tested on GPT-6.1 Sol xhigh. Two of twelve completed
answers contain the parent-scope failure pattern. The first evaluation was
interrupted before any answer completed; all twelve authorized retries succeeded.
On October 1, 2026, the user approved
the ASv6.51 wording with "lgtm" after reviewing its full-context delta.
The preceding drafting authorization followed the agent's confirmation of
N074 trial 3's advice-role loss and N096 trial 2's loss of sautéing restrictions.
The subsequent testing instruction authorized the comparison below.

[ASv6.51 (approved candidate, tested on Sol xhigh)](../asv6.51/ASv6.51.md) replaces
ASv6.50's existing hierarchy condition with a counterexample check. Compare the `subject` headings
alone and imagine another post that fits the child: if it could fail to fit the
proposed parent, use a broader parent. Each applicable branch must pass that
check. The requirements to retain enumerated subjects, combine shared headings
and give every heading its own entry remain.

This is an operational phrasing of the existing relationship requirement.
One hierarchy paragraph changes; all other instructions and both examples are
byte-identical to ASv6.50. No regression-specific examples, extra rule paragraph,
separate model pass or output fields are added. The change stays within one
SP request; actual model token use remains unmeasured.

Shared `experiment.py revise` generated the new prompt and its
[ASv6.51 revision receipt](../asv6.51/ASv6.51.md.revision.json) against ASv6.50,
the last approved prompt at the time, with SHA-256
`2ab157eb34f49edd2a443799c439be8eff512fe61df96f6d508434f4d3807a1c`.
The ASv6.51 SHA-256 is
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
Mechanical revision checks verify preservation and provenance; they do not
establish a semantic improvement. No model calls were made while drafting.
ASv6.48 remains the frozen subject baseline and MPv3.43 remains the frozen
mask working baseline. The authorized regression comparison is complete; it
did not pass, so the conditional fresh-topic transfer check was not started.

## ASv6.51 comparison on GPT-6.1 Sol xhigh

On October 1, 2026, the user authorized the same three-answer regression design
on approved ASv6.51, followed by a fresh non-food check if it passes. N063, N074,
N096 and N100 retain their complete original text and source evidence. Each of
three native `prepare --from ... --prompt ... --prompt-id ASv6.51 --repeat`
trials inherits its corresponding completed ASv6.50 trial, pairing all four
cases with saved answers without regenerating a baseline.

The [ASv6.51 post template](../../experiment_specs/asv6.51-hr01-post-template.txt)
was derived through shared `revise` from the ASv6.50 template using the single
approved paragraph edit. Its instructions are exactly approved ASv6.51, with
the unchanged `<post>` wrapper and `{POST}` variable. Native revision receipts
pin both template hashes. Pre-run checks verify all twelve rendered requests:
same complete inputs, evidence, schema, GPT-6.1 Sol model, xhigh effort,
WebSocket transport, 1,800-second deadline, four concurrent requests per trial
and no output cap. Only the approved paragraph differs. Each trial uses
`run --max-new-attempts 8`, permitting only the shared provider-retry policy's
two-attempt maximum per case. Incremental subscription cash is zero; no paid
fallback is configured.

The ignored experiments are
`sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t3/`.
Twenty saved ASv6.48/ASv6.50 baseline plan, output, report and review files are
hash-pinned before inference. ASv6.48 and MPv3.43 remain frozen; ASv6.51 adoption
remains open. Complete candidate hierarchies must be reviewed for the agreed
parent-scope pattern, core coverage and new errors, with agent assessments
kept separate from user semantic verdicts.

### Interrupted execution

All three trials were launched concurrently. Each native report records four
failed cases, four attempts, zero completed answers and zero reused answers.
All twelve calls ended after 129.69–129.85 seconds with a WebSocket close code
of `1006`, no clean close and no terminal response event. The upgrade had
succeeded (`http_status: 101`), and each connection had received 13 or 15 frames
before closing. The receipts retain a blank `TypeError` in the body phase;
the shared failure classifier reports `unknown`.

All twelve connection failures coincided with a local service interruption.
No runner code was changed by this task.

There are no returned hierarchies to judge, so these are execution failures,
not evidence for or against the ASv6.51 wording. No semantic reviews were
recorded and no non-food transfer requests were sent. The SDK retained zero
token/cost counters without final provider usage; this does not establish that
the interrupted upstream generations consumed no quota. Incremental cash
remains zero on the subscription route, with no paid fallback.

No automatic retries were sent. The [repository retry rule](../../../AGENTS.md)
allows them only for provider failures, not unknown causes. Before explicit
retry authorization, native `prepare` created three identical retry trials at
`sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t1-retry-v1/`,
`sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t2-retry-v1/`
and `sse_multivector/experiments/asv6.51-sol61-xhigh-sp-scope-regression-t3-retry-v1/`.
They preserve the complete inputs and settings, use the same approved ASv6.51
template, and pair against the corresponding saved ASv6.50 answers. Preparation
made no model calls and preserved the interrupted receipts.

### Authorized retry

After the interruption report, the user explicitly authorized retrying all
twelve requests with "proceed" on October 1. Pre-run verification found the
local service active and the approved prompt/template hashes, complete inputs,
settings, paired baselines and prepared workflow code unchanged. All three
retry trials completed through native `run --max-new-attempts 8`: four valid
answers and four attempts each, with no additional provider retries, reused
answers, malformed outputs or execution failures. No paid fallback was used.

### Completed retry results

Complete candidate hierarchies and source posts were read for all twelve
answers. Native agent reviews record ten acceptances for the regression check
and two rejections, with no user semantic verdicts. Numbering is unique and each
parent exists before its children. Mechanical validity does not establish
semantic correctness.

| Post | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| N063 | Pass; 81 entries | Pass; 78 entries | Pass; 85 entries |
| N074 | Pass; 89 entries | Pass; 91 entries | Pass; 87 entries |
| N096 | **Fail; 143 entries** | Pass; 117 entries | **Fail; 158 entries** |
| N100 | Pass; 124 entries | Pass; 141 entries | Pass; 128 entries |

Pass/fail describes the parent-scope check on the complete hierarchy, not
blanket output approval or proof of exhaustive extraction.

N096 trial 1 contains:

```text
1.4.6.1    Finely chopped onion, celery and carrot mixture
1.4.6.1.1  Sautéed onion, celery and carrot mixture with crushed garlic
```

The child loses "finely chopped." A post about a coarsely chopped mixture
sautéed with garlic fits the child without fitting the parent. Its `context`
states that the vegetables were finely chopped, but that cannot constrain the
standalone `subject` heading.

N096 trial 3 contains:

```text
3        Cooking ingredients
3.1      Vegetable ingredients
3.1.1    Onions
3.3      Meat ingredients
3.3.1    Beef
3.6      Pasta
```

The general entity headings lose the ingredient role. A post about onion
cultivation or beef export prices fits the child without describing its use as
an ingredient. Other general entries in this branch require the same check.
This parallels the saved Astra-high `Wine as a cooking ingredient` →
`Dry white wine` failure. The general entities should remain represented under
broader headings; preserving them does not require these invalid relationships.

The earlier garlic-addition loss is avoided in all three N096 answers: garlic
addition and the fully specified sauté have separate broader parents. Pan and
dish-specific water entries have no children that drop their restrictions.
Ingredients and quantities, recipe/dish/yield, the preparation sequence,
heat/timing/visual cues and packet instructions remain represented. N063 keeps
all fifteen general ingredient subjects and particular dish instances. N074
keeps individual and combined advice, comparisons, the mother/10-year-old
example, Bitcoin narrative/fatigue and the Food Rules/Michael Pollan attribution.
Trials 1 and 2 have no separate alternative-to-Bitcoin-carnivore heading; the
critique and complete advice are represented separately. N100 retains general
materials, by-product uses, measurements, animal provisions and product/purchase
subjects. These are agent coverage assessments, not exhaustive-extraction proof.

Separate N100 grounding uncertainties persist. Trials 1 and 3 infer that the
beef steaks were vacuum-sealed from the order of statements; the post does not
name the sealed object. All three interpret the ambiguous "some some" wording
as myoglobin intended for chickens. These findings are distinct from the
parent-scope check and limit the meaning of its pass verdicts.

### Worked-example finding

Reviewing the surviving modifier loss exposed an inconsistency in the unchanged
railway example in [ASv6.51](../asv6.51/ASv6.51.md):

```text
7.1.1    Photography of Bracken the steam locomotive's restoration
7.1.1.1  Photography of Bracken's restoration for an exhibition
```

The child omits "the steam locomotive." A standalone heading about restoration
photography of a different object named Bracken could fit it without fitting
the parent's locomotive restriction. Resolving Bracken from the supplied example
post cannot add that restriction to a subject vector encoded from the heading
alone. The earlier example audit missed this loss; its assessment is corrected
in the ASv6.49 documentation. The same wording is present in frozen ASv6.48.
Neither prompt nor either example was edited during this evaluation.

This is a reason to review a correction to the existing example before another
prompt test. The observed outputs do not establish that the example caused
their failures. A correction is a recommendation, not an approved prompt change.

### Completed retry usage and disposition

Native usage reports for the completed retry trials are:

| Trial | Input tokens | Cached input | Output tokens, including reasoning | Reasoning tokens | Catalog cost estimate, USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 10,954 | 0 | 66,177 | 44,872 | 0.683678 |
| 2 | 10,954 | 0 | 58,700 | 38,130 | 0.608908 |
| 3 | 8,394 | 2,560 | 61,917 | 40,033 | 0.636214 |

Catalog estimates are not invoices or subscription charges. Incremental cash
is zero on the subscription route; provider-reported billing is unavailable.
The interrupted first attempts still lack final usage. No usage total was
assembled outside the shared workflow.

ASv6.51 does not pass the agreed regression. ASv6.50 also had two failing
answers among twelve; these samples do not establish a quality improvement or
generalization. The conditional non-food check was not started. ASv6.48 and
MPv3.43 remain frozen, and ASv6.51 adoption remains open. Any further prompt
revision requires a separately reviewed delta and authorization.

## ASv6.52 example-only draft

Status: superseded draft, untested. Its examples omit required placements in
applicable branches; ASv6.53 corrects them. On October 1, 2026, the user directed
the work to focus on SP, retain examples and ensure that they demonstrate the
intended behavior,
then authorized preparing an example-only delta for review. This authorizes
drafting, not approval of its wording or another model run. ASv6.51 remains the
last approved candidate and ASv6.48 remains the frozen subject baseline.

[ASv6.52 (draft, untested)](../asv6.52/ASv6.52.md) makes three edits to the
railway example against approved ASv6.51:

- Retain "the steam locomotive" in the exhibition-photography child at
  `7.1.1.1`, correcting the loss recorded above.
- Add explicit advice to museum visitors to book their visit ahead and stay on
  the marked visitor route to the example's source post.
- Extend the complete example output with general subjects, a replacement-parts
  branch and the individual and combined visitor-advice subjects.

All instructions and the entire lunar example are byte-identical to ASv6.51.
The original 31 railway entries remain, with only the photography child's
subject wording corrected. Seventeen entries are added. The general `Boilers`
heading remains outside `Replacement parts`; the role branch is
`Replacement parts` → `Replacement boilers` →
`Replacement boiler for Bracken the steam locomotive`. That particular boiler
heading also remains in its original steam-locomotive-boilers branch.

The combined advice appears under each individual instruction. Both occurrences
preserve the advice role, railway-museum visitor scope and both actions.
`Advance booking`, `Marked routes`, `Staying on marked routes` and `Visitors`
have separate general headings and museum-specific children. The example does
not assert that anyone booked or followed the route. The worked examples use
astronomy and railway-museum content, separate from the four food regression
posts.

Before revision, the minimal heading check reproduced the original photography
child's missing locomotive restriction. After revision, that check passes.
Both complete JSON outputs pass the production subjects-adapter validator:
11 lunar entries with six relationships and 48 railway entries with 33
relationships. All entries retain the `number`, `context`, `subject` field
order, with unique numbers and parents preceding children. Preservation checks
verify every original railway entry, the unchanged instruction bytes and the
unchanged lunar example.

The initial agent audit reviewed the 39 existing direct relationships and source
coverage but did not check every applicable placement. The subsequent whole-prompt
review found that both examples violate "including it in each branch that passes
this check." Eclipse observation through binoculars is absent from `Binoculars`
and `Lunar eclipses`; sketching the Moon is absent from `The Moon`; Bracken's
restoration is absent from `Steam locomotive restoration`; and the combined
visitor advice is absent from its booking and route-following branches. Checking
existing relationships and output format did not establish whole-prompt
consistency. ASv6.52 is not ready for inference. Its source remains useful for
reproducing the omission and checking that ASv6.53 preserves the example posts.

This follows the official OpenAI guidance that examples should closely agree
with the instructions; discrepancies can reduce reliability.
[Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices#how-to-prompt-reasoning-models-effectively).
That guidance does not establish that these particular examples improve SP.

Shared `experiment.py revise` generated the draft and its
[ASv6.52 revision receipt](../asv6.52/ASv6.52.md.revision.json) against approved
ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The draft SHA-256 is
`e956efea3391c26c0180893c6c753d7eb246abd26040979b64c6dd8c152df0ff`.
The source prompt grows from 11,057 to 14,385 UTF-8 bytes, adding 3,328 bytes
of repeated input per SP request. This remains one request per post, with two
worked examples and the existing output schema. Actual model token use is
unmeasured. No template, experiment or inference request was created for this
draft. The user subsequently authorized fixing both examples; the correction
is recorded below.

## ASv6.53 example correction

Status: superseded draft, untested. The user authorized fixing the examples after the
whole-prompt audit exposed ASv6.52's missing placements. The authorization covers
the example correction and offline verification. Wording approval, inference and
adoption remain open; ASv6.51 is still the last approved candidate and ASv6.48
is the frozen subject baseline. The subsequent rule-to-case audit below shows
that ASv6.53 does not meet the user's complete example-coverage criterion.

[ASv6.53 (draft, untested)](../asv6.53/ASv6.53.md) replaces both complete example
outputs. Every example post is byte-identical to ASv6.52, and all instructions
are byte-identical to approved ASv6.51. The lunar output retains its 11 distinct
subjects; the railway output retains 46 distinct subjects. Repeated entries now
fill each applicable branch, including every occurrence of a shared heading.

For example, eclipse observation appears beneath both astronomical observation
and lunar eclipses; observing through binoculars also appears beneath binoculars.
Moon sketching appears beneath both sketching and the Moon; cloud obstruction
appears beneath both clouds and the Moon. Bracken's restoration appears beneath
both the named locomotive and steam-locomotive restoration. General boilers
remain outside replacement parts, while replacement boilers have both boilers
and replacement parts as broader headings. The combined advice appears beneath
both individual instructions in every advice, visitor, booking and route branch
that applies. Individual instructions remain outside the combined advice.

Five railway headings are made more explicit where their additional placements
require it. Mira's work names the railway museum's steam locomotive; continuing
tours name Bracken as a steam locomotive; the booking advice names railway-museum
visits; and the route advice names the museum's marked visitor route. The combined
advice preserves both clarified instructions. A child's proposed placement never
borrows those restrictions from the source post or `context`.

The worked examples contain 18 lunar entries and 129 railway entries, with 128
displayed direct relationships in total. The agent reviewed source support,
standalone wording and broader relationships for all 57 distinct subjects.
Seventy-six declared broader relationships include one transitively redundant
relationship; combining shared headings uses the remaining 75 relationships
without repeating a subject directly beside its own containing branch.

The maintained [example tests](../../test_subject_prompt_examples.py) exercise
the production subjects adapter before inspecting placements. The minimal test
first failed against ASv6.52 because the binoculars branch had no eclipse
observation child. It passes against ASv6.53. Checks cover all 76 declared
relationships beneath every copy of each parent, all displayed relationships,
14 prohibited placements, distinct-subject coverage, output field order,
unchanged instructions and unchanged example posts. Negative cases include
general boilers beneath replacement parts, general booking beneath advice,
individual advice beneath combined advice and boiler replacement beneath
restoration: replacement can be ordinary maintenance.

All six example tests and two existing SP workflow checks passed. The latter
exercise preparation of 200 complete posts without requests and validation of
subject numbering without repairs or retries. Mechanical and declared-relation
checks do not independently prove natural-language entailment or teacher
generalization; the semantic relationships remain an agent assessment.

Shared `experiment.py revise` generated the prompt and its
[ASv6.53 revision receipt](../asv6.53/ASv6.53.md.revision.json) against approved
ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The ASv6.53 SHA-256 is
`6e09b33c83358be4857b7e2b6e3d59cc8e782bfbbe38e8a47e195a37bdab46d0`.
The source grows from ASv6.52's 14,385 to 34,028 UTF-8 bytes. Filling every
applicable branch adds 19,643 bytes of repeated input per request; it introduces
no extra model pass or runtime component. Actual model token use is unmeasured.
No template, experiment or model request was created for ASv6.53. The subsequent
ASv6.54 draft below addresses its example-coverage gaps; ASv6.53 and its tests
remain evidence for the missing-branch correction.

## Example correctness and rule coverage

On October 1, 2026, the user set this criterion: examples demonstrate rules
already stated in SP; each example must obey every applicable rule; every
explicit or implicit rule must be traced concisely to an example case. Each
behavior taught by an example must also trace back to those instructions.
Examples must not introduce an additional rule.

The first map exposed ASv6.53's absent ambiguity, unresolved-name, identifier,
number, figurative, negation and comparison cases. Its passing relationship
checks did not cover those decisions. The user then authorized drafting compact
focused cases with complete outputs and rule mappings.

The current map uses [ASv6.54 (draft, untested on models)](../asv6.54/ASv6.54.md).
Case IDs identify the nine examples in source order; they are review references
and are not added to SP or its output schema. Every case contains its complete
source post and expected JSON. The maintained tests contain the same case IDs,
purposes, rule mappings, canonical subjects and reviewed relationships.
"Reviewed" below is the agent's source-support and heading-relationship
assessment, not user approval or a model result.

| Case | Purpose | Demonstrated rules | Review |
| --- | --- | --- | --- |
| C1 | Whole-post references, implied subjects and repeated hierarchy branches. | R01–R04, R16–R32, R34, I04 | Reviewed |
| C2 | Named referent resolution, replacement-part roles and retained locomotive type. | R02–R05, R16, R18–R22, R27–R32, R34, I01–I02, I05 | Reviewed |
| C3 | Individual advice instructions and their stated combination. | R04, R16–R22, R27–R32, R34, I03 | Reviewed |
| C4 | Names, hashtags, figurative labels, rhetorical meaning and an unresolved name. | R01–R06, R10, R12, R16–R22, R27–R32, R34 | Reviewed |
| C5 | URL and opaque identifier bodies without surrounding subject evidence. | R07, R12, R24 | Reviewed |
| C6 | URL and identifier subjects established by prose, without a cross-link. | R04, R07–R08, R10–R12, R16, R18, R20–R22, R27–R31, R34 | Reviewed |
| C7 | Two direct ambiguity interpretations, independent co-mention and statement order. | R01, R03–R04, R09–R12, R16, R18–R22, R27–R32, R34 | Reviewed |
| C8 | Count versus length, preserved negation, both comparison sides and no unstated arithmetic. | R01–R02, R04–R05, R13–R22, R27–R34 | Reviewed |
| C9 | Explicit arithmetic result with separately retained addends and result. | R03–R04, R13–R22, R27–R32, R34 | Reviewed |

The rule-to-case map traces the existing instruction clauses. An example's rule
list identifies its demonstrations; every case must still obey all other
applicable instructions. An absent prohibited output demonstrates a guard only
when the input presents the decision that could produce it.

| ID | Existing SP instruction | Demonstration |
| --- | --- | --- |
| R01 | Build a subject index after understanding the complete post. | C1: observation, Moon, binoculars, sketching and clouds all remain. |
| R02 | Resolve references to the most specific supported description. | C2: Bracken's later identification supplies the boiler's locomotive type; C8 resolves A and B. |
| R03 | Use general knowledge to clarify language, identify referents and recognize subjects. | C1 recognizes astronomical observation; C4 interprets the figurative label; C9 recognizes addends. |
| R04 | Ground every entity, modifier, action and relationship in the post. | C2 retains the stated replacement role and steam-locomotive type; every case has a source-support review. |
| R05 | Interpret names, labels and hashtags by referent, not component words. | C4: #RavenWorks names an app; the figurative lifesaver label names help, without birds, employment or literal rescue. |
| R06 | Retain the name of an unresolved named subject. | C4: AmberLoop remains by name, outside the app, help and appreciation branches. |
| R07 | Treat URLs and opaque identifiers as providing no subject evidence. | C5: the bare URL and hexadecimal identifier yield an empty array; C6 extracts no birds, repair or count from their bodies. |
| R08 | Retain URL or identifier subjects established by surrounding prose. | C6: the labels establish profile URLs and event identifiers, unlike C5's identical bare bodies. |
| R09 | Give each remaining supported interpretation its own direct subject, without uncertainty qualifiers. | C7: observation of a person's duck and observation of a person ducking have separate entries. |
| R10 | Do not infer relationships from co-mention alone. | C4 does not type AmberLoop as an app; C6 does not associate the profile URL with the event; C7 keeps the notebook purchase independent. |
| R11 | Do not infer relationships from statement order alone. | C7 does not add a chronological or causal link between observation and notebook purchase. |
| R12 | Add no commentary about plausibility or what is unclear or unstated. | C4 directly mentions AmberLoop; C5 returns only the empty object wrapper; C7 directly states both interpretations. |
| R13 | Preserve what numbers refer to. | C8 distinguishes the count of two cables from a length of 2 m; C9 distinguishes addends 2 and 3 from result 5. |
| R14 | Support count or measurement interpretations and units with the post. | C8 retains the stated count and metre units; C9 does not turn arithmetic values into counts or measurements. |
| R15 | Include calculated results only when explicitly stated. | C8 adds neither a 1 m difference nor a 5 m total; C9 includes the explicitly stated result 5. |
| R16 | Enumerate specific subjects before deriving broader headings. | C1 and C2 retain each specific subject alongside broader headings. The output demonstrates retention, not internal reasoning order. |
| R17 | Include literal, nonliteral and rhetorical subjects from parts, combined parts or the whole post, including unnamed concepts. | C1 includes implied cloud hindrance; C3 retains the combined advice; C4 includes figurative help and rhetorical appreciation. |
| R18 | Retain individual subjects, particular instances and expressed combinations. | C3 retains both instructions and their combination; C8 retains both cables and their pair; C9 retains addends, result and calculation. |
| R19 | An event description must not replace its involved subjects. | C1 retains binoculars and the Moon; C7 retains ducks, people and notebooks alongside observation and purchase. |
| R20 | Judge broader relationships using headings alone; a counterexample requires a broader parent. | C2 keeps general boilers outside replacement parts and general replacement boilers outside steam-locomotive boilers. |
| R21 | Build upward and combine shared headings. | C1 shares observation headings; C2 shares boiler headings; C3 shares individual advice headings. |
| R22 | Retain each enumerated subject in every branch that passes the heading test. | C1 repeats binocular observation; C3 repeats the combined advice; C8 repeats the particular pair and comparison; C9 repeats the calculation. |
| R23 | Give each heading and subheading its own entry. | C1 and every other nonempty case have an object at every displayed level. |
| R24 | Return only one JSON object containing a subjects array. | Every case uses the wrapper; C5 uses {"subjects": []}, with no commentary. |
| R25 | Use section-style numbering, broad to specific, with parents first. | C1 demonstrates 1, 1.1 and 1.1.1; all nonempty cases retain this ordering. |
| R26 | Order entry fields as number, context, subject. | Every entry in every nonempty case uses this order. |
| R27 | Context identifies the subject and the source establishing its meaning. | C2's context connects the boiler to Bracken's later identification; C7 directly identifies the source observation for each interpretation. |
| R28 | Context may describe a particular instance supporting a general heading. | C1's eclipse supports astronomical observation; C2's particular replacement boiler supports boilers. |
| R29 | Match the heading's generality; keep instance details in subheadings without importing context restrictions. | C2 separates boilers, replacement boilers and the particular boiler for Bracken; its general boiler heading stays general. |
| R30 | Make each heading understandable without the post, context or other entries. | C2's particular boiler heading names Bracken's type; C8's comparison names both cables and their lengths. |
| R31 | A heading need not retell the post's assertion about its subject. | C1 uses Binoculars; C2 uses Boilers; C4 uses AmberLoop. |
| R32 | Preserve meaning, negation and relationships in headings. | C3 preserves the advice role; C4 preserves the rhetorical appreciation; C8 explicitly retains not longer. |
| R33 | Name both comparison sides when provided. | C8 names 2 m cable A and 3 m cable B in its comparison. |
| R34 | Use concise wording. | C1 uses Sketching the Moon; C2 uses Replacement boilers; C8 retains the details needed to identify both comparison sides. |

The five tracked hierarchy implications derive from those instructions, rather
than adding rules:

| ID | Implication | Instruction basis | Demonstration |
| --- | --- | --- | --- |
| I01 | An entity does not acquire a role merely from its context. | R18, R20, R29, R30 | C2: general boilers remain outside replacement parts. |
| I02 | A child retains restrictions needed to fit its parent, using equivalent wording where appropriate. | R20, R30, R32 | C2: the particular replacement-boiler heading retains Bracken's steam-locomotive type. |
| I03 | A stated combination can fit each component; either component alone need not fit the combination. | R18, R20, R22 | C3: combined advice is beneath both individual instructions; neither instruction is beneath the combination. |
| I04 | Repeating a shared heading requires its applicable descendants beneath every occurrence. | R21, R22, R23 | C1: every lunar-eclipse-observation occurrence includes binocular observation. |
| I05 | The source or context cannot repair a relationship unsupported by the headings alone. | R20, R29, R30 | C2: general replacement boilers stay outside steam-locomotive boilers despite this post's particular boiler being for a steam locomotive. |

All 34 instruction clauses and five tracked implications now have a case.
Review goes in both directions: each rule has a demonstration, and each
demonstrated behavior has an instruction basis. Every case was also reviewed
for source support, complete subject retention, standalone wording and each
valid relationship among its headings. Internal reasoning order has no field
in the required JSON; examples demonstrate its visible consequences without
adding a reasoning trace.

## ASv6.54 focused examples

Status: draft, untested on models. The user's "proceed" authorized this
example revision and offline verification. Wording approval, inference and
adoption remain open. ASv6.51 remains the last approved candidate; ASv6.48
remains the frozen subject baseline.

[ASv6.54 (draft, untested on models)](../asv6.54/ASv6.54.md) preserves every
instruction byte from approved ASv6.51. It preserves ASv6.53's corrected lunar
case byte for byte, replaces the overloaded railway story with separate
replacement-part and combined-advice cases, and adds six language cases.
Neither MP nor the runtime workflow changes.

C4 makes "lifesaver" explicitly figurative, so the example does not silently
choose between literal rescue and helpfulness. Its rhetorical question conveys
appreciation. AmberLoop stays as a named subject without an inferred type.
C5 and C6 use identical URL and opaque-identifier bodies; only C6's surrounding
labels establish subjects. C7 states both duck interpretations directly and
does not connect the notebook purchase to either observation. C8 distinguishes
two cables from a 2 m cable length and preserves both named comparison sides
and "not longer"; it supplies no unstated arithmetic. C9 includes the explicitly
given sum while retaining the individual addends and result.

The nine complete outputs contain 110 entries, 70 distinct subjects counted
within their cases, and 83 displayed direct relationships. The reviewed fixture
declares 71 broader relationships and 23 prohibited placements. Every declared
relationship is checked beneath every copy of its parent, and every displayed
relationship must follow the reviewed relationships. Canonical-subject checks
also reject literal hashtag components, types for AmberLoop, uncertainty
qualifiers, reversed negation, missing comparison sides, unsupported units and
unstated calculated results.

The minimal ambiguity test first failed against ASv6.53 because the case was
absent. All 14 example checks, nine native prompt-revision checks and two existing
SP workflow checks then passed. The workflow checks exercise offline preparation
of 200 complete posts and numbering validation without repairs or retries.
Example parsing uses the production subjects adapter. These checks establish
agreement with the declared fixture and output contract; they do not independently
prove natural-language entailment or teacher generalization.

Shared `experiment.py revise` generated the prompt and
[ASv6.54 revision receipt](../asv6.54/ASv6.54.md.revision.json) directly against
approved ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The ASv6.54 SHA-256 is
`011dbe299b39996ea56c47e84fc3e19621960e6b4cdb477cbc3910aaccd446fd`.
Its 21,707 UTF-8 bytes are 12,321 fewer than ASv6.53, but 10,650 more than
approved ASv6.51. These are repeated input bytes per SP request, not measured
model tokens. No extra pass or runtime component is introduced.

No template, experiment or model request was created. Review the full delta
against approved ASv6.51 before authorizing the same twelve GPT-6.1 Sol xhigh
SP regression cases paired with saved ASv6.51 answers. The rule map establishes
what the examples teach; only subsequent testing can assess transfer to those
unchanged posts.
