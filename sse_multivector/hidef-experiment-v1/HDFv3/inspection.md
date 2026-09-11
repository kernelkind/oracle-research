# HDFv3 — inspection evidence

All new group IDs below refer to **HDFv3 seed 123**. Old IDs refer to **HDFv2 original seed 123**, which exactly replayed HDFv1. Descriptions explain the evidence; no subject titles were generated or inserted into the TUI. These are analyst judgments, not user approvals.

The user requested a chat handoff rather than a TUI. [comparison.json](./comparison.json) preserves exact memberships, counterpart searches, raw occurrences, persistent-family support, ancestors, aliases, and source hashes. Complete original notes remain in the unchanged `../../real-note-fine-segmentation-v1/reviewed-input.json` source artifact.

## A useful added child

The actual path is 916 → 922 → 930 → **951 → 1498**. Group 951 is the unchanged 15-note coffee group. Group 1498 contains only:

- V245 · N029: ⟦2nd⟧ ⟦coffee⟧
- V860 · N095: ⟦Just had⟧ ⟦coffee⟧ ⟦I need another⟧

The full N029 is a short hashtag/image post explicitly saying “2nd #coffee.” N095 says, “Just had a coffee, but I need another one...” before its Sunday greeting. Both support another serving of coffee. This is a plausible narrowing of coffee, rather than merely two random coffee notes. The pair has nine supporting resolutions and survives in both repeats as 1476 and 1490 respectively.

This does not approve the complete path. Group 930 also contains gin/cherry-beer, tea, soda-bread, and isolated dog/sleep-emoji masks. Its broader subject remains uncertain. A good lower transition does not certify its ancestors.

The same coffee parent also contains **1605**:

- V354 · N045: ⟦Half & half ≠ cream⟧
- V285 · N036: ⟦Iced coffee⟧ ⟦served in ice⟧

N045 criticizes half-and-half in coffee; N036 describes iced coffee served in ice. These are legitimately coffee-related. Their pairing does not establish a more specific shared choice than coffee itself. It has seven supporting resolutions, illustrating why persistence alone is not semantic validation.

## The Satoshi pair reaches clustering, not the saved hierarchy

The two target masks are V189/N024 ⟦satoshi⟧ and V433/N054 ⟦Satoshis⟧. They are a Bitcoin-related connection, not an assertion that the creator's name and the currency unit are identical concepts.

| Seed | Added resolutions containing exactly the pair | Candidate connections | Retained together? |
| --- | --- | --- | --- |
| 123 | 60.715, 66.7704, 86.037, 88.8072 | Two separate connected pairs | No |
| 124 | 62.6698, 64.6876, 80.7532 | A three-candidate path | No |
| 125 | 56.9863, 64.6876, 75.7939, 100.809 | A three-candidate path and an isolated candidate | No |

HiDeF links sufficiently similar candidate memberships at nearby resolutions. None of these components reaches the unchanged persistence requirement of five. The clean pair has no compatible larger candidate neighbors under the strict Jaccard >0.75 rule. No retained family includes its raw candidates.

The old mixed Satoshi group remains exactly, now **1047**. Its masks include Sorrento, restaurant places, and the baby Sophia. New retained **1532** contains:

- V015 · N002: ⟦Sorrento's Savory Stroll⟧ ⟦easy⟧
- V189 · N024: ⟦satoshi⟧

Group **1550** instead pairs the Satoshi mask with V021/N002 ⟦Sorrento's cuisine⟧ ⟦🇮🇹⟧. The source is an Italian food-tour advertisement, not Bitcoin. The other target vector, V433, remains under a broader Bitcoin group **969**, but V189 is absent there. In all three runs, the two target vectors' only common ancestor is the artificial root.

This establishes stage-specific progress and a remaining failure. It does not justify changing persistence solely until this pair passes.

## Other preselected baseline checks

