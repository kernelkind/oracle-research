# TEv4.1 — Did Clearer Masks Produce Better Semantic Vectors?

## Answer

No—not reliably.

The new prompts made several masks easier for a person to understand. But the
extra words used to clarify a meaning also changed the resulting SSE vector.
In two important cases, those extra words became more influential than the
relationship we wanted the vector to represent.

The clearest example is the retirement note:

- The old mask said only `This will be the first steps to my non consumption
  based retirement.` The word `This` was ambiguous by itself.
- The new mask clarified that `This` meant the author's geothermal,
  solar-powered greenhouse.
- After that clarification, the vector retrieved solar panels, greenhouses,
  and Bitcoin mining before retirement content.

So a mask that reconstructs a takeaway clearly for a person is not necessarily
a mask that isolates that takeaway's desired semantic direction for SSE.

## What the experiment tested

The pipeline represents one meaning from a note in three steps:

1. A language model writes a plain-language **takeaway** describing one meaning
   communicated by the note.
2. A second language-model call selects a **mask**: the exact fragments of the
   original note that support that takeaway.
3. SSE receives the complete note plus that mask. It produces a **vector** from
   its contextual representations of the selected tokens.

We then compare vectors with cosine similarity. A higher cosine means two
vectors point in more nearly the same direction in the embedding space.

TEv2 and TEv3.1 contained three suspicious results:

- **Failure #3:** `they want to control everything` matched automatic backups.
- **Failure #5:** an autonomy statement remained unexpectedly close to coffee
  vectors from other notes. Its own source note also discussed coffee.
- **Failure #6:** a retirement statement remained close to greenhouse and
  energy vectors from other notes. Its own source note discussed a greenhouse.

One possible explanation was that the masks were not self-contained. Failure
#3 left `they` unresolved, and Failure #6 left `This` unresolved. TEv4.1 tested
whether the newer TPv3.81 takeaway prompt and MPv3.3 mask prompt would repair
those vector neighborhoods.

This experiment changes both prompts together. It tests the new
takeaway-and-mask pipeline as one unit; it does not isolate the takeaway prompt
from the mask prompt.

## Result at a glance

| Case | What the new extraction changed | Result |
|---|---|---|
| #3 — control and surveillance | Added proprietary operating systems, telemetry, device access, and `tech surveillance state` to resolve `they` | Automatic backups fell from rank 2 to rank 43, but generic software and platform content took over. The failure changed form. |
| #5 — autonomy and coffee | Produced two overlapping autonomy vectors, one of which exactly retained the old mask | The retained vector's coffee similarity was exactly unchanged; the new narrower vector was more coffee-heavy. |
| #6 — greenhouse and retirement | Added the geothermal, solar-powered greenhouse to resolve `This` | Solar, greenhouse, and mining content dominated. Retrieval of retirement meanings became worse. |

## What stayed controlled

TEv3.1 and TEv4.1 use the same:

- ordered 50 notes;
- SSE checkpoint;
- Sentence-T5 base model;
- worker implementation;
- 768-dimensional output;
- inference batch size.

Their note-set SHA-256 is:

`c7064a8eff5826273fc514ab47ee7b7cd1f91c1f994e3de6d2887d23c8843c85`

TEv4.1 regenerated every takeaway and mask with:

- TPv3.81;
- MPv3.3;
- `gpt-5.6-sol` at `max` reasoning;
- one fresh model process for every takeaway call and every mask call.

No generated result received a subjective correction pass. One mask response
contained a non-exact substring. Mechanical validation rejected it, and a
fresh retry succeeded. The rejected attempt remains in the audit log.

The old prompts produced 131 vectors. The new prompts produced 194. Because
the set of vectors being compared changed, a rank change alone cannot identify
its cause. The case analyses therefore also use raw cosine values,
byte-identical candidate vectors, and direct comparisons between old and new
vectors.

## Failure #3 — Control and Surveillance

### Before

