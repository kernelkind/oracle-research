# Subject-prompt goal

Continue from ASv6.11. The assistant now makes routine semantic judgments and can revise/test the subject prompt independently. The latest agreed requirements, Sol low, isolated runner and earlier evidence remain unchanged.

The [validation plan](./plan.json) was recorded before new generation. It fixes 28 development notes, eight repeated difficult notes, and a final test of 60 previously unused notes with 12 repeated notes. Passing requires at least 54 of the 60 final notes to have no identified error or unresolved judgment, at least 95% of subjects accepted, and no recurring failure under the plan's exact definitions. These are pilot acceptance limits, not a population accuracy estimate.

Current state: the goal is active and no prompt has passed. All 352 isolated calls have been reviewed and verified; no generation unit is running. The latest 24-call comparison tested ASv6.20, which removed two relationship warnings from ASv6.13. It stopped at its predeclared futility check: the hiring and CEO notes still had missing-context errors in both outputs under both versions. ASv6.20 is not promoted. The latest full-development results remain ASv6.13 20/28 and ASv6.19 22/28 clean notes; neither passed. ASv6.8 remains the frozen default, and no final-validation calls have been made.

The original plan remains byte-identical as predeclared evidence. Its self-imposed revision, call and final-attempt caps, and the historical verification reports' permission-blocking conclusions, are superseded by the revised goal. They are not current authorization limits. The semantic requirements, source data, validation criteria and resource safeguards remain fixed. Current operational authority is recorded in [status.json](./status.json).

The approved iteration-policy revision requires each comparison to state its keep/reject/unresolved evidence and bounded confirmation plan before generation. Before another prompt revision, assess cumulative improvement against the earlier evidence-backed baseline; stop a line of tweaks that mostly exchanges errors and seek a materially different, evidence-backed hypothesis within scope. Diagnostic learning, review corrections and documentation are not extraction improvements. Hide prompt identities during comparative review where practical and record judgments before revealing the versions; earlier reviews are not retrospectively described as blinded. The policy revision did not change the fixed validation criteria or itself resume the goal; the subsequent goal continuation resumed the work.

ASv6.12 incorrectly turned fee-priority values into counts in all three trials. Its publication-label problem occurred in two of three trials. ASv6.13 removed the targeted publication label in its first run, but the numeric error remained and commentary about truncated text returned in all three trials. Later revisions stopped inventing counts, but still produced items without their source context. The financial diagnostic also exposed incorrect or unresolved source attribution. These are difficult-case diagnostics, not estimates of corpus-wide accuracy.

ASv6.17 handled the clipped CEO passage correctly in all three trials. It omitted the unfinished word and included CEO context in the later subjects. Two failures still recurred in all three trials:

- Fee-priority entries such as “For Bitcoin block 923432, high priority is paired with 3” omit the fee/mempool context that another item supplies.
- The financial report's “Sector: Insurance | Confidence: 94%” becomes a subject about the report's classification rather than its content.

One financial trial also explicitly assigned the two-model analysis to CIAB, the source of the earlier survey. Another left that source ambiguous. These are difficult-case results, not a corpus-wide error rate. Broad, overlapping and duplicate subjects were not counted as errors.

The ASv6.14–17 candidates used the same three diagnostic notes, each generated three times. A clean output means every subject was accepted and no missing meaning was identified.

| Prompt | Clean outputs out of 9 |
| --- | ---: |
| ASv6.14 | 1 |
| ASv6.15 | 0 |
| ASv6.16 | 0 |
| ASv6.17 | 3 |

ASv6.17 was the strongest of these focused results, but those diagnostics alone left its broader performance unmeasured. The earlier audited full runs gave ASv6.13 24 clean notes and ASv6.12 23; accepted subjects were 257/269 and 255/264 respectively. Both failed the fixed criteria. Those historical results remain preserved separately from the fresh comparison below.

The [review audit](./semantic-review-audit-v1.json) corrects four judgments that treated plausible implications too strictly. It separately records unresolved slang and non-English interpretation as reviewer uncertainty, not established extractor failures. These corrections do not make either prompt pass.

The [second review audit](./semantic-review-audit-v2.json) distinguishes known D08 coverage from unresolved extra literal-flight subjects and corrects two overly strict rejections of supported possibilities in the metadata comparison. Its adjusted ASv6.17 subject count is 185/227 rather than 183/227; clean-output counts and the comparison's conclusion are unchanged. Original reviews and outputs remain intact.

The [completed full-development comparison](./representative-comparison-v1/README.md) used unchanged ASv6.13 and ASv6.17 on the same 28 notes, with one fresh isolated output each. ASv6.13 had 21/28 clean notes and 254/271 accepted subjects; ASv6.17 had 19/28 and 147/172. ASv6.17 improved four notes but regressed on six, notably presentation metadata and URL-only names. It did not establish a best overall prompt or the causal effect of individual instructions. The final notes stay unused.

The [completed metadata comparison](./metadata-sentence-comparison-v1/README.md) restored only ASv6.13's content-versus-presentation sentence in ASv6.17. Three fresh trials of both versions on nine fixed notes found fewer metadata-error outputs on three of four targets. URL naming and numerical context remained problematic.

The [12-call confirmation](./metadata-confirmation-v1/README.md) repeated the insurance and CEO notes with both prompts unchanged. Metadata improvement persisted, but ASv6.18 explicitly misattributed the insurance interpretation in two of three additional outputs. Both prompts again showed CEO-context or missing-text problems. Keep the metadata finding as evidence, not ASv6.18 as a validated replacement.

