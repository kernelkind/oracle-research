# Sol low versus medium

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Test the unchanged ASv6.13 prompt on the same six development notes at low and medium reasoning effort. Each note gets three fresh calls per setting: 36 calls. Trial 1 completed sequentially. The user then approved up to 12 concurrent calls for the remaining 24, each with its own output directory; see the amendment (`./parallel-amendment.json`). Source strings, prompt and review criteria are unchanged.

The [predeclared comparison](./proposal.json) asks whether medium repeatedly fixes missing subject context without dropping meanings or introducing other errors. Review every output against the complete source note with effort identities hidden until judgments are saved.

The comparison is complete. Both settings produced 8/18 fully accepted outputs. Medium met none of the three targeted context-improvement conditions and misattributed the insurance analysis in two trials. Do not promote it from this result.

[Full notes, outputs and analysis](./results.md) · Judgments (`./review.json`) · [Decision](./assessment.json) · Integrity checks (`./verification.json`).

The remaining 24 calls finished in 2 minutes 32 seconds at up to 12 concurrent calls. All 36 raw outputs, separate threads/workdirs, unchanged sources/prompts and no-tool executions were verified. No process remains.

ASv6.8 and the original development/final validation requirements remain unchanged. No final-validation input was used. This was a diagnostic comparison, not a permanent migration or a passing extractor.

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
