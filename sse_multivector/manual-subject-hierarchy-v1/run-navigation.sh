#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$project_root"
exec nix develop -c cargo run --release --bin sse-subject-navigation -- \
  sse_multivector/manual-subject-hierarchy-v1/hierarchy.json \
  sse_multivector/fine-region-hierarchy-result-v2/analysis.json \
  sse_multivector/fine-region-partition-result-v1/analysis.json
