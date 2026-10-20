# Inspect and repeat the experiments

Start by browsing a saved hierarchy. To try the generation process, prepare one
recorded post before attempting a whole corpus. The examples below use the
current publication code and the recorded inputs; they keep new outputs separate
from the original results.

**Downloads are not available yet.** The
[shared-dataset commands](#check-the-converted-local-selection) prepare, verify
and restore the local upload files listed in [publication-files.csv](publication-files.csv).
Restoration recovers original compact exports, not complete native experiment
directories. The browsing and generation examples below still use local copies
of original research files in an earlier layout; restoration alone does not
supply those files. Public paths and hosted reader workflows remain untested.
In the clean-VM check, HR39 and the used-posts collection restored successfully,
but `export-canonical-viewer` required an internal `state.json` absent from the
compact export. Browsing directly from the published `hierarchy.jsonl` and posts
still needs a supported command.

To generate and browse a new hierarchy from your own posts, use the
[generation guide](../generate-hierarchy.md). Its complete 12-post workflow
passed in a fresh Linux VM; it does not require these historical files.

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

The [locally checked examples](downloads.md#start-small) use three original-file
groups: `hr39-viewer`, `corpus-42d5ce5211a1` and `fine-tune-comparison`.
With those original files available locally, place them under `RELEASE_ROOT`
at the paths below. Public exports may use different files and paths.
[reproduction.sha256](reproduction.sha256) lists the five files used here
and their measured checksums. They total about 47 MiB uncompressed; model
downloads and build dependencies are additional. These examples do not require
the full research collection.

| Files | Purpose |
| --- | --- |
| `evidence/hierarchy-run-store/hr39-v53-auto-5000-note-v1/hr39-review-ui-v1/{hierarchy,notes}.json` | Saved HR39 viewer |
| `datasets/42d5ce5211a1a72b08d8df3d80cb5d5668383d2afd27fbee6df331f567e8baef.json` | HR36's 1,000 posts and ASv6.100 answers |
| `evidence/oracle-mvp-qwen-continuation-grading-v1/target/pilot-l1-results-v1/{analysis,verification}.json` | Saved fine-tune comparison |

The combined check below requires all five original files. Published exports
will receive checksums for their actual contents.
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
nix --extra-experimental-features 'nix-command flakes' develop \
  --command cargo build --locked --release --jobs 1 \
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
  nix --extra-experimental-features 'nix-command flakes' develop \
    --command cargo build --locked --release --jobs 1 \
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

### Export compact hierarchy results

New `run-hierarchy` executions write a `publication/` directory after completion
or blockage and attempt the same export after failure or interruption, once
submitted jobs have stopped. The saved graph can be partial; its execution
status and graph status are recorded separately.

To export the HR36 run above without inference or refresh it after a resume:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-hierarchy-results \
  target/reproduction/HR36
```

The default output is `target/reproduction/HR36/publication/`. For another
destination, pass `--output target/reproduction/HR36-results`. The same command
accepts an original saved hierarchy directory containing `state.json`; the five
viewer/corpus/comparison files used elsewhere in this guide do not include that
state.

| File | What it preserves |
| --- | --- |
| `experiment.json` | Recorded versions/settings, input identity, graph and execution status, counts and payload checksums |
| `input-note-ids.txt` | The full ordered input selection, including unrepresented notes |
| `hierarchy.jsonl` | Unsigned hierarchy nodes with titles, definitions, ordered links and direct source-post references |

No signing credentials, source-corpus scan or original receipt files are needed
for this export. It streams the saved state once, hashes its bytes, retains graph
and settings, and skips construction working data. The runner's editable install
above includes the streaming parser dependency. Export validates graph/reference
structure; it does not reverify the research's complete original inputs or
semantic quality. Missing historical provenance stays unknown;
an unrecorded execution outcome is `not_recorded` rather than inferred from the
exporter's checkout or graph status. The [format description](downloads.md#automated-outputs)
explains the unsigned records and outside-children post references.

The command honors an existing native execution lock and refuses an active run.
Older directories without that lock receive a coherent saved-state snapshot
check; this does not exclude every possible external writer. Destinations with
unrelated files are refused, and concurrent publication writes are serialized.
It refreshes only this experiment's existing three-file export; an unchanged
re-export retains bytes and modification times. `experiment.json` is replaced
last and hashes the other two files so an interrupted refresh can be detected.
Original state and research evidence are left intact.

New runs retain a publication UUID across moves. Older runs without that saved
identity use an opaque source-location hash; after moving such a source, choose
a fresh publication destination. No original absolute path is included in that
identity. Preparation-time commits and later code upgrades are distinguished in
the metadata. The input's deprecation field records known pre-ASv6.100 lineage;
unknown provenance remains `null`, and `false` is not semantic approval.

These three files are publication outputs; the browser above still uses its
separate viewer files. The local backfill includes all 37 official outputs and
203 supported historical branch outputs. Unsupported older formats and testing
the eventual public downloads remain open.

### Export other compact results

These are publisher commands for selected saved experiments. The paths below
illustrate each input type; use the corresponding original source from the
experiment index. They perform no inference and leave that evidence intact.
Download locations still need to be assigned.

For a native prompt experiment containing `experiment.json` and `report.json`:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-results \
  target/prompt-study-v1 --output target/prompt-study-results
```

The three files are `experiment.json`, `inputs.jsonl` and `results.jsonl`.
Inputs store exact template variables once per hash; results retain final
answers, case outcomes, reuse and attributed reviews. The metadata binds the
saved report and input order. This exports that report snapshot, including its
recorded judgments; it does not merge newer sidecar edits or reverify receipts.
Missing reports and known internal construction jobs are refused. New standalone
preparation, execution and review refresh the same export automatically. Native
hierarchy children, coordinator-created grading jobs and cache warmups are
excluded from separate prompt exports; final evaluations retain their judgments.

For an older subject-prompt study saved with `calls.json`, `input.json`,
`plan.json`, final outputs and review records:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  target/saved-prompt-study --kind prompt-study \
  --output target/saved-prompt-study-results
```

This publisher command requires the original saved study directory. A report
copied into Git or a compact download alone does not provide that working layout.
It exports exact used posts in `inputs.jsonl`, final responses in `answers.jsonl`,
recorded assessments in `judgments.jsonl`, final measurements in `results.jsonl`
and parameters/source hashes in `experiment.json`. Reviews retain their recorded
attribution and caveats; they do not establish user approval. Preparation and
output bindings are checked without running models. Authentication settings,
rendered requests and transport logs are excluded, and original files remain
unchanged. Known pre-ASv6.100 results are labeled as historical deprecated data.

The ASv6.100 generalization assessment also has five original Markdown documents
under `evaluations/asv6.100-generalization-v1/`: its final quality summary and
four frozen agent rubrics. These are selected verbatim, without a conversion
command or `experiment.json` wrapper. The [study record](../../sse_multivector/subject-prompt-goal-v1/asv6.100-generalization-v1/README.md#publication-files)
lists their paths. Their original source hashes are the publication-file
checksums; the six existing native bundles contain the answers and reviews.

For the six additional subject/mask collections, the same command accepts an
explicit selection and study ID. `SOURCE_ROOT` is the original repository root,
rather than an individual study directory. The
[subject/mask checks](#historical-subject-and-mask-study-checks) describe the
three selections, source requirements and five-file output.

For the selected legacy title/description studies, a publisher with the exact
original saved files can use the maintained
[selection specification](../../sse_multivector/experiment_specs/title-study-publication-v1.json):

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  sse_multivector/hdbv2-node-description-probe-v21 \
  --kind title-study \
  --spec sse_multivector/experiment_specs/title-study-publication-v1.json \
  --output target/title-study-results
```

The source directory's parent must contain the exact declared study files and
shared inputs; a clean checkout or compact download alone does not have that
original layout. The command makes no model calls. Its five files are
`experiment.json`, `inputs.jsonl`, `answers.jsonl`, `judgments.jsonl` and
`results.jsonl`. They retain final answers, scientific findings, recorded reviews,
failure outcomes and necessary inputs/settings. Source hashes, UTF-8 mask spans,
prompt substitution and receipt bindings are checked; unknown scientific fields
or ambiguous joins stop the export. Rendered requests, account settings and
transport logs are excluded. See the [checks](#historical-title-study-checks).

For fine-tune validation answers, final grading reports and final comparisons:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  target/fine-tune-run --kind validation
python sse_multivector/experiment.py export-evaluation-results \
  target/grading/grades.json --kind grades
python sse_multivector/experiment.py export-evaluation-results \
  target/review-method/report.json --kind review
python sse_multivector/experiment.py export-evaluation-results \
  target/l1-comparison/analysis.json --kind comparison
```

`validation` accepts a training-run directory or one complete/partial saved
validation stage. It scans baseline, legacy trained and checkpoint evaluation
stages, excluding `test/`. Outputs live outside sealed stages under
`publication/evaluations/`. Grading exports include the exact selected raw
answers, scores/proofs and deduplicated supporting judgments; missing bindings
remain explicit. These selections do not include sealed Qwen pass-two answers.
L1, paired-grade and effort reports retain their distinct measurement schemas.
Use `--output` to choose a separate destination.

Numerical studies require a supported result profile:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-numerical-results \
  target/geometric-study --family geometric
```

The profiles are `geometric`, `fuzzy`, `hidef`, `merge-rule`, `comparison`,
`performance`, `fine-region` and `pair-scores`. Use `fuzzy` for the native fuzzy
memberships and final interpolation; a hard projection is a distinct result.
Directory inputs default to their `publication/` directory; individual result
files default to `publication/STEM/` alongside the source. An explicit profile
is required when the old format is ambiguous. Unsupported schemas fail.

Geometric/fuzzy, HiDeF, merge-rule and benchmark final writers also call this
exporter automatically. Older Rust/diagnostic command implementations remain
unchanged and need the offline command. The exports retain native results and
canonical source mappings, omitting working coordinates and distance tables.
Historical AS provenance must still be checked before any current-pipeline reuse.

The [format reference](downloads.md#automated-outputs) explains the payloads and
their limits. Managed exports refuse unrelated destinations, bind payload
checksums and preserve unchanged file bytes/mtimes. The supported historical
selection has been converted locally. Review of the selected public contents
and testing eventual downloads remain open.

### Check the converted local selection

[Publications](publications.csv) records 2,988 output/input bundles plus one
shared-content row. [Publication files](publication-files.csv) and
[checksums](publication.sha256) describe 9,684 physical files beneath
`target/publication-dataset/`. Original compact exports stay unchanged in
`target/publication-exports/`.

Publishers prepare both historical and future exports with the same command.
Preparation and restoration both require a new output directory; an existing
output is refused. Use a fresh directory for another revision.
This historical selection uses a private, bound execution audit:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py prepare-publication-dataset \
  target/publication-exports \
  --output target/publication-dataset \
  --selection target/publication-audit/shared-dataset-7bee4993/unrun-selection.json
```

The audit and its private source locations are not reader dependencies. For
all-unrun snapshots, preparation requires execution evidence bound to the saved
exports and rechecks originals under their read locks. Unclassified or changed
evidence stops preparation. The audited selection excludes 196 preparations
proven never executed and retains three ambiguous snapshots. Native exporters
remain unchanged; a saved all-unrun report alone does not establish nonexecution.

To verify a complete prepared or downloaded dataset:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py verify-publication-dataset \
  target/publication-dataset
```

This checks physical hashes, shared records and references, and each restored
original file's hash. Shared rows contain numeric IDs, full SHA-256 hashes and
values; JSON files may contain references such as `{"$ref":123}`.
`dataset.json` records both physical and original compact-file identities.

To recover one bundle for ordinary JSON inspection or consumers of the original
compact format:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset \
  --output target/restored-publication \
  --publication historical-studies/crec-119-500-note-vector-v1
```

Omit `--publication` to restore all included bundles. A single-bundle restore
needs `dataset.json`, that bundle's files and its referenced shared files; it
verifies those inputs without requiring unrelated downloads. Whole-dataset
verification requires all files. Restored compact exports match their original
bytes and `experiment.json` payload hashes. They do not provide the native plans,
receipts and run directories required by `show`, `review` or native `verify`.

The complete preparation verified every reconstructed original hash, finished
in 54.06 seconds and used 108,516 KiB peak resident memory under a 512 MiB
address-space limit. All 34 relevant runner/project tests passed. This verifies
file integrity, not scientific correctness or privacy. The
[measured selection](downloads.md#measured-local-exports) describes sizes and
exclusions. The
[conversion-gap table](publication-gaps.csv) now has no open rows. TRUE10's
export uses its saved run configuration and plan. All 33 formerly unsupported entries
now have selected evidence or an explicit intermediate/duplicate disposition. The
[historical collection review](open-items.md#historical-collection-review)
resolved its 109 groups through retained material or selected final evidence.

Four old output-note counts include notes present only in the old top container:

| Run | Recorded output notes | Notes under published topics | Top-container-only notes |
| --- | ---: | ---: | ---: |
| HR27 | 46 | 43 | 3 |
| HR28 | 94 | 87 | 7 |
| HR29 | 198 | 177 | 21 |
| HR30 | 976 | 582 | 394 |

The saved states reproduce these counts exactly. The unsigned hierarchy retains
actual topic nodes, while the complete ordered input selection remains separate.
The original ledger and graphs were preserved; the publication table explains
the difference. Completion and graph coverage do not establish semantic quality.

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

The recorded Oracle IDs remain unchanged after the generated-data rewrite.
The bundled [commit map](commit-map.txt) has an `old new` header followed by full
original and rewritten IDs. Use the `new` column for raw Git commands; Git does
not read this file automatically. The runner's history was not rewritten.

Historical readers and verifiers use
`generation_history.source_at_revision(path, revision)`. It accepts a full
original ID or a unique 7–40-character hexadecimal prefix. It prefers the
original commit when that object is available; otherwise it reads the mapped
commit, without replacement refs or a working-file fallback. Named refs such as
`HEAD` pass through. For example, read HR36's saved generator source:

```bash
cd "$ORACLE_ROOT"
python3 - <<'PY'
from pathlib import Path
import sys
from sse_multivector.generation_history import source_at_revision

sys.stdout.buffer.write(source_at_revision(
    Path("sse_multivector/hierarchy_generation.py"),
    "12ab025bd1a3f7b0615e764c0823be56604f1dc7",
))
PY
```

This reads saved source only. It cannot recover generated artifacts removed
from history or establish a complete historical environment. At code commit
`3ecbc0d4`, the six revision tests, the legacy automatic-workflow test and this
example were checked in a fresh ordinary clone without replacement refs, private
audit files or saved research inputs.

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
The [publication plan](downloads.md#corpora-and-fine-tunes) includes all 17
evaluated adapters on Hugging Face, with prepared training data and settings.
Optimizer state remains outside that plan; resuming an exact training state
requires additional local artifacts.
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

The [study index](experiments.csv) contains 2,488 selected entries: native prompt
preparations, official hierarchy runs, training runs, historical collections
and the four located historical subject-prompt studies.
It records saved plan identities and prompt/model settings.
[Publications](publications.csv) connects them to the exported results;
[publication files](publication-files.csv) lists their exact files and hashes.
Structured exports record their versions and bindings in `experiment.json`;
the original Markdown documents use direct source hashes.

The complete original index and workspace discovery tables are preserved in the
local audit described in [open items](open-items.md). They cover internal jobs,
warmups and original receipt dependencies as well as selected studies. Historical
input-version limitations remain documented there. The compact exports do not
contain complete original native receipt packages.

Outputs derived from subjects older than **ASv6.100** are historical evidence,
including their downstream hierarchies and evaluations. They are not current
pipeline inputs or validation. Original source posts remain usable.

### Verify a saved prompt experiment after extraction

This workflow requires a complete original native experiment package. It does
not apply to the intended compact publication exports or require publishing
internal hierarchy-generation responses. For a complete local package, check its
checksums and extract it with its original structure, bound inputs, responses
and location metadata. Verification then works without recreating the research
machine's paths.

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
has been tested locally; publishing it is not part of the compact-output plan.
The [native verification instructions](open-items.md#prepare-verification-metadata)
describe how such complete local packages are prepared.

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

### Hierarchy publication checks

A local HR39 export was checked against its saved 250.61 MiB state: 200 nodes,
six roots, 2,693 represented notes and the full ordered selection of 5,000 input
IDs. Its three output files total **804,511 bytes (about 786 KiB)**; post text
remains separate. The streaming export used **47,380 KiB peak resident memory**
and passed under a **512 MiB process address-space limit**. These measurements
describe exporting this saved graph, not memory needed to generate it or proof
of million-note scalability. Nothing was uploaded.

A fresh isolated editable runner installation automatically installed its
dependencies and passed `pip check`; six JSON-projection tests passed.

After correcting the receipt-reader instance call used by numerical validation,
all **177 relevant Oracle checks pass**: 127 V3/V5 construction checks, 38
publication/viewer/runtime checks and 12 HDBSCAN adapter checks. This includes
the 42 construction checks that previously failed and a new regression that
first reproduced the exact call error, then passed with the fix. The checks
exercise production paths with local fixture runners and encoders; they make
no paid model calls and do not rerun the archived experiments.

### Other compact export checks

Local fixture tests cover standalone prompt lifecycle/review exports, explicit
historical snapshots, internal-job exclusion, partial validation and grading,
selected-answer/judgment bindings, guest packaging, and supported numerical
profiles. They also check source preservation, destination ownership, unchanged
refreshes, bounded streaming and omission of private configuration and raw
execution diagnostics. Scientific findings and attributed review comments remain
part of the results; these checks do not replace review of the selected contents.

The complete shared-runner suite ran 246 checks: 244 passed and two were skipped;
its focused publication group also passed all 54 checks. The Oracle hierarchy,
adapter, viewer/runtime and publication integration group passed all 190 distinct
checks across the full run and a targeted eight-test rerun after removing the
retired concurrency field from its fixture. The evaluation exporter passed
12 checks plus three relevant native regressions. The numerical/final-writer
group ran 75 checks: 71 passed and four requiring GPU hardware were skipped.
The complete pinned HiDeF environment was not exercised; its final-writer hook
and selected containment regressions were checked with local fixtures.

Two broader evaluation-workflow failures also reproduce with unchanged Oracle
code and the same runner: the native allowance/resume test receives an additional
stopped-before-dispatch error, and the effort-analysis CLI fixture has a native
concurrency mismatch. These are unresolved compatibility limits, not successful
reproductions. No paid inference or official research experiment was run.

Representative historical sources were exported locally with a 512 MiB process
address-space limit. A 1,200-answer grading preview, including scores/proofs and
38,017 distinct supporting judgments, totaled about 91.5 MiB with about 48 MiB
peak resident memory. Numerical previews ranged from about 14 KiB for a small
comparison to 7.81 MiB for native fuzzy memberships. These samples do not measure
the final collection or establish conversion of the entire inventory. Originals
were preserved, and nothing was uploaded.

### Historical backfill checks

Before dataset selection and sharing, the source-export checkpoint contained
**3,184 output/input directories and 10,015 files**, totaling
**1,178,119,887 bytes**. These are preserved original compact exports, not current
upload sizes. Every checkpoint file was independently
rehashed. Structured payload bindings were checked against their export manifests;
the five original ASv6.100 Markdown documents match their recorded source hashes.
Exact prepared-input copies were also checked against their frozen source hashes.
The complete staged file tree
matches the selected file list, excluding all private selection logs and
superseded generated copies.

All **27,032 native jobs** were classified in the source audit. The public
source-export index selected 2,547 standalone preparations with distinct frozen
plan identities. The current dataset excludes 196 proven unexecuted preparations
from that selection and retains three ambiguous snapshots. The other source
jobs are warmups, internal hierarchy/grading units, manual construction or
resource-test intermediates, or input preparation. Simulated worker responses
from the resource tests were excluded; their final measurements were retained.
The historical hierarchy selection adds 203 saved final/last branch outputs to
the 37 official runs without treating those branches as independent trials.

All 67 selected evaluation sources passed their answer and judgment joins:
zero missing selected answers, zero missing judgments and zero conflicting
judgment hashes. **1,966** older judgments have `receipt_only` bindings; this
does not invent an absent separate output hash. Source-assessment actor fields
remain `not_recorded` wherever the originals did not identify an actor.

Conversion workers used a 512 MiB process address-space cap. Recorded prompt
and evaluation peaks were about 163 MiB and 158 MiB respectively. Historical
format regressions passed 20 evaluation/paired/native checks and 78 numerical
checks (four GPU skips); four final production-CLI integration checks also
passed. The two broader evaluation compatibility failures described above
remain unresolved. No fresh inference, training or semantic grading occurred.

This checks the selected formats; it does not claim exhaustive all-history
coverage. The [conversion-gap list](publication-gaps.csv) is now empty. Privacy
review and a clean reader test against the eventual hosted selection remain pending.

### Saved hierarchy, navigation and performance checks

Three maintained selections cover the final 33 formerly unsupported entries.
They produce 28 bundles; duplicate and intermediate records do not become
separate studies:

| Selection under `sse_multivector/experiment_specs/` | Contents |
| --- | --- |
| [saved-hierarchy-publication-v1.json](../../sse_multivector/experiment_specs/saved-hierarchy-publication-v1.json) | 14 final hierarchies/partitions and two manual reference fixtures |
| [navigation-study-publication-v1.json](../../sse_multivector/experiment_specs/navigation-study-publication-v1.json) | Eight navigation studies |
| [performance-study-publication-v1.json](../../sse_multivector/experiment_specs/performance-study-publication-v1.json) | Four units containing seven final reports and their summary |

With the original saved files arranged under the source repository root:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/saved-hierarchy-publication-v1.json \
  --study saved-hierarchy-GDC09 \
  --output target/saved-hierarchy-results
```

For another entry, use its specification and exact key from that file's
`studies` object. Each selection checks its original source hashes; compact
downloads alone do not recreate the required source layout. The command performs
no model calls. The five-file historical-study format keeps results, inputs,
judgments and parameters separate.

Categorized hierarchies use unsigned `kind`/`tags`/`content` records in
`results.jsonl`; original assignments remain bound in their input records.
Infomap partitions retain their native numerical meaning. The two manual
fixtures remain reference inputs, not generated trial outcomes. HR02 retains
its final view rather than its preparation state. CPC01's run and complementary
analysis form one unit; the redundant HR35 source-hash comparison is excluded.

The batch totals **140 files, 10,973,854 bytes**, or **2,078,449 bytes** with
gzip level 6. All **219 relevant tests** pass. The exact admitted 180-case
training selection and frozen fitter/runtime version remain unlocated for the
learning benchmark; saved measurements do not establish full replay. Unknown
AS provenance stays unknown. Original evidence remains unchanged; nothing was
uploaded. Final privacy review and hosted reader tests remain open.

For TRUE10, use the [true-graph selection](../../sse_multivector/experiment_specs/true-graph-publication-v1.json)
and study ID `navigation-TRUE10` in the same command. The source root must also
contain the six selected score bundles at the `target/publication-exports/`
paths declared by the specification, so their referenced payloads can be verified.
It binds the existing
`TRUE10/run/config.json` and `TRUE10/plan.json`; assembly never wrote
`TRUE10/graph/config.json`. The raw 60-node/95-edge graph and canonical
58-node/88-edge graph retain their four and two cycles respectively, alongside
58 note memberships, 77 source posts and two saved agent assessments. Its
3,540 raw direction references use exact score bodies in six existing bundles;
3,306 canonical directions are verified separately. All 25 focused/common/unsigned
tests pass. This closes the conversion gap without claiming full reproduction.

### Archived baseline checks

The [baseline selection](../../sse_multivector/experiment_specs/baseline-study-publication-v1.json)
binds four compact historical bundles to exact archive members and their saved,
extracted counterparts:

| Study ID | Selected final evidence |
| --- | --- |
| `crec-119-500-note-vector-v1` | 500 posts, 1,311 takeaways and 150 segments |
| `crec-119-500-note-vector-v2` | 500 posts, 1,268 takeaways and 147 segments |
| `communicated-meaning-tev4-1` | 194 subjects and 18,721 unique pairwise cosine measurements |
| `narrowest-subject-v1` | 187 subjects and 17,391 unique pairwise cosine measurements |

A publisher with the original saved repository layout can use:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/baseline-study-publication-v1.json \
  --study crec-119-500-note-vector-v1 \
  --output target/baseline-results
```

Use another exact study ID from the table to export that selection. The command
checks the frozen hashes against the extracted counterparts without decoding
archives or making model calls. It needs the original saved layout; compact
downloads alone do not recreate it. No additional dependency is required.
Each bundle contains `experiment.json`, `inputs.jsonl`, `answers.jsonl`,
`judgments.jsonl` and `results.jsonl`. Full archives and working vectors remain
outside the selected downloads.

The CREC answers preserve **parsed assembled note results**, not raw per-call
response strings. V2 retains reuse of 492 notes and 3,004 final jobs; its eight
new notes account for 32 new final jobs. The two geometry bundles retain exact
cosine values, analysis headers and subject diagnostics. TEv4.1's 194 answer
inputs already appear in `numerical/fine-region-00d974f22ed8935f/inputs.jsonl`;
the new bundle references them and intentionally has an empty `answers.jsonl`.
AS lineage remains unknown. Recorded TP versions do not establish AS provenance,
and these historical results do not validate the current pipeline.

The four bundles total **20 files, 6,196,469 bytes**, or **1,218,841 bytes** with
gzip level 6. All **178 relevant tests** pass; all four actual-file exports pass
under a 512 MiB worker address-space limit. Independent checks verified the four
archive/member/counterpart mappings. The 50 selected originals (69,121,674 bytes),
all 98 independently audited originals and all 9,850 previously selected files
retain their original bytes, modes and modification times. Nothing has been uploaded; final
publication privacy review and hosted reader tests remain open.

### Fine-region title and real-note segmentation checks

These three local bundles retain final evidence from two title collections and
nine real-note segmentations. Their maintained selections name exact original
files and SHA-256 hashes:

| Selection under `sse_multivector/experiment_specs/` | Study ID |
| --- | --- |
| `title-audit-publication-v1.json` | `fine-region-hierarchy-title-candidates-v1` |
| `title-audit-publication-v1.json` | `fine-region-title-cutoff-audit-v1` |
| `segmentation-study-publication-v1.json` | `real-note-fine-segmentation-v1` |

A publisher with the original saved layout can prepare the same data without
model calls. This example uses a sibling directory for those originals:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/title-audit-publication-v1.json \
  --study fine-region-title-cutoff-audit-v1 \
  --output target/title-cutoff-results
```

For another selection, substitute its specification and exact study ID from the
table. The source argument identifies the complete original repository layout;
a clean checkout or compact download alone does not contain it. Each bundle has
`experiment.json`, `inputs.jsonl`, `answers.jsonl`, `judgments.jsonl` and
`results.jsonl`. Unchanged refreshes preserve their bytes and modification times.

The title bundles retain all **50 raw answers and 49 recorded user decisions**.
H000019 remains unreviewed. Generated wording and the wording actually reviewed
are separate fields: ten cutoff labels still differ after ignoring letter case
and outer bold markers.
The inputs preserve both original post/mask context and the exact supplied
fragment or descendant-title order. Frozen prompt templates reconstruct every
request; model settings and isolation controls remain recorded. The historical
prompt-registry hash differs from the located registry; that mismatch is explicit,
and its selected template reproduces all frozen requests.

The segmentation bundle retains **nine final selections, complete hierarchy
outputs for two tested runs, and 248 distinct curated posts** across five datasets.
Dataset-specific vector identities and token/index mappings remain, while
duplicated subject and mask fields reference the curated input records. No
embedding values or working distance arrays are published. Its empty
`answers.jsonl` is intentional: these curated inputs are not additional model
answers. Frozen generation packages, encoder identities, numerical parameters
and input normalization remain recorded.

The **132 structured user decisions** are the original saved states, alongside
215 baseline packets without a recorded decision. They are not a latest aggregate
verdict: the [cross-note findings](../../sse_multivector/real-note-fine-segmentation-v1/cross-note-density-v1/README.md)
separately record the later garden/allotment retraction. Music-review status and
the authorized encoding omission remain explicit. ASv6.23-derived subjects and
masks remain deprecated historical evidence; raw posts are not deprecated.

The three exports total **15 files, 15,222,404 bytes**, or **3,006,062 bytes** with
gzip level 6. Actual-file exports and independent source/payload comparisons
pass under a 512 MiB worker address-space limit. Original sources remain
unchanged. Nothing has been uploaded; publication privacy review remains open.

### Frontier comparison checks

The [frontier selection](../../sse_multivector/experiment_specs/frontier-study-publication-v1.json)
names 13 entries from one historical collection: compatibility tests, subject
comparisons, recorded completion variants, a mask-cost study and the interim
teacher comparison. With the same original source layout used above:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/frontier-study-publication-v1.json \
  --study frontier-asv6.23-diagnostic-v2 \
  --output target/frontier-as23-results
```

Other study IDs are exact keys in the selection's `studies` object. This command
performs no model calls.

The **65 files total 4,193,178 bytes**, or **627,081 bytes** with gzip level 6.
They retain **233 completed raw answers**, three partial strings from failed
attempts, 73 recorded failed attempts and 17 outcomes absent from their individual
frozen runs. Later continuations remain separate; an absent result in an initial
run does not imply the collection never obtained that answer. Transport completion,
format validation, failure details, usage, settings and nullable token limits are
preserved separately.

Sixty Muse mask answers and 22 Astra baselines link their already-selected
publications with exact answer hashes. The N031 answer reused by the later
high-reasoning comparison remains linked to the earlier variant. These references
are not additional answers or trials. Full source posts and the shortened text
actually supplied in two ASv6.23 cases remain distinct.

All **437 review cells** preserve their comments and exact source-answer/display
bindings, or explicit finding/outcome text. The **258 blinded-packet membership
rows** preserve case/arm mappings and rubrics; overlapping slots are intentional.
These counts are not user judgments. The original score-A file contains 129
recorded scores. The teacher summary remains interim: its aggregate counts eight
subject answers while native receipts retain ten, including later retries; it
records no final parity verdict.

All **172 relevant regressions** pass, including the focused offline checks:

```bash
cd "$ORACLE_ROOT"
PYTHONPATH=.:sse_multivector python -m unittest \
  sse_multivector.test_historical_study_streams \
  sse_multivector.test_title_audit_publication \
  sse_multivector.test_segmentation_study_publication \
  sse_multivector.test_frontier_study_publication \
  sse_multivector.test_historical_study_cli
```

All 16 title/segmentation/frontier original-file exports also pass under a
512 MiB worker address-space limit. Their 366 selected sources retain their
SHA-256 hashes, bytes, modes and modification times; all 9,770 previously selected
files are unchanged. The [file list](publication-files.csv) and
[checksums](publication.sha256) cover the exact local selection. ASv6.23/ASv6.48
derivatives remain deprecated historical evidence. No inference or uploads
occurred; final publication privacy review remains open.

### Early prompt and manual prominence study checks

The 22 additional collections contain early TP/MP development batches, standalone
mask studies and three manual prominence studies. The selections retain their
514 saved final answers, used inputs, scientific settings, recorded assessments
and user reviews. Prominence scores remain paired with their exact raw answers,
source posts and masks. The 93 already-selected native prominence bundles retain
their existing files and links.

| Selection | Entries | Example study ID |
| --- | ---: | --- |
| [Early and standalone prompt studies](../../sse_multivector/experiment_specs/standalone-prompt-publication-v1.json) | 21 | `mask-prompt-astra-ten-note-v1` |
| [Manual prominence studies](../../sse_multivector/experiment_specs/prominence-study-publication-v1.json) | 3 | `prominence-prompt-goal-v1/ppv10-ranking-v1` |

A publisher with the exact original files can export a selected study using the
same offline command. This example places those originals in a sibling directory
named `oracle-mvp-original`:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/standalone-prompt-publication-v1.json \
  --study mask-prompt-astra-ten-note-v1 \
  --output target/early-mask-results
```

For a prominence study, use its selection file and exact study ID from the table.
The source argument names the original repository root. A clean checkout or
compact download alone does not contain that complete saved layout. The five
output files use the same names as the [subject/mask exports](#historical-subject-and-mask-study-checks).
Their source and payload hashes identify the exact evidence; no model runs.

Reused comparison baselines remain references to their original studies. Setup
subject-generation outputs validate the used inputs without becoming additional
standalone results. The transfer study retains one recorded failure alongside
71 saved answers. `tpv3.82-redundancy-iteration-1` retains two receipt-only answers
and three unknown outcomes among its five configured cases. Missing canonical
post IDs stay missing; native case IDs and exact text identify those inputs.

Original review states and later rereviews remain distinct; identical embedded
snapshots reference those states. Undecided items acquire no decision, and
assistant applications of user feedback remain separate from the user's own
decisions. The probe-v3 M05 review displayed fragments in a different order:
that display transformation and the original raw answer are both preserved.
Recorded subject provenance determines deprecation; unknown lineage stays unknown.
All 12 standalone mask studies derive from ASv6.8 and remain deprecated historical
evidence. The nine early TP/MP studies have unknown AS lineage. Raw posts are not
deprecated by this rule.

The prominence exports retain frozen score expectations, comparisons and agent
assessments. Missing execution/reuse fields remain unknown. One historical mask
helper has moved; its pinned earlier bytes are located in retained Git history.
The export checks the saved masks and requests without claiming to have rerun
that historical helper.

All 113 relevant historical-study, prompt/title, evaluation and publication-workflow
tests pass. The focused new regressions can be run without model calls:

```bash
cd "$ORACLE_ROOT"
PYTHONPATH=.:sse_multivector python -m unittest \
  sse_multivector.test_standalone_prompt_publication \
  sse_multivector.test_prominence_study_publication \
  sse_multivector.test_historical_study_publication \
  sse_multivector.test_historical_study_cli
```

All 24 original-file exports pass under a 512 MiB worker address-space limit.
Their 120 files total 2,440,074 bytes (370,563 bytes with gzip level 6). Every
payload/source binding matches, and all 302 selected source files retain their
bytes, hashes, modes and modification times. A regression verifies identical
output bytes and native missing-case order across separate Python processes.
This verifies selected evidence, not semantic quality or publication privacy.

### Historical subject and mask study checks

Six original collections now link 123 additional study/review entries under
`historical-studies/`. Their 1,965 exact saved responses comprise 114 atomic
subject answers, 931 subject-goal answers and 920 mask-goal responses. The latter
include mask answers and the subject, comparison and position responses used by
those studies. These are saved-response counts, including reuse, rather than
counts of independent calls.

The maintained selections bind each original source by SHA-256:

| Selection | Entries | Study IDs |
| --- | ---: | --- |
| [Atomic subjects](../../sse_multivector/experiment_specs/atomic-study-publication-v1.json) | 4 | `atomic-subject-…` |
| [Subject goals](../../sse_multivector/experiment_specs/subject-goal-publication-v1.json) | 55 | Exact keys in `studies`, such as `asv6.12` |
| [Mask goals](../../sse_multivector/experiment_specs/mask-goal-publication-v1.json) | 64 | `mask-prompt-goal-v1/…` |

A publisher with the exact saved files can export one selected entry without
inference. This example runs the publication code with the original files in
a sibling directory named `oracle-mvp-original`:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-evaluation-results \
  ../oracle-mvp-original \
  --kind prompt-study \
  --spec sse_multivector/experiment_specs/atomic-study-publication-v1.json \
  --study atomic-subject-asv6.10-test-v1 \
  --output target/atomic-subject-results
```

Pass the original repository root as the source argument. All declared files
must be present with matching hashes, including any source-bound scientific review
state. A clean checkout or compact download alone does not provide that original
layout. Moved files can remain behind links; their complete contents must still
match the declared hashes. This command neither runs models nor changes sources.

Each entry contains `experiment.json`, `inputs.jsonl`, `answers.jsonl`,
`judgments.jsonl` and `results.jsonl`. Shared posts and prompt templates are
referenced within the entry rather than expanding every request. Raw answers
retain their exact strings and hashes; separately parsed answers keep their
source binding. Scientific parameters retain recorded ordering, normalization,
isolation, repeat/reuse policies and execution limits. Credentials, account
locations, private execution identifiers and transport logs are excluded.

The 197 scientific assessment, comparison, measurement and correction records
remain separate from two explicit user rejections. Undecided subjects acquire
no decision; missing reviewer identity stays unknown. Later corrections do not
replace earlier assessments. The failed MPv3.26 attempt retains its outcome
without a credential diagnostic. ASv6.47's sampler retains three reused-answer
references and no new answers. Known pre-ASv6.100 subject outputs stay deprecated
historical evidence; unknown lineage stays unknown. Raw posts are not deprecated.

The four previously selected subject studies, ASv6.100's 180 native answers and
its five evaluation documents retain their existing publication links. They are
not duplicated in these 123 entries.

All 85 historical-study, older prompt/title, evaluation and publication-workflow
tests pass:

```bash
cd "$ORACLE_ROOT"
PYTHONPATH=.:sse_multivector python -m unittest \
  sse_multivector.test_historical_study_publication \
  sse_multivector.test_atomic_study_publication \
  sse_multivector.test_historical_study_cli \
  sse_multivector.test_subject_goal_publication \
  sse_multivector.test_mask_goal_publication \
  sse_multivector.test_prompt_study_publication \
  sse_multivector.test_title_study_publication \
  sse_multivector.test_evaluation_publication \
  sse_multivector.test_publication_workflow
```

All 123 real-file commands also pass under a 512 MiB worker address-space limit.
Their 615 files total 14,109,305 bytes (2,899,941 bytes with gzip level 6).
Every declared source and payload hash matches. All 3,266 selected original
files retain their bytes, hashes, modes and modification times. This verifies
the selected saved evidence; it does not re-evaluate scientific quality or
complete the final publication privacy review.

### Historical title study checks

The 33 title/description publication groups contain 506 saved answers and 24
separate failed attempts, with three final 61-group title sets. All 183 selected
titles bind to their chosen saved answers, including 32 reused answers from
other selected studies. Published inputs preserve original order, exact masks
and the recorded deduplication or hashtag condition. Reconstructing the requests
from those inputs and exported templates reproduces all 506 request hashes;
the raw answer strings also reproduce their saved hashes. These are mechanical
checks, not new assessments or approval of the titles.

The maintained selection contains only paths, hashes and input/template bindings.
Frozen parameters retain their scientific fields; private execution and billing
containers are excluded. Unknown fields fail explicitly. A selected-title view
reuses an input reference only when its exact masks match the chosen call.
Otherwise its original evidence remains present. Comments without an author or
decision field remain unattributed comments. Unresolved external file references
are explicitly identified; they are not guessed from a shared filename.

All 62 title-study, projection, mask-input, older prompt-study, evaluation-export
and publication-workflow tests pass:

```bash
cd "$ORACLE_ROOT"
PYTHONPATH=.:sse_multivector python -m unittest \
  sse_multivector.test_title_study_publication \
  sse_multivector.test_title_study_records \
  sse_multivector.test_category_title_inputs \
  sse_multivector.test_prompt_study_publication \
  sse_multivector.test_evaluation_publication \
  sse_multivector.test_publication_workflow
```

All 33 real-file exports also pass with a 512 MiB address-space limit and about
31 MiB maximum resident memory. The 2,262 input/receipt/source files read by
these exports retain their bytes, modes and modification times. No new model
answers, user decisions or semantic judgments were created. All output hashes
and sizes are listed in [publication files](publication-files.csv).

### SSE representation study checks

These 11 historical studies used manually supplied text spans to test SSE
representations. Their original final comparisons, recorded outcomes, fixed
inputs and encoder settings are selected under `representations/`. No automatic
subject or mask generation was involved; AS version classification does not
apply.

A publisher with the original saved study layout can prepare these files
without inference:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-numerical-results \
  sse_multivector/mask-fidelity-location-v1 \
  --family representation \
  --output target/representation-results
```

Use the study directory containing `experiment.json` and `worker-input.json`,
rather than its `result/` subdirectory. The context-counterfactual study instead
uses `sse_multivector/context-counterfactual-result-v1` and its original sibling
fixture and source-note files. A clean checkout or selected download alone does
not contain the complete original source layout.

The three output files are `experiment.json`, `inputs.jsonl` and `results.jsonl`.
They retain native result values, including failed scientific comparisons,
without rerunning the encoder or assessing the results again. The compound
study's complete cosine table is a required measured result; raw vectors,
token-index diagnostics and duplicate CSV views are excluded.

The context fixture hash is checked against the saved records. Its worker-request
hash is checked for agreement across the analysis, manifest and receipt; the
missing compiled request bytes prevent recomputing that hash. Recorded review
and authorization fields describe the saved study and grant no new approval.

All 40 representation, numerical-publication and publication-workflow tests pass:

```bash
cd "$ORACLE_ROOT"
PYTHONPATH=.:sse_multivector python -m unittest \
  sse_multivector.test_representation_publication \
  sse_multivector.test_numerical_publication \
  sse_multivector.test_publication_workflow
```

The 11 real-file publication commands also pass under a 512 MiB address-space
limit, with about 28 MiB peak resident memory. The selected 33 files total
880,381 bytes (146,702 bytes with gzip level 6). Independent checks match every
native analysis, proposal/fixture and saved worker input, all 381 encoded row
identities and all 2,025 compound-matrix cells. All 99 original files retain
their bytes, hashes, modes and modification times. No encoder or model ran.
