# TEv4.1 — Did clearer masks produce better semantic vectors?

## Status

Executed historical diagnostic using communicated takeaways as vector units.
It explains one transition toward atomic-subject masks, but it does not define
or validate the current intended representation.

## Result

TEv4.1 did not support the hypothesis.

TEv4.1 tested whether making a mask self-contained would make SSE represent its
takeaway more cleanly. The evidence shows that adding a referent to a mask can
move its vector toward the referent's subject matter. It does not establish that
self-contained masks are always worse, nor does it establish the current
atomic-subject design.

The main argument below is deliberately sequential. Each claim presents its
evidence before its analysis. The selected dataset preserves the full 50-note input and final measurements.
Representative evidence follows each claim.

## What the experiment changed

The pipeline is:

1. TPv3.81 reads one complete note and generates takeaways.
2. A fresh MPv3.3 call receives one takeaway and the complete note. It selects
   exact source fragments as the mask.
3. SSE encodes the complete note, takes the contextual token representations
   selected by the mask, and pools them into one vector.

The takeaway text itself is not passed to SSE. It only guides mask selection.
Within the same fixed SSE configuration, identical source text and identical
masks produce identical vectors even if the takeaways are worded differently.
In every note below, `⟦…⟧` marks text selected by the mask; the surrounding
text is visible context that was not selected for pooling.

TEv3.1 and TEv4.1 used the same ordered 50 notes, SSE checkpoint,
Sentence-T5 base model, worker, 768 dimensions, and inference batch size.
TEv3.1 used the previous takeaways and masks. TEv4.1 regenerated all of them
with TPv3.81 and MPv3.3.

A higher cosine means two vectors point in more nearly the same direction.
Rank is the vector's position among vectors from other notes.

TEv3.1 has 131 vectors and TEv4.1 has 194. Therefore, a rank change by itself
is not a controlled comparison: the number and identity of competing vectors
also changed. The cases below use raw cosines and byte-identical candidate
vectors wherever possible.

## Logical argument

### Claim 1 — `RET-NEW` adds solar-greenhouse text to `RET-OLD`

#### Evidence

Both retirement target vectors came from this exact note:

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> This will be the first steps to my non consumption based retirement.
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**`RET-OLD` — TEv3.1 target mask:**

> Flexicables installed for our geothermal solar powered greenhouse. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

**`RET-NEW` — TEv4.1 target mask:**

> Flexicables installed for ⟦our geothermal solar powered greenhouse⟧. The
> greenhouse they have in Aliance Nebraska grows pineapple and dates and
> citrus.
> ⟦This will be the first steps to my non consumption based retirement.⟧
> https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

The note, SSE checkpoint, and inference configuration were fixed. `RET-OLD` and
`RET-NEW` have cosine `0.8002`, so adding the referent changed the vector.

#### Analysis

This evidence establishes the intervention: `RET-NEW` directly pooled the words
`our geothermal solar powered greenhouse`, while `RET-OLD` did not. It does not
yet establish whether that change was helpful or harmful.

### Claim 2 — `RET-NEW` became more similar to one fixed solar vector

#### Evidence

The controlled candidate was this one-sentence note:

> ⟦Solar power will be the vast majority of power generation in the future⟧

Both runs selected that complete sentence. Its vector was byte-identical across
runs. Its cosine to the target was:

| Target | Cosine to the fixed solar candidate |
|---|---:|
| `RET-OLD` | `0.3690` |
| `RET-NEW` | `0.6565` |

#### Analysis

Because the candidate did not change, the target-mask change caused the
increase. This proves only that `RET-NEW` became more similar to this one
solar vector. It does not, by itself, show that retirement meaning became
weaker or that the new vector was worse.

### Claim 3 — `RET-NEW` became less similar to one fixed retirement vector

#### Evidence

The controlled retirement candidate came from this note:

> When I joined my current company, I was provided a retirement packet to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

The fixed candidate vector selected:

> ⟦When I joined my current company, I was provided a retirement packet⟧ to fill
> out.
>
> In it, I wrote that I planned on retiring in 2029, and then declined opening a
> retirement account with them.
>
> #JustBitcoinerThings

The TEv3.1 candidate vector was held fixed while only the target changed:

| Fixed candidate meaning | `RET-OLD` | `RET-NEW` |
|---|---:|---:|
| Receiving a retirement packet | `0.3562099685` | `0.2455033805` |

#### Analysis

This explicitly retirement-related candidate was less similar to `RET-NEW`
than to `RET-OLD`. That is direct retirement evidence, unlike the weaker “break
free from the typical American grind” comparison. It is still only one
candidate and does not establish movement away from every retirement meaning.

