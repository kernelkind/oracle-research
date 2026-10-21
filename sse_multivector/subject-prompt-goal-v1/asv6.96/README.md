# ASv6.96 consolidated instructions

Status: tested experimental draft; clear failures remain; not adopted.

The user-approved [ASv6.97 C1 correction](../asv6.97/README.md) now demonstrates
Food → Sea salt and retains the explicit source-seasoning purpose. ASv6.96's
tested bytes remain frozen. The new version's 18-answer medium screen completes
at 2 bounded accepts/15 rejects/1 uncertain; it is not a reliable correction.

[ASv6.96](ASv6.96.md) consolidates ASv6.95's repeated instruction checks into
ten paragraphs before its seven unchanged examples. Instruction words decrease
from 731 to 534; complete source size decreases from 27,665 to 26,372 UTF-8 bytes.
The complete-source qualification requirement and the permission to use general
headings are now explained together. The repeated rereading, edge-checking and
final collection procedures are removed; their required output properties remain.
This is a controlled instruction-organization change, not a changed JSON contract
or a claim that shorter instructions cause a model repair.

Every example post, explanation and output is byte-identical to ASv6.95:
54/32/0/8/18/15/10 entries, 137 total. The book-index analogy is retained;
its removal was already tested in ASv6.77 without reliable correction.
Production ASv6.48 and MP are outside this experimental revision.

## Actual instruction and example coverage

Paragraphs below refer to the ten instruction paragraphs before `<example>`.
Clause IDs preserve the maintained 34-clause map. Every ID has one primary
example assignment; related secondary demonstrations remain useful contrasts.
The semantic before/after review is separate from counting static IDs.

| IDs | Paragraphs | Primary example and actual demonstration |
| --- | --- | --- |
| R01, R02, R04 | 1–2 | C1: whole-post resolution of the counted tissue, scraps and cutting references, with supported ingredient and recipient roles. |
| R03, R05, R06 | 2–3 | C2: figurative helpfulness, referent-based names/hashtags and an unresolved name retained without an invented type. |
| R07, R24 | 4, 10 | C3: opaque URL/identifier bodies alone produce the empty subjects array in one JSON object. |
| R08 | 4 | C4: surrounding prose establishes URL and identifier subjects without extracting meanings from their bodies. |
| R09–R12 | 5 | C5: two directly worded duck interpretations; notebook purchase stays independent of co-mention and statement order; no uncertainty commentary. |
| R13–R14 | 6 | C6: two cables are distinguished from their 2 m and 3 m lengths; units and referents are stated. |
| R15 | 6 | C7: stated addends and result of 2 + 3 = 5 remain; no unstated calculation is introduced. |
| R16 | 2 | C1: complete specific tissue/scrap subjects and cutting survive broader headings; visible output does not prove hidden enumeration order. |
| R17 | 2 | C2: nonliteral helpfulness and rhetorical appreciation are expressed subjects even without literal concept names. |
| R18 | 2 | C6: each named cable and the expressed counted pair remain separately represented. |
| R19 | 2 | C5: ducks, people and notebooks remain alongside their observation/purchase events. |
| R20–R23 | 8–9 | C1: preserved Food seasoning and Dog food role interpretations remain subject to calibration; compatible shared headings and every numbered copy retain complete source descendants, with each entry represented. General Food is not an exclusive-use restriction. |
| R25–R26 | 10 | C1: section-style numbering, parent precedence and number/context/subject field order. |
| R27–R28 | 10 | C1: contexts establish references and local purposes while also supporting unrestricted general headings. |
| R29–R31 | 7–8 | C1: unrestricted subjects and qualified specific subjects coexist; each heading is meaningful alone, and general headings need not retell the instance's role. |
| R32–R33 | 7 | C6: not-longer comparison retains negation, the relationship and both named measured cables. |
| R34 | 7 | C1: concise Salt and Dogs headings remain alongside complete specific subjects. |

| Tracked implication | Paragraphs | Existing example witness |
| --- | --- | --- |
| Combinations obey the same heading test | 2, 8–9 | C1: complete joint cutting descends from each partial action; partial actions do not descend from their joint action. |
| Context cannot repair a missing heading restriction | 8 | C1: Salt for food seasoning retains the explicit seasoning purpose; recipient-only tissue does not establish a feeding relationship. The former blanket Food exclusion was a grading error. |
| Every numbered compatible parent occurrence needs its collection | 9 | C1: both Dog food occurrences collect the complete supported ingredient and cutting subjects. |
| An unrestricted entity differs from its purpose-qualified instance | 7–8 | C1: Salt and Salt for food seasoning are distinct levels of generality. |
| Parent restrictions appear in the child's own wording | 7–8 | C1: complete cutting retains counted material participants and their food-ingredient/recipient roles. |

The later source-resolution, enclosing/list membership, local purpose and
finite equal-meaning requirements remain explicit. A source's equal-meaning
entry represents itself; no identical self-descendant is required. A complete
source appears below every compatible more-general returned heading occurrence,
not necessarily as a direct child. No optional broader-heading closure, exact
tree or grouped-output requirement is added. Equivalent wording remains allowed.

Independent semantic audits found no missing, weakened or newly introduced output
rule in the revision. The later [evaluator audit](../isolation-v1/README.md#evaluator-audit-after-the-food-correction)
finds that C1's preserved explanation incorrectly uses alternative uses to exclude
generic materials from Food. Its optional broader-heading placements do not
establish an incorrect output edge. The tested bytes remain frozen for provenance;
the explanation needs a versioned correction before another candidate. Earlier
preservation audits do not establish semantic correctness or model adherence.

## Provenance and verification

Native source edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.96/prompt-edits.json`) and template edits (`03bd9e45:sse_multivector/subject-prompt-goal-v1/asv6.96/edits.json`) pin
ASv6.95 and produce versioned revision receipts. The authored order check first
fails on ASv6.95 after validating all seven outputs through the production
subjects adapter: instructions remain after the examples. The focused checks
then inspect ASv6.96's exact example preservation, production validation,
scope/copy obligations, finite source representation and exact POST wrapper.
These offline checks verify authored artifacts; saved N096 production answers
provide the behavioral failure baseline.

Source SHA256: `4899be460978c5b561975d507b8a584b9c65e15f2b5cdd3c2229b42c34e2195b`.
The [fresh blinded comparison](../isolation-v1/guidance-consolidation-v1.md)
finishes 66 valid first answers: three trials of eleven development posts for
each prompt, with no errors, retries or reused answers. All 137 offline checks
pass. Every actual request matches its frozen input and every raw JSON answer
reaches validation unchanged. Instruction consolidation therefore does not
explain away the remaining failures as an adapter or delivery corruption.

Final bounded verdicts are ASv6.95 22 accepts/9 rejects/2 uncertain and ASv6.96
20 accepts/9 rejects/4 uncertain across 33 answers per arm after user calibration.
The earlier 19/10/4 result incorrectly rejected Food → Sea salt. This repeated
development sample does not demonstrate a benefit; it is not population accuracy.
Food → Sea salt is accepted after the user's correction; a full recheck finds no
other decisive failure in that N063 answer. ASv6.96 still omits the complete
shared trimming action in one N100 answer and loses formed
subjects from compatible branches. It is not a reliable correction. Disputed
N074 interpretations and implicit N100 origins remain separate uncertainties;
they are not used as confirmed failures. The comparison records original blind
judgments, explicit reconsiderations and the limits of agent/human calibration.
All eight prospective posts stay reserved. Wording approval, testing and adoption
are different decisions; this candidate is not adopted.
