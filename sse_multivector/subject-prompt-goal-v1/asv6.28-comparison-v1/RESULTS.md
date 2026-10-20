# ASv6.28 subject-index comparison

These pre-ASv6.100 results are retained as historical evidence.

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.28 made useful progress: it independently named Coffee shops in two of three outputs, versus none with frozen ASv6.23. It also recovered other individual subjects. The improvement is incomplete and observed on four reused notes, not a fresh validation set.

24 fresh calls: four identical real posts × two prompts × three trials, Astra low. All 270 generated subjects were read against their full source notes. No definite unsupported addition was identified. ASv6.23 remains frozen.

## What changed

The approved rewrite explicitly asks for individual subjects as well as combinations. It defines a self-contained entry as one whose subject is clear, rather than one that reconstructs the surrounding statement. The auxiliary context field remains before the subject.

This tests the complete rewrite, not the isolated effect of one sentence, context generation, or the book-index analogy.

- [Frozen ASv6.23](../asv6.23/ASv6.23.md)
- [Tested ASv6.28](../asv6.28/ASv6.28.md)
- Plan recorded before generation (`./plan.json`)
- All original notes and every generated subject (`./full-outputs.md`)

## Which subjects appeared independently?

Each number counts outputs out of three. Semantic equivalents count; an entry restricted to a narrower subject is recorded separately. These probes are diagnostic, not a uniquely correct or exhaustive subject list.

| Subject | ASv6.23 | ASv6.28 |
| --- | ---: | ---: |
| Coffee shops | 0/3 | 2/3 |
| Website cookie dialogs | 0/3 | 3/3 |
| Beets | 0/3 | 2/3 |
| Raised-bed gardening | 0/3 | 2/3 |
| Cheesecake | 2/3 | 3/3 |
| Blueberry cheesecake | 3/3 | 3/3 |

ASv6.28 gardening trial 1 instead named **Homegrown beets** and **Raised-bed vegetable gardening**. Those are valid, narrower subjects, not factual errors.

All three candidate software outputs separately named **Ad blocking in Vivaldi** and **Tracker blocking in Vivaldi**. That is useful separation from the original troubleshooting statements, but still restricted to one browser. None independently named the unrestricted browser-ad-blocking or tracker-blocking probes.

The preservation entries remained specific to beets. None independently named general food vacuum sealing or food freezing. One output joined the two methods in a beet-specific entry; the others represented the methods separately.

Machine-readable counts (`./summary.json`) retain every predeclared probe and its present/narrower/absent classification.

## Coffee shops: the concrete change

ASv6.23 trial 1 begins:

> A coffee shop the author liked now prohibits laptops and tablets on weekends.

ASv6.28 trial 1 begins:

> Coffee shops  
> Weekend laptop and tablet bans in coffee shops  
> Weekend laptop bans in coffee shops  
> Weekend tablet bans in coffee shops

ASv6.28 trial 2 also names Coffee shops independently. Trial 3 instead begins:

> Coffee shop device restrictions

That third output still omits the broader Coffee shops entry.

The successful outputs retain incident-specific auxiliary context. For example, trial 1's context for Coffee shops is:

> The writer describes a coffee shop they previously liked, its new weekend device restriction, and their decision to stop visiting it.

This establishes that the context field does not inherently prevent an independent subject entry. It does not establish which instruction caused the improvement: multiple instructions changed together.

## Fidelity and measurement limits

I reviewed all 24 lists and all 270 final subjects with current prompt/trial identities and auxiliary context withheld until judgments were saved. The output styles make conditions recognizable; this was not an independent or fully blinded review.

No definite invented action, relationship, calculation, unit, URL-derived claim or commentary about missing information was identified. Topic-only headings are not treated as assertions that an action happened. Overlap and broad categories remain allowed.

ASv6.28 returned 167 subjects; ASv6.23 returned 103. The increase is not itself proof of quality. The independent-subject examples above are the relevant improvement.

One earlier measurement needs qualification: the ASv6.27 report counted Vivaldi tracker-only settings as covering unrestricted Tracker blocking. Here browser-specific entries are explicitly recorded as narrower, consistently with the declared scope rule. Do not interpret that reporting difference as a model regression. All earlier raw evidence remains unchanged.

The four notes were reused during development. Three outputs per condition do not establish a population reliability rate, and the index task does not require retaining every source fact in every entry. The complete judgments (`./review-judgments.json`) preserve the evidence behind each coverage decision.

## Decision

The comparison meets its predeclared condition for recommending further confirmation: Coffee shops appears in at least two candidate trials, another note gains independent subjects, and no recurring definite fidelity error was identified.

Keep ASv6.28 unchanged for a proposed small, diverse fresh sample. That would check whether subject separation generalizes and whether grounding holds on harder material. No further generation is authorized by this report; no prompt replacement, masking, embedding or segmentation has occurred.

## Execution

All 24 calls succeeded on their first attempt and have distinct response IDs, with no reused IDs from ASv6.27. Actual requests contained the exact prompt and source post, unchanged schema, empty application instructions, no tools and no conversation history. Published outputs match raw responses.

Usage: 25,682 tokens: 13,854 input and 11,828 output, including 1,238 reasoning tokens. Subscription access only; SDK cost estimates are not paid API charges.

The unchanged bounded runner admitted at most eight calls at once, with 2 GiB memory and no swap per call. Across 52 resource samples, available memory stayed above 104.0 GiB; sampled memory and I/O pressure remained zero. All owned jobs have ended. Verification (`./verification.json`).

The task-specific comparison, preserved records and separation of judgment from generation follow the applicable [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices). The guidance does not establish this prompt's effectiveness; the observed outputs above provide the evidence.

**Selected data:** Posts, final answers, recorded assessments, measurements and parameters are selected for release as `prompt-studies/asv6.28-comparison-v1-e8b2ce16c434` in the [publication catalog](../../../docs/experiments/publications.csv). The compact files use a different layout from the original local artifacts cited above.
