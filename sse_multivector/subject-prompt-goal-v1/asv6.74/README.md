# ASv6.74 C1 revision and fixed comparison

Status: candidate, tested with failures. The user approved the C1 revision and
comparison on 2026-10-02. All fifty-six planned candidate answers and their
native agent reviews are complete. ASv6.73 is the fixed comparison baseline.
Frozen production SP remains ASv6.48; MP and adoption are outside this task.

[ASv6.74](ASv6.74.md) changes only C1's complete example. All instruction bytes,
the other six complete examples and the output schema remain unchanged. Native
`experiment.py revise` assembled both the source and ordinary POST template,
with their revision receipts. This candidate introduces no additional rule.

## Example correctness and coverage

C1 now supplies a counted steel plate and two steel bolts for chair repair,
then refers to them in attachment to the chair. Separate steel-plate, steel-bolt
and chair topics remain alongside the action. The expressed repair-material
group appears beneath all three qualified plate copies and all three qualified
bolt copies. Its complete attachment appears beneath all six group copies,
all three repair-qualified attachment headings and the counted attachment
heading: ten copies in total. Descendants provide coverage without an additional
direct duplicate beside their containing branch.

Every displayed edge was reviewed using its headings alone. The complete action
states the same counted materials, attachment and chair-repair purpose; no
parent supplies a missing restriction. Generic counted materials and the
unqualified attachment remain outside Chair repair: the same materials and
attachment could be used to build furniture instead. Each context identifies
source support, including the list heading and resolved references. No drilling,
extra tools or calculated total is invented. Source participants, individual
counted materials, their expressed group and their action are all retained.

C1 has 35 entries and fourteen distinct headings, replacing sixteen entries
and eight headings. The complete source grows from 18,196 to 21,533 UTF-8 bytes,
an additional 3,337 bytes of fixed input per post. SP still makes one model
call per post; the hierarchy's repeated branches remain part of the existing
contract. This revision adds no production component or model pass.

