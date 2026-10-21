# Food & Drink reclustering after S05 replacement

Status: authorized experimental replacement and numerical rerun. The user
approved replacing all original local entries represented by S05 with its
single synthetic definition, then redoing HDBSCAN and epsilon selection.
Previously unassigned entries remain eligible. This does not activate a
production HiGen policy or alter HR22.

The source is the [100-note epsilon review](food-drink-hundred-epsilon-v1.md)
and its [completed S05 synthetic-root trial](food-drink-s05-root-v1.md).
The existing title and meaning, Food and domestic animals, are reused exactly.
All 113 original S05 entries are removed from clustering input. Their 58-note
union and original-entry associations are attached to one replacement item.

## Controls and preparation

The original 728 encoded entries become **616 inputs**: 615 unchanged original
entries plus one synthetic entry. All 361 previously unassigned encoded
entries are retained. The five original null Bootstrap meanings remain absent.
Only the replacement requires encoding; existing original vectors are reused
byte-for-byte from validated native worker receipts.

Its SSE input is the synthetic title followed by two newlines and the complete
explicit meaning. Only title bytes are selected for pooling. The same pinned
checkpoint, sentence-T5-base artifact, 768 dimensions, 512-token limit, CPU
device and learned pooling layers are used. The replacement counts as one
vector for density calculations; it is not replicated or weighted by 113.
Note counts expand its retained original associations and deduplicate IDs.

The reusable project CLI, `sse_multivector.hdbscan_section_replacement`, validates
the native consolidation receipt, exact section input, original HDBSCAN result,
state and source hashes. It prepares the existing SSE worker path and collects
that worker's validated receipt before numerical reclustering. No teacher
requests, prompt changes or paid resources are added.

HDBSCAN uses the unchanged angular-distance configuration: `min_samples=3`,
`min_cluster_size=2`, excess-of-mass selection. The 10%-trimmed bend epsilon
rule is unchanged and applied anew to the newly selected groups. Group and
section IDs refer to this rerun, not the old review. Unassigned inputs are
reported without inventing assignments or retaining old group labels.

## Completed result

| Measure | Original review | After S05 replacement |
|---|---:|---:|
| Clustering inputs | 728 | 616 |
| Selected HDBSCAN groups | 62 | 51 |
| Epsilon sections | 42 | 40 |
| Assigned current inputs | 367 | 293 |
| Represented distinct notes | 94 | 96 |
| Epsilon | 0.8265007473450509 | 0.8912946305292836 |

The 293 assigned inputs include the replacement item. Expanding its saved
113-entry association gives 405 original entries represented in selected
groups; these are associations, not 405 vectors in the new clustering.
All 94 previously represented notes remain represented, and two more notes
are gained. Four of the original 100 notes remain unrepresented by selected
groups. Coverage does not establish semantic correctness.

The replacement is assigned to **new G31**, alongside Animals, Veganism,
Animal slaughter, Animal fat, Raw meat, Non-carnivore recipes and Raw diets
for dogs. G31 has eight clustering inputs and represents 60 notes. It joins
new G11 (chicken, stock and chicken-related topics; eight inputs, five notes)
to form **new S08**, the largest section at 60 notes. Thus G11 adds no distinct
notes beyond G31's represented set. The original 58-note S05 membership is
fully present; the new section has two additional distinct notes.

| Largest new sections | Groups | Distinct notes |
|---|---|---:|
| S08: animal/chicken topics, including the synthetic food/domestic-animal node | G11, G31 | 60 |
| S19: appreciation, positive feelings, greetings, hopes and aspirations | G04, G13, G17, G25, G50 | 27 |
| S14: Nostr and GrowNostr | G22, G23 | 24 |
| S06: coffee, coffee businesses/hashtags and drinking | G03, G29, G40, G44 | 22 |
| S07: food and culinary topics | G06 | 14 |
| S12: breakfast, mornings and sleep | G16, G21, G46 | 13 |

No additional synthetic section meanings were generated. This is one rerun,
not a further contraction or a completed root-selection loop. The unchanged
58-note definition remains available through its original native receipt.

One new 768-dimensional SSE row was encoded. Its complete input has 213 tokens,
below the fixed 512-token limit. Worker source hash and Torch/Transformers/
Tokenizers versions match the source encoding. The 615 retained input vectors
are unchanged; aliases give 613 unique vectors in the HDBSCAN calculation.
There were zero additional teacher calls or paid charges.

Artifacts are retained in
`target/food-drink-s05-recluster-v1/`: `replacement.json`, the single worker
job/receipt, `request.json`, `result.json`, `analysis.json`, and
`food-drink-100-after-s05.svg`, `.png` and `.md`. All 51 group labels, exact
40-section coverage and original-ID removal were verified; the PNG was
visually inspected. Original source state remains unchanged. The 15 focused
checks also passed on the combined local main checkout.