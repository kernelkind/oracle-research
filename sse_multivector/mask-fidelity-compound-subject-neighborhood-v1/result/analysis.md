# Compound-subject neighborhood fidelity

## Question

Under controlled context, do paraphrases of one recognizable compound subject
form a local cosine neighborhood distinct from phrases retaining only one
component?

Every input had the same form:

> This post discusses ⟦subject phrase⟧.

Only the phrase inside `⟦...⟧` was pooled into the SSE vector. Each family had
five compound-subject paraphrases, five controls retaining its first component,
and five controls retaining its second component.

For each compound anchor, the other fourteen phrases in its family were ranked
by cosine. The frozen rules were:

1. At least three of the nearest four must be compound-subject peers, for all
   five anchors in a family.
2. The mean per-anchor AUC must be at least `0.90`. AUC compares each of an
   anchor's four compound peers against each of its ten component-only controls.
3. Every family must pass both rules for the overall pilot to be supportive.

## Result

**The overall strict criterion did not pass. Two of three families passed.**

| Family | Anchors passing top-four rule | Macro-AUC | Family result |
|---|---:|---:|---|
| Python data visualization | 5/5 | `1.000` | Pass |
| Beach volleyball | 5/5 | `1.000` | Pass |
| Solar-powered greenhouses | 4/5 | `0.930` | Fail |

The first two compound subjects formed perfect local neighborhoods under both
metrics. The solar-greenhouse family remained strongly structured overall, but
one paraphrase had only two compound peers among its nearest four.

In the rankings below:

- **Compound** means another formulation of the complete subject.
- **First only** and **second only** mean a control retaining just one of the
  subject's two components.

## Python data visualization

### Complete input set

**Compound**

- A01 — This post discusses ⟦Python data visualization⟧.
- A02 — This post discusses ⟦charting data with Python⟧.
- A03 — This post discusses ⟦creating graphs using Python⟧.
- A04 — This post discusses ⟦visualizing data with Python⟧.
- A05 — This post discusses ⟦plotting datasets in Python⟧.

**Python only**

- A06 — This post discusses ⟦Python web API development⟧.
- A07 — This post discusses ⟦automated testing with Python⟧.
- A08 — This post discusses ⟦Python command-line applications⟧.
- A09 — This post discusses ⟦processing text with Python⟧.
- A10 — This post discusses ⟦Python database programming⟧.

**Data visualization only**

- A11 — This post discusses ⟦data visualization with R⟧.
- A12 — This post discusses ⟦charting data in Julia⟧.
- A13 — This post discusses ⟦creating graphs with Tableau⟧.
- A14 — This post discusses ⟦plotting datasets in MATLAB⟧.
- A15 — This post discusses ⟦visualizing data with JavaScript⟧.

### Four nearest neighbors of every compound anchor

| Anchor | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Result |
|---|---|---|---|---|---|
| A01 | A04 Compound `0.946528` | A05 Compound `0.934991` | A03 Compound `0.919118` | A02 Compound `0.913525` | 4/4 · Pass |
| A02 | A05 Compound `0.948067` | A03 Compound `0.945724` | A04 Compound `0.916706` | A01 Compound `0.913525` | 4/4 · Pass |
| A03 | A05 Compound `0.948823` | A02 Compound `0.945724` | A04 Compound `0.928570` | A01 Compound `0.919118` | 4/4 · Pass |
| A04 | A05 Compound `0.950421` | A01 Compound `0.946528` | A03 Compound `0.928570` | A02 Compound `0.916706` | 4/4 · Pass |
| A05 | A04 Compound `0.950421` | A03 Compound `0.948823` | A02 Compound `0.948067` | A01 Compound `0.934991` | 4/4 · Pass |

Every compound paraphrase ranked all four compound peers above all ten
component-only controls. Each anchor AUC was `1.000`.

## Beach volleyball

### Complete input set

**Compound**

- B01 — This post discusses ⟦beach volleyball⟧.
- B02 — This post discusses ⟦volleyball played on sand at the beach⟧.
- B03 — This post discusses ⟦seaside games of volleyball⟧.
- B04 — This post discusses ⟦competitive beach volleyball⟧.
- B05 — This post discusses ⟦playing volleyball on a sandy beach⟧.

**Beach only**

- B06 — This post discusses ⟦cleaning litter from a beach⟧.
- B07 — This post discusses ⟦relaxing on a sandy beach⟧.
- B08 — This post discusses ⟦coastal erosion at beaches⟧.
- B09 — This post discusses ⟦seaside vacations⟧.
- B10 — This post discusses ⟦nature walks along a beach⟧.

**Volleyball only**

- B11 — This post discusses ⟦indoor volleyball⟧.
- B12 — This post discusses ⟦volleyball serving drills in a gym⟧.
- B13 — This post discusses ⟦professional court volleyball⟧.
- B14 — This post discusses ⟦coaching an indoor volleyball team⟧.
- B15 — This post discusses ⟦setting up a gym volleyball net⟧.

