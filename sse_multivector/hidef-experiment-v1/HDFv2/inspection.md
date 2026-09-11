# HDFv2 — additional inspection selected before the runs

This records the twelve additional groups and ten relationships frozen in [PLAN.md](./PLAN.md). The main [results](./README.md) cover the seven known anchors separately. These are analyst judgments, not user approvals or automatically scored failures.

All IDs below use seed 123. **O** means HDFv1, **M** means HDFv2 `mutual_best_per_note`, and **C** means HDFv2 `strongest_edges_matched`. The number is the actual group ID in that run. Descriptions explain masks; they are not generated or stored titles.

Correspondences are the two closest vector sets plus the closest note set, as recorded in [comparison.json](./comparison.json). One-note groups remain eligible so their disappearance from the TUI cannot be mistaken for improvement. A correspondence is only a place to inspect, not a judgment that two groups mean the same thing.

## Twelve groups

| Original group | Source-note restriction | Strongest-edge control |
| --- | --- | --- |
| **O1071:** cooking/eating implements | **M1134/1099** retain some cooking and utensil content, lose cookware handles, and add chicken, steak, and cooking activities. | **C1314/1330/1150** are one-note counterparts. Fragmentation, not demonstrated repair. |
| **O1030:** beets, chicks, biking | **M1210** mixes moving chicks, Movies, and biking. **M1039** adds workouts and chores. **M1220** matches notes through different kindness/greeting masks. | **C997/972** combine eggs and chickens with the 4×4 beet bed. No demonstrated improvement to the original association. |
| **O1151:** humans eat many foods; normal meat | **M1142** adds Music. **M1038** adds completed tasks and kitchen work. | **C1114** pairs human food with a mostly-plants diet plausibly. The normal-meat mask becomes singleton **C1230**. No compelling original subdivision was established. |
| **O1055:** coffee, bread, plate practices | **M1280** is one-note bread; **M961** mixes fixtures and food; **M1124** combines coffee with high-altitude soda bread. | **C1050** remains mixed coffee/bread, while **C1079** is a useful three-note bread group. |
| **O1069:** beef-dominant mixture | **M1008 → 1106** retains beef quantities alongside Sophia's age of five months and Cheese Doodle Day on March 5. This shrinks membership without fixing the unrelated-number association. | **C994/956** are more beef-focused, though beet sides remain. A local improvement, not perfect beef membership. |
| **O994:** unrelated meanings involving three | **M985** retains three stops, a third storm, three hours, and more number-related material. | Vector counterparts are mostly one-note groups. Note-only counterpart **C1094** concerns dogs through different masks. Disappearance is not semantic reassignment. |
| **O977:** tomato-dominant mixture | **M1007** keeps tomatoes with thyme, tandoori, and Sorrento cuisine. | **C964** is a coherent six-note tomato group. The old tomato joke is outside it. Child **C975** returns exactly the same six notes. |
| **O995:** food/diet arguments | **M957 → 1130** mixes food arguments with an audiobook described as meaningless fluff. | **C988** is more focused on food/diet disagreement; **C932** is a plausible broader meat/diet region. Those two are not a saved parent–child pair. |
| **O923:** broad food region | **M918** expands to 83 notes, including Linux, generic baby/family, and audiobook masks. **M917** has all 100 notes. | **C924/920** are more focused food/diet regions. Sophia's actual interest-in-food masks remain, without needing generic age/family masks to retain that aspect. |
| **O938:** food/cooking region | **M997 → 1166** keeps the king/butler fragment without the knife/fork mask that supported the original note's utensil interpretation. | **C936/943 → 956** gives plausible cooking/meals toward beef-dominant narrowing. **C956 → 994** is another beef subset without an evident further subject refinement. |
| **O931:** wellbeing/social miscellany | **M924/928** remain mixed greetings, routines, wellbeing, hard money, Island Life, and survival. | **C976** is more focused on positivity/humility, though “Don't mind me” is weak evidence. Its parent **C946** mixes that with minimalist appliances and simple food. |
| **O939:** household, food, Nostr mixture | **M933 → 958 → 1013** still mixes greetings with Gentoo and food tags; another equipment branch is heterogeneous. | **C1033** is a clean five-note GM group directly under root. **C963** participates in the promising preservation path below. |

