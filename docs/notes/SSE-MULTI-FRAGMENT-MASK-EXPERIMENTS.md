# Multi-fragment mask experiments

These experiments test the following requirements:

1. Changing the wording, number, boundaries, or redundancy of mask fragments must not materially change the vector when the intended atomic subject remains the same.
2. Changing only text outside the mask should affect the vector less than changing the atomic subject.
3. When changing a fragment changes the human-defined atomic subject, the resulting vector should also become distinguishable from the original vector.

Every control, changed input, and pass condition was frozen before SSE ran. The complete note was given to SSE, but only the text inside `⟦...⟧` was pooled into each vector.

## 2.1) Changing the fragment count without changing the selected words

### Experiment 2.1.1: Dividing dog playing fetch into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦dog playing fetch⟧.

**Changed — two fragments**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

---

### Experiment 2.1.2: Dividing child painting a picture into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦child painting a picture⟧.

**Changed — two fragments**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

---

### Experiment 2.1.3: Dividing car being washed by hand into two fragments

**Description:** The complete note and selected words remain identical. The control mask contains one fragment. The changed mask divides those same words into two fragments.

**Hypothesis:** Both masks will select the same token indices and produce byte-identical vectors.

**Control — one fragment**
> This entry is about the ⟦car being washed by hand⟧.

**Changed — two fragments**
> This entry is about the ⟦car⟧ ⟦being washed by hand⟧.

**Result:** The selected token indices and raw vector bytes were exactly equal. Cosine was `1.000000`.

## 2.2) Changing fragment boundaries without changing the atomic subject

### Experiment 2.2.1: Dog activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `dog` and the activity. The changed masks add only the adjacent determiner, preposition, or terminal punctuation. Dog sleeping indoors is the matched atomic-subject change for dog playing fetch, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Dog playing fetch**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.
>
> This entry is about ⟦the dog⟧ ⟦playing fetch⟧.
>
> This entry is ⟦about the dog⟧ ⟦playing fetch⟧.
>
> This entry is ⟦about the dog⟧ ⟦playing fetch.⟧

**Dog sleeping indoors**
> This entry is about the ⟦dog⟧ ⟦sleeping indoors⟧.
>
> This entry is about ⟦the dog⟧ ⟦sleeping indoors⟧.
>
> This entry is ⟦about the dog⟧ ⟦sleeping indoors⟧.
>
> This entry is ⟦about the dog⟧ ⟦sleeping indoors.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.988242–0.998627`; changed-subject cosines were `0.224933–0.281705`. The smallest margin was `+0.711649`.

---

### Experiment 2.2.2: Child activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `child` and the activity. The changed masks add only the adjacent determiner, preposition, or terminal punctuation. Child reading a book is the matched atomic-subject change for child painting a picture, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Child painting a picture**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.
>
> This entry is about ⟦the child⟧ ⟦painting a picture⟧.
>
> This entry is ⟦about the child⟧ ⟦painting a picture⟧.
>
> This entry is ⟦about the child⟧ ⟦painting a picture.⟧

**Child reading a book**
> This entry is about the ⟦child⟧ ⟦reading a book⟧.
>
> This entry is about ⟦the child⟧ ⟦reading a book⟧.
>
> This entry is ⟦about the child⟧ ⟦reading a book⟧.
>
> This entry is ⟦about the child⟧ ⟦reading a book.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.991441–0.999379`; changed-subject cosines were `0.441327–0.468807`. The smallest margin was `+0.529465`.

---

### Experiment 2.2.3: Car activity boundaries

**Description:** Each complete note remains fixed. The control masks contain `car` and the activity. The changed masks add only the adjacent determiner, preposition, auxiliary verb, or terminal punctuation. Car repair is the matched atomic-subject change for washing a car by hand, and vice versa.

**Hypothesis:** For every mask, each of the other three boundary variants of the same atomic subject will have a higher cosine than the matched different activity using that boundary. All 24 comparisons must pass.

**Car being washed by hand**
> This entry is about the ⟦car⟧ being ⟦washed by hand⟧.
>
> This entry is about ⟦the car⟧ being ⟦washed by hand⟧.
>
> This entry is ⟦about the car⟧ ⟦being washed by hand⟧.
>
> This entry is ⟦about the car⟧ ⟦being washed by hand.⟧

