# HDBv2 node descriptions: v1 versus v2

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

V2 removed the user-confirmed `Keywords` error in the art node. It also added an unsupported `Home` restriction to the coffee node. This small test does not establish v2 as a reliable replacement; v1 remains frozen.

Only the question changed: `semantic similarity among these instances` became `subject matter shared by these instances`. The same complete three HDBv2 nodes, instance ordering, source fragments, formatting, Sol low model and wrapper were retained. Each node received one fresh isolated call. No prior titles, source notes, or review judgments were supplied.

The following are exact generated titles and every input mask. Each line is one vector; separated brackets on that line belong to the same mask. V identifiers identify vectors, not generated categories.

## S24afa84c49

V1: Coffee Bean Preparation

V2: Home coffee-bean preparation

- V410: ⟦grind coffee beans⟧
- V411: ⟦Rise⟧ ⟦grind coffee beans⟧
- V793: ⟦coffee⟧ ⟦Roasting your own beans⟧

Analysis: The common subject is still coffee-bean preparation. However, v2 adds Home. None of the supplied masks establishes a home setting; owning or roasting one's own beans does not establish where preparation occurs. The user confirmed this unsupported restriction as an error in v2.

## S004153390e

V1: Health concerns after excessive consumption

V2: Excessive Food and Drink Consumption Concerns

- V673: ⟦I just realized⟧ ⟦drank over a gallon of hot tea in less than 24 hours⟧
- V113: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧
- V115: ⟦by mid-day⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧ ⟦FUUUUUK⟧
- V672: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧
- V114: ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧
- V674: ⟦I've drank over a gallon of hot tea in less than 24 hours⟧ ⟦wonder⟧ ⟦bad for me⟧

Analysis: Both outputs describe concern about excessive consumption. V2 names food and drink explicitly, but concerns still does not apply explicitly to every mask. Because excessive quantities may themselves communicate concern, this remains a scope question for review, not a confirmed failure or clear improvement.

## S8a6ab7afaf

V1: Visual Art and Painting Keywords

V2: Visual art and painting

- V391: ⟦Photography⟧
- V757: ⟦painting⟧
- V761: ⟦#artoninstagram⟧ ⟦#painting⟧
- V758: ⟦watercolourpainting⟧
- V377: ⟦art⟧

Analysis: V2 drops Keywords and names subject matter. The user-confirmed input-format error is absent in this output. Visual art covers the supplied art forms; painting is already included within that category, so and painting is unnecessary emphasis, not a demonstrated false relationship.

## Reproducibility

- Frozen source packets and complete original notes (`../hdbv2-node-description-probe-v1/source-packets.json`) retain all 14 vector memberships and 26 exact source fragments. No source inputs or v1 files were changed.
- Comparison plan (`comparison-plan.json`) was saved before generation. Measured comparison (`comparison.json`) records exact titles, usage, thread IDs and hashes.
- Each node directory contains the exact `config.json` prompt and the wrapper's original `run/manifest.json`, `run/results.jsonl`, `run/output.json`, and `run/model-instructions.md`.
- All three v2 runs succeeded on their first attempts with distinct fresh threads. No retry or output selection occurred. The wrapper disables tools/web and runs from an empty temporary workspace with explicit minimal model instructions; unavoidable service-level context is not claimed absent.
- V2 used 5,346 input tokens and 452 output tokens, including 418 reasoning tokens. No additional API billing or rented compute was used.

One output per prompt per node cannot distinguish a prompt effect from sampling variation. The art wording improved in this run; the coffee restriction and unresolved consumption scope prevent declaring the prompt solved. The user has confirmed the original Keywords error and v2's unsupported Home restriction. The consumption scope concern remains an assistant judgment, not a confirmed failure.

**Publication status:** `collection:tracked-hdbv2-node-description-probe-v2` is selected as `title-studies/hdbv2-node-description-probe-v2` in the [publication catalog](../../docs/experiments/publications.csv), with [dataset manifest](../../docs/experiments/downloads.md#dataset-manifest). The local export preserves saved answers and recorded assessments; input AS lineage remains unverified. Nothing has been uploaded.