## Ten relationships

| Original parent → child | Inspection of what replaced it |
| --- | --- |
| **O965 → 1071** | Neither policy preserves an edge between the selected counterparts. The control's child counterparts are one-note groups. |
| **O1005 → 1030** | No corresponding useful edge. The mutual chick/biking/Movies group has a mixed work/activity parent; some old parent/child distinctions collapse into the same counterpart. |
| **O929 → 1151** | **M939 → 1038** retains unrelated task-completion content. The control has plausible broader diet toward human-food/mostly-plants descendants, without a clearly established additional subdivision. |
| **O997 → 1055** | No corresponding mutual edge. **C940** has useful bread descendant **C1079**, but C940 also contains a raw, no-bake pie, so the whole parent cannot be described as baking. |
| **O994 → 1060** | Both mutual counterparts become the same faulty number-associated group. The control mostly fragments the original masks into one-note groups. |
| **O923 → 1134** | The mutual route starts through all-note **M917**, followed by food/drink-opinion subsets; no clear additional refinement was established. Selected control counterparts have no corresponding edge. |
| **O938 → 975** | **C936/943 → 956** is a plausible cooking/meals toward beef-dominant refinement. **M997 → 1166** is smaller but retains the butler mask. |
| **O931 → 950** | **C946 → 976** removes food/appliance material and leaves more coherent positivity content, but does not establish a coherent broad parent subject. Mutual counterparts collapse or reverse the original relationship. |
| **O919 → 939** | **C919 → 963** is promising: a broad food/preparation group toward a small cooking/storage group. **M917 → 933** retains a greetings/Linux/food-tag mixture. |
| **O939 → 983** | No direct counterpart edge. The control nevertheless has useful shared descendant **C1014**, under both C963 and C952. |

## One promising path, with its limitation

The control has this actual path, without rearranging memberships:

```text
916 · 100 notes, artificial root
└─ 919 · 36 notes
   └─ 963 · 4 notes
      └─ 1014 · 3 notes
```

Group 963 contains bread-pan cooking, pressure-canning chicken stock, vacuum sealing, and frozen beets. Group 1014 excludes bread and retains these masks:

- V097 · N013: ⟦chicken stock⟧ ⟦I’ll pressure can⟧ ⟦store in the pantry⟧
- V939 · N100: ⟦vacuum sealer⟧
- V099 · N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦save carcasses when we butcher⟧ ⟦I’ll pressure can it⟧ ⟦store in the pantry⟧
- V100 · N013: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦pressure can⟧ ⟦store in the pantry⟧
- V148 · N022: ⟦beets⟧ ⟦Vac sealed⟧ ⟦ready for the freezer⟧
- V943 · N100: ⟦#prepping⟧

That last transition is a defensible move toward food preservation, not just fewer examples. The broad 919 group is substantially food-related but contains weak dog/dogstr masks. Other food material in their source notes does not make those particular masks food evidence. This is a promising route, not certification of every membership or intermediate level.

Inspect this path and its alternate parents:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/run-hidef-hierarchy.sh --graph-policy strongest_edges_matched --start-at 919
```

Expand 963, then 1014. Press Enter on a mask for the complete original note. No subject titles are inserted into the display.

## Limits of this inspection

The independent review read all masks for the semantically assessed counterparts and paths, checking complete source notes where their meaning was ambiguous. M917 was assessed only for its 100-to-100 note transition, not exhaustively judged semantically. The main reviewer separately inspected anchors, original notes, and the control's preservation and tomato groups; those positive examples and the main conclusion agree between reviewers.

This is the primary-seed sample, not exhaustive semantic review of all nine hierarchies. Repeat-seed set intersections are saved but include isolated singletons: the strongest-edge control's high repeatability cannot be interpreted as proof of semantic quality. The useful examples coexist with lost coverage, weak associations, and unnecessary levels.
