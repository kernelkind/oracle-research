# ASv6.27 subject-index experiment

These pre-ASv6.100 results are retained as historical evidence.

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

ASv6.27 changed the answers into shorter index-style headings, but did not recover the missing **Coffee shops** subject. Neither prompt independently named it in any of the three trials.

24 fresh calls: four unchanged real posts, two prompts, three trials each, Astra low. ASv6.23 remains frozen. No masks or vectors were generated.

## What changed

The candidate asks for a subject index, like the index at the back of a book, rather than statements about what happened. Four sentences change the task and expected entry form. Coverage, grounding, numeric and ambiguity rules remain the same, as do the context-before-subject output schema and model settings. No examples or note-specific instructions were added.

This tests the task-framing package, not the isolated effect of the word “index.” It does not test removing the auxiliary context field or replacing the prompt with a minimal index-only instruction.

- [Frozen ASv6.23](../asv6.23/ASv6.23.md)
- [Experimental ASv6.27](../asv6.27/ASv6.27.md)
- Predeclared plan (`./plan.json`)

## Independent subjects

Each count is the number of three outputs that independently named the checked subject. Semantic equivalents count. Merely mentioning a topic inside a specific event or naming a narrower subject does not count at the broad scope checked here. Narrower entries can still be valid and useful; these probes are not a uniquely correct list.

| Subject | ASv6.23 | ASv6.27 |
| --- | ---: | ---: |
| Coffee shops | 0/3 | 0/3 |
| Ad blocking in web browsers | 0/3 | 0/3 |
| Tracker blocking | 0/3 | 3/3 |
| Cookie-consent dialogs | 0/3 | 0/3 |
| Beets | 0/3 | 0/3 |
| Raised-bed gardening | 0/3 | 0/3 |
| Preserving food by vacuum sealing and freezing | 0/3 | 0/3 |
| Vacuum sealing food | 0/3 | 0/3 |
| Freezing food | 0/3 | 0/3 |
| Cheesecake | 0/3 | 1/3 |
| Blueberry cheesecake | 2/3 | 3/3 |

The two separate preservation probes were declared before generation; the original combined probe is also retained. Beets-specific preservation headings are recorded as narrower, not factual errors.

## What the outputs actually did

For the coffee-shop note, ASv6.27 trial 1 starts with:

1. Weekend laptop and tablet bans in coffee shops
2. Hipster success as a cause of coffee-shop laptop and tablet bans
3. Hipster influence on coffee-shop policies

Trial 2 also starts with a weekend device-ban heading. Trial 3 separately names laptop restrictions and tablet restrictions in coffee shops. None supplies Coffee shops by itself.

The same pattern appears elsewhere:

- Vivaldi becomes failures, settings, a particular workaround, and conditions under which a dialog appears. Its tracker-only setting is independently named in all three candidate outputs.
- Beets remain the current-year harvest, cultivation in a 4x4 bed, or preservation specifically of beets.
- The short cheesecake post produces Blueberry cheesecake every time. Only one candidate trial adds Cheesecake separately.

The candidate returned 84 subjects versus 110 from the control. This is evidence of shorter, less repetitive output, not successful broad-subject recovery by itself.

The fresh baseline differs from previous baseline trials on Cheesecake. Historical outputs have not been substituted for these results; three trials do not establish a stable reliability estimate.

## Fidelity and scope

I read all 24 lists and all 194 final subjects against the complete posts, with output identities shuffled and the version/trial key withheld until judgments were saved. Output style makes the task recognizable, so this is not independent or fully blinded validation.

I identified no definite unsupported additions, invented calculations, URL-derived subjects, bare metadata entries or commentary about missing information. The major subject areas in each source remain represented. The index task intentionally does not require every assertion or ownership detail to survive as its own entry.

The complete evidence is in all original posts and generated subjects (`./full-outputs.md`). Review judgments (`./review-judgments.json`) retain present, narrower and absent coverage separately, including accepted interpretations. No generated subject was edited.

## What this establishes

Changing the task to an index changes the output form. It does not, in this test, reliably cause the model to isolate the underlying subjects. The predeclared condition for further positive confirmation was not met because Coffee shops remains absent.

This does not establish that subject indexing is a bad objective, nor identify the internal cause. The remaining prompt still asks the model to write context before each subject and retain contextual relationships.

One concrete observation suggests a next diagnostic. The first coffee-shop entry in candidate trial 1 was produced after this auxiliary context:

> A previously liked coffee shop has introduced a rule against laptops and tablets on weekends.

It then became:

> Weekend laptop and tablet bans in coffee shops

All three candidate trials start with similar incident-specific context. That association does not prove causation. A narrowly scoped comparison with and without the context field could test whether requiring an incident description before the entry is contributing to the omission. Removing it would be an experimental condition, not a decision to discard ASv6.23's earlier context-fidelity improvements.

No next diagnostic or prompt revision has been run. No promotion is warranted from this experiment.

## Execution

All 24 calls succeeded on their first attempts. Each actual wire request contained only the exact prompt and post as one user message, empty application instructions, and no tools or prior history. All response IDs are distinct and differ from the preceding comparison. Published outputs match raw responses.

Usage: 21,720 tokens: 13,026 input and 8,694 output, including 1,242 reasoning tokens. Calls used subscription access, not paid API billing.

The existing bounded runner admitted at most eight calls together, with a 2 GiB limit and no swap per call. The lowest sampled available memory exceeded 103 GiB; sampled memory and I/O pressure stayed at zero. All owned jobs ended. Verification (`./verification.json`), machine-readable results (`./summary.json`).

**Selected data:** Posts, final answers, recorded assessments, measurements and parameters are selected for release as `prompt-studies/asv6.27-comparison-v1-d34c3aaea8dd` in the [publication catalog](../../../docs/experiments/publications.csv). The compact files use a different layout from the original local artifacts cited above.
