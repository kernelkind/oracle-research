# TRUE04 — Semantic reference before score inspection

The [reference](true04-reference.json) was frozen at **2026-09-14 20:31:02 UTC**, after the offline run started but before any TRUE04 scores were inspected. SHA256: `ac461f98b06e1758d49b11f944a9fbfc5d6f118e178a49a3ae2fcc69cb3d4ae7`.

It contains **120 clear containment nominations** (75 distinct ordered title-string pairs), **42 ambiguous nominations**, and the 44 previously judged TRUE03 directions. Every TRUE03 positive is included among the clear nominations; none of its negatives conflicts with them. The clear nominations have no missing transitive implications among the supplied categories.

These are not 120 independent concepts: 74 directions have one of the two Food groups as parent. Report that broad-parent stratum separately from the 46 remaining directions. Unlisted pairs have no assigned expected answer.

## How it was produced

- `/root/true04_reference_a_clean` considered every other title as parent for children 0–30, producing [55 clear and 21 ambiguous nominations](true04-reference-a.json).
- `/root/true04_reference_b` considered every other title as parent for children 31–60, producing [66 clear and 20 ambiguous nominations](true04-reference-b.json).
- Both worked from exact titles and IDs, without TRUE predictions or the main agent's expectations. The [title-only list](true04-titles-only.json) preserves source order. No original notes or masks were used to disambiguate titles.

An earlier `/root/true04_reference_a` read the wrong JSON level and exposed source provenance to itself. It reported this, was stopped without producing judgments, and was replaced by the clean-context reviewer above. No output from the discarded attempt contributes to the reference.

The main agent read both completed references before inspecting scores and made three explicit changes:

1. **Art → Music in Coffee Shops:** clear to ambiguous. Broad arts versus visual-art scope had already been disputed before TRUE03; that ambiguity should not disappear merely because another reviewer chose one reading.
2. **Human Diet and Eating Behavior → Breakfast meals:** clear to ambiguous. A meal category can concern dishes or preparation rather than eating behavior, matching the caution applied to other meal categories.
3. **Communication → Grow Nostr Campaign:** ambiguous to clear. Under the same broad communication-platform reading already used to admit Communication → Nostr and Nostr → Grow Nostr Campaign, the campaign is also a communication topic.

The raw reviewer files are retained unchanged. These expert judgments remain revisable; they are not a claim that every other organization is wrong. Any later revision must remain visible rather than rewrite the pre-score reference.