Claims 2 and 3 together establish the direction of this one target's movement:
adding the greenhouse referent made it more similar to the fixed solar vector
and less similar to the fixed retirement vector above.

This does not prove that the new vector misrepresented the complete compound
claim. A solar greenhouse genuinely is part of that claim. It shows that making
the mask self-contained traded away similarity to the fixed retirement
representation used in this comparison.

### Claim 4 — `CTRL-NEW` showed the same kind of tradeoff

#### Evidence

Both control targets came from this note:

> they want to control everything..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

**`CTRL-OLD` — TEv3.1 target mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.) then you are missing the bigger picture.. ..all
> those OS's are saturated with telemetry mechanisms and APIs that have access
> to everything on your devices.. ..i'm still on iOS phone-wise, but my days are
> numbered with that.. ..likely moving to #GrapheneOS (although i already try to
> use my phone as little as possible).. ..i've already switched to #Linux
> computer-wise.. ..free and opensource is the only way to navigate this tech
> surveillance state with any level of sovereignty

**`CTRL-NEW` — TEv4.1 target mask:**

> ⟦they want to control everything⟧..
> ..if you think your #Nostr nsec key is safe on ⟦a proprietary OS ( #Windows,
> #macOS, #iOS, #Android, etc.)⟧ then you are missing the bigger picture..
> ..⟦all those OS's are saturated with telemetry mechanisms and APIs that have
> access to everything on your devices⟧.. ..i'm still on iOS phone-wise, but my
> days are numbered with that.. ..likely moving to #GrapheneOS (although i
> already try to use my phone as little as possible).. ..i've already switched
> to #Linux computer-wise.. ..free and opensource is the only way to navigate
> ⟦this tech surveillance state⟧ with any level of sovereignty

Three candidate vectors were held fixed:

1. Direct government control:

   > NEW - ⟦The CCC warns that the German left-green-liberal government wants to
   > "effectively end anonymity" and make all citizens "identifiable at all
   > times and in all places,"⟧ including by opening doors to Palantir and other
   > surveillance software.
   >
   > https://www.ccc.de/en/updates/2024/biometrischer-uberwachungsexzess-der-bundesregierung
   >
   > https://hell.twtr.plus/media/cf6857f1982ee096057b3c09692a162778dd08f6e86e47e845309425238d567a.file

2. Generic free software:

   > ⟦Getting close to 100% of my software stack being free and open source.⟧

3. A cross-platform open-source application:

   > It's ready! ⟦#pypush can now send and receive #iMessage, on any platform,
   > completely server-less and open-source!⟧ 🎉
   >
   > https://github.com/JJTech0130/pypush

Their cosines changed as follows:

| Fixed candidate meaning | `CTRL-OLD` | `CTRL-NEW` |
|---|---:|---:|
| Government ending anonymity | `0.5067` | `0.3327` |
| Free and open-source software stack | `0.3763` | `0.4650` |
| Cross-platform open-source iMessage application | `0.4005` | `0.6599` |

#### Analysis

`CTRL-NEW` was less similar than `CTRL-OLD` to the direct government-control
candidate and more similar than `CTRL-OLD` to the two software candidates.
Because all three candidates were held fixed, the target change caused those
differences.

This is a second concrete example of referent or explanatory source text
changing which part of a compound meaning dominates the resulting geometry. It
does not prove that every self-contained mask behaves this way.

### Claim 5 — TEv4.1 also changed the number of vectors produced per note

#### Evidence

TEv3.1 represented this source passage once:

> ⟦Only the things you choose without pressure define you.⟧ ⟦The rest is a
> facade.⟧

TEv4.1 represented it twice:

> ⟦Only the things you choose without pressure define you.⟧ The rest is a
> facade.

and:

> ⟦Only the things you choose without pressure define you. The rest is a
> facade.⟧

The second TEv4.1 vector is byte-identical to the TEv3.1 vector. The two TEv4.1
vectors have cosine `0.9225` with each other.

Across all 50 notes:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Vectors | 131 | 194 |
| Mean vectors per note | 2.62 | 3.88 |
| Same-note pairs with overlapping selected tokens | 6 | 192 |
| All same-note pairs | 193 | 410 |

Forty notes gained takeaways; no note lost takeaways.

#### Analysis

TEv4.1 was not merely the old decomposition with clearer masks. It also emitted
more meanings and reused source spans much more often. Some overlap can be
legitimate, but the example above gives nearly the same source meaning two
opportunities to enter retrieval results.

Therefore, aggregate TEv3.1-versus-TEv4.1 changes cannot be attributed only to
mask clarification. Controlled target/candidate comparisons are required.

