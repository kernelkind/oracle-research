# Complete HDBv2 title run — v20, Astra-low

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

All 61 accepted groups from the original 100-note HDBv2 run now have a v20/Astra-low title: 55 new calls and six reused first trials. The groups, masks and prompt are unchanged. This completes title generation, not hierarchy construction or a prompt/model freeze.

No title objections remain for this run: 59 titles were assistant-accepted, and the user approved the two titles raised for judgment. The original assistant assessments remain preserved as pre-review evidence, not outstanding failures. This is not an estimated general error rate or a claim that the user individually reviewed all 61.

## Review

The default view can revisit the two approved items, with every exact mask and my original reasoning in a separate comment. No further review is requested:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-titles-v20-astra-low/run-review.sh
```

- **Coffee Chains — Sf5a4b23523:** user-approved, with no comment. My earlier objection about café businesses is not an outstanding rejection.
- **Grow Nostr Campaign — S53be040f52:** user-approved, with no comment. My earlier uncertainty about the campaign interpretation is resolved for this title review.

The saved session is `target/hdbv2-node-titles-v20-astra-low-review-session.json`, SHA256 `ec3cc5a12d500524c5181713de8388ee91b3c4d8df9fe2fceb01d9da3b0243b8`. Its batch hash matches the unchanged focused review, and it contains exactly these two approvals with empty comments. No rationale, general interpretation rule or prompt/model freeze is inferred from those clicks.

Optional, all 61 titles:

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-titles-v20-astra-low/run-review-all.sh
```

The views use separate sessions in `target/`. The focused session now contains the user's actual approvals; no decisions were prefilled. B shows an already-saved second Astra trial for the six reused groups; other groups explicitly have no comparison response. This makes no new calls. Original notes and byte spans remain in `source-packets.json`; the title model and title review use the masks only.

## What this run establishes

The fixed prompt with Astra-low produced useful titles across this accepted group set. It did not repeatedly describe the input as strings, phrases or statements. My initial assessment, also reached by two independent read-only reviewers, was 59 accepted, one rejected and one uncertain. The user's subsequent approvals resolve both raised objections; Coffee Chains must not continue to be reported as a demonstrated failure from this review.

Review follows the user's clarification that reasonable interpretations and minor imperfections are acceptable. A broader accurate category, alternate wording, or a possible strict literal objection is not by itself a failure. The user's earlier approval of European Football is preserved in the [additional probe record](../hdbv2-node-description-probe-v20-astra-low-additional-v1/README.md); that separate coverage-expansion group is not added to these 61.

This is not evidence that the title procedure is perfect or that any particular hierarchy works. There was no new model comparison, retrial selection, title rewriting, mask correction, group change, subsumption call or hierarchy construction. The focused judgments are complete. No further prompt edit or freeze has been authorized by these case-specific approvals.

## Which groups

These are exactly the [complete v15 run's 61 accepted HDBv2 groups](../hdbv2-node-titles-v15/README.md), containing 247 mask instances. The original HDBv2 partition has 64 multi-note groups; only S14b6e36e21, S3d2aa08f70 and S68ce4fd21f are excluded. Garden/allotment group Saadde5a7ec remains included after the user's retraction.

The earlier 41-item review covered new or changed groups, while 23 unchanged groups were carried forward. Three of those unchanged groups lack individual saved approval clicks: S18bc272886, S220a14b044 and S24afa84c49. They are included under the documented overall baseline assessment; no clicks have been invented. Group acceptance and title acceptance remain separate.

## Fixed inputs and execution

- [run-plan.json](./run-plan.json) was saved before generation. The six saved Astra trial-1 responses were selected for reuse before the 55 missing groups ran. Saved trial-2 responses remain alternatives, not best-of replacements.
- [prompt.txt](./prompt.txt) is unchanged v20. Its SHA256 is `e7f183a1eceece70038ce697943df6d2ea7be9882a6fe0e4c4785840e3276959`.
- Model: `gpt-6-astra`, effort `low`, Codex 0.153.0, existing isolated wrapper and authorized main subscription. No API billing, rental, download or account change.
- Each new group received one fresh process, thread and empty temporary workspace. Tools, web, repository rules, user configuration, skills and extra runtime instructions were disabled. The runner supplied only its saved minimal instruction, `Follow the user's instructions.`, alongside the prompt; this does not claim removal of service-side context.
- Numbered instances contain quoted mask fragments separated by semicolons. No full notes, vector IDs, prior outputs, reviewer feedback or examples entered generation input. Original group membership, order and duplicate masks were preserved.
- The first call ran alone; the remaining runner pool was limited to three concurrent calls. All 55 succeeded on their first attempt, without retries. All 55 thread IDs are distinct and do not match the historical probe threads checked by the integrity reviewer.
- New-call usage: 122,893 input tokens, including 44,288 cached input tokens; 2,703 output tokens, including 2,216 reasoning tokens. Cache counts do not imply shared conversations.

One successful call, S0c034c4006, logged an internal Codex shell-snapshot validation warning for a missing temporary path. It produced no model tool events, and its saved output and integrity checks passed. The warning remains in the raw record; it was not a generation failure or reason to rerun.

## Evidence and verification

`./titles.json` contains every exact selected output, its raw result path, reuse alternatives and my original per-group reasoning. Its separate `user_review` section records the two later approvals without rewriting the original assessments. `new/<group>/` preserves each of the 55 configurations, manifests and raw outputs. Reused records remain in the [original Astra probe](../hdbv2-node-description-probe-v20-astra-low-v1/README.md).

The source packets match the v15 source artifact byte for byte. Independent integrity review checked scope, byte spans, prompt rendering, model settings, raw-output identity, hashes and isolation. A final packaging audit checked the assembled titles, review masks, comments and reuse paths. `./verification.json` records the checks and the warning above.

Both review views were opened with the existing production binary. The focused view showed both items and their separate comments; the full view showed all 61 and the existing comparison view. Smoke-test sessions were saved only under `/tmp/`, with all decisions unset. No review-tool code was changed.

Plane card CREC-127 could not be updated because no Plane tool was available in this session. No card status change is claimed.

**Publication status:** `collection:tracked-hdbv2-node-titles-v20-astra-low` remains in the [conversion review list](../../docs/experiments/publication-gaps.csv); a complete compact-data conversion has not been established.
