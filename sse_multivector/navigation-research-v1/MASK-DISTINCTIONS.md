# Mask evidence and category distinctions

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

ND02 removes three repeated choices from NP01. It does not solve the hierarchy.
It preserves the original notes, all retained category memberships and masks,
and the baseline browser. No subject, mask, embedding, or title was regenerated.

## Question and literature

A child can contain fewer notes without communicating a narrower subject. The
earlier count-based navigation experiment cannot distinguish those situations.
This investigation holds memberships fixed and examines the actual masked text.

Formal concept analysis distinguishes a collection of objects from the attributes
they all share. A formal concept also requires its collection to contain **all**
objects with those attributes; arbitrary subsets sharing the same attributes are
not separate closed concepts.[^1] GDC09's groups are not formal concepts, however,
and shared words are not complete semantic descriptions. Importing the mathematical
definition does not establish that two GDC09 groups have the same meaning.

Two language-based approaches reinforce the need to examine differences as well
as commonalities. TaxoGen uses within-topic popularity and concentration relative
to sibling topics; it reports that proximity to an embedding cluster's center is
not a reliable substitute for this evidence.[^2] Hierarchical cluster labeling
research uses parent-relative phrase statistics and warns that uneven sibling
groups can require explicit sibling comparisons.[^3] Neither paper proves a rule
for deleting navigation nodes in this corpus.

The experiment therefore uses their distinction between shared and distinguishing
evidence as a hypothesis, not their complete algorithms. No lattice, local
embedding model, trained labeler, or generated category title is introduced.

## First diagnostic: equal common words

Represent each canonical mask by its casefolded words. Keep function words and
numbers; do not stem, expand synonyms, or construct phrases across fragment gaps.
For each saved category, intersect the word sets of all its native mask vectors.

**Hypothesis:** Equal nonempty intersections identify parent–child transitions
without a narrower subject. Empty intersections cause abstention, not rejection.

The baseline has 55 nonempty intersections among 219 categories and 25 matching
parent–child edges. The corresponding NP01 counts are recorded in
`./ND02-NP01/diagnostic.json`. These matches are candidates for
inspection, not accepted deletions.

The hypothesis is too weak. Wine [1493] and both children [1470,1474] all reduce
to `wine`, although their masks contain additional meanings:

- [1470]: V053, N007, `⟦wine was available with the lamb⟧`; other masks select
  `⟦I don’t drink……wine⟧`. V708, N076, selects `⟦wine⟧ ⟦food⟧ ⟦no compromise⟧`.
- [1474]: V536, N063, selects `⟦Mushroom Risotto with Shrimp⟧ ⟦Dry White Wine⟧`;
  the complete note lists recipe ingredients. Other masks from N076 select
  handmade wild rose wine and its accompanying meal.

These do not establish one ideal split. They do establish that an intersection
throws away evidence needed to judge the split. Calling the children redundant
because both intersections equal `wine` would skip that judgment.

A preliminary stopword check makes the loss even clearer. [1008] contains:

- V790, N086: `⟦You’ve had coffee.⟧`
- V859, N095: `⟦Just had⟧ ⟦coffee⟧`

The raw common words are `had, coffee`, unlike parent [1068]'s `coffee`.
Scikit-learn's English stoplist removes `had`, erasing the observed consumption
relationship. That preliminary variant would add a 26th matching edge. It is
not the encoding used by ND02.

Coffeechain is also less uniform than the earlier report suggested. Child [982]
includes V797, N086, `⟦Sipping⟧ ⟦#coffeechain⟧`, alongside V865, N095,
`⟦#coffeechain⟧`. Both complete notes describe drinking coffee. Child [983]'s
two masks contain only Coffeechain, from different surrounding topics. The
distinction is uncertain, but [982] is not a clean removal control.

## ND02: inspect every child's mask, not only their intersection

**Revised hypothesis:** A child whose every mask contains exactly the words
already common to its parent offers no additional textual subject evidence.
Removing that child may remove a redundant destination without losing a useful
narrowing. Any child with extra words is retained, even if those words do not
repeat in every mask.

The rule is generic and contains no note IDs, category IDs, preferred words, or
topic-specific exceptions. It traverses the saved category tree. Eligible children
are removed, their children are offered under the retained parent, and notes not
covered by remaining children become direct notes of that parent. Every retained
category keeps exactly its original complete membership and mask ranges.

