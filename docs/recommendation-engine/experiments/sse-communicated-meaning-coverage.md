# TEv3.1 — coverage diagnostic

## Question

Did TEv2's suspicious neighborhoods look broken because its 32-note corpus
contained too few examples of the intended meanings?

The stable case names are:

- **Failure #3:** control language matched automatic backups;
- **Failure #5:** an autonomy vector developed a coffee-heavy neighborhood;
- **Failure #6:** a retirement vector followed greenhouse and energy context.

Mask extraction is a separate experimental axis.

## Design

TEv3.1 appended real notes selected from raw text without consulting SSE
vectors, scores, or ranks. It retained the TEv2 prompts, masks, checkpoint,
worker, and inference settings.

The experiment ran in two preserved stages:

1. Six autonomy notes and six retirement-related notes added 33 vectors for
   Failures #5 and #6. This stage contains 44 notes and 106 vectors.
2. Six surveillance-and-control notes added 25 vectors for Failure #3. The
   final stage contains 50 notes and 131 vectors.

Every added note is from the frozen learning split, has a distinct author, and
has no author overlap with earlier notes. The original 73 TEv2 vectors are
byte-identical in both stages. The Failure #3 target and its previous leading
neighbors are also byte-identical across the two TEv3.1 stages.

## Observations

### Failure #3 — Control and automatic backups

The target was:

> Unspecified actors want to control everything.

Its mask was only `they want to control everything`.

After targeted coverage, relevant additions reached ranks 1, 3, 4, 6, 9–11,
14, and 15. The first result was a government plan to eliminate anonymity and
identify citizens everywhere at cosine `0.5067`.

The neighborhood did not become clean:

- automatic backups remained rank 2 at `0.4175`;
- an open-source iMessage implementation remained rank 5 at `0.4005`;
- a free-software stack remained rank 7 at `0.3763`;
- direct examples of social-credit restrictions and government camera
  surveillance ranked between 32 and 73;
- less-direct takeaways from a surveillance-heavy Matrix note reached ranks
  16 and 18.

The measured ranks show both improvement and persistent poor matches. Our
interpretation is that the unchanged target contains real
control-and-surveillance signal, but coverage alone does not explain its uneven
ordering.

### Failure #5 — Personal autonomy

The target was:

> Only choices made without pressure define a person; the rest is a facade.

After autonomy coverage, its first eight neighbors were all about
authenticity, self-direction, integrity, nonconformity, or resistance to
external authority. Their cosine scores ranged from `0.4406` to `0.5430`.

The old suspicious scores remained unchanged. Personal coffee roasting stayed
at `0.4347` but moved from rank 2 to rank 10.

### Failure #6 — Non-consumption-based retirement

The target was:

> The greenhouse project is the author's first step toward a
> non-consumption-based retirement.

In its controlled coverage stage, relevant additions reached ranks 1, 4, 6,
8, 11, and 12. The original greenhouse and solar matches remained ranks 2 and
3 with unchanged scores; automatic backups remained rank 5.

This shows useful retirement and work-exit signal, but not a clean retirement
neighborhood. The later Failure #3 stage also introduced financial-independence
notes that matched this target strongly. Those notes were not selected to test
retirement coverage, so the preserved first stage remains the controlled basis
for this case's conclusion.

## Interpretation

| Case | Supported conclusion |
|---|---|
| Failure #3 | Sparse coverage contributed to the failure, but poor leading matches and inconsistent direct matches remain. |
| Failure #5 | Sparse coverage was a major cause of the misleading TEv2 result. |
| Failure #6 | Sparse coverage contributed, but did not fully explain the result. |

The defensible overall result is:

> TEv2's tiny corpus hid useful meaning in all three target vectors. Adding
> relevant coverage largely repaired autonomy and partially repaired control
> and retirement. Coverage did not remove evidence of context influence or
> inconsistent fine-grained geometry.

TEv3.1 is an exploratory diagnostic. It does not establish population-level
accuracy or that SSE works across the complete Nostr corpus.

The complete notes, generated takeaways, masks, ranks, and case-by-case
reasoning are in
[`./sse-communicated-meaning-coverage-cases.md`](./sse-communicated-meaning-coverage-cases.md).
The immutable stages are preserved in
[`../../../sse_multivector/baselines/communicated-meaning-coverage-v1/README.md`](../../../sse_multivector/baselines/communicated-meaning-coverage-v1/README.md)
and
[`../../../sse_multivector/baselines/communicated-meaning-coverage-v2/README.md`](../../../sse_multivector/baselines/communicated-meaning-coverage-v2/README.md).
