# TRUE03 — Expected relationships before scoring

The main agent proposed 24 actual-title pairs and wrote expectations before any TRUE03 inference. A fresh independent reviewer, `/root/true03_blind_semantics`, received the exact title pairs but not the main agent's expectations, original masks or TRUE scores.

For the 22 retained pairs, both reviewers agreed. The exact titles, group IDs and main rationale remain in [the fixture](true03-fixture.json), resolved against the saved source titles. There were no title rewrites.

| Pair | A contains B? | B contains A? |
|---|---|---|
| P01 | Yes | No |
| P02 | Yes | No |
| P03 | Yes | No |
| P04 | No | No |
| P05 | No | No |
| P06 | Yes | Yes |
| P07 | Yes | No |
| P08 | Yes | No |
| P09 | Yes | No |
| P10 | Yes | No |
| P11 | Yes | No |
| P12 | Yes | No |
| P13 | No | No |
| P14 | Yes | No |
| P15 | No | No |
| P17 | Yes | No |
| P18 | Yes | No |
| P19 | Yes | No |
| P20 | No | No |
| P21 | No | No |
| P22 | Yes | No |
| P23 | Yes | No |

## Set aside before inference

**P16 — Meat Eating / Red meat.** The main agent expected neither to contain the other. The reviewer judged the reverse No but the forward direction ambiguous: Meat Eating might be a broad dietary category that includes kinds of meat, or the practice of eating, which does not encompass every red-meat subject. This ambiguity is material to the requested decision, so neither direction is scored in this pilot.

**P24 — Art / Music in Coffee Shops.** The main agent expected Art to contain Music in Coffee Shops, not the reverse. The reviewer judged the reverse No but the forward direction ambiguous between Art broadly including music and the common visual-art reading. The main agent accepted setting this pair aside instead of treating one reading as a definitive model test. This does not reject either generated title.

The removed IDs are intentionally not reassigned. These exclusions occurred before any TRUE03 model call, not after seeing mistakes. They narrow what the pilot establishes; they are not evidence that TRUE can resolve ambiguous categories.

P06 uses two different source groups with the same title, Coffee. This is only an identical-description control; it does not demonstrate recognition of differently worded equivalents or equality of those groups' note memberships.
