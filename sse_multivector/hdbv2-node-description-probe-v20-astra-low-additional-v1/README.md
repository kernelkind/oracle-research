# V20 Astra-low: six previously untitled groups

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

No title objections remain in this six-group sample: ten outputs were assistant-accepted, and the user explicitly accepted “European Football” for the remaining group, covering its two capitalization variants. The original assistant assessments remain preserved separately. These are review outcomes, not a population accuracy estimate.

## Exact outputs

| Complete group | Trial 1 | Trial 2 |
|---|---|---|
| S5a50550c18 | Restricting Network Access | Restricting Network Access |
| Scccd04c325 | Japanese Culture | Japanese Culture |
| Sf1004af893 | Physical Stretching | Physical Stretching |
| S260ccd3184 | Community | Community |
| Sd621a11e19 | Gianduja Availability | Gianduja Availability |
| Sd7a87d7a3c | European Football | European football |

No title, mask, or group was edited. `./titles.json` includes every output, all masks, the original pre-review assistant assessment and raw-result path. The chat approval below resolves the football objection; no TUI clicks were invented.

## Football title: approved in chat

Asked explicitly whether “European Football” was acceptable for this group, the user answered “yes.” The earlier objection was that one instance contains only ⟦football⟧, while other instances supply the European context. Treating that literal scope objection as a clear practical failure was too pedantic.

Complete group, preserving every mask:

- V998: ⟦Before the Euro⟧ ⟦algorithm picked England⟧ ⟦clear favorite⟧ ⟦win⟧
- V1002: ⟦England⟧ ⟦lame football⟧
- V1000: ⟦Before the Euro⟧ ⟦algorithm⟧ ⟦England⟧ ⟦clear favorite to win⟧
- V1001: ⟦Euro⟧ ⟦algorithm picked England⟧ ⟦clear favorite to win⟧ ⟦Have no idea how it got there⟧
- V999: ⟦Euro⟧ ⟦algorithm⟧ ⟦favorite to win⟧
- V1006: ⟦Euro⟧ ⟦algorithm picked England as the clear favorite to win⟧ ⟦lame football surprises⟧ ⟦zero people⟧
- V957: ⟦Decision day⟧ ⟦lot⟧ ⟦leagues⟧ ⟦Europe⟧ ⟦football⟧
- V955: ⟦football⟧
- V956: ⟦leagues around Europe⟧ ⟦football⟧

The user also clarified that nondeterministic models are imperfect: assessment must focus on useful, accurate descriptions at an acceptable error rate, not perfect wording or flawless literal compliance on every call. This title is an accepted description of this group, not an outstanding failure. That does not automatically approve other disputed titles or freeze the prompt/model.

## What the other results show

Network restrictions remain recognizable despite a hypothetical password change versus an actual firewall action. “Community” preserves the broad subject without importing musical context from the other instance. “Physical Stretching” does not require every instance to include bowing or a stiffness-relief purpose. “Japanese Culture” describes the poet/food connection instead of the text format. “Gianduja Availability” keeps availability without adding limited edition, a fixed quantity or freshly made status to every instance.

This is encouraging transfer beyond the first six groups, with no remaining objection after review. It is not a matched model comparison: no Sol calls were made on this sample. Repeated outputs from the same group are not independent semantic examples. The user approved completing [the original 61 accepted groups](../hdbv2-node-titles-v20-astra-low/README.md) using unchanged v20 and Astra-low, with review focused on meaningful errors. No prompt revision, automated correction or freeze followed this test.

## Review

The focused review can revisit both approved football outputs, with every mask and the original pre-review assistant reasoning. It is no longer an outstanding review request. B displays the other trial. The approval is recorded in chat above, not prefilled into a TUI session.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v20-astra-low-additional-v1/run-review.sh
```

[run-review-all.sh](./run-review-all.sh) presents all 12 outputs in a separate session.

## Selection and provenance

All 61 accepted original HDBv2 groups already had saved v15 titles. To avoid calling those unseen, this test used six complete, previously untitled groups from the saved [coverage-expansion experiments](../real-note-fine-segmentation-v1/coverage-expansion-v1/README.md). All six have saved valid user grouping decisions and contain at least two distinct notes.

[run-plan.json](./run-plan.json), `./source-packets.json` and all configs were saved before generation. Selection covered varied subjects and input structures before any new outputs were inspected. It did not prescribe exact expected titles or alter existing HDBv2 memberships.

An independent audit compared the six groups against 157 packets from 17 prior source-packet files and 343 rendered prompts from 309 configs, including old flattened inputs and the hashtag diagnostic. No complete member-set or raw-fragment-group match was found; none of the 26 exact note/range instances appeared in those prior source packets. This is novelty relative to saved title tests, not a newly sampled corpus or wholly unseen source notes. The broader corpus and upstream generation had already been studied.

Full notes and byte ranges are provenance only. Generation received only numbered instances; one instance per vector, with its exact fragments quoted and joined by semicolons. Instance order, duplicate masks and spellings remain unchanged.

## Execution and verification

- Byte-identical [v20 prompt](./prompt.txt), unchanged `gpt-6-astra` at low effort, same pinned Codex 0.153.0 and wrapper.
- Authorized main subscription; no new API billing, rentals, purchases or financial commitments. Credentials were not read or changed.
- First call alone, then waves of at most three. Every call had a fresh process, thread and temporary empty workspace. Tools/web, repo rules, skills and user configuration were disabled. No expected titles, examples or reviewer feedback entered generation.
- Twelve successful first attempts; no retries or best-of selection.
- Usage: 26,976 input tokens including 1,920 cached; 295 output tokens including 201 reasoning tokens. Prefix caching did not reuse conversations.
- `./verification.json` records independent input/output/hash/isolation checks and production review-tool smoke tests.

Raw artifacts and user review sessions are unchanged. This report and the follow-up summary in the [first Astra report](../hdbv2-node-description-probe-v20-astra-low-v1/README.md) record the later chat approval separately from the original assessments. CREC-127 remains the existing card; Plane tools were unavailable, so its external status/comment could not be updated.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v20-astra-low-additional-v1` remains in the [conversion review list](../../docs/experiments/publication-gaps.csv); a complete compact-data conversion has not been established.