### Claim 6 — Some generated takeaways were not supported by selectable text

#### Evidence

One generated takeaway was:

> The post also links to a Hacker News discussion of the article.

Its complete source and selected mask were:

> Why a spritz of water before grinding coffee yields better results
>
> ⟦Comments⟧ ( https://news.ycombinator.com/item?id=38554310 )
>
> https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/

MPv3.3 was forbidden from selecting URLs. The word `Comments` alone does not
identify Hacker News or the linked article.

#### Analysis

This mask is mechanically valid—the selected substring exists—but it does not
contain the takeaway's meaning. Exact-substring validation cannot detect that
semantic failure.

This is separate from SSE geometry. It shows that TPv3.81 can generate meaning
from a URL that MPv3.3 is then unable to ground under its selection rules.

### What the claims jointly establish

The controlled evidence establishes that:

1. Adding referent text can change a vector.
2. In the greenhouse case, the target became more similar to one fixed solar
   vector and less similar to one fixed retirement vector.
3. In the surveillance case, the target became less similar to one fixed
   government-control vector and more similar to two fixed software vectors.
4. TEv4.1 changed decomposition granularity as well as mask context.
5. Some generated takeaways could not be supported by the permitted source
   fragments.

The evidence does **not** establish that:

- self-contained masks are always worse;
- SSE cannot represent independently searchable meanings;
- atomic vectors are already proven to be the right solution;
- TPv3.81 or MPv3.3 individually caused every observed change;
- these 50 diagnostic notes estimate corpus-wide performance.

The hypothesis this result suggested at the time was:

> One vector should represent one independently searchable meaning, while one
> note may produce several such vectors.

For the greenhouse note, that could mean separate vectors for `geothermal solar
powered greenhouse` and `non consumption based retirement`, rather than adding
the greenhouse phrase merely to make the retirement sentence self-contained.
That was not a TEv4.1 result and is not the current definition of an atomic
subject.

## Additional case observations

The full source/answer rows are retained in the selected
`historical-studies/communicated-meaning-tev4-1` bundle and the corresponding
numerical partition inputs. These replace the repeated complete-generation
appendices. The additional interpretations from those cases are retained below.

### Surveillance

If `CTRL-NEW` is intended to preserve an independently searchable `powerful
actors seeking control` meaning, these controls did not improve: cosine to the
fixed government-control vector fell, while cosines to the fixed free-software
and cross-platform-application vectors rose. This does not establish the
intrinsic quality of the complete compound surveillance representation.

The automatic-backup result is not part of that controlled conclusion because
both its candidate mask and the target mask changed.

### Retirement/greenhouse

The new mask correctly resolved what `This` meant for a human, and SSE pooled
the newly selected `geothermal solar powered greenhouse` tokens as part of the
target meaning. Its cosine to one fixed solar vector rose, while its cosine to
one fixed retirement-packet vector fell.

The explicitly selected energy phrase provides a direct mechanism for the
change. SSE also contextualizes selected tokens against the complete note, so
this experiment does not isolate or rule out additional whole-note context
effects. This run emitted no separate retirement-only vector for this note.
Whether a more atomic extraction would preserve both meanings better remains an
untested hypothesis.

### Overlapping vectors

The new pipeline did not merely clarify masks. It changed how many meanings it
claimed each note communicated and frequently reused the same source tokens.
The autonomy example is now represented twice, and those two vectors have
different cross-note neighborhoods. The pipeline emits and uses both;
it does not choose the better one.

## Detailed evidence D — Unsupported or distorted extractions

These are independent prompt or mask failures observed in the same run:

1. **Takeaway:** The post links to id Software’s Doom source-code repository
   and a separate Doom-related social-media post as references for the
   licensing update.

   **Mask over the complete original note:**

   > ⟦Doom 1 and 2 are now officially licensed under the #GPL, no longer
   > dual-licensed with the DSL :)⟧
   >
   > https://github.com/id-Software/DOOM/
   >
   > https://nitter.woodland.cafe/doom_txt/status/1747398603209883882
   >
   > #FOSS #OpenSource #Games #Gaming #GameNews

   **Problem:** The selected licensing sentence does not contain either link's
   meaning.