The primary clause assignments stay those in the maintained
[34-clause map](../autonomous-sp-v1/README.md#rule-coverage-for-asv661).
C1 demonstrates its sixteen primary clauses as follows:

| Clauses | Demonstration |
| --- | --- |
| R01, R02, R04 | Understand the heading/list/action together; resolve `it` to one steel plate and `them` to two steel bolts with supported repair purpose. |
| R16 | The counted repair materials, expressed group and complete action remain beneath broader headings; no internal reasoning trace is added. |
| R20, R29 | Generic material and attachment headings retain their generality; their source context cannot place them beneath Chair repair. |
| R21, R22 | Shared qualified material, group and action subjects fill every compatible numbered parent occurrence. |
| R23, R25, R26 | Each entry has its own broad-to-specific section number, parents first, with fields ordered number/context/subject. |
| R27, R28 | Contexts name source support and may describe this repair instance for a general material topic. |
| R30, R31, R34 | Concise, standalone headings resolve references and retain their own restrictions without repeating the whole assertion at every level. |

R18's existing secondary demonstration now includes the two-material group;
R24 still contrasts nonempty C1 with empty C3. C1 additionally demonstrates
R19's participant retention, whose primary case stays C5. The five tracked
implications retain their original rule assignments. C2–C7 retain their
ASv6.73 mappings and earlier audit findings: C2's help/appreciation combination
remains unresolved. Do not claim that all seven examples have independent
semantic certification.

The participant test first failed against ASv6.73 for its missing Soup subject.
It now checks the replacement participants; another test preserves that old
failure as evidence. Production subjects validation precedes every example
check. The tests inspect every source-subject placement and displayed edge
against the reviewed semantic relationships, prohibited purpose/group edges,
field order, unchanged instructions and six unchanged examples. All forty
example/attempt-budget tests passed. These fixtures encode agent judgments;
they do not independently prove meaning or model generalization.

## Pre-generation comparison

Freeze ASv6.74 for all fifty-six planned candidate answers, without revising it
or stopping early based on quality:

- Twelve [interaction posts](../autonomous-sp-v1/interaction-cases.json),
  three independent medium trials each: thirty-six new answers, paired with
  all three saved ASv6.73 interaction trials.
- Original complete N063, N074, N096 and N100 posts, five independent medium
  trials each: twenty new answers, paired with all five saved fixed ASv6.73
  original-post trials. No baseline is rerun or selected by its quality.

Use native `prepare --from`, the ASv6.74 POST template and `--repeat`. Preserve
each corresponding baseline's exact source posts, evidence and runner settings:
subscription `openai-codex`, `gpt-6.1-sol`, medium, WebSocket, 1,800-second
timeout, no output-token cap or paid fallback. Interaction concurrency is
twelve; original-post concurrency is four. Each native run owns its scheduling.

Reuse the criteria committed before the ASv6.73 runs:
[interaction criteria](../autonomous-sp-v1/interaction-audit-v1.md#pre-generation-criteria)
and [original-post criteria](../autonomous-sp-v1/README.md#fixed-repeated-comparison-asv658-versus-asv673).
Inspect every numbered occurrence, not just distinct heading pairs. Retain
uncertain ingredient-group memberships and the open derived-heading-placement
boundary. Missing food/feeding parents do not count as successful edge tests.
Record each candidate's current output-bound native agent review separately
from user labels. Bounded acceptance is not a full-SP gold pass. Report scope,
source coverage, placement witnesses and exposure separately, including new
regressions. The repair diagnostic shares material/action structure with C1,
so it is development evidence; soup and original-post comparisons test transfer
within this already-used set, not unseen generalization.

The existing persistent attempt budget starts at 246 of 1,000 and is never
reset. Every run names `target/sp-autonomous-v1/attempt-budget.json`. Bound each
twelve-case run to twenty-four attempts and each four-case run to eight,
including any eligible provider retries. Native provider-only retry policy
permits at most two attempts per case; failures remain visible. If every answer
succeeds on its first attempt, the budget will reach 302. Subscription
incremental cash is zero, quota use is unmeasured and catalog estimates are
not bills. The lifetime ledger was inspected before launch; no paid commitment
is introduced.

Native directories are `as74-interactions-medium-r1` through `r3` and
`as74-original-medium-r1` through `r5`, under the ignored campaign experiment
root. Preserve all reports/receipts/reviews and verify exact frozen prompts,
inputs, settings, fresh-attempt counts and review bindings after completion.
No candidate is adopted by this experiment.

## Completed comparison

All fifty-six fresh answers completed on their first attempt, with valid native
receipts, no runner errors and no answer reuse. The prompt stayed fixed through
all eight experiments. Post-run checks verified the exact frozen source/template,
rendering, paired complete inputs/evidence/settings and saved baseline outputs.
Every answer has exactly one current agent review bound to its input and output
hashes; none is a user label. The persistent budget is 302 of 1,000 attempts.
The forty offline example/attempt-budget tests passed before generation.

The C1 revision improved the closely related repair diagnostics, but did not
reduce confirmed-error counts on any original post. The increased uncertainty
on soup and N063 also prevents claiming an overall improvement.

### Interaction diagnostics

These are bounded focal judgments, not full-SP correctness labels. Each family
includes its short and independent-passage forms, three trials each.

| Family | Saved ASv6.73 answers | Fresh ASv6.74 answers | Exposure and finding |
| --- | --- | --- | --- |
| Seasoning, I001–I004 | 12 bounded accepts | 12 bounded accepts | Qualified soup-seasoning subjects retained. Generic Seasonings appears in 5/6 nominal answers in each arm; the original salt failure is not reproduced. |
| Dog recipient, I005/I007 | 6 bounded accepts | 6 bounded accepts | Neither arm returns food/feeding parents in any answer. These are zero exposures of the original failing edge, not six successful edge checks. |
| Explicit feeding, I006/I008 | 6 bounded accepts | 6 bounded accepts | Feeding parents and qualified children occur in all six answers in each arm. |
| Soup placements, I009/I010 | 4 bounded accepts, 1 rejection, 1 uncertain | 1 bounded accept, 5 uncertain | No confirmed missing copy in ASv6.74; ingredient-role wording remains uncertain. |
| Repair placements, I011/I012 | 2 bounded accepts, 4 rejections | 6 bounded accepts | All qualified material/group/action copies checked. |

The thirty-six diagnostic reviews total 31 bounded accepts and five uncertain
for ASv6.74, versus 30 bounded accepts, five rejections and one uncertain for
ASv6.73. Five uncertainties are not five passes or evidence of a general fix.

Every ASv6.74 repair answer has four qualified plate copies and four qualified
bolt copies, each containing the complete two-material group. All eight group
copies contain the complete counted attachment with repair purpose and drill.
For example, trial 1 I011 fills groups at 1.1.1.1, 2.1.1.1, 3.1.1.1.1,
3.1.1.2.1, 4.1.1.1.1, 4.1.1.2.1, 5.1.1.1 and 5.1.2.1. Trials 2 and 3
retain these placements with alternative supported wording. This is observed
transfer from a very similar example, including the same materials and repair
purpose; it does not establish transfer across topics.

The five uncertain soup answers describe materials or their group as being
"for soup preparation" where ingredient role matters. Preparing soup can
involve a material without making it a soup ingredient. The heading-alone
relationship and source ingredient-group retention therefore remain uncertain;
do not infer membership from nearby branches or demand one exact wording.
Trial 1 I009 explicitly qualifies the complete action as involving soup
ingredients and satisfies the bounded placement checks. The saved baseline
reviews are preserved, rather than retrospectively relabelled.

### Original regression posts

| Post | ASv6.73 answers with confirmed errors | ASv6.74 answers with confirmed errors | Additional ASv6.74 uncertain answers |
| --- | --- | --- | --- |
| N063 | 1/5 | 1/5 | 3/5 |
| N074 | 2/5 | 2/5 | 0/5 |
| N096 | 5/5 | 5/5 | 0/5 |
| N100 | 5/5 | 5/5 | 0/5 |

ASv6.74 has thirteen rejections, three uncertain answers and four bounded
accepts on the twenty original-post answers. ASv6.73 has thirteen rejections
and seven bounded accepts. Equal confirmed-error counts do not establish equal
quality: N063 introduces a new scope error, while three other answers change
the ingredient-group representation and cannot be confidently accepted.

- **N063:** trial 5 places unrestricted Olive oil 1.10 and Salt 1.13 beneath
  Food 1; lamp oil and de-icing salt supply counterexamples. This material-scope
  failure occurs in 1/5 ASv6.74 answers versus 0/5 saved ASv6.73 answers. The
  full fifteen-ingredient dish combination also occurs only at 1.1.1.1.16,
  missing all forty-five qualified ingredient-role copies; Arborio rice copies
  1.1.1.1.2, 1.3.1.1 and 3.1.2 provide witnesses. Trials 1–3 retain a complete
  dish description naming all fifteen ingredients without a separate ingredient
  group heading. Whether that representation retains the source's group remains
  open; trial 3 also lacks separate individually qualified ingredient headings.
  Trial 4 retains each individual role and the explicit complete ingredient
  group beneath all fifteen qualified roles and all three dish copies. That
  specific group names all fifteen ingredients: a lone member cannot inherit
  the other fourteen restrictions by being placed below it. Accepting the
  valid group-below-components direction does not impose an exact phrase.
- **N074:** trial 2 returns the full book-attributed advice only under book
  copies 11.1 and 12.1. It is missing below real-food advice 6.2/7.2.1,
  moderation advice 6.3 and mostly-plants advice 6.4/7.3.1, as well as all five
  unattributed combined-advice copies. Trial 5 omits Food Rules attribution from
  every complete advice heading. All five answers preserve the diet comparison
  with its mother/child exception beneath the checked comparison and instruction
  copies. Trials 1, 3 and 4 satisfy the bounded checks.
- **N096:** Seasonings → Salt occurs in trials 2, 3 and 5: 12 → 12.1,
  11 → 11.2 and 2.2.9 → 2.2.9.1. That is 3/5 answers in each arm. Trial 1
  returns no Seasonings parent, so it provides no exposure of that edge. Trial
  4 qualifies salt but still places unrestricted Olive oil beneath Cooking
  oils. All five answers have confirmed errors. Trial 1, for example, places
  the complete recipe-qualified sautéing subject below onion copy 4.1.1 but
  omits identical copies 1.1.2.1 and 2.1.2.1. Three trials' complete sautéing
  headings omit recipe purpose; retaining it elsewhere cannot repair a child.
- **N100:** all five answers place material merely "for the dog" beneath a
  food/feeding parent, as do all five baseline answers. Trial 1's Animal feeding
  14 → About a quarter pound of connective tissue and scrap meat for the dog
  14.2 and trial 3's Dog food 12.1 → the same material 12.1.1 provide witnesses.
  Material for a chew toy fits the child without feeding purpose. Trials 1 and
  4 also put a general model recommendation beneath New Nesco; trial 3 drops
  first-use scope from appreciation beneath a first-use parent. The ambiguous
  myoglobin/chicken reading remains outside confirmed failure counts.

### Interpretation and next step

This example correction improves a local material/action pattern. It does not
explain why the original salt and dog failures persist while the short controls
avoid them. The dog-recipient controls never return the relevant food/feeding
parents; the seasoning controls use Sea salt and explicit soup wording rather
than the original salt/recipe context. Broadly rewriting another example from
these results would not identify the cause.

The approved [salt/dog minimization](../autonomous-sp-v1/scope-minimization-v1.md)
is now complete, with 54 fresh medium answers under this unchanged prompt.
Short posts reproduce Food → Salt in 3/3 title/line/hashtag answers and dog-food
parents containing recipient-only material in 2/3 trimming/hashtag answers.
Other variants preserve scope but lose source relationships or numbered
placements. The linked report separates exposure and exact witnesses from
bounded accepts, with the full-original controls kept as their own trials.
The user subsequently approved drafting that existing-example revision. The
resulting [ASv6.75 (candidate, approved for testing)](../asv6.75/README.md) demonstrates those
food-parent relationships while retaining the prior rule coverage. This
ASv6.74 candidate and its saved comparison remain unchanged. Review of the
exact draft subsequently led to the approved [fixed comparison](../asv6.75/comparison-v1.md);
the drafting task made no model calls. Adoption remains open.

Two semantic questions remain open: the C2 help/appreciation combination and
N063's complete-dish versus separate ingredient-group representation. Neither
has a user answer; do not treat silence as approval. Derived broader-heading
placement remains excluded as before. No candidate is adopted.
