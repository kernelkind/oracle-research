# Autonomous SP iteration

The user authorized autonomous SP iteration on 2026-10-02, with at most
1,000 attempts on `gpt-6.1-sol` at `low` or `medium` reasoning. This is an upper
bound, not a target. Use the subscription `openai-codex` route, without paid
fallback. MP and production adoption remain outside this campaign.

Start from ASv6.58 (candidate, tested with failures). Frozen SP ASv6.48 remains
unchanged. Preserve the existing SP output schema and all instruction/example
coverage. Each candidate needs a version ID and native revision receipt.

## Evidence and evaluation

The six reusable diagnostic cases form three positive/control pairs: purpose
from a list heading versus unrelated co-mention, first use versus newness, and
repair/colour relationships versus distinct objects. Their rubrics are agent
judgments, not user labels. Original regression cases N063, N074, N096 and N100
use native preparation from the saved complete source posts. Both sets are
development evidence, not untouched generalization evidence.

Grade each returned hierarchy for supported meanings, heading-alone parent
relationships, specific source-subject retention and valid placement beneath
every applicable returned parent. Include all occurrences of repeated parents.
Do not infer semantic correctness from output size or text difference. Keep
agent reviews separate from actual user decisions. A rejected answer needs a
concrete source omission or child/parent counterexample.

Whether *derived general headings* also require every valid placement remains
unresolved; track that separately. Do not force controversial memberships
such as vegetable broth under vegetables.

## Execution

All preparation, inference and review use `sse_multivector/experiment.py`.
Saved experiments and receipts live under the ignored
`sse_multivector/experiments/sp-autonomous-v1/`; request history and the native
persistent attempt budget live under ignored `target/sp-autonomous-v1/`.
The attempt budget is never reset or refunded. Only native `run` launches
calls, and each run must name this same budget. Failed/interrupted calls count.
Subscription incremental cash cost is zero; quota consumption is unmeasured.
The monetary ledger was read before launch; no paid commitment is introduced.

Screen revisions on small cases before repeating long outputs. SP remains one
model call per post: no production grading stage or repeated corpus-wide pass
is added. Input work scales with the post and fixed prompt; output work also
includes the existing repeated-branch requirement.

## Results

ASv6.58 (candidate, tested): all four original regression answers at medium
fail confirmed rules. N063 drops culinary scope, N096 drops cooking scope
and sauteing restrictions, N100 drops food purpose, and N074 omits combined
advice beneath its plant-advice component. Short diagnostics pass the bounded
rubric in 5/6 low answers and 6/6 medium answers. Low D006 omits the specific
blue-bicycle repair/red-bicycle observation combination from both component
branches. These are agent reviews saved through native `review`, not user labels.

ASv6.59 (candidate, tested with failures) clarifies the existing heading-only restriction
check and the per-parent placement check. Its seven worked examples and
source-subject contract are unchanged. R20–R23 retain their C1 example mapping;
all other rule mappings remain as recorded in the ASv6.50 maintained audit.
No new normative requirement or decision about derived headings is introduced.
The minimal failing behavioral evidence is the completed ASv6.58 native
regression above, through the production subjects preparation/validation path.

No candidate is adopted. Native budget and all model receipts remain saved.

ASv6.59 medium still has scope failures: edible oils → unrestricted olive
oil (N063), water as a cooking ingredient → one tin of water (N096), and
dog food → tissue and scrap meat merely “for the dog” (N100). A dog's chew
toy provides the last counterexample. Low D006 still misses placements of
its explicitly returned distinct-object combination. The medium D006 answer
preserves the relationship and all relevant source-subject placements.

ASv6.60 (candidate, tested with failures) adds a short explanation inside C1 demonstrating
its already-correct negative parent checks and repeated placements. Its
instructions, example posts and JSON outputs are otherwise identical to
ASv6.59; it introduces no extra post or normative rule.

