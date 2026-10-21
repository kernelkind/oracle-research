# Node-title prompt v12

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The stricter prompt avoided several unsupported restrictions, but did not reliably return subject titles. Art and wine became descriptions of the supplied text. This is not a reason to reject broad categories; the problem is what the title describes.

Six previously used groups, two fresh Sol-low calls each. The exact approved draft is preserved in [prompt.txt](prompt.txt). V12 is a tested candidate; v1 remains frozen.

| Group | Trial 1, exact response | Trial 2, exact response |
| --- | --- | --- |
| Art | Visual Art–Related Hashtags | Art-related keywords |
| Coffee-shop music | Music Playing in a Coffee Shop | Music Playing at a Coffee Shop |
| Wine | `**Text that explicitly mentions wine**` | Mentions of Wine |
| Coffee preparation | Coffee bean preparation and roasting | Coffee bean preparation activities |
| Sea-salt foods | Food combinations that include sea salt | Foods and ingredients featuring sea salt |
| Weekend wishes | Saturday and Sunday well-wishes | Weekend well-wishes |

I accept both calls for coffee-shop music, coffee preparation, sea-salt foods, and weekend wishes. Some wording is redundant or awkward, but that is separate from false membership.

Art is still problematic: Photography and painting are not necessarily hashtags, and art alone does not establish visual art. Both art calls also describe the input as hashtags or keywords. The wine calls avoid the user-rejected pairing relationship, but describe mentioning wine rather than naming Wine as the subject.

The prompt says category but never explicitly specifies a subject category rather than a category of text. That is a plausible explanation for this pattern, not a proven causal diagnosis. This test does not justify abandoning the new per-instance support requirement or automatically revising it.

Every exact input mask, both raw titles, historical v11 title, and per-group reasoning appear in `comparison.json`. `source-packets.json` preserves full notes and mask byte ranges for provenance; full notes were not passed to generation.

All twelve results are available in the existing review tool:

This is optional inspection, not a request to adjudicate twelve uncertain decisions. No user decisions were prefilled. The historical v11 title is context, not a fresh control. Each card shows the current trial, all its masks, and a separate assistant comment.

`verification.json` records twelve distinct threads/workspaces, one attempt per call, exact approved prompts, unchanged masks and previous versions, no tools, and usage. Total: 21,542 input tokens and 2,368 output tokens, including 2,233 reasoning tokens. Existing subscription only; no new API billing or rented compute.

These are six reused development groups, not a holdout or an accuracy estimate. Two calls per group show repeatability on this sample, not general reliability. Historical output differences alone cannot establish causation.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v12` is selected as `title-studies/hdbv2-node-description-probe-v12` in the [publication catalog](../../docs/experiments/publications.csv), with [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
