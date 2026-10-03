# ASv6.74 salt/dog scope minimization

Status: completed, with reproduced scope failures and additional source/placement
failures. All 54 fresh answers and current native agent reviews are saved. The
user approved minimizing the original failures after the ASv6.74 comparison.
ASv6.74 stays fixed, as does production ASv6.48. Prompt revision, MP and
adoption remain outside this task.

## Question and source

The saved original ASv6.74 answers return Seasonings → Salt in three of five
N096 trials and a food/feeding parent → material merely "for the dog" in all
five N100 trials. Earlier short dog controls never exposed a food/feeding
parent. Earlier salt controls use Sea salt and soup wording rather than the
original Salt and pepper to taste line. These contrasts do not identify why
the original answers fail.

The [sixteen authored cases](scope-minimization-cases-v1.json) deliberately
select and edit N096/N100 passages. They are human-readable experimental inputs,
not mechanically gathered original-post artifacts. Original wording comes from
native `show --case N096` in `as74-original-medium-r2` and `show --case N100` in
`as74-original-medium-r3`. Line-ending/trailing-space normalization and the
purpose/Sea salt edits are deliberate. Source provenance and rubrics remain
review-only; only each case's text enters POST. Interpret each edited post on
its own: deleted source clauses cannot supply its missing referents or meanings.

Fresh full-post controls use native `prepare --from` with only N096/N100 from
`as74-original-medium-r2`; native preparation preserves complete original text
and evidence without assembling a second source corpus.

| Cases | Comparison |
| --- | --- |
| S001/S002 | Salt and pepper to taste alone versus the same line under the original recipe title. |
| S002/S003 | Isolated salt/pepper line versus the complete original ingredient list, with the same title. |
| S002/S004 | Same title and line, without versus with original final hashtags. |
| S001/S005, S002/S006 | Original wording versus explicit food-seasoning purpose, without and with the title. |
| S001/S007, S002/S008 | Salt versus Sea salt, without and with the title. |
| D001/D002, D003/D004 | Same trimming/recipient statement, without versus with the source myoglobin-to-dog-food clause. |
| D001/D003, D002/D004 | Recipient wording versus explicit feeding purpose, without and with the dog-food clause. |
| D001/D005 | Trimmed dog material alone versus the original parallel fat-for-tallow clause. |
| D005/D006/D007 | Original trimming sentence, plus dog-food clause, plus the complete original chicken clause. |
| D005/D008 | Original trimming sentence, without versus with original hashtags. |

This is a fixed contrast set, not a binary-search algorithm or a claim to find
the globally shortest failing post. A successful reduction retains the same
concrete failing relationship in a shorter post; its repeatability and parent
exposure must be reported. Original controls test whether that relationship
still appears under the same frozen prompt and settings.

## Pre-generation criteria

Use the existing heading-alone scope rule and numbered-copy requirement.
Judge meaning rather than exact wording or a required tree shape.

1. **Salt scope:** inspect each returned occurrence of the focal salt topic
   and its salt/pepper combination. The original criterion combined Food with
   ingredient and seasoning restrictions, using de-icing as a counterexample.
   The Food evaluator correction withdraws that inference: another use does
   not disprove Food membership. Culinary class versus particular-use meanings
   need separate calibration; retain the earlier Seasonings → Salt user label.
   A heading that states food-seasoning or
   recipe-ingredient purpose may belong beneath the corresponding parent.
   Retain salt, pepper, their expressed combination and supported to-taste/role
   meaning; do not require a named optional derived heading.
2. **Dog scope:** inspect each returned occurrence of the connective-tissue/
   scrap-meat material, its combined approximate quarter-pound amount, trimming
   and recipient. Material merely "for the dog" cannot inherit feeding/food
   purpose: material for a chew toy fits that heading. Explicit feeding forms
   retain feeding purpose. In recipient-only forms feeding may be reasonably
   implied; a qualified interpretation is permitted, not mandatory. The separate
   myoglobin clause does not supply a missing restriction inside another heading.
3. **Source and placement:** retain the focal counts, modifiers, participants,
   relationships and complete combinations supported by the edited post. Inspect
   every numbered occurrence of compatible returned source-component parents,
   including repeated copies. Descendants count. Check alternative complete
   subject strings before declaring a source omission; context alone is
   insufficient. Derived broader-heading closure remains excluded. Ancillary
   recipe/fat/myoglobin/chicken subjects are boundedly inspected for obvious
   changes, not certified as full-SP gold. The ambiguous chicken reading and
   ingredient-group memberships remain outside confirmed rejection counts.
