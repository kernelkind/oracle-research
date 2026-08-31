# SSE Communicated-Meaning Triplet

## Question

Can masked SSE representations place two differently worded notes that
communicate the same kind of request near one another while keeping nearby but
different communicated meanings distinguishable?

This is a three-note diagnostic, not a pass/fail evaluation and not a gate for
the larger 32-note experiment.

## Inputs

The source-bound input contains three real Nostr notes from three authors:

- one request for book recommendations for an 18-year-old;
- one claim about studying the Cultural Revolution followed by a starting-book
  recommendation;
- one mixed note containing completed tasks, gardening plans, a request for
  different book recommendations after listening to a Napoleon book, and
  praise for an earlier book recommendation.

The approved takeaway-generation prompt produced seven takeaways. A separate
call applied the approved mask prompt to each takeaway. Both prompts and every
exact source fragment are pinned in
[`../../../sse_multivector/communicated-meaning-triplet-proposal-v1.json`](../../../sse_multivector/communicated-meaning-triplet-proposal-v1.json).

One generated label normalized the source text `Germs, Guns & steel` to the
canonical title *Guns, Germs, and Steel*. The exact mask remained grounded in
the source. Labels were report metadata and never entered the encoder.

## Execution

The run reused the exact worker, immutable container, full-dimensional
Sentence-T5-base SSE checkpoint, tokenizer, and pooling rule from the original
32-note diagnostic. It generated seven finite, nonzero 768-dimensional vectors
and all 21 pairwise cosine values. Deterministic verification succeeded.

The complete run is preserved at
[`../../../sse_multivector/baselines/communicated-meaning-triplet-v1/README.md`](../../../sse_multivector/baselines/communicated-meaning-triplet-v1/README.md).

## Measurements

Selected cross-note cosine values:

| Left meaning | Right meaning | Cosine |
|---|---|---:|
| Request for books suitable for an 18-year-old | Request for different books after listening to a Napoleon book | 0.366756 |
| Studying the Cultural Revolution as preparation | Request for different books after listening to a Napoleon book | 0.337460 |
| Dikötter as a starting recommendation | Request for different books after listening to a Napoleon book | 0.306687 |
| Request for books suitable for an 18-year-old | Praise for an earlier book recommendation | 0.255651 |
| Request for books suitable for an 18-year-old | Studying the Cultural Revolution as preparation | 0.244825 |
| Request for books suitable for an 18-year-old | Dikötter as a starting recommendation | 0.161308 |
| Request for books suitable for an 18-year-old | Gardening plans | -0.036274 |

The two differently worded recommendation requests formed the strongest of all
14 cross-note pairs. The four disjoint takeaways extracted from the mixed note
also remained distinct: their six pairwise cosines ranged from `0.062811` to
`0.280505`.

## Interpretation

This triplet provides encouraging evidence that SSE can associate differently
worded instances of a communicated request while separating unrelated meaning
from the same mixed note.

It does not show that the representation isolates communicative meaning from
topic and context. The historical-book meanings were also close to the
recommendation request. With three notes, these values cannot establish an
accuracy rate or general ranking quality.
