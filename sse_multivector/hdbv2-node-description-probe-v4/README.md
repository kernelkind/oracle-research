# V4 node-title experiment and review

The single unrelated contrastive example did not fix the targeted weather issue in this trial. Both fresh prompts titled the weather group as fall despite two masks supplying frost/sunrise information without establishing the season. Other selected controls remained broadly defensible. V4 is versioned but not frozen or selected as the replacement.

## Open the review

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v4/run-review.sh --start-at Sfd8645f195
```

The launcher builds the existing `sse-mask-review` binary through Nix with two build jobs, then opens its dedicated `review-titles` mode. No model calls are made by the UI.

- Only uncertain assistant judgments were surfaced: one card, **Sea salt** (Sfd8645f195), which you have now approved. The command above reopens it with that approval preserved. The other five results remain saved; they are not assigned user approvals or rejections.
- The exact v4 title stays above the masks. V3 is hidden until B opens the comparison; it is not another approval question.
- All original member masks appear together with V IDs, blank lines between masks, and bracketed fragments separated by spaces. Neither duplicate masks nor source fragments are removed.
- **My assessment** gives the brief judgment. A separate **My comment** section explains why I was unsure: the masks share a food-use context that “Sea salt” alone does not express. Both the masks and comment remain visible; Tab chooses which section up/down scrolls.
- A approves v4; R rejects v4; C edits **your** optional comment and Enter saves it; S skips. Left/right revisits cards. B opens/closes the comparison, including complete long titles or assessments. Ctrl-C saves/exits. Without `--start-at`, the launcher resumes unfinished work or reports completion.
- The supplementary assistant comment comes from `review-comments.json`, supplied with `--comments`. It is tied to this batch but stored separately from the original reviewed title, masks, assessment, and your decision. Adding the explanation does not reset or reinterpret your approval.
- This focused review uses `target/hdbv2-node-description-v4-uncertain-review-session.json`; its saved approval remains unchanged. The original six-card artifact and `target/hdbv2-node-description-v4-review-session.json` are also unchanged. Tests and smoke inspection use temporary sessions. Changed original review inputs cannot inherit previous decisions.

## Exact results

These are fresh v3/v4 calls, not replacements for earlier outputs. Markdown/code formatting below preserves the returned text, including the weather response's Title: prefix.

| Node | Fresh v3 | V4 |
| --- | --- | --- |
| Scc38f7607c | `The Arrival of Fall` | `Title: Fall’s arrival` |
| S24afa84c49 | `Coffee preparation` | `Coffee bean preparation` |
| S8a6ab7afaf | `Art` | `Art` |
| Sfd8645f195 | `Foods with Sea Salt` | `Sea salt` |
| S3d2aa08f70 | `Literature` | `Literature` |
| S96e55b4730 | `Weekend well-wishes` | `Weekend well-wishes` |

## Assistant assessment, separate from user review

- Scc38f7607c: Both fresh versions restrict the category to fall even though V729 and V728 supply only frost/sunrise/garden evidence. V4's unrelated example did not remove that restriction in this trial. The raw v4 response additionally includes Title:, which is preserved rather than stripped. I can reject this title without asking for another user decision. This is not a user verdict or a claim the underlying group is invalid.

- S24afa84c49: Both outputs capture preparation. V4's bean qualifier is present in all masks through grinding beans or roasting one's own beans with coffee. Neither fresh output adds Home. This does not establish that the example caused the omission: unchanged v3 had already omitted Home in earlier repeats.

- S8a6ab7afaf: Both return Art. This covers the supplied art, photography, painting and watercolor masks and avoids the earlier keywords/tag-format description. A broader title than some previous Visual art outputs is not automatically a failure, particularly given the plain art instance.

- Sfd8645f195: Sea salt is present in every instance. V4 drops the food context retained by v3 and supported by the bagel/risotto masks. Both are defensible subjects; whether the shorter title is informative enough is a review question, not an automatic correctness failure.

- S3d2aa08f70: Both retain Literature, covering the broad Literature mask without letting the three more detailed negative audiobook masks impose a restriction on it.

- S96e55b4730: Both retain weekend well-wishes, covering Saturday/Sunday and avoiding a Sunday-only, religious, or Nostr-only restriction.

The example tests the difference between a plausible qualification and one established by every instance: a yellow metal ring is not necessarily gold, while polishing remains shared. It is separate from the actual node instances and uses no expected answer from these cases. The original v3 body and actual-instance format are unchanged. The [registered v4](../fine-region-title-prompt-versions.json) preserves the exact example and prior versions.

Adding only a targeted demonstration and retesting the same cases follows the [official GPT-5.6 prompting guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6); the measured outcome here, not that guidance, determines whether this example helped. It did not fix the targeted case in this sample. No further prompt revision or experiment was run.

## Evidence and reproducibility

- [Run plan](run-plan.json) records selection, hypothesis and fixed settings before generation.
- [Source packets](source-packets.json) retain all 25 masks / 54 exact UTF-8 fragments from six complete HDBv2 groups, including full original notes for provenance. Full notes, review judgments and target answers were not passed to the model.
- [Comparison](comparison.json) contains exact outputs, hashes, fresh thread IDs, usage and separate assistant judgments.
- [Original complete batch](review.json) preserves all six exact generated titles and complete masks, unchanged.
- [Assistant assessments](assistant-assessments.json) distinguish four confident accepts, one confident rejection, and one uncertain judgment. These are not user decisions.
- [Focused UI batch](review-uncertain.json) contains only that uncertain item, with unchanged titles/masks and the assistant's opinion. Selection happens before opening the UI; the UI only presents supplied items and records the user's decisions.
- [Supplementary assistant comment](review-comments.json) adds the explanation in its own section without changing the focused batch or saved user approval. It is not a new model result or a new approval question.
- Each node/version directory contains its exact `config.json` and unedited run manifest, output, result log and model instructions.
- All twelve fresh isolated Sol low calls succeeded on attempt one, with at most three concurrent calls. Independent audit verified input reconstruction, complete membership, source spans, exact hashes, distinct threads/workspaces, no tools, and preserved v1–v3 registry entries and previous raw artifacts. No retries or best-output selection.
- Original UI verification: the CLI test first failed against the old binary for the missing title-review entrypoint. All 7 new and 84 relevant existing tests then passed. The full six-card artifact was checked against every raw output and all original UTF-8 mask ranges. Those original tests and artifacts are retained unchanged.
- Focused UI verification: the new assessment test first failed because the old input schema rejected `assessment`; the new tall-terminal test first demonstrated 23 unwanted blank rows between masks and opinion. After implementation, all 91 unchanged regressions and 8 new tests pass. New tests cover the actual one-card artifact, visible complete opinion/masks at 72×24, content-sized layout at 80×40, pinned title during scrolling, B comparison, complete long text, comments, and unchanged legacy session hashes. Old user data and all original generated artifacts remain unchanged.
- Separate-comment verification: 99 unchanged regressions and 8 new tests pass. Test-first checks cover the `--comments` entrypoint, complete masks and explanation together at 72×24 and 80×40, independent scrolling, B comparison versus C user comments, validation before session changes, and preservation of completed approvals when supplementary comments change. Original title/mask/assessment changes still fail the saved-session identity check. Release-terminal inspection at both sizes showed the complete explanation and three masks together with Approved status, using a temporary copy of the approved session. The original focused input and both actual user session files remain byte-for-byte unchanged.

| Version | Input | Output | Reasoning included in output | Cached input |
| --- | ---: | ---: | ---: | ---: |
| v3 | 10706 | 1056 | 1003 | 0 |
| v4 | 10988 | 815 | 762 | 0 |

Existing Codex subscription only; no new API billing or rented compute. This is a six-node selected comparison with one output per version per node. It is not a representative accuracy estimate or proof that all contrastive examples fail. No new semantic verdict is presumed to have user approval.
