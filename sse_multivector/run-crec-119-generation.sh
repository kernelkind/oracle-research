#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

if [[ $# -ne 1 ]]; then
  echo 'Usage: run-crec-119-generation.sh NEW-PI-AI-CONFIG.json' >&2
  echo 'The frozen Codex config is historical; supply explicit provider/authentication and a fresh run directory.' >&2
  exit 2
fi
nix develop -c python3 sse_multivector/extraction_pipeline.py run "$1"
