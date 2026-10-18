# Whole-note admission audit v1 — experimental findings

The later matched [mean-centering trial](hierarchy-reference-centering-v1.md)
reuses this frozen sample, preserving these original assessments and recording
changed-route reviews separately. It retains useful note routes but does not
consistently reduce unwanted extra root placements.

The unchanged full-meaning candidate recovers useful note routes, but also
produces substantial wrong-root placements. This audit does not justify calling
it a quality-preserving automatic admission pass. That is a practical error
tradeoff, not a requirement for perfect labels or complete recovery.

No hierarchy, prompt, score, boundary or source membership changed. There were
no LLM calls, encodings, training or paid resources. New judgments below are
provisional agent assessments, not new human gold.

## What was audited

Use the completed `MM_coverage` decisions: independently compare each incoming
full-meaning vector against fixed accepted-only fusion members, with its whole
source note excluded and the existing reference-note-coverage boundaries.
Neither synthetic root vectors nor outsider-to-outsider connections are used.

For each corpus, select 24 proposed **distinct notes** by a frozen hash ordering.
Then add separately reported cases until every available root has at least two
reviewed proposed notes. HR36 requires three supplemental notes; HR37 requires
none. Independently select eight eligible unproposed notes per corpus to screen
for missed matches. Freeze this selection before whole-note assessment.

Review all selected meanings and root routes alongside the full original post
and all original accepted reference meanings, including references unassigned
by fusion. Actual accepted topical families supply the scope; synthetic root
names do not define it. The post can clarify identity and roles without silently
restricting every broad meaning to the particular use in that post. Open family
extensions are provisional, not containment claims beneath a particular example.

A proposed note is useful when at least one **actually selected** entry/root
route is supported. An unselected plausible heading cannot rescue a proposal.
Record the correctness of each selected root separately: one good route does
not excuse unrelated extra placements. If no route is clearly useful but one
is unresolved, keep the note unresolved. Existing exact-entry judgments stay
unchanged; another valid heading can rescue the note without overturning an
old wrong heading. No prior-entry conflicts were found.

The samples are small and conditional on this method's proposals. Their results
are not a corpus-wide accuracy or recall estimate. Root supplements must not be
pooled into primary sample rates; multiple root assignments from one note are
not independent observations.

## Results on primary proposed-note samples

| Corpus | Proposed notes reviewed | Useful route | Wrong routes only | Unresolved |
|---|---:|---:|---:|---:|
| HR36 | 24 | 19 | 2 | 3 |
| HR37 | 24 | 18 | 5 | 1 |

This is better than judging a whole note by one bad heading. For example, the
HR36 day-trader post retains a valid **Day traders** finance route even though
its previously rejected **Office absence** heading remains wrong. The software
fix post has a valid software route despite being wrongly placed under gaming.

The three supplemental HR36 notes all have useful routes: approval, a space-news
feature with aerospace companies/Canada, and an LLM question. They establish
coverage of the rarer sampled roots, not three more random successes.

### Selected-root quality is a separate problem

| Corpus | Primary selected-root assignments | Supported | Unsupported | Unresolved |
|---|---:|---:|---:|---:|
| HR36 | 38 | 26 | 5 | 7 |
| HR37 | 72 | 40 | 22 | 10 |

Three useful HR36 notes and eight useful HR37 notes also have at least one
unsupported extra root. Counting only whether a note is reachable would hide
those placements and the resulting browsing noise.

The most problematic sampled HR37 collection is **C00005**: 8 of 20 selected
placements are supported, 10 unsupported and 2 unresolved. Its actual families
include technology/software, finance, language learning and gaming. The bad
placements include generic students, declarations of love, biological topics,
clothing needs, decisive moments and unrestricted creators. Merely learning,
expressing something, having a function, or determining an outcome does not
establish the narrower roles supplied by those accepted families.

HR37 C00004 has 9 supported, 5 unsupported and 3 unresolved assignments among
17. Its Games/Communication/organized Events families are confused with generic
software operations, clothing requirements, productive work and abstract decisive
time points. The exact old **Asynchronous operations** rejection is preserved.
HR37 C00006 has 5 supported, 4 unsupported and 1 unresolved among 10: cryptographic
values, software operations and psychoactive substances do not acquire an
emotional/religious role merely by affecting states or outcomes.

Concrete whole-note errors include:

- A hallucinogen topic placed under technical and emotional/religious families,
  with no supported selected route.
