# Grounded descriptions and phrase-model neighborhoods

PPR01 finds useful semantic evidence in existing subject descriptions, but does
not establish an automatic membership or parent-construction rule. The base
Sentence-BERT handles the rosemary/bread connection that literal adjacency lost.
It also separates coffee-taste experience from experiencing internet loss.
Phrase-BERT is not a consistent improvement over that base.

Retain base affinity as possible **proposal evidence**, not a rule for accepting
categories. Missing preservation evidence remains a concrete limitation. No
hierarchy, subject, source mask or browser changed.

## Experiment and evidence

The [pre-run plan](./PPR01-PLAN.md) selects four diagnostic subjects before scoring.
Both models encode the same 945 existing subject records. Identical strings
require only 927 encodings, but all records and notes remain. The models read the
**subject string**, not the original post or concatenated mask. This is not an
SSE rerun or a comparison with its original vectors.

Row numbers below index saved subject/mask records. For example, row 258 comes
from N017/V120 and produces a new description vector under each model. Original
vector aliases identify the source masks, not these new embeddings.

For each query, rank other notes by their closest subject record. One note can
occupy only one position. Preserve the winning record: finding a correct note
through an unrelated mask is different from correctly matching its subject.
Euclidean distance is primary, matching the training loss; cosine is a
prespecified sensitivity control. Neither is an equivalence probability.

The [audit](./PPR01/audit.json) contains all sixteen ten-note lists, fixed
diagnostic scores, semantic judgments and full originals/masks for 90 inspected
records from 50 notes. Unknown neighbors are not automatic negatives. Broader
shared subjects are allowed; identical claims or actions are unnecessary.

## Morning greetings

Query row 258 / N017 / V120:

> The author wishes readers a good morning.

Source mask: ⟦Good morning⟧.

The base model's ten nearest other notes under Euclidean distance contain all
nine other known morning greetings and N018's afternoon greeting. The afternoon
greeting is a reasonable broader connection, not a semantic failure. This
recovers wording differences that split CAP04's literal patterns.

Phrase-BERT's ten winning masks contain only one morning greeting and the
afternoon greeting. Others concern coffee, expecting a good day, health,
sleepiness or chicken care. Two returned notes independently greet the reader,
but their winning masks do not. For example:

| Exact other record | Subject | Base distance | Phrase distance |
|---|---|---:|---:|
| 192 / N040 / V310 | A good-morning greeting to the Siamstr community. | 14.43321 | 13.09519 |
| 551 / N060 / V503 | The post author made coffee today. | 18.01704 | 11.58869 |

Lower distance means nearer within each model. The first mask is
⟦GM⟧ ⟦siamstr⟧. The second is ⟦Made⟧ ⟦coffee⟧ ⟦today⟧, from:

> Made my coffee with raw cream and a raw egg yolk today #coffeechain

The base places the greeting nearer; Phrase-BERT reverses that ordering. The
experiment does not isolate whether reporting style, lexical association or
another learned feature causes the reversal. A cutoff cannot reverse it.

Cosine returns the same ten notes for the base but selects N058's hot-coffee
mask instead of its greeting mask. Phrase-BERT retains the same broad pattern
under both metrics. Metric choice affects which evidence supplies membership,
not only which note appears.

## Rosemary in bread

Query row 669 / N037 / V290 is “Rosemary in sourdough bread,” supported by
⟦rosemary⟧ ⟦sourdough bread⟧.

Relevant record 254 / N072 / V665 says:

> The author added fresh rosemary and cranberries to the Irish soda bread.

Its mask is ⟦Irish soda bread⟧ ⟦I added fresh rosemary and cranberries⟧.
The full original explicitly says these were added to that bread. Different
bread types and extra ingredients do not invalidate the shared rosemary-in-bread
subject. All original wording and URLs remain in the audit.

| Model | Distance to record 254 | Cosine | N072's note position |
|---|---:|---:|---:|
| Base | 12.55519 | .67567 | 2 under both metrics |
| Phrase | 10.63058 | .79218 | 19 under both metrics |

Raw scores are not a common quality scale across models. Despite the higher
cosine, Phrase-BERT places many other foods ahead of N072. Its distance to
Tandoori-spiced chicken with yogurt is 7.99711, versus 10.63058 to the rosemary
bread. Both models put plain sourdough bread first: a legitimate broader match,
not a failure. Other food neighbors may also support broader categories.

The discriminating result is that the base keeps the explicit cross-note
combination accessible and Phrase-BERT weakens that ordering. This is not an
exact-equivalence claim or an assertion that every other food neighbor is invalid.

## Two different coffee experiences

Query row 572 / N094 / V852:

> Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee.

Source mask: ⟦Decafe coffee drinkers⟧ ⟦for the experience⟧.

N086's record 854 / V792 describes experiencing coffee with an individual taste
profile. Its mask selects ⟦You’ve had coffee. But have you had your coffee?⟧
⟦taste profile that’s uniquely yours⟧. This supports a common coffee-experience
subject, without making the same claim about decaffeination.

N065's record 345 / V561 instead describes making coffee-shop operators
experience losing internet access. Its mask is ⟦Coffee shop⟧
⟦Felt like changing their router/ap passwords so they⟧ ⟦experience⟧
⟦freedom from internet⟧.

