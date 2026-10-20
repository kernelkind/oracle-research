# Individual-category discrimination

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

TCC02 changes the earlier conclusion in one important respect: Coffee's
supported and unsupported descriptions no longer separate perfectly. Morning
greetings still separates on these records. Neither result establishes a
membership rule for complete notes, because only selected descriptions from
each note were scored.

## Controlled question

TCC01's individual-category scores separated its supported and unsupported
examples despite many errors at the native 0.5 cutoff. TCC02 tests whether that
ordering holds on other records, without changing the model or label wording.

The 25 records come from 20 notes outside TCC01's 14 notes. Two descriptions
are identical, so there are 24 distinct subject strings. Other strings can
still express the same meaning. The complete originals,
source masks and existing subject descriptions are preserved in
`./TCC02/inputs.json`. The main agent and an independent reviewer
read that evidence before scores existed; the assistant judgments and open
scope boundaries are frozen in `./TCC02/judgments.json`.
They are not user approvals or a random sample of the corpus.

Each request supplies one unchanged subject description and one category:
`coffee` or `morning greetings`. The model does not see the full original,
the source fragments, another description, or another category. Its scores
are independent sigmoids from the native classifier, not cosine similarities
or calibrated probabilities of semantic correctness. The release's native
training and task-fit audit remains in [TCC01](./NATIVE-CATEGORY-MEMBERSHIP.md);
no new technique is introduced here.[^1]

## Complete result

| Category | Lowest supported score | Highest unsupported score | Unsupported–supported pairs in the wrong order |
| --- | ---: | ---: | ---: |
| Coffee | 0.839482 | 0.946979 | 5 of 143 |
| Morning greetings | 0.999392 | 0.999266 | 0 of 128 |

The ordering counts compare every judged supported description with every
judged unsupported one. They are not counts of independent trials. Coffee
still orders 138 of 143 such pairs correctly; five inversions do not make it
generally useless. They do defeat exact separation by one Coffee cutoff on
these tested descriptions.

At the unchanged native 0.5 cutoff, Coffee accepts all 11 supported records,
9 of 13 unsupported records, and its one unjudged record. Morning greetings
accepts all 8 supported records, 14 of 16 unsupported records, and its one
unjudged record. All 50 scores, including rejected values and logits, are in
`./TCC02/run/scores.json`. No cutoff was selected.

## Coffee: every inverted pair

Two supported records occur in these inversions:

**151 · N004 · V035**, description: “A rave taking place at a coffee shop.”
Coffee score: **0.839482**. Complete original with mask:

> Weird #coffeechain today
> ⟦Rave at a coffee shop⟧ lol https://video.nostr.build/252e03e0d852e21d29e875ca7e1f381ad5559b8eee53b4a683babcb688b946ed.mp4

**62 · N036 · V281**, description: “Iced coffee.”
Coffee score: **0.936674**. Complete original with mask:

> ⟦Iced coffee⟧, served in ice
>
> 📹 wolf.0313
>
> https://t.co/58sduGh4ME https://video.twimg.com/amplify_video/1807714912455872512/vid/avc1/720x1280/TRtP3N_40gd9jFGv.mp4?tag=14

These unsupported greeting descriptions outrank them:

| Greeting record | Description supplied to the model | Coffee score | Supported record below it |
| --- | --- | ---: | --- |
| 255 · N095 · V861 | The author wishes the world a good morning. | 0.877604 | 151 |
| 619 · N071 · V647 | A good-morning greeting to friends. | 0.904886 | 151 |
| 71 · N092 · V824 | Wishing the Nostr community a good morning. | 0.946979 | 151 and 62 |
| 361 · N099 · V914 | A good-morning greeting. | 0.859700 | 151 |

Complete originals with those masks:

**255 · N095**

> Just had a coffee, but I need another one... ⟦Good morning world⟧, I wish you all a wonderful and blessed Sunday.
>
> #coffeechain #plebchain

**619 · N071**

> ⟦Good morning frens⟧.
> #Duck egg and #basil #breakfast burrito on a tomato tortilla and of course some good #coffee to go with.
>
> Miss unicorn jealously watching hehe 😜
> #coffeechain #grownostr https://image.nostr.build/804c5dc348d07b0322c87bedbe2284de6900fdd16796c876e0640791a24287d3.jpg

**71 · N092**

> ⟦Good morning nostr⟧, its gonna be a great day. I got up early and put the roast and veggies in the crockpot, so i  wont need to worry about lunch later.  I think i want to go to Home Depot and find some safety grab bars for the bathroom in the cabin.  We get quite a few bnb guests that are older, and i always worry about someone falling, so i think it will be worth installing them.
>
> I havent checked the chicks this morning, after moving them to a tractor inside the main run.  Hopefully they are ok. Anyway, yall have a great Saturday nostr friends, and remember that today is a gift. #coffeechain #grownostr #homesteading #bnbstr https://i.nostr.build/zgYxLu3ooskKaAzE.jpg

**361 · N099**

> ⟦GM⟧ happy pizza day to those who observe

The masks and descriptions support greetings, not Coffee. N095 and N071
nevertheless contain explicit coffee content elsewhere; returning those notes
under Coffee is legitimate through their other masks. N092 has Coffeechain
outside this mask, making full-note category scope debatable. N099's other
saved masks concern Pizza Day: it provides a clear extra note on the tested
scores. A cutoff retaining the rave's tested score also retains this greeting.

