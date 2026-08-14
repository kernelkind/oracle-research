# Telemetry-mask counterfactual

## Question

Does selecting R08's direct telemetry statement make the R07–R08 telemetry
edge stronger than both cookie-dark-pattern control edges?

## Controlled change

The frozen v5 experiment was rerun with the same nine notes, note order,
encoder, checkpoint, and container. Only R08's selected byte span changed.

Old R08 mask:

> ⟦Ledger Live Tracks and Sends ALL User Information to Outsourced Data Harvesting Service⟧

New R08 mask:

> ⟦Ledger Live is doing analytics on everything from screen views, to button clicks, error events, installs, uninstalls, etc. It's basically tracking everything.⟧

The complete R08 note was:

> Ledger Live Tracks and Sends ALL User Information to Outsourced Data Harvesting Service
>
> "The tracking code is too structural to be just counting users and downloads, like regular apps do. Ledger Live is doing analytics on everything from screen views, to button clicks, error events, installs, uninstalls, etc. It's basically tracking everything. Anything you do on that app gets tracked."
>
> https://www.nobsbitcoin.com/ledger-live-tracks-and-sends-out-all-user-information-by-default/

The two unchanged reference masks were:

R07 — operating-system telemetry:

> ⟦all those OS's are saturated with telemetry mechanisms and APIs that have access to everything on your devices⟧

R09 — cookie dark patterns:

> ⟦A lot of websites use dark patterns in relation to cookies management, with the majority of them trying to trick you into accepting all of them.⟧

## Result

**The revised telemetry edge became the strongest edge in the triangle.**

| Edge | Old R08 mask | New R08 mask | Change |
|---|---:|---:|---:|
| R07 telemetry ↔ R08 telemetry | `0.385255` | `0.511356` | `+0.126101` |
| R07 telemetry ↔ R09 cookie patterns | `0.396109` | `0.396109` | unchanged |
| R08 telemetry ↔ R09 cookie patterns | `0.264622` | `0.474193` | `+0.209571` |

With the revised mask:

- R07↔R08 exceeded R07↔R09 by `+0.115248`.
- R07↔R08 exceeded R08↔R09 by `+0.037163`.

Both predeclared comparisons passed.

## Isolation check

The eight unchanged output-vector rows are byte-for-byte identical to the v5
baseline. The R08 row is the only row that differs. The experiment binds the
baseline experiment and raw-vector hashes in `experiment.json`.

## What this establishes

The original telemetry ordering was caused at least partly by selecting the
headline about sending data to an outsourced service instead of the passage
directly describing pervasive analytics and tracking. With the direct
telemetry passage selected, the intended telemetry pair became the strongest
relationship among these three notes.

Both of R08's tested relationships increased, so the new mask did not isolate
only R07. It shifted R08 toward both tested tracking-and-privacy references
while still making R07 its closer reference in this triangle.

This is one controlled three-note result. It does not establish mask fidelity
for arbitrary real notes, automatic mask extraction, or later segmentation.