4. **Exposure:** separately record food/seasoning/feeding parents actually
   returned, the focal child meaning and every failing numbered edge. An absent
   parent is no scope error but provides zero observations of its relationship;
   do not count it as a successful edge test. An action itself concerning dog
   feeding is a different subject from material merely for the dog.

Record current output-bound native agent reviews for every answer. Reject only
with a concrete focal source omission, placement omission or heading-alone
counterexample. Preserve material semantic uncertainty. Acceptance concerns
these focal checks, not all SP rules, optional hierarchy shapes or user labels.
For fresh full originals, also retain the earlier bounded original-post review
criteria and separate a focal scope failure from other confirmed errors.

Report every trial and case, exposure counts and the particular failing edges.
Do not equate a wording change with improvement, or infer causation from a
single stochastic pair. These previously examined posts and authored contrasts
are development evidence; none is unseen validation or an example revision.

## Execution and scale

Use the [native subjects spec](scope-minimization-spec-v1.json) for trial 1;
trials 2 and 3 inherit cases/settings with `--from` and `--repeat`. Prepare
three full-post control experiments with N096/N100 only and `--repeat`.
All use subscription `openai-codex`, exact `gpt-6.1-sol`, medium, WebSocket,
1,800-second timeout, no output-token cap and no paid fallback. Diagnostic
concurrency is four per trial; full-post concurrency is one per trial, changed
from the earlier four solely to bound concurrent work. The six independent
native experiments together permit at most fifteen in-flight requests. Each
native run owns scheduling; no separate waves or execution scripts are added.

Plan 48 diagnostic answers and six full-original answers: 54 fresh calls, with
no quality-based early stopping or prompt/criteria changes. Every run shares
`target/sp-autonomous-v1/history` and persistent
`target/sp-autonomous-v1/attempt-budget.json`, starting at 302 of 1,000. Bound
each diagnostic run to 32 new attempts and each control run to four, including
eligible provider-only retries, at most two attempts per case. Failures remain
visible and count. All-first-attempt success would reach 356; never reset or
refund the counter.

Native directories under the ignored campaign experiment root are
`as74-scope-min-medium-r1` through `r3` and `as74-scope-original-medium-r1`
through `r3`. Verify exact rendering, inputs, settings, receipts and review
bindings after completion. Commit these criteria and inputs before inference.

This finite investigation adds no production component, grader or inference
stage. SP still makes one call per post; fixed prompt and repeated-branch
output costs are unchanged. The shorter posts reduce this experiment's variable
input and most output work. Subscription incremental cash is zero, quota use
is unmeasured and catalog estimates are not bills. The monetary ledger was
inspected before launch; no paid commitment is introduced.

## Results

All 54 planned answers completed on their first attempt, with valid native
receipts, no runner errors and no reuse. The criteria and source/spec were
committed as `cd27a60b` before inference. Post-run verification checked the
unchanged ASv6.74 source/template and exact rendering; identical diagnostic
inputs/settings; preserved full-original inputs, evidence and baseline outputs;
every receipt; and every current review's input/output hashes. Each answer has
one initial agent review and no user label. The later Food correction appends
three agent reviews for S004; scoring uses each latest hash-current verdict.
The persistent budget at initial completion is 356 of
1,000 attempts. Native preparation/validation and Git whitespace checks passed.

