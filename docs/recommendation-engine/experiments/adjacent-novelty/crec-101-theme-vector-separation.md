# CREC-101: Theme-Vector Separation

## Question

Do the frozen Oracle document vectors preserve the broad themes that felt
repetitive in the valid `140`-note Phase 4 prefix?

This was a necessary-condition test. It did not test an exposure formula,
adjacent probes, personalization, or recommendation quality.

## Method

- The exact Phase 4 presentations `1–140` were shuffled into a text-only
  packet with opaque IDs.
- Two independent labelers assigned content-only theme labels. They agreed on
  `138/140` complete label sets.
- The raw label files were sealed before this diagnostic read Oracle vectors
  or computed similarity scores.
- Bitcoin and Monero were derived into one `cryptocurrency` analysis family.
  This pre-score correction prevented their heavily overlapping raw labels
  from counting as two independent themes.
- A pair of families counted as distinct only when each had at least eight
  notes not shared with the other under both label sets.
- For every qualifying family, stored document-vector cosine ranked same-family
  notes against outside-family notes. Each result was compared with `10,000`
  deterministic whole-label-set permutations.

The original sealed label hashes and the pre-score correction chronology are
preserved in the run artifacts and CREC-101.

## Result

The fixed decision rule yielded `ProceedToExposureReplay`.

| Label set | Macro AUROC | Permutation null 95th percentile |
| --- | ---: | ---: |
| A | `0.9249` | `0.5330` |
| B | `0.9202` | `0.5345` |

Nostr, cryptocurrency, and LLM/AI qualified as mutually distinct families and
were individually above their permutation null under both label sets:

| Family | A AUROC | B AUROC |
| --- | ---: | ---: |
| Nostr | `0.8837` | `0.8837` |
| Cryptocurrency | `0.9420` | `0.9340` |
| LLM/AI | `0.9490` | `0.9430` |

Every reported permutation p-value was `0.0001`, the minimum resolution of
`10,000` permutations. The normalized exact-content sensitivity pass removed
no notes and therefore produced the same decision.

## Meaning

The current Oracle vectors contain strong broad-theme structure at cosine
values well below the close-vector thresholds used by v1. A temporary exposure
mechanism based on these vectors is therefore plausible enough to test.

This does **not** show that a particular exposure accumulation, decay,
qualification, or adjacent-probe rule will improve the feed. That is the next
small experiment.

## Artifacts

The auditable local run is:

`damus_snapshot/runs/crec-101-theme-vector-separation-v1`

Its canonical input representation remains unchanged. The run contains the
blind packet, sealed raw labels, hashes, exact configs, and deterministic JSON
and Markdown reports.