**Car being repaired in a garage**
> This entry is about the ⟦car⟧ being ⟦repaired in a garage⟧.
>
> This entry is about ⟦the car⟧ being ⟦repaired in a garage⟧.
>
> This entry is ⟦about the car⟧ ⟦being repaired in a garage⟧.
>
> This entry is ⟦about the car⟧ ⟦being repaired in a garage.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.991952–0.999328`; changed-subject cosines were `0.368443–0.428111`. The smallest margin was `+0.571172`.

## 2.3) Changing fragment wording and atomic subject

### Experiment 2.3.1: Dog playing fetch

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves dog playing fetch or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦dog⟧ ⟦playing fetch⟧.

**First fragment — same subject**
> This entry is about the ⟦canine⟧ ⟦playing fetch⟧.

**First fragment — changed subject**
> This entry is about the ⟦child⟧ ⟦playing fetch⟧.

**Second fragment — same subject**
> This entry is about the ⟦dog⟧ ⟦retrieving a thrown ball⟧.

**Second fragment — changed subject**
> This entry is about the ⟦dog⟧ ⟦sleeping indoors⟧.

**Both fragments — same subject**
> This entry is about the ⟦canine⟧ ⟦retrieving a thrown ball⟧.

**Both fragments — changed subject**
> This entry is about the ⟦child⟧ ⟦sleeping indoors⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.983086` | `0.774015` | `+0.209072` |
| Second fragment | `0.761176` | `0.211456` | `+0.549720` |
| Both fragments | `0.752066` | `0.004272` | `+0.747794` |

**Result:** All three comparisons passed.

---

### Experiment 2.3.2: Child painting a picture

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves child painting a picture or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦child⟧ ⟦painting a picture⟧.

**First fragment — same subject**
> This entry is about the ⟦kid⟧ ⟦painting a picture⟧.

**First fragment — changed subject**
> This entry is about the ⟦robot⟧ ⟦painting a picture⟧.

**Second fragment — same subject**
> This entry is about the ⟦child⟧ ⟦making a painting⟧.

**Second fragment — changed subject**
> This entry is about the ⟦child⟧ ⟦reading a book⟧.

**Both fragments — same subject**
> This entry is about the ⟦kid⟧ ⟦making a painting⟧.

**Both fragments — changed subject**
> This entry is about the ⟦robot⟧ ⟦reading a book⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.990198` | `0.600571` | `+0.389627` |
| Second fragment | `0.960052` | `0.439388` | `+0.520664` |
| Both fragments | `0.951676` | `0.117733` | `+0.833943` |

**Result:** All three comparisons passed.

---

### Experiment 2.3.3: Car being washed by hand

**Description:** The original vector is the control. The first fragment, second fragment, or both are changed either to a paraphrase that preserves a car being washed by hand or to wording that changes the atomic subject.

**Hypothesis:** For each position, the meaning-preserving version will have a higher cosine to the original than the subject-changing version.

**Original**
> This entry is about the ⟦car⟧ being ⟦washed by hand⟧.

**First fragment — same subject**
> This entry is about the ⟦automobile⟧ being ⟦washed by hand⟧.

**First fragment — changed subject**
> This entry is about the ⟦bicycle⟧ being ⟦washed by hand⟧.

**Second fragment — same subject**
> This entry is about the ⟦car⟧ being ⟦cleaned manually⟧.

**Second fragment — changed subject**
> This entry is about the ⟦car⟧ being ⟦repaired in a garage⟧.

**Both fragments — same subject**
> This entry is about the ⟦automobile⟧ being ⟦cleaned manually⟧.

**Both fragments — changed subject**
> This entry is about the ⟦bicycle⟧ being ⟦repaired in a garage⟧.

| Change | Same subject | Changed subject | Margin |
|---|---:|---:|---:|
| First fragment | `0.997523` | `0.892023` | `+0.105500` |
| Second fragment | `0.883891` | `0.361299` | `+0.522592` |
| Both fragments | `0.887655` | `0.316613` | `+0.571042` |

**Result:** All three comparisons passed. The first-fragment comparison was the weakest wording result, but it still favored the unchanged atomic subject by `+0.105500`.

## 2.4) Adding redundant or unrelated meaning to the mask

### Experiment 2.4.1: Redundant dog-fetch meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for dog playing fetch. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant dog-fetch fragment will affect the vector less than adding the unrelated child-painting fragment.

**Control**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described a canine retrieving a thrown ball. A child painted a picture nearby.

**Added redundant meaning**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described ⟦a canine retrieving a thrown ball⟧. A child painted a picture nearby.

**Added unrelated meaning**
> The ⟦dog⟧ ⟦played fetch⟧ in the yard. Later, the note described a canine retrieving a thrown ball. ⟦A child painted a picture⟧ nearby.

**Result:** Control-to-redundant cosine was `0.892011`; control-to-unrelated cosine was `0.330721`. The hypothesis passed by `+0.561290`.

---

### Experiment 2.4.2: Redundant child-painting meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for a child painting a picture. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant child-painting fragment will affect the vector less than adding the unrelated dog-sleeping fragment.

**Control**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described a kid making a painting. A dog slept indoors nearby.

**Added redundant meaning**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described ⟦a kid making a painting⟧. A dog slept indoors nearby.

**Added unrelated meaning**
> The ⟦child⟧ ⟦painted a picture⟧ after lunch. Later, the note described a kid making a painting. ⟦A dog slept indoors⟧ nearby.

**Result:** Control-to-redundant cosine was `0.967705`; control-to-unrelated cosine was `0.445399`. The hypothesis passed by `+0.522306`.

---

### Experiment 2.4.3: Redundant hand-washed-car meaning

**Description:** The complete note remains fixed. The control mask contains two fragments for a car being washed by hand. One changed mask adds a third fragment that repeats the same meaning. The other adds an unrelated fragment from the same note.

**Hypothesis:** Adding the redundant hand-washed-car fragment will affect the vector less than adding the unrelated bicycle-repair fragment.

**Control**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described an automobile being cleaned manually. A bicycle needed a new tire nearby.

**Added redundant meaning**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described ⟦an automobile being cleaned manually⟧. A bicycle needed a new tire nearby.

**Added unrelated meaning**
> The ⟦car⟧ was ⟦washed by hand⟧ in the driveway. Later, the note described an automobile being cleaned manually. ⟦A bicycle needed a new tire⟧ nearby.

**Result:** Control-to-redundant cosine was `0.967867`; control-to-unrelated cosine was `0.623034`. The hypothesis passed by `+0.344833`.

## 2.5) Changing only text outside the mask

### Experiment 2.5.1: Dog activities under different surrounding text

**Description:** The mask remains exactly `dog` plus the activity while the neutral text outside the mask changes. Dog playing fetch and dog sleeping indoors provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Dog playing fetch**
> The first note about the ⟦dog⟧ ⟦playing fetch⟧ was filed yesterday.
>
> An archived memo about the ⟦dog⟧ ⟦playing fetch⟧ was reviewed today.
>
> This short report about the ⟦dog⟧ ⟦playing fetch⟧ was copied twice.

**Dog sleeping indoors**
> The first note about the ⟦dog⟧ ⟦sleeping indoors⟧ was filed yesterday.
>
> An archived memo about the ⟦dog⟧ ⟦sleeping indoors⟧ was reviewed today.
>
> This short report about the ⟦dog⟧ ⟦sleeping indoors⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.995244–0.998576`; changed-subject cosines were `0.250671–0.285189`. The smallest margin was `+0.712164`.

