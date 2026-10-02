# ASv6.50

Status: approved candidate, tested on GPT-6.1 Sol xhigh. The October 2
[offline audit](#offline-audit-of-saved-candidate-answers) confirms scope
failures in eight of twelve saved answers, correcting the original two. On
October 1, 2026, the user approved the full-context delta and authorized this
test. This supersedes the ASv6.49 draft. ASv6.48 remains the frozen subject
baseline. MPv3.43 remains the frozen mask working baseline. Adoption as the
subject baseline remains open.

The reports below preserve the original assessments and counts. Use the
[offline audit](#offline-audit-of-saved-candidate-answers) for corrected scope
counts and the unresolved interpretation of missing broader headings. Earlier
"Pass" cells are historical agent judgments, not current acceptance decisions.

The subsequent [ASv6.51 (approved candidate, tested on Sol xhigh)](../asv6.51/ASv6.51.md)
provides the saved comparison answers for the ASv6.55 test below. ASv6.50 and
its saved answers remain comparison evidence.

[ASv6.55 (candidate, tested on Sol xhigh)](../asv6.55/ASv6.55.md) was authorized
for testing. It removes two overlapping
examples from ASv6.54 while retaining demonstrations of every existing
instruction clause.
The test found five of twelve answers with scope failures and ten with missing
valid branches. Adoption remains open. The
[rule-to-case map](#example-correctness-and-rule-coverage) records each case's
instruction basis; the [draft audit](#asv655-consolidated-examples) records verification.
The subsequent [unchanged ASv6.54 comparison](#asv654-completed-answers-and-agent-review)
also failed, with five answers containing scope failures and eleven missing
valid branches.
The subsequent [ASv6.56 (candidate, tested on Sol xhigh)](../asv6.56/ASv6.56.md) changes only the
boiler case from ASv6.55 to demonstrate general cutting separately from cutting
for boiler repair. The [audit](#asv656-cutting-for-boiler-repair-example) records
the approved draft and updated rule map. The completed twelve-case Sol xhigh
test found four answers with scope failures and all twelve missing valid
branches; adoption remains open.
The subsequent [ASv6.57 (candidate, tested on Sol xhigh)](../asv6.57/ASv6.57.md) revises the same
case to show a quantified tube separately from its repair purpose and
purpose-qualified cutting. The [audit](#asv657-quantified-tube-and-repair-purpose-example)
records the approved candidate and updated rule map. The completed twelve-answer
Sol xhigh test found four answers with scope failures and eleven missing valid
branches. Only N063 T2 passes both reviewed checks; adoption remains open.
The current [ASv6.58 (candidate, tested on Sol xhigh)](../asv6.58/ASv6.58.md) supplies the same
repair purpose through C1's heading, preserving every subject heading and
placement. Its [audit](#asv658-purpose-supplied-by-a-heading) records 29 passing
offline checks. The user approved the wording and the same twelve-answer Sol
xhigh test. The [completed review](#asv658-completed-answers-and-agent-review)
found four answers with scope failures and all twelve missing valid branch
placements. No answer passes both reviewed checks; adoption remains open.

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

Status: approved candidate, tested on GPT-6.1 Sol xhigh. The October 2
[offline audit](#offline-audit-of-saved-candidate-answers) confirms scope
failures in five of twelve completed answers, correcting the original two.
The first evaluation was
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
number, figurative, negation and comparison cases. ASv6.54 supplied focused
cases. The user then clarified that consolidation should change the examples
themselves, while keeping every rule demonstrated.

The current map uses [ASv6.58 (candidate, tested on Sol xhigh)](../asv6.58/ASv6.58.md).
Case IDs identify its seven examples in source order. Each case contains its
complete post and expected JSON. Each of the 34 existing instruction clauses
has exactly one primary case. Nine secondary demonstrations remain because
they show a different aspect or useful contrast; each states that reason.
These assignments identify demonstrations, not exemptions: every case must
obey every applicable instruction. They are review metadata and add no fields
or rules to SP.

The five previously separate implications are folded into their originating
rows: R20 covers combinations and rejects relationships repaired only by
context; R22 covers descendants beneath every parent occurrence; R29 separates
an entity from its instance's role; R30 retains restrictions inside the child
heading. These are consequences of the existing instructions, not additional
requirements to count.

The maintained tests contain the same case IDs, purposes, primary assignments
and explained secondary assignments. "Reviewed" means the agent assessed
source support and heading relationships. The user approved testing ASv6.56,
then authorized drafting ASv6.57 after its failures and approved its test.
After that test, the user authorized the ASv6.58 heading-purpose draft for review.
The user subsequently approved its wording and the same twelve-answer Sol
xhigh test. That completed test found four answers with scope failures and
all twelve missing valid branches. Adoption remains open. Agent assessments
remain separate from user semantic judgments and adoption.

| Case | Purpose | Review |
| --- | --- | --- |
| C1 | Reference resolution and heading-established repair purpose, with general and qualified items and cutting retained. | Reviewed |
| C2 | Names, hashtags, figurative labels, rhetorical meaning and an unresolved name. | Reviewed |
| C3 | URL and opaque identifier bodies without surrounding subject evidence. | Reviewed |
| C4 | URL and identifier subjects established by prose, without a cross-link. | Reviewed |
| C5 | Two direct ambiguity interpretations, independent co-mention and statement order. | Reviewed |
| C6 | Count versus length, preserved negation, both comparison sides and no unstated arithmetic. | Reviewed |
| C7 | Explicit arithmetic result with separately retained addends and result. | Reviewed |

| ID | Existing SP instruction | Primary case and demonstration | Secondary case and distinct aspect |
| --- | --- | --- | --- |
| R01 | Build a subject index after understanding the complete post. | C1: The heading and list together establish the counted tube, its repair purpose and the cutting reference before the hierarchy is presented. | — |
| R02 | Resolve references to the most specific supported description. | C1: 'It' becomes the one tube, with its boiler-repair purpose supplied by the heading. | C2: Named referent: 'it' retains RavenWorks's stated app type and hashtag-established name. |
| R03 | Use general knowledge to clarify language, identify referents and recognize subjects. | C2: The figurative 'lifesaver' label conveys help, and the rhetorical question conveys appreciation. | — |
| R04 | Ground every entity, modifier, action and relationship in the post. | C1: The stated tube count and cutting object retain the repair purpose reasonably implied by the heading and list. | — |
| R05 | Interpret names, labels and hashtags by referent, not component words. | C2: #RavenWorks names an app; its component words yield no birds or employment subjects, and the figurative label conveys help. | — |
| R06 | Retain the name of an unresolved named subject. | C2: AmberLoop remains by name, outside the app, help and appreciation branches. | — |
| R07 | Treat URLs and opaque identifiers as providing no subject evidence. | C3: The bare URL and hexadecimal identifier yield no subjects. | C4: Relevant prose establishes topics while URL bodies still contribute no birds, repair or count. |
| R08 | Retain URL or identifier subjects established by surrounding prose. | C4: The surrounding labels establish profile URLs and event identifiers. | — |
| R09 | Give each remaining supported interpretation its own direct subject, without uncertainty qualifiers. | C5: Observation of a person's duck and observation of a person ducking appear as separate, directly stated subjects. | — |
| R10 | Do not infer relationships from co-mention alone. | C5: The notebook purchase remains independent of both observations. | — |
| R11 | Do not infer relationships from statement order alone. | C5: No chronology or causal relationship is added from the order of the observation and purchase statements. | — |
| R12 | Add no commentary about plausibility or what is unclear or unstated. | C5: Both interpretations are stated directly, without plausibility or ambiguity commentary. | C2: Unresolved name retained without commentary about its unknown type. |
| R13 | Preserve what numbers refer to. | C6: The count of two cables is distinct from the 2 m and 3 m cable lengths. | C7: Arithmetic roles distinguish addends 2 and 3 from result 5. |
| R14 | Support count or measurement interpretations and units with the post. | C6: The cable count and metre units come directly from the post. | — |
| R15 | Include calculated results only when explicitly stated. | C7: The explicitly stated result 5 appears with the calculation. | C6: No unstated 1 m difference or 5 m total. |
| R16 | Enumerate specific subjects before deriving broader headings. | C1: The counted tube and its purpose-qualified cutting remain under derived headings; JSON shows retention rather than internal reasoning order. | — |
| R17 | Include literal, nonliteral and rhetorical subjects from parts, combined parts or the whole post, including unnamed concepts. | C2: The figurative label conveys help and the rhetorical question conveys appreciation. | C6: The pair combines the count, both named cables and their stated lengths. |
| R18 | Retain individual subjects, particular instances and expressed combinations. | C6: Cable A, cable B and their stated pair remain as individual instances and an expressed combination. | C1: One tube remains alongside its repair-qualified and cutting subjects. |
| R19 | An event description must not replace its involved subjects. | C5: Ducks, people and notebooks remain alongside observation and purchase subjects. | — |
| R20 | Judge broader relationships using headings alone; a counterexample requires a broader parent. | C1: One tube and Cutting one tube can concern another purpose, so they stay outside Boiler repair despite their source context. | C6: The pair fits both cable headings; either cable can be mentioned without the other. |
| R21 | Build upward and combine shared headings. | C1: One tube for boiler repair is shared beneath One tube and Boiler repair. Cutting for boiler repair is shared beneath Cutting and Boiler repair. | — |
| R22 | Retain each enumerated subject in every branch that passes the heading test. | C1: One tube for boiler repair appears beneath every One tube and Boiler repair copy. Cutting one tube for boiler repair appears beneath every copy of its three direct broader subjects. | — |
| R23 | Give each heading and subheading its own entry. | C1: Every displayed heading and subheading has its own entry. | — |
| R24 | Return only one JSON object containing a subjects array. | C3: The output is only one JSON object with a subjects array, here empty. | C1: Nonempty output contrasts with C3's empty array. |
| R25 | Use section-style numbering, broad to specific, with parents first. | C1: Section-style numbering presents each parent before its children. | — |
| R26 | Order entry fields as number, context, subject. | C1: Every entry orders its fields as number, context, subject. | — |
| R27 | Context identifies the subject and the source establishing its meaning. | C1: Contexts identify the list's count and 'it' reference and the heading that supplies the repair purpose. | — |
| R28 | Context may describe a particular instance supporting a general heading. | C1: One tube's context describes this instance's repair purpose without restricting that general heading. | — |
| R29 | Match the heading's generality; keep instance details in subheadings without importing context restrictions. | C1: One tube and Cutting one tube retain the count but stay outside Boiler repair; their repair roles appear in context and qualified subheadings. | — |
| R30 | Make each heading understandable without the post, context or other entries. | C1: Qualified tube and cutting headings retain the count, object and boiler-repair purpose without pronouns. | — |
| R31 | A heading need not retell the post's assertion about its subject. | C1: One tube names the counted object without retelling its boiler-repair purpose. | — |
| R32 | Preserve meaning, negation and relationships in headings. | C6: The comparison retains not longer, both cable descriptions and their relationship. | — |
| R33 | Name both comparison sides when provided. | C6: The comparison names 2 m cable A and 3 m cable B. | — |
| R34 | Use concise wording. | C1: One tube concisely retains the stated count and object type. | — |

All 34 clauses have one primary assignment; the nine explained secondary
assignments bring the mapping to 43 references. Review goes in both directions:
each clause has a demonstration, and each demonstration has an instruction
basis. The examples were reviewed for source support, complete subject
retention, standalone wording and each valid relationship among their headings.
Internal reasoning order has no field in the required JSON; examples demonstrate
its visible consequences without adding a reasoning trace.

## ASv6.54 focused examples

Status: unchanged comparison candidate, tested on Sol xhigh; regression failures
found. The user's earlier "proceed" authorized this example revision and offline
verification; the latest "proceed" authorizes the twelve-answer comparison
below. ASv6.54 wording approval and adoption remain open. ASv6.51 was the last
approved candidate at that comparison; ASv6.48 remains the frozen subject baseline.

[ASv6.54 (candidate, tested on Sol xhigh)](../asv6.54/ASv6.54.md) preserves every
instruction byte from approved ASv6.51. It preserves ASv6.53's corrected lunar
case byte for byte, replaces the overloaded railway story with separate
replacement-part and combined-advice cases, and adds six language cases.
Neither MP nor the runtime workflow changes.
Case IDs in this audit refer to ASv6.54's nine examples; the current rule map
uses ASv6.58's seven examples.

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

The approved mapping cleanup first failed the strengthened coverage check because
the old assignments repeated primary rules. All 14 example checks and two SP
workflow checks passed after assigning each clause one primary case and requiring
an explanation for every secondary demonstration. The prompt, revision receipt,
example posts, expected subjects and reviewed relationships are unchanged.

Shared `experiment.py revise` generated the prompt and
[ASv6.54 revision receipt](../asv6.54/ASv6.54.md.revision.json) directly against
approved ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The ASv6.54 SHA-256 is
`011dbe299b39996ea56c47e84fc3e19621960e6b4cdb477cbc3910aaccd446fd`.
Its 21,707 UTF-8 bytes are 12,321 fewer than ASv6.53, but 10,650 more than
approved ASv6.51. These are repeated input bytes per SP request, not measured
model tokens. No extra pass or runtime component is introduced.

Drafting created no template, experiment or model request. ASv6.55 below
consolidates the examples; ASv6.54 remains unchanged as the source for
preservation checks and the subsequent comparison test.

### Authorized ASv6.54 Sol 6.1 xhigh comparison test

After reviewing ASv6.55's completed results, the user authorized testing
unchanged ASv6.54 on N063, N074, N096 and N100 with three independent trials
per post. The only prompt difference from ASv6.55 is the retained lunar and
combined-advice examples: every instruction byte and all seven common example
blocks match. This comparison examines consolidation before another edit;
it does not establish a general failure rate or imply adoption.

Native `experiment.py revise` generated the reusable
[ASv6.54 post template](../../experiment_specs/asv6.54-hr01-post-template.txt)
and [revision receipt](../../experiment_specs/asv6.54-hr01-post-template.txt.revision.json)
against the approved ASv6.51 post template, preserving the post wrapper.
The template is the unchanged ASv6.54 source followed by that wrapper; its
SHA-256 is
`b19683efb32a3a1d45a96274977838c8433ada8f568f13d98dde7101d3686b0e`.

Three native `prepare --from ... --repeat` experiments inherit the corresponding
ASv6.55 trials. All four complete posts, evidence and model settings match;
all four saved outputs per trial are frozen as comparison answers without
regeneration. Twenty-seven ASv6.55 source files are hash-pinned and unchanged.
The ignored experiments are
`sse_multivector/experiments/asv6.54-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.54-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.54-sol61-xhigh-sp-scope-regression-t3/`.

The model is exact `gpt-6.1-sol`, reasoning `xhigh`, through the existing
`openai-codex` subscription WebSocket route: four concurrent cases per trial,
1,800-second timeout and no output cap or paid fallback. Native runs allow at
most eight new attempts per trial, preserving the provider-only, two-attempt
retry policy. These allowances include retries and do not authorize additional
trials. Incremental subscription cash is zero; quota consumption is unmeasured.
The ledger's monetary totals were validated before inference.

All 26 offline prompt-revision, example and SP workflow checks passed before
inference. All twelve answers completed on their first attempt with valid JSON
and native receipts. There were no execution failures, retries, repairs,
reused answers, regenerated baselines or output-truncation requests. All entry
fields retain the number/context/subject order. The source prompt, template and
27 pinned ASv6.55 files remain unchanged after execution and native reviews.
No user semantic verdict, source-prompt change or adoption is implied.

### ASv6.54 completed answers and agent review

Agent review rejects all twelve answers. Five answers contain heading-alone
scope failures; eleven omit an enumerated heading from a valid broader branch.
The corresponding ASv6.55 figures were five and ten. The unchanged nine-example
prompt still exhibits both patterns, so consolidation does not explain their
presence by itself. These small independent samples do not establish general
failure rates or prove that ASv6.54 is worse. The source instructions are
unchanged in both prompts.

The cells below show scope assessment and hierarchy-entry counts. "Pass" means
no confirmed scope failure was found; every answer still fails at least one
reviewed requirement.

| Post | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| N063 | Pass; 143 entries | Fail; 153 entries | Pass; 159 entries |
| N074 | Pass; 169 entries | Pass; 140 entries | Pass; 151 entries |
| N096 | Fail; 266 entries | Fail; 242 entries | Fail; 224 entries |
| N100 | Pass; 243 entries | Pass; 191 entries | Fail; 215 entries |

Representative scope findings for the five failing answers are:

- **N063 T2, 10 -> 10.1, and N096 T3, 1.7 -> 1.7.1:** Edible oils -> Olive oil.
  The generic child includes lampante olive oil that is unfit for human
  consumption without further processing. The
  [USDA olive-oil grades](https://www.ams.usda.gov/grades-standards/olive-oil-and-olive-pomace-oil-grades-and-standards)
  identify refining and nonfood purposes for that grade. A post about it fits
  the child without fitting the edible parent; this source's cooking use cannot
  narrow the heading.
- **N096 T1, 3 -> 3.1:** Food preparation -> Ingredient preparation. Preparing
  ingredients for soap fits the generic child without fitting Food preparation.
  The child lacks the food restriction established by this particular recipe.
- **N096 T2, 3 -> 3.1:** Cooking -> Chopping. Chopping wood fits the generic
  child without fitting Cooking. Cooking oils -> Olive oil at 1.6 -> 1.6.1 also
  lacks the restriction to a cooking grade or role.
- **N100 T3, 1.1.4 -> 1.1.4.1:** Beef by-products -> Beef fat. A post about fat
  within an intact beef cut fits Beef fat without requiring a processing
  by-product role. The generic connective-tissue and myoglobin children have
  the same role problem; the trimming context supplies it only for this source.

For each omission below, the child already occurs elsewhere in the answer and
fits the stated broader heading by itself, but is absent beneath every listed
parent occurrence. The child position is representative when it has several
copies. Narrower descendants do not retain the separately enumerated heading
required by R22.

| Post/trial | Existing child occurrence | Valid broader branch missing it |
| --- | --- | --- |
| N063 T1 | 10.1 Vegetable broth | 6 Vegetables |
| N063 T3 | 10.1 Vegetable broth | 5 Vegetables |
| N074 T1 | 1.3.1 Plant-based diets | 5.1 Plant foods |
| N074 T2 | 7.1 Weariness with diet narratives | 1.1.6 Diet narratives |
| N074 T3 | 11.1 Dietary advice | 1 Diets |
| N096 T1 | 3.1.1 Finely chopped vegetables | 1.2 Vegetables |
| N096 T2 | 6.1.1 Tinned tomatoes | 1.2.5 Tomatoes |
| N096 T3 | 3.6 Cooking according to packet instructions | 10 Cooking instructions |
| N100 T1 | 15.1.1.3 Nesco VS-12 food vacuum sealer rated much better than previously used FoodSaver food vacuum sealers | 15.1.2.1, 15.1.3.2, 16.1.2.1 and 16.1.3.2 Past use of FoodSaver food vacuum sealers |
| N100 T2 | 14.1.1.2 New Nesco VS-12 vacuum sealer rated much better than previously used FoodSaver vacuum sealers | 14.2.1 and 14.3.2 Past use of FoodSaver vacuum sealers |
| N100 T3 | 13.1 Vacuum sealer evaluations | 10 Vacuum sealers |

No confirmed valid-branch omission was found in N063 T2; its scope failure
still rejects the answer. Core dish/ingredient, diet/advice, recipe/quantity/
action/time and meat/animal/equipment/purchase subjects are largely retained.
N074 T1 has no separate Nostr entry, though its Nostr diet headings remain.
That preservation does not prove full individual-subject or interpretation
coverage.

All three N100 answers retain both the water/seeds-only plan and a reading
that includes saved myoglobin for chickens. The doubled "some some" source
remains ambiguous: retaining both readings is not a user verdict that the
writer actually plans to feed myoglobin to chickens. No answer asserts that
the writer sealed this beef. A keyword check for uncertainty/plausibility
commentary found no such qualifiers in the saved entries.

Native `experiment.py review --role agent` records one reject per answer and
no user judgments. These are agent semantic assessments with source-bound
outputs, exact positions and counterexamples, not an independent entailment
oracle. JSON/receipt validity and the 26 passing offline checks remain separate
from the failed semantic regression. Neither prompt was edited or adopted;
ASv6.48 remains frozen.

Native usage is preserved separately for each trial. Reasoning tokens are
already included in output tokens:

| Trial | New attempts | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Catalog estimate USD |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 23,534 | 0 | 103,145 | 61,537 | 1.078518 |
| T2 | 4 | 23,534 | 0 | 87,527 | 50,020 | 0.922338 |
| T3 | 4 | 23,534 | 0 | 87,718 | 51,864 | 0.924248 |

Every attempt has native usage and a catalog estimate; provider billing is
unavailable. Catalog estimates are not subscription charges or measured quota
consumption; incremental cash remains zero. ASv6.54 repeats 5,185 additional
prompt bytes per request compared with ASv6.55. Entry counts vary in both
directions against the paired answers: ASv6.55 counts were N063 161/186/182,
N074 163/169/154, N096 260/225/210 and N100 230/193/211. Restoring more examples
did not prevent these failures and added repeated input at corpus scale.

The user subsequently authorized the focused [ASv6.56 draft](#asv656-cutting-for-boiler-repair-example).
It revises the existing boiler case to retain general cutting separately from
cutting for boiler repair and repeats qualified subjects in every valid broader
branch. Review the source, subjects, relationships and rule map before further
inference. The user subsequently approved ASv6.56 and authorized the same
twelve-case Sol xhigh comparison; adoption remains open.

## ASv6.55 consolidated examples

Status: candidate, tested on Sol xhigh; regression failures found. The user
explicitly confirmed that the next prompt should consolidate overlapping
examples while keeping every rule demonstrated, then explicitly authorized
testing ASv6.55 on the same twelve
GPT-6.1 Sol xhigh regression cases. ASv6.51 supplies the saved comparison
answers; ASv6.48 remains frozen. Adoption remains open.

[ASv6.55 (candidate, tested on Sol xhigh)](../asv6.55/ASv6.55.md) removes ASv6.54's
lunar and combined-advice cases. Their instruction demonstrations are retained
in existing cases: the boiler case resolves a reference across sentences,
distinguishes entities from roles and repeats descendants beneath every valid
parent; the app case resolves a pronoun and conveys unnamed, figurative and
rhetorical subjects; the cable case retains both individual cables and their
combination. No instruction text or retained example is rewritten.

This consolidation reduces demonstration variety: the draft no longer includes
an astronomy topic or advice modality. All existing clauses and the five tracked
implications still have demonstrations. This establishes instruction coverage,
not that the removed examples have no effect on model behavior.

The bare/labeled identifier pair remains because identical bodies provide no
subject evidence while surrounding prose can establish subjects. Both number
cases remain because they contrast an unstated calculated result with an
explicit result, and distinguish counts, measurements and arithmetic roles.
The ambiguity case retains an unrelated purchase, demonstrating that neither
co-mention nor statement order establishes a relationship.

The seven complete outputs contain 80 entries, 52 distinct subjects counted
within cases and 61 displayed direct relationships. The fixture declares 53
broader relationships and 18 prohibited placements. The two additional cable
guards reject nesting either individual cable beneath their pair, preserving
the component/combination direction previously demonstrated by advice.
Every declared relationship is checked beneath every parent occurrence; every
displayed relationship must follow the reviewed relationships. The rule map
assigns all 34 clauses one primary case and explains nine secondary
demonstrations, for 43 references.

The minimal consolidation check first failed against ASv6.54 because both
overlapping cases were still present. All 15 example checks, nine native
prompt-revision checks and two existing SP workflow checks now pass. The
production subjects adapter parses every retained output; the workflow checks
exercise preparation of 200 complete posts and numbering validation without
repairs or retries. A preservation check verifies that the approved instructions
and all seven retained example blocks are byte-identical to their sources.
The fixture and agent semantic review are not independent proofs of entailment
or teacher generalization.

Shared `experiment.py revise` generated the prompt and
[ASv6.55 revision receipt](../asv6.55/ASv6.55.md.revision.json) directly against
approved ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The ASv6.55 SHA-256 is
`e96764bc92eeaccbd6b8376ad089c4b1afb892a31f0fbab9b2cf69e697dade84`.
Its 16,522 UTF-8 bytes are 5,185 fewer than ASv6.54 (24% smaller), but 5,465
more than approved ASv6.51. These are repeated input bytes per SP request,
not measured model tokens. No runtime component or extra model pass is added.

Drafting made no model requests. The subsequent authorized test below checks
transfer to the unchanged regression posts.

### Authorized Sol 6.1 xhigh regression test

The user authorized the same twelve-answer design after reviewing the ASv6.55
consolidation and rule coverage: N063, N074, N096 and N100, with three independent
answers per post. Three native `prepare --from ... --repeat` experiments pair
each trial with its corresponding completed ASv6.51 retry trial. Complete
original post text, source evidence, output schema and model settings are
preserved; saved baselines are not regenerated.

Shared `experiment.py revise` derives the
[ASv6.55 post template](../../experiment_specs/asv6.55-hr01-post-template.txt)
and its [native receipt](../../experiment_specs/asv6.55-hr01-post-template.txt.revision.json)
from the approved ASv6.51 template. The source prompt and unchanged `{POST}`
wrapper match exactly. The ASv6.55 template SHA-256 is
`5a321bf7146bc5d577fbd8f5d32a4fc11ac3adb7090c2f76988b43c2145720a5`;
its baseline template SHA-256 is
`8c8ef84d5c27726c710fcb6bf91b107df93abe157ce1cd63a2286b3d65a72003`.

Preflight verifies all twelve cases, four valid saved baselines per trial and
unchanged GPT-6.1 Sol xhigh subscription settings: WebSocket transport,
1,800-second timeout, four concurrent requests per trial and no output cap.
Twenty-seven saved ASv6.51 files are hash-pinned before inference. Each native
run allows at most eight new attempts, retaining the shared provider-only retry
policy and two-attempt maximum per case. Incremental subscription cash is zero;
quota consumption is unmeasured and no paid fallback is configured.

The ignored experiments are
`sse_multivector/experiments/asv6.55-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.55-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.55-sol61-xhigh-sp-scope-regression-t3/`.
All twelve answers completed with valid JSON and valid native receipts, each
on its first attempt. There were no execution failures, repairs, retries,
truncation requests, reused answers or regenerated baselines. Entry fields
retain the required number/context/subject order. Source and template hashes,
and all 27 pinned ASv6.51 files, remain unchanged.

### Completed answers and agent review

ASv6.55 does not pass the regression check. Agent review found five of twelve
answers with a heading-alone scope failure, compared with two in the saved
ASv6.51 cohort. Ten answers also omit an enumerated heading from a valid
broader branch. This is a sample comparison, not an estimate of general failure
rates or proof that removing the two examples caused the difference. The
[unchanged ASv6.54 comparison](#authorized-asv654-sol-61-xhigh-comparison-test)
was subsequently authorized and completed: it also has five answers with scope
failures, and eleven with missing valid branches.

The following cells show the scope assessment and number of hierarchy entries.
"Pass" means no confirmed scope failure was found in that review; it does not
mean every SP requirement passed.

| Post | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- |
| N063 | Pass; 161 entries | Pass; 186 entries | Fail; 182 entries |
| N074 | Pass; 163 entries | Pass; 169 entries | Pass; 154 entries |
| N096 | Fail; 260 entries | Fail; 225 entries | Fail; 210 entries |
| N100 | Pass; 230 entries | Pass; 193 entries | Fail; 211 entries |

The five scope findings are:

- **N063 T3, 8.1 -> 8.1.1:** Edible fats and oils -> Vegetable oils. The generic
  child includes nonedible oils. Tung oil is a concrete counterexample,
  explicitly classified as a nonedible vegetable oil in the
  [USDA Fats and Oils report](https://ers.usda.gov/sites/default/files/_laserfiche/outlooks/37342/32910_ius6c_002.pdf).
  The edible olive-oil instance in this source cannot narrow that generic heading.
- **N096 T1, 1.6 -> 1.6.1, and T3, 1.7 -> 1.7.1:** Cooking oils -> Olive oil.
  The child itself does not specify a cooking role; another post can concern
  olive oil used outside cooking. This uses the same entity/role criterion as
  the saved ingredient-role failures, rather than borrowing the recipe context.
- **N096 T2, 1.2.1.2 -> 1.2.1.2.1:** Translucent sautéed onions -> Moving
  sautéed ingredients to the pan's side and adding 500 g ground beef when onions
  turn translucent, for spaghetti Bolognaise. The child calls the moved
  ingredients sautéed, but does not identify the translucent onions as those
  ingredients. A post can move sautéed celery while separately cooked onions
  become translucent. The full source supplies the missing sautéed-onion
  relationship; the child heading alone does not.
- **N100 T3, 6 -> 6.4:** Food preparation -> Tallow production. Generic tallow
  production can have a nonfood purpose. The
  [EPA vegetable-oil processing analysis](https://www.epa.gov/sites/production/files/2020-07/documents/vegetable-oil_eia_neshap_final_01-2001.pdf)
  includes inedible tallow among industrial substitutes. Neither this source's
  cooking hashtag nor its planned fat use supplies a food restriction in the
  generic child heading.

These are agent semantic assessments of the agreed heading test, not an
independent entailment oracle or user verdict. The native reviews retain exact
source-bound outputs and the counterexamples used for each assessment.

The valid-branch omissions concern headings already present elsewhere in the
same answer. Each listed child fits the named broader heading by itself, but
is absent beneath the indicated occurrence. A narrower descendant does not
retain the separately enumerated heading required by R22.

| Post/trial | Existing child occurrence | Valid broader branch missing it |
| --- | --- | --- |
| N063 T1 | 11.1 Vegetable broth | 7 Vegetables |
| N063 T3 | 12.1.1 Sea salt as a seasoning | 11.1 Sea salt |
| N074 T1 | 10.1 Weariness of diet narratives | 1.7 and 9.1 Diet narratives |
| N074 T2 | 12.1 Weariness of dietary narratives | 1.9 and 9.1 Dietary narratives |
| N074 T3 | 9.1.1 Advice to eat real food | 1.6 and 12.1 Dietary advice |
| N096 T1 | 6.1.1 Tinned tomatoes | 1.5 Tomatoes |
| N096 T2 | 3.10.1 Adding garlic after a few minutes of sautéing | 3.3 Adding cooking ingredients |
| N096 T3 | 1.10.1.1 Finely chopped vegetables | 1.3 Vegetables |
| N100 T1 | 1.3.1 and 4.1.1 Beef fat for making tallow | 8 Tallow |
| N100 T3 | 6.4 Tallow production | 3.2 Tallow |

No confirmed scope or branch-retention failure was found in N063 T2 or N100 T2.
N100 T2 remains uncertain overall: its source's doubled "some some" can be read
as referring to saved myoglobin for chickens, alongside the water/seeds-only
reading. It retains only the latter; whether the former is sufficiently
supported to require a separate subject under the ambiguity rule needs a
semantic verdict. T1 and T3 retain both readings.
No candidate answer assumes that the writer sealed this beef.

Core dish/ingredient, diet/advice, recipe/quantity/action/time and
meat/animal/equipment/purchase subjects remain represented. That does not
establish complete interpretation coverage or satisfy every valid-branch
requirement. All twelve hierarchies are larger than their paired ASv6.51
answers: the respective saved entry counts were N063 81/78/85, N074 89/91/87,
N096 143/117/158 and N100 124/141/128. More output did not prevent these omissions.
The repeated input and larger output matter when assessing corpus-scale use.

Native `experiment.py review --role agent` records ten rejects, one accept
(N063 T2) and one uncertain assessment (N100 T2). These judgments combine scope,
branch retention and interpretation coverage; they are not just the scope
matrix above. No user semantic review or adoption was recorded. ASv6.48 remains
the frozen subject baseline, and neither ASv6.55 nor MP was changed during testing.

Native usage remains separate for each trial; reasoning tokens are already
included in output tokens:

| Trial | New attempts | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Catalog estimate USD |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 18,354 | 0 | 95,230 | 53,105 | 0.989008 |
| T2 | 4 | 13,874 | 4,480 | 95,898 | 56,122 | 0.987176 |
| T3 | 4 | 18,354 | 0 | 87,556 | 48,866 | 0.912268 |

Every attempt has native usage and a catalog estimate. These estimates are not
subscription bills or measured quota consumption; provider-reported billing
is unavailable and incremental cash remains zero. The 26 offline example,
revision and SP workflow checks passed before inference. Native case parsing
and receipt validation pass after the run; the semantic regression does not.

The user subsequently authorized unchanged ASv6.54 on the same twelve cases,
paired with these saved ASv6.55 answers, to examine the effect of consolidating
the examples before another edit. That test completed above and still exhibits
both failure patterns. The rule map establishes demonstration coverage; these
results show that coverage alone does not establish teacher generalization.

## ASv6.56 cutting-for-boiler-repair example

Status: candidate, tested on Sol xhigh. After the unchanged ASv6.54 comparison failed, the user
authorized drafting a focused change to the existing boiler example, with a
full-context delta for review before model testing. On October 2, 2026, the user
approved the delta and authorized the same twelve-case Sol xhigh comparison.
Adoption remains open. ASv6.48 remains the frozen subject
baseline; no MP work is included.

[ASv6.56 (candidate, tested on Sol xhigh)](../asv6.56/ASv6.56.md) replaces only C1 from ASv6.55.
The source is now: "Cutting for boiler repair on Bracken. Bracken is a steam
locomotive." The source directly states cutting's purpose and resolves Bracken's
type in the next sentence. It adds no cutting tool, material, replacement part,
worker or completion claim.

General **Cutting** stays outside **Boiler repair**, because another post about
cutting can concern a purpose other than boiler repair. **Cutting for boiler
repair** fits both headings and appears beneath every occurrence of each.
General **Boiler repair** stays outside **Steam locomotive boilers**, because
another post about boiler repair can concern a boiler of another type.
Bracken, its boiler, the named repair and the named cutting remain separately
represented; each qualified heading retains the locomotive type. Every copy of
the boiler retains its named repair, and every applicable branch retains the
named cutting subject. Neither the action's instance-specific purpose nor the
boiler's repair role is imported into a general heading from its context.

The agent reviewed all twelve C1 headings against the two source sentences,
all fourteen declared broader relationships and all eight prohibited placements.
The [current rule map](#example-correctness-and-rule-coverage) retains exactly
one primary assignment for each of 34 clauses and nine explained secondary
demonstrations. The five tracked implications remain folded into their original
rules. The six other example blocks and all instruction bytes remain identical
to their sources. The replacement case has 29 entries; all seven cases together
contain 95 entries, 56 distinct subjects counted within cases and 75 displayed
direct relationships. The fixture declares 58 broader relationships and 23
prohibited placements. No eighth example or new instruction is added.

The minimal cutting-purpose check first failed against ASv6.55 because its case
contained no Cutting subject. All sixteen example checks, nine native revision
checks and two existing SP workflow checks pass. The production subjects adapter
parses every example, and each reviewed relationship is checked beneath every
parent occurrence. Preservation checks pin the instructions to approved ASv6.51,
the unchanged six blocks to ASv6.55, and ASv6.55's earlier consolidation to ASv6.54.
These checks establish fixture consistency; the agent's source and relationship
review does not establish that the draft generalizes on model outputs.

Shared `experiment.py revise` generated the prompt and
[ASv6.56 revision receipt](../asv6.56/ASv6.56.md.revision.json) directly against
then-approved ASv6.51 SHA-256
`db164a973f81791445b1816a9a2cc79da36e9e20a294b1dea9292552ae298cc7`.
The receipt reconstructs the exact draft, whose SHA-256 is
`a1a1292b45ab5afa9a2a87c25ac0434e7e2b4428b518767f846e67130ce4b4d2`.
The source is 19,256 UTF-8 bytes: 2,734 more than ASv6.55, 2,451 fewer than
ASv6.54 and 8,199 more than approved ASv6.51. The added bytes repeat per SP
request; actual model tokens are unmeasured. No runtime component or additional
model pass is introduced. ASv6.51, ASv6.54 and ASv6.55 remain hash-identical.

Both full-context diffs are ignored review artifacts in
`target/sp-scope-regression-v1/`: `asv656-full-context.diff` shows approved
ASv6.51 to ASv6.56; `asv656-from-asv655-full-context.diff` isolates this turn's
change from ASv6.55. Drafting created no model template, experiment or inference
request. The subsequently authorized test below checks whether the demonstrated
distinction transfers to the saved failure topics.

### Authorized ASv6.56 Sol 6.1 xhigh regression test

The user approved the focused delta and authorized N063, N074, N096 and N100
with three independent answers per post. Native `prepare --from ... --repeat`
pairs each trial with the corresponding saved ASv6.55 trial, preserving the
complete original posts, evidence, schema and runner settings. ASv6.51 and
ASv6.54 remain saved comparison evidence; no baseline is regenerated.

Native `experiment.py revise` derives the reusable
[ASv6.56 post template](../../experiment_specs/asv6.56-hr01-post-template.txt)
and [revision receipt](../../experiment_specs/asv6.56-hr01-post-template.txt.revision.json)
directly from the approved ASv6.56 source. It adds only the existing `{POST}`
wrapper, byte-identical to the ASv6.51 and ASv6.55 wrappers. The template
SHA-256 is `d984a8f4ea4e9838a91f58eb967d0ee7be0f3cb95e159bd39a4dc3a597ca1964`.

Preflight found four valid saved baselines and four new, nonreusable requests
per trial. All 27 offline checks pass. The approved source, new template and
all 27 saved ASv6.55 files are hash-pinned; they remain unchanged after preparation.
The ignored experiments are
`sse_multivector/experiments/asv6.56-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.56-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.56-sol61-xhigh-sp-scope-regression-t3/`.

The exact model is `gpt-6.1-sol`, effort `xhigh`, through the subscription
WebSocket route: four concurrent cases per trial, 1,800-second timeout, no
output cap or paid fallback. Each native run allows at most eight new attempts,
including only provider-eligible retries, with two attempts maximum per case.
This does not authorize additional trials. The ledger's monetary totals are
valid; incremental subscription cash is zero and quota consumption is unmeasured.
Preparation made no model calls. All twelve answers subsequently completed on
the first attempt with valid JSON and native receipts. There were no execution
failures, retries, repairs, reused answers or regenerated baselines. Field order
remains number/context/subject. All 29 pinned source, template and saved-baseline
files remain unchanged after execution and native reviews. The complete-output
agent reviews below assess relationships, retained subjects and every valid
branch; no user semantic judgment or adoption is inferred.

### ASv6.56 completed answers and agent review

ASv6.56 does not pass. Agent review found four of twelve answers with a
heading-alone parent-scope failure and all twelve missing an enumerated
subject from a valid broader branch. The corresponding ASv6.55 counts were
five and ten; ASv6.54 had five and eleven. These are small sets of stochastic
answers, not estimates of general failure rates or proof that the example
change improved scope handling or worsened coverage. All twelve current native
agent verdicts are reject; no user verdict is recorded.

| Post | T1 scope / entries | T2 scope / entries | T3 scope / entries | Answers missing valid branches |
| --- | --- | --- | --- | --- |
| N063 | Pass / 149 | Pass / 167 | Fail / 202 | 3 of 3 |
| N074 | Pass / 155 | Pass / 158 | Pass / 156 | 3 of 3 |
| N096 | Fail / 211 | Fail / 199 | Fail / 296 | 3 of 3 |
| N100 | Pass / 225 | Pass / 229 | Pass / 261 | 3 of 3 |

Pass means no confirmed scope failure was found in that complete-output review;
it does not mean the answer passes coverage or every other instruction.
Each failing scope answer has a displayed edge and a heading-only counterexample:

| Answer | Displayed parent → child | Counterexample |
| --- | --- | --- |
| N063 T3 | 1.7 Edible fats and oils → 1.7.1 Olive oil | Generic olive oil includes lampante grades that require processing before human consumption. The post's EVOO context cannot make that general heading edible. |
| N096 T1 | 3 Cooking → 3.5 Mixing ingredients | Mixing ingredients for paint can fit the child without cooking. The food restriction is absent from the heading. |
| N096 T2 | 3.1 Water used in cooking → 3.1.1 One tin of water | A tin of water for watering plants can fit the child without retaining the cooking purpose. |
| N096 T3 | 10 Cookware → 10.1 Pans | A pan for collecting drained engine oil can fit the generic child without being cookware. The cooking type appears only in this post's context. |

The olive-oil counterexample is supported by the primary
[USDA olive-oil grade definitions](https://www.ams.usda.gov/grades-standards/olive-oil-and-olive-pomace-oil-grades-and-standards),
checked October 2, 2026. Edible oils → Olive oil also appears in N096 T1
(1.5 → 1.5.1) and T2 (1.6 → 1.6.1). N096 T2 additionally nests Finely chopping
vegetables (6.8.1.1) beneath Chopping cooking ingredients (6.8.1); chopping
vegetables for compost does not retain the cooking role. These additional
edges are in already-counted answers. N096 T3 correctly places generic olive
oil beneath Oils, and N063 T2 explicitly uses Edible olive oils.

Every missing placement below was checked against the full returned hierarchy,
including every occurrence of the parent. A narrower instance does not replace
the enumerated general subject. These are semantic agent assessments; different
equivalent wording is allowed, and the source facts and relationships remain
separate from any user judgment.

| Answer | Retained subject and its position(s) | Missing broader placement(s) |
| --- | --- | --- |
| N063 T1 | Culinary ingredients, 2.2 | Cooking, 2.1 |
| N063 T2 | Vegetable broth, 1.9.1 | Vegetables, 1.5 |
| N063 T3 | Cooking ingredients, 2.1 and 3.1 | Food and drink, 1 |
| N074 T1 | Online clicks generated by diets, 3.1.1 | Diets, 1 |
| N074 T2 | Dietary advice, 1.9 | Food consumption, 9 |
| N074 T3 | Weariness with diet narratives, 12.1 | Diet narratives, 1.7 and 11.1 |
| N096 T1 | Cooking ingredients, 1.9 | Cooking, 3 |
| N096 T2 | Finely chopping vegetables, 6.8.1.1 | Vegetables, 1.3 |
| N096 T3 | Food preparation, 9.1 | Food, 1 |
| N100 T1 | About 3 lb of beef fat for tallow production, 2.1.3.1.1 and 4.1.1.1 | Tallow production, 5.1 |
| N100 T2 | Vacuum sealer purchases, 13.2 | Vacuum sealers, 12.1 |
| N100 T3 | New Nesco VS-12 vacuum sealer better than previously used FoodSaver vacuum sealers; seven copies | Previous use of FoodSaver vacuum sealers, 15.1.1.2.1.1, 15.1.1.3.2, 16.1.1.2.1.1, 16.1.1.3.2 and 22.1.1.2 |

N100 T3's comparison copies are at 15.1.1.1.1.3, 15.1.1.2.1.2, 15.1.1.4.1,
16.1.1.1.1.3, 16.1.1.2.1.2, 16.1.1.4.1 and 21.1.1.1. None occurs beneath
any of the five past-use entries. The specific comparison is present, but its
placements remain incomplete.

The answers retain N063's fifteen ingredients and dish; N074's comparisons,
mother/10-year-old example, Bitcoin narrative, attribution and individual plus
combined advice; N096's ingredient quantities, yield, actions, heat levels and
simmering time; and N100's price, steak count/thickness, trimming quantities and
purposes, dog food, chicken provisions and sealer details. This does not
establish exhaustive coverage. N096 T1 has thirteen terminal copies of its
named recipe's ingredient heading. Its ingredient quantities remain in general
branches, without recipe-qualified counterparts beneath that heading. T2's
named recipe entries are also terminal. Moving the general quantity headings
under the recipe without retaining the recipe role would recreate the scope
failure; the supported general and qualified subjects must both remain.

N100 T1 represents only the water/seeds reading for chickens. T2 and T3 also
represent the possible myoglobin-for-chickens reading. The doubled "some some"
source remains ambiguous; the missing reading in T1 is a separate ambiguity-
coverage caveat, without an invented user grounding verdict. No answer claims
that the purchased beef was vacuum-sealed. N074's wording of the comparative
controversy exception remains a separate semantic caveat. No unstated
arithmetic result was identified. No answer was repaired or regenerated.

Native usage for the four new attempts in each trial is recorded below.
Output already includes reasoning; these columns must not be added together
as separate output charges. No cross-trial token or cost total is assembled.

| Trial | New attempts | Input tokens | Cached input | Output tokens | Reasoning tokens | Catalog estimate, USD |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 21,382 | 0 | 91,404 | 53,241 | 0.956804 |
| T2 | 4 | 11,142 | 10,240 | 90,365 | 51,471 | 0.926958 |
| T3 | 4 | 16,134 | 5,248 | 100,344 | 53,157 | 1.0362328 |

Every attempt has native usage and a catalog estimate; provider billing is
unavailable. The estimates are not subscription charges or measured quota
consumption; incremental cash is zero. Cached input does not mean an answer
was reused: all twelve were independent new attempts. ASv6.56 repeats 2,734
additional prompt bytes per request compared with ASv6.55. The 27 offline
checks passed before inference, and native parsing and receipt validation pass
after execution; the semantic regression does not. ASv6.48 remains frozen,
with no adoption or MP change.

A useful proposed next step is to revise the existing boiler case to show a
quantified general item separately from its repair role, while retaining the
action-purpose demonstration and every rule mapping. This would demonstrate the
distinction behind the One tin of water failure and missing recipe-qualified
quantities with a short example outside food. The user subsequently authorized
the ASv6.57 draft below, then approved the same twelve-answer Sol xhigh test.

## ASv6.57 quantified tube and repair-purpose example

Status: approved candidate, tested on Sol xhigh. On October 2, 2026, after the ASv6.56 results, the user
authorized revising the existing boiler case to demonstrate a quantified item
separately from its repair purpose and presenting the delta for review.
The user subsequently approved ASv6.57 for the same twelve-answer Sol xhigh
test. Adoption remains open; ASv6.48 remains the frozen subject baseline.

[ASv6.57 (candidate, tested on Sol xhigh)](../asv6.57/ASv6.57.md) replaces only C1. Its post is:
"One tube for boiler repair. Cutting it for that repair." The second sentence's
"it" refers to the counted tube, and "that repair" refers to boiler repair.
The qualified headings retain both references' supported meaning. The source
does not specify a replacement, material, dimensions, tool, worker or completed
repair; none is added. It does not establish that the tube itself is a boiler
component, so the headings do not call it a boiler tube.

The count distinguishes **One tube** from its broader **Tubes** heading; it does
not establish a repair purpose by itself. One tube cut for an art project fits
**One tube** and **Cutting one tube** without fitting **Boiler repair**. Both
general subjects remain outside that branch. Their source contexts may describe
the repair purpose, but cannot restrict the headings. The qualified subjects
retain that purpose and appear beneath every valid broader subject:

| Retained subject | Broader subjects requiring its placement |
| --- | --- |
| One tube for boiler repair | One tube; Boiler repair |
| Cutting one tube | One tube; Cutting |
| Cutting for boiler repair | Cutting; Boiler repair |
| Cutting one tube for boiler repair | One tube for boiler repair; Cutting one tube; Cutting for boiler repair |

Boiler repair remains beneath both Boilers and Repair. Every occurrence of
each listed parent retains its applicable child. Designating a tube for repair
does not itself establish cutting; the general repair-qualified tube heading
therefore stays outside Cutting. Generic boiler repair and cutting for boiler
repair need not involve a tube, so neither is nested under Tubes. These
contrasts demonstrate the existing heading-only relationship test without
adding instructions or an eighth case.

The agent reviewed all ten C1 headings against both source sentences, all
twelve declared broader relationships and eleven prohibited placements.
The [current rule map](#example-correctness-and-rule-coverage) retains all 34
primary assignments and nine explained secondary demonstrations. Its five
tracked implications remain within R20, R22, R29 and R30. Removing Bracken
removes repeated locomotive branches; reference resolution now uses "it" and
"that repair", and the explicit tube type remains in every qualified heading.
All instruction bytes and the other six example blocks are identical to
approved ASv6.56. The replacement case has 23 entries instead of 29. All seven
cases together contain 89 entries, 54 distinct subjects counted within cases
and 69 displayed direct relationships. The fixture declares 56 broader
relationships and 26 prohibited placements.

The new quantified-purpose check first failed against ASv6.56 because its case
contained no One tube subject. All seventeen example checks now pass, along
with nine native revision checks and two existing SP workflow checks. These
exercise the production subjects validator, native revision CLI and existing
SP preparation/execution paths without provider calls. The fixtures check
every parent occurrence, negative placements, all rule assignments, field
order and preservation. These checks establish example and fixture consistency;
they do not establish model generalization.

Native `experiment.py revise` generated the prompt and
[ASv6.57 revision receipt](../asv6.57/ASv6.57.md.revision.json) directly against
approved ASv6.56 SHA-256
`a1a1292b45ab5afa9a2a87c25ac0434e7e2b4428b518767f846e67130ce4b4d2`.
One exact edit replaces C1; the receipt reconstructs the exact draft. ASv6.57
SHA-256 is
`0257ef96bf407d2941d16c26c2e4fecf67bacbe7183d1bbc14c3001e6b07bdaf`.
Its source is 18,136 UTF-8 bytes, 1,120 fewer than ASv6.56. Those bytes repeat
per SP request; model token counts are unmeasured. No runtime component or
additional model pass is introduced. All 29 pinned ASv6.56 source/template and
saved ASv6.55 files remain unchanged.

The full-context ASv6.56 → ASv6.57 delta is an ignored review artifact at
`target/sp-scope-regression-v1/asv657-full-context.diff`; its exact authoring
edits are ignored alongside it. Drafting prepared no model template, experiment
or inference request. The subsequently authorized test below checks whether
the quantified-purpose distinction transfers beyond this example.

### Authorized ASv6.57 Sol 6.1 xhigh regression test

The user approved testing the candidate on N063, N074, N096 and N100 with three
independent answers per post. Native `prepare --from ... --repeat` pairs each
trial with the corresponding saved ASv6.56 trial, preserving complete original
posts, review evidence, schema and runner settings. No baseline is regenerated.

Native `experiment.py revise` derives the reusable
[ASv6.57 post template](../../experiment_specs/asv6.57-hr01-post-template.txt)
and [revision receipt](../../experiment_specs/asv6.57-hr01-post-template.txt.revision.json)
directly from the approved ASv6.57 source. It adds only the existing `{POST}`
wrapper, byte-identical to the ASv6.56 and earlier comparison wrappers. The
template SHA-256 is
`9f5d473433ebf8ea9afc5a13c68b4bcdcc75d6135641182ddd00eb0b12c6907e`.

Preflight found four valid saved baselines and four new, nonreusable requests
per trial. The draft's 28 offline checks passed, and native template receipt
reconstruction and preparation validation pass. The approved source, new
template and all 27 saved ASv6.56 files are hash-pinned; all 29 remain unchanged
after preparation. The ignored experiments are
`sse_multivector/experiments/asv6.57-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.57-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.57-sol61-xhigh-sp-scope-regression-t3/`.

The exact model is `gpt-6.1-sol`, effort `xhigh`, through the subscription
WebSocket route: four concurrent cases per trial, 1,800-second timeout, no
output cap or paid fallback. Each native run allows at most eight new attempts,
including only provider-eligible retries, with two attempts maximum per case.
No additional trial is authorized. The ledger's monetary totals are valid;
incremental subscription cash is zero and quota consumption is unmeasured.
Preparation made no model calls. All twelve answers subsequently completed on
the first attempt with valid JSON and native receipts. There were no execution
failures, retries, repairs, reused answers or regenerated baselines. Field order
remains number/context/subject. All 29 pinned source, template and saved-baseline
files remain unchanged after execution and native reviews. Agent assessments
remain separate from user judgments and adoption.

### ASv6.57 completed answers and agent review

ASv6.57 does not pass. Agent review found four of twelve answers with a
heading-alone parent-scope failure and eleven missing an enumerated subject
from a valid broader branch. N063 T2 passes both reviewed checks. The saved
ASv6.56 counts were four scope failures and twelve missing-branch failures.
This small set of stochastic answers does not establish improvement or a
general failure rate. Current native agent verdicts are eleven reject and one
accept; no user verdict or adoption is inferred.

| Post | T1 scope / entries | T2 scope / entries | T3 scope / entries | Answers missing valid branches |
| --- | --- | --- | --- | --- |
| N063 | Pass / 197 | Pass / 164 | Pass / 157 | 2 of 3 |
| N074 | Pass / 177 | Pass / 169 | Pass / 142 | 3 of 3 |
| N096 | Fail / 289 | Fail / 296 | Fail / 255 | 3 of 3 |
| N100 | Fail / 199 | Pass / 226 | Pass / 255 | 3 of 3 |

Pass means no confirmed scope failure was found in that complete-output review;
it does not establish compliance with every instruction. N063 T2 also retains
all fifteen ingredients and their dish roles, the dish, cooks and food/Nostr
subjects. Its general olive oil uses Oils, and vegetable broth appears beneath
both Vegetables and Broths. Its acceptance is bounded to the reviewed checks.

Each failing scope answer has a displayed direct edge and a heading-only
counterexample. The post or `context` cannot supply a missing restriction:

| Answer | Displayed parent → child | Counterexample |
| --- | --- | --- |
| N096 T1 | 2 Food preparation → 2.2 Chopping | Chopping wood fits the child without preparing food. |
| N096 T2 | 3 Cooking → 3.6 Mixing ingredients | Mixing paint ingredients fits the child without cooking. |
| N096 T3 | 3 Cooking → 3.5 Mixing ingredients | Mixing paint ingredients fits the child without cooking. |
| N100 T1 | 5 Meat processing → 5.2 Trimming fat | Trimming human body fat during surgery fits the child without processing meat as food. |

The missing placements below were checked against the full returned hierarchy,
including every occurrence of each parent. Narrower instances do not replace
the enumerated general subject. Equivalent wording is allowed; these remain
semantic agent assessments rather than user judgments.

| Answer | Retained subject and its position(s) | Missing broader placement(s) |
| --- | --- | --- |
| N063 T1 | Vegetable broth, 10.1 | Vegetables, 6 |
| N063 T3 | Preparing risotto, 14.1 | Risotto, 1.2.1 |
| N074 T1 | Weariness with narratives, 14 | Narratives, 13 |
| N074 T2 | Weariness with narratives, 11.1 | Narratives, 10 |
| N074 T3 | Dietary click-generation comparisons, 1.1.4.1 | Click generation by diets, 1.1.5 and 4.1 |
| N096 T1 | One tin of water, 3.1 | Tins, 5.1 |
| N096 T2 | Dinner recipes, 2.5 | Food recipes, 1.11 and 2.1 |
| N096 T3 | One tin of water for bolognaise sauce, 5.1.2.1.1 and 6.1.1 | Bolognaise sauce, 1.7.1 |
| N100 T1 | Beef-processing byproducts for tallow and animal food, 1.7.1 and 19.1.1 | Tallow production, 2.2.1 |
| N100 T2 | Beef fat for making tallow, 3.1.2.1.1 | Beef fat, 2.1.3 and 3.1.1 |
| N100 T3 | Myoglobin in dog food, 10.2.1 | Dog food, 7.1.2 and 8.1.2 |

The answers retain N063's ingredients and dish; N074's comparisons,
mother/ten-year-old example, Bitcoin narrative, attribution and individual plus
combined advice; N096's ingredient quantities, yield, actions, heat levels and
simmering time; and N100's price, steak count/thickness, trimming quantities and
purposes, animal provisions and sealer details. This does not establish
exhaustive coverage. N096 T1 and T2 retain many recipe-purpose quantities;
T3 retains the water-purpose distinction but lacks many other recipe-purpose
counterparts. The fully qualified named recipe headings remain terminal.
General quantity headings cannot simply be placed beneath them without
retaining the recipe role. These source-coverage caveats are separate from the
missing placements counted among subjects already returned.

All three N100 answers represent both the water/seeds provision and possible
myoglobin-addition readings for chickens; the doubled "some some" remains
ambiguous, without a user grounding verdict. No answer claims that the purchased
beef was vacuum-sealed. N074's comparative controversy-exception wording remains
a separate semantic caveat. No unstated arithmetic result was identified.

Native usage for the four new attempts in each trial is recorded below.
Output already includes reasoning; these columns must not be added together
as separate output charges. No cross-trial token or cost total is assembled.

| Trial | New attempts | Input tokens | Cached input | Output tokens | Reasoning tokens | Catalog estimate, USD |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 10,358 | 9,856 | 91,584 | 48,464 | 0.9375416 |
| T2 | 4 | 20,214 | 0 | 92,642 | 47,570 | 0.966848 |
| T3 | 4 | 15,350 | 4,864 | 97,692 | 55,477 | 1.0081064 |

Every attempt has native usage and a catalog estimate; provider billing is
unavailable. The estimates are not subscription charges or measured quota
consumption; incremental cash is zero. Cached input does not mean an answer
was reused. ASv6.57 uses 1,120 fewer prompt bytes per request than ASv6.56.
The 28 offline checks passed before inference, and native parsing and receipt
validation pass after execution; the semantic regression does not. ASv6.48
remains frozen, with no adoption or MP change.

A proposed next step is to review a delta to the existing boiler example that
demonstrates purpose supplied by a heading, while preserving general subjects,
qualified subjects and all valid placements. This targets a transfer hypothesis:
the current case states "for boiler repair" explicitly, whereas a recipe heading
supplies the purpose of its ingredient list and steps. The user subsequently
authorized the ASv6.58 draft below for review, then approved its wording and
the same twelve-answer Sol xhigh test. Adoption remains open.

## ASv6.58 purpose supplied by a heading

Status: approved candidate, tested on Sol xhigh. On October 2, 2026, after the
ASv6.57 results, the user authorized revising the existing boiler example to demonstrate purpose supplied
by a heading, verifying it offline and presenting the delta. This authorizes
neither inference nor adoption by itself. The user subsequently approved
ASv6.58 and the same twelve-answer Sol xhigh test below; adoption remains open
and ASv6.48 remains the frozen subject baseline.

[ASv6.58 (candidate, tested on Sol xhigh)](../asv6.58/ASv6.58.md) changes only C1's post and
source contexts. The old post says "One tube for boiler repair. Cutting it for
that repair." The new post is:

```text
Boiler repair:
One tube.
Cutting it.
```

The heading supplies the list's repair purpose, and "it" refers to the counted
tube. The qualified headings state that supported purpose directly. Their
contexts identify the heading as its source rather than citing the removed
phrase "that repair". The heading/list structure supports this relationship;
the separate co-mention and statement-order case C5 remains unchanged.

All 23 C1 entries keep their original numbers and subject headings. General
One tube and Cutting one tube remain outside Boiler repair; their repair-
qualified counterparts remain beneath every valid broader subject. All ten
headings retain source support under the new wording. The twelve declared
relationships and eleven prohibited placements remain valid. The post still
does not establish that the tube itself is a boiler component.

Every instruction byte and the other six example blocks are identical to
approved ASv6.57. All 34 primary rule assignments, nine explained secondary
demonstrations and five implications folded into R20, R22, R29 and R30 remain
unchanged. The current rule map updates only C1's source-specific descriptions.
The seven cases still contain 89 entries, 54 distinct subjects counted within
cases and 69 displayed direct relationships. The fixture declares 56 broader
relationships and 26 prohibited placements.

The new heading-purpose check first failed against ASv6.57 because it has no
purpose heading. It now passes, together with the other seventeen example
checks, nine native revision checks and two existing SP workflow checks: 29
total. These exercise the production subjects validator, native revision CLI
and existing SP preparation/execution paths without provider calls. The
preservation check also verifies every C1 number/heading pair against ASv6.57.
The first full-suite run exposed a stale variable left while updating that
check; it was corrected before the passing run. Offline checks establish
example and fixture consistency, not generalization to the regression posts.

Native `experiment.py revise` generated the prompt and
[ASv6.58 revision receipt](../asv6.58/ASv6.58.md.revision.json) directly against
approved ASv6.57 SHA-256
`0257ef96bf407d2941d16c26c2e4fecf67bacbe7183d1bbc14c3001e6b07bdaf`.
One exact edit changes C1; the receipt reconstructs the exact draft. ASv6.58
SHA-256 is
`7d498096d5ee2144b1513a46dab42fd1046cfd1ef7fdaf179a9642ec98d87f0f`.
Its source is 18,075 UTF-8 bytes, 61 fewer than ASv6.57. Those prompt bytes
repeat per SP request; the model token difference is unmeasured. No runtime
component or additional model pass is introduced. All 29 pinned ASv6.57
source/template and saved-answer files remain unchanged.

The full-context ASv6.57 → ASv6.58 delta is an ignored review artifact at
`target/sp-scope-regression-v1/asv658-full-context.diff`; exact authoring edits
and input hashes are ignored alongside it. Drafting prepared no post template,
experiment or inference request. The subsequently authorized test below checks
whether the heading-purpose example transfers to recipe ingredients and actions.

### Authorized ASv6.58 Sol 6.1 xhigh regression test

The user approved ASv6.58 and testing it on N063, N074, N096 and N100 with three
independent answers per post. Native `prepare --from ... --repeat` pairs each
trial with its corresponding saved ASv6.57 trial. Full original posts, review
evidence, schema and runner settings are preserved. Every saved baseline output,
parse and receipt matches; no baseline is regenerated.

Native `experiment.py revise` derives the reusable
[ASv6.58 post template](../../experiment_specs/asv6.58-hr01-post-template.txt)
and [revision receipt](../../experiment_specs/asv6.58-hr01-post-template.txt.revision.json)
directly from the approved source. The template adds only the existing `{POST}`
wrapper, byte-identical to the previous wrappers, and reconstructs exactly from
its native receipt. It contains 18,097 UTF-8 bytes; SHA-256 is
`3f819679d5cebc30cea9d9d055978e3f17e674fc243c7ee334e6ad86a0aae195`.

Preflight found four valid saved baselines and four new, nonreusable requests
per trial. All twelve prepared prompts render exactly with their original post.
The draft's 29 offline checks passed, and native receipt and preparation checks
pass. All 29 pinned approved-source, new-template and saved-ASv6.57 files remain
unchanged after preparation. The ignored experiments are
`sse_multivector/experiments/asv6.58-sol61-xhigh-sp-scope-regression-t1/`,
`sse_multivector/experiments/asv6.58-sol61-xhigh-sp-scope-regression-t2/` and
`sse_multivector/experiments/asv6.58-sol61-xhigh-sp-scope-regression-t3/`.

The exact model is `gpt-6.1-sol`, effort `xhigh`, through the subscription
WebSocket route: four concurrent cases per trial, 1,800-second timeout, no
output cap or paid fallback. Each native run allows at most eight new attempts,
including only provider-eligible retries, with two attempts maximum per case.
This test covers those three trials; fresh-topic testing remains open. The ledger's
monetary totals are valid; incremental subscription cash is zero and quota
consumption is unmeasured. Preparation made no model calls. The completed
execution and reviews are recorded below. Agent assessments remain separate
from user judgments and adoption.

### ASv6.58 completed answers and agent review

On October 2, 2026, all twelve requests completed on the first attempt. Each
trial has four valid answers, four attempts and zero empty, malformed,
invalid-receipt, failed or unrun cases. There were no retries, answer reuses,
baseline regenerations, output repairs or paid fallbacks. Native parsing and
receipt checks pass. Every entry preserves `number`, `context`, `subject` key
order. All four answers in each trial differ from their saved ASv6.57 answers;
the native text comparison is not a quality judgment.

The agent read every numbered subject in all twelve hierarchies and checked
the complete source posts and distinct subjects' contexts. The review tests
heading-only scope and retention of returned subjects beneath applicable
broader headings. Source-grounding and entity-coverage caveats are recorded
separately; a passing scope check is not a claim that every prompt rule passes.
All twelve native reviews are current agent rejections, each bound to its input
and output with a concrete missing-placement witness. Four also have a scope
counterexample. No user output verdict or adoption decision is inferred from
approval of the prompt and test.

| Post | Entries T1 / T2 / T3 | Answers with scope failure | Answers with missing valid placement |
| --- | --- | --- | --- |
| N063 | 144 / 147 / 175 | 0 / 3 | 3 / 3 |
| N074 | 200 / 159 / 183 | 0 / 3 | 3 / 3 |
| N096 | 232 / 251 / 223 | 2 / 3 | 3 / 3 |
| N100 | 217 / 191 / 187 | 2 / 3 | 3 / 3 |

**Scope fails in 4/12 answers; valid branch retention fails in 12/12.** No
answer passes both reviewed checks. ASv6.57 had four scope failures and eleven
placement failures, with N063 T2 its only bounded pass. The approved
heading-purpose edit does not resolve these regressions in this sample. These
small stochastic samples do not establish a causal change in failure rate or
generalization to other topics.

Confirmed heading-only scope witnesses are:

| Answer | Direct parent → child | Counterexample that fits the child but loses the parent restriction |
| --- | --- | --- |
| N096 T2 | 2.6 Cooking oils → 2.6.1 Olive oil | Olive oil used in a lamp does not establish a cooking role. |
| N096 T3 | 1.6 Seasonings → 1.6.1 Salt | Salt used to de-ice a road does not establish a seasoning role. |
| N100 T1 | 3 Food preparation → 3.1 Beef preparation | Preparing beef tissue as a laboratory specimen does not establish food preparation. |
| N100 T3 | 14.1.1.1 Using the new Nesco VS-12 vacuum sealer → 14.1.1.1.1 Appreciation for the Nesco VS-12 vacuum sealer after use | Appreciation after using an old VS-12 does not establish use of a new sealer. |

The N100 T3 edge also occurs at 14.3.1 → 14.3.1.1 and
19.1.1 → 19.1.1.1. N096 T2 also puts generic subjects under Culinary herbs,
Seasonings, Cookware and Food containers. This table supplies a confirmed
witness per failing answer rather than an exhaustive count of bad edges.
An instance's `context` does not repair restrictions missing from its heading.

Each answer also omits at least one already-returned subject from an applicable
branch. These witnesses do not depend on demanding a particular vocabulary or
inventing an additional subject. A narrower subject or event elsewhere in the
branch does not retain the missing heading's level of generality.

| Answer | Returned subject and all its occurrences | Applicable parent occurrences lacking that subject beneath them |
| --- | --- | --- |
| N063 T1 | Ingredients for mushroom risotto with shrimp, 1.2.1.1.1.1, 1.2.1.2.1.1, 2.2.1.1, 3.2.1.1 and 15.1 | Cooking, 16; only the preparation subject is present. |
| N063 T2 | Ingredients for cremini mushroom risotto with shrimp, 1.1.1.1.1.1, 2.1, 3.1.1.1, 4.2.1.1.1.1 and 6.1.1.1.1.1 | Cooking, 15; it is terminal. |
| N063 T3 | Risotto ingredients, 4.1 and 16.1 | Risotto, 1.2 |
| N074 T1 | Comparisons of diets' click generation, 1.1.4.1 | Click generation by diets, 1.1.6 and 7.1.1 |
| N074 T2 | Weariness with narratives, 11.1 | Narratives, 10 |
| N074 T3 | Weariness with dietary narratives, 12.1 | Dietary narratives, 1.6 and 11.1 |
| N096 T1 | Onions turning clear during cooking, 1.2.1.2 | Cooking, 8 |
| N096 T2 | Spaghetti bolognaise recipes feeding 5 people, 1.4.1 | Spaghetti bolognaise recipes, 1.1 and 2.1.1.1.1 |
| N096 T3 | One tin of water for spaghetti Bolognese sauce, 1.1.1.2.4.13 and 3.1.1 | Bolognese sauce, 1.8.1; Bolognese sauce for spaghetti Bolognese, 1.1.1.2.5 and 1.8.1.1 |
| N100 T1 | Dog food, 11.1.1 | Dogs, 9; only food for the writer's dog is present. |
| N100 T2 | Beef steaks, 2.2 | Steaks, 3; only the narrower sirloin strip steaks subject is present. |
| N100 T3 | Beef steaks approximately 1.5–2 inches thick, 3.2.1 | Beef steaks, 2.2 and 3.1; only the narrower 15-steak subject is present. |

Read-only checks against the native saved parses verify each cited heading,
all its occurrences, absence beneath each cited parent, and the four scope
edges' direct-parent coordinates. The assessments themselves remain semantic
agent judgments rather than automatic label matching.

N063 retains all fifteen named ingredients and their dish roles in every
answer. T2 also retains the chef emoji as Cooks and Male cooks; T1 and T3 use
it to establish cooking/preparation but lack that entity heading. N074 retains
the diet comparisons, mother/ten-year-old example, Bitcoin narrative,
attribution and individual plus combined advice. Its controversy-exception
wording remains a separate semantic caveat. N096 retains ingredients,
recipe-purpose quantities, yield, actions, heat levels and simmering time.
Many general quantity headings are absent in T3 compared with T1/T2, and the
fully qualified writer's recipe headings remain terminal in all three answers.
These coverage caveats are separate from the counted missing placements among
subjects already returned. No unstated arithmetic result was identified.

N100 retains the beef price, steak count and thickness, combined trimming
quantities and purposes, animal provisions and sealer details. T2 and T3 retain
both chicken-water/seeds provision and possible myoglobin-addition readings.
T1 retains only the provision reading. The doubled "some some" remains
ambiguous without a user grounding verdict. T1 and T2 additionally connect
vacuum-sealer use to preservation of the sirloin steaks. Their contexts cite
the account's sequence and #foodpreservation; the post does not state what was
sealed, so this is a separate grounding concern under the existing co-mention
and statement-order rule. T3 does not assert that beef was vacuum-sealed.

Native usage for each trial's four new attempts is below. Output includes
reasoning; these are not separate output charges. No cross-trial token or cost
total is assembled.

| Trial | New attempts | Input tokens | Cached input | Output tokens | Reasoning tokens | Catalog estimate, USD |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 4 | 20,198 | 0 | 91,976 | 50,131 | 0.960156 |
| T2 | 4 | 20,198 | 0 | 93,486 | 53,213 | 0.975256 |
| T3 | 4 | 15,334 | 4,864 | 88,709 | 48,662 | 0.9182444 |

Every attempt has native usage and a catalog estimate; provider billing is
unavailable. These estimates are not subscription charges or measured quota
consumption; incremental cash is zero. Cached input does not mean answer reuse.
All 29 pinned approved-source, template and saved-ASv6.57 files remain unchanged
after execution and review. Inputs, evidence, schema, runner settings, rendered
prompts and saved baseline outputs/parses/receipts still match preflight.
The unchanged source's 29 offline checks passed before inference. Native
format, receipt, preservation and review checks pass after execution; the
semantic regression fails. ASv6.48 remains frozen, with no adoption or MP change.

A proposed next step is a small transfer test of the unchanged prompt on short
posts from other topics, covering general materials versus roles and retention
under two valid parents. That would check whether these failures also occur on
simple inputs before another example edit. That test and any next draft remain
unapproved; neither has started. Fresh-topic generalization remains open.

## Offline audit of saved candidate answers

On October 2, 2026, the user authorized auditing the saved answers against
common criteria and proposing short diagnostic cases before another prompt
edit. This audit made no model calls and changed no prompts, post inputs,
settings, receipts or model outputs. It covers the 84 completed Sol 6.1 xhigh
answers from ASv6.50, ASv6.51 and ASv6.54–58: three trials on each of N063,
N074, N096 and N100. ASv6.52/53 are untested drafts and are not samples.

Native `experiment.py show` validates all 84 answers. The post inputs match
across all seven versions. The instruction prefix before `<example>` is
byte-identical across ASv6.51 and ASv6.54–58; their differences are in examples.
For ASv6.50/51, this audit reads all distinct headings and all direct
parent-heading relationships, then checks full numbered branches and contexts
for its witnesses. For the later 60 answers it rechecks the existing scope and
placement witnesses and searches the saved direct relationships for the same
restriction losses. This is a bounded reassessment, not a new proof that all
other relationships, interpretations or coverage requirements pass.

### Common scope check and corrected findings

Compare the child and parent headings by themselves. A counterexample post
that fits the child without the parent confirms a failure. Source context
cannot restore a missing cooking role, edible grade, food-preparation purpose,
advice role, method or modifier. The same counterexample must receive the same
assessment across prompt versions.

Applying this criterion consistently finds twelve additional failing answers.
The scope columns count answers with at least one confirmed witness, not bad
edges and not overall acceptances:

| Tested candidate | Original scope failures / 12 | Confirmed scope failures / 12 after audit |
| --- | --- | --- |
| ASv6.50 | 2 | 8 |
| ASv6.51 | 2 | 5 |
| ASv6.54 | 5 | 5 |
| ASv6.55 | 5 | 6 |
| ASv6.56 | 4 | 5 |
| ASv6.57 | 4 | 5 |
| ASv6.58 | 4 | 4 |

Each counted answer has a direct-parent witness verified against its saved
parse. The twelve corrections are:

| Candidate / answer | Previously missed direct relationship |
| --- | --- |
| ASv6.50 N063 T1 | 8 Cooking fats and oils → 8.1 Olive oil |
| ASv6.50 N063 T2 | 1.8.1 Cooking oils → 1.8.1.1 Olive oil |
| ASv6.50 N096 T1 | 1.7 Cooking oils → 1.7.1 Olive oil |
| ASv6.50 N096 T3 | 1.12 Cooking oils → 1.12.1 Olive oil |
| ASv6.50 N100 T1 | 3 Food preparation → 3.1 Beef preparation |
| ASv6.50 N100 T3 | 4 Food preparation → 4.1 Beef preparation |
| ASv6.51 N096 T2 | 2.6 Edible oils → 2.6.1 Olive oil |
| ASv6.51 N100 T1 | 10.1.1 First use of a new Nesco VS-12 vacuum sealer → 10.1.1.1 Satisfaction with the Nesco VS-12 after first use |
| ASv6.51 N100 T2 | 3 Food preparation → 3.2 Meat preparation |
| ASv6.55 N100 T2 | 10 Food preparation → 10.1 Meat cutting |
| ASv6.56 N100 T2 | 10 Food preparation → 10.1 Meat preparation |
| ASv6.57 N100 T3 | 3 Food preparation → 3.1 Meat preparation |

The oil witnesses use the same lampante/nonfood counterexample as the later
reviews; the [USDA olive-oil grades](https://www.ams.usda.gov/grades-standards/olive-oil-and-olive-pomace-oil-grades-and-standards)
already supplied its basis. Preparing or cutting meat samples for laboratory
testing fits the generic preparation/cutting child without food preparation,
the same distinction used in ASv6.58 N100 T1. Satisfaction after someone's
first use of a previously owned VS-12 fits the ASv6.51 child without use of a
new sealer, matching ASv6.58's lost-new modifier check. These are agent semantic
assessments, not independently calibrated user labels.

These counts correct earlier review omissions. They do not establish a causal
effect of examples, a general failure rate, or a reliable ranking among these
small samples. In particular, the original ten scope acceptances in ASv6.50
and ASv6.51 are not evidence that those candidates satisfy the later criteria.

### Placement check and open interpretation

The instruction first enumerates specific subjects expressed by the post, then
derives broader headings. Its placement sentence says: "Retain every enumerated
subject as an entry, including it in each branch that passes this check."
Later reviews applied that requirement to every returned heading, including
derived general headings. The schema does not distinguish those two origins.
The user has been asked whether branch retention applies to every returned
heading or to the subjects expressed by the post. That interpretation remains
open; this audit does not amend the prompt or infer a user decision.

An omission witness needs both a valid heading-only relationship and absence
of the same meaning from the proposed branch. Repetition elsewhere proves
that the model returned a meaning, not that it belongs beneath another parent.
For example, ASv6.50 N096 T2 returns a sauce-simmering heading beneath
Ground-beef and tomato sauce **for spaghetti bolognese**, but the child names
bolognese sauce without the spaghetti purpose. Its existing placement can
itself lose scope; copying it beneath the other parent occurrences would not
repair that loss. Likewise, trimming tissue and scraps **for a dog** does not,
by heading alone, establish a dog-food role. Those two proposed omission
witnesses were discarded rather than used to inflate failure counts.

The audit verifies the coordinates and exact-heading absence of all 56
previously recorded omission witnesses in ASv6.54–58. That structural check
does not decide semantic entailment or the open enumeration boundary. Several
witnesses demand a derived broader heading despite narrower source meanings
being present. Five also rely on Vegetable broth fitting Vegetables, a
relationship needing calibration rather than an assumed class-membership
judgment. No replacement aggregate placement score is asserted while those
boundaries remain open.

Missing placements also affect subjects directly grounded in the post, so the
regression does not depend entirely on the broader-heading interpretation.
The following additional early-answer witnesses retain source-specific
meanings and pass the heading-only relationship check. Full numbered branches
were checked for equivalent wording as well as these exact headings:

| Answer | Returned source subject | Broader parent occurrence lacking it |
| --- | --- | --- |
| ASv6.50 N063 T1 | 2.1.1 Ingredients for mushroom risotto with shrimp | 1.1.1.1 and 1.1.2.1 Mushroom risotto with shrimp |
| ASv6.50 N063 T2 | 1.1.1.1.1.1.1.1 Ingredients for cremini mushroom risotto with shrimp | 2 Cooking |
| ASv6.50 N100 T3 | 2.4.1.1 About a quarter pound of beef connective tissue and meat scraps reserved for a dog | 10.1.2.1 Beef connective tissue reserved for a dog |
| ASv6.51 N063 T1 | 5.1.1 Ingredients for cremini mushroom risotto with shrimp | 1.1.1.1.1.1.1 and 1.1.1.1.2.1.1 Cremini mushroom risotto with shrimp |
| ASv6.51 N063 T2 | 2.1.1.1 Ingredients for cremini mushroom risotto with shrimp | 1.1.1.1.1 and 1.1.2.1.1 Cremini mushroom risotto with shrimp |
| ASv6.51 N063 T3 | 2.1.1 Ingredients for cremini mushroom risotto with shrimp | 1.1.1.1.1, 1.1.1.2.1 and 1.1.2.1.1 Cremini mushroom risotto with shrimp |
| ASv6.51 N074 T2 | 3.2.1.1.1.1 10-year-olds' resistance to mothers' instructions to eat vegetables | 2.4.1 Mothers telling 10-year-olds to eat vegetables |
| ASv6.51 N074 T3 | 8.2.1 Michael Pollan's advice not to eat too much | 8.5 Michael Pollan's dietary advice |
| ASv6.51 N096 T1 | 1.6.1.1.1 500 g of ground beef for spaghetti bolognaise | 1.1.1.2 and 1.2.1.1 Spaghetti bolognaise |
| ASv6.51 N096 T2 | 1.1.1.1.1 Never-fail spaghetti Bolognaise recipe that feeds 5 | 2.1.1.2 Spaghetti Bolognaise |
| ASv6.51 N096 T3 | 1.5.1 Ingredients for the writer's spaghetti Bolognaise recipe | 1.1.1.1.1 Writer's spaghetti Bolognaise recipe |
| ASv6.51 N100 T1 | 6.2.2.1 Providing chickens with cold water and sunflower seeds tomorrow | 6.2.1.1 Sunflower seeds for chickens |
| ASv6.51 N100 T3 | 2.4.1.1 Trimming about a quarter pound of beef connective tissue and meat scraps for a dog | 2.7.2 About a quarter pound of beef connective tissue and meat scraps reserved for a dog |

Combining the confirmed scope and placement witnesses for subjects expressed
by the post rejects at least eleven of ASv6.51's twelve saved answers.
N074 T1 has no confirmed
failure in this bounded audit; that is not an exhaustive pass. Thus an earlier
candidate's scope-only acceptance cannot be used as an overall control pass.

For ASv6.58, the four scope witnesses remain confirmed. The placement witnesses
for subjects expressed by the post in N063 T1/T2 and N096 T1/T3 also remain
supported. Their
union confirms failures in at least seven answers independently of requiring
every derived broader heading. The remaining five answers' recorded rejections
depend on broader-heading omission witnesses in the completed review. The
earlier 12/12 placement figure remains the historical assessment under that
interpretation, not a settled common-criterion score.

### Evidence preservation and diagnostic proposal

Twenty native `experiment.py review --role agent` reassessments record the
twelve additional scope findings and thirteen early source-placement witnesses;
several answers have both. Every preceding review remains in its JSONL history.
No user judgments were added. The saved source-coverage and N100 grounding
caveats remain available separately from the confirmed failures.

The initial hash capture and supplemental recursive capture live in ignored
`target/sp-scope-regression-v1/saved-candidate-audit-v1-*-hashes.json` artifacts.
They pin 161 immutable files, the original prefixes of 21 review files and 21
original reports. Native reviews append history and regenerate reports; those
two changes are expected. Approved prompts, templates, frozen experiment
plans, runner settings and saved run artifacts are unchanged.

Repeated entries should not be mistaken for added coverage. N063 T2 has 78
entries and 61 distinct headings in ASv6.51, versus 147 entries and 61 distinct
headings in ASv6.58. Equal distinct counts do not prove equal meanings or
coverage; they show why entry count alone cannot measure either.

The proposed next diagnostic is six short posts in three pairs. These are
cases for review, not new SP worked examples or an approved experiment spec:

| Pair | Positive post | Control post | Required distinction |
| --- | --- | --- | --- |
| Purpose supplied by a heading | Bridge repair: one steel plate. I drilled four holes in it. | I visited a bridge repair site. At home, I drilled four holes in one steel plate for a sculpture. | The first post supports repair-purpose subjects. The control supports sculpture-purpose subjects; the site visit does not give the drilling a bridge-repair purpose. Keep the general plate and the purpose-qualified instance; a generic Steel plates child cannot borrow repair purpose from context. |
| First use and new | I tried my new camera for the first time and liked it. | I tried an old borrowed camera for the first time and liked it. | Both support first use and appreciation. Only the first supports a new camera. A child beneath use of a new camera must retain new; first use alone cannot supply it. |
| One subject under two valid parents | I repaired a red bicycle. | I repaired a blue bicycle and saw a different red bicycle. | The first supports repair of a red bicycle beneath both bicycle repair and red bicycles, when those broader headings are returned. The control supports two separate events and does not establish repair of the red bicycle. |

Assess meanings and valid relationships, allowing faithful alternate wording
and numbering. Require the source-specific subjects under every applicable
returned parent; leave derived-heading obligations conditional on the open
decision. Check controls as well as positives so that successful purpose
inference does not reward attaching nearby statements to the same purpose or
object. These cases are informed by the development failures; they are
diagnostics rather than untouched evidence of generalization.

After the user settles the grading boundary and approves these cases, the
suggested first run is the unchanged ASv6.58 candidate on Sol 6.1 xhigh, one
fresh answer per case through the native workflow. This is six bounded calls,
without an additional model grading pass or a new production process. Any
repeat, wider transfer test or prompt revision remains unapproved. None has
started. ASv6.48 remains frozen and adoption remains open.
