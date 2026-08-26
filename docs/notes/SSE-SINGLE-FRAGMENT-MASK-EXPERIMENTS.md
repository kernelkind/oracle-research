# Single-fragment mask experiments

## 1.1) Same mask, different surrounding context

### Experiment 1.1.1: N01 vs N03

**Description:** N01 is the control. N03 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `on a quiet beach`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Changed context — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Result:** Cosine `0.982316`. The hypothesis was supported for this comparison.

---

### Experiment 1.1.2: N02 vs N04

**Description:** N02 is the control. N04 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `beside a calm shoreline`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Changed context — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.984553`. The hypothesis was supported for this comparison.

---

### Experiment 1.1.3: N05 vs N07

**Description:** N05 is the control. N07 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `in a windowless office`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Changed context — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Result:** Cosine `0.980081`. The hypothesis was supported for this comparison.

---

### Experiment 1.1.4: N06 vs N08

**Description:** N06 is the control. N08 changes only the unselected surrounding context from Rust debugging and a martini to watercolor painting and lemonade. The selected mask remains exactly `inside an office without windows`.
**Hypothesis:** The cosine will be high because the selected mask is identical and the changed surrounding context is unrelated to the selected location.

**Control — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Changed context — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.971089`. The hypothesis was supported for this comparison.

## 1.2) Paraphrased mask, same surrounding context

### Experiment 1.2.1: N01 vs N02

**Description:** N01 is the control. N02 changes only the selected mask from `on a quiet beach` to `beside a calm shoreline`. Both masks describe the same beach location, and the unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Paraphrased mask — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.855579`. The hypothesis was supported for this comparison.

---

### Experiment 1.2.2: N03 vs N04

**Description:** N03 is the control. N04 changes only the selected mask from `on a quiet beach` to `beside a calm shoreline`. Both masks describe the same beach location, and the unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Paraphrased mask — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Result:** Cosine `0.822117`. The hypothesis was supported for this comparison.

---

### Experiment 1.2.3: N05 vs N06

**Description:** N05 is the control. N06 changes only the selected mask from `in a windowless office` to `inside an office without windows`. Both masks describe the same office location, and the unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Paraphrased mask — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Result:** Cosine `0.946553`. The hypothesis was supported for this comparison.

---

### Experiment 1.2.4: N07 vs N08

**Description:** N07 is the control. N08 changes only the selected mask from `in a windowless office` to `inside an office without windows`. Both masks describe the same office location, and the unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be high if SSE recognizes the shared location meaning rather than requiring identical words.

**Control — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Paraphrased mask — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.969186`. The hypothesis was supported for this comparison.

## 1.3) Different mask, same surrounding context

### Experiment 1.3.1: N01 vs N05

**Description:** N01 is the control. N05 changes only the selected mask from the beach location `on a quiet beach` to the office location `in a windowless office`. The unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N01**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦on a quiet beach⟧.

**Different mask — N05**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦in a windowless office⟧.

**Result:** Cosine `0.116487`. The hypothesis was supported for this comparison.

---

### Experiment 1.3.2: N02 vs N06

**Description:** N02 is the control. N06 changes only the selected mask from the beach location `beside a calm shoreline` to the office location `inside an office without windows`. The unselected Rust-and-martini context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N02**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦beside a calm shoreline⟧.

**Different mask — N06**
> I spent the afternoon debugging a Rust borrow-checker error while drinking a martini ⟦inside an office without windows⟧.

**Result:** Cosine `0.086605`. The hypothesis was supported for this comparison.

---

### Experiment 1.3.3: N03 vs N07

**Description:** N03 is the control. N07 changes only the selected mask from the beach location `on a quiet beach` to the office location `in a windowless office`. The unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N03**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a quiet beach⟧.

**Different mask — N07**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a windowless office⟧.

**Result:** Cosine `0.149702`. The hypothesis was supported for this comparison.

---

### Experiment 1.3.4: N04 vs N08

