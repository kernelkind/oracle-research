# M04 semantic audit B

## Scope and evidence

Provisional analyst judgments, not user approvals. No proposed semantic cut. The raw points below were disjoint inspection batches; their upper parents are outside this report.

Inspected **all 190 canonical leaves, 195 exact vectors, 501 mask fragments, and 168 internal merges** below raw M04 points `1767, 1763, 1753, 1708, 1634, 814, 1346, 1666, 1587, 1439, 1529, 892, 871, 1153, 1097, 1169, 0, 99, 1080, 1462, 1430, 1442`. These cover 61 distinct source notes. Alias vectors were individually included. The appendix records every canonical leaf, vector, and internal merge.

Evidence: frozen `real-note-fine-segmentation-v1/vectors/vector-map.json` fragments and byte spans; `real-note-fine-segmentation-v1/reviewed-input.json` original text; raw `M04.json`, `M01.json`, and `real-note-fine-segmentation-v1/hdbv3-cross-note-edges-v1/response.json` single-linkage tree. All 501 fragments were programmatically checked against their original UTF-8 byte spans, with zero mismatches. Original text of 47 notes was read in full when context affected interpretation. No vector subject strings or generated subject titles were used.

The criterion is broad-to-narrow **note** discovery. More masks from an already discoverable relevant note are not a new discovery; a missing exact-vector set is not automatically a loss. Broad connections can be useful even when their descendants are more specific. Weak parent attachments do not invalidate good descendants.

## Main findings

