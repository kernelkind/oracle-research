#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

nix develop -c python3 sse_multivector/codex_usage_calibration.py \
  sse_multivector/crec-119-generation-v1.json \
  target/crec-119-500-note-v1/codex-usage-calibration.json \
  --max-seconds 3600
