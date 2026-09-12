# GDC09 navigation research

The original GDC09 tree, masks, vectors, labels, and browser remain unchanged.
The objective is a repeatable construction method, not a hand-repaired 100-note tree.

Latest task-trained relation evidence: [SRR01–SRR03](./SENSE-RELATIONS.md).
A WordNet definition-relation classifier preserves Bread → Sourdough but also
produces false Coffee/greeting and human-diet/Dog parents. Explicit definitions
change the errors rather than reliably removing them, adding Music → greetings
and Bread → Coffee. Retaining both names and definitions also fails. Neither a
new hierarchy nor another description rewrite is
adopted. The next research lead is a shared learned hierarchy representation;
the model's scoring and calibration still need inspection before testing.

Earlier contextual-relation evidence: [GDR02](./EXISTING-SUBJECT-RELATIONS.md) and
[GDR03](./SUBJECT-INPUT-RENDERING.md). Existing generated subjects recover greeting
equivalence without GDR01's manual descriptions, but one seed's subject often
does not describe its whole group. A controlled input-format change fixes some
coverage misses and introduces incorrect associated-topic relations, including
Coffee → morning greetings. No automatic classifier, group description or new
hierarchy is adopted. All inputs and scores are preserved. The task-trained
follow-up is recorded above. Earlier [GDR01](./CONTEXTUAL-GROUP-RELATIONS.md) remains the manual-input
control.

Prior group-relation evidence: [lexical broader and equivalent relations](./GROUP-RELATIONS.md).
LGR01 checks all 462 ordered pairs of the 22 frozen MDH02 groups. It proposes
the existing Bread → Sourdough bread link and an animal-sense Carnivore → Dog
link that does not fit the human-diet parent group. It finds no equivalences;
GM resolves to the unit of mass, not the greeting. No new defensible parent
link or browser change results. Full evidence and an offline replay are saved.

Latest learned-membership evidence: [entailment and relevance models](./MODEL-MEMBERSHIP.md).
NLI01/NLI02 show some useful broader-subject recognition but also abbreviation,
negation and greeting-association errors. RER01/RER02 do not fix membership:
for Coffee, the reranker puts `Good morning` above explicit coffee masks.
All inputs and scores are preserved. No classifier, membership rule or new
hierarchy is adopted by these component tests.

Latest parent-construction evidence: [mask descriptions and hierarchy relations](./MASK-DESCRIPTION-HIERARCHY.md).
MDH02 removes the old-tree dependency and finds three immediate relations, but
literal matching confuses word senses and leaves twenty roots. It is not a new
browser candidate. The record also corrects an `I` candidate caused by stripping
a sleep emoji from its source mask.

Latest membership evidence: [explicit masks and missing notes](./LITERAL-MEMBERSHIP.md).
NMR03 finds four notes outside broad Coffee and two outside Bitcoin through
literal subject evidence. It is an audited diagnostic, not an adopted assignment
rule or a new hierarchy. Source snapshots and all proposed masks are preserved.

Latest browser comparison: [mask distinctions and middle-level scoring](./MASK-DISTINCTIONS.md).
ND02-NP01 removes three repeated textual choices from NP01 while preserving all
retained evidence. It is a small inspectable improvement, not a solved hierarchy.

## NMR01 — original-vector membership

**Question:** Can fixed examples from an existing group recover omitted subject
vectors without admitting unrelated meanings?

The six groups are native GDC09 nodes 1614, 1533, 1551, 1325, 1671, and 1598.
Their masks respectively suggest exercise, sleep, cooking times, coffee-shop
music, kitchen equipment, and coffee/tea. These descriptions select diagnostic
destinations; they are not input features or certified labels. In particular,
1598 already contains a dog emoji, an ice-only mask, and a soda-bread mask.
These are preserved, not silently cleaned before the test.

**Hypothesis:** Original-coordinate support from independent notes can recover
the known exercise omission V620 and additional defensible memberships. Any
unrelated admission is counterevidence to the assignment rule's selectivity.
All proposed masks, not just newly reached notes, require semantic inspection.

For each vector, find its highest cosine to an example from each source note.
Exclude examples from its own note. Average those note scores so repeated masks
from one note do not receive repeated votes. For each existing note, take its
best mask's score against the other notes. The smallest of these scores is the
group's provisional acceptance threshold. An outside vector must clear it and
have at least two other source notes available. Examples remain frozen; new
admissions cannot recruit further members.

This threshold is a hypothesis, **not** a calibrated probability or a statistical
guarantee. Two-note groups are especially weak calibration cases: an existing
mask is scored against one other note, whereas an outside mask is scored against
two. The experiment records this asymmetry rather than claiming independent
validation. Additional held-out-note work is needed before adopting the rule.

The runner records all outside scores, per-note witnesses, every proposed
addition, and full original notes/masks for all proposals and the top twelve
outside vectors. Existing non-members are unlabeled, not presumed negatives.