2. **Takeaway:** The post also links to a Hacker News discussion of the
   article.

   **Mask over the complete original note:**

   > Why a spritz of water before grinding coffee yields better results
   >
   > ⟦Comments⟧ ( https://news.ycombinator.com/item?id=38554310 )
   >
   > https://arstechnica.com/science/2023/12/study-why-a-spritz-of-water-before-grinding-coffee-yields-less-waste-tastier-espresso/

   **Problem:** `Comments` does not identify Hacker News or the article.

3. **Takeaway:** The author provides a link to the pypush project’s GitHub
   repository.

   **Mask over the complete original note:**

   > It's ready! #⟦pypush⟧ can now send and receive #iMessage, on any platform,
   > completely server-less and open-source! 🎉
   >
   > https://github.com/JJTech0130/pypush

   **Problem:** The project name does not establish that the omitted link is a
   GitHub repository.

4. **Takeaway:** Flexible cables have been installed as part of a greenhouse
   project shared by the author and others.

   **Mask over the complete original note:**

   > ⟦Flexicables installed for our ⟧geothermal solar powered ⟦greenhouse.⟧ The
   > greenhouse they have in Aliance Nebraska grows pineapple and dates and
   > citrus.
   > This will be the first steps to my non consumption based retirement.
   > https://image.nostr.build/21c798c130ea79bcc6fd7c1a30126a8177d0810275f4011af6c0592e6e62084c.jpg

   **Problem:** `Flexicables` was rewritten as generic flexible cables.

The first three expose a mismatch between the prompts:

1. TPv3.81 can preserve meaning contributed by a URL.
2. MPv3.3 forbids selecting URLs.
3. The mask generator substitutes nearby source words that do not contain the
   omitted link's meaning.

Mechanical validation proves that each selected fragment occurs in the source
and appears in source order. It cannot prove that the fragments preserve the
takeaway's meaning.

## Aggregate measurements

The cross-note cosine distributions were:

| Measurement | TEv3.1 | TEv4.1 |
|---|---:|---:|
| Median | `0.0520` | `0.0490` |
| Mean | `0.0728` | `0.0701` |
| p95 | `0.3214` | `0.3169` |

These summaries barely changed, but they are not quality metrics. They cannot
establish or refute a semantic improvement.

## Final interpretation

TEv4.1 asked whether resolving ambiguous masks by adding enough exact source
text to reconstruct a takeaway would improve SSE's representation.

The controlled evidence showed two direction changes:

- `RET-NEW` was more similar than `RET-OLD` to one fixed solar vector and less
  similar than `RET-OLD` to one fixed retirement vector.
- `CTRL-NEW` was more similar than `CTRL-OLD` to two fixed software vectors and
  less similar than `CTRL-OLD` to one fixed government-control vector.

Separately, TEv4.1 generated more overlapping vectors and some
takeaways that its mask rules could not support.

Therefore, TEv4.1 does not provide evidence that making masks self-contained
improves independently searchable meanings. It also does not prove the opposite
for all notes: these are two controlled examples inside a 50-note diagnostic
set, not a population estimate.

The experiment does not reject SSE or multi-vector representations. It exposes
a narrower problem: exact source text needed to explain a reference can carry
additional subject matter that changes the vector's retrieval behavior.

The later atomic-subject direction was not established by TEv4.1. Both prompts
changed together, so this run also cannot attribute every effect specifically
to TPv3.81 or MPv3.3.

## Exact controls and preserved evidence

The ordered 50-note set has SHA-256:

`c7064a8eff5826273fc514ab47ee7b7cd1f91c1f994e3de6d2887d23c8843c85`

TEv4.1 used:

- TPv3.81;
- MPv3.3;
- `gpt-5.6-sol` at `max` reasoning;
- one fresh ephemeral Codex process for every takeaway and mask call;
- the same SSE checkpoint, Sentence-T5 base model, worker, 768-dimensional
  output, and inference batch size as TEv3.1.

No generated result received a subjective correction pass. One mask response
contained a non-exact substring. Mechanical validation rejected it, and a
fresh retry succeeded. The rejected attempt remains in the audit log.

The selected `historical-studies/communicated-meaning-tev4-1` bundle retains
source posts, subject identities and final pairwise comparisons.
`numerical/fine-region-00d974f22ed8935f` retains the 194 takeaways/masks and
partition outcomes. The [bundle catalog](../publications.csv) identifies these
files; original transport logs, vectors and complete receipt directories are
outside the compact selection.

The cross-run retirement control uses normalized vectors directly:

- `RET-OLD`: TEv3.1 ordinal 64;
- `RET-NEW`: TEv4.1 ordinal 101;
- fixed TEv3.1 retirement-packet candidate: ordinal 96;
- `RET-OLD` cosine: `0.3562099685`;
- `RET-NEW` cosine: `0.2455033805`.

Each cosine is the dot product of the fixed candidate row from TEv3.1's
`normalized-vectors.f32le` and the corresponding `RET-OLD` or `RET-NEW`
normalized target row. The solar control uses the same calculation with a
byte-identical candidate vector and yields `0.3690140084` and `0.6565306208`.