ASv6.60 medium still fails all four original regression posts: unrestricted
sea salt under Food and drink (N063), the Nostr-diet relationship omitted from
the mother/child exception (N074), salt under Seasonings (N096), and appreciation
under use of a new sealer without newness (N100). Four of six low diagnostics pass the bounded pair targets. The original
D006 acceptance was corrected: it reaches both kinds of parent but omits
four numbered parent copies (1.1.1, 1.2.1, 1.3.1, 1.4.1).
That is not a full SP correctness score.

[ASv6.61 (candidate, tested with failures)](../asv6.61/ASv6.61.md) revises C2 to name a new
app and explicitly place help and appreciation on first use. All source
subjects retain newness and first-use qualifiers under those parents; broad
help/appreciation remain broad. C2 has 21 entries and 12 distinct headings,
compared with 15 entries and nine headings before. Six other cases and all
instruction bytes remain unchanged from ASv6.60. This demonstrates existing
restrictions without adding an example or requiring a new output field.

### Rule coverage for ASv6.61

The 34 clause definitions remain the IDs in the maintained ASv6.50 audit.
Each has one primary example. Existing secondary demonstrations keep their
distinct explanations; C2 adds R20 for newness/first-use restrictions and R22
for repeated qualified subjects. No new rule is introduced.

| Case | Primary clauses | Demonstration |
| --- | --- | --- |
| C1 | R01, R02, R04, R16, R20–R23, R25–R31, R34 | Counted tube, resolved cutting reference, repair-purpose restrictions and every valid branch. |
| C2 | R03, R05, R06, R17 | Hashtag name, figurative help, rhetorical appreciation, unresolved independent name; qualified new-app first use. |
| C3 | R07, R24 | Bare URL and opaque identifier contribute no subjects; empty JSON array. |
| C4 | R08 | Prose establishes profile URL and event identifier without a cross-link. |
| C5 | R09–R12, R19 | Two direct duck interpretations, independent notebook purchase, individual entities retained. |
| C6 | R13, R14, R18, R32, R33 | Count vs lengths, individual cables and pair, negated comparison naming both sides. |
| C7 | R15 | Explicit addition result with both addends and result retained. |

The five implications remain folded into R20 (combinations and no context
repair), R22 (every parent occurrence), R29 (entity vs instance role) and R30
(restrictions inside child headings). Mechanical tests reuse the production
subjects validator and the reviewed positive/negative relationship fixtures;
they independently check each parent occurrence and every displayed edge.
The semantic fixtures are agent judgments, not an independent truth oracle.

ASv6.61 medium improves the N100 appreciation wording, but its recommendation
still drops newness beneath a New Nesco heading. N096 also drops cooking
purpose from chopping beneath a cooking-qualified onion. N074 drops the
Nostr-diet relationship from the mother/child exception, while N063 omits
the expressed whole ingredient-list subject. All four remain rejected.
Low D006 loses the distinct-object observation beneath repaired-blue-bicycle
branches; other five pair targets pass.

[ASv6.62 (candidate, tested with failures)](../asv6.62/ASv6.62.md) extends C1 with the explicit
separate phrase “olive oil for cooking.” Unqualified Olive oil remains outside
Oils for cooking and Cooking; the qualified subject appears in both material
and purpose branches. The original 23 repair entries remain byte-equivalent
as parsed entries; eight new entries add five distinct headings. C2 and the
other five examples remain unchanged. R20/R22/R29 already cover this contrast;
all 34 primary assignments remain present. The source has seven examples.

Eight new transfer cases cover software, music, archive restoration, fitness,
food/lamp oil, microscopes, ambiguity and opaque URLs/numbers/negation. These
are diagnostic fixtures with agent rubrics, not actual user labels. They are
kept out of worked prompts. Any case used to guide a later revision becomes
development evidence. Compare unchanged ASv6.58 medium with ASv6.62 medium
using native preparation, exact same source inputs and the shared budget.

### Numbered-copy correction

