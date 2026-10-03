# ASv6.73 example audit and fixed diagnostics

The user approved this audit and diagnostic experiment on 2026-10-02. Keep
ASv6.73 fixed while investigating its failures: twelve handwritten posts,
three independent subscription Sol 6.1 medium trials each. This is development
evidence, not held-out validation. Prompt revision and adoption remain open.

## Example audit

Read every complete example against every applicable instruction, rather than
checking only the clauses assigned to that example. Interpret relationships as
subject-index relationships: observing a duck concerns ducks; it need not be a
physical subtype of a duck. A conditional subject can concern blocking without
asserting that blocking occurred. Neither source context nor the surrounding
branch can repair a restriction absent from a heading.

All seven example outputs pass the production subjects adapter. Source SHA-256
is `9f4e18ec3518b068c8d29739af80d6d1156d273bd7c066a94566adea489973b8`;
the template is exactly that source followed by its ordinary POST wrapper.
Mechanical validity does not establish semantic correctness.

| Case | Entries / distinct headings | Complete-source assessment |
| --- | --- | --- |
| C1, soup preparation | 16 / 8 | Quantity, water reference, purpose, heating and checked repeated placements are preserved. **Participant omission:** soup appears only through preparation/purpose subjects, with no separate soup subject. R19 requires retaining participants alongside their events, as C5 demonstrates for ducks and notebooks. Mapping R19 to C5 did not check C1's compliance. |
| C2, new app | 32 / 15 | App name/type/newness, first use, figurative help, rhetorical appreciation, unresolved blocker and the complete unless subject are retained. The full exception occurs beneath all returned copies of its qualified help/blocking components. **Uncertain combination coverage:** help and appreciation concerning the same first use are separate; no combined help/appreciation subject is returned. The instruction does not establish an exhaustive boundary for every possible conjunction of source parts. Do not turn that uncertainty into a confirmed failure. |
| C3, bare URL/hash | 0 / 0 | Correct empty output under the opaque-identifier rule. URL component words and numbers contribute no subjects. |
| C4, labelled URL/ID | 8 / 6 | Prose supplies profile-URL and event-identifier topics and their constituent topics. Both specific subjects occur beneath both applicable roots; no relationship between the two lines is invented. Identifier bodies supply no extra subjects. |
| C5, duck/notebook | 18 / 11 | Both supported duck interpretations are direct subjects; participant topics remain alongside observation/purchase topics. The observations and notebook purchase stay independent. Each specific observation appears beneath all returned component copies. |
| C6, cables | 15 / 10 | Two named cables, their individual metre lengths, their counted pair and the explicit negated comparison are preserved. The pair and comparison appear beneath all checked component copies. No difference or total is calculated. |
| C7, arithmetic | 10 / 8 | Both addends, the explicitly stated result and the complete addition are retained, with the complete addition beneath each source component. |

For C3–C7, no confirmed error was found in this bounded whole-example review;
this is an agent assessment, not independent proof. The open boundary for
placement of derived broader headings remains separate. A rule mapping and
tests using the same declared semantic fixtures cannot certify all examples.
C1 needs correction before a later candidate can be described as having correct
examples; this experiment does not edit it or its fixtures to hide the finding.

## Pre-generation criteria

The [cases](interaction-cases.json) and [spec](interaction-spec.json) are the
fixed inputs. Every post is handwritten for this experiment; the added passage
is the same in every long form. It introduces real independent source subjects
and therefore tests additional semantic work, not token length alone. It is not
copied from a saved regression post and does not establish an exact N096/N100
reproduction. Rubrics and provenance are review-only and never enter POST.

