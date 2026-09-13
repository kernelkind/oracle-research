# HDBv2 node descriptions: v2 versus v3

V3 produced more useful descriptions in this small comparison, especially for art. It retained the specific sea-salt connection and avoided the earlier Home restriction. It is not yet a proven replacement: v2 also stopped adding Home on this repeat, and some category wording remains interpretive.

Both versions ran freshly on the same six complete HDBv2 nodes: the original three and three additional nodes selected from masks before generation. V3 adds only the approved requirement that the title's full meaning, including qualifying details, be supported by every instance. The [version registry](../fine-region-title-prompt-versions.json) retains v1 and v2 unchanged; v1 remains frozen.

## Exact outputs

These v2 results are new calls, not replacements for the [previous v2 results](../hdbv2-node-description-probe-v2/README.md).

| Node | Fresh v2 | V3 |
| --- | --- | --- |
| S24afa84c49 | `Coffee beans` | `Coffee Bean Preparation` |
| S004153390e | `Excessive Tea and Chocolate Consumption` | `Consuming large amounts of tea or chocolate within a day` |
| S8a6ab7afaf | `Visual art media and social media tags` | `Visual art` |
| Sfd8645f195 | `Sea Salt–Seasoned Foods` | `Foods with Sea Salt` |
| Saf220f7de1 | `Veganism vs. Meat-Based Dietary Advice` | `Dietary advice on whether to eat vegan or meat-based diets` |
| Sd6b13ec91f | `**Kindness Over Status**` | `**Kindness Over Social Status**` |

Each section below shows every exact input mask. V identifiers identify vectors. Multiple bracketed fragments on one line are one mask; repeated masks remain separate because they were separate members of the saved node. Full original notes and byte ranges are in [source-packets.json](source-packets.json), for provenance only; the model saw only the numbered fragments.

## S24afa84c49

V2: `Coffee beans`

V3: `Coffee Bean Preparation`

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

Analysis: V3 names the preparation activity shared by grinding and roasting. It avoids Home and is more informative than this fresh v2 title, Coffee beans. However, v2 also omitted Home on this repeat, so the prior error's absence cannot be attributed solely to the new instruction.

## S004153390e

V2: `Excessive Tea and Chocolate Consumption`

V3: `Consuming large amounts of tea or chocolate within a day`

- V673: ⟦I just realized⟧ ⟦drank over a gallon of hot tea in less than 24 hours⟧
- V113: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧
- V115: ⟦by mid-day⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧ ⟦FUUUUUK⟧
- V672: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧
- V114: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧
- V674: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧ ⟦wonder⟧ ⟦bad for me⟧

Analysis: V3 describes large quantities, the relevant food/drink alternatives, and the short time window supported by the masks. It no longer requires every instance to express health concern. The result is descriptively sound but reads more like a sentence than a concise category title. The fresh v2 output also dropped concerns, so this is not uniquely a v3 gain.

## S8a6ab7afaf

V2: `Visual art media and social media tags`

V3: `Visual art`

- V391: ⟦Photography⟧
- V757: ⟦painting⟧
- V761: ⟦#artoninstagram⟧ ⟦#painting⟧
- V758: ⟦watercolourpainting⟧
- V377: ⟦art⟧

Analysis: V3 describes the shared subject. V2 adds social media tags, which describes presentation and does not fit the photography, painting, and art masks uniformly. This is the same general input-format problem as the user-confirmed Keywords error, not merely repetition of that exact word.

## Sfd8645f195

V2: `Sea Salt–Seasoned Foods`

V3: `Foods with Sea Salt`

- V362: ⟦bagels⟧ ⟦sea salt flakes⟧
- V538: ⟦Mushroom Risotto with Shrimp⟧ ⟦Sea Salt⟧
- V360: ⟦bagels⟧ ⟦sesame⟧ ⟦sea salt flakes⟧ ⟦plain⟧