That last statement is deliberately limited. N004 has other, unscored subject
descriptions. One might recover the rave note above a higher cutoff. This
experiment does not prove impossibility after pooling every available mask.

## Morning greetings: the strongest competing description

The highest unsupported record is **274 · N058 · V495**:

> The author is glad to have hot coffee this morning.

Morning greetings score: **0.999266**. Complete original with mask:

> GM Nostr!
>
> Happy Sunday!
>
> Woke up to 35 degress today---brrr. It'll warm up, but fall is definitely here.
>
> ⟦Glad⟧ the ⟦coffee⟧ is ⟦hot⟧ this ⟦AM⟧!
>
> #coffeechain

This description does not greet anyone. The original does, through its separate
GM mask, and that description scores **0.999467**. The weakest supported
greeting is **913 · N064 · V541**, at **0.999392**:

> A good-morning greeting expressing warmth, affection, and a hug to the audience.

Complete original with mask:

> ⟦GM⟧! ⟦💜⟧⟦🫂⟧ How are you today?
> It's now after Christmas, things are slowly getting back to normal and I'm starting to slow down. In the kitchen as always a lot of work but I like it 😂😂
> From all this I even forgot to take photos 🙈Today meat dumplings, so out of sentiment....
> #food #foodstr #plebchain https://image.nostr.build/3fb21ce7646872c6b17a873a3849f902dca94e24079fdcb5d99db096a3056653.jpg https://image.nostr.build/d63ddf6c600431c95faa2ce795c99d7653afa1c300d2f0a1a5cb922a1b2ed60d.jpg

Thus the ordering remains correct despite almost saturated sigmoids. The small
sigmoid gap is not evidence of numerical instability: the replay is exact.
Nor is finding a separating interval the same as fitting and independently
validating a decision procedure.

## Consequences for notes

At 0.5, Coffee returns 16 notes from the evaluated records. Four wrong
greeting witnesses belong to notes with separately tested coffee witnesses.
N089 (bread preparation) and N099 (Pizza Day) are clear extra notes. N005 and
N092 are hashtag-only scope boundaries; N034 is caffeine-only and remains
unjudged. None is relabeled after scores to manufacture a pass or fail.

Morning greetings returns 18 notes. Four wrong witnesses belong to notes with
separately tested valid greetings. Seven additional notes have no greeting
in their readable text. N018 greets in the afternoon; N052's “Rise
and grind coffee beans” can function as morning encouragement. The subsequent
pre-score TCC03 audit also identifies N045's “Dear America” as a conventional
salutation outside its saved masks. These three full-note scope boundaries
remain unresolved. This refinement of note consequences does not change any
frozen TCC02 witness judgment: the supplied grinding and coffee descriptions
do not themselves express greetings.

The audit (`./TCC02/audit.json`) enumerates these cases. This is a consequence
audit of the tested records, not an exhaustive classification of every subject
in their notes or a corpus-wide quality estimate.

## Decision and remaining construction question

Single-category scoring removes the competing-label problem, but does not
guarantee exact grounded witness ordering. Keep it as potentially useful,
imperfect evidence; do not declare the whole model or architecture invalid.
Morning greetings' separation remains worth investigating without tuning to
this challenge set.

Before another threshold or model experiment, check the architectural step
that maps several subject witnesses back to one note. The intended rule is
that any genuinely supporting mask can place the note in a category. Score
all existing descriptions for these same notes, leave the model and categories
unchanged, and examine which additional witness determines each note's score.
That can reveal both recovery and amplification of false associations. It is
a pooling diagnostic, not an unseen validation sample.

Category generation and semantic parent–child construction remain unproven.
Neither perfect witness ordering nor successful note pooling would establish
them. No hierarchy, browser, extraction prompt, source mask or GDC09 baseline
was changed.

## Verification

The single-condition runner test first failed because the option did not
exist. It now passes with all 72 selected regressions. The original TCC01
default run retains byte-identical scores and token inputs. TCC02's offline
replay retains byte-identical scores, inputs and runner, with matching
model/source hashes, native checks and package versions. Pre-score plan,
input and judgment hashes are preserved in the audit.

One CPU process, two Torch threads, 50 primary scores: 1.69 seconds inference
and about 4.9 GiB peak RSS. No paid resource, frontier generation or new model
download. The exact runtime and native source are recorded in
`./TCC02/run/config.json`.

Run from the repository root, using a new output directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib \
/tmp/oracle-gliclass-probe-venv/bin/python sse_multivector/native_category_probe.py \
  --input sse_multivector/navigation-research-v1/TCC02/inputs.json \
  --labels coffee 'morning greetings' --conditions single \
  --source /tmp/navigation-gliclass-v3-source-20260912 \
  --cache /tmp/oracle-gliclass-probe-cache --offline \
  --output /tmp/tcc02-another-replay
```

## Sources

[^1]: Stepanov et al., [GLiClass: Generalist Lightweight Model for Sequence Classification Tasks](https://arxiv.org/html/2508.07662v1), 2025, §§2–3; [pinned native source](https://github.com/Knowledgator/GLiClass/tree/5d96d8a5d099a10f00d90a2493e5f93a3ddbd2ae). Native label/text input and independent classification scores; no claim of calibrated arbitrary-category membership or hierarchy construction.