The rule does **not** require preserving all original leaves: a leaf can itself
be a duplicate destination. This is a separate hypothesis from NP01's
leaf-preserving count experiment. The baseline and NP01 are both preserved.

| Input → output | Categories | Maximum depth | Notes at root |
| --- | ---: | ---: | ---: |
| GDC09 → ND02-baseline | 219 → 207 | 40 → 40 | 100 → 100 |
| NP01 → ND02-NP01 | 113 → 110 | 8 → 8 | 100 → 100 |

All twelve baseline removals were inspected against their full masks and original
notes by the main agent and an independent, clean-context agent. None demonstrated
a clear shared narrower subject. This is a limited semantic judgment, not a
general proof of safety.

| Retained parent → removed node | Complete child word evidence | Judgment |
| --- | --- | --- |
| 1016 → 966 | Every mask says `coffee` | No narrower coffee subject demonstrated. |
| 1003 → 956 | Every mask says `coffee` | More-coffee and coffee-availability contexts differ; no shared narrower subject. |
| 1035 → 983 | Every mask says `coffeechain` | Source notes have different surrounding topics. |
| 1077 → 1006 | Every mask's words say `GM` | Plain greeting and greeting with affectionate emoji; warmth is not shared by both. |
| 1043 → 1032 | Every mask says `grownostr` | No narrower subject demonstrated. |
| 1043 → 1004 | Every mask says `grownostr` | Same result after its former parent is removed. |
| 1133 → 1101 | Every mask says `grownostr` | No narrower subject demonstrated. |
| 1180 → 1100 | Every mask says `plebchain` | Parent additionally has Nostr/Plebchain text; child supplies no narrowing. |
| 1284 → 988 | Every mask says `bitcoin` | Parent also contains workshop and island-life evidence. |
| 1284 → 970 | Every mask says `bitcoin` | No shared narrower Bitcoin subject. |
| 1284 → 949 | Every mask says `bitcoin` | Same result after ancestor removal. |
| 1284 → 961 | Every mask says `bitcoin` | Shared hashtag-list format is not a narrower Bitcoin subject. |

The source texts, ranges, aliases, and complete notes for these comparisons are
in each run's `review.json`; `descriptions.json` maps each node to its canonical
rows and every word set. `selection.json` records each actual transition,
including temporarily promoted descendants. In these two outputs, **no new
retained parent–child edge survives**: those temporary descendants are also
removed. The baseline loses nine old leaves and three intermediates. NP01 loses
three leaves, and [1016] becomes a leaf itself.

For NP01 specifically, the removed nodes are [966,956,983]. Coffee [1016] now
offers its five notes without two further Coffee choices. Coffeechain [1035]
retains [982], including the `Sipping` evidence. Wine children, drinking coffee,
coffee-shop music, coffee flavor, sleep, exercise, and equipment remain. Empty
word intersections in some of these groups mean the rule abstained; they do not
validate those groups or establish their incoherence.

## Limits and complete paths

ND02-NP01 still has this route:

`All [1753,100] → [1745,99] → [1701,98] → [1652,86] → Coffee/tea [1598,22] → Coffee [1016,5]`

The final repeated choices are gone. The near-identical upper steps are not.
The Coffeechain [1035,7] → [982,2] transition also remains; no cosmetic renaming
was used to claim a distinction. Existing titles are copied solely to use the
existing browser, not accepted as ground truth.

Word order, punctuation, symbols, and context outside masks are absent from the
feature sets. These can affect meaning. In particular, the GM example contains
emoji discarded by the feature representation. An absence of **extra words** is
not a universal absence of **extra meaning**. Thus this rule is an inspectable
conservative experiment, not an adopted semantic-equivalence component.

It also changes no membership. A coffee note elsewhere in the tree does not
become reachable under [1016] through this operation. Removing duplicate choices
and recovering missing relevant content remain different tasks.

## A separate middle-level scoring diagnostic

Basic-level concept research studies category utility,
`P(c) × Σ_y [P(y|c)² − P(y)²]`, as one possible measure of an informative
category.[^4] This can reward useful intermediate concepts without protecting
particular node IDs. It is not a browsing-quality guarantee.

The diagnostic applies the formula to all 219 categories with 1,308 binary
masked-word attributes. It gives each note equal total mass, distributed uniformly
over that note's canonical masks. This is an explicit modeling choice, not an
estimate of user interests. No cutoff or hierarchy selection was run.