**Description:** N04 is the control. N08 changes only the selected mask from the beach location `beside a calm shoreline` to the office location `inside an office without windows`. The unselected watercolor-and-lemonade context remains identical.
**Hypothesis:** The cosine will be low if SSE follows the materially different selected locations instead of the identical surrounding context.

**Control — N04**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a calm shoreline⟧.

**Different mask — N08**
> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside an office without windows⟧.

**Result:** Cosine `0.081676`. The hypothesis was supported for this comparison.

## Combined Result

- Same masks under different surrounding contexts produced cosine `0.971089–0.984553`.
- Paraphrased masks expressing the same location produced cosine `0.822117–0.969186`.
- Different masked locations under identical surrounding contexts produced cosine `0.081676–0.149702`.

> For explicit narrow masks, SSE can isolate selected meaning without substantial contamination from the rest of the note.

This conclusion is limited to the simple beach-versus-office location distinction tested here.

## 1.4) Same atomic subject under different mask boundaries

### Experiment 1.4.1: Dog and cat mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The dog and cat notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each dog or cat mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Dog note**
> This story is about the ⟦dog⟧.
>
> This story is about ⟦the dog⟧.
>
> This story is ⟦about the dog⟧.
>
> This story is ⟦about the dog.⟧

**Cat note**
> This story is about the ⟦cat⟧.
>
> This story is about ⟦the cat⟧.
>
> This story is ⟦about the cat⟧.
>
> This story is ⟦about the cat.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.931409–0.994477`; matched different-subject cosines were `0.494654–0.625200`. The smallest margin was `+0.364795`.

---

### Experiment 1.4.2: Coffee and tea mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The coffee and tea notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each coffee or tea mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Coffee note**
> This discussion is about the ⟦coffee⟧.
>
> This discussion is about ⟦the coffee⟧.
>
> This discussion is ⟦about the coffee⟧.
>
> This discussion is ⟦about the coffee.⟧

**Tea note**
> This discussion is about the ⟦tea⟧.
>
> This discussion is about ⟦the tea⟧.
>
> This discussion is ⟦about the tea⟧.
>
> This discussion is ⟦about the tea.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.954442–0.997088`; matched different-subject cosines were `0.455609–0.550715`. The smallest margin was `+0.446341`.

---

### Experiment 1.4.3: Bicycle and car mask boundaries

**Description:** Each complete note remains fixed. The control mask contains only the subject noun. The changed masks add the adjacent determiner, preposition, and terminal punctuation without changing the human-defined atomic subject. The bicycle and car notes provide matched different-subject controls with the same sentence form and mask boundaries.

**Hypothesis:** For each bicycle or car mask, all three other boundary variants of the same subject will have a higher cosine than the matched different subject with the same boundary. All 24 comparisons must pass.

**Bicycle note**
> This report is about the ⟦bicycle⟧.
>
> This report is about ⟦the bicycle⟧.
>
> This report is ⟦about the bicycle⟧.
>
> This report is ⟦about the bicycle.⟧

**Car note**
> This report is about the ⟦car⟧.
>
> This report is about ⟦the car⟧.
>
> This report is ⟦about the car⟧.
>
> This report is ⟦about the car.⟧

**Result:** All 24 comparisons passed. Same-subject cosines were `0.931499–0.995233`; matched different-subject cosines were `0.359477–0.479524`. The smallest margin was `+0.492452`.

## Mask-boundary result

All 72 predeclared comparisons passed. The weakest comparison still favored the unchanged subject by `+0.364795` cosine.

> For these three common matched subject pairs, adding a determiner, preposition, or terminal punctuation to a single-fragment mask affected the SSE vector much less than replacing the atomic subject.

This fills the previously untested single-fragment boundary case. It does not establish the same behavior for arbitrary language, real Nostr notes, or masks containing multiple fragments.

The frozen inputs, every unrounded comparison, and the complete cosine matrix are in `sse_multivector/mask-fidelity-single-fragment-boundary-v1/`.
