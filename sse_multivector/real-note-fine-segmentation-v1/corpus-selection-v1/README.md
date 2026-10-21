# Frozen 100-note food/drink collection

`notes.json` contains the first 100 passing notes in the combined audit's
deterministic event-ID hash order. All 100 complete texts were inspected before
the freeze. No generation or SSE vector results were used to select them.

The 100 notes represent 95 public author keys, with at most two notes per author.
Complete texts use 6–478 tokens including special tokens. Forty selected notes
have 5–17 visible words; that count is an outcome, not a quota. All original
URLs, spelling, formatting, emoji, references and mixed-topic content remain.

All 194 manually eligible candidates passed the 512-token limit. The first 100
also passed the existing normalized-copy/near-copy checks and author cap, so no
candidate before the cutoff was replaced. The remaining 94 are simply outside
the deterministic cutoff. Every candidate's disposition is recorded in
`selection-accounting.json`.

## Identity and review

- `manifest.json` binds the frozen notes, complete accounting, token counts,
  review record and selection script by SHA-256.
- `notes.json` uses `schema_version: 1` and `notes[].note_id` / `notes[].text`,
  with public author, original corpus provenance, token counts and rationale.
- `complete-note-review.json` records full-note inspection and caveats without
  generating subjects, masks or segment judgments.
- `token-counts.json` records all 194 token lengths, local tokenizer file
  identities, exact settings, library versions, pinned image and resource limits.
- `selection-draft.json` and `selection-accounting-draft.json` preserve the
  mechanically proposed selection that was inspected before finalization.

Tokenizer: the existing local Sentence-T5-base revision
`fc5d4628481afbbaaacd7af6bb07cf9d3865f781`, with verified artifact tree
`bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d`.
The pinned SSE image uses Transformers 4.41.2 / Tokenizers 0.19.1 and
`T5TokenizerFast`. Settings match the production SSE worker: fast tokenizer,
local files only, remote code disabled, complete original text, special tokens
included, no truncation, attention masks and offsets. Unpadded counts equal the
production worker's attention-mask sums.

Only the small local tokenizer files were read. No checkpoint, weights, vectors,
database scan, network request, download, or model-generation call was used.

## Commands

The original token-count command, from the repository root:

After complete-note inspection and creation of the review record:

All outputs are create-once: these commands intentionally fail if their output
already exists. Preserve this frozen version and its history; do not delete
files merely to rerun. A necessary source correction would require a new version,
not note replacement to improve segmentation.
