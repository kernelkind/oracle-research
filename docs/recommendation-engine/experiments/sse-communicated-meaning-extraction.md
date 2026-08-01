# TEv4.1 — Did Clearer Masks Produce Better Semantic Vectors?

## Result

No—not reliably.

The new prompts made some masks clearer to a person. But the words added to
clarify a meaning also became part of the vector's meaning. In the control note,
generic software and platform content took over. In the retirement note, solar,
greenhouse, and mining content took over.

The central finding is:

> A mask that clearly reconstructs a takeaway for a person is not necessarily a
> mask that isolates that takeaway's desired semantic direction for SSE.

## What changed

The pipeline has three operations:

1. A language model reads a complete note and writes its communicated meanings
   as plain-language **takeaways**.
2. A separate language-model call receives one takeaway and the complete note.
   It selects a **mask**: exact fragments from the note that support the whole
   takeaway.
3. SSE receives the complete note and the mask. It produces a **vector** from
   its contextual representations of the selected tokens.

TEv3.1 used the old takeaway and mask prompts. TEv4.1 regenerated every
takeaway and mask with TPv3.81 and MPv3.3. The ordered 50 notes, SSE checkpoint,
base model, worker, vector dimensions, and inference batch size did not change.

A higher cosine means two vectors point in more nearly the same direction. Rank
means where one vector appears among vectors from other notes.

TEv3.1 contains 131 vectors; TEv4.1 contains 194. A rank change by itself is
therefore not a controlled comparison. The cases below also compare raw cosine
values and hold particular candidate vectors fixed where possible.

## Failure #3 — Control and Surveillance

**Complete source note**

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

**TEv3.1 extraction**

- Takeaway: `Unspecified actors want to control everything.`
- Mask: `they want to control everything`
- Selected tokens: 5

**TEv4.1 extraction**

- Takeaway: `The author believes that the forces behind pervasive
  proprietary-technology surveillance seek total control.`
- Mask fragments:
  - `they want to control everything`
  - `a proprietary OS ( #Windows, #macOS, #iOS, #Android, etc.)`
  - `all those OS's are saturated with telemetry mechanisms and APIs that have
    access to everything on your devices`
  - `this tech surveillance state`
- Selected tokens: 55

TPv3.81 did not identify who `they` are. It rendered them descriptively from
the rest of the post. The old and new target vectors have cosine `0.5209`, so
the new mask changed the target substantially.

**Measured changes**

| Comparison | TEv3.1 | TEv4.1 | What was held fixed? |
|---|---:|---:|---|
| Molly supports automatic backups | rank 2, `0.4175` | rank 43, `0.1723` | Neither candidate nor target |
| Government seeks to eliminate anonymity and identify citizens | `0.5067` | `0.3327` | Candidate vector was byte-identical |
| Entire software stack is free and open source | `0.3763` | `0.4650` | Candidate vector was byte-identical |

The automatic-backup result improved, but its mask also changed. That row alone
cannot identify the cause. The two byte-identical controls show that the new
target itself moved away from direct government-control content and toward
generic free-software content.

The new rank-1 result was an iMessage implementation that works on any
platform, at `0.6889`. Comparing every old/new combination isolates where that
increase came from:

| Target vector | iMessage candidate vector | Cosine |
|---|---|---:|
| Old | Old combined candidate | `0.4005` |
| Old | New platform-only candidate | `0.2810` |
| New | Old combined candidate | `0.6599` |
| New | New platform-only candidate | `0.6889` |

Even with the old iMessage candidate held fixed, changing the target raises the
cosine from `0.4005` to `0.6599`. The target's added operating-system and
platform context caused most of the increase.

**Interpretation**

The new extraction pushed automatic backups from rank 2 to rank 43, but it did
not isolate systemic control and surveillance. Generic platform, Matrix, and
free-software content moved upward while several direct control and
surveillance signals moved downward. Failure #3 changed form rather than being
repaired.