Analysis: Both descriptions retain the specific sea-salt connection shared by all three instances, while avoiding a bagel-only or risotto-only restriction. This supports that v3's constraint need not force a vague food label. The mixed toppings in V360 remain preserved; the title does not assert every topping is salt.

## Saf220f7de1

V2: `Veganism vs. Meat-Based Dietary Advice`

V3: `Dietary advice on whether to eat vegan or meat-based diets`

- V799: ⟦Time to become vegan⟧
- V815: ⟦modern dietitians⟧ ⟦should ignore⟧ ⟦just eat meat⟧
- V798: ⟦become vegan⟧
- V814: ⟦modern dietitians⟧ ⟦should ignore⟧ ⟦just eat meat⟧

Analysis: Both titles connect opposing dietary positions without claiming that all instances favor veganism or meat. V3's advice wording is plausible for Time to become vegan and should ignore / just eat meat. However, become vegan alone could also express personal intention. I would not call this a confirmed failure, but it is a useful test of whether a qualifier is justified rather than merely plausible.

## Sd6b13ec91f

V2: `**Kindness Over Status**`

V3: `**Kindness Over Social Status**`

- V630: ⟦not grant someone more priveleges based on status, or similar, but based on kindness and goodness⟧
- V461: ⟦poorest⟧ ⟦often⟧ ⟦most generous⟧
- V460: ⟦poorest⟧ ⟦often⟧ ⟦most generous⟧

Analysis: One mask explicitly prefers kindness/goodness over status when granting privileges. The others associate poverty with generosity. Kindness and generosity can share a recognizable meaning that is not reducible to status, so the description is plausible. Over adds a value-priority framing more explicit in the first instance than in the others. This is not yet a confirmed error; judge the shared subject, not whether every mask asserts the identical proposition. Markdown emphasis in the raw outputs is preserved.

## What this changes

- The v3 art title is preferable to the fresh v2 output: it describes visual art, not social-media-tag formatting.
- Coffee preparation and foods with sea salt show that the added constraint can preserve a useful specific shared subject.
- The earlier Home error did not repeat even in v2. Likewise, both fresh prompts stopped requiring consumption concerns. These changes reveal output variation, so they are not clean evidence that v3 caused those fixes.
- The dietary and kindness titles need semantic judgment rather than exact-string grading. Their possible scope concerns are assistant questions, not user-confirmed failures.

Recommendation: keep v3 unchanged as the candidate for the next small test on new nodes, after reviewing the less certain interpretations above. Do not freeze it or append another rule merely to eliminate a word in one plausible result. No further calls have been made.

## Execution and preservation

The [comparison plan](comparison-plan.json) and exact inputs were saved before running. All 12 calls used the same gpt-5.6-sol model, low effort, CLI executable and wrapper as before, with at most three concurrent calls. Each node/version has its exact config and unedited run manifest, output, and result log. No previous title, label suggestion, expected result, rationale or full source note was sent to a generation call.

[comparison.json](comparison.json) preserves measured outputs, prompt hashes, thread IDs, usage and assistant assessments. Each raw output was retained as returned, including Markdown emphasis. No retries or best-of selection were used. Earlier v1/v2 experiment files remain unchanged.

An independent read-only audit verified all 24 masks and 49 source fragments, exact prompt rendering, 12 first-attempt successes in distinct fresh threads/workspaces, matching raw outputs, and no model tool calls.

| Version | Input tokens | Output tokens | Reasoning tokens (included in output) | Cached input tokens (included in input) |
| --- | ---: | ---: | ---: | ---: |
| v2 | 10634 | 572 | 501 | 0 |
| v3 | 10742 | 942 | 867 | 1536 |

Cached input tokens are reported separately from thread identity; prefix caching is not evidence of conversation reuse. The wrapper uses fresh temporary workspaces and threads and disables tools and web. Service-level system context is not claimed absent. This used the existing Codex subscription, not new API billing or rented compute.

This six-node purposive sample is not a representative accuracy estimate, and one result per version per node is not enough to isolate prompt effects from output variation. No automatically generated title was treated as the uniquely correct answer.
