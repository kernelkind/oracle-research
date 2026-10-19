# Oracle MVP

This project explores a way for people to discover the kinds of Nostr content they want to see.

The approach starts from the idea that people can recognize an interesting direction when presented with meaningful choices. A subject hierarchy offers those choices in a progressively narrowing pattern, helping the person reach the content they’re looking for.

Each choice lets the person direct their own discovery. The goal is to put that control in people’s hands, without predatory algorithms or invasions of privacy.

## Walkthrough

[Watch the walkthrough in Notedeck (19 seconds)](docs/media/hierarchy-walkthrough.mp4): choose a topic, narrow it down, and view its posts.

## Goals

### Hierarchy generation

- Run the complete hierarchy-generation process on consumer-grade hardware, including any required model inference.
- Make zero AI model API calls.
- Scale to corpora exceeding one million notes on consumer-grade hardware.

### The hierarchy

- Help people find notes about any desired topic in the corpus with minimal effort.
- Offer only a few meaningful choices at each step, progressively narrowing within the selected topic.
- Minimize duplicated information among sibling choices.

## How it works

An AI language model identifies the subjects discussed in each Nostr post and writes definitions for them. An AI embedding model represents each subject using vectors. The generator uses these vectors to estimate similarity between subjects across posts.

The generator groups related subjects and uses a language model to define broader topics for the groups. It builds a few broad starting choices, then constructs the choices within each branch from the original subjects assigned to it. Posts stay linked to their subjects and can appear in multiple branches.

The [current prototype, HiGen V5.3](docs/recommendation-engine/hierarchy-generation-v5.md), uses external AI services for subject identification and definition writing.

## Generate a hierarchy

Follow [the generation guide](docs/generate-hierarchy.md) to set up the models and runner, process your own posts, and browse the resulting hierarchy. It includes example configurations; validation of the complete setup on a fresh machine remains pending.

## Current status and results

This is a research prototype. Fully local hierarchy generation and million-note scalability have not yet been demonstrated.

The [largest completed HiGen V5.3 run (HR39)](docs/recommendation-engine/hierarchy-runs.md#hr39--automatically-sampled-5000-note-higen-v53) processed 5,000 notes and produced six root choices representing 2,693 of them. Review of the hierarchy's semantic quality remained pending.

[Fine-tuning trials](docs/planning/fine-tuning-pilot-process.md#l1-only-test-results-october-15) improved subject identification over the corresponding untuned models in a 200-note evaluation, although subjects were still missed. These results concern subject identification; evaluation of the complete hierarchy-generation process remains separate.

## Experiments and data

The [experiment index](docs/experiments/README.md) connects the recorded experiments to their inputs, settings, saved results and fine-tuned adapters. It includes an exact file inventory for the planned GitHub release, with unresolved input versions and verification work identified. Data downloads and tested instructions for rerunning the historical experiments are still being prepared.
