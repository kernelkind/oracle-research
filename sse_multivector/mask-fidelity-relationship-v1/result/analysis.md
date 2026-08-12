# Separated-fragment relationship fidelity

## Question

Can SSE combine separated selected fragments into a representation that
preserves which entity performed an action and which entity received it?

## Result

**Fail: all four predeclared comparisons failed.**

SSE received each complete note. Only the contextual token representations
inside `⟦...⟧` were pooled into its vector.

### The four inputs

**N01 — red dog chased blue cat, active voice**

> Before sunset, the ⟦red dog⟧ suddenly ⟦chased⟧ the ⟦blue cat⟧ through the
> garden.

**N02 — red dog chased blue cat, passive voice**

> Through the garden, the ⟦blue cat⟧ ⟦was chased by⟧ the ⟦red dog⟧ before
> sunset.

**N03 — blue cat chased red dog, active voice**

> Before sunset, the ⟦blue cat⟧ suddenly ⟦chased⟧ the ⟦red dog⟧ through the
> garden.

**N04 — blue cat chased red dog, passive voice**

> Through the garden, the ⟦red dog⟧ ⟦was chased by⟧ the ⟦blue cat⟧ before
> sunset.

N01 and N02 communicate the same relationship. N03 and N04 communicate the
opposite relationship. Every note uses the same two entities and the same
ordinary action.

### Test 1

Same relationship, changed from active to passive voice:

> **N01:** Before sunset, the ⟦red dog⟧ suddenly ⟦chased⟧ the ⟦blue cat⟧
> through the garden.
>
> **N02:** Through the garden, the ⟦blue cat⟧ ⟦was chased by⟧ the ⟦red dog⟧
> before sunset.

Cosine: `0.983838`

Control with the same active syntax but the relationship reversed:

> **N01:** Before sunset, the ⟦red dog⟧ suddenly ⟦chased⟧ the ⟦blue cat⟧
> through the garden.
>
> **N03:** Before sunset, the ⟦blue cat⟧ suddenly ⟦chased⟧ the ⟦red dog⟧
> through the garden.

Cosine: `0.988368`

The reversed relationship scored higher by `0.004531`. Test 1 failed.

### Test 2

The same N01–N02 relationship match scored `0.983838`.

Control with the relationship reversed but the selected concepts appearing in
the same source order—red dog, chase, blue cat:

> **N01:** Before sunset, the ⟦red dog⟧ suddenly ⟦chased⟧ the ⟦blue cat⟧
> through the garden.
>
> **N04:** Through the garden, the ⟦red dog⟧ ⟦was chased by⟧ the ⟦blue cat⟧
> before sunset.

Cosine: `0.994998`

The reversed relationship scored higher by `0.011160`. Test 2 failed.

### Test 3

Same reversed relationship, changed from active to passive voice:

> **N03:** Before sunset, the ⟦blue cat⟧ suddenly ⟦chased⟧ the ⟦red dog⟧
> through the garden.
>
> **N04:** Through the garden, the ⟦red dog⟧ ⟦was chased by⟧ the ⟦blue cat⟧
> before sunset.

Cosine: `0.985039`

Control with the same active syntax but the relationship reversed:

> **N03:** Before sunset, the ⟦blue cat⟧ suddenly ⟦chased⟧ the ⟦red dog⟧
> through the garden.
>
> **N01:** Before sunset, the ⟦red dog⟧ suddenly ⟦chased⟧ the ⟦blue cat⟧
> through the garden.

Cosine: `0.988368`

The reversed relationship scored higher by `0.003330`. Test 3 failed.

### Test 4

The same N03–N04 relationship match scored `0.985039`.

Control with the relationship reversed but the selected concepts appearing in
the same source order—blue cat, chase, red dog:

> **N03:** Before sunset, the ⟦blue cat⟧ suddenly ⟦chased⟧ the ⟦red dog⟧
> through the garden.
>
> **N02:** Through the garden, the ⟦blue cat⟧ ⟦was chased by⟧ the ⟦red dog⟧
> before sunset.

Cosine: `0.995689`

The reversed relationship scored higher by `0.010651`. Test 4 failed.

## Complete cosine matrix

| | N01 | N02 | N03 | N04 |
|---|---:|---:|---:|---:|
| **N01** | 1.000000 | 0.983838 | 0.988368 | 0.994998 |
| **N02** | 0.983838 | 1.000000 | 0.995689 | 0.986555 |
| **N03** | 0.988368 | 0.995689 | 1.000000 | 0.985039 |
| **N04** | 0.994998 | 0.986555 | 0.985039 | 1.000000 |

`analysis.json` retains the unrounded values used for every verdict.

## What this establishes

For this controlled relationship, the separated-fragment masks did not
preserve who chased whom. All four vectors were extremely similar, and the two
strongest cross-note similarities joined opposite relationships whose selected
concepts appeared in the same source order:

- N01 ↔ N04: `0.994998`
- N02 ↔ N03: `0.995689`

This is evidence against using this separated-fragment formulation for a
relationship whose meaning depends on how its selected pieces connect.

## What this does not establish

This does not show that every multi-fragment mask fails. It tests one simple
binary relationship. It also does not tell us whether selecting each complete,
contiguous proposition would preserve the relationship; that requires a
separate controlled run with the notes and SSE checkpoint held fixed.