| Cases | Contrast | Required focal meanings |
| --- | --- | --- |
| I001–I004 | Soup seasonings versus seasoning soup, each alone and with identical independent background | Sea salt, pepper, their expressed pair, and their soup-seasoning roles. The individual materials remain subjects alongside their role/action combination. |
| I005–I008 | Beef scraps merely for the writer's dog versus explicitly for feeding that dog, each alone and with the same background | About a quarter pound of beef scraps for the writer's dog; preserve the approximate amount and recipient. Explicit-feeding forms also retain that purpose. |
| I009–I010 | Counted soup ingredients and their qualified sautéing, alone versus background | One medium onion; two tablespoons of olive oil; their soup-preparation roles and expressed ingredient group; sautéing the finely chopped counted onion in the stated oil amount, in a large pan over medium heat, for soup preparation. |
| I011–I012 | Counted chair-repair supplies and their qualified attachment, alone versus background | One steel plate; two steel bolts; chair and drill participants; repair-purpose supplies and their expressed group; attaching the stated plate with the stated bolts to the chair using a drill for chair repair. Do not invent drilling holes. |

Judge equivalent wording by meaning, not exact strings. Before finding a
missing source subject, check all complete subject strings for that meaning;
its presence only in context is insufficient. Require an individual participant
subject, not just its mention inside the whole action. Do not require a
particular optional derived heading or a fixed tree shape.

Review each answer separately for these dimensions:

1. **Focal source coverage:** retain the meanings above, their amounts,
   modifiers, resolved references and expressed relationships. In recipient-only
   dog forms, feeding may be reasonably implied but is not a mandatory added
   interpretation. A feeding-qualified child must be supported by that complete
   post. Do not require an invented food use to make a parent work.