| Earlier evidence | Extended result | Interpretation |
| --- | --- | --- |
| 951: coffee | Exact membership remains 951; new children include 1498 and 1605 | Useful and questionable added subdivisions coexist. |
| 965 → 1037: equipment | Exact memberships remain 965 → 1033 | The broad parent still includes the isolated “king's butler” mask. More frying-pan/stove/smoker subsets do not certify that parent. |
| 976: eggs | Exact membership remains 976; new 1028 → 1071 returns six notes at both levels | Eggs is coherent, but this transition does not narrow returned notes. |
| 1027: wine/gin | Exact membership remains 1020 | New children 1354 and 1355 retain the same three notes with alternative wild-rose-wine masks. No new useful distinction established. |
| 1023: exercise | New 1031 changes exact masks while remaining exercise-related | It drops overlapping mental-rust masks and adds a long-term workout-plan mask. Not a demonstrated regression. Its lower 1117 → 1151/1152 retains the same four notes. |
| 977: tomato-dominant mixture | Old mixed membership remains; new 1058 is a cleaner five-note tomato group | 1058 contains tomato tortillas, purée/chopped tomatoes in Bolognaise, roasting tomatoes for salsa, buying tomatoes, and fried homegrown tomatoes. Useful local grouping. Child 1193 is smaller without an obvious further subject distinction. |
| 994 → 1060: number association | Number-associated material still has retained groups | Shared uses of “three” and nearby vocabulary do not establish useful narrowing among travel stops, storms, durations, and Apocalypse. No demonstrated repair. |
| 919 → 939 → 983: food/storage mixture | New 996 is a more coherent three-note appliance/use group | It removes Nostr/zap, grab bars, and selling-salsa material from the old mixture, retaining induction-hob, vacuum-sealer, and vacuum-sealed-beet masks. Its ancestors 939/944 remain mixed, and 996 → 1049 returns exactly the same three notes. |

Some retained memberships are consensus results that never occurred as one exact raw group. That is permitted by the unchanged method. The comparison records their contributing families rather than treating zero exact occurrences as missing support.

## Four new groups selected mechanically

These were selected using the frozen hash rule in [PLAN.md](./PLAN.md): two new groups with 2–4 notes, two with 5–14 notes. No newly added primary group contains 15 or more notes, so that stratum is empty. Selection did not depend on semantic quality.

**1640 · two notes**

- V058 · N008: ⟦Another small win⟧ ⟦cooked⟧ ⟦proper food tonight⟧
- V302 · N039: ⟦Next rounds of storms look like⟧ ⟦hit just in time for grilling out dinner⟧

Both involve preparing dinner. The complete first note also discusses chemotherapy; the second discusses weather disrupting a parade, grilling, and fireworks. Those additional meanings do not invalidate their cooking connection. Its parent 1080 adds leftover BBQ pizza, brisket on a smoker, and broader storm/cooking masks. A related local group, but an especially fine shared refinement is not established.

**1555 · two notes**

- V745 · N080: ⟦audio book⟧ ⟦drivel⟧ ⟦I gave up⟧ ⟦started⟧ ⟦new murder mystery⟧
- V439 · N054: ⟦Literature⟧

The masks share a reading/literature connection. Parent 1319 also contains V340/N043 ⟦first minutes written⟧, so removing that writing mask is defensible. However, N054 supplies only a Literature hashtag among unrelated island-life material. That weakens the note-discovery example even though the selected word is related; the grouping experiment did not change extraction. Ancestor 999 combines philosophy, music, education, knowledge, and talking, without an established useful parent description.

**1064 · six notes**

Its masks cover a baby and family, a mother buying a child's lunch, family/community advice, a mother telling a child to eat vegetables, dadlife, and older Airbnb guests. The older-guest mask is:

- V830 · N092: ⟦We get quite a few bnb guests⟧ ⟦older⟧

The full note discusses bathroom grab bars to prevent guests falling. It does not identify those guests as family. Thus “family” does not cover the parent as a whole. Child 1129 removes older guests and broader health advice and retains coherent family-related masks; that useful child does not repair the parent. Another child, 1614, pairs family/community advice with the older guests, which is not an established family refinement.

**1028 · six notes**

All masks concern eggs: an omelette, using up eggs, century-egg preservation, cooking eggs, a broken egg, boiled eggs as a snack, and egg yolk in coffee. The broad connection is valid. Parent 976 has seven egg notes; child 1071 removes two masks but returns the identical six notes. Neither fewer masks nor fewer examples automatically creates a useful new subject choice.

## Review limits

The main and independent reviewer inspected the frozen cases and the four new sampled groups, checking original notes where context mattered. Additional targeted checks include the second-coffee pair and the appliance/tomato groups. They did not judge every new group. Seed comparisons establish membership recurrence, not universal correctness. All concerns and positives leave masks, labels, memberships, and parameters unchanged.