- A students topic placed under technology/language learning without that role.
- Travel, luggage and clothing requirements assigned to content, interpersonal
  and technical families without an established matching role.
- An abstract decisive moment assigned to four roots without a supported role.
- A political-establishment topic assigned to publication/commerce/science solely
  on a selected meaning that establishes political power instead.

Borderline scope is retained as unresolved: general work versus business or
emotional labor; utilitarian video versus art; generic predictive models versus
AI; and culinary instructions versus the broad technical-method family. The
finding does not depend on declaring every ambiguous case an error.

## Unproposed-note screen

| Corpus | Notes screened | Plausible missed fit | No supported fit found | Unresolved |
|---|---:|---:|---:|---:|
| HR36 | 8 | 4 | 2 | 2 |
| HR37 | 8 | 5 | 1 | 2 |

These are provisional judgments about omitted notes with usable meanings, not a
demand that every note fit a root. Specific examples:

- HR36 has two omitted Japanese **Nostr relay** meanings that explicitly define
  the event-relay servers already represented by many accepted Network relays.
  A Japanese **Books** meaning also has a plausible Content route. These are
  cross-language misses, without proving language is the sole cause.
- The HR36 protest note has a **Texas** entry matching accepted U.S. states;
  its organized-public-protest entry also matches the accepted Events family.
- HR37 **Buses** and **Aircraft** explicitly denote designed practical vehicles,
  fitting the broad accepted Technology meanings. Do not impose a digital-only
  limit. This does not endorse the previous wrong Bus/Data-transfer placement.
- HR37 association football fits Games/Competitions; **Chicago** has an explicit
  United States geographic role. These are missed routes through supplied entries.
- A Canadian politician/provincial policy is a plausible open extension of the
  accepted government/international-policy family. This is not putting Canada
  beneath the United States or endorsing the prior Data/mining clock-policy routes.

Cats/meowing, kinship families and unrestricted botanical plants need not fit
these particular root collections. Opaque `p-worm ... build` and Pollerama
identities remain unresolved. No external app identity is invented.

## Practical interpretation

A useful majority of the proposed notes have sound routes in both corpora.
The method has genuine coverage value. However, the wrong-only notes and the
unsupported extra-root placements are substantial enough that unchanged,
unrestricted automatic admission is not yet demonstrated to preserve browsing
quality. Correctness cannot be judged from potential note-count gains alone.
No arbitrary target accuracy or zero-error gate is imposed here.

Do not run another boundary sweep to make these labels look perfect. A focused
next hypothesis is whether a shared component of definition-style meaning
vectors is contributing to unrelated matches, such as generic software roles
against organized events or biological processes against emotional/technical
families. A saved-vector postprocessing test could examine that hypothesis;
this audit does not establish the cause or authorize a new representation.

## Frozen evidence and verification

Task directory: `target/food-halves-v1/whole-note-admission-audit-v1/` in
`oracle-mvp-hierarchy-food-halves-v1`, retained through its external-storage
symlink. Plan SHA256:
`0d1a640e46eee35c238f841c1bf952c449184bb27827768bd28799b98fa3b5cb`.

- `selection.json`: seed, populations, 48 primary notes, 3 root supplements and
  16 unproposed notes; chosen before these assessments.
- `review-input.json`: full posts, exact supplied meanings, selected routes and
  preserved prior entry judgments for all 67 distinct reviewed notes.
- `root-references.json`: all original accepted reference meanings and the
  fixed fusion memberships for the twelve actual root collections.
- `assessments.json` / `root-assessments.json`: every note/root judgment,
  selected-entry witnesses, reasons and original entry judgments.
- `summary.json`, `primary-root-summary.json` and `review.md`: separate primary,
  supplemental and omitted populations, plus a compact index of every case.
- `verification.json`: every selected case covered, all supported routes have
  selected witnesses, no prior-entry conflicts, source/selection hashes intact,
  and no numerical decisions or memberships altered.

HR36 has 254 eligible omitted notes, with 239 proposed and 15 not proposed;
63 additional omitted notes have no usable meanings. HR37 has 290 eligible
omitted notes, with 261 proposed and 29 not proposed; 88 more lack usable meanings.
The audit cannot measure admission performance on missing meanings. Original
post collections and review cases preserve ASv6.100 provenance. Generated data
and full post text remain ignored; source code and prompts are unchanged.
