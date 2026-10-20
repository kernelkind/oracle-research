# Generate a hierarchy

This guide runs HiGen V5.3 on your own posts, from subject extraction to an
interactive hierarchy. It uses the existing experiment runner to save inputs,
model responses and resumable construction state. Previous research datasets
and experiment outputs are not required.

To use recorded research inputs or browse a saved result, see the
[experiment reproduction guide](experiments/reproduce.md).

The language-model steps use an external subscription or API account. SSE
encoding and numerical construction run locally on CPU. Fully local generation
and million-note scalability remain project goals. Start with a few dozen posts:
the current numerical implementation includes quadratic distance matrices, and
there is no established minimum-RAM specification for this workflow.

The commands and configurations below are provided for publication preparation.
A complete fresh-machine run with the public authentication route has not yet
been validated. The final runner submodule URL and commit will be recorded after
publication history cleanup.

## 1. Install the runtime

Use Linux with Python 3.13, Node.js 24 or later, and Nix for the repository's
pinned Rust/C build environment. Python's `venv` and `pip`, `curl`, and
`sha256sum` are also needed. The Torch, Transformers and Tokenizers versions below
match the recorded CPU runtime; the guide does not require a GPU or a container.

Place the matching `experiment-runner` source checkout either inside Oracle as
`experiment-runner/` or alongside it as `../experiment-runner/`. An explicit
`EXPERIMENT_RUNNER_ROOT` selects a different checkout. The publication submodule
will eventually supply this pairing; installing an arbitrary latest runner is
not a reproducibility guarantee.

From the directory containing your Oracle checkout, run this setup in Bash.
Keep this shell open for the following steps:

```bash
cd oracle-mvp
export ORACLE_ROOT="$PWD"
if [ -z "${EXPERIMENT_RUNNER_ROOT:-}" ]; then
  if [ -f experiment-runner/experiment_runner/__init__.py ]; then
    export EXPERIMENT_RUNNER_ROOT="$ORACLE_ROOT/experiment-runner"
  else
    export EXPERIMENT_RUNNER_ROOT="$(realpath ../experiment-runner)"
  fi
fi
mkdir -p target/hierarchy-example/models target/hierarchy-example/history
python3.13 -m venv target/hierarchy-env
source target/hierarchy-env/bin/activate
python -m pip install torch==2.13.0 \
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers==4.57.1 tokenizers==0.22.2 \
  -e "$EXPERIMENT_RUNNER_ROOT"
npm --prefix "$EXPERIMENT_RUNNER_ROOT/experiment_runner/frontier_runner" \
  ci --ignore-scripts --no-audit --no-fund
nix develop --command cargo build --locked --release \
  --bin fine-segmentation-candidate --bin sse-subject-navigation
python sse_multivector/experiment.py --help
```

The coordinating Python process loads SSE itself. Running the CLI from another
Python environment will not use the packages installed above. The worker loads
the supplied `tokenizer.json` with the fast tokenizer; no separate SentencePiece
Python package or tokenizer conversion is needed.

## 2. Authenticate

For a machine without Anvil's account service, explicitly select direct
authentication and log in through pi-ai:

```bash
cd "$ORACLE_ROOT"
export EXPERIMENT_RUNNER_AUTH=direct
./sse_multivector/run-model.sh login openai-codex
```

The login command prints the instructions for completing subscription login.
Credentials are saved outside the repository at
`$XDG_CONFIG_HOME/experiment-runner/auth.json`, or
`~/.config/experiment-runner/auth.json` when `XDG_CONFIG_HOME` is unset.
`EXPERIMENT_RUNNER_AUTH_FILE` can select another file outside the repository.
Do not put credentials in the example JSON files.

On Anvil, leave `EXPERIMENT_RUNNER_AUTH` unset to continue using the selected
`agent-account` account and the existing credential service. Direct mode is an
explicit alternative; neither mode falls back to the other.

To use OpenRouter instead, complete its login:

```bash
cd "$ORACLE_ROOT"
export EXPERIMENT_RUNNER_AUTH=direct
./sse_multivector/run-model.sh login openrouter
```

Alternatively, direct OpenRouter requests accept `OPENROUTER_API_KEY` when no
credential is stored. A saved credential takes precedence. Before preparing
anything, change `runner.provider` to `openrouter` and `runner.model` to the
chosen OpenRouter model ID in **all three** language-model specs listed below.
Check that the model accepts the selected reasoning effort, and remove
`runner.prompt_cache` from all three specs: that prefix-cache setting is
subscription-SSE-only. This changes the model used by the experiment and is
not an exact repetition of the subscription runs.

