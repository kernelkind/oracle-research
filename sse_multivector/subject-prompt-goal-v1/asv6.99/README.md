# ASv6.99 Individual action copies under a shared tool

Status: tested experimental draft; both focused targets pass; whole-answer failures
remain; not adopted.
The user approves the next N096 target after the [ASv6.98 results](../asv6.98/README.md#completed-results).
Production adoption remains a separate decision.

[ASv6.99](ASv6.99.md) extends existing C1 instead of adding another example:

> Cutting it and them with a knife.

Every complete individual and shared cutting subject now names the knife.
All previous numbered placements remain; five entries add Knife and both
individual actions, with the shared action beneath each. The Knife branch
therefore retains three distinct source meanings. Its shared action alone
cannot replace the individual copies. A general Knife heading does not impose
a purpose absent from those source strings. The tool example differs from
the regression's olive-oil participant while demonstrating the existing copy rule.

The instructions and C2–C8, including the successful recipe example, remain
byte-identical. The [34 primary assignments and five implications](../asv6.96/README.md#actual-instruction-and-example-coverage)
remain intact. C1 adds a focused R20–R23 compatible-copy witness; complete
partial/shared sources and tool reference resolution also retain R01/R02/R04/R16.
No new requirement or production step is introduced.

C1 grows from 56 to 61 entries; eight examples total 154 entries, up from 149.
The exact addition is 2,002 characters per request, not a measured token increase.
The same single prompt/post inference remains. Repeating example context across
the corpus still costs input; adoption needs demonstrated benefit.
The minimal authored tool-copy check first fails on ASv6.98 because no shared
tool branch is demonstrated. ASv6.99 passes 158 focused consolidation, example,
revision and attempt-budget checks using production subject validation. C1's
copy grouping is checked; C8's reviewed branch ordering is preserved verbatim.
Static validation does not establish model correctness.

Pinned native [source edits](prompt-edits.json) and [template edits](edits.json)
produce separate revision receipts. Source SHA256:
`e87bc404c65bd911b789d9c88d9b8d3e13f10f0ba97805ab6dfc10a55eb7acc0`.
The change follows [official OpenAI guidance on direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices).

## Fixed regression screen

Three native six-case plans under `experiments/sp-autonomous-v1/shared-tool-v1/`
U1/U2/U3 inherit ASv6.98 T1/T2/T3 through `prepare --from`, with the new template,
`--repeat` and the same history root `experiments/sp-autonomous-v1`.
Complete POST/evidence and settings remain unchanged: subscription
openai-codex/gpt-6.1-sol/medium, WebSocket, 1,800-second timeout, no output cap
and concurrency one per runner. Three runners permit three in-flight requests.
Freeze all plans and source before inference. Finish all 18 intentional first
calls regardless of quality: N063, N074, N096, N100, S006 and D006 in each trial.

Each `run --max-new-attempts 12` uses the unchanged shared counter
`target/sp-autonomous-v1/attempt-budget.json`, initially 1,523/2,000.
Existing provider-transient retries alone qualify, at most two total attempts
per case; no quality retry, model switch or paid fallback. Subscription calls
add no incremental cash charge; quota remains unmeasured. The eight prospective
posts stay unused.

Primary target: first retain three complete individual N096 sauté sources—onion,
celery and carrot—with supported quantities/modifiers, two tablespoons olive oil,
large pan, medium heat and the enclosing author's easy, never-fail recipe feeding
five people. Then require each formed source under every compatible returned
oil occurrence. Never-formed sources are source loss, not additionally missing
copies. Retain the complete shared sauté separately. Optional Oil headings need
not be added. Sauce-qualified pan compatibility stays open and is not decisive.

Native historical review finds this narrow target already passes ASv6.98 T1
and T2, and fails T3: **2/3**, not 0/3. T3 forms individual sources at
1.1.1.1.1.1/1.1.1.1.2.1/1.1.1.1.3.1, while olive oil 1.1.1.1.11 contains
only the combined sauté. This baseline is historical, not a contemporaneous
causal control. Repeated development cases do not establish unseen accuracy.

S006 recipe source retention/placement is the separate preservation target;
ASv6.98 passes 3/3. Whole-answer A/R/U uses the unchanged [bounded ASv6.98 criteria](../asv6.98/README.md#review-corrections-and-limits):
Food is not an exclusive-use class, SP supports action/relationship aboutness,
and unresolved readings stay separate from decisive defects. Review complete
unchanged POST and parsed answers via native `show`; preserve actual individual
reviewer reasons and corrections through native `review`, then broker adjudicate.
Agent assessments are not human whole-answer gold or independent accuracy proof.

## Completed results

All 18 planned medium calls return valid first answers with no failures, invalid
receipts, retries, reuse or unrun cases. The shared counter moves from
1,523 to **1,541/2,000**, leaving **459 attempts**. Native source/template and
plans remain frozen at checkpoint `683c97d8`; saved SDK requests and receipts
retain the exact prompt, provider/model, effort and schema. All 158 focused
offline checks pass; static correctness is separate from teacher correctness.

**N096 source retention and individual sauté copies under olive oil pass 3/3.**
All three complete individual actions retain material quantities, fine chopping,
oil amount, pan, heat and full recipe scope. Each answer returns one oil occurrence
and includes all three individual actions there, alongside their complete shared
sauté. U3's feeding-five paraphrase preserves the recipe capacity. Sauce-qualified
pan compatibility is not used to establish this target.

| Trial | Individual source locations (onion / celery / carrot) | Oil occurrence | Individual copies under oil |
| --- | --- | --- | --- |
| U1 | 1.1.1.1 / 1.1.2.1 / 1.1.3.1 | 1.1.11 | .1 / .2 / .3 |
| U2 | 1.1.1.1.1 / 1.1.1.2.1 / 1.1.1.3.1 | 1.1.1.11 | .1 / .2 / .3 |
| U3 | 1.1.1.1.1 / 1.1.1.2.1 / 1.1.1.3.1 | 1.1.1.11 | .1 / .2 / .3 |

The shared sauté appears beneath each of these oil-branch individual actions.
The saved same-criterion ASv6.98 result is 2/3; fresh ASv6.99 is 3/3. This small
historical contrast supports a bounded repair signal, not causal proof.

**S006 recipe-retention and placement also remain 3/3.** Complete salt and pepper
sources occur at 1.1.1/1.1.2 and their combination at 1.1.1.1. Salt repeats at
2.1.1/3.1/5.1; pepper at 2.1.2/4.1/5.2; the combination appears beneath all eight
individual occurrences. All retain seasoning food, to taste, author, reliability,
dish and five-person capacity. No absent easy claim is required.

| Case | U1 | U2 | U3 | Remaining finding |
| --- | --- | --- | --- | --- |
| N063 | U | U | R | U1/U2 Foodstr community/platform reading open; U3 Cooking lacks formed ingredient/list copies. |
| N074 | U | R | U | U2 individual quantity advice lacks Food copy; other advice/Unless readings remain open. |
| N096 | R | R | R | Sauté target passes; U1/U2 individual tomato additions lack beef-condition copies, U3 individual additions never form. |
| N100 | R | R | R | U1/U3 whole shared trimming source never forms; U2 loses finally and nests generic recommendation below specific purchased unit. |
| S006 | A | A | A | Complete recipe-qualified seasoning sources and copies retained. |
| D006 | R | R | R | U1/U3 reciprocal material-action copies missing; U2 improves those copies but omits separate complete individual material sources. |

Whole-answer totals are **3 bounded accepts, 11 rejects, 4 uncertain**.
The twelve original answers are 0/8/4; the six diagnostics are 3/3/0.
Historical ASv6.98 labels remain 3/14/1; neither total is a causal quality score
comparison. Optional returned headings and unresolved readings affect whole-answer
assessment. Prospective posts remain unused; no unseen/general accuracy claim.

Three native `show` witnesses describe the clearest remaining target:

- U1 N096 forms individual chopped-tomato addition 1.1.7.2, explicitly conditioned
  on the 500 g beef being uniformly coloured. Beef 1.1.6 contains only the combined
  tomato/purée/water addition, not this complete individual source.
- U2 N096 forms the analogous individual source 1.1.1.7.1, but beef 1.1.1.6 again
  receives only the combined addition. Its own beef-condition wording establishes
  the relationship; the copy requirement does not come from adjacency or context.
- U3 N096 forms combined addition 1.1.1.6.4 but no complete individual chopped-tomato,
  purée or water addition source. This is source loss, not extra missing-copy counts.

## Review corrections and limits

Two whole-answer reviewers inspect unchanged complete POST and parsed answers
with prompt/version definitions withheld. Reviewer B's first readiness command
accidentally exposes truncated baseline-containing metadata, so a fully blinded
claim is unavailable. Later judgments use actual full POST/parsed projections.
Each reviewer's actual reasons are recorded separately, not substituted with the
broker's selected witness. The separate fixed-target audit matches the complete
source/copy evidence above; reviewer agreement is not independent accuracy proof.

Native history preserves ten initial/superseded events, 36 final individual
reviewer events and 18 broker adjudications: **64 hash-current events**. Score
the latest broker verdict per case. Both reviewers initially miss U3 N063's
returned Cooking branch and change A→R. Reviewer B changes U2 N074 U→R on the
individual Food-quantity copy. Reviewer A proposes vegetable/plant-food rejections
for U1/U3 N074, then withdraws them as uncalibrated; U1 follows U→proposed R→U.
Reviewer A changes U1/U3 N100 U→R after applying explicit shared-predicate
combination coverage. Both change U2 D006 A→R: correctly copied individual
trimming events do not replace separate complete individual material subjects,
as the existing event-versus-subject clause requires. No extra copy count is
charged for these never-formed material sources.

Foodstr membership, N074 advice/Unless and vegetable/plant-food readings,
mother-instruction/Dietary-advice compatibility, dinner/purchase attachment,
sauce membership, implicit sirloin origin, duplicated some and vacuum-sealer
food-preservation purpose remain separate uncertainties. Neither nonfood uses
nor a universal culinary-purpose restriction establishes a rejection here.
Human edge calibration is not whole-answer gold.

The useful next target is N096's individual tomato/purée/water additions and
their copies under compatible beef-condition headings. It repeats across all
three answers as either source loss or missing copies. Preserve both successful
demonstrations while investigating this next existing-rule transfer. This is a
proposal for a subsequent iteration, not another run or production adoption.

The user approves this target. [ASv6.100](../asv6.100/README.md) adds a separately
named condition participant to existing C1 while preserving Knife and C8.
Its [completed fixed screen](../asv6.100/README.md#completed-results) keeps the
individual-addition/beef-copy target at 0/3 and full sauté preservation at 2/3;
S006 remains 3/3. ASv6.100 is not a promotion candidate. Source completeness and
conditional copies remain separately reported.

## Condition source diagnostic v1

Status: user-approved input investigation completed; ASv6.99 stays unchanged.
The user approves testing a minimal addition/condition post, then adding recipe
scope and surrounding steps separately after the ASv6.100 result. This changes
test inputs, not the prompt or production. These are six synthetic development
cases, not prospective posts or matched controls for the original N096.
In particular, this diagnostic explicitly names large pan in the target;
original N096 supplies it in earlier instructions and has additional ingredients.
Differences from that original cannot be attributed solely to post length.

The reusable [native spec](../../experiment_specs/asv6.99-condition-source-diagnostic-v1.json)
uses the production subjects adapter. Input data remain ignored at
`target/sp-autonomous-v1/condition-source-diagnostic-v1/posts.json`; native plans
pin exact bytes and preserve the full POST. The controlled source parts are:

Input fixture SHA256:
`27809bf08532646c47e53af3d2ee855d0ee2bebead94c311f14d1ca06d7df436`.
Spec SHA256:
`de3e4a3346afd00adfed35f9df2c68275e1abb3349e403ee5985e95f6c4d06ae`.
Unchanged ASv6.99 template SHA256:
`2f51994997528e001647faf73469344ca7341ece9b4a51619b2df9d1c01afcbf`.

Resolved target sentence:

```text
Once 500g ground beef is all the same colour, add 1x 400g tin chopped tomatoes and 1x 400g tin tomato purée plus 1 tin of water to a large pan.
```

Matching list:

```text
500g ground beef
1x 400g tin chopped tomatoes
1x 400g tin tomato purée
```

Reference-form target sentence:

```text
Once beef is all the same colour, add both tins of tomatoes plus 1 tin of water to a large pan.
```

Recipe scope prefixes `My #neverfail Spaghetti Bolognaise recipe that feeds 5.`
and suffixes `#easy`. Nearby steps insert `Gently fry beef without browning.`
before the target, then `Mix all ingredients thoroughly. Simmer on low heat for
45min-1hr.` after it. No medium heat is added to the target. Native preparation
sends only POST, not case labels or review evidence.

| Case | Input | Fixed comparison |
| --- | --- | --- |
| C001 | Resolved target sentence alone | Minimal formation/copy check |
| C002 | Matching list, blank line, resolved target | C001→C002 adds list and redundant descriptions |
| C003 | Same list and reference-form target | C002→C003 shortens only target references |
| C004 | C003 plus recipe scope | C003→C004 adds scope |
| C005 | C003 plus nearby steps | C003→C005 adds other instructions |
| C006 | C003 plus both scope and nearby steps | C004/C005→C006 checks their interaction |

List presence is not a pure length intervention. Recipe scope bundles author,
never-fail, dish, five-person capacity and easy. Nearby steps reuse the entity
inventory but add actions, references and potential referent details; that is not
a pure length intervention either. The diagnostic can locate an observable
failure boundary, not establish an internal cognitive mechanism.

Freeze primary checks before inference: three distinct individual additions and
their separate expressed combination, each retaining the respective 400 g tin
or one tin of water, the 500 g ground-beef same-colour condition and large pan.
C004/C006 additionally retain the full stated recipe scope. Then check each
formed target source under every actually returned compatible beef occurrence;
check compatible pan copies separately. Own subject wording establishes
relationships, including condition aboutness. Equivalent paraphrases count;
context or a separate entry cannot restore a missing target field.

Never-formed individual targets are source loss, not additional missing-copy
counts. Combined targets cannot replace individual sources. Missing separate
beef/pan participant sources or zero compatible returned occurrences are reported
separately, not counted as vacuous copying success. Generic wider headings are
optional. Extra-step-dependent full referent completeness is a separate check;
passing the common target subset does not prove full source completeness. Do not
infer a specific colour, require browning, or calculate a water amount.

Prepare W1 from the spec, then W2/W3 through native `prepare --from W1`, all with
`--repeat` under `experiments/sp-autonomous-v1/condition-source-diagnostic-v1/`.
Each has all six cases in order and unchanged subscription
openai-codex/gpt-6.1-sol/medium, WebSocket, 1,800-second timeout, no output cap,
concurrency one. Three runners allow three simultaneous requests. Freeze all
source/plans before calls and finish all 18 first attempts regardless of quality.
Each `run --max-new-attempts 12` uses the shared 1,559/2,000 attempt counter.
Only provider-transient retries qualify, at most two total per case; no quality
retry, paid fallback or model switch. Subscription adds no incremental cash;
quota remains unmeasured. No production stage or prompt growth is introduced.
Review native full POST/parsed outputs and record bounded target assessments
through `review`; do not treat them as user gold or whole-answer accuracy.

Pre-inference case-design and native provenance audits pass. All 118 existing
experiment/hierarchy-input checks pass under cached `uv` with repository-pinned
`tiktoken==0.14.0`. The default Python first lacks that dependency for one
unrelated parent-guide check; the complete suite passes in the cached environment.
No production code, dependency pin or global Python environment is changed.

### Results

Source freeze commit `20991334` precedes the requests. All 18 answers finish on
their first attempt: six native-valid answers per trial, no failed requests,
malformed outputs, invalid receipts, retries or reuse. Saved wire inputs match
the frozen renderings and all source/settings pins remain valid. The shared
counter moves **1,559→1,577/2,000**, leaving **423** attempts. Review records add
no model calls. W1 has `missing_baseline`; W2/W3 have `not_comparable` because
their frozen W1 baseline has no answers. These are fresh input comparisons,
not a measured prompt-version improvement or matched original-N096 control.

The following measures require all three individual additions in an answer.
Formation checks the frozen common fields; individual copying checks every
actually returned compatible occurrence. Shared formation is reported separately.
Neither the table nor its verdicts grade every rule or the complete answer.

| Case | W1 | W2 | W3 | Individual formation | Separate shared formation | All beef individual copies | All pan individual copies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C001: minimal resolved sentence | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| C002: add matching list | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| C003: shorten references | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| C004: add recipe scope | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| C005: add nearby steps | R | A | R | 3/3 | 3/3 | **1/3** | 3/3 |
| C006: scope plus nearby steps | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |

Thus individual formation, separate shared formation and pan copying each pass
**18/18**; all beef individual copies pass **16/18**. Both recipe-scoped cases
retain author, easy, never-fail, dish and five-person capacity in all three
individual additions in every trial. Every answer has separate beef and pan
participant subjects and eligible occurrences; none receives vacuous success.

The two rejects are observable copying failures, with complete individual sources
already present elsewhere:

- **W1/C005:** `2.1.2`, `2.2.2` and `3.1.2` form the complete chopped-tomato,
  purée and water additions. Under `1` Ground beef, `1.1` 500 g ground beef and
  `1.1.2` 500 g ground beef becoming uniformly coloured, only shared addition
  `1.1.2.1` appears. None of the individual additions appears below these
  compatible occurrences. Large-pan copies `4.2`, `4.3` and `4.4` are complete.
- **W3/C005:** `2.1.2`, `3.1.2` and `4.1.2` form the same three complete sources.
  Beef occurrences `1`, `1.1` and `1.1.3` Uniform colour of all 500 g ground beef
  contain only shared addition `1.1.3.1`. The equal-meaning colour occurrence
  `6.1` does contain all three individuals at `6.1.1`, `6.1.2` and `6.1.3`.
  That separate branch cannot repair the missing beef branch. Pan copies
  `10.1.1`, `10.1.2` and `10.1.3` are complete.

W2/C005 retains every individual below beef `1.1` at `1.1.2`, `1.1.3` and
`1.1.4`, and below Large pans `2` at `2.1`, `2.2` and `2.3`. For the combined
intervention, W1/C006 retains them beneath all three recipe-qualified beef
occurrences (`1.1.1`, `2.1.1`, `3.1`) and Large pans `7`; W2/W3 also pass.
This establishes that the teacher can form and place these conditional meanings.
The omission is intermittent in this batch; the longer C006 passing 3/3 does
not support a monotonic post-length explanation.

Nearby steps are a bundled intervention. C003 passes 3/3 while C005 loses two
trials, but this does not isolate frying, mixing or simmering, or an internal
mechanism. Recipe scope does not lose the target in this sample, including in
C006; three repetitions do not establish that it reliably prevents the failure.
All six answers with nearby steps omit the earlier gently-frying-without-browning
wording from their addition subjects. That observation remains separate from
whether such prior-action detail must enter every complete referent description;
the common-field formation passes do not adjudicate it or full source completeness.
Original N096's inherited pan and additional ingredients remain untested factors.

### Review corrections and next investigation

A reviewer reads actual full POST/parsed answers with prompt/version definitions,
baseline answers and old labels withheld; the broker reads all numbered subjects.
Follow-ups clarify the existing parent restriction check and exact witnesses;
final agreement is not independent accuracy proof or user whole-answer gold.
Native history preserves **40 hash-current agent events**: four earlier actual
assessments, 18 final reviewer assessments and 18 broker adjudications. Score
the latest broker verdict per case, limited to the primary target above.

The reviewer initially rejects all C002 trials and W3/C003 for missing individual
copies under combined beef/chopped-tomato/purée headings. Those four rejects are
withdrawn: an individual addition's own wording does not preserve every material
restriction of the combined parent, so that parent is incompatible. Explicit
beef condition aboutness still supports simple beef/colour headings. Likewise,
plain additions do not qualify for frying, mixing or simmering parents whose
action restrictions they omit. This correction fixes the assessment, not the
prompt, and does not remove either C005 copying failure.

The user approves adding frying, mixing and simmering separately to C003,
retaining C003/C005 as fresh controls, before another prompt change. The
[condition step diagnostic](#condition-step-diagnostic-v1) freezes that batch;
its 15 calls are complete. This tests which instruction additions reproduce the
observed omission.

## Condition step diagnostic v1

Status: user-approved input investigation, complete; plans frozen before inference.
ASv6.99 remains the experimental comparison prompt. This adds five
synthetic development inputs, not a prompt change, new production stage or
prospective evaluation. The original N096's inherited pan and other ingredients,
and extra-step-dependent complete referent requirements, remain open.

The [native spec](../../experiment_specs/asv6.99-condition-step-diagnostic-v1.json)
uses the production subjects adapter and unchanged medium subscription settings.
The ignored fixture is
`target/sp-autonomous-v1/condition-step-diagnostic-v1/posts.json`.
Fixture SHA256:
`ba4d0cd4bec543c7e26ce4e022b28af71b6f1798e9db35db055e5ad4d17e36da`.
Spec SHA256:
`8c6d818c3ecf501f6402aa53df8a5324658aad96a9c6e84dc1d676bc3a9d61b7`.
ASv6.99 template remains
`2f51994997528e001647faf73469344ca7341ece9b4a51619b2df9d1c01afcbf`.

All cases reuse the matching list and reference-form target sentence above.
There is no recipe scope. Single-step cases change exactly one instruction;
the two controls retain the previous complete POST bytes:

| Case | Intervention relative to C003 | Purpose |
| --- | --- | --- |
| S001 | None; exact C003 | Fresh reference-form control |
| S002 | Insert `Gently fry beef without browning.` before target | Frying alone |
| S003 | Append `Mix all ingredients thoroughly.` on next line | Mixing alone |
| S004 | Append `Simmer on low heat for 45min-1hr.` on next line | Simmering alone |
| S005 | Exact C005: frying before target; mixing and simmering on one final line | Fresh all-steps control |

Freeze the same bounded primary check: form three distinct individual additions
with one 400 g tin for each tomato material or one tin of water, the 500 g
ground-beef uniform-colour condition and large pan in their own wording.
Separately form the expressed shared three-material addition. Copy each formed
**individual** under every actually returned compatible beef occurrence; assess
pan copies separately.
Equivalent faithful paraphrases count. Context, another entry or another branch
cannot supply a missing field or placement. Never-formed individuals are source
loss, not extra absent-copy counts. Missing separate participants or zero eligible
occurrences are reported separately, never treated as vacuous copying success.

Compatibility requires each child's own wording to preserve every parent
restriction. A combined-material heading adds material restrictions; frying,
mixing and simmering headings add action restrictions. Mentioning beef or a pan
does not by itself make such a heading compatible. Explicit condition aboutness
still supports simple beef and colour headings. Extra-step-dependent referent
details remain separate observations, not newly imposed primary requirements.
Accept requires all primary checks; reject requires a concrete failure witness;
unresolved primary readings remain uncertain. These are agent target judgments,
not user gold or whole-answer accuracy.

Prepare T1 from the spec, then unrun T2/T3 from T1, each with `--repeat`, under
`experiments/sp-autonomous-v1/condition-step-diagnostic-v1/`. Finish all 15 first
attempts regardless of quality. Use unchanged openai-codex/gpt-6.1-sol/medium,
WebSocket, 1,800-second timeout, no output cap and concurrency one per runner;
three runners permit three simultaneous requests. Each `run --max-new-attempts 10`
uses the shared **1,577/2,000** counter. Automatic retries remain provider-only,
at most two total attempts per case, including resumes; no local or quality retry,
model switch or paid fallback. Fifteen first calls would end at 1,592, leaving
408; the permitted retry ceiling is 30 total calls. Subscription adds no
incremental cash; quota is unmeasured. This bounded investigation adds no
corpus-scale process.

Case order remains S001–S005 in all trials; the native CLI preserves source order.
Three repeats and fixed ordering do not establish a precise failure rate, a unique
causal mechanism or general correctness. Fresh control answers are not reused
old samples. T2/T3's unrun T1 baselines have no saved answers and are not matched
quality controls. Compare actual current POST/parsed targets, not native text-diff
labels. Preserve receipts and all real review corrections through native review.

Two reviewers assess actual POST/parsed answers separately, followed by broker
adjudication of exact numbered witnesses. Prompt/version definitions and other
reviewer verdicts are withheld during their initial assessments, but they retain
prior conversation context; this is not a fully blinded evaluation. Provenance
audit remains separate. The scoped metrics and explicit uncertainty follow the
[official OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices);
reviewer agreement does not establish human-label accuracy.

### Completed step results

All 15 planned medium calls return valid first answers; all three native runners
exit successfully. No provider failures, malformed answers, invalid receipts,
retries, reused answers or unrun cases occur. The shared counter moves from 1,577
to **1,592/2,000**, leaving **408 attempts**. Spec, fixture, prompt template and
plans remain unchanged from freeze commit **`392fd7cb`**. Native preparation and
the completed runs validate production input/schema/receipt paths; unchanged
runner/unit checks are not rerun for this input-only investigation.

A/R below are bounded primary agent judgments, not whole-answer scores. Individual
formation, separate shared formation and all compatible pan copies each pass
**15/15**; all compatible beef individual copies pass **14/15**. Every answer
has separate material/pan participants and eligible beef/pan occurrences, so
none receives vacuous copying success.

| Case | T1 | T2 | T3 | Individual formation | Shared formation | All beef individual copies | All pan individual copies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S001: fresh reference control | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| S002: frying alone | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| S003: mixing alone | A | A | R | 3/3 | 3/3 | **2/3** | 3/3 |
| S004: simmering alone | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |
| S005: fresh all-steps control | A | A | A | 3/3 | 3/3 | 3/3 | 3/3 |

**T3/S003 is a copying failure.** Complete individual sources appear at `1.2.2`
(one 400 g tin chopped tomatoes), `1.3.2` (one 400 g tin tomato purée) and `1.4.1`
(one tin water). Each names the large pan and all 500 g ground beef becoming the
same colour. Simple beef occurrence `1.1` **500 g ground beef** has none of these
three individual descendants; it contains only shared addition `1.1.1.1`.
Pan copies `2.1`, `2.2` and `2.3` are complete. The qualified condition heading
`1.1.1` adds the joint tomatoes-and-water relationship and is incompatible with
the individual sources; the decisive absent-copy witness is simple beef `1.1`.
No never-formed source is charged as a copying omission.

This reproduces the missing-copy pattern with mixing alone, without frying,
simmering or recipe scope. It does not prove that mixing uniquely causes it or
explain an internal model mechanism. The fresh all-steps control passes 3/3,
where the previous separate C005 cohort passed 1/3. Keep both cohorts and their
labels: this is variability evidence, not a prompt improvement or a reason to
pool controls as matched samples. Three repeats with fixed case order do not
estimate a stable failure rate; original N096 remains a different input.

### Additional relationships and review scope

Two separate reviewer assessments and broker adjudication agree on the bounded
14 A / 1 R / 0 U outcomes. Native history contains **45 hash-current agent review
events**, one per reviewer and broker per case; no teacher calls are made by
review commands. Score the latest broker event for the frozen target only.
Reviewer A has no holds or corrections. Reviewer B withholds an initial
T3/S002 primary label until the scope is clarified, then accepts its bounded
target while retaining the actual qualified-pan edge defect below. No provisional
verdict was given, so no earlier accept/reject/uncertain event is invented.
The scope clarification is not independent accuracy evidence; neither reviewer
agreement nor a bounded accept certifies the entire answer.

Two actual returned-edge defects are recorded separately from the frozen
formation/missing-copy metrics:

- **T3/S002:** `4.1` Large pan for adding the contents of the tomato tins and
  water adds joint purpose/material restrictions. Its direct children
  `4.1.1`, `4.1.2` and `4.1.3` describe individual additions without preserving
  that whole relationship. Generic Pans `4` is compatible and has all three
  descendants, so the bounded pan-copy check still passes.
- **T2/S004:** `1.1.2` 500 g ground beef being all the same colour as the
  prerequisite for adding the tomato tins and water adds the joint relationship.
  Direct children `1.1.2.1`, `1.1.2.2` and `1.1.2.3` omit some of its materials.
  Simple beef `1`/`1.1` is compatible and covered. The actual edges are defective
  even though the bounded missing-copy check passes.

Historical action detail remains a separate observation. In S002, T2/T3's
addition strings retain gently frying without browning and therefore qualify
for their actual frying-qualified beef occurrences; T1 omits it. All three
S005 answers omit that earlier frying detail. These observations neither impose
a new primary requirement nor establish complete retention of every source detail.

The next prompt investigation is not started. The existing instruction already
requires every formed source under every compatible occurrence, and ASv6.100's
condition-example extension failed its original N096 target. Any proposed delta
must distinguish execution of that existing rule from adding another duplicate
rule or condition example; the smaller S003 failure supplies a concrete witness.