| Group | Score |
| --- | ---: |
| Chocolate/tea consumption [1432,2 notes] | 0.128252 |
| That group plus chicken-stock quantity [1524,3 notes] | 0.120163 |
| Broad coffee [1539,19 notes] | 0.071883 |
| Coffee/tea [1598,22 notes] | 0.067556 |
| Equipment [1671,5 notes] | 0.043955 |
| Exercise [1614,2 notes] | 0.015929 |
| Bare coffee [1016,5 notes] | 0.010315 |
| Sleep [1533,2 notes] | 0.007643 |
| Root [1753,100 notes] | 0 |

The complete ranking, probabilities, source hashes and code dependencies are in
`./category-utility-diagnostic.json`.

The broad-coffee result is encouraging but insufficient. Every new word found
in only one mask inside a category **increases** this score. If that mask has
weight `w` and the category has mass `m < 1`, the increase is
`w² × (1/m − m) > 0`. Repeatedly adding different one-off words can therefore
increase the score without adding any evidence shared by different notes. A
production-code arithmetic test verifies this effect. The diagnostic did not
alter the real notes or masks.

This is a problem with treating this particular word-based score as shared
semantic quality, not a refutation of category utility with well-chosen
attributes. The actual top group is plausibly coherent overeating/overdrinking;
its high score is not itself a failure. The mechanism prevents interpreting
that rank as proof or simply selecting high-scoring groups.

## Membership follow-up

[NMR03](./LITERAL-MEMBERSHIP.md) tests the separate consequence of explicit
evidence: masks elsewhere can identify the same subject despite being outside
the original destination. It recovers concrete Coffee and Bitcoin omissions,
but literal matching has unresolved scope, word-sense and coverage limits.
Neither its results nor ND02 establish a general semantic rule. No score cutoff
or membership change was adopted. The next investigation concerns meaningful
descriptions independent of old ancestry, with memberships separately auditable.

## Reproduction and inspection

From the repository root, using a new output directory:

```sh
PYTHONPATH="$PWD/sse_multivector" python3 \
  sse_multivector/navigation-research-v1/ND02-NP01/runner.py \
  sse_multivector/navigation-research-v1/NP01/categories.json \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --output /tmp/nd02-reproduction --run-id ND02-NP01
```

The snapshot is not standalone: it imports `select_note_categories.py`. Its
required hash and committed version are in `./ND02-provenance.json`.
The independent audit reproduced all six artifacts byte-for-byte for both runs
through the actual CLI entry point, and exhaustively checked native note/mask
compatibility with each projection. That compatibility is verified for these
inputs; the selector does not independently validate it from node IDs alone.

```sh
python3 sse_multivector/category_utility.py \
  sse_multivector/geometric-hierarchy-v1/GDC09/categories.json \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --output /tmp/category-utility-reproduction.json
```

Inspect the combined candidate in the unchanged tool:

```sh
target/infomap-review-build/debug/sse-subject-navigation \
  --categories sse_multivector/navigation-research-v1/ND02-NP01/categories.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json
```

Both candidate exports pass `--check`. The usual diffusion launcher still opens
GDC09. The research goal remains incomplete.

## Sources

[^1]: Buzmakov, Kuznetsov and Napoli, 2014, [Concept Stability as a Tool for Pattern Selection](https://ceur-ws.org/Vol-1257/paper6.pdf), §2.1. For a corpus-based hierarchy application with parsed dependency attributes rather than these literal words: Cimiano, Hotho and Staab, 2005, [Learning Concept Hierarchies from Text Corpora using Formal Concept Analysis](https://arxiv.org/pdf/1109.2140), §§2–3. Neither paper validates this experiment's word features.
[^2]: Zhang et al., 2018, [TaxoGen: Unsupervised Topic Taxonomy Construction by Adaptive Term Embedding and Clustering](https://hanj.cs.illinois.edu/pdf/kdd18_czhang.pdf), §4.2.2.
[^3]: Treeratpituk and Callan, 2006, [Automatically Labeling Hierarchical Clusters](https://www.cs.cmu.edu/~callan/Papers/dgo06-puck.pdf), §§4.3 and 5.3.1.
[^4]: Belohlavek and Trnecka, 2013, [Basic Level in Formal Concept Analysis: Interesting Concepts and Psychological Ramifications](https://www.ijcai.org/Proceedings/13/Papers/186.pdf), §3, category utility approach.