---

### Experiment 2.5.2: Child activities under different surrounding text

**Description:** The mask remains exactly `child` plus the activity while the neutral text outside the mask changes. Painting a picture and reading a book provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Child painting a picture**
> The first note about the ⟦child⟧ ⟦painting a picture⟧ was filed yesterday.
>
> An archived memo about the ⟦child⟧ ⟦painting a picture⟧ was reviewed today.
>
> This short report about the ⟦child⟧ ⟦painting a picture⟧ was copied twice.

**Child reading a book**
> The first note about the ⟦child⟧ ⟦reading a book⟧ was filed yesterday.
>
> An archived memo about the ⟦child⟧ ⟦reading a book⟧ was reviewed today.
>
> This short report about the ⟦child⟧ ⟦reading a book⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.992030–0.997193`; changed-subject cosines were `0.375291–0.414937`. The smallest margin was `+0.581214`.

---

### Experiment 2.5.3: Car activities under different surrounding text

**Description:** The mask remains exactly `car` plus the activity while the neutral text outside the mask changes. Washing a car by hand and repairing it in a garage provide matched atomic-subject controls in all three surrounding texts.

**Hypothesis:** Changing only text outside the mask will affect each vector less than replacing its activity. All 12 comparisons must pass.

**Car being washed by hand**
> The first note about the ⟦car⟧ being ⟦washed by hand⟧ was filed yesterday.
>
> An archived memo about the ⟦car⟧ being ⟦washed by hand⟧ was reviewed today.
>
> This short report about the ⟦car⟧ being ⟦washed by hand⟧ was copied twice.

**Car being repaired in a garage**
> The first note about the ⟦car⟧ being ⟦repaired in a garage⟧ was filed yesterday.
>
> An archived memo about the ⟦car⟧ being ⟦repaired in a garage⟧ was reviewed today.
>
> This short report about the ⟦car⟧ being ⟦repaired in a garage⟧ was copied twice.

**Result:** All 12 comparisons passed. Same-subject cosines were `0.993667–0.997870`; changed-subject cosines were `0.386410–0.404772`. The smallest margin was `+0.589299`.

## Combined result

| Requirement-focused test | Result |
|---|---:|
| Same selected words divided into one or two fragments | 3/3 exact |
| Changed fragment boundaries, same atomic subject | 72/72 |
| Paraphrased fragments versus subject-changing fragments | 9/9 |
| Added redundant meaning versus unrelated meaning | 3/3 |
| Changed text outside the mask versus changed atomic subject | 36/36 |

All five tests passed every predeclared comparison.

> For these controlled synthetic examples, multi-fragment masks preserved the intended atomic subject under changes to fragment count, boundaries, wording, redundancy, and surrounding text, while remaining sensitive to changes in the atomic subject.

This establishes the required behavior only for these common synthetic examples. It does not establish the same behavior for real Nostr language, automatically generated masks, fine segmentation, or hierarchy construction.

The frozen inputs, every unrounded comparison, and the complete cosine matrix are in `sse_multivector/mask-fidelity-multifragment-requirements-v1/`.