The initial ASv6.60 D006 acceptance collapsed repeated headings during review.
The lossless heading/parent-label summary is sufficient to find scope errors,
but cannot prove placement beneath every numbered parent occurrence. The
full numbered audit rejects ASv6.60 D006: four of six parent copies lack the
combination. The original native review is preserved and a correcting rejection
is appended. For D006, ASv6.58 low misses six copies, ASv6.59 low misses six,
ASv6.61 low misses three, and ASv6.62 low misses two. The two completed medium
answers (ASv6.58 and ASv6.59) satisfy all six component copies. Lower missing
counts in one sample are not proof of a causal or reliable improvement.

Before accepting placement coverage, inspect every numbered parent occurrence
for each semantically checked source relationship. A shared parent-label edge
or a correct placement elsewhere is insufficient. The worked-example fixtures
already enforce this; saved model-answer assessments need the same check.

The same numbered-copy audit also corrects ASv6.60 D004: its returned first-use
and liking combination misses four first-use/liking component occurrences
(1.1.1.1, 1.1.1.2, 1.2.1.1, 1.2.1.2). Its earlier acceptance is preserved and
a correcting native rejection appended. ASv6.60 therefore passes four of six
bounded diagnostic targets, not the original six. The targeted copy checks
for D001–D005 in the other completed diagnostic trials found no analogous
omission among the checked qualified repair/drilling, new/old camera and
red-bicycle relationships; these remain bounded checks, not full SP gold.

### Later controlled revisions

| Candidate | Change from preceding version | Original four-post medium result |
| --- | --- | --- |
| ASv6.63 | Generalize without adding a typical-purpose restriction; examples unchanged. | Four confirmed failures. |
| ASv6.64 | Compact JSON layout only; all example values unchanged. | Four confirmed failures. |
| ASv6.65 | Move the two existing hierarchy paragraphs after the examples. | Four confirmed failures. |
| ASv6.66 | Test parent restrictions across any domain, not just this post's domain. | Four confirmed failures. |
| ASv6.67 | Finish relationships before numbering; repeated headings retain all enumerated descendants. | N063/N096 rejected; N074/N100 uncertain on full source specificity. |
| ASv6.68 | Replace C1 with simpler repair and explicit edible/inedible oil qualities, purposes and their source combination. | N074/N096/N100 rejected; N063 uncertain on full coverage. |
| ASv6.69 | Rewrite only the parent-check paragraph to distinguish generic kinds from this post's role-qualified subjects. | Testing. |

ASv6.67 low D004 and D006 satisfy the checked first-use/appreciation and
repair/observation relationships beneath every numbered parent copy in two
independent trials each. This is a bounded diagnostic result, not a full SP
pass or causal comparison. Its medium original regressions still fail or need
further semantic review. ASv6.68 restores the ingredient group beneath the
risotto heading but still produces Seasonings → Salt, Food → Oils and
Dog feeding → material merely “for the dog.” N074 loses the combined advice's
book/author attribution. Native source-bound agent reviews record the witnesses.

ASv6.68/69 keep seven examples and all 34 primary clause assignments above.
C1 now demonstrates a counted tube with generic repair purpose plus separate
edible and inedible olive oils with stated cooking/lamp purposes. The generic
Olive oil heading stays outside both quality and purpose parents. The stated
oil combination appears beneath every copy of both qualified constituents.
C1 has 38 entries and 19 distinct headings; the other six cases are unchanged
from ASv6.67. Its secondary R18 demonstration includes the explicit source
combination. The five existing implications keep the same rule mappings.

The eight transfer answers for each of ASv6.58, ASv6.62 and ASv6.63 are saved.
Their review is incomplete, so they do not establish a generalization score.
Known placement failures include ASv6.58 H001's returned deletion/copying
combination outside all configuration-copying parents, and ASv6.63 H004's
returned physiotherapy/gym sequence outside its constituent branches.
H006's rubric is too narrow about “I liked it”: the preceding lesson is also a
plausible referent, so retaining that interpretation alone is not a failure.
Frozen source inputs and historical reviews are preserved.
