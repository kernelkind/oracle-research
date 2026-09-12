# TRUE02 — Review before model scores

The main agent proposed the fixture. A separate reviewer (`released_large_hierarchy`) read only `true02-fixture.json` and `TRUE02-PLAN.md` for this audit, not model outputs. All judgments below were returned before TRUE02 inference. The reviewer agreed with all 75 unordered pairs; no answer-key change or exclusion was proposed.

A newly spawned clean-context reviewer first supplied general design pitfalls but finished before receiving the fixture. The tool then refused to resume or replace that thread because of its thread limit. The existing research reviewer above performed the actual complete fixture audit. Its earlier research context was retained; it was blind to TRUE02 scores, not a newly isolated generation call. No subject or mask generation was performed by that reviewer.

Fixture SHA256: `a514757d32adc0c31f859d0d8a912870cec4c7296ee07d231d9edc7608098e21`.

## Every pair

IDs refer to the complete category strings in [the fixture](true02-fixture.json). For row i–j: `>` means i contains j only; `<` means j contains i only; `=` means both directions; `neither` means neither direction. These are topical-scope judgments, not physical type identity or mere co-occurrence.

| Pair | Food F | Software S | Economics E | Politics P | Interpersonal R |
|---|---|---|---|---|---|
| 1–2 | > | > | > | > | > |
| 1–3 | neither | > | neither | > | neither |
| 1–4 | > | > | > | > | neither |
| 1–5 | > | > | > | > | neither |
| 1–6 | > | > | neither | > | > |
| 2–3 | neither | neither | neither | neither | < |
| 2–4 | neither | > | neither | > | neither |
| 2–5 | neither | > | neither | > | neither |
| 2–6 | neither | neither | neither | neither | neither |
| 3–4 | > | > | > | > | > |
| 3–5 | > | > | > | > | > |
| 3–6 | neither | neither | > | neither | neither |
| 4–5 | = | = | = | = | = |
| 4–6 | neither | neither | neither | neither | neither |
| 5–6 | neither | neither | neither | neither | neither |

There are 35 strict-containment pairs, five equivalent pairs, and 35 neither-direction pairs: **45 positive and 105 negative directional judgments**.

## Why overlapping or related categories do not necessarily contain each other

The first example belongs under the first category without requiring the second; the second example establishes the reverse. Grouped IDs cover both equivalent descriptions.

| Pair(s) | Counterexamples in the two directions |
|---|---|
| F1/F3 | Wheat bread; gluten-free rice. |
| F2/F3 | Wheat sourdough; gluten-free rice. |
| F2/F4, F2/F5 | Wheat sourdough; gluten-free bread made without sourdough fermentation. |
| F2/F6 | Sourdough bread storage or sandwich uses; baking non-sourdough bread. |
| F3/F6 | Gluten-free rice; baking wheat bread. |
| F4/F6, F5/F6 | Nutritional properties or storage of gluten-free bread; baking wheat bread. |
| S2/S3 | Testing a web page's layout; security testing desktop software. |
| S2/S6 | Manual web-application testing; automated desktop-application testing. |
| S3/S6 | Manual security testing; automated non-security functional testing. |
| S4/S6, S5/S6 | Manual web security testing; automated desktop functional testing. |
| E1/E3 | Ordinary income taxes; habitat-protection regulation. |
| E1/E6 | Ordinary income taxes; emissions-allowance market design. |
| E2/E3 | Corporate-profit tax rates; habitat-protection regulation. |
| E2/E4, E2/E5 | Taxation based on corporate profits; taxation based on emissions independently of profit. |
| E2/E6 | Corporate-profit tax accounting; emissions-allowance trading rules. |
| E4/E6, E5/E6 | A carbon-emissions levy; trading allowances under an emissions cap. |
| P2/P3 | An offline donor dinner; online political advocacy without fundraising. |
| P2/P6 | A donor dinner without canvassing; door-to-door voter outreach without fundraising. |
| P3/P6 | Political social-media advertising; offline door-to-door canvassing. |
| P4/P6, P5/P6 | An online donation campaign without canvassing; offline voter outreach without fundraising. |
| R1/R3 | Friendship between people who do not work together; a purely professional manager–employee relationship. |
| R1/R4, R1/R5 | Friendship without workplace mentoring; a professional mentor–mentee relationship without friendship. |
| R2/R4, R2/R5 | Coworker friends who do not mentor one another; workplace mentoring between people who are not friends. |
| R2/R6 | Nearby coworker friends; distant friends who are not coworkers. |
| R3/R6 | A local professional workplace relationship; distant friends with no shared workplace. |
| R4/R6, R5/R6 | Local workplace mentoring without friendship; distant friends with no workplace mentoring relationship. |

These establish noncontainment, not disjointness. Some categories intersect; others principally concern related activities or instruments.

## Boundaries checked explicitly

- Bread contains bread baking topically. Baking does not contain all discussion of a bread variety: storage, nutrition, and consumption extend beyond baking.
- Political campaigning contains election fundraising as an activity. Online campaigning and fundraising intersect, but neither contains the other.
- Workplace relationships contain workplace mentoring. Mentoring need not be friendship, and coworker friendship need not involve mentoring.
- The five equivalences are ordinary paraphrases at the intended category granularity, not assertions of identity under every conceivable specialized interpretation.
