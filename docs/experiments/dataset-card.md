---
pretty_name: Oracle Research data
viewer: false
tags:
  - nostr
  - subject-extraction
  - hierarchical-clustering
  - research
---

# Oracle Research data

Inputs and final results from research into content discovery on Nostr through
a subject hierarchy. The hierarchy offers progressively narrower choices so
people can direct their own discovery.

This collection accompanies the [Oracle Research code](https://github.com/kernelkind/oracle-research) and experiment index. It
contains the posts actually used, experiment parameters, generated hierarchies,
prompt answers and evaluation evidence, including unsuccessful and superseded
work.

**Private dataset:** the snapshot is uploaded to
[KernelKind/oracle-research](https://huggingface.co/datasets/KernelKind/oracle-research).
Access currently requires an authorized Hugging Face account; public dataset
release remains pending. Every payload file's remote content identity and size
matches the reviewed local snapshot. A selected six-file download passed native
HR39/post restoration, viewer export and the viewer's `--check` validation.

## Contents

The payload is **844.00 MiB (884,995,321 bytes)** in **9,686 files**.
It contains 2,989 input/result bundles, with repeated content stored once.

| Material | What it provides |
| --- | --- |
| Used source posts | Exact text and note IDs for 10,571 shared posts used in the selected experiments |
| Hierarchies | All 37 official hierarchy outputs and selected historical branches, ordered input selections, settings and recorded outcomes |
| Prompt experiments | Selected inputs, prompt/model settings, final saved answers, failures and recorded reviews |
| Evaluations and numerical studies | Final judgments, scores, measurements, graphs and memberships, with available provenance |
| Fine-tuning inputs | Prepared training data, split/settings records, reference fixtures and hash bindings for all 17 evaluated adapters |

The code repository's [study index](https://github.com/kernelkind/oracle-research/blob/main/docs/experiments/experiments.csv) connects studies to
bundle IDs. Its [bundle catalog](https://github.com/kernelkind/oracle-research/blob/main/docs/experiments/publications.csv) describes the bundles; the
dataset's `publication-dataset/dataset.json` identifies their exact files,
sizes and hashes. The 2,488 study-index entries overlap and are not a count of
independent trials. Reused answers remain identified as reused.

The dataset excludes 196 preparations proven never executed. Three snapshots
with unknown execution status remain included and labeled accordingly.

Full source corpora, intermediate vectors, transport logs, expanded requests,
optimizer state and whole original run directories are outside this selection.
Weights for all 17 evaluated adapters are in the separate
[subject-adapter repository](https://huggingface.co/KernelKind/oracle-subject-adapters).
Upstream base-model weights are additional downloads.

## Download and inspect

Use Linux, Git and Python 3.13. [Oracle Research](https://github.com/kernelkind/oracle-research)
includes [Experiment Runner](https://github.com/kernelkind/experiment-runner) as
a pinned submodule. Clone both with:

```bash
git clone --recurse-submodules https://github.com/kernelkind/oracle-research.git
```

Setup was checked at Oracle commit `20fc5b2b7dcd8b6131d417da1ffb563f69fe0226`
with runner commit `26bc051378b5db6ee4456b5bdaac9554ac1e6bf3`.

Start a Bash shell and keep it open for the following commands. An explicit
`EXPERIMENT_RUNNER_ROOT` can select an existing runner checkout instead of the
submodule. These tools use `publication-env`, separate from the generation
guide's model environment:

```bash
cd oracle-research
export ORACLE_ROOT="$PWD"
if [ -z "${EXPERIMENT_RUNNER_ROOT:-}" ]; then
  git submodule update --init --recursive -- experiment-runner
  export EXPERIMENT_RUNNER_ROOT="$ORACLE_ROOT/experiment-runner"
fi
python3.13 -m venv target/publication-env
source target/publication-env/bin/activate
python -m pip install huggingface_hub==2.2.0 -e "$EXPERIMENT_RUNNER_ROOT"
```

Use the complete payload commit pinned below.
Start with no existing `target/publication-dataset` directory;
downloading another revision does not remove stale files. The command preserves
the `publication-dataset/` folder beneath `target/`:

```bash
cd "$ORACLE_ROOT"
DATASET_REPO='KernelKind/oracle-research'
DATASET_REVISION='439f98b3479559306fda369977a6e9978a7005b2'
hf download "$DATASET_REPO" --repo-type dataset \
  --revision "$DATASET_REVISION" \
  --include 'publication-dataset/**' --local-dir target --max-workers 4
```

The repository card and Hugging Face download metadata stay outside
`target/publication-dataset`. Keep that folder unchanged: verification rejects
extra files and symlinks. The download syntax and metadata placement follow the
[Hugging Face CLI guide](https://huggingface.co/docs/huggingface_hub/guides/cli#download-files).

Check the manifest against this prepared snapshot, then verify the files and
the original compact bytes recoverable from shared content:

```bash
cd "$ORACLE_ROOT"
(
  set -e
  sha256sum --check <<'SHA256'
e517707bced7fb2ab1e50224b9cd96d4596acca4fd9966a503db2fc33eeb87f0  target/publication-dataset/dataset.json
SHA256
  python sse_multivector/experiment.py verify-publication-dataset \
    target/publication-dataset
)
```

The SHA-256 above identifies `dataset.json`; it is separate from the Hugging
Face commit ID used to download the repository.

Hosted checks compared all uploaded dataset files using Git blob hashes or LFS
SHA-256 values. The fresh download contained only `dataset.json`, HR39 and the
used-posts bundle: six files totaling 8,232,565 bytes. Native restoration checked
the original compact bytes, and viewer export plus `--check` passed.

For a first result, restore the saved HR39 hierarchy into a new directory:

```bash
cd "$ORACLE_ROOT"
python sse_multivector/experiment.py restore-publication-dataset \
  target/publication-dataset --publication hierarchies/HR39 \
  --output target/reproduction/hr39
```

This produces `experiment.json`, `hierarchy.jsonl` and `input-note-ids.txt`.
`experiment.json` records the run's parameters, outcome and payload hashes.
The hierarchy is unsigned Nostr-format data for local inspection; reading it
requires no signing key, relay or model inference. The experimental protocol
is intended for local or private testing; please avoid sending these events
to public Nostr relays.

The [reproduction guide](https://github.com/kernelkind/oracle-research/blob/main/docs/experiments/reproduce.md) explains how
to restore the corresponding posts, browse HR39 and inspect the fine-tuning
comparison. It also covers model loading and selected reruns. The
[Notedeck hierarchy interface](https://github.com/kernelkind/notedeck/tree/hierarchies)
provides the graphical browser shown in the project's walkthrough.

## Format and interpretation

This is a collection of different research outputs, rather than a single
tabular training dataset. JSON/JSONL files use format-specific schemas.
Repeated values can appear as `{"$ref":123}`; `shared/` holds their full content.
Use `restore-publication-dataset` before passing a bundle to a reader that
expects its original compact JSON. Restoration checks hashes and expands
references without rerunning an experiment. It does not recreate native plans,
execution logs or receipt directories.

The experiments span changing methods and prompts. Subjects and downstream
results produced before **ASv6.100** are historical evidence; this does not
deprecate the original posts. Unknown provenance remains unknown. A higher
prompt version does not establish approval.

Recorded observations, agent assessments and user judgments remain distinct.
Generated answers and assessments are fallible; successful execution and valid
hashes do not establish semantic quality. Some historical input versions remain
missing, so not every original run can be reproduced exactly. The code
repository's [evidence limits](https://github.com/kernelkind/oracle-research/blob/main/docs/experiments/open-items.md) list the known gaps.

The source posts are public Nostr text, not anonymized text or a representative
sample of the network. The collection supports inspection of the recorded
research; it does not establish fully local hierarchy generation or scalability
to a million notes.

## License and provenance

Original project material uses **GPL-3.0-or-later**, as specified in the code
repository's [LICENSE](https://github.com/kernelkind/oracle-research/blob/main/LICENSE). Third-party Nostr posts and other upstream material
retain their respective rights; this project does not grant a blanket GPL
license over that content. Dataset-wide license metadata is therefore unset.
Source hashes and note IDs are preserved for provenance.
