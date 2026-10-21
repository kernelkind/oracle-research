# Existing subjects for group relations

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

GDR02 removes GDR01's hand-written descriptions. Existing generated subjects
recover the greeting equivalence, but also produce incorrect category relations
and reject obvious members. They are useful context, not a validated automatic
group-description or parent-construction method.

## What was tested

All 22 MDH02 groups remain unchanged. They contain 246 distinct canonical masks
from 53 notes. Each original seed supplies its exact mask text and every existing
generated subject attached to it. There are 29 distinct mask-text candidates and
30 subject candidates. Nothing was regenerated or manually rewritten.

For each candidate, the model checks every member's generated subject for
coverage. Separately, it scores every ordered pair of candidates from different
groups. All alternatives remain visible; the experiment does not choose whichever
description gives the desired answer. The 2,409 scores comprise 771 coverage
checks and 1,638 candidate relations.

The fixed classifier is `MoritzLaurer/deberta-v3-base-zeroshot-v2.0`, revision
`8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8`. Both sides use
`This text is about {text}.` A score above 0.5 flags a pair for inspection; it
is not a calibrated probability or an adopted acceptance threshold.

The [pre-run plan](./GDR02-PLAN.md), all inputs and scores (`./GDR02/scores.json`),
candidate provenance (`./GDR02/candidates.json`), complete source notes and masks (`./GDR02/groups.json`)
and coverage summaries (`./GDR02/summary.json`) are preserved.

## Useful signal

| Proposed child → parent | Mask text | Existing subject |
|---|---:|---:|
| GM → Good morning | 0.0035 | 0.9168 |
| Good morning → GM | 0.0073 | 0.9801 |
| Sourdough bread → Bread | 0.9957 | 0.9689 |
| Brisket → Beef | 0.9037 | 0.9359 |

The greeting masks actually greet people; both directions indicate equivalent
subjects, not a reason to put one greeting category beneath the other. The seed
subject `A good-morning greeting.` covers all six GM masks. The raw `GM` candidate
covers none when compared with those same member subjects.

Brisket is a plausible additional food refinement under Beef, given the two
notes about smoking brisket. It is not an implemented parent edge. In particular,
the selected Beef seed subject is narrower than the complete Beef group.

## Different causes of failure

### A seed can describe less than its group

The Beef seed's generated subject is `Beef as part of a meal.` The group also
contains N100's beef-fat preparation for tallow and scraps reserved for a dog:

- V925: ⟦fat for making tallow⟧ ⟦beef⟧
- V928: ⟦connective tissue and scrap meat for the dog⟧ ⟦Saved the excess myoglobin⟧ ⟦beef⟧

These are reasonable Beef members, but the meal description does not fully
describe them. Only 11 of 21 canonical masks pass that candidate, although each
of the four notes has at least one passing mask. Note-level coverage alone would
hide the scope mismatch. Rejecting all such masks would also be the wrong repair.

### The classifier can confuse association with narrowing

It scores Beef → Carnivore diet at 0.6942 and the reverse at 0.8285. Those are
not equivalent categories. N096's Beef masks describe spaghetti Bolognaise with
vegetables and pasta. N074's Carnivore masks discuss controversy and criticism:

> The #nostr diet is boring. It doesn’t generate clicks like the #plantbased diet. It doesn’t stir controversy like the #carnivore diet…
>
> Unless, of course, you’re 10 and your mom tells you to eat your veggies.
>
> Tired of the bitcoin carnivore narrative.
>
> Eat real food. Not too much. Mostly plants. #FoodRules (Michael Pollan)

V679 selects ⟦stir controversy⟧ ⟦carnivore diet⟧. V684 selects
⟦Tired of⟧ ⟦bitcoin carnivore narrative⟧. Neither identifies beef. A shared
broader food/diet subject may exist; these two existing groups are not thereby
parent and child.

The subject pair `Nostr.` → `Music.` scores 0.6805. The more descriptive Nostr
alternative scores 0.0001 against Music. Neither the original Nostr masks nor
the complete notes justify placing the entire Nostr category under Music.
Preserving alternatives exposes this instability; taking their maximum would
accept the bad relationship.

### Coverage rejection is not automatically evidence of a bad group

| Existing member subject | Candidate | Score |
|---|---|---:|
| The author has just had a coffee. | Coffee. | 0.0976 |
| Grinding coffee beans. | Coffee. | 0.1759 |
| Rosemary in sourdough bread. | Sourdough bread. | 0.3299 |
| Wishing the Nostr community a good morning. | The author wishes readers a good morning. | 0.0588 |

The corresponding masks are V859 ⟦Just had⟧ ⟦coffee⟧, V410
⟦grind coffee beans⟧, V290 ⟦rosemary⟧ ⟦sourdough bread⟧ and V824
⟦Good morning nostr⟧. These are meaningful topical matches. The scores cannot
be used to prune them without introducing omissions.

The Good morning candidate also contains a particular author's action and
audience. A complete communicated claim is not automatically a good generic
category description. The current input renderer adds another potential problem:
it embeds such sentences inside `This text is about ...`, with two final periods.

### Some rejection does expose real sense differences

The Rise candidate `Getting up.` covers the three N052 masks from `Rise and grind
coffee beans`, while rejecting V519's ⟦Aussies' Christmas lunch costs rise⟧ at
0.000075. Art likewise rejects a state-of-the-art cooking-appliance claim at
0.000084. These sense mixtures were already known; this run shows an available
subject-based check can expose them. It does not establish that every rejected
member is wrong, as the coverage examples above demonstrate.

## Every positive group direction

