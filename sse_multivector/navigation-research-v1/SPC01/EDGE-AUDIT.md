# SPC01 parent–child audit

These are all 30 links whose two endpoints contain at least two distinct notes.
The counts and labels are the unmodified algorithm output. Judgments concern
meaning and source evidence, not agreement with a prescribed taxonomy.

P identifiers belong to `construction/result.json`. Row numbers identify the
saved generated description in `construction/inputs.json`, not a new note.
[Source evidence](./SOURCE-EVIDENCE.md) supplies the full original note with its
original mask for every endpoint's source row and the diagnostic controls.
The raw result retains every occurrence, phrase-selection range and edge witness.

Every child occurrence was inspected, with parent evidence checked for the
distinctions and omissions stated below. This is not an exhaustive annotation
of every possible note/category membership. The last fifteen links received an
independent semantic audit of all their child and parent records. Judgments are
research analysis, not user approvals or a numerical semantic benchmark.

An equal note set does not make a conceptual refinement false; it makes that
particular transition unhelpful for narrowing the returned notes. Conversely,
a smaller set is not proof of narrower meaning: relevant notes may simply be
missing. These two findings must remain separate.

| Parent → child | Notes | Judgment and concrete evidence |
|---|---:|---|
| P0066 author → P1499 post author | 37 → 2 | No useful distinction. All are authors of these posts. Rows 119, 311, 551, 901, 906 select N045/N060 because their descriptions happen to say “post author.” |
| P0122 bread → P1601 Sourdough bread | 8 → 2 | Valid refinement, already known before this run. Rows 40, 99, 148, 170, 356, 656, 669, 674, 680 support N015/N037. |
| P0129 Brisket → P1596 Smoking brisket | 2 → 2 | Valid cooking-method refinement, but equal destinations. Rows 438/N019 and 628/N085 explicitly have brisket and a smoker. |
| P0164 chain → P2111 themed social media posting chain | 10 → 6 | The shared social-posting meaning is plausible; the parent “chain” is underspecified. Rows 175, 241, 382, 430, 644, 701 are mostly coffeechain/foodchain masks. Excluded N029/N071 describe that same general kind of chain; the shrinkage is not a demonstrated conceptual distinction. |
| P0164 chain → P2114 coffee themed social media posting chain | 10 → 2 | A coffee-related posting refinement is plausible. Rows 347/N071 and 648/N029 support it through coffeechain. Other coffeechain parent notes are omitted. Hashtag affiliation is not automatically substantive discussion, but is not automatically meaningless either. |
| P0200 coffee → P1706 author's coffee | 21 → 2 | Reporting-language distinction, not a dependable narrower destination. Rows 549/N058 and 921/N045 concern personal coffee, but other parent notes do too; for example N095 explicitly says “Just had a coffee.” “Author” also changes referent across notes. |
| P0209 community → P1442 Nostr community | 10 → 4 | Plausible specific-community refinement. Rows 60, 71, 133, 539, 651, 925 address or refer to the Nostr community in N005/N058/N089/N092. This does not mean they discuss protocol engineering. |
| P0209 community → P1495 Plebchain community | 10 → 2 | Plausible affiliation/community refinement from rows 262/N095 and 640/N048. Both witnesses are plebchain hashtags; the desired scope of hashtag-derived categories remains open. |
| P0235 cream → P1336 ice cream | 4 → 2 | Scope-sensitive, not certified as a strict refinement. N024/N068 discuss the frozen dessert; N045/N060 discuss cream in coffee. A cream-based-food connection is plausible, but stripping the compound does not establish that the standalone parent has the same intended sense. Rows 9, 46, 308, 416, 570, 571, 587, 595, 727, 794. |
| P0266 diet → P1132 carnivore diet | 5 → 3 | Valid diet-topic refinement. Rows 206, 267, 304, 414, 833, 882, 883 concern N028's non-carnivore recipe qualification, N041's diet context and N074's diet controversy. A negative comment about a diet still concerns that diet. No animal-sense Carnivore → Dog inference is involved. |
| P0272 dinner → P1707 author's dinner | 7 → 2 | Non-distinguishing reporting language. Rows 70, 200, 332, 351, 353, 659, 896 concern N007/N023's own dinners, but other parent notes also describe their own dinners, such as N078. |
| P0352 food → P1295 better food | 29 → 2 | Genuine positive food-quality commonality is plausible; comparative wording is not consistent. Rows 348/602 describe N070's choice of better food, while 385 describes N054's “good food.” Native lemmatization combines good/better. This is not automatically a false semantic grouping merely because one is comparative. |
| P0352 food → P1396 many foods | 29 → 2 | Variety/quantity is a plausible shared qualification, but “many foods” is a weak standalone rendering. Row 89/N070 concerns the variety of foods humans can eat; 346/N011 concerns finding many new tasty things in Japan. Preserve this uncertainty rather than rejecting an unexpected commonality. |
| P0352 food → P1505 processed food | 29 → 2 | Valid refinement. Rows 47, 164, 765, 781, 824 support N032's criticism of processed food and N069's advice to avoid it. The phrase itself was already available in earlier experiments. |
| P0392 greeting → P1796 good morning greeting | 7 → 7 | Valid conceptual refinement; all retained parent notes already contain morning greetings. Rows 133, 192, 361, 539, 619, 651, 913. Equal destinations add no navigation value. |
| P0412 health → P1637 their health | 2 → 2 | No distinct shared subject. Rows 781/N032 and 564/N073 expand “bad for me” into the respective authors' health. “Their” is not a common specific referent. |
| P0479 jars → P1247 few jars | 2 → 2 | A real quantity qualification, not a parser mistake. N081 adds a few gianduja jars; N026 considers selling a few salsa jars. Rows 225, 390, 652, 653; equal destinations. Its usefulness as a category remains uncertain. |
| P0554 media → P1597 social media | 10 → 8 | General conceptual refinement, but all parent evidence already concerns social media. Excluded rows 347/N071 and 648/N029 literally describe a coffee-themed social-media posting chain. The observed shrinkage is a wording/structure omission. |
| P0554 media → P1749 coffee social media | 10 → 2 | Plausible coffee-related posting meaning, awkward incomplete rendering. Rows 347/N071 and 648/N029 mask coffeechain; projection loses “-themed” and “posting chain.” Other coffeechain witnesses remain outside the child. |
| P0567 milk → P1519 raw milk | 2 → 2 | Valid explicit qualification, equal destinations. Rows 331/N006 and 743/767/N051 genuinely discuss raw milk. |
| P0581 morning → P1296 good morning | 15 → 10 | Meaningful greeting-topic narrowing. Ten notes have explicit GM/good-morning greetings. Parent-only N043/783 and N069/90 concern morning activities. Read the child as a greeting topic, not a claim that the morning was pleasant. |
| P0599 network → P1444 Nostr network | 2 → 2 | Plausible particular-network refinement, equal destinations. Rows 218/N024 and 221/N048 expand grownostr. Both original witnesses are hashtags; discussion of network behavior is not established. |
| P0605 Nostr → P1312 Growing Nostr | 12 → 2 | Growth/promotion is a plausible narrower topic; hashtag-only scope is unresolved. Rows 250/N029 and 622/N071 are admitted, while equivalent parent descriptions at 60, 218, 221, 609, 925 are omitted. Native amod attachment of “Growing” does not prove the semantic relationship. |
| P0686 plans → P1081 author plans | 6 → 4 | Unsupported nominal refinement from a parse error. All eight child occurrences are finite clauses; e.g. row 41 says “The author plans to store…”. Native annotation makes plans a noun and author its compound modifier. Rows 28, 41, 128, 364, 555, 610, 686, 728. Do not silently rewrite the result as “authors' plans.” |
| P0709 preparation → P1259 Food preparation | 4 → 2 | Valid category relation, incomplete membership. Admitted 899/N026 and 673/N076 concern food preparation/chef affiliation. Excluded 866/N089 explicitly describes bread preparation; 350/N100 describes beef and steak preparation. Neither is a valid non-food contrast. |
| P0710 preservation → P1260 food preservation | 3 → 2 | Valid category relation, incomplete membership. Rows 48/484/N100 concern food preservation, and 468/N013 concerns pressure-canning stock. Excluded 904/N022 preserves garden-grown beets by freezing. Row 468's bad global attachment does not invalidate its correct local food-preservation phrase. |
| P0827 shop → P1157 coffee shop | 3 → 3 | Valid venue refinement, equal destinations. All 24 occurrences in N004/N038/N065 concern actual cafes; e.g. 151's rave, 825's music and 803's laptop/tablet restriction. Not merely hashtag evidence. |
| P0882 stock → P1144 chicken stock | 2 → 2 | Valid with Stock read as culinary stock. All twelve occurrences in N013/N026 concern chicken stock. Examples 360 and 712 explicitly identify it. No financial-stock contrast is observed here. |
| P0920 tea → P1330 hot tea | 4 → 2 | Valid explicit temperature qualification. Rows 234/N042 and 4/327/564/N073 say hot tea. Parent-only N072 has sweet tea and N080 unspecified tea; do not infer that either was cold. |
| P1796 good morning greeting → P1794 good morning greeting to Nostr community | 7 → 2 | Valid addressee refinement, incomplete membership. Rows 539/N089 and 651/N058 mask GM Nostr. Row 133/N005 explicitly addresses members of the Nostr community but is omitted. Row 71/N092 is also relevant and missing from the nominal greeting parent. |