## 3. Obtain the encoder files

Download **`subencoder_st5_base.ckpt`** from the
[authors' checkpoint folder](https://drive.google.com/drive/folders/179Ga1WElV3yjxIA5MRk9lxRo5b9ImDqN),
linked by the [official SSE repository](https://github.com/schen149/sub-sentence-encoder#model-checkpoint).
The [specific checkpoint](https://drive.google.com/file/d/1_6cBPKT_RydY0wMPDm_Sde7FRY-kDmzP/view)
is 1,329,859,448 bytes. Save it at
`target/hierarchy-example/models/subencoder_st5_base.ckpt`.

Verify it against the file used by the recorded experiments:

```bash
cd "$ORACLE_ROOT"
sha256sum --check <<'SHA256'
ef9d34ca38f04fc30b2879fa365d07cd8264dc2cd3f5c24084533fe18535ad1d  target/hierarchy-example/models/subencoder_st5_base.ckpt
SHA256
```

The worker also needs the tokenizer and model configuration from
[`sentence-transformers/sentence-t5-base`, revision `fc5d4628481afbbaaacd7af6bb07cf9d3865f781`](https://huggingface.co/sentence-transformers/sentence-t5-base/tree/fc5d4628481afbbaaacd7af6bb07cf9d3865f781).
Its learned weights come from the SSE checkpoint, so downloading the separate
Sentence-T5 weight files is unnecessary. Obtain these five files only:

```bash
cd "$ORACLE_ROOT"
model_dir=target/hierarchy-example/models/sentence-t5-base
model_url=https://huggingface.co/sentence-transformers/sentence-t5-base
model_revision=fc5d4628481afbbaaacd7af6bb07cf9d3865f781
mkdir -p "$model_dir"
for model_file in config.json special_tokens_map.json spiece.model \
  tokenizer.json tokenizer_config.json; do
  curl --fail --location \
    "$model_url/resolve/$model_revision/$model_file" \
    --output "$model_dir/$model_file" || break
done
python - <<'PY'
from pathlib import Path
from sse_multivector.worker import canonical_tree_sha256

expected = 'bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d'
actual = canonical_tree_sha256(Path('target/hierarchy-example/models/sentence-t5-base'))
if actual != expected:
    raise SystemExit(f'Tokenizer/configuration mismatch: {actual}; expected {expected}')
print('Tokenizer/configuration verified')
PY
```

This five-file download was checked against the recorded tree hash during
publication preparation. No checkpoint download or encoder inference was
performed in that check. Extra files, cache metadata or symlinks in this model
directory change or invalidate its tree hash.

## 4. Supply posts and review the configuration

Save your posts as `target/hierarchy-example/posts.json`. The input contains
stable, unique post IDs and original text:

```json
{
  "schema_version": 1,
  "notes": [
    {
      "note_id": "original-nostr-event-id",
      "text": "The complete original post text."
    }
  ]
}
```

Use the event's `id` as `note_id` and its `content` as `text` when exporting
from Nostr. Raw relay event envelopes are not this input format. This guide
starts from an exported file; the generator does not fetch posts from relays.
Choose several posts with enough shared subject matter to form groups. One
post is useful for checking input format, but not for evaluating discovery.

The maintained [example configurations](../sse_multivector/examples/hierarchy-v5.3/)
use paths relative to their own files:

| File | Purpose |
| --- | --- |
| `subjects.spec.json` | Extract subjects with **ASv6.100** |
| `bootstrap.spec.json` | Define original subjects with **Hierarchy-bootstrap-v133** |
| `consolidation.spec.json` | Define groups with **Hierarchy-consolidated-grouped-v1** |
| `worker-config.json` | Select the local SSE checkpoint, tokenizer/configuration, hashes and CPU batching |
| `hierarchy.spec.json` | Select HiGen V5.3, the collected subjects and the numerical executable |

These are new input configurations, separate from the historical run records.
They use `gpt-6.1-sol`, medium reasoning and SSE transport for the language-model
steps, matching the recorded HR36 settings. Review these choices before
preparation. Omitting `note_ids` from the hierarchy spec selects every post in
the collected input; an explicit list selects a subset. The selected IDs are
frozen when the hierarchy is prepared.

`worker-config.json` is a template. Its request path, request hash and output
path are replaced for each generated encoder job. The `container_image` value
is retained historical artifact metadata; it does not launch a container or
establish the runtime used by a new run. Worker receipts record the actual
local Python, Torch, Transformers and Tokenizers versions.

Keep the source files, configurations, code and model files at their original
paths after preparation. Saved runs verify their frozen sources. Use a fresh
output directory when changing inputs or settings; do not edit saved manifests
or historical experiment specifications.

## 5. Extract subjects

Prepare the subject requests without inference, then inspect them:

```bash
cd "$ORACLE_ROOT"
source target/hierarchy-env/bin/activate
python sse_multivector/experiment.py prepare \
  target/hierarchy-example/subjects \
  --spec sse_multivector/examples/hierarchy-v5.3/subjects.spec.json \
  --history-root target/hierarchy-example/history
python sse_multivector/experiment.py show target/hierarchy-example/subjects
```

The next command sends model requests using your selected account. Subscription
limits or API charges apply. The runner's shared queue handles dispatch and
retries; there is no default model-attempt cap.

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py run target/hierarchy-example/subjects
python sse_multivector/experiment.py show target/hierarchy-example/subjects
```

Once every case has a valid saved answer, collect them into the hierarchy input:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py collect \
  target/hierarchy-example/subjects \
  --output target/hierarchy-example/subject-collection
```

Collection makes no model calls. It writes `subjects.json` and
`provenance.json`, retaining original post IDs and text and checking the saved
answers against their sources. Posts with valid empty subject answers are
retained. HiGen cannot construct a hierarchy if the whole input has no usable
subjects.

## 6. Construct the hierarchy

Prepare the frozen hierarchy state without inference:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py prepare-hierarchy \
  target/hierarchy-example/hierarchy \
  --spec sse_multivector/examples/hierarchy-v5.3/hierarchy.spec.json \
  --history-root target/hierarchy-example/history
```

Then run construction. This step sends language-model requests, performs local
SSE encoding and runs numerical clustering:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py run-hierarchy \
  target/hierarchy-example/hierarchy --cpu-workers 1
```

`--cpu-workers 1` limits numerical worker concurrency for this initial run; it
is not a memory limit. Start with the small input before increasing the corpus
size. Completion means construction finished, not that the labels or navigation
have been semantically approved.

If subject extraction or hierarchy construction stops, inspect the reported
failure and resume with the same `run` or `run-hierarchy` command once it is
resolved. Previously saved valid results remain available for reuse. Do not
rerun `prepare` into an existing output directory or delete receipts to force
progress. Invalid answers and changed frozen sources require investigation.

After construction completes or blocks, `run-hierarchy` writes
`target/hierarchy-example/hierarchy/publication/`. It also attempts this export
after failure or interruption, once submitted jobs have stopped. The directory
contains `experiment.json` (settings and outcome), `input-note-ids.txt` (the full
ordered selection) and `hierarchy.jsonl` (the final or last partial unsigned
hierarchy, including definitions). No signing key is needed. The full selection
can contain notes absent from the hierarchy.

To export a saved run without resuming construction, or refresh its results:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-hierarchy-results \
  target/hierarchy-example/hierarchy
```

This makes no model calls and leaves the saved state unchanged. It honors the
native execution lock; unchanged re-exports preserve the files' bytes and
modification times. See the [publication format](experiments/downloads.md#automated-outputs)
for the exported fields and historical provenance limits.

## 7. Export and browse

Export the saved hierarchy and its matching original post text, then validate
the browser inputs without opening a terminal UI:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py export-canonical-viewer \
  target/hierarchy-example/hierarchy \
  --output target/hierarchy-example/viewer
target/release/sse-subject-navigation --categories \
  target/hierarchy-example/viewer/hierarchy.json \
  target/hierarchy-example/viewer/notes.json --check
```

Open the browser from an interactive terminal:

```bash
cd "$ORACLE_ROOT"
target/release/sse-subject-navigation --categories \
  target/hierarchy-example/viewer/hierarchy.json \
  target/hierarchy-example/viewer/notes.json
```

Choose a category to narrow the displayed choices; press `N` to view that
category's notes. Exporting and browsing make no model calls. Keep both viewer
files together: the hierarchy binds the exact `notes.json` bytes by hash, and
the browser does not retrieve missing text from Nostr.

All generated files in this example live under ignored `target/`. Preserve the
source posts, collected subjects, saved experiment history and hierarchy state
if you want to resume or audit the run. The two viewer files are sufficient for
browsing. See [HiGen V5.3](recommendation-engine/hierarchy-generation-v5.md) for
the algorithm and [the runner reference](../sse_multivector/model-runner.md)
for detailed preparation, receipt and recovery behavior.
