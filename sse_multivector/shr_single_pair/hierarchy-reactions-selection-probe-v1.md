# Audience reactions pooling probe v1 — experimental findings

Pooling only **reactions** instead of **Audience reactions**, in the identical
context, reduces the People-group score by 34–36%. Both entries still score
above five of the six actual people-class controls. Pooling the actor word
contributes to the false match, but removing it from pooling does not resolve
the ordering problem. The actor words remain in encoder context throughout.

This is a controlled local SSE diagnostic, not an admission improvement, prompt
revision, new hierarchy or held-out accuracy estimate. The prior conservative
admission candidate remains unchanged.

## Fixed inputs and calculation

Use the two saved HR38 entries that failed the
[title-versus-meaning comparison](hierarchy-hr38-title-meaning-score-v1.md):

| Entry | Original title | Original explicit meaning |
|---|---|---|
| L04535 | Audience reactions | Audience reactions are impressions, feelings or evaluations that audience members communicate in response to content they encounter. These responses may express different sentiments through different communication methods. |
| L07783 | Audience reactions | Reactions are audience responses that communicate a feeling or attitude toward a social-media post or the content it presents. They may take the form of a platform reaction or another expressive response. |

Keep each entire `title + "\n\n" + meaning` text identical. Request three views
per entry: pool the complete title, pool the complete meaning, or pool only the
exact title substring **reactions**. The first two are numerical replay controls.
The selection is an experimental text span, not an MP mask or standalone
subject vector. There is no automatic noun extraction rule.

The existing native [worker](../worker.py) encodes two contexts and six pooled
vectors using the same frozen checkpoint, base artifact, 768 dimensions,
512-token maximum, projection/pooling rule and batch size 32. The reusable
[input adapter](../title_selection_probe.py) reads the original source-bound
study, pins source hashes and prepares ordinary native requests. Its collection
checks native receipts and row/vector bindings. No alternative encoder or
execution path is introduced.

Keep all seven C00006 reference groups and their 69 original entries fixed.
The primary comparison is against fused-002's 15 People entries and one
Individuals entry. Complete-title queries and **reactions** queries use the
same saved contextual-title reference vectors. Complete-meaning queries use the
same saved meaning reference vectors as their original baseline. Preserve
source-note exclusion, `exp(-5.5 * (1 - cosine))`, and averaging over a group's
references. Do not recompute groups, boundaries or memberships.

## Results

These are group mean-support scores, not cosines or probabilities.

| Entry | Entire title pooled | Only reactions pooled | Reduction | Useful people classes outranked, before → after |
|---|---:|---:|---:|---:|
| L04535 | 0.067404 | 0.044577 | 33.87% | 6/6 → 5/6 |
| L07783 | 0.064796 | 0.041539 | 35.89% | 6/6 → 5/6 |

The saved contextual-title controls remain: Celebrities L03026, 0.010988;
Spectators, 0.051219; Racing drivers, 0.009688; Celebrities L07104, 0.009467;
Astronauts, 0.010740; Australians, 0.006748. Only Spectators now scores above
either **reactions** query. These are the same provisional reviewed controls;
none is relabeled. Patient advocacy and the other wrong/unresolved cases are
not converted into new expectations.

Raw mean cosine against the same 16 title references falls from 0.509034 to
0.434016 for L04535 and from 0.501621 to 0.421092 for L07783. The nonlinear
mean-support score is calculated separately, rather than by applying the kernel
to the mean cosine. All raw pair cosines and all seven group scores are saved.

The test isolates the words included in pooling. It does not isolate the
remaining effect of audience-related context, establish causality for every
People error, or show that selecting main nouns is a usable admission policy.
A useful next diagnostic would pool the identical word **reactions** without
the surrounding definition to measure how much of its remaining People match
comes from context. That further encoding is not performed or authorized here.

## Evidence and verification

Ignored artifacts remain at
`target/food-halves-v1/hr38-reactions-selection-v1/` in the research worktree,
through its external-storage symlink. Retain the worktree for these source and
artifact paths.

- Analysis plan frozen before new SSE output, SHA256:
  `debf426b72038ef4e9266cd40079ec6054323446fa4fe41f62e1eebace11260b`.
  All 34 analysis source bindings and the adapter's source bindings remain
  unchanged. The source study retains ASv6.100 provenance.
- `scores.json` and the three `*-scores.npz` files retain every query/reference
  cosine and query/group score. `token-checks.json` confirms the selected token
  is the exact final token of each full title, with identical ID and position
  in the same context. No tokenization change explains the pooling contrast.
- Full-title and full-meaning replay maximum normalized component differences
  are `4.56e-8` and `5.94e-8`; cosine errors are `6.30e-14` and `1.15e-13`.
  Baseline group-score differences are below `1.3e-8`. These small numerical
  replay differences are retained, not represented as exact vector equality.
- Independent scalar reconstruction checks all 414 raw pair cosines and 42
  group means; maximum error is `3.34e-16`. Native vector bytes, request hashes,
  selected UTF-8 spans and original context text are checked independently.
- The new adapter tests first failed because the capability was absent. Its
  native production preparation/worker/collection tests then pass, including
  UTF-8 selection, absent/duplicate selection, immutable output, and changed
  source/vector rejection. Native tests run in the pinned Torch environment;
  numerical regression tests run in the existing NumPy/SciPy environment:
  **15 native/adapter tests and 65 numerical tests pass**, with no skips.
  Attempting the numerical suite in the Torch-only environment first exposed
  missing SciPy; rerunning in the existing numerical environment passes.
- No LLM calls, training, paid resources, admissions, prompt changes, hierarchy
  changes or UI updates. This diagnostic is not an official HR construction.
