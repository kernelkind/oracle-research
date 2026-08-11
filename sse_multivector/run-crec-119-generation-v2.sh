#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

source_root="$repo_root/target/crec-119-500-note-v2/reuse-source-v1"
if [[ ! -f "$source_root/input/notes.json" || ! -f "$source_root/generation/output.json" ]]; then
  echo "CREC-119 v1 reuse source is missing under $source_root" >&2
  echo "Extract the v1 baseline input and generation directories there before running v2." >&2
  exit 1
fi

nix develop -c cargo run --release --bin materialize-semantic-map-input -- \
  semantic_map/crec-119-generation-input-v2.json
nix develop -c python3 sse_multivector/codex_exec.py \
  run sse_multivector/crec-119-generation-v2.json
