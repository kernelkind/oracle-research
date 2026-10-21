# ASv6.28 — six additional notes

These pre-ASv6.100 results are retained as historical evidence.

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

Six fresh Astra-low calls, one per note. **No ASv6.23 calls.** The prompt, model and schema stayed unchanged.

I read all 91 generated subjects against the complete original notes. I found no definite unsupported subjects in this sample.

## What the outputs show

| Note | Individual subjects returned | What remains qualified or restricted |
| --- | --- | --- |
| Guitar tuning | Electric guitars; Guitar capo use; Guitar tuning stability; Guitar setup | Some entries are narrower than unrestricted Guitars or Guitar tuning. |
| Linux update | Linux use; Laptop boot failures; BIOS; Older Linux kernels | Update subjects remain PopOS-specific. |
| Cat-themed shop | Shopify storefront; Bitcoin payments | The cat entry names Carl specifically; there is no separate Cats entry. |
| Strike headline | Alberta; Teachers; Impending teachers’ strike | Business adaptation is restricted to Alberta. |
| SubGenius satire | Political practices; Economic practices; Spiritual practices; Friendly teasing | The combined group-alignment and membership/payment subjects are also preserved. |
| Insurance marketing | Fleet management; Travel insurance; Travel insurance premiums; Driver protection | The more detailed numerical and combined entries are preserved as well. |

These are actual output excerpts, not prescribed labels or a complete list. Read every original note and generated subject (`./full-outputs.md`).

The result supports individual-topic indexing beyond the four reused notes. It does not establish complete broad-topic coverage. In particular, “Carl, the author's handsome farm cat” is valid but does not independently name cats in general. That is a coverage observation, not a factual error; no mask was generated to test its downstream effect.

The fidelity review found no invented guitar diagnosis, precise Linux repair, implemented Bitcoin integration, business adaptation details, insurance tactics or calculated numbers. Literal and ironic readings of the satire were allowed, as the prompt requires. Overlapping entries were not penalized.

## Decision

Keep ASv6.28 unchanged. This result does not justify another speculative prompt edit. Next, inspect a short sample of the saved outputs in the existing review tool before deciding whether to freeze it; that review needs no new inference.

ASv6.23 remains frozen. ASv6.28 has not been promoted, and no further calls, masks, vectors or downstream changes were made.

## Limits and record

The six notes were selected from a text-only slice for variety before generation. They were excluded from the earlier four-note revision probes; they are not claimed to be a globally untouched or representative random holdout. One output per note does not establish repeatability, and “no definite error found” is my review judgment, not independent proof.

All six requests used fresh processes and one user message, empty application instructions and no model tools or conversation history. All succeeded on their first attempt. Total reported tokens: 7,311 (3,981 input, 3,330 output). No paid-API fallback was used.

Predeclared plan (`./plan.json`), semantic review (`./review.json`), summary (`./summary.json`), verification (`./verification.json`), scheduler record (`./scheduler/results.json`).

**Selected data:** Posts, final answers, recorded assessments, measurements and parameters are selected for release as `prompt-studies/asv6.28-fresh-v1-ce12886f6c3c` in the [publication catalog](../../../docs/experiments/publications.csv). The compact files use a different layout from the original local artifacts cited above.
