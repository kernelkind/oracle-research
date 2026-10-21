# PPv10 on Muse 1.3 high — single-call probe

First test of the prominence scorer **PPv10** (draft, `../ppv10-draft-v1/PPv10.md`)
on `meta/muse-spark-1.3-contributor` at reasoning `high` via OpenRouter.
The mask is not regenerated: it is the frozen `MPv3.43` (draft) Astra-low
answer for probe case H15 ("Encouragement to work hard" against
"Rise and grind coffee beans"), mechanically decoded to exact word positions.
One call only; no semantic expectations were predeclared beyond requiring a
valid single-integer score.

Prepare (offline, refuses to overwrite evidence):

The old saved-batch CLI is retired. Preserve these inputs and receipts as evidence;
import them with an explicit template/input mapping rather than rerunning the baseline.
The preparation/collection scripts below describe this saved study, not a second
supported workflow for new prompt experiments.

Collect (verifies pinned inputs and the actual receipt):

`results.json` holds the measured score and provider usage; charges are
settled in `budget-ledger.json`. A valid score is not a semantic approval.
