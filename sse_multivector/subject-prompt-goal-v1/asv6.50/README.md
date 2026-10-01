# ASv6.50

Status: approved candidate, testing in progress on GPT-6.1 Sol xhigh. On
October 1, 2026, the user approved the full-context delta and authorized this
test. This supersedes the ASv6.49 draft. ASv6.48 remains the frozen subject
baseline. MPv3.43 remains the frozen mask working baseline. Adoption as the
subject baseline remains open.

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
Results are pending. A fresh transfer test outside food remains proposed and
requires separate authorization.