Arrows run from proposed child to proposed parent. Scores are ranges across
retained alternatives; the fraction is positive alternatives / all alternatives.
Judgments concern masks and their original notes, not the diagnostic names.
Equivalent subjects need union/recovery of note membership, not redundant nesting.

| Input | Child → parent | Positive | Score range | Inspection |
|---|---|---:|---:|---|
| Mask text | Beef → Carnivore | 1/1 | .8950 | Related food topics, not containment; N096 pasta and vegetables. |
| Mask text | GM Nostr → GM | 2/2 | .9012–.9358 | Valid greeting refinement; already present through literal containment. |
| Mask text | GM Nostr → Nostr | 2/2 | .9432–.9869 | Plausible Nostr-community refinement; narrower protocol-only interpretation would not cover it. |
| Mask text | GM Nostr → Music | 2/2 | .5250–.8942 | Wrong; V805 and V486 are greetings, not music. |
| Mask text | Sourdough bread → Bread | 1/1 | .9957 | Valid, already known. |
| Mask text | Rise → Bread | 1/1 | .6749 | Wrong for this group: getting up and rising lunch costs. |
| Mask text | Rise → Good morning | 1/1 | .9746 | Waking/getting up is not a greeting; price-rise member further contradicts it. |
| Mask text | Brisket → Beef | 1/1 | .9037 | Plausible ordinary food refinement from N019/N085. |
| Mask text | Good morning → GM Nostr | 1/2 | .0014–.8196 | General greetings are not specifically Nostr greetings; V120/V861 and case sensitivity contradict containment. |
| Mask text | Good morning → Rise | 1/1 | .7957 | Greeting and getting up are associated, not equivalent; Rise also mixes price meaning. |
| Subject | GM → Good morning | 1/1 | .9168 | Equivalent greeting topics, not narrowing. |
| Subject | Beef → Carnivore diet | 1/1 | .6942 | Not containment; N096 recipe includes vegetables/pasta. |
| Subject | GM Nostr → GM | 1/1 | .9923 | Valid greeting refinement. |
| Subject | GM Nostr → Good morning | 1/1 | .8078 | Valid greeting refinement, but parent seed is written as a particular author's claim. |
| Subject | Carnivore diet → Beef | 1/1 | .8285 | Not containment; N074 discusses diet controversy without identifying beef. |
| Subject | Coffeechain → Coffee | 2/4 | .3250–.9824 | Plausible coffee-community refinement; alternatives vary in community/drink scope. Not certified by the highest score. |
| Subject | Homesteading → Nostr | 1/2 | .0062–.6032 | Wrong as a general subject relation; a post's platform does not make homesteading a kind of Nostr. |
| Subject | Homesteading → Freedom | 1/1 | .6053 | Possible association, unsupported containment. Homesteading masks identify food preparation/chicks, not freedom. |
| Subject | Nostr → Music | 1/2 | .0001–.6805 | Wrong. Added protocol context changes the decision dramatically. |
| Subject | Grow Nostr → Nostr | 5/8 | .1984–.8453 | Plausible community-growth refinement; wording-dependent decisions. |
| Subject | Sourdough bread → Bread | 1/1 | .9689 | Valid, already known. |
| Subject | Brisket → Beef | 1/1 | .9359 | Plausible under Beef; the actual meal-specific parent description does not cover every Beef member. |
| Subject | Good morning → GM | 1/1 | .9801 | Equivalent greeting topics, not narrowing. |

All 23 positive directions were inspected. No overall accuracy is reported:
the remaining pairs do not come with an exhaustive gold taxonomy, and some
plausible refinements remain questions of scope. This is a main-agent audit;
an independent audit agent could not be started because the thread limit was reached.

## Next question and limits

Existing subjects can supply missing abbreviation context. But a group's seed
subject is not necessarily a description of the whole group, and aboutness
classification is not a certified category-containment test. HyperDef's
sense-specific definitions motivate using context, not treating every associated
description as a broader subject.[^1]

The model author's example uses the input sentence directly and wraps only the
candidate class.[^2] [GDR03's completed rendering control](./SUBJECT-INPUT-RENDERING.md)
fixes some coverage misses but introduces associated-topic relations and retains
other obvious misses. It preserves all current subjects, including descriptions
that may themselves be unsuitable. Group-description choice, reliable relations,
membership recovery and complete browsing paths remain unproven.

## Reproduction

The GDR02 directory includes the exact runner and helpers, pinned model hashes,
source/input hashes and all 2,409 scores. A replay from the saved source into
`/tmp/navigation-gdr02-reproduce` was byte-identical for scores, candidates,
summaries, groups, fixture and runner snapshots. Inference took 84.63 seconds
with two CPU threads, batch size four and no model download. Peak process RSS
was approximately 4.80 GiB. No paid model or external compute was used.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/seed_subject_relations.py \
  --groups sse_multivector/navigation-research-v1/LGR01/groups.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --fixture sse_multivector/navigation-research-v1/GDR02/fixture.json \
  --cache /tmp/oracle-nli-model-cache --output /tmp/gdr02-replay-new
```

[^1]: Yin and Roth (2018), [Term Definitions Help Hypernymy Detection](https://aclanthology.org/S18-2025.pdf), section 3.3 and section 4 analysis. This experiment is not a reproduction of HyperDef.
[^2]: Moritz Laurer, [DeBERTa zero-shot model card](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0#how-to-use-the-models), accessed September 11, 2026.

**Selected data:** Compact pair-score results, inputs and parameters for `GDR02` are selected for release as `numerical/pair-scores-73a3d2de97c2627c` in the [publication catalog](../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.
