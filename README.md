# Oracle Research

This project explores a way for people to discover the kinds of Nostr content they want to see.

This repository contains the hierarchy generator, along with the code, prompts and findings from its development.

The approach starts from the idea that people can recognize an interesting direction when presented with meaningful choices. A subject hierarchy offers those choices in a progressively narrowing pattern, helping the person reach the content they’re looking for.

Each choice lets the person direct their own discovery. The goal is to put that control in people’s hands, without predatory algorithms or invasions of privacy.

## Walkthrough

https://github.com/user-attachments/assets/2f8cca89-d52e-4cf6-bd0a-55a24ddb7960

Use the **Hierarchy** column to choose a topic, narrow it down, and view its posts.

The interface uses a [toy hierarchy snapshot protocol](docs/design/nostr-hierarchy-snapshot.md) developed for this prototype. The format is intended for local or private testing, so please avoid publishing its experimental events to public Nostr relays.

The [Notedeck hierarchy interface](https://github.com/kernelkind/notedeck/tree/hierarchies) provides the **Hierarchy** column shown in the walkthrough.

The [generation guide](docs/generate-hierarchy.md) covers terminal browsing and [exporting a completed hierarchy in the toy Nostr format](docs/generate-hierarchy.md#8-export-as-nostr-notes) for local testing.

## Goals

### Hierarchy generation

- Run the complete hierarchy-generation process on consumer-grade hardware, including any required model inference.
- Make zero AI model API calls.
- Scale to corpora exceeding one million notes on consumer-grade hardware.

### The hierarchy

- Help people find notes about any desired topic in the corpus with minimal effort.
- Offer only a few meaningful choices at each step, progressively narrowing within the selected topic.
- Minimize duplicated information among sibling choices.

## Start here

**Current implementation:** This is a research prototype. The documented generator, [HiGen V5.3](docs/design/hierarchy-generation.md), uses external AI services for subject identification and definition writing; embedding and numerical construction run locally. Fully local hierarchy generation and million-note scalability have not yet been demonstrated.

| What you want to do | Guide | Main requirements |
| --- | --- | --- |
| Generate a hierarchy from your own posts | [Complete generation workflow](docs/generate-hierarchy.md) | Linux, an external language-model account, and CPU resources for embedding and clustering |
| Browse an existing hierarchy | [Browse HR39](docs/experiments/reproduce.md#browse-hr39-without-running-models) | Saved hierarchy and post files; no model inference |
| Export a hierarchy in the toy Nostr format | [Local signing and export](docs/generate-hierarchy.md#8-export-as-nostr-notes) | Complete saved run, `nak` and a local signing-key file |
| Extract subjects locally with a trained model | [Use a subject-extraction adapter](docs/experiments/reproduce.md#use-a-subject-adapter) | CUDA GPU, selected adapter and matching base-model weights |
| Inspect the fine-tuning measurements | [Read the saved comparison](docs/experiments/reproduce.md#inspect-the-fine-tune-comparison) | Saved comparison files; no model inference |
| Repeat the subject fine-tuning | [Training inputs and instructions](docs/experiments/reproduce.md#prepare-the-fine-tuning-inputs) | CUDA GPU, base-model weights and prepared training data |

The linked guides cover setup, hardware requirements and validation limits. The [subject adapters](https://huggingface.co/KernelKind/oracle-subject-adapters) and [research dataset](https://huggingface.co/datasets/KernelKind/oracle-research) are publicly available on Hugging Face.

Source code is available in [Oracle Research](https://github.com/kernelkind/oracle-research) and [Experiment Runner](https://github.com/kernelkind/experiment-runner). The guides include clone instructions.

## How it works

An AI language model identifies the subjects discussed in each Nostr post and writes definitions for them. An AI embedding model represents each subject using vectors. The generator uses these vectors to estimate similarity between subjects across posts.

The generator groups related subjects and uses a language model to define broader topics for the groups. It builds a few broad starting choices, then constructs the choices within each branch from the original subjects assigned to it. Posts stay linked to their subjects and can appear in multiple branches.

The fine-tuned models cover subject identification within individual posts.

The generation workflow uses the separate [Experiment Runner](https://github.com/kernelkind/experiment-runner) to execute language-model requests and record their inputs and responses. The generation guide includes its setup.

## Results

### Hierarchy generation

The [largest completed HiGen V5.3 run (HR39)](docs/experiments/hierarchy/runs.md#hr39--automatically-sampled-5000-note-higen-v53) processed 5,000 notes and produced six root choices representing 2,693 of them. Review of the hierarchy's semantic quality remained pending.

### Subject fine-tuning

The saved evaluation on the same **200 test notes** found these changes after one training pass over **1,000 notes**. The measurements concern the top-level subjects extracted from each post.

**Correctness** measures whether returned subjects are supported by the post. **Coverage** measures how many of the top-level reference subjects were recovered. Scores are averaged over the 200 notes, with invalid outputs scored as zero.

| Model | Correctness, untuned → fine-tuned | Coverage of reference subjects, untuned → fine-tuned |
| --- | ---: | ---: |
| Qwen3.8-27B | 67.0% → 96.1% | 42.1% → 61.6% |
| Gemma 4 31B | 93.7% → 96.6% | 46.2% → 55.0% |
| Gemma 4 26B-A4B | 88.0% → 89.8% | 42.9% → 55.8% |

Two additional Qwen passes increased correctness to **97.5%**, while coverage fell to **57.1%**. These results assess subject extraction; they do not establish the quality of the resulting global hierarchy. See the [full results and scoring definitions](docs/experiments/subject-extraction/fine-tuning.md#l1-only-test-results-october-15) and [instructions for inspecting the saved comparison](docs/experiments/reproduce.md#inspect-the-fine-tune-comparison).

## Experiments and data

The [experiment index](docs/experiments/README.md) connects the experiments to their inputs, prompts, settings and saved results, including unsuccessful trials and superseded approaches. The [reproduction guide](docs/experiments/reproduce.md) explains how to inspect and repeat recorded work, with its tested paths and remaining limitations.

The [research dataset](https://huggingface.co/datasets/KernelKind/oracle-research) includes posts actually used in experiments, prepared training inputs, final hierarchies, prompt answers and evaluation results. All **17 evaluated subject-model adapters** are hosted in the separate [subject-adapter repository](https://huggingface.co/KernelKind/oracle-subject-adapters).

## License

Unless otherwise noted, this project is licensed under the **GNU General Public License, version 3 or later** (`GPL-3.0-or-later`). See [LICENSE](LICENSE).
