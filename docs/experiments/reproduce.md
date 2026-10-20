# Inspect and repeat the experiments

Start by browsing a saved hierarchy. To try the generation process, prepare one
recorded post before attempting a whole corpus. The examples below use the
current publication code and the recorded inputs; they keep new outputs separate
from the original results.

**Release downloads are not available yet.** These instructions use the planned
[release layout](README.md#release-layout). The offline checks described at the
end were performed with local copies of the listed files. A download-to-result
test remains pending.

| What you want to do | Example | Model work |
| --- | --- | --- |
| Explore a completed hierarchy | Browse HR39's saved topics and posts | None |
| Try subject identification | Run ASv6.100 on one original HR36 post | Fresh language-model inference |
| Repeat hierarchy construction | Use HR36's 1,000 saved subject outputs with HiGen V5.3 | New definition writing, local SSE encoding and clustering |
| Examine fine-tuning results | Read the seven-version L1 comparison | None |
| Repeat training or recompute L1 scores | See the unfinished workflows below | GPU training; offline scoring from saved judgments |

## Obtain the inputs

From the directory containing the Oracle checkout, start a Bash shell:

```bash
cd oracle-mvp
export ORACLE_ROOT="$PWD"
export RELEASE_ROOT="$ORACLE_ROOT/target/reproduction/release"
mkdir -p "$RELEASE_ROOT" target/reproduction/history
```

The [download plan](downloads.md#start-small) assigns these examples to three
downloads: `hr39-viewer`, `corpus-42d5ce5211a1` and `fine-tune-comparison`.
Choose the downloads for the examples you want to follow. Extract their files
under `RELEASE_ROOT`, preserving their member paths.
[reproduction.sha256](reproduction.sha256) lists the five files used here
and their measured checksums. They total about 47 MiB uncompressed; model
downloads and build dependencies are additional. Archive sizes are not yet
known. These examples do not require the full research collection.

| Files | Purpose |
| --- | --- |
| `evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1/hr39-review-ui-v1/{hierarchy,notes}.json` | Saved HR39 viewer |
| `datasets/42d5ce5211a1a72b08d8df3d80cb5d5668383d2afd27fbee6df331f567e8baef.json` | HR36's 1,000 posts and ASv6.100 answers |
| `evidence/oracle-mvp-qwen-continuation-grading-v1/target/pilot-l1-results-v1/{analysis,verification}.json` | Saved fine-tune comparison |

The combined check below requires all three downloads and all five files.
Individual downloads will also receive their own checksum lists when packaged.
Once all five files are present, verify them:

```bash
cd "$RELEASE_ROOT"
sha256sum --check "$ORACLE_ROOT/docs/experiments/reproduction.sha256"
```

These checks identify the input bytes used for this guide. They do not replace
the eventual release archive checksums or privacy review.

## Browse HR39 without running models

Use Linux and the repository's Nix build environment. Build the viewer:

```bash
cd "$ORACLE_ROOT"
nix develop --command cargo build --locked --release --jobs 1 \
  --bin sse-subject-navigation
export HR39_VIEWER="$RELEASE_ROOT/evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1/hr39-review-ui-v1"
target/release/sse-subject-navigation \
  --categories "$HR39_VIEWER/hierarchy.json" "$HR39_VIEWER/notes.json" \
  --check
```

`--check` validates the saved viewer data without opening an interactive terminal.
Then browse it:

```bash
cd "$ORACLE_ROOT"
target/release/sse-subject-navigation \
  --categories "$HR39_VIEWER/hierarchy.json" "$HR39_VIEWER/notes.json"
```

This opens the existing result: six root choices representing 2,693 of the 5,000
input notes. It does not regenerate the hierarchy or establish that its topic
choices are semantically correct. The [HR39 record](../recommendation-engine/hierarchy-runs.md#hr39--automatically-sampled-5000-note-higen-v53)
describes the run and its review status.

## Try ASv6.100 on a recorded post

Use Python 3.13 and the matching `experiment-runner` checkout described in the
[runtime setup](../generate-hierarchy.md#1-install-the-runtime). For this section,
install only the runner's Python package; Torch and encoder files are unnecessary:

```bash
cd "$ORACLE_ROOT"
if [ -z "${EXPERIMENT_RUNNER_ROOT:-}" ]; then
  if [ -f experiment-runner/experiment_runner/__init__.py ]; then
    export EXPERIMENT_RUNNER_ROOT="$ORACLE_ROOT/experiment-runner"
  else
    export EXPERIMENT_RUNNER_ROOT="$(realpath ../experiment-runner)"
  fi
fi
python3.13 -m venv target/hierarchy-env
source target/hierarchy-env/bin/activate
python -m pip install -e "$EXPERIMENT_RUNNER_ROOT"
```

Keep this environment active. Authentication is not needed for `prepare` or
`show`.

The HR36 corpus includes original post text and saved subject answers. The
`subjects` adapter sends only the post text to the prompt; it does not include
the saved subjects as hints. This example uses the first recorded HR36 note.

Use an unused `target/hierarchy-example/posts.json` and a new experiment
directory. The guard below stops the copy if that input path already exists:

```bash
cd "$ORACLE_ROOT"
export HR36_CORPUS="$RELEASE_ROOT/datasets/42d5ce5211a1a72b08d8df3d80cb5d5668383d2afd27fbee6df331f567e8baef.json"
export CASE_ID=e975bb986241e25414d5aaa81bd9464ed667fce43d81093fbd88e94c1b879d63
(
  set -e
  mkdir -p target/hierarchy-example
  test ! -e target/hierarchy-example/posts.json || {
    echo 'Input already exists: target/hierarchy-example/posts.json' >&2
    exit 1
  }
  cp "$HR36_CORPUS" target/hierarchy-example/posts.json
  python sse_multivector/experiment.py prepare target/reproduction/AS-one \
    --spec sse_multivector/examples/hierarchy-v5.3/subjects.spec.json \
    --history-root target/reproduction/history --only "$CASE_ID"
  python sse_multivector/experiment.py show target/reproduction/AS-one \
    --case "$CASE_ID"
)
```

Confirm that the saved plan contains one case, prompt **ASv6.100**, provider
`openai-codex`, model `gpt-6.1-sol`, and `medium` reasoning effort. The case should
be unrun. `show --case` displays the exact post and prepared request.

To obtain a new answer, use Node.js 24 or later and install the transport's
dependencies:

```bash
cd "$ORACLE_ROOT"
npm --prefix "$EXPERIMENT_RUNNER_ROOT/experiment_runner/frontier_runner" \
  ci --ignore-scripts --no-audit --no-fund
```

Then [authenticate with your own account](../generate-hierarchy.md#2-authenticate)
and run:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py run target/reproduction/AS-one
python sse_multivector/experiment.py show target/reproduction/AS-one \
  --case "$CASE_ID"
```

`run` performs inference and can use paid account capacity, including cache
warming and retries. Inspect the answer's
validation status and any error in `show`; a saved response is not necessarily a
valid subject hierarchy. A new answer need not match the historical answer.

For all 1,000 posts, prepare a **new** directory with the same spec and omit
`--only`. This can require at least 1,000 language-model requests before any
definition writing. Start with the one-post example to check your setup. Use the
generation guide's `collect` step to pass newly generated subjects to hierarchy
construction.

Ordinary preparation can reuse identical saved requests within the supplied
history root. Use `prepare --repeat` only when you want an independent fresh
trial. Reused answers are not additional samples. Changing the provider, model,
prompt or settings creates a different experiment; change the editable spec
before preparation and use a new output directory.

## Repeat HR36 construction from its saved subjects

This skips subject extraction and uses the exact 1,000 ASv6.100 answers originally
supplied to HR36. It performs new definition writing and numerical construction.
It does not reuse HR36's saved definition answers, vectors or final hierarchy.

Complete the [runtime, authentication and encoder setup](../generate-hierarchy.md)
through step 3. The existing example specs match HR36's prompt contents and
language-model settings: **Hierarchy-bootstrap-v133** and
**Hierarchy-consolidated-grouped-v1**, both using `gpt-6.1-sol` with `medium`
reasoning. The corpus order matches HR36's recorded note selection.

The commands require an unused `target/hierarchy-example/subject-collection/subjects.json`
and a new `target/reproduction/HR36` directory. Keep this saved-input run separate
from a run using newly extracted subjects:

```bash
cd "$ORACLE_ROOT"
export HR36_CORPUS="$RELEASE_ROOT/datasets/42d5ce5211a1a72b08d8df3d80cb5d5668383d2afd27fbee6df331f567e8baef.json"
(
  set -e
  mkdir -p target/hierarchy-example/subject-collection
  test ! -e target/hierarchy-example/subject-collection/subjects.json || {
    echo 'Input already exists: target/hierarchy-example/subject-collection/subjects.json' >&2
    exit 1
  }
  cp "$HR36_CORPUS" target/hierarchy-example/subject-collection/subjects.json
  nix develop --command cargo build --locked --release --jobs 1 \
    --bin fine-segmentation-candidate --bin sse-subject-navigation
  python sse_multivector/experiment.py prepare-hierarchy target/reproduction/HR36 \
    --spec sse_multivector/examples/hierarchy-v5.3/hierarchy.spec.json \
    --history-root target/reproduction/history
)
```

Preparation should report `hierarchy-generation-v5.3`, status `bootstrap`,
**5,378 original L1 subjects**, and no completed canonical nodes. It freezes the
new run's inputs without inference. It also lists 61 notes with no original L1
subjects. Preparation does not check that the encoder can load or establish a
memory requirement for construction.

To execute the prepared run:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py run-hierarchy target/reproduction/HR36 \
  --cpu-workers 1
```

This begins language-model requests and local encoding/clustering. One CPU
worker limits concurrency, not total RAM. The current numerical implementation
uses quadratic distance matrices. The 1,000-note experiment is a reproduction
target, not a minimum-resource setup check or evidence of million-note scaling.
Resume this run with the same `run-hierarchy` command after resolving any
reported failure. Do not prepare over an existing run or edit its frozen inputs.
After it completes, export and browse its result:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-canonical-viewer \
  target/reproduction/HR36 --output target/reproduction/HR36-viewer
target/release/sse-subject-navigation \
  --categories target/reproduction/HR36-viewer/hierarchy.json \
  target/reproduction/HR36-viewer/notes.json --check
```

Remove `--check` to browse interactively.

The historical HR36 result represented **683/1,000 notes** beneath its roots.
Compare your run's coverage and inspect its choices; do not treat that count as
a required exact outcome of fresh model responses.

### Which code is being repeated?

The examples above use publication code. They reproduce the inputs, prompt
contents and model settings of the selected stages. They do not recreate the
historical software environment exactly.

For HR36, the recorded Oracle construction commit is
`12ab025bd1a3f7b0615e764c0823be56604f1dc7`; its runner commit is
`38561fefc5e72171a2a3ac7bcbef21367da6e4d7`. The
[run index](hierarchy.csv) distinguishes initial preparation and construction
commits. Earlier commits predate the public authentication support and may need
the original environment. A portable rerun at those exact commits has not been
validated. Record both repository commits, configuration changes and input
hashes when reporting a new run.

## Inspect the fine-tune comparison

The current comparison evaluates the roots of each post's subject hierarchy
(L1) on the same 200 test notes, across seven model/checkpoint combinations.
The [research record](../planning/fine-tuning-pilot-process.md#l1-only-test-results-october-15)
defines correctness and both completeness measures.

Read the saved table with Python's standard library; no model runtime is needed:

```bash
cd "$ORACLE_ROOT"
export L1_RESULTS="$RELEASE_ROOT/evidence/oracle-mvp-qwen-continuation-grading-v1/target/pilot-l1-results-v1"
python3 - <<'PY'
import json
import os
from pathlib import Path

analysis = json.loads((Path(os.environ['L1_RESULTS']) / 'analysis.json').read_text())
print('Version                 Correctness  All roots  Required roots  Invalid')
for name, result in analysis['results'].items():
    s = result['stats']
    print(f"{name:23} {s['correctness_percent']:10.2f}% "
          f"{s['all_root_completeness_percent']:9.2f}% "
          f"{s['required_root_completeness_percent']:14.2f}% "
          f"{s['invalid_outputs']:8}")
PY
```

This displays existing scores. `analysis.json` also retains per-note fractions
and source hashes. `verification.json` records the original verification; reading
it does not rerun that verification. The Qwen pass-2 test collection remains
sealed and is not part of this comparison.

The [adapter inventory](models.csv) identifies all 17 checkpoints, their pinned
base-model revisions and associated training manifests. Inference requires an
adapter's weights/configuration and its matching base model. Resuming training
also requires its optimizer/training state and the original prepared dataset.
These larger files are separate from the five-file example above.
The [publication proposal](downloads.md#corpora-and-fine-tunes) includes all 17
evaluated adapters on Hugging Face. It distinguishes adapter use from
continuation's training-state requirements and identifies the records needed
for a portable training recipe.
The inventory still lists all candidates; these are not available downloads.

There is currently no maintained CLI that rebuilds this L1 analysis from the
saved judgments. The shared runner's `compare-distillation-grades` compares
automated and audited full-hierarchy grades; it does not compute this table.
Likewise, `run-distillation-automatic-grading` can make new model calls and is not
an offline score viewer. Portable training, adapter inference and complete
regrading instructions still need their own validation. The historical
[training runbook](../planning/fine-tuning-pilot-process.md) records what was done;
its machine-specific deployment commands are not a ready-to-run public recipe.

## Other experiments and moved files

Use [experiments.csv](experiments.csv) to identify the saved plan and prompt
version, then the [file lists](files/README.md) and [dependencies](dependencies.csv)
to find its inputs, answers and receipts. Some historical plans have unresolved
input versions or no saved results; see [open items](open-items.md).

Outputs derived from subjects older than **ASv6.100** are historical evidence,
including their downstream hierarchies and evaluations. They are not current
pipeline inputs or validation. Original source posts remain usable.

### Verify a saved prompt experiment after extraction

Check the archive checksums, then extract the experiment's evidence package,
keeping its directory structure. The package supplies the inputs, saved
responses and location metadata needed for verification. Readers do not need
to recreate the research machine's paths or edit any configuration.

Verification requires the Python runtime above, but no credentials or model
worker. For HR39's saved `HR39-resumed-1/batch-00025` prompt experiment:

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
export HR39_EVIDENCE="$RELEASE_ROOT/evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1"
python sse_multivector/experiment.py verify \
  "$HR39_EVIDENCE/HR39-resumed-1/batch-00025/experiment"
```

The command finds the bundled `experiment-locations.json` automatically. These
are additional evidence files beyond the five-file example above. The package
has been tested locally; its release download is still pending. Publishers
prepare it using the [release checklist](open-items.md#prepare-verification-metadata).

This checks the plan and bound source hashes, the manifest, ledger sequence and
provenance, and successful response receipts. Reused responses are checked
against their original producer receipts. The summary distinguishes successful,
failed, unrun and mechanical cases. A successful command means its integrity
checks passed; it does not mean the experiment completed or its answers are
correct. Add `--json` for the measured counts and plan hash.

The command does not reconstruct hierarchy or training outputs, reevaluate
mechanical decisions, verify every transitive adapter input, or recover the
original code from its recorded hashes. Failed attempts receive ledger checks,
not successful-response verification. Archive checksums remain necessary to
check collection completeness. Source hashing and ledger reads are streamed;
the selected plan, configuration and manifests are loaded as JSON. For large
builds, select an individual child prompt experiment.

Preserve the original frozen files. For a new run, use an editable specification
pointing at the verified extracted input files, then `prepare` into a new output
directory. Keep an explicit record of changed paths and settings. Location
mappings apply only to `verify`; they do not make `show`, `collect`, `run` or
`prepare --from` portable. Replay of whole historical collections remains
unfinished.

## What has been tested

Checked on **2026-10-19**, using Oracle code at `ddef7569` and runner code at
`3b73550`, with Python 3.13.12 and tiktoken 0.14.0:

| Check | Result |
| --- | --- |
| Selected release files | All five staged member paths/sizes match the inventory; all five SHA-256 checks pass. |
| Minimal Python setup | The documented editable install succeeds in a new virtual environment without Torch. |
| ASv6.100 preparation and inspection | One unrun case, zero model attempts; its post, rendered prompt and model settings match the original HR36 case. |
| Rust build | Both release binaries build with the repository's locked dependencies and Nix environment, one compilation job at a time. |
| HR39 viewer | `--check` passes on the copied viewer files: 201 categories and 2,693 represented notes. |
| HR36 preparation | V5.3 preparation succeeds with 5,378 original L1 subjects; construction has not started. |
| L1 result display | All seven displayed rows match the saved per-note averages over 200 notes each. This does not reapply the original semantic judgments. |

The Python preparation checks used copies under the planned release layout,
with network connections and access to the original artifact locations blocked
in the checking process. They ran under a 4 GiB process address-space limit.
That limit describes these preparation checks, not the memory needed for
inference, encoding or clustering. Existing tokenizer resources and Cargo
dependency caches were available on the test machine.

No fresh language-model inference, encoder execution, GPU training or new
semantic grading was performed. Interactive browsing was not manually reviewed;
the viewer check exercised its noninteractive validation path. Downloaded-archive
testing, a complete run with public authentication, and exact historical-code
replays remain pending.

The relocation verifier in runner `edf9177` was additionally checked against a copied HR39
`HR39-resumed-1/batch-00025/experiment`: all 11 bound sources and its one
successful receipt passed, with the original artifact locations and network
blocked and a 4 GiB address-space limit. Its frozen plan hash is
`25afccd740b15b2b83fd45246a6d121685176896808b296e1336579fe03f336a`.
This is one saved prompt experiment, not verification of all HR39 evidence.
Runner fixtures also cover moved reused answers, altered/missing inputs and
receipts, deduplicated input locations, failed/unrun cases, upgrade ledgers and
preservation of every evidence file's bytes.

The runner's Python suite passed (211 tests, two skips), as did all ten dedicated
verification tests. The broader Oracle regression check is not green: all 24
failing test methods also failed with the unchanged runner at `3b73550`. No
newly failing Oracle test methods were observed in this comparison.

Archive extraction was also tested locally with runner `62c06e0`: release preparation generated the
bundled locations for this HR39 experiment, then a tar.gz archive was extracted
into a different directory. All 15 evidence files and the generated metadata
retained their checksums. The reader command passed without `--locations`, with
the original artifact paths and network blocked, the staging directory moved,
the private locations file unavailable, and a 4 GiB address-space limit.
This checks one local archive; it is not a download test of a published release.
All 16 verification tests and 90 relevant shared-runner, update and receipt
regression tests passed for this change.
