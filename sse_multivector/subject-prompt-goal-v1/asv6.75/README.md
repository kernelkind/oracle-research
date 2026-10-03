# ASv6.75 food-role example draft

Status: draft, untested. On 2026-10-02 the user approved drafting and auditing
the existing-example revision recommended by the completed
[ASv6.74 scope minimization](../autonomous-sp-v1/scope-minimization-v1.md).
Approval of this exact draft and model testing remain open. Production SP
remains frozen ASv6.48; MP and adoption are outside this task.

[ASv6.75](ASv6.75.md) replaces only C1's post, explanation and complete output.
Instructions, C2–C7 and the JSON schema remain byte-for-byte unchanged from
ASv6.74. This demonstrates existing scope and placement rules without adding
another rule, example, component or model pass. Native `experiment.py revise`
assembled the source and ordinary POST template from the approved ASv6.74
files; both have exact-edit definitions and revision receipts. Full-context
deltas remain in the ignored `target/sp-autonomous-v1/as75-source.diff` and
`as75-template.diff` artifacts.

## Source meanings and heading scope

The post expresses food-seasoning salt, a counted pair of food ingredients for
the dog, their mixing with resolved references, and a separate tissue-for-dog
subject. The two ingredient quantities belong to their respective materials:
one piece of connective tissue and two meat scraps. No total is calculated.
The complete mixing subject states both quantities, ingredient role and dog
recipient. Salt, connective tissue, meat scraps and dogs remain as individual
subjects alongside the action. Mixing the pair concerns both participants; it
does not replace either participant or the expressed pair.

Every displayed relationship was reviewed using heading meanings alone.
These are subject-index relationships: mixing explicit food ingredients for
the dog concerns the ingredients, Dog food, Food and Dogs. Qualifying the
material's role preserves its meaning beneath the food parents. The separate
recipient clause supports connective tissue for the dog without establishing
an ingredient relationship for that separate material. Its heading is general
enough to include the counted ingredient subject from the other clause; each
copy receives that subject because its wording fits, regardless of the source
instance described in the parent's context.

| Heading | Placement and reason |
| --- | --- |
| Salt | Root 1; de-icing salt also fits, so food context cannot place this unrestricted heading beneath Food or Food seasoning. |
| Salt for food seasoning | Beneath Salt at 1.1 and Food seasoning at 5.1.1; the source heading supplies the supported purpose, and the child states it. |
| Connective tissue | Root 2; tissue can be used in nonfood material. |
| Connective tissue for the dog | 2.1 and 4.2 beneath tissue and Dogs; training-scent material also fits, so a recipient alone does not establish a food role. |
| Meat scraps | Root 3; scraps can have a nonfood use, including a training scent. |
| Counted food-ingredient subjects | Explicit ingredient role and recipient allow both beneath Dog food and Food, while their counts stay in their own headings. |
| Mixing | Root 6; mixing can involve nonfood materials. The qualified action below it preserves ingredient role and recipient. |

No child imports a food restriction from its parent, context or a placement
elsewhere. No feeding action, relationship between the separate material and
the ingredients, or mixing of salt with the dog-food ingredients is added.
During the manual audit, the initially authored food-ingredient headings were
made explicit about "for the dog": dog-food ingredient type alone would not
retain the same recipient restriction as the tissue-for-dog parent. This was
corrected before review or inference.

## Complete numbered placements

The source-subject placements below are mechanically checked after production
subjects validation. Descendants count; a direct duplicate beside the same
containing branch is unnecessary. Each ingredient subject and full group/action
appears beneath both Dog food occurrences, 4.1 and 5.2, through their ingredient
branches. The unrestricted recipient subject stays outside both.

