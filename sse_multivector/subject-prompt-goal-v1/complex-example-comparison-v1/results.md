# Does the harder example improve subject generation?

Not clearly. ASv6.22 recovered context in two additional CEO-related subjects, but both prompts still failed on the CEO note in two of three trials. Both had 14 of 18 fully accepted outputs. ASv6.22 is not promoted.

Only the second worked example changed: tapestry restoration became a longer puppet-and-suitcase example with several references and a return to an earlier topic. Instructions and the pool example stayed identical. Both prompts ran on the same six original notes, three fresh calls per note, using Astra low.

| Result | ASv6.21 | ASv6.22 |
| --- | ---: | ---: |
| CEO outputs missing necessary context | 2 of 3 | 2 of 3 |
| CEO meanings with necessary context | 4 of 12 | 6 of 12 |
| Hiring outputs missing necessary context | 1 of 3 | 1 of 3 |
| Outputs with no error, unresolved judgment or omission | 14 of 18 | 14 of 18 |
| Accepted subjects | 300 of 310 | 305 of 313 |
| Definite subject errors | 9 | 7 |
| Unresolved subjects | 1 | 1 |

All 623 subjects and every note's coverage were reviewed. More accepted subjects alone does not establish improvement: broad, narrow, overlapping and duplicate subjects are allowed.

## The CEO result

Complete unchanged source, including its unfinished quotation:

> "CEO has all employee calls where he does questions at the end that you can ask via an anon chat. He always says ask me something hard. So I asked him if his wife knew about what he&#39;s up to with hi"
> 
> this development changes my entire thesis. I've been tracking this for months and the trajectory is undeniable. the fundamentals are aligning in a way that's hard to ignore.
> 
> https://mastodon.social/@fesshole/116810711404206903

The four later meanings were present in every output. Here, “yes” means that the subject independently identifies the CEO-related matter, without needing another subject.

| Meaning | ASv6.21 trial 1 | Trial 2 | Trial 3 | ASv6.22 trial 1 | Trial 2 | Trial 3 |
| --- | --- | --- | --- | --- | --- | --- |
| Changed thesis | No | Yes | No | Yes | Yes | Yes |
| Months of tracking | No | Yes | No | Yes | No | No |
| Undeniable trajectory | No | Yes | No | Yes | No | No |
| Aligning fundamentals | No | Yes | No | Yes | No | No |

ASv6.22 trial 2 begins its later claims with a self-contained subject:

> The author presenting the quoted account of an employee questioning a CEO about his wife's knowledge of his conduct as a development that changes the author's entire thesis.

But the next item is:

> The author claiming to have tracked the matter discussed in the post for months.

And the following items are:

> The author describing the trajectory of the matter being tracked as undeniable.
>
> The author claiming that underlying fundamentals are aligning in a way that is hard to ignore.

Those three do not identify the CEO-related matter. The previous subject supplies their missing context. Trial 3 has the same pattern. Trial 1 gets all four right.

ASv6.21 also gets all four right in one trial, but none in the other two. The new example therefore adds two correctly grounded thesis subjects; it does not reliably carry that context through the remaining items. The predeclared improvement criterion—at most one failing candidate CEO output against at least two failing control outputs—was not met.

This is evidence about the outputs, not proof of how the model reasoned. The example changed its length, content and output count as well as its reference pattern.

## The other notes

The hiring note has one context error under each prompt. Complete source:

> Riley Walz, the Jester of Silicon Valley, Is Joining OpenAI
> 
> The software engineer known for online stunts is joining OpenAI to work on new ways for humans to use AI systems.
> 
> Sector: Electronic Labour | Confidence: 96%
> Source: https://www.wired.com/story/openai-hires-riley-walz/
> 
> ---
> Council (2 models): OpenAI hires Riley Walz, a high‑visibility internet personality, to embed cultural relevance into its AI offerings and sharpen user‑centric design. The move acts as a branding lever that shapes market perception, prompting heightened investor sentiment, prompting insurers to reassess liability exposures from new human‑AI interaction patterns, and driving data‑center planners to scale capacity for anticipated usage spikes. Analysts converge on the significance of this talent acquisition for brand and experience strategy, while noting that one analyst deviated by using predictive phrasing. The council highlights key metrics, valuation impacts, and cloud infrastructure adjustments for ongoing monitoring.
> Cross-sector: Finance, Insurance, Real Infrastructure
> 
>   ? Which user‑experience metrics does OpenAI prioritize in evaluating the impact of culturally‑oriented talent?
>   ? How do investors incorporate talent announcements into valuation models for AI firms?
>   ? What adjustments do cloud providers make to support increased interactive AI workloads linked to engagement‑driven features?
> 
> #FIRE #Circle #ai

ASv6.21 trial 3:

> One analyst differing from other analysts by using predictive phrasing.

ASv6.22 trial 1:

> One analyst deviating from other analysts by using predictive phrasing.

Both specific statements omit what the analyst was assessing: Riley Walz joining OpenAI. The other two trials of each prompt retain that context. The monitoring subjects also retain it.

The Bitcoin dashboard, fee/mempool, and enforcement notes have no identified errors or omissions under either prompt. Every fee output retains the block number somewhere in the list; the standing standard does not require repeating it in every fee-value subject.

The insurance note leaves one attribution unresolved under each prompt: “The Council” could refer to CIAB or the separate two-model analysis. Neither output explicitly conflates them. All original insurance text and outputs are in the complete record below.

One ASv6.21 CEO output also leaves whole-post rhetorical coverage unresolved. All four literal meanings are present, but whether their financial vocabulary adequately preserves the rhetorical framing is disputed. It already fails on clear context errors, so this uncertainty does not change the comparison count. No definite coverage omission was identified.

## Review and execution checks

Each call used a distinct thread and working directory, the unchanged isolated wrapper and schema, no conversation history, and disabled tools/web search. Exact source, prompt, manifest and raw-output checks passed. Saved output strings were not edited.

Three fresh independent reviewers saw complete notes and all outputs under opaque IDs. Their judgments were saved before prompt identities were revealed. The main reviewer read all subjects and reconciled disagreements. Two overly strict proposed judgments were withdrawn before identity reveal: mandatory block-number repetition and rejection of explicitly described infidelity insinuations. These corrections and remaining uncertainties are preserved in [review-reconciliation.json](./review-reconciliation.json).

Generation took about 100 seconds at up to 12 simultaneous calls. An initial launcher-path failure occurred before Python or inference started; it consumed no model calls. There were 36 model calls, no inference retries, and no remaining owned processes.

Available memory in the samples stayed above 103 GiB. However, the intended five-second polling cadence was not maintained: there were roughly 31-second gaps at the beginning and end of recorded execution. No pressure excursion was observed; those unsampled intervals are not verified. This scheduling shortfall is recorded, not treated as a successful five-second monitor.

The test used the existing subscription only. No paid API or rented compute was used. No final-validation data was opened.

[Full original notes and every unedited output](./full-outputs.md) · [Review](./review.json) · [Decision](./assessment.json) · [Mechanical verification](./verification.json) · [Resources and per-prompt tokens](./resources.json)

This comparison is complete. The result does not justify promoting ASv6.22 or claiming that a complex example solves context handling. ASv6.8 remains frozen.
