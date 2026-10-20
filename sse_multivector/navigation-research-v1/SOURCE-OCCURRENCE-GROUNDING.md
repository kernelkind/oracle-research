# Grounding concepts in source occurrences

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

The next representation need not repair the existing DRS graph. There are
already source-token offsets for all fifteen selected descriptions. A contextual
sense matcher can operate on those occurrences directly. However, reusing the
saved word parser's lemma and part-of-speech restrictions would exclude some
correct meanings before a model sees them.

This prerequisite audit changed the next experiment, not the baseline hierarchy.
The audit itself used no new model inference. The subsequent
[USM01 comparison is now complete](./USM01-RESULTS.md). Original notes, masks,
descriptions, native graphs, SGC03 and the browser remain unchanged.

## Existing source occurrences

`SPC01/native/parses.json` contains the unchanged descriptions, token text,
character offsets, predicted lemmas and parts of speech. All fifteen SGC01
descriptions match exactly; every token's saved character range recovers its
text. Offsets refer to the **generated description**, not the original note.
The original note and mask remain separate evidence for whether that
description is supported.

Inspecting every NOUN, PROPN, VERB, ADJ and ADV occurrence gives 134 targets
from fifteen descriptions and thirteen notes. This includes all four
descriptions excluded by SGC01's malformed native output. The audit does not
hand-select only the words previously misinterpreted by DRS.

Frozen WordNet lookups give these mechanical observations:

| Lookup input | Occurrences with no candidate |
| --- | ---: |
| Saved lemma and saved part of speech | 9 |
| Actual token text and saved part of speech | 6 |
| Actual token text, any part of speech | 2 |

Four occurrences change candidate sets when actual token text replaces the
saved lemma while part of speech remains fixed:

| Source | Actual word | Saved lemma | Result of the substitution |
| --- | --- | --- | --- |
| Row 187 · N026 | tomatoes | tomatoe | Empty set becomes the two tomato senses. |
| Row 378 · N022 | beet | boot | Seven unrelated noun candidates become the two beet senses. |
| Row 544 · N096 | tomatoes | tomatoe | Empty set becomes the two tomato senses. |
| Row 544 · N096 | simmering | simmere | Empty set becomes `simmer.v.01`. |

These are candidate-set facts, not WSD accuracy results. A nonempty set can
still omit the intended meaning. Conversely, an empty surface lookup can be
an inflection, spelling or multiword-association problem, not an absent concept.
The two empty any-part-of-speech lookups are Bolognaise and sautéing. This does
not prove that WordNet lacks related cooking concepts.

The earlier grilling concern needs precision: the saved noun analysis of
“grilling” **does** find `broil.n.01`, defined as cooking by direct radiant
heat. It must not be counted as another demonstrated candidate exclusion.
The DRS-generated `grilling.v.01` is a separate invalid-identifier problem.

The complete changed candidate sets, totals and input hashes are in
the lookup audit (`./USM01/lookup-audit.json`). This audit used NLTK 3.9.2 and
the same WordNet 3.0 archive as [the mapping audit](./MAPPING-VALIDATION.md).
The script below reproduces the totals without running a neural model.

## Whether DRS connections are necessary

