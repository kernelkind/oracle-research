# Merge rules: results to inspect

Start with **M06 and M07**. Keep **M01** beside them: it preserves useful relationships that both weaken. These are candidates for inspection, not a selected replacement for HDBv3.

All runs contain the same 100 notes and 916 distinct vectors, representing 945 original masks. Only the merge rule changes. No hierarchy titles were generated and no memberships were moved by hand.

`N046` identifies a note. `V362` identifies one mask and its vector. `M06/1397` identifies group1397 in M06; the same number in another run means something different. Brackets below show the exact mask fragments, in source order.

## Open the hierarchies

Each command opens the saved hierarchy with the default two-note display minimum, initially focused on one example. Children remain nested. Press `j/k` to select, `l` to expand, and `Enter` on a mask to see its full original note. `Esc` returns to the hierarchy; `u` moves upward. Unopened siblings appear above the branch already opened. `q` exits. Omit `--start-at` to begin at the root.

### Manual coffee example

This separate, read-only proposal was constructed from the original notes,
not by labeling the existing tree. Coffee contains 18 notes; Morning coffee
contains six and Coffee preparation contains five. Seven notes remain directly
at Coffee without a forced narrower category. This is one proposed arrangement,
not a unique target or an approved hierarchy. It has not yet been compared with
the algorithm's output. All saved algorithm runs and source artifacts remain
unchanged.

```sh
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-manual-coffee-hierarchy.sh
```

Choose with `j/k`; open with `Enter` or `l`. Only immediate child categories
are shown. The separate note actions let you inspect all notes in a category
or only its notes outside children; those actions are not additional subjects.
Within notes, `h/l` selects the previous/next note and `j/k` scrolls. `Backspace`
or `Esc` returns; `q` exits. `?` shows the manual reasoning and controls separately
from the original note. No decisions are automatically recorded.

The launcher uses the existing `sse-subject-navigation` binary with the explicit
`--notes` mode. `--check` validates the manual input and its source checksum
without opening the terminal. If needed, build once in `oracle-mvp`:

```sh
CARGO_BUILD_JOBS=2 CARGO_TARGET_DIR=target/merge-rule-review-build nix develop -c cargo build --bin sse-subject-navigation
```

### Algorithm hierarchies

M06, starting with the ingredient example:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M06.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history --start-at 1397
```

M07, starting with the restaurant example:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M07.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history --start-at 1523
```

M01, starting with preparation for later use:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M01.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history --start-at 1434
```

Baseline, using the identical note-set simplification:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/response.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --note-navigation
```

## Optional five-note view of M06

This is the same M06 tree, not a new merge-rule run. Only groups containing at least five distinct notes are offered as choices. Masks from smaller groups appear at their nearest displayed ancestor. All 100 notes, 916 unique vectors and 945 original mask IDs remain; no merge, source text or membership changes. The root is always available, even when a corpus has fewer notes than the minimum. Existing parent-mask hiding still applies when that note is accessible in a displayed child.

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
target/merge-rule-review-build/debug/hdbscan-hierarchy \
  sse_multivector/merge-rule-exploration-v1/M06.json \
  sse_multivector/real-note-fine-segmentation-v1/vectors/vector-map.json \
  sse_multivector/real-note-fine-segmentation-v1/reviewed-input.json \
  --merge-history --min-notes 5 --start-at 1512
