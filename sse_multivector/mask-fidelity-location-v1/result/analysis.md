# Narrow-location mask fidelity

## Question

When only a location phrase is selected, does SSE represent that location more strongly than the unrelated Rust-and-martini or watercolor-and-lemonade context surrounding it?

## Result

**Pass: all four predeclared comparisons passed.**

SSE received each complete note. The text inside `⟦...⟧` is the only text whose
contextual token representations were pooled into that note's vector.

### Test 1

Same location meaning despite different wording and surrounding context:

> **N01:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦on a quiet beach⟧.
>
> **N04:** I spent the afternoon painting a watercolor while drinking lemonade
> ⟦beside a calm shoreline⟧.

Cosine: `0.821019`

Control with identical surrounding context but a different masked location:

> **N01:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦on a quiet beach⟧.
>
> **N05:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦in a windowless office⟧.

Cosine: `0.116487`

Result: the beach-location match won by `+0.704532`.

### Test 2

Same location meaning despite different wording and surrounding context:

> **N02:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦beside a calm shoreline⟧.
>
> **N03:** I spent the afternoon painting a watercolor while drinking lemonade
> ⟦on a quiet beach⟧.

Cosine: `0.839550`

Control with identical surrounding context but a different masked location:

> **N02:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦beside a calm shoreline⟧.
>
> **N06:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦inside an office without windows⟧.

Cosine: `0.086605`

Result: the beach-location match won by `+0.752945`.

### Test 3

Same location meaning despite different wording and surrounding context:

> **N05:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦in a windowless office⟧.
>
> **N08:** I spent the afternoon painting a watercolor while drinking lemonade
> ⟦inside an office without windows⟧.

Cosine: `0.952025`

Control with identical surrounding context but a different masked location:

> **N05:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦in a windowless office⟧.
>
> **N01:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦on a quiet beach⟧.

Cosine: `0.116487`

Result: the office-location match won by `+0.835538`.

### Test 4

Same location meaning despite different wording and surrounding context:

> **N06:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦inside an office without windows⟧.
>
> **N07:** I spent the afternoon painting a watercolor while drinking lemonade
> ⟦in a windowless office⟧.

Cosine: `0.930510`

Control with identical surrounding context but a different masked location:

> **N06:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦inside an office without windows⟧.
>
> **N02:** I spent the afternoon debugging a Rust borrow-checker error while
> drinking a martini ⟦beside a calm shoreline⟧.

Cosine: `0.086605`

Result: the office-location match won by `+0.843905`.

## Complete cosine matrix

| | N01 | N02 | N03 | N04 | N05 | N06 | N07 | N08 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **N01** | 1.0000 | 0.8556 | 0.9823 | 0.8210 | 0.1165 | 0.1167 | 0.1096 | 0.1176 |
| **N02** | 0.8556 | 1.0000 | 0.8395 | 0.9846 | 0.1083 | 0.0866 | 0.1035 | 0.0906 |
| **N03** | 0.9823 | 0.8395 | 1.0000 | 0.8221 | 0.1499 | 0.1491 | 0.1497 | 0.1629 |
| **N04** | 0.8210 | 0.9846 | 0.8221 | 1.0000 | 0.0932 | 0.0686 | 0.0991 | 0.0817 |
| **N05** | 0.1165 | 0.1083 | 0.1499 | 0.0932 | 1.0000 | 0.9466 | 0.9801 | 0.9520 |
| **N06** | 0.1167 | 0.0866 | 0.1491 | 0.0686 | 0.9466 | 1.0000 | 0.9305 | 0.9711 |
| **N07** | 0.1096 | 0.1035 | 0.1497 | 0.0991 | 0.9801 | 0.9305 | 1.0000 | 0.9692 |
| **N08** | 0.1176 | 0.0906 | 0.1629 | 0.0817 | 0.9520 | 0.9711 | 0.9692 | 1.0000 |

`analysis.json` retains the unrounded values used for every verdict.

## Secondary observations

Identical selected wording remained nearly unchanged when the unselected context changed:

| Pair | Cosine |
|---|---:|
| N01 ↔ N03 | `0.982316` |
| N02 ↔ N04 | `0.984553` |
| N05 ↔ N07 | `0.980081` |
| N06 ↔ N08 | `0.971089` |

Location paraphrases also remained close:

| Pair | Cosine |
|---|---:|
| N01 ↔ N02 | `0.855579` |
| N03 ↔ N04 | `0.822117` |
| N05 ↔ N06 | `0.946553` |
| N07 ↔ N08 | `0.969186` |

## What this establishes

> For explicit narrow masks, SSE can isolate selected meaning without
> substantial contamination from the rest of the note.

This conclusion is limited to the simple, explicit location phrases tested
here. The evidence is strong within that scope: the same masked location under
different surrounding context scored from `0.821019` to `0.952025`, while a
different masked location under identical surrounding context scored only
`0.086605` to `0.116487`.

## What this does not establish

This run used one easy semantic distinction: beach versus office. It did not compare narrow masks with broader masks, test references or relationships distributed across several fragments, test automatic mask extraction, use real notes, or test segmentation. Those remain separate questions.