## Failure #5 — Autonomy and Coffee

**Complete source note**

> Annie's Saturday Morning Thoughts
>
> Don't assume that everyone who agrees with you in public agrees with you in
> private. 😏
>
> The wren on the fence has been chirping for a while. Must have good lungs.
>
> Only the things you choose without pressure define you. The rest is a facade.
> 🤥
>
> Flavored coffee is nice but can get old if you have it every day.
>
> Sunshine, cool breeze, doves, wrens, robins, squirrels, shade from an oak tree
> and a crossvine in bloom. This is the recipe for a good Saturday. 🤗

**TEv3.1 extraction**

- Takeaway: `Only choices made without pressure define a person; the rest is a
  facade.`
- Mask:
  - `Only the things you choose without pressure define you.`
  - `The rest is a facade.`

**TEv4.1 extraction**

TPv3.81 represented the source passage twice:

1. Takeaway: `The author believes that only choices made freely and without
   pressure reveal a person’s true character.`
   - Mask: `Only the things you choose without pressure define you.`
2. Takeaway: `The author believes that choices made under pressure create a
   false outward image rather than authentically defining the person.`
   - Mask: `Only the things you choose without pressure define you. The rest is
     a facade.`

The second TEv4.1 mask selects exactly the same tokens as the TEv3.1 mask. Its
target vector is byte-identical to the old target. The suspicious
coffee-roasting candidate is also byte-identical.

**Measured changes**

| Vector | Result |
|---|---|
| Retained full-mask autonomy vector ↔ coffee-roasting vector | Cosine remains exactly `0.4347354678`; coffee remains rank 10 |
| New first-clause-only autonomy vector | Coffee takeaways occupy ranks 4 and 8–10 |

Relevant autonomy examples still rank ahead of the coffee vector for the
retained full-mask target. TEv3.1 had added appropriate autonomy coverage, and
that coverage still prevents the old coffee relationship from dominating its
leading results.

**Interpretation**

For the retained vector, sparse coverage explained most of TEv2's misleading
ranking, but the residual coffee similarity never changed. The new pipeline
also emits a second, overlapping autonomy vector whose neighborhood is more
coffee-heavy. One source meaning is now represented twice with materially
different neighborhoods. Failure #5 was not repaired.

## Failure #6 — Greenhouse and Retirement

**Complete source note**

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> This will be the first steps to my non consumption based retirement.
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**TEv3.1 extraction**

- Takeaway: `The greenhouse project is the author's first step toward a
  non-consumption-based retirement.`
- Mask: `This will be the first steps to my non consumption based retirement.`

The mask did not say what `This` referred to, but the old vector still retained
useful retirement signal.

**TEv4.1 extraction**

- Takeaway: `The author views the greenhouse project as an initial step toward
  a retirement that is not consumption-based.`
- Mask fragments:
  - `our geothermal solar powered greenhouse`
  - `This will be the first steps to my non consumption based retirement.`

The new mask tells a person what `This` means. The old and new target vectors
have cosine `0.8002`: they remain related, but the added greenhouse fragment
moves the new vector sharply toward greenhouse and energy content.

**Measured changes**

| Comparison | TEv3.1 target | TEv4.1 target | What was held fixed? |
|---|---:|---:|---|
| Future solar generation | `0.3690` | `0.6565` | Candidate vector was byte-identical |
| Leaving the conventional American grind | `0.3957` | `0.2486` | TEv3.1 candidate vector was held fixed |

The regenerated TEv4.1 leaving-grind vector is not byte-identical. It ranks 32
at `0.2282`.

The first eleven TEv4.1 neighbors concern solar energy, greenhouses, or Bitcoin
mining. The first explicit financial-independence result is rank 12. Direct
retirement results begin at rank 13.

**Interpretation**