The [completed ASv6.13/ASv6.19 comparison](./contract-comparison-v1/README.md) tested a simpler output contract across all 28 development notes, with fresh calls under both prompts. ASv6.13 had 20/28 clean notes and 256/274 accepted subjects; ASv6.19 had 22/28 and 187/198. ASv6.19 gained four clean notes and lost two. Both still had numerical-context and source-gap problems; its new two-week interval was not stated by the source. One paired run does not establish repeatable improvement.

The [completed confirmation](./contract-confirmation-v1/README.md) kept both prompts unchanged and repeated all observed clean-note differences plus the eight fixed difficult-note controls: 12 notes, two further outputs per version, 48 calls. All outputs were reviewed and provenance-verified. The first 12 reviews had visible prompt identities; the other 36 used opaque identities with judgments saved before mapping reveal. This is limited identity hiding, not independent review. The [recorded decision](./contract-confirmation-v1/assessment.json) retains ASv6.13 as the earlier broadly tested reference and ASv6.19 as an unvalidated experimental branch. Numerical-context improvements are useful, but several relative gains disappeared and insurance-source ambiguity recurred. This bounded comparison is finished; no further rerun of it is planned.

The [relationship-warning comparison](./relation-rule-ablation-v1/README.md) tested exactly two sentence deletions, with the general grounding constraint unchanged. Six selected notes were generated twice under each prompt. All 24 current outputs were reviewed with prompt/trial identities hidden and judgments saved before reveal. D10 and D25 had missing-context errors in both outputs for each prompt; D19 retained context in all four outputs. A third trial could not meet the declared two-target improvement condition, so its 12 calls were not run. One ASv6.20 insurance output also omitted most of its source, with no identified runner truncation; this single occurrence does not establish a recurring regression. The [decision](./relation-rule-ablation-v1/assessment.json) closes this change as negative diagnostic evidence, not an improved extractor.

The current check found no active generation unit; the goal is active. Host-pressure checks and sequential call admission remain mandatory. Do not rerun or reword the same relationship-warning removal automatically. A materially different hypothesis must be supported by existing evidence and predeclared before another comparison; none is selected at this checkpoint. No prompt is eligible for final validation.

- [Current checkpoint](./status.json)
- [Latest diagnostic: full notes and outputs](./relation-rule-ablation-v1/results.md), [review](./relation-rule-ablation-v1/review.json), and [verification](./relation-rule-ablation-v1/verification.json): 24 further unique threads/workdirs, exact frozen sources/prompts, unedited outputs and complete reviews. All 24 opaque IDs and the early-stop arithmetic were independently checked in a [read-only audit](./relation-rule-ablation-v1/independent-audit.json).
- [ASv6.12 full review](./asv6.12/review.json) and [diagnostic review](./asv6.12/diagnostic-review.json)
- [ASv6.13 full review](./asv6.13/review.json)
- [ASv6.13 repeated diagnostics](./asv6.13/diagnostic-review.json) and [reference-resolution review correction](./asv6.13/review-corrections.json)
- [ASv6.14 repeated diagnostics](./asv6.14/diagnostic-review.json)
- [ASv6.15 repeated diagnostics](./asv6.15/diagnostic-review.json)
- [ASv6.16 repeated diagnostics](./asv6.16/diagnostic-review.json)
- [ASv6.17 repeated diagnostics](./asv6.17/diagnostic-review.json), [exact tested prompt](./asv6.17/ASv6.17.md), and [proposal](./asv6.17/proposal.json)
- [Explicit review correction](./review-corrections.json): mirroring-only provenance is not the linked post's content. This changes ASv6.12's first-pass result from 24/28 to 23/28 clean notes; its historical judgments are retained.
- [Earlier isolation and preservation verification](./verification-development-3.json): 102 distinct threads and working directories, one turn each, no tool events, exact prompts and unedited raw outputs.
- [Full-development comparison review](./representative-comparison-v1/review.json) and [verification](./representative-comparison-v1/verification.json): 56 further distinct threads/workdirs, paired sequential admission, exact prompts, unchanged inputs and unedited outputs; no reuse across the 217 earlier calls checked.
- [Metadata comparison review](./metadata-sentence-comparison-v1/review.json) and [verification](./metadata-sentence-comparison-v1/verification.json): 54 further distinct threads/workdirs, exact prompts, unchanged inputs, unedited outputs and complete reviews; no reuse across the 273 earlier calls checked.
- [Confirmation review](./metadata-confirmation-v1/review.json) and [confirmation verification](./metadata-confirmation-v1/verification.json): 12 further distinct threads/workdirs, unchanged prompts and sources, complete reviews and sequential admission; no reuse across the 327 earlier calls checked.
- [Latest full-development review](./contract-comparison-v1/review.json) and [latest verification](./contract-comparison-v1/verification.json): 56 further distinct threads/workdirs, exact prompts and sources, complete reviews and sequential admission; no reuse across the 339 earlier calls checked. Minimum observed available memory was 105.21 GiB; memory and I/O PSI averages remained zero.

Every generated subject is preserved verbatim in each run's `output.json` and `results.jsonl`. The JSON reviews record subject-level decisions and whole-note coverage separately. These are assistant judgments, not new user approvals.

No personal notes, previous prompt text, raw output or user decision is to be edited. Masks and downstream processing are outside this goal.