The design borrows separation of discovery and later assignment from
[Dynamic Hybrid Tree Cut](https://academic.oup.com/bioinformatics/article/24/5/719/200751),
and the use of multiple examples from
[HDBSCAN soft clustering](https://hdbscan.readthedocs.io/en/latest/soft_clustering_explanation.html).
The note-balanced score and threshold above are experimental adaptations, not
those papers' published algorithms. No moved diffusion coordinates, titles, or
text embeddings generated from labels enter the calculation.

Run from the repository root with the existing NumPy environment:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/crec100-plscan-venv/bin/python sse_multivector/category_membership.py \
  --data sse_multivector/real-note-fine-segmentation-v1 \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --groups 1614 1533 1551 1325 1671 1598 \
  --output sse_multivector/navigation-research-v1/NMR01
```

The output directory must not exist. A reproduction should choose a new output
directory. Configuration records hash the frozen inputs and source code.

## NMR02 — local agreement instead of a group-wide threshold

NMR01's exercise threshold was 0.5498 and rejected V620 at 0.3898. Its kitchen
threshold was 0.2951 and proposed 88 masks, including dinner ingredients and
the word `chef`. Group-wide average affinity and an internal threshold did not
give a reliable boundary. Coffee/tea also proposed plain sourdough-bread masks.
An audit of all proposed additions is retained separately.

**New hypothesis:** Requiring the two nearest examples from different notes to
both belong to the frozen group will retain local subject support while rejecting
the broad spillover seen in NMR01. The nearest examples are found across the
complete original corpus, excluding every vector from the query's own note.
Membership of a note does not transfer to its other masks: the actual nearest
vector must belong to the group. No new member recruits another during the pass.

This changes assignment only. The groups, masks, vectors, and six destinations
stay frozen. Two is the smallest number requiring independent source-note support;
it is not a tuned cosine cutoff. Unknown examples do not supply group support,
but are not presumed semantically negative. The procedure can still miss a valid
point whose neighbors are themselves missing from the group, or accept a weak
point whose nearest available examples are both misleading. Those outcomes must
be inspected rather than assumed away. In particular, no nearest-neighbor rule
alone establishes an absolute semantic confidence.

Run the command above with `--method local` and output directory `NMR02`.
The original mean scores remain available as diagnostics, but no longer decide
admission. This is not a reproduction of a published classifier; it tests the
specific local-support mechanism revealed by NMR01.

The rejection problem also motivated a follow-up reading of
[Tax's nearest-neighbor data description, Appendix B](https://rduin.nl/papers/thesis_01_tax.pdf).
It compares a query's distance to its nearest example with that example's own
nearest-training-example distance. This gives a local reference scale instead
of a group-wide radius. However, the saved exercise numbers already show why
the default acceptance boundary would be too restrictive here: V620 has cosine
0.4452 to V122, whereas V122 has cosine 0.5498 to its closest other-note anchor.
V620 is farther away. This does not invalidate the published method; it rejects
the assumption that adding its default local-density gate automatically solves
our omissions. No new fitted run or tuned ratio threshold was adopted.

## NP01 — bounded descendant promotion

**Question:** Can navigation skip low-value intermediates without losing access
to notes, changing retained category masks, or creating unwieldy menus?

This experiment uses the unchanged GDC09 categories, not NMR01/NMR02 membership
proposals. For each parent, it considers replacing an internal child with that
child's own children. A count-based gain trades one less step against more
choices: `child_notes * (1 + child_count) - parent_notes * (child_count - 1)`.
It performs the highest positive-gain replacement, breaking ties by saved order,
and repeats. The resulting menu is bounded to eight choices. Existing larger
menus may remain but cannot grow. Eight is a prototype setting, not an empirically
validated cognitive limit. `NP00` removes this bound as a mechanism control.

**Hypothesis:** Promotion shortens the repetitive routes while leaving useful
destinations available and keeping menus readable. Every original leaf must
remain; every retained category must have exactly its original complete notes
and mask ranges. Notes no longer covered by promoted children remain directly
accessible at the retained parent.

Preserving leaves does not prove that removed intermediate destinations were
expendable. The review must check the removed groups and newly adjacent
parent/child pairs, including Coffee, Exercise, Sleep, and Kitchen equipment.
The rule cannot validate category meaning, repair membership, or distinguish
two Coffeechain children with effectively the same meaning. Shorter paths alone
will not establish success.

This is a simple experimental cost proxy inspired by
[BioNav](https://www.cs.ucr.edu/~vagelis/publications/BioNav%20TKDE2009.pdf),
not its published optimizer. BioNav assumes an already-valid semantic hierarchy.
Overlapping memberships here also prevent interpreting raw note counts as
calibrated browsing probabilities.

```sh
python3 sse_multivector/select_note_categories.py \
  sse_multivector/geometric-hierarchy-v1/GDC09/categories.json \
  --output sse_multivector/navigation-research-v1/NP01 --run-id NP01
```

The unbounded control uses `--max-choices 0`, `--run-id NP00`, and its own output
directory. Neither run changes the original browser's default artifact.

## ND02 — repeated masked words

The follow-up [research record](./MASK-DISTINCTIONS.md) contains the rejected
common-word-intersection hypothesis, the stricter tested rule, every removal,
preservation controls, provenance, and inspection commands. It also records a
separate category-utility diagnostic that changes no category or membership.
The follow-up NMR03 tests missing explicit subject evidence elsewhere in the
corpus, not another arbitrary pruning threshold.

## NMR03 — literal subject membership

[The record](./LITERAL-MEMBERSHIP.md) separates seed-union growth from omissions
in existing broad destinations, inspects all additions, and preserves uncertain
scope and literal-matching misses. No browsing membership changed. MDH01/MDH02
now test descriptions independent of the old groups; shared wording yields a
few useful relationships but does not supply semantic parent construction.