```

Remove `--min-notes 5` to compare the old view at the same group. Omit `--start-at 1512` to open the root. Press `?` for the active view's rules. These options belong to the binary above; the older HDBv2 launcher is unchanged.

| M06 view | Displayed groups | Terminal groups | Notes per terminal group | Maximum depth |
|---|---:|---:|---|---:|
| Default minimum 2 | 488 | 194 | 2 | 22 |
| Optional minimum 5 | 150 | 39 | 5–7 | 19 |

These are counts, not quality scores. Inspect these same starts in both views:

| Start | Current view | Five-note view | What to inspect |
|---|---|---|---|
| 1512 · 5 notes | Children 1385 and 1444, each with 3 notes | No subgroup choices; all 15 original masks directly available | Animal flesh as food across preparation, preference and opposition. The view gathers the evidence without forcing another choice. |
| 1627 · 22 notes | Children 1561 (3 notes) and 1605 (19) | Child 1605 remains; the five masks from 1561 appear directly at 1627 | The smaller group connects hot tea, sweet tea and morning tea. Its notes remain, but the independently selectable tea group disappears into a parent also containing coffee and other material. |
| 1733 · 5 notes | Children 1641 (2 notes) and 1681 (4) | No subgroup choices; all 25 masks directly available | Stock preservation, frozen beets and a vacuum sealer coexist with bathroom grab bars, an induction hob and chicken feeding. Meeting five does not make this uniformly food preservation. |

The minimum reduces choices, but cannot repair the underlying parent placements. Whether losing useful small choices is worth the simpler navigation remains for user inspection; five is not a frozen product requirement.

## 1. M06 gives useful intermediate groups that HDBv3 lacks

**Evidence — every mask in M06/1397, from N046, N063 and N096:**

- V360 · N046: ⟦bagels⟧ ⟦sesame⟧ ⟦sea salt flakes⟧ ⟦plain⟧
- V362 · N046: ⟦bagels⟧ ⟦sea salt flakes⟧
- V538 · N063: ⟦Mushroom Risotto with Shrimp⟧ ⟦Sea Salt⟧
- V528 · N063: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pecorino⟧
- V539 · N063: ⟦Mushroom Risotto with Shrimp⟧ ⟦Pepper⟧
- V881 · N096: ⟦Spaghetti Bolognaise⟧ ⟦Salt and pepper to taste⟧

The original N046 lists bagel toppings; N063 lists risotto ingredients; N096 supplies a Bolognaise recipe. The child1029 groups bagel/risotto salt, while child1274 groups pepper and cheese. Their parent remains broader than salt alone: Pecorino is not described as a salt substitute.

**Comparison:** allowing relevant alternative masks from each note, HDBv3 first contains the three seasoning contributions at displayed group1352, with85 notes. M06/1397 contains only these three notes and preserves both children.

**Analysis:** this is a plausible improvement in intermediate discovery, not merely a shorter tree. However, M07/1336 already contains the same three notes through salt and added recipe water. M06 supplies more specific seasoning evidence; it does not newly recover those notes from M07. M07's complete seasoning counterpart1541 contains8 notes.

A second M06 stop is **1489**. Its complete four-mask membership is:

- V501 · N059: ⟦Maybe seeing the world with a restricted color palate tones down⟧ ⟦emotion-based resistance to new foods⟧
- V182 · N024: ⟦people⟧ ⟦don’t like ice cream⟧ ⟦else⟧ ⟦hiding⟧
- V500 · N059: ⟦emotion-based resistance to new foods⟧
- V552 · N064: ⟦Today meat dumplings⟧ ⟦out of sentiment⟧

N024 jokes about red flags; N059 offers a speculative explanation of food resistance; N064 describes sentimental food after Christmas. Their different attitudes can support one broader food-related connection. Neither the joke nor the speculative explanation is endorsed. HDBv3's relevant counterpart1297 contains62 notes; M07's1814 contains37.

## 2. M07 preserves relationships that M06 separates

**Evidence — every mask in M07/1523, from N010, N050, N057 and N065:**

- V568 · N065: ⟦No laptops or tablets⟧ ⟦on weekends⟧ ⟦went to another coffee shop⟧ ⟦will remove this one from rotation⟧
- V404 · N050: ⟦currently have no ways to get pizza⟧ ⟦goals by next year⟧ ⟦ONE pizza restaurant⟧ ⟦our town of St Michel de L'Attalaye⟧ ⟦haiti⟧
- V485 · N057: ⟦Largest Barbecue Chain in U.S. Quietly Shuttering Locations⟧
- V077 · N010: ⟦Chinese take out place⟧ ⟦behind the register⟧ ⟦eating⟧ ⟦beautiful dish⟧ ⟦isn't on the menu⟧

The originals concern changing coffee shops after a restriction, a town without pizza, restaurant closures, and unavailable off-menu food. N065's full original says the author considered changing router passwords but instead left; the mask does not claim they changed them. N050 proposes a future restaurant; one does not already exist.

**Comparison:** the first three restaurant notes, even allowing their other relevant masks, require99-note ancestors in HDBv3/1640 and M06/1812. M07/1523 supplies a four-note group, adding a substantive coffee-shop example. Its two children1253 and1324 remain separate underneath. M05/1467 also provides a useful three-note option; this is not unique to M07.

**Analysis:** M07 offers a defensible broader relationship across different venue problems, without pretending they are the same cuisine or restriction. It is a useful reason to inspect M07 alongside M06.

Another stop, **M07/1080**, has exactly:

- V549 · N064: ⟦kitchen⟧ ⟦work⟧ ⟦From all this I⟧ ⟦forgot to take photos⟧
- V391 · N048: ⟦Photography⟧
- V761 · N080: ⟦#artoninstagram⟧ ⟦#painting⟧

HDBv3/1614 and M01/1674 already preserve these three notes through relevant art/photo masks; M06 requires the100-note root. This is preservation of existing discovery, not a new success over the baseline. Two contributions are bare tags: they support a limited art/photo connection, not evidence that those notes teach photography. The original N048 is mainly an animal-ethics quotation with tags; N080 is a diary with an art-related passage and tags. No linked image was interpreted.

## 3. M01 still offers useful groups that the later candidates weaken

**Evidence — every mask in M01/1434, from N013, N080 and N091:**

- V737 · N080: ⟦I soft boiled nine eggs for my lunch over the next few days⟧
- V823 · N091: ⟦Century eggs⟧ ⟦preserving duck, chicken, or quail eggs⟧ ⟦for several weeks to several months⟧
- V095 · N013: ⟦chicken stock⟧ ⟦We save carcasses⟧ ⟦a couple of times a year do this⟧

The original N013 saves butchered carcasses, makes stock, then pressure-cans it for the pantry. N080 prepares eggs for future lunches. N091 describes preserving eggs. These are different timescales and methods, but preparation or preservation over time is a reasonable commonality.

**Comparison:** permissive relevant alternatives need62 notes in HDBv3/1297,8 in M06/1647, and6 in M07/1564. Requiring N080's explicit future-lunch mask gives95 notes in HDBv3/1517; the shortlisted candidates' counterparts stay unchanged.

**Analysis:** M01 preserves a focused option. The M06/M07 counterparts also contain food reluctance, a red-flags joke, and ancient-meat consumption: broader food/time connections, not uniformly irrelevant notes. M02/1577 reaches the same three notes through daily egg production, so it has not lost those notes; that is a different relationship from future meal preparation. Moving upward from M01/1434 also brings ancient-meat material into1519. The useful child survives, but its parent is not simply more preservation material.

For a separate preservation comparison, open **M01/1477**. Its complete masks are:

- V149 · N022: ⟦This year’s beets⟧ ⟦ready for the freezer⟧ ⟦raised bed⟧
- V939 · N100: ⟦vacuum sealer⟧
- V942 · N100: ⟦foodpreservation⟧
- V099 · N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦save carcasses when we butcher⟧ ⟦I’ll pressure can it⟧ ⟦store in the pantry⟧
- V148 · N022: ⟦beets⟧ ⟦Vac sealed⟧ ⟦ready for the freezer⟧
- V097 · N013: ⟦chicken stock⟧ ⟦I’ll pressure can⟧ ⟦store in the pantry⟧
- V100 · N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦pressure can⟧ ⟦store in the pantry⟧
- V943 · N100: ⟦#prepping⟧
- V102 · N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦pressure can⟧ ⟦pantry⟧ ⟦foodsecurity⟧

The originals describe canned stock, vacuum-sealed beets, and using a new sealer after cutting meat. The three-note group is supported beyond the tags. HDBv3's concrete counterpart1396 has87 notes. M06/1681 and M07/1163 have4, including bathroom grab-bar masks from N092. N092's separate lunch paragraph cannot turn those masks into food-preservation evidence. M06/1586 does reach the three notes through `#prepping`, so the weakness concerns concrete preservation access, not complete disappearance of that note combination.

