# V4 node-title experiment and review

The single unrelated contrastive example did not fix the targeted weather issue in this trial. Both fresh prompts titled the weather group as fall despite two masks supplying frost/sunrise information without establishing the season. Other selected controls remained broadly defensible. V4 is versioned but not frozen or selected as the replacement.

## Open the review

```bash
/home/dev/src/notedeck_worktrees/algos/oracle-mvp/sse_multivector/hdbv2-node-description-probe-v4/run-review.sh
```

The launcher builds the existing `sse-mask-review` binary through Nix with two build jobs, then opens its dedicated `review-titles` mode. No model calls are made by the UI.

- Six cards; one node and one v4-title decision per card.
- The exact v4 output is under review. The fresh v3 output is comparison only, not another approval question.
- All original member masks appear together with V IDs and bracketed fragments separated by spaces. Neither duplicate masks nor source fragments are removed.
- A approves v4; R disapproves v4; C opens the optional comment editor and Enter saves it; S skips. Left/right revisits cards, including reviewed cards; up/down scrolls. Ctrl-C pauses. Running the same command resumes the saved card.
- To reopen a completed card, append `--start-at Scc38f7607c` (or another node ID).
- User decisions live in `target/hdbv2-node-description-v4-review-session.json`. It is not prefilled with assistant assessments. Tests and smoke inspection use temporary sessions, not that path. Input identity is checked on resume so changed titles/masks cannot inherit decisions.

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

- Scc38f7607c: Both fresh versions restrict the category to fall even though V729 and V728 supply only frost/sunrise/garden evidence. V4's unrelated example did not remove that restriction in this trial. The raw v4 response additionally includes Title:, which is preserved rather than stripped. This is an assistant scope assessment pending user review, not a claim the underlying group is invalid.

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
- [UI batch](review.json) contains the exact generated titles and complete masks. It contains no assistant verdicts or edits to generated text.
- Each node/version directory contains its exact `config.json` and unedited run manifest, output, result log and model instructions.
- All twelve fresh isolated Sol low calls succeeded on attempt one, with at most three concurrent calls. Independent audit verified input reconstruction, complete membership, source spans, exact hashes, distinct threads/workspaces, no tools, and preserved v1–v3 registry entries and previous raw artifacts. No retries or best-output selection.
- UI verification: the new CLI test first failed against the old binary for the missing title-review entrypoint. All 7 new and 84 relevant existing tests then passed. A real-terminal check opened all six cards and verified pause/resume using a temporary session; the user session remains untouched. An independent code review found no concrete correctness issue. The UI batch was also checked directly against every raw output and all original UTF-8 mask ranges.

| Version | Input | Output | Reasoning included in output | Cached input |
| --- | ---: | ---: | ---: | ---: |
| v3 | 10706 | 1056 | 1003 | 0 |
| v4 | 10988 | 815 | 762 | 0 |

Existing Codex subscription only; no new API billing or rented compute. This is a six-node selected comparison with one output per version per node. It is not a representative accuracy estimate or proof that all contrastive examples fail. No new semantic verdict is presumed to have user approval.
