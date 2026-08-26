# Single-fragment mask-boundary fidelity

## Question

When a single contiguous mask still means the same atomic subject, does adding harmless grammatical text to its boundaries change the SSE vector less than replacing the subject?

## Controlled change

Each subject used one fixed note. Only the mask boundaries changed:

- subject noun;
- determiner plus subject noun;
- preposition, determiner, and subject noun;
- the same text plus terminal punctuation.

The matched different-subject control used the same sentence form and the same boundary mode.

| Subject | B1 | B2 | B3 | B4 |
|---|---|---|---|---|
| Dog | `dog` | `the dog` | `about the dog` | `about the dog.` |
| Cat | `cat` | `the cat` | `about the cat` | `about the cat.` |
| Coffee | `coffee` | `the coffee` | `about the coffee` | `about the coffee.` |
| Tea | `tea` | `the tea` | `about the tea` | `about the tea.` |
| Bicycle | `bicycle` | `the bicycle` | `about the bicycle` | `about the bicycle.` |
| Car | `car` | `the car` | `about the car` | `about the car.` |

## Hypothesis

For every mask, every other boundary variant of the same subject will have a higher cosine than the matched different subject using that other boundary. All 72 comparisons must pass.

## Result

**Passed. 72 of 72 predeclared comparisons favored the unchanged subject.**

| Subject | Comparisons | Same-subject cosine | Different-subject cosine | Smallest margin |
|---|---:|---:|---:|---:|
| Dog | 12/12 | `0.931409–0.993003` | `0.494654–0.625200` | `+0.364795` |
| Cat | 12/12 | `0.949108–0.994477` | `0.494654–0.625200` | `+0.369276` |
| Coffee | 12/12 | `0.969296–0.997088` | `0.455609–0.550715` | `+0.446373` |
| Tea | 12/12 | `0.954442–0.997056` | `0.455609–0.550715` | `+0.446341` |
| Bicycle | 12/12 | `0.932928–0.994358` | `0.359477–0.479524` | `+0.498941` |
| Car | 12/12 | `0.931499–0.995233` | `0.359477–0.479524` | `+0.492452` |

The weakest comparison still favored the unchanged subject by `+0.364795` cosine.

## Conclusion

For these three common matched subject pairs, expanding a single mask across a determiner, preposition, or terminal punctuation affected the vector much less than replacing the atomic subject.

This fills the previously untested mask-boundary case. It does not establish the same behavior for arbitrary language, real Nostr notes, or masks containing multiple fragments.

Every unrounded comparison is in `analysis.json`; the complete 24-by-24 cosine matrix is in `cosine-matrix.csv`.