- Clear useful descendants survive: coffee preparation/consumption; coffee flavour and experience; wine usage/preference; tea; raw milk; coffee-shop music; coffee cream preferences; overconsumption concerns; timed cooking; sourdough; and cranberry/rosemary bread variations.
- Several unexpected broader connections are defensible: food flavour/preferences across coffee, gamey meat, a food walk, and resistance to new foods; wine availability, abstention, and cooking; different bread-making constraints. These should not be rejected merely for being broad.
- The most questionable small attachments are `1346` (ice / ice cream), `1224` and `1244` under `1462` (unrelated quantified fragments), `1387` (three stops / three chickens), `1559` (spaghetti packet instruction / opening last year's salsa), and `1680` (ambient temperature / cooking durations). The observations support weak semantic connections; they do **not** establish which input feature caused a merge.
- M04's seven-versus-six-mask difference for N040/N078 is **not** lost note discovery. M01 `1617` has seven masks; M04 `1550` keeps six that still discover exactly those two notes. The removed mask V314 describes the same breakfast venue already represented by four retained N040 masks.
- A broad mixed parent is not a reason to delete an entire branch. For example `1442` contains questionable pasta/pie attachments but also strong separate sourdough, cranberry/rosemary, and bread-process descendants.

## Audit by raw point

### 1767

Observed:

- `1387` pairs V016/N002 `["Sorrento's Savory Stroll", "3 delightful stops"]` with V202/N026 `["Today i", "acquired 3 rotisserie chickens", "marked down"]`. `1395, 1438, 1454` add only alternative masks from these same two notes. The source N002 is a short gastronomic walk, not buying three food items.
- `1690` adds V936/N100 `["vacuum sealer", "I got", "30% off", "Nesco VS-12"]`. The original note explicitly describes buying and using the sealer while processing meat.
- `1528` pairs V568/N065's weekend laptop/tablet rule and change of coffee shop with V404/N050's absent pizza restaurant and next-year goal. `1577, 1609, 1611` add three same-note N065 variants.
- `1591` pairs V314/N040 `["Local breakfast", "no service charge", "Roti  IKHWANA"]` with V399/N050 `["we currently have no ways to get pizza", "St Michel de L'Attalaye", "haiti"]`. `1701` adds the “easy” Sorrento walk mask; `1721` joins the two venue-related branches; `1767` joins this with food purchases/the sealer.

Judgment:

The small three-stops/three-chickens pair does not establish a specific culinary relation. Food access, obtaining food, and choosing local venues are legitimate broader connections for `1721` and possibly `1767`; they should not be dismissed just because the geography and food differ. The weak part is the very early N002/N026 pairing and its effect on the discount-sealer attachment: discounted chickens and a discounted sealer are concretely connected, but N002 already sits inside that descendant. The N065/N050 pair has a defensible broader commonality in inability/unwillingness to use a desired local venue, not a shared rule, country, or kind of meal.

Comparison: M01 `1423 → 1437 → 1479 → 1489` reproduces the two-note stops/chickens buildup; M01 `1569 → 1622 → … → 1663` also preserves the N065/N050 route. Thus these are not newly invented M04 problems. N040's placement here does not remove the N040/N078 discovery at `1550`.

### 1763

Observed:

- `1410`: V762/N081 `["Added", "few", "gianguja jars", "store"]` + V201/N026 `["Today i", "Made", "big jar", "yogurt"]`. `1417` adds another store/jar mask; `1541` adds N026's salsa-sale mask; `1695` adds N081's store/melanger mask.
- `1559`: V895/N096 `["Cook spaghetti according to packet."]` + V218/N026 `["salsa", "Pictured", "jar from last year", "i just opened"]`. `1630` adds another last-year salsa mask.
- `1717` adds V249/N030 `["salad dressing"]`; `1763` combines both branches. N030's original text is the tomato/salad-dressing joke, not a recipe.

Judgment:

The jars, homemade food, and offering jars for sale give `1410–1695` a defensible broad connection, becoming clearer when V215 explicitly mentions sale. `1559` does not share that commercial or preservation operation: a packet instruction and opening old salsa have only a broad prepared-food relationship. “Salad dressing” can relate broadly to salsa, but the exact mask drops the joke's action, so it cannot support a cooking-process interpretation of N030.

Comparison/alternative: M01 `1453, 1461, 1570` preserves the jar route and `1608` reproduces `1559`. More importantly, M04 already joins N026 and N096 through substantively matching tomato preparation at `1070`: V197/N026's acquired/roasted/prepared tomatoes for salsa and V891/N096's chopped tomatoes, tomato purée, and added water for Bolognaise. The poor small pair at `1559` therefore is not loss of relevant discovery of those two notes.

### 1753

Observed and judged merge by merge:

- `1041` joins V894/N096's low-heat `"45min-1hr"` simmer with V368/N047's bread-pan cooking taking `"5-6 min"`. `1299` adds V787/N085's brisket on a smoker for about three hours. These are valid examples of cooking durations, across very different foods/methods.
- `1680` then adds V488/N058 `["Woke up to 35 degress"]`. Original N058 describes cold autumn weather and being glad the coffee is hot, not oven or food temperature. The new attachment does not extend the cooking-duration relationship.
- `1046` joins V114/N016's half-pound chocolate intake making the writer sick with V674/N073's gallon of hot tea in under 24 hours and concern about whether it is bad. `1051, 1060, 1084` retain that clear excessive-intake/concern relationship while adding same-note variants.
- `1151` joins V113/N016's chocolate consumed by midday with V098/N013's chicken-stock batch yielding around 25 quarts. `1281` combines this with the five-mask excessive-intake branch. Producing a quantity of stock is not consuming too much; the full N013 note confirms batch preparation, pressure canning, and pantry storage. This is a weaker quantitative connection inserted beside a genuine one.
- `1452, 1485` add N088's claimed bodily persistence of consumed linoleic acid and distress about it. A broader relation through dietary intake and health concern is supported by the text, without endorsing the medical claim.
- `1163` joins V119/N016's long eggs/chocolate/laziness/distress mask with V173/N024's multi-clause red-flags joke about workout plans, food expiry, and dislike of ice cream. This is broad food attitudes/humour, not a precise shared eating behavior. `1360` adds V737/N080's eggs prepared for lunches; eggs connect it specifically to part of V119, not to N024. `1487` adds V682/N074's diet/veggie joke. `1590` joins this with the intake branch: a defensible broad dietary-attitudes parent, but with N013's batch-output insertion still present.
- `1029` joins V823/N091's preserved eggs over weeks/months with V095/N013's saved carcasses and twice-yearly stock making. This is more than “both mention time”: both concern preparing/preserving animal foods, and the original N013 expressly confirms pressure canning.
- `1411, 1422` add N090's argument for eating meat because humans have done so for millions of years. That shares animal foods but not a preservation operation. `1668` adds V800/N088 `["Linoleic acid", "FOUR YEAR half life"]`; this weakens the animal-food-preservation relation to disparate food-related timescales.
- `1711` combines dietary attitudes/intake with that mixed branch. `1753` adds cooking durations and the cold-weather mask. Only very broad food-related quantities/times/attitudes cover every member; the useful smaller cooking, intake-concern, and preservation descendants remain identifiable.

Comparison: M01 `1050` and baseline `1070` preserve the cooking-duration pair; M01 `1039` and baseline `1055` preserve the stock/egg-preservation pair. The five-mask N016/N073 branch exists at M01 `1086` and baseline `1112`; the questionable seven-mask expansion including stock output also exists at M01 `1244` and baseline `1254`. M04 has not newly discovered the underlying two-note overconsumption relationship.

### 1708

Observed:

- `1361` combines V722/N078 `["india", "food"]` and V311/N040 `["Local breakfast", "Roti  IKHWANA"]`. `1369, 1465, 1540, 1550` add N040 variants and the bare `["india"]` mask, with no new notes.
- `1245` pairs V700/N076's Tandori chicken/yogo with V081/N011's request to cook mochi bread from a Japanese convenience store. `1323, 1377` add N011 variants; `1398` adds V910/N098 eating kimchi.
- `1385` pairs V086/N011's mochi bread/Japan/common convenience-store food with V701/N076 `["sexi yogo"]`. `1413` adds N011 `["JapaneseFood"]`. `1464` joins these two branches; `1521, 1602` add N076/N011 variants; `1685` adds the N040/N078 branch.
- `1507` separately pairs V080/N011 `["mochi bread", "combini", "ハムチーズ"]` with V522/N063 `["Risotto", "Cremini"]`; `1708` joins this to the rest.

Judgment:

There is room for a broad connection among regional dishes and trying/making foods from different cuisines. India, a roti venue, Japan/mochi, Tandori chicken, and kimchi must not be misrepresented as one country or one dish. N040's original text says `#siamstr`, not India; N078 actually describes Lacha Paratha with dal fry. The initial mochi/yogo and mochi/risotto pairs are much weaker than a specific shared ingredient or method. The final risotto addition makes a narrowly Asian interpretation insufficient. This does not make every regional-food descendant bad; it makes the proper level of generality important.

Exact note-discovery comparison: M01 `1617` = V311–V315/N040 and V721–V722/N078, seven masks/two notes. M04 `1550` has six masks/two notes: V311, V312, V313, V315, V721, V722. V314 moves to `1591` but N040's breakfast/roti venue is still represented four times at `1550`. There is no lost N040/N078 discovery. Baseline `1549` already has the two-note regional-food pair, and `1554` expands it without adding a note.

### 1634

`972, 993, 995` retain N007's wine availability/abstention and N076's wine/food preference. `1065, 1098` connect N007's wine available with lamb to N076's wild-rose wine; `1127` adds N063's dry white wine in risotto; `1195, 1255` add N076 variants. `1433` joins these wine branches. `1634` adds V751/N080's gift of gin.

This is a defensible broad-to-narrow structure: different wine uses/preferences under a broader alcoholic-drink connection. Abstention is relevant discovery, not negative evidence that the note should be excluded. M01 `1334` has the same ten-vector/three-note wine set as `1433`. Baseline already has a three-note wine route at `1169`; its failure to retain every duplicate in one small descendant is not loss of those three notes.

### 1346

V282/N036 `["ice"]` joins aliased V181/V183/N024 `["Red flags", "people who don’t like ice cream"]`.

The originals are coffee served in ice and a humorous red-flags list. Cold/frozen consumables are a possible broad link, but the masks do not share coffee preparation, a dessert, or a preference about the same item. This is a weak small grouping, not proof of a particular lexical mechanism. M01 `1382` has the exact same three vectors, and M01 `1517` merely adds another N024 variant. Losing that extra variant in M04 is not lost note discovery.

### 1666

`1006, 1013, 1067` link N086's personal coffee roasting/taste profile with N094's decaf experience/flavour. `1056` independently links the fuller statements from those same notes; `1077` joins both. `1108, 1171, 1223, 1243` add N094 variants while retaining exactly the two notes.

`1282` adds V020/N002's foodies craving local flavours; `1350` adds another decaf-experience mask. `1474` adds V266/N033's liking strong/gamey meat flavour; `1501` adds another N002 flavour mask. `1627` introduces N059's colour-vision/new-food resistance comparison; `1649, 1666` add N059 variants.

Judgment: the coffee descendant is strong. The subsequent broadening is unexpectedly but defensibly about taste, enjoyment, and food preferences, then openness/resistance to trying food. It is not necessary that every member discuss coffee. The colour-vision note is a broader relation, not an identical mechanism to liking decaf or gamey meat.

Comparison: M01 `1165` contains nine masks from N086/N094, including V856; M04 places V856 under caffeine `1153`. M04 `1171, 1223, 1243` still provide eight, nine, and ten directly relevant flavour/experience masks from those same two notes. M01 `1337` and baseline `1183` include N002 as a third note; M04 `1282/1350` also preserve that exact three-note discovery. The higher exact-vector LCA is not evidence of a lost flavour/preference relationship.

### 1587 and 1439

At `1175`, V333/V334/N042's desire for hot tea joins V730/N080's getting out of bed for tea and a wee; `1208` adds the morning/order variant. `1587` adds V670/N072's Southerners having different ways of making sweet tea. Broad tea discovery, including an incidental comparison in a bread note, is defensible; hot and sweet tea need not be identical. M01 `1227` and baseline `1355` retain the four-vector/two-note core. Baseline `1439` instead adds N076's Tandori chicken “On fire” mask; that is not a better tea relation. M01 `1683` pairs V670 with N045's “America”/half-and-half complaint: regional drink conventions are a conceivable broad relation, but not clearly better than tea itself.

At `1439`, V412/N052 `["Rise", "grind"]` joins V351/N043 `["9am", "Fetching coffee", "stretching", "bowing"]`. The original N052 is exactly “Rise and grind coffee beans.” The note-level morning/coffee relation is defensible, but V412 alone drops the object and is ambiguous. Better explicit coffee-preparation masks from N052 already occur at `951`; no missing note discovery follows.

### 1529

`948, 1059, 1187, 1192` are a clear raw-milk relation between N006's slush and N051's “stack raw milk,” adding same-note variants. M01 `1159` and baseline `1166` have the exact five-vector/two-note branch.

`1075` joins V088/N012 `["Cheese Doodle"]` with V579/V580/N067 `["cheesecake"]`. These are cheese-named foods, but the original N012 is National Cheese Doodle Day trivia, not a cake/recipe note. `1475` adds V765/N081 `["gianguja", "craftchocolate"]`; `1529` joins this with raw milk. Food/drink treats are a possible broad relationship. A single dairy or dessert interpretation is not supported by every exact mask, and the chocolate addition should not acquire an assumed ingredient.

M01 `1085` and baseline `1121` reproduce the cheese-word pair. M01 `1471` additionally includes N083's gluten-free pie; this does not establish a lost specific relation in M04, given the already mixed Cheese Doodle/cheesecake/chocolate masks. The strong raw-milk child remains intact.

### 1153, 1097, 1169, and standalone raw leaves

- `1038` pairs V855/N094's “caffeine addicted heathens” with V270/N034's excessive caffeine today; `1153` adds V856/N094's decaf/caffeine contrast. This supports caffeine dependence/intake as a separate view of N094, alongside its preserved coffee-flavour route. M01 `1047` already has the two-note core.
- `1097`: aliased V355/V356/N045's half-and-half ruining coffee + V504/N060's coffee with raw cream. This is a concrete coffee-cream preference relation; M01 `1110` has the identical three vectors.
- `1026` pairs V035/N004's rave at a coffee shop with V295/N038's music playing in a coffee shop. `1042, 1169` add same-note variants, including “Baby Got Back.” Clear shared note discovery. M01 `1035/1051` and baseline `1051` already expose both notes through fewer masks; M04's four-mask completeness is not newly discovered notes.
- Leaf `892` = V357/N045's “America”/half-and-half complaint; N045 is already discoverable in `1097`. Leaf `871` = V296/N038's laughing “Baby Got Back” variant; N038 is already in `1169`. Leaf `0` = V034/N004 `["Weird", "#coffeechain"]`; N004 is also in `1169`. Leaf `99` = V283/V284/N036 `["Iced coffee", "in ice"]`; N036 has explicit iced-coffee masks in `1080`. None of these singleton inspection roots proves lost note discovery.
- Leaf `814` = V331/N041 `["#keto"]`. It carries only the dietary hashtag. Its upper placement is outside this batch; no placement verdict is made here.

### 1080

All 31 internal merges were inspected. The concrete structure is:

- `917 → 919 → 928 → 935` joins/expands explicit coffee/fetching coffee masks; `932` joins having had coffee; `937` combines them.
- `920` pairs plain coffee masks; `922` pairs coffeechain masks; `934` joins those; `943` joins with the other coffee-consumption branch. `947, 952, 954, 962` add iced coffee, asking for coffee, and breakfast coffee.
- `921 → 924 → 926 → 927 → 944` is a coffeechain-tag branch (including “Sipping”). `966` combines that with the preceding coffee branch; `984` adds fetching coffee as a ritual.
- `942` pairs grinding coffee beans with roasting one's own beans; `951` adds the “Rise” variant. This is a legitimate more-specific coffee-preparation descendant. `987` combines it with the broader coffee branch.
- `1009, 1011, 1015` add coffee in cool places and making coffee. `1017` adds V725/N079 `["🐶"]`; `1066` adds iced coffee served in ice.
- `988` pairs V860/N095's having coffee and needing another with V791/N086's “have you had your coffee”; `1080` joins it to the larger branch.

Judgment: a clear broad coffee discovery route with a useful preparation child. Some small children simply group generic mentions and do not imply a meaningful new subtopic. The bare dog emoji is not standalone evidence of coffee, but N079's original is “Is there coffee for me? 🐶☕️” and its explicit coffee masks are already present. It adds no new note and does not make the whole coffee group bad. Similarly, a hashtag-only note need not contain a substantive discussion of coffee beyond that chosen hashtag.

Comparison: M04 `1080`, M01 `1042`, and baseline `1024` are **exactly the same 32 vectors / 15 notes**. M01 `944/954` and baseline `948/957` also preserve the beans-preparation core. This is preserved discovery, not a M04-specific gain.

### 1462

`1224` pairs V238/N028 `["pancakes", "I", "added 2T cacao", "mix"]` with V354/N045 `["Half & half ≠ cream"]`. `1244` pairs V245/N029 `["2nd", "coffee"]` with V159/N023 `["My dinner today", "2 pieces of bread"]`. `1462` joins these pairs.

The originals confirm different actions: modifying pancake batter, objecting to half-and-half in coffee, announcing a second coffee, and listing dinner. Quantities/fractions occur, but the four masks do not describe one preparation, preference, meal, or ingredient relation. This is a weak four-note descendant. M01 `1245, 1267, 1418` gives the same two pairs and combined set, so compactness here is not evidence of quality. N045/N029 have clearer coffee routes already described; the scope does not justify forcing every mask into them.

### 1430

`1193` pairs V650/N071 `["basil", "breakfast burrito"]` with V581/N067 `["my", "Blueberry cheesecake"]`. `1311, 1318, 1351` add N096's Bolognaise recipe/serving count/dinner masks; `1430` adds V359/N046 `["chewy bagels"]`.

A broad connection across prepared dishes is real. A narrower common recipe, ingredient, meal time, or cooking process is not in these masks. Original N067 merely posts cheesecake; it supplies no recipe instructions. The first pair is therefore weak as a specific discovery and becomes broadly dish-related rather than more specific as pasta and bagels join. The word “basil” also has a concrete alternative in N096's V877 basil mask, but this report does not prescribe moving leaves or claim this must replace every broad dish connection.

M01 `1212` reproduces the initial burrito/cheesecake pair; no clearly better narrow all-four-note alternative was established by the comparator inspection.

### 1442

Observed and judged:

- `931 → 950 → 958 → 980 → 997 → 1007`: clear N015/N037 sourdough, preparing sourdough, and rosemary/cinnamon/brown-sugar sourdough variants. Seven masks, two notes.
- `994, 1008, 1021`: clear N037/N072 cranberry/rosemary bread variants across sourdough and Irish soda bread. `1012` pairs N072's usual currants with N037's cranberry sourdough: a defensible fruit-in-bread variation, not identical fruit. `1044` combines these; `1235` adds N072's out-of-season currants variant. These remain exactly two relevant notes.
- `1063` pairs V286/N037 `["bread"]` with V806/N089 `["Bread", "salt", "yeast", "mixing"]`; `1136` joins this with sourdough preparation. A valid broad bread-process connection.
- `1273` adds V893/N096 `["Spaghetti Bolognaise", "Mix all ingredients thoroughly.", "Simmer"]`. Mixing/preparing food is shared only at a broader level; it is not a bread-process example. `1296` adds N072's soda-bread recipe variation mask; `1315` joins the fruit-bread descendant.
- `1137` pairs V808/N089's salt/yeast separation before mixing with V664/N072's high-altitude soda-bread success/failure. `1144, 1149` add salt-placement variants; `1306, 1340` add altitude variants. These can usefully discover notes about constraints on making bread work, without claiming the two notes describe the same cause or technique.
- `1275` pairs V777/N083 `["easter matcha-cashew pie", "no refined sugar"]` with V671/N072's soda-bread variation/sweet-tea analogy. The originals do not supply a shared restriction: N083 explicitly says “No-baking,” gluten-free, vegan; N072 discusses altitude and fruit substitutions. A broad homemade-food/recipe-variation relation is possible, but no narrow shared preparation or dietary rule is established.
- `1381` joins that pair to the larger bread/pasta branch; `1420` adds the altitude/salt branch; `1442` adds the generic soda-bread recipe mask. These parents retain useful bread descendants even though no specifically bread-only interpretation covers every member.

Comparison: M01 `1001` and baseline `1003` have the exact seven-vector N015/N037 sourdough set. M01 `1027` and baseline `1037` already expose N037/N072 through four cranberry/rosemary masks; M04 `1235` has seven masks from those same two notes. This is not three newly discovered notes or a lost discovery in either comparator. M01 `1156, 1162, 1166` retains the N072/N089 process pair through fewer variants. M04 keeps those six masks together at `1340`, but the two-note connection was already available.

## Input-mask limits and comparison cautions

1. Fragment arrays are faithful to original byte spans; the limits above are semantic selection limits, not corrupt text.
2. Very small masks remove the needed relation: V725 `["🐶"]`, V282 `["ice"]`, V412 `["Rise", "grind"]`, V249 `["salad dressing"]`, V721 `["india"]`, V701 `["sexi yogo"]`. Original context can explain a note's relevance but does not make the missing words present in the exact mask.
3. Long masks can combine several distinct assertions: V119's eating/laziness/eggs/chocolate, V173's three red flags, and V671's bread/sweet-tea comparison. A match to one part does not establish that all clauses belong to one narrow relation.
4. Quantity/time fragments sometimes connect real behaviors (cooking durations, excessive intake), sometimes different behaviors (batch output versus intake, ambient temperature versus cooking). The distinction comes from the actual action and object, not the mere presence of numbers.
5. Exact-vector LCA growth was used to locate differences, never as a standalone loss metric. Specifically checked counterexamples include M01 `1617` versus M04 `1550`, coffee-flavour V856, the bread variants, coffee-shop music variants, and alias duplicates.
6. Weak local merges can coexist with good discovery of the same notes elsewhere, as N026/N096 at `1070` demonstrates. Conversely, an exact same-note set is only a useful substitute when the retained masks express the relevant relationship; generic corpus hashtags are not a universal substitute.
7. No inference run, code change, test/Cargo operation, commit, card mutation, or change outside this report was performed.

## Exact coverage registry

The following is coverage, not a proposed hierarchy cut. Each listed vector's entire fragment array and each listed internal merge's two children were inspected.

### Raw point 1767

14 canonical leaves; 14 exact vectors; 6 notes; 13 internal merges.

Canonical leaf → exact vector(s): 121 → V568; 125 → V017; 153 → V566; 162 → V015; 272 → V016; 274 → V314; 392 → V936; 411 → V556; 428 → V567; 446 → V018; 506 → V202; 729 → V399; 844 → V203; 860 → V404.

Internal merges inspected: 1387, 1395, 1438, 1454, 1528, 1577, 1591, 1609, 1611, 1690, 1701, 1721, 1767.

Notes: N002, N026, N040, N050, N065, N100.

### Raw point 1763

9 canonical leaves; 9 exact vectors; 4 notes; 8 internal merges.

Canonical leaf → exact vector(s): 213 → V762; 373 → V215; 508 → V249; 559 → V766; 619 → V763; 670 → V895; 696 → V201; 810 → V218; 905 → V217.

Internal merges inspected: 1410, 1417, 1541, 1559, 1630, 1695, 1717, 1763.

Notes: N026, N030, N081, N096.

### Raw point 1753

22 canonical leaves; 22 exact vectors; 13 notes; 21 internal merges.

Canonical leaf → exact vector(s): 4 → V673; 40 → V113; 81 → V115; 216 → V737; 226 → V098; 310 → V672; 372 → V804; 385 → V114; 520 → V488; 531 → V119; 534 → V823; 538 → V674; 568 → V173; 602 → V095; 649 → V800; 688 → V817; 705 → V816; 714 → V894; 719 → V682; 727 → V787; 790 → V802; 809 → V368.

Internal merges inspected: 1029, 1041, 1046, 1051, 1060, 1084, 1151, 1163, 1281, 1299, 1360, 1411, 1422, 1452, 1485, 1487, 1590, 1668, 1680, 1711, 1753.

Notes: N013, N016, N024, N047, N058, N073, N074, N080, N085, N088, N090, N091, N096.

### Raw point 1708

18 canonical leaves; 18 exact vectors; 6 notes; 17 internal merges.

Canonical leaf → exact vector(s): 38 → V080; 68 → V085; 171 → V312; 190 → V086; 220 → V701; 250 → V703; 321 → V722; 337 → V082; 417 → V315; 492 → V313; 528 → V522; 576 → V078; 630 → V700; 660 → V721; 697 → V081; 711 → V910; 776 → V079; 788 → V311.

Internal merges inspected: 1245, 1323, 1361, 1369, 1377, 1385, 1398, 1413, 1464, 1465, 1507, 1521, 1540, 1550, 1602, 1685, 1708.

Notes: N011, N040, N063, N076, N078, N098.

### Raw point 1634

11 canonical leaves; 11 exact vectors; 4 notes; 10 internal merges.

Canonical leaf → exact vector(s): 63 → V056; 65 → V053; 290 → V706; 304 → V707; 338 → V708; 438 → V751; 618 → V704; 653 → V536; 868 → V705; 879 → V054; 890 → V055.

Internal merges inspected: 972, 993, 995, 1065, 1098, 1127, 1195, 1255, 1433, 1634.

Notes: N007, N063, N076, N080.

### Raw point 814

1 canonical leaves; 1 exact vectors; 1 notes; 0 internal merges.

Canonical leaf → exact vector(s): 814 → V331.

Internal merges inspected: none.

Notes: N041.

### Raw point 1346

2 canonical leaves; 3 exact vectors; 2 notes; 1 internal merges.

Canonical leaf → exact vector(s): 106 → V282; 544 → V183,V181.

Internal merges inspected: 1346.

Notes: N024, N036.

### Raw point 1666

17 canonical leaves; 17 exact vectors; 5 notes; 16 internal merges.

Canonical leaf → exact vector(s): 83 → V854; 103 → V858; 160 → V497; 180 → V794; 186 → V498; 232 → V795; 245 → V019; 295 → V853; 545 → V852; 589 → V796; 593 → V502; 596 → V857; 654 → V020; 748 → V266; 781 → V850; 825 → V792; 849 → V851.

Internal merges inspected: 1006, 1013, 1056, 1067, 1077, 1108, 1171, 1223, 1243, 1282, 1350, 1474, 1501, 1627, 1649, 1666.

Notes: N002, N033, N059, N086, N094.

### Raw point 1587

4 canonical leaves; 5 exact vectors; 3 notes; 3 internal merges.

Canonical leaf → exact vector(s): 222 → V334,V333; 370 → V670; 608 → V731; 898 → V730.

Internal merges inspected: 1175, 1208, 1587.

Notes: N042, N072, N080.

### Raw point 1439

2 canonical leaves; 2 exact vectors; 2 notes; 1 internal merges.

Canonical leaf → exact vector(s): 445 → V412; 461 → V351.

Internal merges inspected: 1439.

Notes: N043, N052.

### Raw point 1529

8 canonical leaves; 9 exact vectors; 5 notes; 7 internal merges.

Canonical leaf → exact vector(s): 212 → V088; 223 → V579,V580; 285 → V765; 314 → V044; 715 → V408; 739 → V407; 782 → V046; 811 → V045.

Internal merges inspected: 948, 1059, 1075, 1187, 1192, 1475, 1529.

Notes: N006, N012, N051, N067, N081.

### Raw point 892

1 canonical leaves; 1 exact vectors; 1 notes; 0 internal merges.

Canonical leaf → exact vector(s): 892 → V357.

Internal merges inspected: none.

Notes: N045.

### Raw point 871

1 canonical leaves; 1 exact vectors; 1 notes; 0 internal merges.

Canonical leaf → exact vector(s): 871 → V296.

Internal merges inspected: none.

Notes: N038.

### Raw point 1153

3 canonical leaves; 3 exact vectors; 2 notes; 2 internal merges.

Canonical leaf → exact vector(s): 444 → V855; 581 → V270; 895 → V856.

Internal merges inspected: 1038, 1153.

Notes: N034, N094.

### Raw point 1097

2 canonical leaves; 3 exact vectors; 2 notes; 1 internal merges.

Canonical leaf → exact vector(s): 111 → V356,V355; 296 → V504.

Internal merges inspected: 1097.

Notes: N045, N060.

### Raw point 1169

4 canonical leaves; 4 exact vectors; 2 notes; 3 internal merges.

Canonical leaf → exact vector(s): 142 → V035; 755 → V036; 796 → V295; 894 → V294.

Internal merges inspected: 1026, 1042, 1169.

Notes: N004, N038.

### Raw point 0

1 canonical leaves; 1 exact vectors; 1 notes; 0 internal merges.

Canonical leaf → exact vector(s): 0 → V034.

Internal merges inspected: none.

Notes: N004.

### Raw point 99

1 canonical leaves; 2 exact vectors; 1 notes; 0 internal merges.

Canonical leaf → exact vector(s): 99 → V283,V284.

Internal merges inspected: none.

Notes: N036.

### Raw point 1080

32 canonical leaves; 32 exact vectors; 15 notes; 31 internal merges.

Canonical leaf → exact vector(s): 10 → V790; 14 → V278; 21 → V725; 58 → V281; 127 → V653; 145 → V726; 166 → V797; 167 → V381; 169 → V727; 176 → V187; 185 → V410; 233 → V724; 259 → V860; 271 → V411; 330 → V656; 365 → V297; 413 → V865; 512 → V342; 526 → V503; 550 → V276; 557 → V279; 612 → V791; 617 → V126; 621 → V243; 632 → V244; 644 → V343; 669 → V859; 673 → V043; 758 → V285; 818 → V280; 851 → V793; 897 → V277.

Internal merges inspected: 917, 919, 920, 921, 922, 924, 926, 927, 928, 932, 934, 935, 937, 942, 943, 944, 947, 951, 952, 954, 962, 966, 984, 987, 988, 1009, 1011, 1015, 1017, 1066, 1080.

Notes: N005, N017, N024, N029, N035, N036, N038, N043, N048, N052, N060, N071, N079, N086, N095.

### Raw point 1462

4 canonical leaves; 4 exact vectors; 4 notes; 3 internal merges.

Canonical leaf → exact vector(s): 120 → V245; 257 → V238; 280 → V354; 631 → V159.

Internal merges inspected: 1224, 1244, 1462.

Notes: N023, N028, N029, N045.

### Raw point 1430

6 canonical leaves; 6 exact vectors; 4 notes; 5 internal merges.

Canonical leaf → exact vector(s): 179 → V650; 454 → V581; 516 → V867; 622 → V359; 769 → V868; 824 → V870.

Internal merges inspected: 1193, 1311, 1318, 1351, 1430.

Notes: N046, N067, N071, N096.

### Raw point 1442

27 canonical leaves; 27 exact vectors; 6 notes; 26 internal merges.

Canonical leaf → exact vector(s): 36 → V107; 94 → V109; 112 → V808; 139 → V287; 146 → V664; 161 → V292; 177 → V293; 192 → V777; 217 → V669; 240 → V665; 256 → V660; 339 → V288; 351 → V668; 354 → V807; 480 → V667; 567 → V809; 628 → V291; 634 → V893; 641 → V290; 646 → V289; 652 → V108; 687 → V658; 694 → V662; 742 → V671; 759 → V666; 760 → V286; 837 → V806.

Internal merges inspected: 931, 950, 958, 980, 994, 997, 1007, 1008, 1012, 1021, 1044, 1063, 1136, 1137, 1144, 1149, 1235, 1273, 1275, 1296, 1306, 1315, 1340, 1381, 1420, 1442.

Notes: N015, N037, N072, N083, N089, N096.


