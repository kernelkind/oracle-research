# Inspect and repeat the experiments

Start by browsing a saved hierarchy. To try the generation process, prepare one
recorded post before attempting a whole corpus. The examples below use the
current publication code and the recorded inputs; they keep new outputs separate
from the original results.

**Downloads are not available yet.** The
[dataset commands](#verify-and-restore-the-dataset) verify
and restore the selected files listed in [dataset manifest](downloads.md#dataset-manifest).
Restoration recovers original compact exports, not complete native experiment
directories. Browsing, HR36 preparation and training-input checks
use restored compact files. Hosted reader workflows and a fresh GPU training
run have not been tested for this guide.

To generate and browse a new hierarchy from your own posts, use the
[generation guide](../generate-hierarchy.md). Its complete 12-post workflow
passed in a fresh Linux VM; it does not require these historical files.

| What you want to do | Example | Model work |
| --- | --- | --- |
| Explore a completed hierarchy | Browse HR39's saved topics and posts | None |
| Try subject identification | Run ASv6.100 on one original HR36 post | Fresh language-model inference |
| Repeat hierarchy construction | Use HR36's 1,000 saved subject outputs with HiGen V5.3 | New definition writing, local SSE encoding and clustering |
| Examine fine-tuning results | Read the seven-version L1 comparison | None |
| Use a subject adapter | Extract subjects from one post with a saved checkpoint | Local GPU inference |
| Repeat subject training | Check data/order, run a saved pilot recipe, then optionally continue your own Qwen run | GPU training |

## Obtain the inputs

From the directory containing the Oracle checkout, start a Bash shell:

```bash
cd oracle-mvp
export ORACLE_ROOT="$PWD"
export RELEASE_ROOT="$ORACLE_ROOT/target/reproduction/release"
mkdir -p "$RELEASE_ROOT" target/reproduction/history
```

The reader examples restore their required files from `target/publication-dataset`,
the prepared local collection or its eventual downloaded copy. Restoration
verifies the file hashes. No original native run directory or full research
corpus is needed for these examples. Training also requires upstream base-model
weights. Model downloads and build dependencies are additional.

## Browse HR39 without running models

Use Linux, Python 3.13, the matching `experiment-runner` checkout and the
repository's Nix build environment. Install the runner's Python package and
build the viewer. No account login, language model or encoder checkpoint is
needed:

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
nix --extra-experimental-features 'nix-command flakes' develop \
  --command cargo build --locked --release --jobs 1 \
  --bin sse-subject-navigation
```

Start from `target/publication-dataset`, the prepared local collection or its
eventual downloaded copy. Restore `hierarchies/HR39` and `inputs/used-posts`
into separate new directories. Each restore verifies its file hashes:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset --publication hierarchies/HR39 \
  --output target/reproduction/hr39
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset --publication inputs/used-posts \
  --output target/reproduction/used-posts
python sse_multivector/experiment.py export-canonical-viewer \
  target/reproduction/hr39 \
  --posts target/reproduction/used-posts/posts.jsonl \
  --output target/reproduction/hr39-viewer
target/release/sse-subject-navigation \
  --categories target/reproduction/hr39-viewer/hierarchy.json \
  target/reproduction/hr39-viewer/notes.json \
  --check
```

`--check` validates the saved viewer data without opening an interactive terminal.
Then browse it:

```bash
cd "$ORACLE_ROOT"
target/release/sse-subject-navigation \
  --categories target/reproduction/hr39-viewer/hierarchy.json \
  target/reproduction/hr39-viewer/notes.json
```

This opens the existing result: six root choices representing 2,693 of the 5,000
input notes. It does not regenerate the hierarchy or establish that its topic
choices are semantically correct. The [HR39 record](hierarchy/runs.md#hr39--automatically-sampled-5000-note-higen-v53)
describes the run and its review status.

`export-canonical-viewer --posts` checks both payload hashes in `experiment.json`,
the graph and its counts, and the presence of each referenced post exactly once.
The post file may be JSONL records with `note_id` and `text`, or JSON containing
a `notes` array. It is streamed; only represented posts are retained. Viewer
files preserve root and child order, shared branches, definitions and direct
post references, and bind the supplied post text by SHA-256. The source files
are read-only. No construction history, vectors, model responses, signing key
or network access is required. An empty hierarchy has no nodes to browse.

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

Restore HR36's ordered selection and the shared posts, then select its 1,000
posts into a native corpus. This input contains only note IDs and exact post
text, with no saved subject answers. The example prepares the first recorded
HR36 note.

Use an unused `target/hierarchy-example/posts.json` and a new experiment
directory. `prepare-corpus` refuses an existing output file:

```bash
cd "$ORACLE_ROOT"
export CASE_ID=e975bb986241e25414d5aaa81bd9464ed667fce43d81093fbd88e94c1b879d63
(
  set -e
  python sse_multivector/experiment.py restore-publication-dataset \
    target/publication-dataset --publication hierarchies/HR36 \
    --output target/reproduction/AS-inputs/selection
  python sse_multivector/experiment.py restore-publication-dataset \
    target/publication-dataset --publication inputs/used-posts \
    --output target/reproduction/AS-inputs/posts
  python sse_multivector/experiment.py prepare-corpus \
    --posts target/reproduction/AS-inputs/posts/posts.jsonl \
    --note-ids target/reproduction/AS-inputs/selection/input-note-ids.txt \
    --output target/hierarchy-example/posts.json
  python sse_multivector/experiment.py prepare target/reproduction/AS-one \
    --spec examples/hierarchy-v5.3/subjects.spec.json \
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

This skips subject extraction and uses the saved ASv6.100 subject trees for
HR36's 1,000 posts. These include all 25,258 entries: Bootstrap uses each of the
5,378 top-level subjects together with its full original local tree and post.
The starting-subject bundle is about 4.76 MiB; post text is shared separately.
The run performs new definition writing and numerical construction.
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
(
  set -e
  python sse_multivector/experiment.py restore-publication-dataset \
    target/publication-dataset --publication hierarchies/HR36 \
    --output target/reproduction/HR36-inputs/selection
  python sse_multivector/experiment.py restore-publication-dataset \
    target/publication-dataset --publication inputs/used-posts \
    --output target/reproduction/HR36-inputs/posts
  python sse_multivector/experiment.py restore-publication-dataset \
    target/publication-dataset --publication inputs/hr36-subjects \
    --output target/reproduction/HR36-inputs/subjects
  python sse_multivector/experiment.py prepare-corpus \
    --posts target/reproduction/HR36-inputs/posts/posts.jsonl \
    --note-ids target/reproduction/HR36-inputs/selection/input-note-ids.txt \
    --subjects target/reproduction/HR36-inputs/subjects \
    --output target/hierarchy-example/subject-collection/subjects.json
  nix --extra-experimental-features 'nix-command flakes' develop \
    --command cargo build --locked --release --jobs 1 \
    --bin fine-segmentation-candidate --bin sse-subject-navigation
  python sse_multivector/experiment.py prepare-hierarchy target/reproduction/HR36 \
    --spec examples/hierarchy-v5.3/hierarchy.spec.json \
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
accepts an original saved hierarchy directory containing `state.json`; compact
exports and starting-subject inputs alone do not include that state.

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

### Verify and restore the dataset

The dataset's `dataset.json` identifies the physical files, shared values and
exact compact results recoverable by restoration. [Publications](publications.csv)
connects each bundle ID to its study and recorded outcome.

Verify the complete downloaded collection:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py verify-publication-dataset \
  target/publication-dataset
```

To restore one selected bundle into a new directory:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset \
  --publication historical-studies/crec-119-500-note-vector-v1 \
  --output target/reproduction/crec-119-vector-v1
```

Omit `--publication` to restore every included bundle. A single-bundle restore
needs `dataset.json`, that bundle's files and its referenced shared files; it
checks their hashes without requiring unrelated bundles. Whole-dataset
verification requires every physical file. Output directories must be new.

Restoration recovers compact inputs and results. It does not reconstruct native
plans, execution logs or receipt directories for the original `show`, `review`
and native `verify` commands. The [format reference](downloads.md#automated-outputs)
describes the retained fields. The exporters' maintained selection specifications
remain beside the publication code; preparing the collection from private
originals is separate from reading it.

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

### Source removed from the current tree

The cleanup preserves earlier source at commit
`03bd9e4595fbbf6be18cd08e7d273e69ff563a9b`. Original paths include `gte/`,
`topic_map/`, `sse_multivector/hierarchy-runs/` and the study-specific launchers.
For example, inspect a former configuration with:

```bash
cd "$ORACLE_ROOT"
git show 03bd9e4595fbbf6be18cd08e7d273e69ff563a9b:sse_multivector/hierarchy-runs/hr39/hierarchy.spec.json
```

This is the later source copy preserved before tip cleanup, not proof that its
bytes produced an original experiment. Use the recorded producer revision and
hashes where available. Some records have only a path/hash or an unresolved
revision; the [source limits](open-items.md#source-versions) remain explicit.

## Inspect the fine-tune comparison

The current comparison evaluates the roots of each post's subject hierarchy
(L1) on the same 200 test notes, across seven model/checkpoint combinations.
The [research record](subject-extraction/fine-tuning.md#l1-only-test-results-october-15)
defines correctness and both completeness measures.

Use the runner's Python environment from above to restore this two-file bundle
from `target/publication-dataset`. Choose a new output directory. Restoration
checks its file hashes; printing the saved table uses only Python's standard
library. No model runtime or login is needed:

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset \
  --publication evaluations/qwen-continuation-grading-v1-analysis-00a437b45662 \
  --output target/reproduction/l1-comparison
export L1_RESULTS="$ORACLE_ROOT/target/reproduction/l1-comparison"
python3 - <<'PY'
import json
import os
from pathlib import Path

comparison = json.loads((Path(os.environ['L1_RESULTS']) / 'experiment.json').read_text())
if comparison['format'] != 'evaluation-comparison-publication-v1':
    raise SystemExit('Expected a published evaluation comparison.')
print('Version                 Correctness  All roots  Required roots  Invalid')
for name, result in comparison['models'].items():
    s = result['stats']
    print(f"{name:23} {s['correctness_percent']:10.2f}% "
          f"{s['all_root_completeness_percent']:9.2f}% "
          f"{s['required_root_completeness_percent']:14.2f}% "
          f"{s['invalid_outputs']:8}")
PY
```

This displays the recorded totals in `experiment.json`, which also retains model
versions, scoring definitions and source hashes. `results.jsonl` contains 1,400
per-note records: 200 for each of the seven versions, including score fractions
and invalid-output flags. Reading the table does not reapply semantic judgments
or rerun the original verification. The Qwen pass-2 test collection remains
sealed and is not part of this comparison.

The [adapter inventory](models.csv) identifies all 17 checkpoints, their pinned
base-model revisions and associated training manifests. Inference requires an
adapter's weights/configuration and its matching base model. Resuming training
also requires its optimizer/training state and the original prepared dataset.
These model files are separate from the compact comparison bundle.
The [publication plan](downloads.md#corpora-and-fine-tunes) includes all 17
evaluated adapters on Hugging Face, with prepared training data and settings.
Optimizer state remains outside that plan; resuming an exact training state
requires additional local artifacts.
The inventory still lists all candidates; these are not available downloads.

The sections below provide training-input checks and local GPU commands.
For evaluation, `compare-distillation-grades` compares automated and audited
full-hierarchy grades, and `run-distillation-automatic-grading` can make new model
calls. Neither command computes this saved L1 table. The historical
[training runbook](subject-extraction/fine-tuning.md) records the original
hardware, qualification and results.

## Prepare the fine-tuning inputs

Start here for training. Use the Python environment from the
earlier examples and runner commit `140fa38` or later. That version restores
directories whose metadata is nested, as it is for these inputs.

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset --publication inputs/prepared-training \
  --output target/reproduction/subject-training
for student in qwen gemma-dense gemma-moe; do
  python -m sse_multivector.distillation_run \
    "sse_multivector/distillation/subject-pilot-${student}-v1.json" \
    --output "target/reproduction/${student}-plan" --through plan
done
```

This checks all four prepared file hashes, the ordered 1,000/100/200 split,
author/content separation, the full ASv6.100 instruction and saved teacher
targets. It writes `input-check.json` and `training-plan.json` for each recipe.
Each first pass uses all 1,000 training notes once, shuffling only within its
200-note checkpoint blocks, with eight examples per update. The loader reads
the published metadata directly; it does not fabricate a historical manifest.

`--through plan` imports no model runtime, downloads no weights and performs no
tokenization, training or inference. It is an input check, not a CUDA or memory
qualification. Existing plan destinations are refused.

## Set up the GPU runtime

Adapter inference and training use the same pinned runtime. The instructions
below load an unquantized BF16 base model on one CUDA GPU. The original work
used 96 GB GPUs; smaller-memory and quantized recipes have not been validated.
The adapter download is only part of the model: the base weights, host memory
during loading, and generation cache also need space.

On your GPU host, use a clean checkout and configure
[Docker NVIDIA GPU access](https://docs.docker.com/engine/containers/gpu/).
Build the Dockerfile's pinned runtime stage using
[`--target`](https://docs.docker.com/build/building/multi-stage/#stop-at-a-specific-build-stage).
It supplies the recorded Python/CUDA packages without requiring the private
deployment package. The image and base-model downloads need substantial storage
beyond the research dataset. The shell function below runs Python in that
runtime with the source and model-cache mounts:

```bash
cd "$ORACLE_ROOT"
docker build --target runtime \
  --file sse_multivector/distillation/Dockerfile \
  --tag oracle-subject-training .
mkdir -p target/subject-model-cache
distillation_python() {
  docker run --rm --interactive --gpus all --entrypoint python \
    --mount "type=bind,src=$ORACLE_ROOT,dst=/work" \
    --mount "type=bind,src=$EXPERIMENT_RUNNER_ROOT,dst=/runner,readonly" \
    --mount "type=bind,src=$ORACLE_ROOT/target/subject-model-cache,dst=/model-cache" \
    --env EXPERIMENT_RUNNER_ROOT=/runner --env HF_HOME=/model-cache \
    --workdir /work oracle-subject-training "$@"
}
```

Keep this Bash shell open for the examples below. Gated base models require
your own upstream access. The model cache and generated training state are
outside the publication dataset.

## Use a subject adapter

These adapters identify subjects within individual posts. Building the corpus's
browsable hierarchy is a separate step in the [generation guide](../generate-hierarchy.md).
For inference, you need the selected adapter's `adapter_model.safetensors` and
`adapter_config.json`, its matching base model, and the **ASv6.100** instruction.
You do not need the prepared training dataset or optimizer state.

**Adapter download links are pending.** Once available, download one checkpoint's
two files into a local directory; the example uses
`target/reproduction/adapters/qwen-checkpoint-3000/`. Match its identity and hashes
to [models.csv](models.csv) and the published
`inputs/adapter-hashes/adapters.jsonl`. Use the matching configuration below;
each pins the original base-model and tokenizer revision.

| Adapter family | Configuration in `sse_multivector/distillation/` | Checkpoints |
| --- | --- | --- |
| Qwen3.8-27B | `subject-pilot-qwen-v1.json` | 200, 400, 600, 800, 1000, 2000, 3000 |
| Gemma 4 31B | `subject-pilot-gemma-dense-v1.json` | 200, 400, 600, 800, 1000 |
| Gemma 4 26B-A4B | `subject-pilot-gemma-moe-v1.json` | 200, 400, 600, 800, 1000 |

Checkpoint numbers count training-note uses; Qwen's 2000 and 3000 checkpoints
repeat the same 1,000 training notes. Publishing these checkpoints does not
designate one as production-approved.

Set up the [GPU runtime](#set-up-the-gpu-runtime), then put one post's exact
UTF-8 text in `target/reproduction/post.txt`. The following example uses Qwen's
checkpoint 3000. It calls the existing loader, adapter verification, generation
and subject parser in
[distillation_run.py](../../sse_multivector/distillation_run.py):

```bash
cd "$ORACLE_ROOT"
distillation_python - <<'PY'
from pathlib import Path
from transformers import AutoTokenizer
from sse_multivector.distillation_run import (
    generate, load_model, parse_subjects, read_json, verify_adapter,
)

config = read_json("sse_multivector/distillation/subject-pilot-qwen-v1.json")
adapter = Path("target/reproduction/adapters/qwen-checkpoint-3000")
instruction = Path("sse_multivector/subject-prompt-goal-v1/asv6.100/ASv6.100.md").read_text().rstrip()
post = Path("target/reproduction/post.txt").read_text(encoding="utf-8")
messages = [{"role": "user", "content": instruction + "\n\n<post>\n" + post + "\n</post>"}]

tokenizer = AutoTokenizer.from_pretrained(
    config["model"], revision=config["revision"], trust_remote_code=False,
)
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token
model = load_model(config, adapter)
verify_adapter(model, adapter)
model = model.merge_and_unload(safe_merge=True)
answer = generate(model, tokenizer, messages, config)
print(answer["raw"], flush=True)
if answer["truncated"]:
    raise ValueError("Subject answer reached its output limit without EOS")
parse_subjects(answer["raw"])
PY
```

The loader applies the pinned base revision before loading the adapter. As in
the original evaluation, the example verifies the loaded adapter and
[merges it into the in-memory base](https://huggingface.co/docs/peft/v0.21.0/package_reference/lora#merge-lora-weights-into-the-base-model).
It leaves the downloaded files unchanged. Generation uses the native chat
template with thinking off, greedy decoding, a 20,480-token context and up to
10,240 new tokens. Inputs that cannot fit with that output allowance are refused.
The full **ASv6.100** instruction matches the one used in training.

The printed answer contains `subjects`, whose entries have `number`, `context`
and `subject` fields. A truncated or malformed answer raises an error after
printing the original text; parsing does not establish semantic correctness.
For another checkpoint, change the adapter directory and use its family's
configuration from the table. The configuration's training/data fields are not
used by these inference calls. This example has been checked against the
existing code and for syntax; a fresh GPU execution remains untested.

## Run subject fine-tuning

These experiments train language models to produce ASv6.100 subject hierarchies;
they do not train the SSE encoder. The maintained configurations preserve the
saved model revisions and pilot settings:

| Configuration | Base model | First-pass checkpoints |
| --- | --- | --- |
| `subject-pilot-qwen-v1.json` | Qwen3.8-27B | 200, 400, 600, 800, 1,000 |
| `subject-pilot-gemma-dense-v1.json` | Gemma 4 31B | 200, 400, 600, 800, 1,000 |
| `subject-pilot-gemma-moe-v1.json` | Gemma 4 26B-A4B | 200, 400, 600, 800, 1,000 |

All use thinking off, answer-only loss, constant learning rate 0.0001, LoRA
rank 16/alpha 32, 20,480-token context and a 10,240-token generation allowance.
Gemma MoE additionally adapts packed expert weights at rank 2/alpha 32. See the
configurations for exact target modules and batching budgets.

Restore the [fine-tuning inputs](#prepare-the-fine-tuning-inputs) and set up the
[GPU runtime](#set-up-the-gpu-runtime). Preflight downloads the pinned tokenizer
and checks actual lengths and answer-only tokenization without loading model
weights:

```bash
cd "$ORACLE_ROOT"
distillation_python -m sse_multivector.distillation_run \
  sse_multivector/distillation/subject-pilot-qwen-v1.json \
  --output target/reproduction/qwen-run --through preflight
```

To run the complete Qwen first pass:

```bash
cd "$ORACLE_ROOT"
distillation_python -m sse_multivector.distillation_run \
  sse_multivector/distillation/subject-pilot-qwen-v1.json \
  --output target/reproduction/qwen-run --through report
```

This loads the pinned base, saves untuned validation/test answers, trains through
five milestones and evaluates each checkpoint on the 100 validation notes. It
also saves the final checkpoint's 200 test answers. Saved invalid answers remain
measured failures. Resume with the same configuration and output path; native
seals and state checks remain in force. For a Gemma pilot, use its configuration
and a separate run directory.

After **your own first pass completes**, repeat Qwen's two additional passes by
binding a configuration to that run's sealed checkpoint. Keep the same container
mounts so saved paths remain valid:

```bash
cd "$ORACLE_ROOT"
distillation_python -m sse_multivector.distillation_run \
  --prepare-continuation target/reproduction/qwen-run \
  --data target/reproduction/subject-training \
  --output target/reproduction/qwen-continuation.json
distillation_python -m sse_multivector.distillation_run \
  target/reproduction/qwen-continuation.json \
  --output target/reproduction/qwen-continuation-plan --through plan
distillation_python -m sse_multivector.distillation_run \
  target/reproduction/qwen-continuation.json \
  --output target/reproduction/qwen-continuation-run --through report
```

This preserves the parent optimizer and training order, then adds two full
passes over the same notes, ending at 2,000 and 3,000 total note uses. It reuses
your saved baselines. Public adapter weights alone cannot resume the original
research checkpoint because its optimizer state is not included. New GPU
results need not match historical answers or scores. The offline checks above
passed; these public GPU commands have not been run as a fresh end-to-end test.

## Other experiments and moved files

The [study index](experiments.csv) contains 2,488 selected entries: native prompt
preparations, official hierarchy runs, training runs, historical collections
and the four located historical subject-prompt studies.
It records saved plan identities and prompt/model settings.
[Publications](publications.csv) connects them to the exported results;
[dataset manifest](downloads.md#dataset-manifest) lists their exact files and hashes.
Structured exports record their versions and bindings in `experiment.json`;
the original Markdown documents use direct source hashes.

The index covers selected studies, rather than internal jobs, cache warmups or
whole original workspaces. [Evidence limits](open-items.md) distinguish available
results from missing historical inputs and native receipt packages.

Outputs derived from subjects older than **ASv6.100** are historical evidence,
including their downstream hierarchies and evaluations. They are not current
pipeline inputs or validation. Original source posts remain usable.

## What has been tested

The compact HR36 examples were checked on **2026-10-20** in an isolated source
copy. The reader processes could not read the original research inputs or
account credential files, and Python network access was blocked. Restoration,
post selection, the one-case ASv6.100 preparation and full HR36 preparation all
passed. All 1,000 post texts, 25,258 subject entries and their order match the
original corpus. All 5,378 Bootstrap inputs match the earlier preparation from
that full corpus; teacher prompt bytes and model settings also match. The 61
empty subject trees remain present. These checks stop before inference, encoding
or clustering; they do not replay HR36's final result. The Rust binary was copied
from the earlier build. All 33 relevant corpus, publication and provenance tests
pass, including a bounded-memory corpus-selection regression.

The compact fine-tune comparison was checked on **2026-10-20**: restoration
verified both files, and the documented display ran with original-file access
and network connections blocked. All seven rows match the original recorded
totals and the means of their 200 published per-note scores. This checks saved
arithmetic, not the underlying semantic judgments. No model requests ran.

The complete generation guide also passed in a fresh Debian 13 VM with
8 GiB RAM and four CPU cores, from installation through unsigned export and
interactive browsing of a 12-post hierarchy. Authentication renewal and later
revocation were checked there; offline export and browsing then worked without
credentials. This validates a small reader workflow, not semantic quality,
large-corpus scalability or reproduction of a historical model draw.

Hosted download testing and fresh GPU training/adapter-inference runs remain
unverified. Some historical entry points require original files outside the
compact selection; see [replay limits](open-items.md#source-versions).

The dataset checks verify file identities and restored bytes. They do not
reevaluate semantic judgments or prove exact replay of historical model answers.
See [evidence and reproduction limits](open-items.md) for missing input versions,
unknown execution or usage, and outcomes that remain scientifically unresolved.
