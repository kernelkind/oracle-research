# Candidate atomic-subject mask audit

This document contains the 53 existing SSE inputs that might be reused in the
fine-segmentation experiments. It does **not** claim that any mask is a correct
atomic subject.

For each item, the complete text given to SSE is shown. Only the text inside
`⟦...⟧` was selected and averaged into the resulting vector. Everything outside
the brackets was unselected context.

Review each item by its ID and decide whether the selected text expresses one
correct atomic subject. The section headings record how the old experiments
organized the inputs; they are not new judgments about the correct grouping.

## Python data visualization family

### Complete-subject candidates

- **A01** — This post discusses ⟦Python data visualization⟧.
- **A02** — This post discusses ⟦charting data with Python⟧.
- **A03** — This post discusses ⟦creating graphs using Python⟧.
- **A04** — This post discusses ⟦visualizing data with Python⟧.
- **A05** — This post discusses ⟦plotting datasets in Python⟧.

### Python-related controls

- **A06** — This post discusses ⟦Python web API development⟧.
- **A07** — This post discusses ⟦automated testing with Python⟧.
- **A08** — This post discusses ⟦Python command-line applications⟧.
- **A09** — This post discusses ⟦processing text with Python⟧.
- **A10** — This post discusses ⟦Python database programming⟧.

### Data-visualization-related controls

- **A11** — This post discusses ⟦data visualization with R⟧.
- **A12** — This post discusses ⟦charting data in Julia⟧.
- **A13** — This post discusses ⟦creating graphs with Tableau⟧.
- **A14** — This post discusses ⟦plotting datasets in MATLAB⟧.
- **A15** — This post discusses ⟦visualizing data with JavaScript⟧.

## Beach volleyball family

### Complete-subject candidates

- **B01** — This post discusses ⟦beach volleyball⟧.
- **B02** — This post discusses ⟦volleyball played on sand at the beach⟧.
- **B03** — This post discusses ⟦seaside games of volleyball⟧.
- **B04** — This post discusses ⟦competitive beach volleyball⟧.
- **B05** — This post discusses ⟦playing volleyball on a sandy beach⟧.

### Beach-related controls

- **B06** — This post discusses ⟦cleaning litter from a beach⟧.
- **B07** — This post discusses ⟦relaxing on a sandy beach⟧.
- **B08** — This post discusses ⟦coastal erosion at beaches⟧.
- **B09** — This post discusses ⟦seaside vacations⟧.
- **B10** — This post discusses ⟦nature walks along a beach⟧.

### Volleyball-related controls

- **B11** — This post discusses ⟦indoor volleyball⟧.
- **B12** — This post discusses ⟦volleyball serving drills in a gym⟧.
- **B13** — This post discusses ⟦professional court volleyball⟧.
- **B14** — This post discusses ⟦coaching an indoor volleyball team⟧.
- **B15** — This post discusses ⟦setting up a gym volleyball net⟧.

## Solar-powered greenhouse family

### Complete-subject candidates

- **C01** — This post discusses ⟦solar-powered greenhouses⟧.
- **C02** — This post discusses ⟦greenhouses powered by photovoltaic panels⟧.
- **C03** — This post discusses ⟦solar electricity for greenhouse operations⟧.
- **C04** — This post discusses ⟦off-grid greenhouses running on solar energy⟧.
- **C05** — This post discusses ⟦using solar panels to operate a glasshouse⟧.

### Solar-power-related controls

- **C06** — This post discusses ⟦solar-powered houses⟧.
- **C07** — This post discusses ⟦photovoltaic electricity for residences⟧.
- **C08** — This post discusses ⟦rooftop solar charging home batteries⟧.
- **C09** — This post discusses ⟦solar panels running office equipment⟧.
- **C10** — This post discusses ⟦residential solar-energy systems⟧.

### Greenhouse-related controls

- **C11** — This post discusses ⟦greenhouse tomato cultivation⟧.
- **C12** — This post discusses ⟦ventilating a greenhouse⟧.
- **C13** — This post discusses ⟦natural-gas heating for greenhouses⟧.
- **C14** — This post discusses ⟦greenhouse irrigation systems⟧.
- **C15** — This post discusses ⟦gardening inside a glasshouse⟧.

## Location masks under changing context

### Beach-location candidates

**N01**

> I spent the afternoon debugging a Rust borrow-checker error while drinking a
> martini ⟦on a quiet beach⟧.

**N02**

> I spent the afternoon debugging a Rust borrow-checker error while drinking a
> martini ⟦beside a calm shoreline⟧.

**N03**

> I spent the afternoon painting a watercolor while drinking lemonade ⟦on a
> quiet beach⟧.

**N04**

> I spent the afternoon painting a watercolor while drinking lemonade ⟦beside a
> calm shoreline⟧.

### Office-location candidates

**N05**

> I spent the afternoon debugging a Rust borrow-checker error while drinking a
> martini ⟦in a windowless office⟧.

**N06**

> I spent the afternoon debugging a Rust borrow-checker error while drinking a
> martini ⟦inside an office without windows⟧.

**N07**

> I spent the afternoon painting a watercolor while drinking lemonade ⟦in a
> windowless office⟧.

**N08**

> I spent the afternoon painting a watercolor while drinking lemonade ⟦inside
> an office without windows⟧.

## Provenance

- **A01–C15:**
  `sse_multivector/mask-fidelity-compound-subject-neighborhood-v1/worker-input.json`
- **N01–N08:**
  `sse_multivector/mask-fidelity-location-v1/worker-input.json`

The source artifacts remain unchanged.