The added fragment correctly supplies the missing referent, but it also inserts
the greenhouse's subject matter into the evidence SSE pools. SSE follows that
subject matter strongly. Failure #6 became worse for retrieving retirement and
non-consumption meanings.

## Complete-run measurements

TPv3.81 produced more vectors and much more overlap between masks from the same
note:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |

Forty of the 50 notes gained takeaways; none lost takeaways. The 6 overlapping
pairs in TEv3.1 came from 193 total same-note pairs. The 192 in TEv4.1 came from
410 total same-note pairs.

Overlap is not automatically wrong: one source passage can support several
distinct meanings. But this amount of overlap creates many closely related
vectors, adds computation, and makes rank-only comparisons misleading.

The aggregate cross-note cosine distribution barely changed:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

These aggregate measurements do not show a global geometry improvement.

## Other extraction failures

| Generated takeaway | Selected mask | Problem |
|---|---|---|
| `The post links to id Software’s Doom source-code repository and a separate Doom-related social-media post as references for the licensing update.` | `Doom 1 and 2 are now officially licensed under the #GPL, no longer dual-licensed with the DSL :)` | The licensing sentence does not contain either link's meaning. |
| `The post also links to a Hacker News discussion of the article.` | `Comments` | `Comments` does not identify Hacker News or the article. |
| `The author provides a link to the pypush project’s GitHub repository.` | `pypush` | The project name does not establish that the omitted link is a GitHub repository. |
| `Flexible cables have been installed as part of a greenhouse project shared by the author and others.` | `Flexicables installed for our ` + `greenhouse.` | The product name `Flexicables` was rewritten as generic flexible cables. |

The first three failures expose a mismatch between the prompts:

1. TPv3.81 can preserve meaning contributed by a URL.
2. MPv3.3 forbids selecting URLs.
3. The mask generator sometimes substitutes nearby words that do not contain
   the link's meaning.

The validator proves that every selected fragment exists in the source and is
in the correct order. It cannot prove that those fragments preserve the
takeaway's meaning. That requires semantic evaluation.

## Conclusion and limits

TEv4.1 tested this hypothesis:

> Resolving ambiguous masks by adding all source context needed to reconstruct
> the takeaway will improve the SSE geometry.

The evidence does not support it.

The new extraction pipeline:

- did not repair Failure #3;
- retained one unchanged branch of Failure #5 while adding a worse overlapping
  branch;
- made Failure #6 worse for its intended retirement meaning;
- created substantially more overlapping vectors;
- produced additional unsupported or distorted extractions.

This does not reject communicated-meaning vectors or SSE generally. It rejects
the simpler assumption that a more self-contained source mask will necessarily
produce a better-isolated SSE vector.

Both prompts changed together, so TEv4.1 cannot attribute a result to TPv3.81
or MPv3.3 alone. Generation was one run, and these 50 notes are a diagnostic set
rather than a representative sample. The experiment does not establish
population-level accuracy.

## Exact controls and preserved evidence

The ordered note set has SHA-256:

`c7064a8eff5826273fc514ab47ee7b7cd1f91c1f994e3de6d2887d23c8843c85`

TEv4.1 used:

- TPv3.81;
- MPv3.3;
- `gpt-5.6-sol` at `max` reasoning;
- one fresh model process for every takeaway and mask call;
- the same SSE checkpoint, Sentence-T5 base model, worker, 768-dimensional
  output, and inference batch size as TEv3.1.

No generated result received a subjective correction pass. One mask response
contained a non-exact substring. Mechanical validation rejected it, and a
fresh retry succeeded. The rejected attempt remains in the audit log.

The immutable run contains:

- the exact prompts and ordered input;
- raw generation logs from every fresh-context call;
- the mechanically rejected mask attempt;
- the source-bound proposal and SSE worker request;
- raw vectors and the worker receipt;
- the complete pairwise cosine analysis.

It is preserved in
[`communicated-meaning-tev4-1`](../../../sse_multivector/baselines/communicated-meaning-tev4-1/).