| Exact other record | Base distance | Base cosine | Phrase distance | Phrase cosine |
|---|---:|---:|---:|---:|
| 854: individual coffee-taste experience | 13.05038 | .63825 | 12.08643 | .71226 |
| 345: operators losing internet access | 18.00989 | .29781 | 13.10206 | .65009 |

Both models order this contrast usefully. Complete descriptions distinguish the
attachments that CAP04's word-order pattern did not. This evidence goes beyond
merely reproducing the already-demonstrated greeting recovery.

Neither ten-note list isolates a coffee-experience category. The base mainly
returns ordinary coffee meanings and reaches N086 through its broader “The
reader has had coffee” record. Phrase-BERT's nearest selected mask is ⟦#keto⟧
from N041. The full N041 note separately discusses not needing coffee, so calling
the **note** unrelated would be wrong. Its selected keto mask does not supply
that coffee connection. Other beverage or culinary-enjoyment neighbors may be
valid broader associations, not certified members of the narrower subject.

## Food preservation

Query row 484 / N100 / V942 is “Food preservation,” supported by
⟦foodpreservation⟧. Its full note also describes using a vacuum sealer.

N013's record 468 / V100 explicitly describes canning stock for storage. Its
mask selects ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦pressure can⟧
⟦store in the pantry⟧. N022's record 904 / V149 says:

> The author is preparing this year's garden-grown beets for preservation by freezing.

Its mask selects ⟦This year’s beets⟧ ⟦ready for the freezer⟧ ⟦raised bed⟧.
The original also says the beets are vacuum sealed. Preservation is supported
by the text, not an image or URL inference.

| Fixed record | Base distance | Base cosine | Phrase distance | Phrase cosine |
|---|---:|---:|---:|---:|
| 468: canning chicken stock | 15.01282 | .53562 | 9.60405 | .83352 |
| 904: preserving beets by freezing | 18.71541 | .25912 | 11.99329 | .72993 |
| 414: carnivore diet | 15.50330 | .49176 | 9.84413 | .82408 |

Phrase-BERT improves N013's note position from fifth to first. N022 improves
from 23rd to 14th under Euclidean distance and 28th to 17th under cosine. These
note positions use each note's best record: the base selects a beet-side-dishes
record, while Phrase-BERT selects explicit freezing record 904.

Ten is an inspection window, not a category boundary. Being outside it does not
alone prove failure. The membership limitation is that both models place
non-preservation diet evidence ahead of explicit freezing evidence. A threshold
admitting the latter would also admit the former. Both can fit a broader Food
topic; that does not place both under Food preservation. The missing containment
decision cannot be read directly from either affinity score.

## Construction decision

The base can help propose related descriptions while retaining some meaning
that word patterns lost. This does not justify grouping a fixed number of its
neighbors, merging equivalent descriptions, or turning its scores into parent
relations. Phrase-BERT's preservation gain comes with regressions elsewhere;
do not replace the base or rewrite frozen subjects on this evidence.

The complete-method reassessment is concrete: a full expression can help with
attachment, but affinity still mixes a subject with broader neighbors. We need
evidence of **what common meaning is preserved**, not merely close descriptions.
Next, investigate retaining explicit compositional relationships as candidate
evidence alongside affinity, before accepting shared or broader descriptions.
Any parser or relation model must first demonstrate task fit; neither is
selected here. These source examples specify a missing capability, not a
canonical taxonomy. Equivalence, membership and parent construction remain open.

## Verification and reproduction

Both models have 109,482,240 parameters. They ran sequentially on two CPU threads
in float32. Each initial encoding pass took about 15 seconds; peak process RSS
was about 4.9 GiB. No paid service, GPU or frontier call was used. New downloads
were limited to the two public checkpoints and configuration/tokenizer files.

The official three-phrase Phrase-BERT cosine example matches within 6e-8.
All inputs fit the shared 128-token maximum; the observed maximum was 61.
Three new tests initially failed because the module was missing. A preceding
test launch hit a missing Nix library path; that was corrected before the
expected missing-module failure was verified. All 41 relevant tests pass.

Both complete runs were repeated offline. Vectors, native controls, input files,
all scores, neighborhoods and runner snapshots were byte-identical. Timing and
peak memory are naturally separate measurements, not claimed identical.

[PPR01/base](./PPR01/base/) and [PPR01/phrase](./PPR01/phrase/) retain all inputs,
raw vectors, pairwise scores, package versions, native controls and model/code
hashes. The [audit](./PPR01/audit.json) retains full source evidence and the
judgments above. No full-corpus semantic accuracy is claimed.

Reproduce from the repository root with an unused output directory, then repeat
with `--model base` and a different output path:

```sh
env LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 \
  /tmp/oracle-nli-probe-venv/bin/python sse_multivector/phrase_description_probe.py \
  --input sse_multivector/navigation-research-v1/CAP04/result.json \
  --cache /tmp/oracle-phrase-probe-cache --model phrase \
  --output /tmp/ppr01-another-replay/phrase
```

The offline flag assumes the pinned public checkpoints are already cached.
No account credential is required. Replays never overwrite previous artifacts.

## Sources

The [pre-run plan](./PPR01-PLAN.md) records the method review, exact revisions
and primary sources: [Wang et al., Phrase-BERT (2021)](https://aclanthology.org/2021.emnlp-main.846.pdf)
and the [official model](https://huggingface.co/whaleloops/phrase-bert/tree/6f68f4dc2d28aadefa038c79023dc7dfd51f6495).
Numerical results and semantic judgments here are local PPR01 observations, not
the paper's benchmark results.
