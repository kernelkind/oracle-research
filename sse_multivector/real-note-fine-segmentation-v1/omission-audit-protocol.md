# Missing cross-note partners

Question: among masks absent from the baseline's multi-note segments, can we find masks that have suitable partners in other notes?

This follows the user's positive assessment of the 43 displayed baseline segments. It does not change that assessment, the corpus, the masks, the vectors, or any HDBSCAN result.

## What is counted

The baseline contains 945 vectors:

- 150 in segments containing more than one note;
- 633 in segments containing only one note;
- 162 assigned to no segment.

The latter two sets give 795 mask vectors to investigate. These represent 772 distinct source masks: some generated subjects selected exactly the same source ranges. Preserve those aliases. A mask's absence from a multi-note segment is not itself an error.

Each proposed pair contains vectors from different notes, with at least one of these 795 vectors. There are 428,086 such unordered vector pairs. Each pair is counted once even if several methods suggest it. Sampling is by vector ID, so exact-source aliases can receive extra weight; results must not be presented as a uniform sample of distinct source masks. This excludes possible omissions involving only masks already in multi-note segments; it is not a complete audit of every split in the partition.

## Finding possible partners

Use three sources before making any new judgments:

1. Every eligible pair placed together in the saved leaf or density HDBSCAN result.
2. For each of the 795 masks, its highest-cosine mask from each of its three closest other notes. Same-note duplicates cannot fill these three places.
3. Four fresh, isolated text-only calls. Each receives the complete mask catalog and a disjoint quarter of the 795 target IDs. It proposes up to three partners from different notes for each target. It sees no vectors, cosine scores, subject descriptions, existing segments, or earlier judgments.

This produces suggestions, not accepted groups. Empty text-only answers do not prove that no partner exists.

Technical gate: the first text call covered all 199 assigned IDs but suggested four same-note partners. Preserve that raw response. Exclude same-note/self suggestions mechanically, recording each excluded proposal and reason; do not retry model calls for note-ID filtering. Unknown IDs, malformed responses, or missing target records still block collection. This rule was recorded before the other three text calls and before sampling or semantic judgments. If multiple suggested partners come from the same other note, retain all distinct eligible pairs and record the instruction violation. Otherwise a discarded but genuinely proposed pair could incorrectly enter the random "unsuggested" sample. Deduplicate only identical unordered pairs.

## Checking suggestions and blind spots

Freeze the combined suggestions. With seed `20260908`, independently sample without replacement:

- 64 pairs from the combined suggestions;
- 64 pairs from all remaining eligible pairs.

Record both complete populations, selected IDs, and each pair's sampling probability before review. Mix the 128 pairs into one review set so the screen does not reveal their origin. Do not add unusually convincing examples to this sample afterward.

Two fresh isolated assessments judge every sampled pair using the existing question:

> Are all instances recognizable as refinements of one fine subject?

They receive only the masks, opaque IDs, and the existing Valid / Invalid / Uncertain definitions. They do not receive cosine scores, proposal sources, original note context, or one another's answers. These are separate calls to the same model, not independent human ground truth. Preserve both answers. The primary assistant inspects the evidence and records any disagreement separately. Surface unresolved judgments to the user through the masks-only review tool; do not enter user decisions on their behalf.

Run the first text call and the first assessment batches before expanding, checking response integrity and evidence presentation. This is a technical gate, not permission to change the sample or judgment criterion based on which pairs pass.

## What the result can establish

A valid pair demonstrates an available cross-note relationship for a mask the baseline left without a multi-note segment. Report the exact masks, their source-note IDs, and how they were treated by the baseline. Count demonstrated pairs, distinct affected masks, and distinct affected notes separately.

Pairwise compatibility does not require all compatible masks to share one segment. Do not chain approved pairs into larger groups without reviewing those groups. Do not count pairs as distinct missing fine subjects.

Report judgments on the random unsuggested pairs even if none pass. A small sample cannot certify that the rest contain no omissions. Sampling probabilities permit pair-level estimates under stated judgment assumptions, but they do not supply a denominator for all valid groupings or an estimate of the percentage of masks with no possible partner. This first audit will report demonstrated omissions and its inspected scope, not a fabricated overall recall score.

## Preservation and resources

Keep all raw calls, exact prompts, sampling records, and assessments separately from the frozen input artifacts and existing user sessions. Use the existing subscription runner with Astra low, fresh context per call, no tools/web, and the existing resource guards. No new extraction, encoding, rented compute, or paid API resources. Local pair calculations need only the existing 945-by-768 vector matrix.

The approach combines multiple proposal sources with random inspection outside their union. This addresses the incompleteness of pooled judgments described in [NIST's pooled-versus-sampled comparison](https://www.nist.gov/publications/comparison-pooled-and-sampled-relevance-judgments-trec-2006-terabyte-track); it does not import information-retrieval recall as a clustering metric.