## 4. Changing the merge rule does not settle every weak placement

**Evidence — the complete two-mask M06/1601:**

- V909 · N098: ⟦I'm⟧ ⟦in⟧ ⟦corner⟧
- V229 · N027: ⟦CombiCookTop V4000 I804⟧ ⟦V-Zug⟧ ⟦sits flush with the worktop⟧

N098's complete original:

> Don't mind me. I'm just that goblin in the corner eating a whole tub of kimchi.

N027's complete original, with V229 highlighted:

> ⟦CombiCookTop V4000 I804⟧ by ⟦V-Zug⟧
>
> http://static.dezeen.com/uploads/2024/04/combicooktop-v4000-i804-vzug-design_dezeen_2364_sq-411x411.jpg
>
> Dezeen Showroom: the extractor fan appears almost invisible in the CombiCookTop V4000 I804, a refined induction hob by Swiss brand V-Zug. The CombiCookTop V4000 I804 is one of V-Zug's most state-of-the-art products, with a design that is sleek and minimalist while incorporating several advanced cooking functions. The hob ⟦sits flush with the worktop⟧, and the applicance
> The post CombiCookTop V4000 I804 by V-Zug appeared first on Dezeen.
>
> https://www.dezeen.com/2024/04/08/combicooktop-v4000-i804-vzug-dezeen-showroom/

