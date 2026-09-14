# V20 Astra-low: six previously untitled groups

Ten of 12 titles look usable. Both football trials add an unsupported European restriction. The five other groups work in both trials. These are assistant judgments, independently checked—not user title approvals or a population accuracy estimate.

## Exact outputs

| Complete group | Trial 1 | Trial 2 |
|---|---|---|
| S5a50550c18 | Restricting Network Access | Restricting Network Access |
| Scccd04c325 | Japanese Culture | Japanese Culture |
| Sf1004af893 | Physical Stretching | Physical Stretching |
| S260ccd3184 | Community | Community |
| Sd621a11e19 | Gianduja Availability | Gianduja Availability |
| Sd7a87d7a3c | European Football | European football |

No title, mask, or group was edited. [titles.json](./titles.json) includes every output, all masks, individual assessment and raw-result path.

## The repeated problem

Both football titles include “European,” but one instance is only ⟦football⟧. That instance does not independently restrict the subject to Europe. Other instances mentioning European leagues or England cannot supply the missing restriction under the unchanged prompt.

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

This is the same kind of unsupported narrowing previously seen with “Visual Art” over standalone ⟦art⟧. It demonstrates that Astra's earlier success on the art group did not establish reliable independent support. It does not invalidate the user's approval of this grouping or show that it cannot receive a valid title.

## What the other results show

Network restrictions remain recognizable despite a hypothetical password change versus an actual firewall action. “Community” preserves the broad subject without importing musical context from the other instance. “Physical Stretching” does not require every instance to include bowing or a stiffness-relief purpose. “Japanese Culture” describes the poet/food connection instead of the text format. “Gianduja Availability” keeps availability without adding limited edition, a fixed quantity or freshly made status to every instance.

This is encouraging transfer beyond the first six groups, with a specific remaining support problem. It is not a matched model comparison: no Sol calls were made on this sample. Repeated outputs from the same group are not independent semantic examples. No new prompt revision, automated correction or freeze followed this test.

## Review

The focused review contains both football outputs, with every mask and separate assistant reasoning. B displays the other trial. No user decisions are prefilled.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v20-astra-low-additional-v1/run-review.sh
```

[run-review-all.sh](./run-review-all.sh) presents all 12 outputs in a separate session.

## Selection and provenance

All 61 accepted original HDBv2 groups already had saved v15 titles. To avoid calling those unseen, this test used six complete, previously untitled groups from the saved [coverage-expansion experiments](../real-note-fine-segmentation-v1/coverage-expansion-v1/README.md). All six have saved valid user grouping decisions and contain at least two distinct notes.

[run-plan.json](./run-plan.json), [source-packets.json](./source-packets.json) and all configs were saved before generation. Selection covered varied subjects and input structures before any new outputs were inspected. It did not prescribe exact expected titles or alter existing HDBv2 memberships.

An independent audit compared the six groups against 157 packets from 17 prior source-packet files and 343 rendered prompts from 309 configs, including old flattened inputs and the hashtag diagnostic. No complete member-set or raw-fragment-group match was found; none of the 26 exact note/range instances appeared in those prior source packets. This is novelty relative to saved title tests, not a newly sampled corpus or wholly unseen source notes. The broader corpus and upstream generation had already been studied.

Full notes and byte ranges are provenance only. Generation received only numbered instances; one instance per vector, with its exact fragments quoted and joined by semicolons. Instance order, duplicate masks and spellings remain unchanged.

## Execution and verification

- Byte-identical [v20 prompt](./prompt.txt), unchanged `gpt-6-astra` at low effort, same pinned Codex 0.153.0 and wrapper.
- Authorized main subscription; no new API billing, rentals, purchases or financial commitments. Credentials were not read or changed.
- First call alone, then waves of at most three. Every call had a fresh process, thread and temporary empty workspace. Tools/web, repo rules, skills and user configuration were disabled. No expected titles, examples or reviewer feedback entered generation.
- Twelve successful first attempts; no retries or best-of selection.
- Usage: 26,976 input tokens including 1,920 cached; 295 output tokens including 201 reasoning tokens. Prefix caching did not reuse conversations.
- [verification.json](./verification.json) records independent input/output/hash/isolation checks and production review-tool smoke tests.

Previous artifacts and user review sessions are unchanged. Only a follow-up link was added to the [first Astra report](../hdbv2-node-description-probe-v20-astra-low-v1/README.md). CREC-127 remains the existing card; Plane tools were unavailable, so its external status/comment could not be updated.
