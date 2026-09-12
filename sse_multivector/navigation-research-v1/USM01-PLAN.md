# USM01: contextual meanings with and without candidate restrictions

Status: selected, not yet run. [Research and prerequisite audit](./SOURCE-OCCURRENCE-GROUNDING.md).

## Question and construction role

Does unrestricted contextual matching add useful source meanings beyond a
generic lookup using the original word, while retaining correct interpretations?
The current dictionary lookup cannot recover beet when its input is boot.
This is a known input restriction; it is not yet evidence that unrestricted
matching will choose beet rather than another related or unrelated meaning.

The plausible construction path is source occurrences → contextual concepts →
shared, broader patterns → meaningful note destinations. This comparison tests
the first transition only. It does not add an alignment layer to the DRS parser.
If source-valid meanings improve, their actual construction consequences must
be traced before adopting the representation. Fine-grained roles, an exact
taxonomy and perfect word-sense accuracy are not prerequisites imposed here.

## Fixed inputs

Use all fifteen unchanged SGC01 descriptions from thirteen notes, including
the four that produced malformed DRS graphs. Their original notes, masks and
aliases remain audit evidence, not new encoder context. Freeze the existing
SPC01 token text/offsets and predicted lemma/POS; do not repair beet, tomatoes,
simmering or other annotations by hand.

Use all 134 NOUN/PROPN/VERB/ADJ/ADV occurrences identified in the lookup audit,
not just known failures. Encode each complete description with all its tokens;
the target is the current token's contextual representation. Assert the token
offsets against its exact description before inference. No extra subjects,
multiword targets, definitions or paraphrases are generated for this run.

These are word occurrences within generated descriptions, not SSE vectors or
new original-note masks. A success would not validate every generated
description or establish complete multiword extraction.

## One representation, three conditions

Use the released LMMS-SP-USM BERT-large-cased **sensekey** vectors and pinned
BERT/weight artifacts listed in the research record. Do not switch to the
separate synset vectors or SP-WSD profile.

Encode every occurrence once, normalize its vector, then score the same
released sense inventory in three conditions:

1. **Saved lemma:** restrict matches to the saved lemma and part of speech,
   following the released `match_senses` interpretation. An empty set remains
   empty; no most-frequent-sense fallback or manual correction.
2. **Surface word:** use WordNet's existing morphology on the original token,
   across noun, verb, adjective and adverb. Admit sensekeys for those lexical
   forms only, not every synonym in their synsets. This uses NLTK 3.9.2's
   `_morphy` followed by exact-name `lemmas` lookup, without special-case repairs.
3. **Unrestricted:** use all entries, without lemma/POS restrictions.

The surface-word condition is necessary: its candidate lookup already repairs
the known beet/tomatoes/simmering exclusions. Beating the saved-lemma condition
alone would not justify removing lexical restrictions generally. PROPN uses
NOUN in the saved-lemma condition, matching the audit's WordNet convention.

Retain the highest match and the top five distinct sensekeys for each
condition, including their canonical synset IDs and definitions. Synonymous
keys may map to the same synset: report that explicitly, not as independent
support. Additional lexical alternatives are diagnostic, not five accepted
subjects. No cutoff is fitted and no missing-sense rejection is assumed.

Use the author's evaluation convention: the last 24 hidden states in reverse
order with the first 24 published weights, mean WordPiece pooling per supplied
token, then normalization. Record that the 25th weight is unused, as in the
evaluation source; the embedding-build scripts use 25 states. Keep this choice
fixed across all conditions. This CPU/safetensors application is not a claim
to reproduce the published benchmark exactly.

## Hypothesis, alternatives and decisions

The hypothesis is that unrestricted matching supplies source-valid highest
matches unavailable or misranked under surface-word lookup, without enough
regressions to defeat its value for construction.

Competing explanations include:

- The useful change is simply bypassing erroneous lemmas. If surface-word
  lookup explains the gains, there is no demonstrated reason to drop lexical
  evidence and search the entire inventory.
- The intended meaning is available, but the contextual representation cannot
  rank it above merely associated meanings.
- Restricted matching is useful lexical evidence on ordinary cases even though
  its errors exclude correct meanings elsewhere.
- Neither condition can identify a sense absent from the inventory. Smoker's
  missing cooking-equipment sense must not become a false success by choosing
  a nearby person or a more specific, unsupported device.
- Target tokenization, the description itself or the inference implementation
  can fail independently of the representation.

Inspect the actual description and its original mask/note for every changed
highest match, all existing known failures and the unchanged controls. Record
separately whether the matched sense fits the encoder description and whether
that description/occurrence is supported by the original mask. Separate
an appropriate source meaning from a supported broader topic, a merely
associated concept and a genuinely unsupported interpretation. Preserve
reasonable ambiguity rather than force a unique dictionary answer.

Would either outcome change the next decision? Yes. Useful source-valid gains
beyond surface-word lookup, with manageable regressions, justify tracing
unrestricted matching through actual construction. If surface-word lookup
explains the gains, prefer that simpler restriction for the next investigation.
Strong gains only in the top five justify candidate proposal,
not automatic top-one assignment. Widespread unrelated matches instead argue
against unrestricted assignment; another cutoff cannot remove higher-ranked
wrong meanings while admitting lower-ranked correct ones. If implementation
fidelity is uncertain, resolve that before making a semantic conclusion.

The four newly processable descriptions are not credited as semantic coverage
merely because their outputs exist. Their interpretations require the same
audit. The beets/preparation ancestry gap and later SUMO errors remain separate
limitations even if individual words are interpreted correctly.

## Execution and preservation

Before inference, verify public asset hashes, native token/layer pooling and
safe local loading. Create minimal failing tests for any new runner behavior,
then implement the smallest production path and run relevant regressions.
Use local CPU, two Torch threads and one inference process. Do not rent compute,
call a paid API, execute unpinned downloaded code or load remote pickle objects.
Check available memory and cap loading allocations; never run this concurrently
with another model load. Verify no truncation and preserve empty candidates.

Save exact source identities, input hashes, model/resource hashes, code
snapshots, tokenization, target vectors, scores, actual runtime/memory, and
source-grounded judgments. Preserve the baseline and all previous results.
No UI packaging is part of this diagnostic. The next construction decision
must follow its evidence; this plan does not declare a replacement hierarchy.