TEv3.1 represented the target using only five selected tokens:

> they want to control everything

That vector's second-nearest cross-note result was the unrelated statement that
Molly supports automatic backups, at cosine `0.4175`.

### After

TPv3.81 rendered the unidentified actors descriptively as forces behind
proprietary-technology surveillance. MPv3.3 selected 55 tokens covering:

- `they want to control everything`;
- proprietary operating systems;
- operating-system telemetry and access to device data;
- `this tech surveillance state`.

The old and new target vectors have cosine `0.5209`. The clarification
therefore changed the vector substantially.

The automatic-backup result fell from rank 2 at `0.4175` to rank 43 at
`0.1723`. That sounds like a repair, but both the target mask and the
automatic-backup candidate's mask changed. This comparison alone cannot tell
us which change caused the improvement.

Two candidate vectors remained byte-identical between TEv3.1 and TEv4.1. They
isolate how changing the target moved it:

| Byte-identical candidate | TEv3.1 target | TEv4.1 target |
|---|---:|---:|
| Government seeks to eliminate anonymity and identify citizens | `0.5067` | `0.3327` |
| Entire software stack is free and open source | `0.3763` | `0.4650` |

The clarified target became less similar to direct government-control content
and more similar to generic free-software content.

Its new rank-1 result was an iMessage implementation that works on any
platform, at `0.6889`. We compared both versions of the target with both
versions of the iMessage candidate:

| Target vector | iMessage candidate vector | Cosine |
|---|---|---:|
| Old | Old combined candidate | `0.4005` |
| Old | New platform-only candidate | `0.2810` |
| New | Old combined candidate | `0.6599` |
| New | New platform-only candidate | `0.6889` |

The large increase appears even when the old iMessage candidate is held fixed:
`0.4005` becomes `0.6599`. The expanded target mask—not merely the new iMessage
decomposition—shifted the vector toward operating systems and platforms.

### What this means

The new extraction weakened one false match, but it did not isolate systemic
control and surveillance. Generic platform, Matrix, and free-software content
moved upward while several direct control and surveillance signals moved
downward. Failure #3 changed form rather than being repaired.

## Failure #5 — Autonomy and Coffee

### Before

TEv3.1 represented this meaning:

> Only the things you choose without pressure define you. The rest is a facade.

The source note also discussed flavored coffee. Even after TEv3.1 added enough
autonomy coverage for relevant results to occupy the leading ranks, a
coffee-roasting vector remained unexpectedly close.

### After

TPv3.81 produced two overlapping autonomy takeaways:

1. Free choices reveal a person's true character.
2. Choices made under pressure create a false outward image rather than
   authentically defining the person.

The second takeaway retained exactly the same selected tokens as TEv3.1:

> Only the things you choose without pressure define you. The rest is a facade.

Its target vector is byte-identical to the TEv3.1 target. The suspicious
coffee-roasting vector is also byte-identical. Their cosine is therefore
exactly unchanged at `0.4347354678`.

For this retained full-mask vector, relevant autonomy examples still rank
ahead of the coffee vector because the 50-note corpus contains appropriate
coverage. The coffee vector remains rank 10.

The new first-clause-only autonomy vector behaves worse. Four coffee takeaways
occupy ranks 4 and 8–10 in its neighborhood.

### What this means

For the retained full-mask vector, TEv4.1 preserves TEv3.1's conclusion: sparse
coverage explained most of the originally misleading ranking, but the residual
coffee similarity remains.

The new extraction does not repair that residual relationship. The pipeline
now emits both autonomy vectors: the retained full-mask vector and a second,
overlapping vector whose neighborhood is more coffee-heavy. The same source
meaning is therefore represented twice with materially different
neighborhoods.

## Failure #6 — Greenhouse and Retirement

### Before

TEv3.1 selected only:

> This will be the first steps to my non consumption based retirement.

`This` was not understandable without the rest of the note. The old vector
nonetheless contained useful retirement signal.

### After