| Source subject | All numbered occurrences |
| --- | --- |
| Salt for food seasoning | 1.1, 5.1.1 |
| Connective tissue for the dog | 2.1, 4.2 |
| One piece of connective tissue as a food ingredient for the dog | 2.1.1, 4.1.1.1, 4.2.1, 5.2.1.1 |
| Two meat scraps as food ingredients for the dog | 3.1, 4.1.1.2, 5.2.1.2 |
| Complete two-material ingredient group | 2.1.1.1, 3.1.1, 4.1.1.1.1, 4.1.1.2.1, 4.2.1.1, 5.2.1.1.1, 5.2.1.2.1 |
| Complete counted mixing action | 2.1.1.1.1, 3.1.1.1, 4.1.1.1.1.1, 4.1.1.2.1.1, 4.1.1.3.1, 4.2.1.1.1, 5.2.1.1.1.1, 5.2.1.2.1.1, 5.2.1.3.1, 6.1.1 |

The group fills all four tissue-ingredient and all three meat-ingredient
copies. The complete action fills all seven group copies and all three
qualified mixing copies. Tests inspect every compatible numbered ancestor,
not only distinct heading pairs. They also check every displayed edge,
excluded scope/group relationships, participants, field order and unchanged
instructions/examples/template. Derived broader-heading closure remains the
same unresolved evaluation boundary; this audit checks source subjects beneath
the returned compatible headings.

## Existing instruction coverage

The [34-clause primary map](../autonomous-sp-v1/README.md#rule-coverage-for-asv661)
retains every assignment. C1's sixteen primary clauses are demonstrated here:

| Clauses | Demonstration |
| --- | --- |
| R01, R02, R04 | Interpret the headings/list/action together; resolve it to the tissue piece and them to two meat scraps, retaining supported role and recipient. |
| R16 | Counted ingredients, their expressed group and the complete action are retained under broader headings; the JSON does not expose internal reasoning order. |
| R20, R29 | Generic materials and recipient-only tissue stay outside food parents despite their source context; food-qualified children carry their own role. |
| R21, R22 | Shared ingredient and action headings collect every compatible source subject beneath each numbered copy, including both Dog food branches. |
| R23, R25, R26 | Each entry has its own section number, broad-to-specific with parents first, and fields ordered number/context/subject. |
| R27, R28 | Context identifies source support and can describe a food-use instance without restricting its general material heading. |
| R30, R31, R34 | Standalone headings resolve references, preserve counts/roles/recipient and remain concise; a general material heading need not retell its instance's use. |

C1 retains secondary demonstrations of R18 (individual subjects and group),
R19 (participants alongside action) and R24 (nonempty JSON). It adds a secondary
R10 demonstration: the separate recipient clause does not create a food-role
relationship. C2–C7 retain the other eighteen primary clauses and their prior
secondary demonstrations. The five tracked implications remain folded into
R20, R22, R29 and R30. No clause or implication is dropped or newly invented.

C2's help/appreciation combination remains an open semantic question, as does
N063's complete-dish versus separate ingredient-group representation. Their
answers are not decided by this C1 revision. The semantic fixtures and this
audit are agent judgments, not independent gold labels or proof that all seven
examples are correct.

## Verification, scale and next step

The minimal test first failed against ASv6.74 because C1 had no Food heading.
The replacement passes; a retained test checks that historical failure. All
47 example/attempt-budget tests and nine native revision tests pass. The tests
use the production subjects adapter; no production API or runner change was
introduced. Passing these offline checks establishes the declared example
structure, not model behavior or cross-topic generalization.

C1 has 42 entries and sixteen distinct headings, versus ASv6.74's 35 and
fourteen. The complete source grows from 21,533 to 23,662 UTF-8 bytes: 2,129
additional fixed input bytes per post, or 9.9%. Across K posts this adds
2,129 × K input bytes; the required hierarchy copies remain part of the
existing contract. Generated output size and token usage are unmeasured.
There is no additional per-post pass. Source SHA-256 is
`4a673d7d6c87dc568bcf6043e46bb05c01ca873eacc9c87c4797f12231dc8c70`.
No model calls were made: the persistent campaign budget remains 356 of
1,000 attempts.

After review, the useful next step is a fixed comparison with ASv6.74 on all
sixteen minimized cases and the original four regression posts, retaining
parent exposure, scope, source coverage, every numbered placement and
uncertainty separately. Include the earlier repair diagnostics to check the
effect of replacing their closely related example. Freeze criteria and the
whole draft before generation; do not select trials by their quality. This is
a recommendation, not an approved or started model experiment.
