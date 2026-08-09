#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

nix develop -c python3 sse_multivector/codex_exec.py \
  run sse_multivector/crec-119-generation-v1.json
