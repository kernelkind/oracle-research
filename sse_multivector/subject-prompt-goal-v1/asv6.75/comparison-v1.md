# ASv6.75 fixed comparison with ASv6.74

Status: completed; ASv6.75 is a candidate tested with failures. All 74 fresh
medium answers completed on their first attempt, with current output-bound
native agent reviews and no runner errors or reuse. The user approved testing
this exact draft on 2026-10-02 after reviewing its delta and offline audit.
The plan below was committed as `ce87c96a` before generation and stayed fixed.
No candidate is adopted. Production SP remains ASv6.48; MP is outside scope.

The minimized checks improve from 32/48 to 40/48 bounded accepts, and all six
repair checks remain accepted. Original-post confirmed failures change from
13/20 to 14/20, with three earlier uncertainties becoming decided. Culinary
salt and dog-recipient qualifications improve, but source combinations,
numbered placements and group/member restrictions still fail. These are
development-set agent assessments, not full-SP gold or generalization rates.

## Frozen source and trials

Use the committed ASv6.75 source and ordinary POST template without changes:
source SHA-256 `4a673d7d6c87dc568bcf6043e46bb05c01ca873eacc9c87c4797f12231dc8c70`;
template SHA-256 `ad2d0130f4bf0c1fb4afbeae32209a6ca82a0994b6da539832e34887045e5ccb`.
ASv6.74 source remains
`3c94791e498fa002d05dcdea144770d0b313fffcb01421ca0b251e7f9e247560`.
All instruction bytes and C2–C7 remain unchanged between the two versions.

Prepare only through native `experiment.py prepare --from`, with ASv6.75's
template, prompt ID and `--repeat`. Preserve the exact complete inputs,
evidence, schema and saved baseline output for every selected case. Do not
rerun baselines, select trials by their quality or stop early for quality.

| Cases | Candidate trials | Saved ASv6.74 baseline |
| --- | --- | --- |
| S001–S008, D001–D008 | Three independent trials each: 48 new answers | `as74-scope-min-medium-r1` through `r3`, paired by trial. |
| N063, N074, N096, N100 | Five independent trials each: 20 new answers | `as74-original-medium-r1` through `r5`, paired by trial. |
| I011, I012 | Three independent trials each: six new answers | Select these two cases from `as74-interactions-medium-r1` through `r3`. |

The repair cases inspect regressions after replacing their closely related C1.
The minimized cases inspect scope and source/placement separately. Original
posts inspect transfer within the used regression set. All are development
evidence; this is not unseen-topic validation.

## Criteria fixed before generation