MPv3.3 resolved the reference by additionally selecting:

> our geothermal solar powered greenhouse

The new target remains related to the old target at cosine `0.8002`, but it
moves sharply toward greenhouse and energy content.

Against a byte-identical future-solar vector, cosine rises from `0.3690` to
`0.6565`.

Holding TEv3.1's vector about leaving the conventional American grind fixed,
cosine falls from `0.3957` to `0.2486`. The regenerated TEv4.1 leaving-grind
vector is not byte-identical and ranks 32 at `0.2282`.

The first eleven TEv4.1 neighbors concern solar energy, greenhouses, or Bitcoin
mining. The first explicit financial-independence result is rank 12. Direct
retirement results begin at rank 13.

### What this means

The mask now tells a person what `This` means, but that clarification inserts
the greenhouse's subject matter into the selected evidence. SSE follows that
subject matter strongly. Failure #6 became worse for retrieving retirement and
non-consumption meanings.

## What changed across the complete 50-note run

TPv3.81 produced more vectors and much more overlap between masks from the same
note:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |

Forty of the 50 notes gained takeaways; none lost takeaways.

Overlap is not automatically wrong. One source passage can support several
distinct meanings. But this amount of overlap creates many closely related
vectors, adds computation, and makes rank-only comparisons misleading.

Despite the additional vectors, the aggregate cross-note cosine distribution
barely changed:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

These aggregate measurements do not show a global geometry improvement.

## Other extraction problems found during the audit

The prompts also produced failures outside the three target cases:

- A takeaway says that a post links to a Doom source-code repository and a
  separate social-media post, but its mask selects the licensing sentence
  rather than either excluded URL.
- A takeaway about a Hacker News link is masked only by `Comments`.
- A takeaway about a GitHub link is masked only by `pypush`.
- The product name `Flexicables` is rewritten as the generic phrase “Flexible
  cables.”

The first three reveal a direct mismatch between the prompts:

1. TPv3.81 can preserve substantive meaning contributed by a URL.
2. MPv3.3 forbids selecting URLs.
3. The mask generator therefore sometimes substitutes nearby words that do not
   contain the link's meaning.

The validator confirms that every returned fragment exists in the source and
appears in a valid order. It cannot mechanically determine whether those
fragments actually preserve the takeaway's meaning. That requires semantic
evaluation.

## Conclusion

TEv4.1 tested this hypothesis:

> Resolving ambiguous masks by adding all source context needed to reconstruct
> the takeaway will improve the SSE geometry.

The evidence does not support it.

TPv3.81 and MPv3.3 were designed to make takeaways and masks self-contained.
They did clarify the inspected `they` and `This` references, but the audit shows
that they do not work reliably across all notes. More importantly, adding
clarifying source context changes the SSE vector. The added context can
outweigh the relationship the takeaway was intended to represent.

The new extraction pipeline:

- does not repair Failure #3;
- preserves only one controlled branch of Failure #5, while adding a worse
  overlapping branch;
- makes Failure #6 worse for its intended retirement meaning;
- creates substantially more overlapping vectors;
- contains additional unsupported or distorted extractions.

This does not reject communicated-meaning vectors or SSE generally. It shows a
specific mismatch:

> A mask optimized to reconstruct a human-readable takeaway is not necessarily
> a mask that isolates the desired semantic direction for this SSE checkpoint.

Both prompts changed together, generation was a single run, and these 50 notes
are a diagnostic set rather than a representative sample. The experiment does
not support prompt-level causal claims or population-level accuracy claims.

## Preserved evidence

The immutable run contains:

- the exact prompts and ordered input;
- raw generation logs from every fresh-context call;
- the mechanically rejected mask attempt;
- the source-bound proposal and SSE worker request;
- raw vectors and the worker receipt;
- the complete pairwise cosine analysis.

It is preserved in
[`communicated-meaning-tev4-1`](../../../sse_multivector/baselines/communicated-meaning-tev4-1/).
