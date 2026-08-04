#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
archive="$repo_root/sse_multivector/baselines/communicated-meaning-tev4-1/baseline.tar.zst"
hierarchy="$repo_root/sse_multivector/fine-region-hierarchy-result-v2/analysis.json"
output_dir="${1:-$repo_root/sse_multivector/fine-region-scc-preflight-v1}"
baseline="$(mktemp -d -t sse-fine-region-scc.XXXXXXXX)"
candidate_dir="$(mktemp -d -t sse-fine-region-scc-result.XXXXXXXX)"
candidate="$candidate_dir/analysis.json"

cleanup() {
  rm -rf "$baseline"
  rm -rf "$candidate_dir"
}
trap cleanup EXIT

expected_archive="fff03a8b1ed76e45413def0049cdd9fc3c948ae014d5ac94d72fa62f41f8cfa6"
actual_archive="$(sha256sum "$archive" | cut -d ' ' -f 1)"
if [[ "$actual_archive" != "$expected_archive" ]]; then
  echo "baseline archive hash mismatch: expected $expected_archive, got $actual_archive" >&2
  exit 1
fi

expected_hierarchy="1371b94a47675652e85f54a294a78f6f34fbc508727236b596f2f9be37a48643"
actual_hierarchy="$(sha256sum "$hierarchy" | cut -d ' ' -f 1)"
if [[ "$actual_hierarchy" != "$expected_hierarchy" ]]; then
  echo "hierarchy analysis hash mismatch: expected $expected_hierarchy, got $actual_hierarchy" >&2
  exit 1
fi

tar --zstd -xf "$archive" -C "$baseline"
mkdir -p "$output_dir"
cd "$repo_root"
nix develop -c cargo run --release --bin sse-fine-region-scc-preflight -- \
  "$hierarchy" \
  "$baseline/analysis/normalized-vectors.f32le" \
  "$candidate"

output="$output_dir/analysis.json"
if [[ -e "$output" ]]; then
  if ! cmp -s "$candidate" "$output"; then
    echo "existing SCC preflight differs from deterministic replay: $output" >&2
    exit 1
  fi
  echo "verified SCC preflight: $output"
else
  mv "$candidate" "$output"
  echo "published SCC preflight: $output"
fi
