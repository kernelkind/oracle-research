# TCC04 — transfer of one frozen membership cutoff

## Missing capability

TCC03 supplies useful complete-note score ordering but an unsuitable native
0.5 cutoff. The [decision-method review](./CATEGORY-DECISION-METHODS.md) found
that a simple shared cutoff offers useful imperfect development tradeoffs;
a calibration subsystem is not yet necessary. Test whether that same decision
works on different notes and categories before adding another component.

The candidate cutoff is **0.9969531560953688**. It was frozen in commit
`9c8577f69293d74ea5b1aae1bf93d7fe617e5639`, before selecting these inputs.
It is the midpoint of the minimum equal-cost FN+FP interval on the 34 judged
TCC03 development pairs. It is not retuned here, and 0.5 remains the control.

## Inputs and unchanged implementation

Use 12 complete notes outside both TCC01 and TCC02/TCC03:
N006, N010, N011, N020, N023, N026, N046, N047, N063, N075, N091 and N096.
They supply 145 saved CAP04 descriptions and 143 canonical masks, with 3–29
descriptions per note. Copy every source record exactly, in CAP04 row order.
No manual subject or mask repair, deduplication, new extraction or note editing.

The three category strings are existing CAP02 single-feature candidates:

| String passed to the model | CAP02 candidate |
| --- | --- |
| `bread` | D82879f64c8d0 |
| `chicken` | Dfb7949c5d5e2 |
| `salt` | Df2f3d5e8a775 |

None was used to fit the cutoff. Bread and Chicken were considered in earlier
model diagnostics, so these are categories held out from cutoff fitting, not
categories never previously examined by the research. These original notes
also belong to a previously studied corpus. This is a deliberately selected
challenge set, not a random holdout or general corpus-accuracy estimate.

The set includes explicit bread, bagels, a bread recipe request, bread baking,
a sandwich, chicken takeout, chicken pizza, chicken stock, preserved chicken
eggs, salt toppings and ingredients, and other food meanings. Nearby nonmembers
include rice/pasta, dairy, vegetables and other meats. Raw-milk slush supplies
a short all-category negative. Broad and compound subjects both remain available.

Use the unchanged pinned native GLiClass runner with `--conditions single`.
Each request contains only one saved subject description and one category.
Neither the original note nor the other descriptions are model input.
For each note/category, take the maximum over every available description and
retain all attaining rows. Apply both fixed cutoffs to this same score matrix.
No joint competing labels, model switch, examples or alternate wording.

## Source judgments before scores

The main and independent reviewers read all 12 originals and all 145 saved
subject/mask records before scoring. `TCC04/judgments.json` preserves the
full-note judgments and source witnesses, not user approvals.

| Note | Bread | Chicken | Salt |
| --- | --- | --- | --- |
| N006 | unsupported | unsupported | unsupported |
| N010 | unsupported | supported | unsupported |
| N011 | supported | unsupported | unsupported |
| N020 | unresolved | supported | unsupported |
| N023 | supported | unresolved | unsupported |
| N026 | unsupported | supported | unsupported |
| N046 | supported | unsupported | supported |
| N047 | supported | unsupported | unsupported |
| N063 | unsupported | unsupported | supported |
| N075 | supported | unsupported | unsupported |
| N091 | unsupported | supported | supported |
| N096 | unsupported | unsupported | supported |

N020's pizza/Bread boundary and N023's eggs of unstated species/Chicken
boundary remain unresolved. N091 explicitly names chicken eggs; that source
supports a Chicken refinement without requiring every egg to be treated as
chicken. Bagels count as Bread without requiring the literal word “bread.”
Unmentioned ingredients do not become note subjects merely because a dish
usually contains them. In particular, bread, chicken stock, sushi, cheese and
other foods do not automatically supply a Salt subject.

N011 is truncated in its source, but the intact passage explicitly supports
its bread topic and recipe request. No missing suffix, linked media or URL
slug is used to supply an additional decisive subject. Existing interpretation
issues remain recorded rather than repaired for this test.

## Hypothesis, competing explanations and decisions

Hypothesis: the frozen cutoff reduces the total number of incorrect judged
note/category decisions relative to 0.5. Compute TP, FN, FP and TN separately
for every category as well as pooled; leave the two unresolved pairs outside
those counts. Both conditions contain the same 13 supported and 21 unsupported
pairs, not 34 independent notes.

A lower total error is not sufficient if it empties a supported category or
rejects most of that category's supported notes. More than half of its supported
notes missed triggers this retrieval safeguard. This is a diagnostic safeguard,
not a universally correct product threshold. Report every miss and incorrect
admission, and judge their practical meaning from the full source.

Audit every attaining mask in both conditions. Correct note admission is not
proof that the winning description or mask supplies the right subject. Preserve
that distinction without imposing perfect mask accuracy as a requirement.
Also inspect lower-scoring genuine witnesses for each missed note. Do not
manually substitute them into the algorithm's output.

Competing explanations and the observations separating them:

- A reusable score cutoff exists: incorrect additions fall and useful retrieval
  survives across these new category/note pairs. This supports a bounded
  construction-facing test using the same rule, not broad deployment.
- Category score levels differ: the frozen rule misses valid notes whose
  complete-note maxima are nevertheless well ordered above nonmembers.
  This supports investigating label-relative decisions.
- Semantic ordering fails: unsupported notes outrank supported notes under
  the same complete-note maximum. A per-category scalar threshold cannot
  repair those pairs. Do not infer this from individual-witness inversions alone.
- Input evidence or scope is defective: the original, mask and description
  do not justify the presumed membership. Keep this separate from scorer and
  cutoff errors; do not relabel a difficult case to improve the result.

Would either outcome change the next decision? Yes. Useful transfer moves
the research back toward automatically proposed categories and meaningful
refinements. Failure directs attention to score levels, ordering or grounding
before adding machinery. Changing notes and categories together tests combined
transfer; it does not causally isolate which change explains a failure.

## Boundaries and execution

This does not generate a hierarchy, prove semantic parenthood from note-set
inclusion, validate all category scopes, or prescribe one correct taxonomy.
Category generation and parent relations remain separate open dependencies.

Run one local CPU process, two Torch threads, 435 primary scores, using the
existing offline model/source/runtime. Preserve inputs and judgment hashes
before inference, all scores and token inputs, per-note maxima, every error,
native loading checks, resource use and an exact offline replay. No production
code change is required. GDC09, earlier experiments and the browser remain
unchanged; no review-tool packaging before wrap-up.

The actual model/task-fit audit is in [TCC01](./NATIVE-CATEGORY-MEMBERSHIP.md).
The threshold literature and its supervision/transfer limitations are in
[the decision-method review](./CATEGORY-DECISION-METHODS.md). No new training
objective or learned-model transfer is introduced here.