Reuse the committed criteria for
[scope minimization](../autonomous-sp-v1/scope-minimization-v1.md#pre-generation-criteria),
[original posts](../autonomous-sp-v1/README.md#fixed-repeated-comparison-asv658-versus-asv673)
and [repair interactions](../autonomous-sp-v1/interaction-audit-v1.md#pre-generation-criteria).
Judge equivalent wording by meaning, without imposing a tree shape or phrase.

- **Scope:** inspect heading strings alone. Generic salt/oil cannot inherit
  food purpose; tissue or scraps merely for the dog cannot inherit feeding.
  Explicit qualified interpretations are allowed when supported. Inspect other
  displayed restrictions, including counts, medium size, first use and newness.
- **Source:** preserve specific participants, amounts, modifiers, negation,
  references and expressed relationships. Keep source material groups and
  complete actions; separate pieces or context cannot replace their combination.
  The dog trim amount is for the combined tissue/scraps, not each separately.
- **Placement:** inspect every compatible numbered parent occurrence for each
  complete source group/action. Descendants count. Correct scope elsewhere does
  not repair a bare child, and a correct copy elsewhere cannot fill an omitted
  branch. Explicit dog-feeding materials concern every returned Dog food parent,
  including copies otherwise containing only the separate myoglobin topic.
- **Exposure:** report whether food/seasoning/feeding parents were actually
  returned, separately from observed valid/invalid edges. No parent means zero
  observations, not a successful relationship check.

Reject with a concrete confirmed witness. Where no confirmed failure is found
but a material question remains, mark uncertain; bounded acceptance is not
full-SP gold. Keep N063's complete-dish/ingredient-group question, uncertain
ingredient memberships, N100's chicken/myoglobin ambiguity and derived
broader-heading closure outside confirmed rejection counts. Preserve the open
C2 help/appreciation question. These are agent assessments, not user labels.

Record one current output-bound native agent review per completed answer.
Report all trials, including failures/uncertainties, exact numbered witnesses
and changes to baseline findings. Do not collapse scope, source and placement
into a claim that qualification alone fixes the prompt.

## Execution, budget and scale

All eleven experiments use subscription `openai-codex`, exact `gpt-6.1-sol`,
medium, WebSocket, 1,800-second timeout, no output-token cap or paid fallback.
Scope-minimization concurrency stays four per experiment. Original-post and
repair concurrency is one per experiment, overriding the predecessors' four
and twelve solely to bound scheduling. At most twenty requests can be in
flight across the independent native runners; each owns its scheduling.

Plan 74 new answers. The persistent campaign attempt budget starts at 356 of
1,000 and is never reset or refunded. Every run names
`target/sp-autonomous-v1/attempt-budget.json` and the existing history root is
`target/sp-autonomous-v1/history`. Native provider-only retries permit at most
two total attempts per case. Bound each sixteen-case run to 32 attempts, each
four-case run to eight and each two-case run to four, including retries.
All-first-attempt success reaches 430; the full allowed 148 attempts reaches
504, still beneath the campaign ceiling. Retain malformed/local/unknown
failures without ineligible retry or quality-driven reruns.

SP still uses one model pass per post. This finite comparison introduces no
production component; ASv6.75 adds 2,129 fixed UTF-8 input bytes per post.
Hierarchy repetition remains part of the existing contract. Use native reports
for usage, without manual token/cost aggregation. Subscription incremental cash
is zero; quota and provider billing are unmeasured and catalog estimates are
not bills. No paid commitment is added.

The ignored native directories are `as75-scope-min-medium-r1` through `r3`,
`as75-original-medium-r1` through `r5`, and `as75-repair-medium-r1` through `r3`,
under `sse_multivector/experiments/sp-autonomous-v1/`. Before launch, run the
offline example/attempt-budget/revision tests and verify exact frozen source,
rendering, inputs/evidence/settings and paired baselines. After completion,
verify native receipts, fresh attempts, absence of reuse and every review's
current input/output binding. Commit this plan before inference; keep rendered
inputs, model outputs and per-run reports ignored.

## Completed execution and provenance

All eleven native experiments completed their planned cases: three runs of
sixteen minimized cases, five runs of four original posts and three runs of
two repair cases. Every answer is valid with a verified receipt. Each run has
exactly its planned fresh attempt count, zero reused answers and zero failed,
malformed, empty, invalid-receipt or unrun cases. No retries or paid fallback
were used. The persistent budget is **430 of 1,000 attempts**, up from 356.

The 56 offline example/attempt-budget/revision checks passed before launch.
After completion, native `show` refreshed every report and verified receipts.
Read-only checks verified the frozen source/template/code/config hashes,
exact rendering, complete inputs and evidence, paired saved ASv6.74 outputs
and receipts, schema and settings, and all 74 current agent reviews' exact
input/output bindings. The declared concurrency changes are the only runner
setting differences from the saved baselines. Neither prompt changed.

Native reports retain per-run token usage and catalog estimates; none is
manually aggregated here. Subscription incremental cash is zero; quota and
provider billing remain unmeasured. The experiment directories and generated
answers/reports are ignored artifacts. Use native `show --case ID` within the
named trial to inspect the complete post, headings, receipt and agent review.

## Minimized cases: all trials

**A** means accept under the bounded focal criteria; **R** means a confirmed
rejection. Each sequence is trial 1, 2, 3. No candidate answer is uncertain.
The saved baseline assessments are unchanged.

| Case | ASv6.74 | ASv6.75 | Candidate finding |
| --- | --- | --- | --- |
| S001 | A A A | A A A | Salt/pepper, to-taste meaning and checked placements retained. |
| S002 | A A A | R A A | Trial 1 omits the complete recipe-qualified pair beneath Food. |
| S003 | A A A | A A A | Focal recipe-qualified salt/pepper pair and checked role copies retained. |
| S004 | R R R | R R A | Bare-Salt culinary failure absent; trial 1 misses a dish copy, trial 2 reverses group/member direction. |
| S005 | A A A | A A A | Explicit seasoning purpose and complete pair retained. |
| S006 | R A R | A R R | Trials 2/3 omit the complete seasoning-pair/recipe relationship. |
| S007 | A A A | A A A | Sea-salt seasoning scope and complete pair retained. |
| S008 | A A A | A A A | Sea-salt recipe pair and checked qualifications retained. |
| D001 | A A A | A A A | Counted recipient material retained; no food/feeding parent exposure. |
| D002 | A A A | A A A | Myoglobin food parents exposed; recipient-only material stays outside. |
| D003 | A A A | A A A | Explicit feeding materials/actions correctly qualified and placed. |
| D004 | R R R | A A A | Complete feeding materials/actions fill both Dog food copies in all trials. |
| D005 | A A A | A A A | Joint fat/tissue trimming retained; no food/feeding parent exposure. |
| D006 | R R A | A R A | Trial 2 omits the joint fat/tissue trimming heading. |
| D007 | R R R | R A R | Dog scope improves; trials 1/3 still omit the joint trimming heading. |
| D008 | R R R | A A A | Joint trimming retained; zero dog-food/feeding parent exposure in all candidate trials. |

The totals are 32 accepts/16 rejections for ASv6.74 and 40 accepts/eight
rejections for ASv6.75. These counts include source and placement checks;
qualification alone does not determine a verdict.

### Target relationships and exposure

| Check | ASv6.74 | ASv6.75 | Candidate exposure |
| --- | --- | --- | --- |
| S004 unrestricted salt beneath a culinary parent | 3/3 failures | 0/3 failures | Food returned in all three trials, with qualified salt below it. |
| D004 explicit feeding subject absent beneath Dog food copies | 3/3 failures | 0/3 failures | Two Dog food copies in every trial; all six copies contain the full material/action. |
| D007 recipient-only tissue/scraps beneath dog-food parents | 1/3 failures | 0/3 failures | Two Dog food copies in every candidate trial, used for myoglobin. |
| D008 recipient-only tissue/scraps beneath dog-food parents | 2/3 failures | 0/3 observed failures | No candidate dog-food/feeding parents: zero observations of this edge. |

D001/D005 likewise provide no food/feeding exposure. D002/D003/D006 expose
food parents in all candidate trials and preserve the checked purpose
restrictions. D008's accepted source combinations do not establish that the
missing dog-food edge was corrected. The full N100 results below supply
additional observations with actual dog-food parent exposure.

### Confirmed minimized witnesses

- **S002 trial 1:** Food `1` contains only the pasta/dish branch. None of the
  twelve complete salt/pepper-to-taste recipe-pair copies is beneath it.
- **S004 trial 1:** Spaghetti bolognaise `2.1.1.1` lacks the complete
  recipe-qualified salt/pepper pair. The qualified seasoning copies elsewhere
  cannot fill this named-dish occurrence.
- **S004 trial 2:** the complete salt/pepper pair at `1.1.1.1.1.1` parents
  salt alone at `1.1.1.1.1.1.1`. A salt-only subject need not concern pepper;
  the child drops the parent's other member. The direction recurs elsewhere.
- **S006 trials 2/3:** every seasoning-pair heading lacks its expressed
  relationship to the author's recipe serving five. Separate recipe and
  seasoning headings do not replace the combined source subject.
- **D006 trial 2; D007 trials 1/3:** all trimming headings represent the
  quantified fat/tallow and combined tissue/scraps/dog actions separately.
  No heading retains their complete joint relationship. D006 trial 2's
  `7.1`/`7.2` and D007 trials 1/3's `5.1`/`5.2` and `11.1`/`11.2` are witnesses.

D004's successful candidate Dog food occurrences are `4.1`/`5.1` in trials
1/2 and `3.2`/`4.1` in trial 3. The full quantified feeding material and
trimming action occur beneath each through the material branches. This is
source-subject placement, not derived broader-heading closure.

## Original posts: all trials

**U** means the earlier assessment remains uncertain. Sequences are trials
1 through 5; each post has five fresh candidate answers.

| Post | ASv6.74 | ASv6.75 | Confirmed failures, baseline → candidate |
| --- | --- | --- | --- |
| N063 | U U U A R | A A R A A | 1/5 → 1/5; three baseline uncertainties remain recorded. |
| N074 | A R A A R | A A R R R | 2/5 → 3/5. |
| N096 | R R R R R | R R R R R | 5/5 → 5/5. |
| N100 | R R R R R | R R R R R | 5/5 → 5/5. |

The candidate has six bounded accepts, fourteen confirmed rejections and no
uncertain answers. The baseline has four accepts, thirteen rejections and
three uncertainties. These are small independent trials on used development
posts; neither their ordering nor a changed count proves causation.

| Focal scope check | ASv6.74 | ASv6.75 | Candidate exposure |
| --- | --- | --- | --- |
| N063 unrestricted oil/salt beneath culinary parents | 1/5 failures | 0/5 failures | Culinary food/ingredient parents returned in all five trials. |
| N096 unrestricted Salt beneath culinary parents | 3/5 failures | 0/5 failures | Culinary ingredient/seasoning parents returned in all five trials. |
| N100 recipient-only tissue/scraps beneath dog-food/feeding parents | 5/5 failures | 0/5 failures | Dog-food parents returned in all five trials. |

These rows concern their stated restrictions. The N096 group/member failure
below is another scope violation, and N100 retains other source/scope errors.

- **N063:** trials 1/2/4/5 retain all fifteen individually qualified ingredient
  subjects and the explicit group or complete ingredient combination beneath
  the checked dish/group/role copies. Trial 3 returns the dish at `1.1.1.1`
  without any ingredient-group descendants; the complete ingredient group at
  `1.2.1` cannot fill that occurrence. All five keep generic oil/salt outside
  culinary parents. None uses the earlier full-dish-only representation, so
  that unresolved semantic question is not needed for these verdicts.
- **N074:** trials 1/2 retain the complete three-part advice attributed to
  Michael Pollan's Food Rules beneath the checked advice components and book
  copies. In trial 3, the attributed full combination exists only at
  `14.1.1`/`15.1.1`, missing real-food recommendation `11.1.1` and the other
  component copies. Trial 4 has the same omission, including real-food advice
  `7.2.1`. Their generic three-part copies lack the attribution. Trial 5 names
  Michael Pollan in the full advice but never its Food Rules relationship;
  book copies `5.3.1`/`12.1` have no advice descendants. The checked comparative
  controversy/mother/ten-year-old exception is retained in all five.
- **N096:** trial 1's complete sautéing at `3.1.2` retains ingredient counts,
  large pan and medium heat but drops recipe purpose, as do its other copies.
  Trial 2's sautéing at `4.2.1` additionally drops the ingredient amounts and
  onion/carrot medium-size qualifications; no complete source action repairs
  those omissions. Trial 3 retains counts but again drops recipe purpose.
  Trials 3/4/5 also reverse group/member direction: combined salt/pepper at
  `1.3.9`, `1.1.2.9` and `2.2.1.9`, respectively, parents salt alone at each
  parent's `.1` child. Trial 5 retains full recipe-qualified sautéing at
  `13.4.1.1`/`13.4.2.1` but omits it beneath bare counted onion `4.1.1`, celery
  `4.2.1`, carrot `4.3.1` and olive-oil amount `10.1`. Its basil addition at
  `13.4.1.6` also drops the source bunch. Ingredient-membership uncertainty
  is not needed to establish any of these rejections.
- **N100:** all five retain the two separately quantified trimming actions but
  omit their complete joint source combination. Trial 1's `4.2.1`/`4.2.2`,
  trial 2's `7.1`/`7.2`, trial 3's `2.1.1.3`/`2.1.1.4`, trial 4's
  `2.1.3.1`/`2.1.3.2` and trial 5's `5.2.1`/`5.2.2` are witnesses. Generic
  trimming headings omit their amounts/purposes. Trial 3 additionally changes
  the general model recommendation to a recommendation of the **new** Nesco
  at `12.1.1.4`/`18.1`, adding an unsupported restriction. Trial 5 places the
  general model recommendation `15.1.1.5` beneath New Nesco `15.1.1`, dropping
  newness. Raw dog-recipient material stays outside dog-food parents or is
  explicitly food-qualified. The chicken/myoglobin ambiguity remains excluded;
  deciding whether trial 4's "Finally using" conveys first use is unnecessary
  for its confirmed rejection.

## Repair regression checks

All six candidate answers and all six paired ASv6.74 answers satisfy the
bounded I011/I012 checks. Counted plate/bolt subjects, their expressed supply
group and complete chair-repair attachment action retain counts, repair purpose,
chair and drill, beneath every checked compatible occurrence. The participants
remain individually represented. I012's additional camera, bicycle and
attributed two-part advice subjects retain the inspected qualifiers; this is
not independent full-post gold for that background material.

| Case/trial | Qualified plate copies | Qualified bolt copies | Full group copies | Complete action copies |
| --- | --- | --- | --- | --- |
| I011/1 | 4 | 4 | 8 | 12 |
| I011/2 | 5 | 5 | 10 | 15 |
| I011/3 | 5 | 5 | 10 | 16 |
| I012/1 | 3 | 3 | 6 | 10 |
| I012/2 | 2 | 2 | 4 | 7 |
| I012/3 | 5 | 5 | 10 | 14 |

For example, I011 trial 1 has the counted plate at `1.1.1.1`, complete supply
group at `1.1.1.1.1` and complete attachment at `1.1.1.1.1.1`. I012 trial 2
retains the same meanings at `1.1`, `1.1.1` and `1.1.1.1`, including the full
action beneath every other checked plate/bolt/group occurrence. Correct meaning
and placement were inspected; counts alone do not determine acceptance.

## Interpretation and recommended next step

ASv6.75 provides observed progress on culinary purpose and explicit dog-food
placements, including the full original posts with actual parent exposure.
It does not reliably retain complete source relationships or all their copies.
N074's confirmed failures increase in these trials, and N096/N100 still fail
every original answer. The prior repair gains survive this comparison.

The strongest concrete next target is the reversed combined-parent/member-child
pattern in S004 and three N096 answers. C1, C6 and C7 already show the valid
combination-below-components direction; simply adding another such output would
duplicate existing demonstrations. Recommend a small controlled revision of
an existing example's explanation to state why the reverse direction drops a
member, followed first by the saved short S004 contrast. This tests whether
explaining the existing demonstration changes that particular failure before
another long-post sweep. It is a recommendation, not an authorized new draft or
run, and would not by itself settle the separate combination omissions.

C2 help/appreciation, N063's alternative group representation, uncertain
ingredient memberships and derived broader-heading closure remain open. No
candidate is adopted and no change to MP or production is made.
