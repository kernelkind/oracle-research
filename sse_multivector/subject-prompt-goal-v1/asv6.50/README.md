# ASv6.50

Status: draft, untested. The user authorized preparing this replacement for
review; its wording and inference have not been approved. This supersedes the
ASv6.49 draft. ASv6.48 remains the frozen subject baseline. MPv3.43 remains the
frozen mask working baseline.

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
The draft SHA-256 is
`2ab157eb34f49edd2a443799c439be8eff512fe61df96f6d508434f4d3807a1c`.
No model calls were made while preparing this draft. Mechanical checks do not
establish semantic improvement.

The [agreed regression set](../asv6.49/README.md#agreed-regression-set) remains
N063, N074, N096 and N100, using complete original posts and saved ASv6.48
outputs. The proposed next comparison remains three independent candidate
outputs per post, reviewing complete hierarchies for preserved coverage and
new errors. It has not been started or authorized.

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
no new user verdicts. ASv6.50 remains untested and unapproved; the recommended
next step is testing it against these saved Sol outputs without rerunning
completed ASv6.48 cases.

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

ASv6.50 remains an untested, unapproved draft. The useful next step is testing
its replacement paragraph against these saved ASv6.48 answers, checking both
parent relationships and preservation of individual subjects and their
particular instances. No candidate inference was started.