### Four nearest neighbors of every compound anchor

| Anchor | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Result |
|---|---|---|---|---|---|
| B01 | B04 Compound `0.945336` | B03 Compound `0.941899` | B02 Compound `0.905852` | B05 Compound `0.884337` | 4/4 · Pass |
| B02 | B05 Compound `0.962960` | B01 Compound `0.905852` | B03 Compound `0.891786` | B04 Compound `0.858895` | 4/4 · Pass |
| B03 | B01 Compound `0.941899` | B04 Compound `0.941457` | B02 Compound `0.891786` | B05 Compound `0.860846` | 4/4 · Pass |
| B04 | B01 Compound `0.945336` | B03 Compound `0.941457` | B02 Compound `0.858895` | B05 Compound `0.845241` | 4/4 · Pass |
| B05 | B02 Compound `0.962960` | B01 Compound `0.884337` | B03 Compound `0.860846` | B04 Compound `0.845241` | 4/4 · Pass |

Again, every compound paraphrase ranked all four compound peers above all ten
component-only controls. Each anchor AUC was `1.000`.

## Solar-powered greenhouses

### Complete input set

**Compound**

- C01 — This post discusses ⟦solar-powered greenhouses⟧.
- C02 — This post discusses ⟦greenhouses powered by photovoltaic panels⟧.
- C03 — This post discusses ⟦solar electricity for greenhouse operations⟧.
- C04 — This post discusses ⟦off-grid greenhouses running on solar energy⟧.
- C05 — This post discusses ⟦using solar panels to operate a glasshouse⟧.

**Solar power only**

- C06 — This post discusses ⟦solar-powered houses⟧.
- C07 — This post discusses ⟦photovoltaic electricity for residences⟧.
- C08 — This post discusses ⟦rooftop solar charging home batteries⟧.
- C09 — This post discusses ⟦solar panels running office equipment⟧.
- C10 — This post discusses ⟦residential solar-energy systems⟧.

**Greenhouses only**

- C11 — This post discusses ⟦greenhouse tomato cultivation⟧.
- C12 — This post discusses ⟦ventilating a greenhouse⟧.
- C13 — This post discusses ⟦natural-gas heating for greenhouses⟧.
- C14 — This post discusses ⟦greenhouse irrigation systems⟧.
- C15 — This post discusses ⟦gardening inside a glasshouse⟧.

### Four nearest neighbors of every compound anchor

| Anchor | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Result |
|---|---|---|---|---|---|
| C01 | C03 Compound `0.961149` | C04 Compound `0.948807` | C02 Compound `0.932255` | C10 Solar only `0.819817` | 3/4 · Pass |
| C02 | C01 Compound `0.932255` | C04 Compound `0.923339` | C03 Compound `0.904428` | C10 Solar only `0.809207` | 3/4 · Pass |
| C03 | C01 Compound `0.961149` | C04 Compound `0.943004` | C02 Compound `0.904428` | C10 Solar only `0.799754` | 3/4 · Pass |
| C04 | C01 Compound `0.948807` | C03 Compound `0.943004` | C02 Compound `0.923339` | C10 Solar only `0.870823` | 3/4 · Pass |
| C05 | C01 Compound `0.816256` | C10 Solar only `0.815843` | C06 Solar only `0.815705` | C04 Compound `0.790014` | 2/4 · Fail |

Per-anchor AUCs were:

| Anchor | AUC |
|---|---:|
| C01 | `0.975` |
| C02 | `0.950` |
| C03 | `0.925` |
| C04 | `0.950` |
| C05 | `0.850` |

The family macro-AUC was `0.930`, which passed its `0.90` rule. The family
failed only because C05 had two compound peers, rather than the required three,
among its nearest four.

C05's first three similarities were almost tied:

- C01, complete subject: `0.816256`
- C10, solar component only: `0.815843`
- C06, solar component only: `0.815705`

The frozen top-four rule still counts their order exactly. The small gaps are
important context for understanding the failure, but they do not change it.

## Supported conclusion

This controlled pilot gives strong positive evidence that SSE plus cosine can
form local neighborhoods for some recognizable compound subjects. It does not
show that this behavior is reliable across the tested subjects: one of the
three families failed its predeclared local-neighborhood rule.

The failure is narrow. The solar-greenhouse family still had a `0.930`
macro-AUC, and four anchors passed. We have not isolated why the C05 wording was
less stable, so the run does not distinguish among encoder geometry, phrasing,
or this particular subject family.

The complete rankings are in `analysis.json`. The complete 45-by-45 matrix is
in `cosine-matrix.csv`. The raw vectors and worker receipt are retained beside
this report.
