# Complete HDBv2 title run — v15

All 61 accepted HDBv2 groups now have a saved v15 output: 12 reused first trials and 49 new calls. This is output coverage, not approval of all titles or a completed hierarchy.

Later follow-up: the [complete v20/Astra-low title run](../hdbv2-node-titles-v20-astra-low/README.md) covers these same 61 groups with unchanged masks. This v15 artifact remains intact as the earlier result; the later run has its own outputs and review sessions.

The user approved all three titles raised for judgment, without comments. Of the 49 new outputs, 42 remain assistant-accepted and three are now explicitly user-approved; four remain assistant-flagged problems. No output was edited or regenerated. These are case-specific title approvals, not a new general rule or a prompt freeze.

## Review

The default review reopens the three approved titles, with every member mask and my original reasoning in a separate comment:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp && \
  ./sse_multivector/hdbv2-node-titles-v15/run-review.sh
```

- Successful recipe results — S07d0857008: approved.
- Rate reduction — S6621c8eaa9: approved.
- Foods with “cheese” in the name — Sa6996b199f: approved.

The saved session is `target/hdbv2-node-titles-v15-review-session.json`, SHA256 `0779bd0c19450595e882d32d0dc2630181119f9cfa8cb190b0da85dfd0cb8048`. It contains exactly these three approvals, all with empty comments. Its batch hash matches the unchanged review. Original assistant concerns remain pre-review evidence, not outstanding objections. No further interpretation of why the user approved each title is inferred.

Optional: `run-review-problems.sh` shows the four clear problems; `run-review-all.sh` shows all 61 outputs. Each view has a separate saved session. No new user decisions are prefilled. B shows an existing second trial when there is one; otherwise it explicitly says no comparison call was made.

## Four clear problems

| Group | Exact output | Problem |
|---|---|---|
| S0eafedb82e | Two numbered lines: “1. Recipes” and “2. Recipes” | Two answers instead of one title. The raw spacing and newline remain in the artifact. |
| S18bc272886 | Strings prefixed with “dog” | Names the strings' construction rather than the dog subject. |
| S78e7660d1d | Tea-related statements | Classifies the input as statements rather than naming tea. |
| S83f6ab41f0 | Everyday English expressions | Names language/form rather than the messages about someone's day. |

The repeated text-form titles show that the earlier problem is not fully resolved by v15. Most new titles remain straightforward subject categories. This does not justify rejecting HDBv2 or changing its memberships, and no prompt revision was made in this run.

The “Eggs” and “Food preparation” titles were not rejected merely because some masks were broader than others. My reasons, including disagreements with the independent reviewers, are preserved in `titles.json` and `assessment-audit.json`.

## Which groups are included

The original HDBv2 artifact contains 64 multi-note groups. The earlier review showed 41 new/changed groups; 23 unchanged baseline groups were carried forward.

The saved 41-group review has 37 valid / 4 invalid clicks. The later garden/allotment retraction makes that 38 accepted / 3 rejected. The 23 unchanged groups inherit the user's overall baseline assessment. Only 20 have individual saved valid clicks; S18bc272886, S220a14b044 and S24afa84c49 do not. No clicks were invented.

The three excluded groups are S14b6e36e21, S3d2aa08f70 and S68ce4fd21f. Garden group Saadde5a7ec stays included. Thus 61 groups are included; every one contains at least two distinct notes. Group acceptance is separate from title acceptance.

Sources: [full HDBv2 groups](../real-note-fine-segmentation-v1/hdbscan-cross-note/review/review.json), [original decisions](../real-note-fine-segmentation-v1/cross-note-density-v1/user-response.json), [documented retraction](../real-note-fine-segmentation-v1/cross-note-density-v1/README.md), [baseline record](../real-note-fine-segmentation-v1/results.md).

## Fixed inputs and execution

- Unchanged v15 prompt, gpt-5.6-sol, low effort, pinned Codex 0.153.0 and existing isolated wrapper.
- One fresh process, thread and empty workspace per new group; three concurrent calls at most. All 49 succeeded on their first attempt.
- Only numbered mask instances entered the prompt. Fragments within an instance remained quoted and separated by semicolons. Complete groups, ordering and duplicate masks were preserved.
- No full source notes, IDs, previous titles, reviewer feedback or examples in generation input; tools and web disabled. Same minimal runner instruction and service context as earlier runs.
- Existing subscription only; no new API billing, model download or rental.
- New-call usage: 88,537 input tokens, including 3,072 reported cached input tokens; 5,048 output tokens, including 4,594 reasoning tokens. Fresh thread IDs were verified independently of prefix-cache accounting.

The [first v15 run](../hdbv2-node-description-probe-v15/README.md) and [six-new-group run](../hdbv2-node-description-probe-v15-additional-v1/README.md) remain unchanged as generation evidence. Their first trials are reused by a policy recorded before generation; second trials remain alternatives. No best-of selection was performed.

## Evidence

`run-plan.json` was saved before generation. `source-packets.json` preserves original notes, byte spans and exact fragments for all 61 groups; full notes are provenance only. `new/<group>/` preserves configs and raw execution records for the 49 calls. `titles.json` assembles all 61 raw outputs with source paths, alternatives and per-group assistant reasoning. It is not an approved-title whitelist.

Two independent read-only reviews covered the first 32 new outputs; I reviewed all 49. `assessment-audit.json` records disagreements. `verification.json` checks the unchanged prompt, source membership/spans/fragments, raw output identity, isolated execution, usage and review packaging. Focused, problem and full views were smoke-tested without recording user decisions.

V15 remains unfrozen. No hierarchy links, subsumption calls or membership changes were made. The three review questions are resolved. The user subsequently confirmed the four problems above in chat and approved a targeted v16 test; no reject clicks were fabricated. The [v16 results](../hdbv2-node-description-probe-v16/README.md) preserve two new trials on those four groups and five accepted controls. The assistant finds usable titles twice for three former failure groups; the dog group still fails. The user accepted v16's only uncertain title, “Temporal deceleration.” No focused review questions remain. This complete v15 artifact and all raw outputs remain intact; v16 is not frozen or installed as its replacement.
