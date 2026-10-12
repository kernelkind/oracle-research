# Bootstrap prompt-development test-case reset

The user requested starting Bootstrap prompt-development evidence from scratch,
clarifying that the reset concerns **test cases**, while retaining prompts.
This retires the existing case collection; it does not establish that every
historical output was incorrect or change the original AS provenance.

## Git backup and removal

Before deletion, every selected file's current bytes were checked against its
committed Git blob. The complete pre-reset state is protected by the local tag
`bootstrap-tests-before-reset-20261012-cb8c51e0`, pointing to
`cb8c51e0` on the Bootstrap task history. Recovery requires no model calls.

Removed from the working Bootstrap checkout:

- 94 case datasets/collections, including the current ASv6.100 regression and
  branch collections, focused controls, four-Food selection and their older
  source selections.
- 179 experiment specifications referring to those datasets.
- One obsolete data-specific software test asserting the removed historical
  case expectations. General experiment and adapter tests remain.

Of the 273 data/specification files, 33 were present on local main at inventory;
240 were already absent there and existed only in the retained task history.
The reset lands the applicable removals on main without reintroducing that
older history. Git records the complete deleted-path list; the ignored
`target/bootstrap-test-case-reset-v1/inventory.json` also records classification
and pre-reset prompt hashes, without retaining case payloads.

Bootstrap prompts, revision receipts, output schemas and shared prompt fragments
are preserved. A byte-hash check covers all 270 Bootstrap prompt-related files
in the pre-reset checkout. Experiment code and the shared runner are unchanged.

## Data that must remain until backed up

Frozen experiment inputs, model outputs, reviews and raw corpora under `target/`
are not committed Git data. They have **not been deleted**, following the user's
instruction not to delete evidence that is not Git-backed. Raw shared corpora
and other agents' worktrees are also untouched. This task does not authorize
committing ignored model-output blobs or pushing a backup.

Historical findings and accounting records remain available for provenance,
but their cases, hypotheses, expected meanings and semantic judgments are
retired as Bootstrap development evidence. Old `prepare --from` artifacts and
saved case outputs must not be used to seed or grade the fresh Bootstrap tests.
No active Bootstrap regression collection is currently established. New cases
must be prepared from scratch under the user's next test-design instructions.

The embedded synthetic examples remain in the retained prompts; they are not
an active validation set. This reset introduces no new prompt version, inference,
semantic gold, replacement dataset or hierarchy change.

## Verification

Verified that all 273 selected files are absent, all 270 preserved
Bootstrap prompt-related files retain their original byte hashes, and unbacked
native experiment inputs remain present. The native CLI refuses preparation
from the removed four-Food specification without inference, as expected.
Forty-four focused prompt/workflow checks and two production-path collection
adapter checks pass. No model calls were made.
