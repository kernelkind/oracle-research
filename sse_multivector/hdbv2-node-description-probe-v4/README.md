# V4 node-title experiment and review

The single unrelated contrastive example did not fix the targeted weather issue in this trial. Both fresh prompts titled the weather group as fall despite two masks supplying frost/sunrise information without establishing the season. Subsequent user feedback also identified omitted food context in Sea salt. V4 is versioned but not frozen or selected as the replacement.

## Open the review

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v4/run-review.sh --start-at Sfd8645f195
```

The launcher builds the existing `sse-mask-review` binary through Nix with two build jobs, then opens its dedicated `review-titles` mode. No model calls are made by the UI.

- Only uncertain assistant judgments were surfaced: one card, **Sea salt** (Sfd8645f195). Its saved UI decision is Approved; subsequent chat feedback clarified that the description should include the shared food context. The command above preserves the recorded decision and original assessment rather than rewriting review history. The other five results remain saved; they are not assigned user approvals or rejections.
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

- Sfd8645f195: Sea salt is present in every instance, but V4 drops the food context retained by v3 and supported by the bagel/risotto masks. The assistant initially treated that omission as an optional naming preference. The user clarified that food is part of the shared meaning the description should preserve: Foods with sea salt captures that meaning, whereas Sea salt alone is too broad. This is a title-generation issue, not a UI or grouping verdict. Original generated outputs, assessment artifacts, and saved user decisions remain unchanged.

- S3d2aa08f70: Both retain Literature, covering the broad Literature mask without letting the three more detailed negative audiobook masks impose a restriction on it.

- S96e55b4730: Both retain weekend well-wishes, covering Saturday/Sunday and avoiding a Sunday-only, religious, or Nostr-only restriction.

The example tests the difference between a plausible qualification and one established by every instance: a yellow metal ring is not necessarily gold, while polishing remains shared. It is separate from the actual node instances and uses no expected answer from these cases. The original v3 body and actual-instance format are unchanged. The [registered v4](../fine-region-title-prompt-versions.json) preserves the exact example and prior versions.

Adding only a targeted demonstration and retesting the same cases follows the [official GPT-5.6 prompting guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6); the measured outcome here, not that guidance, determines whether this example helped. It did not fix the targeted case in this sample.

## V5 — prepared, not tested

The [registered v5](../fine-region-title-prompt-versions.json) changes one line in the existing unrelated jewelry example: it explains that Jewelry is too broad because both instances describe polishing. The existing explanation rejecting the unsupported gold restriction remains intact. This illustrates both omitting supported specificity and adding unsupported specificity, without supplying an answer from the reviewed corpus.

The hypothesis was that this contrast would help preserve shared subject-defining context. It does not establish that the model was caused to omit food by the earlier example, or that every shared word belongs in a title. The user then requested deeper task-definition work before adding examples. V5 remains preserved and untested; the next authorized experiment uses example-free v6 instead. V1–v5 and the frozen v1 selector are unchanged.

## V6 — example-free comparison

V6 defines the desired shared meaning directly: interpret each instance's fragments together, preserve shared context and relationships, generalize differences, and shorten the wording without broadening the meaning. It contains no examples. The [pre-run plan](../hdbv2-node-description-probe-v6/run-plan.json) and [exact comparison](../hdbv2-node-description-probe-v6/comparison.json) preserve the six unchanged groups and twelve new isolated Sol low calls: one v3 and one v6 per group, at most three concurrent calls.

| Node | Fresh v3 | V6 | Assistant judgment of v6 |
| --- | --- | --- | --- |
| Scc38f7607c | A chilly fall morning | Frosty fall mornings | Reject: combines details not established by every mask |
| S24afa84c49 | Coffee beans | Coffee Bean Preparation | Accept: retains the shared preparation activity |
| S8a6ab7afaf | Art | Visual Art and Photography | Uncertain, lean reject: plain art does not establish visual-only scope |
| Sfd8645f195 | Foods Featuring Sea Salt | Foods Seasoned with Sea Salt | Accept: retains the shared food-use context |
| S3d2aa08f70 | Literature | Literature | Accept: respects the generic Literature member |
| S96e55b4730 | Weekend well-wishes | Weekend Day Well-Wishes | Accept: generalizes Saturday and Sunday wishes |

The weather result is still a concrete title failure: V491 supplies only fall, while V729/V728 supply frost and sunrise without establishing fall. V6 combines these details instead of identifying what is shared. Food context is retained, but fresh v3 also retains it. Coffee is more descriptive in this paired trial. These observations do not establish a consistently better prompt; v6 is not frozen.

Only the art judgment needs user input. The independent reviewer rejects the visual-only restriction; the main reviewer leans against it but recognizes that ordinary use of art can mean visual art. That semantic boundary, not a demand that every art mask mention photography, is the review question. The title and every original mask remain unchanged; the reasoning appears separately under My comment.

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v6/run-review.sh
```

The [focused batch](../hdbv2-node-description-probe-v6/review-uncertain.json) uses a fresh v6 session. The [complete six-card batch](../hdbv2-node-description-probe-v6/review.json), [all assistant comments](../hdbv2-node-description-probe-v6/review-all-comments.json), [assessments](../hdbv2-node-description-probe-v6/assistant-assessments.json), and [execution verification](../hdbv2-node-description-probe-v6/verification.json) remain available. No assistant judgments are copied into user decisions and no previous review data is changed.

Verification confirmed exact prompt reconstruction, all 25 masks / 54 fragments, twelve distinct fresh threads/workspaces, one successful attempt per call, no tool events, and unchanged raw responses. The existing release TUI loaded both batches and their hash-bound comments; temporary sessions verified the separate comment, scrolling, baseline comparison, and exit without recording approvals. No production Rust code changed. Total usage was 21,616 input and 1,094 output tokens, including 984 reasoning tokens, with no cached input; existing subscription only.

This is a selected development sample, not a general accuracy estimate. The next justified prompt question is how to distinguish context shared by all instances from details distributed across different instances. This run does not justify adding a corpus-specific example or declaring v6 a replacement.

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
