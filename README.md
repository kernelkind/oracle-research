# Oracle MVP

This project explores a way for people to discover the kinds of Nostr content they want to see.

This repository contains the hierarchy generator, along with the code, prompts and findings from its development.

The approach starts from the idea that people can recognize an interesting direction when presented with meaningful choices. A subject hierarchy offers those choices in a progressively narrowing pattern, helping the person reach the content they’re looking for.

Each choice lets the person direct their own discovery. The goal is to put that control in people’s hands, without predatory algorithms or invasions of privacy.

## Walkthrough

[Watch the walkthrough in Notedeck (19 seconds)](docs/media/hierarchy-walkthrough.mp4): use the **Hierarchy** column to choose a topic, narrow it down, and view its posts.

The interface uses a [toy hierarchy snapshot protocol](docs/recommendation-engine/design/hierarchy-serving-protocol-decisions.md) developed for this prototype. The format is intended for local or private testing, so please avoid publishing its experimental events to public Nostr relays.

**Notedeck interface source code:** link pending publication.
<!-- Add the public source-code URL for the Notedeck hierarchy interface before publication. -->

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

**Current implementation:** This is a research prototype. The documented generator, [HiGen V5.3](docs/recommendation-engine/hierarchy-generation-v5.md), uses external AI services for subject identification and definition writing; embedding and numerical construction run locally. Fully local hierarchy generation and million-note scalability have not yet been demonstrated.

| What you want to do | Guide | Main requirements |
| --- | --- | --- |
| Generate a hierarchy from your own posts | [Complete generation workflow](docs/generate-hierarchy.md) | Linux, an external language-model account, and CPU resources for embedding and clustering |
| Browse an existing hierarchy | [Browse HR39](docs/experiments/reproduce.md#browse-hr39-without-running-models) | Saved hierarchy and post files; no model inference |
| Export a hierarchy in the toy Nostr format | [Local signing and export](docs/generate-hierarchy.md#8-export-as-nostr-notes) | Complete saved run, `nak` and a local signing-key file |
| Extract subjects locally with a trained model | [Use a subject-extraction adapter](docs/experiments/reproduce.md#use-a-subject-adapter) | CUDA GPU, selected adapter and matching base-model weights |
| Inspect the fine-tuning measurements | [Read the saved comparison](docs/experiments/reproduce.md#inspect-the-fine-tune-comparison) | Saved comparison files; no model inference |
| Repeat the subject fine-tuning | [Training inputs and instructions](docs/experiments/reproduce.md#prepare-the-fine-tuning-inputs) | CUDA GPU, base-model weights and prepared training data |

The linked guides cover setup, hardware requirements and validation limits. Model and data downloads are still being prepared.

## How it works

An AI language model identifies the subjects discussed in each Nostr post and writes definitions for them. An AI embedding model represents each subject using vectors. The generator uses these vectors to estimate similarity between subjects across posts.

The generator groups related subjects and uses a language model to define broader topics for the groups. It builds a few broad starting choices, then constructs the choices within each branch from the original subjects assigned to it. Posts stay linked to their subjects and can appear in multiple branches.

The fine-tuned models cover subject identification within individual posts.

The generation workflow uses the separate `experiment-runner` to execute language-model requests and record their inputs and responses. The generation guide includes its setup.

## Results

The [largest completed HiGen V5.3 run (HR39)](docs/recommendation-engine/hierarchy-runs.md#hr39--automatically-sampled-5000-note-higen-v53) processed 5,000 notes and produced six root choices representing 2,693 of them. Review of the hierarchy's semantic quality remained pending.

[Fine-tuning trials](docs/planning/fine-tuning-pilot-process.md#l1-only-test-results-october-15) improved subject identification over the corresponding untuned models in a 200-note evaluation, although subjects were still missed. These results concern subject identification; evaluation of the complete hierarchy-generation process remains separate.

## Experiments and data

The [experiment index](docs/experiments/README.md) connects the experiments to their inputs, prompts, settings and saved results, including unsuccessful trials and superseded approaches. The [reproduction guide](docs/experiments/reproduce.md) explains how to inspect and repeat recorded work, with its tested paths and remaining limitations.

The publication includes posts actually used in experiments, prepared training inputs, final hierarchies, prompt answers and evaluation results. These inputs and results will be available on **Hugging Face Datasets**; all **17 evaluated subject-model adapters** will be available on **Hugging Face Models**. Download links are pending publication.

## License

A project license has not yet been specified.