2. **Scope:** inspect every focal parent-child edge by its heading strings.
   Check explicit Seasonings or soup-seasoning roles separately from generic
   Food classification. The later [evaluator audit](../isolation-v1/README.md#evaluator-audit-after-the-food-correction)
   withdraws other-use-only exclusion from Food; de-icing use alone is not a
   classification counterexample. The earlier Seasonings human label remains
   recorded. Dog food/feeding cannot
   contain material merely "for the dog": a chew/scent-training use supplies
   a counterexample. Generic onion/oil/plate/bolt headings cannot inherit a
   preparation or repair role from context. Distinguish unrestricted material
   kinds from headings whose wording actually specifies the role.
3. **Numbered placement:** for each full source action/group, identify the
   returned participant/component headings it necessarily concerns and inspect
   every numbered occurrence of each. The qualified sautéing must appear below
   every compatible counted-onion/oil occurrence; the qualified attachment below
   every compatible plate/bolt/chair/drill occurrence. The full group likewise
   belongs beneath all compatible source components. Descendants count; direct
   duplication beside a containing branch is unnecessary. Ancestors do not
   change the requirements of an identical parent heading.
4. **Exposure:** record whether the relevant seasoning or feeding parent was
   actually returned, and how many compatible numbered component occurrences
   the answer provided. An absent parent is no observed scope error, but does
   not demonstrate a correctly implemented relationship. Do not count it as a
   successful edge test. Source coverage remains a separate check.

Do not reject ambiguous ingredient-group memberships on plausibility alone.
Require a concrete heading-only counterexample or source omission. Conditional
background topics do not assert an actual dam release. Inspect background
subjects for obvious changed/unsupported meanings, but bounded focal acceptance
is not a full-SP pass for the background. Preserve unresolved judgments.

Native agent reviews record the focal coverage, scope, numbered-copy findings,
exposure and exact witnesses. A rejection needs at least one confirmed witness.
An uncertain case has no confirmed rejection witness but a material unresolved
focal judgment. An acceptance concerns these fixed checks only, not every
possible interpretation or the open derived-heading rule. No user labels are
created by this experiment.

## Execution and scale

Use only native prepare/run/show/review. Trial 1 uses the reusable spec;
trials 2 and 3 inherit its exact cases/settings using `--from` and `--repeat`.
All three share `target/sp-autonomous-v1/history` and the existing persistent
1,000-attempt budget at `target/sp-autonomous-v1/attempt-budget.json`.
Do not reset that budget; 210 attempts were used before this experiment.

Provider is subscription `openai-codex`, model `gpt-6.1-sol`, effort `medium`,
transport WebSocket, timeout 1,800 seconds, concurrency 12, no output-token cap
and no paid fallback. Each trial plans twelve fresh answers. The native
provider-only retry policy permits at most two attempts per case; bound each
run to 24 new attempts, including any eligible retries, under the unchanged
campaign ceiling. Failures and retries remain visible and count against it.

This finite diagnostic adds no production stage. SP still has one model call
per post with the existing schema and fixed prompt input. Added output work
comes from the current repeated-branch requirement; input grows with the post
and fixed prompt. Subscription incremental cash is zero, quota use is
unmeasured, and native catalog estimates are not bills. The lifetime monetary
ledger was inspected before launch; no paid commitment is introduced.

Freeze source meanings and these criteria before inference. Keep every trial
even if its quality is poor. Inspect native receipts, exact inputs/settings,
prompt preservation and every answer's output-bound agent review after the
run. Any later example revision uses these cases as development evidence;
fresh-domain validation remains a separate subsequent step.

## Results

All 36 planned answers completed on subscription `gpt-6.1-sol` at medium:
twelve per trial, each on its first attempt. Native reports record valid
answers, zero runner failures and zero answer reuse. The exact source posts,
settings and ASv6.73 rendering were checked across all three trials. Every
answer has a current, output-bound native agent review. The persistent budget
increased from 210 to 246 of 1,000 attempts; no prompt or production change was
made. C2's help/appreciation combination remains an unresolved user question.

The table records agent judgments under the criteria frozen above. Acceptance
is bounded to the focal checks; it does not certify every background subject
or all SP rules. Uncertainty is retained rather than counted as success or
failure.

| Post | Focal contrast | Trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- | --- |
| I001 | Soup seasonings, short | Accept | Accept | Accept |
| I002 | Seasoning soup, short | Accept | Accept | Accept |
| I003 | Soup seasonings, background | Accept | Accept | Accept |
| I004 | Seasoning soup, background | Accept | Accept | Accept |
| I005 | Beef scraps for dog, short | Accept | Accept | Accept |
| I006 | Beef scraps for feeding dog, short | Accept | Accept | Accept |
| I007 | Beef scraps for dog, background | Accept | Accept | Accept |
| I008 | Beef scraps for feeding dog, background | Accept | Accept | Accept |
| I009 | Counted soup ingredients/action, short | Accept | Accept | Accept |
| I010 | Counted soup ingredients/action, background | Accept | Uncertain | Reject |
| I011 | Counted repair supplies/action, short | Reject | Reject | Accept |
| I012 | Counted repair supplies/action, background | Accept | Reject | Reject |

There are five confirmed rejections, one uncertainty and thirty bounded
acceptances. All confirmed errors concern placement, not loss of the complete
focal meaning everywhere. No confirmed focal scope error was found. These are
handwritten development cases, not exact repetitions of N096/N100 or unseen
validation. The earlier fixed original-post comparison still has confirmed
errors in all five ASv6.73 answers for each of N096 and N100.

### Scope and exposure

- All twelve seasoning answers retain qualified sea-salt/pepper soup roles
  and the full pair beneath every checked role-component occurrence. Generic
  **Seasonings** occurs in five of six nominal-list answers; each contains
  qualified children. The sixth returns **Soup seasoning** directly. All
  twelve expose a soup-seasoning parent, with no unrestricted salt beneath it.
  Thus a nominal list heading alone did not reproduce the original error.
- None of the six recipient-only dog answers returns a food/feeding parent.
  They preserve the amount and recipient, but provide **zero observations**
  of the disputed food/feeding edge. Their acceptance is not six successful
  feeding-edge tests. All six explicit-feeding answers expose feeding parents
  and preserve feeding purpose inside their material children.
- Independent background wording showed no obvious unsupported change in
  the bounded inspection. Its complete combination and placement coverage was
  not certified. Conditional dam-release headings do not assert a release.

### Numbered evidence

Two failures have material-group omissions that do not depend on disputed
action/ingredient membership:

- **Trial 3, I010:** the expressed group **Soup ingredients consisting of one
  medium onion and two tablespoons of olive oil** appears only at `3.1.3`.
  It is missing below both copies of **One medium onion for soup preparation**
  (`1.1.1`, `3.1.1`) and both copies of **Two tablespoons of olive oil for soup
  preparation** (`2.1.1`, `3.1.2`). The qualified action appears in those
  branches; it cannot replace the separately expressed ingredient group.
- **Trial 2, I012:** **One steel plate and two steel bolts as chair-repair
  supplies** occurs below counted plate parents `2.1.1.1` and `4.1.1.1`, but
  not identical parents `1.1.1.1` and `5.1.1`. It occurs below counted bolt
  parents `3.1.1.1` and `4.2.1.1`, but not identical parents `1.1.1.2` and
  `5.1.2`. These four omissions survive checking every numbered occurrence.

Three additional repair answers omit the complete attachment below their
expressed whole supplies group: all fourteen group copies in trial 1 I011,
all eleven in trial 2 I011 and all ten in trial 3 I012. Their complete action
heading itself says **Attaching one steel plate to a chair with two steel bolts
using a drill for chair repair**. It states use of the same counted repair
materials, so the subject concerns those supplies without borrowing a role
from context. This is an agent semantic judgment about subject-index placement,
not physical-object subtyping or closure for every derived heading. For example,
trial 2 I011 returns terminal group `1.1.1.1.1` and the complete action at sibling
`1.1.1.1.2`. Trial 1 I011 also omits that action beneath seven copies each of
the counted plate/bolt **as a chair-repair supply** parents. Trial 2 I012 has
terminal group copies too; its independent four component-copy omissions above
are sufficient to reject it.

**Trial 2 I010 stays uncertain.** The complete sautéing heading reaches all
five qualified counted-onion and two qualified counted-oil occurrences, but
none of the four whole ingredient-group copies. Its wording specifies soup
preparation, without explicitly making those materials soup ingredients.
Preparation use need not mean inclusion as an ingredient; the pre-generation
rubric excludes rejecting ambiguous ingredient-group membership. The unchopped
group is also not required beneath a finely-chopped-onion heading.

The short repair post fails in two of three trials, as does its background
form. Short soup preparation has no confirmed failure in three trials;
its background form has one rejection and one uncertainty. Additional context
is therefore not necessary for an incomplete branch. These small contrasts do
not establish that context caused the errors, or explain why original N096/N100
still fail. C1's omitted soup participant independently establishes that the
current examples cannot all be described as correct.

### Verification and next decision

Native experiment directories are `as73-interactions-medium-r1`, `r2` and `r3`
under the ignored campaign experiment root. Their reports, receipts and
`reviews.jsonl` preserve every answer and review; the handwritten source/spec
and this maintained account are committed separately from those artifacts.
The production example/attempt-budget checks passed all 34 tests before
inference, and Git whitespace checks passed. No production API, grading stage
or additional model pass was added.

The next useful change is a reviewable revision of C1: correct its participant
omission and demonstrate an expressed two-material group and complete action
beneath every compatible numbered component/group copy. The short non-food
repair failures give a concrete development target for that demonstration.
Keep the existing instruction contract and seven-case structure, audit the
complete replacement against every applicable rule, then compare the candidate
with fixed ASv6.73 on these cases and the original regression posts. Scope
qualification remains unresolved on the originals and must be checked there;
this diagnostic does not justify declaring it solved. This is a recommendation,
not a prompt revision, adoption or authorization for additional calls.
