# ASv6.13 versus ASv6.19: repeated results

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Neither prompt is ready to freeze. ASv6.19 did better overall on these repeated notes, but the comparison does not establish a reliable overall improvement.

| Evidence | ASv6.13 | ASv6.19 |
| --- | ---: | ---: |
| Original full test: clean notes | 20/28 | 22/28 |
| Selected 12 notes, all three outputs each | 18/36 | 23/36 |
| Only the two additional outputs each | 13/24 | 16/24 |

A **clean output** has accepted coverage and no erroneous or unresolved subject. Broad, nested, overlapping and duplicate subjects remain allowed. Fewer subjects is not itself a gain.

The original full test required at least 26/28 clean notes and 95% accepted subjects. Both prompts failed. Repeating a selected subset cannot replace that result or authorize final validation.

## What repeated

We used the eight fixed difficult notes plus every note whose clean result differed in the first comparison. Each unchanged prompt received two more fresh calls per note: 48 additional calls. The table includes the first results, not just the new ones.

| Note | ASv6.13: clean outputs of three | ASv6.19: clean outputs of three |
| --- | ---: | ---: |
| D03 — Aerogarden offer | 3 | 3 |
| D04 — Satoshi preceded us | 2 | 3 |
| D08 — Short Snow / fly | 1 | 2 |
| D10 — Riley Walz hiring report | 0 | 0 |
| D18 — Exchange symbol list | 2 | 3 |
| D19 — Bitcoin dashboard | 2 | 2 |
| D23 — Bitcoin fee report | 0 | 1 |
| D24 — Insurance report | 2 | 1 |
| D25 — Clipped CEO quotation | 0 | 0 |
| D26 — Spaceflight crew | 2 | 3 |
| D27 — Cartoon-ban investigation | 2 | 3 |
| D28 — Tether / Hormuz Safe | 2 | 2 |

D-numbers identify the frozen development notes. Every trial's result and flagged subject (`./assessment.json`) is recorded separately from the complete subject-by-subject reviews (`./review.json`).

### Gains that held, weakened, or disappeared

- **D04, D26 and D27:** ASv6.19 remained clean, but ASv6.13 was also clean in both new trials. The first relative advantages did not repeat.
- **D08:** each prompt still produced at least one unresolved weather or literal-flight interpretation. The ambiguous slang is not a settled extractor failure.
- **D18:** ASv6.19 remained clean. ASv6.13 once counted the listed symbols and added “Twelve securities,” although the source did not state that total.
- **D23:** ASv6.19 improved its fee context across the three outputs and was clean once. ASv6.13 first omitted fee context, then twice interpreted the values as counts of items. This is useful evidence for ASv6.19's numerical-context instruction group, not proof that the problem is solved.
- **D19:** each prompt failed once, differently. ASv6.13 left several specific statements referring only to “the dashboard”; ASv6.19 once copied its identity from the URL.
- **D28:** ASv6.19's newly calculated two-week interval did not recur. ASv6.13 once changed a statement about the reason for choosing Bitcoin into “Bitcoin is not better money under normal conditions.” That changes the scope of the source's negation.

### Problems that remain

**The Riley Walz report (D10):** both prompts were unclean in all three outputs. Some items still discussed an analyst's wording or ongoing monitoring without naming the hiring event. ASv6.19 also made the sector/confidence annotation a subject twice.

For example, ASv6.19 trial 2 returned:

> The two-model council highlights key metrics, valuation impacts, and cloud-infrastructure adjustments as matters for ongoing monitoring.

The complete post ties that monitoring to OpenAI hiring Riley Walz. The item does not. Naming the council is not the same as identifying the event being monitored.

**The insurance report (D24):** the source has two distinct sections. CIAB reports premium data; a section headed “Council (2 models)” supplies further interpretations.

ASv6.19 used the bare source name “The Council” in two of three outputs:

> The Council observes that 0.2 percent commercial property and casualty premium growth in Q4 2025 signals tightening underwriting capacity.

That source remains ambiguous when the item is read alone. This is not an explicit wrong attribution. ASv6.13, however, explicitly assigned the interpretation to CIAB in its third output.

**The clipped CEO post (D25):** both prompts were unclean in all three outputs. They repeatedly described the unfinished “hi” text instead of limiting the subject to recoverable meaning. Some later items also referred only to “the development” or “the situation,” omitting the CEO context.

The relevant source ending is:

> So I asked him if his wife knew about what he&#39;s up to with hi

ASv6.19 trial 3 returned:

> An employee used the anonymous chat to ask the CEO whether his wife knew what he was doing with an incompletely identified person or thing described only as “hi.”

The unknown fragment is commentary about missing source information. It is not an additional meaning communicated by the author.

## Decision

Do not promote ASv6.19 as a demonstrated overall improvement, and do not keep repeating this same comparison. Keep ASv6.13 as the earlier broadly tested reference. Preserve ASv6.19 as an experimental branch with useful numerical-context evidence.

The cumulative record still shows changes exchanging errors. ASv6.17 was worse than ASv6.13 in the earlier representative comparison; changing the metadata instruction reduced one problem while attribution problems remained. ASv6.19 improves some context handling but does not clear the recurrent failures or the full-development gates.

The next action is to examine a different instruction-interaction hypothesis, not automatically add another exception to ASv6.19. The fixed validation requirements remain unchanged.

## Review and execution

All 48 calls succeeded, and every output has a whole-note and subject-by-subject review. The first 12 were already reviewed with prompt identities visible. The other 36 were displayed under opaque aliases; their judgments were saved before revealing the version mapping. The reviewer already knew the prompts and prior results, so this was limited identity hiding, not a fully blinded or independent review.

A consistency check revisited the dashboard and insurance judgments. Broad subjects are still allowed; they are not rejected merely for being broad. Specific statements that depend on “the dashboard,” “those dynamics,” or another unresolved reference are a different issue. No new mandatory attribution prefix or canonical subject list was introduced.

The [verifier](./verify.py) checks exact prompts, inputs, raw hashes, review completeness, 48 unique threads and working directories, one turn and no tool events per call, and no reuse across 395 prior calls checked. The original full-development artifacts, validation plan, final inputs and frozen registry are unchanged. It checks the recorded execution schedule for consistency; it cannot independently prove actual execution order or semantic correctness.

The separate read-only audit also checked the blind mapping and saved judgment hash, reconstructed the 12-note selection rule, and checked stdout message/usage agreement with the result records. Those additional checks are not implemented in the saved verifier.

The run used 106,276 input tokens and 21,103 output tokens. These totals include 24,960 cached input tokens and 10,020 reasoning output tokens respectively. No new paid API or rental was used.

Calls were admitted one at a time under the existing host-pressure limits. I/O pressure paused admission during the run. All 48 planned calls are now terminal; no further call was launched to replace a disappointing output.

## Complete evidence

Each output file contains every original note and every generated subject, without editing:

- ASv6.13, trial 2 (`./asv6.13-trial2/output.json`)
- ASv6.19, trial 2 (`./asv6.19-trial2/output.json`)
- ASv6.13, trial 3 (`./asv6.13-trial3/output.json`)
- ASv6.19, trial 3 (`./asv6.19-trial3/output.json`)
- [First paired test, including full sources and both outputs](../contract-comparison-v1/README.md)
- [Predeclared confirmation proposal](./proposal.json)
- Reviews (`./review.json`), pre-reveal judgments (`./blind-review.json`), and identity mapping (`./blind-review-key.json`)
- Verification results (`./verification.json`) and resource/execution observations (`./runtime.json`)

See [conversion gaps](../../../docs/experiments/publication-gaps.csv) for `collection:tracked-subject-prompt-goal-v1`.