**Analysis:** both masks express placement, so their similarity is not inexplicable. But the first is too sparse to convey the kimchi joke, and neither establishes a more specific shared use or setting. I would flag this narrow option for your judgment, not automatically call every broad spatial grouping invalid. M06 leaves singleton-pair scores unchanged; earlier choices made this pair available. Its appearance does not prove source-note weighting changed these vectors or directly lowered this pair's score.

## What the exploration establishes

The frozen vectors support substantially different useful intermediate memberships under different merge rules. HDBv3's existing placement is therefore not the only hierarchy available from this representation. M06 and M07 provide complementary improvements, while M01 and the other saved runs preserve worthwhile alternatives. None is established as a coherent finished hierarchy or an overall winner.

Nine rules were implemented and compared: nearest-partner means, sums, smaller directional sums, all-pairs mean, all-pairs median, source-note-pair means, PARIS, eligibility-conditioned PARIS, and worst finite nearest-partner distance. The [experiment record](README.md) gives each question, definition, research basis, result and complete-tree audit. The examples above are inspection anchors, not the entire evaluation or a numerical pass rate.

The latest [CHAMELEON review](within-child-structure.md) identifies a different possible source of evidence: compare a proposed connection with structure inside its children. Published methods also change graph construction or initialization, and implementations disagree on important conventions. Those changes should be declared and tested separately; they were not quietly folded into this comparison.

**Recommended next step:** inspect M06 and M07 upward from the supplied examples, using M01 as the stated contrast. Include M03/1778 as an optional stop: it retains a useful six-note animal-processing/slaughter parent with a focused three-note child1614. A subsequent investigation can test within-child evidence or graph construction with its additional assumptions made explicit. This package does not preselect that method or authorize changing the representation.

## Verification and reproducibility

All nine saved runs replay exactly through the production experiment CLI: all915 merges, frozen source hashes, canonical IDs, alias groups and summaries match. The37 merge-rule tests pass. A pinned Nix environment providing Python3.13.14/NumPy2.5.0 was also verified against all nine histories; it does not require the original machine-specific Python path. See [reproduction commands](README.md#reproduce-m01).

All listed start IDs pass the production viewer's input validation. M01, M06 and M07 were also opened in real terminals: nested children, inline masks on full originals, upward expansion, and clean exit were inspected. No renderer or input data changed during final packaging. Complete-tree reading coverage is documented separately from these UI checks and from semantic judgments.

All results remain a small, food-focused pilot. Note-count comparisons use the documented, source-supported alternative masks; they do not enumerate every conceivable meaning of a note. The complete root partition, sensitivity to another corpus, and scalability beyond this local comparison remain unestablished. There are no missing results concealed by a forced winner.
