# V18 source-description test — blocked before generation

No titles were generated. All 24 attempted calls returned the same account usage-limit error. This provides no evidence for or against the prompt change.

The runner reports: “try again at Sep 19th, 2026 4:11 AM.” That time is reproduced from the provider error; no timezone was supplied there.

## Authorized change

V18 adds only this sentence after v16's opening:

> The quoted text comes from social-media posts.

The strict per-instance check is unchanged. So are all source masks, including `dogstr` and `dog` without added hashtag markers. No examples, suggested titles or full-note context were inserted.

V17 was the rejected, unrun proposal to remove the check. It was not tested or added to the registry. V18 is a separate version and remains unfrozen.

## Planned comparison

Six complete previously used groups: dogs, art, wine, coffee preparation, tea, and comments about someone's day. Each receives two fresh v16 calls and two fresh v18 calls: 24 calls total.

The comparison checks whether identifying the text's source reduces text-format titles while preserving scope. The art, wine and coffee examples also check for unsupported restrictions; success on dogs alone would not establish that the change is safe.

Both versions use gpt-5.6-sol / low and the unchanged isolated wrapper. Each input keeps every mask in its original order, with quoted fragments together inside one numbered instance.

## What happened

Preflight verified exact prompt rendering, the one-sentence insertion, preservation of the check and prior versions, and six complete source packets. Every attempted call failed on attempt 1, before any response item. Raw events identify 24 distinct threads; failed wrapper records leave their top-level thread fields null. Usage was not reported, not measured as zero.

The launcher's queue continued after the first usage-limit errors, so all 24 attempted calls received that same error before the main agent processed completion output. No retries were made. Before resuming, check one call succeeds and stop new submissions if a shared account error recurs.

No account credentials were inspected or changed; no model switch, purchases, downloads, rentals or new API billing was introduced.

## Evidence and next action

[run-plan.json](./run-plan.json) and all configs were saved before execution. [source-packets.json](./source-packets.json) preserves the complete notes and byte spans for provenance only; full notes were not sent to generation. [status.json](./status.json) records the failure and each raw event path. The `v16/` and `v18/` directories preserve all configs, manifests and failed call records.

[prompt.txt](./prompt.txt) and [baseline-prompt.txt](./baseline-prompt.txt) preserve the exact templates. [The earlier v16 results](../hdbv2-node-description-probe-v16/README.md) remain intact.

Await account availability or explicit direction to use another account. Do not infer a title result, freeze v18, or package an empty review as completed.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow) informed the one-change comparison; it supplies no evidence about this uncompleted experiment.

CREC-127 remains the tracking card. Plane tools were not available in this session, so its external status/comment could not be updated.
