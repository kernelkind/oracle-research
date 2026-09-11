# Membership and navigation selection

These are separate experiments on the unchanged GDC09 corpus. Neither membership
rule is adopted. NP01 is an inspectable navigation comparison, not a validated
replacement. The original GDC09 browser remains the default.

The follow-up [mask-distinction experiment](./MASK-DISTINCTIONS.md) removes three
repeated choices from NP01. It preserves all retained evidence but leaves the
upper-level paths and membership problems unresolved. ND02-NP01 is the latest
inspectable comparison, not an adopted replacement.

## Membership

NMR01 uses a note-balanced average of nearest examples and an internal group
threshold. NMR02 requires the two closest examples from different notes to both
belong to the destination. Both keep their examples fixed. The exact definitions,
limitations, and commands are in [README.md](./README.md).

| Destination | NMR01 proposed masks | NMR02 proposed masks |
| --- | ---: | ---: |
| Exercise [1614] | 0 | 1 |
| Sleep [1533] | 1 | 1 |
| Cooking times [1551] | 0 | 0 |
| Coffee-shop music [1325] | 0 | 0 |
| Kitchen equipment [1671] | 88 | 0 |
| Coffee/tea [1598] | 20 | 4 |

### Exercise: local support recovers one real omission

V620 from N069 selects `⟦Work out in zone 2 as much as you can.⟧`.
Its two closest examples from other notes are:

- V122, N017: `⟦crushed⟧ ⟦solid⟧ ⟦gym⟧ ⟦this morning⟧`, cosine 0.445173.
- V174, N024: `⟦Red flags⟧ ⟦Workout plans shorter than 1,000 days⟧`, cosine 0.334416.

Both examples are in [1614]. NMR01 rejects V620 because their average, 0.3898,
falls below the group's internal threshold, 0.5498. NMR02 admits it because
both nearest independent-note examples support the destination.

This shows that final membership need not inherit the missing vector's original
branch. It does not validate NMR02 generally or change the tree yet.

### Kitchen equipment: broad affinity is not a membership boundary

NMR01's threshold falls to 0.2951 for the varied five-note equipment group.
Its 88 proposals include 42 judged valid, 27 invalid, and 19 uncertain under
the subject supported by the anchors. These are semantic judgments, not an
independent benchmark. The complete per-mask audit is in
[kitchen-audit.json](./NMR01/kitchen-audit.json).

Valid examples include pressure canning, using a smoker, packing a lunch box,
and using a plate rather than a bowl. These need not mention the original brands
or repeat the same claims. Clear spillovers include a mask selecting only
`⟦brisket⟧`, dinner ingredients, and `⟦chef⟧`.

Of 25 newly proposed notes, 12 have at least one valid mask, five only uncertain
masks, and eight only invalid masks. An invalid mask on an otherwise relevant
note is not the same error as admitting an irrelevant note. In particular, audit
row 770 contains valid crockpot evidence plus unrelated chicken-housing text:
that is an overscoped supporting mask, not evidence that N092 is an invalid note.

NMR02 avoids all these additions, including the valid ones. Fewer admissions
alone therefore do not establish improvement.

### Coffee/tea: a shared local meaning can be wrong for the destination

NMR01's 20 additions were judged seven valid, twelve invalid, and one uncertain.
For example, matcha in a pie is a valid tea use; plain sourdough preparation is
not coffee/tea. Masks elsewhere in a source note do not supply the missing
subject for an unrelated added highlight.

NMR02 adds four masks:

- V750: gin, beer, and chocolate gifts — invalid for this destination, although
  the source note already belongs through a different tea mask.
- V765: craft chocolate — invalid for coffee/tea.
- V412: `⟦Rise⟧ ⟦grind⟧` — uncertain mask specificity; the complete original
  sentence supplies coffee beans.
- V020: a Sorrento food tour — invalid for this coffee/tea destination.

V020's two witnesses concern enjoying decaf coffee for its flavor and roasting
coffee for a personal taste profile. Their cosines are 0.6763 and 0.6210.
The shared food/flavor experience is legitimate; this is not proof of an SSE
failure or a meaningless similarity. But it does not make a food tour a
refinement of coffee/tea. Local agreement can select a different commonality
from the destination's intended subject.

The explicit hot-coffee mask V494 remains missed: its closest examples are
coffee V503 and the greeting V647. Hence local agreement also rejects a valid
coffee addition. Its original geometry contains competing meanings, not no
coffee signal.

### Membership holdouts expose a recall limit

