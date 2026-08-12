# Narrow-location mask fidelity

## Question

When only a location phrase is selected, does SSE represent that location more strongly than the unrelated Rust-and-martini or watercolor-and-lemonade context surrounding it?

## Result

**Pass: all four predeclared comparisons passed.**

| Comparison | Same location, different wording and context | Same context, different location | Margin |
|---|---:|---:|---:|
| C01 | N01 ↔ N04: `0.821019` | N01 ↔ N05: `0.116487` | `+0.704532` |
| C02 | N02 ↔ N03: `0.839550` | N02 ↔ N06: `0.086605` | `+0.752945` |
| C03 | N05 ↔ N08: `0.952025` | N05 ↔ N01: `0.116487` | `+0.835538` |
| C04 | N06 ↔ N07: `0.930510` | N06 ↔ N02: `0.086605` | `+0.843905` |

The intended pair changes both the wording of the selected location and the unselected surrounding activity. The control keeps the surrounding activity exactly the same while changing the selected location. In every case, the location match won by a large margin.

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

For these simple, explicit location phrases, narrow manual masks made SSE follow the selected location rather than the unrelated surrounding activity. This is positive evidence that narrow masks can isolate an intended meaning.

## What this does not establish

This run used one easy semantic distinction: beach versus office. It did not compare narrow masks with broader masks, test references or relationships distributed across several fragments, test automatic mask extraction, use real notes, or test segmentation. Those remain separate questions.
