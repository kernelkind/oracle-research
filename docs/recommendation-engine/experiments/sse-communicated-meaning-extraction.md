# TEv4.1 — Self-Contained Extraction Diagnostic

## Question

On TEv3.1's final 50-note corpus, does replacing the old extraction prompts
with TPv3.81 and MPv3.3 repair the three suspicious communicated-meaning
vectors identified in TEv2?

This tests the new takeaway-and-mask pipeline as one unit. It does not isolate
the takeaway prompt from the mask prompt.

## Controlled inputs

TEv3.1 and TEv4.1 use the same ordered 50 notes, SSE checkpoint, base model,
worker, 768-dimensional output, and batch size. Their note-set SHA-256 is:

`c7064a8eff5826273fc514ab47ee7b7cd1f91c1f994e3de6d2887d23c8843c85`

TEv4.1 regenerated every takeaway and mask with:

- TPv3.81;
- MPv3.3;
- `gpt-5.6-sol` at `max` reasoning;
- one fresh model process per takeaway or mask call.

No generated result received a subjective correction pass. One mask response
contained a non-exact substring, was rejected mechanically, and succeeded on a
fresh retry. The failed attempt remains in the audit log.

The old prompts produced 131 vectors. The new prompts produced 194. Therefore,
rank changes alone cannot identify a cause; the comparisons below also use raw
cosines and byte-identical control vectors where possible.

## Results

### Failure #3 — control and surveillance

TEv3.1 represented the target with only:

> they want to control everything

TPv3.81 rendered the unidentified actors descriptively as forces behind
proprietary-technology surveillance. MPv3.3 selected 55 tokens spanning the
control statement, proprietary operating systems, telemetry and device access,
and the phrase `tech surveillance state`. The old and new target vectors have
cosine `0.5209`, so this was a substantial change in direction.

The old automatic-backup symptom weakened from rank 2 at `0.4175` to rank 43 at
`0.1723`. Both that candidate's mask and the target mask changed, so that result
alone is not a controlled attribution.

Two unchanged candidate vectors show how the target itself moved:

| Byte-identical candidate | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Government seeks to eliminate anonymity and identify citizens | `0.5067` | `0.3327` |
| Entire software stack is free and open source | `0.3763` | `0.4650` |

The new rank-1 result is an iMessage implementation that works on any platform,
at `0.6889`. A four-way vector comparison shows that this came primarily from
the expanded target mask:

| Target | iMessage candidate | Cosine |
|---|---|---:|
| Old | Old combined candidate | `0.4005` |
| Old | New platform-only candidate | `0.2810` |
| New | Old combined candidate | `0.6599` |
| New | New platform-only candidate | `0.6889` |

The new mask removed one bad neighbor but shifted the target toward operating
systems, platforms, and free software. Direct control and surveillance signals
remained, but several fell substantially. Failure #3 changed form rather than
being repaired.

### Failure #5 — autonomy and coffee

TPv3.81 split the old autonomy takeaway into two related takeaways. One retained
the exact old selected tokens:

> Only the things you choose without pressure define you. The rest is a facade.

That target vector is byte-identical to TEv3.1. The coffee-roasting vector that
previously looked suspicious is also byte-identical. Their cosine therefore
remains exactly `0.4347354678`.

Relevant autonomy examples still rank ahead of that coffee vector because the
50-note corpus contains appropriate coverage. The new extraction also creates
additional, overlapping autonomy and coffee variants; it does not remove the
underlying coffee relationship.

For the retained full-mask vector, TEv4.1 preserves TEv3.1's result: sparse
coverage explained most of the misleading ranking, while the residual coffee
similarity remains. The new first-clause-only autonomy vector regresses: four
coffee takeaways occupy ranks 4 and 8–10. The conclusion therefore depends on
which of TPv3.81's two overlapping representations is used.

### Failure #6 — greenhouse and retirement

TEv3.1 selected only:

> This will be the first steps to my non consumption based retirement.

MPv3.3 correctly resolved what `This` referred to by also selecting:

> our geothermal solar powered greenhouse

The new target remains related to the old target at cosine `0.8002`, but its
ranking moves sharply toward greenhouse and energy content.

Against a byte-identical future-solar vector, cosine rises from `0.3690` to
`0.6565`. Holding TEv3.1's vector about leaving the conventional American grind
fixed, cosine falls from `0.3957` to `0.2486`. The regenerated TEv4.1
leaving-grind vector is not byte-identical and ranks 32 at `0.2282`.

In TEv4.1, the first eleven neighbors concern solar energy, greenhouses, or
Bitcoin mining. The first explicit financial-independence result is rank 12;
direct retirement results begin at rank 13.

The mask is more understandable to a human, but the added referent dominates
the encoded direction. Failure #6 became worse for retrieving retirement and
non-consumption meanings.

## Additional observation

TPv3.81 produces more and more-overlapping evidence units:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |

Overlap is not automatically incorrect: one source passage can support several
distinct meanings. It does mean the new pipeline creates many closely related
vectors, adds computation, and makes rank-only comparisons misleading.

The aggregate cross-note cosine distribution barely changes:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

This is not evidence of a global geometry improvement. Forty of 50 notes gain
takeaways and none lose them, so the added granularity also changes the set of
possible neighbors.

A focused audit found extraction failures outside the three target cases:

- a takeaway claiming that a post links to two Doom repositories is masked by
  the licensing sentence rather than the excluded URLs;
- a Hacker News-link takeaway is masked only by `Comments`;
- a GitHub-link takeaway is masked only by `pypush`;
- `Flexicables` is rewritten as generic “Flexible cables.”

The first three expose a direct mismatch: TPv3.81 can emit the meaning of a
link, while MPv3.3 forbids selecting the URL that supplies that meaning.
Mechanical source validation cannot detect this semantic failure.

## Conclusion

The tested hypothesis was too simple:

> Resolving ambiguous masks by adding all source context needed to reconstruct
> the takeaway will improve the SSE geometry.

TEv4.1 does not support that hypothesis. TPv3.81 and MPv3.3 were designed to
improve textual self-containment and do so in the inspected referent cases, but
the audit shows that they do not do so reliably. Added source context is also
not neutral to SSE. It becomes part of the vector and can outweigh the
relationship the takeaway was meant to represent.

This does not reject communicated-meaning vectors or SSE generally. It shows
that the new extraction pipeline repairs neither Failure #3 nor Failure #6 and
preserves only one controlled branch of Failure #5. A mask optimized to
reconstruct a human-readable takeaway is not necessarily a mask that isolates
the desired semantic direction for this SSE checkpoint.

Both prompts changed together, generation was a single run, and these 50 notes
are a diagnostic set rather than a representative sample. The results do not
support prompt-level causal claims or population-level accuracy claims.

The immutable run, including prompts, raw generation logs, the rejected mask
attempt, source-bound proposal, vectors, receipt, and complete pairwise
analysis, is preserved in
[`communicated-meaning-tev4-1`](../../../sse_multivector/baselines/communicated-meaning-tev4-1/).
