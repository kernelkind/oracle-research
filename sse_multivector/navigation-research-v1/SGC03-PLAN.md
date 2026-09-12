# SGC03: additional broader concepts in category construction

Status: pre-run design. No SGC03 construction or new inference has run.

## Capability and hypothesis

Can a general, released concept resource add meaningful parent–child paths
missing from SGC02, rather than merely produce larger or more numerous groups?
The source graphs already contain a correct cooking/brisket connection, but
their WordNet-only generalization order cannot connect it to the food-work
patterns expressed with nouns. Separate Food senses also lack a shared Food
parent. These are available-evidence limitations, not hypothesized density
problems. [Source evidence](./CONNECTED-PATTERN-CONSTRUCTION.md).

The hypothesis is that adding separately identified SUMO ancestors supplies
at least one new, source-supported broader category with meaningful narrowing
and improved coverage of the relevant available notes. A known mapping lookup,
an extra generic parent, or a renamed existing note set is insufficient.
Unexpected coherent paths can support the hypothesis; no exact hierarchy or
preferred number of categories is prescribed.

This tests construction with a fallible resource, not the proposition that
the augmented WordNet-to-SUMO order guarantees semantic containment. The
inspected Food mapping already disproves that universal claim: nourishment
for any animal does not imply human food. This mapping error does not by itself
establish that SUMO's internal subclass order is unsound.
The resulting local memberships and their derivations must be judged separately.
[Research and resource qualifications](./SEMANTIC-ORDER-RESOURCES.md).

## Fixed inputs and conditions

Keep SGC02's eleven accepted graphs from nine notes, the exact descriptions,
masks, note identities, native senses, actual edges, connection policy and
existing WordNet ancestors. Preserve all fifteen selected inputs and four
malformed exclusions. Do not repair source graphs, generate descriptions,
infer participants, choose a food-specific relation, or change a browser.

Use one pinned resource revision, with three construction conditions:

1. **WordNet:** replay the complete SGC02 construction.
2. **Additional noun ancestors:** add eligible WordNet-noun mappings and their
   SUMO subclass ancestors, keeping the original senses distinct.
3. **Additional noun and verb ancestors:** add eligible verb mappings as well,
   with everything else identical to condition 2.

Conditions 2–3 distinguish new noun-level category connections from the added
cross-part-of-speech reachability. Their effects are not inferred from the final
counts alone. No threshold sweep, replacement parser or new model is involved.

The original WordNet patterns and memberships must remain unchanged in every
condition. New intermediary ancestors can change generating links and which
patterns have most-specific status; retain and compare those changes explicitly.
The original Food and Activity patterns are not silently repaired or renamed.

## Resource admission before construction

Use SUMO revision `abcb7cc1090c5b35cbfacd9e44e50e50c7434433` and the already
frozen WordNet 3.0 offsets. Preserve original mapping annotations and source
locations. Keep `SUMO:` concept identities separate from WordNet identities;
add no SUMO-to-WordNet reverse mapping and no equivalence collapse.

The initially eligible mappings are positive equivalence/subsumption mappings
to declared classes, used only as candidate forward ancestors. Class ancestry
comes from explicit top-level ground subclass statements. Instance, complement,
attribute-instance and relation-valued mappings must not be recast as subclass
edges. Adjective and adverb mappings remain outside this noun/verb intervention;
their original WordNet evidence is retained. Do not infer participants or new
facts from logical axioms.

Before construction, verify the released mapping syntax, treatment of multiple
annotations, class declarations, closure and resource notices. Record unsupported
or unresolvable mappings rather than guess their semantics. Resource parsing
must distinguish ground facts from quoted text and conditional axioms. Any
cycle must be reported rather than silently collapsed. If these checks require
changing the treatment, amend this plan before running and preserve the reason.

Save the exact generalization paths used by each candidate. Do not whitelist
food mappings because they give preferred results, or blacklist a known bad
mapping to repair this sample. The scope is deliberately approximate: forward
use prevents identity collapse, but does not correct an invalid broadening.
Known scope mismatches remain flagged independently of local source support.

## Controls and semantic reading

Inspect every new or changed recurring representative and its native witnesses,
including new meanings whose note set already existed. Also inspect removed
representatives and every new recurring note set. For every claimed improvement,
retain a complete actual parent–child path, source masks inline in full notes,
all memberships, and the
notes excluded at each step. Interpret the class definitions and graph pattern,
not just the displayed word Food, Activity or Preparation.

Compare each claimed connected-category gain with:

- Every existing WordNet-only category with the same note set or an equally
  useful source-supported route.
- Its single-concept categories under the same augmented order. A Food–Process
  category returning exactly Food's notes does not establish a useful extra
  navigation step merely because its pattern is longer.
- The intersection of its endpoint singleton **source-row** sets under that
  same order. An equal intersection means native connections have not shown
  additional discrimination in this sample. An unequal intersection requires
  inspecting the excluded source occurrences; inequality alone is not success.

Complete paths must show a meaningful narrowing, not merely a smaller note set.
Sibling categories may overlap. A broad Food destination can be useful without
matching an imagined finer taxonomy. Inspect incorrect additions and new
misleading paths alongside recoveries; do not present only the motivating food
witnesses. Four excluded parser outputs remain missing evidence, not negatives.

Separate three judgments for a new admission: whether the original source
supports the category, whether the native source graph supplies the claimed
connection, and whether the mapping chain is semantically justified. A correct
note at the end does not vindicate a wrong source sense or mapping. No global
validity or unseen-note accuracy is inferred from this small selected sample.

## Competing explanations and decisions

Apparent gains may come from a useful broader concept, a generic union, a
redundant parent, an invalid mapping, or a source error whose final note happens
to fit. Missing gains may come from absent source connections, inappropriate
ancestors, or an inadequate construction/selection rule. Conditions 2–3 and
the same-order singleton controls distinguish some of these explanations;
source and mapping inspection must distinguish the rest.

Would either outcome change the next decision?

- Meaningful additional paths with justified source witnesses and mappings
  support testing the construction on different, more varied source graphs.
  Category selection and computational growth would remain separate work.
- Locally plausible recovery depending on a known invalid mapping is evidence
  for an approximate candidate only. It does not justify adopting that mapping
  as semantic containment or scaling it without a general treatment of the
  mismatch. Do not claim the original missing category was repaired.
- Only generic or duplicate paths provide no demonstrated navigation gain.
  Do not expand ontology machinery merely because the expected union appears.
- If appropriate ancestors exist but no useful path is constructed, investigate
  the construction or selection restriction. If the available ancestor meanings
  are inappropriate, reconsider the resource rather than tune a frequency cutoff.

## Preservation and verification

Create production-path tests before implementation; verify their expected
initial failures. Test typed mappings, exact offsets, no invented source edges,
no reverse sense collapse, parsing boundaries, closure, unchanged WordNet
supports, deterministic construction and full witness provenance. Structural
consistency does not certify semantics.

Save every condition, resource revision/hash/notice, source snapshot, native
witness, candidate inventory and semantic audit, including one-note output and
unhelpful candidates. Keep frozen SGC01/SGC02/GDC09 bytes untouched. Use local
deterministic processing and public resource reads only; no paid service or
inference is part of this plan. Review-tool packaging remains reserved for goal
wrap-up and requires a demonstrated improvement.
