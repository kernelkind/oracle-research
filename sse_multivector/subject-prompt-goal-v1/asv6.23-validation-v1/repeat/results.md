# ASv6.23 repeatability check

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../../docs/experiments/README.md#reading-the-research-records).

ASv6.23 passes the fixed development gates. The next step is the approved final test, with no prompt change.

| Evidence | Fully accepted subject lists | Accepted subjects |
| --- | ---: | ---: |
| Original 28-note pass | 27 / 28 | 267 / 268 |
| 12 new repeat calls | 11 / 12 | 183 / 186 |
| All outputs for the eight fixed repeated notes | 25 / 26 | 446 / 449 |

The last row includes the original outputs and all four existing outputs each for the hiring and CEO notes. They were not generated again or selectively discarded. Six notes have three independent outputs; those two have four.

## What remains uncertain

One new insurance output says:

> The described insurance, lending, infrastructure, gig-platform, and underwriting dynamics collectively reshape risk transfer across the economy.

Two more items use the same wording for credit availability and operational efficiencies. The subject names the relevant domains, but “the described … dynamics” may still need the missing description. These three items remain unresolved, not proven failures or accepted outputs. The other two outputs for this note name the capacity constraints and associated changes. This issue did not recur in two outputs.

The earlier snow interpretation also remains unresolved. It is unchanged by this repeat test.

The independent reviewer additionally questioned whether an author's expectation of an “editor or owner” could yield separate subjects for the two roles. The final review accepts these under the existing permission for separate supported interpretations. Neither output claims that either person actually was Jewish. The disagreement is preserved in the review (`./review.json`).

## What was checked

All 186 new subjects and whole-note coverage were reviewed against complete source notes. Auxiliary `context` fields were hidden during semantic review and never used to rescue an incomplete subject. Raw subjects were not edited.

All 12 calls used Astra low, the exact ASv6.23 prompt and schema, fresh isolated contexts, and no tools. All succeeded on their first attempt. No experiment units remain active. Minimum sampled available memory was 105.29 GiB; memory pressure stayed zero. Four calls logged nonfatal shell-snapshot startup diagnostics. Technical verification (`./technical-verification.json`).

This is an operational development pass, not evidence that arbitrary corpus extraction is solved. The reserved final test has not yet run.

Full source notes and outputs (`./full-outputs.md`) · Decisions (`./review.json`) · Counts and gate assessment (`./assessment.json`)

See conversion gaps (`03bd9e45:docs/experiments/publication-gaps.csv`) for `collection:tracked-subject-prompt-goal-v1`.