The [SGC03 control](./ONTOLOGY-CONSTRUCTION.md#what-the-connection-control-establishes)
intersects singleton **source-row** memberships. Rechecking all 157 saved
representatives finds 96 paired patterns with added rows: 212 pair–row additions
in total. Of those, 194 can use two distinct native concept occurrences; 18
require reusing one occurrence for both endpoints. Therefore, unrestricted
intersection is not a clean ablation of edges alone.

Those counts do not measure new categories, new notes or semantic errors.
For concrete existing patterns, deduplicating source notes gives:

| Existing pattern | Notes added by singleton-row intersection |
| --- | --- |
| Food / IntentionalProcess · `G0953c4544ac6b557bbcc` | N039, N094 |
| Food / Process · `Gd0e51a46f88d73d8638a` | N039 |
| Food / preparation · `G58b7c19d4e4ae0af7655` | None |
| Food / preservation · `G63a768150ba5cfe1fe77` | None |
| ContentBearingProcess / Process · `G6d262e2a81fd2bce2749` | None; another source row belongs to an existing N094 member. |
| IntentionalProcess / SocialInteraction · `G81d9b4fc37dceb893e96` | N039 |
| SocialRole / person · `G50c9e382a3b151da1f8d` | None |

N039 discusses weather threatening outdoor grilling, so its food-activity
membership is plausible. But the SocialInteraction admission comes through
the wrong professional-visits meaning of “rounds” of storms. N094 discusses
coffee experience, but its knowledge/learning interpretation was already wrong.
The existing edge restriction also retains the smoker/person error in N085.
These examples do not show that edges distinguish valid from invalid
combinations of **correctly interpreted** source concepts.

The eleven accepted descriptions do explicitly connect several pairs omitted
by the immediate-edge rule: coffee and experience; food and storage;
preparation and salt; preparation and mixing. Some remain connected through
longer native paths. This is not proof that all graph structure is useless.
It is insufficient evidence for preserving DRS and adding another model plus
an alignment layer merely to repair it.

Coffee/Learning has two source rows, 88 and 572, but only one note, N094.
It is not a new recurring two-note category. All source texts and native
connections remain available in [SGC01's evidence](./SGC01/construction/SOURCE-EVIDENCE.md).

## Two barriers to the beets preparation path

Row 904, N022, supplies this unchanged description:

> The author is preparing this year's garden-grown beets for preservation by freezing.

The native graph has `fix.v.12` at node 3 and `beet.n.02` at node 7, without
a direct connection. The frozen augmented ancestors of `fix.v.12` are:

```text
fix.v.12
change.v.01
SUMO:Entity
SUMO:Physical
SUMO:Process
SUMO:IntentionalProcess
```

`preparation.n.01` is absent, and no other row-904 node supplies it. Thus the
Food/preparation pattern cannot include the note merely by deleting the edge
restriction. Adding only a direct edge would also be insufficient. This
corrects the earlier explanation that emphasized the missing connection alone.
The existing sense is plausible; changing it to force the desired ancestry
would be a hand-repair, not a demonstrated semantic improvement.

## A directly relevant alternative

LMMS represents known dictionary senses using contextual examples, WordNet
relations and glosses. Its unrestricted matching task compares a target in
context against the entire inventory, without lemma/POS filtering. The later
version weights encoder layers using a validation task and uses SemCor plus
unambiguous-word examples. Its neural encoder is pretrained rather than
fine-tuned into a new definition-pair classifier.[^lmms]

The BERT-large unrestricted result is 60.8 sensekey F1 and 86.7 reported P@5;
these are different measures, not interchangeable accuracy claims. Evaluation
supplies target occurrences and does not establish missing-sense rejection,
raw-text target discovery or hierarchy construction. A nearest meaning need
not be correct: the released demonstration retrieves Capone for Corleone.[^lmms][^demo]

This mechanism addresses a demonstrated candidate-filter limitation. It is
not adopted merely because it is inexpensive or available. The controlled
[USM01 plan](./USM01-PLAN.md) compares saved-lemma filtering, original-word
morphological lookup and unrestricted matching using the same vectors.
The original-word control already repairs the known lemma exclusions; beating
only the faulty parser input would not establish value from removing lexical
restrictions. Correct controls and unavailable meanings are included. The
comparison does not preserve or align to DRS nodes.

ESCHER remains plausible for choosing among supplied candidates, but cannot
recover a meaning already removed from that candidate set. MWE-aware input
handling and original-note context remain separate questions; this investigation
does not silently replace descriptions with notes or infer new source topics.

## Implementation fit and reproducibility

The selected BERT variant uses the author's Transformers token-pooling path,
avoiding the separate Fairseq implementation used for RoBERTa. BERT's source
still hardcodes CUDA. A safe CPU implementation must preserve token and layer
pooling, use pinned safetensors and record its adaptations.[^encoder]

The released layer file has 25 weights. Annotation/gloss construction uses
25 states, but evaluation selects 24 and ignores the last weight, `0.00652`.
USM01 fixes the evaluation convention for all conditions rather than silently
reconciling that discrepancy or tuning it on this corpus.[^builders][^evaluation]

At this prerequisite checkpoint, public metadata was checked independently
without downloading weights. The subsequent execution record verifies the
downloaded identities:

| Resource | Pinned identity |
| --- | --- |
| LMMS code | `65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1` |
| BERT model | `google-bert/bert-large-cased` at `06fa25dc1b6e034e91607fd67c247051ccaeff65` |
| Safetensors | 1,338,695,354 bytes; SHA-256 `137eefff71696316817af618eb19f72e277daab3225b56584848c5723a47cc59` |
| Sensekey ZIP | Figshare 21975734 v1, file 38999342; 640,557,312 bytes; published MD5 `d0ea3c709d2e8e62c0ff92cb127a1dab` |
| Layer-weight file | SHA-256 `3bde7e1ee2b8903a89033901094fd0e305566d195db577d77ecb8b892d6cfa95` |

The BERT release is Apache-2.0, the sense-vector release CC BY 4.0, and LMMS
code GPL-3.0-or-later. These are separate artifacts, not one blanket license.
The checkpoint/ZIP hashes still require verification after any download.
No paid resource is needed for the planned local CPU diagnostic.[^assets]

## Reproducing the lookup audit

Run from the repository root with the existing NLTK environment:

```sh
env PYTHONDONTWRITEBYTECODE=1 NLTK_DATA=/tmp/navigation-wordnet-data \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-nli-probe-venv/bin/python - <<'PY'
import json
from pathlib import Path
from nltk.corpus import wordnet as wn

root = Path('sse_multivector/navigation-research-v1')
records = json.loads((root / 'SGC01/native/inputs.json').read_bytes())
parses = {p['row']: p for p in json.loads(
    (root / 'SPC01/native/parses.json').read_bytes())}
parts = {'NOUN': 'n', 'PROPN': 'n', 'VERB': 'v', 'ADJ': 'a', 'ADV': 'r'}
observations = []
for record in records:
    parsed = parses[record['row']]
    assert parsed['subject'] == record['subject']
    for sentence in parsed['sentences']:
        for word in sentence:
            assert record['subject'][word['start_char']:word['end_char']] == word['text']
            if word['upos'] not in parts:
                continue
            pos = parts[word['upos']]
            observations.append([
                {s.name() for s in wn.synsets(word['lemma'], pos=pos)},
                {s.name() for s in wn.synsets(word['text'], pos=pos)},
                {s.name() for s in wn.synsets(word['text'])},
            ])
print(len(records), len({r['note'] for r in records}), len(observations))
print([sum(not row[i] for row in observations) for i in range(3)])
print(sum(row[0] != row[1] for row in observations))
PY
```

Verified output: `15 13 134`, then `[9, 6, 2]`, then `4`.
The edge-control counts were independently reproduced using SGC03's unchanged
`augment` function, fixed representatives and original node identities. They
are dependency observations, not a construction rerun or adopted rule.

## Sources

[^lmms]: Loureiro et al., [LMMS Reloaded: Transformer-based Sense Embeddings for Disambiguation and Beyond](https://arxiv.org/pdf/2105.12449), Artificial Intelligence 2022, §§4–5 and 7.2/Table 11. The selected USM representation must not be confused with the separately trained layer profile used for lemma-filtered WSD.
[^demo]: Author [matching demonstration](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/demo_matching.py) and [candidate filtering implementation](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/vectorspace.py#L102).
[^encoder]: Author [Transformers encoder](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/transformers_encoder.py), pinned source inspected completely.
[^builders]: Author [annotation embedding](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/scripts/embed_annotations.py) and [gloss embedding](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/scripts/embed_glosses.py) scripts.
[^evaluation]: Author [USM evaluation](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/evaluation/eval_usm.py) and [BERT layer weights](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/data/weights/lmms-sp-usm.bert-large-cased.weights.txt).
[^assets]: [Figshare version metadata](https://api.figshare.com/v2/articles/21975734/versions/1), [BERT release](https://huggingface.co/google-bert/bert-large-cased/tree/06fa25dc1b6e034e91607fd67c247051ccaeff65), and [LMMS license](https://github.com/danlou/LMMS/blob/65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1/LICENSE). Metadata inspection is not runtime verification.
