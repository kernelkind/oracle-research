# SGC02: connection evidence without exact role labels

## Question

Does requiring an exact relationship type and direction unnecessarily prevent
useful broader note categories? SGC01 retains genuine preparation/food and
beet/preservation connections, but its patterns cannot share them when the
native labels or directions differ. Fine-grained event logic is not a browsing
requirement. Conversely, arbitrary words from the same description do not
necessarily express a shared subject.

## Fixed evidence and intervention

Use SGC01's eleven accepted native graphs, the same source records, and the
same WordNet ancestor dictionary. Preserve all fifteen input records and the
four exclusions in the evidence. This is a targeted comparison on nine included
notes from thirteen selected notes, not a complete-corpus coverage study.
Do not rerun a model, correct an input or sense, infer a missing participant,
add frames, tune a threshold, or change the browser.

Control: SGC01's exact, directed single-role patterns.

Changed condition: patterns contain two concepts joined by an existing source
edge, without requiring that edge's type or direction. Keep the native edge,
node identities, direction and contexts in each witness. Replace a concept
only with its existing dictionary ancestor. Never form a pair merely because
its concepts occur in one description, or connect through an arbitrary path.

This jointly relaxes relationship type and direction. A gain does not isolate
which of those two restrictions was responsible. The tested decision is whether
precise role normalization is necessary before this construction can progress.
Single-concept patterns and their memberships must remain unchanged.

## Hypothesis and competing explanations

Hypothesis: forgetting the exact role requirement while preserving actual
connected participants produces at least one useful, source-supported broader
pattern joining relevant notes that no corresponding exact-role pattern joined.
Its category must support recognizable narrowing in a saved path; counts or
renamed patterns alone are insufficient. No exact taxonomy is prescribed.

One pre-run opportunity is the shared activity/food abstraction of preparation
and preservation. It would be a broader food-related activity meaning, not an
assertion that every activity is the same preparation process. The source
dictionary, not a hand-added activity relationship, determines whether the
path exists. An unexpected coherent result can also support the hypothesis.

Competing explanations for apparent gains include generic or incidental
concepts, source interpretation errors, a misleading paraphrase of the relaxed
pattern, and notes already discoverable through an equally useful existing
pattern. Missing gains can arise from wrong senses, absent participants,
dictionary gaps or insufficient sampling rather than essential role precision.
Inspect every witness of a claimed gain and check relevant omissions within
the available inputs. Do not call a source error caused by role relaxation when
the same error existed in the control.

The coffee-drinking source's erroneous `Result → coffee` can still support a
coffee-drinking topic without asserting coffee production. In contrast,
CAP03's “more complete disconnection” at a coffee shop must not become “more
coffee” through whole-description co-occurrence. These earlier observations
motivate keeping connections; the latter malformed SGC01 input remains excluded
and is not advertised as a passed experimental control.

## Decision consequences

Would either outcome change the next decision?

- Useful new connected patterns weaken the case for acquiring a precise-role
  model first. Retain only the supported capability claim; category selection,
  other lexical gaps and broader transfer remain open.
- New pairs that cannot sustain recognizable meanings or useful paths do not
  justify adoption. Identify whether role information was actually needed or
  whether other fixed inputs explain the problem before choosing a remedy.
- Only generic combinations or changes already matched by a simpler control
  provide no consequential construction improvement. Do not expand this run
  merely because it creates more or fewer patterns.

## Evaluation and preservation

Save both conditions in full, including one-note patterns, original witnesses,
construction links and unhelpful output. Compare patterns sharing the same
unordered endpoint concepts, retaining every exact-role counterpart rather
than choose one convenient control. Inventory every recurring connected-pattern
note set and its most-specific patterns. Audit all such representatives and
all witnesses of claimed gains. Preserve complete paths and the full original
notes with inline masks for any presented evidence.

Verify tests first against production code, unchanged exact output, unchanged
singletons, no invented pairs, note deduplication, support containment,
acyclicity and deterministic replay. Structural checks are not semantic scores.
Use only local deterministic construction; no inference or paid resource.

## Research basis

The [SGC01 report](./SEMANTIC-GRAPH-CONSTRUCTION.md) and
[predicate-frame investigation](./PREDICATE-FRAME-RESOURCES.md) distinguish
useful local topical connections from exact event semantics. Order-labelled
graph refinement supports generalized labels and deleting constraints, but
does not establish semantic usefulness for text browsing: [Ontañón 2016,
sections 2–2.4](https://arxiv.org/pdf/1604.06954). This experiment is a bounded
relaxation, not a claim to reproduce that library or its complete search.
The [CAP03](./SUBJECT-DESCRIPTION-CONSTRUCTION.md) and
[DSP01](./DEPENDENCY-DESCRIPTIONS.md) records supply the connection/co-occurrence
distinction and its limitations.
