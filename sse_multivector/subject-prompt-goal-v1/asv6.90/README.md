# ASv6.90 resolved referents before specific subjects

Status: tested with failures; not adopted.
[ASv6.90](ASv6.90.md) replaces only the first two source-resolution sentences
in frozen ASv6.81 with three sentences: resolve the complete supported referent
for each occurrence, build complete specific subjects and expressed combinations
from those referents, then derive less specific descriptions as broader headings.
The original grounding sentence, all other instructions, seven complete examples,
schema and one-call POST template remain byte-identical. The source edit adds
six words per request, constant with corpus size, without adding an output field
or model call.

## Existing instruction coverage

The change applies existing reference resolution (R02), source-first enumeration
(R16), complete particular subjects and combinations (R18), and heading generality
(R29/R31). It retains both enclosing relationships and local roles or purposes.
The grounding sentence preserves R04. C1 remains the primary demonstration:
resolved tissue/scrap counts and food roles appear in the complete group and
mixing action. C2 already demonstrates the same operation with the new RavenWorks
app, its first use, complete conditional help and appreciation; broader help
headings retain their own level of generality. R20/R22/R30 still govern scope,
compatible copies and standalone meanings. All 34 primary clause assignments
and five tracked implications retain their unchanged examples and meanings.

## Narrow generation hypothesis

ASv6.87's original N096 answers retain the complete recipe in separate headings
but omit explicit recipe identity from the counted saute and seasoning pair.
For example, trial 3 has the author's never-fail recipe feeding five at 1.1.1,
while all eleven saute copies name only the Spaghetti Bolognaise recipe.
This draft changes how complete source subjects are formed: the local ingredient
descriptions resolve to their counted roles in that particular recipe before
the action is composed. Its prediction is improved retention of that supported
recipe relationship in the complete specific action, rather than only in a
separate recipe leaf. It does not establish why earlier answers failed.

This differs from ASv6.80's paragraph-position edit and ASv6.87's C1 inventory
explanation. Paragraph positions and all example bytes remain those of ASv6.81;
only the source-resolution operation changes. A complete source subject still
must be collected beneath every compatible numbered occurrence, and every
displayed scope edge must pass the heading-string test. This edit does not
demonstrate that those independent failures, shared-action omissions or later
properties are repaired.

## Occurrence and generality boundaries

“For that occurrence” keeps resolution tied to the supported source use.
A state acquired later must not be imported into an earlier action where the
post establishes a different state. A later description can complete the same
referent only where its applicability is supported by the complete post.
No new source relationship follows from co-mention or statement order.

“Less specific” concerns meaning, not phrase length: equivalent concise wording
remains valid. General headings may omit instance details; complete specific
subjects retain them in their own headings and compatible copies. Optional
broader headings are not newly required. No literal phrase-copy format,
canonical metadata, reasoning trace or schema field is introduced.

## Provenance and checks

The versioned source edit (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.90/prompt-edits.json`) pins the ASv6.81 source hash.
Its native revision receipt records the exact changed strings and destination
hash. The template edit (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.90/edits.json`) independently pins ASv6.81's
reusable POST template; native revision preserves its existing POST wrapper.
Production ASv6.48, MP, model route, settings and frozen evaluation criteria
remain unchanged. Root's minimal source-generation check first fails on ASv6.81
for the missing replacement. All 95 relevant offline checks now pass, including
the exact edit, unchanged examples, production validation and template identity.
Both native revision receipts and the unchanged POST wrapper are verified.
This authoring task makes no inference calls and changes no test files; no
semantic repair is claimed. Root owns the native development screen and commit.

## Completed development result

The [completed comparison](../isolation-v1/source-completion-phase-v1.md)
finishes 24 valid original/minimized/later answers: fifteen bounded accepts,
nine rejects. Originals are 6 accepts/6 rejects, minimized cases 5/6 and later
properties 4/6. All three original N096 sautés retain explicit author/easy/
never-fail/feeding-five recipe identity, versus one of three fresh ASv6.81
answers. Independent N096 copies still fail in every trial. Source completion,
missing partial actions and later-property/copy failures remain elsewhere.
The nine occurrence guards have eight accepts and one chronology-preserving
copy rejection, versus nine accepts for fresh ASv6.81. Neither version imports
later wetness into earlier packing. This is a bounded targeted source finding,
not a reliable correction or a unique internal model explanation.
