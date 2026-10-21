# V3 node descriptions: six additional nodes

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The unchanged v3 prompt produced several useful descriptions, including an appropriately broad Literature title. The main concern is Fall’s Arrival: two member masks describe frost and sunrise but do not establish fall. This is an assistant-identified restriction, not a user-confirmed verdict.

These are six additional HDBv2 nodes, not a new corpus: 25 masks from 13 notes, three of which also appeared in the prior sample. Nodes were selected from masks before inspecting outputs. No earlier result, mask, grouping or prompt was changed.

## Exact outputs

| Node | Raw output |
| --- | --- |
| S53be040f52 | `grownostr` |
| Scc38f7607c | `Fall’s Arrival` |
| S96e55b4730 | `Weekend Well-Wishes` |
| S3d2aa08f70 | `Literature` |
| Sbec762f76f | `Mental Health Concerns` |
| S6fefae17d0 | `Family` |

The following is every input mask, in the order supplied to the model. Each V identifier is one vector; multiple bracketed fragments on its line form one mask. Repeated masks are retained. Full original notes and exact byte ranges are preserved in `source-packets.json`, but were not supplied to the model.

## S53be040f52

Output: `grownostr`

- V042: ⟦grownostr⟧
- V192: ⟦#grownostr⟧
- V386: ⟦#grownostr⟧
- V241: ⟦grownostr⟧
- V517: ⟦grownostr⟧
- V657: ⟦#grownostr⟧
- V844: ⟦grownostr⟧

Analysis: All seven masks name grownostr, with or without hashtag syntax. Returning the term itself avoids inventing a more specific campaign, objective or activity. A reader may still need to know the term, but the supplied masks provide no further description. The model did not label the input as keywords or hashtags.

## Scc38f7607c

Output: `Fall’s Arrival`

- V493: ⟦It'll warm up, but fall is definitely here⟧
- V729: ⟦sunrise over⟧ ⟦frosty garden⟧ ⟦got me out of bed⟧
- V728: ⟦beautiful morning⟧ ⟦Stunning sunrise over a frosty garden⟧
- V492: ⟦Woke up⟧ ⟦brrr⟧ ⟦fall⟧ ⟦here⟧
- V491: ⟦fall⟧ ⟦definitely here⟧

Analysis: The title fits the masks that explicitly name fall. V729 and V728 describe a sunrise and frosty garden, not a season. Frost can occur outside fall, and those masks do not establish the arrival of a season. This looks like carrying a qualification from part of the group into its whole title, the same general concern as the earlier Home restriction. This is an assistant flag, not a user-confirmed verdict. The group can still have a valid shared weather subject; this does not establish a grouping failure.

## S96e55b4730

Output: `Weekend Well-Wishes`

- V863: ⟦I wish⟧ ⟦all⟧ ⟦wonderful⟧ ⟦Sunday⟧
- V487: ⟦Happy Sunday⟧
- V864: ⟦I wish⟧ ⟦all⟧ ⟦blessed Sunday⟧
- V840: ⟦have a great Saturday nostr friends⟧
- V862: ⟦I wish⟧ ⟦all⟧ ⟦wonderful⟧ ⟦blessed Sunday⟧

Analysis: The masks wish people well on Sunday or Saturday. Weekend Well-Wishes covers both days without restricting every instance to Sunday, a religious blessing, or a Nostr audience. It preserves the social meaning rather than merely listing the day names.

## S3d2aa08f70

Output: `Literature`

- V744: ⟦audio book⟧ ⟦meaningless drivel⟧ ⟦I gave up⟧
- V742: ⟦new audio book⟧ ⟦fluff⟧ ⟦Total meaningless⟧
- V743: ⟦new audio book I had⟧ ⟦like⟧ ⟦a load of fluff⟧
- V439: ⟦Literature⟧

Analysis: Three masks criticize audiobooks, but V439 supplies only Literature. The broad title covers all instances without claiming every instance concerns audiobooks, criticism or disappointment. This is useful restraint, not automatically a failure for being broad. It does not establish whether this node is the best possible grouping.

## Sbec762f76f

Output: `Mental Health Concerns`

- V063: ⟦anxiety⟧
- V601: ⟦change your life if you have unhealthy stress⟧

Analysis: Anxiety and unhealthy stress support a mental-health subject. The title does not import the change-your-life advice from only one mask. It is broader than the particular anxiety/stress connection and could potentially be more informative, but no uniquely correct alternative title is assumed.

## S6fefae17d0

Output: `Family`

- V513: ⟦Sophia⟧ ⟦baby⟧ ⟦family⟧
- V605: ⟦Focus on⟧ ⟦family⟧

Analysis: Family is shared by both masks. The output does not extend Sophia, baby, or the advice to focus on family to every instance.

## What this establishes

V3 can retain shared social meaning (Weekend Well-Wishes), use a necessary broad title (Literature), and avoid carrying a person or baby detail into a general family title. These are concrete useful outputs, not proof of general reliability.

The weather output shows the remaining issue more clearly: a detail supplied by some instances can still become a restriction on the entire category. A frosty garden is compatible with fall, but does not establish it. That distinction matters when a title will later represent the category for subsumption and navigation. The concern is label scope, not an assertion that the weather masks should not be grouped.

The next work should target this scope problem without forcing every output into a vague label. No further prompt edit or test has been run, and v3 has not been frozen. The weather assessment remains available for user review; there is no presumed user approval of any new verdict.

## Reproducibility

- [Run plan](run-plan.json) records the selection reasons and interpretation boundaries before generation.
- [Registered v3](../fine-region-title-prompt-versions.json) was unchanged, as were the executable, wrapper, Sol model and low effort used previously.
- Six fresh calls, at most three concurrent, all succeeded on attempt one. An independent read-only audit verified all 25 masks / 49 source fragments, exact prompt rendering, six distinct fresh threads/workspaces, matching raw outputs, and no model tool calls. No retries or best-output selection occurred.
- Each node directory contains its exact config and unedited run manifest, output, result log and model instructions. Only numbered source fragments and the exact v3 question/constraint entered the user prompt. Source notes, rationales and review instructions did not.
- Measured results (`results.json`) preserve titles, hashes, thread IDs, usage and separate assistant assessments.
- Usage: 10,681 input tokens and 582 output tokens; 530 reasoning tokens are included in output, with 0 cached input tokens. Existing Codex subscription only; no new API billing or rented compute.

This is a purposively selected same-corpus sample with one output per node. It is not an unseen-note holdout or a representative accuracy estimate. It contains no new comparative v2 runs and cannot measure a causal prompt improvement on these six nodes.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v3-additional-v1` is selected as `title-studies/hdbv2-node-description-probe-v3-additional-v1` in the [publication catalog](../../docs/experiments/publications.csv), with [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
