# ASv6.97 Food classification example correction

Status: tested experimental draft; clear failures remain; not adopted.
The user approves correcting C1 after the [Food evaluator audit](../isolation-v1/README.md#evaluator-audit-after-the-food-correction),
then testing the corrected prompt. Production adoption remains a separate decision.

[ASv6.97](ASv6.97.md) changes only C1's post, explanation and output from
ASv6.96. The ten instruction paragraphs and C2–C7 remain byte-identical. C1
uses sea salt rather than generic salt, demonstrates Food → Sea salt, and
removes the explanation that alternative uses disqualify food substances.
The complete Sea salt for food seasoning subject remains under both Sea salt
copies and Food seasoning. This preserves the expressly stated purpose without
deciding whether every culinary heading names a class or a particular use.

The new output adds two entries, from 54 to 56 in C1 and 137 to 139 overall.
The existing counted ingredients, group, partial cutting, complete cutting and
all compatible copies remain. Optional general tissue/meat headings need not
repeat a particular use; their standalone placement does not establish exclusion
from Food. No optional broader-heading closure or production stage is added.

## Example coverage and verification

The [34-clause and five-implication map](../asv6.96/README.md#actual-instruction-and-example-coverage)
keeps its primary assignments. C1's concrete witnesses are:

| Existing clauses | Corrected C1 demonstration |
| --- | --- |
| R01, R02, R04, R16 | Enclosing ingredient role, counted tissue/scraps, resolved it/them, complete source meanings. |
| R20, R29 | Food → Sea salt demonstrates type membership; Sea salt for food seasoning retains the stated purpose. |
| R21, R22, R23 | Both Sea salt copies and both Dog food branches retain their compatible complete source descendants. |
| R25, R26 | Each heading has its own number; parents precede children; number/context/subject field order is preserved. |
| R27, R28 | Context establishes source support without adding restrictions to a heading. |
| R30, R31, R34 | General Sea salt and Dogs coexist with complete specific subjects; general headings need not retell each instance's use. |

The five tracked implications retain their witnesses: complete versus partial
combination direction; explicit restrictions in a heading; every compatible
numbered copy; general versus purpose-qualified meanings; parent restrictions
retained in child wording. Shared-predicate and separate-participant coverage
also remains. C2–C7 retain every other primary assignment.

The minimal new production-validator check first fails on ASv6.96 because C1
lacks the accepted Food → Sea salt demonstration. The revised prompt passes
146 focused example, consolidation, native revision and attempt-budget checks.
These checks verify authored fixtures and production validation, not model
accuracy. Two independent semantic reviews inspect the actual edges and source
copies and find no new inconsistency; this does not establish model repair.

Native source and template revisions use pinned [source edits](prompt-edits.json)
and [template edits](edits.json), preserving the exact POST wrapper. Source SHA256:
`4533c70516beccd4c1b444b1d1c1819e2e3e72c95e78958983b662cf0e2be06a`.
This follows the official guidance on [direct instructions and aligned examples](https://developers.openai.com/api/docs/guides/reasoning-best-practices);
guidance compliance does not establish success on this task.

## Fixed regression test

Freeze three native six-case plans before inference, using ASv6.96's saved
trials as historical baselines. Each plan contains N063, N074, N096, N100,
S006 and D006, with complete original POST inputs. Native `prepare --from`
inherits settings and source evidence, uses the new template and `--repeat`,
and preserves the saved answer without rerunning it. Baseline snapshot reviews
are omitted by native preparation; the following corrected verdicts are read
from the original live native runs, not inferred from textual comparison fields.

| New native run under experiments/sp-autonomous-v1/food-classification-v1 | ASv6.96 baseline under guidance-consolidation-v1 | N063 / N074 / N096 / N100 / S006 / D006 |
| --- | --- | --- |
| Q1 | E03, trial 1 | A / U / R / R / A / A |
| Q2 | E04, trial 2 | A / U / R / R / R / A |
| Q3 | E01, trial 3 | A / U / R / R / A / A |

A/R/U are bounded agent accept/reject/uncertain labels, not human whole-answer
gold. Historical baseline totals are 8 accept, 7 reject and 3 uncertain.
This is a development-set screen with historical controls; it does not establish
a causal effect, unseen generalization or reliable SP correctness.

Settings remain subscription openai-codex/gpt-6.1-sol/medium, WebSocket,
1,800-second timeout, no output cap, concurrency one per native runner. Three
native runners together allow three in-flight requests. The actual history root
remains experiments/sp-autonomous-v1. Plan 18 first attempts, with at most two
total attempts per case only for the existing permitted provider-transient retry.
Use `run --max-new-attempts 12` per plan and the unchanged persistent
target/sp-autonomous-v1/attempt-budget.json: 1,487/2,000 before this screen.
No quality retry, early quality stopping, model switch or paid fallback follows
a result. Subscription calls add zero incremental cash; quota is unmeasured.
All eight prospective posts remain reserved.

Review complete posts and answers through native `show`. Answer reviewers receive
the unchanged parsed answer and POST without the prompt or old verdicts. Record
their assessments through native `review`, preserving disagreements separately.
Agent agreement does not establish human accuracy. Apply these fixed criteria:

- Food membership is not disproved by another use. Report actual parent exposure;
  do not demand an optional Food heading or fail Sea salt beneath Food.
- Preserve complete ingredient meanings/groups, recipe-qualified seasoning pairs,
  quantified full/partial sautéing and joint trimming, and their compatible copies.
  A complete shared action can retain its participant group without a separate
  non-action group node. The quarter-pound tissue/scrap amount remains combined.
- Judge every actual edge by its heading meanings, distinguishing type/class from
  a stated purpose, modifier or relationship. Alternative uses alone do not settle
  uncalibrated culinary-class meanings. Keep the earlier Seasonings → Salt user
  label separate from generic Food membership.
- A source subject never correctly formed is source loss; a formed source missing
  a compatible occurrence is a copy failure. Equal meaning represents itself;
  another branch cannot repair a missing compatible copy.
- Preserve N074 interpretation and dinner-attachment uncertainty. An implicit
  N100 sirloin-origin objection alone remains uncertain, not a decisive rejection.
  S006 accepts reliable for never-fail and does not demand an absent easy claim.

Any clear original-post rejection prevents a reliable-fix claim. Complete all
fixed trials and record results even if the first answer fails. Rendered requests,
answers and native reports stay ignored artifacts. This changes only the prompt's
example demonstration; per-request context remains one prompt plus one post.

## Completed results

All 18 planned medium calls complete with valid first answers, no errors, retries,
reuse or unrun cases. The persistent counter is 1,505/2,000. All 146 focused
checks pass; the source/template stay frozen at pre-inference commit `982a5c7c`.
The actual SDK inputs match the frozen requests; structural validity and authored
example audits do not imply correct teacher behavior.

| Case | Q1 | Q2 | Q3 | Remaining finding |
| --- | --- | --- | --- | --- |
| N063 | A | U | A | All 15 ingredient roles and full list copies retained; Q2 Foodstr-to-Nostr membership remains open. |
| N074 | R | R | R | Complete mother/ten-year-old vegetable instruction missing compatible Plants as food, Food intake or Dietary advice copies. |
| N096 | R | R | R | Full quantified sauté retained; other complete instruction copies or source quantities/recipe identity missing. |
| N100 | R | R | R | Full shared trimming retained; Q1 misses a Beef copy on its chosen reading, Q2 a Tallow copy, Q3 a long-awaited-use qualifier. |
| S006 | R | R | R | Seasoning sources lose the complete enclosing recipe relationship. |
| D006 | R | R | R | Q1/Q2 miss Food copies; Q3 omits the full shared trimming action. |

Current totals are 2 bounded accepts, 15 rejects and 1 uncertain. The original-
post subset is 2/9/1 among 12; all six diagnostics reject. The historical baseline
labels remain 8/7/3, but their differing time and assessment history prevent a
causal regression claim. This is not a reliable SP correction or population
accuracy estimate. The eight prospective posts remain unused.

Concrete independent witnesses, checked through native `show`, include:

- Q2 N096 forms its full quantified sauté at 1.1.1.2.1, but Cooking instructions
  4 contains only spaghetti packet instructions/cooking. Its context cannot
  restrict that general heading to the packet.
- Q2 N100 forms the complete two-portion trimming at 1.1.2.1.1, but Tallow 3.2
  collects only the partial tallow-making source. The combined quarter-pound
  tissue/scrap amount is preserved; inferred origin is not the rejection basis.
- Q3 N100 parent 12.1.1 specifies the author's long-awaited use of the new sealer;
  child 12.1.1.1 names love after using it and omits long-awaited qualification.
- Q1/Q2 D006 form the complete joint trimming at 1.1.1.1 but Food 8/9 collects
  only saved myoglobin for dog food. Scrap meat is a food substance; another
  participant's tallow purpose does not exclude the full action's Food topic.
  The more-specific dog-feeding role is kept as a separate uncertainty.
- Q3 D006 forms only partial fat/tallow and tissue/scrap/dog trimming. The
  expressed complete shared action never forms, so this is source loss rather
  than an independent missing-copy count.

Food appears in 10 of 18 answers. N063's sea salt is always qualified as a dish
ingredient, so there is no direct generic Food → Sea salt exposure in this
screen. Q1 S006 directly returns Food → Salt/Pepper; those class edges are
accepted, while its missing recipe relationship independently rejects. No
Seasonings → bare Salt rejection is used. Correcting the authored example is
established; general transfer of its class distinction is not.

## Assessment corrections and limits

Two answer reviewers see only complete POST and unchanged parsed subjects,
without prompt/version or old labels. Their initial judgments reveal another
contract error: one initially requires is-a-only edges, rejecting dish → its
ingredients and Food → food sharing. The existing subject-index contract allows
topics about their parent through actions/relationships; the three initial
N063 rejects are withdrawn. This is a grader correction, not a teacher repair.

The duplicated some in N100 also remains open: the first some could refer to
saved myoglobin, or be a repeated word. The initial invented chicken-link
objection is withdrawn as decisive evidence. Q1's selected beef-myoglobin
chicken provision still lacks a Beef copy whenever that reading is supported.
Q3's initial uncertainty changes after an actual missing parent qualifier is
identified. N074 readings, dinner/purchase attachment, sauce membership and
implicit sirloin origin stay separate from independently supported failures.

Native history preserves six initial/superseded judgments and the subsequent
reviewer verdict summaries and broker assessments. Earlier reviewer-labelled
comments include combined broker witnesses; the latest broker event explicitly
separates each reviewer's actual reasons, including the Q3 N096 mixing claim:
missing participant quantities are source loss, not an independent mixing-copy
failure. All 78 events match the unchanged input/output hashes. Scoring uses
one latest clarified broker verdict per case; hash-current does not mean latest.
No human whole-answer labels or independent agreement-rate claim is invented.

The useful next prompt target is S006's short, repeated loss of the enclosing
recipe relationship. Its source defect survives the corrected Food interpretation
and provides a concrete example requirement before another wording change.

The user approves this target. [ASv6.98](../asv6.98/README.md) appends a compact
recipe example while retaining these tested bytes. Its 18-answer medium screen
completes at 3 bounded accepts/14 rejects/1 uncertain. S006's recipe-retention
and placement checks pass all three trials; original-post failures remain.
