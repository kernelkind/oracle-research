# User-Directed Semantic Region Navigation

## Status

This is a working hypothesis, not an approved architecture. No mapping
technology, implementation, or experiment has been chosen.

## Realization

A note rating and a request for more content from the same subject are
different statements:

- Rating a note says that the particular note was or was not valuable.
- Selecting a semantic region says what the person wants to explore now.
- Being shown a note records exposure; it does not establish preference.

Oracle MVP v1 treated positive note ratings as permission to repeatedly expand
their semantic neighborhoods. Explicit region selection could avoid guessing
whether the person wants more of a subject or has become tired of it.

## Possible Responsibility Boundary

Public computation could derive a versioned semantic structure from the
complete public embedding corpus. No subject ontology exists beforehand: the
regions emerge from relationships among the embedded notes. The structure must
support different levels of specificity, and one note may belong to more than
one region.

Every eligible public note must be considered by this mapping. A note may have
graded membership in several regions or be recorded as an explicit outlier; it
must not disappear merely because it is outside the neighborhoods reached from
private positive examples.

Private local state could use that public map without turning note ratings into
region preferences:

- each rating remains evidence about that particular note;
- repeated positive or negative evidence near a region may inform local
  ranking, but does not mean "show more" or "show less" of the region;
- being shown a note records exposure only;
- explicit region selection represents temporary current intent.

The interface could order regions by how much positive note-level evidence they
contain, followed by unexplored regions that become increasingly distant from
that evidence. This ordering would not authorize automatic expansion. Different
semantic directions must remain visible so one dense subject cannot fill the
list. Disconnected regions must also remain browsable.

Selecting a region would decide where to explore. It would not replace the
local task of selecting worthwhile, varied notes within that region.

## Central Unknown

We do not currently know how to produce the required note-to-region mapping.

The current Oracle provides one vector for each whole note and similarity
between notes. It does not provide:

- a reliable way to produce useful semantic-region choices when needed;
- accurate descriptive labels for those regions;
- membership strengths when a note expresses several subjects;
- evidence that the resulting mapping matches human interpretation.

A whole-note vector may blend several subjects. The mapping must not assume
that each note has exactly one subject.

The subjects are corpus-induced rather than predefined. This does not imply one
objectively correct partition: the construction still chooses granularity,
overlap, and outlier behavior. What remains unresolved is which construction
produces useful regions and whether public definitions, cuts, labels, and note
memberships must be materialized after discovery or can be computed lazily from
a versioned public structure.

Until this prerequisite is demonstrated, semantic-region navigation must not
be treated as the next architecture.

See
[Corpus-Induced Semantic Region Discovery](../research/semantic-region-discovery-and-labeling.md)
for the literature review.

## Decisions Not Yet Made

- Which corpus-wide construction derives the public semantic structure.
- Which public cuts, labels, and memberships are materialized or computed
  lazily.
- How private evidence orders and selects among those public regions.
- How regions at different levels of specificity relate.
- How labels are generated and grounded in representative notes.
- How one note contributes to multiple regions.
- How private positive, neutral, and negative evidence is combined.
- How unexplored regions are ordered without reproducing exposure bias.