## Other source and construction controls

- N013/468: stock is the native grammatical head of “Pressure-canning homemade
  chicken stock.” The generated Stock → extended phrase link therefore needs
  caution: the complete activity is not simply a narrower kind of stock.
  This stays visible in the raw `construction/result.json`, not the multi-note
  menus. No copular link from Stock to
  Food preservation is generated, and no such link is credited as a success.
- N100/728: the description combines saved myoglobin with chicken feeding,
  while the original gives the myoglobin to the dog. This is an upstream
  description error. Other clean planning descriptions (610/686) still support
  the note's occurrence; do not explain its entire placement by row 728 alone.
- N046/779 and 909: sea and salt both modify flakes/toppings rather than one
  another in the saved parses. Sea salt flakes is produced; the intermediate
  Sea salt is not. N063/696 and 822 do produce Sea salt. Consequently the latter
  is a one-note candidate and disappears from the multi-note menu. This is a
  missed familiar refinement, not evidence that N046 is irrelevant to sea salt.
- N010/278 and N092/243: Chicken dish and Chicken tractor are distinct complete
  candidates. They improve on the earlier prefix “a chicken,” but each has one
  note. Their existence establishes local expression construction, not useful
  multi-note browsing. Dish → Chicken dish and Tractor → Chicken tractor are the
  actual paths. The separate Chicken root also contains both source notes and
  spans food and live birds; it is not an ancestor of those two candidates.
