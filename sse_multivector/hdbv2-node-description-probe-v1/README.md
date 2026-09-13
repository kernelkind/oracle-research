# Frozen title v1 on three HDBv2 nodes

Three new, isolated Sol low calls used the unchanged v1 prompt. No subjects, masks, embeddings, memberships, hierarchy, or previous results were changed. Each numbered input was one original vector's complete mask; its exact source fragments stayed together, quoted and separated by semicolons. The model received no original notes, subject descriptions, node IDs, proposed labels, or other calls' results.

The nodes were selected before generation for different kinds of shared meaning. This is a small inspection, not a representative accuracy estimate. The assessments below are the assistant's, not user decisions.

## S24afa84c49

Generated description: **Coffee Bean Preparation**

All 3 masks, from 2 notes:

- V410 · N052: ⟦grind coffee beans⟧
- V411 · N052: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793 · N086: ⟦coffee⟧ ⟦Roasting your own beans⟧

Assessment: Looks sound: grinding and roasting are both ways of preparing coffee beans. The description captures their common subject without inventing a combined activity.

## S004153390e

Generated description: **Health concerns after excessive consumption**

All 6 masks, from 2 notes:

- V673 · N073: ⟦I just realized⟧ ⟦drank over a gallon of hot tea in less than 24 hours⟧
- V113 · N016: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧
- V115 · N016: ⟦by mid-day⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧ ⟦FUUUUUK⟧
- V672 · N073: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧
- V114 · N016: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧
- V674 · N073: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧ ⟦wonder⟧ ⟦bad for me⟧

Assessment: Plausible but potentially too narrow. V115, V114 and V674 explicitly include illness or concern about health. V673, V113 and V672 select quantities consumed without that qualification. The output emphasizes a meaning shared by some masks, not explicitly by every mask. This is a scope concern for user review, not a confirmed failure.

## S8a6ab7afaf

Generated description: **Visual Art and Painting Keywords**

All 5 masks, from 2 notes:

- V391 · N048: ⟦Photography⟧
- V757 · N080: ⟦painting⟧
- V761 · N080: ⟦#artoninstagram⟧ ⟦#painting⟧
- V758 · N080: ⟦watercolourpainting⟧
- V377 · N048: ⟦art⟧

Assessment: The art connection is sound, but “Keywords” describes the form of the supplied fragments rather than the subject of the notes. Listing Painting separately also repeats a type of visual art. This is a description-wording concern, not evidence of a grouping failure.

## Execution and checks

- All three completed on the first attempt, each with a different thread ID and empty temporary working directory. No retry, cached result reuse, or conversation resume.
- Exact prompts reconstructed from the frozen registry matched configs and saved manifests. All 14 source members and 26 UTF-8 byte-span fragments match the original review data, in order.
- An independent read-only agent verified input fidelity and run isolation. The generation agents themselves were three fresh harness processes.
- Web search, tools, skills, inherited user config, and extra runtime context were disabled. The runner's model-instructions file was unchanged; no response schema was added.
- The original HDBv2 review/response, frozen title registry, and wrapper hashes were unchanged after generation. No production code changed; checks exercised the existing runner and its saved outputs, not a new implementation.
- OpenAI Docs was consulted to check the existing runner's non-interactive/session controls; it did not change the experiment prompt. [Official command reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec).

| Node | Input tokens | Output tokens | Reasoning tokens (included in output) | Seconds |
|---|---:|---:|---:|---:|
| S24afa84c49 | 1745 | 105 | 96 | 16.91 |
| S004153390e | 1851 | 72 | 61 | 14.49 |
| S8a6ab7afaf | 1747 | 9 | 0 | 17.12 |

Calls ran concurrently. Reported tokens include runner/service context, not just the short visible prompt. All cache counters were zero. Subscription usage only; no paid API call, model download, local neural-model load, or rented compute.

Exact input configurations and raw output/event/usage records are saved in each node's directory. [Source packets](source-packets.json) retain original notes and mask ranges for provenance; that file was not passed to the model. The [frozen prompt registry](../fine-region-title-prompt-versions.json) remains unchanged.