The originally claimed generic-Food salt reproduction is withdrawn after the
[evaluator correction](../isolation-v1/README.md#evaluator-audit-after-the-food-correction).
Dog-related historical labels also occur in shortened passages, with variable
exposure and repeatability; their parent-role meanings need separate checking.
The prompt has not improved during this experiment: it stayed fixed while the
inputs were changed to expose its behavior.

### All diagnostic trials

Accept is bounded to the frozen focal criteria, not full-SP gold. Rejections
include source and placement errors as well as scope errors. A zero scope-error
count does not count missing parent exposure as success.

| Case | Trial 1 | Trial 2 | Trial 3 | Focal scope errors | Other finding |
| --- | --- | --- | --- | --- | --- |
| S001, isolated salt line | Accept | Accept | Accept | 0/3 | Trial 1 has no food/seasoning parent; other trials retain role-qualified children. |
| S002, recipe title + salt line | Accept | Accept | Accept | 0/3 | Full recipe/pair relationship and checked copies retained. |
| S003, complete ingredient list | Accept | Accept | Accept | 0/3 | Salt recipe roles retained; full ingredient-list coverage is not certified. |
| S004, title + salt line + hashtags | Accept | Accept | Accept | 0/3 after calibration | Food → Salt is not disproved by another use; qualified recipe pair/copies pass. |
| S005, explicit seasoning purpose | Accept | Accept | Accept | 0/3 | Food-seasoning parents use qualified children. |
| S006, title + explicit purpose | Reject | Accept | Reject | 0/3 | Trials 1/3 omit the salt/pepper relationship with the recipe. |
| S007, Sea salt line | Accept | Accept | Accept | 0/3 | Seasoning parents use to-taste children. |
| S008, title + Sea salt line | Accept | Accept | Accept | 0/3 | Complete source combination fills all checked numbered copies. |
| D001, dog-material trimming | Accept | Accept | Accept | 0/3 | No food/feeding parent in any answer: zero exposure. |
| D002, plus myoglobin food clause | Accept | Accept | Accept | 0/3 | Dog food parents are present; recipient-only scraps stay outside them. |
| D003, explicit feeding purpose | Accept | Accept | Accept | 0/3 | Feeding purpose and checked source placements retained. |
| D004, explicit feeding + myoglobin | Reject | Reject | Reject | 0/3 | Feeding material/action missing beneath both Dog food copies in every answer. |
| D005, complete trimming sentence | Accept | Accept | Accept | 0/3 | Joint trimming retained; no food/feeding parent. |
| D006, trimming + myoglobin clause | Reject | Reject | Accept | 0/3 | Trials 1/2 omit the complete joint trimming subject. |
| D007, plus complete chicken clause | Reject | Reject | Reject | 1/3 | Trials 2/3 omit joint trimming; trial 1 has the dog-food scope failure. |
| D008, trimming + original hashtags | Reject | Reject | Reject | 2/3 | Trials 1/3 have scope failures; trial 2 omits joint trimming and returns no dog-food/feeding parent. |

After calibration these forty-eight reviews total 35 bounded accepts and
thirteen rejections, replacing 32/16. The three generic-Food salt scope labels
are withdrawn; three dog-related historical scope labels remain separately
recorded. Counts
for different contrasts are not a combined SP accuracy score or a claim about
unseen posts. No unresolved ingredient membership or derived-heading closure
is counted as a confirmed error.

### Salt witnesses and exposure

S004 removes the ingredient list, all cooking instructions and the media URL
from N096, retaining its title, salt/pepper line and final hashtags:

```text
My #neverfail Spaghetti Bolognaise recipe that feeds 5.
Salt and pepper to taste

#food #recipe #easy #spaghetti #bolognaise #tomato #dinner
```

Its previously rejected edges are Food 1 → Salt 1.3 in trial 1 and Food 2 →
Salt 2.3 in trials 2 and 3. De-icing use alone does not make salt fall outside
Food. All three answers retain the complete qualified recipe pair and its
required focal copies; their corrected bounded verdicts accept. Food and the
original Seasonings parent were incorrectly treated as the same restriction.
The shorter post therefore does not establish the claimed scope reproduction.

S002 differs only by omitting the final hashtags. All three S002 answers use
role-qualified children beneath seasoning parents and preserve the full
recipe/pair relationship. This controlled source contrast associates the
returned broad Food branch with a former erroneous label in these samples; it
does not establish the model's internal cause or a universal hashtag effect.

The isolated original salt line and Sea salt variants do not fail the scope
check here. Salt versus Sea salt alone therefore does not explain the earlier
full-post difference. The Sea salt variant with the original hashtags was not
tested. Explicit food-seasoning purpose produces qualified children in all
six S005/S006 answers, but S006 trials 1 and 3 lose the full recipe relationship
from every salt/pepper heading. Correct qualification alone is insufficient.

### Dog witnesses and exposure

D008 retains the original complete trimming sentence and hashtags, omitting
the steak purchase, myoglobin/chicken clause and sealer passage. Trial 1
returns Dog food at 5.1 and 7.1, each containing the approximate quarter-pound
beef tissue/scrap merely "for a dog" at 5.1.1 and 7.1.1. Trial 3 returns
Food for dogs 5.1 with Connective tissue for a dog 5.1.1 and Scrap meat for a
dog 5.1.2. A chew-toy use fits those recipient-only children without food
purpose. Trial 2 returns generic Food for preservation/cooking but no dog-food
or feeding parent; it is not a successful observation of the disputed edge.

D007 trial 1 also reproduces Dog food 6.1 → the approximate quarter-pound
tissue/scrap for the dog 6.1.1, without any final hashtags. Hashtags are therefore
not necessary for this failure. D002/D006 add only the dog-food myoglobin clause;
all six answers expose Dog food parents yet keep recipient-only scraps outside
them. The separate food co-mention is not sufficient to reproduce the failure
in these samples. D001/D005 expose no food/feeding parents at all.

D003's explicit feeding wording retains correct feeding scope and checked
placements. D004 adds the myoglobin food clause and retains correct feeding
qualifications too, but its full counted feeding material and trimming are
absent beneath both Dog food copies in each answer:

- Trial 1: 3.2 and 7.1.
- Trial 2: 5.2 and 7.1.
- Trial 3: 5.2 and 8.1.

The full source material says it is for feeding a dog, so it concerns dog food;
the Dog food headings have no restriction to myoglobin alone. Correct placement
under the other feeding branch cannot repair those six omitted copies. This is
an agent semantic judgment about placement of explicit source materials/actions,
not a requirement to add or place every derived general heading.

D006 trials 1/2, D007 trials 2/3 and D008 trial 2 additionally omit the complete
first-sentence joint trimming of fat for tallow and tissue/scrap for the dog.
Both partial actions remain, but none of their headings states the complete
source combination. D008 trial 1 retains that combination only at 6.1.1/6.2.1,
missing other compatible partial-trimming copies such as 1.1.1.1.1. These are
independent source/placement findings, not extra recipient-versus-food errors.

### Fresh full-original controls

All six controls have confirmed errors under the earlier bounded original-post
criteria. Keep these trials separate from the five earlier ASv6.74 trials.

| Post | Focal scope failures | Other confirmed errors |
| --- | --- | --- |
| N096 | Seasonings → Salt in trials 1/3: 2/3 | Trial 2 loses the medium-onion restriction in a child; trials 1/3 omit recipe purpose from all complete sautéing headings. |
| N100 | Recipient-only tissue/scrap trimming under Dog feeding in trial 2: 1/3 | Trials 1/2 omit the joint trimming subject; trial 3 loses first-use scope in appreciation children. |

N096's bare Salt is 1.5.1 beneath Seasonings 1.5 in both failing scope answers.
Trial 2 returns no Seasonings parent and keeps qualified salt recipe subjects
outside its food branch, but One medium onion for Spaghetti Bolognaise 4.1.1
has child 4.1.1.3 that omits medium. A non-medium onion fits that child.

N100 trial 2 returns Dog feeding 12.1/13.1 with recipient-only trimming children
12.1.1/13.1.1. Trial 1 exposes food parents but keeps those materials outside
them. Trial 3 explicitly qualifies the material "for dog food", a permitted
supported interpretation; its first-use parents 13.1.1.1/16.1 nevertheless have
appreciation children without first-use specificity. The earlier 5/5 dog scope
failure count is therefore not deterministic behavior of this frozen prompt.
The ambiguous myoglobin/chicken reading remains excluded.

## Interpretation and next step

We now have concrete short posts exposing the failing food-parent relationships,
alongside nearby inputs that preserve qualifications. This improves the evidence
for choosing examples; it is not a prompt improvement. A correct qualified
heading elsewhere and a correctly qualified child with missing copies are two
different incomplete results. The existing scope and placement rules cover both.

The user subsequently approved drafting an existing-example revision around
these Food/Salt and Dog food/recipient contrasts. The resulting
[ASv6.75 (candidate, tested with failures)](../asv6.75/README.md) demonstrates unrestricted
materials, qualified food-role children under the broad food parents, and
complete source groups/actions beneath every compatible numbered parent. Its
audit preserves C1's count, reference, participant and action coverage and the
existing clause assignments. No calls were made for that drafting task. Review
of the exact draft subsequently led to the now-completed
[fixed comparison](../asv6.75/comparison-v1.md). Its 74 fresh medium answers
compare minimized bounded accepts at 35/48 versus 40/48 after calibration,
replacing the earlier 32/48 baseline, and retain all six repair
accepts, but original-post failures persist. D008's candidate trials expose no
dog-food parents; the observed scope improvements with exposure are recorded
separately. The campaign budget is now 430 of 1,000. Adoption remains open.

Food-context additions are useful controlled contrasts, not proved necessary or
sufficient causes. These small repeated samples do not establish unseen-topic
generalization. C2 and N063's open semantic questions remain open; no candidate
is adopted.
