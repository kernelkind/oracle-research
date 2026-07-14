# Oracle MVP Rules

- The lifetime monetary budget for the entire oracle MVP is **$500 USD**. This is a hard ceiling, not a target.
- The ceiling includes every paid resource used by the effort, including CPU and GPU rentals, storage, transfers, failed or interrupted runs, calibration, evaluation, diagnostics, and confirmation work.
- Before any action that can incur a charge, read `budget-ledger.json`. Do not spend money when the ledger is missing, internally inconsistent, or contains an unknown value needed to prove admission. Treat the ledger as stale whenever an active paid resource or an incurred charge is not represented and reconciled.
- A paid action is admissible only when `actual spend + existing outstanding commitments + the action's maximum charge + reserved remaining-work budget <= $500`. The existing commitments value excludes the proposed action during this check; after approval, add the action's maximum charge to the ledger before accepting the paid commitment.
- Every paid action requires the user's explicit approval of its maximum charge and an external provider-side termination limit that enforces that maximum. A software estimate or process timeout alone is insufficient.
- Update and commit `budget-ledger.json` before accepting a paid commitment and again after reconciling its actual charge.
- Plane work items must represent work that is understood, certain, and ready to execute. Do not create cards for hypothetical branches, conditional future work, or unresolved implementation choices. Create the work item only when its trigger has occurred and its scope is known.