Every mask from the queried note is excluded from its supporting examples.
For groups with at least three notes, NMR02 recovers some original membership
for 20/22 coffee/tea notes, 2/5 equipment notes, and 2/3 cooking-time notes.
The misses are recorded in [whole-note-holdouts.json](./NMR02/whole-note-holdouts.json).

This measures recovery of existing assignments, not semantic correctness of
every original assignment. Discovery already used the full corpus. Two-note
groups cannot supply two independent examples after holding out one note, so
their zero recoveries are an unavailable calibration case, not model failures.

The numerical review and semantic audit include every proposed mask. Full notes,
exact fragments, byte ranges, and vector IDs remain in each run's `review.json`;
all outside scores and supporting examples remain in `results.json`. The
[main semantic audit](./semantic-audit.json) covers the remaining groups and all
six NMR02 proposals. Uncertain sleep/fatigue cases are not silently counted as
successes or failures.

## Navigation selection

NP00 and NP01 keep the baseline memberships fixed; they do not include either
membership experiment. They promote descendants using the same count-based
cost proxy. NP01 bounds new menus to eight choices; NP00 is unbounded.

| View | Categories | Maximum depth | Root choices |
| --- | ---: | ---: | ---: |
| Original GDC09 | 219 | 40 | 3 |
| Existing single-child absorption | 148 | 28 | 3 |
| NP00 | 109 | 4 | 41 |
| NP01 | 113 | 8 | 3 |

NP01's largest menu still has 15 entries because a pre-existing larger menu is
not forced smaller. Every retained category has exactly its original recursive
notes and mask ranges. All 87 original leaves and all 100 notes remain reachable.
Both exports pass the existing browser's validation.

The coffee/tea path [1598] changes from 16 selections to four:

`All notes [1753,100] → [1745,99] → [1701,98] → [1652,86] → Coffee/tea [1598,22]`

Exercise needs four instead of seven selections; Sleep needs five instead of
eleven; Kitchen equipment needs three instead of four. These are structural
measurements, not browsing-time estimates.

Three important problems remain:

- The near-identical 100→99→98 steps remain. The menu bound prevents flattening
  their many descendants in one operation.
- The 19-note Coffee [1539] and five-note reading/writing group [1700] disappear.
  Coffee/tea [1598,22], a smaller Coffee [1016,5], and Knowledge/reading [1693,4]
  remain. Losing a particular node is not automatically a semantic regression:
  the unresolved question is whether those remaining destinations offer equally
  useful access. Retaining every old node is not a requirement.
- In NP01, Coffeechain [1035] offers [982] and [983]. Their masks mostly select
  the same Coffeechain text; no useful subject distinction is demonstrated.
  An earlier version of this report incorrectly used [1050] and [1015] from
  the baseline/single-child view. Those nodes are absent in NP01.

NP00's 41 root choices show the tradeoff the menu bound addresses. Forty-one is
not automatically invalid, but a shorter path does not establish a better menu,
especially when several choices overlap or are themselves weak groups.

No title was changed to make a result appear coherent. For example, the promoted
node [1749] retains its existing label, but its masks select only `alby` and
`#DCA`; those masks must be evaluated rather than trusting the title. Promotion
can expose a weak group sooner without improving its meaning.

## What the evidence establishes

Independent assignment can recover a concrete omitted meaning without changing
the discovered tree. Independent navigation selection can remove many steps
without changing the evidence in retained destinations. These are useful
mechanisms, not a solution to the complete hierarchy problem.

The unresolved issue linking them is semantic scope: which common meaning
defines a destination, which differences justify keeping its children, and
which nearby meanings truly refine it? Neither internal cosine thresholds nor
note-count pruning answers that. More arbitrary threshold or menu-size tuning
would not isolate this problem.

That investigation now has a limited result: shared-word intersections alone
discard distinctions, while checking every child's mask permits a few defensible
removals. Coffeechain [982] contains `Sipping` evidence and is retained; [983]
contains only the general tag and is removed. This corrects the earlier premise
that both children were clean removal controls. See the follow-up record for
the full audit and why general semantic selection remains unvalidated.

## Inspect NP01

From the repository root:

```sh
target/infomap-review-build/debug/sse-subject-navigation \
  --categories sse_multivector/navigation-research-v1/NP01/categories.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json
```

This opens the existing category-and-original-note tool, with all applicable
masks overlaid together. Use `--check` for noninteractive validation. The normal
`sse_multivector/run-diffusion-categories.sh` still opens the preserved baseline.
NP01 is packaged for comparison, not recommended as a solved navigation system.
