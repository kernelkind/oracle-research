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

Public computation could derive human-understandable semantic regions from
public notes. Regions may exist at different levels of specificity, and one
note may belong to more than one region.

Private local state could overlay the person's ratings onto that public map:

- supported regions contain repeated positive evidence;
- rejected regions contain meaningful negative evidence;
- unexplored regions contain insufficient evidence;
- explicit region selection represents temporary current intent.

The interface could present supported regions first, followed by unexplored
regions that become increasingly distant from demonstrated interests. Different
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

The literature does not establish that the regions must be a permanent,
corpus-wide subject inventory. They could be precomputed, generated
dynamically, or assembled dynamically from reusable public structure. The
choice remains unresolved.

Until this prerequisite is demonstrated, semantic-region navigation must not
be treated as the next architecture.

See
[Semantic Region Discovery and Labeling](../research/semantic-region-discovery-and-labeling.md)
for the literature review.

## Decisions Not Yet Made

- Whether semantic regions are precomputed, generated dynamically, or hybrid.
- How regions at different levels of specificity relate.
- How labels are generated and grounded in representative notes.
- How one note contributes to multiple regions.
- How private positive, neutral, and negative evidence is combined.
- How unexplored regions are ordered without reproducing exposure bias.