- N037/356: Bread → Sourdough bread → ingredient-qualified sourdough bread is
  produced. The last expression has one note; Sourdough bread has two. No new
  multi-note ingredient refinement is demonstrated.
- N047/375 and 838: Baking bread in pans and Bread in pans are complete but
  separate one-note candidates. N072/501 instead produces Irish soda bread;
  no shared category from the ambiguous prefix “bread in” is forced.
- N037/669 and N072/254: Rosemary in sourdough bread and fresh rosemary to Irish
  soda bread remain separate. The latter reflects the saved attachment, not a
  corrected paraphrase. No shared rosemary-bread refinement is constructed.
- N094/572 and N086/854: the common coffee-taste experience is not recovered as
  one refinement. N065/345's internet dispute does not enter the Experience
  candidate through the verb “experience.” This avoids that particular mistake
  without establishing complete experience membership.

## What the audit establishes

Useful source-backed refinements coexist with reporting-language choices,
incomplete memberships and a few incorrect grammatical projections. The audit
does not assign one aggregate semantic pass rate to these different issues.
It does not equate 204 disconnected roots with 204 invalid subjects.

SPC01 establishes a limited construction capability, not a usable full menu.
Its Food and Bread roots are not connected; Coffee's only recurring child is
“author's coffee.” Removing weak labels or raising the support threshold would
not supply the missing relationships or recover omitted relevant notes.
